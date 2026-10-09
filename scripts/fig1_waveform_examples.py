"""
Gambar 1 — Contoh waveform empat sumber getaran (dari data asli PNW-ML di HDFS).

Style matches Gambar 2/3/5 in the report: serif font, black & white, 300 dpi.
Reads metadata + waveforms directly from HDFS over WebHDFS (no local copy).

Plots the vertical (Z) component, located via the HDF5 component order (ENZ).
Output: outputs/figures/gambar1_waveform.png + outputs/facts/gambar1_selection.json (traces used).

Run from the project root: .venv/bin/python scripts/fig1_waveform_examples.py
"""
import json
import os
import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from common import webhdfs, RAW, ROOT, OUT_FIGS  # noqa: E402

OUT_DIR = OUT_FIGS
SEED = 42
FS_HZ = 100.0

PANELS = [  # (dataset, source_type value, label in report, min mean SNR)
    ("comcat", "earthquake", "(a) Gempa bumi", 20),
    ("comcat", "explosion", "(b) Ledakan", 20),
    ("exotic", "surface event", "(c) Peristiwa permukaan", 10),
    ("noise", None, "(d) Noise", None),
]


def read_meta(fs, ds):
    with fs.open(f"{RAW}/{ds}/{ds}_metadata.csv", "rb") as f:
        return pd.read_csv(f, low_memory=False)


def mean_snr(s):
    try:
        vals = [float(v) for v in str(s).split("|") if v not in ("", "nan")]
        return np.mean(vals) if vals else np.nan
    except ValueError:
        return np.nan


def pick_row(df, source_type, min_snr):
    d = df.copy()
    if source_type is not None:
        d = d[d["source_type"] == source_type]
    for col in ("trace_missing_channel", "trace_has_offset"):
        if col in d.columns:
            d = d[d[col].fillna(0) == 0]
    if min_snr is not None and "trace_snr_db" in d.columns:
        snr = d["trace_snr_db"].map(mean_snr)
        d = d[(snr >= min_snr) & (snr <= 40)]
    if d.empty:
        raise RuntimeError(f"No candidate rows for {source_type}")
    return d.sample(1, random_state=SEED).iloc[0]


def z_index(h5):
    order = None
    if "data_format" in h5:
        g = h5["data_format"]
        if "component_order" in g:
            order = g["component_order"][()]
        elif "component_order" in g.attrs:
            order = g.attrs["component_order"]
    if isinstance(order, bytes):
        order = order.decode()
    if order and "Z" in str(order).upper():
        return str(order).upper().index("Z"), str(order)
    print("WARNING: component order not found; plotting index 2")
    return 2, None


def read_trace(fs, ds, trace_name):
    bucket, arr = trace_name.split("$")
    x, y, z = [int(v) for v in arr.split(",:")]
    with fs.open(f"{RAW}/{ds}/{ds}_waveforms.hdf5", "rb") as f, h5py.File(f, "r") as h5:
        zi, order = z_index(h5)
        data = h5[f"/data/{bucket}"][x, :y, :z]
    return data[zi].astype(float), order


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    fs = webhdfs()
    metas = {ds: read_meta(fs, ds) for ds in {p[0] for p in PANELS}}

    plt.rcParams["font.family"] = ["Times New Roman", "Liberation Serif", "serif"]
    fig, axes = plt.subplots(4, 1, figsize=(6.5, 6.4), dpi=300)
    chosen = []

    for ax, (ds, stype, label, min_snr) in zip(axes, PANELS):
        row = pick_row(metas[ds], stype, min_snr)
        sig, order = read_trace(fs, ds, row["trace_name"])
        sig = sig - np.mean(sig)
        sig = sig / (np.max(np.abs(sig)) or 1.0)
        t = np.arange(sig.size) / FS_HZ

        ax.plot(t, sig, color="black", lw=0.45)
        p = row.get("trace_P_arrival_sample", np.nan)
        if pd.notna(p):
            ax.axvline(float(p) / FS_HZ, color="black", ls="--", lw=0.8)
        ax.set_xlim(0, t[-1]); ax.set_ylim(-1.1, 1.1); ax.set_yticks([-1, 0, 1])
        ax.text(0.01, 0.93, label, transform=ax.transAxes, va="top", fontsize=9,
                fontweight="bold", bbox=dict(fc="white", ec="none", pad=1))
        ax.tick_params(labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

        chosen.append({"panel": label, "dataset": ds, "trace_name": row["trace_name"],
                       "event_id": str(row.get("event_id")), "source_type": str(row.get("source_type")),
                       "station": f'{row.get("station_network_code")}.{row.get("station_code")}.'
                                  f'{row.get("station_channel_code")}',
                       "component_order": order, "n_samples": int(sig.size)})

    axes[-1].set_xlabel("Waktu sejak awal rekaman (detik)", fontsize=9)
    fig.supylabel("Amplitudo (dinormalisasi)", fontsize=9)
    axes[0].plot([], [], color="black", ls="--", lw=0.8, label="Waktu tiba gelombang P")
    axes[0].legend(loc="upper right", fontsize=7.5, frameon=False)
    fig.tight_layout(h_pad=0.6)

    fig.savefig(os.path.join(OUT_DIR, "gambar1_waveform.png"), facecolor="white")
    with open(os.path.join(ROOT, "outputs", "facts", "gambar1_selection.json"), "w") as f:
        json.dump(chosen, f, indent=2)
    print(json.dumps(chosen, indent=2))


if __name__ == "__main__":
    main()
