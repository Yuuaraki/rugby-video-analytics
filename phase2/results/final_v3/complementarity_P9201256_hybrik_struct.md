# Complementarity (ORACLE upper bound, not a contestant): interp vs hybrik_struct, clip P9201256
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | hybrik_struct | oracle | gain | both | interp-only | hybrik_struct-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.368 | 0.152 | 0.435 | +0.067 | 96 | 318 | 75 | 636 |
| vis0 | 733 | 0.407 | 0.124 | 0.465 | +0.059 | 48 | 250 | 43 | 392 |
| vis1 | 392 | 0.296 | 0.204 | 0.378 | +0.082 | 48 | 68 | 32 | 244 |
| pre | 36 | 0.694 | 0.611 | 0.750 | +0.056 | 20 | 5 | 2 | 9 |
| contact | 324 | 0.361 | 0.022 | 0.373 | +0.012 | 3 | 114 | 4 | 203 |
| fusion | 405 | 0.195 | 0.160 | 0.321 | +0.126 | 14 | 65 | 51 | 275 |
| fall | 360 | 0.536 | 0.214 | 0.586 | +0.050 | 59 | 134 | 18 | 149 |
| sho | 185 | 0.297 | 0.065 | 0.319 | +0.022 | 8 | 47 | 4 | 126 |
| elb | 196 | 0.536 | 0.219 | 0.592 | +0.056 | 32 | 73 | 11 | 80 |
| wri | 156 | 0.519 | 0.141 | 0.558 | +0.038 | 16 | 65 | 6 | 69 |
| hip | 196 | 0.133 | 0.117 | 0.219 | +0.087 | 6 | 20 | 17 | 153 |
| kne | 196 | 0.378 | 0.250 | 0.531 | +0.153 | 19 | 55 | 30 | 92 |
| ank | 196 | 0.372 | 0.112 | 0.408 | +0.036 | 15 | 58 | 7 | 116 |

## alpha = 0.20
| subset | n | interp | hybrik_struct | oracle | gain | both | interp-only | hybrik_struct-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.670 | 0.492 | 0.781 | +0.111 | 428 | 326 | 125 | 246 |
| vis0 | 733 | 0.707 | 0.487 | 0.806 | +0.100 | 284 | 234 | 73 | 142 |
| vis1 | 392 | 0.602 | 0.500 | 0.735 | +0.133 | 144 | 92 | 52 | 104 |
| pre | 36 | 0.972 | 1.000 | 1.000 | +0.000 | 35 | 0 | 1 | 0 |
| contact | 324 | 0.630 | 0.102 | 0.660 | +0.031 | 23 | 181 | 10 | 110 |
| fusion | 405 | 0.457 | 0.563 | 0.716 | +0.153 | 123 | 62 | 105 | 115 |
| fall | 360 | 0.917 | 0.711 | 0.942 | +0.025 | 247 | 83 | 9 | 21 |
| sho | 185 | 0.735 | 0.486 | 0.832 | +0.097 | 72 | 64 | 18 | 31 |
| elb | 196 | 0.689 | 0.531 | 0.786 | +0.097 | 85 | 50 | 19 | 42 |
| wri | 156 | 0.647 | 0.487 | 0.744 | +0.096 | 61 | 40 | 15 | 40 |
| hip | 196 | 0.582 | 0.490 | 0.765 | +0.184 | 60 | 54 | 36 | 46 |
| kne | 196 | 0.714 | 0.597 | 0.842 | +0.128 | 92 | 48 | 25 | 31 |
| ank | 196 | 0.653 | 0.357 | 0.714 | +0.061 | 58 | 70 | 12 | 56 |

