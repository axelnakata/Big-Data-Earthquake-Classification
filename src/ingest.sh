#!/bin/zsh
# Ingest 1 file download ke HDFS raw zone + verifikasi SHA-256 + bukti fsck + lineage.
# Pakai: src/ingest.sh <dataset> <filename> [source_url]   contoh: src/ingest.sh exotic exotic_waveforms.hdf5
set -euo pipefail
ds=$1; f=$2
ROOT=${0:A:h:h}
SRC=$HOME/pnwml-data/staging/downloads/$f
DST=/datalake/raw/$ds/$f
URL=${3:-https://dasway.ess.washington.edu/shared/niyiyu/PNW-ML/$f}
export JAVA_HOME=$(/usr/libexec/java_home -v 11) HADOOP_HOME=$HOME/opt/hadoop
export PATH=$HADOOP_HOME/bin:$PATH HADOOP_ROOT_LOGGER=ERROR,console

[[ -f $SRC.aria2 ]] && { echo "ERROR: $f belum selesai download"; exit 1; }

echo "[$f] sha256 lokal..."
local_sha=$(shasum -a 256 "$SRC" | cut -d' ' -f1)
echo "[$f] put -> $DST"
hdfs dfs -put "$SRC" "$DST"
echo "[$f] sha256 dari HDFS..."
hdfs_sha=$(hdfs dfs -cat "$DST" | shasum -a 256 | cut -d' ' -f1)
[[ $local_sha == $hdfs_sha ]] || { echo "ERROR: SHA-256 beda! lokal=$local_sha hdfs=$hdfs_sha"; exit 1; }

hdfs fsck "$DST" -files -blocks > "$ROOT/outputs/hdfs/fsck_$f.txt" 2>/dev/null
bytes=$(stat -f %z "$SRC")
printf '{"dataset":"%s","file":"%s","source_url":"%s","bytes":%s,"sha256":"%s","hdfs_path":"%s","ingested_at":"%s"}\n' \
  "$ds" "$f" "$URL" "$bytes" "$local_sha" "$DST" "$(date -u +%FT%TZ)" >> "$ROOT/outputs/hdfs/lineage.jsonl"
hdfs dfs -put -f "$ROOT/outputs/hdfs/lineage.jsonl" /datalake/_lineage/lineage.jsonl
echo "[$f] OK sha256=$local_sha $(grep -Eo 'Total blocks \(validated\):\s+[0-9]+' "$ROOT/outputs/hdfs/fsck_$f.txt")"
