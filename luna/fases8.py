"""Las 8 fases de la Luna en puntillismo (B/N, 1080x1920).

Híbrido: la textura es una foto real de la Luna llena (NASA, dominio público) y la iluminación de cada fase
la calcula este script (esfera + dirección del Sol). Los puntos se mueven con coherencia temporal.

    python3 fases8.py salida_sin_textos.mp4      # luego: textos con componer_textos()
"""
import sys, os, subprocess, numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "video"))
import video_stipple as V
import estilo as E                                     # tiempos y ajustes aprobados

W, H, FPS, K = 1080, 1920, 24, 2
GW, GH = W//K, H//K                                   # grilla de densidad
CX, CY, R = 540, 900, 390                              # Luna en el video final (px)
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))

# ---------- textura (albedo) desde la foto ----------
def cargar_textura(path=os.path.join(os.path.dirname(__file__), "src", "luna_llena_nasa.jpg"), n=900):
    g = np.asarray(Image.open(path).convert("L"), float)/255
    ys, xs = np.nonzero(g > 0.08)
    cx, cy = (xs.min()+xs.max())/2, (ys.min()+ys.max())/2; r = (xs.max()-xs.min() + ys.max()-ys.min())/4
    crop = Image.fromarray((g*255).astype(np.uint8)).crop((cx-r, cy-r, cx+r, cy+r)).resize((n, n), Image.LANCZOS)
    t = np.asarray(crop, float)/255
    yy, xx = (np.mgrid[0:n, 0:n] + 0.5)/n*2 - 1; rr = np.hypot(xx, yy)
    mu = np.sqrt(np.clip(1 - rr**2, 0, 1))
    t = t/np.clip(0.55 + 0.45*mu, 0.3, 1)               # quita el leve oscurecimiento del borde de la foto
    return np.clip(t/np.percentile(t[rr < 0.97], 99.5), 0, 1)
TEX = cargar_textura(); TN = TEX.shape[0]

# ---------- iluminación de una fase ----------
CONTRASTE_BASE = E.CONTRASTE_BASE
yy, xx = np.mgrid[0:GH, 0:GW]
def luna(phi, escala=1.0, luz=1.0, ceniza=E.CENIZA):
    """phi: 0 = nueva, pi/2 = cuarto creciente, pi = llena, 3pi/2 = cuarto menguante (hemisferio norte)."""
    r = R*escala/K
    x = (xx + 0.5 - CX/K)/max(r, 1e-3); y = (yy + 0.5 - CY/K)/max(r, 1e-3)
    rr2 = x*x + y*y; dentro = rr2 < 1
    z = np.sqrt(np.clip(1 - rr2, 0, 1))
    L = np.array([np.sin(phi), 0.0, -np.cos(phi)])
    mu0 = x*L[0] + z*L[2]                                 # coseno del ángulo con el Sol
    dia = ss(-0.03, 0.12, mu0)*(0.45 + 0.55*np.sqrt(np.clip(mu0, 0, 1)))
    u = np.clip(((x + 1)/2*TN).astype(int), 0, TN-1); v = np.clip(((y + 1)/2*TN).astype(int), 0, TN-1)
    alb = CONTRASTE_BASE + (1 - CONTRASTE_BASE)*TEX[v, u]  # contraste intermedio: los mares se notan sin dejar huecos
    img = alb*(luz*dia + ceniza*(1 - ss(-0.03, 0.12, mu0)))   # luz cenicienta en la parte oscura
    borde = ss(1.0, 0.985, np.sqrt(rr2))                   # borde suave del disco
    return np.where(dentro, img*borde, 0.0)

# ---------- guion ----------
FASES = ["LUNA NUEVA", "CRECIENTE", "CUARTO CRECIENTE", "GIBOSA CRECIENTE",
         "LUNA LLENA", "GIBOSA MENGUANTE", "CUARTO MENGUANTE", "MENGUANTE"]
T_GANCHO, T_APAGA, T_CICLO = E.GANCHO_INICIO, E.GANCHO_FIN, E.ACCION_INICIO
SEG, QUIETO = E.ETAPA, E.ETAPA_QUIETA
SEG_ULT, QUIETO_ULT = E.ETAPA_FINAL, E.ETAPA_FINAL_QUIETA
T_FIN_CICLO = T_CICLO + 7*SEG + SEG_ULT
DUR = T_FIN_CICLO + E.CIERRE

def estado(t):
    """(phi, escala, luz, indice de fase o None)."""
    if t < T_APAGA:
        return np.pi, 0.02 + 0.98*(1 - (1 - ss(T_GANCHO, E.GANCHO_FORMADO, t))**1.6), 1.0, None
    if t < T_CICLO:                                       # la luz se apaga: queda la luz cenicienta
        return np.pi, 1.0, 1 - ss(T_APAGA, T_CICLO - 0.2, t), None
    if t < T_FIN_CICLO:
        k = min(int((t - T_CICLO)//SEG), 7); tt = (t - T_CICLO) - k*SEG
        q, s_ = (QUIETO, SEG) if k < 7 else (QUIETO_ULT, SEG_ULT)
        return k*np.pi/4 + np.pi/4*ss(q, s_, tt), 1.0, 1.0, k
    return np.pi, 1.0, ss(T_FIN_CICLO, T_FIN_CICLO + E.REMATE_FORMA, t), None          # se vuelve a formar la Luna llena

def textos():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "video"))
    from textos import Texto
    T = [Texto("¿SABÍAS QUE LA LUNA", 0.5, 4.4, y=230, tam=42), Texto("TIENE 8 FASES?", 1.1, 4.6, y=295, tam=42)]
    for k, nombre in enumerate(FASES):
        t0 = T_CICLO + k*SEG - 0.1
        T.append(Texto(nombre, t0, t0 + (QUIETO if k < 7 else QUIETO_ULT) + 0.6, y=1430, tam=34))
    T += [Texto("UN CICLO COMPLETO", T_FIN_CICLO - E.REMATE_TEXTO_ANTES, DUR - 1.3, y=230, tam=36),
          Texto("DURA 29,5 DÍAS", T_FIN_CICLO + 0.1, DUR - 1.2, y=290, tam=36)]
    return T

# ---------- render ----------
rng_i = np.random.default_rng(11)
def indicador(buf, t):
    """Fila de 8 puntitos: la fase actual brilla."""
    if t < T_CICLO - 0.6 or t > T_FIN_CICLO + 0.6: return
    e = ss(T_CICLO - 0.6, T_CICLO, t)*(1 - ss(T_FIN_CICLO, T_FIN_CICLO + 0.6, t))
    pos = (t - T_CICLO)/SEG                                # avance continuo entre fases
    for k in range(8):
        x = W/2 + (k - 3.5)*38; cerca = np.clip(1 - abs(pos - k - 0.18), 0, 1)**2
        x = W/2 + (k - 3.5)*44
        r = 2.5 + 9*cerca; a = np.linspace(0, 2*np.pi, 28, endpoint=False)
        V.splat(buf, x + r*np.cos(a), 1530 + r*np.sin(a), np.full(28, e*(0.15 + 0.95*cerca)))   # anillo
        rd = 4.5*cerca; b = rng_i.uniform(0, 2*np.pi, 14); q = rd*np.sqrt(rng_i.uniform(0, 1, 14))
        V.splat(buf, x + q*np.cos(b), 1530 + q*np.sin(b), np.full(14, e*1.2*cerca))            # relleno de la actual
        V.splat(buf, np.array([x]), np.array([1530.0]), np.array([e*(0.45 + 1.8*cerca)]))

class A:                                                  # parámetros de densidad (como en video_stipple)
    invertir = False; aislar = 0; negro = 0.0; gamma = E.GAMMA; bordes = E.BORDES

def main(out):
    rng = np.random.default_rng(3); MX = E.PUNTOS_MAX
    st = V.Stippler(MX, GH, GW); big = rng.uniform(size=MX) < 0.2; tw = rng.uniform(0, 6.28, MX)
    sx, sy = rng.uniform(0, W, 200), rng.uniform(0, H, 200); sb = rng.uniform(.15, .7, 200)**2; sp = rng.uniform(0, 6.28, 200)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "15", out], stdin=subprocess.PIPE)
    nprev = None; esc_prev = 1.0; total = int(DUR*FPS)
    for f in range(total):
        t = f/FPS; phi, esc, luz, _ = estado(t)
        g = luna(phi, esc, luz)
        gy, gx = np.gradient(V.blur(V.blur(g))); edge = np.clip(np.hypot(gx, gy)*A.bordes, 0, 1)
        d = np.clip(g, 0, 1)**A.gamma + 0.3*edge + 1e-5
        n = int(np.clip(d.sum()*0.33, 800, MX)); n = n if nprev is None else int(nprev + 0.3*(n - nprev)); nprev = n
        if st.pts is not None and esc != esc_prev:              # la Luna crece: los puntos se expanden desde el centro
            c = np.array([CX/K, CY/K]); st.pts = c + (st.pts - c)*(esc/esc_prev)
        esc_prev = esc
        pts, lum = st.step(d, 3, n); nn = len(pts)
        ln = np.clip(lum/max(np.percentile(lum, 97), 0.05), 0, 1)
        w = (E.TONO_MIN + (1 - E.TONO_MIN)*ln**1.1)*(0.92 + 0.08*np.sin(t*3 + tw[:nn]))*3.6
        sm = np.zeros((H, W)); bg = np.zeros((H, W)); bb = big[:nn]
        V.splat(sm, pts[~bb, 0], pts[~bb, 1], w[~bb]); V.splat(bg, pts[bb, 0], pts[bb, 1], w[bb])
        V.splat(sm, sx, sy, sb*(0.6 + 0.4*np.sin(t*1.5 + sp))*3*ss(0, 2, t))
        indicador(sm, t)
        img = (sm + 2.2*V.blur(bg))*min(1, (DUR - t)/E.FUNDIDO_FINAL)
        p.stdin.write((np.clip(img, 0, 1)*255).astype(np.uint8).tobytes())
        if f % 48 == 0: print(f"{f}/{total}", flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main(sys.argv[1])
