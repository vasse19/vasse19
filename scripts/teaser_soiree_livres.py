"""Teaser (vertical, ~24 s) of a book / discussion evening: his 17 s room video cut in three pieces, the 6 s books
video and his 6 photos (Ken Burns pans), Kali neon keywords, 3D cards, library transitions, synthesized chill
boom-bap (90 BPM, no copyright). The room speech is too far from the mic to caption reliably, so it stays as
ambience (beat ducked) without subtitles.
usage: teaser_soiree_livres.py WORK OUT.mp4   (WORK holds v1.mov = books, v2.mov = room, p1..p6.jpg)"""
import sys, os, subprocess, numpy as np, cv2
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, rgba_file, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BPM = 90; B = 60 / BPM; BAR = 4 * B
# (start, duration, kind, source, src start or pan, crop centre x 0..1)
SEG = []
def add(d, kind, src, a, x): SEG.append((sum(s[1] for s in SEG), d, kind, src, a, x))
add(BAR,     "vid", "v1", 0.3, 0.5)     # the books on the table
add(2 * B,   "pic", "p4", 0, 0.50)      # the circle, wide (pans right)
add(2 * B,   "pic", "p6", 0, 0.55)
add(BAR,     "vid", "v2", 1.4, 0.45)    # people arriving
add(2 * B,   "pic", "p3", 0, 0.51)
add(2 * B,   "pic", "p5", 0, 0.45)
add(3.4,     "vid", "v2", 8.6, 0.50)    # the talk, piece 2 (voice kept)
add(1.5 * B, "pic", "p2", 0, 0.68)
add(4.9,     "vid", "v2", 12.2, 0.58)   # piece 3, ends on the speaker with his book (voice kept)
add(2 * B,   "pic", "p1", 0, 0.53)
T_END = sum(s[1] for s in SEG); DUR = T_END + 2.9; N = int(DUR * FPS)
VOICE = [(s[0], s[1], s[4]) for s in SEG if s[3] == "v2" and s[4] > 5]

def vframes(name, t0, dur, cx):
    """Fill-crop 16:9 → 9:16 around cx, 10 % extra for the slow push-in."""
    sw = int(round(1920 * 1.1 * 16 / 9 / 2)) * 2; sh = int(1920 * 1.1)
    x = int(min(max(cx * sw - W * 1.1 / 2, 0), sw - W * 1.1))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(dur + 0.2), "-i", f"{WORK}/{name}.mov", "-an", "-vf",
        f"fps={FPS},scale={sw}:{sh}:flags=lanczos,crop={int(W*1.1)}:{sh}:{x}:0,scale={W}:{H},eq=contrast=1.08:saturation=1.15:brightness=0.02,unsharp=5:5:0.6",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
def pic(name):
    im = cv2.imread(f"{WORK}/{name}.jpg"); s = H * 1.15 / im.shape[0]
    im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    im = cv2.addWeighted(im, 1.5, cv2.GaussianBlur(im, (0, 0), 3), -0.5, 0)
    return im
_c = {}
def frame(i, k):
    t0, d, kind, src, a, cx = SEG[i]
    if i not in _c:
        _c.clear(); _c[i] = vframes(src, a, d, cx) if kind == "vid" else pic(src)
    c = _c[i]; p = k / d
    if kind == "vid":
        f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
        M = cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, 1 + 0.06 * p); return cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    h, w = c.shape[:2]; z = 1.0 + 0.06 * p                                           # pan across + slow zoom
    cw, ch = W * h / H / z, h / z
    x0 = cx * w - cw / 2 + (p - 0.5) * 0.18 * w if src in ("p4", "p6", "p5") else cx * w - cw / 2
    x0 = min(max(x0, 0), w - cw); y0 = (h - ch) / 2
    M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
    return cv2.warpAffine(c, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32) / 255

HOOK = block("ÇA PARLE", "LIVRES", 1000, 640)
END = block("LE BIG", "VASS", 900, 600)
LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 520)
def card(img, im, t, t0, y):
    k = t - t0
    if k < 0: return
    paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
S = [s[0] for s in SEG]
def overlay(img, t):
    if t < S[1]: card(img, HOOK, t, 0.25, 1350)
    elif t < S[2]: stack(img, t, [(S[1] + 0.05, "UNE SOIRÉE", WHT), (S[1] + B, "ENTRE NOUS", YEL)], 150, 1460, 180)
    elif t < S[3]: stack(img, t, [(S[2] + 0.05, "DES LIVRES", GOLD)], 170, 1560, 0)
    elif t < S[4]: stack(img, t, [(S[3] + 0.1, "TOUT LE MONDE", WHT), (S[3] + 2 * B, "EST LÀ", RED)], 150, 1420, 180)
    elif t < S[5]: stack(img, t, [(S[4] + 0.05, "ÇA DÉBAT", YEL)], 180, 330, 0)
    elif t < S[6]: stack(img, t, [(S[5] + 0.05, "ÇA ÉCHANGE", GRN)], 170, 1560, 0)
    elif t < S[7]: stack(img, t, [(S[6] + 0.3, "ON PARLE", WHT), (S[6] + 1.2, "DE LIVRES", GOLD)], 140, 300, 165)
    elif t < S[8]: pass
    elif t < S[9]: stack(img, t, [(S[8] + 0.3, "DES IDÉES", WHT), (S[8] + 1.6, "DES QUESTIONS", YEL)], 130, 300, 155)
    elif t < T_END: stack(img, t, [(S[9] + 0.05, "LA VIDÉO", WHT), (S[9] + B, "ARRIVE…", RED)], 160, 1480, 190)
    else:
        img *= 0.4; paste(img, LOGO, W / 2, 640, min((t - T_END) / 0.25, 1) * 0.15 + 0.85); card(img, END, t, T_END, 1260)
        stack(img, t, [(T_END + 0.9, "BIENTÔT", YEL)], 120, 1680, 0)

def trans(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions", name), "-vf", f"fps={FPS},scale=-2:{H},crop={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
TR = {"burn": (trans("burn-transition-12.mp4"), 11 / 30), "red": (trans("red-flash-39.mp4"), 17 / 30),
      "bw": (trans("bw-flash-33.mp4"), 4 / 23.976), "light": (trans("light-flash-23.mp4"), 5 / 23.976)}
TRANS = [(S[1], "light"), (S[3], "red"), (S[4], "bw"), (S[6], "burn"), (S[8], "light"), (S[9], "bw"), (T_END, "burn")]

VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", "vignette=angle=PI/6,noise=alls=3:allf=t+u,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY],
    stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS
    i = max(j for j in range(len(SEG)) if S[j] <= t) if t < T_END else len(SEG) - 1
    k = t - S[i]; img = frame(i, min(k, SEG[i][1]))
    if k < 0.07 and t < T_END: img = np.clip(img + (0.07 - k) / 0.07 * 0.45, 0, 1)        # flash on every cut
    overlay(img, t)
    for t0, name in TRANS:
        fr, pk = TR[name]; j = int(round((t - (t0 - pk)) * FPS))
        if 0 <= j < len(fr): img = 1 - (1 - img) * (1 - fr[j].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()

# ---------- sound: chill boom-bap (synthesized), room sound of each video piece, beat ducked under the talk ----------
SR = 48000; L = int(DUR * SR) + SR
mus = np.zeros(L, np.float32); fx = np.zeros(L, np.float32); amb = np.zeros(L, np.float32)
def place(buf, snd, t, g):
    i = int(t * SR); n = min(len(snd), len(buf) - i)
    if n > 0: buf[i:i + n] += snd[:n] * g
tt = lambda d: np.arange(int(d * SR)) / SR
rng = np.random.default_rng(3)
def filt(x, kind, f): return sosfilt(butter(4, f, kind, fs=SR, output="sos"), x).astype(np.float32)
def kick():
    t_ = tt(0.45); fr = 52 * (1 + 2.2 * np.exp(-t_ * 30)); return (np.tanh(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t_ / 0.16) * 2.5) * 0.9).astype(np.float32)
def snare():
    t_ = tt(0.3); n = rng.normal(0, 1, len(t_)).astype(np.float32)
    return filt(n * np.exp(-t_ * 18).astype(np.float32), "bandpass", [700, 6000]) * 0.55 + (np.sin(2 * np.pi * 190 * t_) * np.exp(-t_ * 30) * 0.3).astype(np.float32)
def hat(d=0.06): t_ = tt(d); return filt(rng.normal(0, 1, len(t_)).astype(np.float32) * np.exp(-t_ * 60).astype(np.float32), "highpass", 7000) * 0.2
def keys(freqs, d):
    t_ = tt(d); x = sum(np.sin(2 * np.pi * f * t_) + 0.3 * np.sin(4 * np.pi * f * t_) for f in freqs)
    return (x * np.exp(-t_ * 1.2) * np.minimum(1, t_ / 0.01) * 0.06).astype(np.float32)
def bass(f, d): t_ = tt(d); return (np.tanh(np.sin(2 * np.pi * f * t_) * 1.5) * np.exp(-t_ * 1.5) * 0.35).astype(np.float32)
CH = [((220, 261.63, 329.63, 392), 55), ((174.61, 220, 261.63, 329.63), 43.65), ((196, 246.94, 293.66, 349.23), 49), ((164.81, 207.65, 246.94, 293.66), 41.2)]
for bar in range(int(T_END / BAR) + 1):
    t0 = bar * BAR; ch, root = CH[bar % 4]
    place(mus, keys(ch, BAR + 0.3), t0, 1.0); place(mus, bass(root, BAR * 0.9), t0, 1.0)
    if bar == 0: continue                                          # first bar: keys only, the drums drop on bar 2
    for kb in (0, 1.75, 2.5): place(mus, kick(), t0 + kb * B, 0.9)
    for sb in (1, 3): place(mus, snare(), t0 + sb * B, 0.8)
    for h in range(8): place(mus, hat(), t0 + h * B / 2 + (0.03 if h % 2 else 0), 0.9 if h % 2 == 0 else 0.55)
mus[int(T_END * SR):] *= np.exp(-np.arange(L - int(T_END * SR)) / SR / 0.35)
def load(path, ss=0.0, d=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss)] + (["-t", str(d)] if d else []) + ["-i", path, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.check_output(cmd), np.float32).copy()
def fade(x, f=0.04): n = int(f * SR); e = np.ones(len(x), np.float32); e[:n] = np.linspace(0, 1, n); e[-n:] = np.linspace(1, 0, n); return x * e
for t0, d, kind, src, a, cx in SEG:
    if kind != "vid": continue
    s = fade(load(f"{WORK}/{src}.mov", a, d)); talk = src == "v2" and a > 5
    s = filt(s, "highpass", 100) / (np.sqrt(np.mean(s ** 2)) + 1e-6) * (0.12 if talk else 0.035)     # level-matched room sound
    place(amb, s, t0, 1.0)
    if talk:
        i0, i1 = int(t0 * SR), int((t0 + d) * SR); r = int(0.15 * SR)
        env = np.ones(L, np.float32); env[i0:i1] = 0.3; env[i0 - r:i0] = np.linspace(1, 0.3, r); env[i1:i1 + r] = np.linspace(0.3, 1, r); mus *= env
wh = [load(os.path.join(LIB, "sfx", f"whoosh-{m}.mp3")) for m in (1, 2, 3, 4)]
for m, (t0, _) in enumerate(TRANS): place(fx, wh[m % 4], max(t0 - 0.13, 0), 0.25)
place(fx, load(os.path.join(LIB, "sfx", "synth-hit.wav")), T_END, 0.5)
mix = (mus * 0.8 + amb + fx)[:int(DUR * SR)]; mix /= np.abs(mix).max() + 1e-6
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", f"{WORK}/mix.wav"], input=(mix * 0.8).astype(np.float32).tobytes(), check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/mix.wav", "-filter_complex",
    "[1:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,asetpts=N/SR/TB,alimiter=limit=0.8:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, f"{DUR:.1f}s", flush=True)
