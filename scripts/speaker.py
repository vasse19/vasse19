import cv2, numpy as np, sys, json
cap=cv2.VideoCapture(sys.argv[1]); fps=cap.get(cv2.CAP_PROP_FPS)
# mouth regions (full-res 1080x1920): woman top ~ (x 200-560, y 520-760) ; man bottom ~ (x 220-560, y 1460-1640)
regs={"top":(150,620,450,800),"bot":(200,560,1420,1680)}
prev=None; out=[]
while True:
    ok,f=cap.read()
    if not ok: break
    g=cv2.cvtColor(cv2.resize(f,(540,960)),cv2.COLOR_BGR2GRAY).astype(np.float32)
    if prev is not None:
        d=np.abs(g-prev)
        out.append([float(d[y0//2:y1//2,x0//2:x1//2].mean()) for (x0,x1,y0,y1) in regs.values()])
    prev=g
a=np.array(out); k=15
sm=np.array([np.convolve(a[:,i],np.ones(k)/k,mode="same") for i in range(2)]).T
for t in range(0,len(sm),15): print(f"{t/fps:5.1f} top {sm[t,0]:5.2f} bot {sm[t,1]:5.2f} {'TOP' if sm[t,0]>sm[t,1]*1.3 else ('BOT' if sm[t,1]>sm[t,0]*1.3 else '-')}")
json.dump(sm.tolist(),open(sys.argv[2],"w"))
