# phase2/tgct/model.py
import torch, torch.nn as nn
from .layers import GCTLayer, TemporalAttention

class TGCT(nn.Module):
    """Factorised spatio-temporal GCT. Input (B, T, K, 4) = (x_fill, y_fill, conf, m); output residual (B, T, K, 2)."""
    def __init__(self, in_features=4, d_model=64, num_heads=4, ffn_dim=128, num_blocks=2, dropout=0.1, max_len=256):
        super().__init__()
        self.input_proj = nn.Linear(in_features, d_model)
        self.spatial = nn.ModuleList([GCTLayer(d_model, num_heads, ffn_dim, dropout) for _ in range(num_blocks)])
        self.temporal = nn.ModuleList([TemporalAttention(d_model, num_heads, dropout, max_len) for _ in range(num_blocks)])
        self.output_proj = nn.Linear(d_model, 2)
        nn.init.zeros_(self.output_proj.weight)
        nn.init.zeros_(self.output_proj.bias) # design: start AT the interpolation
    
    def forward(self, feats, A_norm):
        B, T, K, C = feats.shape
        h = self.input_proj(feats)
        for sp, tp in zip(self.spatial, self.temporal):
            # spatial: fold (B, T) into the batch -> each frame is one 12-joint graph
            h, _, _ = sp(h.reshape(B * T, K, -1), A_norm)
            h = h.reshape(B, T, K, -1)
            # temporal: fold (B, K) into the batch -> each joint is one T-step sequence
            h = h.permute(0, 2, 1, 3).reshape(B * K, T, -1)
            h, _ = tp(h)
            h = h.reshape(B, K, T, -1).permute(0, 2, 1, 3)
        return self.output_proj(h)
    
    