#!/usr/bin/env python
"""overlay_frames.py -- draw the as-run sheets (condition A) and the ground truth on real frames, for the presentation.

Nothing is re-scored and no sheet is changed: the script reads the existing npz sheets and the GT, draws one method
per panel, and writes into the panel title the number of joints within 0.20 * L_ref (same rule as pck.py). Those
per-frame counts are new numbers: they are appended to <out-dir>/addendum_counts.csv and must be copied into
claude/ledger_addendum_<date>.md before they are used in a figure title or in speech. They are never used in tables.

Run in the `rugby` env from the repository root (PYTHONPATH=. so that phase2.pck is importable):

  PYTHONPATH=. python phase2/scripts/overlay_frames.py --clip P9201256 --frames 3314 --methods hybrik interp
  PYTHONPATH=. python phase2/scripts/overlay_frames.py --clip P9201256 --frames 3222 3236 3300 3380 --methods yolo --strip phases_yolo
  PYTHONPATH=. python phase2/scripts/overlay_frames.py --clip P9201256 --frames 3300 --mode circles --joint L_sho
  PYTHONPATH=. python phase2/scripts/overlay_frames.py --clip P9201256 --frames 3222 --mode graph
  PYTHONPATH=. python phase2/scripts/overlay_frames.py --clip P9201256 --frames 3236 --mode boxes
  PYTHONPATH=. python phase2/scripts/overlay_frames.py --clip PA041271 --frames 4440 4492 4504 4520 --mode frame --strip phases_PA041271
  PYTHONPATH=. python phase2/scripts/overlay_frames.py --clip P9201256 --list-keys

Modes
  points   (default) ground truth as circles + one method per panel (--methods ...; "all" = the five rows)
  circles  ground truth + the 0.20 L_ref and 0.10 L_ref circles around --joint (default L_sho)
  graph    the 12-joint skeleton graph (nodes + 12 edges) drawn from the detector sheet, no ground truth
  boxes    the tackler-track box and the carrier-track box of the frame (from the two assign sheets)
  frame    the frame only, with the phase name (thumbnails)

Symbols (fixed): ground truth = white circles, filled = Visible, hollow = Occluded, Out-of-frame not drawn;
detector = crosses, dark = confidence >= 0.5 (observed by the temporal methods), light = below 0.5;
every other method = its own colour, points joined by the 12 edges of the body-12 skeleton.

Frame source, in this order: outputs/20261018/<clip>_*/hybrik/raw_images (1080p PNGs written by the HybrIK demo),
the 1080p clip (data/clips/20261018/<clip>_*_1080p.mp4), the 4K master (data/raw/...). The clip-frame index is
frame - 1 - first_orig_0based, with first_orig_0based read from outputs/.../offset.txt (fallback: 3116 / 4321).
"""
import argparse
import csv
import glob
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from PIL import Image

try:
    from phase2.pck import load_gt, load_sheet, torso_length, PHASES, BODY12
except ImportError as exc:  # pragma: no cover
    sys.exit(f"phase2.pck is not importable -- run from the repository root with PYTHONPATH=. ({exc})")

# ----------------------------------------------------------------------------------------------------------------
# fixed names (condition A, as run)
# ----------------------------------------------------------------------------------------------------------------
HOME = Path.home()
REPO = Path(__file__).resolve().parents[2]            # phase2/scripts/overlay_frames.py -> repository root
NPZ = HOME / "data" / "phase2_npz"
GT_PATH = {"P9201256": HOME / "data" / "phase2_gt" / "gt_P9201256_tackler.npz",
           "PA041271": HOME / "data" / "phase2_gt" / "gt_PA041271_win4358_tackler.npz"}
WIN = {"P9201256": "win3162", "PA041271": "win4358"}
OUT_DATE = "20261018"                                  # HybrIK run of the final experiment day
DEFAULT_OFFSET = {"P9201256": 3116, "PA041271": 4321}  # first_orig_0based of the 10/18 clips; offset.txt overrides
RAW_4K = {"P9201256": REPO / "data" / "raw" / "20260920" / "P9201256.MOV",
          "PA041271": REPO / "data" / "raw" / "20261004" / "PA041271.MOV"}
W4K, H4K = 3840.0, 2160.0                              # every sheet and the GT are normalised to this frame
ALPHA_MAIN, ALPHA_STRICT = 0.20, 0.10

FIVE = ["yolo", "interp", "rts", "tgct", "hybrik"]
LABEL = {"yolo": "YOLO-Pose (detector only)", "interp": "Linear interpolation",
         "kalman": "Kalman filter (forward pass only)", "rts": "Kalman-RTS (constant velocity)",
         "tgct": "T-GCT", "hybrik": "HybrIK (anatomical prior)"}
COLOR = {"yolo": "#1f77b4", "interp": "#1f77b4", "kalman": "#7f7f7f", "rts": "#d62728",
         "tgct": "#ff7f0e", "hybrik": "#e377c2"}
PHASE_NAME = {"pre": "Approach", "contact": "Contact", "fusion": "Fusion", "fall": "Fall",
              "hold": "Hold", "post": "Post-hold"}
# BODY12 order: 0 L_sho 1 R_sho 2 L_elb 3 R_elb 4 L_wri 5 R_wri 6 L_hip 7 R_hip 8 L_kne 9 R_kne 10 L_ank 11 R_ank
EDGES12 = [(0, 1), (0, 2), (2, 4), (1, 3), (3, 5), (0, 6), (1, 7), (6, 7), (6, 8), (8, 10), (7, 9), (9, 11)]
assert len(EDGES12) == 12


def sheet_path(clip, method):
    d = NPZ / WIN[clip]
    return {"yolo": d / f"yolo_raw_{clip}_tackler_assign.npz",
            "carrier": d / f"yolo_raw_{clip}_carrier_assign.npz",
            "interp": d / f"interp_{clip}_A.npz",
            "kalman": d / f"kalman_{clip}_A.npz",
            "rts": d / f"rts_{clip}_A.npz",
            "tgct": d / f"tgct_v1_{clip}_A.npz",
            "hybrik": d / f"hybrik_struct_{clip}.npz"}[method]


# ----------------------------------------------------------------------------------------------------------------
# loading
# ----------------------------------------------------------------------------------------------------------------
def _find_key(z, candidates, ndim):
    for k in candidates:
        if k in z.files and np.ndim(z[k]) == ndim:
            return k
    return None


def load_conf_box(path):
    """Detector sheet -> (conf (N,12) or None, box (N,4) or None, frames (N,), keys). Key names are auto-detected."""
    with np.load(path, allow_pickle=True) as z:
        frames = z["frame_index"].astype(int)
        ck = _find_key(z, ["conf", "confs", "confidence", "confidences", "kp_conf", "scores", "score"], 2)
        conf = z[ck].astype(float) if ck else None
        if conf is not None and conf.shape[1] == 17:
            conf = conf[:, 5:17]                       # COCO -> body-12
        bk = _find_key(z, ["bbox", "box", "boxes", "bboxes", "xywh", "xyxy"], 2)
        box = z[bk].astype(float) if bk else None
        keys = list(z.files)
    if conf is None:
        print(f"  warning: no confidence array in {path.name} (keys: {keys}); crosses drawn as observed")
    return conf, box, frames, keys


def outputs_dir(clip):
    cands = sorted(glob.glob(str(REPO / "outputs" / OUT_DATE / f"{clip}_*")))
    return Path(cands[0]) if cands else None


def read_offset(clip):
    d = outputs_dir(clip)
    if d is not None and (d / "offset.txt").exists():
        txt = (d / "offset.txt").read_text()
        m = re.search(r"first_orig_0based\D*(\d+)", txt) or re.search(r"(\d+)", txt)
        if m:
            return int(m.group(1)), str(d / "offset.txt")
    return DEFAULT_OFFSET[clip], "built-in default (process_tackles 2026-10-18)"


def read_video_frame(path, idx):
    """Frame idx (0-based) of a video by sequential grabbing (exact; seeking can land on a keyframe)."""
    try:
        import cv2
    except ImportError:
        return None
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None
    for _ in range(idx):
        if not cap.grab():
            cap.release()
            return None
    ok, bgr = cap.read()
    cap.release()
    return Image.fromarray(bgr[:, :, ::-1]) if ok else None


def frame_image(clip, frame, offset_override=None):
    """Original 1-based frame number -> (PIL image, description of the source)."""
    off, src = (offset_override, "--offset") if offset_override is not None else read_offset(clip)
    idx = frame - 1 - off                               # 0-based index inside the 10/18 clip
    d = outputs_dir(clip)
    if d is not None:                                   # (A) raw_images of the HybrIK demo, 1-based %06d, sorted
        raw = [p for p in sorted(glob.glob(str(d / "hybrik" / "raw_images" / "*")))
               if p.lower().endswith((".png", ".jpg", ".jpeg"))]
        if raw and 0 <= idx < len(raw):
            return Image.open(raw[idx]).convert("RGB"), f"raw_images[{idx}] = {Path(raw[idx]).name} (offset {off}: {src})"
    clips = sorted(glob.glob(str(REPO / "data" / "clips" / OUT_DATE / f"{clip}_*_1080p.mp4")))
    if d is not None:
        clips += sorted(glob.glob(str(d / "*1080p*.mp4")))
    for c in clips:                                     # (B) the 1080p clip of the same run
        if idx >= 0:
            img = read_video_frame(c, idx)
            if img is not None:
                return img, f"{Path(c).name} frame {idx} (offset {off}: {src})"
    master = RAW_4K[clip]                               # (C) the 4K master, original numbering
    if master.exists():
        img = read_video_frame(master, frame - 1)
        if img is not None:
            return img, f"{master.name} frame {frame - 1} (0-based)"
    raise FileNotFoundError(f"no frame source for {clip} f{frame}: raw_images, 1080p clip and 4K master not found")


def phase_of(clip, frame):
    for name, lo, hi in PHASES[clip]:
        if lo <= frame <= hi:
            return PHASE_NAME.get(name, name)
    return "?"


def lref_of(gt):
    """Per-clip L_ref in 4K px: pck.torso_length (per-clip default), with the same rule as a fallback."""
    try:
        return float(np.asarray(torso_length(gt))[0])
    except Exception:                                   # pragma: no cover
        c, v = gt["coords"], gt["vis"]
        ok = (v[:, 0:2] < 2).all(1) & (v[:, 6:8] < 2).all(1)
        mid = np.linalg.norm(c[:, 0:2].mean(1) - c[:, 6:8].mean(1), axis=1)
        return float(np.median(mid[ok]))


def correct_count(pred_px, gt_px, vis, lref, alpha):
    """Same rule as pck.py: scored = vis < 2 and finite; correct = distance <= alpha * L_ref ((0,0) stays finite -> wrong)."""
    ok = (vis < 2) & np.isfinite(pred_px).all(-1) & np.isfinite(gt_px).all(-1)
    d = np.linalg.norm(pred_px - gt_px, axis=-1)
    return int(((d <= alpha * lref) & ok).sum()), int(ok.sum())


def row_of(sheet, frame):
    pos = np.where(sheet["frames"] == frame)[0]
    return int(pos[0]) if len(pos) else None


# ----------------------------------------------------------------------------------------------------------------
# drawing (all coordinates in 4K px, scaled by s to the image)
# ----------------------------------------------------------------------------------------------------------------
def drawable(pts):
    """(0,0) rows are no-detection placeholders: not drawn (they still count as wrong in correct_count)."""
    p = np.array(pts, float)
    p[(p == 0).all(-1)] = np.nan
    return p


def draw_gt(ax, gt_px, vis, s):
    for j in range(12):
        if vis[j] == 2 or not np.isfinite(gt_px[j]).all():
            continue
        x, y = gt_px[j] * s
        ax.plot(x, y, marker="o", ms=10, mfc=("white" if vis[j] == 0 else "none"), mec="white", mew=2.2,
                ls="none", zorder=6)


def draw_skeleton(ax, pts_px, color, s, lw=2.5, ms=6):
    p = drawable(pts_px)
    for a, b in EDGES12:
        if np.isfinite(p[[a, b]]).all():
            ax.plot(p[[a, b], 0] * s, p[[a, b], 1] * s, "-", color=color, lw=lw, zorder=3)
    if ms:
        ax.plot(p[:, 0] * s, p[:, 1] * s, "o", color=color, ms=ms, ls="none", zorder=4)


def draw_detector(ax, pts_px, conf, s):
    p = drawable(pts_px)
    hi = np.ones(12, bool) if conf is None else (np.asarray(conf) >= 0.5)
    draw_skeleton(ax, pts_px, "#1f77b4", s, lw=1.5, ms=0)
    ax.plot(p[hi, 0] * s, p[hi, 1] * s, "x", color="#1f77b4", ms=11, mew=3, ls="none", zorder=5)
    ax.plot(p[~hi, 0] * s, p[~hi, 1] * s, "x", color="#9ecae1", ms=11, mew=3, ls="none", zorder=5)


def box_xyxy(b, fmt):
    b = np.asarray(b, float)
    if b.size != 4 or not np.isfinite(b).all() or np.all(b == 0):
        return None
    if b.max() <= 1.5:
        b = b * np.array([W4K, H4K, W4K, H4K])
    if fmt == "cxcywh":
        cx, cy, w, h = b
        return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    return tuple(b)


# ----------------------------------------------------------------------------------------------------------------
# one panel
# ----------------------------------------------------------------------------------------------------------------
def panel(clip, frame, method, mode, out_dir, joint, box_format, offset, csv_rows):
    gt = load_gt(GT_PATH[clip])
    lref = lref_of(gt)
    gi = row_of({"frames": gt["frames"]}, frame)
    img, src = frame_image(clip, frame, offset)
    s = img.width / W4K
    fig, ax = plt.subplots(figsize=(img.width / 150, img.height / 150), dpi=150)
    ax.imshow(img)
    ax.set_axis_off()
    ph = phase_of(clip, frame)
    title = f"{clip} f{frame} {ph} -- "

    if mode == "frame":
        title = f"{clip} f{frame} -- {ph}"

    elif mode == "graph":
        sh = load_sheet(sheet_path(clip, "yolo"))
        i = row_of(sh, frame)
        if i is None:
            plt.close(fig)
            print(f"  skip: frame {frame} not in the detector sheet")
            return None
        draw_skeleton(ax, sh["coords"][i], "#ffd92f", s, lw=3, ms=9)
        title += "skeleton graph: 12 joints (nodes), 12 edges"

    elif mode == "boxes":
        for name, colr in (("yolo", "black"), ("carrier", "#2ca02c")):
            p = sheet_path(clip, name)
            if not p.exists():
                print(f"  warning: {p.name} missing; box not drawn")
                continue
            _, box, frames, keys = load_conf_box(p)
            if box is None:
                plt.close(fig)
                sys.exit(f"no box array in {p.name}; keys = {keys}. Pass the right sheet or add the key to load_conf_box.")
            pos = np.where(frames == frame)[0]
            xy = box_xyxy(box[int(pos[0])], box_format) if len(pos) else None
            lab = "tackler track" if name == "yolo" else "carrier track"
            if xy is None:
                ax.text(20, 40 + (40 if name == "carrier" else 0), f"{lab}: no box", color=colr, fontsize=11,
                        bbox=dict(fc="white", alpha=0.7, ec="none"))
                continue
            x1, y1, x2, y2 = (v * s for v in xy)
            ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, ec=colr, lw=3, zorder=4))
            ax.text(x1, max(y1 - 6, 12), lab, color=colr, fontsize=11, va="bottom",
                    bbox=dict(fc="white", alpha=0.7, ec="none"))
        title += "detector boxes of the two tracks (as run)"

    else:  # points / circles
        if gi is not None:
            draw_gt(ax, gt["coords"][gi], gt["vis"][gi], s)
        if mode == "circles":
            if gi is None:
                plt.close(fig)
                print(f"  skip: frame {frame} has no ground truth")
                return None
            j = BODY12.index(joint)
            x, y = gt["coords"][gi][j] * s
            for alpha, colr in ((ALPHA_MAIN, "white"), (ALPHA_STRICT, "yellow")):
                ax.add_patch(Circle((x, y), alpha * lref * s, fill=False, ec=colr, lw=2.2, ls="--", zorder=7))
            title += (f"{joint}: 0.20 L_ref = {ALPHA_MAIN * lref:.0f} px (white), "
                      f"0.10 L_ref = {ALPHA_STRICT * lref:.0f} px (yellow); L_ref = {lref:.1f} px")
        else:
            p = sheet_path(clip, method)
            if not p.exists():
                plt.close(fig)
                print(f"  skip: {p.name} does not exist")
                return None
            sh = load_sheet(p)
            i = row_of(sh, frame)
            if i is None:
                plt.close(fig)
                print(f"  skip: frame {frame} not in {p.name}")
                return None
            pts = sh["coords"][i]
            if method == "yolo":
                conf, _, cf, _ = load_conf_box(p)
                ci = np.where(cf == frame)[0]
                draw_detector(ax, pts, (conf[int(ci[0])] if conf is not None and len(ci) else None), s)
            else:
                draw_skeleton(ax, pts, COLOR[method], s)
            if gi is not None:
                n_ok, n = correct_count(pts, gt["coords"][gi], gt["vis"][gi], lref, ALPHA_MAIN)
                title += f"{LABEL[method]}: {n_ok}/{n} correct @0.20 (as run)"
                csv_rows.append([clip, frame, ph, method, n_ok, n, f"{ALPHA_MAIN * lref:.1f}"])
                print(f"ADDENDUM {clip} f{frame} {ph} {method} {n_ok}/{n} @0.20")
            else:
                title += f"{LABEL[method]} (no ground truth on this frame)"

    ax.set_xlim(0, img.width)                           # keep boxes / points outside the image from growing the figure
    ax.set_ylim(img.height, 0)
    ax.set_title(title, fontsize=9)
    stem = {"points": method, "circles": f"circles_{joint}", "graph": "graph", "boxes": "boxes", "frame": "frame"}[mode]
    out = Path(out_dir) / f"overlay_{clip}_f{frame}_{stem}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}   [frame from {src}]")
    return out


# ----------------------------------------------------------------------------------------------------------------
# strips, gif, csv
# ----------------------------------------------------------------------------------------------------------------
def make_strip(paths, out_path):
    ims = [Image.open(p).convert("RGB") for p in paths]
    h = min(im.height for im in ims)
    ims = [im.resize((int(im.width * h / im.height), h)) for im in ims]
    strip = Image.new("RGB", (sum(im.width for im in ims) + 8 * (len(ims) - 1), h), "white")
    x = 0
    for im in ims:
        strip.paste(im, (x, 0))
        x += im.width + 8
    strip.save(out_path)
    print(f"wrote {out_path}")


def make_gif(paths, out_path, duration_ms=80):
    ims = [Image.open(p).convert("P", palette=Image.ADAPTIVE) for p in paths]
    ims[0].save(out_path, save_all=True, append_images=ims[1:], duration=duration_ms, loop=0)
    print(f"wrote {out_path} ({len(ims)} frames)")


def append_csv(out_dir, rows):
    if not rows:
        return
    path = Path(out_dir) / "addendum_counts.csv"
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["clip", "frame", "phase", "method", "n_correct", "n_scored", "threshold_px"])
        w.writerows(rows)
    print(f"appended {len(rows)} rows to {path}")


def list_keys(clip):
    for m in ["yolo", "carrier", "interp", "kalman", "rts", "tgct", "hybrik"]:
        p = sheet_path(clip, m)
        if not p.exists():
            print(f"{m:8s} MISSING  {p}")
            continue
        with np.load(p, allow_pickle=True) as z:
            print(f"{m:8s} {p.name}: " + ", ".join(f"{k}{tuple(np.shape(z[k])) if np.ndim(z[k]) else ''}" for k in z.files))
    g = GT_PATH[clip]
    with np.load(g, allow_pickle=True) as z:
        print(f"{'gt':8s} {g.name}: " + ", ".join(f"{k}{tuple(np.shape(z[k])) if np.ndim(z[k]) else ''}" for k in z.files))
    off, src = read_offset(clip)
    d = outputs_dir(clip)
    nraw = len(glob.glob(str(d / "hybrik" / "raw_images" / "*"))) if d else 0
    print(f"outputs dir: {d}; offset {off} ({src}); raw_images: {nraw} files; 4K master: {RAW_4K[clip].exists()}")


# ----------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clip", required=True, choices=sorted(WIN))
    ap.add_argument("--frames", type=int, nargs="*", default=[], help="original 1-based frame numbers")
    ap.add_argument("--methods", nargs="*", default=["yolo"], help="yolo interp kalman rts tgct hybrik, or all")
    ap.add_argument("--mode", default="points", choices=["points", "circles", "graph", "boxes", "frame"])
    ap.add_argument("--joint", default="L_sho", choices=BODY12, help="circles mode: joint to draw the circles around")
    ap.add_argument("--box-format", default="cxcywh", choices=["cxcywh", "xyxy"], help="boxes mode: layout of the box array")
    ap.add_argument("--offset", type=int, default=None, help="override first_orig_0based (clip frame 0 = this original 0-based frame)")
    ap.add_argument("--out-dir", default="phase2/results/final_v4/figures/pres")
    ap.add_argument("--strip", default=None, help="also join the panels of this run side by side into strip_<name>.png")
    ap.add_argument("--gif", default=None, help="also save the panels of this run as <name>.gif (80 ms per frame)")
    ap.add_argument("--list-keys", action="store_true", help="print the npz keys and the frame sources, then exit")
    a = ap.parse_args()

    if a.list_keys:
        list_keys(a.clip)
        return
    if not a.frames:
        ap.error("--frames is required (unless --list-keys)")
    methods = []
    for m in a.methods:                                 # "all" expands to the five rows; names are validated here
        for mm in (FIVE if m == "all" else [m]):
            if mm not in LABEL:
                ap.error(f"unknown method {mm!r}; choose from {list(LABEL)} or 'all'")
            if mm not in methods:
                methods.append(mm)
    if a.mode != "points":
        methods = [methods[0] if methods else "yolo"]

    made, rows = [], []
    for f in a.frames:
        for m in methods:
            out = panel(a.clip, f, m, a.mode, a.out_dir, a.joint, a.box_format, a.offset, rows)
            if out is not None:
                made.append(out)
    append_csv(a.out_dir, rows)
    if a.strip and made:
        make_strip(made, Path(a.out_dir) / f"strip_{a.strip}.png")
    if a.gif and made:
        make_gif(made, Path(a.out_dir) / f"{a.gif}.gif")


if __name__ == "__main__":
    main()