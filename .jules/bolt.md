# Bolt's Journal - Critical Learnings

## 2026-08-14 - SQLite Indexable Range Queries vs Function Evaluation
**Learning:** Wrapping indexed columns in functions (e.g. `date(created_at) = date('now')`) prevents SQLite from utilizing composite indexes, causing full table scans (`SCAN roasts`). Converting the condition to an index-friendly range query (`created_at >= date('now')`) allows SQLite's query planner to execute a B-tree search (`SEARCH roasts USING COVERING INDEX`).
**Action:** When writing date-based filtering or rate-limiting queries in SQLite, use range comparison operators (`>=`, `<=`, `BETWEEN`) against raw datetime values rather than evaluating functions on the table column.
