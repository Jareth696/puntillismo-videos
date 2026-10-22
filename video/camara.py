"""Cámara para planos que se sostienen mientras pasan los textos: NUNCA quieta.

Regla del motor (aprobada con Galileo): si una misma imagen queda en pantalla mientras se leen textos, la cámara se
sigue acercando al punto de interés (el rostro, el objeto clave). Las etiquetas de identidad (pergamino) quedan fijas.

    from camara import acercar, aplicar
    z, cx, cy = acercar(t, t0, t1, ancla=(585, 440), destino=(540, 760), z1=2.4)
    z, cx, cy = acercar_toma(t, t0, t1, ancla, destino)       # el zoom sale de lo que dura la toma
    x, y = aplicar(x, y, z, cx, cy)
"""
import numpy as np

W, H = 1080, 1920
CX, CY = W/2, H/2
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))

def cam_ancla(k, z0, z1, ancla, s0, s1):
    """Entre dos vistas: zoom logarítmico y un punto 'ancla' que viaja suave en pantalla de s0 a s1 (sin derivas)."""
    z = z0*(z1/z0)**k; s = np.asarray(s0, float)*(1 - k) + np.asarray(s1, float)*k
    c = np.asarray(ancla, float) - (s - [CX, CY])/z
    return z, c[0], c[1]

def acercar(t, t0, t1, ancla, destino, z1, z0=1.0):
    """Acercamiento continuo de t0 a t1: el ancla (p. ej. el rostro) va hacia 'destino' en pantalla con zoom z1."""
    return cam_ancla(ss(t0, t1, t), z0, z1, ancla, ancla, destino)

# regla: en tomas de personajes la cámara se acerca de a poco al rostro; más larga la toma, más se acerca
ACERCA_POR_SEGUNDO = 0.13
ACERCA_MAX = 2.4
def acercar_toma(t, t0, t1, ancla, destino):
    """Acercamiento de toma de personaje: el zoom final depende de lo que dura la toma (t0 -> t1)."""
    z1 = min(1 + ACERCA_POR_SEGUNDO*(t1 - t0), ACERCA_MAX)
    return acercar(t, t0, t1, ancla, destino, z1)

def aplicar(x, y, z, cx, cy):
    return (x - cx)*z + CX, (y - cy)*z + CY
