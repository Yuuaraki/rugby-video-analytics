# final_v4 — condition A (as run), 2026-10-23

Main-table condition after the professor catch-up (claude/final_structure_v6_1022.md §1): no identity fix, no person_ok gate, every contestant scored on the GT's full joint-frames (P9201256 1125, PA041271 732). Ruler: per-clip L_ref (441 / 266 px), PCK@0.20 main, @0.10 secondary, no bias correction. v3 (conditions B and C) in ../final_v3/ is untouched; tag thesis-v3-final not moved. v3 and v4 numbers are never mixed in one table.

## Inputs (all in ~/data/phase2_npz/win3162 and win4358)

| row | sheet | made by |
|---|---|---|
| yolo | `yolo_raw_<clip>_tackler_assign.npz` (P9201256 2026-09-30, PA041271 2026-10-11) | `phase2/scripts/labels_to_sheets.py`: YOLO label txt → IoU tracking; the only human input is `--tackler-side` (initialisation rule, no per-frame correction). Same sheet that `apply_identity_fix.py` reads (its line 114) and that `PhaseB_temporal_baselines.ipynb` used for Fig. 3 (RTS weak/strong) and Fig. 6 (ID continuity) |
| interp, rts | `interp_<clip>_A.npz`, `rts_<clip>_A.npz` (`kalman_<clip>_A.npz` also written, not scored) | `make_temporal_sheets.py <win> <clip> --person tackler_assign --suffix _A`: sigma_m 0.00051, sigma_a 1e-5 from temporal_params_P9201256.json (same as v3); the `input` key records the source sheet |
| tgct | `tgct_v1_<clip>_A.npz` (label `tgct_v1_A`) | `python -m phase2.tgct.infer --sheet <assign sheet> --ckpt ~/data/tgct/ckpt/v1_best.pt --out ... --source tgct_v1_A`: inference only, no retraining |
| hybrik | `hybrik_struct_<clip>.npz` | unchanged from v3 (demo person selection as run) |

HQ's provisional names interp_A_<clip> / rts_A_<clip> / tgct_A_<clip> are the files above (suffix form, because make_temporal_sheets.py appends `--suffix`).

## Commands (rugby env, repo root)

```
python phase2/scripts/make_temporal_sheets.py ~/data/phase2_npz/win3162 P9201256 --person tackler_assign --suffix _A   # observed 2599/3060
python phase2/scripts/make_temporal_sheets.py ~/data/phase2_npz/win4358 PA041271 --person tackler_assign --suffix _A   # observed 2117/3060
python -m phase2.tgct.infer --sheet $HOME/data/phase2_npz/win3162/yolo_raw_P9201256_tackler_assign.npz --ckpt $HOME/data/tgct/ckpt/v1_best.pt --out $HOME/data/phase2_npz/win3162/tgct_v1_P9201256_A.npz --source tgct_v1_A   # 1305/1536 observed, max|res| 0.140
python -m phase2.tgct.infer --sheet $HOME/data/phase2_npz/win4358/yolo_raw_PA041271_tackler_assign.npz --ckpt $HOME/data/tgct/ckpt/v1_best.pt --out $HOME/data/phase2_npz/win4358/tgct_v1_PA041271_A.npz --source tgct_v1_A   # 1054/1536, max|res| 0.012
python phase2/pck.py $HOME/data/phase2_gt/gt_P9201256_tackler.npz P9201256 yolo=<assign> interp=<interp_A> rts=<rts_A> tgct=<tgct_A> hybrik=<hybrik_struct> --alphas 0.10 0.20 --out phase2/results/final_v4
python phase2/pck.py $HOME/data/phase2_gt/gt_PA041271_win4358_tackler.npz PA041271 <same five sheets for win4358> --alphas 0.10 0.20 --out phase2/results/final_v4
python phase2/scripts/final_table_v4.py --dir phase2/results/final_v4   # final_table_v4.md: main, A1 by phase, A2 by joint group, A-vs-B check tables
```

Full pck.py output: pck_<clip>.log (gitignored), pck_<clip>.md/.csv, offset_<clip>_<row>.csv.

## Open items resolved

- E-32: the unmodified sheet is `yolo_raw_<clip>_tackler_assign.npz`, an automatic output (table above). HQ's guess `yolo_raw_<clip>_tackler.npz` does not exist.
- E-35: infer.py builds the observation mask (`observed_mask`: conf >= 0.5 and not a no-detection frame) and the interpolation fill (`fill_and_features`) internally; without an `identity_verdict` key every frame is valid, so the assign sheet is passed directly.
- E-36: pck.py never reads conf (scored = vis<2 & finite; a (0,0) miss is wrong because its distance is large). In both the assign and the verified sheets (0,0) occurs only on whole-frame no-detection (plus no_valid frames in verified); joints with conf < 0.5 keep their coordinates (P9201256 assign: 1128 low-conf joints, of which 170 zero = 10 no-detection frames x 17). So the yolo row scores the detector coordinates as returned, low-confidence joints included, the same rule as v3's raw_verified row; conf >= 0.5 acts only on the input masks of interp / rts (temporal.observed_mask) and T-GCT (infer.py).
- E-33: skipped. tgct_fig_joint.py hard-codes the yolo / interp / tgct_v1 sheet names (only --hybrik and --out are arguments); Fig. 1 and figS stay the v3 figures, captioned as condition B (identity-corrected input).

## Checks (v6 §1.3), all passed

- (a) hybrik row = v3 hybrik_struct on every subset and both alphas (difference 0.000).
- (b) interp: P9201256 fusion .457 / fall .917, PA041271 pre .966 / contact .833 / post .686, identical to v3 (the fix touched 3228-3260 and 4496-4512 only; interpolation outside a gap returns the input).
- (c) |A - B| all@0.20: P9201256 max .034 (interp) <= .128; PA041271 max .012 (rts) <= .131.
- (d) interp A .636 >= .542 and .825 >= .690, so interpolation > HybrIK (as run) on both clips.
- Ranking (A, all@0.20), both clips: interp > tgct > yolo > rts > hybrik.

## Observations for HQ

1. The identity loss sits in contact: P9201256 interp contact .630 (B) -> .512 (A), all .670 -> .636; the yolo row moves only .603 -> .601. In A the carrier's joints come in as observed points (conf >= 0.5), so interpolation never bridges them; in B those frames were invalidated and bridged.
2. rts pre on P9201256 drops .639 -> .167 (n = 36, 3 frames): the swap at 3234-3238 sits right after pre, and the two-sided RTS smoother (T* ~ 7 frames) leaks the carrier's coordinates backwards; sigma_m = 0.00051 makes the filter trust wrong observations strongly.
3. PA041271: A ~ B (yolo and tgct identical, interp +.004, rts +.012). The 8 hold no_valid frames were already tackler-no-detection in the assign sheet (IoU tracking gave the single detection to the carrier); B only invalidated 3 odd frames via --transition, which the even-frame T-GCT input never sees.