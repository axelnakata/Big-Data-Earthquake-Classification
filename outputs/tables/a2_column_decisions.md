# 11 kolom CSV yang ada di ketiga dataset dan perannya

| column                 | decision   | reason                                                 |
|:-----------------------|:-----------|:-------------------------------------------------------|
| source_type            | dipakai    | label (versi bersih A1: kolom `label`)                 |
| station_network_code   | disimpan   | hanya untuk graph analytics Bab 6, bukan fitur         |
| station_channel_code   | dipakai    | fitur jenis sensor EH/BH/HH (notebook 09)              |
| station_code           | disimpan   | hanya untuk graph analytics Bab 6, bukan fitur         |
| station_location_code  | dibuang    | lokasi: posisi sensor di dalam stasiun                 |
| station_latitude_deg   | dibuang    | lokasi: 41 stasiun hanya merekam 1 kelas               |
| station_longitude_deg  | dibuang    | lokasi: 41 stasiun hanya merekam 1 kelas               |
| station_elevation_m    | dibuang    | lokasi: 41 stasiun hanya merekam 1 kelas               |
| trace_name             | dipakai    | kunci ke waveform                                      |
| trace_sampling_rate_hz | dibuang    | selalu 100 Hz, tidak membawa informasi                 |
| trace_start_time       | dipakai    | fitur waktu: jam, hari, hari dalam tahun (notebook 09) |
