# Bolt's Performance Journal

This journal records critical performance lessons learned during optimization of RoastLab.

## 2025-02-19 - Index-friendly Range Queries vs. Column Function Evaluations
**Learning:** Using `date(created_at) = date('now')` in SQLite queries prevents the database from utilizing indexes on the `created_at` column because the function must be evaluated for every row (resulting in O(N) full-table scans). Rewriting the query to use range-based comparisons like `created_at >= date('now')` allows SQLite to perform highly-optimized `INDEX RANGE SCAN` operations with O(log N) complexity.
**Action:** Always prefer range-based comparisons on raw columns instead of functions (like `date()`, `datetime()`, etc.) wrapping indexed columns in SQLite rate-limiting and filtering queries.
