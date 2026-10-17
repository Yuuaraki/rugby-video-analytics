# phase2/tgct/train.py
"""T-GCT training (worksheet exercise d). Run in rugby, from the repo root:
    python -m phase2.tgct.train --tag v1 --epochs 60
Resume after a pre-emption:
    python -m phase2.tgct.train --tag v1 --epochs 60 --resume
Outputs (outside git): ~/data/tgct/log_<tag>.csv, ~/data/tgct/ckpt/<tag>_{last,best}.pt
"""
import argparse, csv, time
from pathlib import Path
import numpy as np
import torch
from phase2.tgct.graph import body12_A_norm
from phase2.tgct.model import TGCT
from phase2.tgct.losses import tgct_loss
from phase2.tgct.data import load_seqs, WindowDataset

TRAIN = ["PA041266", "PA041267", "PA041269", "PA041270"]
VAL = ["PA041268"]
OUT = Path.home() / "data/tgct"

def hidden_l1(pred, target, hidden):
    """Sum over hidden joint-frames of |dx|+|dy|, and their count (same quantity as the c-5 val_interp preview)."""
    e = (pred - target).abs().sum(-1)
    return e[hidden].sum().item(), hidden.sum().item()

@torch.no_grad()
def evaluate(model, loader, A, device):
    """Hide-and-predict on the fixed val set. Returns (val_tgct, val_interp)."""
    model.eval()
    s_t = s_i = den = 0.0
    for b in loader:
        feats, target, fill, hidden = (b[k].to(device) for k in ("feats", "target", "fill", "hidden"))
        pred = fill + model(feats, A)
        st, d = hidden_l1(pred, target, hidden)
        si, _ = hidden_l1(fill, target, hidden)
        s_t += st
        s_i += si
        den += d
    if den == 0:
        raise ValueError("Validation has no hidden joint-frames to score")
    if not np.isfinite([s_t, s_i]).all():
        raise ValueError("Validation produced non-finite errors")
    return s_t / den, s_i / den

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lam", type=float, default=0.0)
    ap.add_argument("--w-vis", type=float, default=0.1)
    ap.add_argument("--T", type=int, default=128)
    ap.add_argument("--stride", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    if args.epochs <= 0 or args.batch <= 0 or args.stride <= 0 or args.T < 3:
        ap.error("--epochs, --batch, --stride must be positive and --T must be at least 3")
    if args.workers < 0 or args.seed < 0:
        ap.error("--workers and --seed must be non-negative")
    
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    A = torch.as_tensor(body12_A_norm()).to(device)
    
    tr_ds = WindowDataset(load_seqs(TRAIN), T=args.T, stride=args.stride, seed=args.seed)
    va_ds = WindowDataset(load_seqs(VAL), T=args.T, stride=args.stride, seed=123, flip=False, scale=0.0, fixed=True)
    if len(tr_ds) == 0 or len(va_ds) == 0:
        raise ValueError("Training and validation must each contain at least one eligible window")
    tr = torch.utils.data.DataLoader(tr_ds, batch_size=args.batch, shuffle=True, num_workers=args.workers)
    va = torch.utils.data.DataLoader(va_ds, batch_size=args.batch, shuffle=False, num_workers=args.workers)
    print(f"device {device}  train windows {len(tr_ds)}  val windows {len(va_ds)}")
    
    model = TGCT(max_len=max(256, args.T)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    
    ckpt_dir = OUT / "ckpt"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    last, best = ckpt_dir / f"{args.tag}_last.pt", ckpt_dir / f"{args.tag}_best.pt"
    log_path = OUT / f"log_{args.tag}.csv"
    start, best_val = 0, float("inf")
    
    if args.resume:
        if not last.exists():
            raise FileNotFoundError(f"Cannot resume: checkpoint not found: {last}")
        ck = torch.load(last, map_location=device, weights_only=True)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        sched.load_state_dict(ck["sched"])
        start = ck["epoch"] + 1
        best_val = ck["best_val"]
        print(f"resumed from epoch {ck['epoch']} (best val_tgct so far {best_val:.4f})")
        v_t, v_i = evaluate(model, va, A, device)
    else:
        with open(log_path, "w", newline="") as f:
            csv.writer(f).writerow(["epoch", "train_loss", "train_hidden", "train_visible", "train_acc",
                                    "val_tgct", "val_interp", "lr", "sec"])
        v_t, v_i = evaluate(model, va, A, device)
        print(f"epoch  -1 (untrained)  val_tgct {v_t:.4f}  val_interp {v_i:.4f}  -> design decision 3 holds: {abs(v_t - v_i) < 1e-6}")
        with open(log_path, "a", newline="") as f:
            csv.writer(f).writerow([-1, "", "", "", "",  f"{v_t:.6f}", f"{v_i:.6f}", "", ""])
    
    for epoch in range(start, args.epochs):
        t0 = time.time()
        model.train()
        tr_ds.set_epoch(epoch)
        sums = dict(loss=0.0, hidden=0.0, visible=0.0, acc=0.0)
        n = 0
        for b in tr:
            feats, target, fill, hidden, visible = (b[k].to(device) for k in ["feats", "target", "fill", "hidden", "visible"])
            pred = fill + model(feats, A)
            loss, parts = tgct_loss(pred, target, hidden, visible, lam=args.lam, w_vis=args.w_vis)
            if not torch.isfinite(loss).item():
                raise ValueError(f"Non-finite training loss at epoch {epoch}, batch {n}")
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            opt.step()
            sums["loss"] += loss.item()
            n += 1
            for k in ("hidden", "visible", "acc"):
                sums[k] += parts[k]
        lr = opt.param_groups[0]["lr"]
        sched.step()
        v_t, v_i = evaluate(model, va, A, device)
        sec = time.time() - t0
        print(f"epoch {epoch:3d}  loss {sums['loss']/n:.4f}  val_tgct {v_t:.4f}  val_interp {v_i:.4f}  lr {lr:.2e}  {sec:.0f}s")
        with open(log_path, "a", newline="") as f:
            csv.writer(f).writerow([epoch, f"{sums['loss']/n:.6f}", f"{sums['hidden']/n:.6f}", f"{sums['visible']/n:.6f}",
                                    f"{sums['acc']/n:.6f}", f"{v_t:.6f}", f"{v_i:.6f}", f"{lr:.2e}", f"{sec:.1f}"])
        # checkpoint every epoch (pre-emptible VM); keep the best by val_tgct
        state = dict(model=model.state_dict(),
                     opt=opt.state_dict(),
                     sched=sched.state_dict(),
                     epoch=epoch,
                     best_val=min(best_val, v_t),
                     args=vars(args))
        torch.save(state, last)
        if v_t < best_val:
            best_val = v_t
            torch.save(state, best)
    improvement = f"{100 * (1 - best_val / v_i):.1f}% lower" if v_i > 0 else "relative improvement undefined: val_interp is zero"
    print(f"done. best val_tgct {best_val:.4f} vs val_interp {v_i:.4f}  ({improvement})")


if __name__ == "__main__":
    main()
