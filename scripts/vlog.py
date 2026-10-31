"""Fast-paced talking-head edit (vertical short or horizontal YouTube) from a jump-cut clip."""
import json, sys, subprocess, os, numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from fx3d import text3d

SRC, WORK, OUT, FMT = sys.argv[1:5]           # FMT: vertical | horizontal
W, H = (1080, 1920) if FMT == "vertical" else (1920, 1080)
FPS = 30
SW, SH = 854, 480
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC]))
N = int(DUR * FPS); ft = np.arange(N) / FPS
words = json.load(open(f"{WORK}/words_cut.json"))
edl = json.load(open(f"{WORK}/edl.json"))
def wt(text, nth=0):
    hits = [w for w in words if w["w"].lower().strip(",.?!") == text]
    return hits[nth]["s"]

# ---------- cards ----------
CARDS = [  # start, end, top, bottom ('|' = new line), kind
    (0.0, 1.7, "YOUTUBE", "C'EST|CARDIO", "hook"),
    (wt("énormément", 0) - 0.1, wt("réalité") + 0.1, "TIKTOK", "= VISIBILITÉ", "card"),
    (wt("graal") - 0.25, wt("graal") + 0.9, "YOUTUBE", "LE GRAAL", "card"),
    (wt("temps", 1), wt("temps", 4) + 0.3, "TWITCH", "TOUT LE|TEMPS", "card"),
    (wt("niche") - 0.35, wt("niche") + 0.8, "CHANGER", "DE NICHE", "card"),
    (wt("continuer") - 0.2, DUR, "ON VA PAS", "LÂCHER", "end"),
]
def block(top, bot, width, maxh):
    lines = [text3d(top, 230, "chrome", 30)] + [text3d(l, 210, "red", 30) for l in bot.split("|")]
    im = Image.new("RGBA", (max(l.width for l in lines) + 40, sum(l.height for l in lines) - 110 * (len(lines) - 1)))
    y = 0
    for l in lines:
        im.alpha_composite(l, ((im.width - l.width) // 2, y)); y += l.height - 110
    im = im.rotate(5, expand=True, resample=Image.BICUBIC)
    sc = min(width / im.width, maxh / im.height)
    return np.asarray(im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)).astype(np.float32) / 255
card_img = [block(c[2], c[3], 1070 if FMT == "vertical" else 1100, 1100 if FMT == "vertical" else 900) for c in CARDS]
warn = Image.new("RGBA", (220, 200)); d = ImageDraw.Draw(warn)
d.polygon([(110, 6), (214, 194), (6, 194)], fill=(255, 210, 0, 255), outline=(0, 0, 0, 255), width=10)
d.rectangle((100, 60, 120, 140), fill=(0, 0, 0, 255)); d.ellipse((98, 152, 122, 176), fill=(0, 0, 0, 255))
warn = np.asarray(warn).astype(np.float32) / 255
def paste(dst, rgba, cx, cy, scale=1.0):
    if scale != 1.0: rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = rgba.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    src = rgba[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4]
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a
def in_card(t): return any(c[0] <= t < c[1] for c in CARDS)

# ---------- shots: change framing at phrase ends roughly every 2.5-3.5 s ----------
cuts = [0.0]
src_cuts = []                                     # real jump cuts in the edit
t = 0
for a, b in edl["edl"]:
    t += b - a; src_cuts.append(t)
for w in words:
    if w["w"][-1] in ",.?" and w["e"] - cuts[-1] > 2.5: cuts.append(w["e"])
    elif w["s"] - cuts[-1] > 3.6: cuts.append(w["s"])
cuts += [c for c in src_cuts[:-1]]
cuts = sorted(set(round(c, 2) for c in cuts))
cuts = [c for i, c in enumerate(cuts) if i == 0 or c - cuts[i - 1] > 1.2]
CYCLE = ["MED", "TIGHT", "MED", "WIDE"]
SHOTS = [(c, CYCLE[i % 4]) for i, c in enumerate(cuts)]
def shot_at(t):
    m = SHOTS[0][1]
    for s_, mm in SHOTS:
        if t >= s_: m = mm
    return m

# ---------- face track ----------
f = np.array(json.load(open(f"{WORK}/faces.json")))
fx, fy = np.interp(ft, f[:, 0], f[:, 1]), np.interp(ft, f[:, 0], f[:, 2])
ker = np.ones(21) / 21
sm = lambda v: np.convolve(np.pad(v, 10, mode="edge"), ker, mode="valid")
fx, fy = sm(sm(fx)), sm(sm(fy))

# ---------- zoom ----------
z = np.ones(N)
def punch(t0, amt, hold=0.3, rel=0.45):
    a = np.clip((ft - t0) / 0.07, 0, 1); a = a * a * (3 - 2 * a)
    r = np.clip((ft - t0 - hold) / rel, 0, 1); r = r * r * (3 - 2 * r)
    return amt * a * (1 - r)
EMPH_RED = {"cardio", "costaud", "visibilité", "graal", "dur", "obligé", "lâcher", "niche", "réalité", "prêts"}
EMPH_WHITE = {"youtube", "twitch", "tiktok", "football", "sport", "musique", "audience"}
key = lambda w: w["w"].lower().strip(",.?!")
for w in words:
    if key(w) in EMPH_RED: z += punch(w["s"], 0.13)
for c, _ in SHOTS[1:]: z += punch(c - 0.001, 0.07, 0.0, 0.25)
shake = np.zeros((N, 2)); rng = np.random.default_rng(5)
for c in CARDS:
    m = (ft >= c[0]) & (ft < c[0] + 0.3)
    shake[m] = rng.normal(0, 10, (m.sum(), 2)) * np.linspace(1, 0, m.sum())[:, None]

def layout(i):
    """Source crop (x0, y0, cw, ch) and destination box (dx, dy, dw, dh)."""
    m = shot_at(ft[i]); zz = z[i]
    if FMT == "vertical":
        if m == "WIDE": ch = SH / zz; cw = ch * SW / SH; dst = (0, 656, 1080, 608)
        else: ch = (470 if m == "MED" else 340) / zz; cw = ch * 0.8; dst = (0, 285, 1080, 1350)
    else:
        ch = SH / (zz * {"WIDE": 1.0, "MED": 1.3, "TIGHT": 1.65}[m]); cw = ch * 16 / 9; dst = (0, 0, W, H)
    x0 = np.clip(fx[i] - cw / 2, 0, SW - cw); y0 = np.clip(fy[i] + 0.12 * ch - ch / 2, 0, SH - ch)
    return x0, y0, cw, ch, dst

# ---------- captions ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
FS, CY = (104, 1500) if FMT == "vertical" else (96, 900)
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: W,Inter ExtraBold,{FS},&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,8,5,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
for w in words:
    if in_card(w["s"]): continue
    e = w["e"]
    for c in CARDS:
        if w["s"] < c[0] < e: e = c[0]
    col = r"\c&H002A2AFF&" if key(w) in EMPH_RED else (r"\c&H00FFFFFF&" if key(w) in EMPH_WHITE else "")
    txt = w["w"].upper().rstrip(",.?!") or w["w"]
    ass.append(f"Dialogue: 0,{ts(w['s'])},{ts(e)},W,,0,0,0,,{{\\an5\\pos({W//2},{CY}){col}\\fscx72\\fscy72\\t(0,90,\\fscx108\\fscy108)\\t(90,150,\\fscx100\\fscy100)}}{txt}")
open(f"{WORK}/caps_{FMT}.ass", "w").write("\n".join(ass) + "\n")

# ---------- sound design ----------
def synth(args, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", args, "-ac", "1", "-ar", "48000", path], check=True)
    return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"]), np.float32)
whoosh = synth("anoisesrc=d=0.45:c=pink:a=0.9,highpass=f=600,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.18:d=0.27", f"{WORK}/whoosh.wav")
hit = synth("sine=f=52:d=0.7,volume=1.4,afade=t=out:st=0.05:d=0.65", f"{WORK}/hit.wav")
sfx = np.zeros(int(DUR * 48000) + 48000, np.float32)
def place(snd, t, g):
    i = int(max(t, 0) * 48000); sfx[i:i + len(snd)] += snd[:len(sfx) - i] * g
for c, _ in SHOTS[1:]: place(whoosh, c - 0.2, 0.16)
for c in CARDS: place(hit, c[0], 0.5); place(whoosh, c[0] - 0.25, 0.28)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", "-", f"{WORK}/sfx.wav"], input=sfx[:int(DUR * 48000)].tobytes(), check=True)

# ---------- render ----------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
VF = ("eq=contrast=1.08:saturation=1.1:gamma=1.03,vignette=angle=PI/6,noise=alls=4:allf=t+u,"
      f"ass={WORK}/caps_{FMT}.ass,format=yuv420p")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-i", f"{WORK}/sfx.wav", "-filter_complex", f"[0:v]{VF}[v];[1:a][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]",
    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
FR = SW * SH * 3
for i in range(N):
    buf = dec.stdout.read(FR)
    if len(buf) < FR: break
    fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
    if FMT == "vertical":
        bg = cv2.resize(fr, (64, 36), interpolation=cv2.INTER_AREA)
        bg = cv2.resize(cv2.GaussianBlur(bg, (0, 0), 2), (int(1920 * SW / SH), 1920), interpolation=cv2.INTER_CUBIC)
        ox = (bg.shape[1] - W) // 2
        img = bg[:, ox:ox + W].astype(np.float32) / 255 * 0.5
    else:
        img = np.zeros((H, W, 3), np.float32)
    x0, y0, cw, ch, (dx, dy, dw, dh) = layout(i)
    x0 += shake[i, 0] * cw / dw; y0 += shake[i, 1] * ch / dh
    M = np.array([[dw / cw, 0, -x0 * dw / cw], [0, dh / ch, -y0 * dh / ch]])
    fg = cv2.warpAffine(fr, M, (dw, dh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
    fg = np.clip(fg + 0.45 * (fg - cv2.GaussianBlur(fg, (0, 0), 2.2)), 0, 1)
    img[dy:dy + dh, dx:dx + dw] = fg
    t = ft[i]
    for ci, c in enumerate(CARDS):
        if not (c[0] <= t < c[1]): continue
        k = t - c[0]
        if c[4] in ("hook", "end"):
            img = img * 0.5
        else:
            bgc = cv2.GaussianBlur(img, (0, 0), 22); L = bgc.mean(axis=2, keepdims=True)
            img = np.clip(L * np.array([0.12, 0.12, 0.9]) * 1.3 + bgc * 0.15, 0, 1)
        if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.8, 0, 1)
        s = 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1)
        paste(img, card_img[ci], W / 2 + shake[i, 0], H / 2 + shake[i, 1], s)
        if c[4] == "end":
            paste(img, warn, W / 2 + (330 if FMT == "vertical" else 520), H / 2 - (420 if FMT == "vertical" else 330), min(k / 0.15, 1) * 0.9 + 0.01)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
print("done", OUT, len(SHOTS), "shots")
