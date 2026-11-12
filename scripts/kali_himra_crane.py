"""Kali Muscle-style edit (« Ils se rasent la tête ! » : rumeur Himra boule à zéro, les ultras font la trend), same engine as
vlog_kali.py; upright 1080x1920 phone source. His Snapchat story (locks in a bag, circled with his brush-circle overlay),
the TikTok trend clip (watermark blurred, @esthayaourtchou credited), the three options, varied transitions."""
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
END = 45.65
ANTON = os.path.expanduser("~/.fonts/anton-latin-400.ttf")

# ---------- transcript (Parakeet on short windows) + fixes ----------
words = json.load(open(f"{WORK}/w.json"))
def near(t): return min(words, key=lambda w: abs(w["s"] - t))
def ren(t, txt): near(t)["w"] = txt
def rm(t):
    global words; x = near(t); words = [w for w in words if w is not x]
def add(t, txt): words.append({"w": txt, "s": t}); words.sort(key=lambda w: w["s"])
ren(7.9, "Himra"); ren(9.3, "boule à zéro."); ren(19.1, "locks"); ren(25.0, "trends"); ren(34.6, "Himra"); ren(38.2, "coiffure")
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP_SRC = [(12.75, 13.55), (31.65, 34.05), (44.5, END)]   # unclear words / comment call shown as a screen

# ---------- jump cuts ----------
DROP = [(20.62, 21.05),   # second « tout rasé »
        (28.33, 28.95),   # second « ça me fait rire »
        (29.15, 31.65),   # « C'est que les gens… »
        (35.05, 36.15),   # « là il doit se… » (false start)
        (37.25, 37.65)]   # « son » before « sa nouvelle coiffure »
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
# blanks and « euh » between words (fillers are not transcribed): cut the gap, 0.06 s kept after / 0.05 s before
for a_, b_ in zip(words, words[1:]):
    w_ = a_["w"].strip(",.?!…")
    if any(ch.isdigit() for ch in w_) or (len(w_) > 1 and w_.isupper()): continue   # numbers and acronyms (GTA = « G-T-A ») last longer than their letters
    e_ = a_["s"] + 0.10 + 0.06 * len(a_["w"].strip(",.?!…"))
    if b_["s"] - e_ >= 0.25 and a_["s"] < 44.4: keep[int((e_ + 0.06) / 0.02):int((b_["s"] - 0.05) / 0.02)] = False
# breaths between sentences: quieter than the voice and without low frequencies (inhale noise). Between two words,
# find where the voice of the first word really ends and where the next word really starts, and cut what lies between
# when it holds a breath (or follows the end of a sentence).
fr_ = au[:len(db) * hop].reshape(len(db), hop) * np.hanning(hop)
sp_ = np.abs(np.fft.rfft(fr_, axis=1)) ** 2; fq_ = np.fft.rfftfreq(hop, 1 / sr)
lfr = sp_[:, (fq_ > 80) & (fq_ < 1000)].sum(1) / (sp_.sum(1) + 1e-12)
MED = np.median(db)
voiced = (db > MED - 8) & (lfr > 0.6)
loud = db > MED - 6
BREATHS = []
for a_, b_ in zip(words, words[1:]):
    if a_["s"] >= 44.4: break
    i0, i1 = int(a_["s"] / 0.02), int(b_["s"] / 0.02)
    if i1 - i0 < 6: continue
    v = np.nonzero(voiced[i0:i1])[0]
    ve = i0 + (v[-1] + 1 if len(v) else 3)                     # end of the first word's voice
    on = i1
    while on > ve and loud[on - 1]: on -= 1                    # the next word's onset (consonants included)
    c0, c1 = ve + 4, on - 3                                    # keep 0.08 s of tail, 0.06 s before the onset
    if c1 - c0 < 5: continue                                   # under 0.1 s: leave it
    seg = slice(c0, c1)
    breath = np.sum((db[seg] > MED - 22) & (lfr[seg] < 0.65)) >= 4
    if breath or a_["w"][-1] in ",.?!…":
        keep[c0:c1] = False; BREATHS.append((round(c0 * 0.02, 2), round(c1 * 0.02, 2)))
print(f"{len(BREATHS)} breaths / pauses cut, {sum(b - a for a, b in BREATHS):.1f}s", flush=True)
keep[int(44.4 / 0.02):] = True                       # comment call + sign-off whole
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
SW, SH = 1080, 1920

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
from kali_fx import bg_for
def card_set(names, width, rim): return [cover_card(f"{WORK}/{n}.jpg", width, rim) for n in names]
VOIT = cover_card(f"{WORK}/himra_voiture.jpg", 720, (255, 80, 60))
SAC = cover_card(f"{WORK}/snap_sac.jpg", 640, (255, 255, 255))
CR1 = cover_card(f"{WORK}/snap_crane.jpg", 380, (255, 255, 255))
CR2 = cover_card(f"{WORK}/crane2.jpg", 440, (255, 255, 255))
WM = ("split[a][b];[b]crop=170:120:0:450,boxblur=14[l];[a][l]overlay=0:450[c];"
      "[c]split[d][e];[e]crop=180:130:396:750,boxblur=14[r];[d][r]overlay=396:750")
def clip_frames(path, t0, dur, vf=""):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(dur), "-i", path, "-an", "-filter_complex",
                          (vf + "," if vf else "") + "fps=30,scale=360:640,eq=contrast=1.05:saturation=1.08",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 640, 360, 3)
TREND1 = clip_frames(f"{WORK}/trend.mp4", 0.0, 4.0, WM)
TREND2 = clip_frames(f"{WORK}/trend.mp4", 9.0, 4.5, WM)
def play(frames, k, dim=0.85):
    fr = frames[min(int(k * FPS), len(frames) - 1)]
    return cv2.resize(fr, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255 * dim
# his brush-circle overlay (white stroke on black, 35-frame loop), screen-blended at half size
_bc = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "overlays", "brush-circle.mov"), "-vf", "fps=30,scale=880:1564",
                      "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
BRUSH = np.frombuffer(_bc, np.uint8).reshape(-1, 1564, 880, 3)
def screen_at(img, fr, cx, cy):
    h, w = fr.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    src = fr[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32) / 255
    img[ya:yb, xa:xb] = 1 - (1 - img[ya:yb, xa:xb]) * (1 - src)
def flag(kind):
    w, h = 300, 200; f = np.zeros((h, w, 3), np.float32)
    if kind == "ci":
        f[:, :100] = (247, 127, 0); f[:, 100:200] = (255, 255, 255); f[:, 200:] = (0, 158, 96)
    elif kind == "ng":
        f[:, :100] = (0, 135, 81); f[:, 100:200] = (255, 255, 255); f[:, 200:] = (0, 135, 81)
    elif kind == "be":
        f[:, :100] = (20, 20, 20); f[:, 100:200] = (253, 218, 36); f[:, 200:] = (239, 51, 64)
    elif kind == "ch":
        w = h = 220; f = np.zeros((h, w, 3), np.float32); f[:] = (218, 41, 28)
        f[46:174, 88:132] = (255, 255, 255); f[88:132, 46:174] = (255, 255, 255)
    else:
        for r in range(13): f[r * h // 13:(r + 1) * h // 13] = (178, 34, 52) if r % 2 == 0 else (255, 255, 255)
        f[:7 * h // 13, :120] = (60, 59, 110)
        for r in range(5):
            for q in range(6): cv2.circle(f, (10 + q * 20, 11 + r * 21), 4, (255, 255, 255), -1, cv2.LINE_AA)
    rgba = np.dstack([f / 255, np.ones(f.shape[:2], np.float32)])
    return glow_rgba(rgba, (255, 255, 255), 12, 1.2)
FLAG_CI, FLAG_NG, FLAG_BE, FLAG_CH, FLAG_US = flag("ci"), flag("ng"), flag("be"), flag("ch"), flag("us")
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
CARDS = [  # start, end, top, bottom, kind, centre y
    (0.0, R(3.20), "ILS SE RASENT", "LA TÊTE !", "hook", 520),
    (R(44.40), DUR, "LE BIG", "VASS", "end", 1370),
]
card_img = [block(c[2], c[3], 1040, {"hook": 760, "end": 700, "over": 700}.get(c[4], 1000)) for c in CARDS]
def in_card(t): return any(c[0] <= t < c[1] for c in CARDS)

# ---------- scenes: (start, end, background, captions?) ; everything else is the face-cam ----------
SCENES = [
    (0.0, R(3.20), "hook", False),
    (R(3.20), R(6.55), "ultras", False),
    (R(6.55), R(10.15), "rumeur", False),
    (R(10.15), R(17.35), "sac", False),
    (R(17.35), R(23.30), "options", False),
    (R(23.30), R(27.00), "trend", False),
    (R(31.65), R(34.05), "comment", False),
    (R(34.05), R(38.90), "montre", False),
]
def scene_at(t):
    for s in SCENES:
        if s[0] <= t < s[1]: return s
    return None
TYPES = {"rumeur": (7.0, "SELON LES RUMEURS", 18), "comment": (31.7, "DONNEZ VOTRE AVIS", 20)}
def tw(img, t, name, size, col, y):
    s0, txt, cps = TYPES[name]; typewriter(img, t, R(s0), txt, size, col, y, cps)
OVER = [
    (R(27.00), R(29.15), 0.15, True,
     lambda img, t: stack(img, t, [(R(27.2), "ÇA ME FAIT", WHT), (R(27.6), "RIRE", YEL)], 200, 600, 240)),
    (R(41.90), R(43.60), 0.45, False,
     lambda img, t: stack(img, t, [(R(42.7), "UN PEU DE", WHT), (R(43.1), "CHEVEUX ?", YEL)], 180, 600, 220)),
]
def over_at(t): return [o for o in OVER if o[0] <= t < o[1]]

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def settle(k): return (1.1 - 0.1 * min(k / 0.3, 1) ** 0.4) * (1 + 0.03 * min(k, 1.5))
def pop_at(img, t, t0, im, x, y, sc=1.0):
    if t >= R(t0): paste(img, im, x, y, sc * popk(t, R(t0)))
def credit(img, txt):
    im, _ = neon(txt, 34, WHT); paste(img, im, W / 2, 1860, 1.0, 0.85)
def draw_scene(name, t, k):
    if name in ("ultras", "trend"):
        img = play(TREND1 if name == "ultras" else TREND2, k, 0.8)
        if name == "ultras":
            stack(img, t, [(R(3.2), "LES ULTRAS", YEL)], 170, 300, 0)
            stack(img, t, [(R(5.1), "SE RASENT LA TÊTE", WHT)], 120, 1600, 0)
        else:
            stack(img, t, [(R(23.4), "LA TREND", YEL)], 170, 300, 0)
            stack(img, t, [(R(25.9), "ILS SE RASENT LE CRÂNE", WHT)], 100, 1600, 0)
        credit(img, "SOURCE TIKTOK : @ESTHAYAOURTCHOU")
        return img
    img = bg_for([s[2] for s in SCENES].index(name), t)
    if name == "hook":
        paste(img, VOIT, W / 2, 1300, settle(k))
    elif name == "rumeur":
        tw(img, t, "rumeur", 110, WHT, 300)
        paste(img, VOIT, W / 2, 1000, 0.75 * settle(k))
        stack(img, t, [(R(7.9), "HIMRA", YEL), (R(9.2), "BOULE À ZÉRO ?", RED)], 150, 1550, 180)
    elif name == "sac":
        paste(img, SAC, W / 2, 1060, settle(min(k, 1.5)))
        stack(img, t, [(R(12.5), "CETTE PHOTO", WHT)], 120, 260, 0)
        if t >= R(14.1):
            k2 = min((t - R(14.1)) / 0.35, 1.0)                          # neon circle drawn around the bag
            lay = np.zeros((H, W), np.float32)
            cv2.ellipse(lay, (615, 1228), (215, 175), -20, -90, -90 + 360 * k2, 1.0, 14, cv2.LINE_AA)
            g = np.clip(cv2.GaussianBlur(lay, (0, 0), 14) * 1.8, 0, 1)[..., None]
            a_ = np.maximum(g, lay[..., None])                               # red glow (BGR) with a white core
            img[:] = img * (1 - a_) + np.clip(np.array([0.25, 0.2, 1.0]) * g + lay[..., None], 0, 1) * a_
            stack(img, t, [(R(14.1), "SES LOCKS DANS UN SAC", YEL)], 90, 400, 0)
        stack(img, t, [(R(16.3), "ON N'A PAS VU SON CRÂNE", RED)], 85, 1780, 0)
    elif name == "options":
        stack(img, t, [(R(17.4), "ON SAIT PAS SI…", WHT)], 120, 260, 0)
        stack(img, t, [(R(18.6), "RÉDUIT ?", GRN), (R(20.2), "TOUT RASÉ ?", RED), (R(21.9), "DÉGRADÉ ?", (120, 190, 255))], 150, 480, 190)
        pop_at(img, t, 20.2, CR1, 310, 1350); pop_at(img, t, 20.4, CR2, 790, 1350)
    elif name == "comment":
        tw(img, t, "comment", 110, WHT, 760)
        stack(img, t, [(R(32.6), "EN COMMENTAIRE", YEL)], 150, 960, 0)
    elif name == "montre":
        paste(img, VOIT, W / 2, 1100, 0.85 * settle(k))
        stack(img, t, [(R(34.1), "D'AILLEURS", WHT), (R(34.6), "HIMRA", YEL)], 130, 250, 160)
        stack(img, t, [(R(36.6), "MONTRE-NOUS", WHT), (R(37.9), "TA NOUVELLE COIFFURE", YEL)], 110, 1660, 140)
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
EMPH_RED = {"raser", "rasé", "rasé,", "crâne", "zéro.", "rire", "rire."}
EMPH_WHITE = {"himra", "ultras", "locks", "dégradé", "trends", "coiffure"}
for w in words:
    if key(w) in EMPH_RED: z += punch(w["s"], 0.1)
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
place(hit, R(9.2), 0.45); place(hit, R(20.2), 0.4)
for s0, txt, cps in TYPES.values():
    for j, ch in enumerate(txt):
        if ch != " ": place(click, R(s0) + j / cps, 0.25)
place(riser, R(9.2) - RISER_PEAK, 0.5)
place(whoosh, R(14.1) - 0.1, 0.25)
BURN_PEAK = 11 / FPS
BURN_AT = [R(6.55)]
TRANS = [(R(3.20), "red-flash-39.mp4", 17 / 30, True), (R(10.15), "light-flash-23.mp4", 5 / 23.976, False),
         (R(17.35), "bw-flash-33.mp4", 4 / 23.976, False), (R(23.30), "red-flash-39.mp4", 17 / 30, True)]
for b_ in BURN_AT: place(burn_snd, b_ - BURN_PEAK, 0.6)
TRF = {}
for _, fn, pk, snd in TRANS:
    if fn not in TRF:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions", fn), "-vf", f"fps=30,scale={W}:{H}",
                              "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
        TRF[fn] = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    if snd: place(load(os.path.join(LIB, "transitions", fn)), _ - pk, 0.5)
    else: place(whoosh, _ - 0.2, 0.3)
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
    for b_, fn, pk, _s in TRANS:
        k = int(round((t - (b_ - pk)) * FPS))
        if 0 <= k < len(TRF[fn]): img = 1 - (1 - img) * (1 - TRF[fn][k].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if i % 300 == 0: print(f"frame {i}/{N}", flush=True)
enc.stdin.close(); enc.wait()
dec.stdout.close(); dec.kill(); dec.wait()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", CUT, "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]highpass=f=70,volume=4dB,acompressor=threshold=-22dB:ratio=4:attack=5:release=90:makeup=3dB,loudnorm=I=-14:TP=-1.5:LRA=7,"
    "aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.75:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, len(SHOTS), "shots", flush=True)
