"""HybrIK 6-struct answer sheets: res.pk (1080p clip) -> body-12 normalised coords on ORIGINAL even frames.
Run in the `hybrik` env (res.pk pickled by numpy 1.23):
  python phase2/scripts/make_hybrik_sheet.py --clip P9201256 \
      --res outputs/20261018/P9201256_tackle01/hybrik/res.pk --offset outputs/20261018/P9201256_tackle01/offset.txt \
      --verified ~/data/phase2_npz/win3162/yolo_raw_P9201256_tackler_verified.npz --out-dir ~/data/phase2_npz/win3162
Writes hybrik_struct_<clip>.npz (all even window frames), hybrik_struct_ok_<clip>.npz (coords NaN where not person_ok)
and hybrik_interp_<clip>.npz (not-ok frames bridged by phase2.temporal.interpolate_gaps).
The verified bbox uses normalised (cx, cy, w, h), as checked in step 3-2a.
Coords are normalised by the 1080p clip size, which equals normalisation by the 4K original (exact 2x downscale);
the W/H keys carry the ORIGINAL size so that pck.py scales the sheet onto the same pixel ruler as the GT."""
import argparse, pickle, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))            # repo root -> `import phase2`
from phase2.temporal import interpolate_gaps

DEPTH_FACTOR, F_CROP, INP = 2.2, 1000.0, 256.0
SMPL_TO_BODY12 = [16, 17, 18, 19, 20, 21, 1, 2, 4, 5, 7, 8]            # SMPL-24 order (NOT pred_xyz_17 / H36M)
BODY12 = ["L_sho", "R_sho", "L_elb", "R_elb", "L_wri", "R_wri", "L_hip", "R_hip", "L_kne", "R_kne", "L_ank", "R_ank"]

def project_cam_to_pixels(X_abs, bbox, W, H):
    """B1 worksheet ex. f: pinhole, principal point = image centre, f_img = 1000 * crop_width / 256. X_abs (N,J,3) metres."""
    X_abs = np.asarray(X_abs, float)
    bbox = np.asarray(bbox, float)
    if np.any(X_abs[..., 2] <= 0):
        raise ValueError("All Z coordinates must be positive")
    f_img = F_CROP * (bbox[:, 2] - bbox[:, 0]) / INP
    x = W / 2.0 + f_img[:, None] * X_abs[..., 0] / X_abs[..., 2]
    y = H / 2.0 + f_img[:, None] * X_abs[..., 1] / X_abs[..., 2]
    return np.stack([x, y], axis=-1)

def read_offset(path):
    """offset.txt (key=value lines) -> dict of strings."""
    kv = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", required=True)
    ap.add_argument("--res", required=True)
    ap.add_argument("--offset", required=True)
    ap.add_argument("--verified", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    
    with open(args.res, "rb") as f:
        res = pickle.load(f)
    bbox = np.asarray(res["bbox"], float)
    N = len(bbox)
    W, H = int(res["width"][0]), int(res["height"][0])  #1920, 1080 (clip)
    X = np.asarray(res["pred_xyz_24_struct"], float) * DEPTH_FACTOR + np.asarray(res["transl"], float)[:, None, :]
    P = project_cam_to_pixels(X, bbox, W, H)[:, SMPL_TO_BODY12] / np.array([W, H]) # (N, 12, 2) normalized pixel coordinates
    S = np.asarray(res["pred_scores"], float)[:, SMPL_TO_BODY12] # (N, 12) scores for the selected joints
    
    #: clip index i (0-based, order of res["img_path"]) -> original 1-based frame.
    off = int(read_offset(args.offset)["first_orig_0based"])
    orig = np.arange(N) + 1 + off   #(shape (N,))

    #: keep even original frames inside the verified window.
    with np.load(args.verified, allow_pickle=True) as archive:
        v = {key: archive[key] for key in ("frame_index", "bbox", "identity_verdict", "W", "H")}
    vf = v["frame_index"].astype(int)
    if vf.ndim != 1 or vf.size == 0 or np.any(np.diff(vf) <= 0):
        raise ValueError("Verified frame_index must be non-empty and strictly increasing")
    lo, hi = vf.min(), vf.max()
    keep = (orig % 2 == 0) & (orig >= lo) & (orig <= hi);  idx = np.where(keep)[0];  frames = orig[idx]
    expected = np.arange(lo + lo % 2, hi + 1, 2)
    if frames.size == 0 or not np.array_equal(frames, expected) or not np.isin(frames, vf).all():
        raise ValueError("HybrIK frames must fully cover the verified window's even frames")

    #: person_ok = HybrIK crop centre inside the verified tackler bbox of the same frame; False where that bbox is all zero.
    vrow = np.searchsorted(vf, frames)            # rows of the verified sheet for our frames (vf is sorted, consecutive)
    vb = v["bbox"][vrow].astype(float); verdict = v["identity_verdict"][vrow]
    cx = (bbox[idx, 0] + bbox[idx, 2]) / 2 / W;  cy = (bbox[idx, 1] + bbox[idx, 3]) / 2 / H
    # Step 3-2a confirmed normalised (cx,cy,w,h); both bbox formats have four columns.
    inside = (np.abs(cx - vb[:, 0]) <= vb[:, 2] / 2) & (np.abs(cy - vb[:, 1]) <= vb[:, 3] / 2)
    person_ok = inside & (vb != 0).any(1)
    if not person_ok.any():
        raise ValueError("Cannot interpolate: no person_ok frames in the verified window")

    #4: the three coordinate sets (all normalised).
    coords = P[idx]; confs = S[idx]
    coords_ok = coords.copy(); coords_ok[~person_ok] = np.nan
    coords_interp = coords.copy()
    for j in range(12):
        for a in range(2): 
            coords_interp[:, j, a] = interpolate_gaps(coords[:, j, a], person_ok)

    #: save. Common keys for all three sheets:
    common = dict(frame_index=frames, confs=confs, person_ok=person_ok, identity_verdict=verdict,
                  joint_names=np.array(BODY12), W=int(v["W"]), H=int(v["H"]), norm_size=np.array([W, H]),
                  clip=args.clip, person="tackler", first_orig_0based=off, res_pk=str(args.res),
                  crop_centre=np.stack([cx, cy], 1))
    out = Path(args.out_dir).expanduser(); out.mkdir(parents=True, exist_ok=True)
    np.savez(out / f"hybrik_struct_{args.clip}.npz",    coords=coords,        source="hybrik_struct",    **common)
    np.savez(out / f"hybrik_struct_ok_{args.clip}.npz", coords=coords_ok,     source="hybrik_struct_ok", **common)
    np.savez(out / f"hybrik_interp_{args.clip}.npz",    coords=coords_interp, source="hybrik_interp",    **common)
    print("n frames", len(frames), "range", f"{frames[0]}..{frames[-1]}", "person_ok", int(person_ok.sum()))
    for vd in ("ok", "swap", "fused", "no_valid"): m = verdict == vd; print(vd, int(m.sum()), "person_ok", int((m & person_ok).sum()))
    
    
if __name__ == "__main__":
    main()
    
