from fr1_common import M, C, T, build

mcqs = [
M("SQL", '''What is the LOGICAL order in which a SQL engine evaluates these clauses?''',
["SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY", "FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY",
 "FROM, GROUP BY, WHERE, HAVING, SELECT, ORDER BY", "FROM, WHERE, SELECT, GROUP BY, HAVING, ORDER BY"], 1,
'''Logically, rows are gathered (FROM/JOIN), filtered (WHERE), grouped (GROUP BY), groups are filtered (HAVING), expressions are projected (SELECT, DISTINCT), and the result is sorted and limited (ORDER BY, LIMIT). That is why a SELECT alias cannot be used in WHERE but works in ORDER BY.''',
["Walmart", "Oracle", "Amazon"]),

M("SQL", '''Which query is INVALID?''',
["SELECT dept, COUNT(*) FROM emp GROUP BY dept HAVING COUNT(*) > 5",
 "SELECT dept, COUNT(*) FROM emp WHERE COUNT(*) > 5 GROUP BY dept",
 "SELECT dept, AVG(salary) FROM emp WHERE salary > 0 GROUP BY dept",
 "SELECT dept FROM emp GROUP BY dept ORDER BY COUNT(*) DESC"], 1,
'''WHERE filters individual rows before grouping, so aggregate functions are not allowed there. Conditions on aggregates belong in HAVING. Filtering plain rows in WHERE first (such as `salary > 0`) also reduces the rows that need to be grouped, which is good for performance.''',
["Walmart", "Oracle", "Paytm"]),

M("SQL", '''Column `bonus` in a 4-row table has values 100, NULL, 300, NULL. What do `COUNT(*)`, `COUNT(bonus)` and `AVG(bonus)` return?''',
["4, 4, 100", "4, 2, 200", "2, 2, 200", "4, 2, 100"], 1,
'''`COUNT(*)` counts rows, which gives 4. `COUNT(col)` and the other aggregates skip NULLs, so `COUNT(bonus)` = 2 and `AVG(bonus)` = (100 + 300) / 2 = 200, not 400 / 4. Use `AVG(COALESCE(bonus, 0))` if NULL should count as zero.''',
["Oracle", "Walmart", "Goldman Sachs"]),

M("SQL", '''Table A has ids 1, 2, 3. Table B has a_id values 1, 1, 4. How many rows does `SELECT * FROM A LEFT JOIN B ON A.id = B.a_id` return?''',
["3", "4", "5", "6"], 1,
'''id 1 matches two B rows, which gives 2 rows. ids 2 and 3 have no match, so each appears once with NULLs for B's columns. Total = 4. B's row with a_id 4 is dropped because it is on the right side of a LEFT JOIN.''',
["Walmart", "Oracle", "Amazon"]),

M("SQL", '''Salaries are 100, 100, 90 (ordered DESC). What do `ROW_NUMBER()`, `RANK()` and `DENSE_RANK()` give for the row with 90?''',
["3, 3, 3", "3, 2, 2", "3, 3, 2", "2, 3, 2"], 2,
'''ROW_NUMBER is always unique (1, 2, 3). RANK gives ties the same rank and then skips (1, 1, 3). DENSE_RANK gives ties the same rank without gaps (1, 1, 2). Use DENSE_RANK for "Nth highest distinct salary" problems.''',
["Walmart", "Oracle", "Amazon", "PhonePe"]),

M("SQL", '''Which statement about `TRUNCATE` in MySQL is TRUE?''',
["It supports a WHERE clause", "It logs each deleted row and fires DELETE triggers",
 "It removes all rows, resets AUTO_INCREMENT and is DDL that causes an implicit commit", "It removes the table definition"], 2,
'''TRUNCATE effectively drops and recreates the table's data. It is fast, minimally logged, resets the auto-increment counter, does not fire triggers, and cannot be rolled back in MySQL because of the implicit commit. DELETE is DML that supports WHERE and triggers. DROP removes the table itself.''',
["Oracle", "Walmart", "SAP"]),

M("SQL", '''`SELECT * FROM users WHERE phone = NULL;` returns…''',
["All rows where phone is NULL", "No rows, because comparing with NULL yields UNKNOWN", "A syntax error", "All rows"], 1,
'''Any comparison with NULL using =, <> or < evaluates to UNKNOWN, and WHERE keeps only rows that are TRUE. Use `IS NULL` or `IS NOT NULL`. MySQL also offers the null-safe operator `<=>`.''',
["Oracle", "Walmart"]),

M("SQL", '''`orders` has customer_ids 1, 2, 3. `blocked` has customer_ids 2 and NULL. What does this return?
```sql
SELECT customer_id FROM orders
WHERE customer_id NOT IN (SELECT customer_id FROM blocked);
```''', ["1, 3", "1, 2, 3", "No rows", "Only 3"], 2,
'''`x NOT IN (2, NULL)` means `x <> 2 AND x <> NULL`. The second part is UNKNOWN for every row, so no row passes. It is a well-known trap. Use `NOT EXISTS` or a `LEFT JOIN ... WHERE b.id IS NULL`, both of which handle NULLs correctly.''',
["Walmart", "Oracle", "Goldman Sachs"]),

M("SQL indexing", '''A composite index exists on `(city, age, name)`. Which WHERE clause can NOT use this index efficiently for lookup?''',
["WHERE city = 'Pune'", "WHERE city = 'Pune' AND age = 30", "WHERE age = 30 AND name = 'Raj'", "WHERE city = 'Pune' AND age > 25"], 2,
'''B+ tree composite indexes follow the leftmost-prefix rule. Entries are sorted by city first, then age, then name. Without a condition on `city`, the engine cannot seek into the tree. It would have to scan, or use an index skip scan in newer versions. Put the most commonly filtered equality columns first.''',
["Walmart", "Oracle", "Amazon", "Razorpay"]),

M("DBMS", '''Under the ANSI standard, which isolation level prevents dirty reads and non-repeatable reads but may still allow phantom reads?''',
["READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"], 2,
'''REPEATABLE READ guarantees that rows you have read do not change, but new rows matching your predicate (phantoms) may appear. InnoDB's default REPEATABLE READ largely prevents phantoms with MVCC snapshots and next-key locks. READ COMMITTED is the default in Oracle and PostgreSQL.''',
["Oracle", "Goldman Sachs", "Walmart"]),

M("SQL", '''What is the difference between `UNION` and `UNION ALL`?''',
["UNION ALL removes duplicates", "UNION removes duplicates (with an extra sort or hash), while UNION ALL keeps all rows and is faster",
 "They are identical", "UNION requires the same table"], 1,
'''UNION applies DISTINCT to the combined result, which needs a sort or hash step. UNION ALL simply appends the result sets. Prefer UNION ALL when duplicates are impossible or acceptable. Both require the same number of columns with compatible types.''',
["Oracle", "Walmart"]),

M("DBMS", '''Table `Employee(emp_id, dept_id, dept_name)` with key emp_id, where dept_id determines dept_name. Which normal form does it violate?''',
["1NF", "2NF", "3NF", "None"], 2,
'''The key is a single column, so partial dependencies (2NF) cannot occur. But emp_id determines dept_id, which determines dept_name, a transitive dependency of a non-key attribute through another non-key attribute. That violates 3NF. Fix it by moving `(dept_id, dept_name)` into a Department table.''',
["Oracle", "SAP", "Walmart"]),

M("Java collections", '''What are the time complexities of `get(index)` for ArrayList and LinkedList?''',
["O(1) and O(1)", "O(1) and O(n)", "O(n) and O(1)", "O(log n) and O(n)"], 1,
'''ArrayList is backed by an array, so random access is a direct index lookup. LinkedList is doubly linked and must walk from the nearer end, which is O(n). LinkedList also has poor cache locality, so ArrayList is usually faster even for many middle inserts.''',
["Oracle", "Walmart", "SAP"]),

M("Java collections", '''What does this print?
```java
List<Integer> list = new ArrayList<>(List.of(1, 2, 3));
for (Integer x : list) {
    if (x == 2) list.remove(x);
}
System.out.println(list);
```''', ["ConcurrentModificationException", "[1, 3]", "[1, 2, 3]", "[3]"], 1,
'''After removing 2, the size is 2 and the iterator's cursor is also 2, so `hasNext()` returns false and the loop exits before `next()` can check modCount. Removing the second-to-last element avoids the exception by luck. With [1, 2, 3, 4] it would throw. Use `removeIf` or `Iterator.remove()` instead.''',
["Walmart", "Oracle", "Paytm"]),

M("Java collections", '''What happens on `new TreeMap<String, Integer>().put(null, 1)`?''',
["Stores null as the smallest key", "NullPointerException", "Stores it at the end", "Compile error"], 1,
'''TreeMap orders keys with `compareTo` or a Comparator. Natural ordering calls `compareTo` on the key, so a null key throws NullPointerException. A custom Comparator such as `Comparator.nullsFirst(...)` can allow it. Null values are fine. HashMap and LinkedHashMap allow one null key.''',
["Oracle", "Walmart"]),

M("Java collections", '''Which built-in class can be turned into an LRU cache by overriding a single method?''',
["HashMap", "TreeMap", "LinkedHashMap created with accessOrder = true", "ConcurrentSkipListMap"], 2,
'''`new LinkedHashMap<>(cap, 0.75f, true)` reorders entries on access, and overriding `removeEldestEntry` to return `size() > capacity` evicts the least recently used entry. It is not thread-safe. Interviewers usually then ask you to build it yourself with a HashMap and a doubly linked list.''',
["Walmart", "Oracle", "Atlassian"]),

M("Java collections", '''What does this print?
```java
PriorityQueue<Integer> pq = new PriorityQueue<>(List.of(5, 1, 4, 2));
System.out.println(pq.poll() + " " + pq.peek());
```''', ["5 1", "1 2", "1 4", "5 4"], 1,
'''PriorityQueue is a min-heap by default. `poll()` removes the smallest element, 1, and `peek()` then returns the new smallest, 2. Iterating over a PriorityQueue does not give sorted order; only repeated poll does. Use `Comparator.reverseOrder()` for a max-heap.''',
["Walmart", "Oracle", "Amazon"]),

M("Java collections", '''Why can `list.sort((a, b) -> a - b)` be buggy for an `int`/`Integer` list?''',
["Lambdas cannot be comparators", "The subtraction can overflow for large values of opposite sign, giving the wrong ordering",
 "It sorts in descending order", "It throws NullPointerException for every list"], 1,
'''For example, `Integer.MIN_VALUE - 1` overflows to a large positive number, so the comparator reports the wrong sign. Use `Integer.compare(a, b)`, `Comparator.naturalOrder()` or `Comparator.comparingInt(...)`, which never overflow.''',
["Oracle", "Walmart", "Goldman Sachs"]),

M("Java collections", '''What happens when this runs?
```java
List<Integer> nums = List.of(1, 2, null);
```''', ["Creates a list with a null element", "NullPointerException", "Compile error", "Creates [1, 2]"], 1,
'''The `List.of`, `Set.of` and `Map.of` factories (Java 9+) create immutable collections and reject null elements with NullPointerException. They also throw UnsupportedOperationException on add or remove. `Set.of` additionally rejects duplicate elements with IllegalArgumentException.''',
["Walmart", "SAP"]),

M("Java collections", '''What is the underlying data structure of `HashSet`?''',
["A TreeMap", "An array of linked lists with no map", "A HashMap whose keys are the elements and whose values are a shared dummy object",
 "A LinkedList"], 2,
'''`HashSet` wraps a `HashMap<E, Object>`. `add(e)` calls `map.put(e, PRESENT)` and returns true if the key was new. So set performance and the equals/hashCode rules match HashMap's. `LinkedHashSet` uses a LinkedHashMap and `TreeSet` uses a TreeMap.''',
["Oracle", "Walmart", "Paytm"]),
]

coding = [
C("Employees Earning More Than Their Managers (SQL)", "Easy", ["Walmart", "Oracle", "Amazon"],
'''Table `Employee(id INT PK, name VARCHAR, salary INT, managerId INT NULL)`. `managerId` refers to another row's `id`. Write a query that returns the names of employees who earn more than their own manager, in a column named `Employee`.

**Example**
```
Employee
| id | name  | salary | managerId |
| 1  | Joe   | 70000  | 3         |
| 2  | Henry | 80000  | 4         |
| 3  | Sam   | 60000  | NULL      |
| 4  | Max   | 90000  | NULL      |

Output
| Employee |
| Joe      |
```
**Constraints**
- Return rows in any order''',
["You need to compare two rows of the same table: use a self-join.",
 "Join employee e to manager m on e.managerId = m.id, then filter on salary."],
r'''
-- SQL (MySQL 8)
SELECT e.name AS Employee
FROM Employee e
JOIN Employee m ON e.managerId = m.id
WHERE e.salary > m.salary;
''',
'''This is a self-join. The table appears twice under different aliases, `e` for the employee and `m` for the manager. Joining on `e.managerId = m.id` puts each employee's salary next to their manager's on the same row, and the WHERE clause keeps employees who out-earn their manager. An INNER JOIN automatically drops employees without a manager (NULL managerId), which is what we want. An index on `managerId` helps the join on large tables. Interviewers like to follow up with "employees with no manager" (LEFT JOIN plus `IS NULL`) or "the manager chain" (a recursive CTE in MySQL 8).''',
"O(n) with an index on id (hash/nested-loop join)", "O(1) extra", "https://leetcode.com/problems/employees-earning-more-than-their-managers/"),

C("Second Highest Salary (SQL)", "Medium", ["Walmart", "Oracle", "Amazon", "Goldman Sachs"],
'''Table `Employee(id INT PK, salary INT)`. Return the second highest DISTINCT salary as `SecondHighestSalary`. If it does not exist, return NULL (one row containing NULL, not an empty result).

**Example 1**
```
salaries: 100, 200, 300  ->  SecondHighestSalary = 200
```
**Example 2**
```
salaries: 100            ->  SecondHighestSalary = NULL
```
**Follow-up**: generalise to the Nth highest salary.''',
["DISTINCT plus ORDER BY ... LIMIT 1 OFFSET 1 finds it, but an empty result is not NULL.",
 "Wrap the query as a scalar subquery: a scalar subquery with no rows evaluates to NULL."],
r'''
-- SQL (MySQL 8)
-- Approach 1: scalar subquery turns "no row" into NULL
SELECT (
    SELECT DISTINCT salary
    FROM Employee
    ORDER BY salary DESC
    LIMIT 1 OFFSET 1
) AS SecondHighestSalary;

-- Approach 2: classic without LIMIT
-- SELECT MAX(salary) AS SecondHighestSalary
-- FROM Employee
-- WHERE salary < (SELECT MAX(salary) FROM Employee);

-- Nth highest (window function), N = 2:
-- SELECT MAX(salary) AS SecondHighestSalary FROM (
--   SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
--   FROM Employee) t
-- WHERE rnk = 2;
''',
'''This is probably the most frequently asked SQL question in Indian service and product company interviews. `DISTINCT` matters, because with salaries 300, 300, 200 the second highest is 200, not 300. `LIMIT 1 OFFSET 1` skips the top value. On its own it returns an empty set when no second value exists, so wrapping it as a scalar subquery inside an outer SELECT turns that into NULL. The `MAX(...) WHERE salary < MAX` version works everywhere, including databases without LIMIT. For "Nth highest", use `DENSE_RANK()` so ties do not create gaps. Be ready to explain why `RANK()` would fail when there are ties.''',
"O(n log n) for the sort (O(log n) seek with an index on salary)", "O(n) worst case for DISTINCT/sort", "https://leetcode.com/problems/second-highest-salary/"),

C("Department Top Three Salaries (SQL)", "Hard", ["Walmart", "Oracle", "Amazon", "Flipkart"],
'''Tables `Employee(id, name, salary, departmentId)` and `Department(id, name)`. A "high earner" is an employee whose salary is among the top three UNIQUE salaries in their department. Return `Department`, `Employee` and `Salary` for every high earner, in any order.

**Example**
```
IT salaries: Max 90000, Joe 85000, Randy 85000, Will 70000, Janet 69000
Sales: Henry 80000, Sam 60000

Output includes IT: Max 90000, Joe 85000, Randy 85000, Will 70000
                Sales: Henry 80000, Sam 60000
```
**Constraints**
- Ties share a position (85000 counts once among the top three)''',
["Rank salaries per department with a window function partitioned by departmentId.",
 "Which ranking function treats ties as one value without skipping numbers?"],
r'''
-- SQL (MySQL 8)
SELECT d.name AS Department, r.name AS Employee, r.salary AS Salary
FROM (
    SELECT e.*,
           DENSE_RANK() OVER (PARTITION BY e.departmentId
                              ORDER BY e.salary DESC) AS rnk
    FROM Employee e
) r
JOIN Department d ON d.id = r.departmentId
WHERE r.rnk <= 3;

-- Pre-window-function alternative (correlated subquery):
-- SELECT d.name, e.name, e.salary
-- FROM Employee e JOIN Department d ON e.departmentId = d.id
-- WHERE (SELECT COUNT(DISTINCT e2.salary) FROM Employee e2
--        WHERE e2.departmentId = e.departmentId AND e2.salary > e.salary) < 3;
''',
'''`PARTITION BY departmentId` restarts the ranking in every department, and `DENSE_RANK` gives tied salaries the same rank without gaps. So "top three unique salaries" becomes `rnk <= 3`, and tied employees are all returned. The ranking must happen in a derived table or CTE, because window functions cannot appear in WHERE: they are computed after WHERE, in the SELECT phase. The correlated-subquery version counts how many distinct salaries in the same department are higher than the current one. It works on MySQL 5.7 but is O(n^2) without good indexes. Mention a composite index on `(departmentId, salary)`.''',
"O(n log n) (sort within partitions)", "O(n)", "https://leetcode.com/problems/department-top-three-salaries/"),

C("Merge Intervals", "Medium", ["Walmart", "Oracle", "Google", "Microsoft"],
'''Given an array `intervals` where `intervals[i] = [start, end]`, merge every overlapping interval and return the non-overlapping intervals that cover all the input ranges.

**Example 1**
```
Input:  [[1,3],[2,6],[8,10],[15,18]]
Output: [[1,6],[8,10],[15,18]]
```
**Example 2**
```
Input:  [[1,4],[4,5]]
Output: [[1,5]]   // touching intervals overlap
```
**Constraints**
- 1 <= intervals.length <= 10^4
- 0 <= start <= end <= 10^4''',
["Sort by start time; then overlapping intervals become adjacent.",
 "Keep the last merged interval; if the current start <= last end, extend the end, otherwise start a new interval."],
r'''
import java.util.*;

class Solution {
    public int[][] merge(int[][] intervals) {
        Arrays.sort(intervals, Comparator.comparingInt(a -> a[0]));
        List<int[]> merged = new ArrayList<>();
        for (int[] cur : intervals) {
            if (merged.isEmpty() || merged.get(merged.size() - 1)[1] < cur[0]) {
                merged.add(cur);
            } else {
                int[] last = merged.get(merged.size() - 1);
                last[1] = Math.max(last[1], cur[1]);
            }
        }
        return merged.toArray(new int[0][]);
    }
}
''',
'''After sorting by start, any interval that overlaps the current merged block must come right after it. So a single linear scan is enough. Compare each interval with the last merged one: if it starts before or at the last end, extend the end with `max` (to handle fully contained intervals such as [1,10] and [2,3]); otherwise start a new block. `Comparator.comparingInt` avoids the overflow risk of `(a, b) -> a[0] - b[0]`. Walmart asks a variant about merging booking slots; follow-ups include "insert interval" and "minimum meeting rooms" (min-heap of end times). The sort dominates the running time.''',
"O(n log n)", "O(n) for the output (O(log n) sort stack)", "https://leetcode.com/problems/merge-intervals/"),
]

theory = [
T("Clustered vs non-clustered index: how does an index speed up a query, and when can it hurt?",
'''Most relational databases store indexes as **B+ trees**: sorted keys in internal nodes and data or row pointers in linked leaf nodes, so a lookup is O(log n) and range scans are sequential. A **clustered index** determines the physical order of the rows. In InnoDB, the table itself is stored in primary-key order, so each table has exactly one. A **non-clustered (secondary) index** stores the indexed columns plus the primary key, so a lookup may need a second step to fetch the row. A **covering index** that contains every column the query needs avoids that step. Indexes hurt when they slow down INSERT, UPDATE and DELETE (every index must be maintained), use extra storage, are built on low-selectivity columns (such as a boolean), or are bypassed by functions on the column (`WHERE YEAR(created_at) = 2024`), leading wildcards (`LIKE '%x'`) or implicit type conversion.''',
["Walmart", "Oracle", "Amazon", "PhonePe"]),

T("Explain ACID and the anomalies that each isolation level prevents.",
'''**Atomicity:** all of a transaction happens or none of it does (undo log). **Consistency:** constraints hold before and after a transaction. **Isolation:** concurrent transactions behave as if they ran one at a time, depending on the level. **Durability:** committed data survives crashes (redo log, WAL). The anomalies are a **dirty read** (reading uncommitted data), a **non-repeatable read** (the same row returns a different value the second time), and a **phantom read** (a repeated range query returns new rows). READ UNCOMMITTED allows all three. READ COMMITTED prevents dirty reads (default in Oracle and Postgres). REPEATABLE READ also prevents non-repeatable reads (MySQL default; InnoDB also blocks most phantoms using MVCC and gap locks). SERIALIZABLE prevents all of them but reduces concurrency. In Spring, set the level with `@Transactional(isolation = Isolation.READ_COMMITTED)`.''',
["Oracle", "Goldman Sachs", "Walmart", "JP Morgan"]),

T("Explain normalization (1NF to BCNF). When would you deliberately denormalize?",
'''Normalization removes redundancy so that update, insert and delete anomalies cannot happen. **1NF:** atomic values with no repeating groups (no comma-separated phone list in one column). **2NF:** 1NF and no partial dependency of a non-key column on part of a composite key. **3NF:** 2NF and no transitive dependency (a non-key column depending on another non-key column, such as dept_name depending on dept_id). **BCNF:** for every functional dependency X to Y, X must be a superkey. **Denormalize** for read-heavy workloads where joins become the bottleneck: reporting tables, storing `order_total` instead of summing line items on every read, caching a user's name on posts, or NoSQL document models. The cost is keeping copies in sync through triggers, events or batch jobs. Normalize OLTP schemas first, and denormalize based on measured query patterns.''',
["Oracle", "SAP", "Walmart"]),

T("A query in production is slow. How do you troubleshoot and optimize it?",
'''First, **measure**: find it in the slow query log or APM and note how often it runs and how long it takes. Second, run **EXPLAIN** (or `EXPLAIN ANALYZE` in MySQL 8) and look for `type: ALL` (a full scan), large `rows` estimates, `Using filesort` or `Using temporary`, and which index was chosen. Third, **fix the access path**: add or adjust indexes, putting equality columns first in composite indexes and making them covering where useful. Make predicates sargable, with no functions on indexed columns. Avoid `SELECT *`. Use keyset pagination instead of large `OFFSET`s. Fourth, consider the **application side**: N+1 queries from the ORM, missing batching, and caching hot reads in Redis. Finally, archive or partition very large tables, and verify the gain with numbers, for example "the plan went from a full scan of 2M rows to a 40-row range scan, and latency fell from 1.8 s to 30 ms".''',
["Walmart", "Paytm", "PhonePe", "Oracle"]),

T("ArrayList vs LinkedList: how does ArrayList grow, and which would you use?",
'''`ArrayList` is backed by an `Object[]` array. When it is full, it grows to about 1.5 times its size (`old + old >> 1`) and copies the elements over, so `add` is amortised O(1). `get` and `set` are O(1), while inserting or removing in the middle is O(n) because elements shift (the shift is a fast `System.arraycopy`). `LinkedList` is a doubly linked list: O(1) insert or remove at the ends or through an iterator, O(n) index access, about 24 extra bytes per node, and poor CPU cache locality. It also implements `Deque`. In practice, ArrayList wins almost every benchmark, even for many inserts, because of memory locality. Use `ArrayDeque` for stack or queue needs instead of LinkedList. Pre-size an ArrayList (`new ArrayList<>(n)`) when you know the size, to avoid repeated copying.''',
["Oracle", "Walmart", "SAP"]),

T("What is the difference between fail-fast and fail-safe iterators?",
'''**Fail-fast** iterators (ArrayList, HashMap and other non-concurrent collections) track the collection's `modCount`. If the collection is structurally modified outside the iterator during iteration, the next `next()` throws `ConcurrentModificationException`. This is a best-effort bug detector, not a thread-safety guarantee. Remove safely with `iterator.remove()` or `removeIf`. **Fail-safe** (more precisely, weakly consistent or snapshot) iterators come from concurrent collections. `CopyOnWriteArrayList` iterates over a snapshot of the array, so it never throws but does not see later changes. `ConcurrentHashMap` iterators are weakly consistent: they may or may not reflect updates made after creation and never throw CME. The trade-off is that copy-on-write costs a full array copy per write, which suits read-mostly lists such as listener registries.''',
["Walmart", "Oracle", "SAP", "Paytm"]),
]

DAY = build(4, "Walmart & Oracle", "SQL fundamentals and SQL query coding from Walmart and Oracle rounds, plus Java Collections internals and gotchas.", mcqs, coding, theory)
