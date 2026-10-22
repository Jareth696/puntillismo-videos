"""Textos en puntillismo sobre un video ya renderizado (1080x1920, B/N).

Las letras se dibujan con una fuente fina, se convierten en puntos, se forman juntando puntos dispersos
y se disuelven flotando. Una etiqueta puede seguir a un objeto secundario del video (p. ej. la Tierra).

Uso como módulo:
    from textos import Texto, componer
    componer("entrada.mp4", "salida.mp4", [Texto("FASES DE LA LUNA", 0.6, 4.6, y=230, tam=44), ...])
"""
import os, subprocess, numpy as np
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

W, H, FPS = 1080, 1920, 24
ESPACIADO = 0.14          # espacio entre letras (proporción del tamaño)
DENSIDAD = 0.9            # puntos por letra (más = trazo más firme)
ANCHO_MAX = 960           # px: una línea más ancha se achica sola
FUENTE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "letras", "Inter-Regular.otf")
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))

@dataclass
class Texto:
    texto: str
    t0: float                 # aparece
    t1: float                 # se va
    x: float = W/2            # centro
    y: float = 1720
    tam: int = 34             # alto de letra en px
    brillo: float = 0.8
    seguir: bool = False      # True: se ubica junto al segundo objeto más grande del video
    dx: float = 0             # desplazamiento respecto del objeto seguido
    dy: float = -60
    pista: list = None        # posiciones (x, y) por cuadro calculadas desde el video original (más confiable)
    anillo: float = 0         # radio de un anillo de puntos alrededor del objeto seguido (0 = sin anillo)

def puntos_de_texto(t: Texto, densidad=None, seed=0):
    """Máscara del texto -> puntos (muestreo por la máscara, sin grumos). Si no entra en ANCHO_MAX, se achica."""
    densidad = DENSIDAD if densidad is None else densidad
    s = 3                                                          # supermuestreo para trazos finos
    f = ImageFont.truetype(FUENTE, t.tam*s)
    track = int(t.tam*s*ESPACIADO)                                  # espaciado entre letras
    anchos = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else t.tam*s*0.35 for c in t.texto]
    total = int(sum(anchos) + track*(len(t.texto)-1)) + 8
    if total/s > ANCHO_MAX and t.tam > 12:
        from dataclasses import replace
        return puntos_de_texto(replace(t, tam=int(t.tam*ANCHO_MAX/(total/s))), densidad, seed)
    im = Image.new("L", (total, int(t.tam*s*1.5))); d = ImageDraw.Draw(im); x = 4
    for c, a in zip(t.texto, anchos):
        if c != " ": d.text((x - f.getbbox(c)[0], 0), c, font=f, fill=255)
        x += a + track
    m = np.asarray(im.resize((total//s, im.height//s), Image.LANCZOS), float)/255
    ys, xs = np.nonzero(m > 0.15); w = m[ys, xs]
    rng = np.random.default_rng(seed); n = max(int(w.sum()*densidad*3), 60)
    i = rng.choice(len(xs), n, p=w/w.sum())
    p = np.c_[xs[i] + rng.uniform(-.5, .5, n), ys[i] + rng.uniform(-.5, .5, n)]
    p -= [m.shape[1]/2, m.shape[0]/2]                               # centrado en (0, 0)
    return p

def leer(path):
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W*H)
        if len(b) < W*H: break
        yield np.frombuffer(b, np.uint8).reshape(H, W).astype(float)/255

def objeto_secundario(g):
    """Centro del segundo objeto más grande (el principal es el más grande), o None."""
    s = g[::4, ::4]; s = ndimage.uniform_filter(s, 5)
    lab, n = ndimage.label(s > 0.04)
    if n < 2: return None
    areas = ndimage.sum(np.ones_like(s), lab, range(1, n+1)); orden = np.argsort(areas)[::-1]
    zona = ndimage.binary_dilation(ndimage.binary_fill_holes(lab == orden[0] + 1), iterations=6)   # el principal y su entorno
    for k in orden[1:] + 1:
        if areas[k-1] >= 6 and not (zona & (lab == k)).any():
            cy, cx = ndimage.center_of_mass(lab == k); return cx*4, cy*4
    return None

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)

# ---------- sello de los títulos (identidad, opción A aprobada) ----------
# Debajo de los títulos de arriba nace una línea de puntos desde un rombo central; un punto guía la recorre; si entra
# una segunda línea, la regla baja deslizándose y se estira; al salir el texto se recoge hacia el rombo.
SELLO_ZONA = 450            # textos con y menor a esto (y que no siguen a un objeto) son "títulos de arriba"
SELLO_SEPARA = 62           # distancia de la regla bajo la última línea
def _linea_h(capa, x0, x1, y, w, paso=4.0):
    if x1 - x0 < 1: return
    x = np.arange(x0, x1, paso); splat(capa, x, np.full(len(x), y), np.full(len(x), w))
def _rombo(capa, cx, cy, r, w):
    a = np.linspace(0, 2*np.pi, 40, endpoint=False); x, y = np.cos(a), np.sin(a); s = np.abs(x) + np.abs(y)
    splat(capa, cx + r*x/s, cy + r*y/s, np.full(40, w)); splat(capa, np.array([cx]), np.array([cy]), np.array([1.6*w]))
_PG = np.random.default_rng(0); _PA = _PG.uniform(0, 2*np.pi, 40); _PR = np.sqrt(_PG.uniform(0, 1, 40))
def _punto(capa, cx, cy, r, w):
    splat(capa, cx + r*_PR*np.cos(_PA), cy + r*_PR*np.sin(_PA), np.full(40, w*0.4))

def sello_titulo(capa, t, titulos):
    """titulos: lista de (Texto, ancho en px). Dibuja la regla bajo el bloque de títulos activo."""
    act = []
    for tx, ancho in titulos:
        p = ss(tx.t0, tx.t0 + 0.5, t)*(1 - ss(tx.t1 - 0.1, tx.t1 + 0.6, t))
        if p > 0.005: act.append((tx.y, p, ancho, tx))
    if not act: return
    act.sort(key=lambda a: a[0])
    y = act[0][0] + SELLO_SEPARA; prev = act[0][0]
    for yy, p, _, _ in act[1:]: y += (yy - prev)*p; prev = yy
    m = max(an*min(1, p*1.5) for _, p, an, _ in act)/2*0.8
    tx0 = min(act, key=lambda a: a[3].t0)[3]
    e = ss(tx0.t0 + 0.2, tx0.t0 + 0.9, t)*max(p for _, p, _, _ in act)
    if e < 0.01: return
    m *= e; cx = W/2
    _linea_h(capa, cx - m, cx - 20*e, y, 0.75*e); _linea_h(capa, cx + 20*e, cx + m, y, 0.75*e)
    _rombo(capa, cx, y, 11*e, e); _punto(capa, cx - m - 10, y, 2.5, e); _punto(capa, cx + m + 10, y, 2.5, e)
    _punto(capa, cx + m*0.92*np.sin(t*2.2), y, 4.5, 2.6*e)                      # punto guía

def a_zona_segura(textos):
    """Los títulos de arriba se escribieron a varias alturas con letra chica: se llevan a la zona segura (debajo de la
    barra de la app) con el espacio de la letra grande. Un título es '2ª línea' si a la vez hay otro más arriba."""
    from dataclasses import replace
    import estilo as E
    arriba = [t for t in textos if not t.seguir and t.y < SELLO_ZONA]
    def mover(t):
        if t not in arriba: return t
        segunda = any(o.y < t.y and o.t0 < t.t1 and t.t0 < o.t1 for o in arriba if o is not t)
        return replace(t, y=E.TITULO_Y2 if segunda else E.TITULO_Y1)
    return [mover(t) for t in textos]

def componer(entrada, salida, textos, crf=15, sello=True):
    textos = a_zona_segura(textos)
    rng = np.random.default_rng(7)
    datos = []
    for k, t in enumerate(textos):
        p = puntos_de_texto(t, seed=k); n = len(p)
        datos.append(dict(p=p, dis=rng.normal(0, 1, (n, 2))*[60, 35], st=rng.uniform(0, 0.35, n),
                          sube=rng.uniform(20, 60, n), pos=None))
    out = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), salida],
                           stdin=subprocess.PIPE)
    titulos = [(tx, float(np.ptp(d["p"][:, 0]))) for tx, d in zip(textos, datos)
               if sello and not tx.seguir and tx.y < SELLO_ZONA]
    for f, g in enumerate(leer(entrada)):
        t = f/FPS; capa = np.zeros((H, W))
        sello_titulo(capa, t, titulos)
        for tx, d in zip(textos, datos):
            if not (tx.t0 - 0.1 < t < tx.t1 + 1.0): continue
            cx, cy = tx.x, tx.y
            if tx.seguir:
                o = (tx.pista[f] if f < len(tx.pista) else None) if tx.pista is not None else objeto_secundario(g)
                if o: d["pos"] = o if d["pos"] is None else (d["pos"][0]*0.8 + o[0]*0.2, d["pos"][1]*0.8 + o[1]*0.2)
                if d["pos"] is None: continue
                cx, cy = d["pos"][0] + tx.dx, d["pos"][1] + tx.dy
                if tx.anillo:                                           # marca: anillo fino de puntos que gira
                    a = np.linspace(0, 2*np.pi, 70, endpoint=False) + t*0.6
                    r = tx.anillo*(1.25 - 0.25*ss(tx.t0, tx.t0 + 0.8, t))
                    e = ss(tx.t0, tx.t0 + 0.8, t)*(1 - ss(tx.t1, tx.t1 + 0.8, t))
                    splat(capa, d["pos"][0] + r*np.cos(a), d["pos"][1] + r*np.sin(a), np.full(70, 0.9*e))
            ent = ss(0, 1, (t - tx.t0 - d["st"])/0.8)                   # se juntan
            sal = ss(0, 1, (t - tx.t1 + 0.2 - d["st"]*0.6)/0.9)          # se disuelven flotando
            q = d["p"] + d["dis"]*(1 - ent)[:, None] + np.c_[d["dis"][:, 0]*0.5, -d["sube"]]*sal[:, None]
            w = tx.brillo*ent*(1 - sal)*1.6
            splat(capa, q[:, 0] + cx, q[:, 1] + cy, w)
        img = np.clip(g + capa, 0, 1)
        out.stdin.write((img*255).astype(np.uint8).tobytes())
    out.stdin.close(); out.wait()
