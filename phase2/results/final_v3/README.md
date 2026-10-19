# final_v3 — final tables and figures (per-clip L_ref, 2026-10-19)

Ruler: PCK@α with the per-clip reference torso length L_ref (median shoulder-mid–hip-mid distance over GT frames with all four torso joints vis≠2): P9201256 440.7 px (n=87), PA041271 265.5 px (n=61). Per-frame results: ../final_v3_perframe/ (sensitivity only).

| output | script | inputs |
|---|---|---|
| pck_<clip>.md/.csv, pck_<clip>_bc.md/.csv, offset_*.csv, bias_*.csv | `phase2/pck.py <gt> <clip> name=sheet ... --alphas 0.10 0.20 --bias-correct clean --out phase2/results/final_v3` (13 sheets, see pck_<clip>.log) | ~/data/phase2_gt/gt_<clip>*.npz, ~/data/phase2_npz/win3162, win4358 |
| complementarity_<clip>_<hybrik>.md/.csv (3 pairs) | `phase2/scripts/complementarity.py` | interp / interp_ok and hybrik_struct / hybrik_struct_ok / hybrik_interp sheets |
| final_table_v3.md | `phase2/scripts/final_table_v3.py --dir phase2/results/final_v3` | the csv above |
| sensitivity_lref.md | `phase2/scripts/sensitivity_lref.py` | same sheets, both rulers |
| overlay/*.png, fig3_candidates.txt | `phase2/scripts/hybrik_overlay.py`, `phase2/scripts/fig3_hybrik_2x2.py` | outputs/20261018/<stem>_<tag>/hybrik/raw_images, res.pk |
| figures/ | see figures/README.md | |

Sheets: hybrik_* by `phase2/scripts/make_hybrik_sheet.py` (hybrik env) from outputs/20261018/*/hybrik/res.pk (made by `phase2/analysis/process_tackles.sh 20261018 phase2/analysis/tackles_1018.txt`); interp_ok by `phase2/scripts/make_interp_ok.py`.
Commits: 4a46440 (HybrIK sheets, pck NaN test + --bias-correct, complementarity, table v3), a8545c7 (HQ fixes 1–3: interp_ok, pre+fall calibration, fig 2x2), 759faa6 (per-clip L_ref), 936b43f (regenerated with L_ref, A5 three pairs, sensitivity).
Data: ~/data/phase2_npz (sheets), ~/data/phase2_gt (GT, re-annotation, frames), outputs/20261018 (HybrIK), ~/data/tgct/ckpt (T-GCT); GCS mirror gs://yu-thesis-migrate-2026/{phase2_npz,phase2_gt,outputs/20261018,labels}.

Identity fix (from phase2/results/identity_fix_<clip>.csv, judged from images): P9201256: 12 frames corrected of 20 verified even frames (no_valid 8, swap 3, fused 1); even frames in the GT range only, odd frames filled by apply_identity_fix.py --fill-odd | PA041271: 8 frames corrected of 61 verified even frames (no_valid 8); even frames in the GT range only, odd frames filled by apply_identity_fix.py --fill-odd
