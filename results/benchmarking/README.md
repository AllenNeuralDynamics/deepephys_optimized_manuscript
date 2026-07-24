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
| `kilosort4_summary.csv` | full aggregate performance, unit/event counts, event rates, runtimes, and matched-cluster accounting | `65e716973382b13c860e32d1b6e6d6466f00ba188d7e41b82724eb9f98675b6c` |
| `kilosort4_summary.md` | manuscript aggregate table | `a6e739c571848f6b2e4fb2151a86775ce7b36a6975dcef119acc88eba703d01b` |
| `kilosort4_event_accounting.md` | compact matched-cluster event accounting | `2b34d3ed84ee8383bc4925333a58dc771bfc76e94fa60c8c957337f6b046d978` |
| `kilosort4_per_unit.csv` | 10 GT units × raw/omission0/omission1 performance and integer event accounting | `2107b03f3a4874ffd08800db9451a8000d4334a95c970cafbbef386204406def` |

Regenerate with authenticated Code Ocean access:

```bash
set -a; source ~/.codeocean.env; set +a
python code/benchmarking/audit_ks4_results.py
```

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
unchanged. A 20-minute confirmation is running because thresholds 9 and 10 were
not conclusively separated across units on the short clip.