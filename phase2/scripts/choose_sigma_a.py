"""Finalise sigma_a by ONE hide-and-predict run on the solo footage.
sigma_m is the detector floor from temporal_params (D6), i.e. the value RTS will be applied with. Run in `rugby`:
   python phase2/scripts/choose_sigma_a.py PA041266 PA041267 [--win 60] [--tail-drop 30]"""
import argparse, json, sys, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
sys.path.append(str(Path.home() / "rugby-video-analytics"))
from phase2.temporal import hide_and_predict, observed_mask


GRID = (1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3)
BODY12 = list(range(5, 17))
PARAMS = Path("phase2/results/temporal_params_P9201256.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stems", nargs="+")
    ap.add_argument("--win", type=int, default=60)
    ap.add_argument("--tail-drop", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true", help="print the curve only; leave the JSON and the figure untouched")
    args = ap.parse_args()
    if args.win <= 0:
        ap.error("--win must be positive")
    if args.tail_drop < 0:
        ap.error("--tail-drop must be non-negative")

    params = json.loads(PARAMS.read_text())
    sigma_m = float(params["sigma_m"])
    results = {}

    for stem in args.stems:
        with np.load(Path.home() / f"data/phase2_npz/yolo_raw_{stem}_solo.npz", allow_pickle=True) as z:
            c, k = z["coords"][:, BODY12], z["confs"][:, BODY12]
            n_cand = z["n_cand"] if "n_cand" in z.files else None
        obs = observed_mask(c, k)
        if n_cand is not None:
            obs &= (n_cand == 1)[:, None]
        if args.tail_drop:
            obs[-args.tail_drop:] = False
        err, starts = hide_and_predict(c, obs, sigma_m, sigma_a_grid=GRID, win=args.win, n_win=1000, seed=0)
        results[stem] = dict(err=err, n=len(starts), T=len(c), obs_frac=float(obs.mean()))
        print(f"{stem}: T={len(c)} obs={obs.mean():.2f} windows{args.win}={len(starts)}")

    names = [s for s in results if results[s]["n"] > 0]
    if not names:
        raise ValueError(f"No eligible {args.win}-frame windows; parameters were not updated")
    w = np.array([results[s]["n"] for s in names], float)
    curve = {sa: float(np.average([results[s]["err"][sa] for s in names], weights=w)) for sa in GRID}
    interp = float(np.average([results[s]["err"]["interp"] for s in names], weights=w))
    if not np.isfinite([*curve.values(), interp]).all():
        raise ValueError(f"Non-finite errors for {args.win}-frame windows; parameters were not updated")
    best = min(curve, key=curve.get)
    n_total = int(w.sum())
    print(f"windows={n_total}  best sigma_a={best:.0e}  RTS={curve[best]:.5f}  interp={interp:.5f}  (sigma_m={sigma_m:.5f})")
    if best in (GRID[0], GRID[-1]):
        print("WARNING: minimum at the grid edge — report, do not expand (設計本部: no deep dive)")

    if args.dry_run:
        print("dry run: JSON and figure not written"); return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(list(curve), list(curve.values()), "ro-", label=f"RTS, {args.win}-frame windows (n={n_total})")
    ax.axhline(interp, color="r", ls="--", lw=1, label="linear interpolation"); ax.plot(best, curve[best], "r*", ms=14)
    ax.set(xscale="log", xlabel="sigma_a (Phase-1 units / frame^2 @ 59.94 fps)", ylabel="mean hidden-joint error", title=f"solo footage {'+'.join(args.stems)}, sigma_m = detector floor {sigma_m:.4f}")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig("phase2/results/fig_sigma_a_solo.png", dpi=120)

    params["sigma_a"] = best
    params["sigma_a_solo"] = dict(stems=args.stems, win=args.win, n_windows=n_total, err=curve[best], interp=interp, sigma_m=sigma_m)
    params["sigma_a_note"] = "final: one hide-and-predict run on solo footage with sigma_m = detector floor (D6/D7, 2026-10-14)"
    if "sigma_a_by_window" in params:
        params["sigma_a_provisional_P9201256"] = params.pop("sigma_a_by_window")
    PARAMS.write_text(json.dumps(params, indent=2)); print(PARAMS.read_text())


if __name__ == "__main__":
    main()