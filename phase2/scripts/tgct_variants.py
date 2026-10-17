# phase2/scripts/tgct_variants.py
"""Inference-time variants built from a tgct_v1 answer sheet (no retraining):
   v1m : residual applied only on unobserved joints (observed joints = YOLO as-is)
   v1g : v1m, and only inside gaps longer than GATE even frames (short gaps = linear interpolation)
Run in rugby, from the repo root:  python -m phase2.scripts.tgct_variants
"""
import numpy as np
from pathlib import Path
from phase2.scripts.tgct_report import run_lengths

GATE = 14                                    # val breakdown: interpolation wins at <= 14 even frames
HOME = Path.home()
for clip, win in [("P9201256", "win3162"), ("PA041271", "win4358")]:
    p = HOME / f"data/phase2_npz/{win}/tgct_v1_{clip}.npz"
    z = dict(np.load(p, allow_pickle=True))
    obs, interp, res = z["obs"], z["interp"], z["residual"]
    L = run_lengths(~obs)
    for tag, use in [("v1m", ~obs), ("v1g", (~obs) & (L > GATE))]:
        coords = np.where(use[..., None], interp + res, interp).astype(np.float32)   # interp == YOLO on observed joints
        out = dict(z); out["coords"] = coords; out["source"] = f"tgct_{tag}"
        np.savez(p.with_name(f"tgct_{tag}_{clip}.npz"), **out)
        print(f"{clip} {tag}: residual kept on {int(use.sum()):4d}/{obs.size} joint-frames")