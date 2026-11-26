"""« Kaaris × La B7 » Short (Kali style): his voice note opening on Feuneu (« Feuneu fait le taf »), then what Kaaris does for La B7 (a song together out tomorrow, and La B7's feat
with L2B), with the song snippet from Kaaris' TikTok (@kaarisofficiel1, watermark blurred small, end card cut, credited)
inserted with its own sound, the BGZ photo of the two, the studio videos, La B7's clips, the « La B7 × L2B » post, 3D cards,
word-by-word neon captions, his logo top left, library transitions. His voice kept as recorded (limiter only).
usage: kali_kaaris_b7.py WORK OUT.mp4   (WORK: voix.mp3, w.json, v1.mp4 song, k2a_b7.jpg, feuneu2.jpg, b7_l2b.jpg, t1/t2.mp4 studio, c1/c2.mp4 clips)"""
import sys, os, json, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VOICE = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{WORK}/voix.mp3"]))
SONG = (8.2, 14.4)                                    # « Je vais appeler quelqu'un qui va appeler quelqu'un … La B7 »
PIECES = [("voix", 0.0, 18.75), ("song", *SONG), ("voix", 19.35, VOICE)]
OUTT = []; o = 0.0
for p in PIECES: OUTT.append(o); o += p[2] - p[1]
DUR = o + 0.3; N = int(DUR * FPS); O_SONG = OUTT[1]
def V(t):
    for (src, a, b), o0 in zip(PIECES, OUTT):
        if src == "voix" and a <= t <= b + 0.01: return o0 + t - a
    raise ValueError(t)

# ---------- captions (his voice only; the song shows its own lyrics) ----------
REN = [(0.0, "Feuneu,"), (17.08, "son"), (17.48, "avec Kaaris"), (21.46, "feat"), (22.18, "L2B."), (37.14, "Kaaris ×"),
       (42.22, "le Big Vass"), (42.78, "servir.")]
RM = [0.16, 0.40, 42.46]
NOCAP = [(2.55, 3.65)]                                 # unclear (« je lui tire mon bonnet » ?): no caption rather than a guess
words = []
for w in json.load(open(f"{WORK}/w.json")):
    if any(abs(w["s"] - t) < 0.05 for t in RM) or any(a <= w["s"] < b for a, b in NOCAP): continue
    w = dict(w)
    for t, txt in REN:
        if abs(w["s"] - t) < 0.05: w["w"] = txt
    try: w["s"] = V(w["s"])
    except ValueError: continue
    words.append(w)
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))

# ---------- footage ----------
def frames(path, t0, d, vf):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d + 0.3), "-i", path, "-an", "-vf",
                          f"{vf},fps={FPS},scale={W}:{H}:flags=lanczos,eq=contrast=1.05:saturation=1.1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
TT = "delogo=x=5:y=468:w=165:h=90,delogo=x=440:y=775:w=134:h=92"      # TikTok watermark, both positions
FILL = f"scale=-2:{H}:flags=lanczos,crop={W}:{H},unsharp=5:5:0.5"
SCENES = [  # (output start, kind, source, src start, vf)
    (0.0, "pic", "feuneu2.jpg", 0, ""), (V(6.5), "pic", "k2a_b7.jpg", 0, ""), (V(10.6), "vid", "t2.mp4", 1.0, "null"),
    (V(15.0), "vid", "t1.mp4", 1.0, "null"), (O_SONG, "vid", "v1.mp4", SONG[0], TT), (V(19.35), "vid", "c2.mp4", 13.6, FILL),
    (V(20.6), "pic", "b7_l2b.jpg", 0, ""), (V(26.9), "vid", "c1.mp4", 13.0, FILL), (V(30.5), "vid", "c2.mp4", 9.2, FILL),
    (V(33.5), "vid", "c1.mp4", 2.4, FILL), (V(37.0), "pic", "k2a_b7.jpg", 0, ""), (V(40.4), "end", "k2a_b7.jpg", 0, "")]
_c = {}
def scene(t): i = max(j for j, s in enumerate(SCENES) if s[0] <= t); return i, t - SCENES[i][0]
def pic(path):
    im = cv2.imread(path).astype(np.float32) / 255; s = W / im.shape[1]; fg = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    if fg.shape[0] >= H: y0 = int((fg.shape[0] - H) * 0.3); return fg[y0:y0 + H], None
    b = cv2.resize(cv2.GaussianBlur(cv2.resize(im, (60, int(60 * im.shape[0] / im.shape[1]))), (0, 0), 3), (int(H * im.shape[1] / im.shape[0]), H))
    x0 = (b.shape[1] - W) // 2; return b[:, x0:x0 + W] * 0.4, fg
def footage(i, k):
    s0, kind, src, a, vf = SCENES[i]; d = (SCENES[i + 1][0] if i + 1 < len(SCENES) else DUR) - s0
    if i not in _c: _c.clear(); _c[i] = pic(f"{WORK}/{src}") if kind in ("pic", "end") else frames(f"{WORK}/{src}", a, d, vf)
    if kind in ("pic", "end"):
        base, fg = _c[i]; z = 1.0 + 0.06 * k / d
        if fg is None: return cv2.warpAffine(base, cv2.getRotationMatrix2D((W / 2, H * 0.4), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)
        img = base.copy(); f2 = cv2.resize(fg, None, fx=z, fy=z); x0 = (f2.shape[1] - W) // 2; y0 = (H - f2.shape[0]) // 2
        img[max(y0, 0):max(y0, 0) + min(f2.shape[0], H)] = f2[max(-y0, 0):max(-y0, 0) + min(f2.shape[0], H), x0:x0 + W]
        return img * (0.45 if kind == "end" else 1.0)
    c = _c[i]; f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
    z = 1.0 + 0.04 * k / d + 0.04 * max(0, 1 - k / 0.15)
    return cv2.warpAffine(f, cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def card(img, im, t, t0, y):
    k = t - t0
    if k >= 0: paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
HOOK = block("FEUNEU", "FAIT LE TAF", 1000, 560)
DEMAIN = block("LE SON SORT", "DEMAIN", 1000, 520)
VS = block("KAARIS", "× LA B7", 1000, 560)
END = block("DIS-LE EN", "COMMENTAIRE", 1000, 560)
LOGO_S = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 200)
CREDIT, _ = neon("TikTok : @kaarisofficiel1", 42, WHT)

def draw(t):
    i, k = scene(t); s0, kind, src = SCENES[i][:3]; img = footage(i, k)
    if i == 0:
        card(img, HOOK, t, 0.1, 420); stack(img, t, [(V(5.4), "IL A LA VISION", YEL)], 120, 1350, 0)
    elif i == 1: stack(img, t, [(V(8.34), "CE QU'IL FAIT", WHT), (V(8.42), "POUR LA B7", GOLD)], 120, 300, 150)
    elif i == 2:
        for n, tt in enumerate((V(13.9), V(14.38))):
            if t >= tt: im, _ = neon("TRÈS HAUT", 150, YEL); paste(img, im, W / 2, 1300 - n * 260 - min((t - tt) / 0.3, 1) * 80, popk(t, tt))
    elif i == 3:
        stack(img, t, [(V(16.92), "UN SON AVEC KAARIS", WHT)], 105, 1250, 0)
        if t >= V(18.28): card(img, DEMAIN, t, V(18.28), 640)
    elif i == 4: stack(img, t, [(O_SONG + 0.1, "KAARIS × LA B7", GOLD)], 120, 330, 0)
    elif i == 5: stack(img, t, [(V(19.4), "MAIS EN PLUS…", WHT)], 130, 330, 0)
    elif i == 6: stack(img, t, [(V(21.46), "UN FEAT AVEC", WHT), (V(22.18), "L2B", YEL), (V(24.66), "DU TRÈS LOURD", RED)], 120, 300, 150)
    elif i in (7, 8): stack(img, t, [(V(29.26), "RESTE CONCENTRÉ", YEL), (V(30.14), "SUR SA MUSIQUE", WHT)], 115, 330, 145)
    elif i == 9: stack(img, t, [(V(33.5), "ÇA VA POP", GRN)], 170, 330, 0)
    elif i == 10: card(img, VS, t, V(37.14), 360)
    elif kind == "end":
        card(img, END, t, V(40.46), 560)
        if t > DUR - 0.4: img *= max(0.0, (DUR - t) / 0.4)
    if src == "v1.mp4": paste(img, CREDIT, W / 2, 1865)
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
WHITE = {"feuneu,", "kaaris,", "kaaris ×", "avec kaaris", "b7,", "b7", "b7.", "l2b.", "le big vass"}
REDW = {"vision", "lourd,", "lourd", "pop", "demain,"}
for w in words:
    i, _ = scene(w["s"])
    if SCENES[i][1] == "end" or (i == 10 and w["s"] >= V(37.14)): continue
    y = 1560 if i == 0 else 1690
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
NAMES = ["red", "light", "bw", "burn", "light", "red", "bw", "light", "red", "burn", "bw"]
TRANS = [(s[0], NAMES[(n - 1) % len(NAMES)]) for n, s in enumerate(SCENES) if n > 0]

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
def fade(x, f=0.03):
    n = int(f * SR); e = np.ones(len(x), np.float32); e[:n] = np.linspace(0, 1, n); e[-n:] = np.linspace(1, 0, n); return x * e
voice = load(f"{WORK}/voix.mp3"); ref = np.sqrt(np.mean(voice ** 2))
for (src, a, b), o0 in zip(PIECES, OUTT):
    if src == "voix": place(fade(voice[int(a * SR):int(b * SR)]), o0, 1.0)
    else: s = load(f"{WORK}/v1.mp4", a, b - a); place(fade(s * ref / (np.sqrt(np.mean(s ** 2)) + 1e-9), 0.08), o0, 1.0)
S = lambda f: os.path.join(LIB, "sfx", f)
wh = [load(S(f"whoosh-{m}.mp3")) for m in (1, 2, 3, 4)]; hit = load(S("synth-hit.wav"))
for m, (t0, _) in enumerate(TRANS): place(wh[m % 4], t0 - 0.13, 0.2)
for t0 in (0.1, V(18.28), V(22.18), V(37.14), V(40.46)): place(hit, t0, 0.45)
place(load(S("sparkle.mp3"))[:int(1.2 * SR)], V(5.4), 0.3)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-filter_complex",
    "[1:a]alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]", "-map", "0:v", "-map", "[a]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT],
    input=mix[:int(DUR * SR)].tobytes(), check=True)
print("done", OUT, f"{DUR:.1f}s")
