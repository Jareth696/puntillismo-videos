# Guía de estilo (aprobada con `videos/luna_8_fases.mp4` y `videos/hoja_viento.mp4`)

## Resumen: así funciona el motor
1. **Entrada:** puntos dispersos que se juntan rápido y forman el elemento, mientras se forma el texto de contexto.
2. **Un solo plano:** nada de viajar entre escenarios. El movimiento sale de **cambiar la vista del mismo plano**
   (girar o inclinar el elemento, la luz que cambia como en las fases) y de **elementos que entran**
   (viento, lluvia, suelo, etiquetas) o que se transforman en otros.
3. **Ritmo rápido:** transiciones ágiles, salidas cortas, el remate llega antes de que la gente deslice.
4. **Fondo negro, puntos blancos** (Matrix verde solo para temas digitales).

Los valores exactos están en `video/estilo.py`. Todo script nuevo debe importarlo (`import estilo as E`).

## EL GANCHO (lo más importante)
- Hablarle a la **persona común**, no al especialista: partir de **lo que la mayoría cree o ve** (el mono que se
  endereza, "el Sol gira alrededor de la Tierra") y luego **aclararlo**. La corrección de un mito engancha más que un dato.
- Una pregunta o afirmación corta, directa y llamativa, en 2 líneas como máximo, mientras se forma la imagen.
- Lo visual del gancho debe ser la creencia popular misma (la imagen que todos tienen en la cabeza).

## REGLA DE INICIO (permanente)
**Fondo negro. Puntos dispersos por toda la pantalla se juntan rápido (en ~2 s, escalonados) y forman el elemento
principal, mientras al mismo tiempo se forma el texto de contexto (gancho).** Como la entrada de Tesla: desde el primer
instante se nota que todo está hecho de puntos. Código: `video/formacion.py` (`converger`, `textos_gancho`).

## Dirección principal: plano fijo, los elementos aparecen y se transforman
- La cámara casi no se mueve; los protagonistas son los puntos: nacen, se transforman, se disuelven.
- Imágenes con estructura clara (siluetas, líneas principales) antes que texturas finas.
- Pocos elementos por escena, grandes y bien iluminados.

## Dos tipos de video
1. **Transformación en el lugar** (`luna_8_fases.mp4`, Tesla, `darwin_evolucion.mp4`): el elemento se queda quieto y lo que cambia es él
   mismo (fases, forma). No necesita gestos propios.
2. **Protagonista que viaja** (`ciclo_agua.mp4`, `hoja_viento.mp4`): el elemento recorre entornos y debe "actuar".
   Usar `video/protagonista.py`:
   - se **estira e inclina** hacia donde se mueve; **respira/se mece** cuando flota; **tiembla al llegar** y se asienta;
   - **cámara un poco más cerca** toda la acción y **zoom puntual** en momentos clave (p. ej. al llegar a la montaña),
     luego alejamiento para mostrar a dónde va;
   - **impactos visibles**: salpicón al chocar, ondas al entrar al agua;
   - movimiento con **física**: caídas que aceleran (gravedad), sin frenar en el aire; el zoom empieza DESPUÉS del impacto;
   - **uno entre muchos**: todos con la misma forma, bien dibujados y grandes ("con zoom", pocos y nítidos);
     el nuestro solo con **más brillo y un halo de puntos** (nunca un círculo que lo marque);
   - entornos **solo de perfil** (contornos de puntos: nube con borde abajo y arriba, montaña), con un rótulo de contexto
     pequeño ("NUBE", "MONTAÑA") en el espacio vacío;
   - etapas un poco más largas (~4,6 s) para que el movimiento se aprecie.

## Ritmo: nada hace esperar al espectador
- **Lo visual empieza en el primer segundo.** El objeto se forma desde un punto mientras aparece el gancho (título/pregunta).
- **El objeto está completo a los ~3,8 s** y la acción principal arranca **antes de los 6,5 s**.
- **Etapas de ~3,8 s:** ~1,4 s quieta (para leer la etiqueta) + transición continua (sin cortes).
- **La última etapa es más corta (~2,2 s)** y lleva directo al remate.
- **El remate se forma en ~1,3 s** y su texto **empieza antes** de que termine la acción (se superponen).
- **Cierre total ~4,6 s** desde el fin de la acción, con fundido de 1,2 s. Pensado para Reels: el dato final llega antes de que la gente deslice.

## Textos (en puntos, `video/textos.py`)
- Fuente fina (Inter ExtraLight), mayúsculas espaciadas, un poco más tenues que la imagen.
- Se forman juntando puntos (~0,8 s) y se disuelven flotando (~0,9 s).
- Pocos y breves: gancho arriba, etiquetas abajo y pequeñas, remate arriba. Lo principal es la imagen.
- Contenido enfocado en el tema: sin elementos que distraigan del mensaje (p. ej. se quitó la Tierra en las fases).

## Puntos
- Blanco y negro, fondo negro (Matrix: verde y negro).
- Contraste de textura intermedio (`CONTRASTE_BASE = 0.24`): se ven los detalles (mares, cráteres) sin huecos.
- Sombras oscuras (`TONO_MIN`) y luz tenue en la parte oscura (`CENIZA`) para ver la silueta.
- El motor reubica puntos varados en sombras y reparte rápido cuando cambia la luz (activado por defecto).
- Indicador de progreso: fila de puntitos, la etapa actual grande y rellena.

## Fuentes
- Mejor: fondo oscuro, luz lateral, un objeto principal claro, movimiento moderado.
- Revisar siempre antes con `--analizar` (cortes, destellos, objetos secundarios).

## ¿Puntillismo o Matrix?
- **Puntillismo (por defecto):** naturaleza, espacio y universo, retratos, ciencia visual, todo lo que busque realismo o poesía visual. Conserva mucho más detalle (40–60 mil puntos libres).
- **Matrix (verde y negro):** solo cuando el tema es digital: tecnología, datos, código, inteligencia artificial, ciberseguridad, personajes del mundo digital. El 0/1 refuerza el mensaje, pero la grilla de caracteres pierde detalle.
- Ante la duda: puntillismo.

## Flujo de trabajo (acordado)
1. **Elementos reales aislados** (hoja, rostro, Luna, edificio…): se toman de una foto o de un cuadro de video con buen
   contraste, se les quita el fondo y se guardan en `elementos/` (biblioteca reutilizable). Se convierten a puntos
   **una vez, con la imagen quieta** (Voronoi, 30 pasadas): así se ven nítidos, como Tesla.
2. **Lo simple lo genera el código:** pasto, lluvia, viento, estrellas, montañas, rayos, partículas.
3. **El movimiento y la historia los ponemos nosotros:** cámara, vuelo, transformaciones, textos y tiempos de esta guía.
4. **Los elementos se combinan entre videos** (p. ej. la hoja vuela frente a la casa de Tesla).

## Lección: convertir videos reales cuadro por cuadro casi nunca queda bien
Muchos elementos pequeños, fondos con detalle y movimiento constante hacen que los puntos se vean como ruido.
Usar video real solo para **extraer elementos** (como la textura de la hoja, del video 3737 de Mixkit) o en casos
muy limpios (un objeto sobre fondo negro). El puntillismo se luce con **un objeto grande, fondo limpio y buena luz**.

## Fuentes que funcionan desde la nube
- **NASA** (images.nasa.gov): dominio público.  **Mixkit** (mixkit.co): videos gratis, uso comercial sin crédito.
- Bloqueadas o limitadas desde la nube: Wikimedia/Flickr (429), Pexels/Freepik/Rawpixel (403), Unsplash/Pixabay (piden cuenta).
  Desde el celular o la PC funcionan: se pueden subir a `fuentes/` del repo.

## Lección de Darwin (aprobado al primer intento)
- Un mismo conjunto de puntos que pasa por **estados** (retrato → figuras → diagrama → árbol → retrato), emparejados
  por curva de Hilbert y con la llegada escalonada (`darwin/evolucion.py`). Es la plantilla para temas de "idea/historia".
- Usar una imagen popular **para corregir un mito** es un gancho muy fuerte (la "marcha" → el árbol con ancestro común).
- Los diagramas (ramas) crecen desde su origen: el orden de llegada sigue la estructura, no al azar.

## Lección de Galileo (aprobado en v3)
- **Pergamino con el nombre** (`video/pergamino.py`): cinta con colas en V y el nombre en mayúsculas con serifa, a los
  pies del personaje. Es el sello de identidad de los videos de personajes y tapa recortes feos (pies, bases).
- **Más contexto sin aburrir:** contar la historia completa (lo que se creía → lo que vio → lo que dedujo → lo que
  cambió), pero cada texto con algo moviéndose: planos que se inclinan, acercamientos lentos, órbitas.
- **El objeto real muestra lo que se ve con él:** el telescopio se ve de cerca, la cámara se aleja, de su boca sale lo
  que vio (Júpiter) y la cámara hace zoom hasta eso. Un mismo plano, distintas vistas.
- **La duración la pone la historia:** dura lo que tenga que durar, con entradas, transiciones y salidas rápidas.
- **Que el tiempo se vea** (ciclo del agua v9): cuando la historia dice "pasan años/días", mostrarlo con relojes de
  puntos, contadores y cámara rápida, no solo decirlo.
