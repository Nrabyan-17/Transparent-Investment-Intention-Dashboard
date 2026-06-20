"""
generate_sample_data.py
=======================
Script untuk generate sample CSV data untuk populate Data Warehouse.

Output: 4 CSV files di data/raw/ yang siap di-load oleh ETL script.

Cara pakai:
    python scripts/generate_sample_data.py

Note: Data ini SIMULASI/SAMPLE untuk demonstrasi DW.
Untuk production, ganti dengan data riil dari FAR-Trans atau core banking.
"""

import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Reproducibility
random.seed(42)
np.random.seed(42)

# Konfigurasi (bisa di-adjust)
NUM_CUSTOMERS = 500       # Sample size customer
NUM_ASSETS = 50           # Sample stocks/assets
NUM_TRANSACTIONS = 3000   # Sample transactions
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2023, 12, 31)

# ============================================================
# 1. Generate Customer Data
# ============================================================
def generate_customers(n=NUM_CUSTOMERS):
    """Generate sample customer data."""
    customer_types = ['Mass', 'Premium', 'Professional', 'Legal Entity', 'Inactive']
    risk_levels = ['Conservative', 'Income', 'Balanced', 'Aggressive']
    capacities = ['<30K', '30K-80K', '80K-300K', '>300K']

    # Probabilities (realistic distribution)
    type_probs = [0.55, 0.25, 0.10, 0.05, 0.05]
    risk_probs = [0.30, 0.20, 0.30, 0.20]
    cap_probs  = [0.40, 0.30, 0.20, 0.10]

    customers = []
    for i in range(n):
        cust = {
            'customer_id': f'CUST{i+1:05d}',
            'customer_type': np.random.choice(customer_types, p=type_probs),
            'risk_level': np.random.choice(risk_levels, p=risk_probs),
            'investment_capacity': np.random.choice(capacities, p=cap_probs),
            'has_questionnaire': np.random.choice([True, False], p=[0.85, 0.15]),
            'customer_segment': f'Segment-{random.randint(1, 5)}'
        }
        customers.append(cust)

    return pd.DataFrame(customers)


# ============================================================
# 2. Generate Asset Data
# ============================================================
def generate_assets(n=NUM_ASSETS):
    """Generate sample asset/stock data."""
    sectors = ['Technology', 'Financial Services', 'Healthcare',
               'Consumer Cyclical', 'Energy', 'Industrials',
               'Real Estate', 'Communication Services', 'Utilities']
    industries = {
        'Technology': ['Software', 'Hardware', 'Semiconductors'],
        'Financial Services': ['Banking', 'Insurance', 'Investment'],
        'Healthcare': ['Pharma', 'Biotech', 'Medical Devices'],
        'Consumer Cyclical': ['Retail', 'Automotive', 'Apparel'],
        'Energy': ['Oil & Gas', 'Renewable'],
        'Industrials': ['Manufacturing', 'Aerospace'],
        'Real Estate': ['REIT', 'Property Dev'],
        'Communication Services': ['Telecom', 'Media'],
        'Utilities': ['Electric', 'Gas']
    }
    categories = ['Stock', 'Bond', 'Fund', 'ETF']
    cat_probs = [0.70, 0.15, 0.10, 0.05]
    markets = ['IDX', 'NYSE', 'NASDAQ', 'LSE']

    assets = []
    for i in range(n):
        sector = random.choice(sectors)
        asset = {
            'ISIN': f'ISIN{i+1:08d}AB',
            'asset_name': f'Asset Company {i+1} {sector[:5]}',
            'asset_category': np.random.choice(categories, p=cat_probs),
            'sector': sector,
            'industry': random.choice(industries[sector]),
            'market_id': random.choice(markets)
        }
        assets.append(asset)

    return pd.DataFrame(assets)


# ============================================================
# 3. Generate Date Dimension
# ============================================================
def generate_dates(start=START_DATE, end=END_DATE):
    """Generate complete date dimension from start to end."""
    dates = []
    current = start
    while current <= end:
        d = {
            'date_key': int(current.strftime('%Y%m%d')),
            'full_date': current.strftime('%Y-%m-%d'),
            'year': current.year,
            'quarter': (current.month - 1) // 3 + 1,
            'month': current.month,
            'month_name': current.strftime('%B'),
            'day_of_month': current.day,
            'day_of_week': current.strftime('%A'),
            'is_weekend': current.weekday() >= 5
        }
        dates.append(d)
        current += timedelta(days=1)

    return pd.DataFrame(dates)


# ============================================================
# 4. Generate Channel Dimension
# ============================================================
def generate_channels():
    """Generate channel dimension (static, hanya 3 channels)."""
    channels = [
        {
            'channel_name': 'Branch',
            'channel_type': 'Physical',
            'is_digital': False,
            'description': 'Transaksi tatap muka di cabang bank'
        },
        {
            'channel_name': 'Internet Banking',
            'channel_type': 'Digital',
            'is_digital': True,
            'description': 'Transaksi via aplikasi mobile/web banking'
        },
        {
            'channel_name': 'Phone Banking',
            'channel_type': 'Hybrid',
            'is_digital': False,
            'description': 'Transaksi via telepon ke customer service'
        }
    ]
    return pd.DataFrame(channels)


# ============================================================
# 5. Generate Fact Transactions
# ============================================================
def generate_transactions(customers_df, assets_df, channels_df,
                          n=NUM_TRANSACTIONS):
    """Generate sample transaction data."""
    transactions = []

    # Channel distribution (Internet Banking dominan = 70%)
    channel_probs = [0.20, 0.70, 0.10]  # Branch, IB, Phone

    for i in range(n):
        customer_id = random.choice(customers_df['customer_id'].tolist())
        ISIN = random.choice(assets_df['ISIN'].tolist())
        channel_name = np.random.choice(
            channels_df['channel_name'].tolist(), p=channel_probs)

        # Random date dalam range
        random_days = random.randint(0, (END_DATE - START_DATE).days)
        trans_date = START_DATE + timedelta(days=random_days)

        # Realistic transaction values
        units = round(random.uniform(1, 1000), 4)
        unit_price = round(random.uniform(10, 5000), 4)
        total_value = round(units * unit_price, 2)

        # BUY 60%, SELL 40% (accumulator pattern)
        trans_type = np.random.choice(['BUY', 'SELL'], p=[0.6, 0.4])

        t = {
            'customer_id': customer_id,
            'ISIN': ISIN,
            'transaction_date': trans_date.strftime('%Y-%m-%d'),
            'channel_name': channel_name,
            'transaction_type': trans_type,
            'total_value': total_value,
            'units': units,
            'unit_price': unit_price
        }
        transactions.append(t)

    return pd.DataFrame(transactions)


# ============================================================
# MAIN: Generate all data and save to CSV
# ============================================================
def main():
    print("="*60)
    print("GENERATING SAMPLE DATA UNTUK DW")
    print("="*60)

    # Setup output folder
    output_dir = Path(__file__).parent.parent / 'data' / 'raw'
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output folder: {output_dir.absolute()}\n")

    # Generate customers
    print(f"1. Generating {NUM_CUSTOMERS} customers...")
    customers_df = generate_customers()
    customers_df.to_csv(output_dir / 'customer_information.csv', index=False)
    print(f"   ✓ Saved: customer_information.csv ({len(customers_df)} rows)")
    print(f"   Distribution by risk_level:")
    for level, count in customers_df['risk_level'].value_counts().items():
        print(f"     - {level}: {count} ({count/len(customers_df)*100:.1f}%)")

    # Generate assets
    print(f"\n2. Generating {NUM_ASSETS} assets...")
    assets_df = generate_assets()
    assets_df.to_csv(output_dir / 'asset_information.csv', index=False)
    print(f"   ✓ Saved: asset_information.csv ({len(assets_df)} rows)")

    # Generate channels
    print(f"\n3. Generating 3 channels...")
    channels_df = generate_channels()
    channels_df.to_csv(output_dir / 'channel_information.csv', index=False)
    print(f"   ✓ Saved: channel_information.csv ({len(channels_df)} rows)")

    # Generate dates
    print(f"\n4. Generating date dimension...")
    dates_df = generate_dates()
    dates_df.to_csv(output_dir / 'date_dimension.csv', index=False)
    print(f"   ✓ Saved: date_dimension.csv ({len(dates_df)} rows)")
    print(f"   Date range: {dates_df['full_date'].min()} to {dates_df['full_date'].max()}")

    # Generate transactions
    print(f"\n5. Generating {NUM_TRANSACTIONS} transactions...")
    transactions_df = generate_transactions(customers_df, assets_df, channels_df)
    transactions_df.to_csv(output_dir / 'transactions.csv', index=False)
    print(f"   ✓ Saved: transactions.csv ({len(transactions_df)} rows)")
    print(f"   Transaction type distribution:")
    for ttype, count in transactions_df['transaction_type'].value_counts().items():
        print(f"     - {ttype}: {count} ({count/len(transactions_df)*100:.1f}%)")
    print(f"   Total volume: EUR {transactions_df['total_value'].sum():,.2f}")

    print("\n" + "="*60)
    print("✅ SAMPLE DATA GENERATION COMPLETE")
    print("="*60)
    print(f"\nFiles ready di: {output_dir.absolute()}")
    print("Next step: jalankan etl_to_mysql.py untuk load ke MySQL")


if __name__ == '__main__':
    main()
