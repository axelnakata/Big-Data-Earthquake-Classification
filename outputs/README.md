# Outputs: bukti hasil eksekusi

Semua angka di laporan berasal dari file di folder ini, yang dihasilkan oleh notebook dan script di repo.

| Folder / file | Isi | Dihasilkan oleh | Bab |
|---|---|---|---|
| `hdfs/fsck_*.txt` | Kondisi blok tiap file di HDFS (jumlah blok, replikasi, HEALTHY) | `src/ingest.sh` | 2.2 |
| `hdfs/lineage.jsonl` | Asal-usul tiap file: URL sumber, ukuran, SHA-256, waktu ingest | `src/ingest.sh` | 2.1, 3.2 |
| `tables/hadoop_settings.md`, `spark_settings.md`, `machine_spec.md` | Pengaturan Hadoop/Spark beserta alasannya, spesifikasi mesin | manual | 2.2, 2.3 |
| `tables/data_elements.md`, `column_comparison.md`, `hdf5_structure.md` | Elemen data, format (terstruktur/tidak), struktur HDF5, perbandingan kolom 37/17/11 | `02` | 4.1.1 |
| `tables/data_dictionary.md` | Kamus data: arti, tipe, % kosong, contoh, peran tiap kolom | `02` | 4.1.1 |
| `tables/class_counts.md`, `null_percent.md`, `coverage.md`, `orphans.md` | Jumlah kelas mentah, nilai kosong, cakupan, waveform tanpa metadata | `02` | 4.1 |
| `tables/leakage_evidence.md`, `column_roles.md` | Bukti data leakage dan peran tiap kolom | `02` | 4.1.1 |
| `tables/initial_data_questions.md` | Jawaban pertanyaan awal tentang struktur data | `02` | 4.1 |
| `tables/label_crosstab.md`, `label_cases.md` | Label ComCat vs kode PNSN (Tabel S2) | `02`, `03` | 3.4, 4.1.2 |
| `tables/cleaning_funnel.md` | Jumlah baris setelah tiap aturan cleaning | `03` | 4.1.2 |
| `tables/quality_report.md`, `metadata_quality.json` | Laporan kualitas data sebelum/sesudah cleaning | `03` | 3.4 |
| `tables/waveform_conversion.md`, `.json` | Waktu, ukuran, dan validasi konversi HDF5 → Parquet | `04`, `src/convert_waveforms.py` | 2.3, 4.1.3 |
| `tables/empty_components.md` | Komponen kosong per kelas × jenis sensor | `04` | 4.1.3 |
| `tables/data_model.md`, `graph_summary.md` | Model data relasional / array / graf | `05` | 4.2.1 |
| `tables/operations_timing.md`, `waveform_features_by_class.md` | Operasi Spark beserta waktu dan hasilnya | `05` | 4.2.2 |
| `tables/audit_log_sample.md` | Contoh audit log HDFS (akses diizinkan/ditolak) | `06` | 3.1 |
| `facts/*.json` | Angka mentah untuk Subbab 4.1 dan 4.2.2 | `scripts/` | 4.1, 4.2 |
| `figures/` | Gambar laporan (waveform per kelas, rekaman per tahun) | `02`, `05`, `scripts/` | 1, 4.1 |
| `screenshots/` | Tangkapan layar NameNode UI dan Spark UI | manual | 2.2, 2.3 |

`01`–`06` = notebook di `notebooks/`.
