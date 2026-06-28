#!/usr/bin/env python3
"""
Panel Regression: Two-Way Fixed Effects (TWFE) with Clustered Standard Errors

Usage:
    python panel_regression.py --data <path> --y <dep_var> --x <exog_vars...>
                                --entity <entity_id> --time <time_id>
                                [--cluster entity|two-way]
                                --output_pickle <path>
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


def validate_panel(df, entity_var, time_var):
    """Validate panel structure."""
    if entity_var not in df.columns:
        raise ValueError(f"Entity variable '{entity_var}' not found in data. Available: {list(df.columns)}")
    if time_var not in df.columns:
        raise ValueError(f"Time variable '{time_var}' not found in data. Available: {list(df.columns)}")

    n_entities = df[entity_var].nunique()
    n_times = df[time_var].nunique()
    n_obs = len(df)

    print(f"📋 [面板结构验证]")
    print(f"   - 个体数 (entities): {n_entities:,}")
    print(f"   - 时期数 (time periods): {n_times}")
    print(f"   - 总观测值 (observations): {n_obs:,}")
    print(f"   - 平衡面板: {'✅ 是' if n_obs == n_entities * n_times else '⚠️ 否（非平衡面板）'}")
    return n_entities, n_times, n_obs


def check_missing(df, dep_var, exog_vars):
    """Check missing data on key variables."""
    required = [dep_var] + list(exog_vars)
    missing_report = []
    for var in required:
        if var in df.columns:
            n_missing = df[var].isna().sum()
            pct = n_missing / len(df) * 100
            if n_missing > 0:
                missing_report.append(f"   - {var}: {n_missing:,} ({pct:.1f}%)")
    if missing_report:
        print("⚠️ [缺失值警告]")
        print("\n".join(missing_report))
    return df.dropna(subset=[dep_var] + list(exog_vars))


def compute_vif(X):
    """Compute VIF for exogenous variables."""
    from numpy.linalg import lstsq
    X_arr = X.values
    n_vars = X_arr.shape[1]
    vif_list = []
    for i in range(n_vars):
        y_vif = X_arr[:, i]
        X_others = np.delete(X_arr, i, axis=1)
        if len(X_others.shape) == 1:
            X_others = X_others.reshape(-1, 1)
        ones = np.ones((X_others.shape[0], 1))
        X_with_intercept = np.hstack([ones, X_others])
        try:
            _, residuals, _, _ = lstsq(X_with_intercept, y_vif, rcond=None)
            r_squared = 1 - (residuals.sum() / (len(y_vif) * np.var(y_vif) + 1e-10))
            vif = 1 / (1 - r_squared + 1e-10)
            vif_list.append((X.columns[i], min(vif, 999.9)))
        except Exception:
            vif_list.append((X.columns[i], np.nan))
    return vif_list


def run_panel_regression(args):
    """Main regression logic."""
    print(f"\n{'='*60}")
    print(f"📊 双向固定效应面板回归 (Two-Way Fixed Effects)")
    print(f"{'='*60}\n")

    # Load data
    df = load_data(args.data)

    # Validate panel structure
    n_entities, n_times, n_obs = validate_panel(df, args.entity, args.time)

    # Drop missing on key variables
    df_clean = check_missing(df, args.y, args.x)

    # Set MultiIndex for linearmodels
    # Only convert to Categorical for string/object time IDs; numeric pass through as-is
    time_dtype = df_clean[args.time].dtype
    if time_dtype == 'object' or str(time_dtype).startswith('str') or str(time_dtype).startswith('category'):
        df_clean[args.time] = pd.Categorical(df_clean[args.time])
    # else: leave numeric as-is (linearmodels accepts numeric time indices)
    df_panel = df_clean.set_index([args.entity, args.time])

    # Build dependent and exogenous
    y = df_panel[args.y]
    X = df_panel[list(args.x)]

    # Check entity-level variation
    for col in args.x:
        if col in df_panel.columns:
            within_std = df_panel.groupby(level=0)[col].transform(lambda x: x - x.mean()).std()
            if within_std.mean() < 1e-10:
                raise ValueError(f"❌ [固定效应错误] 变量 '{col}' 在个体内部无变异，无法估计双向固定效应模型")

    print(f"\n📈 [回归估计中]...")
    print(f"   - 被解释变量: {args.y}")
    print(f"   - 外生控制变量: {list(args.x)}")

    try:
        from linearmodels.panel import PanelOLS

        model = PanelOLS(
            dependent=y,
            exog=X,
            entity_effects=True,
            time_effects=True,

        )

        cluster_type = "clustered" if args.cluster == "entity" else "clustered"
        cluster_entity = True if args.cluster == "entity" else False
        cluster_time = True if args.cluster == "two-way" else False

        results = model.fit(
            cov_type="clustered",
            cluster_entity=cluster_entity,
            cluster_time=cluster_time
        )
    except Exception as e:
        print(f"❌ [回归估计失败] {str(e)}")
        sys.exit(1)

    # VIF check
    print(f"\n🔍 [共线性诊断]")
    vif_results = compute_vif(X)
    max_vif = max(v for _, v in vif_results)
    for var, vif in vif_results:
        flag = " ⚠️" if vif > 5 else ""
        print(f"   - {var}: VIF = {vif:.2f}{flag}")
    if max_vif > 5:
        print(f"⚠️ [VIF警告] 最大VIF={max_vif:.2f}，建议检查多重共线性")
    else:
        print(f"✅ [VIF检验通过] 所有VIF < 5，无严重共线性")

    # Print summary
    print(f"\n{'='*60}")
    print("### [双向固定效应面板回归结果]")
    print(f"{'='*60}\n")
    print(results.summary)

    # Save pickle
    with open(args.output_pickle, "wb") as f:
        pickle.dump(results, f)
    print(f"\n✅ [结果已保存] {args.output_pickle}")

    # Return key metrics for downstream skills
    summary = {
        "n_obs": int(n_obs),
        "n_entities": int(n_entities),
        "n_times": int(n_times),
        "r_squared_within": float(results.rsquared_within),
        "f_statistic": float(results.f_statistic.stat),
        "f_pvalue": float(results.f_statistic.pval),
        "max_vif": float(max_vif),
        "cluster_type": args.cluster,
    }
    return summary


def main():
    parser = argparse.ArgumentParser(description="Two-Way Fixed Effects Panel Regression")
    parser.add_argument("--data", required=True, help="Path to data file")
    parser.add_argument("--y", required=True, help="Dependent variable")
    parser.add_argument("--x", required=True, nargs="+", help="Exogenous control variables")
    parser.add_argument("--entity", required=True, help="Entity ID variable")
    parser.add_argument("--time", required=True, help="Time ID variable")
    parser.add_argument("--cluster", default="entity",
                        choices=["entity", "two-way"],
                        help="Cluster dimension: 'entity' (default) or 'two-way'")
    parser.add_argument("--output_pickle", required=True, help="Output pickle path")

    args = parser.parse_args()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        summary = run_panel_regression(args)

    print(f"\n📋 [回归摘要]")
    print(f"   - 样本量: N = {summary['n_obs']:,}")
    print(f"   - R² (within): {summary['r_squared_within']:.4f}")
    print(f"   - F 统计量: {summary['f_statistic']:.4f} (p = {summary['f_pvalue']:.4f})")
    print(f"   - 聚类维度: {summary['cluster_type']}")
    print(f"   - 最大 VIF: {summary['max_vif']:.2f}")


if __name__ == "__main__":
    main()