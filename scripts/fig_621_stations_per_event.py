"""Gambar 6.2.1: sebaran jumlah stasiun per kejadian, per kelas. Read-only dari /datalake/graph/g1_*."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from common import HDFS, spark_session
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

FIG = os.path.join(ROOT, 'outputs', 'figures')
FACTS = os.path.join(ROOT, '_private', 'a2_notes', 'gambar_bab6')  # gitignored
spark = spark_session('fig621', driver_mem='4g')
e = spark.read.parquet(f'{HDFS}/datalake/graph/g1_edges')
v = spark.read.parquet(f'{HDFS}/datalake/graph/g1_vertices').where("kind='event'").select('id', 'label')
pdf = e.groupBy('src').count().toPandas().rename(columns={'count': 'n'})
vp = v.toPandas()
df = vp.merge(pdf, left_on='id', right_on='src', how='left')
assert df.n.notna().all(), 'ada kejadian tanpa edge'
df['n'] = df.n.astype(int)

classes = [('earthquake', 'Gempa bumi'), ('explosion', 'Ledakan'), ('surface_event', 'Peristiwa permukaan')]
bins, names = [0, 1, 3, 9, 10**9], ['1 stasiun', '2–3 stasiun', '4–9 stasiun', '≥ 10 stasiun']
df['grp'] = pd.cut(df.n, bins=bins, labels=names)
cnt = df.groupby(['label', 'grp'], observed=False).size().unstack().loc[[c for c, _ in classes]]
pct = cnt.div(cnt.sum(1), axis=0) * 100
tot = cnt.sum(1)
stat = df.groupby('label').n.agg(['mean', 'median']).loc[[c for c, _ in classes]]

fmt = lambda x, d=1: f'{x:.{d}f}'.replace('.', ',')
nid = lambda n: f'{n:,}'.replace(',', '.')

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'STIX Two Text', 'STIXGeneral'],
                     'mathtext.fontset': 'stix', 'pdf.fonttype': 42, 'ps.fonttype': 42, 'font.size': 9})
cols = ['#1b2a41', '#3f5f8a', '#8fa9c9', '#d3deec']
fig, ax = plt.subplots(figsize=(15.9 / 2.54, 6 / 2.54))
y = np.arange(len(classes))[::-1]
left = np.zeros(len(classes))
for i, g in enumerate(names):
    w = pct[g].values
    ax.barh(y, w, left=left, color=cols[i], edgecolor='white', linewidth=0.6, height=0.6)
    for yi, l, wi in zip(y, left, w):
        if wi >= 4:
            ax.text(l + wi / 2, yi, fmt(wi) + '%', ha='center', va='center', fontsize=9,
                    color='white' if i < 2 else 'black')
    left += w
ax.set_yticks(y, [f'{n} (n = {nid(tot[c])})' for c, n in classes])
ax.set_xlim(0, 100); ax.set_xlabel('Persentase kejadian (%)')
for s in ('top', 'right'): ax.spines[s].set_visible(False)
ax.legend([plt.Rectangle((0, 0), 1, 1, color=c) for c in cols], ['1', '2–3', '4–9', '≥ 10'],
          title='Jumlah stasiun yang merekam satu kejadian:', title_fontsize=9, fontsize=9, ncol=4,
          loc='lower center', bbox_to_anchor=(0.4, 1.0), frameon=False, handlelength=1.2, columnspacing=1.2)
ax.legend_._legend_box.align = 'left'
fig.tight_layout()
fig.savefig(f'{FIG}/a2_graph_stations_per_event.pdf')
fig.savefig(f'{FIG}/a2_graph_stations_per_event.png', dpi=200)

L = ['# Fakta Gambar 6.2.1 — jumlah stasiun per kejadian', '',
     'Sumber: `/datalake/graph/g1_edges` + `g1_vertices` (read-only). Jumlah stasiun per kejadian = degree vertex kejadian (1 edge = 1 pasangan kejadian–stasiun).', '',
     '## 1. Kelas × kelompok (jumlah kejadian, % dari kelas)', '',
     '| Kelas | n | ' + ' | '.join(names) + ' |', '|---|---|' + '---|' * 4]
for c, n in classes:
    L.append(f'| {n} | {nid(tot[c])} | ' + ' | '.join(f'{nid(cnt.loc[c, g])} ({fmt(pct.loc[c, g])}%)' for g in names) + ' |')
L += ['', '## 2. Rata-rata dan median stasiun per kejadian', '',
      '| Kelas | Rata-rata | Median | % hanya 1 stasiun | Nilai cek (rata-rata / median / % 1 stasiun) |', '|---|---|---|---|---|']
chk = {'earthquake': '4,11 / 3 / 17,5', 'explosion': '2,52 / 2 / 33,7', 'surface_event': '1,64 / 1 / 77,7'}
for c, n in classes:
    L.append(f'| {n} | {fmt(stat.loc[c, "mean"], 2)} | {fmt(stat.loc[c, "median"], 0)} | {fmt(pct.loc[c, names[0]])}% | {chk[c]} |')
L += ['', f'Total kejadian: {nid(int(tot.sum()))}; total edge: {nid(int(df.n.sum()))}.', '']
open(f'{FACTS}/A2_fakta_gambar6.2.1.md', 'w').write('\n'.join(L))
print('\n'.join(L))
