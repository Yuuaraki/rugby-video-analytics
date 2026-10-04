"""Apply annotation-chat identity verdicts to the tackler sheet; the carrier sheet is read-only.
Run in `rugby` from ~/rugby-video-analytics:
   python phase2/scripts/apply_identity_fix.py <sheet_dir> <csv> [--stem P9201256] [--fill-odd]
Writes <sheet_dir>/yolo_raw_<stem>_tackler_verified.npz"""
import argparse, csv, numpy as np
from pathlib import Path

VERDICTS = ("ok", "swap", "fused", "no_valid")
IDENTITY_FIELDS = ("coords", "confs", "bbox")


def _load_sheet(path, label):
    with np.load(path, allow_pickle=False) as archive:
        sheet = {name: archive[name] for name in archive.files}

    required = ("frame_index", *IDENTITY_FIELDS)
    missing = [name for name in required if name not in sheet]
    if missing:
        raise ValueError(f"{label} sheet {path} is missing required arrays: {', '.join(missing)}")

    frames = sheet["frame_index"]
    if frames.ndim != 1:
        raise ValueError(f"{label} sheet frame_index must be one-dimensional")
    if len(np.unique(frames)) != len(frames):
        raise ValueError(f"{label} sheet frame_index contains duplicates")
    for name in IDENTITY_FIELDS:
        if sheet[name].ndim == 0 or sheet[name].shape[0] != len(frames):
            raise ValueError(f"{label} sheet {name} does not align with frame_index")
    return sheet


def _read_verdicts(csv_path):
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        required = {"frame", "verdict"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{csv_path} must have CSV columns: frame, verdict")

        rows = {}
        for line, row in enumerate(reader, start=2):
            try:
                frame = int(row["frame"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{csv_path}:{line}: frame must be an integer") from exc
            verdict = (row["verdict"] or "").strip()
            if verdict not in VERDICTS:
                raise ValueError(f"{csv_path}:{line}: unknown verdict {verdict!r}; expected one of {VERDICTS}")
            if frame in rows:
                raise ValueError(f"{csv_path}:{line}: duplicate verdict for frame {frame}")
            rows[frame] = (verdict, row.get("basis") or "")
    return rows


def _apply_verdicts(tackler, carrier, decisions):
    frames = tackler["frame_index"]
    carrier_frames = carrier["frame_index"]
    tackler_index = {int(frame): i for i, frame in enumerate(frames)}
    carrier_index = {int(frame): i for i, frame in enumerate(carrier_frames)}
    verdicts = ["ok"] * len(frames)
    bases = [""] * len(frames)

    for frame, (verdict, basis) in decisions.items():
        i = tackler_index.get(frame)
        if i is None:
            print(f"Warning: frame {frame} not found in the tackler sheet")
            continue

        verdicts[i] = verdict
        bases[i] = basis
        if verdict == "swap":
            j = carrier_index.get(frame)
            if j is None:
                raise ValueError(f"frame {frame} has verdict 'swap' but is missing from the carrier sheet")
            for name in IDENTITY_FIELDS:
                if tackler[name].shape[1:] != carrier[name].shape[1:]:
                    raise ValueError(f"tackler and carrier {name} arrays have incompatible shapes")
                tackler[name][i] = carrier[name][j]
        elif verdict in ("fused", "no_valid"):
            for name in IDENTITY_FIELDS:
                tackler[name][i] = 0

    return np.asarray(verdicts, dtype=str), np.asarray(bases, dtype=str)


def _fill_unlisted_frames(frames, decisions):
    filled = dict(decisions)
    for frame in map(int, frames):
        if frame in decisions or (frame - 1) not in decisions or (frame + 1) not in decisions:
            continue
        left_verdict, right_verdict = decisions[frame - 1][0], decisions[frame + 1][0]
        if left_verdict == right_verdict:
            filled[frame] = (left_verdict, "filled from neighbours")
    return filled


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet_dir"); ap.add_argument("csv"); ap.add_argument("--stem", default="P9201256")
    ap.add_argument(
        "--fill-odd",
        action="store_true",
        help="unlisted frame inherits the verdict when both neighbours are listed with the same verdict",
    )
    args = ap.parse_args()
    d = Path(args.sheet_dir).expanduser()
    tk = _load_sheet(d / f"yolo_raw_{args.stem}_tackler_assign.npz", "tackler")
    cr = _load_sheet(d / f"yolo_raw_{args.stem}_carrier_assign.npz", "carrier")
    frames = tk["frame_index"]
    decisions = _read_verdicts(args.csv)
    if args.fill_odd:
        decisions = _fill_unlisted_frames(frames, decisions)
    verdict, basis = _apply_verdicts(tk, cr, decisions)
    counts = {v: int((verdict == v).sum()) for v in VERDICTS}
    tk["identity_verdict"] = verdict
    tk["identity_fix_basis"] = basis
    tk["identity_fix_counts"] = np.array(
        [(v, counts[v]) for v in VERDICTS],
        dtype=[("verdict", "U16"), ("count", "i8")],
    )
    tk["person"] = "tackler_verified"; tk["identity_fix_source"] = Path(args.csv).name
    np.savez(d / f"yolo_raw_{args.stem}_tackler_verified.npz", **tk)
    print("verdict counts:", counts, " fixed frames:", counts["swap"] + counts["fused"] + counts["no_valid"])
    print("frames changed:", [int(frames[i]) for i, v in enumerate(verdict) if v != "ok"])

if __name__ == "__main__":
    main()