"""Kali Muscle-style edit (« Fela Kuti, 1er artiste africain au Rock and Roll Hall of Fame »), same engine as vlog_kali.py;
upright 720x1280 60 fps phone source, voice kept as recorded. Fela photos, the Hall of Fame building, inductee grid (Jay-Z,
2Pac, N.W.A, then Queen Latifah, Wu-Tang Clan, Phil Collins), 3D cards, 3D gold PNGs, varied transitions."""
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
END = 102.68
ANTON = os.path.expanduser("~/.fonts/anton-latin-400.ttf")

# ---------- transcript (Parakeet on short windows) + fixes ----------
words = json.load(open(f"{WORK}/w.json"))
def near(t): return min(words, key=lambda w: abs(w["s"] - t))
def ren(t, txt): near(t)["w"] = txt
def rm(t):
    global words; x = near(t); words = [w for w in words if w is not x]
def add(t, txt): words.append({"w": txt, "s": t}); words.sort(key=lambda w: w["s"])
ren(4.58, "Fela Kuti"); ren(8.50, "cérémonie"); ren(9.40, "du"); ren(9.48, "Rock"); ren(9.80, "and Roll"); ren(9.96, "Hall of"); ren(10.28, "Fame")
ren(15.50, "Rock and Roll"); ren(15.82, "Hall"); ren(16.14, "of"); ren(16.30, "Fame,"); ren(17.42, "c'est"); ren(17.66, "un musée,")
ren(22.66, "intronisés,"); ren(24.66, "Jay-Z,"); ren(25.46, "Tupac,"); ren(26.74, "N.W.A."); rm(27.16)
ren(28.52, "a eu"); ren(28.76, "Queen"); ren(29.08, "Latifah,"); ren(29.64, "a eu"); ren(29.96, "Wu-Tang"); ren(30.36, "Clan,")
ren(30.92, "Phil"); ren(31.16, "Collins,"); ren(32.70, "Fela"); ren(32.94, "Kuti."); rm(33.18)
ren(37.60, "Fela"); ren(37.76, "Kuti,"); rm(37.92); ren(45.08, "politiques,"); ren(49.08, "avait"); ren(49.58, "au Nigeria,")
ren(64.04, "1997,"); ren(69.74, "est"); ren(69.90, "intronisé"); ren(77.22, "Seun"); ren(77.62, "Kuti"); ren(79.22, "Kuti,")
ren(92.40, "Burna Boy,"); ren(93.20, "Wizkid,"); ren(93.76, "Asake,"); ren(94.66, "Davido")
ren(101.56, "le Big"); ren(101.72, "Vass"); ren(102.04, "pour"); ren(102.12, "vous"); ren(102.28, "servir.")
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP_SRC = [(13.70, 14.40), (36.40, 37.55), (50.90, 51.30), (98.30, 99.70)]   # unclear words: audio kept, no caption

# ---------- jump cuts ----------
DROP = [(2.30, 2.98),     # second « c'était incroyable »
        (85.60, 90.30)]   # first « peut-être une vidéo détaillée sur lui » (said again at the end)
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
    if b_["s"] - e_ >= 0.25 and a_["s"] < 99.6: keep[int((e_ + 0.06) / 0.02):int((b_["s"] - 0.05) / 0.02)] = False
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
    if a_["s"] >= 99.6: break
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
keep[int(99.6 / 0.02):] = True                       # comment call + sign-off whole
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
SW, SH = 720, 1280

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
FELA1 = cover_card(f"{WORK}/p1.jpg", 720, (255, 190, 60)); FELA2 = cover_card(f"{WORK}/p2.jpg", 600, (255, 190, 60))
FELAS = cover_card(f"{WORK}/p1.jpg", 400, (255, 190, 60))
FELAS = cv2.resize(FELAS, None, fx=470 / max(FELAS.shape[:2]), fy=470 / max(FELAS.shape[:2]))
HALL = cover_card(f"{WORK}/p3.jpg", 960, (255, 255, 255)); HALLS = cover_card(f"{WORK}/p3.jpg", 760, (255, 255, 255))
IND = {k: cover_card(f"{WORK}/{f}", 300, c) for k, f, c in (("jay", "p4.jpg", (255, 255, 255)), ("pac", "p5.jpg", (255, 255, 255)),
       ("nwa", "p6.jpg", (255, 255, 255)), ("wu", "p7.jpg", (255, 222, 40)), ("phil", "p8.jpg", (255, 60, 60)), ("queen", "p9.jpg", (255, 190, 60)))}
def blur_boxes(boxes):
    """Blur only small watermark boxes (x, y, w, h) in the 576x1024 TikTok frame."""
    out, src = [], "[0:v]"
    for n, (x, y, w, h) in enumerate(boxes):
        out.append(f"{src}split[a{n}][b{n}];[b{n}]crop={w}:{h}:{x}:{y},boxblur=8[c{n}];[a{n}][c{n}]overlay={x}:{y}[o{n}]"); src = f"[o{n}]"
    return ";".join(out) + f";{src}"
def clip_frames(path, t0, dur, boxes):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(dur), "-i", path, "-an", "-filter_complex",
                          blur_boxes(boxes) + "fps=30,scale=360:640,eq=contrast=1.05:saturation=1.08", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 640, 360, 3)
WM_STD = [(0, 462, 165, 100), (412, 752, 164, 150)]          # TikTok logo + handle: left (early) and right (later)
C_LIVE = clip_frames(f"{WORK}/fc2.mp4", 6.0, 5.6, WM_STD)                                   # @rockhall: Fela on stage, blue trousers
C_STAGE = clip_frames(f"{WORK}/fc3.mp4", 2.0, 12.6, WM_STD + [(230, 705, 150, 95)])          # @9japr247: leopard shirt (+ « 9ja PR » logo)
C_SMOKE = clip_frames(f"{WORK}/fc1.mp4", 15.5, 5.0, WM_STD)                                 # @thegr8vibe: close-up with cigarette
C_BAND = clip_frames(f"{WORK}/fc1.mp4", 0.3, 6.6, WM_STD)                                   # @thegr8vibe: the band in yellow
CREDIT = {"live": "@ROCKHALL", "stage": "@9JAPR247", "smoke": "@THEGR8VIBE", "band": "@THEGR8VIBE"}
def play(frames, k, dim=0.82):
    fr = frames[min(int(k * FPS), len(frames) - 1)]
    return cv2.resize(fr, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255 * dim
def credit(img, key_):
    im, _ = neon(f"SOURCE TIKTOK : {CREDIT[key_]}", 34, WHT); paste(img, im, W / 2, 1860, 1.0, 0.85)
def fit(v, m=470):
    sc = m / max(v.shape[:2]); return cv2.resize(v, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
IND = {k: fit(v) for k, v in IND.items()}
BOLT = {c: rgba_file(os.path.join(LIB, "3d", f), 640) for c, f in (("gold", "lightning-gold.png"), ("heart", "heart-gold.png"), ("note", "music-note-gold.png"))}
def bolt(img, t, t0, col, x, y, sc=1.0):
    k = t - t0
    if 0 <= k < 1.2: paste(img, BOLT[col], x, y, sc * popk(t, t0) * (1 + 0.04 * k), min(k / 0.08, 1) * min((1.2 - k) / 0.2, 1))
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
    (0.0, R(2.30), "FELA KUTI", "AU ROCK|HALL OF FAME", "hook", 600),
    (R(38.90), R(42.20), "LE FONDATEUR", "DE L'AFROBEAT", "card", 960),
    (R(66.50), R(69.40), "30 ANS", "PLUS TARD", "card", 960),
    (R(99.60), DUR, "LE BIG", "VASS", "end", 1370),
]
card_img = [block(c[2], c[3], 1040, {"hook": 760, "end": 700, "over": 700}.get(c[4], 1000)) for c in CARDS]
def in_card(t): return any(c[0] <= t < c[1] for c in CARDS)

# ---------- scenes: (start, end, background, captions?) ; everything else is the face-cam ----------
SCENES = [
    (0.0, R(2.30), "hook", False),
    (R(4.40), R(9.30), "fela", False),
    (R(9.30), R(13.70), "hall", False),
    (R(23.10), R(28.00), "avant", False),
    (R(28.00), R(34.00), "2026", False),
    (R(42.20), R(54.00), "engage", False),
    (R(54.00), R(58.50), "legende", False),
    (R(63.30), R(66.50), "1997", False),
    (R(69.40), R(72.00), "intronise", False),
    (R(74.80), R(81.00), "fils", False),
    (R(90.30), R(95.60), "heritage", False),
]
def scene_at(t):
    for s in SCENES:
        if s[0] <= t < s[1]: return s
    return None
TYPES = {"1997": (64.04, "1997", 8)}
def tw(img, t, name, size, col, y):
    s0, txt, cps = TYPES[name]; typewriter(img, t, R(s0), txt, size, col, y, cps)
OVER = [
    (R(2.98), R(4.40), 0.45, False,
     lambda img, t: stack(img, t, [(R(3.04), "POUR CEUX QUI", WHT), (R(3.52), "NE SAVENT PAS", YEL)], 160, 580, 195)),
    (R(17.90), R(23.10), 0.45, False,
     lambda img, t: (stack(img, t, [(R(18.40), "UN PANTHÉON", YEL), (R(19.12), "DE LA MUSIQUE", WHT), (R(21.60), "QUE DES GRANDS", GOLD)], 150, 520, 185),
                     bolt(img, t, R(18.48), "note", 860, 330, 0.8))),
    (R(34.00), R(36.40), 0.15, True,
     lambda img, t: stack(img, t, [(R(34.78), "UN TRUC", WHT), (R(35.10), "DE OUF", RED)], 200, 600, 240)),
    (R(72.00), R(74.80), 0.45, False,
     lambda img, t: (stack(img, t, [(R(72.32), "ÇA FAIT", WHT), (R(72.96), "GRAVE PLAISIR", YEL)], 170, 600, 205), bolt(img, t, R(72.96), "heart", 860, 380, 0.7))),
    (R(81.00), R(85.60), 0.15, True,
     lambda img, t: stack(img, t, [(R(83.40), "GRANDIOSE", GOLD)], 220, 640, 0)),
]
def over_at(t): return [o for o in OVER if o[0] <= t < o[1]]

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def settle(k): return (1.1 - 0.1 * min(k / 0.3, 1) ** 0.4) * (1 + 0.03 * min(k, 1.5))
def tag(img, t, t0, im, lbl, x, y, col=WHT):
    if t >= R(t0):
        paste(img, im, x, y, popk(t, R(t0))); lb, _ = neon(lbl, 62, col); paste(img, lb, x, y + im.shape[0] / 2 - 6)
def draw_scene(name, t, k):
    if name == "fela":
        img = play(C_LIVE, k); credit(img, "live")
        stack(img, t, [(R(4.58), "FELA KUTI", GOLD), (R(6.18), "1ER ARTISTE AFRICAIN", WHT)], 120, 230, 145)
        stack(img, t, [(R(7.70), "INTRONISÉ", RED)], 150, 1680, 0)
        return img
    if name == "engage":
        img = play(C_STAGE, k); credit(img, "stage")
        stack(img, t, [(R(42.20), "CONNU POUR", WHT), (R(44.42), "SES ENGAGEMENTS", YEL), (R(45.08), "POLITIQUES", RED)], 100, 220, 120)
        if t >= R(49.58): paste(img, FLAG_NG, 220, 1600, popk(t, R(49.58)) * 0.8)
        cur = [x for x in ((48.04, "IL DÉNONÇAIT", WHT), (50.30, "LA CORRUPTION", RED), (51.42, "LA COLONISATION", RED)) if t >= R(x[0])]
        if cur: im, _ = neon(cur[-1][1], 100, cur[-1][2]); paste(img, im, W / 2 + 80, 1620, popk(t, R(cur[-1][0])))
        return img
    if name == "legende":
        img = play(C_SMOKE, k); credit(img, "smoke")
        stack(img, t, [(R(54.32), "DES ALLERS-RETOURS", WHT), (R(55.04), "EN PRISON", RED)], 110, 230, 135)
        stack(img, t, [(R(57.12), "SA LÉGENDE", GOLD)], 160, 1640, 0)
        return img
    if name == "fils":
        img = play(C_BAND, k); credit(img, "band")
        stack(img, t, [(R(74.85), "À LA CÉRÉMONIE", WHT), (R(77.22), "SEUN KUTI", GOLD), (R(78.58), "FEMI KUTI", GOLD)], 120, 220, 145)
        stack(img, t, [(R(76.90), "SES DEUX FILS, ARTISTES", WHT)], 85, 1680, 0)
        return img
    img = bg_for([s[2] for s in SCENES].index(name), t)
    if name == "hook":
        paste(img, FELA1, W / 2, 1280, settle(k)); bolt(img, t, 0.0, "gold", 870, 1400, 0.8)
    elif name == "fela":
        paste(img, FELA2, W / 2, 1120, settle(min(k, 1.5)))
        stack(img, t, [(R(4.58), "FELA KUTI", GOLD), (R(6.18), "1ER ARTISTE AFRICAIN", WHT)], 120, 230, 145)
        stack(img, t, [(R(7.70), "INTRONISÉ", RED)], 150, 1740, 0)
    elif name == "hall":
        paste(img, HALL, W / 2, 1000, settle(min(k, 1.5)))
        stack(img, t, [(R(9.48), "ROCK AND ROLL", YEL), (R(9.96), "HALL OF FAME", GOLD)], 130, 260, 160)
        stack(img, t, [(R(10.60), "AUX ÉTATS-UNIS", WHT)], 110, 1460, 0)
        if t >= R(10.76): paste(img, FLAG_US, W / 2, 1650, popk(t, R(10.76)))
    elif name == "avant":
        stack(img, t, [(R(23.22), "LES ANNÉES PRÉCÉDENTES", YEL)], 100, 200, 0)
        tag(img, t, 24.66, IND["jay"], "JAY-Z", 290, 720); tag(img, t, 25.46, IND["pac"], "2PAC", 790, 720)
        tag(img, t, 26.42, IND["nwa"], "N.W.A", 540, 1340)
    elif name == "2026":
        stack(img, t, [(R(28.04), "CETTE ANNÉE", GOLD)], 110, 200, 0)
        tag(img, t, 28.76, IND["queen"], "QUEEN LATIFAH", 290, 660); tag(img, t, 29.96, IND["wu"], "WU-TANG CLAN", 790, 660)
        tag(img, t, 30.92, IND["phil"], "PHIL COLLINS", 290, 1310); tag(img, t, 32.70, FELAS, "FELA KUTI", 790, 1310, GOLD)
        if t >= R(32.70): bolt(img, t, R(32.70), "gold", 960, 1000, 0.5)
    elif name == "engage":
        paste(img, FELA1, W / 2, 1150, 0.8 * settle(min(k, 1.5)))
        stack(img, t, [(R(42.20), "CONNU POUR", WHT), (R(44.42), "SES ENGAGEMENTS", YEL), (R(45.08), "POLITIQUES", RED)], 100, 220, 120)
        if t >= R(49.58): paste(img, FLAG_NG, 220, 1650, popk(t, R(49.58)) * 0.8)
        cur = [x for x in ((48.04, "IL DÉNONÇAIT", WHT), (50.30, "LA CORRUPTION", RED), (51.42, "LA COLONISATION", RED)) if t >= R(x[0])]
        if cur: im, _ = neon(cur[-1][1], 100, cur[-1][2]); paste(img, im, W / 2 + 80, 1680, popk(t, R(cur[-1][0])))
    elif name == "legende":
        paste(img, FELA2, W / 2, 1000, 0.85 * settle(min(k, 1.5)))
        stack(img, t, [(R(54.32), "DES ALLERS-RETOURS", WHT), (R(55.04), "EN PRISON", RED)], 110, 230, 135)
        stack(img, t, [(R(57.12), "SA LÉGENDE", GOLD)], 160, 1680, 0)
    elif name == "1997":
        tw(img, t, "1997", 300, WHT, 760)
        stack(img, t, [(R(65.00), "IL NOUS A QUITTÉS", RED)], 120, 1100, 0)
    elif name == "intronise":
        paste(img, HALLS, W / 2, 1000, settle(min(k, 1.5)))
        stack(img, t, [(R(69.42), "INTRONISÉ", GOLD), (R(70.70), "DANS CE PANTHÉON", WHT)], 120, 260, 150)
    elif name == "fils":
        paste(img, FELA1, W / 2, 1150, 0.75 * settle(min(k, 1.5)))
        stack(img, t, [(R(74.85), "À LA CÉRÉMONIE", WHT), (R(77.22), "SEUN KUTI", GOLD), (R(78.58), "FEMI KUTI", GOLD)], 120, 220, 145)
        stack(img, t, [(R(76.90), "SES DEUX FILS, ARTISTES", WHT)], 85, 1720, 0)
    elif name == "heritage":
        stack(img, t, [(R(90.32), "SANS LUI…", WHT)], 150, 330, 0)
        stack(img, t, [(R(92.40), "BURNA BOY", YEL), (R(93.20), "WIZKID", YEL), (R(93.76), "ASAKE", YEL), (R(94.66), "DAVIDO", YEL)], 150, 620, 190)
        stack(img, t, [(R(95.62), "NON NON NON !", RED)], 130, 1460, 0)
        bolt(img, t, R(92.40), "note", 880, 1580, 0.7)
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
EMPH_RED = {"incroyable,", "corruption,", "colonisation,", "prison.", "quittés.", "grandiose", "grandiose."}
EMPH_WHITE = {"fela", "kuti", "kuti,", "kuti.", "jay-z,", "tupac,", "n.w.a.", "queen", "latifah,", "wu-tang", "clan,", "phil", "collins,", "seun", "femi", "1997,", "l'afrobeat."}
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
for t0 in (4.58, 7.70, 24.66, 25.46, 26.42, 28.76, 29.96, 30.92, 32.70, 50.30, 51.42, 55.04, 92.40, 93.20, 93.76, 94.66): place(hit, R(t0), 0.3)
for s0, txt, cps in TYPES.values():
    for j, ch in enumerate(txt):
        if ch != " ": place(click, R(s0) + j / cps, 0.25)
place(riser, R(38.90) - RISER_PEAK, 0.5); place(riser, R(66.50) - RISER_PEAK, 0.45)
BURN_PEAK = 11 / FPS
BURN_AT = [R(42.20)]
TRANS = [(R(4.40), "red-flash-39.mp4", 17 / 30, True), (R(23.10), "light-flash-23.mp4", 5 / 23.976, False),
         (R(63.30), "bw-flash-33.mp4", 4 / 23.976, False), (R(90.30), "red-flash-39.mp4", 17 / 30, True)]
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
# voice as recorded (he asked to keep his sound): no compressor or loudness change, safety limiter only
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", CUT, "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.7:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, len(SHOTS), "shots", flush=True)
