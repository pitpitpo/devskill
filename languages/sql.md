# 🗄️ SQL Mastery & Query Optimization (`sql.md`)

> **Standard**: ANSI SQL / PostgreSQL Dialect  
> **Classification**: Relational Query Engineering  
> **Core Philosophy**: "Write SARGable Queries, Leverage Window Functions, Avoid N+1 at the DB Layer."

---

## 1. SARGable Queries (Index Utilization)

A query is **SARGable** (Search Argument Able) when the database engine can take direct advantage of an index.

```sql
-- ❌ NON-SARGable: Function wraps indexed column; forces full table scan
SELECT id FROM users WHERE LOWER(email) = 'alex@example.com';
SELECT id FROM orders WHERE DATE(created_at) = '2026-11-13';

-- ✅ SARGable: Column is bare; index can perform binary search
SELECT id FROM users WHERE email = 'alex@example.com';
SELECT id FROM orders WHERE created_at >= '2026-11-13 00:00:00' 
                        AND created_at <  '2026-11-14 00:00:00';
```

---

## 2. Window Functions & Analytical Queries

Window functions calculate aggregate values across subsets of rows without collapsing them like `GROUP BY`:

```sql
-- Rank products by sales within each category
SELECT 
    category_id,
    product_name,
    total_sales,
    ROW_NUMBER() OVER (
        PARTITION BY category_id 
        ORDER BY total_sales DESC
    ) as rank_in_category
FROM product_sales;
```

---

## 3. Common Table Expressions (CTEs)

```sql
WITH HighValueCustomers AS (
    SELECT customer_id, SUM(amount) AS total_spent
    FROM orders
    GROUP BY customer_id
    HAVING SUM(amount) > 10000
)
SELECT c.name, c.email, h.total_spent
FROM HighValueCustomers h
JOIN customers c ON c.id = h.customer_id
ORDER BY h.total_spent DESC;
```
