# phase2/tgct/losses.py
import torch
import torch.nn.functional as F


def tgct_loss(pred, target, hidden, visible, lam=0.0, w_vis=0.1, delta=0.01):
    """pred, target (B,T,K,2) centred coords; hidden/visible (B,T,K) bool. Worksheet 1.5.

    pred must be the final coordinates (fill + residual), with T >= 3.

    L = mean_H rho(err) + w_vis * mean_V rho(err) + lam * mean ||acc||^2
    """
    if pred.size(1) < 3:
        raise ValueError("tgct_loss requires at least 3 frames for the acceleration term")
    err = F.smooth_l1_loss(pred, target, reduction='none', beta=delta).sum(-1) # (B,T,K)
    L_h = (err * hidden).sum() / (hidden.sum().clamp(min=1))  # avoid division by zero
    L_v = (err * visible).sum() / (visible.sum().clamp(min=1))
    acc = pred[:, 2:] - 2 * pred[:, 1:-1] + pred[:, :-2]  # (B,T-2,K,2)
    L_a = (acc ** 2).sum(-1).mean()  # mean over (B, T-2, K)
    return L_h + w_vis * L_v + lam * L_a, dict(hidden=L_h.item(), visible=L_v.item(), acc=L_a.item())
