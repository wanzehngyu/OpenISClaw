# OpenISClaw Web UI — TensorBoard-Style Econometrics Dashboard

## 1. Concept & Vision

A local-first, browser-based workbench for IS-Econometrics that feels like opening a research tool built by economists who care about UX. Think TensorBoard meets JupyterLab — structured enough for serious work, approachable enough that an IS PhD student won't rage-quit after 5 minutes. The interface should convey rigor (LaTeX tables, publication-quality plots) while hiding the terminal underneath.

**Core metaphor:** A lab notebook that runs itself. You bring data, ask questions in plain Chinese, get publication-ready results.

---

## 2. Design Language

**Aesthetic:** Academic dark mode — deep navy backgrounds, crisp white text, accent colors borrowed from academic publishing (IEEE blue, Elsevier orange). Feels like Overleaf meets a Bloomberg terminal.

**Color Palette:**
- Background: `#0f172a` (slate-900)
- Surface: `#1e293b` (slate-800)
- Border: `#334155` (slate-700)
- Primary: `#3b82f6` (blue-500) — buttons, active states
- Accent: `#f97316` (orange-500) — highlights, running states
- Success: `#22c55e` (green-500)
- Warning: `#eab308` (yellow-500)
- Text primary: `#f1f5f9` (slate-100)
- Text secondary: `#94a3b8` (slate-400)
- Code/Mono: `#e879f9` (fuchsia-400)

**Typography:**
- UI: `Inter` (clean, readable)
- Chinese: `Noto Sans SC`
- Code/Results: `JetBrains Mono` or `Fira Code`
- Fallback: system-ui, monospace

**Spatial System:**
- 4px base unit, 8px grid
- Sidebar: 240px fixed width
- Content area: fluid, max 1400px
- Card padding: 20px
- Section gaps: 24px

**Motion:**
- Transitions: 150ms ease for micro-interactions, 300ms for panel changes
- Loading states: subtle pulse animation (not spinners)
- Results appear: fade + slide-up 200ms

---

## 3. Layout & Structure

```
┌──────────────────────────────────────────────────────────────┐
│  TOPBAR: Logo | Project Name | Status Indicators | Settings  │
├────────────┬─────────────────────────────────────────────────┤
│            │                                                  │
│  SIDEBAR   │              MAIN CONTENT AREA                  │
│  240px     │                                                  │
│            │  ┌────────────────────────────────────────────┐  │
│  ○ 仪表盘  │  │  Page content (Dashboard / Skill panels)  │  │
│  ○ 数据    │  │                                            │  │
│  ○ 对话    │  │                                            │  │
│  ○ 面板回归│  │                                            │  │
│  ○ IV      │  └────────────────────────────────────────────┘  │
│  ○ DID     │                                                  │
│  ○ PSM     │  ┌────────────────────────────────────────────┐  │
│  ○ 论文    │  │  RESULTS PANEL (collapsible, bottom)       │  │
│  ○ 表格    │  │  Tables | Plots | Logs                      │  │
│  ○ 技能库  │  └────────────────────────────────────────────┘  │
│            │                                                  │
├────────────┴─────────────────────────────────────────────────┤
│  STATUS BAR: API status | Data loaded | Last run | GPU/CPU    │
└──────────────────────────────────────────────────────────────┘
```

**Pages:**
1. **仪表盘 (Dashboard)** — Overview: datasets, recent analyses, quick actions
2. **数据 (Data)** — Upload, preview, variable inspector, data quality report
3. **对话 (Chat)** — LLM-powered natural language interface (agent-loop)
4. **面板回归 (Panel Regression)** — TWFE form-based interface
5. **IV 估计 (IV Estimator)** — 2SLS interface with diagnostics
6. **多时点 DID (Staggered DID)** — Event study + CS estimator
7. **倾向得分匹配 (PSM)** — Propensity score interface
8. **论文写作 (Paper Writer)** — Full paper generation workflow
9. **结果 (Results)** — All generated tables, plots, logs
10. **技能库 (Skills)** — Browse + configure all 18 skills

---

## 4. Features & Interactions

### 4.1 Dashboard
- **Dataset cards:** Show name, rows × cols, file type, last modified. Click to load into current session.
- **Recent analyses:** List of past runs with timestamp, skill used, key result snippet (e.g., "β=0.34***").
- **Quick actions:** "上传数据", "新建分析", "查看结果" large buttons.
- **System health:** API connection status, dependency check, model in use.

### 4.2 Data Panel
- **Upload zone:** Drag-and-drop or click upload. Supports .csv, .dta, .xlsx. Shows upload progress.
- **Data preview:** First 100 rows, column headers colored by type (numeric vs string vs date). Click column header for stats (mean, sd, n, missing%).
- **Variable inspector:** Select variable → shows distribution histogram, summary stats, missing rate.
- **Data quality badge:** Green/Yellow/Red indicators for each column based on missing %, outliers.

### 4.3 Chat Interface
- **Message input:** Text area with placeholder "用自然语言描述你的分析需求...". Submit on Enter (Shift+Enter for newline).
- **Streaming response:** LLM reply streams in token by token, shown with blinking cursor.
- **Script preview:** When LLM recommends a command, show it in a code block with "▶ 执行" and "✏️ 编辑" buttons.
- **Execution output:** Stdout/stderr appear below the script block, styled as terminal output.
- **History sidebar:** Collapsible list of past chat sessions (stored in localStorage).

### 4.4 Panel Regression Panel
- **Form fields:**
  - Data selector (dropdown of loaded datasets)
  - Y variable (dropdown from data columns, filtered to numeric)
  - X variables (multi-select checklist)
  - Entity ID column (dropdown)
  - Time column (dropdown)
  - Cluster level (radio: entity / time / double)
  - Fixed effects (checkboxes: entity FE, time FE, entity×time FE)
  - Output format (checkboxes: LaTeX, HTML, Word, Pickle)
- **Run button:** "▶ 运行回归" with loading state.
- **Results:** Appear in Results Panel below. Show coefficient table + fit stats inline.

### 4.5 IV Estimator Panel
- **Form fields:** Y, Exogenous X, Endogenous variable, Instruments (multi-select), Output format.
- **Diagnostics section:** First-stage F-stat, DW-Hausman test, Hansen J test — shown as labeled cards with color-coded pass/fail.

### 4.6 Staggered DID Panel
- **Form fields:** Y, Time, ID, Treatment timing variable, Control group type, Estimator (CS/SA), Covariates.
- **Parallel trends plot:** Generated automatically, shown inline with attribution line at t=0.
- **ATT(g,t) heatmap:** Color-coded grid of group-time specific treatment effects.

### 4.7 Paper Writer Panel
- **Step-by-step wizard:** Research question → Theory selection → Hypotheses → Method → Results → Discussion.
- **Template selector:** IEEE dual-column / Single column.
- **Progress bar:** Shows which sections are complete.
- **Preview pane:** Live-updating paper preview in read-only panel.

### 4.8 Results Panel
- **Tabbed:** Tables | Plots | Logs | Diagnostics
- **Tables:** Rendered LaTeX/HTML with "Copy" and "Download" buttons.
- **Plots:** Zoomable images (event study, forest plots, heatmaps).
- **Logs:** Terminal-style output with ANSI color support.
- **Export:** Batch download all results as ZIP.

### 4.9 Skills Library
- **Card grid:** Each skill as a card with icon, name, description, trigger keywords.
- **Enable/disable toggle** per skill.
- **Click card** → opens skill-specific panel in main area.

---

## 5. Component Inventory

### Navigation
- **Sidebar item:** Icon + label. States: default (slate-700 bg), hover (slate-600), active (blue-500 left border + blue-900 bg).
- **Topbar:** Logo left, status pills center, settings gear right. Height 56px.

### Cards
- **Dataset card:** Rounded-lg, slate-800 bg, border slate-700. Hover: border-blue-500.
- **Skill card:** Rounded-lg, gradient bg optional. Icon top, title, description, keyword pills.

### Forms
- **Select/Dropdown:** Custom styled, slate-700 bg, blue-500 focus ring.
- **Multi-select checklist:** Scrollable list with checkboxes, search filter input above.
- **Button primary:** Blue-500 bg, white text, hover blue-600, active scale-98.
- **Button secondary:** Transparent bg, slate-400 text, border slate-600, hover bg slate-700.
- **Button danger:** Red-500 bg for destructive actions.

### Data Display
- **Table (results):** Rounded, slate-800 bg, thead slate-700, alternating rows slate-750/slate-800. Significance stars in fuchsia.
- **Code block:** JetBrains Mono, slate-900 bg, fuchsia-400 for keywords, green for strings.
- **Stat card:** Single number large (32px), label below (12px slate-400). Example: "β = 0.34***".

### Feedback
- **Toast notification:** Bottom-right, slide-in. Types: success (green), error (red), info (blue), warning (yellow). Auto-dismiss 4s.
- **Loading state:** Pulsing skeleton bars (not spinner) for content areas; subtle glow on buttons.
- **Empty state:** Illustration + message + CTA button. Example: "还没有分析结果，上传数据开始吧 📊"

---

## 6. Technical Approach

**Backend:** FastAPI (Python). Single `server.py` that:
- Serves the web UI (HTML/CSS/JS) as static files + Jinja2 templates
- Proxies to existing `api-server.py` endpoints (or embeds them)
- Handles file uploads to `user_data/`
- Reads `user_output/` for results
- WebSocket for streaming LLM responses

**Frontend:** Vanilla HTML/CSS/JS (no build step). Chart.js for plots. Highlight.js for code blocks.

**Key API endpoints:**
```
GET  /                           → Web UI (HTML)
GET  /api/datasets               → List available datasets
POST /api/datasets/upload        → Upload file to user_data/
GET  /api/datasets/<name>/preview → First N rows + column types
GET  /api/results                → List all results (tables/plots)
GET  /api/results/<id>            → Get specific result content
POST /api/chat                   → LLM chat (proxies to /analyze)
POST /api/run                    → Execute skill script
GET  /api/skills                 → List all skills + registry
WS   /ws/chat                    → Streaming chat responses
```

**File structure:**
```
web-ui/
├── server.py              # FastAPI main app
├── DESIGN.md              # This file
├── templates/
│   └── index.html         # Single-page app shell
└── static/
    ├── css/
    │   └── style.css      # All styles
    └── js/
        └── app.js         # All frontend logic
```

**Startup:**
```bash
cd is-econometrics-skills
export OPENAI_API_KEY=sk-xxx
python web-ui/server.py
# Opens at http://localhost:8000
```
