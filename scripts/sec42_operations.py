"""Bab 4.2.2 — Operasi data Spark pada processed zone.

Baca-saja dari /datalake/processed/{metadata,waveforms}.
5 operasi utama dijalankan 3x, waktu dilaporkan median (detik). Fungsi bawaan Spark saja
(DataFrame API / SQL / array functions transform-aggregate-array_max), tanpa UDF Python.

Pengecualian yang disengaja: pengecekan tambahan #2 (kode PNSN `qb`) butuh baris qb, tapi
baris itu sudah DIBUANG saat cleaning (notebook 03, aturan R3) sehingga tidak ada di processed sama
sekali. Untuk menghitung dampak skenario "qb dipertahankan", 21 baris itu dibaca dari raw zone
(read-only, tidak diubah) — dicatat di laporan, bukan workaround diam-diam.

Output: outputs/facts/42_facts.json (angka mentah) + outputs/facts/42_operations_summary.md.

Jalankan dari root project: .venv/bin/python scripts/sec42_operations.py
"""
import json, os, sys, time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from common import HDFS, PROCESSED, RAW, ROOT, spark_session
from pyspark.sql import functions as F, Window
import pandas as pd

OUT_FACTS = os.path.join(ROOT, 'outputs', 'facts', '42_facts.json')
OUT_REPORT = os.path.join(ROOT, 'outputs', 'facts', '42_operations_summary.md')


def median_time(fn, runs=3):
    """Run fn() `runs` times, return (last result, median seconds, all seconds)."""
    times, result = [], None
    for _ in range(runs):
        t0 = time.time()
        result = fn()
        times.append(time.time() - t0)
    return result, sorted(times)[len(times) // 2], [round(t, 3) for t in times]


def main():
    spark = spark_session('42_ops', driver_mem='12g')
    meta = spark.read.parquet(f'{HDFS}{PROCESSED}/metadata')
    wf = spark.read.parquet(f'{HDFS}{PROCESSED}/waveforms')
    facts = {'spark_config': {'master': 'local[*]', 'driver_memory': '12g'}, 'ops': {}, 'checks': {}}

    # ---------------------------------------------------------------- Op 1
    def op1():
        return (meta.filter(F.col('label').isNotNull())
                    .groupBy('label').count().orderBy(F.desc('count')).collect())
    r1, t1, runs1 = median_time(op1)
    facts['ops']['op1_class_count'] = {
        'question': 'Berapa jumlah rekaman per kelas?',
        'result': {row['label']: row['count'] for row in r1},
        'seconds_median': round(t1, 2), 'seconds_runs': runs1}
    print('[op1] selesai', facts['ops']['op1_class_count']['result'])

    # ---------------------------------------------------------------- Op 2
    def build_events():
        return (meta.filter(F.col('event_id').isNotNull())
                    .groupBy('dataset', 'event_id')
                    .agg(F.first('label').alias('label'),
                         F.first('preferred_source_magnitude').alias('magnitude'),
                         F.first('preferred_source_magnitude_type').alias('magnitude_type'),
                         F.first('source_origin_time').alias('origin_time')))

    def op2():
        events = build_events()
        w = Window.partitionBy('label').orderBy(F.desc('magnitude'))
        top1 = (events.withColumn('rn', F.row_number().over(w)).filter('rn = 1')
                      .filter(F.col('label').isin('earthquake', 'explosion'))
                      .withColumn('year', F.year('origin_time')))
        return top1.select('label', 'event_id', 'magnitude', 'magnitude_type', 'year').collect()
    r2, t2, runs2 = median_time(op2)
    facts['ops']['op2_biggest_event_per_class'] = {
        'question': 'Kejadian mana yang terbesar per kelas (earthquake, explosion), dihitung per event_id unik',
        'result': [{'label': r['label'], 'event_id': r['event_id'], 'magnitude': r['magnitude'],
                    'magnitude_type': r['magnitude_type'], 'year': r['year']} for r in r2],
        'seconds_median': round(t2, 2), 'seconds_runs': runs2}
    print('[op2] selesai', facts['ops']['op2_biggest_event_per_class']['result'])

    # ---------------------------------------------------------------- Op 3
    def op3():
        return meta.groupBy('station_network_code').pivot('label').count().fillna(0).collect()
    r3, t3, runs3 = median_time(op3)
    net = pd.DataFrame([row.asDict() for row in r3]).set_index('station_network_code')
    class_cols = [c for c in net.columns]
    net['total'] = net[class_cols].sum(axis=1)
    net_pct = net[class_cols].div(net['total'], axis=0) * 100
    top3 = net.sort_values('total', ascending=False).head(3)
    overall_pct = net[class_cols].sum() / net[class_cols].sum().sum() * 100
    dev = (net_pct.loc[top3.index] - overall_pct).abs()
    worst_net, worst_class = dev.stack().idxmax()
    finding = (f'Jaringan {worst_net}: kelas {worst_class} = {net_pct.loc[worst_net, worst_class]:.1f}% dari '
               f'rekaman jaringan itu, vs {overall_pct[worst_class]:.1f}% rata-rata semua jaringan '
               f'(selisih {dev.loc[worst_net, worst_class]:.1f} poin persen) — sinyal jalan pintas kelas-jaringan.')
    facts['ops']['op3_pivot_network_class'] = {
        'question': 'Bagaimana proporsi kelas di setiap jaringan stasiun?',
        'top3_networks_by_records': {n: int(top3.loc[n, 'total']) for n in top3.index},
        'pct_per_class_top3': {n: {c: round(v, 2) for c, v in net_pct.loc[n].to_dict().items()} for n in top3.index},
        'most_notable_finding': finding,
        'seconds_median': round(t3, 2), 'seconds_runs': runs3}
    print('[op3] selesai;', finding)

    # ---------------------------------------------------------------- Op 4
    def op4():
        base = wf.join(F.broadcast(meta.select('dataset', 'trace_name', 'label')), ['dataset', 'trace_name'])
        mean_raw = F.aggregate('z', F.lit(0.0), lambda acc, x: acc + x) / F.size('z')
        raw_peak_abs = F.array_max(F.transform('z', lambda x: F.abs(x)))
        feat = base.withColumn('mean_raw', mean_raw).withColumn('raw_peak_abs', raw_peak_abs)
        demeaned_abs = F.transform('z', lambda x: F.abs(x - F.col('mean_raw')))
        feat = (feat.withColumn('demeaned_peak', F.array_max(demeaned_abs))
                    .withColumn('demeaned_mean', F.aggregate(demeaned_abs, F.lit(0.0), lambda acc, x: acc + x) / F.size('z'))
                    .withColumn('is_empty_z', F.col('raw_peak_abs') == 0)
                    .withColumn('peak_ratio', F.col('demeaned_peak') / F.col('demeaned_mean')))
        empty_ct = {r['label']: r['n'] for r in
                    feat.filter('is_empty_z').groupBy('label').agg(F.count('*').alias('n')).collect()}
        stats = (feat.filter('NOT is_empty_z').groupBy('label')
                     .agg(F.count('*').alias('n'),
                          F.round(F.expr('percentile_approx(peak_ratio, 0.25)'), 2).alias('q1'),
                          F.round(F.expr('percentile_approx(peak_ratio, 0.5)'), 2).alias('median'),
                          F.round(F.expr('percentile_approx(peak_ratio, 0.75)'), 2).alias('q3'))
                     .collect())
        return stats, empty_ct
    r4, t4, runs4 = median_time(op4)
    stats4, empty4 = r4
    facts['ops']['op4_peak_ratio_z'] = {
        'question': 'Seberapa menonjol lonjakan terbesar dibanding getaran rata-rata (komponen Z)?',
        'definition': 'demean per rekaman (z - mean(z)), lalu rasio = max(|z_demean|) / mean(|z_demean|); rekaman dengan z kosong (semua nol) dilewati dan dihitung terpisah',
        'result': {r['label']: {'n': r['n'], 'q1': r['q1'], 'median': r['median'], 'q3': r['q3']} for r in stats4},
        'skipped_empty_z_per_class': empty4,
        'seconds_median': round(t4, 2), 'seconds_runs': runs4}
    print('[op4] selesai', facts['ops']['op4_peak_ratio_z']['result'])

    # ---------------------------------------------------------------- Op 5
    def op5():
        events = build_events()
        stations = meta.groupBy('station_network_code', 'station_code').agg(F.count('*').alias('n_traces'))
        edges = (meta.filter(F.col('event_id').isNotNull())
                     .select(F.concat_ws(':', F.lit('ev'), 'dataset', 'event_id').alias('src'),
                             F.concat_ws(':', F.lit('st'), 'station_network_code', 'station_code').alias('dst'),
                             'label'))
        deg_ev = edges.groupBy('src', 'label').agg(F.countDistinct('dst').alias('stations_per_event'))
        per_class = (deg_ev.groupBy('label')
                            .agg(F.expr('percentile_approx(stations_per_event, 0.5)').alias('median_stations_per_event'),
                                 F.round(F.avg('stations_per_event'), 2).alias('avg_stations_per_event'))
                            .collect())
        return events.count(), stations.count(), edges.count(), per_class
    r5, t5, runs5 = median_time(op5)
    n_ev, n_st, n_edges, per_class5 = r5
    facts['ops']['op5_graph_degree'] = {
        'question': 'Setiap kejadian direkam oleh berapa stasiun?',
        'method': 'DataFrame (vertices + edges diturunkan dari metadata dengan groupBy/countDistinct), bukan GraphFrames — dependency tambahan tidak diperlukan untuk sekadar menghitung derajat',
        'n_event_nodes': n_ev, 'n_station_nodes': n_st, 'n_edges': n_edges,
        'stations_per_event_by_class': {r['label']: {'median': r['median_stations_per_event'],
                                                       'avg': r['avg_stations_per_event']} for r in per_class5},
        'seconds_median': round(t5, 2), 'seconds_runs': runs5}
    print('[op5] selesai', n_ev, n_st, n_edges)

    # -------------------------------------------------- Pemeriksaan tambahan 1: komponen kosong
    base_ck1 = wf.join(F.broadcast(meta.select('dataset', 'trace_name', 'label')), ['dataset', 'trace_name'])
    for comp in ('e', 'n', 'z'):
        base_ck1 = base_ck1.withColumn(f'{comp}_empty', F.array_max(F.transform(comp, lambda x: F.abs(x))) == 0)
    agg_cols = [F.count('*').alias('n')] + [F.sum(F.col(f'{c}_empty').cast('int')).alias(f'{c}_empty') for c in 'enz']
    ck1_dataset = base_ck1.groupBy('dataset').agg(*agg_cols).collect()
    ck1_label = base_ck1.groupBy('label').agg(*agg_cols).collect()
    facts['checks']['1_empty_components'] = {
        'question': 'Apakah komponen Z pernah kosong (semua nol)? Dibandingkan dengan E dan N.',
        'per_dataset': {r['dataset']: {'n': r['n'], 'e_empty': r['e_empty'], 'n_empty': r['n_empty'], 'z_empty': r['z_empty']}
                        for r in ck1_dataset},
        'per_class': {r['label']: {'n': r['n'], 'e_empty': r['e_empty'], 'n_empty': r['n_empty'], 'z_empty': r['z_empty']}
                      for r in ck1_label}}
    print('[check1] selesai', facts['checks']['1_empty_components']['per_dataset'])

    # -------------------------------------------------- Pemeriksaan tambahan 2: kode qb
    qb_raw = (spark.read.csv(f'{HDFS}{RAW}/comcat/comcat_metadata.csv', header=True, inferSchema=True)
                    .filter("source_type_pnsn_label = 'qb'"))
    qb_rows = qb_raw.count()
    qb_events = qb_raw.select('event_id').distinct()
    existing_events_comcat = meta.filter("dataset = 'comcat'").select('event_id').distinct()
    new_events = qb_events.join(existing_events_comcat, 'event_id', 'left_anti').count()

    counts_a = dict(facts['ops']['op1_class_count']['result'])
    counts_b = dict(counts_a); counts_b['explosion'] = counts_b.get('explosion', 0) + qb_rows
    facts['checks']['2_qb_code'] = {
        'meaning': 'qb = quarry blast (ledakan tambang)',
        'source': 'Tabel S2 (supplement) Ni dkk. (2023), Seismica 2(1) — dipetakan di notebooks/03_cleaning_quality.ipynb dan tercatat di outputs/tables/label_cases.md',
        'rows_dropped_currently': qb_rows,
        'note_scope_exception': ("21 baris qb tidak ada di /datalake/processed (dibuang saat cleaning, aturan R3) "
                                  "sehingga untuk cek dampak skenario ini baris qb dibaca dari raw zone (read-only, "
                                  "tidak diubah) — satu-satunya bacaan raw di skrip ini, "
                                  "disengaja dan dicatat di sini."),
        'scenario_a_current_qb_dropped': {
            'counts_per_class': counts_a, 'total_rows': sum(counts_a.values()),
            'n_events': n_ev, 'n_edges': n_edges},
        'scenario_b_qb_kept_as_explosion': {
            'counts_per_class': counts_b, 'total_rows': sum(counts_b.values()),
            'n_events': n_ev + new_events, 'n_edges': n_edges + qb_rows,
            'new_events_introduced_by_qb': new_events},
        'decision': 'Data TIDAK diubah oleh skrip ini. qb tetap dibuang sesuai aturan R3 (Tabel 11 laporan A1).'}
    print('[check2] selesai, qb_rows=', qb_rows, 'new_events=', new_events)

    # -------------------------------------------------- Pemeriksaan tambahan 3: unique event/station
    n_unique_events = meta.filter('event_id IS NOT NULL').select('dataset', 'event_id').distinct().count()
    n_unique_stations = meta.select('station_network_code', 'station_code').distinct().count()
    facts['checks']['3_unique_counts'] = {
        'unique_event_id_on_clean_data': n_unique_events,
        'unique_station_network_code_plus_station_code_on_clean_data': n_unique_stations}
    print('[check3] selesai', n_unique_events, n_unique_stations)

    os.makedirs(os.path.dirname(OUT_FACTS), exist_ok=True)
    json.dump(facts, open(OUT_FACTS, 'w'), indent=1, default=str)
    print('facts ->', OUT_FACTS)

    build_report(facts)
    print('laporan ->', OUT_REPORT)
    spark.stop()


def build_report(facts):
    o = facts['ops']
    ck = facts['checks']

    summary_rows = [
        ('Relasional', 'filter + groupBy + count',
         'Jumlah rekaman per kelas?',
         'earthquake {earthquake}, explosion {explosion}, surface_event {surface_event}, noise {noise}.'.format(
             **o['op1_class_count']['result']),
         o['op1_class_count']['seconds_median']),
        ('Relasional', 'window (row_number per kelas, urut magnitudo)',
         'Kejadian terbesar per kelas?',
         '; '.join(f"{r['label']} {r['event_id']} (M{r['magnitude']} {r['magnitude_type']}, {r['year']})"
                    for r in o['op2_biggest_event_per_class']['result']) + '.',
         o['op2_biggest_event_per_class']['seconds_median']),
        ('Relasional', 'pivot (kelas × station_network_code)',
         'Proporsi kelas per jaringan stasiun?',
         o['op3_pivot_network_class']['most_notable_finding'],
         o['op3_pivot_network_class']['seconds_median']),
        ('Array', 'transform + aggregate / array_max (komponen Z)',
         'Seberapa menonjol lonjakan terbesar dibanding getaran rata-rata?',
         '; '.join(f"{lab} median {v['median']}x (Q1 {v['q1']}–Q3 {v['q3']})"
                    for lab, v in o['op4_peak_ratio_z']['result'].items()) + '.',
         o['op4_peak_ratio_z']['seconds_median']),
        ('Graf', 'node + edge, hitung derajat',
         'Setiap kejadian direkam berapa stasiun?',
         '; '.join(f"{lab} median {v['median']} (rata-rata {v['avg']})"
                    for lab, v in o['op5_graph_degree']['stations_per_event_by_class'].items()) + '.',
         o['op5_graph_degree']['seconds_median']),
    ]
    summary_md = '| Model | Operasi | Pertanyaan | Hasil | Waktu (detik) |\n|---|---|---|---|---|\n'
    for model, opname, q, hasil, secs in summary_rows:
        summary_md += f'| {model} | {opname} | {q} | {hasil} | {secs} |\n'

    op1, op2, op3, op4, op5 = (o['op1_class_count'], o['op2_biggest_event_per_class'], o['op3_pivot_network_class'],
                                o['op4_peak_ratio_z'], o['op5_graph_degree'])

    def runs_note(op):
        return f"(3x run: {op['seconds_runs']} detik, median {op['seconds_median']})"

    detail = []
    detail.append('### Operasi 1 — filter + groupBy + count\n')
    detail.append(f"Hasil: {op1['result']}. {runs_note(op1)}\n")
    detail.append('### Operasi 2 — window function per event\n')
    for r in op2['result']:
        detail.append(f"- {r['label']}: `{r['event_id']}`, magnitudo {r['magnitude']} ({r['magnitude_type']}), tahun {r['year']}\n")
    detail.append(f"{runs_note(op2)}\n")
    detail.append('### Operasi 3 — pivot kelas × jaringan stasiun\n')
    detail.append(f"3 jaringan dengan rekaman terbanyak: {op3['top3_networks_by_records']}\n\n")
    detail.append('| jaringan | ' + ' | '.join(next(iter(op3['pct_per_class_top3'].values())).keys()) + ' |\n')
    detail.append('|---|' + '---|' * len(next(iter(op3['pct_per_class_top3'].values()))) + '\n')
    for net, pct in op3['pct_per_class_top3'].items():
        detail.append('| ' + net + ' | ' + ' | '.join(f'{v}%' for v in pct.values()) + ' |\n')
    detail.append(f"\nTemuan paling mencolok: {op3['most_notable_finding']} {runs_note(op3)}\n")
    detail.append('### Operasi 4 — rasio puncak komponen Z (array)\n')
    detail.append(f"Definisi: {op4['definition']}\n\n")
    detail.append('| kelas | n | Q1 | median | Q3 |\n|---|---|---|---|---|\n')
    for lab, v in op4['result'].items():
        detail.append(f"| {lab} | {v['n']} | {v['q1']} | {v['median']} | {v['q3']} |\n")
    detail.append(f"\nRekaman z kosong dilewati (per kelas): {op4['skipped_empty_z_per_class']}. {runs_note(op4)}\n")
    detail.append('### Operasi 5 — graph event ↔ stasiun\n')
    detail.append(f"Metode: {op5['method']}\n\n")
    detail.append(f"Node kejadian: {op5['n_event_nodes']}, node stasiun: {op5['n_station_nodes']}, edge: {op5['n_edges']}.\n\n")
    detail.append('| kelas | median stasiun/kejadian | rata-rata stasiun/kejadian |\n|---|---|---|\n')
    for lab, v in op5['stations_per_event_by_class'].items():
        detail.append(f"| {lab} | {v['median']} | {v['avg']} |\n")
    detail.append(f"\n{runs_note(op5)}\n")

    ck1, ck2, ck3 = ck['1_empty_components'], ck['2_qb_code'], ck['3_unique_counts']
    checks_md = []
    checks_md.append('### 1. Apakah komponen Z pernah kosong?\n')
    checks_md.append('| dataset | n | E kosong | N kosong | Z kosong |\n|---|---|---|---|---|\n')
    for d, v in ck1['per_dataset'].items():
        checks_md.append(f"| {d} | {v['n']} | {v['e_empty']} | {v['n_empty']} | {v['z_empty']} |\n")
    checks_md.append('\n| kelas | n | E kosong | N kosong | Z kosong |\n|---|---|---|---|---|\n')
    for lab, v in ck1['per_class'].items():
        checks_md.append(f"| {lab} | {v['n']} | {v['e_empty']} | {v['n_empty']} | {v['z_empty']} |\n")
    z_total_empty = sum(v['z_empty'] for v in ck1['per_dataset'].values())
    z_claim = ('Klaim "komponen Z terisi pada seluruh rekaman" TERBUKTI.' if z_total_empty == 0 else
               'Klaim "komponen Z terisi pada seluruh rekaman" TIDAK terbukti — lihat rincian di atas.')
    checks_md.append(f"\nTotal rekaman dengan Z kosong: **{z_total_empty}**. {z_claim}\n")

    checks_md.append('\n### 2. Arti kode PNSN `qb`\n')
    checks_md.append(f"**{ck2['meaning']}**. Sumber: {ck2['source']}.\n\n")
    checks_md.append(f"Catatan cakupan: {ck2['note_scope_exception']}\n\n")
    a, b = ck2['scenario_a_current_qb_dropped'], ck2['scenario_b_qb_kept_as_explosion']
    checks_md.append('| skenario | ' + ' | '.join(a['counts_per_class'].keys()) + ' | total rekaman | jumlah kejadian | jumlah edge |\n')
    checks_md.append('|---|' + '---|' * len(a['counts_per_class']) + '---|---|---|\n')
    checks_md.append('| A: qb dibuang (saat ini) | ' + ' | '.join(str(v) for v in a['counts_per_class'].values())
                      + f" | {a['total_rows']} | {a['n_events']} | {a['n_edges']} |\n")
    checks_md.append('| B: qb dipertahankan sebagai explosion | ' + ' | '.join(str(v) for v in b['counts_per_class'].values())
                      + f" | {b['total_rows']} | {b['n_events']} | {b['n_edges']} |\n")
    checks_md.append(f"\n{ck2['decision']}\n")

    checks_md.append('\n### 3. Jumlah kejadian & stasiun unik (data bersih)\n')
    checks_md.append(f"- event_id unik: **{ck3['unique_event_id_on_clean_data']}**\n")
    checks_md.append(f"- (station_network_code, station_code) unik: **{ck3['unique_station_network_code_plus_station_code_on_clean_data']}**\n")

    verify_md = [
        "- Kuartil (Q1/median/Q3) Operasi 4 dan median di Operasi 5 dihitung dengan `percentile_approx` (pendekatan, bukan persentil eksak) — wajar untuk data sejumlah ratusan ribu baris, tapi disebut di sini agar tidak dianggap angka eksak.",
        "- Pengecekan tambahan #2 (kode `qb`) membaca raw zone, bukan hanya processed — lihat catatan cakupan di bagian itu; 21 baris qb tetap dibuang sesuai aturan R3.",
        "- Skrip ini mengasumsikan HDFS/Spark sudah berjalan (namenode+datanode aktif, lihat README) sebelum dijalankan.",
    ]

    md = f"""# Ringkasan Operasi Data — Subbab 4.2.2 (PNW-ML)

Dihasilkan oleh `scripts/sec42_operations.py`, dibaca dari `/datalake/processed/{{metadata,waveforms}}`.
Konfigurasi Spark: {facts['spark_config']['master']}, driver memory {facts['spark_config']['driver_memory']}.
Semua angka dihitung langsung dari data ; setiap operasi utama dijalankan 3x, waktu = median.

## 1. Ringkasan

{summary_md}
## 2. Rincian angka per operasi

{''.join(detail)}
## 3. Pemeriksaan tambahan

{''.join(checks_md)}
## 4. PERLU VERIFIKASI

{chr(10).join(verify_md)}
"""
    open(OUT_REPORT, 'w').write(md)


if __name__ == '__main__':
    main()
