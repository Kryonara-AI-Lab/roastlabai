# Bolt's Journal — Critical Performance Learnings Only

This journal contains only critical performance learnings that are specific to the codebase architecture or represent surprising findings.

## 2026-08-01 - [Initial setup: Database Indexing & Query Formats]
**Learning:** SQLite database tables without explicit indexes default to O(N) table scans on foreign keys and frequently filtered columns. Applying functions like `date(created_at)` prevents the query planner from using indexes even if they are created. Range queries on text ISO8601 timestamps are fully indexable and highly performant.
**Action:** Always verify schema definition in SQLite/relational databases, ensure key columns have appropriate composite indexes, and write range queries using ISO8601 strings (e.g., `created_at >= date('now')`) instead of functional queries.

## 2026-08-01 - [Deserialization Overhead vs Indexing Speedups]
**Learning:** When benchmarking query performance in Python, fetching very large results (e.g. 16,000 rows representing 1/3 of a 50k DB) can bottleneck in the Python-level SQLite deserialization/object-creation layer, making database index speedups appear minimal. However, when querying realistic individual user slices (e.g., 10 rows), the indexed queries are 160x faster (0.038ms vs 6.08ms). For count limits, avoiding full table scans via indexing yields >360x faster responses.
**Action:** Always verify query performance with realistic slice sizes rather than bloated test-sets that might shift the bottleneck to python memory allocation.
