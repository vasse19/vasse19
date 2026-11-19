"""YouTube 16:9 video from a voice-over, no face-cam (« Burna Boy : 14 nominations aux Grammys, 1 seule victoire »).
Style taken from the explainer he asked to study: photos and covers shown as glowing CARDS over a blurred copy of
themselves, keywords only on screen (no full subtitles), counters on numbers, 3D chapter titles, white flash on cuts,
his burn transition on chapter changes, logo pulsing with his voice, end card. Gentle silence cut for long-form.
usage: yt_burna_grammys.py WORK OUT.mp4    (WORK holds src.mp3, words.json and img/*.jpg)"""
import sys, os, json, subprocess, numpy as np, cv2, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import LIB, ANTON, YEL, RED, WHT, GRN, GOLD, neon, rgba_file, glow_rgba, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IMG = f"{WORK}/img"
W, H, FPS, SR = 1920, 1080, 30, 48000
PREVIEW = os.environ.get("PREVIEW")                   # "a-b" (output seconds) renders only that range, no audio mix

# ---------- transcript (source seconds) ----------
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WORK}/src.mp3", "-ac", "1", "-ar", "16000", f"{WORK}/a16.wav"], check=True)
au, sr16 = sf.read(f"{WORK}/a16.wav"); END = len(au) / sr16
words = sorted(json.load(open(f"{WORK}/words.json")), key=lambda w: w["s"])
norm = lambda s: s.lower().strip(",.?!…«» :")
def T(sub, after=0.0):
    """Start time of the first word containing `sub` after `after` (source seconds)."""
    for w in words:
        if w["s"] >= after and sub in norm(w["w"]): return w["s"]
    raise KeyError(f"{sub} after {after}")

DROP = []

# ---------- silences shortened (long-form: pauses kept short, not removed) ----------
hop = int(0.02 * sr16)
db = 20 * np.log10(np.array([np.sqrt(np.mean(au[i:i + hop] ** 2)) for i in range(0, len(au) - hop, hop)]) + 1e-9)
db = np.convolve(db, np.ones(3) / 3, mode="same")
keep = db >= np.median(db) - 12
i = 0
while i < len(keep):
    if not keep[i]:
        j = i
        while j < len(keep) and not keep[j]: j += 1
        if (j - i) * 0.02 < 0.30: keep[i:j] = True
        else: keep[i:i + 6] = True; keep[max(j - 6, i):j] = True
        i = j
    else: i += 1
for a, b in DROP: keep[int(a / 0.02):int(b / 0.02)] = False
keep[int(259.0 / 0.02):] = True                       # sign-off kept whole
runs = []
for k, v in enumerate(keep):
    if v:
        if runs and runs[-1][1] == k: runs[-1][1] = k + 1
        else: runs.append([k, k + 1])
segs = [[a * 0.02, b * 0.02] for a, b in runs if (b - a) * 0.02 >= 0.10]
segs[-1][1] = END
fc = [f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{n}]" for n, (a, b) in enumerate(segs)]
fc.append("".join(f"[a{n}]" for n in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[a]")
if not os.path.exists(f"{WORK}/voice_cut.wav") or not PREVIEW:
    open(f"{WORK}/fc.txt", "w").write(";".join(fc))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WORK}/src.mp3", "-filter_complex_script", f"{WORK}/fc.txt", "-map", "[a]",
                    "-ar", str(SR), "-ac", "1", f"{WORK}/voice_cut.wav"], check=True)
def R0(t):
    acc = 0.0
    for a, b in segs:
        if t < a: return acc
        if t < b: return acc + t - a
        acc += b - a
    return acc
CLIPS = os.path.join(REPO, "assets/extraits/musique")
INS = [(84.05, 7.6, "burna-boy-grammy-2021-victoire-16x9.mp4", 21.5)]   # his acceptance speech, with its own sound
INS_LOOK = {84.05: ("twice-as-tall.jpg", "BURNA BOY · GRAMMY 2021", "SOURCE : GRAMMYS / RECORDING ACADEMY",
                    [(0.1, 3.3, "« L'AFRIQUE EST DANS LA PLACE ! »"), (3.4, 7.6, "« UNE GRANDE VICTOIRE POUR MA GÉNÉRATION D'AFRICAINS »")])}
def R(t): return R0(t) + sum(d for at, d, *_ in INS if t >= at)
INS_OUT = [(R0(at) + sum(d2 for at2, d2, *_ in INS if at2 < at), d, clip, ss, at) for at, d, clip, ss in INS]
DUR = sum(b - a for a, b in segs) + sum(x[1] for x in INS); N = int(DUR * FPS)
if os.environ.get("EXPORT_WORDS"):                     # words with their time in the finished video (for Shorts captions)
    out = [{"w": w["w"], "s": R(w["s"]), "e": R(w["e"]), "src": w["s"]} for w in words if any(a <= w["s"] < b for a, b in segs)]
    json.dump({"words": out, "ins": INS_OUT}, open(os.environ["EXPORT_WORDS"], "w"), ensure_ascii=False); sys.exit()
print(f"{len(segs)} segments, {DUR:.1f}s (from {END:.1f}s)", flush=True)
voice = sf.read(f"{WORK}/voice_cut.wav")[0]
for at, d, *_ in sorted(INS, reverse=True):          # silence in his voice while the clip speaks
    i0 = int(R0(at) * SR); voice = np.concatenate([voice[:i0], np.zeros(int(d * SR)), voice[i0:]])
sf.write(f"{WORK}/voice_ins.wav", voice, SR)
lvl = np.array([np.sqrt(np.mean(voice[int(i / FPS * SR):int((i + 1) / FPS * SR)] ** 2) + 1e-12) for i in range(N)])
lvl = np.clip(lvl / (np.percentile(lvl, 95) + 1e-9), 0, 1.2)

# ---------- drawing helpers (frames: float BGR [0,1]; images: float RGBA, RGB order) ----------
def paste(dst, img, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.003: return
    if scale != 1.0: img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = img.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    src = img[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4] * alpha
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a
def popk(k): return 1 + 0.28 * max(0.0, 1 - max(k, 0) / 0.13) ** 2
def settle(k): return (1.12 - 0.12 * min(max(k, 0) / 0.32, 1) ** 0.4) * (1 + 0.012 * max(k, 0))
_cards = {}
def card(name, width, rim=(255, 255, 255), gray=False):
    key = (name, width, rim, gray)
    if key not in _cards:
        im = cv2.imread(f"{IMG}/{name}"); s = width / im.shape[1]
        c = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA)
        c = cv2.addWeighted(c, 1.35, cv2.GaussianBlur(c, (0, 0), 2), -0.35, 0)
        if gray: c = cv2.cvtColor(cv2.cvtColor(c, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR); c = (c * 0.55).astype(np.uint8)
        c[:6] = c[-6:] = c[:, :6] = c[:, -6:] = rim[::-1]
        _cards[key] = glow_rgba(np.dstack([c[..., ::-1].astype(np.float32) / 255, np.ones(c.shape[:2], np.float32)]), rim, 22, 1.0)
    return _cards[key]
_png = {}
def png(rel, width):
    if (rel, width) not in _png: _png[(rel, width)] = rgba_file(os.path.join(LIB, rel), width)
    return _png[(rel, width)]
_em = {}
def emoji(ch, size):
    if (ch, size) not in _em:
        f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109); im = Image.new("RGBA", (300, 160))
        ImageDraw.Draw(im).text((20, 15), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox()); im = im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)
        _em[(ch, size)] = np.asarray(im).astype(np.float32) / 255
    return _em[(ch, size)]
_box = {}
def kbox(text, size=64):
    """Keyword in a dark box with a red bar (lower-third style of the explainer)."""
    if (text, size) not in _box:
        f = ImageFont.truetype(ANTON, size); x0, y0, x1, y1 = f.getbbox(text); px, py = int(size * 0.45), int(size * 0.28)
        im = Image.new("RGBA", (x1 - x0 + 2 * px + 14, y1 - y0 + 2 * py), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), 10, fill=(8, 6, 10, 215)); d.rectangle((0, 0, 13, im.height), fill=(230, 30, 45, 255))
        d.text((14 + px - x0, py - y0), text, font=f, fill=(255, 255, 255, 255))
        _box[(text, size)] = np.asarray(im).astype(np.float32) / 255
    return _box[(text, size)]
def stamp(text, size=110):
    if ("stamp", text, size) not in _box:
        f = ImageFont.truetype(ANTON, size); x0, y0, x1, y1 = f.getbbox(text); p = int(size * 0.3)
        im = Image.new("RGBA", (x1 - x0 + 2 * p, y1 - y0 + 2 * p)); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, im.width - 1, im.height - 1), outline=(235, 30, 40, 255), width=12)
        d.text((p - x0, p - y0), text, font=f, fill=(235, 30, 40, 255))
        im = im.rotate(-8, expand=True, resample=Image.BICUBIC)
        _box[("stamp", text, size)] = np.asarray(im).astype(np.float32) / 255
    return _box[("stamp", text, size)]

# ---------- backgrounds ----------
G = 80
gridm = np.zeros((H + G, W), np.float32); gridm[::G, :] = 1; gridm[:, ::G] = 1
gridm = cv2.GaussianBlur(gridm, (0, 0), 0.8) * 1.5
_rng = np.random.default_rng(7)
EMB = np.c_[_rng.uniform(0, W, 120), _rng.uniform(0, H, 120), _rng.uniform(30, 110, 120), _rng.uniform(1.5, 4.0, 120), _rng.uniform(0, 6.3, 120)]
yy, xx = np.ogrid[:H, :W]
VIG = np.clip(1.25 - np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 1.35, 0.25, 1).astype(np.float32)[..., None]
def embers(t, strength=1.0):
    lay = np.zeros((H, W), np.float32)
    for x, y, v, r, ph in EMB:
        cv2.circle(lay, (int(x + 16 * np.sin(t * 1.3 + ph)), int((y - v * t) % H)), int(r), 0.5 + 0.5 * np.sin(t * 7 + ph), -1, cv2.LINE_AA)
    return cv2.GaussianBlur(lay, (0, 0), 1.5)[..., None] * np.array([0.2, 0.55, 1.0], np.float32) * strength
_paper = {}
_blur = {}
def background(spec, t, k):
    if spec == "grid":
        img = np.zeros((H, W, 3), np.float32); img[:] = (0.035, 0.02, 0.05)
        gm = gridm[G - int(t * 16) % G:G - int(t * 16) % G + H, :, None]
        img = img * (1 - 0.35 * gm) + np.array([0.1, 0.1, 0.8], np.float32) * 0.3 * gm
        return np.clip(img * VIG + embers(t), 0, 1)
    if spec.startswith("paper_"):
        if spec not in _paper:
            tex = cv2.imread(os.path.join(LIB, f"backgrounds/grid-paper-{spec[6:]}.png"))
            _paper[spec] = cv2.resize(cv2.rotate(tex, cv2.ROTATE_90_CLOCKWISE), (W, H)).astype(np.float32) / 255
        img = np.roll(_paper[spec], int(t * 14) % 36, axis=1) * 0.55
        return np.clip(img * VIG + embers(t, 0.6), 0, 1)
    if spec not in _blur:                             # blurred, darkened, slightly warm copy of the scene's photo
        im = cv2.imread(f"{IMG}/{spec}"); s = max(W * 1.14 / im.shape[1], H * 1.14 / im.shape[0])
        im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
        im = cv2.GaussianBlur(im, (0, 0), 38).astype(np.float32) / 255
        im = im * 0.42 + np.array([0.02, 0.02, 0.10], np.float32)
        _blur[spec] = im
    im = _blur[spec]; mh, mw = im.shape[0] - H, im.shape[1] - W
    u = (np.sin(k * 0.12) + 1) / 2
    x0, y0 = int(mw * u), int(mh * (1 - u) * 0.6)
    return np.clip(im[y0:y0 + H, x0:x0 + W] * VIG + embers(t, 0.45), 0, 1)

# ---------- scene elements ----------
class C:                                              # photo / cover card
    def __init__(s, name, cx, cy, w, t0=None, rim=(255, 255, 255), gray_at=None, zoom=None, out=None):
        s.name, s.cx, s.cy, s.w, s.t0, s.rim, s.gray_at, s.zoom, s.out = name, cx, cy, w, t0, rim, gray_at, zoom, out
class X:                                              # neon keyword ('pop'), typewriter ('type') or dark box ('box')
    def __init__(s, t0, text, cx, cy, size=90, col=WHT, mode="pop", out=None):
        s.t0, s.text, s.cx, s.cy, s.size, s.col, s.mode, s.out = t0, text, cx, cy, size, col, mode, out
class Nn:                                             # counter
    def __init__(s, t0, t1, value, cx, cy, size=150, col=YEL, suffix="", out=None):
        s.t0, s.t1, s.value, s.cx, s.cy, s.size, s.col, s.suffix, s.out = t0, t1, value, cx, cy, size, col, suffix, out
class E:                                              # emoji
    def __init__(s, t0, ch, cx, cy, size=140, out=None): s.t0, s.ch, s.cx, s.cy, s.size, s.out = t0, ch, cx, cy, size, out
class P:                                              # 3D png from his library, floating
    def __init__(s, t0, rel, cx, cy, w=260, out=None): s.t0, s.rel, s.cx, s.cy, s.w, s.out = t0, rel, cx, cy, w, out
class S:                                              # red stamp
    def __init__(s, t0, text, cx, cy, size=110): s.t0, s.text, s.cx, s.cy, s.size = t0, text, cx, cy, size
class V:                                              # video clip: glowing card, or full-screen background ('bg')
    def __init__(s, clip, t0, cx, cy, w, ss=0.0, out=None, mode="card", credit=None, gain=0.12):
        s.clip, s.t0, s.cx, s.cy, s.w, s.ss, s.out, s.mode, s.credit, s.gain = clip, t0, cx, cy, w, ss, out, mode, credit, gain
_vp, _vglow = {}, {}
def vframe(v, k):
    st = _vp.get(id(v)); want = int(round(k * FPS)); h = (int(v.w * 9 / 16) // 2) * 2 if v.mode == "card" else H
    if st is None or st["n"] != want:
        if st: st["p"].kill(); st["p"].wait()
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{v.ss + want / FPS:.3f}", "-i", os.path.join(CLIPS, v.clip), "-an",
                              "-vf", f"scale={v.w}:{h}", "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
        st = _vp[id(v)] = {"p": p, "n": want, "last": st["last"] if st else None, "h": h}
    buf = st["p"].stdout.read(v.w * h * 3); st["n"] += 1
    if len(buf) == v.w * h * 3: st["last"] = np.frombuffer(buf, np.uint8).reshape(h, v.w, 3).astype(np.float32) / 255
    return st["last"]
def draw_video(img, v, k, fade):
    fr = vframe(v, k)
    if fr is None: return
    if v.mode == "bg":
        a = min(k / 0.3, 1) * fade; img[:] = img * (1 - a) + fr * 0.42 * a
    else:
        h, w = fr.shape[:2]
        if (w, h) not in _vglow: _vglow[(w, h)] = glow_rgba(np.dstack([np.zeros((h, w, 3), np.float32), np.ones((h, w), np.float32)]), (255, 255, 255), 22, 1.0)
        sc, a = settle(min(k, 2.0)), min(k / 0.15, 1) * fade
        paste(img, _vglow[(w, h)], v.cx, v.cy, sc, a)
        paste(img, np.dstack([fr[..., ::-1], np.ones((h, w), np.float32)]), v.cx, v.cy, sc, a)
        x0, y0, x1, y1 = int(v.cx - w * sc / 2), int(v.cy - h * sc / 2), int(v.cx + w * sc / 2), int(v.cy + h * sc / 2)
        if a > 0.5: cv2.rectangle(img, (x0, y0), (x1, y1), (1.0, 1.0, 1.0), 5)
    if v.credit:
        cb = kbox(v.credit, 24); paste(img, cb, 40 + cb.shape[1] / 2, H - 40, 1.0, 0.85 * fade * min(k / 0.3, 1))
class B:                                              # animated bar duel (e.g. Grammy nominations)
    def __init__(s, t0, items, cx, cy, w, h): s.t0, s.items, s.cx, s.cy, s.w, s.h = t0, items, cx, cy, w, h
def draw_bars(img, el, k):
    n = len(el.items); rowh = el.h / n; vmax = max(v for _, v, _, _ in el.items); x0 = int(el.cx - el.w / 2 + 330)
    for i, (lab, v, col, pic) in enumerate(el.items):
        ki = k - i * 0.35
        if ki < 0: continue
        y = int(el.cy - el.h / 2 + rowh * (i + 0.5)); u = 1 - (1 - min(ki / 0.9, 1)) ** 3
        paste(img, card(pic, 120, col), el.cx - el.w / 2 + 80, y, popk(ki), min(ki / 0.1, 1))
        im, _ = neon(lab, 40, WHT); paste(img, im, x0 + im.shape[1] / 2 - 30, y - 52, 1.0, min(ki / 0.1, 1))
        L = int((el.w - 520) * v / vmax * u); c = tuple(float(x) / 255 for x in col[::-1])
        if L > 2:
            glow = np.zeros_like(img); cv2.rectangle(glow, (x0, y - 18), (x0 + L, y + 30), c, -1)
            img[:] = np.clip(img + cv2.GaussianBlur(glow, (0, 0), 14) * 0.8, 0, 1); cv2.rectangle(img, (x0, y - 18), (x0 + L, y + 30), c, -1)
        num, _ = neon(str(int(round(v * u))), 76, col); paste(img, num, x0 + L + 80, y + 6, popk(ki - 0.9) if ki > 0.9 else 1.0)
class K:                                              # red cross over a rectangle
    def __init__(s, t0, x0, y0, x1, y1): s.t0, s.r = t0, (x0, y0, x1, y1)

def draw_el(img, el, t, ts):
    t0 = ts if getattr(el, "t0", None) is None else R(el.t0)
    k = t - t0
    if k < 0: return
    out = getattr(el, "out", None)
    fade = 1.0 if out is None else float(np.clip((R(out) - t) / 0.2, 0, 1))
    if fade <= 0: return
    if isinstance(el, C):
        gray = el.gray_at is not None and t >= R(el.gray_at)
        im = card(el.name, el.w, el.rim, gray); sc = settle(k); cx, cy = el.cx, el.cy
        if el.zoom:
            za, zb, s1, dx, dy = el.zoom; u = float(np.clip((t - R(za)) / max(R(zb) - R(za), 0.01), 0, 1)); u = u * u * (3 - 2 * u)
            sc *= 1 + (s1 - 1) * u; cx += dx * u; cy += dy * u
        paste(img, im, cx, cy, sc, min(k / 0.15, 1) * fade)
    elif isinstance(el, X):
        if el.mode == "box":
            im = kbox(el.text, el.size); dx = (1 - min(k / 0.18, 1)) ** 2 * -60
            paste(img, im, el.cx + dx, el.cy, 1.0, min(k / 0.12, 1) * fade)
        elif el.mode == "type":
            n = min(len(el.text), int(k * 18) + 1); full, pad = neon(el.text, el.size, el.col); im, _ = neon(el.text[:n], el.size, el.col)
            left = el.cx - full.shape[1] / 2; paste(img, im, left + im.shape[1] / 2, el.cy, 1.0, fade)
            if n < len(el.text) or (k * 2.2) % 1 < 0.6:
                x = int(left + im.shape[1] - pad + 8); hh = int(el.size * 0.42)
                img[max(int(el.cy - hh), 0):int(el.cy + hh), x:x + 8] = 1.0 * fade + img[max(int(el.cy - hh), 0):int(el.cy + hh), x:x + 8] * (1 - fade)
        else:
            im, _ = neon(el.text, el.size, el.col); paste(img, im, el.cx, el.cy, popk(k), min(k / 0.08, 1) * fade)
    elif isinstance(el, Nn):
        u = min(k / max(R(el.t1) - t0, 0.05), 1); v = int(el.value * (1 - (1 - u) ** 3))
        im, _ = neon(f"{v:,}".replace(",", " ") + el.suffix, el.size, el.col)
        paste(img, im, el.cx, el.cy, popk(k - (R(el.t1) - t0)) if u >= 1 else 1.0, min(k / 0.08, 1) * fade)
    elif isinstance(el, E):
        paste(img, emoji(el.ch, el.size), el.cx, el.cy + 6 * np.sin(t * 2.5 + el.cx), popk(k), min(k / 0.08, 1) * fade)
    elif isinstance(el, P):
        paste(img, png(el.rel, el.w), el.cx, el.cy + 10 * np.sin(t * 2 + el.cy), popk(k) * (1 + 0.02 * np.sin(t * 1.7)), min(k / 0.1, 1) * fade)
    elif isinstance(el, S):
        sc = 1.0 + 1.6 * max(0.0, 1 - k / 0.14) ** 2; paste(img, stamp(el.text, el.size), el.cx, el.cy, sc, min(k / 0.06, 1))
    elif isinstance(el, V): draw_video(img, el, k, fade)
    elif isinstance(el, B): draw_bars(img, el, k)
    elif isinstance(el, K):
        x0, y0, x1, y1 = el.r; u = min(k / 0.25, 1)
        cv2.line(img, (x0, y0), (int(x0 + (x1 - x0) * u), int(y0 + (y1 - y0) * u)), (0.15, 0.1, 0.95), 18, cv2.LINE_AA)
        if k > 0.15:
            u2 = min((k - 0.15) / 0.25, 1); cv2.line(img, (x1, y0), (int(x1 - (x1 - x0) * u2), int(y0 + (y1 - y0) * u2)), (0.15, 0.1, 0.95), 18, cv2.LINE_AA)

# ---------- the video, scene by scene (source seconds; T('word', after) = when he says it) ----------
CL, CR = 600, 1350                                    # card column / text column (two-column layout)
NG, CI, GH, ZA, GB, FR, CO, US = "🇳🇬", "🇨🇮", "🇬🇭", "🇿🇦", "🇬🇧", "🇫🇷", "🇨🇴", "🇺🇸"
SCENES = [
    # --- intro ---
    (0.0, 10.65, "burna-grammy-2021.jpg", [C("burna-grammy-2021.jpg", CL, 540, 480),
        Nn(0.32, 1.4, 14, CR, 280, 140, GOLD, " NOMINATIONS"), X(1.6, "AUX GRAMMY AWARDS", CR, 400, 56, WHT, "box"),
        X(4.8, "AUCUN NIGÉRIAN N'A FAIT MIEUX", CR, 510, 50, WHT), X(6.8, "ET POURTANT…", CR, 630, 70, WHT),
        X(T("seule"), "1 SEULE VICTOIRE", CR, 760, 100, RED), X(9.2, "EN 2021", CR, 890, 60, YEL, "box"), P(6.8, "3d/grammy.png", CL + 300, 800, 170)]),
    (10.65, 16.85, "grid", [X(14.5, "LE 7 FÉVRIER, IL RETENTE SA CHANCE", 960, 540, 64, YEL)]),
    # --- 1. qui est Burna Boy ---
    (16.85, 24.80, "burna-grammy-2021.jpg", [C("burna-grammy-2021.jpg", CL, 540, 460),
        X(17.0, "DAMINI EBUNOLUWA OGULU", CR, 300, 60, WHT), X(20.5, "NÉ LE 2 JUILLET 1991", CR, 440, 66, YEL),
        X(22.5, "PORT HARCOURT", CR, 570, 80, WHT, "box"), E(24.0, "🇳🇬", CR, 700, 110)]),
    (24.80, 39.10, "benson-idonije-85-ans.jpg", [C("benson-idonije-85-ans.jpg", CL, 540, 760, 27.7, out=31.4), C("fela-kuti.jpg", CL, 540, 470, 31.4),
        X(24.9, "UNE HISTOIRE DE FAMILLE", CR, 220, 66, YEL), X(27.8, "SON GRAND-PÈRE : BENSON IDONIJE", CR, 370, 44, WHT, "box"),
        X(31.4, "1ER MANAGER DE FELA KUTI", CR, 510, 60, GOLD), X(33.8, "L'INVENTEUR DE L'AFROBEAT", CR, 630, 54, WHT),
        X(36.0, "BURNA L'A CONFIRMÉ À LA TÉLÉ", CR, 770, 44, WHT, "box")]),
    (39.10, 47.30, "benson-idonije-85-ans.jpg", [C("benson-idonije-85-ans.jpg", CL, 540, 760, out=43.7), C("burna-et-bose-ogulu.jpg", CL, 540, 820, 43.8),
        X(39.2, "EN JUIN DERNIER", CR, 250, 56, WHT, "box"), X(40.5, "LES 90 ANS DU GRAND-PÈRE", CR, 370, 54, YEL), X(41.6, "À LAGOS", CR, 470, 60, WHT),
        X(43.8, "SA MÈRE BOSE OGULU", CR, 630, 62, GOLD), X(45.3, "DEVIENT SA MANAGEUSE", CR, 740, 54, WHT, "box")]),
    # --- 2. l'ascension ---
    (47.30, 56.50, "african-giant.jpg", [X(47.4, "2017", 960, 130, 110, YEL), C("atlantic-records.jpg", 960, 430, 420, 48.3, rim=(255, 220, 40)),
        X(48.6, "SIGNÉ CHEZ ATLANTIC RECORDS", 960, 720, 76, WHT), E(50.0, "🇺🇸", 1560, 430, 110),
        X(52.0, "2019 : UN TITRE QUI ANNONCE SES AMBITIONS", 960, 870, 54, WHT, "box")]),
    (56.50, 69.70, "african-giant.jpg", [C("african-giant.jpg", CL, 540, 560),
        X(56.6, "AFRICAN GIANT", CR, 250, 110, GOLD, "type"), X(58.5, "1RE NOMINATION AUX GRAMMYS", CR, 410, 56, WHT),
        X(62.0, "2020 · MEILLEUR ALBUM DE MUSIQUE DU MONDE", CR, 510, 36, WHT, "box"),
        X(66.2, "IL PERD…", CR, 670, 96, RED), X(67.8, "MAIS IL NE LÂCHE RIEN", CR, 800, 62, YEL)]),
    # --- 3. la victoire ---
    (69.70, 89.40, "twice-as-tall.jpg", [C("twice-as-tall.jpg", CL, 540, 560, out=76.9), C("burna-grammy-2021.jpg", CL, 540, 470, 76.9, out=79.4),
        V("burna-boy-grammy-2021-victoire-16x9.mp4", 79.4, CL, 540, 820, ss=0.8, gain=0.12, credit="SOURCE : GRAMMYS / RECORDING ACADEMY"),
        X(69.8, "AOÛT 2020", CR, 210, 66, YEL), X(71.5, "TWICE AS TALL", CR, 340, 96, WHT, "type"),
        X(74.98, "« DEUX FOIS PLUS GRAND »", CR, 460, 48, WHT, "box"), X(76.98, "2021 : C'EST LA BONNE", CR, 590, 74, GOLD),
        X(79.4, "1ER GRAMMY", CR, 720, 110, YEL), P(79.4, "3d/lightning-gold.png", CR + 420, 700, 170),
        X(84.3, "1ER GAGNANT DE LA CATÉGORIE SOUS SON NOUVEAU NOM", CR, 860, 32, WHT, "box")]),
    (89.40, 96.30, "grid", [X(89.5, "TOUT LE MONDE SE DIT :", 960, 300, 70, WHT), X(90.5, "CE N'EST QUE LE DÉBUT", 960, 440, 104, GOLD),
        X(93.5, "SAUF QUE…", 960, 690, 140, RED)]),
    # --- 4. 11 défaites ---
    (96.30, 109.00, "justice-bieber.jpg", [X(96.4, "2022 · 2 NOMINATIONS", 960, 100, 80, YEL),
        C("burna-angelique-kidjo.jpg", 540, 500, 700, 98.6), X(98.6, "« DO YOURSELF » AVEC ANGÉLIQUE KIDJO", 540, 830, 38, WHT, "box"),
        C("justice-bieber.jpg", 1400, 480, 400, T("justice", 100)), X(T("justice", 100), "« LOVED BY YOU » · JUSTICE", 1400, 760, 38, WHT, "box"),
        X(106.4, "ALBUM DE L'ANNÉE", 1400, 850, 46, GOLD), X(107.9, "0 VICTOIRE", 960, 975, 84, RED)]),
    (109.00, 114.55, "love-damini.jpg", [X(109.1, "2023", 960, 100, 90, YEL),
        C("last-last.jpg", 600, 500, 420, 109.6), X(109.6, "« LAST LAST »", 600, 790, 50, WHT, "box"),
        C("love-damini.jpg", 1320, 500, 420, T("love", 110)), X(T("love", 110), "LOVE, DAMINI", 1320, 790, 50, WHT, "box"),
        X(113.71, "0 VICTOIRE", 960, 950, 96, RED)]),
    (114.55, 130.70, "i-told-them.jpg", [X(114.6, "2024 · SA PLUS GROSSE ANNÉE", 960, 90, 66, YEL),
        C("i-told-them.jpg", CL - 40, 560, 480), Nn(116.5, 118.0, 4, CR, 210, 110, GOLD, " NOMINATIONS"),
        V("burna-boy-grammys-2024-brandy-16x9.mp4", 119.9, CR, 560, 740, ss=2.0, gain=0.15, credit="SOURCE : GRAMMYS / RECORDING ACADEMY"),
        X(120.5, "SUR SCÈNE AVEC BRANDY & 21 SAVAGE", CR, 820, 42, WHT, "box"), X(122.5, "4 FÉVRIER 2024", CR, 900, 56, YEL),
        X(126.0, "IL REPART SANS RIEN", 960, 1000, 66, RED)]),
    (130.70, 139.50, "grid", [X(130.8, "2025", 960, 120, 90, YEL), X(131.2, "MEILLEURE PERFORMANCE DE MUSIQUE AFRICAINE", 960, 240, 42, WHT, "box"),
        C("higher.jpg", 560, 560, 380, 131.2), X(131.6, "« HIGHER »", 560, 820, 50, WHT, "box"),
        C("tems.jpg", 1360, 560, 320, T("thames")), X(T("thames"), "C'EST TEMS QUI GAGNE", 1360, 850, 60, GOLD),
        X(T("love", 137), "« LOVE ME JEJE »", 1360, 950, 46, WHT, "box")]),
    (139.50, 151.40, "no-sign-of-weakness.jpg", [X(139.6, "2026 · 2 NOMINATIONS", 960, 90, 70, YEL),
        C("no-sign-of-weakness.jpg", CL, 560, 480), X(140.6, "« LOVE »", CR, 240, 60, WHT, "box"),
        X(141.8, "NO SIGN OF WEAKNESS", CR, 350, 62, WHT, "type"),
        C("youssou-ndour.jpg", CR, 610, 240, 144.7), X(145.3, "FACE À YOUSSOU N'DOUR", CR, 850, 46, WHT, "box"), X(149.0, "ENCORE PERDU", CR, 950, 66, RED)]),
    (151.40, 158.30, "grid", [X(151.42, "LE BILAN DEPUIS 2021", 960, 190, 90, YEL),
        Nn(152.5, 153.8, 11, 960, 450, 150, WHT, " NOMINATIONS"), Nn(154.0, 155.3, 11, 960, 650, 150, RED, " DÉFAITES"),
        X(156.7, "COMMENT L'EXPLIQUER ?", 960, 880, 80, GOLD)]),
    # --- 5. 3 raisons ---
    (158.30, 173.40, "grid", [X(159.58, "1. LA CONCURRENCE A EXPLOSÉ", 960, 110, 72, YEL),
        X(161.82, "EN 2021, L'AFROBEATS ÉTAIT UNE NICHE AUX GRAMMYS", 960, 220, 42, WHT, "box"),
        C("tems.jpg", 260, 520, 290, T("thames", 165)), C("wizkid.jpg", 620, 520, 340, T("whisked")), C("davido.jpg", 980, 520, 340, T("davido", 165)),
        C("asake.jpg", 1340, 520, 290, T("asake", 165)), C("ayra-starr.jpg", 1700, 520, 300, T("airastar")),
        X(T("thames", 165), "TEMS", 260, 760, 42, WHT), X(T("whisked"), "WIZKID", 620, 760, 42, WHT), X(T("davido", 165), "DAVIDO", 980, 760, 42, WHT),
        X(T("asake", 165), "ASAKE", 1340, 760, 42, WHT), X(T("airastar"), "AYRA STARR", 1700, 760, 42, WHT),
        X(171.5, "LE NIGERIA SE BAT CONTRE LUI-MÊME", 960, 920, 60, RED)]),
    (173.40, 182.90, "grid", [X(173.5, "2. EN FACE : DES LÉGENDES", 960, 120, 76, YEL),
        C("burna-angelique-kidjo.jpg", 600, 520, 640, 175.7), C("youssou-ndour.jpg", 1360, 520, 330, 177.3),
        X(175.7, "ANGÉLIQUE KIDJO", 600, 840, 50, WHT, "box"), X(177.3, "YOUSSOU N'DOUR", 1360, 840, 50, WHT, "box"),
        X(179.5, "RESPECTÉS DEPUIS DES DÉCENNIES", 960, 970, 54, GOLD)]),
    (182.90, 196.00, "i-told-them.jpg", [V("burna-boy-i-told-them-tour-16x9.mp4", None, 960, 540, 1920, ss=3.0, mode="bg", gain=0.12),X(183.0, "3. SA MUSIQUE A CHANGÉ", 960, 110, 76, YEL),
        C("i-told-them.jpg", 600, 500, 420, 184.8), X(184.8, "PLUS HIP-HOP, MOINS AFROBEATS", 600, 790, 40, WHT, "box"),
        C("no-sign-of-weakness.jpg", 1320, 500, 420, 189.47), X(191.3, "SOLIDE, MAIS PEU DE RISQUES", 1320, 790, 40, WHT, "box")]),
    # --- 6. Dai Dai ---
    (196.00, 211.20, "dai-dai.jpg", [C("dai-dai.jpg", CL, 540, 580, out=204.9),
        V("burna-boy-nfl-paris-16x9.mp4", 204.9, CL, 540, 820, ss=0.0, gain=0.12),
        X(196.1, "14E NOMINATION", CR, 220, 92, GOLD), X(197.4, "16 NOVEMBRE", CR, 340, 58, WHT, "box"),
        X(T("day", 199), "« DAI DAI » · SHAKIRA", CR, 470, 64, YEL), X(201.5, "L'HYMNE DE LA COUPE DU MONDE 2026", CR, 580, 40, WHT),
        X(204.9, "N°1 EN FRANCE TOUT L'ÉTÉ", CR, 720, 56, WHT, "box"), E(205.2, "🇫🇷", CR, 820, 80), X(208.5, "MAIS REGARDEZ…", CR, 940, 66, RED)]),
    (211.20, 220.30, "burna-angelique-kidjo.jpg", [C("burna-angelique-kidjo.jpg", 960, 520, 1060),
        X(211.3, "ANGÉLIQUE KIDJO", 960, 90, 80, YEL), X(213.5, "NOMMÉS ENSEMBLE EN 2022", 960, 970, 56, WHT, "box", out=217.2),
        X(217.29, "4 ANS PLUS TARD : DE PARTENAIRES À RIVAUX", 960, 970, 48, RED, "box"), S(217.29, "RIVAUX", 960, 520, 140)]),
    # --- 7. le bilan ---
    (220.30, 230.00, "grid", [X(220.4, "LE 1ER À AVOIR 5 NOMINATIONS EN CATÉGORIE ALBUM", 960, 110, 42, WHT, "box"),
        X(222.0, "NOMINATIONS AUX GRAMMYS", 960, 220, 62, YEL),
        B(223.5, [("BURNA BOY", 14, GOLD, "burna-grammy-2021.jpg"), ("TEMS", 12, WHT, "tems.jpg"), ("WIZKID", 7, WHT, "wizkid.jpg")], 960, 620, 1560, 600)]),
    (230.00, 249.60, "burna-grammy-2021.jpg", [C("burna-grammy-2021.jpg", CL, 540, 470),
        X(230.01, "14 NOMINATIONS :", CR, 200, 70, WHT), X(231.3, "PAS UN ÉCHEC", CR, 310, 84, GOLD),
        X(232.65, "UNE PREUVE DE RÉGULARITÉ", CR, 430, 52, WHT, "box"), X(238.0, "MAIS POUR L'« AFRICAN GIANT »", CR, 570, 46, WHT),
        X(239.3, "1 SEUL TROPHÉE", CR, 680, 86, RED), P(239.3, "3d/grammy.png", CR + 420, 680, 150), X(241.55, "7 FÉVRIER : SA MEILLEURE CHANCE", CR, 810, 46, YEL, "box"),
        P(241.55, "3d/lightning-gold.png", CR + 400, 790, 150), X(246.3, "VA-T-IL ENFIN GAGNER ?", CR, 940, 60, GOLD)]),
    # --- question ---
    (249.60, 259.10, "grid", [X(249.7, "DONNEZ VOTRE AVIS EN COMMENTAIRE", 960, 230, 76, YEL), E(250.5, "💬", 960, 390, 120),
        X(252.5, "ABONNEZ-VOUS À MA 2E CHAÎNE", 960, 570, 60, WHT), X(254.0, "LE BIG VASS WORLD", 960, 710, 110, GOLD, "type"),
        X(257.46, "LE LIEN EST JUSTE ICI", 960, 870, 56, WHT, "box")]),
    (259.10, END + 1, "end", []),
]
CHAPTERS = [  # (source time, top, bottom) — 3D title over the first seconds of each chapter; YouTube chapters list
    (0.0, "INTRO", ""), (16.85, "CHAPITRE 1", "QUI EST BURNA BOY"), (47.30, "CHAPITRE 2", "L'ASCENSION"), (69.70, "CHAPITRE 3", "LA VICTOIRE"),
    (96.30, "CHAPITRE 4", "11 DÉFAITES"), (158.30, "CHAPITRE 5", "3 RAISONS"), (196.00, "CHAPITRE 6", "DAI DAI"),
    (220.30, "CHAPITRE 7", "LE BILAN"), (249.60, "ET VOUS ?", "")]
HOOK = (R(10.72), R(14.4))
hook_img = block("11 NOMINATIONS", "11 DÉFAITES", 1400, 700)
chap_img = {c[0]: block(c[1], c[2], 1300, 520) for c in CHAPTERS if c[2]}
CHAP_SHOW = 1.7
SC = [(R(a), R(b), bgs, els) for a, b, bgs, els in SCENES]
logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 130)
END_LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 520)
end_img = block("LE BIG", "VASS", 900, 420)

def chapter_at(t):
    cur = CHAPTERS[0]
    for c in CHAPTERS:
        if R(c[0]) <= t: cur = c
    return cur

# ---------- render ----------
burn = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions/burn-transition-12.mp4"), "-vf", f"scale={W}:{H}",
                       "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
BURN = np.frombuffer(burn, np.uint8).reshape(-1, H, W, 3); BURN_PEAK = 11 / FPS
BURN_AT = [R(c[0]) for c in CHAPTERS[1:]] + [SC[-1][0]]
f0, f1 = 0, N
SNAP = os.environ.get("SNAP")                         # "src_t1,src_t2,..." writes one PNG per source time, then exits
frames = range(f0, f1)
if SNAP: frames = [int((float(x[1:]) if x[0] == "o" else R(float(x))) * FPS) for x in SNAP.split(",")]
if PREVIEW: a_, b_ = map(float, PREVIEW.split("-")); f0, f1 = int(a_ * FPS), min(int(b_ * FPS), N)
VIDEO_ONLY = f"{WORK}/video_only.mp4" if not PREVIEW else OUT
SKIP_VIDEO = os.environ.get("SKIP_VIDEO")             # reuse WORK/video_only.mp4, redo only the sound
enc = None if SNAP or SKIP_VIDEO else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", "noise=alls=3:allf=t+u,format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "19", VIDEO_ONLY], stdin=subprocess.PIPE)
lab_cache = {}; _vins = {}
for i in ([] if SKIP_VIDEO else frames if SNAP else range(f0, f1)):
    t = i / FPS
    si = max(j for j, s in enumerate(SC) if s[0] <= t) if t >= SC[0][0] else 0
    ts, te, bgs, els = SC[si]; k = t - ts
    ins = next((x for x in INS_OUT if x[0] <= t < x[0] + x[1]), None)
    if ins:
        o0, d, clip, ss, at = ins; kk = t - o0; k = kk; bgi, label, cred, quotes = INS_LOOK[at]
        img = background(bgi, t, kk)
        if ins not in _vins: _vins[ins] = V(clip, None, 960, 495, 1220, ss=ss, credit=cred)
        draw_video(img, _vins[ins], kk, float(np.clip((d - kk) / 0.2, 0, 1)))
        lb = kbox(label, 44); paste(img, lb, W / 2, 75, popk(kk), min(kk / 0.1, 1))
        for q0, q1, q in quotes:
            if q0 <= kk < q1: im, _ = neon(q, 48, YEL); paste(img, im, W / 2, 935, popk(kk - q0), min((kk - q0) / 0.08, 1) * min((q1 - kk) / 0.15, 1))
    elif bgs == "end":
        img = background("grid", t, k) * 0.8
        paste(img, END_LOGO, W / 2, 380, 0.85 + 0.15 * min(k / 0.3, 1))
        paste(img, end_img, W / 2, 800, 0.6 + 0.4 * min(k / 0.15, 1))
        im, _ = neon("ABONNE-TOI", 70, YEL); paste(img, im, W / 2, 1010, popk(k - 0.6), min(max(k - 0.6, 0) / 0.1, 1))
    else:
        img = background(bgs, t, k)
        for el in els: draw_el(img, el, t, ts)
        if HOOK[0] <= t < HOOK[1]:
            kk = t - HOOK[0]; img *= 0.55
            paste(img, hook_img, W / 2, 560, 0.55 + 0.55 * min(kk / 0.12, 1) - 0.1 * min(max(kk - 0.12, 0) / 0.1, 1))
        c = chapter_at(t); kc = t - R(c[0])
        if c[2] and kc < CHAP_SHOW:                   # 3D chapter title over the opening of the chapter
            img *= 0.35 + 0.65 * min(max(kc - (CHAP_SHOW - 0.25), 0) / 0.25, 1)
            a = 1 - min(max(kc - (CHAP_SHOW - 0.2), 0) / 0.2, 1)
            paste(img, chap_img[c[0]], W / 2, H / 2, 0.55 + 0.55 * min(kc / 0.12, 1) - 0.1 * min(max(kc - 0.12, 0) / 0.1, 1), a)
        if c[2]:                                      # chapter label, top right
            if c[2] not in lab_cache: lab_cache[c[2]] = kbox(c[2], 30)
            lb = lab_cache[c[2]]; paste(img, lb, W - 40 - lb.shape[1] / 2, 60, 1.0, 0.9)
        lv = lvl[min(i, N - 1)]                       # presenter: his logo pulses with his voice
        cv2.circle(img, (95, 95), int(70 + 10 * lv), (0.25, 0.75, 1.0), 4, cv2.LINE_AA)
        paste(img, logo, 95, 95, 1.0 + 0.06 * lv)
    if k < 0.08 and si > 0: img = np.clip(img + (0.08 - k) / 0.08 * 0.55, 0, 1)      # white flash on every cut
    for o0, d, *_ in INS_OUT:
        if 0 <= t - (o0 + d) < 0.08: img = np.clip(img + (0.08 - (t - o0 - d)) / 0.08 * 0.55, 0, 1)
    for b_ in BURN_AT:
        kb = int(round((t - (b_ - BURN_PEAK)) * FPS))
        if 0 <= kb < len(BURN): img = 1 - (1 - img) * (1 - BURN[kb].astype(np.float32) / 255)
    if SNAP: cv2.imwrite(f"{WORK}/snap_{i:05d}.jpg", (np.clip(img, 0, 1) * 255).astype(np.uint8)); continue
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if i % 600 == 0: print(f"frame {i}/{N}", flush=True)
if SNAP: sys.exit()
if enc: enc.stdin.close(); enc.wait()
if PREVIEW: print("preview done", OUT); sys.exit()

# ---------- sound ----------
def load(p): return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]), np.float32)
sfx = np.zeros(int(DUR * SR) + SR, np.float32)
def place(snd, t, g):
    i0 = int(t * SR)
    if i0 < 0: snd, i0 = snd[-i0:], 0
    n = min(len(snd), len(sfx) - i0)
    if n > 0: sfx[i0:i0 + n] += snd[:n] * g
L = lambda p: load(os.path.join(LIB, p))
whooshes = [(L("sfx/whoosh-1.mp3"), 0.42), (L("sfx/whoosh-2.mp3"), 0.13), (L("sfx/whoosh-3.mp3"), 0.26), (L("sfx/whoosh-4.mp3"), 0.08)]
shutter, click, hit = L("sfx/camera-shutter-short.mp3"), L("sfx/synth-click.wav"), L("sfx/synth-hit.wav")
riser, ding, money, sparkle = L("sfx/riser-metallic-transition.mp3"), L("sfx/cash-ding.mp3"), L("sfx/money-counter.mp3"), L("sfx/sparkle.mp3")
uhh, burn_a, crowd = L("sfx/uhh.mp3"), L("transitions/burn-transition-12.mp4"), L("sfx/goal-crowd.mp3")
for n, (a, b, bgs, els) in enumerate(SC[1:]):
    w, pk = whooshes[n % 4]; place(w, a - pk, 0.28)
for a, b, bgs, els in SC:
    for el in els:
        t0 = a if getattr(el, "t0", None) is None else R(el.t0)
        if isinstance(el, C) and t0 > a + 0.05: place(shutter, t0 - 0.2, 0.45)
        elif isinstance(el, X) and el.mode == "type":
            for j, ch in enumerate(el.text):
                if ch != " " and j < 30: place(click, t0 + j / 18, 0.2)
        elif isinstance(el, Nn):
            d = R(el.t1) - t0; seg = money[int(0.6 * SR):int(0.6 * SR) + int(max(d, 0.3) * SR)].copy()
            seg[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR)); place(seg, t0, 0.5); place(ding, R(el.t1) - 0.4, 0.45)
        elif isinstance(el, S) or isinstance(el, K): place(hit, t0, 0.4)
        elif isinstance(el, P) and "gold" in el.rel: place(sparkle[int(4.2 * SR):int(5.4 * SR)], t0 - 0.1, 0.3)
        elif isinstance(el, (E, P)): place(hit, t0, 0.12)
def clip_audio(clip, ss, d):
    a = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{d:.3f}", "-i", os.path.join(CLIPS, clip),
        "-af", "loudnorm=I=-16:TP=-2", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]), np.float32).copy()
    f = min(int(0.25 * SR), len(a) // 4)
    if f: a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
    return a
for a, b, bgs, els in SC:
    for el in els:
        if isinstance(el, V):
            t0 = a if el.t0 is None else R(el.t0); t1 = b if el.out is None else R(el.out)
            place(clip_audio(el.clip, el.ss, t1 - t0), t0, el.gain)
for o0, d, clip, ss, _at in INS_OUT:
    place(clip_audio(clip, ss, d), o0, 1.0); place(whooshes[0][0], o0 - whooshes[0][1], 0.25)
for c in CHAPTERS:
    if c[2]: place(hit, R(c[0]), 0.45)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.45)
place(hit, HOOK[0], 0.5); place(riser, HOOK[0] - 2.95, 0.4); place(riser, R(196.0) - 2.95, 0.45)   # 14th nomination
place(crowd, R(79.4), 0.3); place(uhh, R(107.9) + 0.2, 0.2); place(uhh, R(113.71) + 0.2, 0.2)    # 1st Grammy; « 0 victoire »
for i in range(3): place(hit, R(223.5) + i * 0.35, 0.25)
sf.write(f"{WORK}/sfx.wav", sfx[:int(DUR * SR)], SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/voice_ins.wav", "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]highpass=f=70,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2dB,loudnorm=I=-14:TP=-1.5:LRA=7,"
    "aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.75:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
with open(os.path.splitext(OUT)[0] + "_chapitres.txt", "w") as f:
    for c in CHAPTERS:
        s = int(R(c[0])); f.write(f"{s // 60}:{s % 60:02d} {(c[2] or c[1]).capitalize()}\n")
print("done", OUT, flush=True)
