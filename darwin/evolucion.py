"""Darwin y la evolución (puntillismo B/N, 1080x1920, transformación en el lugar).

Un mismo conjunto de puntos pasa por estados: retrato de Darwin -> la "marcha" (5 figuras en fila) ->
cladograma (las figuras en las puntas de ramas con un ancestro común) -> el árbol de la vida ("I think") ->
de nuevo el retrato.

    python3 evolucion.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(AQUI, "..", "video")); sys.path.insert(0, os.path.join(AQUI, "..", "tesla"))
import estilo as E
import stipple
import elementos as EL
from formacion import converger, textos_gancho
from pergamino import pergamino
from camara import acercar_toma, aplicar

W, H, FPS = 1080, 1920, 24
N = 30000
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))
rng = np.random.default_rng(4)

def a_n(P, n=N, seed=0):
    """Ajusta un conjunto de puntos a exactamente n (submuestreo o repetición con leve dispersión)."""
    r = np.random.default_rng(seed)
    if len(P) >= n: return P[r.choice(len(P), n, replace=False)]
    extra = P[r.choice(len(P), n - len(P))].copy(); extra[:, :2] += r.normal(0, 1.2, (len(extra), 2))
    return np.r_[P, extra]

def linea(p0, p1, paso=3.0, b=0.85, curva=0.0):
    """Rama: puntos a lo largo de un segmento (levemente curvo), con un poco de grosor."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); L = np.hypot(*(p1 - p0))
    s = np.linspace(0, 1, max(int(L/paso), 2))
    n_ = np.array([-(p1 - p0)[1], (p1 - p0)[0]])/max(L, 1e-6)
    pts = p0 + np.outer(s, p1 - p0) + np.outer(np.sin(np.pi*s)*curva, n_)
    pts = np.r_[pts, pts + rng.normal(0, 1.6, pts.shape)]
    return np.c_[pts, np.full(len(pts), b)]

# ---------- estado 0: retrato con su nombre (pergamino) ----------
PERG_Y = 1680; ROSTRO = (500.0, 770.0)
def retrato_con_nombre():
    R = EL.retrato(); R = R[R[:, 1] < PERG_Y - 70]
    P = pergamino("CHARLES DARWIN", seed=3); P[:, 0] += 540; P[:, 1] += PERG_Y
    S = np.r_[a_n(R, N - len(P), seed=1), P]
    return np.c_[S, np.r_[np.zeros(N - len(P)), np.ones(len(P))]]       # 4ª columna: 1 = pergamino (queda fijo)
S_RETRATO = retrato_con_nombre()

# ---------- estado 1: la marcha ----------
FIG = EL.figuras()
def colocar(fig, escala, x, pie_y):
    P = fig[0].copy(); P[:, 0] = x + P[:, 0]*escala; P[:, 1] = pie_y + P[:, 1]*escala; return P
alto_max = max(f[1] for f in FIG); cxs = np.array([f[2] for f in FIG])
xs_marcha = 120 + (cxs - cxs.min())/(cxs.max() - cxs.min())*840
S_MARCHA = a_n(np.concatenate([colocar(f, 760/alto_max, x, 1260) for f, x in zip(FIG, xs_marcha)]), seed=2)

# ---------- estado 2: cladograma (ancestro común) ----------
PUNTAS = [(160, 860), (350, 860), (540, 860), (730, 860), (920, 860)]
NODOS = [(540, 1500), (560, 1360), (640, 1240), (720, 1120), (800, 1000)]     # raíz y bifurcaciones
def cladograma():
    ramas = [linea(NODOS[0], NODOS[1], b=0.9)]
    for k in range(4):                                         # cada nodo: una rama a una punta y otra al siguiente nodo
        ramas.append(linea(NODOS[k + 1], PUNTAS[k], curva=-18))
        if k < 3: ramas.append(linea(NODOS[k + 1], NODOS[k + 2]))
    ramas.append(linea(NODOS[4], PUNTAS[4], curva=18))
    R = np.concatenate(ramas)
    figs = [colocar(f, 300/alto_max, x, y - 8) for f, (x, y) in zip(FIG, PUNTAS)]
    raiz = np.c_[NODOS[0][0] + rng.normal(0, 5, 300), NODOS[0][1] + rng.normal(0, 5, 300), np.full(300, 1.0)]
    nf = N - len(R) - len(raiz)
    F = a_n(np.concatenate(figs), nf, seed=3)
    # orden de llegada: ramas desde la raíz hacia arriba, después las figuras
    dR = np.clip((NODOS[0][1] - R[:, 1])/700, 0, 1)*0.75
    return np.r_[raiz, R, F], np.r_[np.zeros(len(raiz)), dR, 0.8 + rng.uniform(0, 0.2, nf)]
S_CLADO, D_CLADO = cladograma()

# ---------- estado 3: el árbol de la vida ("I think") ----------
def arbol():
    segs = []
    def rama(p, ang, largo, prof):
        q = (p[0] + np.sin(ang)*largo, p[1] - np.cos(ang)*largo)
        segs.append((p, q, prof))
        if prof < 7:
            for d in (-1, 1):
                rama(q, ang + d*rng.uniform(0.28, 0.6), largo*rng.uniform(0.66, 0.8), prof + 1)
    rama((540, 1560), 0.0, 260, 0)
    partes, orden = [], []
    for p, q, prof in segs:
        L = linea(p, q, paso=2.6 + 0.4*prof, b=max(0.95 - 0.08*prof, 0.4), curva=rng.normal(0, 6))
        partes.append(L); orden.append(np.full(len(L), prof/8))
        if prof == 7:                                        # especies: un punto brillante en cada punta
            partes.append(np.c_[q[0] + rng.normal(0, 3, 30), q[1] + rng.normal(0, 3, 30), np.ones(30)]); orden.append(np.full(30, 1.0))
    P = np.concatenate(partes); O = np.concatenate(orden)
    idx = rng.choice(len(P), N, replace=len(P) < N)
    return P[idx], O[idx]
S_ARBOL, D_ARBOL = arbol()

# ---------- emparejar puntos entre estados (Hilbert: vecinos con vecinos) ----------
def ordenar(S, D=None):
    o = stipple.hilbert_order(S[:, :2]); return S[o], (D[o] if D is not None else rng.uniform(0, 1, N)**1.2)
ESTADOS = [ordenar(S_RETRATO), ordenar(S_MARCHA), ordenar(S_CLADO, D_CLADO), ordenar(S_ARBOL, D_ARBOL), ordenar(S_RETRATO)]

# guion: (t inicio de la transición, duración) hacia el estado k
TRANS = [(4.6, 2.2), (9.8, 3.2), (16.4, 3.0), (21.6, 2.2)]
DUR = 27.4
TOMAS = {0: (E.GANCHO_INICIO + 1.0, TRANS[0][0] + 0.6), 4: (TRANS[3][0] + 0.6, DUR - 0.4)}   # tomas del retrato (se acerca)
def vista(k, S, t):
    """Estado k en el instante t: en las tomas del retrato la cámara se acerca al rostro; el pergamino queda fijo."""
    if k not in TOMAS: return S
    z = acercar_toma(t, *TOMAS[k], ROSTRO, (540, 820)); S = S.copy(); m = S[:, 3] < 0.5
    S[m, 0], S[m, 1] = aplicar(S[m, 0], S[m, 1], *z); S[m, 2] *= z[0]**0.9
    S[m, 2] *= 1 - ss(PERG_Y - 120, PERG_Y - 60, S[m, 1])                 # pasa por detrás de la cinta
    return S
fase = rng.uniform(0, 6.28, N); dis = rng.normal(0, 1, (N, 2))*[90, 60]

def posiciones(t):
    P = vista(0, ESTADOS[0][0], t)
    x, y, b = P[:, 0].copy(), P[:, 1].copy(), P[:, 2].copy()
    x, y, b = converger(x, y, b, t, seed=7)
    for k, (t0, d) in enumerate(TRANS):
        if t <= t0: break
        Q, Dq = ESTADOS[k + 1]; Q = vista(k + 1, Q, t)
        e = ss(0, 1, (t - t0 - Dq*d*0.55)/(d*0.45))
        rem = np.sin(np.pi*e)[:, None]*dis                     # en el camino, los puntos se abren un poco
        x = x*(1 - e) + Q[:, 0]*e + rem[:, 0]; y = y*(1 - e) + Q[:, 1]*e + rem[:, 1]; b = b*(1 - e) + Q[:, 2]*e
    resp = 0.8*np.sin(t*1.3 + fase)
    return x + resp, y + 0.8*np.cos(t*1.1 + fase), b

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)
def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

big = rng.uniform(size=N) < 0.2
def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W))
    x, y, b = posiciones(t)
    w = b*(0.9 + 0.1*np.sin(t*4 + fase))*1.9
    splat(sm, x[~big], y[~big], w[~big]); splat(bg, x[big], y[big], w[big])
    img = (sm + 2.2*blur(bg))*min(1, (DUR - t)/E.FUNDIDO_FINAL)
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

def textos():
    from textos import Texto
    T = textos_gancho("LA IDEA QUE", "CAMBIÓ LA BIOLOGÍA")
    T += [Texto("¿ASÍ EVOLUCIONAMOS?", 6.4, 9.6, y=330, tam=E.TAM_TITULO),
          Texto("NO VENIMOS DEL MONO", 11.6, 16.0, y=330, tam=E.TAM_TITULO),
          Texto("COMPARTIMOS UN ANCESTRO", 12.3, 16.2, y=395, tam=E.TAM_TITULO),
          Texto("ANCESTRO COMÚN", 12.6, 16.0, y=1570, tam=E.TAM_ETIQUETA, brillo=0.7),
          Texto("LA VIDA ES UN ÁRBOL", 18.4, 21.4, y=230, tam=E.TAM_TITULO),
          Texto("TODOS SOMOS", 22.4, DUR - 1.3, y=230, tam=E.TAM_CIERRE),
          Texto("UNA MISMA FAMILIA", 23.0, DUR - 1.2, y=290, tam=E.TAM_CIERRE)]
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
