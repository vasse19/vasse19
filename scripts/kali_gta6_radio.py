"""Video from a voice note (« GTA VI aura sa radio afro : Afrobank FM, Burna Boy et Palmsy »), same engine as kali_vocal.py:
no face-cam, his voice kept as recorded drives the logo and the waveform; the GTA VI trailer (sent sideways: transpose=2)
as a 16:9 band over its blurred copy, the Afrobank FM player screen, 3D hook / card, 3D notes and wifi, « Joha » very low
under the bangers and Vice City part.
usage: kali_gta6_radio.py WORK OUT.mp4   (WORK holds src.mp3, w.json, v1.mp4 trailer, v2.mp4 player, afrobank.jpg, burna.jpg)"""
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
ren(0.72, "VI"); ren(4.16, "musique"); rm(4.40); ren(8.26, "VI."); ren(10.28, "Afrobank"); ren(16.46, "Palmsy.")
ren(18.16, "Au programme"); ren(18.56, "l'afrobeats,"); ren(19.60, "l'amapiano,"); rm(19.92); ren(24.18, "« Joha »"); ren(24.58, "d'Asake,")
ren(25.38, "« Shay'sana »"); rm(25.86); ren(26.26, "de DJ Lag,"); ren(36.24, "prêts")
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP = [(20.40, 21.30), (37.00, END)]          # third genre unclear; comment call + sign-off shown as screens

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
keep[int(37.00 / 0.02):] = True
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
AFRO = card(f"{WORK}/afrobank.jpg", 760, (60, 200, 90)); AFROS = card(f"{WORK}/afrobank.jpg", 360, (60, 200, 90))
BURNA = card(f"{WORK}/burna.jpg", 680, (200, 120, 255))
def frames(path, t0, dur, vf, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(dur), "-i", path, "-an", "-vf", f"{vf},fps=30,scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
TR = {k: frames(f"{WORK}/v1.mp4", a, d, "transpose=2,crop=iw:ih*0.84", 1080, 512) for k, (a, d) in
      {"logo": (162.3, 3.0), "rock": (2.2, 2.6), "beach": (6.4, 3.0), "night": (143.0, 4.0), "city": (31.0, 3.5)}.items()}
PL = {k: frames(f"{WORK}/v2.mp4", a, d, "null", 900, 864) for k, (a, d) in {"burna": (1.0, 2.6), "joha": (17.0, 7.5)}.items()}
def trailer(key, k, dim=1.0):
    f = TR[key][min(int(k * FPS), len(TR[key]) - 1)]
    bgf = cv2.resize(cv2.GaussianBlur(cv2.resize(f, (135, 240)), (0, 0), 6), (W, H)).astype(np.float32) / 255 * 0.45
    bgf[704:1216] = f.astype(np.float32) / 255 * dim
    return bgf
def player(img, key, k, y):
    f = PL[key][min(int(k * FPS), len(PL[key]) - 1)].astype(np.float32) / 255
    paste(img, glow_rgba(np.dstack([f[..., ::-1], np.ones(f.shape[:2], np.float32)]), (60, 200, 90), 22, 1.0), W / 2, y, 1.0)
P3D = {n: rgba_file(os.path.join(LIB, "3d", f), 640) for n, f in (("note", "music-note-gold.png"), ("note2", "music-note-red.png"),
                                                                   ("wifi", "wifi-gradient.png"), ("bolt", "lightning-gold.png"))}
def pop3d(img, t, t0, n, x, y, sc=1.0, life=2.5):
    k = t - t0
    if 0 <= k < life: paste(img, P3D[n], x, y, sc * popk(t, t0) * (1 + 0.03 * k), min(k / 0.08, 1) * min((life - k) / 0.25, 1))
def fr_flag():
    f = np.zeros((200, 300, 3), np.float32); f[:, :100] = (0, 85, 164); f[:, 100:200] = (255, 255, 255); f[:, 200:] = (239, 65, 53)
    return glow_rgba(np.dstack([f / 255, np.ones((200, 300), np.float32)]), (255, 255, 255), 12, 1.2)
FLAG_FR = fr_flag()
logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 210)
END_LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 640)
CARDS = [(0.0, R(2.40), "GTA VI", "RADIO AFRO", "hook", 470), (R(35.60), R(37.00), "VOUS N'ÊTES", "PAS PRÊTS", "card", 960),
         (R(38.40), DUR, "LE BIG", "VASS", "end", 1370)]
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
    (0.0, 2.40, "hook"), (2.40, 4.00, "rock"), (4.00, 9.00, "afro"), (9.00, 13.45, "afrobank"), (13.45, 16.00, "burna"),
    (16.00, 18.10, "palmsy"), (18.10, 22.40, "genres"), (22.40, 29.30, "bangers"), (29.30, 31.50, "vice"), (31.50, 35.60, "city"),
    (35.60, 37.00, "card"), (37.00, 38.40, "comment"), (38.40, END + 1, "end")]
SC = [(R(a), R(b), n) for a, b, n in SCENES]
def scene(t, i):
    for a, b, n in SC:
        if a <= t < b: return a, n
    return SC[-1][0], SC[-1][2]
def draw(name, t, k):
    if name == "rock":
        img = trailer("rock" if t < R(3.20) else "beach", k if t < R(3.20) else t - R(3.20))
        stack(img, t, [(R(2.48), "ROCKSTAR", WHT), (R(3.68), "CONFIRME", YEL)], 140, 380, 165)
        return img
    if name == "vice":
        img = trailer("night", k)
        stack(img, t, [(R(29.40), "IMAGINEZ…", WHT), (R(30.36), "VICE CITY DE NUIT", (255, 90, 200))], 120, 400, 150)
        return img
    if name == "city":
        img = trailer("city" if t < R(33.40) else "night", k if t < R(33.40) else 1.5 + t - R(33.40))
        stack(img, t, [(R(31.98), "À FOND", YEL), (R(32.30), "DANS LA VOITURE", WHT)], 120, 380, 150)
        stack(img, t, [(R(33.98), "LES COURSES-POURSUITES", RED)], 95, 1400, 0)
        return img
    img = bg("black" if name in ("genres", "palmsy", "comment") else "red", t)
    if name == "afro":
        stack(img, t, [(R(4.00), "LA MUSIQUE", WHT), (R(4.90), "AFRICAINE", GOLD)], 150, 320, 180)
        pop3d(img, t, R(4.90), "note", 280, 820, 0.9, 4.0)
        stack(img, t, [(R(6.02), "SA PROPRE RADIO", YEL)], 130, 1000, 0)
        pop3d(img, t, R(6.26), "wifi", 800, 760, 0.9, 3.0)
        stack(img, t, [(R(7.14), "DANS GTA VI", (255, 90, 200))], 150, 1250, 0)
    elif name == "afrobank":
        paste(img, AFRO, W / 2, 980, settle(min(k, 1.5)))
        typewriter(img, t, R(10.28), "AFROBANK FM", 150, GRN, 300, 14)
        stack(img, t, [(R(12.28), "ACCROCHE-TOI BIEN", YEL)], 100, 1520, 0)
    elif name == "burna":
        paste(img, BURNA, W / 2, 1020, settle(min(k, 1.5)))
        stack(img, t, [(R(13.82), "BURNA BOY", (200, 120, 255)), (R(14.78), "EN PERSONNE", WHT)], 140, 260, 170)
    elif name == "palmsy":
        player(img, "burna", k, 980)
        stack(img, t, [(R(16.06), "AUX CÔTÉS DE", WHT), (R(16.46), "PALMSY", YEL)], 130, 230, 155)
    elif name == "genres":
        stack(img, t, [(R(18.16), "AU PROGRAMME", WHT)], 120, 260, 0)
        stack(img, t, [(R(18.56), "AFROBEATS", GOLD), (R(19.60), "AMAPIANO", GRN), (R(21.52), "GROS CLASSIQUES", RED)], 160, 560, 230)
        pop3d(img, t, R(18.56), "note", 870, 1350, 0.75, 3.8); pop3d(img, t, R(19.60), "note2", 220, 1300, 0.7, 2.8)
    elif name == "bangers":
        player(img, "joha", k, 820)
        stack(img, t, [(R(23.54), "DES BANGERS", YEL)], 110, 230, 0)
        stack(img, t, [(R(24.18), "JOHA – ASAKE", WHT), (R(25.38), "SHAY'SANA – DJ LAG", WHT), (R(28.20), "LÉGENDE : PAT THOMAS", GOLD)], 75, 1330, 95)
    elif name == "comment":
        typewriter(img, t, R(37.04), "DONNEZ VOTRE AVIS", 110, WHT, 760, 22)
        stack(img, t, [(R(37.70), "EN COMMENTAIRE", YEL)], 150, 960, 0)
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
WHITE = {"gta", "vi", "vi.", "rockstar", "afrobank", "fm", "burna", "boy", "palmsy", "joha", "asake", "dj", "lag", "pat", "thomas", "vice", "city"}
REDW = {"africaine", "radio", "bangers", "légendes", "nuit", "fond"}
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
BURN_AT = [R(2.40), R(9.00), R(29.30)]
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
        elif c[4] == "hook": img = trailer("logo", t, 1.0); paste(img, AFROS, W / 2, 1520, 1.0)
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
for t0, txt, cps in [(R(10.28), "AFROBANK FM", 14), (R(37.04), "DONNEZ VOTRE AVIS", 22)]:
    for j, ch in enumerate(txt):
        if ch != " ": place(click, t0 + j / cps, 0.22)
for t0 in (R(4.90), R(6.26), R(13.82), R(18.56), R(24.18), R(25.38), R(28.20)): place(hit, t0, 0.25)
place(riser, R(35.60) - 2.95, 0.45)
joha = load(f"{WORK}/v2.mp4")[int(17.0 * SR):int(31.0 * SR)]      # « Joha » from the Afrobank FM player, very low under his voice
a0, a1 = R(22.40), R(35.60); n = min(len(joha), int((a1 - a0) * SR)); env = np.minimum(np.minimum(np.arange(n) / (0.6 * SR), 1), np.minimum((n - np.arange(n)) / (0.8 * SR), 1))
place(joha[:n] * env, a0, 0.13)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.5)
sf.write(f"{WORK}/sfx.wav", sfx[:int(DUR * SR)], SR)
# voice as recorded (he asked to keep his sound): no compressor or loudness change, safety limiter only
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/voice_cut.wav", "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, flush=True)
