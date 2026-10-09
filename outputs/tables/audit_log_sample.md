# Potongan audit log NameNode (hdfs-audit.log)

allowed=false = akses ditolak permission.

| time                    | allowed   | ugi       | ip        | cmd         | src                                      | dst   |
|:------------------------|:----------|:----------|:----------|:------------|:-----------------------------------------|:------|
| 2026-09-24 06:09:41,981 | true      | guest     | 127.0.0.1 | checkAccess | /datalake/raw/exotic/exotic_metadata.csv | null  |
| 2026-09-24 06:09:42,506 | true      | engineer  | 127.0.0.1 | getfileinfo | /datalake/raw/exotic/_acl_test_engineer  | null  |
| 2026-09-24 06:09:42,530 | false     | engineer  | 127.0.0.1 | create      | /datalake/raw/exotic/_acl_test_engineer  | null  |
| 2026-09-24 06:09:43,104 | true      | scientist | 127.0.0.1 | getfileinfo | /datalake/raw/exotic/_acl_test_scientist | null  |
| 2026-09-24 06:09:43,130 | false     | scientist | 127.0.0.1 | create      | /datalake/raw/exotic/_acl_test_scientist | null  |
| 2026-09-24 06:09:43,745 | true      | guest     | 127.0.0.1 | getfileinfo | /datalake/raw/exotic/_acl_test_guest     | null  |
| 2026-09-24 06:09:43,766 | false     | guest     | 127.0.0.1 | create      | /datalake/raw/exotic/_acl_test_guest     | null  |
| 2026-09-24 06:09:52,224 | true      | engineer  | 127.0.0.1 | getfileinfo | /datalake/processed/_acl_test_engineer   | null  |
| 2026-09-24 06:09:52,245 | true      | engineer  | 127.0.0.1 | create      | /datalake/processed/_acl_test_engineer   | null  |
| 2026-09-24 06:09:52,880 | true      | engineer  | 127.0.0.1 | getfileinfo | /datalake/processed/_acl_test_engineer   | null  |
| 2026-09-24 06:09:52,909 | true      | engineer  | 127.0.0.1 | delete      | /datalake/processed/_acl_test_engineer   | null  |
| 2026-09-24 06:09:53,489 | true      | scientist | 127.0.0.1 | getfileinfo | /datalake/processed/_acl_test_scientist  | null  |
| 2026-09-24 06:09:53,508 | false     | scientist | 127.0.0.1 | create      | /datalake/processed/_acl_test_scientist  | null  |
| 2026-09-24 06:09:54,031 | false     | guest     | 127.0.0.1 | getfileinfo | /datalake/processed/_acl_test_guest      | null  |
| 2026-09-24 06:09:56,335 | true      | scientist | 127.0.0.1 | getfileinfo | /datalake/processed/_acl_test            | null  |
| 2026-09-24 06:09:56,355 | false     | scientist | 127.0.0.1 | create      | /datalake/processed/_acl_test            | null  |
| 2026-09-24 06:09:56,905 | true      | scientist | 127.0.0.1 | getfileinfo | /datalake/processed/_spoof_test          | null  |
| 2026-09-24 06:09:56,930 | false     | scientist | 127.0.0.1 | create      | /datalake/processed/_spoof_test          | null  |
| 2026-09-24 06:09:57,494 | true      | engineer  | 127.0.0.1 | getfileinfo | /datalake/processed/_spoof_test          | null  |
| 2026-09-24 06:09:57,514 | true      | engineer  | 127.0.0.1 | create      | /datalake/processed/_spoof_test          | null  |
