import numpy as np, sys
from pathlib import Path
sys.path.append(str(Path.home() / "rugby-video-analytics"))
from phase2.temporal import interpolate_gaps, kf_cv_1d

T = 80; t = np.arange(T); p_true = 0.30 + 0.004 * t
# constant velocity model. Phase-1 units
obs_all = np.ones(T, dtype=bool)

#test 1: noise-free, fully observed -> RS reproduces the line exacly (filter only asymptotically)
res = kf_cv_1d(p_true, obs_all, sigma_a=1e-4, sigma_m=3e-3)
assert np.allclose(res['smooth'], p_true, atol=1e-6)
assert np.allclose(res['vel'][10:], 0.004, atol=1e-4)

# Test 2: a 15-frame gap in the middle -> the prior fills it exactly (both interp and RTS)
obs_gap = obs_all.copy(); obs_gap[30:45] = False
res = kf_cv_1d(p_true, obs_gap, sigma_a=1e-4, sigma_m=3e-3)
assert np.allclose(res['smooth'][30:45], p_true[30:45], atol=1e-6)
assert np.allclose(interpolate_gaps(p_true, obs_gap), p_true, atol=1e-9)

# Test 3: white measurement noise -> RTS reduces the error at least 2x (sigma_a small relative to sigma_m)
rng = np.random.default_rng(0);z = p_true + rng.normal(0,0.01,T)
res = kf_cv_1d(z, obs_all, sigma_a=1e-4, sigma_m=0.01)
assert np.std(res['smooth'] - p_true) < 0.5 * np.std(z - p_true)

# Test 4: a gap that runs to the END -> filter extrapolates at constant velocity (no crash, finite values)
obs_end = obs_all.copy(); obs_end[60:] = False
res = kf_cv_1d(p_true, obs_end, sigma_a=1e-4, sigma_m=3e-3)
assert np.isfinite(res["smooth"]).all() and abs(res["smooth"][-1] - p_true[-1]) < 1e-3
print("all temporal tests passed")