"""Train the CNN with Spark's TorchDistributor (5 CPU processes, DDP over gloo).

    caffeinate -i .venv/bin/python src/train_cnn.py     # full run; resumes from last.pt if the run dir has one
    .venv/bin/python src/train_cnn.py --pilot           # 200 steps, speed check only

Live progress: python -m http.server 8765 --bind 127.0.0.1 --directory ~/pnwml-data/runs/cnn
then open http://127.0.0.1:8765/monitor.html
"""
import argparse
import json
import os
import shutil
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
from common import ML, OUT_TABLES, ROOT, sh, spark_session, webhdfs  # noqa: E402

RUNS = os.path.expanduser('~/pnwml-data/runs')


def parquet_files(fs, split):
    import pyarrow.parquet as pq
    files = []
    for path in sorted(fs.ls(f'{ML}/waveforms_z150s/split={split}', detail=False)):
        if path.endswith('.parquet'):
            with fs.open(path, 'rb') as f:
                files.append((path, pq.ParquetFile(f).metadata.num_rows))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--name', default=None)
    ap.add_argument('--processes', type=int, default=5)
    ap.add_argument('--max-epochs', type=int, default=15)
    ap.add_argument('--steps', type=int, default=None, help='steps per epoch (default: full pass)')
    ap.add_argument('--val-files', type=int, default=None, help='limit validation files (quick tests)')
    ap.add_argument('--stride1', type=int, default=1)
    args = ap.parse_args()

    run_dir = os.path.join(RUNS, args.name or ('pilot' if args.pilot else 'cnn'))
    os.makedirs(run_dir, exist_ok=True)
    shutil.copy(os.path.join(SRC, 'monitor.html'), run_dir)

    fs = webhdfs()
    cfg = dict(run_dir=run_dir, files={s: parquet_files(fs, s) for s in ('train', 'val')},
               batch_size=64, lr=1e-3, weight_decay=1e-4, max_epochs=1 if args.pilot else args.max_epochs,
               patience=3, steps=200 if args.pilot else args.steps, val_files=args.val_files,
               validate=not args.pilot, threads=2, seed=42, stride1=args.stride1, log_every=20)

    os.environ['PYTHONPATH'] = SRC + os.pathsep + os.environ.get('PYTHONPATH', '')
    os.environ['OMP_NUM_THREADS'] = str(cfg['threads'])
    os.environ.setdefault('GLOO_SOCKET_IFNAME', 'lo0')
    os.environ.setdefault('PET_LOCAL_ADDR', '127.0.0.1')  # torchrun otherwise uses the Mac's odd FQDN and hangs

    spark = spark_session('cnn_training', driver_mem='2g')
    from pyspark.ml.torch.distributor import TorchDistributor
    import cnn

    result = TorchDistributor(num_processes=args.processes, local_mode=True, use_gpu=False).run(cnn.fit, cfg)
    print(result)
    spark.stop()

    if args.pilot:
        with open(os.path.join(OUT_TABLES, 'a2_pilot.json'), 'w') as f:
            json.dump(dict(result, processes=args.processes, batch_per_process=cfg['batch_size'],
                           train_rows=sum(r for _, r in cfg['files']['train'])), f, indent=1)
    elif args.name is None:
        models = os.path.join(ROOT, 'outputs', 'models')
        os.makedirs(models, exist_ok=True)
        shutil.copy(os.path.join(run_dir, 'best.pt'), os.path.join(models, 'cnn_best.pt'))
        shutil.copy(os.path.join(run_dir, 'history.json'), os.path.join(OUT_TABLES, 'a2_training_history.json'))
        shutil.copy(os.path.join(run_dir, 'train.log'), os.path.join(OUT_TABLES, 'a2_training_log.txt'))
        sh(f'hdfs dfs -mkdir -p {ML}/models && hdfs dfs -put -f {models}/cnn_best.pt {ML}/models/', quiet=True)


if __name__ == '__main__':
    main()
