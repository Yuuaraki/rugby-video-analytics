# phase2/scripts/tgct_report.py
"""Learning curve + hide-and-predict breakdown by gap length (worksheet d-3 / 1.7).
Run in rugby, from the repo root:  python -m phase2.scripts.tgct_report --tags v1      (add tags for ablations)
"""
import argparse
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from phase2.tgct.graph import body12_A_norm
from phase2.tgct.model import TGCT
from phase2.tgct.data import load_seqs, WindowDataset
from phase2.tgct.train import VAL, OUT

RES = Path("phase2/results")
# gap-length bins in even frames: contact ~14, fusion ~38-64 (P9201256), ">=65" = spans merged with real gaps or window edges
BINS = [(1, 14, "short <=14"), (15, 40, "mid 15-40"), (41, 64, "long 41-64"), (65, 10**9, "very long >=65")]

def plot_curves(tags):
    fig, ax = plt.subplots(figsize=(7, 4))
    for tag in tags:
        d = np.atleast_1d(np.genfromtxt(OUT / f"log_{tag}.csv", delimiter=",", names=True))
        if d.size == 0:
            raise ValueError(f"{tag}: learning log contains no rows")
        trained = d["epoch"] >= 0
        ax.plot(d["epoch"][trained], d["train_hidden"][trained], "--", label=f"{tag} train (hidden, Huber)")
        ax.plot(d["epoch"], d["val_tgct"], "-", label=f"{tag} val_tgct")
        ax.axhline(d["val_interp"][0], ls=":", label=f"{tag} val_interp (linear interpolation)")
    ax.set_xlabel("epoch")
    ax.set_ylabel("hidden-joint error (train: Huber; val: L1, Phase-1 units)")
    ax.set_ylim(0, None)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = RES / f"fig_tgct_curve_{'_'.join(tags)}.png"
    fig.savefig(out, dpi=150); print("saved", out)
    plt.close(fig)
    
def run_lengths(unobserved):
    """(T,K) bool -> (T,K) int: length of the contiguous unobserved run containing each point (0 where observed)."""
    out = np.zeros(unobserved.shape, dtype=int)
    for k in range(unobserved.shape[1]):
        m, t = unobserved[:, k], 0
        while t < len(m):
            if not m[t]:
                t += 1; continue
            s = t
            while t < len(m) and m[t]:
                t += 1
            out[s:t, k] = t - s
    return out


@torch.no_grad()
def breakdown(tag):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    A = torch.as_tensor(body12_A_norm()).to(device)
    ck = torch.load(OUT / "ckpt" / f"{tag}_best.pt", map_location=device, weights_only=True)
    T, stride = ck["args"]["T"], ck["args"]["stride"]
    model = TGCT(max_len=max(256, T)).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    va = WindowDataset(load_seqs(VAL), T=T, stride=stride, seed=123, flip=False, scale=0.0, fixed=True)
    if len(va) == 0:
        raise ValueError(f"{tag}: validation contains no eligible windows")
    error_t, error_i, length = [], [], []
    for i in range(len(va)):
        d = va[i]
        pred = (d["fill"][None].to(device) + model(d["feats"][None].to(device), A))[0].cpu()
        h = d["hidden"].numpy()
        L = run_lengths(~d["visible"].numpy()) # gap length as the model sees it (hidden + real gaps merged)
        error_t.append((pred - d["target"]).abs().sum(-1).numpy()[h])
        error_i.append((d["fill"] - d["target"]).abs().sum(-1).numpy()[h])
        length.append(L[h])
    err_t, err_i, length = map(np.concatenate, (error_t, error_i, length))
    if len(length) == 0:
        raise ValueError(f"{tag}: validation has no hidden joint-frames to score")
    if not np.isfinite(err_t).all() or not np.isfinite(err_i).all():
        raise ValueError(f"{tag}: validation produced non-finite errors")
    change = f"{100 * (1 - err_t.mean() / err_i.mean()):.1f}% lower" if err_i.mean() > 0 else "relative improvement undefined: interp is zero"
    print(f"\n{tag}: best epoch {ck['epoch']}  n={len(length)}  interp {err_i.mean():.4f}  tgct {err_t.mean():.4f}  "
          f"({change})")
    print(f"{'gap length (even frames)':26s} {'n':>7s} {'interp':>8s} {'tgct':>8s} {'change':>8s}")
    for lo, hi, name in BINS:
        m = (length >= lo) & (length <= hi)
        if m.sum() == 0:
            continue
        change = f"{100 * (1 - err_t[m].mean() / err_i[m].mean()):.1f}%" if err_i[m].mean() > 0 else "N/A"
        print(f"{name:26s} {m.sum():7d} {err_i[m].mean():8.4f} {err_t[m].mean():8.4f} {change:>8s}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="+", default=["v1"])
    args = ap.parse_args()
    RES.mkdir(exist_ok=True)
    plot_curves(args.tags)
    for t in args.tags:
        breakdown(t)
        
