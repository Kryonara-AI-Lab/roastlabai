# Bolt's Journal

## 2025-02-16 - SQLite Range Scans vs Un-indexable Functions
**Learning:** Functions wrapped around column names in SQLite `WHERE` clauses (like `date(created_at) = date('now')`) prevent SQLite from utilizing standard b-tree indexes on those columns, causing full table scans. Converting the condition to a range query (`created_at >= date('now')`) allows SQLite to perform an index range scan using covering composite indexes (`(user_id, created_at)` or `(ip_address, user_id, created_at)`).
**Action:** When writing timestamp/date filter queries in SQLite, always prefer range queries (e.g. `>= date('now')`) over function evaluations on the column (e.g. `date(created_at)`), and ensure appropriate composite indexes exist on filtering and sorting columns.
