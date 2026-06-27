# Shared renderer for the PFE use-case diagrams (report colour scheme).
# Expects these globals from the caller: pos, GREEN, actors, owner, gens, deps,
# systems, sysdeps, BND, TITLE, CANVAS, S.  Writes argv[1]=.drawio, argv[2]=.png
import html, math, sys
from PIL import Image, ImageDraw, ImageFont

gens    = globals().get("gens", [])
systems = globals().get("systems", {})
sysdeps = globals().get("sysdeps", [])

def c(l): x,y,w,h=pos[l]; return (x+w/2, y+h/2)
def ract(n): x,y=actors[n]; return (x+20, y+30)
def sysc(n): x,y,w,h,_=systems[n]; return (x, y+h/2)

# ================= draw.io =================
esc = lambda s: html.escape(s, quote=True)
cells = []
def node(cid,v,st,x,y,w,h):
    cells.append(f'<mxCell id="{cid}" value="{esc(v)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
def edge(cid,s,t,st,v=""):
    cells.append(f'<mxCell id="{cid}" value="{esc(v)}" style="{st}" edge="1" parent="1" source="{s}" target="{t}"><mxGeometry relative="1" as="geometry"/></mxCell>')
ACTOR="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontSize=13;fontStyle=1;"
UC="ellipse;whiteSpace=wrap;html=1;fontSize=12;fillColor=#dae8fc;strokeColor=#6c8ebf;"
UCG="ellipse;whiteSpace=wrap;html=1;fontSize=12;fillColor=#d5e8d4;strokeColor=#82b366;"
SYS="rounded=0;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;align=center;verticalAlign=middle;fontSize=13;"
BNDS="rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;fontSize=15;fontStyle=1;fillColor=none;strokeColor=#666666;"
ASSOC="endArrow=none;html=1;strokeColor=#555555;"
SYSASSOC="endArrow=none;html=1;strokeColor=#d79b00;"
GEN="endArrow=block;endFill=0;html=1;strokeColor=#333333;"
DEP="endArrow=open;dashed=1;html=1;fontSize=11;fontStyle=2;strokeColor=#9933cc;"
node("bnd",TITLE[0],BNDS,BND[0],BND[1],BND[2]-BND[0],BND[3]-BND[1])
nid={}
for l,(x,y,w,h) in pos.items():
    cid="uc_"+str(abs(hash(l))%100000); nid[l]=cid
    node(cid,l,UCG if l in GREEN else UC,x,y,w,h)
for n,(x,y) in actors.items():
    nid[n]="a_"+n.lower().replace(" ","_"); node(nid[n],n,ACTOR,x,y,40,80)
for n,(x,y,w,h,sub) in systems.items():
    nid[n]="s_"+n.replace(" ","").lower()
    node(nid[n],f'<i>«system»</i><br><b>{n}</b><br><font style="font-size:10px">{sub}</font>',SYS,x,y,w,h)
for ch,pa in gens:
    edge("g_"+ch.lower(),nid[ch],nid[pa],GEN)
for a,ucs in owner.items():
    for l in ucs: edge(f"as_{nid[l]}",nid[a],nid[l],ASSOC)
for i,(s,t) in enumerate(sysdeps): edge(f"sd{i}",nid[s],nid[t],SYSASSOC)
for i,(s,t,k) in enumerate(deps): edge(f"d{i}",nid[s],nid[t],DEP,f"«{k}»")
xml=f'''<mxfile host="app.diagrams.net" type="device">
  <diagram id="uc" name="Use-Case">
    <mxGraphModel dx="1100" dy="850" grid="0" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{CANVAS[0]}" pageHeight="{CANVAS[1]}" math="0" shadow="0">
      <root><mxCell id="0"/><mxCell id="1" parent="0"/>
        {chr(10).join(cells)}
      </root></mxGraphModel>
  </diagram>
</mxfile>
'''
open(sys.argv[1],"w").write(xml)

# ================= PIL render =================
def fnt(sz,b=False):
    try: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"%("-Bold" if b else ""),int(sz*S))
    except: return ImageFont.load_default()
F,FB,FT,FI=fnt(12),fnt(12,True),fnt(15,True),fnt(10)
PUR,ORA="#9933cc","#d79b00"
W,H=int(CANVAS[0]*S),int(CANVAS[1]*S)
img=Image.new("RGB",(W,H),"white"); d=ImageDraw.Draw(img)
def sc(x,y): return (x*S,y*S)
def dline(p1,p2,dash=False,width=2,fill="black"):
    x1,y1=sc(*p1); x2,y2=sc(*p2)
    if not dash: d.line([x1,y1,x2,y2],fill=fill,width=width); return
    tot=math.hypot(x2-x1,y2-y1); n=max(1,int(tot/12))
    for i in range(n):
        if i%2: continue
        t1,t2=i/n,(i+1)/n
        d.line([x1+(x2-x1)*t1,y1+(y2-y1)*t1,x1+(x2-x1)*t2,y1+(y2-y1)*t2],fill=fill,width=width)
def arrowhead(p_from,p_to,fill,size=11):
    x1,y1=sc(*p_from); x2,y2=sc(*p_to)
    ux,uy=x2-x1,y2-y1; L=math.hypot(ux,uy) or 1; ux,uy=ux/L,uy/L
    px,py=-uy,ux
    d.line([x2,y2,x2-ux*size+px*size*0.5,y2-uy*size+py*size*0.5],fill=fill,width=2)
    d.line([x2,y2,x2-ux*size-px*size*0.5,y2-uy*size-py*size*0.5],fill=fill,width=2)
def ctext(cx,cy,s,font,fill="black"):
    bb=d.textbbox((0,0),s,font=font); d.text((cx-(bb[2]-bb[0])/2,cy-(bb[3]-bb[1])/2-bb[1]),s,font=font,fill=fill)
def wrap(s,n=22):
    ws,ls,cur=s.split(),[],""
    for w in ws:
        if len(cur)+len(w)+1<=n: cur=(cur+" "+w).strip()
        else: ls.append(cur); cur=w
    if cur: ls.append(cur)
    return ls[:2]
# boundary + title
d.rectangle([*sc(BND[0],BND[1]),*sc(BND[2],BND[3])],outline="black",width=2)
ctext(TITLE[1]*S,TITLE[2]*S,TITLE[0],FT)
# associations (actor -> use case)
for a,ucs in owner.items():
    for l in ucs: d.line([*sc(*ract(a)),*sc(*c(l))],fill="black",width=1)
# system links (orange)
for s,t in sysdeps: d.line([*sc(*sysc(s)),*sc(*c(t))],fill=ORA,width=1)
# generalizations (line + hollow triangle at parent)
for ch,pa in gens:
    a=ract(ch); b=ract(pa); d.line([*sc(*a),*sc(*b)],fill="black",width=2)
    ax,ay=sc(*a); bx,by=sc(*b); ux,uy=ax-bx,ay-by; L=math.hypot(ux,uy) or 1; ux,uy=ux/L,uy/L
    base=(bx+ux*16,by+uy*16); px,py=-uy,ux
    d.polygon([(bx,by),(base[0]+px*9,base[1]+py*9),(base[0]-px*9,base[1]-py*9)],outline="black",fill="white")
# dependencies (dashed purple + label + arrowhead), trimmed to the ellipse rims
def rim(label, toward):
    x,y,w,h=pos[label]; cx,cy=x+w/2.0,y+h/2.0; a,b=w/2.0,h/2.0
    dx,dy=toward[0]-cx,toward[1]-cy
    if dx==0 and dy==0: return (cx,cy)
    sca=1.0/math.sqrt((dx/a)**2+(dy/b)**2)
    return (cx+dx*sca, cy+dy*sca)
for src,tgt,kind in deps:
    sc0,tc0=c(src),c(tgt)
    p=rim(src,tc0); q=rim(tgt,sc0)     # start at source rim, end at target rim
    dline(p,q,dash=True,fill=PUR); arrowhead(p,q,PUR)
    dx,dy=tc0[0]-sc0[0],tc0[1]-sc0[1]; f=0.40
    lx=sc0[0]+f*dx; ly=sc0[1]+f*dy-9
    if abs(dx)<50: lx+=36          # near-vertical edge: push label to the side
    ctext(lx*S,ly*S,f"«{kind}»",FI,fill=PUR)
# ellipses
for l,(x,y,w,h) in pos.items():
    fill="#d5e8d4" if l in GREEN else "#dae8fc"; out="#5a8a5a" if l in GREEN else "#3b5b8c"
    d.ellipse([*sc(x,y),*sc(x+w,y+h)],fill=fill,outline=out,width=2)
    ls=wrap(l); y0=c(l)[1]-(len(ls)-1)*8
    for k,ln in enumerate(ls): ctext(c(l)[0]*S,(y0+k*15)*S,ln,F)
# actors (stick figures)
for n,(x,y) in actors.items():
    cx=x+20
    d.ellipse([*sc(cx-9,y+3),*sc(cx+9,y+21)],outline="black",width=2,fill="white")
    d.line([*sc(cx,y+21),*sc(cx,y+48)],fill="black",width=2)
    d.line([*sc(cx-16,y+30),*sc(cx+16,y+30)],fill="black",width=2)
    d.line([*sc(cx,y+48),*sc(cx-14,y+70)],fill="black",width=2)
    d.line([*sc(cx,y+48),*sc(cx+14,y+70)],fill="black",width=2)
    ctext(cx*S,(y+82)*S,n,FB)
# system boxes (orange «system»)
for n,(x,y,w,h,sub) in systems.items():
    d.rectangle([*sc(x,y),*sc(x+w,y+h)],fill="#ffe6cc",outline=ORA,width=2)
    cx=x+w/2
    ctext(cx*S,(y+16)*S,"«system»",FI,fill="#555")
    ctext(cx*S,(y+h/2)*S,n,FB)
    ctext(cx*S,(y+h-16)*S,sub,FI,fill="#777")
img.save(sys.argv[2])
print("wrote", sys.argv[1], "and", sys.argv[2], img.size)
