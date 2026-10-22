"""Genera los videos finales, listos para publicar, en finales/.

    python3 hacer_finales.py                 # los 4
    python3 hacer_finales.py luna galileo    # solo algunos

Para cada video: dibuja los puntos (sin textos), pone los textos con el sello de títulos y lo comprime para Reels
(1080x1920, H.264, inicio rápido). Los archivos intermedios quedan en trabajo/ (no van al repositorio).
"""
import os, sys, subprocess, time

RAIZ = os.path.dirname(os.path.abspath(__file__))
TRABAJO = os.path.join(RAIZ, "trabajo"); FINALES = os.path.join(RAIZ, "finales")
VIDEOS = {                      # nombre: (carpeta, script, archivo final)
    "luna":    ("luna",    "fases8.py",      "01_luna_8_fases.mp4"),
    "agua":    ("agua",    "ciclo_agua7.py", "02_ciclo_del_agua.mp4"),
    "darwin":  ("darwin",  "evolucion.py",   "03_darwin_evolucion.mp4"),
    "galileo": ("galileo", "galileo.py",     "04_galileo.mp4"),
}

def hacer(nombre):
    carpeta, script, final = VIDEOS[nombre]
    sin = os.path.join(TRABAJO, f"{nombre}_sin_textos.mp4"); con = os.path.join(TRABAJO, f"{nombre}_con_textos.mp4")
    cwd = os.path.join(RAIZ, carpeta); t0 = time.time()
    print(f"[{nombre}] dibujando puntos...", flush=True)
    if nombre == "luna":                                   # fases8 tiene su propio main (solo el video sin textos)
        subprocess.run([sys.executable, script, sin], cwd=cwd, check=True)
        codigo = ("import sys; sys.path.insert(0, '../video'); import fases8 as F; from textos import componer; "
                  f"componer({sin!r}, {con!r}, F.textos())")
        subprocess.run([sys.executable, "-c", codigo], cwd=cwd, check=True)
    else:
        subprocess.run([sys.executable, script, sin, "0", con], cwd=cwd, check=True)
    print(f"[{nombre}] comprimiendo para publicar...", flush=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", con, "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", os.path.join(FINALES, final)], check=True)
    print(f"[{nombre}] listo: finales/{final} ({time.time() - t0:.0f} s)", flush=True)

if __name__ == "__main__":
    os.makedirs(TRABAJO, exist_ok=True); os.makedirs(FINALES, exist_ok=True)
    for n in (sys.argv[1:] or list(VIDEOS)):
        hacer(n)
