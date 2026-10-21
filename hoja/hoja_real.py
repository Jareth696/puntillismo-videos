"""Hoja REAL (textura de video) — Puntillismo B/N v2: hoja 3D con nervaduras, vuela, aterriza, llueve. Fondo negro, puntos blancos."""
import sys, subprocess, numpy as np

W, H, FPS, DUR, SC = 720, 1280, 24, 32, 1.5      # diseño en 720x1280, salida 1080x1920
OW, OH = int(W*SC), int(H*SC)
rng = np.random.default_rng(11)
ss = lambda a, b, x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a), 0, 1))
PHI = 0.5; CP, SP = np.cos(PHI), np.sin(PHI); Y0 = 1160.0
T_FLY, T_LAND, T_RAIN = 3.8, 20.3, 19.8
TRAV = 2650.0

# ---------- hoja 3D ----------
HL = 95.0; LS = HL/175.0                                        # semilargo en px
def Wd(u): return LS*78*np.clip(np.sin(np.pi*(np.clip(u,-1,1)+1)/2), 0, 1)**0.8*(1-0.38*np.clip(u,-1,1))*(1+0.04*np.abs(np.sin(19*u)))
def zsurf(u, v):
    return LS*(22*u**2 + 20*v**2*(0.5+0.5*(1-u)) + 7*v**2*np.sin(u*7) + 5*np.sin(u*2.6+v))
def leaf_pts():
    """Hoja REAL: textura de nervaduras extraída de un video (elementos/hoja_textura.png), convertida a puntos
    con Voronoi (como Tesla) sobre la forma de nuestra hoja. Se agregan borde, nervio central y rabillo."""
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tesla"))
    import stipple
    from PIL import Image
    T = np.asarray(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "elementos", "hoja_textura.png")), float)/255
    F, C = T.shape
    esc = 4.0                                           # resolución del mapa de densidad (px por px de pantalla)
    Hh, Ww = int(2*HL*esc), int(2*Wd(np.linspace(-1, 1, 400)).max()*esc) + 4
    yy, xx = np.mgrid[0:Hh, 0:Ww]
    u = (xx*0 + yy)/(Hh - 1)*2 - 1                       # filas = largo (u), columnas = ancho
    w = Wd(u)*esc; v = (xx - Ww/2)/np.maximum(w, 1e-3); m = np.abs(v) <= 1
    tex = np.zeros_like(u)
    fi = np.clip(((u + 1)/2*(F - 1)).astype(int), 0, F - 1); ci = np.clip(((v + 1)/2*(C - 1)).astype(int), 0, C - 1)
    tex[m] = T[fi[m], ci[m]]
    tex = np.maximum(tex, m*np.exp(-(v/0.035)**2)*0.95)  # nervio central marcado
    dens = (0.05 + 0.95*tex)**2.0*m
    pts, _ = stipple.voronoi(dens, 8500, 30, 4)
    pu = pts[:, 1]/(Hh - 1)*2 - 1; pv = (pts[:, 0] - Ww/2)/np.maximum(Wd(pu)*esc, 1e-3)
    pv = np.clip(pv, -0.995, 0.995)
    tone = tex[np.clip(pts[:, 1].astype(int), 0, Hh-1), np.clip(pts[:, 0].astype(int), 0, Ww-1)]
    U = [pu]; V = [pv]; TN = [np.clip(tone*1.2, 0, 1)]; K = [np.zeros(len(pu))]
    ue = np.linspace(-1, 1, 750)                       # borde
    for s_ in (1, -1): U.append(ue); V.append(np.full_like(ue, s_)); TN.append(np.ones_like(ue)); K.append(np.full_like(ue, 1))
    um = np.linspace(-1.28, -1.0, 60)                    # rabillo
    U.append(um); V.append(np.zeros_like(um)); TN.append(np.ones_like(um)); K.append(np.full_like(um, 2))
    return np.concatenate(U), np.concatenate(V), np.concatenate(TN), np.concatenate(K)
lu, lv, ltone, lkind = leaf_pts()
NL = len(lu)
lx = lu*HL
ly = np.where(lu < -1, lv*1.5*LS, lv*Wd(lu))
ly = np.where(lu < -1, (lu+1)**2*14*LS, ly)       # rabillo curvo
lz = zsurf(np.clip(lu,-1.3,1), lv*(lu >= -1))
LOC = np.c_[lx, ly, lz]
# normales locales por diferencias finitas
e = 1e-3
dzu = (zsurf(np.clip(lu+e,-1.3,1), lv) - zsurf(np.clip(lu-e,-1.3,1), lv))/(2*e*HL)
dzv = (zsurf(np.clip(lu,-1.3,1), np.clip(lv+e,-1,1)) - zsurf(np.clip(lu,-1.3,1), np.clip(lv-e,-1,1)))/(2*e*np.maximum(Wd(lu), 6))
NRM = np.c_[-dzu, -dzv, np.ones(NL)]; NRM /= np.linalg.norm(NRM, axis=1, keepdims=True)
start = rng.normal(0, 1, (NL, 2))*[330, 520] + [360, 560]
delay = rng.uniform(0, 1, NL)
big = rng.uniform(size=NL) < np.where(lkind > 0, 0.55, 0.30)
rnd_ph = rng.uniform(0, 6.28, NL)

def Rx(a): c,s=np.cos(a),np.sin(a); o,z=np.ones_like(a),np.zeros_like(a); return np.stack([np.stack([o,z,z],-1),np.stack([z,c,-s],-1),np.stack([z,s,c],-1)],-2)
def Ry(a): c,s=np.cos(a),np.sin(a); o,z=np.ones_like(a),np.zeros_like(a); return np.stack([np.stack([c,z,s],-1),np.stack([z,o,z],-1),np.stack([-s,z,c],-1)],-2)
def Rz(a): c,s=np.cos(a),np.sin(a); o,z=np.ones_like(a),np.zeros_like(a); return np.stack([np.stack([c,-s,z],-1),np.stack([s,c,z],-1),np.stack([z,z,o],-1)],-2)
M0 = np.array([[1,0,0],[0,0,1],[0,1,0]], float)         # local (x,y,z) -> mundo (X, Y=z, Z=y)
LIGHT = np.array([0.5, 0.75, -0.45]); LIGHT /= np.linalg.norm(LIGHT)

def trav(u): return TRAV*(0.5*u + 0.5*u*u*(3-2*u))
def cam(t):
    u = np.clip((np.asarray(t, float)-T_FLY)/(T_LAND-T_FLY), 0, 1); return trav(u)
def pose(t):
    t = np.atleast_1d(np.asarray(t, float)); u = np.clip((t-T_FLY)/(T_LAND-T_FLY), 0, 1)
    amp = (0.28 + 0.72*ss(0, 0.10, u))*(1-ss(0.82, 1.0, u))
    X = 360 + trav(u) + 130*np.sin(2*np.pi*3.5*u)*(1-ss(.8, 1, u))
    Ycr = 780 - 215*ss(0, 0.18, u) + 75*np.sin(2*np.pi*4.5*u)*(1-ss(.7, 1, u))
    Y = np.maximum(Ycr*(1-ss(0.64, 1.0, u))**1.05 + 12*np.sin(t*2.2)*(1-ss(0, .1, u)), 3)
    Z = 110*np.sin(2*np.pi*1.5*u+0.5)*(1-ss(.7, 1, u)) - 70*ss(.6, 1, u)
    roll = -0.85*amp*np.cos(2*np.pi*3.5*u) + 0.15*amp*np.sin(t*3)
    pitch = 0.7*amp*np.sin(2*np.pi*7*u+0.6) + 0.1*amp*np.sin(t*2.3)
    yaw = 0.35 + amp*(1.9*np.sin(2*np.pi*1.8*u) + 2.6*u)
    R = Ry(yaw) @ Rz(roll) @ Rx(pitch) @ M0
    return np.stack([X, Y, Z], -1), R, u

def project(P, cx=0.0):
    sc = 1/(1 - P[..., 2]*0.0006)
    return 360 + (P[..., 0]-cx-360)*sc, Y0 - (P[..., 1]*CP + P[..., 2]*SP)*sc, sc

# ---------- entorno por capas (paralaje): par -> puntos en x de mundo ----------
CAMMAX = TRAV; WW = CAMMAX + W + 80
LAY = {}
def add(par, x, y, b, sw=0.0):
    x = np.asarray(x, float); LAY.setdefault(par, []).append(np.c_[x, np.broadcast_to(y, x.shape), np.broadcast_to(b, x.shape), np.broadcast_to(sw, x.shape)])
def stipple_line(xs, ys, dens, depth, level):
    X, Y, B = [], [], []
    for x, y in zip(xs, ys):
        k = rng.poisson(dens)
        X.append(x+rng.normal(0, 0.8, k)); Y.append(y + rng.uniform(0, 1, k)**2.0*depth); B.append(np.full(k, level)*rng.uniform(.5, 1, k))
    return np.concatenate(X), np.concatenate(Y), np.concatenate(B)
def fnoise(x, seed, octs):
    r = np.random.default_rng(seed); out = np.zeros_like(x)
    for per, amp in octs:
        k = r.normal(0, 1, int(x.max()/per)+3); i = (x/per).astype(int); f = x/per - i; f = f*f*(3-2*f)
        out += amp*(k[i]*(1-f) + k[i+1]*f)
    return out
for par, base, hgt, lvl, seed, gap in ((0.22, Y0-60, 420, 0.34, 3, 300), (0.5, Y0-40, 170, 0.44, 9, 170)):
    hx = np.linspace(0, CAMMAX*par+W+80, int((CAMMAX*par+W+80)/1.2))
    n_ = fnoise(hx, seed, ((260, 1.0), (90, 0.45), (30, 0.18), (11, 0.07)))
    rp = np.random.default_rng(seed+1); pk = np.arange(-gap, hx.max()+gap, gap) + rp.uniform(-0.3, 0.3, int((hx.max()+2*gap)/gap)+1)[:len(np.arange(-gap, hx.max()+gap, gap))]*gap
    ph_ = rp.uniform(0.45, 1.0, len(pk)); pw = rp.uniform(0.5, 0.8, len(pk))*gap
    prof = np.max([h_*np.clip(1-np.abs(hx-p_)/w_, 0, 1)**1.25 for p_, h_, w_ in zip(pk, ph_, pw)], axis=0)
    ridge = base - hgt*np.clip(prof*(1+0.12*n_) + 0.06*n_ + 0.08, 0.04, 1.2)
    slope = np.gradient(ridge, hx)
    lit = np.clip(0.5 - slope*2.2, 0.15, 1)                      # ladera hacia la luna = más clara
    X_, Y_, B_ = [], [], []
    for x, y, l in zip(hx, ridge, lit):
        k = rng.poisson(1.6 + 3.5*l)
        d = rng.uniform(0, 1, k)**2.3*(base+10-y)
        X_.append(x + rng.normal(0, .6, k)); Y_.append(y + d); B_.append(lvl*l*(1-0.75*d/(base+10-y+1))*rng.uniform(.6, 1, k))
    add(par, np.concatenate(X_), np.concatenate(Y_), np.concatenate(B_))
    add(par, hx, ridge, lvl*1.3*(0.55+0.45*lit))                  # línea de cresta
nG = int(9000*WW/W)
gx = rng.uniform(0, WW, nG); gy = Y0 - 18 + rng.uniform(0, 1, nG)**1.6*190
add(1.0, gx, gy, 0.55*np.clip(1-(gy-Y0)/200, .12, 1)*rng.uniform(.5, 1, nG))
for x0 in rng.uniform(0, WW, int(55*WW/W)):
    for _ in range(4):
        a_ = rng.uniform(-0.6, 0.6); h = rng.uniform(18, 62); kk = np.linspace(0, 1, int(h/2.5))
        add(1.0, x0+a_*h*kk**2*1.4, Y0-14-h*kk, 0.8*(1-0.4*kk), (kk*h/60)**1.5)
mx, my = [], []
while len(mx) < 1500:
    a_ = rng.uniform(0, 6.28); r = 52*np.sqrt(rng.uniform()); x, y = r*np.cos(a_), r*np.sin(a_)
    if np.hypot(x-24, y-8) > 44: mx.append(x+575); my.append(y+160)
add(0.03, mx, my, rng.uniform(.6, 1, len(mx)))
ha = rng.uniform(0, 6.28, 1400); hr = 56 + rng.exponential(28, 1400)
add(0.03, 575+hr*np.cos(ha), 160+hr*np.sin(ha), 0.22*np.exp(-(hr-56)/45))
def tree(x, y, ang, ln, depth):
    n = max(int(ln/2.2), 2); t = np.linspace(0, 1, n)
    xs = x + np.sin(ang)*ln*t; ys = y - np.cos(ang)*ln*t
    for _ in range(4 if depth > 3 else 2): add(1.0, xs+rng.normal(0, 1.4*(depth/3+.3), n), ys+rng.normal(0, 1.2, n), 0.6*np.clip(depth/5+.35, .35, 1), np.clip((Y0-ys)/520, 0, 1)**2*(1.2-depth/6))
    if depth > 0:
        for s_ in (-1, 1): tree(xs[-1], ys[-1], ang+s_*rng.uniform(.3, .65), ln*rng.uniform(.62, .78), depth-1)
tree(95, Y0-5, 0.04, 210, 6)                 # escena 1: un árbol
tree(1560, Y0-5, -0.03, 200, 6)              # escena 3: dos árboles
tree(1900, Y0-5, 0.05, 245, 6)
for par in list(LAY):
    arr = np.concatenate(LAY[par]); arr = arr[np.argsort(arr[:, 0])]
    LAY[par] = (arr, rng.uniform(size=len(arr)) < 0.25)
stars = np.c_[rng.uniform(0, W, 90), rng.uniform(20, 760, 90)]; st_ph = rng.uniform(0, 6.28, 90)

# ---------- lluvia (cerca/lejos, intensidad creciente) ----------
ND = 950; WINDR = 0.13
d_near = rng.uniform(size=ND) < 0.3
d_x = rng.uniform(-80, W+160, ND); d_ly = Y0 + 8 + rng.uniform(0, 1, ND)**1.4*185
d_ly = np.where(d_near, Y0 + 120 + rng.uniform(0, 70, ND), d_ly)
d_T = rng.uniform(0.75, 1.15, ND); d_off = rng.uniform(0, 2, ND); d_on = T_RAIN + rng.uniform(0, 1, ND)**1.6*6.5
NLS = 60; ls_ph = rng.uniform(0, 1, NLS); ls_T = rng.uniform(0.5, 0.9, NLS)    # gotas sobre la hoja
# ---------- ráfagas de viento, motas, polvo ----------
NWS = 18; ws_ph = rng.uniform(0, 2.6, NWS); ws_y = rng.uniform(250, 1000, NWS); ws_dx = rng.uniform(-250, 600, NWS)
NM = 160; m_x = rng.uniform(0, W+100, NM); m_y = rng.uniform(80, 1250, NM); m_ph = rng.uniform(0, 6.28, NM)
NP = 260; p_a = rng.uniform(0, np.pi, NP); p_v = rng.uniform(20, 140, NP); p_lr = rng.uniform(-1, 1, NP)
FLASH = ((24.0, 0.07), (24.22, 0.05), (24.45, 0.25))
def flash(t): return sum(np.exp(-((t-c)/w)**2) if t > c else np.exp(-((t-c)/0.02)**2) for c, w in FLASH)
def wind(t): return 0.6 + 0.9*ss(T_FLY, T_FLY+2, t) - 0.3*ss(T_LAND-2, T_LAND, t) + 0.5*ss(T_RAIN, T_RAIN+4, t) + 0.25*np.sin(t*0.7)
ZOOM = [1.0, 360.0, 1150.0]
yy_, xx_ = np.mgrid[0:OH, 0:OW]
VIG = 1 - 0.45*(((xx_-OW/2)/(OW/2))**2*0.6 + ((yy_-OH*0.55)/(OH/2))**2)**1.3
VIG = np.clip(VIG, 0.3, 1); del yy_, xx_
# ---------- sombra de estela ----------
NS = 1100; s_ph = rng.uniform(0, 1.6, NS); s_vx = rng.uniform(-45, 5, NS); s_vy = rng.uniform(-25, 15, NS); LIFE = 1.6

def splat(buf, x, y, w):
    z, zx, zy = ZOOM
    x = ((x-zx)*z+zx)*SC; y = ((y-zy)*z+zy)*SC
    m = (x > 1) & (x < OW-2) & (y > 1) & (y < OH-2)
    x, y, w = x[m], y[m], w[m]; ix = x.astype(int); fx = x-ix; iy = y.astype(int); fy = y-iy
    for dx, dy, ww in ((0,0,(1-fx)*(1-fy)), (1,0,fx*(1-fy)), (0,1,(1-fx)*fy), (1,1,fx*fy)):
        buf += np.bincount((iy+dy)*OW + ix+dx, weights=w*ww, minlength=OW*OH).reshape(OH, OW)
def blur(b):
    o = b.copy(); o[:, 1:-1] = (b[:, :-2] + 2*b[:, 1:-1] + b[:, 2:])/4
    p = o.copy(); p[1:-1] = (o[:-2] + 2*o[1:-1] + o[2:])/4; return p

def frame(t):
    sm = np.zeros(OH*OW).reshape(OH, OW); bg = np.zeros_like(sm)
    ea = ss(0.5, 4.5, t); cx = float(cam(t)); wd = wind(t); fsh = flash(t)
    lp, _, _ = pose(T_LAND); lxs, lys, _ = project(lp[0], cam(T_LAND))
    pc0, _, _ = pose(t); cxs, cys, _ = project(pc0[0], cx)
    zz = (1 + 1.6*(1-ss(2.8, 7.5, t)))*(1 + 0.6*ss(T_LAND+0.8, DUR-0.3, t)); ZOOM[:] = [zz, float(cxs), float(cys)]
    for par, (arr, bgm) in LAY.items():
        lo = np.searchsorted(arr[:, 0], cx*par-6); hi = np.searchsorted(arr[:, 0], cx*par+W+6)
        seg = arr[lo:hi]; m = bgm[lo:hi]; xs_ = seg[:, 0]-cx*par
        xs_ = xs_ + seg[:, 3]*wd*(7*np.sin(t*1.4 + seg[:, 0]*0.006) + 3*np.sin(t*3.1 + seg[:, 0]*0.03))
        vb = seg[:, 2]*ea*(1 + 1.6*fsh)
        splat(sm, xs_[~m], seg[~m, 1], vb[~m]); splat(bg, xs_[m], seg[m, 1], vb[m])
    splat(sm, (stars[:, 0]-cx*0.05) % W, stars[:, 1], ea*(0.35+0.35*np.sin(t*2+st_ph)))
    # motas flotando
    mxx = (m_x + 9*t - cx*0.9) % (W+100) - 50 + 6*np.sin(t*0.8+m_ph)
    myy = m_y + 10*np.sin(t*0.5+m_ph*2) + (t > T_RAIN)*0
    splat(sm, mxx, myy, ea*0.32*(0.5+0.5*np.sin(t*1.7+m_ph))**2*(1-0.6*ss(T_RAIN, T_RAIN+3, t)))
    # corrientes de viento que llevan la hoja
    if T_FLY-0.5 < t < T_LAND+0.5:
        env = ss(T_FLY-0.5, T_FLY+1.5, t)*(1-ss(T_LAND-2.5, T_LAND, t))
        sv = t + np.linspace(-1.6, 0.6, 320)
        pc, _, _ = pose(sv); qx, qy, _ = project(pc, cx)
        for j, (off, ph, sp_) in enumerate(((-55, 0.0, 1.0), (40, 1.3, 1.25), (-110, 2.1, 0.8), (85, 3.0, 1.1), (-20, 4.4, 1.4))):
            wav = off + 14*np.sin(sv*2.3 + ph) + 10*np.sin(sv*5.1 + ph*2)
            puls = np.clip(np.sin(2*np.pi*(sv*0.9*sp_ - t*0.9*sp_*1.6) + ph), 0, 1)**1.5
            fade = ss(-1.6, -0.6, sv-t)*(1-ss(0.1, 0.6, sv-t))
            splat(sm, qx + wav*0.25, qy + wav, 0.9*env*fade*puls*(1 - 0.45*abs(off)/110))
            splat(bg, qx + wav*0.25, qy + wav, 0.35*env*fade*puls*(1 - 0.45*abs(off)/110))
    # hoja
    P, R, u = pose(t); P = P[0]; R = R[0]
    if t > T_RAIN+1:
        q = 0.025*ss(T_RAIN+1, T_RAIN+5, t)*(np.sin(t*23)*np.sin(t*7.3))
        R = R @ Rx(np.array(q)) 
    form = ss(0, 1, (t - 0.1 - delay*2.6)/1.3)
    wp = LOC @ R.T + P                                  # puestos en el mundo
    sx, sy, sc = project(wp, cx)
    n = NRM @ R.T; nd = n @ LIGHT
    bright = np.clip(0.30 + 0.70*np.abs(nd)**0.8, 0, 1)*np.where(nd < 0, 0.85, 1.0)*(0.25+0.95*ltone)
    bright = np.where(lkind > 0, np.minimum(1, bright*1.15 + 0.15), bright)
    wob = 1-form
    px = start[:, 0]*wob + sx*form + wob*np.sin(t*2+rnd_ph)*16
    py = start[:, 1]*wob + sy*form + wob*np.cos(t*2+rnd_ph)*16
    fl = (np.sin(t*5+rnd_ph)*0.06*(u > 0)) + 1                    # leve centelleo
    wgt = bright*(0.12+0.88*form)*fl
    px = px + np.where(u > 0, np.sin(t*3+lx*.05)*0.6, 0)
    splat(sm, px[~big], py[~big], wgt[~big]); splat(bg, px[big], py[big], wgt[big])
    # estela de puntos
    if T_FLY < t < T_LAND+0.8:
        age = (t - s_ph) % LIFE; tb = t - age; k = np.floor((t - s_ph)/LIFE).astype(int)
        ok = (tb > T_FLY+0.3) & (tb < T_LAND-0.4)
        pb, Rb, _ = pose(tb); idx = (np.arange(NS)*7 + k*977) % NL
        wp2 = np.einsum('nij,nj->ni', Rb, LOC[idx]) + pb
        x2, y2, _ = project(wp2, cx); x2 = x2 + s_vx*age; y2 = y2 + s_vy*age + 14*age**2
        splat(sm, x2, y2, np.where(ok, 0.65*(1-age/LIFE)**1.6, 0))
    # polvo al posarse
    pa = t - (T_LAND-0.35)
    if 0 < pa < 1.6:
        g = p_v*pa*(1-pa/3.2)
        xp = lxs + p_lr*35 + np.cos(p_a)*g; yp = lys + 6 - np.sin(p_a)*g*0.45 + 22*pa**2
        splat(sm, xp, yp, 0.55*(1-pa/1.6)**1.5*np.ones(NP))
    # lluvia
    if t > T_RAIN:
        act = t >= d_on
        tau = (t - d_on + d_off) % d_T; fall = d_T*0.62
        fl_ = act & (tau < fall)
        yy = -90 + (d_ly+90)*(tau/fall); xx = d_x - WINDR*yy
        for s in range(9):
            nearw = 1.6*np.where(d_near, 1.0*(1-s*0.10), np.where(s < 5, 0.6*(1-s*0.18), 0))
            sp = np.where(d_near, 15, 9)
            rxs = xx + WINDR*s*sp; rys = yy - s*sp; rw_ = np.where(fl_, nearw, 0)
            splat(sm, rxs, rys, rw_); splat(bg, rxs[d_near], rys[d_near], rw_[d_near]*0.7)
        p = np.clip((tau-fall)/(d_T-fall)/0.5, 0, 1); sp_ = act & (tau >= fall) & (p < 1)
        gx_ = d_x - WINDR*d_ly
        for a in np.linspace(0, 2*np.pi, 14, endpoint=False):
            r = (3 + 30*p)*np.where(d_near, 1.5, 1)
            splat(sm, gx_ + r*np.cos(a), d_ly + 0.3*r*np.sin(a), np.where(sp_, 0.85*(1-p), 0))
        for j in range(4):
            ang = 0.5 + j*0.7
            splat(bg, gx_ + np.cos(ang)*14*p, d_ly - np.sin(ang)*16*np.sin(np.pi*np.clip(p*1.4, 0, 1)), np.where(sp_ & (p < .55), 0.7, 0))
        # gotas que golpean la hoja
        rl = ss(T_RAIN+0.5, T_RAIN+4, t)
        if rl > 0:
            ta = (t + ls_ph*ls_T) % ls_T; kk = np.floor((t + ls_ph*ls_T)/ls_T).astype(int)
            idx = (np.arange(NLS)*131 + kk*7919) % NL; pp = np.clip(ta/0.35, 0, 1)
            for a in np.linspace(0, 2*np.pi, 8, endpoint=False):
                r = 2 + 11*pp
                splat(sm, px[idx] + r*np.cos(a), py[idx] + 0.4*r*np.sin(a), rl*0.8*(1-pp))
    img = (sm + 2.3*blur(bg))*VIG + 0.05*fsh
    img = np.clip(img*(1 - ss(DUR-1.8, DUR-0.15, t)), 0, 1)
    return (img*255).astype(np.uint8)

def fb(f): return frame(f/FPS).tobytes()
if __name__ == "__main__":
    from multiprocessing import Pool
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else FPS*DUR
    p = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","gray","-s",f"{OW}x{OH}",
        "-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","15",out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(fb, range(n), chunksize=2): p.stdin.write(b)
    p.stdin.close(); p.wait()
