"""Senior SD chunk 4: leaderboard & top-K trending, flash sale inventory."""
from sdsenior_common import *

topics = []

# ---------------------------------------------------------------- 10
topics.append(T("leaderboard-top-k-trending", "Real-Time Leaderboard & Top-K Trending", 10, "case-study", "Intermediate",
"Two ranking problems in one round: an exact real-time leaderboard on Redis sorted sets (rank, neighbours, hot keys, durability) and approximate top-K trending over sliding windows with count-min sketch and stream processing.",
r'''
## 1. Requirements

Interviewers often merge these two prompts: "Design the leaderboard for a fantasy-cricket contest" and "Show trending searches or hashtags".

**Functional**
- Leaderboard: update a user's score as match events arrive. Get the top 100, a user's own rank, and the 5 users above and below them. Support per-contest, daily, weekly and all-time boards.
- Trending: the top 50 searched terms or hashtags for the last 5 min, 1 h and 24 h, per region.

**Non-functional**
- 50M users in the largest contest. 20k score updates/s on average, **200k/s peak** when a wicket falls and every team's points change.
- Top-100 reads at 200k QPS, rank reads under 50 ms, scores visible within 1-2 s.
- Leaderboard ranks must be **exact** (prizes depend on them). Trending can be **approximate**, with a freshness of about 1 minute.

## 2. Estimates

- A sorted set entry costs roughly 80-100 B (member, score, skip-list and hash overhead), so 50M members is about **5 GB**. Memory fits on one Redis node. **CPU on a single key** is the real limit, because a sorted set lives on one shard and Redis runs commands on a single thread (about 100k+ simple ops/s).
- Trending input of 1M events/s, with maybe 100M distinct terms a day. An exact hash map of counts would be tens of GB per window. A count-min sketch with 5 rows × 2^20 counters × 4 B is **20 MB**.

## 3. API

```text
POST /v1/leaderboards/{lbId}/scores     {"userId":"u9","delta":12,"eventId":"m77-ov14.3"}
GET  /v1/leaderboards/{lbId}/top?limit=100
GET  /v1/leaderboards/{lbId}/users/{userId}?neighbors=5   -> {rank, score, above[], below[]}
GET  /v1/trending?window=1h&region=IN&k=50                -> [{term, score}], asOf
```

## 4. Data model

```text
Redis   ZSET  lb:{contest:991}      member=userId  score=compositeScore
        HASH  lbuser:{contest:991}  userId -> display name, team (for rendering top-100)
MySQL   score_events(event_id PK, contest_id, user_id, delta, created_at)   -- source of truth
        user_scores(contest_id, user_id, points, achieved_at, PRIMARY KEY(contest_id,user_id))
```

**Ties**: the user who reached the score first should rank higher. Encode a composite score such as `points * 10^7 + (MAX_SECONDS - secondsSinceContestStart)`. Keep it under 2^53, because Redis scores are IEEE doubles and larger integers lose precision.

## 5. High-level design

```text
LEADERBOARD
 Match events -> [Points calculator] -> Kafka score-events (key = contestId:userId)
     -> [Score service x N]: dedupe eventId (DB unique) -> update user_scores -> ZINCRBY (pipelined)
     -> Redis Cluster (ZSET per contest/shard) <- [Leaderboard API] <- micro-cache top-100 (1s)
 [Rebuilder]: recreates a ZSET from user_scores if Redis loses it

TRENDING
 Search/post events -> Kafka (key = term) -> [Flink: per-minute counts per key + CMS for long tail]
     -> each task emits local top-K per minute -> [Merger] -> trending:{region}:{window} in Redis
     -> Trending API (CDN cache 30s, returns asOf)
```

## 6. Deep dives

### 6.1 Sorted set operations

- `ZINCRBY lb:{c} 12 u9`: O(log N)
- `ZREVRANGE lb:{c} 0 99 WITHSCORES`: top 100 in O(log N + 100)
- `ZREVRANK lb:{c} u9`: the user's rank in O(log N), then `ZREVRANGE lb:{c} r-5 r+5` for neighbours

The same queries in MySQL (`ORDER BY points DESC LIMIT 100`) are fine with an index. Rank, though, is `COUNT(*) WHERE points > ?`, which scans up to N index entries per request, and that is why sorted sets win.

### 6.2 The hot-key problem at 200k updates/s

One contest means one key on one shard. Options, in the order I'd apply them:

1. **Coalesce writes**: the score service aggregates deltas per user over 200-500 ms windows and pipelines one `ZINCRBY` per user. A wicket produces one update per team, not one per event.
2. **Micro-cache reads**: everyone sees the same top 100, so cache it in the API tier for 1 s. 200k QPS becomes about one Redis call per second per API node.
3. **Shard the board**: split users across N sorted sets by `hash(userId) % N` on different shards. Top 100 = fetch the top 100 from each shard and merge (exact). A user's rank = 1 + the sum over shards of `ZCOUNT shard (myScore +inf` (N calls, each O(log n)).
4. **Approximate the tail**: for user 31,456,789, "top 63%" is as useful as an exact rank. Keep a score histogram (bucket counts) and compute exact ranks only for the top 10k.

### 6.3 Durability and correctness

Redis is a **derived view**. The source of truth is `score_events` and `user_scores` in MySQL (or a compacted Kafka topic). Score updates are idempotent by `eventId`: the unique insert happens first, and Redis is updated only if the insert succeeds. If a Redis node fails and its replica lost the last few writes, a rebuilder reloads the contest's sorted set from `user_scores`. **Prize settlement always runs on the database**, never on Redis.

### 6.4 Time-windowed boards

Use one key per period (`lb:daily:2026-10-09`) with a TTL. A weekly board computed with `ZUNIONSTORE` over 7 daily keys is expensive for 50M members. It's cheaper to write each update to both the daily and weekly keys.

### 6.5 Top-K trending

Exact counting of every term isn't needed. Two techniques:

- **Partition by key**: Kafka and Flink `keyBy(term)` put each term on exactly one task, so that task's count is exact. Each task emits its local top K per minute, and **merging local top-Ks is exact because no key is split across tasks**. With random partitioning, the merge would be wrong.
- **Count-min sketch** for very high cardinality: d hash rows of w counters. An increment touches one counter per row, and the estimate is the **minimum** across rows. It can only **overestimate**, with error at most εN when w ≈ e/ε. Pair it with a min-heap of the K current candidates. Sketches of the same shape **merge by adding matrices**, so a 1-hour window is the sum of 60 per-minute sketches kept in a ring buffer. Redis Stack has `CMS.*` and `TOPK.*` commands for smaller setups.

**Trending isn't the same as popular.** "Weather" is always popular. Rank by velocity: the current window's count against a baseline (the same hour last week, or an exponentially decayed average), for example `(current - baseline) / sqrt(baseline + 1)`. Add a minimum count threshold, plus bot and spam filtering before counting.

Windows: tumbling 1-minute buckets are simple. A sliding hour is the sum of the last 60 buckets: add the newest, subtract the expired one. A Flink window sliding every minute over 24 hours would duplicate state enormously, so use per-minute buckets plus rollups instead.

### 6.6 Failure paths

- Flink checkpoints its state to S3. After a crash it restores and replays Kafka from the checkpointed offsets.
- Late events: a 1-minute watermark allowance, after which they are dropped and counted in a metric.
- A lagging pipeline means stale trending. The API returns `asOf`, and the UI hides the module if data is older than 10 minutes.

## 7. Observability

- Score freshness: event time to visible in Redis, p99 (SLO under 2 s).
- Dedupe hits, Kafka consumer lag in seconds, Redis CPU and ops per shard, and hot-key detection (`redis-cli --hotkeys`, or proxy metrics).
- **Correctness audit**: every few minutes, recompute the top 100 from MySQL and diff it with Redis. Any mismatch alerts.
- Trending: checkpoint duration and failures, watermark lag, and the age of the published trending list.

## 8. Trade-offs

- Exact vs approximate: exact for prize ranks, approximate for trending and long-tail ranks.
- One sorted set (simple, hot) vs sharded sets (scales, needs scatter-gather for rank).
- Redis CMS/TOPK (simple, limited windowing and durability) vs Flink (exact per key, checkpointed, more to operate).
- A database-only leaderboard is fine below about 1M users and modest QPS. Say so before reaching for Redis.
''',
[
 "Redis sorted sets give O(log N) updates, top-N and rank. Rank in SQL is COUNT(*) WHERE score > x, which degrades with N.",
 "One sorted set lives on one shard and Redis is single-threaded, so CPU on the hot key is the limit, not memory (50M members is about 5 GB).",
 "Scale the hot board by coalescing deltas, micro-caching the shared top 100, sharding by user with scatter-gather merge, and approximating long-tail ranks.",
 "Break ties with a composite score (points plus earliest time), kept under 2^53 for double precision.",
 "Redis is a derived view: idempotent event-ID writes to MySQL first, a rebuilder for lost data, and prize settlement from the database.",
 "Top-K: partition by key so each task's counts are exact and local top-Ks merge exactly. Use a count-min sketch (overestimates only, mergeable) for huge cardinality.",
 "Trending means velocity against a baseline, with spam filtering and minimum thresholds. Sliding windows are built from per-minute buckets.",
 "Monitor freshness, consumer lag, hot keys and a periodic Redis-vs-DB top-100 audit, and return asOf for trending."
],
[
 ("How do you get a user's rank among 50 million users in milliseconds?",
  r'''Keep scores in a Redis sorted set: `ZREVRANK` returns the rank in O(log N) using the skip list, and `ZREVRANGE` around that rank returns neighbours. In MySQL, rank means counting all rows with a higher score, which grows with N and gets hammered at scale. If the board is sharded across N sets, rank is 1 plus the sum of `ZCOUNT` of higher scores in each shard, which is N O(log n) calls. For users deep in the tail, I'd show a percentile from a score histogram instead of an exact rank.'''),
 ("A single contest receives 200k score updates a second and its Redis key is hot. What do you do?",
  r'''First reduce writes: the score service coalesces deltas per user over a few hundred milliseconds and pipelines one ZINCRBY per user, which cuts updates sharply during bursts. Second, reads: the top 100 is identical for everyone, so micro-cache it in the API for one second. If it's still too hot, shard the contest across several sorted sets on different Redis shards by user hash. Top-N becomes a merge of each shard's top N, and rank sums ZCOUNTs across shards. Long-tail ranks can be approximate.'''),
 ("Design top-K trending hashtags for the last hour at 1 million events a second.",
  r'''Events go to Kafka keyed by hashtag, and a Flink job keyed by hashtag keeps per-minute counts, so each tag's count is exact within one task. Each task emits its local top K every minute, and a merger combines them. That's exact because keys aren't split across tasks. The hour view sums the last 60 minute-buckets. For trending rather than popular, I score velocity against a baseline and filter spam. If the key space is too large for exact state, a count-min sketch plus a heap bounds memory while only overestimating counts.'''),
 ("The Redis node holding a contest's leaderboard fails. What happens?",
  r'''Redis Cluster promotes the replica within seconds. Because replication is asynchronous, it may have missed the last few hundred milliseconds of ZINCRBYs. That's acceptable because Redis isn't the source of truth: every score event was written idempotently to MySQL first. A rebuilder compares and reloads the sorted set from `user_scores`, or replays recent events from Kafka, and the audit job confirms the top 100 matches the database. Users might see a rank flicker briefly. Prize settlement is unaffected because it runs on the database.'''),
 ("How would you know the leaderboard is wrong or stale?",
  r'''Freshness: measure event time to visibility in Redis, and alert if p99 exceeds 2 seconds or Kafka consumer lag in seconds grows. Correctness: a periodic audit recomputes the top 100 from MySQL and diffs it against Redis, and any difference pages, because prizes depend on it. Dedupe hit rates catch replay storms. Redis CPU and per-key ops catch a hot shard before it saturates. User-facing signals help too: support tickets about "wrong rank" spiking right after a match event are a strong symptom.'''),
 ("How do you handle ties fairly?",
  r'''Decide the business rule first. Usually the earlier achiever wins, sometimes ties share the rank. For earliest-wins, encode a composite score: points multiplied by a large factor, plus the inverse of the time the score was reached, so equal points sort by time. Redis scores are doubles, so the composite must stay under 2^53 to remain exact. Otherwise, sort members lexicographically on equal scores with fixed-width encoded strings. For shared ranks, compute rank as 1 plus the count of strictly greater scores with ZCOUNT.''')
],
[("Redis Docs - Sorted sets", "https://redis.io/docs/latest/develop/data-types/sorted-sets/"),
 ("Redis Docs - Count-min sketch", "https://redis.io/docs/latest/develop/data-types/probabilistic/count-min-sketch/"),
 HI_TOPK,
 ("ByteByteGo - Real-time Gaming Leaderboard", "https://bytebytego.com/courses/system-design-interview/real-time-gaming-leaderboard"),
 ("Wikipedia - Count-min sketch (Cormode & Muthukrishnan)", "https://en.wikipedia.org/wiki/Count%E2%80%93min_sketch")]))

# ---------------------------------------------------------------- 11
topics.append(T("flash-sale-inventory", "Flash Sale Inventory (Big Billion Days Style)", 11, "case-study", "Advanced",
"Selling 10,000 units to 5 million people at 12:00 noon: an edge waiting room, atomic Redis decrements as the admission gate, MySQL as the source of truth, reservation expiry, bot defence, and never overselling.",
r'''
## 1. Requirements

**Functional**
- A sale opens at 12:00:00 for limited stock (say 10,000 phones at a deal price), with a limit of 1 per user.
- A successful click **reserves** a unit for 10 minutes while the user pays. Unpaid reservations go back to stock.
- Users see "sold out" as soon as stock runs out. Admitted users see their place in the queue.

**Non-functional**
- **Never oversell**: sold + reserved ≤ total is a hard invariant. Underselling is tolerable for a short time.
- 5M users waiting, **0.5-1M requests/s** in the first seconds.
- Roughly first-come-first-served, and resistant to bots.
- **The rest of the site keeps working** (browse, other orders, payments for other products).

## 2. Estimates

- Winners: 10k. Losers: about 5M. So **99.8% of the work is saying "no" quickly and cheaply**.
- Successful database writes are about 10k reservations plus 10k orders, which is trivial. The problem is the **attempt storm**, not write volume.
- One hot MySQL row under row locks handles a few hundred to a few thousand conditional updates a second. One Redis shard handles about 100k simple ops/s. Neither can take 1M/s directly, so you need a funnel.

## 3. API

```text
GET  /v1/sales/{saleId}                 static page + countdown (CDN; server time in response)
POST /v1/sales/{saleId}/queue           -> {queueToken, position, pollAfterMs}
GET  /v1/sales/{saleId}/queue/{token}   -> {status: WAITING|ADMITTED|SOLD_OUT, admissionToken?}
POST /v1/sales/{saleId}/reservations    Idempotency-Key, Authorization, X-Admission-Token
     -> 201 {reservationId, expiresAt} | 409 SOLD_OUT | 409 ALREADY_PURCHASED
POST /v1/orders {reservationId}         -> payment flow
```

## 4. Data model

```sql
CREATE TABLE sale_inventory (
  sale_id BIGINT, sku VARCHAR(32), total INT NOT NULL, reserved INT NOT NULL DEFAULT 0,
  sold INT NOT NULL DEFAULT 0, PRIMARY KEY (sale_id, sku),
  CHECK (reserved >= 0 AND sold >= 0 AND reserved + sold <= total)      -- MySQL 8.0.16+
);
CREATE TABLE reservations (
  id VARCHAR(32) PRIMARY KEY, sale_id BIGINT, sku VARCHAR(32), user_id BIGINT,
  status ENUM('HELD','CONFIRMED','EXPIRED','CANCELLED') NOT NULL, expires_at DATETIME(3),
  UNIQUE KEY uk_one_per_user (sale_id, user_id), INDEX (status, expires_at)
);
-- Redis: stock:{sale:42}  (counter)    buyers:{sale:42}  (SET of userIds)   same hash slot
```

## 5. High-level design

```text
 5M users
   |  static page, JS, images, "sold out" flag (short TTL)
 [CDN] ------------------------------------------------------------+
   |                                                                |
 [WAF + bot manager]: per IP/device/account limits, CAPTCHA, fingerprint
   |
 [Waiting room @ edge]: FIFO tickets by arrival, admits ~5k users/s, signed admission token
   |
 [API Gateway] -> [Sale service (isolated cluster)]
                      |  Lua: already bought? stock>0? DECR + SADD   (atomic)
                      v
                 [Redis Cluster - sale only]
                      | success -> write reservation (sync)
                      v
                 [Reservation service] -> MySQL: INSERT reservation + conditional UPDATE inventory
                      |                         (the real source of truth)
                      +-> Kafka reservation.held -> Order / Payment / Notification
 [Expiry worker]: HELD past expires_at -> EXPIRED -> release DB + INCR Redis
 [Reconciler]: Redis stock == total - (reserved + sold) in DB?  (repairs leaks)
```

## 6. Deep dives

### 6.1 The funnel

Each layer rejects most of the traffic before the next, more expensive one:

1. **CDN** serves the sale page and a `soldOut` JSON flag with a 1-2 s TTL. After the sellout, most traffic never reaches the origin.
2. **Waiting room**: users get a ticket based on arrival order and poll their status. The room admits a fixed rate the backend can handle. Shopify's flash-sale throttle did this with a leaky bucket in OpenResty/Lua at the edge, a polling queue page, and a signed cookie for admitted shoppers. Their lesson: random admission felt unfair (some waited 40 minutes for a 40-minute sale), so issue **ordered tickets**.
3. **Redis gate**: atomic check-and-decrement, about 0.2 ms per attempt.
4. **MySQL** sees only the winners.

### 6.2 Never oversell: comparing the options

| Approach | Correct? | Throughput |
|---|---|---|
| `SELECT stock ...; if > 0 UPDATE` | **No**: read-then-write race | n/a |
| `SELECT ... FOR UPDATE` on the stock row | Yes | Serialises on one hot row |
| `UPDATE ... SET reserved=reserved+1 WHERE reserved+sold < total` | Yes, atomic | Hot-row bound, about 1-2k/s |
| Redis Lua check-and-decrement | Yes (single-threaded) | ~100k/s per shard |
| Stock split into N Redis keys or token lists | Yes | ~N × 100k/s |

```lua
-- KEYS[1]=stock:{sale:42}  KEYS[2]=buyers:{sale:42}  ARGV[1]=userId
if redis.call('SISMEMBER', KEYS[2], ARGV[1]) == 1 then return -2 end   -- already bought
local s = tonumber(redis.call('GET', KEYS[1]) or '0')
if s <= 0 then return -1 end                                           -- sold out
redis.call('DECR', KEYS[1]); redis.call('SADD', KEYS[2], ARGV[1])
return s - 1
```

Redis is the **gate**, and MySQL is the **ledger**. A winner's reservation is committed with the conditional update and the `UNIQUE(sale_id, user_id)` insert in one transaction. Only after that commit does the user see "Reserved!". The database `CHECK` and `WHERE` clause make overselling impossible even if Redis is wrong.

### 6.3 When Redis and the database disagree

- **Redis decremented, then the service crashed before writing to the DB**: the unit has leaked (undersell). The reconciler compares Redis stock with `total - reserved - sold` every few seconds and returns leaked units with `INCRBY`. It also removes the user from `buyers` so they can try again.
- **Redis failover lost recent decrements** (replication is async): Redis now shows *more* stock than reality. Extra winners pass the gate, but the DB conditional update affects 0 rows, so they get "sold out" instead of a confirmation. No oversell happens. The cost is a worse experience for a few users, which is why confirmation waits for the DB commit.
- Defensive choices: run the sale's Redis with AOF `everysec`, keep stock and buyers in one hash slot (`{sale:42}`), and set the sold-out CDN flag from the **database** count.

### 6.4 Reservation expiry and late payments

The expiry worker runs `UPDATE reservations SET status='EXPIRED' WHERE id=? AND status='HELD' AND expires_at < NOW(3)`. Only if 1 row changed does it decrement `reserved` and `INCR` Redis stock. A conditional update prevents a double release. If a payment success arrives **after** expiry, the conditional confirm (`WHERE status='HELD'`) fails, so we either re-reserve if stock remains or auto-refund. Released units flow back to users still in the queue, which is why the waiting room keeps going for a while after "sold out".

### 6.5 Bots and fairness

- Require login with a verified phone number. One unit per account and per payment instrument (catch the same card across many accounts).
- Per IP, device and account rate limits at the WAF. Device fingerprinting. CAPTCHA or proof-of-work when joining the queue, **not** at the buy click.
- Issue the reservation endpoint's admission token only at 12:00:00 from the server, so pre-scripted calls fail. The server clock decides when the sale opens, never the client.
- Optional: randomise order among everyone who joined in the first N seconds (a lottery), which removes the millisecond advantage of bots.
- After the sale, cancel suspicious orders (velocity, shared addresses) before shipping.

### 6.6 Isolation

The sale runs on its **own** service deployment, Redis cluster and connection pools (bulkheads), so a meltdown can't take search or other checkouts with it. Pre-scale an hour before the sale (autoscaling is too slow for a step from 0 to 1M), pre-warm caches, freeze deploys, and keep feature flags ready to switch off recommendations and personalisation.

## 7. Observability

- **Invariant monitor**: `reserved + sold <= total` from the DB, checked every few seconds. A violation pages immediately (it should be impossible).
- The Redis vs DB stock gap (should converge to 0), and leaked units repaired by the reconciler.
- Funnel metrics: edge RPS, queue length and p95 wait, admission rate, gate outcomes (OK / SOLD_OUT / ALREADY), DB reservation latency and failures.
- Time to sellout, reservation-to-payment conversion, and expiry releases.
- Bot blocks by rule, and 429/503 rates per layer. A war-room dashboard with these funnels next to the saturation of each component.

## 8. Trade-offs

- **Redis gate + DB ledger** (fast, needs reconciliation) vs **DB-only behind a strict waiting room** (simpler, lower admission rate).
- **Strict FCFS vs lottery**: FCFS rewards the fastest connection (and bots), while a lottery is fairer but surprises users.
- **Hold time**: long holds lock stock behind abandoned carts, short holds fail slow payers (UPI approvals can take a minute).
- **Synchronous confirmation** (simple, holds a request open) vs **async** ("we're confirming", then push): async absorbs bursts better.
''',
[
 "99.8% of the work is saying no cheaply. Build a funnel: CDN, then WAF and bot defence, then the waiting room, then the Redis gate, then MySQL for winners only.",
 "Read-then-write stock checks oversell. Use atomic conditional updates or Redis Lua check-and-decrement, plus a DB CHECK constraint.",
 "Redis is the admission gate and MySQL the ledger. Confirm a reservation only after the DB commit, so Redis errors can cause underselling but never overselling.",
 "A reconciler repairs units leaked when Redis decremented and the DB write never happened, by comparing Redis stock with total minus reserved minus sold.",
 "Expiry and confirmation use conditional transitions (WHERE status='HELD'), so releases happen once and late payments are refunded or re-reserved.",
 "A waiting room with ordered tickets admits at backend capacity (Shopify's lesson: random admission feels unfair).",
 "Bot defence: verified accounts, per-instrument limits, rate limits, CAPTCHA at queue entry, server-timed tokens, optional lottery, post-sale fraud review.",
 "Isolate the sale's infrastructure, pre-scale, and monitor the oversell invariant, the Redis vs DB gap and the funnel conversion."
],
[
 ("How exactly do you guarantee no overselling?",
  r'''The final guard is in MySQL. The reservation transaction runs `UPDATE sale_inventory SET reserved = reserved + 1 WHERE sale_id = ? AND reserved + sold < total` and inserts the reservation with a unique (sale, user) key. A CHECK constraint backs it up. If the update touches 0 rows, the user gets sold out. Because that statement is atomic, no read-then-write race exists. Redis sits in front only to reject the millions of losers cheaply. It can be wrong in either direction, but a reservation is only confirmed after the DB commit, so Redis errors can't produce an oversell.'''),
 ("Redis decremented the stock, but the service crashed before writing the reservation. Now what?",
  r'''That unit is leaked: Redis thinks it's taken, but the database has no reservation, so we'd undersell by one. A reconciler runs every few seconds during the sale and compares the Redis counter with total minus reserved minus sold from the database. When Redis is lower, it adds the difference back and removes the affected user from the buyers set so they can retry. The user's client got an error or timeout and can retry with the same idempotency key. Underselling briefly is acceptable, overselling is not.'''),
 ("What if the sale's Redis primary fails over in the middle of the rush?",
  r'''Replication is asynchronous, so the new primary may have missed the last few decrements and show slightly more stock than reality. Extra users pass the gate, but their database conditional updates affect 0 rows, so they see sold out instead of a confirmation. No oversell, just a brief bad experience. During the failover seconds, the gate errors and the waiting room pauses admissions instead of sending users to the database. Afterwards, the reconciler resets Redis stock from the database. AOF with fsync every second limits loss on a restart.'''),
 ("How do you stop bots and resellers from buying everything?",
  r'''Layered defences. Require login with a verified phone number, and limit one unit per account and per payment instrument or address. Apply WAF rate limits per IP, device and account, plus device fingerprinting. Put a CAPTCHA or proof-of-work at queue entry, not at the buy click where it would slow real users. Issue admission tokens from the server only when the sale opens, so pre-scripted requests fail. Optionally randomise order among everyone who joined in the first few seconds, removing the millisecond edge. After the sale, cancel orders flagged by velocity or shared-attribute analysis before shipping.'''),
 ("How do you keep the rest of the site alive during the sale?",
  r'''Isolation and shedding. The sale runs on its own deployment, Redis cluster, connection pools and database capacity (bulkheads), so its overload can't consume the catalog's or other checkouts' resources. The CDN and waiting room absorb the spike at the edge, so origin traffic is bounded by the admission rate. I pre-scale an hour ahead because autoscaling can't react to a step change, freeze deploys, and keep feature flags to switch off recommendations and personalisation. If the main site still struggles, the gateway sheds low-priority traffic first.'''),
 ("How would you know something is going wrong during the sale?",
  r'''A war-room dashboard tracks the funnel: edge RPS, queue length and wait, admission rate, gate outcomes, reservation latency and errors, and payment conversion. Hard alerts: the oversell invariant (reserved + sold > total) pages immediately, the Redis vs database stock gap not converging means leaks or a failover, and the reservation error rate or p99 jumping means the database is the bottleneck. Saturation per component (Redis CPU, DB connections, row lock waits) shows where. Business signals like a stalled sellout or zero payments in a minute catch silent failures.''')
],
[("Shopify Engineering - Surviving Flashes of High-Write Traffic Using Scriptable Load Balancers (Part I)", "https://shopify.engineering/surviving-flashes-of-high-write-traffic-using-scriptable-load-balancers-part-i"),
 ("Shopify Engineering - Surviving Flashes of High-Write Traffic Using Scriptable Load Balancers (Part II)", "https://shopify.engineering/surviving-flashes-of-high-write-traffic-using-scriptable-load-balancers-part-ii"),
 ("Hello Interview - Design a Ticket Booking Site Like Ticketmaster", "https://www.hellointerview.com/learn/system-design/problem-breakdowns/ticketmaster"),
 ("Redis Docs - Scripting with Lua", "https://redis.io/docs/latest/develop/programmability/eval-intro/"),
 ("MySQL 8.0 Reference - CHECK Constraints", "https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html")]))

if __name__ == "__main__":
    report(topics)
