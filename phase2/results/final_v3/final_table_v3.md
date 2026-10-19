# Final table v3 (2026-10-18)

Scoring: phase2/pck.py with the per-clip reference torso length L_ref = median shoulder-mid–hip-mid distance over GT frames with all four torso joints vis≠2 (P9201256 441 px, PA041271 266 px; pre-registered 2026-10-17). Per-frame results are kept in results/final_v3_perframe/ as a sensitivity check. GT frames only; NaN joint-frames excluded from the denominator; (0,0) misses count as wrong. Main metric PCK@0.20, secondary @0.10. hybrik_struct = all window even frames (person-selection failures retained and scored against the GT); hybrik_struct_ok = frames where HybrIK's crop centre lies inside the verified tackler box (NaN elsewhere); hybrik_interp = hybrik_struct_ok with not-ok frames bridged by linear interpolation. Bias-corrected, oracle and 2x2 tables are diagnostics (appendix), not contestants.
n counts joint-frames, not images. hybrik_struct_ok is conditional on person_ok and has a different denominator. Self-PCK is a re-annotation consistency reference, not a strict mathematical ceiling. Complementarity uses only joint-frames scored by both sheets; its rates may differ from standalone PCK. The oracle is an upper bound for choosing between the two predictions on that common set, not arbitrary fusion.
Denominators: hybrik_struct_ok is compared with interp_ok (the same not-person_ok frames blanked), never directly with interp; where every frame is person_ok (P9201256 fusion, n=405) interp = interp_ok and the usual comparison holds. Complementarity (i) interp vs hybrik_struct is the pipeline as it stands; (ii) interp_ok vs hybrik_struct_ok is the complementarity when person selection is right; (iii) interp vs hybrik_interp.

## Main table — P9201256
self-PCK ceiling (5-frame re-annotation, L_ref 441 px): vis0 0.89@0.10 / 0.92@0.20, vis1 0.70 / 1.00

| condition | n all | n vis0 | n vis1 | all@0.20 | vis0@0.20 | vis1@0.20 | all@0.10 | vis0@0.10 | vis1@0.10 |
|---|---|---|---|---|---|---|---|---|---|
| raw_verified | 1125 | 733 | 392 | 0.603 | 0.648 | 0.518 | 0.337 | 0.371 | 0.273 |
| interp | 1125 | 733 | 392 | 0.670 | 0.707 | 0.602 | 0.368 | 0.407 | 0.296 |
| interp_ok | 969 | 631 | 338 | 0.669 | 0.707 | 0.598 | 0.369 | 0.404 | 0.305 |
| rts | 1125 | 733 | 392 | 0.586 | 0.610 | 0.541 | 0.252 | 0.266 | 0.227 |
| tgct_v1 | 1125 | 733 | 392 | 0.615 | 0.653 | 0.543 | 0.325 | 0.357 | 0.265 |
| hybrik_struct | 1125 | 733 | 392 | 0.492 | 0.487 | 0.500 | 0.152 | 0.124 | 0.204 |
| hybrik_struct_ok | 969 | 631 | 338 | 0.557 | 0.547 | 0.577 | 0.173 | 0.139 | 0.237 |
| hybrik_interp | 1125 | 733 | 392 | 0.495 | 0.490 | 0.505 | 0.153 | 0.126 | 0.204 |

Footnote: HybrIK person check on the 98 GT frames: person_ok 85, no verified box 9 (fused 1, no_valid 8: contact), HybrIK crop centre outside the verified box on 4 frames (3260, 3266, 3268, 3270: contact). Bias calibration: pre+fall, 33 GT frames (A3).

## Main table — PA041271
self-PCK ceiling (L_ref 266 px): vis0 0.92@0.10 / 1.00@0.20, vis1 0.81 / 1.00

| condition | n all | n vis0 | n vis1 | all@0.20 | vis0@0.20 | vis1@0.20 | all@0.10 | vis0@0.10 | vis1@0.10 |
|---|---|---|---|---|---|---|---|---|---|
| raw_verified | 732 | 480 | 252 | 0.747 | 0.838 | 0.575 | 0.449 | 0.523 | 0.310 |
| interp | 732 | 480 | 252 | 0.821 | 0.912 | 0.647 | 0.496 | 0.575 | 0.345 |
| interp_ok | 528 | 346 | 182 | 0.831 | 0.925 | 0.654 | 0.498 | 0.564 | 0.374 |
| rts | 732 | 480 | 252 | 0.697 | 0.794 | 0.512 | 0.264 | 0.285 | 0.222 |
| tgct_v1 | 732 | 480 | 252 | 0.809 | 0.904 | 0.627 | 0.470 | 0.544 | 0.329 |
| hybrik_struct | 732 | 480 | 252 | 0.266 | 0.296 | 0.210 | 0.131 | 0.135 | 0.123 |
| hybrik_struct_ok | 528 | 346 | 182 | 0.367 | 0.408 | 0.291 | 0.182 | 0.188 | 0.170 |
| hybrik_interp | 732 | 480 | 252 | 0.268 | 0.298 | 0.210 | 0.131 | 0.135 | 0.123 |

Footnote: HybrIK person check on the 61 GT frames: person_ok 44, no verified box 8 (no_valid 4496-4512 exc. 4500), HybrIK crop centre outside the verified box on 9 frames (4426-4442, even frames). Bias calibration: pre 32 + post 17 GT frames.

# Appendix

## A1 by phase — P9201256

| condition | n pre | n contact | n fusion | n fall | pre@0.20 | contact@0.20 | fusion@0.20 | fall@0.20 | pre@0.10 | contact@0.10 | fusion@0.10 | fall@0.10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw_verified | 36 | 324 | 405 | 360 | 0.972 | 0.420 | 0.437 | 0.917 | 0.694 | 0.262 | 0.188 | 0.536 |
| interp | 36 | 324 | 405 | 360 | 0.972 | 0.630 | 0.457 | 0.917 | 0.694 | 0.361 | 0.195 | 0.536 |
| interp_ok | 36 | 168 | 405 | 360 | 0.972 | 0.583 | 0.457 | 0.917 | 0.694 | 0.363 | 0.195 | 0.536 |
| rts | 36 | 324 | 405 | 360 | 0.639 | 0.503 | 0.338 | 0.933 | 0.278 | 0.133 | 0.121 | 0.506 |
| tgct_v1 | 36 | 324 | 405 | 360 | 0.972 | 0.481 | 0.422 | 0.917 | 0.722 | 0.265 | 0.173 | 0.511 |
| hybrik_struct | 36 | 324 | 405 | 360 | 1.000 | 0.102 | 0.563 | 0.711 | 0.611 | 0.022 | 0.160 | 0.214 |
| hybrik_struct_ok | 36 | 168 | 405 | 360 | 1.000 | 0.119 | 0.563 | 0.711 | 0.611 | 0.024 | 0.160 | 0.214 |
| hybrik_interp | 36 | 324 | 405 | 360 | 1.000 | 0.114 | 0.563 | 0.711 | 0.611 | 0.025 | 0.160 | 0.214 |
| rts_sa1e-3 | 36 | 324 | 405 | 360 | 0.944 | 0.614 | 0.447 | 0.917 | 0.722 | 0.340 | 0.188 | 0.542 |
| tgct_v1m | 36 | 324 | 405 | 360 | 0.972 | 0.491 | 0.422 | 0.917 | 0.694 | 0.290 | 0.178 | 0.536 |
| tgct_v1g | 36 | 324 | 405 | 360 | 0.972 | 0.630 | 0.442 | 0.917 | 0.694 | 0.361 | 0.188 | 0.536 |
| interp_oracle | 36 | 324 | 405 | 360 | 0.972 | 0.531 | 0.331 | 0.658 | 0.667 | 0.306 | 0.143 | 0.350 |
| tgct_v1_oracle | 36 | 324 | 405 | 360 | 0.917 | 0.429 | 0.279 | 0.653 | 0.528 | 0.253 | 0.126 | 0.356 |

## A2 by joint group — P9201256

| condition | n sho | n elb | n wri | n hip | n kne | n ank | sho@0.20 | elb@0.20 | wri@0.20 | hip@0.20 | kne@0.20 | ank@0.20 | sho@0.10 | elb@0.10 | wri@0.10 | hip@0.10 | kne@0.10 | ank@0.10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw_verified | 185 | 196 | 156 | 196 | 196 | 196 | 0.632 | 0.612 | 0.583 | 0.526 | 0.643 | 0.617 | 0.281 | 0.490 | 0.474 | 0.133 | 0.327 | 0.342 |
| interp | 185 | 196 | 156 | 196 | 196 | 196 | 0.735 | 0.689 | 0.647 | 0.582 | 0.714 | 0.653 | 0.297 | 0.536 | 0.519 | 0.133 | 0.378 | 0.372 |
| interp_ok | 159 | 170 | 130 | 170 | 170 | 170 | 0.748 | 0.694 | 0.654 | 0.559 | 0.694 | 0.665 | 0.314 | 0.553 | 0.538 | 0.135 | 0.347 | 0.365 |
| rts | 185 | 196 | 156 | 196 | 196 | 196 | 0.616 | 0.602 | 0.551 | 0.510 | 0.648 | 0.582 | 0.254 | 0.316 | 0.372 | 0.071 | 0.276 | 0.250 |
| tgct_v1 | 185 | 196 | 156 | 196 | 196 | 196 | 0.686 | 0.622 | 0.603 | 0.526 | 0.633 | 0.622 | 0.265 | 0.485 | 0.481 | 0.117 | 0.301 | 0.332 |
| hybrik_struct | 185 | 196 | 156 | 196 | 196 | 196 | 0.486 | 0.531 | 0.487 | 0.490 | 0.597 | 0.357 | 0.065 | 0.219 | 0.141 | 0.117 | 0.250 | 0.112 |
| hybrik_struct_ok | 159 | 170 | 130 | 170 | 170 | 170 | 0.566 | 0.582 | 0.577 | 0.565 | 0.659 | 0.400 | 0.075 | 0.247 | 0.162 | 0.135 | 0.282 | 0.129 |
| hybrik_interp | 185 | 196 | 156 | 196 | 196 | 196 | 0.492 | 0.526 | 0.494 | 0.495 | 0.607 | 0.357 | 0.065 | 0.214 | 0.135 | 0.117 | 0.260 | 0.117 |

## A3 bias-corrected (within-clip calibration: P9201256 pre+fall / PA041271 pre+post, vis0; secondary) — P9201256

| condition | n all | n vis0 | n vis1 | all@0.20 | vis0@0.20 | vis1@0.20 | all@0.10 | vis0@0.10 | vis1@0.10 |
|---|---|---|---|---|---|---|---|---|---|
| raw_verified | 1125 | 733 | 392 | 0.620 | 0.675 | 0.515 | 0.408 | 0.486 | 0.263 |
| interp | 1125 | 733 | 392 | 0.679 | 0.734 | 0.577 | 0.451 | 0.535 | 0.293 |
| interp_ok | 969 | 631 | 338 | 0.679 | 0.739 | 0.568 | 0.448 | 0.537 | 0.281 |
| rts | 1125 | 733 | 392 | 0.572 | 0.644 | 0.436 | 0.293 | 0.405 | 0.084 |
| tgct_v1 | 1125 | 733 | 392 | 0.622 | 0.673 | 0.528 | 0.412 | 0.480 | 0.283 |
| hybrik_struct | 1125 | 733 | 392 | 0.570 | 0.602 | 0.510 | 0.333 | 0.419 | 0.173 |
| hybrik_struct_ok | 969 | 631 | 338 | 0.648 | 0.681 | 0.586 | 0.385 | 0.483 | 0.201 |
| hybrik_interp | 1125 | 733 | 392 | 0.577 | 0.608 | 0.518 | 0.336 | 0.422 | 0.176 |

Calibration footnote: 33 GT frames; interp n_used per joint 3-33 (0 joints uncorrected); interp_ok n_used per joint 3-33 (0 joints uncorrected); hybrik_struct_ok n_used per joint 3-33 (0 joints uncorrected). fall is a fallen posture: the joint-definition offset there may differ from standing, so the P9201256 bias-corrected values are read as a secondary metric.

## A4 sensitivity / variants / oracle rows — P9201256

| condition | n all | n vis0 | n vis1 | all@0.20 | vis0@0.20 | vis1@0.20 | all@0.10 | vis0@0.10 | vis1@0.10 |
|---|---|---|---|---|---|---|---|---|---|
| rts_sa1e-3 | 1125 | 733 | 392 | 0.661 | 0.711 | 0.569 | 0.362 | 0.401 | 0.288 |
| tgct_v1m | 1125 | 733 | 392 | 0.618 | 0.652 | 0.554 | 0.341 | 0.374 | 0.281 |
| tgct_v1g | 1125 | 733 | 392 | 0.665 | 0.704 | 0.592 | 0.365 | 0.404 | 0.293 |
| interp_oracle | 1125 | 733 | 392 | 0.514 | 0.698 | 0.168 | 0.273 | 0.401 | 0.033 |
| tgct_v1_oracle | 1125 | 733 | 392 | 0.462 | 0.638 | 0.133 | 0.249 | 0.362 | 0.038 |

## A5 complementarity (i) pipeline as it stands — ORACLE upper bound @0.20, interp vs hybrik_struct — P9201256

| subset | n | interp | hybrik_struct | oracle | gain | both | interp-only | hybrik_struct-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.670 | 0.492 | 0.781 | +0.111 | 428 | 326 | 125 | 246 |
| vis0 | 733 | 0.707 | 0.487 | 0.806 | +0.100 | 284 | 234 | 73 | 142 |
| vis1 | 392 | 0.602 | 0.500 | 0.735 | +0.133 | 144 | 92 | 52 | 104 |
| pre | 36 | 0.972 | 1.000 | 1.000 | +0.000 | 35 | 0 | 1 | 0 |
| contact | 324 | 0.630 | 0.102 | 0.660 | +0.031 | 23 | 181 | 10 | 110 |
| fusion | 405 | 0.457 | 0.563 | 0.716 | +0.153 | 123 | 62 | 105 | 115 |
| fall | 360 | 0.917 | 0.711 | 0.942 | +0.025 | 247 | 83 | 9 | 21 |

## A5 complementarity (ii) person_ok frames: complementarity when person selection is right — ORACLE upper bound @0.20, interp_ok vs hybrik_struct_ok — P9201256

| subset | n | interp_ok | hybrik_struct_ok | oracle | gain | both | interp_ok-only | hybrik_struct_ok-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 969 | 0.669 | 0.557 | 0.795 | +0.126 | 418 | 230 | 122 | 199 |
| vis0 | 631 | 0.707 | 0.547 | 0.818 | +0.111 | 275 | 171 | 70 | 115 |
| vis1 | 338 | 0.598 | 0.577 | 0.751 | +0.154 | 143 | 59 | 52 | 84 |
| pre | 36 | 0.972 | 1.000 | 1.000 | +0.000 | 35 | 0 | 1 | 0 |
| contact | 168 | 0.583 | 0.119 | 0.625 | +0.042 | 13 | 85 | 7 | 63 |
| fusion | 405 | 0.457 | 0.563 | 0.716 | +0.153 | 123 | 62 | 105 | 115 |
| fall | 360 | 0.917 | 0.711 | 0.942 | +0.025 | 247 | 83 | 9 | 21 |

## A5 complementarity (iii) — ORACLE upper bound @0.20, interp vs hybrik_interp — P9201256

| subset | n | interp | hybrik_interp | oracle | gain | both | interp-only | hybrik_interp-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 1125 | 0.670 | 0.495 | 0.781 | +0.111 | 432 | 322 | 125 | 246 |
| vis0 | 733 | 0.707 | 0.490 | 0.805 | +0.098 | 287 | 231 | 72 | 143 |
| vis1 | 392 | 0.602 | 0.505 | 0.737 | +0.135 | 145 | 91 | 53 | 103 |
| pre | 36 | 0.972 | 1.000 | 1.000 | +0.000 | 35 | 0 | 1 | 0 |
| contact | 324 | 0.630 | 0.114 | 0.660 | +0.031 | 27 | 177 | 10 | 110 |
| fusion | 405 | 0.457 | 0.563 | 0.716 | +0.153 | 123 | 62 | 105 | 115 |
| fall | 360 | 0.917 | 0.711 | 0.942 | +0.025 | 247 | 83 | 9 | 21 |

## A1 by phase — PA041271

| condition | n pre | n contact | n hold | n post | pre@0.20 | contact@0.20 | hold@0.20 | post@0.20 | pre@0.10 | contact@0.10 | hold@0.10 | post@0.10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw_verified | 384 | 36 | 108 | 204 | 0.966 | 0.861 | 0.065 | 0.676 | 0.638 | 0.361 | 0.019 | 0.338 |
| interp | 384 | 36 | 108 | 204 | 0.966 | 0.833 | 0.556 | 0.686 | 0.641 | 0.361 | 0.324 | 0.338 |
| interp_ok | 276 | 36 | 12 | 204 | 0.953 | 0.833 | 0.500 | 0.686 | 0.649 | 0.361 | 0.167 | 0.338 |
| rts | 384 | 36 | 108 | 204 | 0.818 | 0.611 | 0.389 | 0.647 | 0.315 | 0.167 | 0.148 | 0.245 |
| tgct_v1 | 384 | 36 | 108 | 204 | 0.969 | 0.833 | 0.481 | 0.676 | 0.633 | 0.361 | 0.176 | 0.338 |
| hybrik_struct | 384 | 36 | 108 | 204 | 0.474 | 0.306 | 0.019 | 0.000 | 0.242 | 0.083 | 0.000 | 0.000 |
| hybrik_struct_ok | 276 | 36 | 12 | 204 | 0.659 | 0.306 | 0.083 | 0.000 | 0.337 | 0.083 | 0.000 | 0.000 |
| hybrik_interp | 384 | 36 | 108 | 204 | 0.474 | 0.306 | 0.028 | 0.000 | 0.242 | 0.083 | 0.000 | 0.000 |
| rts_sa1e-3 | 384 | 36 | 108 | 204 | 0.977 | 0.861 | 0.546 | 0.691 | 0.643 | 0.333 | 0.352 | 0.348 |
| tgct_v1m | 384 | 36 | 108 | 204 | 0.966 | 0.833 | 0.481 | 0.686 | 0.641 | 0.361 | 0.176 | 0.343 |
| tgct_v1g | 384 | 36 | 108 | 204 | 0.966 | 0.833 | 0.556 | 0.686 | 0.641 | 0.361 | 0.324 | 0.343 |
| interp_oracle | 384 | 36 | 108 | 204 | 0.852 | 0.639 | 0.352 | 0.652 | 0.549 | 0.333 | 0.241 | 0.319 |
| tgct_v1_oracle | 384 | 36 | 108 | 204 | 0.810 | 0.556 | 0.324 | 0.642 | 0.510 | 0.278 | 0.130 | 0.324 |

## A2 by joint group — PA041271

| condition | n sho | n elb | n wri | n hip | n kne | n ank | sho@0.20 | elb@0.20 | wri@0.20 | hip@0.20 | kne@0.20 | ank@0.20 | sho@0.10 | elb@0.10 | wri@0.10 | hip@0.10 | kne@0.10 | ank@0.10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw_verified | 122 | 122 | 122 | 122 | 122 | 122 | 0.672 | 0.680 | 0.689 | 0.820 | 0.811 | 0.811 | 0.303 | 0.484 | 0.533 | 0.287 | 0.623 | 0.467 |
| interp | 122 | 122 | 122 | 122 | 122 | 122 | 0.713 | 0.680 | 0.705 | 0.943 | 0.943 | 0.943 | 0.328 | 0.484 | 0.541 | 0.320 | 0.705 | 0.598 |
| interp_ok | 88 | 88 | 88 | 88 | 88 | 88 | 0.727 | 0.727 | 0.761 | 0.932 | 0.920 | 0.920 | 0.318 | 0.568 | 0.580 | 0.341 | 0.659 | 0.523 |
| rts | 122 | 122 | 122 | 122 | 122 | 122 | 0.762 | 0.590 | 0.484 | 0.787 | 0.820 | 0.738 | 0.254 | 0.320 | 0.156 | 0.221 | 0.320 | 0.311 |
| tgct_v1 | 122 | 122 | 122 | 122 | 122 | 122 | 0.762 | 0.689 | 0.713 | 0.861 | 0.893 | 0.934 | 0.328 | 0.492 | 0.541 | 0.320 | 0.615 | 0.525 |
| hybrik_struct | 122 | 122 | 122 | 122 | 122 | 122 | 0.311 | 0.320 | 0.262 | 0.262 | 0.279 | 0.164 | 0.164 | 0.262 | 0.107 | 0.082 | 0.131 | 0.041 |
| hybrik_struct_ok | 88 | 88 | 88 | 88 | 88 | 88 | 0.432 | 0.432 | 0.364 | 0.364 | 0.386 | 0.227 | 0.227 | 0.364 | 0.148 | 0.114 | 0.182 | 0.057 |
| hybrik_interp | 122 | 122 | 122 | 122 | 122 | 122 | 0.311 | 0.328 | 0.262 | 0.262 | 0.279 | 0.164 | 0.164 | 0.262 | 0.107 | 0.082 | 0.131 | 0.041 |

## A3 bias-corrected (within-clip calibration: P9201256 pre+fall / PA041271 pre+post, vis0; secondary) — PA041271

| condition | n all | n vis0 | n vis1 | all@0.20 | vis0@0.20 | vis1@0.20 | all@0.10 | vis0@0.10 | vis1@0.10 |
|---|---|---|---|---|---|---|---|---|---|
| raw_verified | 732 | 480 | 252 | 0.762 | 0.863 | 0.571 | 0.590 | 0.713 | 0.357 |
| interp | 732 | 480 | 252 | 0.837 | 0.940 | 0.643 | 0.639 | 0.773 | 0.385 |
| interp_ok | 528 | 346 | 182 | 0.858 | 0.962 | 0.659 | 0.644 | 0.754 | 0.434 |
| rts | 732 | 480 | 252 | 0.714 | 0.823 | 0.508 | 0.403 | 0.496 | 0.226 |
| tgct_v1 | 732 | 480 | 252 | 0.833 | 0.944 | 0.623 | 0.617 | 0.746 | 0.373 |
| hybrik_struct | 732 | 480 | 252 | 0.317 | 0.358 | 0.238 | 0.221 | 0.258 | 0.151 |
| hybrik_struct_ok | 528 | 346 | 182 | 0.434 | 0.488 | 0.330 | 0.305 | 0.355 | 0.209 |
| hybrik_interp | 732 | 480 | 252 | 0.317 | 0.358 | 0.238 | 0.221 | 0.258 | 0.151 |

Calibration footnote: 49 GT frames; interp n_used per joint 0-49 (1 joints uncorrected); interp_ok n_used per joint 0-40 (1 joints uncorrected); hybrik_struct_ok n_used per joint 0-23 (1 joints uncorrected). fall is a fallen posture: the joint-definition offset there may differ from standing, so the P9201256 bias-corrected values are read as a secondary metric.

## A4 sensitivity / variants / oracle rows — PA041271

| condition | n all | n vis0 | n vis1 | all@0.20 | vis0@0.20 | vis1@0.20 | all@0.10 | vis0@0.10 | vis1@0.10 |
|---|---|---|---|---|---|---|---|---|---|
| rts_sa1e-3 | 732 | 480 | 252 | 0.828 | 0.917 | 0.659 | 0.503 | 0.583 | 0.349 |
| tgct_v1m | 732 | 480 | 252 | 0.810 | 0.904 | 0.631 | 0.475 | 0.550 | 0.333 |
| tgct_v1g | 732 | 480 | 252 | 0.821 | 0.912 | 0.647 | 0.497 | 0.577 | 0.345 |
| interp_oracle | 732 | 480 | 252 | 0.712 | 0.910 | 0.333 | 0.429 | 0.575 | 0.151 |
| tgct_v1_oracle | 732 | 480 | 252 | 0.679 | 0.900 | 0.258 | 0.391 | 0.531 | 0.123 |

## A5 complementarity (i) pipeline as it stands — ORACLE upper bound @0.20, interp vs hybrik_struct — PA041271

| subset | n | interp | hybrik_struct | oracle | gain | both | interp-only | hybrik_struct-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.821 | 0.266 | 0.842 | +0.020 | 180 | 421 | 15 | 116 |
| vis0 | 480 | 0.912 | 0.296 | 0.933 | +0.021 | 132 | 306 | 10 | 32 |
| vis1 | 252 | 0.647 | 0.210 | 0.667 | +0.020 | 48 | 115 | 5 | 84 |
| pre | 384 | 0.966 | 0.474 | 0.995 | +0.029 | 171 | 200 | 11 | 2 |
| contact | 36 | 0.833 | 0.306 | 0.889 | +0.056 | 9 | 21 | 2 | 4 |
| hold | 108 | 0.556 | 0.019 | 0.574 | +0.019 | 0 | 60 | 2 | 46 |
| post | 204 | 0.686 | 0.000 | 0.686 | +0.000 | 0 | 140 | 0 | 64 |

## A5 complementarity (ii) person_ok frames: complementarity when person selection is right — ORACLE upper bound @0.20, interp_ok vs hybrik_struct_ok — PA041271

| subset | n | interp_ok | hybrik_struct_ok | oracle | gain | both | interp_ok-only | hybrik_struct_ok-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 528 | 0.831 | 0.367 | 0.858 | +0.027 | 180 | 259 | 14 | 75 |
| vis0 | 346 | 0.925 | 0.408 | 0.951 | +0.026 | 132 | 188 | 9 | 17 |
| vis1 | 182 | 0.654 | 0.291 | 0.681 | +0.027 | 48 | 71 | 5 | 58 |
| pre | 276 | 0.953 | 0.659 | 0.993 | +0.040 | 171 | 92 | 11 | 2 |
| contact | 36 | 0.833 | 0.306 | 0.889 | +0.056 | 9 | 21 | 2 | 4 |
| hold | 12 | 0.500 | 0.083 | 0.583 | +0.083 | 0 | 6 | 1 | 5 |
| post | 204 | 0.686 | 0.000 | 0.686 | +0.000 | 0 | 140 | 0 | 64 |

## A5 complementarity (iii) — ORACLE upper bound @0.20, interp vs hybrik_interp — PA041271

| subset | n | interp | hybrik_interp | oracle | gain | both | interp-only | hybrik_interp-only | neither |
|---|---|---|---|---|---|---|---|---|---|
| all | 732 | 0.821 | 0.268 | 0.843 | +0.022 | 180 | 421 | 16 | 115 |
| vis0 | 480 | 0.912 | 0.298 | 0.935 | +0.023 | 132 | 306 | 11 | 31 |
| vis1 | 252 | 0.647 | 0.210 | 0.667 | +0.020 | 48 | 115 | 5 | 84 |
| pre | 384 | 0.966 | 0.474 | 0.995 | +0.029 | 171 | 200 | 11 | 2 |
| contact | 36 | 0.833 | 0.306 | 0.889 | +0.056 | 9 | 21 | 2 | 4 |
| hold | 108 | 0.556 | 0.028 | 0.583 | +0.028 | 0 | 60 | 3 | 45 |
| post | 204 | 0.686 | 0.000 | 0.686 | +0.000 | 0 | 140 | 0 | 64 |

## A6 gap-length breakdown (T-GCT): see phase2/results/tgct_v1/ (tgct_report.py output, unchanged)

