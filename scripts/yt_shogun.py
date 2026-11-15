"""YouTube 16:9 video from a voice-over, no face-cam (« Didi B : pourquoi tout recommencer à Lagos ? » / Shogun in Lagos).
Style taken from the explainer he asked to study: photos and covers shown as glowing CARDS over a blurred copy of
themselves, keywords only on screen (no full subtitles), counters on numbers, 3D chapter titles, white flash on cuts,
his burn transition on chapter changes, logo pulsing with his voice, end card. Gentle silence cut for long-form.
usage: yt_shogun.py WORK OUT.mp4    (WORK holds src.mp3, words.json and img/*.jpg)"""
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

DROP = [(222.20, 222.70)]                             # « Kai » removed at his request

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
keep[int(451.3 / 0.02):] = True                       # sign-off kept whole
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
INS = [  # (source time where his voice pauses, duration, clip, clip start) — Didi B speaks at Planète Rap
    (127.40, 12.0, "didib-interview-planete-rap-16x9.mp4", 8.95)]
def R(t): return R0(t) + sum(d for at, d, *_ in INS if t >= at)
INS_OUT = [(R0(at) + sum(d2 for at2, d2, *_ in INS if at2 < at), d, clip, ss) for at, d, clip, ss in INS]
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
    (0.0, 5.45, "shogun-in-lagos.jpg", [C("shogun-in-lagos.jpg", CL, 540, 720), X(0.3, "6 NOVEMBRE 2026", CR, 380, 90, YEL),
        X(T("shogun"), "SHOGUN IN LAGOS", CR, 560, 96, WHT, "type"), X(T("shogun") + 0.8, "LA MIXTAPE DE DIDI B", CR, 720, 60, WHT, "box")]),
    (5.45, 11.55, "grid", [Nn(T("23", 5), T("titres", 5), 23, 960, 220, 170, YEL, " TITRES"),
        C("davido.jpg", 420, 640, 380, T("davido", 5)), C("phyno.jpg", 860, 640, 380, T("finos", 5)),
        C("zlatan.jpg", 1240, 640, 340, T("latan", 5)), C("tayc.jpg", 1560, 640, 330, T("tyque", 5)),
        X(T("featuring", 5), "DES FEATURINGS", 960, 940, 70, WHT, "box")]),
    (11.55, 24.30, "shogun-in-lagos.jpg", [C("shogun-in-lagos.jpg", CL, 540, 640),
        E(T("ivoire", 11), CI, CR - 330, 330, 120), X(T("tête", 11), "N°1 APPLE MUSIC", CR + 60, 330, 84, YEL),
        E(T("nigeria", 15), NG, CR - 330, 520, 120), X(T("chartes", 17), "ENTRÉE DANS LES CHARTS", CR + 60, 520, 72, WHT),
        X(T("première", 20), "UNE PREMIÈRE", CR, 720, 96, GOLD), X(T("ivoirien", 21), "POUR UN ARTISTE IVOIRIEN", CR, 840, 60, WHT, "box"),
        P(T("première", 20), "3d/lightning-gold.png", CR + 380, 690, 200)]),
    (24.30, 30.75, "zenith-complet.jpg", [C("zenith-complet.jpg", 960, 560, 520, None)]),
    (30.75, 36.0, "grid", [X(30.8, "AVANT DE COMMENCER", 960, 160, 96, WHT), X(T("liker", 30), "LIKE", 560, 520, 130, WHT), X(T("commenter", 30), "COMMENTE", 960, 520, 130, YEL),
        X(T("partager", 30), "PARTAGE", 1380, 520, 130, RED), P(T("liker", 30), "3d/heart-gold.png", 560, 300, 200),
        E(T("commenter", 30), "💬", 960, 300, 170), E(T("partager", 30), "🔁", 1380, 300, 170)]),
    # --- 1. les débuts ---
    (36.0, 45.80, "kiff-no-beat.jpg", [C("kiff-no-beat.jpg", CL, 520, 820, out=T("premier", 40)),
        V("kiff-no-beat-clip-16x9.mp4", T("premier", 40), CL, 520, 820, ss=10.0, credit="SOURCE : TIKTOK @2X_RAMAZANNY"), X(T("keefnobit"), "KIFF NO BEAT", CR + 80, 330, 110, YEL, "type"),
        X(T("2009"), "2009 · ABIDJAN", CR + 80, 480, 70, WHT, "box"), X(T("premier", 40), "1ER GROUPE HIP-HOP AFRICAIN", CR + 80, 640, 58, WHT),
        X(T("universal"), "SIGNÉ CHEZ UNIVERSAL", CR + 80, 740, 74, GOLD), X(T("2017"), "2017", CR + 80, 860, 70, WHT, "box")]),
    # --- 2. la carrière solo ---
    (45.80, 55.0, "grid", [X(T("solo"), "LA CARRIÈRE SOLO", 960, 230, 110, WHT), C("92i-africa.jpg", 960, 600, 460, T("label", 48)),
        X(T("woba"), "LE LABEL DE BOOBA", 960, 930, 64, WHT, "box")]),
    (55.0, 63.55, "mojotrone-2-history.jpg", [C("mojotrone-2-history.jpg", CL, 540, 700),
        X(T("mojotron"), "MOJOTRONE II : HISTORY", CR, 420, 76, GOLD, "type"),
        E(T("chartes", 59), FR, CR - 280, 640, 110), X(T("chartes", 59), "DANS LES CHARTS EN FRANCE", CR + 60, 640, 58, WHT)]),
    (63.55, 76.30, "projet-genius.jpg", [C("projet-genius.jpg", CL, 540, 700), X(T("quitté"), "APRÈS 92i", CR, 300, 80, WHT),
        X(T("2025", 64), "SON PROJET 2025", CR, 430, 80, YEL), X(T("platine", 70), "DISQUE DE PLATINE", CR, 640, 96, GOLD),
        P(T("platine", 70), "3d/lightning-gold.png", CR + 400, 600, 180), X(T("prodemsi"), "APRODEMCI · CÔTE D'IVOIRE", CR, 780, 56, WHT, "box")]),
    # --- 3. Félicia ---
    (76.30, 94.65, "stade-fhb-felicia.jpg", [C("stade-fhb-felicia.jpg", 960, 480, 960, out=T("remplir")),
        V("didib-stade-fhb-concert-16x9.mp4", T("remplir"), 960, 480, 960, ss=7.0, out=89.4, credit="SOURCE : TIKTOK @MARCEL.MEDIA0"),
        X(T("mai", 76), "3 MAI 2025", 960, 105, 84, YEL, out=89.4), Nn(T("plus", 82), T("personnes", 84), 30000, 960, 880, 130, YEL, " PERSONNES", out=89.4),
        X(T("alpha", 85), "1ÈRE FOIS DEPUIS ALPHA BLONDY EN 1985", 960, 1005, 56, WHT, "box", out=89.4),
        X(T("tout", 89), "IL A TOUT GAGNÉ", 960, 400, 120, WHT), X(T("nouveau", 92), "NOUVEAU TERRAIN", 960, 600, 100, YEL),
        E(T("nigeria", 92), NG, 960, 790, 170)]),
    # --- 4. cap sur le Nigeria ---
    (94.65, 106.10, "nueva-era.jpg", [C("nueva-era.jpg", CL, 540, 700), X(T("novembre", 94), "14 NOVEMBRE 2025", CR, 330, 84, YEL),
        X(T("juventus"), "JUVENTUS NUEVA ERA", CR, 500, 80, WHT, "type"), Nn(T("neuf"), T("titres", 103), 9, CR, 700, 120, GOLD, " TITRES")]),
    (106.10, 111.95, "nueva-era-deluxe.jpg", [C("nueva-era-deluxe.jpg", CL, 540, 700), X(T("luxe"), "VERSION DELUXE", CR, 480, 100, GOLD),
        X(T("quelques", 105), "QUELQUES MOIS APRÈS", CR, 340, 64, WHT, "box")]),
    (111.95, 131.0, "zenith-complet.jpg", [C("zenith-live.jpg", 520, 540, 420), C("zenith-complet.jpg", 1400, 540, 520, T("guichet")),
        X(T("dix-neuf"), "19 AVRIL 2026", 960, 110, 84, YEL), X(T("zénith", 118), "ZÉNITH DE PARIS", 960, 960, 90, WHT),
        S(T("sold", 124), "SOLD OUT", 1400, 760, 110), X(T("deuxième", 118), "2E RAPPEUR IVOIRIEN", 960, 860, 56, WHT, "box", out=T("guichet"))]),
    (131.0, 139.40, "je-mappelle.jpg", [C("je-mappelle.jpg", 420, 540, 500), C("zlatan.jpg", 890, 560, 330, T("zlatan", 130)),
        X(T("zlatan", 130), "« JE M'APPELLE »", 1470, 330, 90, YEL), X(T("zlatan", 130), "FEAT. ZLATAN", 1470, 450, 64, WHT, "box"),
        Nn(T("bientôt", 133), T("millions", 135), 5000000, 1470, 650, 120, GRN), X(T("spotify", 136), "STREAMS SUR SPOTIFY", 1470, 790, 60, WHT, "box"),
        P(T("bientôt", 133), "3d/money-stack-teal.png", 1470, 920, 220)]),
    (139.40, 155.80, "grid", [X(T("enchaîne"), "IL ENCHAÎNE LES SINGLES", 960, 170, 96, WHT), P(T("singles", 141), "3d/music-note-gold.png", 960, 540, 260),
        C("mavo.jpg", 480, 560, 380, T("mavo")), X(T("mavo"), "FEAT. MAVO", 480, 860, 60, WHT, "box"),
        V("young-jonn-diner-raba-16x9.mp4", T("young", 146), 1400, 560, 640, ss=9.1, gain=0.2), X(T("young", 146), "« RABA » FEAT. YOUNG JONN", 1400, 860, 60, WHT, "box")]),
    # --- 5. la signature ---
    (155.80, 177.10, "paper_red", [X(T("juin"), "JUIN 2026", 960, 170, 96, YEL), X(T("sonic", 158), "SIGNÉ CHEZ SONY MUSIC FRANCE", 960, 330, 96, WHT),
        E(T("sonic", 158), "✍️", 960, 500, 150), X(T("annoncent"), "ANNONCÉ PAR LE LABEL", 960, 660, 60, WHT, "box"),
        X(T("pôle"), "LE NOUVEAU PÔLE AFRO DE SONY", 960, 780, 64, GOLD), X(T("rca"), "+ RCA RECORDS FRANCE", 960, 910, 80, RED),
        P(T("sonic", 158), "3d/money-stack-gold.png", 300, 520, 300), P(T("sonic", 158), "3d/money-stack-gold.png", 1620, 520, 300)]),
    # --- 6. Shogun in Lagos ---
    (177.10, 192.15, "shogun-in-lagos.jpg", [C("shogun-in-lagos.jpg", CL, 540, 700), X(T("octobre"), "OCTOBRE 2026 : L'ANNONCE", CR, 300, 64, WHT, "box"),
        X(T("attendait"), "LA MIXTAPE TANT ATTENDUE", CR, 450, 66, YEL), X(T("vendredi"), "VENDREDI 6 NOVEMBRE", CR, 620, 84, WHT),
        X(T("distribué"), "DISTRIBUÉ PAR SONY MUSIC FRANCE", CR, 780, 52, WHT, "box")]),
    (192.15, 208.30, "grid", [V("zrai-studio-16x9.mp4", None, 960, 540, 1920, ss=8.0, mode="bg", gain=0.15), Nn(T("23", 192), T("titres", 193), 23, 960, 230, 160, YEL, " TITRES"),
        X(T("afrobit"), "UNE DA AFROBEATS", 960, 470, 130, GOLD), P(T("afrobit"), "3d/music-note-red.png", 360, 520, 260),
        P(T("afrobit"), "3d/music-note-gradient.png", 1560, 520, 260), X(T("rap", 200), "PAS DU RAP CETTE FOIS", 960, 720, 80, RED),
        X(T("vraiment", 203), "100 % AFROBEATS", 960, 880, 76, WHT, "box")]),
    (208.30, 224.45, "grid", [X(T("exclusivités"), "7 EXCLUSIVITÉS SUR 23 TITRES", 960, 120, 76, YEL), X(T("nigeria", 215), "NIGERIA À L'HONNEUR", 960, 230, 86, WHT),
        E(T("nigeria", 215), NG, 1460, 230, 110),
        C("davido.jpg", 280, 560, 300, T("davido", 218)), C("phyno.jpg", 600, 560, 300, T("finot", 218)), C("zlatan.jpg", 900, 560, 260, T("zlatan", 219)), X(T("zlatan", 219), "ZLATAN", 900, 820, 50, WHT),
        C("young-jonn.jpg", 1180, 560, 250, T("youngjoin")), C("qing-madi.jpg", 1460, 560, 250, T("queen")), C("mavo.jpg", 1720, 560, 230, T("mavo", 222)),
        X(T("davido", 218), "DAVIDO", 280, 820, 50, WHT), X(T("finot", 218), "PHYNO", 600, 820, 50, WHT), X(T("youngjoin"), "YOUNG JONN", 1180, 820, 50, WHT),
        X(T("queen"), "QING MADI", 1460, 820, 50, WHT), X(T("mavo", 222), "MAVO", 1720, 820, 50, WHT)]),
    (224.45, 237.0, "grid", [C("king-promise.jpg", 300, 520, 330, T("king", 224)), E(T("ghana"), GH, 300, 820, 90), X(T("king", 224), "KING PROMISE", 300, 920, 48, WHT),
        C("focalistic.jpg", 760, 520, 330, T("focalistique")), E(T("afrique", 225), ZA, 760, 820, 90), X(T("focalistique"), "FOCALISTIC", 760, 920, 48, WHT),
        C("tayc.jpg", 1200, 520, 330, T("taïk")), X(T("taïk"), "TAYC", 1200, 920, 48, WHT),
        C("nsg.jpg", 1640, 520, 330, T("nsg")), E(T("londonien"), GB, 1640, 820, 90), X(T("nsg"), "NSG", 1640, 920, 48, WHT),
        X(T("ghana"), "AU-DELÀ DU NIGERIA", 960, 120, 76, YEL)]),
    (237.0, 244.35, "je-mappelle.jpg", [V("didib-je-mappelle-clip-16x9.mp4", None, 560, 540, 780, ss=0.5, gain=0.2, credit="SOURCE : TIKTOK @DIDIB.MOJAVELI"), X(T("je", 237), "« JE M'APPELLE »", CR, 340, 90, YEL),
        X(T("prod", 238), "SUR UNE PROD AMAPIANO", CR, 500, 64, WHT, "box"), X(T("différence"), "IL A FAIT LA DIFFÉRENCE", CR, 680, 72, GOLD)]),
    (244.35, 275.70, "davido.jpg", [C("davido.jpg", 960, 545, 800), X(T("attendu"), "LE SON LE PLUS ATTENDU", 960, 110, 90, YEL, out=T("savent")),
        X(T("davido", 247), "FEAT. DAVIDO", 960, 960, 90, WHT, out=T("savent")),
        X(T("savent"), "ENREGISTRÉ IL Y A PLUS D'1 AN", 960, 110, 80, WHT, out=T("moment", 255)), X(T("clip", 254), "LE CLIP EST DÉJÀ TOURNÉ", 960, 960, 70, WHT, "box", out=T("moment", 255)),
        X(T("moment", 255), "BIENTÔT SUR YOUTUBE", 960, 110, 90, RED, out=T("écouté", 259)),
        X(T("écouté", 259), "IL A FAIT DU SALE", 960, 110, 100, YEL, out=T("époque")), X(T("alchimie"), "L'ALCHIMIE", 960, 960, 80, GOLD, out=T("époque")),
        X(T("époque"), "COMME LE DAVIDO D'AVANT", 960, 110, 84, WHT), X(T("banger"), "UN BANGER", 960, 960, 130, RED),
        E(T("banger"), "🔥", 640, 960, 130), E(T("banger"), "🔥", 1280, 960, 130)]),
    # --- 7. les chiffres ---
    (275.70, 298.65, "shogun-in-lagos.jpg", [C("shogun-in-lagos.jpg", CL, 540, 640), X(T("charts", 276), "TOUJOURS DANS LES CHARTS", CR, 230, 66, WHT),
        E(T("ivoire", 277), CI, CR - 140, 340, 100), E(T("nigeria", 280), NG, CR + 140, 340, 100),
        Nn(T("plus", 287), T("streams", 288), 20000000, CR, 540, 110, GRN), X(T("spotify", 289), "STREAMS SUR SPOTIFY", CR, 660, 60, WHT, "box"),
        P(T("plus", 287), "3d/money-stack-gold.png", CR + 380, 560, 220),
        X(T("platine", 294), "ÉLIGIBLE PLATINE", CR, 800, 80, GOLD), X(T("double", 296), "VOIRE DOUBLE PLATINE", CR, 910, 60, WHT, "box")]),
    # --- 8. le concert de Lagos ---
    (298.65, 314.90, "affiche-afrika-shrine.jpg", [C("affiche-afrika-shrine.jpg", CL, 540, 720), X(T("dimanche"), "DIMANCHE 8 NOVEMBRE", CR, 260, 80, YEL),
        X(T("concert", 303), "1ER CONCERT AU NIGERIA", CR, 390, 76, WHT), X(T("africa", 304), "AFRIKA SHRINE · LAGOS", CR, 520, 64, WHT, "box"),
        X(T("salle", 307), "LA SALLE MYTHIQUE DE FELA KUTI", CR, 680, 52, GOLD), S(T("guiche"), "GUICHET FERMÉ", CR, 860, 90)]),
    (314.90, 334.25, "affiche-afrika-shrine.jpg", [C("affiche-afrika-shrine.jpg", 960, 540, 1000, None, gray_at=T("surprise"), zoom=(314.95, 316.5, 1.0, 0, -260)),
        X(T("annoncés", 315), "SUR L'AFFICHE", 960, 90, 80, WHT, out=T("surprise")),
        X(T("surprise"), "SURPRISE", 960, 300, 140, RED), X(T("seul", 325), "IL EST SEUL SUR SCÈNE", 960, 460, 96, WHT),
        K(T("pas", 328), 420, 560, 1500, 1060), X(T("aucun", 330), "AUCUN INVITÉ NIGÉRIAN", 960, 1000, 70, WHT, "box")]),
    (334.25, 347.0, "grid", [P(T("polémique"), "3d/wifi-red.png", 960, 260, 230), X(T("polémique"), "LA POLÉMIQUE ÉCLATE", 960, 470, 110, RED),
        E(T("frustrés"), "😤", 560, 650, 140), X(T("frustrés"), "FANS FRUSTRÉS", 560, 800, 70, WHT, "box"),
        X(T("personne", 339), "PERSONNE NE VIENT", 560, 900, 56, WHT),
        E(T("courage"), "💪", 1360, 650, 140), X(T("courage"), "D'AUTRES : DU COURAGE", 1360, 800, 70, WHT, "box"),
        X(T("dur", 345), "LE MARCHÉ LE PLUS DUR D'AFRIQUE", 1360, 900, 50, GOLD)]),
    (347.0, 375.70, "grid", [X(347.0, "LOIN DE SA ZONE DE CONFORT", 960, 200, 90, WHT), X(352.0, "AU NIGERIA, IL REPART DE ZÉRO", 960, 340, 86, YEL),
        X(T("single", 359), "« GOOD VIBES » FEAT. ZINOLEESKY", 960, 540, 76, WHT), X(T("d'or", 364), "1ER SINGLE D'OR AU NIGERIA", 960, 660, 70, GOLD, "box"),
        X(T("remontés"), "DES FANS REMONTÉS", 960, 860, 90, RED), E(T("remontés"), "😡", 1480, 860, 110)]),
    (375.70, 392.45, "grid", [X(T("stratégie"), "UNE STRATÉGIE ?", 960, 260, 110, YEL), E(T("stratégie"), "❓", 1440, 250, 140),
        X(T("déplacer"), "OU UN EMPÊCHEMENT ?", 960, 420, 100, WHT), X(T("tanzanie") - 0.6, "ON NE SAIT PAS", 960, 580, 70, WHT, "box"),
        X(T("conclure"), "LE CONCERT S'EST BIEN PASSÉ", 960, 800, 84, GRN), E(T("débordement"), "✅", 960, 930, 120)]),
    # --- 9. mon avis ---
    (392.45, 410.10, "shogun-in-lagos.jpg", [C("shogun-in-lagos.jpg", CL, 540, 640), X(T("avis", 392), "MON AVIS", CR, 260, 110, YEL),
        X(T("écouter", 395), "ALLEZ L'ÉCOUTER", CR, 420, 80, WHT), E(T("écouter", 395), "🎧", CR + 340, 420, 110),
        X(T("tiktok"), "MON AVIS EST SUR TIKTOK", CR, 560, 56, WHT, "box"), X(T("challenge"), "UN TRÈS GROS CHALLENGE", CR, 740, 72, GOLD)]),
    (410.10, 437.55, "grid", [X(T("marche", 410), "SI ÇA MARCHE…", 960, 170, 100, WHT), X(T("francophone"), "DES PORTES S'OUVRENT POUR LES FRANCOPHONES", 960, 300, 64, YEL),
        X(T("babi"), "SHOGUN IN BABI ?", 560, 520, 96, GOLD), X(T("us", 423), "SHOGUN IN US ?", 1360, 520, 96, GOLD),
        E(T("babi"), CI, 560, 640, 90), E(T("us", 423), US, 1360, 640, 90),
        X(T("colombiens"), "DES FEATS AVEC DES COLOMBIENS", 960, 800, 66, WHT, "box"), E(T("colombie"), CO, 760, 920, 90),
        X(T("amérique"), "CAP SUR L'AMÉRIQUE", 1080, 920, 64, RED)]),
    # --- question ---
    (437.55, 451.35, "grid", [X(T("raison"), "A-T-IL EU RAISON ?", 960, 170, 120, YEL), E(T("nigeria", 440), NG, 560, 430, 170), X(T("nigeria", 440), "LE NIGERIA", 560, 600, 84, WHT),
        X(T("rester"), "OU", 960, 470, 90, RED), E(T("ivoire", 442), CI, 1360, 430, 170), X(T("ivoire", 442), "LE RAP IVOIRE", 1360, 600, 84, WHT),
        X(T("commentaire"), "DITES-LE EN COMMENTAIRE", 960, 800, 84, YEL), E(T("commentaire"), "💬", 1500, 790, 110),
        X(T("réaction"), "MA RÉACTION COMPLÈTE : LIEN EN DESCRIPTION", 960, 930, 52, WHT, "box")]),
    (451.35, END + 1, "end", []),
]
CHAPTERS = [  # (source time, top, bottom) — 3D title over the first seconds of each chapter; YouTube chapters list
    (0.0, "INTRO", ""), (36.0, "CHAPITRE 1", "LES DÉBUTS"), (45.80, "CHAPITRE 2", "LA CARRIÈRE SOLO"), (76.30, "CHAPITRE 3", "LE STADE FÉLICIA"),
    (94.65, "CHAPITRE 4", "CAP SUR LE NIGERIA"), (155.80, "CHAPITRE 5", "LA SIGNATURE"), (177.10, "CHAPITRE 6", "SHOGUN IN LAGOS"),
    (275.70, "CHAPITRE 7", "LES CHIFFRES"), (298.65, "CHAPITRE 8", "LE CONCERT DE LAGOS"), (392.45, "CHAPITRE 9", "MON AVIS"),
    (437.55, "ET VOUS ?", "")]
HOOK = (R(T("pourquoi", 23)), R(30.75))
hook_img = block("POURQUOI TOUT|RECOMMENCER", "À LAGOS ?", 1500, 760)
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
enc = None if SNAP else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", "noise=alls=3:allf=t+u,format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "19", VIDEO_ONLY], stdin=subprocess.PIPE)
lab_cache = {}; _vins = {}
for i in (frames if SNAP else range(f0, f1)):
    t = i / FPS
    si = max(j for j, s in enumerate(SC) if s[0] <= t) if t >= SC[0][0] else 0
    ts, te, bgs, els = SC[si]; k = t - ts
    ins = next((x for x in INS_OUT if x[0] <= t < x[0] + x[1]), None)
    if ins:
        o0, d, clip, ss = ins; kk = t - o0; k = kk
        img = background("zenith-complet.jpg", t, kk)
        if ins not in _vins: _vins[ins] = V(clip, None, 960, 495, 1220, ss=ss, credit="SOURCE : PLANÈTE RAP / SKYROCK")
        draw_video(img, _vins[ins], kk, float(np.clip((d - kk) / 0.2, 0, 1)))
        lb = kbox("DIDI B À PLANÈTE RAP", 44); paste(img, lb, W / 2, 75, popk(kk), min(kk / 0.1, 1))
        for q0, q1, q in ((0.9, 6.2, "« ON NE POUVAIT MÊME PAS PARLER DE ZÉNITH »"), (10.3, d, "« IL NOUS MONTRE LA VOIE, ON LE SUIT »")):
            if q0 <= kk < q1: im, _ = neon(q, 48, YEL); paste(img, im, W / 2, 935, popk(kk - q0), min((kk - q0) / 0.08, 1) * min((q1 - kk) / 0.15, 1))
        if 6.4 <= kk < 10.2: im, _ = neon("FALLY IPUPA · 2 STADES DE FRANCE", 46, WHT); paste(img, im, W / 2, 935, popk(kk - 6.4), min((kk - 6.4) / 0.08, 1))
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
enc.stdin.close(); enc.wait()
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
for o0, d, clip, ss in INS_OUT:
    place(clip_audio(clip, ss, d), o0, 1.0); place(whooshes[0][0], o0 - whooshes[0][1], 0.25)
for c in CHAPTERS:
    if c[2]: place(hit, R(c[0]), 0.45)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.45)
place(hit, HOOK[0], 0.5); place(riser, HOOK[0] - 2.95, 0.4); place(riser, R(T("surprise")) - 2.95, 0.45)
place(uhh, R(T("vient", 340)) + 0.15, 0.2); place(crowd, R(T("personnes", 84)), 0.3)
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
