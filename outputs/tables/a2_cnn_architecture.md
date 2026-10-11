# Arsitektur CNN (200,868 parameter)

| bagian   | lapisan                                                     | bentuk_keluaran   |   parameter |
|:---------|:------------------------------------------------------------|:------------------|------------:|
| wave.0   | Conv1d → BatchNorm → ReLU → MaxPool ÷4                      | (16, 3000)        |         160 |
| wave.1   | Conv1d → BatchNorm → ReLU → MaxPool ÷4                      | (32, 750)         |        3680 |
| wave.2   | Conv1d → BatchNorm → ReLU → MaxPool ÷4                      | (64, 187)         |       14528 |
| wave.3   | Conv1d → BatchNorm → ReLU → MaxPool ÷4                      | (128, 46)         |       57728 |
| wave.4   | Conv1d                                                      | (128, 46)         |      114816 |
| wave.5   | BatchNorm1d                                                 | (128, 46)         |         256 |
| wave.6   | ReLU                                                        | (128, 46)         |           0 |
| wave.7   | AdaptiveAvgPool1d                                           | (128, 1)          |           0 |
| wave.8   | Flatten                                                     | (128,)            |           0 |
| context  | Linear 9 → 16 → ReLU                                        | (16,)             |         160 |
| head     | gabung 128 + 16 → Linear 64 → ReLU → Dropout 0.3 → Linear 4 | (4,)              |        9540 |
