"""« Booba × Himra » v2 (vertical, Kali style), from his updated 2 min 25 voice note: Booba's Instagram story (TikTok repost,
watermarks blurred, credited) and Himra's freestyle line kept with their own sound; the « Je suis froid » reply shown with the
press tweets as proofs (Rvpfr, Kultur); Booba/Himra and La Fouine/Booba VS splits; Lamborghini Urus shots from the story;
Himra live footage from the library; word-by-word neon captions (ASR-garbled passages replaced by his words as heard);
breath gate on his voice; his logo top left; library transitions.
usage: kali_booba_himra_v2.py WORK OUT.mp4
  (WORK: voix.mp3, w.json, w_free.mp4.json, free.mp4 = Booba's story, story.mov = Himra's freestyle line, booba.png, himra.jpg,
   la-fouine.jpg, himra-live.jpg, proof-rvpfr.jpg, proof-kultur.jpg)"""
import sys, os, json, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
EXT = os.path.join(REPO, "assets/extraits/musique")
VOICE = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{WORK}/voix.mp3"]))
PIECES = [("voix", 0.0, 65.9), ("free", 0.0, 27.9), ("voix", 65.9, 124.5), ("story", 0.0, 2.15), ("voix", 124.5, VOICE)]
OUTT = []; o = 0.0
for p in PIECES: OUTT.append(o); o += p[2] - p[1]
DUR = o + 0.3; N = int(DUR * FPS)
def V(t):
    for (src, a, b), o0 in zip(PIECES, OUTT):
        if src == "voix" and a <= t <= b + 0.01: return o0 + t - a
    raise ValueError(t)
O_FREE, O_STORY = OUTT[1], OUTT[3]

# ---------- captions (his words; garbled ASR passages replaced by what he says) ----------
REN = {3.6: "Vass", 14.7: "de Boulogne,", 16.1: "Booba,", 33.9: "Himra.", 35.4: "Himra,", 39.9: "Himra,", 43.0: "Urus.", 58.5: "Himra",
       61.3: "Booba", 69.0: "Himra", 71.1: "Booba,", 92.7: "La Fouine,", 93.3: "La Fouine…", 97.7: "Booba ?", 101.1: "Fouine", 101.8: "Booba",
       105.4: "Booba,", 107.5: "Himra,", 135.3: "Himra,", 143.3: "Vass", 4.9: "on reprend les", 5.8: "toutes", 6.6: "vidéos", 7.4: "YouTube."}
RM = [28.6, 109.9]
REPL = [(47.0, 57.6, "C'est costaud. Et dans sa story, en fait, il a proposé à Himra de faire un featuring. Et"),
        (75.7, 89.3, "Je pense que c'est une réponse, mais de manière défavorable : il refuse le feat. Parce que d'un côté, ma théorie, c'est qu'il ne faut pas oublier que"),
        (109.7, 124.4, "Donc voilà, c'était ça le scoop du jour. Moi aussi, j'aurais kiffé voir les deux en featuring. Parce que, il y a quelques années, dans le freestyle Drill Ivoire 3, Himra avait dit : « je prépare un son que je dois envoyer au Duc »")]
words = []
for w in json.load(open(f"{WORK}/w.json")):
    if any(abs(w["s"] - t) < 0.06 for t in RM) or any(a <= w["s"] < b for a, b, _ in REPL): continue
    w = dict(w)
    for t, txt in REN.items():
        if abs(w["s"] - t) < 0.06: w["w"] = txt
    words.append(w)
for a, b, text in REPL:
    toks = text.split(); L = sum(len(x) + 2 for x in toks); acc = 0
    for x in toks: words.append({"w": x, "s": a + (b - a) * acc / L}); acc += len(x) + 2
out = []
for w in words:
    try: out.append({"w": w["w"], "s": V(w["s"])})
    except ValueError: pass
for w in json.load(open(f"{WORK}/w_free.mp4.json")):                                     # Booba's words in the story
    if w["s"] < 27.9:
        fix = {"Imara.": "Himra.", "Imara": "Himra", "chaud,": "chaud", "ce": "pour", "fit": "le feat ?", "répond.": "réponds.", "taureau": "Taureau"}
        out.append({"w": fix.get(w["w"], w["w"]), "s": O_FREE + w["s"]})
for i, txt in enumerate("J'prépare le son que j'dois envoyer au DUC".split()):
    out.append({"w": txt, "s": O_STORY + 0.05 + i * 0.2})
words = sorted(out, key=lambda w: w["s"])
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))

# ---------- footage ----------
def frames(path, t0, d, vf):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d + 0.3), "-i", path, "-an", "-vf",
                          f"{vf},fps={FPS},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
DELOGO = "delogo=x=5:y=468:w=196:h=90,delogo=x=378:y=775:w=196:h=92,delogo=x=414:y=56:w=118:h=58"
PILLAR = "crop=ih*9/16:ih,unsharp=5:5:0.5"
SCENES = [  # (output start, kind, path, src start, vf)
    (0.0, "hook", None, 0, ""),
    (V(11.1), "vs", None, 0, ""),
    (V(26.2), "vid", f"{WORK}/free.mp4", 8.0, DELOGO),                  # the Lamborghini Urus shots of the story
    (V(43.7), "money", None, 0, ""),
    (V(63.9), "extrait", None, 0, ""),
    (O_FREE, "vid", f"{WORK}/free.mp4", 0.0, DELOGO),
    (OUTT[2], "proof", None, 0, ""),
    (V(85.0), "fouine", None, 0, ""),
    (V(104.4), "vid", f"{EXT}/himra-zenith-live-16x9.mp4", 44.0, PILLAR + ",eq=contrast=1.06:saturation=1.15"),
    (V(109.7), "vid", f"{EXT}/himra-zenith-live-16x9.mp4", 0.5, PILLAR + ",hue=s=0,eq=contrast=1.2"),
    (O_STORY, "band", f"{WORK}/story.mov", 0.0, ""),
    (OUTT[4], "vid", f"{EXT}/himra-zenith-live-16x9.mp4", 20.0, PILLAR + ",eq=contrast=1.06:saturation=1.15"),
    (V(131.9), "outro", None, 0, "")]
_c = {}
def scene(t): i = max(j for j, s in enumerate(SCENES) if s[0] <= t); return i, t - SCENES[i][0]
def crop_fill(path, w, h, fy=0.4):
    im = cv2.imread(path); s = max(w / im.shape[1], h / im.shape[0]); im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    x0 = (im.shape[1] - w) // 2; y0 = int((im.shape[0] - h) * fy); return im[y0:y0 + h, x0:x0 + w].astype(np.float32) / 255
BOOBA_H = crop_fill(f"{WORK}/booba.png", W, H // 2, 0.2); HIMRA_H = crop_fill(f"{WORK}/himra.jpg", W, H // 2, 0.25)
FOUINE_H = crop_fill(f"{WORK}/la-fouine.jpg", W, H // 2, 0.2)
def card_img(path, width, rim):
    im = cv2.imread(path); s = width / im.shape[1]; c = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    c[:6] = c[-6:] = c[:, :6] = c[:, -6:] = rim[::-1]
    return glow_rgba(np.dstack([c[..., ::-1].astype(np.float32) / 255, np.ones(c.shape[:2], np.float32)]), rim, 24, 1.0)
PROOF1 = card_img(f"{WORK}/proof-rvpfr.jpg", 940, (255, 255, 255)); PROOF2 = card_img(f"{WORK}/proof-kultur.jpg", 900, (90, 160, 255))
LIVE = card_img(f"{WORK}/himra-live.jpg", 860, (255, 190, 60))
def footage(i, k, t):
    s0, kind, path, a, vf = SCENES[i]; d = (SCENES[i + 1][0] if i + 1 < len(SCENES) else DUR) - s0
    if kind in ("hook", "money", "extrait", "proof"): return bg({"hook": "red", "money": "paper_red", "extrait": "black", "proof": "paper_blue"}[kind], t)
    if kind in ("vs", "outro", "fouine"):
        top = FOUINE_H if kind == "fouine" else BOOBA_H; bot = BOOBA_H if kind == "fouine" else HIMRA_H
        img = np.vstack([top, bot]).copy()
        if kind == "outro": img *= 0.45
        cv2.rectangle(img, (0, H // 2 - 6), (W, H // 2 + 6), (0.2, 0.2, 1.0), -1)
        return img
    if i not in _c:
        _c.clear()
        if kind == "band":
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-an", "-vf", f"fps={FPS},scale={W}:-2:flags=lanczos",
                                  "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
            bh = int(round(W * 718 / 1290 / 2) * 2); _c[i] = np.frombuffer(raw, np.uint8).reshape(-1, bh, W, 3)
        else: _c[i] = frames(path, a, d, vf)
    c = _c[i]; f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
    if kind == "band":
        img = cv2.resize(cv2.GaussianBlur(cv2.resize(f, (108, 60)), (0, 0), 3), (W * 4, H))[:, W * 3 // 2:W * 5 // 2] * 0.4
        y0 = 820; img[y0:y0 + f.shape[0]] = f; return img
    z = 1.0 + 0.04 * k / max(d, 0.1) + 0.04 * max(0, 1 - k / 0.15)
    return cv2.warpAffine(f, cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def settle(k): return (1.1 - 0.1 * min(max(k, 0) / 0.3, 1) ** 0.4) * (1 + 0.02 * max(k, 0))
def card(img, im, t, t0, y):
    k = t - t0
    if k >= 0: paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
HOOK = block("LE SCOOP", "DU JOUR", 1000, 620)
CARD = block("IL A RAISON", "OU PAS ?", 1000, 640)
LOGO_S = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 200)
X, _ = neon("×", 300, GOLD)
CREDIT, _ = neon("TikTok : @topdumomentofficiel1", 42, WHT)
MONEY = rgba_file(os.path.join(LIB, "3d/money-stack-gold.png"), 420)
_ef = None
def emoji(ch, size):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109); im = Image.new("RGBA", (160, 160))
    ImageDraw.Draw(im).text((20, 15), ch, font=f, embedded_color=True); im = im.crop(im.getbbox()).resize((size, size))
    return np.asarray(im).astype(np.float32) / 255
COLD = emoji("🥶", 220)

def draw(t):
    i, k = scene(t); kind = SCENES[i][1]; img = footage(i, k, t)
    if kind == "hook": card(img, HOOK, t, 0.1, 960)
    elif kind == "vs":
        for tt, txt, y, col in ((V(16.1), "BOOBA", 820, WHT), (V(33.9), "HIMRA", 1100, YEL)):
            if t >= tt: im, _ = neon(txt, 150, col); paste(img, im, W / 2, y, popk(t, tt))
        if t >= V(21.8): paste(img, X, W / 2, H / 2, popk(t, V(21.8)))
        if t < V(21.8): stack(img, t, [(V(12.9), "IL Y A QUELQUES HEURES", WHT), (V(17.9), "UNE STORY DE BOOBA", YEL)], 95, 300, 120)
        else: stack(img, t, [(V(21.8), "UN FEAT AVEC UN RAPPEUR", WHT), (V(24.6), "QUI A UNE LAMBORGHINI", GOLD)], 95, 300, 120)
    elif i == 2:
        if t < V(32.0): stack(img, t, [(V(29.5), "PAS TOUT LE MONDE", WHT), (V(30.4), "PEUT S'EN ACHETER UNE", YEL)], 100, 330, 125)
        else: stack(img, t, [(V(33.9), "HIMRA", YEL), (V(42.2), "UNE LAMBORGHINI URUS", GOLD)], 110, 330, 135)
    elif kind == "money":
        if t >= V(45.6): paste(img, MONEY, W / 2, 760, popk(t, V(45.6)))
        stack(img, t, [(V(45.6), "300 000 €", GRN), (V(48.1), "C'EST COSTAUD", YEL)], 140, 1120, 170)
        stack(img, t, [(V(53.0), "BOOBA PROPOSE LE FEAT", WHT), (V(58.5), "SINON ?", RED), (V(62.1), "IL FERA LE SON SEUL", YEL)], 85, 260, 110)
    elif kind == "extrait": stack(img, t, [(V(64.1), "PLACE", WHT), (V(64.6), "À L'EXTRAIT", YEL)], 170, 820, 200)
    elif i == 5: stack(img, t, [(O_FREE + 0.05, "BOOBA :", GOLD)], 110, 330, 0)
    elif kind == "proof":
        if t < V(79.5):
            paste(img, PROOF1, W / 2, 900, settle(k) * min(1.0, 0.85 + k))
            stack(img, t, [(V(69.0), "LA RÉPONSE DE HIMRA", WHT)], 90, 230, 0)
            if t >= V(73.8): im, _ = neon("« JE SUIS FROID »", 120, (140, 220, 255)); paste(img, im, W / 2, 1600, popk(t, V(73.8))); paste(img, COLD, W / 2, 1760, popk(t, V(74.5)))
        else:
            paste(img, PROOF2, W / 2, 880, settle(t - V(79.5)))
            stack(img, t, [(V(79.5), "UN REFUS ?", RED)], 130, 230, 0)
            stack(img, t, [(V(83.4), "LA PRESSE : IL REFUSE LE FEAT", YEL)], 70, 1560, 0)
    elif kind == "fouine":
        for tt, txt, y, col in ((V(92.7), "LA FOUINE", 820, WHT), (V(97.7), "BOOBA", 1100, YEL)):
            if t >= tt: im, _ = neon(txt, 150, col); paste(img, im, W / 2, y, popk(t, tt))
        if t >= V(101.8): paste(img, X, W / 2, H / 2, popk(t, V(101.8)))
        stack(img, t, [(V(87.1), "MA THÉORIE", YEL), (V(90.4), "SON MENTOR : LA FOUINE", WHT)], 95, 300, 120)
        stack(img, t, [(V(102.7), "ILS NE S'ENTENDENT PAS", RED)], 90, 1560, 0)
    elif i == 8: stack(img, t, [(V(104.4), "MAIS DE L'AUTRE CÔTÉ", WHT), (V(105.4), "BOOBA L'A SOUTENU", YEL)], 100, 330, 125)
    elif i == 9: stack(img, t, [(V(113.0), "RAPPELEZ-VOUS…", WHT), (V(119.8), "FREESTYLE DRILL IVOIRE 3", RED)], 90, 330, 115)
    elif kind == "band": stack(img, t, [(O_STORY + 0.1, "HIMRA", YEL), (O_STORY + 1.3, "LE DUC = BOOBA", GOLD)], 110, 420, 140)
    elif i == 11: stack(img, t, [(V(126.3), "UN SON DÉJÀ ENREGISTRÉ ?", YEL), (V(130.1), "DOMMAGE…", RED)], 95, 330, 120)
    elif kind == "outro":
        card(img, CARD, t, V(134.9), 960)
        if t > DUR - 0.4: img *= max(0.0, (DUR - t) / 0.4)
    if SCENES[i][2] and SCENES[i][2].endswith("free.mp4"): paste(img, CREDIT, W / 2, 1865)
    paste(img, LOGO_S, 130, 130)
    return img

# ---------- captions ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: G,Anton,120,&H6000E5FF,&H0000E5FF,&H8000C8FF,&H00000000,0,0,0,0,100,100,1,0,1,10,0,5,40,40,0,1
Style: W,Anton,120,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,4,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
WHITE = {"booba", "booba,", "booba ?", "himra.", "himra", "himra,", "duc", "lamborghini.", "lamborghini,", "lamborghini", "urus.", "fouine", "la fouine,", "la fouine…", "vass"}
REDW = {"scoop", "featuring", "featuring.", "freestyle", "froid.", "refuse", "chaud.", "défavorable"}
for w in words:
    i, _ = scene(w["s"]); kind = SCENES[i][1]
    if kind == "hook" and w["s"] < 2.0: continue
    if kind == "outro" and w["s"] >= V(134.9): continue
    if kind == "proof" and w["s"] < V(79.5) and w["s"] >= V(73.6): continue        # « je suis froid » already on screen
    y = 1300 if SCENES[i][2] and SCENES[i][2].endswith("free.mp4") else (1560 if kind == "band" else 1690)
    if kind == "proof": y = 1450 if w["s"] >= V(79.5) else 1690
    lw = w["w"].lower()
    col = r"\c&H002A2AFF&\3c&H002A2AFF&" if lw in REDW else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if lw in WHITE else "")
    txt = w["w"].upper().strip(",.?!…: ") or w["w"]
    pp = r"\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)"
    ass.append(f"Dialogue: 0,{ts(w['s'])},{ts(max(w['e'], w['s'] + 0.15))},G,,0,0,0,,{{\\an5\\pos(540,{y}){col}\\blur14{pp}}}{txt}")
    ass.append(f"Dialogue: 1,{ts(w['s'])},{ts(max(w['e'], w['s'] + 0.15))},W,,0,0,0,,{{\\an5\\pos(540,{y}){col.split(chr(92) + '3c')[0] if col else ''}{pp}}}{txt}")
open(f"{WORK}/caps.ass", "w").write("\n".join(ass) + "\n")

# ---------- transitions ----------
def trans(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions", name), "-vf", f"fps={FPS},scale=-2:{H},crop={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
TR = {"burn": (trans("burn-transition-12.mp4"), 11 / 30), "red": (trans("red-flash-39.mp4"), 17 / 30),
      "bw": (trans("bw-flash-33.mp4"), 4 / 23.976), "light": (trans("light-flash-23.mp4"), 5 / 23.976)}
KINDS = ["red", "light", "burn", "light", "red", "burn", "light", "red", "bw", "light", "burn", "red"]
TRANS = [(s[0], KINDS[(j - 1) % len(KINDS)]) for j, s in enumerate(SCENES) if j > 0]

VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", f"vignette=angle=PI/6,noise=alls=3:allf=t+u,ass={WORK}/caps.ass:fontsdir={os.path.dirname(ANTON)},format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", VIDEO_ONLY], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; img = draw(t); i, k = scene(t)
    if 0 < k < 0.07 and t > 0.1: img = np.clip(img + (0.07 - k) / 0.07 * 0.45, 0, 1)
    for t0, name in TRANS:
        fr, pk = TR[name]; j = int(round((t - (t0 - pk)) * FPS))
        if 0 <= j < len(fr): img = 1 - (1 - img) * (1 - fr[j].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()

# ---------- sound ----------
SR = 48000; L = int(DUR * SR) + SR; mix = np.zeros(L, np.float32)
def load(p, ss=0.0, d=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss)] + (["-t", str(d)] if d else []) + ["-i", p, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.check_output(cmd), np.float32).copy()
def place(snd, t, g):
    i0 = max(int(t * SR), 0); n = min(len(snd), L - i0)
    if n > 0: mix[i0:i0 + n] += snd[:n] * g
def fade(x, f=0.02):
    n = int(f * SR); e = np.ones(len(x), np.float32); e[:n] = np.linspace(0, 1, n); e[-n:] = np.linspace(1, 0, n); return x * e
voice = load(f"{WORK}/voix.mp3")
rms = np.sqrt(np.mean(voice[int(10 * SR):int(60 * SR)] ** 2)); voice = voice * (0.2 / (rms + 1e-9))       # his level up (~ -14 LUFS after the limiter)
_h = int(0.01 * SR); _db = 20 * np.log10(np.array([np.sqrt(np.mean(voice[i:i + _h] ** 2)) for i in range(0, len(voice), _h)]) + 1e-9)
_open = np.convolve((np.convolve(_db, np.ones(5) / 5, "same") > -40).astype(np.float32), np.ones(13), "same") > 0
voice = voice * np.repeat(np.convolve(np.where(_open, 1.0, 0.12), np.ones(3) / 3, "same"), _h)[:len(voice)]     # breath gate
ref = voice[int(13 * SR):int(60 * SR)]
def match(x): return x * (np.sqrt(np.mean(ref ** 2)) / (np.sqrt(np.mean(x ** 2)) + 1e-9))
for (src, a, b), o0 in zip(PIECES, OUTT):
    if src == "voix": place(fade(voice[int(a * SR):int(b * SR)]), o0, 1.0)
    else: place(fade(match(load(f"{WORK}/{'story.mov' if src == 'story' else 'free.mp4'}", a, b - a))), o0, 1.0)
S = lambda f: os.path.join(LIB, "sfx", f)
wh = [load(S(f"whoosh-{m}.mp3")) for m in (1, 2, 3, 4)]; hit = load(S("synth-hit.wav"))
for m, (t0, _) in enumerate(TRANS): place(wh[m % 4], t0 - 0.13, 0.2)
place(hit, 0.1, 0.45); place(hit, V(21.8), 0.45); place(hit, V(101.8), 0.45); place(hit, V(134.9), 0.45)
place(load(S("cash-ding.mp3")), V(45.6) - 0.4, 0.4); place(load(S("camera-shutter-short.mp3")), OUTT[2] + 0.1, 0.45)
place(load(S("camera-shutter-short.mp3")), V(79.5), 0.45); place(load(S("uhh.mp3")), V(74.6), 0.18)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-filter_complex",
    "[1:a]alimiter=limit=0.89:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]", "-map", "0:v", "-map", "[a]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT],
    input=mix[:int(DUR * SR)].tobytes(), check=True)
print("done", OUT, f"{DUR:.1f}s")
