"""Build per-person YOLO answer sheets (.npz, Phase-1 schema) from the canonical label txt files.
One file per frame, 1-based original frame number in the name; missing file = no detection.
Run in `rugby` from ~/rugby-video-analytics:
   python phase2/scripts/labels_to_sheets.py <labels_dir> <stem> <first> <last> <out_dir> [--fusion assign|drop]
"""
import argparse, numpy as np
from pathlib import Path

W,H, FPS = 3840, 2160, 60000/1001
COCO17 = ["nose", "L_eye", "R_eye", "L_ear", "R_ear", "L_sho", "R_sho", "L_elb", "R_elb",
          "L_wri", "R_wri", "L_hip", "R_hip", "L_kne", "R_kne", "L_ank", "R_ank"]
PERSON = ["tackler", "carrier"]                 # track 0 / track 1

def read_frame(labels_dir, stem, n):
    """Detections of original frame n (1-based) -> list of dict(box=(cx,cy,w,h), kp=(17,2), kc=(17,), conf=float).
    Label line: cls cx cy w h (kx ky kc)x17 box_conf = 57 values, all normalised 0..1 (handover 3.3)."""
    p = Path(labels_dir) / f"{stem}_{n}.txt"
    if not p.exists():
        return []
    dets = []
    for line in p.read_text().splitlines():
        v = np.array(line.split(), dtype=float)
        if v.size != 57:
            continue
        kp3 = v[5:56].reshape(17, 3)
        dets.append(
            dict(box=v[1:5], kp=kp3[:,:2], kc=kp3[:,2], conf=float(v[56]))
        )
    return dets

def iou(a,b):
    """IoU of two (cx, cy, w, h) boxes."""
    ax1, ay1 = a[0] - a[2]/2, a[1] - a[3]/2
    ax2, ay2 = a[0] + a[2]/2, a[1] + a[3]/2
    bx1, by1 = b[0] - b[2]/2, b[1] - b[3]/2
    bx2, by2 = b[0] + b[2]/2, b[1] + b[3]/2
    iw = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    union = a[2]*a[3] + b[2]*b[3] - inter
    return inter / union if union > 0 else 0.0

def assign(prev, dets, min_iou=0.1):
    """prev: last known box of track 0 / 1. dets: detections of this frame.
    Returns [j0, j1]: index into dets for each track, or -1 (not observed). Brute force over all injective maps."""
    n = len(dets)
    M = np.array([[iou(prev[i], d["box"]) for d in dets] for i in range(2)]).reshape(2, n)
    best, best_score = [-1, -1], 0.0
    for j0 in [-1] + list(range(n)):
        for j1 in [-1] + list(range(n)):
            if j0 == j1 and j0 != -1:
                continue
            if j0 != -1 and M[0, j0] < min_iou:
                continue
            if j1 != -1 and M[1, j1] < min_iou:
                continue
            score = 0.0
            if j0 != -1:
                score += M[0, j0]
            if j1 != -1:
                score += M[1, j1]
            if score > best_score:
                best_score = score
                best = [j0, j1]
    return best

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labels_dir"); ap.add_argument("stem")
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int)
    ap.add_argument("out_dir")
    ap.add_argument("--fusion", choices=["assign", "drop"], default="assign", help="Single-detection frames: assign to the better-overlapping track, or drop(both unobserved)")
    args = ap.parse_args()
    
    frames = np.arange(args.first, args.last + 1)
    T = len(frames)
    coords = np.zeros((T,2,17,2))
    confs = np.zeros((T,2,17))
    boxes = np.zeros((T,2,4))
    n_det = np.zeros(T, dtype=int)
    prev = [None, None]  # last known boxes for track 0 and 1
    started = False
    init_frame = -1
    
    for i, n in enumerate(frames):
        dets = read_frame(args.labels_dir, args.stem, n)
        n_det[i] = len(dets)
        if not started:
            if len(dets) != 2:
                continue           
            j_right = int(np.argmax([d["box"][0] for d in dets]))
            a = [j_right, 1 - j_right]
            started = True
            init_frame = int(n)
        elif len(dets) == 1 and args.fusion == "drop":
            a = [-1, -1]
        else:
            a = assign(prev, dets)
        for p in range(2):
            j = a[p]
            if j >= 0:
                d = dets[j]
                coords[i, p] = d["kp"]
                confs[i, p] = d["kc"]
                boxes[i, p] = d["box"]
                prev[p] = d["box"]
            
            

    print(f"frames {args.first}-{args.last}: T={T}  n_det histogram (0/1/2/3+):",
          [int((n_det == c).sum()) for c in (0, 1, 2)] + [int((n_det >= 3).sum())], " init frame:", init_frame)
    out_dir = Path(args.out_dir).expanduser(); out_dir.mkdir(parents=True, exist_ok=True)
    for p, name in enumerate(PERSON):
        seen = np.any(boxes[:, p] != 0, axis=1)
        print(f"  {name}: observed {int(seen.sum())}/{T} frames")
        np.savez(out_dir / f"yolo_raw_{args.stem}_{name}_{args.fusion}.npz",
                 coords=coords[:, p].astype(np.float32), confs=confs[:, p].astype(np.float32),
                 bbox=boxes[:, p].astype(np.float32), n_det=n_det, frame_index=frames,
                 fps=FPS, W=W, H=H, joint_names=np.array(COCO17), source="yolo_raw", person=name, fusion=args.fusion)
    print("saved to", out_dir)


if __name__ == "__main__":
    main()