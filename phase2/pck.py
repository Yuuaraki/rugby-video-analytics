"""Scoring harness shared by every contestant (worksheet phase2C appendix A). `metrics.py` is untouched.
Scores on the GT's even frames, in pixels, normalised by the GT torso length. Run in `rugby` from ~/rugby-video-analytics:
   python phase2/pck.py <gt.npz> <clip> <name>=<sheet.npz> [<name>=<sheet.npz> ...] [--alphas 0.10 0.20] [--out phase2/results]
"""
import argparse, csv, warnings, numpy as np
from pathlib import Path

BODY12 = ["L_sho", "R_sho", "L_elb", "R_elb", "L_wri", "R_wri", "L_hip", "R_hip", "L_kne", "R_kne", "L_ank", "R_ank"]
COCO_BODY12 = list(range(5, 17))
GROUPS = {"sho": [0, 1], "elb": [2, 3], "wri": [4, 5], "hip": [6, 7], "kne": [8, 9], "ank": [10, 11]}
PHASES = {"P9201256": [("pre", -np.inf, 3226), ("contact", 3228, 3280), ("fusion", 3282, 3356), ("fall", 3358, np.inf)],
          "PA041271": [("pre", -np.inf, 4488), ("contact", 4490, 4494), ("hold", 4496, 4512), ("post", 4514, np.inf)]}   # provisional (annotation chat 10/17: first touch 4490, single detection 4496-4512)

def load_gt(path):
    """GT .npz (coords normalised, vis, frame_index, W, H) -> dict(coords px (N,12,2), vis (N,12) int, frames (N,))."""
    with np.load(path) as z:
        c = z["coords"].astype(float)
        vis = z["vis"].astype(int)
        frames = z["frame_index"].astype(int)
        W, H = float(z["W"]), float(z["H"])
    if c.ndim != 3 or c.shape[1:] != (12, 2):
        raise ValueError(f"GT coords must have shape (N, 12, 2), got {c.shape}")
    if vis.shape != c.shape[:2] or frames.shape != (len(c),):
        raise ValueError("GT vis and frame_index must align with coords")
    if not np.isfinite([W, H]).all() or W <= 0 or H <= 0:
        raise ValueError(f"GT image dimensions must be finite and positive, got W={W}, H={H}")
    c *= np.array([W, H])
    bad = ~np.isfinite(c).all(-1) & (vis < 2)
    if bad.any():
        warnings.warn(f"{int(bad.sum())} NaN joints with vis<2 in {path}: excluded (treated as vis=2)")
        vis[bad] = 2
    return dict(coords=c, vis=vis, frames=frames)
    
def load_sheet(path):
    """Any answer sheet -> body-12 coords in px (N,12,2) + frames (N,). Accepts K=17 (COCO), K=12 (BODY12 order) or joint_names."""
    with np.load(path, allow_pickle=True) as z:
        c = z["coords"].astype(float)
        frames = z["frame_index"].astype(int)
        names = [
            n.decode("utf-8") if isinstance(n, bytes) else str(n)
            for n in z["joint_names"]
        ] if "joint_names" in z.files else None
        W = float(z["W"]) if "W" in z.files else 3840.0
        H = float(z["H"]) if "H" in z.files else 2160.0
    if c.ndim != 3 or c.shape[-1] != 2:
        raise ValueError(f"Sheet coords must have shape (N, K, 2), got {c.shape}")
    if frames.shape != (len(c),):
        raise ValueError("Sheet frame_index must align with coords")
    if not np.isfinite([W, H]).all() or W <= 0 or H <= 0:
        raise ValueError(f"Sheet image dimensions must be finite and positive, got W={W}, H={H}")

    if names is not None:
        if len(names) != c.shape[1]:
            raise ValueError("Sheet joint_names length must match coords")
        missing = [name for name in BODY12 if name not in names]
        if missing:
            if c.shape[1] == 17:
                c = c[:, COCO_BODY12, :]
            else:
                raise ValueError(f"Sheet joint_names are missing required joints: {', '.join(missing)}")
        else:
            c = c[:, [names.index(name) for name in BODY12], :]
    elif c.shape[1] == 17:
        c = c[:, COCO_BODY12, :]
    elif c.shape[1] != 12:
        raise ValueError("Sheet must contain 12 BODY12 joints, 17 COCO joints, or joint_names")

    finite = c[np.isfinite(c)]
    if finite.size and np.max(finite) <= 1.5:
        c = c * np.array([W, H])
    return dict(coords=c, frames=frames)
    
def align(gt, sheet):
    """Pick the sheet rows whose frame_index matches the GT frames -> pred (N,12,2); GT frames missing from the sheet -> NaN."""
    frames = np.asarray(sheet["frames"])
    coords = np.asarray(sheet["coords"])
    if frames.ndim != 1 or coords.shape != (len(frames), 12, 2):
        raise ValueError("Sheet frames and BODY12 coordinates must have matching (N,) and (N, 12, 2) shapes")
    if len(np.unique(frames)) != len(frames):
        raise ValueError("Sheet frame_index contains duplicates")
    pos = {int(f): i for i, f in enumerate(frames)}
    pred = np.full(gt["coords"].shape, np.nan)
    for i, f in enumerate(gt["frames"]):
        if int(f) in pos:
            pred[i] = coords[pos[int(f)]]
    missing = int(np.isnan(pred[:, 0, 0]).sum())
    if missing:
        warnings.warn(f"{missing} GT frames missing from the sheet")
    return pred

PER_FRAME = False          # module default; main() sets it from --per-frame (appendix sensitivity check only)


def torso_length(gt, per_frame=None):
    """s_t (N,) px. Default (per_frame=False): per-clip L_ref = median |mid(shoulders) - mid(hips)| over frames whose
    four torso joints are vis<2 and finite, broadcast to every frame (pre-registered 2026-10-17; HQ 2026-10-19).
    per_frame=True: each frame's own length, frames with a torso joint vis==2 -> clip median (behaviour before
    2026-10-19, kept for the appendix sensitivity table)."""
    if per_frame is None:
        per_frame = PER_FRAME
    c, vis = gt["coords"], gt["vis"]
    s = np.linalg.norm(c[:, [0, 1]].mean(1) - c[:, [6, 7]].mean(1), axis=-1)
    ok = (vis[:, [0, 1, 6, 7]] < 2).all(1) & np.isfinite(s)
    if not ok.any():
        raise ValueError("Cannot compute torso length: no frame has all four shoulder/hip joints in-frame")
    median = np.median(s[ok])
    if not np.isfinite(median) or median <= 0:
        raise ValueError(f"Median GT torso length must be finite and positive, got {median}")
    if not per_frame:
        return np.full_like(s, median)
    s[~ok] = median
    return s

def pck_matrix(pred, gt, alpha):
    """-> correct (N,12) bool, scored (N,12) bool, dist (N,12) px. Scored = vis<2 and the prediction exists (a (0,0) miss counts as wrong)."""
    s = torso_length(gt)
    dist = np.linalg.norm(pred - gt["coords"], axis=-1)
    scored = (gt["vis"] < 2) & np.isfinite(dist)
    correct = scored & (dist <= alpha * s[:, None])
    return correct, scored, dist

def subsets(gt, clip):
    """Named (N,12) bool masks: all / vis0 / vis1 / each phase / each joint group."""
    N, K = gt["vis"].shape
    out = {"all": np.ones((N,K), bool), "vis0": gt["vis"] == 0, "vis1": gt["vis"] == 1}
    for name, lo, hi in PHASES.get(clip, []):
        in_phase = (gt["frames"] >= lo) & (gt["frames"] <= hi)
        out[name] = np.broadcast_to(in_phase[:, None], (N, K))
    for g, idx in GROUPS.items():
        m = np.zeros((N, K), bool)
        m[:, idx] = True
        out[g] = m
    return out

def score(pred, gt, clip, alphas=(0.10, 0.20)):
    """-> list of rows dict(subset, n, pck@a...) for one sheet."""
    rows = []
    mats = {a: pck_matrix(pred, gt, a) for a in alphas}
    for name, m in subsets(gt, clip).items():
        row = {"subset": name}
        for a in alphas:
            correct, scored, _ = mats[a]
            sc = scored & m
            row["n"] = int(sc.sum())
            row[f"pck@{a:.2f}"] = float((correct & sc).sum() / max(1, sc.sum()))
        rows.append(row)
    return rows

def offsets(pred, gt, clean=None, max_rel=0.5):
    """Per joint on CLEAN vis==0 joint-frames: mean offset vector (systematic) and std per axis (scatter), px.
    clean: (N,) bool frame mask (default: all frames). (0,0) misses and dist > max_rel * s_t (identity errors) are dropped."""
    rows = []
    s = torso_length(gt)
    dist = np.linalg.norm(pred - gt["coords"], axis=-1)
    present = ~(pred == 0).all(-1)
    frame_ok = np.ones(len(pred), bool) if clean is None else np.asarray(clean, bool)
    for k, name in enumerate(BODY12):
        vis0 = gt["vis"][:, k] == 0
        ok = vis0 & np.isfinite(pred[:, k]).all(-1) & present[:, k] & frame_ok & (dist[:, k] <= max_rel * s)
        d = pred[ok, k] - gt["coords"][ok, k]
        if len(d):
            mean_dx, mean_dy = d.mean(axis=0)
            std_dx, std_dy = d.std(axis=0)
            mean_dist = np.linalg.norm(d, axis=-1).mean()
        else:
            mean_dx = mean_dy = std_dx = std_dy = mean_dist = float("nan")
        rows.append(dict(joint=name, n=int(vis0.sum()), n_used=int(ok.sum()), mean_dx=mean_dx, mean_dy=mean_dy,
                         std_dx=std_dx, std_dy=std_dy, mean_dist=mean_dist))
    return rows


def bias_correct(pred, gt, clean):
    """Within-clip calibration (secondary metric): subtract each joint's mean offset, estimated by offsets() on CLEAN
    vis==0 joint-frames (same estimator and outlier rule as the offset tables), from every frame of the sheet.
    Joints with no usable clean sample keep bias 0. -> pred_bc (N,12,2), bias (12,2) px."""
    rows = offsets(pred, gt, clean if clean.any() else None)
    bias = np.nan_to_num(np.array([[r["mean_dx"], r["mean_dy"]] for r in rows], float))
    return pred - bias[None], bias

def main():
    global PER_FRAME
    ap = argparse.ArgumentParser()
    ap.add_argument("gt")
    ap.add_argument("clip")
    ap.add_argument("sheets", nargs="+", help="name=path.npz")
    ap.add_argument("--alphas", type=float, nargs="+", default=[0.10, 0.20])
    ap.add_argument("--out", default="phase2/results")
    ap.add_argument("--bias-correct", choices=["clean"], default=None,
                    help="also score pred - per-joint mean offset estimated on clean (pre+post) vis=0 joint-frames")
    ap.add_argument("--per-frame", action="store_true",
                    help="normalise by each frame's own torso length (appendix sensitivity); default = per-clip L_ref")
    args = ap.parse_args()
    PER_FRAME = args.per_frame
    if any(not np.isfinite(a) or a < 0 for a in args.alphas):
        ap.error("--alphas values must be finite and nonnegative")
    gt = load_gt(Path(args.gt).expanduser())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    s = torso_length(gt)
    print(f"{args.clip}: {len(gt['frames'])} GT frames, "
          f"{'per-frame torso median' if args.per_frame else 'L_ref'} {np.median(s):.0f} px "
          f"(alpha 0.10 -> {0.10 * np.median(s):.0f} px)")
    all_rows, md = [], [f"| condition | subset | n | " + " | ".join(f"PCK@{a:.2f}" for a in args.alphas) + " |", "|---" * (3 + len(args.alphas)) + "|"]
    bc_rows, md_bc = [], list(md)                                              # same header, bias-corrected rows
    for spec in args.sheets:
        name, path = spec.split("=", 1)
        if not name or not path:
            ap.error("each sheet must be specified as a nonempty name=path.npz")
        pred = align(gt, load_sheet(Path(path).expanduser()))
        for r in score(pred, gt, args.clip, tuple(args.alphas)):
            all_rows.append({"condition": name, **r})
            md.append(f"| {name} | {r['subset']} | {r['n']} | " + " | ".join(f"{r[f'pck@{a:.2f}']:.3f}" for a in args.alphas) + " |")
        clean = np.zeros(len(gt["frames"]), bool)
        for ph, lo, hi in PHASES.get(args.clip, []):
            if ph in ("pre", "fall", "post"):                                   # clean segments: no fusion, no identity ambiguity
                clean |= (gt["frames"] >= lo) & (gt["frames"] <= hi)
        with open(out / f"offset_{args.clip}_{name}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["joint", "n", "n_used", "mean_dx", "mean_dy", "std_dx", "std_dy", "mean_dist"]); w.writeheader()
            w.writerows(offsets(pred, gt, clean if clean.any() else None))
        if args.bias_correct == "clean":
            calib = np.zeros(len(gt["frames"]), bool)
            for ph, lo, hi in PHASES.get(args.clip, []):
                if ph in ("pre", "fall", "post"):                                       # plan 1018 §3: pre+post only
                    calib |= (gt["frames"] >= lo) & (gt["frames"] <= hi)
            pred_bc, bias = bias_correct(pred, gt, calib)
            n_used = np.array([r["n_used"] for r in offsets(pred, gt, calib if calib.any() else None)])
            np.savetxt(out / f"bias_{args.clip}_{name}.csv", np.column_stack([bias, n_used]), delimiter=",", fmt="%.2f",
                       header=f"dx,dy px per BODY12 joint (pred - gt), n_used; calibration = {int(calib.sum())} GT frames (pre+fall|post, vis0); 0 = no sample", comments="# ")
            print(f"[bias] {name}: calibration {int(calib.sum())} GT frames, n_used per joint {n_used.min()}-{n_used.max()}")
            for r in score(pred_bc, gt, args.clip, tuple(args.alphas)):
                bc_rows.append({"condition": name, **r})
                md_bc.append(f"| {name} | {r['subset']} | {r['n']} | " + " | ".join(f"{r[f'pck@{a:.2f}']:.3f}" for a in args.alphas) + " |")
    with open(out / f"pck_{args.clip}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys())); w.writeheader(); w.writerows(all_rows)
    (out / f"pck_{args.clip}.md").write_text("\n".join(md) + "\n"); print("\n".join(md))
    if args.bias_correct:
        with open(out / f"pck_{args.clip}_bc.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(bc_rows[0].keys())); w.writeheader(); w.writerows(bc_rows)
        (out / f"pck_{args.clip}_bc.md").write_text("\n".join(md_bc) + "\n"); print("\n[bias-corrected (within-clip calibration, pre+post vis0)]"); print("\n".join(md_bc))

if __name__ == "__main__":
    main()