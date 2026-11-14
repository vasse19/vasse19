"""Video from a voice note (« Ameka Zrai peut aller dans la DA rock / pop punk »), same engine as kali_vocal.py: no face-cam,
his voice drives the pulsing logo and the waveform; Post Malone / Trippie Redd / MGK grid, « Neon Shark vs Pegasus », France,
3D cards « du rap au rock » and « un feat avec Yseult ? », end card. His voice kept as recorded (safety limiter only).
usage: kali_amekazrai.py WORK OUT.mp4   (WORK holds src.mp3, w.json and the images named below)"""
import sys, os, json, subprocess, numpy as np, cv2, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, typewriter, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SR = 48000
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WORK}/src.mp3", "-ac", "1", "-ar", "16000", f"{WORK}/a16.wav"], check=True)
au, sr16 = sf.read(f"{WORK}/a16.wav"); END = len(au) / sr16

# ---------- transcript + his corrections (source seconds) ----------
words = sorted(json.load(open(f"{WORK}/w.json")), key=lambda w: w["s"])
def near(t): return min(words, key=lambda w: abs(w["s"] - t))
def ren(t, txt): near(t)["w"] = txt
def rm(t):
    global words; x = near(t); words = [w for w in words if w is not x]
ren(1.36, "d'Ameka Zrai"); ren(2.32, "featuring"); ren(4.58, "Ameka"); ren(4.66, "Zrai"); ren(12.52, "prêts")
ren(18.08, "comme"); ren(19.12, "Trippie"); ren(19.68, "Redd,"); ren(29.80, "Trippie Redd."); ren(30.36, "Trippie Redd,"); ren(30.92, "en")
ren(32.70, "« Neon"); ren(33.10, "Shark"); ren(33.50, "vs"); ren(33.74, "Pegasus »"); ren(39.68, "Post"); ren(40.00, "Malone,")
ren(49.82, "lui ouvrir"); ren(52.14, "un"); ren(53.58, "feat"); ren(54.24, "Yseult."); rm(54.40); ren(55.44, "Yseult,"); rm(55.68)
ren(60.34, "Vass"); words.append({"w": "vous", "s": 60.58}); words.sort(key=lambda w: w["s"])
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP = [(2.85, 3.30), (59.40, END)]            # featured artist's name unclear; sign-off under the end card

# ---------- silences out (audio only) ----------
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
keep[int(59.40 / 0.02):] = True
keep[int(42.30 / 0.02):int(45.30 / 0.02)] = False        # line 8, unclear: cut
runs = []
for k, v in enumerate(keep):
    if v:
        if runs and runs[-1][1] == k: runs[-1][1] = k + 1
        else: runs.append([k, k + 1])
segs = [[a * 0.02, b * 0.02] for a, b in runs if (b - a) * 0.02 >= 0.12]
segs[-1][1] = END
fc = [f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{n}]" for n, (a, b) in enumerate(segs)]
fc.append("".join(f"[a{n}]" for n in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WORK}/src.mp3", "-filter_complex", ";".join(fc), "-map", "[a]",
                "-ar", str(SR), "-ac", "1", f"{WORK}/voice_cut.wav"], check=True)
def R(t):
    acc = 0.0
    for a, b in segs:
        if t < a: return acc
        if t < b: return acc + t - a
        acc += b - a
    return acc
DUR = sum(b - a for a, b in segs); N = int(DUR * FPS)
print(f"{len(segs)} segments, {DUR:.1f}s (from {END:.1f}s)", flush=True)
voice = sf.read(f"{WORK}/voice_cut.wav")[0]
lvl = np.array([np.sqrt(np.mean(voice[int(i / FPS * SR):int((i + 1) / FPS * SR)] ** 2) + 1e-12) for i in range(N)])
lvl = np.clip(lvl / (np.percentile(lvl, 95) + 1e-9), 0, 1.2)

# ---------- graphics ----------
def popk(t, t0): return 1 + 0.3 * max(0, 1 - max(t - t0, 0) / 0.12) ** 2
def settle(k): return (1.1 - 0.1 * min(max(k, 0) / 0.3, 1) ** 0.4) * (1 + 0.03 * max(k, 0))
def card(path, width, rim):
    im = cv2.imread(path); s = width / im.shape[1]
    c = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4)
    c = cv2.addWeighted(c, 1.4, cv2.GaussianBlur(c, (0, 0), 2), -0.4, 0)
    c[:7] = c[-7:] = c[:, :7] = c[:, -7:] = rim[::-1]
    return glow_rgba(np.dstack([c[..., ::-1].astype(np.float32) / 255, np.ones(c.shape[:2], np.float32)]), rim, 26, 1.1)
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_em = {}
def emoji(ch, size):
    if (ch, size) not in _em:
        f = ImageFont.truetype(EMOJI, 109); im = Image.new("RGBA", (160, 160)); ImageDraw.Draw(im).text((20, 15), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox()); im = im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)
        _em[(ch, size)] = np.asarray(im).astype(np.float32) / 255
    return _em[(ch, size)]
ORA = (255, 121, 0)
POSTM = card(f"{WORK}/postmalone.jpg", 400, (255, 255, 255)); TRIP = card(f"{WORK}/trippie.jpg", 400, (255, 60, 60))
MGK = card(f"{WORK}/mgk.jpg", 400, (255, 190, 60)); NEON = card(f"{WORK}/neonshark.jpg", 620, (150, 90, 255))
TRIPS = card(f"{WORK}/trippie.jpg", 320, (255, 60, 60)); POSTB = card(f"{WORK}/postmalone.jpg", 680, (255, 255, 255))
YSE = card(f"{WORK}/yseult.jpg", 620, (255, 190, 60))
def fr_flag():
    f = np.zeros((200, 300, 3), np.float32); f[:, :100] = (0, 85, 164); f[:, 100:200] = (255, 255, 255); f[:, 200:] = (239, 65, 53)
    return glow_rgba(np.dstack([f / 255, np.ones((200, 300), np.float32)]), (255, 255, 255), 12, 1.2)
FLAG_FR = fr_flag()
logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 210)
END_LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 640)
CARDS = [(0.0, R(4.50), "AMEKA ZRAI", "VERSION ROCK ?", "hook", 700), (R(25.30), R(28.80), "DU RAP", "AU ROCK", "card", 960),
         (R(59.40), DUR, "LE BIG", "VASS", "end", 1370)]
card_img = [block(c[2], c[3], 1040, {"hook": 820, "end": 700}.get(c[4], 1000)) for c in CARDS]

# his clip: square TikTok repost; watermark top-left (start) / bottom-right (later) blurred, account credited
WMBLUR = ("split=3[wa][wb][wc];[wb]crop=210:120:0:0,boxblur=22:3[wl];[wc]crop=210:120:366:456,boxblur=22:3[wr];"
          "[wa][wl]overlay=0:0[wx];[wx][wr]overlay=366:456,")
_vc = {}
def vclip(key, path, src_t):
    st = _vc.get(key)
    if st is None:
        vf = (f"{WMBLUR}split[p][q];[p]scale=-2:{H},crop={W}:{H},boxblur=26,eq=brightness=-0.28[bgv];"
              f"[q]scale={W}:-2[fg];[bgv][fg]overlay=0:(H-h)/2-120")
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(src_t), "-i", path, "-an", "-filter_complex", vf, "-r", str(FPS),
                              "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
        st = _vc[key] = {"p": p, "last": None}
    buf = st["p"].stdout.read(W * H * 3)
    if len(buf) == W * H * 3: st["last"] = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    return st["last"].copy()
def credit(img, handle):
    im, _ = neon(f"SOURCE TIKTOK : {handle}", 40, WHT); paste(img, im, W / 2, 1890, 1.0, 0.85)

SCENES = [  # (start, end, name) in source seconds; every moment has one
    (0.0, 4.50, "hook"), (4.50, 13.40, "da"), (13.40, 22.50, "us"), (22.50, 25.30, "debut"), (25.30, 28.80, "card"),
    (28.80, 39.10, "trippie"), (39.10, 45.30, "post"), (45.30, 51.30, "portes"), (51.30, 59.40, "yseult"), (59.40, END + 1, "end")]
SC = [(R(a), R(b), n) for a, b, n in SCENES]
def scene(t, i):
    for a, b, n in SC:
        if a <= t < b: return a, n
    return SC[-1][0], SC[-1][2]
def draw(name, t, k):
    img = bg("black" if name in ("us", "portes") else "red", t)
    if name == "da":
        typewriter(img, t, R(4.58), "AMEKA ZRAI", 170, WHT, 330, 12)
        stack(img, t, [(R(5.38), "PEUT ALLER DANS", WHT), (R(6.02), "CETTE DA", YEL)], 120, 560, 150)
        stack(img, t, [(R(10.04), "ROCK", RED), (R(10.44), "× POP PUNK", (255, 120, 200))], 190, 950, 220)
        stack(img, t, [(R(11.96), "VOUS N'ÊTES PAS PRÊTS", WHT)], 95, 1430, 0)
    elif name == "us":
        stack(img, t, [(R(15.26), "ÇA M'A FAIT PENSER À…", WHT)], 100, 230, 0)
        for im_, t0, x_, y_, lbl in [(POSTM, 18.24, 300, 660, "POST MALONE"), (TRIP, 19.12, 780, 660, "TRIPPIE REDD"), (MGK, 20.48, 540, 1220, "MGK")]:
            if t >= R(t0):
                paste(img, im_, x_, y_, popk(t, R(t0)))
                lab, _ = neon(lbl, 64, YEL); paste(img, lab, x_, y_ + im_.shape[0] / 2 - 10)
    elif name == "debut":
        stack(img, t, [(R(23.14), "AU TOUT DÉBUT", WHT), (R(25.14), "DU RAP", YEL)], 150, 700, 200)
    elif name == "trippie":
        paste(img, NEON, W / 2, 900, settle(min(k, 1.5)))
        if t >= R(29.80): paste(img, TRIPS, 830, 520, popk(t, R(29.80)))
        stack(img, t, [(R(31.00), "EN 2021", WHT)], 130, 260, 0)
        typewriter(img, t, R(32.70), "NEON SHARK VS PEGASUS", 85, (150, 120, 255), 1300, 20)
        stack(img, t, [(R(35.42), "100 % ROCK & POP PUNK", RED), (R(38.56), "IL A FAIT LE TAF", GRN)], 95, 1430, 120)
    elif name == "post":
        paste(img, POSTB, W / 2, 900, settle(min(k, 1.5)))
        stack(img, t, [(R(39.68), "POST MALONE", WHT)], 150, 260, 0)
        stack(img, t, [(R(40.66), "VOUS CONNAISSEZ", WHT), (R(41.14), "LA SUITE", YEL)], 110, 1340, 140)
    elif name == "portes":
        stack(img, t, [(R(46.92), "UN PUBLIC", WHT), (R(47.48), "PLUS LARGE", YEL)], 150, 330, 185)
        if t >= R(48.52): paste(img, FLAG_FR, W / 2, 800, 1.5 * popk(t, R(48.52)))
        stack(img, t, [(R(48.52), "EN FRANCE", WHT)], 130, 1020, 0)
        stack(img, t, [(R(49.82), "ÇA VA LUI OUVRIR", WHT), (R(50.86), "DES PORTES", GRN)], 120, 1250, 150)
    elif name == "yseult":
        paste(img, YSE, W / 2, 1000, settle(min(k, 1.5)))
        typewriter(img, t, R(53.50), "UN FEAT AVEC", 120, WHT, 230, 14)
        stack(img, t, [(R(54.24), "YSEULT ?", GOLD)], 160, 400, 0)
        stack(img, t, [(R(57.36), "ÇA PEUT CRÉER QUELQUE CHOSE", YEL)], 80, 1500, 0)
    elif name == "card":
        img = bg("red", t) * 0.6
    return img

# ---------- captions (neon Anton, one word at a time, y 1660) ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: G,Anton,150,&H6000E5FF,&H0000E5FF,&H8000C8FF,&H00000000,0,0,0,0,100,100,1,0,1,10,0,5,40,40,0,1
Style: W,Anton,150,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,4,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
key = lambda w: w["w"].lower().strip(",.?!…«» :")
WHITE = {"ameka", "zrai", "post", "malone", "trippie", "redd", "mgk", "neon", "shark", "pegasus", "yseult", "2021", "france"}
REDW = {"rock", "punk", "pop"}
in_card = lambda t: any(c[0] <= t < c[1] for c in CARDS)
for w in words:
    if any(a <= w["s"] < b for a, b in NOCAP) or not any(a <= w["s"] < b for a, b in segs): continue
    s0, e0 = R(w["s"]), R(w["e"])
    if in_card(s0): continue
    col = r"\c&H002A2AFF&\3c&H002A2AFF&" if key(w) in REDW else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if key(w) in WHITE else "")
    txt = w["w"].upper().strip(",.?!… ") or w["w"]
    pop = r"\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)"
    ass.append(f"Dialogue: 0,{ts(s0)},{ts(max(e0, s0 + 0.15))},G,,0,0,0,,{{\\an5\\pos(540,1660){col}\\blur14{pop}}}{txt}")
    ass.append(f"Dialogue: 1,{ts(s0)},{ts(max(e0, s0 + 0.15))},W,,0,0,0,,{{\\an5\\pos(540,1660){col.split(chr(92) + '3c')[0] if col else ''}{pop}}}{txt}")
open(f"{WORK}/caps.ass", "w").write("\n".join(ass) + "\n")

# ---------- render ----------
burn = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions/burn-transition-12.mp4"), "-vf", f"scale=-2:{H},crop={W}:{H}",
                       "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
BURN = np.frombuffer(burn, np.uint8).reshape(-1, H, W, 3); BURN_PEAK = 11 / FPS
BURN_AT = [R(4.50), R(13.40), R(28.80), R(51.30)]
VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", f"noise=alls=3:allf=t+u,ass={WORK}/caps.ass:fontsdir={os.path.dirname(ANTON)},format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY], stdin=subprocess.PIPE)
bars = 48
for i in range(N):
    t = i / FPS; a, name = scene(t, i); k = t - a
    img = draw(name, t, k)
    if k < 0.07 and name != "end": img = np.clip(img + (0.07 - k) / 0.07 * 0.6, 0, 1)
    for ci, c in enumerate(CARDS):
        if not (c[0] <= t < c[1]): continue
        kk = t - c[0]
        if c[4] == "end": img = bg("red", t) * 0.55; paste(img, END_LOGO, W / 2, 700, min(kk / 0.25, 1) * 0.15 + 0.85)
        elif c[4] == "hook": img = bg("red", t) * 0.8; [paste(img, im_, x_, 1250, 0.8) for im_, x_ in ((POSTM, 220), (TRIP, 540), (MGK, 860))]
        sc = 0.55 + 0.55 * min(kk / 0.12, 1) - 0.1 * min(max(kk - 0.12, 0) / 0.1, 1)
        paste(img, card_img[ci], W / 2, c[5], sc)
    if name != "end":
        lv = lvl[i]                                                  # presenter: his logo pulses with his voice
        cv2.circle(img, (120, 120), int(108 + 14 * lv), (0.25, 0.75, 1.0), 5, cv2.LINE_AA)
        paste(img, logo, 120, 120, 1.0 + 0.06 * lv)
        for b in range(bars):                                        # waveform under the captions
            j = min(N - 1, max(0, i - bars // 2 + b)); hgt = int(8 + 70 * lvl[j] * (0.6 + 0.4 * np.sin(b * 1.7 + t * 9) ** 2))
            x = int(W / 2 + (b - bars / 2) * 18); img[1780 - hgt // 2:1780 + hgt // 2, x:x + 9] = (0.25, 0.85, 1.0)
    for b_ in BURN_AT:
        kb = int(round((t - (b_ - BURN_PEAK)) * FPS))
        if 0 <= kb < len(BURN): img = 1 - (1 - img) * (1 - BURN[kb].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if i % 300 == 0: print(f"frame {i}/{N}", flush=True)
enc.stdin.close(); enc.wait()
for st in _vc.values(): st["p"].stdout.close(); st["p"].kill(); st["p"].wait()

# ---------- sound ----------
def load(p): return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]), np.float32)
sfx = np.zeros(int(DUR * SR) + SR, np.float32)
def place(snd, t, g):
    i0 = int(t * SR)
    if i0 < 0: snd, i0 = snd[-i0:], 0
    n = min(len(snd), len(sfx) - i0); sfx[i0:i0 + n] += snd[:n] * g
whoosh = load(os.path.join(LIB, "sfx/synth-whoosh.wav")); hit = load(os.path.join(LIB, "sfx/synth-hit.wav"))
click = load(os.path.join(LIB, "sfx/synth-click.wav")); riser = load(os.path.join(LIB, "sfx/riser-metallic-transition.mp3"))
burn_a = load(os.path.join(LIB, "transitions/burn-transition-12.mp4"))
for a, b, n in SC[1:]: place(whoosh, a - 0.2, 0.2)
for c in CARDS: place(hit, c[0], 0.45)
for t0, txt, cps in [(R(4.58), "AMEKA ZRAI", 12), (R(32.70), "NEON SHARK VS PEGASUS", 20), (R(53.50), "UN FEAT AVEC", 14)]:
    for j, ch in enumerate(txt):
        if ch != " ": place(click, t0 + j / cps, 0.22)
for t0 in (R(10.04), R(18.24), R(19.12), R(20.48), R(48.52), R(54.24)): place(hit, t0, 0.25)
place(riser, R(25.30) - 2.95, 0.45); place(riser, R(54.24) - 2.95, 0.4)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.5)
sf.write(f"{WORK}/sfx.wav", sfx[:int(DUR * SR)], SR)
# voice as recorded (he asked to keep his sound): no compressor or loudness change, safety limiter only
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/voice_cut.wav", "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, flush=True)
