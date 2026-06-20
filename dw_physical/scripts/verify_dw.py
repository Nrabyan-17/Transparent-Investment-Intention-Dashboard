"""
verify_dw.py
============
Verification script untuk validate Data Warehouse sudah ter-setup
dengan benar setelah ETL pipeline selesai.

Run setelah etl_to_mysql.py untuk:
- Check semua tables exist & populated
- Validate foreign key integrity
- Run sample OLAP queries
- Print summary report

Cara pakai:
    python scripts/verify_dw.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# Sama dengan etl_to_mysql.py
DB_CONFIG = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '3306'),
    'database': os.getenv('DB_NAME', 'dw_investment'),
}

CONN_STRING = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)


def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def check_pass(condition, message):
    status = "✓ PASS" if condition else "✗ FAIL"
    print(f"  [{status}] {message}")
    return condition


def main():
    print("="*60)
    print("DATA WAREHOUSE VERIFICATION")
    print("="*60)
    print(f"Target: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    # Test connection
    try:
        engine = create_engine(CONN_STRING, echo=False)
        with engine.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).fetchone()[0]
        print(f"✓ Connected to MySQL {version}\n")
    except SQLAlchemyError as e:
        print(f"✗ Connection FAILED: {e}")
        return False

    all_passed = True

    # ============================================================
    # CHECK 1: All tables exist
    # ============================================================
    print_section("CHECK 1: Tables Existence")

    expected_tables = ['dim_customer', 'dim_asset', 'dim_date',
                      'dim_channel', 'fact_transactions']
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = :db
        """), {'db': DB_CONFIG['database']}).fetchall()
        existing_tables = [r[0] for r in result]

    for tbl in expected_tables:
        all_passed &= check_pass(tbl in existing_tables, f"Table {tbl} exists")

    # ============================================================
    # CHECK 2: Tables populated
    # ============================================================
    print_section("CHECK 2: Tables Populated")

    row_counts = {}
    with engine.connect() as conn:
        for tbl in expected_tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).fetchone()[0]
            row_counts[tbl] = count
            all_passed &= check_pass(count > 0, f"{tbl}: {count:,} rows")

    # ============================================================
    # CHECK 3: Foreign key integrity
    # ============================================================
    print_section("CHECK 3: Foreign Key Integrity")

    with engine.connect() as conn:
        # Check all fact rows have valid FK
        result = conn.execute(text("""
            SELECT COUNT(*) FROM fact_transactions f
            JOIN dim_customer c ON f.customer_key = c.customer_key
            JOIN dim_asset    a ON f.asset_key    = a.asset_key
            JOIN dim_date     d ON f.date_key     = d.date_key
            JOIN dim_channel  ch ON f.channel_key = ch.channel_key
        """)).fetchone()[0]

        total_fact = row_counts['fact_transactions']
        all_passed &= check_pass(
            result == total_fact,
            f"All {total_fact:,} fact rows have valid FK lookups"
        )

    # ============================================================
    # CHECK 4: Star Schema Indexes
    # ============================================================
    print_section("CHECK 4: Indexes for Performance")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = :db AND TABLE_NAME = 'fact_transactions'
        """), {'db': DB_CONFIG['database']}).fetchall()
        fact_indexes = set(r[0] for r in result)

    expected_fact_indexes = ['PRIMARY', 'idx_fact_customer', 'idx_fact_asset',
                            'idx_fact_date', 'idx_fact_channel']
    for idx in expected_fact_indexes:
        all_passed &= check_pass(idx in fact_indexes,
                                f"Index {idx} on fact_transactions")

    # ============================================================
    # CHECK 5: Sample OLAP Queries (run successfully)
    # ============================================================
    print_section("CHECK 5: Sample OLAP Queries")

    olap_queries = [
        ("SLICE - Stock only",
         "SELECT COUNT(*) FROM fact_transactions f "
         "JOIN dim_asset a ON f.asset_key = a.asset_key "
         "WHERE a.asset_category = 'Stock'"),
        ("DICE - Aggressive Tech 2023",
         "SELECT COUNT(*) FROM fact_transactions f "
         "JOIN dim_customer c ON f.customer_key = c.customer_key "
         "JOIN dim_asset a ON f.asset_key = a.asset_key "
         "JOIN dim_date d ON f.date_key = d.date_key "
         "WHERE c.risk_level='Aggressive' AND a.sector='Technology' AND d.year=2023"),
        ("ROLL-UP - Per customer",
         "SELECT COUNT(DISTINCT c.customer_id) FROM fact_transactions f "
         "JOIN dim_customer c ON f.customer_key = c.customer_key"),
        ("ROLL-UP - Per sector",
         "SELECT COUNT(DISTINCT a.sector) FROM fact_transactions f "
         "JOIN dim_asset a ON f.asset_key = a.asset_key"),
        ("DRILL-DOWN - Hierarchical date",
         "SELECT COUNT(*) FROM fact_transactions f "
         "JOIN dim_date d ON f.date_key = d.date_key "
         "WHERE d.year = 2023 AND d.quarter = 2"),
    ]

    with engine.connect() as conn:
        for name, sql in olap_queries:
            try:
                result = conn.execute(text(sql)).fetchone()[0]
                all_passed &= check_pass(result >= 0,
                                        f"{name}: {result:,} rows")
            except Exception as e:
                check_pass(False, f"{name}: ERROR - {e}")
                all_passed = False

    # ============================================================
    # CHECK 6: Data Quality Validation
    # ============================================================
    print_section("CHECK 6: Data Quality Validation")

    with engine.connect() as conn:
        # Check no NULL FKs
        null_check = conn.execute(text("""
            SELECT
                SUM(CASE WHEN customer_key IS NULL THEN 1 ELSE 0 END) AS null_cust,
                SUM(CASE WHEN asset_key IS NULL THEN 1 ELSE 0 END) AS null_asset,
                SUM(CASE WHEN date_key IS NULL THEN 1 ELSE 0 END) AS null_date,
                SUM(CASE WHEN channel_key IS NULL THEN 1 ELSE 0 END) AS null_channel
            FROM fact_transactions
        """)).fetchone()

        all_passed &= check_pass(null_check[0] == 0, f"No NULL customer_key ({null_check[0]} nulls)")
        all_passed &= check_pass(null_check[1] == 0, f"No NULL asset_key ({null_check[1]} nulls)")
        all_passed &= check_pass(null_check[2] == 0, f"No NULL date_key ({null_check[2]} nulls)")
        all_passed &= check_pass(null_check[3] == 0, f"No NULL channel_key ({null_check[3]} nulls)")

        # Check transaction_type is valid
        invalid_types = conn.execute(text("""
            SELECT COUNT(*) FROM fact_transactions
            WHERE transaction_type NOT IN ('BUY', 'SELL')
        """)).fetchone()[0]
        all_passed &= check_pass(invalid_types == 0,
                                f"All transaction_types valid (BUY/SELL)")

        # Check positive values
        invalid_vals = conn.execute(text("""
            SELECT COUNT(*) FROM fact_transactions
            WHERE total_value <= 0 OR units <= 0 OR unit_price <= 0
        """)).fetchone()[0]
        all_passed &= check_pass(invalid_vals == 0,
                                f"All numeric values positive")

    # ============================================================
    # FINAL REPORT
    # ============================================================
    print_section("VERIFICATION SUMMARY")

    if all_passed:
        print("\n✅ ALL CHECKS PASSED - Data Warehouse ready for use!")
        print("\nNext steps:")
        print("  1. Run sample OLAP queries: mysql -u root -p dw_investment < sql/olap_runnable_queries.sql")
        print("  2. Generate ERD diagram di MySQL Workbench")
        print("  3. Screenshot table data + query results untuk laporan")
    else:
        print("\n⚠️  SOME CHECKS FAILED - Review errors above")
        print("Possible solutions:")
        print("  - Re-run dw_schema.sql untuk recreate tables")
        print("  - Re-run etl_to_mysql.py untuk reload data")
        print("  - Check MySQL service running")

    engine.dispose()
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
