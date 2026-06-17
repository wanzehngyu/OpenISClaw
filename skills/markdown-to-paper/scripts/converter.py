#!/usr/bin/env python3
"""
Main converter: Markdown → Word (.docx) or PDF
Supports custom reference templates for Word and .tex/.cls for PDF.
"""

import argparse
import os
import re
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from markdown_parser import parse_markdown


# ─────────────────────────────────────────────────────────────────────────────
# Word Document Generation (python-docx)
# ─────────────────────────────────────────────────────────────────────────────

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def set_cell_border_threeline(cell):
    """Apply three-line table borders to a cell."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "bottom", "left", "right"):
        border = OxmlElement(f"w:{edge}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "4")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "000000")
        tcBorders.append(border)
    tcPr.append(tcBorders)


def add_threeline_table(doc, table_data):
    """Add a three-line academic table to the Word document."""
    headers = table_data["headers"]
    rows = table_data["rows"]
    caption = table_data.get("caption", "")

    # Caption above table
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.space_before = Pt(4)
        cp.paragraph_format.space_after = Pt(2)
        run = cp.add_run(caption)
        run.bold = True
        run.font.size = Pt(9)

    n_cols = len(headers)
    table = doc.add_table(rows=len(rows) + 1, cols=n_cols)
    table.style = "Table Grid"

    # Header row
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = h
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(9)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_border_threeline(cell)

    # Data rows
    for r_idx, row in enumerate(rows):
        for j, cell_text in enumerate(row):
            if j < len(table.rows[r_idx + 1].cells):
                cell = table.rows[r_idx + 1].cells[j]
                cell.text = cell_text
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(9)
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER if j > 0 else WD_ALIGN_PARAGRAPH.LEFT
                set_cell_border_threeline(cell)

    # Make header top/bottom borders double-line
    for j in range(n_cols):
        tc = table.rows[0].cells[j]._tc
        tcPr = tc.get_or_add_tcPr()
        tcBorders = OxmlElement("w:tcBorders")
        for edge in ("top", "bottom"):
            border = OxmlElement(f"w:{edge}")
            border.set(qn("w:val"), "double")
            border.set(qn("w:sz"), "6")
            border.set(qn("w:space"), "0")
            border.set(qn("w:color"), "000000")
            tcBorders.append(border)
        tcPr.append(tcBorders)

    doc.add_paragraph()


def render_text_paragraph(doc, text):
    """Add a text paragraph with basic markdown formatting."""
    if not text.strip():
        return
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    # Handle bold and italic
    segments = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text)
    for seg in segments:
        if seg.startswith("**") and seg.endswith("**"):
            run = p.add_run(seg[2:-2])
            run.bold = True
        elif seg.startswith("*") and seg.endswith("*") and not seg.startswith("**"):
            run = p.add_run(seg[1:-1])
            run.italic = True
        else:
            p.add_run(seg)


def markdown_to_docx(md_text, output_path, ref_template=None):
    """Convert markdown paper to formatted Word document."""
    if not HAS_DOCX:
        raise ImportError("python-docx not installed. Run: pip install python-docx")

    paper = parse_markdown(md_text)
    doc = Document()

    # Page setup: A4, standard margins
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3.18)
    section.right_margin = Cm(3.18)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)

    # Default font
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)

    # Title
    title_text = paper.title or "论文标题"
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tp.paragraph_format.space_before = Pt(0)
    tp.paragraph_format.space_after = Pt(12)
    run = tp.add_run(title_text)
    run.bold = True
    run.font.size = Pt(16)
    run.font.name = "Times New Roman"

    # Abstract
    if paper.abstract:
        ap = doc.add_paragraph()
        ap.paragraph_format.space_before = Pt(6)
        ap.paragraph_format.space_after = Pt(6)
        run = ap.add_run("摘要　")
        run.bold = True
        ap.add_run(paper.abstract)

    if paper.keywords:
        kp = doc.add_paragraph()
        kp.paragraph_format.space_after = Pt(12)
        run = kp.add_run("关键词：")
        run.bold = True
        kp.add_run(paper.keywords)

    # Horizontal divider
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "auto")
    pBdr.append(bottom)
    pPr.append(pBdr)

    doc.add_paragraph()

    # Sections
    for section_data in paper.sections:
        level = section_data.level
        title = section_data.title

        if level == 1:
            hp = doc.add_heading(title, level=1)
            for run in hp.runs:
                run.font.size = Pt(14)
                run.bold = True
        elif level == 2:
            hp = doc.add_heading(title, level=2)
            for run in hp.runs:
                run.font.size = Pt(12)
                run.bold = True
        elif level == 3:
            hp = doc.add_heading(title, level=3)
            for run in hp.runs:
                run.bold = True
        else:
            hp = doc.add_heading(title, level=4)
            for run in hp.runs:
                run.bold = True

        for item in section_data.content:
            if hasattr(item, "headers"):  # Table object
                add_threeline_table(doc, {
                    "headers": item.headers,
                    "rows": item.rows,
                    "caption": item.caption
                })
            elif isinstance(item, str):
                render_text_paragraph(doc, item)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, str):
                        render_text_paragraph(doc, sub)

    # References
    if paper.references:
        doc.add_heading("参考文献", level=1)
        for ref in paper.references:
            p = doc.add_paragraph()
            p.paragraph_format.first_line_indent = Cm(-0.74)
            p.paragraph_format.left_indent = Cm(0.74)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(ref)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)

    doc.save(output_path)
    print(f"[OK] Word document saved: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# LaTeX / PDF Generation
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_LATEX_TEMPLATE = r"""\documentclass[12pt,a4paper,oneside]{article}

%% Packages
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{times}
\usepackage{geometry}
\geometry{top=2.54cm,bottom=2.54cm,left=3.18cm,right=3.18cm}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{graphicfix}\n\usepackage{xeCJK}\n\setCJKmainfont{SimSun}
\usepackage[colorlinks=true,linkcolor=black]{hyperref}

%% Paragraph formatting
\setlength{\parindent}{2em}
\setlength{\parskip}{6pt}
\linespread{1.5}

%% Abstract environment
% Abstract (plain)

\begin{document}

%% Body (populated by converter.py)
__BODY__

\end{document}
"""


def escape_latex(text):
    """Escape special LaTeX characters."""
    if not text:
        return ""
    text = str(text)
    for char, replacement in [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
        ("\\", r"\textbackslash{}"),
    ]:
        text = text.replace(char, replacement)
    return text


def md_to_latex_text(text):
    """Convert markdown inline formatting to LaTeX."""
    text = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"\*([^*]+)\*", r"\\textit{\1}", text)
    return text


def table_to_latex(table_data):
    """Convert table data to LaTeX three-line table."""
    headers = table_data["headers"]
    rows = table_data["rows"]
    caption = table_data.get("caption", "")

    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"  \centering")
    n_cols = len(headers)
    lines.append(r"  \begin{tabular}{" + "c" * n_cols + "}")
    lines.append(r"    \toprule")
    lines.append("    " + " & ".join(escape_latex(h) for h in headers) + r" \\")
    lines.append(r"    \midrule")
    for row in rows:
        lines.append("    " + " & ".join(escape_latex(str(c)) for c in row) + r" \\")
    lines.append(r"    \bottomrule")
    lines.append(r"  \end{tabular}")
    if caption:
        lines.append(r"  \caption{" + escape_latex(caption) + "}")
    lines.append(r"\end{table}")
    return "\n".join(lines)


def paper_to_latex(paper, template=None):
    """Convert parsed Paper to LaTeX document string."""
    if template is None:
        template = DEFAULT_LATEX_TEMPLATE

    body_parts = []

    # Title and abstract
    if paper.title:
        body_parts.append(r"\title{" + escape_latex(paper.title) + "}")
        body_parts.append(r"\maketitle")

    if paper.abstract:
        body_parts.append(r"")
        body_parts.append(paper.abstract)
        body_parts.append(r"")

    if paper.keywords:
        body_parts.append(r"\paragraph*{关键词：}" + paper.keywords)

    body_parts.append(r"\newpage")

    # Sections
    for section_data in paper.sections:
        level = section_data.level
        title = section_data.title
        sec_cmd = {1: "section", 2: "subsection", 3: "subsubsection"}.get(level, "paragraph")
        body_parts.append(r"\{0}{{{1}}}".format(sec_cmd, escape_latex(title)))

        for item in section_data.content:
            if hasattr(item, "headers"):
                body_parts.append(table_to_latex({
                    "headers": item.headers,
                    "rows": item.rows,
                    "caption": item.caption
                }))
                body_parts.append("")
            elif isinstance(item, str):
                body_parts.append(md_to_latex_text(item))
                body_parts.append("")
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, str):
                        body_parts.append(md_to_latex_text(sub))
                body_parts.append("")

    # References
    if paper.references:
        body_parts.append(r"\newpage")
        body_parts.append(r"\section*{参考文献}")
        for ref in paper.references:
            escaped_ref = escape_latex(ref)
            body_parts.append(r"\par\noindent\hskip2em\relax " + escaped_ref)

    body = "\n\n".join(body_parts)
    tex = template.replace("__BODY__", body)
    return tex


def compile_latex_to_pdf(tex_path, output_dir):
    """Compile LaTeX to PDF using pdflatex (3 passes)."""
    basename = os.path.splitext(os.path.basename(tex_path))[0]
    pdf_path = os.path.join(output_dir, basename + ".pdf")

    for pass_num in range(3):
        cmd = [
            "xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={output_dir}",
            tex_path
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            errors = [l for l in result.stderr.split("\n") if l.strip() and "Error" in l.upper() or "!" in l]
            if errors[:5]:
                print(f"[WARN] pdflatex pass {pass_num+1}: " + "; ".join(errors[:3]))

    if os.path.exists(pdf_path):
        print(f"[OK] PDF saved: {pdf_path}")
        return pdf_path
    raise RuntimeError(f"PDF not found after compilation. Check LaTeX errors above.")


def markdown_to_pdf(md_text, output_path, template_tex=None):
    """Convert markdown paper to PDF via LaTeX."""
    paper = parse_markdown(md_text)

    if template_tex and os.path.exists(template_tex):
        with open(template_tex, "r", encoding="utf-8") as f:
            template = f.read()
        print(f"[INFO] Using custom LaTeX template: {template_tex}")
    else:
        template = DEFAULT_LATEX_TEMPLATE
        print("[INFO] Using default LaTeX template")

    tex_content = paper_to_latex(paper, template)

    tex_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    tex_path = os.path.join(tex_dir, os.path.splitext(os.path.basename(output_path))[0] + ".tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)
    print(f"[INFO] LaTeX file written: {tex_path}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_tex = os.path.join(tmp_dir, os.path.basename(tex_path))
        shutil.copy(tex_path, tmp_tex)
        pdf_path = compile_latex_to_pdf(tmp_tex, tmp_dir)
        shutil.copy(pdf_path, output_path)

    print(f"[OK] PDF saved: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Convert Markdown paper to Word or PDF")
    parser.add_argument("--input", required=True, help="Input markdown file path")
    parser.add_argument("--output_format", required=True, choices=["docx", "pdf"],
                        help="Output format: docx or pdf")
    parser.add_argument("--output", required=True, help="Output file path (with extension)")
    parser.add_argument("--reference", help="Path to reference .docx template (for Word output)")
    parser.add_argument("--template", help="Path to custom LaTeX template .tex (for PDF output)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        md_text = f.read()

    if args.output_format == "docx":
        markdown_to_docx(md_text, args.output, ref_template=args.reference)
    elif args.output_format == "pdf":
        markdown_to_pdf(md_text, args.output, template_tex=args.template)
    else:
        print(f"[ERROR] Unknown format: {args.output_format}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
