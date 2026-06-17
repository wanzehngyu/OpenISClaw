---
name: markdown-to-paper
description: 面向已有完整Markdown格式论文草稿的研究者，将markdown文件转换为符合学术期刊格式规范的Word(.docx)或PDF文档。支持用户上传自定义Word模板文件以精确控制字体、字号、页边距、单双栏等格式；PDF输出基于LaTeX，可指定 cls 格式文件和编译选项。对于没有模板的用户，提供默认IS期刊格式（单栏，Times New Roman 12pt）。技能读取markdown论文内容和表格数据，自动生成标题、摘要、章节、脚注、参考文献和三线表。触发词："生成Word"、"生成PDF"、"输出论文"、"导出Word"、"导出PDF"、"格式转换"、"markdown转Word"、"markdown转PDF"。
metadata: {
  "openclaw": {
    "emoji": "📄",
    "requires": {
      "bins": ["python"],
      "os": ["linux", "darwin", "win32"]
    }
  }
}
---

# Markdown-to-Paper: 学术论文格式输出技能

## 概述

用户在完成论文草稿（Markdown格式）后，需要将其转换为符合期刊投稿格式的 Word 或 PDF 文档。本技能提供两种输出路径：

- **Word (.docx)**：调用 `python-docx`，读取用户提供的 `.docx` 格式参考模板（reference document），将 Markdown 内容注入模板样式，生成格式一致的 Word 文档。
- **PDF**：将 Markdown 解析为 LaTeX 格式，调用 `pdflatex` 编译生成 PDF，支持用户指定 `.cls` 格式文件和自定义导言区（preamble）。

```
用户: 已有 markdown 论文草稿，希望生成符合期刊格式的 Word 或 PDF
  │
  ▼
markdown-to-paper（本技能）
  │
  ├─→ [Word路径] python-docx + reference.docx 模板
  │     输入：markdown + reference.docx（可选）
  │     输出：formatted.docx
  │
  └─→ [PDF路径] Markdown → LaTeX → pdflatex
        输入：markdown + template.tex/.cls（可选）
        输出：formatted.pdf
```

## 技能架构

```
markdown-to-paper/
├── SKILL.md（本文档）
├── scripts/
│   ├── converter.py              # 主转换器（Word + PDF）
│   └── markdown_parser.py        # Markdown 解析引擎
└── references/
    ├── default_latex_template.tex # 默认 LaTeX 模板（单栏，12pt）
    └── template_config.yaml       # 格式配置文件
```

## 输入与输出

| 输入 | 类型 | 说明 |
|------|------|------|
| `markdown_file` | `.md` 文件路径 | 必填，论文草稿的 Markdown 内容 |
| `reference_docx` | `.docx` 文件路径 | 可选，用户提供的 Word 格式模板 |
| `template_tex` | `.tex/.cls` 文件路径 | 可选，LaTeX 格式模板 |
| `format_config` | `.yaml` 文件路径 | 可选，格式配置文件（字体/栏/边距等） |
| `output_format` | `docx` 或 `pdf` | 必填，输出格式 |

| 输出 | 类型 | 说明 |
|------|------|------|
| `output_file` | `.docx` 或 `.pdf` | 生成的格式化论文文档 |

## 使用方式

### 方式一：通过 skill-writer 联动（自动）

当 `paper-writer` 技能完成论文生成后，可直接调用本技能导出格式化文档：

```bash
python skills/markdown-to-paper/scripts/converter.py \
  --input "./output/paper.md" \
  --output_format "docx" \
  --reference "./templates/reference_ MISQ.docx" \
  --output "./output/paper_formatted.docx"
```

### 方式二：独立使用

```bash
# 生成 Word（使用用户模板）
python skills/markdown-to-paper/scripts/converter.py \
  --input "./paper.md" \
  --output_format "docx" \
  --reference "./my_template.docx" \
  --output "./paper.docx"

# 生成 PDF（使用用户 LaTeX 模板）
python skills/markdown-to-paper/scripts/converter.py \
  --input "./paper.md" \
  --output_format "pdf" \
  --template "./my_template.tex" \
  --output "./paper.pdf"

# 生成 PDF（无模板，使用默认 IS 期刊格式）
python skills/markdown-to-paper/scripts/converter.py \
  --input "./paper.md" \
  --output_format "pdf" \
  --output "./paper.pdf"
```

## converter.py 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入的 Markdown 文件路径 |
| `--output_format` | 是 | 输出格式：`docx` 或 `pdf` |
| `--output` | 是 | 输出文件路径（含扩展名） |
| `--reference` | 否（Word用） | 用户提供的 `.docx` 参考模板路径 |
| `--template` | 否（PDF用） | 用户提供的 LaTeX 模板（`.tex` 或 `.cls`） |
| `--format_config` | 否 | 格式配置文件（`.yaml`），覆盖默认设置 |
| `--latex_preamble` | 否 | 自定义 LaTeX 导言区（字符串） |

## converter.py 功能说明

### Markdown 解析引擎（markdown_parser.py）

将 Markdown 内容解析为结构化数据：

1. **元数据提取**：从 Markdown 文件开头的 YAML front matter 或自然文本中提取标题、作者、摘要、关键词
2. **章节结构解析**：识别 `# 一级标题`、`## 二级标题` 等，生成文档大纲
3. **表格识别与解析**：识别 `| 表头 | ... |` 格式的 Markdown 表格，提取行列数据和表题
4. **强调和特殊格式**：识别 `**粗体**`、`*斜体*`、脚注 `[^n]` 等
5. **参考文献识别**：识别以 `## 参考文献` 或 `# References` 开头的章节
6. **数学公式识别**：识别 `$inline$` 和 `$$block$$` 格式的 LaTeX 数学公式

### Word 文档生成（python-docx）

Word 路径的转换流程：

1. **加载模板**：读取用户提供的 `reference.docx`，提取其样式（标题1-3、正文、表格样式等）
2. **构建文档树**：将解析后的 Markdown 结构注入 Word 文档，按模板样式分配格式
3. **生成标题**：根据 Markdown 的 `#` 层级映射到 Word 的 Heading 1/2/3 样式
4. **生成正文段落**：保留粗体/斜体，按模板规定的正文字体和字号输出
5. **生成表格**：读取 Markdown 表格数据，在 Word 中重建三线表（含表题），表题位于表格上方
6. **插入分页**：在摘要之后、正文第一章之前自动插入分页符
7. **处理参考文献**：参考文献节使用正文样式（首行缩进格式）

### PDF 文档生成（LaTeX + pdflatex）

PDF 路径的转换流程：

1. **加载模板**：若用户提供了 `.tex` 或 `.cls` 文件，使用用户模板；否则使用默认 `default_latex_template.tex`
2. **生成 LaTeX 文档**：
   - 写入文档类（`\documentclass{article}` 或用户的模板）
   - 写入导言区（宏包、字体设置、页边距等）
   - 将 Markdown 章节转写为 LaTeX 章节命令
   - 将 Markdown 表格转写为 `booktabs` 三线表格式
   - 将 Markdown 公式转写为 LaTeX 数学环境
   - 将参考文献转写为 `thebibliography` 环境
3. **编译 PDF**：执行 `pdflatex → biber/pdflatex → pdflatex`（三遍编译）确保交叉引用和文献索引正确
4. **输出 PDF**：将生成的 PDF 文件复制到输出路径

## 格式规范

### 默认 Word 格式（无模板时）

- 页面：A4
- 页边距：上下 2.54cm，左右 3.18cm
- 正文：Times New Roman 12pt，1.5倍行距
- 标题1（章）：Times New Roman 16pt，加粗
- 标题2（节）：Times New Roman 14pt，加粗
- 标题3（小节）：Times New Roman 12pt，加粗
- 摘要：正文格式，首行不缩进，"**摘要**"加粗
- 表格：黑细边框+表头双线，表题在表格上方，五号 Times New Roman
- 参考文献：正文格式，首行悬挂缩进

### 默认 LaTeX 格式（无模板时）

- 文档类：`\documentclass[12pt,a4paper,oneside]{article}`
- 字体：Times New Roman（`\usepackage{times}`）
- 页面：oneside，上下 2.54cm，左右 3.18cm
- 标题：居中加粗
- 摘要：`\begin{abstract}...\end{abstract}` 环境
- 表格：`\begin{table}\begin{tabular}...\end{tabular}\end{table}`，使用 `booktabs` 宏包（三线表）
- 数学：`\(inline\)` 和 `\[displayed\]` 环境
- 参考文献：`thebibliography` 环境，plain 样式

## 与其他技能的联动

| 上游技能 | 输出内容 | 本技能接收方式 |
|---------|---------|--------------|
| `paper-writer` | `.md` 论文草稿 | 通过 `--input` 参数传入 |
| 用户直接上传 | 已有 `.md` 文件 | 通过 `--input` 参数传入 |

## 限制与边界

1. **表格支持**：仅支持标准 Markdown pipe table 格式（`| col1 | col2 |`）；复杂合并单元格暂不支持
2. **公式支持**：PDF 路径原生支持 LaTeX 数学公式；Word 路径需 Word 2016+ 支持墨迹公式渲染
3. **图片支持**：Markdown 中的 `![alt](path)` 图片引用暂不自动嵌入，Word/PDF 中以占位符替代
4. **参考文献格式**：默认输出为未格式化的 plain 列表，期刊特定引用格式（如 APA、MLA）需额外配置
5. **LaTeX 模板依赖**：`pdflatex` 编译需要系统中已安装 TeX Live 或等价发行版

## 安装依赖

```bash
# Python 包（建议使用 venv）
python3 -m venv venv
source venv/bin/activate
pip install python-docx pyyaml

# LaTeX（macOS，已安装 TeX Live）
# pandoc（用于 Word 路径的备选方案，若 python-docx 格式支持不足时可启用）
brew install pandoc
```

## 学术引用

若在学术研究中使用本技能辅助论文格式输出，建议引用：

> 万院士 (2026). Markdown-to-Paper: IS 实证论文格式输出技能. GitHub Repository.
