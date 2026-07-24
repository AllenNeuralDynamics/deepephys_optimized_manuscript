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
| `kilosort4_summary.csv` | full aggregate performance, unit/event counts, event rates, runtimes, and matched-cluster accounting | `040cd3192deaa1e8be6c87b45cf9919b9175e24277a3ec68b5e951147050ebca` |
| `kilosort4_summary.md` | manuscript aggregate table | `a6e739c571848f6b2e4fb2151a86775ce7b36a6975dcef119acc88eba703d01b` |
| `kilosort4_event_accounting.md` | compact matched-cluster event accounting | `1496ce40ba46a35e6492141a0c4caf3c0142699edac939f75d2e0a9245c30c67` |
| `kilosort4_per_unit.csv` | 10 GT units × raw/omission0/omission1 performance and integer event accounting | `236d0ec9eec92fdbfe1c15c72a9a6156302d6189bd813d14e603eead4b4cf8b7` |

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

`S_u - TP_u` is called evaluator-unmatched rather than noise because native
spikes can legitimately enter a cluster matched to an injected unit.

Both denoised inputs produce about 55.4% more total sorter events than raw. This
is not explained by cluster count alone: events per sorter unit rise from 36,857
raw to 55,777 omission0 and 53,102 omission1. Among matched clusters, recovered
injected spikes rise by about 24%, while evaluator-unmatched events rise from
119,881 to 366,462/360,588. Together with longer sorter runtimes, these results
are consistent with the unchanged Kilosort configuration being less selective
on denoised voltage. They do not establish why; threshold calibration, native
spike assignment, splitting/merging, and residual structure remain possible
contributors.