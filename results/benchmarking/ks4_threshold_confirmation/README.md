# Twenty-minute Kilosort4 threshold confirmation

This directory records the `Th_learned=8,9,10` confirmation on the first
1,200 s of the exact 681532 ProbeC `recording1_3` hybrid case after Full96
omission1 denoising. It supersedes the five-minute screen for threshold
selection, although the intervals are nested rather than independent.

## Provenance

- Inference computation: `6add9fa7-e1ff-435d-b9d9-52a3e360901f`
- Inference result asset: `e7134769-b8c9-437a-ba0d-f5bd9ee0078b`
- Kilosort confirmation computation: `c474cfbf-d8ff-4548-93b6-7df282523473`
- Owned Kilosort capsule: `eb0a6d2f-2418-4a0a-9765-beaa973745db`
- Calibration capsule commit: `0a6ffac`
- Exact hybrid asset: `8046af5a-6e53-420e-9e28-52bd54514342`
- Duration: 1,200 s at 30 kHz
- Injected events in clip: 179,366 (17,720--18,122 per GT unit)

The denoised recording was preprocessed once with the frozen production
high-pass, bad-channel-removal, and global median-reference chain. Kilosort4
then ran sequentially at all three thresholds with every other setting fixed.
The computation succeeded in 8,433 s; the sweep itself took 7,761.9 s.

## Results

| `Th_learned` | mean accuracy | precision | recall | GT detected | GT >0.8 | sorter units | events/s | FP spikes in GT-matched clusters |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.4628 | 0.5004 | **0.7106** | 8/10 | 2/10 | 620 | 8,370.7 | 116,908 |
| 9 | 0.5187 | **0.5574** | 0.6830 | **8/10** | 2/10 | 624 | 5,848.1 | 63,732 |
| 10 | **0.5204** | 0.5547 | 0.6329 | 7/10 | **3/10** | 600 | **4,357.4** | **38,307** |

Relative to threshold 8, threshold 10 increased mean accuracy by 0.0576 and
precision by 0.0543 while reducing recall by 0.0777. Total sorter events fell
47.9%, and false-positive spikes in GT-matched clusters fell 67.2%.

Thresholds 9 and 10 remained effectively tied in mean accuracy: threshold 10
was higher by only 0.0016. A descriptive paired unit bootstrap gave a
threshold-10 minus threshold-9 mean accuracy interval of
`[-0.0549, +0.0393]`. Threshold 10 reduced total events by another 25.5% and
GT-matched-cluster false-positive spikes by 39.9%, but recall fell by 0.0500.
It also removed the weak match for unit 720, which had accuracy 0.2291,
precision 0.4091, and recall 0.3423 at threshold 9. The other five non-ceiling
matched units improved in accuracy at threshold 10.

## Decision

Use `Th_learned=9` for the next Full96 omission1 benchmark. It recovered 8/10
GT units instead of 7/10 at threshold 10, had nearly identical mean accuracy,
and preserved 0.0500 more recall. This is the conservative unit-retention choice
given that the paired unit analysis did not distinguish thresholds 9 and 10.

Retain threshold 10 as the precision-first sensitivity. It provided the
strongest suppression of excess sorter events and GT-relative false positives,
and was numerically best on the prespecified primary metric in both clips. This
is not evidence that threshold 9 is statistically superior to threshold 10;
the selection prioritizes retention of weak units over maximum event
suppression.

All-sorter events include native activity and cannot be labeled global false
positives. The false-positive counts above apply only to clusters matched to
injected GT units and can still include legitimate native spikes.