"""Answer sheets of the classical temporal baselines (interp / kalman / rts) from a verified YOLO sheet (worksheet ex. c).
sigma_m (detector floor, D6) and sigma_a (hide-and-predict, D7) are read from temporal_params. Run in `rugby`:
   python phase2/scripts/make_temporal_sheets.py <sheet_dir> <stem> [--person tackler_verified]"""
import argparse, json, sys, numpy as np
from pathlib import Path
sys.path.append(str(Path.home() / "rugby-video-analytics"))
from phase2.temporal import smooth_sheet, observed_mask

BODY12 = list(range(5, 17))
NAMES = np.array(["L_sho", "R_sho", "L_elb", "R_elb", "L_wri", "R_wri", "L_hip", "R_hip", "L_kne", "R_kne", "L_ank", "R_ank"])
PARAMS = Path("phase2/results/temporal_params_P9201256.json")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet_dir")
    ap.add_argument("stem")
    ap.add_argument("--person", default="tackler_verified")
    ap.add_argument("--sigma-a", type=float, default=None, help="override for a labelled sensitivity run (NOT adopted)")
    ap.add_argument("--suffix", default="", help="output name suffix for sensitivity runs, e.g. _sa1e-3")
    args = ap.parse_args()
    d = Path(args.sheet_dir).expanduser()
    params = json.loads(PARAMS.read_text())
    sigma_m = float(params["sigma_m"])
    sigma_a = float(params["sigma_a"]) if args.sigma_a is None else args.sigma_a
    input_name = f"yolo_raw_{args.stem}_{args.person}.npz"
    with np.load(d / input_name, allow_pickle=False) as z:
        required = ("coords", "confs", "frame_index", "fps", "W", "H")
        missing = [name for name in required if name not in z.files]
        if missing:
            raise ValueError(f"{d / input_name} is missing required arrays: {', '.join(missing)}")
        raw_coords, raw_confs = z["coords"], z["confs"]
        if raw_coords.ndim != 3 or raw_coords.shape[1] <= BODY12[-1] or raw_coords.shape[2] != 2:
            raise ValueError(f"coords must have shape (T, at least 17, 2), got {raw_coords.shape}")
        if raw_confs.ndim != 2 or raw_confs.shape != raw_coords.shape[:2]:
            raise ValueError(f"confs must match coords' first two dimensions, got {raw_confs.shape}")
        if z["frame_index"].shape != (len(raw_coords),):
            raise ValueError("frame_index must align with coords")
        metadata = {name: z[name] for name in ("frame_index", "fps", "W", "H")}
        coords = raw_coords[:, BODY12].astype(float)
        confs = raw_confs[:, BODY12].astype(float)

    obs = observed_mask(coords, confs)
    print(f"{args.stem}/{args.person}: T={len(coords)}  observed joint-frames={int(obs.sum())}/{obs.size}  "
          f"per-joint min={int(obs.sum(0).min())}  sigma_m={sigma_m:.5f}  sigma_a={sigma_a:.0e}")
    if np.any(obs.sum(axis=0) == 0):
        raise SystemExit("a joint has no observation in this window -> report before continuing")

    out = smooth_sheet(coords, confs, sigma_a, sigma_m)
    for key, src in (("interp", "interp"), ("kalman", "filt"), ("rts", "smooth")):
        output_path = d / f"{key}_{args.stem}{args.suffix}.npz"
        np.savez(
            output_path,
            coords=out[src].astype(np.float32),
            confs=confs.astype(np.float32),
            **metadata,
            joint_names=NAMES,
            source=key,
            input=f"yolo_raw_{args.stem}_{args.person}",
            sigma_a=sigma_a,
            sigma_m=sigma_m,
        )
        print("saved", output_path)


if __name__ == "__main__":
    main()