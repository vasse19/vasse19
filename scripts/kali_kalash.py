"""Video from a voice note (Kalash × Himra en studio): no face-cam, full motion design in the Kali Muscle style.
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
rm(1.20); ren(1.12, "hein ?"); ren(1.44, "Kalash"); ren(2.08, "Himra"); ren(8.04, "Himra,"); ren(8.68, "lui ouvrir")
ren(12.34, "Antilles"); ren(19.50, "Bamby,"); ren(20.82, "« Gangsta »,"); ren(25.86, "avec"); ren(26.02, "Kalash.")
rm(33.26); rm(35.18); rm(36.70); rm(37.18); ren(34.30, "shatta bouyon ?"); rm(34.62); rm(34.78); ren(36.22, "mélo ?"); ren(36.86, "Bref !")
ren(42.78, "Vass"); ren(43.10, "vous"); ren(43.26, "servir.")
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
NOCAP = [(6.0, 7.85), (26.95, 27.80), (40.95, END)]   # unclear words; sign-off under the end card

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
keep[int(40.9 / 0.02):] = True
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
KAL = card(f"{WORK}/kalash.jpg", 470, (90, 200, 255))
HIM = card(f"{WORK}/himra.jpg", 470, (255, 170, 60))
KAL_L = card(f"{WORK}/kalash.jpg", 760, (90, 200, 255))
GANG = card(f"{WORK}/gangsta.jpg", 760, (255, 40, 50))
BAM = card(f"{WORK}/bamby.jpg", 420, (255, 230, 60))
DUO = KAL_L
MYS = DUO
_f = np.zeros((200, 300, 3), np.float32); _f[:, :100] = (247, 127, 0); _f[:, 100:200] = (255, 255, 255); _f[:, 200:] = (0, 158, 96)
_m = np.zeros((200, 300, 3), np.float32); _m[:] = (0, 160, 70); _m[:100] = (220, 30, 40); _m[:, :150] = _m[:, :150]
FLAG_CI = glow_rgba(np.dstack([_f / 255, np.ones((200, 300), np.float32)]), (255, 255, 255), 12, 1.2)
_m = np.zeros((200, 300, 3), np.float32); _m[:100] = (220, 30, 40); _m[100:] = (0, 150, 60); cv2.fillPoly(_m, [np.array([[0, 0], [130, 100], [0, 200]])], (10, 10, 10))
FLAG_MQ = glow_rgba(np.dstack([_m / 255, np.ones((200, 300), np.float32)]), (255, 255, 255), 12, 1.2)   # Martinique (red-green-black)
logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 210)
END_LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 640)
CARDS = [(0.0, R(2.85), "KALASH × HIMRA", "EN STUDIO ?", "hook", 1150), (R(28.20), R(30.70), "PAS N'IMPORTE", "QUI", "card", 960),
         (R(40.95), DUR, "LE BIG", "VASS", "end", 1370)]
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
    (0.0, 2.85, "card"), (2.85, 7.85, "studio"), (7.85, 15.55, "antilles"), (15.55, 24.10, "gangsta"), (24.10, 28.20, "kalash"),
    (28.20, 30.70, "card"), (30.70, 37.40, "collab"), (37.40, 40.95, "studio2"), (40.95, END + 1, "end")]
SC = [(R(a), R(b), n) for a, b, n in SCENES]
def scene(t, i):
    for a, b, n in SC:
        if a <= t < b: return a, n
    return SC[-1][0], SC[-1][2]
# his two Jeune Lion clips (TikTok reposts 576x1024): watermark mid-left then low-right, both blurred, account credited
WMB = ("split=3[wa][wb][wc];[wb]crop=200:190:0:420,boxblur=22:3[wl];[wc]crop=240:150:336:780,boxblur=22:3[wr];"
       "[wa][wl]overlay=0:420[wx];[wx][wr]overlay=336:780,")
_vj = {}
def jclip(key, path, src_t):
    st = _vj.get(key)
    if st is None:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(src_t), "-i", path, "-an", "-filter_complex",
                              f"{WMB}scale={W}:{H},eq=contrast=1.05:saturation=1.08", "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                             stdout=subprocess.PIPE)
        st = _vj[key] = {"p": p, "last": None}
    buf = st["p"].stdout.read(W * H * 3)
    if len(buf) == W * H * 3: st["last"] = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    return st["last"].copy()
def jcredit(img):
    im, _ = neon("SOURCE TIKTOK : @JEUNELION13", 40, WHT); paste(img, im, W / 2, 1890, 1.0, 0.85)
_vs = {}
def sclip(key, src_t):
    st = _vs.get(key)
    if st is None:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(src_t), "-i", f"{WORK}/studio.mp4", "-an", "-vf",
                              f"scale={W}:{H},eq=contrast=1.05:saturation=1.1", "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
        st = _vs[key] = {"p": p, "last": None}
    buf = st["p"].stdout.read(W * H * 3)
    if len(buf) == W * H * 3: st["last"] = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    return st["last"].copy()
def draw(name, t, k):
    if name == "studio":
        img = sclip("a", 0.5) * 0.85
        stack(img, t, [(R(2.88), "APERÇUS", WHT), (R(3.72), "AU STUDIO", YEL)], 150, 330, 180)
        return img
    if name == "studio2":
        img = sclip("b", 15.5) * 0.85
        stack(img, t, [(R(37.82), "QU'ILS NOUS RÉSERVENT", WHT), (R(38.38), "LA SURPRISE", YEL)], 110, 330, 140)
        return img
    kind = {"antilles": "paper_blue", "gangsta": "black", "kalash": "red", "collab": "paper_red", "card": "red", "end": "red"}[name]
    img = bg(kind, t) * (0.6 if name == "card" else 1.0)
    if name == "card":
        tmp = np.zeros_like(img); paste(tmp, KAL_L, W / 2, 1000, 1.2 + 0.04 * k); img = img + tmp * 0.5
    elif name == "antilles":
        paste(img, HIM, 290, 980, settle(k)); paste(img, KAL, 790, 980, settle(k))
        stack(img, t, [(R(8.04), "POUR HIMRA", WHT), (R(9.16), "DES PORTES", YEL), (R(10.36), "AUX ANTILLES", YEL)], 110, 220, 135)
        if t >= R(10.36): paste(img, FLAG_CI, 290, 1420, 0.55 * popk(t, R(10.36))); paste(img, emoji("🏝️", 170), 790, 1420, popk(t, R(10.36)))
    elif name == "gangsta":
        paste(img, GANG, W / 2, 820, settle(k))
        stack(img, t, [(R(16.86), "IL Y A 2 ANS", WHT)], 110, 220, 0)
        if t >= R(19.50): paste(img, BAM, 880, 1060, 0.62 * popk(t, R(19.50)))
        t1, t2 = R(21.62), R(22.42)
        if t >= t1:
            v = int(10_000_000 * min(1.0, 1 - (1 - min((t - t1) / (t2 - t1), 1)) ** 3))
            im, _ = neon(f"{v:,}".replace(",", " "), 150, YEL); paste(img, im, W / 2, 1380, popk(t, t2) if t >= t2 else 1.0)
            stack(img, t, [(R(22.82), "VUES SUR YOUTUBE", RED)], 100, 1520, 0)
    elif name == "kalash":
        paste(img, KAL_L, W / 2, 1000, settle(k))
        stack(img, t, [(R(25.06), "MAIS LÀ", WHT), (R(26.02), "AVEC KALASH", YEL)], 140, 260, 170)
    elif name == "collab":
        paste(img, HIM, 290, 880, settle(k)); paste(img, KAL, 790, 880, settle(k))
        stack(img, t, [(R(31.26), "J'AI HÂTE", WHT)], 120, 220, 0)
        stack(img, t, [(R(34.30), "SHATTA BOUYON ?", YEL), (R(36.22), "MÉLO ?", RED)], 120, 1330, 150)
        if t >= R(32.06): paste(img, emoji("❓", 160), W / 2, 880, popk(t, R(32.06)))
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
WHITE = {"kalash", "himra", "bamby", "gangsta", "youtube", "antilles", "studio"}
REDW = {"incroyable", "hâte", "plaisir", "surprise"}
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
BURN_AT = [R(2.85), R(15.55), R(28.20), R(37.40), R(40.95)]
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
        elif c[4] == "hook": img = sclip("h", 4.0) * 0.6
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
for t0 in (R(10.36), R(19.50), R(26.02), R(32.06), R(34.30), R(36.22)): place(hit, t0, 0.25); place(whoosh, t0 - 0.12, 0.15)
money = load(os.path.join(LIB, "sfx/money-counter.mp3"))[int(0.6 * SR):int(0.6 * SR) + int((R(22.42) - R(21.62)) * SR)].copy()
place(money, R(21.62), 0.6); place(load(os.path.join(LIB, "sfx/cash-ding.mp3")), R(22.42) - 0.25, 0.5)
place(riser, R(28.20) - 2.95, 0.45)
for b_ in BURN_AT: place(burn_a, b_ - BURN_PEAK, 0.5)
sf.write(f"{WORK}/sfx.wav", sfx[:int(DUR * SR)], SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/voice_cut.wav", "-i", f"{WORK}/sfx.wav", "-filter_complex",
    "[1:a]highpass=f=90,afftdn=nr=10:nf=-40,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2dB,loudnorm=I=-14:TP=-1.5:LRA=7,"
    "aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.75:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, flush=True)
