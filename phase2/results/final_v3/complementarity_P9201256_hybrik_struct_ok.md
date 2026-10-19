# Complementarity (ORACLE upper bound, not a contestant): interp vs hybrik_struct_ok, clip P9201256
oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);
All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).
Rates may differ from standalone PCK when scoring denominators differ.
This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.

## alpha = 0.10
| subset | n | interp | hybrik_struct_ok | oracle | gain | both | interp-only | hybrik_struct_ok-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 969 | 0.369 | 0.173 | 0.444 | +0.074 | 96 | 262 | 72 | 539 |
| vis0 | 631 | 0.404 | 0.139 | 0.468 | +0.063 | 48 | 207 | 40 | 336 |
| vis1 | 338 | 0.305 | 0.237 | 0.399 | +0.095 | 48 | 55 | 32 | 203 |
| pre | 36 | 0.694 | 0.611 | 0.750 | +0.056 | 20 | 5 | 2 | 9 |
| contact | 168 | 0.363 | 0.024 | 0.369 | +0.006 | 3 | 58 | 1 | 106 |
| fusion | 405 | 0.195 | 0.160 | 0.321 | +0.126 | 14 | 65 | 51 | 275 |
| fall | 360 | 0.536 | 0.214 | 0.586 | +0.050 | 59 | 134 | 18 | 149 |
| sho | 159 | 0.314 | 0.075 | 0.340 | +0.025 | 8 | 42 | 4 | 105 |
| elb | 170 | 0.553 | 0.247 | 0.612 | +0.059 | 32 | 62 | 10 | 66 |
| wri | 130 | 0.538 | 0.162 | 0.577 | +0.038 | 16 | 54 | 5 | 55 |
| hip | 170 | 0.135 | 0.135 | 0.235 | +0.100 | 6 | 17 | 17 | 130 |
| kne | 170 | 0.347 | 0.282 | 0.518 | +0.171 | 19 | 40 | 29 | 82 |
| ank | 170 | 0.365 | 0.129 | 0.406 | +0.041 | 15 | 47 | 7 | 101 |

## alpha = 0.20
| subset | n | interp | hybrik_struct_ok | oracle | gain | both | interp-only | hybrik_struct_ok-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 969 | 0.669 | 0.557 | 0.795 | +0.126 | 418 | 230 | 122 | 199 |
| vis0 | 631 | 0.707 | 0.547 | 0.818 | +0.111 | 275 | 171 | 70 | 115 |
| vis1 | 338 | 0.598 | 0.577 | 0.751 | +0.154 | 143 | 59 | 52 | 84 |
| pre | 36 | 0.972 | 1.000 | 1.000 | +0.000 | 35 | 0 | 1 | 0 |
| contact | 168 | 0.583 | 0.119 | 0.625 | +0.042 | 13 | 85 | 7 | 63 |
| fusion | 405 | 0.457 | 0.563 | 0.716 | +0.153 | 123 | 62 | 105 | 115 |
| fall | 360 | 0.917 | 0.711 | 0.942 | +0.025 | 247 | 83 | 9 | 21 |
| sho | 159 | 0.748 | 0.566 | 0.862 | +0.113 | 72 | 47 | 18 | 22 |
| elb | 170 | 0.694 | 0.582 | 0.806 | +0.112 | 80 | 38 | 19 | 33 |
| wri | 130 | 0.654 | 0.577 | 0.762 | +0.108 | 61 | 24 | 14 | 31 |
| hip | 170 | 0.559 | 0.565 | 0.771 | +0.206 | 60 | 35 | 36 | 39 |
| kne | 170 | 0.694 | 0.659 | 0.829 | +0.135 | 89 | 29 | 23 | 29 |
| ank | 170 | 0.665 | 0.400 | 0.735 | +0.071 | 56 | 57 | 12 | 45 |

