"""YouTube 16:9 video from a voice-over, no face-cam (« Kiff No Beat : comment le groupe a disparu pendant 7 ans »).
Style taken from the explainer he asked to study: photos and covers shown as glowing CARDS over a blurred copy of
themselves, keywords only on screen (no full subtitles), counters on numbers, 3D chapter titles, white flash on cuts,
his burn transition on chapter changes, logo pulsing with his voice, end card. Gentle silence cut for long-form.
usage: yt_kiff_no_beat.py WORK OUT.mp4    (WORK holds src.mp3, words.json and img/*.jpg)"""
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
keep[int(433.3 / 0.02):] = True                       # sign-off kept whole
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
INS = []
INS_LOOK = {}
def R(t): return R0(t) + sum(d for at, d, *_ in INS if t >= at)
INS_OUT = [(R0(at) + sum(d2 for at2, d2, *_ in INS if at2 < at), d, clip, ss, at) for at, d, clip, ss in INS]
DUR = sum(b - a for a, b in segs) + sum(x[1] for x in INS); N = int(DUR * FPS)
if os.environ.get("EXPORT_WORDS"):                     # words with their time in the finished video (for Shorts captions)
    out = [{"w": w["w"], "s": R(w["s"]), "e": R(w["e"]), "src": w["s"]} for w in words if any(a <= w["s"] < b for a, b in segs)]
    json.dump({"words": out, "ins": INS_OUT}, open(os.environ["EXPORT_WORDS"], "w"), ensure_ascii=False); sys.exit()
print(f"{len(segs)} segments, {DUR:.1f}s (from {END:.1f}s)", flush=True)
voice = sf.read(f"{WORK}/voice_cut.wav")[0]
# breath / room-noise gate (his recording was very quiet, so breaths came up with the loudness boost)
_h = int(0.01 * SR); _db = 20 * np.log10(np.array([np.sqrt(np.mean(voice[i:i + _h] ** 2)) for i in range(0, len(voice), _h)]) + 1e-9)
_db = np.convolve(_db, np.ones(5) / 5, mode="same"); _open = (_db > -40).astype(np.float32)
_open = np.convolve(_open, np.ones(13), mode="same") > 0                     # ~60 ms hold either side of speech
_g = np.where(_open, 1.0, 0.1).astype(np.float32); _g = np.convolve(_g, np.ones(3) / 3, mode="same")
voice = voice * np.repeat(_g, _h)[:len(voice)]
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
    (0.0, 12.60, "affiche-on-va-pas-dormir-2019.jpg", [C("affiche-on-va-pas-dormir-2019.jpg", CL, 540, 820),
        X(0.72, "10 AOÛT 2019", CR, 230, 90, YEL), X(2.2, "PALAIS DE LA CULTURE", CR, 360, 62, WHT), X(3.4, "TREICHVILLE", CR, 460, 50, WHT, "box"),
        X(4.4, "5 RAPPEURS · SALLE PLEINE", CR, 600, 56, GOLD), X(6.9, "LE PUBLIC CHANTE TOUT", CR, 720, 52, WHT),
        X(10.0, "ET APRÈS… PLUS RIEN", CR, 870, 72, RED)]),
    (12.60, 25.00, "kiff-no-beat.jpg", [C("kiff-no-beat.jpg", 960, 470, 900, out=19.0), C("affiche-kiff-no-beat-28-nov.jpg", 960, 500, 520, 19.0),
        X(15.16, "PAS DE SÉPARATION ANNONCÉE", 960, 930, 60, WHT, "box", out=19.0), X(17.08, "LE GROUPE S'EST ÉTEINT", 960, 1020, 60, RED, out=19.0),
        X(19.0, "ET SAMEDI, ILS REVIENNENT", 960, 90, 80, YEL), X(21.0, "COMMENT KIFF NO BEAT A DISPARU PENDANT 7 ANS", 960, 960, 44, WHT, "box")]),
    # --- 1. les débuts ---
    (25.00, 36.50, "kiff-no-beat.jpg", [V("kiff-no-beat-clip-16x9.mp4", None, CL, 540, 820, ss=10.0, gain=0.08, credit="SOURCE : TIKTOK @2X_RAMAZANNY"),
        X(25.0, "DEUX GROUPES RIVAUX", CR, 260, 70, WHT), X(28.0, "QUI FUSIONNENT", CR, 380, 70, YEL),
        X(30.5, "ILS ONT À PEINE 20 ANS", CR, 540, 54, WHT, "box"), X(33.0, "ILS VONT CHANGER LE RAP IVOIRE", CR, 680, 50, GOLD)]),
    (36.50, 53.70, "cadeau-de-noel.jpg", [C("cadeau-de-noel.jpg", CL, 540, 620, 47.0),
        X(36.6, "2010 : UN CONCOURS DE RAP TÉLÉVISÉ", CR, 200, 46, WHT, "box"), X(41.6, "ILS LE GAGNENT", CR, 320, 84, YEL),
        P(41.6, "3d/lightning-gold.png", CR + 420, 300, 150), X(42.9, "L'ARGENT DU PRIX ?", CR, 460, 56, WHT),
        X(44.2, "PAS DE CHAÎNES : UN PRODUCTEUR", CR, 560, 46, GOLD, "box"), X(49.5, "CADEAU DE NOËL", CR, 720, 84, RED, "type"),
        Nn(50.6, 51.6, 16, CR - 120, 860, 66, WHT, " TITRES"), X(52.0, "2011", CR + 220, 860, 66, YEL)]),
    (53.70, 69.40, "cadeau-de-noel.jpg", [C("cadeau-de-noel.jpg", CL, 540, 620),
        X(53.8, "UN TITRE QUI RAPPELLE", CR, 220, 56, WHT), X(55.5, "LA CRISE DE 2010", CR, 330, 76, RED),
        X(57.4, "LES IVOIRIENS PRIVÉS DE NOËL", CR, 450, 46, WHT, "box"), X(61.8, "LA VOIX DE SA GÉNÉRATION", CR, 590, 56, YEL),
        X(64.3, "RÉVÉLATION DE L'ANNÉE", CR, 730, 70, GOLD), P(64.3, "3d/lightning-gold.png", CR + 420, 720, 140)]),
    # --- 2. l'ascension ---
    (69.40, 86.70, "petards-d-ados.jpg", [V("kiff-no-beat-clip-d-fete-de-rue-16x9.mp4", None, 960, 540, 1920, ss=8.0, mode="bg", gain=0.1), X(69.5, "ENSUITE, PLUS RIEN NE LES ARRÊTE", 960, 100, 64, YEL),
        X(71.7, "2012 : UNE MIXTAPE DE 20+ TITRES", 520, 280, 46, WHT, "box"), X(74.5, "+ UNE TOURNÉE NATIONALE", 520, 370, 46, WHT),
        C("petards-d-ados.jpg", 1360, 450, 470, 77.6), X(77.6, "PÉTARDS D'ADOS · 2014", 1360, 760, 46, YEL, "box"),
        X(80.5, "CUBISME · 2015", 520, 560, 80, GOLD), X(83.1, "DES INVITÉS DE TAILLE", 520, 700, 54, WHT)]),
    (86.70, 101.00, "cassper-nyovest.jpg", [X(86.8, "SUR CUBISME", 960, 110, 70, YEL),
        C("cassper-nyovest.jpg", 600, 520, 420, 86.8), X(87.5, "CASSPER NYOVEST", 600, 800, 52, WHT, "box"), E(88.5, "🇿🇦", 600, 890, 70),
        C("burna-boy.jpg", 1320, 520, 360, 90.5), X(90.5, "BURNA BOY", 1320, 800, 52, WHT, "box"), E(91.0, "🇳🇬", 1320, 890, 70),
        X(93.9, "DIDI B : « UNE STRATÉGIE POUR CONQUÉRIR D'AUTRES PAYS »", 960, 1000, 40, GOLD)]),
    (101.00, 124.70, "grid", [V("kiff-no-beat-clip-b-quartier-16x9.mp4", None, 960, 540, 1920, ss=1.0, mode="bg", gain=0.1), X(101.0, "MONTRER LA MUSIQUE IVOIRIENNE AU MONDE", 960, 200, 58, WHT),
        X(104.6, "COMME LES PEINTRES CUBISTES", 960, 360, 66, YEL), X(106.5, "INSPIRÉS DE L'ART AFRICAIN", 960, 460, 52, WHT, "box"),
        X(108.5, "« LES CUBISTES 2.0 »", 960, 640, 110, GOLD), P(108.5, "3d/lightning-gold.png", 1500, 620, 160)]),
    (124.70, 136.80, "grid", [V("kiff-no-beat-clip-c-nuit-bleue-16x9.mp4", None, 960, 540, 1920, ss=18.0, mode="bg", gain=0.1), X(124.8, "À L'ÉPOQUE, DIDI B DISAIT :", 960, 260, 60, WHT),
        X(129.7, "« NOTRE OBJECTIF : UN GRAMMY »", 960, 460, 90, YEL), P(129.7, "3d/grammy.png", 960, 680, 200),
        X(132.4, "UNE VISION TRÈS LOINTAINE", 960, 900, 56, WHT, "box")]),
    # --- 3. DJ Arafat ---
    (136.80, 152.70, "dj-arafat.jpg", [C("dj-arafat.jpg", CL, 540, 520),
        X(136.9, "2016", CR, 220, 90, YEL), X(138.5, "AVEC LA PLUS GRANDE STAR DE L'ÉPOQUE", CR, 340, 40, WHT, "box"),
        X(142.0, "DJ ARAFAT", CR, 460, 100, GOLD), X(143.4, "« APPROCHEZ REGARDEZ »", CR, 600, 62, WHT),
        Nn(145.6, 147.6, 5202504, CR, 750, 84, GRN), X(147.7, "STREAMS SUR SPOTIFY", CR, 850, 44, WHT, "box")]),
    (152.70, 165.90, "dj-arafat.jpg", [C("dj-arafat.jpg", CL, 540, 520),
        X(149.7, "UNE RELATION PAS SIMPLE", CR, 220, 64, RED), X(152.8, "SELON AFRIQUE-SUR7 :", CR, 340, 44, WHT, "box"),
        X(153.8, "ARAFAT LEUR REPROCHE", CR, 450, 58, WHT), X(155.0, "D'ALLER AUX PRIMUD QU'IL BOYCOTTE", CR, 550, 44, WHT),
        X(159.4, "LEUR RÉPONSE :", CR, 690, 56, YEL), X(160.5, "« ON N'EST PAS LES DANSEURS D'ARAFAT »", CR, 800, 40, GOLD),
        X(163.0, "ÊTRE SON PROPRE PATRON", CR, 910, 52, WHT, "box")]),
    # --- 4. Universal ---
    (165.90, 197.20, "kiff-no-beat.jpg", [X(165.9, "2017 : LA CONSÉCRATION", 960, 110, 80, YEL),
        X(168.7, "1ER GROUPE DE HIP-HOP AFRICAIN", 960, 260, 64, WHT), X(170.8, "SIGNÉ CHEZ UNIVERSAL", 960, 370, 84, GOLD),
        P(170.8, "3d/lightning-gold.png", 1560, 350, 160), X(175.0, "SELON PAM : 1ERS SIGNÉS CHEZ UNIVERSAL MUSIC AFRICA", 960, 490, 40, WHT, "box"),
        X(180.0, "QUI VIENT DE S'INSTALLER À ABIDJAN", 960, 570, 42, WHT),
        C("sidiki-diabate.jpg", 600, 800, 260, 186.0), X(186.0, "2018 : AVEC SIDIKI DIABATÉ", 600, 990, 40, WHT, "box"), E(186.5, "🇲🇱", 820, 800, 60),
        X(192.9, "ET THE SHIN SEKAÏ", 1320, 800, 62, YEL), E(193.5, "🇫🇷", 1320, 900, 70)]),
    (197.20, 214.50, "bledard-is-the-new-fresh.jpg", [C("bledard-is-the-new-fresh.jpg", 400, 520, 520),
        X(197.3, "2019 · BLEDARD IS THE NEW FRESH", 1240, 110, 50, YEL),
        C("dadju.jpg", 960, 420, 250, 205.0), C("sofiane.jpg", 1260, 420, 290, 205.6), C("kaaris.jpg", 1560, 420, 250, 206.4), C("vegedream.jpg", 1260, 760, 220, 207.4),
        X(205.0, "DADJU", 960, 600, 40, WHT), X(205.6, "SOFIANE", 1260, 600, 40, WHT), X(206.4, "KAARIS", 1560, 600, 40, WHT), X(207.4, "VEGEDREAM", 1260, 920, 40, WHT),
        X(209.2, "UNE DINGUERIE", 1240, 1010, 54, RED)]),
    (214.50, 227.20, "dadju.jpg", [C("dadju.jpg", CL, 540, 460), X(211.4, "« PAUSE » FEAT. DADJU", CR, 220, 66, YEL),
        Nn(212.0, 213.5, 1968490, CR, 360, 80, GRN), X(213.6, "STREAMS SUR SPOTIFY", CR, 460, 44, WHT, "box"),
        X(214.6, "EN 10 ANS : DU CONCOURS RADIO", CR, 600, 48, WHT), X(219.9, "AUX PLUS GRANDS DU RAP FRANÇAIS", CR, 700, 46, WHT, "box"),
        X(223.0, "LE PATRON DU RAP IVOIRE", CR, 860, 68, GOLD)]),
    # --- 5. le dernier concert ---
    (227.20, 253.40, "affiche-on-va-pas-dormir-2019.jpg", [C("affiche-on-va-pas-dormir-2019.jpg", 960, 530, 860, zoom=(232.9, 235.0, 1.15, 0, 0)),
        X(232.9, "« ON VA PAS DORMIR ! »", 960, 80, 70, YEL), X(238.9, "LEUR 1ER GRAND CONCERT", 960, 980, 56, WHT, "box", out=244.6),
        X(244.7, "MAIS CE SOIR-LÀ…", 960, 980, 66, RED, out=247.6), X(247.6, "DJ ARAFAT EN CONCERT LE MÊME SOIR, À QUELQUES MÈTRES", 960, 980, 40, WHT, "box")]),
    (253.40, 271.00, "grid", [C("dj-arafat.jpg", 960, 470, 420), X(253.5, "12 AOÛT 2019", 960, 760, 84, WHT),
        X(254.5, "DJ ARAFAT NOUS QUITTE", 960, 880, 60, WHT, "box"), X(258.5, "TOUTE LA CÔTE D'IVOIRE SOUS LE CHOC", 960, 980, 46, WHT, out=262.0),
        X(262.1, "KIFF NO BEAT : PLUS DE GRAND CONCERT PENDANT 7 ANS", 960, 980, 42, YEL)]),
    # --- 6. les carrières solo ---
    (271.00, 302.80, "kiff-no-beat.jpg", [X(271.1, "NOVEMBRE 2019 : LES SOLOS", 960, 100, 70, YEL),
        X(272.5, "DIDI B", 330, 300, 70, WHT, "box"), X(277.7, "ELOW'N", 750, 300, 70, WHT, "box"), X(280.0, "EL JAY", 1170, 300, 70, WHT, "box"), X(282.5, "BLACK K", 1590, 300, 70, WHT, "box"),
        X(284.6, "LES FANS PANIQUENT", 960, 470, 70, RED), X(286.0, "LE GROUPE EST-IL FINI ?", 960, 570, 60, WHT),
        X(287.7, "LEUR RÉPONSE À LA TÉLÉ :", 960, 700, 50, WHT, "box"), X(288.8, "« UN PROGRAMME DE CARRIÈRES SOLO »", 960, 800, 56, GOLD),
        X(291.8, "PAS ASSEZ DE PLACE POUR 5 DANS UN MORCEAU", 960, 900, 42, WHT), X(297.0, "AUCUN PROBLÈME ENTRE EUX", 960, 990, 50, YEL, "box")]),
    (302.80, 326.40, "zenith-complet.jpg", [X(302.9, "DIDI B DEVIENT UN PHÉNOMÈNE", 960, 100, 70, YEL),
        C("92i-africa.jpg", 330, 460, 330, 306.9), X(306.9, "BIG BOSS · 92I AFRICA", 330, 690, 40, WHT, "box"),
        C("mojotrone-2-history.jpg", 760, 460, 330, 314.0), Nn(315.0, 317.0, 50000000, 760, 690, 48, GRN, " ÉCOUTES"),
        C("stade-fhb-felicia.jpg", 1190, 460, 360, 319.1), X(319.1, "FÉLICIA · 2025", 1190, 690, 40, WHT, "box"),
        C("zenith-complet.jpg", 1600, 460, 260, 322.5), X(322.5, "ZÉNITH · 2026", 1600, 690, 40, WHT, "box")]),
    (326.40, 352.30, "grid", [V("kiff-no-beat-clip-e-verres-fete-16x9.mp4", None, 960, 540, 1920, ss=2.0, mode="bg", gain=0.1), X(326.5, "ELOW'N", 600, 220, 100, YEL), X(327.6, "SON ALBUM EN NOVEMBRE", 600, 340, 46, WHT, "box"),
        X(331.7, "15 TITRES EN INDÉPENDANT", 600, 450, 50, WHT),
        X(336.6, "JOOCHAR", 1320, 220, 100, YEL), X(338.0, "ENCHAÎNE LES PROJETS", 1320, 340, 46, WHT, "box"), X(340.0, "2025 · 2026", 1320, 450, 50, WHT),
        X(346.3, "BLACK K & EL JAY", 960, 680, 80, GOLD), X(348.0, "LEUR SON, ET SUR CELUI DES AUTRES", 960, 800, 46, WHT, "box")]),
    # --- 7. le retour ---
    (352.30, 376.30, "c-komen.jpg", [C("spotify-populaires.jpg", 960, 300, 1300, 352.4),
        X(352.4, "2021 : « ÉTONNÉ »", 520, 600, 62, YEL), Nn(354.0, 356.5, 5655379, 520, 720, 80, GRN), X(356.6, "LEUR SON LE PLUS ÉCOUTÉ", 520, 820, 42, WHT, "box"),
        C("c-komen.jpg", 1400, 680, 300, 359.9), X(359.9, "2024 · « C KOMEN ? »", 1400, 880, 44, WHT, "box"),
        X(365.2, "+ « DOHI »", 1400, 960, 50, YEL)]),
    (369.30, 376.30, "affiche-kiff-no-beat-28-nov.jpg", [C("affiche-kiff-no-beat-28-nov.jpg", CL, 540, 540),
        X(369.3, "SAMEDI 28 NOVEMBRE", CR, 280, 80, YEL), X(371.0, "PARC DES EXPOSITIONS", CR, 410, 60, WHT, "box"),
        X(372.5, "LES 5 SUR SCÈNE", CR, 560, 84, GOLD), X(375.0, "7 ANS APRÈS", CR, 700, 96, RED)]),
    # --- 8. mon avis ---
    (376.30, 410.80, "kiff-no-beat.jpg", [C("kiff-no-beat.jpg", 520, 540, 640),
        X(376.4, "MON AVIS :", CR, 180, 70, YEL), X(377.8, "ILS N'ONT JAMAIS DISPARU", CR, 290, 60, WHT),
        X(380.0, "UNE PAUSE, SANS SE DÉTRUIRE", CR, 400, 50, GOLD, "box"), X(384.1, "PAS DE CLASH · PAS DE PROCÈS", CR, 510, 48, WHT),
        X(391.4, "LE RÊVE : UN GRAMMY", CR, 650, 66, YEL), P(391.4, "3d/grammy.png", CR + 380, 640, 130),
        X(402.8, "ET APRÈS SAMEDI ?", CR, 790, 66, RED), X(404.0, "UN NOUVEL ALBUM ?", CR, 900, 70, GOLD)]),
    # --- question ---
    (410.80, 433.40, "grid", [V("kiff-no-beat-clip-a-bar-champagne-16x9.mp4", None, 960, 540, 1920, ss=1.0, mode="bg", gain=0.1), X(410.9, "VOTRE SON PRÉFÉRÉ DE KIFF NO BEAT ?", 960, 200, 70, YEL),
        X(414.3, "LE MIEN :", 960, 360, 56, WHT), X(415.0, "« APPROCHEZ REGARDEZ »", 960, 460, 72, GOLD), X(419.4, "« ÉTONNÉ »", 960, 570, 72, GOLD),
        X(421.6, "DITES-LE EN COMMENTAIRE", 960, 730, 60, WHT, "box"), E(421.6, "💬", 1420, 730, 90),
        X(427.2, "ABONNEZ-VOUS À MA PAGE FACEBOOK", 960, 880, 52, YEL)]),
    (433.40, END + 1, "end", []),
]
CHAPTERS = [  # (source time, top, bottom) — 3D title over the first seconds of each chapter; YouTube chapters list
    (0.0, "INTRO", ""), (25.00, "CHAPITRE 1", "LES DÉBUTS"), (69.40, "CHAPITRE 2", "L'ASCENSION"), (136.80, "CHAPITRE 3", "DJ ARAFAT"),
    (165.90, "CHAPITRE 4", "UNIVERSAL"), (227.20, "CHAPITRE 5", "LE DERNIER CONCERT"), (271.00, "CHAPITRE 6", "LES CARRIÈRES SOLO"),
    (352.30, "CHAPITRE 7", "LE RETOUR"), (376.30, "CHAPITRE 8", "MON AVIS"), (410.80, "ET VOUS ?", "")]
HOOK = (R(12.68), R(17.0))
hook_img = block("7 ANS", "DE SILENCE", 1200, 640)
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
place(hit, HOOK[0], 0.5); place(riser, HOOK[0] - 2.95, 0.4); place(riser, R(244.7) - 2.95, 0.4)   # « mais ce soir-là… »
place(crowd, R(170.8), 0.25); place(riser, R(369.3) - 2.95, 0.45)                                # Universal ; le retour
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
