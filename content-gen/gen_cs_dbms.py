from cs_common import build, B, I, A

notes = [
("DBMS Basics & the ER Model", r"""
A **DBMS** (Database Management System) is software to store, retrieve and manage data while handling concurrency, integrity, security and recovery. An **RDBMS** stores data in **relations (tables)** of rows (tuples) and columns (attributes), queried with SQL — MySQL, PostgreSQL, Oracle, SQL Server.

### Why not just files?
File systems suffer from data redundancy and inconsistency, difficult querying, no concurrency control, no atomicity on crash, weak security and integrity. A DBMS solves all of these.

### Three-schema architecture & data independence
- **External (view) level** – what individual users/apps see.
- **Conceptual (logical) level** – tables, columns, relationships, constraints.
- **Internal (physical) level** – files, indexes, storage layout.

**Physical data independence**: change storage (add an index, move to SSD) without changing the logical schema. **Logical data independence**: change the logical schema (add a column) without breaking external views/apps (harder to achieve).

### Languages
- **DDL** – define structure: `CREATE`, `ALTER`, `DROP`, `TRUNCATE`.
- **DML** – manipulate data: `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
- **DCL** – permissions: `GRANT`, `REVOKE`.
- **TCL** – transactions: `COMMIT`, `ROLLBACK`, `SAVEPOINT`.

### ER (Entity-Relationship) model
A high-level conceptual design tool, drawn as an **ER diagram** before creating tables.

- **Entity** – a real-world object (Customer, Order). **Entity set** – collection of similar entities. Drawn as a rectangle.
- **Weak entity** – can't be uniquely identified by its own attributes; depends on an owner entity (OrderItem depends on Order). Double rectangle; identified by owner's key + **partial key** (discriminator).
- **Attributes** (ovals):
  - Simple vs **composite** (Name → first, last).
  - Single-valued vs **multivalued** (phone numbers — double oval).
  - Stored vs **derived** (age from DOB — dashed oval).
  - **Key attribute** (underlined).
- **Relationship** – association among entities (Customer *places* Order). Diamond.
- **Degree** – unary (Employee manages Employee), binary, ternary.

### Cardinality (mapping constraints)
- **One-to-one (1:1)** – User ↔ Profile.
- **One-to-many (1:N)** – Customer → Orders.
- **Many-to-many (M:N)** – Student ↔ Course, Order ↔ Product.

**Participation**: **total** (every entity must participate, double line — every Order must belong to a Customer) vs **partial**.

### Mapping ER to tables
- Strong entity → table with its attributes; key → primary key.
- Weak entity → table including owner's PK as FK; PK = owner PK + partial key.
- 1:N → put the FK on the "many" side (`orders.customer_id`).
- 1:1 → FK on either side (prefer the side with total participation) with a UNIQUE constraint.
- M:N → **junction table** (`order_items(order_id, product_id, qty)`) with composite PK.
- Multivalued attribute → separate table (`customer_phones`).
- Composite attribute → flatten into columns.

### Extended ER concepts
- **Generalisation** (bottom-up: Car, Bike → Vehicle) and **specialisation** (top-down: Employee → Manager, Engineer); disjoint vs overlapping, total vs partial.
- **Aggregation** – treat a relationship as an entity to relate it further.
- Inheritance mapping to tables (like JPA): single table, table per class, joined — ties neatly to `@Inheritance(strategy = ...)` in Hibernate.

### Relational algebra (quick)
Selection σ (filter rows), Projection π (choose columns), Union ∪, Difference −, Cartesian product ×, Rename ρ, Join ⋈ (natural, theta, outer), Division ÷ ("students who took all courses"). SQL is declarative; the optimiser converts it to a relational-algebra plan.
"""),

("Keys & Integrity Constraints", r"""
Keys uniquely identify rows and link tables.

| Key | Definition | Example (`employee`) |
|---|---|---|
| **Super key** | Any set of attributes that uniquely identifies a row | {emp_id}, {emp_id, name}, {email} |
| **Candidate key** | A **minimal** super key (no proper subset is a super key) | {emp_id}, {email}, {pan} |
| **Primary key** | The candidate key chosen to identify rows; **NOT NULL + UNIQUE**, one per table | emp_id |
| **Alternate key** | Candidate keys not chosen as PK | email, pan |
| **Composite key** | Key made of 2+ columns | (order_id, product_id) in order_items |
| **Foreign key** | Column referencing a PK/unique key in another (or same) table | employee.dept_id → department.id |
| **Unique key** | Values must be unique, but (in most DBs) NULLs allowed | email |
| **Surrogate key** | Artificial key with no business meaning (auto-increment, UUID) | id BIGINT AUTO_INCREMENT |
| **Natural key** | Key with business meaning | PAN, Aadhaar, ISBN |

Relationships: every candidate key is a super key; primary key ⊂ candidate keys; candidate keys − PK = alternate keys.

### Primary key vs unique key
| Primary | Unique |
|---|---|
| One per table | Many per table |
| No NULLs | NULLs allowed (MySQL allows multiple NULLs) |
| In InnoDB, defines the **clustered index** (physical row order) | Creates a secondary (non-clustered) index |

### Surrogate vs natural keys
Surrogate keys (auto-increment `BIGINT` or UUID) are stable, small and never change; natural keys can change (a person changes email) and may be long. Most production schemas use surrogate PKs plus UNIQUE constraints on natural keys. Note: random UUIDv4 as InnoDB PK causes page splits and fragmentation — prefer sequential IDs or time-ordered UUIDv7.

### Integrity constraints
1. **Domain constraint** – values must be from the attribute's domain (type, `CHECK (age >= 18)`, `NOT NULL`, ENUM).
2. **Entity integrity** – primary key can't be NULL.
3. **Referential integrity** – a foreign key must match an existing referenced key or be NULL.
4. **Key constraint** – uniqueness of keys.

### Referential actions
```sql
CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'CREATED',
  CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
    REFERENCES customers(id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_status CHECK (status IN ('CREATED','PAID','SHIPPED','CANCELLED'))
);
```
Options: `CASCADE` (propagate delete/update), `SET NULL`, `SET DEFAULT`, `RESTRICT`/`NO ACTION` (block). Use CASCADE carefully — deleting a customer shouldn't silently delete financial records; many companies use **soft deletes** (`deleted_at`).

### Self-referencing foreign key
`employee.manager_id REFERENCES employee(id)` — models hierarchies; query with self-joins or recursive CTEs (`WITH RECURSIVE`).

### Interview tip
"Find candidate keys" questions: given R(A,B,C,D) and FDs A→B, B→C, C→D, compute closures. A⁺ = {A,B,C,D} = all attributes, so **A is a candidate key**. Any attribute that never appears on the right side of an FD must be part of every candidate key — a handy shortcut.
"""),

("Functional Dependencies & Normalization (1NF to BCNF)", r"""
**Normalization** organises tables to reduce **redundancy** and avoid **anomalies**:
- **Insertion anomaly** – can't add data without unrelated data (can't add a new course until a student enrols).
- **Update anomaly** – the same fact stored in many rows; updating one row leaves inconsistency.
- **Deletion anomaly** – deleting a row loses other facts (delete the last student → lose the course info).

### Functional dependency (FD)
`X → Y` means if two rows agree on X they must agree on Y (emp_id → emp_name).
- **Trivial**: Y ⊆ X. **Full**: Y depends on all of X, not a part. **Partial**: Y depends on part of a composite key. **Transitive**: X → Y and Y → Z (Y not a key) gives X → Z.
- **Armstrong's axioms**: reflexivity, augmentation, transitivity (+ derived union, decomposition, pseudo-transitivity).
- **Attribute closure X⁺** – all attributes determined by X; if X⁺ contains every attribute, X is a super key.
- **Prime attribute** – part of some candidate key.

### Running example
`StudentCourse(student_id, student_name, course_id, course_name, instructor, instructor_phone, grade)` with key (student_id, course_id).
FDs: student_id → student_name; course_id → course_name, instructor; instructor → instructor_phone; (student_id, course_id) → grade.

### 1NF — atomic values
Each cell holds a single atomic value; no repeating groups/arrays. ❌ `phones = "98xx, 97xx"` → separate rows or a `student_phones` table.

### 2NF — 1NF + no partial dependency
Every non-prime attribute must depend on the **whole** candidate key. Only matters with composite keys.
student_name depends only on student_id (partial) → split:
- `Student(student_id, student_name)`
- `Course(course_id, course_name, instructor, instructor_phone)`
- `Enrollment(student_id, course_id, grade)`

### 3NF — 2NF + no transitive dependency
No non-prime attribute depends on another non-prime attribute. Formally, for every FD X → A: X is a super key **or** A is prime.
In `Course`, course_id → instructor → instructor_phone is transitive → split:
- `Course(course_id, course_name, instructor)`
- `Instructor(instructor, instructor_phone)`

### BCNF (Boyce-Codd) — stricter 3NF
For **every** non-trivial FD X → Y, **X must be a super key** (no exception for prime attributes).
Classic case: `Teaches(student, subject, teacher)` with FDs (student, subject) → teacher and teacher → subject (each teacher teaches one subject). Candidate keys: (student, subject) and (student, teacher). It's in 3NF (subject is prime) but **not BCNF** because teacher isn't a super key. Decompose into `(teacher, subject)` and `(student, teacher)`. Trade-off: BCNF decomposition may **not preserve all dependencies**.

### Higher forms (brief)
- **4NF** – no non-trivial **multivalued dependencies** (a person's skills and languages stored in one table create combinations).
- **5NF** – no join dependencies; decomposition is lossless only into specific projections.

### Decomposition properties
- **Lossless join** – rejoining decomposed tables gives exactly the original (holds if the common attribute is a key in at least one table).
- **Dependency preservation** – all FDs checkable without joins. 3NF always achievable with both; BCNF guarantees lossless but not always dependency preservation.

### Denormalization
Intentionally adding redundancy for **read performance** — fewer joins (store `order_total` or `customer_name` on orders), reporting tables, materialised views, read models in CQRS. Costs: extra storage, update complexity, possible inconsistency. OLTP systems usually stay in 3NF; analytics/OLAP uses star schemas (denormalised fact + dimension tables).

### Quick summary table
| Form | Rule |
|---|---|
| 1NF | Atomic values, no repeating groups |
| 2NF | 1NF + no partial dependency on composite key |
| 3NF | 2NF + no transitive dependency |
| BCNF | Every determinant is a super key |
"""),

("Transactions & ACID Properties", r"""
A **transaction** is a logical unit of work — a sequence of operations that must be treated as one: either all succeed or none do. Classic example: transfer ₹500 from A to B.

```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 500 WHERE id = 'A';
UPDATE accounts SET balance = balance + 500 WHERE id = 'B';
COMMIT;      -- or ROLLBACK on error
```
In Spring: `@Transactional` on a service method (rolls back on unchecked exceptions by default).

### ACID
**Atomicity** – all or nothing. If the system crashes after debiting A but before crediting B, the debit is undone. Implemented using **undo logs** (InnoDB undo log) / shadow paging.

**Consistency** – a transaction takes the database from one valid state to another, respecting constraints (PK, FK, CHECK) and business invariants (total money stays the same). Responsibility shared by the DB (constraints) and the application.

**Isolation** – concurrent transactions don't interfere; the result is as if they ran in some serial order (to the degree specified by the isolation level). Implemented using **locking** and/or **MVCC**.

**Durability** – once committed, changes survive crashes/power loss. Implemented with **write-ahead logging (WAL)** — the redo log is flushed (`fsync`) to disk on commit before acknowledging (MySQL `innodb_flush_log_at_trx_commit=1`), plus replication/backups.

### Transaction states
**Active** → **Partially committed** (last statement executed) → **Committed**; or Active → **Failed** → **Aborted** (rolled back) → restart or kill. Then **Terminated**.

### Savepoints
```sql
SAVEPOINT before_items;
-- ... insert items
ROLLBACK TO before_items;
```

### Write-ahead logging & recovery
**WAL rule**: log records describing a change must be written to stable storage **before** the changed data pages are written. On crash recovery (ARIES algorithm):
1. **Analysis** – find active transactions and dirty pages at crash time.
2. **Redo** – repeat history: reapply all logged changes (committed or not) to restore the crash state.
3. **Undo** – roll back transactions that hadn't committed.
**Checkpoints** limit how far back recovery must scan.

Other techniques: **deferred update** (apply changes only at commit — no undo needed) vs **immediate update** (changes written before commit — needs undo and redo); **shadow paging** (copy-on-write pages; swap page table on commit).

### Autocommit
MySQL runs each statement in its own transaction by default (`autocommit=1`). Multi-statement units need an explicit transaction — or Spring's `@Transactional`.

### ACID in distributed systems
Across microservices you can't use a single DB transaction. Options: **Two-Phase Commit (2PC)** (prepare → commit, blocking coordinator, rarely used in microservices) or **Saga pattern** (sequence of local transactions with **compensating actions** — e.g. refund payment if inventory reservation fails), with the **outbox pattern** to reliably publish events. Many NoSQL systems trade strict ACID for **BASE**: Basically Available, Soft state, Eventually consistent.

### Interview tip
Relate to your experience: "Our order placement saves the order, reserves stock and writes an audit row in one `@Transactional` method; I learned the hard way that calling a `@Transactional` method from within the same class bypasses the proxy, so the transaction doesn't apply."
"""),

("Concurrency Control & Isolation Levels", r"""
When transactions run concurrently, the DBMS must prevent them from corrupting each other while still allowing parallelism.

### Concurrency problems (anomalies)
1. **Dirty read** – T2 reads data written by T1 that is **not yet committed**; T1 rolls back → T2 used data that never existed.
2. **Non-repeatable read** – T1 reads a row, T2 updates & commits it, T1 reads again and sees a different value.
3. **Phantom read** – T1 runs a range query (`WHERE amount > 1000`), T2 **inserts** a matching row and commits, T1 re-runs and sees an extra "phantom" row.
4. **Lost update** – T1 and T2 both read stock = 10, both write 9 → one decrement lost.
5. **Write skew** – two transactions read overlapping data and update disjoint rows, violating an invariant (two doctors both go off-call because each saw the other on call).

### SQL standard isolation levels
| Level | Dirty read | Non-repeatable read | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | Possible | Possible | Possible |
| READ COMMITTED | Prevented | Possible | Possible |
| REPEATABLE READ | Prevented | Prevented | Possible (per standard) |
| SERIALIZABLE | Prevented | Prevented | Prevented |

- **MySQL InnoDB default: REPEATABLE READ** — uses MVCC consistent snapshots for plain reads and **next-key (gap) locks** for locking reads, so most phantoms are prevented.
- **PostgreSQL, Oracle, SQL Server default: READ COMMITTED**.
- Higher isolation = more correctness, less concurrency.

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```
Spring: `@Transactional(isolation = Isolation.READ_COMMITTED)`.

### Lock-based protocols
- **Shared (S) lock** – for reading; many transactions can hold S locks together.
- **Exclusive (X) lock** – for writing; incompatible with any other lock.
- Granularity: row, page, table (InnoDB uses row-level locks; MyISAM table-level). Intention locks (IS/IX) support multi-granularity locking.

**Two-Phase Locking (2PL)**: a transaction has a **growing phase** (acquire locks, release none) then a **shrinking phase** (release, acquire none). Guarantees **conflict serializability**, but can deadlock and allows cascading rollbacks.
- **Strict 2PL** – hold all **X locks** until commit/abort → no cascading aborts (used by most DBs).
- **Rigorous 2PL** – hold **all** locks until commit.

### Timestamp ordering
Each transaction gets a timestamp; operations are allowed only if consistent with timestamp order, otherwise the transaction is rolled back and restarted. No deadlocks. **Thomas' write rule** ignores obsolete writes.

### MVCC (Multi-Version Concurrency Control)
Writers create new **versions** of rows instead of overwriting; readers see a **consistent snapshot** as of their start time (or statement time). **Readers don't block writers and writers don't block readers.** InnoDB keeps old versions in the undo log; PostgreSQL keeps tuple versions in the table (cleaned by VACUUM).

### Optimistic vs pessimistic locking (application level)
- **Pessimistic**: lock rows when reading — `SELECT ... FOR UPDATE` (JPA `@Lock(PESSIMISTIC_WRITE)`). Good under high contention (seat booking, inventory).
- **Optimistic**: no lock; check a **version** column on update: `UPDATE product SET stock=?, version=version+1 WHERE id=? AND version=?`; 0 rows updated → conflict → retry. JPA `@Version` throws `OptimisticLockException`. Good when conflicts are rare.

### Fixing the lost update
Atomic update: `UPDATE product SET stock = stock - 1 WHERE id = 7 AND stock > 0;` — single statement, row lock, no read-modify-write race. This is a favourite question for e-commerce companies.

### Deadlocks in DBs
T1 locks row A then wants B; T2 locks B then wants A. InnoDB detects the cycle and rolls back the cheaper transaction (error 1213). Prevent by accessing rows in a consistent order, keeping transactions short, and indexing so updates lock fewer rows. Retry on deadlock errors.
"""),

("Schedules & Serializability", r"""
A **schedule** is the order in which operations (read R, write W, commit) of concurrent transactions are executed.

- **Serial schedule** – transactions run one after another, no interleaving. Always correct but no concurrency.
- **Non-serial (concurrent) schedule** – operations interleaved. Correct only if **serializable**.

### Serializability
A schedule is **serializable** if its effect is equivalent to **some** serial schedule.

### Conflicting operations
Two operations conflict if they:
1. belong to **different transactions**,
2. access the **same data item**, and
3. at least one is a **write**.
So R-W, W-R and W-W conflict; R-R doesn't.

### Conflict serializability
A schedule is conflict serializable if it can be turned into a serial schedule by swapping **non-conflicting adjacent** operations.

**Test – precedence graph:** one node per transaction; draw edge Ti → Tj if an operation of Ti conflicts with and comes **before** an operation of Tj. **Acyclic graph ⇔ conflict serializable**; a topological sort gives the equivalent serial order.

**Example:** S: R1(A) W1(A) R2(A) W2(A) R1(B) W1(B) R2(B) W2(B)
- W1(A) before R2(A) → T1 → T2. W1(B) before R2(B) → T1 → T2.
- No cycle → conflict serializable, equivalent to T1, T2.

**Non-serializable example:** S: R1(A) R2(A) W1(A) W2(A)
- R1(A) before W2(A) → T1 → T2; R2(A) before W1(A) → T2 → T1 → **cycle** → not conflict serializable (this is the lost update).

### View serializability
Weaker (broader) condition: schedules are view-equivalent if they have the same initial reads, same reads-from relationships and the same final writes. Every conflict-serializable schedule is view serializable, but not vice versa — the extra ones involve **blind writes** (writes without prior reads). Testing view serializability is NP-complete, so DBMSs enforce conflict serializability.

### Recoverability
Even serializable schedules must handle aborts correctly.
- **Recoverable schedule** – if Tj reads data written by Ti, then Ti commits **before** Tj commits. Otherwise, if Ti aborts after Tj committed, we can't undo Tj → irrecoverable.
- **Cascadeless schedule** – transactions read only **committed** data, so one abort never forces others to abort (**avoids cascading rollback**).
- **Strict schedule** – no transaction reads **or writes** an item until the last transaction that wrote it has committed/aborted. Makes undo simple (restore before-image).

Hierarchy: Strict ⊂ Cascadeless ⊂ Recoverable. **Strict 2PL** produces strict, conflict-serializable schedules — which is why databases use it.

### Practice drill
For a given schedule:
1. List conflicting pairs and draw the precedence graph.
2. Check for cycles → conflict serializable or not.
3. Check reads-from + commit order → recoverable / cascadeless / strict.

These questions appear in some product-company CS-fundamentals rounds and online assessments (and GATE-style MCQs), so practise two or three on paper.
"""),

("Indexing & Query Optimization", r"""
An **index** is an auxiliary data structure that speeds up lookups at the cost of extra storage and slower writes — like a book's index.

### Without an index
A query like `SELECT * FROM orders WHERE customer_id = 42` performs a **full table scan**: O(n) reads.

### B-Tree / B+ Tree indexes (default in MySQL InnoDB, PostgreSQL)
A **B+ tree** is a balanced, high-fanout tree:
- Internal nodes hold only keys for navigation; **all data/pointers are in leaves**.
- Leaves are **linked**, making **range scans** (`BETWEEN`, `>`, `ORDER BY`) efficient.
- High fanout (hundreds of keys per 16 KB page) → height 3–4 even for millions/billions of rows → lookups in O(log n) with few disk reads.
**B+ tree vs B-tree:** B-trees store data in internal nodes too; B+ trees keep internal nodes small (more keys per page → shallower tree) and support sequential leaf scans — ideal for disk-based DBs.

### Clustered vs non-clustered (secondary) index
- **Clustered index** – the table data itself is stored in the index order (leaf = full row). Only **one per table**. In InnoDB the **primary key is the clustered index**.
- **Secondary index** – separate structure; leaf stores the indexed column(s) + a pointer. In InnoDB, the pointer is the **primary key value**, so a secondary-index lookup = index search + PK lookup ("bookmark lookup"/"back to table").
- **Covering index** – the index contains all columns the query needs, so the table isn't touched (`EXPLAIN` shows "Using index").

### Other index types
- **Hash index** – O(1) equality lookups, useless for ranges/sorting (MySQL MEMORY engine; InnoDB adaptive hash index internally).
- **Composite (multi-column) index** – `(customer_id, status, created_at)`. Follows the **leftmost prefix rule**: usable for filters on `customer_id`, `customer_id + status`, all three; **not** for `status` alone.
- **Unique index**, **full-text index** (MATCH ... AGAINST), **spatial (R-tree)**, **bitmap** (low-cardinality columns in data warehouses), **GIN/GiST** (PostgreSQL JSONB, arrays), **LSM trees** (write-optimised, used by Cassandra, RocksDB).
- **Dense vs sparse** index: dense has an entry for every record; sparse has entries for some (requires sorted data).

### When indexes are NOT used (common pitfalls)
- Functions on the column: `WHERE YEAR(created_at) = 2025` → rewrite as a range `created_at >= '2025-01-01' AND created_at < '2026-01-01'`.
- Leading wildcard: `LIKE '%kumar'`.
- Implicit type conversion: `WHERE phone = 9876543210` when phone is VARCHAR.
- `OR` across different columns (may need separate indexes / UNION).
- Low selectivity columns (gender, boolean) – optimiser prefers a scan.
- Not using the leftmost column of a composite index.

### Cost of indexes
Every INSERT/UPDATE/DELETE must update every index → slower writes; extra disk and memory. Don't index everything — index columns used in **WHERE, JOIN, ORDER BY, GROUP BY** with good selectivity.

### Reading EXPLAIN (MySQL)
```sql
EXPLAIN SELECT id, total FROM orders WHERE customer_id = 42 AND status = 'PAID' ORDER BY created_at DESC LIMIT 20;
```
Look at `type` (ALL = full scan ❌, index, range, ref, eq_ref, const ✅), `key` (index chosen), `rows` (estimated rows examined), `Extra` ("Using filesort", "Using temporary" are warning signs; "Using index" is good). `EXPLAIN ANALYZE` shows actual timings.

Fix for the above: composite index `(customer_id, status, created_at)` → no filesort, minimal rows.

### Query optimisation checklist
1. Select only needed columns (avoid `SELECT *`), paginate with **keyset pagination** (`WHERE id < ? LIMIT 20`) for deep pages instead of large OFFSET.
2. Proper indexes; check with EXPLAIN.
3. Avoid N+1 queries from ORM (JPA `JOIN FETCH`, `@EntityGraph`, batch fetching).
4. Use joins wisely; ensure join columns are indexed.
5. Cache hot reads (Redis); read replicas for read-heavy loads.
6. Partition very large tables (by date) and archive old data.
7. Batch inserts (`saveAll` with `hibernate.jdbc.batch_size`).
8. Slow query log to find offenders.
"""),

("NoSQL Databases & CAP Theorem", r"""
**NoSQL** ("not only SQL") databases drop some relational features (fixed schema, joins, sometimes full ACID) to gain **horizontal scalability, flexible schemas, and high throughput** for specific access patterns.

### Four main types
| Type | Data model | Examples | Good for |
|---|---|---|---|
| **Key-value** | Key → opaque value | Redis, DynamoDB, Memcached | Caching, sessions, rate limiting, leaderboards |
| **Document** | JSON/BSON documents with nested fields | MongoDB, Couchbase, Firestore | Product catalogues, CMS, user profiles with varying attributes |
| **Wide-column** | Rows with dynamic columns grouped in column families, partitioned by key | Cassandra, HBase, ScyllaDB, Bigtable | Massive write-heavy time-series, messaging, IoT, activity feeds |
| **Graph** | Nodes and edges with properties | Neo4j, Amazon Neptune | Social networks, recommendations, fraud detection |

Others: search engines (Elasticsearch/OpenSearch – inverted index), time-series DBs (InfluxDB, TimescaleDB), vector databases (pgvector, Pinecone) for AI similarity search.

### SQL vs NoSQL
| SQL (RDBMS) | NoSQL |
|---|---|
| Fixed schema, tables & relations | Flexible/dynamic schema |
| Strong ACID transactions, joins | Often limited joins; transactions vary (MongoDB has multi-document ACID since 4.0) |
| Vertical scaling primarily (+ read replicas, sharding is hard) | Designed for **horizontal scaling** / sharding |
| SQL standard | Database-specific APIs |
| Best for structured data with complex queries and integrity needs (payments, orders, banking) | Best for huge scale, high write throughput, varied/evolving structure, known access patterns |

Real systems are **polyglot**: MySQL for orders/payments, Redis for cache and sessions, Elasticsearch for product search, Cassandra/Kafka for events.

### CAP theorem
In a distributed data store, when a **network partition (P)** happens you must choose between:
- **Consistency (C)** – every read gets the most recent write (or an error).
- **Availability (A)** – every request gets a non-error response (possibly stale).

Since partitions are unavoidable in distributed systems, the real choice is **CP vs AP** during a partition:
- **CP** – HBase, MongoDB (default majority writes/primary reads), ZooKeeper, etcd: may reject requests to stay consistent.
- **AP** – Cassandra, DynamoDB (default eventual reads), CouchDB: stay available, reconcile later (eventual consistency).
A single-node RDBMS is "CA" only because it has no partitions to tolerate.

**PACELC** extends CAP: if Partition → choose A or C; **E**lse (normal operation) → choose **L**atency or **C**onsistency. Cassandra is PA/EL, typical RDBMS clusters PC/EC.

### Consistency models
Strong (linearizable) → sequential → causal → read-your-writes → **eventual** consistency. Cassandra offers **tunable consistency**: with replication factor N, read quorum R and write quorum W, **R + W > N** guarantees reads see the latest write.

### BASE
**B**asically **A**vailable, **S**oft state, **E**ventually consistent — the philosophy of many AP NoSQL systems, contrasting ACID.

### Scaling techniques (apply to both worlds)
- **Replication** – copies of data on multiple nodes (leader-follower, multi-leader, leaderless) for availability and read scaling. Replication lag causes stale reads.
- **Sharding/partitioning** – split data across nodes by a **shard key** (hash or range). Choose keys to avoid hotspots; **consistent hashing** minimises data movement when nodes are added/removed.

### MongoDB quick facts (often asked)
Documents in collections, `_id` primary key, embedding vs referencing (embed for one-to-few data read together; reference for large/unbounded relations), aggregation pipeline (`$match`, `$group`, `$lookup`), indexes (single, compound, text, TTL), replica sets for HA, sharding for scale.

### Redis quick facts
In-memory, single-threaded command execution (I/O threads since 6.0), data structures (strings, hashes, lists, sets, sorted sets, streams), TTLs, persistence via RDB snapshots/AOF, used as cache (cache-aside pattern), distributed lock, rate limiter, pub/sub.
"""),
]

qa = [
("What is the difference between DBMS and RDBMS?", r"""
- **DBMS** – software for storing and managing data; data can be stored as files, hierarchies, or networks. May not enforce relationships, normalization, or full ACID; often single-user. Examples: file-based systems, early hierarchical DBs (IMS), XML stores.
- **RDBMS** – a DBMS based on the **relational model** (E.F. Codd): data in **tables** with rows and columns, relationships through **primary/foreign keys**, integrity constraints, normalization, SQL, multi-user concurrency control and ACID transactions. Examples: MySQL, PostgreSQL, Oracle, SQL Server.

| DBMS | RDBMS |
|---|---|
| No relationships enforced | Relationships via keys |
| Redundancy common | Normalization reduces redundancy |
| Small data, single user | Large data, many concurrent users |
| Limited security/integrity | Constraints, ACID, access control |
""", B, ["basics"], False),

("Explain the different types of keys in DBMS.", r"""
- **Super key** – any set of columns that uniquely identifies a row (e.g. {emp_id}, {emp_id, name}).
- **Candidate key** – a minimal super key (no redundant column). A table can have several: emp_id, email, PAN.
- **Primary key** – the chosen candidate key; unique and NOT NULL; one per table; in InnoDB it's the clustered index.
- **Alternate key** – candidate keys not chosen as primary.
- **Composite key** – a key with 2+ columns, e.g. (order_id, product_id).
- **Foreign key** – a column referencing another table's primary/unique key; enforces referential integrity.
- **Unique key** – enforces uniqueness but allows NULL(s); many per table.
- **Surrogate key** – system-generated ID without business meaning (AUTO_INCREMENT, UUID) vs **natural key** (PAN, ISBN).

Relationship: Primary ⊆ Candidate ⊆ Super keys.
""", B, ["keys"], True),

("What is the difference between a primary key and a unique key?", r"""
| Primary key | Unique key |
|---|---|
| Uniquely identifies each row | Ensures column values are unique |
| **Cannot be NULL** | **NULL allowed** (MySQL/PostgreSQL allow multiple NULLs; SQL Server allows one) |
| Only **one** per table | **Multiple** per table |
| In InnoDB, becomes the **clustered index** (determines physical row order) | Creates a **secondary (non-clustered)** index |
| Referenced by foreign keys typically | Can also be referenced by foreign keys |

Example: `users(id PK, email UNIQUE, phone UNIQUE)` — `id` is a surrogate primary key used in joins, while `email`/`phone` are business identifiers that must be unique but might be optional.
""", B, ["keys"], True),

("What is normalization? Explain 1NF, 2NF, 3NF and BCNF with examples.", r"""
Normalization structures tables to minimise redundancy and avoid insert/update/delete anomalies.

- **1NF** – atomic values, no repeating groups. ❌ `phones = '98x, 97x'` → separate rows/table.
- **2NF** – 1NF + **no partial dependency** (non-key attribute depending on part of a composite key). In `Enrollment(student_id, course_id, student_name, grade)`, student_name depends only on student_id → move to `Student(student_id, student_name)`.
- **3NF** – 2NF + **no transitive dependency** (non-key → non-key). In `Employee(emp_id, dept_id, dept_name)`, emp_id → dept_id → dept_name → move dept_name to `Department(dept_id, dept_name)`.
- **BCNF** – for every FD X → Y, **X is a super key**. Example: `(student, subject, teacher)` with teacher → subject; teacher isn't a super key → split into `(teacher, subject)` and `(student, teacher)`.

OLTP schemas typically target 3NF/BCNF; denormalise selectively for read performance.
""", I, ["normalization"], True),

("What is the difference between 3NF and BCNF?", r"""
**3NF** condition: for every non-trivial FD X → A, either X is a **super key**, or A is a **prime attribute** (part of some candidate key).

**BCNF** condition: for every non-trivial FD X → A, X must be a **super key** — the "A is prime" escape is removed. So BCNF is stricter; every BCNF relation is in 3NF but not vice versa.

Example in 3NF but not BCNF: `Booking(student, subject, teacher)`, FDs: {student, subject} → teacher, teacher → subject. Candidate keys: {student, subject}, {student, teacher}. teacher → subject: teacher isn't a super key, but subject is prime → OK for 3NF, violates BCNF.

Trade-off: decomposing into BCNF is always **lossless** but may **not preserve dependencies** ({student, subject} → teacher can't be checked within one table). 3NF can always be achieved with both lossless join and dependency preservation.
""", A, ["normalization"], False),

("What are insertion, update and deletion anomalies?", r"""
Anomalies occur in poorly normalised tables where multiple facts are stored together. Consider `Emp(emp_id, name, dept_id, dept_name, dept_location)`:

- **Insertion anomaly** – can't insert a new department until at least one employee belongs to it (emp_id would be NULL in the PK).
- **Update anomaly** – department location is repeated for every employee; changing it requires updating many rows, and missing one leaves inconsistent data.
- **Deletion anomaly** – deleting the last employee of a department also deletes all information about that department.

Fix: normalise into `Employee(emp_id, name, dept_id)` and `Department(dept_id, dept_name, location)`. Each fact is stored once.
""", B, ["normalization"], False),

("What is denormalization and when would you use it?", r"""
**Denormalization** intentionally introduces redundancy into a normalised schema to **improve read performance** by avoiding expensive joins or aggregations.

Examples:
- Storing `customer_name` on `orders` so the order list doesn't join `customers`.
- Keeping a precomputed `order_total` or `like_count` column.
- Reporting/analytics tables, star schemas, materialised views.
- Read models in CQRS, or documents in MongoDB embedding related data.

When to use: read-heavy workloads, latency-sensitive queries, dashboards, data that rarely changes.

Costs: more storage, more complex writes (keep copies in sync via triggers, application logic, or events), risk of inconsistency. Approach: start normalised (3NF), measure, then denormalise specific hot paths.
""", I, ["normalization", "performance"], False),

("Explain ACID properties with an example.", r"""
Using a bank transfer of ₹1000 from A to B:

- **Atomicity** – both the debit and the credit happen, or neither. If the server crashes after the debit, the DB rolls it back using the undo log.
- **Consistency** – the transaction moves the DB from one valid state to another: constraints hold (balance ≥ 0 CHECK, FKs) and the total money remains the same.
- **Isolation** – a concurrent transaction calculating total bank balance won't see the intermediate state where A is debited but B isn't credited (degree depends on isolation level).
- **Durability** – once COMMIT returns, the transfer survives crashes, because the redo log/WAL was flushed to disk.

Implementation: atomicity & durability via logging (undo/redo, WAL); isolation via locks and MVCC; consistency via constraints plus correct application logic. In Spring Boot, `@Transactional` demarcates the transaction.
""", B, ["acid", "transactions"], True),

("What are dirty reads, non-repeatable reads and phantom reads? Explain isolation levels.", r"""
- **Dirty read** – reading another transaction's **uncommitted** changes (which may be rolled back).
- **Non-repeatable read** – the same row read twice in one transaction returns different values because another transaction **updated** and committed in between.
- **Phantom read** – a range query returns a different **set of rows** on re-execution because another transaction **inserted/deleted** matching rows.

Isolation levels (SQL standard):
| Level | Dirty | Non-repeatable | Phantom |
|---|---|---|---|
| Read Uncommitted | ✔ possible | ✔ | ✔ |
| Read Committed | ✘ | ✔ | ✔ |
| Repeatable Read | ✘ | ✘ | ✔ |
| Serializable | ✘ | ✘ | ✘ |

MySQL InnoDB defaults to **Repeatable Read** (MVCC snapshots + next-key locks largely prevent phantoms); PostgreSQL/Oracle/SQL Server default to **Read Committed**. Higher isolation = fewer anomalies but less concurrency.
""", I, ["isolation", "concurrency"], True),

("What is the lost update problem? How do you prevent it? (Optimistic vs pessimistic locking)", r"""
**Lost update:** two transactions read the same value and both write back updates based on it; one update overwrites the other. E.g. stock = 10, two buyers read 10 and both write 9 → one sale lost.

Solutions:
1. **Atomic update** – let the DB do read-modify-write in one statement:
```sql
UPDATE product SET stock = stock - 1 WHERE id = 7 AND stock > 0;
```
2. **Pessimistic locking** – lock on read: `SELECT stock FROM product WHERE id = 7 FOR UPDATE;` (JPA `@Lock(LockModeType.PESSIMISTIC_WRITE)`). Others wait. Best under high contention (flash sales, seat booking), risk of deadlocks/waiting.
3. **Optimistic locking** – no locks; a `version` column checked on update:
```sql
UPDATE product SET stock = 9, version = 6 WHERE id = 7 AND version = 5;  -- 0 rows → conflict, retry
```
JPA `@Version` does this automatically and throws `OptimisticLockException`. Best when conflicts are rare.
4. Higher isolation (Serializable).
""", I, ["concurrency", "locking"], True),

("What is Two-Phase Locking (2PL)? What is strict 2PL?", r"""
**2PL** is a locking protocol that guarantees **conflict serializability**. Each transaction has two phases:
1. **Growing phase** – acquires locks (shared/exclusive), releases none.
2. **Shrinking phase** – releases locks, acquires no new ones.
The point where the last lock is acquired is the **lock point**; transactions serialize in lock-point order.

Problems of basic 2PL: **deadlocks** are possible, and **cascading rollbacks** — another transaction may read a value written by T after T released its lock but before T aborts.

- **Strict 2PL** – holds all **exclusive (write) locks until commit/abort**. Prevents cascading aborts and produces strict schedules. Used by most lock-based DBMSs.
- **Rigorous 2PL** – holds **all** locks (shared and exclusive) until commit; transactions serialize in commit order.
- **Conservative 2PL** – acquires all locks before starting; deadlock-free but impractical.
""", A, ["concurrency", "locking"], False),

("What is MVCC (Multi-Version Concurrency Control)?", r"""
**MVCC** lets a database keep **multiple versions of a row** so that readers and writers don't block each other.

How it works (InnoDB-style):
- Each row stores hidden transaction metadata (creating transaction ID, pointer to the previous version in the **undo log**).
- A transaction reading data gets a **read view (snapshot)**: it sees only versions committed before the snapshot, reconstructing older versions from the undo log if needed.
- Writers create new versions instead of overwriting in place; old versions are purged when no snapshot needs them.

Benefits: **readers never block writers and writers never block readers**, high concurrency, consistent reads without locks. Writers still lock rows against other writers.

In MySQL **Repeatable Read**, the snapshot is taken at the first read of the transaction; in **Read Committed** a new snapshot per statement. PostgreSQL stores versions in the table itself and cleans up with VACUUM.
""", A, ["concurrency", "mvcc"], False),

("What is serializability? How do you check if a schedule is conflict serializable?", r"""
A concurrent schedule is **serializable** if its outcome is equivalent to some **serial** execution of the same transactions — it's the correctness criterion for concurrency.

**Conflict serializability** test:
1. Identify **conflicting operations**: different transactions, same data item, at least one write (R-W, W-R, W-W).
2. Build a **precedence graph**: node per transaction; edge Ti → Tj if Ti's conflicting operation precedes Tj's.
3. If the graph has **no cycle**, the schedule is conflict serializable; a topological order gives the equivalent serial schedule.

Example: `R1(A) R2(A) W1(A) W2(A)` → R2(A) before W1(A) gives T2→T1; R1(A) before W2(A) gives T1→T2 → **cycle** → not serializable (classic lost update).

**View serializability** is a broader notion (allows blind writes) but is NP-hard to test, so DBMSs enforce conflict serializability (e.g. via strict 2PL).
""", A, ["serializability", "transactions"], False),

("What are recoverable, cascadeless and strict schedules?", r"""
- **Recoverable** – if T2 reads a value written by T1, then **T1 commits before T2 commits**. Otherwise, if T1 aborts after T2 committed, T2's result is based on invalid data and can't be undone.
- **Cascadeless (avoids cascading rollback)** – transactions read only **committed** data. Then one transaction's abort never forces others to abort.
- **Strict** – a data item written by T can't be read **or overwritten** by others until T commits or aborts. Makes recovery simple (restore the before-image).

Hierarchy: **Strict ⊂ Cascadeless ⊂ Recoverable**. Strict 2PL yields strict schedules, which is why most databases use it.

Example of a non-recoverable schedule: W1(A), R2(A), C2, A1 — T2 committed after reading T1's uncommitted write, then T1 aborted.
""", A, ["transactions", "recovery"], False),

("What is an index? How does a B+ tree index work?", r"""
An **index** is a data structure that speeds up data retrieval by avoiding full table scans, at the cost of extra storage and slower writes.

**B+ tree** (default in MySQL InnoDB, PostgreSQL):
- Balanced tree with very high **fanout** (hundreds of keys per node/page), so even a billion rows need only ~3–4 levels → few disk reads per lookup (O(log n)).
- **Internal nodes** store only keys for navigation; **all records (or pointers) live in the leaves**.
- **Leaves are linked** in sorted order, making **range queries** and `ORDER BY` efficient — find the start, then scan sideways.
- Stays balanced on inserts/deletes via node splits/merges.

Compared to a B-tree, B+ trees keep internal nodes smaller (more keys per page → shallower) and support efficient sequential scans. Hash indexes give O(1) equality lookups but can't do ranges or sorting.
""", I, ["indexing"], True),

("What is the difference between a clustered and non-clustered index?", r"""
- **Clustered index** – determines the **physical order of rows**; the leaf nodes contain the actual row data. Only **one** per table. In MySQL InnoDB the **primary key** is the clustered index (if none, the first NOT NULL unique key or a hidden row ID).
- **Non-clustered (secondary) index** – a separate structure whose leaves hold the indexed columns plus a **pointer** to the row. In InnoDB the pointer is the **primary key value**, so a lookup searches the secondary index, then the clustered index ("back to table"). Many allowed per table.

Implications:
- Range queries on the clustered key are very fast (rows are contiguous).
- A large PK (e.g. random UUID string) bloats every secondary index and causes page splits — prefer compact, increasing PKs.
- A **covering index** (all needed columns in the secondary index) avoids the extra lookup.
""", I, ["indexing"], True),

("When does a database not use an index? What are the disadvantages of indexes?", r"""
Indexes get skipped when:
1. A **function or expression** wraps the column: `WHERE LOWER(email) = ?`, `YEAR(created_at) = 2025` (use functional indexes or rewrite as a range).
2. **Leading wildcard** `LIKE '%abc'`.
3. **Implicit type conversion** (comparing a VARCHAR column to a number).
4. The **leftmost prefix** of a composite index isn't used (index `(a, b)` with `WHERE b = ?`).
5. **Low selectivity** – the optimiser estimates that a full scan is cheaper (e.g. `status = 'ACTIVE'` matching 90% of rows).
6. `OR` conditions on different unindexed columns, `!=`/`NOT IN` in many cases.
7. Stale statistics mislead the optimiser.

Disadvantages: extra **disk and memory**, slower **INSERT/UPDATE/DELETE** (each index must be maintained), potential lock contention, and too many indexes confuse the optimiser. Index columns used in WHERE/JOIN/ORDER BY with good selectivity, and verify with `EXPLAIN`.
""", I, ["indexing", "optimization"], True),

("What is a composite index and the leftmost prefix rule?", r"""
A **composite index** is built on multiple columns, e.g. `CREATE INDEX idx ON orders(customer_id, status, created_at);`. Entries are sorted by customer_id, then status, then created_at — like a phone book sorted by last name, then first name.

**Leftmost prefix rule:** the index can be used for queries that filter on a **leftmost prefix** of its columns:
- ✅ `WHERE customer_id = 1`
- ✅ `WHERE customer_id = 1 AND status = 'PAID'`
- ✅ `WHERE customer_id = 1 AND status = 'PAID' ORDER BY created_at` (no filesort)
- ⚠ `WHERE customer_id = 1 AND created_at > ?` (uses customer_id part; created_at can't use index order across all statuses)
- ❌ `WHERE status = 'PAID'` (skips the first column; MySQL 8 may use *skip scan* in limited cases)

Column order guideline: equality-filtered columns first, then range/sort columns; put more selective columns earlier when other factors are equal.
""", I, ["indexing"], True),

("What is the CAP theorem?", r"""
The **CAP theorem** (Brewer) states that a distributed data store can't simultaneously guarantee all three of:
- **Consistency** – every read returns the latest write (or an error).
- **Availability** – every request receives a non-error response, without guaranteeing it's the latest.
- **Partition tolerance** – the system keeps working despite network messages being lost between nodes.

Since network partitions are inevitable in distributed systems, during a partition you must choose:
- **CP** – sacrifice availability to remain consistent (MongoDB with majority concerns, HBase, ZooKeeper, etcd). Suitable for payments, inventory.
- **AP** – remain available with possibly stale data, reconciling later (Cassandra, DynamoDB default, CouchDB). Suitable for social feeds, likes, shopping carts.

**PACELC** adds: Else (no partition), trade off **Latency vs Consistency**. Many systems offer tunable consistency (Cassandra quorum: R + W > N).
""", I, ["nosql", "cap", "distributed"], True),

("SQL vs NoSQL — how do you decide which to use?", r"""
Choose **SQL (MySQL/PostgreSQL)** when:
- Data is structured with clear relationships (orders, payments, users).
- You need **ACID transactions**, joins, constraints and ad-hoc queries.
- Consistency is critical (finance, inventory, bookings).

Choose **NoSQL** when:
- You need **massive horizontal scale** and very high write throughput (events, logs, IoT) → wide-column (Cassandra).
- Schema is flexible or evolves rapidly (product catalogue with varied attributes) → document (MongoDB).
- Simple key-based access at very low latency (cache, sessions, counters) → key-value (Redis, DynamoDB).
- Relationship traversal is the core query (social graph, fraud rings) → graph (Neo4j).

Most real systems are **polyglot**: MySQL as the source of truth, Redis for caching, Elasticsearch for search, Kafka/Cassandra for events. In interviews, justify with access patterns, consistency needs, scale and team familiarity.
""", I, ["nosql", "design"], True),

("What are the types of NoSQL databases? Give examples and use cases.", r"""
1. **Key-value stores** – data as key → value, extremely fast lookups. *Redis, DynamoDB, Memcached.* Use: caching, sessions, rate limiting, leaderboards (Redis sorted sets), feature flags.
2. **Document stores** – self-describing JSON/BSON documents with nested fields, indexable and queryable. *MongoDB, Couchbase, Firestore.* Use: product catalogues, CMS, user profiles, mobile backends.
3. **Wide-column stores** – rows identified by a partition key, with flexible columns; optimised for huge write volumes and queries by key. *Cassandra, HBase, ScyllaDB, Bigtable.* Use: time-series, messaging (Discord used Cassandra/Scylla), activity logs, IoT telemetry.
4. **Graph databases** – nodes and relationships as first-class citizens; efficient multi-hop traversals. *Neo4j, Amazon Neptune.* Use: social networks, recommendations, fraud detection, knowledge graphs.

Also: search engines (Elasticsearch), time-series DBs (InfluxDB), vector DBs (Pinecone, pgvector) for semantic search and AI features.
""", B, ["nosql"], True),

("What is the difference between DELETE, TRUNCATE and DROP?", r"""
| | DELETE | TRUNCATE | DROP |
|---|---|---|---|
| Type | DML | DDL | DDL |
| Removes | Selected rows (`WHERE`) or all | All rows | Entire table (data + structure + indexes) |
| WHERE clause | Yes | No | No |
| Rollback | Yes (within a transaction) | Generally no in MySQL (implicit commit); yes in PostgreSQL | Generally no in MySQL; yes in PostgreSQL |
| Triggers | Fires DELETE triggers | No | No |
| Speed | Slower (row by row, logged) | Fast (deallocates pages) | Fast |
| Auto-increment | Not reset | **Reset** | Gone with table |
| FK referenced table | Allowed (subject to constraints) | Fails if referenced by FK (MySQL) | Fails unless constraints dropped/cascade |

Use DELETE for selective removal, TRUNCATE to empty a staging table, DROP to remove the table entirely.
""", B, ["sql", "basics"], True),

("What is a weak entity? How is it represented in ER diagrams and tables?", r"""
A **weak entity** cannot be uniquely identified by its own attributes alone; it depends on a related **owner (strong) entity** through an **identifying relationship**, and has total participation in it.

Example: `OrderItem` – line number 1, 2, 3 exists in every order, so line_no alone isn't unique; it's unique only within an `Order`. Similarly `Dependent` of an `Employee`.

ER diagram: weak entity as a **double rectangle**, identifying relationship as a **double diamond**, its **partial key (discriminator)** underlined with a dashed line, and a double line for total participation.

Table mapping: include the owner's primary key as a foreign key; the primary key = owner PK + partial key:
```sql
CREATE TABLE order_item (
  order_id BIGINT, line_no INT, product_id BIGINT, qty INT,
  PRIMARY KEY (order_id, line_no),
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
```
""", I, ["er-model"], False),

("How is a many-to-many relationship implemented in a relational database?", r"""
An M:N relationship can't be represented by a single foreign key, so we create a **junction (bridge/associative) table** containing foreign keys to both tables, typically with a composite primary key, plus any relationship attributes.

Example: Students ↔ Courses.
```sql
CREATE TABLE enrollment (
  student_id BIGINT NOT NULL,
  course_id  BIGINT NOT NULL,
  enrolled_on DATE,
  grade CHAR(2),
  PRIMARY KEY (student_id, course_id),
  FOREIGN KEY (student_id) REFERENCES student(id),
  FOREIGN KEY (course_id) REFERENCES course(id)
);
CREATE INDEX idx_enrollment_course ON enrollment(course_id); -- for reverse lookups
```
In JPA, `@ManyToMany` with `@JoinTable` creates this; but when the relationship has its own attributes (grade, quantity, price), model it as a separate entity with two `@ManyToOne` relations — a common best-practice point.
""", B, ["er-model", "design"], True),

("What is a deadlock in a database and how is it handled?", r"""
A database deadlock occurs when two transactions each hold locks the other needs:
```
T1: UPDATE account SET ... WHERE id = 1;   -- locks row 1
T2: UPDATE account SET ... WHERE id = 2;   -- locks row 2
T1: UPDATE account SET ... WHERE id = 2;   -- waits for T2
T2: UPDATE account SET ... WHERE id = 1;   -- waits for T1 → deadlock
```
**Handling:** InnoDB maintains a wait-for graph, **detects** the cycle immediately and **rolls back** the transaction with less work (error 1213 "Deadlock found when trying to get lock"); the other proceeds. Lock wait timeouts (`innodb_lock_wait_timeout`) are a fallback.

**Prevention in application code:**
- Access rows in a **consistent order** (e.g. lock accounts by ascending id in transfers).
- Keep transactions **short**; no user interaction or remote calls inside.
- Use proper **indexes** so updates lock fewer rows (no gap/table-scan locks).
- Use lower isolation where acceptable.
- **Retry** the transaction on deadlock errors (Spring Retry).
""", I, ["concurrency", "deadlock"], False),
]

sources = [
("Database System Concepts (Silberschatz, Korth, Sudarshan) - book site", "https://www.db-book.com/"),
("MySQL 8 Reference - InnoDB Transaction Isolation Levels", "https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html"),
("MySQL 8 Reference - How MySQL Uses Indexes", "https://dev.mysql.com/doc/refman/8.0/en/mysql-indexes.html"),
("PostgreSQL docs - Concurrency Control (MVCC)", "https://www.postgresql.org/docs/current/mvcc.html"),
("Use The Index, Luke - SQL indexing guide", "https://use-the-index-luke.com/"),
("GeeksforGeeks - DBMS Interview Questions", "https://www.geeksforgeeks.org/dbms-interview-questions/"),
("InterviewBit - DBMS Interview Questions", "https://www.interviewbit.com/dbms-interview-questions/"),
("MongoDB - NoSQL explained", "https://www.mongodb.com/resources/basics/databases/nosql-explained"),
]

build("dbms", "dbms", "DBMS Theory", 9, "🗄️",
      "Relational theory for interviews: ER modelling, keys, normalization, ACID, isolation and concurrency control, indexing and NoSQL/CAP.",
      notes, qa, sources)
