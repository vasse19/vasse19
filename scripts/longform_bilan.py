"""YouTube long-form edit (16:9), « Bilan, la polémique et la suite » (8 min source): hook « je suis un phénix », his intro kept,
jump cuts + breaths between sentences, repeated « comment vous dire » cut, 9 chapter cards, BIG keyword text (he asked for
large plain text on the important words), burn transitions, end screen, denoised voice at -14 LUFS."""
import json, sys, subprocess, os, numpy as np, cv2
import soundfile as sf
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from fx3d import text3d

SRC, WORK, OUT, LOGO = sys.argv[1:5]
W, H, FPS = 1920, 1080, 30
INTRO_END = 2.75          # « Yo tout le monde… c'est le Big Vass pour vous servir », kept whole
BODY_END = 486.1          # « ciao, peace » ends the source
ENDSCREEN = 15.0

words = [w for w in json.load(open(f"{WORK}/words.json")) if "<unk>" not in w["w"] and w["w"] not in ("?", "!")]
key = lambda w: w["w"].lower().strip(",.?!…")
def find(sub, t, span=6.0):
    """Start time of the word containing `sub` closest to source time t."""
    c = [w for w in words if sub in key(w) and abs(w["s"] - t) < span]
    if not c: raise ValueError(f"{sub} near {t}")
    return min(c, key=lambda w: abs(w["s"] - t))["s"]

# ---------- edit decision list (source time) ----------
HOOK = [(207.85, 210.30)]                          # « je suis un phénix. Travail et persévérance. »
DROP = [(9.48, 9.78),                              # « on a » stutter
        (20.45, 21.45),                            # « comment vous dire en fait, »
        (69.25, 70.30),                            # « Comment vous dire ? En fait, »
        (87.85, 90.65),                            # « Et puis, comment vous dire en fait, d'être chouette venu, »
        (220.55, 222.30)]                          # « même 1, hein. 1, ouais, »

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-ac", "1", "-ar", "16000", f"{WORK}/edl.wav"], check=True)
au, sr = sf.read(f"{WORK}/edl.wav"); hop = int(0.02 * sr)
db = 20 * np.log10(np.array([np.sqrt(np.mean(au[i:i + hop] ** 2)) for i in range(0, len(au) - hop, hop)]) + 1e-9)
db = np.convolve(db, np.ones(3) / 3, mode="same")
speech = db[int(INTRO_END / 0.02):int(BODY_END / 0.02)]
keep = db >= np.median(speech) - 10
i = 0
while i < len(keep):
    if not keep[i]:
        j = i
        while j < len(keep) and not keep[j]: j += 1
        if (j - i) * 0.02 < 0.16: keep[i:j] = True
        else: keep[i:i + 3] = True; keep[max(j - 3, i):j] = True
        i = j
    else: i += 1
keep[:int(INTRO_END / 0.02)] = False
# breaths between sentences: quieter than the voice, no low frequencies, between two words
fr_ = au[:len(db) * hop].reshape(len(db), hop) * np.hanning(hop)
sp_ = np.abs(np.fft.rfft(fr_, axis=1)) ** 2; fq_ = np.fft.rfftfreq(hop, 1 / sr)
lfr = sp_[:, (fq_ > 80) & (fq_ < 1000)].sum(1) / (sp_.sum(1) + 1e-12)
MED = np.median(speech); voiced = (db > MED - 8) & (lfr > 0.6); loud = db > MED - 6
nb = 0
for a_, b_ in zip(words, words[1:]):
    if a_["s"] < INTRO_END or a_["s"] >= 481.4: continue
    i0, i1 = int(a_["s"] / 0.02), int(b_["s"] / 0.02)
    if i1 - i0 < 6: continue
    v = np.nonzero(voiced[i0:i1])[0]; ve = i0 + (v[-1] + 1 if len(v) else 3)
    on = i1
    while on > ve and loud[on - 1]: on -= 1
    c0, c1 = ve + 4, on - 3
    if c1 - c0 < 5: continue
    seg = slice(c0, c1)
    if np.sum((db[seg] > MED - 22) & (lfr[seg] < 0.65)) >= 4 or a_["w"][-1] in ",.?!…":
        keep[c0:c1] = False; nb += 1
print(f"{nb} breaths / pauses cut", flush=True)
keep[int(481.4 / 0.02):int(BODY_END / 0.02)] = True        # sign-off kept whole
keep[int(BODY_END / 0.02):] = False
for a0, b0 in DROP: keep[int(a0 / 0.02):int(b0 / 0.02)] = False
runs = []
for k, v in enumerate(keep):
    if v:
        if runs and runs[-1][1] == k: runs[-1][1] = k + 1
        else: runs.append([k, k + 1])
body = [[a0 * 0.02, b0 * 0.02] for a0, b0 in runs if (b0 - a0) * 0.02 >= 0.12]
EDL = [list(h) for h in HOOK] + [[0.0, INTRO_END]] + body
# snap every cut to the 30 fps frame grid so each segment's audio and video have the same length
# (otherwise the concatenated file drifts out of sync over ~90 segments)
EDL = [[round(a * FPS) / FPS, round(b * FPS) / FPS] for a, b in EDL]
EDL = [s_ for s_ in EDL if s_[1] - s_[0] >= 2 / FPS]
HOOK_DUR = sum(b - a for a, b in HOOK)

def remap(t):
    """Source time (body or intro) -> output time; returns None if t was cut."""
    acc = 0.0
    for a, b in EDL[len(HOOK):]:
        if a <= t < b: return HOOK_DUR + acc + t - a
        acc += b - a
    return None
def remap_near(t):
    acc, best = 0.0, None
    for a, b in EDL[len(HOOK):]:
        if t < a: return HOOK_DUR + acc if best is None else best
        if t < b: return HOOK_DUR + acc + t - a
        acc += b - a
        best = HOOK_DUR + acc
    return best
CONTENT = sum(b - a for a, b in EDL)
DUR = CONTENT + ENDSCREEN
N = int(DUR * FPS); ft = np.arange(N) / FPS
print(f"{len(EDL)} segments, content {CONTENT:.1f}s + end screen {ENDSCREEN:.0f}s (source {BODY_END:.0f}s)", flush=True)

# one small file per segment, then the concat demuxer: a single filter graph with ~90 trims of a long
# source buffers decoded frames and gets killed for lack of memory
CUT = f"{WORK}/cut.mov"
segdir = f"{WORK}/segs"; os.makedirs(segdir, exist_ok=True)
with open(f"{segdir}/list.txt", "w") as lst:
    for i, (a, b) in enumerate(EDL):
        n = round((b - a) * FPS); d = n / FPS          # exact frame count; audio cut to the same length
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", SRC, "-frames:v", str(n), "-t", f"{d:.6f}",
                        "-af", f"afade=t=in:d=0.01,afade=t=out:st={max(d - 0.012, 0):.3f}:d=0.012,apad,atrim=0:{d:.6f}", "-r", "30",
                        "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000",
                        f"{segdir}/s{i:03d}.mov"], check=True)
        lst.write(f"file 's{i:03d}.mov'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{segdir}/list.txt", "-c", "copy", CUT], check=True)
real = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", CUT]))
print(f"cut file {real:.2f}s (EDL {CONTENT:.2f}s)", flush=True)
subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(__file__), "faces_any.py"), CUT, f"{WORK}/faces.json"], check=True, capture_output=True)
SW, SH = 1280, 720
f = np.array(json.load(open(f"{WORK}/faces.json")))
fx, fy = np.interp(ft, f[:, 0], f[:, 1]), np.interp(ft, f[:, 0], f[:, 2])
ker = np.ones(31) / 31
sm = lambda v: np.convolve(np.pad(v, 15, mode="edge"), ker, mode="valid")
fx, fy = sm(sm(fx)), sm(sm(fy))

# ---------- keywords (source time, text, colour): yellow default, W = names, R = strong ----------
KW = [("10", 7.5, "10 000 ABONNÉS", "R"), ("120", 10.4, "120 000 SUR TIKTOK", "R"), ("18", 15.0, "18 000", "R"),
      ("changement", 22.2, "DU CHANGEMENT", "Y"), ("concerts", 34.0, "DES CONCERTS", "Y"), ("culture", 50.0, "LA CULTURE", "Y"),
      ("polémique", 61.6, "LA POLÉMIQUE", "R"), ("médias", 66.4, "MÉDIA OU ULTRA ?", "Y"), ("bidjan", 71.6, "ABIDJAN", "W"),
      ("2024", 77.7, "DÉCEMBRE 2024", "W"), ("imra", 105.4, "HIMRA", "W"), ("didi", 108.8, "DIDI B", "W"),
      ("insult", 119.5, "INSULTÉ", "R"), ("live", 129.0, "LE LIVE", "Y"), ("jamais", 152.5, "JAMAIS DIT ÇA", "R"),
      ("rien", 169.5, "HIMRA OU RIEN", "R"), ("propagande", 201.0, "LA PROPAGANDE", "R"), ("1000", 211.8, "−1000 ABONNÉS", "R"),
      ("didi", 219.9, "MÊME DIDI B", "W"), ("2027", 236.9, "OBJECTIF 2027", "Y"), ("vlogs", 240.8, "CONCERTS · VLOGS", "Y"),
      ("new", 246.0, "LA NEW WAVE", "W"), ("interview", 247.2, "INTERVIEWS", "Y"), ("hypocrite", 266.0, "« HYPOCRITE »", "R"),
      ("haters", 300.6, "HATERS", "R"), ("anciens", 309.0, "D'ANCIENS FANS", "Y"), ("toxique", 336.7, "UN GAME TOXIQUE", "R"),
      ("musique", 372.3, "JE PARLE DE LA MUSIQUE", "Y"), ("120", 381.5, "120 000", "R"), ("youtube", 395.3, "10 000 SUR YOUTUBE", "W"),
      ("qualité", 421.9, "QUALITÉ & QUANTITÉ", "Y"), ("persévérance", 453.0, "TRAVAIL · PERSÉVÉRANCE", "Y"),
      ("ivoire", 470.0, "CÔTE D'IVOIRE", "W"), ("ouf", 478.0, "ÇA VA LE FAIRE DE OUF", "R")]
keywords = []
for sub, t, txt, col in KW:
    try: s0 = remap(find(sub, t))
    except ValueError as e: print("keyword skipped:", e, flush=True); continue
    if s0 is not None: keywords.append((s0, txt, col))
keywords.sort()

# ---------- chapters (3D cards) and photo B-roll (output time) ----------
CHAPTERS = [(22.9, "NOUVELLE", "DA"), (58.6, "LA", "POLÉMIQUE"), (126.0, "LE", "LIVE"), (166.5, "HIMRA", "OU RIEN ?"),
            (234.0, "OBJECTIF", "2027"), (261.0, "LES", "HATERS"), (333.0, "UN GAME", "TOXIQUE"), (378.0, "TIKTOK", "& YOUTUBE"),
            (450.0, "MERCI", "À VOUS")]
CARDS = [(0.0, 2.2, "JE SUIS", "UN PHÉNIX", "hook", 760)]
for t, top, bot in CHAPTERS:
    s0 = remap_near(t); CARDS.append((s0, s0 + 1.8, top, bot, "card", 540))
CARDS.append((CONTENT, DUR, "LE BIG", "VASS", "end", 640))
CARDS.sort()
def in_card(t): return any(c[0] <= t < c[1] for c in CARDS)
BROLL = []
def in_broll(t):
    for a, b, n in BROLL:
        if a <= t < b: return (a, b, n)
    return None
def cover(img, w, h):
    s = max(w / img.shape[1], h / img.shape[0]); r = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    y = (r.shape[0] - h) // 2; x = (r.shape[1] - w) // 2
    return r[y:y + h, x:x + w]
def card_layer(path, height):
    im = cv2.imread(path)
    bg = cv2.GaussianBlur(cover(im, W, H), (0, 0), 30).astype(np.float32) / 255 * 0.45
    s_ = height / im.shape[0]
    c = cv2.resize(im, None, fx=s_, fy=s_, interpolation=cv2.INTER_LANCZOS4)
    c[:6] = c[-6:] = c[:, :6] = c[:, -6:] = (66, 197, 245)
    return bg, np.dstack([c[..., ::-1].astype(np.float32) / 255, np.ones(c.shape[:2], np.float32)])
PH = {}

def block(top, bot, width, maxh):
    lines = [text3d(l, 220, "chrome", 30) for l in top.split("|")] + [text3d(l, 210, "red", 30) for l in bot.split("|")]
    im = Image.new("RGBA", (max(l.width for l in lines) + 40, sum(l.height for l in lines) - 110 * (len(lines) - 1)))
    y = 0
    for l in lines:
        im.alpha_composite(l, ((im.width - l.width) // 2, y)); y += l.height - 110
    im = im.rotate(5, expand=True, resample=Image.BICUBIC)
    sc = min(width / im.width, maxh / im.height)
    return np.asarray(im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)).astype(np.float32) / 255
card_img = [block(c[2], c[3], {"hook": 900, "end": 760}.get(c[4], 1100), {"hook": 420, "end": 420}.get(c[4], 760)) for c in CARDS]
def rgba(path, width):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED); s = width / im.shape[1]
    return cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA).astype(np.float32)[..., [2, 1, 0, 3]] / 255
logo = rgba(LOGO, 420)
def paste(dst, img, cx, cy, scale=1.0):
    if scale != 1.0: img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = img.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    src = img[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4]
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a

# ---------- shots: change framing every 5-8 s at phrase ends (long-form pace) ----------
outw = sorted(({"w": w["w"], "s": remap(w["s"])} for w in words if remap(w["s"]) is not None), key=lambda w: w["s"])
cuts = [0.0, HOOK[0][1] - HOOK[0][0], HOOK_DUR, HOOK_DUR + INTRO_END]
last = cuts[-1]
for w in outw:
    if w["s"] <= last: continue
    if (w["w"][-1] in ",.?" and w["s"] - last > 5.0) or w["s"] - last > 8.0:
        last = round(w["s"] + 0.15, 2); cuts.append(last)
CYCLE = ["WIDE", "MED", "TIGHT", "MED"]
SHOTS = [(c, CYCLE[i % 4]) for i, c in enumerate(cuts)]
def shot_at(t):
    m = SHOTS[0][1]
    for s_, mm in SHOTS:
        if t >= s_: m = mm
    return m
z = np.ones(N)
def punch(t0, amt, hold=0.3, rel=0.45):
    a = np.clip((ft - t0) / 0.07, 0, 1); a = a * a * (3 - 2 * a)
    r = np.clip((ft - t0 - hold) / rel, 0, 1); r = r * r * (3 - 2 * r)
    return amt * a * (1 - r)
for s0, _, col in keywords:
    if col == "R": z += punch(s0, 0.06)
for c, _ in SHOTS[1:]: z += punch(c - 0.001, 0.04, 0.0, 0.25)
shake = np.zeros((N, 2)); rng = np.random.default_rng(10)
for c in CARDS:
    m = (ft >= c[0]) & (ft < c[0] + 0.3)
    shake[m] = rng.normal(0, 10, (m.sum(), 2)) * np.linspace(1, 0, m.sum())[:, None]
def crop_rect(i):
    m = shot_at(ft[i])
    in_intro = HOOK_DUR <= ft[i] < HOOK_DUR + INTRO_END
    zz = z[i] * (1.0 if in_intro else {"WIDE": 1.0, "MED": 1.22, "TIGHT": 1.45}[m])
    ch = SH / zz; cw = ch * W / H
    return np.clip(fx[i] - cw / 2, 0, SW - cw), np.clip(fy[i] - ch * 0.42, 0, SH - ch), cw, ch

# ---------- keyword captions ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
COL = {"Y": "", "W": r"\c&H00FFFFFF&", "R": r"\c&H002A2AFF&"}
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: K,Anton,230,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,2,0,1,12,8,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
for i, (s0, txt, col) in enumerate(keywords):
    if in_card(s0) or in_broll(s0): continue
    e = s0 + 1.8
    if i + 1 < len(keywords): e = min(e, keywords[i + 1][0] - 0.05)
    for c in CARDS:
        if s0 < c[0] < e: e = c[0]
    ass.append(f"Dialogue: 0,{ts(s0)},{ts(e)},K,,0,0,0,,{{\\an5\\pos(960,840){COL[col]}\\fscx70\\fscy70\\t(0,100,\\fscx108\\fscy108)\\t(100,170,\\fscx100\\fscy100)}}{txt}")
open(f"{WORK}/caps.ass", "w").write("\n".join(ass) + "\n")

# ---------- chapters list for the YouTube description ----------
def mmss(t): return f"{int(t // 60)}:{int(t % 60):02d}"
lines = ["0:00 Je suis un phénix", f"{mmss(HOOK_DUR)} Intro"] + [f"{mmss(remap_near(t))} {top.title()} {bot.replace('|', ' ').capitalize()}" for t, top, bot in CHAPTERS] + [f"{mmss(CONTENT)} Fin"]
open(f"{WORK}/chapitres.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines), flush=True)

# ---------- sound: SFX bed, burn transitions, end-screen music ----------
def synth(args, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", args, "-ac", "1", "-ar", "48000", path], check=True)
    return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"]), np.float32)
whoosh = synth("anoisesrc=d=0.45:c=pink:a=0.9,highpass=f=600,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.18:d=0.27", f"{WORK}/whoosh.wav")
hit = synth("sine=f=52:d=0.7,volume=1.4,afade=t=out:st=0.05:d=0.65", f"{WORK}/hit.wav")
sfx = np.zeros(int(DUR * 48000) + 48000, np.float32)
def place(snd, t, g):
    i = int(max(t, 0) * 48000); sfx[i:i + len(snd)] += snd[:len(sfx) - i] * g
for c, _ in SHOTS[1:]: place(whoosh, c - 0.2, 0.06)
for a, b, n in BROLL: place(whoosh, a - 0.2, 0.2)
for c in CARDS[1:]: place(hit, c[0], 0.4)
BURN_AT = [c[0] for c in CARDS if c[4] == "card" and c[2] in [ch[1] for ch in CHAPTERS]] + [HOOK_DUR, CONTENT]
burn_snd = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", f"{WORK}/burn.mp4", "-f", "f32le", "-ac", "1", "-ar", "48000", "-"]), np.float32)
for b_ in BURN_AT: place(burn_snd, b_ - 0.39, 0.6)
# end screen: his intro music, faded
place(hit, CONTENT, 0.45)                                   # no music intro in this source: a soft A-minor pad under the end screen
pad = synth(f"aevalsrc='0.25*sin(2*PI*110*t)+0.35*sin(2*PI*220*t)+0.22*sin(2*PI*261.6*t)+0.2*sin(2*PI*329.6*t)':d={ENDSCREEN},"
            f"tremolo=f=0.5:d=0.4,lowpass=f=1200,afade=t=in:d=1.5,afade=t=out:st={ENDSCREEN - 3}:d=3", f"{WORK}/pad.wav")
place(pad, CONTENT, 0.25)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", "-", f"{WORK}/sfx.wav"], input=sfx[:int(DUR * 48000)].tobytes(), check=True)

# ---------- render ----------
bdec = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WORK}/burn.mp4", "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
BURN = np.frombuffer(bdec, np.uint8).reshape(-1, H, W, 3)
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", CUT, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
VF = f"unsharp=5:5:0.5,eq=contrast=1.06:saturation=1.08,vignette=angle=PI/6,noise=alls=3:allf=t+u,ass={WORK}/caps.ass:fontsdir={os.path.expanduser('~/.fonts')},format=yuv420p"
VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", VF, "-c:v", "libx264", "-preset", "medium", "-b:v", "1600k", "-maxrate", "2600k", "-bufsize", "5200k", VIDEO_ONLY], stdin=subprocess.PIPE)   # ~95 MB: under GitHub's 100 MB
FR = SW * SH * 3
last_frame = None
endbg = None
for i in range(N):
    t = ft[i]
    if t < CONTENT:
        buf = dec.stdout.read(FR)
        if len(buf) == FR: last_frame = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
        fr = last_frame
        br = in_broll(t)
        if br:
            a, b, n = br; bgi, card = PH[n]; k = t - a
            img = bgi.copy()
            paste(img, card, W / 2, H / 2, (1.12 - 0.12 * min(k / 0.3, 1) ** 0.4) * (1 + 0.03 * k / (b - a)))
            if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.5, 0, 1)
        else:
            x0, y0, cw, ch = crop_rect(i)
            x0 += shake[i, 0] * cw / W; y0 += shake[i, 1] * ch / H
            M = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
            img = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
    else:
        if endbg is None:
            endbg = cv2.GaussianBlur(cv2.resize(last_frame, (W, H)), (0, 0), 25).astype(np.float32) / 255 * 0.35
        img = endbg.copy()
        # YouTube end-screen element slots (videos are placed over these in YouTube Studio)
        k = t - CONTENT
        a = min(k / 0.6, 1)
        for (x, y) in ((1130, 250), (1130, 610)):
            cv2.rectangle(img, (x, y), (x + 620, y + 349), (0.26 * a, 0.77 * a, 0.96 * a), 4)
        paste(img, logo, 470, 330, 0.9 + 0.1 * min(k / 0.4, 1))
    for ci, c in enumerate(CARDS):
        if not (c[0] <= t < c[1]): continue
        k = t - c[0]
        if c[4] == "card":
            bgc = cv2.GaussianBlur(img, (0, 0), 22); L = bgc.mean(axis=2, keepdims=True)
            img = np.clip(L * np.array([0.12, 0.12, 0.9]) * 1.3 + bgc * 0.15, 0, 1)
        elif c[4] == "hook":
            img = img * (1 - 0.25 * min(k / 0.2, 1))
        if k < 0.07 and c[4] != "end": img = np.clip(img + (0.07 - k) / 0.07 * 0.8, 0, 1)
        s = 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1)
        cx = 470 if c[4] == "end" else W / 2
        paste(img, card_img[ci], cx + shake[i, 0], (c[5] + 250 if c[4] == "end" else c[5]) + shake[i, 1], s)
    for b_ in BURN_AT:
        k = int(round((t - (b_ - 0.39)) * FPS))
        if 0 <= k < len(BURN):
            img = 1 - (1 - img) * (1 - BURN[k].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()
dec.stdout.close(); dec.kill(); dec.wait()
# voice as recorded (he asked to keep his sound as it was): no denoise, compressor or loudness change, only a safety limiter
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", CUT, "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]aresample=48000,asetpts=N/SR/TB,apad[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[fx][vo]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, len(SHOTS), "shots", flush=True)
