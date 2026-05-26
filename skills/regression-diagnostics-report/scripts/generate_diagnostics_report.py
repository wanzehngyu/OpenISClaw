#!/usr/bin/env python3
"""
generate_diagnostics_report.py — 回归诊断报告生成脚本
读取所有 pickle 结果，综合生成 Markdown（+ 可选 LaTeX）诊断报告
"""
import argparse, warnings
warnings.filterwarnings('ignore')
import pickle, re, datetime

def load_pickle(path):
    with open(path, 'rb') as f:
        return pickle.load(f)

def extract_summary(pkl_path):
    """从 pickle 中提取关键统计量，供报告生成使用"""
    try:
        obj = load_pickle(pkl_path)
        if hasattr(obj, 'summary'):
            smry = str(obj.summary())
        else:
            smry = str(obj)
        return smry
    except Exception as e:
        return f'[读取失败: {e}]'

def generate_report(pickles_models, plots, rename_map, title, out_md):
    rename = {}
    if rename_map:
        for pair in rename_map.split(','):
            k, v = pair.split(':')
            rename[k.strip()] = v.strip()

    lines = []
    lines.append(f'# {title or "实证分析报告"}\n')
    lines.append(f'*生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}*\n')
    lines.append('---\n')

    lines.append('## 一、模型设定\n')
    lines.append('本报告汇总以下回归模型的分析结果：\n')
    for pkl, model_name in pickles_models:
        lines.append(f'- **{model_name}** (`{pkl.split("/")[-1]}`)')
    lines.append('\n')

    lines.append('## 二、回归结果\n')
    for pkl, model_name in pickles_models:
        lines.append(f'### 2.1 {model_name}\n')
        summary = extract_summary(pkl)
        lines.append('```\n')
        lines.append(summary[:2000])  # 限制长度
        lines.append('```\n')

    if plots:
        lines.append('## 三、可视化结果\n')
        for i, plot_path in enumerate(plots, 1):
            lines.append(f'**图{i}**：`{plot_path.split("/")[-1]}`\n')
            lines.append(f'![]({plot_path})\n')

    lines.append('## 四、学术结论与启示\n')
    lines.append('（由大模型根据上述结果综合生成）\n\n')
    lines.append('### 4.1 主要发现\n')
    lines.append('[请大模型根据回归结果提炼核心发现]\n\n')
    lines.append('### 4.2 稳健性说明\n')
    lines.append('[如有多模型设定或多方法，请对比说明估计结果的稳健性]\n\n')
    lines.append('### 4.3 研究局限\n')
    lines.append('[由大模型根据方法局限性客观描述]\n')

    content = '\n'.join(lines)
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'\n📋 诊断报告已生成: {out_md}')
    return content

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pickles', required=True, help='空格分隔的pickle路径')
    parser.add_argument('--models', required=True, help='空格分隔的模型名称')
    parser.add_argument('--plots', help='空格分隔的图表路径')
    parser.add_argument('--rename')
    parser.add_argument('--title', default='实证分析报告：回归诊断结果')
    parser.add_argument('--output_markdown', required=True)
    parser.add_argument('--output_latex')  # 可选
    args = parser.parse_args()

    pickles = args.pickles.split()
    model_names = args.models.split()
    plots = args.plots.split() if args.plots else []

    generate_report(
        zip(pickles, model_names),
        plots,
        args.rename,
        args.title,
        args.output_markdown
    )
    print('✅ 完成')

if __name__ == '__main__':
    main()