"""Final table assembled from phase2/results/final_v3/*.csv. Run in `rugby`.
  python phase2/scripts/final_table_v3.py --dir phase2/results/final_v3"""
import argparse
from pathlib import Path
import pandas as pd
import re

CLIPS = ["P9201256", "PA041271"]
MAIN = ["raw_verified", "interp", "interp_ok", "rts", "tgct_v1", "hybrik_struct", "hybrik_struct_ok", "hybrik_interp"]
APPX = ["rts_sa1e-3", "tgct_v1m", "tgct_v1g", "interp_oracle", "tgct_v1_oracle"]
SUBS = ["all", "vis0", "vis1"]
PHASES = {"P9201256": ["pre", "contact", "fusion", "fall"], "PA041271": ["pre", "contact", "hold", "post"]}
CEIL = {"P9201256": "self-PCK ceiling (5-frame re-annotation, L_ref 441 px): vis0 0.89@0.10 / 0.92@0.20, vis1 0.70 / 1.00",
        "PA041271": "self-PCK ceiling (L_ref 266 px): vis0 0.92@0.10 / 1.00@0.20, vis1 0.81 / 1.00"}
FOOT = {"P9201256": "HybrIK person check on the 98 GT frames: person_ok 85, no verified box 9 (fused 1, no_valid 8: contact), "
                    "HybrIK crop centre outside the verified box on 4 frames (3260, 3266, 3268, 3270: contact). Bias calibration: pre+fall, 33 GT frames (A3).",
        "PA041271": "HybrIK person check on the 61 GT frames: person_ok 44, no verified box 8 (no_valid 4496-4512 exc. 4500), "
                    "HybrIK crop centre outside the verified box on 9 frames (4426-4442, even frames). Bias calibration: pre 32 + post 17 GT frames."}

def table(df, conds, subs, alphas=(0.20, 0.10)):
    """rows = conditions, columns = n per subset, then PCK per alpha x subset."""
    head  ="| condition | " + " | ".join(f"n {s}" for s in subs) + " | " + " | ".join(f"{s}@{a:.2f}" for a in alphas for s in subs) + " |"
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

def comp_table(df, subs, name, iname="interp"):
    """complementarity csv (alpha 0.20) -> markdown with rates and the 2x2 cells. """
    d = df[(df.alpha == 0.20) & df.subset.isin(subs)].set_index("subset")
    lines = [f"| subset | n | {iname} | {name} | oracle | gain | both | {iname}-only | {name}-only | neither |", "|---" * 10 + "|"]
    if not d.index.is_unique:
        raise ValueError(f"Duplicate complementarity subset rows at alpha 0.20 for {name}")
    # TODO 1: one line per subset, preserving the values from the complementarity CSV.
    for s in subs:
        if s not in d.index:
            continue
        n = int(d.loc[s, "n"])
        interp = d.loc[s, "interp"]
        hybrik = d.loc[s, "hybrik"]
        oracle = d.loc[s, "oracle"]
        gain = d.loc[s, "gain"]
        both = int(d.loc[s, "both"])
        interp_only = int(d.loc[s, "interp_only"])
        hybrik_only = int(d.loc[s, "hybrik_only"])
        neither = int(d.loc[s, "neither"])
        lines.append(f"| {s} | {n} | {interp:.3f} | {hybrik:.3f} | {oracle:.3f} | {gain:+.3f} | {both} | {interp_only} | {hybrik_only} | {neither} |")
    return lines + [""]

def a3_foot(D, clip, conds=("interp", "interp_ok", "hybrik_struct_ok")):
    """Calibration frame count (from the bias csv header) and per-joint n_used range for the key conditions."""
    head = (D / f"bias_{clip}_{conds[0]}.csv").read_text().splitlines()[0]
    frames = re.search(r"calibration = (\d+) GT frames", head).group(1)
    parts = []
    for c in conds:
        b = pd.read_csv(D / f"bias_{clip}_{c}.csv", comment="#", header=None, names=["dx", "dy", "n_used"])
        parts.append(f"{c} n_used per joint {int(b.n_used.min())}-{int(b.n_used.max())} ({int((b.n_used == 0).sum())} joints uncorrected)")
    return f"{frames} GT frames; " + "; ".join(parts)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", default="phase2/results/final_v3"); args = ap.parse_args()
    D = Path(args.dir).expanduser(); md = ["# Final table v3 (2026-10-18)", "",
        "Scoring: phase2/pck.py with the per-clip reference torso length L_ref = median shoulder-mid–hip-mid distance over GT frames "
        "with all four torso joints vis≠2 (P9201256 441 px, PA041271 266 px; pre-registered 2026-10-17). Per-frame results are kept in "
        "results/final_v3_perframe/ as a sensitivity check. GT frames only; NaN joint-frames excluded from the denominator; (0,0) misses count as wrong. "
        "Main metric PCK@0.20, secondary @0.10. hybrik_struct = all window even frames (person-selection failures retained and scored against the GT); "
        "hybrik_struct_ok = frames where HybrIK's crop centre lies inside the verified tackler box (NaN elsewhere); "
        "hybrik_interp = hybrik_struct_ok with not-ok frames bridged by linear interpolation. "
        "Bias-corrected, oracle and 2x2 tables are diagnostics (appendix), not contestants.",
        "n counts joint-frames, not images. hybrik_struct_ok is conditional on person_ok and has a different denominator. "
        "Self-PCK is a re-annotation consistency reference, not a strict mathematical ceiling. "
        "Complementarity uses only joint-frames scored by both sheets; its rates may differ from standalone PCK. "
        "The oracle is an upper bound for choosing between the two predictions on that common set, not arbitrary fusion.", 
        "Denominators: hybrik_struct_ok is compared with interp_ok (the same not-person_ok frames blanked), never directly with interp; "
        "where every frame is person_ok (P9201256 fusion, n=405) interp = interp_ok and the usual comparison holds. "
        "Complementarity (i) interp vs hybrik_struct is the pipeline as it stands; (ii) interp_ok vs hybrik_struct_ok is the complementarity when person selection is right; (iii) interp vs hybrik_interp.", ""]
    for clip in CLIPS:
        pck = pd.read_csv(D / f"pck_{clip}.csv")
        md += [f"## Main table — {clip}", CEIL[clip], ""] + table(pck, MAIN, SUBS) + [f"Footnote: {FOOT[clip]}", ""]
    md += ["# Appendix", ""]
    for clip in CLIPS:
        pck = pd.read_csv(D / f"pck_{clip}.csv")
        md += [f"## A1 by phase — {clip}", ""] + table(pck, MAIN + APPX, PHASES[clip])
        # TODO 2: retain the CSV's joint-group order after excluding visibility and phase subsets.
        groups = [s for s in pck["subset"].unique() if s not in SUBS + PHASES[clip]]
        md += [f"## A2 by joint group — {clip}", ""] + table(pck, MAIN, groups)
        md += [f"## A3 bias-corrected (within-clip calibration: P9201256 pre+fall / PA041271 pre+post, vis0; secondary) — {clip}", ""] + table(pd.read_csv(D / f"pck_{clip}_bc.csv"), MAIN, SUBS)
        md += [f"Calibration footnote: {a3_foot(D, clip)}. fall is a fallen posture: the joint-definition offset there may differ from standing, so the P9201256 bias-corrected values are read as a secondary metric.", ""]
        md += [f"## A4 sensitivity / variants / oracle rows — {clip}", ""] + table(pck, APPX, SUBS)
        for iname, name, label in (("interp", "hybrik_struct", "(i) pipeline as it stands"),
                                   ("interp_ok", "hybrik_struct_ok", "(ii) person_ok frames: complementarity when person selection is right"),
                                   ("interp", "hybrik_interp", "(iii)")):
            comp = pd.read_csv(D / f"complementarity_{clip}_{name}.csv")
            md += [f"## A5 complementarity {label} — ORACLE upper bound @0.20, {iname} vs {name} — {clip}", ""] + comp_table(comp, SUBS + PHASES[clip], name, iname)
    md += ["## A6 gap-length breakdown (T-GCT): see phase2/results/tgct_v1/ (tgct_report.py output, unchanged)", ""]
    (D / "final_table_v3.md").write_text("\n".join(md) + "\n"); print(f"wrote {D / 'final_table_v3.md'} ({len(md)} lines)")

if __name__ == "__main__":
    main()
    
