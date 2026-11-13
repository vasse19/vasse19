"""Video from a voice note (« Orange Days à Bamako, Didi B en tête d'affiche »), same engine as kali_vocal.py: no face-cam,
full motion design in the Kali Muscle style; his voice drives the pulsing logo and the waveform; Mali flag, the Orange Days
posters, Didi B's post with the date highlighted, 3D « ENTRÉE GRATUITE » card, end card.
usage: kali_orangedays.py WORK OUT.mp4   (WORK holds src.mp3, w.json and the images named below)"""
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
ren(1.60, "c'est"); ren(1.76, "le"); ren(2.16, "Vass"); words.append({"w": "vous", "s": 2.56}); words.sort(key=lambda w: w["s"])
ren(6.26, "Bamako,"); ren(8.02, "Days."); ren(9.72, "festivités"); ren(13.08, "Didi B,"); ren(17.74, "Cinquantenaire,")
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP = [(25.75, END)]                          # sign-off under the end card

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
keep[int(25.75 / 0.02):] = True
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
POST = card(f"{WORK}/post.jpg", 760, (90, 140, 255)); POSTHL = card(f"{WORK}/post_hl.jpg", 760, (90, 140, 255))
LINEUP = card(f"{WORK}/lineup.jpg", 700, ORA)
CONC = card(f"{WORK}/concert13.jpg", 760, ORA)
VILL = card(f"{WORK}/village.jpg", 720, ORA)
def mali_flag():
    f = np.zeros((200, 300, 3), np.float32); f[:, :100] = (20, 181, 58); f[:, 100:200] = (252, 209, 22); f[:, 200:] = (206, 17, 38)
    return glow_rgba(np.dstack([f / 255, np.ones((200, 300), np.float32)]), (255, 255, 255), 12, 1.2)
FLAG_ML = mali_flag()
logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 210)
END_LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 640)
CARDS = [(0.0, R(3.10), "DIDI B", "À BAMAKO", "hook", 1250), (R(23.90), R(25.75), "ENTRÉE", "GRATUITE", "card", 960),
         (R(25.75), DUR, "LE BIG", "VASS", "end", 1370)]
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
    (0.0, 3.10, "hook"), (3.10, 7.40, "mali"), (7.40, 9.00, "orange"), (9.00, 12.60, "fest"), (12.60, 15.50, "didib"),
    (15.50, 19.30, "lieu"), (19.30, 23.90, "horaires"), (23.90, 25.75, "card"), (25.75, END + 1, "end")]
SC = [(R(a), R(b), n) for a, b, n in SCENES]
def scene(t, i):
    for a, b, n in SC:
        if a <= t < b: return a, n
    return SC[-1][0], SC[-1][2]
def draw(name, t, k):
    img = bg("black" if name in ("mali", "horaires") else "red", t)
    if name == "mali":
        stack(img, t, [(R(4.50), "AUJOURD'HUI", WHT), (R(4.98), "AU MALI", YEL)], 140, 300, 175)
        if t >= R(4.98): paste(img, FLAG_ML, W / 2, 860, 1.6 * popk(t, R(4.98)))
        typewriter(img, t, R(6.26), "BAMAKO", 200, ORA, 1350, 12)
    elif name == "orange":
        paste(img, VILL, W / 2, 1000, settle(k))
        stack(img, t, [(R(7.54), "LES ORANGE DAYS", ORA)], 130, 230, 0)
    elif name == "fest":
        paste(img, CONC, W / 2, 1040, 0.9 * settle(k))
        stack(img, t, [(R(9.24), "2 JOURS DE FESTIVITÉS", WHT)], 100, 200, 0)
        stack(img, t, [(R(11.08), "STARS DE LA MUSIQUE", WHT), (R(11.96), "MALIENNE", ORA)], 85, 330, 105)
    elif name == "didib":
        paste(img, POSTHL if t >= R(14.38) else POST, W / 2, 1060, settle(min(k, 1.5)))
        typewriter(img, t, R(13.08), "DIDI B", 170, WHT, 230, 10)
        stack(img, t, [(R(14.06), "EN TÊTE D'AFFICHE", GOLD)], 110, 400, 0)
    elif name == "lieu":
        paste(img, LINEUP, W / 2, 1050, 0.95 * settle(k))
        stack(img, t, [(R(15.58), "PRENEZ VOS PLACES", WHT)], 110, 220, 0)
        typewriter(img, t, R(17.34), "PLACE DU CINQUANTENAIRE", 80, ORA, 360, 24)
    elif name == "horaires":
        stack(img, t, [(R(19.36), "ANIMATIONS", WHT)], 150, 420, 0)
        typewriter(img, t, R(20.56), "DÈS 9H", 220, YEL, 640, 10)
        stack(img, t, [(R(22.00), "CONCERTS", WHT)], 150, 1000, 0)
        typewriter(img, t, R(23.30), "22H", 240, ORA, 1230, 8)
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
WHITE = {"bamako", "mali", "orange", "days", "didi", "b", "cinquantenaire", "9h", "22h"}
REDW = {"gratuit", "stars"}
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
BURN_AT = [R(3.10), R(9.00), R(15.50), R(23.90)]
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
        elif c[4] == "hook": img = bg("red", t) * 0.8; paste(img, POST, W / 2, 760, 0.85)
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
for t0, txt, cps in [(R(6.26), "BAMAKO", 12), (R(13.08), "DIDI B", 10), (R(17.34), "PLACE DU CINQUANTENAIRE", 24),
                     (R(20.56), "DÈS 9H", 10), (R(23.30), "22H", 8)]:
    for j, ch in enumerate(txt):
        if ch != " ": place(click, t0 + j / cps, 0.22)
for t0 in (R(4.98), R(14.38)): place(hit, t0, 0.25)
place(riser, R(23.90) - 2.95, 0.45)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.5)
sf.write(f"{WORK}/sfx.wav", sfx[:int(DUR * SR)], SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/voice_cut.wav", "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]highpass=f=70,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2dB,loudnorm=I=-14:TP=-1.5:LRA=7,"
    "aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.75:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, flush=True)
