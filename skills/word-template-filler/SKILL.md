---
name: word-template-filler
description: 将 Markdown 格式的论文内容填充到用户提供的 Word 模板（.docx/.dotx）中，生成格式规范的最终文档。用于：将已生成的 Markdown 论文转换为符合期刊格式的 Word/PDF；使用用户指定的模板（单栏/双栏、特定字体字号）；需要保持模板中的标题层级、段落样式、页眉页脚等格式时激活。触发词：「填充模板」「生成 Word 文档」「导出 PDF」「按照模板生成论文」。
metadata: {
  "openclaw": {
    "emoji": "📄",
    "requires": {
      "bins": ["python"],
      "os": ["linux", "darwin", "win32"],
      "python": ["docx", "lxml"]
    }
  }
}
---

# Word Template Filler

将 Markdown 论文填充到 Word 模板中，生成规范格式的最终文档。

## 安装与使用

本技能支持三种安装运行方式：

### 方式一：有 OpenClaw（推荐）

OpenClaw 用户直接通过命令安装：

```bash
openclaw skill install word-template-filler
```

OpenClaw 会自动检测并安装所需 pip 依赖。

### 方式二：纯 pip 安装（无 Docker / 无 OpenClaw）

安装 pip 依赖后，直接运行脚本：

```bash
# 安装依赖（核心计量包）
pip install pandas numpy scipy python-docx lxml

# 运行脚本
python skills/word-template-filler/scripts/filler.py --help
```

### 方式三：Docker 免安装（无需本地 Python 环境）

克隆项目后，用 Docker 运行 Agent Loop（自然语言交互）或 API Server：

```bash
git clone https://github.com/wanzehngyu/OpenISClaw.git
cd OpenISClaw
cp .env.example .env  # 编辑填入 OPENAI_API_KEY

# 对话式 Agent Loop（自然语言 → 自动分析）
make chat

# HTTP API 服务
make api-run
# 访问 http://localhost:8000 查看所有技能并发起分析
```

详见 [项目 README](https://github.com/wanzehngyu/OpenISClaw) 。


## 工作流程

### Step 1：准备模板

用户需要提供一个 `.docx` 或 `.dotx` 模板文件，模板中使用**占位符**标记需要填充的位置：

| 占位符 | 填充内容 |
|--------|---------|
| `{{TITLE}}` | 论文标题 |
| `{{ABSTRACT}}` | 摘要正文 |
| `{{KEYWORDS}}` | 关键词（用中文顿号分隔） |
| `{{SECTION:1}}` `{{SECTION:2}}` ... | 一级章节标题 |
| `{{SUBSECTION:2-1}}` `{{SUBSECTION:2-2}}` ... | 二级章节标题 |
| `{{PARAGRAPH:3-1}}` ... | 三级及以下章节 |
| `{{TABLE:1}}` `{{TABLE:2}}` ... | 表格（自动插入三线表） |
| `{{REF}}` | 参考文献列表 |

示例模板结构：
```
{{TITLE}}                    ← 标题位置（占位符本身可设为标题样式）
{{ABSTRACT}}                 ← 摘要段落
{{KEYWORDS}}                 ← 关键词
---
{{SECTION:1}}                ← 1 引言
{{PARAGRAPH:1-1}}            引言正文...
{{SECTION:2}}                ← 2 理论基础
{{PARAGRAPH:2-1}}            理论基础正文...
{{TABLE:1}}                  ← 表1占位符（替换为三线表）
{{PARAGRAPH:2-2}}            ...
{{SECTION:3}}                ← 3 研究假设
{{SUBSECTION:3-1}}           ← 3.1 假设1
{{PARAGRAPH:3-1-1}}          ...
{{REF}}                      ← 参考文献
```

> **提示**：在 Word 中创建模板时，将占位符本身的字符格式设置为你期望的样式（如"标题1"），脚本会自动将内容应用相同样式。

### Step 2：准备 Markdown 文件

Markdown 文件应包含论文完整内容，结构如下：
- `# 标题` → 论文标题
- `## 摘要` → 摘要（正文在 `## 摘要` 之后）
- `**关键词：** ...` → 关键词
- `## 章节标题` → 一级章节
- `### 子章节标题` → 二级章节
- `#### 子子章节` → 三级章节
- 表格格式：标准 Markdown 表格（含 caption）

脚本会自动识别并提取所有章节、段落和表格。

### Step 3：运行填充脚本

```bash
python3 scripts/filler.py \
  --template "模板.docx" \
  --paper "论文.md" \
  --output "输出.docx" \
  [--pdf]                     # 可选：同时生成 PDF（需 LibreOffice）
```

### Step 4：自动处理说明

**样式继承**：所有填充内容的样式自动继承占位符在模板中的字符格式。如果占位符使用了"标题1"样式，则填充内容自动应用该样式。

**表格处理**：Markdown 中的表格会被替换为符合学术规范的三线表（顶线、底线加粗，中间线细）。表注自动添加到表格下方。

**参考文献**：`{{REF}}` 会被替换为参考文献列表，每条以悬挂缩进格式呈现。

**PDF 生成**：使用 LibreOffice（`soffice`）进行格式转换，保留 Word 中的字体和布局。

## 依赖

```bash
pip install python-docx lxml
# PDF 转换（可选）
# macOS: brew install libreoffice
# Linux: sudo apt install libreoffice
```

## 脚本说明

- `scripts/filler.py` — 主脚本，完成全部填充和导出逻辑
- `scripts/md_parser.py` — 从 Markdown 论文中提取结构化内容
- `references/template-guide.md` — 模板制作详细指南
