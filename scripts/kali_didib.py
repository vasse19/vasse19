"""Kali Muscle-style edit (Didi B « Shogun in Lagos » / Cardi B « WAP »), same engine as vlog_kali.py: motion-design intro on a red grid,
neon text (stacked lines, typewriter with cursor), cut-out artist with glow, covers, flags, light-leak burns,
punch-in reframing every ~2 s, tunnel vignette on the strongest line, 3D cards, neon word captions, -14 LUFS."""
import json, sys, subprocess, os, numpy as np, cv2, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from fx3d import text3d

SRC, WORK, OUT, LOGO = sys.argv[1:5]
# his library (assets/): copied into the work folder unless a file of that name is already there
import shutil
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
for _n, _p in {'burn12.mp4': 'transitions/burn-transition-12.mp4', 'riser.mp3': 'sfx/riser-metallic-transition.mp3', 'red.mp4': 'backgrounds/red-gradient.mp4'}.items():
    if not os.path.exists(f"{WORK}/{_n}"): shutil.copy(os.path.join(LIB, _p), f"{WORK}/{_n}")
W, H, FPS = 1080, 1920, 30
END = 64.66
ANTON = os.path.expanduser("~/.fonts/anton-latin-400.ttf")

# ---------- transcript (Parakeet: whole file for 0-7 s, short windows after) + fixes ----------
words = [w for w in json.load(open(f"{WORK}/wm.json"))] + [w for w in json.load(open(f"{WORK}/w4.json")) if w["s"] < 11.6]
words.sort(key=lambda w: w["s"])
def near(t): return min(words, key=lambda w: abs(w["s"] - t))
def ren(t, txt): near(t)["w"] = txt
def rm(t):
    global words; x = near(t); words = [w for w in words if w is not x]
def add(t, txt): words.append({"w": txt, "s": t}); words.sort(key=lambda w: w["s"])
ren(3.28, "de"); ren(3.44, "Didi"); add(3.70, "B,")
ren(7.16, "dans"); ren(8.36, "d'autre"); ren(9.08, "in"); ren(9.24, "Lagos.")
ren(22.40, "Cardi"); add(22.75, "B")
add(27.35, "Thee")
ren(31.10, "2025 ?"); rm(31.18); rm(31.34); rm(31.50)
ren(40.26, "l'APRODEMCI."); rm(40.34); rm(40.74)
rm(34.66); rm(36.70); ren(44.48, "SNEP,"); ren(56.56, "tes"); ren(59.56, "Y'en")
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP_SRC = [(15.55, 15.9), (43.7, 44.38), (62.15, END)]   # unclear words: audio kept, no caption

# ---------- jump cuts ----------
DROP = [(18.15, 20.42)]    # unclear line about a concert next week
def dropped(t): return any(a <= t < b for a, b in DROP)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-ac", "1", "-ar", "16000", f"{WORK}/edl.wav"], check=True)
au, sr = sf.read(f"{WORK}/edl.wav"); au = au[:int(END * sr)]; hop = int(0.02 * sr)
db = 20 * np.log10(np.array([np.sqrt(np.mean(au[i:i + hop] ** 2)) for i in range(0, len(au) - hop, hop)]) + 1e-9)
db = np.convolve(db, np.ones(3) / 3, mode="same")
keep = db >= np.median(db) - 10
i = 0
while i < len(keep):
    if not keep[i]:
        j = i
        while j < len(keep) and not keep[j]: j += 1
        if (j - i) * 0.02 < 0.16: keep[i:j] = True
        else: keep[i:i + 3] = True; keep[max(j - 3, i):j] = True
        i = j
    else: i += 1
keep[int(59.4 / 0.02):] = True                       # sign-off whole
for a0, b0 in DROP: keep[int(a0 / 0.02):int(b0 / 0.02)] = False
runs = []
for k, v in enumerate(keep):
    if v:
        if runs and runs[-1][1] == k: runs[-1][1] = k + 1
        else: runs.append([k, k + 1])
segs = [[a0 * 0.02, b0 * 0.02] for a0, b0 in runs if (b0 - a0) * 0.02 >= 0.12]
segs[-1][1] = END
def remap(t):
    acc = 0.0
    for a, b in segs:
        if t < a: return acc
        if t < b: return acc + t - a
        acc += b - a
    return acc
DUR = sum(b - a for a, b in segs)
fc = []
for i, (a, b) in enumerate(segs):
    fc.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a]")
CUT = f"{WORK}/cut.mov"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-r", "30", "-c:a", "pcm_s16le", CUT], check=True)
nocap_ids = {id(w) for w in words if any(a <= w["s"] < b for a, b in NOCAP_SRC)}
words = [dict(w, s=remap(w["s"]), e=remap(w["e"]), nc=id(w) in nocap_ids) for w in words if not dropped(w["s"])]
json.dump(words, open(f"{WORK}/words_final.json", "w"), ensure_ascii=False)
print(f"{len(segs)} segments, {DUR:.1f}s (from {END}s)", flush=True)
N = int(DUR * FPS); ft = np.arange(N) / FPS
key = lambda w: w["w"].lower().strip(",.?!…")
def at(text, nth=0): return [w for w in words if key(w) == text][nth]["s"]

subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(__file__), "faces_any.py"), CUT, f"{WORK}/faces.json"], check=True, capture_output=True)
f = np.array(json.load(open(f"{WORK}/faces.json")))
fx, fy = np.interp(ft, f[:, 0], f[:, 1]), np.interp(ft, f[:, 0], f[:, 2])
ker = np.ones(15) / 15
sm = lambda v: np.convolve(np.pad(v, 7, mode="edge"), ker, mode="valid")
fx, fy = sm(sm(fx)), sm(sm(fy))
SW, SH = 512, 910

# ---------- graphics helpers (images are float RGBA in RGB order; frames are float BGR) ----------
def paste(dst, img, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0: img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = img.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    src = img[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4] * alpha
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a
_neon = {}
def neon(text, size, rgb):
    """Neon text: light core, coloured glow."""
    k = (text, size, rgb)
    if k in _neon: return _neon[k]
    font = ImageFont.truetype(ANTON, size); pad = int(size * 0.45)
    x0, y0, x1, y1 = font.getbbox(text or " ")
    im = Image.new("L", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad)); ImageDraw.Draw(im).text((pad - x0, pad - y0), text, font=font, fill=255)
    m = np.asarray(im).astype(np.float32) / 255
    g = np.clip(cv2.GaussianBlur(m, (0, 0), size * 0.16) * 1.5 + cv2.GaussianBlur(m, (0, 0), size * 0.05) * 0.9, 0, 1)
    c = np.array(rgb, np.float32) / 255; core = c * 0.45 + 0.55
    a = np.clip(g * 0.85 + m, 0, 1)
    col = (c * (g * 0.85 * (1 - m))[..., None] + core * m[..., None]) / np.maximum(a, 1e-4)[..., None]
    out = np.dstack([np.clip(col, 0, 1), a]); _neon[k] = (out, pad); return out, pad
YEL, RED, WHT, GRN, GOLD = (255, 222, 40), (255, 40, 50), (255, 255, 255), (40, 230, 110), (255, 190, 60)
def stack(img, t, items, size, y0, gap):
    """Lines appear one by one (pop), stacked from y0."""
    for n, (t0, txt, col) in enumerate(items):
        k = t - t0
        if k < 0: continue
        im, _ = neon(txt, size, col)
        s = 1.0 + 0.25 * max(0.0, 1 - k / 0.12) ** 2
        paste(img, im, W / 2, y0 + n * gap, s, min(k / 0.08, 1))
def typewriter(img, t, t0, text, size, col, y, cps=16):
    k = t - t0
    if k < 0: return
    n = min(len(text), int(k * cps) + 1); pre = text[:n]
    full, pad = neon(text, size, col); im, _ = neon(pre, size, col)
    left = W / 2 - full.shape[1] / 2
    paste(img, im, left + im.shape[1] / 2, y)
    if n < len(text) or (k * 2.2) % 1 < 0.6:            # cursor: solid while typing, then blinking
        x = int(left + im.shape[1] - pad + 10); hh = int(size * 0.42)
        img[max(int(y - hh), 0):int(y + hh), x:x + 9] = 1.0
def rgba_file(path, width):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED); s = width / im.shape[1]
    im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
    if im.shape[2] == 3: im = np.dstack([im, np.ones(im.shape[:2], np.float32)])
    return im[..., [2, 1, 0, 3]]
def glow_rgba(im, rgb, sigma, strength):
    """Put a coloured glow behind an RGBA image (padding added)."""
    p = int(sigma * 3); im = cv2.copyMakeBorder(im, p, p, p, p, cv2.BORDER_CONSTANT, value=0)
    g = np.clip(cv2.GaussianBlur(cv2.dilate(im[..., 3], np.ones((9, 9), np.uint8)), (0, 0), sigma) * strength, 0, 1)
    a = im[..., 3]; ga = g * (1 - a)
    col = (im[..., :3] * a[..., None] + np.array(rgb, np.float32) / 255 * ga[..., None]) / np.maximum(a + ga, 1e-4)[..., None]
    return np.dstack([col, np.clip(a + ga, 0, 1)])
def cover_card(path, width, rim):
    im = cv2.imread(path); s = width / im.shape[1]
    c = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4)
    c = cv2.addWeighted(c, 1.5, cv2.GaussianBlur(c, (0, 0), 2.2), -0.5, 0)
    c[:7] = c[-7:] = c[:, :7] = c[:, -7:] = rim[::-1]
    rgba = np.dstack([c[..., ::-1].astype(np.float32) / 255, np.ones(c.shape[:2], np.float32)])
    return glow_rgba(rgba, rim, 26, 1.1)
DIDI = cover_card(f"{WORK}/didib.jpg", 600, (255, 255, 255))
SHOG = cover_card(f"{WORK}/shogun.jpg", 820, (255, 170, 60))
CALB = cover_card(f"{WORK}/cardi_album.jpg", 920, (255, 60, 60))
WAPC = cover_card(f"{WORK}/wap.jpg", 760, (255, 120, 200))
WAPM = cover_card(f"{WORK}/wap.jpg", 300, (255, 120, 200))
def flag(kind):
    w, h = 300, 200; f = np.zeros((h, w, 3), np.float32)
    if kind == "ci":
        f[:, :100] = (247, 127, 0); f[:, 100:200] = (255, 255, 255); f[:, 200:] = (0, 158, 96)
    elif kind == "ng":
        f[:, :100] = (0, 135, 81); f[:, 100:200] = (255, 255, 255); f[:, 200:] = (0, 135, 81)
    else:
        for r in range(13): f[r * h // 13:(r + 1) * h // 13] = (178, 34, 52) if r % 2 == 0 else (255, 255, 255)
        f[:7 * h // 13, :120] = (60, 59, 110)
        for r in range(5):
            for q in range(6): cv2.circle(f, (10 + q * 20, 11 + r * 21), 4, (255, 255, 255), -1, cv2.LINE_AA)
    rgba = np.dstack([f / 255, np.ones((h, w), np.float32)])
    return glow_rgba(rgba, (255, 255, 255), 12, 1.2)
FLAG_CI, FLAG_NG = flag("ci"), flag("ng")
logo = rgba_file(LOGO, 640)

# backgrounds: his red gradient clip + a grid that drifts down + rising embers
rd = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WORK}/red.mp4", "-vf", "fps=30,scale=270:480", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                    capture_output=True, check=True).stdout
REDBG = np.frombuffer(rd, np.uint8).reshape(-1, 480, 270, 3)
G = 72
gridm = np.zeros((H + G, W), np.float32)
gridm[::G, :] = 1; gridm[:, ::G] = 1
gridm = cv2.GaussianBlur(gridm, (0, 0), 0.8) * 1.6
rng = np.random.default_rng(7)
EMB = np.c_[rng.uniform(0, W, 160), rng.uniform(0, H, 160), rng.uniform(40, 160, 160), rng.uniform(1.5, 4.5, 160), rng.uniform(0, 6.3, 160)]
def bg(kind, t):
    if kind == "red":
        img = cv2.resize(REDBG[int(t * FPS) % len(REDBG)], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
        line = np.array([0.15, 0.15, 0.75], np.float32)
    else:
        img = np.zeros((H, W, 3), np.float32); img[:] = (0.03, 0.02, 0.04)
        line = np.array([0.1, 0.1, 0.85], np.float32)
    off = int(t * 18) % G
    gm = gridm[G - off:G - off + H, :, None]
    img = img * (1 - 0.35 * gm) + line * 0.35 * gm
    lay = np.zeros((H, W), np.float32)
    for x, y, v, r, ph in EMB:
        yy = (y - v * t) % H; xx = x + 18 * np.sin(t * 1.3 + ph)
        cv2.circle(lay, (int(xx), int(yy)), int(r), 0.5 + 0.5 * np.sin(t * 7 + ph), -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.6)[..., None]
    return np.clip(img + lay * np.array([0.2, 0.6, 1.0], np.float32), 0, 1)
yy_, xx_ = np.mgrid[0:H, 0:W]
TUNNEL = np.clip(1.25 - np.sqrt(((xx_ - W / 2) / (W * 0.62)) ** 2 + ((yy_ - H * 0.42) / (H * 0.5)) ** 2) * 1.25, 0.05, 1).astype(np.float32)[..., None]

# ---------- 3D cards (house style) ----------
def block(top, bot, width, maxh):
    lines = [text3d(l, 220, "chrome", 30) for l in top.split("|")] + [text3d(l, 210, "red", 30) for l in bot.split("|")]
    im = Image.new("RGBA", (max(l.width for l in lines) + 40, sum(l.height for l in lines) - 110 * (len(lines) - 1)))
    y = 0
    for l in lines:
        im.alpha_composite(l, ((im.width - l.width) // 2, y)); y += l.height - 110
    im = im.rotate(5, expand=True, resample=Image.BICUBIC)
    sc = min(width / im.width, maxh / im.height)
    return np.asarray(im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)).astype(np.float32) / 255
R = remap                                   # all times below are written in source seconds
PINK = (255, 110, 200)
CARDS = [  # start, end, top, bottom, kind, centre y
    (0.0, R(1.90), "DIDI B", "TRICHE OU|STRATÉGIE ?", "hook", 1180),
    (R(33.82), R(34.88), "VOUS VOYEZ", "LE DÉLIRE ?", "card", 960),
    (R(59.50), R(62.15), "TRICHE OU", "STRATÉGIE ?", "over", 1000),
    (R(62.15), DUR, "LE BIG", "VASS", "end", 1370),
]
card_img = [block(c[2], c[3], 1040, {"hook": 900, "end": 700, "over": 700}.get(c[4], 1000)) for c in CARDS]
def in_card(t): return any(c[0] <= t < c[1] for c in CARDS)

# ---------- scenes: (start, end, background, captions?) ; everything else is the face-cam ----------
SCENES = [
    (R(1.90), R(7.12), "didib", False),
    (R(7.12), R(9.70), "shogun", False),
    (R(14.45), R(18.15), "nigeria", False),
    (R(22.20), R(33.82), "cardi", False),
    (R(48.88), R(53.66), "zero", False),
    (R(53.66), R(58.50), "ci", False),
]
def scene_at(t):
    for s in SCENES:
        if s[0] <= t < s[1]: return s
    return None
# overlays on the face-cam: (start, end, dim, tunnel, draw fn)
OVER = [
    (R(10.45), R(14.45), 0.45, False,
     lambda img, t: (stack(img, t, [(R(10.86), "PAS DE LA", YEL), (R(11.34), "TRICHE", RED)], 170, 560, 200),
                     typewriter(img, t, R(12.38), "UNE STRATÉGIE", 150, YEL, 1000, 20))),
    (R(38.55), R(41.08), 0.45, False,
     lambda img, t: (stack(img, t, [(R(38.84), "PAS LA FAUTE", WHT), (R(39.40), "DES ARTISTES", YEL)], 160, 600, 190),
                     stack(img, t, [(R(39.94), "C'EST PLUS", WHT)], 120, 1000, 0),
                     typewriter(img, t, R(40.26), "L'APRODEMCI", 180, RED, 1170, 22))),
    (R(41.08), R(42.75), 0.45, False,
     lambda img, t: stack(img, t, [(R(41.12), "C'EST EUX QUI", WHT), (R(41.60), "DOIVENT FIXER", YEL), (R(42.16), "LES RÈGLES", RED)], 150, 520, 180)),
    (R(44.35), R(45.10), 0.4, False,
     lambda img, t: typewriter(img, t, R(44.40), "LE SNEP", 200, WHT, 640, 14)),
    (R(46.80), R(47.34), 0.15, True,
     lambda img, t: stack(img, t, [(R(46.84), "C'EST MORT", RED)], 210, 640, 0)),
]
def over_at(t): return [o for o in OVER if o[0] <= t < o[1]]

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def settle(k): return (1.1 - 0.1 * min(k / 0.3, 1) ** 0.4) * (1 + 0.03 * k)
def draw_scene(name, t, k):
    img = bg("black" if name == "zero" else "red", t)
    if name == "didib":
        paste(img, DIDI, W / 2, 1260, settle(k))
        typewriter(img, t, R(1.92), "DES GENS SE PLAIGNENT", 80, WHT, 180, 24)
        stack(img, t, [(R(2.96), "L'ALBUM DE DIDI B", WHT), (R(5.20), "UNE EXCLU", YEL), (R(6.16), "DÉJÀ ÉCOUTÉE", RED)], 125, 300, 165)
    elif name == "shogun":
        paste(img, SHOG, W / 2, 880, settle(k))
        stack(img, t, [(R(7.40), "SON PROCHAIN ALBUM", WHT)], 100, 330, 0)
        typewriter(img, t, R(8.68), "SHOGUN IN LAGOS", 140, GOLD, 1430, 20)
        stack(img, t, [(R(9.30), "LE 6 NOVEMBRE", WHT)], 110, 1600, 0)
    elif name == "nigeria":
        paste(img, DIDI, W / 2, 1300, 0.9 * settle(k))
        stack(img, t, [(R(14.80), "LE NIGERIA", GRN), (R(16.48), "SON BUT :", WHT), (R(17.20), "S'EXPORTER", YEL)], 140, 300, 165)
        for t0, fl, x in [(R(14.80), FLAG_NG, 830), (R(16.48), FLAG_CI, 250)]:
            if t >= t0: paste(img, fl, x, 860, popk(t, t0))
    elif name == "cardi":
        if t < R(24.50):
            paste(img, CALB, W / 2, 900, settle(k))
            typewriter(img, t, R(22.24), "MÊME CARDI B", 150, WHT, 330, 16)
            stack(img, t, [(R(23.44), "CETTE STRATÉGIE", YEL)], 130, 1430, 0)
        elif t < R(28.20):
            paste(img, WAPC, W / 2, 900, settle(t - R(24.50)))
            stack(img, t, [(R(24.68), "EN 2020", WHT)], 150, 330, 0)
            typewriter(img, t, R(26.60), "WAP", 220, PINK, 1430, 10)
            stack(img, t, [(R(27.08), "AVEC MEGAN THEE STALLION", WHT)], 80, 1620, 0)
        else:
            paste(img, CALB, W / 2, 900, settle(t - R(28.20)))
            typewriter(img, t, R(28.38), "QU'EST-CE QUI S'EST PASSÉ ?", 80, WHT, 180, 24)
            stack(img, t, [(R(29.82), "SON ALBUM", WHT), (R(31.10), "2025", YEL)], 140, 300, 165)
            if t >= R(32.10): paste(img, WAPM, 820, 1180, popk(t, R(32.10)))
            stack(img, t, [(R(32.66), "+ WAP DEDANS", PINK)], 140, 1520, 0)
    elif name == "zero":
        stack(img, t, [(R(48.92), "MÊME AVEC DES", WHT), (R(49.88), "EXCLUSIVITÉS", YEL)], 130, 380, 160)
        t1, t2 = R(50.84), R(51.48)
        if t >= t1:
            v = int(1_250_000 * max(0.0, 1 - (t - t1) / (t2 - t1)) ** 2)
            im, _ = neon(f"{v:,}".replace(",", " ") if v else "0", 220, RED if v == 0 else YEL)
            paste(img, im, W / 2, 900, popk(t, t2) if t >= t2 else 1.0)
            stack(img, t, [(t1, "STREAMS", WHT)], 100, 1080, 0)
        stack(img, t, [(R(52.74), "RETOUR À ZÉRO", RED)], 160, 1350, 0)
    elif name == "ci":
        stack(img, t, [(R(54.02), "EN CÔTE D'IVOIRE", WHT)], 140, 330, 0)
        if t >= R(54.02): paste(img, FLAG_CI, W / 2, 680, 1.6 * popk(t, R(54.02)))
        stack(img, t, [(R(54.82), "TU PEUX METTRE", WHT), (R(55.30), "DES EXCLUS", YEL), (R(56.56), "TES STREAMS", WHT),
                       (R(57.52), "COMPTABILISÉS", GRN)], 130, 1000, 165)
    return img

# ---------- shots: punch-in reframing about every 2 s ----------
cuts = [0.0]
for w in words:
    if (w["w"][-1] in ",.?" and w["e"] - cuts[-1] > 1.6) or w["s"] - cuts[-1] > 2.5:
        cuts.append(round(w["e"] if w["w"][-1] in ",.?" else w["s"], 2))
CYCLE = ["MED", "TIGHT", "WIDE", "TIGHT"]
SHOTS = [(c, CYCLE[i % 4]) for i, c in enumerate(cuts)]
def shot_at(t):
    m = SHOTS[0][1]
    for s_, mm in SHOTS:
        if t >= s_: m = mm
    return m
z = np.ones(N)
def punch(t0, amt, hold=0.3, rel=0.45):
    a = np.clip((ft - t0) / 0.07, 0, 1); a = a * a * (3 - 2 * a)
    r = np.clip((ft - t0 - hold) / rel, 0, 1); r = r * r * (3 - 2 * r)
    return amt * a * (1 - r)
EMPH_RED = {"triche", "mort", "zéro", "règles", "faute", "stratégie"}
EMPH_WHITE = {"l'aprodemci", "didi", "b", "shogun", "lagos", "nigeria", "cardi", "wap", "megan", "thee", "stallion", "snep", "côte", "d'ivoire", "2020", "2025"}
for w in words:
    if key(w) in EMPH_RED: z += punch(w["s"], 0.1)
z += punch(R(46.84), 0.14, 0.5, 0.4)
for c, _ in SHOTS[1:]: z += punch(c - 0.001, 0.06, 0.0, 0.25)
shake = np.zeros((N, 2)); rng2 = np.random.default_rng(4)
for t0 in [c[0] for c in CARDS] + [R(46.84)]:
    m = (ft >= t0) & (ft < t0 + 0.3)
    shake[m] = rng2.normal(0, 10, (m.sum(), 2)) * np.linspace(1, 0, m.sum())[:, None]
def crop_rect(i):
    zz = z[i] * {"WIDE": 1.0, "MED": 1.15, "TIGHT": 1.32}[shot_at(ft[i])]
    ch = SH / zz; cw = ch * W / H
    return np.clip(fx[i] - cw / 2, 0, SW - cw), np.clip(fy[i] - ch * 0.4, 0, SH - ch), cw, ch

# ---------- captions: neon yellow, one word at a time ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: G,Anton,172,&H6000E5FF,&H0000E5FF,&H8000C8FF,&H00000000,0,0,0,0,100,100,1,0,1,10,0,5,40,40,0,1
Style: W,Anton,172,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,4,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
def capped(t):
    s = scene_at(t)
    if s and not s[3]: return False
    return not in_card(t) and not over_at(t)
for w in words:
    if w["nc"] or not capped(w["s"]): continue
    e = w["e"]
    for b in [c[0] for c in CARDS] + [o[0] for o in OVER] + [s[0] for s in SCENES]:
        if w["s"] < b < e: e = b
    col = (r"\c&H002A2AFF&\3c&H002A2AFF&" if key(w) in EMPH_RED else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if key(w) in EMPH_WHITE else ""))
    txt = w["w"].upper().rstrip(",.?!…") or w["w"]
    y = 1620 if scene_at(w["s"]) else 1420
    pop = r"\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)"
    ass.append(f"Dialogue: 0,{ts(w['s'])},{ts(e)},G,,0,0,0,,{{\\an5\\pos(540,{y}){col}\\blur14{pop}}}{txt}")
    ass.append(f"Dialogue: 1,{ts(w['s'])},{ts(e)},W,,0,0,0,,{{\\an5\\pos(540,{y}){col.split(chr(92) + '3c')[0] if col else ''}{pop}}}{txt}")
open(f"{WORK}/caps.ass", "w").write("\n".join(ass) + "\n")

# ---------- sound design ----------
SR = 48000
def synth(args, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", args, "-ac", "1", "-ar", str(SR), path], check=True)
    return load(path)
def load(path): return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]), np.float32)
whoosh = synth("anoisesrc=d=0.45:c=pink:a=0.9,highpass=f=600,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.18:d=0.27", f"{WORK}/whoosh.wav")
hit = synth("sine=f=52:d=0.7,volume=1.4,afade=t=out:st=0.05:d=0.65", f"{WORK}/hit.wav")
click = synth("anoisesrc=d=0.03:c=white:a=0.8,highpass=f=2500,afade=t=out:st=0.004:d=0.026", f"{WORK}/click.wav")
riser = load(f"{WORK}/riser.mp3"); RISER_PEAK = 2.95
burn_snd = load(f"{WORK}/burn12.mp4")
sfx = np.zeros(int(DUR * SR) + SR, np.float32)
def place(snd, t, g):
    i = int(t * SR)
    if i < 0: snd, i = snd[-i:], 0
    n = min(len(snd), len(sfx) - i); sfx[i:i + n] += snd[:n] * g
for c, _ in SHOTS[1:]:
    if not scene_at(c): place(whoosh, c - 0.2, 0.08)
for s in SCENES: place(whoosh, s[0] - 0.2, 0.22)
for c in CARDS: place(hit, c[0], 0.45); place(whoosh, c[0] - 0.25, 0.2)
place(hit, R(46.84), 0.45); place(hit, R(51.48), 0.4)
for t0, txt, cps in [(R(8.68), "SHOGUN IN LAGOS", 20), (R(12.38), "UNE STRATÉGIE", 20), (R(22.24), "MÊME CARDI B", 16),
                     (R(26.60), "WAP", 10), (R(44.40), "LE SNEP", 14), (R(40.26), "L'APRODEMCI", 22),
                     (R(1.92), "DES GENS SE PLAIGNENT", 24), (R(28.38), "QU'EST-CE QUI S'EST PASSÉ ?", 24)]:
    for j, ch in enumerate(txt):
        if ch != " ": place(click, t0 + j / cps, 0.25)
place(riser, R(8.68) - RISER_PEAK, 0.55)
place(riser, R(59.50) - RISER_PEAK, 0.55)
BURN_PEAK = 11 / FPS
BURN_AT = [R(7.12), R(9.70), R(22.20), R(53.66), R(59.50)]
for b_ in BURN_AT: place(burn_snd, b_ - BURN_PEAK, 0.6)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", f"{WORK}/sfx.wav"], input=sfx[:int(DUR * SR)].tobytes(), check=True)

# ---------- render ----------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", CUT, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
VF = f"unsharp=5:5:0.6,eq=contrast=1.06:saturation=1.1,vignette=angle=PI/6,noise=alls=3:allf=t+u,ass={WORK}/caps.ass:fontsdir={os.path.dirname(ANTON)},format=yuv420p"
VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", VF, "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY], stdin=subprocess.PIPE)
bdec = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WORK}/burn12.mp4", "-vf", f"scale=-2:{H},crop={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
BURN = np.frombuffer(bdec, np.uint8).reshape(-1, H, W, 3)
FR = SW * SH * 3
for i in range(N):
    buf = dec.stdout.read(FR)
    if len(buf) < FR: break
    fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3); t = ft[i]
    sc = scene_at(t)
    if sc:
        k = t - sc[0]; img = draw_scene(sc[2], t, k)
        if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.6, 0, 1)
    else:
        x0, y0, cw, ch = crop_rect(i)
        x0 += shake[i, 0] * cw / W; y0 += shake[i, 1] * ch / H
        M = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
        img = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
        for a, b, dim, tun, fn in over_at(t):
            r = min((t - a) / 0.15, 1)
            if dim: img = img * (1 - dim * r)
            if tun: img = img * (1 - r + r * TUNNEL)
            fn(img, t)
    for ci, c in enumerate(CARDS):
        if not (c[0] <= t < c[1]): continue
        k = t - c[0]
        if c[4] == "card":
            bgc = cv2.GaussianBlur(img, (0, 0), 22); L = bgc.mean(axis=2, keepdims=True)
            img = np.clip(L * np.array([0.12, 0.12, 0.9]) * 1.3 + bgc * 0.15, 0, 1)
        elif c[4] == "end": img = img * 0.45
        elif c[4] == "over": img = img * (1 - 0.4 * min(k / 0.2, 1))
        if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.8, 0, 1)
        s = 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1)
        if c[4] == "end": paste(img, logo, W / 2, 700, min(k / 0.25, 1) * 0.15 + 0.85)
        paste(img, card_img[ci], W / 2 + shake[i, 0], c[5] + shake[i, 1], s)
    for b_ in BURN_AT:
        k = int(round((t - (b_ - BURN_PEAK)) * FPS))
        if 0 <= k < len(BURN): img = 1 - (1 - img) * (1 - BURN[k].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if i % 300 == 0: print(f"frame {i}/{N}", flush=True)
enc.stdin.close(); enc.wait()
dec.stdout.close(); dec.kill(); dec.wait()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", CUT, "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]highpass=f=70,volume=12dB,acompressor=threshold=-22dB:ratio=4:attack=5:release=90:makeup=3dB,loudnorm=I=-14:TP=-1.5:LRA=7,"
    "aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.75:level=false[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, len(SHOTS), "shots", flush=True)
