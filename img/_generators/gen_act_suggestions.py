#!/usr/bin/env python3
"""Render the product-suggestions ACTIVITY diagram to a PNG.

draw.io cannot export headless here (no display server), so this mirrors
img/act-suggestions.drawio with PIL, matching the report's diagram style.

    python3 img/_generators/gen_act_suggestions.py
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

S = 2
OUT = os.path.join(os.path.dirname(__file__), "..", "act-suggestions.png")
FD = "/usr/share/fonts/truetype/dejavu"
def font(name, sz): return ImageFont.truetype(os.path.join(FD, name), sz*S)
F  = font("DejaVuSans.ttf", 11)
FB = font("DejaVuSans-Bold.ttf", 11)
FG = font("DejaVuSans-Oblique.ttf", 10)  # guards

W, H = 770, 890
img = Image.new("RGB", (W*S, H*S), "white")
d = ImageDraw.Draw(img)
def sc(x, y): return (x*S, y*S)

ACT_FILL, ACT_LINE = "#dae8fc", "#3b5b8c"
DEC_FILL, DEC_LINE = "#ffe6cc", "#d79b00"

def text_block(cx, cy, lines, fnt, fill="black", lh=14):
    y0 = cy - (len(lines)-1)*lh/2
    for i, ln in enumerate(lines):
        bb = d.textbbox((0,0), ln, font=fnt)
        d.text((cx*S-(bb[2]-bb[0])/2, (y0+i*lh)*S-(bb[3]-bb[1])/2-bb[1]), ln, font=fnt, fill=fill)

def action(cx, cy, w, h, lines):
    d.rounded_rectangle([*sc(cx-w/2, cy-h/2), *sc(cx+w/2, cy+h/2)],
                        radius=8*S, fill=ACT_FILL, outline=ACT_LINE, width=2)
    text_block(cx, cy, lines, F)

def decision(cx, cy, w, h, lines):
    pts = [sc(cx, cy-h/2), sc(cx+w/2, cy), sc(cx, cy+h/2), sc(cx-w/2, cy)]
    d.polygon(pts, fill=DEC_FILL, outline=DEC_LINE)
    d.line(pts+[pts[0]], fill=DEC_LINE, width=2)
    text_block(cx, cy, lines, F)

def start(cx, cy, r=12):
    d.ellipse([*sc(cx-r, cy-r), *sc(cx+r, cy+r)], fill="black")

def end(cx, cy, r=13):
    d.ellipse([*sc(cx-r, cy-r), *sc(cx+r, cy+r)], outline="black", width=2)
    d.ellipse([*sc(cx-r+5, cy-r+5), *sc(cx+r-5, cy+r-5)], fill="black")

def arrowhead(p_from, p_to, size=9):
    x1, y1 = sc(*p_from); x2, y2 = sc(*p_to)
    ux, uy = x2-x1, y2-y1; L = math.hypot(ux, uy) or 1; ux, uy = ux/L, uy/L; px, py = -uy, ux
    d.polygon([(x2,y2), (x2-ux*size*S/1.6+px*size*S/2.6, y2-uy*size*S/1.6+py*size*S/2.6),
               (x2-ux*size*S/1.6-px*size*S/2.6, y2-uy*size*S/1.6-py*size*S/2.6)], fill="black")

def flow(points, head=True):
    for i in range(len(points)-1):
        d.line([*sc(*points[i]), *sc(*points[i+1])], fill="black", width=2)
    if head:
        arrowhead(points[-2], points[-1])

def guard(x, y, s):
    d.text(sc(x, y), s, font=FG, fill="#555")

# ---- node coordinates ----
N = {
 'start':(250,40), 'A1':(250,108), 'A2':(250,196), 'D1':(250,300),
 'A3':(250,430), 'D2':(250,540), 'A4':(250,660), 'A5':(250,760),
 'end':(250,840), 'F1':(565,430),
}
DW, DH = 240, 104          # decision size
AW, AH = 270, 50           # action size

start(*N['start'])
action(*N['A1'], 280, 50, ["The product page requests","suggestions for the viewed product"])
action(*N['A2'], 280, 50, ["The backend calls the n8n suggestion","workflow (bounded by a timeout)"])
decision(*N['D1'], DW, DH, ["Structured IDs","returned before","the timeout?"])
action(*N['A3'], 280, 50, ["Validate and hydrate each","candidate product ID"])
decision(*N['D2'], DW, DH, ["At least one","valid suggestion","remains?"])
action(*N['A4'], 285, 50, ["Assemble the same-item offer","and the alternatives"])
action(*N['A5'], 300, 50, ["Return the suggestions; the","product page renders them"])
end(*N['end'])
action(*N['F1'], 250, 74, ["Run the deterministic","catalogue query (same category,","ranked by similarity)"])

# ---- main flow ----
flow([(250,52),(250,83)])                                   # start -> A1
flow([(250,133),(250,171)])                                 # A1 -> A2
flow([(250,221),(250,248)])                                 # A2 -> D1
flow([(250,352),(250,405)]); guard(258,366,"[yes]")         # D1 -> A3
flow([(250,455),(250,488)])                                 # A3 -> D2
flow([(250,592),(250,635)]); guard(258,606,"[yes]")         # D2 -> A4
flow([(250,685),(250,735)])                                 # A4 -> A5
flow([(250,785),(250,827)])                                 # A5 -> end

# ---- fallback branch ----
flow([(370,300),(565,300),(565,393)]); guard(395,290,"[no / timeout]")   # D1 -> F1
flow([(370,540),(565,540),(565,467)]); guard(395,530,"[none valid]")     # D2 -> F1
flow([(690,430),(715,430),(715,760),(400,760)])                          # F1 -> A5

img.save(OUT)
print("wrote", os.path.abspath(OUT), img.size)
