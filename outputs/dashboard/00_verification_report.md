# Phase 0 — Verification report (PRD_Final_Dashboard v1.0)

Checked 2026-11-09 against the code base, notebook code and HDFS (read-only Spark inspection, HDFS NameNode + DataNode running).
✓ confirmed · ✗ different (real value given) · ? could not check.

## Differences that matter

| # | PRD statement | Real value | What was done |
|---|---|---|---|
| 1 | §6.3 "the station → group mapping was never saved" | ✗ It was saved: `/datalake/graph/g2_communities` (columns `id`, `label`), written 2026-10-17 by `scripts/fig_623_communities_map.py` | PRD re-run still done to the new path. Re-run compared to this saved mapping |
| 2 | §6.5, §7.5, §12.2 network average *surface event* ≈ 4.8% | ✗ **4.7%** (8,912 / 187,751 = 4.747%). 4.8 comes from averaging the already-rounded group percentages | Dashboard uses the recomputed 4.7. Check the report text if it quotes 4.8 |
| 3 | §6.5 office hours "between 08:00 and 17:00" | Clarification: notebook 07 cell 20 uses `hour BETWEEN 8 AND 16`, so 08:00–16:59, 17:00 excluded | Reused exactly |
| 4 | §7.5 K6 "near the Three Sisters" | ✗ K6 centre is 101 km from Three Sisters; 0 of 22 stations within 30 km. K6 is about 42 km from Newberry Volcano (✓), with 14 of 22 stations within 30 km | Dashboard mentions Newberry only |

## §11 open checks

| # | Check | Result |
|---|---|---|
| 1 | Schema of `/datalake/ml/predictions` | ✓ `dataset, trace_name, label, pred, p_earthquake, p_explosion, p_surface_event, p_noise` (float), partition `split` (`test` 35,341 · `val` 35,078). No duplicate keys in test |
| 2 | Metadata column names | ✓ `label, event_id, station_network_code, station_code, station_channel_code, trace_start_time, source_latitude_deg, source_longitude_deg, preferred_source_magnitude, source_origin_time` all exist. Times are `timestamp` (UTC). `source_origin_time` and epicentre are null for `exotic` and `noise`; only `comcat` has them |
| 3 | Does `/datalake/ml/traces` have station/time columns? | ✓ for `station_network_code, station_code, station_channel_code, trace_start_time`. It has no `event_id`, so `n_stations_event` needs `/datalake/processed/metadata`. The export joins metadata |
| 4 | ID formats | ✓ `g1_edges.src` = `ev:comcat:<id>` or `ev:exotic:<id>`; `g1_edges.dst` and `g2_vertices.id` = `st:NET.STA`; `g2_vertices.name` = `NET.STA` (0 mismatches) |
| 5 | PageRank reproduces Table 27 | ✓ Exactly, same 10 stations, same order: UW.GNW 4.433 · PB.B201 4.288 · PB.B018 4.232 · UW.HDW 3.933 · PB.B941 3.810 · UW.LTY 3.666 · PB.B202 3.548 · PB.B203 3.429 · UW.DOSE 3.278 · PB.B013 3.278 |
| 6 | Code behind `a2_context_by_class.md` | ✓ Notebook 07 cell 20. `from_utc_timestamp(trace_start_time, 'America/Los_Angeles')` (DST-aware), `dayofweek` 2–6 and `hour` 8–16. Computed on all 237,978 metadata rows (recordings), not only test |
| 7 | `waveforms_z150s` | ✓ Column `z`, `array<float>`, length 15,000, z-scored (mean ≈ 0, std ≈ 1 on a 200-row sample). `N = 15000`, `CROP = 12000`, evaluation start `(N − CROP) // 2 = 1500` in `src/ml_prep.py` |
| 8 | Explosion events with coordinates vs G1 | ✓ 6,392 distinct events, all with coordinates, none with several coordinates, no null magnitudes; G1 also has 6,392 |
| 9 | Base-map licence | ✓ `us-atlas@3.0.1`: ISC licence (`package.json`). Geometry derived from US Census Bureau cartographic boundary files, 2017 edition (package README). File `states-10m.json`, 114,554 bytes |
| 10 | `.gitignore` rules | ✗ blocker for Phase 3 only: `*.csv` blocks `docs/data/*.csv`. `*.json` is not ignored. Phase 3 needs a narrow exception for `docs/data/*.csv`. `outputs/dashboard/rid_map.csv` stays ignored, as wanted |
| 11 | GitHub repo | ✓ `origin` = `github.com/axelnakata/Big-Data-Earthquake-Classification`. Pages URL pattern as in the PRD; live check is Phase 3 |

## Other PRD statements

| Section | Statement | Result |
|---|---|---|
| §1.1 | 237,978 records | ✓ metadata count |
| §1.1, §12.1 | Test 35,341; confusion matrix | ✓ Recomputed from HDFS, every cell equals `a2_confusion_matrix.md` and §12.1 |
| §1.1, §12.1 | Accuracy 0.925, macro-F1 0.861; per-class F1 | ✓ `a2_test_metrics_*.md` (0.9249 / 0.8609) |
| §1.1 | Baseline 0.677 / 0.202 | ✓ `a2_test_metrics_overall.md` |
| §1.1 | G1: 51,448 events + 642 stations, 187,751 edges; G2 8,637 edges | ✓ `g1_vertices` 52,090 rows (= 51,448 + 642), `g1_edges` 187,751, `g2_vertices` 642, `g2_edges` 8,637 |
| §1.1, §6.3 | Label propagation groups | ✓ Re-run sizes 246, 125, 61, 48, 24, 22, 12, 7, then 6 + 4 = 10, isolated 87. Station→label mapping identical to the saved `g2_communities` (100%) |
| §4 | 71 GB processed waveforms | ✓ README 71.37 GB; CLAUDE.md "66.5 GB" is the same size in GiB |
| §5, §6 | Notebook 12 cells 3, 16, 19 | ✓ Cell numbers and parameters match (`pageRank(resetProbability=0.15, maxIter=20)`, `labelPropagation(maxIter=10)`, `e2_both`) |
| §6.1 | `n_stations_event` empty iff noise | ✓ All 7,616 noise test rows have no event; 0 event rows missing a G1 degree |
| §6.1 | Sensors EH / BH / HH | ✓ Only these three values |
| §6.2 | Crop 1,500–13,499 | ✓ Same as `ml_prep.crop(train=False)` |
| §6.5 | Stations per event, office-hours targets | Rechecked in the export notebook (see `01_export_report.md`) |
| §6.6 | us-atlas | ✓ See §11.9 |
| §1.1 | Report file `2702749701_BigData_ASSG2-Report` | ? Not on this machine. `outputs/tables/a2_*` were used instead |
| §4 | Free-host sleep rules, GitHub Pages limits | ? Not checked (web facts for report Bab 7.1). Verify before quoting them |
| §12.3 | Volcano coordinates from Wikipedia | ? Page not opened. All 11 are plausible |
| §12.4 | Kharita et al. quotations | ? Paper not on this machine |

## Conclusion
No ✗ blocks the export. Items 1–3 are recorded and handled.
