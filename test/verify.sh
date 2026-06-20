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
check "Ch.2 analysis summary count = 36"          present chap_02.tex '36 user stories'
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

# ----- summary -------------------------------------------------------------
section "Result"
printf '  %d passed, %d failed\n\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
