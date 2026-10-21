"""La hoja en el viento: plano fijo, la hoja grande en el centro; el vuelo lo cuentan el viento de puntos
y los cambios de ángulo (de frente, de canto, de espaldas). Al final se posa sobre un suelo que se forma.

    python3 hoja_viento.py salida.mp4
"""
import os, sys, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
import hoja_bn5 as B                                   # hoja dibujada aprobada (geometría, normales, tonos)
import estilo as E
from formacion import aplicar_crecimiento, textos_gancho

W, H, FPS = 1080, 1920, 24
ss = B.ss
rng = np.random.default_rng(21)

# ---------- hoja grande ----------
ESC = 3.4                                              # la hoja de la v5 agrandada para plano cercano
LOC = B.LOC*ESC; NRM = B.NRM; NL = B.NL
CX, CY = 540.0, 860.0                                  # centro de la hoja en pantalla
LUZ = np.array([0.45, -0.6, 0.65]); LUZ /= np.linalg.norm(LUZ)   # x derecha, y abajo, z hacia el espectador
start = np.c_[rng.uniform(-150, W + 150, NL), rng.uniform(-200, H + 200, NL)]
delay = rng.uniform(0, 1, NL)**1.2
big = rng.uniform(size=NL) < np.where(B.lkind > 0, 0.5, 0.25)
tw = rng.uniform(0, 6.28, NL)

def Rx(a): c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def Ry(a): c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def Rz(a): c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

# ---------- guion ----------
T_FORMA, T_VIENTO, T_CALMA, T_SUELO, DUR = E.GANCHO_FORMADO, 4.2, 16.8, 17.2, 22.0

# claves de ángulo (t, giro en el plano, vuelco sobre el largo, inclinación)
CLAVES = np.array([
    [0.0,  -0.55, 0.00, 0.00],
    [4.0,  -0.55, 0.10, 0.05],
    [6.0,  -0.35, 0.45, -0.15],
    [7.6,  -0.20, 1.45, 0.10],      # de canto: una línea fina
    [9.0,  -0.45, 2.60, 0.25],      # de espaldas
    [10.4, -0.70, 3.40, 0.00],
    [11.6, -0.50, 2*np.pi + 0.15, -0.20],   # vuelta completa: de nuevo de frente
    [13.0,  0.40, 2*np.pi + 0.35, 0.30],    # gira sobre sí misma con la ráfaga
    [14.4,  1.30, 2*np.pi + 0.80, -0.10],
    [15.8,  0.90, 2*np.pi + 0.25, 0.15],
    [16.8,  0.25, 2*np.pi + 0.10, 0.05],
    [22.0,  0.15, 2*np.pi + 0.00, 0.00],
])
def angulos(t):
    a = [np.interp(t, CLAVES[:, 0], CLAVES[:, k]) for k in (1, 2, 3)]
    # suavizado entre claves con un leve vaivén propio del vuelo
    vv = ss(T_VIENTO - 1, T_VIENTO + 1, t)*(1 - ss(T_CALMA, T_SUELO + 1, t))
    return a[0] + 0.06*vv*np.sin(t*2.1), a[1] + 0.08*vv*np.sin(t*3.3), a[2] + 0.07*vv*np.sin(t*1.7)

def pose(t):
    giro, vuelco, incl = angulos(t)
    acuesta = ss(T_SUELO, T_SUELO + 2.6, t)                      # al posarse queda acostada (vista en perspectiva)
    R = Rz(giro) @ Rx(-1.15*acuesta) @ Ry(incl) @ Rx(vuelco)
    vv = ss(T_VIENTO - 1, T_VIENTO + 1, t)*(1 - ss(T_CALMA, T_SUELO, t))
    cx = CX + 40*vv*np.sin(t*0.9) - 30*vv*np.sin(t*2.3)
    cy = CY + 35*vv*np.sin(t*1.3 + 1) + (1215 - CY)*ss(T_SUELO, T_SUELO + 2.8, t)
    return R, cx, cy

# ---------- viento ----------
NV = 750
v_y0 = rng.uniform(-100, H + 100, NV); v_ph = rng.uniform(0, 1, NV)
v_cap = rng.choice([0, 1, 2], NV, p=[0.45, 0.35, 0.2])           # lejos / medio / cerca
v_vel = np.array([700, 1150, 1800])[v_cap]*rng.uniform(0.8, 1.2, NV)
v_len = np.array([8, 14, 22])[v_cap]; v_b = np.array([0.55, 0.9, 1.3])[v_cap]
v_ond = rng.uniform(0, 6.28, NV)
def intensidad(t):
    return ss(T_VIENTO - 0.6, T_VIENTO + 1.2, t)*(1 - ss(T_CALMA - 0.5, T_SUELO + 0.8, t))*(0.75 + 0.25*np.sin(t*1.1)**2 + 0.35*np.exp(-((t - 13.6)/1.0)**2))

def viento(sm, bg, t, cx, cy):
    I = intensidad(t)
    if I < 0.02: return
    ciclo = (W + 500)/v_vel; tau = (t/ciclo + v_ph) % 1
    x = W + 250 - tau*(W + 500)
    y = v_y0 + 30*np.sin(x*0.004 + v_ond + t*0.8)
    # el aire rodea la hoja: se aparta arriba y abajo cerca de ella, y se enrosca detrás
    dx, dy = x - cx, y - cy; r2 = (dx/1.6)**2 + dy**2
    empuje = 230**2/(r2 + 230**2)
    y = y + np.sign(dy + 1e-6)*170*empuje*np.exp(-(np.maximum(dx, 0)/400)**2)
    detras = (dx < 0)*np.exp(-r2/600**2)
    y = y + 60*detras*np.sin(dx*0.018 + t*4)
    for j in range(22):
        m = j < v_len
        xs = x + j*5.5*(v_vel/1150); w = v_b*I*np.clip(1 - j/v_len, 0, 1)**1.3*m
        B_ = (v_cap == 2)
        E_ = ~B_
        splat(sm, xs[E_], y[E_], w[E_]); splat(bg, xs[B_], y[B_], w[B_]*0.6)

# ---------- suelo y gotas (final) ----------
NS = 7000
s_x = rng.uniform(0, W, NS); s_y = 1255 + rng.uniform(0, 1, NS)**1.7*260
s_b = 0.5*np.clip(1 - (s_y - 1255)/280, 0.1, 1)*rng.uniform(0.5, 1, NS); s_d = rng.uniform(0, 1, NS)
ND = 160; d_x = rng.uniform(0, W, ND); d_ly = 1265 + rng.uniform(0, 1, ND)**1.5*240
d_T = rng.uniform(0.8, 1.2, ND); d_on = T_SUELO + 2.2 + rng.uniform(0, 1.8, ND); d_off = rng.uniform(0, 1, ND)

def suelo(sm, t):
    a = ss(T_SUELO - 0.3, T_SUELO + 1.6, t - s_d*0.9)
    if a.max() > 0: splat(sm, s_x, s_y, s_b*a)
    act = t >= d_on
    if act.any():
        tau = (t - d_on + d_off) % d_T; cae = d_T*0.6; f = act & (tau < cae)
        yy = -60 + (d_ly + 60)*(tau/cae)
        for j in range(6): splat(sm, d_x, yy - j*14, np.where(f, 0.9*(1 - j/6), 0))
        p = np.clip((tau - cae)/(d_T - cae)/0.55, 0, 1); sp = act & (tau >= cae) & (p < 1)
        for ang in np.linspace(0, 2*np.pi, 12, endpoint=False):
            r = 3 + 30*p; splat(sm, d_x + r*np.cos(ang), d_ly + 0.3*r*np.sin(ang), np.where(sp, 0.8*(1 - p), 0))

# ---------- render ----------
def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)

def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W))
    R, cx, cy = pose(t)
    viento(sm, bg, t, cx, cy)
    suelo(sm, t)
    p = LOC @ R.T; n = NRM @ R.T
    persp = 1/(1 - p[:, 2]*0.0007)
    sx = cx + p[:, 0]*persp; sy = cy + p[:, 1]*persp
    nd = n @ LUZ; frente = n[:, 2] > 0
    luz = np.clip(0.28 + 0.72*np.abs(nd)**0.8, 0, 1)*np.where(frente, 1.0, 0.7)
    bright = luz*(0.55 + 0.45*B.ltone)
    bright = np.where(B.lkind > 0, np.minimum(1, bright*1.15 + 0.2), bright)
    w = bright*(0.94 + 0.06*np.sin(t*5 + tw))*1.25
    px, py, w = aplicar_crecimiento(sx, sy, w, t, cx, cy)          # regla de inicio: nace desde un punto
    splat(sm, px[~big], py[~big], w[~big]); splat(bg, px[big], py[big], w[big])
    img = (sm + 2.2*B.blur(bg))*min(1, (DUR - t)/E.FUNDIDO_FINAL)
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

def textos():
    return textos_gancho("EL VIAJE", "DE UNA HOJA")

def fb(f): return frame(f/FPS).tobytes()
if __name__ == "__main__":
    from multiprocessing import Pool
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else int(DUR*FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "15", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(fb, range(n), chunksize=2): p.stdin.write(b)
    p.stdin.close(); p.wait()
    if len(sys.argv) > 3:                                        # con textos: python3 hoja_viento.py sin.mp4 0 final.mp4
        from textos import componer
        componer(out, sys.argv[3], textos())
