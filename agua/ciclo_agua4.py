"""El ciclo del agua v3: nuestra gota es UNA MÁS entre muchas gotitas iguales que hacen lo mismo;
solo brilla más y lleva su anillo. La nube y la montaña van solo de perfil (líneas finas de puntos).

Reutiliza el recorrido, la cámara, el mar y los textos de ciclo_agua2.py.

    python3 ciclo_agua3.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import ciclo_agua2 as B
from ciclo_agua2 import W, H, FPS, ss, E, GOTA, camino, camara, mar, splat, blur, indicador, PANT_Y
from ciclo_agua2 import T_EV, T_CO, T_PR, T_ES, T_FIN, DUR, Y_NUBE, LADERA, NM
from formacion import converger, _origen

rng = np.random.default_rng(17)

# ---------- perfiles (líneas de puntos) ----------
def linea_puntos(pts, paso=2.6, jit=1.0, capas=((0, 1.0), (3.5, 0.45), (-3.5, 0.3))):
    """Polilínea -> puntos a lo largo, en 2-3 trazos paralelos (borde a mano, de puntos)."""
    pts = np.asarray(pts, float); seg = np.hypot(*np.diff(pts, axis=0).T); L = np.r_[0, np.cumsum(seg)]
    s = np.arange(0, L[-1], paso); x = np.interp(s, L, pts[:, 0]); y = np.interp(s, L, pts[:, 1])
    nx, ny = -np.gradient(y), np.gradient(x); nn = np.hypot(nx, ny) + 1e-9; nx, ny = nx/nn, ny/nn
    X, Y, Wt = [], [], []
    for off, b in capas:
        m = rng.uniform(size=len(s)) < (1.0 if off == 0 else 0.6)
        X.append((x + nx*off + rng.normal(0, jit, len(s)))[m]); Y.append((y + ny*off + rng.normal(0, jit, len(s)))[m])
        Wt.append(np.full(m.sum(), b))
    return np.c_[np.concatenate(X), np.concatenate(Y), np.concatenate(Wt)]

# montaña: cresta + algunas líneas de ladera
xs = np.linspace(255, 540, 220)
perf = np.c_[xs*2 + B.MONT_X0, (650 - 380*np.exp(-((xs - 450)/105)**2) - 70*np.exp(-((xs - 360)/45)**2)
                                - 10*np.sin(xs/7)*np.exp(-((xs - 440)/90)**2))*2 + B.MONT_Y0]
MONT_L = [linea_puntos(perf, 2.4)]
for k in range(9):                                       # trazos de ladera (sombras sueltas)
    i = int(len(perf)*(0.15 + 0.08*k)); x0, y0 = perf[i]
    if y0 > -60: continue
    largo = rng.uniform(80, 200)
    MONT_L.append(linea_puntos([(x0, y0 + 10), (x0 + largo*0.25, y0 + largo)], 4.0, 1.4, ((0, 0.35),)))
MONT_P = np.concatenate(MONT_L)

# nube: contorno de la unión de círculos
def contorno_nube():
    im = Image.new("L", (620, 400)); d = ImageDraw.Draw(im); cx, cy = 310, 200
    for dx, dy, r in ((-75, 8, 42), (-30, -20, 55), (28, -12, 50), (75, 8, 40), (0, 20, 55), (-50, 25, 38), (50, 25, 40)):
        dx, dy, r = dx*2, dy*2, r*2; d.ellipse((cx + dx - r, cy + dy - r*0.72, cx + dx + r, cy + dy + r*0.72), fill=255)
    m = np.asarray(im) > 0; borde = m & ~ndimage.binary_erosion(m, iterations=2)
    ys, xs_ = np.nonzero(borde); ang = np.arctan2(ys - cy, xs_ - cx); o = np.argsort(ang)
    p = np.c_[xs_[o] + 600 - 310, ys[o] + Y_NUBE - 200].astype(float)
    sel = rng.uniform(size=len(p)) < 0.55
    out = np.c_[p[sel] + rng.normal(0, 1.0, (sel.sum(), 2)), np.full(sel.sum(), 0.9)]
    # un segundo trazo interior tenue (volumen)
    inn = ndimage.binary_erosion(m, iterations=22); b2 = inn & ~ndimage.binary_erosion(inn, iterations=2)
    ys2, xs2 = np.nonzero(b2); s2 = rng.uniform(size=len(xs2)) < 0.18
    return np.r_[out, np.c_[xs2[s2] + 290, ys2[s2] + Y_NUBE - 200, np.full(s2.sum(), 0.35)]]
def nube_cielo():
    xs = np.linspace(-40, W + 40, 700); base = Y_NUBE + 160
    borde = base + 34*np.sin(xs/95) + 18*np.sin(xs/37 + 1) + 70*np.abs(np.sin(xs/210 + 0.6))**3
    P1 = linea_puntos(np.c_[xs, borde], 2.2, 0.9)
    n = 9000; x = rng.uniform(-40, W + 40, n); prof = rng.uniform(0, 1, n)**1.3*1100
    y = np.interp(x, xs, borde) - prof - 6
    b = 0.55*np.exp(-prof/360)*rng.uniform(0.4, 1, n)                 # más densa cerca del borde, se pierde hacia arriba
    return np.r_[P1, np.c_[x, y, b]]
NUBE_P = nube_cielo()

# ---------- gotitas: muchas iguales a la nuestra ----------
NO = 26
o_dx = rng.permutation(np.r_[np.linspace(-520, -70, 13), np.linspace(70, 520, 13)]) + rng.normal(0, 18, NO)
o_dy = rng.uniform(-1, 1, NO)*70; o_d = rng.uniform(-0.9, 0.9, NO)
PTS = 420                                                # puntos por gotita (la nuestra: 420 al ser chica)
o_idx = np.array([np.arange(PTS) for _ in range(NO)])          # el mismo dibujo que la nuestra
o_ang = rng.uniform(0, 2*np.pi, (NO, PTS)); o_rad = np.clip(np.abs(rng.normal(0, 0.45, (NO, PTS))), 0, 1)
o_b = rng.uniform(0.45, 0.6, NO)

def factor_dispersion(t):
    """Qué tan separadas están las gotitas de la nuestra según la etapa (se juntan al bajar por la ladera)."""
    if t < T_EV: return 1.0
    if t < T_CO: return 1.0 - 0.2*ss(T_EV, T_CO, t)
    if t < T_PR: return 0.8 - 0.35*ss(T_CO, T_CO + 1.5, t)
    if t < T_ES: return 0.45 - 0.27*ss(T_PR + 0.6, T_PR + 2.4, t)
    return 0.18 - 0.16*ss(T_ES, T_ES + 1.0, t)        # por la ladera: en fila, como un hilo de agua

def o_vis(t, i):
    """En la escorrentía solo bajan un par de gotas con la nuestra."""
    return 1.0 if i < 3 else 1 - ss(T_PR + 1.8, T_ES + 0.2, t)

def gotitas(t):
    """Todas las otras gotas: el mismo recorrido que la nuestra, con su propio desfase y lugar."""
    if t < 3.4 or t > T_FIN + 1.0: return None
    f = factor_dispersion(t); vis = ss(3.6, 4.8, t)*(1 - ss(T_FIN - 0.2, T_FIN + 0.8, t))
    X, Y, Wt = [], [], []
    for i in range(NO):
        tt = float(np.clip(t - o_d[i], 5.0, T_FIN - 0.05))
        gx, gy, esc, rac = camino(tt)
        base = GOTA[o_idx[i]]
        x = base[:, 0]*esc; y = base[:, 1]*esc
        if rac > 0:
            R_ = 50*rac; a = o_ang[i] + tt*0.9*(1.2 - o_rad[i])
            x = x*(1 - rac) + R_*o_rad[i]*np.cos(a); y = y*(1 - rac) + R_*o_rad[i]*np.sin(a)
        X.append(x + gx + o_dx[i]*f); Y.append(y + gy + o_dy[i]*f + 3*np.sin(t*2 + i))
        Wt.append(base[:, 2]*o_b[i]*vis*o_vis(t, i))
    return np.concatenate(X), np.concatenate(Y), np.concatenate(Wt)

def gota_nuestra(t):
    x, y, w, gx, gy, esc, rac = B.gota(t)
    # al achicarse, quedan ~420 puntos (como las demás pero algo más densa) para que no parezca pegada encima
    keep = np.ones(len(x)); keep[420:] = np.clip((esc - 0.2)/0.35, 0, 1)
    return x, y, w*keep, gx, gy, esc, rac

def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W)); amb = np.zeros((H, W))
    cy = camara(t); P = lambda y: y - cy + PANT_Y
    entorno = ss(3.0, 4.4, t)*(1 - ss(T_FIN - 0.2, T_FIN + 1.0, t))
    # mar tenue (para que las gotitas floten sobre él)
    mx, my, mb = mar(t); o, dem, _ = _origen(NM, 41); e = ss(0, 1, (t - 3.0 - dem*0.6)/0.9)
    splat(amb, o[:, 0]*(1 - e) + mx*e, P(my)*e + o[:, 1]*(1 - e), mb*0.55*entorno)
    # montaña y nube: solo perfil
    vm = ss(T_PR - 0.6, T_PR + 0.4, t)*(1 - ss(T_FIN - 0.2, T_FIN + 1.0, t))
    if vm > 0.01:
        o2, d2, _ = _origen(len(MONT_P), 44); e2 = ss(0, 1, (t - T_PR + 0.6 - d2*0.5)/0.8)
        splat(amb, o2[:, 0]*(1 - e2) + MONT_P[:, 0]*e2, o2[:, 1]*(1 - e2) + P(MONT_P[:, 1])*e2, MONT_P[:, 2]*vm)
    vn = ss(T_CO - 0.6, T_CO + 0.6, t)*(1 - ss(T_PR + 2.4, T_ES + 0.3, t))
    if vn > 0.01:
        o3, d3, _ = _origen(len(NUBE_P), 45); e3 = ss(0, 1, (t - T_CO + 0.6 - d3*0.5)/0.8)
        splat(amb, o3[:, 0]*(1 - e3) + NUBE_P[:, 0]*e3, o3[:, 1]*(1 - e3) + P(NUBE_P[:, 1])*e3, NUBE_P[:, 2]*vn)
    # rayos del Sol en la evaporación
    I = ss(T_EV, T_EV + 0.8, t)*(1 - ss(T_CO, T_CO + 1.2, t))
    if I > 0.01:
        for j in range(12):
            ang = 0.35 + j*0.09; rr = np.arange(80, 1500, 9.0)
            splat(amb, -60 + rr*np.cos(ang), -60 + rr*np.sin(ang), I*0.3*(1 - rr/1500)**1.5*(0.7 + 0.3*np.sin(t*2 + j)))
    # las otras gotitas
    g = gotitas(t)
    if g is not None:
        x, y, w = g; splat(sm, x, P(y), w*0.75); splat(bg, x, P(y), w*0.15)
    # LA nuestra: misma forma, más brillo + anillo
    x, y, w, gx, gy, esc, rac = gota_nuestra(t)
    splat(sm, x, P(y), w*3.0); splat(bg, x, P(y), w*1.8)              # la nuestra: mucho más brillo
    est = ss(T_EV, T_EV + 1.0, t)*(1 - ss(T_FIN, T_FIN + 0.6, t))     # estela: su recorrido reciente
    if est > 0.01:
        tt = t - np.linspace(0.05, 1.6, 90); cam = [camino(max(u, 0)) for u in tt]
        ex = np.array([c[0] for c in cam]); ey = np.array([c[1] for c in cam])
        splat(sm, ex + rng.normal(0, 2, 90), P(ey) + rng.normal(0, 2, 90), est*0.55*(1 - np.linspace(0, 1, 90))**1.5)
    marca = 0
    if marca > 0.01:
        a = np.linspace(0, 2*np.pi, 80, endpoint=False) + t*0.7; r = 62 + 70*rac
        splat(sm, gx + r*np.cos(a), P(gy) + r*np.sin(a), np.full(80, 1.2*marca)); splat(bg, gx + r*np.cos(a), P(gy) + r*np.sin(a), np.full(80, 0.4*marca))
    indicador(sm, t)
    img = (1.6*(sm + 2.2*blur(bg)) + 1.15*amb)*min(1, (DUR - t)/E.FUNDIDO_FINAL)
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

textos = B.textos

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
