# Full96 Kilosort4 benchmark tables

These compact tables audit the completed fixed-configuration Kilosort4 runs on
the exact ProbeC `recording1_3` hybrid case:

| route | successful computation | checkpoint SHA-256 |
|---|---|---|
| omission0 | `db76c533-9f39-46e6-98fe-e83adf56ea51` | `f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506` |
| omission1 | `2ad21011-a937-44dc-a370-5280049621ef` | `90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a` |

`code/benchmarking/audit_ks4_results.py` downloads the small evaluator CSVs,
reads only the headers of the 0.6–0.9-GB SpikeInterface `spikes.npy` arrays to
obtain exact event counts, and downloads the 25-MB GT spike vector for per-unit
event accounting. It aborts unless both computations succeeded and their raw
per-unit accuracy, precision, recall, unit count, runtime, and total spike-event
count agree exactly.

The generated files are:

| file | contents | SHA-256 |
|---|---|---|
| `kilosort4_all_runs.csv` | all 15 runs with all-10 metrics plus fixed-seven metrics and TP/FN/FP counts | `b437298695e150abdd5df014f6792ab8b5206a160468eb7d80ea0e5241dae52a` |
| `kilosort4_all_runs.md` | compact comparison with fixed-seven accuracy, precision, recall, TP, FN, and FP | `f876f5e804db275da3c62ab5ec07bbea5d31d8fa9d2febefd369aae5f391d28f` |
| `kilosort4_full_per_unit_by_snr.csv` | 7 reference GT units x 9 full-recording sorter conditions ordered by raw template SNR | `14ab308ce934f5f884958ecebaa59e83914a000fe666641ffe933e5fa17dd70d` |
| `kilosort4_full_per_unit_by_snr.md` | readable per-unit accuracy, precision, recall, TP/FN/FP, and exact-checkpoint SNR comparison | `dde12569ad18a1df5c409871ce8f9049fcd2ad69fd6cd8544a7a397b34721f5d` |
| `kilosort4_raw_vs_10p75_by_snr.csv` | seven-unit paired raw versus omission1 9/10.75 SNR and precision changes | `f28a74f087b9b09f82c7b8631d0734bc194bdc8dc3494b25da74731a1213bb0d` |
| `kilosort4_raw_vs_10p75_by_snr.md` | focused readable merge of the SNR ranking and precision comparison | `ed1794f43ba95c28c82efa2af789d321091ea409d38f1650f7ec4c8f8f3ef8a3` |
| `kilosort4_summary.csv` | full aggregate performance, unit/event counts, event rates, runtimes, and matched-cluster accounting | `65e716973382b13c860e32d1b6e6d6466f00ba188d7e41b82724eb9f98675b6c` |
| `kilosort4_summary.md` | manuscript aggregate table | `a6e739c571848f6b2e4fb2151a86775ce7b36a6975dcef119acc88eba703d01b` |
| `kilosort4_event_accounting.md` | compact matched-cluster event accounting | `2b34d3ed84ee8383bc4925333a58dc771bfc76e94fa60c8c957337f6b046d978` |
| `kilosort4_per_unit.csv` | 10 GT units × raw/omission0/omission1 performance and integer event accounting | `2107b03f3a4874ffd08800db9451a8000d4334a95c970cafbbef386204406def` |

`ks4_event_lineage/` contains the fixed-template event-lineage diagnosis and
accepted-score analysis at `Th_learned=8` and `10.75`. The reproducible figures
are `figures/kilosort4_fp_by_peel.{png,pdf}` and
`figures/kilosort4_score_margin_by_peel.{png,pdf}`.

Regenerate with authenticated Code Ocean access:

```bash
set -a; source ~/.codeocean.env; set +a
python code/benchmarking/audit_ks4_results.py
```

Regenerate the combined table from the local audited outputs without network
access:

```bash
python code/benchmarking/build_ks4_all_runs_table.py
python code/benchmarking/build_ks4_per_unit_snr_table.py
```

The combined table includes the raw comparator, full omission0 and omission1
runs, every full threshold follow-up, and both clip-calibration sweeps. Compare
metrics within the labeled scope because recording duration changes Kilosort
template learning, clustering, and drift behavior. Its fixed-seven accuracy,
precision, recall, TP, FN, and FP columns use GT units 337, 664, 793, 1122,
1143, 1300, and 2143, the set matched by raw 9/8 and every denoised full run.
When raw 10.75 loses four of those units, their zeros and full FN counts remain
in the comparison. Units 94, 720, and 1129 are excluded. The all-10 macro
metrics remain alongside the fixed-seven values.

The per-unit SNR table is ordered by descending raw template SNR so every sorter
condition retains the same unit order. It also reports each route's input-domain
template SNR from the exact scheduled-step checkpoint used for Kilosort. This
SNR is a pre-sort GT-template detectability metric, not Kilosort's post-sort
quality-metric SNR, and therefore should be treated as an explanatory covariate
rather than a sorter output.

The focused raw-versus-10.75 table pairs the seven SNR-ranked units one-to-one
and reports raw and omission1 template SNR beside raw 9/8 and omission1 9/10.75
precision. It is generated with the full 63-row per-unit table by the same
command.

## Interpretation boundary

All-sorter event counts include injected units, unlabeled native spikes, and any
noise detections, so extra events cannot be labeled false positives globally.
For the seven GT units with a matched cluster, integer accounting is recovered
from the exact GT count $N_u$ and evaluator metrics:

$$
TP_u = \operatorname{round}(N_u\,\mathrm{recall}_u), \qquad
S_u = \operatorname{round}(TP_u / \mathrm{precision}_u).
$$

By the evaluator definition, $FP_u=S_u-TP_u$ is the number of **false-positive
spikes** in the cluster matched to injected unit $u$. This is a GT-relative label:
native spikes can legitimately enter a cluster matched to an injected unit and
are still counted as false positives relative to that injected spike train.

Both denoised inputs produce about 55.4% more total sorter events than raw. This
is not explained by cluster count alone: events per sorter unit rise from 36,857
raw to 55,777 omission0 and 53,102 omission1. Among matched clusters, recovered
injected spikes rise by about 24%, while false-positive spikes rise from
119,881 to 366,462/360,588. Together with longer sorter runtimes, these results
are consistent with the unchanged Kilosort configuration being less selective
on denoised voltage. They do not establish why; threshold calibration, native
spike assignment, splitting/merging, and residual structure remain possible
contributors.

## Threshold calibration

`ks4_threshold_sweep/` contains the five-minute Full96 omission1
`Th_learned=8,9,10` calibration, including aggregate and per-unit metrics plus a
one-second chunk-boundary check. Threshold 10 was the best short-clip candidate:
mean accuracy increased from 0.4044 to 0.5002 and GT-matched-cluster false
positives fell 73.5% relative to threshold 8, while detected-unit counts were
unchanged.

`ks4_threshold_confirmation/` contains the completed 20-minute confirmation.
Thresholds 9 and 10 remained tied in mean accuracy (0.5187 versus 0.5204), but
threshold 10 reduced total events by 25.5% and GT-matched-cluster false-positive
spikes by 39.9% relative to 9. Threshold 9 retained 8/10 GT units and 0.6830
recall; threshold 10 retained 7/10 and 0.6329 recall. Threshold 10 is selected
as the precision-first sensitivity; threshold 9 is selected for the next
benchmark to prioritize unit retention.

`ks4_full_threshold9/` contains the completed full-recording comparison against
the frozen threshold-8 omission1 result. Threshold 9 increased mean accuracy
from 0.4503 to 0.4715 and precision from 0.4808 to 0.5303, while recall fell from
0.6124 to 0.5823. It preserved 7/10 detected and 2/10 well-detected GT units,
reduced total sorter events by 22.9%, and reduced false-positive spikes in
GT-matched clusters by 36.4%. Threshold 9 was retained as the provisional
unit-retention setting before the full threshold matrix completed.

`ks4_full_threshold_matrix/` contains the completed raw, omission1 threshold,
and matched omission0 9/10.75 matrix. Raising `Th_universal` alone was nearly neutral.
Raising `Th_learned` to 10.75 brought precision to 0.5783, only 0.0068 below
raw, and brought matched-cluster false-positive spikes within 321 (0.27%) of
raw while retaining 0.0062 higher accuracy and 0.0138 higher recall. Thus
9/10.75 is the closest tested raw-selectivity match, whereas 9/10 remains the
higher-recall and higher-accuracy operating point. Both are within-case
calibration results requiring held-out validation.

Matched-threshold Full96 omission0 computation
`a2ccfc54-5109-44ef-9968-b3c1435fcffc` completed successfully in 17,981 s.
At 9/10.75, omission0 has accuracy 0.4548, precision 0.5779, recall 0.5099,
673 sorter units, 546,055 TP, and 121,759 FP across the common seven units.
Relative to omission1 9/10.75, those differences are +0.0015 accuracy, -0.0005
precision, +0.0022 recall, +2,361 TP, and +1,557 FP. The two denoisers are
therefore effectively tied at the matched operating point on this case.

Raw AP matched-threshold control computation
`fab61c02-f1d5-4d26-965b-2cdb47aad29b` completed successfully in 14,618 s with
`Th_universal=9`, `Th_learned=10.75`. Saved provenance differs from raw 9/8 only
at `Th_learned` and exactly matches the denoised sorter dictionary. Raw 10.75
detects only units 793, 1143, and 2143: 3/10 versus 7/10 for raw 9/8 and both
denoised 10.75 runs. Across the fixed seven reference units it has 274,830 TP,
474,726 FN, and 3,565 FP. The low FP count therefore reflects severe unit loss,
not a better overall tradeoff. Both denoisers retain all seven units at the same
threshold, showing that denoising shifts the useful Kilosort operating range.

## Fixed-template event lineage

Code Ocean computation `d0efc11d-4141-443b-b381-98c9dbeecd6a` learned templates,
whitening, drift, and channel selection once from the first 1,200 seconds of
Full96 omission1 denoised voltage, then traced every accepted raw and denoised
event through detection, clustering, merging, and duplicate removal at learned
thresholds 8 and 10.75. The final manifest write failed after all scientific
artifacts were saved; commit `d200d09` fixes that serialization-only defect.

At threshold 10.75, final matched-cluster FPs occur later and closer to the
acceptance boundary than TPs. Raw TP events have event-weighted mean score margin
`score - Th_learned` 12.03 at median peel 6, versus FP margin 2.29 at median peel
22. Denoised TP events have margin 10.95 at median peel 6, versus FP margin 2.99
at median peel 13. Denoised threshold 8 shows the same separation: TP margin
12.31 at median peel 7, versus FP margin 2.85 at median peel 25. Cluster merging
changes no matched TP/FN/FP totals, and deduplication removes only 16–54
matched-cluster FPs depending on the condition.

This is a controlled denoised-template experiment, not the production raw
baseline. Under the denoised-derived transform, raw threshold 8 matches only two
GT units, has zero evaluator-defined FP in those two clusters, and places
21,112,308 events in unmatched clusters. The production raw 9/8 run instead
learns raw-native templates and matches 7/10 GT units.

## Native default 9/8 baseline lineage

`ks4_native_baseline/` pairs the completed raw-native computation
`adaf8bcd-453d-472c-a98e-bf00158b6b67` with the denoised-native threshold-8
lineage above. Each domain learns its own preprocessing, whitening, drift, and
templates on the same first 1,200 seconds. Raw-native matches 7/10 GT units with
97,677 TP, 81,689 FN, and 31,012 matched-cluster FP. Denoised-native matches 8/10
with 125,183 TP, 54,183 FN, and 80,624 FP. Thus denoising adds 27,506 recovered
injected spikes and one GT match while adding 49,612 matched-cluster FP.

In both baselines, FP events occur later and closer to threshold than TP events.
Raw-native TP/FP median peels are 7/13 and their event-weighted score margins are
6.89/2.20. Denoised-native values are 7/25 and 12.31/2.85. The comparison is
rendered in `figures/kilosort4_native_baseline_by_peel.{png,pdf}`.