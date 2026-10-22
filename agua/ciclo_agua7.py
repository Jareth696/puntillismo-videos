"""Ciclo del agua v7 = v6 + el TIEMPO se ve: túnel del tiempo en el gancho, reloj de arena y contador de años
mientras la gota espera en el mar (las olas en cámara rápida), cambios de estado marcados (calor que la agita y la
abre en vapor / anillo que se cierra al volver a ser gota), reloj con los días que viaja en la nube y un círculo
de "ciclo" en el remate.

    python3 ciclo_agua7.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(AQUI, "..", "video"))
import estilo as E
MAR_EXTRA = 4.2                                    # segundos de más en el mar (el reloj de arena)
E.ACCION_INICIO = E.ACCION_INICIO + MAR_EXTRA
E.SEG_AGUA = 5.0                                   # etapas un poco más largas: el viaje toma su tiempo
import ciclo_agua6 as C6
import ciclo_agua5 as C5
import ciclo_agua2 as B
from ciclo_agua2 import W, H, FPS, ss, camino, T_EV, T_CO, T_PR, T_ES, T_FIN, DUR
from formacion import _origen
from textos import Texto, puntos_de_texto

rng = np.random.default_rng(71)
raw = B.splat                                      # pantalla (sin zoom): reloj de arena, contadores
zs = C6.zsplat                                     # mundo (con el zoom de la cámara): lo pegado a la gota

# ---------- tiempos ----------
T_RA = (5.3, 6.0, 9.6, T_EV + 0.2)                 # reloj de arena: se forma, 3 vueltas, se disuelve en vapor
VUELTAS = 3
T_CALOR = (T_EV - 0.4, T_EV + 1.4)                 # la gota se agita antes de abrirse
T_ABRE = T_EV + 1.0                                # anillo que se abre: líquido -> vapor
T_CIERRA = (T_CO + 0.5, T_CO + 1.9)                # anillo que se cierra: vapor -> gota
T_DIAS = (T_CO + 2.3, T_PR + 0.3)                  # reloj de los días en la nube

# ---------- las olas en cámara rápida mientras pasan los años ----------
_mar = C5.mar
def mar_rapido(t): return _mar(t + 11*ss(T_RA[1], T_RA[2], t))
C5.mar = mar_rapido

# ---------- contador en puntos (mismo estilo que los textos) ----------
_cache = {}
def contador(buf, texto, y, e, tam=E.TAM_TITULO):
    if e < 0.01: return
    if texto not in _cache: _cache[texto] = puntos_de_texto(Texto(texto, 0, 1, tam=tam), seed=len(texto))
    p = _cache[texto]; raw(buf, p[:, 0] + W/2, p[:, 1] + y, np.full(len(p), 0.8*e))

def miles(n): return f"{n:,}".replace(",", ".")

# ---------- túnel del tiempo (gancho): anillos de marcas de reloj que se abren desde la gota ----------
TICK_A = np.linspace(0, 2*np.pi, 60, endpoint=False); TICK_L = np.where(np.arange(60) % 5 == 0, 0.12, 0.05)
def anillo_reloj(buf, cx, cy, r, ang, w, splat=raw):
    k = np.linspace(0, 1, 5)
    a = np.repeat(TICK_A + ang, 5); rr = r*(1 + np.outer(TICK_L, k).ravel())
    splat(buf, cx + rr*np.cos(a), cy + rr*np.sin(a), np.full(len(a), w))

def tunel(buf, t, P):
    g = ss(0.5, 1.0, t)*(1 - ss(2.5, 3.3, t))
    if g < 0.01: return
    gx, gy, _, _ = camino(t)
    for k in range(8):
        a = t - (0.4 + 0.38*k)
        if 0 < a < 2.2:
            r = 150 + 380*a**1.5
            anillo_reloj(buf, gx, P(gy), r, (0.35 if k % 2 else -0.35)*a, g*0.95*ss(0, 0.25, a)*(1 - r/1150)**0.8, zs)

# ---------- reloj de arena ----------
HB, WB, CUELLO = 135.0, 100.0, 7.0
def borde(n=90):
    s = np.linspace(0, 1, n); pts = []
    for sg in (-1, 1):                                                  # bulbo de arriba (-1) y de abajo (+1)
        for lado in (-1, 1):
            pts.append(np.c_[lado*(CUELLO + (WB - CUELLO)*s**0.8), sg*HB*s])
        x = np.linspace(-WB - 22, WB + 22, 70); pts.append(np.c_[x, np.full(70, sg*(HB + 10))])   # tapas
        pts.append(np.c_[x, np.full(70, sg*(HB + 16))])
    for lado in (-1, 1):                                                # columnas
        pts.append(np.c_[np.full(80, lado*(WB + 16)), np.linspace(-HB - 10, HB + 10, 80)])
    return np.concatenate(pts)
RA_B = borde(); NS = 900
s_u = np.sort(rng.uniform(0, 1, NS)); s_x = rng.uniform(-1, 1, NS)
def arena(p):
    """Granos: los de u < 1-p siguen arriba (junto al cuello), el resto ya cayó (montón abajo)."""
    s = np.sqrt(s_u); arriba = s_u < 1 - p
    ancho = CUELLO + (WB - CUELLO)*s**0.8 - 6
    y = np.where(arriba, -HB*(s*0.92 + 0.04), HB*(1.0 - (1 - s)*0.92) - 4)
    y = np.where(arriba, y, HB - (HB*0.96)*(1 - s))
    x = s_x*np.maximum(ancho, 2)
    return np.c_[x, y]
CHORRO = rng.uniform(0, 1, 80)

def reloj_arena(buf, t):
    f0, c0, c1, d1 = T_RA
    if not f0 < t < d1 + 1.0: return
    dur = (c1 - c0)/VUELTAS; u = np.clip((t - c0)/dur, 0, VUELTAS); k = min(int(u), VUELTAS - 1); fr = u - k
    giro = 0.22                                                          # fracción de la vuelta que dura el volteo
    p = np.clip(fr/(1 - giro), 0, 1); ang = np.pi*ss(1 - giro, 1, fr) if t < c1 else 0.0
    if t >= c1: p = 1.0
    G = np.r_[arena(p), RA_B]; w = np.r_[np.full(NS, 0.75), np.full(len(RA_B), 0.55)]
    if 0 < p < 1 and t < c1:                                            # chorro por el cuello
        yy = CHORRO*HB*(0.9 - 0.4*p); G = np.r_[G, np.c_[np.sin(CHORRO*40 + t*30)*1.2, yy]]; w = np.r_[w, np.full(80, 0.7)]
    c, s_ = np.cos(ang), np.sin(ang); x = G[:, 0]*c - G[:, 1]*s_; y = G[:, 0]*s_ + G[:, 1]*c
    cx, cy = W/2, 610.0
    x, y = x + cx, y + cy
    o, dem, _ = _origen(len(x), 72)
    e = ss(0, 1, (t - f0 - dem*0.4)/0.6)                                # se forma
    sal = ss(0, 1, (t - d1 + 0.6 - dem*0.5)/0.9)                        # se disuelve subiendo (vapor)
    x = o[:, 0]*(1 - e) + x*e + 40*np.sin(dem*20 + t)*sal; y = o[:, 1]*(1 - e) + y*e - 520*sal**1.4
    raw(buf, x, y, w*e*(1 - sal))

# ---------- cambios de estado ----------
CAL_A = rng.uniform(0, 2*np.pi, 34); CAL_R = rng.uniform(1.25, 1.9, 34); CAL_F = rng.uniform(0, 1, 34)
def calor(buf, t, P):
    """Líneas de calor que suben ondulando alrededor de la gota, cada vez más rápido."""
    g = ss(T_CALOR[0], T_CALOR[0] + 0.5, t)*(1 - ss(T_CALOR[1] - 0.6, T_CALOR[1], t))
    if g < 0.01: return
    gx, gy, _, _ = camino(t); R = C5.R_GOTA
    k = np.linspace(0, 1, 14)
    for a, r, f in zip(CAL_A, CAL_R, CAL_F):
        tau = (t*1.4 + f) % 1
        x0 = gx + R*r*np.cos(a)*0.9; y0 = gy + R*0.6 - tau*R*2.4
        yy = y0 - k*45; xx = x0 + 7*np.sin(k*7 + t*9 + a*5)
        zs(buf, xx, P(yy), np.full(14, 0.8*g*np.sin(np.pi*tau)))

def anillo_estado(buf, t, P):
    p = (t - T_ABRE)/0.9                                                # se abre: líquido -> vapor
    if 0 < p < 1:
        gx, gy, _, _ = camino(t); a = np.linspace(0, 2*np.pi, 120, endpoint=False); r = 70 + 260*p**0.7
        zs(buf, gx + r*np.cos(a), P(gy + r*np.sin(a)), np.full(120, 0.9*(1 - p)**1.5))
    p = (t - T_CIERRA[0])/(T_CIERRA[1] - T_CIERRA[0])                   # se cierra: vapor -> gota
    if 0 < p < 1:
        gx, gy, _, _ = camino(t); a = np.linspace(0, 2*np.pi, 120, endpoint=False) - t*1.5; r = 330 - 250*ss(0, 1, p)
        zs(buf, gx + r*np.cos(a), P(gy + r*np.sin(a)), np.full(120, 0.8*np.sin(np.pi*p)))

def reloj_dias(buf, t, P):
    t0, t1 = T_DIAS; g = ss(t0, t0 + 0.6, t)*(1 - ss(t1 - 0.5, t1, t))
    if g < 0.01: return
    gx, gy, _, _ = camino(t); cy = P(gy); R = 205
    anillo_reloj(buf, gx, cy, R, 0, 0.5*g, zs)
    u = ss(t0 + 0.3, t1 - 0.6, t)*9                                     # 9 vueltas de la aguja = 9 días
    for largo, vel, w in ((0.62, 1.0, 0.75), (0.85, 12.0, 0.5)):
        a = -np.pi/2 + 2*np.pi*u*vel; k = np.linspace(0.08, largo, 40)
        zs(buf, gx + R*k*np.cos(a), cy + R*k*np.sin(a), np.full(40, w*g))

# ---------- remate: círculo de "ciclo" alrededor de la gota ----------
def ciclo(buf, t, P):
    g = ss(T_FIN + 0.9, T_FIN + 1.6, t)
    if g < 0.01: return
    gx, gy, _, _ = camino(t); cy = P(gy); R = 270
    a0 = t*1.4; a = a0 + np.linspace(0, 2*np.pi*0.8*g, 240)
    zs(buf, gx + R*np.cos(a), cy + R*np.sin(a), np.full(240, 0.7))
    tip = a[-1]; d = np.array([np.cos(tip + np.pi/2), np.sin(tip + np.pi/2)])     # punta de flecha
    px, py = gx + R*np.cos(tip), cy + R*np.sin(tip); k = np.linspace(0, 1, 18)
    for lado in (-1, 1):
        n = np.array([np.cos(tip), np.sin(tip)])*lado
        zs(buf, px - (d[0]*22 - n[0]*16)*k, py - (d[1]*22 - n[1]*16)*k, np.full(18, 0.8*g))

# ---------- todo junto ----------
_extra6 = C5.EXTRA
def extra(sm, t, P):
    _extra6(sm, t, P)
    tunel(sm, t, P); reloj_arena(sm, t); calor(sm, t, P); anillo_estado(sm, t, P); reloj_dias(sm, t, P); ciclo(sm, t, P)
    # contadores (en cámara rápida)
    _, c0, c1, d1 = T_RA
    if c0 - 0.4 < t < d1:
        anos = int(round(3000*ss(0, 1, (t - c0)/(c1 - c0))**1.0/10)*10)
        contador(sm, f"{miles(anos)} AÑOS", 295, ss(c0 - 0.4, c0, t)*(1 - ss(d1 - 0.5, d1, t)))
    t0, t1 = T_DIAS
    if t0 < t < t1:
        dia = 1 + int(ss(t0 + 0.3, t1 - 0.6, t)*8.999)
        contador(sm, f"DÍA {dia}", 295, ss(t0, t0 + 0.4, t)*(1 - ss(t1 - 0.4, t1, t)))
C5.EXTRA = extra

def textos():
    T = C6.textos()
    TT = E.TAM_TITULO
    T += [Texto("EN EL MAR PUEDE ESPERAR", T_RA[1] - 0.6, T_RA[3] - 0.4, y=230, tam=TT),
          Texto("EL SOL LA CALIENTA", T_EV - 0.2, T_EV + 2.4, y=230, tam=TT),
          Texto("Y SE VUELVE VAPOR", T_EV + 0.4, T_EV + 2.5, y=295, tam=TT),
          Texto("ARRIBA SE ENFRÍA", T_CO, T_CO + 2.0, y=230, tam=TT),
          Texto("Y VUELVE A SER GOTA", T_CO + 0.5, T_CO + 2.1, y=295, tam=TT),
          Texto("VIAJA CON LA NUBE", T_DIAS[0], T_DIAS[1] - 0.2, y=230, tam=TT),
          Texto("CAE COMO LLUVIA", T_PR + 0.6, T_PR + 3.4, y=230, tam=TT),
          Texto("Y EN SEMANAS", T_ES, T_FIN + 0.2, y=230, tam=TT),
          Texto("VUELVE AL MAR", T_ES + 0.5, T_FIN + 0.3, y=295, tam=TT)]
    return T

frame = C6.frame
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
