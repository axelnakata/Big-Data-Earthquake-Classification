# Laporan kualitas data metadata (sebelum vs sesudah cleaning)

| dimension    | metric                                                | before                                                              | after                                         |
|:-------------|:------------------------------------------------------|:--------------------------------------------------------------------|:----------------------------------------------|
| Completeness | null % kolom kunci                                    | lihat tabel completeness                                            | tidak berubah untuk kolom asli; label 0% null |
| Validity     | sampling rate, jumlah sampel, pointer HDF5, SNR range | 0 pelanggaran                                                       | 0 pelanggaran                                 |
| Uniqueness   | duplikat (dataset, trace_name)                        | noise 790 baris (395 nilai)                                         | 0                                             |
| Consistency  | label ComCat vs PNSN (Tabel S2)                       | consistent 161,964, dropped 100, mapping_only 16,508, relabeled 367 | 367 di-relabel, 100 dibuang                   |
| Orphans      | slot HDF5 tanpa metadata                              | comcat 8,114, exotic 250, noise 840                                 | comcat 8,214, exotic 605, noise 1,235         |

## Validitas

| check                                     |   comcat |   exotic |   noise |
|:------------------------------------------|---------:|---------:|--------:|
| sampling_rate != 100 Hz                   |        0 |        0 |       0 |
| n_samples != expected (15001/18001)       |        0 |        0 |       0 |
| n_samples != HDF5 array length            |        0 |        0 |       0 |
| bucket not found in HDF5                  |        0 |        0 |       0 |
| row >= bucket size (pointer out of range) |        0 |        0 |       0 |
| SNR above 80 dB                           |        0 |        0 |       0 |
| SNR below -20 dB                          |        0 |        0 |       0 |
| trace_start_time is NULL                  |        0 |        0 |       0 |

## Completeness (null % kolom kunci)

| dataset   | stage   |   event_id |   source_type |   station_code |   trace_name |   trace_start_time |   trace_P_arrival_sample |   trace_snr_db |   label |
|:----------|:--------|-----------:|--------------:|---------------:|-------------:|-------------------:|-------------------------:|---------------:|--------:|
| comcat    | before  |          0 |             0 |              0 |            0 |                  0 |                     0    |              0 |       0 |
| comcat    | after   |          0 |             0 |              0 |            0 |                  0 |                     0    |              0 |       0 |
| exotic    | before  |          0 |             0 |              0 |            0 |                  0 |                     1.29 |              0 |       0 |
| exotic    | after   |          0 |             0 |              0 |            0 |                  0 |                     1.21 |              0 |       0 |
| noise     | before  |        100 |             0 |              0 |            0 |                  0 |                   100    |            100 |       0 |
| noise     | after   |        100 |             0 |              0 |            0 |                  0 |                   100    |            100 |       0 |

## Orphan waveform

| dataset   |   hdf5_traces |   orphans_before |   orphans_after |   readme_removed_nov2025 |   unexplained |
|:----------|--------------:|-----------------:|----------------:|-------------------------:|--------------:|
| comcat    |        187053 |             8114 |            8214 |                     4970 |          3144 |
| exotic    |          9517 |              250 |             605 |                        0 |           250 |
| noise     |         51462 |              840 |            1235 |                      445 |           395 |

## Flag kualitas (dipertahankan)

| dataset   |   flag_has_offset |   flag_missing_channel |
|:----------|------------------:|-----------------------:|
| comcat    |              1534 |                  53453 |
| exotic    |               nan |                    nan |
| noise     |               nan |                    nan |

## Distribusi kelas setelah cleaning

| dataset   | label         |   count |   pct_of_total |
|:----------|:--------------|--------:|---------------:|
| comcat    | earthquake    |  162700 |          68.37 |
| comcat    | explosion     |   16139 |           6.78 |
| exotic    | surface_event |    8912 |           3.74 |
| noise     | noise         |   50227 |          21.11 |
