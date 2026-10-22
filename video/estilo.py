"""Estilo aprobado (video de las 8 fases de la Luna, v5). Todos los scripts nuevos parten de estos valores.

Regla general: es un efecto muy visual, así que nada debe hacer esperar al espectador.
Lo visual empieza en el primer segundo y cada mensaje se superpone con el movimiento.
"""

# ---------- tiempos (segundos) ----------
GANCHO_INICIO = 0.3        # el objeto empieza a formarse casi de inmediato
GANCHO_FORMADO = 3.8       # el objeto principal ya está completo
GANCHO_FIN = 4.9           # termina el gancho; empieza la transición a la acción
ACCION_INICIO = 6.4        # la acción principal (p. ej. el ciclo de fases) arranca antes de los 6,5 s

ETAPA = 3.8                # duración de cada etapa de un ciclo (quieta + transición)
ETAPA_QUIETA = 1.4         # tiempo quieto para leer el nombre de la etapa
ETAPA_FINAL = 2.2          # la última etapa es más corta: lleva rápido al remate
ETAPA_FINAL_QUIETA = 1.0

REMATE_FORMA = 1.3         # el remate (imagen final) se forma en ~1,3 s
REMATE_TEXTO_ANTES = 0.4   # el texto final empieza a formarse ANTES de que termine el ciclo
CIERRE = 4.6               # desde el fin de la acción hasta el final del video
FUNDIDO_FINAL = 1.2        # fundido a negro

# ---------- REGLA DE INICIO (permanente, ver formacion.py) ----------
# Fondo negro. Puntos dispersos por toda la pantalla se juntan rápido (como Tesla) y forman el elemento principal,
# mientras se forma el texto de contexto. Nada estático al inicio.
CONVERGE_INICIO = 0.2      # los puntos empiezan a moverse
CONVERGE_ESCALON = 1.1     # demora máxima entre el primer y el último punto (llegan escalonados)
CONVERGE_VIAJE = 1.0       # lo que tarda cada punto en llegar -> elemento formado a ~2,3 s
TEXTO_GANCHO_1 = (0.5, 4.4)  # (aparece, se va) primera línea del gancho
TEXTO_GANCHO_2 = (1.1, 4.6)  # segunda línea

# ---------- textos ----------
TEXTO_ENTRADA = 0.8        # los puntos se juntan en ~0,8 s (ver textos.py)
TEXTO_SALIDA = 0.9         # se disuelven flotando en ~0,9 s
TAM_TITULO = 42            # px; título arriba (y≈230 / 295 para dos líneas)
TAM_ETIQUETA = 34          # px; etiquetas abajo (y≈1430)
TAM_CIERRE = 36

# ---------- puntos ----------
CONTRASTE_BASE = 0.24      # textura: 0 = original (zonas oscuras vacías), 0.38 = muy suave; 0.24 = aprobado
GAMMA = 1.7
BORDES = 6
PUNTOS_MAX = 60000
TONO_MIN = 0.04            # brillo mínimo de un punto: las sombras quedan oscuras
CENIZA = 0.035             # luz tenue en la parte oscura (se ve la silueta sin competir con lo iluminado)


# ---------- tiempo de lectura (regla del motor) ----------
# El espectador reparte la atención entre el texto de arriba, la etiqueta de abajo y la imagen en movimiento.
# Cada texto dura según cuántas palabras tiene y cuántas otras cosas hay que mirar a la vez.
LECTURA_BASE = 1.2          # s para notar el texto
LECTURA_PALABRA = 0.38      # s por palabra
LECTURA_EXTRA = 0.6         # s por cada otro elemento con texto en pantalla (etiqueta de etapa, contador, rótulo)
def tiempo_lectura(*lineas, extra=0):
    palabras = sum(len(l.split()) for l in lineas)
    return LECTURA_BASE + LECTURA_PALABRA*palabras + LECTURA_EXTRA*extra
