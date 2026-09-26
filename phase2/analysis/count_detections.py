"""Count person detections per frame from Ultralytics pose label files."""
import re
import sys
from pathlib import Path

FPS = 60000 / 1001


def frame_index(path: Path) -> int:
    """Ultralytics names labels <stem>_<frame>.txt; missing files mean zero detections."""
    match = re.search(r"_(\d+)$", path.stem)
    if match is None:
        raise ValueError(f"cannot parse frame number from {path.name}")
    return int(match.group(1))


def load_counts(label_dir: Path) -> dict[int, int]:
    counts: dict[int, int] = {}
    for path in label_dir.glob("*.txt"):
        lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
        counts[frame_index(path)] = len(lines)
    return counts


def find_runs(counts: dict[int, int], total: int, target: int):
    """Return (start, end, length) for consecutive frames whose count == target."""
    runs, start = [], None
    for n in range(1, total + 1):
        if counts.get(n, 0) == target:
            start = n if start is None else start
        elif start is not None:
            runs.append((start, n - 1, n - start))
            start = None
    if start is not None:
        runs.append((start, total, total - start + 1))
    return runs


def main(label_dir: str, start_time: float) -> None:
    counts = load_counts(Path(label_dir))
    total = int(sys.argv[3]) if len(sys.argv) > 3 else max(counts)
    print(f"frames with labels: {len(counts)} / {total}")
    for target in (0, 1, 3):
        for a, b, length in find_runs(counts, total, target):
            if length < 3:
                continue
            t_a = start_time + (a - 1) / FPS
            t_b = start_time + (b - 1) / FPS
            print(f"count={target}  frames {a}-{b} ({length})  orig {t_a:.2f}s-{t_b:.2f}s")


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]))
