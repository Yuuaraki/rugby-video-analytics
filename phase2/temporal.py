import numpy as np
#from pyproj import err

def interpolate_gaps(z, observed):
    """z: (T,) 1-D series; observed: (T,) bool. Linear interpolation across unobserved runs; edges held constant.""" 
    idx = np.flatnonzero(observed)
    return np.interp(np.arange(len(z)), idx, z[idx])

def kf_cv_1d(z, observed, sigma_a, sigma_m):
    """Constant-velocity Kalman filter + RTS smoother on ONE 1-D series (worksheet 0.2-0.5).
    Returns dict(filt=(T,) positions after the forward filter, smooth=(T,) after RTS, vel=(T,) smoothed velocity).""" 
    T = len(z)
    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    Q = sigma_a**2 * np.array([[0.25, 0.5], [0.5, 1.0]])
    r = sigma_m**2
    x_pred = np.zeros((T,2)); P_pred = np.zeros((T,2,2))
    x_filt = np.zeros((T,2)); P_filt = np.zeros((T,2,2))
    
    t0 = int(np.flatnonzero(observed)[0]) # first observed time step
    x = np.array([z[t0], 0.0]); P = np.diag([r, 1.0]) 
    #start: known position, unknown velocity
    
    for t in range(T):
        if t > 0:
            x = F @ x; 
            P = F @ P @ F.T + Q
        x_pred[t] = x
        P_pred[t] = P
        
        if observed[t] and t >= t0:
            y = z[t] - x[0]
            S = P[0, 0] + r
            K = P[:, 0] / S
            x = x + K * y
            P = P - np.outer(K, P[0, :])

        x_filt[t] = x
        P_filt[t] = P
        
    x_s = x_filt.copy(); P_s = P_filt.copy()
    for t in range(T-2, -1, -1):
        C = P_filt[t] @ F.T @ np.linalg.inv(P_pred[t+1])
        x_s[t] = x_filt[t] + C @ (x_s[t+1] - x_pred[t+1])
        P_s[t] = P_filt[t] + C @ (P_s[t+1] - P_pred[t+1]) @ C.T

    return dict(filt=x_filt[:,0], smooth=x_s[:,0], vel=x_s[:,1])

def observed_mask(coords, confs, tau=0.5):
    """(T,K) bool: joint observed if conf >= tau AND the frame is not an all-zero (no-detection) frame."""    
    no_det = np.all(coords == 0, axis=(1,2))
    return (confs >= tau) & (~no_det)[:, None]  

def estimate_sigma_m(coords, obs):
    """Second-difference estimator (worksheet 0.6) over frames where t-1, t, t+1 are all observed. Returns one scalar (median over joints/axes)."""
    r = coords[1:-1] - 0.5*(coords[:-2] + coords[2:])
    mask = obs[:-2] & obs[1:-1] & obs[2:]
    stds = []
    for k in range(r.shape[1]):          # joint
        for a in range(2):               # axis
            ok = mask[:, k]
            if ok.sum() >= 2:
                stds.append(np.std(r[ok, k, a]))
    return float(np.median(stds)) / np.sqrt(1.5)

def smooth_sheet(coords, confs, sigma_a, sigma_m, tau=0.5):
    """Apply per joint, per axis. coords (T,K,2), confs (T,K) -> dict(interp, filt, smooth), each (T,K,2)."""
    obs = observed_mask(coords, confs, tau=tau)
    out = {k: np.zeros_like(coords) for k in ['interp', 'filt', 'smooth']}
    
    for k in range(coords.shape[1]):  # iterate over joints
        for a in range(2):
            z = coords[:, k, a]
            ob = obs[:, k]
            out['interp'][:, k, a] = interpolate_gaps(z, ob)
            kf_res = kf_cv_1d(z, ob, sigma_a, sigma_m)
            out['filt'][:, k, a] = kf_res['filt']
            out['smooth'][:, k, a] = kf_res['smooth']

    return out

def hide_and_predict(coords, obs, sigma_m, sigma_a_grid=(1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3), win=30, n_win=20, seed=0):
    """Worksheet ex. d: hide n_win fully-observed windows of `win` frames, run RTS for each sigma_a, and measure the
    mean joint error (Euclidean, Phase-1 units) inside the hidden windows against the raw visible coordinates.
    coords (T,K,2), obs (T,K) bool. Returns (err: dict {sigma_a or 'interp': error}, starts: list of window starts)."""
    T, K, _ = coords.shape
    # 1. candidate starts: windows where ALL joints are observed on EVERY frame
    full = np.array([obs[t:t + win].all() for t in range(T - win + 1)])
    cand = np.flatnonzero(full)
    rng = np.random.default_rng(seed)
    rng.shuffle(cand)
    start = []
    for s in cand:
        all_good = True
        for prev_s in start:
            if abs(s - prev_s) < win:
                all_good = False
                break
        if all_good:
            start.append(s)
        if len(start) >= n_win:
            break

    hidden = np.zeros(T, bool)
    for s in start:
        hidden[s:s + win] = True
    obs_h= obs & (~hidden)[:, None]
    err = {}
    # 2. linear interpolation on the same windows (reference line in the figure)
    est = np.zeros_like(coords)
    for k in range(K):
        for a in range(2):
            est[:, k, a] = interpolate_gaps(coords[:, k, a], obs_h[:, k])
    err['interp'] = np.linalg.norm(est - coords, axis=-1)[hidden].mean()
    # 3. RTS per sigma_a
    for sa in sigma_a_grid:
        est = np.zeros_like(coords)
        for k in range(K):
            for a in range(2):
                kf_res = kf_cv_1d(coords[:, k, a], obs_h[:, k], sa, sigma_m)
                est[:, k, a] = kf_res['smooth']
        err[sa] = np.linalg.norm(est - coords, axis=-1)[hidden].mean()
    return err, start