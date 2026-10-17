# phase2/tgct/data.py
import numpy as np
import torch
from phase2.temporal import interpolate_gaps, observed_mask
from .graph import LR_SWAP

# worksheet 1.6: limb groups that get hidden together (body-12 indices)
GROUPS = {"L_arm": [0, 2, 4], "R_arm": [1, 3, 5], "L_leg": [6, 8, 10], "R_leg": [7, 9, 11],
          "torso": [0, 1, 6, 7], "all": list(range(12))}

def sample_occlusion(T, K, rng, n_events=(1,2), span=(5, 65), p_drop=0.05):
    """ limb-group contiguous spans + sparse point dropout. Returns (T, K) bool 'hide'."""
    hide = np.zeros((T, K), dtype=bool)
    n = int(rng.integers(n_events[0], n_events[1] + 1))  # number of occlusion events
    for _ in range(n):
        L = int(rng.integers(span[0], span[1] + 1))
        s = int(rng.integers(0, max(1, T-L+1)))
        g = GROUPS[rng.choice(list(GROUPS))]
        hide[s:s + L, g] = True
    # sparse point dropout
    hide |= rng.random((T, K)) < p_drop
    return hide

def center(coords, obs):
    """Subtract one mean vector c (2,) of all visible joints in the window. Returns (centred, c)."""
    c = coords[obs].mean(axis=0) if obs.any() else np.zeros(2, dtype=coords.dtype)
    centred = coords - c
    return centred, c

def hflip(coords, obs, conf):
    """Horizontal flip: x -> 1 - x (apply BEFORE centring), then swap L/R joints by LR_SWAP. Returns (coords, obs, conf)."""
    coords = coords.copy()
    coords[..., 0] = 1.0 - coords[..., 0]  # horizontal flip
    coords = coords[:, LR_SWAP]      # swap L/R joints
    obs = obs[:, LR_SWAP]
    conf = conf[:, LR_SWAP]
    return coords, obs, conf

def fill_and_features(coords, obs_in, conf):
    """coords (T,K,2) centred; obs_in (T,K) bool AFTER hiding; conf (T,K) YOLO confidence.
    Returns feats (T,K,4) float32 = (x_fill, y_fill, conf_in, m) and fill (T,K,2) float32."""
    fill = np.zeros_like(coords, dtype=np.float32)
    for k in range(coords.shape[1]):
        if obs_in[:, k].any():
            for a in range(2):
                fill[:, k, a] = interpolate_gaps(coords[:, k, a], obs_in[:, k])
    conf_in = np.where(obs_in, conf, 0.0).astype(np.float32) # hidden joints look like "no detection"
    m = obs_in.astype(np.float32)
    feats = np.concatenate([fill, conf_in[..., None], m[..., None]], axis=-1).astype(np.float32)
    return feats, fill

def load_seqs(stems, root=None):
    """Read ~/data/tgct/seq_<stem>.npz into a list of dicts (coords, confs, present, frame_index)."""
    from pathlib import Path
    root = Path(root) if root else Path.home() / "data/tgct"
    out = []
    for s in stems:
        with np.load(root / f"seq_{s}.npz", allow_pickle=False) as z:
            out.append(dict(stem=s, coords=z["coords"], confs=z["confs"], present=z["present"], frame_index=z["frame_index"]))
    return out

class WindowDataset(torch.utils.data.Dataset):
    """One item = one window of T even frames. Returns a dict of tensors:
    feats (T,K,4), target (T,K,2) centred, fill (T,K,2), hidden (T,K) bool, visible (T,K) bool, c (2,)."""
    
    def __init__(self, seqs, T=128, stride=16,seed=0, flip=True, scale=0.1, min_obs_frac=0.5, fixed=False):
        self.seqs, self.T, self.seed, self.flip, self.scale, self.fixed = seqs, T, seed, flip, scale, fixed
        self.epoch = 0
        self.items = []
        for i, s in enumerate(seqs):
            obs = observed_mask(s["coords"], s["confs"]) & s["present"][:, None]
            for st in range(0, len(obs) - T + 1, stride):
                if obs[st:st+T].mean() >= min_obs_frac:
                    self.items.append((i, st))
                    
    def set_epoch(self, epoch):
        self.epoch = epoch
        
    def __len__(self):
        return len(self.items)
    
    def __getitem__(self, i):
        si, st = self.items[i]
        s, T = self.seqs[si], self.T
        coords = s["coords"][st:st+T]
        conf = s["confs"][st:st+T]
        present = s["present"][st:st+T]
        K = coords.shape[1]
        rng = np.random.default_rng([self.seed, i] if self.fixed else [self.seed, self.epoch, i])
        obs = observed_mask(coords, conf) & present[:, None]
        if self.flip and rng.random() < 0.5:
            coords, obs, conf = hflip(coords, obs, conf)
        coords_c, c = center(coords, obs)
        if self.scale > 0:
            coords_c *= rng.uniform(1 - self.scale, 1 + self.scale)
        hide = sample_occlusion(T, K, rng) & obs
        obs_in = obs & ~hide
        feats, fill = fill_and_features(coords_c, obs_in, conf)
        return dict(feats=torch.from_numpy(feats),
                    target=torch.from_numpy(coords_c.astype(np.float32)),
                    fill=torch.from_numpy(fill),
                    hidden=torch.from_numpy(hide),
                    visible=torch.from_numpy(obs_in),
                    c=torch.from_numpy(np.asarray(c, dtype=np.float32)))