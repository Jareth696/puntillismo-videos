"""Galileo (puntillismo B/N, 1080x1920). Plantilla de estados (como Darwin) con estados ANIMADOS (órbitas).

Geocéntrico (mito, gancho; el plano se inclina) -> estatua con pergamino -> telescopio que se aleja y de su boca sale
lo que vio -> zoom a Júpiter y sus 4 lunas -> heliocéntrico -> estatua (condena y remate).
Fuentes: estatua (Uffizi, foto aportada por el usuario, recorte GrabCut), Sol (NASA SDO), Júpiter (dibujado),
telescopio (Pixabay, aportado por el usuario).

    python3 galileo.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
from PIL import Image
from scipy import ndimage
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "video")); sys.path.insert(0, os.path.join(AQUI, "..", "tesla"))
import estilo as E
import stipple
from formacion import converger, textos_gancho
from pergamino import pergamino
from camara import acercar, aplicar

W, H, FPS = 1080, 1920, 24
N = 35000; CX, CY = 540.0, 960.0
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))
rng = np.random.default_rng(9)

def cache(nombre, fn):
    p = os.path.join(AQUI, f"cache_{nombre}.npy")
    if os.path.exists(p): return np.load(p)
    v = fn(); np.save(p, v); return v

# ---------- elementos (Voronoi, centrados en 0,0) ----------
def disco_imagen(archivo, n, seed, gamma=1.3, umbral=0.06):
    """Puntos de un cuerpo redondo a partir de una foto (radio normalizado a 1)."""
    g = np.asarray(Image.open(os.path.join(AQUI, "src", archivo)).convert("L"), float)/255
    m = ndimage.binary_fill_holes(ndimage.gaussian_filter(g, 3) > umbral)
    lab, k = ndimage.label(m); m = lab == (np.argmax(ndimage.sum(m, lab, range(1, k+1))) + 1)
    ys, xs = np.nonzero(m); cy, cx = ys.mean(), xs.mean(); r = max(xs.max() - cx, cx - xs.min(), ys.max() - cy, cy - ys.min())
    r = int(r) + 4; gm = np.pad(g*m, r)                               # margen: el recorte nunca sale de la imagen
    cy, cx = int(cy) + r, int(cx) + r
    G = Image.fromarray((gm[cy - r:cy + r, cx - r:cx + r]*255).astype(np.uint8)).resize((400, 400), Image.LANCZOS)
    G = np.asarray(G, float)/255
    gy, gx = np.gradient(ndimage.gaussian_filter(G, 1)); edge = np.clip(np.hypot(gx, gy)*6, 0, 1)
    d = np.clip(G/np.percentile(G[G > 0.02], 99), 0, 1)**gamma + 0.3*edge + 1e-6*(G > 0.01)
    p, _ = stipple.voronoi(d, n, 30, seed)
    b = G[np.clip(p[:, 1].astype(int), 0, 399), np.clip(p[:, 0].astype(int), 0, 399)]
    return np.c_[(p - 200)/200, np.clip(0.3 + 0.9*b/np.percentile(b, 95), 0, 1)]

SOL = cache("sol", lambda: disco_imagen("sol_sdo.jpg", 12000, 1, gamma=1.0))
def jupiter_dibujado(n=21000):
    """Júpiter completo: bandas, Gran Mancha Roja y oscurecimiento del borde (dibujado, radio 1)."""
    yy, xx = (np.mgrid[0:400, 0:400] + 0.5)/200 - 1; rr = np.hypot(xx, yy); m = rr < 1
    bandas = 0.62 + 0.25*np.sin(yy*17 + 0.6*np.sin(xx*3)) + 0.1*np.sin(yy*41 + xx*2)
    mancha = np.exp(-(((xx + 0.25)/0.2)**2 + ((yy - 0.38)/0.1)**2))
    G = m*np.clip(bandas - 0.35*mancha + 0.25*np.exp(-(((xx + 0.25)/0.27)**2 + ((yy - 0.38)/0.14)**2))*(1 - mancha), 0, 1)
    G *= np.sqrt(np.clip(1 - rr**2, 0, 1))**0.5
    d = G**1.3 + 0.5*(np.abs(rr - 0.985) < 0.015) + 1e-6*m
    p, _ = stipple.voronoi(d, n, 30, 2)
    b = G[np.clip(p[:, 1].astype(int), 0, 399), np.clip(p[:, 0].astype(int), 0, 399)]
    return np.c_[(p - 200)/200, np.clip(0.35 + 0.8*b, 0, 1)]
JUP = cache("jupiter", jupiter_dibujado)

def estatua(n=24000):
    g = np.asarray(Image.open(os.path.join(AQUI, "src", "estatua.jpg")).convert("L"), float)/255
    m = np.load(os.path.join(AQUI, "mask_estatua.npy"))
    ys, xs = np.nonzero(m); sub = slice(ys.min(), ys.max()), slice(xs.min(), xs.max())
    G = g[sub]*m[sub]; M = m[sub]
    G = np.asarray(Image.fromarray((G*255).astype(np.uint8)).resize((G.shape[1]//2, G.shape[0]//2), Image.LANCZOS), float)/255
    M = np.asarray(Image.fromarray((M*255).astype(np.uint8)).resize((G.shape[1], G.shape[0])), float)/255 > 0.5
    gy, gx = np.gradient(ndimage.gaussian_filter(G, 1)); edge = np.clip(np.hypot(gx, gy)*6, 0, 1)
    d = M*(np.clip((G - 0.2)/0.7, 0, 1)**1.3 + 0.5*edge) + 1e-6*M
    esc = 1320/G.shape[0]; fila = np.arange(G.shape[0])[:, None]
    d = d*(1 + 2.2*ss(G.shape[0]/2 + (560 - 1010)/esc, G.shape[0]/2 + (500 - 1010)/esc, fila))   # más puntos en la cabeza (el cierre se acerca al rostro)
    p, _ = stipple.voronoi(d, n, 30, 3)
    b = G[np.clip(p[:, 1].astype(int), 0, G.shape[0]-1), np.clip(p[:, 0].astype(int), 0, G.shape[1]-1)]
    return np.c_[(p[:, 0] - G.shape[1]/2)*esc, (p[:, 1] - G.shape[0]/2)*esc, np.clip(0.25 + 0.9*b, 0, 1)]
ESTATUA = cache("estatua_rostro", lambda: estatua(26000))

def disco_liso(n, seed, borde=0.35):
    """Cuerpo simple (planeta/luna): relleno + borde marcado."""
    r = np.random.default_rng(seed); a = r.uniform(0, 2*np.pi, n); rr = np.sqrt(r.uniform(0, 1, n))
    rr = np.where(r.uniform(size=n) < borde, 0.97 + r.normal(0, 0.02, n), rr)
    luz = np.clip(0.45 + 0.55*np.cos(a - 2.4)*rr, 0.25, 1)               # iluminado de un lado
    return np.c_[rr*np.cos(a), rr*np.sin(a), luz]

def anillo(n, R, achata=1.0, b=0.3):
    a = np.linspace(0, 2*np.pi, n, endpoint=False) + rng.uniform(0, 0.01, n)
    return np.c_[R*np.cos(a), R*achata*np.sin(a), np.full(n, b)]

def telescopio(n=12000):
    """Telescopio (foto con fondo transparente aportada por el usuario). Sin la caja de monedas. Alto normalizado a 1."""
    im = np.asarray(Image.open(os.path.join(AQUI, "src", "telescopio.webp")).convert("RGBA"), float)/255
    im = im[:1560]; g = im[..., :3].mean(2); a = im[..., 3]*np.clip((1560 - np.arange(1560))/140, 0, 1)[:, None]
    G = np.asarray(Image.fromarray((g*255).astype(np.uint8)).resize((g.shape[1]//2, g.shape[0]//2), Image.LANCZOS), float)/255
    A = np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((G.shape[1], G.shape[0]), Image.LANCZOS), float)/255
    gy, gx = np.gradient(ndimage.gaussian_filter(G*A, 1)); edge = np.clip(np.hypot(gx, gy)*6, 0, 1)
    d = A*(np.clip((G - 0.12)/0.8, 0, 1)**1.2 + 0.6*edge) + 1e-6*(A > 0.5)
    p, _ = stipple.voronoi(d, n, 30, 4)
    iy, ix = np.clip(p[:, 1].astype(int), 0, G.shape[0]-1), np.clip(p[:, 0].astype(int), 0, G.shape[1]-1)
    b = G[iy, ix]*A[iy, ix]
    return np.c_[(p[:, 0] - G.shape[1]/2)/G.shape[0], (p[:, 1] - G.shape[0]/2)/G.shape[0], np.clip(0.3 + 0.9*b, 0, 1)]
TELESC = cache("telescopio", telescopio)
TEL_LENTE = np.array([(1600 - 1847/2)/1560, (300 - 780)/1560])      # boca del telescopio (coordenadas locales)
TEL_OCULAR = np.array([(300 - 1847/2)/1560, (990 - 780)/1560])

# ---------- estados: listas de cuerpos (puntos locales, escala, órbita) ----------
class Cuerpo:
    def __init__(self, P, escala, R=0.0, periodo=1.0, fase=0.0, achata=1.0, centro=(CX, CY), oculto_por=None, brillo=1.0, plano=False):
        self.P, self.esc, self.R, self.per, self.fase, self.ach = P, escala, R, periodo, fase, achata
        self.centro, self.oculto_por, self.brillo, self.plano = centro, oculto_por, brillo, plano
    def pos(self, t, inc=1.0):
        """inc: inclinación de la vista del plano orbital (1 = desde arriba, menos = más de costado)."""
        a = self.fase + 2*np.pi*t/self.per
        cx = self.centro[0] + self.R*np.cos(a); cy = self.centro[1] + self.R*self.ach*inc*np.sin(a)
        x = cx + self.P[:, 0]*self.esc; y = cy + self.P[:, 1]*self.esc*(inc if self.plano else 1); b = self.P[:, 2]*self.brillo
        if self.oculto_por is not None and np.sin(a) < 0 and abs(cx - self.centro[0]) < self.oculto_por:
            b = b*0.0                                                    # pasa detrás del planeta
        return np.c_[x, y, b], (cx, cy)

def completar(Q):
    if len(Q) >= N: return Q[:N]
    return np.r_[Q, Q[rng.integers(0, len(Q), N - len(Q))]]

def estado(cuerpos, inc=lambda t: 1.0, cam=None):
    def pos(t):
        k = inc(t); Q = np.concatenate([c.pos(t, k)[0] for c in cuerpos])
        if cam is not None: Q = camara(Q, *cam(t))
        return completar(Q)
    return pos

def camara(Q, z, cx, cy):
    Q = Q.copy(); Q[:, 0] = (Q[:, 0] - cx)*z + CX; Q[:, 1] = (Q[:, 1] - cy)*z + CY; return Q

def cam_ancla(k, z0, z1, ancla, s0, s1):
    """Cámara entre dos vistas: zoom logarítmico y un punto 'ancla' que viaja suave en pantalla (sin derivas)."""
    z = z0*(z1/z0)**k; s = np.asarray(s0, float)*(1 - k) + np.asarray(s1, float)*k
    c = np.asarray(ancla, float) - (s - [CX, CY])/z
    return z, c[0], c[1]

# guion
T_GEO_GIRA = (5.2, 8.6)                     # el plano geocéntrico se inclina (otra vista del mismo plano)
TRANS = [(9.4, 2.2), (15.0, 2.0), (24.6, 0.001), (31.4, 2.4), (40.8, 2.2)]
DUR = 50.6
T_EST1 = TRANS[0][0] + TRANS[0][1]; T_TEL = TRANS[1][0] + TRANS[1][1]; T_HELIO = TRANS[3][0] + TRANS[3][1]; T_EST2 = TRANS[4][0] + TRANS[4][1]
T_ALEJA = (T_TEL + 0.8, T_TEL + 2.6)        # el telescopio se aleja: aparece el cielo
T_SALE = (T_TEL + 2.0, T_TEL + 4.0)         # de la boca del telescopio sale lo que vio
T_ZOOM = (T_TEL + 5.8, TRANS[2][0])         # zoom a Júpiter

TIERRA_P = disco_liso(2600, 11, 0.3)
GEO = estado([Cuerpo(TIERRA_P, 70),                                                       # la Tierra en el centro
              Cuerpo(anillo(1600, 400, b=0.25), 1, plano=True), Cuerpo(anillo(1100, 240, b=0.2), 1, plano=True),
              Cuerpo(SOL, 95, R=400, periodo=7.0, fase=-0.6),                            # el Sol gira alrededor
              Cuerpo(disco_liso(900, 12), 22, R=240, periodo=4.2, fase=2.0)],           # un planeta
             inc=lambda t: 1 - 0.55*ss(*T_GEO_GIRA, t))
# heliocéntrico: los 5 planetas que se ven a simple vista (+ Júpiter con sus 4 lunas, guiño a lo que vio Galileo)
HELIO_T = Cuerpo(TIERRA_P, 30, R=290, periodo=9.0, fase=0.8, brillo=1.35)
INC_HELIO = lambda t: 1 - 0.5*ss(T_HELIO + 1.6, T_HELIO + 6.0, t)
ORBITAS = [(165, 3.6, 2.6, 9, 13), (225, 5.8, 4.4, 15, 15), (360, 14.0, 5.6, 12, 17), (470, 30.0, 3.4, 26, 18)]   # R, periodo, fase, tamaño, seed
HELIO_J = Cuerpo(JUP[np.random.default_rng(7).choice(len(JUP), 1600, replace=False)], 26, R=470, periodo=30.0, fase=3.4)
HELIO = estado([Cuerpo(SOL, 110)]
               + [Cuerpo(anillo(int(R*3.2), R, b=0.2), 1, plano=True) for R in (165, 225, 290, 360, 470)]
               + [Cuerpo(disco_liso(600, sd), tam, R=R, periodo=p, fase=f) for R, p, f, tam, sd in ORBITAS[:3]]
               + [HELIO_T, HELIO_J], inc=INC_HELIO)
class LunaDeJupiter(Cuerpo):
    """Lunitas que siguen a Júpiter en su órbita (en el modelo heliocéntrico)."""
    def __init__(self, k): super().__init__(disco_liso(120, 40 + k), 3.0, R=[38, 46, 55, 64][k], periodo=[1.6, 3.2, 6.4, 13][k], fase=k*1.7, achata=0.25)
    def pos(self, t, inc=1.0):
        self.centro = HELIO_J.pos(t, inc)[1]; return super().pos(t, inc)
HELIO_LUNAS = [LunaDeJupiter(k) for k in range(4)]
_helio_base = HELIO
def HELIO(t):
    Q = _helio_base(t); L = np.concatenate([c.pos(t, INC_HELIO(t))[0] for c in HELIO_LUNAS])
    Q[-len(L):] = L; return Q

# estatua + pergamino con el nombre (tapa el recorte de los pies)
PERG_Y = 1430                                        # sobre la zona que tapa Reels
def estatua_con_nombre():
    S = ESTATUA.copy(); S[:, 0] += CX; S[:, 1] += 1160         # más abajo: la cabeza no choca con los títulos
    S = S[S[:, 1] < PERG_Y - 30]                                        # los pies quedan detrás de la cinta
    P = pergamino("GALILEO GALILEI", seed=2); P[:, 0] += CX; P[:, 1] += PERG_Y
    return np.r_[S, P], len(P)                                         # el pergamino al final
EST_P, N_PERG = estatua_con_nombre()
ROSTRO = (585.0, 590.0)
def est(t0, t1, z1, destino):
    """Estatua mientras se leen los textos: la cámara se sigue acercando al rostro; el pergamino queda fijo."""
    def pos(t):
        Q = EST_P.copy(); S = Q[:-N_PERG]
        z = acercar(t, t0, t1, ROSTRO, destino, z1); S[:, 0], S[:, 1] = aplicar(S[:, 0], S[:, 1], *z)
        S[:, 2] *= z[0]**0.9                                               # de cerca los puntos se separan: más brillo
        S[:, 2] *= 1 - ss(PERG_Y - 110, PERG_Y - 50, S[:, 1])                 # el cuerpo pasa por detrás de la cinta
        return completar(Q)
    return pos

# telescopio -> lo que vio (Júpiter y sus lunas) -> zoom a Júpiter: un mismo plano, distintas vistas
ANG = np.radians(30)
def rotar(P, ang):
    c, s = np.cos(ang), np.sin(ang); return np.c_[P[:, 0]*c + P[:, 1]*s, -P[:, 0]*s + P[:, 1]*c]
TEL_ESC = 780
J_W, J_R = np.array([660.0, 640.0]), 60.0                            # Júpiter en el mundo (vista amplia)
_dir = rotar((TEL_LENTE - TEL_OCULAR)[None], ANG)[0]; _dir /= np.hypot(*_dir)
TEL_C = J_W - _dir*500 - rotar(TEL_LENTE[None], ANG)[0]*TEL_ESC      # el telescopio apunta a Júpiter
LENTE_W = TEL_C + rotar(TEL_LENTE[None], ANG)[0]*TEL_ESC
TEL_W = np.c_[rotar(TELESC[:, :2], ANG)*TEL_ESC + TEL_C, TELESC[:, 2]*1.7]
JUP_S = JUP[np.random.default_rng(5).choice(len(JUP), 17000, replace=False)]
f = J_R/210
GRUPO_J = [Cuerpo(JUP_S, J_R, centro=tuple(J_W))] + \
          [Cuerpo(disco_liso(420, 20 + k), 13*f, R=R*f, periodo=p, fase=ph, achata=0.12, oculto_por=225*f, centro=tuple(J_W), brillo=1.6)
           for k, (R, p, ph) in enumerate(((300, 8.0, 4.71), (365, 14.0, 2.29), (435, 26.0, 2.33), (505, 56.0, 3.6)))]
_r = np.random.default_rng(6); N_J = sum(len(c.P) for c in GRUPO_J)
SALE_D = _r.uniform(0, 1, N_J); SALE_CURVA = _r.normal(0, 1, N_J)*40
Z_CERCA, Z_JUP = 1.7, 210/J_R
def cam_tel(t):
    if t < T_ZOOM[0]:
        k = ss(*T_ALEJA, t); a = TEL_C + [40, -60]
        return cam_ancla(k, Z_CERCA, 1.0, a, [CX, CY], (a - [CX, CY]) + [CX, CY])
    k = ss(*T_ZOOM, t); return cam_ancla(k, 1.0, Z_JUP, J_W, J_W, [CX, CY])
def telescopio_y_jupiter(t):
    Jq = np.concatenate([c.pos(t)[0] for c in GRUPO_J])
    e = ss(0, 1, (t - T_SALE[0] - SALE_D*(T_SALE[1] - T_SALE[0] - 0.7))/0.7)          # cada punto sale de la boca
    d = Jq[:, :2] - LENTE_W; perp = np.c_[-d[:, 1], d[:, 0]]/np.maximum(np.hypot(*d.T), 1)[:, None]
    Jq[:, :2] = LENTE_W + d*e[:, None] + perp*(np.sin(np.pi*e)*SALE_CURVA)[:, None]
    Jq[:, 2] *= ss(0, 0.2, e)
    z = cam_tel(t)
    Jq[:len(JUP_S), 2] *= 0.3 + 0.7*np.clip((z[0] - 1)/(Z_JUP - 1), 0, 1)   # de lejos Júpiter no se satura
    Q = np.r_[TEL_W, Jq]
    return completar(camara(Q, *z))
def pista_jupiter():
    return [tuple(camara(J_W[None], *cam_tel(f/FPS))[0]) if T_SALE[1] - 0.6 < f/FPS < T_ZOOM[0] + 0.4 else None for f in range(int(DUR*FPS))]

ESTADOS = [GEO, est(T_EST1 - 0.6, TRANS[1][0] + 0.6, 1.35, (560, 700)), telescopio_y_jupiter, telescopio_y_jupiter, HELIO,
           est(T_EST2 - 0.4, DUR - 0.6, 2.3, (540, 760))]
# emparejamiento por Hilbert (al momento en que cada estado se ve completo). El estado 3 es el mismo que el 2
# (cambio instantáneo e invisible) solo para reordenar los puntos con Júpiter ya grande: así la salida al
# heliocéntrico es ordenada.
T_REF = [0.0] + [t0 + d for t0, d in TRANS]; T_REF[2] = T_SALE[1] + 0.5; T_REF[3] = TRANS[2][0] + 0.5
ORDEN = [stipple.hilbert_order(ESTADOS[k](T_REF[k])[:, :2]) for k in range(len(ESTADOS))]
DEM = rng.uniform(0, 1, N)**1.2; fase = rng.uniform(0, 6.28, N); dis = rng.normal(0, 1, (N, 2))*[80, 60]

def posiciones(t):
    Q = ESTADOS[0](t)[ORDEN[0]]; x, y, b = Q[:, 0].copy(), Q[:, 1].copy(), Q[:, 2].copy()
    x, y, b = converger(x, y, b, t, seed=5)
    for k, (t0, d) in enumerate(TRANS):
        if t <= t0: break
        Q = ESTADOS[k + 1](t)[ORDEN[k + 1]]
        e = ss(0, 1, (t - t0 - DEM*d*0.5)/(d*0.5)); rem = np.sin(np.pi*e)[:, None]*dis
        x = x*(1 - e) + Q[:, 0]*e + rem[:, 0]; y = y*(1 - e) + Q[:, 1]*e + rem[:, 1]; b = b*(1 - e) + Q[:, 2]*e
    return x + 0.7*np.sin(t*1.3 + fase), y + 0.7*np.cos(t*1.1 + fase), b

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)
def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

big = rng.uniform(size=N) < 0.2
st_x, st_y, st_b, st_p = rng.uniform(0, W, 220), rng.uniform(0, H, 220), rng.uniform(.1, .5, 220)**2, rng.uniform(0, 6.28, 220)
def frame(t):
    sm = np.zeros((H, W)); bg = np.zeros((H, W))
    x, y, b = posiciones(t); w = b*(0.92 + 0.08*np.sin(t*4 + fase))*1.9
    splat(sm, x[~big], y[~big], w[~big]); splat(bg, x[big], y[big], w[big])
    cielo = 1 - ss(TRANS[0][0], TRANS[0][0] + 1, t) + ss(*T_ALEJA, t) - ss(TRANS[4][0], TRANS[4][0] + 1, t)   # estrellas en el cielo
    splat(sm, st_x, st_y, st_b*(0.6 + 0.4*np.sin(t*1.5 + st_p))*3*np.clip(cielo, 0, 1)*ss(0, 2, t))
    img = (sm + 2.2*blur(bg))*min(1, (DUR - t)/E.FUNDIDO_FINAL)
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

def pista_tierra():
    """Posición en pantalla de la Tierra en el modelo heliocéntrico (para su etiqueta)."""
    return [HELIO_T.pos(f/FPS, INC_HELIO(f/FPS))[1] if T_HELIO - 0.6 < f/FPS < TRANS[4][0] else None for f in range(int(DUR*FPS))]

def textos():
    from textos import Texto
    T = textos_gancho("¿EL SOL GIRA", "ALREDEDOR DE LA TIERRA?")
    L1, L2, TT = 230, 295, E.TAM_TITULO
    T += [Texto("DURANTE MÁS DE 1.400 AÑOS", 5.2, 9.3, y=L1, tam=TT),
          Texto("SE CREYÓ QUE SÍ", 5.8, 9.4, y=L2, tam=TT),
          Texto("TIERRA", 6.0, 9.2, y=1090, tam=36, brillo=0.8),
          Texto("HASTA QUE EN 1610", 11.0, 14.8, y=150, tam=TT),
          Texto("GALILEO HIZO ALGO SIMPLE", 11.6, 14.9, y=215, tam=TT),
          Texto("APUNTÓ UN TELESCOPIO", T_TEL - 0.4, T_SALE[0] + 0.4, y=L1, tam=TT),
          Texto("AL CIELO", T_TEL + 0.2, T_SALE[0] + 0.5, y=L2, tam=TT),
          Texto("Y VIO ALGO QUE", T_SALE[0] + 1.0, T_ZOOM[0] + 0.2, y=L1, tam=TT),
          Texto("NADIE HABÍA VISTO", T_SALE[0] + 1.6, T_ZOOM[0] + 0.3, y=L2, tam=TT),
          Texto("JÚPITER", T_SALE[1] - 0.4, T_ZOOM[0] + 0.3, tam=36, seguir=True, dx=0, dy=-80, brillo=0.8, pista=pista_jupiter()),
          Texto("4 LUNAS GIRANDO", TRANS[2][0] + 0.2, 27.8, y=L1, tam=TT),
          Texto("ALREDEDOR DE JÚPITER", TRANS[2][0] + 0.8, 27.9, y=L2, tam=TT),
          Texto("ENTONCES NO TODO GIRA", 28.3, 31.5, y=L1, tam=TT),
          Texto("ALREDEDOR DE LA TIERRA", 28.9, 31.6, y=L2, tam=TT),
          Texto("LA TIERRA GIRA", T_HELIO - 0.4, 37.0, y=L1, tam=TT),
          Texto("ALREDEDOR DEL SOL", T_HELIO + 0.2, 37.1, y=L2, tam=TT),
          Texto("TIERRA", T_HELIO, TRANS[4][0] - 0.2, tam=36, seguir=True, dx=0, dy=-62, brillo=0.8, pista=pista_tierra()),
          Texto("COPÉRNICO LO PROPUSO", 37.4, 40.9, y=L1, tam=TT),
          Texto("GALILEO DIO LAS PRUEBAS", 38.0, 41.0, y=L2, tam=TT),
          Texto("EN 1633 LO CONDENARON", T_EST2 - 0.4, 45.6, y=150, tam=TT),
          Texto("POR DEFENDERLO", T_EST2 + 0.2, 45.7, y=215, tam=TT),
          Texto("MIRÓ AL CIELO", 46.1, DUR - 1.3, y=150, tam=E.TAM_CIERRE),
          Texto("Y NOS CAMBIÓ DE LUGAR", 46.7, DUR - 1.2, y=210, tam=E.TAM_CIERRE)]
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
