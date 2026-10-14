# phase2/tests/test_tgct.py
"""Tests for phase2.tgct (worksheet phase2C_tgct_worksheet_1009, tests 1-5)."""
import numpy as np
import torch
from phase2.tgct.graph import body12_A_norm, EDGES12, LR_SWAP
from phase2.tgct.layers import GCTLayer, TemporalAttention

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


if __name__ == "__main__":           # allows running without pytest
    test_1a_graph(); test_1b_layer_shapes(); print("test 1 OK")