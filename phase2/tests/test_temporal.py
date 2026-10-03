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

# ---- Test 6: leading gap — recursion starts at t0; frames before t0 hold z[t0] ----
obs_lead = obs_all.copy(); obs_lead[:20] = False
full = kf_cv_1d(p_true, obs_all, sigma_a=1e-4, sigma_m=3e-3)
lead = kf_cv_1d(p_true, obs_lead, sigma_a=1e-4, sigma_m=3e-3)
assert np.allclose(lead["smooth"][20:], full["smooth"][20:], atol=1e-6)
assert np.allclose(lead["smooth"][:20], p_true[20]) and np.allclose(lead["filt"][:20], p_true[20])
print("test 6: leading gap OK")

# ---- Test 5: hide_and_predict ----
from phase2.temporal import hide_and_predict
rng = np.random.default_rng(1)
T, K = 900, 12
sa_true, sm_true = 3e-4, 3e-3
acc = rng.normal(0, sa_true, size=(T, K, 2)) 
vel = np.cumsum(acc, axis=0) + rng.normal(0, 0.003, size=(1, K, 2))
pos = 0.5 + np.cumsum(vel, axis=0)
z = pos + rng.normal(0, sm_true, pos.shape)
err, starts = hide_and_predict(z, np.ones((T, K), dtype=bool), sigma_m=sm_true)
best = min((k for k in err if k != 'interp'), key = err.get)
assert len(starts) == 20 and best in (1e-4, 3e-4, 1e-3), (best, err)     # within a factor of 3 of the truth
assert err[best] < err["interp"], err
print("test 5:", {k: round(float(v), 5) for k, v in err.items()}, "best:", best)



print("all temporal tests passed")