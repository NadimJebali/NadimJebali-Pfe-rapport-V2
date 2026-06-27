#!/usr/bin/env python3
"""Sprint 1 use-case diagram (Authentication & Seller Onboarding)."""
import sys
pos = {
 "Register":                 (450, 90,200,46),
 "Reset password":           (450,175,200,46),
 "Apply to become seller":   (450,255,200,46),
 "Sign out":                 (450,335,200,46),
 "Review seller application":(450,560,200,46),
 "Sign in":                  (730,410,175,46),
 "Verify email":             (730, 90,165,46),
 "Approve application":      (730,530,185,46),
 "Reject application":       (730,595,185,46),
 "Request more information": (730,660,185,46),
}
GREEN = {"Verify email"}
actors = {"Visitor":(70,110), "Customer":(70,320), "Administrator":(70,560)}
owner = {
 "Visitor":["Register"],
 "Customer":["Reset password","Apply to become seller","Sign out"],
 "Administrator":["Review seller application"],
}
gens = [("Customer","Visitor")]
systems = {}
sysdeps = []
deps = [
 ("Register","Verify email","include"),
 ("Reset password","Sign in","include"),
 ("Apply to become seller","Sign in","include"),
 ("Sign out","Sign in","include"),
 ("Review seller application","Sign in","include"),
 ("Approve application","Review seller application","extend"),
 ("Reject application","Review seller application","extend"),
 ("Request more information","Review seller application","extend"),
]
BND = (410,45,940,730)
TITLE = ("Sprint 1 - Authentication & Seller Onboarding", (410+940)//2, 68)
CANVAS = (980, 760)
S = 2.4
exec(open(sys.argv[3]).read())
