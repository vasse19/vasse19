"""« La B7 au Mother Africa Festival » Short (Kali style): his voice note announcing La B7 as a headliner of the Mother
Africa Festival (27 & 28 décembre, Marcory Zone 4, Abidjan), with the official poster, La B7's clips, the Kaaris × La B7
photo and the La B7 × L2B post for the recap, 3D cards, word-by-word neon captions, his logo top left, library
transitions, the Kaaris × La B7 snippet very low underneath. His voice kept as recorded (limiter only).
usage: kali_b7_mother_africa.py WORK OUT.mp4   (WORK: voix.mp3, w.json, affiche.jpg, c1/c2.mp4, k2a_b7.jpg, b7_l2b.jpg, v1.mp4)"""
import sys, os, json, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VOICE = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{WORK}/voix.mp3"]))
DUR = VOICE + 0.3; N = int(DUR * FPS)
ORANGE = (255, 140, 30)

# ---------- captions ----------
REN = [(0.40, "team,"), (0.88, "Big Vass"), (1.52, "servir."), (7.04, "Mother"), (7.68, "Africa."), (8.24, "Et"), (8.48, "franchement,"),
       (14.20, "Kaaris,"), (16.60, "L2B,"), (25.24, "places,"), (26.04, "places."), (31.18, "Big Vass")]
RM = [1.04, 8.90, 16.76, 19.72, 31.34]
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
                          f"scale=-2:{H}:flags=lanczos,crop={W}:{H},unsharp=5:5:0.5,fps={FPS},eq=contrast=1.05:saturation=1.12",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
SCENES = [  # (start, kind, source, src start)
    (0.0, "vid", "c2.mp4", 13.6), (4.0, "poster", "affiche.jpg", 0), (8.9, "vid", "c1.mp4", 13.0), (12.4, "pic", "k2a_b7.jpg", 0),
    (15.0, "pic", "b7_l2b.jpg", 0), (17.4, "posterzoom", "affiche.jpg", 0), (23.4, "vid", "c1.mp4", 2.4), (29.9, "end", "affiche.jpg", 0)]
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
        fy = im.shape[0] * (0.5 + 0.3 * e)                            # focus moves down to « 27 & 28 DÉCEMBRE »
        return place_img(img, im, W / 2, 960 - (fy - im.shape[0] / 2) * z, z)
    z = W / im.shape[1] * (1 + 0.05 * u); return place_img(img, im, W / 2, 900, z)

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def card(img, im, t, t0, y):
    k = t - t0
    if k >= 0: paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
ANN = block("PETITE", "ANNONCE", 1000, 560)
TETE = block("TÊTE", "D'AFFICHE", 900, 420)
PLACES = block("PRENEZ", "VOS PLACES", 1000, 560)
END = block("RDV LES", "27 & 28 DÉC.", 1000, 560)
LOGO_S = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 200)

def draw(t):
    i, k = scene(t); img = footage(i, k)
    if i == 0: card(img, ANN, t, 1.92, 420)
    elif i == 2: stack(img, t, [(10.34, "ON L'ARRÊTE PLUS", YEL)], 140, 330, 0)
    elif i == 3: stack(img, t, [(13.56, "FEAT AVEC", WHT), (14.20, "KAARIS", RED)], 130, 330, 160)
    elif i == 4: stack(img, t, [(15.80, "FEAT AVEC", WHT), (16.60, "L2B", YEL)], 130, 330, 160)
    elif i == 5:
        if t >= 19.0: card(img, TETE, t, 19.0, 300)
    elif i == 6:
        card(img, PLACES, t, 24.68, 420)
        stack(img, t, [(26.76, "27 & 28 DÉCEMBRE", WHT), (27.48, "MARCORY ZONE 4 · ABIDJAN", ORANGE)], 85, 1330, 110)
    elif i == 7:
        card(img, END, t, 29.9, 900)
        if t > DUR - 0.4: img *= max(0.0, (DUR - t) / 0.4)
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
WHITE = {"b7", "mother", "africa.", "africa", "kaaris,", "l2b,", "big vass", "festival"}
REDW = {"annonce,", "annonce", "décembre.", "places,", "places.", "d'affiche"}
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
TRANS = [(4.0, "burn"), (8.9, "red"), (12.4, "light"), (15.0, "bw"), (17.4, "red"), (23.4, "light"), (29.9, "burn")]

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
bed = load(f"{WORK}/v1.mp4", 0.0, 25.5); bed = np.concatenate([bed, bed])[:int(DUR * SR)]
env = np.ones(len(bed), np.float32); n0 = int(0.8 * SR); env[:n0] = np.linspace(0, 1, n0); env[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR))
place(bed * env * (ref * 0.22 / (np.sqrt(np.mean(bed ** 2)) + 1e-9)), 0, 1.0)            # the Kaaris × La B7 snippet, very low
S = lambda f: os.path.join(LIB, "sfx", f)
wh = [load(S(f"whoosh-{m}.mp3")) for m in (1, 2, 3, 4)]; hit = load(S("synth-hit.wav"))
for m, (t0, _) in enumerate(TRANS): place(wh[m % 4], t0 - 0.13, 0.2)
for t0 in (1.92, 19.0, 24.68, 29.9): place(hit, t0, 0.45)
place(load(S("cash-ding.mp3")), 25.56, 0.35); place(load(S("camera-shutter-short.mp3")), 4.0, 0.4)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-filter_complex",
    "[1:a]alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]", "-map", "0:v", "-map", "[a]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT],
    input=mix[:int(DUR * SR)].tobytes(), check=True)
print("done", OUT, f"{DUR:.1f}s")
