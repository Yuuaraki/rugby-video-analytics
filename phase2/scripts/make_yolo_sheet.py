"""Make the raw-YOLO answer sheet for tackle_01 in the common .npz format. Run in the `rugby` env."""
import sys
from pathlib import Path
import numpy as np
sys.path.append(str(Path.home() / "rugby-video-analytics"))
from phase2.extract import extract_keypoints_from_video   # verbatim port of Phase 1 (cells 15-16)

VIDEO = Path.home() / "HybrIK/data/Rugby_tackle_occlusion_1.mp4"   # tackle_01: 126 frames, 3840x2160
OUT   = Path.home() / "data/phase2_npz/yolo_raw_tackle_01.npz"
COCO17 = ["nose","l_eye","r_eye","l_ear","r_ear","l_sho","r_sho","l_elb","r_elb",
          "l_wri","r_wri","l_hip","r_hip","l_kne","r_kne","l_ank","r_ank"]

coords, confs, gt_indices, fps = extract_keypoints_from_video(str(VIDEO))
print(coords.shape, confs.shape)                       # expect (126, 17, 2) (126, 17)
assert coords.shape == (126, 17, 2) and confs.shape == (126, 17)

np.savez(OUT, coords=coords.astype(np.float32), confs=confs.astype(np.float32),
         fps=30.0, W=3840, H=2160, joint_names=np.array(COCO17), source="yolo_raw")
print("saved", OUT)