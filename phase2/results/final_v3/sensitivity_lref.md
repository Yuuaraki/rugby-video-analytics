# Sensitivity: per-frame torso length -> per-clip L_ref (PCK@0.20, vis1)

| clip | condition | n | per-frame | L_ref | delta |
|---|---|---|---|---|---|
| P9201256 | yolo | 392 | 0.508 | 0.518 | +0.010 |
| P9201256 | interp | 392 | 0.559 | 0.602 | +0.043 |
| P9201256 | interp_ok | 338 | 0.595 | 0.598 | +0.003 |
| P9201256 | rts | 392 | 0.487 | 0.541 | +0.054 |
| P9201256 | tgct_v1 | 392 | 0.515 | 0.543 | +0.028 |
| P9201256 | hybrik_struct_ok | 338 | 0.598 | 0.577 | -0.021 |
| PA041271 | yolo | 252 | 0.575 | 0.575 | +0.000 |
| PA041271 | interp | 252 | 0.663 | 0.647 | -0.016 |
| PA041271 | interp_ok | 182 | 0.676 | 0.654 | -0.022 |
| PA041271 | rts | 252 | 0.607 | 0.512 | -0.095 |
| PA041271 | tgct_v1 | 252 | 0.643 | 0.627 | -0.016 |
| PA041271 | hybrik_struct_ok | 182 | 0.286 | 0.291 | +0.005 |

## By phase (vis1 only), interp_ok and hybrik_struct_ok

| clip | condition | phase | n | per-frame | L_ref | delta |
|---|---|---|---|---|---|---|
| P9201256 | interp_ok | pre | 6 | 0.833 | 1.000 | +0.167 |
| P9201256 | interp_ok | contact | 56 | 0.196 | 0.411 | +0.214 |
| P9201256 | interp_ok | fusion | 156 | 0.487 | 0.423 | -0.064 |
| P9201256 | interp_ok | fall | 120 | 0.908 | 0.892 | -0.017 |
| P9201256 | hybrik_struct_ok | pre | 6 | 0.833 | 1.000 | +0.167 |
| P9201256 | hybrik_struct_ok | contact | 56 | 0.018 | 0.054 | +0.036 |
| P9201256 | hybrik_struct_ok | fusion | 156 | 0.628 | 0.564 | -0.064 |
| P9201256 | hybrik_struct_ok | fall | 120 | 0.817 | 0.817 | +0.000 |
| PA041271 | interp_ok | pre | 63 | 0.921 | 0.937 | +0.016 |
| PA041271 | interp_ok | contact | 15 | 0.733 | 0.733 | +0.000 |
| PA041271 | interp_ok | hold | 6 | 0.333 | 0.333 | +0.000 |
| PA041271 | interp_ok | post | 98 | 0.531 | 0.480 | -0.051 |
| PA041271 | hybrik_struct_ok | pre | 63 | 0.730 | 0.746 | +0.016 |
| PA041271 | hybrik_struct_ok | contact | 15 | 0.400 | 0.400 | +0.000 |
| PA041271 | hybrik_struct_ok | hold | 6 | 0.000 | 0.000 | +0.000 |
| PA041271 | hybrik_struct_ok | post | 98 | 0.000 | 0.000 | +0.000 |
