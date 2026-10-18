"""Gambar 6.2.3: peta kelompok stasiun (label propagation pada G2). Jalankan ulang LPA, cek ukuran, lalu gambar."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from common import HDFS, spark_session
import numpy as np, pandas as pd, shapefile
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.patheffects as pe

FIG = os.path.join(ROOT, 'outputs', 'figures')
FACTS = os.path.join(ROOT, '_private', 'a2_notes', 'gambar_bab6')  # gitignored
NE = os.path.expanduser('~/pnwml-data/tmp/ne')
EXPECT = [246, 125, 61, 48, 24, 22, 12, 7]; EXPECT_SMALL_N, EXPECT_SMALL_SUM, EXPECT_ISO = 2, 10, 87

spark = spark_session('fig623', driver_mem='6g', packages='io.graphframes:graphframes-spark3_2.12:0.12.3')
spark.sparkContext.setCheckpointDir(os.path.expanduser('~/pnwml-data/tmp/graph-ckpt'))
from graphframes import GraphFrame
from pyspark.sql import functions as F

G = f'{HDFS}/datalake/graph'
v2 = spark.read.parquet(f'{G}/g2_vertices'); e2 = spark.read.parquet(f'{G}/g2_edges')
e2b = e2.unionByName(e2.select(F.col('dst').alias('src'), F.col('src').alias('dst'), 'weight'))
lp = GraphFrame(v2, e2b).labelPropagation(maxIter=10).select('id', 'label')
lp.write.mode('overwrite').parquet(f'{G}/g2_communities')
lp = spark.read.parquet(f'{G}/g2_communities').toPandas()
nb = e2b.groupBy('src').count().toPandas().rename(columns={'src': 'id', 'count': 'tetangga'})
st = v2.toPandas().merge(lp, on='id').merge(nb, on='id', how='left').fillna({'tetangga': 0})
assert st.id.is_unique
st['community'] = np.where(st.tetangga == 0, 'iso', st.label.astype(str))
sizes = st[st.community != 'iso'].community.value_counts()
got = dict(top8=list(sizes.iloc[:8]), small_n=len(sizes) - 8, small_sum=int(sizes.iloc[8:].sum()), iso=int((st.community == 'iso').sum()))
ok = got == dict(top8=EXPECT, small_n=EXPECT_SMALL_N, small_sum=EXPECT_SMALL_SUM, iso=EXPECT_ISO)
head = ['# Fakta Peta 6.2.3 — kelompok stasiun', '', '## Cek ulang label propagation (maxIter=10, G2 bobot ≥ 5)', '',
        '| | Lama (laporan) | Baru (dijalankan ulang) |', '|---|---|---|',
        f'| 8 kelompok terbesar | {EXPECT} | {got["top8"]} |',
        f'| kelompok kecil (jumlah / total stasiun) | {EXPECT_SMALL_N} / {EXPECT_SMALL_SUM} | {got["small_n"]} / {got["small_sum"]} |',
        f'| terisolasi | {EXPECT_ISO} | {got["iso"]} |', '', f'Hasil: **{"SAMA" if ok else "BERBEDA — peta tidak dibuat"}**', '']
print('\n'.join(head))
if not ok:
    open(f'{FACTS}/A2_fakta_peta6.2.3.md', 'w').write('\n'.join(head)); sys.exit('ukuran kelompok berbeda, STOP')

names = {c: f'K{i + 1}' for i, c in enumerate(sizes.index[:8])}
st['k'] = st.community.map(names)
LEG = ['Washington barat', 'Washington barat daya – Oregon utara', 'Washington timur', 'Oregon barat daya',
       'Oregon barat tengah', 'Oregon tengah, pemantau gunung api', 'Oregon timur laut', 'Perbatasan Oregon–Idaho']
cols = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9', '#8c6d1f', '#444444']  # Okabe-Ito
X0, X1, Y0, Y1 = -125, -116, 41.8, 49.2

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'STIX Two Text', 'STIXGeneral'],
                     'mathtext.fontset': 'stix', 'pdf.fonttype': 42, 'ps.fonttype': 42, 'font.size': 9})
fig = plt.figure(figsize=(15.9 / 2.54, 10 / 2.54)); ax = fig.add_axes([0.095, 0.13, 0.36, 0.84])
def draw(path, keep=None):
    r = shapefile.Reader(path)
    for sr in r.shapeRecords():
        if keep and sr.record['name'] not in keep: continue
        pts = np.array(sr.shape.points); parts = list(sr.shape.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            ax.plot(pts[a:b, 0], pts[a:b, 1], color='#b0b0b0', lw=0.6, zorder=1)
note = 'Batas wilayah: Natural Earth 1:50m (admin-1 dan garis pantai).'
try:
    draw(f'{NE}/a1/ne_50m_admin_1_states_provinces.shp', {'Washington', 'Oregon', 'Idaho'}); draw(f'{NE}/co/ne_50m_coastline.shp')
    for t, x, y, rot in [('WASHINGTON', -119.9, 48.85, 0), ('OREGON', -119.6, 42.65, 0), ('IDAHO', -116.3, 45.6, 90)]:
        ax.text(x, y, t, ha='center', va='center', rotation=rot, color='#8a8a8a', fontsize=9, zorder=2,
                path_effects=[pe.withStroke(linewidth=2.5, foreground='white')])
except Exception as ex:
    note = f'Batas wilayah tidak dapat dimuat ({ex}); peta tanpa latar.'
inside = st.lon.between(X0, X1) & st.lat.between(Y0, Y1)
for i in range(8):
    g = st[st.k == f'K{i + 1}']
    ax.scatter(g.lon, g.lat, s=14, color=cols[i], edgecolor='white', linewidth=0.3, zorder=3,
               label=f'K{i + 1} {LEG[i]} ({len(g)})')
ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1)
ax.set_aspect(1 / np.cos(np.radians(45.5)))
ax.set_xticks(range(-124, -115, 2)); ax.set_yticks(range(42, 50, 2))
ax.set_xlabel('Bujur (°)'); ax.set_ylabel('Lintang (°)')
for s in ('top', 'right'): ax.spines[s].set_visible(False)
fig.legend(*ax.get_legend_handles_labels(), loc='center left', bbox_to_anchor=(0.47, 0.5), frameon=False, fontsize=9, handletextpad=0.1, borderaxespad=0)
fig.savefig(f'{FIG}/a2_graph_communities_map_v2.pdf'); fig.savefig(f'{FIG}/a2_graph_communities_map_v2.png', dpi=200)

shown = st[st.k.notna()]
out = shown[~inside[shown.index]]
tail = ['## Peta', '', f'- Stasiun K1–K8 ditampilkan: {len(shown)}; di luar batas peta (terpotong): {len(out)}'
        + (' — ' + ', '.join(f'{k}: {n}' for k, n in out.k.value_counts().sort_index().items()) if len(out) else ''),
        f'- Tidak ditampilkan: kelompok kecil {got["small_sum"]} stasiun + terisolasi {got["iso"]} stasiun = {got["small_sum"] + got["iso"]}',
        f'- Hasil LPA disimpan: `/datalake/graph/g2_communities` (Parquet, kolom id, label)', f'- {note}', '']
open(f'{FACTS}/A2_fakta_peta6.2.3.md', 'w').write('\n'.join(head + tail)); print('\n'.join(tail))
