## 2025-10-25 - [Index-Friendly Range-Based Queries in SQLite]
**Learning:** Evaluating functions on indexed columns (e.g., `date(created_at)`) prevents SQLite from using indices on those columns, causing a full table scan. Range-based comparisons (e.g., `created_at >= date('now')`) allow composite indexes to be fully utilized.
**Action:** Always rewrite date/time filters as range comparisons and create composite indexes on the filtering columns to optimize query execution plans.
