# Trace HDF5 vs baris metadata

README Nov 2025 menyebut 4,970 ComCat & 445 Noise dihapus dari CSV. Selisih ComCat kita lebih besar → sebagian slot sudah tidak dirujuk sejak rilis awal.

| dataset   |   traces_in_hdf5 |   metadata_rows |   distinct_slots_referenced |   orphans |
|:----------|-----------------:|----------------:|----------------------------:|----------:|
| comcat    |           187053 |          178939 |                      178939 |      8114 |
| exotic    |             9517 |            9267 |                        9267 |       250 |
| noise     |            51462 |           51017 |                       50622 |       840 |
