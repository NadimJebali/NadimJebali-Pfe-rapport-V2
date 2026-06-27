#!/usr/bin/env python3
"""Sprint 4 use-case diagram (AI Verification & Premium Tier)."""
import sys
pos = {
 "View product suggestions":      (430,110,210,46),
 "Switch theme (light/dark)":     (430,190,210,46),
 "Subscribe to premium":          (430,440,210,46),
 "Manage subscription":           (430,540,210,46),
 "Use DB chat assistant":         (430,650,210,46),
 "AI verification (store & product)":(430,745,210,46),
 "Override AI verdict":           (430,840,210,46),
 "Curate product suggestions":    (720,110,190,46),
 "Operate multiple stores":       (720,260,190,46),
 "Use advanced customisation":    (720,330,190,46),
 "unsubscribe":                   (720,540,150,46),
}
GREEN = {"View product suggestions","Use DB chat assistant","AI verification (store & product)"}
actors = {"Customer":(70,160), "Seller":(70,500), "Administrator":(70,760)}
owner = {
 "Customer":["View product suggestions","Switch theme (light/dark)"],
 "Seller":["Subscribe to premium","Manage subscription"],
 "Administrator":["Use DB chat assistant","AI verification (store & product)","Override AI verdict"],
}
gens = []
systems = {
 "Stripe":     (1040,400,200,80,"premium subscription"),
 "AI service": (1040,620,200,80,"n8n + LLM"),
}
sysdeps = [
 ("AI service","Curate product suggestions"),
 ("AI service","Use DB chat assistant"),
 ("AI service","AI verification (store & product)"),
 ("Stripe","Subscribe to premium"),
 ("Stripe","Manage subscription"),
]
deps = [
 ("View product suggestions","Curate product suggestions","include"),
 ("Subscribe to premium","Operate multiple stores","include"),
 ("Subscribe to premium","Use advanced customisation","include"),
 ("unsubscribe","Manage subscription","extend"),
 ("Override AI verdict","AI verification (store & product)","extend"),
]
BND = (410,45,920,900)
TITLE = ("Sprint 4 - AI Verification & Premium Tier", (410+920)//2, 68)
CANVAS = (1290, 930)
S = 2.0
exec(open(sys.argv[3]).read())
