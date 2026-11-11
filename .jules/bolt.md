# Bolt's Performance Journal - Critical Learnings

## 2026-11-11 - SQLite Sargable Queries with Composite Indexes
**Learning:** SQLite cannot use B-tree indexes when functions wrap indexed columns (e.g. `date(created_at) = date('now')`), forcing a full table scan (`SCAN roasts`) even if `created_at` or `(user_id, created_at)` has an index. Because `created_at` defaults to `CURRENT_TIMESTAMP` ('YYYY-MM-DD HH:MM:SS'), switching to a sargable range comparison `created_at >= date('now')` allows SQLite to perform an index seek (`SEARCH roasts USING COVERING INDEX`) on composite indexes like `(user_id, created_at DESC)` and `(ip_address, user_id, created_at)`.
**Action:** When querying timestamps for "today" or date boundaries in SQLite, avoid function wrappers on indexed columns and use range comparisons (`col >= date(...)` / `col < date(...)`) combined with multi-column composite indexes.
