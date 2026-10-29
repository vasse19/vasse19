import json, sys, subprocess, numpy as np, cv2, math
src, faces, words, ass, out = sys.argv[1:6]
limit = float(sys.argv[6]) if len(sys.argv)>6 else None   # (start,dur) preview
start = float(sys.argv[7]) if len(sys.argv)>7 else 0.0
W,H,FPS,OW,OH = 1920,1080,25,1080,1920
dur=89.44; N=int(dur*FPS)
# --- face track -> smooth horizontal centre
f=np.array([d for d in json.load(open(faces)) if d[1]>800 and d[2]<900])
t,x,yy=f[:,0],f[:,1],f[:,2]
med=np.array([np.median(x[(t>tt-1.5)&(t<tt+1.5)]) for tt in t])
keep=np.abs(x-med)<150; t,x,yy=t[keep],x[keep],yy[keep]
ft=np.arange(N)/FPS
cx=np.interp(ft,t,x)
k=int(FPS*0.8); ker=np.ones(2*k+1)/(2*k+1)
cx=np.convolve(np.pad(cx,k,mode="edge"),ker,mode="valid")
cx=np.convolve(np.pad(cx,k,mode="edge"),ker,mode="valid")
cy=np.interp(ft,t,yy)
cy=np.convolve(np.pad(cy,k,mode="edge"),ker,mode="valid")
cy=np.convolve(np.pad(cy,k,mode="edge"),ker,mode="valid")
# --- zoom envelope: punch-ins on emphasis words, gentle push while talking
w=json.load(open(words))
z=np.full(N,1.12)
speech_start=w[0]["s"]
z+=0.07*np.clip((ft-speech_start)/0.6,0,1)          # tighter framing once talking starts
def punch(t0,amt,hold=0.35,rel=0.5):
    a=np.clip((ft-t0)/0.08,0,1); a=a*a*(3-2*a)
    r=np.clip((ft-t0-hold)/rel,0,1); r=r*r*(3-2*r)
    return amt*a*(1-r)
shake=np.zeros((N,2))
for x_ in w:
    lw=x_["w"].lower()
    if lw in {"tiens !","bam!","carré!"}:
        z+=punch(x_["s"],0.22)
        m=(ft>=x_["s"])&(ft<x_["s"]+0.3)
        shake[m]=np.random.default_rng(1).normal(0,9,(m.sum(),2))*np.linspace(1,0,m.sum())[:,None]
    elif lw in {"boost","vérité","fort","commentaire !"}:
        z+=punch(x_["s"],0.12,0.4,0.6)
# word-onset micro bounce while talking
for x_ in w: z+=punch(x_["s"],0.012,0.05,0.2)
s0=int(start*FPS); n=int((limit or dur)*FPS); n=min(n,N-s0)
dec=subprocess.Popen(["ffmpeg","-v","error","-ss",str(start),"-i",src,"-frames:v",str(n),"-f","rawvideo","-pix_fmt","bgr24","-"],stdout=subprocess.PIPE)
VF=("eq=contrast=1.10:saturation=0.78:gamma=0.97,curves=all='0/0.05 0.25/0.22 0.75/0.78 1/0.95',"
    "colorbalance=rs=-0.06:bs=0.07:rm=0.03:bm=-0.02:rh=0.05:gh=0.02:bh=-0.05,"
    f"vignette=angle=PI/6,noise=alls=7:allf=t+u,ass={ass},format=yuv420p")
enc=subprocess.Popen(["ffmpeg","-v","error","-f","rawvideo","-pix_fmt","bgr24","-s",f"{OW}x{OH}","-r",str(FPS),"-i","-",
    "-ss",str(start),"-t",str(n/FPS),"-i",src,"-map","0:v","-map","1:a","-vf",
    VF if start==0 else VF.replace(f"ass={ass}",f"setpts=PTS+{start}/TB,ass={ass},setpts=PTS-STARTPTS"),
    "-c:v","libx264","-preset","medium","-crf","20","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest","-y",out],stdin=subprocess.PIPE)
for i in range(s0,s0+n):
    buf=dec.stdout.read(W*H*3)
    if len(buf)<W*H*3: break
    fr=np.frombuffer(buf,np.uint8).reshape(H,W,3)
    ch=H/z[i]; cw=ch*OW/OH
    x0=float(np.clip(cx[i]+shake[i,0]-cw/2,0,W-cw)); y0=float(np.clip(cy[i]+shake[i,1]-ch*0.5+(H/2-cy[i])*(1-1/z[i])*0,0,H-ch))
    y0=float(np.clip(cy[i]-ch*0.47+shake[i,1],0,H-ch))
    M=np.array([[OW/cw,0,-x0*OW/cw],[0,OH/ch,-y0*OH/ch]])
    enc.stdin.write(cv2.warpAffine(fr,M,(OW,OH),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE).tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
