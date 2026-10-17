# phase2/tgct/infer.py
"""Test sheet (60 fps, 17 joints, identity-verified) -> T-GCT answer sheet (even frames, body-12), worksheet exercise e.
Run in rugby, from the repo root:
    python -m phase2.tgct.infer --sheet ~/data/phase2_npz/win3162/yolo_raw_P9201256_tackler_verified.npz \
        --ckpt ~/data/tgct/ckpt/v1_best.pt --out ~/data/phase2_npz/win3162/tgct_v1_P9201256.npz
"""
import argparse
from pathlib import Path
import numpy as np
import torch
from phase2.temporal import observed_mask
from phase2.tgct.graph import body12_A_norm, COCO_IDX_BODY12, BODY12
from phase2.tgct.model import TGCT
from phase2.tgct.data import center, fill_and_features

INVALID_VERDICTS = ("no_valid", "fused")       # adjust to the exact strings seen in step e-1 work 1

def load_test_window(sheet, oracle_gt=None):
    """60 fps sheet -> even frames, body-12. Returns dict(coords (N,12,2), confs (N,12), obs (N,12) bool, frame_index, meta)."""
    z = np.load(sheet, allow_pickle=True)
    fi = z["frame_index"]
    even = fi % 2 == 0
    coords = z["coords"][even][:, COCO_IDX_BODY12]
    confs = z["confs"][even][:, COCO_IDX_BODY12]
    valid = ~np.isin(z["identity_verdict"][even], INVALID_VERDICTS) if "identity_verdict" in z.files else np.ones(even.sum(), bool)
    obs = observed_mask(coords, confs) & valid[:, None]
    if oracle_gt is not None:                                     # oracle occlusion: what the GT annotator marked hidden becomes unknown
        g = np.load(oracle_gt)
        pos = {int(f): i for i, f in enumerate(fi[even])}
        for f, vis in zip(g["frame_index"], g["vis"]):
            if int(f) in pos:
                obs[pos[int(f)]] &= (vis == 0)
    meta = dict(fps=float(z["fps"]), W=int(z["W"]), H=int(z["H"]), person=str(z["person"]))
    return dict(coords=coords, confs=confs, obs=obs, frame_index=fi[even], meta=meta)

@torch.no_grad()
def run_tgct(win, ckpt):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ck = torch.load(ckpt, map_location=device, weights_only=True)
    T, stride = ck["args"]["T"], ck["args"]["stride"]
    model = TGCT(max_len=max(256, ck["args"]["T"])).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    A = torch.as_tensor(body12_A_norm()).to(device)
    coords_c, c = center(win["coords"], win["obs"])
    feats, fill = fill_and_features(coords_c, win["obs"], win["confs"])
    res = model(torch.from_numpy(feats[None]).to(device), A)[0].cpu().numpy()
    coords_out = fill + res + c
    return coords_out, fill + c, res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", default=None, help="label stored in the sheet (default: ckpt tag, e.g. tgct_v1)")
    ap.add_argument("--oracle-gt", default=None, help="DIAGNOSTIC ONLY: GT npz; joints with vis!=0 are hidden on the input")
    ap.add_argument("--also-interp", default=None, help="also save the interpolation of the same mask as a sheet")
    args = ap.parse_args()

    win = load_test_window(Path(args.sheet).expanduser(), Path(args.oracle_gt).expanduser() if args.oracle_gt else None)
    N = len(win["frame_index"])
    print(f"even frames {N}  frame_index {win['frame_index'].min()}..{win['frame_index'].max()}  "
          f"observed joint-frames {int(win['obs'].sum())}/{N * 12} ({win['obs'].mean():.3f})")
    coords_out, interp, res = run_tgct(win, Path(args.ckpt).expanduser())
    source = args.source or f"tgct_{Path(args.ckpt).stem.replace('_best', '')}"
    confs_out = np.where(win["obs"], win["confs"], 0.0).astype(np.float32)
    np.savez(Path(args.out).expanduser(),
             coords=coords_out.astype(np.float32), confs=confs_out, frame_index=win["frame_index"],
             obs=win["obs"], interp=interp.astype(np.float32), residual=res.astype(np.float32),
             joint_names=np.array(BODY12), fps_effective=win["meta"]["fps"] / 2,
             W=win["meta"]["W"], H=win["meta"]["H"], person=win["meta"]["person"], source=source)
    print(f"saved {args.out}  ({source})  max |residual| = {np.abs(res).max():.4f}  "
          f"mean |residual| on unobserved = {np.abs(res[~win['obs']]).mean() if (~win['obs']).any() else 0:.4f}")
    if args.also_interp:
        np.savez(Path(args.also_interp).expanduser(), coords=interp.astype(np.float32), frame_index=win["frame_index"],
                 obs=win["obs"], joint_names=np.array(BODY12), source="interp_oracle")


if __name__ == "__main__":
    main()

