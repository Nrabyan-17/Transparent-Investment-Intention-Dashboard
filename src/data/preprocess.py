"""
02 - Preprocessing Script
Dataset FAR-Trans: Transparent Investment Intention Analysis

Script ini melakukan preprocessing data FAR-Trans untuk modeling:
1. Load data menggunakan src.data.load_data
2. Terapkan treatment dari data_quality_report.csv
3. Feature engineering dari data transaksional
4. Split train/test
5. Simpan ke data/processed/

Cara menjalankan:
    python src/data/preprocess.py
    
    Atau dari notebook:
    %run ../src/data/preprocess.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Output directory
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Import data loader
from src.data.load_data import load_all


def step1_load_data():
    """Step 1: Load semua data FAR-Trans."""
    print("\n" + "=" * 60)
    print("STEP 1: Loading Data")
    print("=" * 60)
    
    data = load_all(verbose=True)
    return data['customers'], data['assets'], data['transactions'], data['prices']


def step2_clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2: Cleaning customer data.
    
    Treatment dari data_quality_report.csv:
    - Deduplikasi: ambil snapshot terbaru per customerID
    - Predicted_* risk labels -> hanya gunakan 4 label asli
    - Risk level Not_Available -> drop
    - Placeholder date 2000-01-01 -> replace NaN, flag sebagai feature
    """
    print("\n" + "=" * 60)
    print("STEP 2: Cleaning Customer Data")
    print("=" * 60)
    
    print(f"  Sebelum cleaning: {len(customers):,} rows")
    
    # 2a. Deduplikasi -- ambil snapshot terbaru per customerID
    customers_clean = (
        customers
        .sort_values('timestamp')
        .groupby('customerID', observed=True)
        .last()
        .reset_index()
    )
    print(f"  Setelah deduplikasi: {len(customers_clean):,} rows "
          f"(dihapus {len(customers) - len(customers_clean):,})")
    
    # 2b. Handle Predicted_* risk labels -- hanya gunakan 4 label asli
    original_labels = ['Conservative', 'Income', 'Balanced', 'Aggressive']
    before = len(customers_clean)
    customers_clean = customers_clean[
        customers_clean['riskLevel'].isin(original_labels)
    ].copy()
    print(f"  Setelah filter riskLevel (4 label asli): {len(customers_clean):,} rows "
          f"(dihapus {before - len(customers_clean):,} Predicted_*/Not_Available)")
    
    # 2c. Handle placeholder date 2000-01-01
    if 'lastQuestionnaireDate' in customers_clean.columns:
        customers_clean['lastQuestionnaireDate'] = pd.to_datetime(
            customers_clean['lastQuestionnaireDate'], errors='coerce'
        )
        placeholder_mask = customers_clean['lastQuestionnaireDate'] == pd.Timestamp('2000-01-01')
        n_placeholder = placeholder_mask.sum()
        customers_clean.loc[placeholder_mask, 'lastQuestionnaireDate'] = pd.NaT
        
        # Buat feature: has_questionnaire (1 = punya, 0 = tidak)
        customers_clean['has_questionnaire'] = (
            customers_clean['lastQuestionnaireDate'].notna()
        ).astype(int)
        
        print(f"  Placeholder dates 2000-01-01: {n_placeholder:,} -> replaced with NaT")
        print(f"  Feature 'has_questionnaire' created")
    
    # 2d. Distribusi risk level
    print(f"\n  Distribusi riskLevel:")
    for level, count in customers_clean['riskLevel'].value_counts().items():
        pct = count / len(customers_clean) * 100
        print(f"    {level}: {count:,} ({pct:.1f}%)")
    
    return customers_clean


def step3_clean_assets(assets: pd.DataFrame) -> pd.DataFrame:
    """
    Step 3: Cleaning asset data.
    
    Treatment:
    - Missing sector -> imputasi 'Unknown'
    - Missing industry -> imputasi 'Unknown'
    - Deduplikasi aset (ambil terbaru)
    """
    print("\n" + "=" * 60)
    print("STEP 3: Cleaning Asset Data")
    print("=" * 60)
    
    # Deduplikasi aset
    if 'timestamp' in assets.columns:
        assets_clean = (
            assets
            .sort_values('timestamp')
            .groupby('ISIN', observed=True)
            .last()
            .reset_index()
        )
    else:
        assets_clean = assets.drop_duplicates(subset='ISIN', keep='last').copy()
    
    print(f"  Unique assets: {len(assets_clean):,}")
    
    # Imputasi missing sector dan industry
    if 'sector' in assets_clean.columns:
        n_missing = assets_clean['sector'].isna().sum()
        assets_clean['sector'] = assets_clean['sector'].fillna('Unknown')
        print(f"  Missing sector filled: {n_missing:,}")
    
    if 'industry' in assets_clean.columns:
        n_missing = assets_clean['industry'].isna().sum()
        assets_clean['industry'] = assets_clean['industry'].fillna('Unknown')
        print(f"  Missing industry filled: {n_missing:,}")
    
    return assets_clean


def step4_clean_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Step 4: Cleaning transaction data.
    
    Treatment:
    - Outliers extreme (>Q99) -> winsorization
    """
    print("\n" + "=" * 60)
    print("STEP 4: Cleaning Transaction Data")
    print("=" * 60)
    
    print(f"  Total transactions: {len(transactions):,}")
    
    # Winsorization untuk totalValue
    if 'totalValue' in transactions.columns:
        q99 = transactions['totalValue'].quantile(0.99)
        n_outliers = (transactions['totalValue'] > q99).sum()
        transactions_clean = transactions.copy()
        transactions_clean.loc[transactions_clean['totalValue'] > q99, 'totalValue'] = q99
        print(f"  Outliers totalValue (>{q99:,.0f}): {n_outliers:,} -> winsorized")
    else:
        transactions_clean = transactions.copy()
    
    return transactions_clean


def step5_feature_engineering(
    customers: pd.DataFrame,
    assets: pd.DataFrame,
    transactions: pd.DataFrame
) -> pd.DataFrame:
    """
    Step 5: Feature Engineering.
    
    Membuat fitur per customer dari data transaksional:
    
    Per Customer:
    - Profil Dasar
        - customerType
        - investmentCapacity
        - has_questionnaire
    - Perilaku Transaksi
        - total_transactions
        - buy_count / sell_count / buy_ratio
        - avg_transaction_value
        - total_invested / total_sold
        - unique_assets_traded
        - preferred_channel
    - Preferensi Aset
        - pct_stocks / pct_bonds / pct_mtf
        - portfolio_diversity (nunique ISIN)
    - Temporal
        - investment_period (last - first transaction)
        - avg_days_between_transactions
    """
    print("\n" + "=" * 60)
    print("STEP 5: Feature Engineering")
    print("=" * 60)
    
    # Gabung transactions dengan asset info untuk category
    tx_with_asset = transactions.merge(
        assets[['ISIN', 'assetCategory']],
        on='ISIN',
        how='left'
    )
    
    # --- Perilaku Transaksi ---
    print("  Menghitung fitur perilaku transaksi...")
    
    # Total transaksi per customer
    tx_count = tx_with_asset.groupby('customerID').size().rename('total_transactions')
    
    # Buy/Sell counts dan ratio
    buy_sell = tx_with_asset.groupby(['customerID', 'transactionType']).size().unstack(fill_value=0)
    if 'Buy' not in buy_sell.columns:
        buy_sell['Buy'] = 0
    if 'Sell' not in buy_sell.columns:
        buy_sell['Sell'] = 0
    buy_sell = buy_sell.rename(columns={'Buy': 'buy_count', 'Sell': 'sell_count'})
    buy_sell['buy_ratio'] = buy_sell['buy_count'] / (buy_sell['buy_count'] + buy_sell['sell_count'])
    
    # Rata-rata nilai transaksi
    avg_val = tx_with_asset.groupby('customerID')['totalValue'].mean().rename('avg_transaction_value')
    
    # Total invested dan total sold
    buy_mask = tx_with_asset['transactionType'] == 'Buy'
    sell_mask = tx_with_asset['transactionType'] == 'Sell'
    
    total_invested = tx_with_asset[buy_mask].groupby('customerID')['totalValue'].sum().rename('total_invested')
    total_sold = tx_with_asset[sell_mask].groupby('customerID')['totalValue'].sum().rename('total_sold')
    
    # Unique assets traded
    unique_assets = tx_with_asset.groupby('customerID')['ISIN'].nunique().rename('unique_assets_traded')
    
    # Preferred channel
    def get_preferred_channel(group):
        return group['channel'].mode().iloc[0] if len(group['channel'].mode()) > 0 else 'Unknown'
    
    preferred_channel = tx_with_asset.groupby('customerID').apply(
        get_preferred_channel, include_groups=False
    ).rename('preferred_channel')
    
    # --- Preferensi Aset ---
    print("  Menghitung fitur preferensi aset...")
    
    asset_pcts = tx_with_asset.groupby(['customerID', 'assetCategory']).size().unstack(fill_value=0)
    total_per_customer = asset_pcts.sum(axis=1)
    
    for cat in ['Stock', 'Bond', 'MTF']:
        col_name = f'pct_{cat.lower()}'
        if cat in asset_pcts.columns:
            asset_pcts[col_name] = asset_pcts[cat] / total_per_customer
        else:
            asset_pcts[col_name] = 0.0
    
    asset_pcts = asset_pcts[['pct_stock', 'pct_bond', 'pct_mtf']]
    
    # Portfolio diversity
    portfolio_div = unique_assets.rename('portfolio_diversity')
    
    # --- Temporal ---
    print("  Menghitung fitur temporal...")
    
    if 'timestamp' in tx_with_asset.columns:
        tx_with_asset['timestamp'] = pd.to_datetime(tx_with_asset['timestamp'], errors='coerce')
        
        temporal = tx_with_asset.groupby('customerID')['timestamp'].agg(
            first_transaction='min',
            last_transaction='max'
        )
        temporal['investment_period_days'] = (
            temporal['last_transaction'] - temporal['first_transaction']
        ).dt.days
        
        # Rata-rata hari antar transaksi
        def avg_days_between(group):
            dates = group['timestamp'].sort_values()
            if len(dates) < 2:
                return 0
            diffs = dates.diff().dropna().dt.days
            return diffs.mean() if len(diffs) > 0 else 0
        
        avg_gap = tx_with_asset.groupby('customerID').apply(
            avg_days_between, include_groups=False
        ).rename('avg_days_between_transactions')
        
        temporal = temporal[['investment_period_days']].join(avg_gap)
    else:
        temporal = pd.DataFrame(index=tx_count.index)
        temporal['investment_period_days'] = 0
        temporal['avg_days_between_transactions'] = 0
    
    # --- Gabung semua fitur transaksi ---
    print("  Menggabungkan semua fitur...")
    
    tx_features = (
        tx_count
        .to_frame()
        .join(buy_sell[['buy_count', 'sell_count', 'buy_ratio']])
        .join(avg_val)
        .join(total_invested)
        .join(total_sold)
        .join(unique_assets)
        .join(preferred_channel)
        .join(asset_pcts)
        .join(temporal)
    )
    
    # Fill NaN (beberapa customer mungkin hanya buy atau hanya sell)
    tx_features = tx_features.fillna(0)
    
    # --- Gabung dengan data customer ---
    print("  Menggabungkan dengan profil customer...")
    
    # Kolom profil yang digunakan
    customer_cols = ['customerID', 'customerType', 'riskLevel', 
                     'investmentCapacity', 'has_questionnaire']
    
    available_cols = [c for c in customer_cols if c in customers.columns]
    
    final_df = customers[available_cols].merge(
        tx_features,
        on='customerID',
        how='inner'  # Hanya customer yang punya transaksi
    )
    
    print(f"\n  Final dataset shape: {final_df.shape}")
    print(f"  Customers with transactions: {len(final_df):,}")
    print(f"  Features: {len(final_df.columns) - 2}")  # -2 for customerID and riskLevel
    
    return final_df


def step6_encode_and_split(df: pd.DataFrame, target_col: str = 'riskLevel', 
                           test_size: float = 0.2, random_state: int = 42):
    """
    Step 6: Encoding dan Train/Test Split.
    
    - Label Encoding untuk variabel kategorik
    - Stratified train/test split
    - Simpan ke data/processed/
    """
    print("\n" + "=" * 60)
    print("STEP 6: Encoding & Train/Test Split")
    print("=" * 60)
    
    # Hapus customerID (bukan feature)
    df_encoded = df.drop(columns=['customerID']).copy()
    
    # Identifikasi kolom kategorik
    cat_cols = df_encoded.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Hapus target dari list encoding
    if target_col in cat_cols:
        cat_cols.remove(target_col)
    
    # Label Encoding untuk setiap kolom kategorik
    encoders = {}
    for col in cat_cols:
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
        encoders[col] = le
        print(f"  Encoded '{col}': {len(le.classes_)} classes -> {list(le.classes_)}")
    
    # Encode target variable
    le_target = LabelEncoder()
    df_encoded[target_col] = le_target.fit_transform(df_encoded[target_col])
    print(f"  Target '{target_col}' encoded: {list(le_target.classes_)}")
    print(f"    -> Mapping: {dict(zip(le_target.classes_, le_target.transform(le_target.classes_)))}")
    
    # Split features dan target
    X = df_encoded.drop(columns=[target_col])
    y = df_encoded[target_col]
    
    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"\n  Train set: {X_train.shape[0]:,} samples")
    print(f"  Test set:  {X_test.shape[0]:,} samples")
    
    # Distribusi target di train dan test
    print(f"\n  Train target distribution:")
    for cls_idx, cls_name in enumerate(le_target.classes_):
        count = (y_train == cls_idx).sum()
        pct = count / len(y_train) * 100
        print(f"    {cls_name} ({cls_idx}): {count:,} ({pct:.1f}%)")
    
    print(f"\n  Test target distribution:")
    for cls_idx, cls_name in enumerate(le_target.classes_):
        count = (y_test == cls_idx).sum()
        pct = count / len(y_test) * 100
        print(f"    {cls_name} ({cls_idx}): {count:,} ({pct:.1f}%)")
    
    return X_train, X_test, y_train, y_test, le_target, encoders


def step7_save(X_train, X_test, y_train, y_test):
    """Step 7: Simpan ke data/processed/."""
    print("\n" + "=" * 60)
    print("STEP 7: Saving to data/processed/")
    print("=" * 60)
    
    X_train.to_csv(PROCESSED_DIR / 'X_train.csv', index=False)
    X_test.to_csv(PROCESSED_DIR / 'X_test.csv', index=False)
    y_train.to_csv(PROCESSED_DIR / 'y_train.csv', index=False, header=True)
    y_test.to_csv(PROCESSED_DIR / 'y_test.csv', index=False, header=True)
    
    print(f"  [OK] X_train.csv: {X_train.shape}")
    print(f"  [OK] X_test.csv:  {X_test.shape}")
    print(f"  [OK] y_train.csv: {y_train.shape}")
    print(f"  [OK] y_test.csv:  {y_test.shape}")
    print(f"  Saved to: {PROCESSED_DIR}")


def main():
    """Main preprocessing pipeline."""
    print("=" * 60)
    print("02 - PREPROCESSING PIPELINE")
    print("Dataset: FAR-Trans")
    print("Target: riskLevel (4 classes)")
    print("=" * 60)
    
    # Step 1: Load data
    customers, assets, transactions, prices = step1_load_data()
    
    # Step 2: Clean customers
    customers_clean = step2_clean_customers(customers)
    
    # Step 3: Clean assets
    assets_clean = step3_clean_assets(assets)
    
    # Step 4: Clean transactions
    transactions_clean = step4_clean_transactions(transactions)
    
    # Step 5: Feature engineering
    final_df = step5_feature_engineering(
        customers_clean, assets_clean, transactions_clean
    )
    
    # Step 6: Encode & split
    X_train, X_test, y_train, y_test, le_target, encoders = step6_encode_and_split(final_df)
    
    # Step 7: Save
    step7_save(X_train, X_test, y_train, y_test)
    
    print("\n" + "=" * 60)
    print("[OK] PREPROCESSING COMPLETE!")
    print("=" * 60)
    
    return X_train, X_test, y_train, y_test


if __name__ == '__main__':
    main()
