# Final Validation Experiment Summary

## Global Correctness

- Total runs: 24
- Total validation `get` checks: 2310
- Total mismatches: 0
- Result: all runs reached `validation_accuracy = 1.0`.

## Global Comparison After LCS Lookup Optimization And Versioned MemTable

- In `12 / 12` workload-profile pairs, LCS read amplification is lower than STC.
- In `10 / 12` pairs, LCS write amplification is higher than STC.
- In `2 / 12` pairs, LCS write amplification is lower than STC.
- In `6 / 12` pairs, LCS compaction count is lower than STC.

The experiment set has been rerun after the MemTable semantic refactor:

- duplicate user keys are now kept as multiple versions in MemTable;
- flush keeps duplicate versions and writes them into SSTables;
- old versions are cleaned later during compaction instead of being overwritten inside MemTable.

The two pairs where LCS keeps both lower read amplification and lower write amplification are:

1. `final_sequential_ingest + final_balanced`
2. `final_sequential_ingest + final_dense_compaction`

This is a property of the current teaching-oriented LCS trigger and pushdown model. It should be interpreted as a simulator result under the current simplified semantics, not as a universal claim about industrial LCS.

## Recommended Result Groups

| Workload | Profile | STC Read Amp | LCS Read Amp | STC Write Amp | LCS Write Amp | STC Compactions | LCS Compactions | Interpretation |
|---|---|---:|---:|---:|---:|---:|---:|---|
| final_overlap_waves | final_dense_compaction | 3.729 | 2.562 | 19.352 | 22.742 | 26 | 19 | Overlap-heavy workload: LCS shows the expected lower read amplification while paying extra rewrite cost. |
| final_hotspot_overwrite | final_dense_compaction | 3.550 | 3.013 | 20.391 | 24.394 | 22 | 18 | Duplicate-heavy hotspot workload: LCS preserves a modest read advantage, but repeated overlap handling pushes write amplification above STC. |
| final_mixed_read_validation | final_overlap_sensitive | 3.855 | 2.645 | 20.822 | 39.328 | 18 | 43 | Mixed workload under aggressive overlap pressure: LCS sharply improves reads but may trigger many more high-level compactions. |
| final_sequential_ingest | final_balanced | 3.070 | 2.298 | 28.082 | 23.207 | 10 | 10 | After range pruning and binary candidate lookup, LCS now has a stable read advantage and, in this sequential scene, lower write amplification as well. |
