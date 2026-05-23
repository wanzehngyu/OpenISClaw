#!/usr/bin/env python3
"""
IV-Estimator: Two-Stage Least Squares (2SLS) Instrumental Variable Regression

Usage:
    python iv_regression.py --data <path> --y <dep_var>
                            [--exog <exog_vars...>]
                            --endog <endog_vars...>
                            --iv <instrument_vars...>
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


def check_sample_size(n_obs, n_exog, n_iv):
    """Check if sample size meets minimum requirement."""
    required = 10 * (n_exog + n_iv)
    if n_obs < required:
        print(f"⚠️ [样本量警告] 当前有效观测值仅为 {n_obs}，")
        print(f"   建议针对本模型推荐的最低样本量为 {required}。")
        print(f"   样本量偏低可能导致标准误估计不稳定。")
        return False
    return True


def compute_first_stage_f_stats(endog_df, exog_df, iv_df):
    """Compute first-stage partial F-statistics for each endogenous variable."""
    from numpy.linalg import lstsq

    results = {}
    iv_matrix = iv_df.values
    n_iv = iv_matrix.shape[1]

    for col in endog_df.columns:
        y = endog_df[col].values
        X = exog_df.values
        X_with_iv = np.hstack([X, iv_matrix]) if X.size > 0 else iv_matrix

        # Compute partial R² / F-stat
        # Regress IV on exogenous and compute R² for instruments predicting endog
        ones = np.ones((len(y), 1))
        Z = np.hstack([ones, X_with_iv]) if X.size > 0 else iv_matrix

        try:
            # Full model
            coeffs, residuals_full, rank_full, s_full = lstsq(Z, y, rcond=None)
            y_pred_full = Z @ coeffs
            ss_full = np.sum((y_pred_full - y.mean()) ** 2)

            # Restricted model (without instruments)
            Z_reduced = np.ones((len(y), 1)) if X.size == 0 else np.hstack([np.ones((len(y), 1)), X])
            coeffs_red, residuals_red, rank_red, s_red = lstsq(Z_reduced, y, rcond=None)
            y_pred_red = Z_reduced @ coeffs_red
            ss_reduced = np.sum((y_pred_red - y.mean()) ** 2)

            # Partial F = (SS_reduced - SS_full) / (n_iv) / (SS_full / (n - k - 1))
            df1 = n_iv
            df2 = len(y) - Z.shape[1] - 1
            if df2 <= 0:
                df2 = 1
            f_stat = ((ss_reduced - ss_full) / df1) / (s_full.sum() / df2) if s_full.sum() > 0 else 0.0
            results[col] = max(f_stat, 0.0)
        except Exception:
            results[col] = np.nan
    return results


def run_iv_regression(args):
    """Main IV regression logic."""
    print(f"\n{'='*60}")
    print(f"⚖️ IV-Estimator: 两阶段最小二乘法（2SLS）工具变量回归")
    print(f"{'='*60}\n")

    # Load data
    df = load_data(args.data)

    # Check columns
    all_vars = [args.y] + (args.exog or []) + args.endog + args.iv
    missing = [v for v in all_vars if v not in df.columns]
    if missing:
        raise ValueError(f"变量未找到: {missing}。可用变量: {list(df.columns)}")

    # Drop missing
    required_cols = [args.y] + (args.exog or []) + args.endog + args.iv
    df_clean = df.dropna(subset=required_cols)
    n_obs = len(df_clean)
    print(f"📋 [样本信息]")
    print(f"   - 有效观测值: {n_obs:,}")
    print(f"   - 因变量: {args.y}")
    print(f"   - 内生解释变量: {args.endog}")
    print(f"   - 外生控制变量: {args.exog or '仅常数项'}")
    print(f"   - 工具变量: {args.iv}")

    # Check sample size
    n_exog = len(args.exog) if args.exog else 0
    n_iv = len(args.iv)
    check_sample_size(n_obs, n_exog, n_iv)

    # Prepare arrays
    endog = df_clean[args.endog]
    iv = df_clean[args.iv]
    exog = df_clean[args.exog] if args.exog else None

    print(f"\n📈 [估计中]...")

    try:
        from linearmodels.iv import IV2SLS

        if exog is not None and len(exog.columns) > 0:
            model = IV2SLS(
                dependent=df_clean[args.y],
                exog=exog,
                endog=endog,
                instruments=iv
            )
        else:
            model = IV2SLS(
                dependent=df_clean[args.y],
                exog=None,
                endog=endog,
                instruments=iv
            )

        results = model.fit(cov_type="robust")
    except Exception as e:
        print(f"❌ [2SLS估计失败] {str(e)}")
        sys.exit(1)

    # First-stage diagnostics
    print(f"\n🔍 [第一阶段诊断]")
    f_stats = compute_first_stage_f_stats(endog, exog if exog is not None else pd.DataFrame(index=endog.index), iv)
    for var, f_stat in f_stats.items():
        flag = " ⚠️ 弱IV" if f_stat < 10 else " ✅ 通过"
        print(f"   - {var}: 偏 F = {f_stat:.4f}{flag}")

    # Overall weak IV check
    weak_iv_warning = all(f < 10 for f in f_stats.values())

    # Save pickle
    with open(args.output_pickle, "wb") as f:
        pickle.dump({
            "results": results,
            "f_stats": f_stats,
            "weak_iv_warning": weak_iv_warning,
            "n_obs": n_obs,
            "vars": {
                "y": args.y,
                "endog": args.endog,
                "exog": args.exog or [],
                "iv": args.iv
            }
        }, f)
    print(f"\n✅ [结果已保存] {args.output_pickle}")

    # Print summary
    print(f"\n{'='*60}")
    print("### [IV回归结果]")
    print(f"{'='*60}\n")
    print(results.summary.to_string())

    return {
        "n_obs": n_obs,
        "f_stats": f_stats,
        "weak_iv_warning": weak_iv_warning,
        "has_sargan": hasattr(results, "sargan") and results.sargan is not None
    }


def main():
    parser = argparse.ArgumentParser(description="Two-Stage Least Squares IV Regression")
    parser.add_argument("--data", required=True, help="Path to data file")
    parser.add_argument("--y", required=True, help="Dependent variable")
    parser.add_argument("--exog", nargs="*", default=[], help="Exogenous control variables")
    parser.add_argument("--endog", required=True, nargs="+", help="Endogenous explanatory variables")
    parser.add_argument("--iv", required=True, nargs="+", help="Instrumental variables")
    parser.add_argument("--output_pickle", required=True, help="Output pickle path")

    args = parser.parse_args()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        summary = run_iv_regression(args)

    print(f"\n📋 [IV诊断摘要]")
    for var, f in summary["f_stats"].items():
        status = "✅" if f >= 10 else "⚠️"
        print(f"   {status} {var}: F = {f:.4f}")
    if summary["weak_iv_warning"]:
        print(f"\n⚠️ [警告] 所有内生变量的第一阶段F统计量均 < 10，存在弱工具变量风险。")


if __name__ == "__main__":
    main()