"""Herramientas para videos de PROTAGONISTA QUE VIAJA (aprobado con la gota del ciclo del agua y la hoja).

Para un elemento que se mueve por distintos entornos, el elemento debe "actuar":
  - se estira e inclina hacia donde se mueve (deformar)
  - respira / se mece suavemente cuando está quieto o flotando (deformar)
  - tiembla como gelatina y se asienta al llegar a algo (temblor)
  - la cámara lo sigue un poco más cerca durante toda la acción, con zoom puntual en los momentos clave (zoom_camara)
  - los impactos se ven: salpicón y ondas (salpicon, ondas)
  - si hay muchos iguales: misma forma para todos; el nuestro solo más brillo + halo de puntos (halo)

Para videos de TRANSFORMACIÓN EN EL LUGAR (la Luna, Tesla) no hace falta nada de esto.
"""
import numpy as np

ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))

# valores aprobados (gota v8)
ESTIRA_MAX = 0.32          # cuánto se estira a máxima velocidad
ESTIRA_VEL = 1400.0        # px/s para el estiramiento máximo
RESPIRA = 0.035            # amplitud del "respirar"
TEMBLOR = 0.12             # amplitud del temblor al llegar
TEMBLOR_DUR = 1.2
ZOOM_BASE = 1.18           # cámara más cerca durante toda la acción
ZOOM_CLAVE = 1.75          # zoom puntual en un momento clave (llegada, lugar nuevo)

def temblor(t, llegadas, fase=0.0):
    """Suma de temblores amortiguados después de cada momento de llegada."""
    v = 0.0
    for t0 in llegadas:
        d = t - t0 - 0.05*fase
        if 0 < d < TEMBLOR_DUR: v += TEMBLOR*np.exp(-d*3.2)*np.sin(d*22)
    return v

def deformar(x, y, t, vel=(0.0, 0.0), llegadas=(), fase=0.0):
    """Puntos locales del elemento (centrados en 0,0) -> estirados/inclinados según la velocidad, respirando y
    temblando al llegar. vel en px/s (pantalla)."""
    sp = float(np.hypot(*vel)); est = 1 + min(sp/ESTIRA_VEL, ESTIRA_MAX)
    resp = RESPIRA*np.sin(t*2.6 + fase) + temblor(t, llegadas, fase)
    x = x*(1 + resp)/np.sqrt(est); y = y*(1 - resp)*est
    if sp > 1:
        ang = np.clip(np.arctan2(vel[0], vel[1]), -0.5, 0.5)*min(sp/600, 1)
        c, s = np.cos(ang), np.sin(ang); x, y = x*c + y*s, -x*s + y*c
    return x, y

def mecer(t, amp=8.0, vel=1.9, fase=0.0):
    """Desplazamiento vertical suave (flotar)."""
    return amp*np.sin(t*vel + fase)

def zoom_camara(t, inicio, fin, claves=()):
    """Zoom de cámara: ZOOM_BASE durante la acción, y ZOOM_CLAVE en cada (entra, sale) de 'claves'."""
    z = 1 + (ZOOM_BASE - 1)*ss(inicio, inicio + 1.4, t)*(1 - ss(fin - 0.6, fin + 0.4, t))
    for a, b in claves:
        z = max(z, 1 + (ZOOM_CLAVE - 1)*ss(a, a + 0.9, t)*(1 - ss(b, b + 1.7, t)))
    return z

def halo(cx, cy, R, t, n=160, seed=0):
    """Halo de puntos alrededor del protagonista (lo distingue sin marcarlo con un círculo)."""
    r = np.random.default_rng(seed); a = r.uniform(0, 2*np.pi, n); rr = 1.25 + r.exponential(0.45, n)
    w = 0.55*np.exp(-(rr - 1.25)/0.5)*(0.7 + 0.3*np.sin(t*4 + a*7))
    return cx + R*rr*np.cos(a + t*0.4), cy + R*rr*1.1*np.sin(a + t*0.4), w

def salpicon(cx, cy, t, t0, n=26):
    """Pequeño estallido de puntos hacia arriba al chocar (coordenadas de pantalla)."""
    p = (t - t0)/0.7
    if not 0 < p < 1: return None
    a = np.linspace(np.pi*1.05, np.pi*1.95, n); r = 20 + 90*p
    return cx + r*np.cos(a), cy + r*np.sin(a)*0.8 + 160*p*p, np.full(n, 0.9*(1 - p))

def ondas(cx, cy, t, t0, n=90, cantidad=3):
    """Ondas que se abren en una superficie de agua (lista de (x, y, w))."""
    out = []
    for k in range(cantidad):
        p = (t - t0 - 0.35*k)/1.6
        if 0 < p < 1:
            a = np.linspace(0, 2*np.pi, n, endpoint=False); r = 30 + 170*p
            out.append((cx + r*np.cos(a), cy + 0.22*r*np.sin(a), np.full(n, 0.75*(1 - p)**1.3)))
    return out
