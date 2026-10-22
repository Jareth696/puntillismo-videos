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

# =====================================================================================================
# Segunda tanda (muestra en muestras/muestras_movimientos_2.mp4)
# =====================================================================================================

# ---------- globo que gira: esfera de puntos con textura ----------
def esfera(n=30000, seed=0):
    """Puntos repartidos parejo sobre una esfera de radio 1 (espiral de Fibonacci)."""
    i = np.arange(n) + 0.5; lat = np.arcsin(1 - 2*i/n); lon = (i*2.39996) % (2*np.pi)
    return lat, lon

def globo(lat, lon, brillo, rot, c, R, inclina=0.25, luz=(-0.5, -0.3, -0.8)):
    """Esfera que gira (rot en rad) e inclinada; solo se ve la cara de adelante, con luz suave de costado."""
    x = np.cos(lat)*np.sin(lon + rot); y = -np.sin(lat); z = -np.cos(lat)*np.cos(lon + rot)
    y, z = y*np.cos(inclina) - z*np.sin(inclina), y*np.sin(inclina) + z*np.cos(inclina)
    L = np.array(luz)/np.linalg.norm(luz); sombra = np.clip(0.25 + 0.95*(x*L[0] + y*L[1] + z*L[2]), 0.12, 1)
    vis = z < 0.05
    return c[0] + R*x[vis], c[1] + R*y[vis], (brillo*sombra)[vis]

# ---------- lupa: un círculo que agranda lo que pasa por debajo ----------
def lupa(P, centro, r, zoom, aro=True):
    """Dentro del círculo los puntos se ven agrandados (zoom) alrededor del centro; afuera, igual pero más tenue."""
    dx = P[:, 0] - centro[0]; dy = P[:, 1] - centro[1]
    gx, gy = centro[0] + dx*zoom, centro[1] + dy*zoom
    dentro = np.hypot(gx - centro[0], gy - centro[1]) < r
    fuera = np.hypot(dx, dy) >= r
    x = np.r_[P[fuera, 0], gx[dentro]]; y = np.r_[P[fuera, 1], gy[dentro]]
    w = np.r_[P[fuera, 2]*0.55, P[dentro, 2]*1.3*zoom**0.6]
    if aro:
        a = np.linspace(0, 2*np.pi, 360, endpoint=False)
        x = np.r_[x, centro[0] + r*np.cos(a), centro[0] + (r + 5)*np.cos(a)]; y = np.r_[y, centro[1] + r*np.sin(a), centro[1] + (r + 5)*np.sin(a)]
        w = np.r_[w, np.full(360, 1.0), np.full(360, 0.4)]
    return x, y, w

# ---------- desintegración en el viento ----------
def desintegrar(P, k, frente_x0, frente_x1, viento=(1.0, -0.35), seed=0):
    """Un frente avanza (de frente_x0 a frente_x1) y los puntos que pasa se van volando con el viento.
    k: 0 = entero, 1 = todo volado. Si k vuelve a 0, se rearma (los puntos regresan)."""
    r = np.random.default_rng(seed); n = len(P)
    turb = r.uniform(0.6, 1.4, n); fase = r.uniform(0, 6.28, n)
    fx = frente_x0 + (frente_x1 - frente_x0)*k
    d = np.clip((fx - P[:, 0])/max(abs(frente_x1 - frente_x0), 1)*np.sign(frente_x1 - frente_x0), 0, None)
    vuelo = d*1400*turb
    x = P[:, 0] + vuelo*viento[0] + 40*np.sin(vuelo/90 + fase)*np.minimum(d*6, 1)
    y = P[:, 1] + vuelo*viento[1] + 30*np.cos(vuelo/70 + fase)*np.minimum(d*6, 1)
    return x, y, P[:, 2]*np.exp(-d*2.2)

# ---------- línea que se dibuja ----------
def trazar(puntos, k, paso=3.0, b=0.8):
    """Polilínea que se dibuja de a poco (k: 0..1) con una punta brillante."""
    p = np.asarray(puntos, float); seg = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    s = np.arange(0, seg[-1]*np.clip(k, 0, 1), paso)
    x = np.interp(s, seg, p[:, 0]); y = np.interp(s, seg, p[:, 1])
    w = np.full(len(s), b)
    if 0 < k < 1 and len(s): x = np.r_[x, x[-1]]; y = np.r_[y, y[-1]]; w = np.r_[w, 3.0]
    return x, y, w

# ---------- onda expansiva sobre una superficie ----------
def superficie_onda(t, t0, centro=(0.0, 0.0), lado=900.0, paso=14.0, vel=420.0, pitch=0.95, c=(540.0, 1000.0)):
    """Superficie de puntos en perspectiva con anillos que se abren desde 'centro' a partir de t0."""
    g = np.arange(-lado, lado + 1, paso); X, Z = np.meshgrid(g, g); X = X.ravel(); Z = Z.ravel()
    r = np.hypot(X - centro[0], Z - centro[1]); dt = max(t - t0, 0); frente = vel*dt
    amp = 38*np.exp(-dt*0.7)*np.exp(-((r - frente)/140)**2)*(dt > 0)
    Hh = amp*np.sin((r - frente)/38)
    sx, sy, f = ver_tela(X, Hh, Z, pitch, c)
    w = 0.8*np.clip(f, 0.3, 1.3)*(1 + 2.5*np.abs(Hh)/38)*(1 - ss(lado*0.7, lado, np.maximum(np.abs(X), np.abs(Z))))
    return sx, sy, w

# ---------- puntos que cuentan ----------
def grilla_contadora(n, cols, cx, cy, paso, k):
    """n puntos en grilla que se encienden en orden (k: 0..1). Devuelve x, y, w y el índice del último encendido."""
    i = np.arange(n); x = cx + (i % cols - (cols - 1)/2)*paso; y = cy + (i//cols - (n//cols - 1)/2)*paso
    on = i < k*n; w = np.where(on, 1.5, 0.1)
    return x, y, w, int(k*n)
