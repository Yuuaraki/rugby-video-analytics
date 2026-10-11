"""Draw the YOLO tackler/carrier sheets on the GT crop frames for the identity check."""
import csv
import json
from pathlib import Path

import cv2
import numpy as np

CLIP = "P9201256"
NPZ_DIR = Path.home() / "data/phase2_npz"
FRAME_DIR = Path.home() / "data/phase2_gt/frames_P9201256"
OUT_DIR = Path.home() / "data/phase2_gt/identity_overlay_P9201256"
CSV_PATH = Path.home() / "rugby-video-analytics/phase2/results/identity_fix_P9201256.csv"
CONF_DRAW = 0.05
EDGES = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12),
         (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]  # COCO-17
SHEETS = {"T": ("tackler_assign", (0, 255, 255)),  # yellow (BGR)
          "C": ("carrier_assign", (255, 0, 255))}  # magenta (BGR)

def to_crop_px(xy_norm, crop_origin, W, H):
    """Full-frame normalized coords (..., 2) -> crop pixel coords (..., 2)."""
    xy = np.array(xy_norm, dtype=np.float32)
    xy[..., 0] = xy[..., 0] * W - crop_origin[0]
    xy[..., 1] = xy[..., 1] * H - crop_origin[1]
    return xy

def draw_sheet(img, xy, conf, color, tag):
    """Draw one 17-joint skeleton on img; return the number of joints drawn."""
    ok = np.isfinite(xy).all(axis=1) & (conf >= CONF_DRAW)
    for a, b in EDGES:
        if ok[a] and ok[b]:
            cv2.line(img, tuple(map(int, xy[a])), tuple(map(int, xy[b])), color, 3)
    for j in np.where(ok)[0]:
        cv2.circle(img, tuple(map(int, xy[j])), 8, color, -1)
    if ok.any():
        x, y = xy[ok].min(axis=0)
        cv2.putText(img, tag, (int(x), int(y) - 15), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 4)
    return int(ok.sum())

def main():
    meta = json.loads((FRAME_DIR / "crop_meta.json").read_text())
    W,H, origin = meta["W"], meta["H"], meta["crop_origin"]
    sheets = {tag: np.load(NPZ_DIR / f"yolo_raw_{CLIP}_{name}.npz") for tag, (name, _) in SHEETS.items()}
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    rows = []
    for k in meta["frames"]:
        img = cv2.imread(str(FRAME_DIR / f"{k:06d}.jpg"))
        counts = {}
        for tag, (_, color) in SHEETS.items():
            s = sheets[tag]
            r = int(np.searchsorted(s["frame_index"], k))
            assert s["frame_index"][r] == k, (tag, k)
            xy = to_crop_px(s["coords"][r], origin, W, H)
            counts[tag] = draw_sheet(img, xy, s["confs"][r], color, tag)
            n_det = int(s['n_det'][r])
        label = f"{k}  n_det={n_det}  T joints={counts['T']}  C joints={counts['C']}"
        cv2.rectangle(img, (0, 0), (1500, 90), (0, 0, 0), -1)
        cv2.putText(img, label, (20, 62), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 4)
        cv2.imwrite(str(OUT_DIR / f"{k:06d}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        rows.append([k, n_det, "", ""])

    if CSV_PATH.exists():
        print("CSV already exists, not overwritten:", CSV_PATH)
    else:
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["frame", "n_det", "verdict", "basis"])
            w.writerows(rows)
        print("template written:", CSV_PATH)
    print("overlays:", len(rows), "->", OUT_DIR)


if __name__ == "__main__":
    main()