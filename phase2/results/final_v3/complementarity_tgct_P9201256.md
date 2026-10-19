# Complementarity (ORACLE upper bound, not a contestant): interp vs tgct_v1, clip P9201256
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | tgct_v1 | oracle | gain | both | interp-only | tgct_v1-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.368 | 0.325 | 0.385 | +0.017 | 347 | 67 | 19 | 692 |
| vis0 | 733 | 0.407 | 0.357 | 0.426 | +0.019 | 248 | 50 | 14 | 421 |
| vis1 | 392 | 0.296 | 0.265 | 0.309 | +0.013 | 99 | 17 | 5 | 271 |
| pre | 36 | 0.694 | 0.722 | 0.722 | +0.000 | 25 | 0 | 1 | 10 |
| contact | 324 | 0.361 | 0.265 | 0.373 | +0.012 | 82 | 35 | 4 | 203 |
| fusion | 405 | 0.195 | 0.173 | 0.222 | +0.027 | 59 | 20 | 11 | 315 |
| fall | 360 | 0.536 | 0.511 | 0.544 | +0.008 | 181 | 12 | 3 | 164 |
| sho | 185 | 0.297 | 0.265 | 0.324 | +0.027 | 44 | 11 | 5 | 125 |
| elb | 196 | 0.536 | 0.485 | 0.546 | +0.010 | 93 | 12 | 2 | 89 |
| wri | 156 | 0.519 | 0.481 | 0.538 | +0.019 | 72 | 9 | 3 | 72 |
| hip | 196 | 0.133 | 0.117 | 0.133 | +0.000 | 23 | 3 | 0 | 170 |
| kne | 196 | 0.378 | 0.301 | 0.383 | +0.005 | 58 | 16 | 1 | 121 |
| ank | 196 | 0.372 | 0.332 | 0.413 | +0.041 | 57 | 16 | 8 | 115 |

## alpha = 0.20
| subset | n | interp | tgct_v1 | oracle | gain | both | interp-only | tgct_v1-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.670 | 0.615 | 0.683 | +0.012 | 678 | 76 | 14 | 357 |
| vis0 | 733 | 0.707 | 0.653 | 0.720 | +0.014 | 469 | 49 | 10 | 205 |
| vis1 | 392 | 0.602 | 0.543 | 0.612 | +0.010 | 209 | 27 | 4 | 152 |
| pre | 36 | 0.972 | 0.972 | 0.972 | +0.000 | 35 | 0 | 0 | 1 |
| contact | 324 | 0.630 | 0.481 | 0.636 | +0.006 | 154 | 50 | 2 | 118 |
| fusion | 405 | 0.457 | 0.422 | 0.481 | +0.025 | 161 | 24 | 10 | 210 |
| fall | 360 | 0.917 | 0.917 | 0.922 | +0.006 | 328 | 2 | 2 | 28 |
| sho | 185 | 0.735 | 0.686 | 0.751 | +0.016 | 124 | 12 | 3 | 46 |
| elb | 196 | 0.689 | 0.622 | 0.704 | +0.015 | 119 | 16 | 3 | 58 |
| wri | 156 | 0.647 | 0.603 | 0.654 | +0.006 | 93 | 8 | 1 | 54 |
| hip | 196 | 0.582 | 0.526 | 0.587 | +0.005 | 102 | 12 | 1 | 81 |
| kne | 196 | 0.714 | 0.633 | 0.719 | +0.005 | 123 | 17 | 1 | 55 |
| ank | 196 | 0.653 | 0.622 | 0.679 | +0.026 | 117 | 11 | 5 | 63 |

