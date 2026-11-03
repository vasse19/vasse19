"""Short from a split-screen interview (« Famille et business musical »): best lines only (~45 s), silences cut,
both people kept on screen (top/bottom halves), name tags, Kali-style neon overlays on the seam, neon captions,
3D hook and conclusion card, then a « LA SUITE SUR YOUTUBE » end screen.
usage: kali_split.py WORK OUT.mp4   (WORK holds src.mp4 and w.json)"""
import sys, os, json, subprocess, numpy as np, cv2, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, typewriter, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SR = 48000
SRC = f"{WORK}/src.mp4"
SWAP = 5.43                       # before: him on top, her below; after: her on top, him below

# ---------- what we keep (source seconds) ----------
KEEP = [(0.10, 9.06), (9.46, 14.10), (15.30, 29.40), (30.05, 33.45), (38.50, 48.95), (65.95, 69.62)]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-ac", "1", "-ar", "16000", f"{WORK}/a16.wav"], check=True)
au, sr16 = sf.read(f"{WORK}/a16.wav"); END = len(au) / sr16
hop = int(0.02 * sr16)
db = 20 * np.log10(np.array([np.sqrt(np.mean(au[i:i + hop] ** 2)) for i in range(0, len(au) - hop, hop)]) + 1e-9)
db = np.convolve(db, np.ones(3) / 3, mode="same")
keep = db >= np.median(db) - 10
i = 0
while i < len(keep):
    if not keep[i]:
        j = i
        while j < len(keep) and not keep[j]: j += 1
        if (j - i) * 0.02 < 0.16: keep[i:j] = True
        else: keep[i:i + 3] = True; keep[max(j - 3, i):j] = True
        i = j
    else: i += 1
mask = np.zeros_like(keep)
for a, b in KEEP: mask[int(a / 0.02):int(b / 0.02)] = True
keep &= mask
runs = []
for k, v in enumerate(keep):
    if v:
        if runs and runs[-1][1] == k: runs[-1][1] = k + 1
        else: runs.append([k, k + 1])
segs = [[a * 0.02, b * 0.02] for a, b in runs if (b - a) * 0.02 >= 0.12]
lst = []
for n, (s0, s1) in enumerate(segs):                 # frame-exact pieces, then concat
    nf = max(1, round((s1 - s0) * FPS)); d = nf / FPS; p = f"{WORK}/s{n:03d}.mov"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s0:.3f}", "-i", SRC, "-frames:v", str(nf), "-t", f"{d:.4f}",
                    "-af", f"afade=t=in:d=0.01,afade=t=out:st={max(d - 0.012, 0):.3f}:d=0.012,apad,atrim=0:{d:.4f}",
                    "-c:v", "libx264", "-crf", "15", "-preset", "fast", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1", p], check=True)
    lst.append(f"file '{p}'"); segs[n][1] = s0 + d
open(f"{WORK}/list.txt", "w").write("\n".join(lst) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/list.txt", "-c", "copy", f"{WORK}/cut.mov"], check=True)
def R(t):
    acc = 0.0
    for a, b in segs:
        if t < a: return acc
        if t < b: return acc + t - a
        acc += b - a
    return acc
DUR = sum(b - a for a, b in segs); CTA = 3.4; TOT = DUR + CTA
N, NV = int(TOT * FPS), int(DUR * FPS)
print(f"{len(segs)} segments, {DUR:.1f}s + {CTA}s end screen", flush=True)

# ---------- transcript fixes ----------
words = sorted(json.load(open(f"{WORK}/w.json")), key=lambda w: w["s"])
def near(t): return min(words, key=lambda w: abs(w["s"] - t))
def ren(t, txt): near(t)["w"] = txt
def rm(t):
    global words; x = near(t); words = [w for w in words if w is not x]
ren(3.20, "après,"); ren(6.72, "discernement !"); ren(10.58, "discernement."); ren(20.79, "tels."); rm(24.82)
ren(26.90, "n'y a"); ren(23.96, "allez être"); ren(68.83, "discernement !")
words = [w for w in words if any(a <= w["s"] < b for a, b in segs)]
for k, w in enumerate(words):
    nxt = words[k + 1]["s"] if k + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP = [(15.9, 16.6)]                              # « dès qu'il y a [?] dedans »: unclear word

# ---------- overlays (source seconds -> cut seconds through R) ----------
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_em = {}
def emoji(ch, size):
    if (ch, size) not in _em:
        f = ImageFont.truetype(EMOJI, 109); im = Image.new("RGBA", (160, 160)); ImageDraw.Draw(im).text((20, 15), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox()); im = im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)
        _em[(ch, size)] = np.asarray(im).astype(np.float32) / 255
    return _em[(ch, size)]
def popk(t, t0): return 1 + 0.3 * max(0, 1 - max(t - t0, 0) / 0.12) ** 2
CARDS = [(0.0, R(3.10), "FAMILLE", "OU BUSINESS ?", "hook"), (R(65.95), DUR, "IL FAUT JUSTE", "DU|DISCERNEMENT", "over")]
card_img = [block(c[2], c[3], 1000, 760) for c in CARDS]
OVER = [  # (start, end, draw) over the dimmed split screen, centred on the seam
    (R(5.95), R(7.40), lambda img, t: (stack(img, t, [(R(5.95), "UN MOT :", WHT)], 110, 820, 0),
                                       typewriter(img, t, R(6.40), "DISCERNEMENT", 170, YEL, 990, 18))),
    (R(17.40), R(21.20), lambda img, t: (stack(img, t, [(R(17.43), "PLUS TES PARENTS", WHT), (R(18.15), "TES AGENTS", YEL)], 130, 880, 160),
                                         [paste(img, emoji("💼", 230), W / 2, 1220, popk(t, R(18.47))) if t >= R(18.47) else None])),
    (R(22.28), R(24.30), lambda img, t: (stack(img, t, [(R(22.28), "LES CONTRATS", WHT)], 150, 960, 0),
                                         [paste(img, emoji("📄", 230), W / 2, 1220, popk(t, R(23.32))) if t >= R(23.32) else None])),
    (R(26.00), R(29.40), lambda img, t: stack(img, t, [(R(26.02), "PLUS DE PAPA", WHT), (R(26.90), "PLUS DE MAMAN", WHT),
                                                       (R(28.06), "AGENT & ARTISTE", YEL)], 130, 800, 165)),
    (R(39.55), R(42.40), lambda img, t: (stack(img, t, [(R(39.56), "2E FACTEUR", WHT)], 130, 880, 0),
                                         [paste(img, emoji("❤️", 260), W / 2, 1140, popk(t, R(41.78))) if t >= R(41.78) else None])),
    (R(44.90), R(48.95), lambda img, t: stack(img, t, [(R(44.96), "L'AMOUR", WHT), (R(45.36), "AUTHENTIQUE", RED)], 170, 880, 200)),
]
def over_at(t): return [o for o in OVER if o[0] <= t < o[1]]
TAGS = lambda t, src_t: (("LE BIG VASS", 0), ("L'ARTISTE", 1)) if src_t < SWAP else (("L'ARTISTE", 0), ("LE BIG VASS", 1))

# ---------- captions ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: G,Anton,140,&H6000E5FF,&H0000E5FF,&H8000C8FF,&H00000000,0,0,0,0,100,100,1,0,1,10,0,5,40,40,0,1
Style: W,Anton,140,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,5,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
key = lambda w: w["w"].lower().strip(",.?!…« » :")
REDW = {"discernement", "contrats", "vicieux", "litiges"}
WHITEW = {"famille", "business", "papa", "maman", "agent", "artiste", "parents", "agents", "authentique", "l'amour"}
blocked = lambda t: any(c[0] <= t < c[1] for c in CARDS) or over_at(t)
for w in words:
    if any(a <= w["s"] < b for a, b in NOCAP): continue
    s0, e0 = R(w["s"]), R(w["e"])
    if blocked(s0): continue
    for b in [c[0] for c in CARDS] + [o[0] for o in OVER]:
        if s0 < b < e0: e0 = b
    col = r"\c&H002A2AFF&\3c&H002A2AFF&" if key(w) in REDW else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if key(w) in WHITEW else "")
    txt = w["w"].upper().strip(",.?!… ") or w["w"]
    pop = r"\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)"
    ass.append(f"Dialogue: 0,{ts(s0)},{ts(max(e0, s0 + 0.15))},G,,0,0,0,,{{\\an5\\pos(540,960){col}\\blur14{pop}}}{txt}")
    ass.append(f"Dialogue: 1,{ts(s0)},{ts(max(e0, s0 + 0.15))},W,,0,0,0,,{{\\an5\\pos(540,960){col.split(chr(92) + '3c')[0] if col else ''}{pop}}}{txt}")
open(f"{WORK}/caps.ass", "w").write("\n".join(ass) + "\n")

# ---------- render ----------
def src_time(t):
    acc = 0.0
    for a, b in segs:
        if t < acc + (b - a): return a + t - acc
        acc += b - a
    return segs[-1][1]
burn = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions/burn-transition-12.mp4"), "-vf", f"scale=-2:{H},crop={W}:{H}",
                       "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
BURN = np.frombuffer(burn, np.uint8).reshape(-1, H, W, 3); BURN_PEAK = 11 / FPS
BURN_AT = [R(65.95), DUR]
logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 520)
YT = emoji("▶️", 230)
cuts_at = [R(a) for a, b in KEEP[1:]]               # chapter joins: small punch-in to hide the jump
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{WORK}/cut.mov", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", f"eq=contrast=1.05:saturation=1.08,vignette=angle=PI/6,ass={WORK}/caps.ass:fontsdir={os.path.dirname(ANTON)},format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY], stdin=subprocess.PIPE)
last = None
for i in range(N):
    t = i / FPS
    if i < NV:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) == W * H * 3: last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        img = last.astype(np.float32) / 255
        z = 1.0
        for c in cuts_at:
            if 0 <= t - c < 0.35: z = 1.0 + 0.06 * (1 - (t - c) / 0.35)
        if z > 1.0: img = cv2.warpAffine(img, cv2.getRotationMatrix2D((W / 2, H / 2), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)
        img[956:964] = (0.15, 0.15, 0.95)                                  # red seam between the two halves
        for txt, half in TAGS(t, src_time(t)):                             # name tags, bottom-left of each half
            im, pad = neon(txt, 76, YEL if txt == "LE BIG VASS" else WHT); y = 90 if half == 0 else 1835; w = im.shape[1] - 2 * pad
            img[int(y - 52):int(y + 52), 24:int(64 + w)] *= 0.35; img[int(y - 52):int(y + 52), 24:32] = (0.15, 0.15, 0.95)
            paste(img, im, 48 + im.shape[1] / 2 - pad, y)
        ov = over_at(t)
        for a, b, fn in ov:
            r = min((t - a) / 0.15, 1); img = img * (1 - 0.5 * r); fn(img, t)
        for ci, c in enumerate(CARDS):
            if c[0] <= t < c[1]:
                k = t - c[0]; img = img * (1 - 0.45 * min(k / 0.2, 1))
                if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.8, 0, 1)
                paste(img, card_img[ci], W / 2, 960, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
    else:                                                                  # end screen: the rest on YouTube
        k = t - DUR; img = bg("red", t) * 0.75
        paste(img, logo, W / 2, 470, 0.85 + 0.15 * min(k / 0.25, 1))
        stack(img, t, [(DUR + 0.25, "LA SUITE", WHT), (DUR + 0.65, "SUR YOUTUBE", RED)], 190, 950, 220)
        if k > 1.0: paste(img, YT, W / 2, 1450, popk(t, DUR + 1.0))
        stack(img, t, [(DUR + 1.5, "LIEN EN BIO", YEL)], 110, 1700, 0)
    for b_ in BURN_AT:
        kb = int(round((t - (b_ - BURN_PEAK)) * FPS))
        if 0 <= kb < len(BURN): img = 1 - (1 - img) * (1 - BURN[kb].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.kill(); dec.wait()

# ---------- sound ----------
def load(p): return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]), np.float32)
sfx = np.zeros(int(TOT * SR) + SR, np.float32)
def place(snd, t, g):
    i0 = int(t * SR)
    if i0 < 0: snd, i0 = snd[-i0:], 0
    n = min(len(snd), len(sfx) - i0); sfx[i0:i0 + n] += snd[:n] * g
whoosh, hit = load(os.path.join(LIB, "sfx/synth-whoosh.wav")), load(os.path.join(LIB, "sfx/synth-hit.wav"))
click, riser = load(os.path.join(LIB, "sfx/synth-click.wav")), load(os.path.join(LIB, "sfx/riser-metallic-transition.mp3"))
burn_a = load(os.path.join(LIB, "transitions/burn-transition-12.mp4"))
for a, b, fn in OVER: place(whoosh, a - 0.2, 0.18); place(hit, a, 0.2)
for c in CARDS: place(hit, c[0], 0.45)
for j, ch in enumerate("DISCERNEMENT"): place(click, R(6.40) + j / 18, 0.22)
for c in cuts_at: place(whoosh, c - 0.2, 0.1)
place(riser, R(65.95) - 2.95, 0.45); place(riser, DUR + 0.25 - 2.95, 0.35)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.5)
place(hit, DUR + 0.25, 0.5); place(hit, DUR + 1.0, 0.35)
sf.write(f"{WORK}/sfx.wav", sfx[:int(TOT * SR)], SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/cut.mov", "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]highpass=f=70,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=1dB,loudnorm=I=-14:TP=-1.5:LRA=7,"
    f"aresample=48000,asetpts=N/SR/TB,apad=whole_dur={TOT:.3f}[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.75:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-t", f"{TOT:.3f}", OUT], check=True)
print("done", OUT, flush=True)
