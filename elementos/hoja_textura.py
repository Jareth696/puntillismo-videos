"""Extrae la textura real de una hoja (nervaduras) de un cuadro de video y la 'despliega' en coordenadas de hoja.

Salida: elementos/hoja_textura.png  — filas = largo de la hoja (abajo base, arriba punta), columnas = ancho
(centro = nervio central). Fuente: Mixkit, video 3737 'Green leaves in detail view' (licencia libre Mixkit).

    python3 hoja_textura.py hd3737.mp4 [segundo]
"""
import sys, subprocess, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

def cuadro(path, t):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", path, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).astype(float)/255

def extraer(path, t=4.0, filas=640, cols=240):
    im = cuadro(path, t); r, g, b = im[..., 0], im[..., 1], im[..., 2]
    verde = ndimage.gaussian_filter(np.clip((g - (r + b)/2)*4, 0, 1), 2) > 0.16
    verde[1450:] = False                                        # abajo está desenfocado y se une con otras hojas
    verde = ndimage.binary_opening(verde, iterations=3)
    lab, n = ndimage.label(verde)
    k = lab[1000, 300] or np.argmax(ndimage.sum(verde, lab, range(1, n+1))) + 1   # la hoja del centro-izquierda
    hoja = ndimage.binary_fill_holes(lab == k)
    ys = np.nonzero(hoja.any(1))[0]; y_punta = ys.min()
    # nitidez por fila: la parte baja está desenfocada; se usa hasta donde hay detalle
    L = 0.3*r + 0.59*g + 0.11*b
    det = ndimage.uniform_filter(np.abs(L - ndimage.gaussian_filter(L, 3))*hoja, (40, 1)).mean(1)
    y_fin = y_punta + int(np.argmax(np.r_[det[y_punta:], 0] < 0.25*det[y_punta:].max())) if det[y_punta:].max() > 0 else ys.max()
    y_fin = min(max(y_fin, y_punta + 600), ys.max() - 10)
    # textura: luz normalizada + nervaduras (pasa-altos) resaltadas
    hp = L - ndimage.gaussian_filter(L, 6)
    tex = np.clip(0.45*(L - np.percentile(L[hoja], 5))/np.ptp(np.percentile(L[hoja], [5, 99])) + 3.5*np.clip(hp, 0, None), 0, 1)
    out = np.zeros((filas, cols))
    for i in range(filas):
        u = 1 - i/(filas - 1)                                   # fila 0 = punta (u=1) ... última = base (u=-1)
        y = int(y_punta + (1 - u)/2*(y_fin - y_punta))
        xs = np.nonzero(hoja[y])[0]
        if len(xs) < 3: continue
        c, w = (xs.min() + xs.max())/2, (xs.max() - xs.min())/2
        x = np.clip((c + np.linspace(-1, 1, cols)*w*0.97).astype(int), 0, 1079)
        out[i] = tex[y, x]
    return out[::-1]                                            # fila 0 = base, última = punta

def extraer_espejo(path, t=4.0, filas=640, cols=240, y0=520, y1=1420, x_nervio=(355, 318), media=300):
    """Más robusto: usa la mitad iluminada de la hoja (nervaduras nítidas) y la refleja a ambos lados del nervio.
    x_nervio: posición x del nervio central en y0 y en y1 (cuadro 1080x1920); media: ancho de la mitad usada."""
    im = cuadro(path, t); r, g, b = im[..., 0], im[..., 1], im[..., 2]
    L = 0.3*r + 0.59*g + 0.11*b
    hp = L - ndimage.gaussian_filter(L, 5)
    zona = L[y0:y1, max(x_nervio[1] - media, 0):x_nervio[0]]
    lo, hi = np.percentile(zona, [3, 99])
    tex = np.clip(0.5*(L - lo)/(hi - lo) + 4.0*np.clip(hp, 0, None), 0, 1)
    out = np.zeros((filas, cols))
    v = np.abs(np.linspace(-1, 1, cols))                        # espejo: los dos lados usan la mitad izquierda
    for i in range(filas):
        f = i/(filas - 1)                                       # 0 = base (abajo, y1) ... 1 = punta (arriba, y0)
        y = int(y1 + (y0 - y1)*f); xm = x_nervio[1] + (x_nervio[0] - x_nervio[1])*f
        x = np.clip((xm - 6 - v*(media - 10)).astype(int), 0, 1079)
        out[i] = tex[y, x]
    return out

if __name__ == "__main__":
    t = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    T = extraer_espejo(sys.argv[1], t)
    Image.fromarray((T*255).astype(np.uint8)).save("hoja_textura.png"); print(T.shape, T.mean().round(3))
