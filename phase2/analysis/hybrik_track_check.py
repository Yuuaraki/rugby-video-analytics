"""Inspect HybrIK demo output (res.pk): frame count, bbox continuity, likely identity switches."""
import pickle
import sys
import numpy as np

JUMP_PX = 100  # a real player cannot move its bbox centre this far in 1/60 s


def main(pk_path):
    with open(pk_path, "rb") as f:
        res = pickle.load(f)
    bbox = np.asarray(res["bbox"], dtype=float)  # (N, 4) xyxy in the 1080p frame
    n = len(bbox)
    scores = np.asarray(res["pred_scores"], dtype=float).reshape(n, -1)
    centre = np.stack([(bbox[:, 0] + bbox[:, 2]) / 2, (bbox[:, 1] + bbox[:, 3]) / 2], axis=1)
    height = bbox[:, 3] - bbox[:, 1]
    jump = np.linalg.norm(np.diff(centre, axis=0), axis=1)

    print(f"frames             : {n}")
    print(f"bbox height px     : median {np.median(height):.0f}, min {height.min():.0f}, max {height.max():.0f}")
    print(f"mean joint score   : median {np.median(scores.mean(axis=1)):.3f}")
    switches = np.where(jump > JUMP_PX)[0]
    print(f"centre jumps >{JUMP_PX}px : {len(switches)}")
    for i in switches:
        print(f"  frame {i + 1:3d} -> {i + 2:3d}: {jump[i]:4.0f} px  "
              f"({centre[i, 0]:.0f},{centre[i, 1]:.0f}) -> ({centre[i + 1, 0]:.0f},{centre[i + 1, 1]:.0f})")


if __name__ == "__main__":
    main(sys.argv[1])
