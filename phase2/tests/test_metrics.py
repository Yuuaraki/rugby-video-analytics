import numpy as np, sys
from pathlib import Path
sys.path.append(str(Path.home() / "rugby-video-analytics"))
from phase2.metrics import compute_jitter, jk_table

# Test 1: uniform motion -> every step has length |v|, so the mean must be exactly |v|
T, K, v = 50, 3, np.array([0.003, 0.004])                      # |v| = 0.005
P = np.zeros((T, K, 2)) + np.arange(T)[:, None, None] * v
assert np.allclose(compute_jitter(P).mean(axis=0), 0.005)

# Test 2: the "occluded" aggregation counts pairs by the LATER frame's confidence
confs = np.full((T, K), 0.9); confs[5:10, 0] = 0.2            # later frames 5..9 -> 5 pairs
tbl = jk_table(P, confs)
assert tbl[0]["n_occ"] == 5 and np.isclose(tbl[0]["Jk_occ"], 0.005)

# Test 3 (regression): the ported ruler must reproduce the B1 table on the uvd sheet
z = np.load(Path.home() / "data/phase2_npz/hybrik_uvd_tackle_01.npz")
Jk = compute_jitter(z["coords"]).mean(axis=0)
print("L_sho", round(Jk[0], 5), "(expect 0.00646)   R_wri", round(Jk[5], 5), "(expect 0.01175)")
assert np.isclose(Jk[0], 0.00646, atol=2e-5) and np.isclose(Jk[5], 0.01175, atol=2e-5)
print("all tests passed")