"""Senior SD chunk 1: failure handling, idempotency, multi-region DR."""
from sdsenior_common import *

topics = []

# ---------------------------------------------------------------- 1
topics.append(T("failure-handling-resilience", "Failure Handling & Resilience Patterns", 1, "concept", "Intermediate",
"How production services survive slow and failing dependencies: timeouts with deadline budgets, retries with backoff and jitter, circuit breakers, bulkheads, load shedding and graceful degradation.",
r'''
## Why seniors get this question

In a distributed system something is always partially broken: one MySQL replica is lagging, a payment provider is answering in 9 seconds, a pod is in a GC pause. A mid-level answer draws the happy path. A senior answer explains **what each box does when the box next to it is slow**, because a slow dependency is far more dangerous than a dead one. A dead one fails fast. A slow one holds your threads, fills your connection pool and spreads the outage upstream. That is how cascading failures start.

These six tools work together. Know what each one protects against.

| Pattern | Protects against | Typical Java tool |
|---|---|---|
| Timeout + deadline | Hanging calls holding threads | `HttpClient`/`WebClient` timeouts, JDBC query timeout |
| Retry + backoff + jitter | Transient blips | Resilience4j `Retry`, Spring Retry |
| Circuit breaker | Hammering a dependency that is already down | Resilience4j `CircuitBreaker` |
| Bulkhead | One dependency using up every thread | Separate pools, Resilience4j `Bulkhead` |
| Load shedding | More traffic than you can serve | Concurrency limiter, 503 + `Retry-After` |
| Graceful degradation | Losing a non-critical feature | Fallbacks, feature flags, cached data |

## 1. Timeouts and deadline budgets

Every remote call needs a **connect timeout** and a **request (read) timeout**. Library defaults are often unsafe: many HTTP clients wait forever, and a JDBC statement has no query timeout unless you set one. AWS's guidance is to pick an acceptable false-timeout rate (for example 0.1%) and set the timeout at the matching downstream latency percentile (p99.9). Add some padding when p99.9 sits close to p50. Also warm connections at startup, so a cold TLS handshake doesn't push the first calls past a tight timeout.

Timeouts must also fit a **budget**. If the user-facing SLO is 800 ms, the parts must add up:

```text
API gateway (total deadline 800 ms)
  -> order-service          own work 50 ms
       -> pricing-service   timeout 150 ms
       -> inventory-service timeout 150 ms (parallel with pricing)
       -> MySQL             query timeout 200 ms
  remaining slack for retry: ~250 ms -> at most ONE retry, only for idempotent reads
```

**Deadline propagation** (the Google SRE term): pass the remaining time downstream, for example as a gRPC deadline or an `X-Request-Deadline` header. Each hop then uses what's left instead of a fresh hard-coded 2 s. Servers check the deadline before expensive work, because the caller has already given up.

## 2. Retries with exponential backoff and jitter

Retry only when the failure is **transient** (connection reset, 503, timeout on an idempotent call) **and** the operation is **idempotent**. Never retry a 400 or a validation error. Never blindly retry a non-idempotent call like "charge card".

Retries multiply. AWS's example: five layers that each try three times put up to 3^5 = **243x** load on the database during an outage. So:

- **Retry at one layer**, usually the one closest to the failing dependency.
- **Exponential backoff with full jitter**: `sleep = random(0, min(cap, base * 2^attempt))`. Jitter breaks the synchronized waves of clients retrying together.
- **Retry budgets**: Google caps a request at 3 attempts and a client's retries at 10% of its requests. AWS SDKs use a token bucket: retries spend tokens, and once the bucket is empty retries stop.
- Honour `Retry-After`, and let an overloaded server say "overloaded, don't retry".

## 3. Circuit breakers

A breaker watches outcomes and stops calling a dependency that is clearly failing. It moves through **CLOSED** (normal), **OPEN** (fail fast for a wait period) and **HALF_OPEN** (let a few trial calls through). Resilience4j's defaults are a 50% failure rate threshold, a 100-call sliding window, at least 100 calls before it calculates a rate, 60 s in OPEN and 10 trial calls. The default slow-call threshold is 60 s, far too high for most APIs, so set it explicitly:

```yaml
resilience4j.circuitbreaker.instances.pricing:
  sliding-window-type: TIME_BASED
  sliding-window-size: 30            # seconds
  minimum-number-of-calls: 20
  failure-rate-threshold: 50
  slow-call-duration-threshold: 300ms
  slow-call-rate-threshold: 60
  wait-duration-in-open-state: 10s
  permitted-number-of-calls-in-half-open-state: 5
resilience4j.timelimiter.instances.pricing.timeout-duration: 150ms
```

Know the counter-argument too. The AWS Builders' Library warns that breakers add modal behaviour that is hard to test. Use them for clear dependency failures, and keep the open state short.

## 4. Bulkheads

Ships have watertight compartments. Services should too. If pricing and recommendations share one Tomcat pool of 200 threads, a slow recommendations service can tie up all 200, and checkout dies with it. Give each dependency its own bounded pool or semaphore (for example, recommendations gets 20 concurrent calls at most). Apply the same idea to data: a separate HikariCP pool for reporting queries, and per-tenant concurrency limits so one big merchant can't starve the rest.

## 5. Load shedding and admission control

When demand exceeds capacity, serving everyone slowly means serving no one. Reject early and cheaply with a **503 + `Retry-After`** once in-flight requests pass a limit. Keep queues short: Google suggests queues no longer than about half the thread pool. Shed by **priority**. Netflix sheds prefetch traffic before user-initiated requests. During one incident, prefetch availability fell to about 20% while user-initiated requests stayed above 99.4%. Adaptive concurrency limiters (Netflix's open-source `concurrency-limits` library) find the limit from observed latency instead of a hand-tuned number.

## 6. Graceful degradation

Decide ahead of time what the product does when each dependency is down:

- Recommendations down: show cached or generic "bestsellers".
- Pricing down: **fail closed** on checkout (never sell at a wrong price), but browsing keeps working.
- Review service slow: hide the reviews widget.
- Primary DB failing over: switch to read-only mode and queue writes.

A fallback must never call the failing dependency, and it must be exercised regularly. As the SRE book says, the code path you never use is the one that often doesn't work.

## Putting it together in Spring Boot

Resilience4j's Spring Boot aspects apply this default order: `Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( call ) ) ) ) )`. Each attempt is time-limited and isolated, the breaker counts every attempt, and retry sits outermost so it can back off while the breaker is open.

```java
@Retry(name = "pricing")
@CircuitBreaker(name = "pricing", fallbackMethod = "cachedPrice")
@Bulkhead(name = "pricing")
public Price getPrice(String sku) { return pricingClient.get(sku); }

private Price cachedPrice(String sku, Throwable t) {
    return priceCache.getIfFresh(sku, Duration.ofMinutes(5))
        .orElseThrow(() -> new ServiceDegradedException("pricing", t));
}
```

## How you know it's working

Export Resilience4j metrics through Micrometer: breaker state changes, retry counts, bulkhead rejections, fallback calls and shed requests. Alert when a **critical** dependency's breaker stays open, or when the retry ratio passes about 10% (a retry storm is starting). Then test the whole setup with fault injection (add latency to pricing in staging), not only by reading the config.
''',
[
 "A slow dependency is more dangerous than a dead one: it holds threads and pools and spreads the outage upstream.",
 "Every remote call needs connect and read timeouts. Derive them from downstream p99.9 and fit them into an end-to-end deadline budget that you propagate.",
 "Retry only transient failures of idempotent operations, at one layer, with exponential backoff plus full jitter and a retry budget (about 3 attempts, 10% ratio).",
 "Circuit breakers fail fast when a dependency is clearly down. Tune the slow-call threshold (Resilience4j defaults to 60 s) and keep the open state short.",
 "Bulkheads (separate pools or semaphores per dependency and tenant) stop one slow dependency from using up every thread.",
 "Load shedding rejects early with 503 + Retry-After and drops low-priority traffic first (Netflix: prefetch before user-initiated).",
 "Plan graceful degradation per dependency: fail open for nice-to-haves, fail closed for money and correctness, and exercise fallbacks regularly.",
 "Prove it with metrics (breaker state, retry ratio, rejections, fallbacks) and fault-injection tests."
],
[
 ("How do you choose a timeout for a downstream call?",
  r'''Start from the downstream's latency distribution, not a round number. Pick a false-timeout rate you can accept, say 0.1%, and set the timeout near that percentile (p99.9), with padding if p99.9 is close to p50. Then check it fits the caller's budget: if the user SLO is 800 ms and two calls run in sequence, each can't take 1 s. Set connect and read timeouts separately, set a JDBC query timeout, and propagate the remaining deadline downstream so lower layers don't keep working after the caller has given up.'''),
 ("Your service retries three times, and so do its two upstream callers. What goes wrong?",
  r'''Retries multiply across layers. With three layers each making three attempts, one user action can turn into 27 calls to the bottom service, right when it is already struggling. That turns a blip into a sustained outage. The fix: retry at one layer only (usually closest to the dependency), use exponential backoff with full jitter, cap attempts per request, and add a retry budget (for example, retries at most 10% of traffic, or a token bucket). Overloaded servers should return a "don't retry" signal or a `Retry-After`.'''),
 ("How do timeout, retry and circuit breaker fit together in Resilience4j?",
  r'''The default aspect order is Retry wrapping CircuitBreaker wrapping RateLimiter, TimeLimiter and Bulkhead. Each attempt is bounded by the TimeLimiter and isolated by the Bulkhead, and the CircuitBreaker records every attempt's outcome, including slow calls. Retry sits outermost, so once the breaker opens, retries fail fast with `CallNotPermittedException` instead of hitting the dependency. Retry should skip that exception, or only retry after backoff. A fallback at the breaker returns cached or degraded data. Keep total retry time inside the caller's deadline.'''),
 ("During a sale, the recommendations service gets slow. Walk me through what your design does.",
  r'''Calls to recommendations have a tight timeout (about 150 ms) and their own bulkhead of 20 concurrent calls, so checkout threads never wait on it. As slow calls pass the threshold, the breaker opens and the page renders "bestsellers" from a Redis cache through the fallback. Checkout, pricing and payment are on separate pools and unaffected. If overall traffic still exceeds capacity, the gateway sheds low-priority traffic such as prefetch and recommendations first. Dashboards show the breaker open and the fallback rate rising. That pages the recommendations team, not checkout.'''),
 ("How do you know these resilience mechanisms are working, or that something is broken?",
  r'''Instrument them. Micrometer exports Resilience4j metrics: breaker state transitions, failure and slow-call rates, retry attempts, bulkhead rejections, fallback invocations and shed request counts. User-facing alerts stay symptom-based (error rate, latency SLO burn). The resilience metrics explain why. I would also alert on a critical dependency's breaker staying open, and on the retry ratio passing about 10%, which signals a retry storm. Finally, verify with fault injection: add latency or errors to a dependency in staging, or to a canary, and confirm the fallback actually serves.'''),
 ("What if the primary MySQL fails over and writes fail for about 60 seconds?",
  r'''Reads keep working from replicas and caches. Writes get connection errors, which are transient, so the data layer retries with backoff and jitter within the request deadline. Don't retry forever: hold connections briefly, then fail. For user flows, degrade: show "orders are taking longer than usual", accept requests into a durable queue (Kafka) where that's safe, and process them after promotion. Idempotency keys stop queued or retried writes from applying twice. HikariCP must drop stale connections so traffic follows the new primary. Alert on write error rate, then confirm recovery.''')
],
[AWS_RETRY, SRE_CASCADE, SRE_OVERLOAD, R4J_CB,
 ("InfoQ - Netflix Enhances Reliability with Service-Level Prioritized Load Shedding", "https://www.infoq.com/news/2024/11/netflix-load-shedding/"),
 ("Netflix concurrency-limits library (GitHub)", "https://github.com/Netflix/concurrency-limits")]))

# ---------------------------------------------------------------- 2
topics.append(T("idempotency-exactly-once", "Idempotency & Exactly-Once Processing", 2, "concept", "Advanced",
"Why exactly-once delivery isn't possible, and how at-least-once delivery plus idempotency keys, dedup tables, conditional updates and the outbox/inbox patterns give an exactly-once effect.",
r'''
## The honest starting point

Over an unreliable network you can't guarantee that a message is **delivered** exactly once. When a request times out, the sender can't know whether the receiver never got it, processed it and crashed, or processed it and the response was lost. The only safe move is to send again. So real systems use **at-least-once delivery** and make processing **idempotent**: applying the same message twice has the same effect as applying it once.

> at-least-once delivery + idempotent processing = exactly-once effect

Interviewers want you to say this sentence, then show where duplicates come from and how each one is absorbed.

## Where duplicates come from

- A client or mobile app retries after a timeout, or a user double-taps "Pay".
- A load balancer or service mesh retries an upstream request.
- A Kafka consumer processes a record, then crashes or gets rebalanced before committing the offset.
- A producer retries a send whose acknowledgement was lost.
- A webhook sender redelivers because your 200 came back too late.
- An outbox relay publishes, crashes before marking the row sent, and publishes again.

## 1. Idempotency keys for APIs

The client generates a unique key (a UUID) for each **logical operation** and sends it with every retry of that operation. Stripe uses an `Idempotency-Key` header. The server records the key together with the result:

```sql
CREATE TABLE idempotency_keys (
  merchant_id   BIGINT       NOT NULL,
  idem_key      VARCHAR(64)  NOT NULL,
  request_hash  CHAR(64)     NOT NULL,          -- SHA-256 of method+path+body
  status        ENUM('IN_PROGRESS','COMPLETED') NOT NULL,
  response_code INT NULL,
  response_body JSON NULL,
  locked_until  DATETIME(3)  NOT NULL,           -- lease, longer than downstream timeout
  created_at    DATETIME(3)  NOT NULL,
  PRIMARY KEY (merchant_id, idem_key)
);
```

Flow for `POST /payments`:

1. `INSERT ... ` the key as `IN_PROGRESS` with a lease. If the insert fails on the primary key, a request with this key already exists.
2. Existing key and `COMPLETED`: if the request hash matches, return the stored response. If it doesn't match, return 422, because the key was reused for a different payload.
3. Existing key, `IN_PROGRESS` and lease still valid: return 409 "in progress". If the lease has expired, the previous worker died, so take over and **resume**.
4. Do the work, then store the response and mark the key `COMPLETED`.

Production details that separate senior answers:

- **Read the key from the primary, never a replica.** Airbnb's Orpheus library does this, because with replica lag a retry looks new and causes a double payment.
- **Never hold a DB transaction open across a network call.** Airbnb splits each request into pre-RPC (record intent), RPC (call the provider) and post-RPC (record outcome) phases, with no network calls inside DB phases.
- **Pass a derived key downstream.** When you call a payment provider, send `attempt_id` as its idempotency key, so your own retry of the RPC is safe too.
- **Retention must exceed the retry window.** Keep keys 24-72 hours. Brandur's Stripe-style design suggests about 72 hours, so a weekend outage can still be recovered on Monday.

## 2. Natural idempotency and conditional writes

Many operations can be made idempotent without a key table:

```sql
-- state transition: only the first caller wins
UPDATE orders SET status = 'PAID', paid_at = NOW(3)
 WHERE id = ? AND status = 'PENDING_PAYMENT';      -- 0 rows -> already applied, no-op

-- NOT idempotent: replays add money twice
UPDATE wallets SET balance = balance + 500 WHERE user_id = ?;

-- idempotent alternative: unique business id on an append-only ledger
INSERT INTO ledger_entries (txn_id, account_id, amount, direction) VALUES (?, ?, 500, 'CREDIT');
-- UNIQUE(txn_id, account_id, direction) turns a replay into a duplicate-key no-op
```

"Set state to X" and "insert row with unique business ID" are idempotent. "Increment by N" isn't, unless it is tied to a unique operation ID.

## 3. Idempotent consumers (the inbox / dedup table)

For Kafka or SQS consumers, record the processed message ID **in the same local transaction** as the business change:

```java
@KafkaListener(topics = "payment-events", groupId = "order-service")
@Transactional
public void on(PaymentEvent e) {
    int inserted = jdbc.update(
        "INSERT IGNORE INTO processed_messages(consumer, message_id) VALUES ('order-service', ?)",
        e.eventId());
    if (inserted == 0) return;                // duplicate: already applied
    orderRepo.markPaid(e.orderId(), e.paymentId());
}   // offset is committed after the DB commit; a crash in between just replays -> deduped
```

Redis `SET key NX EX` works as a fast path, but it isn't the source of truth: a Redis failover can lose recent keys. Keep the database constraint as the real guard and purge old dedup rows on a schedule.

## 4. The transactional outbox (producer side)

The **dual-write problem**: you commit an order in MySQL and then publish `OrderCreated` to Kafka. If you crash between the two, the event is lost forever. If you publish first, the event can describe an order that was rolled back. The fix is to write the event to an `outbox` table **in the same transaction** as the order. A relay (a poller, or Debezium CDC reading the binlog) publishes outbox rows to Kafka. The relay is at-least-once, so every event carries a stable `event_id` and consumers dedupe on it. Outbox on the producer side plus inbox on the consumer side is the standard pair.

## 5. What Kafka's exactly-once actually covers

- **Idempotent producer** (`enable.idempotence=true`, the default since Kafka 3.0): the broker drops duplicate retries using producer ID + sequence number per partition.
- **Transactions**: atomically write to several partitions **and** commit consumer offsets, so a consume-transform-produce loop inside Kafka is exactly-once (Kafka Streams `processing.guarantee=exactly_once_v2`). Downstream consumers must use `isolation.level=read_committed`. A stable `transactional.id` fences zombie producers.
- **Not covered**: side effects outside Kafka. Confluent says plainly that if processing touches other storage systems, these APIs aren't enough. A DB write, an email or a PSP call inside your consumer still needs idempotency of its own.

## Common mistakes

- Generating the idempotency key on the **server** on each attempt. It must come from the caller, once per logical operation.
- Scoping keys globally instead of per merchant or user, so tenants can collide.
- A dedup TTL shorter than the maximum redelivery delay (for example, webhooks retried for 3 days).
- Treating "the consumer is idempotent" as enough, when its side effects (emails, payouts) are not.
''',
[
 "Exactly-once delivery isn't possible over an unreliable network. Build at-least-once delivery plus idempotent processing to get an exactly-once effect.",
 "API idempotency: a client-generated key per logical operation, stored with a request hash, status, lease and response under a unique constraint.",
 "Read idempotency keys from the primary (replica lag causes double payments) and never hold a DB transaction across a network call.",
 "Pass derived idempotency keys to downstream providers so your own RPC retries are safe as well.",
 "Prefer naturally idempotent writes: conditional state transitions and append-only rows with unique business IDs, not blind increments.",
 "Consumers dedupe by recording the message ID in the same DB transaction as the business change (inbox), with the DB constraint as the source of truth.",
 "Use the transactional outbox (poller or Debezium CDC) to solve the DB + Kafka dual-write problem. The relay is at-least-once, so events carry stable IDs.",
 "Kafka transactions give exactly-once only for read-process-write inside Kafka. External side effects still need their own idempotency."
],
[
 ("Can Kafka give us exactly-once processing?",
  r'''Partly. The idempotent producer removes duplicates caused by producer retries, and transactions let a consume-transform-produce loop commit output records and input offsets atomically. So Kafka-to-Kafka pipelines (Kafka Streams with `exactly_once_v2`) are effectively exactly-once, as long as downstream readers use `read_committed`. Most real consumers also write to MySQL, call a PSP or send an email, and Kafka transactions don't cover those. For them I use at-least-once consumption plus an inbox/dedup table, written in the same DB transaction as the business change, or naturally idempotent writes.'''),
 ("Design idempotency for POST /payments. What happens when two requests with the same key arrive at once?",
  r'''The client sends an `Idempotency-Key`. I insert `(merchant_id, key)` into an idempotency table with status IN_PROGRESS, a request hash and a lease. The primary key constraint means only one insert succeeds. The loser sees the existing row: if it is IN_PROGRESS with a valid lease, it returns 409 so the client retries later. If it is COMPLETED with the same hash, it returns the stored response. A different hash gets a 422. The winner calls the PSP with a derived key, outside any open DB transaction, then stores the response. Keys live 24-72 hours.'''),
 ("A consumer processed a message and crashed before committing the offset. What happens and how do you handle it?",
  r'''After restart or rebalance, the consumer reads from the last committed offset, so the message is redelivered. That's normal at-least-once behaviour. The handler must be idempotent. I insert the event ID into a `processed_messages` table inside the same transaction as the business update. On redelivery, the insert hits the unique key, the handler skips, and the offset is committed. If the side effect is external, like sending an SMS, I pass the event ID as the provider's idempotency key, or record "sent" before acknowledging, and accept a rare duplicate where the provider can't dedupe.'''),
 ("Outbox with polling, outbox with CDC, or Kafka transactions: how do you choose?",
  r'''If the source of truth is MySQL, I need the outbox, because Kafka transactions can't include a MySQL commit. Polling (SELECT unsent rows, publish, mark sent) is simple and fine for hundreds of events per second, but it adds latency and query load. CDC with Debezium tails the binlog: lower latency, no polling queries, and ordering per aggregate, at the cost of running Kafka Connect. Kafka transactions fit when both input and output are Kafka topics, as in stream processing. In every case downstream consumers still dedupe on event ID.'''),
 ("How would you know duplicates are slipping through in production?",
  r'''Measure the deduplication itself: a counter for idempotency-key replays, dedup-table hits per consumer, and unique-constraint violations caught in handlers. A sudden jump usually means a retry storm or a rebalance loop. For money, the backstop is reconciliation: compare our ledger with the PSP or bank settlement file every day, plus near-real-time checks such as "two successful charges for the same order". Business alerts help too: refund requests mentioning "charged twice", or duplicate notification complaints. Traces showing several attempts for one operation help confirm the cause.'''),
 ("What if your idempotency store is Redis and it fails over and loses recent keys?",
  r'''Then a retry arriving just after the failover looks new and can run twice. That's why Redis shouldn't be the only guard for anything involving money. I'd keep Redis as a fast path to reject obvious duplicates cheaply, but enforce correctness with a durable constraint: the idempotency row in MySQL, a unique `(order_id)` on payment attempts, and conditional state transitions. Redis replication is asynchronous, so a promoted replica can miss writes from the last few hundred milliseconds. Design so losing the cache costs latency, not correctness.''')
],
[STRIPE_IDEM, BRANDUR_IDEM, AIRBNB_PAY, OUTBOX, KAFKA_TX,
 ("Debezium documentation - Outbox Event Router", "https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html")]))

# ---------------------------------------------------------------- 3
topics.append(T("multi-region-disaster-recovery", "Multi-Region Architecture & Disaster Recovery", 3, "concept", "Advanced",
"How to keep a system available when a whole region fails: RPO/RTO, the DR strategy ladder, active-passive vs active-active, replication lag, failover without split-brain, and data residency.",
r'''
## The vocabulary interviewers expect

- **RPO (Recovery Point Objective)**: how much data you can afford to lose, measured in time. With async replication, RPO is roughly the replication lag at the moment of failure.
- **RTO (Recovery Time Objective)**: how long until service is restored.
- **HA vs DR**: high availability handles a node or availability-zone failure automatically, within a region (Multi-AZ RDS, three Kafka brokers across zones). Disaster recovery handles losing a **region**, or losing data through corruption or a bad deploy.

Most real "region down" events are partial: one managed service, the control plane, DNS, or a network partition between zones. A strong answer says how you **detect** the failure and **decide** to fail over, not only how you replicate.

## The DR strategy ladder

AWS describes four strategies. Each step buys lower RPO/RTO with more money and complexity:

| Strategy | Standby region | Typical RPO / RTO | Cost |
|---|---|---|---|
| Backup & restore | Only backups/snapshots | Hours / hours | Lowest |
| Pilot light | Data replicated live, app servers off | Seconds-minutes / tens of minutes | Low |
| Warm standby | Scaled-down full stack serving nothing (or a little) | Seconds / minutes | Medium |
| Active-active (multi-site) | Full stack serving traffic | ~0 (async lag) / near zero | Highest |

Match the strategy to the business. A payments ledger might need RPO ≈ 0 and RTO under 15 minutes. An analytics dashboard can live with backup and restore. Saying "it depends" is fine if you then put numbers on it.

## Active-passive in practice

Take an Indian e-commerce app with its primary in AWS Mumbai (ap-south-1) and DR in Hyderabad (ap-south-2):

```text
            Route 53 / global LB (health-checked)
                 |                         .
         [Mumbai: ACTIVE]            [Hyderabad: PASSIVE]
   app pods, Redis, Kafka           app pods (scaled down), Redis (cold)
   MySQL primary ---- async binlog replication ---> MySQL replica
   S3 bucket   ---- cross-region replication ---> S3 bucket
```

**Failover runbook** (automate every step, keep the decision to a human pressing one button):

1. **Detect**: synthetic probes from several outside locations, plus SLO burn across many services, not one health check.
2. **Decide**: a false failover costs as much as a real one, so AWS recommends caution with fully automatic regional failover.
3. **Fence the old primary**: make it read-only or cut its network, so it can't accept writes if it comes back. This prevents split-brain.
4. **Promote** the replica, then check how far behind it was. Transactions that never replicated are your RPO. Record them so you can reconcile later.
5. **Shift traffic** with data-plane mechanisms (health-checked DNS failover, Application Recovery Controller routing controls). Don't depend on control-plane APIs that may be impaired during the incident.
6. **Warm up**: scale the app tier, pre-warm Redis from the DB for hot keys, and let consumers resume from synced offsets.
7. **Fail back** later, deliberately. It is often harder than the failover, because the old region now has diverged data.

**Static stability**: if failover depends on autoscaling launching 200 instances during a regional event, your RTO depends on a control plane under stress. Pre-provisioned (hot) capacity costs more but removes that dependency.

## Active-active and the write problem

Reads are easy in active-active: serve them from the local region. Writes are the hard part. AWS lists three write patterns:

- **Write global**: all writes go to one region's primary, and reads are local. Simple and consistent, with extra latency for remote writers. Good for a ledger or inventory.
- **Write local**: each region accepts writes and replicates both ways. Concurrent updates conflict, and **last-writer-wins** silently drops one of them. Acceptable for a user profile's "last seen", dangerous for a balance.
- **Write partitioned**: each user (or tenant) has a **home region** that owns their writes. No conflicts, and still local for most users. Netflix and Uber-style designs lean this way, routing a user's traffic to the home region and re-homing users when a region is evacuated.

When conflicts are unavoidable, use data types that merge (CRDT counters and sets) or keep version vectors and resolve in application logic.

## Messaging across regions

Uber's multi-region Kafka setup is a good reference. Producers write to regional clusters, which are replicated (with uReplicator) into **aggregate clusters** in every region. Consumers run in either mode:

- **Active-active**: every region consumes the full stream and computes state itself, with one region chosen as the primary writer of results (Uber's surge pricing works this way).
- **Active-passive**: one consumer in the primary region. On failover it resumes in the other region from a mapped offset. Uber picks the **smallest** safe mapped offset, accepting some reprocessing over data loss. That only works because consumers are idempotent.

## Data residency is a hard constraint

RBI's 2018 circular on storage of payment system data requires the full end-to-end transaction data of payment systems operating in India to be stored only in India. India's DPDP Act 2023 and the EU's GDPR add their own rules. So "fail over to Singapore" may be illegal for payment data. Pick two in-country regions, or keep regulated data in-country and fail over only stateless or non-regulated tiers abroad. Mention this, because it shows production experience.

## Test it or it doesn't exist

- Run failover drills (game days) every quarter and measure the real RPO/RTO. Restore backups on a schedule, because a backup you have never restored is a hope, not a plan.
- Netflix's Chaos Kong exercises evacuate a whole region in production.
- Watch replication lag as an SLI (`Seconds_Behind_Source` or heartbeat tables like pt-heartbeat), with an alert when it threatens the RPO.

## Interview script: "What if the Mumbai region goes down?"

1. State the RPO/RTO per data class: money gets RPO ≈ 0, the feed gets minutes.
2. Explain detection from outside the region and the human-approved, automated runbook.
3. Fence, promote, shift traffic with data-plane tools, and warm caches.
4. Explain what is lost (async lag) and how reconciliation and idempotency clean it up.
5. Say what degrades during the switch, for example read-only mode for 5 minutes.
6. Close with how you test this regularly.
''',
[
 "RPO is the data you can lose (roughly the replication lag). RTO is the time to recover. Set them per data class, not per system.",
 "DR ladder: backup & restore, then pilot light, then warm standby, then active-active. Each step costs more for lower RPO/RTO.",
 "Failover runbook: detect from outside, decide (human button, automated steps), fence the old primary, promote, shift traffic, warm up, fail back deliberately.",
 "Prevent split-brain by fencing the old primary before promoting, and prefer data-plane failover mechanisms over control-plane APIs.",
 "Active-active writes: write-global (consistent), write-local (conflicts and last-writer-wins data loss) or write-partitioned by home region (no conflicts).",
 "Cross-region Kafka (Uber): regional plus aggregate clusters. Passive consumers resume from the smallest mapped offset, so consumers must be idempotent.",
 "Data residency (RBI payment data localisation, DPDP, GDPR) can rule out failing over to a foreign region.",
 "Drill failovers and restore backups regularly, and alert on replication lag as an RPO SLI."
],
[
 ("Explain RPO and RTO with realistic targets for payments versus a social feed.",
  r'''RPO is how much recent data you can lose, and RTO is how long you can be down. For a payments ledger I'd aim for RPO close to zero, using synchronous or semi-synchronous replication to a second zone or region plus reconciliation with the PSP, and an RTO of maybe 15-30 minutes, because a wrong balance is worse than brief downtime. For a feed, RPO of a few minutes (an occasional lost like) and RTO of minutes with degraded mode are fine. The targets decide the cost: near-zero RPO across regions adds write latency.'''),
 ("Would you run checkout active-active or active-passive across two regions?",
  r'''Mixed. Stateless tiers (gateway, catalog, browse, search) run active-active and serve local reads. Inventory and payment writes go write-global to one primary region, or write-partitioned by seller or user home region, because concurrent writes to the same stock count or ledger can't use last-writer-wins. The cart can be write-local with merge semantics, since a duplicated cart item is harmless. That gives near-zero RTO for most traffic while keeping money and stock consistent. In a regional loss, only the write path does a controlled failover.'''),
 ("What happens to transactions that hadn't replicated when the primary region died?",
  r'''With async replication they're missing on the promoted replica. That's the RPO. First, quantify it: record the last applied GTID on the replica, and when the old primary comes back, extract the unreplicated binlog range instead of discarding it. Second, reconcile: payments are cross-checked against PSP and bank records, and missing orders can be rebuilt from Kafka events or client retries. Idempotency keys make those replays safe. For data that can't be lost, use semi-sync replication so a commit only acknowledges after another location has the binlog event.'''),
 ("How do you prevent split-brain during failover?",
  r'''Split-brain happens when the old primary keeps accepting writes after the replica is promoted. Fence before promoting: set the old primary `super_read_only`, revoke its network or security group, or use STONITH. Use a single authority for leadership, such as a consensus-backed lock (etcd or ZooKeeper) or a managed service, so two nodes can't both believe they're primary. Writers should also check fencing tokens or an epoch, so writes from a deposed leader are rejected. Finally, route traffic through one switch (DNS or global LB) so clients don't keep writing to the stale region.'''),
 ("How do you know a region is actually down, and who decides to fail over?",
  r'''Use signals from outside the failing region: synthetic probes from several locations and ISPs, SLO burn across many services, and the cloud provider's health signals. One health check is never enough. Flapping or partial failures (one AZ, one service) are more common than a full outage, and a false failover is expensive. So the incident commander decides, using a dashboard that shows replication lag, so they know the data-loss cost of failing over now. The steps themselves are automated, so the decision is one button, practised in drills.'''),
 ("Can you fail Indian payment data over to Singapore if both Indian regions have issues?",
  r'''Not for regulated data. RBI's 2018 storage of payment system data circular requires the full end-to-end transaction data to be stored only in India, with an exception for the foreign leg of cross-border transactions. So I'd design DR across two Indian regions (for example AWS Mumbai and Hyderabad), and possibly a second cloud in India for extreme cases. Stateless tiers or non-sensitive features could run elsewhere, but the payment database, ledger and backups stay in-country. I'd confirm the details with compliance.''')
],
[("AWS Whitepaper - Disaster recovery options in the cloud", "https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html"),
 ("Uber Engineering - Disaster Recovery for Multi-Region Kafka at Uber", "https://www.uber.com/blog/kafka/"),
 ("RBI - Storage of Payment System Data (April 2018)", "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11244"),
 ("Netflix Tech Blog - Chaos Engineering Upgraded (Chaos Kong)", "https://netflixtechblog.com/chaos-engineering-upgraded-878d341f15fa"),
 ("Designing Data-Intensive Applications - Martin Kleppmann", "https://dataintensive.net/")]))

if __name__ == "__main__":
    report(topics)
