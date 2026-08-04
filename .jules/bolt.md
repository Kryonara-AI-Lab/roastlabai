# Bolt's Optimization Journal

## 2026-08-04 - [Database Indexing and Range-Based Query Optimization]
**Learning:** Using scalar function evaluations like `date(created_at) = date('now')` inside SQL `WHERE` clauses forces the database (e.g. SQLite) to perform a full table scan. This is because the engine must run the `date()` function for every row in the table, rendering normal indexes on the `created_at` column completely useless. Transitioning queries to index-friendly range-based constraints such as `created_at >= date('now')` allows database engines to use composite indexes optimally, reducing lookup time from O(N) to O(log N).
**Action:** Always prefer range-based comparisons (e.g. `column >= val`) over applying functions to indexed columns. Pair these queries with composite indexes covering all columns used in filtering and ordering to achieve optimal database query performance.
