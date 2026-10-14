# phase2/tgct/graph.py
import numpy as np
BODY12 = ["L_sho","R_sho","L_elb","R_elb","L_wri","R_wri","L_hip","R_hip","L_kne","R_kne","L_ank","R_ank"]
COCO_IDX_BODY12 = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
EDGES12 = [(0,1),(0,2),(2,4),(1,3),(3,5),(0,6),(1,7),(6,7),(6,8),(8,10),(7,9),(9,11)]
LR_SWAP = [1,0,3,2,5,4,7,6,9,8,11,10]

def build_adjacency_matrix(num_nodes, edges, add_self_loops=True):
    """
    Build adjacency matrix A from skeleton connection list.
    
    ■ Mathematical meaning:
      A ∈ R^{N×N}, A[i][j] = 1 if (i,j) ∈ E
      Since it is an undirected graph, A is a symmetric matrix: A = A^T
    
    ■ Adding Self-loops:
      A_hat = A + I (I = identity matrix)
      → To retain each node's own features during GCN updates
    
    Parameters:
        num_nodes: Number of nodes (17)
        edges: List of edges [(i, j), ...]
        add_self_loops: Whether to add self-loops
    
    Returns:
        A: Adjacency matrix (numpy array, shape [N, N])
    """
    
    A = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    for i, j in edges:
        A[i][j] = 1
        A[j][i] = 1  # Undirected graph
    if add_self_loops:
        A = A + np.eye(num_nodes, dtype=np.float32)  # A_hat = A + I 
    return A

def normalize_adjacency(A):
    """
    Symmetric normalization: D^{-1/2} * A * D^{-1/2}
    
    This is the standard normalization proposed in the GCN paper by Kipf & Welling (2017).
    Corresponds to equation (5) in the attached paper (GCT, Dwivedi & Bresson):
      h_i^{l+1} = σ( Σ_j (1/√(d_i * d_j)) * W * h_j )
    
    Parameters:
        A: Adjacency matrix (numpy array, shape [N, N])
    
    Returns:
        A_norm: Normalized adjacency matrix
    """
    #Step1: Compute degree matrix D
    #D_ii = Σ_j A_ij; D is a diagonal matrix where each diagonal element D_ii is the degree of node i
    D = np.diag(A.sum(axis=1))  # D_ii = Σ_j A_ij
    
    # Step 2: Compute D^{-1/2} 
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(D) + 1e-8))  # D^{-1/2}
    
    #Step3: D^{-1/2} * A * D^{-1/2}
    A_norm = D_inv_sqrt @ A @ D_inv_sqrt                 # D^{-1/2} A D^{-1/2}
    return A_norm

def body12_A_norm():
    """Normalised adjacency D^-1/2 (A+I) D^-1/2 for the 12-joint graph."""
    return normalize_adjacency(build_adjacency_matrix(12, EDGES12, add_self_loops=True))