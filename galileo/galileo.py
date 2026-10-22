"""Galileo (puntillismo B/N, 1080x1920). Plantilla de estados (como Darwin) con estados ANIMADOS (órbitas).

Geocéntrico (mito, gancho) -> estatua de Galileo -> Júpiter y sus 4 lunas -> heliocéntrico -> estatua.
Fuentes: estatua (Uffizi, foto aportada por el usuario, recorte GrabCut), Sol (NASA SDO), Júpiter (NASA Cassini).

    python3 galileo.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
from PIL import Image
from scipy import ndimage
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "video")); sys.path.insert(0, os.path.join(AQUI, "..", "tesla"))
import estilo as E
import stipple
from formacion import converger, textos_gancho

W, H, FPS = 1080, 1920, 24
N = 30000; CX, CY = 540.0, 960.0
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))
rng = np.random.default_rng(9)

def cache(nombre, fn):
    p = os.path.join(AQUI, f"cache_{nombre}.npy")
    if os.path.exists(p): return np.load(p)
    v = fn(); np.save(p, v); return v

# ---------- elementos (Voronoi, centrados en 0,0) ----------
def disco_imagen(archivo, n, seed, gamma=1.3, umbral=0.06):
    """Puntos de un cuerpo redondo a partir de una foto (radio normalizado a 1)."""
    g = np.asarray(Image.open(os.path.join(AQUI, "src", archivo)).convert("L"), float)/255
    m = ndimage.binary_fill_holes(ndimage.gaussian_filter(g, 3) > umbral)
    lab, k = ndimage.label(m); m = lab == (np.argmax(ndimage.sum(m, lab, range(1, k+1))) + 1)
    ys, xs = np.nonzero(m); cy, cx = ys.mean(), xs.mean(); r = max(xs.max() - cx, cx - xs.min(), ys.max() - cy, cy - ys.min())
    r = int(r) + 4; gm = np.pad(g*m, r)                               # margen: el recorte nunca sale de la imagen
    cy, cx = int(cy) + r, int(cx) + r
    G = Image.fromarray((gm[cy - r:cy + r, cx - r:cx + r]*255).astype(np.uint8)).resize((400, 400), Image.LANCZOS)
    G = np.asarray(G, float)/255
    gy, gx = np.gradient(ndimage.gaussian_filter(G, 1)); edge = np.clip(np.hypot(gx, gy)*6, 0, 1)
    d = np.clip(G/np.percentile(G[G > 0.02], 99), 0, 1)**gamma + 0.3*edge + 1e-6*(G > 0.01)
    p, _ = stipple.voronoi(d, n, 30, seed)
    b = G[np.clip(p[:, 1].astype(int), 0, 399), np.clip(p[:, 0].astype(int), 0, 399)]
    return np.c_[(p - 200)/200, np.clip(0.3 + 0.9*b/np.percentile(b, 95), 0, 1)]

SOL = cache("sol", lambda: disco_imagen("sol_sdo.jpg", 12000, 1, gamma=1.0))
def jupiter_dibujado(n=21000):
    """Júpiter completo: bandas, Gran Mancha Roja y oscurecimiento del borde (dibujado, radio 1)."""
    yy, xx = (np.mgrid[0:400, 0:400] + 0.5)/200 - 1; rr = np.hypot(xx, yy); m = rr < 1
    bandas = 0.62 + 0.25*np.sin(yy*17 + 0.6*np.sin(xx*3)) + 0.1*np.sin(yy*41 + xx*2)
    mancha = np.exp(-(((xx + 0.25)/0.2)**2 + ((yy - 0.38)/0.1)**2))
    G = m*np.clip(bandas - 0.35*mancha + 0.25*np.exp(-(((xx + 0.25)/0.27)**2 + ((yy - 0.38)/0.14)**2))*(1 - mancha), 0, 1)
    G *= np.sqrt(np.clip(1 - rr**2, 0, 1))**0.5
    d = G**1.3 + 0.5*(np.abs(rr - 0.985) < 0.015) + 1e-6*m
    p, _ = stipple.voronoi(d, n, 30, 2)
    b = G[np.clip(p[:, 1].astype(int), 0, 399), np.clip(p[:, 0].astype(int), 0, 399)]
    return np.c_[(p - 200)/200, np.clip(0.35 + 0.8*b, 0, 1)]
JUP = cache("jupiter", jupiter_dibujado)

def estatua(n=24000):
    g = np.asarray(Image.open(os.path.join(AQUI, "src", "estatua.jpg")).convert("L"), float)/255
    m = np.load(os.path.join(AQUI, "mask_estatua.npy"))
    ys, xs = np.nonzero(m); sub = slice(ys.min(), ys.max()), slice(xs.min(), xs.max())
    G = g[sub]*m[sub]; M = m[sub]
    G = np.asarray(Image.fromarray((G*255).astype(np.uint8)).resize((G.shape[1]//2, G.shape[0]//2), Image.LANCZOS), float)/255
    M = np.asarray(Image.fromarray((M*255).astype(np.uint8)).resize((G.shape[1], G.shape[0])), float)/255 > 0.5
    gy, gx = np.gradient(ndimage.gaussian_filter(G, 1)); edge = np.clip(np.hypot(gx, gy)*6, 0, 1)
    d = M*(np.clip((G - 0.2)/0.7, 0, 1)**1.3 + 0.5*edge) + 1e-6*M
    p, _ = stipple.voronoi(d, n, 30, 3)
    b = G[np.clip(p[:, 1].astype(int), 0, G.shape[0]-1), np.clip(p[:, 0].astype(int), 0, G.shape[1]-1)]
    esc = 1320/G.shape[0]
    return np.c_[(p[:, 0] - G.shape[1]/2)*esc, (p[:, 1] - G.shape[0]/2)*esc, np.clip(0.25 + 0.9*b, 0, 1)]
ESTATUA = cache("estatua", estatua)

def disco_liso(n, seed, borde=0.35):
    """Cuerpo simple (planeta/luna): relleno + borde marcado."""
    r = np.random.default_rng(seed); a = r.uniform(0, 2*np.pi, n); rr = np.sqrt(r.uniform(0, 1, n))
    rr = np.where(r.uniform(size=n) < borde, 0.97 + r.normal(0, 0.02, n), rr)
    luz = np.clip(0.45 + 0.55*np.cos(a - 2.4)*rr, 0.25, 1)               # iluminado de un lado
    return np.c_[rr*np.cos(a), rr*np.sin(a), luz]

def anillo(n, R, achata=1.0, b=0.3):
    a = np.linspace(0, 2*np.pi, n, endpoint=False) + rng.uniform(0, 0.01, n)
    return np.c_[R*np.cos(a), R*achata*np.sin(a), np.full(n, b)]

# ---------- estados: listas de cuerpos (puntos locales, escala, órbita) ----------
class Cuerpo:
    def __init__(self, P, escala, R=0.0, periodo=1.0, fase=0.0, achata=1.0, centro=(CX, CY), oculto_por=None, brillo=1.0):
        self.P, self.esc, self.R, self.per, self.fase, self.ach = P, escala, R, periodo, fase, achata
        self.centro, self.oculto_por, self.brillo = centro, oculto_por, brillo
    def pos(self, t):
        a = self.fase + 2*np.pi*t/self.per
        cx = self.centro[0] + self.R*np.cos(a); cy = self.centro[1] + self.R*self.ach*np.sin(a)
        x = cx + self.P[:, 0]*self.esc; y = cy + self.P[:, 1]*self.esc; b = self.P[:, 2]*self.brillo
        if self.oculto_por is not None and np.sin(a) < 0 and abs(cx - self.centro[0]) < self.oculto_por:
            b = b*0.0                                                    # pasa detrás del planeta
        return np.c_[x, y, b], (cx, cy)

def estado(cuerpos):
    tam = sum(len(c.P) for c in cuerpos)
    def pos(t):
        Q = np.concatenate([c.pos(t)[0] for c in cuerpos])
        if len(Q) >= N: return Q[:N]
        return np.r_[Q, Q[rng.integers(0, len(Q), N - len(Q))]]
    return pos, tam

TIERRA_P = disco_liso(2600, 11, 0.3)
GEO = estado([Cuerpo(TIERRA_P, 70),                                                       # la Tierra en el centro
              Cuerpo(anillo(1600, 400, b=0.25), 1, ), Cuerpo(anillo(1100, 240, b=0.2), 1),
              Cuerpo(SOL, 95, R=400, periodo=7.0, fase=-0.6),                            # el Sol gira alrededor
              Cuerpo(disco_liso(900, 12), 22, R=240, periodo=4.2, fase=2.0)])           # un planeta
HELIO_T = Cuerpo(TIERRA_P, 34, R=330, periodo=8.0, fase=0.8, brillo=1.25)
HELIO = estado([Cuerpo(SOL, 150),
                Cuerpo(anillo(900, 230, b=0.22), 1), Cuerpo(anillo(1300, 330, b=0.28), 1), Cuerpo(anillo(1500, 450, b=0.22), 1),
                Cuerpo(disco_liso(700, 13), 16, R=230, periodo=4.6, fase=2.6),
                HELIO_T,
                Cuerpo(disco_liso(800, 14), 24, R=450, periodo=13.0, fase=4.2)])
LUNAS = [Cuerpo(disco_liso(420, 20 + k), 13, R=R, periodo=p, fase=f, achata=0.12, oculto_por=210)
         for k, (R, p, f) in enumerate(((270, 2.4, 0.3), (335, 4.8, 2.2), (410, 9.6, 4.0), (490, 16.0, 5.3)))]
JUPITER = estado([Cuerpo(JUP, 210)] + LUNAS)
EST = estado([Cuerpo(ESTATUA, 1.0, centro=(CX, 1010), brillo=1.45)])

# guion: (estado, t llega, duración transición)
ESTADOS = [GEO[0], EST[0], JUPITER[0], HELIO[0], EST[0]]
TRANS = [(5.0, 2.2), (10.4, 2.2), (16.4, 2.4), (23.0, 2.2)]
DUR = 28.6

# emparejamiento por Hilbert (al momento en que cada estado aparece)
T_REF = [0.0] + [t0 + d for t0, d in TRANS]
ORDEN = [stipple.hilbert_order(ESTADOS[k](T_REF[k])[:, :2]) for k in range(len(ESTADOS))]
DEM = rng.uniform(0, 1, N)**1.2; fase = rng.uniform(0, 6.28, N); dis = rng.normal(0, 1, (N, 2))*[80, 60]

def posiciones(t):
    Q = ESTADOS[0](t)[ORDEN[0]]; x, y, b = Q[:, 0].copy(), Q[:, 1].copy(), Q[:, 2].copy()
    x, y, b = converger(x, y, b, t, seed=5)
    for k, (t0, d) in enumerate(TRANS):
        if t <= t0: break
        Q = ESTADOS[k + 1](t)[ORDEN[k + 1]]
        e = ss(0, 1, (t - t0 - DEM*d*0.5)/(d*0.5)); rem = np.sin(np.pi*e)[:, None]*dis
        x = x*(1 - e) + Q[:, 0]*e + rem[:, 0]; y = y*(1 - e) + Q[:, 1]*e + rem[:, 1]; b = b*(1 - e) + Q[:, 2]*e
    return x + 0.7*np.sin(t*1.3 + fase), y + 0.7*np.cos(t*1.1 + fase), b

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)
def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

big = rng.uniform(size=N) < 0.2
st_x, st_y, st_b, st_p = rng.uniform(0, W, 220), rng.uniform(0, H, 220), rng.uniform(.1, .5, 220)**2, rng.uniform(0, 6.28, 220)
def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W))
    x, y, b = posiciones(t); w = b*(0.92 + 0.08*np.sin(t*4 + fase))*1.9
    splat(sm, x[~big], y[~big], w[~big]); splat(bg, x[big], y[big], w[big])
    cielo = 1 - ss(5.0, 6.0, t) + ss(10.4, 11.4, t) - ss(23.0, 24.0, t)   # estrellas en las escenas del cielo
    splat(sm, st_x, st_y, st_b*(0.6 + 0.4*np.sin(t*1.5 + st_p))*3*np.clip(cielo, 0, 1)*ss(0, 2, t))
    img = (sm + 2.2*blur(bg))*min(1, (DUR - t)/E.FUNDIDO_FINAL)
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

def pista_tierra():
    """Posición en pantalla de la Tierra en el modelo heliocéntrico (para su etiqueta)."""
    return [HELIO_T.pos(f/FPS)[1] if TRANS[2][0] + 1.5 < f/FPS < TRANS[3][0] else None for f in range(int(DUR*FPS))]

def textos():
    from textos import Texto
    T = textos_gancho("¿EL SOL GIRA", "ALREDEDOR DE LA TIERRA?")
    T += [Texto("EN 1610 APUNTÓ", 6.0, 10.2, y=150, tam=E.TAM_TITULO),
          Texto("UN TELESCOPIO AL CIELO", 6.6, 10.3, y=215, tam=E.TAM_TITULO),
          Texto("GALILEO GALILEI", 6.4, 10.1, y=1790, tam=E.TAM_ETIQUETA, brillo=0.7),
          Texto("Y VIO LUNAS", 11.6, 16.2, y=230, tam=E.TAM_TITULO),
          Texto("GIRANDO ALREDEDOR DE JÚPITER", 12.2, 16.3, y=295, tam=E.TAM_TITULO),
          Texto("LA TIERRA GIRA", 17.8, 22.8, y=230, tam=E.TAM_TITULO),
          Texto("ALREDEDOR DEL SOL", 18.4, 22.9, y=295, tam=E.TAM_TITULO),
          Texto("TIERRA", 18.2, 22.6, tam=26, seguir=True, dx=0, dy=-62, brillo=0.8, pista=pista_tierra()),
          Texto("MIRÓ AL CIELO", 23.8, DUR - 1.3, y=150, tam=E.TAM_CIERRE),
          Texto("Y NOS CAMBIÓ DE LUGAR", 24.4, DUR - 1.2, y=210, tam=E.TAM_CIERRE)]
    return T

def fb(f): return frame(f/FPS).tobytes()
if __name__ == "__main__":
    from multiprocessing import Pool
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 and int(sys.argv[2]) > 0 else int(DUR*FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "15", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(fb, range(n), chunksize=2): p.stdin.write(b)
    p.stdin.close(); p.wait()
    if len(sys.argv) > 3:
        from textos import componer
        componer(out, sys.argv[3], textos())
