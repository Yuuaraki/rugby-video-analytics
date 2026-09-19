# phase2/metrics.py  -- compute_jitter ported VERBATIM from notebooks/Skelton_graph_GCN.ipynb cell 24
import numpy as np

def compute_jitter(c):
    d = np.diff(c, axis=0)
    return np.sqrt((d**2).sum(axis=-1))

def jk_table(coords, confs, tau=0.5):
    """Phase-1 aggregation, repackaged: Jk = mean step length; Occ = pairs whose LATER frame has conf < tau."""
    j = compute_jitter(coords)                      # (T-1, K)
    out = {}
    for k in range(coords.shape[1]):
        om = confs[1:, k] < tau                     # verbatim rule from Phase 1 cell 24
        out[k] = dict(Jk=j[:, k].mean(),
                      Jk_occ=(j[om, k].mean() if om.sum() > 0 else 0.0),
                      n_occ=int(om.sum()))
    return out