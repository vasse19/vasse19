import cv2, json, sys
cap=cv2.VideoCapture(sys.argv[1]); fps=cap.get(cv2.CAP_PROP_FPS)
fr=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
out=[]; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    if i%3==0:
        g=cv2.equalizeHist(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY))
        c=fr.detectMultiScale(g,1.1,5,minSize=(40,40))
        if len(c):
            x,y,w,h=max(c,key=lambda r:r[2]*r[3]); out.append([i/fps,float(x+w/2),float(y+h/2),float(w)])
    i+=1
json.dump(out,open(sys.argv[2],"w")); print(len(out),"/",i//3, out[::40])
