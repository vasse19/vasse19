import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
src,out=sys.argv[1],sys.argv[2]
im=Image.open(src).convert("RGB")
# frame the face on the right third
fx,fy,cw=1220,690,960
ch=cw*9/16; x0=fx-cw*0.70; y0=fy-ch*0.48
im=im.crop((int(x0),int(y0),int(x0+cw),int(y0+ch))).resize((1280,720),Image.LANCZOS)
im=ImageEnhance.Contrast(im).enhance(1.18); im=ImageEnhance.Color(im).enhance(1.15)
im=ImageEnhance.Brightness(im).enhance(1.08)
im=im.filter(ImageFilter.UnsharpMask(radius=2,percent=110,threshold=2))
# darken the left side for the text
grad=Image.new("L",(1280,720))
gd=ImageDraw.Draw(grad)
for x in range(1280):
    a=int(235*max(0,min(1,(760-x)/520))**1.3); gd.line([(x,0),(x,720)],fill=a)
im=Image.composite(Image.new("RGB",im.size,(8,8,12)),im,grad)
# warm glow behind the face
glow=Image.new("RGB",im.size,(0,0,0)); ImageDraw.Draw(glow).ellipse((700,40,1260,720),fill=(255,170,60))
glow=glow.filter(ImageFilter.GaussianBlur(120))
im=Image.fromarray(np.clip(np.asarray(im,dtype=float)+np.asarray(glow,dtype=float)*0.18,0,255).astype("uint8"))
d=ImageDraw.Draw(im)
F="/usr/share/fonts/opentype/inter/"
def text(xy,s,size,fill,stroke=10,font="Inter-Black.otf",shadow=True):
    f=ImageFont.truetype(F+font,size)
    if shadow: d.text((xy[0]+8,xy[1]+10),s,font=f,fill=(0,0,0),stroke_width=stroke,stroke_fill=(0,0,0))
    d.text(xy,s,font=f,fill=fill,stroke_width=stroke,stroke_fill=(0,0,0))
    return d.textbbox(xy,s,font=f,stroke_width=stroke)
text((48,70),"LE SON",128,(255,255,255))
text((48,215),"À FOND",128,(255,214,0))
text((48,360),"AU VOLANT",104,(255,255,255))
# red tag
f=ImageFont.truetype(F+"Inter-Black.otf",58); tag="ÇA TE BOOST !"
b=d.textbbox((0,0),tag,font=f); w,h=b[2]-b[0],b[3]-b[1]
tg=Image.new("RGBA",(w+60,h+44),(0,0,0,0)); td=ImageDraw.Draw(tg)
td.rounded_rectangle((0,0,w+60,h+44),18,fill=(230,30,40))
td.text((30-b[0],22-b[1]),tag,font=f,fill=(255,255,255))
tg=tg.rotate(4,expand=True,resample=Image.BICUBIC)
im.paste(tg,(52,530),tg)
im.save(out,quality=95)
