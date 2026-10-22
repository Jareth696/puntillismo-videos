"""Muestrario de movimientos, segunda tanda: túnel del tiempo con escrituras y 6 movimientos nuevos.

    python3 muestras2.py salida_sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
from PIL import Image
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.join(AQUI, "..")
for d in ("video", "tesla", "darwin", "galileo"): sys.path.insert(0, os.path.join(RAIZ, d))
import estilo as E
import movimientos as M
import efectos as EF
import evolucion as DW
import galileo as GA
from movimientos import ss
from textos import Texto, puntos_de_texto
from muestras import splat, blur, sub, cuerpo, junta, W, H, FPS

rng = np.random.default_rng(5)
def pts(P, w=1.0): P = np.asarray(P, float); return np.c_[P[:, 0], P[:, 1], np.full(len(P), w)]
def linea(p0, p1, paso=2.5):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); n = max(int(np.hypot(*(p1 - p0))/paso), 2)
    return p0 + np.outer(np.linspace(0, 1, n), p1 - p0)

# ---------- glifos dibujados con código (sin imágenes) ----------
def maya(v):
    """Número maya: rayas (5) y puntos (1)."""
    P = []
    for b in range(v//5):
        y = 18 - b*16
        for yy in (y - 4, y + 4): P.append(linea((-30, yy), (30, yy)))
    for d in range(v % 5):
        a = np.linspace(0, 6.28, 24); x0 = (d - (v % 5 - 1)/2)*16; y0 = 18 - (v//5)*16 - 4
        P.append(np.c_[x0 + 5*np.cos(a), y0 + 5*np.sin(a)])
    return np.concatenate(P)
def cuneiforme(seed):
    """Un signo cuneiforme: 2 a 4 cuñas (cabeza triangular + cola)."""
    r = np.random.default_rng(seed); P = []
    for _ in range(r.integers(2, 5)):
        a = r.choice([0, np.pi/2, np.pi/4]); L = r.uniform(25, 45); o = r.uniform(-18, 18, 2)
        d = np.array([np.cos(a), np.sin(a)]); n = np.array([-d[1], d[0]])
        h = o; P += [linea(h - n*7, h + n*7), linea(h - n*7, h + d*12), linea(h + n*7, h + d*12), linea(h + d*12, h + d*L)]
    return np.concatenate(P)
def huella():
    """Huella de dinosaurio de tres dedos."""
    P = [linea((0, 10), (0, -40)), linea((0, 10), (-24, -32)), linea((0, 10), (24, -32))]
    a = np.linspace(0, 6.28, 30); P.append(np.c_[12*np.cos(a), 18 + 10*np.sin(a)]); return np.concatenate(P)
def sim(txt, tam=48, seed=0): return EF.simbolo(txt, tam=tam, seed=seed)

ERAS = [("HOY", [sim(s, seed=k) for k, s in enumerate(["0101", "1010", "∞", "0110", "10", "π", "0011", "1"])]),
        ("1905", [sim(s, seed=k) for k, s in enumerate(["E=mc²", "c", "λ", "ħ", "E=mc²", "Δt", "v", "c²"])]),
        ("1687", [sim(s, seed=k) for k, s in enumerate(["F=ma", "G", "m₁m₂", "r²", "F=ma", "g", "∫", "dx"])]),
        ("300 a. C.", [sim(s, seed=k) for k, s in enumerate(["a²+b²=c²", "π", "α", "β", "γ", "Δ", "Ω", "θ"])]),
        ("500 a. C.", [maya(v) for v in (1, 4, 7, 9, 12, 13, 17, 19)]),
        ("3000 a. C.", [cuneiforme(k) for k in range(8)]),
        ("HACE 66 MILLONES DE AÑOS", [huella() for _ in range(8)]),
        ("HACE 4.000 MILLONES DE AÑOS", [])]
ANIOS = [puntos_de_texto(Texto(a, 0, 1, tam=70), seed=k) for k, (a, _) in enumerate(ERAS)]
def gota(R=90, n=900):
    a = np.linspace(0, 6.28, 220, endpoint=False); s = np.sin(a)
    cx, cy = np.cos(a)*(1 - 0.55*np.maximum(0, -s)**3), s*(1 + 0.8*np.maximum(0, -s)**1.4)
    a2 = rng.uniform(0, 6.28, n); r2 = np.sqrt(rng.uniform(0, 1, n))*0.9; s2 = np.sin(a2)
    fx, fy = np.cos(a2)*(1 - 0.55*np.maximum(0, -s2)**3)*r2, s2*(1 + 0.8*np.maximum(0, -s2)**1.4)*r2
    return np.r_[np.c_[cx*R, cy*R, np.full(220, 1.0)], np.c_[fx*R, fy*R, np.full(n, 0.35)]]
GOTA = gota()

SEP = 1150.0
def e_tunel_tiempo(u):
    """Túnel hacia atrás en el tiempo: cada plano es una época con sus escrituras; la gota viaja en el centro."""
    cz = -700 + SEP*len(ERAS)*0.95*ss(0.3, 7.6, u)**1.15; partes = []
    for k, (_, glifos) in enumerate(ERAS):
        Zr = k*SEP - cz
        if Zr < -1300 or Zr > 2700: continue                               # solo la época que viene y la que pasa
        f = M.D/max(M.D + Zr, 60); a = ss(2700, 1700, Zr)*(1 - ss(-700, -1300, Zr))
        for j, G in enumerate(glifos):
            ang = j*2*np.pi/len(glifos) + k*0.4 + u*0.25*(-1)**k; R = 420
            partes.append(np.c_[(G[:, 0] + R*np.cos(ang))*f + 540, (G[:, 1] + R*np.sin(ang)*1.15)*f + 960, np.full(len(G), 0.9*a)])
        T = ANIOS[k]; partes.append(np.c_[T[:, 0]*f + 540, (T[:, 1] + 640)*f + 960, np.full(len(T), 1.2*a)])
    brillo = 1 + 0.8*ss(6.8, 7.8, u)                                      # al llegar al origen la gota brilla
    partes.append(np.c_[GOTA[:, 0] + 540, GOTA[:, 1] + 960 + 6*np.sin(u*3), GOTA[:, 2]*brillo])
    return junta(*partes)

# ---------- globo que gira: la Luna en 3D con su textura real ----------
_g = np.asarray(Image.open(os.path.join(RAIZ, "luna", "src", "luna_llena_nasa.jpg")).convert("L"), float)/255
_ys, _xs = np.nonzero(_g > 0.08); _cx, _cy = (_xs.min() + _xs.max())/2, (_ys.min() + _ys.max())/2; _r = (_xs.max() - _xs.min())/2
LAT, LON = M.esfera(160000)
_lf = np.where(np.cos(LON) >= 0, LON, np.pi - LON)                        # la cara de atrás: espejo de la de adelante
_u = _cx + _r*np.cos(LAT)*np.sin(_lf)*0.98; _v = _cy - _r*np.sin(LAT)*0.98
from scipy import ndimage
_gs = ndimage.gaussian_filter(_g, 6)                                    # sin el ruido fino de los cráteres
_t = _gs[np.clip(_v.astype(int), 0, _g.shape[0] - 1), np.clip(_u.astype(int), 0, _g.shape[1] - 1)]
_p5, _p95 = np.percentile(_t[_t > 0.1], [5, 95])
LUNA_B = np.clip((_t - _p5)/(_p95 - _p5), 0, 1)                        # contraste: mares oscuros, tierras altas claras
_k = np.random.default_rng(1).uniform(size=len(LUNA_B)) < 0.03 + 0.42*LUNA_B**2   # puntillismo: densidad según el brillo
LAT, LON, LUNA_B = LAT[_k], LON[_k], 0.5 + 0.5*LUNA_B[_k]
def e_globo(u):
    x, y, w = M.globo(LAT, LON, LUNA_B, u*0.55, (540, 960), 380, inclina=0.2 + 0.1*np.sin(u*0.7)); return x, y, w*3.0

# ---------- lupa: el detalle de un retrato ----------
RET = DW.S_RETRATO[:, :3]
def e_lupa(u):
    k = ss(0.6, 4.4, u); c = (np.interp(k, [0, 0.5, 1], [330, 470, 560]), np.interp(k, [0, 0.5, 1], [900, 720, 840]))
    x, y, w = M.lupa(RET, c, 170*ss(0.3, 0.9, u) + 1, 2.3)
    return x, y, w

# ---------- puntos que cuentan: la Tierra en 4.500 puntos ----------
def e_contar(u):
    k = ss(0.5, 3.0, u)**1.3
    x, y, w, i = M.grilla_contadora(4500, 60, 540, 1000, 11, k)
    p = ss(3.2, 3.6, u); a = np.linspace(0, 6.28, 60)
    halo = np.c_[x[-1] + (14 + 30*(1 - p))*np.cos(a), y[-1] + (14 + 30*(1 - p))*np.sin(a), np.full(60, 1.2*p)]
    w = w.copy(); w[-1] = 0.9 + 2.5*p
    return junta((x, y, w), halo)
def contador_contar(sm, u):
    k = ss(0.5, 3.0, u)**1.3
    EF.contador(sm, f"{EF.miles(int(k*4500))} MILLONES DE AÑOS", 525, ss(0.3, 0.6, u)*(1 - ss(4.5, 4.9, u)), splat, tam=44)

# ---------- desintegración: lo que el tiempo se lleva ----------
EST = cuerpo(GA.ESTATUA, 0.82, 540, 1010)
def e_desintegrar(u):
    k = ss(0.8, 2.6, u)*(1 - ss(3.0, 4.6, u))
    return M.desintegrar(EST, k, 200, 900)

# ---------- línea que se dibuja: la constelación de Orión ----------
ESTR = {"Meissa": (545, 560), "Betelgeuse": (380, 660), "Bellatrix": (705, 700), "Mintaka": (612, 960), "Alnilam": (548, 990),
        "Alnitak": (485, 1022), "Saiph": (700, 1360), "Rigel": (360, 1310)}
TRAZO = [("Meissa", "Betelgeuse"), ("Meissa", "Bellatrix"), ("Betelgeuse", "Alnitak"), ("Bellatrix", "Mintaka"),
         ("Mintaka", "Alnilam"), ("Alnilam", "Alnitak"), ("Alnitak", "Saiph"), ("Mintaka", "Rigel")]
FONDO = np.c_[rng.uniform(0, W, 400), rng.uniform(400, 1550, 400), rng.uniform(0.1, 0.5, 400)**2]
def e_orion(u):
    partes = [np.c_[FONDO[:, 0], FONDO[:, 1], FONDO[:, 2]*ss(0.0, 0.6, u)]]
    for j, (n, (x, y)) in enumerate(ESTR.items()):
        g = ss(0.3 + j*0.08, 0.6 + j*0.08, u); a = rng.uniform(0, 6.28, 60); r = np.sqrt(rng.uniform(0, 1, 60))*(9 if n in ("Betelgeuse", "Rigel") else 6)
        partes.append(np.c_[x + r*np.cos(a), y + r*np.sin(a), np.full(60, 1.0*g)])
    for j, (a_, b_) in enumerate(TRAZO):
        k = ss(1.2 + j*0.35, 1.55 + j*0.35, u)
        if k > 0: partes.append(np.c_[M.trazar([ESTR[a_], ESTR[b_]], k, b=0.55)])
    return junta(*partes)

# ---------- onda expansiva: un impacto que viaja ----------
def e_onda(u):
    T0 = 1.3; x, y, w = M.superficie_onda(u, T0)
    partes = [(x, y, w)]
    if u < T0:                                                        # la gota cae
        sx, sy, f = M.ver_tela(np.array([0.0]), np.array([0.0]), np.array([0.0]))
        yy = sy[0] - 700*(1 - (u/T0)**2)
        partes.append(np.c_[GOTA[:, 0]*0.5 + sx[0], GOTA[:, 1]*0.5 + yy - 45, GOTA[:, 2]])
    return junta(*partes)

ESCENAS = [("TÚNEL DEL TIEMPO", "ESCRITURAS DE CADA ÉPOCA", e_tunel_tiempo, 8.0), ("GLOBO QUE GIRA", "LA LUNA EN 3D", e_globo, 5.0),
           ("LUPA", "EL DETALLE QUE NO SE VE", e_lupa, 5.0), ("PUNTOS QUE CUENTAN", "1 PUNTO = 1 MILLÓN DE AÑOS", e_contar, 5.0),
           ("DESINTEGRACIÓN", "LO QUE EL TIEMPO SE LLEVA", e_desintegrar, 5.0), ("LÍNEA QUE SE DIBUJA", "LA CONSTELACIÓN DE ORIÓN", e_orion, 5.0),
           ("ONDA EXPANSIVA", "UN IMPACTO QUE VIAJA", e_onda, 5.0)]
INI = np.cumsum([0] + [e[3] for e in ESCENAS]); DUR = float(INI[-1])

def frame(t):
    k = min(int(np.searchsorted(INI, t, side="right") - 1), len(ESCENAS) - 1); u = t - INI[k]; seg = ESCENAS[k][3]
    x, y, w = ESCENAS[k][2](u)
    fase = np.random.default_rng(k).uniform(0, 6.28, len(x))
    x = x + 0.7*np.sin(t*1.3 + fase); y = y + 0.7*np.cos(t*1.1 + fase)
    w = w*ss(0, 0.35, u)*(1 - ss(seg - 0.35, seg, u))*1.8
    big = np.random.default_rng(k + 50).uniform(size=len(x)) < 0.2
    sm = np.zeros((H, W)); bg = np.zeros((H, W)); splat(sm, x[~big], y[~big], w[~big]); splat(bg, x[big], y[big], w[big])
    if ESCENAS[k][2] is e_contar: contador_contar(sm, u)
    return (np.clip(sm + 2.2*blur(bg), 0, 1)*255).astype(np.uint8)

def textos():
    T = []
    for k, (a, b, _, seg) in enumerate(ESCENAS):
        t0 = INI[k]; T += [Texto(a, t0 + 0.2, t0 + seg - 0.6, y=230, tam=E.TAM_TITULO), Texto(b, t0 + 0.5, t0 + seg - 0.5, y=295, tam=E.TAM_ETIQUETA)]
    t0 = INI[3]; T.append(Texto("LOS HUMANOS: MENOS DE UN PUNTO", t0 + 3.4, t0 + 4.7, y=1460, tam=40))
    return T

def fb(f): return frame(f/FPS).tobytes()
if __name__ == "__main__":
    from multiprocessing import Pool
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 and int(sys.argv[2]) > 0 else int(DUR*FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(fb, range(n), chunksize=2): p.stdin.write(b)
    p.stdin.close(); p.wait()
    if len(sys.argv) > 3:
        from textos import componer
        componer(out, sys.argv[3], textos())
