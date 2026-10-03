#!/usr/bin/env bash
# Exports the Markdown sources (technical sheet, working paper) to Word, PDF and LaTeX.
# Usage: scripts/export_docs.sh [output directory]   (default: private/exports, ignored by git)
# Requirements: pandoc; Google Chrome for the PDFs (headless printing of the HTML export).
# The .tex is meant to be compiled on Overleaf or with pdflatex (not installed here).
set -euo pipefail
OUT="${1:-private/exports}"; mkdir -p "$OUT"
PANDOC="${PANDOC:-$(command -v pandoc || echo /opt/anaconda3/bin/pandoc)}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
TMP="$(mktemp -d)"

docx() { "$PANDOC" --from gfm+smart "$1" -o "$OUT/$2.docx" --metadata lang="$3"; }
pdf()  {   # Markdown → standalone HTML with the print stylesheet → Chrome headless → PDF
  "$PANDOC" --from gfm+smart "$1" -o "$TMP/$2.html" --standalone --embed-resources --css scripts/doc.css --metadata title=" " --metadata lang="$3"
  if [ -x "$CHROME" ]; then
    # Chrome writes the PDF but does not always exit in headless mode on macOS: start it in the background,
    # wait for the file to be complete (size stable for 2 s), then stop the process. Fresh profile per call.
    rm -f "$OUT/$2.pdf"
    "$CHROME" --headless=new --disable-gpu --no-first-run --user-data-dir="$TMP/profile-$2" \
      --no-pdf-header-footer --print-to-pdf="$OUT/$2.pdf" "file://$TMP/$2.html" >/dev/null 2>&1 &
    local pid=$! last=-1 i=0
    while [ $i -lt 60 ]; do
      sleep 1; i=$((i + 1))
      if [ -s "$OUT/$2.pdf" ]; then
        size=$(stat -f %z "$OUT/$2.pdf"); if [ "$size" = "$last" ]; then break; fi; last=$size
      fi
    done
    kill "$pid" >/dev/null 2>&1 || true; wait "$pid" 2>/dev/null || true
    if [ -s "$OUT/$2.pdf" ]; then echo "pdf: $OUT/$2.pdf"; else echo "pdf failed for $2"; fi
  else
    echo "Chrome not found, no PDF for $2 (HTML kept in $TMP)"
  fi
}

docx docs/fr/FICHE_TECHNIQUE.md Fiche_technique_WAPP_DAM_Simulator fr
docx docs/TECHNICAL_SHEET.md     Technical_sheet_WAPP_DAM_Simulator en
pdf  docs/fr/FICHE_TECHNIQUE.md  Fiche_technique_WAPP_DAM_Simulator fr
pdf  docs/TECHNICAL_SHEET.md     Technical_sheet_WAPP_DAM_Simulator en

if [ -f private/paper/working_paper_draft.md ]; then
  docx private/paper/working_paper_draft.md working_paper_draft en
  pdf  private/paper/working_paper_draft.md working_paper_draft en
  # LaTeX: the body after the first horizontal rule (title, authors and status come from paper_meta.yaml)
  awk 'f{print} /^---$/{f=1}' private/paper/working_paper_draft.md > "$TMP/paper_body.md"
  "$PANDOC" --from markdown+smart "$TMP/paper_body.md" -o "$OUT/working_paper_draft.tex" --standalone \
    --metadata-file=private/paper/paper_meta.yaml --number-sections
  sed -i '' -E 's/\\section\{(Abstract|Résumé|References)\}/\\section*{\1}/; s/\\section\{Appendix /\\section*{Appendix /' "$OUT/working_paper_draft.tex"
fi
rm -rf "$TMP"
echo "exports written to $OUT"
