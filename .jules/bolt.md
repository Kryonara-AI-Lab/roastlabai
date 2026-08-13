## 2025-05-20 - [SQLite Composite Indexing and SARGable Queries]
**Learning:** SQLite cannot use indexes for queries where database columns are wrapped inside functions like `date(created_at)`. Replacing un-indexable function evaluations with index-friendly, range-based expressions such as `created_at >= date('now')` (SARGable queries) allows the SQLite query planner to leverage composite indexes instead of resorting to full table scans.
**Action:** Always rewrite function-based column evaluations into range-based comparison operators when writing query filters on indexed columns in SQLite.
