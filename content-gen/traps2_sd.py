from traps2_common import T

A = "system-design"

SNOWFLAKE = """public final class Snowflake {
    private static final long EPOCH = 1704067200000L;  // 2024-01-01T00:00:00Z
    private final long workerId;                        // 0..1023, unique per running instance
    private long lastMs = -1L, seq = 0L;

    public Snowflake(long workerId) {
        if (workerId < 0 || workerId > 1023) throw new IllegalArgumentException("workerId");
        this.workerId = workerId;
    }

    public synchronized long nextId() {
        long now = System.currentTimeMillis();
        if (now < lastMs) throw new IllegalStateException("clock moved backwards");
        if (now == lastMs) {
            seq = (seq + 1) & 4095;                     // 12-bit sequence
            if (seq == 0)                               // 4096 ids used this ms: wait for the next ms
                while ((now = System.currentTimeMillis()) <= lastMs) { }
        } else {
            seq = 0;
        }
        lastMs = now;
        return ((now - EPOCH) << 22) | (workerId << 12) | seq;   // 41 | 10 | 12 bits
    }
}"""

HOTKEY = """// Read path: local cache first, then one of N replicas of the hot key
static final int COPIES = 8;

String readHot(String key) {
    String v = localCache.getIfPresent(key);            // Caffeine, TTL ~2s, absorbs most traffic
    if (v != null) return v;
    int copy = ThreadLocalRandom.current().nextInt(COPIES);
    v = redis.get(key + "#" + copy);                    // copies hash to different nodes
    if (v == null) v = loadOnce(key);                   // single-flight DB load + write all copies
    localCache.put(key, v);
    return v;
}"""

TRAPS = [
    T("trap-system-design-jump-to-architecture", A, "Drawing boxes before requirements and numbers", "Basic", "Very common",
      """"Design a URL shortener." Within the first two minutes the candidate says: "We'll have an API gateway, five microservices, Kafka, Cassandra, a Redis cluster and Kubernetes." The interviewer asks, "Why Kafka?" and the candidate can't connect it to anything.

What should the first 5-8 minutes look like instead?""",
      "Show breadth fast by naming the standard big-tech stack; requirements can be figured out along the way.",
      """Candidates memorise reference architectures from videos and fear that silence looks like not knowing. So they show tools instead of reasoning. But interviewers score **requirement gathering, estimation and justified trade-offs**. A component with no requirement behind it is a red flag, not a bonus. Over-building also eats the time you need for the deep dive, which is where senior signal is earned. Service-company engineers who have never chosen an architecture are especially prone to reciting one.""",
      """Spend the first few minutes on:

1. **Functional scope**: 3-4 core features, and say what you are cutting ("custom aliases yes, analytics later").
2. **Non-functional needs**: latency targets, availability vs consistency, durability, read:write ratio.
3. **Back-of-envelope numbers that drive decisions**: QPS (average and peak), storage over 5 years, bandwidth.
4. **API and data model**, then the **simplest design that meets the numbers**: often one service and one database.
5. **Deep dive** where the numbers say it hurts: hot reads → cache, ID generation, partitioning.

Every box must be justified by a requirement: "reads are 100x writes and p99 should be under 50 ms, so I put a cache in front of the database." Start simple and evolve. "We don't need Kafka at 40 writes/sec" is a *strong* statement, not a weak one.""",
      "Open with \"Let me spend five minutes on requirements and scale, then design to those numbers\", and later point back to them when you justify each component.",
      fix="""```text
URL shortener: numbers first
100M new URLs/month   -> 100M / 2.6M s ≈ 40 writes/s avg (≈ 200/s peak)
Read:write = 100:1    -> ≈ 4,000 reads/s avg (≈ 20k/s peak)
Row ≈ 500 B, 5 years  -> 100M × 60 = 6B rows × 500 B ≈ 3 TB
Decisions: a single primary handles the writes; reads need a cache (hot links);
           3 TB needs partitioning eventually -> key = short code; 7 base62 chars = 3.5 trillion codes
```""",
      askedAt=["Amazon", "Google", "Flipkart", "Razorpay"]),

    T("trap-system-design-cache-aside-race", A, "Cache-aside write ordering and stale cache", "Advanced", "Very common",
      """Product prices are read through Redis (cache-aside: on a miss, read the DB and populate the cache). When a price changes, which ordering is **safest**?""",
      "Update the DB and then write the new value into the cache, so the cache is always fresh.",
      """"Write the new value to the cache" feels both efficient and fresh, and candidates reason about one request at a time. The bugs only appear with **two concurrent requests** interleaving, which nobody draws on the whiteboard. Another common blind spot: people forget the delete must run **after the transaction commits**. In Spring, an eviction inside a `@Transactional` method runs before commit, so a concurrent reader can repopulate the cache with the old row.""",
      """**Update the DB, then delete the key** (with a TTL on every entry as a safety net).

Why the others fail:
- **DB then set cache**: writer 1 sets the DB to 10, writer 2 sets it to 20, writer 2 caches 20, then writer 1 caches 10. The cache is stale *indefinitely*.
- **Delete then update DB**: between the delete and the commit, a reader misses, reads the *old* row and puts it back in the cache.
- **Cache then DB**: if the DB write fails, the cache serves a price that never existed.

Delete-after-commit still has a rare race: a slow reader loads the old value before the commit and writes it after the delete. Narrow it with short TTLs, a delayed second delete, or versioned writes ("set only if newer"). For strong guarantees, drive invalidation from the DB's change log (CDC, for example Debezium on the MySQL binlog), so an app crash between commit and delete cannot leave the cache stale.""",
      "Name the exact interleaving that breaks each option; that is what separates a senior answer from \"invalidate the cache\".",
      options=[
          "Update cache, then update DB",
          "Update DB, then set the new value in the cache",
          "Delete the cache key, then update DB",
          "Update DB (commit), then delete the cache key, with a TTL as a safety net",
      ], answer=3,
      fix="""```text
write(price):
  BEGIN; UPDATE products SET price = ? WHERE id = ?; COMMIT;
  after commit -> DEL product:{id}            (Spring: @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT))
  optional     -> schedule a second DEL ~1s later (closes the slow-reader race)
read(id):
  v = GET product:{id}
  if miss: v = SELECT ...; SET product:{id} v EX 300   (TTL bounds any staleness)
```""",
      askedAt=["Amazon", "Flipkart", "Swiggy", "PhonePe"]),

    T("trap-system-design-hot-key", A, "Hot key / celebrity problem", "Advanced", "Common",
      """Your Redis cache is sharded across 10 nodes by key hash. A celebrity posts, and the key `post:9001` suddenly gets **500k reads/sec**. One node hits 100% CPU while the other nine are idle. What do you do?""",
      "Add more Redis nodes or switch to consistent hashing so the load spreads out.",
      """Sharding and consistent hashing spread **keys**, so candidates assume they spread **load**. But a single key always hashes to a single node, so adding nodes changes nothing for that key. People also forget the follow-on failure: when that hot entry expires, thousands of requests miss at once and stampede the database. Interviewers use "celebrity" and "flash sale" prompts specifically to test whether you know this.""",
      """First **detect** it: per-key request sampling, Redis `--hotkeys` (with an LFU eviction policy), or client-side counters. Then apply one or more mitigations:

1. **Local in-process cache** (Caffeine, 1-5 s TTL) on every app server. A few seconds of staleness on a like count or post body is fine, and it absorbs most reads before they reach Redis.
2. **Replicate the hot key**: store `post:9001#0..#7` on different nodes. Reads pick a random copy, and writes update all copies.
3. **Read replicas** for the overloaded shard.
4. **Request coalescing (single-flight)**: on a miss, only one request loads from the DB while the others wait for its result.
5. For **hot writes** (a counter on a viral post), split into N sub-counters and sum on read.

For feeds, use **hybrid fan-out**: push posts to followers' timelines for normal users, but pull celebrity posts at read time.""",
      "Say \"one key always lives on one shard, so more shards won't help\" before proposing fixes; it shows you understand the root cause.",
      fix=f"""```java
{HOTKEY}
```""",
      askedAt=["Meta", "Twitter/X", "ShareChat", "Hotstar"]),

    T("trap-system-design-shard-key", A, "Choosing a shard key that creates hotspots", "Intermediate", "Very common",
      """An `orders` table has 2 billion rows and is growing. The dominant queries are "show **my** orders" (by user) and "get order by id". Which shard key is the best default?""",
      "Shard by `created_at` (one shard per month), because old data can then be archived easily.",
      """Time ranges and auto-increment ranges *feel* natural because data is naturally ordered that way and archival looks easy. Candidates miss that **all new writes land on the newest shard**, so one shard is hot while the others idle. Others pick a low-cardinality or skewed key like country (the India shard is huge) without checking the distribution. The real skill being tested is starting from the **access patterns**, not from the data.""",
      """**`hash(user_id)`**. A user's orders live together, so "my orders" is a single-shard query, and hashing spreads writes evenly.

Then handle the other access paths explicitly:
- **Get by order id**: embed the shard (or user id bits) inside the order id, or keep a small `order_id → user_id` lookup table.
- **Queries by merchant or date range** become scatter-gather across shards. Serve them from a separate read model (merchant-partitioned copy fed by CDC or Kafka) or a search/analytics store.
- **Co-locate related tables** (order_items, payments) on the same key to avoid cross-shard joins and distributed transactions.
- **Plan for resharding**: map keys to many *logical* shards (for example 1024) and logical shards to fewer physical nodes, so growth means moving whole logical shards, not rehashing every row.

Mention the trade-off: one huge customer (a B2B merchant) can still create a hotspot.""",
      "Before naming a shard key, list the top 2-3 queries; the right key is the one that keeps the most frequent query on one shard.",
      options=[
          "`created_at` range (one shard per month)",
          "`hash(user_id)`",
          "`country`",
          "Ranges of the auto-increment `order_id`",
      ], answer=1,
      fix="""```text
logical = murmur3(user_id) % 1024          -- fixed forever
physical = shard_map[logical]              -- small config table, changes during rebalancing
order_id = snowflake id with logical shard in its low bits  -> get-by-id needs no lookup
merchant dashboards -> CDC -> separate store partitioned by merchant_id
```""",
      askedAt=["Flipkart", "Amazon", "Razorpay", "Meesho"]),

    T("trap-system-design-global-id", A, "Generating IDs after sharding", "Intermediate", "Common",
      """You have sharded MySQL. What is the best default for generating `order_id`, given that it must be unique across shards, fit in a `BIGINT` and be roughly time-ordered?""",
      "Keep `AUTO_INCREMENT`, or use a random `UUID.randomUUID()` string as the primary key.",
      """Auto-increment "just works" on one database, so candidates forget that two shards will both hand out id 1001. Random UUIDs solve uniqueness, so they stop there, without knowing how InnoDB stores rows: the primary key **is** the clustered index. Random keys scatter inserts across pages, and every secondary index stores a copy of the PK. Interviewers at Java/MySQL shops probe exactly this.""",
      """A **Snowflake-style 64-bit id**: 41 bits of milliseconds since a custom epoch, 10 bits of worker id, and 12 bits of sequence. That gives 4,096 ids per ms per worker, roughly time-ordered values (good B-tree locality), and a `BIGINT`. The edge cases to mention are the clock moving backwards (refuse or wait) and assigning unique worker ids (config, ZooKeeper or a DB lease).

Why not the others:
- **Per-shard AUTO_INCREMENT** collides. Offsets (`auto_increment_increment`) work but freeze the shard count.
- **Random UUIDv4 as a VARCHAR(36) PK** causes random inserts → page splits and buffer-pool misses, plus a 36-byte PK copied into every secondary index.
- **`MAX(id) + 1`** races under concurrency.

Alternatives: **UUIDv7** (RFC 9562, time-ordered, stored as `BINARY(16)`), or **segment allocation**, where each app instance reserves ranges of 1,000 ids from a DB row.""",
      "Mention the InnoDB clustered-index cost of random UUIDs; it shows you know the database, not just the buzzword.",
      options=[
          "Per-shard `AUTO_INCREMENT`",
          "Random UUIDv4 stored as `VARCHAR(36)` primary key",
          "Snowflake-style 64-bit id (timestamp | worker | sequence), or UUIDv7",
          "`SELECT MAX(id) + 1` before each insert",
      ], answer=2,
      fix=f"""```java
{SNOWFLAKE}
```""",
      askedAt=["Twitter/X", "Flipkart", "Swiggy"]),

    T("trap-system-design-just-add-kafka", A, "\"Just add Kafka\" without delivery semantics", "Intermediate", "Very common",
      """Order service → notification service. The candidate says: "I'll put Kafka in between, now it's reliable and decoupled." The interviewer asks:

- "The consumer sends the SMS, then crashes before committing the offset. What happens?"
- "Do events for one order arrive in order?"
- "One message always throws. Then what?"
- "How does the event get into Kafka if the order DB commit succeeds but the publish fails?\"""",
      "Kafka is durable and decoupled, so once a message is in the queue reliability is solved.",
      """A queue is a component, not a guarantee. Candidates name-drop Kafka because it appears in every reference design, but they can't state its **delivery semantics, ordering scope or failure handling**. Interviewers ask these follow-ups precisely because the answers reveal whether you have run a consumer in production or only drawn one. "It's reliable" without specifics reads as memorised.""",
      """A queue moves the problem; you still have to specify:

- **Delivery**: committing offsets after processing gives **at-least-once**, so the SMS above is sent twice on restart. The consumer must be **idempotent** (dedupe on event id, or a unique constraint on `(order_id, notification_type)`).
- **Ordering**: only within a partition. Use `orderId` as the message key so one order's events stay ordered. There is no global order.
- **Poison messages**: bounded retries with backoff (retry topic), then a **dead-letter topic** with alerting and a replay tool. Never block the partition forever.
- **Producer side**: `acks=all` plus the idempotent producer. And the DB-commit-then-publish gap is the **dual-write problem**, solved with an outbox.
- **Operations**: consumer lag alerts, retention and replay, schema evolution.

Also ask whether async is right at all: if the user needs the result now, a queue only adds latency.""",
      "Whenever you add a queue, say in one breath: \"at-least-once, keyed by X for ordering, idempotent consumer, DLQ after N retries.\"",
      fix="""```text
Queue checklist (say it every time you draw one)
1. Semantics : at-least-once (commit after processing) -> idempotent consumer
2. Ordering  : key = aggregate id (orderId); order only within a partition
3. Failure   : retry with backoff -> DLQ -> alert -> replay tool
4. Producer  : acks=all, enable.idempotence=true, outbox for DB + event atomicity
5. Ops       : consumer lag SLO, retention for replay, schema compatibility rules
```""",
      askedAt=["Swiggy", "Zomato", "Uber", "Razorpay"]),

    T("trap-system-design-read-your-writes", A, "Read-your-writes with async replicas", "Intermediate", "Common",
      """MySQL primary + 2 async read replicas; all reads go to replicas. A user changes their display name, the page reloads and shows the **old** name; a second reload shows the new one. Support files it as "save is broken". What is the best fix?""",
      "Put a Redis cache in front of the replicas, or make replication synchronous.",
      """Replication lag is usually milliseconds, so candidates assume replicas are "basically consistent". Under load or long transactions, lag spikes to seconds. Making every replica synchronous sounds rigorous, but it ties write latency and availability to the slowest replica. Adding a cache usually makes staleness *worse*. The skill being tested is naming the consistency model the user expects (**read-your-writes**) and providing it narrowly, only where it matters.""",
      """Give **read-your-writes** consistency to the user who wrote, without sending everyone to the primary:

1. **Read your own data from the primary**: profile or settings pages are low volume, so route them to the primary.
2. **Sticky window**: after a write, store `lastWriteAt` in the session or a cookie and route that user's reads to the primary for a few seconds.
3. **Position tracking**: record the write's GTID (MySQL) or LSN (Postgres), and read from a replica only once it has applied that position. Otherwise fall back to the primary.
4. **Return the updated resource in the write response** and update client state, so the UI never needs to re-read immediately.

Related guarantee: **monotonic reads**. Pin a user to one replica so successive reads never go "back in time" when replicas have different lag. Monitor replica lag and take lagging replicas out of rotation.""",
      "Name the guarantee (\"read-your-writes\", \"monotonic reads\") before the fix; vocabulary signals seniority here.",
      options=[
          "Make all replicas synchronous.",
          "Route the writer's reads of their own recent data to the primary (sticky window or GTID/LSN check) and return the updated object in the write response.",
          "Add a Redis cache in front of the replicas.",
          "Buy bigger replicas so lag becomes zero.",
      ], answer=1,
      askedAt=["Amazon", "LinkedIn", "Atlassian"]),

    T("trap-system-design-counting-at-scale", A, "COUNT(*) on every read for likes and views", "Intermediate", "Common",
      """Each post in the feed shows a like count. The candidate's design runs `SELECT COUNT(*) FROM likes WHERE post_id = ?` for every post on every feed render. There are 20 posts per feed and **50k feed loads/sec**. What is wrong, and what would you do?""",
      "Add an index on `post_id` and COUNT(*) will be fast enough.",
      """An index makes one count fast, so it feels solved. But the work still grows with the number of likes: counting 2 million index entries for a viral post on every view is about a million times more work than reading one number. Candidates also jump straight to "Redis counter" without saying what keeps it correct, how it survives restarts, or what happens when one row becomes a write hotspot.""",
      """50k × 20 = **1 million counts/sec**, and each one scans index entries proportional to the like count. Instead, **precompute** the count:

- Keep `likes(user_id, post_id)` with a UNIQUE constraint as the source of truth. It makes liking idempotent.
- Maintain a counter: increment `post_counters` **only if the insert actually happened**. For viral posts, one counter row becomes a lock hotspot, so use **N sharded counter rows** (pick one at random on write, SUM on read), or `INCR` in Redis and flush to the DB periodically.
- Accept **eventual consistency** for display ("1.2M" does not need to be exact), and run a periodic reconciliation job that recomputes counts from the source table.
- For **unique** counts (unique viewers), use HyperLogLog: about 12 KB per key with roughly 0.81% error, instead of storing every viewer id.

Cache the rendered counts alongside the post object.""",
      "Multiply it out loud (\"50k × 20 = 1M counts/sec\"); the number alone justifies precomputation.",
      fix="""```sql
-- source of truth, idempotent like
INSERT IGNORE INTO likes(user_id, post_id) VALUES (?, ?);      -- UNIQUE(user_id, post_id)
-- only if a row was inserted (affected rows = 1):
UPDATE post_counters SET likes = likes + 1
 WHERE post_id = ? AND shard = ?;                              -- shard = random 0..15
-- read path (cache the result for a few seconds)
SELECT SUM(likes) FROM post_counters WHERE post_id = ?;
```""",
      askedAt=["Meta", "Instagram", "ShareChat", "Dream11"]),
]

CHECKS = [
    {"name": "sd-snowflake", "lang": "java", "code": "import java.util.*;\nimport java.util.concurrent.*;\npublic class Main {\n" +
     SNOWFLAKE.replace("public final class", "static final class").replace("public Snowflake", "Snowflake").replace("public synchronized", "synchronized") + """
  public static void main(String[] a) throws Exception {
    Snowflake s = new Snowflake(7);
    long prev = -1; HashSet<Long> set = new HashSet<>();
    for (int i = 0; i < 300_000; i++) { long id = s.nextId(); if (id <= prev) throw new RuntimeException("not increasing"); prev = id; set.add(id); }
    ExecutorService ex = Executors.newFixedThreadPool(4); Set<Long> all = ConcurrentHashMap.newKeySet();
    List<Future<?>> fs = new ArrayList<>(); for (int t = 0; t < 4; t++) fs.add(ex.submit(() -> { for (int i = 0; i < 50_000; i++) all.add(s.nextId()); }));
    for (Future<?> f : fs) f.get(); ex.shutdown();
    System.out.println("unique " + set.size() + " " + all.size() + " worker=" + ((prev >> 12) & 1023) + " positive=" + (prev > 0));
  }
}""", "expect": ["unique 300000 200000 worker=7 positive=true"]},
    {"name": "sd-hotkey", "lang": "java", "code": """import java.util.*;
import java.util.concurrent.*;
public class Main {
  interface Cache { String getIfPresent(String k); void put(String k, String v); }
  interface Redis { String get(String k); }
  static Map<String, String> local = new HashMap<>(), remote = new HashMap<>();
  Cache localCache = new Cache() { public String getIfPresent(String k) { return local.get(k); } public void put(String k, String v) { local.put(k, v); } };
  Redis redis = remote::get;
  String loadOnce(String key) { for (int i = 0; i < COPIES; i++) remote.put(key + "#" + i, "v1"); return "v1"; }
""" + "\n".join("  " + l for l in HOTKEY.splitlines()) + """
  public static void main(String[] a) { Main m = new Main(); System.out.println(m.readHot("post:9001") + " " + m.readHot("post:9001") + " " + remote.size()); }
}""", "expect": ["v1 v1 8"]},
]
