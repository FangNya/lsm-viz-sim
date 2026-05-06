# Final Validation Experiment Summary

## Global Correctness

- Total runs: 24
- Total validation `get` checks: 2310
- Total mismatches: 0
- Result: all runs reached `validation_accuracy = 1.0`.

## Recommended Result Groups

| Workload | Profile | STC Read Amp | LCS Read Amp | STC Write Amp | LCS Write Amp | STC Compactions | LCS Compactions | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| final_overlap_waves | final_dense_compaction | 3.729 | 2.562 | 19.352 | 26.809 | 26 | 18 | Overlap-heavy workload: LCS now shows the intended lower read amplification, while still paying higher write amplification. |
| final_hotspot_overwrite | final_dense_compaction | 3.550 | 3.013 | 20.391 | 33.971 | 22 | 16 | Duplicate-heavy hotspot workload: STC still has lower write amplification in the current simplified implementation, while LCS keeps a modest read advantage. |
| final_mixed_read_validation | final_overlap_sensitive | 3.855 | 2.645 | 20.822 | 71.218 | 18 | 30 | Mixed workload under aggressive overlap pressure: LCS keeps lower read amplification but write amplification remains much higher. |
| final_sequential_ingest | final_balanced | 3.070 | 2.298 | 28.082 | 21.481 | 10 | 8 | After enabling range pruning and binary candidate lookup, LCS now shows lower read amplification and lower write amplification than STC on sequential ingest. |
