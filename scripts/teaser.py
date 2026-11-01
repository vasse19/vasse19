"""US-creator style channel teaser (vertical, ~30 s): cold open with his voice, record-scratch freeze frame
(« OUI, C'EST MOI. »), countdown into a trap beat drop, beat-synced flashes of his best moments in four
chapters, hard stop on « VOUS N'ÊTES PAS PRÊTS. », gold 3D intro, end card « BIENTÔT ».
The beat is synthesized here (no copyrighted music).
usage: teaser.py REPO_DIR WORK_DIR OUT.mp4"""
import sys, os, subprocess, numpy as np, cv2
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, YEL, RED, WHT, GOLD, GRN, paste, neon, stack, typewriter, rgba_file, glow_rgba, bg, block

REPO, WORK, OUT = sys.argv[1:4]
os.makedirs(WORK, exist_ok=True)
SR = 48000
BPM = 140; B = 60 / BPM
V = lambda n: os.path.join(REPO, n)
WAN, DID, SUS, KHA = V("wantche_platinum_trapper.mp4"), V("didib_triche_ou_strategie.mp4"), V("suspect95_ou_est_il.mp4"), V("djkhaled_rap_ivoire.mp4")
X = lambda n: os.path.join(LIB, "extraits", n)
MUS_TV, MUS_LIVE = X("musique/tv-big-up-monsieur-vass.mp4"), X("musique/sortie-concert-nuit.mp4")
CUL_RED, CUL_ITW = X("culture/tapis-rouge-evenement.mp4"), X("culture/interview-monsieur-vass.mp4")
SPO_CIV = X("sport/cote-divoire-coupe-du-monde.mp4")
RAW = CUL_ITW                                    # his interview: « Et c'est là que je me suis dit : je vais continuer à faire du contenu »
FULL = "scale=1080:1920"
BAND = "crop=576:324:0:318,scale=-2:1920,crop=1080:1920"          # 16:9 picture band of a TikTok repost, filled to 9:16
LETTER = "crop=310:310:133:334,scale=1080:1080,pad=1080:1920:0:380:black"   # square crop on him, cinematic black bars

# ---------- timeline ----------
T_COLD = 3.30                                    # cold open ends on « ...faire du contenu »
T_CD = T_COLD + 1.58                             # countdown screen
TD = T_CD + 4 * B                                # the drop
# the three pillars of the channel; clip = (file, start, keep voice, beats, crop)
GROUPS = [
    ("MUSIQUE", YEL, [(WAN, 9.6, False, 2, FULL), (DID, 22.5, False, 2, FULL), (KHA, 3.4, False, 2, FULL),
                      (MUS_LIVE, 9.2, False, 2, FULL), (MUS_TV, 13.45, True, 4, BAND)]),
    ("CULTURE", WHT, [(CUL_RED, 6.5, False, 2, FULL), (CUL_ITW, 34.0, False, 2, BAND), (SUS, 9.2, False, 2, FULL),
                      (KHA, 21.2, False, 2, FULL), (WAN, 44.0, True, 2, FULL)]),
    ("SPORT", GRN,   [(SPO_CIV, 12.5, False, 2, FULL), (SPO_CIV, 20.5, False, 2, FULL), (SPO_CIV, 41.5, False, 2, FULL),
                      (SPO_CIV, 33.2, False, 2, FULL), (SPO_CIV, 36.35, True, 4, FULL)]),
]
SEGS = []                                        # (start, end, kind, data)
t = TD
for title, col, clips in GROUPS:
    SEGS.append((t, t + B, "card", (title, col))); t += B
    for c in clips:
        SEGS.append((t, t + c[3] * B, "clip", c)); t += c[3] * B
TE = t                                           # beat stops
T_STOP = TE + 2.6                                # « VOUS N'ÊTES PAS PRÊTS. » ends
T_LOGO_END = T_STOP + 4.0
DUR = T_LOGO_END + 2.6
N = int(DUR * FPS)
print(f"drop {TD:.2f}s, beat stops {TE:.2f}s, total {DUR:.2f}s", flush=True)

# ---------- sources ----------
def frames(path, start, dur, vf="scale=1080:1920"):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", path, "-an", "-vf", vf, "-r", str(FPS),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)
COLD = frames(RAW, 0.0, T_COLD + 0.1, LETTER)
FREEZE = COLD[min(len(COLD) - 1, int(T_COLD * FPS) - 1)].astype(np.float32) / 255
CLIPF = {}
for s, e, kind, d in SEGS:
    if kind == "clip": CLIPF[(d[0], d[1])] = frames(d[0], d[1], e - s + 0.1, d[4])
INTRO = frames(V("intro_3d_monsieur_vass.mp4"), 0.0, 4.0, "crop=1560:1080,scale=1080:-2,pad=1080:1920:0:(oh-ih)/2:black")
logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 560)
burn = frames(os.path.join(LIB, "transitions/burn-transition-12.mp4"), 0, 0.68, "scale=-2:1920,crop=1080:1920")
BURN_PEAK = 11 / FPS
BURN_AT = [TD, T_STOP]
END_CARD = block("LE BIG", "VASS", 1000, 640)
COUNT = {str(n): neon(str(n), 420, RED)[0] for n in (3, 2, 1)}

def bars(img, h=150):
    img[:h] = 0; img[-h:] = 0; return img
def punch_in(img, k, amt=0.16, d=0.14):
    s = 1 + amt * max(0.0, 1 - k / d) ** 2
    if s > 1.001:
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s); img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return img
def rgb_split(img, px):
    if px <= 0: return img
    o = img.copy(); o[:, px:, 2] = img[:, :-px, 2]; o[:, :-px, 0] = img[:, px:, 0]; return o
def flash(img, k, d=0.07, a=0.7):
    return np.clip(img + max(0.0, (d - k) / d) * a, 0, 1) if k < d else img

def render(i):
    t = i / FPS
    if t < T_COLD:                                                    # cold open
        img = COLD[min(i, len(COLD) - 1)].astype(np.float32) / 255
        s = 1 + 0.06 * t / T_COLD
        img = cv2.warpAffine(img, cv2.getRotationMatrix2D((W / 2, H * 0.4), 0, s), (W, H), borderMode=cv2.BORDER_REFLECT)
        return bars(img * 0.92)
    if t < T_CD:                                                      # record scratch freeze frame
        k = t - T_COLD
        g = cv2.cvtColor((FREEZE * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
        g = np.clip((g - 0.5) * 1.35 + 0.48, 0, 1)
        img = np.dstack([g, g, g])
        img = cv2.warpAffine(img, cv2.getRotationMatrix2D((W / 2, H * 0.4), 0, 1.06 + 0.03 * k), (W, H), borderMode=cv2.BORDER_REFLECT)
        img = flash(img, k, 0.1, 0.9)
        typewriter(img, t, T_COLD + 0.12, "OUI, C'EST MOI.", 110, WHT, 1545, 18)
        stack(img, t, [(T_COLD + 0.85, "LE BIG VASS", YEL)], 125, 1680, 0)
        return bars(img)
    if t < TD:                                                        # countdown
        img = bg("black", t)
        typewriter(img, t, T_CD + 0.05, "CE QUI ARRIVE…", 110, WHT, 520, 20)
        for n, tn in (("3", TD - 3 * B), ("2", TD - 2 * B), ("1", TD - B)):
            if tn <= t < tn + B: paste(img, COUNT[n], W / 2, 1050, 1 + 0.35 * max(0, 1 - (t - tn) / 0.12) ** 2)
        return img
    if t < TE:                                                        # beat-synced flashes
        for s, e, kind, d in SEGS:
            if s <= t < e: break
        k = t - s
        if kind == "card":
            img = bg("red", t) * 0.55
            im, _ = neon(d[0], 230, d[1])
            paste(img, im, W / 2 + np.random.default_rng(i).normal(0, 6 * max(0, 1 - k / 0.15)), H / 2, 1 + 0.4 * max(0, 1 - k / 0.12) ** 2)
            return flash(img, k, 0.08, 0.9)
        fr = CLIPF[(d[0], d[1])]
        img = fr[min(int(k * FPS), len(fr) - 1)].astype(np.float32) / 255
        img = rgb_split(punch_in(img, k), int(max(0, 14 * (1 - k / 0.1))))
        return flash(img, k, 0.06, 0.5)
    if t < T_STOP:                                                    # hard stop
        img = np.zeros((H, W, 3), np.float32)
        if t >= TE + 0.45:
            img = bg("black", t) * 0.8
            stack(img, t, [(TE + 0.45, "VOUS N'ÊTES", WHT), (TE + 1.05, "PAS PRÊTS.", RED)], 200, 820, 250)
        return img
    if t < T_LOGO_END:                                                # gold 3D intro
        k = t - T_STOP
        return INTRO[min(int(k * FPS), len(INTRO) - 1)].astype(np.float32) / 255
    k = t - T_LOGO_END                                                # end card
    img = bg("red", t) * 0.7
    paste(img, logo, W / 2, 560, 0.85 + 0.15 * min(k / 0.25, 1))
    paste(img, END_CARD, W / 2, 1060, 0.6 + 0.5 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
    typewriter(img, t, T_LOGO_END + 0.5, "BIENTÔT.", 170, YEL, 1480, 10)
    stack(img, t, [(T_LOGO_END + 1.2, "ACTIVE LES NOTIFS", WHT)], 80, 1650, 0)
    return flash(img, k, 0.08, 0.8)

# ---------- picture ----------
VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", "eq=contrast=1.04:saturation=1.06,noise=alls=3:allf=t+u,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY],
    stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS; img = render(i)
    for b_ in BURN_AT:
        kk = int(round((t - (b_ - BURN_PEAK)) * FPS))
        if 0 <= kk < len(burn): img = 1 - (1 - img) * (1 - burn[kk].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if i % 150 == 0: print(f"frame {i}/{N}", flush=True)
enc.stdin.close(); enc.wait()

# ---------- music (synthesized trap, 140 BPM, A minor) ----------
L = int(DUR * SR) + SR
mus = np.zeros(L, np.float32); fx = np.zeros(L, np.float32); vox = np.zeros(L, np.float32)
def place(buf, snd, t, g):
    i = int(t * SR)
    if i < 0: snd, i = snd[-i:], 0
    n = min(len(snd), len(buf) - i)
    if n > 0: buf[i:i + n] += snd[:n] * g
tt = lambda d: np.arange(int(d * SR)) / SR
rng = np.random.default_rng(1)
def filt(x, kind, f): return sosfilt(butter(4, f, kind, fs=SR, output="sos"), x).astype(np.float32)
def s808(f, d=0.75):
    t_ = tt(d); fr = f * (1 + 1.6 * np.exp(-t_ * 28)); ph = 2 * np.pi * np.cumsum(fr) / SR
    return np.tanh(np.sin(ph) * np.exp(-t_ / 0.38) * 2.2).astype(np.float32) * 0.8
def clap():
    t_ = tt(0.35); n = rng.normal(0, 1, len(t_)).astype(np.float32)
    env = np.exp(-t_ * 22) + sum(np.exp(-np.maximum(t_ - o, 0) * 120) * (t_ >= o) for o in (0, 0.011, 0.022)) * 0.6
    return filt(n * env, "bandpass", [900, 5000]) * 0.5
def hat(d=0.05):
    t_ = tt(d); return filt(rng.normal(0, 1, len(t_)).astype(np.float32) * np.exp(-t_ * 70), "highpass", 7000) * 0.22
def pluck(f, d=0.5):
    t_ = tt(d); return (sum(np.sin(2 * np.pi * f * k * t_) / k * np.exp(-t_ * (4 + 2 * k)) for k in range(1, 6)) * 0.18).astype(np.float32)
def pad(d, freqs=(110, 130.81, 164.81)):
    t_ = tt(d); x = sum(((t_ * f * (1 + dt)) % 1 * 2 - 1) for f in freqs for dt in (-0.004, 0.004))
    env = np.minimum(1, t_ / 0.6) * np.minimum(1, (d - t_) / 0.4)
    return filt(x.astype(np.float32) * env.astype(np.float32), "lowpass", 900) * 0.035
def boom(d=2.2):
    t_ = tt(d); return (s808(41.2, d) * 1.2 + filt(rng.normal(0, 1, len(t_)).astype(np.float32) * np.exp(-t_ * 3), "lowpass", 300) * 0.4)
def scratch():
    t_ = tt(0.32); f = 900 + 700 * np.sin(2 * np.pi * 9 * t_)
    return filt(rng.normal(0, 1, len(t_)).astype(np.float32), "bandpass", [300, 3000]) * (0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) ** 2).astype(np.float32) * np.exp(-t_ * 4).astype(np.float32)
whoosh = filt(rng.normal(0, 1, int(0.4 * SR)).astype(np.float32), "bandpass", [600, 5000]) * np.sin(np.linspace(0, np.pi, int(0.4 * SR))).astype(np.float32) * 0.3
def load(path, ss=0.0, d=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss)] + (["-t", str(d)] if d else []) + ["-i", path, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.check_output(cmd), np.float32).copy()

place(mus, pad(T_COLD + 0.2), 0, 1.0)                                  # cold open: dark pad under his voice
cold = load(RAW, 0.0, T_COLD + 0.05); cold *= np.minimum(1, (len(cold) - np.arange(len(cold))) / (0.03 * SR))
place(vox, cold / (np.abs(cold).max() + 1e-6) * 0.6, 0, 1.0)
place(fx, scratch(), T_COLD - 0.03, 1.0)                               # record scratch on the freeze
place(fx, s808(55, 0.5), T_COLD, 0.5)
place(mus, pad(T_CD - T_COLD + 0.1, (55, 65.41, 82.41)), T_COLD + 0.15, 2.2)   # low drone + heartbeat under the freeze
for hb in (T_COLD + 0.63, T_COLD + 0.88, T_COLD + 1.23, T_COLD + 1.48): place(fx, s808(48, 0.28), hb, 0.45)
place(mus, pad(TD - T_CD + 0.3), T_CD, 1.4)
riser = load(os.path.join(LIB, "sfx/riser-metallic-transition.mp3")); place(fx, riser, TD - 2.95, 0.6)
for n in range(3): place(fx, s808(41.2, 0.35), TD - (3 - n) * B, 0.6)
NOTES = [55.0, 55.0, 43.65, 49.0]                                     # 808 roots per bar: A1 A1 F1 G1
MEL = [[440, 523.25, 659.25, 523.25], [440, 523.25, 659.25, 587.33], [349.23, 440, 523.25, 440], [392, 493.88, 587.33, 493.88]]
nbars = int(round((TE - TD) / (4 * B)))
for bar in range(nbars + 1):
    t0 = TD + bar * 4 * B; f = NOTES[bar % 4]
    for beat_off in (0, 1.5, 2.5):
        if t0 + beat_off * B < TE: place(mus, s808(f), t0 + beat_off * B, 0.9)
    for c in (1, 3):
        if t0 + c * B < TE: place(mus, clap(), t0 + c * B, 0.8)
    for h in range(8):
        th = t0 + h * B / 2
        if th < TE: place(mus, hat(), th, 0.9 if h % 2 == 0 else 0.6)
    if bar % 2 == 1:                                                  # triplet hat roll on the last beat
        for r in range(6):
            th = t0 + 3 * B + r * B / 6
            if th < TE: place(mus, hat(0.03), th, 0.5)
    for q, fq in enumerate(MEL[bar % 4]):
        if t0 + q * B < TE: place(mus, pluck(fq), t0 + q * B, 1.0)
    if t0 < TE: place(mus, pad(min(4 * B, TE - t0) + 0.05, (f * 2, f * 2 * 1.189, f * 3)), t0, 0.8)
for s, e, kind, d in SEGS:
    place(fx, whoosh, s - 0.12, 0.25)
    if kind == "clip" and d[2]:                                       # his punchline, voice kept
        v = load(d[0], d[1], e - s); v *= np.minimum(1, np.minimum(np.arange(len(v)), len(v) - np.arange(len(v))) / (0.02 * SR))
        place(vox, v, s, 1.0)
        i0, i1 = int(s * SR), int(e * SR); mus[i0:i1] *= 0.55            # duck the beat under the punchline
place(fx, boom(), TE + 0.45, 0.9); place(fx, boom(), TE + 1.05, 0.9)
intro_a = load(V("intro_3d_monsieur_vass.mp4"), 0, 4.0); place(fx, intro_a, T_STOP, 0.9)
place(mus, pad(DUR - T_LOGO_END + 0.1), T_LOGO_END, 1.6); place(fx, s808(41.2, 1.2), T_LOGO_END, 0.8)
burn_a = load(os.path.join(LIB, "transitions/burn-transition-12.mp4"))
for b_ in BURN_AT: place(fx, burn_a, b_ - BURN_PEAK, 0.5)
mix = (mus * 0.9 + fx + vox * 1.1)[:int(DUR * SR)]
mix /= np.abs(mix).max() + 1e-6
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", f"{WORK}/mix.wav"], input=(mix * 0.8).astype(np.float32).tobytes(), check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/mix.wav", "-filter_complex",
    "[1:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,asetpts=N/SR/TB,alimiter=limit=0.8:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, flush=True)
