# Bolt's Journal - Critical Learnings Only

## 2025-02-15 - Index-Friendly Range Queries & Composite Database Indexes in SQLite
**Learning:** Functions applied on database columns inside WHERE clauses (like `date(created_at) = date('now')`) prevent SQLite from utilizing standard B-tree indexes, forcing a full table scan. Rewriting the expression to a range-based check (`created_at >= date('now')`) enables index-seeking. Additionally, composite indexes on (user_id, created_at) and (ip_address, user_id, created_at) significantly accelerate query performance under heavy traffic.
**Action:** Always rewrite date/time/string function-wrapped query conditions to direct range comparisons on indexed columns, and design precise composite indexes for complex multi-column filter queries.
