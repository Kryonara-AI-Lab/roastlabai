# Bolt's Performance Journal

## 2025-02-18 - Database Range-Based Indexing and Composite Indexes
**Learning:** Applying un-indexable functions like `date(created_at)` in SQLite queries prevents the query planner from utilizing standard B-tree indexes, forcing a full table scan. Rewriting queries to use index-friendly range-based constraints (e.g., `created_at >= date('now')`) coupled with appropriate composite indexes (`idx_roasts_user_created` and `idx_roasts_ip_user_created`) optimizes lookups from O(N) to O(log N).
**Action:** Avoid applying functions to columns in `WHERE` clauses. Use range-based queries instead and support them with composite indexes on the exact query pattern columns (e.g., filtering columns followed by query-range/sorting columns).
