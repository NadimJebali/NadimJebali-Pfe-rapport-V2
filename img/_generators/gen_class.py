#!/usr/bin/env python3
"""Domain class diagram in a plain black-and-white UML style (Malek fig 2.2):
white 3-compartment class boxes (name / attributes / operations), thin black
borders, standard UML relations -- association with multiplicities, composition
(filled diamond at the whole), many-to-many, and <<enumeration>> boxes linked by
dashed dependencies.  Emits an editable .drawio + a rendered PNG.
Usage: gen_class.py <out.drawio> <out.png> [scale]
"""
import sys, html, math
from PIL import Image, ImageDraw, ImageFont

S = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
ROW = 19          # attribute / operation line height (logical px)
TITLE_H = 30      # class name compartment
ESTEREO_H = 18    # <<enumeration>> stereotype line
PAD = 7           # vertical padding inside a compartment
MINW = 150

# ---------------------------------------------------------------- model
# Each class: (id, name, x, y, attrs[], ops[], is_enum)
classes = [
 ("sas", "SellerApplicationStatus", 40, 40,
   ["PENDING", "APPROVED", "REJECTED", "MORE_INFO_REQUESTED"], [], True),
 ("sapp", "SellerApplication", 40, 250,
   ["- id: int", "- status: SellerApplicationStatus", "- fullName: String",
    "- businessDescription: String", "- idDocumentUrl: String"],
   ["+ submit(): void", "+ approve(): void", "+ reject(note): void"], False),

 ("user", "User", 400, 40,
   ["- id: String", "- name: String", "- email: String", "- emailVerified: bool",
    "- role: UserRole", "- isPremium: bool", "- premiumExpiresAt: DateTime",
    "- stripeCustomerId: String"],
   ["+ register(): void", "+ applyAsSeller(): void", "+ upgradeToPremium(): void"], False),
 ("role", "UserRole", 730, 40, ["CUSTOMER", "SELLER", "ADMIN"], [], True),

 ("cat", "Category", 40, 560, ["- id: int", "- name: String"], [], False),
 ("sub", "Subcategory", 40, 740, ["- id: int", "- name: String"], [], False),
 ("slog", "StoreStatusLog", 60, 940,
   ["- id: int", "- status: StoreStatus", "- reason: StoreStatusReason",
    "- title: String", "- isResolved: bool"],
   ["+ resolve(): void"], False),

 ("store", "Store", 400, 470,
   ["- id: int", "- name: String", "- slug: String", "- description: String",
    "- currentStatus: StoreStatus", "- template: StoreTemplate",
    "- customization: Json", "- saleEnabled: bool", "- saleDiscountPercent: int"],
   ["+ create(): void", "+ customize(): void", "+ toggleSale(): void"], False),
 ("sstat", "StoreStatus", 760, 470,
   ["PENDING", "ACTIVE", "SUSPENDED", "REJECTED"], [], True),

 ("prod", "Product", 400, 1130,
   ["- id: int", "- name: String", "- description: String", "- price: float",
    "- displayPrice: float", "- stock: int", "- status: ProductStatus",
    "- verificationStatus: VerificationStatus"],
   ["+ create(): void", "+ updateStock(): void", "+ submitForReview(): void"], False),
 ("pstat", "ProductStatus", 470, 1490, ["AVAILABLE", "UNAVAILABLE"], [], True),
 ("vstat", "VerificationStatus", 720, 1490,
   ["PENDING", "APPROVED", "REJECTED"], [], True),
 ("ptag", "ProductTag", 40, 1190, ["- id: int", "- name: String"], [], False),
 ("pimg", "ProductImage", 40, 1380,
   ["- id: int", "- url: String", "- alt: String"], [], False),

 ("order", "Order", 1050, 470,
   ["- id: int", "- streetAddress: String", "- city: String", "- country: String",
    "- status: OrderStatus", "- paymentStatus: PaymentStatus",
    "- totalAmount: float", "- paidAt: DateTime"],
   ["+ place(): void", "+ confirmPayment(): void"], False),
 ("ostat", "OrderStatus", 1380, 470,
   ["PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED",
    "CANCELLED", "REFUNDED"], [], True),
 ("oitem", "OrderItems", 1050, 1130,
   ["- id: int", "- quantity: int", "- unitPrice: float", "- subtotal: float"],
   [], False),
]
C = {c[0]: c for c in classes}

# edges: (src, src_side, src_frac, tgt, tgt_side, tgt_frac, kind, smult, tmult, label)
#   kind: assoc | comp (filled diamond at src/whole) | m2m | dep (dashed enum)
edges = [
 ("user", "L", 0.5, "sapp", "T", 0.3, "assoc", "1", "0..1", "submits"),
 ("user", "B", 0.5, "store", "T", 0.5, "assoc", "1", "0..*", "owns"),
 ("user", "R", 0.7, "order", "T", 0.5, "assoc", "1", "0..*", "places"),

 ("store", "L", 0.9, "slog", "R", 0.4, "comp", "1", "0..*", "logs"),
 ("store", "B", 0.5, "prod", "T", 0.5, "comp", "1", "0..*", "sells"),
 ("store", "R", 0.7, "order", "L", 0.7, "assoc", "1", "0..*", "receives"),

 ("cat", "B", 0.5, "sub", "T", 0.5, "assoc", "1", "0..*", "groups"),
 ("sub", "R", 0.5, "prod", "L", 0.25, "assoc", "1", "0..*", "classifies"),

 ("prod", "L", 0.55, "pimg", "T", 0.5, "comp", "1", "1..*", "has"),
 ("prod", "L", 0.8, "ptag", "R", 0.5, "m2m", "*", "*", "tagged"),
 ("prod", "R", 0.45, "oitem", "L", 0.5, "assoc", "1", "0..*", "ordered in"),
 ("order", "B", 0.5, "oitem", "T", 0.5, "comp", "1", "1..*", "contains"),

 ("user", "R", 0.3, "role", "L", 0.5, "dep", "", "", ""),
 ("store", "R", 0.3, "sstat", "L", 0.5, "dep", "", "", ""),
 ("prod", "B", 0.35, "pstat", "T", 0.5, "dep", "", "", ""),
 ("prod", "B", 0.65, "vstat", "T", 0.5, "dep", "", "", ""),
 ("order", "R", 0.5, "ostat", "L", 0.5, "dep", "", "", ""),
 ("sapp", "T", 0.7, "sas", "B", 0.5, "dep", "", "", ""),
]

# ---------------------------------------------------------------- fonts
def fnt(sz, b=False):
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""),
            int(sz * S))
    except Exception:
        return ImageFont.load_default()
F_NAME, F_STEREO, F_BODY, F_MULT, F_LBL = fnt(11.5, True), fnt(9, False), fnt(9.5), fnt(8.5), fnt(8.5, False)

_probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))
def tw(s, f): return _probe.textlength(s, font=f) / S      # logical width

def box_w(c):
    _, name, x, y, attrs, ops, is_enum = c
    w = tw(name, F_NAME) + 24
    for s in attrs + ops:
        w = max(w, tw(s, F_BODY) + 18)
    if is_enum:
        w = max(w, tw("<<enumeration>>", F_STEREO) + 18)
    return max(MINW, math.ceil(w))

def box_h(c):
    _, name, x, y, attrs, ops, is_enum = c
    h = TITLE_H + (ESTEREO_H if is_enum else 0)
    h += PAD + max(1, len(attrs)) * ROW + PAD
    if ops:
        h += PAD + len(ops) * ROW + PAD
    return h

DIM = {c[0]: (c[2], c[3], box_w(c), box_h(c)) for c in classes}

def anchor(cid, side, frac=0.5):
    x, y, w, h = DIM[cid]
    if side == "L": return (x, y + h * frac)
    if side == "R": return (x + w, y + h * frac)
    if side == "T": return (x + w * frac, y)
    if side == "B": return (x + w * frac, y + h)

DIRV = {"L": (-1, 0), "R": (1, 0), "T": (0, -1), "B": (0, 1)}

def route(p0, s0, p1, s1):
    d0, d1 = DIRV[s0], DIRV[s1]
    h0, h1 = d0[1] == 0, d1[1] == 0      # horizontal exit?
    if h0 and h1:
        mx = (p0[0] + p1[0]) / 2
        return [p0, (mx, p0[1]), (mx, p1[1]), p1]
    if (not h0) and (not h1):
        my = (p0[1] + p1[1]) / 2
        return [p0, (p0[0], my), (p1[0], my), p1]
    if h0:
        return [p0, (p1[0], p0[1]), p1]
    return [p0, (p0[0], p1[1]), p1]

# ---------------------------------------------------------------- draw.io
esc = lambda s: html.escape(s, quote=True)
cells = []
def add(s): cells.append(s)
def uml_class(c):
    cid, name, x, y, attrs, ops, is_enum = c
    w = box_w(c)
    head = ("<<enumeration>>\n" if is_enum else "") + name
    style = ("swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;"
             "horizontal=1;startSize=%d;horizontalStack=0;resizeParent=1;resizeParentMax=0;"
             "html=1;collapsible=0;swimlaneFillColor=#ffffff;fillColor=#ffffff;strokeColor=#000000;"
             "fontColor=#000000;fontSize=12;" % (TITLE_H + (ESTEREO_H if is_enum else 0)))
    add(f'<mxCell id="{cid}" value="{esc(head)}" style="{style}" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{box_h(c)}" as="geometry"/></mxCell>')
    yo = TITLE_H + (ESTEREO_H if is_enum else 0)
    rowst = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
             "spacingLeft=6;spacingRight=6;overflow=hidden;rotatable=0;points=[];"
             "html=1;fontSize=11;fontColor=#000000;")
    line = ("line;strokeWidth=1;strokeColor=#000000;fillColor=none;align=left;"
            "verticalAlign=middle;spacingTop=-1;rotatable=0;points=[];")
    for i, a in enumerate(attrs):
        add(f'<mxCell id="{cid}_a{i}" value="{esc(a)}" style="{rowst}" vertex="1" parent="{cid}">'
            f'<mxGeometry y="{yo}" width="{w}" height="{ROW}" as="geometry"/></mxCell>')
        yo += ROW
    if ops:
        add(f'<mxCell id="{cid}_d" value="" style="{line}" vertex="1" parent="{cid}">'
            f'<mxGeometry y="{yo}" width="{w}" height="8" as="geometry"/></mxCell>')
        yo += 8
        for i, o in enumerate(ops):
            add(f'<mxCell id="{cid}_o{i}" value="{esc(o)}" style="{rowst}" vertex="1" parent="{cid}">'
                f'<mxGeometry y="{yo}" width="{w}" height="{ROW}" as="geometry"/></mxCell>')
            yo += ROW

for c in classes:
    uml_class(c)

def sidexy(side, frac):
    if side == "L": return (0, frac)
    if side == "R": return (1, frac)
    if side == "T": return (frac, 0)
    return (frac, 1)
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
    add(f'<mxCell id="e{i}" value="{esc(lbl)}" style="{st}" edge="1" parent="1" source="{s}" target="{t}">'
        f'<mxGeometry relative="1" as="geometry"/></mxCell>')
    if sm:
        add(f'<mxCell id="e{i}s" value="{esc(sm)}" style="resizable=0;html=1;fontSize=10;" '
            f'vertex="1" connectable="0" parent="e{i}"><mxGeometry x="-0.8" relative="1" as="geometry">'
            f'<mxPoint as="offset"/></mxGeometry></mxCell>')
    if tm:
        add(f'<mxCell id="e{i}t" value="{esc(tm)}" style="resizable=0;html=1;fontSize=10;" '
            f'vertex="1" connectable="0" parent="e{i}"><mxGeometry x="0.8" relative="1" as="geometry">'
            f'<mxPoint as="offset"/></mxGeometry></mxCell>')

maxx = max(DIM[c][0] + DIM[c][2] for c in DIM) + 40
maxy = max(DIM[c][1] + DIM[c][3] for c in DIM) + 40
xml = f'''<mxfile host="app.diagrams.net" type="device">
  <diagram id="classdiag" name="Class Diagram">
    <mxGraphModel dx="1400" dy="1000" grid="0" page="1" pageWidth="{maxx}" pageHeight="{maxy}" math="0" shadow="0">
      <root><mxCell id="0"/><mxCell id="1" parent="0"/>
        {chr(10).join(cells)}
      </root></mxGraphModel>
  </diagram>
</mxfile>'''
open(sys.argv[1], "w").write(xml)

# ---------------------------------------------------------------- PIL render
W, H = int(maxx * S), int(maxy * S)
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
def sc(x, y): return (x * S, y * S)
BLACK = "#000000"

def ctext(cx, cy, s, f, fill=BLACK):
    bb = d.textbbox((0, 0), s, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2, cy - (bb[3] - bb[1]) / 2 - bb[1]), s, font=f, fill=fill)
def ltext(lx, cy, s, f, fill=BLACK):
    bb = d.textbbox((0, 0), s, font=f)
    d.text((lx, cy - (bb[3] - bb[1]) / 2 - bb[1]), s, font=f, fill=fill)

def diamond(p, dirv, size=8, fill=BLACK):
    dx, dy = dirv; px, py = -dy, dx
    cx, cy = p[0] + dx * size, p[1] + dy * size      # centre one half-len along edge
    pts = [(cx + dx * size, cy + dy * size), (cx + px * size * 0.6, cy + py * size * 0.6),
           (cx - dx * size, cy - dy * size), (cx - px * size * 0.6, cy - py * size * 0.6)]
    d.polygon([sc(*pp) for pp in pts], fill=fill, outline=BLACK)
def open_arrow(p, dirv, size=10):
    # arrowhead pointing along dirv, tip at p (logical)
    dx, dy = dirv; px, py = -dy, dx
    tip = sc(*p)
    a = (tip[0] - (dx * size - px * size * 0.55) * S, tip[1] - (dy * size - py * size * 0.55) * S)
    b = (tip[0] - (dx * size + px * size * 0.55) * S, tip[1] - (dy * size + py * size * 0.55) * S)
    d.line([a, tip], fill=BLACK, width=2)
    d.line([b, tip], fill=BLACK, width=2)
def dline(pts, dashed=False, w=2):
    for i in range(len(pts) - 1):
        x1, y1 = sc(*pts[i]); x2, y2 = sc(*pts[i + 1])
        if not dashed:
            d.line([x1, y1, x2, y2], fill=BLACK, width=w)
        else:
            tot = math.hypot(x2 - x1, y2 - y1); n = max(1, int(tot / 11))
            for k in range(n):
                if k % 2: continue
                t1, t2 = k / n, (k + 1) / n
                d.line([x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1,
                        x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2], fill=BLACK, width=w)

# edges first (under boxes)
for s, ss, sf, t, ts, tf, kind, sm, tm, lbl in edges:
    p0 = anchor(s, ss, sf); p1 = anchor(t, ts, tf)
    pts = route(p0, ss, p1, ts)
    dline(pts, dashed=(kind == "dep"))
    if kind == "comp":
        diamond(p0, DIRV[ss])
    if kind == "dep":
        open_arrow(p1, (-DIRV[ts][0], -DIRV[ts][1]))
    # multiplicity labels just outside the anchors
    off = 13
    if sm:
        ox, oy = DIRV[ss]; ltext((p0[0] + ox * 6 + (4 if ox >= 0 else -tw(sm, F_MULT) - 4)) * S,
                                 (p0[1] + oy * off) * S, sm, F_MULT)
    if tm:
        ox, oy = DIRV[ts]; ltext((p1[0] + ox * 6 + (4 if ox >= 0 else -tw(tm, F_MULT) - 4)) * S,
                                 (p1[1] + oy * off) * S, tm, F_MULT)
    if lbl:
        bi = max(range(len(pts) - 1),
                 key=lambda k: (pts[k + 1][0] - pts[k][0]) ** 2 + (pts[k + 1][1] - pts[k][1]) ** 2)
        mid = ((pts[bi][0] + pts[bi + 1][0]) / 2, (pts[bi][1] + pts[bi + 1][1]) / 2)
        bb = d.textbbox((0, 0), lbl, font=F_LBL); twd = (bb[2] - bb[0]) / S + 6
        mx, my = mid
        d.rectangle([sc(mx - twd / 2, my - 8)[0], sc(mx - twd / 2, my - 8)[1],
                     sc(mx + twd / 2, my + 8)[0], sc(mx + twd / 2, my + 8)[1]], fill="white")
        ctext(mx * S, my * S, lbl, F_LBL, fill="#333333")

# boxes
for c in classes:
    cid, name, x, y, attrs, ops, is_enum = c
    w = box_w(c); h = box_h(c)
    d.rectangle([*sc(x, y), *sc(x + w, y + h)], fill="white", outline=BLACK, width=2)
    yo = y
    th = TITLE_H + (ESTEREO_H if is_enum else 0)
    if is_enum:
        ctext((x + w / 2) * S, (y + ESTEREO_H / 2 + 3) * S, "«enumeration»", F_STEREO, fill="#333333")
        ctext((x + w / 2) * S, (y + ESTEREO_H + TITLE_H / 2) * S, name, F_NAME)
    else:
        ctext((x + w / 2) * S, (y + TITLE_H / 2) * S, name, F_NAME)
    yo = y + th
    d.line([*sc(x, yo), *sc(x + w, yo)], fill=BLACK, width=2)
    cy = yo + PAD + ROW / 2
    for a in attrs:
        ltext((x + 6) * S, cy * S, a, F_BODY); cy += ROW
    if ops:
        divy = yo + PAD + len(attrs) * ROW + PAD
        d.line([*sc(x, divy), *sc(x + w, divy)], fill=BLACK, width=2)
        cy = divy + PAD + ROW / 2
        for o in ops:
            ltext((x + 6) * S, cy * S, o, F_BODY); cy += ROW

img.save(sys.argv[2])
print("wrote", sys.argv[1], "and", sys.argv[2], img.size)
