#!/usr/bin/env bash
#
# verify.sh — executable acceptance gates for the PFE report build.
#
# Used test-first (TDD): each report slice adds a block of assertions here,
# the block fails (RED), then the slice is implemented until it passes (GREEN).
#
# Usage:
#   test/verify.sh            # build, then run all gates
#   test/verify.sh --no-build # skip the LaTeX build, check existing artifacts
#
# Exit code 0 = all gates pass; non-zero = at least one gate failed.

set -u
cd "$(dirname "$0")/.." || exit 2
ROOT="$(pwd)"

PASS=0
FAIL=0
pass() { printf '  \033[32mPASS\033[0m  %s\n' "$1"; PASS=$((PASS + 1)); }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAIL=$((FAIL + 1)); }
# check <description> <test-command...>  — passes iff the command succeeds
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then pass "$d"; else fail "$d"; fi; }
section() { printf '\n\033[1m%s\033[0m\n' "$1"; }

# ----- helpers -------------------------------------------------------------
# greps that must find NOTHING pass (negated grep). grep -q returns 1 when no
# match, so we invert: "absent" passes when grep finds nothing.
absent() { ! grep -qiE "$2" "$1" 2>/dev/null; }                 # pattern absent in file
present() { grep -qE "$2" "$1" 2>/dev/null; }                   # pattern present in file

# ----- build ---------------------------------------------------------------
if [ "${1:-}" != "--no-build" ]; then
  section "Build (latexmk)"
  if latexmk -pdf -interaction=nonstopmode -file-line-error main.tex >/tmp/report-build.log 2>&1; then
    pass "latexmk build exits 0"
  else
    fail "latexmk build exits 0  (see /tmp/report-build.log)"
  fi
fi

# ----- global gates --------------------------------------------------------
section "Global gates"
check "main.pdf produced"                         test -f main.pdf
# No hard LaTeX errors in the log (lines beginning with '! ').
check "no LaTeX '! ' errors in main.log"          bash -c '! grep -qE "^! " main.log'
# Authoritative undefined-reference signal: zero literal ?? in the rendered text.
if command -v pdftotext >/dev/null 2>&1; then
  pdftotext main.pdf /tmp/report.txt 2>/dev/null
  check "zero '??' (undefined refs) in PDF"        bash -c '! grep -qF "??" /tmp/report.txt'
  check "zero 'cheebo' in rendered PDF"            bash -c '! grep -qi "cheebo" /tmp/report.txt'
else
  fail "pdftotext available (needed for PDF gates)"
fi
# Brand name must not appear in any source either.
check "zero 'cheebo' in *.tex sources"            bash -c '! grep -riq "cheebo" --include="*.tex" .'
# pdftotext cannot see text baked into PNGs, so guard the diagram sources
# and image filenames directly (the only brand vector left in figures).
check "zero 'cheebo' in diagrams/*.puml"          bash -c '! grep -riq "cheebo" diagrams/'
check "no img filename contains 'cheebo'"         bash -c '! ls img/ | grep -qi "cheebo"'

# ----- slice #7: prefactor + payment corrections ---------------------------
section "Slice #7 — prefactor & payment corrections"
check "main.tex inputs chap_03"                   present main.tex '\\input\{chap_03\}'
check "main.tex inputs chap_04"                   present main.tex '\\input\{chap_04\}'
check "\\imagePlaceholder defined"                 present tpl/new_commands.tex 'newcommand\{\\imagePlaceholder\}'
check "listings package loaded"                   present tpl/new_commands.tex 'usepackage\{listings\}'
check "chap_03.tex exists"                        test -f chap_03.tex
check "chap_04.tex exists"                        test -f chap_04.tex
check "\\imagePlaceholder used in a chapter"       bash -c 'grep -lq "imagePlaceholder" chap_03.tex chap_04.tex'
check "a code listing present in a chapter"       bash -c 'grep -Elq "lstlisting|lstinputlisting" chap_03.tex chap_04.tex'
# Ch.1 out-of-scope no longer mentions payment (check the 3 lines after the label).
check "Ch.1 out-of-scope drops payment"           bash -c '! grep -A3 "Out of scope" chap_01.tex | grep -qi "payment"'
# Ch.2 backlog gains a payment user story (US36) and the counts stay consistent.
check "Ch.2 backlog has payment story US36"       present chap_02.tex 'US36 &.*pay'
check "Ch.2 analysis summary count = 39"          present chap_02.tex '39 user stories'
check "Ch.2 no stale 36-user-stories count"       absent chap_02.tex '36 user stories'
check "Ch.2 Sprint 3 row includes US36"           bash -c 'grep -q "Sprint 3.*US36" chap_02.tex'

# ----- slice #8: Ch.3 Release 1 overview + backlog + Sprint 1 --------------
section "Slice #8 — Ch.3 Release 1 + Sprint 1"
check "Ch.3 prefactor smoke stub removed"         absent chap_03.tex 'under construction|smoke test'
check "Ch.3 has the release label"                present chap_03.tex 'label\{chap:release1\}'
check "Ch.3 embeds the R1 use-case diagram"       present chap_03.tex 'uc-release1'
check "Ch.3 embeds the R1 class diagram"          present chap_03.tex 'class-release1'
check "Ch.3 embeds the Sprint 1 use-case diagram" present chap_03.tex 'uc-sprint1'
check "Ch.3 embeds the registration activity"     present chap_03.tex 'act-registration'
check "Ch.3 reuses the auth sequence diagram"     present chap_03.tex 'seq-auth'
check "Ch.3 has the Release 1 backlog table"      present chap_03.tex 'label\{tab:backlog-r1\}'
check "Ch.3 has >= 4 textual use-case tables"     bash -c '[ "$(grep -c "Use case:" chap_03.tex)" -ge 4 ]'
check "Ch.3 has >= 5 realisation placeholders"    bash -c '[ "$(grep -c "imagePlaceholder" chap_03.tex)" -ge 5 ]'
check "img/uc-release1.png rendered"              test -f img/uc-release1.png
check "img/class-release1.png rendered"           test -f img/class-release1.png
check "img/uc-sprint1.png rendered"               test -f img/uc-sprint1.png
check "img/act-registration.png rendered"         test -f img/act-registration.png
# every \ref in Ch.3 figures/tables actually resolves (no ?? already gated globally)

# ----- slice #9: Ch.3 Sprint 2 + conclusion -------------------------------
section "Slice #9 — Ch.3 Sprint 2 + conclusion"
check "Ch.3 has the Sprint 2 section"             present chap_03.tex 'Sprint 2 --- Store'
check "Ch.3 embeds the Sprint 2 use-case diagram" present chap_03.tex 'uc-sprint2'
check "Ch.3 embeds the create-store activity"     present chap_03.tex 'act-create-store'
check "Ch.3 embeds the AI-redesign activity"      present chap_03.tex 'act-ai-redesign'
check "Ch.3 embeds the AI-redesign sequence"      present chap_03.tex 'seq-ai-redesign'
check "Ch.3 has >= 8 textual use-case tables"     bash -c '[ "$(grep -c "Use case:" chap_03.tex)" -ge 8 ]'
check "Ch.3 ends with a Conclusion"               present chap_03.tex 'section\*\{Conclusion\}'
check "img/uc-sprint2.png rendered"               test -f img/uc-sprint2.png
check "img/act-create-store.png rendered"         test -f img/act-create-store.png
check "img/act-ai-redesign.png rendered"          test -f img/act-ai-redesign.png
check "img/seq-ai-redesign.png rendered"          test -f img/seq-ai-redesign.png

# ----- slice #10: Ch.4 Release 2 overview + Sprint 3 (orders, payment) -----
section "Slice #10 — Ch.4 Release 2 + Sprint 3"
check "Ch.4 prefactor smoke stub removed"         absent chap_04.tex 'under construction|smoke test'
check "Ch.4 has the release label"                present chap_04.tex 'label\{chap:release2\}'
check "Ch.4 embeds the R2 use-case diagram"       present chap_04.tex 'uc-release2'
check "Ch.4 embeds the R2 class diagram"          present chap_04.tex 'class-release2'
check "Ch.4 embeds the Sprint 3 use-case diagram" present chap_04.tex 'uc-sprint3'
check "Ch.4 embeds the checkout-payment activity" present chap_04.tex 'act-checkout-payment'
check "Ch.4 reuses the order sequence diagram"    present chap_04.tex 'seq-order'
check "Ch.4 has the Release 2 backlog table"      present chap_04.tex 'label\{tab:backlog-r2\}'
check "Ch.4 has a Stripe Payment Design section"  present chap_04.tex 'Stripe Payment Design'
check "Ch.4 has the PaymentIntent code listing"   present chap_04.tex 'label=\{lst:paymentintent\}'
check "Ch.4 Stripe text: server-side amount"      present chap_04.tex 'tndToStripeUsdMinor'
check "Ch.4 Stripe text: idempotency key"         present chap_04.tex 'idempotency'
check "Ch.4 Stripe text: signature-verified hook" bash -c 'grep -q "signature" chap_04.tex && grep -q "webhook" chap_04.tex'
check "Ch.4 has >= 4 textual use-case tables"     bash -c '[ "$(grep -c "Use case:" chap_04.tex)" -ge 4 ]'
check "Ch.4 has >= 5 realisation placeholders"    bash -c '[ "$(grep -c "imagePlaceholder" chap_04.tex)" -ge 5 ]'
check "img/uc-release2.png rendered"              test -f img/uc-release2.png
check "img/class-release2.png rendered"           test -f img/class-release2.png
check "img/uc-sprint3.png rendered"               test -f img/uc-sprint3.png
check "img/act-checkout-payment.png rendered"     test -f img/act-checkout-payment.png

# ----- slice #11: Ch.4 Sprint 4 (AI verification & premium) ----------------
section "Slice #11 — Ch.4 Sprint 4 (AI & premium)"
check "Ch.4 has the Sprint 4 section"             present chap_04.tex 'Sprint 4 --- AI Verification'
check "Ch.4 embeds the Sprint 4 use-case diagram" present chap_04.tex 'uc-sprint4'
check "Ch.4 embeds the AI-verification activity"  present chap_04.tex 'act-ai-verification'
check "Ch.4 embeds the moderation activity"       present chap_04.tex 'act-moderation'
check "Ch.4 embeds the AI-verify sequence"        present chap_04.tex 'seq-verify'
check "Ch.4 has an n8n Workflow Design section"   present chap_04.tex 'n8n Workflow Design'
check "Ch.4 embeds all three n8n screenshots"     bash -c 'grep -q "n8n-verify" chap_04.tex && grep -q "n8n-chat" chap_04.tex && grep -q "n8n-redesign" chap_04.tex'
check "Ch.4 has a Premium Tier section"           present chap_04.tex 'subsection\{Premium Tier\}'
check "Ch.4 has >= 7 textual use-case tables"     bash -c '[ "$(grep -c "Use case:" chap_04.tex)" -ge 7 ]'
check "img/uc-sprint4.png rendered"               test -f img/uc-sprint4.png
check "img/act-ai-verification.png rendered"      test -f img/act-ai-verification.png
check "img/act-moderation.png rendered"           test -f img/act-moderation.png
check "img/seq-verify.png rendered"               test -f img/seq-verify.png
# de-branded seq-verify source (the reused diagram had cheebo-ai-verify baked in)
check "seq-verify source de-branded"              absent diagrams/seq-verify.puml 'cheebo'

# ----- slice #12: Tests & Validation + DevOps & Deployment + conclusion ----
section "Slice #12 — Tests, DevOps & Ch.4 conclusion"
check "Ch.4 has a Tests & Validation section"     present chap_04.tex 'section\{Tests'
check "Ch.4 has the test-pyramid figure"          present chap_04.tex 'label\{fig:test-pyramid\}'
check "Ch.4 documents the 473-test suite"         present chap_04.tex '473'
check "Ch.4 no stale 445-test count"              absent chap_04.tex '445'
check "Ch.4 has a DevOps & Deployment section"    present chap_04.tex 'DevOps'
check "Ch.4 has the Dockerfile listing"           present chap_04.tex 'label=\{lst:dockerfile\}'
check "Ch.4 has the docker-compose listing"       present chap_04.tex 'label=\{lst:compose\}'
check "Ch.4 has the CI/CD deploy listing"         present chap_04.tex 'label=\{lst:deploy\}'
check "Ch.4 covers Terraform IaC"                 present chap_04.tex 'Terraform'
check "Ch.4 covers GitHub Actions CI/CD"          present chap_04.tex 'GitHub Actions'
check "Ch.4 covers Caddy TLS termination"         present chap_04.tex 'Caddy'
check "Ch.4 ends with a Conclusion"               present chap_04.tex 'section\*\{Conclusion\}'

# ----- slice #13: profile + password-reset fold-in ------------------------
section "Slice #13 — profile & password-reset fold-in"
# Product backlog gains the three new stories and a 9th feature.
check "Ch.2 backlog has reset story US37"          present chap_02.tex 'US37 &.*reset'
check "Ch.2 backlog has profile story US38"        present chap_02.tex 'US38 &.*profile'
check "Ch.2 backlog has purchase-history US39"     present chap_02.tex 'US39 &'
check "Ch.2 backlog has a 9th feature (F9)"        present chap_02.tex 'textbf\{F9\}'
check "Ch.2 summary now says 9 features"           present chap_02.tex '9 features'
check "Ch.2 Sprint 1 plan includes US37"           bash -c 'grep -q "Sprint 1.*US37" chap_02.tex'
check "Ch.2 Sprint 3 plan includes US38"           bash -c 'grep -q "Sprint 3.*US38" chap_02.tex'
# Ch.3 Sprint 1 gains the password-reset use case.
check "Ch.3 R1 backlog Sprint 1 includes US37"     present chap_03.tex 'US01--US04, US37'
check "Ch.3 R1 total is now 31"                    present chap_03.tex 'Release~1 total.*textbf\{31\}'
check "Ch.3 has a Reset password use case"         present chap_03.tex 'Use case: Reset password'
check "Ch.3 has a reset realisation placeholder"   bash -c 'grep -iq "reset" chap_03.tex'
check "uc-sprint1 source has Reset password"       present diagrams/uc-sprint1.puml 'Reset password'
check "uc-release1 source has Reset password"      present diagrams/uc-release1.puml 'Reset password'
# Ch.4 Sprint 3 gains the Account Management feature.
check "Ch.4 R2 backlog has Account Management"     present chap_04.tex 'Account Management'
check "Ch.4 R2 backlog Sprint 3 includes US38"     bash -c 'grep -q "US38" chap_04.tex'
check "Ch.4 R2 total is now 47"                    present chap_04.tex 'Release~2 total.*textbf\{47\}'
check "Ch.4 has a Manage profile use case"         present chap_04.tex 'Use case: Manage profile'
check "Ch.4 has a profile realisation placeholder" bash -c 'grep -iq "profile" chap_04.tex'
check "uc-sprint3 source has Manage profile"       present diagrams/uc-sprint3.puml 'Manage profile'
check "uc-release2 source has Manage profile"      present diagrams/uc-release2.puml 'Manage profile'
# Test totals updated consistently (473 = backend 346 + frontend 127).
check "Ch.4 test pyramid backend count = 346"      present chap_04.tex '346'
check "Ch.4 test pyramid frontend count = 127"     present chap_04.tex '127'

# ----- back-matter & polish -----------------------------------------------
section "Back-matter & polish"
check "General Conclusion written (English)"      present conclusion.tex 'General Conclusion'
check "General Conclusion has prose"              bash -c '[ "$(wc -l < conclusion.tex)" -ge 20 ]'
check "no French 'Conclusion generale' heading"  bash -c '! grep -rq "Conclusion g" *.tex'
check "Dedication heading in English"             present dedicaces.tex 'Dedication'
check "Acknowledgements heading in English"       present remerciement.tex 'Acknowledgements'
check "no French Dedicace/Remerciements headings" bash -c '! grep -rqE "D.dicace|Remerciements" *.tex'
check "bibliography de-doubled (no \\input webo)"  absent main.tex '\\input\{webo\}'
check "bibliography title is English"             present main.tex 'title=\{Bibliography\}'
check "biblio has the stack references"           bash -c 'grep -q "@electronic{nestjs" biblio.bib && grep -q "@electronic{stripe" biblio.bib'

# ----- architecture figures (logos + de-brand) ----------------------------
section "Architecture figures (v2 with logos)"
check "Ch.2 uses the logical arch v2"             present chap_02.tex 'arch-3tier-v2'
check "Ch.2 uses the Docker arch v2"              present chap_02.tex 'arch-docker-v2'
check "logical arch v2 rendered"                  test -f img/arch-3tier-v2.png
check "Docker arch v2 rendered"                   test -f img/arch-docker-v2.png
check "branded arch-docker.png retired"           bash -c '! test -f img/arch-docker.png'
check "Docker arch v2 source de-branded"          absent diagrams/arch-docker-v2.puml 'cheebo'
check "no stale ref to old arch PNGs"             bash -c '! grep -rqE "arch-(3tier|docker)\.png" *.tex'

# ----- summary -------------------------------------------------------------
section "Result"
printf '  %d passed, %d failed\n\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
