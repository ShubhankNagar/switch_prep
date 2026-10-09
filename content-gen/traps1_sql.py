"""SQL traps (generic results checked with sqlite3; MySQL-specific behaviour called out explicitly)."""
from traps1_common import T

A = "sql"

TRAPS = [
T("trap-sql-null-comparison", A, "NULL = NULL and <> with NULLs", "Basic", "Very common",
r"""
`employee(id, name, manager_id)` has 6 rows. Their `manager_id` values are NULL, 1, 1, 1, 4, 4. What do the two
queries return?

```sql
-- Query A
SELECT COUNT(*) FROM employee WHERE manager_id = NULL;

-- Query B
SELECT COUNT(*) FROM employee WHERE manager_id <> 1;
```
""",
["1 and 3", "0 and 2", "1 and 2", "0 and 3"], 1,
"1 and 3: one row has a NULL manager, and three rows don't have manager 1.",
r"""
Candidates treat NULL as a value, like an empty string or zero. In SQL, NULL means 'unknown', and any comparison with
it (`=`, `<>`, `<`, even `NULL = NULL`) gives UNKNOWN, not TRUE. WHERE keeps only rows whose condition is TRUE, so the
NULL rows silently drop out of both queries.
""",
r"""
SQL uses three-valued logic: TRUE, FALSE and UNKNOWN. `manager_id = NULL` is UNKNOWN for every row, including the NULL
one, so Query A returns 0. Use `IS NULL` instead, which returns 1. In Query B, the row with a NULL manager evaluates
`NULL <> 1` to UNKNOWN and is filtered out, so only the two rows with manager 4 qualify: 2, not 3.

This bites in reports such as 'all orders not cancelled' (`status <> 'CANCELLED'`) when status can be NULL. Fixes: add
`OR manager_id IS NULL`, use `COALESCE`, or use MySQL's null-safe equality operator `<=>` (`NOT (manager_id <=> 1)`);
PostgreSQL has `IS DISTINCT FROM`. Aggregates such as `COUNT(col)`, `SUM` and `AVG` skip NULLs, and `NOT IN` with
NULLs is its own trap. Declaring columns `NOT NULL` wherever possible avoids most of this.
""",
r"""
```sql
SELECT COUNT(*) FROM employee WHERE manager_id IS NULL;                      -- 1
SELECT COUNT(*) FROM employee WHERE manager_id <> 1 OR manager_id IS NULL;   -- 3
SELECT COUNT(*) FROM employee WHERE NOT (manager_id <=> 1);                  -- 3 (MySQL null-safe equality)
```
""",
"Say 'three-valued logic' and give a real reporting bug it causes. That's more convincing than reciting IS NULL."),

T("trap-sql-not-in-with-null", A, "NOT IN with a NULL in the subquery", "Intermediate", "Very common",
r"""
Same `employee` table; the CEO's `manager_id` is NULL. This query should list employees who don't manage anyone. What
does it return?

```sql
SELECT name
FROM employee
WHERE id NOT IN (SELECT manager_id FROM employee);
```
""",
["The 4 employees who manage nobody", "An empty result", "An error, because the subquery returns a NULL",
 "All 6 employees"], 1,
"The four employees who aren't anyone's manager.",
r"""
NOT IN reads like plain English: 'id is not in this list'. Candidates don't expand it into what SQL actually
evaluates: `id <> v1 AND id <> v2 AND ...`. Once a single value in the list is NULL, one of those comparisons is
UNKNOWN, and the whole AND can never be TRUE.
""",
r"""
`x NOT IN (1, 4, NULL)` means `x <> 1 AND x <> 4 AND x <> NULL`. The last part is UNKNOWN for every x, so the whole
condition is either FALSE (when x is 1 or 4) or UNKNOWN (for everyone else), and never TRUE. The result is no rows at
all, with no error or warning. It's one of the most common silent bugs in reporting SQL, because it only appears once a
NULL sneaks into the subquery's column.

`IN` doesn't have this problem (a match is TRUE regardless of NULLs), which makes the bug look inconsistent. Fixes:
use `NOT EXISTS` (correlated, NULL-safe, and usually executed as an anti-join in MySQL 8), filter NULLs out inside the
subquery, or use `LEFT JOIN ... WHERE right.id IS NULL`.
""",
r"""
```sql
SELECT e.name
FROM employee e
WHERE NOT EXISTS (SELECT 1 FROM employee m WHERE m.manager_id = e.id);

-- or keep NOT IN, but exclude NULLs explicitly
SELECT name
FROM employee
WHERE id NOT IN (SELECT manager_id FROM employee WHERE manager_id IS NOT NULL);
```
""",
"Default to NOT EXISTS and explain why in one sentence. Interviewers love hearing that you avoid NOT IN on nullable columns out of habit."),

T("trap-sql-count-variants", A, "COUNT(*) vs COUNT(col) vs COUNT(DISTINCT col)", "Basic", "Common",
r"""
Across 6 rows, `employee.dept` holds 'ENG', 'ENG', 'ENG', 'HR', 'HR' and NULL. What does this return?

```sql
SELECT COUNT(*), COUNT(dept), COUNT(DISTINCT dept) FROM employee;
```
""",
["6, 6, 3", "6, 5, 2", "5, 5, 2", "6, 5, 3"], 1,
"6, 6, 3: COUNT counts rows, and DISTINCT counts NULL as one more value.",
r"""
People think every form of COUNT counts rows, and that DISTINCT treats NULL as another distinct value, the way GROUP BY
does. Aggregate functions applied to a column skip NULLs entirely. Only `COUNT(*)` counts rows no matter what they
contain.
""",
r"""
`COUNT(*)` counts rows: 6. `COUNT(dept)` counts non-NULL values: 5. `COUNT(DISTINCT dept)` counts distinct non-NULL
values: 2 (ENG and HR). Note the inconsistency that trips people up: `GROUP BY dept` *does* give NULL its own group
(3 groups), but `COUNT(DISTINCT dept)` ignores it. `SUM`, `AVG`, `MIN` and `MAX` skip NULLs the same way, so
`AVG(bonus)` averages only the rows that have a bonus, which differs from `SUM(bonus) / COUNT(*)`.

The classic bug is in LEFT JOIN reports. Counting orders per customer with `COUNT(*)` gives 1 for customers with no
orders, because the NULL-extended row is still a row. `COUNT(o.id)` correctly gives 0. `COUNT(1)` and `COUNT(*)` are
equivalent in MySQL, with no performance difference.
""",
r"""
```sql
-- orders per customer, including customers with none
SELECT c.id, c.name, COUNT(o.id) AS order_count     -- not COUNT(*)
FROM customer c
LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.name;
```
""",
"Volunteer the LEFT JOIN COUNT(*) vs COUNT(o.id) bug. It's the version that ships wrong numbers to dashboards."),

T("trap-sql-left-join-where-filter", A, "WHERE on the right table turns LEFT JOIN into INNER", "Intermediate", "Very common",
r"""
There are 6 employees. Asha has a PAID and a CANCELLED order, Bala has only a CANCELLED order, Dev has a PAID order,
and the others have no orders. The goal: all employees with their PAID orders, keeping employees who have none. How
many rows come back?

```sql
SELECT e.name, o.id
FROM employee e
LEFT JOIN orders o ON o.emp_id = e.id
WHERE o.status = 'PAID';
```
""",
["6", "2", "4", "8"], 1,
"6: a LEFT JOIN always keeps every row from the left table.",
r"""
Candidates know LEFT JOIN keeps unmatched left rows, but they forget the order of evaluation. The join produces rows
first, with NULLs for missing matches, and only then does WHERE filter them. A condition on a right-table column
rejects every NULL-extended row, so the outer join quietly behaves like an INNER JOIN.
""",
r"""
The LEFT JOIN produces each employee with each of their orders, plus a NULL-extended row for employees with no orders.
Then `WHERE o.status = 'PAID'` runs. For unmatched employees `o.status` is NULL, so the condition is UNKNOWN and the
row is dropped. Bala's only joined row has status CANCELLED, so it's dropped too. Only Asha's and Dev's paid orders
survive: 2 rows.

The fix is to move the right-table filter into the `ON` clause. That restricts which orders are *matched* without
removing any employees, so you get 6 rows, with NULLs for those without paid orders. Rule of thumb: conditions on the
outer (right) table go in `ON`; conditions on the preserved (left) table go in `WHERE`. `WHERE o.id IS NULL` is the
deliberate exception: it's how you find left rows with no match at all (an anti-join).
""",
r"""
```sql
SELECT e.name, o.id
FROM employee e
LEFT JOIN orders o
       ON o.emp_id = e.id
      AND o.status = 'PAID'        -- filter the right side inside ON
ORDER BY e.id;                     -- 6 rows; NULL where there is no paid order
```
""",
"State the rule 'right-table filters go in ON, left-table filters in WHERE' and mention the IS NULL anti-join as the deliberate exception."),

T("trap-sql-group-by-nonaggregated-column", A, "Non-aggregated column in GROUP BY (ONLY_FULL_GROUP_BY)", "Intermediate", "Very common",
r"""
The goal is the highest-paid employee in each department. On MySQL 8 with default settings, what happens?

```sql
SELECT dept, name, MAX(salary)
FROM employee
GROUP BY dept;
```
""",
["It returns each department with its top earner's name",
 "ERROR 1055: name is neither in GROUP BY nor functionally dependent on it (ONLY_FULL_GROUP_BY)",
 "It returns every employee",
 "It returns each department with an arbitrary name and the max salary, plus a warning"], 1,
"It returns each department with the name of the person who earns the max salary.",
r"""
Older MySQL accepted this query, and in small test data the results often *looked* right, so a generation of
developers learned it as valid. The idea that MAX() 'drags along' the rest of its row is intuitive but wrong.
Aggregation collapses the group, and the other columns have no defined row to come from.
""",
r"""
Since MySQL 5.7.5 the `ONLY_FULL_GROUP_BY` SQL mode is on by default, so this fails with ERROR 1055 ("Expression #2
of SELECT list is not in GROUP BY clause and contains nonaggregated column ... incompatible with
sql_mode=only_full_group_by"). With the mode switched off (legacy configs), MySQL returns *some* name from each group,
not necessarily the top earner's, which is worse because it looks plausible. PostgreSQL and SQL Server always reject
the query. SQLite happens to return the max row's name, which misleads people who test there.

MySQL does accept a non-aggregated column that is functionally dependent on the GROUP BY columns, for example when you
group by a primary key. The right approach for 'top row per group' is a window function (MySQL 8+) or a join back to
the per-group maximum. And remember: WHERE filters rows before grouping, HAVING filters groups after aggregation.
""",
r"""
```sql
SELECT dept, name, salary
FROM (
    SELECT dept, name, salary,
           RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rnk
    FROM employee
) ranked
WHERE rnk = 1;          -- RANK keeps ties; use ROW_NUMBER for exactly one row per department
```
""",
"Say that switching off ONLY_FULL_GROUP_BY to 'fix' the error is a red flag, then reach for a window function."),

T("trap-sql-index-sargability", A, "Functions on indexed columns kill the index", "Intermediate", "Very common",
r"""
`orders` has 50 million rows and an index on `created_at` (DATETIME). Which WHERE clause can use the index for a range
scan?

```sql
-- A
WHERE YEAR(created_at) = 2024 AND MONTH(created_at) = 3
-- B
WHERE DATE(created_at) = '2024-03-01'
-- C
WHERE created_at >= '2024-03-01' AND created_at < '2024-03-02'
-- D
WHERE DATE_FORMAT(created_at, '%Y-%m') = '2024-03'
```
""",
["A", "B", "C", "All of them, because MySQL rewrites date functions"], 2,
"All of them: the column is indexed, so any filter on it uses the index.",
r"""
Candidates think 'indexed column in WHERE means the index is used'. A B-tree index is sorted by the raw column value.
Wrapping the column in a function produces values the index doesn't contain, so MySQL has to compute the function for
every row. The queries still return correct results, so nothing warns you until the table is large.
""",
r"""
Only C compares the bare column with constants, so the optimizer can seek into the B-tree and scan just that range
(the predicate is 'sargable'). A, B and D apply a function to every row's `created_at`, so the index can't be used to
seek, which usually means a full scan (`type: ALL` in EXPLAIN).

Other common index killers: a leading wildcard (`name LIKE '%son'`, while `LIKE 'son%'` is fine); implicit type
conversion, such as a VARCHAR `phone` compared with a number (`WHERE phone = 9876543210`), which makes MySQL convert
every row, whereas an INT column compared with a string constant still uses its index; arithmetic on the column
(`WHERE price * 1.18 > 1000`); and mismatched charsets or collations in joins. MySQL 8.0.13+ supports functional
indexes if you really need an expression, but rewriting the predicate as a range is usually better. Always check with
`EXPLAIN`.
""",
r"""
```sql
-- all of March 2024, sargable
WHERE created_at >= '2024-03-01' AND created_at < '2024-04-01'

-- string column: compare with a string literal
WHERE phone = '9876543210'

-- confirm the plan uses the index
EXPLAIN SELECT * FROM orders
WHERE created_at >= '2024-03-01' AND created_at < '2024-04-01';
```
""",
"Use the word 'sargable', rewrite the predicate on the spot, and say you'd confirm with EXPLAIN. That's the full senior answer."),

T("trap-sql-composite-index-leftmost-prefix", A, "Composite index and the leftmost-prefix rule", "Intermediate", "Common",
r"""
`orders` has `INDEX idx_cust_status_date (customer_id, status, created_at)`. Which query **cannot** use this index to
seek?

```sql
-- A
SELECT * FROM orders WHERE customer_id = 7 AND status = 'PAID';
-- B
SELECT * FROM orders WHERE status = 'PAID' AND created_at > '2024-01-01';
-- C
SELECT * FROM orders WHERE status = 'PAID' AND customer_id = 7;
-- D
SELECT * FROM orders WHERE customer_id = 7 ORDER BY status, created_at;
```
""",
["A", "B", "C", "D"], 1,
"C, because its WHERE clause lists status before customer_id, which doesn't match the index order.",
r"""
There are two opposite misconceptions here. One is that the order of conditions in WHERE must match the index; it
doesn't, because the optimizer reorders them. The other is that any query mentioning indexed columns can use the index;
it can't. A composite index is sorted like a phone book (by the first column, then the second within it), so it can
only be entered from the left.
""",
r"""
A composite B-tree index on (customer_id, status, created_at) is sorted by customer_id, then by status within each
customer, then by created_at. It can serve any **leftmost prefix**: (customer_id), (customer_id, status), or all three.
To the optimizer, A and C are the same query (WHERE order is irrelevant), and both seek on the first two columns. D
seeks on customer_id and reads rows already ordered by status and created_at, which avoids a filesort.

B skips customer_id, so the rows with status = 'PAID' are scattered across the whole index and there's nothing to seek
on. MySQL 8.0.13+ has a 'skip scan' for some covering queries when the leading column has few distinct values, but
`SELECT *` doesn't qualify. One more rule: a range condition stops the seek at that column. With
`customer_id = 7 AND status > 'A' AND created_at = ...`, the created_at part can't narrow the seek. Put equality
columns first, then the range or sort column.
""",
r"""
```sql
-- for filters on status and date without customer_id, add an index that starts with status
CREATE INDEX idx_status_date ON orders (status, created_at);

EXPLAIN SELECT * FROM orders WHERE status = 'PAID' AND created_at > '2024-01-01';
-- compare `key` and `rows` in the plan before and after
```
""",
"Explain it with the phone-book analogy and finish with 'equality columns first, then range or sort'. That's how you design the index, not just read it."),

T("trap-sql-nth-highest-with-duplicates", A, "Nth highest salary with LIMIT/OFFSET and ties", "Basic", "Very common",
r"""
Salaries are 100, 90, 90, 70, 60, 50. A candidate writes this to get the **third-highest salary**. What does it
return, and what should it return?

```sql
SELECT salary
FROM employee
ORDER BY salary DESC
LIMIT 1 OFFSET 2;
```
""",
["70, which is correct", "90, but the answer should be 70", "60, but the answer should be 70", "NULL"], 1,
"70: skip the top two rows and take the next one.",
r"""
Candidates test with distinct values, where OFFSET N-1 works. With ties, OFFSET counts rows, not distinct values, so
the two 90s take up two positions. The second hidden requirement, returning NULL when there's no Nth salary, is also
usually missed, because `LIMIT` on an empty result returns no row at all.
""",
r"""
Sorted in descending order the rows are 100, 90, 90, 70, ..., so `OFFSET 2` lands on the second 90. 'Third-highest
salary' normally means the third distinct value, which is 70. Fixes: `SELECT DISTINCT salary ... LIMIT 1 OFFSET 2`,
or `DENSE_RANK()` (MySQL 8+), which gives ties the same rank without gaps, so `rnk = 3` is 70.

If there are fewer distinct salaries, the plain query returns an empty result. Interviewers (and the well-known
LeetCode version) usually expect a single NULL row, which you get by wrapping the query as a scalar subquery:
`SELECT (SELECT ...) AS third_highest`. For 'Nth highest per department', partition the window:
`DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC)`. Ask the interviewer whether ties count; asking is part of
the answer.
""",
r"""
```sql
-- third-highest distinct salary, NULL if it doesn't exist
SELECT (
    SELECT DISTINCT salary FROM employee
    ORDER BY salary DESC
    LIMIT 1 OFFSET 2
) AS third_highest;

-- MySQL 8+: window function, easy to adapt per department
SELECT DISTINCT salary
FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk FROM employee) r
WHERE rnk = 3;
```
""",
"Ask 'should ties count as one?' before writing anything. Clarifying the requirement is exactly what this question tests.",
["Amazon"]),

T("trap-sql-rank-dense-rank-row-number", A, "ROW_NUMBER vs RANK vs DENSE_RANK", "Basic", "Common",
r"""
Salaries: Asha 100, Bala 90, Chen 90, Dev 70. What are `rn`, `rnk` and `drnk` for Dev?

```sql
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn,
       RANK()       OVER (ORDER BY salary DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY salary DESC) AS drnk
FROM employee;
```
""",
["4, 4, 3", "4, 3, 3", "3, 3, 3", "4, 4, 4"], 0,
"4, 3, 3: they assume RANK carries on from the previous rank, like DENSE_RANK.",
r"""
The three functions differ only when there are ties, and practice data often has none. Candidates remember that 'RANK
handles ties' but not *how*: RANK leaves a gap after a tie, DENSE_RANK doesn't, and ROW_NUMBER ignores ties entirely,
numbering tied rows in an unpredictable order.
""",
r"""
`ROW_NUMBER` numbers the rows 1, 2, 3, 4 regardless of ties, so Dev is 4. Whether Bala or Chen gets 2 is arbitrary
unless you add a tie-breaker to the ORDER BY (such as `salary DESC, id`). `RANK` gives tied rows the same rank and then
skips: 1, 2, 2, 4. Dev is 4, like Olympic medals (two silvers, no bronze). `DENSE_RANK` gives ties the same rank with no
gaps: 1, 2, 2, 3, so Dev is 3.

Choosing correctly matters. 'Top 3 salaries' (distinct values) needs DENSE_RANK; 'top 3 people, ties included' needs
RANK; 'exactly one row per group' (latest order per customer, deduplication) needs ROW_NUMBER with a deterministic
ORDER BY. Window functions exist only in MySQL 8.0+. You can't filter on a window function in WHERE; wrap it in a
subquery or CTE.
""",
r"""
```sql
-- latest order per customer: ROW_NUMBER with a deterministic tie-breaker
WITH ranked AS (
    SELECT o.*,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC, id DESC) AS rn
    FROM orders o
)
SELECT * FROM ranked WHERE rn = 1;
```
""",
"Map each function to a business question (top-N distinct, top-N with ties, one row per group). That's what interviewers want beyond the definitions."),

T("trap-sql-delete-duplicates-mysql-1093", A, "Deleting duplicates in MySQL (ERROR 1093)", "Intermediate", "Very common",
r"""
You need to remove duplicate emails from `users`, keeping the row with the lowest id. What happens when you run this
on MySQL?

```sql
DELETE FROM users
WHERE id NOT IN (
    SELECT MIN(id) FROM users GROUP BY email
);
```
""",
["It deletes the duplicates and keeps the lowest id per email",
 "ERROR 1093: You can't specify target table 'users' for update in FROM clause",
 "It deletes every row", "It deletes nothing, because of NOT IN"], 1,
"It works: it keeps MIN(id) per email and deletes the rest.",
r"""
The logic is right, and the same statement works in PostgreSQL and SQLite, so candidates expect it to run anywhere.
MySQL has a specific restriction: in an UPDATE or DELETE, a subquery can't read from the table being modified, unless
that subquery is first materialized as a derived table.
""",
r"""
MySQL rejects the statement with ERROR 1093, because the DELETE's subquery selects from `users`, the very table being
modified. (In SQLite the same statement deletes the duplicates correctly.) MySQL-friendly fixes:

- a multi-table DELETE with a self-join, `DELETE u1 FROM users u1 JOIN users u2 ON u1.email = u2.email AND u1.id > u2.id`,
  which deletes every row that has a twin with a smaller id;
- wrapping the subquery in a derived table, which MySQL materializes first;
- in MySQL 8, numbering rows with `ROW_NUMBER() OVER (PARTITION BY email ORDER BY id)` inside a derived table and
  deleting those with `rn > 1`.

NULL emails behave differently by method: the self-join never matches NULLs (so they're all kept), while GROUP BY puts
all NULLs in one group (so all but one are deleted). On a big table, delete in batches, then add a UNIQUE constraint so
duplicates can't come back.
""",
r"""
```sql
-- MySQL: self-join delete (keeps the lowest id per email)
DELETE u1
FROM users u1
JOIN users u2
  ON u1.email = u2.email
 AND u1.id > u2.id;

-- MySQL 8: window function inside a derived table (materialized, so no ERROR 1093)
DELETE FROM users
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
        FROM users
    ) t
    WHERE rn > 1
);

-- make sure it can't happen again
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);
```
""",
"Name ERROR 1093 and finish with the UNIQUE constraint. Fixing the data without preventing recurrence is only half an answer."),

T("trap-sql-repeatable-read-lost-update", A, "MySQL REPEATABLE READ: snapshot reads vs UPDATE", "Advanced", "Common",
r"""
MySQL 8 with InnoDB at the default isolation level. Account 1 starts with a balance of 100. What do (a) and (b) show?

```sql
-- Session T1                                       -- Session T2
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1;  -- 100
                                                    UPDATE accounts SET balance = 50 WHERE id = 1;
                                                    COMMIT;
SELECT balance FROM accounts WHERE id = 1;  -- (a) ?
UPDATE accounts SET balance = balance - 10 WHERE id = 1;
SELECT balance FROM accounts WHERE id = 1;  -- (b) ?
COMMIT;
```
""",
["(a) 50, (b) 40", "(a) 100, (b) 90", "(a) 100, (b) 40",
 "(a) 100, and then the UPDATE fails with a serialization error"], 2,
"(a) 100 and (b) 90: under REPEATABLE READ, T1 keeps working on its snapshot, so T2's change stays invisible.",
r"""
Candidates learn 'REPEATABLE READ means I keep seeing my snapshot' and apply it to everything. In InnoDB the snapshot
applies only to plain (consistent) SELECTs. UPDATE, DELETE and locking reads (`FOR UPDATE`) always read the latest
committed row version. Many also don't know that MySQL defaults to REPEATABLE READ, while PostgreSQL, Oracle and SQL
Server default to READ COMMITTED.
""",
r"""
InnoDB's default isolation level is REPEATABLE READ. T1's first plain SELECT creates a read view (a snapshot), so (a)
still shows 100 even though T2 has committed 50. But the UPDATE is a *current read*: it locks and reads the latest
committed version (50) and writes 40. T1 then sees its own change, so (b) shows 40, not the 90 the snapshot suggests.

That's why lost updates still happen at REPEATABLE READ in MySQL. If the application reads 100 with a plain SELECT,
computes 90 in Java and runs `SET balance = 90`, T2's update is silently overwritten. (PostgreSQL at REPEATABLE READ
would instead abort T1's UPDATE with a serialization error.) Prevent it with an atomic, guarded relative update
(`SET balance = balance - 10 WHERE id = 1 AND balance >= 10`, then check the affected row count), with
`SELECT ... FOR UPDATE` before computing, or with optimistic locking on a version column.
""",
r"""
```sql
-- atomic, guarded update: no read-modify-write in application code
UPDATE accounts
SET balance = balance - 10
WHERE id = 1 AND balance >= 10;         -- 0 rows affected means insufficient funds

-- or lock the row before computing in Java
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;   -- current read + exclusive row lock
UPDATE accounts SET balance = ? WHERE id = 1;
COMMIT;
```
""",
"Say 'plain SELECTs read the snapshot; DML and FOR UPDATE do current reads', then show the guarded UPDATE. It ties isolation theory to the double-spend problems product companies care about."),

T("trap-sql-between-datetime-end-of-day", A, "BETWEEN on DATETIME misses the last day", "Basic", "Common",
r"""
`orders.created_at` is a DATETIME column containing '2024-01-01 10:00:00', '2024-01-15 09:30:00',
'2024-01-31 18:45:00' and '2024-02-01 00:00:00'. The goal is January's orders. What does this return?

```sql
SELECT COUNT(*)
FROM orders
WHERE created_at BETWEEN '2024-01-01' AND '2024-01-31';
```
""",
["3", "2", "4", "1"], 1,
"3: every order placed in January.",
r"""
People read the dates as whole days. But compared with a DATETIME column, '2024-01-31' becomes '2024-01-31 00:00:00',
the very first instant of the 31st. BETWEEN is inclusive at both ends, but of instants, not days, so almost the whole
last day falls outside the range.
""",
r"""
MySQL converts the string bounds to DATETIME, so the range is 2024-01-01 00:00:00 to 2024-01-31 00:00:00 inclusive.
The 18:45 order on 31 January is after the upper bound, so only 2 rows match.

The tempting fix, `BETWEEN '2024-01-01' AND '2024-01-31 23:59:59'`, still misses rows with fractional seconds
(`DATETIME(3)`/`DATETIME(6)`, e.g. 23:59:59.500), and it doesn't generalise across months. Use a half-open range,
`>= start AND < next_start`. It's correct at any precision, works across month and year boundaries, and is sargable,
so the index on `created_at` gets used. By contrast, `DATE(created_at) BETWEEN ...` is correct but can't seek. Watch
time zones too: store UTC (or know what the column holds), and convert the boundaries, not the column.
""",
r"""
```sql
SELECT COUNT(*)
FROM orders
WHERE created_at >= '2024-01-01'
  AND created_at <  '2024-02-01';      -- half-open: correct at any precision, index-friendly
```
""",
"Say 'half-open interval' and mention fractional seconds. It shows you've been bitten by the 23:59:59 'fix' before."),
]
