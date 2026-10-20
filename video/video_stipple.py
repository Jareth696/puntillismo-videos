"""Puntillismo desde un video real: cada fotograma -> puntos (Voronoi con coherencia temporal). Salida 1080x1920 B/N o Matrix.

Uso: python3 video_stipple.py entrada.mp4 salida.mp4 [--desde 0] [--dur 10] [--puntos 30000] [--invertir] [--matrix]
"""
import argparse, subprocess, numpy as np
from scipy.spatial import cKDTree

W, H, FPS = 1080, 1920, 24
K = 2                                           # el mapa de densidad se calcula a 1/K de resolución

def leer_frames(path, desde, dur, cx):
    """ffmpeg: recorte vertical 9:16 (cx = centro horizontal 0..1), escala a W/K x H/K, gris."""
    vf = f"crop=ih*9/16:ih:(iw-ih*9/16)*{cx}:0,scale={W//K}:{H//K},fps={FPS},format=gray"
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", str(desde), "-t", str(dur), "-i", path, "-vf", vf,
                          "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    n = (W//K)*(H//K)
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(H//K, W//K).astype(float)/255

def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

def blur_grande(g, k=16):
    h, w = g.shape; s = g[:h//k*k, :w//k*k].reshape(h//k, k, w//k, k).mean(axis=(1, 3))
    for _ in range(3): s = blur(s)
    s = np.repeat(np.repeat(s, k, 0), k, 1); out = np.empty_like(g); out[:] = s.mean()
    out[:s.shape[0], :s.shape[1]] = s; return out

NIV = {}
def densidad(g, a):
    if a.invertir: g = 1 - g
    lo, hi = np.percentile(g, 2), np.percentile(g, 99.5)          # contraste automático (suavizado en el tiempo)
    NIV.setdefault("lo", lo); NIV.setdefault("hi", hi)
    NIV["lo"] += 0.1*(lo - NIV["lo"]); NIV["hi"] += 0.1*(hi - NIV["hi"])
    g = np.clip((g - NIV["lo"])/max(NIV["hi"] - NIV["lo"], 0.05), 0, 1)
    if a.aislar > 0:                                                 # resta el fondo suave: quedan los objetos
        g = np.clip((g - a.aislar*blur_grande(g))/(1 - a.aislar*0.5), 0, 1)
    gy, gx = np.gradient(blur(blur(g)))
    edge = np.clip(np.hypot(gx, gy)*a.bordes, 0, 1)
    d = np.clip((g - a.negro)/(1 - a.negro), 0, 1)**a.gamma + 0.35*edge
    return d + 1e-5

class Stippler:
    def __init__(self, n, h, w, seed=0):
        self.n = n; self.rng = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:h, 0:w]; self.px = np.c_[xx.ravel()+0.5, yy.ravel()+0.5]; self.pts = None
    def sample(self, d, k):
        p = d.ravel()/d.sum(); i = self.rng.choice(d.size, k, p=p)
        return self.px[i] + self.rng.uniform(-0.5, 0.5, (k, 2))
    def step(self, d, iters):
        if self.pts is None: self.pts = self.sample(d, self.n); iters = max(iters, 20)
        wt = d.ravel(); m = wt > 2e-3; px = self.px[m]; wt = wt[m]
        for _ in range(iters):
            _, lab = cKDTree(self.pts).query(px, workers=-1)
            sw = np.bincount(lab, wt, self.n); sx = np.bincount(lab, wt*px[:, 0], self.n); sy = np.bincount(lab, wt*px[:, 1], self.n)
            ok = sw > 1e-6; self.pts[ok] = np.c_[sx[ok]/sw[ok], sy[ok]/sw[ok]]
            if (~ok).any(): self.pts[~ok] = self.sample(d, (~ok).sum())
        # brillo de cada punto = densidad local (zonas tenues -> puntos tenues)
        ix = np.clip(self.pts[:, 0].astype(int), 0, d.shape[1]-1); iy = np.clip(self.pts[:, 1].astype(int), 0, d.shape[0]-1)
        return self.pts*K, d[iy, ix]

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada"); ap.add_argument("salida")
    ap.add_argument("--desde", type=float, default=0); ap.add_argument("--dur", type=float, default=10)
    ap.add_argument("--puntos", type=int, default=30000); ap.add_argument("--iters", type=int, default=3)
    ap.add_argument("--centro", type=float, default=0.5, help="recorte horizontal 0=izq 1=der")
    ap.add_argument("--negro", type=float, default=0.15); ap.add_argument("--gamma", type=float, default=1.6)
    ap.add_argument("--bordes", type=float, default=8.0); ap.add_argument("--invertir", action="store_true")
    ap.add_argument("--aislar", type=float, default=0.0, help="0..1: cuánto restar el fondo suave")
    ap.add_argument("--brillo", type=float, default=3.0)
    a = ap.parse_args()
    rng = np.random.default_rng(1); big = rng.uniform(size=a.puntos) < 0.2; tw = rng.uniform(0, 6.28, a.puntos)
    st = Stippler(a.puntos, H//K, W//K)
    out = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "15", a.salida], stdin=subprocess.PIPE)
    total = int(a.dur*FPS)
    for f, g in enumerate(leer_frames(a.entrada, a.desde, a.dur, a.centro)):
        t = f/FPS
        pts, lum = st.step(densidad(g, a), a.iters)
        w = (0.55 + 0.45*np.clip(lum*1.6, 0, 1))*(0.92 + 0.08*np.sin(t*3 + tw))*a.brillo
        sm = np.zeros((H, W)); bg = np.zeros((H, W))
        splat(sm, pts[~big, 0], pts[~big, 1], w[~big]); splat(bg, pts[big, 0], pts[big, 1], w[big])
        img = (sm + 2.2*blur(bg))*min(1, t/0.6, (a.dur - t)/0.6)
        out.stdin.write((np.clip(img, 0, 1)*255).astype(np.uint8).tobytes())
        if f % 24 == 0: print(f"{f}/{total}", flush=True)
    out.stdin.close(); out.wait()

if __name__ == "__main__": main()
