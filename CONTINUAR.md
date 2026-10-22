# Para continuar (estado al 22-oct-2026)

**Antes de crear un video nuevo:** leer `GUIA_ESTILO.md` (reglas) y `BIBLIOTECA.md` (escenas y efectos probados),
y usar `video/estilo.py`.

## Videos terminados (`finales/`, aprobados y listos para publicar)
| Archivo | Script | Qué es |
|---|---|---|
| `01_luna_8_fases.mp4` | `luna/fases8.py` | Las 8 fases de la Luna. Referencia de ritmo |
| `02_ciclo_del_agua.mp4` | `agua/ciclo_agua7.py` | Una gota de millones de años: espiral del tiempo, reloj de arena, cambios de estado, aros 3D |
| `03_darwin_evolucion.mp4` | `darwin/evolucion.py` | Retrato con pergamino → la marcha → ancestro común → árbol de la vida → retrato |
| `04_galileo.mp4` | `galileo/galileo.py` | Geocéntrico → estatua → telescopio que muestra Júpiter → sistema solar → acercamiento al rostro |

Todos llevan el sello de títulos (opción A) y, si aparece una persona, su pergamino con el nombre y el acercamiento.
Regenerar: `python hacer_finales.py` (ver `README.md`).

Tesla (`tesla/`) quedó como prueba temprana (B/N y Matrix); no está entre los finales. La hoja se borró (sigue en el
historial de git si alguna vez hace falta).

## Fuentes de imágenes
- Luna llena: NASA/GSFC, GSFC_20171208_Archive_e001861 (`luna/src/`). Sol: NASA SDO (`galileo/src/`).
- Retrato de Darwin 1881 y de Tesla ca. 1890: dominio público. Escultura de la marcha, estatua de Galileo y telescopio:
  imágenes aportadas por el usuario (Pixabay).
- Sobrevuelos lunares de la NASA (para `video/video_stipple.py`):
  https://images-assets.nasa.gov/video/lunarflyby_1min_2160p30/lunarflyby_1min_2160p30~large.mp4
- Desde la nube funcionan la NASA y Mixkit; Wikimedia, Pexels, Pixabay y Unsplash bloquean descargas automáticas
  (desde la PC sí: se bajan y se ponen en la carpeta `src/` del video).

## Ideas pendientes
- Gancho alternativo para el agua: "EL AGUA QUE TOMAS / PUDO BEBERLA UN DINOSAURIO".
- Opcionales: firma al final (usuario en puntos), portadas para cada Reel.

## Notas
- Las fases de la Luna están orientadas para el hemisferio norte (creciente iluminada a la derecha).
- Los videos pesan más de lo normal por los puntos finos; `hacer_finales.py` los comprime (CRF 20) para publicar.
