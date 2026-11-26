"""« Les 5 radios de GTA VI que tu dois écouter » Short (Kali style) from a voice file: his GTA VI night-drive gameplay
full screen in vertical (centre crop on the car, slowed to the voice length, game hint text blurred), a 3D number card
and the station logo he sent per radio, artist names in neon,
the Afrobank FM player screen + Burna Boy badge for N°2, word-by-word neon captions, his logo top left, library
transitions, hits, riser into N°1, a light synthesized beat underneath. Voice kept as recorded (limiter only).
usage: kali_gta6_top5.py WORK OUT.mp4   (WORK: voix.wav, w.json, tk.mp4 gameplay, player.mp4, burna.jpg, logo_*.*)"""
import sys, os, json, subprocess, numpy as np, cv2
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VOICE = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{WORK}/voix.wav"]))
DUR = VOICE + 0.5; N = int(DUR * FPS)
PINK, CYAN = (255, 80, 200), (60, 220, 255)

# ---------- captions ----------
REN = [(1.6, "VI"), (3.8, "Backcountry."), (14.1, "Numéro"), (17.9, "les"), (18.3, "classiques"), (18.9, "rap"), (19.2, "du"),
       (19.8, "Numéro"), (20.6, "Afrobank"), (21.9, "Burna Boy"), (23.1, "l'afrobeats"), (24.0, "l'amapiano."), (26.0, "VCRR."),
       (29.3, "à Migos,"), (35.5, "Dis-le")]
RM = [18.2]
words = []
for w in json.load(open(f"{WORK}/w.json")):
    if any(abs(w["s"] - t) < 0.06 for t in RM): continue
    w = dict(w)
    for t, txt in REN:
        if abs(w["s"] - t) < 0.06: w["w"] = txt
    words.append(w)
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))

# ---------- footage ----------
BAND_H, BAND_Y = 512, 760
def frames(path, t0, d, vf, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d + 0.3), "-i", path, "-an", "-vf",
                          f"{vf},fps={FPS},scale={w}:{h}:flags=lanczos,eq=contrast=1.05:saturation=1.15", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
# shots: (voice time start, kind, trailer time)
GAME = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{WORK}/tk.mp4"]))
SLOW = (GAME - 0.2) / DUR                     # gameplay slowed a little so the drive lasts the whole voice
SHOTS = [(0.0, "game", 0), (2.8, "game", 0), (9.3, "game", 0), (14.1, "game", 0), (19.8, "game", 0), (21.8, "player", 18.0),
         (25.2, "game", 0), (33.6, "game", 0)]
_c = {}
def shot(t): i = max(j for j, s in enumerate(SHOTS) if s[0] <= t); return i, t - SHOTS[i][0]
def footage(i, k):
    s0, kind, a = SHOTS[i]; d = (SHOTS[i + 1][0] if i + 1 < len(SHOTS) else DUR) - s0
    if i not in _c:
        _c.clear()
        _c[i] = frames(f"{WORK}/player.mp4", a, d, "null", 700, 672) if kind == "player" else \
                frames(f"{WORK}/tk.mp4", s0 * SLOW, d * SLOW + 0.2,
                       f"delogo=x=545:y=676:w=190:h=28,setpts=PTS/{SLOW:.4f},scale=-2:{H}:flags=lanczos,crop={W}:{H},unsharp=5:5:0.5", W, H)
    c = _c[i]; f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
    if kind == "player":
        img = bg("black", s0 + k); paste(img, glow_rgba(np.dstack([f[..., ::-1], np.ones(f.shape[:2], np.float32)]), (40, 230, 110), 18, 0.8), W / 2, 900)
        return img
    z = 1.0 + 0.04 * k / d + 0.04 * max(0, 1 - k / 0.15)
    return cv2.warpAffine(f, cv2.getRotationMatrix2D((W / 2, H * 0.6), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)

# ---------- graphics ----------
def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def card(img, im, t, t0, y):
    k = t - t0
    if k >= 0: paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
def badge(path, size):
    h0, w0 = cv2.imread(path).shape[:2]; src = cv2.imread(path); m = min(h0, w0)
    src = src[max(0, int((h0 - m) * 0.2)):max(0, int((h0 - m) * 0.2)) + m, (w0 - m) // 2:(w0 - m) // 2 + m]
    im = cv2.resize(src, (size, size), interpolation=cv2.INTER_AREA)
    yy, xx = np.mgrid[:size, :size]; r = np.hypot(xx - size / 2, yy - size / 2)
    rgb = im[..., ::-1].astype(np.float32) / 255; rgb[(r > size / 2 - 12) & (r <= size / 2)] = np.array(GOLD) / 255
    return glow_rgba(np.dstack([rgb, (r <= size / 2).astype(np.float32)]), GOLD, 18, 1.0)
HOOK = block("LES 5 RADIOS", "DE GTA VI", 1000, 520)
NUM = {5: (2.8, block("N°5", "BACKCOUNTRY", 980, 440)), 4: (9.3, block("N°4", "FLASH FM", 980, 440)),
       3: (14.1, block("N°3", "DIRTY SOUTH CLASSICS", 1000, 440)), 2: (19.8, block("N°2", "AFROBANK FM", 980, 440)),
       1: (25.2, block("N°1", "VCRR", 980, 440))}
OUTRO = block("TA RADIO", "PRÉFÉRÉE ?", 980, 520)
BURNA = badge(f"{WORK}/burna.jpg", 260)
from PIL import Image
def logo_card(path, size):
    """Station logo he sent: square, rounded corners, white glow."""
    im = Image.open(path).convert("RGB"); m = min(im.size)
    im = im.crop(((im.width - m) // 2, (im.height - m) // 2, (im.width - m) // 2 + m, (im.height - m) // 2 + m)).resize((size, size), Image.LANCZOS)
    rgb = np.asarray(im).astype(np.float32) / 255; a = np.zeros((size, size), np.uint8); r = 40
    cv2.rectangle(a, (r, 0), (size - r - 1, size - 1), 255, -1); cv2.rectangle(a, (0, r), (size - 1, size - r - 1), 255, -1)
    for cx, cy in ((r, r), (size - r - 1, r), (r, size - r - 1), (size - r - 1, size - r - 1)): cv2.circle(a, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return glow_rgba(np.dstack([rgb, a.astype(np.float32) / 255]), (255, 255, 255), 16, 0.7)
LOGOS = {5: logo_card(f"{WORK}/logo_back.jpg", 470), 4: logo_card(f"{WORK}/logo_flash.webp", 470),
         3: logo_card(f"{WORK}/logo_dirty.png", 470), 1: logo_card(f"{WORK}/logo_vcrr.jpg", 470)}
LOGO_S = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 200)

def draw(t):
    i, k = shot(t); img = footage(i, k)
    if t < 2.8: card(img, HOOK, t, 0.1, 420)
    elif t < 33.6:
        n = min(m for m, (t0, _) in NUM.items() if t0 <= t)                   # radios count down 5 → 1
        t0, im = NUM[n]; y = 330 if SHOTS[i][1] == "player" else 420
        card(img, im, t, t0, y)
        if n in LOGOS and t >= t0 + 0.35:
            k = t - t0 - 0.35; paste(img, LOGOS[n], W / 2, 900, popk(t, t0 + 0.35) * (0.6 + 0.4 * min(k / 0.12, 1)) * (1 + 0.02 * k), min(k / 0.1, 1))
        if n == 5: stack(img, t, [(5.4, "DE LA COUNTRY", WHT), (6.4, "LANA DEL REY", YEL), (7.6, "MORGAN WALLEN", YEL)], 90, 1290, 105)
        if n == 4: stack(img, t, [(11.9, "LA RADIO POP CULTE", WHT), (12.7, "DE VICE CITY", PINK)], 95, 1310, 115)
        if n == 3: stack(img, t, [(16.5, "TRICK DADDY", YEL), (17.4, "& TRINA", YEL), (18.9, "LE RAP DU SUD", RED)], 95, 1290, 110)
        if n == 2:
            if SHOTS[i][1] == "player":
                if t >= 21.9: paste(img, BURNA, 880, 1190, popk(t, 21.9))
                stack(img, t, [(21.9, "BURNA BOY", GOLD), (23.1, "AFROBEATS", GRN), (24.0, "& AMAPIANO", GRN)], 85, 1340, 95)
        if n == 1: stack(img, t, [(27.6, "LE RAP D'AUJOURD'HUI", WHT), (28.8, "DRAKE", CYAN), (29.3, "MIGOS", CYAN)], 90, 1290, 105)
    else:
        card(img, OUTRO, t, 33.7, 420); stack(img, t, [(35.5, "DIS-LE EN COMMENTAIRE", YEL)], 95, 1420, 0)
        if t > DUR - 0.35: img *= max(0.0, (DUR - t) / 0.35)
    paste(img, LOGO_S, 130, 130)
    return img

# ---------- captions (neon Anton, one word at a time) ----------
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
WHITE = {"gta", "vi", "backcountry.", "flash", "fm", "fm,", "vice", "city", "trick", "daddy", "trina", "afrobank", "burna boy", "vcrr.", "drake", "à migos,"}
REDW = {"numéro", "radios", "meilleure.", "classiques"}
for w in words:
    if SHOTS[shot(w["s"])[0]][1] == "player": y = 1760
    else: y = 1690
    lw = w["w"].lower()
    col = r"\c&H002A2AFF&\3c&H002A2AFF&" if lw in REDW else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if lw in WHITE else "")
    txt = w["w"].upper().strip(",.?!… ") or w["w"]
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
TRANS = [(2.8, "red"), (9.3, "bw"), (14.1, "red"), (19.8, "bw"), (21.8, "light"),
         (25.2, "burn"), (33.6, "red")]

VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", f"vignette=angle=PI/6,noise=alls=3:allf=t+u,ass={WORK}/caps.ass:fontsdir={os.path.dirname(ANTON)},format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", VIDEO_ONLY], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; img = draw(t); i, k = shot(t)
    if 0 < k < 0.07 and t > 0.1: img = np.clip(img + (0.07 - k) / 0.07 * 0.45, 0, 1)
    for t0, name in TRANS:
        fr, pk = TR[name]; j = int(round((t - (t0 - pk)) * FPS))
        if 0 <= j < len(fr): img = 1 - (1 - img) * (1 - fr[j].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()

# ---------- sound: voice as recorded + synthesized beat (low) + SFX ----------
SR = 48000; L = int(DUR * SR); bed = np.zeros(L, np.float32); fx = np.zeros(L, np.float32)
def place(buf, snd, t, g):
    i0 = max(int(t * SR), 0); n = min(len(snd), len(buf) - i0)
    if n > 0: buf[i0:i0 + n] += snd[:n] * g
tt = lambda d: np.arange(int(d * SR)) / SR
rng = np.random.default_rng(6)
def filt(x, kind, f): return sosfilt(butter(4, f, kind, fs=SR, output="sos"), x).astype(np.float32)
def s808(f, d=0.6):
    t_ = tt(d); fr = f * (1 + 1.6 * np.exp(-t_ * 28)); return (np.tanh(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t_ / 0.3) * 2.2) * 0.8).astype(np.float32)
def clap():
    t_ = tt(0.3); return filt(rng.normal(0, 1, len(t_)).astype(np.float32) * np.exp(-t_ * 22).astype(np.float32), "bandpass", [900, 5000]) * 0.5
def hat(d=0.05): t_ = tt(d); return filt(rng.normal(0, 1, len(t_)).astype(np.float32) * np.exp(-t_ * 70).astype(np.float32), "highpass", 7000) * 0.22
B = 60 / 140; ROOTS = [49.0, 49.0, 41.2, 43.65]
for bar in range(int(VOICE / (4 * B)) + 1):
    t0 = 2.8 + bar * 4 * B
    if t0 >= VOICE: break
    for bo in (0, 1.5, 2.5): place(bed, s808(ROOTS[bar % 4]), t0 + bo * B, 0.8)
    for c in (1, 3): place(bed, clap(), t0 + c * B, 0.7)
    for h in range(8): place(bed, hat(), t0 + h * B / 2, 0.8 if h % 2 == 0 else 0.5)
bed[int(VOICE * SR):] *= np.exp(-np.arange(L - int(VOICE * SR)) / SR / 0.3)
def load(p):
    return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]), np.float32).copy()
S = lambda f: os.path.join(LIB, "sfx", f)
hit = load(S("synth-hit.wav")); wh = [load(S(f"whoosh-{m}.mp3")) for m in (1, 2, 3, 4)]
for m, (t0, _) in enumerate(TRANS): place(fx, wh[m % 4], t0 - 0.13, 0.22)
for t0, _ in NUM.values(): place(fx, hit, t0, 0.5)
place(fx, hit, 0.1, 0.5); place(fx, hit, 33.7, 0.45)
riser = load(S("riser-metallic-transition.mp3"))[int(2.6 * SR):int(5.3 * SR)].copy(); riser[:int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
place(fx, riser, 25.2 - len(riser) / SR, 0.45)
place(fx, load(S("camera-shutter-short.mp3")), 21.8, 0.5); place(fx, load(S("sparkle.mp3"))[:int(1.3 * SR)], 21.9, 0.3)
mix_wav = f"{WORK}/bed_fx.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", mix_wav], input=(bed * 0.12 + fx).astype(np.float32).tobytes(), check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/voix.wav", "-i", mix_wav, "-filter_complex",
    "[1:a]aresample=48000,asetpts=N/SR/TB[v];[2:a]aresample=48000[b];[v][b]amix=inputs=2:normalize=0:duration=longest,"
    "alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, f"{DUR:.1f}s")
