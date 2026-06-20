-- ============================================================
-- DDL: Investment Intention Data Warehouse
-- ============================================================
-- File: dw_schema.sql
-- Project: Transparent Investment Intention Analysis
-- MK Konversi: Data Warehouse (DWO 526)
--
-- Cara pakai:
--   mysql -u root -p < sql/dw_schema.sql
--   atau di MySQL Workbench, buka file ini dan execute
-- ============================================================

-- Drop database kalau sudah ada (untuk fresh install)
DROP DATABASE IF EXISTS dw_investment;

-- Create database
CREATE DATABASE dw_investment
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE dw_investment;

-- ============================================================
-- DIMENSION TABLE 1: dim_customer
-- ============================================================
CREATE TABLE dim_customer (
    customer_key        INT AUTO_INCREMENT PRIMARY KEY,
    customer_id         VARCHAR(50)  NOT NULL UNIQUE,
    customer_type       VARCHAR(20)  COMMENT 'Mass, Premium, Professional, Legal Entity, Inactive',
    risk_level          VARCHAR(20)  COMMENT 'Conservative, Income, Balanced, Aggressive',
    investment_capacity VARCHAR(20)  COMMENT '<30K, 30K-80K, 80K-300K, >300K EUR',
    has_questionnaire   BOOLEAN      DEFAULT FALSE,
    customer_segment    VARCHAR(30),
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_id   (customer_id),
    INDEX idx_risk_level    (risk_level),
    INDEX idx_customer_type (customer_type)
) ENGINE=InnoDB COMMENT='SCD Type 1 - Customer Dimension';


-- ============================================================
-- DIMENSION TABLE 2: dim_asset
-- ============================================================
CREATE TABLE dim_asset (
    asset_key      INT AUTO_INCREMENT PRIMARY KEY,
    ISIN           VARCHAR(20)  NOT NULL UNIQUE,
    asset_name     VARCHAR(100),
    asset_category VARCHAR(30)  COMMENT 'Stock, Bond, Fund, ETF',
    sector         VARCHAR(50),
    industry       VARCHAR(50),
    market_id      VARCHAR(20),
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ISIN     (ISIN),
    INDEX idx_sector   (sector),
    INDEX idx_category (asset_category)
) ENGINE=InnoDB COMMENT='SCD Type 1 - Asset Dimension';


-- ============================================================
-- DIMENSION TABLE 3: dim_date
-- ============================================================
-- Format date_key: YYYYMMDD (e.g., 20230315 untuk 15 Maret 2023)
CREATE TABLE dim_date (
    date_key     INT          PRIMARY KEY COMMENT 'Format YYYYMMDD',
    full_date    DATE         NOT NULL UNIQUE,
    year         INT          NOT NULL,
    quarter      INT          NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month        INT          NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name   VARCHAR(10),
    day_of_month INT          CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_week  VARCHAR(10),
    is_weekend   BOOLEAN      DEFAULT FALSE,
    INDEX idx_year         (year),
    INDEX idx_year_quarter (year, quarter),
    INDEX idx_year_month   (year, month)
) ENGINE=InnoDB COMMENT='SCD Type 0 - Date Dimension (immutable)';


-- ============================================================
-- DIMENSION TABLE 4: dim_channel
-- ============================================================
CREATE TABLE dim_channel (
    channel_key  INT AUTO_INCREMENT PRIMARY KEY,
    channel_name VARCHAR(30)  NOT NULL UNIQUE,
    channel_type VARCHAR(20)  COMMENT 'Physical, Digital, Hybrid',
    is_digital   BOOLEAN      DEFAULT FALSE,
    description  VARCHAR(200),
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_channel_name (channel_name),
    INDEX idx_channel_type (channel_type)
) ENGINE=InnoDB COMMENT='SCD Type 1 - Channel Dimension';


-- ============================================================
-- FACT TABLE: fact_transactions
-- ============================================================
CREATE TABLE fact_transactions (
    transaction_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_key     INT          NOT NULL,
    asset_key        INT          NOT NULL,
    date_key         INT          NOT NULL,
    channel_key      INT          NOT NULL,
    transaction_type VARCHAR(10)  NOT NULL COMMENT 'BUY or SELL',
    total_value      DECIMAL(15, 2) NOT NULL,
    units            DECIMAL(15, 4) NOT NULL,
    unit_price       DECIMAL(10, 4) NOT NULL,
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (asset_key)    REFERENCES dim_asset(asset_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (date_key)     REFERENCES dim_date(date_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (channel_key)  REFERENCES dim_channel(channel_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Check constraint
    CHECK (transaction_type IN ('BUY', 'SELL')),

    -- Indexes untuk query performance
    INDEX idx_fact_customer (customer_key),
    INDEX idx_fact_asset    (asset_key),
    INDEX idx_fact_date     (date_key),
    INDEX idx_fact_channel  (channel_key),
    INDEX idx_fact_type     (transaction_type),
    INDEX idx_fact_value    (total_value)
) ENGINE=InnoDB COMMENT='Fact Table - Transaction events';


-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================
-- Run queries di bawah untuk verifikasi schema sudah ter-create

-- 1. List semua tables di database
SHOW TABLES;

-- 2. Cek struktur fact table
DESCRIBE fact_transactions;

-- 3. Cek foreign key constraints
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM
    INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE
    TABLE_SCHEMA = 'dw_investment'
    AND REFERENCED_TABLE_NAME IS NOT NULL;

-- 4. Cek total tables
SELECT
    COUNT(*) AS total_tables
FROM
    INFORMATION_SCHEMA.TABLES
WHERE
    TABLE_SCHEMA = 'dw_investment';

-- Expected output: 5 tables (1 fact + 4 dimensions)

-- ============================================================
-- END OF DDL SCRIPT
-- ============================================================
