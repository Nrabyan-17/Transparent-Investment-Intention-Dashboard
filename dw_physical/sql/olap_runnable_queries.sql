-- ============================================================
-- OLAP Operations - Runnable Queries
-- ============================================================
-- File: olap_runnable_queries.sql
--
-- Cara pakai:
--   1. Pastikan database dw_investment sudah ada data
--      (run scripts/generate_sample_data.py + etl_to_mysql.py dulu)
--   2. Connect ke MySQL: mysql -u root -p dw_investment
--   3. Copy-paste query satu per satu untuk lihat hasil
--   4. Atau jalankan semua: source sql/olap_runnable_queries.sql
--
-- File ini berisi 12 query OLAP yang siap dijalankan
-- untuk demonstrasi 4 operasi: SLICE, DICE, ROLL-UP, DRILL-DOWN
-- ============================================================

USE dw_investment;

-- ============================================================
-- VERIFIKASI DATA TER-LOAD
-- ============================================================
SELECT 'Verifikasi Data:' AS info;
SELECT 'dim_customer'    AS table_name, COUNT(*) AS row_count FROM dim_customer
UNION ALL
SELECT 'dim_asset'       AS table_name, COUNT(*) FROM dim_asset
UNION ALL
SELECT 'dim_date'        AS table_name, COUNT(*) FROM dim_date
UNION ALL
SELECT 'dim_channel'     AS table_name, COUNT(*) FROM dim_channel
UNION ALL
SELECT 'fact_transactions' AS table_name, COUNT(*) FROM fact_transactions;


-- ============================================================
-- OLAP 1: SLICE (Filter satu dimensi)
-- ============================================================
SELECT '=== OLAP 1: SLICE ===' AS demo;

-- Query 1.1: Slice by asset_category = 'Stock'
SELECT 'Q1.1: Transaksi Stock saja' AS query;
SELECT
    a.asset_category,
    COUNT(*) AS num_transactions,
    ROUND(SUM(f.total_value), 2) AS total_volume
FROM fact_transactions f
INNER JOIN dim_asset a ON f.asset_key = a.asset_key
WHERE a.asset_category = 'Stock'
GROUP BY a.asset_category;

-- Query 1.2: Slice by single date
SELECT 'Q1.2: Transaksi pada tanggal 1 Juni 2023' AS query;
SELECT
    f.transaction_id,
    c.customer_id,
    a.asset_name,
    f.transaction_type,
    f.total_value
FROM fact_transactions f
INNER JOIN dim_customer c ON f.customer_key = c.customer_key
INNER JOIN dim_asset a    ON f.asset_key    = a.asset_key
INNER JOIN dim_date d     ON f.date_key     = d.date_key
WHERE d.full_date = '2023-06-01'
LIMIT 10;


-- ============================================================
-- OLAP 2: DICE (Filter multi-dimensi)
-- ============================================================
SELECT '=== OLAP 2: DICE ===' AS demo;

-- Query 2.1: Customer Aggressive di Technology Q2 2023
SELECT 'Q2.1: Aggressive customers - Technology - Q2 2023' AS query;
SELECT
    c.customer_id,
    c.risk_level,
    c.investment_capacity,
    a.sector,
    ROUND(SUM(f.total_value), 2) AS total_invested,
    COUNT(*) AS num_transactions
FROM fact_transactions f
INNER JOIN dim_customer c ON f.customer_key = c.customer_key
INNER JOIN dim_asset    a ON f.asset_key    = a.asset_key
INNER JOIN dim_date     d ON f.date_key     = d.date_key
WHERE c.risk_level = 'Aggressive'
  AND a.sector = 'Technology'
  AND d.year = 2023
  AND d.quarter = 2
GROUP BY c.customer_id, c.risk_level, c.investment_capacity, a.sector
ORDER BY total_invested DESC
LIMIT 10;

-- Query 2.2: Premium customers + Internet Banking + Stock
SELECT 'Q2.2: Premium customers via Internet Banking - Stock only' AS query;
SELECT
    c.customer_type,
    ch.channel_name,
    a.asset_category,
    COUNT(*) AS num_transactions,
    ROUND(AVG(f.total_value), 2) AS avg_value
FROM fact_transactions f
INNER JOIN dim_customer c  ON f.customer_key = c.customer_key
INNER JOIN dim_channel  ch ON f.channel_key  = ch.channel_key
INNER JOIN dim_asset    a  ON f.asset_key    = a.asset_key
WHERE c.customer_type = 'Premium'
  AND ch.channel_name = 'Internet Banking'
  AND a.asset_category = 'Stock'
GROUP BY c.customer_type, ch.channel_name, a.asset_category;


-- ============================================================
-- OLAP 3: ROLL-UP (Aggregate ke level lebih tinggi)
-- ============================================================
SELECT '=== OLAP 3: ROLL-UP ===' AS demo;

-- Query 3.1: Per-transaction → Per-customer (feature engineering aggregation)
SELECT 'Q3.1: Roll-up to customer level (per-customer metrics)' AS query;
SELECT
    c.customer_id,
    c.risk_level,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN f.transaction_type = 'BUY'  THEN 1 ELSE 0 END) AS buy_count,
    SUM(CASE WHEN f.transaction_type = 'SELL' THEN 1 ELSE 0 END) AS sell_count,
    ROUND(SUM(f.total_value), 2) AS total_value,
    ROUND(AVG(f.total_value), 2) AS avg_transaction_value,
    COUNT(DISTINCT f.asset_key) AS unique_assets_traded,
    ROUND(
        SUM(CASE WHEN f.transaction_type = 'BUY' THEN 1 ELSE 0 END) * 1.0
        / NULLIF(COUNT(*), 0), 4
    ) AS buy_ratio
FROM fact_transactions f
INNER JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.customer_id, c.risk_level
ORDER BY total_value DESC
LIMIT 10;

-- Query 3.2: Roll-up to sector level
SELECT 'Q3.2: Roll-up to sector level' AS query;
SELECT
    a.sector,
    COUNT(*) AS num_transactions,
    ROUND(SUM(f.total_value), 2) AS total_volume,
    ROUND(AVG(f.total_value), 2) AS avg_transaction_size,
    COUNT(DISTINCT f.customer_key) AS num_unique_customers,
    COUNT(DISTINCT f.asset_key) AS num_unique_assets
FROM fact_transactions f
INNER JOIN dim_asset a ON f.asset_key = a.asset_key
GROUP BY a.sector
ORDER BY total_volume DESC;

-- Query 3.3: Roll-up to quarterly level (temporal aggregation)
SELECT 'Q3.3: Roll-up to quarterly level' AS query;
SELECT
    d.year,
    d.quarter,
    COUNT(*) AS num_transactions,
    ROUND(SUM(f.total_value), 2) AS quarterly_volume,
    COUNT(DISTINCT f.customer_key) AS active_customers,
    ROUND(AVG(f.total_value), 2) AS avg_transaction
FROM fact_transactions f
INNER JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.quarter
ORDER BY d.year, d.quarter;


-- ============================================================
-- OLAP 4: DRILL-DOWN (Detail dari aggregated)
-- ============================================================
SELECT '=== OLAP 4: DRILL-DOWN ===' AS demo;

-- Query 4.1: Top 5 high-value customers → drill-down to individual transactions
SELECT 'Q4.1: Drill-down dari top customer ke transaksi individual' AS query;

-- Step 1: Identify top 5 customers
WITH top_customers AS (
    SELECT
        c.customer_id,
        c.customer_key,
        SUM(f.total_value) AS total_value
    FROM fact_transactions f
    INNER JOIN dim_customer c ON f.customer_key = c.customer_key
    WHERE c.risk_level = 'Aggressive'
    GROUP BY c.customer_id, c.customer_key
    ORDER BY total_value DESC
    LIMIT 5
)
SELECT
    tc.customer_id,
    d.full_date,
    a.asset_name,
    a.sector,
    f.transaction_type,
    f.total_value,
    f.units,
    ch.channel_name
FROM top_customers tc
INNER JOIN fact_transactions f ON tc.customer_key = f.customer_key
INNER JOIN dim_date    d  ON f.date_key    = d.date_key
INNER JOIN dim_asset   a  ON f.asset_key   = a.asset_key
INNER JOIN dim_channel ch ON f.channel_key = ch.channel_key
ORDER BY tc.customer_id, d.full_date DESC
LIMIT 20;

-- Query 4.2: Drill from year → quarter → month
SELECT 'Q4.2: Drill-down hierarchical (year → quarter → month)' AS query;
SELECT
    d.year,
    d.quarter,
    d.month,
    d.month_name,
    COUNT(*) AS num_transactions,
    ROUND(SUM(f.total_value), 2) AS monthly_volume
FROM fact_transactions f
INNER JOIN dim_date d ON f.date_key = d.date_key
WHERE d.year = 2023
GROUP BY d.year, d.quarter, d.month, d.month_name
ORDER BY d.year, d.quarter, d.month;


-- ============================================================
-- COMBINED: SLICE + DICE + ROLL-UP + Window Function
-- ============================================================
SELECT '=== COMBINED OLAP (multi-operation) ===' AS demo;

SELECT 'Q5.1: Conservative customer di Financial 2023 dengan ranking' AS query;
SELECT
    c.customer_id,
    c.risk_level,
    a.sector,
    ROUND(SUM(f.total_value), 2) AS customer_total,
    ROUND(AVG(f.total_value), 2) AS avg_per_transaction,
    COUNT(*) AS num_transactions,
    RANK() OVER (ORDER BY SUM(f.total_value) DESC) AS rank_position
FROM fact_transactions f
INNER JOIN dim_customer c ON f.customer_key = c.customer_key
INNER JOIN dim_asset    a ON f.asset_key    = a.asset_key
INNER JOIN dim_date     d ON f.date_key     = d.date_key
WHERE c.risk_level = 'Conservative'         -- SLICE
  AND a.sector = 'Financial Services'       -- DICE
  AND d.year = 2023                         -- DICE
GROUP BY c.customer_id, c.risk_level, a.sector  -- ROLL-UP
ORDER BY customer_total DESC
LIMIT 10;


-- ============================================================
-- BI ANALYTICS QUERIES
-- ============================================================
SELECT '=== BI ANALYTICS ===' AS demo;

-- BI 1: Distribusi risk level
SELECT 'BI 1: Distribusi customer per risk level' AS query;
SELECT
    risk_level,
    COUNT(*) AS num_customers,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dim_customer), 2) AS percentage
FROM dim_customer
GROUP BY risk_level
ORDER BY num_customers DESC;

-- BI 2: Channel preference per customer type
SELECT 'BI 2: Channel preference per customer type' AS query;
SELECT
    c.customer_type,
    ch.channel_name,
    COUNT(*) AS num_transactions,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY c.customer_type), 2) AS pct_of_type
FROM fact_transactions f
INNER JOIN dim_customer c  ON f.customer_key = c.customer_key
INNER JOIN dim_channel  ch ON f.channel_key  = ch.channel_key
GROUP BY c.customer_type, ch.channel_name
ORDER BY c.customer_type, num_transactions DESC;

-- BI 3: Weekday vs weekend pattern
SELECT 'BI 3: Trading pattern - weekday vs weekend' AS query;
SELECT
    d.is_weekend,
    d.day_of_week,
    COUNT(*) AS num_transactions,
    ROUND(AVG(f.total_value), 2) AS avg_value
FROM fact_transactions f
INNER JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.is_weekend, d.day_of_week
ORDER BY num_transactions DESC;

-- ============================================================
-- END OF OLAP QUERIES
-- ============================================================
SELECT '✅ All OLAP queries executed' AS info;
