#!/usr/bin/env python3
"""
fetch_macro_data.py — 宏观经济数据获取脚本
支持 World Bank / FRED / CSMAR / Wind 数据源
"""
import argparse
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import pickle

# ── World Bank ────────────────────────────────────────────────────────────────
def fetch_worldbank(indicators, country, start, end, freq='annual'):
    try:
        import wbdata
        import datetime
    except ImportError:
        raise RuntimeError('wbdata 未安装，请运行: pip install wbdata')

    start_dt = datetime.datetime.strptime(start.split('T')[0], '%Y-%m-%d')
    end_dt   = datetime.datetime.strptime(end.split('T')[0], '%Y-%m-%d')

    indicator_list = indicators.split()
    data = wbdata.get_dataframe(
        indicator={ind: ind for ind in indicator_list},
        country=country,
        date=(start_dt, end_dt),
        freq=freq
    )
    data = data.reset_index()
    data['date'] = pd.to_datetime(data['date'])
    data['year'] = data['date'].dt.year
    for ind in indicator_list:
        if ind in data.columns:
            data[ind] = pd.to_numeric(data[ind], errors='coerce')
    return data[['year', 'country'] + [c for c in data.columns if c not in ('date','country')]]

# ── FRED ──────────────────────────────────────────────────────────────────────
def fetch_fred(indicators, start, end):
    try:
        from fred import Fred
    except ImportError:
        raise RuntimeError('fred 未安装，请运行: pip install fred')

    api_key = __import__('os').getenv('FRED_API_KEY', '')
    if not api_key:
        raise RuntimeError('请设置环境变量 FRED_API_KEY，或在 https://fred.stlouisfed.org/docs/api/api_key.html 申请')
    fred = Fred(api_key=api_key)

    indicator_list = indicators.split()
    frames = []
    for ind in indicator_list:
        series = fred.get_series(ind, observation_start=start.split('T')[0], observation_end=end.split('T')[0])
        df = pd.DataFrame({ind: series})
        frames.append(df)
    result = pd.concat(frames, axis=1).reset_index()
    result.columns = ['date'] + indicator_list
    result['date'] = pd.to_datetime(result['date'])
    result['year'] = result['date'].dt.year
    result = result.groupby('year')[indicator_list].mean().reset_index()
    return result

# ── CSMAR / 国泰安（本地文件）──────────────────────────────────────────────────
def fetch_csmar(file_path, sheet_name=0):
    try:
        import pyreadstat
    except ImportError:
        raise RuntimeError('pyreadstat 未安装，请运行: pip install pyreadstat')

    ext = file_path.lower()
    if ext.endswith('.dta'):
        df, _ = pyreadstat.read_dta(file_path)
    elif ext.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    elif ext.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f'不支持的CSMAR文件格式: {file_path}')
    return df

# ── Wind（本地终端）───────────────────────────────────────────────────────────
def fetch_wind(indicators, start, end):
    try:
        from WindPy import w
    except ImportError:
        raise RuntimeError('WindPy 未安装，请在本地Wind终端环境下使用')

    w.start()
    indicator_list = indicators.split()
    data = w.edb(','.join(indicator_list), start, end)
    result = pd.DataFrame(data.Data, index=data.Codes, columns=data.Times).T
    result['year'] = pd.to_datetime(result.index).year
    result = result.reset_index(drop=True)
    for ind in indicator_list:
        if ind in result.columns:
            result[ind] = pd.to_numeric(result[ind], errors='coerce')
    return result[['year'] + [c for c in result.columns if c != 'year']]

# ── 宏微观合并 ────────────────────────────────────────────────────────────────
def merge_with_panel(macro_df, panel_path, merge_key='year'):
    ext = panel_path.lower()
    if ext.endswith('.dta'):
        panel_df, _ = pyreadstat.read_dta(panel_path)
    elif ext.endswith(('.xlsx', '.xls')):
        panel_df = pd.read_excel(panel_path)
    elif ext.endswith('.csv'):
        panel_df = pd.read_csv(panel_path)
    else:
        raise ValueError(f'不支持的面板文件格式: {panel_path}')

    merged = panel_df.merge(macro_df, on=merge_key, how='left')
    return merged

# ── 主函数 ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='宏观经济数据获取')
    parser.add_argument('--db', required=True,
                        choices=['worldbank','fred','csmar','wind'],
                        help='数据源')
    parser.add_argument('--indicators', required=True, help='指标代码，空格分隔')
    parser.add_argument('--country', help='World Bank 国家代码，如 CN/US')
    parser.add_argument('--start', required=True, help='开始时间 YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='结束时间 YYYY-MM-DD')
    parser.add_argument('--freq', default='annual',
                        choices=['annual','quarterly','monthly'])
    parser.add_argument('--merge_with', help='与已有面板数据合并')
    parser.add_argument('--merge_key', default='year', help='合并键')
    parser.add_argument('--output_csv', required=True, help='输出CSV路径')
    parser.add_argument('--output_pickle', help='输出pickle路径（可选）')
    args = parser.parse_args()

    print(f"\n🌍 [宏观经济数据获取]")
    print(f"   数据源: {args.db.upper()}")
    print(f"   指标: {args.indicators}")
    print(f"   时间: {args.start} — {args.end}")

    if args.db == 'worldbank':
        if not args.country:
            raise ValueError('--country 必须指定（World Bank）')
        df = fetch_worldbank(args.indicators, args.country, args.start, args.end, args.freq)
    elif args.db == 'fred':
        df = fetch_fred(args.indicators, args.start, args.end)
    elif args.db == 'csmar':
        if not args.merge_with:
            raise ValueError('--csmar 需要 --merge_with 指定本地文件路径')
        df = fetch_csmar(args.merge_with)
    elif args.db == 'wind':
        if not args.merge_with:
            raise ValueError('--wind 需要 --merge_with 指定本地文件路径')
        df = fetch_wind(args.indicators, args.start, args.end)

    if args.merge_with:
        print(f"   宏微观合并: {args.merge_with}（按 {args.merge_key}）")
        df = merge_with_panel(df, args.merge_with, args.merge_key)

    print(f"\n✅ 数据获取完成")
    print(f"   样本量: {len(df)} 行 × {len(df.columns)} 列")
    print(f"   列名: {', '.join(df.columns.tolist())}")

    df.to_csv(args.output_csv, index=False, encoding='utf-8-sig')
    print(f"   已保存: {args.output_csv}")

    if args.output_pickle:
        with open(args.output_pickle, 'wb') as f:
            pickle.dump(df, f)
        print(f"   已保存(pickle): {args.output_pickle}")

if __name__ == '__main__':
    main()