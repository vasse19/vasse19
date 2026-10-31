"""whisper: transcribe audio/video with OpenAI Whisper (ONNX via sherpa-onnx).
Usage: whisper FILE [--lang fr] [--model small] [--out PREFIX]
Writes PREFIX.txt and PREFIX.srt (default PREFIX = FILE without extension)."""
import argparse, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf, sherpa_onnx
ap = argparse.ArgumentParser()
ap.add_argument("file"); ap.add_argument("--lang", default="fr"); ap.add_argument("--model", default="small")
ap.add_argument("--out"); ap.add_argument("--int8", action="store_true", help="faster, slightly less accurate")
a = ap.parse_args()
md = os.path.expanduser(f"~/models/sherpa-onnx-whisper-{a.model}")
q = ".int8" if a.int8 else ""
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{md}/{a.model}-encoder{q}.onnx", decoder=f"{md}/{a.model}-decoder{q}.onnx",
    tokens=f"{md}/{a.model}-tokens.txt", language=a.lang, task="transcribe", num_threads=os.cpu_count())
with tempfile.TemporaryDirectory() as td:
    wav = os.path.join(td, "a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-i", a.file, "-ac", "1", "-ar", "16000", "-y", wav], check=True)
    audio, sr = sf.read(wav, dtype="float32")
# split into <= 28 s chunks at the quietest point (Whisper works on 30 s windows)
hop = int(0.05 * sr)
rms = np.array([np.sqrt(np.mean(audio[i:i + hop] ** 2)) for i in range(0, max(len(audio) - hop, 1), hop)])
dur = len(audio) / sr; cuts = [0.0]
while dur - cuts[-1] > 28:
    lo, hi = int((cuts[-1] + 15) / 0.05), int((cuts[-1] + 28) / 0.05)
    cuts.append((lo + int(np.argmin(rms[lo:hi]))) * 0.05)
cuts.append(dur)
segs = []
for s, e in zip(cuts, cuts[1:]):
    st = rec.create_stream(); st.accept_waveform(sr, audio[int(s * sr):int(e * sr)]); rec.decode_stream(st)
    text = st.result.text.strip()
    if text: segs.append((s, e, text)); print(f"[{s:6.1f}-{e:6.1f}] {text}", flush=True)
def ts(t): return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(t*1000)%1000:03d}"
out = a.out or os.path.splitext(a.file)[0]
open(out + ".txt", "w").write("\n".join(t for _, _, t in segs) + "\n")
open(out + ".srt", "w").write("\n".join(f"{i+1}\n{ts(s)} --> {ts(e)}\n{t}\n" for i, (s, e, t) in enumerate(segs)))
print(f"-> {out}.txt  {out}.srt", file=sys.stderr)
