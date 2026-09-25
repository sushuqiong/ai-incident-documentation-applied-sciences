# -*- coding: utf-8 -*-
"""
Build Applied_Sciences_Article_Manuscript_v8.docx and .pdf from the markdown source.

Handles: H1/H2 headings, paragraphs, pipe tables, images with captions,
**bold** / *italic* inline markup, superscript author affiliations ([1] -> ¹),
and an MDPI-style page header with the year corrected to 2026.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "01_submission" / "Applied_Sciences_Article_Manuscript_v8.md"
OUT_DOCX = ROOT / "01_submission" / "Applied_Sciences_Article_Manuscript_v8.docx"

SUPER = {"1": "\u00b9", "2": "\u00b2", "3": "\u00b3", "4": "\u2074",
         "5": "\u2075", "6": "\u2076", "7": "\u2077", "8": "\u2078", "9": "\u2079"}

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def add_runs(par, text: str) -> None:
    """Render **bold** / *italic* inline markup into runs."""
    tokens = re.split(r"(\*\*.+?\*\*|\*[^*]+?\*)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            r = par.add_run(tok[2:-2])
            r.bold = True
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = par.add_run(tok[1:-1])
            r.italic = True
        else:
            par.add_run(tok)


def author_line(par, text: str) -> None:
    """Render 'Name* [n]' with the bracket number as superscript."""
    for token in re.split(r"(\[\d\])", text):
        if re.fullmatch(r"\[\d\]", token):
            r = par.add_run(SUPER[token[1]])
            r.font.superscript = True
        else:
            par.add_run(token)


def style_doc(doc: Document) -> None:
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.15

    for name, size, bold in (("Heading 1", 14, True), ("Heading 2", 12, True)):
        h = doc.styles[name]
        h.font.name = "Times New Roman"
        h.font.size = Pt(size)
        h.font.bold = bold
        h.font.color.rgb = RGBColor(0x1F, 0x1F, 0x1F)
        h.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Cm(2.2)
    sec.left_margin = sec.right_margin = Cm(2.2)

    # MDPI-style running header; year corrected from the template's 2025 (reviewer point 7)
    hdr = sec.header.paragraphs[0]
    hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = hdr.add_run("Appl. Sci. 2026, 16, x.  Template placeholder; volume and page numbers are set by MDPI.")
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor(0x60, 0x60, 0x60)


def add_table(doc, rows: list[list[str]]) -> None:
    tbl = doc.add_table(rows=len(rows), cols=len(rows[0]))
    tbl.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            c = tbl.cell(i, j)
            c.text = ""
            p = c.paragraphs[0]
            add_runs(p, cell)
            for r in p.runs:
                r.font.size = Pt(8.5)
                if i == 0:
                    r.bold = True


def build() -> Path:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    doc = Document()
    style_doc(doc)

    i = 0
    first_h1_done = False
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("# ") and not first_h1_done:            # title
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(ln[2:].strip())
            r.bold = True
            r.font.size = Pt(15)
            first_h1_done = True
            i += 1
            continue

        if ln.startswith("## "):
            doc.add_heading(ln[3:].strip(), level=2); i += 1; continue
        if ln.startswith("# "):
            doc.add_heading(ln[2:].strip(), level=1); i += 1; continue

        if ln.startswith("!["):                                   # image
            m = re.match(r"!\[(.*?)\]\((.*?)\)", ln)
            alt, path = m.group(1), m.group(2)
            img = (ROOT / "01_submission" / path).resolve()
            if not img.exists():
                img = (ROOT / path).resolve()
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(img), width=Cm(15.5))
            i += 1
            continue

        if ln.startswith("|"):                                    # table block
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in row):
                    block.append(row)
                i += 1
            add_table(doc, block)
            doc.add_paragraph()
            continue

        if ln.startswith("> "):                                   # block quote
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            add_runs(p, ln[2:].strip())
            for r in p.runs:
                r.italic = True
            i += 1
            continue

        if ln.strip():                                            # paragraph
            p = doc.add_paragraph()
            text = ln.strip()
            if text.startswith("Shuqiong Su") or text.startswith("\\*These"):
                author_line(p, text)
            else:
                add_runs(p, text)
            i += 1
            continue

        i += 1

    doc.save(OUT_DOCX)
    print("saved", OUT_DOCX, OUT_DOCX.stat().st_size, "bytes")
    return OUT_DOCX


def to_pdf(docx: Path) -> Path:
    soffice = next((p for p in SOFFICE_CANDIDATES if Path(p).exists()), None)
    if soffice is None:
        print("LibreOffice not found; PDF not generated.")
        return None
    out = ROOT / "01_submission"
    subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                    "--outdir", str(out), str(docx)], check=True,
                   capture_output=True, timeout=300)
    pdf = out / (docx.stem + ".pdf")
    print("saved", pdf, pdf.stat().st_size if pdf.exists() else "MISSING")
    return pdf


if __name__ == "__main__":
    d = build()
    to_pdf(d)
