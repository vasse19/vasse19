"""Vertical TikTok version of a 16:9 scene with French subtitles: the scene as a band in the middle over a blurred,
darkened copy of itself, his logo top left, one subtitle colour per speaker (A white, B yellow) under the band,
original sound as is (safety limiter only), optional small blur over a channel logo.
usage: tiktok_sous_titres.py VIDEO CUES.txt OUT.mp4 [x:y:w:h of the logo to blur, in source pixels]
CUES.txt: one cue per line, « start|end|A or B|text »"""
import sys, os, subprocess

VIDEO, CUES, OUT = sys.argv[1:4]
LOGO_BOX = sys.argv[4] if len(sys.argv) > 4 else None
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOGO = os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png")
W, H, BAND_Y = 1080, 1920, 600                      # band 1080x608 starts at y 600, subtitles under it

def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: A,Poppins Black,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,3,8,70,70,0,1
Style: B,Poppins Black,80,&H0028DEFF,&H0028DEFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,3,8,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
for line in open(CUES, encoding="utf-8"):
    if not line.strip() or line.startswith("#"): continue
    s, e, who, txt = line.rstrip("\n").split("|", 3)
    pop = r"{\fad(60,60)\fscx90\fscy90\t(0,100,\fscx100\fscy100)}"
    ass.append(f"Dialogue: 0,{ts(float(s))},{ts(float(e))},{who},,0,0,{BAND_Y + 608 + 70},,{pop}{txt}")
SUBS = os.path.splitext(OUT)[0] + ".ass"
open(SUBS, "w", encoding="utf-8").write("\n".join(ass) + "\n")

src = "[0:v]" + (f"delogo=x={LOGO_BOX.split(':')[0]}:y={LOGO_BOX.split(':')[1]}:w={LOGO_BOX.split(':')[2]}:h={LOGO_BOX.split(':')[3]}," if LOGO_BOX else "")
fc = (f"{src}split[a][b];"
      f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.18:saturation=0.8[bg];"
      f"[b]scale={W}:-2:flags=lanczos,unsharp=5:5:0.6[fg];"
      f"[bg][fg]overlay=0:{BAND_Y}[v1];"
      f"[1:v]scale=190:-1[lg];[v1][lg]overlay=30:30,"
      f"ass={SUBS}:fontsdir={os.path.expanduser('~/.fonts')},format=yuv420p[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-i", LOGO, "-filter_complex", fc,
                "-map", "[v]", "-map", "0:a", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                "-af", "aresample=48000,alimiter=limit=0.89:level=false", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000",
                "-movflags", "+faststart", OUT], check=True)
print("done", OUT)
