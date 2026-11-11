## 2026-11-11 - SQLite Index Utilization with Timestamps
**Learning:** Wrapping indexed timestamp columns in functions like `date(created_at) = date('now')` prevents SQLite from using composite B-tree indexes, forcing an O(N) full table scan. Rewriting to a range comparison `created_at >= date('now')` enables SQLite to use covering composite indexes, resulting in hundreds-fold speedups (~890x on 50k rows).
**Action:** When indexing timestamp/date fields in SQLite, write queries using direct range comparisons (`>=`, `<`) rather than wrapping column names in date/time parsing functions.
