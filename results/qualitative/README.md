# Qualitative benchmark artifact

These compact files support the manuscript's first three figures without
requiring the full S3 recording, a model checkpoint, SpikeInterface, or a GPU.
They were exported from the frozen benchmark with inference commit `808d7fa`.
Figures 1–2 compare three endpoint-validated model artifacts; Figure 3 uses the
Full96 omission0 score distributions.

| artifact stem | model | export job | NPZ SHA-256 |
|---|---|---|---|
| `full96_om0_examples` | `ib_w96_om0_s0` | `23244894` | `5be9ca2cbb07a62b626b87ac56495fde490ae2d64a02c1bf92af8d305163e93e` |
| `full96_om1_examples` | `ib_w96_om1_s0` | `23246072` | `433582303a763e273b0f972f67502149f78e3336f8150b580081323ad63b2122` |
| `origdi_s0_examples` | `ib_origdi_s0` | `23246073` | `39af42d4029c44b07a3ed44780d2d6ff021a54604c986face0bb14915ac14393` |

Each stem has an NPZ containing 30-ms all-probe raw/denoised voltage, the 4-ms
unit-1143 close-up, four units' empirical templates, and matched-filter scores;
a CSV with all ten reproduced endpoint rows; and a metadata JSON with recording,
checkpoint, extraction, and exemplar identities. Each exporter recomputed every
committed per-unit SNR and d′ value and aborted unless the maximum absolute
discrepancy was below `1e-6`; all three observed errors were 0. The local renderer
also rejects disagreement in their shared raw/event/template domain. Full hashes
and checkpoint provenance are in
[`data/provenance.md`](../../data/provenance.md).

Auxiliary file SHA-256 values are:

| file | SHA-256 |
|---|---|
| `full96_om0_examples.csv` | `fb75d4663cbd66fb68bfda27d0ac84010f76bdfa75d51e3be6cc9f8d2992102f` |
| `full96_om0_examples_metadata.json` | `f89fc514fdafbc8e3af03a6855596bf9619fb325213a1c13597e31ee97eda1e2` |
| `full96_om1_examples.csv` | `fffdfb7b05e6c7022c48cb321dc48512a5c357f118e7ee28e2f3c0a76df77e56` |
| `full96_om1_examples_metadata.json` | `4ce5427fe9d7c13a4bd06945865f0bb8641cb2ac86b5ede4b21ac025e36ae23d` |
| `origdi_s0_examples.csv` | `628e68404b7861fd15dbd6210a31430ae53ff922f648e35449166fba086a9d50` |
| `origdi_s0_examples_metadata.json` | `eb050a3f9e55e6860b9b1a9e4ed7b4cd247de57480f94cd1238207e4121dcacf` |

Figures 20–22 use a second collection of 10 checkpoint-specific triplets under
[`learning_stages/`](learning_stages/README.md): five scheduled states from each
Full96 omission route. The collection fixes the raw event, display contacts, and
four GT units across every checkpoint. Its manifest records the export jobs,
checkpoint hashes, and SHA-256 values for all 30 files, including the strict
Pascal-node replacement for one rejected A100 replay.

Regenerate the figures locally with:

```bash
python code/figures/qualitative_examples.py
```

Recreating the artifact itself is a GPU/S3 operation documented in
[`code/scoring/README.md`](../../code/scoring/README.md). The probe heatmaps
remove each displayed channel's median only to suppress stationary offsets;
that centering is not part of endpoint scoring.
