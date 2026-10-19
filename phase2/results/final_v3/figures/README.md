# Figures for the thesis draft (final_v3, per-clip L_ref)

| file | made by | inputs |
|---|---|---|
| fig1_P9201256_R_wri_x.png, fig1_PA041271_R_wri_x.png | `PYTHONPATH=. python phase2/scripts/tgct_fig_joint.py --clip <c> --hybrik hybrik_struct_<c>.npz --out ...` | GT, yolo_raw_<c>_tackler_verified, interp_<c>, tgct_v1_<c>, hybrik_struct_<c> (~/data/phase2_npz/win*) |
| fig2_hybrik_2x2.png | `phase2/scripts/fig3_hybrik_2x2.py` (copy of overlay/fig3_hybrik_2x2.png); success frame 3314 chosen by max(#HybrIK correct - #interp correct @0.20, L_ref), candidates in fig3_candidates.txt; failures 3250 (L0), 4500 (L1) | GT, interp_<c>, hybrik_struct_<c>, outputs/20261018/*/hybrik/raw_images |
| fig3_rts_weak_P9201256.png, fig3_rts_strong_P9201256.png | copies of phase2/results/fig_temporal_P9201256_tackler_Rwri.png / _strong.png (`phase2/PhaseB_temporal_baselines.ipynb`; sigma_m = detector floor vs 0.0050) | yolo_raw_P9201256 sheets |
| fig4_sigma_a_hide_and_predict.png | copy of phase2/results/fig_sigma_a_solo.png (`phase2/scripts/choose_sigma_a.py`, solo PA041266+PA041267, 60-frame windows) | yolo_raw_PA04126x_solo.npz |
| fig5_tgct_curve_v1.png, fig5b_tgct_lambda.png | copies of phase2/results/fig_tgct_curve_v1.png and fig_tgct_curve_v1_lam1e-3_lam1e-2_lam1_lam10.png (`phase2/scripts/tgct_report.py`) | ~/data/tgct/ckpt |
| fig6_id_continuity_P9201256.png | copy of phase2/results/fig_id_continuity_P9201256_assign.png (`phase2/PhaseB_temporal_baselines.ipynb`) | yolo_raw_P9201256_*_assign.npz |
| fig7_phase2A_betas_dance.png, fig7_phase2A_beta_dist_dance.png, fig7_phase2A_forearm_vs_beta_dance.png | `phase2/phase2_01_respk_anatomy.ipynb` cell 4 (two plots; spike window 1030-1060 shaded) and cell 6, run with the `hybrik` kernel | phase2/results/res_dance/res.pk |

Bone-length CV raw vs struct (K2): exists as a printed table only (`phase2_01_respk_anatomy.ipynb` cell 3; B1 worksheet cell 8/10), no figure.
