## 2026-07-13 - Avoid SQLite Function Wrappers in WHERE Clauses
**Learning:** Evaluated function calls on table columns in SQLite (such as `WHERE date(created_at) = date('now')`) prevent SQLite from using indexes on `created_at`, forcing a full table scan (`SCAN roasts`).
**Action:** Replace `date(created_at) = date('now')` with indexable range queries (`created_at >= date('now')`) combined with composite indexes (e.g. `(user_id, created_at)` or `(ip_address, user_id, created_at)`) to achieve index searches (`SEARCH roasts USING COVERING INDEX`).
