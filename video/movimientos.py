"""Movimientos de plano y cámara en 3D para nubes de puntos (biblioteca del motor, ver BIBLIOTECA.md sección 7).

Todos trabajan con puntos (n, 3): x, y en pantalla y brillo. Devuelven (x, y, w) listos para `splat`.
Muestra de todos: muestras/muestras.py
"""
import numpy as np

D = 1500.0                                   # distancia de la cámara (perspectiva)
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))

def proyectar(X, Y, Z, c=(540.0, 960.0)):
    """Mundo 3D (centrado en c, Z hacia adentro de la pantalla) -> pantalla. Devuelve x, y y el factor f."""
    f = D/np.maximum(D + Z, 1.0); return c[0] + X*f, c[1] + Y*f, f

def borde_rect(cx, cy, ax, ay, paso=5.0, b=0.6):
    """Contorno de una tarjeta o página (puntos)."""
    xs = np.arange(-ax, ax, paso); ys = np.arange(-ay, ay, paso)
    P = np.r_[np.c_[xs, np.full(len(xs), -ay)], np.c_[xs, np.full(len(xs), ay)],
              np.c_[np.full(len(ys), -ax), ys], np.c_[np.full(len(ys), ax), ys]]
    return np.c_[P[:, 0] + cx, P[:, 1] + cy, np.full(len(P), b)]

# ---------- tarjeta que gira ----------
def tarjeta(A, B, ang, c, tilt=0.25, borde=None):
    """A de frente, B en el dorso. ang: 0 = se ve A, pi = se ve B. Mientras gira, la tarjeta se inclina un poco
    (tilt) para que se note el 3D. borde: contorno de la tarjeta (se ve de los dos lados)."""
    out = []
    capas = [(A, 0.0, True), (B, np.pi, True)] + ([(borde, 0.0, False)] if borde is not None else [])
    for P, extra, cara in capas:
        x = P[:, 0] - c[0]; y = P[:, 1] - c[1]; th = ang + extra
        X = x*np.cos(th); Z = -x*np.sin(th) + y*tilt*np.sin(ang)
        sx, sy, f = proyectar(X, y, Z, c)
        w = P[:, 2]*(0.55 + 0.45*abs(np.cos(ang)))*((np.cos(th) > 0) if cara else 1.0)
        out.append(np.c_[sx, sy, w])
    Q = np.concatenate(out); return Q[:, 0], Q[:, 1], Q[:, 2]

# ---------- pliegue de página ----------
def pagina(A, B, k, c, ax, ay):
    """Pasar la página: A queda debajo a la izquierda, la mitad derecha gira sobre el lomo (x = c[0]) y al
    terminar se ve B completa. k: 0..1."""
    th = np.pi*ss(0, 1, k); out = []
    xa, xb = A[:, 0] - c[0], B[:, 0] - c[0]
    izqA = xa < 0; derA = ~izqA; izqB = xb < 0; derB = ~izqB
    out.append(np.c_[A[izqA, 0], A[izqA, 1], A[izqA, 2]*(1 - ss(0.85, 1.0, k))])        # A izquierda (se tapa)
    out.append(np.c_[B[derB, 0], B[derB, 1], B[derB, 2]*ss(0.0, 0.5, k)])                # B derecha (se destapa)
    for P, m, dorso in ((A, derA, False), (B, izqB, True)):                              # la hoja que gira
        x = P[m, 0] - c[0]; y = P[m, 1] - c[1]
        if dorso: X = -x*np.cos(th); Z = x*np.sin(th)
        else: X = x*np.cos(th); Z = -x*np.sin(th)
        sx, sy, f = proyectar(X, y, Z*0.6, c)
        vis = (np.cos(th) < 0) if dorso else (np.cos(th) > 0)
        out.append(np.c_[sx, sy, P[m, 2]*vis*(0.6 + 0.4*abs(np.cos(th)))])
    Q = np.concatenate(out); return Q[:, 0], Q[:, 1], Q[:, 2]

# ---------- mesa que se inclina ----------
def inclinar(P, alfa, eje_y, c, giro=0.0):
    """La imagen se acuesta hacia atrás girando sobre la línea y = eje_y (alfa en rad); giro: la cámara rodea."""
    x = P[:, 0] - c[0]; y = P[:, 1] - eje_y
    Y = y*np.cos(alfa); Z = -y*np.sin(alfa)
    X = x*np.cos(giro) + Z*np.sin(giro); Z = -x*np.sin(giro) + Z*np.cos(giro)
    sx, sy, f = proyectar(X, Y, Z, (c[0], eje_y))
    return sx, sy, P[:, 2]*np.clip(f, 0.3, 1.4)

# ---------- tela que se hunde ----------
def tela(hundir, pozo=(0.0, 0.0), ancho=260.0, lado=900.0, paso=60.0, fino=6.0, pitch=0.95, c=(540.0, 1000.0)):
    """Malla de líneas de puntos vista desde arriba en perspectiva, hundida por un objeto pesado.
    Devuelve (x, y, w) y una función alto(X, Z) para apoyar cosas sobre la tela."""
    g = np.arange(-lado, lado + 1, paso); s = np.arange(-lado, lado + 1, fino)
    X = np.r_[np.repeat(g, len(s)), np.tile(s, len(g))]; Zs = np.r_[np.tile(s, len(g)), np.repeat(g, len(s))]
    alto = lambda X, Z: hundir*np.exp(-((X - pozo[0])**2 + (Z - pozo[1])**2)/(2*ancho**2))
    Hh = alto(X, Zs)
    sx, sy, f = ver_tela(X, Hh, Zs, pitch, c)
    w = 0.9*np.clip(f, 0.3, 1.3)*(1 - ss(lado*0.7, lado, np.maximum(np.abs(X), np.abs(Zs))))
    return (sx, sy, w), alto

def ver_tela(X, Hh, Z, pitch=0.95, c=(540.0, 1000.0)):
    """Punto de la tela (X, hundimiento, Z) -> pantalla, con la cámara mirando hacia abajo (pitch)."""
    Yc = Hh*np.cos(pitch) - Z*np.sin(pitch); Zc = Z*np.cos(pitch) + Hh*np.sin(pitch)
    return proyectar(X, Yc, Zc, c)

# ---------- campo de flujo: líneas de un dipolo (imán, campo magnético de la Tierra) ----------
def lineas_dipolo(Ls, n=400, inclina=0.0):
    """Líneas r = L sin²θ a ambos lados. Devuelve una lista de polilíneas (k, 2) centradas en 0,0."""
    th = np.linspace(0.12, np.pi - 0.12, n); out = []
    for L in Ls:
        r = L*np.sin(th)**2
        for lado in (-1, 1):
            x = lado*r*np.sin(th); y = -r*np.cos(th)
            c, s = np.cos(inclina), np.sin(inclina); out.append(np.c_[x*c - y*s, x*s + y*c])
    return out

def particulas_en_lineas(lineas, t, por_linea=14, vel=0.18, seed=0):
    """Partículas que viajan por las líneas (sur -> norte), sin estado: dependen solo de t."""
    r = np.random.default_rng(seed); xs, ys = [], []
    for L in lineas:
        seg = np.r_[0, np.cumsum(np.hypot(*np.diff(L, axis=0).T))]
        u = (t*vel + r.uniform(0, 1, por_linea)) % 1*seg[-1]
        xs.append(np.interp(u, seg, L[:, 0])); ys.append(np.interp(u, seg, L[:, 1]))
    return np.concatenate(xs), np.concatenate(ys)

# ---------- paralaje: cordilleras por capas ----------
def cordillera(seed, alto, base, n=9000, rugosidad=1.0, ancho=3000.0):
    """Perfil de montañas (línea brillante) + relleno de puntos que se apaga hacia abajo."""
    r = np.random.default_rng(seed); xs = np.linspace(-ancho/2, ancho/2, 1500)
    perfil = base - alto*(0.55 + 0.45*np.sin(xs/260*rugosidad + r.uniform(0, 6)))*(0.7 + 0.3*np.sin(xs/97 + r.uniform(0, 6)))
    linea = np.c_[xs, perfil, np.full(len(xs), 0.9)]
    x = r.uniform(-ancho/2, ancho/2, n); p = np.interp(x, xs, perfil); d = r.exponential(90, n)
    return np.r_[linea, np.c_[x, p + d, 0.5*np.exp(-d/120)]]
