#!/usr/bin/env python3
"""Render the product-suggestions sequence diagram to a PNG.

draw.io cannot export headless in this environment (no display server), so
this mirrors img/seq-suggestions.drawio with PIL. Keep the two in sync:
edit the .drawio for structure, then re-run this to regenerate the PNG.

    python3 img/_generators/gen_seq_suggestions.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

S = 2  # render scale for crisp text
OUT = os.path.join(os.path.dirname(__file__), "..", "seq-suggestions.png")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size * S)
F_HEAD = font("DejaVuSans-Bold.ttf", 12)
F_MSG = font("DejaVuSans.ttf", 10)
F_TAG = font("DejaVuSans-Bold.ttf", 10)
F_COND = font("DejaVuSans-Oblique.ttf", 10)

W, H = 980, 620
img = Image.new("RGB", (W * S, H * S), "white")
d = ImageDraw.Draw(img)

def sc(v):
    return v * S

def text_center(cx, cy, s, fnt, fill="black"):
    bb = d.textbbox((0, 0), s, font=fnt)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text((sc(cx) - w / 2, sc(cy) - h / 2), s, font=fnt, fill=fill)

def text_left(x, y, s, fnt, fill="black"):
    d.text((sc(x), sc(y)), s, font=fnt, fill=fill)

def dashed(x1, y1, x2, y2, fill, width=1, dash=6, gap=4):
    import math
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    ux, uy = dx / dist, dy / dist
    n = int(dist // (dash + gap)) + 1
    for i in range(n):
        s0 = i * (dash + gap)
        s1 = min(s0 + dash, dist)
        d.line([sc(x1 + ux * s0), sc(y1 + uy * s0), sc(x1 + ux * s1), sc(y1 + uy * s1)],
               fill=fill, width=width * S)

def head(x, y, w, h, label, fill, stroke):
    d.rectangle([sc(x), sc(y), sc(x + w), sc(y + h)], fill=fill, outline=stroke, width=1 * S)
    lines = label.split("\n")
    cy = y + h / 2 - (len(lines) - 1) * 8
    for ln in lines:
        text_center(x + w / 2, cy, ln, F_HEAD, fill="black")
        cy += 16

def arrowhead_filled(x, y, direction):
    sz = 7 * S
    if direction == "right":
        d.polygon([(sc(x), sc(y)), (sc(x) - sz, sc(y) - sz * 0.6), (sc(x) - sz, sc(y) + sz * 0.6)], fill="black")
    else:
        d.polygon([(sc(x), sc(y)), (sc(x) + sz, sc(y) - sz * 0.6), (sc(x) + sz, sc(y) + sz * 0.6)], fill="black")

def arrowhead_open(x, y, direction):
    sz = 7 * S
    if direction == "right":
        d.line([sc(x), sc(y), sc(x) - sz, sc(y) - sz * 0.6], fill="black", width=1 * S)
        d.line([sc(x), sc(y), sc(x) - sz, sc(y) + sz * 0.6], fill="black", width=1 * S)
    else:
        d.line([sc(x), sc(y), sc(x) + sz, sc(y) - sz * 0.6], fill="black", width=1 * S)
        d.line([sc(x), sc(y), sc(x) + sz, sc(y) + sz * 0.6], fill="black", width=1 * S)

def message(x1, x2, y, label, ret=False):
    direction = "right" if x2 > x1 else "left"
    if ret:
        dashed(x1, y, x2, y, fill="black", width=1)
        arrowhead_open(x2, y, direction)
    else:
        d.line([sc(x1), sc(y), sc(x2), sc(y)], fill="black", width=1 * S)
        arrowhead_filled(x2, y, direction)
    text_center((x1 + x2) / 2, y - 9, label, F_MSG)

# ---- lifelines ----
LIFE = {"page": 150, "back": 390, "n8n": 635, "db": 870}
heads = [
    (80, "page", "Product Page\n(frontend)", "#dae8fc", "#6c8ebf"),
    (320, "back", "Backend API\n(NestJS)", "#d5e8d4", "#82b366"),
    (560, "n8n", "n8n Workflow\n(AI suggestions)", "#ffe6cc", "#d79b00"),
    (800, "db", "Database\n(MariaDB)", "#f8cecc", "#b85450"),
]
hw = {"page": 140, "back": 140, "n8n": 150, "db": 140}
for x, key, label, fill, stroke in heads:
    head(x, 30, hw[key], 44, label, fill, stroke)
    dashed(LIFE[key], 74, LIFE[key], 610, fill=stroke, width=1)

# ---- alt fragment box (drawn before messages so messages sit on top) ----
d.rectangle([sc(105), sc(275), sc(925), sc(580)], outline="#999999", width=1 * S)
d.rectangle([sc(105), sc(275), sc(149), sc(297)], fill="#f5f5f5", outline="#999999", width=1 * S)
text_left(115, 278, "alt", F_TAG)
text_left(155, 279, "[valid candidates returned]", F_COND)
dashed(105, 430, 925, 430, fill="#999999", width=1)
text_left(155, 433, "[workflow error / invalid / empty]", F_COND)

# ---- messages ----
message(LIFE["page"], LIFE["back"], 110, "GET /products/{id}/suggestions")
message(LIFE["back"], LIFE["n8n"], 150, "request candidate product IDs")
message(LIFE["n8n"], LIFE["back"], 190, "candidate IDs", ret=True)

# self message: validate & filter
d.line([sc(390), sc(222), sc(470), sc(222)], fill="black", width=1 * S)
d.line([sc(470), sc(222), sc(470), sc(252)], fill="black", width=1 * S)
d.line([sc(470), sc(252), sc(390), sc(252)], fill="black", width=1 * S)
arrowhead_filled(390, 252, "left")
text_left(412, 228, "validate & filter IDs", F_MSG)

# success branch
message(LIFE["back"], LIFE["db"], 330, "hydrate: fetch products by ID")
message(LIFE["db"], LIFE["back"], 368, "product rows", ret=True)
message(LIFE["back"], LIFE["page"], 406, "same-item offer + alternatives", ret=True)

# fallback branch
message(LIFE["back"], LIFE["db"], 490, "deterministic catalogue query (same category)")
message(LIFE["db"], LIFE["back"], 528, "fallback products", ret=True)
message(LIFE["back"], LIFE["page"], 566, "fallback suggestions", ret=True)

img.save(OUT)
print("wrote", os.path.abspath(OUT), img.size)
