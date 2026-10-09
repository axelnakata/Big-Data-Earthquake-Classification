# Hadoop (HDFS) settings used by this project

Values are the **effective** configuration, read live on 2026-09-24 with `hdfs getconf -confKey <key>` (Hadoop 3.4.3), not copied from docs.
Source files: `config/hadoop/core-site.xml`, `config/hadoop/hdfs-site.xml` (copies of `~/opt/hadoop/etc/hadoop/`). Everything not in those two files is a Hadoop default.

## 1. Deployment in one picture

```
MacBook (macOS arm64, 10 cores, 24 GB RAM)
 ├─ NameNode  (Java 11)  — the "table of contents": which file = which blocks, permissions   :9000 RPC, :9870 web UI
 ├─ DataNode  (Java 11)  — stores the actual 128 MB blocks on the Mac disk                   :9866 data, :9864 web
 └─ Spark 3.5.9 local[*] (PySpark in .venv) — reads/writes hdfs://localhost:9000             (no YARN)
```

| Choice | Value | Why |
|---|---|---|
| Mode | **Pseudo-distributed**: 1 NameNode + 1 DataNode on one machine | Real HDFS (same APIs, blocks, permissions as a cluster) on a laptop. Standalone mode would just use the local disk, which isn't HDFS |
| Install | Native binary tarball (`~/opt/hadoop` → `hadoop-3.4.3`), **not Docker** | Most Hadoop Docker images are amd64-only → slow emulation on Apple Silicon |
| Java | Temurin **11** | The Java version officially supported by both Hadoop 3.4 and Spark 3.5 |
| Start daemons | `hdfs --daemon start namenode` / `datanode` | `start-dfs.sh` needs SSH to localhost (would require enabling macOS Remote Login) |
| YARN | **Not used** | YARN schedules jobs across many machines; with 1 machine Spark local mode does the same job with less complexity. The lecturer's requirement is *storage* in Hadoop |

## 2. Settings we changed (in the XML files)

| Key | Our value | Default | Why we changed it |
|---|---|---|---|
| `fs.defaultFS` | `hdfs://localhost:9000` | `file:///` | Makes HDFS the default filesystem; this is the address Spark and `hdfs dfs` use |
| `hadoop.tmp.dir` | `~/pnwml-data/hadoop-data/tmp` | `/tmp/hadoop-${user}` | **Critical on macOS**: `/tmp` is wiped on reboot → the whole HDFS would disappear |
| `dfs.namenode.name.dir` | `~/pnwml-data/hadoop-data/namenode` | under `hadoop.tmp.dir` | Where the NameNode keeps its metadata (fsimage + edit log). Kept outside `~/Documents` to avoid iCloud sync |
| `dfs.datanode.data.dir` | `~/pnwml-data/hadoop-data/datanode` | under `hadoop.tmp.dir` | Where the real block files live (`blk_...`) |
| `dfs.replication` | **1** | 3 | Only 1 DataNode exists → a 2nd/3rd copy has nowhere to go (blocks would stay "under-replicated" forever). On a real cluster we'd use 3 (see Bab 3 design) |
| `dfs.permissions.enabled` | `true` | `true` | Written explicitly because the governance demo (read-only raw zone, ACL per role) depends on it |
| `dfs.webhdfs.enabled` | `true` | `true` | Written explicitly: Python (`h5py` + `fsspec`) reads HDF5 from HDFS over the WebHDFS REST API — Spark has no HDF5 reader |
| `dfs.datanode.hostname` | `localhost` | machine hostname | WebHDFS redirects reads to the DataNode by hostname; the Mac's hostname didn't resolve reliably → force `localhost` |
| `dfs.client.use.datanode.hostname` | `true` | `false` | Client connects to the DataNode by that hostname (pairs with the line above) |

## 3. Important defaults we kept

| Key | Value | Meaning / effect on our data |
|---|---|---|
| `dfs.blocksize` | **134217728 (128 MB)** | Files are cut into 128 MB blocks. ComCat waveform 67.3 GB → **502 blocks**, Noise 18.5 GB → **139**, Exotic 4.1 GB → **31**, each CSV → 1 block. Whole lake: **676 blocks** (avg 127 MB). Big blocks = few blocks to track = small NameNode memory; good for large sequential files like ours |
| `dfs.checksum.type` / `dfs.bytes-per-checksum` | CRC32C / 512 bytes | HDFS checksums every 512 bytes and verifies on read → silent disk corruption is detected. (Not SHA-256, so we verified ingest separately with SHA-256) |
| `dfs.datanode.scan.period.hours` | 504 (3 weeks) | DataNode re-reads all blocks every 3 weeks to find bit rot |
| `dfs.heartbeat.interval` | 3 s | DataNode tells NameNode "I'm alive" every 3 s |
| `dfs.namenode.heartbeat.recheck-interval` | 300000 ms | DataNode declared dead after ≈ 2×5 min + 10×3 s ≈ 10.5 min of silence |
| `dfs.blockreport.intervalMsec` | 21600000 (6 h) | DataNode sends full list of its blocks every 6 h |
| `dfs.namenode.safemode.threshold-pct` | 0.999 | After start, NameNode is read-only ("safe mode") until 99.9% of blocks are reported → that's why HDFS is briefly read-only after a restart |
| `dfs.namenode.safemode.extension` | 30000 ms | …plus 30 s extra |
| `dfs.namenode.checkpoint.period` / `.txns` | 3600 s / 1,000,000 | How often the edit log is merged into the fsimage (only with a Secondary NameNode; we don't run one) |
| `fs.permissions.umask-mode` | 022 | New files `rw-r--r--`, new dirs `rwxr-xr-x` |
| `dfs.permissions.superusergroup` | `supergroup` | The user who started the NameNode (`axelnakata`) is superuser — permission checks don't apply to them |
| `dfs.namenode.acls.enabled` | `true` | POSIX-style ACLs (`hdfs dfs -setfacl`) available → used for per-role access in governance demo |
| `hadoop.security.authentication` | **`simple`** | HDFS trusts whatever username the client claims (no password/Kerberos). Fine for a laptop, a security gap in production → Bab 3 design |
| `hadoop.security.authorization` | `false` | No service-level authorization |
| `dfs.encrypt.data.transfer` | `false` | Data between client and DataNode is not encrypted (design item for Bab 3) |
| `fs.trash.interval` | **0** | Trash is **off** → `hdfs dfs -rm` deletes immediately. Our raw zone is protected by permission 555 instead |
| `dfs.namenode.audit.loggers` | `default` | Audit logger exists; writing it to a separate file needs a log4j change (governance step) |
| `dfs.datanode.du.reserved` | 0 | HDFS may use all free disk; we monitor free space manually |
| `dfs.namenode.handler.count` | 10 | NameNode RPC threads — plenty for one user |
| `io.file.buffer.size` | 4096 | Read/write buffer size |
| Ports | NameNode RPC 9000 (from `fs.defaultFS`), NameNode web 9870, DataNode 9866 / web 9864 | Web UI: http://localhost:9870 |

## 4. Current state of the cluster (`hdfs dfsadmin -report`, `hdfs fsck /`)

| Metric | Value |
|---|---|
| Configured capacity | 926.3 GB (the whole Mac disk — HDFS shares it with macOS) |
| DFS used | 84.5 GB (73.9% of HDFS-usable space) |
| DFS remaining | 29.9 GB |
| Files / blocks | 7 files, 676 blocks, all replication 1 |
| Missing / corrupt / under-replicated blocks | 0 / 0 / 0 |
| fsck status | **HEALTHY** |

| HDFS file | Size | Blocks |
|---|---|---|
| `/datalake/raw/comcat/comcat_waveforms.hdf5` | 62.7 GiB | 502 |
| `/datalake/raw/noise/noise_waveforms.hdf5` | 17.3 GiB | 139 |
| `/datalake/raw/exotic/exotic_waveforms.hdf5` | 3.8 GiB | 31 |
| `/datalake/raw/comcat/comcat_metadata.csv` | 47.7 MiB | 1 |
| `/datalake/raw/noise/noise_metadata.csv` | 4.8 MiB | 1 |
| `/datalake/raw/exotic/exotic_metadata.csv` | 1.4 MiB | 1 |
| `/datalake/_lineage/lineage.jsonl` | 2 KB | 1 |

## 5. What would change on a real cluster (for Bab 2.2 / 3)
- `dfs.replication = 3` across ≥3 DataNodes (+ rack awareness) → survives a node failure.
- NameNode HA (active + standby + JournalNodes) — our single NameNode is a single point of failure.
- YARN (or Kubernetes) to schedule Spark across nodes.
- `hadoop.security.authentication = kerberos`, `dfs.encrypt.data.transfer = true`, TLS on web UIs, encryption zones (KMS).
- `fs.trash.interval > 0` so accidental deletes are recoverable.

Regenerate section 3/4 values: `hdfs getconf -confKey <key>`, `hdfs dfsadmin -report`, `hdfs fsck /`.
