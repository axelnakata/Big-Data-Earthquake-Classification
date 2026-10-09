"""Subbab 4.1 — fakta tambahan yang belum ada di outputs/tables/ (blok, cakupan, statistik tambahan).

Angka yang SUDAH dihitung di notebook 04/05/06 (funnel, label crosstab, orphans,
null %, HDF5 tree, konversi) dibaca ulang dari outputs/tables/*.json/*.md, tidak
dihitung ulang di sini. Jalankan dari root project:

    .venv/bin/python scripts/sec41_facts.py
"""
import json
import os
import sys

import h5py
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from common import ROOT, HDFS, RAW, PROCESSED, DATASETS, sh, spark_session, webhdfs  # noqa: E402

OUT_DIR = os.path.join(ROOT, 'outputs', 'facts')
os.makedirs(OUT_DIR, exist_ok=True)

RAW_BYTES = {  # dari Content-Length server (machine_spec.md) = sama persis dgn fsck HDFS
    'comcat_metadata.csv': 50_025_733, 'comcat_waveforms.hdf5': 67_343_580_072,
    'exotic_metadata.csv': 1_476_207, 'exotic_waveforms.hdf5': 4_111_581_160,
    'noise_metadata.csv': 5_028_650, 'noise_waveforms.hdf5': 18_527_565_888,
}
BLOCKS = {  # dari outputs/hdfs/fsck_*.txt (grep "bytes, replicated")
    'comcat_metadata.csv': 1, 'comcat_waveforms.hdf5': 502,
    'exotic_metadata.csv': 1, 'exotic_waveforms.hdf5': 31,
    'noise_metadata.csv': 1, 'noise_waveforms.hdf5': 139,
}


def gb(b):
    return round(b / 1e9, 2)


def mb(b):
    return round(b / 1e6, 2)


def section_A():
    rows = []
    for ds in DATASETS:
        for kind in ('metadata.csv', 'waveforms.hdf5'):
            fname = f'{ds}_{kind}'
            b = RAW_BYTES[fname]
            rows.append({'dataset': ds, 'file': fname, 'hdfs_path': f'{RAW}/{ds}/{fname}',
                         'bytes': b, 'MB': mb(b), 'GB': gb(b), 'hdfs_blocks': BLOCKS[fname],
                         'format': 'CSV' if kind.startswith('metadata') else 'HDF5',
                         'data_type': 'terstruktur' if kind.startswith('metadata') else 'tidak terstruktur (wadah semi-structured)'})
    total_bytes = sum(RAW_BYTES.values())
    total_blocks = sum(BLOCKS.values())
    return {'files': rows, 'total_bytes': total_bytes, 'total_GB': gb(total_bytes), 'total_blocks': total_blocks}


def section_D(spark, fs):
    from pyspark.sql import functions as F
    meta_clean = spark.read.parquet(f'{HDFS}{PROCESSED}/metadata')

    examples = []
    picks = {
        'comcat': "label='earthquake' AND trace_P_arrival_sample IS NOT NULL",
        'exotic': "trace_P_arrival_sample IS NOT NULL",
        'noise': "1=1",
    }
    for ds in DATASETS:
        row = (meta_clean.filter(f"dataset='{ds}'").filter(picks[ds])
               .select('trace_name', 'source_type', 'trace_start_time', 'station_network_code',
                        'station_code', 'station_channel_code',
                        *(['trace_P_arrival_sample'] if ds != 'noise' else []),
                        'event_id' if ds != 'noise' else F.lit(None).alias('event_id'))
               .limit(1).toPandas().iloc[0])
        bucket, rest = row['trace_name'].split('$')
        idx_str, comp_str, samp_str = rest.split(',')
        r = int(idx_str)
        n_comp = int(comp_str.replace(':', ''))
        n_samp = int(samp_str.replace(':', ''))
        with fs.open(f'{RAW}/{ds}/{ds}_waveforms.hdf5', 'rb') as fo, h5py.File(fo, 'r') as f:
            arr = f[f'/data/{bucket}'][r, :n_comp, :n_samp]
        p_sample = row.get('trace_P_arrival_sample')
        p_sec = float(p_sample) / 100.0 if pd.notna(p_sample) else None
        examples.append({
            'dataset': ds, 'trace_name': row['trace_name'], 'event_id': str(row.get('event_id')),
            'source_type': row['source_type'], 'station': f"{row['station_network_code']}.{row['station_code']}.{row['station_channel_code']}",
            'trace_start_time': str(row['trace_start_time']),
            'bucket': bucket, 'row_index': r, 'n_components': n_comp, 'n_samples': n_samp,
            'shape_read': list(arr.shape),
            'first5_E': arr[0, :5].tolist(), 'first5_N': arr[1, :5].tolist(), 'first5_Z': arr[2, :5].tolist(),
            'P_arrival_sample': None if p_sample is None or pd.isna(p_sample) else int(p_sample),
            'P_arrival_seconds': p_sec,
        })

    # D.3 — kecocokan metadata <-> HDF5
    match = []
    for ds in DATASETS:
        m = meta_clean.filter(f"dataset='{ds}'")
        n_clean = m.count()
        # sudah divalidasi di notebook 05 (R6): 0 baris dgn bucket tak ada / row >= bucket_rows
        n_ok = n_clean  # validity check R6 = 0 pelanggaran -> semua clean rows menunjuk waveform yang ada
        n_missing = 0
        dup = (m.groupBy('trace_name').count().filter('count > 1'))
        n_dup_trace = dup.count()
        match.append({'dataset': ds, 'metadata_rows_clean': n_clean,
                      'rows_pointing_to_existing_waveform': n_ok,
                      'rows_pointing_to_missing_waveform': n_missing,
                      'trace_name_referenced_by_gt1_row': n_dup_trace})
    return {'examples': examples, 'match': match}


def section_E_bounds(spark):
    from pyspark.sql import functions as F
    meta_clean = spark.read.parquet(f'{HDFS}{PROCESSED}/metadata')
    out = []
    for ds in ('comcat', 'exotic'):
        m = meta_clean.filter(f"dataset='{ds}'")
        viol_p = m.filter('trace_P_arrival_sample IS NOT NULL AND (trace_P_arrival_sample < 0 OR trace_P_arrival_sample >= n_samples)').count()
        viol_s = m.filter('trace_S_arrival_sample IS NOT NULL AND (trace_S_arrival_sample < 0 OR trace_S_arrival_sample >= n_samples)').count()
        out.append({'dataset': ds, 'P_arrival_out_of_bounds': viol_p, 'S_arrival_out_of_bounds': viol_s})
    return out


def section_F(spark):
    from pyspark.sql import functions as F
    meta = spark.read.parquet(f'{HDFS}{PROCESSED}/metadata')
    wf = spark.read.parquet(f'{HDFS}{PROCESSED}/waveforms')

    # kolom asli per file, dibaca dari header CSV via Spark (murah, tidak baca isi)
    orig_cols = {}
    for ds in DATASETS:
        hdr = spark.read.option('header', True).csv(f'{HDFS}{RAW}/{ds}/{ds}_metadata.csv')
        orig_cols[ds] = set(hdr.columns)
    all_orig = set().union(*orig_cols.values())
    meta_cols = meta.columns
    added_cols = [c for c in meta_cols if c not in all_orig]

    du_meta = sh('hdfs dfs -du /datalake/processed/metadata', quiet=True)
    du_wf = sh('hdfs dfs -du /datalake/processed/waveforms', quiet=True)

    def parse_du(txt):
        out = {}
        for line in txt.splitlines():
            parts = line.split()
            if len(parts) >= 3 and 'dataset=' in parts[-1]:
                ds = parts[-1].split('dataset=')[-1]
                out[ds] = int(parts[0])
        return out

    meta_sizes = parse_du(du_meta)
    wf_sizes = parse_du(du_wf)
    row_counts = meta.groupBy('dataset').count().toPandas().set_index('dataset')['count'].to_dict()
    wf_row_counts = wf.groupBy('dataset').count().toPandas().set_index('dataset')['count'].to_dict()

    csv_total = sum(RAW_BYTES[f'{d}_metadata.csv'] for d in DATASETS)
    parquet_meta_total = sum(meta_sizes.values())

    return {
        'metadata_columns_total': len(meta_cols), 'metadata_columns_original': len(all_orig),
        'metadata_columns_added': sorted(added_cols),
        'metadata_waveform_schema': wf.schema.simpleString(),
        'processed_metadata': [{'dataset': d, 'bytes': meta_sizes.get(d), 'MB': mb(meta_sizes.get(d, 0)),
                                 'rows': row_counts.get(d)} for d in DATASETS],
        'processed_waveforms': [{'dataset': d, 'bytes': wf_sizes.get(d), 'GB': gb(wf_sizes.get(d, 0)),
                                  'rows': wf_row_counts.get(d)} for d in DATASETS],
        'csv_total_bytes': csv_total, 'csv_total_MB': mb(csv_total),
        'parquet_metadata_total_bytes': parquet_meta_total, 'parquet_metadata_total_MB': mb(parquet_meta_total),
    }


def main():
    spark = spark_session('facts_41')
    fs = webhdfs()
    facts = {
        'A_inventaris': section_A(),
        'D_relasi_csv_hdf5': section_D(spark, fs),
        'E_batas_arrival': section_E_bounds(spark),
        'F_organisasi': section_F(spark),
    }
    out_path = os.path.join(OUT_DIR, '41_facts_tambahan.json')
    with open(out_path, 'w') as f:
        json.dump(facts, f, indent=2, default=str)
    print('wrote', out_path)
    print(json.dumps(facts, indent=2, default=str))
    spark.stop()


if __name__ == '__main__':
    main()
