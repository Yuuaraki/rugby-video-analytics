# Complementarity (ORACLE upper bound, not a contestant): interp vs hybrik_struct, clip PA041271
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | hybrik_struct | oracle | gain | both | interp-only | hybrik_struct-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.519 | 0.123 | 0.544 | +0.025 | 72 | 308 | 18 | 334 |
| vis0 | 480 | 0.590 | 0.125 | 0.613 | +0.023 | 49 | 234 | 11 | 186 |
| vis1 | 252 | 0.385 | 0.119 | 0.413 | +0.028 | 23 | 74 | 7 | 148 |
| pre | 384 | 0.609 | 0.227 | 0.651 | +0.042 | 71 | 163 | 16 | 134 |
| contact | 36 | 0.361 | 0.083 | 0.417 | +0.056 | 1 | 12 | 2 | 21 |
| hold | 108 | 0.370 | 0.000 | 0.370 | +0.000 | 0 | 40 | 0 | 68 |
| post | 204 | 0.456 | 0.000 | 0.456 | +0.000 | 0 | 93 | 0 | 111 |
| sho | 122 | 0.361 | 0.164 | 0.385 | +0.025 | 17 | 27 | 3 | 75 |
| elb | 122 | 0.492 | 0.254 | 0.525 | +0.033 | 27 | 33 | 4 | 58 |
| wri | 122 | 0.549 | 0.090 | 0.549 | +0.000 | 11 | 56 | 0 | 55 |
| hip | 122 | 0.377 | 0.066 | 0.426 | +0.049 | 2 | 44 | 6 | 70 |
| kne | 122 | 0.730 | 0.123 | 0.770 | +0.041 | 10 | 79 | 5 | 28 |
| ank | 122 | 0.607 | 0.041 | 0.607 | +0.000 | 5 | 69 | 0 | 48 |

## alpha = 0.20
| subset | n | interp | hybrik_struct | oracle | gain | both | interp-only | hybrik_struct-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.833 | 0.262 | 0.858 | +0.025 | 174 | 436 | 18 | 104 |
| vis0 | 480 | 0.923 | 0.292 | 0.952 | +0.029 | 126 | 317 | 14 | 23 |
| vis1 | 252 | 0.663 | 0.206 | 0.679 | +0.016 | 48 | 119 | 4 | 81 |
| pre | 384 | 0.943 | 0.461 | 0.974 | +0.031 | 165 | 197 | 12 | 10 |
| contact | 36 | 0.833 | 0.306 | 0.889 | +0.056 | 9 | 21 | 2 | 4 |
| hold | 108 | 0.611 | 0.037 | 0.648 | +0.037 | 0 | 66 | 4 | 38 |
| post | 204 | 0.745 | 0.000 | 0.745 | +0.000 | 0 | 152 | 0 | 52 |
| sho | 122 | 0.795 | 0.303 | 0.844 | +0.049 | 31 | 66 | 6 | 19 |
| elb | 122 | 0.656 | 0.336 | 0.697 | +0.041 | 36 | 44 | 5 | 37 |
| wri | 122 | 0.721 | 0.254 | 0.730 | +0.008 | 30 | 58 | 1 | 33 |
| hip | 122 | 0.951 | 0.254 | 0.992 | +0.041 | 26 | 90 | 5 | 1 |
| kne | 122 | 0.943 | 0.270 | 0.943 | +0.000 | 33 | 82 | 0 | 7 |
| ank | 122 | 0.934 | 0.156 | 0.943 | +0.008 | 18 | 96 | 1 | 7 |

