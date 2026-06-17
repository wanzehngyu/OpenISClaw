"""
Markdown Parser for Academic Paper Conversion
Handles standard markdown with YAML front matter, as well as plain-text headers.
"""

import re
import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Table:
    headers: List[str]
    rows: List[List[str]]
    caption: str = ""


@dataclass
class Section:
    level: int  # 1 = #, 2 = ##, etc.
    title: str
    content: List[Any] = field(default_factory=list)  # str (text) or Table or dict


@dataclass
class Paper:
    title: str = ""
    authors: str = ""
    abstract: str = ""
    keywords: str = ""
    sections: List[Section] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


def parse_front_matter(lines: List[str]) -> tuple[Dict[str, Any], List[str]]:
    """Parse YAML front matter from markdown lines."""
    if not lines or lines[0].strip() != "---":
        return {}, lines
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx is not None:
        try:
            meta = yaml.safe_load("\n".join(lines[1:end_idx]))
            return meta or {}, lines[end_idx + 1:]
        except yaml.YAMLError:
            return {}, lines[1:]
    return {}, lines


def is_separator(line: str) -> bool:
    """Check if a line is a markdown table separator |---|...|."""
    return bool(re.match(r'^\|[\s\-:|#]+\|$', line.strip()))


def parse_markdown_table(lines: List[str], start_idx: int) -> tuple[Table, int]:
    """Parse a markdown table at start_idx. Returns (Table, next_idx)."""
    header_line = lines[start_idx].strip().strip("|")
    headers = [h.strip() for h in header_line.split("|")]

    i = start_idx + 1
    while i < len(lines) and is_separator(lines[i]):
        i += 1

    rows = []
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#") or is_separator(line):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        if any(cells):
            rows.append(cells)
        i += 1

    return Table(headers=headers, rows=rows), i


def extract_caption_before(lines: List[str], before_idx: int) -> str:
    """Look backward from before_idx to find a caption line."""
    for j in range(before_idx - 1, max(0, before_idx - 4), -1):
        line = lines[j].strip()
        if not line:
            continue
        if is_separator(line) or line.startswith("|"):
            continue
        cleaned = re.sub(r'\*+', '', line).strip()
        if re.match(r'^(#{1,6}\s|\*\*?[^*]+\*\*?|\d+\.)', line):
            continue
        if len(cleaned) > 3:
            return cleaned
    return ""


def parse_reference_list(lines: List[str], start_idx: int) -> tuple[List[str], int]:
    """Parse numbered reference list starting at start_idx."""
    refs = []
    i = start_idx
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        m = re.match(r'^\[?(\d+)\]?[\.\)]\s+(.+)', line)
        if m:
            refs.append(m.group(2).strip())
        else:
            if refs and line and not line.startswith("#"):
                refs[-1] += " " + line
        i += 1
    return refs, i


def parse_markdown(text: str) -> Paper:
    """
    Parse a markdown paper into a structured Paper object.
    Handles both YAML front matter format and plain markdown with # Title header.
    """
    paper = Paper()
    raw_lines = text.split("\n")
    lines = raw_lines

    # ── 1. Front matter ─────────────────────────────────────────────────────
    meta, after_fm = parse_front_matter(lines)
    if meta:
        paper.title = meta.get("title", "")
        paper.authors = meta.get("author", meta.get("authors", ""))
        paper.abstract = meta.get("abstract", "")
        paper.keywords = meta.get("keywords", "")
        lines = after_fm

    # ── 2. Title (if no YAML front matter) ─────────────────────────────────
    if not paper.title:
        for i, line in enumerate(lines[:10]):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("##"):
                paper.title = stripped.lstrip("# ").strip()
                lines = lines[i + 1:]
                break

    # ── 3. Abstract ─────────────────────────────────────────────────────────
    abs_start = None
    kw_end = None
    for i, line in enumerate(lines):
        ls = line.strip()
        if re.match(r'^##?\s*摘要', ls) or re.match(r'^\*?\*?摘要\*?\*?$', ls) or re.match(r'^##?\s*Abstract\b', ls, re.IGNORECASE):
            abs_start = i + 1
        elif abs_start and (ls.startswith("---") or ls.startswith("***")):
            kw_end = i
            break
        elif abs_start and kw_end is None and (ls.startswith("##") or ls.startswith("# ")):
            kw_end = i
            break

    if abs_start:
        abs_lines = []
        i = abs_start
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("---") or line.startswith("**关键词") or \
               re.match(r'^##?\s*关键词', line) or \
               (kw_end and i == kw_end):
                break
            if line and not line.startswith("##") and not line.startswith("# "):
                clean = re.sub(r'\*+', '', line).strip()
                if clean:
                    abs_lines.append(clean)
            i += 1
        if not paper.abstract:
            paper.abstract = " ".join(abs_lines).strip()

    # ── 4. Keywords ─────────────────────────────────────────────────────────
    kw_start = None
    for i, line in enumerate(lines):
        ls = line.strip()
        if re.match(r'\*\*关键词', ls) or re.match(r'^##?\s*关键词', ls):
            kw_start = i
            break

    if kw_start:
        kw_line = lines[kw_start].strip()
        kw_clean = re.sub(r'\*+', '', kw_line).strip()
        kw_clean = re.sub(r'^关键词[：:\s]*', '', kw_clean)
        if not paper.keywords:
            paper.keywords = kw_clean
        lines = lines[kw_start + 1:]

    # Remove leading horizontal rules
    while lines and (not lines[0].strip() or lines[0].strip() in ("---", "***")):
        lines.pop(0)

    # ── 5. Sections ─────────────────────────────────────────────────────────
    current_section: Optional[Section] = None
    current_content: List[Any] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # References
        if "参考文献" in line or re.match(r'^#{1,3}\s*参考文献', line) or \
           re.match(r'^#{1,3}\s*References', line, re.IGNORECASE):
            if current_section:
                current_section.content = current_content
                paper.sections.append(current_section)
            refs, _ = parse_reference_list(lines, i + 1)
            paper.references = refs
            break

        # Section heading
        sec_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if sec_match:
            if current_section:
                current_section.content = current_content
                paper.sections.append(current_section)
            level = len(sec_match.group(1))
            title = sec_match.group(2).strip()
            current_section = Section(level=level, title=title)
            current_content = []
            i += 1
            continue

        # Table
        if line.startswith("|") and "|" in line:
            if i + 1 < len(lines) and is_separator(lines[i + 1]):
                caption = extract_caption_before(lines, i)
                table, next_i = parse_markdown_table(lines, i)
                table.caption = caption
                current_content.append(table)
                i = next_i
                continue

        # Regular paragraph
        if line:
            current_content.append(line)

        i += 1

    if current_section:
        current_section.content = current_content
        paper.sections.append(current_section)

    return paper


def paper_to_dict(paper: Paper) -> Dict[str, Any]:
    """Serialize Paper to dict."""
    def ser_content(item):
        if isinstance(item, Table):
            return {"type": "table", "data": {
                "headers": item.headers,
                "rows": item.rows,
                "caption": item.caption
            }}
        elif isinstance(item, dict) and item.get("type") == "table":
            return item
        return {"type": "text", "data": item}

    return {
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "keywords": paper.keywords,
        "sections": [
            {
                "level": s.level,
                "title": s.title,
                "content": [ser_content(item) for item in s.content]
            }
            for s in paper.sections
        ],
        "references": paper.references
    }
