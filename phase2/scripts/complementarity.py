"""Complementarity diagnostic (plan 1018 §2.2) — an ORACLE UPPER BOUND, not a contestant.
Per joint-frame: is linear interpolation or HybrIK closer to the GT? Oracle fusion = pick the closer one with the GT
(= correct iff either is correct at alpha), plus the 2x2 table correct/incorrect for interp vs HybrIK,
over all / vis0 / vis1 / phases / joint groups. Uses pck.py's ruler (align, pck_matrix, subsets). Run in `rugby`.
All rates use the common scored joint-frames, not each sheet's separate scoring denominator.
This is an upper bound for selecting one of the two predictions on that common support, not for arbitrary fusion.
  python phase2/scripts/complementarity.py <gt.npz> <clip> --interp <interp.npz> --hybrik <name>=<sheet.npz> [...] --alphas 0.10 0.20 --out phase2/results/final_v3"""
import argparse, csv, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from phase2.pck import load_gt, load_sheet, align, pck_matrix, subsets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gt"); ap.add_argument("clip")
    ap.add_argument("--interp", required=True)
    ap.add_argument("--hybrik", nargs="+", required=True, help="name=path.npz, e.g. hybrik_struct=... hybrik_interp=...")
    ap.add_argument("--alphas", type=float, nargs="+", default=[0.10, 0.20])
    ap.add_argument("--out", default="phase2/results/final_v3")
    args = ap.parse_args()
    if not all(np.isfinite(a) and a > 0 for a in args.alphas):
        ap.error("--alphas must be finite and positive")
    for spec in args.hybrik:
        name, sep, path = spec.partition("=")
        if not sep or not name.strip() or not path.strip():
            ap.error("--hybrik entries must have the form name=path.npz")
    gt = load_gt(Path(args.gt).expanduser())
    pred_i = align(gt, load_sheet(Path(args.interp).expanduser()))
    masks = subsets(gt, args.clip)
    out = Path(args.out).expanduser()
    for spec in args.hybrik:
        name, path = spec.split("=", 1)
        pred_h = align(gt, load_sheet(Path(path).expanduser()))
        md = [f"# Complementarity (ORACLE upper bound, not a contestant): interp vs {name}, clip {args.clip}",
              "oracle = per joint-frame the closer of the two (chosen with the GT); gain = oracle - max(interp, hybrik);",
              "All rates and cells use joint-frames scored by BOTH sheets (NaN/Inf in either -> excluded; GT vis>=2 excluded).",
              "Rates may differ from standalone PCK when scoring denominators differ.",
              "This upper bound applies to choosing one of these two predictions on the common scored set, not arbitrary fusion.", ""]
        rows = []
        for a in args.alphas:
            ci, si, _ = pck_matrix(pred_i, gt, a); ch, sh, _ = pck_matrix(pred_h, gt, a)
            both = si & sh
            md += [f"## alpha = {a:.2f}", f"| subset | n | interp | {name} | oracle | gain | both | interp-only | {name}-only | neither |", "|---" * 10 + "|"]
            for sname, m in masks.items():
                mm = both & m; n = int(mm.sum())
                if n == 0:
                    continue
                # oracle succeeds iff either prediction is correct on the common scored set.
                pck_i = (ci & mm).sum()/n ; pck_h = (ch & mm).sum()/n ; pck_or = ((ci | ch) & mm).sum()/n ; gain = pck_or - max(pck_i, pck_h)
                # the four mutually exclusive cells partition the common scored set.
                both_c = (ci & ch & mm).sum() ; i_only = (ci & ~ch & mm).sum() ; h_only = (~ci & ch & mm).sum() ; neither = (~ci & ~ch & mm).sum()
                # save rates and cell counts for each alpha/subset.
                rows.append(dict(alpha=a, subset=sname, n=n, interp=pck_i, hybrik=pck_h, oracle=pck_or, gain=gain,
                                both=both_c, interp_only=i_only, hybrik_only=h_only, neither=neither))
                md.append(f"| {sname} | {n} | {pck_i:.3f} | {pck_h:.3f} | {pck_or:.3f} | {gain:+.3f} | {both_c} | {i_only} | {h_only} | {neither} |")
            md.append("")
        if not rows:
            raise ValueError(f"No jointly scored joint-frames for interp vs {name}; check frame alignment, visibility and finite coordinates")
        out.mkdir(parents=True, exist_ok=True)
        (out / f"complementarity_{args.clip}_{name}.md").write_text("\n".join(md) + "\n")
        with open(out / f"complementarity_{args.clip}_{name}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print("\n".join(md))


if __name__ == "__main__":
    main()