"""Re-edit a split-screen podcast clip in a fast 'faceless documentary short' style."""
import json, sys, subprocess, os, numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from fx3d import text3d

SRC, WORK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS = 1080, 1920, 30
DUR = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",SRC]))
N = int(DUR * FPS); ft = np.arange(N) / FPS

# ---------- transcript (ASR + manual fixes) ----------
words = json.load(open(f"{WORK}/words.json"))
def sub(t0, t1, text):
    global words
    keep = [w for w in words if not (t0 - 0.01 <= w["s"] < t1)]
    new = text.split(); k = len(new)
    add = [{"w": x, "s": t0 + (t1 - t0) * i / k, "e": t0 + (t1 - t0) * (i + 1) / k} for i, x in enumerate(new)]
    words = sorted(keep + add, key=lambda w: w["s"])
sub(9.4, 10.95, "Elle fait la musique même parce que ça nous plaît")
sub(11.0, 11.15, "En fait")
sub(20.7, 21.2, "narratif")
sub(22.9, 24.6, "autour d'elle, tu vois, elle a pas")
sub(27.2, 31.3, "Il y a dû forcément avoir des litiges, il y a eu même des litiges avec Mathew Knowles, son père.")
for i, w in enumerate(words):
    w["e"] = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(w["e"], w["s"] + 0.6)
json.dump(words, open(f"{WORK}/words_fixed.json", "w"), ensure_ascii=False)

# ---------- shot list: (start, mode) ----------
SHOTS = [(0.0,"SPLIT"),(3.8,"TOP"),(5.4,"TOPT"),(7.3,"BOT"),(8.6,"TOP"),(11.0,"TOPT"),(13.0,"SPLIT"),
         (15.3,"TOP"),(17.8,"BOT"),(19.0,"TOPT"),(23.2,"TOP"),(25.4,"SPLIT"),(27.2,"TOPT"),
         (29.0,"TOP"),(31.3,"BOT"),(32.2,"TOPT")]
def shot_at(t):
    m = SHOTS[0][1]
    for s, mm in SHOTS:
        if t >= s: m = mm
    return m
CUTS = [s for s, _ in SHOTS[1:]]

# ---------- B-roll photo shown full screen when Beyoncé is mentioned ----------
BROLL_IMG = sys.argv[4] if len(sys.argv) > 4 else None
BROLL = [(2.0, 4.4), (32.4, DUR)] if BROLL_IMG else []
def in_broll(t): return any(a <= t < b for a, b in BROLL)
CUTS += [b for a, b in BROLL if b < DUR] + [a for a, b in BROLL if a > 0]
if BROLL_IMG:
    photo = cv2.imread(BROLL_IMG)
    ph, pw = photo.shape[:2]
    pcx, pcy = pw * 0.42, ph * 0.40          # framing centre (face / torso)
def broll_frame(t, a, b):
    k = (t - a) / max(b - a, 1e-3)
    zz = 1.0 + 0.10 * k                       # slow Ken Burns push-in
    ch = ph / zz; cw = ch * W / H
    x0 = np.clip(pcx - cw / 2, 0, pw - cw); y0 = np.clip(pcy - ch * 0.40 - 20 * k, 0, ph - ch)
    M = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
    out = cv2.warpAffine(photo, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return out.astype(np.float32) / 255

# ---------- full-screen 3D text cards ----------
CARDS = [  # start, end, top word, bottom word, kind
    (0.0, 2.0, "BEYONCÉ", "RIEN À PROUVER", "hook"),
    (21.2, 22.7, "CONTRÔLER", "LE NARRATIF", "card"),
    (29.4, 30.9, "LITIGES", "AVEC SON PÈRE", "card"),
    (33.6, DUR, "BEYONCÉ", "TRÈS PRIVÉE", "end"),
]
def block(top, bot, width):
    a = text3d(top, 230, "chrome", 30); b = text3d(bot, 210, "red", 30)
    im = Image.new("RGBA", (max(a.width, b.width) + 40, a.height + b.height - 110))
    im.alpha_composite(a, ((im.width - a.width) // 2, 0))
    im.alpha_composite(b, ((im.width - b.width) // 2, a.height - 110))
    im = im.rotate(5, expand=True, resample=Image.BICUBIC)
    sc = width / im.width
    return np.asarray(im.resize((width, int(im.height * sc)), Image.LANCZOS)).astype(np.float32) / 255
card_img = [block(c[2], c[3], 1070) for c in CARDS]
# warning sign for the end card
warn = Image.new("RGBA", (220, 200)); d = ImageDraw.Draw(warn)
d.polygon([(110, 6), (214, 194), (6, 194)], fill=(255, 210, 0, 255), outline=(0, 0, 0, 255), width=10)
d.rectangle((100, 60, 120, 140), fill=(0, 0, 0, 255)); d.ellipse((98, 152, 122, 176), fill=(0, 0, 0, 255))
warn = np.asarray(warn).astype(np.float32) / 255

def paste(dst, rgba, cx, cy, scale=1.0):
    if scale != 1.0:
        rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = rgba.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    src = rgba[ya - y0:yb - y0, xa - x0:xb - x0]
    a = src[..., 3:4]
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a   # RGBA -> BGR

# ---------- face tracks ----------
fc = json.load(open(f"{WORK}/faces.json"))
def track(name, default):
    a = np.array(fc[name]); t, x, y = a[:, 0], a[:, 1], a[:, 2]
    mx = np.array([np.median(x[(t > tt - 1) & (t < tt + 1)]) for tt in t])
    k = np.abs(x - mx) < 120; t, x, y = t[k], x[k], y[k]
    xs, ys = np.interp(ft, t, x), np.interp(ft, t, y)
    ker = np.ones(31) / 31
    sm = lambda v: np.convolve(np.pad(v, 15, mode="edge"), ker, mode="valid")
    return sm(sm(xs)), sm(sm(ys))
txc, tyc = track("top", 500); bxc, byc = track("bot", 520)

# ---------- zoom envelope ----------
z = np.ones(N)
def punch(t0, amt, hold=0.3, rel=0.45):
    a = np.clip((ft - t0) / 0.07, 0, 1); a = a * a * (3 - 2 * a)
    r = np.clip((ft - t0 - hold) / rel, 0, 1); r = r * r * (3 - 2 * r)
    return amt * a * (1 - r)
EMPH_RED = {"salle", "prouver,", "réussi", "narratif", "business.", "litiges,", "litiges", "père.", "privé"}
EMPH_WHITE = {"beyoncé", "beyoncé,", "mathew", "knowles,", "aujourd'hui", "aujourd'hui?"}
for w in words:
    if w["w"].lower() in EMPH_RED: z += punch(w["s"], 0.14)
for c in CUTS: z += punch(c - 0.001, 0.08, 0.0, 0.25)   # cut "landing" zoom
shake = np.zeros((N, 2)); rng = np.random.default_rng(3)
for c in CARDS:
    m = (ft >= c[0]) & (ft < c[0] + 0.3)
    shake[m] = rng.normal(0, 10, (m.sum(), 2)) * np.linspace(1, 0, m.sum())[:, None]

def crop_rect(i):
    m = shot_at(ft[i]); zz = z[i]
    if m == "SPLIT":
        cw, ch = W / zz, H / zz; return 540 - cw / 2, 960 - ch / 2, cw, ch, (0, H)
    if m == "BOT":
        cx, cy, half = bxc[i], byc[i], (960, 1920); cw, ch = 540 / zz, 960 / zz
    else:
        cx, cy, half = txc[i], tyc[i], (0, 960)
        cw, ch = (540 / zz, 960 / zz) if m == "TOP" else (430 / zz, 765 / zz)
    x0 = np.clip(cx - cw / 2, 0, W - cw); y0 = np.clip(cy - ch * 0.42, half[0], half[1] - ch)
    return x0, y0, cw, ch, half

# ---------- captions (one word at a time) ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: W,Inter ExtraBold,104,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,8,5,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
def in_card(t): return any(c[0] <= t < c[1] for c in CARDS)
for w in words:
    if in_card(w["s"]): continue
    e = w["e"]
    for c in CARDS:
        if w["s"] < c[0] < e: e = c[0]
    lw = w["w"].lower(); txt = w["w"].upper().rstrip(",.?")
    col = r"\c&H002A2AFF&" if lw in EMPH_RED else (r"\c&H00FFFFFF&" if lw in EMPH_WHITE else "")
    y = 960 if shot_at(w["s"]) == "SPLIT" and not in_broll(w["s"]) else 1380
    ass.append(f"Dialogue: 0,{ts(w['s'])},{ts(e)},W,,0,0,0,,{{\\an5\\pos(540,{y}){col}\\fscx72\\fscy72\\t(0,90,\\fscx108\\fscy108)\\t(90,150,\\fscx100\\fscy100)}}{txt}")
open(f"{WORK}/caps.ass", "w").write("\n".join(ass) + "\n")

# ---------- sound design ----------
def synth(args, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", args, "-ac", "1", "-ar", "48000", path], check=True)
    return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"]), np.float32)
whoosh = synth("anoisesrc=d=0.45:c=pink:a=0.9,highpass=f=600,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.18:d=0.27", f"{WORK}/whoosh.wav")
hit = synth("sine=f=52:d=0.7,volume=1.4,afade=t=out:st=0.05:d=0.65", f"{WORK}/hit.wav")
sfx = np.zeros(int(DUR * 48000) + 48000, np.float32)
def place(snd, t, g):
    i = int(t * 48000); sfx[i:i + len(snd)] += snd[:len(sfx) - i] * g
for c in CUTS: place(whoosh, max(c - 0.2, 0), 0.22)
for c in CARDS: place(hit, c[0], 0.55); place(whoosh, max(c[0] - 0.25, 0), 0.3)
sfx_path = f"{WORK}/sfx.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", "-", sfx_path], input=sfx[:int(DUR * 48000)].tobytes(), check=True)

# ---------- render ----------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
VF = ("unsharp=5:5:0.6,eq=contrast=1.07:saturation=1.12,vignette=angle=PI/6,noise=alls=5:allf=t+u,"
      f"ass={WORK}/caps.ass,format=yuv420p")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-i", sfx_path, "-filter_complex", f"[0:v]{VF}[v];[1:a][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]",
    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
prev_cut = -1
for i in range(N):
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    x0, y0, cw, ch, _ = crop_rect(i)
    x0 += shake[i, 0]; y0 += shake[i, 1]
    M = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
    img = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
    t = ft[i]
    for a, b in BROLL:
        if a <= t < b:
            img = broll_frame(t, a, b)
            if t - a < 0.07: img = np.clip(img + 0.6, 0, 1)
    for ci, c in enumerate(CARDS):
        if not (c[0] <= t < c[1]): continue
        k = t - c[0]
        if c[4] == "hook":   # text over the live picture, darker backdrop
            img = img * 0.55
        elif c[4] == "end" and in_broll(t):   # end card over the photo
            img = np.clip(img * 0.5 * np.array([0.75, 0.75, 1.0]), 0, 1)
        else:                # full-screen card: blurred, red-tinted picture behind 3D text
            bg = cv2.GaussianBlur(img, (0, 0), 22)
            L = bg.mean(axis=2, keepdims=True)
            img = np.clip(L * np.array([0.12, 0.12, 0.9]) * 1.3 + bg * 0.15, 0, 1)
        if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.8, 0, 1)   # white flash
        s = 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1)
        cy = 960 if c[4] != "hook" else 900
        paste(img, card_img[ci], 540 + shake[i, 0], cy + shake[i, 1], s)
        if c[4] == "end":
            paste(img, warn, 870, 560, min(k / 0.15, 1) * 0.9 + 0.01)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
print("done", OUT)
