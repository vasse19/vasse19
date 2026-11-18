"""« 1 an de beatmaking » Short: a radio cold open (La Peufra / Nostalgie, 16:9 band, its own sound brought to -14 LUFS),
then his voice-over on his own beat (beat.mp3, kept as recorded) over his silent studio takes, word-by-word neon
captions, a type-beat grid (Rick Ross, 2 Chainz, Gucci Mane, Kanye West), a grid of the 8 beatmakers he names, 3D cards,
his library flashes, end card. No names for the radio guests and no source line (he asked « mets rien »).
usage: kali_beatmaking.py WORK OUT.mp4"""
import sys, os, json, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, GRN, GOLD, paste, neon, stack, typewriter, rgba_file, glow_rgba, bg, block

WORK, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def dur(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
INTRO = 13.0                                  # the radio clip, cut after « plus facile que… »
O = INTRO                                     # voice-over starts here (output seconds)
VO = dur(f"{WORK}/beat.mp3"); DUR = O + VO; N = int(DUR * FPS)

# ---------- captions: radio clip words + his voice-over words (fixed) ----------
iw = json.load(open(f"{WORK}/iw.json")); vw = json.load(open(f"{WORK}/bw.json"))
def fix(words, ren, rm, nocap):
    out = []
    for w in words:
        if any(abs(w["s"] - t) < 0.02 for t in rm): continue
        w = dict(w)
        for t, txt in ren:
            if abs(w["s"] - t) < 0.02: w["w"] = txt
        w["nc"] = any(a <= w["s"] < b for a, b in nocap); out.append(w)
    return out
iw = fix(iw, [(9.16, "FL,"), (9.72, "c'est facile.")], [], [(1.55, 2.6), (10.8, 13.0)])
vw = fix(vw, [(15.28, "passé"), (16.32, "à écouter des type beats"), (17.28, "que ce"), (17.84, "type"), (18.24, "beats"), (18.80, "Rick Ross,"),
              (19.60, "2 Chainz,"), (20.48, "Gucci"), (20.96, "Mane,"), (21.28, "Kanye"), (42.96, "Zaytoven,"), (44.32, "Chop,"), (44.96, "Boomin,"),
              (45.60, "Mike WiLL Made-It,"), (46.96, "Southside,"), (47.52, "Sonny"), (48.08, "Digital,"), (48.48, "London"), (48.72, "on"),
              (48.88, "da"), (49.04, "Track,"), (49.68, "Lex"), (50.08, "Luger."), (66.40, "Monsieur"), (66.80, "Vass"), (67.44, "on"),
              (67.60, "the beat."), (70.72, "Like,"), (71.20, "commente,"), (71.60, "partage."), (72.88, "Ciao,"), (73.28, "peace.")],
         [43.36, 46.32, 46.56, 47.28, 49.20, 67.12, 71.04], [(58.90, 59.70), (68.30, 70.70)])
for w in iw: w["s"] += 0.0
for w in vw: w["s"] += O
words = sorted(iw + vw, key=lambda w: w["s"])
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else DUR
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
def V(t): return O + t                        # voice-over time -> output time

# ---------- footage ----------
def frames(path, t0, d, vf="null"):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d), "-i", path, "-an", "-vf",
                          f"{vf},fps={FPS},scale={W}:{H},eq=contrast=1.06:saturation=1.12", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
_cache = {}
def take(key, path, t0, d):
    if key not in _cache: _cache.clear(); _cache[key] = frames(path, t0, d)
    return _cache[key]
def cam(name, t0, k, d):
    c = take((name, t0), f"{WORK}/{name}.mp4", t0, d); f = c[min(int(k * FPS), len(c) - 1)].astype(np.float32) / 255
    z = (1.0, 1.1, 1.04, 1.16)[int(k / 1.7) % 4]
    return cv2.warpAffine(f, cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)
def radio(k):
    c = _cache.get("radio")
    if c is None:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-t", str(INTRO), "-i", f"{WORK}/intro.mov", "-an", "-vf", f"fps={FPS},scale={W}:608",
                              "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
        c = _cache["radio"] = np.frombuffer(raw, np.uint8).reshape(-1, 608, W, 3)
    f = c[min(int(k * FPS), len(c) - 1)]
    img = cv2.resize(cv2.GaussianBlur(cv2.resize(f, (135, 240)), (0, 0), 5), (W, H)).astype(np.float32) / 255 * 0.4
    img[656:1264] = f.astype(np.float32) / 255
    return img

def popk(t, t0): return 1 + 0.3 * max(0, 1 - (t - t0) / 0.12) ** 2
def card_img(path, box):
    im = cv2.imread(path); s = box / max(im.shape[:2]); c = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    c[:6] = c[-6:] = c[:, :6] = c[:, -6:] = (60, 190, 255)
    return glow_rgba(np.dstack([c[..., ::-1].astype(np.float32) / 255, np.ones(c.shape[:2], np.float32)]), (255, 190, 60), 16, 1.0)
RAP = [(V(18.80), "rickross.jpg", "RICK ROSS"), (V(19.60), "2chainz.jpg", "2 CHAINZ"), (V(20.48), "gucci.jpg", "GUCCI MANE"), (V(21.28), "kanye.jpg", "KANYE WEST")]
BM = [(V(42.96), "zaytoven.jpg", "ZAYTOVEN"), (V(44.08), "youngchop.jpg", "YOUNG CHOP"), (V(44.64), "metroboomin.webp", "METRO BOOMIN"),
      (V(45.60), "mikewill.jpg", "MIKE WILL MADE-IT"), (V(46.96), "southside.jpg", "SOUTHSIDE"), (V(47.52), "sonnydigital.jpg", "SONNY DIGITAL"),
      (V(48.48), "londonontrack.webp", "LONDON ON DA TRACK"), (V(49.68), "lexluger.webp", "LEX LUGER")]
RAPI = [card_img(f"{WORK}/{f}", 470) for _, f, _ in RAP]; BMI = [card_img(f"{WORK}/{f}", 320) for _, f, _ in BM]
def grid(img, t, items, ims, cols, xs, ys, lsize):
    for n, ((t0, _, lbl), im) in enumerate(zip(items, ims)):
        if t < t0: continue
        x, y = xs[n % cols], ys[n // cols]
        paste(img, im, x, y, popk(t, t0)); lb, _ = neon(lbl, lsize, YEL); paste(img, lb, x, y + im.shape[0] / 2 + 4)
HOOK = block("FL STUDIO", "C'EST COMPLIQUÉ ?", 1000, 520)
C1 = block("1 AN DE", "BEATMAKING", 1000, 700)
C2 = block("MONSIEUR VASS", "ON THE BEAT", 1000, 700)
END = block("LE BIG", "VASS", 900, 600)
LOGO = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 560)
NOTE = rgba_file(os.path.join(LIB, "3d", "music-note-gold.png"), 480)
def card(img, im, t, t0, y):
    k = t - t0; paste(img, im, W / 2, y, 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1))
def pop3d(img, im, t, t0, x, y, life=2.0):
    k = t - t0
    if 0 <= k < life: paste(img, im, x, y, popk(t, t0) * (1 + 0.03 * k), min(k / 0.08, 1) * min((life - k) / 0.25, 1))

# ---------- scenes (output seconds) ; captions are hidden where nocap is True ----------
SCENES = [  # start, end, kind, captions
    (0.0, INTRO, "radio", True), (V(0), V(4.0), "c728", True), (V(4.0), V(12.0), "c726", True), (V(12.0), V(16.2), "c723", True),
    (V(16.2), V(22.3), "rap", False), (V(22.3), V(31.6), "c722", True), (V(31.6), V(40.0), "c725", True), (V(40.0), V(50.6), "bm", False),
    (V(50.6), V(56.0), "c721", True), (V(56.0), V(60.0), "c723b", True), (V(60.0), V(66.2), "c722b", True), (V(66.2), V(68.3), "otb", False),
    (V(68.3), V(72.8), "c728b", True), (V(72.8), DUR + 1, "end", False)]
def scene(t):
    for s in SCENES:
        if s[0] <= t < s[1]: return s
    return SCENES[-1]
def draw(t):
    a, b, kind, _ = scene(t); k = t - a
    if kind == "radio":
        img = radio(t)
        if t < 1.5: card(img, block("T'AS DÉJÀ ÉTÉ", "RAPPEUR ?", 1000, 420), t, 0.0, 400)
        elif 4.7 <= t < 9.0: card(img, HOOK, t, 4.8, 400)
        elif t >= 9.1: stack(img, t, [(9.16, "FL, C'EST FACILE", GRN)], 130, 420, 0)
        return img
    if kind == "rap":
        img = bg("paper_red", t)
        stack(img, t, [(V(16.3), "LES TYPE BEATS", WHT), (V(16.8), "SUR YOUTUBE", YEL)], 120, 210, 140)
        grid(img, t, RAP, RAPI, 2, (290, 790), (700, 1340), 74); return img
    if kind == "bm":
        img = bg("black", t)
        stack(img, t, [(V(40.0), "J'ÉTAIS FAN", WHT), (V(42.08), "DES BEATMAKERS", GOLD)], 100, 140, 115)
        grid(img, t, BM, BMI, 2, (290, 790), (480, 860, 1240, 1620), 60); return img
    if kind == "otb":
        img = bg("red", t); card(img, C2, t, a, 960); pop3d(img, NOTE, t, a + 0.3, 860, 1500); return img
    if kind == "end":
        img = cam("00728", 9.0, k, 4.0) * 0.45; paste(img, LOGO, W / 2, 650, min(k / 0.25, 1) * 0.15 + 0.85); card(img, END, t, a, 1300); return img
    src = {"c728": ("00728", 2.0), "c726": ("00726", 0.3), "c723": ("00723", 0.5), "c722": ("00722", 3.0), "c725": ("00725", 0.2),
           "c721": ("00721", 0.0), "c723b": ("00723", 5.5), "c722b": ("00722", 12.0), "c728b": ("00728", 5.0)}[kind]
    img = cam(src[0], src[1], k, b - a + 0.5)
    if kind == "c728": stack(img, t, [(V(1.28), "J'ÉTAIS OBLIGÉ", WHT), (V(2.08), "DE VOUS EN PARLER", YEL)], 120, 330, 150)
    elif kind == "c726":
        stack(img, t, [(V(4.16), "JE ME SUIS LANCÉ", WHT), (V(4.80), "DANS LE BEATMAKING", YEL)], 110, 330, 140)
        if t >= V(9.44): card(img, C1, t, V(9.44), 1000)
    elif kind == "c723": stack(img, t, [(V(14.40), "AU LYCÉE", YEL)], 170, 330, 0)
    elif kind == "c722": stack(img, t, [(V(22.30), "J'ÉTAIS HYPÉ", YEL), (V(31.28), "LE BEAT", RED)], 150, 330, 190); pop3d(img, NOTE, t, V(31.28), 860, 760)
    elif kind == "c725": stack(img, t, [(V(32.72), "LE MIX", WHT), (V(33.68), "LES PAROLES", YEL), (V(37.84), "ÇA CHANGE LA DONNE", RED)], 130, 330, 165)
    elif kind == "c721": stack(img, t, [(V(50.60), "ÉNORMÉMENT", WHT), (V(54.56), "M'ONT INSPIRÉ", YEL)], 140, 1350, 170)
    elif kind == "c723b": stack(img, t, [(V(56.56), "UN CHALLENGE", YEL)], 150, 330, 0)
    elif kind == "c722b": stack(img, t, [(V(60.00), "QUELQUES ÉPISODES", WHT), (V(64.48), "MON ÉVOLUTION", YEL), (V(65.52), "SOYEZ PRÊTS", RED)], 120, 330, 155)
    elif kind == "c728b": stack(img, t, [(V(70.72), "LIKE", WHT), (V(71.20), "COMMENTE", YEL), (V(71.60), "PARTAGE", RED)], 150, 330, 180)
    return img

# ---------- captions (neon Anton, one word at a time, y 1660) ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: G,Anton,140,&H6000E5FF,&H0000E5FF,&H8000C8FF,&H00000000,0,0,0,0,100,100,1,0,1,10,0,5,40,40,0,1
Style: W,Anton,140,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,4,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
WHITE = {"rick", "ross", "chainz", "gucci", "mane", "kanye", "west", "zaytoven", "young", "chop", "metro", "boomin", "mike", "will", "made-it",
         "southside", "sonny", "digital", "london", "lex", "luger", "fl", "studio", "monsieur", "vass", "youtube"}
REDW = {"beatmaking", "challenge", "challenges", "an", "hypé", "beat", "mix", "paroles"}
key = lambda w: w["w"].lower().strip(",.?!…« »")
for w in words:
    sc = scene(w["s"])
    if w["nc"] or not sc[3]: continue
    if sc[2] == "radio" and (w["s"] < 1.5 or 4.7 <= w["s"]): continue      # the 3D cards already say it
    col = r"\c&H002A2AFF&\3c&H002A2AFF&" if key(w) in REDW else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if key(w).split()[0] in WHITE else "")
    txt = w["w"].upper().strip(",.?!… ") or w["w"]
    pop = r"\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)"
    y = 1500 if sc[2] == "radio" else 1660
    ass.append(f"Dialogue: 0,{ts(w['s'])},{ts(max(w['e'], w['s'] + 0.15))},G,,0,0,0,,{{\\an5\\pos(540,{y}){col}\\blur14{pop}}}{txt}")
    ass.append(f"Dialogue: 1,{ts(w['s'])},{ts(max(w['e'], w['s'] + 0.15))},W,,0,0,0,,{{\\an5\\pos(540,{y}){col.split(chr(92) + '3c')[0] if col else ''}{pop}}}{txt}")
open(f"{WORK}/caps_bm.ass", "w").write("\n".join(ass) + "\n")

# ---------- transitions (his library, screen blend, peak on the cut) ----------
def trans(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions", name), "-vf", f"fps={FPS},scale=-2:{H},crop={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
TR = {"burn": (trans("burn-transition-12.mp4"), 11 / 30), "red": (trans("red-flash-39.mp4"), 17 / 30),
      "bw": (trans("bw-flash-33.mp4"), 4 / 23.976), "light": (trans("light-flash-23.mp4"), 5 / 23.976)}
TRANS = [(V(0), "burn"), (V(4.0), "light"), (V(16.2), "red"), (V(22.3), "bw"), (V(31.6), "light"), (V(40.0), "red"), (V(50.6), "bw"),
         (V(56.0), "light"), (V(60.0), "red"), (V(66.2), "burn"), (V(68.3), "bw"), (V(72.8), "red")]

VIDEO_ONLY = f"{WORK}/video_only_bm.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", f"vignette=angle=PI/6,noise=alls=3:allf=t+u,ass={WORK}/caps_bm.ass:fontsdir={os.path.dirname(ANTON)},format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", VIDEO_ONLY], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; img = draw(t)
    a = scene(t)[0]
    if 0 < t - a < 0.07 and a > 0: img = np.clip(img + (0.07 - (t - a)) / 0.07 * 0.5, 0, 1)
    for t0, name in TRANS:
        fr, pk = TR[name]; j = int(round((t - (t0 - pk)) * FPS))
        if 0 <= j < len(fr): img = 1 - (1 - img) * (1 - fr[j].astype(np.float32) / 255)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if n % 300 == 0: print(f"frame {n}/{N}", flush=True)
enc.stdin.close(); enc.wait()

# ---------- sound: radio clip (quiet source, brought to -14 LUFS), then his voice-over on the beat as recorded ----------
wh = ";".join(f"[{3 + m}:a]adelay={int(max(t0 - 0.13, 0) * 1000)}|{int(max(t0 - 0.13, 0) * 1000)},volume=0.2[w{m}]" for m, (t0, _) in enumerate(TRANS))
ins = sum([["-i", os.path.join(LIB, "sfx", f"whoosh-{(m % 4) + 1}.mp3")] for m in range(len(TRANS))], [])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", f"{WORK}/intro.mov", "-i", f"{WORK}/beat.mp3", *ins, "-filter_complex",
    f"[1:a]atrim=0:{INTRO},asetpts=N/SR/TB,loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000,afade=t=out:st={INTRO - 0.15}:d=0.15,apad=whole_dur={INTRO}[r];"
    f"[2:a]aresample=48000,asetpts=N/SR/TB[v];[r][v]concat=n=2:v=0:a=1[s];{wh};"
    "[s]" + "".join(f"[w{m}]" for m in range(len(TRANS))) + f"amix=inputs={1 + len(TRANS)}:normalize=0:duration=first,"
    "alimiter=limit=0.7:level=false,aformat=sample_fmts=s16:channel_layouts=stereo[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, f"{DUR:.1f}s", flush=True)
