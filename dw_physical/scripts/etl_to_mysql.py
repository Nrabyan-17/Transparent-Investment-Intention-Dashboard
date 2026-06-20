"""
etl_to_mysql.py
===============
ETL Script: Load sample CSV data ke MySQL Data Warehouse.

Workflow:
    EXTRACT  → Baca CSV dari data/raw/
    TRANSFORM → Cleaning + denormalize + create surrogate keys
    LOAD     → Insert ke MySQL star schema (dim tables → fact table)

Cara pakai:
    1. Pastikan MySQL running & schema sudah dibuat:
       mysql -u root -p < sql/dw_schema.sql

    2. Setup database credentials di .env atau langsung edit DB_CONFIG di bawah

    3. Generate sample data dulu kalau belum:
       python scripts/generate_sample_data.py

    4. Run ETL:
       python scripts/etl_to_mysql.py

Output:
    - 5 tables di MySQL populated dengan data
    - Log proses di stdout
"""

import os
import sys
import time
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ============================================================
# DATABASE CONFIGURATION
# ============================================================
# CATATAN: Ubah credentials sesuai setup MySQL kamu
# Recommended: pakai .env file untuk production
DB_CONFIG = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),  # Kosong kalau XAMPP default
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '3306'),
    'database': os.getenv('DB_NAME', 'dw_investment'),
}

# Build connection string
CONN_STRING = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# Path config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'


# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def log(message, level='INFO'):
    """Print log message dengan timestamp dan level."""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")


def test_connection(engine):
    """Test MySQL connection sebelum mulai ETL."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()")).fetchone()
            log(f"Connected to MySQL {result[0]}", "OK")
            return True
    except SQLAlchemyError as e:
        log(f"Connection failed: {e}", "ERROR")
        log("Pastikan:", "ERROR")
        log("  1. MySQL service is running", "ERROR")
        log("  2. Database 'dw_investment' sudah dibuat (run dw_schema.sql)", "ERROR")
        log("  3. Credentials di DB_CONFIG benar", "ERROR")
        return False


def clear_tables(engine):
    """Clear existing data dari tables (untuk re-run ETL)."""
    log("Clearing existing data...")
    tables = ['fact_transactions', 'dim_customer', 'dim_asset',
              'dim_date', 'dim_channel']
    with engine.begin() as conn:
        # Disable FK checks sementara untuk clear dengan urutan bebas
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in tables:
            conn.execute(text(f"TRUNCATE TABLE {table}"))
            log(f"  ✓ Cleared {table}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


# ============================================================
# EXTRACT PHASE
# ============================================================
def extract():
    """EXTRACT: Read CSV files dari data/raw/."""
    log("="*60)
    log("PHASE 1: EXTRACT")
    log("="*60)

    files_to_load = {
        'customers':    'customer_information.csv',
        'assets':       'asset_information.csv',
        'channels':     'channel_information.csv',
        'dates':        'date_dimension.csv',
        'transactions': 'transactions.csv',
    }

    data = {}
    for key, filename in files_to_load.items():
        filepath = DATA_DIR / filename
        if not filepath.exists():
            log(f"File not found: {filepath}", "ERROR")
            log("Run scripts/generate_sample_data.py first!", "ERROR")
            sys.exit(1)

        df = pd.read_csv(filepath)
        data[key] = df
        log(f"  ✓ Loaded {filename}: {len(df)} rows")

    return data


# ============================================================
# TRANSFORM PHASE
# ============================================================
def transform(data):
    """TRANSFORM: Cleaning, type conversion, surrogate key mapping."""
    log("\n" + "="*60)
    log("PHASE 2: TRANSFORM")
    log("="*60)

    # 1. Date conversion + type validation
    log("Transform dim_date...")
    data['dates']['full_date'] = pd.to_datetime(data['dates']['full_date']).dt.date
    data['dates']['is_weekend'] = data['dates']['is_weekend'].astype(bool)
    log(f"  ✓ Date dim ready: {len(data['dates'])} rows")

    # 2. Customer cleaning
    log("Transform dim_customer...")
    data['customers']['has_questionnaire'] = data['customers']['has_questionnaire'].astype(bool)
    # Remove duplicates kalau ada
    before = len(data['customers'])
    data['customers'] = data['customers'].drop_duplicates(subset=['customer_id'])
    after = len(data['customers'])
    if before > after:
        log(f"  ⚠ Removed {before-after} duplicate customers")
    log(f"  ✓ Customer dim ready: {after} rows")

    # 3. Asset cleaning
    log("Transform dim_asset...")
    before = len(data['assets'])
    data['assets'] = data['assets'].drop_duplicates(subset=['ISIN'])
    after = len(data['assets'])
    if before > after:
        log(f"  ⚠ Removed {before-after} duplicate assets")
    log(f"  ✓ Asset dim ready: {after} rows")

    # 4. Channel cleaning
    log("Transform dim_channel...")
    data['channels']['is_digital'] = data['channels']['is_digital'].astype(bool)
    log(f"  ✓ Channel dim ready: {len(data['channels'])} rows")

    # 5. Transactions cleaning
    log("Transform fact_transactions...")
    data['transactions']['transaction_date'] = pd.to_datetime(
        data['transactions']['transaction_date'])
    data['transactions']['date_key'] = data['transactions']['transaction_date'].dt.strftime('%Y%m%d').astype(int)
    log(f"  ✓ Transactions ready: {len(data['transactions'])} rows")

    return data


# ============================================================
# LOAD PHASE
# ============================================================
def load_dimensions(data, engine):
    """LOAD: Insert dimensions ke MySQL (must be BEFORE fact)."""
    log("\n" + "="*60)
    log("PHASE 3: LOAD DIMENSIONS")
    log("="*60)

    # 1. Load dim_date
    log("Loading dim_date...")
    start = time.time()
    data['dates'].to_sql('dim_date', engine, if_exists='append',
                        index=False, chunksize=1000)
    elapsed = time.time() - start
    log(f"  ✓ Loaded {len(data['dates'])} rows in {elapsed:.2f}s")

    # 2. Load dim_customer
    log("Loading dim_customer...")
    start = time.time()
    data['customers'].to_sql('dim_customer', engine, if_exists='append',
                              index=False, chunksize=500)
    elapsed = time.time() - start
    log(f"  ✓ Loaded {len(data['customers'])} rows in {elapsed:.2f}s")

    # 3. Load dim_asset
    log("Loading dim_asset...")
    start = time.time()
    data['assets'].to_sql('dim_asset', engine, if_exists='append',
                          index=False, chunksize=500)
    elapsed = time.time() - start
    log(f"  ✓ Loaded {len(data['assets'])} rows in {elapsed:.2f}s")

    # 4. Load dim_channel
    log("Loading dim_channel...")
    start = time.time()
    data['channels'].to_sql('dim_channel', engine, if_exists='append',
                            index=False, chunksize=100)
    elapsed = time.time() - start
    log(f"  ✓ Loaded {len(data['channels'])} rows in {elapsed:.2f}s")


def load_facts(data, engine):
    """LOAD: Insert facts AFTER dimensions (need FK lookups)."""
    log("\n" + "="*60)
    log("PHASE 4: LOAD FACTS (with surrogate key lookup)")
    log("="*60)

    # Get surrogate key mappings dari dimensions
    log("Building surrogate key lookups...")
    with engine.connect() as conn:
        cust_map = dict(conn.execute(text(
            "SELECT customer_id, customer_key FROM dim_customer")).fetchall())
        asset_map = dict(conn.execute(text(
            "SELECT ISIN, asset_key FROM dim_asset")).fetchall())
        channel_map = dict(conn.execute(text(
            "SELECT channel_name, channel_key FROM dim_channel")).fetchall())
    log(f"  ✓ Customer lookups: {len(cust_map)}")
    log(f"  ✓ Asset lookups: {len(asset_map)}")
    log(f"  ✓ Channel lookups: {len(channel_map)}")

    # Map business keys → surrogate keys
    log("Mapping foreign keys di transactions...")
    fact_df = data['transactions'].copy()
    fact_df['customer_key'] = fact_df['customer_id'].map(cust_map)
    fact_df['asset_key'] = fact_df['ISIN'].map(asset_map)
    fact_df['channel_key'] = fact_df['channel_name'].map(channel_map)

    # Validation: ensure no missing FK
    missing_cust = fact_df['customer_key'].isna().sum()
    missing_asset = fact_df['asset_key'].isna().sum()
    missing_channel = fact_df['channel_key'].isna().sum()

    if missing_cust + missing_asset + missing_channel > 0:
        log(f"  ⚠ Missing FK: cust={missing_cust}, asset={missing_asset}, channel={missing_channel}", "WARN")
        log("  Dropping rows with missing FK...", "WARN")
        fact_df = fact_df.dropna(subset=['customer_key', 'asset_key', 'channel_key'])

    # Select columns sesuai schema fact_transactions
    fact_to_insert = fact_df[[
        'customer_key', 'asset_key', 'date_key', 'channel_key',
        'transaction_type', 'total_value', 'units', 'unit_price'
    ]].copy()

    # Convert FK columns to int
    for col in ['customer_key', 'asset_key', 'channel_key']:
        fact_to_insert[col] = fact_to_insert[col].astype(int)

    # Load fact table
    log("Loading fact_transactions...")
    start = time.time()
    fact_to_insert.to_sql('fact_transactions', engine, if_exists='append',
                          index=False, chunksize=1000)
    elapsed = time.time() - start
    log(f"  ✓ Loaded {len(fact_to_insert)} rows in {elapsed:.2f}s")


# ============================================================
# VERIFICATION
# ============================================================
def verify(engine):
    """Verify ETL berjalan dengan benar."""
    log("\n" + "="*60)
    log("PHASE 5: VERIFICATION")
    log("="*60)

    tables = ['dim_customer', 'dim_asset', 'dim_date',
              'dim_channel', 'fact_transactions']

    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {table}")).fetchone()
            log(f"  ✓ {table}: {result[0]:,} rows")

        # Sample query: distribusi risk level
        log("\nSample query - Risk level distribution:")
        result = conn.execute(text("""
            SELECT risk_level, COUNT(*) as count
            FROM dim_customer
            GROUP BY risk_level
            ORDER BY count DESC
        """)).fetchall()
        for risk_level, count in result:
            log(f"  {risk_level}: {count}")

        # Sample query: top sectors by volume
        log("\nSample query - Top 5 sectors by volume:")
        result = conn.execute(text("""
            SELECT a.sector, SUM(f.total_value) as total_volume
            FROM fact_transactions f
            JOIN dim_asset a ON f.asset_key = a.asset_key
            GROUP BY a.sector
            ORDER BY total_volume DESC
            LIMIT 5
        """)).fetchall()
        for sector, volume in result:
            log(f"  {sector}: EUR {volume:,.2f}")


# ============================================================
# MAIN ETL ORCHESTRATION
# ============================================================
def main():
    log("="*60)
    log("ETL PIPELINE: Investment Intention Data Warehouse")
    log("="*60)
    log(f"Source: {DATA_DIR}")
    log(f"Target: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    log("")

    # Create engine
    try:
        engine = create_engine(CONN_STRING, echo=False)
    except Exception as e:
        log(f"Failed to create engine: {e}", "ERROR")
        sys.exit(1)

    # Test connection
    if not test_connection(engine):
        sys.exit(1)

    # Run ETL phases
    overall_start = time.time()

    try:
        clear_tables(engine)
        data = extract()
        data = transform(data)
        load_dimensions(data, engine)
        load_facts(data, engine)
        verify(engine)

        overall_elapsed = time.time() - overall_start
        log("\n" + "="*60)
        log(f"✅ ETL PIPELINE COMPLETED in {overall_elapsed:.2f}s")
        log("="*60)

    except Exception as e:
        log(f"ETL failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
