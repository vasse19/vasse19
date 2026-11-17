"""YouTube 16:9 video from a voice-over, no face-cam (« Himra : le bilan de son année 2026 »).
Style taken from the explainer he asked to study: photos and covers shown as glowing CARDS over a blurred copy of
themselves, keywords only on screen (no full subtitles), counters on numbers, 3D chapter titles, white flash on cuts,
his burn transition on chapter changes, logo pulsing with his voice, end card. Gentle silence cut for long-form.
usage: yt_himra.py WORK OUT.mp4    (WORK holds src.mp3, words.json and img/*.jpg)"""
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
keep[int(413.6 / 0.02):] = True                       # sign-off kept whole
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
INS = [  # (source time where his voice pauses, duration, clip, clip start) — Himra receives his Flamme
    (94.05, 12.3, "himra-flammes-16x9.mp4", 4.3)]
INS_LOOK = {94.05: ("flammes-trophee.jpg", "HIMRA AUX FLAMMES", "SOURCE : TIKTOK @LESFLAMMESAWARDS",
                    [(0.2, 4.6, "« C'EST LA PREMIÈRE FLAMME DE L'AFRIQUE »"), (9.0, 12.3, "« PREMIÈRE FLAMME AFRICAINE POUR LA CÔTE D'IVOIRE »")])}
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
    (0.0, 10.85, "zenith-28-01-2026.jpg", [
        C("zenith-28-01-2026.jpg", CL, 540, 760, out=T("single")), C("number-one-or-snep.jpg", CL, 540, 420, T("single"), out=T("trophy")),
        C("flammes-trophee.jpg", CL, 540, 440, T("trophy"), out=T("album")), C("sorry-im-bad.jpg", CL, 540, 560, T("album"), out=T("combat")),
        C("affiche-boxe-5-dec.jpg", CL, 540, 640, T("combat")),
        X(0.32, "UN ZÉNITH DE PARIS", CR, 220, 66, WHT), X(T("single"), "UN SINGLE D'OR SNEP", CR, 340, 66, GOLD),
        X(T("trophy"), "UN TROPHÉE HISTORIQUE", CR, 460, 66, WHT), X(T("album"), "UN ALBUM N°1", CR, 580, 66, YEL),
        X(T("combat"), "UN COMBAT DE BOXE", CR, 720, 84, RED), X(T("contre"), "CONTRE UN BOXEUR ITALIEN", CR, 840, 52, WHT, "box")]),
    (10.85, 18.45, "affiche-ebimpe-26-dec.jpg", [C("affiche-ebimpe-26-dec.jpg", CL, 540, 520, T("26")),
        X(T("26"), "26 DÉCEMBRE 2026", CR, 300, 84, YEL), X(T("ebimpe"), "LE STADE EBIMPÉ", CR, 450, 96, WHT, "type"),
        X(T("ebimpe") + 1.0, "LE PLUS GROS STADE DE CÔTE D'IVOIRE", CR, 620, 46, WHT, "box")]),
    # --- 1. le Zénith ---
    (18.45, 33.30, "zenith-28-01-2026.jpg", [C("zenith-28-01-2026.jpg", 960, 500, 1000, out=30.1),
        V("himra-zenith-live-16x9.mp4", 30.1, 960, 500, 1000, ss=2.0),
        X(18.52, "LE FILM DE SON ANNÉE 2026", 960, 110, 80, WHT, out=22.5), X(22.6, "28 JANVIER 2026", 960, 110, 90, YEL),
        X(26.8, "ZÉNITH DE PARIS", 960, 960, 96, WHT, out=30.1), X(30.2, "DEVANT DES MILLIERS DE PERSONNES", 960, 960, 64, WHT, "box")]),
    (33.30, 50.40, "zenith-28-01-2026.jpg", [V("himra-zenith-live-16x9.mp4", None, CL, 540, 820, ss=14.0),
        X(35.0, "SON ENTRÉE", CR, 260, 96, WHT), X(38.0, "SUR UN TRÔNE, AVEC UNE COURONNE", CR, 390, 46, GOLD, "box"),
        E(38.6, "👑", CR, 520, 130), X(42.0, "LE NOUVEAU BOSS DU RAP IVOIRE", CR, 680, 56, YEL), X(45.5, "IL FALLAIT ÊTRE LÀ", CR, 820, 76, RED)]),
    (50.40, 62.50, "disque-or-la-fouine.jpg", [C("la-fouine.jpg", CL, 540, 560, out=58.2), C("disque-or-la-fouine.jpg", CL, 540, 820, 58.2),
        X(52.0, "SON MENTOR, SON IDOLE", CR, 260, 66, WHT), X(55.5, "LA FOUINE", CR, 400, 120, YEL, "type"),
        X(58.3, "DISQUE D'OR HONORIFIQUE", CR, 580, 66, GOLD), P(58.3, "3d/lightning-gold.png", CR + 380, 560, 160),
        X(60.0, "CAPITALE DU CRIME RADIO VOL. 2", CR, 700, 46, WHT, "box")]),
    # --- 2. le single d'or ---
    (62.50, 83.40, "number-one-or-snep.jpg", [C("number-one-or-snep.jpg", CL, 540, 500),
        X(64.5, "QUELQUES TEMPS APRÈS", CR, 180, 50, WHT, "box"), X(66.9, "1ER SINGLE D'OR SNEP", CR, 300, 84, GOLD),
        X(68.6, "« NUMBER ONE »", CR, 430, 100, YEL), X(70.5, "FEAT. MINZ", CR, 550, 60, WHT, "box"), E(70.5, "🇳🇬", CR + 220, 550, 70), C("minz.jpg", CL + 300, 800, 250, 70.5),
        X(73.8, "UNE PREMIÈRE POUR LE RAP IVOIRE", CR, 680, 54, WHT),
        Nn(76.5, 79.0, 15000000, CR, 810, 96, GRN, out=81.5), X(79.2, "ÉQUIVALENTS STREAMS", CR, 910, 44, WHT, "box", out=81.5),
        X(81.55, "LE PLATINE BIENTÔT ?", CR, 860, 80, GOLD), P(81.55, "3d/lightning-gold.png", CR + 400, 840, 150)]),
    # --- 3. les Flammes ---
    (83.40, 94.05, "flammes-trophee.jpg", [C("flammes-trophee.jpg", CL, 540, 470),
        X(83.5, "3 MOIS APRÈS LE ZÉNITH", CR, 230, 50, WHT, "box"), X(85.5, "LES FLAMMES", CR, 380, 130, GOLD, "type"),
        X(87.9, "MUSIQUE AFRICAINE", CR, 540, 66, WHT), X(89.0, "OU D'INSPIRATION AFRICAINE", CR, 630, 50, WHT),
        X(90.8, "4E ÉDITION · PARIS", CR, 760, 56, WHT, "box"), P(85.5, "3d/lightning-gold.png", CR + 420, 360, 170)]),
    (94.05, 113.40, "grid", [X(94.2, "LE 1ER ARTISTE AFRICAIN", 960, 170, 96, YEL), X(95.5, "À REMPORTER CETTE FLAMME", 960, 290, 70, WHT),
        X(99.24, "FALLY IPUPA : UN TITRE HONORIFIQUE", 960, 450, 60, WHT, "box"), X(104.84, "SANS VOTE", 960, 550, 56, WHT),
        X(106.76, "HIMRA : LE VOTE + LE JURY", 960, 700, 86, GOLD), E(109.2, "🏆", 960, 880, 150)]),
    (113.40, 124.90, "grid", [X(113.5, "UNE CATÉGORIE COSTAUD", 960, 170, 96, WHT),
        X(T("asake"), "ASAKE", 360, 420, 66, WHT, "box"), X(T("fali", 116), "FALLY IPUPA", 760, 420, 66, WHT, "box"),
        X(T("chacola"), "TIAKOLA", 1160, 420, 66, WHT, "box"), X(T("chili"), "CHILLY", 1560, 420, 66, WHT, "box"),
        X(119.9, "ET C'EST HIMRA", 960, 620, 110, GOLD), X(121.5, "QUI GAGNE AVEC « NUMBER ONE »", 960, 760, 60, YEL),
        P(119.9, "3d/lightning-gold.png", 300, 640, 180), P(119.9, "3d/lightning-gold.png", 1620, 640, 180)]),
    # --- 4. Sorry I'm Bad ---
    (124.90, 140.50, "sorry-im-bad.jpg", [C("sorry-im-bad.jpg", CL, 540, 640, out=134.1),
        V("himra-epic-records-promo-16x9.mp4", 134.1, CL, 540, 820, ss=33.5, gain=0.12),
        X(124.95, "29 MAI 2026", CR, 230, 84, YEL), X(126.4, "SORRY I'M BAD", CR, 370, 100, WHT, "type"),
        Nn(128.4, 130.4, 17, CR, 510, 100, GOLD, " TITRES"), X(131.43, "UN CHANGEMENT DE DIMENSION", CR, 650, 52, WHT, "box"),
        X(134.15, "SIGNÉ CHEZ EPIC RECORDS FRANCE", CR, 780, 50, GOLD), X(135.9, "LABEL DU GROUPE SONY", CR, 870, 44, WHT, "box")]),
    (140.50, 157.80, "sorry-im-bad.jpg", [X(138.5, "LES INVITÉS", 960, 75, 70, YEL),
        C("gazo.jpg", 240, 320, 270, T("gaso"), out=151.8), C("leto.jpg", 600, 320, 270, T("leto"), out=151.8),
        C("zlatan.jpg", 960, 320, 270, T("zlatan", 140), out=151.8), C("babydaiz.jpg", 1320, 320, 270, T("zlatan", 140) + 0.35, out=151.8),
        C("elgrande-toto.jpg", 1680, 320, 270, T("grand", 140), out=151.8),
        C("la-fouine.jpg", 420, 700, 270, T("fouine", 140), out=151.8), C("enfant-noir.jpg", 780, 700, 270, T("enfant"), out=151.8),
        C("philipayne.jpg", 1140, 700, 270, T("philippaine"), out=151.8), C("m24.jpg", 1500, 700, 270, T("m24"), out=151.8),
        X(T("gaso"), "GAZO", 240, 495, 40, WHT, out=151.8), X(T("leto"), "LETO", 600, 495, 40, WHT, out=151.8),
        X(T("zlatan", 140), "ZLATAN", 960, 495, 40, WHT, out=151.8), X(T("zlatan", 140) + 0.35, "BABYDAIZ", 1320, 495, 40, WHT, out=151.8),
        X(T("grand", 140), "ELGRANDE TOTO", 1680, 495, 40, WHT, out=151.8),
        X(T("fouine", 140), "LA FOUINE", 420, 875, 40, WHT, out=151.8), X(T("enfant"), "ENFANT NOIR", 780, 875, 40, WHT, out=151.8),
        X(T("philippaine"), "PHILIPAYNE", 1140, 875, 40, WHT, out=151.8), X(T("m24"), "M24 · LONDRES", 1500, 875, 40, WHT, out=151.8),
        X(T("wilfrid"), "UN TITRE « WILFRIED ZAHA »", 960, 420, 90, GOLD), X(T("footballeurs"), "EN HOMMAGE AUX FOOTBALLEURS IVOIRIENS", 960, 560, 50, WHT, "box"),
        E(T("footballeurs"), "⚽", 760, 720, 110), E(T("footballeurs"), "🇨🇮", 1160, 720, 110)]),
    # --- 5. les chiffres ---
    (157.80, 184.50, "sorry-im-bad.jpg", [V("himra-clip-sorry-im-bad-16x9.mp4", None, CL, 540, 820, ss=0.5, out=170.0, credit="SOURCE : TIKTOK @MACHETTEHIMRA"),
        V("himra-bara-bara-teaser-16x9.mp4", 170.0, CL, 540, 820, ss=3.0, credit="SOURCE : TIKTOK @MACHETTEHIMRA"),
        X(157.84, "LES CHIFFRES SUIVENT", CR, 160, 70, YEL), X(159.36, "TOP FRANCE · APPLE MUSIC", CR, 280, 56, WHT),
        X(164.56, "EN MÊME TEMPS QUE BOOBA", CR, 410, 66, RED), X(167.52, "« BLANCO NEMESIS »", CR, 510, 52, WHT, "box"),
        X(175.10, "GRANDIOSE", CR, 630, 90, GOLD),
        Nn(T("plus", 176), T("millions", 180), 76000000, CR, 780, 96, GRN), X(T("millions", 180), "ÉCOUTES SPOTIFY · EN MOINS D'1 AN", CR, 890, 44, WHT, "box"),
        P(T("plus", 176), "3d/money-stack-gold.png", CR + 400, 760, 200)]),
    # --- 6. les collabs ---
    (184.50, 195.00, "grid", [X(184.6, "L'ÉTÉ DES COLLABS", 960, 120, 96, YEL),
        C("kodes-himra-wawa.jpg", 520, 560, 560, 190.4), C("kodes.jpg", 200, 820, 220, T("codes")), X(190.4, "« WAWA » · KODES", 520, 920, 56, WHT, "box"),
        C("dopelym.jpg", 1400, 560, 560, T("doplyme")), X(T("amargedon"), "« ARMAGEDDON » · DOPELYM", 1400, 920, 52, WHT, "box")]),
    (195.00, 217.85, "nouchi-trap-asap-jo.jpg", [C("nouchi-trap-asap-jo.jpg", CL, 540, 780),
        X(196.5, "AVEC ASAP JO", CR + 80, 250, 84, WHT), X(T("birdman"), "« BIRDMAN & WEEZY »", CR + 80, 380, 66, YEL),
        X(T("nouchitrap"), "NOUCHI TRAP VOL. 1", CR + 80, 500, 60, WHT, "box"), X(T("streamé"), "LE SON LE PLUS STREAMÉ", CR + 80, 630, 54, GOLD),
        X(212.5, "ASAP JO : SIGNÉ CHEZ 1X", CR + 80, 780, 54, WHT, "box")]),
    # --- 7. les coups durs ---
    (217.85, 233.70, "grid", [X(217.9, "SEPTEMBRE 2026", 960, 160, 84, YEL), X(219.5, "2 DATES ANNULÉES", 960, 300, 110, RED),
        X(221.6, "LUXEMBOURG", 640, 470, 66, WHT, "box"), E(221.6, "🇱🇺", 640, 580, 90), X(223.5, "GENÈVE", 1280, 470, 66, WHT, "box"), E(223.5, "🇨🇭", 1280, 580, 90),
        X(225.8, "JUIN : LES ÉTATS-UNIS", 960, 740, 70, WHT), X(T("reportées"), "REPORTÉ À AVRIL 2027", 960, 870, 76, RED, "box"), E(225.8, "🇺🇸", 1400, 740, 80)]),
    # --- 8. la boxe ---
    (233.70, 241.50, "grid", [X(233.8, "12 OCTOBRE", 960, 180, 90, YEL), X(234.6, "COUP DE THÉÂTRE", 960, 320, 120, RED),
        X(235.8, "IL INTERPELLE LE MINISTÈRE DES SPORTS", 960, 500, 56, WHT, "box"), X(238.3, "ET LA FÉDÉRATION DE BOXE", 960, 600, 56, WHT, "box"),
        X(240.36, "IL VEUT UN COMBAT", 960, 760, 90, GOLD), E(240.36, "🥊", 960, 910, 140)]),
    (241.50, 261.80, "affiche-boxe-5-dec.jpg", [C("affiche-boxe-5-dec.jpg", CL, 540, 660),
        X(241.6, "C'EST OFFICIEL", CR, 200, 90, YEL), X(242.6, "SAMEDI 5 DÉCEMBRE", CR, 320, 70, WHT),
        X(244.0, "PALAIS DES SPORTS DE TREICHVILLE", CR, 420, 44, WHT, "box"), X(T("liselli"), "VS MICHELE PAOLICELLI", CR, 550, 62, RED),
        E(T("liselli"), "🇮🇹", CR + 400, 550, 70), X(248.72, "19 ANS · BOXEUR ITALIEN", CR, 660, 52, WHT, "box"),
        X(257.53, "UN RAPPEUR FACE À UN VRAI BOXEUR", CR, 800, 46, GOLD), X(259.8, "3 SEMAINES AVANT EBIMPÉ", CR, 900, 50, RED, "box")]),
    (261.80, 284.80, "snap-sans-locks.jpg", [C("snap-sans-locks.jpg", CL, 540, 470),
        X(261.93, "IL S'EST COUPÉ LES LOCKS", CR, 220, 72, RED), X(266.49, "LA POLÉMIQUE", CR, 350, 80, WHT),
        X(268.5, "DES ULTRAS L'ONT SUIVI", CR, 470, 56, WHT, "box"), E(268.5, "✂️", CR + 330, 470, 90),
        X(277.61, "CRÂNE RASÉ", CR, 610, 84, YEL), X(279.85, "EN MODE TUPAC", CR, 730, 80, GOLD),
        X(281.53, "UNE IMAGE PLUS AGRESSIVE", CR, 850, 50, WHT, "box")]),
    # --- 9. les récompenses ---
    (284.80, 303.00, "grid", [X(284.9, "3 PRIX", 960, 170, 140, GOLD), E(284.9, "🏆", 1340, 170, 120),
        X(287.49, "ARAWO AMBASSADE AWARDS", 960, 330, 76, WHT), X(289.5, "MEILLEUR ARTISTE DE L'ANNÉE", 960, 460, 64, YEL),
        X(291.5, "AFRIQUE FRANCOPHONE", 960, 560, 56, WHT, "box"), X(293.65, "NOMINÉ AUX PRIMUD", 960, 720, 76, WHT),
        X(298.0, "DIDI B : ABSENT DE CETTE ÉDITION", 960, 870, 54, RED, "box")]),
    # --- 10. Nouveau Boss & Ebimpé ---
    (303.00, 323.85, "nouveau-boss.jpg", [C("nouveau-boss.jpg", 960, 430, 1500, out=310.7),
        X(306.46, "CE N'EST PAS UNE UTOPIE", 960, 830, 56, WHT, "box", out=310.7), X(308.6, "IL SORTIRA", 960, 950, 90, GOLD, out=310.7),
        C("affiche-ebimpe-26-dec.jpg", CL, 540, 520, 310.8), X(310.8, "MA THÉORIE :", CR, 600, 60, WHT),
        X(312.3, "UNE RÉÉDITION DE SORRY I'M BAD", CR, 700, 44, WHT, "box"), X(315.6, "AVANT EBIMPÉ", CR, 800, 70, RED),
        Nn(320.6, 321.9, 60000, CR, 930, 80, GRN, " PLACES")]),
    (323.85, 366.80, "grid", [X(323.9, "HIMRA EST CHAUD", 960, 150, 100, RED), E(323.9, "🔥", 1420, 150, 110),
        X(326.0, "IL FAUT BATTRE LE FER TANT QU'IL EST CHAUD", 960, 280, 52, WHT, "box"), X(329.9, "LE BON MOMENT POUR EBIMPÉ", 960, 390, 70, YEL),
        X(334.85, "ET EN 2027 ?", 960, 530, 100, GOLD), X(339.5, "DE NOUVEAUX PROJETS", 600, 670, 52, WHT, "box"),
        X(342.5, "UNE ADIDAS ARENA ?", 1320, 670, 52, WHT, "box"), X(347.0, "VOIRE L'ACCOR ARENA ?", 960, 790, 84, RED),
        X(358.0, "AVEC LUI, TOUT EST POSSIBLE", 960, 920, 56, WHT, "box", out=361.7), X(361.77, "LE DÉFI DACHIBA", 960, 920, 70, GOLD, "box")]),
    # --- bilan ---
    (366.80, 385.10, "grid", [X(366.81, "LE BILAN : 11 MOIS", 960, 120, 100, YEL),
        X(368.9, "ZÉNITH DE PARIS", 600, 280, 58, GRN), X(370.6, "SINGLE D'OR SNEP", 600, 390, 58, GRN), X(372.2, "TROPHÉE AUX FLAMMES", 600, 500, 58, GRN),
        X(374.3, "ALBUM DANS LE TOP FRANCE", 600, 610, 50, GRN), X(376.6, "SIGNATURE CHEZ EPIC RECORDS", 600, 720, 48, GRN),
        X(379.8, "DATES ANNULÉES", 1380, 400, 62, RED), X(381.6, "EBIMPÉ REPORTÉ PLUSIEURS FOIS", 1380, 520, 44, RED, "box")]),
    (385.10, 399.90, "grid", [X(385.2, "IL RESTE 3 RENDEZ-VOUS", 960, 120, 100, YEL),
        C("affiche-boxe-5-dec.jpg", 400, 520, 380, 388.8), X(388.8, "5 DÉC. · LA BOXE", 400, 920, 48, WHT, "box"),
        C("nouveau-boss.jpg", 960, 520, 560, T("nouveau", 389)), X(T("nouveau", 389), "LE PROJET", 960, 920, 48, WHT, "box"),
        C("affiche-ebimpe-26-dec.jpg", 1520, 520, 330, 393.75), X(393.75, "26 DÉC. · EBIMPÉ", 1520, 920, 48, WHT, "box")]),
    # --- question ---
    (399.90, 413.60, "grid", [X(399.94, "VA-T-IL REMPLIR EBIMPÉ ?", 960, 230, 100, YEL), X(404.66, "VA-T-IL GAGNER SON COMBAT ?", 960, 400, 86, WHT),
        E(404.66, "🥊", 960, 540, 120), X(406.82, "DITES-LE EN COMMENTAIRE", 960, 700, 84, YEL), E(406.82, "💬", 1500, 700, 100),
        X(409.38, "LIKE · COMMENTE · PARTAGE · ABONNE-TOI", 960, 880, 50, WHT, "box")]),
    (413.60, END + 1, "end", []),
]
CHAPTERS = [  # (source time, top, bottom) — 3D title over the first seconds of each chapter; YouTube chapters list
    (0.0, "INTRO", ""), (18.45, "CHAPITRE 1", "LE ZÉNITH"), (62.50, "CHAPITRE 2", "LE SINGLE D'OR"), (83.40, "CHAPITRE 3", "LES FLAMMES"),
    (124.90, "CHAPITRE 4", "SORRY I'M BAD"), (157.80, "CHAPITRE 5", "LES CHIFFRES"), (184.50, "CHAPITRE 6", "LES COLLABS"),
    (217.85, "CHAPITRE 7", "LES COUPS DURS"), (233.70, "CHAPITRE 8", "LA BOXE"), (284.80, "CHAPITRE 9", "LES RÉCOMPENSES"),
    (303.00, "CHAPITRE 10", "NOUVEAU BOSS"), (366.80, "LE BILAN", ""), (399.90, "ET VOUS ?", "")]
HOOK = (R(T("tout", 10)), R(13.6))
hook_img = block("TOUT ÇA EN|UNE SEULE ANNÉE", "ET CE N'EST|PAS FINI", 1400, 780)
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
place(hit, HOOK[0], 0.5); place(riser, HOOK[0] - 2.95, 0.4); place(riser, R(234.6) - 2.95, 0.45)   # « coup de théâtre »
place(crowd, R(119.9), 0.3); place(uhh, R(219.5) + 0.3, 0.2)                                   # Flamme won; dates cancelled
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
