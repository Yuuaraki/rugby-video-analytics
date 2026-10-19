# Complementarity (ORACLE upper bound, not a contestant): interp vs hybrik_interp, clip P9201256
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | hybrik_interp | oracle | gain | both | interp-only | hybrik_interp-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.368 | 0.153 | 0.432 | +0.064 | 100 | 314 | 72 | 639 |
| vis0 | 733 | 0.407 | 0.126 | 0.461 | +0.055 | 52 | 246 | 40 | 395 |
| vis1 | 392 | 0.296 | 0.204 | 0.378 | +0.082 | 48 | 68 | 32 | 244 |
| pre | 36 | 0.694 | 0.611 | 0.750 | +0.056 | 20 | 5 | 2 | 9 |
| contact | 324 | 0.361 | 0.025 | 0.364 | +0.003 | 7 | 110 | 1 | 206 |
| fusion | 405 | 0.195 | 0.160 | 0.321 | +0.126 | 14 | 65 | 51 | 275 |
| fall | 360 | 0.536 | 0.214 | 0.586 | +0.050 | 59 | 134 | 18 | 149 |
| sho | 185 | 0.297 | 0.065 | 0.319 | +0.022 | 8 | 47 | 4 | 126 |
| elb | 196 | 0.536 | 0.214 | 0.587 | +0.051 | 32 | 73 | 10 | 81 |
| wri | 156 | 0.519 | 0.135 | 0.551 | +0.032 | 16 | 65 | 5 | 70 |
| hip | 196 | 0.133 | 0.117 | 0.219 | +0.087 | 6 | 20 | 17 | 153 |
| kne | 196 | 0.378 | 0.260 | 0.526 | +0.148 | 22 | 52 | 29 | 93 |
| ank | 196 | 0.372 | 0.117 | 0.408 | +0.036 | 16 | 57 | 7 | 116 |

## alpha = 0.20
| subset | n | interp | hybrik_interp | oracle | gain | both | interp-only | hybrik_interp-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.670 | 0.495 | 0.781 | +0.111 | 432 | 322 | 125 | 246 |
| vis0 | 733 | 0.707 | 0.490 | 0.805 | +0.098 | 287 | 231 | 72 | 143 |
| vis1 | 392 | 0.602 | 0.505 | 0.737 | +0.135 | 145 | 91 | 53 | 103 |
| pre | 36 | 0.972 | 1.000 | 1.000 | +0.000 | 35 | 0 | 1 | 0 |
| contact | 324 | 0.630 | 0.114 | 0.660 | +0.031 | 27 | 177 | 10 | 110 |
| fusion | 405 | 0.457 | 0.563 | 0.716 | +0.153 | 123 | 62 | 105 | 115 |
| fall | 360 | 0.917 | 0.711 | 0.942 | +0.025 | 247 | 83 | 9 | 21 |
| sho | 185 | 0.735 | 0.492 | 0.838 | +0.103 | 72 | 64 | 19 | 30 |
| elb | 196 | 0.689 | 0.526 | 0.786 | +0.097 | 84 | 51 | 19 | 42 |
| wri | 156 | 0.647 | 0.494 | 0.737 | +0.090 | 63 | 38 | 14 | 41 |
| hip | 196 | 0.582 | 0.495 | 0.765 | +0.184 | 61 | 53 | 36 | 46 |
| kne | 196 | 0.714 | 0.607 | 0.842 | +0.128 | 94 | 46 | 25 | 31 |
| ank | 196 | 0.653 | 0.357 | 0.714 | +0.061 | 58 | 70 | 12 | 56 |

