import sys, json, soundfile as sf, sherpa_onnx
wav, md, out = sys.argv[1], sys.argv[2], sys.argv[3]
audio, sr = sf.read(wav, dtype="float32")
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{md}/encoder.int8.onnx",decoder=f"{md}/decoder.int8.onnx",joiner=f"{md}/joiner.int8.onnx",tokens=f"{md}/tokens.txt",model_type="nemo_transducer",num_threads=4)
words=[]
for w in sys.argv[4:]:
    a,b=map(float,w.split("-"))
    st=rec.create_stream(); st.accept_waveform(sr,audio[int(a*sr):int(b*sr)]); rec.decode_stream(st)
    r=st.result; cur=None
    for tok,t in zip(r.tokens,r.timestamps):
        t+=a
        if tok.startswith(" ") or cur is None:
            if cur: words.append(cur)
            cur={"w":tok.strip(),"s":t,"e":t+0.25}
        else: cur["w"]+=tok; cur["e"]=t+0.25
    if cur: words.append(cur)
    print(f"[{a}-{b}]", r.text)
json.dump(words,open(out,"w"),ensure_ascii=False)
print(" ".join(f"{x['w']}@{x['s']:.2f}" for x in words))
