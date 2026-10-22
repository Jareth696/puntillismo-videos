"""Pergamino (cinta) con el nombre de un personaje, dibujado con puntos: identidad visual de los videos.

Cinta central levemente curva + dos colas detrás con corte en V + pliegues + sombreado de grabado.
El nombre va en mayúsculas con serifa (como las inscripciones de las estatuas).

    from pergamino import pergamino
    P = pergamino("GALILEO GALILEI")      # (n, 3): x, y (centrado en 0,0) y brillo
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FUENTE = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"

def _linea(pts, paso=2.2, b=0.9, jit=0.6, rng=None):
    pts = np.asarray(pts, float); seg = np.hypot(*np.diff(pts, axis=0).T); L = np.r_[0, np.cumsum(seg)]
    s = np.arange(0, L[-1], paso); x = np.interp(s, L, pts[:, 0]); y = np.interp(s, L, pts[:, 1])
    return np.c_[x + rng.normal(0, jit, len(s)), y + rng.normal(0, jit, len(s)), np.full(len(s), b)]

def _texto(texto, tam, rng, dens=0.6):
    s = 3; f = ImageFont.truetype(FUENTE, tam*s); track = int(tam*s*0.18)
    anchos = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else tam*s*0.35 for c in texto]
    total = int(sum(anchos) + track*(len(texto) - 1)) + 8
    im = Image.new("L", (total, int(tam*s*1.4))); d = ImageDraw.Draw(im); x = 4
    for c, a in zip(texto, anchos):
        if c != " ": d.text((x - f.getbbox(c)[0], 0), c, font=f, fill=255)
        x += a + track
    m = np.asarray(im.resize((total//s, im.height//s), Image.LANCZOS), float)/255
    ys, xs = np.nonzero(m > 0.2); w = m[ys, xs]; n = int(w.sum()*dens*3.2)
    i = rng.choice(len(xs), n, p=w/w.sum())
    p = np.c_[xs[i] + rng.uniform(-.5, .5, n), ys[i] + rng.uniform(-.5, .5, n)]
    p -= [m.shape[1]/2, m.shape[0]*0.42]
    return np.c_[p, np.ones(n)], m.shape[1]

def pergamino(texto, tam=42, alto=96, curva=16, seed=0):
    rng = np.random.default_rng(seed)
    T, ancho_txt = _texto(texto, tam, rng)
    a = ancho_txt/2 + 70                                         # medio ancho de la cinta central
    u = np.linspace(-1, 1, 160)
    arriba = np.c_[u*a, -alto/2 + curva*u**2]; abajo = np.c_[u*a, alto/2 + curva*u**2]
    partes = [_linea(arriba, b=0.95, rng=rng), _linea(abajo, b=0.95, rng=rng),
              _linea(arriba + [0, 6], b=0.35, rng=rng)]                        # doble línea arriba (grabado)
    for sgn in (-1, 1):
        xe = sgn*a; ye0, ye1 = -alto/2 + curva, alto/2 + curva
        partes.append(_linea([(xe, ye0), (xe - sgn*6, (ye0 + ye1)/2 - 8), (xe + sgn*2, (ye0 + ye1)/2 + 6), (xe, ye1)], b=0.9, rng=rng))
        # cola detrás: más baja, con corte en V al final
        x0, x1 = sgn*(a - 55), sgn*(a + 120); yt, yb = -alto/2 + curva + 38, alto/2 + curva + 38
        cola = [(x0, yt), (x1, yt + 6), (x1 - sgn*34, (yt + yb)/2 + 3), (x1, yb + 6), (x0, yb)]
        partes.append(_linea([p for p in cola if abs(p[0]) > a - 2] or cola, b=0.75, rng=rng))
        partes.append(_linea([(x1, yt + 6), (x1 - sgn*34, (yt + yb)/2 + 3), (x1, yb + 6)], b=0.75, rng=rng))
        partes.append(_linea([(xe, ye1), (sgn*(a - 30), yb), (sgn*(a + 4), yb)], b=0.7, rng=rng))     # pliegue
        # sombreado de grabado en la cola
        for k in range(10):
            xx = sgn*(a + 8 + k*10)
            if abs(xx) < abs(x1) - 30:
                partes.append(_linea([(xx, yt + 8), (xx - sgn*10, yb - 4)], paso=3.0, b=0.35, rng=rng))
    # relleno muy tenue de la cinta central
    n = int(a*alto*0.05); fx = rng.uniform(-a, a, n); fy = rng.uniform(-alto/2, alto/2, n) + curva*(fx/a)**2
    partes.append(np.c_[fx, fy, np.full(n, 0.12)])
    T[:, 1] += curva*0.5
    return np.concatenate(partes + [T])
