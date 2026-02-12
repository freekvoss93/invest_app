-- Average stock value per position on 11-02-2026
-- Run with: sqlite3 portfolio.db < avg_stock_value_20260211.sql

SELECT
    p.name,
    p.isin,
    COUNT(*)            AS num_snapshots,
    ROUND(AVG(p.price), 2)  AS avg_price,
    ROUND(AVG(p.value), 2)  AS avg_value,
    ROUND(AVG(p.size), 2)   AS avg_size,
    ROUND(AVG(p.pl), 2)     AS avg_pl
FROM position p
JOIN portfolio_snapshot s ON s.id = p.snapshot_id
WHERE date(s.fetched_at) = '2026-02-11'
GROUP BY p.product_id
ORDER BY avg_value DESC;
