import sys, soundfile as sf, sherpa_onnx
wav, md = sys.argv[1], sys.argv[2]
audio, sr = sf.read(wav, dtype="float32")
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{md}/encoder.int8.onnx",decoder=f"{md}/decoder.int8.onnx",joiner=f"{md}/joiner.int8.onnx",tokens=f"{md}/tokens.txt",model_type="nemo_transducer",num_threads=4)
for w in sys.argv[3:]:
    a,b=map(float,w.split("-"))
    st=rec.create_stream(); st.accept_waveform(sr,audio[int(a*sr):int(b*sr)]); rec.decode_stream(st)
    print(f"[{a}-{b}] {st.result.text}")
