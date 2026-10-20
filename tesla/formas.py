"""Mapas de densidad: retrato de Tesla y bombilla. Lienzo de diseño 1080x1920."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
W, H = 1080, 1920

def tesla(scale=0.5):
    im = Image.open("src/tesla.jpg").convert("L")                # 940x1260
    poly = [(215,230),(240,110),(330,60),(460,40),(580,60),(670,130),(700,240),(725,340),(715,450),(670,510),
            (650,600),(700,640),(760,700),(860,820),(940,920),(940,1260),(0,1260),(0,1130),(90,960),(200,840),
            (310,760),(330,700),(340,640),(310,580),(270,470),(240,390),(225,320)]
    mk = Image.new("L", im.size); ImageDraw.Draw(mk).polygon(poly, fill=255); mk = mk.filter(ImageFilter.GaussianBlur(9))
    # ubicar en el lienzo: cara grande, centrada en el tercio superior
    s = 1240/940; nw, nh = int(940*s), int(1260*s); ox, oy = (W-nw)//2, 180
    def place(img):
        A = np.asarray(img.resize((nw, nh), Image.LANCZOS), float)/255; out = np.zeros((H, W))
        x0, x1 = max(ox, 0), min(ox+nw, W); y0, y1 = max(oy, 0), min(oy+nh, H)
        out[y0:y1, x0:x1] = A[y0-oy:y1-oy, x0-ox:x1-ox]; return out
    I = place(im); M = place(mk)
    gy, gx = np.gradient(np.asarray(Image.fromarray((I*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), float)/255)
    edge = np.clip(np.hypot(gx, gy)*9, 0, 1)
    d = np.clip((I - 0.12)/0.85, 0, 1)**1.9 + 0.22*edge
    yy = np.arange(H)[:, None]
    d *= M*(1 - 0.85*np.clip((yy - 1150)/420, 0, 1))
    small = Image.fromarray((np.clip(d, 0, 1)*255).astype(np.uint8)).resize((int(W*scale), int(H*scale)), Image.BILINEAR)
    return np.asarray(small, float)/255

def bombilla(scale=0.5):
    """Bombilla: vidrio (contorno), filamento en espiral, soportes y rosca. Devuelve densidad y máscara de filamento."""
    S = 4; w, h = W*S//4, H*S//4                                       # se dibuja a 1/1 y luego se reduce
    im = Image.new("L", (W, H)); fm = Image.new("L", (W, H)); d = ImageDraw.Draw(im); df = ImageDraw.Draw(fm)
    cx, cy, R = 540, 820, 300
    # vidrio: círculo + cuello que se estrecha
    t = np.linspace(-np.pi*0.80, np.pi*0.80, 400)
    glass = [(cx + R*np.sin(a), cy - R*np.cos(a)) for a in t]
    nb = [(cx + R*np.sin(np.pi*0.80), cy - R*np.cos(np.pi*0.80))]
    for k in np.linspace(0, 1, 60):
        y = cy - R*np.cos(np.pi*0.80) + k*190; x = cx + (R*np.sin(np.pi*0.80))*(1-k) + 125*k + 18*np.sin(k*np.pi)
        nb.append((x, y))
    left = [(2*cx - x, y) for x, y in nb[::-1]]
    outline = left + glass[::-1] + nb[1:]
    outline = [(2*cx - x, y) for x, y in outline]
    d.line(outline, fill=255, width=7)
    d.line([(x+(cx-x)*0.03, y+(cy-y)*0.03) for x, y in outline], fill=90, width=4)   # doble borde (grosor del vidrio)
    # reflejo
    for a in np.linspace(-2.3, -1.5, 40):
        d.ellipse((cx+R*0.78*np.cos(a)-5, cy+R*0.78*np.sin(a)-5, cx+R*0.78*np.cos(a)+5, cy+R*0.78*np.sin(a)+5), fill=200)
    # soportes del filamento
    yb = cy + R*0.55 + 120
    for sx in (-38, 38):
        d.line([(cx+sx*0.4, yb), (cx+sx*1.6, cy+10)], fill=170, width=4)
    d.line([(cx, yb), (cx, cy+70)], fill=150, width=5)
    # filamento: espiral
    fx = np.linspace(-60, 60, 900); fy = cy + 10 - 14*np.cos(fx/60*np.pi/2*0)
    pts = [(cx + x + 9*np.cos(x*0.55), fy[i] + 11*np.sin(x*0.55) - 18*(1-(x/60)**2)) for i, x in enumerate(fx)]
    d.line(pts, fill=255, width=5); df.line(pts, fill=255, width=7)
    # rosca
    y0 = cy - R*np.cos(np.pi*0.80) + 190
    for k in range(6):
        yk = y0 + 8 + k*28; wk = 128 - k*3
        d.line([(cx-wk, yk), (cx+wk, yk+14)], fill=230, width=8)
        d.line([(cx-wk, yk+14), (cx+wk, yk+14)], fill=110, width=3)
    d.rectangle((cx-118, y0, cx+118, y0+175), outline=160, width=4)
    d.ellipse((cx-42, y0+175, cx+42, y0+215), fill=200)
    im = im.filter(ImageFilter.GaussianBlur(2.5)); fm = fm.filter(ImageFilter.GaussianBlur(3))
    # relleno muy tenue del interior del vidrio (para que se lea el volumen)
    inn = Image.new("L", (W, H)); ImageDraw.Draw(inn).ellipse((cx-R+20, cy-R+20, cx+R-20, cy+R-20), fill=28)
    inn = inn.filter(ImageFilter.GaussianBlur(40))
    a = np.maximum(np.asarray(im, float), np.asarray(inn, float))/255
    sz = (int(W*scale), int(H*scale))
    return (np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize(sz, Image.BILINEAR), float)/255,
            np.asarray(fm.resize(sz, Image.BILINEAR), float)/255, (cx, cy, R))
