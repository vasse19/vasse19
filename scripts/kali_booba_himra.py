"""« Booba × Himra » Short (Kali style): his voice note on Booba proposing a featuring to Himra, with two inserts that keep
their own sound — Himra's freestyle line (« J'prépare le son que j'dois envoyer au DUC ») and Booba's Instagram story
(TikTok repost by @topdumomentofficiel1: TikTok + « Top du moment » watermarks blurred small, TikTok end card cut) —
Booba / Himra photos in a VS split, Himra live footage from the library (B&W for the flashback), 3D cards, word-by-word
neon captions, his logo top left, library transitions. His voice kept as recorded (limiter only); the inserts are
brought to his level.
usage: kali_booba_himra.py WORK OUT.mp4   (WORK: voix.mp3, w.json, w_free.mp4.json, story.mov, free.mp4, booba.png, himra.jpg)"""
import sys, os, json, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
EXT = os.path.join(REPO, "assets/extraits/musique")
VOICE = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{WORK}/voix.mp3"]))
# timeline pieces: (source, src start, src end) — his voice, the freestyle insert, his voice, Booba's story, his voice
PIECES = [("voix", 0.0, 12.40), ("story", 0.0, 2.15), ("voix", 13.00, 29.10), ("free", 7.0, 18.3), ("voix", 29.10, VOICE)]
OUTT = []; o = 0.0
for p in PIECES: OUTT.append(o); o += p[2] - p[1]
DUR = o + 0.3; N = int(DUR * FPS)
def V(t):
    """voice time -> output time"""
    for (src, a, b), o0 in zip(PIECES, OUTT):
        if src == "voix" and a <= t <= b + 0.01: return o0 + t - a
    raise ValueError(t)
O_STORY, O_FREE = OUTT[1], OUTT[3]

# ---------- captions ----------
REN = [(2.9, "Booba"), (4.2, "featuring"), (5.2, "Himra."), (9.3, "Himra"), (14.7, "Booba"), (18.2, "qui a une"), (26.1, "proposé"), (37.9, "J'aimerais"),
       (42.3, "le Big Vass")]
RM = [37.6, 42.5]
NOCAP = [(11.1, 12.5), (20.3, 24.3)]          # unclear: cut from the captions rather than guessed
words = []
for w in json.load(open(f"{WORK}/w.json")):
    if any(abs(w["s"] - t) < 0.06 for t in RM) or any(a <= w["s"] < b for a, b in NOCAP): continue
    w = dict(w)
    for t, txt in REN:
        if abs(w["s"] - t) < 0.06: w["w"] = txt
    try: w["s"] = V(w["s"])
    except ValueError: continue
    words.append(w)
for i, txt in enumerate("J'prépare le son que j'dois envoyer au DUC".split()):          # the freestyle line, as subtitled in the video
    words.append({"w": txt, "s": O_STORY + 0.05 + i * 0.2})
for w in json.load(open(f"{WORK}/w_free.mp4.json")):                                    # Booba's words
    if 7.0 <= w["s"] < 18.3 and w["w"] != "ce":
        words.append({"w": {"Imara.": "Himra.", "Imara": "Himra,"}.get(w["w"], w["w"]), "s": O_FREE + w["s"] - 7.0})
words.sort(key=lambda w: w["s"])
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))

# ---------- footage ----------
def frames(path, t0, d, vf):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d + 0.3), "-i", path, "-an", "-vf",
                          f"{vf},fps={FPS},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
DELOGO = "delogo=x=5:y=468:w=196:h=90,delogo=x=378:y=775:w=196:h=92,delogo=x=414:y=56:w=118:h=58"
PILLAR = "crop=ih*9/16:ih,unsharp=5:5:0.5"                     # the library Himra clips are vertical videos pillarboxed in 16:9
SCENES = [  # (output start, kind, path, src start, vf)
    (0.0, "hook", None, 0, ""), (V(2.6), "vs", None, 0, ""),
    (V(6.0), "vid", f"{EXT}/himra-zenith-live-16x9.mp4", 0.5, PILLAR + ",hue=s=0,eq=contrast=1.2"),
    (O_STORY, "band", f"{WORK}/story.mov", 0.0, ""),
    (OUTT[2], "vid", f"{WORK}/free.mp4", 0.0, DELOGO),
    (O_FREE, "vid", f"{WORK}/free.mp4", 7.0, DELOGO),
    (OUTT[4], "vid", f"{EXT}/himra-zenith-live-16x9.mp4", 44.0, PILLAR + ",eq=contrast=1.06:saturation=1.15"),
    (V(37.2), "outro", None, 0, "")]
_c = {}
def scene(t): i = max(j for j, s in enumerate(SCENES) if s[0] <= t); return i, t - SCENES[i][0]
def crop_fill(path, w, h, fy=0.4):
    im = cv2.imread(path); s = max(w / im.shape[1], h / im.shape[0]); im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    x0 = (im.shape[1] - w) // 2; y0 = int((im.shape[0] - h) * fy); return im[y0:y0 + h, x0:x0 + w].astype(np.float32) / 255
BOOBA_H = crop_fill(f"{WORK}/booba.png", W, H // 2, 0.25); HIMRA_H = crop_fill(f"{WORK}/himra.jpg", W, H // 2, 0.3)
def footage(i, k, t):
    s0, kind, path, a, vf = SCENES[i]; d = (SCENES[i + 1][0] if i + 1 < len(SCENES) else DUR) - s0
    if kind == "hook": return bg("red", t)
    if kind in ("vs", "outro"):
        img = np.vstack([BOOBA_H, HIMRA_H]).copy()
        if kind == "outro": img *= 0.45
        cv2.rectangle(img, (0, H // 2 - 6), (W, H // 2 + 6), (0.2, 0.2, 1.0), -1)
        return img
    if i not in _c:
        _c.clear()
        if kind == "band":
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-an", "-vf", f"fps={FPS},scale={W}:-2:flags=lanczos",
                                  "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
            bh = int(round(W * 718 / 1290 / 2) * 2); _c[i] = np.frombuffer(raw, np.uint8).reshape(-1, bh, W, 3)
        else: _c[i] = frames(path, a, d, vf)
    c = _c[i]; f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
    if kind == "band":
        img = cv2.resize(cv2.GaussianBlur(cv2.resize(f, (108, 60)), (0, 0), 3), (W * 4, H))[:, W * 3 // 2:W * 5 // 2] * 0.4
        y0 = 820; img[y0:y0 + f.shape[0]] = f; return img
    z = 1.0 + 0.04 * k / d + 0.04 * max(0, 1 - k / 0.15)
    return cv2.warpAffine(f, cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def card(img, im, t, t0, y):
    k = t - t0
    if k >= 0: paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
HOOK = block("LE SCOOP", "DU JOUR", 1000, 620)
CARD = block("POUR OU", "CONTRE ?", 1000, 640)
LOGO_S = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 200)
X, _ = neon("×", 300, GOLD)

def draw(t):
    i, k = scene(t); kind = SCENES[i][1]; img = footage(i, k, t)
    if kind == "hook": card(img, HOOK, t, 0.1, 960)
    elif kind == "vs":
        for tt, txt, y, col in ((V(2.9), "BOOBA", 820, WHT), (V(5.2), "HIMRA", 1100, YEL)):
            if t >= tt: im, _ = neon(txt, 150, col); paste(img, im, W / 2, y, popk(t, tt))
        if t >= V(5.2): paste(img, X, W / 2, H / 2, popk(t, V(5.2)))
        stack(img, t, [(V(3.6), "PROPOSE UN FEAT", RED)], 110, 330, 0)
    elif i == 2: stack(img, t, [(V(7.4), "RAPPELEZ-VOUS…", WHT), (V(8.3), "IL Y A QUELQUES ANNÉES", YEL), (V(10.2), "DANS UN FREESTYLE", RED)], 95, 330, 115)
    elif kind == "band": stack(img, t, [(O_STORY + 0.1, "HIMRA", YEL), (O_STORY + 1.3, "LE DUC = BOOBA", GOLD)], 110, 420, 140)
    elif i == 4:
        if t < V(17.3): items = [(V(13.2), "LE CONTEXTE", YEL), (V(15.5), "STORY INSTAGRAM", WHT)]
        elif t < V(24.9): items = [(V(17.3), "UN RAPPEUR AVEC", WHT), (V(18.5), "UNE LAMBORGHINI", GOLD)]
        else: items = [(V(27.4), "UN SON ENSEMBLE", RED)]
        stack(img, t, items, 100, 330, 120)
    elif i == 5: stack(img, t, [(O_FREE + 0.05, "BOOBA :", GOLD)], 110, 330, 0)
    elif i == 6: stack(img, t, [(V(32.5), "J'AI HÂTE", YEL), (V(35.6), "POUR LA CULTURE", GOLD)], 130, 330, 160)
    elif kind == "outro":
        card(img, CARD, t, V(39.7), 960)
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
WHITE = {"booba", "himra.", "himra", "himra,", "duc", "lamborghini.", "lamborghini,", "lamborghini", "instagram.", "le big vass"}
REDW = {"scoop", "featuring", "freestyle", "hâte.", "hâte,", "culture.", "culture,", "contre"}
for w in words:
    i, _ = scene(w["s"]); kind = SCENES[i][1]
    if kind in ("hook", "outro") and w["s"] >= V(39.7): continue
    y = 1300 if SCENES[i][2] and SCENES[i][2].endswith("free.mp4") else (1560 if kind == "band" else 1690)
    if kind == "vs": y = 1690
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
TRANS = [(SCENES[1][0], "red"), (SCENES[2][0], "bw"), (SCENES[3][0], "light"), (SCENES[4][0], "burn"), (SCENES[5][0], "light"),
         (SCENES[6][0], "red"), (SCENES[7][0], "burn")]

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
def lufs_match(x, ref):
    return x * (np.sqrt(np.mean(ref ** 2)) / (np.sqrt(np.mean(x ** 2)) + 1e-9))
def place(snd, t, g):
    i0 = max(int(t * SR), 0); n = min(len(snd), L - i0)
    if n > 0: mix[i0:i0 + n] += snd[:n] * g
def fade(x, f=0.02):
    n = int(f * SR); e = np.ones(len(x), np.float32); e[:n] = np.linspace(0, 1, n); e[-n:] = np.linspace(1, 0, n); return x * e
voice = load(f"{WORK}/voix.mp3")
for (src, a, b), o0 in zip(PIECES, OUTT):
    if src == "voix": place(fade(voice[int(a * SR):int(b * SR)]), o0, 1.0)
    else:
        s = load(f"{WORK}/{'story.mov' if src == 'story' else 'free.mp4'}", a, b - a)
        place(fade(lufs_match(s, voice[int(13 * SR):int(29 * SR)])), o0, 1.0)            # inserts brought to his voice level
S = lambda f: os.path.join(LIB, "sfx", f)
wh = [load(S(f"whoosh-{m}.mp3")) for m in (1, 2, 3, 4)]; hit = load(S("synth-hit.wav"))
for m, (t0, _) in enumerate(TRANS): place(wh[m % 4], t0 - 0.13, 0.2)
place(hit, 0.1, 0.45); place(hit, V(5.2), 0.45); place(hit, V(39.7), 0.45)
place(load(S("camera-shutter-short.mp3")), O_STORY, 0.45); place(load(S("camera-shutter-short.mp3")), OUTT[2], 0.4)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-filter_complex",
    "[1:a]alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]", "-map", "0:v", "-map", "[a]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT],
    input=mix[:int(DUR * SR)].tobytes(), check=True)
print("done", OUT, f"{DUR:.1f}s")
