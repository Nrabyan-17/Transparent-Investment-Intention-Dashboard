"""
Module untuk loading dataset FAR-Trans.

Dataset FAR-Trans terdiri dari:
- customer_information.csv: Profil investor
- asset_information.csv: Informasi aset
- transactions.csv: Transaksi buy/sell
- close_prices.csv: Harga harian
- limit_prices.csv: Analisis harga
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict


def _get_data_dir() -> Path:
    """Menentukan path ke folder data/raw/."""
    # Cek beberapa kemungkinan lokasi
    candidates = [
        Path(__file__).resolve().parent.parent.parent / 'data' / 'raw',
        Path.cwd() / 'data' / 'raw',
        Path.cwd().parent / 'data' / 'raw',
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Folder data/raw/ tidak ditemukan!")


def load_customers(data_dir: Optional[Path] = None, verbose: bool = False) -> pd.DataFrame:
    """Load customer_information.csv."""
    if data_dir is None:
        data_dir = _get_data_dir()
    
    filepath = data_dir / 'customer_information.csv'
    df = pd.read_csv(filepath)
    
    if verbose:
        print(f"[OK] Customers loaded: {len(df):,} rows x {len(df.columns)} cols")
        print(f"  - Unique customers: {df['customerID'].nunique():,}")
        dupes = len(df) - df['customerID'].nunique()
        print(f"  - Duplicates (multiple snapshots): {dupes:,}")

    
    return df


def load_assets(data_dir: Optional[Path] = None, verbose: bool = False) -> pd.DataFrame:
    """Load asset_information.csv."""
    if data_dir is None:
        data_dir = _get_data_dir()
    
    filepath = data_dir / 'asset_information.csv'
    df = pd.read_csv(filepath)
    
    if verbose:
        print(f"[OK] Assets loaded: {len(df):,} rows x {len(df.columns)} cols")
        print(f"  - Unique ISINs: {df['ISIN'].nunique():,}")
        cats = df['assetCategory'].value_counts().to_dict()
        print(f"  - Categories: {cats}")
    
    return df


def load_transactions(data_dir: Optional[Path] = None, verbose: bool = False) -> pd.DataFrame:
    """Load transactions.csv."""
    if data_dir is None:
        data_dir = _get_data_dir()
    
    filepath = data_dir / 'transactions.csv'
    df = pd.read_csv(filepath)
    
    # Konversi timestamp ke datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    if verbose:
        print(f"[OK] Transactions loaded: {len(df):,} rows x {len(df.columns)} cols")
        print(f"  - Unique customers: {df['customerID'].nunique():,}")
        print(f"  - Unique assets: {df['ISIN'].nunique():,}")
        if 'timestamp' in df.columns:
            print(f"  - Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        types = df['transactionType'].value_counts().to_dict()
        print(f"  - Buy/Sell: {types}")
    
    return df


def load_prices(data_dir: Optional[Path] = None, verbose: bool = False) -> pd.DataFrame:
    """Load close_prices.csv."""
    if data_dir is None:
        data_dir = _get_data_dir()
    
    filepath = data_dir / 'close_prices.csv'
    df = pd.read_csv(filepath)
    
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    if verbose:
        print(f"[OK] Prices loaded: {len(df):,} rows x {len(df.columns)} cols")
        print(f"  - Unique ISINs: {df['ISIN'].nunique():,}")
        if 'timestamp' in df.columns:
            print(f"  - Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df


def load_all(stocks_only: bool = False, verbose: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Load semua dataset FAR-Trans.
    
    Returns:
        dict dengan keys: 'customers', 'assets', 'transactions', 'prices'
    """
    data_dir = _get_data_dir()
    
    if verbose:
        print("=" * 60)
        print("Loading FAR-Trans Dataset")
        print("=" * 60)
    
    data = {
        'customers': load_customers(data_dir, verbose),
        'assets': load_assets(data_dir, verbose),
        'transactions': load_transactions(data_dir, verbose),
        'prices': load_prices(data_dir, verbose),
    }
    
    if verbose:
        print("=" * 60)
        print("[OK] All data loaded successfully")
        print("=" * 60)
    
    return data
