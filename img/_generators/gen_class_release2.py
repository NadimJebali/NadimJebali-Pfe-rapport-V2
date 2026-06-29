#!/usr/bin/env python3
"""Emit an editable draw.io for the Release 2 domain model (subset of the full
class diagram), in the same plain black-and-white UML style as gen_class.py.
Render the PNG afterwards with render_class.py.
Usage: gen_class_release2.py <out.drawio>
"""
import sys, html, math
from PIL import Image, ImageDraw, ImageFont

ROW, TITLE_H, ESTEREO_H, PAD, MINW = 19, 30, 18, 7, 150

# (id, name, x, y, attrs[], is_enum)
classes = [
 ("user", "User", 320, 40,
   ["- id: String", "- role: UserRole", "- isPremium: bool",
    "- premiumExpiresAt: DateTime", "- stripeCustomerId: String",
    "- stripeSubscriptionId: String", "- cancelAtPeriodEnd: bool"], False),
 ("order", "Order", 640, 40,
   ["- id: int", "- status: OrderStatus", "- paymentStatus: PaymentStatus",
    "- total: float", "- stripePaymentIntentId: String", "- createdAt: DateTime"], False),
 ("ostat", "OrderStatus", 930, 40,
   ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"], True),
 ("paystat", "PaymentStatus", 930, 250, ["UNPAID", "PAID"], True),
 ("oitem", "OrderItem", 670, 280,
   ["- id: int", "- quantity: int", "- unitPrice: float"], False),

 ("store", "Store", 320, 270,
   ["- id: int", "- currentStatus: StoreStatus", "- aiReviewed: bool",
    "- adminReviewed: bool"], False),
 ("slog", "StoreStatusLog", 40, 300,
   ["- id: int", "- status: StoreStatus", "- reason: String"], False),
 ("fstore", "FeaturedStore", 40, 470, ["- id: int", "- position: int"], False),

 ("prod", "Product", 320, 470,
   ["- id: int", "- displayPrice: float", "- stock: int",
    "- verificationStatus: VerificationStatus", "- aiReviewed: bool",
    "- adminReviewed: bool", "- saleEnabled: bool",
    "- saleDiscountPercent: int", "- saleEndsAt: DateTime"], False),
 ("vstat", "VerificationStatus", 320, 730,
   ["PENDING", "APPROVED", "REJECTED"], True),
 ("fprod", "FeaturedProduct", 40, 620, ["- id: int", "- position: int"], False),
 ("sub", "Subcategory", 40, 760, ["- id: int", "- name: String"], False),
]
C = {c[0]: c for c in classes}

# (src, ss, sf, tgt, ts, tf, kind, smult, tmult, label)
edges = [
 ("user", "R", 0.5, "order", "L", 0.5, "assoc", "1", "0..*", "places"),
 ("user", "B", 0.5, "store", "T", 0.5, "assoc", "1", "0..*", "owns"),
 ("store", "B", 0.5, "prod", "T", 0.5, "comp", "1", "0..*", "sells"),
 ("order", "B", 0.5, "oitem", "T", 0.5, "comp", "1", "1..*", "contains"),
 ("prod", "R", 0.25, "oitem", "L", 0.7, "assoc", "1", "0..*", "ordered in"),

 ("store", "L", 0.75, "slog", "R", 0.4, "comp", "1", "0..*", "logs"),
 ("store", "L", 0.35, "fstore", "R", 0.4, "assoc", "1", "0..1", "featured"),
 ("prod", "L", 0.8, "fprod", "R", 0.4, "assoc", "1", "0..1", "featured"),
 ("sub", "R", 0.5, "prod", "L", 0.4, "assoc", "1", "0..*", "classifies"),

 ("order", "R", 0.35, "ostat", "L", 0.5, "dep", "", "", ""),
 ("order", "R", 0.7, "paystat", "L", 0.5, "dep", "", "", ""),
 ("prod", "B", 0.5, "vstat", "T", 0.5, "dep", "", "", ""),
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
  <diagram id="classr2" name="Release 2 Class Diagram">
    <mxGraphModel dx="1200" dy="900" grid="0" page="1" pageWidth="{maxx}" pageHeight="{maxy}" math="0" shadow="0">
      <root><mxCell id="0"/><mxCell id="1" parent="0"/>
        {chr(10).join(cells)}
      </root></mxGraphModel>
  </diagram>
</mxfile>'''
open(sys.argv[1], "w").write(xml)
print("wrote", sys.argv[1], f"({len(classes)} classes, {len(edges)} edges)")
