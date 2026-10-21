"""Regla permanente de inicio (aprobada con la Luna):

    Fondo negro. El elemento principal nace desde un punto en el centro y crece hasta formarse,
    mientras AL MISMO TIEMPO se forma el texto de contexto (gancho). Nada estático al inicio.

Uso:
    from formacion import crecer, aplicar_crecimiento, textos_gancho
    s = crecer(t)                                   # 0.02 -> 1.0 entre GANCHO_INICIO y GANCHO_FORMADO
    x, y, w = aplicar_crecimiento(x, y, w, t, cx, cy)
    T = textos_gancho("¿SABÍAS QUE LA LUNA", "TIENE 8 FASES?") + [...]
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

def textos_gancho(linea1, linea2=None, y=230, tam=None):
    """Texto de contexto que se forma junto con el elemento (tiempos aprobados de la Luna)."""
    from textos import Texto
    tam = tam or E.TAM_TITULO
    T = [Texto(linea1, E.TEXTO_GANCHO_1[0], E.TEXTO_GANCHO_1[1], y=y, tam=tam)]
    if linea2: T.append(Texto(linea2, E.TEXTO_GANCHO_2[0], E.TEXTO_GANCHO_2[1], y=y + 65, tam=tam))
    return T
