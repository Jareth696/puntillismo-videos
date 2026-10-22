"""Ciclo del agua v6 = v5 + rótulos de contexto (NUBE, MONTAÑA) + zoom a la montaña cuando cae la gota
y alejamiento mientras baja hasta el mar.

    python3 ciclo_agua6.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import ciclo_agua5 as C5
from ciclo_agua2 import W, H, FPS, ss, E, camino, camara, PANT_Y, T_CO, T_PR, T_ES, T_FIN, DUR
import ciclo_agua2 as B

T_TOCA = T_PR + 2.1                               # la gota toca la montaña
Z_IN0, Z_IN1 = T_TOCA, T_TOCA + 0.9              # acercamiento DESPUÉS de que aterriza
Z_OUT0, Z_OUT1 = T_ES + 0.3, T_ES + 2.0          # alejamiento mientras baja al mar
Z_MAX = 1.75
ZOOM = [1.0, 540.0, 960.0, 540.0, 960.0]          # z, centro origen (x, y), centro destino (x, y)

def zoom(t):
    return 1 + (Z_MAX - 1)*ss(Z_IN0, Z_IN1, t)*(1 - ss(Z_OUT0, Z_OUT1, t))

_splat = C5.splat
def zsplat(buf, x, y, w):
    z, cx, cy, tx, ty = ZOOM
    if z > 1.0001: x = tx + (x - cx)*z; y = ty + (y - cy)*z
    _splat(buf, x, y, w)
C5.splat = zsplat                                  # todo lo que dibuja la v5 pasa por el zoom (el indicador no)

from ciclo_agua2 import LADERA
T_AGUA = T_ES + 0.1 + 1.6                          # aprox. cuando entra al mar
def impactos(sm, t, P):
    """Salpicón al tocar la montaña y ondas en el agua al volver al mar."""
    p = (t - T_TOCA)/0.7
    if 0 < p < 1:
        a = np.linspace(np.pi*1.05, np.pi*1.95, 26); r = 20 + 90*p
        x = 790 + r*np.cos(a); y = -560 + r*np.sin(a)*0.8 + 160*p*p
        zsplat(sm, x, P(y), np.full(26, 0.9*(1 - p)))
    for k in range(3):
        p = (t - T_AGUA - 0.35*k)/1.6
        if 0 < p < 1:
            a = np.linspace(0, 2*np.pi, 90, endpoint=False); r = 30 + 170*p
            zsplat(sm, 460 + r*np.cos(a), P(28 + 0.22*r*np.sin(a)), np.full(90, 0.75*(1 - p)**1.3))
C5.EXTRA = impactos

def frame(t):
    z = zoom(t)
    gx, gy, _, _ = camino(t); sy = gy - camara(t) + PANT_Y
    k = (z - 1)/(Z_MAX - 1)
    ZOOM[:] = [z, gx, sy, gx + (560 - gx)*k, sy + (900 - sy)*k]   # la gota se acerca al centro al hacer zoom
    return C5.frame(t)

def textos():
    from textos import Texto
    T = B.textos()
    T.append(Texto("NUBE", T_CO + 0.8, T_PR + 0.6, y=700, tam=E.TAM_ETIQUETA, brillo=0.7))
    T.append(Texto("MONTAÑA", Z_IN1 - 0.3, Z_OUT0 + 0.4, y=470, tam=E.TAM_ETIQUETA, brillo=0.7))
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
