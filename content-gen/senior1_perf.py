from senior1_common import build, B, I, A

NOTES = [
("Performance Vocabulary: Latency, Throughput, Percentiles and Little's Law", r"""
## Latency vs throughput
- **Latency:** how long *one* request takes. This is what a user feels.
- **Throughput:** how many requests the system *completes* per second.
- **Capacity:** the maximum throughput you can sustain while still meeting your latency SLO.

They're linked through **queueing**. At low load, latency is flat. As a resource gets close to 100% busy, requests wait behind each other and latency shoots up. For a simple single-server queue, the waiting factor grows like `ρ / (1 - ρ)`, where ρ is utilization:

| Utilization | Relative queueing delay |
|---|---|
| 50% | 1x |
| 80% | 4x |
| 90% | 9x |
| 95% | 19x |

```text
latency
  ^                                   |
  |                                  /
  |                                /      <- the "knee": small load increase,
  |                           __--          huge latency increase
  |______________________----
  +---------------------------------------> utilization
  0%          50%        70%   85%   100%
```
That's why capacity plans aim for **60-70% utilization** at peak, not 95%.

## Percentiles, not averages
p50 is the median. p99 means 99% of requests are faster than this value. Averages hide the tail: 99 requests at 50 ms plus one at 10 s average to 150 ms, which looks fine, while one user in a hundred waits 10 seconds. Your heaviest users (big carts, many orders) often *live* in the tail.

Two rules:
1. **You cannot average percentiles** across hosts or time windows. Aggregate **histograms** (Prometheus buckets), then compute the percentile.
2. Track the **latency of failures** separately. Fast 500s pull latency graphs down.

## Tail latency gets worse with fan-out
If a page calls 100 backends in parallel and each has a 1% chance of being slow, the page is slow whenever *any* of them is: `1 - 0.99^100 ≈ 63%` of page loads. That's the core idea of Dean and Barroso's *The Tail at Scale*. Mitigations: reduce fan-out, set tight timeouts with partial results, send **hedged requests** (a second copy after the p95 time), and make each backend's tail tighter.

## Little's Law: your most useful formula
```text
L = λ × W
in-flight work = arrival rate × time each item spends in the system
```
It holds for any stable system, whatever the arrival or service distribution.

**Example 1: threads.** 500 req/s, each taking 200 ms, means 500 × 0.2 = **100 requests in flight**. A blocking servlet stack needs about 100 busy threads; with headroom, 150. If a dependency slows down and W becomes 2 s, you'd need **1,000** threads. That's how a slow dependency exhausts Tomcat's default 200.

**Example 2: DB pool.** 500 req/s, each holding a connection for 20 ms, means **10 connections** busy on average. Add an 800 ms HTTP call inside the transaction and each request holds the connection ~820 ms: 500 × 0.82 = **410 connections**. No pool survives that. That's the maths behind "no remote calls inside transactions".

**Example 3: consumer sizing.** Kafka delivers 2,000 msg/s and each takes 15 ms to process, so about 30 must be in progress at once. 6 partitions with single-threaded consumers can't keep up (6 / 0.015 = 400 msg/s max), so lag grows without bound.

## Trade-offs to name in interviews
- **Batching** raises throughput but adds latency (wait to fill a batch). Use it for imports, Kafka producers (`linger.ms`) and JDBC batches.
- **GC choice:** Parallel GC maximises throughput but has longer pauses. ZGC keeps pauses tiny but costs some CPU.
- **More threads** help while you're waiting on I/O and hurt when you're CPU-bound (context switching).
- **Caching** cuts latency but adds staleness and invalidation complexity.

## How to talk about performance
1. Define the goal as a percentile at a load: "p99 < 300 ms at 1,500 RPS".
2. Measure the baseline under realistic load.
3. Find the bottleneck (profile, USE method), fix the **biggest** item, re-measure.
4. Stop when you meet the goal. Optimising past the SLO is usually wasted effort.
"""),

("JVM Memory and Garbage Collection", r"""
## Where memory goes
```text
+-------------------- Java process (container limit) --------------------+
| Heap (-Xmx)                                        | Non-heap            |
|  Young gen: Eden | S0 | S1   ->   Old gen          |  Metaspace (classes)|
|  (new objects)       (survivors)  (long-lived)     |  Thread stacks      |
|                                                    |  Code cache (JIT)   |
|                                                    |  Direct buffers     |
+--------------------------------------------------------------------------+
```
The **generational hypothesis**: most objects die young. Minor GCs copy the few survivors out of Eden, which is cheap when almost everything is garbage. Objects that survive several cycles are **promoted** to old gen, which is collected less often and costs more to collect.

Remember the non-heap part: each platform thread reserves a stack (often ~1 MB of address space), Netty uses direct buffers, and class-heavy frameworks fill metaspace. **Container OOMKills usually come from this part.**

## The collectors you should know
| Collector | Strategy | Pick it when |
|---|---|---|
| **Serial** | Single-threaded, stop-the-world | Tiny heaps, or the JVM's own choice in small containers |
| **Parallel** | Multi-threaded STW, maximises throughput | Batch jobs where pauses don't matter |
| **G1** (default since JDK 9) | Heap split into regions; young + *mixed* collections; concurrent marking; aims for a pause target (`MaxGCPauseMillis`, default 200 ms) | Most services, heaps ~2-32 GB |
| **ZGC** | Concurrent marking *and* relocation; pauses typically under a millisecond, regardless of heap size | Latency-sensitive services, large heaps; costs some CPU and throughput |

ZGC versions matter: on **JDK 21** turn on generational mode with `-XX:+UseZGC -XX:+ZGenerational`. Generational became the default in JDK 23 (JEP 474), and the old non-generational mode was removed in JDK 24 (JEP 490).

**G1 terms worth knowing:** *humongous objects* (bigger than half a region) are allocated straight into old gen and fragment the heap, so a 20 MB `byte[]` per request hurts. An *evacuation failure / to-space exhausted* means G1 ran out of room to copy survivors. A **Full GC in G1** is a red flag: the heap is too small or the allocation rate too high.

## Container sizing gotchas
- The JVM is container-aware, but the **default `MaxRAMPercentage` is 25%**. A 4 GB pod gets a 1 GB heap unless you set it. Use `-XX:MaxRAMPercentage=70` to `75`, leaving room for non-heap memory.
- If the container has **fewer than 2 CPUs or less than ~1.8 GB of memory**, JVM ergonomics quietly pick **SerialGC**. Set the collector explicitly.
- Setting `-Xms` equal to `-Xmx` (or `InitialRAMPercentage` equal to the max) avoids resize pauses and shows memory problems at startup instead of at 3 a.m.

## Reading GC logs
Turn them on with `-Xlog:gc*:file=/logs/gc.log:time,uptime:filecount=5,filesize=20M`. Check:
- **Pause times** (p99 and max) and **frequency**. A pause every 2 seconds means a high allocation rate.
- **Heap after GC**: a rising floor means a leak or growing live set.
- Words like `Full`, `to-space exhausted`, `Humongous`, `Allocation Failure` storms.
- **GC CPU share**: more than ~5-10% of CPU spent in GC deserves attention.

```text
[2026-10-09T14:05:01.120+0000][gc] GC(812) Pause Young (Normal) (G1 Evacuation Pause) 3021M->1180M(4096M) 18.402ms
[2026-10-09T14:05:44.871+0000][gc] GC(823) Pause Full (G1 Compaction Pause) 4090M->3950M(4096M) 2843.112ms   <- trouble
```
The second line says the heap is almost full of **live** data (3950M left after a full compaction). That's a leak or an undersized heap, not a tuning problem.

## A tuning procedure that works
1. **Measure first**: GC logs plus latency percentiles under realistic load.
2. **Right-size the heap**: a common starting point is 3-4x the live set (heap after a full GC).
3. **Reduce the allocation rate**: this is the biggest lever, and it's code work. Use an allocation profile (`asprof -e alloc` or JFR) to find the top allocators.
4. **Choose the collector** for the goal: G1 by default, ZGC for strict tail latency, Parallel for batch.
5. Only then touch flags such as `MaxGCPauseMillis`, one at a time, measuring each change.

Avoid cargo-cult flags copied from a 2014 blog post. Modern collectors' defaults are good.

## Allocation reduction patterns
```java
// Load-everything: allocates a 2M-entity list and fills the persistence context
List<Order> all = orderRepo.findAll();

// Stream in pages or use a forward-only cursor, keep the memory footprint flat
try (Stream<OrderRow> rows = jdbcTemplate.queryForStream(
        "SELECT id, total FROM orders WHERE created_at >= ?",
        (rs, i) -> new OrderRow(rs.getLong(1), rs.getBigDecimal(2)), since)) {
    rows.forEach(exporter::write);
}
```
Other wins: reuse one thread-safe `ObjectMapper`; avoid boxing in hot loops (`long` not `Long`); don't build log strings when the level is off; return DTO projections instead of full entity graphs; set an initial capacity for big collections. (With MySQL Connector/J, a JDBC fetch size of `Integer.MIN_VALUE` or `useCursorFetch=true` is needed to truly stream large result sets.)
"""),

("Profiling Java: Finding Where Time Goes", r"""
## Measure, don't guess
Engineers are bad at guessing hotspots. The slow part is rarely the code you suspect. A profiler shows reality in minutes. Your options:
- **async-profiler**: low overhead, no safepoint bias, flame graphs. Modes: `cpu`, `wall`, `alloc`, `lock`.
- **JDK Flight Recorder + Mission Control**: built in, ~1-2% overhead, can run continuously in production.
- **IntelliJ Profiler**: wraps async-profiler and JFR for local work.

## Pick the right profiling mode
| Question | Mode | Why |
|---|---|---|
| Where is CPU burned? | `cpu` | Samples threads that are on-CPU |
| Why is it slow when CPU is idle? | `wall` | Samples all threads, including waiting ones (locks, sockets, pools) |
| Why is GC busy? | `alloc` | Shows the call stacks allocating the most bytes |
| Are threads fighting over locks? | `lock` | Contended monitors and `j.u.c` locks |

## Reading a flame graph
```text
|                          JsonSerializer.serialize (38%)           | Pattern.compile (22%) |
|                     OrderMapper.toDto (41%)                       | Validator.check (24%) |
|                              OrderController.list (68%)                                   |
|                                   DispatcherServlet.doDispatch (90%)                      |
```
- **Width** is the share of samples. **Order left to right is alphabetical, not time.**
- Read **upward**: a frame's parent is below it.
- Look for **wide frames with nothing above them**: they're consuming time themselves. Here, `Pattern.compile` at 22% stands out. Someone compiles a regex on every request.

## The usual hotspots and their fixes
```java
// 1. Regex compiled per call
boolean ok = input.matches("[A-Z]{3}-\\d{6}");          // compiles every time
private static final Pattern SKU = Pattern.compile("[A-Z]{3}-\\d{6}");
boolean ok2 = SKU.matcher(input).matches();               // compile once

// 2. ObjectMapper per request (expensive to build, thread-safe to share)
new ObjectMapper().writeValueAsString(dto);               // inject the Spring-managed one

// 3. Exceptions for control flow (stack trace capture is costly)
try { return Integer.parseInt(s); } catch (NumberFormatException e) { return -1; }   // in a hot loop

// 4. Logging cost when the level is off
log.debug("cart=" + cart.toDetailedString());             // builds the string anyway
log.debug("cart={}", cart);                               // cheap when DEBUG is off
```
Other frequent findings: `synchronized` on a hot shared path; heavy reflection in mapping libraries; Hibernate dirty-checking thousands of managed entities on flush; `String +=` inside loops; serialising huge object graphs (entities with lazy collections); `SecureRandom` or `UUID.randomUUID()` contention under extreme rates.

## A disciplined profiling loop
```text
reproduce under realistic load -> profile 30-60 s -> fix the single widest item
        ^                                                      |
        +--------------- re-measure p99 & throughput <---------+
```
Profile under **load**, not one request in a quiet JVM: the JIT, caches and contention behave differently. Always compare against a baseline. Some "optimisations" make things slower.

## Microbenchmarks: why naive timing lies
```java
long t = System.nanoTime();
for (int i = 0; i < 1_000_000; i++) compute(i);      // JIT may remove unused results entirely,
System.out.println(System.nanoTime() - t);           // and the first runs are interpreted (cold)
```
Problems: JIT warm-up, **dead-code elimination** (an unused result is removed), constant folding, on-stack replacement, GC noise. Use **JMH**:
```java
@State(Scope.Benchmark)
@Warmup(iterations = 3) @Measurement(iterations = 5) @Fork(1)
public class SkuBench {
    String input = "ABC-123456";
    @Benchmark public boolean precompiled() { return SKU.matcher(input).matches(); }
    @Benchmark public boolean adHoc()       { return input.matches("[A-Z]{3}-\\d{6}"); }
}
```
JMH handles forking, warm-up and blackholes. Even so, a microbenchmark proves a micro-fact. Confirm the end-to-end effect with a load test.

## What to say in an interview
"I'd reproduce the slowness under load, take a CPU flame graph (or a wall-clock one if CPU is low), fix the widest frame, and re-measure p99. I'd only reach for JVM flags after the GC log and an allocation profile point there." That shows a method, which is what interviewers grade.
"""),

("MySQL Query Performance: EXPLAIN and Index Design", r"""
## How InnoDB finds rows
InnoDB stores each table as a **clustered B+tree ordered by the primary key**. Leaf pages hold whole rows. A **secondary index** is another B+tree whose leaves hold the indexed columns **plus the primary key**. A lookup through a secondary index therefore usually needs a second descent into the clustered index for the rest of the row, unless the index already contains every column the query needs. That case is a **covering index**.

## Reading EXPLAIN
| Column | What to look for |
|---|---|
| `type` | Best to worst: `const`/`eq_ref` (single row), `ref` (index equality), `range`, `index` (full index scan), **`ALL` (full table scan)** |
| `key` | The index actually chosen (`possible_keys` is just the candidates) |
| `key_len` | How many bytes, and so how many leading columns, of a composite index are used |
| `rows` × `filtered` | Estimated rows examined and the share surviving the WHERE |
| `Extra` | `Using index` = covering; `Using index condition` = index condition pushdown; **`Using filesort`**, **`Using temporary`** = extra sorting or grouping work |

`EXPLAIN ANALYZE` (MySQL 8.0.18+) **runs** the query and prints actual times and row counts per step. Use it to find where estimates and reality differ.

## Worked example
```sql
-- "My orders" page: 40M rows, ~600 orders for a typical user
SELECT id, status, total, created_at
FROM orders
WHERE user_id = ? AND status = 'DELIVERED'
ORDER BY created_at DESC
LIMIT 20;
```
With only an index on `user_id`, EXPLAIN shows `type=ref, key=idx_user, rows=600, Extra: Using where; Using filesort`. It reads all of the user's orders, filters them and sorts. Fine for most users, terrible for a seller account with 2M rows.
```sql
CREATE INDEX idx_user_status_created ON orders (user_id, status, created_at);
```
Now it's `type=ref, key=idx_user_status_created, Extra: Backward index scan`. It walks the index already in order and stops after 20 rows, with no filesort. Add `total` to the end of the index and it becomes **covering** (`Using index`): no clustered-index lookups at all.

## Composite index rules
1. **Equality columns first, then the range or ORDER BY column.** `(user_id, status, created_at)` serves `user_id = ? AND status = ? ORDER BY created_at`.
2. **Leftmost prefix:** that index also serves `WHERE user_id = ?`, but **not** `WHERE status = ?` alone.
3. **The index stops being used for seeking after the first range column.** With `(user_id, created_at, status)` and a range on `created_at`, `status` can only be filtered (index condition pushdown), not used to seek.
4. **Covering** indexes remove the row lookup, which is great for hot, narrow queries. Don't index every column, though: each index costs writes, memory and disk.

## Things that silently disable an index
```sql
WHERE DATE(created_at) = '2026-10-09'       -- function on the column
  -> WHERE created_at >= '2026-10-09' AND created_at < '2026-10-10'
WHERE phone = 9876543210                    -- VARCHAR column vs number: implicit cast, full scan
WHERE name LIKE '%raj%'                     -- leading wildcard (use full-text search)
WHERE user_id = ? OR email = ?              -- OR across columns (consider UNION)
WHERE status != 'DELETED'                   -- low selectivity: the optimiser picks a scan
ORDER BY created_at DESC, id ASC            -- mixed directions need a matching index (8.0 supports DESC)
```
Also: an index on a low-cardinality column alone (`is_active`) rarely helps. Collation or charset mismatches on JOIN columns can prevent index use.

## Finding the queries worth fixing
```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.5;           -- seconds
-- Top statements by total time, from performance_schema via the sys schema:
SELECT query, exec_count, total_latency, avg_latency, rows_examined_avg
FROM sys.statement_analysis ORDER BY total_latency DESC LIMIT 10;
```
Rank by **total time** (frequency × average), not just the slowest single query. A 5 ms query run 2,000 times a second matters more than a 3 s nightly report. `pt-query-digest` summarises slow logs the same way. `sys.schema_unused_indexes` finds indexes you're paying for but never use.

## Interview checklist for "this query is slow"
EXPLAIN it -> check the access type and rows examined -> check the predicate for index killers -> design a composite index (equality, then range or sort, maybe covering) -> verify with EXPLAIN ANALYZE -> think about write cost and data skew -> consider pagination or caching only if indexing isn't enough.
"""),

("Application-to-Database Performance: N+1, Batching, Pools and Replicas", r"""
## The N+1 problem
```java
List<Order> orders = orderRepo.findByUserId(userId);      // 1 query
for (Order o : orders) {
    total += o.getItems().size();                          // +1 lazy query per order
}
```
50 orders means 51 round trips. Each is fast, so nobody notices in development, but in production it's 50 x 2 ms plus pool pressure. It also scales with data.

**Detect it:**
- Traces showing dozens of identical `SELECT ... FROM order_items WHERE order_id=?` spans.
- `spring.jpa.properties.hibernate.generate_statistics=true` in tests (it logs the statement count per session).
- Assert the query count in tests with a datasource proxy.

**Fix it:**
```java
@Query("select distinct o from Order o join fetch o.items where o.user.id = :uid")
List<Order> findWithItems(@Param("uid") Long uid);

@EntityGraph(attributePaths = {"items"})
List<Order> findByUserId(Long userId);
```
Or set `hibernate.default_batch_fetch_size=50`, which loads lazy collections with `IN (...)` in batches. Often the best fix is a **DTO projection** that selects only the columns the screen needs.

**Pitfall:** `JOIN FETCH` of a collection combined with pagination makes Hibernate paginate **in memory** (warning HHH90003004). Page the IDs first, then fetch those entities with their collections.

## Batch writes
Inserting 1M rows one at a time means 1M round trips. To batch with JPA:
```text
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
spring.datasource.url=jdbc:mysql://db/shop?rewriteBatchedStatements=true
```
**Gotcha:** `GenerationType.IDENTITY` (AUTO_INCREMENT) **disables Hibernate insert batching**, because Hibernate needs each generated ID right away. For bulk loads, use `JdbcTemplate.batchUpdate` (or app-generated IDs):
```java
jdbcTemplate.batchUpdate(
    "INSERT INTO order_events (order_id, type, created_at) VALUES (?, ?, ?)",
    events, 1000,
    (ps, e) -> { ps.setLong(1, e.orderId()); ps.setString(2, e.type()); ps.setObject(3, e.at()); });
```
With JPA batch jobs, call `entityManager.flush(); entityManager.clear();` every N rows so the persistence context doesn't grow without bound. Commit in chunks (1,000-5,000 rows) to keep transactions and locks short.

## Connection pools (HikariCP)
- **Bigger isn't better.** A database can only run as many queries in parallel as it has cores and I/O. HikariCP's pool-sizing guide starts from `connections = cores × 2 + effective spindles`, and their benchmarks show response times *improve* when an oversized pool is shrunk.
- **Do the fleet maths:** 40 pods × 20 connections = 800 connections into a 16-core MySQL. Too many. Smaller per-pod pools, or a proxy (ProxySQL / RDS Proxy), keep the total sane.
- **Use Little's law:** connections needed ≈ queries/s × average hold time. Hold time is the lever: short transactions, no remote calls inside.
- **Settings:** `connectionTimeout` 2-5 s (fail fast instead of the 30 s default), `maxLifetime` a little below the DB's or network's idle-kill time, and alerts on `hikaricp_connections_pending`.

## Read replicas
Send read-only traffic (reports, listing pages) to replicas to take load off the primary:
```java
@Transactional(readOnly = true)    // routed to a replica by an AbstractRoutingDataSource
public Page<OrderView> history(Long userId, Pageable p) { ... }
```
(Wrap the routing datasource in `LazyConnectionDataSourceProxy` so the read-only flag is known before a connection is picked.)

**The catch is replication lag.** A user updates their address and the next page, read from a replica 2 seconds behind, shows the old one. Options:
- **Read-your-writes:** route that user's reads to the primary for N seconds after a write (a session flag or cookie).
- Critical reads (balances, inventory checks before payment) **always go to the primary**.
- Monitor lag (`Seconds_Behind_Source` or heartbeat tables) and pull lagging replicas out of rotation.

## Fewer round trips, smaller results
- `SELECT *` from wide tables wastes I/O and memory. Select the columns you need.
- Push work to the DB when it's set-based: one `UPDATE ... WHERE` instead of load-modify-save loops.
- Replace "query in a loop" with `WHERE id IN (...)` (in chunks of ~500-1,000).

```text
Request budget 300 ms:  [auth 5][load cart 4 queries x 2ms][price 25][payment 180][save 3 queries]
                         ^ the DB is rarely the whole story: measure each part
```
"""),

("Caching Strategy and Pitfalls", r"""
## Where caches live, and rough costs
| Layer | Typical latency | Example |
|---|---|---|
| In-process (Caffeine) | ~0.1-1 µs | Config, product details, rate-limit buckets |
| Distributed (Redis) | ~0.3-1 ms in the same DC | Sessions, shared hot objects |
| Database (indexed query) | ~1-10 ms | Source of truth |
| CDN / HTTP cache | Served at the edge | Images, static JSON, public pages |

A two-level setup (**L1 Caffeine with a short TTL in front of L2 Redis**) handles hot keys and Redis blips well.

## Patterns
| Pattern | How | Notes |
|---|---|---|
| **Cache-aside** | App reads cache; on a miss, loads from DB and populates | Most common; app owns the logic |
| Read-through | Cache library loads on a miss | Caffeine `LoadingCache`, Spring `@Cacheable` |
| Write-through | Write goes to the cache and DB synchronously | Fresh cache, slower writes |
| Write-behind | Write to the cache, flush to DB asynchronously | Fast, but a crash can lose data |

```java
@Cacheable(cacheNames = "product", key = "#id", sync = true)   // sync=true: one loader per key per JVM
public ProductView getProduct(long id) { return mapper.toView(repo.findById(id).orElseThrow()); }

@CacheEvict(cacheNames = "product", key = "#cmd.id()")
@Transactional
public void updateProduct(UpdateProduct cmd) { ... }
```
Gotchas: `@Cacheable` goes through a proxy, so **self-invocation skips the cache**. Cache **DTOs**, not JPA entities with lazy proxies. Set TTLs explicitly per cache (`RedisCacheConfiguration.entryTtl`).

## Pitfall 1: the stale-data race in cache-aside
```text
T1 (reader)                       T2 (writer)
read cache: MISS
read DB: price=100
                                  UPDATE price=120; COMMIT
                                  DELETE cache key
SET cache price=100   <-- stale value written AFTER the delete; stays until the TTL
```
**Mitigations:**
- Always **update the DB, then delete the key**, and delete *after commit* (`@TransactionalEventListener(phase = AFTER_COMMIT)`). Deleting before the commit lets readers reload the old row.
- Always set a **TTL** as a safety net.
- **Versioned writes:** store `{version, value}` and only overwrite with a newer version.
- A **delayed second delete** (delete again ~1 s later).
- **CDC-driven invalidation** (Debezium reads the binlog and evicts keys) for strong guarantees.
- For truly critical data (balance, stock at payment time), **don't trust the cache**. Read the DB.

## Pitfall 2: stampede (thundering herd)
A hot key expires and 5,000 concurrent requests all miss and hit the DB.
- **Single-flight:** one loader per key. `sync = true` or Caffeine `get(key, loader)` per JVM. Across JVMs, a short Redis lock (`SET lock:k 1 NX PX 3000`) while the others briefly wait or serve stale data.
- **Early refresh:** refresh in the background before expiry (soft TTL), or the probabilistic "XFetch" approach where a request occasionally refreshes early as expiry gets close.
- **Serve stale while revalidating.**

## Pitfall 3: synchronized expiry
Keys loaded together (warm-up, nightly job) with the same TTL expire together. Add **jitter**: `ttl = base + random(0, 10% of base)`.

## Pitfall 4: hot keys
One celebrity product or flash-sale item sends 100k reads/s to a single Redis shard, which saturates while the others sit idle.
- **L1 in-process cache** with a 1-5 s TTL absorbs most reads.
- **Key replication:** write `product:42#0..#9` and have readers pick a random suffix.
- Read from Redis replicas. Detect with `redis-cli --hotkeys` (LFU policy) or client-side metrics.

## Pitfall 5: penetration and negative caching
Requests for IDs that don't exist always miss and go to the DB, a favourite of scrapers and attackers. **Cache "not found"** with a short TTL (30-60 s), validate IDs early, and use a Bloom filter for huge keyspaces.

## Pitfall 6: memory and eviction
Set `maxmemory` and an eviction policy (`allkeys-lru` or `allkeys-lfu` for pure caches). Watch evictions, big values (over 100 KB values slow everything; compress or split them) and serialisation CPU. Never use `KEYS *` in production; use `SCAN`.

## When to cache, and when not to
Cache when data is **read-heavy, expensive to produce and tolerant of some staleness**. Avoid caching data that changes on every read, per-user data with a near-zero hit rate, or values where staleness causes real harm (inventory at checkout, permissions right after revocation, unless you have explicit invalidation). Track the **hit ratio, load latency, evictions and DB load**. A cache with a 20% hit ratio adds complexity and cost for little benefit.
"""),

("API and HTTP Performance", r"""
## Send less
- **Compression:** `server.compression.enabled=true` (plus `server.compression.min-response-size=2KB`) gzips JSON. A 1 MB list often drops to about 100 KB, which makes a big difference on mobile networks.
- **Don't serialise entities.** Return DTOs with the fields the client needs. Entities pull lazy collections, cause N+1 queries during serialisation, and leak internal fields.
- **Paginate everything that can grow**, and cap page sizes (`size <= 100`).

## Pagination: offset vs keyset
```sql
-- Offset: MySQL reads and throws away 100,000 rows to return 20. Gets slower with every page.
SELECT id, title FROM posts ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 100000;

-- Keyset (seek): start right after the last row of the previous page. Same cost on every page.
SELECT id, title FROM posts
WHERE (created_at, id) < (:lastCreatedAt, :lastId)
ORDER BY created_at DESC, id DESC
LIMIT 20;                       -- index on (created_at, id)
```
Keyset also avoids duplicates or skipped rows when new rows arrive between page loads. The trade-off: no "jump to page 500", which suits infinite scroll and APIs that hand back a `nextCursor`. Row-constructor comparisons can be planned poorly on some MySQL versions; the expanded form `created_at < ? OR (created_at = ? AND id < ?)` always works. Check with EXPLAIN.

## Reuse connections
A new TCP plus TLS handshake per call costs 1-3 round trips, which adds up fast. Use **pooled, keep-alive HTTP clients** and **one shared client per downstream**, not a new client per request. Know your client's pool limits: Apache HttpClient's classic pooling manager allows only **5 connections per route** by default, so outbound concurrency to a single host silently queues. Expose and alert on client pool metrics.

## Timeouts and deadlines
Every remote call gets a **connect timeout** (~200-500 ms in a data centre) and a **read timeout** based on the dependency's real latency (around p99.9 plus margin). Then think in **budgets**: if your SLO is 800 ms and you call three services in sequence, each can't take 2 s. Pass the remaining deadline downstream (a header or gRPC deadline) so callees stop working on requests nobody is waiting for.

## Parallelise independent calls
```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class DashboardFanOut {
    record Dashboard(String profile, int orders, String offer) {}

    static <T> T call(T value, long millis) {          // stands in for a remote call
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        }
        return value;
    }

    public static void main(String[] args) {
        try (ExecutorService io = Executors.newVirtualThreadPerTaskExecutor()) {
            long start = System.nanoTime();
            var profile = CompletableFuture.supplyAsync(() -> call("Raj", 300), io);
            var orders  = CompletableFuture.supplyAsync(() -> call(7, 300), io);
            var offer   = CompletableFuture.supplyAsync(() -> call("10% off", 400), io)
                    .completeOnTimeout("no offer", 350, TimeUnit.MILLISECONDS);   // optional: degrade
            CompletableFuture.allOf(profile, orders, offer).orTimeout(1, TimeUnit.SECONDS).join();
            var d = new Dashboard(profile.join(), orders.join(), offer.join());
            System.out.println(d + " in " + (System.nanoTime() - start) / 1_000_000 + " ms");  // ~400, not 1,000
        }
    }
}
```
Points to mention: use a **dedicated executor** (the default `ForkJoinPool.commonPool()` is sized for CPU work and shared by everything), give each call a timeout, and **degrade** optional parts instead of failing the whole response.

## Virtual threads (Java 21)
`spring.threads.virtual.enabled=true` runs Tomcat requests and `@Async` tasks on virtual threads. **Benefit:** blocking I/O no longer ties up a scarce OS thread, so an I/O-bound service handles far more concurrent requests with simple blocking code. **Not a speed-up for CPU-bound work**, and **the downstream limits don't move**: 10,000 virtual threads still share a 20-connection DB pool, so add semaphores or bulkheads. On JDK 21-23, blocking inside `synchronized` **pins** the carrier thread (prefer `ReentrantLock` there). JDK 24's JEP 491 removed most of that pinning.

## Async for long work
If a request triggers work that takes more than a couple of seconds (report generation, bulk import), don't hold the connection open. Return **202 Accepted** with a job ID, process the work through a queue, and let the client poll `GET /jobs/{id}` or receive a webhook.

## HTTP caching
For read-mostly resources, send `ETag` and `Cache-Control`. Clients send `If-None-Match` and get a **304 Not Modified** with no body. Spring's `ShallowEtagHeaderFilter` saves bandwidth but still computes the response; a real ETag computed from a version column saves the work too. Public, non-personal data can sit on a CDN.

## Checklist for "this endpoint is slow"
Trace it -> how many DB queries and remote calls? -> sequential calls that could run in parallel? -> payload size and compression? -> N+1 during serialisation? -> missing index? -> client pool or timeout limits? -> can any part be cached or done asynchronously?
"""),

("Load Testing and Capacity Math", r"""
## Types of tests
| Test | Question | Shape |
|---|---|---|
| **Load** | Do we meet the SLO at expected peak? | Ramp to peak, hold 15-30 min |
| **Stress / breakpoint** | Where and how do we break? | Keep increasing until errors or the SLO breaks |
| **Spike** | Can we absorb a sudden 5-10x burst (sale starts, push notification)? | Instant jump |
| **Soak** | Leaks, slow degradation, connection churn? | Moderate load for 4-24 h |

## Tools
- **k6**: JavaScript scripts, CLI-first, built-in thresholds that work as CI gates.
- **Gatling**: Java/Scala/Kotlin DSL, efficient, good HTML reports, open injection models.
- **JMeter**: GUI plus many plugins. Common in enterprises; run it headless (`-n`) for real tests.

```javascript
// k6: open model (arrival rate), with SLO thresholds that fail the run
import http from 'k6/http';
import { check } from 'k6';
export const options = {
  scenarios: {
    checkout: { executor: 'constant-arrival-rate', rate: 500, timeUnit: '1s',
                duration: '20m', preAllocatedVUs: 200, maxVUs: 2000 },
  },
  thresholds: { http_req_failed: ['rate<0.01'], http_req_duration: ['p(99)<400'] },
};
export default function () {
  const res = http.post(`${__ENV.BASE}/api/checkout`, JSON.stringify({ cartId: `c-${__VU}-${__ITER}` }),
                        { headers: { 'Content-Type': 'application/json', 'Idempotency-Key': `${__VU}-${__ITER}` } });
  check(res, { 'status 200': (r) => r.status === 200 });
}
```

## Open vs closed models and coordinated omission
A **closed** model (N virtual users, each waiting for a response before sending the next request) **slows down when the system slows down**. When the server stalls for 2 s, the tool simply stops sending, so the stall barely shows up in the latency numbers. Gil Tene calls this **coordinated omission**. Real users don't politely wait for each other. Use an **open model** (constant arrival rate: k6 `constant-arrival-rate`, Gatling `constantUsersPerSec`, wrk2) for user-facing APIs, and treat latency reports from closed-loop tools with suspicion.

## Making results trustworthy
- **Production-like data volume.** Indexes that look fine on 10k rows fail at 50M.
- **Realistic mix** of endpoints and payloads, real key distribution (hot products), varied users (avoid one cached user).
- **Warm up** the JVM (JIT) before measuring, **and** run once with a **cold cache** to see the worst case.
- **Watch the system under test**: CPU, GC, pools, DB, using the USE method. Find the *bottleneck*, not just the numbers.
- Make sure the **load generator isn't the bottleneck** (its CPU, network, open-file limits).
- Mock or sandbox third parties such as payment gateways. Don't load-test a partner by accident.

## Reading results: find the knee
Plot throughput and p99 against offered load. Throughput rises linearly, then flattens. Latency stays flat, then curves upward. **Sustainable capacity** is the highest load where p99 still meets the SLO with resources around 70% busy, not the point where errors start.

## Capacity math worked example
```text
Traffic:   30M checkout-related API calls/day  -> average 30M / 86,400 ≈ 350 RPS
Peak:      daily peak ≈ 4x average             -> 1,400 RPS
Sale:      flash sale ≈ 3x the daily peak      -> 4,200 RPS target
Per pod:   load test: 250 RPS at p99 < 300 ms with CPU ~70%
Pods:      4,200 / 250 = 17 pods
Headroom:  +30% for bursts and deploys         -> 22 pods
AZ loss:   must survive losing 1 of 3 AZs      -> 22 × 3/2 = 33 pods during the sale
DB conns:  Little: 4,200 RPS × 8 ms hold time  -> ~34 connections busy on average
           33 pods × pool 10 = 330 max         -> shrink pools to ~4 per pod or add a proxy
Redis:     3 GETs per request = 12,600 ops/s   -> well within one shard, watch hot keys
```
Say your assumptions out loud, round the numbers, and **validate them with a load test**. Interviewers care more about the method and the sanity checks (connections, hot keys, AZ failure) than exact numbers.

## Before a big sale: a checklist
Load test at 1.5x the forecast. Pre-scale (autoscalers react in minutes, too slow for a spike). Warm the caches. Raise rate limits deliberately. Freeze deploys. Prepare kill switches for non-critical features (recommendations, reviews). Rehearse the runbook. Have dashboards and on-call ready.
"""),
]

QA = [
("Why do we track p99 latency instead of the average?", r"""
**Averages hide the tail.** 99 requests at 50 ms and one at 10 s average about 150 ms, which looks healthy, while 1 in 100 users waits 10 seconds. Percentiles describe what users actually experience:
- **p50**: the typical experience.
- **p95/p99**: the slow experiences that drive complaints and abandonment.
- **p99.9**: very important at scale (1M requests means 1,000 terrible ones).

**Why the tail matters more than it seems:**
1. **Fan-out amplifies it.** A page calling 100 services, each slow 1% of the time, is slow on about 63% of loads (`1 - 0.99^100`).
2. **Heavy users live in the tail:** the biggest carts, the most orders, the biggest customers.
3. **The tail warns of saturation early:** queues show up in p99 before they show up in p50.

**Practical rules:**
- Compute percentiles from **histograms** aggregated across instances. You can't average p99s.
- Track the latency of errors separately.
- Write SLOs as thresholds ("99% under 300 ms"), not averages.
""", B, ["latency", "percentiles", "metrics"], True),

("Explain Little's Law and use it to size a thread pool or connection pool.", r"""
**Little's Law:** `L = λ × W`. The average number of items in a system equals the arrival rate times the average time each item spends there. It holds for any stable system.

**Thread pool:** 800 req/s with 150 ms average latency gives `800 × 0.15 = 120` requests in flight. A blocking stack needs about 120 threads; with headroom for variance, ~160-180. Tomcat's default of 200 is fine **until latency changes**. If a dependency slows down and W becomes 1.5 s, you'd need 1,200 threads. That's why timeouts and bulkheads matter more than pool size.

**DB pool:** 800 req/s × 2 queries, each holding a connection 5 ms: `1,600 × 0.005 = 8` connections busy on average. A pool of 10-15 is plenty. Now put a 500 ms HTTP call inside the transaction: hold time becomes ~510 ms, and you need `800 × 0.51 ≈ 408` connections. **The fix is reducing W, not raising L.**

**Kafka:** 3,000 msg/s at 20 ms each gives 60 in-flight. With 12 single-threaded partitions you top out at 600 msg/s, so lag grows.

It's a great sanity check in system design and incident discussions.
""", I, ["littles-law", "capacity", "thread-pool"], True),

("What's the difference between latency and throughput? Can improving one hurt the other?", r"""
- **Latency:** time to complete one request (milliseconds).
- **Throughput:** requests completed per unit of time (RPS).

They're related through **queueing**: when throughput gets close to capacity, utilization nears 100%, queues form and latency rises sharply (the knee of the curve). So pushing for maximum throughput usually costs latency.

**Common trade-offs:**
- **Batching** (JDBC batches, Kafka `linger.ms`, bulk APIs) raises throughput a lot but adds per-item latency while a batch fills.
- **GC:** Parallel GC gives the best throughput with long pauses; ZGC gives tiny pauses but uses more CPU.
- **Concurrency:** more threads raise throughput for I/O-bound work until contention and context switching make both worse.
- **Compression:** less transfer time, more CPU.
- **Caching:** lowers latency and raises effective throughput, at the cost of freshness.

**In practice:** state which one the use case needs. User-facing APIs care about p99 latency at a target load. Batch and ETL jobs care about throughput (rows/hour). Then size for the target, keeping utilization around 60-70% so the latency curve stays flat.
""", B, ["latency", "throughput", "fundamentals"], False),

("Your API fans out to 10 backends in parallel. Why is its p99 worse than any single backend's p99, and what can you do?", r"""
The response is only as fast as the **slowest** of the 10 calls. If each backend is above its p99 1% of the time (independently), the chance that at least one is slow is `1 - 0.99^10 ≈ 9.6%`. Your p99 is set by the backends' **p99.9 territory**, not their p99. At 100 backends, ~63% of requests hit at least one slow call.

**Mitigations:**
1. **Reduce fan-out:** batch endpoints, denormalise, precompute or cache aggregated views.
2. **Timeouts with partial results:** for optional parts (recommendations, badges), wait up to a deadline and return without them.
3. **Hedged requests:** if a replica hasn't answered by its p95, send a second copy to another replica and take the first response. This removes much of the tail for a few percent extra load. Use it only for idempotent reads.
4. **Tighten each backend's tail:** GC tuning, avoiding head-of-line blocking, separating slow batch traffic from interactive traffic.
5. **Load-aware routing:** least-outstanding-requests instead of round robin, outlier ejection.

This is the main point of Dean and Barroso's "The Tail at Scale". Naming it shows depth.
""", A, ["tail-latency", "fan-out", "distributed"], False),

("Explain how G1 garbage collection works. When would you choose ZGC instead?", r"""
**G1 (default since JDK 9):**
- The heap is divided into equal **regions** (1-32 MB). Each region acts as Eden, Survivor, Old or Humongous.
- **Young collections** (stop-the-world, parallel) evacuate live objects from Eden and Survivor regions.
- **Concurrent marking** finds live data in old regions while the app runs, then **mixed collections** evacuate young regions plus the old regions with the most garbage ("garbage first").
- It sizes work to meet a pause **target** (`MaxGCPauseMillis`, default 200 ms). That's a goal, not a guarantee.
- Watch for: humongous allocations (objects bigger than half a region), evacuation failures, and **Full GCs** (a sign of an undersized heap or a high allocation rate).

**ZGC:** does marking *and* relocation **concurrently** using load barriers and coloured pointers. Pauses are typically **under 1 ms regardless of heap size**. On JDK 21 enable generational mode (`-XX:+UseZGC -XX:+ZGenerational`). It's the default ZGC mode from JDK 23.

**Choose ZGC** when tail latency is critical (trading, real-time APIs, p99.9 SLOs), heaps are large (tens of GB and up), and you have CPU headroom, since it trades some throughput and CPU for latency. **Stay on G1** for typical services with modest heaps. **Parallel GC** for batch jobs where only throughput matters.
""", I, ["jvm", "gc", "g1", "zgc"], True),

("GC pauses are causing p99 latency spikes. How do you investigate and fix them?", r"""
**1. Confirm it's GC:** line up the latency spikes with `jvm_gc_pause_seconds_max` or the GC log. If pauses don't match the spikes, look elsewhere (locks, downstreams).

**2. Read the GC log** (`-Xlog:gc*`):
- **Long young pauses:** a large young gen with many survivors, or a high allocation rate.
- **Full GC** in G1: the heap is too small or there's a leak. Check *heap after GC*. A rising floor means a leak, so fix the code, not the flags.
- **Humongous allocations:** big arrays (huge JSON buffers, big `byte[]`). Stream instead, or raise the region size.
- **To-space exhausted:** not enough free regions to evacuate into.

**3. Find who allocates:** `asprof -e alloc` or JFR allocation events. Typical findings: loading whole result sets, building large strings, boxing, mapping entities to DTOs repeatedly.

**4. Fix in priority order:**
1. **Cut allocation** (code changes): this helps every collector.
2. **Right-size the heap**: about 3-4x the live set; `Xms = Xmx`; in containers set `MaxRAMPercentage`.
3. **Switch collector** if the SLO needs it: generational ZGC for sub-ms pauses.
4. Then tune flags (`MaxGCPauseMillis`), one change at a time, measured under load.

Also check the container isn't CPU-throttled. Concurrent GC threads starved of CPU produce longer pauses.
""", A, ["jvm", "gc", "latency"], False),

("How do you size the Java heap for a service running in a Kubernetes container?", r"""
**Key facts:**
- The JVM is container-aware and reads cgroup limits, but the **default max heap is only 25%** of container memory (`MaxRAMPercentage=25`).
- The container limit covers **the whole process**: heap + metaspace + thread stacks + code cache + direct buffers + GC overhead. Exceed it and the kernel **OOMKills** the pod (exit 137) with no Java error.

**Practical recipe:**
1. Set `-XX:MaxRAMPercentage=70` to `75` (lower if the service uses lots of threads or Netty direct memory). Prefer percentages over a fixed `-Xmx`, so changing the pod's memory limit resizes the heap with it.
2. Set `InitialRAMPercentage` to the same value (like `Xms = Xmx`) to avoid resize pauses and catch problems at startup.
3. Set **memory request = limit** for predictable scheduling (Guaranteed QoS).
4. **Choose the GC explicitly.** In containers with under 2 CPUs or ~1.8 GB, the JVM falls back to SerialGC.
5. Validate with a load or soak test: watch heap after GC (live set), GC pause and CPU share, and total RSS against the limit. Use Native Memory Tracking if RSS grows beyond heap.

Rule of thumb: the heap should be about 3-4x the live set. Much bigger only makes individual collections longer, unless you use ZGC.
""", I, ["jvm", "kubernetes", "memory"], False),

("Walk me through reading an EXPLAIN plan for a slow MySQL query.", r"""
I go column by column, asking "how much work, and why?":

1. **`type`**, the access method: `const`/`eq_ref` (one row) > `ref` (index equality) > `range` > `index` (full index scan) > **`ALL`** (full table scan, usually the problem on a big table).
2. **`key`**: which index was actually chosen. If it's NULL or unexpected, compare with `possible_keys`.
3. **`key_len`**: how much of a composite index is used. A short `key_len` means only the leading column is used, so later columns aren't helping.
4. **`rows` × `filtered`**: estimated rows examined vs kept. 2M rows examined to return 20 is the smell.
5. **`Extra`**:
   - `Using index`: covering, which is good.
   - `Using index condition`: index condition pushdown, good.
   - `Using filesort` / `Using temporary`: extra sort or grouping work. Often fixable with an index that matches the ORDER BY or GROUP BY.
6. Then **`EXPLAIN ANALYZE`** (8.0.18+) to see **actual** rows and time per step. Big gaps between estimate and reality suggest stale statistics (`ANALYZE TABLE`) or skewed data.

Then I check the predicate for index killers (functions on columns, implicit casts, leading `%`), design the composite index (equality columns, then range or sort column, optionally covering), and re-run EXPLAIN to confirm.
""", I, ["mysql", "explain", "indexes"], True),

("Design an index for: SELECT id, total FROM orders WHERE user_id = ? AND status = ? ORDER BY created_at DESC LIMIT 20.", r"""
**Index:** `CREATE INDEX idx_orders_user_status_created ON orders (user_id, status, created_at);`

**Why this column order:**
1. `user_id` and `status` are **equality** predicates, so they go first. Together they narrow the scan to one contiguous slice of the index.
2. `created_at` comes next. Within that slice, entries are **already sorted** by `created_at`, so MySQL reads the slice **backwards** and **stops after 20 rows**. No filesort, no reading the user's whole history.
3. Putting `created_at` before `status` would break this: the range or sort column has to come after all the equality columns.

**Make it covering (optional):** `(user_id, status, created_at, total)`. `id` is the primary key, so every InnoDB secondary index already contains it. Now EXPLAIN shows `Using index` and no clustered-index lookups. Worth it for a hot query; skip it if `total` changes constantly or the index would get wide.

**Verify:** EXPLAIN should show `type=ref`, this `key`, no `Using filesort`, and `rows` close to 20 in EXPLAIN ANALYZE.

**Trade-offs:** each index slows inserts and updates and uses buffer-pool memory. If an `idx(user_id)` already exists, this new index makes it redundant (leftmost prefix), so drop it.
""", I, ["mysql", "indexes", "query-design"], True),

("What is a covering index, and when does it help?", r"""
In InnoDB, a secondary index leaf stores the **indexed columns plus the primary key**. A normal lookup finds matching entries in the secondary index, then goes into the **clustered index** (the table, ordered by PK) to fetch the rest of each row. That's one extra B+tree descent per row, often random I/O.

A **covering index** contains **every column the query needs** (SELECT, WHERE, ORDER BY), so MySQL answers from the index alone. EXPLAIN shows **`Using index`**.

```sql
-- Query
SELECT status, created_at FROM orders WHERE user_id = 42 ORDER BY created_at DESC LIMIT 20;
-- Covering index (PK id is included automatically)
CREATE INDEX idx_user_created_status ON orders (user_id, created_at, status);
```

**When it helps most:**
- Hot queries that read many rows (lists, counts, reports over ranges).
- Wide tables where fetching full rows is expensive.
- `COUNT(*)` with a filter, or existence checks.

**Costs:**
- Bigger indexes use more memory and disk.
- Every write to those columns updates the index too.

So cover the **few critical queries**, not everything, and keep indexed columns narrow. `SELECT *` can never be covered, which is another reason to select only the columns you need.
""", B, ["mysql", "indexes"], False),

("You added an index, but MySQL isn't using it. Why might that be?", r"""
**Query-side reasons:**
- A **function or expression on the column:** `WHERE DATE(created_at) = ?`, `WHERE LOWER(email) = ?`. Rewrite as a range, or use a functional index (8.0.13+).
- **Implicit type conversion:** a VARCHAR column compared to a number (`phone = 98765...`), or a JOIN on columns with different charsets or collations.
- **Leading wildcard:** `LIKE '%abc'`.
- **Leftmost prefix not satisfied:** the index is `(a, b)` but the query filters only on `b`.
- **`OR` across different columns** (sometimes index merge helps; otherwise rewrite as `UNION`).
- **ORDER BY** directions or columns that don't match the index.

**Optimiser-side reasons:**
- **Low selectivity:** if the predicate matches ~20-30%+ of rows, a full scan is genuinely cheaper than random lookups (`status = 'ACTIVE'`).
- **Stale or skewed statistics:** run `ANALYZE TABLE`. Data skew means one parameter value gets a different best plan.
- **Small table:** a scan is cheaper anyway.
- **A better index exists** for the combined predicate and ORDER BY.

**How to investigate:** EXPLAIN with **real** parameter values, `EXPLAIN ANALYZE`, `EXPLAIN FORMAT=JSON` for cost details, and the optimizer trace if needed. `FORCE INDEX` can confirm a hypothesis, but it's rarely the right permanent fix because data changes.
""", I, ["mysql", "indexes", "optimizer"], False),

("What is the N+1 query problem, and how do you detect and fix it in a Spring Boot app?", r"""
**What:** you load N parent entities with one query, then touching a lazy association on each fires one more query per parent: 1 + N round trips. With 200 orders and items that's 201 queries. Each is fast, but together they add latency, hold the connection and grow with data.

**Detect:**
- **Tests:** `hibernate.generate_statistics=true`, or a datasource proxy that asserts the query count per request.
- **Production:** traces showing many identical child-table spans; the slow log showing high-frequency identical statements.
- **Code smell:** a loop calling `getXxx()` on lazy collections, or **Jackson serialising entities** (lazy loads triggered during JSON rendering, especially with Open Session in View on).

**Fix:**
- `JOIN FETCH` in JPQL, or `@EntityGraph(attributePaths = "items")` on the repository method.
- `hibernate.default_batch_fetch_size=50` (or `@BatchSize`) loads lazy collections with `IN (...)`.
- **DTO projections** selecting only the needed columns, often the best option for read endpoints.

**Pitfalls:** fetch-joining several collections causes a cartesian explosion (or `MultipleBagFetchException`). Fetch-join plus pagination paginates in memory, so page IDs first, then fetch. Never switch associations to `EAGER` globally. That just moves the N+1 somewhere else.
""", B, ["jpa", "n-plus-one", "hibernate"], True),

("Inserting 1 million rows through Spring Data JPA takes 40 minutes. How do you speed it up?", r"""
**Why it's slow:** one `INSERT` round trip per row, and a persistence context holding a million managed entities (memory plus dirty-checking cost on each flush), possibly all in one huge transaction.

**Fixes, in order of impact:**
1. **Use JDBC batching:** `hibernate.jdbc.batch_size=500`, `order_inserts=true`, and `rewriteBatchedStatements=true` on the MySQL URL so the driver turns batches into multi-row `INSERT`s.
2. **Watch ID generation:** `GenerationType.IDENTITY` **disables Hibernate insert batching**. Use app-generated IDs, or skip JPA for the bulk path.
3. **Use `JdbcTemplate.batchUpdate`** for bulk loads. It's simpler and faster, with no entity overhead:
   `jdbcTemplate.batchUpdate(sql, rows, 1000, (ps, r) -> {...})`.
4. **Commit in chunks** of 1,000-5,000 rows. If you stay on JPA, call `flush()` and `clear()` each chunk so memory stays flat. Short transactions also avoid huge undo logs and long locks.
5. **Parallelise carefully:** a few worker threads with separate key ranges, but watch DB CPU and lock contention.
6. For huge one-off loads: `LOAD DATA INFILE`, temporarily deferring secondary index creation, or bulk tools.

Typical result: from about 1-2k rows/s to 30-100k rows/s. Measure before and after, and make the job restartable by tracking the last committed chunk.
""", I, ["jpa", "batching", "mysql"], False),

("Offset pagination gets very slow on page 5,000. Why, and how do you fix it?", r"""
**Why:** `LIMIT 20 OFFSET 100000` makes MySQL **read and discard 100,000 rows** (walking the index and often fetching full rows) to return 20. The cost grows linearly with the page number. Deep pages from crawlers or "export all" loops can overload the DB. Offset also shows **duplicates or skipped rows** when new rows are inserted between page loads.

**Fix: keyset (seek) pagination.** Remember the sort key of the last row and continue after it:
```sql
SELECT id, title, created_at FROM posts
WHERE (created_at < :lastCreatedAt)
   OR (created_at = :lastCreatedAt AND id < :lastId)
ORDER BY created_at DESC, id DESC
LIMIT 20;                                  -- index (created_at, id)
```
Every page costs about the same: an index seek plus 20 rows. The API returns an opaque `nextCursor` (base64 of `created_at,id`).

**Trade-offs:** no random "jump to page 500". It fits feeds, infinite scroll and APIs. You need a **unique, stable** sort key (add `id` as a tie-breaker).

**If you must keep offset** (admin UIs): use a deferred join (`SELECT ... JOIN (SELECT id ... LIMIT 20 OFFSET n) t USING (id)`) so the scan touches only the narrow index, cap the maximum page, and require filters.
""", I, ["pagination", "mysql", "api"], True),

("How do you size a HikariCP connection pool? Isn't bigger always better?", r"""
**No. Bigger is often worse.** A database runs only as many queries in parallel as it has CPU cores and I/O capacity. Past that, extra connections just add context switching, lock contention and memory on the DB, and latency rises for everyone. HikariCP's pool-sizing guide cites a demo where **shrinking** an oversized pool cut response times dramatically.

**How I size it:**
1. **Little's Law:** connections in use ≈ queries/s × average connection hold time. 1,000 q/s × 5 ms = 5 busy connections, so a pool of 10 has room.
2. **Starting formula** from HikariCP/PostgreSQL guidance: `cores × 2 + effective spindles`, measured against the **DB server's** cores. It's a starting point to test around.
3. **Fleet total:** pods × pool size must stay well under what the DB handles (and under `max_connections`). 50 pods × 20 = 1,000 is too many. Use small per-pod pools or a proxy (ProxySQL / RDS Proxy).
4. **Load test** and watch `hikaricp_connections_pending` and DB CPU.

**Related settings:** `connectionTimeout` 2-5 s (fail fast), `maxLifetime` below network or DB idle timeouts, and `leakDetectionThreshold` when debugging.

**The real lever is hold time:** short transactions and no remote calls inside them.
""", I, ["hikaricp", "connection-pool", "database"], True),

("You added read replicas. Now users update their profile and immediately see the old data. Why, and how do you fix it?", r"""
**Why:** MySQL replication is **asynchronous**. The write commits on the primary, and replicas apply it later, usually in milliseconds but seconds under load or during big transactions. The follow-up `GET /profile` was routed (for example through `@Transactional(readOnly = true)`) to a replica that hadn't applied the change yet. That breaks **read-your-writes consistency**.

**Fixes:**
1. **Sticky primary after a write:** after a user writes, route *their* reads to the primary for N seconds (a session flag, cookie or request-context flag). Simple and effective.
2. **Classify reads:** critical "just changed" or decision-making reads (balance, stock before payment, the profile page right after editing) go to the primary. Feeds, search and reports can tolerate lag.
3. **Return the updated resource in the write response** so the client doesn't need an immediate re-read.
4. **GTID-based waiting:** capture the GTID after the write and have the replica wait (`WAIT_FOR_EXECUTED_GTID_SET`) before reading. Precise but more complex.
5. **Operations:** monitor replica lag and take lagging replicas out of the read pool automatically.

Also mention the routing mechanics: an `AbstractRoutingDataSource` keyed on the read-only flag, wrapped in `LazyConnectionDataSourceProxy` so the decision happens when the transaction starts.
""", I, ["replication", "consistency", "mysql"], False),

("In cache-aside, how can the cache end up with stale data even when you delete the key on every update? How do you minimise it?", r"""
**The race:**
```text
Reader: cache MISS -> reads DB (price=100) ...... (slow) ...... SET cache=100
Writer:                    UPDATE price=120; COMMIT; DEL cache
```
The reader loaded the old value **before** the update and wrote it **after** the delete, so the stale 100 stays until the TTL. A second variant: deleting **before** the transaction commits lets a reader reload the not-yet-updated row.

**Minimise it:**
1. **Order:** update the DB, then delete the key **after commit** (`@TransactionalEventListener(phase = AFTER_COMMIT)`), never before.
2. **Always set a TTL** so staleness is bounded.
3. **Delayed double delete:** delete again after ~1 s to catch slow readers.
4. **Versioning:** store `{version, value}` and only write if the new version is greater (a Lua script compares atomically).
5. **CDC invalidation** (Debezium reads the binlog and evicts) when you need reliable eviction across services.
6. **Prefer delete over update** in the cache, so concurrent writers don't race to set values.

**Know where staleness is unacceptable:** stock at checkout, account balance, permissions. Read those from the source of truth, or use explicit versioning.
""", A, ["cache", "consistency", "redis"], True),

("What is a cache stampede? Give three ways to prevent it.", r"""
**Stampede (thundering herd):** a popular key expires, or the cache is cold after a restart or deploy, and **many concurrent requests miss at once**. All of them run the same expensive DB query or computation, the DB spikes, latency rises, and in bad cases it becomes an outage that keeps itself going.

**Prevention:**
1. **Single-flight / request coalescing:** only one caller loads a key; the others wait for that result.
   - Within a JVM: Caffeine `cache.get(key, loader)` or Spring `@Cacheable(sync = true)`.
   - Across instances: a short Redis lock per key (`SET lock:{key} token NX PX 3000`). Losers wait briefly and re-read, or serve stale data.
2. **Refresh before expiry:** a soft TTL with background refresh (Caffeine `refreshAfterWrite`), or probabilistic early expiration where requests occasionally refresh as the TTL approaches. Hot keys then never fully expire.
3. **TTL jitter:** `ttl = base ± random(10%)` so keys loaded together don't expire together.
4. **Serve stale on miss or error** (stale-while-revalidate), using a hard TTL as the limit.
5. **Operations:** warm caches before taking traffic, shed load when the DB saturates, and load test with a flushed cache.
""", I, ["cache", "stampede", "redis"], True),

("A flash-sale product key is overloading one Redis shard (hot key). What do you do?", r"""
**Diagnose:** one Redis node at 100% CPU or network while the others are idle. Client metrics or `redis-cli --hotkeys` (LFU eviction policy needed) show one key taking a huge share of reads.

**Fix reads, best first:**
1. **Local L1 cache** (Caffeine) in each app instance with a short TTL (1-5 s). Each pod then makes at most one Redis read per key per TTL. 100k reads/s becomes ~(pods / TTL) reads/s. A few seconds of staleness is fine for product details.
2. **Key replication / sharding:** store copies as `product:42#0` to `#9` on different slots; readers pick a random suffix, writers update all copies.
3. **Read from replicas** (with Redis Cluster replicas or Sentinel), accepting slight lag.
4. **Push static parts to the CDN** (images, descriptions).

**Hot writes** (the stock counter for the sale item) are harder:
- Split the counter into N sub-counters (`stock:42:0..N`) and decrement a random one, falling back to others when it's empty.
- Or allocate stock **in batches** to app instances or queue the requests. Keep the source-of-truth decrement atomic (Lua or DB conditional update).

**Prevent:** identify sale items ahead of time and pre-warm the L1 cache, run load tests with realistic key skew, and alert on per-shard imbalance.
""", A, ["cache", "hot-key", "redis", "flash-sale"], False),

("When should you NOT add a cache?", r"""
Caches add consistency problems, failure modes and operating cost. Skip or rethink one when:

- **The real problem is a missing index or a bad query.** Fix the root cause first. A cache in front of a 3 s query still gives a 3 s miss, and stampedes when it expires.
- **The hit ratio will be low:** highly personalised or unique requests, data that changes on almost every read, a long-tail keyspace. A 10-20% hit ratio adds a network hop to most requests for little gain.
- **Staleness is unacceptable:** balances, inventory at payment time, permissions just after revocation, unless you can invalidate reliably. Correctness beats speed.
- **The data is cheap to compute or already fast** (an indexed PK lookup in 1 ms vs Redis at 0.5 ms: almost no win, plus another dependency).
- **You can't handle the cache being down.** If the system dies without the cache, you've created a critical dependency and a cold-start outage risk.
- **Write-heavy data:** the invalidation churn costs more than it saves.

**Ask first:** What's the read/write ratio? How stale can the data be? What's the expected hit ratio? What happens when the cache is empty or unavailable? How will we invalidate? Then measure hit ratio and latency after adding it.
""", I, ["cache", "trade-offs", "design"], False),

("How do you choose timeout values for downstream calls?", r"""
**Principles:**
1. **Every remote call gets a timeout:** connect plus read (or response). Library defaults are often infinite or 30-60 s, which ties up threads during incidents.
2. **Connect timeout:** short, around 200-500 ms inside a data centre. Connection setup is fast or it's broken.
3. **Read timeout from data, not gut feel:** look at the dependency's latency distribution and set it near **p99.9 plus margin**, accepting that ~0.1% of calls will time out. (AWS's Builders' Library describes this approach.)
4. **Fit the caller's budget:** with an 800 ms endpoint SLO and three sequential calls, each can't take 2 s. Allocate a budget per call, and **propagate the deadline** so downstreams stop work nobody's waiting for.
5. **Timeouts and retries together:** total worst case = attempts × timeout + backoff. Make sure it fits the budget. Retry only idempotent operations, at one layer.
6. **Differentiate:** a fraud check may justify 1 s; optional recommendations get 150 ms and a fallback.

**Then verify:** track timeout counts per dependency, alert when they rise, and revisit the values when the dependency's latency profile changes. In Spring: configure timeouts on the `RestClient`/`WebClient` request factory, and add `@Transactional(timeout = ...)` or JDBC query timeouts for the DB.
""", I, ["timeouts", "resilience", "api"], False),

("Your endpoint calls three independent services one after another, about 300 ms each. How do you optimise it?", r"""
Since the calls are **independent**, run them **in parallel**. Latency drops from ~900 ms to roughly the slowest one (~300 ms).

```java
try (var io = Executors.newVirtualThreadPerTaskExecutor()) {
    var profile = CompletableFuture.supplyAsync(() -> profileClient.get(userId), io);
    var orders  = CompletableFuture.supplyAsync(() -> orderClient.recent(userId), io);
    var offers  = CompletableFuture.supplyAsync(() -> offerClient.forUser(userId), io)
            .completeOnTimeout(Offers.none(), 350, TimeUnit.MILLISECONDS);   // optional part degrades
    CompletableFuture.allOf(profile, orders, offers).orTimeout(1, TimeUnit.SECONDS).join();
    return new Dashboard(profile.join(), orders.join(), offers.join());
}
```

**Details to mention:**
- Use a **dedicated executor**, not `ForkJoinPool.commonPool()`, which is shared and sized for CPU work. Virtual threads fit blocking I/O well.
- **Per-call timeouts** plus an overall deadline; **fallbacks** for optional data.
- Propagate **MDC and trace context** to the async tasks.
- Decide how failures combine: fail the whole response if a critical part fails, degrade for optional parts.
- Watch the **downstream impact**: parallel calls raise peak concurrency on the dependencies.

**Beyond parallelism:** cache slow-changing parts, ask for a batch or aggregate endpoint, or precompute the dashboard asynchronously when the data changes.
""", I, ["latency", "completablefuture", "concurrency"], True),

("Will switching to virtual threads make my Spring Boot app faster?", r"""
**It depends on where the time goes.**

**Helps:** I/O-bound services with many concurrent requests that **block** (JDBC, HTTP calls). A blocked virtual thread unmounts from its carrier, so you're no longer limited by ~200 platform threads. You get much higher concurrency and throughput with simple blocking code. Turn it on with `spring.threads.virtual.enabled=true` (Boot 3.2+).

**Doesn't help:**
- **CPU-bound work:** you still have N cores. Per-request latency doesn't improve.
- **Single-request latency:** the code path is the same.
- **Downstream limits:** 10,000 virtual threads still share a 20-connection Hikari pool and a rate-limited partner. Requests now queue on the pool instead of the thread pool. Use semaphores or bulkheads to cap concurrency per dependency.

**Gotchas:**
- **Pinning:** on JDK 21-23, blocking inside `synchronized` pins the carrier. Prefer `ReentrantLock` on blocking paths. JDK 24 (JEP 491) fixed most cases. Detect it with the JFR `jdk.VirtualThreadPinned` event.
- **ThreadLocal-heavy code:** millions of threads times big ThreadLocals uses a lot of memory.
- **Don't pool virtual threads.** Create one per task.

**Verdict:** a throughput and simplicity win for blocking I/O workloads. Measure with a load test before and after.
""", I, ["virtual-threads", "java21", "concurrency"], True),

("How would you load test a new checkout API before a big sale?", r"""
**1. Define success:** target load (forecast peak × 1.5 safety factor, say 4,000 RPS), SLO (p99 < 400 ms, errors < 0.5%), and duration.

**2. Realistic scenario:**
- The real mix: browse → cart → checkout ratios, realistic payloads, **hot-product skew**, many distinct users and carts.
- **Open model** (constant arrival rate in k6 or Gatling) to avoid coordinated omission.
- Idempotency keys and test accounts. **Stub or sandbox the payment gateway** so you don't load-test a partner.

**3. Environment:** prod-like sizing and **data volume**. Warm the JVM, then run once with **cold caches** too.

**4. Test types:** ramp to target (load), push until it breaks (stress) to learn the failure mode, a **spike** test (0 → peak in seconds, how sales really start), and a short soak.

**5. Observe the system:** USE metrics per resource (CPU, GC, Hikari pending, DB CPU and locks, Redis, Kafka lag). Find the first bottleneck, fix it, rerun.

**6. Output:** max sustainable RPS per pod at the SLO, a scaling plan (pre-scale, since autoscalers lag spikes), DB connection maths, kill switches for non-critical features, and a runbook.

Bonus: k6 thresholds in CI as a regression gate for the checkout path.
""", I, ["load-testing", "capacity", "k6"], False),

("Back-of-the-envelope: 50M API requests a day with a 5x peak factor. How many app pods do you need?", r"""
**Step 1: average RPS.** 50M / 86,400 s ≈ **580 RPS** (round to 600).

**Step 2: peak.** 600 × 5 = **3,000 RPS**.

**Step 3: per-pod capacity.** Measure it with a load test. Assume one pod (2 vCPU) sustains **300 RPS at p99 within the SLO** with CPU around 70%.

**Step 4: base pods.** 3,000 / 300 = **10 pods**.

**Step 5: headroom.**
- +30% for bursts, rolling deploys, uneven load balancing: ~13.
- **Survive losing one of three AZs:** the remaining two must carry the peak, so 13 × 3/2 ≈ **20 pods** at peak. Autoscale between ~8 off-peak and 20 at peak.

**Step 6: check the shared dependencies** (this is where candidates stand out):
- DB: if each request runs 2 queries with ~5 ms connection hold, Little's law gives 3,000 × 2 × 0.005 = **30 busy connections**. With 20 pods × a pool of 10 = 200 possible, cap pools at ~5 or add a proxy.
- Redis: 3 operations per request = 9k ops/s, fine for one shard, but watch hot keys.
- Payment gateway rate limits and Kafka partition counts.

State assumptions clearly, round freely, and say you'd validate with a load test.
""", I, ["capacity-planning", "estimation"], False),

("What is coordinated omission in load testing?", r"""
**Coordinated omission** (a term from Gil Tene) is a measurement flaw in **closed-loop** load generators, where each virtual user waits for a response before sending its next request.

When the server **stalls** (say a 3 s GC pause or lock), the generator **stops sending** during the stall. Only the few in-flight requests record the 3 s; the hundreds of requests that *would have* arrived during that window, and queued behind the stall, are never sent or measured. The tool "coordinates" with the system under test and **omits the bad samples**. Reported p99 looks fine while real users, who keep arriving regardless, would have seen seconds of delay.

**Example:** the target is 1,000 RPS and the system freezes for 2 s. A closed-loop tool records maybe 50 slow samples. In reality ~2,000 requests would have waited up to 2 s, enough to wreck the p99.

**Avoid it:**
- Use an **open model** (constant arrival rate): k6 `constant-arrival-rate`, Gatling open injection (`constantUsersPerSec`), wrk2.
- Measure latency from the **intended** send time, not the actual send time (HdrHistogram supports correction).
- Check that the achieved request rate actually matched the target throughout the test.
""", A, ["load-testing", "measurement"], False),

("A microbenchmark shows method A is 10x faster than method B. Should you trust it?", r"""
**Not without checking how it was measured.** Naive `System.nanoTime()` loops on the JVM are misleading:

- **JIT warm-up:** early iterations run interpreted, later ones compiled, so the result depends on order and iteration count.
- **Dead-code elimination:** if the result isn't used, the JIT may delete the computation, making a "10x faster" method actually do nothing.
- **Constant folding:** constant inputs get computed at compile time.
- **On-stack replacement and inlining** differ from real call sites. GC noise and CPU frequency scaling add variance.

**Do it properly with JMH:** `@Benchmark` methods that return results (or use a `Blackhole`), `@State` for inputs, warm-up and measurement iterations, multiple forks, reporting error margins.

**Then ask whether it matters:**
- Is this code on the hot path? A profiler (flame graph under real load) should show it as significant first.
- Does the end-to-end p99 or throughput improve in a load test? A 10x win on 0.5% of request time is invisible.
- Does the faster version cost readability or correctness?

Senior framing: **profile first, microbenchmark second, confirm end to end.**
""", A, ["benchmarking", "jmh", "jvm"], False),

("A 5 MB JSON response makes the mobile app slow. What do you do?", r"""
Big payloads cost server serialisation CPU, network time (especially on mobile) and client parse time and memory.

**Reduce what you send:**
1. **Paginate** with keyset pagination and a capped page size. Mobile screens show 20-50 items, not 10,000.
2. **Return only the fields the screen needs:** list DTOs vs detail DTOs, or sparse fieldsets (`?fields=id,name,price`). Never serialise entities (lazy collections, internal fields).
3. **Remove waste:** nulls (`@JsonInclude(NON_NULL)`), repeated nested objects (send IDs plus a lookup map), long enum strings.

**Send it more efficiently:**
4. **Compression:** `server.compression.enabled=true` with JSON MIME types. Text JSON typically shrinks 5-10x. Brotli at the CDN or gateway.
5. **HTTP caching:** `ETag` + `If-None-Match` gives a 304 with no body when nothing changed; `Cache-Control` for static catalogues; CDN for public data.
6. **Delta sync:** `?updatedSince=` so the app fetches only changes.

**Verify:** measure response size before and after, server time vs transfer time, and the client's time-to-render. Then add a guardrail: response-size metrics and alerts per endpoint.
""", B, ["api", "http", "payload"], False),
]

SOURCES = [
 ("Dean & Barroso - The Tail at Scale (CACM)", "https://research.google/pubs/the-tail-at-scale/"),
 ("Oracle - HotSpot Virtual Machine Garbage Collection Tuning Guide (JDK 21)", "https://docs.oracle.com/en/java/javase/21/gctuning/"),
 ("OpenJDK JEP 474 - ZGC: Generational Mode by Default", "https://openjdk.org/jeps/474"),
 ("OpenJDK JEP 491 - Synchronize Virtual Threads without Pinning", "https://openjdk.org/jeps/491"),
 ("async-profiler (GitHub)", "https://github.com/async-profiler/async-profiler"),
 ("OpenJDK JMH - Java Microbenchmark Harness", "https://github.com/openjdk/jmh"),
 ("MySQL 8.4 Reference - EXPLAIN Output Format", "https://dev.mysql.com/doc/refman/8.4/en/explain-output.html"),
 ("MySQL 8.4 Reference - Optimization and Indexes", "https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html"),
 ("MySQL 8.4 Reference - The Slow Query Log", "https://dev.mysql.com/doc/refman/8.4/en/slow-query-log.html"),
 ("HikariCP - About Pool Sizing", "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing"),
 ("Vlad Mihalcea - N+1 query problem with JPA and Hibernate", "https://vladmihalcea.com/n-plus-1-query-problem/"),
 ("Baeldung - Spring Data JPA Batch Inserts", "https://www.baeldung.com/spring-data-jpa-batch-inserts"),
 ("AWS Builders' Library - Caching challenges and strategies", "https://aws.amazon.com/builders-library/caching-challenges-and-strategies/"),
 ("AWS Builders' Library - Timeouts, retries and backoff with jitter", "https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/"),
 ("Use The Index, Luke - Paging Through Results (keyset pagination)", "https://use-the-index-luke.com/no-offset"),
 ("Grafana k6 Documentation - Scenarios and executors", "https://grafana.com/docs/k6/latest/using-k6/scenarios/"),
 ("Gil Tene - How NOT to Measure Latency (coordinated omission)", "https://www.youtube.com/watch?v=lJ8ydIuPFeU"),
]

build("performance", "perf", "Performance: JVM, Database & Caching", 13, "⚡",
      "Measure and fix real performance problems: percentiles and Little's law, JVM memory and GC, profiling, MySQL indexing, caching pitfalls, API latency and load testing with capacity math.",
      NOTES, QA, SOURCES)
