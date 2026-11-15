"""4 vertical Shorts cut from the finished 16:9 YouTube video (Didi B, Shogun in Lagos), Kali style:
blurred copy of the frame as background, the 16:9 video in a glowing card, his 3D title on top,
neon word captions underneath (re-transcribed from the cut audio, names fixed), end card « LA VIDÉO COMPLÈTE SUR YOUTUBE ».
usage: shorts_shogun.py FULL_16x9.mp4 WORK OUTDIR   (first run transcribes and prints the words, then renders)"""
import sys, os, json, subprocess, numpy as np, cv2, soundfile as sf
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import W, H, FPS, LIB, ANTON, YEL, RED, WHT, paste, neon, glow_rgba, rgba_file, bg, block

SRC, WORK, OUTDIR = sys.argv[1:4]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MODEL = "/root/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
os.makedirs(WORK, exist_ok=True)

COMMON = {"djb": "Didi B", "jdb": "Didi B", "dj": None, "b": None, "didible": "Didi B", "djibé": "Didi B", "legos": "Lagos", "l'ego": "Lagos ?",
          "mixtep": "mixtape", "chartes": "charts", "latan": "Zlatan", "finos": "Phyno", "finot": "Phyno", "tyque": "Tayc"}
SHORTS = [  # name, [(start, end) ranges in the finished video, joined], ~1 min each, 3D title (chrome | red), word fixes, emphasis words (white / red)
    ("shogun_seul_sur_scene_lagos", [(266.95, 329.25)], "SEUL SUR SCÈNE", "À LAGOS ?", {"_repl": [
        (0.4, 7.95, "Deux jours après la sortie, le dimanche 8 novembre, Didi_B donne son tout premier concert au Nigeria, à l'Afrika Shrine."),
        (8.3, 13.6, "La salle mythique de Fela Kuti. Le symbole est fort et la soirée est annoncée guichet fermé."),
        (16.8, 22.3, "tels que Young Jonn, Zinoleesky, Zlatan, Qing Madi."), (29.4, 29.9, "nigérians de"), (39.4, 40.2, "saluent son courage."),
        (46.9, 48.25, "au Nigeria, Didi_B")], "zinolensky": "Zinoleesky"}, {"lagos", "nigeria", "shrine", "fela", "kuti", "zinoleesky", "good", "vibes"}, {"zéro", "surprise", "seul", "polémique", "personne", "courage"}),
    ("shogun_zenith_planete_rap", [(81.05, 131.75)], "LE ZÉNITH", "COMPLET", {"_clip": (27.93, 39.93, "c4.json", 8.95), "fali": "Fally", "ibele": "Ibile", "2025,": None, "_repl": [(10.8, 11.6, "février,")]}, {"zénith", "paris", "fally", "stade", "france", "juventus", "nueva", "era", "zlatan", "spotify"}, {"millions", "fermé", "sold", "out", "big"}),
    ("shogun_pourquoi_lagos", [(0.0, 26.40), (54.75, 81.05)], "IL A TOUT GAGNÉ…", "POURQUOI LAGOS ?", {"gilbe": "Didi B", "disible": "Didi B", "type": "Tayc.",
        "jb": "Didi B", "didib": "Didi B", "disib": "Didi B", "légos": "Lagos ?", "nigerien": "Nigeria.",
        "_repl": [(3.7, 4.9, "Shogun in Lagos."), (10.1, 11.5, "En Côte d'Ivoire, la mixtape"), (14.5, 15.9, "cette même mixtape"),
                  (26.4, 32.9, "Quelque temps après, après avoir quitté le 92i, il sort son autre projet en 2025…"), (35.2, 36.6, "à l'APRODEMCI en Côte d'Ivoire."),
                  (43.0, 44.3, "Félix-Houphouët-Boigny"), (44.6, 45.5, "30_000"), (46.8, 47.7, "Alpha Blondy")], "_drop": [(25.95, 26.4)]}, {"shogun", "lagos", "davido", "zlatan", "phyno", "tayc", "apple", "music", "nigeria", "92i", "aprodemci", "félix-houphouët-boigny", "alpha", "blondy"}, {"platine", "30 000", "gagné", "première", "risque", "recommencer"}),
    ("shogun_son_avec_davido", [(190.30, 248.45)], "LE SON AVEC", "DAVIDO", {"fuck": "F***", "finno": "Phyno,", "join": "Jonn,", "gana": "Ghana", "prom": "Promise,", "focalistique": "Focalistic,", "nsg": "NSG.",
        "_repl": [(3.1, 3.95, "il y a"), (12.0, 12.7, "Qing Madi,"), (17.7, 18.7, "il a mis Tayc"), (27.4, 28.5, "prod amapiano"), (40.1, 40.5, "carrément")]}, {"davido", "youtube", "clip", "phyno", "zlatan", "young", "jonn", "qing", "madi", "mavo", "king", "promise", "focalistic", "tayc", "nsg", "nigeria", "ghana"}, {"exclusivités", "attendu", "sale", "banger", "fuck"}),
]

def cut(name, rng):
    """The short's source: one or several ranges of the finished video, joined."""
    out = f"{WORK}/{name}_src.mp4"
    if not os.path.exists(out):
        fc = "".join(f"[0:v]trim={x}:{y},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={x}:{y},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={y - x - 0.05:.3f}:d=0.05[a{i}];"
                     for i, (x, y) in enumerate(rng))
        fc += "".join(f"[v{i}][a{i}]" for i in range(len(rng))) + f"concat=n={len(rng)}:v=1:a=1[v][a]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16",
                        "-preset", "fast", "-c:a", "aac", "-b:a", "256k", out], check=True)
    return out, sum(y - x for x, y in rng)
def asr(name, a, b):
    js = f"{WORK}/{name}.json"
    if os.path.exists(js): return json.load(open(js))
    wav = f"{WORK}/{name}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", CUR, "-ac", "1", "-ar", "16000", wav], check=True)
    d = b - a; wins = [f"{i}-{min(i + 15, d):.2f}" for i in range(0, int(d) + 1, 15) if i < d - 0.3]
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "asr_words_win.py"), wav, MODEL, js] + wins, check=True, stdout=subprocess.DEVNULL)
    return json.load(open(js))

def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: G,Anton,128,&H6000E5FF,&H0000E5FF,&H8000C8FF,&H00000000,0,0,0,0,100,100,1,0,1,10,0,5,40,40,0,1
Style: W,Anton,128,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,4,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""

# end card (2.6 s): his red background, logo, « LA VIDÉO COMPLÈTE SUR YOUTUBE »
END_DUR = 2.6
endmp4 = f"{WORK}/endcard.mp4"
if not os.path.exists(endmp4):
    logo = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 560)
    ttl = block("LA VIDÉO COMPLÈTE", "SUR YOUTUBE", 1000, 620)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", os.path.join(LIB, "sfx/synth-hit.wav"), "-filter_complex", "[1:a]volume=0.5,apad,aresample=48000[a]",
                            "-map", "0:v", "-map", "[a]", "-t", str(END_DUR), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", endmp4], stdin=subprocess.PIPE)
    for i in range(int(END_DUR * FPS)):
        t = i / FPS; img = bg("red", t) * 0.7
        paste(img, logo, W / 2, 560, 0.9 + 0.1 * min(t / 0.25, 1))
        paste(img, ttl, W / 2, 1180, 0.55 + 0.5 * min(t / 0.12, 1) - 0.05 * min(max(t - 0.12, 0) / 0.1, 1))
        im, _ = neon("LIEN EN DESCRIPTION / EN BIO", 54, YEL); paste(img, im, W / 2, 1600, 1.0, min(max(t - 0.5, 0) / 0.15, 1))
        enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()

CARD_W, CARD_Y = 1000, 900
CARD_H = int(CARD_W * 9 / 16)
g = glow_rgba(np.dstack([np.zeros((CARD_H, CARD_W, 3), np.float32), np.ones((CARD_H, CARD_W), np.float32)]), (255, 255, 255), 24, 1.1)
cv2.imwrite(f"{WORK}/glow.png", (np.dstack([g[..., [2, 1, 0]], g[..., 3:]]) * 255).astype(np.uint8))

ONLY = os.environ.get("ONLY")
os.makedirs(OUTDIR, exist_ok=True)
for name, rng, top, bot, fixes, white, red in SHORTS:
    if ONLY and ONLY not in name: continue
    CUR, b = cut(name, rng); a = 0.0
    words = asr(name, a, b)
    fx = {**COMMON, **fixes}
    for t0, t1, text in fixes.get("_repl", []):          # passages the ASR got wrong: his exact words, spread over the same time
        words = [w for w in words if not (t0 <= w["s"] < t1)]; toks = text.split(); L = sum(len(x) + 2 for x in toks); acc = 0
        for x in toks: words.append({"w": x.replace("_", " "), "s": t0 + (t1 - t0) * acc / L}); acc += len(x) + 2
    if "_clip" in fixes:                                  # interview inserted in the video: words from the clip's own transcript
        c0, c1, js, ss = fixes["_clip"]; cw = json.load(open(os.path.join(WORK, "..", "clips", js)))
        words = [w for w in words if not (c0 <= w["s"] < c1)] + [{"w": w["w"], "s": c0 + w["s"] - ss} for w in cw if ss <= w["s"] < ss + (c1 - c0) - 0.1]
    words = sorted([w for w in words if not any(x <= w["s"] < y for x, y in fixes.get("_drop", []))], key=lambda w: w["s"])
    out_words = []
    for w in words:
        k = w["w"].lower().strip(",.?!…«» :")
        if k in fx and not k.startswith("_"):
            if fx[k] is None: continue
            w = {**w, "w": fx[k]}
        out_words.append(w)
    for i, w in enumerate(out_words):
        nxt = out_words[i + 1]["s"] if i + 1 < len(out_words) else b - a
        w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
    print(name, " | ".join(f"{w['w']}@{w['s']:.2f}" for w in out_words), flush=True)
    if os.environ.get("WORDS_ONLY"): continue
    ass = [HEAD]
    for w in out_words:
        key = w["w"].lower().strip(",.?!…«» :")
        col = r"\c&H002A2AFF&\3c&H002A2AFF&" if key in red else (r"\c&H00FFFFFF&\3c&H00FFFFFF&" if key in white else "")
        txt = w["w"].upper().strip(",.… ") or w["w"]
        pop = r"\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)"
        s0, e0 = w["s"], max(w["e"], w["s"] + 0.15)
        ass.append(f"Dialogue: 0,{ts(s0)},{ts(e0)},G,,0,0,0,,{{\\an5\\pos(540,1480){col}\\blur14{pop}}}{txt}")
        ass.append(f"Dialogue: 1,{ts(s0)},{ts(e0)},W,,0,0,0,,{{\\an5\\pos(540,1480){col.split(chr(92) + '3c')[0] if col else ''}{pop}}}{txt}")
    open(f"{WORK}/{name}.ass", "w").write("\n".join(ass) + "\n")
    t3 = block(top, bot, 1000, 470)
    Image.fromarray((t3 * 255).astype(np.uint8)).save(f"{WORK}/{name}_title.png")
    out = os.path.join(OUTDIR, f"{name}.mp4")
    fc = (f"[0:v]split[a][b];[a]scale=-2:{H},crop={W}:{H},boxblur=40:4,eq=brightness=-0.32:saturation=1.2[bgv];"
          f"[b]scale={CARD_W}:{CARD_H}[fg];[bgv][2:v]overlay=(W-w)/2:{CARD_Y}-h/2:shortest=1[g1];[g1][fg]overlay=(W-w)/2:{CARD_Y}-h/2[g2];"
          f"[1:v]format=rgba,fade=in:st=0:d=0.15:alpha=1[ti];[g2][ti]overlay=(W-w)/2:330-h/2:shortest=1[g3];"
          f"[g3]ass={WORK}/{name}.ass:fontsdir={os.path.dirname(ANTON)},fps={FPS},format=yuv420p,setsar=1[mv];"
          f"[0:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=out:st={b - a - 0.25:.2f}:d=0.25[ma];"
          f"[3:v]fps={FPS},format=yuv420p,setsar=1[ev];[3:a]aformat=channel_layouts=stereo[ea];[mv][ma][ev][ea]concat=n=2:v=1:a=1[v][au]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", CUR, "-loop", "1", "-i", f"{WORK}/{name}_title.png",
                    "-loop", "1", "-i", f"{WORK}/glow.png", "-i", endmp4, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[au]", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print("done", out, flush=True)
