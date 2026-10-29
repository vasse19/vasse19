import json, sys
words=[dict(x) for x in json.load(open(sys.argv[1])) if x["s"]>=54.5]
# merge standalone punctuation into previous word
m=[]
for x in words:
    if m and all(c in "!?.,;:" for c in x["w"]): m[-1]["w"]+=x["w"]; m[-1]["e"]=x["e"]
    else: m.append(x)
words=m
def at(t): return min(range(len(words)),key=lambda i:abs(words[i]["s"]-t))
# manual fixes (ASR errors), by approximate start time
def sub(t0,n,new):
    i=at(t0); s=words[i]["s"]; e=words[i+n-1]["e"]; k=len(new)
    words[i:i+n]=[{"w":w,"s":s+(e-s)*j/k,"e":s+(e-s)*(j+1)/k} for j,w in enumerate(new)]
sub(87.9,7,["Dites-moi","en","commentaire !"])
sub(83.2,3,["On","met","du","son"])
sub(68.9,3,["mets","du","son"])
sub(65.1,1,["Tiens !"])
for x in words: x["e"]=max(x["e"],x["s"]+0.15)
# group into chunks of <=3 words, break on punctuation / pauses
groups=[];cur=[]
for i,x in enumerate(words):
    cur.append(x)
    if x["w"].lower()=="en" and i+1<len(words) and words[i+1]["w"].lower().startswith("fait") and len(cur)>1:
        cur.pop(); groups.append(cur); cur=[x]
    nxt=words[i+1] if i+1<len(words) else None
    starter=nxt and nxt["w"].lower() in {"je","et","on","mais","ouais","bon","non","tu","genre","quand"} and (len(cur)>=2 or nxt["w"].lower() in {"et","genre"})
    if len(cur)==4 or x["w"][-1] in "!?.," or not nxt or nxt["s"]-x["e"]>0.45 or starter:
        groups.append(cur);cur=[]
def ts(t):
    t=max(t,0); h=int(t//3600); mi=int(t%3600//60); s=t%60
    return f"{h}:{mi:02d}:{s:05.2f}"
EMPH={"tiens !","bam!","carré!","boost","vérité","fort"}
hdr="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter ExtraBold,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,4,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
X,Y=540,int(sys.argv[3]) if len(sys.argv)>3 else 1480
ev=[]
for gi,g in enumerate(groups):
    gend=g[-1]["e"]
    if gi+1<len(groups): gend=min(max(gend,groups[gi+1][0]["s"]-0.05) if groups[gi+1][0]["s"]-gend<0.4 else gend+0.2, groups[gi+1][0]["s"])
    for wi,w in enumerate(g):
        s=w["s"]; e=g[wi+1]["s"] if wi+1<len(g) else gend
        parts=[]
        for j,o in enumerate(g):
            t=o["w"].upper()
            if j==wi:
                col="&H0000E5FF&" if o["w"].lower() not in EMPH else "&H003C3CFF&"
                parts.append(r"{\c"+col+r"\fscx118\fscy118\t(0,90,\fscx108\fscy108)}"+t+r"{\c&HFFFFFF&\fscx100\fscy100}")
            elif j<wi: parts.append(t)
            else: parts.append(r"{\alpha&H70&}"+t+r"{\alpha&H00&}")
        intro=r"\fscx70\fscy70\t(0,110,\fscx100\fscy100)" if wi==0 else ""
        L=sum(len(o["w"]) for o in g)+len(g)-1
        fs=min(92,int(960/(L*0.55*1.12)))
        intro=(rf"\fs{fs}" if fs<92 else "")+intro
        rot=r"\frz-3" if any(o["w"].lower() in EMPH for o in g) else ""
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{{\\an5\\pos({X},{Y}){intro}{rot}}}"+" ".join(parts))
open(sys.argv[2],"w").write(hdr+"\n".join(ev)+"\n")
json.dump(words,open(sys.argv[2]+".words.json","w"),ensure_ascii=False)
print(len(groups),"groups");print(" | ".join(" ".join(x["w"] for x in g) for g in groups))
