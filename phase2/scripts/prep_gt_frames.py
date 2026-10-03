"""Prepare cropped JPEG frames for ground-truth annotation (P9201256 tackle window)."""
from pathlib import Path
import numpy as np
import json
import cv2

W, H = 3840, 2160
F_START, F_END, F_STEP = 3222, 3416, 2
MARGIN = 150
CLIP = "P9201256"
REPO = Path.home() / "rugby-video-analytics"
LABEL_DIR = REPO / "runs/pose/runs/pose/20260920_full/labels"

VIDEO = REPO / "data/raw/20260920/P9201256.MOV"
OUT_DIR = Path.home() / "data/phase2_gt/frames_P9201256"
JPEG_QUALITY = 95

def read_box_px(label_path):
    """Return (n, 4) array [x1, y1, x2, y2] in pixels; shape (0, 4) if the file is missing."""
    if not label_path.exists():
        return np.zeros((0, 4))
    rows = np.loadtxt(label_path, ndmin=2) # (n, 57): cls, cx, cy, w, h, 51 kpt values, conf
    cx, cy, w, h = rows[:, 1], rows[:, 2], rows[:, 3], rows[:, 4]
    x1 = (cx - w / 2) * W
    y1 = (cy - h / 2) * H
    x2 = (cx + w / 2) * W
    y2 = (cy + h / 2) * H
    return np.stack([x1, y1, x2, y2], axis=1)

def compute_crop_rect():
    """Compute the crop rectangle [x1, y1, x2, y2] that encompasses all boxes with a margin."""
    frames = list(range(F_START, F_END + 1, F_STEP))
    all_boxes = []
    for k in frames:
        b = read_box_px(LABEL_DIR / f"{CLIP}_{k}.txt")
        if len(b) >= 3:
            print(f"n>=3 at frame {k}")
            print(np.round(b))
        all_boxes.append(b)
    boxes = np.concatenate(all_boxes, axis=0) #(N, 4)
    
    #union rectangle of all boxes (4 floats)
    ux0, uy0, ux1, uy1 = boxes[:, 0].min(), boxes[:, 1].min(), boxes[:, 2].max(), boxes[:, 3].max()
    
    #add MARGIN, round outward, clip to the image, cast to int
    rx0, ry0, rx1, ry1 = (
    int(np.clip(np.floor(ux0 - MARGIN), 0, W)),
    int(np.clip(np.floor(uy0 - MARGIN), 0, H)),
    int(np.clip(np.ceil(ux1 + MARGIN), 0, W)),
    int(np.clip(np.ceil(uy1 + MARGIN), 0, H)),
    )
    return frames, (rx0, ry0, rx1, ry1), (ux0, uy0, ux1, uy1)

def export_frames(frames, rect):
    """Read the video sequentially and save cropped JPEGs for the wanted frames."""
    rx0, ry0, rx1, ry1 = rect
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wanted = set(frames)
    cap = cv2.VideoCapture(str(VIDEO))
    k = 0  # 1-based number of the frame just read
    n_saved = 0
    try:
        while k < F_END:
            ok, img = cap.read()
            if not ok:
                raise RuntimeError(f"read failed after frame {k}")
            k += 1
            if k == 1:
                assert img.shape == (H, W, 3), img.shape
            if k in wanted:
                crop = img[ry0:ry1, rx0:rx1]
                path = OUT_DIR / f"{k:06d}.jpg"
                if not cv2.imwrite(str(path), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]):
                    raise RuntimeError(f"failed to write {path}")
                n_saved += 1
    finally:
        cap.release()

    meta = {
        "clip": CLIP,
        "crop_origin": [rx0, ry0],
        "crop_size": [rx1 - rx0, ry1 - ry0],
        "W": W,
        "H": H,
        "margin": MARGIN,
        "jpeg_quality": JPEG_QUALITY,
        "frames": frames,
    }
    with (OUT_DIR / "crop_meta.json").open("w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2)
    return n_saved

if __name__ == "__main__":
    frames, rect, union = compute_crop_rect()
    rx0, ry0, rx1, ry1 = rect
    print("n_frames:", len(frames))
    print("union [px]:", np.round(union))
    print("crop origin (x0, y0):", (rx0, ry0))
    print("crop size (w, h):", (rx1 - rx0, ry1 - ry0))
    n_saved = export_frames(frames, rect)
    print("saved:", n_saved, "->", OUT_DIR)
    
    