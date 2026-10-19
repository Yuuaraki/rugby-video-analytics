"""Sensitivity of PCK@0.20 on hidden joints (vis1) to the ruler: per-frame torso length vs per-clip L_ref.
Both rulers are scored in one process with pck.py's own functions (pck.PER_FRAME toggles torso_length). Run in `rugby`.
  python phase2/scripts/sensitivity_lref.py --out phase2/results/final_v3/sensitivity_lref.md"""
import argparse, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from phase2 import pck
from phase2.pck import load_gt, load_sheet, align, pck_matrix, PHASES

NPZ, GT = Path.home() / "data/phase2_npz", Path.home() / "data/phase2_gt"
CLIPS = {"P9201256": (GT / "gt_P9201256_tackler.npz", NPZ / "win3162"), "PA041271": (GT / "gt_PA041271_win4358_tackler.npz", NPZ / "win4358")}
CONDS = {"yolo": "yolo_raw_{c}_tackler_verified", "interp": "interp_{c}", "interp_ok": "interp_ok_{c}",
         "rts": "rts_{c}", "tgct_v1": "tgct_v1_{c}", "hybrik_struct_ok": "hybrik_struct_ok_{c}"}
ALPHA = 0.20


def pck_vis1(pred, gt, per_frame, frame_mask=None):
    """PCK@ALPHA over vis==1 joint-frames (optionally inside a frame mask) under one ruler -> (value, n)."""
    pck.PER_FRAME = per_frame
    correct, scored, _ = pck_matrix(pred, gt, ALPHA)
    m = scored & (gt["vis"] == 1)
    if frame_mask is not None:
        m &= frame_mask[:, None]
    return float((correct & m).sum() / max(1, m.sum())), int(m.sum())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    
    md = ["# Sensitivity: per-frame torso length -> per-clip L_ref (PCK@0.20, vis1)", "",
          "| clip | condition | n | per-frame | L_ref | delta |", "|---|---|---|---|---|---|"]
    rows_phase = ["", "## By phase (vis1 only), interp_ok and hybrik_struct_ok", "", "| clip | condition | phase | n | per-frame | L_ref | delta |", "|---|---|---|---|---|---|---|"]
    for clip, (gt_path, d) in CLIPS.items():
        gt = load_gt(gt_path)
        preds = {k: align(gt, load_sheet(d / (v.format(c=clip) + ".npz"))) for k, v in CONDS.items()}
        for k, pred in preds.items():
            (a, n) = pck_vis1(pred, gt, True)
            (b, _) = pck_vis1(pred, gt, False)
            md.append(f"| {clip} | {k} | {n} | {a:.3f} | {b:.3f} | {b - a:+.3f} |")
        for k in ("interp_ok", "hybrik_struct_ok"):
            for ph, lo, hi in PHASES[clip]:
                fm = (gt["frames"] >= lo) & (gt["frames"] <= hi); (a, n) = pck_vis1(preds[k], gt, True, fm); (b, _) = pck_vis1(preds[k], gt, False, fm)
                rows_phase.append(f"| {clip} | {k} | {ph} | {n} | {a:.3f} | {b:.3f} | {b - a:+.3f} |")
    pck.PER_FRAME = False                                                  # leave the module in its default state
    text = "\n".join(md + rows_phase) + "\n"; Path(args.out).write_text(text); print(text)


if __name__ == "__main__":
    main()        
