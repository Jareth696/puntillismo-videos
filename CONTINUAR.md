# Para continuar (estado al 21-oct-2026)

**Antes de crear un video nuevo, leer `GUIA_ESTILO.md` y usar `video/estilo.py`.**

## Videos terminados (`videos/`)
| Archivo | Qué es |
|---|---|
| `hoja_bn_v5.mp4` | Hoja 3D en puntillismo B/N (3 escenas, lluvia) |
| `hoja_matrix_verde.mp4` | La hoja en estilo Matrix verde |
| `tesla_bombilla_v1.mp4` | Rostro de Tesla → bombilla sin cables (B/N) |
| `tesla_bombilla_matrix_v1.mp4` | Tesla en Matrix verde |
| `luna_fases_textos.mp4` | Sobrevuelo lunar real (NASA) en puntos, con textos |
| `luna_8_fases.mp4` | **Aprobado (v6):** las 8 fases de la Luna, entrada estilo Tesla. Referencia de estilo |
| `ciclo_agua.mp4` | **Aprobado (v8):** el ciclo del agua, la gota protagonista. Referencia de protagonista que viaja |
| `darwin_evolucion.mp4` | **Aprobado (v1, sin cambios):** Darwin → la marcha → ancestro común → árbol de la vida. Fuentes en `darwin/src/` (retrato 1881, dominio público; escultura aportada por el usuario) |
| `galileo.mp4` | **Aprobado (v3):** geocéntrico → estatua con pergamino → telescopio que se aleja y de su boca sale Júpiter → zoom a sus 4 lunas → sistema solar → condena y remate (`galileo/galileo.py`) |
| `hoja_viento.mp4` | **Aprobado:** la hoja en el viento, plano fijo con cambios de ángulo. Referencia de movimiento |

## Cómo regenerar
- 8 fases: `cd luna && python3 fases8.py sin_textos.mp4` y luego
  `python3 -c "import sys; sys.path.insert(0,'../video'); import fases8 as F; from textos import componer; componer('sin_textos.mp4','final.mp4',F.textos())"`
- Requisitos: `pip install -r requirements.txt` + ffmpeg. Fuentes: Inter (textos), JetBrains Mono (Matrix).

## Fuentes externas (no están en el repo, se descargan de nuevo si hacen falta)
- Sobrevuelo Artemis II, luz lateral: https://images-assets.nasa.gov/video/lunarflyby_1min_2160p30/lunarflyby_1min_2160p30~large.mp4
- Sobrevuelo Artemis II, luz frontal: https://images-assets.nasa.gov/video/a2_flyby_1min_2160p30/a2_flyby_1min_2160p30~large.mp4
- Tomas reales Artemis I (Orion dejando la Luna): https://images.nasa.gov/details/Artemis_I_Post-RPF_Leaving_Moon_221205_1735009
- Foto Luna llena (ya incluida en `luna/src/`): NASA/GSFC, GSFC_20171208_Archive_e001861

## Próximos pasos posibles
1. Probar el motor con temas nuevos (ver ideas en la conversación / GUIA_ESTILO.md).
2. Otros temas de la NASA (planetas, Sol, ISS, eclipses): revisar primero con `python3 video/video_stipple.py VIDEO x.mp4 --analizar`.

## Notas
- Las fases están orientadas para el hemisferio norte (creciente iluminada a la derecha).
- Desde la nube, Wikimedia limita descargas de video y Pexels/Pixabay bloquean descargas automáticas; la NASA funciona.

## En curso
- Ciclo del agua v9 (`agua/ciclo_agua7.py`, borrador): el tiempo se ve (túnel del tiempo, reloj de arena + contador de
  años en el mar, cambios de estado marcados, reloj de días en la nube, círculo de ciclo al final).
