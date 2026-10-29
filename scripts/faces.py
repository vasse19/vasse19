import cv2, json, sys
cap=cv2.VideoCapture(sys.argv[1]); fps=cap.get(cv2.CAP_PROP_FPS)
fc=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
out=[]; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    if i%5==0:
        g=cv2.equalizeHist(cv2.cvtColor(cv2.resize(f,(960,540)),cv2.COLOR_BGR2GRAY))
        fs=fc.detectMultiScale(g,1.1,6,minSize=(50,50))
        if len(fs):
            x,y,w,h=max(fs,key=lambda r:r[2]*r[3]); out.append([i/fps,float(x+w/2)*2,float(y+h/2)*2,float(w)*2])
    i+=1
json.dump(out,open(sys.argv[2],"w")); print(len(out),"detections of",i//5)
