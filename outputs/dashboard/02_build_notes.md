# Catatan pembuatan dashboard (bahan Bab 7.1)

Berisi fakta saja. Kalimat laporan ditulis pemilik.

## 1. Tujuan dan pembaca
- Pembaca: dosen yang tidak mengikuti Assignment I/II, dan pengambil keputusan non-IT di lembaga pemantau seismik.
- Tiap tab dirancang bisa dipahami dalam ±90 detik: temuan, angka kunci, lalu keputusan yang didukung.
- Ada 4 insight, 2 berbasis model dan 2 berbasis graph, karena brief mewajibkan insight dari model ML dan graph analytics.

| Tab | Sumber | Pertanyaan | Keputusan |
|---|---|---|---|
| 01 Otomatisasi pemeriksaan | ML | Berapa banyak pemeriksaan bisa diambil alih model? | Mengatur batas *confidence level*: naik berarti lebih sedikit salah, turun berarti beban analis lebih ringan |
| 02 Deteksi *surface event* | Graph + *deep learning* | Bagaimana agar *surface event* tidak terlewat? | Alarm 1 stasiun + model *deep learning*: 4,4× lebih banyak terdeteksi daripada aturan 2 stasiun |
| 03 Pola kejadian per wilayah | Graph | Apa pola kejadian tiap wilayah? | Fokus pemeriksaan disesuaikan dengan pola wilayah |
| 04 Stasiun paling sentral | Graph | Stasiun mana yang paling sentral? | Anggaran pemeliharaan dan daya cadangan didahulukan untuk 10 stasiun |

## 2. Arsitektur
HDFS (±90 GB mentah, 71 GB waveform olahan) → Spark, notebook `13_dashboard_export` → 6 file ringkas di `docs/data/` (3,32 MB) → situs statis (HTML, CSS, JavaScript) di GitHub Pages.

Alasan (detail di PRD §4):
- Pengambil keputusan butuh hasil, bukan data mentah. Pekerjaan berat sudah selesai di Spark.
- Ukuran dan kecepatan: 90 GB menjadi 3,32 MB (sekitar 27.000× lebih kecil), dan tiap klik dijawab di browser.
- Situs statis tidak punya server yang bisa "tertidur". Aturan hosting di PRD §4 belum saya periksa, jadi cek dulu sebelum dikutip.
- Bisa diulang: notebook 13 dapat dijalankan ulang dari HDFS dan memvalidasi dirinya sendiri.
- Lisensi: PNW-ML (MIT) dicantumkan di *footer*. Sumber peta dasar us-atlas (ISC) dicatat di `summary.json → provenance`.

Revisi setelah tinjauan pemilik (9 Nov 2026): dashboard diubah menjadi versi untuk *stakeholder*. Teks penjelasan, baris sumber data, dan asumsi aturan alarm dihapus. Tab 02 menjadi interaktif: pengguna memilih satu dari tiga aturan alarm, lalu KPI, grafik, dan kalimat keputusan menyesuaikan. Angka *noise* untuk aturan 2 stasiun ditampilkan "–" karena data tidak mengukurnya.

## 3. Kontrak data

| File | Baris | Ukuran | Sumber |
|---|---|---|---|
| `predictions.csv` | 35.341 | 2,79 MB | `/datalake/ml/predictions` (test), `/datalake/processed/metadata`, `/datalake/graph/g1_edges` |
| `waveforms_sample.json` | 48 | 157 KB | `/datalake/ml/waveforms_z150s` (test) |
| `stations.csv` | 642 | 39 KB | G1, G2, PageRank, `/datalake/dashboard/lpa_rerun` |
| `explosions.csv` | 6.392 | 311 KB | `/datalake/processed/metadata` (label ledakan) |
| `summary.json` | 1 objek | 6 KB | G1, metadata, `lpa_rerun` |
| `states.json` | 3 negara bagian | 16 KB | npm `us-atlas@3.0.1` (US Census Bureau 2017) |

## 4. Hasil validasi
Daftar lengkap: `01_export_report.md`. 58 dari 59 pemeriksaan PASS. Satu FAIL bukan kesalahan data, melainkan selisih PRD (lihat di bawah).

| Pemeriksaan | Hasil |
|---|---|
| Jumlah rekaman test | 35.341 |
| *Confusion matrix* | sama persis dengan `a2_confusion_matrix.md` |
| Accuracy / macro-F1 | 0,9249 / 0,8609 |
| PageRank 10 teratas | stasiun dan urutan sama, skor ±0,01 |
| *Label propagation* dijalankan ulang | 100% sama dengan pemetaan tersimpan `g2_communities` |
| Stasiun per kejadian | dalam ±0,002 dari Gambar 16 |
| Jam kerja per kelas | sama dengan `a2_context_by_class.md` |
| Rata-rata *surface event* jaringan | 4,7%, bukan 4,8% seperti di PRD (8.912 / 187.751 = 4,747%) |

Perbedaan lain terhadap PRD:
- K6 berjarak ±42 km dari Newberry Volcano. Kalimat "dekat Three Sisters" dibuang karena pusat K6 berjarak 101 km dan tidak ada stasiun K6 dalam 30 km.
- Kelompok ledakan terpadat berada di British Columbia, 24,3% ledakan ada di utara 49°LU, jadi peta diperluas sampai ke sana.
- Ledakan di Oregon barat: 1.218 kejadian, 91,8% pada jam kerja, 44,8% di titik berulang. Pola ini mengarah ke peledakan tambang atau *quarry*. Datanya tidak mencatat sumber ledakan, jadi kesimpulan ini berasal dari pola waktu dan lokasi yang berulang.

## 5. Alat dan versi
- Python 3.11.15, PySpark 3.5.9, GraphFrames 0.12.3, Hadoop 3.4.3
- Front end: HTML, CSS, JavaScript tanpa *framework* dan tanpa *build step*; peta dan grafik SVG
- Font: Instrument Sans dan IBM Plex Mono (Google Fonts)
- Uji tampilan: Chrome 157, lebar 1280 dan 400 piksel, mode terang dan gelap

## 6. Tangkapan layar
`outputs/dashboard/screenshots/` berisi `tab1_otomatisasi.png`, `tab2_surface_event.png`, `tab3_wilayah.png`, `tab4_stasiun.png` (mode terang, lebar 1280, skala 2×).
