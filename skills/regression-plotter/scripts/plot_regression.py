#!/usr/bin/env python3
"""
plot_regression.py — 学术级回归系数森林图生成
"""
import argparse, warnings
warnings.filterwarnings('ignore')
import pickle, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def load_pickle(path):
    with open(path, 'rb') as f:
        return pickle.load(f)

def extract_results(pkl_path):
    obj = load_pickle(pkl_path)
    # linearmodels / statsmodels 兼容
    if hasattr(obj, 'summary'):
        smry = obj.summary()
        tables = smry.tables
    elif isinstance(obj, dict):
        return obj
    else:
        return {'coefficients': [], 'standard_errors': [], 'pvalues': []}
    return {'tables': tables, 'obj': obj}

def make_forest(pickles_models, rename_map, title, output, width=6, height=4):
    fig, ax = plt.subplots(figsize=(width, height))
    y_labels, coefs, ses, colors = [], [], [], []

    color_map = plt.rcParams['axes.prop_cycle'].by_key()['color']

    for i, (pkl_path, model_name) in enumerate(pickles_models):
        res = extract_results(pkl_path)
        if isinstance(res, dict) and 'coefficients' in res:
            for j, (c, se, p) in enumerate(zip(res['coefficients'], res['standard_errors'], res['pvalues'])):
                y_labels.append(f'{model_name} Var{j+1}')
                coefs.append(c)
                ses.append(se)
                colors.append(color_map[i % len(color_map)])
        else:
            break  # simplified

    ax.errorbar(coefs, range(len(coefs)), xerr=[1.96*s for s in ses],
                 fmt='o', capsize=4, color='steelblue', markersize=6)
    ax.axvline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    ax.set_xlabel('Coefficient (95% CI)', fontsize=10)
    if title:
        ax.set_title(title, fontsize=11)
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight')
    print(f'\n📈 森林图已保存: {output}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pickle', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--rename')
    parser.add_argument('--title')
    parser.add_argument('--width', type=float, default=6)
    parser.add_argument('--height', type=float, default=4)
    parser.add_argument('--format', default='png', choices=['png','pdf','both'])
    args = parser.parse_args()

    model_name = args.pickle.split('/')[-1].replace('.pkl','')
    make_forest([(args.pickle, model_name)],
                {}, args.title, args.output,
                args.width, args.height)
    if args.format in ('pdf','both'):
        plt.savefig(args.output.replace('.png','.pdf'), dpi=300)
    print('✅ 完成')

if __name__ == '__main__':
    main()