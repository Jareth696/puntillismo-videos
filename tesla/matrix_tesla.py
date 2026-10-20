"""Tesla -> bombilla en estilo Matrix: la escena de puntos (tesla.py) convertida a 0 y 1 verdes, con lluvia digital."""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import tesla as S

CW, CH = 8, 12                                         # celda de cada carácter
COLS, ROWS = S.W // CW, S.H // CH
FONT = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
def glyph(ch):
    im = Image.new("L", (CW, CH)); f = ImageFont.truetype(FONT, 11)
    ImageDraw.Draw(im).text((CW/2, CH/2), ch, font=f, fill=255, anchor="mm"); return np.asarray(im, float)/255
GL = np.stack([glyph("0"), glyph("1")])
rng = np.random.default_rng(5)
c_ph = rng.uniform(0, 100, (ROWS, COLS)); c_rate = rng.uniform(0.5, 2.0, (ROWS, COLS))
r_on = rng.uniform(size=COLS) < 0.6
r_v = rng.uniform(6, 20, COLS); r_len = rng.uniform(10, 32, COLS); r_ph = rng.uniform(0, 400, COLS)
rows_ = np.arange(ROWS)[:, None]
# verde Matrix: oscuro -> verde intenso -> blanco verdoso en los brillos
v = np.linspace(0, 1, 256)
LUT = (np.c_[255*v**3.2*0.75, 255*np.minimum(1, v**0.9*1.08), 255*v**2.6*0.45]).astype(np.uint8)

def mframe(t):
    g = S.frame(t).astype(float)/255
    blk = g.reshape(ROWS, CH, COLS, CW)
    b = 0.25*blk.max(axis=(1, 3)) + 0.75*np.clip(blk.mean(axis=(1, 3))*2.4, 0, 1.2)
    b = np.clip((b - 0.16)/0.8, 0, 1)**1.5
    cyc = ROWS + r_len + 20; head = (t*r_v + r_ph) % cyc; d = head[None, :] - rows_
    tail = np.where((d >= 0) & (d < r_len[None, :]), np.clip(1 - d/r_len[None, :], 0, 1)**1.6, 0)*r_on[None, :]
    morph = np.exp(-((t - (S.T_MORPH + 1.6))/1.6)**2)                  # más lluvia durante la transformación
    amb = (0.11 + 0.12*morph)*S.ss(0.0, 2.0, t)*(1 - S.ss(S.DUR-1.6, S.DUR-0.1, t))
    rain = tail*amb + np.where((d >= 0) & (d < 1), 1, 0)*r_on[None, :]*amb*2.4
    b = np.maximum(b, rain)
    rate = np.where(rain > b*0.99, 10.0, c_rate)
    ch = (np.floor(t*rate + c_ph).astype(int)*2654435761 + np.arange(ROWS*COLS).reshape(ROWS, COLS)*97) >> 7 & 1
    img = (GL[ch]*b[:, :, None, None]).transpose(0, 2, 1, 3).reshape(S.H, S.W)
    img = img + 0.6*S.blur(S.blur(img))
    return LUT[(np.clip(img, 0, 1)*255).astype(np.uint8)]

def fb(f): return mframe(f/S.FPS).tobytes()
if __name__ == "__main__":
    from multiprocessing import Pool
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else S.FPS*S.DUR
    p = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{S.W}x{S.H}",
        "-r",str(S.FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","16",out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(fb, range(n), chunksize=2): p.stdin.write(b)
    p.stdin.close(); p.wait()
