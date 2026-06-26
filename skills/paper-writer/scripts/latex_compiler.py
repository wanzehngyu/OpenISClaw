#!/usr/bin/env python3
"""
latex_compiler.py
编译 LaTeX 项目并报告编译结果。
支持 XeLaTeX + BibTeX 三次编译流程。
"""

import argparse
import os
import re
import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd: list[str], cwd: str = None, timeout: int = 60) -> tuple[int, str, str]:
    """运行命令，返回 (返回码, stdout, stderr)。"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def compile_latex(
    tex_file: str,
    output_dir: str,
    template: str = "ieee_dual_column",
    max_passes: int = 3,
) -> dict:
    """
    执行 XeLaTeX × N + BibTeX 编译流程。

    返回：
    {
        "success": bool,
        "pdf_path": str,
        "errors": [str],
        "warnings": {"overfull": int, "underfull": int, "undefined_refs": int},
        "bbl_entries": int,
        "pages": int,
    }
    """
    base = Path(output_dir)
    tex_name = Path(tex_file).stem

    # 清理辅助文件
    for ext in [".aux", ".bbl", ".blg", ".log", ".out", ".toc", ".lof", ".lot"]:
        f = base / f"{tex_name}{ext}"
        if f.exists():
            f.unlink()

    errors = []
    warnings = {"overfull": 0, "underfull": 0, "undefined_refs": 0}
    pages = 0
    bbl_entries = 0

    # 第 1 遍：xelatex
    rc, out, err = run_command(
        ["xelatex", "-interaction=nonstopmode", f"-output-directory={output_dir}", tex_file],
        cwd=output_dir,
        timeout=120,
    )
    log_text = (out + err)

    # 提取错误
    for line in log_text.splitlines():
        if re.match(r"^! ", line):
            errors.append(f"[XeLaTeX Error] {line}")

    # 提取 overfull/underfull
    for line in log_text.splitlines():
        if "Overfull" in line and "too wide" in line:
            warnings["overfull"] += 1
        if "Underfull" in line and "has occurred" in line:
            warnings["underfull"] += 1
        if "undefined reference" in line.lower():
            warnings["undefined_refs"] += 1

    # 提取页数
    m = re.search(r"\[(\d+)\s*pages?\]", log_text)
    if m:
        pages = int(m.group(1))

    # 检查是否有致命错误
    if rc != 0 and not errors:
        errors.append(f"[XeLaTeX] Non-zero exit code {rc}")

    # 第 2 遍：bibtex（如有 .aux）
    aux_file = base / f"{tex_name}.aux"
    if aux_file.exists():
        rc2, bout, berr = run_command(
            ["bibtex", tex_name],
            cwd=output_dir,
            timeout=30,
        )
        # 统计 bbl 条目数
        bbl_file = base / f"{tex_name}.bbl"
        if bbl_file.exists():
            bbl_text = bbl_file.read_text(encoding="utf-8", errors="replace")
            bbl_entries = len(re.findall(r"\\bibitem\{", bbl_text))

    # 第 2-3 遍：xelatex
    for pass_n in range(2, max_passes + 1):
        rc, out2, err2 = run_command(
            ["xelatex", "-interaction=nonstopmode", f"-output-directory={output_dir}", tex_file],
            cwd=output_dir,
            timeout=120,
        )
        log_text2 = (out2 + err2)

        # 检查新增错误
        for line in log_text2.splitlines():
            if re.match(r"^! ", line):
                err_msg = f"[XeLaTeX Pass {pass_n}] {line}"
                if err_msg not in errors:
                    errors.append(err_msg)

        # 提取 undefined references（新增的）
        for line in log_text2.splitlines():
            if "undefined reference" in line.lower() and "Citation" not in line:
                warnings["undefined_refs"] += 1

    # 最终页数
    m2 = re.search(r"\[(\d+)\s*pages?\]", (out2 if 'out2' in dir() else out))
    if m2:
        pages = int(m2.group(1))

    pdf_path = str(base / f"{tex_name}.pdf")
    pdf_exists = os.path.exists(pdf_path)

    return {
        "success": len(errors) == 0 and pdf_exists,
        "pdf_path": pdf_path,
        "errors": errors,
        "warnings": warnings,
        "bbl_entries": bbl_entries,
        "pages": pages,
        "pdf_size_kb": os.path.getsize(pdf_path) // 1024 if pdf_exists else 0,
    }


def print_report(result: dict):
    """打印编译报告。"""
    print("=" * 50)
    print("LaTeX 编译报告")
    print("=" * 50)
    status = "✅ 成功" if result["success"] else "❌ 失败"
    print(f"状态：{status}")
    print(f"页数：{result['pages']} 页")
    print(f"PDF 大小：{result['pdf_size_kb']} KB")
    print(f"参考文献条目：{result['bbl_entries']} 条")

    if result["errors"]:
        print(f"\n❌ 错误（{len(result['errors'])} 个）：")
        for e in result["errors"]:
            print(f"  {e}")
    else:
        print("\n✅ 无编译错误")

    w = result["warnings"]
    print(f"\n⚠️  警告：")
    print(f"  Overfull hbox: {w['overfull']} 个")
    print(f"  Underfull hbox: {w['underfull']} 个")
    print(f"  Undefined refs: {w['undefined_refs']} 个")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="LaTeX 编译与检查工具")
    parser.add_argument("--dir", required=True, help="项目目录（包含 main.tex）")
    parser.add_argument("--main", default="main.tex", help="主文档名称")
    parser.add_argument("--template", default="ieee_dual_column",
                        choices=["ieee_dual_column", "single_column"],
                        help="论文模板类型")
    parser.add_argument("--passes", type=int, default=3, help="XeLaTeX 编译次数")
    args = parser.parse_args()

    project_dir = Path(args.dir).resolve()
    main_tex = project_dir / args.main

    if not main_tex.exists():
        print(f"错误：找不到主文档 {main_tex}")
        sys.exit(1)

    # 确保 template 的 main.tex 在项目目录中
    skill_dir = Path(__file__).parent.parent.resolve()
    template_main = skill_dir / "templates" / args.template / "main.tex"
    if not main_tex.exists() and template_main.exists():
        shutil.copy(template_main, main_tex)
        print(f"已从模板复制 main.tex → {main_tex}")

    print(f"正在编译：{main_tex}")
    print(f"项目目录：{project_dir}")

    result = compile_latex(
        str(main_tex),
        str(project_dir),
        template=args.template,
        max_passes=args.passes,
    )

    print_report(result)

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
