#!/usr/bin/env python3
"""
build_variables.py — 变量构建脚本
"""
import argparse, warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np

OPS = {
    'diff':         lambda s: s.diff(1),
    'pct_change':   lambda s: s.pct_change(1),
    'lag1':         lambda s: s.shift(1),
    'lag2':         lambda s: s.shift(2),
    'lead1':        lambda s: s.shift(-1),
    'winsorize':    lambda s: s.clip(s.quantile(0.01), s.quantile(0.99)),
    'demean':       lambda s: s - s.mean(),
    'stdz':         lambda s: (s - s.mean()) / s.std(),
    'winsor':       lambda s: s.clip(s.quantile(0.01), s.quantile(0.99)),
}

def apply_op(df, entity, col, op, new_name):
    if op in ('industry_mean', 'industry_adj'):
        grp = df.groupby([entity, 'year'])[col].transform('mean')
        if op == 'industry_mean':
            df[new_name] = grp
        else:
            df[new_name] = df[col] - grp
    else:
        df[new_name] = OPS[op](df[col])
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--entity', required=True)
    parser.add_argument('--time', required=True)
    parser.add_argument('--operations', required=True,
                        help='格式: 原变量:操作:新变量名[|...]')
    parser.add_argument('--output_csv', required=True)
    args = parser.parse_args()

    ext = args.data.lower()
    if ext.endswith('.dta'):
        df, _ = __import__('pyreadstat').read_dta(args.data)
    elif ext.endswith(('.xlsx','.xls')):
        df = pd.read_excel(args.data)
    else:
        df = pd.read_csv(args.data)

    added = []
    for spec in args.operations.split('|'):
        old, op, new = spec.split(':')
        df = apply_op(df, args.entity, old.strip(), op.strip(), new.strip())
        added.append(f'  {new} = {op}({old})')

    print(f'\n🔧 [变量构建完成]')
    print(f'  新增变量: {len(added)} 个')
    for a in added:
        print(a)
    df.to_csv(args.output_csv, index=False, encoding='utf-8-sig')
    print(f'\n✅ 保存至: {args.output_csv}')

if __name__ == '__main__':
    main()