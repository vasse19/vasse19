import json, sys, re, subprocess
import numpy as np, soundfile as sf, sherpa_onnx
wav, out, md = sys.argv[1], sys.argv[2], sys.argv[3]
audio, sr = sf.read(wav, dtype="float32")
# silence midpoints as candidate cut points
log = subprocess.run(["ffmpeg","-i",wav,"-af","silencedetect=n=-35dB:d=0.3","-f","null","-"],capture_output=True,text=True).stderr
starts=[float(x) for x in re.findall(r"silence_start: ([\d.]+)",log)]
ends=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",log)]
mids=[(a+b)/2 for a,b in zip(starts,ends)]
dur=len(audio)/sr; hop=int(0.05*sr)
rms=np.array([np.sqrt(np.mean(audio[i:i+hop]**2)) for i in range(0,len(audio)-hop,hop)])
cuts=[0.0]
while dur-cuts[-1]>14:
    lo,hi=int((cuts[-1]+7)/0.05),int((cuts[-1]+14)/0.05)
    cuts.append((lo+int(np.argmin(rms[lo:hi])))*0.05+0.025)
cuts.append(dur)
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{md}/encoder.int8.onnx",decoder=f"{md}/decoder.int8.onnx",joiner=f"{md}/joiner.int8.onnx",tokens=f"{md}/tokens.txt",model_type="nemo_transducer",num_threads=4)
words=[]
for a,b in zip(cuts,cuts[1:]):
    st=rec.create_stream(); st.accept_waveform(sr,audio[int(a*sr):int(b*sr)]); rec.decode_stream(st)
    r=st.result; print(f"[{a:6.2f}-{b:6.2f}] {r.text}",file=sys.stderr)
    cur=None
    for tok,t in zip(r.tokens,r.timestamps):
        t+=a
        if tok.startswith(" ") or cur is None:
            if cur: words.append(cur)
            cur={"w":tok.strip(),"s":t,"e":t+0.25}
        else:
            cur["w"]+=tok; cur["e"]=t+0.25
    if cur: words.append(cur)
for i in range(len(words)-1):
    words[i]["e"]=min(max(words[i]["e"],words[i]["s"]+0.12),words[i+1]["s"])
json.dump(words,open(out,"w"),ensure_ascii=False,indent=0)
