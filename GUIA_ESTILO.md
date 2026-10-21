# Guía de estilo (aprobada con `videos/luna_8_fases.mp4`)

Los valores exactos están en `video/estilo.py`. Todo script nuevo debe importarlo (`import estilo as E`).

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
