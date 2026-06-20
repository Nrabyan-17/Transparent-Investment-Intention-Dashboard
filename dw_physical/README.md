# Physical MySQL Data Warehouse - Implementation Guide

## Investment Intention Analysis System

**Tujuan:** Implementasi fisik Data Warehouse di MySQL sebagai bukti konkret untuk konversi MK Data Warehouse (DWO 526).

**Estimasi waktu setup:** 30-45 menit (sudah include install MySQL kalau belum ada)

---

## 1. Folder Structure

```
dw_physical/
├── README.md                          ← File ini
├── scripts/
│   ├── generate_sample_data.py       ← Generate sample CSV (Step 2)
│   ├── etl_to_mysql.py               ← ETL pipeline (Step 4)
│   └── verify_dw.py                  ← Verification (Step 5)
├── sql/
│   ├── dw_schema.sql                 ← DDL CREATE database + tables (Step 3)
│   └── olap_runnable_queries.sql     ← 12 OLAP queries demo (Step 6)
└── data/
    └── raw/                           ← Output dari generate_sample_data.py
        ├── customer_information.csv
        ├── asset_information.csv
        ├── transactions.csv
        ├── date_dimension.csv
        └── channel_information.csv
```

---

## 2. Prerequisites

### 2.1 MySQL Server

**Option A: XAMPP (Recommended untuk Windows)**
1. Download dari https://www.apachefriends.org/
2. Install dan start MySQL service via XAMPP Control Panel
3. Default credentials: user `root`, password kosong

**Option B: MySQL Community Server**
1. Download dari https://dev.mysql.com/downloads/mysql/
2. Install + setup root password saat installation
3. Start service:
   - Windows: `services.msc` → MySQL → Start
   - Mac: `brew services start mysql`
   - Linux: `sudo systemctl start mysql`

**Verify installation:**
```bash
mysql --version
# Output: mysql  Ver 8.x.x or similar
```

### 2.2 MySQL Workbench (Optional but Recommended)

Download dari https://dev.mysql.com/downloads/workbench/

Berguna untuk:
- Visual database management
- Generate ERD diagram dari schema
- Screenshot bukti untuk laporan

### 2.3 Python Environment

```bash
# Check Python version (minimum 3.8)
python --version

# Install dependencies
pip install pandas numpy sqlalchemy pymysql
```

---

## 3. Setup Steps

### Step 1: Clone/Copy Project

```bash
# Pindah ke folder kerja
cd /path/to/your/projects

# Kalau dari folder transparent-investment-intention, salin folder dw_physical
cp -r dw_physical /path/to/desired/location
cd dw_physical
```

### Step 2: Generate Sample Data

```bash
python scripts/generate_sample_data.py
```

**Output yang diharapkan:**
```
✓ Saved: customer_information.csv (500 rows)
✓ Saved: asset_information.csv (50 rows)
✓ Saved: channel_information.csv (3 rows)
✓ Saved: date_dimension.csv (730 rows)
✓ Saved: transactions.csv (3000 rows)
```

5 file CSV akan ter-generate di `data/raw/`.

### Step 3: Create Database & Schema

**Option A: Via Command Line**
```bash
# Login sebagai root
mysql -u root -p

# Atau jalankan script langsung
mysql -u root -p < sql/dw_schema.sql
```

**Option B: Via MySQL Workbench**
1. Open MySQL Workbench → Connect ke local instance
2. File → Open SQL Script → pilih `sql/dw_schema.sql`
3. Execute (lightning bolt icon)

**Verifikasi:**
```sql
SHOW DATABASES;        -- Harus ada 'dw_investment'
USE dw_investment;
SHOW TABLES;           -- Harus ada 5 tables (1 fact + 4 dim)
```

### Step 4: Configure Database Credentials

Edit `scripts/etl_to_mysql.py`, sesuaikan DB_CONFIG:

```python
DB_CONFIG = {
    'user': 'root',           # ← Sesuaikan
    'password': 'YOUR_PASSWORD',  # ← Sesuaikan (kosong untuk XAMPP default)
    'host': 'localhost',
    'port': '3306',
    'database': 'dw_investment',
}
```

**Alternatif (lebih aman):** Pakai environment variables
```bash
# Linux/Mac
export DB_USER=root
export DB_PASSWORD=your_password

# Windows (cmd)
set DB_USER=root
set DB_PASSWORD=your_password
```

### Step 5: Run ETL Pipeline

```bash
python scripts/etl_to_mysql.py
```

**Output yang diharapkan:**
```
[12:00:01] [OK]   Connected to MySQL 8.x.x
[12:00:01] [INFO] PHASE 1: EXTRACT
[12:00:01] [INFO] ✓ Loaded customer_information.csv: 500 rows
...
[12:00:05] [INFO] PHASE 5: VERIFICATION
[12:00:05] [INFO] ✓ dim_customer: 500 rows
[12:00:05] [INFO] ✓ dim_asset: 50 rows
[12:00:05] [INFO] ✓ dim_date: 730 rows
[12:00:05] [INFO] ✓ dim_channel: 3 rows
[12:00:05] [INFO] ✓ fact_transactions: 3,000 rows
[12:00:05] [INFO] ✅ ETL PIPELINE COMPLETED in 4.50s
```

### Step 6: Run OLAP Queries

```bash
# Via command line
mysql -u root -p dw_investment < sql/olap_runnable_queries.sql

# Atau buka di MySQL Workbench dan execute satu per satu
# untuk lihat hasil per query
```

---

## 4. Verification Checklist

Setelah semua step selesai, verifikasi:

```sql
USE dw_investment;

-- 1. Cek total rows per table
SELECT 'dim_customer' AS tbl, COUNT(*) AS rows FROM dim_customer
UNION SELECT 'dim_asset', COUNT(*) FROM dim_asset
UNION SELECT 'dim_date', COUNT(*) FROM dim_date
UNION SELECT 'dim_channel', COUNT(*) FROM dim_channel
UNION SELECT 'fact_transactions', COUNT(*) FROM fact_transactions;

-- 2. Cek foreign keys berfungsi
SELECT COUNT(*)
FROM fact_transactions f
JOIN dim_customer c ON f.customer_key = c.customer_key
JOIN dim_asset a ON f.asset_key = a.asset_key
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_channel ch ON f.channel_key = ch.channel_key;
-- Harus = total rows fact_transactions

-- 3. Sample query OLAP
SELECT a.sector, COUNT(*) AS n, ROUND(SUM(f.total_value), 2) AS volume
FROM fact_transactions f
JOIN dim_asset a ON f.asset_key = a.asset_key
GROUP BY a.sector
ORDER BY volume DESC;
```

---

## 5. Screenshots untuk Laporan

Untuk **bukti konkret** di laporan, screenshot:

1. **MySQL Workbench - Schema view**
   - Right click `dw_investment` → Reverse Engineer
   - Generate ERD diagram
   - Screenshot ERD untuk laporan Bab 3

2. **Table data preview**
   - Klik kanan table → Select Rows
   - Screenshot beberapa rows untuk bukti data ter-load

3. **OLAP query results**
   - Jalankan query, screenshot hasil
   - 4 screenshots untuk 4 operations (SLICE, DICE, ROLL-UP, DRILL-DOWN)

4. **Performance**
   - Lihat di MySQL Workbench → Server Status
   - Screenshot uptime + connection info

---

## 6. Troubleshooting

### Error: "Access denied for user 'root'@'localhost'"

**Solusi:** Update password di DB_CONFIG atau reset MySQL password:
```bash
# Reset password XAMPP MySQL:
# 1. Stop MySQL via XAMPP Control Panel
# 2. Run: mysqld_safe --skip-grant-tables
# 3. Connect: mysql -u root
# 4. UPDATE mysql.user SET authentication_string=PASSWORD('new_password') WHERE User='root';
# 5. FLUSH PRIVILEGES;
```

### Error: "Unknown database 'dw_investment'"

**Solusi:** Run dw_schema.sql dulu:
```bash
mysql -u root -p < sql/dw_schema.sql
```

### Error: "Table 'fact_transactions' doesn't exist"

**Solusi:** Schema belum ter-create dengan benar. Re-run:
```bash
mysql -u root -p
DROP DATABASE IF EXISTS dw_investment;
SOURCE sql/dw_schema.sql;
```

### Error: "ModuleNotFoundError: No module named 'pymysql'"

**Solusi:**
```bash
pip install sqlalchemy pymysql pandas numpy
```

### Error: "(2003, \"Can't connect to MySQL server on 'localhost'\")"

**Solusi:** MySQL service tidak running. Start via:
- XAMPP Control Panel → MySQL → Start
- Windows Services → MySQL → Start
- `sudo systemctl start mysql` (Linux)
- `brew services start mysql` (Mac)

---

## 7. Mapping ke RPS DWO

| Step | SUB-CPMK Coverage | Bobot RPS |
|------|------------------|-----------|
| Step 3 (Schema) | 653 (Model Multidimensi), 655 (Desain DW) | 20% |
| Step 5 (ETL) | 654 (ETL + DQ), 634 (Implementasi) | 20% |
| Step 6 (OLAP) | 633 (OLAP), 656 (Implementasi OLAP) | 30% |
| Documentation | 657 (Laporan) | 10% |
| **TOTAL** | **5 SUB-CPMK ter-cover** | **80% of RPS** |

---

## 8. Catatan Penting

**Data ini SAMPLE/SIMULASI**, bukan data riil FAR-Trans:
- Generated dengan random seed (`np.random.seed(42)`) untuk reproducibility
- Realistic distribution tapi bukan transaksi nyata
- Cukup untuk demonstrasi konsep DW + OLAP

**Untuk produksi (kalau ada):**
- Ganti `generate_sample_data.py` dengan loader yang baca dari `data/raw/` FAR-Trans
- Sesuaikan column mapping di `etl_to_mysql.py`
- Tambah validation rules sesuai data quality requirements

**Limitations vs RPS yang strict:**
- Mondrian OLAP Engine tidak digunakan (pakai SQL native saja)
- Highcharts PHP dashboard tidak ada (sudah ada Streamlit dashboard di project utama)
- Pentaho PDI tidak digunakan (ETL pakai Python langsung)

Kalau koordinator MK DWO meminta strict compliance ke RPS, akan perlu effort tambahan untuk install + integrate tools tersebut.

---

## 9. References

- Kimball, R., & Ross, M. (2002). *The Data Warehouse Toolkit*. Wiley.
- Inmon, W. H. (2002). *Building the Data Warehouse*. Wiley.
- MySQL Documentation: https://dev.mysql.com/doc/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/

---

**Last updated:** 19 May 2026
**Project:** Transparent Investment Intention Analysis
**Course:** Data Warehouse (DWO 526) - Universitas Pembangunan Nasional "Veteran" Jawa Timur