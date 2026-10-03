"""Sanity check: pixel distance between GT joints (vis == 0) and the raw-YOLO tackler sheet."""
import argparse

import numpy as np

JOINTS = ["L_sho", "R_sho", "L_elb", "R_elb", "L_wri", "R_wri",
          "L_hip", "R_hip", "L_kne", "R_kne", "L_ank", "R_ank"]  # COCO 5..16
SWAP_LR = [1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10]
CONF_MIN = 0.5

def pixel_dists(a,b,W,H):
    """Distance in pixels between normalized coords a and b, shape (..., 2) -> (...)."""
    d = np.linalg.norm((a - b) * np.array([W, H], dtype=float), axis=-1)
    return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--yolo", required=True)
    args = ap.parse_args()
    
    gt = np.load(args.gt)
    yo = np.load(args.yolo)
    W,H = int(gt["W"]), int(gt["H"])
    assert (int(yo["W"]), int(yo["H"])) == (W, H)
    
    # rows of the YOLO sheet that match gt["frame_index"], in the same order
    rows = np.searchsorted(yo["frame_index"], gt["frame_index"])
    assert (rows < len(yo["frame_index"])).all(), "GT frame not found in YOLO sheet"
    assert (yo["frame_index"][rows] == gt["frame_index"]).all(), "GT frame not found in YOLO sheet"
    
    y_xy = yo["coords"][rows][:, 5:17]  # (T, 12, 2) body-12
    y_cf = yo["confs"][rows][:, 5:17]   # (T, 12)
    n_det = yo["n_det"][rows]
    g_xy = gt["coords"]
    g_vis = gt["vis"]
    
    d = pixel_dists(g_xy, y_xy, W, H) # (T, 12)
    d_swap = pixel_dists(g_xy, y_xy[:, SWAP_LR], W, H) # GT L vs YOLO R and vice versa
    
    # boolean mask (T, 12): GT visible, YOLO confident, distance finite
    use = (g_vis == 0) & (y_cf >= CONF_MIN) & np.isfinite(d)
    
    print("n used:", int(use.sum()), "of", use.size)
    median = np.median(d[use]) if use.any() else float("nan")
    p90 = np.percentile(d[use], 90) if use.any() else float("nan")
    swap_median = np.median(d_swap[use]) if use.any() else float("nan")
    print(f"all joints : median {median:.1f} px, p90 {p90:.1f} px")
    print(f"L/R swapped: median {swap_median:.1f} px")
    for j, name in enumerate(JOINTS):
        m = use[:, j]
        if m.any():
            print(f"{name}: n={int(m.sum()):2d} median {np.median(d[m, j]):6.1f} px")
    for t, k in enumerate(gt["frame_index"]):
        m = use[t]
        med = np.median(d[t, m]) if m.any() else float("nan")
        print(f"frame {k}: n_det={int(n_det[t])} n={int(m.sum()):2d} median {med:6.1f} px")


if __name__ == "__main__":
    main() 
    

