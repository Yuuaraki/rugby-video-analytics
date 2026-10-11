"""Propose tackle windows from Ultralytics pose labels of a FULL video.
 
Signature of a tackle in the detection stream:
  1. two players are detected for a while (count == 2), then
  2. the detector collapses both into ONE box (count == 1) that is clearly
     larger than a single player and sits between the two previous boxes, then
  3. they separate again (count == 2) or leave the frame (count == 0).
 
"count == 1" alone is NOT enough: it also happens when one player simply walks
out of frame. The area/position test below tells the two apart in most cases,
but every candidate must still be confirmed by eye (1-second thumbnails).
 
Usage:
    python find_tackle_candidates.py <labels_dir> <total_frames> [fps]
 
Prints one line per merge run. Lines marked TACKLE? are the candidates; the two
numbers after "clip:" are the suggested start/end seconds for tackles.txt.
"""
import re
import sys
from pathlib import Path
 
import numpy as np
 
MIN_MERGE = 20              # frames a merged (count==1) run must last (~0.33 s at 60 fps)
MIN_PAIR = 30               # two-person frames required shortly before the merge
LOOKBACK = 120              # how far back to look for the two-person phase (2 s)
AREA_RATIO = 1.25           # merged box must be this much larger than one player
PRE_S, POST_S = 2.0, 1.5    # margins added around the merge window for the clip
 
 
def load_boxes(label_dir):
    """frame -> array of (cx, cy, w, h) in normalised coords, one row per detection."""
    boxes = {}
    for path in Path(label_dir).glob("*.txt"):
        frame = int(re.search(r"_(\d+)$", path.stem).group(1))
        rows = [ln.split() for ln in path.read_text().splitlines() if ln.strip()]
        boxes[frame] = np.array([[float(v) for v in r[1:5]] for r in rows])
    return boxes
 
 
def constant_runs(values):
    """Yield (value, first_frame, last_frame) for maximal constant runs; frames are 1-based."""
    start = 1
    for i in range(2, len(values) + 1):
        if values[i - 1] != values[start - 1]:
            yield values[start - 1], start, i - 1
            start = i
    yield values[start - 1], start, len(values)
 
 
def main(label_dir, total, fps=60000 / 1001):
    boxes = load_boxes(label_dir)
    count = [len(boxes.get(n, ())) for n in range(1, total + 1)]
    found = 0
    for value, a, b in constant_runs(count):
        if value != 1 or (b - a + 1) < MIN_MERGE:
            continue
        pair = [n for n in range(max(1, a - LOOKBACK), a) if count[n - 1] == 2]
        if len(pair) < MIN_PAIR:
            continue
        single = np.concatenate([boxes[n] for n in pair[-MIN_PAIR:]])
        merged = np.concatenate([boxes[n] for n in range(a, min(b, a + MIN_MERGE - 1) + 1)])
        ratio = np.median(merged[:, 2] * merged[:, 3]) / np.median(single[:, 2] * single[:, 3])
        xlo, xhi = sorted(boxes[pair[-1]][:, 0])
        between = (xlo - 0.05) <= float(np.median(merged[:, 0])) <= (xhi + 0.05)
        verdict = "TACKLE?" if (ratio >= AREA_RATIO and between) else "one-left"
        t0, t1 = (a - 1) / fps, b / fps
        print(f"{verdict:8s} frames {a}-{b} ({b - a + 1})  t={t0:.2f}-{t1:.2f}s  "
              f"area x{ratio:.2f}  between={between}  clip: {max(t0 - PRE_S, 0):.1f} {t1 + POST_S:.1f}")
        found += verdict == "TACKLE?"
    print(f"--- {found} candidate(s); confirm each one on the 1-second thumbnails ---")
 
 
if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 60000 / 1001)