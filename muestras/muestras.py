"""Muestrario de movimientos (video/movimientos.py): 10 escenas de ~5 s, cada una con un tema.

    python3 muestras.py salida_sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.join(AQUI, "..")
for d in ("video", "tesla", "darwin", "galileo"): sys.path.insert(0, os.path.join(RAIZ, d))
import estilo as E
import movimientos as M
import efectos as EF
import evolucion as DW                                   # elementos ya convertidos a puntos
import galileo as GA
from movimientos import ss

W, H, FPS = 1080, 1920, 24
SEG = 5.0
rng = np.random.default_rng(3)
def sub(P, n, seed=0):
    r = np.random.default_rng(seed); return P[r.choice(len(P), min(n, len(P)), replace=False)][:, :3]
def cuerpo(P, esc, cx, cy, b=1.0):
    return np.c_[P[:, 0]*esc + cx, P[:, 1]*esc + cy, P[:, 2]*b]
def junta(*partes):
    Q = np.concatenate([np.c_[p[0], p[1], p[2]] if isinstance(p, tuple) else p for p in partes])
    return Q[:, 0], Q[:, 1], Q[:, 2]

# 1 ---------- tarjeta que gira: el mito de la marcha -> el ancestro común ----------
MARCHA = sub(DW.S_MARCHA, 22000, 1); MARCHA[:, 1] += 110
CLADO = sub(DW.S_CLADO, 22000, 2); CLADO[:, 1] += 20
C1 = (540.0, 990.0); BORDE1 = M.borde_rect(540, 990, 500, 520, b=0.55)
def e_tarjeta(u):
    ang = np.pi*ss(1.5, 2.9, u) + (0.14*np.exp(-(u - 2.9)*4)*np.sin((u - 2.9)*15) if u > 2.9 else 0)
    return M.tarjeta(MARCHA, CLADO, ang, C1, borde=BORDE1)

# 2 ---------- mesa que se inclina: el árbol de la vida se vuelve un mapa ----------
ARBOL = sub(DW.S_ARBOL, 24000, 3)
def e_mesa(u):
    a = 1.15*ss(1.0, 2.8, u); g = 0.35*np.sin((u - 1.0)*0.9)*ss(1.0, 2.8, u)
    x, y, w = M.inclinar(ARBOL, a, 1460, (540, 960), giro=g)
    return x, y - 260*ss(1.0, 2.8, u), w

# 3 ---------- tela que se hunde: el Sol curva el espacio y la Tierra rueda en la curva ----------
SOL = GA.SOL; TIERRA = GA.TIERRA_P
def e_tela(u):
    hund = 330*ss(0.8, 2.2, u)
    (x, y, w), alto = M.tela(hund)
    sx, sy, f = M.ver_tela(np.array([0.0]), np.array([hund - 140*ss(0.8, 2.2, u)]), np.array([0.0]))   # el Sol baja a la tela
    sx, sy = sx[0], sy[0] - 520 + 520*ss(0.0, 2.2, u)
    a = (u - 1.8)*2.4; R = 420; tx, tz = R*np.cos(a), R*np.sin(a)
    px, py, pf = M.ver_tela(np.array([tx]), np.array([alto(tx, tz) - 40]), np.array([tz]))
    vis = ss(1.8, 2.4, u)
    return junta((x, y, w), cuerpo(SOL, 120, sx, sy, 0.9), cuerpo(TIERRA, 34*pf[0], px[0], py[0], 1.2*vis))

# 4 ---------- túnel de planos: un viaje por la historia ----------
PLANOS = [(sub(GA.TELESC, 7000, 4), 520, "1609"), (sub(GA.ESTATUA, 9000, 5), 0.62, "1610"),
          (sub(DW.S_RETRATO, 9000, 6), 0.7, "1859"), (sub(GA.JUP, 8000, 7), 300, "HOY")]
_ret = PLANOS[2][0]; _ret[:, 0] -= 540; _ret[:, 1] -= 970               # retrato centrado en 0,0
from textos import Texto, puntos_de_texto
ANIOS = [puntos_de_texto(Texto(a, 0, 1, tam=80), seed=k) for k, (_, _, a) in enumerate(PLANOS)]
def e_tunel(u):
    cz = -900 + u*1000; partes = []
    for k, (P, esc, _) in enumerate(PLANOS):
        Zr = k*1300 - cz
        if Zr < -1200: continue
        f = M.D/max(M.D + Zr, 60); dx = (-1)**k*170*f
        a = ss(-1200, -500, Zr)*(1 - ss(3200, 4200, Zr))                  # aparece de lejos, se va al pasar
        partes.append(np.c_[P[:, 0]*esc*f + 540 + dx, P[:, 1]*esc*f + 960, P[:, 2]*a*np.clip(f, 0.4, 1.3)])
        T = ANIOS[k]; partes.append(np.c_[T[:, 0]*f + 540 + dx, T[:, 1]*f + 960 + 560*f, np.full(len(T), 1.2*a)])
    return junta(*partes)

# 5 ---------- zoom infinito: de la galaxia a la Tierra ----------
GAL = np.c_[EF.galaxia(16000, seed=9, radio=430), np.full(16000, 0.6)]
GAL = np.r_[GAL, np.c_[rng.normal(0, 30, 3000), rng.normal(0, 18, 3000), np.full(3000, 1.0)]]   # núcleo brillante
P1 = np.array([250.0, 95.0])                                             # dónde está el Sol en la galaxia
ORB = np.concatenate([np.c_[R*np.cos(np.linspace(0, 6.28, int(R*3))), R*np.sin(np.linspace(0, 6.28, int(R*3))),
                            np.full(int(R*3), 0.25)] for R in (8, 11, 15)])
def e_zoom(u):
    k1 = ss(0.4, 2.0, u); k2 = ss(2.5, 4.2, u)
    z = 28**k1*12**k2
    anc = P1 + np.array([11.0, 0.0])*k2                                  # el ancla pasa del Sol a la Tierra
    cx, cy = anc
    sx = lambda X: (X - cx)*z + 540; sy = lambda Y: (Y - cy)*z + 960
    gal = np.c_[sx(GAL[:, 0]), sy(GAL[:, 1]), GAL[:, 2]*(1 - ss(14, 40, z))]
    sol = np.c_[sx(P1[0] + SOL[:, 0]*5), sy(P1[1] + SOL[:, 1]*5), SOL[:, 2]*np.clip((z*5/60)**1.5, 0, 1)*0.9]
    orb = np.c_[sx(P1[0] + ORB[:, 0]), sy(P1[1] + ORB[:, 1]), ORB[:, 2]*ss(8, 20, z)]
    tie = np.c_[sx(P1[0] + 11 + TIERRA[:, 0]), sy(P1[1] + TIERRA[:, 1]), TIERRA[:, 2]*np.clip((z/40)**1.5, 0, 1)*np.clip(z/40, 1, 7)**0.9]
    return junta(gal, sol, orb, tie)

# 6 ---------- despiece: las partes del telescopio ----------
TEL = GA.TELESC; tx, ty = TEL[:, 0], TEL[:, 1]
PARTE = np.select([ty > 0.12, tx < -0.18, tx < 0.12, tx < 0.36], [0, 1, 2, 3], 4)     # soporte, ocular, cuerpo, tubo, boca
SEPARA = np.array([(0, 300), (-230, 60), (-40, -120), (120, -220), (300, -330)], float)
NOMBRES = ["SOPORTE", "OCULAR", "CUERPO", "TUBO", "LENTE"]
CENTROS = np.array([[tx[PARTE == k].mean()*900 + 540 + SEPARA[k, 0], ty[PARTE == k].mean()*900 + 960 + SEPARA[k, 1]] for k in range(5)])
def e_despiece(u):
    e = ss(1.0, 2.0, u)*(1 - ss(3.7, 4.6, u))
    off = SEPARA[PARTE]*e[None] if np.ndim(e) else SEPARA[PARTE]*e
    return TEL[:, 0]*900 + 540 + off[:, 0], TEL[:, 1]*900 + 960 + off[:, 1], TEL[:, 2]*1.6

# 7 ---------- paralaje por capas: profundidad con puntos ----------
CAPAS = [(M.cordillera(11, 260, 1020, 6000, 0.8), 0.15, 0.45), (M.cordillera(12, 230, 1180, 8000, 1.2), 0.4, 0.7),
         (M.cordillera(13, 200, 1340, 9000, 1.7), 0.75, 0.9), (M.cordillera(14, 160, 1480, 9000, 2.3), 1.25, 1.1)]
def e_paralaje(u):
    cam = -u*260; partes = [cuerpo(SOL, 80, 760 + cam*0.03, 640, 0.7)]
    for P, vel, b in CAPAS:
        partes.append(np.c_[P[:, 0] + 540 + cam*vel, P[:, 1], P[:, 2]*b])
    return junta(*partes)

# 8 ---------- campo de flujo: el escudo magnético de la Tierra ----------
LINEAS = M.lineas_dipolo([190, 260, 340, 430, 530, 640], inclina=0.19)
LIN_P = np.concatenate([L[::3] for L in LINEAS])
def e_campo(u):
    px, py = M.particulas_en_lineas(LINEAS, u, por_linea=16)
    g = ss(0.3, 1.2, u)
    return junta(cuerpo(TIERRA, 120, 540, 960, 1.2), np.c_[LIN_P[:, 0] + 540, LIN_P[:, 1] + 960, np.full(len(LIN_P), 0.5*g)],
                 np.c_[px + 540, py + 960, np.full(len(px), 1.5*g)], np.c_[px + 538, py + 958, np.full(len(px), 0.7*g)])

# 9 ---------- escáner de luz: las capas de la Tierra ----------
def capas_tierra(n=26000):
    r = np.sqrt(rng.uniform(0, 1, n)); a = rng.uniform(0, 2*np.pi, n)
    b = np.select([r < 0.19, r < 0.55, r < 0.96], [1.0, 0.75, 0.35], 0.9)
    keep = rng.uniform(size=n) < np.select([r < 0.19, r < 0.55, r < 0.96], [1.0, 0.8, 0.45], 1.0)
    anillos = np.concatenate([np.c_[R*np.cos(np.linspace(0, 6.28, 500)), R*np.sin(np.linspace(0, 6.28, 500)), np.full(500, 0.9)] for R in (0.19, 0.55, 0.96)])
    return np.r_[np.c_[r*np.cos(a), r*np.sin(a), b][keep], anillos]
CAPAS_T = capas_tierra(); SUP = np.r_[GA.disco_liso(9000, 31, 0.25)]
def e_escaner(u):
    R = 360; xb = -R*1.35 + 2.7*R*ss(0.6, 4.2, u); ancho = 150
    S = cuerpo(SUP, R, 540, 960, 1.5); C = cuerpo(CAPAS_T, R, 540, 960, 1.6)
    dentro_s = np.abs(S[:, 0] - 540 - xb) < ancho; dentro_c = np.abs(C[:, 0] - 540 - xb) < ancho
    yy = np.linspace(960 - R*1.1, 960 + R*1.1, 300)
    bordes = [np.c_[np.full(300, 540 + xb + s*ancho), yy, np.full(300, 0.8)] for s in (-1, 1)]
    return junta(S[~dentro_s], C[dentro_c], *bordes)

# 10 ---------- pliegue de página: del retrato a su idea ----------
RET = sub(DW.S_RETRATO, 22000, 8); RET[:, 1] -= 30
ARB2 = sub(DW.S_ARBOL, 22000, 9); ARB2[:, 1] -= 60
def e_pagina(u):
    x, y, w = M.pagina(RET, ARB2, ss(1.3, 3.3, u), (540, 960), 500, 560)
    B = M.borde_rect(540, 960, 500, 600, b=0.4); lomo = np.c_[np.full(240, 540.0), np.linspace(360, 1560, 240), np.full(240, 0.6)]
    return junta((x, y, w), B, lomo)

ESCENAS = [("TARJETA QUE GIRA", "DEL MITO A LA REALIDAD", e_tarjeta), ("MESA QUE SE INCLINA", "UN ÁRBOL QUE SE VUELVE MAPA", e_mesa),
           ("TELA QUE SE HUNDE", "ASÍ CURVA EL SOL EL ESPACIO", e_tela), ("TÚNEL DE PLANOS", "UN VIAJE POR LA HISTORIA", e_tunel),
           ("ZOOM INFINITO", "DE LA GALAXIA A LA TIERRA", e_zoom), ("DESPIECE", "LAS PARTES DE UN TELESCOPIO", e_despiece),
           ("PARALAJE POR CAPAS", "PROFUNDIDAD CON PUNTOS", e_paralaje), ("CAMPO DE FLUJO", "EL ESCUDO MAGNÉTICO", e_campo),
           ("ESCÁNER DE LUZ", "LAS CAPAS DE LA TIERRA", e_escaner), ("PLIEGUE DE PÁGINA", "DEL RETRATO A SU IDEA", e_pagina)]
DUR = SEG*len(ESCENAS)

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2) & (w > 0); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)
def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

def frame(t):
    k = min(int(t//SEG), len(ESCENAS) - 1); u = t - k*SEG
    x, y, w = ESCENAS[k][2](u)
    fase = np.random.default_rng(k).uniform(0, 6.28, len(x))
    x = x + 0.7*np.sin(t*1.3 + fase); y = y + 0.7*np.cos(t*1.1 + fase)
    w = w*ss(0, 0.35, u)*(1 - ss(SEG - 0.35, SEG, u))*1.8                # fundido corto entre muestras
    big = np.random.default_rng(k + 50).uniform(size=len(x)) < 0.2
    sm = np.zeros((H, W)); bg = np.zeros((H, W)); splat(sm, x[~big], y[~big], w[~big]); splat(bg, x[big], y[big], w[big])
    return (np.clip(sm + 2.2*blur(bg), 0, 1)*255).astype(np.uint8)

def textos():
    T = []
    for k, (a, b, _) in enumerate(ESCENAS):
        t0 = k*SEG; T += [Texto(a, t0 + 0.2, t0 + SEG - 0.6, y=230, tam=E.TAM_TITULO), Texto(b, t0 + 0.5, t0 + SEG - 0.5, y=295, tam=E.TAM_ETIQUETA)]
    T += [Texto(n, 5*SEG + 2.0, 5*SEG + 3.6, x=float(np.clip(c[0], 150, 930)), y=float(c[1]) - 70, tam=34)
          for n, c in zip(NOMBRES, CENTROS)]
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
