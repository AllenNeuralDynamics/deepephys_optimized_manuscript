# Five-minute Kilosort4 threshold calibration

This directory records a post-hoc `Th_learned` sensitivity on the first 300 s
of the exact 681532 ProbeC `recording1_3` hybrid case after Full96 omission1
denoising.

## Provenance

- Inference computation: `b1745055-ce00-4cb9-8344-44087a0dd3e6`
- Inference result asset: `0eed5c9d-02c8-4709-b322-15c8ea400aef`
- Kilosort calibration computation: `93d1865b-a451-45df-90b2-dbcf554544cb`
- Owned Kilosort capsule: `eb0a6d2f-2418-4a0a-9765-beaa973745db`
- Calibration capsule commit: `d3b57d2`
- Exact hybrid asset: `8046af5a-6e53-420e-9e28-52bd54514342`
- Duration: 300 s at 30 kHz
- Injected events in clip: 44,896 (4,443--4,584 per GT unit)

The denoised recording was preprocessed once with the production high-pass,
bad-channel-removal, and global median-reference chain. Kilosort4 then ran
sequentially with `Th_learned=8,9,10`; all other sorter settings were frozen.

## Results

| `Th_learned` | mean accuracy | precision | recall | GT detected | GT >0.8 | sorter units | events/s | FP spikes in GT-matched clusters |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.4044 | 0.4125 | 0.6528 | 7/10 | 2/10 | 511 | 7,660.6 | 32,340 |
| 9 | 0.4615 | 0.4934 | 0.6202 | 7/10 | 2/10 | 478 | 5,217.2 | 19,357 |
| 10 | **0.5002** | **0.5403** | 0.5996 | 7/10 | 2/10 | 457 | 4,028.4 | **8,559** |

Relative to threshold 8, threshold 10 increased mean accuracy by 0.0958 and
precision by 0.1277 while reducing recall by 0.0532. Total sorter events fell
47.4%, and false-positive spikes in GT-matched clusters fell 73.5%. Four of the
seven detected GT units improved in accuracy, one worsened, and two remained at
ceiling. Units 94, 720, and 1129 remained undetected at every threshold.

A descriptive paired unit bootstrap gave a threshold-10 minus threshold-8 mean
accuracy interval of `[+0.0160, +0.1992]`. Threshold 10 was not clearly separated
from threshold 9 (`[-0.0299, +0.1396]`), so both should advance to a longer
confirmation if compute permits.

## Chunk-boundary check

The inherited 300-Hz filter uses a 5-ms chunk margin, below SpikeInterface's
16.67-ms recommendation. Detected event phases were nevertheless essentially
uniform around one-second chunk boundaries: enrichment within 16.67 ms was only
1.010--1.014 times the uniform expectation across thresholds. The threshold
result is therefore not explained by boundary-locked detections in this clip.

This is a calibration on the same benchmark case, not independent validation.
Short recordings also alter template learning, clustering, and drift behavior.
Confirm thresholds 9 and 10 on a longer clip before changing the full pipeline.
