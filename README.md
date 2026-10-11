# Rugby Video Analytics: AI-Based Tackle Analysis Robust to Keypoint Occlusion

**Capstone Project — National University of Singapore**

## Overview

This project develops an AI-based coaching pipeline for rugby tackle analysis that is robust to keypoint occlusion. The system combines YOLO-Pose for base keypoint detection with a Graph Convolutional Transformer (GCT) for spatial refinement of occluded joints.

### Pipeline Architecture

```
Input Video → YOLO-Pose (17 keypoints) → GCT Refinement → Confidence-Aware Blending → Refined Pose
```

## Repository Structure

```
rugby-video-analytics/
├── README.md
├── .gitignore
├── notebooks/
│   ├── media_pipe.ipynb          # Stage 1: MediaPipe pose estimation
│   ├── Yolo_-_26.ipynb           # Stage 1: YOLO-Pose estimation & comparison
│   └── Skelton_graph_GCN.ipynb   # Stage 2: GCT implementation & training
└── report/
    ├── tex/
    │   ├── main.tex              # Interim report (LaTeX source)
    │   └── sample.bib            # Bibliography
    └── figures/
        ├── GCT_layer_architecture.png
        ├── confidence_timeline_plot.png
        └── phase_detection_comparison.png
```

## Notebooks

| Notebook | Stage | Description |
|----------|-------|-------------|
| `media_pipe.ipynb` | Stage 1 | MediaPipe Pose estimation on rugby tackle video. Extracts 33 keypoints per frame and computes joint angles, trunk inclination, and joint speeds. |
| `Yolo_-_26.ipynb` | Stage 1 | YOLOv11s-Pose estimation and quantitative comparison with MediaPipe. Analyses confidence scores across 17 COCO keypoints with focus on occlusion phases. |
| `Skelton_graph_GCN.ipynb` | Stage 2 | Full GCT pipeline: skeleton graph construction → GCN layer → Multi-Head Attention → Gating Mechanism → self-supervised training with masked keypoints → evaluation on tackle video. |

## Technical Stack

- **Python 3.13**, PyTorch 2.10
- **YOLO**: Ultralytics YOLOv11s-pose
- **MediaPipe**: Google MediaPipe Pose
- **GCT**: Custom implementation (PyTorch) — Graph Convolution + Multi-Head Attention + Sigmoid Gating
- **Report**: LaTeX (Overleaf compatible)

## Raw-video duplicate-frame QC

Run the read-only check with OpenCV and NumPy installed:

```sh
python phase2/video_qc.py data/raw/20261004/PA041264.MOV
python phase2/video_qc.py data/raw/20261004/PA041264.MOV --max-frames 120
python phase2/video_qc.py data/raw/20261004/PA041264.MOV --tail 0
python -m unittest phase2.tests.test_video_qc
```

The check samples every fourth pixel without averaging, converts to grayscale,
and subtracts signed values. It flags adjacent pairs with mean absolute
difference strictly below `--ratio` (default 0.3) times the body's P90.
`--tail` defaults to 30: the last 30 pairs are excluded from the body and
counted separately against the same body-derived threshold. `dup` and
`rate%` describe only the body; the denominator is `N - 1 - tail` pairs,
not frames. `tail_dup` is the number of flagged tail pairs. `min_d`, `p90_d`,
and `min/p90` describe the body only; reported indices are 1-based
later-frame candidates in the body. For N decoded frames, the last 30 pairs
correspond to later frames N-29 through N, including the body/tail boundary
comparison. `--tail 0` restores whole-clip statistics and sets `tail_dup` to 0.
`--max-frames 0` reads the entire video; with a positive limit, the tail is
relative to the decoded prefix, not necessarily the original video's end.

Negative tail values, a tail that leaves no body pairs, fewer than two decoded
frames, or body P90 equal to zero produce an explicit error, not a misleading
0% result. The default requires at least 32 decoded frames.
The relative rule is unreliable for bodies dominated
by duplicates (roughly 90% or more), and low differences alone do not prove a
frame was copied. Lossy compression can suppress genuine-frame noise and
cause false positives even when the baseline has no flagged pairs.

For a known-answer check, encode the first two seconds at 30000/1001 fps as a
baseline, then repeat each baseline frame at 60000/1001 fps and re-encode it.
Do not resize either clip. Store derivatives in a temporary directory and
remove them after checking. For 60 baseline frames repeated twice, there are
60 duplicate pairs out of 119 pairs: **50.42%**, not exactly 50%.

Use a lossless baseline to avoid an extra lossy generation:

```sh
qc_dir=$(mktemp -d /tmp/rugby-video-qc-XXXXXX)
trap 'rm -f "$qc_dir/baseline.mkv" "$qc_dir/duplicated.mkv"; rmdir "$qc_dir"' EXIT
ffmpeg -nostdin -i data/raw/20261004/PA041264.MOV -t 2 -map 0:v:0 \
  -vf fps=30000/1001 -an -c:v ffv1 "$qc_dir/baseline.mkv"
ffmpeg -nostdin -i "$qc_dir/baseline.mkv" -map 0:v:0 \
  -vf fps=60000/1001 -an -c:v ffv1 "$qc_dir/duplicated.mkv"
python phase2/video_qc.py "$qc_dir/baseline.mkv" "$qc_dir/duplicated.mkv" --tail 0
```

The following historical whole-clip results correspond to `--tail 0`.
On PA041264's first two seconds, a lossless 29.97 fps baseline had 0 flagged
pairs. Its lossless repeated clip flagged exactly 60 of 119 pairs (50.42%),
with candidates at every even frame from 2 through 120. H.264 recompression
with `libx264 -crf 10 -preset fast` also matched all 60 copy indices, despite
nonzero differences on copied pairs. Encoding with H.264 (`libx264`,
`-crf 18 -preset fast`) flagged 63 of 119 pairs (52.94%): all 60 true copies
plus 3 false positives. This is a limitation of the prescribed relative
threshold, not evidence of 63 actual copied frames.

## Solo-footage answer sheet

Build one person's time series from completed per-frame YOLO pose labels:

```sh
python phase2/scripts/solo_sheet.py <labels_dir> <stem> <n_frames> \
  --out-dir ~/data/phase2_npz --runs-dir phase2/results
python -m unittest phase2.tests.test_solo_sheet -v
```

Each `<stem>_<n>.txt` uses the original 1-based frame number and must contain
57 values per detection: class, normalized `(cx, cy, w, h)`, 17 `(x, y, conf)`
triples, and box confidence. Candidates must satisfy both horizontal edge
conditions `cx - w/2 >= edge_eps`, `cx + w/2 <= 1 - edge_eps`, and the size
condition `sqrt((w * width) * (h * height)) >= min_size`. The default
`--edge-eps` is 0.005 and `--min-size` is provisionally 400 px; choose the
final size threshold from the five clips' edge-filtered size distributions,
not from an assumed valley. Only left/right edges are gated.
The highest-box-confidence candidate is selected, not the highest-confidence
row among all detections.
Missing or empty files mean no detection; malformed rows are errors, not
silently discarded. The labels directory must exist. Run after inference
finishes so missing files are not mistaken for not-yet-written detections.

The output `yolo_raw_<stem>_solo.npz` retains all N frames, including the tail,
with float32 `coords (N,17,2)`, `confs (N,17)`, `bbox (N,4)`, integer `n_det`
and `n_cand` (all detections and gated candidates respectively)
and original `frame_index`, plus `fps`, `W`, `H`, the existing COCO17 joint
names, `source="yolo_raw"`, `person="solo"`, and `tail`, `tau`, `win`,
`min_size`, `edge_eps` metadata.
Frames with no candidates have zero coordinates, confidences and bounding boxes;
their frame indices are still retained. Set `--fps`, `--width` and `--height`
to the source video's metadata (defaults: 60000/1001, 3840, 2160).

Visibility reuses `temporal.observed_mask(coords, confs, tau)` and requires
all body-12 joints (COCO indices 5 through 16) to be observed and exactly
one gated candidate (`n_cand == 1`); face joints
are not required. `--tail 30` excludes the last 30 frames from runs only.
`--tail 0` excludes none; a tail at least as large as N leaves no runs.
`solo_runs_<stem>.csv` lists maximal visible runs using inclusive, original
1-based `start` and `end`, `length`, and `n_flag` (frames with `n_det != 1`).
Multiple raw detections may remain in runs if only one passes the gates,
and are flagged via `n_flag`. Frames with multiple candidates break runs,
but their selected pose and counts remain in the NPZ. Highest confidence
alone does not guarantee stable identity; downstream training must respect
the run eligibility rather than using joint confidence alone.

The console reports fully visible frames and, for runs of length L at least
`--win` (default 60), the total `L - win + 1` sliding windows. Overlapping
windows are not independent samples: the qualifying frame total divided by
the window length is only a rough information-volume estimate.

## References

1. Ji, C., Zhong, Y., & Gao, M. (2025). Multimodal fusion approach for sports injury prevention and pose keypoint detection. *PLOS ONE*, 20(8).
2. Kipf, T. N. & Welling, M. (2017). Semi-Supervised Classification with Graph Convolutional Networks. *ICLR*.
3. Vaswani, A. et al. (2017). Attention Is All You Need. *NeurIPS*.
4. Dwivedi, V. P. & Bresson, X. (2021). A Generalization of Transformer Networks to Graphs. *AAAI Workshop*.
