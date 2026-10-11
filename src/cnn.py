"""1D CNN for the 4-class seismic problem, trained with DDP under Spark's TorchDistributor (Bab 5.3-5.4)."""
import io
import json
import os
import time

import numpy as np
import pyarrow.parquet as pq
import torch
import torch.nn as nn
import torch.nn.functional as F

import ml_prep as mp

CLASSES = ['earthquake', 'explosion', 'surface_event', 'noise']


def block(c_in, c_out, stride=1):
    return nn.Sequential(nn.Conv1d(c_in, c_out, 7, stride=stride, padding=3), nn.BatchNorm1d(c_out),
                         nn.ReLU(), nn.MaxPool1d(4))


class CNN(nn.Module):
    def __init__(self, n_context=len(mp.CONTEXT_FEATURES), n_classes=len(CLASSES), stride1=1):
        super().__init__()
        self.wave = nn.Sequential(block(1, 16, stride1), block(16, 32), block(32, 64), block(64, 128),
                                  nn.Conv1d(128, 128, 7, padding=3), nn.BatchNorm1d(128), nn.ReLU(),
                                  nn.AdaptiveAvgPool1d(1), nn.Flatten())
        self.context = nn.Sequential(nn.Linear(n_context, 16), nn.ReLU())
        self.head = nn.Sequential(nn.Linear(128 + 16, 64), nn.ReLU(), nn.Dropout(0.3), nn.Linear(64, n_classes))

    def forward(self, x, c):
        return self.head(torch.cat([self.wave(x), self.context(c)], dim=1))


def f1_per_class(y, p, k=len(CLASSES)):
    cm = np.bincount(y * k + p, minlength=k * k).reshape(k, k)
    tp = np.diag(cm)
    precision = tp / np.maximum(cm.sum(0), 1)
    recall = tp / np.maximum(cm.sum(1), 1)
    return 2 * precision * recall / np.maximum(precision + recall, 1e-12)


class Context:
    """The 9 context features, labels and class weights, keyed by (dataset, trace_name)."""

    def __init__(self, fs, path):
        f = next(p for p in fs.ls(path, detail=False) if p.endswith('.parquet'))
        df = pq.read_table(io.BytesIO(fs.cat_file(f))).to_pandas()
        self.row = {k: i for i, k in enumerate(df.dataset + '|' + df.trace_name)}
        self.features = df[mp.CONTEXT_FEATURES].to_numpy(np.float32)
        self.labels = df.label.map(CLASSES.index).to_numpy(np.int64)
        w = df.groupby('label').class_weight.first()
        self.class_weights = torch.tensor([w[c] for c in CLASSES], dtype=torch.float32)


def shard(files, rank, world):
    """Greedy split of (path, rows) pairs over processes so every process gets about the same number of rows."""
    parts, load = [[] for _ in range(world)], [0] * world
    for path, rows in sorted(files, key=lambda f: -f[1]):
        i = load.index(min(load))
        parts[i].append((path, rows))
        load[i] += rows
    return parts[rank], parts


def read(fs, path, ctx):
    t = pq.read_table(io.BytesIO(fs.cat_file(path)), columns=['dataset', 'trace_name', 'z'])
    z = t.column('z').combine_chunks().values.to_numpy().reshape(-1, mp.N)
    idx = np.array([ctx.row[f'{d}|{n}'] for d, n in zip(t.column('dataset').to_pylist(), t.column('trace_name').to_pylist())])
    return z, idx


def batches(fs, files, ctx, batch_size, train, rng=None, offset=None, mix=6):
    """Training: files are read `mix` at a time and their rows shuffled together, because Spark wrote
    most files with one dominant class; a batch from a single file would be almost one class."""
    paths = [p for p, _ in files]
    groups = [list(g) for g in np.array_split(rng.permutation(paths), max(1, -(-len(paths) // mix)))] if train else [[p] for p in paths]
    start = (mp.N - mp.CROP) // 2 if offset is None else offset
    for group in groups:
        parts = [read(fs, p, ctx) for p in group]
        z = np.concatenate([p[0] for p in parts])
        idx = np.concatenate([p[1] for p in parts])
        order = rng.permutation(len(z)) if train else np.arange(len(z))
        for s in range(0, len(order), batch_size):
            b = order[s:s + batch_size]
            x = np.stack([mp.crop(z[i], True, rng) for i in b]) if train else z[b, start:start + mp.CROP]
            yield (torch.from_numpy(np.ascontiguousarray(x)).unsqueeze(1),
                   torch.from_numpy(ctx.features[idx[b]]), torch.from_numpy(ctx.labels[idx[b]]))


def n_batches(files, batch_size):
    return sum(rows for _, rows in files) // batch_size


class Progress:
    """Writes progress.json and train.log for the live monitor page (rank 0 only)."""

    def __init__(self, run_dir, active):
        self.run_dir, self.active, self.state = run_dir, active, {}

    def log(self, msg):
        if self.active:
            line = f'{time.strftime("%Y-%m-%d %H:%M:%S")}  {msg}'
            print(line, flush=True)
            with open(os.path.join(self.run_dir, 'train.log'), 'a') as f:
                f.write(line + '\n')

    def update(self, **kw):
        if self.active:
            self.state.update(kw, updated_at=time.strftime('%H:%M:%S'))
            tmp = os.path.join(self.run_dir, 'progress.json.tmp')
            with open(tmp, 'w') as f:
                json.dump(self.state, f)
            os.replace(tmp, os.path.join(self.run_dir, 'progress.json'))


def evaluate(model, fs, files, ctx, batch_size, weights):
    model.eval()
    ys, ps, loss = [], [], 0.0
    with torch.no_grad():
        for x, c, y in batches(fs, files, ctx, batch_size, train=False):
            out = model(x, c)
            loss += F.cross_entropy(out, y, weight=weights, reduction='sum').item()
            ys.append(y.numpy())
            ps.append(out.argmax(1).numpy())
    y = np.concatenate(ys) if ys else np.zeros(0, int)
    return y, np.concatenate(ps) if ps else np.zeros(0, int), loss, weights[torch.from_numpy(y)].sum().item()


def fit(cfg):
    """Training loop run by every TorchDistributor process. Resumes from last.pt when it exists."""
    import torch.distributed as dist
    from torch.nn.parallel import DistributedDataParallel as DDP
    from common import ML, webhdfs

    dist.init_process_group('gloo')
    rank, world = dist.get_rank(), dist.get_world_size()
    torch.set_num_threads(cfg['threads'])
    torch.manual_seed(cfg['seed'])
    run_dir, bs = cfg['run_dir'], cfg['batch_size']
    prog = Progress(run_dir, rank == 0)

    fs = webhdfs()
    ctx = Context(fs, f'{ML}/context')
    train_files, all_train = shard(cfg['files']['train'], rank, world)
    val_files, _ = shard(cfg['files']['val'][:cfg.get('val_files') or None], rank, world)
    steps = cfg['steps'] or min(n_batches(p, bs) for p in all_train)

    model = CNN(stride1=cfg['stride1'])
    ddp = DDP(model)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg['lr'], weight_decay=cfg['weight_decay'])
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode='max', factor=0.5, patience=1)
    loss_fn = nn.CrossEntropyLoss(weight=ctx.class_weights)

    last = os.path.join(run_dir, 'last.pt')
    state = dict(epoch=0, best_f1=-1.0, best_epoch=0, bad_epochs=0, history=[])
    if os.path.exists(last):
        ck = torch.load(last, weights_only=False)
        model.load_state_dict(ck['model'])
        opt.load_state_dict(ck['optimizer'])
        sched.load_state_dict(ck['scheduler'])
        state = ck['state']
        prog.log(f'resume from checkpoint: epoch {state["epoch"]} done, continuing with epoch {state["epoch"] + 1}')
    else:
        prog.log(f'start: {world} processes x {cfg["threads"]} threads, batch {bs}/process, {steps} steps/epoch, '
                 f'{sum(r for _, r in cfg["files"]["train"]):,} train rows, {sum(r for _, r in cfg["files"]["val"]):,} val rows')
    prog.update(status='training', max_epochs=cfg['max_epochs'], steps=steps, history=state['history'],
                best_epoch=state['best_epoch'], best_f1=state['best_f1'], patience=cfg['patience'],
                bad_epochs=state['bad_epochs'], started_at=time.strftime('%Y-%m-%d %H:%M:%S'))

    losses, t_run = [], time.time()
    for epoch in range(state['epoch'] + 1, cfg['max_epochs'] + 1):
        ddp.train()
        rng = np.random.default_rng(cfg['seed'] + 1000 * epoch + rank)
        t0, running = time.time(), 0.0
        for step, (x, c, y) in enumerate(batches(fs, train_files, ctx, bs, True, rng), 1):
            opt.zero_grad()
            loss = loss_fn(ddp(x, c), y)
            loss.backward()
            opt.step()
            running += loss.item()
            losses.append(loss.item())
            if step % cfg['log_every'] == 0 or step == steps:
                rate = step * bs * world / (time.time() - t0)
                epoch_s = state['history'][-1]['seconds'] if state['history'] else steps * bs * world / rate
                eta = (steps - step) * bs * world / rate
                prog.update(status='training', epoch=epoch, step=step, loss=running / step, rate=rate,
                            lr=opt.param_groups[0]['lr'], eta_epoch=eta,
                            eta_max=eta + (cfg['max_epochs'] - epoch) * epoch_s)
                if step % (cfg['log_every'] * 10) == 0:
                    prog.log(f'epoch {epoch} step {step}/{steps}  loss {running / step:.4f}  {rate:.0f} rec/s')
            if step == steps:
                break
        train_s = time.time() - t0

        if not cfg['validate']:
            prog.log(f'pilot done: {steps} steps in {train_s:.0f} s, {steps * bs * world / train_s:.0f} rec/s')
            prog.update(status='done')
            dist.destroy_process_group()
            return dict(rate=steps * bs * world / train_s, seconds=train_s, steps=steps,
                        loss_first=float(np.mean(losses[:20])), loss_last=float(np.mean(losses[-20:])))

        prog.update(status='validating')
        y, p, loss_sum, w_sum = evaluate(model, fs, val_files, ctx, 256, ctx.class_weights)
        gathered = [None] * world
        dist.all_gather_object(gathered, (y, p, loss_sum, w_sum))
        metric = [0.0]
        if rank == 0:
            y = np.concatenate([g[0] for g in gathered])
            p = np.concatenate([g[1] for g in gathered])
            f1 = f1_per_class(y, p)
            row = dict(epoch=epoch, train_loss=running / steps, val_loss=sum(g[2] for g in gathered) / sum(g[3] for g in gathered),
                       val_macro_f1=float(f1.mean()), val_acc=float((y == p).mean()),
                       **{f'f1_{c}': float(v) for c, v in zip(CLASSES, f1)},
                       lr=opt.param_groups[0]['lr'], seconds=time.time() - t0, val_rows=len(y))
            metric = [row['val_macro_f1']]
        dist.broadcast_object_list(metric, src=0)
        macro = metric[0]
        sched.step(macro)

        improved = macro > state['best_f1']
        state['bad_epochs'] = 0 if improved else state['bad_epochs'] + 1
        if improved:
            state.update(best_f1=macro, best_epoch=epoch)
        state['epoch'] = epoch
        if rank == 0:
            state['history'].append(row)
            ck = dict(model=model.state_dict(), optimizer=opt.state_dict(), scheduler=sched.state_dict(), state=state)
            torch.save(ck, last + '.tmp')
            os.replace(last + '.tmp', last)
            if improved:
                torch.save(dict(model=model.state_dict(), epoch=epoch, val_macro_f1=macro, stride1=cfg['stride1']),
                           os.path.join(run_dir, 'best.pt'))
            with open(os.path.join(run_dir, 'history.json'), 'w') as f:
                json.dump(state['history'], f, indent=1)
            prog.log(f'epoch {epoch} done in {row["seconds"] / 60:.1f} min  train_loss {row["train_loss"]:.4f}  '
                     f'val_loss {row["val_loss"]:.4f}  val_macro_f1 {macro:.4f}' + ('  * best' if improved else ''))
            prog.update(history=state['history'], best_epoch=state['best_epoch'], best_f1=state['best_f1'],
                        bad_epochs=state['bad_epochs'], last_checkpoint=time.strftime('%H:%M:%S'))
        dist.barrier()
        if state['bad_epochs'] >= cfg['patience']:
            prog.log(f'early stopping: no improvement for {cfg["patience"]} epochs')
            break

    prog.log(f'finished: best epoch {state["best_epoch"]}, val macro-F1 {state["best_f1"]:.4f}, '
             f'{(time.time() - t_run) / 60:.0f} min this session')
    prog.update(status='finished')
    dist.destroy_process_group()
    return dict(best_epoch=state['best_epoch'], best_f1=state['best_f1'], epochs=state['epoch'])


if __name__ == '__main__':
    m = CNN()
    out = m(torch.randn(2, 1, mp.CROP), torch.randn(2, len(mp.CONTEXT_FEATURES)))
    n = sum(p.numel() for p in m.parameters())
    assert out.shape == (2, 4) and 150_000 < n < 250_000, (out.shape, n)
    assert CNN(stride1=2)(torch.randn(2, 1, mp.CROP), torch.randn(2, 9)).shape == (2, 4)
    assert np.allclose(f1_per_class(np.array([0, 1, 2, 3, 0]), np.array([0, 1, 2, 3, 1])), [2 / 3, 2 / 3, 1, 1])
    parts = shard([('a', 10), ('b', 7), ('c', 5), ('d', 3)], 0, 2)[1]
    assert sorted(sum(r for _, r in p) for p in parts) == [12, 13]
    print('ok', n, 'parameters')
