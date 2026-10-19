# Complementarity (ORACLE upper bound, not a contestant): interp vs tgct_v1, clip PA041271
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | tgct_v1 | oracle | gain | both | interp-only | tgct_v1-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.496 | 0.470 | 0.508 | +0.012 | 335 | 28 | 9 | 360 |
| vis0 | 480 | 0.575 | 0.544 | 0.588 | +0.013 | 255 | 21 | 6 | 198 |
| vis1 | 252 | 0.345 | 0.329 | 0.357 | +0.012 | 80 | 7 | 3 | 162 |
| pre | 384 | 0.641 | 0.633 | 0.654 | +0.013 | 238 | 8 | 5 | 133 |
| contact | 36 | 0.361 | 0.361 | 0.361 | +0.000 | 13 | 0 | 0 | 23 |
| hold | 108 | 0.324 | 0.176 | 0.333 | +0.009 | 18 | 17 | 1 | 72 |
| post | 204 | 0.338 | 0.338 | 0.353 | +0.015 | 66 | 3 | 3 | 132 |
| sho | 122 | 0.328 | 0.328 | 0.336 | +0.008 | 39 | 1 | 1 | 81 |
| elb | 122 | 0.484 | 0.492 | 0.492 | +0.000 | 59 | 0 | 1 | 62 |
| wri | 122 | 0.541 | 0.541 | 0.549 | +0.008 | 65 | 1 | 1 | 55 |
| hip | 122 | 0.320 | 0.320 | 0.352 | +0.033 | 35 | 4 | 4 | 79 |
| kne | 122 | 0.705 | 0.615 | 0.713 | +0.008 | 74 | 12 | 1 | 35 |
| ank | 122 | 0.598 | 0.525 | 0.607 | +0.008 | 63 | 10 | 1 | 48 |

## alpha = 0.20
| subset | n | interp | tgct_v1 | oracle | gain | both | interp-only | tgct_v1-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.821 | 0.809 | 0.836 | +0.015 | 581 | 20 | 11 | 120 |
| vis0 | 480 | 0.912 | 0.904 | 0.923 | +0.010 | 429 | 9 | 5 | 37 |
| vis1 | 252 | 0.647 | 0.627 | 0.671 | +0.024 | 152 | 11 | 6 | 83 |
| pre | 384 | 0.966 | 0.969 | 0.974 | +0.005 | 369 | 2 | 3 | 10 |
| contact | 36 | 0.833 | 0.833 | 0.833 | +0.000 | 30 | 0 | 0 | 6 |
| hold | 108 | 0.556 | 0.481 | 0.630 | +0.074 | 44 | 16 | 8 | 40 |
| post | 204 | 0.686 | 0.676 | 0.686 | +0.000 | 138 | 2 | 0 | 64 |
| sho | 122 | 0.713 | 0.762 | 0.779 | +0.016 | 85 | 2 | 8 | 27 |
| elb | 122 | 0.680 | 0.689 | 0.689 | +0.000 | 83 | 0 | 1 | 38 |
| wri | 122 | 0.705 | 0.713 | 0.713 | +0.000 | 86 | 0 | 1 | 35 |
| hip | 122 | 0.943 | 0.861 | 0.943 | +0.000 | 105 | 10 | 0 | 7 |
| kne | 122 | 0.943 | 0.893 | 0.943 | +0.000 | 109 | 6 | 0 | 7 |
| ank | 122 | 0.943 | 0.934 | 0.951 | +0.008 | 113 | 2 | 1 | 6 |

