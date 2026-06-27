#!/usr/bin/env python3
"""Logical architecture (Malek-style layered bands + clean block arrows) with a
tech logo in each component box for readability.
Usage: gen_arch.py <out.drawio> <out.png> [logodir]"""
import sys, html, math, os, base64
from PIL import Image, ImageDraw, ImageFont

LOGODIR = sys.argv[3] if len(sys.argv) > 3 else "logos"
PAL = {
 "green":  ("#d5e8d4", "#82b366"), "yellow": ("#fff2cc", "#d6b656"),
 "blue":   ("#dae8fc", "#6c8ebf"), "red":    ("#f8cecc", "#b85450"),
 "purple": ("#e1d5e7", "#9673a6"), "gray":   ("#f5f5f5", "#999999"),
}
TITLE = ("LOGICAL ARCHITECTURE", 450, 26)
# (title, colour, x, y, w, h)
bands = [
 ("Presentation Tier", "green",  70, 150, 760, 122),
 ("Application Tier",   "yellow", 70, 318, 760, 150),
 ("Data Access Layer",  "blue",   70, 512, 760,  95),
 ("Data Tier",          "red",    70, 652, 760, 118),
 ("Automation & AI",    "purple",858, 318, 198, 200),
]
# (label, colour, x, y, w, h, logo)
boxes = [
 ("Browser\n(end user)", "gray", 365, 52, 170, 44, ""),
 ("Nginx\n(static + reverse proxy)", "green", 110, 198, 320, 62, "nginx"),
 ("React 19 SPA\nVite · Tailwind · Zustand · TanStack Query", "green", 470, 198, 320, 62, "react"),
 ("NestJS 11 API\n(modular · Better-Auth)", "yellow", 110, 360, 230, 92, "nestjs"),
 ("Multer\n(file uploads)", "yellow", 360, 374, 200, 60, "multer"),
 ("Nodemailer\n(SMTP email)", "yellow", 580, 374, 210, 60, "nodemailer"),
 ("Prisma ORM\n(queries · migrations)", "blue", 285, 548, 310, 54, "prisma"),
 ("MariaDB 11\n(relational store)", "red", 150, 694, 290, 60, "mariadb"),
 ("File storage\n(uploads/)", "red", 480, 694, 250, 60, ""),
 ("n8n\nverify · chat · redesign", "purple", 872, 362, 170, 66, "n8n"),
 ("Groq / Gemini\n(LLM provider)", "purple", 872, 442, 170, 58, "gemini"),
]
arrows = [
 (450, 96, 450, 150), (450, 272, 450, 318), (450, 468, 450, 512),
 (450, 607, 450, 652), (830, 393, 858, 393), (957, 428, 957, 442),
]
dedges = [
 ("box0","band0",0.5,1,0.5,0), ("band0","band1",0.5,1,0.5,0),
 ("band1","band2",0.5,1,0.5,0), ("band2","band3",0.5,1,0.5,0),
 ("band1","band4",1,0.5,0,0.5), ("box9","box10",0.5,1,0.5,0),
]
CANVAS = (1090, 810); S = 2.2

def logopath(name): return os.path.join(LOGODIR, name + ".png")

# ---------------- draw.io ----------------
esc = lambda s: html.escape(s, quote=True).replace("\n", "&#10;")
cells = []
def vcell(cid, val, style, x, y, w, h):
    cells.append(f'<mxCell id="{cid}" value="{esc(val)}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
def imgcell(cid, name, x, y, w, h):
    data = base64.b64encode(open(logopath(name), "rb").read()).decode()
    st = f"shape=image;html=1;imageAspect=1;aspect=fixed;image=data:image/png,{data};"
    cells.append(f'<mxCell id="{cid}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
def edge(cid, src, tgt, ex, ey, nx, ny):
    st = (f"endArrow=block;html=1;rounded=0;strokeColor=#333333;strokeWidth=1.5;endFill=1;"
          f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={nx};entryY={ny};entryDx=0;entryDy=0;")
    cells.append(f'<mxCell id="{cid}" style="{st}" edge="1" parent="1" source="{src}" target="{tgt}"><mxGeometry relative="1" as="geometry"/></mxCell>')

vcell("title", TITLE[0], "text;html=1;align=center;fontSize=16;fontStyle=1;", TITLE[1]-160, TITLE[2]-12, 320, 24)
for i,(t,col,x,y,w,h) in enumerate(bands):
    f,s = PAL[col]
    vcell(f"band{i}", t, f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor={f};strokeColor={s};verticalAlign=top;align=center;fontSize=12;fontStyle=1;spacingTop=6;", x,y,w,h)
LSZ = 34
for i,(lab,col,x,y,w,h,logo) in enumerate(boxes):
    s = PAL[col][1]
    pad = (f"align=left;spacingLeft={LSZ+16};" if logo else "align=center;")
    vcell(f"box{i}", lab, f"rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor={s};verticalAlign=middle;fontSize=10;{pad}", x,y,w,h)
    if logo: imgcell(f"logo{i}", logo, x+8, y+(h-LSZ)/2, LSZ, LSZ)
for i,de in enumerate(dedges): edge(f"e{i}", *de)
xml = f'''<mxfile host="app.diagrams.net" type="device">
  <diagram id="arch" name="Logical Architecture">
    <mxGraphModel dx="1100" dy="850" grid="0" page="1" pageWidth="{CANVAS[0]}" pageHeight="{CANVAS[1]}" math="0" shadow="0">
      <root><mxCell id="0"/><mxCell id="1" parent="0"/>
        {chr(10).join(cells)}
      </root></mxGraphModel>
  </diagram>
</mxfile>'''
open(sys.argv[1], "w").write(xml)

# ---------------- PIL ----------------
W, H = int(CANVAS[0]*S), int(CANVAS[1]*S)
img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img)
def fnt(sz, b=False):
    try: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"%("-Bold" if b else ""), int(sz*S))
    except: return ImageFont.load_default()
FT, FBND, FN, FD = fnt(16, True), fnt(12, True), fnt(9.5, True), fnt(7.8)
_logocache = {}
def load_logo(name, px):
    key=(name,px)
    if key not in _logocache:
        im = Image.open(logopath(name)).convert("RGBA").resize((px,px), Image.LANCZOS)
        _logocache[key]=im
    return _logocache[key]
def sc(x,y): return (x*S, y*S)
def ctext(cx, cy, s, font, fill="black"):
    bb = d.textbbox((0,0), s, font=font); d.text((cx-(bb[2]-bb[0])/2, cy-(bb[3]-bb[1])/2-bb[1]), s, font=font, fill=fill)
def ltext(lx, cy, s, font, fill="black"):
    bb = d.textbbox((0,0), s, font=font); d.text((lx, cy-(bb[3]-bb[1])/2-bb[1]), s, font=font, fill=fill)
def wrap_fit(s, font, maxpx):
    words=s.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if not cur or d.textlength(t,font=font)<=maxpx: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines
def block_arrow(x1,y1,x2,y2,fill="#333333",w=2,size=11):
    p1=sc(x1,y1); p2=sc(x2,y2); d.line([*p1,*p2],fill=fill,width=w)
    ux,uy=p2[0]-p1[0],p2[1]-p1[1]; L=math.hypot(ux,uy) or 1; ux,uy=ux/L,uy/L; px,py=-uy,ux
    d.polygon([p2,(p2[0]-ux*size+px*size*0.55,p2[1]-uy*size+py*size*0.55),
               (p2[0]-ux*size-px*size*0.55,p2[1]-uy*size-py*size*0.55)], fill=fill)
def rrect(x,y,w,h,fill,outline,width=2,r=8):
    d.rounded_rectangle([*sc(x,y),*sc(x+w,y+h)], radius=int(r*S), fill=fill, outline=outline, width=width)

ctext(*sc(TITLE[1],TITLE[2]), TITLE[0], FT)
for t,col,x,y,w,h in bands:
    f,s = PAL[col]; rrect(x,y,w,h,f,s,2,10); ctext((x+w/2)*S,(y+16)*S,t,FBND,fill="#222222")
for a in arrows: block_arrow(*a)
for lab,col,x,y,w,h,logo in boxes:
    s = PAL[col][1]; rrect(x,y,w,h,"#ffffff",s,2,8)
    name,detail = (lab.split("\n",1)+[""])[:2]
    if logo:
        lpx=int(LSZ*S); lg=load_logo(logo,lpx)
        lx=int((x+8)*S); ly=int((y+(h-LSZ)/2)*S); img.paste(lg,(lx,ly),lg)
        tx=(x+8+LSZ+10); tw=(x+w-6)-tx
        dlines = wrap_fit(detail, FD, tw*S) if detail else []
        total = 1 + len(dlines)
        cy=(y+h/2); lh=12; y0=cy-(total-1)*lh/2
        ltext(tx*S, y0*S, name, FN)
        for i,dl in enumerate(dlines): ltext(tx*S,(y0+(i+1)*lh)*S, dl, FD, fill="#555")
    else:
        lines=[name]+([detail] if detail else []); lh=12; y0=(y+h/2)-(len(lines)-1)*lh/2
        for i,ln in enumerate(lines): ctext((x+w/2)*S,(y0+i*lh)*S, ln, FN if i==0 else FD, fill="black" if i==0 else "#555")
img.save(sys.argv[2]); print("wrote", sys.argv[1], "and", sys.argv[2], img.size)
