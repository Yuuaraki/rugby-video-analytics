# phase2/tgct/layers.py
import math, torch, torch.nn as nn, torch.nn.functional as F

# --- Phase 1 classes (notebooks/Skelton_graph_GCN.ipynb, cell index 7 / 9 / 12 / 13), copied VERBATIM ---

class GraphConvLayer(nn.Module):
    '''
    H^{(l+1)} = σ( Â * H^{(l)} * W^{(l)} + b^{(l)} )

    It is corresponding to Ji et al. (2025)'s formula:
      h_i^{(l+1)} = σ( Σ_{j∈N(i)} (1/√(d_i*d_j)) * W^{(l)} * h_j^{(l)} + b^{(l)} )
    '''

    def __init__(self, in_features, out_features):
        super().__init__()

        # W^{(l)}: Learnable weight matrix for linear transformation
        self.W = nn.Linear(in_features, out_features, bias=False)

        # Xavier initialization for better convergence and to reduce vanishing gradients
        nn.init.xavier_uniform_(self.W.weight)

    def forward(self, H, A_norm):
        """
        Parameters:
            H: Node features (shape: [batch, N, F_in])
            A_norm: Normalized adjacency matrix (shape: [N, N])
        Returns:
            H_new: Updated node features (shape: [batch, N, F_out])
        """
        # Step 1: A * H -> Aggregate neighbor features
        #   A_norm: [N, N], H: [batch, N, F_in]
        #   A_norm @ H: [batch, N, F_in] (matrix multiplication)
        support = torch.matmul(A_norm, H)

        # Step 2: (A * H) * W -> Linear transformation
        output = self.W(support)

        return output

class MultiHeadAttention(nn.Module):
    '''
    Multi-Head Attention for skelton graph.
    Attention(Q,K,V) = softmax(QK^T / √d_k) V
    
    w_ij = softmax_j(Q h_i・K h_j / √d_k) (attention weight from node i to node j)
    h_i^{new} = O_h || Σ_j w_ij V h_j (updated feature for node i)
    
    H = Shape: [batch, N, d_model]
    B = batch size
    N = number of nodes
    d_model = feature dimension

    '''
    def __init__(self, d_model, num_heads=4, dropout=0.1):
        super().__init__()
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        # Learnable weight matrices for Q, K, V
        self.W_Q = nn.Linear(d_model, d_model)
        self.W_K = nn.Linear(d_model, d_model)
        self.W_V = nn.Linear(d_model, d_model)
        
        # Output linear layer
        self.W_O = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.d_k) # Scaling factor for attention scores to prevent large values in softmax
        
    def forward(self, H, mask=None):
        '''
        parameters:
           H: Node features (shape: [batch, N, d_model]) (N=17 nodes, d_model=feature dimension)
           mask: Optional mask for attention (shape: [N, N]) (1 for allowed attention, 0 for masked)
        returns:
           out: Updated node features after multi-head attention (shape: [batch, N, d_model])
           attn_weights: Attention weights for visualization (shape: [batch, num_heads, N, N])        
        '''        
        B, N, _ = H.size()
        
        # Step 1: Linear projections to get Q, K, V
        Q = self.W_Q(H).view(B, N, self.num_heads, self.d_k).transpose(1, 2)  # [B, num_heads, N, d_k]
        K = self.W_K(H).view(B, N, self.num_heads, self.d_k).transpose(1, 2)  # [B, num_heads, N, d_k]
        V = self.W_V(H).view(B, N, self.num_heads, self.d_k).transpose(1, 2)  # [B, num_heads, N, d_k]
        # Q,K,V: [batch, num_heads, N, d_k]
        
        # Step 2: Attention scores = QK^T / √d_k
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale  # [B, num_heads, N, N]
        
        # Step 3: Apply mask (if provided)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)  # Masked positions get large negative scores
        
        # Step 4: Softmax to get attention weights
        attn_weights = F.softmax(scores, dim=-1)  # [B, num_heads, N, N]
        attn_weights = self.dropout(attn_weights)       # Apply dropout to attention weights
        
        # Step 5: Weighted sum of values
        context = torch.matmul(attn_weights, V)  # [B, num_heads, N, d_k]
        
        # Step 6: Concatenate heads and apply output linear layer
        context = context.transpose(1, 2).contiguous().view(B, N, self.d_model)  # [B, N, d_model]
        out = self.W_O(context)  # [B, N, d_model]
        
        return out, attn_weights

class GatingMechanism(nn.Module):
    '''
    Confidence-aware gating for skeleton keypoints
    
    Suppresses afeatrure of low-confidence keypionts,
    so that features completed by GCN are weighted more heavilily
    '''
    
    def __init__(self, d_model):
        super().__init__()
        self.gate_linear = nn.Linear(d_model, d_model)  # Learnable linear layer for gating
    
    def forward(self, x):
        gate_values = torch.sigmoid(self.gate_linear(x))  # [B, N, d_model]
        gated = x * gate_values  # Element-wise multiplication
        return gated, gate_values
    
class GCTLayer(nn.Module):
    '''
    Graph Convolutional Transformer Layer
    = GCN (local) + Attention (global) + gating + FFN
    '''
    
    def __init__(self, d_model, num_heads=4, ffn_dim=128, dropout=0.1):
        super().__init__()
        
        #1 GCN (local neighborhood aggregation)
        self.gcn = GraphConvLayer(d_model, d_model)
        
        #2 Multi-Head Attention (global context)
        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
        
        #3 Gating Mechanism (confidence-aware feature filtering)
        self.gating = GatingMechanism(d_model)
        
        #4 Feed-Forward Network
        # FFN Linear (d-> ffn_dim) -> ReLu -> Linear (ffn_dim -> d)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, ffn_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ffn_dim, d_model),
            nn.Dropout(dropout)
        )
        
        #5 Layer Normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, H, A_norm):
        """
        Processing flow: 
        H -> [GCN + Residual + Norm] -> [Attn + Gate + Residual + Norm]
          -> [FFN + Residual + Norm] -> H_new
          
        Parameters:
        H: [batch, 17, d_model]
        A_model: [17, 17] normalized adjacency matrix
        """
        # -- 1. GCN Layer ---
        gcn_out = self.gcn(H, A_norm)  # [B, 17, d_model]
        H = self.norm1(H + self.dropout(gcn_out))  # Residual + Norm
        
        # -- 2. Multi-Head Attention + Gating ---
        attn_out, attn_weights = self.attention(H)  # [B, 17, d_model], [B, num_heads, 17, 17]
        gated_out, gate_values = self.gating(attn_out)  # [B, 17, d_model], [B, 17, d_model]
        H = self.norm2(H + self.dropout(gated_out))  # Residual + Norm
        
        # -- 3. Feed-Forward Network ---
        ffn_out = self.ffn(H)  # [B, 17, d_model]
        H = self.norm3(H + self.dropout(ffn_out))  # Residual + Norm
        
        return H, attn_weights, gate_values
    
    
class TemporalAttention(nn.Module):
    """The SAME attention, applied along time: input (N, T, d) where N = batch*joints."""
    def __init__(self, d_model, num_heads=4, dropout=0.1, max_len=256):
        super().__init__()
        self.attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.pos = nn.Parameter(torch.zeros(1, max_len, d_model))  # Positional embeddings
        nn.init.normal_(self.pos, std=0.02)  # Initialize positional embeddings with normal distribution
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):                      # x: (N, T, d), N = batch*joints
        T = x.size(1)  # Sequence length (time dimension)
        h = x + self.pos[:, :T]                # 1) Add positional embeddings, using only the first T of max_len=256 positions
        out, w = self.attn(h)                  # 2) Phase 1 MHA treats dim 1 as nodes; here, each node is a frame
        return self.norm(x + self.dropout(out)), w   # 3) Residual connection + LayerNorm, following the Phase 1 GCTLayer pattern