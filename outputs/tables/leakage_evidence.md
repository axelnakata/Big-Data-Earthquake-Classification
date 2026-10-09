# Bukti leakage: aturan sederhana dari kolom metadata vs kelas

Keberadaan kolom (bukan isi sinyal) sudah memisahkan kelas → kolom-kolom ini dilarang jadi fitur model.

| aturan                                       | rule   |   earthquake |   explosion |   noise |   surface_event |
|:---------------------------------------------|:-------|-------------:|------------:|--------:|----------------:|
| punya trace_P_arrival_sample                 | True   |       163064 |       15875 |       0 |            8804 |
| punya trace_P_arrival_sample                 | False  |            0 |           0 |   51017 |             108 |
| punya magnitudo (preferred_source_magnitude) | True   |       163064 |       15875 |       0 |               0 |
| punya magnitudo (preferred_source_magnitude) | False  |            0 |           0 |   51017 |            8912 |
| n_samples = 18001                            | True   |            0 |           0 |       0 |            8912 |
| n_samples = 18001                            | False  |       163064 |       15875 |   51017 |               0 |
| punya event_id                               | True   |       163064 |       15875 |       0 |            8912 |
| punya event_id                               | False  |            0 |           0 |   51017 |               0 |
