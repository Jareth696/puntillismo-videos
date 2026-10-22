"""Ciclo del agua v12 (final) = v11 + túnel del tiempo con escrituras en el gancho (en lugar del espiral).

La gota se forma con el gancho ("EL AGUA QUE TOMAS / PUDO BEBERLA UN DINOSAURIO") y viaja hacia atrás en el tiempo por
épocas hechas de escrituras (binario, E=mc², F=ma, a²+b²=c², mayas, cuneiforme, huellas de dinosaurio) hasta hace
4.000 millones de años. Después sigue todo igual que la v11, corrido TUNEL segundos.

    python3 ciclo_agua8.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
from dataclasses import replace
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import ciclo_agua7 as C7
from ciclo_agua2 import W, H, FPS, ss, E
import efectos as EF

C7.ESPIRAL.dibujar = lambda *a, **k: None          # el túnel reemplaza al espiral
T_QUIETA = 2.6                                      # la gota ya formada, justo antes de caer
T_TUN = (1.2, 7.4)                                  # el túnel
DESDE = 7.6                                         # desde acá sigue la v11
CORRE = DESDE - T_QUIETA                            # segundos que se corre todo lo demás
DUR = C7.DUR + CORRE
TUNEL = EF.TunelTiempo(*T_TUN)

def splat(buf, x, y, w):
    m = (x > 1) & (x < W-2) & (y > 1) & (y < H-2) & (w > 0); x, y, w = x[m], y[m], w[m]
    ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*W + ix+dx, weights=w*ww, minlength=W*H).reshape(H, W)

def frame(t):
    if t >= DESDE: return C7.frame(t - CORRE)
    base = C7.frame(min(t, T_QUIETA)).astype(float)/255
    capa = np.zeros((H, W)); TUNEL.dibujar(capa, t, splat, oculta=(230, 300))
    return (np.clip(base + capa*1.6, 0, 1)*255).astype(np.uint8)

def textos():
    T = C7.textos(); out = []
    for k, tx in enumerate(T):
        if k < 2: out.append(replace(tx, t1=tx.t1 + 1.6))                # el gancho se queda un poco más
        else: out.append(replace(tx, t0=tx.t0 + CORRE, t1=tx.t1 + CORRE))
    return out

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
