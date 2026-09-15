#!/usr/bin/env bash
set -uo pipefail
TEX="${1:-article_06082026.tex}"
BASE="${TEX%.tex}"
fail=0

echo "== 1. placeholder tokens in $TEX =="
if grep -nE '\[VALUE\]|\\val\{|\[REPLACE\]|\bTBD\b|\bTODO\b|XXX|ILLUSTRATIVE|dummy data|placeholder' "$TEX"; then
  echo "   FAIL: unfilled placeholder(s) above"; fail=1
else
  echo "   ok: none found"
fi

echo "== 2. unresolved ?? in the compiled PDF =="
if [ -f "$BASE.pdf" ]; then
  if command -v pdftotext >/dev/null && pdftotext "$BASE.pdf" - 2>/dev/null | grep -n '??'; then
    echo "   FAIL: '??' in the PDF -- run pdflatex/bibtex/pdflatex/pdflatex again"; fail=1
  else
    echo "   ok: no '??'"
  fi
else
  echo "   skipped: $BASE.pdf not built"
fi

echo "== 3. undefined references and citations in the log =="
if [ -f "$BASE.log" ]; then
  if grep -n 'undefined on input\|Citation .* undefined' "$BASE.log"; then
    echo "   FAIL: undefined reference(s)/citation(s) above"; fail=1
  else
    echo "   ok: none"
  fi
else
  echo "   skipped: $BASE.log not found"
fi

echo "== 4. blue mark-up still present (revision must stay visible) =="
n=$(grep -c 'textcolor{blue}' "$TEX" || true)
echo "   $n blue-marked change(s)"
[ "$n" -eq 0 ] && { echo "   FAIL: no blue mark-up"; fail=1; }

echo
[ "$fail" -eq 0 ] && echo "ALL CHECKS PASSED" || echo "CHECKS FAILED -- do not resubmit"
exit "$fail"
