# Biblioteca de escenas, efectos y planos

Todo lo que ya probamos y funcionó. **Antes de armar un video nuevo:** leer esta lista, elegir lo que encaja con el
tema y proponerlo ("uso X porque..."). Así los videos salen más rápido y con cosas ya aprobadas.

Cada ficha dice: **qué es**, **cuándo usarlo**, **dónde está el código** y **en qué video se ve**.

---

## 1. Identidad (van en todos los videos)

| Ficha | Qué es | Cuándo | Código | Se ve en |
|---|---|---|---|---|
| **Entrada por convergencia** | Puntos dispersos por toda la pantalla se juntan en ~2 s y forman el elemento mientras aparece el gancho | Siempre, al inicio | `video/formacion.py` → `converger`, `textos_gancho` | todos |
| **Textos en puntos** | Letras finas que se forman juntando puntos y se disuelven flotando | Siempre | `video/textos.py` → `Texto`, `componer` | todos |
| **Sello de títulos (A)** | Línea de puntos con rombo central y punto guía bajo los títulos de arriba; baja con la 2ª línea, se recoge al salir | Automático en todo título de arriba | `video/textos.py` → `sello_titulo` | todos |
| **Pergamino con el nombre** | Cinta con colas en V y el nombre en serifa, a los pies o bajo el retrato; tapa recortes feos | Toda persona real que aparezca | `video/pergamino.py` → `pergamino("NOMBRE")` | Galileo, Darwin |
| **Indicador de etapas** | Fila de puntitos abajo; la etapa actual grande y rellena | Ciclos o procesos con pasos (fases, etapas) | `luna/fases8.py` → `indicador`; `agua/ciclo_agua2.py` → `indicador` | Luna, agua |
| **Etiqueta que sigue** | Rótulo pequeño que acompaña a un objeto que se mueve ("TIERRA", "JÚPITER") | Señalar algo en movimiento | `Texto(..., seguir=True, pista=[...])` | Galileo |

## 2. Cámara y planos

| Ficha | Qué es | Cuándo | Código | Se ve en |
|---|---|---|---|---|
| **Acercamiento al personaje** | La cámara se acerca de a poco al rostro; toma larga = más zoom. El pergamino queda fijo | Toda toma de una persona (regla general) | `video/camara.py` → `acercar_toma`, `aplicar` | Darwin, Galileo |
| **Acercamiento mientras se lee** | Si una imagen se sostiene con textos, la cámara se sigue acercando al punto de interés | Toda imagen sostenida con texto | `video/camara.py` → `acercar` | Galileo (estatua) |
| **Plano que se inclina** | Una vista desde arriba que pasa a verse de costado (órbitas que se vuelven elipses) | Sistemas, diagramas, órbitas | `galileo/galileo.py` → `estado(..., inc=...)`, `Cuerpo(..., plano=True)` | Galileo (geocéntrico, heliocéntrico) |
| **Objeto que muestra lo que vio** | Un objeto real de cerca → la cámara se aleja → de su boca salen los puntos que forman lo que se ve con él → zoom hasta eso | Instrumentos (telescopio, microscopio, cámara, ojo, radio...) | `galileo/galileo.py` → `telescopio_y_jupiter`, `cam_tel`; `video/camara.py` → `cam_ancla` | Galileo (telescopio → Júpiter) |
| **Cámara que sigue al protagonista** | Un poco más cerca durante toda la acción, zoom puntual en momentos clave y alejamiento | Protagonista que viaja | `video/protagonista.py` → `zoom_camara`; `agua/ciclo_agua6.py` | agua |

## 3. Transformaciones

| Ficha | Qué es | Cuándo | Código | Se ve en |
|---|---|---|---|---|
| **Estados que se transforman** | Un mismo conjunto de puntos pasa por imágenes (retrato → figuras → diagrama → retrato), emparejados por Hilbert, llegada escalonada | Temas de idea/historia | `darwin/evolucion.py` (plantilla), `tesla/stipple.py` → `hilbert_order` | Darwin, Galileo, Tesla |
| **Estados animados** | Los estados pueden moverse (órbitas, lunas que pasan detrás) mientras se transforman | Astronomía, máquinas, ciclos | `galileo/galileo.py` → `Cuerpo`, `estado` | Galileo |
| **Diagrama que crece desde su raíz** | Las ramas llegan en orden desde el origen, no al azar | Árboles, genealogías, redes | `darwin/evolucion.py` → `cladograma`, `arbol` | Darwin |
| **Luz que recorre un objeto** | La misma foto iluminada paso a paso (fases) | Fases, día/noche, eclipses | `luna/fases8.py` | Luna |
| **Cambio instantáneo invisible** | Dos estados iguales con transición de 0,001 s para reordenar los puntos sin que se note | Antes de una transformación que necesita otro emparejamiento | `galileo/galileo.py` → `TRANS[2]` | Galileo |

## 4. Efectos (módulo `video/efectos.py`)

| Ficha | Qué es | Cuándo | Código | Se ve en |
|---|---|---|---|---|
| **Espiral del tiempo** | Remolino alrededor del protagonista: brazos en espiral y símbolos (H₂O, E=mc², π, ∞...) y galaxias que salen hacia la cámara | "Pasaron millones de años", orígenes, viajes en el tiempo. En el gancho | `EspiralTiempo(t0, t1, simbolos=[...])` | agua (inicio) |
| **Reloj de arena + contador** | Reloj de arena de puntos que se da vuelta; un contador sube (años, siglos) sincronizado | Esperas largas, eras, "cuánto tarda" | `RelojArena`, `contador`, `miles` | agua (en el mar) |
| **Reloj de días** | Esfera de 60 marcas alrededor del protagonista y agujas que giran rápido + contador "DÍA 1..9" | Tiempos cortos (días, horas) | `anillo_reloj`, `agujas`, `contador` | agua (en la nube) |
| **Cámara rápida** | El entorno se acelera (olas) mientras pasa el tiempo | Junto al reloj de arena | `agua/ciclo_agua7.py` → `mar_rapido` | agua |
| **Calor** | Líneas onduladas que suben alrededor del objeto, cada vez más rápido | Calentar, evaporar, fundir, energía | `calor` | agua (evaporación) |
| **Anillo de cambio de estado** | Anillo que se abre (se dispersa) o se cierra girando (se junta) | Cambios de estado, nacer/morir, explotar/formarse | `anillo_cambio(abre=True/False)` | agua |
| **Aros 3D** | Aros inclinados con perspectiva que giran alrededor del protagonista; la parte de atrás pasa detrás; cola de cometa y flecha | Remate de ciclos, órbitas, "todo vuelve a empezar" | `aro_3d` | agua (final) |
| **Protagonista que actúa** | Se estira al moverse, respira, tiembla al llegar, salpicón y ondas | Protagonista que viaja | `video/protagonista.py` | agua |
| **Uno entre muchos** | Todos iguales; el nuestro con más brillo y halo de puntos | Una gota, una célula, una persona entre muchas | `video/protagonista.py` → `halo`; `agua/ciclo_agua5.py` | agua |
| **Estrellas de fondo** | Puntos tenues que titilan | Escenas de cielo/espacio | `galileo/galileo.py` → `frame` (`st_x`...) | Galileo |

## 5. Elementos ya convertidos a puntos (fuentes en `*/src/`)

| Elemento | Origen | Código |
|---|---|---|
| Luna llena | NASA (dominio público) | `luna/src/luna_llena_nasa.jpg` |
| Sol | NASA SDO | `galileo/src/sol_sdo.jpg` → `disco_imagen` |
| Júpiter | dibujado con código (bandas, Gran Mancha Roja) | `galileo/galileo.py` → `jupiter_dibujado` |
| Planetas/lunas simples | dibujados con código | `galileo/galileo.py` → `disco_liso` |
| Estatua de Galileo | foto del usuario (Uffizi), recorte GrabCut | `galileo/src/estatua.jpg`, `galileo/mask_estatua.npy` |
| Telescopio | Pixabay (aportado por el usuario), fondo transparente | `galileo/src/telescopio.webp` → `telescopio` |
| Retrato de Darwin | 1881, dominio público | `darwin/src/darwin_1881.jpg` → `darwin/elementos.py` |
| La "marcha" (5 figuras) | escultura (foto del usuario) | `darwin/src/marcha.jpg` → `figuras` |
| Retrato de Tesla | Napoleon Sarony, ca. 1890, dominio público | `tesla/src/tesla.jpg` |
| Gota, nube, montaña, mar | dibujados con código | `agua/ciclo_agua2.py`, `ciclo_agua5.py` |

## 6. Estilos de color

- **Puntillismo B/N (por defecto):** naturaleza, espacio, ciencia, historia, personajes.
- **Matrix verde (0 y 1):** solo temas digitales (tecnología, IA, datos). Código: `tesla/matrix_tesla.py`.

## 7. Movimientos de plano y cámara (muestra en `muestras/muestras_movimientos.mp4`)

Juegan con el plano y la cámara en 3D, como la hoja. Código: `video/movimientos.py`; cada escena de la muestra está
en `muestras/muestras.py` (función `e_...`) y sirve de ejemplo para copiar. Estado: **muestra**, afinar al usarlos.

| Movimiento | Qué es | Sirve para | Código / ejemplo |
|---|---|---|---|
| **Tarjeta que gira** | El plano gira en 3D como una carta; al darse vuelta aparece la siguiente imagen | Mito → realidad, antes → después | `tarjeta`, `borde_rect` / `e_tarjeta` (la marcha → ancestro común) |
| **Mesa que se inclina** | La imagen se acuesta y queda como un piso o mapa en perspectiva; la cámara la rodea | Mapas, líneas de tiempo | `inclinar` / `e_mesa` (árbol de la vida) |
| **Tela que se hunde** | Malla de puntos en perspectiva que se curva bajo un objeto pesado; otro rueda en la curva | Gravedad, espacio-tiempo | `tela`, `ver_tela` / `e_tela` (Sol y Tierra) |
| **Túnel de planos** | La cámara avanza entre planos en profundidad, cada uno con imagen y fecha | Historia, eras, evolución | `e_tunel` (1609 → 1610 → 1859 → hoy) |
| **Zoom infinito** | Se entra en un punto y adentro hay otra escala | Escalas: galaxia → Sol → Tierra | `e_zoom` |
| **Despiece** | El objeto se separa en sus partes con nombres y vuelve a armarse | Máquinas, anatomía, átomos | `e_despiece` (telescopio) |
| **Paralaje por capas** | Capas a distinta profundidad que se mueven a distinta velocidad | Paisajes, profundidad, viajes | `cordillera` / `e_paralaje` |
| **Campo de flujo** | Partículas que viajan por las líneas de un campo | Magnetismo, viento, corrientes | `lineas_dipolo`, `particulas_en_lineas` / `e_campo` |
| **Escáner de luz** | Una franja recorre el objeto y muestra lo de adentro | Capas de la Tierra, huesos, interiores | `e_escaner` |
| **Pliegue de página** | La mitad de la imagen gira sobre un lomo como la hoja de un libro y revela otra | Del personaje a su idea, capítulos | `pagina` / `e_pagina` (Darwin → árbol) |

### Segunda tanda (muestra en `muestras/muestras_movimientos_2.mp4`, código en `muestras/muestras2.py`)

| Movimiento | Qué es | Sirve para | Código / ejemplo |
|---|---|---|---|
| **Túnel del tiempo con escrituras** | La cámara viaja hacia atrás por planos de épocas, sin fotos: binario, E=mc², F=ma, a²+b²=c², números mayas, cuneiforme, huellas de dinosaurio; el protagonista en el centro | "Pasaron millones de años", historia de una idea (ideal para el gancho del agua) | `e_tunel_tiempo`, glifos `maya`, `cuneiforme`, `huella` |
| **Globo que gira** | Esfera de puntos con textura real (más puntos donde es clara) que gira e inclina | Planetas, la Luna, la Tierra | `esfera`, `globo` / `e_globo` |
| **Lupa** | Un círculo recorre la imagen y agranda el detalle | Mostrar un detalle, "mirá de cerca" | `lupa` / `e_lupa` |
| **Puntos que cuentan** | Grilla donde cada punto es una cantidad y se van encendiendo con un contador | Cifras enormes, comparaciones ("los humanos: menos de un punto") | `grilla_contadora` / `e_contar` |
| **Desintegración** | Un frente avanza y los puntos se vuelan con el viento; puede volver a armarse | Extinción, olvido, erosión, el paso del tiempo | `desintegrar` / `e_desintegrar` |
| **Línea que se dibuja** | Las estrellas aparecen y las líneas se trazan solas con una punta brillante | Constelaciones, rutas, mapas, firmas | `trazar` / `e_orion` |
| **Onda expansiva** | Algo cae sobre una superficie de puntos en perspectiva y se abren anillos | Impactos, sonido, terremotos, gotas | `superficie_onda` / `e_onda` |

## Cómo proponer un video nuevo con la biblioteca

1. Gancho: ¿qué cree la mayoría? (ver `GUIA_ESTILO.md`).
2. Tipo: ¿transformación en el lugar o protagonista que viaja?
3. Elegir de esta lista las escenas/efectos que cuentan la historia (p. ej. tema de un inventor: *acercamiento al
   personaje + pergamino + objeto que muestra lo que vio + estados que se transforman*).
4. Textos cortos; cada uno dura `E.tiempo_lectura(...)`.
5. Al aprobar algo nuevo: **agregarlo aquí** con su ficha.
