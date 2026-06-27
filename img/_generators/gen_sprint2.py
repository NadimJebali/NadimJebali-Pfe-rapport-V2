#!/usr/bin/env python3
"""Sprint 2 use-case diagram (Store & Product Management)."""
import sys
pos = {
 "Manage store":                   (440, 95,210,46),
 "Customize storefront (WYSIWYG)": (440,255,210,46),
 "Manage product":                 (440,560,210,46),
 "Run store-wide sale":            (440,700,210,46),
 "Browse catalogue by category":   (440,850,210,46),   # Customer
 "Create store":        (760, 90,190,46),
 "Update store":        (760,160,190,46),
 "Delete store":        (760,230,190,46),
 "Apply preset":        (760,320,190,46),
 "Upload banner":       (760,390,190,46),
 "Storefront redesign": (760,470,190,46),
 "Create product":      (760,560,190,46),
 "Update product":      (760,630,190,46),
 "Delete product":      (760,700,190,46),
}
GREEN = {"Apply preset","Upload banner","Storefront redesign"}
actors = {"Seller":(70,430), "Customer":(70,860)}
owner = {
 "Seller":["Manage store","Customize storefront (WYSIWYG)","Manage product","Run store-wide sale"],
 "Customer":["Browse catalogue by category"],
}
gens = []
systems = {
 "AI service": (1060,440,200,80,"storefront redesign"),
}
sysdeps = [("AI service","Storefront redesign")]
deps = [
 ("Create store","Manage store","extend"),
 ("Update store","Manage store","extend"),
 ("Delete store","Manage store","extend"),
 ("Apply preset","Customize storefront (WYSIWYG)","extend"),
 ("Upload banner","Customize storefront (WYSIWYG)","extend"),
 ("Storefront redesign","Customize storefront (WYSIWYG)","extend"),
 ("Create product","Manage product","extend"),
 ("Update product","Manage product","extend"),
 ("Delete product","Manage product","extend"),
]
BND = (410,45,975,915)
TITLE = ("Sprint 2 - Store & Product Management", (410+975)//2, 68)
CANVAS = (1300, 985)
S = 2.2
exec(open(sys.argv[3]).read())
