import cv2, json, sys
cap=cv2.VideoCapture(sys.argv[1]); fps=cap.get(cv2.CAP_PROP_FPS)
fr=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
pr=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_profileface.xml")
out={"top":[],"bot":[]}; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    if i%5==0:
        for name,(y0,y1) in {"top":(0,960),"bot":(960,1920)}.items():
            g=cv2.equalizeHist(cv2.cvtColor(cv2.resize(f[y0:y1],(540,480)),cv2.COLOR_BGR2GRAY))
            c=list(fr.detectMultiScale(g,1.1,5,minSize=(60,60)))
            c+=list(pr.detectMultiScale(g,1.1,5,minSize=(60,60)))
            c+=[(540-x-w,y,w,h) for (x,y,w,h) in pr.detectMultiScale(cv2.flip(g,1),1.1,5,minSize=(60,60))]
            if c:
                x,y,w,h=max(c,key=lambda r:r[2]*r[3])
                out[name].append([i/fps,float(x+w/2)*2,float(y+h/2)*2+y0,float(w)*2])
    i+=1
json.dump(out,open(sys.argv[2],"w"))
for k,v in out.items():
    print(k,len(v),"/",i//5, [ (round(a,1),round(b),round(c)) for a,b,c,_ in v[::12]])
