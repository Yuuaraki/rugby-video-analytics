"""Duplicate-frame check for raw videos.

For each consecutive pair, compute mean |gray_t - gray_{t-1}| on every
`step`-th pixel (no resizing or averaging). A pair is counted as a duplicate
when its difference is strictly below ratio * P90(body). The last 30 pairs
are excluded from the body by default and counted separately using the same
threshold. Use --tail 0 to assess the whole clip.

P90 estimates the genuine-pair level only when enough genuine pairs remain;
bodies dominated by duplicates (roughly 90% or more) are not reliable inputs.
An empty body or body P90 == 0 cannot be assessed by this rule.
Reported frame numbers are candidates, not proof of duplication.

Usage:
    python phase2/video_qc.py data/raw/20261004/PA041264.MOV [more.MOV ...]
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


def frame_diffs(path, step=4, max_frames=0):
    """Return (n_frames, d), with one difference per decoded adjacent pair."""
    if step <= 0:
        raise ValueError("step must be positive")
    if max_frames < 0:
        raise ValueError("max_frames must be nonnegative (0 means unlimited)")

    cap = cv2.VideoCapture(str(path))
    diffs = []
    prev = None
    n = 0
    try:
        if not cap.isOpened():
            raise OSError(f"Cannot open video file: {path}")
        while not max_frames or n < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame[::step, ::step], cv2.COLOR_BGR2GRAY).astype(np.int16)
            if prev is not None:
                diffs.append(float(np.abs(gray - prev).mean()))
            prev = gray
            n += 1
    finally:
        cap.release()
    return n, np.asarray(diffs, dtype=np.float64)


def summarize(d, ratio, tail):
    """Judge the body and last `tail` pairs against the body P90.

    Return (n_dup_body, rate_body, n_dup_tail, p90, min_body, dup_frames_body).
    """
    if not np.isfinite(ratio) or ratio <= 0:
        raise ValueError("ratio must be finite and positive")
    if d.ndim != 1 or len(d) == 0:
        raise ValueError("at least two decoded frames are required")
    if not np.all(np.isfinite(d)) or np.any(d < 0):
        raise ValueError("frame differences must be finite and nonnegative")
    if not isinstance(tail, (int, np.integer)) or tail < 0:
        raise ValueError("tail must be a nonnegative integer")
    split = len(d) - tail
    if split <= 0:
        raise ValueError(
            f"tail ({tail}) must be less than the number of pairs ({len(d)}); "
            "at least one body pair is required"
        )
    body, tail_d = d[:split], d[split:]
    p90 = float(np.percentile(body, 90))
    if p90 == 0:
        raise ValueError("body P90 is zero; the relative duplicate threshold cannot be estimated")
    thr = ratio * p90
    is_dup_body = body < thr
    n_dup_body = int(is_dup_body.sum())
    rate_body = 100.0 * n_dup_body / len(body)
    n_dup_tail = int((tail_d < thr).sum())
    # d[i] compares 1-based frames i+1 and i+2; the copy candidate is i+2.
    dup_frames = np.flatnonzero(is_dup_body) + 2
    return n_dup_body, rate_body, n_dup_tail, p90, float(body.min()), dup_frames


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--ratio", type=float, default=0.3)
    ap.add_argument("--step", type=int, default=4)
    ap.add_argument("--max-frames", type=int, default=0, help="0 means unlimited")
    ap.add_argument("--tail", type=int, default=30, help="last pairs to exclude from body (default: 30)")
    args = ap.parse_args()
    if not np.isfinite(args.ratio) or args.ratio <= 0:
        ap.error("--ratio must be finite and positive")
    if args.step <= 0:
        ap.error("--step must be positive")
    if args.max_frames < 0:
        ap.error("--max-frames must be nonnegative")
    if args.tail < 0:
        ap.error("--tail must be nonnegative")

    print(
        f"{'stem':<16}{'frames':>8}{'dup':>7}{'rate%':>8}{'tail_dup':>10}"
        f"{'min_d':>8}{'p90_d':>8}{'min/p90':>9}"
    )
    for v in args.videos:
        try:
            n, d = frame_diffs(v, args.step, args.max_frames)
            n_dup, rate, n_tail, p90, min_body, dup_frames = summarize(d, args.ratio, args.tail)
        except (OSError, ValueError, cv2.error) as exc:
            ap.exit(1, f"{v}: {exc}\n")
        print(
            f"{Path(v).stem:<16}{n:>8}{n_dup:>7}{rate:>8.2f}{n_tail:>10}"
            f"{min_body:>8.3f}{p90:>8.3f}{min_body / p90:>9.3f}"
        )
        if n_dup:
            print(f"    first duplicate frames in body (1-based): {dup_frames[:10].tolist()}")


if __name__ == "__main__":
    main()
