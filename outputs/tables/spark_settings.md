# Spark settings used by this project

Values are the **effective** configuration, read live on 2026-09-24 from a running session (`spark.conf.get(...)`), created by `spark_session()` in `src/common.py` — the same function every notebook uses.
Versions: **PySpark / Spark 3.5.9** (pip, in `.venv`), Java 11.0.32, bundled Hadoop client 3.3.4 (talks to our HDFS 3.4.3 server over RPC — compatible).

## 1. How Spark runs here

```
Python notebook ──► Spark driver (1 JVM, local[*] = 10 threads = 10 cores)
                        │  reads / writes  hdfs://localhost:9000/datalake/...
                        ▼
                  HDFS (NameNode + DataNode)
```

| Choice | Value | Why |
|---|---|---|
| Mode | **Local mode** (`local[*]`), no YARN, no cluster | 1 machine: the driver runs all tasks itself in 10 threads (1 per CPU core). Same Spark API as on a cluster — only `spark.master` would change |
| Storage | All input/output on **HDFS** (`hdfs://localhost:9000`) | Lecturer's requirement: storage in Hadoop, processing in Spark |
| Install | `pip install pyspark==3.5.*` | PySpark already contains Spark; no separate Spark tarball needed |

## 2. Settings we changed

| Key | Our value | Default | Why |
|---|---|---|---|
| `spark.master` | `local[*]` | — (required) | Use all 10 cores of the Mac |
| `spark.driver.memory` | **12g** | 1g | ~50% of the 24 GB RAM. In local mode the driver *is* the executor, so this is all memory Spark gets. Leaves the rest for macOS + HDFS daemons |
| `spark.local.dir` | `~/pnwml-data/tmp/spark-local` | `/tmp` | Scratch space for shuffle/spill files. Kept next to the HDFS data (outside `~/Documents`/iCloud) and off `/tmp` |
| `spark.hadoop.fs.defaultFS` | `hdfs://localhost:9000` | `file:///` | Paths without a scheme go to HDFS, not the local disk |
| `spark.sql.session.timeZone` + `-Duser.timezone` | `UTC` | Mac local time (WIB, UTC+7) | Seismic timestamps are UTC. Without this, times were shifted +7 h when shown in Python (bug found and fixed in notebook 04) |
| `HADOOP_CONF_DIR` (env var) | `~/opt/hadoop/etc/hadoop` | not set | Makes Spark's bundled Hadoop client read **our** `hdfs-site.xml`. Without it Spark wrote Parquet with Hadoop's default `dfs.replication=3` → blocks stuck "under-replicated" on our 1 DataNode (found + fixed in notebook 05, fsck back to 0 under-replicated) |
| `SPARK_LOCAL_IP` (env var) | `127.0.0.1` | the Mac's LAN IP | Driver and Spark UI listen on localhost only → not reachable from the Wi-Fi network (security) and no hostname warning |
| `PYSPARK_PYTHON` (env var) | `.venv/bin/python` (3.11) | `python3` on PATH (macOS system 3.9) | Spark starts separate Python *worker* processes for Python code inside tasks; they must be the same version as the notebook. Without it: `PYTHON_VERSION_MISMATCH` (found in notebook 05) |

## 3. Important defaults we kept

| Key | Value | What it means for our data |
|---|---|---|
| `spark.default.parallelism` (effective) | **10** | Number of parallel tasks = number of cores |
| `spark.sql.files.maxPartitionBytes` | 128 MB | Max bytes per input partition — same as HDFS block size, so 1 task ≈ 1 block for big files. Small files are split further to keep all cores busy: `comcat_metadata.csv` (50 MB) is read as **10 partitions** (verified) |
| `spark.sql.shuffle.partitions` | 200 | Partitions after a shuffle (`groupBy`, `join`). 200 is too many for our small metadata… |
| `spark.sql.adaptive.enabled` + `coalescePartitions` | `true` | …but Adaptive Query Execution merges them at runtime: `groupBy('source_type')` on ComCat ended with **1** partition (verified). So we don't need to tune 200 by hand |
| `spark.sql.autoBroadcastJoinThreshold` | 10 MB | Tables smaller than 10 MB are copied to every task in a join (no shuffle) — relevant when joining metadata ⇄ waveforms |
| `spark.sql.sources.default` | `parquet` | Parquet is Spark's default format |
| `spark.sql.parquet.compression.codec` | `snappy` | Parquet output is compressed with Snappy (fast, moderate ratio) |
| `spark.sql.sources.partitionOverwriteMode` | `STATIC` | Overwriting a partitioned table replaces **all** partitions. The waveform converter sets `dynamic` so each dataset is rewritten alone |
| `spark.sql.execution.arrow.maxRecordsPerBatch` | 10000 | The waveform converter lowers it to **128** (≈46 MB per batch) so one batch of arrays fits comfortably in memory |
| `spark.sql.execution.arrow.pyspark.enabled` | `false` | Spark→pandas conversion without Arrow; fine for our small result tables |
| `spark.memory.fraction` | 0.6 (default) | 60% of heap for execution + cache |
| Spark UI | http://localhost:4040 (while a session runs) | Shows jobs, stages, tasks — useful screenshot for Bab 2.3 |

## 4. How HDF5 waveforms are read (Spark has no HDF5 reader)

Spark can read CSV, JSON, Parquet, ORC… but **not HDF5**. So waveforms are read with Python `h5py`, opening the file directly from HDFS over **WebHDFS** (`fsspec`, port 9870) — no local copy.

| Stage | Who reads HDF5 | How |
|---|---|---|
| Notebook 04 (done) | The driver only (plain Python) | `h5py.File(webhdfs.open(path))` → read structure + a few single traces (~360 KB each, < 1 s) |
| Notebook 06 / `src/convert_waveforms.py` (done) | **Driver** reads only the byte layout with h5py; **Spark tasks** read the waveform bytes in parallel | h5py gives each bucket's byte offset, shape, dtype (`<f8`, contiguous, uncompressed) → clean metadata (Spark) lists the `(bucket, row)` to keep → rows grouped into chunks of 128 nearby traces → each task sends **one WebHDFS HTTP range request** per chunk, turns bytes into arrays with NumPy, and returns them via `mapInPandas` (Arrow) → Parquet `/datalake/processed/waveforms/dataset=*/`. Measured ~190 MB/s (Exotic 3.85 GB in 20 s); 100/100 random traces bit-identical to h5py reads |

Why this works efficiently: the HDF5 arrays are **contiguous and uncompressed** (notebook 04, B1), so one trace = one continuous byte range → cheap random reads over HTTP.

## 5. What Spark did (notebooks 04–07)
Read 3 CSVs from HDFS with schema inference · counts, null % per column · `groupBy`/`pivot` crosstabs · duplicate & overlap checks with `intersect` · regex parsing of `trace_name` and `trace_snr_db` · `unionByName` of the 3 files for the leakage check (04) · schema unification, rule-based filtering, joins, validation, partitioned Parquet write (05) · parallel HDF5→Parquet conversion with `mapInPandas` (06) · partition/column pruning, window functions, higher-order array functions (`transform`, `slice`, `aggregate`), graph vertices/edges (07).

Regenerate: start `spark_session()` from `src/common.py` and call `spark.conf.get('<key>')`; parallelism via `spark.sparkContext.defaultParallelism`.
