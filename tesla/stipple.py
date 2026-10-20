"""Stippling de Voronoi ponderado (Secord 2002): reparte N puntos según una imagen de densidad."""
import numpy as np
from scipy.spatial import cKDTree

def sample(dens, n, rng):
    p = dens.ravel()/dens.sum(); idx = rng.choice(dens.size, n, p=p)
    y, x = np.divmod(idx, dens.shape[1]); return np.c_[x + rng.uniform(size=n), y + rng.uniform(size=n)]

def voronoi(dens, n, iters=30, seed=0):
    rng = np.random.default_rng(seed); h, w = dens.shape
    pts = sample(dens, n, rng)
    yy, xx = np.mgrid[0:h, 0:w]; m = dens.ravel() > 1e-4
    px = np.c_[xx.ravel()[m]+0.5, yy.ravel()[m]+0.5]; wt = dens.ravel()[m]
    for _ in range(iters):
        _, lab = cKDTree(pts).query(px, workers=-1)
        sw = np.bincount(lab, wt, n); sx = np.bincount(lab, wt*px[:, 0], n); sy = np.bincount(lab, wt*px[:, 1], n)
        ok = sw > 0; pts[ok] = np.c_[sx[ok]/sw[ok], sy[ok]/sw[ok]]
        pts[~ok] = sample(dens, (~ok).sum(), rng)                 # reubicar puntos sin celda
    return pts, sw

def hilbert_order(pts, order=10):
    """Índice de la curva de Hilbert: puntos cercanos en la curva = cercanos en el plano."""
    mn, mx = pts.min(0), pts.max(0); n = 2**order
    q = ((pts - mn)/(mx - mn).max()*(n-1)).astype(np.int64); x, y = q[:, 0].copy(), q[:, 1].copy(); d = np.zeros(len(pts), np.int64)
    s = n//2
    while s > 0:
        rx = (x & s) > 0; ry = (y & s) > 0
        d += s*s*((3*rx) ^ ry)
        sw = ~ry; fl = sw & rx
        x[fl] = s-1-x[fl]; y[fl] = s-1-y[fl]
        x[sw], y[sw] = y[sw].copy(), x[sw].copy()
        s //= 2
    return np.argsort(d)
