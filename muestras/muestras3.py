"""Muestrario 3: movimientos más complejos (cambio de escala, cámara que entra, puntos que se ordenan, reflejo).

    python3 muestras3.py salida_sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import muestras2 as M2
from muestras2 import M, EF, E, DW, GA, ss, Texto, splat, blur, sub, cuerpo, junta, W, H, FPS
import stipple

rng = np.random.default_rng(7)
def emparejar(A, B):
    """Ordena A y B por curva de Hilbert para que cada punto viaje a uno cercano (transformación limpia)."""
    n = min(len(A), len(B)); A = A[rng.choice(len(A), n, replace=False)]; B = B[rng.choice(len(B), n, replace=False)]
    return A[stipple.hilbert_order(A[:, :2])], B[stipple.hilbert_order(B[:, :2])]
def morph(A, B, k, abre=60.0):
    e = ss(0, 1, k); dis = np.random.default_rng(1).normal(0, 1, (len(A), 2))*abre*np.sin(np.pi*e)[..., None]
    return np.c_[A[:, 0]*(1 - e) + B[:, 0]*e + dis[:, 0], A[:, 1]*(1 - e) + B[:, 1]*e + dis[:, 1], A[:, 2]*(1 - e) + B[:, 2]*e]

# 1 ---------- cambio de escala: una gota se vuelve el océano de la Tierra vista desde el espacio ----------
G = M2.GOTA.copy(); G[:, :2] *= 2.6; G[:, 0] += 540; G[:, 1] += 960
G = np.r_[G, np.c_[rng.normal(540, 90, 4000), rng.normal(1000, 110, 4000), np.full(4000, 0.3)]]
G = G[((G[:, 0] - 540)/240)**2 + ((G[:, 1] - 980)/290)**2 < 1.4]
def tierra_oceanos(n=60000):
    lat, lon = M.esfera(n); x = np.cos(lat)*np.sin(lon); y = -np.sin(lat); z = -np.cos(lat)*np.cos(lon)
    tierra = (np.sin(3*lon + 1.3*np.sin(2*lat)) + 0.8*np.sin(5*lat + lon) + 0.5*np.cos(7*lon - 3*lat)) > 0.9
    vis = z < 0; b = np.where(tierra, 0.35, 1.0)
    keep = vis & (rng.uniform(size=n) < np.where(tierra, 0.25, 0.9))
    return np.c_[540 + 330*x[keep], 980 + 330*y[keep], b[keep]]
TIE = tierra_oceanos(); GA_, TA_ = emparejar(G, TIE)
ESTR = np.c_[rng.uniform(0, W, 300), rng.uniform(300, 1600, 300), rng.uniform(0.1, 0.6, 300)**2]
def e_escala(u):
    P = morph(GA_, TA_, ss(1.0, 3.0, u), 90); z = 1 - 0.35*ss(2.6, 4.6, u)
    P[:, 0] = 540 + (P[:, 0] - 540)*z; P[:, 1] = 980 + (P[:, 1] - 980)*z
    return junta(P, np.c_[ESTR[:, 0], ESTR[:, 1], ESTR[:, 2]*ss(2.4, 3.4, u)])

# 2 ---------- cámara que entra: viaje al centro de la Tierra ----------
CAPAS = [(1.00, 0.9, 9000, "CORTEZA"), (0.96, 0.32, 16000, "MANTO"), (0.55, 0.6, 9000, "NÚCLEO EXTERNO"), (0.19, 1.0, 5000, "NÚCLEO INTERNO")]
def capa(R, b, n, seed):
    r = np.random.default_rng(seed); a = r.uniform(0, 6.28, n); rr = R*np.sqrt(r.uniform(0.0 if R < 0.2 else 0.9, 1, n))
    return np.c_[rr*np.cos(a), rr*np.sin(a), np.full(n, b)]
ANILLOS = [capa(R, b, n, k) for k, (R, b, n, _) in enumerate(CAPAS)]
def zoom_entra(u): return 380*np.exp(np.log(12)*ss(0.8, 4.5, u))       # radio en pantalla de la Tierra
def e_entra(u):
    R = zoom_entra(u); partes = []
    for (Rc, b, n, _), P in zip(CAPAS, ANILLOS):
        r_pant = Rc*R; a = 1 - ss(700, 1500, r_pant)                          # las capas que ya pasamos se van
        partes.append(np.c_[540 + P[:, 0]*R, 960 + P[:, 1]*R, P[:, 2]*a*np.clip(R/380, 1, 4)**0.5])
    return junta(*partes)
def etiqueta_entra(sm, u):
    R = zoom_entra(u); vis = [n for (Rc, _, _, n) in CAPAS if Rc*R < 1500]
    actual = [n for (Rc, _, _, n) in CAPAS if Rc*R > 520]
    nombre = actual[-1] if actual else CAPAS[0][3]
    EF.contador(sm, nombre, E.TITULO_Y2 + 1000, ss(0.6, 1.0, u)*(1 - ss(4.6, 4.95, u)), splat, tam=50)

# 3 ---------- puntos que se ordenan: de imagen a datos ----------
RET = sub(DW.S_RETRATO, 9000, 4)
VAL = [1.0, 2.5, 3.0, 6.0, 8.0]; NOMB = ["1800", "1900", "1960", "2000", "HOY"]       # población mundial (miles de millones, aprox.)
def barras(n):
    pesos = np.array(VAL)/sum(VAL); cuenta = (pesos*n).astype(int); cuenta[-1] += n - cuenta.sum(); P = []
    for k, c in enumerate(cuenta):
        x0 = 170 + k*185; i = np.arange(c); cols = 14
        P.append(np.c_[x0 + (i % cols)*9 - 60, 1300 - (i//cols)*9, np.full(c, 0.9)])
    return np.concatenate(P)
BAR = barras(len(RET)); RO = RET[np.argsort(RET[:, 0])]                    # de izquierda a derecha: cada franja a su barra
def e_ordenar(u):
    return junta(morph(RO, BAR, ss(1.0, 2.8, u), 40))

# 4 ---------- reflejo en el agua: la Luna sobre el mar ----------
LX, LY, LB = M.globo(M2.LAT, M2.LON, M2.LUNA_B, 0.3, (540, 760), 230, inclina=0.0)
HORIZ = 1080
def e_reflejo(u):
    luna = np.c_[LX, LY, LB*2.4]
    ry = 2*HORIZ - LY; d = (ry - HORIZ)/400
    rx = LX + 14*np.sin(ry/22 - u*3.2)*(0.4 + d)                              # el reflejo ondula más lejos de la línea
    refl = np.c_[rx, ry*1.0 + 3*np.sin(rx/30 + u*2), LB*2.4*0.45*np.exp(-d*0.8)*(0.6 + 0.4*np.sin(ry/9 + u*6))]
    xs = rng.uniform(0, W, 0) if False else np.linspace(0, W, 400)
    olas = [np.c_[xs, np.full(400, HORIZ + k*42 + 4*np.sin(xs/40 + u*2 + k)), np.full(400, 0.18*np.exp(-k/6))] for k in range(10)]
    return junta(luna, refl, np.c_[np.linspace(0, W, 600), np.full(600, HORIZ), np.full(600, 0.5)], *olas)

ESCENAS = [("CAMBIO DE ESCALA", "DE UNA GOTA AL OCÉANO", e_escala, 5.0), ("CÁMARA QUE ENTRA", "VIAJE AL CENTRO DE LA TIERRA", e_entra, 5.0),
           ("PUNTOS QUE SE ORDENAN", "DE IMAGEN A DATOS", e_ordenar, 5.0), ("REFLEJO EN EL AGUA", "LA LUNA SOBRE EL MAR", e_reflejo, 5.0)]
INI = np.cumsum([0] + [e[3] for e in ESCENAS]); DUR = float(INI[-1])

def frame(t):
    k = min(int(np.searchsorted(INI, t, side="right") - 1), len(ESCENAS) - 1); u = t - INI[k]; seg = ESCENAS[k][3]
    x, y, w = ESCENAS[k][2](u)
    fase = np.random.default_rng(k).uniform(0, 6.28, len(x))
    x = x + 0.7*np.sin(t*1.3 + fase); y = y + 0.7*np.cos(t*1.1 + fase)
    w = w*ss(0, 0.35, u)*(1 - ss(seg - 0.35, seg, u))*1.8
    big = np.random.default_rng(k + 50).uniform(size=len(x)) < 0.2
    sm = np.zeros((H, W)); bg = np.zeros((H, W)); splat(sm, x[~big], y[~big], w[~big]); splat(bg, x[big], y[big], w[big])
    if ESCENAS[k][2] is e_entra: etiqueta_entra(sm, u)
    return (np.clip(sm + 2.2*blur(bg), 0, 1)*255).astype(np.uint8)

def textos():
    T = []
    for k, (a, b, _, seg) in enumerate(ESCENAS):
        t0 = INI[k]; T += [Texto(a, t0 + 0.2, t0 + seg - 0.6, y=230, tam=E.TAM_TITULO), Texto(b, t0 + 0.5, t0 + seg - 0.5, y=295, tam=E.TAM_ETIQUETA)]
    t0 = INI[2]
    T += [Texto(n, t0 + 2.6, t0 + 4.6, x=170 + k*185, y=1345, tam=30) for k, n in enumerate(NOMB)]
    T.append(Texto("POBLACIÓN MUNDIAL", t0 + 2.8, t0 + 4.6, y=1420, tam=40))
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
