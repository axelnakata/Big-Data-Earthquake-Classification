"""Diagram alur end-to-end untuk README (download → HDFS → Spark → CNN → graph). Tanpa data, cukup matplotlib."""
import os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'outputs', 'figures', 'readme_pipeline.png')
A1, A2, EDGE = '#e8e8e8', '#dce7f3', '#333333'

# (judul, italic?, baris detail, warna) — baris 1 kiri→kanan, baris 2 kanan→kiri
ROW1 = [('Pengumpulan data', False, 'PNW-ML: 3 CSV + 3 HDF5\n±90 GB, batch download', A1),
        ('Penyimpanan HDFS', False, 'Raw zone, 675 blok\nread-only, cek SHA-256', A1),
        ('Cleaning & konversi', False, 'Spark: 237.978 rekaman\nHDF5 → Parquet', A1),
        ('Preprocessing', True, 'Komponen Z, 0–150 s\nz-score, split 70/15/15', A2)]
ROW2 = [('Feature engineering', True, '9 fitur konteks\n+ random crop 120 s', A2),
        ('Training CNN', False, 'PyTorch via Spark\nTorchDistributor (5 proses)', A2),
        ('Evaluasi', False, 'Spark predict_batch_udf\nmacro-F1 0,861 (test)', A2),
        ('Graph analytics', True, 'GraphFrames: G1 & G2\nPageRank, label propagation', A2)]

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'STIX Two Text', 'STIXGeneral'], 'font.size': 10})
fig, ax = plt.subplots(figsize=(12, 3.5))
ax.set_xlim(0, 12); ax.set_ylim(0.4, 3.9); ax.axis('off')
W, H, XS, Y1, Y2 = 2.25, 1.05, [1.35, 3.95, 6.55, 9.15], 2.35, 0.6


def box(x, y, title, ital, detail, fc):
    ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle='square,pad=0', fc=fc, ec=EDGE, lw=1.1))
    ax.text(x + W / 2, y + H - 0.25, title, ha='center', va='center', fontweight='bold', fontsize=11.5,
            fontstyle='italic' if ital else 'normal')
    ax.text(x + W / 2, y + 0.38, detail, ha='center', va='center', fontsize=9.5, linespacing=1.25)


def pill(x, y, label):
    ax.add_patch(FancyBboxPatch((x, y + H / 2 - 0.2), 0.8, 0.4, boxstyle='round,pad=0,rounding_size=0.2', fc='#3a3a3a', ec='black'))
    ax.text(x + 0.4, y + H / 2, label, ha='center', va='center', color='white', fontweight='bold', fontsize=10.5)


def arrow(x0, y0, x1, y1):
    ax.annotate('', (x1, y1), (x0, y0), arrowprops=dict(arrowstyle='-|>', color=EDGE, lw=1.2, mutation_scale=12))


pill(0.2, Y1, 'Mulai'); arrow(1.0, Y1 + H / 2, XS[0], Y1 + H / 2)
for i, (x, b) in enumerate(zip(XS, ROW1)):
    box(x, Y1, *b)
    if i < 3: arrow(x + W, Y1 + H / 2, XS[i + 1], Y1 + H / 2)
arrow(XS[3] + W / 2, Y1, XS[3] + W / 2, Y2 + H)
for i, (x, b) in enumerate(zip(XS[::-1], ROW2)):
    box(x, Y2, *b)
    if i < 3: arrow(x, Y2 + H / 2, XS[::-1][i + 1] + W, Y2 + H / 2)
pill(0.2, Y2, 'Selesai'); arrow(XS[0], Y2 + H / 2, 1.0, Y2 + H / 2)
ax.legend(handles=[Patch(fc=A1, ec=EDGE, label='Assignment 1 (data)'), Patch(fc=A2, ec=EDGE, label='Assignment 2 (ML & graph)')],
          loc='upper center', bbox_to_anchor=(0.5, 1.06), ncol=2, frameon=False, fontsize=10)
fig.savefig(OUT, dpi=200, bbox_inches='tight', facecolor='white')
