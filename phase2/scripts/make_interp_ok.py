"""interp_ok sheet : the linear-interpolation sheet with the SAME frames blanked (NaN)
as hybrik_struct_ok, so that the two rows are scored on one denominator. Run in `rugby`.
  python phase2/scripts/make_interp_ok.py --clip P9201256 --dir ~/data/phase2_npz/win3162"""
import argparse
from pathlib import Path
import numpy as np


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--clip", required=True); ap.add_argument("--dir", required=True)
    args = ap.parse_args(); d = Path(args.dir).expanduser()
    with np.load(d / f"hybrik_struct_ok_{args.clip}.npz", allow_pickle=True) as z:
        ok_frames = z["frame_index"].astype(int); person_ok = z["person_ok"].astype(bool)
        nan_rows = np.isnan(z["coords"]).all(axis=(1, 2))
    assert np.array_equal(nan_rows, ~person_ok), "hybrik_struct_ok: NaN rows differ from ~person_ok"
    with np.load(d / f"interp_{args.clip}.npz", allow_pickle=True) as z:
        sheet = {k: z[k] for k in z.files}
    coords = sheet["coords"].astype(float)
    interp_frames = sheet["frame_index"].astype(int); not_ok = ok_frames[~person_ok]
    # every not-ok frame must exist exactly once in the interp sheet (a count check alone lets a miss and a duplicate cancel out)
    assert all((interp_frames == f).sum() == 1 for f in not_ok), "a not-ok frame is missing or duplicated in the interp sheet"
    mask = np.isin(interp_frames, not_ok); coords[mask] = np.nan
    assert mask.sum() == len(not_ok)
    sheet["coords"] = coords; sheet["source"] = "interp_ok"; sheet["person_ok_from"] = f"hybrik_struct_ok_{args.clip}.npz"
    np.savez(d / f"interp_ok_{args.clip}.npz", **sheet)
    print(args.clip, "interp frames", len(coords), "blanked", int(mask.sum()), "not-ok in hybrik sheet", int((~person_ok).sum()))


if __name__ == "__main__":
    main()