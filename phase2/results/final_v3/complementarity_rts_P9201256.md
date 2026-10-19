# Complementarity (ORACLE upper bound, not a contestant): interp vs rts, clip P9201256
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | rts | oracle | gain | both | interp-only | rts-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.368 | 0.252 | 0.426 | +0.058 | 219 | 195 | 65 | 646 |
| vis0 | 733 | 0.407 | 0.266 | 0.468 | +0.061 | 150 | 148 | 45 | 390 |
| vis1 | 392 | 0.296 | 0.227 | 0.347 | +0.051 | 69 | 47 | 20 | 256 |
| pre | 36 | 0.694 | 0.278 | 0.750 | +0.056 | 8 | 17 | 2 | 9 |
| contact | 324 | 0.361 | 0.133 | 0.395 | +0.034 | 32 | 85 | 11 | 196 |
| fusion | 405 | 0.195 | 0.121 | 0.247 | +0.052 | 28 | 51 | 21 | 305 |
| fall | 360 | 0.536 | 0.506 | 0.622 | +0.086 | 151 | 42 | 31 | 136 |
| sho | 185 | 0.297 | 0.254 | 0.368 | +0.070 | 34 | 21 | 13 | 117 |
| elb | 196 | 0.536 | 0.316 | 0.556 | +0.020 | 58 | 47 | 4 | 87 |
| wri | 156 | 0.519 | 0.372 | 0.551 | +0.032 | 53 | 28 | 5 | 70 |
| hip | 196 | 0.133 | 0.071 | 0.163 | +0.031 | 8 | 18 | 6 | 164 |
| kne | 196 | 0.378 | 0.276 | 0.449 | +0.071 | 40 | 34 | 14 | 108 |
| ank | 196 | 0.372 | 0.250 | 0.490 | +0.117 | 26 | 47 | 23 | 100 |

## alpha = 0.20
| subset | n | interp | rts | oracle | gain | both | interp-only | rts-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.670 | 0.586 | 0.732 | +0.062 | 589 | 165 | 70 | 301 |
| vis0 | 733 | 0.707 | 0.610 | 0.757 | +0.050 | 410 | 108 | 37 | 178 |
| vis1 | 392 | 0.602 | 0.541 | 0.686 | +0.084 | 179 | 57 | 33 | 123 |
| pre | 36 | 0.972 | 0.639 | 0.972 | +0.000 | 23 | 12 | 0 | 1 |
| contact | 324 | 0.630 | 0.503 | 0.722 | +0.093 | 133 | 71 | 30 | 90 |
| fusion | 405 | 0.457 | 0.338 | 0.511 | +0.054 | 115 | 70 | 22 | 198 |
| fall | 360 | 0.917 | 0.933 | 0.967 | +0.033 | 318 | 12 | 18 | 12 |
| sho | 185 | 0.735 | 0.616 | 0.822 | +0.086 | 98 | 38 | 16 | 33 |
| elb | 196 | 0.689 | 0.602 | 0.745 | +0.056 | 107 | 28 | 11 | 50 |
| wri | 156 | 0.647 | 0.551 | 0.673 | +0.026 | 82 | 19 | 4 | 51 |
| hip | 196 | 0.582 | 0.510 | 0.622 | +0.041 | 92 | 22 | 8 | 74 |
| kne | 196 | 0.714 | 0.648 | 0.776 | +0.061 | 115 | 25 | 12 | 44 |
| ank | 196 | 0.653 | 0.582 | 0.750 | +0.097 | 95 | 33 | 19 | 49 |

