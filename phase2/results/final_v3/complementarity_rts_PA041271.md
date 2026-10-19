# Complementarity (ORACLE upper bound, not a contestant): interp vs rts, clip PA041271
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | rts | oracle | gain | both | interp-only | rts-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.496 | 0.264 | 0.560 | +0.064 | 146 | 217 | 47 | 322 |
| vis0 | 480 | 0.575 | 0.285 | 0.635 | +0.060 | 108 | 168 | 29 | 175 |
| vis1 | 252 | 0.345 | 0.222 | 0.417 | +0.071 | 38 | 49 | 18 | 147 |
| pre | 384 | 0.641 | 0.315 | 0.711 | +0.070 | 94 | 152 | 27 | 111 |
| contact | 36 | 0.361 | 0.167 | 0.361 | +0.000 | 6 | 7 | 0 | 23 |
| hold | 108 | 0.324 | 0.148 | 0.343 | +0.019 | 14 | 21 | 2 | 71 |
| post | 204 | 0.338 | 0.245 | 0.426 | +0.088 | 32 | 37 | 18 | 117 |
| sho | 122 | 0.328 | 0.254 | 0.377 | +0.049 | 25 | 15 | 6 | 76 |
| elb | 122 | 0.484 | 0.320 | 0.541 | +0.057 | 32 | 27 | 7 | 56 |
| wri | 122 | 0.541 | 0.156 | 0.590 | +0.049 | 13 | 53 | 6 | 50 |
| hip | 122 | 0.320 | 0.221 | 0.418 | +0.098 | 15 | 24 | 12 | 71 |
| kne | 122 | 0.705 | 0.320 | 0.746 | +0.041 | 34 | 52 | 5 | 31 |
| ank | 122 | 0.598 | 0.311 | 0.689 | +0.090 | 27 | 46 | 11 | 38 |

## alpha = 0.20
| subset | n | interp | rts | oracle | gain | both | interp-only | rts-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.821 | 0.697 | 0.855 | +0.034 | 485 | 116 | 25 | 106 |
| vis0 | 480 | 0.912 | 0.794 | 0.944 | +0.031 | 366 | 72 | 15 | 27 |
| vis1 | 252 | 0.647 | 0.512 | 0.687 | +0.040 | 119 | 44 | 10 | 79 |
| pre | 384 | 0.966 | 0.818 | 0.982 | +0.016 | 308 | 63 | 6 | 7 |
| contact | 36 | 0.833 | 0.611 | 0.889 | +0.056 | 20 | 10 | 2 | 4 |
| hold | 108 | 0.556 | 0.389 | 0.602 | +0.046 | 37 | 23 | 5 | 43 |
| post | 204 | 0.686 | 0.647 | 0.745 | +0.059 | 120 | 20 | 12 | 52 |
| sho | 122 | 0.713 | 0.762 | 0.820 | +0.057 | 80 | 7 | 13 | 22 |
| elb | 122 | 0.680 | 0.590 | 0.697 | +0.016 | 70 | 13 | 2 | 37 |
| wri | 122 | 0.705 | 0.484 | 0.705 | +0.000 | 59 | 27 | 0 | 36 |
| hip | 122 | 0.943 | 0.787 | 0.975 | +0.033 | 92 | 23 | 4 | 3 |
| kne | 122 | 0.943 | 0.820 | 0.951 | +0.008 | 99 | 16 | 1 | 6 |
| ank | 122 | 0.943 | 0.738 | 0.984 | +0.041 | 85 | 30 | 5 | 2 |

