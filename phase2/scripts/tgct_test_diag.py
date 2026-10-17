# phase2/scripts/tgct_test_diag.py
"""Why does T-GCT lose on the test clips? Gap lengths, residual sizes and GT-vis vs YOLO-observed, from the tgct_v1 sheets."""
import numpy as np
from pathlib import Path
from phase2.scripts.tgct_report import run_lengths
from phase2.pck import PHASES

HOME = Path.home()
SHEETS = {"P9201256": HOME / "data/phase2_npz/win3162/tgct_v1_P9201256.npz",
          "PA041271": HOME / "data/phase2_npz/win4358/tgct_v1_PA041271.npz"}
GT = {"P9201256": HOME / "data/phase2_gt/gt_P9201256_tackler.npz",
      "PA041271": HOME / "data/phase2_gt/gt_PA041271_win4358_tackler.npz"}
BINS = [(1, 14), (15, 40), (41, 64), (65, 10**9)]

for clip, p in SHEETS.items():
    z = np.load(p, allow_pickle=True)
    obs, res, fi = z["obs"], z["residual"], z["frame_index"]
    W, Hh = int(z["W"]), int(z["H"])
    print(f"\n=== {clip}: unobserved joint-frames {int((~obs).sum())}/{obs.size}")
    L = run_lengths(~obs)                                   # gap length (even frames) of each unobserved point
    for lo, hi in BINS:
        m = (L >= lo) & (L <= hi)
        print(f"   gap {lo:>2d}-{'inf' if hi > 10**6 else hi:<3}: {int(m.sum()):4d} unobserved joint-frames")
    r = (np.abs(res) * np.array([W, Hh])).sum(-1)           # |dx|+|dy| in px
    print(f"   {'phase':8s} {'frames':>6s} {'|res| obs px':>13s} {'|res| unobs px':>15s} {'obs moved >27px':>16s}")
    for name, lo, hi in PHASES[clip]:
        m = (fi >= lo) & (fi <= hi)
        o, rr = obs[m], r[m]
        print(f"   {name:8s} {int(m.sum()):6d} {rr[o].mean() if o.any() else 0:13.1f} {rr[~o].mean() if (~o).any() else 0:15.1f} {(rr[o] > 27).mean() if o.any() else 0:16.2f}")
    g = np.load(GT[clip])
    idx = {int(f): i for i, f in enumerate(fi)}
    sel = np.array([idx[int(f)] for f in g["frame_index"]])
    vis, o = g["vis"], obs[sel]
    for v in (0, 1, 2):
        m = vis == v
        print(f"   GT vis={v}: {int(m.sum()):4d} joint-frames, of which YOLO 'observed' (conf>=0.5 & identity ok): {o[m].mean():.2f}")