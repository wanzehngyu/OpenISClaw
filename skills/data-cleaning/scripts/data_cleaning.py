#!/usr/bin/env python3
"""
data_cleaning.py — 面板数据系统性清洗脚本
"""
import argparse, warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import pickle

def load_data(path):
    p = path.lower()
    if p.endswith('.dta'):
        df, _ = __import__('pyreadstat').read_dta(path)
    elif p.endswith(('.xlsx','.xls')):
        df = pd.read_excel(path)
    elif p.endswith('.csv'):
        df = pd.read_csv(path)
    else:
        raise ValueError(f'Unsupported format: {path}')
    return df

def clean(df, entity, time, missing_strategy, winsorize, report_lines):
    original_n = len(df)
    original_cols = list(df.columns)

    # 1. 缺失值处理
    for col in df.columns:
        if df[col].isna().sum() == 0:
            continue
        n_missing = df[col].isna().sum()
        pct = n_missing / len(df) * 100
        report_lines.append(f'| {col} | {n_missing} | {pct:.1f}% | ')
        if missing_strategy == 'interpolate':
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df.groupby(entity)[col].transform(lambda x: x.interpolate(method='linear'))
                df[col] = df[col].ffill().bfill()
        elif missing_strategy == 'drop':
            df = df.dropna(subset=[col])
        elif missing_strategy == 'mean' and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].mean())

    # 2. 异常值处理（Winsorize）
    if winsorize:
        parts = winsorize.split(',')
        lo = float(parts[0]) if len(parts) > 0 else 0.01
        hi = float(parts[1]) if len(parts) > 1 else 0.99
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and col not in [entity, time]:
                lo_val = df[col].quantile(lo)
                hi_val = df[col].quantile(hi)
                df[col] = df[col].clip(lo_val, hi_val)

    # 3. 去重
    before_dup = len(df)
    df = df.drop_duplicates(subset=[entity, time], keep='first')
    n_dup = before_dup - len(df)
    if n_dup > 0:
        report_lines.append(f'| {entity}+{time} 重复行 | {n_dup} | 删除（保留首条） |')

    # 4. ID-时间唯一性
    if df.duplicated(subset=[entity, time]).any():
        raise ValueError(f'数据中存在相同 {entity}-{time} 组合的多条记录，请检查数据')

    final_n = len(df)
    report_lines.append(f'\n**清洗后样本量**: {original_n} → {final_n}（减少 {original_n-final_n} 行）')
    return df, report_lines

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--entity', required=True)
    parser.add_argument('--time', required=True)
    parser.add_argument('--missing_strategy', default='interpolate',
                        choices=['drop','ffill','interpolate','mean'])
    parser.add_argument('--winsorize', default='yes,0.01,0.99',
                        help='yes/no,lower,upper  如 yes,0.01,0.99')
    parser.add_argument('--output_csv', required=True)
    parser.add_argument('--report_path', help='诊断报告路径')
    args = parser.parse_args()

    print(f'\n🧹 [数据清洗开始]')
    df = load_data(args.data)

    report = [f'# 数据质量报告 — 清洗前 → 清洗后\n',
              f'原始数据: {len(df)} 行 × {len(df.columns)} 列\n']
    df_cleaned, report = clean(df, args.entity, args.time,
                               args.missing_strategy, args.winsorize, report)

    print(f'✅ 清洗完成: {len(df)} → {len(df_cleaned)} 行')
    df_cleaned.to_csv(args.output_csv, index=False, encoding='utf-8-sig')
    print(f'   保存至: {args.output_csv}')

    if args.report_path:
        with open(args.report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        print(f'   报告: {args.report_path}')

if __name__ == '__main__':
    main()