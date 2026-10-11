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
| `tables/a2_dataset_summary.md` … `a2_stations_per_event.md`, `figures/a2_*` (audit) | Kondisi data sebelum ML: kolom, kelas, posisi kejadian, komponen E/N/Z, waktu, lokasi | `07` | 4.3, 5.1 |
| `tables/a2_column_decisions.md`, `a2_preprocessing_funnel.md`, `a2_class_weights.md`, `a2_split_by_class.md`, `a2_normalization_example.md` | Keputusan preprocessing dan hasilnya | `08` | 5.1 |
| `tables/a2_context_check.md`, `a2_model_inputs.md`, `figures/a2_context_encoding.png`, `a2_crop_illustration.png` | Fitur konteks dan input CNN | `09` | 5.2 |
| `tables/a2_pilot.json`, `a2_cnn_architecture.md`, `a2_training_history.*`, `a2_training_log.txt`, `figures/a2_learning_curves.png` | Arsitektur, pilot, riwayat training | `10`, `src/train_cnn.py` | 5.3–5.4 |
| `tables/a2_test_metrics_*.md`, `a2_confusion_matrix.md`, `a2_metrics_by_sensor.md`, `a2_context_permutation.md`, `a2_position_test.md` | Evaluasi dan analisis model | `11` | 5.5–5.6 |
| `tables/a2_graph_*.md`, `figures/a2_graph_*.png` | Graph analytics: ukuran graph, ambang bobot, degree, connected components, PageRank, komunitas, triangle count | `12` | 6 |
| `models/cnn_best.pt` | Bobot CNN terbaik (epoch dengan macro-F1 validasi tertinggi) | `src/train_cnn.py` | 5.4 |
| `facts/*.json` | Angka mentah untuk Subbab 4.1 dan 4.2.2 | `scripts/` | 4.1, 4.2 |
| `figures/` | Gambar laporan (waveform per kelas, rekaman per tahun) | `02`, `05`, `scripts/` | 1, 4.1 |
| `screenshots/` | Tangkapan layar NameNode UI dan Spark UI | manual | 2.2, 2.3 |

`01`–`12` = notebook di `notebooks/`.
