import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, out = sys.argv[1], sys.argv[2]
OW, OH = 1920, 1080
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
rng = np.random.default_rng(7)

# ---------- photo: frame, smooth skin, grade ----------
raw = cv2.imread(src)
fx, fy, cw = 1125, 657, 1150
ch = cw * 9 / 16; x0 = int(fx - cw * 0.66); y0 = int(fy - ch * 0.43)
crop = raw[y0:int(y0 + ch), x0:x0 + cw]
crop = cv2.fastNlMeansDenoisingColored(crop, None, 6, 6, 7, 21)
# skin smoothing at source resolution, limited to the face
s = OW / cw
fcx_s, fcy_s = fx - x0, fy - y0
fmask = np.zeros(crop.shape[:2], np.float32)
cv2.ellipse(fmask, (int(fcx_s), int(fcy_s + 20)), (150, 195), 0, 0, 360, 1, -1)
fmask = cv2.GaussianBlur(fmask, (0, 0), 12)[..., None]
sm = cv2.bilateralFilter(crop, 9, 28, 6)
sm = cv2.bilateralFilter(sm, 9, 20, 6)
crop = (crop * (1 - 0.75 * fmask) + sm * 0.75 * fmask).astype(np.uint8)
img = cv2.resize(crop, (OW, OH), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
img = np.clip(img + 0.45 * (img - cv2.GaussianBlur(img, (0, 0), 2.0)), 0, 1)
fcx, fcy = fcx_s * s, fcy_s * s

# subject mask (head + torso), feathered
subj = np.zeros((OH, OW), np.float32)
cv2.ellipse(subj, (int(fcx + 5 * s), int(fcy - 25 * s)), (int(185 * s), int(225 * s)), 0, 0, 360, 1, -1)
cv2.ellipse(subj, (int(fcx + 20 * s), int(OH + 60)), (int(330 * s), int(260 * s)), 0, 0, 360, 1, -1)
subj = cv2.GaussianBlur(subj, (0, 0), 28)[..., None]

# subject: contrast + warmth ; background: dark, red-tinted
sub = np.clip((img - 0.5) * 1.12 + 0.52, 0, 1)
sub = sub * np.array([0.96, 1.0, 1.05], np.float32)
L = img.mean(axis=2, keepdims=True)
bg = (L ** 1.4) * np.array([0.10, 0.10, 0.85], np.float32) + img * 0.18
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
bg *= np.clip(1.25 - np.sqrt(((xx - OW * 0.6) / OW) ** 2 + ((yy - OH * 0.5) / OH) ** 2) * 1.2, 0.35, 1)[..., None]
img = sub * subj + bg * (1 - subj)
# red light spill + rim light on the subject edges
glow = np.zeros_like(img)
cv2.circle(glow, (int(OW * 0.97), int(OH * 0.25)), 300, (0.05, 0.05, 1.0), -1)
cv2.circle(glow, (int(OW * 0.08), int(OH * 0.65)), 300, (0.04, 0.04, 0.8), -1)
glow = cv2.GaussianBlur(glow, (0, 0), 150)
img = 1 - (1 - img) * (1 - glow * 0.55)
edge = np.clip(subj[..., 0] - cv2.GaussianBlur(subj[..., 0], (0, 0), 25), 0, 1) * 6
edge = np.clip(edge, 0, 1)[..., None] * (L > 0.12)
img = np.clip(img + edge * np.array([0.05, 0.05, 0.6], np.float32) * 0.15, 0, 1)
photo = Image.fromarray(cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert("RGBA")

# ---------- brush stroke ----------
def brush(w, h):
    a = np.zeros((h, w), np.float32)
    for _ in range(1400):
        y = rng.normal(h / 2, h / 4.5)
        xs = rng.uniform(0, w * 0.5); xe = rng.uniform(w * 0.5, w)
        t = rng.integers(2, 11)
        cv2.line(a, (int(xs), int(y)), (int(xe), int(y + rng.normal(0, 3))), float(rng.uniform(0.3, 1)), int(t))
    a = cv2.GaussianBlur(a, (0, 0), 1.0)
    taper = np.clip(np.minimum(np.linspace(0, 3, w), np.linspace(2.2, 0, w)), 0, 1) ** 0.8
    a *= taper[None]
    a = np.clip(a * 1.6, 0, 1)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 0] = 225; rgba[..., 1] = 12; rgba[..., 2] = 18
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba)

# ---------- 3D text ----------
def text3d(word, size, style, depth=38):
    f = ImageFont.truetype(FONT, size)
    b = f.getbbox(word)
    pad = 80
    W, H = b[2] - b[0] + 2 * pad + depth, b[3] - b[1] + 2 * pad + depth
    m = Image.new("L", (W, H)); ImageDraw.Draw(m).text((pad - b[0], pad - b[1]), word, font=f, fill=255)
    M = np.asarray(m, np.float32) / 255
    th, tw = b[3] - b[1], b[2] - b[0]
    ytop = pad
    canvas = np.zeros((H, W, 4), np.float32)
    def over(rgb, alpha):
        a = alpha[..., None]
        canvas[..., :3] = rgb * a + canvas[..., :3] * (1 - a)
        canvas[..., 3] = alpha + canvas[..., 3] * (1 - alpha)
    # extrusion (back to front)
    ext = np.zeros_like(M)
    for k in range(depth, 0, -1):
        sh = np.roll(np.roll(M, k, axis=0), int(k * 0.45), axis=1)
        ext = np.maximum(ext, sh)
        c = (0.18, 0.02, 0.02) if style == "red" else (0.22, 0.22, 0.25)
        f_ = 0.55 + 0.45 * (1 - k / depth)
        base = np.array([0.55, 0.0, 0.02]) if style == "red" else np.array([0.45, 0.46, 0.5])
        over(np.broadcast_to(np.array(c) + (base - np.array(c)) * (1 - k / depth) * 0.6, M.shape + (3,)) * f_, sh)
    # dark outline around everything
    full = np.maximum(M, ext)
    outline = cv2.dilate(full, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (23, 23)))
    o = np.zeros_like(canvas); o[..., :3] = (0.06, 0.0, 0.0); o[..., 3] = outline
    a = canvas[..., 3:4]
    canvas = np.concatenate([canvas[..., :3] * a + o[..., :3] * (1 - a), np.maximum(a, o[..., 3:4])], axis=2)
    # face fill: gradient with a hard "horizon" reflection band
    yy = (np.arange(H)[:, None] - ytop) / th
    yy = np.repeat(yy, W, axis=1)
    if style == "chrome":
        g = np.interp(yy, [0, .42, .5, .52, .75, 1], [1.0, .82, .55, .35, .62, .95])
        rgb = np.stack([g, g, g * 1.04], -1)
    else:
        r = np.interp(yy, [0, .4, .5, .52, 1], [1.0, .95, .85, .7, .55])
        gg = np.interp(yy, [0, .4, .5, .52, 1], [.42, .12, .05, .02, .0])
        rgb = np.stack([r, gg, gg * 0.9], -1)
    # bevel from distance transform, lit from top-left
    d = cv2.distanceTransform((M > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    hgt = np.clip(d / 7, 0, 1)
    hgt = cv2.GaussianBlur(hgt, (0, 0), 1.5)
    gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
    shade = (-gx * -0.7 + -gy * -0.7)
    shade = np.clip(shade, -1, 1)
    rgb = np.clip(rgb + shade[..., None] * 0.55, 0, 1)
    over(rgb, M)
    # specular streak on the top part
    spec = np.clip(1 - np.abs(yy - 0.18) / 0.08, 0, 1) * M * 0.35
    canvas[..., :3] = np.clip(canvas[..., :3] + spec[..., None], 0, 1)
    return Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8), "RGBA")

top = text3d("YOUTUBE", 250, "chrome")
bot = text3d("C'EST CARDIO", 230, "red")

block = Image.new("RGBA", (max(top.width, bot.width) + 300, top.height + bot.height + 120))
br = brush(int(bot.width * 1.05), 200)
block.alpha_composite(br, (-10, top.height - 115 + int(bot.height * 0.62)))
block.alpha_composite(top, (40, 30))
block.alpha_composite(bot, (0, top.height - 115))
block = block.rotate(7, expand=True, resample=Image.BICUBIC)
# red outer glow
a = block.split()[3].filter(ImageFilter.GaussianBlur(28))
glowL = Image.new("RGBA", block.size, (255, 20, 20, 0)); glowL.putalpha(a.point(lambda v: int(v * 0.85)))
scale = 1080 / block.width
block = block.resize((int(block.width * scale), int(block.height * scale)), Image.LANCZOS)
glowL = glowL.resize(block.size, Image.LANCZOS)
pos = (30, int(OH * 0.5 - block.height * 0.5) - 20)
photo.alpha_composite(glowL, pos)
photo.alpha_composite(block, pos)
photo.convert("RGB").save(out, quality=94)
