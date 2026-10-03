"""Convert a CVAT for images 1.1 XML export into the ground-truth sheet (.npz)."""
import argparse
import json
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import numpy as np

JOINTS = ["L_sho", "R_sho", "L_elb", "R_elb", "L_wri", "R_wri",
          "L_hip", "R_hip", "L_kne", "R_kne", "L_ank", "R_ank"]  # COCO 5..16


def parse_point(el):
    """Return (label, x, y, vis) for one <points> element.

    vis: 0 visible / 1 occluded / 2 outside.
    """
    label = el.get("label")
    x, y = map(float, el.get("points").split(","))
    vis = 2 if el.get("outside") == "1" else 1 if el.get("occluded") == "1" else 0
    return label, x, y, vis

def load_cvat(xml_path, max_frame=None):
    """Return frame_index (T,), xy_crop (T, 12, 2) in crop pixels, vis (T, 12)."""
    root = ET.parse(xml_path).getroot()
    frames, xy_list, vis_list = [], [], []
    for image in root.iter("image"):
        k = int(Path(image.get("name")).stem) # "003222.jpg" -> 3222
        if max_frame is not None and k > max_frame:
            continue
        skeletons = image.findall("skeleton")
        assert len(skeletons) == 1, f"frame {k}: expected 1 skeleton, got {len(skeletons)}"
        xy = np.full((len(JOINTS), 2), np.nan)
        vis = np.full(len(JOINTS), -1, dtype=np.int8)
        for el in skeletons[0].iter("points"):
            label, x, y, v = parse_point(el)
            j = JOINTS.index(label)
            xy[j] = [x, y]
            vis[j] = v
        assert(vis >= 0).all(), f"frame {k}: missing joints"
        frames.append(k)
        xy_list.append(xy)
        vis_list.append(vis)
    order = np.argsort(frames)
    return np.array(frames)[order], np.stack(xy_list)[order], np.stack(vis_list)[order]

def to_normalized(xy_crop, vis, crop_origin, W, H):
    """Crop pixels -> full-frame normalized coords (x/W, y/H); NaN where vis == 2."""
    coords = xy_crop + np.asarray(crop_origin, dtype=float)
    coords[..., 0] /= W
    coords[..., 1] /= H
    coords[vis == 2] = np.nan
    return coords.astype(np.float32)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-frame", type=int, default=None)
    args = ap.parse_args()

    meta = json.loads(Path(args.meta).read_text())
    W, H = meta["W"], meta["H"]
    frame_index, xy_crop, vis = load_cvat(args.xml, args.max_frame)
    coords = to_normalized(xy_crop, vis, meta["crop_origin"], W, H)

    same = (xy_crop[1:] == xy_crop[:-1]).all(axis=(1, 2))
    for k in frame_index[1:][same]:
        print(f"WARNING: frame {k} is identical to the previous frame (not annotated?)")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.out, coords=coords, vis=vis, frame_index=frame_index,
             crop_origin=np.array(meta["crop_origin"]), W=W, H=H,
             person="tackler", clip=meta["clip"], annotator="Yu", date=str(date.today()))
    print("T:", len(frame_index), "frames", frame_index[0], "-", frame_index[-1])
    print("vis counts (0/1/2):", [int((vis == v).sum()) for v in (0, 1, 2)])
    print("x range:", np.nanmin(coords[..., 0]), np.nanmax(coords[..., 0]))
    print("y range:", np.nanmin(coords[..., 1]), np.nanmax(coords[..., 1]))


if __name__ == "__main__":
    main()