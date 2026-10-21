"""El ciclo del agua en puntillismo (B/N, 1080x1920, un solo plano).

Entrada: puntos dispersos forman una gota (con el texto). La gota cae al mar y se forma el paisaje
(mar, montaña, Sol). Etapas: evaporación (el vapor sube), condensación (ese vapor forma la nube),
precipitación (llueve sobre la montaña), escorrentía (un río baja al mar). Remate: todo vuelve a ser la gota.

    python3 ciclo_agua.py sin_textos.mp4 [n_cuadros] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "video")); sys.path.insert(0, os.path.join(AQUI, "..", "tesla"))
import estilo as E
import stipple
from formacion import textos_gancho, _origen

W, H, FPS = 1080, 1920, 24
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))
rng = np.random.default_rng(5)

# ---------- composición del plano ----------
NIVEL_MAR = 1270.0                                     # línea del mar / suelo
SOL = (240.0, 470.0, 120.0)                              # x, y, radio
NUBE_C = (650.0, 640.0)
GOTA_C, GOTA_ESC = (540.0, 860.0), 1.0

# ---------- elementos (puntos con Voronoi, una sola vez; se guardan en caché) ----------
def mapa(dibujar, blur=2):
    im = Image.new("L", (W//2, H//2)); dibujar(ImageDraw.Draw(im)); im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, float)/255

def d_gota(d):
    cx, cy = GOTA_C[0]/2, GOTA_C[1]/2
    pts = []
    for a in np.linspace(0, 2*np.pi, 300):            # gota: círculo abajo + punta arriba
        r = 120*(1 - 0.0*np.sin(a))
        x = cx + r*np.cos(a)*(1 - 0.55*max(0, -np.sin(a))**3)
        y = cy + 40 + r*np.sin(a)*(1 + 0.75*max(0, -np.sin(a))**1.4)
        pts.append((x, y))
    d.polygon(pts, fill=150)
    d.ellipse((cx - 70, cy - 10, cx - 20, cy + 70), fill=255)   # brillo
    d.line(pts + [pts[0]], fill=255, width=4)

def d_montana(d):
    base = NIVEL_MAR/2; xs = np.linspace(260, 540, 120)
    perfil = [(x, base - 265*np.exp(-((x - 430)/90)**2) - 110*np.exp(-((x - 330)/55)**2) - 25*np.sin(x/9)*np.exp(-((x - 420)/110)**2)) for x in xs]
    d.polygon(perfil + [(540, base), (260, base)], fill=70)
    d.line(perfil, fill=255, width=3)
    for i in range(1, len(perfil) - 1):                # ladera iluminada por el Sol (lado izquierdo)
        if perfil[i][1] > perfil[i+1][1]:
            d.line([perfil[i], (perfil[i][0] + 12, perfil[i][1] + 60)], fill=150, width=6)
    d.rectangle((0, base, 540, base + 160), fill=30)  # suelo bajo la línea

def d_sol(d):
    x, y, r = SOL[0]/2, SOL[1]/2, SOL[2]/2
    d.ellipse((x - r, y - r, x + r, y + r), fill=235)

def d_nube(d):
    cx, cy = NUBE_C[0]/2, NUBE_C[1]/2
    for dx, dy, r in ((-90, 10, 55), (-35, -25, 70), (35, -15, 62), (95, 12, 50), (0, 25, 70), (-60, 30, 48), (60, 32, 50)):
        dx, dy, r = dx*1.3, dy*1.3, r*1.3
        d.ellipse((cx + dx - r, cy + dy - r*0.75, cx + dx + r, cy + dy + r*0.75), fill=210)

def elemento(nombre, dibujar, n, seed):
    cache = os.path.join(AQUI, f"cache_{nombre}.npy")
    if os.path.exists(cache): return np.load(cache)
    dens = mapa(dibujar)**1.3 + 1e-6
    p, _ = stipple.voronoi(dens, n, 30, seed); p = p*2
    t = dens[np.clip((p[:, 1]/2).astype(int), 0, H//2 - 1), np.clip((p[:, 0]/2).astype(int), 0, W//2 - 1)]
    out = np.c_[p, np.clip(t/np.percentile(t, 95), 0.25, 1)]; np.save(cache, out); return out

GOTA = elemento("gota", d_gota, 7000, 1)
MONT = elemento("montana", d_montana, 9000, 2)
SOLP = elemento("sol", d_sol, 2600, 3)
NUBE = elemento("nube", d_nube, 6500, 4)

# mar: líneas de olas animadas
NM = 7500
m_x = rng.uniform(0, 560, NM); m_prof = rng.uniform(0, 1, NM)**1.5
m_y0 = NIVEL_MAR + 6 + m_prof*300; m_b = (0.9 - 0.7*m_prof)*rng.uniform(0.6, 1, NM); m_ph = rng.uniform(0, 6.28, NM)
def mar(t):
    y = m_y0 + 5*np.sin(m_x*0.03 + t*2.2 + m_prof*3) + 3*np.sin(m_x*0.08 - t*3.1 + m_ph)
    return m_x, y, m_b

# ---------- guion ----------
ETAPAS = ["EVAPORACIÓN", "CONDENSACIÓN", "PRECIPITACIÓN", "ESCORRENTÍA"]
T_CAE, T_ESCENA = 3.0, 3.4                             # la gota cae / se forma el paisaje
T0 = E.ACCION_INICIO                                    # empiezan las etapas
SEG = E.ETAPA; ULT = 3.0                                # última etapa un poco más corta
T_FIN = T0 + 3*SEG + ULT
DUR = T_FIN + E.CIERRE

def etapa(t):
    if t < T0: return -1, 0.0
    k = min(int((t - T0)//SEG), 3); return k, (t - T0 - k*SEG)

# vapor: cada punto de la nube nace como vapor en el mar y sube (sus caminos)
NV = len(NUBE)
COLS = np.linspace(50, 520, 18) + rng.normal(0, 10, 18)           # hilos de vapor
v_col = rng.integers(0, 18, NV); v_x0 = COLS[v_col] + rng.normal(0, 5, NV)
v_ph = rng.uniform(0, 1, NV); v_ond = rng.uniform(0, 6.28, 18)[v_col]

def vapor_y_nube(t):
    """Antes de condensar: vapor que sube (cíclico). Al condensar: cada partícula va a su lugar en la nube."""
    sube = 2.6                                          # segundos que tarda una partícula en subir
    tau = ((t - T0)/sube + v_ph) % 1
    x = v_x0 + (14 + 30*tau)*np.sin(tau*7 + v_ond + t*0.9) + tau*(NUBE_C[0] - 290)*0.35
    y = NIVEL_MAR - 10 - tau*(NIVEL_MAR - NUBE_C[1] - 60)
    vis = np.sin(np.pi*tau)**0.7
    cond = ss(T0 + SEG - 0.3, T0 + SEG + 2.2, t + v_ph*0.6)  # condensación: se juntan en la nube
    px = x*(1 - cond) + NUBE[:, 0]*cond; py = y*(1 - cond) + NUBE[:, 1]*cond
    w = (0.7*vis*(1 - cond) + NUBE[:, 2]*cond)
    w *= ss(T0, T0 + 0.8, t)                            # el vapor empieza con la evaporación
    return px, py, w

# lluvia y río
NL_ = 380; l_x = rng.uniform(NUBE_C[0] - 240, NUBE_C[0] + 240, NL_); l_ph = rng.uniform(0, 1, NL_); l_T = rng.uniform(0.55, 0.8, NL_)
RIO = np.array([(860, 820), (830, 900), (780, 980), (720, 1060), (650, 1140), (590, 1210), (520, 1258), (440, 1275)])
NR = 900; r_ph = rng.uniform(0, 1, NR); r_lat = rng.normal(0, 6, NR)
def rio(t, inten):
    seg = np.cumsum(np.r_[0, np.hypot(*np.diff(RIO, axis=0).T)]); L = seg[-1]
    s = ((t*0.45 + r_ph) % 1)*L
    x = np.interp(s, seg, RIO[:, 0]); y = np.interp(s, seg, RIO[:, 1])
    return x + r_lat, y + r_lat*0.4 + 2*np.sin(t*6 + r_ph*30), np.full(NR, 0.85*inten)

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)
def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

def llegar(P, t0, seed, t):
    """Como converger(), pero empezando en t0 (para elementos que entran después)."""
    o, dem, fase = _origen(len(P), seed)
    e = ss(0, 1, (t - t0 - dem*0.7)/0.9); lib = 1 - e
    return (o[:, 0]*lib + P[:, 0]*e + lib*np.sin(t*2 + fase)*12, o[:, 1]*lib + P[:, 1]*e + lib*np.cos(t*2 + fase)*12,
            P[:, 2]*(0.85 + 0.15*e))

def dispersar(x, y, w, t0, seed, t):
    """Remate: los puntos del paisaje se dispersan y se apagan."""
    if t < t0: return x, y, w
    r = np.random.default_rng(seed); n = len(x)
    ang = r.uniform(0, 2*np.pi, n); v = r.uniform(250, 900, n); k = ss(t0, t0 + 1.4, t)
    return x + np.cos(ang)*v*k, y + np.sin(ang)*v*k, w*(1 - k)

def gota_pos(t):
    """La gota: se forma (dispersos -> gota), cae al mar y salpica; vuelve a formarse en el remate."""
    from formacion import converger
    x, y, w = converger(GOTA[:, 0], GOTA[:, 1], GOTA[:, 2], t, seed=11)
    caida = ss(T_CAE, T_CAE + 0.9, t)**1.8
    dy = caida*(NIVEL_MAR - GOTA_C[1] + 40); enc = 1 - 0.75*caida
    x = GOTA_C[0] + (x - GOTA_C[0])*enc - caida*200; y = GOTA_C[1] + (y - GOTA_C[1])*enc + dy
    w = w*(1 - ss(T_CAE + 0.8, T_CAE + 1.0, t))
    if t >= T_FIN:                                       # remate: la gota vuelve
        x2, y2, w2 = llegar(GOTA, T_FIN, 12, t); return x2, y2, w2
    return x, y, w

def salpicadura(sm, t):
    p = (t - T_CAE - 0.85)/0.9
    if not (0 < p < 1): return
    a = np.linspace(0, np.pi, 60); r = 20 + 160*p
    splat(sm, 340 + r*np.cos(a)*1.2, NIVEL_MAR - r*np.sin(a)*0.8*(1 - p) - 120*p*(1 - p)*np.sin(a), np.full(60, 0.9*(1 - p)))
    a2 = np.linspace(0, 2*np.pi, 80); splat(sm, 340 + r*1.4*np.cos(a2), NIVEL_MAR + 8 + r*0.25*np.sin(a2), np.full(80, 0.7*(1 - p)))

def indicador(buf, t):
    if t < T0 - 0.6 or t > T_FIN + 0.6: return
    e = ss(T0 - 0.6, T0, t)*(1 - ss(T_FIN, T_FIN + 0.6, t)); pos = (t - T0)/SEG
    for k in range(4):
        x = W/2 + (k - 1.5)*44; cerca = np.clip(1 - abs(pos - k - 0.18), 0, 1)**2
        r = 2.5 + 9*cerca; a = np.linspace(0, 2*np.pi, 28, endpoint=False)
        splat(buf, x + r*np.cos(a), 1745 + r*np.sin(a), np.full(28, e*(0.15 + 0.95*cerca)))
        splat(buf, np.array([x]), np.array([1745.0]), np.array([e*(0.45 + 1.8*cerca)]))

def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W))
    k, tt = etapa(t)
    fuera = lambda x, y, w, s: dispersar(x, y, w, T_FIN - 0.2, s, t)
    # paisaje: entra cuando cae la gota
    if t > T_ESCENA - 0.1:
        for P, seed, extra in ((MONT, 21, 1.0), (SOLP, 22, 1.0)):
            x, y, w = llegar(P, T_ESCENA, seed, t)
            if P is SOLP:                                # el Sol brilla más en la evaporación
                w = w*(1 + 0.6*ss(T0, T0 + 1.0, t)*(1 - ss(T0 + SEG, T0 + SEG + 1.5, t)))
            x, y, w = fuera(x, y, w*extra, seed + 100)
            splat(sm, x, y, w*0.9); splat(bg, x, y, w*0.35)
        mx, my, mw = mar(t); o, dem, _ = _origen(NM, 23)
        e = ss(0, 1, (t - T_ESCENA - dem*0.7)/0.9)
        mx2 = o[:, 0]*(1 - e) + mx*e; my2 = o[:, 1]*(1 - e) + my*e
        mx2, my2, mw2 = fuera(mx2, my2, mw*(0.85 + 0.15*e), 124)
        splat(sm, mx2, my2, mw2)
        # rayos del Sol durante la evaporación
        I = ss(T0, T0 + 1.0, t)*(1 - ss(T0 + SEG, T0 + SEG + 1.2, t))
        if I > 0.01:
            for j in range(16):
                ang = j*2*np.pi/16 + t*0.15; rr = np.arange(SOL[2] + 25, SOL[2] + 210, 7.0)
                splat(sm, SOL[0] + rr*np.cos(ang), SOL[1] + rr*np.sin(ang), I*0.45*(1 - (rr - SOL[2] - 25)/185)**1.5)
    # vapor -> nube
    if t > T0:
        x, y, w = vapor_y_nube(t)
        lluvia_fin = ss(T0 + 3*SEG + 1.0, T_FIN, t)        # la nube se aligera al final
        x, y, w = fuera(x, y, w*(1 - 0.5*lluvia_fin), 125)
        splat(sm, x, y, w*0.9); splat(bg, x, y, w*0.3)
    # lluvia
    I = ss(T0 + 2*SEG, T0 + 2*SEG + 0.6, t)*(1 - ss(T_FIN - 0.6, T_FIN, t))
    if I > 0.01:
        tau = (t/l_T + l_ph) % 1; y0 = NUBE_C[1] + 80; yf = 930 + 280*np.abs(np.sin(l_x))
        y = y0 + tau*(yf - y0); x = l_x - tau*30
        for j in range(6): splat(sm, x + j*0.9, y - j*11, np.full(NL_, 0.8*I*(1 - j/6)))
    # río (escorrentía)
    I = ss(T0 + 3*SEG - 0.4, T0 + 3*SEG + 0.8, t)
    if I > 0.01:
        x, y, w = rio(t, I); x, y, w = fuera(x, y, w, 126); splat(sm, x, y, w); splat(bg, x, y, w*0.4)
    # la gota
    x, y, w = gota_pos(t)
    splat(sm, x, y, w*1.1); splat(bg, x, y, w*0.45)
    salpicadura(sm, t)
    indicador(sm, t)
    img = 1.7*(sm + 2.2*blur(bg))*min(1, (DUR - t)/E.FUNDIDO_FINAL)
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

def textos():
    from textos import Texto
    T = textos_gancho("¿A DÓNDE VA", "UNA GOTA DE AGUA?")
    for k, nombre in enumerate(ETAPAS):
        t0 = T0 + k*SEG - 0.1
        T.append(Texto(nombre, t0, t0 + (E.ETAPA_QUIETA + 1.2 if k < 3 else 2.0), y=1660, tam=E.TAM_ETIQUETA))
    T += [Texto("LA MISMA AGUA", T_FIN - E.REMATE_TEXTO_ANTES, DUR - 1.3, y=230, tam=E.TAM_CIERRE),
          Texto("DESDE HACE MILLONES DE AÑOS", T_FIN + 0.1, DUR - 1.2, y=290, tam=E.TAM_CIERRE)]
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
