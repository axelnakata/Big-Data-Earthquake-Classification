# Konversi waveform HDF5 → Parquet

Validasi: jumlah baris = metadata bersih; 100 trace acak per dataset identik bit-per-bit dengan HDF5 (np.array_equal).

| dataset   |   metadata_clean |   waveforms_parquet | match   |   seconds |   throughput_mb_s |   spark_tasks |   hdf5_raw_GB |   parquet_GB |   parquet_vs_hdf5_% |   checked |   identical |
|:----------|-----------------:|--------------------:|:--------|----------:|------------------:|--------------:|--------------:|-------------:|--------------------:|----------:|------------:|
| comcat    |           178839 |              178839 | True    |     284.3 |             226.5 |            88 |         67.34 |        53.73 |                79.8 |       100 |         100 |
| exotic    |             8912 |                8912 | True    |      20.3 |             189.9 |             5 |          4.11 |         2.54 |                61.7 |       100 |         100 |
| noise     |            50227 |               50227 | True    |      85.2 |             212.2 |            25 |         18.53 |        15.11 |                81.5 |       100 |         100 |
