"""Final table v4 - condition A (as run): no identity fix, no person_ok gate, every contestant scored on the GT's
full joint-frames. Assembled from phase2/results/final_v4/pck_<clip>.csv (pck.py, per-clip L_ref). Run in `rugby`:
   python phase2/scripts/final_table_v4.py --dir phase2/results/final_v4 [--v3 phase2/results/final_v3]
--v3 is READ ONLY: it feeds the A-vs-B check tables at the end (final_structure_v6 section 1.3); nothing in it is written."""
import argparse
from pathlib import Path
import pandas as pd

CLIPS = ["P9201256", "PA041271"]
CONDS = ["yolo", "interp", "rts", "tgct", "hybrik"]
B_NAME = {"yolo": "raw_verified", "interp": "interp", "rts": "rts", "tgct": "tgct_v1", "hybrik": "hybrik_struct"}   # v3 row names
SUBS = ["all", "vis0", "vis1"]
PHASES = {"P9201256": ["pre", "contact", "fusion", "fall"], "PA041271": ["pre", "contact", "hold", "post"]}
GROUPS = ["sho", "elb", "wri", "hip", "kne", "ank"]
CEIL = {"P9201256": "self-PCK ceiling (5-frame re-annotation, L_ref 441 px): vis0 0.89@0.10 / 0.92@0.20, vis1 0.70 / 1.00",
        "PA041271": "self-PCK ceiling (L_ref 266 px): vis0 0.92@0.10 / 1.00@0.20, vis1 0.81 / 1.00"}
HEADER = [
    "# Final table v4 - condition A (as run), 2026-10-23", "",
    "Scoring: phase2/pck.py with the per-clip reference torso length L_ref (median shoulder-mid-hip-mid distance over GT frames "
    "with all four torso joints vis!=2: P9201256 441 px, PA041271 266 px). GT frames only; every GT joint-frame with vis<2 is in the "
    "denominator (P9201256 1125, PA041271 732) for all five rows; (0,0) misses count as wrong. No bias correction, no person_ok gate. "
    "Main metric PCK@0.20, secondary @0.10.", "",
    "Condition A (as run): the detector's tackler assignment is the pipeline's automatic output "
    "(yolo_raw_<clip>_tackler_assign.npz from phase2/scripts/labels_to_sheets.py, IoU tracking; no identity fix applied). "
    "interp and rts are rebuilt from that sheet by phase2/scripts/make_temporal_sheets.py (sigma_m 0.00051, sigma_a 1e-5, "
    "observed = conf >= 0.5 and not a no-detection frame; the yolo row itself scores the detector coordinates as returned, "
    "low-confidence joints included); tgct by phase2.tgct.infer with the v1_best checkpoint (inference only, no retraining); "
    "hybrik = hybrik_struct, the same sheet as in v3 (demo person selection as run).", "",
    "Rows: yolo = YOLO-Pose (detector only); interp = Linear interpolation; rts = Kalman-RTS (constant velocity); "
    "tgct = T-GCT; hybrik = HybrIK (anatomical prior).", "",
    "Conditions B (identity-corrected input) and C (on-tackler frames) stay in results/final_v3/final_table_v3.md. "
    "The A-vs-B tables at the end are a plumbing check (v6 section 1.3) and the material for the identity-loss discussion, "
    "not a results table.", ""]

def table(df, conds, subs, alphas=(0.20, 0.10)):
    """rows = conditions, columns = n per subset, then PCK per alpha x subset (copied from final_table_v3.py)."""
    head = "| condition | " + " | ".join(f"n {s}" for s in subs) + " | " + " | ".join(f"{s}@{a:.2f}" for a in alphas for s in subs) + " |"
    lines = [head, "|---" * (1 + len(subs) * (1 + len(alphas))) + "|"]
    for c in conds:
        d = df[df.condition == c].set_index("subset")
        if d.empty:
            continue
        if not d.index.is_unique:
            raise ValueError(f"Duplicate subset rows for condition {c}")
        ns = [str(int(d.loc[s, "n"])) if s in d.index else "-" for s in subs]
        vals = [f"{d.loc[s, f'pck@{a:.2f}']:.3f}" if s in d.index else "-" for a in alphas for s in subs]
        lines.append(f"| {c} | " + " | ".join(ns) + " | " + " | ".join(vals) + " |")
    return lines + [""]

def ab_table(a, b, subs, alpha=0.20):
    """Condition A (this run) vs condition B (v3) at one alpha: 'A / B / A-B' per subset, one row per condition."""
    head = "| condition (A row = B row) | " + " | ".join(f"{s} A / B / A-B" for s in subs) + " |"
    lines = [head, "|---" * (1 + len(subs)) + "|"]
    for c in CONDS:
        da = a[a.condition == c].set_index("subset")
        db = b[b.condition == B_NAME[c]].set_index("subset")
        cells = []
        for s in subs:
            if s in da.index and s in db.index:
                va, vb = float(da.loc[s, f"pck@{alpha:.2f}"]), float(db.loc[s, f"pck@{alpha:.2f}"])
                cells.append(f"{va:.3f} / {vb:.3f} / {va - vb:+.3f}")
            else:
                cells.append("-")
        lines.append(f"| {c} = {B_NAME[c]} | " + " | ".join(cells) + " |")
    return lines + [""]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="phase2/results/final_v4")
    ap.add_argument("--v3", default="phase2/results/final_v3", help="read only; A-vs-B check")
    args = ap.parse_args()
    D, V3 = Path(args.dir), Path(args.v3)
    md = list(HEADER)
    for clip in CLIPS:
        pck = pd.read_csv(D / f"pck_{clip}.csv")
        md += [f"## Main table (condition A) - {clip}", CEIL[clip], ""] + table(pck, CONDS, SUBS)
    md += ["# Appendix", ""]
    for clip in CLIPS:
        pck = pd.read_csv(D / f"pck_{clip}.csv")
        md += [f"## A1 by phase (condition A) - {clip}", ""] + table(pck, CONDS, PHASES[clip])
        md += [f"## A2 by joint group (condition A) - {clip}", ""] + table(pck, CONDS, GROUPS)
    for clip in CLIPS:
        v3 = V3 / f"pck_{clip}.csv"
        if not v3.exists():
            md += [f"## Check A vs B - {clip}: {v3} not found, skipped", ""]
            continue
        pck = pd.read_csv(D / f"pck_{clip}.csv")
        md += [f"## Check: condition A vs condition B (v3, identity-corrected input), PCK@0.20 - {clip}", ""]
        md += ab_table(pck, pd.read_csv(v3), SUBS + PHASES[clip])
    out = D / "final_table_v4.md"
    out.write_text("\n".join(md) + "\n")
    print(f"wrote {out} ({len(md)} lines)")

if __name__ == "__main__":
    main()
