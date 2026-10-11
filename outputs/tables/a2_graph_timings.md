# Waktu setiap langkah graph analytics (Spark local[*], 10 core)

| langkah                        |   detik |
|:-------------------------------|--------:|
| G1: bangun & tulis vertex/edge |     2.1 |
| G2: self-join + hitung bobot   |     1.1 |
| G2: tulis vertex/edge          |     4.6 |
| G1: connected components       |    56.7 |
| G2: PageRank                   |    12.1 |
| G2: label propagation          |     3.6 |
| G2: triangle count             |     4.4 |
