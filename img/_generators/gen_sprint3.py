#!/usr/bin/env python3
"""Sprint 3 use-case diagram (Orders, Payment & Administration)."""
import sys
pos = {
 "Manage cart":          (430,110,200,46),
 "Checkout":             (430,240,200,46),
 "Manage profile":       (430,370,200,46),
 "View store orders":    (430,500,200,46),
 "Moderate":             (430,620,200,46),
 "Curate featured content":(430,750,200,46),
 "Manage categories":    (430,870,200,46),
 "Delete cart":          (720, 95,180,46),
 "Update cart":          (720,165,180,46),
 "Send mail":            (700,300,175,46),
 "Update profile":       (720,370,180,46),
 "View purchase history":(720,440,180,46),
 "Product":              (720,580,180,46),
 "Store":                (720,645,180,46),
 "Suspend / delete store":(705,710,200,46),
 "Create categories":    (720,835,185,46),
 "Update categories":    (720,900,185,46),
 "Delete categories":    (720,965,185,46),
}
GREEN = {"Suspend / delete store"}
actors = {"Customer":(70,280), "Seller":(70,520), "Administrator":(70,720)}
owner = {
 "Customer":["Manage cart","Checkout","Manage profile"],
 "Seller":["View store orders"],
 "Administrator":["Moderate","Curate featured content","Manage categories"],
}
gens = []
systems = {
 "Stripe":        (1050,205,200,80,"payment gateway"),
 "Email service": (1050,330,200,80,"confirmation email"),
}
sysdeps = [("Stripe","Checkout"), ("Email service","Send mail")]
deps = [
 ("Delete cart","Manage cart","extend"),
 ("Update cart","Manage cart","extend"),
 ("Checkout","Send mail","include"),
 ("Update profile","Manage profile","extend"),
 ("View purchase history","Manage profile","extend"),
 ("Product","Moderate","extend"),
 ("Store","Moderate","extend"),
 ("Suspend / delete store","Moderate","extend"),
 ("Create categories","Manage categories","extend"),
 ("Update categories","Manage categories","extend"),
 ("Delete categories","Manage categories","extend"),
]
BND = (410,45,920,1030)
TITLE = ("Sprint 3 - Orders, Payment & Administration", (410+920)//2, 68)
CANVAS = (1290, 1060)
S = 2.0
exec(open(sys.argv[3]).read())
