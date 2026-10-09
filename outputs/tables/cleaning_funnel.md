# Funnel cleaning metadata (jumlah baris setelah tiap aturan)

Setiap angka bisa ditelusuri: baris awal − dibuang per aturan = baris akhir (diverifikasi dengan assert di notebook 03).

| step   | description                                                                                        |   comcat |   exotic |   noise |   total |
|:-------|:---------------------------------------------------------------------------------------------------|---------:|---------:|--------:|--------:|
| R0     | Raw (3 CSV digabung)                                                                               |   178939 |     9267 |   51017 |  239223 |
| R3     | ComCat: buang label PNSN di luar earthquake/explosion (su, sn, uk, qb)                             |   178839 |     9267 |   51017 |  239123 |
| R4     | Exotic: buang sonic boom, thunder, plane crash                                                     |   178839 |     8912 |   51017 |  238768 |
| R5     | Buang semua baris dengan trace_name duplikat (noise: 395 pasangan)                                 |   178839 |     8912 |   50227 |  237978 |
| R6     | Validasi (sampling rate, jumlah sampel, pointer HDF5, SNR) — 0 pelanggaran, tidak ada yang dibuang |   178839 |     8912 |   50227 |  237978 |
