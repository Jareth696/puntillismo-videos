# Puntillismo y Matrix con código

Videos verticales (1080x1920) hechos 100 % con Python: cada fotograma se dibuja con puntos (numpy) y se une con ffmpeg.

## Requisitos
- Python 3 con `pip install -r requirements.txt` (numpy, pillow, scipy)
- ffmpeg
- Para Matrix: fuente JetBrains Mono Bold (o cambiar la ruta `FONT` por otra fuente monoespaciada)

## Proyectos

### `hoja/` — Hoja que viaja y cae bajo la lluvia
- `hoja_bn5.py`: puntillismo blanco y negro. Hoja 3D, 3 escenas (árbol, vacío, dos árboles, vacío), montañas con paralaje, viento, lluvia, relámpago.
  `cd hoja && python3 hoja_bn5.py salida.mp4`
- `matrix.py`: la misma escena convertida a 0 y 1 (sale en gris; el verde se aplicó con el filtro de ffmpeg de abajo).

### `tesla/` — Rostro de Tesla que se transforma en bombilla
- `stipple.py`: stippling de Voronoi ponderado (reparte puntos según una foto) + orden de Hilbert para emparejar formas.
- `formas.py`: mapas de densidad (retrato desde `src/tesla.jpg` con máscara de silueta; bombilla dibujada con código).
- `tesla.py`: animación en puntillismo B/N. `cd tesla && python3 tesla.py salida.mp4`
- `matrix_tesla.py`: versión Matrix verde. `cd tesla && python3 matrix_tesla.py salida.mp4`
- Foto: Napoleon Sarony, ca. 1890, dominio público (Wikimedia Commons).

Consejo: para pruebas rápidas, el segundo argumento limita los fotogramas: `python3 tesla.py prueba.mp4 48` (2 s).

### Verde Matrix sobre un video gris
```
ffmpeg -i entrada.mp4 -vf "format=rgb24,lutrgb=r='255*pow(val/255\,3.2)*0.75':g='255*min(1\,pow(val/255\,0.9)*1.08)':b='255*pow(val/255\,2.6)*0.45',format=yuv420p" -c:v libx264 -crf 16 salida.mp4
```

### `video/` — Puntillismo desde un video real
`video_stipple.py` convierte cualquier video en puntos con coherencia temporal (los puntos se mueven, no parpadean).
- `--analizar`: solo muestra un informe (cortes de escena, tramos sin objeto, destellos) sin renderizar.
- `--seguir`: encuadre automático 9:16 que sigue al objeto principal (ignora destellos) y lo mantiene completo.
- `--cortes antes` (por defecto): termina antes del primer corte de escena o de que un destello (Sol/reflejo) se vuelva el objeto.
- `--variable`: cantidad de puntos según el tamaño del objeto. `--estrellas N`: fondo estrellado.

Ejemplo (Luna, NASA Artemis II, dominio público):
```
python3 video/video_stipple.py flyby_abril.mp4 luna.mp4 --seguir --vel 1.5 --dur 38 --puntos 60000 --variable 0.35 \
  --estrellas 220 --negro 0.18 --gamma 2.2 --bordes 8 --tono_min 0.15 --brillo 4
```
Fuente: https://images.nasa.gov/details/lunarflyby_1min_2160p30 (NASA Scientific Visualization Studio).

Las mejores fuentes: fondo negro u oscuro, luz lateral con sombras, un objeto principal claro, movimiento moderado.

## `videos/`
Versiones aprobadas de cada proyecto.
