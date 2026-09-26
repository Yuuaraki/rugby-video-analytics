"""Locate a stream-copied clip's first frame inside the original video by pixel matching."""
import sys
import cv2
import numpy as np

FPS = 60000 / 1001
THUMB = (480, 270)


def count_and_first(path):
    cap = cv2.VideoCapture(path)
    ok, first = cap.read()
    n = 1 if ok else 0
    while ok:
        ok, _ = cap.read()
        n += ok
    cap.release()
    return n, first


def main(orig_path, clip_path, guess_sec, search=40):
    n_clip, first = count_and_first(clip_path)
    ref = cv2.resize(first, THUMB).astype(np.int32)

    center = int(round(guess_sec * FPS))
    start = max(center - search, 0)
    cap = cv2.VideoCapture(orig_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    scores = []
    for idx in range(start, center + search + 1):
        ok, f = cap.read()
        if not ok:
            break
        diff = np.abs(cv2.resize(f, THUMB).astype(np.int32) - ref).mean()
        scores.append((diff, idx))
    cap.release()

    scores.sort()
    best_diff, best_idx = scores[0]
    print(f"clip decodable frames : {n_clip}")
    print(f"best match            : original frame {best_idx} (0-based), t = {best_idx / FPS:.3f}s, mean|diff| = {best_diff:.2f}")
    print(f"runner-up             : frame {scores[1][1]}, mean|diff| = {scores[1][0]:.2f}")
    print(f"mapping               : original_frame = clip_frame - 1 + {best_idx}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]))
