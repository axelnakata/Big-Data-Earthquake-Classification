# Model data per jenis data

| entity           | key                   |   rows |
|:-----------------|:----------------------|-------:|
| EVENT            | (dataset, event_id)   |  51448 |
| STATION          | (network, station)    |    644 |
| TRACE (metadata) | (dataset, trace_name) | 237978 |
| WAVEFORM         | (dataset, trace_name) | 237978 |

| data                  | format                       | data model                                                                          | storage                                                                 | key                          | operations                                   |
|:----------------------|:-----------------------------|:------------------------------------------------------------------------------------|:------------------------------------------------------------------------|:-----------------------------|:---------------------------------------------|
| Metadata (trace)      | Structured                   | Relasional/tabular, tabel lebar (denormalized) berisi entitas Event, Station, Trace | /datalake/processed/metadata/dataset=*/ (Parquet, Snappy)               | (dataset, trace_name)        | filter, groupBy, pivot, window, join         |
| Waveform              | Unstructured (array float64) | Array / wide-column: 1 baris per trace, kolom array e,n,z                           | /datalake/processed/waveforms/dataset=*/ (Parquet nested array<double>) | (dataset, trace_name)        | join, transform, slice, aggregate, array_max |
| Event–station network | Relasi (turunan)             | Graph: vertices = event & station, edges = trace                                    | diturunkan dari metadata saat dibutuhkan                                | event_id, (network, station) | degree, konektivitas (A2: GraphFrames)       |
| Lineage & quality     | Semi-structured              | Dokumen JSON (key-value)                                                            | /datalake/_lineage/, /datalake/quality/                                 | file                         | baca/append dokumen                          |
