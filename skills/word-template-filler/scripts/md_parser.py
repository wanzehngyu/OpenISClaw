#!/usr/bin/env python3
"""
Markdown Paper Parser for Word Template Filler.
Extracts structured content (title, abstract, sections, paragraphs, tables) from a markdown paper.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TableData:
    headers: list[str]
    rows: list[list[str]]
    caption: str = ""


@dataclass
class SectionContent:
    text: Optional[str] = None
    table: Optional[TableData] = None

    def __repr__(self):
        if self.text is not None:
            return f"Para({self.text[:40]}...)" if len(self.text or "") > 40 else f"Para({self.text!r})"
        if self.table is not None:
            return f"Table({len(self.table.rows)} rows)"


@dataclass
class Section:
    level: int
    number: str
    title: str
    content: list[SectionContent] = field(default_factory=list)


@dataclass
class Paper:
    title: str = ""
    abstract: str = ""
    keywords: str = ""
    sections: list[Section] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


def _clean_markdown(text: str) -> str:
    """Remove bold/italic markers from markdown text."""
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text


def parse_markdown_paper(md_text: str) -> Paper:
    """Parse a markdown paper into a structured Paper object."""
    paper = Paper()
    lines = md_text.split("\n")

    # ── First pass: find title ──────────────────────────────────────────────
    for line in lines:
        if line.startswith("# ") and not paper.title:
            paper.title = line[2:].strip()
            paper.title = _clean_markdown(paper.title)
            break

    i = 0
    current_section: Optional[Section] = None
    current_paragraph_lines: list[str] = []
    abstract_collected = False

    def flush_paragraph():
        nonlocal current_paragraph_lines
        if current_paragraph_lines and current_section is not None:
            text = "\n".join(current_paragraph_lines).strip()
            if text:
                current_section.content.append(SectionContent(text=text))
            current_paragraph_lines = []

    def make_section_number(level: int) -> str:
        if level == 1:
            return str(len([s for s in paper.sections if s.level == 1]) + 1)
        elif level == 2:
            c1 = len([s for s in paper.sections if s.level == 1])
            c2 = len([s for s in paper.sections if s.level == 2]) + 1
            return f"{c1}.{c2}"
        elif level == 3:
            c1 = len([s for s in paper.sections if s.level == 1])
            c2 = len([s for s in paper.sections if s.level == 2])
            c3 = len([s for s in paper.sections if s.level == 3]) + 1
            return f"{c1}.{c2}.{c3}"
        else:
            prev = paper.sections[-1] if paper.sections else None
            base = prev.number if prev else "1"
            return f"{base}.{len([s for s in paper.sections if s.level == level]) + 1}"

    def collect_paragraph_until_next_heading(start_i: int) -> tuple[str, int]:
        """Collect lines as a paragraph until next heading or keywords marker. Returns (text, next_i)."""
        lines_out = []
        j = start_i
        while j < len(lines):
            l = lines[j].rstrip()
            if re.match(r"^#{1,4}\s+", l):
                break
            # Stop at keywords marker line (don't include it in abstract)
            if re.match(r"^\*\*关键词[：:]?\*\*", l):
                break
            if l.strip():
                lines_out.append(l.strip())
            j += 1
        return " ".join(lines_out), j

    def collect_table(start_i: int) -> tuple[Optional[TableData], int]:
        """Collect a markdown table starting at start_i. Returns (TableData, next_i)."""
        table_lines = []
        caption = ""
        j = start_i
        while j < len(lines):
            l = lines[j].strip()
            if l.startswith("|") and ("---" in l or l):
                if "---" not in l:
                    table_lines.append(l)
                j += 1
            elif re.match(r"^\*\*?Table", l, re.IGNORECASE) or "表" in l[:5]:
                caption = re.sub(r"^\*\*?Table:?\s*\*?\*?\s*", "", l).strip("* ")
                j += 1
            elif l.startswith("|") or l == "":
                if l:
                    table_lines.append(l)
                j += 1
            else:
                break
        if len(table_lines) >= 2:
            headers = [h.strip() for h in table_lines[0].split("|")[1:-1]]
            rows = []
            for row_l in table_lines[1:]:
                cells = [c.strip() for c in row_l.split("|")[1:-1]]
                if cells and any(c for c in cells):
                    rows.append(cells)
            if headers and rows:
                return TableData(headers=headers, rows=rows, caption=caption), j
        return None, start_i

    # ── Main parsing loop ───────────────────────────────────────────────────
    while i < len(lines):
        line = lines[i].rstrip()

        # Empty line
        if not line.strip():
            if current_paragraph_lines:
                current_paragraph_lines.append("")
            i += 1
            continue

        # Bold marker for abstract: **摘要** or **Abstract**
        bold_abstract = re.match(r"^\*\*摘要\*\*$", line, re.IGNORECASE)
        if bold_abstract and not abstract_collected:
            abstract_collected = True
            abstract_text, next_i = collect_paragraph_until_next_heading(i + 1)
            paper.abstract = _clean_markdown(abstract_text)
            # Check if next line is keywords (stopped at it)
            if next_i < len(lines):
                kw_line = lines[next_i].rstrip()
                kw_m = re.match(r"^\*\*关键词[：:]\*\*\s*(.*)$", kw_line)
                if kw_m:
                    paper.keywords = _clean_markdown(kw_m.group(1).strip())
                    next_i += 1
                elif re.match(r"^关键词[：:]", kw_line):
                    paper.keywords = _clean_markdown(re.sub(r"^关键词[：:]\s*", "", kw_line))
                    next_i += 1
            i = next_i
            continue

        # Bold marker for keywords: **关键词：** ...  or **关键词:**
        kw_match = re.match(r"^\*\*关键词[：:]\*\*\s*(.*)$", line)
        if kw_match:
            paper.keywords = _clean_markdown(kw_match.group(1).strip())
            i += 1
            continue

        # Also handle inline keywords without bold: 关键词：...
        if re.match(r"^关键词[：:]", line) and not paper.keywords:
            paper.keywords = _clean_markdown(re.sub(r"^关键词[：:]\s*", "", line))
            i += 1
            continue

        # Table (starts with |)
        if line.startswith("|") and "---" in line:
            table_data, next_i = collect_table(i)
            if table_data and current_section is not None:
                flush_paragraph()
                current_section.content.append(SectionContent(table=table_data))
            i = next_i
            continue

        # Heading: ## Section Title  or  ### Subsection
        heading_match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            title = _clean_markdown(title)

            # References section
            if "参考文献" in title or re.match(r"^references?$", title, re.IGNORECASE):
                flush_paragraph()
                i += 1
                paper.references = []
                while i < len(lines):
                    ref_line = lines[i].strip()
                    if ref_line and not ref_line.startswith("#"):
                        paper.references.append(ref_line)
                    elif ref_line.startswith("#"):
                        i -= 1
                        break
                    i += 1
                current_section = None
                i += 1
                continue

            # Skip abstract heading itself
            if re.match(r"^摘\s*要$", title, re.IGNORECASE) or title.lower() == "abstract":
                i += 1
                continue

            # Normal section
            flush_paragraph()
            sec_num = make_section_number(level)
            current_section = Section(level=level, number=sec_num, title=title)
            paper.sections.append(current_section)
            i += 1
            continue

        # Plain paragraph text
        if current_section is not None:
            current_paragraph_lines.append(line)
        i += 1

    flush_paragraph()
    return paper


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 md_parser.py <paper.md>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        paper = parse_markdown_paper(f.read())
    print(f"Title: {paper.title}")
    print(f"Abstract: {paper.abstract[:80]}...")
    print(f"Keywords: {paper.keywords}")
    print(f"Sections: {len(paper.sections)}")
    for s in paper.sections[:5]:
        print(f"  [{s.number}] {s.title} ({len(s.content)} items)")
    tables = sum(1 for s in paper.sections for c in s.content if c.table)
    print(f"Tables: {tables}")
    print(f"References: {len(paper.references)}")
