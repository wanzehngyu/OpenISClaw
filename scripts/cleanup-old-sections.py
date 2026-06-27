#!/usr/bin/env python3
"""
删除各 SKILL.md 中旧的 '## 依赖安装确认' section，
替换为新的统一 '## 安装与使用' section。
"""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SKILLS_DIR = PROJECT_ROOT / "skills"

OLD_SECTIONS = ["## 依赖安装确认", "## 安装确认", "## 环境准备"]

def cleanup_skill(skill_dir: Path) -> bool:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False

    content = skill_md.read_text(encoding="utf-8")
    original = content
    changed = False

    for old_section in OLD_SECTIONS:
        # 匹配从旧 section 标题到下一个 ## 标题或文件末尾的内容
        pattern = rf'\n{re.escape(old_section)}\n.*?(?=\n##[^\w#]|\Z)'
        new_content = re.sub(pattern, '', content, flags=re.DOTALL)
        if new_content != content:
            content = new_content
            changed = True
            print(f"  🧹 {skill_dir.name}: removed '{old_section}'")

    if changed:
        # 清理多余的连续空行（超过2个换行合并为2个）
        content = re.sub(r'\n{3,}', '\n\n', content)
        skill_md.write_text(content, encoding="utf-8")
    return changed

def main():
    count = 0
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        if cleanup_skill(skill_dir):
            count += 1
    print(f"\nCleaned {count} files.")

if __name__ == "__main__":
    main()
