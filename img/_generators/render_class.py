#!/usr/bin/env python3
"""Render a hand-edited UML class-diagram .drawio (the kind emitted by
gen_class.py) to a clean black-and-white PNG, honouring the user's box
placement, sizes, edge anchors and waypoints.  draw.io headless export
segfaults in this env, so we parse the mxGraph XML and draw with PIL.
Usage: render_class.py <in.drawio> <out.png> [scale]
"""
import sys, re, math, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
S = float(sys.argv[3]) if len(sys.argv) > 3 else 2.2
BLACK = "#000000"

root = ET.parse(SRC).getroot()
cells = list(root.iter("mxCell"))
by_id = {c.get("id"): c for c in cells}

def parent_of(c): return c.get("parent")
def top_class(cid):
    c = by_id.get(cid)
    while c is not None and c.get("parent") not in (None, "1", "0"):
        c = by_id.get(c.get("parent"))
    return c.get("id") if c is not None else cid

# ---- classes (top-level swimlanes) ----
classes = {}      # id -> dict(name, x,y,w,h, is_enum, attrs[], ops[])
order = []
for c in cells:
    if c.get("vertex") == "1" and (c.get("style") or "").startswith("swimlane") and c.get("parent") == "1":
        g = c.find("mxGeometry")
        val = (c.get("value") or "").replace("&#10;", "\n")
        is_enum = "enumeration" in val
        name = val.replace("<<enumeration>>", "").replace("«enumeration»", "").strip()
        classes[c.get("id")] = dict(name=name, x=float(g.get("x")), y=float(g.get("y")),
                                    w=float(g.get("width")), h=float(g.get("height")),
                                    is_enum=is_enum, rows=[], divider=False)
        order.append(c.get("id"))
# children rows in document order
for c in cells:
    p = c.get("parent")
    if p in classes and c.get("id") not in classes:
        st = c.get("style") or ""
        if st.startswith("line"):
            classes[p]["divider"] = len(classes[p]["rows"])      # index where ops begin
        elif st.startswith("text"):
            classes[p]["rows"].append((c.get("value") or "").strip())

# ---- edges ----
def fnum(st, k):
    m = re.search(k + r"=([-0-9.]+)", st); return float(m.group(1)) if m else None
edges = []
for c in cells:
    if c.get("edge") != "1":
        continue
    st = c.get("style") or ""
    s, t = top_class(c.get("source")), top_class(c.get("target"))
    if s not in classes or t not in classes:
        continue
    kind = "comp" if "diamond" in st.lower() else ("dep" if ("dashed=1" in st and "open" in st.lower()) else "assoc")
    g = c.find("mxGeometry")
    pts = []
    if g is not None:
        arr = g.find("Array")
        if arr is not None:
            pts = [(float(p.get("x")), float(p.get("y"))) for p in arr.findall("mxPoint")]
    sm = tm = ""
    for ch in cells:
        if ch.get("parent") == c.get("id"):
            cg = ch.find("mxGeometry"); xf = cg.get("x") if cg is not None else None
            if xf is None: continue
            (sm, tm) = ((ch.get("value") or "", tm) if float(xf) < 0 else (sm, ch.get("value") or ""))
    edges.append(dict(s=s, t=t, kind=kind, val=(c.get("value") or "").strip(), pts=pts,
                      ex=fnum(st, "exitX"), ey=fnum(st, "exitY"),
                      nx=fnum(st, "entryX"), ny=fnum(st, "entryY"), sm=sm.strip(), tm=tm.strip()))

# ---- geometry helpers ----
def side_point(b, fx, fy):
    """point on box b given exit/entry fractions; returns (pt, side)."""
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    if fx is None or fy is None:
        return None, None
    if fx <= 0.02: return (x, y + fy * h), "L"
    if fx >= 0.98: return (x + w, y + fy * h), "R"
    if fy <= 0.02: return (x + fx * w, y), "T"
    return (x + fx * w, y + fy * h), "B"

def nearest_side(b, toward):
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    cx, cy = x + w / 2, y + h / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if abs(dx) / (w / 2 + 1) >= abs(dy) / (h / 2 + 1):
        return ((x + w, cy), "R") if dx >= 0 else ((x, cy), "L")
    return ((cx, y + h), "B") if dy >= 0 else ((cx, y), "T")

DIRV = {"L": (-1, 0), "R": (1, 0), "T": (0, -1), "B": (0, 1)}
def route(p0, s0, p1, s1):
    d0, d1 = DIRV[s0], DIRV[s1]
    h0, h1 = d0[1] == 0, d1[1] == 0
    if h0 and h1:
        mx = (p0[0] + p1[0]) / 2; return [p0, (mx, p0[1]), (mx, p1[1]), p1]
    if (not h0) and (not h1):
        my = (p0[1] + p1[1]) / 2; return [p0, (p0[0], my), (p1[0], my), p1]
    return [p0, (p1[0], p0[1]), p1] if h0 else [p0, (p0[0], p1[1]), p1]

# ---- canvas ----
minx = min(b["x"] for b in classes.values()) - 30
miny = min(b["y"] for b in classes.values()) - 30
maxx = max(b["x"] + b["w"] for b in classes.values()) + 30
maxy = max(b["y"] + b["h"] for b in classes.values()) + 30
OX, OY = minx, miny
W, H = int((maxx - minx) * S), int((maxy - miny) * S)
img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img)
def sc(x, y): return ((x - OX) * S, (y - OY) * S)

def fnt(sz, b=False):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), int(sz * S))
    except Exception:
        return ImageFont.load_default()
F_NAME, F_STEREO, F_BODY, F_MULT, F_LBL = fnt(11, True), fnt(8.5), fnt(9), fnt(8.5), fnt(8.5)
def tw(s, f): return d.textlength(s, font=f)
def fit(s, f0, maxpx):
    f = f0
    for sz in (9, 8.5, 8, 7.5, 7):
        f = fnt(sz)
        if tw(s, f) <= maxpx * S: break
    return f
def ctext(cx, cy, s, f, fill=BLACK):
    bb = d.textbbox((0, 0), s, font=f); d.text((cx - (bb[2] - bb[0]) / 2, cy - (bb[3] - bb[1]) / 2 - bb[1]), s, font=f, fill=fill)
def ltext(lx, cy, s, f, fill=BLACK):
    bb = d.textbbox((0, 0), s, font=f); d.text((lx, cy - (bb[3] - bb[1]) / 2 - bb[1]), s, font=f, fill=fill)

def diamond(p, side, size=8):
    dx, dy = DIRV[side]; px, py = -dy, dx
    cx, cy = p[0] + dx * size, p[1] + dy * size
    pts = [(cx + dx * size, cy + dy * size), (cx + px * size * 0.6, cy + py * size * 0.6),
           (cx - dx * size, cy - dy * size), (cx - px * size * 0.6, cy - py * size * 0.6)]
    d.polygon([sc(*pp) for pp in pts], fill=BLACK, outline=BLACK)
def open_arrow(p, side, size=10):
    dx, dy = DIRV[side]; px, py = -dy, dx          # points INTO the box (along -side dir)
    ux, uy = -dx, -dy
    tip = sc(*p)
    a = (tip[0] - (ux * size - px * size * 0.55) * S, tip[1] - (uy * size - py * size * 0.55) * S)
    b = (tip[0] - (ux * size + px * size * 0.55) * S, tip[1] - (uy * size + py * size * 0.55) * S)
    d.line([a, tip], fill=BLACK, width=2); d.line([b, tip], fill=BLACK, width=2)
def polyline(pts, dashed=False, w=2):
    for i in range(len(pts) - 1):
        x1, y1 = sc(*pts[i]); x2, y2 = sc(*pts[i + 1])
        if not dashed:
            d.line([x1, y1, x2, y2], fill=BLACK, width=w)
        else:
            tot = math.hypot(x2 - x1, y2 - y1); n = max(1, int(tot / 11))
            for k in range(n):
                if k % 2: continue
                t1, t2 = k / n, (k + 1) / n
                d.line([x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1, x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2], fill=BLACK, width=w)

# ---- draw edges (under boxes) ----
for e in edges:
    bs, bt = classes[e["s"]], classes[e["t"]]
    p0, s0 = side_point(bs, e["ex"], e["ey"])
    p1, s1 = side_point(bt, e["nx"], e["ny"])
    if p0 is None:
        toward = e["pts"][0] if e["pts"] else (bt["x"] + bt["w"] / 2, bt["y"] + bt["h"] / 2)
        p0, s0 = nearest_side(bs, toward)
    if p1 is None:
        toward = e["pts"][-1] if e["pts"] else (bs["x"] + bs["w"] / 2, bs["y"] + bs["h"] / 2)
        p1, s1 = nearest_side(bt, toward)
    if e["pts"]:
        pts = [p0] + e["pts"] + [p1]
    else:
        pts = route(p0, s0, p1, s1)
    polyline(pts, dashed=(e["kind"] == "dep"))
    if e["kind"] == "comp":
        diamond(p0, s0)
    if e["kind"] == "dep":
        open_arrow(p1, s1)
    off = 13
    if e["sm"]:
        ox, oy = DIRV[s0]
        lx = p0[0] + (6 if ox >= 0 else -6 - tw(e["sm"], F_MULT) / S)
        ltext(*sc(lx, p0[1] + oy * off), e["sm"], F_MULT)
    if e["tm"]:
        ox, oy = DIRV[s1]
        lx = p1[0] + (6 if ox >= 0 else -6 - tw(e["tm"], F_MULT) / S)
        ltext(*sc(lx, p1[1] + oy * off), e["tm"], F_MULT)
    if e["val"]:
        bi = max(range(len(pts) - 1), key=lambda k: (pts[k + 1][0] - pts[k][0]) ** 2 + (pts[k + 1][1] - pts[k][1]) ** 2)
        mx, my = ((pts[bi][0] + pts[bi + 1][0]) / 2, (pts[bi][1] + pts[bi + 1][1]) / 2)
        twd = tw(e["val"], F_LBL) / S + 6
        d.rectangle([*sc(mx - twd / 2, my - 8), *sc(mx + twd / 2, my + 8)], fill="white")
        ctext(*sc(mx, my), e["val"], F_LBL, fill="#333333")

# ---- draw boxes ----
for cid in order:
    b = classes[cid]
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    d.rectangle([*sc(x, y), *sc(x + w, y + h)], fill="white", outline=BLACK, width=2)
    is_enum = b["is_enum"]; rows = b["rows"]
    title_h = 44 if is_enum else 28
    if is_enum:
        ctext(*sc(x + w / 2, y + 11), "«enumeration»", F_STEREO, fill="#333333")
        ctext(*sc(x + w / 2, y + 30), b["name"], fit(b["name"], F_NAME, w - 10), fill=BLACK)
    else:
        ctext(*sc(x + w / 2, y + title_h / 2), b["name"], fit(b["name"], F_NAME, w - 10), fill=BLACK)
    ydiv = y + title_h
    d.line([*sc(x, ydiv), *sc(x + w, ydiv)], fill=BLACK, width=2)
    div = b["divider"] if b["divider"] is not False else len(rows)
    attrs, ops = rows[:div], rows[div:]
    avail = h - title_h
    nattr, nop = max(1, len(attrs)), len(ops)
    if ops:
        attr_band = avail * nattr / (nattr + nop)
        ydiv2 = ydiv + attr_band
    else:
        attr_band = avail; ydiv2 = None
    rowh = attr_band / max(1, len(attrs))
    cy = ydiv + rowh / 2
    for a in attrs:
        ltext(*sc(x + 6, cy), a, fit(a, F_BODY, w - 10)); cy += rowh
    if ops:
        d.line([*sc(x, ydiv2), *sc(x + w, ydiv2)], fill=BLACK, width=2)
        oh = (h - (ydiv2 - y)) / nop
        cy = ydiv2 + oh / 2
        for o in ops:
            ltext(*sc(x + 6, cy), o, fit(o, F_BODY, w - 10)); cy += oh

img.save(OUT)
print("rendered", OUT, img.size, "from", SRC, "(%d classes, %d edges)" % (len(classes), len(edges)))
