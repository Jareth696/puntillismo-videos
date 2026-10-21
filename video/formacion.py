"""Regla permanente de inicio (como Tesla):

    Fondo negro. Puntos DISPERSOS por toda la pantalla se juntan rápido y forman el elemento principal,
    mientras AL MISMO TIEMPO se forma el texto de contexto (gancho). Nada estático al inicio.

Uso:
    from formacion import converger, textos_gancho
    x, y, w = converger(x, y, w, t)                 # x, y: posiciones finales del elemento en pantalla
    T = textos_gancho("¿SABÍAS QUE LA LUNA", "TIENE 8 FASES?") + [...]
(crecer / aplicar_crecimiento: alternativa antigua, nacer desde un punto; ya no es la regla.)
"""
import numpy as np
import estilo as E

ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))

def crecer(t):
    """Escala del elemento principal: nace como un punto y llega a su tamaño a los E.GANCHO_FORMADO s."""
    return 0.02 + 0.98*(1 - (1 - ss(E.GANCHO_INICIO, E.GANCHO_FORMADO, t))**1.6)

def aplicar_crecimiento(x, y, w, t, cx, cy):
    """Puntos de un elemento (ya ubicados en pantalla) -> crecen desde el centro (cx, cy) y se encienden."""
    s = crecer(t)
    return cx + (x - cx)*s, cy + (y - cy)*s, w*(0.25 + 0.75*ss(E.GANCHO_INICIO, E.GANCHO_INICIO + 1.2, t))

_CACHE = {}
def _origen(n, seed, W=1080, H=1920, maximo=200000):
    """Posiciones dispersas y demoras fijas por punto (las mismas en cada cuadro, aunque n cambie un poco)."""
    if seed not in _CACHE:
        r = np.random.default_rng(seed)
        o = np.c_[r.uniform(-120, W + 120, maximo), r.uniform(-160, H + 160, maximo)]
        _CACHE[seed] = (o, r.uniform(0, 1, maximo)**1.4*E.CONVERGE_ESCALON, r.uniform(0, 6.28, maximo))
    o, d, f_ = _CACHE[seed]; return o[:n], d[:n], f_[:n]

def converger(x, y, w, t, seed=0):
    """Regla de inicio: cada punto viaja desde un lugar disperso hasta su posición final, escalonado y rápido."""
    if t > E.CONVERGE_INICIO + E.CONVERGE_ESCALON + E.CONVERGE_VIAJE + 0.05: return x, y, w
    o, dem, fase = _origen(len(x), seed)
    e = ss(0, 1, (t - E.CONVERGE_INICIO - dem)/E.CONVERGE_VIAJE)
    lib = (1 - e)                                              # mientras viajan, un leve titileo/deriva
    px = o[:, 0]*lib + x*e + lib*np.sin(t*2.3 + fase)*14
    py = o[:, 1]*lib + y*e + lib*np.cos(t*1.9 + fase)*14
    return px, py, w*(0.85 + 0.15*e)                           # bien visibles mientras viajan

def textos_gancho(linea1, linea2=None, y=230, tam=None):
    """Texto de contexto que se forma junto con el elemento (tiempos aprobados de la Luna)."""
    from textos import Texto
    tam = tam or E.TAM_TITULO
    T = [Texto(linea1, E.TEXTO_GANCHO_1[0], E.TEXTO_GANCHO_1[1], y=y, tam=tam)]
    if linea2: T.append(Texto(linea2, E.TEXTO_GANCHO_2[0], E.TEXTO_GANCHO_2[1], y=y + 65, tam=tam))
    return T
