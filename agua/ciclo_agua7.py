"""Ciclo del agua v7 = v6 + el TIEMPO se ve: viaje en el tiempo en el gancho (espiral de símbolos y galaxias), reloj de arena y contador de años
mientras la gota espera en el mar (las olas en cámara rápida), cambios de estado marcados (calor que la agita y la
abre en vapor / anillo que se cierra al volver a ser gota), reloj con los días que viaja en la nube y un círculo
de "ciclo" en el remate.

    python3 ciclo_agua7.py sin_textos.mp4 [n_cuadros|0] [con_textos.mp4]
"""
import os, sys, subprocess, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(AQUI, "..", "video"))
import estilo as E
MAR_EXTRA = 4.2                                    # segundos de más en el mar (el reloj de arena)
E.ACCION_INICIO = E.ACCION_INICIO + MAR_EXTRA
# cada etapa dura lo que hace falta para leer su texto mientras se mira la imagen y la etiqueta de abajo
TX_EV = ("EL SOL LA CALIENTA", "Y SE VUELVE VAPOR"); TX_CO = ("ARRIBA SE ENFRÍA", "Y VUELVE A SER GOTA")
TX_NUBE = ("VIAJA CON LA NUBE",); TX_ES = ("Y EN SEMANAS", "VUELVE AL MAR")
L_EV, L_CO, L_NUBE, L_ES = (E.tiempo_lectura(*TX_EV, extra=1), E.tiempo_lectura(*TX_CO, extra=1),
                            E.tiempo_lectura(*TX_NUBE, extra=1), E.tiempo_lectura(*TX_ES, extra=1))
E.SEGS_AGUA = [L_EV + 0.6, L_CO + L_NUBE + 0.6, 5.0]
E.ESC_AGUA = L_ES + 0.4
import ciclo_agua6 as C6
import ciclo_agua5 as C5
import ciclo_agua2 as B
from ciclo_agua2 import W, H, FPS, ss, camino, T_EV, T_CO, T_PR, T_ES, T_FIN, DUR
from formacion import _origen
from textos import Texto, puntos_de_texto

rng = np.random.default_rng(71)
raw = B.splat                                      # pantalla (sin zoom): reloj de arena, contadores
zs = C6.zsplat                                     # mundo (con el zoom de la cámara): lo pegado a la gota

# ---------- tiempos ----------
T_RA = (5.3, 6.0, 9.6, T_EV + 0.2)                 # reloj de arena: se forma, 3 vueltas, se disuelve en vapor
VUELTAS = 3
T_CALOR = (T_EV - 0.4, T_EV + 1.4)                 # la gota se agita antes de abrirse
T_ABRE = T_EV + 1.0                                # anillo que se abre: líquido -> vapor
T_CIERRA = (T_CO + 0.5, T_CO + 1.9)                # anillo que se cierra: vapor -> gota
T_DIAS = (T_CO + 0.4 + L_CO, T_PR + 0.3)                  # reloj de los días en la nube

# ---------- las olas en cámara rápida mientras pasan los años ----------
_mar = C5.mar
def mar_rapido(t): return _mar(t + 11*ss(T_RA[1], T_RA[2], t))
C5.mar = mar_rapido

# ---------- efectos de la biblioteca (video/efectos.py) ----------
import efectos as EF
ESPIRAL = EF.EspiralTiempo(0.4, 3.9)              # viaje en el tiempo mientras se forma la gota y se lee el gancho
RELOJ = EF.RelojArena(T_RA, centro=(W/2, 680.0), vueltas=VUELTAS)       # 3 vueltas = 3.000 años

def extra(sm, t, P):
    _extra6(sm, t, P)
    gx, gy, esc, _ = camino(t); cx, cy = gx, P(gy)
    ESPIRAL.dibujar(sm, t, cx, cy, zs)
    RELOJ.dibujar(sm, t, raw)
    EF.calor(sm, t, cx, cy, C5.R_GOTA, ss(T_CALOR[0], T_CALOR[0] + 0.5, t)*(1 - ss(T_CALOR[1] - 0.6, T_CALOR[1], t)), zs)
    EF.anillo_cambio(sm, t, cx, cy, T_ABRE, 0.9, zs, abre=True)                       # líquido -> vapor
    EF.anillo_cambio(sm, t, cx, cy, T_CIERRA[0], T_CIERRA[1] - T_CIERRA[0], zs, abre=False)   # vapor -> gota
    t0, t1 = T_DIAS; g = ss(t0, t0 + 0.6, t)*(1 - ss(t1 - 0.5, t1, t))
    if g > 0.01:                                                       # reloj de los días en la nube
        EF.anillo_reloj(sm, cx, cy, 205, 0, 0.5*g, zs); EF.agujas(sm, cx, cy, 205, ss(t0 + 0.3, t1 - 0.6, t)*9, g, zs)
    g = ss(T_FIN + 0.6, T_FIN + 1.4, t)
    if g > 0.01:                                                       # remate: dos aros 3D alrededor de la gota
        oc = (205*esc, 265*esc, 25*esc)
        EF.aro_3d(sm, cx, cy, 330, 1.18 + 0.1*np.sin(t*0.7), -0.38 + 0.08*np.sin(t*0.5), t*1.7, g, zs, oc)
        EF.aro_3d(sm, cx, cy, 300, 1.28 + 0.08*np.sin(t*0.6 + 1), 0.55 + 0.06*np.sin(t*0.4), -t*1.3 + 2.0, g*0.7, zs, oc)
    _, c0, c1, d1 = T_RA                                               # contadores (en cámara rápida)
    if c0 - 0.4 < t < d1:
        anos = int(round(1000*RELOJ.progreso(t)/10)*10)
        EF.contador(sm, f"{EF.miles(anos)} AÑOS", E.TITULO_Y2, ss(c0 - 0.4, c0, t)*(1 - ss(d1 - 0.5, d1, t)), raw)
    if t0 < t < t1:
        EF.contador(sm, f"DÍA {1 + int(ss(t0 + 0.3, t1 - 0.6, t)*8.999)}", E.TITULO_Y2, ss(t0, t0 + 0.4, t)*(1 - ss(t1 - 0.4, t1, t)), raw)
_extra6 = C5.EXTRA
C5.EXTRA = extra

def textos():
    T = C6.textos()
    TT = E.TAM_TITULO
    hueco = lambda t0, t1: Texto("·", t0, t1, y=295, tam=TT, brillo=0)   # el contador ocupa la 2ª línea: el sello va debajo
    T += [Texto("EN EL MAR PUEDE ESPERAR", T_RA[1] - 0.6, T_RA[3] - 0.4, y=230, tam=TT), hueco(T_RA[1] - 0.6, T_RA[3] - 0.4),
          hueco(T_DIAS[0], T_DIAS[1] - 0.2),
          Texto(TX_EV[0], T_EV - 0.2, T_EV - 0.2 + L_EV, y=230, tam=TT),
          Texto(TX_EV[1], T_EV + 0.4, T_EV - 0.1 + L_EV, y=295, tam=TT),
          Texto(TX_CO[0], T_CO + 0.1, T_CO + 0.1 + L_CO, y=230, tam=TT),
          Texto(TX_CO[1], T_CO + 0.6, T_CO + 0.2 + L_CO, y=295, tam=TT),
          Texto(TX_NUBE[0], T_DIAS[0], T_DIAS[1] - 0.2, y=230, tam=TT),
          Texto("CAE COMO LLUVIA", T_PR + 0.6, T_PR + 0.6 + E.tiempo_lectura("CAE COMO LLUVIA", extra=1), y=230, tam=TT),
          Texto(TX_ES[0], T_ES - 0.1, T_FIN - 0.5, y=230, tam=TT),
          Texto(TX_ES[1], T_ES + 0.4, T_FIN - 0.4, y=295, tam=TT)]
    return T

frame = C6.frame
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
