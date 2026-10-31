"""Re-edit a 4:3-in-vertical podcast clip in a fast 'faceless documentary short' style."""
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
sub(8.6, 12.4, "créé ça. Ouais. C'est une force de frappe, c'est ça.")
sub(13.0, 15.9, "Et ensuite après le logobi, le biama et tout ça.")
sub(22.2, 23.7, "le... ouais en fait, la force.")
sub(26.0, 26.7, "une copie ou quoi.")
sub(35.0, 36.4, "le balola, tout ça.")
sub(37.2, 38.2, "moi-même je dirais même,")
sub(42.6, DUR, "Oui, après. Bon, après le farotema, les travaillements, tout ça.")
for i, w in enumerate(words):
    w["e"] = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(w["e"], w["s"] + 0.6)
json.dump(words, open(f"{WORK}/words_fixed.json", "w"), ensure_ascii=False)

# ---------- shot list: (start, mode) ----------
SW, SH = 576, 1024
BAND = (0, 296, 576, 432)                      # x, y, w, h of the real picture inside the source
FACE = {"MAN": (165, 590), "WOM": (470, 585)}  # crop centres (face + hands) in source coords
SHOTS = [(0.0,"WIDE"),(2.0,"WOM"),(4.4,"MAN"),(5.0,"WOMT"),(7.2,"WIDE"),(9.6,"MAN"),(10.6,"WOMT"),
         (12.8,"WIDE"),(16.0,"WOM"),(20.0,"WOMT"),(23.6,"MAN"),(24.6,"WOM"),(27.0,"WIDE"),(29.3,"WOMT"),
         (32.0,"WOM"),(34.5,"MAN"),(35.4,"WOMT"),(37.3,"WOM"),(40.3,"WIDE"),(42.6,"MAN"),(44.0,"WOMT")]
def shot_at(t):
    m = SHOTS[0][1]
    for s_, mm in SHOTS:
        if t >= s_: m = mm
    return m
CUTS = [s_ for s_, _ in SHOTS[1:]]

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
    (0.0, 2.0, "CONGO", "OU CÔTE|D'IVOIRE ?", "hook"),
    (18.3, 19.95, "CONGOLAIS", "PLUS|SOUDÉS", "card"),
    (39.1, 40.25, "TOURNER", "LES REINS", "card"),
    (46.0, DUR, "CONGO", "VS CÔTE|D'IVOIRE", "end"),
]
def block(top, bot, width):
    """3D title: first line chrome, following lines ('|'-separated) red."""
    lines = [text3d(top, 230, "chrome", 30)] + [text3d(l, 210, "red", 30) for l in bot.split("|")]
    im = Image.new("RGBA", (max(l.width for l in lines) + 40, sum(l.height for l in lines) - 110 * (len(lines) - 1)))
    y = 0
    for l in lines:
        im.alpha_composite(l, ((im.width - l.width) // 2, y)); y += l.height - 110
    im = im.rotate(5, expand=True, resample=Image.BICUBIC)
    sc = min(width / im.width, 1100 / im.height)
    return np.asarray(im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)).astype(np.float32) / 255
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

# ---------- zoom envelope ----------
z = np.ones(N)
def punch(t0, amt, hold=0.3, rel=0.45):
    a = np.clip((ft - t0) / 0.07, 0, 1); a = a * a * (3 - 2 * a)
    r = np.clip((ft - t0 - hold) / rel, 0, 1); r = r * r * (3 - 2 * r)
    return amt * a * (1 - r)
EMPH_RED = {"original.", "copie", "soudés", "soudés,", "force.", "frappe,", "reins,", "historiquement,", "référence"}
EMPH_WHITE = {"congolais", "congo", "d'ivoire.", "côte", "logobi,", "biama", "balola,", "farotema,", "travaillements,"}
for w in words:
    if w["w"].lower() in EMPH_RED: z += punch(w["s"], 0.14)
for c in CUTS: z += punch(c - 0.001, 0.08, 0.0, 0.25)   # cut "landing" zoom
shake = np.zeros((N, 2)); rng = np.random.default_rng(3)
for c in CARDS:
    m = (ft >= c[0]) & (ft < c[0] + 0.3)
    shake[m] = rng.normal(0, 10, (m.sum(), 2)) * np.linspace(1, 0, m.sum())[:, None]

def crop_rect(i):
    """Source rectangle to show, and the destination box (x, y, w, h) in the 1080x1920 frame."""
    m = shot_at(ft[i]); zz = z[i]
    bx, by, bw, bh = BAND
    if m == "WIDE":
        cw, ch = bw / zz, bh / zz; cx, cy = bx + bw / 2, by + bh / 2; dst = (0, 555, 1080, 810)
    else:
        cx, cy = FACE[m[:3]]
        ch = (380 if not m.endswith("T") else 300) / zz; cw = ch * 0.8; dst = (0, 285, 1080, 1350)
    x0 = np.clip(cx - cw / 2, bx, bx + bw - cw); y0 = np.clip(cy - ch / 2, by, by + bh - ch)
    return x0, y0, cw, ch, dst

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
    y = 1500
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
FR = SW * SH * 3
VF = ("unsharp=5:5:0.6,eq=contrast=1.07:saturation=1.12,vignette=angle=PI/6,noise=alls=5:allf=t+u,"
      f"ass={WORK}/caps.ass,format=yuv420p")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-i", sfx_path, "-filter_complex", f"[0:v]{VF}[v];[1:a][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]",
    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
prev_cut = -1
for i in range(N):
    buf = dec.stdout.read(FR)
    if len(buf) < FR: break
    fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
    bx, by, bw, bh = BAND
    band = fr[by:by + bh, bx:bx + bw]
    # background: the picture itself, zoomed to fill, blurred and darkened
    bg = cv2.resize(band, (int(bw * 192 / bh / 4), 48), interpolation=cv2.INTER_AREA)
    bg = cv2.GaussianBlur(bg, (0, 0), 3)
    bg = cv2.resize(bg, (int(bw * 1920 / bh), 1920), interpolation=cv2.INTER_CUBIC)
    ox = (bg.shape[1] - W) // 2
    img = bg[:, ox:ox + W].astype(np.float32) / 255 * 0.55
    x0, y0, cw, ch, (dx, dy, dw, dh) = crop_rect(i)
    x0 += shake[i, 0] * cw / dw; y0 += shake[i, 1] * ch / dh
    M = np.array([[dw / cw, 0, -x0 * dw / cw], [0, dh / ch, -y0 * dh / ch]])
    fg = cv2.warpAffine(fr, M, (dw, dh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
    fg = np.clip(fg + 0.5 * (fg - cv2.GaussianBlur(fg, (0, 0), 2.5)), 0, 1)
    img[dy:dy + dh, dx:dx + dw] = fg
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
