"""Figure 3 (HQ fix 3, 2026-10-18 evening): 2x2 overlay. Top = one SUCCESS frame from P9201256 fusion (even GT frames
3282-3356) chosen by max(#HybrIK correct - #interp correct @0.20; tie -> a wrist correct by HybrIK only):
left YOLO-verified+interp (green), right HybrIK 6-struct (magenta), GT as white hollow circles on both.
Bottom = failures: P9201256 3250 (contact, L0) and PA041271 4500 (hold, L1). Scores from phase2.pck. Run in `rugby`.
  python phase2/scripts/fig3_hybrik_2x2.py --out phase2/results/final_v3/overlay/fig3_hybrik_2x2.png [--frame 3xxx]"""
import argparse, sys
from pathlib import Path
import cv2, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from phase2.pck import load_gt, load_sheet, align, pck_matrix

NPZ, GT, OUT = Path.home() / "data/phase2_npz", Path.home() / "data/phase2_gt", Path("outputs/20261018")
CLIPS = {"P9201256": dict(gt=GT / "gt_P9201256_tackler.npz", d=NPZ / "win3162", tag="tackle01"),
         "PA041271": dict(gt=GT / "gt_PA041271_win4358_tackler.npz", d=NPZ / "win4358", tag="tackle05")}
EDGES12 = [(0, 2), (2, 4), (1, 3), (3, 5), (6, 8), (8, 10), (7, 9), (9, 11), (0, 1), (6, 7), (0, 6), (1, 7)]
SCALE = np.array([1920, 1080]) / np.array([3840, 2160])      # pck px (4K) -> clip px (1080p)


def load_clip(clip):
    c = CLIPS[clip]; gt = load_gt(c["gt"])
    sheets = {n: align(gt, load_sheet(c["d"] / f"{n}_{clip}.npz")) for n in ("interp", "hybrik_struct")}   # (N,12,2) 4K px
    first = int(np.load(c["d"] / f"hybrik_struct_{clip}.npz")["first_orig_0based"])
    return gt, sheets, first


def per_frame(pred, gt, alpha=0.20):
    correct, scored, _ = pck_matrix(pred, gt, alpha)
    return correct.sum(1), scored.sum(1), correct            # n correct per frame, n scored per frame, (N,12) bool


def pick_frame(gt, sheets, lo=3282, hi=3356):
    frames = gt["frames"]; band = np.where((frames >= lo) & (frames <= hi))[0]
    ch, sh, cmh = per_frame(sheets["hybrik_struct"], gt); ci, si, cmi = per_frame(sheets["interp"], gt)
    diff = ch - ci; wrist_h_only = (cmh[:, [4, 5]] & ~cmi[:, [4, 5]]).any(1)
    print("frame hybrik_correct hybrik_scored interp_correct interp_scored diff wrist_hybrik_only")
    for r in band:
        print(frames[r], ch[r], sh[r], ci[r], si[r], diff[r], wrist_h_only[r])
    best = max(band, key=lambda r: (diff[r], wrist_h_only[r], -frames[r]));  return int(frames[best])


def img_for(clip, frame, first):
    stem = f"{clip}_{CLIPS[clip]['tag']}"; i = frame - 1 - first
    img = cv2.imread(str(OUT / stem / "hybrik" / "raw_images" / f"{stem}_1080p-{i + 1:06d}.png")); assert img is not None, frame
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def panel(ax, img, gt_px, pred_px, color, title, margin=0.35):
    ax.imshow(img)
    for a, b in EDGES12:
        if np.isfinite(pred_px[[a, b]]).all():
            ax.plot([pred_px[a,0], pred_px[b,0]], [pred_px[a,1], pred_px[b,1]], color=color, lw=2)
    ax.scatter(pred_px[:,0], pred_px[:,1], c=color, s=25, zorder=3)
    g = gt_px[np.isfinite(gt_px).all(1)]; ax.scatter(g[:,0], g[:,1], facecolors="none", edgecolors="w", s=60, linewidths=1.5, zorder=4)
    # crop around g: x0,y0 = g.min(0) - margin*(g.max(0)-g.min(0)); x1,y1 = g.max(0) + margin*(...); clip to [0,W]x[0,H]
    x0,y0 = g.min(0) - margin*(g.max(0)-g.min(0)); x1,y1 = g.max(0) + margin*(g.max(0)-g.min(0))
    H, W = img.shape[:2]; x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_title(title, fontsize=9); ax.axis("off")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--frame", type=int, default=None)
    args = ap.parse_args()
    g1, s1, f1 = load_clip("P9201256"); g2, s2, f2 = load_clip("PA041271")
    f_ok = args.frame or pick_frame(g1, s1)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    def row(gt, frame):
        hit = np.where(gt["frames"] == frame)[0]; assert len(hit) == 1, f"frame {frame} is not a GT frame"
        return int(hit[0])

    def counts(gt, sheets, r):
        (ci, si, _), (ch, sh, _) = per_frame(sheets["interp"], gt), per_frame(sheets["hybrik_struct"], gt)
        return int(ci[r]), int(si[r]), int(ch[r]), int(sh[r])

    r = row(g1, f_ok); ci, si, ch, sh = counts(g1, s1, r); img = img_for("P9201256", f_ok, f1); gt_px = g1["coords"][r] * SCALE
    panel(axes[0,0], img, gt_px, s1["interp"][r]*SCALE, "lime", f"P9201256 f{f_ok} fusion — YOLO-verified + interp: {ci}/{si} correct @0.20")
    panel(axes[0,1], img, gt_px, s1["hybrik_struct"][r]*SCALE, "magenta", f"P9201256 f{f_ok} fusion — HybrIK 6-struct: {ch}/{sh} correct @0.20")
    r = row(g1, 3250); _, _, ch, sh = counts(g1, s1, r)
    panel(axes[1,0], img_for("P9201256", 3250, f1), g1["coords"][r]*SCALE, s1["hybrik_struct"][r]*SCALE, "magenta",
          f"P9201256 f3250 contact — HybrIK {ch}/{sh}: L0, crop on the carrier")
    r = row(g2, 4500); _, _, ch, sh = counts(g2, s2, r)
    panel(axes[1,1], img_for("PA041271", 4500, f2), g2["coords"][r]*SCALE, s2["hybrik_struct"][r]*SCALE, "magenta",
          f"PA041271 f4500 hold — HybrIK {ch}/{sh}: L1, person_ok=True but carrier reconstructed")
    fig.tight_layout(); Path(args.out).parent.mkdir(parents=True, exist_ok=True); fig.savefig(args.out, dpi=150)
    print("saved", args.out, "| success frame", f_ok)


if __name__ == "__main__":
    main()