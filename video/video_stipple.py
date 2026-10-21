"""Puntillismo desde un video real: cada fotograma -> puntos (Voronoi con coherencia temporal). Salida 1080x1920 B/N o Matrix.

Uso: python3 video_stipple.py entrada.mp4 salida.mp4 [--desde 0] [--dur 10] [--puntos 30000] [--invertir] [--matrix]
"""
import argparse, subprocess, numpy as np
from scipy.spatial import cKDTree

W, H, FPS = 1080, 1920, 24
K = 2                                           # el mapa de densidad se calcula a 1/K de resolución

def _crudo(path, desde, dur, vel, w, h):
    vf = f"setpts=PTS/{vel},fps={FPS},scale={w}:{h},format=gray"
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", str(desde), "-t", str(dur*vel), "-i", path, "-vf", vf,
                          "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(w*h)
        if len(b) < w*h: break
        yield np.frombuffer(b, np.uint8).reshape(h, w).astype(float)/255

def leer_siguiendo(path, desde, dur, vel):
    """Recorte vertical 9:16 que sigue al objeto brillante (centroide suavizado en el tiempo)."""
    from PIL import Image
    cs = []
    for g in _crudo(path, desde, dur, vel, 320, 180):
        m = np.clip(g - 0.08, 0, None); x = np.arange(320)
        cs.append((m.sum(0)*x).sum()/m.sum()/320 if m.sum() > 1 else (cs[-1] if cs else 0.5))
    cs = np.array(cs); k = np.exp(-np.linspace(-3, 3, 61)**2/2); k /= k.sum()
    cs = np.convolve(np.pad(cs, 30, mode="edge"), k, mode="valid")
    for i, g in enumerate(_crudo(path, desde, dur, vel, 1280, 720)):
        cw = 405; x0 = int(np.clip(cs[i]*1280 - cw/2, 0, 1280 - cw))
        yield np.asarray(Image.fromarray((g[:, x0:x0+cw]*255).astype(np.uint8)).resize((W//K, H//K), Image.BICUBIC), float)/255

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
    def step(self, d, iters, n=None):
        if n is not None and self.pts is not None and n != len(self.pts):
            if n > len(self.pts): self.pts = np.r_[self.pts, self.sample(d, n - len(self.pts))]
            else: self.pts = self.pts[:n]
            self.n = n
        if self.pts is None:
            if n: self.n = n
            self.pts = self.sample(d, self.n); iters = max(iters, 20)
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
    ap.add_argument("--seguir", action="store_true", help="recorte vertical que sigue al objeto brillante")
    ap.add_argument("--vel", type=float, default=1.0, help="velocidad de reproducción")
    ap.add_argument("--variable", type=float, default=0, help="puntos por unidad de luz (0 = cantidad fija)")
    ap.add_argument("--estrellas", type=int, default=0)
    ap.add_argument("--tono_min", type=float, default=0.55, help="brillo mínimo de un punto (1 = todos iguales)")
    a = ap.parse_args()
    rng = np.random.default_rng(1); MX = a.puntos; big = rng.uniform(size=MX) < 0.2; tw = rng.uniform(0, 6.28, MX)
    sx, sy = rng.uniform(0, W, a.estrellas), rng.uniform(0, H, a.estrellas); sb = rng.uniform(.15, .7, a.estrellas)**2; sp = rng.uniform(0, 6.28, a.estrellas)
    st = Stippler(a.puntos, H//K, W//K)
    out = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "15", a.salida], stdin=subprocess.PIPE)
    total = int(a.dur*FPS)
    fuente = leer_siguiendo(a.entrada, a.desde, a.dur, a.vel) if a.seguir else leer_frames(a.entrada, a.desde, a.dur, a.centro)
    nprev = None
    for f, g in enumerate(fuente):
        t = f/FPS; d = densidad(g, a); n = None
        if a.variable:
            n = int(np.clip(d.sum()*a.variable, 1500, MX)); n = n if nprev is None else int(nprev + 0.25*(n - nprev)); nprev = n
        pts, lum = st.step(d, a.iters, n); nn = len(pts)
        ln = np.clip(lum/max(np.percentile(lum, 97), 1e-3), 0, 1)
        w = (a.tono_min + (1 - a.tono_min)*ln**0.9)*(0.92 + 0.08*np.sin(t*3 + tw[:len(lum)]))*a.brillo
        sm = np.zeros((H, W)); bg = np.zeros((H, W))
        bb = big[:nn]; w = w[:nn] if len(w) > nn else w
        splat(sm, pts[~bb, 0], pts[~bb, 1], w[~bb]); splat(bg, pts[bb, 0], pts[bb, 1], w[bb])
        if a.estrellas: splat(sm, sx, sy, sb*(0.6 + 0.4*np.sin(t*1.5 + sp))*3)
        img = (sm + 2.2*blur(bg))*min(1, t/0.6, (a.dur - t)/0.6)
        out.stdin.write((np.clip(img, 0, 1)*255).astype(np.uint8).tobytes())
        if f % 24 == 0: print(f"{f}/{total}", flush=True)
    out.stdin.close(); out.wait()

if __name__ == "__main__": main()
