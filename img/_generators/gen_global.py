#!/usr/bin/env python3
"""Render a hand-made .drawio use-case diagram to a clean white-bg PNG in the
report colour scheme. Parses geometry by cell id (labels are not unique).
Usage: gen_global.py <in.drawio> <out.png>"""
import sys, re, math, html
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

IN, OUT = sys.argv[1], sys.argv[2]
root = ET.parse(IN).getroot()
cells = root.iter("mxCell")

def clean(v):
    if v is None: return ""
    v = re.sub(r"<br\s*/?>", " ", v, flags=re.I)
    v = re.sub(r"<[^>]+>", "", v)
    v = v.replace("&nbsp;", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", v).strip()

verts, edges = {}, []
for cell in root.iter("mxCell"):
    st = cell.get("style", "") or ""
    g = cell.find("mxGeometry")
    if cell.get("vertex") == "1" and g is not None:
        x,y,w,h = (float(g.get(k,0)) for k in ("x","y","width","height"))
        if "umlActor" in st: kind="actor"
        elif "fillColor=#ffe6cc" in st: kind="system"
        elif "fillColor=none" in st and "#666666" in st: kind="boundary"
        elif st.startswith("ellipse"): kind="green" if "#d5e8d4" in st else "uc"
        else: kind="uc"
        verts[cell.get("id")] = dict(kind=kind, x=x, y=y, w=w, h=h,
                                     raw=cell.get("value",""), st=st)
    elif cell.get("edge") == "1":
        sp = tp = None
        if g is not None:
            for p in g.findall("mxPoint"):
                if p.get("as")=="sourcePoint": sp=(float(p.get("x",0)),float(p.get("y",0)))
                if p.get("as")=="targetPoint": tp=(float(p.get("x",0)),float(p.get("y",0)))
        edges.append(dict(s=cell.get("source"), t=cell.get("target"), st=st,
                          val=clean(cell.get("value","")), sp=sp, tp=tp))

boundary = next((v for v in verts.values() if v["kind"]=="boundary"), None)

# ---- canvas ----
maxX = max(v["x"]+v["w"] for v in verts.values())
maxY = max(v["y"]+v["h"] for v in verts.values())
CW, CH = maxX+50, maxY+55
S = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
W, Hh = int(CW*S), int(CH*S)
img = Image.new("RGB",(W,Hh),"white"); d = ImageDraw.Draw(img)
def sc(x,y): return (x*S, y*S)
def fnt(sz,b=False):
    try: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"%("-Bold" if b else ""),int(sz*S))
    except: return ImageFont.load_default()
F,FB,FT,FI = fnt(11),fnt(11,True),fnt(16,True),fnt(9)
PUR,ORA = "#9933cc","#d79b00"

def center(v): return (v["x"]+v["w"]/2, v["y"]+v["h"]/2)
def ctext(cx,cy,s,font,fill="black"):
    bb=d.textbbox((0,0),s,font=font); d.text((cx-(bb[2]-bb[0])/2,cy-(bb[3]-bb[1])/2-bb[1]),s,font=font,fill=fill)
def wrap_fit(s,font,maxpx):
    words=s.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if not cur or d.textlength(t,font=font)<=maxpx: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines
def rim(v,toward):
    cx,cy=center(v); a,b=v["w"]/2.0,v["h"]/2.0
    dx,dy=toward[0]-cx,toward[1]-cy
    if dx==0 and dy==0: return (cx,cy)
    if v["kind"] in ("uc","green"):
        k=1.0/math.sqrt((dx/a)**2+(dy/b)**2)
    else:  # rectangle (system box)
        k=min(a/abs(dx) if dx else 1e9, b/abs(dy) if dy else 1e9)
    return (cx+dx*k, cy+dy*k)
def endpoint(eid, pt, toward, trim):
    if eid and eid in verts:
        v=verts[eid]
        return rim(v,toward) if trim else center(v)
    return pt
def node_center(eid, pt):
    return center(verts[eid]) if (eid and eid in verts) else pt
def dline(p1,p2,fill,width=2,dash=False):
    x1,y1=sc(*p1); x2,y2=sc(*p2)
    if not dash: d.line([x1,y1,x2,y2],fill=fill,width=width); return
    tot=math.hypot(x2-x1,y2-y1); n=max(1,int(tot/13))
    for i in range(n):
        if i%2: continue
        a,b=i/n,(i+1)/n
        d.line([x1+(x2-x1)*a,y1+(y2-y1)*a,x1+(x2-x1)*b,y1+(y2-y1)*b],fill=fill,width=width)
def arrowhead(p_from,p_to,fill,size=10):
    x1,y1=sc(*p_from); x2,y2=sc(*p_to)
    ux,uy=x2-x1,y2-y1; L=math.hypot(ux,uy) or 1; ux,uy=ux/L,uy/L; px,py=-uy,ux
    d.line([x2,y2,x2-ux*size+px*size*0.5,y2-uy*size+py*size*0.5],fill=fill,width=2)
    d.line([x2,y2,x2-ux*size-px*size*0.5,y2-uy*size-py*size*0.5],fill=fill,width=2)

# ---- boundary + title ----
if boundary:
    d.rectangle([*sc(boundary["x"],boundary["y"]),*sc(boundary["x"]+boundary["w"],boundary["y"]+boundary["h"])],outline="black",width=2)
    ctext((boundary["x"]+boundary["w"]/2)*S,(boundary["y"]+18)*S,clean(boundary["raw"]),FT)

def kindof(e):
    st=e["st"]
    if "9933cc" in st: return "dep"
    if "d79b00" in st: return "sys"
    if "endArrow=block" in st: return "gen"
    return "assoc"

# ---- plain lines first (assoc / system / generalization) ----
for e in edges:
    k=kindof(e)
    if k=="dep": continue
    p=node_center(e["s"],e["sp"]); q=node_center(e["t"],e["tp"])
    if p is None or q is None: continue
    if k=="sys": dline(p,q,ORA,2)
    elif k=="gen":
        dline(p,q,"#333333",2)
        x1,y1=sc(*p); x2,y2=sc(*q); ux,uy=x1-x2,y1-y2; L=math.hypot(ux,uy) or 1; ux,uy=ux/L,uy/L
        base=(x2+ux*16,y2+uy*16); px,py=-uy,ux
        d.polygon([(x2,y2),(base[0]+px*9,base[1]+py*9),(base[0]-px*9,base[1]-py*9)],outline="#333333",fill="white")
    else: dline(p,q,"#555555",1)

# ---- dependencies (dashed purple, trimmed, arrowhead) ----
for e in edges:
    if kindof(e)!="dep": continue
    pc=node_center(e["s"],e["sp"]); qc=node_center(e["t"],e["tp"])
    if pc is None or qc is None: continue
    p=endpoint(e["s"],e["sp"],qc,True); q=endpoint(e["t"],e["tp"],pc,True)
    dline(p,q,PUR,2,dash=True)
    if "startArrow=open" in e["st"] and "endArrow=none" in e["st"]:
        arrowhead(q,p,PUR)
    else:
        arrowhead(p,q,PUR)
    if e["val"]:
        mx,my=(p[0]+q[0])/2,(p[1]+q[1])/2
        ctext(mx*S,(my-8)*S,e["val"],FI,fill=PUR)

# ---- ellipses ----
for v in verts.values():
    if v["kind"] not in ("uc","green"): continue
    fill="#d5e8d4" if v["kind"]=="green" else "#dae8fc"
    out="#5a8a5a" if v["kind"]=="green" else "#3b5b8c"
    d.ellipse([*sc(v["x"],v["y"]),*sc(v["x"]+v["w"],v["y"]+v["h"])],fill=fill,outline=out,width=2)
    lab=clean(v["raw"]); cx,cy=center(v)
    lines=wrap_fit(lab,F,(v["w"]-14)*S)[:3]
    lh=13; y0=cy-(len(lines)-1)*lh/2
    for i,ln in enumerate(lines): ctext(cx*S,(y0+i*lh)*S,ln,F)

# ---- actors ----
for v in verts.values():
    if v["kind"]!="actor": continue
    x,y=v["x"],v["y"]; cx=x+v["w"]/2
    d.ellipse([*sc(cx-9,y+3),*sc(cx+9,y+21)],outline="black",width=2,fill="white")
    d.line([*sc(cx,y+21),*sc(cx,y+48)],fill="black",width=2)
    d.line([*sc(cx-16,y+30),*sc(cx+16,y+30)],fill="black",width=2)
    d.line([*sc(cx,y+48),*sc(cx-14,y+70)],fill="black",width=2)
    d.line([*sc(cx,y+48),*sc(cx+14,y+70)],fill="black",width=2)
    ctext(cx*S,(y+82)*S,clean(v["raw"]),FB)

# ---- system boxes ----
for v in verts.values():
    if v["kind"]!="system": continue
    d.rectangle([*sc(v["x"],v["y"]),*sc(v["x"]+v["w"],v["y"]+v["h"])],fill="#ffe6cc",outline=ORA,width=2)
    raw=v["raw"]
    name=clean(re.search(r"<b>(.*?)</b>",raw).group(1)) if re.search(r"<b>(.*?)</b>",raw) else ""
    subm=re.findall(r"<font[^>]*>(.*?)</font>",raw); sub=clean(subm[-1]) if subm else ""
    cx=v["x"]+v["w"]/2
    ctext(cx*S,(v["y"]+16)*S,"«system»",FI,fill="#555")
    ctext(cx*S,(v["y"]+v["h"]/2+2)*S,name,FB)
    ctext(cx*S,(v["y"]+v["h"]-15)*S,sub,FI,fill="#777")

img.save(OUT)
print("wrote",OUT,img.size)
