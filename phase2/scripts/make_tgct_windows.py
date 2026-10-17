# phase2/scripts/make_tgct_windows.py
"""Solo sheets -> even-frame body-12 sequences for T-GCT (worksheet exercise c).
Run in rugby:  python -m phase2.scripts.make_tgct_windows
"""
import numpy as np
from pathlib import Path
from phase2.tgct.graph import COCO_IDX_BODY12
from phase2.temporal import observed_mask

TRAIN = ["PA041266", "PA041267", "PA041269", "PA041270"]
VAL = ["PA041268"]
SRC = Path.home() / "data/phase2_npz"
DST = Path.home() / "data/tgct"
TAIL = 30                 # last 30 original frames excluded (video-processing rule, 2026-10-05)
T, STRIDE, MIN_OBS = 128, 16, 0.5

def convert(stem):
    src_path = SRC / f"yolo_raw_{stem}_solo.npz"
    with np.load(src_path, allow_pickle=False) as z:
        required = ("coords", "confs", "n_cand", "frame_index")
        missing = [name for name in required if name not in z.files]
        if missing:
            raise ValueError(f"{src_path} is missing required arrays: {', '.join(missing)}")
        fi = z["frame_index"]
        raw_coords, raw_confs, n_cand = z["coords"], z["confs"], z["n_cand"]
        if fi.ndim != 1 or fi.size == 0:
            raise ValueError(f"{src_path} frame_index must be a non-empty one-dimensional array")
        if raw_coords.ndim != 3 or raw_coords.shape[1] <= max(COCO_IDX_BODY12) or raw_coords.shape[2] != 2:
            raise ValueError(f"{src_path} coords must have shape (T, at least 17, 2), got {raw_coords.shape}")
        if raw_confs.ndim != 2 or raw_confs.shape != raw_coords.shape[:2]:
            raise ValueError(f"{src_path} confs must match coords' first two dimensions, got {raw_confs.shape}")
        if raw_coords.shape[0] != len(fi) or n_cand.shape != fi.shape:
            raise ValueError(f"{src_path} frame_index, n_cand, and coords must have matching frame counts")

        keep = (fi % 2 == 0) & (fi <= fi.max() - TAIL)  # even frames, tail dropped
        coords = raw_coords[keep][:, COCO_IDX_BODY12]     # (N, 12, 2)
        confs = raw_confs[keep][:, COCO_IDX_BODY12]       # (N, 12)
        present = (n_cand == 1)[keep]                     # (N,) exactly one candidate
        selected_frames = fi[keep]

    if len(coords) == 0:
        raise ValueError(f"{src_path} contains no frames after even-frame and tail filtering")

    np.savez(DST / f"seq_{stem}.npz", coords=coords, confs=confs, present=present, frame_index=selected_frames)
    obs = observed_mask(coords, confs) & present[:, None]  # (N, 12) bool
    N = len(coords)
    starts = range(0, N - T + 1, STRIDE)
    n_all = len(starts)
    n_keep = sum(obs[s:s + T].mean() >= MIN_OBS for s in starts)
    return N, present.mean(), obs.mean(), n_all, n_keep


if __name__ == "__main__":
    DST.mkdir(parents=True, exist_ok=True)
    for split, stems in (("TRAIN", TRAIN), ("VAL", VAL)):
        tot_n = tot_all = tot_w = 0
        for s in stems:
            N, p, o, n_all, n_keep = convert(s)
            tot_n += N
            tot_all += n_all
            tot_w += n_keep
            print(f"{split} {s}: even frames {N:5d}  present {p:.3f}  obs(joint) {o:.3f}  "
                  f"windows T={T} stride={STRIDE}: {n_all} -> {n_keep} after obs>={MIN_OBS}")
        print(f"{split} total: even frames {tot_n}, windows {tot_all} -> {tot_w} after obs>={MIN_OBS}")