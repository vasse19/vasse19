"""« Dopelym à la Machine du Moulin Rouge » reminder Short (Kali style): his voice note (concert next week, tickets
available, his first big concert in France), the official poster (05 décembre 2026, La Machine du Moulin Rouge, Paris)
with a camera move onto the date, Dopelym's clips from his TikTok (@dopelym, watermark blurred small, end card unused,
credited), 3D cards, word-by-word neon captions, his logo top left, library transitions. Voice kept as recorded.
usage: kali_dopelym_rappel.py WORK OUT.mp4   (WORK: voix.mp3, w.json, affiche.jpg, c1.mp4 car clip, c2.mp4 live)"""
import sys, os, json, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VOICE = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{WORK}/voix.mp3"]))
DUR = VOICE + 0.3; N = int(DUR * FPS)

# ---------- captions ----------
REN = [(1.60, "Big Vass"), (2.96, "refait une"), (6.74, "le"), (7.56, "Dopelym"), (8.68, "Machine"), (9.24, "Moulin"), (9.72, "Rouge."),
       (12.50, "il n'en"), (21.22, "Big Vass"), (2.08, "servir."), (21.86, "servir.")]
RM = [1.76, 3.28, 7.08, 12.66, 21.46]
words = []
for w in json.load(open(f"{WORK}/w.json")):
    if any(abs(w["s"] - t) < 0.05 for t in RM): continue
    w = dict(w)
    for t, txt in REN:
        if abs(w["s"] - t) < 0.05: w["w"] = txt
    words.append(w)
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))

# ---------- footage ----------
def frames(path, t0, d):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d + 0.3), "-i", path, "-an", "-vf",
                          f"{TT},scale=-2:{H}:flags=lanczos,crop={W}:{H},unsharp=5:5:0.5,fps={FPS},eq=contrast=1.05:saturation=1.12",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
TT = "delogo=x=5:y=468:w=165:h=90,delogo=x=440:y=775:w=134:h=92"     # his TikTok watermark, both positions
SCENES = [  # (start, kind, source, src start)
    (0.0, "vid", "c1.mp4", 4.5), (4.18, "posterzoom", "affiche.jpg", 0), (10.10, "vid", "c1.mp4", 13.0), (13.66, "vid", "c2.mp4", 1.0),
    (17.46, "poster", "affiche.jpg", 0), (19.70, "end", "affiche.jpg", 0)]
_c = {}
def scene(t): i = max(j for j, s in enumerate(SCENES) if s[0] <= t); return i, t - SCENES[i][0]
def blur_bg(im):
    b = cv2.resize(cv2.GaussianBlur(cv2.resize(im, (60, int(60 * im.shape[0] / im.shape[1]))), (0, 0), 3), (int(H * im.shape[1] / im.shape[0]) + 2, H))
    if b.shape[1] < W: b = cv2.resize(b, (W, int(b.shape[0] * W / b.shape[1])))[:H]
    x0 = (b.shape[1] - W) // 2; return b[:H, x0:x0 + W] * 0.4
def place_img(base, im, cx, cy, z):
    f = cv2.resize(im, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC); h, w = f.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2); xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    base[ya:yb, xa:xb] = f[ya - y0:yb - y0, xa - x0:xb - x0]; return base
def footage(i, k):
    s0, kind, src, a = SCENES[i]; d = (SCENES[i + 1][0] if i + 1 < len(SCENES) else DUR) - s0
    if i not in _c:
        _c.clear()
        if kind == "vid": _c[i] = frames(f"{WORK}/{src}", a, d)
        else:
            im = cv2.imread(f"{WORK}/{src}").astype(np.float32) / 255; _c[i] = (im, blur_bg(im))
    if kind == "vid":
        c = _c[i]; f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
        z = 1.0 + 0.04 * k / d + 0.04 * max(0, 1 - k / 0.15)
        return cv2.warpAffine(f, cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)
    im, base = _c[i]; img = base.copy(); u = k / d
    if kind in ("poster", "end"):                                   # whole poster above the captions
        z0 = 1420 / im.shape[0]; img = place_img(img, im, W / 2, 250 + 710 + 10 * u, z0 * (1 + 0.04 * u))   # starts under his logo
        return img * (0.4 if kind == "end" else 1.0)
    if kind == "posterzoom":                                         # camera from the poster to the date / place
        e = 1 - (1 - min(u / 0.6, 1)) ** 3; z = (1420 / im.shape[0]) * (1 + 0.55 * e)
        fy = im.shape[0] * (0.5 - 0.25 * e)                           # focus moves up to « 05 DÉCEMBRE 2026 · LA MACHINE DU MOULIN ROUGE »
        return place_img(img, im, W / 2, 960 - (fy - im.shape[0] / 2) * z, z)
    z = W / im.shape[1] * (1 + 0.05 * u); return place_img(img, im, W / 2, 900, z)

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def card(img, im, t, t0, y):
    k = t - t0
    if k >= 0: paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
HOOK = block("DOPELYM", "EN CONCERT", 1000, 560)
PLACES = block("PLACES", "DISPONIBLES", 1000, 560)
RDV = block("SOYEZ AU", "RENDEZ-VOUS", 1000, 560)
END = block("LE 5 DÉC.", "À PARIS", 1000, 560)
CREDIT, _ = neon("TikTok : @dopelym", 42, WHT)
LOGO_S = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 200)

def draw(t):
    i, k = scene(t); img = footage(i, k)
    if i == 0:
        card(img, HOOK, t, 0.15, 420); stack(img, t, [(2.40, "NOUVELLE VIDÉO", YEL)], 110, 1350, 0)
    elif i == 1 and t < 7.0: stack(img, t, [(5.86, "LA SEMAINE PROCHAINE", YEL)], 95, 1620, 0)
    elif i == 2:
        card(img, PLACES, t, 10.26, 420); stack(img, t, [(12.50, "IL EN RESTE PEU", RED)], 130, 1300, 0)
    elif i == 3: stack(img, t, [(15.18, "1ER GROS CONCERT", WHT), (16.62, "EN FRANCE", RED)], 125, 330, 155)
    elif i == 4: card(img, RDV, t, 17.94, 360)
    elif i == 5:
        card(img, END, t, 19.70, 900)
        if t > DUR - 0.4: img *= max(0.0, (DUR - t) / 0.4)
    if SCENES[i][1] == "vid": paste(img, CREDIT, W / 2, 1865)
    paste(img, LOGO_S, 130, 130)
    return img

# ---------- captions ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: G,Anton,130,&H6000E5FF,&H0000E5FF,&H8000C8FF,&H00000000,0,0,0,0,100,100,1,0,1,10,0,5,40,40,0,1
Style: W,Anton,130,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,4,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
WHITE = {"dopelym", "machine", "moulin", "rouge.", "france.", "big vass"}
REDW = {"concert", "disponibles,", "dépêchez-vous,", "rendez-vous.", "premier"}
for w in words:
    i, _ = scene(w["s"])
    y = 1770 if SCENES[i][1] in ("poster", "posterzoom", "end") else 1690
    lw = w["w"].lower()
    col = r"\c&H002A2AFF&\3c&H002A2AFF&" if lw in REDW else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if lw in WHITE else "")
    txt = w["w"].upper().strip(",.?!…: ") or w["w"]
    pp = r"\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)"
    ass.append(f"Dialogue: 0,{ts(w['s'])},{ts(max(w['e'], w['s'] + 0.15))},G,,0,0,0,,{{\\an5\\pos(540,{y}){col}\\blur14{pp}}}{txt}")
    ass.append(f"Dialogue: 1,{ts(w['s'])},{ts(max(w['e'], w['s'] + 0.15))},W,,0,0,0,,{{\\an5\\pos(540,{y}){col.split(chr(92) + '3c')[0] if col else ''}{pp}}}{txt}")
open(f"{WORK}/caps.ass", "w").write("\n".join(ass) + "\n")

# ---------- transitions ----------
def trans(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions", name), "-vf", f"fps={FPS},scale=-2:{H},crop={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
TR = {"burn": (trans("burn-transition-12.mp4"), 11 / 30), "red": (trans("red-flash-39.mp4"), 17 / 30),
      "bw": (trans("bw-flash-33.mp4"), 4 / 23.976), "light": (trans("light-flash-23.mp4"), 5 / 23.976)}
TRANS = [(4.18, "burn"), (10.10, "red"), (13.66, "light"), (17.46, "bw"), (19.70, "burn")]

VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", f"vignette=angle=PI/6,noise=alls=3:allf=t+u,ass={WORK}/caps.ass:fontsdir={os.path.dirname(ANTON)},format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", VIDEO_ONLY], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; img = draw(t); i, k = scene(t)
    if 0 < k < 0.07 and t > 0.1: img = np.clip(img + (0.07 - k) / 0.07 * 0.45, 0, 1)
    for t0, name in TRANS:
        fr, pk = TR[name]; j = int(round((t - (t0 - pk)) * FPS))
        if 0 <= j < len(fr): img = 1 - (1 - img) * (1 - fr[j].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()

# ---------- sound ----------
SR = 48000; L = int(DUR * SR) + SR; mix = np.zeros(L, np.float32)
def load(p, ss=0.0, d=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss)] + (["-t", str(d)] if d else []) + ["-i", p, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.check_output(cmd), np.float32).copy()
def place(snd, t, g):
    i0 = max(int(t * SR), 0); n = min(len(snd), L - i0)
    if n > 0: mix[i0:i0 + n] += snd[:n] * g
voice = load(f"{WORK}/voix.mp3"); ref = np.sqrt(np.mean(voice ** 2)); place(voice, 0, 1.0)
S = lambda f: os.path.join(LIB, "sfx", f)
wh = [load(S(f"whoosh-{m}.mp3")) for m in (1, 2, 3, 4)]; hit = load(S("synth-hit.wav"))
for m, (t0, _) in enumerate(TRANS): place(wh[m % 4], t0 - 0.13, 0.2)
for t0 in (0.15, 10.26, 17.94, 19.70): place(hit, t0, 0.45)
place(load(S("cash-ding.mp3")), 10.74, 0.35); place(load(S("camera-shutter-short.mp3")), 4.18, 0.4)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-filter_complex",
    "[1:a]alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]", "-map", "0:v", "-map", "[a]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT],
    input=mix[:int(DUR * SR)].tobytes(), check=True)
print("done", OUT, f"{DUR:.1f}s")
