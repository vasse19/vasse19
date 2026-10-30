import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"

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

