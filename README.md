# Klasifikasi Sinyal Seismik Pacific Northwest dengan Hadoop & Spark

Proyek mata kuliah **COMP8035041 Big Data Analytics**, Magister Teknik Informatika, BINUS Graduate Program.
Axel Nino Nakata (2702749701).

Dataset **PNW-ML** (±84 GB, 2002–2022) berisi ±238 ribu rekaman getaran tanah dari jaringan seismik Pacific Northwest. Proyek ini menyimpannya di **HDFS**, mengolahnya dengan **Spark**, lalu melatih **CNN** yang membaca waveform mentah untuk membedakan empat kelas: **gempa bumi, ledakan, peristiwa permukaan, dan noise**.

## Alur

```
PNW-ML (3 CSV + 3 HDF5) ──► HDFS /datalake/raw          file asli, read-only, SHA-256
                        ──► Spark: cleaning, HDF5 → Parquet          /datalake/processed   (A1)
                        ──► Spark: Z 0–150 s, z-score, split, fitur konteks   /datalake/ml
                        ──► PyTorch CNN via Spark TorchDistributor (5 proses)  → model terbaik
                        ──► Spark predict_batch_udf → prediksi, evaluasi, analisis   (A2)
                        ──► GraphFrames: graph kejadian–stasiun   /datalake/graph
```

Hadoop 3.4.3 (pseudo-distributed) · Spark 3.5.9 (`local[*]`) · PyTorch 2.14 · GraphFrames 0.12.3 · Python 3.11.

## Hasil

CNN 1D (200.868 parameter) pada waveform Z 120 s + 9 fitur konteks (waktu & sensor), dilatih 12 epoch (±2,5 jam, 5 proses CPU via Spark TorchDistributor). Model terbaik: epoch 9.

| Data uji (35.341 rekaman) | Accuracy | Macro-F1 |
|---|---|---|
| **CNN** | **0,925** | **0,861** |
| Baseline "selalu earthquake" | 0,677 | 0,202 |

F1 per kelas: earthquake 0,95 · noise 0,93 · surface event 0,80 · explosion 0,76. Rincian di notebook 11 dan `outputs/tables/a2_test_metrics_*.md`.

**Graph analytics** (GraphFrames): 51.448 kejadian + 642 stasiun, 187.751 edge; 99,99% vertex dalam satu komponen; label propagation menemukan 10 komunitas stasiun yang berkelompok secara geografis dengan komposisi kelas berbeda (mis. 44% ledakan di Oregon barat tengah, 17% surface event di jaringan gunung api CC).

## Struktur

```
config/hadoop/   konfigurasi HDFS yang dipakai
src/             kode pipeline (ingest, konversi, preprocessing, CNN, training)
notebooks/       01–12, dijalankan berurutan
scripts/         pembuat gambar & angka untuk laporan A1
outputs/         tabel, gambar, model, bukti eksekusi (lihat outputs/README.md)
```

| Notebook | Isi | Bab |
|---|---|---|
| `01_hdfs_smoke_test` | Tes HDFS, WebHDFS, Spark | 2 |
| `02_inspect_data` | Elemen & format data, kamus data | 4.1 |
| `03_cleaning_quality` | Pembersihan metadata, laporan kualitas | 3.4, 4.1 |
| `04_convert_waveforms` | HDF5 → Parquet, validasi | 2.3, 4.1 |
| `05_data_model` | Model data relasional / array / graf | 4.2 |
| `06_governance` | Hak akses, audit log, lineage | 3 |
| `07_data_audit_ml` | Kondisi data sebelum ML | 4.3, 5.1 |
| `08_preprocessing` | Z 0–150 s, z-score, split, bobot kelas | 5.1 |
| `09_feature_engineering` | Fitur konteks, input CNN | 5.2 |
| `10_cnn_training` | Arsitektur, training, kurva belajar | 5.3–5.4 |
| `11_evaluation_analysis` | Prediksi Spark, metrik, analisis | 5.5–5.6 |
| `12_graph_analytics` | Graph kejadian–stasiun & stasiun–stasiun (GraphFrames) | 6 |

## Menjalankan

```bash
python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
export JAVA_HOME=$(/usr/libexec/java_home -v 11)
hdfs --daemon start namenode && hdfs --daemon start datanode   # config di config/hadoop/
src/ingest.sh comcat comcat_waveforms.hdf5                     # untuk keenam file
python src/convert_waveforms.py exotic noise comcat            # setelah notebook 03
caffeinate -i python src/train_cnn.py                          # setelah notebook 09, ±2 jam
```

Notebook lainnya dijalankan berurutan di Jupyter. Kemajuan training bisa dipantau di `http://127.0.0.1:8765/monitor.html` (lihat `src/train_cnn.py`).

## Data

PNW-ML tidak disimpan di repo (±84 GB). Sumber dan SHA-256 setiap file ada di `outputs/hdfs/lineage.jsonl`.

- Y. Ni dkk., "Curated Pacific Northwest AI-ready seismic dataset," *Seismica*, vol. 2, no. 1, 2023, doi:10.26443/seismica.v2i1.368.
- Y. Ni, "niyiyu/PNW-ML," Zenodo, 2023, doi:10.5281/zenodo.7627103 (MIT).
