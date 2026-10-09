from sd_common import *

topics = []

topics.append(T("indexing-internals", "Indexing Internals: B+ Trees, LSM Trees and InnoDB", "Intermediate",
"How databases find data fast: B+ tree indexes in MySQL InnoDB, clustered vs secondary indexes, LSM trees in write-heavy stores, and how to design good indexes.",
r'''
## Why indexes exist

Without an index, `SELECT * FROM orders WHERE user_id = 42` scans every row: a **full table scan**. On 100 million rows that is seconds or minutes. An index is an extra data structure that maps column values to row locations, turning O(n) scans into O(log n) lookups. The price: extra storage and slower writes, since every insert/update must also update each index.

## B+ trees (MySQL InnoDB, PostgreSQL, Oracle)

A B+ tree is a balanced tree optimised for disks, where each node is a **page** (16 KB in InnoDB).

```text
                    [ 100 | 500 ]                <- root (internal)
          /               |               \
   [20 | 50 | 80]   [200 | 300 | 400]   [600 | 800]   <- internal
     /  |  |  \         ...                  ...
 [leaf][leaf][leaf] <-> [leaf] <-> [leaf]    <- leaves hold keys (+ data), linked list
```

Key properties:
- **High fan-out**: one 16 KB page holds hundreds of keys, so a tree of depth 3-4 indexes billions of rows. A lookup is 3-4 page reads, and upper levels are usually cached in memory (the buffer pool), so often just 1 disk read.
- **All data in leaves**; internal nodes only route.
- **Leaves are linked**, so range queries (`BETWEEN`, `ORDER BY`, `>`) walk sideways efficiently.
- Updates are **in place**; page splits happen when a page fills.

### InnoDB clustered index

In InnoDB, the table **is** a B+ tree ordered by the primary key: leaf pages contain full rows. This is the **clustered index**.

- Lookups by primary key are fastest (one tree traversal).
- Rows are physically stored in PK order, so **use an auto-increment or time-ordered PK**. Random UUIDv4 primary keys cause inserts all over the tree, page splits, fragmentation and poor cache use. Prefer BIGINT AUTO_INCREMENT, or time-ordered IDs (Snowflake, UUIDv7) stored as BINARY(16).

### Secondary indexes

A secondary index (`INDEX idx_user (user_id)`) is a separate B+ tree whose leaves store the indexed column **plus the primary key**. A lookup by user_id finds PKs, then does a second lookup in the clustered index for each row ("bookmark lookup"). Hence:
- A large PK makes every secondary index bigger.
- A **covering index** contains every column the query needs, avoiding the second lookup. `EXPLAIN` shows `Using index`.

### Composite indexes and the leftmost prefix rule

`INDEX idx (user_id, status, created_at)` is sorted by user_id, then status, then created_at. It can serve:
- `WHERE user_id = ?`
- `WHERE user_id = ? AND status = ?`
- `WHERE user_id = ? AND status = ? ORDER BY created_at DESC`

It cannot efficiently serve `WHERE status = ?` alone (status is not the leftmost column). Order columns as: equality filters first, then range/sort columns. A range condition stops later columns from being used for seeking.

### Things that silently kill index use

- Functions on the column: `WHERE DATE(created_at) = '2026-01-01'` → rewrite as a range.
- Leading wildcard: `LIKE '%phone'`.
- Implicit type conversion: comparing a VARCHAR column to a number.
- Low selectivity: index on `gender` rarely helps.
- `OR` across different columns (sometimes merges, often not).

Always check with `EXPLAIN`: look at `type` (`ALL` = full scan, `ref`/`range`/`const` = good), `key`, `rows`, and `Extra` (`Using filesort`, `Using temporary` are warning signs).

```sql
EXPLAIN SELECT id, total FROM orders
WHERE user_id = 42 AND status = 'DELIVERED'
ORDER BY created_at DESC LIMIT 20;
```

## Hash indexes

O(1) equality lookups, no range support. Used by in-memory engines and internally (InnoDB adaptive hash index). Redis is essentially a giant hash table.

## LSM trees (Cassandra, RocksDB, HBase, LevelDB, ScyllaDB)

The Log-Structured Merge tree optimises for **writes**.

```text
write -> [WAL on disk] + [MemTable in memory, sorted]
                  | when full, flush
                  v
         [SSTable L0] [SSTable L0]   (immutable, sorted files)
                  | background compaction merges
                  v
         [SSTable L1 ........] -> [L2 ..................]
```

1. Writes append to a write-ahead log (durability) and insert into an in-memory sorted structure (memtable).
2. When the memtable fills (e.g., 64 MB) it is flushed as an immutable sorted file (SSTable). All writes are sequential, which disks love.
3. Reads check the memtable, then SSTables from newest to oldest. **Bloom filters** per SSTable skip files that definitely don't contain the key; sparse indexes locate blocks.
4. **Compaction** merges SSTables, discarding overwritten values and deletions (tombstones).

## B+ tree vs LSM tree

| | B+ tree | LSM tree |
|---|---|---|
| Writes | Random in-place updates, slower | Sequential appends, very fast |
| Reads | Predictable, fast | May check several files; Bloom filters help |
| Space | Some fragmentation | Better compression; temporary duplicates |
| Background work | Page splits | Compaction (can cause latency spikes) |
| Amplification | Write amplification moderate | Write amplification from compaction, read amplification |
| Used by | MySQL, Postgres | Cassandra, RocksDB, HBase, Kafka-like logs |

Rule of thumb: read-heavy with range queries and transactions → B+ tree. Massive write ingestion (events, messages, metrics) → LSM.

## Other index types to name-drop

- **Full-text / inverted index** (Elasticsearch, MySQL FULLTEXT).
- **Geospatial** (R-tree, geohash, MySQL SPATIAL, Redis GEO).
- **Bitmap indexes** for analytics on low-cardinality columns.

## Practical guidelines for Spring Boot/MySQL apps

- Index every foreign key you join or filter on.
- Design composite indexes for your top queries; one good composite index beats several single-column ones.
- Use keyset pagination (`WHERE id < ? ORDER BY id DESC LIMIT 20`) instead of large OFFSETs.
- Watch write-heavy tables: 10 indexes means 11 B+ tree updates per insert.
- Enable the slow query log (`long_query_time = 0.5`) and review regularly.
''',
["Index turns full scans into O(log n) lookups at the cost of storage and slower writes",
 "B+ tree: high fan-out, 3-4 levels for billions of rows, linked leaves for range scans",
 "InnoDB clustered index = table stored in PK order; use sequential PKs not random UUIDs",
 "Secondary index leaves store PK; covering indexes avoid the extra lookup",
 "Composite index follows leftmost-prefix rule: equality columns first, then range/sort",
 "LSM tree: WAL + memtable + SSTables + compaction; great for writes",
 "Bloom filters let LSM reads skip files",
 "Always verify with EXPLAIN; avoid functions on indexed columns"],
[("Why does InnoDB perform poorly with random UUID primary keys?",
 "InnoDB stores rows in a clustered B+ tree ordered by primary key. Random UUIDs make each insert land at a random leaf page, causing frequent page splits, fragmented half-empty pages, and poor buffer pool locality, so inserts slow down as the table grows. They are also 16-36 bytes, inflating every secondary index (which stores the PK). Sequential keys like AUTO_INCREMENT, Snowflake IDs or UUIDv7 append to the right edge of the tree instead."),
 ("Explain the leftmost prefix rule with an example.",
 "A composite index on (a, b, c) is sorted by a, then b within a, then c. It can be used for queries filtering on a, on a and b, or on a, b and c, and for sorting by these in order. It cannot be used to seek on b or c alone, because those values are scattered across the index. Also, a range on b (b > 5) prevents using c for seeking. So put equality columns first and range/sort columns last."),
 ("What is a covering index?",
 "An index that contains all the columns a query needs, so the database answers the query from the index alone without fetching the full row from the clustered index. For `SELECT status, total FROM orders WHERE user_id = ?`, an index on (user_id, status, total) is covering. EXPLAIN shows 'Using index'. It saves random I/O but makes the index larger and writes slower."),
 ("Compare B+ trees and LSM trees.",
 "B+ trees update pages in place, giving predictable fast reads and range scans, ideal for read-heavy OLTP like MySQL. LSM trees buffer writes in memory and flush sorted immutable files sequentially, then compact them in the background, giving very high write throughput, used by Cassandra and RocksDB. LSM reads may check multiple files (mitigated by Bloom filters) and compaction can cause latency spikes."),
 ("A query is slow even though there is an index. What could be wrong?",
 "The query may not be able to use it: a function on the column (DATE(created_at)), a leading wildcard LIKE, type mismatch, wrong column order in a composite index, or low selectivity making the optimizer prefer a scan. It might also be doing many bookmark lookups or a filesort. I'd run EXPLAIN, check type, key, rows and Extra, then rewrite the query or create a better composite/covering index.")],
[DDIA, ("MySQL 8.0 Reference - InnoDB Indexes", "https://dev.mysql.com/doc/refman/8.0/en/innodb-index-types.html"), ("Use The Index, Luke", "https://use-the-index-luke.com/"), ("RocksDB Wiki - LSM overview", "https://github.com/facebook/rocksdb/wiki")]))

topics.append(T("replication", "Database Replication", "Intermediate",
"Keeping copies of data on multiple machines for availability and read scaling: leader-follower, multi-leader, leaderless, sync vs async, and replication lag problems.",
r'''
## Why replicate

Replication keeps copies of the same data on several machines:
- **High availability**: if one node dies, another takes over.
- **Read scaling**: spread reads across replicas.
- **Latency**: place replicas near users (Mumbai and Singapore regions).
- **Backups and analytics**: run heavy reports on a replica without hurting production.

## Leader-follower (primary-replica, master-slave)

The most common model, used by MySQL, PostgreSQL, MongoDB replica sets, Redis.

```text
         writes
App -----------> [Primary] --binlog--> [Replica 1]  <--- reads
   \                        \--------> [Replica 2]  <--- reads
    \---------------- reads ---------------^
```

- All writes go to the primary, which records them in a log (MySQL **binlog**). Replicas pull the log and apply changes in order.
- Reads can go to replicas. In Spring Boot you route with `AbstractRoutingDataSource`, sending `@Transactional(readOnly = true)` methods to a replica pool; or use a proxy like ProxySQL.

### Synchronous vs asynchronous

| Mode | How | Pros | Cons |
|---|---|---|---|
| Asynchronous (MySQL default) | Primary commits, ships log later | Fast writes; primary not blocked by slow replicas | Committed data can be lost if primary dies before shipping |
| Semi-synchronous | Primary waits for at least 1 replica to receive the log | Bounded data loss (usually zero) | Slightly higher write latency |
| Synchronous | Waits for all replicas to apply | No loss | One slow replica stalls all writes |

Practical choice: semi-sync with one replica in another availability zone for important data.

### Failover

When the primary dies: detect (heartbeat timeouts), choose the most up-to-date replica, promote it, repoint the application (DNS/VIP/proxy change), and make the old primary a replica when it returns. Tools: Orchestrator, MySQL Group Replication/InnoDB Cluster, AWS RDS Multi-AZ (automatic, ~60-120 s), Patroni for Postgres.

Dangers:
- **Split brain**: two nodes both think they are primary and accept writes. Prevent with fencing (STONITH) and consensus-based leader election.
- **Lost writes** with async replication.
- Choosing the timeout: too short causes needless failovers; too long extends downtime.

## Replication lag and its consequences

Async replicas are behind by milliseconds normally, but seconds or minutes under heavy load. That breaks user expectations:

1. **Read-your-own-writes**: user updates profile, page reloads from a lagging replica and shows the old name. Fixes: read from primary for a few seconds after a user's write, or for that user's own data; track the write's position (GTID) and read from a replica that has caught up.
2. **Monotonic reads**: user sees a comment, refreshes, comment disappears (hit a more-lagged replica). Fix: pin a user to one replica (hash user_id).
3. **Consistent prefix reads**: a reply appears before the question. Fix: keep causally related writes in the same partition.

Monitor lag (`Seconds_Behind_Master` / `Replica_SQL_Running` in MySQL) and remove replicas lagging over a threshold from the read pool.

## Multi-leader replication

Several nodes accept writes and replicate to each other, typically one leader per region.

- **Pros**: local write latency in each region, survives a region outage.
- **Cons**: **write conflicts** (two regions edit the same row). Resolution strategies: last-write-wins by timestamp (loses data), merge logic, CRDTs, or avoid conflicts by routing each user's writes to a home region.

Used in collaborative editing, offline-first mobile apps (the device is a leader), multi-region active-active setups.

## Leaderless replication (Dynamo-style)

Used by Cassandra, DynamoDB, Riak. The client (or a coordinator) writes to several replicas in parallel and reads from several.

With **N** replicas, a write waits for **W** acknowledgements and a read queries **R** replicas. If **W + R > N**, the read and write sets overlap, so at least one replica in the read has the latest value. Typical: N=3, W=2, R=2 (QUORUM in Cassandra).

- Repair mechanisms: **read repair** (fix stale replicas found during reads), **anti-entropy** background sync using Merkle trees, **hinted handoff** (another node holds writes for a down node temporarily).
- Tunable: W=1, R=1 for speed with eventual consistency; ALL for strongest.
- No failover needed; any node can take writes, giving high availability.

## Replication in other systems

- **Kafka**: each partition has a leader and followers; the in-sync replica set (ISR) plus `acks=all` and `min.insync.replicas=2` gives durability.
- **Redis**: async primary-replica; Sentinel or Cluster handles failover; can lose recent writes on failover.
- **Consensus-based** (Raft/Paxos: etcd, ZooKeeper, CockroachDB, TiDB): a write commits when a majority acknowledges; strong consistency with automatic leader election.

## Replication vs backups

Replication copies mistakes too: `DELETE FROM users` without WHERE replicates instantly. You still need **point-in-time backups** (daily snapshots + binlog retention) to restore. Delayed replicas (intentionally 1 hour behind) are another safety net.

## Interview phrasing

"MySQL primary with two async read replicas in different AZs, one of them semi-sync for durability. Reads that tolerate staleness go to replicas; for read-your-writes, the user's own profile reads go to the primary for 5 seconds after an update. Failover through RDS Multi-AZ or Orchestrator with fencing to avoid split brain."
''',
["Replication gives availability, read scaling, geo-latency and offloads analytics",
 "Leader-follower: writes to primary, replicas apply binlog; route reads to replicas",
 "Async = fast but may lose writes on failover; semi-sync = bounded loss",
 "Replication lag breaks read-your-writes, monotonic reads, consistent prefix",
 "Failover needs detection, promotion, fencing to prevent split brain",
 "Multi-leader enables multi-region writes but needs conflict resolution",
 "Leaderless quorum: W + R > N guarantees overlap (N=3, W=2, R=2)",
 "Replication is not backup: keep point-in-time backups"],
[("How does MySQL replication work?",
 "The primary writes every committed change to its binary log. Each replica has an I/O thread that streams the binlog into a local relay log and a SQL thread that replays those events in order. By default it is asynchronous, so the primary does not wait. With GTIDs each transaction has a global ID, which makes failover and repointing replicas easier. Semi-sync replication makes the primary wait until at least one replica has received the event."),
 ("What is replication lag and how do you handle read-your-own-writes?",
 "Replication lag is the delay before a write on the primary appears on replicas. A user who updates data and immediately reads from a replica may see the old value. Fixes: route reads of data the user just modified (or all their reads for a short window after a write) to the primary; track the last write's GTID and only read from replicas that have applied it; or cache the new value client-side."),
 ("What is split brain and how is it prevented?",
 "Split brain is when two nodes simultaneously believe they are the primary, usually after a network partition, and both accept writes, causing divergent data. Prevention: use consensus (majority quorum) for leader election so only one side of a partition can elect a leader, fence the old primary (revoke its access, power it off, or use epoch/fencing tokens), and have the application connect through a single source of truth for the primary's address."),
 ("Explain quorum reads and writes.",
 "In leaderless systems with N replicas, a write is successful after W replicas acknowledge and a read queries R replicas and takes the newest version. If W + R > N, every read set overlaps every write set, so the read sees the latest acknowledged write. With N=3, W=2, R=2 the system tolerates one node down for both reads and writes. Lower W or R improves latency and availability but weakens consistency."),
 ("Synchronous or asynchronous replication: which would you choose for a payment system?",
 "For payments I'd avoid losing committed transactions, so I'd use semi-synchronous replication (or a consensus-based database) with at least one replica in another availability zone acknowledging before commit. Fully synchronous to all replicas risks blocking writes when one replica is slow. The extra few milliseconds of latency is acceptable for the durability guarantee.")],
[DDIA, PRIMER, ("MySQL 8.0 Reference - Replication", "https://dev.mysql.com/doc/refman/8.0/en/replication.html"), ("Amazon Dynamo paper", "https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf")]))

topics.append(T("sharding-partitioning", "Sharding and Partitioning", "Intermediate",
"Splitting data across multiple machines when one database cannot hold or serve it: partitioning strategies, choosing shard keys, hot spots, resharding and cross-shard queries.",
r'''
## What and why

**Partitioning** splits a large dataset into smaller pieces. When those pieces live on different database servers it is usually called **sharding**. You shard when a single primary can no longer handle the **write throughput** or **data size** (or its working set no longer fits in memory), after you have exhausted indexing, caching, read replicas and vertical scaling.

Two forms:
- **Vertical partitioning**: split by columns or features (users DB, orders DB, payments DB). This is what microservices naturally do.
- **Horizontal partitioning (sharding)**: same schema, rows divided across nodes (users 1-10M on shard 1, 10M-20M on shard 2).

Note MySQL also has **table partitioning** within one server (`PARTITION BY RANGE (YEAR(created_at))`), useful for dropping old data quickly, but it doesn't add machines.

## Partitioning strategies

### Range-based
Rows assigned by ranges of the key: A-F, G-M; or by date.
- Pros: efficient range queries, easy to reason about.
- Cons: **hot spots**. Time-based keys send all current writes to the newest shard.

### Hash-based
`shard = hash(key) % N`.
- Pros: even distribution.
- Cons: range queries hit all shards; **changing N remaps almost all keys** (adding a 5th shard to 4 moves ~80% of data). Use consistent hashing or a fixed number of logical partitions instead.

### Directory / lookup-based
A lookup service maps key → shard (`tenant 123 → shard 7`).
- Pros: flexible; move a big tenant to its own shard.
- Cons: the directory is an extra hop and must be highly available and cached.

### Logical shards (recommended practice)
Create many logical partitions (e.g., 1,024 or 4,096) and map them onto fewer physical servers. `logical = hash(user_id) % 1024`, and a small config maps logical ranges to physical hosts. Rebalancing = moving whole logical shards, no rehashing of keys. Used by Vitess, Cassandra vnodes, Redis Cluster (16,384 slots), Elasticsearch (fixed primary shards).

### Geo-based
Partition by region (India users on Mumbai cluster) for latency and data-residency laws.

## Choosing a shard key: the most important decision

A good shard key:
1. Has **high cardinality** (many distinct values).
2. Spreads **load evenly** (reads and writes, not just data).
3. Keeps data needed together **on the same shard**, so the most common queries hit one shard.

Examples:

| System | Good shard key | Why |
|---|---|---|
| E-commerce orders | user_id | "My orders" is single-shard; user's data co-located |
| Chat | conversation_id | Messages of one chat together |
| Multi-tenant SaaS | tenant_id | Tenant isolation, no cross-tenant queries |
| URL shortener | short code | Lookup is always by code |
| Ride-hailing locations | geohash/city | Nearby search stays local |

Bad keys: `created_date` (hot shard), `country` for an India-heavy app (one huge shard), `status` (low cardinality).

### Secondary access patterns

Sharding orders by user_id makes "orders for seller X" a scatter-gather across all shards. Options:
- Maintain a **second copy** sharded by seller_id (written via events/CDC).
- **Global secondary index** table: seller_id → (order_id, user_id).
- Send analytical queries to a data warehouse.

## Hot spots and celebrities

Even with hashing, one key can be hot (a celebrity's posts, a viral product). Mitigations: cache aggressively, split the key (`product42#0..#9` and aggregate on read), or give the hot entity a dedicated shard.

## Cross-shard problems

- **Joins**: avoid; denormalise or join in the application.
- **Transactions**: across shards need 2PC or sagas; design so most transactions are single-shard (co-locate by user_id).
- **Unique constraints**: e.g., unique email across shards needs a separate lookup table or a globally unique ID scheme.
- **Global IDs**: AUTO_INCREMENT per shard collides; use Snowflake IDs or embed the shard id in the ID.
- **Aggregations / pagination across shards**: scatter-gather, then merge-sort; expensive.

## Resharding

Eventually shards fill up. Approaches:
1. Pre-split into many logical shards from day one, so you only move logical shards to new hosts.
2. Online migration: double-write to old and new locations, backfill historical data, verify, switch reads, stop old writes.
3. Tools: Vitess resharding workflows, Cassandra adding nodes (token ranges stream automatically), DynamoDB automatic partition splits.

## Request routing

How does the app find the right shard?
- **Client-side/app-level**: a library computes the shard (e.g., ShardingSphere for Java/Spring).
- **Proxy**: Vitess VTGate, ProxySQL route queries.
- **Coordinator with metadata**: ZooKeeper/etcd holds the shard map; clients cache it.

## When NOT to shard

Sharding is expensive in complexity. A single MySQL instance with 64 cores and NVMe SSDs can serve terabytes and thousands of writes/s. First: archive old data, use read replicas, cache, optimize queries, split by service (vertical partitioning). Interviewers like hearing: "We do not need sharding at 40 writes/s; I would revisit at around 5-10k writes/s or several TB."

## Interview phrasing

"Orders grow 5 TB a year and peak at 20k writes/s, beyond one primary. I'll shard by user_id using 1,024 logical shards mapped to 16 MySQL clusters, each with a primary and two replicas. Order IDs are Snowflake IDs. Seller-side queries are served from a copy indexed by seller_id built via CDC into a separate store."
''',
["Shard only after indexes, caching, replicas and vertical scaling are exhausted",
 "Range sharding supports range queries but creates hot spots",
 "Hash sharding spreads load; hash % N remaps most keys when N changes",
 "Use many logical shards mapped to fewer physical nodes for easy rebalancing",
 "Shard key: high cardinality, even load, co-locates data for common queries",
 "Cross-shard joins, transactions and unique constraints are hard: design them away",
 "Need global unique IDs (Snowflake) once sharded",
 "Routing via app library (ShardingSphere), proxy (Vitess) or metadata service"],
[("How would you choose a shard key for an orders table?",
 "I'd look at the dominant queries. Most are 'get my orders' and 'get order by id' for a user, so user_id is a good key: high cardinality, even distribution, and a user's orders sit on one shard. I'd embed the shard or user info in the order ID (or keep an order_id→user_id lookup) so order lookups also go to one shard. Seller or admin queries would use a separate copy or index built via CDC."),
 ("What is the problem with hash(key) % N sharding?",
 "When N changes (adding or removing a shard), almost every key maps to a different shard, so you'd have to move most of the data. Going from 4 to 5 shards moves about 80% of keys. Fixes are consistent hashing, which moves only about 1/N of keys, or using a large fixed number of logical partitions mapped to physical servers so you move whole partitions instead of rehashing."),
 ("How do you handle a hot shard?",
 "First identify whether a single key or a key range is hot. For a hot key, add caching in front, split the key into multiple sub-keys and aggregate reads, or isolate it on a dedicated shard. For a hot range (like time-based keys), switch to hash-based or composite keys. With logical shards I can also move the hot logical shard onto a bigger or dedicated machine."),
 ("How do you do a transaction across two shards?",
 "Avoid it by design: co-locate data that changes together on the same shard. If unavoidable, use two-phase commit for strict atomicity (at the cost of blocking and latency) or more commonly a saga: a sequence of local transactions with compensating actions, coordinated by events through a reliable queue with an outbox. Each step must be idempotent."),
 ("How would you migrate from one database to a sharded setup without downtime?",
 "Introduce a routing layer, then: start dual writes to old and new shards (or use CDC from the old DB), backfill historical data in batches, run verification comparing both sides, shift reads gradually to the new shards behind a feature flag, then stop writes to the old store. Keep the ability to roll back until confident. Pre-splitting into many logical shards makes future rebalancing easier.")],
[DDIA, PRIMER, ("Vitess documentation - Sharding", "https://vitess.io/docs/reference/features/sharding/"), ("Notion engineering - Sharding Postgres", "https://www.notion.so/blog/sharding-postgres-at-notion")]))

topics.append(T("consistent-hashing", "Consistent Hashing", "Intermediate",
"A hashing scheme that maps keys and servers onto a ring so that adding or removing a server moves only a small fraction of keys, used in caches, Cassandra and load balancers.",
r'''
## The problem with modulo hashing

Suppose you have 4 cache servers and route keys with `server = hash(key) % 4`. Now one server dies or you add a fifth. With `% 5`, a key that hashed to 17 goes from server 1 (17 % 4) to server 2 (17 % 5). In general, changing N from 4 to 5 remaps about **80%** of keys. For a cache that means a mass of misses hitting the database at once (a self-inflicted stampede). For a database it means migrating most of the data.

We want: when a node is added or removed, only about **1/N** of the keys move.

## The hash ring

1. Take a hash function with a large output space, e.g., 0 to 2^32 - 1, and imagine it as a circle.
2. Hash each **server** (by its name or IP) to a position on the ring.
3. Hash each **key** to a position on the ring.
4. A key belongs to the **first server found moving clockwise** from the key's position.

```text
                    0 / 2^32
                 .----S1----.
     key k2 *  /              \
             S3                 * key k1
              |                 |
               \               /
                '-----S2------'

  Moving clockwise (S1 -> k1 -> S2 -> S3 -> k2 -> S1):
  k1 lies between S1 and S2  => stored on S2
  k2 lies between S3 and S1  => stored on S1
```

### Adding a server

A new server S4 placed between S1 and S2 takes over only the keys between S1 and S4 that previously went to S2. Every other key stays put. On average only K/N keys move (K keys, N servers).

### Removing a server

When S2 dies, only S2's keys move to the next server clockwise. Others are unaffected.

## Virtual nodes (vnodes)

With few servers placed randomly, the ring arcs are uneven: one server may own 40% of the ring. Also, when a server leaves, all its load lands on one neighbour.

Fix: place each physical server on the ring many times (e.g., 100-200 **virtual nodes**: hash("S1#1"), hash("S1#2"), ...).

- Load evens out statistically (standard deviation drops sharply with more vnodes).
- When a server leaves, its many small arcs are spread across many servers.
- Heterogeneous hardware: give a bigger machine more vnodes (weighting).

Cassandra historically used 256 vnodes per node (newer guidance uses fewer, like 16, with a smarter token allocator).

## Implementation in Java

A sorted map gives the "next clockwise" lookup in O(log n):

```java
public class ConsistentHash<T> {
    private final TreeMap<Long, T> ring = new TreeMap<>();
    private final int vnodes;

    public ConsistentHash(Collection<T> nodes, int vnodes) {
        this.vnodes = vnodes;
        nodes.forEach(this::add);
    }
    public void add(T node) {
        for (int i = 0; i < vnodes; i++) ring.put(hash(node + "#" + i), node);
    }
    public void remove(T node) {
        for (int i = 0; i < vnodes; i++) ring.remove(hash(node + "#" + i));
    }
    public T get(String key) {
        if (ring.isEmpty()) return null;
        Map.Entry<Long, T> e = ring.ceilingEntry(hash(key));
        return (e != null ? e : ring.firstEntry()).getValue(); // wrap around
    }
    private long hash(String s) { // use a good hash like MurmurHash3 in practice
        return Integer.toUnsignedLong(Hashing.murmur3_32_fixed().hashString(s, UTF_8).asInt());
    }
}
```

## Replication on the ring

To store 3 replicas, walk clockwise and pick the next 3 **distinct physical** servers (skip vnodes of the same machine; ideally also different racks/AZs). This is exactly how Dynamo and Cassandra place replicas. The list of nodes responsible for a key is its **preference list**.

## Where it's used

- **Distributed caches**: Memcached clients (ketama), so adding a cache node doesn't flush everything.
- **Cassandra, DynamoDB, Riak**: partition data across nodes.
- **Load balancers**: Nginx `hash $key consistent`, Envoy ring hash / Maglev, to keep a user or key on the same backend (cache affinity).
- **CDNs and sharded WebSocket gateways**: route a user to a stable server.
- **Discord, Akamai** and many others publicly describe ring-based routing.

## Alternatives and related ideas

- **Fixed slots** (Redis Cluster): 16,384 hash slots, `slot = CRC16(key) % 16384`, slots assigned to nodes; moving a slot moves its keys. Similar benefit with explicit control.
- **Rendezvous (highest random weight) hashing**: for each key, compute hash(key, server) for all servers and pick the highest. Simple and even; O(N) per lookup.
- **Jump consistent hash** (Google): tiny, fast, no memory, but servers must be numbered and can only be added/removed at the end.
- **Maglev hashing**: lookup-table based, used in Google's load balancers for fast, even distribution.

## Limitations

- Doesn't solve **hot keys**: a single viral key still lands on one node. Combine with caching or key splitting.
- Needs consistent membership views; nodes must agree on the ring (gossip in Cassandra, ZooKeeper in other systems).
- Data still has to physically move when nodes change; consistent hashing just minimises how much.

## Interview phrasing

"I'll distribute keys across cache nodes using consistent hashing with ~150 virtual nodes per server, so adding a node moves only about 1/N of keys and load stays balanced. Replicas go to the next two distinct nodes clockwise in different AZs."
''',
["Modulo hashing remaps ~all keys when server count changes",
 "Consistent hashing: servers and keys on a ring; key goes to next server clockwise",
 "Adding/removing a node moves only ~1/N of keys",
 "Virtual nodes even out load and spread a failed node's keys across many nodes",
 "Implement with a sorted map (TreeMap.ceilingEntry) for O(log n) lookup",
 "Replicas = next distinct physical nodes clockwise (Dynamo/Cassandra)",
 "Alternatives: Redis hash slots, rendezvous hashing, jump hash, Maglev",
 "Does not fix hot keys on its own"],
[("Explain consistent hashing in simple terms.",
 "Imagine a circle of hash values. Each server is hashed to a point on the circle, and each key is hashed too. A key is stored on the first server you meet moving clockwise. When a server is added, it only takes keys from the arc just before it; when one is removed, only its keys move to the next server. So on average only 1/N of keys move, unlike modulo hashing where nearly all keys move."),
 ("Why do we need virtual nodes?",
 "With few servers at random points, the arcs between them differ greatly in size, so some servers get far more keys. Also, when a server fails, its whole load moves to a single neighbour. Virtual nodes place each server at many points, making each server's share close to equal and spreading a failed server's keys across many others. They also let us weight more powerful servers by giving them more vnodes."),
 ("How does Cassandra use consistent hashing?",
 "Cassandra hashes the partition key with Murmur3 to a token on a ring. Each node owns token ranges (via vnodes). The node owning the token is the first replica; with replication factor 3, the next distinct nodes on the ring (respecting racks/data centers with NetworkTopologyStrategy) hold the other replicas. When nodes join or leave, only the affected token ranges are streamed."),
 ("How is Redis Cluster's approach different?",
 "Redis Cluster uses a fixed set of 16,384 hash slots. A key's slot is CRC16(key) mod 16384, and each master node owns a subset of slots. Resharding moves slots between nodes. It's not a ring, but achieves the same goal of moving only a fraction of keys. Hash tags like {user42} force related keys into the same slot so multi-key operations work."),
 ("Does consistent hashing solve hot key problems?",
 "No. It balances the number of keys per node, but if one key gets enormous traffic, that key still lives on one node (and its replicas). Solutions are a local in-process cache in front, replicating the hot key under several suffixed keys and choosing randomly, or reading from replicas. Consistent hashing should be combined with these techniques.")],
[("Karger et al. - Consistent Hashing and Random Trees", "https://www.cs.princeton.edu/courses/archive/fall09/cos518/papers/chash.pdf"), ("Amazon Dynamo paper", "https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf"), ("ByteByteGo - Design consistent hashing", "https://bytebytego.com/courses/system-design-interview/design-consistent-hashing"), ("Redis Cluster specification", "https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/")]))

topics.append(T("cap-pacelc-consistency", "CAP, PACELC and Consistency Models", "Intermediate",
"The fundamental trade-offs between consistency, availability and latency in distributed systems, and the spectrum of consistency models from linearizable to eventual.",
r'''
## CAP theorem

In a distributed data store, you can't simultaneously guarantee all three of:

- **Consistency (C)**: every read sees the most recent write (linearizability), as if there were one copy of the data.
- **Availability (A)**: every request to a non-failed node gets a non-error response.
- **Partition tolerance (P)**: the system keeps working despite network messages being lost or delayed between nodes.

Networks do fail, so P is not optional. The real choice is: **during a partition, do you favour C or A?**

```text
   [Node A] ---X--- network partition ---X--- [Node B]
   client writes x=2 to A; another client reads x from B

   CP choice: B refuses (error/timeout) until it can confirm the latest value
   AP choice: B answers with x=1 (possibly stale); reconcile later
```

- **CP systems**: refuse some requests during partitions to stay correct. Examples: ZooKeeper, etcd, HBase, MongoDB with majority writes, a single-primary RDBMS (the minority side can't write), Spanner.
- **AP systems**: keep answering, possibly with stale or conflicting data, and reconcile later. Examples: Cassandra and DynamoDB (default configurations), DNS, CouchDB.

Common misunderstandings:
- CAP's C is not ACID's C (ACID consistency is about invariants/constraints).
- It's not "pick 2 of 3 forever". Outside partitions you can have both C and A. And many systems are tunable per request (Cassandra QUORUM vs ONE).

## PACELC: the more useful version

CAP only talks about partitions, which are rare. PACELC (Daniel Abadi) adds the everyday trade-off:

> If there is a **P**artition, choose **A** or **C**; **E**lse (normal operation), choose **L**atency or **C**onsistency.

Keeping replicas consistent requires coordination (waiting for other nodes), which costs latency even when the network is fine.

| System | P: A or C | E: L or C |
|---|---|---|
| Cassandra, DynamoDB (default) | A | L |
| MongoDB (typical) | C | C-ish (primary reads) |
| MySQL async replication + replica reads | A-ish | L |
| Spanner, CockroachDB | C | C |
| ZooKeeper/etcd | C | C |

This is what you reason about in interviews: "Feed reads can be slightly stale, so PA/EL is fine. The wallet ledger needs PC/EC."

## Consistency models (strongest to weakest)

### Linearizability (strong consistency)
Once a write completes, all subsequent reads (by anyone) see it. Behaves like a single copy. Needed for: distributed locks, leader election, unique username claims, preventing double booking at the source of truth. Cost: coordination (consensus or single leader), higher latency, reduced availability during partitions.

### Sequential consistency
All nodes see operations in the same order, but not necessarily in real-time order.

### Causal consistency
Operations that are causally related (a reply after the question it answers) are seen in order by everyone; unrelated operations may be seen in different orders. A practical sweet spot; achievable while staying available.

### Session guarantees (client-centric)
- **Read-your-writes**: you always see your own updates.
- **Monotonic reads**: you never see time go backwards.
- **Monotonic writes**: your writes are applied in order.
- **Writes-follow-reads**.
These are what users actually notice; implement via sticky routing or version tracking.

### Eventual consistency
If writes stop, all replicas eventually converge. No bound on how stale reads are in the meantime (in practice usually milliseconds to seconds). Examples: DNS propagation, Cassandra with ONE, social media like counts, S3 used to be eventually consistent for overwrites (now strongly consistent).

## Conflict resolution under eventual consistency

When replicas accept concurrent writes:
- **Last-write-wins (LWW)** by timestamp: simple, but silently drops writes and depends on clocks.
- **Version vectors / vector clocks**: detect concurrency; app or user merges (Dynamo shopping cart unions items).
- **CRDTs** (conflict-free replicated data types): counters, sets, text designed to merge automatically (used in collaborative editors, Redis Enterprise active-active).

## Choosing per feature (the senior answer)

Real systems mix models:

| Feature | Model | Why |
|---|---|---|
| Payment ledger, wallet balance | Strong (single leader/consensus, ACID) | Money must be exact |
| Seat booking / inventory decrement | Strong at the point of commit | No double booking/overselling |
| Product catalog, prices display | Eventual (cache, replicas) | Brief staleness OK; re-check at checkout |
| Likes, view counts | Eventual | Approximation acceptable |
| Chat messages order in a conversation | Causal/per-conversation ordering | Replies after messages |
| User's own profile after edit | Read-your-writes | Users notice otherwise |

Spring Boot/MySQL mapping: writing to the primary inside a `@Transactional` method and reading from the primary gives strong consistency for that data; reading from replicas or Redis gives eventual consistency.

## Interview phrasing

"During a partition, for booking I'd rather reject the request (CP) than double-book. For browsing shows and seat maps I prefer availability and low latency (AP/EL), serving cached, slightly stale availability and then validating with a strongly consistent check when the user actually locks seats."
''',
["CAP: during a network partition choose consistency or availability; P is mandatory",
 "CP examples: ZooKeeper, etcd, Spanner; AP examples: Cassandra, DynamoDB defaults",
 "PACELC adds: else, trade latency vs consistency in normal operation",
 "Linearizable = behaves like a single copy; needed for locks, booking, balances",
 "Causal and session guarantees (read-your-writes, monotonic reads) are practical middle grounds",
 "Eventual consistency: replicas converge if writes stop",
 "Conflicts: LWW (lossy), vector clocks, CRDTs",
 "Pick the consistency model per feature, not per system"],
[("Explain the CAP theorem with an example.",
 "CAP says that when a network partition splits nodes, a distributed store must choose between consistency (every read returns the latest write) and availability (every node keeps responding). Example: a booking service with replicas in two zones loses connectivity between them. If it stays available, both sides may sell the same seat; if it stays consistent, the minority side must reject bookings. Since partitions happen, P isn't optional; the choice is C vs A during a partition."),
 ("What does PACELC add to CAP?",
 "CAP only covers behaviour during partitions. PACELC says: if Partitioned, choose Availability or Consistency; Else, choose Latency or Consistency. Even with a healthy network, strong consistency requires waiting for replicas or a leader, adding latency. Cassandra is PA/EL (fast, eventually consistent by default), while Spanner is PC/EC (consistent, higher latency). It captures the everyday trade-off designers actually face."),
 ("Is MySQL CP or AP?",
 "It depends on deployment. A single primary is effectively CP: if clients can't reach the primary, writes fail. With async read replicas and reads from replicas, reads are available but can be stale, behaving AP for reads with latency preference. With semi-sync replication and controlled failover it leans CP. The point is that CAP classifications apply to configurations and operations, not to product names."),
 ("What is eventual consistency and where is it acceptable?",
 "Eventual consistency guarantees that if no new writes occur, all replicas will converge to the same value, but reads in between may be stale. It's acceptable where brief staleness doesn't cause harm: like counts, view counts, social feeds, product catalog display, search indexes, analytics. It's not acceptable for balances, inventory decrements or seat allocation at commit time."),
 ("How would you provide read-your-writes consistency with read replicas?",
 "Options: route a user's reads to the primary for a short window after they write (tracked via a timestamp in session/cookie); record the replication position (GTID) of the user's last write and only use replicas that have applied it; route reads for the user's own mutable data (profile, settings) always to the primary while serving others' data from replicas; or return the updated object in the write response and let the client cache it.")],
[DDIA, ("Brewer - CAP Twelve Years Later", "https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/"), ("Abadi - Consistency Tradeoffs in Modern Distributed Database Design (PACELC)", "https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf"), ("Jepsen - Consistency models", "https://jepsen.io/consistency")]))

topics.append(T("transactions-isolation", "Transactions, Isolation Levels and Distributed Transactions", "Advanced",
"ACID guarantees, the four isolation levels and their anomalies in MySQL, locking strategies, and how to keep data consistent across services with 2PC and sagas.",
r'''
## ACID

A transaction groups operations so they behave as one unit.

- **Atomicity**: all or nothing. If debit succeeds and credit fails, roll back the debit. (InnoDB uses an undo log.)
- **Consistency**: the database moves from one valid state to another, respecting constraints (balance >= 0, foreign keys). Partly the application's job.
- **Isolation**: concurrent transactions don't see each other's intermediate states (to a configurable degree).
- **Durability**: once committed, data survives crashes. (InnoDB redo log, `innodb_flush_log_at_trx_commit=1`.)

In Spring Boot, `@Transactional` opens a transaction on method entry and commits on return (rolls back on unchecked exceptions by default). Gotchas: self-invocation bypasses the proxy, checked exceptions don't roll back unless `rollbackFor` is set, and long transactions hold locks.

## Read anomalies

| Anomaly | What happens |
|---|---|
| **Dirty read** | T1 reads T2's uncommitted change; T2 rolls back |
| **Non-repeatable read** | T1 reads a row twice and gets different values because T2 committed an update in between |
| **Phantom read** | T1 runs the same range query twice and new rows appear (T2 inserted) |
| **Lost update** | Two transactions read-modify-write the same row; one overwrites the other |
| **Write skew** | Two transactions read overlapping data, make disjoint writes that together violate an invariant (two doctors both go off-call) |

## Isolation levels

| Level | Dirty read | Non-repeatable | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | possible | possible | possible |
| READ COMMITTED (Postgres/Oracle default) | prevented | possible | possible |
| REPEATABLE READ (**MySQL InnoDB default**) | prevented | prevented | mostly prevented* |
| SERIALIZABLE | prevented | prevented | prevented |

*InnoDB uses MVCC snapshots for plain SELECTs and **next-key locks** (record + gap locks) for locking reads, which prevent phantoms in most cases.

### MVCC (multi-version concurrency control)

Writers create new row versions; readers see a consistent snapshot without taking locks (undo log holds old versions). So in InnoDB, readers don't block writers and writers don't block readers. Under REPEATABLE READ the snapshot is taken at the first read in the transaction; under READ COMMITTED each statement gets a fresh snapshot.

## Preventing lost updates: the practical toolkit

Example: two requests both try to buy the last unit of stock.

1. **Atomic update** (best when possible):
```sql
UPDATE inventory SET stock = stock - 1
WHERE product_id = 42 AND stock >= 1;   -- check rows affected == 1
```
2. **Pessimistic locking**: `SELECT ... FOR UPDATE` locks the row until commit. In JPA: `@Lock(LockModeType.PESSIMISTIC_WRITE)`. Simple and correct, but holds locks; risk of deadlocks (InnoDB detects them and rolls one back; retry).
3. **Optimistic locking**: version column; update fails if someone else changed it.
```sql
UPDATE account SET balance = 900, version = 8 WHERE id = 1 AND version = 7;
```
In JPA, add `@Version`; you get `OptimisticLockException` on conflict and retry. Great when conflicts are rare.
4. **SERIALIZABLE** isolation or explicit constraints (unique index to prevent double booking: `UNIQUE(show_id, seat_id)`).

Use `SELECT ... FOR UPDATE SKIP LOCKED` to build job queues or to let concurrent users grab different available seats/coupons without waiting.

## Distributed transactions

Once data lives in different databases or services (Order service DB, Payment service DB, Inventory service DB), a single ACID transaction is no longer available.

### Two-phase commit (2PC)

A coordinator asks all participants:
1. **Prepare**: "Can you commit?" Each participant writes changes durably, locks resources, votes yes/no.
2. **Commit/Abort**: if all voted yes, coordinator tells everyone to commit; otherwise abort.

```text
Coordinator --prepare--> [DB A] yes
            --prepare--> [DB B] yes
            --commit---> [DB A], [DB B]
```

Problems: **blocking** (if the coordinator crashes after prepare, participants hold locks indefinitely), latency of extra round trips, every participant must support XA, poor fit for microservices over HTTP. Used inside databases (Spanner, CockroachDB combine 2PC with consensus to remove the blocking issue) and in XA setups, rarely across microservices.

### Saga pattern

A long business transaction split into a sequence of **local transactions**, each publishing an event that triggers the next. If a step fails, run **compensating transactions** to undo prior steps.

Order flow:
```text
1. Order Service: create order (PENDING)
2. Payment Service: charge customer       -- compensate: refund
3. Inventory Service: reserve stock       -- compensate: release stock
4. Order Service: mark CONFIRMED
If step 3 fails -> refund payment -> mark order CANCELLED
```

Two styles:
- **Choreography**: services react to each other's events via Kafka. Loosely coupled, but flow is implicit and hard to trace with many steps.
- **Orchestration**: a central orchestrator (a state machine, e.g., Temporal, Camunda, or a custom Spring service) tells each service what to do. Easier to understand and monitor.

Saga caveats:
- No isolation: other transactions can see intermediate states (order PENDING). Use semantic locks (status fields), and design UI around it.
- Compensations must be **idempotent** and always eventually succeed (retry).
- Use the **transactional outbox** to publish events reliably with the local DB change.

### Other techniques

- **Reservation / TCC (Try-Confirm-Cancel)**: reserve resources (hold seats for 10 minutes), confirm on payment, cancel on timeout.
- **Idempotency keys** so retries don't double-charge.
- **Reconciliation jobs**: periodically compare ledgers with payment gateway reports and fix drift. Every payment system has one.

## Interview phrasing

"Inside the inventory service I decrement stock with a conditional atomic UPDATE, so no overselling. Across order, payment and inventory services I use an orchestrated saga with an outbox for events; payment refund and stock release are the compensations, all idempotent. I avoid 2PC because it blocks on coordinator failure and couples services."
''',
["ACID: atomicity (undo log), consistency, isolation, durability (redo log)",
 "Anomalies: dirty read, non-repeatable read, phantom, lost update, write skew",
 "MySQL InnoDB default is REPEATABLE READ with MVCC and next-key locks",
 "Prevent lost updates: atomic conditional UPDATE, SELECT FOR UPDATE, @Version optimistic locking",
 "2PC: prepare then commit; blocking if coordinator fails",
 "Saga: local transactions + compensations; choreography vs orchestration",
 "Use outbox + idempotency for reliable sagas",
 "Spring @Transactional pitfalls: self-invocation, checked exceptions"],
[("What isolation level does MySQL use by default and what does it prevent?",
 "InnoDB defaults to REPEATABLE READ. Plain SELECTs read from an MVCC snapshot taken at the transaction's first read, so dirty and non-repeatable reads are prevented. Locking reads and writes use next-key locks (record plus gap locks), which prevent most phantom reads. It doesn't automatically prevent lost updates in read-modify-write code; for that you need atomic updates, SELECT FOR UPDATE, or optimistic locking."),
 ("Optimistic vs pessimistic locking: when to use which?",
 "Pessimistic locking (SELECT ... FOR UPDATE) locks rows when read, so other writers wait; it suits high-contention cases like the last seats in a flash sale, but holds locks and can deadlock. Optimistic locking uses a version column and checks it at update time, retrying on conflict; it suits low-contention cases like profile edits, giving better throughput. In JPA these are @Lock(PESSIMISTIC_WRITE) and @Version respectively."),
 ("Explain the saga pattern with an example.",
 "A saga breaks a distributed transaction into local transactions with compensations. For an order: the order service creates a PENDING order, payment service charges the card, inventory reserves stock, then the order is confirmed. If inventory fails, the saga runs compensations: refund the payment and cancel the order. It can be choreographed through events or orchestrated by a coordinator. Steps must be idempotent and events published reliably via an outbox."),
 ("Why is 2PC rarely used across microservices?",
 "2PC requires all participants to hold locks between prepare and commit and depends on a coordinator. If the coordinator crashes after prepare, participants are stuck holding locks (blocking). It adds round trips, couples services' availability together (any participant down blocks everyone), and requires XA support, which REST services and many brokers lack. Sagas with eventual consistency trade isolation for availability and loose coupling."),
 ("How do you prevent two users from booking the same seat?",
 "Enforce it at the database: a unique constraint on (show_id, seat_id) in the bookings table, or a conditional update like UPDATE seats SET status='HELD', held_by=? WHERE id=? AND status='AVAILABLE' and check the affected row count. Only one transaction can succeed. Add a hold with expiry so unpaid holds are released, and use idempotency keys on the booking API to make retries safe."),
 ("What are common @Transactional pitfalls in Spring?",
 "Calling a @Transactional method from another method in the same class bypasses the proxy, so no transaction starts. By default only unchecked exceptions trigger rollback; checked exceptions need rollbackFor. Making remote HTTP calls inside a transaction holds DB locks and connections for long periods. Transactions on private methods don't apply. Also, readOnly=true is a hint, useful for routing to replicas.")],
[DDIA, ("MySQL 8.0 Reference - Transaction Isolation Levels", "https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html"), ("microservices.io - Saga pattern", "https://microservices.io/patterns/data/saga.html"), ("Vlad Mihalcea - Optimistic vs pessimistic locking", "https://vladmihalcea.com/optimistic-vs-pessimistic-locking/")]))

dump("sd_part2.json", topics)
