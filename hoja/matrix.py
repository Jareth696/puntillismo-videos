"""Versión Matrix: la escena de puntillismo (hoja_bn5) convertida a 0 y 1, con lluvia digital de fondo. B/N."""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import hoja_bn5 as S

CW, CH = 9, 14                                   # celda de cada carácter (px de salida)
COLS, ROWS = S.OW // CW, S.OH // CH
OW, OH = COLS*CW, ROWS*CH
FONT = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
def glyph(ch):
    im = Image.new("L", (CW, CH)); f = ImageFont.truetype(FONT, 13)
    ImageDraw.Draw(im).text((CW/2, CH/2), ch, font=f, fill=255, anchor="mm")
    return np.asarray(im, float)/255
GL = np.stack([glyph("0"), glyph("1")])
rng = np.random.default_rng(5)
c_ph = rng.uniform(0, 100, (ROWS, COLS)); c_rate = rng.uniform(0.6, 2.2, (ROWS, COLS))
# lluvia digital: un chorro por columna
r_on = rng.uniform(size=COLS) < 0.55
r_v = rng.uniform(5, 16, COLS); r_len = rng.uniform(8, 26, COLS); r_ph = rng.uniform(0, 300, COLS)
rows_ = np.arange(ROWS)[:, None]

def mframe(t):
    g = S.frame(t)[:OH, :OW].astype(float)/255
    blk = g.reshape(ROWS, CH, COLS, CW)
    b = 0.55*blk.max(axis=(1, 3)) + 0.45*blk.mean(axis=(1, 3))*3
    b = np.clip((b - 0.12)/0.7, 0, 1)**1.35
    # lluvia digital tenue (más intensa cuando llueve, se apaga con el fundido final)
    cyc = ROWS + r_len + 20
    head = (t*r_v + r_ph) % cyc
    d = head[None, :] - rows_
    tail = np.where((d >= 0) & (d < r_len[None, :]), np.clip(1 - d/r_len[None, :], 0, 1)**1.6, 0)*r_on[None, :]
    amb = (0.10 + 0.10*S.ss(S.T_RAIN, S.T_RAIN+4, t))*S.ss(0.0, 2.5, t)*(1 - S.ss(S.DUR-1.8, S.DUR-0.15, t))
    rain = tail*amb + np.where((d >= 0) & (d < 1), 1, 0)*r_on[None, :]*amb*2.2
    b = np.maximum(b, rain)
    # qué carácter: cambia lento en la escena, rápido en los chorros
    rate = np.where(rain > b*0.99, 9.0, c_rate)
    ch = (np.floor(t*rate + c_ph).astype(int)*2654435761 + np.arange(ROWS*COLS).reshape(ROWS, COLS)*97) >> 7 & 1
    img = (GL[ch]*b[:, :, None, None]).transpose(0, 2, 1, 3).reshape(OH, OW)
    img = img + 0.55*S.blur(S.blur(img))                   # brillo suave
    return (np.clip(img, 0, 1)*255).astype(np.uint8)

def fb(f): return mframe(f/S.FPS).tobytes()
if __name__ == "__main__":
    from multiprocessing import Pool
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else S.FPS*S.DUR
    p = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","gray","-s",f"{OW}x{OH}",
        "-r",str(S.FPS),"-i","-","-vf","pad=1080:1920:(ow-iw)/2:(oh-ih)/2","-c:v","libx264","-pix_fmt","yuv420p","-crf","16",out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(fb, range(n), chunksize=2): p.stdin.write(b)
    p.stdin.close(); p.wait()
