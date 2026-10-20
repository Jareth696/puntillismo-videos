"""Puntillismo B/N: rostro de Tesla -> bombilla que se enciende sin cables. 1080x1920."""
import os, sys, subprocess, numpy as np
import formas, stipple

W, H, FPS, DUR = 1080, 1920, 24, 23
N = 40000
rng = np.random.default_rng(3)
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))

# ---------- puntos (con caché) ----------
if os.path.exists("cache.npz"):
    c = np.load("cache.npz"); PT, PB, FW = c["pt"], c["pb"], c["fw"]
else:
    dt = formas.tesla(scale=0.75); PT, _ = stipple.voronoi(dt, N, 30, 1); PT /= 0.75
    db, fm, _ = formas.bombilla(scale=0.75); PB, _ = stipple.voronoi(db, N, 30, 2)
    FW = fm[np.clip(PB[:, 1].astype(int), 0, fm.shape[0]-1), np.clip(PB[:, 0].astype(int), 0, fm.shape[1]-1)]; PB /= 0.75
    np.savez("cache.npz", pt=PT, pb=PB, fw=FW)
BCX, BCY, BR = 540, 820, 300
# emparejar por curva de Hilbert: vecinos en la cara -> vecinos en la bombilla
oa = stipple.hilbert_order(PT); ob = stipple.hilbert_order(PB)
A = PT[oa]; B = PB[ob]; FW = FW[ob]
rank = np.arange(N)/N
START = np.c_[rng.uniform(-100, W+100, N), rng.uniform(-150, H+150, N)]
d_in = rng.uniform(0, 1, N)**1.3*2.2                 # demora de llegada
d_tr = rank*1.4 + rng.uniform(0, 0.25, N)            # onda de transformación por la curva
perp = np.c_[-(B-A)[:, 1], (B-A)[:, 0]]
OFF = perp*rng.uniform(-0.35, 0.35, N)[:, None] + rng.normal(0, 45, (N, 2))
big = rng.uniform(size=N) < 0.22
tw = rng.uniform(0, 6.28, N)
# halo y rayos de luz
NHL = 9000; ha = rng.uniform(0, 2*np.pi, NHL); hr = 20 + rng.exponential(170, NHL)
HX = BCX + hr*np.cos(ha); HY = BCY + 10 + hr*np.sin(ha)*0.95; HB = np.exp(-hr/240)
T_FACE, T_MORPH, T_ARCS, T_ON = 4.5, 9.0, 13.2, 15.0

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)
def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p
def glow(b, k=8):
    s = b.reshape(H//k, k, W//k, k).mean(axis=(1, 3))
    for _ in range(7): s = _blur_small(s)
    return np.repeat(np.repeat(s, k, 0), k, 1)
def _blur_small(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

def light(t):
    """Encendido con parpadeo."""
    if t < T_ON: return 0.0
    k = t - T_ON
    seq = [(0.00, 0.07, 0.8), (0.07, 0.20, 0.0), (0.20, 0.28, 0.6), (0.28, 0.45, 0.15)]
    for a, b, v in seq:
        if a <= k < b: return v
    return float(ss(0.45, 1.3, k))*(0.96 + 0.04*np.sin(t*37)*np.sin(t*11))

def bolt(p0, p1, r, disp, depth=7):
    pts = np.array([p0, p1], float)
    for _ in range(depth):
        mid = (pts[:-1] + pts[1:])/2; seg = pts[1:] - pts[:-1]
        nrm = np.c_[-seg[:, 1], seg[:, 0]]; nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
        mid += nrm*r.normal(0, 1, (len(mid), 1))*disp; disp *= 0.55
        out = np.empty((len(pts)*2-1, 2)); out[0::2] = pts; out[1::2] = mid; pts = out
    seg = np.linalg.norm(pts[1:]-pts[:-1], axis=1); k = np.maximum((seg/2.5).astype(int), 1)
    return np.concatenate([np.linspace(pts[i], pts[i+1], k[i], endpoint=False) for i in range(len(seg))])

def arcs(t, sm, bg, inten):
    slot = int(t*14); r = np.random.default_rng(slot*7 + 1)
    nb = r.poisson(inten*2.2)
    for _ in range(nb):
        a = r.uniform(-np.pi*0.95, np.pi*0.15)                    # llegan desde arriba y los lados
        end = np.array([BCX + BR*0.98*np.cos(a), BCY + BR*0.98*np.sin(a)])
        st = np.array([BCX + r.uniform(560, 900)*np.cos(a + r.normal(0, .25)), BCY + r.uniform(560, 900)*np.sin(a + r.normal(0, .25))])
        p = bolt(st, end, r, np.linalg.norm(end-st)*0.18)
        fade = 1 - ((t*14) % 1)*0.6
        splat(sm, p[:, 0], p[:, 1], np.full(len(p), 1.0*fade)); splat(bg, p[:, 0], p[:, 1], np.full(len(p), 0.8*fade))
        if r.uniform() < 0.6:                                     # rama secundaria
            i = r.integers(len(p)//4, len(p)*3//4); q = bolt(p[i], p[i] + r.normal(0, 120, 2), r, 40, 5)
            splat(sm, q[:, 0], q[:, 1], np.full(len(q), 0.6*fade))

def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W)); gl = np.zeros((H, W))
    # ---- posición de cada punto ----
    e_in = ss(0, 1, (t - d_in)/2.3)
    e_tr = ss(0, 1, (t - T_MORPH - d_tr)/2.0)
    breath = np.c_[np.sin(t*0.9 + tw), np.cos(t*0.7 + tw*1.3)]*0.8
    face = A + breath
    zoom = 1 + 0.07*ss(T_FACE-0.5, T_MORPH+0.3, t)                        # acercamiento lento a la cara
    face = (face - [540, 700])*zoom + [540, 700]
    pos = START*(1-e_in[:, None]) + face*e_in[:, None]
    swirl = np.sin(np.pi*e_tr)[:, None]*OFF
    pos = pos*(1-e_tr[:, None]) + B*e_tr[:, None] + swirl
    # ---- brillo ----
    L = light(t)
    base = 0.85 + 0.15*np.sin(t*2.1 + tw)
    trav = np.sin(np.pi*e_tr)                                             # más brillo mientras viajan
    bulb_dim = 0.6 + 0.8*L
    wgt = 2.1*base*(0.25 + 0.75*e_in)*(1 + 0.5*trav)
    wgt = wgt*np.where(e_tr > 0.99, bulb_dim, 1)
    fil = FW*e_tr
    wgt = wgt + fil*L*1.8
    splat(sm, pos[~big, 0], pos[~big, 1], wgt[~big]); splat(bg, pos[big, 0], pos[big, 1], wgt[big])
    splat(gl, pos[:, 0], pos[:, 1], fil*(0.15 + 5.0*L))
    inside = (np.hypot(B[:, 0]-BCX, B[:, 1]-BCY) < BR*0.97)*e_tr
    splat(gl, pos[:, 0], pos[:, 1], inside*L*0.06)
    # ---- rayos (sin cables) ----
    ia = ss(T_ARCS, T_ON, t)*(1 - 0.75*ss(T_ON+0.5, T_ON+2.5, t))*(1 - ss(DUR-2.5, DUR-1.2, t))
    if ia > 0.02: arcs(t, sm, bg, ia*1.6)
    # ---- halo y rayos de luz ----
    if L > 0:
        hb = HB*L*(0.75 + 0.25*np.sin(t*3 + ha*5))
        splat(sm, HX, HY, hb*1.6); splat(gl, HX, HY, hb*0.3)
        for k in range(28):
            ang = k*2*np.pi/28 + t*0.05; r_ = np.arange(BR+40, BR+520, 7.0)
            splat(sm, BCX + r_*np.cos(ang), BCY + r_*np.sin(ang), L*0.30*(1 - (r_-BR-40)/480)**1.5*(0.6 + 0.4*np.sin(t*1.3 + k)))
    img = sm + 2.2*blur(bg) + 2.4*glow(gl)
    img = img*(1 - ss(DUR-1.6, DUR-0.1, t))
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

def fb(f): return frame(f/FPS).tobytes()
if __name__ == "__main__":
    from multiprocessing import Pool
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else FPS*DUR
    p = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","gray","-s",f"{W}x{H}",
        "-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","15",out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(fb, range(n), chunksize=2): p.stdin.write(b)
    p.stdin.close(); p.wait()
