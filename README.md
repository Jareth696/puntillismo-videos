# Puntillismo con código

Videos verticales para Reels (1080x1920) hechos 100 % con Python: cada fotograma se dibuja con puntos (numpy) y se une
con ffmpeg. No hace falta una PC potente: solo tiempo de cálculo.

## Videos finales (listos para publicar) → `finales/`

| Archivo | Tema |
|---|---|
| `01_luna_8_fases.mp4` | Las 8 fases de la Luna |
| `02_ciclo_del_agua.mp4` | El ciclo del agua: una gota de millones de años |
| `03_darwin_evolucion.mp4` | Darwin: no venimos del mono, compartimos un ancestro |
| `04_galileo.mp4` | Galileo: ¿el Sol gira alrededor de la Tierra? |

## Instalar (Windows, Mac o Linux)

1. **Python 3.10 o más nuevo**: https://www.python.org/downloads/ (en Windows, marcar "Add Python to PATH").
2. **ffmpeg**:
   - Windows: `winget install ffmpeg` (o descargar de https://www.gyan.dev/ffmpeg/builds/ y agregar `bin` al PATH)
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
3. **Librerías**: en la carpeta del proyecto, `pip install -r requirements.txt`

Las letras ya vienen en `video/letras/` (licencias libres en `video/letras/licencias/`). No hay que instalar nada más.

## Generar los videos

```
python hacer_finales.py                 # los 4 videos → finales/
python hacer_finales.py galileo         # solo uno (luna, agua, darwin, galileo)
```

La primera vez tarda más: convierte las fotos a puntos (Voronoi) y lo guarda en caché (`cache_*.npy`).
Después, cada video tarda unos minutos (depende de la PC; usa 4 núcleos).

Para probar rápido un tramo, cada script acepta cuántos fotogramas hacer (24 = 1 segundo):
```
cd galileo
python galileo.py prueba.mp4 48 prueba_con_textos.mp4
```

## Estructura

| Carpeta | Qué hay |
|---|---|
| `video/` | **El motor**: estilo y tiempos (`estilo.py`), entrada (`formacion.py`), textos y sello de títulos (`textos.py`), pergamino (`pergamino.py`), cámara (`camara.py`), efectos (`efectos.py`), protagonista que viaja (`protagonista.py`), puntillismo desde video real (`video_stipple.py`), letras (`letras/`) |
| `tesla/` | `stipple.py` (Voronoi + orden de Hilbert, lo usan todos) y el video de Tesla (B/N y Matrix) |
| `luna/` | Las 8 fases de la Luna |
| `agua/` | El ciclo del agua (`ciclo_agua7.py` es el final; usa 2 → 3 → 4 → 5 → 6 por debajo) |
| `darwin/` | Darwin y la evolución |
| `galileo/` | Galileo |
| `finales/` | Videos listos para publicar |

## Para hacer videos nuevos

1. Leer **`GUIA_ESTILO.md`** (reglas: gancho, entrada, ritmo, tiempo de lectura, cámara, identidad).
2. Leer **`BIBLIOTECA.md`** (escenas, efectos y planos ya probados) y elegir qué usar.
3. Partir de la plantilla más parecida: idea/historia → `darwin/evolucion.py`; personaje + objeto + astronomía →
   `galileo/galileo.py`; proceso con un protagonista que viaja → `agua/`; fases/luz → `luna/fases8.py`.
4. Agregar el video a `hacer_finales.py`.

`CONTINUAR.md` tiene el estado del proyecto y las fuentes de imágenes.
