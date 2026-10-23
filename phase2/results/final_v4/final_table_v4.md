# Final table v4 - condition A (as run), 2026-10-23

Scoring: phase2/pck.py with the per-clip reference torso length L_ref (median shoulder-mid-hip-mid distance over GT frames with all four torso joints vis!=2: P9201256 441 px, PA041271 266 px). GT frames only; every GT joint-frame with vis<2 is in the denominator (P9201256 1125, PA041271 732) for all five rows; (0,0) misses count as wrong. No bias correction, no person_ok gate. Main metric PCK@0.20, secondary @0.10.

Condition A (as run): the detector's tackler assignment is the pipeline's automatic output (yolo_raw_<clip>_tackler_assign.npz from phase2/scripts/labels_to_sheets.py, IoU tracking; no identity fix applied). interp and rts are rebuilt from that sheet by phase2/scripts/make_temporal_sheets.py (sigma_m 0.00051, sigma_a 1e-5, observed = conf >= 0.5 and not a no-detection frame; the yolo row itself scores the detector coordinates as returned, low-confidence joints included); tgct by phase2.tgct.infer with the v1_best checkpoint (inference only, no retraining); hybrik = hybrik_struct, the same sheet as in v3 (demo person selection as run).

Rows: yolo = YOLO-Pose (detector only); interp = Linear interpolation; rts = Kalman-RTS (constant velocity); tgct = T-GCT; hybrik = HybrIK (anatomical prior).

Conditions B (identity-corrected input) and C (on-tackler frames) stay in results/final_v3/final_table_v3.md. The A-vs-B tables at the end are a plumbing check (v6 section 1.3) and the material for the identity-loss discussion, not a results table.

## Main table (condition A) - P9201256
self-PCK ceiling (5-frame re-annotation, L_ref 441 px): vis0 0.89@0.10 / 0.92@0.20, vis1 0.70 / 1.00

| condition | n all | n vis0 | n vis1 | all@0.20 | vis0@0.20 | vis1@0.20 | all@0.10 | vis0@0.10 | vis1@0.10 |
|---|---|---|---|---|---|---|---|---|---|
| yolo | 1125 | 733 | 392 | 0.601 | 0.643 | 0.523 | 0.330 | 0.360 | 0.273 |
| interp | 1125 | 733 | 392 | 0.636 | 0.666 | 0.582 | 0.346 | 0.375 | 0.291 |
| rts | 1125 | 733 | 392 | 0.556 | 0.577 | 0.518 | 0.244 | 0.256 | 0.222 |
| tgct | 1125 | 733 | 392 | 0.612 | 0.648 | 0.543 | 0.320 | 0.344 | 0.276 |
| hybrik | 1125 | 733 | 392 | 0.492 | 0.487 | 0.500 | 0.152 | 0.124 | 0.204 |

## Main table (condition A) - PA041271
self-PCK ceiling (L_ref 266 px): vis0 0.92@0.10 / 1.00@0.20, vis1 0.81 / 1.00

| condition | n all | n vis0 | n vis1 | all@0.20 | vis0@0.20 | vis1@0.20 | all@0.10 | vis0@0.10 | vis1@0.10 |
|---|---|---|---|---|---|---|---|---|---|
| yolo | 732 | 480 | 252 | 0.747 | 0.838 | 0.575 | 0.449 | 0.523 | 0.310 |
| interp | 732 | 480 | 252 | 0.825 | 0.917 | 0.651 | 0.489 | 0.571 | 0.333 |
| rts | 732 | 480 | 252 | 0.709 | 0.806 | 0.524 | 0.269 | 0.292 | 0.226 |
| tgct | 732 | 480 | 252 | 0.809 | 0.904 | 0.627 | 0.470 | 0.544 | 0.329 |
| hybrik | 732 | 480 | 252 | 0.266 | 0.296 | 0.210 | 0.131 | 0.135 | 0.123 |

# Appendix

## A1 by phase (condition A) - P9201256

| condition | n pre | n contact | n fusion | n fall | pre@0.20 | contact@0.20 | fusion@0.20 | fall@0.20 | pre@0.10 | contact@0.10 | fusion@0.10 | fall@0.10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yolo | 36 | 324 | 405 | 360 | 0.972 | 0.414 | 0.437 | 0.917 | 0.694 | 0.238 | 0.188 | 0.536 |
| interp | 36 | 324 | 405 | 360 | 0.972 | 0.512 | 0.457 | 0.917 | 0.694 | 0.284 | 0.195 | 0.536 |
| rts | 36 | 324 | 405 | 360 | 0.167 | 0.454 | 0.338 | 0.933 | 0.083 | 0.127 | 0.121 | 0.506 |
| tgct | 36 | 324 | 405 | 360 | 0.972 | 0.475 | 0.420 | 0.914 | 0.722 | 0.256 | 0.170 | 0.506 |
| hybrik | 36 | 324 | 405 | 360 | 1.000 | 0.102 | 0.563 | 0.711 | 0.611 | 0.022 | 0.160 | 0.214 |

## A2 by joint group (condition A) - P9201256

| condition | n sho | n elb | n wri | n hip | n kne | n ank | sho@0.20 | elb@0.20 | wri@0.20 | hip@0.20 | kne@0.20 | ank@0.20 | sho@0.10 | elb@0.10 | wri@0.10 | hip@0.10 | kne@0.10 | ank@0.10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yolo | 185 | 196 | 156 | 196 | 196 | 196 | 0.638 | 0.612 | 0.596 | 0.520 | 0.638 | 0.602 | 0.281 | 0.490 | 0.481 | 0.133 | 0.306 | 0.316 |
| interp | 185 | 196 | 156 | 196 | 196 | 196 | 0.719 | 0.648 | 0.647 | 0.546 | 0.663 | 0.602 | 0.292 | 0.520 | 0.532 | 0.133 | 0.316 | 0.316 |
| rts | 185 | 196 | 156 | 196 | 196 | 196 | 0.611 | 0.582 | 0.545 | 0.459 | 0.612 | 0.531 | 0.259 | 0.311 | 0.372 | 0.066 | 0.250 | 0.235 |
| tgct | 185 | 196 | 156 | 196 | 196 | 196 | 0.686 | 0.602 | 0.609 | 0.520 | 0.643 | 0.612 | 0.259 | 0.464 | 0.513 | 0.117 | 0.286 | 0.316 |
| hybrik | 185 | 196 | 156 | 196 | 196 | 196 | 0.486 | 0.531 | 0.487 | 0.490 | 0.597 | 0.357 | 0.065 | 0.219 | 0.141 | 0.117 | 0.250 | 0.112 |

## A1 by phase (condition A) - PA041271

| condition | n pre | n contact | n hold | n post | pre@0.20 | contact@0.20 | hold@0.20 | post@0.20 | pre@0.10 | contact@0.10 | hold@0.10 | post@0.10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yolo | 384 | 36 | 108 | 204 | 0.966 | 0.861 | 0.065 | 0.676 | 0.638 | 0.361 | 0.019 | 0.338 |
| interp | 384 | 36 | 108 | 204 | 0.966 | 0.833 | 0.583 | 0.686 | 0.641 | 0.361 | 0.278 | 0.338 |
| rts | 384 | 36 | 108 | 204 | 0.818 | 0.667 | 0.417 | 0.667 | 0.312 | 0.222 | 0.148 | 0.260 |
| tgct | 384 | 36 | 108 | 204 | 0.969 | 0.833 | 0.481 | 0.676 | 0.633 | 0.361 | 0.176 | 0.338 |
| hybrik | 384 | 36 | 108 | 204 | 0.474 | 0.306 | 0.019 | 0.000 | 0.242 | 0.083 | 0.000 | 0.000 |

## A2 by joint group (condition A) - PA041271

| condition | n sho | n elb | n wri | n hip | n kne | n ank | sho@0.20 | elb@0.20 | wri@0.20 | hip@0.20 | kne@0.20 | ank@0.20 | sho@0.10 | elb@0.10 | wri@0.10 | hip@0.10 | kne@0.10 | ank@0.10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yolo | 122 | 122 | 122 | 122 | 122 | 122 | 0.672 | 0.680 | 0.689 | 0.820 | 0.811 | 0.811 | 0.303 | 0.484 | 0.533 | 0.287 | 0.623 | 0.467 |
| interp | 122 | 122 | 122 | 122 | 122 | 122 | 0.721 | 0.680 | 0.713 | 0.951 | 0.943 | 0.943 | 0.320 | 0.484 | 0.541 | 0.311 | 0.689 | 0.590 |
| rts | 122 | 122 | 122 | 122 | 122 | 122 | 0.770 | 0.590 | 0.508 | 0.828 | 0.820 | 0.738 | 0.262 | 0.320 | 0.156 | 0.221 | 0.336 | 0.320 |
| tgct | 122 | 122 | 122 | 122 | 122 | 122 | 0.762 | 0.689 | 0.713 | 0.861 | 0.893 | 0.934 | 0.328 | 0.492 | 0.541 | 0.320 | 0.615 | 0.525 |
| hybrik | 122 | 122 | 122 | 122 | 122 | 122 | 0.311 | 0.320 | 0.262 | 0.262 | 0.279 | 0.164 | 0.164 | 0.262 | 0.107 | 0.082 | 0.131 | 0.041 |

## Check: condition A vs condition B (v3, identity-corrected input), PCK@0.20 - P9201256

| condition (A row = B row) | all A / B / A-B | vis0 A / B / A-B | vis1 A / B / A-B | pre A / B / A-B | contact A / B / A-B | fusion A / B / A-B | fall A / B / A-B |
|---|---|---|---|---|---|---|---|
| yolo = raw_verified | 0.601 / 0.603 / -0.002 | 0.643 / 0.648 / -0.005 | 0.523 / 0.518 / +0.005 | 0.972 / 0.972 / +0.000 | 0.414 / 0.420 / -0.006 | 0.437 / 0.437 / +0.000 | 0.917 / 0.917 / +0.000 |
| interp = interp | 0.636 / 0.670 / -0.034 | 0.666 / 0.707 / -0.041 | 0.582 / 0.602 / -0.020 | 0.972 / 0.972 / +0.000 | 0.512 / 0.630 / -0.117 | 0.457 / 0.457 / +0.000 | 0.917 / 0.917 / +0.000 |
| rts = rts | 0.556 / 0.586 / -0.029 | 0.577 / 0.610 / -0.033 | 0.518 / 0.541 / -0.023 | 0.167 / 0.639 / -0.472 | 0.454 / 0.503 / -0.049 | 0.338 / 0.338 / +0.000 | 0.933 / 0.933 / +0.000 |
| tgct = tgct_v1 | 0.612 / 0.615 / -0.004 | 0.648 / 0.653 / -0.005 | 0.543 / 0.543 / +0.000 | 0.972 / 0.972 / +0.000 | 0.475 / 0.481 / -0.006 | 0.420 / 0.422 / -0.002 | 0.914 / 0.917 / -0.003 |
| hybrik = hybrik_struct | 0.492 / 0.492 / +0.000 | 0.487 / 0.487 / +0.000 | 0.500 / 0.500 / +0.000 | 1.000 / 1.000 / +0.000 | 0.102 / 0.102 / +0.000 | 0.563 / 0.563 / +0.000 | 0.711 / 0.711 / +0.000 |

## Check: condition A vs condition B (v3, identity-corrected input), PCK@0.20 - PA041271

| condition (A row = B row) | all A / B / A-B | vis0 A / B / A-B | vis1 A / B / A-B | pre A / B / A-B | contact A / B / A-B | hold A / B / A-B | post A / B / A-B |
|---|---|---|---|---|---|---|---|
| yolo = raw_verified | 0.747 / 0.747 / +0.000 | 0.838 / 0.838 / +0.000 | 0.575 / 0.575 / +0.000 | 0.966 / 0.966 / +0.000 | 0.861 / 0.861 / +0.000 | 0.065 / 0.065 / +0.000 | 0.676 / 0.676 / +0.000 |
| interp = interp | 0.825 / 0.821 / +0.004 | 0.917 / 0.912 / +0.004 | 0.651 / 0.647 / +0.004 | 0.966 / 0.966 / +0.000 | 0.833 / 0.833 / +0.000 | 0.583 / 0.556 / +0.028 | 0.686 / 0.686 / +0.000 |
| rts = rts | 0.709 / 0.697 / +0.012 | 0.806 / 0.794 / +0.013 | 0.524 / 0.512 / +0.012 | 0.818 / 0.818 / +0.000 | 0.667 / 0.611 / +0.056 | 0.417 / 0.389 / +0.028 | 0.667 / 0.647 / +0.020 |
| tgct = tgct_v1 | 0.809 / 0.809 / +0.000 | 0.904 / 0.904 / +0.000 | 0.627 / 0.627 / +0.000 | 0.969 / 0.969 / +0.000 | 0.833 / 0.833 / +0.000 | 0.481 / 0.481 / +0.000 | 0.676 / 0.676 / +0.000 |
| hybrik = hybrik_struct | 0.266 / 0.266 / +0.000 | 0.296 / 0.296 / +0.000 | 0.210 / 0.210 / +0.000 | 0.474 / 0.474 / +0.000 | 0.306 / 0.306 / +0.000 | 0.019 / 0.019 / +0.000 | 0.000 / 0.000 / +0.000 |

