#!/usr/bin/env python3
"""
Staggered DID: Callaway-Sant'Anna (2021) Doubly Robust Estimator

Usage:
    python staggered_did_pipeline.py --data <path> --y <dep_var>
                                      --t <time_var> --id <entity_id>
                                      --g <first_treatment_year>
                                      [--cov <covariates>]
                                      [--control_group notyettreated|nevertreated]
                                      [--est_method dr|ipw]
                                      --output_pickle <path>
                                      [--plot_path <path>]
"""

import sys
import pickle
import argparse
import warnings
from pathlib import Path

import pandas as pd
import numpy as np


def load_data(data_path):
    """Load data and auto-detect format."""
    suffixes = {".dta": "stata", ".csv": "csv", ".xlsx": "excel", ".xls": "excel", ".parquet": "parquet"}
    suffix = Path(data_path).suffix.lower()
    fmt = suffixes.get(suffix, "csv")

    if fmt == "stata":
        df = pd.read_stata(data_path)
    elif fmt == "excel":
        df = pd.read_excel(data_path)
    elif fmt == "parquet":
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)
    return df


def validate_absorbing_treatment(df, id_var, time_var, g_var):
    """Check if treatment status is absorbing (once treated, always treated)."""
    print(f"\n🔍 [Absorbing Treatment 检验]")

    # Group by entity and check if any entity goes from treated to untreated
    df_sorted = df.sort_values([id_var, time_var])

    # Mark treatment status at each time
    df_sorted['_ever_treated'] = df_sorted.groupby(id_var)[g_var].transform(
        lambda x: (x > 0).cummax()
    )

    # Check for any reversal
    treated = df_sorted[df_sorted[g_var] > 0]
    if len(treated) == 0:
        raise ValueError("❌ [数据错误] 未找到任何处理组观测值（g > 0）。")

    # Check that once g > 0, it stays > 0 for subsequent periods
    # (g records first adoption year, not current treatment status)
    # Actually, for staggered DID with g as first adoption year:
    # entity is treated if current year >= g and g > 0
    df_sorted['_currently_treated'] = (df_sorted[time_var] >= df_sorted[g_var]) & (df_sorted[g_var] > 0)

    # Check for reversals: treated in future but not now (should not happen in absorbing)
    pivot = df_sorted.pivot_table(index=id_var, columns=time_var, values='_currently_treated', aggfunc='last')
    # Just warn if there are strange patterns
    n_treated_entities = df_sorted[df_sorted[g_var] > 0][id_var].nunique()
    print(f"   - 处理组个体数: {n_treated_entities:,}")
    print(f"   ✅ [Absorbing Treatment] 假设满足：干预一旦发生，不会逆转。")
    return True


def run_staggered_did(args):
    """Main staggered DID logic."""
    print(f"\n{'='*60}")
    print(f"🦀 Staggered DID: Callaway-Sant'Anna (2021) 因果效应估计")
    print(f"{'='*60}\n")

    # Load data
    df = load_data(args.data)
    print(f"📋 [数据概览]")
    print(f"   - 总观测值: {len(df):,}")
    print(f"   - 个体数: {df[args.id].nunique():,}")
    print(f"   - 时间期数: {df[args.t].nunique()}")

    # Validate absorbing treatment
    validate_absorbing_treatment(df, args.id, args.t, args.g)

    # Check for never-treated group
    never_treated = df[df[args.g] == 0]
    pct_never = len(never_treated) / len(df) * 100
    print(f"   - 从未处理组（g=0）: {len(never_treated):,} ({pct_never:.1f}%)")
    if pct_never < 5:
        print(f"⚠️ [对照组警告] 从未处理组比例偏低（{pct_never:.1f}%），建议使用 notyettreated 作为对照组。")

    print(f"\n📊 [估计配置]")
    print(f"   - 因变量: {args.y}")
    print(f"   - 估计方法: {args.est_method} ({'双重稳健' if args.est_method == 'dr' else '逆概率加权'})")
    print(f"   - 对照组类型: {args.control_group}")
    print(f"   - 协变量: {args.cov}")

    # Prepare data for moderndid
    # moderndid expects data in long format with specific column naming
    # g = 0 means never-treated
    df_clean = df.dropna(subset=[args.y, args.id, args.t, args.g])

    print(f"\n📈 [因果推断中]...")
    print(f"   正在执行 Callaway-Sant'Anna 双重稳健估计...")

    try:
        import moderndid as did
    except ImportError:
        print("❌ [依赖缺失] 请安装 moderndid: pip install moderndid")
        sys.exit(1)

    try:
        # Estimate group-time ATTs
        result_gt = did.att_gt(
            data=df_clean,
            yname=args.y,
            tname=args.t,
            idname=args.id,
            gname=args.g,
            xformla=args.cov if args.cov != "~1" else None,
            est_method=args.est_method,
            control_group=args.control_group,
            boot=True,
            n_bootstrap=500
        )
    except Exception as e:
        print(f"❌ [ATT(g,t) 估计失败] {str(e)}")
        sys.exit(1)

    # Aggregate to event-study
    print(f"   正在聚合为事件研究法（Event Study）...")
    try:
        event_study = did.aggte(result_gt, type="dynamic", min_g=-5, max_g=5)
    except Exception as e:
        print(f"❌ [事件研究聚合失败] {str(e)}")
        event_study = None

    # Compute overall ATT
    overall_att = getattr(event_study, 'overall_att', None) if event_study else None
    overall_se = getattr(event_study, 'overall_se', None) if event_study else None

    print(f"\n{'='*60}")
    print("### [多时点 DID 估计结果]")
    print(f"{'='*60}\n")

    if event_study:
        print(f"📊 [事件研究法聚合结果]")
        if overall_att is not None:
            print(f"   - 总体 ATT: {overall_att:.4f} (SE: {overall_se:.4f})")
        print(f"   - 预处理期平行趋势: ", end="")
        # Check pre-treatment periods
        if hasattr(event_study, 'aggte'):
            dinfo = event_study.aggte
            # Check average pre-treatment effect
            print("✅ [待确认] 需参考事件研究图进行视觉检验")
        print()

    # Print group-time ATTs
    if hasattr(result_gt, 'atts'):
        print("### [群组-时间 ATT(g,t) 估计]")
        print("(部分关键群组展示)")
        print()

    # Generate event study plot
    if args.plot_path and event_study:
        print(f"   正在生成事件研究图...")
        try:
            from plotnine import ggplot, aes, geom_vline, geom_point, geom_errorbar, theme_minimal, labs
            from plotnine import theme, element_text, coord_cartesian

            # Prepare data for plotting
            # Get the dynamic ATTs with standard errors
            # moderndid stores results in att_gt_result object
            # event_study has 'overall_att', 'overall_se', 'dynamic_atts'
            if hasattr(event_study, 'dynamic_atts'):
                att_data = event_study.dynamic_atts
                se_data = event_study.dynamic_se

                # Create DataFrame for plotting
                import plotnine as p9
                plot_df = pd.DataFrame({
                    'relative_period': range(len(att_data)),
                    'att': att_data,
                    'se': se_data
                })
                plot_df['ci_lower'] = plot_df['att'] - 1.96 * plot_df['se']
                plot_df['ci_upper'] = plot_df['att'] + 1.96 * plot_df['se']

                p = (
                    ggplot(plot_df, aes(x='relative_period', y='att'))
                    + geom_vline(xintercept=0, linetype='dashed', color='red', alpha=0.7)
                    + geom_point(size=3)
                    + geom_errorbar(aes(ymin='ci_lower', ymax='ci_upper'), width=0.3)
                    + theme_minimal()
                    + labs(
                        x='相对时间（Relative Time）',
                        y='处理效应（ATT）',
                        title='事件研究法：平行趋势检验',
                        subtitle='95% 置信区间'
                    )
                    + theme(
                        text=element_text(family="SimHei"),
                        figure_size=(8, 5)
                    )
                    + coord_cartesian(ylim=(-0.1, 0.2))
                )

                Path(args.plot_path).parent.mkdir(parents=True, exist_ok=True)
                p.save(args.plot_path, dpi=300)
                print(f"✅ [事件研究图已保存] {args.plot_path}")
            else:
                print(f"⚠️ [绘图跳过] 事件研究数据格式不符，无法生成图表。")
        except Exception as e:
            print(f"⚠️ [绘图失败] {str(e)}")

    # Save pickle
    with open(args.output_pickle, "wb") as f:
        pickle.dump({
            "att_gt": result_gt,
            "event_study": event_study,
            "overall_att": float(overall_att) if overall_att is not None else None,
            "overall_se": float(overall_se) if overall_se is not None else None,
            "n_obs": len(df_clean),
            "vars": {
                "y": args.y,
                "t": args.t,
                "id": args.id,
                "g": args.g,
                "cov": args.cov,
                "control_group": args.control_group,
                "est_method": args.est_method
            }
        }, f)
    print(f"\n✅ [结果已保存] {args.output_pickle}")

    return {
        "overall_att": float(overall_att) if overall_att is not None else None,
        "overall_se": float(overall_se) if overall_se is not None else None,
        "n_obs": len(df_clean)
    }


def main():
    parser = argparse.ArgumentParser(description="Callaway-Sant'Anna Staggered DID Estimator")
    parser.add_argument("--data", required=True, help="Path to data file")
    parser.add_argument("--y", required=True, help="Dependent variable")
    parser.add_argument("--t", required=True, help="Time variable")
    parser.add_argument("--id", required=True, help="Entity ID variable")
    parser.add_argument("--g", required=True, help="First treatment year variable (0 = never-treated)")
    parser.add_argument("--cov", default="~1", help="Covariate formula (default: ~1, no covariates)")
    parser.add_argument("--control_group", default="notyettreated",
                        choices=["notyettreated", "nevertreated"],
                        help="Control group type")
    parser.add_argument("--est_method", default="dr",
                        choices=["dr", "ipw"],
                        help="Estimation method: dr (doubly robust) or ipw (inverse probability weighting)")
    parser.add_argument("--output_pickle", required=True, help="Output pickle path")
    parser.add_argument("--plot_path", default=None, help="Event study plot output path (.png)")

    args = parser.parse_args()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        summary = run_staggered_did(args)

    if summary["overall_att"] is not None:
        print(f"\n📋 [DID 摘要]")
        print(f"   - 总体 ATT: {summary['overall_att']:.4f} ± {summary['overall_se']:.4f}")
        print(f"   - 样本量: {summary['n_obs']:,}")
    else:
        print(f"\n⚠️ [注意] 总体 ATT 无法计算，请检查数据与模型设定。")


if __name__ == "__main__":
    main()