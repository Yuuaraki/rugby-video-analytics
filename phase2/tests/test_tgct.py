# phase2/tests/test_tgct.py
"""Tests for phase2.tgct (worksheet phase2C_tgct_worksheet_1009, tests 1-5)."""
import numpy as np
import torch
import torch.nn as nn
from phase2.tgct.graph import body12_A_norm, EDGES12, LR_SWAP
from phase2.tgct.layers import GCTLayer, TemporalAttention
from phase2.tgct.model import TGCT
from phase2.tgct.losses import tgct_loss
from phase2.tgct.data import sample_occlusion, hflip


# ---- Test 1: shapes and graph ----
def test_1a_graph():
    A = body12_A_norm()
    assert A.shape == (12, 12)
    assert np.allclose(A, A.T)                                   # symmetric
    assert np.all((A.sum(1) > 0.85) & (A.sum(1) < 1.1))          # row sums near (not exactly) 1


def test_1b_layer_shapes():
    torch.manual_seed(0)
    A = torch.as_tensor(body12_A_norm())
    out, attn, gate = GCTLayer(64).eval()(torch.randn(7, 12, 64), A)
    assert out.shape == (7, 12, 64)
    out, w = TemporalAttention(64).eval()(torch.randn(5, 128, 64))
    assert out.shape == (5, 128, 64)

# ---- Test 2: model identity at init, parameter count, temporal axis meaning ----
def test_2a_identity_and_params():
    torch.manual_seed(0)
    A = torch.as_tensor(body12_A_norm())
    m = TGCT()
    out = m(torch.randn(2, 128, 12, 4), A)
    assert out.shape == (2, 128, 12, 2) # check output shape matches (B, T, K, 2)
    assert out.abs().max().item() == 0.0 # output should be zero at initialization
    n = sum(p.numel() for p in m.parameters()) # total number of parameters
    print("TGCT params:", n)
    assert 100_000 < n < 300_000
    
class _SpatialPass(nn.Module):
    """Stand-in for GCTLayer: returns its input unchanged, so the temporal input is inspectable."""
    def forward(self, h, A_norm):
        return h, None, None

class _TemporalRecord(nn.Module):
    """Stand-in for TemporalAttention: records its input (N, T, d) and returns it unchanged."""
    def forward(self, x):
        self.seen = x.detach().clone()
        return x, None

def test_2b_temporal_axis():
    B, T, K = 2, 6, 12
    m = TGCT(d_model=64)
    m.spatial = nn.ModuleList([_SpatialPass() for _ in m.spatial]) # replace spatial layers with pass-through stand-ins
    m.temporal = nn.ModuleList([_TemporalRecord() for _ in m.temporal]) # replace temporal layers with recording stand-ins
    with torch.no_grad(): 
        m.input_proj.weight.zero_()
        m.input_proj.bias.zero_()
        m.input_proj.weight[0, 0] = 1.0
        m.input_proj.weight[1, 1] = 1.0
    t = torch.arange(T, dtype=torch.float32)
    k = torch.arange(K, dtype=torch.float32)
    feats = torch.zeros(B, T, K, 4)
    feats[..., 0] = t[None, :, None]  # broadcast over B and K
    feats[..., 1] = k[None, None, :]  # broadcast over B and T
    m(feats, torch.eye(K))
    x = m.temporal[0].seen
    assert x.shape == (B * K, T, 64)
    assert torch.equal(x[:, :, 0], t.expand(B * K, T))                                        # each row runs over ALL frames
    assert torch.equal(x[:, :, 1], (torch.arange(B * K) % K).float()[:, None].expand(B * K, T))  # ...of ONE joint (row n -> joint n % K)



# ---- Test 3: loss on a hand-computed example (B=1, T=3, K=2, delta=0.01) ----
def test_3_loss_hand_example():
    target = torch.zeros(1, 3, 2, 2)              # target = 0, so the error is just |pred|
    pred = torch.zeros(1, 3, 2, 2)
    pred[0, 0, 0] = torch.tensor([0.10, 0.0])     # hidden : linear regime    -> 0.10 - 0.005 = 0.095
    pred[0, 1, 0] = torch.tensor([0.0, 0.20])     # hidden : linear regime    -> 0.20 - 0.005 = 0.195
    pred[0, 2, 0] = torch.tensor([0.004, 0.0])    # visible: quadratic regime -> 0.004^2 / (2*0.01) = 0.0008
    pred.requires_grad_()
    hidden = torch.zeros(1, 3, 2, dtype=torch.bool)
    hidden[0, :2, 0] = True                       # joint 0 at t=0,1
    visible = ~hidden                             # the other 4 joint-frames (joint 1 has zero error)
    total, parts = tgct_loss(pred, target, hidden, visible, lam=1.0, w_vis=0.1, delta=0.01)
    assert abs(parts["hidden"] - (0.095 + 0.195) / 2) < 1e-6          # mean over the 2 hidden joint-frames only
    assert abs(parts["visible"] - 0.0008 / 4) < 1e-6                  # mean over the 4 visible joint-frames
    # acc joint 0 = (0.104, -0.40), squared norm = 0.170816; joint 1 = 0.
    assert abs(parts["acc"] - 0.170816 / 2) < 1e-6
    assert abs(total.item() - (parts["hidden"] + 0.1 * parts["visible"] + 1.0 * parts["acc"])) < 1e-6
    total.backward()
    assert pred.grad is not None
    assert torch.isfinite(pred.grad).all()
    assert pred.grad.abs().max().item() > 0.0


def test_3b_loss_requires_three_frames():
    for T in (0, 1, 2):
        pred = torch.zeros(1, T, 2, 2)
        hidden = torch.zeros(1, T, 2, dtype=torch.bool)
        try:
            tgct_loss(pred, pred, hidden, ~hidden)
        except ValueError as error:
            assert "at least 3 frames" in str(error)
        else:
            raise AssertionError(f"Expected ValueError for T={T}")

def test_4_occlusion_stats():
    rng = np.random.default_rng(0)
    T, K = 128, 12
    rates, has_run = [], []
    for _ in range(1000):
        h = sample_occlusion(T, K, rng)
        rates.append(h.mean())
        run5 = h[:-4] & h[1:-3] & h[2:-2] & h[3:-1] & h[4:]  # contiguous runs of 5
        has_run.append(run5.any())
    assert 0.05 < np.mean(rates) < 0.6  
    assert all(has_run)  

# ---- Test 5: horizontal flip is an involution ----
def test_5_hflip_involution():
    rng = np.random.default_rng(0)
    coords = rng.random((10, 12, 2)).astype(np.float32)
    obs = rng.random((10, 12)) < 0.7
    conf = rng.random((10, 12)).astype(np.float32)
    c2, o2, f2 = hflip(*hflip(coords, obs, conf))
    assert np.allclose(c2, coords) and (o2 == obs).all() and np.allclose(f2, conf)
    assert (np.array(LR_SWAP)[LR_SWAP] == np.arange(12)).all()
    c1, _, _ = hflip(coords, obs, conf)
    assert np.allclose(c1[:, 0, 0], 1.0 - coords[:, 1, 0])    # new L_sho x == 1 - old R_sho x


if __name__ == "__main__":           # allows running without pytest
    test_1a_graph(); test_1b_layer_shapes(); print("test 1 OK")
    test_2a_identity_and_params(); test_2b_temporal_axis(); print("test 2 OK")
    test_3_loss_hand_example(); print("test 3 OK")
    test_3b_loss_requires_three_frames(); print("test 3 boundary OK")
    test_4_occlusion_stats(); print("test 4 OK")
    test_5_hflip_involution(); print("test 5 OK")

