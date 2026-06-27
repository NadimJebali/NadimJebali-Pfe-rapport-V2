#!/usr/bin/env python3
"""Emit an editable draw.io for the Release 1 domain model (foundations & core
marketplace: identity, seller onboarding, stores, catalogue), in the same plain
black-and-white UML style as gen_class.py.  Render with render_class.py.
Usage: gen_class_release1.py <out.drawio>
"""
import sys, html, math
from PIL import Image, ImageDraw, ImageFont

ROW, TITLE_H, ESTEREO_H, PAD, MINW = 19, 30, 18, 7, 150

# (id, name, x, y, attrs[], is_enum)
classes = [
 ("sapp", "SellerApplication", 40, 60,
   ["- id: int", "- fullName: String", "- businessDescription: String",
    "- idDocumentUrl: String", "- status: SellerApplicationStatus",
    "- adminNote: String"], False),
 ("sas", "SellerApplicationStatus", 40, 300,
   ["PENDING", "APPROVED", "REJECTED", "MORE_INFO_REQUESTED"], True),

 ("user", "User", 380, 40,
   ["- id: String", "- name: String", "- email: String",
    "- emailVerified: bool", "- role: UserRole"], False),
 ("role", "UserRole", 700, 40, ["CUSTOMER", "SELLER", "ADMIN"], True),

 ("store", "Store", 380, 250,
   ["- id: int", "- name: String", "- slug: String", "- description: String",
    "- template: StoreTemplate", "- currentStatus: StoreStatus",
    "- saleEnabled: bool", "- saleDiscountPercent: int"], False),
 ("sstat", "StoreStatus", 720, 250,
   ["PENDING", "ACTIVE", "SUSPENDED", "REJECTED"], True),

 ("cat", "Category", 40, 500, ["- id: int", "- name: String"], False),
 ("sub", "Subcategory", 40, 650, ["- id: int", "- name: String"], False),

 ("prod", "Product", 380, 540,
   ["- id: int", "- name: String", "- price: float",
    "- displayPrice: float", "- stock: int"], False),
 ("pimg", "ProductImage", 720, 500,
   ["- id: int", "- url: String", "- alt: String"], False),
 ("ptag", "ProductTag", 720, 650, ["- id: int", "- name: String"], False),
]
C = {c[0]: c for c in classes}

# (src, ss, sf, tgt, ts, tf, kind, smult, tmult, label)
edges = [
 ("user", "L", 0.5, "sapp", "R", 0.4, "assoc", "1", "0..1", "submits"),
 ("user", "B", 0.5, "store", "T", 0.5, "assoc", "1", "0..*", "owns"),
 ("store", "B", 0.5, "prod", "T", 0.5, "comp", "1", "0..*", "sells"),

 ("cat", "B", 0.5, "sub", "T", 0.5, "assoc", "1", "0..*", "groups"),
 ("sub", "R", 0.5, "prod", "L", 0.4, "assoc", "1", "0..*", "classifies"),

 ("prod", "R", 0.35, "pimg", "L", 0.5, "comp", "1", "1..*", "has"),
 ("prod", "R", 0.7, "ptag", "L", 0.5, "assoc", "*", "*", "tagged"),

 ("user", "R", 0.3, "role", "L", 0.5, "dep", "", "", ""),
 ("store", "R", 0.3, "sstat", "L", 0.5, "dep", "", "", ""),
 ("sapp", "B", 0.5, "sas", "T", 0.5, "dep", "", "", ""),
]

def fnt(sz, b=False):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), sz)
    except Exception:
        return ImageFont.load_default()
F_NAME, F_STEREO, F_BODY = fnt(12, True), fnt(9), fnt(10)
_p = ImageDraw.Draw(Image.new("RGB", (4, 4)))
def tw(s, f): return _p.textlength(s, font=f)

def box_w(c):
    _, name, x, y, attrs, is_enum = c
    w = tw(name, F_NAME) + 24
    for s in attrs:
        w = max(w, tw(s, F_BODY) + 18)
    if is_enum:
        w = max(w, tw("<<enumeration>>", F_STEREO) + 18)
    return max(MINW, math.ceil(w))
def box_h(c):
    _, name, x, y, attrs, is_enum = c
    h = TITLE_H + (ESTEREO_H if is_enum else 0)
    return h + PAD + max(1, len(attrs)) * ROW + PAD
DIM = {c[0]: (c[2], c[3], box_w(c), box_h(c)) for c in classes}

esc = lambda s: html.escape(s, quote=True)
cells = []
def uml_class(c):
    cid, name, x, y, attrs, is_enum = c
    w, h = box_w(c), box_h(c)
    head = ("<<enumeration>>\n" if is_enum else "") + name
    style = ("swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;"
             "horizontal=1;startSize=%d;horizontalStack=0;resizeParent=1;resizeParentMax=0;"
             "html=1;collapsible=0;swimlaneFillColor=#ffffff;fillColor=#ffffff;strokeColor=#000000;"
             "fontColor=#000000;fontSize=12;" % (TITLE_H + (ESTEREO_H if is_enum else 0)))
    cells.append(f'<mxCell id="{cid}" value="{esc(head)}" style="{style}" vertex="1" parent="1">'
                 f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    yo = TITLE_H + (ESTEREO_H if is_enum else 0)
    rowst = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=6;"
             "spacingRight=6;overflow=hidden;rotatable=0;points=[];html=1;fontSize=11;fontColor=#000000;")
    for i, a in enumerate(attrs):
        cells.append(f'<mxCell id="{cid}_a{i}" value="{esc(a)}" style="{rowst}" vertex="1" parent="{cid}">'
                     f'<mxGeometry y="{yo}" width="{w}" height="{ROW}" as="geometry"/></mxCell>')
        yo += ROW

for c in classes:
    uml_class(c)

def sidexy(side, frac):
    return {"L": (0, frac), "R": (1, frac), "T": (frac, 0), "B": (frac, 1)}[side]
for i, (s, ss, sf, t, ts, tf, kind, sm, tm, lbl) in enumerate(edges):
    ex, ey = sidexy(ss, sf); nx, ny = sidexy(ts, tf)
    base = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;"
            f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={nx};entryY={ny};entryDx=0;entryDy=0;")
    if kind == "comp":
        st = base + "startArrow=diamondThin;startFill=1;startSize=14;endArrow=none;"
    elif kind == "dep":
        st = base + "dashed=1;endArrow=open;endFill=0;startArrow=none;"
    else:
        st = base + "endArrow=none;startArrow=none;"
    cells.append(f'<mxCell id="e{i}" value="{esc(lbl)}" style="{st}" edge="1" parent="1" source="{s}" target="{t}">'
                 f'<mxGeometry relative="1" as="geometry"/></mxCell>')
    if sm:
        cells.append(f'<mxCell id="e{i}s" value="{esc(sm)}" style="resizable=0;html=1;fontSize=10;" '
                     f'vertex="1" connectable="0" parent="e{i}"><mxGeometry x="-0.8" relative="1" as="geometry">'
                     f'<mxPoint as="offset"/></mxGeometry></mxCell>')
    if tm:
        cells.append(f'<mxCell id="e{i}t" value="{esc(tm)}" style="resizable=0;html=1;fontSize=10;" '
                     f'vertex="1" connectable="0" parent="e{i}"><mxGeometry x="0.8" relative="1" as="geometry">'
                     f'<mxPoint as="offset"/></mxGeometry></mxCell>')

maxx = max(DIM[c][0] + DIM[c][2] for c in DIM) + 40
maxy = max(DIM[c][1] + DIM[c][3] for c in DIM) + 40
xml = f'''<mxfile host="app.diagrams.net" type="device">
  <diagram id="classr1" name="Release 1 Class Diagram">
    <mxGraphModel dx="1200" dy="900" grid="0" page="1" pageWidth="{maxx}" pageHeight="{maxy}" math="0" shadow="0">
      <root><mxCell id="0"/><mxCell id="1" parent="0"/>
        {chr(10).join(cells)}
      </root></mxGraphModel>
  </diagram>
</mxfile>'''
open(sys.argv[1], "w").write(xml)
print("wrote", sys.argv[1], f"({len(classes)} classes, {len(edges)} edges)")
