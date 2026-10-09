from cb_common import B, I, A

# Tables assumed in query questions are stated in each question.
QA = [
# ---------------- Query-writing questions ----------------
("Write a query to find the second highest salary from the Employee table. Return NULL if it doesn't exist.", r'''
```sql
-- Approach 1: subquery (works everywhere)
SELECT MAX(salary) AS second_highest
FROM employee
WHERE salary < (SELECT MAX(salary) FROM employee);

-- Approach 2: LIMIT/OFFSET wrapped so an empty result becomes NULL
SELECT (SELECT DISTINCT salary FROM employee
        ORDER BY salary DESC LIMIT 1 OFFSET 1) AS second_highest;

-- Approach 3: window function
SELECT MAX(salary) AS second_highest FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk FROM employee
) t WHERE rnk = 2;
```
`DISTINCT`/`DENSE_RANK` handles duplicate top salaries (100, 100, 90 -> 90). Wrapping in an outer SELECT or MAX returns NULL instead of an empty set.
''', B, ["sql-query", "ranking"], True),

("Write a query to find the Nth highest salary.", r'''
```sql
-- Window function (MySQL 8+)
SELECT DISTINCT salary FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk FROM employee
) t WHERE rnk = 3;                      -- N = 3

-- LIMIT/OFFSET (N-1)
SELECT DISTINCT salary FROM employee ORDER BY salary DESC LIMIT 1 OFFSET 2;

-- Correlated subquery (no window functions): N-1 distinct salaries are greater
SELECT DISTINCT e1.salary FROM employee e1
WHERE 2 = (SELECT COUNT(DISTINCT e2.salary) FROM employee e2 WHERE e2.salary > e1.salary);
```
As a MySQL function (LeetCode 177 style), you can't use an expression in LIMIT directly, so `SET N = N - 1;` first, then `LIMIT 1 OFFSET N`. Mention DENSE_RANK vs RANK difference for ties.
''', I, ["sql-query", "ranking"], True),

("Find employees who earn more than their managers. Table: Employee(id, name, salary, manager_id).", r'''
Self-join the table — one alias for the employee, one for the manager:
```sql
SELECT e.name AS employee
FROM employee e
JOIN employee m ON e.manager_id = m.id
WHERE e.salary > m.salary;
```
The INNER JOIN automatically excludes employees with no manager. Follow-ups: show the manager name too (`m.name AS manager`), or count employees per manager (`GROUP BY m.id, m.name`).
''', B, ["sql-query", "self-join"], True),

("Find duplicate emails in a Person(id, email) table, and then delete duplicates keeping the row with the smallest id.", r'''
Find duplicates:
```sql
SELECT email, COUNT(*) AS cnt
FROM person
GROUP BY email
HAVING COUNT(*) > 1;
```
Delete duplicates keeping the lowest id:
```sql
-- MySQL multi-table DELETE with self-join
DELETE p1 FROM person p1
JOIN person p2 ON p1.email = p2.email AND p1.id > p2.id;

-- Window function version
DELETE FROM person WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn FROM person
  ) t WHERE rn > 1
);
```
The extra derived table is needed because MySQL doesn't allow selecting from the table being deleted in a direct subquery (error 1093). Afterwards, add `UNIQUE(email)` to prevent recurrence.
''', I, ["sql-query", "duplicates"], True),

("Find customers who never placed an order. Tables: Customers(id, name), Orders(id, customer_id).", r'''
```sql
-- LEFT JOIN anti-join
SELECT c.name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.id IS NULL;

-- NOT EXISTS (NULL-safe, usually same plan)
SELECT c.name FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);

-- NOT IN: dangerous if orders.customer_id can be NULL (returns nothing)
SELECT name FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders WHERE customer_id IS NOT NULL);
```
Make sure `orders.customer_id` is indexed.
''', B, ["sql-query", "joins"], True),

("Find the top 3 highest-paid employees in each department. Tables: Employee(id, name, salary, dept_id), Department(id, name).", r'''
```sql
WITH ranked AS (
  SELECT d.name AS department, e.name AS employee, e.salary,
         DENSE_RANK() OVER (PARTITION BY e.dept_id ORDER BY e.salary DESC) AS rnk
  FROM employee e
  JOIN department d ON d.id = e.dept_id
)
SELECT department, employee, salary
FROM ranked
WHERE rnk <= 3
ORDER BY department, salary DESC;
```
`DENSE_RANK` returns everyone within the top 3 *distinct* salaries (ties included); use `ROW_NUMBER` for exactly 3 rows per department. Without window functions:
```sql
SELECT d.name, e.name, e.salary FROM employee e JOIN department d ON d.id = e.dept_id
WHERE (SELECT COUNT(DISTINCT e2.salary) FROM employee e2
       WHERE e2.dept_id = e.dept_id AND e2.salary > e.salary) < 3;
```
''', I, ["sql-query", "window-functions"], True),

("Find the highest-paid employee(s) in each department.", r'''
```sql
-- Window function
SELECT department, employee, salary FROM (
  SELECT d.name AS department, e.name AS employee, e.salary,
         RANK() OVER (PARTITION BY e.dept_id ORDER BY e.salary DESC) AS rnk
  FROM employee e JOIN department d ON d.id = e.dept_id
) t WHERE rnk = 1;

-- Classic: join with grouped max (handles ties)
SELECT d.name AS department, e.name AS employee, e.salary
FROM employee e
JOIN department d ON d.id = e.dept_id
WHERE (e.dept_id, e.salary) IN (
  SELECT dept_id, MAX(salary) FROM employee GROUP BY dept_id
);
```
Both return multiple employees if they tie for the max. A common mistake is `SELECT dept_id, name, MAX(salary) ... GROUP BY dept_id` — `name` isn't grouped, so it's invalid under ONLY_FULL_GROUP_BY (or returns an arbitrary name).
''', B, ["sql-query", "group-by"], True),

("Find numbers that appear at least three times consecutively. Table: Logs(id, num), id is sequential.", r'''
```sql
-- Self-join on consecutive ids
SELECT DISTINCT l1.num AS consecutive_nums
FROM logs l1
JOIN logs l2 ON l2.id = l1.id + 1 AND l2.num = l1.num
JOIN logs l3 ON l3.id = l1.id + 2 AND l3.num = l1.num;

-- LEAD (doesn't assume ids have no gaps)
SELECT DISTINCT num AS consecutive_nums FROM (
  SELECT num,
         LEAD(num, 1) OVER (ORDER BY id) AS n1,
         LEAD(num, 2) OVER (ORDER BY id) AS n2
  FROM logs
) t WHERE num = n1 AND num = n2;
```
For "at least K times", use the gaps-and-islands trick: `ROW_NUMBER() OVER (ORDER BY id) - ROW_NUMBER() OVER (PARTITION BY num ORDER BY id)` is constant within a run; group by `num, grp` and keep `HAVING COUNT(*) >= K`.
''', I, ["sql-query", "window-functions"], True),

("Calculate a running total of sales by date, and a running total per customer. Table: Orders(id, customer_id, order_date, amount).", r'''
```sql
-- Daily totals then running total
SELECT order_date, daily_total,
       SUM(daily_total) OVER (ORDER BY order_date) AS running_total
FROM (SELECT order_date, SUM(amount) AS daily_total FROM orders GROUP BY order_date) d;

-- Running total per customer, row by row
SELECT customer_id, order_date, amount,
       SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date, id
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cust_running_total
FROM orders;
```
Use `ROWS` (or a unique tiebreaker like `id`) when multiple orders share a date; the default `RANGE` frame would add all same-date rows together. Pre-MySQL 8 alternative: a correlated subquery `SELECT SUM(amount) FROM orders o2 WHERE o2.order_date <= o1.order_date` (O(n^2)).
''', I, ["sql-query", "window-functions"], True),

("Pivot rows into columns: from Sales(product, quarter, amount) produce one row per product with Q1..Q4 columns.", r'''
MySQL has no PIVOT keyword; use conditional aggregation:
```sql
SELECT product,
       SUM(CASE WHEN quarter = 'Q1' THEN amount ELSE 0 END) AS q1,
       SUM(CASE WHEN quarter = 'Q2' THEN amount ELSE 0 END) AS q2,
       SUM(CASE WHEN quarter = 'Q3' THEN amount ELSE 0 END) AS q3,
       SUM(CASE WHEN quarter = 'Q4' THEN amount ELSE 0 END) AS q4,
       SUM(amount) AS total
FROM sales
GROUP BY product;
```
In MySQL, `SUM(quarter = 'Q1') ` counts matches because booleans are 0/1. For an unknown set of columns you'd need dynamic SQL (build the query string with `GROUP_CONCAT` and `PREPARE`). Unpivot (columns -> rows) is done with `UNION ALL` of each column.
''', I, ["sql-query", "pivot"], True),

("Find departments with more than 5 employees, and departments whose average salary is above the company average.", r'''
```sql
-- More than 5 employees
SELECT d.name, COUNT(*) AS headcount
FROM employee e JOIN department d ON d.id = e.dept_id
GROUP BY d.id, d.name
HAVING COUNT(*) > 5;

-- Avg salary above company average
SELECT d.name, AVG(e.salary) AS avg_sal
FROM employee e JOIN department d ON d.id = e.dept_id
GROUP BY d.id, d.name
HAVING AVG(e.salary) > (SELECT AVG(salary) FROM employee);
```
Key concept: aggregate conditions go in HAVING, not WHERE.
''', B, ["sql-query", "group-by"], True),

("Find employees earning more than the average salary of their own department.", r'''
```sql
-- Correlated subquery
SELECT e.name, e.salary, e.dept_id
FROM employee e
WHERE e.salary > (SELECT AVG(x.salary) FROM employee x WHERE x.dept_id = e.dept_id);

-- Window function (single pass)
SELECT name, salary, dept_id, dept_avg FROM (
  SELECT e.*, AVG(salary) OVER (PARTITION BY dept_id) AS dept_avg FROM employee e
) t WHERE salary > dept_avg;

-- Join with derived table
SELECT e.name, e.salary FROM employee e
JOIN (SELECT dept_id, AVG(salary) avg_sal FROM employee GROUP BY dept_id) a
  ON a.dept_id = e.dept_id
WHERE e.salary > a.avg_sal;
```
The window version scans the table once and also lets you display the average.
''', I, ["sql-query", "subquery"], True),

("Find the cumulative/month-over-month revenue growth percentage. Table: Orders(order_date, amount).", r'''
```sql
WITH monthly AS (
  SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, SUM(amount) AS revenue
  FROM orders
  GROUP BY DATE_FORMAT(order_date, '%Y-%m')
)
SELECT month, revenue,
       LAG(revenue) OVER (ORDER BY month) AS prev_revenue,
       ROUND(100 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 2) AS growth_pct
FROM monthly
ORDER BY month;
```
The first month has NULL growth. Use `NULLIF(prev, 0)` in the denominator to avoid division by zero. Filtering on `order_date` with a range (not `DATE_FORMAT` in WHERE) keeps the index usable.
''', I, ["sql-query", "window-functions"], True),

("Find users who logged in on at least 3 consecutive days. Table: Logins(user_id, login_date).", r'''
Gaps-and-islands: subtracting a per-user row number from the date gives a constant value for each consecutive streak.
```sql
WITH d AS (
  SELECT DISTINCT user_id, login_date FROM logins
),
g AS (
  SELECT user_id, login_date,
         DATE_SUB(login_date,
                  INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) DAY) AS grp
  FROM d
)
SELECT user_id, MIN(login_date) AS streak_start, MAX(login_date) AS streak_end, COUNT(*) AS days
FROM g
GROUP BY user_id, grp
HAVING COUNT(*) >= 3;
```
`DISTINCT` first so multiple logins on the same day don't break the streak. Alternative: `LEAD(login_date, 2)` and check it equals `login_date + INTERVAL 2 DAY`.
''', A, ["sql-query", "window-functions"], True),

("Get the latest order for each customer. Table: Orders(id, customer_id, order_date, amount).", r'''
```sql
-- ROW_NUMBER (exactly one per customer)
SELECT id, customer_id, order_date, amount FROM (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, id DESC) AS rn
  FROM orders o
) t WHERE rn = 1;

-- Join with grouped max (may return ties)
SELECT o.* FROM orders o
JOIN (SELECT customer_id, MAX(order_date) AS max_dt FROM orders GROUP BY customer_id) m
  ON m.customer_id = o.customer_id AND m.max_dt = o.order_date;

-- NOT EXISTS: no newer order exists
SELECT o.* FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM orders o2
                  WHERE o2.customer_id = o.customer_id AND o2.order_date > o.order_date);
```
An index on `(customer_id, order_date)` makes all three fast. This "greatest-n-per-group" pattern is extremely common.
''', I, ["sql-query", "window-functions"], True),

("Write a query to find the department-wise count of employees including departments with zero employees.", r'''
```sql
SELECT d.name AS department, COUNT(e.id) AS employee_count
FROM department d
LEFT JOIN employee e ON e.dept_id = d.id
GROUP BY d.id, d.name
ORDER BY employee_count DESC;
```
Two traps:
1. Start from `department` with a LEFT JOIN so empty departments appear.
2. Use `COUNT(e.id)`, not `COUNT(*)` — `COUNT(*)` would count the NULL-extended row and report 1 for empty departments.
''', B, ["sql-query", "joins"], True),

("Find the employees who joined in the last 6 months, and the number of hires per year.", r'''
```sql
SELECT id, name, hired_on
FROM employee
WHERE hired_on >= CURDATE() - INTERVAL 6 MONTH;

SELECT YEAR(hired_on) AS yr, COUNT(*) AS hires
FROM employee
GROUP BY YEAR(hired_on)
ORDER BY yr;
```
For the first query keep the column bare (no function around `hired_on`) so an index on it can be used. Functions in SELECT/GROUP BY are fine. To show years with zero hires you'd join to a generated year list (recursive CTE).
''', B, ["sql-query", "dates"], False),

("Swap the gender values 'M' and 'F' in a Salary table with a single UPDATE and no temp table.", r'''
```sql
UPDATE salary
SET sex = CASE sex WHEN 'm' THEN 'f' WHEN 'f' THEN 'm' ELSE sex END;

-- MySQL alternative
UPDATE salary SET sex = IF(sex = 'm', 'f', 'm');
```
`CASE` in UPDATE is the standard way to apply different changes to different rows in one statement. The same idea applies to conditional raises: `SET salary = CASE WHEN dept_id = 1 THEN salary * 1.1 ELSE salary * 1.05 END`.
''', B, ["sql-query", "update"], False),

("Find the median salary (or median per department) in MySQL.", r'''
MySQL has no MEDIAN function; use window functions:
```sql
SELECT dept_id, AVG(salary) AS median_salary
FROM (
  SELECT dept_id, salary,
         ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary) AS rn,
         COUNT(*)     OVER (PARTITION BY dept_id)                  AS cnt
  FROM employee
) t
WHERE rn IN (FLOOR((cnt + 1) / 2), CEIL((cnt + 1) / 2))
GROUP BY dept_id;
```
For odd counts both expressions point to the middle row; for even counts they pick the two middle rows and `AVG` averages them. Drop `PARTITION BY` for the company-wide median.
''', A, ["sql-query", "window-functions"], False),

("Report each product's sales ratio as a percentage of total sales, and the top 20% products by revenue.", r'''
```sql
-- Percentage of total
SELECT product_id, SUM(amount) AS revenue,
       ROUND(100 * SUM(amount) / SUM(SUM(amount)) OVER (), 2) AS pct_of_total
FROM order_item
GROUP BY product_id
ORDER BY revenue DESC;

-- Top 20% products by revenue (quintiles)
SELECT product_id, revenue FROM (
  SELECT product_id, SUM(amount) AS revenue,
         NTILE(5) OVER (ORDER BY SUM(amount) DESC) AS bucket
  FROM order_item GROUP BY product_id
) t WHERE bucket = 1;
```
`SUM(SUM(amount)) OVER ()` nests an aggregate inside a window function: the inner SUM is per group, the outer window sums across all groups. Window functions run after GROUP BY, which makes this possible.
''', A, ["sql-query", "window-functions"], False),

("Find pairs of employees in the same department with the same salary, and classify each employee's salary band.", r'''
```sql
-- Pairs (each pair once)
SELECT e1.name AS emp1, e2.name AS emp2, e1.dept_id, e1.salary
FROM employee e1
JOIN employee e2
  ON e1.dept_id = e2.dept_id AND e1.salary = e2.salary AND e1.id < e2.id;

-- Salary band with CASE
SELECT name, salary,
       CASE WHEN salary >= 150000 THEN 'A'
            WHEN salary >= 80000  THEN 'B'
            ELSE 'C' END AS band
FROM employee;
```
`e1.id < e2.id` avoids self-pairs and duplicate (A,B)/(B,A) pairs — a frequently tested detail.
''', B, ["sql-query", "self-join"], False),

# ---------------- Concept questions ----------------
("What is the logical order of execution of a SQL SELECT query?", r'''
1. `FROM` and `JOIN`s (build the working set)
2. `WHERE` (filter rows)
3. `GROUP BY` (form groups)
4. `HAVING` (filter groups)
5. `SELECT` (compute expressions, window functions)
6. `DISTINCT`
7. `ORDER BY`
8. `LIMIT` / `OFFSET`

Consequences: you can't use a SELECT alias or window function in WHERE; you can use aggregates in HAVING but not WHERE; ORDER BY can use aliases. To filter on a window function's result, wrap the query in a subquery or CTE. The optimizer may physically execute in a different order, but results must match this logical order.
''', B, ["sql-basics"], True),

("Explain the different types of joins with examples.", r'''
- **INNER JOIN**: rows with matches in both tables. `employees JOIN departments ON e.dept_id = d.id`.
- **LEFT (OUTER) JOIN**: all rows from the left + matches from the right (NULLs where none). Used for "including those without" and anti-joins (`WHERE right.id IS NULL`).
- **RIGHT JOIN**: mirror of LEFT.
- **FULL OUTER JOIN**: all rows from both; MySQL doesn't support it — emulate with `LEFT JOIN UNION RIGHT JOIN`.
- **CROSS JOIN**: Cartesian product (every combination) — e.g. generating size x colour variants.
- **SELF JOIN**: a table joined to itself with aliases — employee/manager, comparing rows.
- **Semi-join**: `EXISTS`/`IN` — rows that have a match, without duplicating.

Placing a right-table filter in WHERE turns a LEFT JOIN into an INNER JOIN; keep it in ON to preserve unmatched rows.
''', B, ["joins"], True),

("WHERE vs HAVING?", r'''
- `WHERE` filters **rows before grouping**; it can't use aggregate functions.
- `HAVING` filters **groups after GROUP BY**; it can use aggregates.
```sql
SELECT dept_id, AVG(salary) FROM employee
WHERE status = 'ACTIVE'          -- row filter
GROUP BY dept_id
HAVING AVG(salary) > 60000;      -- group filter
```
Put conditions that don't need aggregates in WHERE — fewer rows reach the grouping step and indexes can be used. HAVING without GROUP BY treats the whole result as one group.
''', B, ["sql-basics", "group-by"], True),

("DELETE vs TRUNCATE vs DROP?", r'''
| | DELETE | TRUNCATE | DROP |
|---|---|---|---|
| Type | DML | DDL | DDL |
| Removes | Selected rows (WHERE) or all | All rows | Whole table (data + structure + indexes) |
| Rollback | Yes (in a transaction) | No in MySQL (implicit commit) | No |
| Triggers | Fires DELETE triggers | No | No |
| Speed | Slow for big tables (row-by-row, undo logging) | Fast (drops & recreates) | Fast |
| AUTO_INCREMENT | Not reset | Reset | Gone |
| FK-referenced table | Allowed per constraints | Fails if referenced by FKs | Fails if referenced |

For deleting millions of rows in production, delete in batches (`LIMIT 5000` loops) to avoid long locks and replication lag, or drop partitions.
''', B, ["sql-basics"], True),

("UNION vs UNION ALL? IN vs EXISTS?", r'''
- `UNION` combines result sets and **removes duplicates** (needs a sort/hash -> slower).
- `UNION ALL` keeps duplicates and is faster. Use it when duplicates are impossible or wanted.

- `IN (subquery)` checks membership in a list of values.
- `EXISTS (subquery)` checks whether the correlated subquery returns any row; stops at the first match.
MySQL 8 converts both into semi-joins in most cases, so performance is usually similar — verify with EXPLAIN. The important difference is **NOT IN vs NOT EXISTS**: if the subquery returns a NULL, `NOT IN` yields no rows (comparison with NULL is unknown), while `NOT EXISTS` behaves intuitively. Prefer `NOT EXISTS` or a LEFT JOIN anti-join.
''', I, ["sql-basics", "subquery"], True),

("What is a CTE? How is it different from a subquery, a temporary table, and a view?", r'''
A **Common Table Expression** (`WITH name AS (...)`) is a named, temporary result set for a single statement (MySQL 8+).
- vs **subquery**: same power for most uses, but CTEs are more readable, can be referenced multiple times, and can be **recursive** (hierarchies, date series).
- vs **temporary table**: a temp table (`CREATE TEMPORARY TABLE`) is physically created, persists for the session, can be indexed and reused across statements; a CTE exists only during one query.
- vs **view**: a view is a stored schema object reusable by any query and grantable for security; a CTE isn't stored.

```sql
WITH RECURSIVE sub AS (
  SELECT id, manager_id FROM employee WHERE id = 10
  UNION ALL
  SELECT e.id, e.manager_id FROM employee e JOIN sub s ON e.manager_id = s.id
) SELECT * FROM sub;    -- all reports under employee 10
```
''', I, ["cte"], True),

("What are window functions? Explain ROW_NUMBER, RANK and DENSE_RANK.", r'''
Window functions calculate a value per row over a set of related rows (`OVER (PARTITION BY ... ORDER BY ...)`) without collapsing rows like GROUP BY.

For salaries 100, 90, 90, 80:
- **ROW_NUMBER**: 1, 2, 3, 4 — unique numbering; use for dedup or "exactly one per group".
- **RANK**: 1, 2, 2, 4 — ties share a rank, then a gap.
- **DENSE_RANK**: 1, 2, 2, 3 — ties share a rank, no gaps; use for "Nth highest distinct salary".

```sql
SELECT name, dept_id, salary,
       DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rnk
FROM employee;
```
Others: `LAG/LEAD` (previous/next row), `SUM/AVG OVER` (running totals, per-group averages), `NTILE`, `FIRST_VALUE`. They can't appear in WHERE — filter in an outer query.
''', I, ["window-functions"], True),

("What is an index? How does a B+Tree index work in MySQL?", r'''
An index is a sorted data structure that lets MySQL locate rows without a full table scan.

InnoDB uses **B+Trees**: a balanced tree where internal nodes contain keys to guide the search, and **leaf nodes contain the actual entries, linked together** in order. With 16KB pages holding hundreds of keys, a tree of 3-4 levels covers hundreds of millions of rows, so a lookup reads only a few pages — O(log n). Linked leaves make **range queries** (`BETWEEN`, `>`, `ORDER BY`) efficient by scanning sideways.

Why not hash? Hash indexes only support equality, not ranges or sorting. Why not binary trees? Too deep -> too many disk reads.

Cost: indexes consume space and slow down INSERT/UPDATE/DELETE because each index must be maintained.
''', I, ["indexes"], True),

("Clustered vs non-clustered (secondary) index in InnoDB?", r'''
- **Clustered index**: in InnoDB, the **primary key index stores the full rows** in its leaf pages, physically ordered by PK. There's exactly one per table (if no PK, InnoDB uses the first NOT NULL UNIQUE key or a hidden row id).
- **Secondary index**: leaf entries hold the indexed columns **plus the primary key**. A lookup finds the PK and then searches the clustered index for the rest of the row (double lookup), unless the index covers the query.

Implications:
- Keep the PK short (BIGINT) — it's duplicated in every secondary index.
- Monotonically increasing PKs (AUTO_INCREMENT, UUIDv7) insert at the end; random UUIDv4 PKs cause page splits and fragmentation.
- PK range queries are very fast (rows are contiguous).
''', I, ["indexes"], True),

("What is a composite index and the leftmost prefix rule? How do you choose column order?", r'''
A composite index covers multiple columns, sorted by the first column, then the second within it, etc. — like a phone book sorted by (last_name, first_name).

**Leftmost prefix rule**: the index on `(a, b, c)` can be used for conditions on `a`, `a,b`, or `a,b,c` — but not for `b` or `c` alone. After a **range** condition on a column, the following columns can't be used for seeking (they can still filter via index condition pushdown).
```sql
INDEX(customer_id, status, created_at)
WHERE customer_id = 7 AND status = 'PAID' ORDER BY created_at DESC   -- fully used, no filesort
WHERE status = 'PAID'                                               -- can't seek
```
Order columns by: equality filters first, then the range or sort column; among equality columns, those used most often/most selective first. An index on `(a,b)` makes a separate `(a)` index redundant.
''', I, ["indexes"], True),

("What is a covering index?", r'''
An index that contains **all the columns a query needs** (in SELECT, WHERE, ORDER BY, GROUP BY), so MySQL can answer the query from the index alone without reading table rows (no lookup into the clustered index). EXPLAIN shows `Using index` in Extra.
```sql
CREATE INDEX idx_status_created_total ON orders (status, created_at, total);
SELECT created_at, total FROM orders WHERE status = 'PAID' ORDER BY created_at DESC LIMIT 50;
```
In InnoDB, secondary indexes implicitly include the primary key, so `SELECT id ...` is also covered. Covering indexes are great for hot read queries, but wide indexes cost storage and write speed — and `SELECT *` defeats them.
''', I, ["indexes", "performance"], True),

("When does MySQL not use an index even if one exists?", r'''
- **Function/expression on the column**: `WHERE DATE(created_at) = '2025-01-01'`, `WHERE salary * 1.1 > 50000`. Rewrite as ranges or use a functional index.
- **Leading wildcard**: `LIKE '%son'` (prefix `LIKE 'son%'` is fine).
- **Implicit type conversion**: comparing a VARCHAR column to a number, or joining columns with different charsets/collations.
- **Leftmost prefix not used** in a composite index.
- **Low selectivity**: if the optimizer estimates many rows match (e.g. `status = 'ACTIVE'` for 90% of rows), a full scan is cheaper.
- **OR across different columns** (may need index merge or UNION).
- `!=`, `NOT IN`, `IS NOT NULL` on mostly-non-null columns often scan.
- **Outdated statistics** — run `ANALYZE TABLE`.
- Small tables where a scan is cheaper.
Confirm with EXPLAIN and check the `key` column.
''', I, ["indexes", "performance"], True),

("How do you read EXPLAIN output? What are the important columns?", r'''
- **type**: access method, from best to worst — `const` (single row by PK/unique), `eq_ref` (one row per join row via unique index), `ref` (non-unique index lookup), `range` (index range scan), `index` (full index scan), `ALL` (full table scan — red flag on large tables).
- **possible_keys / key**: indexes considered vs the one chosen.
- **key_len**: how much of a composite index is used.
- **rows**: estimated rows examined; **filtered**: % remaining after conditions.
- **Extra**: `Using index` (covering — good), `Using where`, `Using index condition` (ICP), `Using filesort` (extra sort step), `Using temporary` (temp table for GROUP BY/DISTINCT), `Using join buffer` (join without index).

Use `EXPLAIN ANALYZE` in MySQL 8 to see actual times and row counts versus estimates.
''', I, ["explain", "performance"], True),

("A query is slow in production. How do you troubleshoot and optimise it?", r'''
1. **Identify**: slow query log, APM traces, `performance_schema`/`sys` schema; get the exact query and parameters; check frequency vs duration.
2. **EXPLAIN / EXPLAIN ANALYZE**: look for full scans (`ALL`), large `rows`, `Using filesort`/`temporary`, wrong index choice.
3. **Indexing**: add a composite index matching WHERE equality columns then ORDER BY/range; make it covering for hot queries; index join/FK columns.
4. **Rewrite**: sargable predicates (no functions on indexed columns), avoid `SELECT *`, replace correlated subqueries with joins/window functions, `OR` -> `UNION ALL`, keyset pagination instead of large OFFSET.
5. **Reduce work**: fetch less data, pre-aggregate into summary tables, cache in Redis.
6. **Check the environment**: lock waits (`data_lock_waits`), buffer pool hit rate, stale stats (`ANALYZE TABLE`), connection pool saturation, N+1 from the ORM.
7. **Verify**: compare EXPLAIN and latency before/after on production-like data, then monitor.
''', I, ["performance", "scenario"], True),

("Why is OFFSET pagination slow for large offsets? What's the alternative?", r'''
`SELECT ... ORDER BY id LIMIT 20 OFFSET 1000000` makes MySQL read and discard 1,000,000 rows before returning 20 — cost grows linearly with the page number. Results can also shift if rows are inserted/deleted between page requests.

**Keyset (seek/cursor) pagination**: remember the last seen sort key and continue from it, using the index directly:
```sql
SELECT id, title, created_at FROM posts
WHERE (created_at, id) < (:last_created_at, :last_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```
Needs an index on `(created_at, id)`. Constant time per page and stable results; downside: no "jump to page 500", only next/previous. Another option is a **deferred join**: get the 20 ids with OFFSET from a covering index, then join back for full rows.
''', I, ["performance", "pagination"], True),

("Explain normalization: 1NF, 2NF, 3NF and BCNF with examples.", r'''
- **1NF**: atomic column values, no repeating groups, a primary key. Bad: `phones = '98..,97..'`; fix with a separate phone table.
- **2NF**: 1NF + no partial dependency on part of a composite key. In `order_item(order_id, product_id, qty, product_name)`, `product_name` depends only on `product_id` -> move to `product`.
- **3NF**: 2NF + no transitive dependency (non-key -> non-key). In `employee(id, dept_id, dept_name)`, `dept_name` depends on `dept_id` -> move to `department`.
- **BCNF**: every determinant is a candidate key (handles edge cases with overlapping candidate keys).

Goal: eliminate redundancy and update/insert/delete anomalies. Denormalize deliberately for read performance (reporting tables, cached totals), accepting extra write complexity.
''', B, ["normalization", "design"], True),

("What is denormalization and when would you use it?", r'''
Denormalization intentionally introduces redundancy to speed up reads by avoiding joins or aggregations at query time. Examples:
- Storing `order_total` on orders instead of summing order items each time.
- Copying `customer_name` into an orders/invoice table (also preserves historical accuracy).
- Counter columns (`likes_count`) updated on write.
- Summary/reporting tables refreshed by jobs (MySQL has no materialised views).
- Read models in CQRS, or star schemas in data warehouses.

Use it when reads vastly outnumber writes, and joins/aggregations are proven bottlenecks. Costs: more storage, more complex writes, risk of inconsistency — keep the denormalized data in sync with transactions, triggers, or events, and treat the normalized data as the source of truth.
''', I, ["normalization", "design"], False),

("What are ACID properties? How does InnoDB implement them?", r'''
- **Atomicity**: all or nothing. InnoDB records an **undo log** so it can roll back partial changes.
- **Consistency**: transactions take the DB from one valid state to another — enforced by constraints (PK, FK, UNIQUE, CHECK) and application invariants.
- **Isolation**: concurrent transactions don't interfere beyond the chosen isolation level — implemented with **MVCC** (snapshots via undo logs) and **locks** (record, gap, next-key).
- **Durability**: committed data survives crashes — InnoDB writes changes to the **redo log** (write-ahead logging) and flushes it at commit (`innodb_flush_log_at_trx_commit=1`); the doublewrite buffer protects against partial page writes; crash recovery replays the redo log.
''', B, ["transactions", "acid"], True),

("Explain transaction isolation levels and the anomalies each prevents. What is MySQL's default?", r'''
| Level | Dirty read | Non-repeatable read | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | possible | possible | possible |
| READ COMMITTED | no | possible | possible |
| REPEATABLE READ | no | no | possible per SQL standard |
| SERIALIZABLE | no | no | no |

- Dirty read: seeing uncommitted changes.
- Non-repeatable read: re-reading a row gives a different value.
- Phantom: re-running a range query returns new rows.

**MySQL InnoDB default is REPEATABLE READ.** Thanks to MVCC, plain SELECTs read a consistent snapshot (no phantoms), and locking reads use next-key locks to block inserts into scanned ranges. PostgreSQL/Oracle default to READ COMMITTED. Higher levels reduce anomalies but increase locking and deadlocks.
''', I, ["transactions", "isolation"], True),

("What is MVCC and how does InnoDB use it?", r'''
**Multi-Version Concurrency Control** keeps multiple versions of rows so readers don't block writers and writers don't block readers.

In InnoDB, each row stores the id of the last transaction that modified it and a pointer to its previous version in the **undo log**. A consistent read creates a **read view** (which transactions were committed/active at that moment) and follows the undo chain to the version visible to it.
- REPEATABLE READ: the read view is created at the first read and reused for the whole transaction -> stable results.
- READ COMMITTED: a new read view per statement -> sees each newly committed change.

Plain SELECTs take no locks. Writes still lock rows. Long-running transactions keep old versions alive, growing the undo history and slowing the server — keep transactions short.
''', A, ["mvcc", "transactions"], True),

("Explain InnoDB locks: shared vs exclusive, record, gap and next-key locks.", r'''
- **Shared (S)**: `SELECT ... FOR SHARE` — multiple transactions can hold it; blocks writers.
- **Exclusive (X)**: `SELECT ... FOR UPDATE`, UPDATE, DELETE — blocks other S and X locks on the row.
- **Intention locks (IS/IX)**: table-level markers that row locks exist.
- **Record lock**: locks an index entry.
- **Gap lock**: locks the gap between index entries, preventing inserts there (REPEATABLE READ and above).
- **Next-key lock**: record + preceding gap; default for range scans in REPEATABLE READ — prevents phantoms.

Locks are taken on **index records**: an UPDATE whose WHERE clause can't use an index scans and locks every row it examines, effectively locking the table. MySQL 8 adds `NOWAIT` and `SKIP LOCKED` for queue-like workloads. Inspect with `performance_schema.data_locks`.
''', A, ["locking", "innodb"], True),

("What is a deadlock in MySQL? How do you detect and prevent it?", r'''
A deadlock occurs when two transactions each hold locks the other needs (T1 locks row 1 then wants row 2; T2 locks row 2 then wants row 1). InnoDB **detects it automatically** and rolls back one transaction (the victim, usually the one with fewer changes) with error 1213; the other continues.

Diagnose: `SHOW ENGINE INNODB STATUS` (LATEST DETECTED DEADLOCK), `innodb_print_all_deadlocks=ON` to log all, `performance_schema.data_lock_waits`.

Prevent:
- Access rows in a consistent order (sort ids before updating).
- Keep transactions short; no user/remote calls inside.
- Index WHERE columns of UPDATE/DELETE to lock fewer rows/gaps.
- Use READ COMMITTED to reduce gap locks if acceptable.
- Break large batch updates into small chunks.
- **Retry** deadlocked transactions in the application — deadlocks can't be fully eliminated.
''', I, ["locking", "deadlock"], True),

("How do you prevent two users from booking the same seat / overselling inventory?", r'''
Options, from simplest:
1. **Atomic conditional update**:
```sql
UPDATE seat SET status = 'BOOKED', user_id = 42
WHERE id = 101 AND status = 'AVAILABLE';   -- check affected rows: 1 = success, 0 = taken
UPDATE product SET stock = stock - 1 WHERE id = 7 AND stock >= 1;
```
2. **Pessimistic locking**: `SELECT ... FOR UPDATE` inside a transaction, then update; others wait (use `NOWAIT`/`SKIP LOCKED` to avoid waiting).
3. **Optimistic locking**: version column; update `WHERE version = ?`, retry on conflict.
4. **Unique constraint** as a safety net: `UNIQUE(show_id, seat_no)` on a bookings table — a second insert fails.
5. At very high scale, temporary holds with TTL in Redis (atomic `SET NX EX` or Lua), then confirm in the DB.
Avoid read-then-write without locks (`SELECT stock` then `UPDATE stock = :new`) — classic lost update.
''', A, ["locking", "scenario"], True),

("What are views? Can you update through a view?", r'''
A view is a saved SQL query treated like a virtual table; it stores no data (MySQL has no materialised views).
```sql
CREATE VIEW active_customers AS
SELECT id, name, email FROM customer WHERE status = 'ACTIVE';
```
Uses: simplify complex joins, restrict columns/rows for security (grant access to the view only), keep a stable interface while the underlying schema changes.

Updatable views: simple views over a single table without aggregates, DISTINCT, GROUP BY, HAVING, UNION or subqueries in SELECT allow INSERT/UPDATE/DELETE, which pass through to the base table. `WITH CHECK OPTION` rejects changes that would make the row invisible to the view. Performance: views using aggregates are materialised into temp tables (TEMPTABLE), which can be slow when filtered from outside.
''', B, ["views"], False),

("Stored procedure vs function? What are the pros and cons of stored procedures?", r'''
**Procedure**: invoked with `CALL`, can have IN/OUT/INOUT parameters, return multiple result sets, and manage transactions (COMMIT/ROLLBACK). **Function**: returns a single value, usable inside SQL expressions (`SELECT tax(amount)`), can't manage transactions.

Pros of procedures: fewer network round trips for multi-step data logic, logic close to data, permission control via EXECUTE grants, reusable across apps.

Cons: business logic hidden in the DB is harder to version, test (no easy unit tests/mocking), debug and review; scales poorly because DB CPU is hardest to scale; vendor lock-in; deployment coordination with app releases.

Product companies typically keep business logic in services and use procedures for data-heavy batch jobs or migrations. From Spring: `@Procedure` or `SimpleJdbcCall`.
''', B, ["stored-procedures"], False),

("What are triggers? When should you avoid them?", r'''
Triggers are SQL code that runs automatically `BEFORE` or `AFTER` an INSERT, UPDATE or DELETE on a table, for each affected row, with access to `OLD` and `NEW` values.
```sql
CREATE TRIGGER trg_audit AFTER UPDATE ON employee FOR EACH ROW
INSERT INTO employee_audit(emp_id, old_salary, new_salary, changed_at)
VALUES (OLD.id, OLD.salary, NEW.salary, NOW());
```
Uses: audit logs, enforcing invariants, maintaining denormalized columns.

Avoid when: logic is business-critical and should be visible in application code, high write throughput (they add latency to every write), complex chains (triggers firing other triggers), or you need to call external systems. Hidden side effects confuse developers and complicate debugging and migrations. Alternatives: application-level auditing (JPA auditing, Hibernate Envers) or CDC with Debezium.
''', B, ["triggers"], False),

("How does MySQL replication work? What is replication lag and how do you handle it?", r'''
In source-replica replication, the source writes every change to its **binary log**. Each replica's I/O thread pulls binlog events into a **relay log**, and the SQL/applier thread(s) replay them. Replicas typically serve read traffic; writes go to the source. Default replication is **asynchronous**; **semi-synchronous** makes the source wait until at least one replica receives the event; **Group Replication/InnoDB Cluster** adds consensus-based failover. GTIDs simplify failover.

**Replication lag**: replicas fall behind due to heavy writes, long transactions, single-threaded apply, or underpowered replicas. Effects: users don't see their own just-made changes.

Handling: read-your-writes by routing a user's reads to the primary briefly after a write, send critical reads to the primary, enable multi-threaded replication, avoid huge transactions (batch updates), and monitor `Seconds_Behind_Source`.
''', I, ["replication", "scaling"], True),

("Partitioning vs sharding? How would you scale a MySQL database?", r'''
- **Partitioning**: one table split into physical partitions **on the same server** (RANGE by date, LIST, HASH, KEY). Benefits: partition pruning, fast archival via `DROP PARTITION`. The partition key must be in every unique key.
- **Sharding**: data split **across multiple database servers** by a shard key (e.g. `user_id` hash). Scales writes and storage beyond one machine, but cross-shard joins/transactions, global IDs and re-sharding are hard. Tools: Vitess, ShardingSphere, ProxySQL.

Scaling path:
1. Optimise queries/indexes and buffer pool.
2. Cache hot reads (Redis).
3. Vertical scaling.
4. Read replicas for read-heavy load.
5. Partition very large tables; archive cold data.
6. Shard when write throughput or dataset size exceeds a single primary, choosing a shard key that keeps most queries on one shard.
''', A, ["scaling", "partitioning"], True),

("CHAR vs VARCHAR? Why use DECIMAL for money? DATETIME vs TIMESTAMP?", r'''
- **CHAR(n)**: fixed length, space-padded; good for fixed-size codes (country code, hashes). **VARCHAR(n)**: variable length + 1-2 byte length prefix; good for names/emails.
- **DECIMAL(p,s)** stores exact base-10 values. FLOAT/DOUBLE are binary approximations (0.1 + 0.2 != 0.3), causing rounding errors in financial sums. Use `DECIMAL(12,2)` or store the amount in paise as BIGINT. In Java, map to `BigDecimal`.
- **DATETIME**: stores the literal date-time without timezone, range 1000-9999. **TIMESTAMP**: stored as UTC and converted to the session time zone on read, range 1970-2038, 4 bytes. Store times in UTC consistently; many teams use DATETIME holding UTC values to avoid the 2038 limit.
- Use `utf8mb4` charset for full Unicode (emoji).
''', B, ["data-types"], False),

("What is the difference between primary key, unique key and foreign key?", r'''
- **Primary key**: uniquely identifies each row; NOT NULL; only one per table (can be composite). In InnoDB it's the **clustered index** that physically orders rows.
- **Unique key**: enforces uniqueness on column(s); multiple allowed per table; allows NULLs (in MySQL, multiple NULLs are permitted). Creates a secondary unique index. Example: `email`.
- **Foreign key**: a column referencing another table's primary/unique key to enforce referential integrity; options `ON DELETE CASCADE | SET NULL | RESTRICT`. InnoDB requires an index on FK columns (creates one automatically). Some high-scale teams skip DB-level FKs for performance/sharding and enforce integrity in the application, but FKs are the safe default.
''', B, ["sql-basics", "keys"], True),

("What is the N+1 query problem from the database perspective, and how do you spot it in MySQL?", r'''
The application issues one query to fetch a list and then one query per row to fetch related data — e.g. 1 query for 100 orders + 100 queries for their customers. Each query is fast, but 101 round trips add latency and load.

Spotting it: the general/slow query log or `performance_schema.events_statements_summary_by_digest` shows the same query digest executed hundreds of times per request with different ids; APM traces show many tiny DB spans; Hibernate statistics show high statement counts.

Fixes: fetch with a JOIN, use `WHERE customer_id IN (...)` batch queries, JPA `JOIN FETCH`/`@EntityGraph`/batch fetching, or DTO projections that select exactly what the page needs.
''', I, ["performance", "orm"], False),

("How would you design tables for a many-to-many relationship, e.g. students and courses?", r'''
Use a **junction (associative) table** holding foreign keys to both sides:
```sql
CREATE TABLE student (id BIGINT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100));
CREATE TABLE course  (id BIGINT PRIMARY KEY AUTO_INCREMENT, title VARCHAR(100));
CREATE TABLE enrollment (
  student_id BIGINT NOT NULL,
  course_id  BIGINT NOT NULL,
  enrolled_on DATE NOT NULL,
  grade CHAR(2),
  PRIMARY KEY (student_id, course_id),           -- no duplicate enrolments
  KEY idx_course_student (course_id, student_id), -- reverse lookups
  FOREIGN KEY (student_id) REFERENCES student(id),
  FOREIGN KEY (course_id)  REFERENCES course(id)
);
-- students in a course
SELECT s.name FROM enrollment e JOIN student s ON s.id = e.student_id WHERE e.course_id = 5;
```
The junction table can carry relationship attributes (date, grade). In JPA, model it as its own entity rather than `@ManyToMany` when it has extra columns.
''', B, ["design", "normalization"], False),
]
