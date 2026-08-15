## 2025-02-15 - Index-friendly date range query optimization for rate limiting
**Learning:** Evaluating `date(created_at) = date('now')` in SQLite queries forces full table scans because SQLite cannot use indexes when expressions or functions are applied to indexed columns.
**Action:** Replace expression evaluations on columns with sargable range operations like `created_at >= date('now')` and create composite covering indexes `(user_id, created_at)` and `(ip_address, user_id, created_at)` to enable covering index searches.
