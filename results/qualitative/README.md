# Qualitative benchmark artifact

These compact files support the manuscript's first three figures without
requiring the full S3 recording, a model checkpoint, SpikeInterface, or a GPU.
They were exported from the frozen benchmark with `ib_w96_om0_s0` and inference
commit `808d7fa` by AIND HPC job `23244894`.

| file | contents |
|---|---|
| `full96_om0_examples.npz` | 30-ms all-probe raw/denoised voltage, the 4-ms unit-1143 event close-up, four units' empirical templates, and their hit/background matched-filter scores |
| `full96_om0_examples.csv` | all ten reproduced endpoint rows, including raw/denoised SNR, d′, and AUC |
| `full96_om0_examples_metadata.json` | recording/sorting URLs, model and checkpoint identity, inference commit, extraction counts, selected units, and exemplar event |

The exporter recomputed every committed per-unit SNR and d′ value and aborted
unless the maximum absolute discrepancy was below `1e-6`; the observed error was
0. The NPZ SHA-256 is
`5be9ca2cbb07a62b626b87ac56495fde490ae2d64a02c1bf92af8d305163e93e`.
Full hashes and checkpoint provenance are in
[`data/provenance.md`](../../data/provenance.md).

Regenerate the figures locally with:

```bash
python code/figures/qualitative_examples.py
```

Recreating the artifact itself is a GPU/S3 operation documented in
[`code/scoring/README.md`](../../code/scoring/README.md). The probe heatmaps
remove each displayed channel's median only to suppress stationary offsets;
that centering is not part of endpoint scoring.
