"""« Preuves » animées, mix video essay x Kali Muscle (16:9 ou 9:16).
- stream_card : carte « titre + pochette + plateforme » dont le compteur de vues / streams défile (count-up), néon vert.
- article_push : capture d'article ou de tweet légèrement inclinée en 3D, travelling du plan large au gros plan sur le titre,
  surligneur jaune qui balaie la phrase clé, vignettage, mot-clé néon en bas.
Fond rouge/noir quadrillé avec braises, transition burn, titres 3D chrome/rouge, effets sonores de sa bibliothèque.
usage (démo) : proof_fx.py OUT.mp4 [vertical]"""
import sys, os, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import LIB, ANTON, YEL, RED, WHT, GRN, GOLD, neon, glow_rgba, block

FPS, SR = 30, 48000
_rng = np.random.default_rng(7)

class Canvas:
    def __init__(s, W, H):
        s.W, s.H, s.G = W, H, 80
        g = np.zeros((H + s.G, W), np.float32); g[::s.G, :] = 1; g[:, ::s.G] = 1
        s.grid = cv2.GaussianBlur(g, (0, 0), 0.8) * 1.5
        yy, xx = np.ogrid[:H, :W]
        s.vig = np.clip(1.25 - np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 1.35, 0.25, 1).astype(np.float32)[..., None]
        n = int(W * H / 17000)
        s.emb = np.c_[_rng.uniform(0, W, n), _rng.uniform(0, H, n), _rng.uniform(30, 110, n), _rng.uniform(1.5, 4.0, n), _rng.uniform(0, 6.3, n)]
    def bg(s, t, red=0.35):
        img = np.zeros((s.H, s.W, 3), np.float32); img[:] = (0.035, 0.02, 0.05 + red * 0.12)
        o = int(t * 16) % s.G; gm = s.grid[s.G - o:s.G - o + s.H, :, None]
        img = img * (1 - 0.35 * gm) + np.array([0.1, 0.1, 0.8], np.float32) * 0.3 * gm
        lay = np.zeros((s.H, s.W), np.float32)
        for x, y, v, r, ph in s.emb:
            cv2.circle(lay, (int(x + 16 * np.sin(t * 1.3 + ph)), int((y - v * t) % s.H)), int(r), 0.5 + 0.5 * np.sin(t * 7 + ph), -1, cv2.LINE_AA)
        return np.clip(img * s.vig + cv2.GaussianBlur(lay, (0, 0), 1.5)[..., None] * np.array([0.2, 0.55, 1.0], np.float32), 0, 1)
    def paste(s, dst, img, cx, cy, scale=1.0, alpha=1.0):
        if alpha <= 0.003: return
        if scale != 1.0: img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        h, w = img.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
        xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, s.W), min(y0 + h, s.H)
        if xa >= xb or ya >= yb: return
        src = img[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4] * alpha
        dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a

def ease(u): u = float(np.clip(u, 0, 1)); return 1 - (1 - u) ** 3
def popk(k): return 1 + 0.28 * max(0.0, 1 - max(k, 0) / 0.13) ** 2

# ---------- stream card ----------
def _font(sz): return ImageFont.truetype(ANTON, sz)
def make_card(cover_path, title, artist, platform, width=1150, plat_rgb=(30, 215, 96)):
    """Static part of the card (RGBA float, RGB order) + where the counter goes."""
    h = int(width * 0.36); cs = h - 60
    im = Image.new("RGBA", (width, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, width - 1, h - 1), 34, fill=(14, 10, 18, 235), outline=(255, 60, 70, 255), width=5)
    cov = Image.open(cover_path).convert("RGB"); s = cs / min(cov.size)
    cov = cov.resize((int(cov.width * s), int(cov.height * s)), Image.LANCZOS)
    cov = cov.crop(((cov.width - cs) // 2, (cov.height - cs) // 2, (cov.width - cs) // 2 + cs, (cov.height - cs) // 2 + cs))
    m = Image.new("L", (cs, cs), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cs - 1, cs - 1), 22, fill=255); im.paste(cov, (30, 30), m)
    x = 30 + cs + 40
    d.text((x, 34), title, font=_font(int(h * 0.17)), fill=(255, 255, 255, 255))
    d.text((x, 34 + int(h * 0.21)), artist, font=_font(int(h * 0.11)), fill=(255, 222, 40, 255))
    pf = _font(int(h * 0.075)); pb = d.textbbox((0, 0), platform, font=pf)
    d.rounded_rectangle((x, h - 30 - (pb[3] - pb[1]) - 26, x + pb[2] - pb[0] + 40, h - 30), 30, fill=plat_rgb + (255,))
    d.text((x + 20 - pb[0], h - 30 - (pb[3] - pb[1]) - 13 - pb[1]), platform, font=pf, fill=(10, 10, 10, 255))
    card = np.asarray(im).astype(np.float32) / 255
    return glow_rgba(card, (255, 50, 60), 24, 0.9), (x + 66, int(h * 0.62) + 66)   # glow adds 3*sigma padding (72); counter origin

def draw_stream_card(cv, img, card, origin, t, t0, dur, v0, v1, suffix, cx, cy, scale=1.0, col=GRN):
    k = t - t0
    if k < 0: return
    # entrance: pops in with a 3D tilt that settles flat
    tilt = (1 - ease(k / 0.5)) * 0.22
    h, w = card[0].shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]]); dy = tilt * h
    dstp = np.float32([[0, dy], [w, -dy * 0.3], [w, h + dy * 0.3], [0, h - dy]])
    c = cv2.warpPerspective(card[0], cv2.getPerspectiveTransform(src, dstp), (w, h), flags=cv2.INTER_LINEAR)
    sc = scale * (0.85 + 0.15 * ease(k / 0.35)) * popk(k - 0.05)
    cv.paste(img, c, cx, cy, sc, min(k / 0.12, 1))
    u = ease((k - 0.45) / dur) if k > 0.45 else 0
    val = int(v0 + (v1 - v0) * u)
    txt = f"{val:,}".replace(",", " ") + suffix
    n_im, pad = neon(txt, int(card[0].shape[0] * 0.17), col)
    ox, oy = origin
    cx0 = cx - w * sc / 2 + (ox + n_im.shape[1] / 2 - pad) * sc; cy0 = cy - h * sc / 2 + oy * sc
    cv.paste(img, n_im, cx0, cy0, sc * (popk(k - 0.45 - dur) if k > 0.45 + dur else 1.0), min(k / 0.2, 1))

# ---------- article push ----------
def tilt_shot(path, width):
    im = cv2.imread(path); s = width / im.shape[1]; im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    h, w = im.shape[:2]
    rgba = np.dstack([im[..., ::-1].astype(np.float32) / 255, np.ones((h, w), np.float32)])
    return rgba, s

def draw_article(cv, img, shot, box, hl, t, t0, dur, keyword=None, kw_col=YEL):
    """shot: (rgba, scale); box: headline (x0,y0,x1,y1) in source pixels; hl: highlighted part of the box (x0,y0,x1,y1)."""
    k = t - t0
    if k < 0: return
    rgba, s = shot; h, w = rgba.shape[:2]
    x0, y0, x1, y1 = [v * s for v in box]
    u = ease(k / (dur * 0.55))
    # camera: from whole shot to the headline (zoom so the headline fills ~95% of the frame width), with a slow drift
    z0 = min(cv.W * 0.86 / w, cv.H * 0.80 / h); z1 = cv.W * 0.95 / (x1 - x0)
    z = z0 + (z1 - z0) * u + 0.02 * k
    fx = (w / 2) * (1 - u) + ((x0 + x1) / 2 + 0.03 * cv.W / z * (k / dur)) * u
    fy = (h / 2) * (1 - u) + ((y0 + y1) / 2) * u
    M = np.float32([[z, 0, cv.W / 2 - fx * z], [0, z, cv.H / 2 - fy * z]])
    layer = cv2.warpAffine(rgba, M, (cv.W, cv.H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    # slight 3D tilt (perspective) that flattens as we get close
    tl = 0.035 * (1 - u)
    src = np.float32([[0, 0], [cv.W, 0], [cv.W, cv.H], [0, cv.H]])
    dstp = np.float32([[cv.W * tl, cv.H * tl], [cv.W * (1 - tl * 0.3), 0], [cv.W * (1 - tl * 0.3), cv.H], [cv.W * tl, cv.H * (1 - tl)]])
    layer = cv2.warpPerspective(layer, cv2.getPerspectiveTransform(src, dstp), (cv.W, cv.H))
    # highlighter sweep on the key words, once the camera has arrived
    kh = k - dur * 0.55
    if kh > 0:
        hx0, hy0, hx1, hy1 = [v * s for v in hl]
        p0 = M @ np.array([hx0, hy0, 1]); p1 = M @ np.array([hx0 + (hx1 - hx0) * ease(kh / 0.45), hy1, 1])
        mk = np.zeros((cv.H, cv.W), np.float32)
        cv2.rectangle(mk, (int(p0[0]), int(p0[1] + (p1[1] - p0[1]) * 0.15)), (int(p1[0]), int(p1[1] + 6)), 1.0, -1)
        mk = cv2.warpPerspective(mk, cv2.getPerspectiveTransform(src, dstp), (cv.W, cv.H))[..., None] * 0.55
        layer[..., :3] = layer[..., :3] * (1 - mk) + layer[..., :3] * np.array([1.0, 0.92, 0.25], np.float32) * mk
    a = layer[..., 3:4] * min(k / 0.15, 1)
    img[:] = img * (1 - a) + layer[..., [2, 1, 0]] * a
    img *= cv.vig * 0.55 + 0.45                       # strong vignette, like the essay shots
    if keyword and kh > 0.35:
        im, _ = neon(keyword, int(min(cv.H * 0.075, cv.W * 0.07)), kw_col); cv.paste(img, im, cv.W / 2, cv.H * 0.86, popk(kh - 0.35), min((kh - 0.35) / 0.08, 1))

# ---------- demo ----------
if __name__ == "__main__":
    OUT = sys.argv[1]; vertical = len(sys.argv) > 2 and sys.argv[2] == "vertical"
    W, H = (1080, 1920) if vertical else (1920, 1080)
    cv = Canvas(W, H)
    SC = "/tmp/claude-0/-home-user-vasse19/ec8c510a-6526-5f05-8c7f-383e06c1407b/scratchpad"
    card = make_card(f"{SC}/sho/img/je-mappelle.jpg", "« JE M'APPELLE »", "DIDI B FEAT. ZLATAN", "SPOTIFY", 1000 if vertical else 1400)
    shot = tilt_shot(f"{SC}/an29/a0.png", 1288)
    hook = block("LES CHIFFRES", "PARLENT", int(W * 0.8), int(H * 0.42))
    burn = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions/burn-transition-12.mp4"), "-vf",
                           f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                          capture_output=True, check=True).stdout
    BURN = np.frombuffer(burn, np.uint8).reshape(-1, H, W, 3); BP = 11 / FPS
    T_CARD, T_ART, END = 2.2, 7.2, 13.5
    BURN_AT = [T_CARD, T_ART]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-vf", "noise=alls=3:allf=t+u,format=yuv420p", "-c:v", "libx264", "-crf", "18", f"{OUT}.v.mp4"], stdin=subprocess.PIPE)
    for i in range(int(END * FPS)):
        t = i / FPS; img = cv.bg(t)
        if t < T_CARD:
            k = t; cv.paste(img, hook, W / 2, H / 2, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
        elif t < T_ART:
            draw_stream_card(cv, img, card, card[1], t, T_CARD, 2.6, 0, 4_900_000, "", W / 2, H * (0.46 if vertical else 0.48))
            if t > T_CARD + 3.2:
                im, _ = neon("STREAMS SUR SPOTIFY", int(H * (0.04 if vertical else 0.065)), WHT); cv.paste(img, im, W / 2, H * (0.62 if vertical else 0.80), popk(t - T_CARD - 3.2))
        else:
            draw_article(cv, img, shot, (60, 118, 1215, 245), (500, 118, 950, 184), t, T_ART, 5.0, "140 MILLIARDS DE STREAMS")
        for b in BURN_AT:
            kb = int(round((t - (b - BP)) * FPS))
            if 0 <= kb < len(BURN): img = 1 - (1 - img) * (1 - BURN[kb].astype(np.float32) / 255)
        enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    def load(p): return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]), np.float32)
    sfx = np.zeros(int(END * SR) + SR, np.float32)
    def place(snd, t, g):
        i0 = max(int(t * SR), 0); n = min(len(snd), len(sfx) - i0); sfx[i0:i0 + n] += snd[:n] * g
    place(load("sfx/synth-hit.wav"), 0.05, 0.5); place(load("sfx/whoosh-1.mp3"), T_CARD - 0.42, 0.3)
    mc = load("sfx/money-counter.mp3")[int(0.6 * SR):int(3.2 * SR)].copy(); mc[-int(0.1 * SR):] *= np.linspace(1, 0, int(0.1 * SR))
    place(mc, T_CARD + 0.45, 0.5); place(load("sfx/cash-ding.mp3"), T_CARD + 0.45 + 2.6 - 0.4, 0.5)
    place(load("sfx/whoosh-3.mp3"), T_ART - 0.26, 0.3); place(load("sfx/camera-shutter-short.mp3"), T_ART + 0.05, 0.6)
    place(load("sfx/sparkle.mp3")[int(4.2 * SR):int(5.4 * SR)], T_ART + 2.75, 0.35); place(load("sfx/synth-hit.wav"), T_ART + 3.1, 0.35)
    burn_a = load("transitions/burn-transition-12.mp4")
    for b in BURN_AT: place(burn_a, b - BP, 0.45)
    import soundfile as sf
    sf.write(f"{OUT}.a.wav", np.clip(sfx[:int(END * SR)], -0.9, 0.9), SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}.v.mp4", "-i", f"{OUT}.a.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ac", "2", "-movflags", "+faststart", "-shortest", OUT], check=True)
    os.remove(f"{OUT}.v.mp4"); os.remove(f"{OUT}.a.wav"); print("done", OUT)
