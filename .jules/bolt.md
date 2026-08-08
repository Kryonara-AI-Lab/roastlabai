# Bolt's Journal

## 2025-02-08 - Function-based vs Range-based SQLite Queries
**Learning:** SQLite cannot use indexes on columns that are wrapped inside function evaluations like `date(created_at) = date('now')`. Applying functions to columns forces SQLite to perform a full table scan.
**Action:** Rewrite daily rate limits or history loading queries to use range-based comparisons, such as `created_at >= date('now')`, allowing the query planner to utilize composite indexes on `(user_id, created_at)` or `(ip_address, user_id, created_at)`.
