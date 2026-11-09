'use strict';
/* PNW Seismic Insights: all numbers come from data/*; everything else is labels and copy. */
const CLS = ['earthquake', 'explosion', 'surface_event', 'noise'];
const EVENTS = CLS.slice(0, 3);
const NAME = { earthquake: 'Gempa bumi', explosion: 'Ledakan', surface_event: '<em>Surface event</em>', noise: '<em>Noise</em>' };
const LOWER = { earthquake: 'gempa bumi', explosion: 'ledakan', surface_event: '<em>surface event</em>' };
const COL = { earthquake: 'var(--eq)', explosion: 'var(--ex)', surface_event: 'var(--su)', noise: 'var(--no)' };
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
const TABS = ['otomatisasi', 'surface-event', 'wilayah', 'stasiun'];

const $ = s => document.querySelector(s);
const fm = [0, 1].map(d => new Intl.NumberFormat('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d }));
const fmt = n => fm[0].format(n);
/** x in 0..100 → "92,5%"; exact 0 and 100 lose the decimal. */
const pct = x => (x === 0 || x === 100 ? fm[0].format(x) : fm[1].format(x)) + '%';
const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
/** Small seeded generator so "Tampilkan 6 lainnya" gives the same sequence in every run (useful for the video). */
function rng(s) {
  return () => { s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function shuffled(a, r) {
  const o = a.slice();
  for (let i = o.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [o[i], o[j]] = [o[j], o[i]]; }
  return o;
}
/** Labelled horizontal bars: label + value on one line, bar under it. */
const barRows = rows => rows.map(r => `<div class="hb${r.on ? ' on' : ''}"${r.tip ? ` data-tip="${r.tip}"` : ''}><span>${r.label}</span><span class="hv num">${pct(r.v)}</span><div class="ht"><div style="width:${r.v}%;background:${r.color}"></div></div></div>`).join('');

/* ---------- tooltip: any element with data-tip ---------- */
const tip = $('#tip');
function tipAt(e) {
  const t = e.target.closest && e.target.closest('[data-tip]');
  if (!t) { tip.hidden = true; return; }
  tip.innerHTML = t.dataset.tip;
  tip.hidden = false;
  tip.style.transform = `translate(${Math.max(4, Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8))}px,${Math.max(4, Math.min(e.clientY + 14, innerHeight - tip.offsetHeight - 8))}px)`;
}
addEventListener('pointermove', tipAt);
addEventListener('pointerdown', tipAt);
addEventListener('scroll', () => { tip.hidden = true; }, { passive: true });

/* ---------- routing ---------- */
function route() {
  const h = location.hash.slice(1), t = TABS.includes(h) ? h : TABS[0];
  document.querySelectorAll('.tabs a').forEach(a => {
    if (a.getAttribute('href') === '#' + t) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  document.querySelectorAll('[data-panel]').forEach(p => { p.hidden = p.dataset.panel !== t; });
  tip.hidden = true;
}
addEventListener('hashchange', route);
route();

/* ---------- data ---------- */
const FILES = ['predictions.csv', 'waveforms_sample.json', 'stations.csv', 'explosions.csv', 'summary.json', 'states.json'];
const TEXT_COLS = new Set(['label', 'pred', 'sensor', 'station', 'local_time', 'network', 'group', 'event_id']);
function parseCSV(text) {
  const lines = text.trim().split('\n'), head = lines[0].split(',');
  return lines.slice(1).map(l => {
    const c = l.split(','), o = {};
    head.forEach((h, i) => { o[h] = TEXT_COLS.has(h) ? c[i] : c[i] === '' ? null : +c[i]; });
    return o;
  });
}
async function load(f) {
  const r = await fetch('data/' + f).catch(() => { throw new Error(f); });
  if (!r.ok) throw new Error(f);
  return f.endsWith('.json') ? r.json() : parseCSV(await r.text());
}
Promise.all(FILES.map(load)).then(([pred, waves, stations, explosions, summary, states]) => {
  initAuto(pred, waves);
  initSurface(pred, summary);
  initRegions(summary, explosions, states);
  initStations(stations, summary, states);
  $('#status').hidden = true;
  $('#app').hidden = false;
}).catch(e => {
  const s = $('#status');
  s.classList.add('err');
  s.innerHTML = `Data <code>${e.message}</code> tidak bisa dimuat. Periksa koneksi, lalu <a href="">muat ulang halaman</a>.`;
  console.warn('load failed', e);
});

/* ---------- 01 otomatisasi ---------- */
const conf = r => Math.max(r.p_earthquake, r.p_explosion, r.p_surface_event, r.p_noise);
function fmtDate(s) {
  const [d, t] = s.split(' '), [y, m, day] = d.split('-');
  return `${+day} ${MONTHS[+m - 1]} ${y}, ${t.replace(':', '.')}`;
}
function initAuto(pred, waves) {
  const byRid = new Map(pred.map(r => [r.rid, r]));
  const samples = waves.map(w => ({ ...byRid.get(w.rid), points: w.points }));
  const c = Float64Array.from(pred, conf), ok = Uint8Array.from(pred, r => r.label === r.pred ? 1 : 0);
  const status = (s, T) => conf(s) < T ? 'hold' : s.label === s.pred ? 'ok' : 'bad';
  const r = rng(42);
  const shown = new Set();
  let current = [];

  const covers = (list, T) => ['ok', 'hold', 'bad'].every(st => !samples.some(s => status(s, T) === st) || list.some(s => status(s, T) === st));
  const valid = (list, T) => list.length === 6 && covers(list, T) && new Set(list.map(s => s.label)).size >= 3;

  /** Six unseen samples containing every outcome that exists at T and at least 3 analyst classes. */
  function draw(T) {
    let pool = samples.filter(s => !shown.has(s.rid));
    if (pool.length < 6) { shown.clear(); pool = samples.slice(); }
    pool = shuffled(pool, r);
    const pick = [], rest = shuffled(samples, r);  // a scarce outcome may repeat; the other rows stay unseen
    for (const st of ['ok', 'hold', 'bad']) {
      const hit = pool.find(s => status(s, T) === st && !pick.includes(s)) || rest.find(s => status(s, T) === st && !pick.includes(s));
      if (hit) pick.push(hit);
    }
    while (pick.length < 6) {
      const seen = new Set(pick.map(s => s.label));
      pick.push(pool.find(s => !pick.includes(s) && (seen.size >= 3 || !seen.has(s.label))) || pool.find(s => !pick.includes(s)));
    }
    pick.forEach(s => shown.add(s.rid));
    return shuffled(pick, r);
  }

  function signal(points) {
    const m = Math.max(...points.map(Math.abs)) || 1;
    let grid = '';
    for (let x = 50; x < 600; x += 50) grid += `<line x1="${x}" x2="${x}" y1="0" y2="60" stroke="var(--paperline)" stroke-width="1" vector-effect="non-scaling-stroke"/>`;
    const line = points.map((v, i) => `${i},${(30 - v / m * 27).toFixed(1)}`).join(' ');
    return `<svg class="sig" viewBox="0 0 600 60" preserveAspectRatio="none" role="img" aria-label="Sinyal seismik 120 detik"><line x1="0" x2="600" y1="30" y2="30" stroke="var(--paperline)" stroke-width="1" vector-effect="non-scaling-stroke"/>${grid}<polyline points="${line}" fill="none" stroke="var(--ink)" stroke-width="1" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>`;
  }
  const PILL = { ok: 'Otomatis · benar', bad: 'Otomatis · salah', hold: 'Ke analis' };
  function renderQueue(T) {
    $('#queue').innerHTML = current.map(s => {
      const st = status(s, T);
      const bars = CLS.map(k => {
        const v = s['p_' + k] * 100, top = k === s.pred ? 'top' : '';
        return `<span class="${top}">${NAME[k]}</span><div class="bar"><div style="width:${v.toFixed(1)}%;background:${COL[k]}"></div></div><span class="v ${top}">${pct(v)}</span>`;
      }).join('');
      return `<tr><td class="rec">${fmtDate(s.local_time)}</td><td>${signal(s.points)}</td><td><div class="probs">${bars}</div></td><td><span class="pill ${st}"><i></i>${PILL[st]}</span></td><td><span class="lab"><i class="sw" style="background:${COL[s.label]}"></i>${NAME[s.label]}</span></td></tr>`;
    }).join('');
  }
  function update() {
    const T = +$('#thr').value / 100;
    $('#thrv').textContent = fmt(T * 100) + '%';
    let a = 0, right = 0;
    for (let i = 0; i < c.length; i++) if (c[i] >= T) { a++; right += ok[i]; }
    const auto = 100 * a / c.length, hold = 100 - auto;
    $('#kAuto').textContent = pct(auto);
    $('#kHold').textContent = pct(hold);
    $('#kOk').textContent = a ? pct(100 * right / a) : '–';
    $('#kBad').textContent = a ? '· ' + pct(100 * (a - right) / a) + ' salah' : '';
    const sa = $('#sAuto'), sh = $('#sHold');
    sa.style.flex = `${auto} 1 0`; sh.style.flex = `${hold} 1 0`;
    sa.innerHTML = auto > 12 ? `${pct(auto)}<span class="w">&nbsp;otomatis</span>` : '';
    sh.innerHTML = hold > 12 ? `<span class="plate">${pct(hold)}<span class="w">&nbsp;ke analis</span></span>` : '';
    sa.dataset.tip = `${fmt(a)} rekaman diproses otomatis`;
    sh.dataset.tip = `${fmt(c.length - a)} rekaman ke analis`;
    $('#dec1').innerHTML = `Jika kesalahan ingin ditekan, batas dapat dinaikkan, namun pemeriksaan oleh analis akan bertambah. Jika beban analis ingin diringankan, batas dapat diturunkan, namun risiko kesalahan akan meningkat. Pada batas ${fmt(T * 100)}%, analis perlu memeriksa ${pct(hold)} rekaman dan ${a ? pct(100 * right / a) : '–'} prediksi otomatis benar.`;
    if (!valid(current, T)) current = draw(T);
    renderQueue(T);
  }
  $('#thr').addEventListener('input', update);
  $('#again').addEventListener('click', () => { const T = +$('#thr').value / 100; current = draw(T); renderQueue(T); });
  update();
}

/* ---------- 02 surface event ---------- */
function initSurface(pred, summary) {
  const spe = summary.stations_per_event;
  const byLabel = k => pred.filter(r => r.label === k);
  const passed = rows => 100 * rows.filter(r => r.pred !== 'noise').length / rows.length;
  const oneRec = byLabel('surface_event').filter(r => r.n_stations_event === 1);
  const multi = k => 100 - 100 * spe[k].share[0];
  const noisePass = passed(byLabel('noise')), dlSurface = passed(byLabel('surface_event'));
  const perEvent = k => `Dihitung per kejadian dari ${fmt(spe[k].events)} kejadian`;
  const perRec = k => `Dihitung per rekaman dari ${fmt(byLabel(k).length)} rekaman data test`;

  const SETUPS = [
    { label: '1 stasiun', detect: () => 100, noise: 100, detectTip: () => 'Setiap getaran langsung memicu alarm', noiseTip: 'Tanpa model, semua <em>noise</em> masuk ke analis',
      decision: 'Jika alarm cukup dari 1 stasiun, seluruh <em>surface event</em> terdeteksi, namun seluruh <em>noise</em> juga masuk dan harus diperiksa analis.' },
    { label: 'Minimal 2 stasiun', detect: multi, noise: null, detectTip: perEvent, noiseTip: 'Data tidak mengukur <em>noise</em> yang terjadi bersamaan di 2 stasiun',
      decision: `Jika alarm memerlukan minimal 2 stasiun, ${pct(100 - multi('surface_event'))} <em>surface event</em> terlewat karena hanya terekam 1 stasiun.` },
    { label: '1 stasiun + model <em>deep learning</em>', detect: k => passed(byLabel(k)), noise: noisePass,
      detectTip: k => k === 'surface_event' ? `Dari rekaman yang hanya terekam 1 stasiun, ${pct(passed(oneRec))} tetap terdeteksi` : perRec(k), noiseTip: perRec('noise'),
      decision: `Jika alarm 1 stasiun digabungkan dengan model <em>deep learning</em>, <em>surface event</em> yang terdeteksi ${fm[1].format(dlSurface / multi('surface_event'))}× lebih banyak daripada aturan minimal 2 stasiun.` },
  ];

  const seg = $('#setup'), box = $('#cEvents'), noiseBox = $('#cNoise');
  seg.innerHTML = SETUPS.map((s, i) => `<button type="button" data-i="${i}">${s.label}</button>`).join('');
  const ORDER = ['surface_event', 'explosion', 'earthquake'];
  box.innerHTML = barRows(ORDER.map(k => ({ label: NAME[k], v: 0, color: COL[k], on: k === 'surface_event' })));
  noiseBox.innerHTML = barRows([{ label: NAME.noise, v: 0, color: COL.noise }]);
  const setBar = (row, v, tip) => {
    row.querySelector('.hv').textContent = v === null ? '–' : pct(v);
    row.querySelector('.ht div').style.width = (v || 0) + '%';
    row.dataset.tip = tip;
  };

  function pick(i) {
    const s = SETUPS[i], d = s.detect('surface_event');
    seg.querySelectorAll('button').forEach((b, j) => b.setAttribute('aria-pressed', j === i));
    $('#kDetect').textContent = pct(d);
    $('#kLost').textContent = pct(100 - d);
    $('#kNoise').textContent = s.noise === null ? '–' : pct(s.noise);
    ORDER.forEach((k, j) => setBar(box.children[j], s.detect(k), s.detectTip(k)));
    setBar(noiseBox.children[0], s.noise, s.noiseTip);
    $('#dec2').innerHTML = s.decision;
  }
  seg.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pick(+b.dataset.i); });
  pick(0);
}

/* ---------- maps ---------- */
const COS = Math.cos(45.5 * Math.PI / 180), DEG = 60;
const proj = (lon, lat) => [(lon + 127.7) * COS * DEG, (51 - lat) * DEG];
const stateCache = new WeakMap();
function drawStates(svg, geo) {
  if (!stateCache.has(geo)) {
    stateCache.set(geo, geo.features.map(f => f.geometry.coordinates.map(poly => poly.map(ring =>
      'M' + ring.map(([x, y]) => proj(x, y).map(v => v.toFixed(1)).join(' ')).join('L') + 'Z').join('')).join('')));
  }
  stateCache.get(geo).forEach(d => el('path', { d, class: 'state' }, svg));
}
function stateLabel(svg, text, lon, lat, size, anchor = 'start') {
  const [x, y] = proj(lon, lat);
  el('text', { x, y, class: 'stl', 'font-size': size, 'text-anchor': anchor }, svg).textContent = text;
}

/* ---------- 03 wilayah ---------- */
function initRegions(summary, explosions, states) {
  const groups = summary.groups.filter(g => /^K\d$/.test(g.key));
  const byKey = Object.fromEntries(groups.map(g => [g.key, g]));
  $('#kEx').textContent = pct(byKey.K5.pct.explosion);
  $('#kSu').textContent = pct(byKey.K6.pct.surface_event);
  $('#kOffice').textContent = pct(summary.office_hours_share.explosion * 100);

  const svg = $('#regionMap');
  svg.setAttribute('viewBox', '76 69 410 515');
  drawStates(svg, states);
  stateLabel(svg, 'Washington', -120.2, 48.75, 10);
  stateLabel(svg, 'Oregon', -120, 42.35, 10);
  stateLabel(svg, 'Idaho', -116.2, 47.3, 10, 'end');
  stateLabel(svg, 'British Columbia (Kanada)', -125.6, 49.6, 9);

  const exLayer = el('g', {}, svg);
  for (const x of explosions) {
    const [cx, cy] = proj(x.lon, x.lat);
    el('circle', { cx: cx.toFixed(1), cy: cy.toFixed(1), r: 1.5, fill: 'var(--ex)', 'fill-opacity': .3, 'data-tip': `Ledakan · M ${fm[1].format(x.magnitude)}<br>${fmtDate(x.local_time)}` }, exLayer);
  }

  for (const v of summary.volcanoes) {
    const [x, y] = proj(v.lon, v.lat);
    const g = el('g', { 'data-tip': `<b>${v.name}</b> · gunung api` }, svg);
    el('path', { d: `M${x} ${y - 4.5}L${x + 4} ${y + 3}L${x - 4} ${y + 3}Z`, fill: 'var(--volc)', stroke: 'var(--sea)', 'stroke-width': .8 }, g);
    el('circle', { cx: x, cy: y, r: 7, fill: 'transparent' }, g);
  }

  const rings = new Map();
  const sw = 7;
  for (const c of groups) {
    const [x, y] = proj(c.lon, c.lat), R = 6 + 1.35 * Math.sqrt(c.stations);
    const g = el('g', { class: 'hit', tabindex: 0, role: 'button', 'data-tip': `<b>${c.name_id}</b><br>Ledakan ${pct(c.pct.explosion)} · <em>surface event</em> ${pct(c.pct.surface_event)}` }, svg);
    g.setAttribute('aria-label', `${c.name_id}, ${c.stations} stasiun`);
    const disc = el('circle', { class: 'disc', cx: x, cy: y, r: R + 2, fill: 'none', stroke: 'var(--ring)', 'stroke-width': 1 }, g);
    el('circle', { cx: x, cy: y, r: R - sw / 2, fill: 'none', stroke: 'var(--sea)', 'stroke-width': sw + 1.5 }, g);
    let off = 0;
    EVENTS.forEach(k => {
      const v = c.pct[k];
      if (v <= 0) return;
      const len = v >= 99.9 ? 100 : Math.max(v - 1, .4);
      el('circle', { cx: x, cy: y, r: R - sw / 2, fill: 'none', stroke: COL[k], 'stroke-width': sw, pathLength: 100, 'stroke-dasharray': `${len} ${100 - len}`, 'stroke-dashoffset': -off, transform: `rotate(-90 ${x} ${y})` }, g);
      off += v;
    });
    const left = c.lon > -117.5;
    el('text', { x: left ? x - R - 5 : x + R + 5, y: y + 3.5, 'text-anchor': left ? 'end' : 'start', 'font-size': 10.5, class: 'lbl' }, g).textContent = c.name_id.replace(/ \(.*\)$/, '');
    const pick = () => select(c.key);
    g.addEventListener('click', pick);
    g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
    rings.set(c.key, disc);
  }
  const selEl = $('#groupSel');
  selEl.innerHTML = groups.map(g => `<option value="${g.key}">${g.name_id}</option>`).join('');
  selEl.addEventListener('change', () => select(selEl.value));

  function select(key) {
    selEl.value = key;
    rings.forEach((d, k) => { d.setAttribute('stroke', k === key ? 'var(--ink)' : 'var(--ring)'); d.setAttribute('stroke-width', k === key ? 2 : 1); });
    const c = byKey[key], note = summary.region_notes[key];
    const lead = ['explosion', 'surface_event'].find(k => c.pct[k] >= 15) || 'earthquake';
    $('#regionDetail').innerHTML = `<div><span class="eyebrow">${fmt(c.stations)} stasiun · ${fmt(c.recordings)} rekaman</span><h3 class="rname">${c.name_id}</h3></div>
      <p class="lead"><b class="num">${fmt(Math.round(c.pct[lead]))} dari 100</b> rekaman adalah ${LOWER[lead]}.</p>
      <div class="hbars">${barRows(EVENTS.map(k => ({ label: NAME[k], v: c.pct[k], color: COL[k] })))}</div>
      ${note ? `<p class="note"><span>${note}</span></p>` : ''}`;
  }
  select('K5');
}

/* ---------- 04 stasiun ---------- */
function initStations(stations, summary, states) {
  const sorted = stations.slice().sort((a, b) => a.pagerank_rank - b.pagerank_rank);
  const top = sorted.slice(0, 10), others = sorted.slice(10);
  const links = top.map(s => s.n_linked);
  $('#kTop').textContent = fmt(top.length);
  $('#kAll').textContent = fmt(stations.length);
  $('#kNb').textContent = fmt(top[0].n_linked);
  $('#dec4').innerHTML = `Anggaran <em>maintenance</em> dan daya cadangan dapat diprioritaskan untuk ${fmt(top.length)} stasiun ini, dikarenakan masing-masing terhubung dengan ${fmt(Math.min(...links))}–${fmt(Math.max(...links))} stasiun lain, walaupun jumlahnya hanya ${pct(100 * top.length / stations.length)} dari ${fmt(stations.length)} stasiun.`;

  const svg = $('#stMap');
  const FULL = { x: 0, y: 0, w: 571, h: 618 };
  const ratio = FULL.h / FULL.w;
  const pts = top.map(s => proj(s.lon, s.lat));
  const [xs, ys] = [pts.map(p => p[0]), pts.map(p => p[1])];
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const w = Math.max(Math.max(...xs) - Math.min(...xs), (Math.max(...ys) - Math.min(...ys)) / ratio) * 1.5;
  const ZOOM = { x: cx - w / 2, y: cy - w * ratio / 2, w, h: w * ratio };
  let highlight = true, sel = top[0].station;

  function render() {
    const v = highlight ? ZOOM : FULL, u = v.w / 480;
    svg.setAttribute('viewBox', `${v.x} ${v.y} ${v.w} ${v.h}`);
    svg.replaceChildren();
    drawStates(svg, states);
    if (highlight) {
      stateLabel(svg, 'Washington', -122.0, 47.95, 10 * u);
      stateLabel(svg, 'Oregon', -122.6, 45.72, 10 * u);
    } else {
      stateLabel(svg, 'Washington', -120.2, 48.75, 10 * u);
      stateLabel(svg, 'Oregon', -120, 42.35, 10 * u);
      stateLabel(svg, 'Idaho', -115.6, 46.5, 10 * u);
    }
    const dimR = (highlight ? 3 : 2.6) * u;
    for (const s of highlight ? others : sorted) {
      const [x, y] = proj(s.lon, s.lat);
      el('circle', { cx: x, cy: y, r: dimR, fill: 'var(--dim)', 'fill-opacity': .8, 'data-tip': `<span class="mono">${s.station}</span> · ${fmt(s.n_linked)} stasiun terhubung` }, svg);
    }
    if (highlight) {
      const R = 8.5 * u;
      top.forEach((s, i) => { if (s.station !== sel) marker(s, i, R, u); });
      const i = top.findIndex(s => s.station === sel);
      marker(top[i], i, R * 1.15, u, true);
    }
    el('text', { x: v.x + 12 * u, y: v.y + 22 * u, 'font-size': 13 * u, class: 'lbl', style: `stroke-width:${3 * u}px;font-weight:600` }, svg).textContent =
      highlight ? `${fmt(top.length)} dari ${fmt(stations.length)} stasiun` : `${fmt(stations.length)} stasiun`;
    $('#stLegend').innerHTML = highlight
      ? `<span><i class="sw round" style="background:var(--ink)"></i>${fmt(top.length)} stasiun sentral</span><span><i class="sw round" style="background:var(--dim)"></i>${fmt(others.length)} stasiun lain</span>`
      : `<span><i class="sw round" style="background:var(--dim)"></i>Seluruh jaringan: ${fmt(stations.length)} stasiun</span>`;
  }
  function marker(s, i, R, u, on) {
    const [x, y] = proj(s.lon, s.lat);
    const g = el('g', { class: 'hit', tabindex: 0, role: 'button', 'data-tip': `<b>#${i + 1} <span class="mono">${s.station}</span></b><br>${fmt(s.n_linked)} stasiun terhubung`, 'aria-label': `Peringkat ${i + 1}, ${s.station}` }, svg);
    el('circle', { class: 'disc', cx: x, cy: y, r: R, fill: 'var(--ink)', stroke: 'var(--surface)', 'stroke-width': (on ? 2 : 1.2) * u }, g);
    el('text', { x, y: y + 3.6 * u, 'text-anchor': 'middle', 'font-size': 10 * u, 'font-weight': 700, fill: 'var(--surface)' }, g).textContent = i + 1;
    if (on) {
      const right = x < ZOOM.x + ZOOM.w * .75;
      el('text', { x: x + (right ? R + 4 * u : -R - 4 * u), y: y + 4 * u, 'text-anchor': right ? 'start' : 'end', 'font-size': 12 * u, class: 'lbl', style: `stroke-width:${3 * u}px` }, g).textContent = s.station;
    }
    const pick = () => choose(s.station);
    g.addEventListener('click', pick);
    g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
  }
  const L = $('#rankList'), toggle = $('#hlToggle');
  function choose(station) {
    sel = station;
    highlight = toggle.checked = true;
    render();
    list();
  }
  function list() {
    L.innerHTML = top.map((s, i) => `<button type="button" data-s="${s.station}" aria-pressed="${s.station === sel}"><span class="r num">${i + 1}</span><span class="c">${s.station}</span><span class="l num">${fmt(s.n_linked)} stasiun terhubung</span></button>`).join('');
    const s = top.find(x => x.station === sel), i = top.indexOf(s);
    $('#stDetail').innerHTML = `<b class="mono">${s.station}</b><span>Peringkat ${i + 1}. Terhubung dengan ${fmt(s.n_linked)} stasiun. Merekam ${fmt(s.n_events)} kejadian.</span>`;
  }
  L.addEventListener('click', e => { const b = e.target.closest('button'); if (b) choose(b.dataset.s); });
  toggle.addEventListener('change', () => { highlight = toggle.checked; render(); });
  render();
  list();
}
