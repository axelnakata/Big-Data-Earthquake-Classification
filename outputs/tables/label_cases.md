# Label ComCat vs kode PNSN (Tabel S2 Ni dkk. 2023)

| label_case   |   rows |   events |
|:-------------|-------:|---------:|
| consistent   | 161964 |    39385 |
| dropped      |    100 |       31 |
| mapping_only |  16508 |     6558 |
| relabeled    |    367 |       80 |

| label_case   | source_type   | source_type_pnsn_label   | pnsn_comcat_label   |   count |
|:-------------|:--------------|:-------------------------|:--------------------|--------:|
| consistent   | earthquake    | eq                       | earthquake          |  161901 |
| consistent   | explosion     | ex                       | explosion           |      63 |
| dropped      | earthquake    | su                       | surface event       |      72 |
| dropped      | explosion     | qb                       | quarry blast        |      21 |
| dropped      | earthquake    | sn                       | sonic boom          |       4 |
| dropped      | earthquake    | uk                       | unknown             |       3 |
| mapping_only | explosion     | px                       | explosion           |   15750 |
| mapping_only | earthquake    | lf                       | earthquake          |     758 |
| relabeled    | earthquake    | px                       | explosion           |     326 |
| relabeled    | explosion     | eq                       | earthquake          |      41 |
