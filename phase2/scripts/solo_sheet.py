"""Build a single-person answer sheet from per-frame YOLO pose labels (solo footage).

For every original frame n = 1..N:
  - read <labels_dir>/<stem>_<n>.txt if it exists (one row per detected person,
    57 normalized values: cls cx cy w h (kx ky kconf)x17 box_conf)
  - gate detections by horizontal edges and either sqrt(bbox area) or bbox long side
  - keep the highest-box_conf candidate; no candidates means an all-zero pose
  - record n_det (all rows) and n_cand (rows passing both gates)

Outputs:
  <out_dir>/yolo_raw_<stem>_solo.npz   (coords, confs, bbox, n_det, frame_index, fps, W, H, ...)
  <runs_dir>/solo_runs_<stem>.csv      (body-12 observed and exactly one candidate)

Visibility uses temporal.observed_mask, including its no-detection check.
Tail frames are excluded from runs only; the raw NPZ retains all N frames.

Usage:
    python phase2/scripts/solo_sheet.py <labels_dir> <stem> <n_frames>
"""

import argparse
import csv
import sys
from io import StringIO
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from phase2.scripts.labels_to_sheets import COCO17  # noqa: E402
from phase2.temporal import observed_mask  # noqa: E402

BODY12 = list(range(5, 17))  # COCO: shoulders, elbows, wrists, hips, knees, ankles
JOINT_NAMES = COCO17


def read_frame(path, min_size, edge_eps, width, height, min_long=700.0):
    """Return (coords (17,2), confs (17,), bbox (4,), n_det, n_cand).

    n_det  = number of rows in the file (all detections)
    n_cand = number of rows left after the edge gate and the size gate
    The returned pose is the highest-box_conf row among the candidates
    (all-zero when no candidate remains).
    """
    text = Path(path).read_text()
    if not text.strip():
        return np.zeros((17, 2)), np.zeros(17), np.zeros(4), 0, 0
    try:
        rows = np.loadtxt(StringIO(text), ndmin=2)
    except ValueError as exc:
        raise ValueError(f"{path}: invalid YOLO pose labels: {exc}") from exc
    if rows.shape[1] != 57:
        raise ValueError(f"{path}: expected 57 values per row, got {rows.shape[1]}")
    if not np.all(np.isfinite(rows)):
        raise ValueError(f"{path}: label values must be finite")
    if np.any((rows[:, 1:] < 0) | (rows[:, 1:] > 1)):
        raise ValueError(f"{path}: coordinates and confidence values must be normalized to [0, 1]")
    x0 = rows[:, 1] - rows[:, 3] / 2
    x1 = rows[:, 1] + rows[:, 3] / 2
    size = np.sqrt((rows[:, 3] * width) * (rows[:, 4] * height))
    long_side = np.maximum(rows[:, 3] * width, rows[:, 4] * height)
    big = (size >= min_size) | (long_side >= min_long)
    cand = rows[(x0 >= edge_eps) & (x1 <= 1 - edge_eps) & big]
    if len(cand) == 0:
        return np.zeros((17, 2)), np.zeros(17), np.zeros(4), len(rows), 0
    best = cand[np.argmax(cand[:, -1])]
    kpts = best[5:56].reshape(17, 3)
    return kpts[:, :2], kpts[:, 2], best[1:5], len(rows), len(cand)


def true_runs(mask):
    """Return [(start, end), ...] (inclusive, 0-based) of maximal runs of True."""
    mask = np.asarray(mask)
    if mask.ndim != 1 or not np.all((mask == 0) | (mask == 1)):
        raise ValueError("mask must be a one-dimensional boolean or binary array")
    edges = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1) - 1
    return list(zip(starts.tolist(), ends.tolist()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labels_dir")
    ap.add_argument("stem")
    ap.add_argument("n_frames", type=int)
    ap.add_argument("--out-dir", default=str(Path.home() / "data" / "phase2_npz"))
    ap.add_argument("--runs-dir", default=".")
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--tail", type=int, default=30)
    ap.add_argument("--win", type=int, default=60)
    ap.add_argument("--min-size", type=float, default=400.0, help="minimum sqrt(bbox area) in px; provisional default")
    ap.add_argument("--min-long", type=float, default=700.0, help="minimum bbox long side in px (alternative to --min-size)")
    ap.add_argument("--edge-eps", type=float, default=0.005, help="normalized horizontal edge margin")
    ap.add_argument("--fps", type=float, default=60000 / 1001)
    ap.add_argument("--width", type=int, default=3840)
    ap.add_argument("--height", type=int, default=2160)
    args = ap.parse_args()
    if args.n_frames <= 0:
        ap.error("n_frames must be positive")
    if not np.isfinite(args.tau) or not 0 <= args.tau <= 1:
        ap.error("--tau must be finite and in [0, 1]")
    if args.tail < 0:
        ap.error("--tail must be nonnegative")
    if args.win <= 0:
        ap.error("--win must be positive")
    if not np.isfinite(args.min_size) or args.min_size < 0:
        ap.error("--min-size must be finite and nonnegative")
    if not np.isfinite(args.min_long) or args.min_long < 0:
        ap.error("--min-long must be finite and nonnegative")
    if not np.isfinite(args.edge_eps) or not 0 <= args.edge_eps < 0.5:
        ap.error("--edge-eps must be finite and in [0, 0.5)")
    if not np.isfinite(args.fps) or args.fps <= 0:
        ap.error("--fps must be finite and positive")
    if args.width <= 0 or args.height <= 0:
        ap.error("--width and --height must be positive")
    labels_dir = Path(args.labels_dir).expanduser()
    if not labels_dir.is_dir():
        ap.error(f"labels directory does not exist: {labels_dir}")

    N = args.n_frames
    coords = np.zeros((N, 17, 2), dtype=np.float32)
    confs = np.zeros((N, 17), dtype=np.float32)
    bbox = np.zeros((N, 4), dtype=np.float32)
    n_det = np.zeros(N, dtype=np.int64)
    n_cand = np.zeros(N, dtype=np.int64)
    frame_index = np.arange(1, N + 1, dtype=np.int64)

    for i in range(N):
        p = labels_dir / f"{args.stem}_{i+1}.txt"
        if p.exists():
            try:
                coords[i], confs[i], bbox[i], n_det[i], n_cand[i] = read_frame(
                    p, args.min_size, args.edge_eps, args.width, args.height, args.min_long)
            except (OSError, ValueError) as exc:
                ap.exit(1, f"{p}: {exc}\n")

    obs = observed_mask(coords, confs, tau=args.tau)
    full = obs[:, BODY12].all(axis=1) & (n_cand == 1)
    full[max(N - args.tail, 0):] = False

    runs = true_runs(full)
    rows = []
    for s, e in runs:
        length = e - s + 1
        n_flag = int((n_det[s:e + 1] != 1).sum())
        rows.append((args.stem, int(frame_index[s]), int(frame_index[e]), length, n_flag))

    lengths = np.array([r[3] for r in rows], dtype=np.int64)
    long = lengths[lengths >= args.win]
    n_windows = int((long - args.win + 1).sum())

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_npz = out_dir / f"yolo_raw_{args.stem}_solo.npz"
    np.savez(out_npz, coords=coords, confs=confs, bbox=bbox, n_det=n_det,
             frame_index=frame_index, fps=args.fps, W=args.width, H=args.height,
             joint_names=np.array(JOINT_NAMES), source="yolo_raw", person="solo",
             tail=args.tail, tau=args.tau, win=args.win,
             n_cand=n_cand, min_size=args.min_size, edge_eps=args.edge_eps,
             min_long=args.min_long)

    runs_dir = Path(args.runs_dir).expanduser()
    runs_dir.mkdir(parents=True, exist_ok=True)
    out_csv = runs_dir / f"solo_runs_{args.stem}.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stem", "start", "end", "length", "n_flag"])
        w.writerows(rows)

    hist = [int((n_det == 0).sum()), int((n_det == 1).sum()), int((n_det == 2).sum()), int((n_det >= 3).sum())]
    print(f"{args.stem}: N={N}  n_det histogram (0/1/2/3+): {hist}  tail excluded: {min(N, args.tail)}")
    chist = [int((n_cand == 0).sum()), int((n_cand == 1).sum()), int((n_cand >= 2).sum())]
    print(f"  n_cand histogram (0/1/2+): {chist}  (edge_eps={args.edge_eps}, min_size={args.min_size}, min_long={args.min_long})")
    print(f"  fully visible frames (body-12, tau={args.tau}, n_cand==1): {int(full.sum())}")
    print(f"  runs: {len(rows)}  longest: {int(lengths.max()) if len(lengths) else 0}")
    print(f"  runs >= {args.win}: {len(long)}  frames: {int(long.sum())}  windows: {n_windows}")
    print(f"  wrote {out_npz}")
    print(f"  wrote {out_csv}")


if __name__ == "__main__":
    main()