# Complementarity (ORACLE upper bound, not a contestant): interp vs hybrik_interp, clip PA041271
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | hybrik_interp | oracle | gain | both | interp-only | hybrik_interp-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.496 | 0.131 | 0.520 | +0.025 | 78 | 285 | 18 | 351 |
| vis0 | 480 | 0.575 | 0.135 | 0.598 | +0.023 | 54 | 222 | 11 | 193 |
| vis1 | 252 | 0.345 | 0.123 | 0.373 | +0.028 | 24 | 63 | 7 | 158 |
| pre | 384 | 0.641 | 0.242 | 0.682 | +0.042 | 77 | 169 | 16 | 122 |
| contact | 36 | 0.361 | 0.083 | 0.417 | +0.056 | 1 | 12 | 2 | 21 |
| hold | 108 | 0.324 | 0.000 | 0.324 | +0.000 | 0 | 35 | 0 | 73 |
| post | 204 | 0.338 | 0.000 | 0.338 | +0.000 | 0 | 69 | 0 | 135 |
| sho | 122 | 0.328 | 0.164 | 0.344 | +0.016 | 18 | 22 | 2 | 80 |
| elb | 122 | 0.484 | 0.262 | 0.516 | +0.033 | 28 | 31 | 4 | 59 |
| wri | 122 | 0.541 | 0.107 | 0.541 | +0.000 | 13 | 53 | 0 | 56 |
| hip | 122 | 0.320 | 0.082 | 0.369 | +0.049 | 4 | 35 | 6 | 77 |
| kne | 122 | 0.705 | 0.131 | 0.754 | +0.049 | 10 | 76 | 6 | 30 |
| ank | 122 | 0.598 | 0.041 | 0.598 | +0.000 | 5 | 68 | 0 | 49 |

## alpha = 0.20
| subset | n | interp | hybrik_interp | oracle | gain | both | interp-only | hybrik_interp-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.821 | 0.268 | 0.843 | +0.022 | 180 | 421 | 16 | 115 |
| vis0 | 480 | 0.912 | 0.298 | 0.935 | +0.023 | 132 | 306 | 11 | 31 |
| vis1 | 252 | 0.647 | 0.210 | 0.667 | +0.020 | 48 | 115 | 5 | 84 |
| pre | 384 | 0.966 | 0.474 | 0.995 | +0.029 | 171 | 200 | 11 | 2 |
| contact | 36 | 0.833 | 0.306 | 0.889 | +0.056 | 9 | 21 | 2 | 4 |
| hold | 108 | 0.556 | 0.028 | 0.583 | +0.028 | 0 | 60 | 3 | 45 |
| post | 204 | 0.686 | 0.000 | 0.686 | +0.000 | 0 | 140 | 0 | 64 |
| sho | 122 | 0.713 | 0.311 | 0.762 | +0.049 | 32 | 55 | 6 | 29 |
| elb | 122 | 0.680 | 0.328 | 0.713 | +0.033 | 36 | 47 | 4 | 35 |
| wri | 122 | 0.705 | 0.262 | 0.713 | +0.008 | 31 | 55 | 1 | 35 |
| hip | 122 | 0.943 | 0.262 | 0.975 | +0.033 | 28 | 87 | 4 | 3 |
| kne | 122 | 0.943 | 0.279 | 0.943 | +0.000 | 34 | 81 | 0 | 7 |
| ank | 122 | 0.943 | 0.164 | 0.951 | +0.008 | 19 | 96 | 1 | 6 |

