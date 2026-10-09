# Perbandingan kolom metadata antar file

Kolom bersarang: noise (11) ⊂ exotic (17) ⊂ comcat (37). Tidak ada kolom yang hanya dimiliki noise atau exotic.

| group        |   comcat |   exotic |   noise | reason                                                                              |
|:-------------|---------:|---------:|--------:|:------------------------------------------------------------------------------------|
| station      |        7 |        7 |       7 | Stasiun perekam — ada di semua file (setiap rekaman pasti punya stasiun)            |
| trace        |        3 |        3 |       3 | Info rekaman (pointer ke HDF5, waktu mulai, sampling rate) — ada di semua file      |
| label        |        2 |        1 |       1 | Label kelas                                                                         |
| event        |        1 |        1 |       0 | Identitas kejadian — noise tidak punya kejadian                                     |
| picks        |        5 |        5 |       0 | Waktu tiba gelombang P/S & kualitasnya — hanya ada kalau ada kejadian (noise tidak) |
| picks_detail |        3 |        0 |       0 | Detail pick (ketidakpastian, polaritas) — hanya dihitung di katalog resmi ComCat    |
| source       |       14 |        0 |       0 | Lokasi/kedalaman/magnitudo sumber — hanya dihitung untuk kejadian di katalog ComCat |
| quality      |        2 |        0 |       0 | Flag kualitas rekaman — hanya disediakan tim PNW-ML untuk ComCat                    |

| column                                 | group        | comcat   | exotic   | noise   |
|:---------------------------------------|:-------------|:---------|:---------|:--------|
| source_type                            | label        | ✓        | ✓        | ✓       |
| station_network_code                   | station      | ✓        | ✓        | ✓       |
| station_channel_code                   | station      | ✓        | ✓        | ✓       |
| station_code                           | station      | ✓        | ✓        | ✓       |
| station_location_code                  | station      | ✓        | ✓        | ✓       |
| station_latitude_deg                   | station      | ✓        | ✓        | ✓       |
| station_longitude_deg                  | station      | ✓        | ✓        | ✓       |
| station_elevation_m                    | station      | ✓        | ✓        | ✓       |
| trace_name                             | trace        | ✓        | ✓        | ✓       |
| trace_sampling_rate_hz                 | trace        | ✓        | ✓        | ✓       |
| trace_start_time                       | trace        | ✓        | ✓        | ✓       |
| event_id                               | event        | ✓        | ✓        | –       |
| trace_S_arrival_sample                 | picks        | ✓        | ✓        | –       |
| trace_P_arrival_sample                 | picks        | ✓        | ✓        | –       |
| trace_S_onset                          | picks        | ✓        | ✓        | –       |
| trace_P_onset                          | picks        | ✓        | ✓        | –       |
| trace_snr_db                           | picks        | ✓        | ✓        | –       |
| source_type_pnsn_label                 | label        | ✓        | –        | –       |
| trace_S_arrival_uncertainty_s          | picks_detail | ✓        | –        | –       |
| trace_P_arrival_uncertainty_s          | picks_detail | ✓        | –        | –       |
| trace_P_polarity                       | picks_detail | ✓        | –        | –       |
| trace_missing_channel                  | quality      | ✓        | –        | –       |
| trace_has_offset                       | quality      | ✓        | –        | –       |
| source_origin_time                     | source       | ✓        | –        | –       |
| source_latitude_deg                    | source       | ✓        | –        | –       |
| source_longitude_deg                   | source       | ✓        | –        | –       |
| source_depth_km                        | source       | ✓        | –        | –       |
| preferred_source_magnitude             | source       | ✓        | –        | –       |
| preferred_source_magnitude_type        | source       | ✓        | –        | –       |
| preferred_source_magnitude_uncertainty | source       | ✓        | –        | –       |
| source_depth_uncertainty_km            | source       | ✓        | –        | –       |
| source_horizontal_uncertainty_km       | source       | ✓        | –        | –       |
| source_local_magnitude                 | source       | ✓        | –        | –       |
| source_local_magnitude_uncertainty     | source       | ✓        | –        | –       |
| source_duration_magnitude              | source       | ✓        | –        | –       |
| source_duration_magnitude_uncertainty  | source       | ✓        | –        | –       |
| source_hand_magnitude                  | source       | ✓        | –        | –       |
