# phase2/scripts/tgct_fig_joint.py
"""One joint's coordinate over time on a test clip: GT (filled = visible, open = occluded), YOLO observed points,
linear interpolation, T-GCT v1, with the occlusion phases shaded; residual panel below.
Run in rugby: python -m phase2.scripts.tgct_fig_joint --clip P9201256 --joint 5 --axis x
"""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from phase2.pck import PHASES
from phase2.tgct.graph import BODY12

HOME = Path.home()
CFG = {"P9201256": dict(win="win3162", gt="gt_P9201256_tackler.npz"),
       "PA041271": dict(win="win4358", gt="gt_PA041271_win4358_tackler.npz")}

ap = argparse.ArgumentParser()
ap.add_argument("--clip", default="P9201256", choices=list(CFG))
ap.add_argument("--joint", type=int, default=5, choices=range(len(BODY12)), help="BODY12 index (5 = R_wri)")
ap.add_argument("--axis", default="x", choices=["x", "y"])
ap.add_argument("--hybrik", default=None, help="HybrIK 6-struct sheet (coords, frame_index, person_ok); frames with person_ok=False are not drawn")
ap.add_argument("--out", default=None, help="output png (default: phase2/results/fig_tgct_<clip>_<joint>_<axis>.png)")
args = ap.parse_args()
cfg, a, j = CFG[args.clip], 0 if args.axis == "x" else 1, args.joint

t = np.load(HOME / f"data/phase2_npz/{cfg['win']}/tgct_v1_{args.clip}.npz", allow_pickle=True)
g = np.load(HOME / f"data/phase2_gt/{cfg['gt']}")
scale = int(t["W"]) if a == 0 else int(t["H"])
fi, obs = t["frame_index"], t["obs"][:, j]
tg, ip, res = t["coords"][:, j, a] * scale, t["interp"][:, j, a] * scale, t["residual"][:, j, a] * scale
gf, gc, gv = g["frame_index"], g["coords"][:, j, a] * scale, g["vis"][:, j]
hb = None
if args.hybrik:
    h = np.load(Path(args.hybrik).expanduser(), allow_pickle=True)
    hf, hc, ok = h["frame_index"], h["coords"][:, j, a].astype(float) * scale, h["person_ok"].astype(bool)
    hc[~ok] = np.nan                                   # break the line where HybrIK was on the wrong person / had no box
    hb = (hf, hc)

fig, (ax, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6.5), gridspec_kw=dict(height_ratios=[3, 1]))
for name, lo, hi in PHASES[args.clip]:
    if name in ("contact", "fusion", "hold"):
        lo, hi = max(lo, fi.min()), min(hi, fi.max())
        if lo > hi:
            continue
        for axx in (ax, ax2):
            axx.axvspan(lo, hi, color="orange", alpha=0.15)
        ax.text((lo + hi) / 2, 0.98, name, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=9)

ax.plot(fi[obs], ip[obs], "x", color="gray", ms=4, label="YOLO (observed on input)")
ax.plot(fi, ip, "--", color="tab:blue", lw=1.2, label="linear interpolation")
ax.plot(fi, tg, "-", color="tab:red", lw=1.2, label="T-GCT v1 (= interpolation + residual)")
if hb is not None:
    ax.plot(hb[0], hb[1], "-", color="purple", lw=1.2, label="HybrIK (6-struct)")
ax.plot(gf[gv == 0], gc[gv == 0], "o", color="k", ms=4, label="GT visible (vis=0)")
ax.plot(gf[gv == 1], gc[gv == 1], "o", mfc="none", mec="k", ms=5, label="GT occluded (vis=1)")
ax.set_ylabel(f"{BODY12[j]} {args.axis} [px]"); ax.legend(fontsize=8, loc="best"); ax.grid(alpha=0.3)
ax2.plot(fi, res, color="tab:red"); ax2.axhline(0, color="k", lw=0.5); ax2.grid(alpha=0.3)
ax2.set_ylabel("residual [px]"); ax2.set_xlabel("original frame index (even frames)")
fig.suptitle(f"{BODY12[j]} {args.axis}(t): GT, YOLO, interpolation, T-GCT, HybrIK")      # clip is in the file name
fig.tight_layout()
out = Path(args.out) if args.out else Path("phase2/results") / f"fig_tgct_{args.clip}_{BODY12[j]}_{args.axis}.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=150); print("saved", out)
plt.close(fig)