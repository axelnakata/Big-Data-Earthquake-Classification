# Klasifikasi Sinyal Seismik Pacific Northwest dengan Hadoop & Spark

Proyek mata kuliah **COMP8035041 Big Data Analytics**, Magister Teknik Informatika, BINUS Graduate Program.
Penulis: Axel Nino Nakata (2702749701).

Proyek ini membangun pipeline big data untuk dataset **PNW-ML** (±84 GB, 2002–2022). Tujuannya adalah menyiapkan data
untuk klasifikasi otomatis sinyal seismik ke dalam empat kelas: **gempa bumi, ledakan, peristiwa permukaan, dan noise**.

| Tahap | Isi | Status |
|---|---|---|
| Assignment 1 | Pengumpulan data → HDFS data lake → pemeriksaan & pembersihan → konversi ke Parquet → model data | Selesai |
| Assignment 2 | Machine learning (dengan dan tanpa Spark MLlib) + graph analytics | Dalam pengerjaan |

## Arsitektur

```
 PNW-ML (UW / Google Drive)          HDFS data lake                          Apache Spark (PySpark)
 3 CSV + 3 HDF5, ±84 GB   ──put──▶  /datalake/raw/{comcat,exotic,noise}  ──▶  pembersihan metadata
                          SHA-256   (file asli, read-only)                     konversi HDF5 → Parquet
                                                                                     │
                                    /datalake/processed/                    ◀────────┘
                                      metadata/dataset=*/   (237.978 baris)
                                      waveforms/dataset=*/  (66,5 GB, 1 baris = 1 rekaman, kolom array e/n/z)
                                    /datalake/quality/     laporan kualitas data
                                    /datalake/_lineage/    asal-usul setiap file
```

- **Penyimpanan:** Hadoop 3.4.3 (HDFS pseudo-distributed, blok 128 MB, replikasi 1), Java 11.
- **Pemrosesan:** Spark 3.5.9 lokal (`local[*]`, 10 core, driver 12 GB), tanpa YARN.
- **Kunci penghubung** metadata ↔ waveform: `(dataset, trace_name)`.

## Struktur repositori

```
├── config/hadoop/     Konfigurasi Hadoop yang dipakai (core-site.xml, hdfs-site.xml, hadoop-env.sh)
├── src/               Kode pipeline
│   ├── common.py              setup bersama: environment Hadoop/Spark, path HDFS, helper
│   ├── ingest.sh              upload 1 file ke raw zone + verifikasi SHA-256 + fsck + lineage
│   └── convert_waveforms.py   konversi HDF5 → Parquet secara paralel dengan Spark
├── notebooks/         Langkah analisis, dijalankan berurutan (lihat tabel di bawah)
├── scripts/           Pembuat gambar dan angka untuk laporan
└── outputs/           Bukti hasil eksekusi: tabel, gambar, fsck, lineage (lihat outputs/README.md)
```

| Notebook | Isi | Bab laporan |
|---|---|---|
| `01_hdfs_smoke_test` | Tes HDFS, WebHDFS, dan Spark baca/tulis | 2.2, 2.3 |
| `02_inspect_data` | Identifikasi elemen & format data, kamus data, bukti data leakage | 4.1.1 |
| `03_cleaning_quality` | Pembersihan metadata → `processed/metadata`, funnel, laporan kualitas | 3.4, 4.1.2 |
| `04_convert_waveforms` | Konversi & validasi waveform HDF5 → `processed/waveforms` | 2.3, 4.1.3 |
| `05_data_model` | Model data relasional / array / graf dan operasi Spark | 4.2 |
| `06_governance` | Hak akses per peran (ACL), audit log, lineage | 3 |

| Script | Menghasilkan |
|---|---|
| `scripts/fig1_waveform_examples.py` | Gambar 1: contoh waveform empat kelas |
| `scripts/sec41_facts.py`, `sec41_figures.py` | Angka dan gambar tambahan Subbab 4.1 |
| `scripts/sec42_operations.py` | Angka operasi data Subbab 4.2.2 |

## Dataset

**PNW-ML** (Ni dkk., 2023), tersedia di https://github.com/niyiyu/PNW-ML. Data **tidak** disimpan di repo ini karena ukurannya ±84 GB.

| Bagian | Metadata (CSV) | Waveform (HDF5) |
|---|---|---|
| ComCat (gempa, ledakan) | 178.939 baris × 37 kolom | 62,7 GB, 3 × 15.001 sampel |
| Exotic (peristiwa permukaan) | 9.267 baris × 17 kolom | 3,8 GB, 3 × 18.001 sampel |
| Noise | 51.017 baris × 11 kolom | 17,3 GB, 3 × 15.001 sampel |

Waveform ComCat diunduh dari mirror Google Drive resmi karena server UW membatasi kecepatan. URL sumber dan SHA-256
setiap file tercatat di `outputs/hdfs/lineage.jsonl`.

## Menjalankan ulang

Prasyarat: macOS/Linux, Java 11, Hadoop 3.4.x di `~/opt/hadoop`, Python 3.11, ±250 GB ruang disk (raw + processed + salinan download).

```bash
# 1. Python
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. HDFS: salin config/hadoop/* ke ~/opt/hadoop/etc/hadoop/ (sesuaikan path), lalu:
export JAVA_HOME=$(/usr/libexec/java_home -v 11)
hdfs namenode -format                      # HANYA sekali pada instalasi baru
hdfs --daemon start namenode && hdfs --daemon start datanode
hdfs dfs -mkdir -p /datalake/raw/{comcat,exotic,noise} /datalake/processed /datalake/quality /datalake/_lineage

# 3. Ingest (file hasil download di ~/pnwml-data/staging/downloads/)
src/ingest.sh comcat comcat_metadata.csv   # ulangi untuk keenam file
hdfs dfs -chmod -R 555 /datalake/raw

# 4. Notebook 01 → 03, lalu konversi waveform (±7 menit), lalu notebook 04 → 06
jupyter lab
python src/convert_waveforms.py exotic noise comcat
```

NameNode UI: http://localhost:9870 · Spark UI: http://localhost:4040

## Referensi & lisensi

- Y. Ni dkk., "Curated Pacific Northwest AI-ready seismic dataset," *Seismica*, vol. 2, no. 1, 2023, doi:10.26443/seismica.v2i1.368 (CC BY 4.0).
- Y. Ni, "niyiyu/PNW-ML: PNW-ML seismic dataset," Zenodo, 2023, doi:10.5281/zenodo.7627103 (lisensi MIT).
