# Complementarity (ORACLE upper bound, not a contestant): interp vs hybrik_struct_ok, clip PA041271
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | hybrik_struct_ok | oracle | gain | both | interp-only | hybrik_struct_ok-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 528 | 0.498 | 0.182 | 0.532 | +0.034 | 78 | 185 | 18 | 247 |
| vis0 | 346 | 0.564 | 0.188 | 0.595 | +0.032 | 54 | 141 | 11 | 140 |
| vis1 | 182 | 0.374 | 0.170 | 0.412 | +0.038 | 24 | 44 | 7 | 107 |
| pre | 276 | 0.649 | 0.337 | 0.707 | +0.058 | 77 | 102 | 16 | 81 |
| contact | 36 | 0.361 | 0.083 | 0.417 | +0.056 | 1 | 12 | 2 | 21 |
| hold | 12 | 0.167 | 0.000 | 0.167 | +0.000 | 0 | 2 | 0 | 10 |
| post | 204 | 0.338 | 0.000 | 0.338 | +0.000 | 0 | 69 | 0 | 135 |
| sho | 88 | 0.318 | 0.227 | 0.341 | +0.023 | 18 | 10 | 2 | 58 |
| elb | 88 | 0.568 | 0.364 | 0.614 | +0.045 | 28 | 22 | 4 | 34 |
| wri | 88 | 0.580 | 0.148 | 0.580 | +0.000 | 13 | 38 | 0 | 37 |
| hip | 88 | 0.341 | 0.114 | 0.409 | +0.068 | 4 | 26 | 6 | 52 |
| kne | 88 | 0.659 | 0.182 | 0.727 | +0.068 | 10 | 48 | 6 | 24 |
| ank | 88 | 0.523 | 0.057 | 0.523 | +0.000 | 5 | 41 | 0 | 42 |

## alpha = 0.20
| subset | n | interp | hybrik_struct_ok | oracle | gain | both | interp-only | hybrik_struct_ok-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 528 | 0.831 | 0.367 | 0.858 | +0.027 | 180 | 259 | 14 | 75 |
| vis0 | 346 | 0.925 | 0.408 | 0.951 | +0.026 | 132 | 188 | 9 | 17 |
| vis1 | 182 | 0.654 | 0.291 | 0.681 | +0.027 | 48 | 71 | 5 | 58 |
| pre | 276 | 0.953 | 0.659 | 0.993 | +0.040 | 171 | 92 | 11 | 2 |
| contact | 36 | 0.833 | 0.306 | 0.889 | +0.056 | 9 | 21 | 2 | 4 |
| hold | 12 | 0.500 | 0.083 | 0.583 | +0.083 | 0 | 6 | 1 | 5 |
| post | 204 | 0.686 | 0.000 | 0.686 | +0.000 | 0 | 140 | 0 | 64 |
| sho | 88 | 0.727 | 0.432 | 0.795 | +0.068 | 32 | 32 | 6 | 18 |
| elb | 88 | 0.727 | 0.432 | 0.750 | +0.023 | 36 | 28 | 2 | 22 |
| wri | 88 | 0.761 | 0.364 | 0.773 | +0.011 | 31 | 36 | 1 | 20 |
| hip | 88 | 0.932 | 0.364 | 0.977 | +0.045 | 28 | 54 | 4 | 2 |
| kne | 88 | 0.920 | 0.386 | 0.920 | +0.000 | 34 | 47 | 0 | 7 |
| ank | 88 | 0.920 | 0.227 | 0.932 | +0.011 | 19 | 62 | 1 | 6 |

