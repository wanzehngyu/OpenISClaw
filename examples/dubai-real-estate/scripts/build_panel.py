#!/usr/bin/env python3
"""
build_panel.py — 迪拜二手房数据聚合为社区-季度面板
"""
import pandas as pd
import numpy as np
import argparse

def build_panel(secondary_csv, area_csv, output_csv):
    # Load secondary sales
    df = pd.read_csv(secondary_csv)
    df['date_listed'] = pd.to_datetime(df['date_listed'])
    df['quarter'] = df['date_listed'].dt.to_period('Q').astype(str)

    # Aggregate to community × quarter
    panel = df.groupby(['community', 'quarter']).agg(
        avg_price_usd=('price_usd', 'mean'),
        avg_price_per_sqft=('price_per_sqft_usd', 'mean'),
        n_transactions=('id', 'count'),
        avg_area=('area_sqft', 'mean'),
        avg_bedrooms=('bedrooms', 'mean'),
        pct_furnished=('furnishing', lambda x: (x == 'fully_furnished').mean()),
        avg_metro_dist=('metro_distance_min', 'mean'),
        pct_freehold=('is_freehold', 'mean'),
    ).reset_index()

    panel['ln_price_per_sqft'] = np.log(panel['avg_price_per_sqft'])

    # Load area_prices for mortgage rate (same for all communities at each time point)
    area = pd.read_csv(area_csv)
    area['quarter'] = pd.to_datetime(area['year_month']).dt.to_period('Q').astype(str)
    rate_df = area[['community', 'quarter', 'avg_mortgage_rate_pct', 'cbuae_base_rate_pct']].drop_duplicates(
        subset=['quarter']
    )[['quarter', 'avg_mortgage_rate_pct', 'cbuae_base_rate_pct']]

    # Merge rate (same for all communities per quarter)
    panel = panel.merge(rate_df, on='quarter', how='left')

    print(f"Panel: {panel.shape[0]} obs × {panel.shape[1]} vars")
    print(f"  Communities: {panel['community'].nunique()}")
    print(f"  Quarters: {panel['quarter'].nunique()}")
    panel.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Saved → {output_csv}")

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--secondary', required=True)
    ap.add_argument('--area', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    build_panel(args.secondary, args.area, args.output)