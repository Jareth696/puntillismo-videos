"""Ciclo del agua v7 = v6 + el TIEMPO se ve: viaje en el tiempo en el gancho (espiral de símbolos y galaxias), reloj de arena y contador de años
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
# cada etapa dura lo que hace falta para leer su texto mientras se mira la imagen y la etiqueta de abajo
TX_EV = ("EL SOL LA CALIENTA", "Y SE VUELVE VAPOR"); TX_CO = ("ARRIBA SE ENFRÍA", "Y VUELVE A SER GOTA")
TX_NUBE = ("VIAJA CON LA NUBE",); TX_ES = ("Y EN SEMANAS", "VUELVE AL MAR")
L_EV, L_CO, L_NUBE, L_ES = (E.tiempo_lectura(*TX_EV, extra=1), E.tiempo_lectura(*TX_CO, extra=1),
                            E.tiempo_lectura(*TX_NUBE, extra=1), E.tiempo_lectura(*TX_ES, extra=1))
E.SEGS_AGUA = [L_EV + 0.6, L_CO + L_NUBE + 0.6, 5.0]
E.ESC_AGUA = L_ES + 0.4
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
T_DIAS = (T_CO + 0.4 + L_CO, T_PR + 0.3)                  # reloj de los días en la nube

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

# ---------- viaje en el tiempo (gancho): espiral de símbolos que sale de la gota ----------
from PIL import Image, ImageDraw, ImageFont
SIMBOLOS = ["H₂O", "E=mc²", "π", "∞", "Σ", "∫", "√2", "Δt", "λ", "Ω", "10⁹", "∂", "α", "ƒ(t)", "4.000.000.000 AÑOS",
            "β", "γ", "∇", "e", "θ", "≈", "x²", "1/2", "μ", "H", "O", "Δ", "φ"]
def simbolo(txt, tam=56, seed=0):
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", tam*2)
    bb = f.getbbox(txt); im = Image.new("L", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), txt, font=f, fill=255)
    m = np.asarray(im.resize((im.width//2, im.height//2), Image.LANCZOS), float)/255
    ys, xs = np.nonzero(m > 0.2); r = np.random.default_rng(seed); n = max(int(m.sum()*0.9), 30)
    i = r.choice(len(xs), n, p=m[ys, xs]/m[ys, xs].sum())
    return np.c_[xs[i] - m.shape[1]/2 + r.uniform(-.5, .5, n), ys[i] - m.shape[0]/2 + r.uniform(-.5, .5, n)]
GLIFOS = [simbolo(s_, seed=k) for k, s_ in enumerate(SIMBOLOS)]

def galaxia(n=500, seed=0):
    r = np.random.default_rng(seed); brazo = r.integers(0, 2, n); u = r.uniform(0, 1, n)**0.7
    a = brazo*np.pi + u*4.2 + r.normal(0, 0.25, n); rr = u*60
    return np.c_[rr*np.cos(a), rr*np.sin(a)*0.55]
GALAX = [galaxia(seed=k) for k in range(5)]

T_VIAJE = (0.4, 3.9)                              # mientras se forma la gota y se lee el gancho
NV = 72                                           # símbolos/galaxias que salen en espiral
v_t0 = np.sort(rng.uniform(T_VIAJE[0], T_VIAJE[1] - 0.9, NV)); v_a0 = np.arange(NV)*2.39996 + rng.normal(0, 0.2, NV)   # ángulo áureo: llenan toda la pantalla parejo
v_g = np.arange(NV) % len(GLIFOS); v_gal = rng.uniform(size=NV) < 0.18; v_rot = rng.uniform(-1, 1, NV)
BR = 3; br_k = np.linspace(0, 1, 260)               # brazos del espiral (estelas de puntos)
def viaje(buf, t, P):
    g = ss(T_VIAJE[0], T_VIAJE[0] + 0.5, t)*(1 - ss(T_VIAJE[1] - 0.5, T_VIAJE[1], t))
    if g < 0.01: return
    gx, gy, _, _ = camino(t); cx, cy = gx, P(gy)
    giro = -2.2*t                                                       # todo el remolino gira
    for j in range(BR):                                                 # brazos: espiral logarítmica que gira
        a = giro*1.3 + j*2*np.pi/BR + br_k*5.0; r = 110*np.exp(br_k*2.3)
        zs(buf, cx + r*np.cos(a), cy + r*np.sin(a)*0.92, 0.6*g*(1 - br_k)**0.6*(0.6 + 0.4*np.sin(br_k*40 - t*12)))
    for i in range(NV):                                                 # símbolos y galaxias que salen hacia la cámara
        e = (t - v_t0[i])/1.6
        if not 0 < e < 1: continue
        r = 180*np.exp(e*2.1); a = v_a0[i] + giro + e*3.0
        esc = 0.35 + 1.6*e**1.5
        G = (GALAX[i % len(GALAX)] if v_gal[i] else GLIFOS[v_g[i]])*esc
        c_, s_ = np.cos(v_rot[i]*e*2), np.sin(v_rot[i]*e*2)
        x = G[:, 0]*c_ - G[:, 1]*s_; y = G[:, 0]*s_ + G[:, 1]*c_
        w = 0.85*g*ss(0.08, 0.3, e)*(1 - ss(0.65, 1, e))
        zs(buf, cx + r*np.cos(a) + x, cy + r*np.sin(a) + y, np.full(len(x), w))

TICK_A = np.linspace(0, 2*np.pi, 60, endpoint=False); TICK_L = np.where(np.arange(60) % 5 == 0, 0.12, 0.05)
def anillo_reloj(buf, cx, cy, r, ang, w, splat=raw):
    """Esfera de reloj: 60 marcas (cada 5, más largas)."""
    k = np.linspace(0, 1, 5)
    a = np.repeat(TICK_A + ang, 5); rr = r*(1 + np.outer(TICK_L, k).ravel())
    splat(buf, cx + rr*np.cos(a), cy + rr*np.sin(a), np.full(len(a), w))

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
ARO = np.linspace(0, 2*np.pi, 520, endpoint=False)
def aro_3d(buf, cx, cy, R, inclina, giro, cabeza, g, esc_gota):
    """Aro en 3D alrededor de la gota: perspectiva, la parte de atrás pasa detrás de la gota, cola de cometa y flecha."""
    X = R*np.cos(ARO); Y = R*np.sin(ARO)*np.cos(inclina); Z = R*np.sin(ARO)*np.sin(inclina)
    c, s_ = np.cos(giro), np.sin(giro); X, Y = X*c - Y*s_, X*s_ + Y*c
    f = 1000/(1000 - Z)                                                  # perspectiva
    x, y = cx + X*f, cy + Y*f
    u = ((cabeza - ARO) % (2*np.pi))/(2*np.pi)                           # 0 en la cabeza, crece hacia la cola
    w = g*0.95*(1 - u)**1.3*f**2*np.where(Z < 0, 0.45, 1.0)
    detras = (Z < 0) & (((x - cx)/(205*esc_gota))**2 + ((y - cy - 25*esc_gota)/(265*esc_gota))**2 < 1)
    w = np.where(detras, 0.0, w)
    for d in (-1.2, 0, 1.2):                                             # grosor (más grueso adelante)
        zs(buf, x + d*f*np.cos(ARO), y + d*f*np.sin(ARO), w*(0.6 if d else 1.0))
    i = int(np.argmin(u)); j = (i - 6) % len(ARO)                        # flecha en la cabeza
    if not detras[i]:
        tx, ty = x[i] - x[j], y[i] - y[j]; L = np.hypot(tx, ty) + 1e-6; tx, ty = tx/L, ty/L
        k = np.linspace(0, 1, 22); tam = 30*f[i]
        for lado in (-1, 1):
            zs(buf, x[i] - (tx*tam - lado*ty*tam*0.7)*k, y[i] - (ty*tam + lado*tx*tam*0.7)*k, np.full(22, 1.1*g*f[i]**2))

def ciclo(buf, t, P):
    """Remate: dos aros en 3D giran alrededor de la gota (el ciclo), vistos en ángulo, no planos."""
    g = ss(T_FIN + 0.6, T_FIN + 1.4, t)
    if g < 0.01: return
    gx, gy, esc, _ = camino(t); cy = P(gy)
    aro_3d(buf, gx, cy, 330, 1.18 + 0.1*np.sin(t*0.7), -0.38 + 0.08*np.sin(t*0.5), t*1.7, g, esc)
    aro_3d(buf, gx, cy, 300, 1.28 + 0.08*np.sin(t*0.6 + 1), 0.55 + 0.06*np.sin(t*0.4), -t*1.3 + 2.0, g*0.7, esc)

# ---------- todo junto ----------
_extra6 = C5.EXTRA
def extra(sm, t, P):
    _extra6(sm, t, P)
    viaje(sm, t, P); reloj_arena(sm, t); calor(sm, t, P); anillo_estado(sm, t, P); reloj_dias(sm, t, P); ciclo(sm, t, P)
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
          Texto(TX_EV[0], T_EV - 0.2, T_EV - 0.2 + L_EV, y=230, tam=TT),
          Texto(TX_EV[1], T_EV + 0.4, T_EV - 0.1 + L_EV, y=295, tam=TT),
          Texto(TX_CO[0], T_CO + 0.1, T_CO + 0.1 + L_CO, y=230, tam=TT),
          Texto(TX_CO[1], T_CO + 0.6, T_CO + 0.2 + L_CO, y=295, tam=TT),
          Texto(TX_NUBE[0], T_DIAS[0], T_DIAS[1] - 0.2, y=230, tam=TT),
          Texto("CAE COMO LLUVIA", T_PR + 0.6, T_PR + 0.6 + E.tiempo_lectura("CAE COMO LLUVIA", extra=1), y=230, tam=TT),
          Texto(TX_ES[0], T_ES - 0.1, T_FIN - 0.5, y=230, tam=TT),
          Texto(TX_ES[1], T_ES + 0.4, T_FIN - 0.4, y=295, tam=TT)]
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
