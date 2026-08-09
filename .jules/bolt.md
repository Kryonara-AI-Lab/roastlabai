# Bolt's Performance Optimization Journal

## 2025-08-09 - [SQLite Sargable Range Queries with Composite Indexes]
**Learning:** Functions like `date(created_at)` prevent SQLite from utilizing composite or field-specific indexes because they must evaluate the function for every row in the table (a full table scan). Refactoring function calls on indexed columns to use index-friendly range-based comparisons (e.g., `created_at >= date('now')`) makes the query fully sargable. Together with optimized composite indexes like `idx_roasts_user_created` and `idx_roasts_ip_user_created`, this reduces rate-limiting lookup complexity from O(n) to O(log n), providing a massive speedup on high-traffic endpoints.
**Action:** Always inspect queries for function evaluations wrapped around indexed columns in search clauses. Re-write them as range comparisons on the raw column to ensure the database query engine can use the index, and verify index usage programmatically using `EXPLAIN QUERY PLAN`.
