# Bolt's Performance Journal

## 2025-02-18 - SQLite Function-Based Query Bottleneck on Timestamp Fields
**Learning:** In SQLite, applying a date/time formatting function like `date(created_at)` in a `WHERE` clause prevents SQLite from utilizing standard column indexes on `created_at`. This forces a full table scan of the `roasts` table, which degrades to O(N) complexity as history grows.
**Action:** Replace un-indexable function evaluations (such as `date(created_at) = date('now')`) with index-friendly range-based queries (e.g., `created_at >= date('now')`). Pair this with composite indexes on the specific query filter columns (`user_id, created_at` and `ip_address, user_id, created_at`) to achieve lightning-fast O(log N) index seek operations.
