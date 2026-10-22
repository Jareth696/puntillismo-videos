"""Elementos del video de Darwin: retrato (1881, dominio público) y las 5 figuras de la 'marcha' (escultura),
convertidos a puntos con Voronoi una sola vez (caché)."""
import os, sys, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "tesla"))
import stipple

def _cache(nombre, fn):
    p = os.path.join(AQUI, f"cache_{nombre}.npy")
    if os.path.exists(p): return np.load(p, allow_pickle=True)
    v = fn(); np.save(p, v, allow_pickle=True); return v

def retrato(n=42000, ancho=1000, cx=540, top=330):
    """Puntos (x, y, brillo) del retrato en pantalla 1080x1920: barba, cara y pelo brillantes; saco tenue."""
    def hacer():
        im = Image.open(os.path.join(AQUI, "src", "darwin_1881.jpg")).convert("L")
        s = ancho/im.width; im = im.resize((int(im.width*s/2), int(im.height*s/2)), Image.LANCZOS)
        g = np.asarray(im, float)/255
        gy, gx = np.gradient(ndimage.gaussian_filter(g, 1.0)); edge = np.clip(np.hypot(gx, gy)*7, 0, 1)
        d = np.clip((g - 0.10)/0.85, 0, 1)**1.7 + 0.30*edge
        yy = np.arange(g.shape[0])[:, None]/g.shape[0]
        d *= 1 - 0.6*np.clip((yy - 0.62)/0.38, 0, 1)                    # el saco se apaga hacia abajo
        p, _ = stipple.voronoi(d + 1e-6, n, 30, 1)
        b = g[np.clip(p[:, 1].astype(int), 0, g.shape[0]-1), np.clip(p[:, 0].astype(int), 0, g.shape[1]-1)]
        p = p*2; p[:, 0] += cx - ancho/2; p[:, 1] += top
        return np.c_[p, np.clip(0.3 + 0.9*b, 0, 1)]
    return _cache("retrato", hacer)

def figuras(n_total=30000):
    """Las 5 figuras de la escultura, cada una como array (x, y, brillo) en coordenadas locales:
    centradas en x=0, pies en y=0, altura normalizada a 1000 px. Separadas por color (dorado vs pared)."""
    def hacer():
        im = np.asarray(Image.open(os.path.join(AQUI, "src", "marcha.jpg")).convert("RGB"), float)/255
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        mx, mn = im.max(-1), im.min(-1); sat = (mx - mn)/np.maximum(mx, 1e-3)
        pared = np.median(im[50:400, :].reshape(-1, 3), axis=0)          # color de la pared
        dif = np.linalg.norm(ndimage.gaussian_filter(im, (2, 2, 0)) - pared, axis=-1)
        m = (dif > 0.16) | (ndimage.gaussian_filter(sat, 2) > 0.28)
        m[1262:] = False                                              # sin la base de madera
        m = ndimage.binary_opening(m, iterations=2); m = ndimage.binary_closing(m, iterations=3)
        m = ndimage.binary_fill_holes(m)
        cortes = [0, 478, 765, 1040, 1385, im.shape[1]]                # franjas de cada figura
        lab = np.zeros(m.shape, int)
        for k in range(5):
            mk = np.zeros_like(m); mk[:, cortes[k]:cortes[k+1]] = m[:, cortes[k]:cortes[k+1]]
            l2, n2 = ndimage.label(mk)
            if n2: lab[l2 == 1 + int(np.argmax(ndimage.sum(mk, l2, range(1, n2+1))))] = k + 1
        cajas = [(ndimage.find_objects((lab == i).astype(np.int32))[0], i) for i in range(1, 6)]
        L = 0.3*r + 0.59*g + 0.11*b; hp = L - ndimage.gaussian_filter(L, 4)
        out = []
        for (sl, i) in cajas:
            mk = (lab == i)[sl]; Lc = L[sl]; hc = hp[sl]
            d = mk*(0.25 + 0.75*np.clip((Lc - 0.25)/0.6, 0, 1)**1.2 + 2.5*np.clip(np.abs(hc), 0, 0.2))
            borde = mk & ~ndimage.binary_erosion(mk, iterations=2); d = d + 0.8*borde
            nn = int(n_total*mk.sum()/sum((lab == j).sum() for _, j in cajas))
            p, _ = stipple.voronoi(d + 1e-6*mk, max(nn, 800), 30, i)
            bb = Lc[np.clip(p[:, 1].astype(int), 0, mk.shape[0]-1), np.clip(p[:, 0].astype(int), 0, mk.shape[1]-1)]
            p[:, 0] -= mk.shape[1]/2; p[:, 1] -= mk.shape[0]
            alto_px = 1262 - sl[0].start                                # altura real en la foto
            out.append((np.c_[p, np.clip(0.35 + 0.8*bb, 0, 1)], alto_px, (sl[1].start + sl[1].stop)/2))
        return np.array(out, dtype=object)
    return _cache("figuras", hacer)
