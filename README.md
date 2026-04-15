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

## Key Results

- **YOLO-Pose outperforms MediaPipe** in tackle scenarios (mean confidence: 0.857 vs 0.722), especially for upper-limb keypoints (wrist: 0.729 vs 0.312).
- **GCT refinement** achieves ~5% jitter reduction on wrist keypoints overall, but remains limited under severe simultaneous occlusion.
- **Phase detection consistency** is preserved: both YOLO and YOLO+GCT identify the same impact frame (t = 2.63s).

## Technical Stack

- **Python 3.13**, PyTorch 2.10
- **YOLO**: Ultralytics YOLOv11s-pose
- **MediaPipe**: Google MediaPipe Pose
- **GCT**: Custom implementation (PyTorch) — Graph Convolution + Multi-Head Attention + Sigmoid Gating
- **Report**: LaTeX (Overleaf compatible)

## References

1. Ji, C., Zhong, Y., & Gao, M. (2025). Multimodal fusion approach for sports injury prevention and pose keypoint detection. *PLOS ONE*, 20(8).
2. Kipf, T. N. & Welling, M. (2017). Semi-Supervised Classification with Graph Convolutional Networks. *ICLR*.
3. Vaswani, A. et al. (2017). Attention Is All You Need. *NeurIPS*.
4. Dwivedi, V. P. & Bresson, X. (2021). A Generalization of Transformer Networks to Graphs. *AAAI Workshop*.

## License

This project is for academic purposes as part of the NUS Capstone programme.
