# ported verbatim from notebooks/Skelton_graph_GCN.ipynb cell 15
import cv2
import numpy as np
from ultralytics import YOLO

# ported verbatim from notebooks/Skelton_graph_GCN.ipynb cell 15
YOLO26_MODEL_NAME = 'yolo26s-pose.pt'

# ported verbatim from notebooks/Skelton_graph_GCN.ipynb cell 16
yolo_det = YOLO(YOLO26_MODEL_NAME)


# ported verbatim from notebooks/Skelton_graph_GCN.ipynb cell 16
def extract_keypoints_from_video(video_path, conf_threshold=0.4):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video opened: {total_frames} frames, {W}x{H} @ {fps: .2f} FPS")
    
    all_frame_coords = []
    all_frame_confs = []
    gt_indices = []

    fi = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        res = yolo_det(frame, verbose=False, conf=0.1)[0]
        ok = (
            res.keypoints is not None
            and res.keypoints.data is not None
            and len(res.keypoints.data) > 0
        )

        if ok:
            pid = 0
            if res.boxes is not None and len(res.boxes.xyxy) > 1:
                bx = res.boxes.xyxy.detach().cpu().numpy()
                pid = int(np.argmax((bx[:, 2] - bx[:, 0]) * (bx[:, 3] - bx[:, 1])))  # Largest box = main player

            kp = res.keypoints.data[pid].detach().cpu().numpy()  # [17, 3]
            co = np.stack([kp[:, 0] / W, kp[:, 1] / H], axis=-1).astype(np.float32)  # Normalize to [0,1]
            cf = kp[:, 2].astype(np.float32)
            all_frame_coords.append(co)
            all_frame_confs.append(cf)

            if cf.min() >= conf_threshold:
                gt_indices.append(len(all_frame_coords) - 1)  # Index of GT frames
        else:
            all_frame_coords.append(np.zeros((17, 2), dtype=np.float32))
            all_frame_confs.append(np.zeros(17, dtype=np.float32))

        fi += 1
        if fi % 30 == 0:
            print(f"Processed {fi}/{total_frames} frames, GT frames so far: {len(gt_indices)}", end='\r')

    cap.release()

    all_frame_coords = np.array(all_frame_coords)  # [num_frames, 17, 2]
    all_frame_confs = np.array(all_frame_confs)    # [num_frames, 17]
    print(f"\nFinished processing video. Total GT frames: {len(gt_indices)}")

    return all_frame_coords, all_frame_confs, gt_indices, fps