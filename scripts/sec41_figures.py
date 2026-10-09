"""Subbab 4.1 bagian G — visualisasi waveform (grid 2x2, 4 kelas, dua varian).

Aturan pemilihan sampel (Gambar Subbab 4.1):
  - dari data yang sudah dibersihkan (processed/metadata + n_empty_components dari processed/waveforms)
  - tanpa komponen kosong (n_empty_components == 0); tanpa trace_has_offset (hanya ada di ComCat)
  - kelas kejadian (earthquake/explosion/surface_event): SNR komponen Z di persentil 80-95 kelasnya
    (dipilih tinggi, bukan median, supaya bentuk kejadian terlihat jelas dibanding noise latar)
  - utamakan sensor broadband (HH atau BH)
  - noise: cari stasiun yang sama dengan salah satu sampel kejadian bila memungkinkan
  - seed acak tetap = 42

Jalankan dari root project: .venv/bin/python scripts/sec41_figures.py
"""
import json
import os
import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from common import ROOT, HDFS, RAW, PROCESSED, spark_session, webhdfs  # noqa: E402

SEED = 42
FS_HZ = 100.0
OUT_DIR = os.path.join(ROOT, 'outputs', 'figures')
os.makedirs(OUT_DIR, exist_ok=True)

CLASSES = [  # (panel label, dataset, label kolom 'label' di processed/metadata)
    ('(a) Gempa bumi', 'comcat', 'earthquake'),
    ('(b) Ledakan', 'comcat', 'explosion'),
    ('(c) Peristiwa permukaan', 'exotic', 'surface_event'),
    ('(d) Noise', 'noise', 'noise'),
]
DURATION_S = {'comcat': 150, 'exotic': 180, 'noise': 150}


def snr_z(s):
    try:
        parts = str(s).split('|')
        if len(parts) != 3:
            return np.nan
        z = parts[2]
        return np.nan if z == 'nan' else float(z)
    except (ValueError, TypeError):
        return np.nan


def parse_trace_name(tn):
    bucket, rest = tn.split('$')
    idx_str, comp_str, samp_str = rest.split(',')
    return bucket, int(idx_str), int(comp_str.replace(':', '')), int(samp_str.replace(':', ''))


def read_waveform(fs, ds, trace_name):
    bucket, r, n_comp, n_samp = parse_trace_name(trace_name)
    with fs.open(f'{RAW}/{ds}/{ds}_waveforms.hdf5', 'rb') as fo, h5py.File(fo, 'r') as f:
        return f[f'/data/{bucket}'][r, :n_comp, :n_samp].astype(float)  # (3, n_samples), order E,N,Z


def candidates(spark, ds, label):
    """Baris bersih dataset=ds & label=label, broadband, tanpa komponen kosong / offset."""
    meta = spark.read.parquet(f'{HDFS}{PROCESSED}/metadata').filter(f"dataset='{ds}' AND label='{label}'")
    wf = spark.read.parquet(f'{HDFS}{PROCESSED}/waveforms').filter(f"dataset='{ds}'").select('trace_name', 'n_empty_components')
    df = meta.join(wf, 'trace_name').filter('n_empty_components = 0').filter("station_channel_code IN ('HH','BH')")
    if 'flag_has_offset' in df.columns:
        df = df.filter('flag_has_offset = false OR flag_has_offset IS NULL')
    cols = ['trace_name', 'event_id', 'station_network_code', 'station_code', 'station_channel_code',
            'trace_start_time', 'trace_snr_db'] if ds != 'noise' else \
           ['trace_name', 'station_network_code', 'station_code', 'station_channel_code', 'trace_start_time']
    return df.select(*[c for c in cols if c in df.columns]).toPandas()


def pick_event_sample(df, label_name):
    df = df.copy()
    df['snr_z'] = df['trace_snr_db'].map(snr_z)
    df = df.dropna(subset=['snr_z'])
    lo, hi = df['snr_z'].quantile(0.80), df['snr_z'].quantile(0.95)
    band = df[(df['snr_z'] >= lo) & (df['snr_z'] <= hi)]
    if band.empty:
        band = df
    row = band.sample(1, random_state=SEED).iloc[0]
    pct = float((df['snr_z'] <= row['snr_z']).mean() * 100)
    row = row.copy()
    row['snr_z_percentile_in_class'] = round(pct, 1)
    return row


def pick_noise_sample(df, preferred_stations):
    same_station = df[df['station_code'].isin(preferred_stations)]
    pool = same_station if not same_station.empty else df
    return pool.sample(1, random_state=SEED).iloc[0]


def style_axes(ax):
    ax.tick_params(labelsize=8, width=0.5)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_linewidth(0.5)


def main():
    plt.rcParams['font.family'] = ['Times New Roman', 'Liberation Serif', 'serif']
    plt.rcParams['font.size'] = 10

    spark = spark_session('figures_41')
    fs = webhdfs()

    picked = {}
    for label, ds, cls in CLASSES:
        cand = candidates(spark, ds, cls)
        if ds == 'noise':
            continue  # dipilih setelah tahu stasiun kelas kejadian
        picked[label] = (ds, pick_event_sample(cand, cls))
    spark.stop()  # noise dipilih dgn spark baru agar driver tidak menahan memori lama

    event_stations = [row['station_code'] for _, row in picked.values()]
    spark = spark_session('figures_41_noise')
    noise_cand = candidates(spark, 'noise', 'noise')
    picked['(d) Noise'] = ('noise', pick_noise_sample(noise_cand, event_stations))
    spark.stop()

    order = ['(a) Gempa bumi', '(b) Ledakan', '(c) Peristiwa permukaan', '(d) Noise']
    signals, table = {}, []
    for label in order:
        ds, row = picked[label]
        z = read_waveform(fs, ds, row['trace_name'])[2]
        signals[label] = (ds, z)
        table.append({
            'kelas': label, 'dataset': ds, 'trace_name': row['trace_name'],
            'event_id': str(row.get('event_id', '')), 'station_code': row.get('station_code'),
            'station_channel_code': row.get('station_channel_code'),
            'trace_start_time': str(row.get('trace_start_time')),
            'snr_z_db': None if 'snr_z' not in row else round(float(row['snr_z']), 2),
            'snr_z_percentile_in_class': row.get('snr_z_percentile_in_class'),
            'z_abs_max_counts': round(float(np.max(np.abs(z))), 1),
        })

    with open(os.path.join(ROOT, 'outputs', 'facts', '41_sampel_gambar.json'), 'w') as f:
        json.dump(table, f, indent=2, default=str)
    print(json.dumps(table, indent=2, default=str))

    cm = 1 / 2.54
    for variant, fname, ylabel, normalize in (
        ('A', '41_waveform_4kelas_A', 'Amplitudo (dinormalisasi)', True),
        ('B', '41_waveform_4kelas_B', 'Amplitudo (counts)', False),
    ):
        fig, axes = plt.subplots(2, 2, figsize=(16 * cm, 9 * cm), dpi=300)
        for ax, label in zip(axes.flat, order):
            ds, z = signals[label]
            t = np.arange(z.size) / FS_HZ
            y = z / (np.max(np.abs(z)) or 1.0) if normalize else z
            ax.plot(t, y, color='black', lw=0.5)
            ax.set_xlim(0, DURATION_S[ds])
            if normalize:
                ax.set_ylim(-1.1, 1.1)
            ax.set_title(label, fontsize=10, loc='left')
            style_axes(ax)
        # setiap panel independen (TIDAK sharex) -> tick angka ditampilkan di semua panel
        # supaya durasi 150 dtk (comcat/noise) vs 180 dtk (exotic) terlihat jelas berbeda;
        # hanya teks label sumbu ("Waktu sejak...") yang ditulis sekali di baris bawah.
        for ax in axes[1, :]:
            ax.set_xlabel('Waktu sejak awal rekaman (detik)', fontsize=9)
        fig.supylabel(ylabel, fontsize=9)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_DIR, f'{fname}.png'), facecolor='white')
        fig.savefig(os.path.join(OUT_DIR, f'{fname}.pdf'), facecolor='white')
        plt.close(fig)

    # gambar tambahan (opsional): 3 komponen, sampel yang sama dengan panel (a)
    ds_a, row_a = picked['(a) Gempa bumi']
    e, n, z = read_waveform(fs, ds_a, row_a['trace_name'])
    t = np.arange(z.size) / FS_HZ
    fig, axes = plt.subplots(3, 1, figsize=(16 * cm, 10 * cm), dpi=300, sharex=True)
    for ax, comp, name in zip(axes, (e, n, z), ('E', 'N', 'Z')):
        ax.plot(t, comp, color='black', lw=0.5)
        ax.set_xlim(0, DURATION_S[ds_a])
        ax.set_title(f'Komponen {name}', fontsize=10, loc='left')
        style_axes(ax)
    axes[-1].set_xlabel('Waktu sejak awal rekaman (detik)', fontsize=9)
    fig.supylabel('Amplitudo (counts)', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, '41_waveform_3komponen.png'), facecolor='white')
    fig.savefig(os.path.join(OUT_DIR, '41_waveform_3komponen.pdf'), facecolor='white')
    plt.close(fig)
    print('done ->', OUT_DIR)


if __name__ == '__main__':
    main()
