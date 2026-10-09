NOTES = []

NOTES.append(("SQL Fundamentals and Joins", r'''
We'll use these tables throughout:
```sql
CREATE TABLE department (id INT PRIMARY KEY, name VARCHAR(50));
CREATE TABLE employee (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100), salary DECIMAL(10,2),
  dept_id INT, manager_id INT, hired_on DATE,
  FOREIGN KEY (dept_id) REFERENCES department(id)
);
```

## Logical order of execution (very commonly asked)
`FROM/JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT (window functions here) -> DISTINCT -> ORDER BY -> LIMIT/OFFSET`
That's why you can't use a SELECT alias in WHERE (it doesn't exist yet), but you can in ORDER BY (MySQL also allows aliases in HAVING and GROUP BY as an extension).

## DDL, DML, DCL, TCL
- DDL: `CREATE, ALTER, DROP, TRUNCATE, RENAME` (auto-commit in MySQL).
- DML: `SELECT, INSERT, UPDATE, DELETE`.
- DCL: `GRANT, REVOKE`. TCL: `COMMIT, ROLLBACK, SAVEPOINT`.

**DELETE vs TRUNCATE vs DROP:** DELETE removes rows (optionally with WHERE), logs each row, fires triggers, can be rolled back. TRUNCATE removes all rows quickly by recreating the table, resets AUTO_INCREMENT, can't be rolled back in MySQL, no triggers. DROP removes the table structure entirely.

## Joins
```sql
-- INNER: only matching rows
SELECT e.name, d.name AS dept FROM employee e
JOIN department d ON d.id = e.dept_id;

-- LEFT: all employees, dept NULL if none
SELECT e.name, d.name FROM employee e
LEFT JOIN department d ON d.id = e.dept_id;

-- Anti-join: departments with no employees
SELECT d.name FROM department d
LEFT JOIN employee e ON e.dept_id = d.id
WHERE e.id IS NULL;

-- SELF JOIN: employee with manager name
SELECT e.name AS emp, m.name AS manager
FROM employee e LEFT JOIN employee m ON m.id = e.manager_id;

-- CROSS JOIN: cartesian product (sizes x colors)
SELECT s.size, c.color FROM sizes s CROSS JOIN colors c;
```
- **RIGHT JOIN**: mirror of LEFT; rarely used (rewrite as LEFT).
- **FULL OUTER JOIN**: not supported in MySQL; emulate with `LEFT JOIN ... UNION ... RIGHT JOIN`.
- Condition placement matters with outer joins: a filter on the right table in `WHERE` turns a LEFT JOIN into an INNER JOIN; put it in `ON` to keep unmatched rows.
```sql
-- keeps all departments, counts only employees hired in 2024
SELECT d.name, COUNT(e.id) FROM department d
LEFT JOIN employee e ON e.dept_id = d.id AND YEAR(e.hired_on) = 2024
GROUP BY d.name;
```

## Row counts quiz
Table A has 3 rows, B has 4 rows. INNER JOIN on a key: 0 to 12 rows depending on matches (duplicates multiply). CROSS JOIN: 12. LEFT JOIN: at least 3.

## UNION vs UNION ALL
UNION removes duplicates (sort/hash cost); UNION ALL keeps all rows and is faster. Column counts and types must match.

## NULL handling
- `NULL = NULL` is unknown, not true. Use `IS NULL` / `IS NOT NULL`, or MySQL's null-safe `<=>`.
- Aggregates ignore NULLs except `COUNT(*)`.
- `COALESCE(a, b, c)` returns the first non-null; `IFNULL(a, b)` MySQL-specific.
- `NOT IN (subquery)` returns no rows if the subquery contains a NULL — prefer `NOT EXISTS`.

## Keys and constraints
PRIMARY KEY (unique + not null, one per table, clustered index in InnoDB), UNIQUE (allows multiple NULLs in MySQL), FOREIGN KEY (referential integrity; `ON DELETE CASCADE/SET NULL/RESTRICT`), NOT NULL, CHECK (enforced since MySQL 8.0.16), DEFAULT. Candidate key, composite key, surrogate key (auto-increment id) vs natural key (email, PAN).

## CHAR vs VARCHAR, data types
CHAR(n) fixed length (padded), good for fixed codes; VARCHAR(n) variable length with a length prefix. Use DECIMAL for money (never FLOAT/DOUBLE — binary rounding errors). DATETIME (no timezone, 1000-9999) vs TIMESTAMP (stored as UTC, converted to session time zone, range until 2038). Use `utf8mb4` (real UTF-8 incl. emoji), not `utf8` (3-byte alias).
'''))

NOTES.append(("GROUP BY, HAVING, Aggregates, Subqueries and CTEs", r'''
## Aggregates and GROUP BY
```sql
SELECT dept_id, COUNT(*) AS cnt, AVG(salary) AS avg_sal, MAX(salary) AS max_sal
FROM employee
WHERE hired_on >= '2020-01-01'      -- filters rows BEFORE grouping
GROUP BY dept_id
HAVING COUNT(*) > 5                 -- filters groups AFTER grouping
ORDER BY avg_sal DESC;
```
- **WHERE vs HAVING**: WHERE filters individual rows and can't use aggregates; HAVING filters groups and can. Put non-aggregate filters in WHERE (cheaper — fewer rows to group).
- Every non-aggregated column in SELECT must be in GROUP BY (MySQL's `ONLY_FULL_GROUP_BY` mode, default since 5.7, enforces this).
- `COUNT(*)` counts rows; `COUNT(col)` counts non-null values; `COUNT(DISTINCT col)` counts unique non-nulls.
- `GROUP_CONCAT(name ORDER BY name SEPARATOR ', ')` concatenates values per group.
- `WITH ROLLUP` adds subtotal rows.

## Conditional aggregation (pivot)
```sql
SELECT dept_id,
       SUM(CASE WHEN gender = 'M' THEN 1 ELSE 0 END) AS male,
       SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) AS female
FROM employee GROUP BY dept_id;
```

## Subqueries
```sql
-- Scalar subquery
SELECT name FROM employee WHERE salary > (SELECT AVG(salary) FROM employee);

-- IN subquery
SELECT name FROM employee WHERE dept_id IN (SELECT id FROM department WHERE name IN ('IT','HR'));

-- Correlated subquery: runs per outer row (conceptually)
SELECT e.name, e.salary FROM employee e
WHERE e.salary > (SELECT AVG(salary) FROM employee x WHERE x.dept_id = e.dept_id);

-- EXISTS: stops at first match; NULL-safe
SELECT d.name FROM department d
WHERE EXISTS (SELECT 1 FROM employee e WHERE e.dept_id = d.id);

-- Derived table (subquery in FROM)
SELECT dept_id, avg_sal FROM (
  SELECT dept_id, AVG(salary) AS avg_sal FROM employee GROUP BY dept_id
) t WHERE avg_sal > 50000;
```
**IN vs EXISTS**: modern MySQL optimises both into semi-joins in most cases. Use `NOT EXISTS` over `NOT IN` when NULLs are possible. **Subquery vs JOIN**: joins are often clearer and historically faster in MySQL; MySQL 8 rewrites many subqueries anyway — check EXPLAIN.

## Common Table Expressions (MySQL 8+)
```sql
WITH dept_avg AS (
  SELECT dept_id, AVG(salary) AS avg_sal FROM employee GROUP BY dept_id
)
SELECT e.name, e.salary, d.avg_sal
FROM employee e JOIN dept_avg d ON d.dept_id = e.dept_id
WHERE e.salary > d.avg_sal;
```
CTEs improve readability, can be referenced multiple times in a query, and can be **recursive**:
```sql
-- Org hierarchy under manager 1
WITH RECURSIVE chain AS (
  SELECT id, name, manager_id, 1 AS lvl FROM employee WHERE id = 1
  UNION ALL
  SELECT e.id, e.name, e.manager_id, c.lvl + 1
  FROM employee e JOIN chain c ON e.manager_id = c.id
)
SELECT * FROM chain;

-- Generate dates (fill gaps in reports)
WITH RECURSIVE d AS (
  SELECT DATE('2025-01-01') AS dt UNION ALL SELECT dt + INTERVAL 1 DAY FROM d WHERE dt < '2025-01-31'
) SELECT dt FROM d;
```
**Subquery vs CTE**: functionally similar; CTEs are named, reusable within the statement, and support recursion. In MySQL 8 a CTE may be merged into the outer query or materialised once. A **view** is a stored, reusable named query at the schema level; a CTE lives only for one statement.

## CASE expressions
```sql
SELECT name,
  CASE WHEN salary >= 100000 THEN 'High'
       WHEN salary >= 50000 THEN 'Medium'
       ELSE 'Low' END AS band
FROM employee;
```
Also usable in ORDER BY (custom sort order) and UPDATE (`SET salary = CASE ... END`).
'''))

NOTES.append(("Window Functions", r'''
Window functions compute a value for each row using a set of related rows (the window) **without collapsing rows** like GROUP BY does. Available in MySQL 8+.

```sql
function() OVER (PARTITION BY ... ORDER BY ... [ROWS|RANGE frame])
```

## Ranking: ROW_NUMBER vs RANK vs DENSE_RANK
Salaries: 100, 90, 90, 80
| salary | ROW_NUMBER | RANK | DENSE_RANK |
|---|---|---|---|
| 100 | 1 | 1 | 1 |
| 90 | 2 | 2 | 2 |
| 90 | 3 | 2 | 2 |
| 80 | 4 | 4 | 3 |
- ROW_NUMBER: unique sequential number (ties broken arbitrarily unless ORDER BY is unique).
- RANK: ties share a rank; gaps follow.
- DENSE_RANK: ties share a rank; no gaps — use for "Nth highest salary".

```sql
-- Top 3 salaries per department (distinct salary levels)
SELECT * FROM (
  SELECT e.*, DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rnk
  FROM employee e
) t WHERE rnk <= 3;
```
You can't filter window results in WHERE (computed after WHERE) — wrap in a subquery/CTE. Other ranking: `NTILE(4)` (quartiles), `PERCENT_RANK()`, `CUME_DIST()`.

## Aggregate windows
```sql
SELECT name, dept_id, salary,
  AVG(salary) OVER (PARTITION BY dept_id)                AS dept_avg,
  salary - AVG(salary) OVER (PARTITION BY dept_id)       AS diff_from_avg,
  SUM(salary) OVER ()                                    AS company_total,
  ROUND(100 * salary / SUM(salary) OVER (PARTITION BY dept_id), 2) AS pct_of_dept
FROM employee;
```

## Running totals and moving averages (frames)
```sql
SELECT order_date, amount,
  SUM(amount) OVER (ORDER BY order_date)                                         AS running_total,
  AVG(amount) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg_7d
FROM daily_sales;
```
- With ORDER BY and no frame, the default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — rows with equal ORDER BY values (peers) are included together. Use `ROWS` for strict row-by-row running totals when dates repeat.
- `ROWS` counts physical rows; `RANGE` uses value ranges.

## LAG / LEAD
```sql
-- Month-over-month growth
SELECT month, revenue,
  LAG(revenue) OVER (ORDER BY month) AS prev,
  ROUND(100 * (revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month), 2) AS growth_pct
FROM monthly_revenue;

-- Days between consecutive logins per user
SELECT user_id, login_date,
  DATEDIFF(login_date, LAG(login_date) OVER (PARTITION BY user_id ORDER BY login_date)) AS gap_days
FROM logins;
```
`LAG(col, n, default)`, `LEAD(col, n, default)`.

## FIRST_VALUE / LAST_VALUE / NTH_VALUE
```sql
SELECT name, dept_id, salary,
  FIRST_VALUE(name) OVER (PARTITION BY dept_id ORDER BY salary DESC) AS top_earner
FROM employee;
```
`LAST_VALUE` needs a full frame (`ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`), otherwise it returns the current row.

## Named windows
```sql
SELECT name, RANK() OVER w, SUM(salary) OVER w
FROM employee WINDOW w AS (PARTITION BY dept_id ORDER BY salary DESC);
```

## Gaps and islands (consecutive sequences)
Classic trick: `value - ROW_NUMBER()` is constant within a consecutive run.
```sql
-- Streaks of consecutive login days per user
WITH x AS (
  SELECT user_id, login_date,
         DATE_SUB(login_date, INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) DAY) AS grp
  FROM (SELECT DISTINCT user_id, login_date FROM logins) d
)
SELECT user_id, MIN(login_date) AS start_dt, MAX(login_date) AS end_dt, COUNT(*) AS streak
FROM x GROUP BY user_id, grp HAVING COUNT(*) >= 3;
```

## Window vs GROUP BY
GROUP BY returns one row per group; windows keep every row and add computed columns — perfect for "show each employee with their department average" or rankings. Window functions are evaluated after WHERE/GROUP BY/HAVING and before ORDER BY/LIMIT.
'''))

NOTES.append(("Indexes in MySQL InnoDB: B+Trees, Clustered, Composite, Covering", r'''
An index is a data structure that lets the database find rows without scanning the whole table — like a book's index. Trade-off: faster reads, slower writes (every INSERT/UPDATE/DELETE maintains indexes) and extra storage.

## B+Tree structure
InnoDB indexes are B+Trees:
- Balanced: all leaves at the same depth, so lookups are O(log n) — typically 3-4 levels even for hundreds of millions of rows, because each 16KB page holds hundreds of keys (high fan-out).
- Internal nodes hold only keys for navigation; **leaf nodes hold the data** (or pointers) and are linked in a doubly linked list — making **range scans** and ORDER BY efficient.
- Why not a hash index? Hash gives O(1) equality but no range queries, sorting or prefix matching. (InnoDB has an internal *adaptive hash index* on top of B+Trees for hot lookups; the MEMORY engine supports hash indexes.)
- Why not a binary tree? Too deep -> too many disk reads.

## Clustered vs secondary indexes
- **Clustered index** = the PRIMARY KEY. In InnoDB, the table data itself is stored in the leaf pages of the PK B+Tree, ordered by PK. One per table. If no PK, InnoDB uses the first NOT NULL UNIQUE index, or a hidden 6-byte row id.
- **Secondary index** leaves store the indexed columns **+ the primary key value**. A lookup via a secondary index finds the PK, then traverses the clustered index to fetch the row (a "bookmark lookup"/double lookup).
- Implications: keep the PK small (BIGINT, not long VARCHAR/UUID strings) because it's copied into every secondary index; sequential PKs (AUTO_INCREMENT) avoid page splits — random UUIDv4 PKs cause fragmentation (use UUIDv7/ordered or BINARY(16)).

## Composite indexes and the leftmost prefix rule
```sql
CREATE INDEX idx_dept_sal_hire ON employee (dept_id, salary, hired_on);
```
The index is sorted by dept_id, then salary within dept, then hired_on. It can be used for:
- `WHERE dept_id = 5` yes
- `WHERE dept_id = 5 AND salary > 50000` yes (range on salary — columns after a range can't be used for seeking, so hired_on won't help seek)
- `WHERE dept_id = 5 ORDER BY salary` yes, no filesort
- `WHERE salary > 50000` **no** (leftmost column missing) — may do full index scan at best
- `WHERE dept_id = 5 AND hired_on = '2024-01-01'` uses dept_id part only (MySQL 8 index condition pushdown helps filter)
MySQL 8.0.13+ has **skip scan** for some cases where the leading column has few distinct values.

**Column order guidelines:** equality columns first, then range/sort columns; more selective columns earlier among equality columns; match common query patterns. An index on (a, b) makes a separate index on (a) redundant.

## Covering index
If an index contains all columns a query needs, MySQL answers from the index alone — no clustered lookup. EXPLAIN shows `Using index`.
```sql
-- covered by idx_dept_sal_hire (plus PK id implicitly)
SELECT id, salary FROM employee WHERE dept_id = 5;
```

## When indexes are NOT used
- Function or expression on the column: `WHERE YEAR(hired_on) = 2024` -> rewrite as `hired_on >= '2024-01-01' AND hired_on < '2025-01-01'` (or use a functional index in MySQL 8.0.13+).
- Leading wildcard: `LIKE '%raj'` (but `LIKE 'raj%'` can use the index).
- Implicit type conversion: `WHERE phone = 9876543210` when phone is VARCHAR; charset/collation mismatches in joins.
- Leftmost prefix not satisfied in composite index.
- `OR` across different columns (sometimes index merge; often better as UNION).
- Low selectivity (e.g. `status` with 2 values, `gender`) — optimizer prefers full scan when it expects to read a large fraction of the table.
- Negations like `!=`, `NOT IN` often lead to scans.
- Stale statistics — run `ANALYZE TABLE`.

## Other index types
- **Unique index** — enforces uniqueness.
- **Prefix index** — `INDEX(name(10))` for long strings.
- **Full-text index** — `MATCH ... AGAINST` for text search (or use Elasticsearch).
- **Functional index** (8.0.13): `INDEX ((LOWER(email)))`.
- **Invisible index** (8.0): test dropping an index safely.
- **Descending index** (8.0): `INDEX (created_at DESC)`.
- Spatial indexes (R-tree).

## Choosing what to index
Index columns in WHERE, JOIN ON (foreign keys!), ORDER BY, and GROUP BY of frequent queries; prefer high cardinality; avoid over-indexing write-heavy tables; drop unused indexes (`sys.schema_unused_indexes`).
'''))

NOTES.append(("EXPLAIN and Query Optimization", r'''
## EXPLAIN
Prefix a query with `EXPLAIN` to see the optimizer's plan; `EXPLAIN ANALYZE` (MySQL 8.0.18+) actually runs it and shows real timings and row counts; `EXPLAIN FORMAT=TREE` gives a readable tree.
```sql
EXPLAIN SELECT e.name FROM employee e JOIN department d ON d.id = e.dept_id
WHERE d.name = 'IT' AND e.salary > 50000;
```
Key columns:
| Column | What to look for |
|---|---|
| `type` (access type) | Best to worst: `system` > `const` (PK/unique equality) > `eq_ref` (one row per join via PK/unique) > `ref` (non-unique index equality) > `range` (index range) > `index` (full index scan) > **`ALL` (full table scan — usually bad on big tables)** |
| `possible_keys` / `key` | Candidate indexes vs the one chosen (NULL = none) |
| `key_len` | How many bytes/columns of a composite index are used |
| `rows` | Estimated rows examined |
| `filtered` | % of rows remaining after the condition |
| `Extra` | `Using index` (covering, good), `Using where`, `Using index condition` (ICP), **`Using filesort`** (extra sort), **`Using temporary`** (temp table for GROUP BY/DISTINCT), `Using join buffer` (no index for the join) |

## Optimization checklist
1. **Find slow queries**: enable the slow query log (`long_query_time=1`), `performance_schema`, `sys.statements_with_runtimes_in_95th_percentile`, or APM tools; `pt-query-digest` to aggregate.
2. **EXPLAIN** them; look for `ALL`, large `rows`, filesort/temporary.
3. **Add or fix indexes**: composite indexes matching WHERE + ORDER BY; covering indexes for hot queries; index foreign keys.
4. **Make predicates sargable**: no functions on indexed columns, no leading wildcards, matching data types.
5. **Select only needed columns** — avoid `SELECT *` (more I/O, prevents covering indexes, breaks when schema changes).
6. **Pagination**: `LIMIT 100000, 20` still reads and discards 100,000 rows. Use keyset pagination:
```sql
SELECT id, name FROM orders WHERE id < :last_seen_id ORDER BY id DESC LIMIT 20;
```
Or "deferred join": select ids with the offset from a covering index, then join back.
7. **Avoid N+1** from the application — batch queries with `IN (...)` or joins.
8. **Rewrite**: correlated subqueries -> joins/window functions; `OR` on different columns -> `UNION ALL`; `NOT IN` -> `NOT EXISTS`/anti-join; `COUNT(*)` on huge tables -> maintained counters or approximate counts.
9. **Batch writes**: multi-row INSERTs, `LOAD DATA INFILE` for bulk loads; chunk huge UPDATE/DELETE (e.g. 5,000 rows per transaction) to avoid long locks and replication lag.
10. **Schema**: right data types (INT vs BIGINT, DECIMAL for money), avoid huge rows, consider partitioning very large time-series tables, archive old data.
11. **Statistics**: `ANALYZE TABLE` after big changes; optimizer hints (`FORCE INDEX`, `/*+ INDEX() */`) only as a last resort.
12. **Server config**: `innodb_buffer_pool_size` (~60-75% of RAM on a dedicated DB server) so the working set fits in memory; connection pool sizing on the app side.
13. **Caching** at app level (Redis) for hot read-mostly data; **read replicas** for read scaling.

## Example walkthrough
```sql
-- Slow: full scan + filesort
SELECT * FROM orders WHERE customer_id = 42 AND status = 'DELIVERED' ORDER BY created_at DESC LIMIT 10;
-- Fix: composite index matching equality columns then sort column
CREATE INDEX idx_orders_cust_status_created ON orders (customer_id, status, created_at);
-- EXPLAIN now: type=ref, key=idx_orders_cust_status_created, no filesort, rows ~10
```

## COUNT performance
InnoDB doesn't store an exact row count (MVCC means different transactions see different counts), so `COUNT(*)` scans the smallest index. `COUNT(*)` and `COUNT(1)` are equivalent in MySQL.

## Joins under the hood
MySQL uses nested-loop joins (with index lookups on the inner table) and, since 8.0.18, **hash joins** for equi-joins without indexes. Always index join columns on the inner (looked-up) side.
'''))

NOTES.append(("Normalization and Schema Design", r'''
Normalization organises tables to reduce redundancy and avoid update/insert/delete anomalies.

## Anomalies in an unnormalized table
`orders(order_id, customer_name, customer_phone, product, price)`:
- **Update anomaly**: customer changes phone -> must update many rows; miss one -> inconsistency.
- **Insert anomaly**: can't store a new customer until they order.
- **Delete anomaly**: deleting the last order loses the customer's info.

## Normal forms
- **1NF**: atomic values (no comma-separated lists or repeating groups), each row unique (primary key).
  Bad: `phones = '98..., 97...'`. Fix: separate `customer_phone` table.
- **2NF**: 1NF + no **partial dependency** — every non-key column depends on the **whole** composite key.
  `order_item(order_id, product_id, qty, product_name)`: `product_name` depends only on `product_id` -> move to `product`.
- **3NF**: 2NF + no **transitive dependency** — non-key columns depend only on the key, not on other non-key columns.
  `employee(id, dept_id, dept_name)`: `dept_name` depends on `dept_id` -> move to `department`.
  Memory aid: "the key, the whole key, and nothing but the key."
- **BCNF**: for every functional dependency X -> Y, X must be a superkey. Stricter 3NF; matters with overlapping candidate keys.
- 4NF (no multi-valued dependencies) and 5NF — rarely asked.

## Denormalization
Intentionally adding redundancy for read performance: storing `order_total` instead of summing items, `customer_name` in orders for invoices (also historically accurate), counters (`comment_count`), reporting tables, materialised views (emulated in MySQL with summary tables refreshed by jobs/triggers). Trade-off: faster reads, more complex writes and risk of inconsistency. OLTP systems are usually ~3NF; analytics/OLAP uses denormalized star schemas (fact + dimension tables).

## Relationship modelling
- **One-to-one**: user <-> user_profile (FK with UNIQUE, or shared PK).
- **One-to-many**: department -> employees (FK on the "many" side).
- **Many-to-many**: students <-> courses via a junction table `enrollment(student_id, course_id, PRIMARY KEY(student_id, course_id), enrolled_on)`.

## Practical schema design tips
- Surrogate `BIGINT AUTO_INCREMENT` PKs for most tables; unique constraints on natural keys (email).
- Index all foreign keys.
- Money: `DECIMAL(12,2)` (or store paise as BIGINT). Never FLOAT.
- Timestamps: store in UTC; `created_at`, `updated_at` columns.
- Enums: VARCHAR with CHECK or a lookup table is more flexible than MySQL ENUM (changing ENUM requires ALTER).
- Soft delete (`deleted_at`) vs hard delete — consider unique constraints and query filters.
- Audit/history tables for compliance.
- JSON columns (MySQL 5.7+) for flexible attributes, with generated columns + indexes for fields you filter on — but don't use JSON to avoid modelling.
- Large tables: plan for partitioning (by date range), archiving, and online schema change tools (gh-ost, pt-online-schema-change, or MySQL 8 INSTANT/INPLACE DDL).

## Example: e-commerce core schema
```sql
customer(id PK, email UNIQUE, name, created_at)
address(id PK, customer_id FK, line1, city, pincode)
product(id PK, sku UNIQUE, name, price DECIMAL(10,2), stock INT)
orders(id PK, customer_id FK, status, total DECIMAL(12,2), created_at, INDEX(customer_id, created_at))
order_item(order_id FK, product_id FK, qty, unit_price, PRIMARY KEY(order_id, product_id))
payment(id PK, order_id FK UNIQUE, amount, status, gateway_ref UNIQUE)
```
Note `order_item.unit_price` is deliberately copied from product: price at time of purchase must not change when the catalog price changes — not every duplication is a normalization violation.
'''))

NOTES.append(("Transactions, ACID and Isolation Levels in InnoDB", r'''
## ACID
- **Atomicity**: all statements in a transaction succeed or none do (InnoDB uses the **undo log** to roll back).
- **Consistency**: the transaction moves the DB from one valid state to another (constraints, FKs, application invariants).
- **Isolation**: concurrent transactions don't see each other's intermediate states (per isolation level; MVCC + locks).
- **Durability**: once committed, changes survive crashes (**redo log** / write-ahead logging, flushed per `innodb_flush_log_at_trx_commit=1`; doublewrite buffer protects against torn pages).

```sql
START TRANSACTION;
UPDATE account SET balance = balance - 500 WHERE id = 1;
UPDATE account SET balance = balance + 500 WHERE id = 2;
COMMIT;      -- or ROLLBACK;
SAVEPOINT s1; ROLLBACK TO s1;
```
MySQL runs in **autocommit** mode by default: each statement is its own transaction unless you start one explicitly. DDL causes an implicit commit.

## Concurrency anomalies
- **Dirty read**: T1 reads T2's uncommitted change; T2 rolls back -> T1 used data that never existed.
- **Non-repeatable read**: T1 reads a row, T2 updates and commits it, T1 re-reads and gets a different value.
- **Phantom read**: T1 runs a range query, T2 inserts a matching row and commits, T1 re-runs and sees a new row.
- **Lost update**: two transactions read the same value and both write back based on it; one update is overwritten (e.g. both read stock=10 and write 9).
- **Write skew**: two transactions read overlapping data and update disjoint rows, jointly violating an invariant (two doctors both going off-call).

## Isolation levels
| Level | Dirty | Non-repeatable | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | Yes | Yes | Yes |
| READ COMMITTED | No | Yes | Yes |
| **REPEATABLE READ** (InnoDB default) | No | No | Mostly prevented* |
| SERIALIZABLE | No | No | No |

*In InnoDB REPEATABLE READ, **consistent (snapshot) reads** see a snapshot taken at the first read of the transaction, so plain SELECTs never see phantoms. **Locking reads** (`SELECT ... FOR UPDATE`, UPDATE, DELETE) read the latest committed data and use **next-key locks** (record + gap) to block inserts into the scanned range, preventing phantoms for those reads. Mixing snapshot reads and locking reads in one transaction can still show surprising results.

Oracle and PostgreSQL default to READ COMMITTED; many high-throughput MySQL shops also switch to READ COMMITTED (fewer gap locks, fewer deadlocks) and handle anomalies explicitly.
```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SELECT @@transaction_isolation;
```
SERIALIZABLE in InnoDB turns plain SELECTs into `SELECT ... FOR SHARE` (when autocommit is off) — lots of locking, low concurrency.

## Preventing lost updates
```sql
-- 1. Atomic update (best when possible)
UPDATE product SET stock = stock - 1 WHERE id = 7 AND stock > 0;   -- check affected rows = 1

-- 2. Pessimistic lock
START TRANSACTION;
SELECT stock FROM product WHERE id = 7 FOR UPDATE;   -- others block on this row
UPDATE product SET stock = stock - 1 WHERE id = 7;
COMMIT;

-- 3. Optimistic lock (version column; JPA @Version)
UPDATE product SET stock = 9, version = version + 1 WHERE id = 7 AND version = 3;  -- 0 rows -> retry
```

## Long transactions are harmful
They hold locks (blocking others), keep old row versions in the undo log (history list grows, purge lags, queries slow down), and increase deadlock odds and replication lag. Keep transactions short; never wait for user input or remote HTTP calls inside one.
'''))

NOTES.append(("InnoDB Locking, MVCC and Deadlocks", r'''
## MVCC (Multi-Version Concurrency Control)
InnoDB lets readers and writers not block each other:
- Each row has hidden columns: `DB_TRX_ID` (last transaction that modified it) and `DB_ROLL_PTR` (pointer to the previous version in the **undo log**).
- When a transaction does a consistent read, it creates a **read view**: the list of transactions active at that moment. For each row, InnoDB walks the undo chain back to the newest version that was committed before the read view (and is not from an active transaction).
- REPEATABLE READ: one read view per transaction (created at the first consistent read) -> same results every time.
- READ COMMITTED: a new read view per statement -> sees newly committed data.
- Plain `SELECT`s take **no locks**; old versions are purged once no read view needs them.

## Lock types
- **Shared (S)** lock: `SELECT ... FOR SHARE` (`LOCK IN SHARE MODE`) — others can read-lock but not write.
- **Exclusive (X)** lock: `SELECT ... FOR UPDATE`, UPDATE, DELETE — no other S or X locks.
- **Intention locks** (IS/IX) at table level signal row locks inside, so table-level locks can be checked quickly.
- InnoDB locks are on **index records**, not physical rows. If a query has no usable index, it scans (and locks) every row it examines — effectively locking the whole table for UPDATE/DELETE. Index your WHERE columns in updates!

## Record, gap and next-key locks
- **Record lock**: locks an index record.
- **Gap lock**: locks the gap between index records, preventing inserts into it (only in REPEATABLE READ+).
- **Next-key lock**: record lock + gap lock before it — the default for locking reads/range scans in REPEATABLE READ; prevents phantoms.
- **Insert intention lock**: a special gap lock taken by INSERT; multiple inserts into the same gap at different positions don't conflict.
- For a unique index equality lookup that finds a row, InnoDB takes just a record lock (no gap).
```sql
-- T1 (REPEATABLE READ)
SELECT * FROM employee WHERE salary BETWEEN 50000 AND 60000 FOR UPDATE;
-- T2 trying INSERT with salary 55000 blocks until T1 commits (gap locked) - if salary is indexed
```

## Table locks and metadata locks
`LOCK TABLES t WRITE` (rarely used with InnoDB). **Metadata locks (MDL)**: DDL (ALTER) needs an exclusive MDL and waits for running transactions on that table; meanwhile new queries queue behind it — a long-running transaction plus an ALTER can freeze a table. Use online DDL (`ALGORITHM=INSTANT/INPLACE`, `LOCK=NONE`) or gh-ost.

## SKIP LOCKED and NOWAIT (MySQL 8)
```sql
-- job queue: each worker grabs different rows without waiting
SELECT id FROM jobs WHERE status = 'PENDING' ORDER BY id LIMIT 10 FOR UPDATE SKIP LOCKED;
-- fail immediately instead of waiting
SELECT * FROM seat WHERE id = 12 FOR UPDATE NOWAIT;
```
Useful for outbox relays, ticket/seat booking, and work queues.

## Deadlocks
Two transactions each hold a lock the other needs:
```
T1: UPDATE account SET ... WHERE id = 1;   T2: UPDATE account SET ... WHERE id = 2;
T1: UPDATE account SET ... WHERE id = 2;   (waits for T2)
T2: UPDATE account SET ... WHERE id = 1;   (waits for T1) -> deadlock
```
InnoDB **detects deadlocks automatically** (wait-for graph) and rolls back the transaction with less work (the "victim"), returning error 1213 `ER_LOCK_DEADLOCK`. The other proceeds. If detection is disabled, `innodb_lock_wait_timeout` (default 50s) applies (error 1205).

Diagnose: `SHOW ENGINE INNODB STATUS` (LATEST DETECTED DEADLOCK section), `innodb_print_all_deadlocks=ON`, `performance_schema.data_locks` and `data_lock_waits` (8.0).

Prevention:
- Access rows/tables in a **consistent order** (e.g. always lock lower account id first).
- Keep transactions short; commit quickly.
- Index columns used in UPDATE/DELETE WHERE so fewer rows/gaps are locked.
- Use READ COMMITTED to reduce gap locking where acceptable.
- Avoid large range updates; batch them.
- **Retry** the transaction on deadlock errors in application code (Spring: catch `DeadlockLoserDataAccessException`/`CannotAcquireLockException`, or use `@Retryable`).

## Optimistic vs pessimistic, again
Pessimistic (`FOR UPDATE`) suits high-contention hot rows (inventory in a flash sale) but limits throughput; optimistic (version column) suits low-contention edits and scales better; atomic conditional UPDATEs are often the simplest correct option.
'''))

NOTES.append(("Views, Stored Procedures, Functions and Triggers", r'''
## Views
A view is a stored named query; it doesn't store data (MySQL has no native materialised views).
```sql
CREATE VIEW v_dept_salary AS
SELECT d.name AS dept, COUNT(e.id) AS headcount, AVG(e.salary) AS avg_salary
FROM department d LEFT JOIN employee e ON e.dept_id = d.id
GROUP BY d.name;

SELECT * FROM v_dept_salary WHERE headcount > 10;
```
Uses: simplify complex joins, expose a restricted subset of columns for security (grant access to the view, not the table), provide backward compatibility after schema changes. Simple views (single table, no aggregates/DISTINCT/GROUP BY) are **updatable**; `WITH CHECK OPTION` prevents inserting rows the view can't see. Performance: MySQL either merges the view into the outer query (MERGE algorithm) or materialises it into a temp table (TEMPTABLE, for aggregates) — the latter can't use indexes on the outer filter efficiently.

**Materialised view emulation**: summary table refreshed by a scheduled event/job or maintained via triggers.

## Stored procedures
```sql
DELIMITER //
CREATE PROCEDURE give_raise(IN p_dept INT, IN p_pct DECIMAL(5,2), OUT p_rows INT)
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
  START TRANSACTION;
  UPDATE employee SET salary = salary * (1 + p_pct / 100) WHERE dept_id = p_dept;
  SET p_rows = ROW_COUNT();
  COMMIT;
END //
DELIMITER ;

CALL give_raise(3, 10, @n); SELECT @n;
```
Parameters: IN, OUT, INOUT. Support variables, IF/CASE, loops (WHILE, REPEAT, LOOP), cursors, error handlers.
Pros: fewer network round trips, logic close to data, precompiled per connection, security via EXECUTE grants. Cons: harder to version-control, test, debug and scale (DB CPU is the most expensive to scale); vendor lock-in; business logic split between app and DB. Modern product companies keep most logic in the service layer and use procedures sparingly (batch jobs, data migrations). Calling from Spring: `@Procedure` in Spring Data JPA or `SimpleJdbcCall`.

## Functions
```sql
CREATE FUNCTION tax(amount DECIMAL(10,2)) RETURNS DECIMAL(10,2) DETERMINISTIC
RETURN amount * 0.18;

SELECT name, salary, tax(salary) FROM employee;
```
**Procedure vs function**: a function returns exactly one value and can be used inside SQL statements (SELECT/WHERE); it can't commit/rollback. A procedure is invoked with CALL, can return multiple result sets and OUT params, and can manage transactions.

## Triggers
Code that runs automatically `BEFORE` or `AFTER` an `INSERT`, `UPDATE` or `DELETE`, per row, with access to `NEW` and `OLD` row values.
```sql
CREATE TRIGGER trg_salary_audit
AFTER UPDATE ON employee FOR EACH ROW
BEGIN
  IF NEW.salary <> OLD.salary THEN
    INSERT INTO salary_audit(emp_id, old_salary, new_salary, changed_at)
    VALUES (OLD.id, OLD.salary, NEW.salary, NOW());
  END IF;
END;

CREATE TRIGGER trg_email_lower BEFORE INSERT ON customer FOR EACH ROW
SET NEW.email = LOWER(NEW.email);
```
Uses: audit trails, derived columns, enforcing complex invariants. Drawbacks: hidden logic ("magic"), harder debugging, slows writes, run inside the same transaction, can cascade unexpectedly. Prefer application-level auditing (JPA auditing/Envers) or CDC (Debezium) for event streaming.

## Events (scheduler)
```sql
CREATE EVENT purge_sessions ON SCHEDULE EVERY 1 HOUR
DO DELETE FROM sessions WHERE expires_at < NOW();
```
Requires `event_scheduler=ON`.

## Cursors
Iterate row by row inside procedures. Generally slow — prefer set-based SQL.
'''))

NOTES.append(("Replication, Scaling, Partitioning and MySQL Architecture", r'''
## MySQL architecture in brief
Client -> connection handling (thread per connection) -> parser -> optimizer (cost-based, chooses indexes/join order) -> executor -> **storage engine API** -> InnoDB (default, transactional, row-level locks, MVCC, FKs, crash recovery) or others (MyISAM: table locks, no transactions — legacy; MEMORY).

InnoDB internals: **buffer pool** (caches data and index pages in RAM; most important tuning knob), **redo log** (WAL for durability), **undo log** (rollbacks + MVCC), **doublewrite buffer**, change buffer (defers secondary index updates), adaptive hash index.

**Binary log (binlog)**: a server-level log of all data changes (row-based format by default), used for replication and point-in-time recovery; also the source for CDC tools like Debezium. Redo log is InnoDB-level for crash recovery; binlog is server-level for replication — a two-phase commit between them keeps them consistent.

## Replication
- **Source-replica (master-slave)**: the source writes changes to the binlog; each replica's I/O thread pulls events into its relay log; the SQL (applier) thread replays them. Replicas serve **reads**; the source handles writes.
- **Asynchronous** (default): source doesn't wait for replicas — fast, but a source crash can lose the last transactions and replicas can lag.
- **Semi-synchronous**: source waits until at least one replica has received (not applied) the event before acknowledging commit — less data loss risk, more latency.
- **Group Replication / InnoDB Cluster**: Paxos-based multi-node with automatic failover (single-primary mode typical). Managed services: AWS RDS/Aurora, Cloud SQL.
- **GTIDs** (global transaction IDs) make failover and replica repointing easier.
- Parallel replication (multi-threaded applier) reduces lag.

### Replication lag and read-your-writes
Reads from a replica right after a write may return stale data. Mitigations: read from the primary for a short period after a user's write (sticky session/flag), route critical reads to primary, monitor `Seconds_Behind_Source`, or wait for a GTID on the replica. In Spring, `AbstractRoutingDataSource` + `@Transactional(readOnly = true)` routes reads to replicas.

## Scaling strategy (in order)
1. Optimise queries and indexes; right-size the buffer pool.
2. **Caching** (Redis) for hot reads.
3. **Vertical scaling** (bigger instance).
4. **Read replicas** for read-heavy workloads.
5. **Partitioning** within one server for very large tables.
6. **Sharding** across servers when write volume or data size exceeds one primary.

## Partitioning (single server)
Split one logical table into physical partitions:
```sql
CREATE TABLE events (
  id BIGINT NOT NULL, created_at DATE NOT NULL, payload JSON,
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (YEAR(created_at)) (
  PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION p2025 VALUES LESS THAN (2026),
  PARTITION pmax  VALUES LESS THAN MAXVALUE
);
```
Types: RANGE, LIST, HASH, KEY. Benefits: **partition pruning** (queries filtering by the partition key only scan relevant partitions) and instant archiving (`ALTER TABLE ... DROP PARTITION` vs a huge DELETE). Constraints: the partition key must be part of every unique key/PK; FKs not supported on partitioned tables; queries not filtering by the key scan all partitions.

## Sharding (multiple servers)
Horizontal split of data across independent databases by a **shard key** (e.g. `customer_id`).
- Strategies: hash-based (even distribution, hard to re-shard — use consistent hashing or many logical shards mapped to fewer physical ones), range-based (easy range queries, hotspot risk), directory/lookup-based (flexible, lookup service needed), geo-based.
- Challenges: cross-shard joins and transactions, global unique IDs (Snowflake IDs, UUIDv7), re-sharding, hot shards, operational overhead.
- Tools: Vitess (YouTube, Slack), ProxySQL, Apache ShardingSphere, or app-level routing. Choose a shard key matching the dominant access pattern so most queries hit one shard.

**Partitioning vs sharding**: partitioning splits a table within one server; sharding distributes data across multiple servers.

## Backups and recovery
Logical backups (`mysqldump`, `mysqlpump`, MySQL Shell dump) vs physical (Percona XtraBackup, snapshots). Point-in-time recovery = full backup + replay binlogs. Test restores regularly.

## High availability
Primary + replicas with automatic failover (Orchestrator, InnoDB Cluster/MySQL Router, RDS Multi-AZ). The application should use a stable endpoint and retry on connection failure.

## SQL vs NoSQL quick take
Use relational DBs for structured data, joins, strong consistency and transactions (payments, orders). NoSQL for massive scale with simple access patterns (Cassandra/DynamoDB), flexible documents (MongoDB), caching/counters (Redis), search (Elasticsearch). Many systems use both (polyglot persistence).
'''))
