# Template-support sensitivity

This post hoc diagnostic tests whether the frozen matched-filter d-prime deficit
is caused by using too much temporal or spatial template support. It evaluates
Full96 omission0, Full96 omission1, and seed-0 original DeepInterpolation on the
same frozen hybrid recording, GT events, and spike-excluded background centers.

## Design

- Temporal crops: 0.5, 1, 2, 3, and 4 ms centered on the GT frame.
- Spatial supports: top 1, 2, 4, 8, 16, or 24 channels ranked by the raw
  training template, plus the frozen 50%-amplitude endpoint rule.
- In-sample estimate: the endpoint's template/hit reuse.
- Cross-fitted estimate: deterministic two-fold event split; channel ranking and
  raw/denoised templates use 50 training events and scores use the other 50.
- The same 200 background windows enter raw, denoised, and both folds.
- Fold results are averaged within unit before the ten units are averaged.
- No support is selected as an optimum. The figure shows full prespecified
  one-axis curves; `template_support_prespecified_results.csv` retains six named
  cells, absolute raw/deep d-prime, all-unit gaps, unit counts, and weak/other
  subgroup gaps.

The 4-ms in-sample endpoint cells reproduce the committed endpoint d-prime
values within `1e-6` and reproduce each unit's selected channel count. The
fold-specific endpoint rule is less stable with 50 training events (8.8 mean
channels versus 5.4 with all 100), so the principal temporal comparison fixes
support at top 2 channels and the principal spatial comparison fixes duration at
1 ms.

## Key result

At cross-fitted top-2 support, shortening 4 ms to 1 ms changes the mean
denoised-minus-raw d-prime gap:

| model | 4 ms gap | 1 ms gap | raw d-prime at 1 ms | deep d-prime at 1 ms |
|---|---:|---:|---:|---:|
| Full96 omission0 | -0.0429 | +0.0163 | 4.5426 | 4.5589 |
| Full96 omission1 | -0.0362 | +0.0903 | 4.5426 | 4.6330 |
| original DI seed 0 | -0.3223 | -0.1702 | 4.5426 | 4.3724 |

The Full96 aggregate reversal is driven by stronger units. At 1 ms/top-2, only
3/10 units improve in either Full96 model. The four post hoc weak-unit gaps are
-0.1674 (omission0) and -0.2907 (omission1), versus +0.1388 and +0.3444 for the
other six. Original DI remains negative overall at every tested support, and its
weak-unit gap is -0.5866 at 1 ms/top-2.

Thus oversized support explains why the **all-unit Full96 mean** need not be
below raw. It does not explain away weak-unit losses and does not account for the
original-DI deficit. This linear-filter sensitivity is not a Kilosort benchmark.

## Provenance and files

| model | HPC job | elapsed | node GPU |
|---|---:|---:|---|
| `ib_w96_om0_s0` | `23258586` | 00:08:46 | TITAN Xp |
| `ib_w96_om1_s0` | `23258587` | 00:08:41 | TITAN Xp |
| `ib_origdi_s0` | `23258588` | 00:08:40 | TITAN X (Pascal) |

For each model:

- `*_detail.csv`: 1,050 rows (in-sample plus both cross-fit folds).
- `*_per_unit.csv`: 700 rows after fold averaging.
- `*_summary.csv`: 70 model/evaluation/support means.

SHA-256:

| file | SHA-256 |
|---|---|
| `ib_w96_om0_s0_detail.csv` | `f31625ca4b744b1cfdb6f1bb4f1b8e7f4c18afea5ce464ab9f21a5fd8b53ff1a` |
| `ib_w96_om0_s0_per_unit.csv` | `e59f7cb8c8015b6ce31cb720de35f87f562935fcc9e5f30a2b281e32f3f272be` |
| `ib_w96_om0_s0_summary.csv` | `770c448f0391a40a1eefd07c3288f874153dd1882dc34282c0c71af78e794c47` |
| `ib_w96_om1_s0_detail.csv` | `985afbae3f78a0f2c3e8f15433ae440d8ab964af7e8f062c8681ef0ebd8a64af` |
| `ib_w96_om1_s0_per_unit.csv` | `6af938d7d8aebaaf28130ded62f3c6e5e9a051cffc5cb6062335bb10775866f6` |
| `ib_w96_om1_s0_summary.csv` | `a4abadacc47e49705e0ee34d2f7fed1f600bf6fb55448dbeb41a5aa171eab030` |
| `ib_origdi_s0_detail.csv` | `ebd69215128989f6734243ab1ba1c5db3f26b3a2d123d6c780c04bead22ab337` |
| `ib_origdi_s0_per_unit.csv` | `3dc12f632d066966fbb45229fc3491a6a6a0a93eb524c461b8199a010fb19e4d` |
| `ib_origdi_s0_summary.csv` | `a9ca05be61e0555487abdde59b29dbcbae85fd9e605e6cc4a5c306a11c573ead` |
| `template_support_prespecified_results.csv` | `baf3ceda0baa353b64188ec7e61ca01595ab7ae57ec4c3427dae57094108588d` |

Implementation and focused tests are in
[`code/scoring/template_support_sweep.py`](../../code/scoring/template_support_sweep.py)
and [`code/tests/test_template_support_sweep.py`](../../code/tests/test_template_support_sweep.py).
Regenerate the figure with:

```bash
python code/figures/template_support_sweep.py
```
