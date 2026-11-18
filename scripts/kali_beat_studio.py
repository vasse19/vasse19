"""Beat-driven studio Short (no voice, the whole beat as he asked): his silent phone takes (GTA VI on screen, FL Studio, hands on the keyboard, piano
roll, him vibing) cut on the beat of his own instrumental (~143 BPM half-time, bar = 3.34 s), Kali-style neon text,
3D hook and end card, his library flashes on bar changes and 3D music notes. Beat kept as is, safety limiter only.
usage: kali_beat_studio.py WORK OUT.mp4   (WORK holds beat.mp3 and the takes 00720/00721/00722/00723/00725/00726/00728.mp4)"""
import sys, os, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, typewriter, rgba_file, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BPM, PHASE = 143.56, 0.104                 # measured on beat.mp3 (spectral-flux autocorrelation)
BEAT = 60 / BPM; BAR = 8 * BEAT             # the beat is felt in half-time: one bar = 8 beats at 143.56 = 3.34 s
def bar(n): return PHASE + n * BAR
BEAT_LEN = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{WORK}/beat.mp3"]))
NB = 21; DUR = BEAT_LEN                      # he asked for the whole beat: 21 bars + the end card until the beat ends
N = int(DUR * FPS)

def frames(name, t0, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(dur), "-i", f"{WORK}/{name}.mp4", "-an", "-vf",
                          f"fps={FPS},scale={W}:{H},eq=contrast=1.06:saturation=1.12", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
# shots: (bar start, bar end, take, take start s) ; inside a shot the framing punches in every 2 beats
SHOTS = [(0, 2, "00720", 0.5), (2, 3, "00721", 1.2), (3, 4, "00728", 2.0), (4, 6, "00726", 0.3), (6, 8, "00722", 3.0),
         (8, 9, "00723", 0.5), (9, 11, "00725", 0.2), (11, 12, "00723", 5.5), (12, 14, "00722", 10.0), (14, 15, "00726", 8.0),
         (15, 16, "00728", 7.5), (16, 18, "00725", 1.5), (18, 19, "00723", 2.0), (19, 20, "00722", 0.5), (20, 21, "00720", 4.0),
         (21, NB + 2, "00728", 4.0)]
_cache = {}
def clip(i):
    """Frames of shot i, decoded on demand; only the current shot stays in memory (the whole beat is ~74 s of 1080p)."""
    if i not in _cache:
        _cache.clear(); b0, b1, tk, t0 = SHOTS[i]; _cache[i] = frames(tk, t0, (b1 - b0) * BAR + 2.0)
    return _cache[i]
def shot(t):
    for i, (b0, b1, tk, t0) in enumerate(SHOTS):
        if bar(b0) <= t < bar(b1) or (i == 0 and t < bar(b0)): return i, max(t - bar(b0), 0)
    return len(SHOTS) - 1, t - bar(SHOTS[-1][0])
def frame(i, k):
    c = clip(i); f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
    step = int(k / (2 * BEAT)); z = (1.0, 1.12, 1.05, 1.2)[step % 4]
    kk = k - step * 2 * BEAT; z *= 1 + 0.04 * max(0, 1 - kk / 0.18)            # small punch on every 2nd beat
    M = cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z)
    return cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
HOOK = block("COOK-UP", "EN STUDIO", 1000, 620)
END = block("LE BIG", "VASS", 900, 600)
LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 560)
NOTE = rgba_file(os.path.join(LIB, "3d", "music-note-gold.png"), 520); NOTE2 = rgba_file(os.path.join(LIB, "3d", "music-note-red.png"), 440)
def card(img, im, t, t0, y):
    k = t - t0; s = 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1)
    paste(img, im, W / 2, y, s)
def pop3d(img, im, t, t0, x, y, life=2.0):
    k = t - t0
    if 0 <= k < life: paste(img, im, x, y, popk(t, t0) * (1 + 0.03 * k), min(k / 0.08, 1) * min((life - k) / 0.25, 1))

def overlay(img, t):
    b = (t - PHASE) / BAR
    if b < 2:
        if t < bar(1): card(img, HOOK, t, 0.0, 1380)
        else: stack(img, t, [(bar(1), "INSPIRATION", WHT), (bar(1) + 2 * BEAT, "GTA VI", (255, 90, 200))], 150, 1300, 180)
    elif b < 3: typewriter(img, t, bar(2) + BEAT, "FL STUDIO", 170, (255, 150, 40), 330, 10)
    elif b < 4: stack(img, t, [(bar(3) + BEAT, "LE BIG VASS", YEL), (bar(3) + 3 * BEAT, "EN STUDIO", WHT)], 160, 330, 190)
    elif b < 6: stack(img, t, [(bar(4) + BEAT, "ON LANCE", WHT), (bar(5), "LE BEAT", RED)], 170, 330, 200); pop3d(img, NOTE, t, bar(5), 840, 760)
    elif b < 8: stack(img, t, [(bar(6), "LES DRUMS", YEL), (bar(7), "LA MÉLODIE", GRN)], 160, 330, 200)
    elif b < 9: stack(img, t, [(bar(8) + BEAT, "ÇA DONNE QUOI ?", YEL)], 150, 1560, 0); pop3d(img, NOTE2, t, bar(8) + 2 * BEAT, 860, 520)
    elif b < 11: stack(img, t, [(bar(9), "ÉCOUTEZ…", WHT), (bar(10), "LA VIBE", GOLD)], 170, 330, 200); pop3d(img, NOTE, t, bar(10), 220, 1500)
    elif b < 12: stack(img, t, [(bar(11) + BEAT, "LE BIG VASS", YEL), (bar(11) + 3 * BEAT, "AU MIX", RED)], 150, 1500, 180)
    elif b < 14: stack(img, t, [(bar(12), "LE BEAT", WHT), (bar(13), "PREND FORME", YEL)], 160, 330, 200); pop3d(img, NOTE2, t, bar(13), 860, 1500)
    elif b < 15: stack(img, t, [(bar(14) + BEAT, "LES DÉTAILS", GOLD)], 160, 330, 0)
    elif b < 16: stack(img, t, [(bar(15) + BEAT, "ÇA PASSE ?", YEL)], 160, 330, 0)
    elif b < 18: stack(img, t, [(bar(16), "ÇA MONTE", WHT), (bar(17), "EN PUISSANCE", RED)], 160, 330, 200); pop3d(img, NOTE, t, bar(17), 860, 1500)
    elif b < 19: stack(img, t, [(bar(18) + BEAT, "LA VIBE", GOLD)], 170, 1560, 0)
    elif b < 21: stack(img, t, [(bar(19), "DONNEZ VOTRE AVIS", WHT), (bar(19) + 4 * BEAT, "EN COMMENTAIRE", YEL)], 110, 1300, 140)
    else:
        img *= 0.45; paste(img, LOGO, W / 2, 650, min((t - bar(21)) / 0.25, 1) * 0.15 + 0.85); card(img, END, t, bar(21), 1300)

def trans(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions", name), "-vf", f"fps={FPS},scale=-2:{H},crop={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
TR = {"burn": (trans("burn-transition-12.mp4"), 11 / 30), "red": (trans("red-flash-39.mp4"), 17 / 30),
      "bw": (trans("bw-flash-33.mp4"), 4 / 23.976), "light": (trans("light-flash-23.mp4"), 5 / 23.976)}
TRANS = [(bar(2), "red"), (bar(3), "light"), (bar(4), "bw"), (bar(6), "burn"), (bar(8), "red"), (bar(9), "light"), (bar(11), "bw"),
         (bar(12), "red"), (bar(14), "light"), (bar(16), "burn"), (bar(18), "bw"), (bar(19), "red"), (bar(21), "burn")]

VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", "vignette=angle=PI/6,noise=alls=3:allf=t+u,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY],
    stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; i, k = shot(t)
    img = frame(i, k)
    if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.5, 0, 1)
    overlay(img, t)
    for t0, name in TRANS:
        fr, pk = TR[name]; j = int(round((t - (t0 - pk)) * FPS))
        if 0 <= j < len(fr): img = 1 - (1 - img) * (1 - fr[j].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if n % 300 == 0: print(f"frame {n}/{N}", flush=True)
enc.stdin.close(); enc.wait()
# sound: his beat as is (it clips at +2.9 dBFS, so a safety limiter), fade-out under the end card, soft whooshes on bar changes
wh = ";".join(f"[{2 + m}:a]adelay={int(max(t0 - 0.13, 0) * 1000)}|{int(max(t0 - 0.13, 0) * 1000)},volume=0.22[w{m}]" for m, (t0, _) in enumerate(TRANS))
ins = sum([["-i", os.path.join(LIB, "sfx", f"whoosh-{(m % 4) + 1}.mp3")] for m in range(len(TRANS))], [])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/beat.mp3", *ins, "-filter_complex",
    f"[1:a]asetpts=N/SR/TB,aresample=48000[b];{wh};"          # the whole beat, untouched (no trim, no fade)
    "[b]" + "".join(f"[w{m}]" for m in range(len(TRANS))) + f"amix=inputs={1 + len(TRANS)}:normalize=0:duration=first,"
    "alimiter=limit=0.7:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, f"{DUR:.1f}s", flush=True)
