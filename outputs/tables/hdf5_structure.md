# Struktur internal file HDF5

component_order: {'comcat': 'ENZ', 'exotic': 'ENZ', 'noise': 'ENZ'}. 1 trace ComCat = 3 × 15,001 × 8 byte = 360 KB.

| dataset   | hdf5_path     | shape             | dtype   | chunks   | compression   |     MB |
|:----------|:--------------|:------------------|:--------|:---------|:--------------|-------:|
| comcat    | data/bucket1  | (18790, 3, 15001) | float64 | None     | None          | 6764.9 |
| comcat    | data/bucket10 | (18646, 3, 15001) | float64 | None     | None          | 6713   |
| comcat    | data/bucket2  | (18568, 3, 15001) | float64 | None     | None          | 6684.9 |
| comcat    | data/bucket3  | (18545, 3, 15001) | float64 | None     | None          | 6676.6 |
| comcat    | data/bucket4  | (18764, 3, 15001) | float64 | None     | None          | 6755.5 |
| comcat    | data/bucket5  | (18954, 3, 15001) | float64 | None     | None          | 6823.9 |
| comcat    | data/bucket6  | (18497, 3, 15001) | float64 | None     | None          | 6659.4 |
| comcat    | data/bucket7  | (18751, 3, 15001) | float64 | None     | None          | 6750.8 |
| comcat    | data/bucket8  | (18794, 3, 15001) | float64 | None     | None          | 6766.3 |
| comcat    | data/bucket9  | (18744, 3, 15001) | float64 | None     | None          | 6748.3 |
| exotic    | data/bucket1  | (8998, 3, 18001)  | float64 | None     | None          | 3887.4 |
| exotic    | data/bucket2  | (370, 3, 18001)   | float64 | None     | None          |  159.8 |
| exotic    | data/bucket3  | (146, 3, 18001)   | float64 | None     | None          |   63.1 |
| exotic    | data/bucket4  | (3, 3, 18001)     | float64 | None     | None          |    1.3 |
| noise     | data/bucket1  | (5163, 3, 15001)  | float64 | None     | None          | 1858.8 |
| noise     | data/bucket10 | (5129, 3, 15001)  | float64 | None     | None          | 1846.6 |
| noise     | data/bucket2  | (5160, 3, 15001)  | float64 | None     | None          | 1857.7 |
| noise     | data/bucket3  | (5157, 3, 15001)  | float64 | None     | None          | 1856.6 |
| noise     | data/bucket4  | (5154, 3, 15001)  | float64 | None     | None          | 1855.6 |
| noise     | data/bucket5  | (5149, 3, 15001)  | float64 | None     | None          | 1853.8 |
| noise     | data/bucket6  | (5142, 3, 15001)  | float64 | None     | None          | 1851.2 |
| noise     | data/bucket7  | (5140, 3, 15001)  | float64 | None     | None          | 1850.5 |
| noise     | data/bucket8  | (5135, 3, 15001)  | float64 | None     | None          | 1848.7 |
| noise     | data/bucket9  | (5133, 3, 15001)  | float64 | None     | None          | 1848   |
