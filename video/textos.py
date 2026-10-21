"""Textos en puntillismo sobre un video ya renderizado (1080x1920, B/N).

Las letras se dibujan con una fuente fina, se convierten en puntos, se forman juntando puntos dispersos
y se disuelven flotando. Una etiqueta puede seguir a un objeto secundario del video (p. ej. la Tierra).

Uso como módulo:
    from textos import Texto, componer
    componer("entrada.mp4", "salida.mp4", [Texto("FASES DE LA LUNA", 0.6, 4.6, y=230, tam=44), ...])
"""
import subprocess, numpy as np
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

W, H, FPS = 1080, 1920, 24
FUENTE = "/usr/share/fonts/opentype/inter/Inter-ExtraLight.otf"
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

def puntos_de_texto(t: Texto, densidad=0.55, seed=0):
    """Máscara del texto con espaciado amplio -> puntos (muestreo por la máscara, sin grumos)."""
    s = 3                                                          # supermuestreo para trazos finos
    f = ImageFont.truetype(FUENTE, t.tam*s)
    track = int(t.tam*s*0.32)                                      # espaciado entre letras
    anchos = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else t.tam*s*0.35 for c in t.texto]
    total = int(sum(anchos) + track*(len(t.texto)-1)) + 8
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

def componer(entrada, salida, textos, crf=15):
    rng = np.random.default_rng(7)
    datos = []
    for k, t in enumerate(textos):
        p = puntos_de_texto(t, seed=k); n = len(p)
        datos.append(dict(p=p, dis=rng.normal(0, 1, (n, 2))*[60, 35], st=rng.uniform(0, 0.35, n),
                          sube=rng.uniform(20, 60, n), pos=None))
    out = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), salida],
                           stdin=subprocess.PIPE)
    for f, g in enumerate(leer(entrada)):
        t = f/FPS; capa = np.zeros((H, W))
        for tx, d in zip(textos, datos):
            if not (tx.t0 - 0.1 < t < tx.t1 + 1.0): continue
            cx, cy = tx.x, tx.y
            if tx.seguir:
                o = (tx.pista[f] if f < len(tx.pista) else None) if tx.pista is not None else objeto_secundario(g)
                if o: d["pos"] = o if d["pos"] is None else (d["pos"][0]*0.8 + o[0]*0.2, d["pos"][1]*0.8 + o[1]*0.2)
                if d["pos"] is None: continue
                cx, cy = d["pos"][0] + tx.dx, d["pos"][1] + tx.dy
            ent = ss(0, 1, (t - tx.t0 - d["st"])/0.8)                   # se juntan
            sal = ss(0, 1, (t - tx.t1 + 0.2 - d["st"]*0.6)/0.9)          # se disuelven flotando
            q = d["p"] + d["dis"]*(1 - ent)[:, None] + np.c_[d["dis"][:, 0]*0.5, -d["sube"]]*sal[:, None]
            w = tx.brillo*ent*(1 - sal)*1.6
            splat(capa, q[:, 0] + cx, q[:, 1] + cy, w)
        img = np.clip(g + capa, 0, 1)
        out.stdin.write((img*255).astype(np.uint8).tobytes())
    out.stdin.close(); out.wait()
