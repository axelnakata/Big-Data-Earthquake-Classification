# Phase 1 — Export report

Generated 2026-11-09T12:20:39Z by `notebooks/13_dashboard_export.ipynb` (git e75fa56).

## Files in `docs/data/`

| file                  |   bytes |   rows | source                                                                                                         |
|:----------------------|--------:|-------:|:---------------------------------------------------------------------------------------------------------------|
| explosions.csv        |  310799 |   6392 | /datalake/processed/metadata (label=explosion)                                                                 |
| predictions.csv       | 2794751 |  35341 | /datalake/ml/predictions (split=test); /datalake/processed/metadata; /datalake/graph/g1_edges                  |
| states.json           |   16022 |      3 | npm us-atlas@3.0.1 states-10m.json (lisensi ISC), dari US Census Bureau cartographic boundary files 2017       |
| stations.csv          |   38648 |    642 | /datalake/graph/g1_edges; /datalake/graph/g2_vertices; /datalake/graph/g2_edges; /datalake/dashboard/lpa_rerun |
| summary.json          |    5613 |      1 | /datalake/graph/g1_edges; /datalake/processed/metadata; /datalake/dashboard/lpa_rerun                          |
| waveforms_sample.json |  156828 |     48 | /datalake/ml/waveforms_z150s (split=test)                                                                      |

Total: 3.32 MB (limit 10 MB).

## New paths (nothing existing was changed)

- HDFS `/datalake/dashboard/lpa_rerun`
- `docs/data/*`
- `outputs/dashboard/*`
- `notebooks/13_dashboard_export.ipynb`

## Deviations from the report numbers

- Network average surface event = 4.7% (PRD 4.8%). Exact value 8,912 / 187,751; 4.8 came from averaging rounded group percentages.
- `pct_*` in `stations.csv` are percentages 0–100 with 1 decimal, matching `summary.json → groups[].pct`.
- Label propagation: mapping identical to saved `/datalake/graph/g2_communities` (PRD thought it was never saved).

## Waveform sample buckets (recordings taken)

| kelas         |   a_benar_conf>=0.95 |   b_benar_conf_0.70-0.95 |   c_conf<0.70 |   d_salah_conf>=0.85 |
|:--------------|---------------------:|-------------------------:|--------------:|---------------------:|
| earthquake    |                    3 |                        3 |             3 |                    3 |
| explosion     |                    3 |                        3 |             3 |                    3 |
| surface_event |                    3 |                        3 |             3 |                    3 |
| noise         |                    3 |                        3 |             3 |                    3 |

## Label propagation re-run (tolerance rule §6.3)

| group      |   stations |   lat |     lon |   recordings |   earthquake |   explosion |   surface_event |
|:-----------|-----------:|------:|--------:|-------------:|-------------:|------------:|----------------:|
| K1         |        246 | 47.74 | -122.47 |       102537 |         90.2 |         6.9 |             2.9 |
| K2         |        125 | 45.76 | -122.58 |        62972 |         84.3 |         7.2 |             8.6 |
| K3         |         61 | 46.39 | -119.26 |        11304 |         86.8 |        12.9 |             0.4 |
| K4         |         48 | 42.89 | -123.07 |         4066 |         62.7 |        37.3 |             0   |
| K5         |         24 | 43.97 | -122.43 |         2962 |         53.5 |        44.2 |             2.4 |
| K6         |         22 | 43.45 | -120.86 |         2468 |         76.1 |         6.6 |            17.4 |
| K7         |         12 | 45.21 | -120.52 |          724 |         97.9 |         2.1 |             0   |
| K8         |          7 | 44.48 | -116.74 |          113 |        100   |         0   |             0   |
| lainnya    |         10 | 44.73 | -119.24 |          202 |         92.1 |         7.9 |             0   |
| terisolasi |         87 | 45.35 | -121.15 |          403 |         83.6 |        14.6 |             1.7 |

## Explosion locations and station groups

| kelompok   |   ledakan |   median_km_ke_pusat |   pct_dalam_100km |   lat_median |   lon_median |   sel_terpadat_pct |   pct_3_sel_terpadat |
|:-----------|----------:|---------------------:|------------------:|-------------:|-------------:|-------------------:|---------------------:|
| K1         |      3326 |                  171 |              31.7 |        48.49 |      -121.39 |               28.6 |                 48.8 |
| K2         |      1826 |                   71 |              71.4 |        45.84 |      -122.63 |                7.5 |                 19.8 |
| K3         |       621 |                   95 |              54.8 |        46.42 |      -119.18 |                9.8 |                 24.3 |
| K4         |       729 |                   77 |              70.5 |        43.43 |      -123.11 |                8.1 |                 23.9 |
| K5         |       724 |                   65 |              82.9 |        44.1  |      -122.89 |               10.6 |                 22.2 |
| K6         |       100 |                   98 |              51   |        44.04 |      -121.02 |               18   |                 42   |
| K7         |        14 |                   78 |              71.4 |        45.66 |      -121.09 |               14.3 |                 28.6 |

Densest 0.25° cells:

|   cell |   cell_lon |   n |   lat |     lon |   pct |
|-------:|-----------:|----:|------:|--------:|------:|
|  49.25 |    -120.75 | 951 | 49.41 | -120.53 |  14.9 |
|  49.25 |    -120.5  | 381 | 49.39 | -120.48 |   6   |
|  48    |    -122    | 293 | 48.1  | -121.93 |   4.6 |
|  46.75 |    -122.25 | 170 | 46.95 | -122.21 |   2.7 |
|  47    |    -122    | 157 | 47.16 | -121.85 |   2.5 |
|  45.75 |    -122.5  | 137 | 45.84 | -122.45 |   2.1 |
|  46    |    -123.25 | 116 | 46.19 | -123.05 |   1.8 |
|  49    |    -122.25 | 116 | 49.11 | -122.14 |   1.8 |
|  45.5  |    -122.5  | 110 | 45.68 | -122.37 |   1.7 |
|  46    |    -123    |  90 | 46.11 | -122.85 |   1.4 |

## Volcano distance checks

| kelompok   | gunung           |   km_pusat_kelompok |   stasiun_≤30km |   stasiun_≤50km |   dari |
|:-----------|:-----------------|--------------------:|----------------:|----------------:|-------:|
| K2         | Mount St. Helens |                  58 |              35 |              44 |    125 |
| K2         | Mount Hood       |                  81 |              12 |              17 |    125 |
| K6         | Three Sisters    |                 101 |               0 |               1 |     22 |
| K6         | Newberry Volcano |                  42 |              14 |              17 |     22 |

## What the explosion layer shows

- Western Oregon box (42–45.2°N, 124.5–121.8°W): 1,218 explosions, 91.8% in weekday working hours, 44.8% at repeated sites. They spread along the western valleys and repeat at many sites. There is no single dominant point.
- K4 and K5 notes: see `summary.json → region_notes`. The wording says "possible quarry blasting, not confirmed": the pattern fits, but the data has no blast-source field.
- The densest cluster overall is outside the US: 1,551 explosions (24.3%) lie north of 49°N, mostly near 49.4°N, 120.5°W (British Columbia). K1 stations record them. The map extends north of the border to show this.
- §7.5 says K6 is "near the Three Sisters". Not supported: the K6 centre is 101 km away and 0 of 22 stations are within 30 km. Only the Newberry Volcano note is used.


## All checks

| check                                                          | result   | detail                                                                                                        |
|:---------------------------------------------------------------|:---------|:--------------------------------------------------------------------------------------------------------------|
| predictions: jumlah baris = baris test HDFS                    | PASS     | 35,341                                                                                                        |
| predictions: pred = argmax                                     | PASS     |                                                                                                               |
| predictions: jumlah peluang = 1 (±0,01)                        | PASS     | 1.000000..1.000000                                                                                            |
| predictions: confusion matrix = a2_confusion_matrix.md         | PASS     |                                                                                                               |
| predictions: accuracy 0,925 (±0,001)                           | PASS     | 0.9249                                                                                                        |
| predictions: macro-F1 0,861 (±0,001)                           | PASS     | 0.8609                                                                                                        |
| predictions: n_stations_event kosong hanya untuk noise         | PASS     |                                                                                                               |
| predictions: n_stations_event ≥ 1 untuk kejadian               | PASS     |                                                                                                               |
| predictions: sensor hanya EH/BH/HH                             | PASS     |                                                                                                               |
| waveforms: jumlah sesuai keranjang                             | PASS     | 48 dari 48                                                                                                    |
| waveforms: tiap entri 600 titik                                | PASS     |                                                                                                               |
| waveforms: semua rid ada di predictions                        | PASS     |                                                                                                               |
| LPA: sama dengan pemetaan lama g2_communities                  | PASS     | 100.0% stasiun                                                                                                |
| stations: 642 baris                                            | PASS     | 642                                                                                                           |
| stations: semua punya koordinat                                | PASS     |                                                                                                               |
| PageRank: 10 teratas sama, urutan sama                         | PASS     | UW.GNW, PB.B201, PB.B018, UW.HDW, PB.B941, UW.LTY, PB.B202, PB.B203, UW.DOSE, PB.B013                         |
| PageRank: skor ±0,01                                           | PASS     |                                                                                                               |
| LPA: tetap 8 kelompok utama + 2 kecil                          | PASS     | 10 kelompok terhubung                                                                                         |
| LPA K1: ukuran dalam toleransi                                 | PASS     | 246 vs 246                                                                                                    |
| LPA K1: lokasi rata-rata dekat                                 | PASS     | selisih 0.00°                                                                                                 |
| LPA K2: ukuran dalam toleransi                                 | PASS     | 125 vs 125                                                                                                    |
| LPA K2: lokasi rata-rata dekat                                 | PASS     | selisih 0.00°                                                                                                 |
| LPA K3: ukuran dalam toleransi                                 | PASS     | 61 vs 61                                                                                                      |
| LPA K3: lokasi rata-rata dekat                                 | PASS     | selisih 0.00°                                                                                                 |
| LPA K4: ukuran dalam toleransi                                 | PASS     | 48 vs 48                                                                                                      |
| LPA K4: lokasi rata-rata dekat                                 | PASS     | selisih 0.00°                                                                                                 |
| LPA K5: ukuran dalam toleransi                                 | PASS     | 24 vs 24                                                                                                      |
| LPA K5: lokasi rata-rata dekat                                 | PASS     | selisih 0.00°                                                                                                 |
| LPA K6: ukuran dalam toleransi                                 | PASS     | 22 vs 22                                                                                                      |
| LPA K6: lokasi rata-rata dekat                                 | PASS     | selisih 0.00°                                                                                                 |
| LPA K7: ukuran dalam toleransi                                 | PASS     | 12 vs 12                                                                                                      |
| LPA K7: lokasi rata-rata dekat                                 | PASS     | selisih 0.00°                                                                                                 |
| LPA K8: ukuran dalam toleransi                                 | PASS     | 7 vs 7                                                                                                        |
| LPA K8: lokasi rata-rata dekat                                 | PASS     | selisih 0.00°                                                                                                 |
| LPA lainnya: ukuran dalam toleransi                            | PASS     | 10 vs 10                                                                                                      |
| LPA lainnya: lokasi rata-rata dekat                            | PASS     | selisih 0.00°                                                                                                 |
| LPA terisolasi: ukuran dalam toleransi                         | PASS     | 87 vs 87                                                                                                      |
| LPA: K4 dan K5 kaya ledakan                                    | PASS     | [37.3, 44.2]                                                                                                  |
| LPA: K6 punya surface event tertinggi                          | PASS     | 17.4                                                                                                          |
| explosions: jumlah ≈ 6.392 (kejadian ledakan di G1)            | PASS     | 6,392                                                                                                         |
| explosions: semua punya koordinat                              | PASS     |                                                                                                               |
| stations_per_event earthquake: jumlah kejadian                 | PASS     | 39631                                                                                                         |
| stations_per_event earthquake: share ±0,002                    | PASS     | [0.175, 0.328, 0.446, 0.051]                                                                                  |
| stations_per_event explosion: jumlah kejadian                  | PASS     | 6392                                                                                                          |
| stations_per_event explosion: share ±0,002                     | PASS     | [0.337, 0.444, 0.214, 0.005]                                                                                  |
| stations_per_event surface_event: jumlah kejadian              | PASS     | 5425                                                                                                          |
| stations_per_event surface_event: share ±0,002                 | PASS     | [0.777, 0.126, 0.091, 0.007]                                                                                  |
| office_hours earthquake: sama dengan a2_context_by_class.md    | PASS     | 0.249 vs 0.249                                                                                                |
| office_hours explosion: sama dengan a2_context_by_class.md     | PASS     | 0.878 vs 0.878                                                                                                |
| office_hours surface_event: sama dengan a2_context_by_class.md | PASS     | 0.255 vs 0.255                                                                                                |
| office_hours noise: sama dengan a2_context_by_class.md         | PASS     | 0.298 vs 0.298                                                                                                |
| network_average: rekaman = 187.751                             | PASS     | 187751                                                                                                        |
| network_average earthquake vs PRD ±0,05                        | PASS     | 86.7 vs 86.7                                                                                                  |
| network_average explosion vs PRD ±0,05                         | PASS     | 8.6 vs 8.6                                                                                                    |
| network_average surface_event vs PRD ±0,05                     | FAIL     | 4.7 vs 4.8                                                                                                    |
| states: 3 negara bagian                                        | PASS     |                                                                                                               |
| states: ≤ 50 KB                                                | PASS     | 16,022 byte, 3 desimal                                                                                        |
| docs/data: total < 10 MB                                       | PASS     | 3.32 MB                                                                                                       |
| summary: provenance mencakup semua file                        | PASS     | ['explosions.csv', 'predictions.csv', 'states.json', 'stations.csv', 'summary.json', 'waveforms_sample.json'] |
