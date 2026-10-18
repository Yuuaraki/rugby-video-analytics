# Complementarity (ORACLE upper bound, not a contestant): interp vs hybrik_interp, clip P9201256
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | hybrik_interp | oracle | gain | both | interp-only | hybrik_interp-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.340 | 0.170 | 0.420 | +0.079 | 102 | 281 | 89 | 653 |
| vis0 | 733 | 0.374 | 0.135 | 0.438 | +0.064 | 52 | 222 | 47 | 412 |
| vis1 | 392 | 0.278 | 0.235 | 0.385 | +0.107 | 50 | 59 | 42 | 241 |
| pre | 36 | 0.611 | 0.444 | 0.722 | +0.111 | 12 | 10 | 4 | 10 |
| contact | 324 | 0.198 | 0.015 | 0.201 | +0.003 | 4 | 60 | 1 | 259 |
| fusion | 405 | 0.249 | 0.220 | 0.407 | +0.158 | 25 | 76 | 64 | 240 |
| fall | 360 | 0.544 | 0.225 | 0.600 | +0.056 | 61 | 135 | 20 | 144 |
| sho | 185 | 0.292 | 0.081 | 0.324 | +0.032 | 9 | 45 | 6 | 125 |
| elb | 196 | 0.510 | 0.224 | 0.577 | +0.066 | 31 | 69 | 13 | 83 |
| wri | 156 | 0.462 | 0.135 | 0.513 | +0.051 | 13 | 59 | 8 | 76 |
| hip | 196 | 0.122 | 0.158 | 0.235 | +0.077 | 9 | 15 | 22 | 150 |
| kne | 196 | 0.342 | 0.276 | 0.490 | +0.148 | 25 | 42 | 29 | 100 |
| ank | 196 | 0.337 | 0.133 | 0.393 | +0.056 | 15 | 51 | 11 | 119 |

## alpha = 0.20
| subset | n | interp | hybrik_interp | oracle | gain | both | interp-only | hybrik_interp-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.634 | 0.516 | 0.745 | +0.111 | 455 | 258 | 125 | 287 |
| vis0 | 733 | 0.674 | 0.516 | 0.783 | +0.109 | 298 | 196 | 80 | 159 |
| vis1 | 392 | 0.559 | 0.515 | 0.673 | +0.115 | 157 | 62 | 45 | 128 |
| pre | 36 | 0.833 | 0.917 | 0.917 | +0.000 | 30 | 0 | 3 | 3 |
| contact | 324 | 0.426 | 0.059 | 0.441 | +0.015 | 14 | 124 | 5 | 181 |
| fusion | 405 | 0.516 | 0.667 | 0.788 | +0.121 | 160 | 49 | 110 | 86 |
| fall | 360 | 0.933 | 0.717 | 0.953 | +0.019 | 251 | 85 | 7 | 17 |
| sho | 185 | 0.692 | 0.530 | 0.778 | +0.086 | 82 | 46 | 16 | 41 |
| elb | 196 | 0.673 | 0.556 | 0.791 | +0.117 | 86 | 46 | 23 | 41 |
| wri | 156 | 0.609 | 0.462 | 0.712 | +0.103 | 56 | 39 | 16 | 45 |
| hip | 196 | 0.515 | 0.526 | 0.709 | +0.184 | 65 | 36 | 38 | 57 |
| kne | 196 | 0.663 | 0.612 | 0.776 | +0.112 | 98 | 32 | 22 | 44 |
| ank | 196 | 0.648 | 0.398 | 0.699 | +0.051 | 68 | 59 | 10 | 59 |

