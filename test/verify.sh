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
check "chap_03 renders a placeholder (smoke)"     present chap_03.tex '\\imagePlaceholder'
check "chap_03 renders a listing (smoke)"         present chap_03.tex 'lstlisting'
check "chap_04 renders a placeholder (smoke)"     present chap_04.tex '\\imagePlaceholder'
check "chap_04 renders a listing (smoke)"         present chap_04.tex 'lstlisting'
# Ch.1 out-of-scope no longer mentions payment (check the 3 lines after the label).
check "Ch.1 out-of-scope drops payment"           bash -c '! grep -A3 "Out of scope" chap_01.tex | grep -qi "payment"'
# Ch.2 backlog gains a payment user story (US36) and the counts stay consistent.
check "Ch.2 backlog has payment story US36"       present chap_02.tex 'US36 &.*pay'
check "Ch.2 analysis summary count = 36"          present chap_02.tex '36 user stories'
check "Ch.2 Sprint 3 row includes US36"           bash -c 'grep -q "Sprint 3.*US36" chap_02.tex'

# ----- summary -------------------------------------------------------------
section "Result"
printf '  %d passed, %d failed\n\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
