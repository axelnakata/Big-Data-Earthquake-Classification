# Machine spec & download test (2026-09-23)

| Item | Nilai |
|---|---|
| OS | macOS 26.7 (build 25G229), arm64 |
| RAM | 24 GB |
| CPU | 10 core |
| Disk kosong | 200 GB |

## Server UW-ESS (curl -I)
| File | Bytes | Last-Modified |
|---|---|---|
| comcat_metadata.csv | 50,025,733 | 2025-11-21 |
| noise_metadata.csv | 5,028,650 | 2025-11-21 |
| exotic_metadata.csv | 1,476,207 | 2025-06-03 |
| exotic_waveforms.hdf5 | 4,111,581,160 | 2023-12-17 |
| comcat_waveforms.hdf5 | 67,343,580,072 | 2023-12-17 |
| noise_waveforms.hdf5 | 18,527,565,888 | 2023-12-17 |
| **Total** | **90,039,257,710 (~90 GB)** | |

- `Accept-Ranges: bytes`, range request → HTTP 206 → **resume didukung**.
- Kecepatan per koneksi: 0.09–4.2 MB/s (tidak stabil). 4 koneksi paralel: 2 dapat ~4 MB/s, 2 dapat ~0.2 MB/s.
- Keputusan: aria2c 8 koneksi per file.
