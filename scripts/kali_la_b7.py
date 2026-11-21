"""La B7 Short (Kali style): his voice note on La B7 (Burkinabè origins, the boycott talk, 1 million views in three weeks,
the clip by Sponge Productions, studio with Kaaris), over La B7's clips (16:9 fill-crop) and two studio videos with Kaaris,
word-by-word neon captions, 3D cards, Burkina Faso flag, animated view counter, his library flashes, end card.
Voice kept as recorded (safety limiter only); the clips' own sound is a quiet bed under it.
usage: kali_la_b7.py WORK OUT.mp4   (WORK: voix.mp3, w.json, c1.mp4 c2.mp4 = clips, t1.mp4 t2.mp4 = studio, b7.jpg)"""
import sys, os, json, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def dur(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
DUR = dur(f"{WORK}/voix.mp3") + 0.6; N = int(DUR * FPS)

# ---------- captions ----------
REN = [(11.60, "burkinabè."), (15.82, "rire"), (19.50, "il"), (19.74, "revendiquait"), (20.38, "origines"), (20.78, "burkinabè."),
       (28.80, "Sponge"), (29.60, "Productions,"), (32.48, "Kaaris."), (42.88, "donnez"), (46.00, "allez"), (46.16, "ciao,"),
       (46.48, "c'est"), (46.64, "le Big Vass"), (47.20, "servir.")]
RM = [20.94, 34.08]
NOCAP = [(3.30, 4.39)]                     # « … » unclear between « comédiens » and « c'est n'importe quoi »
words = []
for w in json.load(open(f"{WORK}/w.json")):
    if any(abs(w["s"] - t) < 0.02 for t in RM): continue
    w = dict(w)
    for t, txt in REN:
        if abs(w["s"] - t) < 0.02: w["w"] = txt
    if any(a <= w["s"] < b for a, b in NOCAP): continue
    words.append(w)
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))

# ---------- footage ----------
def frames(path, t0, d, vf):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d + 0.3), "-i", path, "-an", "-vf",
                          f"{vf},fps={FPS},eq=contrast=1.06:saturation=1.12", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
FILL = f"scale=-2:{H}:flags=lanczos,crop={W}:{H},unsharp=5:5:0.5"          # 16:9 clip → centre 9:16
VERT = f"scale={W}:{H}:flags=lanczos"
# shots: (voice time start, source, source start) ; each runs until the next one
SHOTS = [(0.0, "c1", 13.0), (1.6, "c1", 0.2), (3.4, "c1", 9.2), (5.4, "c2", 0.3), (7.2, "c1", 22.2),
         (8.4, "c2", 9.2), (10.6, "c2", 13.6), (12.5, "c1", 2.4), (14.8, "c1", 18.0), (17.0, "c1", 11.0), (19.4, "c2", 22.4),
         (21.6, "count", 0), (25.9, "c2", 4.4), (27.3, "c2", 18.4), (30.3, "t1", 1.0), (33.3, "t2", 1.0), (36.2, "c1", 13.0),
         (38.4, "c1", 6.6), (40.9, "card", 0), (42.3, "c2", 12.0), (44.0, "c1", 15.8), (45.2, "end", 0)]
_c = {}
def shot(t):
    i = max(j for j, s in enumerate(SHOTS) if s[0] <= t); return i, t - SHOTS[i][0]
def footage(i, k):
    s0, src, a = SHOTS[i]; d = (SHOTS[i + 1][0] if i + 1 < len(SHOTS) else DUR) - s0
    if i not in _c: _c.clear(); _c[i] = frames(f"{WORK}/{src}.mp4", a, d, VERT if src[0] == "t" else FILL)
    c = _c[i]; f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
    z = 1.0 + 0.05 * k / max(d, 0.1) + 0.04 * max(0, 1 - k / 0.15)               # slow push-in + punch on the cut
    return cv2.warpAffine(f, cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)

# ---------- graphics ----------
def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def card(img, im, t, t0, y):
    k = t - t0
    if k >= 0: paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
def pop(img, im, t, t0, x, y, life=9.0):
    k = t - t0
    if 0 <= k < life: paste(img, im, x, y, popk(t, t0), min(k / 0.08, 1))
def badge(path, size):
    im = cv2.imread(path); im = cv2.resize(im, (size, size), interpolation=cv2.INTER_CUBIC)
    im = cv2.addWeighted(im, 1.4, cv2.GaussianBlur(im, (0, 0), 2), -0.4, 0)
    yy, xx = np.mgrid[:size, :size]; r = np.hypot(xx - size / 2, yy - size / 2)
    rgb = im[..., ::-1].astype(np.float32) / 255; ring = (r > size / 2 - 12) & (r <= size / 2)
    rgb[ring] = np.array(GOLD) / 255
    return glow_rgba(np.dstack([rgb, (r <= size / 2).astype(np.float32)]), GOLD, 18, 1.0)
def flag(w=560):
    """Burkina Faso flag: red over green, yellow five-point star, light 3D wave."""
    h = int(w * 2 / 3); f = np.zeros((h, w, 3), np.float32); f[:h // 2] = (239 / 255, 43 / 255, 45 / 255); f[h // 2:] = (0, 158 / 255, 73 / 255)
    cx, cy, R = w / 2, h / 2, h * 0.2
    pts = [(cx + (R if j % 2 == 0 else R * 0.38) * np.sin(j * np.pi / 5), cy - (R if j % 2 == 0 else R * 0.38) * np.cos(j * np.pi / 5)) for j in range(10)]
    cv2.fillPoly(f, [np.int32(pts)], (252 / 255, 209 / 255, 22 / 255), cv2.LINE_AA)
    x = np.arange(w); shade = 0.85 + 0.15 * np.sin(x / w * 2 * np.pi * 1.5)
    f *= shade[None, :, None]; yoff = (np.sin(x / w * 2 * np.pi * 1.5) * 14).astype(int)
    out = np.zeros((h + 40, w, 4), np.float32)
    for xi in range(w): out[20 + yoff[xi]:20 + yoff[xi] + h, xi, :3] = f[:, xi]; out[20 + yoff[xi]:20 + yoff[xi] + h, xi, 3] = 1
    return glow_rgba(out, (255, 255, 255), 14, 0.6)
B7 = badge(f"{WORK}/b7.jpg", 380); FLAG = flag()
HOOK = block("TELLEMENT DE", "COMÉDIENS", 1000, 560)
CARD2 = block("BANDE DE", "COMÉDIENS", 1000, 640)
END = block("LE BIG", "VASS", 900, 600)
LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 560)

def counter(img, t, t0, t1):
    p = min(max((t - t0) / (t1 - t0), 0), 1); p = 1 - (1 - p) ** 3
    n = int(round(1_000_000 * p)); txt = f"{n:,}".replace(",", " ")
    im, _ = neon(txt, 210 if n < 1_000_000 else 230, YEL if n < 1_000_000 else GOLD); paste(img, im, W / 2, 900, popk(t, t1) if t >= t1 else 1.0)

def draw(t):
    i, k = shot(t); s0, src, _ = SHOTS[i]
    if src == "count":
        img = bg("black", t)
        stack(img, t, [(21.66, "ET LÀ ?", WHT)], 140, 420, 0)
        if t >= 22.9: counter(img, t, 22.9, 24.5)
        stack(img, t, [(24.86, "DE VUES", WHT), (25.34, "EN 3 SEMAINES", RED)], 130, 1150, 160); return img
    if src == "card":
        img = bg("red", t); card(img, CARD2, t, s0 + 0.05, 960); return img
    if src == "end":
        img = bg("black", t) * 0.9; paste(img, LOGO, W / 2, 650, min(k / 0.25, 1) * 0.15 + 0.85); card(img, END, t, s0 + 0.3, 1300); return img
    img = footage(i, k)
    if t < 5.4: card(img, HOOK, t, 1.68, 420)
    elif t < 8.4: stack(img, t, [(5.44, "POURQUOI", WHT), (5.92, "JE DIS ÇA ?", YEL)], 140, 1300, 170)
    elif t < 14.8:
        pop(img, B7, t, 9.44, W / 2, 560); stack(img, t, [(9.44, "LA B7", GOLD)], 150, 840, 0)
        if t >= 11.60: pop(img, FLAG, t, 11.60, W / 2, 1210); stack(img, t, [(11.60, "BURKINABÈ", YEL)], 110, 1440, 0)
    elif t < 21.6:
        stack(img, t, [(15.82, "ÇA ME FAIT RIRE", WHT)], 120, 330, 0)
        if t >= 17.66:
            im, _ = neon("BOYCOTT", 220, RED); paste(img, im, W / 2, 620, popk(t, 17.66))
            if t >= 18.2:
                p = min((t - 18.2) / 0.25, 1); x0, x1 = 120, int(120 + 840 * p); cv2.line(img, (x0, 650), (x1, 590), (1, 1, 1), 26, cv2.LINE_AA)
    elif t < 27.3: stack(img, t, [(26.30, "IL A SORTI", WHT), (26.94, "UN CLIP", YEL)], 150, 330, 180)
    elif t < 30.3: stack(img, t, [(27.76, "RÉALISÉ PAR", WHT), (28.80, "SPONGE PRODUCTIONS", YEL)], 110, 1320, 140)
    elif t < 33.3: stack(img, t, [(31.76, "AU STUDIO AVEC", WHT), (32.48, "KAARIS", RED)], 130, 1200, 170)
    elif t < 36.2: stack(img, t, [(33.84, "LA CARRIÈRE", WHT), (34.96, "AVANCE BIEN", GRN)], 140, 1200, 170)
    elif t < 40.9: stack(img, t, [(37.52, "J'ATTENDS", WHT), (38.24, "LES HYPOCRITES", YEL), (39.68, "« BOYCOTT »", RED)], 125, 330, 155)
    elif t < 45.2: stack(img, t, [(42.88, "DONNEZ LA FORCE", WHT), (43.60, "À LA B7", GOLD), (44.32, "DU VRAI ARRIVE", RED)], 115, 330, 145)
    return img

# ---------- captions (neon Anton, one word at a time) ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: G,Anton,140,&H6000E5FF,&H0000E5FF,&H8000C8FF,&H00000000,0,0,0,0,100,100,1,0,1,10,0,5,40,40,0,1
Style: W,Anton,140,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,4,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
WHITE = {"la", "b7", "kaaris.", "sponge", "productions,", "côte", "d'ivoire,"}
REDW = {"comédiens,", "comédiens.", "boycotter", "boycott", "hypocrites", "million", "burkinabè."}
for w in words:
    src = SHOTS[shot(w["s"])[0]][1]
    if src in ("count", "card", "end"): continue                               # the graphic already says it
    lw = w["w"].lower()
    col = r"\c&H002A2AFF&\3c&H002A2AFF&" if lw in REDW else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if lw in WHITE else "")
    txt = w["w"].upper().strip(",.?!… ") or w["w"]
    pp = r"\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)"
    y = 1680
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
TRANS = [(5.4, "light"), (8.4, "red"), (14.8, "bw"), (21.6, "burn"), (25.9, "light"), (30.3, "red"), (36.2, "bw"), (40.9, "red"),
         (42.3, "light"), (45.2, "burn")]

VIDEO_ONLY = f"{WORK}/video_only.mp4"
SKIP = os.environ.get("SKIP_VIDEO") and os.path.exists(VIDEO_ONLY)   # re-mux the sound only
enc = None if SKIP else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", f"vignette=angle=PI/6,noise=alls=3:allf=t+u,ass={WORK}/caps.ass:fontsdir={os.path.dirname(ANTON)},format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", VIDEO_ONLY], stdin=subprocess.PIPE)
for n in range(0 if SKIP else N):
    t = n / FPS; img = draw(t); i, k = shot(t)
    if 0 < k < 0.07 and t > 0.1: img = np.clip(img + (0.07 - k) / 0.07 * 0.45, 0, 1)
    for t0, name in TRANS:
        fr, pk = TR[name]; j = int(round((t - (t0 - pk)) * FPS))
        if 0 <= j < len(fr): img = 1 - (1 - img) * (1 - fr[j].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if n % 300 == 0: print(f"frame {n}/{N}", flush=True)
if enc: enc.stdin.close(); enc.wait()

# ---------- sound: his voice as recorded (limiter only) + La B7's clips as a quiet bed + whooshes + counter SFX ----------
wh = ";".join(f"[{5 + m}:a]adelay={int(max(t0 - 0.13, 0) * 1000)}|{int(max(t0 - 0.13, 0) * 1000)},volume=0.2[w{m}]" for m, (t0, _) in enumerate(TRANS))
ins = sum([["-i", os.path.join(LIB, "sfx", f"whoosh-{(m % 4) + 1}.mp3")] for m in range(len(TRANS))], [])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/voix.mp3", "-i", f"{WORK}/c1.mp4", "-i", f"{WORK}/c2.mp4",
    "-i", os.path.join(LIB, "sfx", "money-counter.mp3"), *ins, "-filter_complex",
    "[1:a]aresample=48000,asetpts=N/SR/TB[v];"
    "[2:a]aresample=48000,asetpts=N/SR/TB,afade=t=out:st=25.8:d=1[b1];[3:a]aresample=48000,asetpts=N/SR/TB,afade=t=in:d=1[b2];"
    "[b1][b2]acrossfade=d=1,loudnorm=I=-30:TP=-9,aresample=48000,"
    f"afade=t=out:st={DUR - 1.2}:d=1.2[bed];"
    "[4:a]atrim=0:1.4,afade=t=out:st=1.1:d=0.3,adelay=22900|22900,volume=0.35[mc];" + wh + ";"
    "[v][bed][mc]" + "".join(f"[w{m}]" for m in range(len(TRANS))) + f"amix=inputs={3 + len(TRANS)}:normalize=0:duration=first,apad=whole_dur={DUR},"
    "alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, f"{DUR:.1f}s", flush=True)
