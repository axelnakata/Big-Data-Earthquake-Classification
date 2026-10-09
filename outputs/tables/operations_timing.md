# Contoh operasi Spark dan waktunya (local[*], 10 core)

| operation                                                         | data                 |   seconds |
|:------------------------------------------------------------------|:---------------------|----------:|
| count semua trace (hanya metadata file Parquet, tanpa baca array) | waveforms            |      0.47 |
| count trace_name distinct (baca 1 kolom kecil)                    | waveforms            |      7.72 |
| jumlah semua sampel z (harus membaca seluruh array z)             | waveforms            |     10.74 |
| filter dataset=exotic → count (partition pruning)                 | waveforms            |      0.06 |
| groupBy dataset, label → count                                    | metadata             |      0.22 |
| groupBy year(trace_start_time), label                             | metadata             |      0.64 |
| window: rank magnitude per label                                  | metadata             |      0.54 |
| pivot network × label (% per label)                               | metadata             |      0.16 |
| join + transform/slice/aggregate array per trace → groupBy label  | waveforms + metadata |     37.62 |
| slice window 120 s → cek panjang                                  | waveforms            |     14.88 |
| graph: vertices, edges, degree                                    | metadata (graph)     |      1.6  |
