"""Overlay check for the HybrIK 6-struct sheets (plan 1018 §1.2): draws, on the clip's raw_images PNG,
struct body-12 (magenta, from the sheet), raw heatmap body-12 (green, projected from pred_xyz_29 + pred_cam_root, B1 f1),
the HybrIK crop bbox (blue) and the verified tackler bbox (yellow). Run in the `hybrik` env.
  python phase2/scripts/hybrik_overlay.py --clip P9201256 --res <res.pk> --sheet <hybrik_struct_<clip>.npz> \
      --verified <verified.npz> --frames 3200 3230 3250 --out-dir phase2/results/final_v3/overlay"""
import argparse, pickle, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from phase2.scripts.make_hybrik_sheet import project_cam_to_pixels, SMPL_TO_BODY12, DEPTH_FACTOR

HYBRIK_ROOT = Path.home() / "HybrIK"                                     # res["img_path"] is relative to this
EDGES12 = [(0, 2), (2, 4), (1, 3), (3, 5), (6, 8), (8, 10), (7, 9), (9, 11), (0, 1), (6, 7), (0, 6), (1, 7)]

def draw_pose(img, pts12, color):
    for a, b in EDGES12:
        cv2.line(img, tuple(np.rint(pts12[a]).astype(int)), tuple(np.rint(pts12[b]).astype(int)), color, 2)
    for x, y in pts12:
        cv2.circle(img, (int(round(x)), int(round(y))), 4, color, -1)
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", required=True)
    ap.add_argument("--res", required=True)
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--verified", required=True)
    ap.add_argument("--frames", type=int, nargs="+", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    with open(Path(args.res).expanduser(), "rb") as f:
        res = pickle.load(f)
    with np.load(Path(args.sheet).expanduser(), allow_pickle=True) as archive:
        z = {key: archive[key] for key in ("coords", "frame_index", "person_ok", "first_orig_0based")}
    with np.load(Path(args.verified).expanduser(), allow_pickle=True) as archive:
        v = {key: archive[key] for key in ("bbox", "frame_index")}
    W, H = int(res["width"][0]), int(res["height"][0])
    off = int(z["first_orig_0based"])
    bbox = np.asarray(res["bbox"], float)
    # TODO 1: raw heatmap joints in 1080p px (B1 f1).
    X_raw = np.asarray(res["pred_xyz_29"], float) * DEPTH_FACTOR + np.asarray(res["pred_cam_root"], float)[:, None, :]
    raw_px = project_cam_to_pixels(X_raw, bbox, W, H)[:, SMPL_TO_BODY12]
    out = Path(args.out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    # TODO 2: overlay each requested original frame on its clip image.
    for f in args.frames:
        i = f - 1 - off                               # clip index
        if not 0 <= i < len(bbox) or i >= len(res["img_path"]):
            raise ValueError(f"Frame {f} maps outside the HybrIK clip (index {i})")
        srow = np.flatnonzero(z["frame_index"] == f)
        vrow = np.flatnonzero(v["frame_index"] == f)
        if len(srow) != 1 or len(vrow) != 1:
            raise ValueError(f"Frame {f} must occur exactly once in both the struct and verified sheets")
        struct_px = z["coords"][srow[0]] * [W, H]      # sheet is normalised -> clip px
        vb = np.asarray(v["bbox"][vrow[0]], float)     # (cx,cy,w,h) normalised
        if struct_px.shape != (12, 2) or not np.isfinite(struct_px).all() or not np.isfinite(raw_px[i]).all():
            raise ValueError(f"Frame {f} requires finite raw and struct body-12 coordinates; use the unmasked struct sheet")
        if vb.shape != (4,) or not np.isfinite(vb).all() or not np.isfinite(bbox[i]).all():
            raise ValueError(f"Frame {f} requires finite four-element bounding boxes")
        img_path = HYBRIK_ROOT / res["img_path"][i]
        img = cv2.imread(str(img_path))
        if img is None:
            raise FileNotFoundError(f"Could not read frame {f} image: {img_path}")
        if img.shape[:2] != (H, W):
            raise ValueError(f"Frame {f} image size {img.shape[:2]} differs from res.pk {(H, W)}")

        draw_pose(img, raw_px[i], (0, 255, 0))
        draw_pose(img, struct_px, (255, 0, 255))
        x1, y1, x2, y2 = np.rint(bbox[i]).astype(int)
        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
        if (vb != 0).any():
            cx, cy, w, h = vb
            x1, y1, x2, y2 = np.rint([(cx-w/2)*W, (cy-h/2)*H, (cx+w/2)*W, (cy+h/2)*H]).astype(int)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(img, f"{args.clip} f{f} person_ok={bool(z['person_ok'][srow[0]])}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
        output_path = out / f"overlay_{args.clip}_{f}.png"
        if not cv2.imwrite(str(output_path), img):
            raise OSError(f"Could not write overlay: {output_path}")
        print(f, "struct-vs-raw median px", np.median(np.linalg.norm(struct_px - raw_px[i], axis=-1)).round(1))


if __name__ == "__main__":
    main()    