# Pertanyaan awal tentang data

| id   | question                     | answer                                                                                                 |
|:-----|:-----------------------------|:-------------------------------------------------------------------------------------------------------|
| U1   | Nama kolom                   | comcat 37, exotic 17, noise 11 kolom; magnitudo = 5 kolom terpisah (local/duration/hand + uncertainty) |
| U2   | Kolom Noise/Exotic = ComCat? | Tidak — bersarang noise ⊂ exotic ⊂ comcat                                                              |
| U3   | Label noise                  | source_type ada, isinya 'noise' untuk semua baris                                                      |
| U4   | Jumlah baris                 | comcat 178,939, exotic 9,267, noise 51,017 (sama dengan proposal)                                      |
| U5   | trace_name unik antar file?  | Tidak — irisan comcat∩noise besar; + 395 duplikat di dalam noise                                       |
| U6   | dtype waveform               | float64                                                                                                |
| U7   | Struktur HDF5                | data/bucketK (N,3,samples), contiguous, tanpa kompresi; component_order = ENZ                          |
| U11  | Label PNSN                   | kode eq/lf/ex/px/qb/su/sn/uk (Tabel S2); 467 rekaman (111 event) tidak konsisten                       |
| U12  | SNR noise                    | Noise tidak punya kolom trace_snr_db sama sekali; ComCat/Exotic: nilai "nan" per komponen kosong       |
