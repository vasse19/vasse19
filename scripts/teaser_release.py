"""Event teaser (Philipayne « Black Opps » release party, 6 Nov 2026, Saint-Denis): his clip footage cut on the beat of
the track itself, flyers as glowing cards, guests THB and Tchaikabo, date / address / free entry, Monsieur Vass logo
throughout and a « présenté par » end card.
usage: teaser_release.py WORK OUT.mp4   (WORK holds c1.mov, fly_phil.jpg, fly_thb.jpg, fly_tchaikabo.jpg)"""
import sys, os, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, typewriter, rgba_file, glow_rgba, bg

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SR = 48000
DUR = 24.0; N = int(DUR * FPS)
CLIP = f"{WORK}/c1.mov"

def frames(start, dur):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", CLIP, "-an",
                        "-vf", f"scale={W}:{H},eq=contrast=1.06:saturation=1.1", "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)
def card(path, width, rim):
    im = cv2.imread(path); s = width / im.shape[1]
    c = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    c[:6] = c[-6:] = c[:, :6] = c[:, -6:] = rim[::-1]
    return glow_rgba(np.dstack([c[..., ::-1].astype(np.float32) / 255, np.ones(c.shape[:2], np.float32)]), rim, 26, 1.1)
def popk(t, t0): return 1 + 0.3 * max(0, 1 - max(t - t0, 0) / 0.12) ** 2
def settle(k): return (1.1 - 0.1 * min(max(k, 0) / 0.3, 1) ** 0.4) * (1 + 0.03 * max(k, 0))

F_PHIL = card(f"{WORK}/fly_phil.jpg", 860, (255, 40, 50))
F_THB = card(f"{WORK}/fly_thb.jpg", 740, (255, 120, 60))
F_TCH = card(f"{WORK}/fly_tchaikabo.jpg", 740, (255, 255, 255))
LOGO_S = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 190)
LOGO_L = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 560)

# (start, end, kind, data): footage spans take (clip start); the beat of « Deux Mondes » drives the cuts
SEQ = [
    (0.0, 1.6, "open", None),
    (1.6, 4.0, "clip", 0.0),
    (4.0, 6.2, "flyer", None),
    (6.2, 8.0, "clip", 5.0),
    (8.0, 10.2, "thb", None),
    (10.2, 12.4, "tch", None),
    (12.4, 14.6, "clip", 12.0),
    (14.6, 18.2, "info", None),
    (18.2, 20.6, "clip", 17.2),
    (20.6, DUR, "end", None),
]
CLIPS = {s: frames(d, e - s + 0.1) for s, e, k, d in SEQ if k == "clip"}

def draw(t):
    for s, e, kind, d in SEQ:
        if s <= t < e: break
    k = t - s
    if kind == "clip":
        fr = CLIPS[s]; img = fr[min(int(k * FPS), len(fr) - 1)].astype(np.float32) / 255
        z = 1 + 0.12 * max(0, 1 - k / 0.18) ** 2
        if z > 1.001: img = cv2.warpAffine(img, cv2.getRotationMatrix2D((W / 2, H / 2), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)
        if s == 1.6:
            stack(img, t, [(1.7, "RELEASE PARTY", RED), (2.2, "PHILIPAYNE", WHT)], 170, 1350, 200)
        elif s == 6.2:
            stack(img, t, [(6.3, "L'ALBUM", WHT), (6.7, "BLACK OPPS", GRN)], 170, 1400, 200)
        elif s == 12.4:
            stack(img, t, [(12.5, "ON VOUS ATTEND", YEL)], 150, 1500, 0)
        elif s == 18.2:
            stack(img, t, [(18.3, "ENTRÉE GRATUITE", GRN), (18.9, "TICKET OBLIGATOIRE", WHT)], 130, 1450, 160)
    elif kind == "open":
        img = bg("black", t)
        typewriter(img, t, 0.15, "VENDREDI 6 NOVEMBRE", 110, WHT, 860, 22)
        stack(img, t, [(1.0, "SAINT-DENIS", YEL)], 130, 1040, 0)
    elif kind == "flyer":
        img = bg("paper_red", t); paste(img, F_PHIL, W / 2, 960, settle(k))
    elif kind in ("thb", "tch"):
        img = bg("paper_blue" if kind == "thb" else "red", t)
        paste(img, F_THB if kind == "thb" else F_TCH, W / 2, 1180, settle(k))
        stack(img, t, [(s + 0.15, "GUEST", WHT)], 110, 230, 0)
        stack(img, t, [(s + 0.45, "THB" if kind == "thb" else "TCHAIKABO", YEL)], 170, 370, 0)
    elif kind == "info":
        img = bg("black", t)
        stack(img, t, [(14.7, "06 NOV. 2026", YEL)], 200, 520, 0)
        stack(img, t, [(15.3, "19H – 22H", WHT)], 150, 760, 0)
        typewriter(img, t, 16.0, "6 RUE JEAN-PHILIPPE RAMEAU", 78, WHT, 1050, 30)
        stack(img, t, [(17.0, "93200 SAINT-DENIS", RED)], 120, 1200, 0)
    else:                                                    # end card: presented by Monsieur Vass
        img = bg("red", t) * 0.7
        paste(img, LOGO_L, W / 2, 380, 0.85 + 0.15 * min(k / 0.25, 1))
        stack(img, t, [(20.8, "PRÉSENTÉ PAR", WHT), (21.1, "LE BIG VASS", YEL)], 100, 700, 125)
        paste(img, F_PHIL, W / 2, 1290, 0.62 * settle(k))
        stack(img, t, [(21.7, "RÉSERVE TA PLACE", WHT), (22.2, "LIEN EN BIO", GRN)], 90, 1730, 115)
    if k < 0.06 and s > 0: img = np.clip(img + (0.06 - k) / 0.06 * 0.7, 0, 1)
    if kind != "end": paste(img, LOGO_S, 125, 125, 1.0)      # his logo on every shot
    return img

burn = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions/burn-transition-12.mp4"), "-vf", f"scale=-2:{H},crop={W}:{H}",
                       "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
BURN = np.frombuffer(burn, np.uint8).reshape(-1, H, W, 3); BURN_PEAK = 11 / FPS
BURN_AT = [4.0, 8.0, 14.6, 20.6]
VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", "noise=alls=3:allf=t+u,vignette=angle=PI/6,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY],
    stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS; img = draw(t)
    for b_ in BURN_AT:
        kb = int(round((t - (b_ - BURN_PEAK)) * FPS))
        if 0 <= kb < len(BURN): img = 1 - (1 - img) * (1 - BURN[kb].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()

# sound: the track from his clip (0-22 s) as the bed, his SFX on top
def load(p, ss=0.0, d=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss)] + (["-t", str(d)] if d else []) + ["-i", p, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.check_output(cmd), np.float32).copy()
L = int(DUR * SR); mix = np.zeros(L, np.float32)
def place(snd, t, g):
    i0 = int(t * SR)
    if i0 < 0: snd, i0 = snd[-i0:], 0
    n = min(len(snd), L - i0)
    if n > 0: mix[i0:i0 + n] += snd[:n] * g
music = load(CLIP, 0.0, 22.0); music *= np.minimum(1, (len(music) - np.arange(len(music))) / (1.2 * SR)).astype(np.float32)
place(music, 0.0, 0.55)
whoosh = load(os.path.join(LIB, "sfx/synth-whoosh.wav")); hit = load(os.path.join(LIB, "sfx/synth-hit.wav")); click = load(os.path.join(LIB, "sfx/synth-click.wav"))
burn_a = load(os.path.join(LIB, "transitions/burn-transition-12.mp4"))
for s, e, kind, d in SEQ[1:]: place(whoosh, s - 0.2, 0.25); place(hit, s, 0.25)
for j, ch in enumerate("VENDREDI 6 NOVEMBRE"):
    if ch != " ": place(click, 0.15 + j / 22, 0.3)
for j, ch in enumerate("6 RUE JEAN-PHILIPPE RAMEAU"):
    if ch != " ": place(click, 16.0 + j / 30, 0.2)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.5)
place(load(os.path.join(LIB, "sfx/cash-ding.mp3")), 18.3 - 0.25, 0.4)          # « ENTRÉE GRATUITE »
place(load(os.path.join(LIB, "sfx/riser-metallic-transition.mp3")), 20.6 - 2.95, 0.4)
place(hit, 20.8, 0.5); place(hit, 21.1, 0.4); place(hit, 22.2, 0.4); place(whoosh, 22.9, 0.3); place(hit, 23.2, 0.35)
mix /= np.abs(mix).max() + 1e-6
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", f"{WORK}/mix.wav"], input=(mix * 0.8).tobytes(), check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/mix.wav", "-filter_complex",
    "[1:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,asetpts=N/SR/TB,alimiter=limit=0.8:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, flush=True)
