"""HDF5 waveforms (raw zone) -> Parquet (processed zone), driven by the clean metadata table.

How it works:
  1. Driver: h5py reads only the HDF5 *layout* (byte offset, shape, dtype of each bucket) over WebHDFS.
     All buckets are contiguous + uncompressed, so trace i = bytes [offset + i*trace_bytes, +trace_bytes).
  2. Spark: clean metadata rows (only these are converted -> orphans are skipped) are grouped into chunks of
     nearby rows of the same bucket. Each Spark task reads its chunk's byte range from HDFS over WebHDFS
     (one HTTP range request), slices it into traces and returns them as Arrow batches (mapInPandas).
  3. Written as Parquet partitioned by dataset; dynamic overwrite = only that dataset's partition is replaced.

CLI (long runs):  caffeinate -i .venv/bin/python src/convert_waveforms.py noise comcat
"""
import getpass, json, os, sys, time
import numpy as np, pandas as pd, requests

sys.path.insert(0, os.path.dirname(__file__))
from common import HDFS, RAW, PROCESSED, QUALITY, OUT_TABLES, sh, spark_session, webhdfs

CHUNK = 128             # traces per HTTP request (~46 MB for 15001 samples)
TRACES_PER_TASK = 2048  # ~0.7 GB of waveform per Spark task / output file
OUT = f'{HDFS}{PROCESSED}/waveforms'
STATS = os.path.join(OUT_TABLES, 'waveform_conversion.json')
SCHEMA = ('trace_name string, event_id string, n_samples int, n_empty_components int, '
          'e array<double>, n array<double>, z array<double>, dataset string')


def layout(dataset):
    """Byte layout of every bucket, read with h5py on the driver (no waveform data is read)."""
    import h5py
    rows = []
    with webhdfs().open(f'{RAW}/{dataset}/{dataset}_waveforms.hdf5', 'rb') as fo, h5py.File(fo, 'r') as f:
        order = f['data_format/component_order'][()].decode()
        assert order == 'ENZ', order
        for b in f['data']:
            ds = f['data'][b]
            assert ds.dtype.str == '<f8' and ds.chunks is None and ds.compression is None, (b, ds.dtype, ds.chunks)
            rows.append((b, int(ds.id.get_offset()), ds.shape[0], ds.shape[2]))
    return pd.DataFrame(rows, columns=['bucket', 'offset', 'bucket_rows', 'n_samples_h5'])


def _reader(path, user):
    url = f'http://localhost:9870/webhdfs/v1{path}'

    def read_batches(batches):
        for pdf in batches:
            for (_, _), g in pdf.sort_values('row').groupby(['bucket', 'chunk']):
                s = int(g.n_samples_h5.iloc[0]); tb = 3 * s * 8
                r0, r1 = int(g.row.min()), int(g.row.max())
                resp = requests.get(url, params={'op': 'OPEN', 'user.name': user,
                                                 'offset': int(g.offset.iloc[0]) + r0 * tb, 'length': (r1 - r0 + 1) * tb}, timeout=600)
                resp.raise_for_status()
                arr = np.frombuffer(resp.content, '<f8').reshape(r1 - r0 + 1, 3, s)[g.row.to_numpy() - r0]
                yield pd.DataFrame({
                    'trace_name': g.trace_name.to_numpy(), 'event_id': g.event_id.to_numpy(),
                    'n_samples': g.n_samples.to_numpy(), 'n_empty_components': (np.abs(arr).max(axis=2) == 0).sum(axis=1),
                    'e': list(arr[:, 0]), 'n': list(arr[:, 1]), 'z': list(arr[:, 2]), 'dataset': g.dataset.to_numpy()})
    return read_batches


def convert(spark, dataset):
    """Convert one dataset; returns stats dict."""
    from pyspark.sql import functions as F
    t0 = time.time()
    lay = spark.createDataFrame(layout(dataset))
    meta = (spark.read.parquet(f'{HDFS}{PROCESSED}/metadata').filter(F.col('dataset') == dataset)
            .select('dataset', 'trace_name', 'event_id', 'bucket', 'row', 'n_samples')
            .join(F.broadcast(lay), 'bucket'))
    assert meta.filter('n_samples != n_samples_h5 OR row >= bucket_rows').count() == 0
    n = meta.count()
    meta = meta.withColumn('chunk', (F.col('row') / CHUNK).cast('int'))
    n_tasks = max(1, -(-n // TRACES_PER_TASK))
    spark.conf.set('spark.sql.sources.partitionOverwriteMode', 'dynamic')
    spark.conf.set('spark.sql.execution.arrow.maxRecordsPerBatch', CHUNK)
    wf = (meta.repartition(n_tasks, 'bucket', 'chunk').sortWithinPartitions('bucket', 'row')
              .mapInPandas(_reader(f'{RAW}/{dataset}/{dataset}_waveforms.hdf5', getpass.getuser()), SCHEMA))
    wf.write.mode('overwrite').partitionBy('dataset').parquet(OUT)
    secs = time.time() - t0
    raw_gb = n * 3 * int(lay.first().n_samples_h5) * 8 / 1e9
    stats = {'dataset': dataset, 'traces': n, 'spark_tasks': n_tasks, 'seconds': round(secs, 1),
             'waveform_gb': round(raw_gb, 2), 'throughput_mb_s': round(raw_gb * 1e3 / secs, 1),
             'finished_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    all_stats = json.load(open(STATS)) if os.path.exists(STATS) else {}
    all_stats[dataset] = stats
    json.dump(all_stats, open(STATS, 'w'), indent=1)
    sh(f'hdfs dfs -put -f {STATS} {QUALITY}/waveform_conversion.json', quiet=True)
    return stats


if __name__ == '__main__':
    spark = spark_session('convert_waveforms')
    for d in sys.argv[1:]:
        print(time.strftime('%F %T'), 'start', d, flush=True)
        print(time.strftime('%F %T'), convert(spark, d), flush=True)
    spark.stop()
