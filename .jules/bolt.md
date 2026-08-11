# Bolt's Performance Journal - Critical Learnings Only

## 2026-08-11 - Index-Friendly Range-Based Queries in SQLite
**Learning:** Wrapping a database column in a function (such as `date(created_at)`) prevents SQLite from utilizing indexes on that column, forcing a full-table scan (O(N) search complexity). By rewriting queries to use range-based operators (e.g., `created_at >= date('now')`), SQLite can leverage composite indexes on `(user_id, created_at)` or `(ip_address, user_id, created_at)`, turning an O(N) search into an O(log N) search.
**Action:** Always prefer range-based comparisons on raw columns over function evaluations on indexed columns in SQL queries, and ensure composite indexes are created for fields frequently queried together.
