# Bolt's Performance Optimization Journal

## 2026-08-13 - [SQLite Composite Indexing & Range Queries for Date Filtering]
**Learning:** Wrapping indexed columns inside SQL functions (such as `date(created_at)`) prevents SQLite from using standard column indexes, forcing a full-table scan (O(N) complexity) to evaluate the function for every single row. By converting functional matches to index-friendly range-based query conditions (e.g., `created_at >= date('now')`), SQLite can leverage composite indexes (like `(user_id, created_at)` or `(ip_address, user_id, created_at)`) for a direct B-tree search range sweep (O(log N) complexity).
**Action:** Avoid wrapping filtered table columns inside functions in WHERE clauses. Instead, refactor conditions into direct column-to-value range comparisons (e.g., column >= start_value) to maintain index-friendliness.
