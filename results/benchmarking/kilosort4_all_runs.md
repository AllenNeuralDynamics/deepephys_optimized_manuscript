# All raw and denoised Kilosort4 runs

All rows use the exact 681532 ProbeC `recording1_3` hybrid case. Compare performance within a scope: the 5-minute and 20-minute intervals are nested calibration clips, and recording duration changes Kilosort template learning, clustering, and drift behavior. The fixed-7 metrics and TP/FN/FP columns are restricted to GT units 337, 664, 793, 1122, 1143, 1300, and 2143, the units matched by raw 9/8 and all denoised full-recording conditions. A stricter condition that loses one of these units retains its zero metrics and full FN count; units 94, 720, and 1129 are excluded.

| scope | input | Th universal | Th learned | accuracy (all 10) | precision (all 10) | recall (all 10) | accuracy (fixed 7) | precision (fixed 7) | recall (fixed 7) | GT detected | GT >0.8 | sorter units | events/s | TP spikes in fixed 7 GT units | FN spikes in fixed 7 GT units | FP spikes in fixed 7 GT-matched clusters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full recording | raw AP | 9 | 8 | 0.4471 | 0.5851 | 0.4939 | 0.6387 | 0.8359 | 0.7056 | 7/10 | 2/10 | 672 | 3,467 | 528,844 | 220,712 | 119,881 |
| full recording | raw AP | 9 | 10.75 | 0.2549 | 0.2945 | 0.2567 | 0.3641 | 0.4207 | 0.3668 | 3/10 | 2/10 | 634 | 2,084 | 274,830 | 474,726 | 3,565 |
| full recording | Full96 omission0 | 9 | 8 | 0.4489 | 0.4782 | 0.6136 | 0.6412 | 0.6831 | 0.8766 | 7/10 | 2/10 | 690 | 5,387 | 657,056 | 92,500 | 366,462 |
| full recording | Full96 omission0 | 9 | 10.75 | 0.4548 | 0.5779 | 0.5099 | 0.6497 | 0.8255 | 0.7285 | 7/10 | 2/10 | 673 | 2,988 | 546,055 | 203,501 | 121,759 |
| full recording | Full96 omission1 | 9 | 8 | 0.4503 | 0.4808 | 0.6124 | 0.6432 | 0.6869 | 0.8749 | 7/10 | 2/10 | 725 | 5,389 | 655,819 | 93,737 | 360,588 |
| full recording | Full96 omission1 | 9 | 10 | 0.4688 | 0.5626 | 0.5430 | 0.6697 | 0.8037 | 0.7757 | 7/10 | 2/10 | 689 | 3,393 | 581,454 | 168,102 | 156,203 |
| full recording | Full96 omission1 | 9 | 9 | 0.4715 | 0.5303 | 0.5823 | 0.6735 | 0.7576 | 0.8318 | 7/10 | 2/10 | 706 | 4,155 | 623,520 | 126,036 | 229,311 |
| full recording | Full96 omission1 | 9 | 10.75 | 0.4533 | 0.5783 | 0.5077 | 0.6476 | 0.8262 | 0.7253 | 7/10 | 2/10 | 682 | 2,988 | 543,694 | 205,862 | 120,202 |
| full recording | Full96 omission1 | 10 | 9 | 0.4720 | 0.5364 | 0.5799 | 0.6743 | 0.7663 | 0.8284 | 7/10 | 2/10 | 718 | 4,186 | 620,953 | 128,603 | 224,003 |
| 20 min clip | Full96 omission1 | 9 | 8 | 0.4628 | 0.5004 | 0.7106 | 0.6056 | 0.6159 | 0.9481 | 8/10 | 2/10 | 620 | 8,371 | 119,215 | 6,510 | 113,209 |
| 20 min clip | Full96 omission1 | 9 | 9 | 0.5187 | 0.5574 | 0.6830 | 0.7083 | 0.7379 | 0.9268 | 8/10 | 2/10 | 624 | 5,848 | 116,546 | 9,179 | 54,971 |
| 20 min clip | Full96 omission1 | 9 | 10 | 0.5204 | 0.5547 | 0.6329 | 0.7434 | 0.7924 | 0.9042 | 7/10 | 3/10 | 600 | 4,357 | 113,719 | 12,006 | 38,307 |
| 5 min clip | Full96 omission1 | 9 | 8 | 0.4044 | 0.4125 | 0.6528 | 0.5777 | 0.5893 | 0.9326 | 7/10 | 2/10 | 511 | 7,661 | 29,364 | 2,111 | 32,340 |
| 5 min clip | Full96 omission1 | 9 | 9 | 0.4615 | 0.4934 | 0.6202 | 0.6592 | 0.7049 | 0.8860 | 7/10 | 2/10 | 478 | 5,217 | 27,906 | 3,569 | 19,357 |
| 5 min clip | Full96 omission1 | 9 | 10 | 0.5002 | 0.5403 | 0.5996 | 0.7146 | 0.7718 | 0.8566 | 7/10 | 2/10 | 457 | 4,028 | 26,980 | 4,495 | 8,559 |
