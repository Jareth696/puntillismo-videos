"""Ciclo del agua v5: pocas gotas grandes y bien dibujadas (contorno nítido + brillo + relleno suave);
la nuestra brilla más y tiene un halo de puntos. Nube con contorno abajo y arriba.

    python3 ciclo_agua5.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import ciclo_agua2 as B
import ciclo_agua4 as C4
from ciclo_agua2 import W, H, FPS, ss, E, camino, camara, mar, splat, blur, indicador, PANT_Y
from ciclo_agua2 import T_EV, T_CO, T_PR, T_ES, T_FIN, DUR, Y_NUBE, NM
from ciclo_agua3 import linea_puntos, MONT_P
from formacion import _origen

rng = np.random.default_rng(23)

# ---------- una gota bien dibujada (coordenadas locales, radio 1) ----------
def forma(a):
    s = np.sin(a)
    return np.cos(a)*(1 - 0.55*np.maximum(0, -s)**3), s*(1 + 0.8*np.maximum(0, -s)**1.4)
a = np.linspace(0, 2*np.pi, 150, endpoint=False)
cx_, cy_ = forma(a)
CONT = np.c_[cx_, cy_, np.full(150, 1.0)]                                   # contorno nítido
a2 = rng.uniform(0, 2*np.pi, 160); r2 = np.sqrt(rng.uniform(0, 1, 160))*0.88
fx, fy = forma(a2); REL = np.c_[fx*r2, fy*r2, 0.25 + 0.25*np.clip(fy, 0, 1)]   # más relleno abajo (volumen)           # relleno suave
ab = np.linspace(2.5, 3.6, 22); BRI = np.c_[0.6*np.cos(ab), 0.15 + 0.55*np.sin(ab)*-1, np.full(22, 0.95)]  # brillo
BRI[:, 1] = -0.05 + 0.5*np.sin(ab - 2.5)
GOTA_L = np.r_[CONT, REL, BRI]; NG = len(GOTA_L)
ang_r = rng.uniform(0, 2*np.pi, NG); rad_r = np.clip(np.abs(rng.normal(0, 0.5, NG)), 0, 1.2)  # racimo de vapor
HALO_A = rng.uniform(0, 2*np.pi, 160); HALO_R = 1.25 + rng.exponential(0.45, 160)

def dibujar(sm, bg, cx, cy, R, rac, b, nuestra, t, P, vel=(0.0, 0.0), fase=0.0):
    x = GOTA_L[:, 0]*R; y = GOTA_L[:, 1]*R; w = GOTA_L[:, 2]*b
    # movimiento sutil: se estira en la dirección en que se mueve y respira/tiembla un poco
    sp = np.hypot(*vel); est = 1 + min(sp/1400, 0.32)
    resp = 0.035*np.sin(t*2.6 + fase) + temblor(t, fase)
    x = x*(1 + resp)/np.sqrt(est); y = y*(1 - resp)*est
    if sp > 1:                                                # inclinación leve hacia donde va
        ang = np.clip(np.arctan2(vel[0], vel[1]), -0.5, 0.5)*min(sp/600, 1)
        c_, s_ = np.cos(ang), np.sin(ang); x, y = x*c_ + y*s_, -x*s_ + y*c_
    if rac > 0:                                               # vapor: los puntos se abren en un racimo que gira
        rr = R*1.5*rac; ang = ang_r + t*0.9*(1.3 - rad_r/1.2)
        x = x*(1 - rac) + rr*rad_r*np.cos(ang); y = y*(1 - rac) + rr*rad_r*np.sin(ang)
        w = w*(1 - 0.5*rac) + 0.6*b*rac
    splat(sm, cx + x, P(cy + y), w); splat(bg, cx + x, P(cy + y), w*(0.5 if nuestra else 0.15))
    if nuestra:                                              # halo de puntos alrededor (como en la evaporación)
        hr = R*HALO_R*(1 + 0.5*rac); ha = HALO_A + t*0.4
        hw = 0.55*np.exp(-(HALO_R - 1.25)/0.5)*(0.7 + 0.3*np.sin(t*4 + HALO_A*7))
        splat(sm, cx + hr*np.cos(ha), P(cy + hr*1.1*np.sin(ha)), hw)

# ---------- otras gotas: pocas, separadas ----------
NO = 8
o_dx = np.array([-170, 170, -340, 340, -510, 510, -680, 680], float) + rng.normal(0, 12, NO)
o_dy = rng.uniform(-1, 1, NO)*40; o_d = rng.uniform(-0.6, 0.6, NO)
def separacion(t):
    if t < T_CO: return 1.0
    if t < T_PR: return 1.0 - 0.15*ss(T_CO, T_CO + 1.5, t)
    if t < T_ES: return 0.85 - 0.25*ss(T_PR + 0.6, T_PR + 2.4, t)
    return 0.6
def visible_otra(t, i):
    if t > T_PR + 1.0 and i >= 2: return 1 - ss(T_PR + 1.0, T_PR + 2.0, t)   # al bajar, solo dos acompañan
    return 1.0

EXTRA = None
R_GOTA = 72.0
LLEGADAS = []                                            # momentos de impacto (los define ciclo_agua6)
def temblor(t, fase):
    """Al llegar (montaña, mar) la gota tiembla como gelatina y se asienta."""
    v = 0.0
    for t0 in LLEGADAS:
        d = t - t0 - 0.05*fase
        if 0 < d < 1.2: v += 0.12*np.exp(-d*3.2)*np.sin(d*22)
    return v                                               # radio de las gotas "con zoom"

# ---------- nube: contorno abajo y arriba (cúmulo) ----------
def nube():
    xs = np.linspace(-40, W + 40, 800)
    abajo = Y_NUBE + 170 + 30*np.sin(xs/95) + 15*np.sin(xs/37 + 1) + 55*np.abs(np.sin(xs/210 + 0.6))**3
    arriba = Y_NUBE - 330 - np.max([110*np.clip(1 - ((xs - c)/w)**2, 0, 1)**0.5 for c, w in
                                    ((90, 170), (330, 200), (560, 180), (780, 210), (1010, 170))], axis=0)
    L1 = linea_puntos(np.c_[xs, abajo], 2.2, 0.9); L2 = linea_puntos(np.c_[xs, arriba], 2.2, 0.9)
    n = 7000; x = rng.uniform(-40, W + 40, n); f = rng.uniform(0, 1, n)
    ab = np.interp(x, xs, abajo); ar = np.interp(x, xs, arriba); y = ar + (ab - ar)*f
    b = 0.32*(0.5 + 0.5*np.exp(-np.minimum(f, 1 - f)/0.12))*rng.uniform(0.4, 1, n)
    return np.r_[L1, L2, np.c_[x, y, b]]
NUBE_P = nube()

def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W)); amb = np.zeros((H, W))
    cy = camara(t); P = lambda y: y - cy + PANT_Y
    entorno = ss(3.0, 4.4, t)*(1 - ss(T_FIN - 0.2, T_FIN + 1.0, t))
    mx, my, mb = mar(t); o, dem, _ = _origen(NM, 41); e = ss(0, 1, (t - 3.0 - dem*0.6)/0.9)
    splat(amb, o[:, 0]*(1 - e) + mx*e, P(my)*e + o[:, 1]*(1 - e), mb*0.5*entorno)
    vm = ss(T_PR - 0.6, T_PR + 0.4, t)*(1 - ss(T_FIN - 0.2, T_FIN + 1.0, t))
    if vm > 0.01:
        o2, d2, _ = _origen(len(MONT_P), 44); e2 = ss(0, 1, (t - T_PR + 0.6 - d2*0.5)/0.8)
        splat(amb, o2[:, 0]*(1 - e2) + MONT_P[:, 0]*e2, o2[:, 1]*(1 - e2) + P(MONT_P[:, 1])*e2, MONT_P[:, 2]*vm)
    vn = ss(T_CO - 0.6, T_CO + 0.6, t)*(1 - ss(T_PR + 2.4, T_ES + 0.3, t))
    if vn > 0.01:
        o3, d3, _ = _origen(len(NUBE_P), 45); e3 = ss(0, 1, (t - T_CO + 0.6 - d3*0.5)/0.8)
        splat(amb, o3[:, 0]*(1 - e3) + NUBE_P[:, 0]*e3, o3[:, 1]*(1 - e3) + P(NUBE_P[:, 1])*e3, NUBE_P[:, 2]*vn)
    I = ss(T_EV, T_EV + 0.8, t)*(1 - ss(T_CO, T_CO + 1.2, t))
    if I > 0.01:
        for j in range(12):
            ang = 0.35 + j*0.09; rr = np.arange(80, 1500, 9.0)
            splat(amb, -60 + rr*np.cos(ang), -60 + rr*np.sin(ang), I*0.3*(1 - rr/1500)**1.5*(0.7 + 0.3*np.sin(t*2 + j)))
    # gotas: la grande del inicio (Voronoi) pasa a la gota bien dibujada al achicarse
    k = ss(4.0, 4.8, t)*(1 - ss(T_FIN, T_FIN + 0.6, t))
    if k < 0.999:
        x, y, w, gx, gy, esc, rac = B.gota(t)
        splat(sm, x, P(y), w*1.6*(1 - k)); splat(bg, x, P(y), w*0.9*(1 - k))
    if k > 0.001:
        gx, gy, esc, rac = camino(t)
        vis_o = ss(4.2, 5.2, t)*k
        f = separacion(t)
        for i in range(NO):
            tt = float(np.clip(t - o_d[i], 5.0, T_FIN - 0.05)); ox, oy, _, orac = camino(tt)
            dibujar(sm, bg, ox + o_dx[i]*f, oy + o_dy[i]*f + 7*np.sin(t*1.7 + i*1.3), R_GOTA, orac,
                    0.42*vis_o*visible_otra(t, i), False, t, P, (0.0, 0.0), i*1.7)
        px, py, _, _ = camino(max(t - 0.06, 0)); vel = ((gx - px)/0.06, (gy - py)/0.06)
        mece = 8*np.sin(t*1.9)*(1 - ss(T_EV + 0.3, T_EV + 1.0, t) + ss(T_FIN - 0.8, T_FIN, t))   # se mece en el mar
        dibujar(sm, bg, gx, gy + mece, R_GOTA, rac, 1.15*k, True, t, P, vel)
    if EXTRA: EXTRA(sm, t, P)
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
