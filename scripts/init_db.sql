-- Create airflow database if it doesn't exist.
-- \gexec sends the SELECT output back to psql as a SQL command, making this
-- idempotent without requiring a superuser DO $$ block.
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

-- Batch analytics tables
CREATE TABLE IF NOT EXISTS daily_metrics (
    date DATE PRIMARY KEY,
    total_events BIGINT DEFAULT 0,
    unique_users BIGINT DEFAULT 0,
    total_views BIGINT DEFAULT 0,
    total_carts BIGINT DEFAULT 0,
    total_purchases BIGINT DEFAULT 0,
    total_revenue NUMERIC(14,2) DEFAULT 0,
    conversion_rate NUMERIC(6,4) DEFAULT 0,
    avg_order_value NUMERIC(10,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS funnel_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    category VARCHAR(255) NOT NULL,
    views BIGINT DEFAULT 0,
    carts BIGINT DEFAULT 0,
    purchases BIGINT DEFAULT 0,
    view_to_cart_rate NUMERIC(6,4) DEFAULT 0,
    cart_to_purchase_rate NUMERIC(6,4) DEFAULT 0,
    UNIQUE (date, category)
);

CREATE TABLE IF NOT EXISTS top_products (
    product_id BIGINT PRIMARY KEY,
    category VARCHAR(255),
    brand VARCHAR(255),
    price NUMERIC(10,2) DEFAULT 0,
    views BIGINT DEFAULT 0,
    carts BIGINT DEFAULT 0,
    purchases BIGINT DEFAULT 0,
    revenue NUMERIC(14,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS top_categories (
    category VARCHAR(255) PRIMARY KEY,
    views BIGINT DEFAULT 0,
    carts BIGINT DEFAULT 0,
    purchases BIGINT DEFAULT 0,
    revenue NUMERIC(14,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS top_brands (
    brand VARCHAR(255) PRIMARY KEY,
    views BIGINT DEFAULT 0,
    carts BIGINT DEFAULT 0,
    purchases BIGINT DEFAULT 0,
    revenue NUMERIC(14,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cart_abandonment (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    category VARCHAR(255) NOT NULL,
    abandoned_carts BIGINT DEFAULT 0,
    completed_purchases BIGINT DEFAULT 0,
    abandonment_rate NUMERIC(6,4) DEFAULT 0,
    UNIQUE (date, category)
);

CREATE TABLE IF NOT EXISTS product_affinity (
    id SERIAL PRIMARY KEY,
    product_a BIGINT NOT NULL,
    product_b BIGINT NOT NULL,
    co_occurrences BIGINT DEFAULT 0,
    lift NUMERIC(8,4) DEFAULT 0,
    UNIQUE (product_a, product_b)
);

CREATE TABLE IF NOT EXISTS category_events (
    category VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_count BIGINT DEFAULT 0,
    PRIMARY KEY (category, event_type)
);

CREATE TABLE IF NOT EXISTS brand_revenue (
    brand VARCHAR(255) PRIMARY KEY,
    total_revenue NUMERIC(14,2) DEFAULT 0,
    purchase_count BIGINT DEFAULT 0
);

-- Streaming table
CREATE TABLE IF NOT EXISTS live_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT,
    last_event_time TIMESTAMP,
    event_count INT DEFAULT 0,
    has_cart BOOLEAN DEFAULT FALSE,
    has_purchase BOOLEAN DEFAULT FALSE,
    last_product_id BIGINT,
    last_category VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW()
);
