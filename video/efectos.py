"""Efectos reutilizables (biblioteca del motor). Cada uno dibuja puntos con la función `splat(buf, x, y, w)` que se
le pase: la de pantalla (sin zoom) o la del mundo (con la cámara). Ver BIBLIOTECA.md para cuándo usar cada uno.

    from efectos import EspiralTiempo, RelojArena, anillo_reloj, agujas, contador, calor, anillo_cambio, aro_3d
"""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
LETRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "letras")
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))

# ---------- viaje en el tiempo: espiral de símbolos y galaxias (ciclo del agua, gancho) ----------
SIMBOLOS_CIENCIA = ["H₂O", "E=mc²", "π", "∞", "Σ", "∫", "√2", "Δt", "λ", "Ω", "10⁹", "∂", "α", "ƒ(t)",
                    "4.000.000.000 AÑOS", "β", "γ", "∇", "e", "θ", "≈", "x²", "1/2", "μ", "H", "O", "Δ", "φ"]

def simbolo(txt, tam=56, seed=0):
    """Un símbolo o palabra como puntos (centrado en 0,0)."""
    f = ImageFont.truetype(os.path.join(LETRAS, "DejaVuSans.ttf"), tam*2)
    bb = f.getbbox(txt); im = Image.new("L", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), txt, font=f, fill=255)
    m = np.asarray(im.resize((im.width//2, im.height//2), Image.LANCZOS), float)/255
    ys, xs = np.nonzero(m > 0.2); r = np.random.default_rng(seed); n = max(int(m.sum()*0.9), 30)
    i = r.choice(len(xs), n, p=m[ys, xs]/m[ys, xs].sum())
    return np.c_[xs[i] - m.shape[1]/2 + r.uniform(-.5, .5, n), ys[i] - m.shape[0]/2 + r.uniform(-.5, .5, n)]

def galaxia(n=500, seed=0, radio=60):
    """Galaxia espiral pequeña de puntos (dos brazos, vista inclinada)."""
    r = np.random.default_rng(seed); brazo = r.integers(0, 2, n); u = r.uniform(0, 1, n)**0.7
    a = brazo*np.pi + u*4.2 + r.normal(0, 0.25, n); rr = u*radio
    return np.c_[rr*np.cos(a), rr*np.sin(a)*0.55]

class EspiralTiempo:
    """Remolino que gira alrededor del protagonista: brazos en espiral y símbolos/galaxias que salen hacia la cámara,
    creciendo y girando. Expresa "pasó muchísimo tiempo". Usar en el gancho, mientras se forma el protagonista."""
    def __init__(self, t0, t1, simbolos=SIMBOLOS_CIENCIA, n=72, brazos=3, prop_galaxias=0.18, seed=71):
        rng = np.random.default_rng(seed)
        self.t0, self.t1, self.n, self.brazos = t0, t1, n, brazos
        self.glifos = [simbolo(s, seed=k) for k, s in enumerate(simbolos)]
        self.galax = [galaxia(seed=k) for k in range(5)]
        self.v_t0 = np.sort(rng.uniform(t0, t1 - 0.9, n))
        self.v_a0 = np.arange(n)*2.39996 + rng.normal(0, 0.2, n)          # ángulo áureo: llenan la pantalla parejo
        self.v_g = np.arange(n) % len(self.glifos); self.v_gal = rng.uniform(size=n) < prop_galaxias
        self.v_rot = rng.uniform(-1, 1, n); self.br_k = np.linspace(0, 1, 260)
    def dibujar(self, buf, t, cx, cy, splat):
        g = ss(self.t0, self.t0 + 0.5, t)*(1 - ss(self.t1 - 0.5, self.t1, t))
        if g < 0.01: return
        giro = -2.2*t; k = self.br_k
        for j in range(self.brazos):                                      # brazos: espiral logarítmica que gira
            a = giro*1.3 + j*2*np.pi/self.brazos + k*5.0; r = 110*np.exp(k*2.3)
            splat(buf, cx + r*np.cos(a), cy + r*np.sin(a)*0.92, 0.6*g*(1 - k)**0.6*(0.6 + 0.4*np.sin(k*40 - t*12)))
        for i in range(self.n):                                           # símbolos y galaxias hacia la cámara
            e = (t - self.v_t0[i])/1.6
            if not 0 < e < 1: continue
            r = 180*np.exp(e*2.1); a = self.v_a0[i] + giro + e*3.0; esc = 0.35 + 1.6*e**1.5
            G = (self.galax[i % len(self.galax)] if self.v_gal[i] else self.glifos[self.v_g[i]])*esc
            c, s = np.cos(self.v_rot[i]*e*2), np.sin(self.v_rot[i]*e*2)
            x = G[:, 0]*c - G[:, 1]*s; y = G[:, 0]*s + G[:, 1]*c
            w = 0.85*g*ss(0.08, 0.3, e)*(1 - ss(0.65, 1, e))
            splat(buf, cx + r*np.cos(a) + x, cy + r*np.sin(a) + y, np.full(len(x), w))

# ---------- relojes ----------
TICK_A = np.linspace(0, 2*np.pi, 60, endpoint=False); TICK_L = np.where(np.arange(60) % 5 == 0, 0.12, 0.05)
def anillo_reloj(buf, cx, cy, r, ang, w, splat):
    """Esfera de reloj: 60 marcas (cada 5, más largas)."""
    k = np.linspace(0, 1, 5)
    a = np.repeat(TICK_A + ang, 5); rr = r*(1 + np.outer(TICK_L, k).ravel())
    splat(buf, cx + rr*np.cos(a), cy + rr*np.sin(a), np.full(len(a), w))

def agujas(buf, cx, cy, R, vueltas, g, splat):
    """Agujas de reloj: 'vueltas' de la aguja corta (la larga gira 12 veces más rápido)."""
    for largo, vel, w in ((0.62, 1.0, 0.75), (0.85, 12.0, 0.5)):
        a = -np.pi/2 + 2*np.pi*vueltas*vel; k = np.linspace(0.08, largo, 40)
        splat(buf, cx + R*k*np.cos(a), cy + R*k*np.sin(a), np.full(40, w*g))

def miles(n): return f"{n:,}".replace(",", ".")
_cache_cont = {}
def contador(buf, texto, y, e, splat, tam=60, x=W/2):
    """Texto que cambia en cada cuadro (años, días...) con el mismo estilo de puntos que los títulos."""
    if e < 0.01: return
    if texto not in _cache_cont:
        from textos import Texto, puntos_de_texto
        _cache_cont[texto] = puntos_de_texto(Texto(texto, 0, 1, tam=tam), seed=len(texto))
    p = _cache_cont[texto]; splat(buf, p[:, 0] + x, p[:, 1] + y, np.full(len(p), 0.8*e))

class RelojArena:
    """Reloj de arena de puntos: se forma, se da vuelta `vueltas` veces (la arena cae por el cuello) y se disuelve
    subiendo (puede convertirse en vapor, humo, polvo). tiempos = (forma, empieza, termina, disuelve)."""
    HB, WB, CUELLO = 135.0, 100.0, 7.0
    def __init__(self, tiempos, centro=(W/2, 610.0), vueltas=3, seed=72):
        rng = np.random.default_rng(seed)
        self.T, self.centro, self.vueltas, self.seed = tiempos, centro, vueltas, seed
        self.borde = self._borde(); self.NS = 900
        self.s_u = np.sort(rng.uniform(0, 1, self.NS)); self.s_x = rng.uniform(-1, 1, self.NS)
        self.chorro = rng.uniform(0, 1, 80)
    def _borde(self, n=90):
        HB, WB, CU = self.HB, self.WB, self.CUELLO; s = np.linspace(0, 1, n); pts = []
        for sg in (-1, 1):
            for lado in (-1, 1): pts.append(np.c_[lado*(CU + (WB - CU)*s**0.8), sg*HB*s])
            x = np.linspace(-WB - 22, WB + 22, 70); pts.append(np.c_[x, np.full(70, sg*(HB + 10))])
            pts.append(np.c_[x, np.full(70, sg*(HB + 16))])
        for lado in (-1, 1): pts.append(np.c_[np.full(80, lado*(WB + 16)), np.linspace(-HB - 10, HB + 10, 80)])
        return np.concatenate(pts)
    def _arena(self, p):
        HB, WB, CU = self.HB, self.WB, self.CUELLO
        s = np.sqrt(self.s_u); arriba = self.s_u < 1 - p; ancho = CU + (WB - CU)*s**0.8 - 6
        y = np.where(arriba, -HB*(s*0.92 + 0.04), HB - (HB*0.96)*(1 - s))
        return np.c_[self.s_x*np.maximum(ancho, 2), y]
    def progreso(self, t):
        """0..vueltas: cuántas vueltas de arena pasaron (para sincronizar un contador)."""
        _, c0, c1, _ = self.T; return self.vueltas*ss(0, 1, (t - c0)/(c1 - c0))**1.0 if t > c0 else 0.0
    def dibujar(self, buf, t, splat):
        from formacion import _origen
        f0, c0, c1, d1 = self.T
        if not f0 < t < d1 + 1.0: return
        dur = (c1 - c0)/self.vueltas; u = np.clip((t - c0)/dur, 0, self.vueltas); k = min(int(u), self.vueltas - 1); fr = u - k
        giro = 0.22                                                       # fracción de la vuelta que dura el volteo
        p = np.clip(fr/(1 - giro), 0, 1); ang = np.pi*ss(1 - giro, 1, fr) if t < c1 else 0.0
        if t >= c1: p = 1.0
        G = np.r_[self._arena(p), self.borde]; w = np.r_[np.full(self.NS, 0.75), np.full(len(self.borde), 0.55)]
        if 0 < p < 1 and t < c1:                                          # chorro por el cuello
            yy = self.chorro*self.HB*(0.9 - 0.4*p)
            G = np.r_[G, np.c_[np.sin(self.chorro*40 + t*30)*1.2, yy]]; w = np.r_[w, np.full(80, 0.7)]
        c, s = np.cos(ang), np.sin(ang); x = G[:, 0]*c - G[:, 1]*s + self.centro[0]; y = G[:, 0]*s + G[:, 1]*c + self.centro[1]
        o, dem, _ = _origen(len(x), self.seed)
        e = ss(0, 1, (t - f0 - dem*0.4)/0.6)                              # se forma
        sal = ss(0, 1, (t - d1 + 0.6 - dem*0.5)/0.9)                      # se disuelve subiendo
        x = o[:, 0]*(1 - e) + x*e + 40*np.sin(dem*20 + t)*sal; y = o[:, 1]*(1 - e) + y*e - 520*sal**1.4
        splat(buf, x, y, w*e*(1 - sal))

# ---------- cambios de estado ----------
_rc = np.random.default_rng(73); CAL_A = _rc.uniform(0, 2*np.pi, 34); CAL_R = _rc.uniform(1.25, 1.9, 34); CAL_F = _rc.uniform(0, 1, 34)
def calor(buf, t, cx, cy, R, g, splat):
    """Líneas de calor que suben ondulando alrededor de un objeto de radio R (se calienta, se agita)."""
    if g < 0.01: return
    k = np.linspace(0, 1, 14)
    for a, r, f in zip(CAL_A, CAL_R, CAL_F):
        tau = (t*1.4 + f) % 1
        x0 = cx + R*r*np.cos(a)*0.9; y0 = cy + R*0.6 - tau*R*2.4
        splat(buf, x0 + 7*np.sin(k*7 + t*9 + a*5), y0 - k*45, np.full(14, 0.8*g*np.sin(np.pi*tau)))

def anillo_cambio(buf, t, cx, cy, t0, dur, splat, abre=True):
    """Anillo que marca un cambio de estado: se abre (se dispersa, se evapora) o se cierra girando (se junta)."""
    p = (t - t0)/dur
    if not 0 < p < 1: return
    a = np.linspace(0, 2*np.pi, 120, endpoint=False)
    if abre: r = 70 + 260*p**0.7; w = 0.9*(1 - p)**1.5
    else: a = a - t*1.5; r = 330 - 250*ss(0, 1, p); w = 0.8*np.sin(np.pi*p)
    splat(buf, cx + r*np.cos(a), cy + r*np.sin(a), np.full(120, w))

# ---------- aro en 3D (remate de "ciclo") ----------
ARO = np.linspace(0, 2*np.pi, 520, endpoint=False)
def aro_3d(buf, cx, cy, R, inclina, giro, cabeza, g, splat, oculta=(205, 265, 25)):
    """Aro en 3D alrededor del protagonista: perspectiva, la parte de atrás pasa por detrás de él (elipse `oculta` =
    semiancho, semialto, desplazamiento vertical), cola de cometa y flecha en la cabeza. Nunca un círculo plano."""
    X = R*np.cos(ARO); Y = R*np.sin(ARO)*np.cos(inclina); Z = R*np.sin(ARO)*np.sin(inclina)
    c, s = np.cos(giro), np.sin(giro); X, Y = X*c - Y*s, X*s + Y*c
    f = 1000/(1000 - Z); x, y = cx + X*f, cy + Y*f
    u = ((cabeza - ARO) % (2*np.pi))/(2*np.pi)
    w = g*0.95*(1 - u)**1.3*f**2*np.where(Z < 0, 0.45, 1.0)
    ax, ay, dy = oculta
    detras = (Z < 0) & (((x - cx)/ax)**2 + ((y - cy - dy)/ay)**2 < 1); w = np.where(detras, 0.0, w)
    for d in (-1.2, 0, 1.2):
        splat(buf, x + d*f*np.cos(ARO), y + d*f*np.sin(ARO), w*(0.6 if d else 1.0))
    i = int(np.argmin(u)); j = (i - 6) % len(ARO)
    if not detras[i]:
        tx, ty = x[i] - x[j], y[i] - y[j]; L = np.hypot(tx, ty) + 1e-6; tx, ty = tx/L, ty/L
        k = np.linspace(0, 1, 22); tam = 30*f[i]
        for lado in (-1, 1):
            splat(buf, x[i] - (tx*tam - lado*ty*tam*0.7)*k, y[i] - (ty*tam + lado*tx*tam*0.7)*k, np.full(22, 1.1*g*f[i]**2))

# ---------- túnel del tiempo con escrituras (muestra: muestras/muestras2.py) ----------
def _linea(p0, p1, paso=2.5):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); n = max(int(np.hypot(*(p1 - p0))/paso), 2)
    return p0 + np.outer(np.linspace(0, 1, n), p1 - p0)
def glifo_maya(v):
    """Número maya: rayas (5) y puntos (1)."""
    P = []
    for b in range(v//5):
        y = 18 - b*16
        for yy in (y - 4, y + 4): P.append(_linea((-30, yy), (30, yy)))
    for d in range(v % 5):
        a = np.linspace(0, 6.28, 24); x0 = (d - (v % 5 - 1)/2)*16; y0 = 18 - (v//5)*16 - 4
        P.append(np.c_[x0 + 5*np.cos(a), y0 + 5*np.sin(a)])
    return np.concatenate(P)
def glifo_cuneiforme(seed):
    """Un signo cuneiforme: 2 a 4 cuñas (cabeza triangular + cola)."""
    r = np.random.default_rng(seed); P = []
    for _ in range(r.integers(2, 5)):
        a = r.choice([0, np.pi/2, np.pi/4]); L = r.uniform(25, 45); h = r.uniform(-18, 18, 2)
        d = np.array([np.cos(a), np.sin(a)]); n = np.array([-d[1], d[0]])
        P += [_linea(h - n*7, h + n*7), _linea(h - n*7, h + d*12), _linea(h + n*7, h + d*12), _linea(h + d*12, h + d*L)]
    return np.concatenate(P)
def glifo_huella():
    """Huella de dinosaurio de tres dedos."""
    P = [_linea((0, 10), (0, -40)), _linea((0, 10), (-24, -32)), _linea((0, 10), (24, -32))]
    a = np.linspace(0, 6.28, 30); P.append(np.c_[12*np.cos(a), 18 + 10*np.sin(a)]); return np.concatenate(P)

def eras_escritura():
    """Épocas hacia atrás en el tiempo, cada una con sus escrituras (sin imágenes)."""
    s = lambda lista: [simbolo(x, tam=48, seed=k) for k, x in enumerate(lista)]
    return [("HOY", s(["0101", "1010", "∞", "0110", "10", "π", "0011", "1"])),
            ("1905", s(["E=mc²", "c", "λ", "ħ", "E=mc²", "Δt", "v", "c²"])),
            ("1687", s(["F=ma", "G", "m₁m₂", "r²", "F=ma", "g", "∫", "dx"])),
            ("300 a. C.", s(["a²+b²=c²", "π", "α", "β", "γ", "Δ", "Ω", "θ"])),
            ("500 a. C.", [glifo_maya(v) for v in (1, 4, 7, 9, 12, 13, 17, 19)]),
            ("3000 a. C.", [glifo_cuneiforme(k) for k in range(8)]),
            ("HACE 66 MILLONES DE AÑOS", [glifo_huella() for _ in range(8)]),
            ("HACE 4.000 MILLONES DE AÑOS", [])]

class TunelTiempo:
    """La cámara viaja hacia atrás por planos de épocas (anillos de escrituras + año) con el protagonista en el
    centro. Úsese para "pasaron miles/millones de años"."""
    def __init__(self, t0, t1, eras=None, centro=(W/2, 960.0), radio=420, sep=1150.0):
        from textos import Texto, puntos_de_texto
        self.t0, self.t1, self.c, self.R, self.sep = t0, t1, centro, radio, sep
        self.eras = eras or eras_escritura()
        self.anios = [puntos_de_texto(Texto(a, 0, 1, tam=70), seed=k) for k, (a, _) in enumerate(self.eras)]
    def dibujar(self, buf, t, splat, D=1500.0, oculta=None):
        """oculta: (semiancho, semialto) del protagonista: lo que pasa por encima de él se atenúa."""
        if not self.t0 - 0.1 < t < self.t1 + 0.6: return
        g = ss(self.t0, self.t0 + 0.5, t)*(1 - ss(self.t1, self.t1 + 0.6, t))
        u = (t - self.t0)/(self.t1 - self.t0); cz = -700 + self.sep*len(self.eras)*0.95*ss(0.04, 0.95, u)**1.15
        cx, cy = self.c
        for k, (_, glifos) in enumerate(self.eras):
            Zr = k*self.sep - cz
            if Zr < -1300 or Zr > 2700: continue
            f = D/max(D + Zr, 60); a = g*ss(2700, 1700, Zr)*(1 - ss(-700, -1300, Zr))
            for j, G in enumerate(glifos):
                ang = j*2*np.pi/len(glifos) + k*0.4 + t*0.25*(-1)**k
                x = (G[:, 0] + self.R*np.cos(ang))*f + cx; y = (G[:, 1] + self.R*np.sin(ang)*1.15)*f + cy; w = np.full(len(G), 0.9*a)
                if oculta is not None: w = w*np.where(((x - cx)/oculta[0])**2 + ((y - cy)/oculta[1])**2 < 1, 0.15, 1.0)
                splat(buf, x, y, w)
            T = self.anios[k]; splat(buf, T[:, 0]*f + cx, (T[:, 1] + 640)*f + cy, np.full(len(T), 1.2*a))
