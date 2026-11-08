"""Video from a voice note (Burna Boy, « Odogwu »): no face-cam, full motion design in the Kali Muscle style.
His voice (silences cut, -14 LUFS) drives a pulsing Monsieur Vass logo and a waveform; photos, covers and his clips
follow what he says; neon word captions all along; burns, risers, clicks; 3D hook and cards; end card.
Clip watermarks are blurred and the account credited on screen.
usage: kali_vocal.py WORK OUT.mp4   (WORK holds src.mp3, w.json and the images/clips named below)"""
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
rm(7.10)
rm(0.48); ren(3.44, "Burna Boy,"); ren(6.48, "Burna Boy ?"); rm(7.12); ren(13.13, "Burna Boy"); ren(14.57, "sale.")
ren(17.96, "cérémonies"); ren(22.28, "son"); ren(22.76, "officiel"); ren(28.22, "quelques jours"); ren(32.60, "Burna"); ren(32.92, "Boy ?")
ren(33.49, "Burna Boy,"); ren(41.62, "il"); ren(50.22, "dise quoi"); ren(52.08, "il a"); rm(58.28); ren(59.16, "Burna Boy ?"); rm(59.88)
ren(62.02, "Odogwu."); ren(52.64, "Stade"); ren(53.52, "Stade")
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP = [(35.80, 37.90), (62.90, END)]          # « il est trop [loin ?] »; sign-off under the end card

# ---------- silences out (audio only) ----------
hop = int(0.02 * sr16)
db = 20 * np.log10(np.array([np.sqrt(np.mean(au[i:i + hop] ** 2)) for i in range(0, len(au) - hop, hop)]) + 1e-9)
db = np.convolve(db, np.ones(3) / 3, mode="same")
keep = db >= np.median(db) - 7
i = 0
while i < len(keep):
    if not keep[i]:
        j = i
        while j < len(keep) and not keep[j]: j += 1
        if (j - i) * 0.02 < 0.10: keep[i:j] = True
        else: keep[i:i + 2] = True; keep[max(j - 2, i):j] = True
        i = j
    else: i += 1
keep[int(62.9 / 0.02):] = True
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
B_PORT = card(f"{WORK}/burna1.jpg", 760, (255, 190, 60))
B_SHAK = card(f"{WORK}/burna2.jpg", 760, (255, 160, 60))
B_BW = card(f"{WORK}/burna3.jpg", 960, (255, 255, 255))
B_WC = card(f"{WORK}/burna4.jpg", 940, (90, 200, 255))
B_FAM = card(f"{WORK}/burna5.jpg", 640, (255, 110, 170))
logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 210)
END_LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 640)
CARDS = [(R(33.10), R(35.80), "C'EST UN AUTRE", "NIVEAU", "card", 960), (R(60.15), R(62.90), "ON L'APPELLE", "ODOGWU", "card", 960),
         (R(62.90), DUR, "LE BIG", "VASS", "end", 1370)]
card_img = [block(c[2], c[3], 1040, {"hook": 820, "end": 700}.get(c[4], 1000)) for c in CARDS]

# his clip: square TikTok repost; watermark top-left (start) / bottom-right (later) blurred, account credited
WMBLUR = ("split=3[wa][wb][wc];[wb]crop=210:120:0:0,boxblur=22:3[wl];[wc]crop=210:120:366:456,boxblur=22:3[wr];"
          "[wa][wl]overlay=0:0[wx];[wx][wr]overlay=366:456,")
_vc = {}
def vclip(key, path, src_t):
    st = _vc.get(key)
    if st is None:
        vf = (f"split[p][q];[p]scale=-2:{H},crop={W}:{H},boxblur=26,eq=brightness=-0.28[bgv];"
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
    (0.0, 4.45, "intro"), (4.45, 11.10, "da"), (11.10, 17.10, "sale"), (17.10, 22.40, "ceremonies"), (22.40, 27.60, "mondial"),
    (27.60, 33.10, "nfl"), (33.10, 35.80, "card"), (35.80, 38.30, "loin"), (38.30, 48.60, "famille"), (48.60, 56.80, "tournees"),
    (56.80, 60.15, "question"), (60.15, 62.90, "card"), (62.90, END + 1, "end")]
SC = [(R(a), R(b), n) for a, b, n in SCENES]
def scene(t, i):
    for a, b, n in SC:
        if a <= t < b: return a, n
    return SC[-1][0], SC[-1][2]
GBONA, NFL = f"{WORK}/gbona.mp4", f"{WORK}/nfl.mp4"
def draw(name, t, k):
    if name == "sale":
        img = vclip("g1", GBONA, 12.0) * 0.8
        stack(img, t, [(R(11.13), "AH NON NON NON", WHT), (R(14.25), "IL A FAIT DU SALE", RED)], 130, 330, 160)
        return img
    if name == "nfl":
        img = vclip("nfl", NFL, 22.0) * 0.85
        stack(img, t, [(R(28.22), "IL Y A QUELQUES JOURS", WHT), (R(29.88), "LA MI-TEMPS", YEL)], 110, 260, 140)
        typewriter(img, t, R(30.44), "NFL PARIS", 170, RED, 1460, 12)
        return img
    if name == "loin":
        img = vclip("g2", GBONA, 40.0) * 0.85
        return img
    if name == "tournees":
        img = vclip("g3", GBONA, 44.0) * 0.8
        stack(img, t, [(R(51.76), "IL A FAIT", WHT), (R(52.64), "LE STADE DE FRANCE", YEL), (R(53.52), "LONDRES", YEL),
                       (R(55.48), "UNE GROSSE TOURNÉE", WHT), (R(55.80), "AMÉRICAINE", RED)], 105, 260, 130)
        if t >= R(52.64): paste(img, emoji("🏟️", 170), W / 2, 1450, popk(t, R(52.64)))
        return img
    kind = {"intro": "black", "da": "paper_blue", "ceremonies": "red", "mondial": "paper_red", "famille": "red", "question": "black",
            "card": "red", "end": "red"}[name]
    img = bg(kind, t) * (0.6 if name == "card" else 1.0)
    if name == "intro":
        paste(img, B_PORT, W / 2, 1050, settle(k))
        stack(img, t, [(R(0.80), "J'ÉTAIS OBLIGÉ", WHT), (R(1.44), "DE PARLER DE LUI", WHT)], 110, 250, 135)
        typewriter(img, t, R(3.44), "BURNA BOY", 170, YEL, 1560, 12)
    elif name == "da":
        paste(img, B_BW, W / 2, 960, settle(k))
        stack(img, t, [(R(4.96), "CES 5 DERNIÈRES ANNÉES", WHT)], 100, 300, 0)
        stack(img, t, [(R(7.92), "SA DA", YEL), (R(10.32), "SON STAFF", YEL)], 150, 1380, 180)
    elif name == "ceremonies":
        paste(img, B_SHAK, W / 2, 1060, settle(k))
        stack(img, t, [(R(17.80), "CÉRÉMONIES DE CLÔTURE", WHT), (R(19.72), "LIGUE DES CHAMPIONS", YEL)], 100, 250, 130)
    elif name == "mondial":
        paste(img, B_WC, W / 2, 1000, settle(k))
        stack(img, t, [(R(22.76), "LE SON OFFICIEL", WHT), (R(23.32), "COUPE DU MONDE 2026", YEL)], 110, 260, 140)
        stack(img, t, [(R(25.64), "OUVERTURE & CLÔTURE", GRN)], 100, 1560, 0)
        if t >= R(23.32): paste(img, emoji("⚽", 150), 900, 680, popk(t, R(23.32)))
    elif name == "famille":
        paste(img, B_FAM, W / 2, 960, settle(k))
        stack(img, t, [(R(40.62), "SON STAFF", WHT), (R(42.58), "SA MÈRE · SA SŒUR", YEL)], 110, 220, 140)
        stack(img, t, [(R(45.86), "TOUTE LA FAMILLE", RED)], 120, 1530, 0)
        if t >= R(45.86): paste(img, emoji("❤️", 150), 900, 560, popk(t, R(45.86)))
    elif name == "card":                              # 3D line over a dimmed photo of him
        ph = B_BW if t < R(40.0) else B_PORT
        tmp = np.zeros_like(img); paste(tmp, ph, W / 2, 1000, 1.25 + 0.04 * k); img = img + tmp * 0.55
    elif name == "question":
        paste(img, B_PORT, W / 2, 1080, settle(k))
        stack(img, t, [(R(57.32), "VOUS VOULEZ", WHT), (R(57.80), "QU'ON DISE QUOI ?", YEL)], 130, 300, 160)
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
WHITE = {"burna", "boy", "nfl", "paris", "londres", "france", "monde", "2026", "champions", "odogwu", "staff", "da"}
REDW = {"sale", "niveau", "clôture", "d'ouverture", "américaine"}
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
BURN_AT = [R(11.10), R(27.60), R(33.10), R(60.15), R(62.90)]
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
        elif c[4] == "hook": img = bg("red", t) * 0.8; paste(img, K_CROWN, W / 2, 820, 0.9)
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
for t0, txt, cps in [(R(3.44), "BURNA BOY", 12), (R(30.44), "NFL PARIS", 12)]:
    for j, ch in enumerate(txt):
        if ch != " ": place(click, t0 + j / cps, 0.22)
for t0 in (R(14.25), R(23.32), R(45.86), R(52.64), R(55.80)): place(hit, t0, 0.25)
place(load(os.path.join(LIB, "sfx/goal-crowd.mp3")), R(29.88), 0.3)
place(riser, R(33.10) - 2.95, 0.45); place(riser, R(60.15) - 2.95, 0.45)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.5)
sf.write(f"{WORK}/sfx.wav", sfx[:int(DUR * SR)], SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/voice_cut.wav", "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]highpass=f=70,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2dB,loudnorm=I=-14:TP=-1.5:LRA=7,"
    "aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.75:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, flush=True)
