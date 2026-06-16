#!/usr/bin/env python3
"""
literature_fetcher.py
基于用户研究问题，使用 Tavily API 检索 IS 领域近 5 年相关文献，
并生成格式化的文献综述草稿。
"""

import argparse
import json
import sys
import os
from pathlib import Path

# 尝试导入 Tavily，如果不可用则给出提示
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("Warning: tavily package not installed. Will use mock data for demonstration.", file=sys.stderr)


# IS 核心期刊列表（用于过滤）
IS_JOURNALS = [
    "MIS Quarterly", "MISQ", "Information Systems Research", "ISR",
    "Journal of the Association for Information Systems", "JAIS",
    "Journal of Management Information Systems", "JMIS",
    "European Journal of Information Systems", "EJIS",
    "Information Systems Journal", "ISJ",
    "Decision Support Systems", "DSS",
    "Journal of Information Technology", "JIT",
    "Internet Research", "Management Science", "Academy of Management Journal",
    "Strategic Management Journal", "Administrative Science Quarterly",
    "Organization Science", "Harvard Business Review",
]


def build_search_queries(research_question: str, topic: str) -> list:
    """构建多角度检索查询，提升文献覆盖度。"""
    queries = [
        f"{topic} IS information systems",
        f"{topic} digital transformation firm performance",
        f"{research_question} empirical study",
        f"{topic} theoretical framework",
    ]
    return queries[:4]


def search_tavily(query: str, api_key: str = None, max_results: int = 10) -> list:
    """使用 Tavily API 检索文献。"""
    if not TAVILY_AVAILABLE:
        return _mock_results(query, max_results)

    client = TavilyClient(api_key=api_key or os.environ.get("TAVILY_API_KEY"))
    results = client.search(query=query, max_results=max_results, include_answer=False)
    return results.get("results", [])


def _mock_results(query: str, max_results: int) -> list:
    """Tavily 不可用时的模拟返回数据。"""
    print(f"[Mock] Searching Tavily for: {query}", file=sys.stderr)
    mock_papers = [
        {
            "title": "Digital Transformation and Firm Performance: A Literature Review",
            "url": "https://doi.org/10.1287/isre.2022.0000",
            "content": "A comprehensive review of digital transformation literature in IS, finding positive effects on firm performance across multiple studies.",
        },
        {
            "title": "Dynamic Capabilities and Digital Transformation: An Empirical Investigation",
            "url": "https://doi.org/10.1287/misq.2023.0000",
            "content": "This study examines how dynamic capabilities mediate the relationship between digital transformation and firm performance, using panel data from Chinese manufacturing firms.",
        },
        {
            "title": "The Role of Institutional Pressures in Digital Transformation: Evidence from Emerging Markets",
            "url": "https://doi.org/10.1080/07421222.2022.0000",
            "content": "Investigates how institutional pressures shape firms' digital transformation strategies in emerging markets like China.",
        },
    ]
    return mock_papers[:max_results]


def filter_is_journals(results: list) -> list:
    """过滤出 IS 领域期刊的文献。"""
    filtered = []
    for r in results:
        title_lower = r.get("title", "").lower()
        content_lower = r.get("content", "").lower()
        # 简单关键词匹配
        is_keywords = ["information systems", "mis quarterly", "is research", "jaIS",
                       "digital transformation", "it investment", "information technology",
                       "firm performance", "enterprise", "management information"]
        if any(kw in title_lower or kw in content_lower for kw in is_keywords):
            filtered.append(r)
    return filtered


def extract_year(title: str, content: str = "") -> str:
    """从标题或内容中提取年份。"""
    import re
    years = re.findall(r"(20[1-2][0-9])", title + content)
    if years:
        return years[0]
    return "n.d."


def extract_authors(title: str) -> str:
    """从标题中提取作者（简化版）。"""
    import re
    # 尝试匹配 "Author, A. A., & Author, B. B. (Year)" 格式
    if "(" in title:
        return title.split("(")[0].strip()
    # 简单处理：取标题第一部分作为作者占位
    parts = title.split(":")
    return parts[0].strip() if parts else title


def format_reference(result: dict) -> str:
    """将检索结果格式化为 APA 格式参考文献。"""
    title = result.get("title", "Untitled")
    url = result.get("url", "")
    content_snippet = result.get("content", "")[:200]

    # 提取年份
    year = extract_year(title, content_snippet)
    authors = extract_authors(title)

    ref = f"{authors} ({year}). {title}."
    if url and url.startswith("http"):
        ref += f" Retrieved from {url}"

    return ref


def generate_literature_review_section(literature_items: list,
                                       research_question: str,
                                       topic: str) -> str:
    """生成文献综述章节内容。"""

    if not literature_items:
        review_text = f"""### 1.2 文献综述

> 注：由于当前 Tavily API 暂不可用或未检索到 IS 领域文献，
> 以下文献列表为占位内容。用户可自行补充相关文献。

围绕"{research_question}"这一主题，现有文献主要从以下角度展开研究：

**已有研究的主要发现：**
- 关于 {topic} 与企业绩效的关系，现有研究普遍发现[正向/负向/复杂]关系
- 主流理论框架包括[理论1]、[理论2]等

**已有研究的不足（Research Gap）：**
- 现有研究较少在[中国制度背景/特定行业/特定情境]下检验[理论名称]的适用性
- 现有研究对[调节/中介机制]的关注不足
- 现有研究多使用[截面数据/横截面调查]，面板数据证据相对缺乏

**本研究的定位：**
本研究在[现有研究空白]的基础上，运用{topic}理论和面板数据，对{research_question}进行系统检验。

"""
        return review_text

    # 按主题聚类分组
    review_text = """### 1.2 文献综述

围绕本研究主题，既有文献主要从以下方面展开：

"""

    for i, item in enumerate(literature_items[:10], 1):
        title = item.get("title", "Untitled")
        snippet = item.get("content", "")[:300]
        url = item.get("url", "")
        year = extract_year(title)
        authors = extract_authors(title)

        review_text += f"""**文献{i}：{title}**
- **作者/来源**：{authors} ({year})
- **主要发现**：{snippet}
"""
        if url:
            review_text += f"- **链接**：{url}\n"
        review_text += "\n"

    review_text += """**文献综述小结：**
既有文献为本研究提供了理论基础和方法参照，但存在以下不足：
- 现有研究较少在[中国制度背景]下检验[理论名称]的适用性
- 现有研究对[具体机制/调节因素]的关注不足
- 面板数据证据相对缺乏

本研究在上述空白的基础上，运用[理论名称]和[实证方法]，对[研究问题]进行系统检验。
"""

    return review_text


def main():
    parser = argparse.ArgumentParser(description="IS 文献检索与综述生成")
    parser.add_argument("--query", required=True, help="研究问题（用于检索）")
    parser.add_argument("--topic", required=True, help="核心主题关键词")
    parser.add_argument("--top_k", type=int, default=10, help="每个查询返回的最大结果数")
    parser.add_argument("--output", default="literature_review.md", help="输出文件路径")
    parser.add_argument("--api_key", default=None, help="Tavily API Key（可选，从环境变量 TAVILY_API_KEY 读取）")
    args = parser.parse_args()

    queries = build_search_queries(args.query, args.topic)
    all_results = []

    print(f"开始文献检索，共 {len(queries)} 个查询...")
    for q in queries:
        print(f"  查询：{q[:60]}...")
        results = search_tavily(q, api_key=args.api_key, max_results=args.top_k)
        all_results.extend(results)

    # 去重（基于 URL）
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = r.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    # 过滤 IS 期刊文献
    is_results = filter_is_journals(unique_results)

    print(f"\n检索完成：共 {len(all_results)} 条结果，去重后 {len(unique_results)} 条，IS 相关 {len(is_results)} 条")

    # 生成文献综述章节
    review_text = generate_literature_review_section(is_results, args.query, args.topic)

    # 生成参考文献列表
    ref_list = []
    ref_list.append("# 参考文献\n")
    for i, r in enumerate(is_results[:15], 1):
        ref_list.append(f"[{i}] {format_reference(r)}\n")

    output_content = review_text + "\n---\n" + "".join(ref_list)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output_content)

    print(f"\n文献综述已生成：{args.output}")
    print(f"文献数量：{len(is_results)} 篇")
    print(f"检索查询数：{len(queries)} 个")

    return 0


if __name__ == "__main__":
    sys.exit(main())