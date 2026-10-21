"""El ciclo del agua v2: UNA gota protagonista, siempre identificada (brilla + anillo), la cámara la sigue.

Mundo vertical: el mar en y=0, la nube arriba (y<0), la montaña a la derecha. La gota se forma (puntos dispersos),
cae al mar entre miles de gotas tenues, se evapora en un racimo brillante que sube, se condensa en la nube,
cae como lluvia sobre la montaña, baja por la ladera y vuelve al mar. Remate: vuelve a ser la gota grande.

    python3 ciclo_agua2.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "video")); sys.path.insert(0, os.path.join(AQUI, "..", "tesla"))
import estilo as E
import stipple
from formacion import converger, textos_gancho, _origen

W, H, FPS = 1080, 1920, 24
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))
rng = np.random.default_rng(8)
PANT_Y = 960.0                                          # la cámara pone la gota a esta altura de pantalla

# ---------- elementos (Voronoi una vez, en caché) ----------
def voronoi_de(nombre, w, h, dibujar, n, seed, blur=2):
    cache = os.path.join(AQUI, f"cache2_{nombre}.npy")
    if os.path.exists(cache): return np.load(cache)
    im = Image.new("L", (w//2, h//2)); dibujar(ImageDraw.Draw(im)); im = im.filter(ImageFilter.GaussianBlur(blur))
    dens = (np.asarray(im, float)/255)**1.3 + 1e-6
    p, _ = stipple.voronoi(dens, n, 30, seed); p = p*2
    t = dens[np.clip((p[:, 1]/2).astype(int), 0, h//2 - 1), np.clip((p[:, 0]/2).astype(int), 0, w//2 - 1)]
    out = np.c_[p, np.clip(t/np.percentile(t, 95), 0.25, 1)]; np.save(cache, out); return out

def d_gota(d):                                          # gota de 520x700 (centro en 260, 380)
    cx, cy, r = 130, 200, 105
    pts = []
    for a in np.linspace(0, 2*np.pi, 300):
        x = cx + r*np.cos(a)*(1 - 0.55*max(0, -np.sin(a))**3)
        y = cy + r*np.sin(a)*(1 + 0.8*max(0, -np.sin(a))**1.4)
        pts.append((x, y))
    d.polygon(pts, fill=140); d.line(pts + [pts[0]], fill=255, width=4)
    d.ellipse((cx - 62, cy - 30, cx - 22, cy + 40), fill=255)          # brillo
GOTA = voronoi_de("gota", 520, 700, d_gota, 5200, 1)
GOTA[:, 0] -= 260; GOTA[:, 1] -= 380                    # centrada en (0, 0)

MONT_X0, MONT_Y0 = 0, -1300                             # caja de la montaña en el mundo (1080 x 1300)
def d_montana(d):
    xs = np.linspace(255, 540, 160)
    perf = [(x, 650 - 380*np.exp(-((x - 450)/105)**2) - 70*np.exp(-((x - 360)/45)**2) - 10*np.sin(x/7)*np.exp(-((x - 440)/90)**2)) for x in xs]
    d.polygon([(255, 650)] + perf + [(540, 650)], fill=60); d.line(perf, fill=230, width=3)
    for i in range(0, len(perf) - 1, 2):              # ladera izquierda iluminada
        if perf[i][1] > perf[i + 1][1]: d.line([perf[i], (perf[i][0] + 10, perf[i][1] + 50)], fill=140, width=5)
MONT = voronoi_de("montana", 1080, 1300, d_montana, 9000, 2)
MONT[:, 0] += MONT_X0; MONT[:, 1] += MONT_Y0

Y_NUBE = -1550.0
def d_nube(d):
    cx, cy = 155, 100
    for dx, dy, r in ((-75, 8, 42), (-30, -20, 55), (28, -12, 50), (75, 8, 40), (0, 20, 55), (-50, 25, 38), (50, 25, 40)):
        d.ellipse((cx + dx - r, cy + dy - r*0.72, cx + dx + r, cy + dy + r*0.72), fill=200)
NUBE = voronoi_de("nube", 620, 400, d_nube, 7000, 3)
NUBE[:, 0] += 600 - 310; NUBE[:, 1] += Y_NUBE - 200

# mar: miles de gotas tenues (olas)
NM = 11000; m_x = rng.uniform(-20, W + 20, NM); m_d = rng.uniform(0, 1, NM)**2.4
m_y0 = 8 + m_d*700 + 30*np.round(rng.uniform(0, 4, NM))*(m_d < 0.25); m_b = (1.05 - 0.85*m_d)*rng.uniform(0.5, 1, NM); m_ph = rng.uniform(0, 6.28, NM)
def mar(t):
    return m_x, m_y0 + 6*np.sin(m_x*0.025 + t*2 + m_d*4) + 3*np.sin(m_x*0.07 - t*2.8 + m_ph), m_b

# ---------- guion ----------
ETAPAS = ["EVAPORACIÓN", "CONDENSACIÓN", "PRECIPITACIÓN", "ESCORRENTÍA"]
T0 = E.ACCION_INICIO; SEG = E.ETAPA
T_EV, T_CO, T_PR, T_ES = T0, T0 + SEG, T0 + 2*SEG, T0 + 3*SEG
T_FIN = T_ES + 2.6
DUR = T_FIN + E.CIERRE
X_MAR = 400.0
ATERRIZA = (790.0, -560.0)                              # punto de la ladera donde cae la gota
LADERA = np.array([(790, -560), (750, -450), (705, -330), (660, -215), (615, -110), (570, -30), (530, 8), (470, 20)], float)

def camino(t):
    """Centro de la gota en el mundo (x, y), escala de la gota y 'racimo' (0 = gota, 1 = vapor disperso)."""
    if t < 2.8: return 540.0, -560.0, 1.0, 0.0
    if t < T_EV + 0.6:                                  # cae al mar y se achica
        e = ss(2.8, 5.0, t)**1.6
        x = 540 + (X_MAR - 540)*ss(2.8, 5.0, t); y = -560 + 560*e + 4*np.sin(t*3)*ss(5.0, 5.4, t)
        return x, y, 1.0 - 0.8*ss(2.8, 4.6, t), 0.0
    if t < T_CO + 0.3:                                  # evaporación: racimo que sube hasta la nube
        e = ss(T_EV + 0.6, T_CO + 0.2, t)
        return X_MAR + (600 - X_MAR)*e + 30*np.sin(t*1.7)*e*(1 - e), Y_NUBE*e**1.15, 0.2, ss(T_EV + 0.4, T_EV + 1.4, t)
    if t < T_PR + 0.6:                                  # condensación: el racimo vuelve a ser gota dentro de la nube
        return 600.0, Y_NUBE + 20*np.sin(t*1.3), 0.2, 1 - ss(T_CO + 0.6, T_CO + 2.0, t)
    if t < T_ES:                                        # precipitación: cae a la ladera
        e = ss(T_PR + 0.6, T_PR + 2.4, t)**1.5
        return 600 + (ATERRIZA[0] - 600)*e, Y_NUBE + 60 + (ATERRIZA[1] - Y_NUBE - 60)*e, 0.2, 0.0
    if t < T_FIN:                                       # escorrentía: baja por la ladera al mar
        seg = np.cumsum(np.r_[0, np.hypot(*np.diff(LADERA, axis=0).T)])
        s = ss(T_ES + 0.1, T_ES + 2.3, t)*seg[-1]
        return float(np.interp(s, seg, LADERA[:, 0])), float(np.interp(s, seg, LADERA[:, 1])), 0.2, 0.0
    e = ss(T_FIN, T_FIN + E.REMATE_FORMA, t)            # remate: vuelve a ser la gota grande
    return 470 + (540 - 470)*e, 20 + (-560 - 20)*e, 0.2 + 0.8*e, 0.0

def camara(t):
    """La cámara sigue a la gota con suavidad (promedio de su altura en el último medio segundo)."""
    ys = [camino(max(t - d, 0))[1] for d in np.linspace(0, 0.6, 7)]
    return float(np.mean(ys))

# racimo de vapor: cada punto de la gota tiene su lugar en el racimo
r_ang = rng.uniform(0, 2*np.pi, len(GOTA)); r_rad = np.clip(np.abs(rng.normal(0, 0.45, len(GOTA))), 0, 1)
def gota(t):
    from formacion import converger
    gx, gy, esc, rac = camino(t)
    x = GOTA[:, 0]*esc; y = GOTA[:, 1]*esc; w = GOTA[:, 2].copy()
    if rac > 0:                                          # vapor: los puntos se separan y ondulan, siguen siendo "ella"
        R_ = 120*rac
        vx = R_*r_rad*np.cos(r_ang + t*0.9*(1.2 - r_rad)) + 8*np.sin(t*3 + r_ang*7)*rac
        vy = R_*r_rad*np.sin(r_ang + t*0.9*(1.2 - r_rad)) + 8*np.cos(t*2.6 + r_ang*5)*rac
        x = x*(1 - rac) + vx; y = y*(1 - rac) + vy
    w = w*(0.55 + 0.45*esc)                              # chiquita: menos peso por punto (se ven los puntos)
    x, y, w = x + gx, y + gy, w
    if t < 3: x, y, w = converger(x, y - camara(t) + PANT_Y, w, t, seed=31); y = y + camara(t) - PANT_Y
    return x, y, w, gx, gy, esc, rac

# lluvia y vapor ambiente
NVA = 4000; va_x = rng.uniform(20, W - 20, NVA); va_ph = rng.uniform(0, 1, NVA); va_o = rng.uniform(0, 6.28, NVA)
NLL = 500; ll_x = rng.uniform(380, 900, NLL); ll_ph = rng.uniform(0, 1, NLL); ll_T = rng.uniform(0.6, 0.9, NLL)
NHI = 500; hi_ph = rng.uniform(0, 1, NHI); hi_l = rng.normal(0, 5, NHI)

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)
def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

def llegar(P, t0, seed, t, dur=0.9):
    o, dem, fase = _origen(len(P), seed); e = ss(0, 1, (t - t0 - dem*0.6)/dur); lib = 1 - e
    return o[:, 0]*lib + P[:, 0]*e, o[:, 1]*lib + P[:, 1]*e, P[:, 2]*(0.8 + 0.2*e), e

def indicador(buf, t):
    if t < T0 - 0.6 or t > T_FIN + 0.6: return
    e = ss(T0 - 0.6, T0, t)*(1 - ss(T_FIN, T_FIN + 0.6, t)); pos = (t - T0)/SEG
    for k in range(4):
        x = W/2 + (k - 1.5)*44; cerca = np.clip(1 - abs(pos - k - 0.18), 0, 1)**2
        r = 2.5 + 9*cerca; a = np.linspace(0, 2*np.pi, 28, endpoint=False)
        splat(buf, x + r*np.cos(a), 1745 + r*np.sin(a), np.full(28, e*(0.15 + 0.95*cerca)))
        splat(buf, np.array([x]), np.array([1745.0]), np.array([e*(0.45 + 1.8*cerca)]))

def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W)); amb = np.zeros((H, W))
    cy = camara(t); P = lambda y: y - cy + PANT_Y        # mundo -> pantalla (vertical)
    entorno = ss(3.0, 4.4, t)*(1 - ss(T_FIN - 0.2, T_FIN + 1.0, t))
    # mar (miles de gotas tenues): entran desde dispersas cuando cae la gota
    mx, my, mb = mar(t); o, dem, _ = _origen(NM, 41); e = ss(0, 1, (t - 3.0 - dem*0.6)/0.9)
    splat(amb, o[:, 0]*(1 - e) + mx*e, (o[:, 1] - PANT_Y + cy)*(1 - e)*0 + P(my)*e + o[:, 1]*(1 - e), mb*entorno)
    # montaña y nube (aparecen cuando la cámara las alcanza)
    xm, ym, wm, _ = llegar(MONT, T_PR - 0.8, 42, t)
    splat(amb, xm, P(ym)*np.where(t > T_PR - 0.8, 1, 0) + (1 - ss(T_PR - 0.8, T_PR, t))*0, wm*ss(T_PR - 0.8, T_PR, t)*(1 - ss(T_FIN - 0.2, T_FIN + 1.0, t)))
    nube_vis = ss(T_CO - 0.4, T_CO + 1.6, t)*(1 - ss(T_PR + 2.5, T_ES, t))
    if nube_vis > 0.01:                                # el vapor de alrededor se junta en la nube
        o2, dem2, _ = _origen(len(NUBE), 43); e2 = ss(0, 1, (t - T_CO + 0.4 - dem2*0.8)/1.4)
        nx = va_x[:len(NUBE)]*(1 - e2) + NUBE[:, 0]*e2 if len(NUBE) <= NVA else NUBE[:, 0]
        nx = o2[:, 0]*(1 - e2) + NUBE[:, 0]*e2; ny = (Y_NUBE + 500 + o2[:, 1]*0.3)*(1 - e2) + NUBE[:, 1]*e2
        splat(amb, nx, P(ny), NUBE[:, 2]*nube_vis*0.8)
    # vapor ambiente (evaporación): sube de todo el mar
    I = ss(T_EV, T_EV + 0.8, t)*(1 - ss(T_CO + 0.5, T_CO + 1.5, t))
    if I > 0.01:
        tau = (t/3.0 + va_ph) % 1; vy = -tau*1500; vx = va_x + 25*np.sin(tau*7 + va_o + t)
        splat(amb, vx, P(vy), 0.5*I*np.sin(np.pi*tau)**0.8)
        # el Sol: rayos desde arriba a la izquierda (pantalla)
        for j in range(12):
            ang = 0.35 + j*0.09; rr = np.arange(80, 1500, 9.0)
            splat(amb, -60 + rr*np.cos(ang), -60 + rr*np.sin(ang), I*0.35*(1 - rr/1500)**1.5*(0.7 + 0.3*np.sin(t*2 + j)))
    # lluvia
    I = ss(T_PR, T_PR + 0.5, t)*(1 - ss(T_ES + 0.5, T_ES + 1.5, t))
    if I > 0.01:
        tau = (t/ll_T + ll_ph) % 1; y0 = Y_NUBE + 80; yf = np.where(ll_x < 540, 10.0, -420 + 380*np.abs(np.sin(ll_x*0.013)))
        yy = y0 + tau*(yf - y0); xx = ll_x - tau*25
        for j in range(8): splat(amb, xx + j*0.6, P(yy - j*12), np.full(NLL, 0.95*I*(1 - j/8)))
    # hilo de agua por la ladera (escorrentía)
    I = ss(T_ES - 0.3, T_ES + 0.5, t)*(1 - ss(T_FIN, T_FIN + 0.8, t))
    if I > 0.01:
        seg = np.cumsum(np.r_[0, np.hypot(*np.diff(LADERA, axis=0).T)]); s = ((t*0.5 + hi_ph) % 1)*seg[-1]
        hx = np.interp(s, seg, LADERA[:, 0]) + hi_l; hy = np.interp(s, seg, LADERA[:, 1]) + hi_l*0.3
        splat(amb, hx, P(hy), np.full(NHI, 0.55*I))
    # LA gota: protagonista (brilla + anillo)
    x, y, w, gx, gy, esc, rac = gota(t)
    splat(sm, x, P(y), w*1.15); splat(bg, x, P(y), w*0.6)
    marca = ss(4.2, 5.0, t)*(1 - ss(T_FIN, T_FIN + 0.6, t))
    rmar = 70 + 90*rac
    if marca > 0.01:
        a = np.linspace(0, 2*np.pi, 80, endpoint=False) + t*0.7; r = rmar
        splat(sm, gx + r*np.cos(a), P(gy) + r*np.sin(a), np.full(80, 0.85*marca))
    indicador(sm, t)
    img = (1.6*(sm + 2.2*blur(bg)) + 1.15*amb)*min(1, (DUR - t)/E.FUNDIDO_FINAL)
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

def textos():
    from textos import Texto
    T = textos_gancho("ESTA GOTA DE AGUA", "TIENE MILLONES DE AÑOS")
    for k, nombre in enumerate(ETAPAS):
        t0 = T0 + k*SEG - 0.1
        T.append(Texto(nombre, t0, t0 + (E.ETAPA_QUIETA + 1.2 if k < 3 else 1.8), y=1660, tam=E.TAM_ETIQUETA))
    T += [Texto("Y SIGUE VIAJANDO", T_FIN - E.REMATE_TEXTO_ANTES, DUR - 1.3, y=230, tam=E.TAM_CIERRE),
          Texto("EL CICLO DEL AGUA", T_FIN + 0.1, DUR - 1.2, y=290, tam=E.TAM_CIERRE)]
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
