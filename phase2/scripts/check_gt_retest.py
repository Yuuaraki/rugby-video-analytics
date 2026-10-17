"""Re-annotation variability in pixels and GT torso-length units.

Ratios exclude frames with missing or zero-length GT torsos; pixel reports
still include their comparable joints.
"""
import argparse

import numpy as np

JOINTS = ["L_sho", "R_sho", "L_elb", "R_elb", "L_wri", "R_wri",
          "L_hip", "R_hip", "L_kne", "R_kne", "L_ank", "R_ank"]
TORSO = [0, 1, 6, 7]  # shoulders and hips


def select(npz, frames):
    """Rows of npz whose frame_index equals the given frames, in that order."""
    index = npz["frame_index"]
    if index.ndim != 1 or not np.issubdtype(index.dtype, np.integer):
        raise ValueError("frame_index must be a one-dimensional integer array")
    if (index[1:] <= index[:-1]).any():
        raise ValueError("frame_index must be sorted and contain no duplicates")
    rows = np.searchsorted(index, frames)
    found = rows < len(index)
    found[found] = index[rows[found]] == frames[found]
    if not found.all():
        raise ValueError(f"frames not found: {frames[~found].tolist()}")
    return rows


def pixel_dist(a, b, W, H):
    """Distance in pixels between normalized coords a and b, shape (..., 2) -> (...)."""
    d = np.linalg.norm((a - b) * np.array([W, H], dtype=float), axis=-1)
    return d


def torso_length_px(xy, W, H):
    """Per-frame distance between mid-shoulder and mid-hip in px; xy is (T, 12, 2) normalized."""
    mid_sho = xy[:, [0, 1]].mean(axis=1)
    mid_hip = xy[:, [6, 7]].mean(axis=1)
    L = pixel_dist(mid_sho, mid_hip, W, H)
    return L


def report(name, d, mask):
    v = d[mask]
    if v.size == 0:
        print(f"{name:12s}: n=  0")
        return
    print(f"{name:12s}: n={v.size:3d} median {np.median(v):6.1f} px  "
          f"p90 {np.percentile(v, 90):6.1f} px  max {v.max():6.1f} px")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--retest", required=True)
    ap.add_argument("--frames", required=True, help="comma-separated original frame numbers")
    ap.add_argument("--ref-length", action="store_true",
                    help="also report self-PCK normalised by the clip reference torso length")
    args = ap.parse_args()
    try:
        frames = np.array([int(f) for f in args.frames.split(",")])
    except ValueError:
        ap.error("--frames must be comma-separated integers")
    if len(np.unique(frames)) != len(frames):
        ap.error("--frames must not contain duplicates")

    with np.load(args.gt) as g, np.load(args.retest) as r:
        W, H = float(g["W"]), float(g["H"])
        if not np.isfinite([W, H]).all() or W <= 0 or H <= 0:
            raise ValueError("GT image dimensions must be finite and positive")
        if (float(r["W"]), float(r["H"])) != (W, H):
            raise ValueError("GT and retest image dimensions must match")
        gi, ri = select(g, frames), select(r, frames)
        for name, sheet in (("GT", g), ("retest", r)):
            if sheet["coords"].shape != (len(sheet["frame_index"]), len(JOINTS), 2):
                raise ValueError(f"{name}: coords must have shape (T, 12, 2)")
            if sheet["vis"].shape != sheet["coords"].shape[:2]:
                raise ValueError(f"{name}: vis must have shape (T, 12)")
        g_xy, g_vis = g["coords"][gi], g["vis"][gi]
        r_xy, r_vis = r["coords"][ri], r["vis"][ri]
        g_all_xy, g_all_vis = g["coords"], g["vis"]

    for name, xy, vis in (("GT", g_xy, g_vis), ("retest", r_xy, r_vis)):
        if not np.isin(vis, [0, 1, 2]).all():
            raise ValueError(f"{name}: vis must be 0, 1, or 2")
        if not np.isfinite(xy[vis != 2]).all():
            raise ValueError(f"{name}: joints with vis != 2 must have finite coordinates")
        xy[vis == 2] = np.nan

    diff = g_vis != r_vis
    print("vis agreement:", int((~diff).sum()), "of", diff.size)
    for t, j in zip(*np.where(diff)):
        print(f"  frame {frames[t]} {JOINTS[j]}: original vis={g_vis[t, j]} retest vis={r_vis[t, j]}")

    d = pixel_dist(g_xy, r_xy, W, H)  # (T, 12); NaN where either side is Outside
    both = (g_vis != 2) & (r_vis != 2)
    vis0 = both & (g_vis == 0)
    vis1 = both & (g_vis == 1)
    tor = np.zeros_like(both)
    tor[:, TORSO] = True

    L = torso_length_px(g_xy, W, H)  # (T,)
    print("torso length [px] per frame:", np.round(L, 1))
    valid_torso = np.isfinite(L) & (L > 0)
    if not valid_torso.all():
        print("WARNING: invalid GT torso length; excluded from ratios for frames:",
              frames[~valid_torso].tolist())
    ratio = np.full_like(d, np.nan)
    np.divide(d, L[:, None], out=ratio, where=valid_torso[:, None])

    print("--- by vis (original) ---")
    report("vis0 all", d, vis0)
    report("vis1 all", d, vis1)
    print("--- torso (sho, hip) vs limbs ---")
    report("vis0 torso", d, vis0 & tor)
    report("vis0 limbs", d, vis0 & ~tor)
    report("vis1 torso", d, vis1 & tor)
    report("vis1 limbs", d, vis1 & ~tor)
    print("--- in torso-length units (PCK@0.10 counts a joint correct at or below 0.10) ---")
    for name, m in (("vis0", vis0), ("vis1", vis1)):
        v = ratio[m & valid_torso[:, None]]
        if v.size == 0:
            print(f"{name}: n=  0")
            continue
        print(f"{name}: n={v.size:3d} median {np.median(v):.3f}  p90 {np.percentile(v, 90):.3f}")
        print(f"      self-PCK@0.10 {np.mean(v <= 0.10):.2f}   self-PCK@0.20 {np.mean(v <= 0.20):.2f}") 
    print("--- per joint (all vis) ---")
    if args.ref_length:
        n_strict = int((g_all_vis[:, TORSO] == 0).all(axis=1).sum())
        torso_ok = (g_all_vis[:, TORSO] != 2).all(axis=1)
        L_ref = float(np.median(torso_length_px(g_all_xy, W, H)[torso_ok]))
        print(f"--- clip reference L_ref = {L_ref:.1f} px (median over n={int(torso_ok.sum())} frames "
              f"with all 4 torso joints vis!=2; strict vis=0 definition gives n={n_strict}) ---")
        for name, m in (("vis0", vis0), ("vis1", vis1)):
            v = d[m] / L_ref
            print(f"{name}: median {np.median(v):.3f}  p90 {np.percentile(v, 90):.3f}  "
                  f"self-PCK@0.10 {np.mean(v <= 0.10):.2f}   self-PCK@0.20 {np.mean(v <= 0.20):.2f}")
    for j, name in enumerate(JOINTS):
        m = both[:, j]
        if m.any():
            print(f"{name}: n={int(m.sum())} median {np.median(d[m, j]):6.1f} px")


if __name__ == "__main__":
    main()