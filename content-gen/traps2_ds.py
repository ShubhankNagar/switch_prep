from traps2_common import T

A = "distributed-systems"

RETRY_FIX = """PaymentResult chargeWithRetry(Order order, long amountPaise) throws InterruptedException {
    String idemKey = order.paymentAttemptKey();      // generated ONCE per logical payment, stored with the order
    for (int attempt = 0; attempt < 3; attempt++) {
        try {
            return gateway.charge(order.id(), amountPaise, idemKey);   // same key on every retry
        } catch (TimeoutException e) {
            Thread.sleep(backoffMillis(attempt, 200, 2_000));         // outcome unknown: retry is safe
        }                                                              // only because the key repeats
    }
    order.markPaymentPending();     // NOT failed: a reconciler / webhook settles the real status
    return PaymentResult.PENDING;
}"""

DUAL_BUGGY = """@Transactional
public void placeOrder(Order order) {
    orderRepository.save(order);
    kafkaTemplate.send("order-placed", order.getId(), toJson(order));
}"""

OUTBOX_FIX = """@Transactional
public void placeOrder(Order order) {
    orderRepository.save(order);
    outboxRepository.save(new OutboxEvent(UUID.randomUUID(), "order-placed",
            order.getId(), toJson(order)));          // same DB transaction: both rows or neither
}

// Relay: a scheduler like this, or Debezium CDC reading the binlog instead
@Scheduled(fixedDelay = 500)
@Transactional
public void relayOutbox() {
    for (OutboxEvent e : outboxRepository.lockNextBatch(100)) {    // SELECT ... FOR UPDATE SKIP LOCKED
        kafkaTemplate.send(e.type(), e.aggregateId(), e.payload()).join();  // wait for the broker ack
        outboxRepository.markSent(e.id());   // crash before this line => re-sent => consumers dedupe on e.id()
    }
}"""

BACKOFF = """// Exponential backoff with "full jitter": sleep a random time in [0, min(cap, base * 2^attempt)]
static long backoffMillis(int attempt, long baseMs, long capMs) {
    long ceiling = Math.min(capMs, baseMs * (1L << Math.min(attempt, 20)));
    return ThreadLocalRandom.current().nextLong(ceiling + 1);
}"""

TIMEOUT_FIX = """HttpClient client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(1))           // default: none
        .build();

HttpRequest request = HttpRequest.newBuilder(URI.create("http://reco-service/api/recs?user=42"))
        .timeout(Duration.ofMillis(800))                 // response deadline; default: wait forever
        .build();

// plus: a bulkhead (cap concurrent calls to this dependency), a circuit breaker,
// and a fallback (e.g. cached or popular items) when the call fails fast"""

TRAPS = [
    T("trap-distributed-systems-timeout-is-unknown", A, "A timeout is not a failure", "Intermediate", "Very common",
      """Checkout calls the payment gateway to charge ₹500. The call **times out after 3 seconds**. What do you know about the charge?""",
      "The payment failed, so show an error and let the user (or the code) retry.",
      """Locally, an exception means "it didn't happen", and candidates carry that intuition over the network. But a timeout only means **you stopped waiting**. The request may never have arrived, may have been processed with the response lost, or may still be running. Treating it as a failure and retrying without protection is how real systems double-charge customers. Interviewers at payments companies open with this exact scenario.""",
      """The outcome is **unknown**. Design for all three possibilities:

- **Idempotency key per logical operation**, not per attempt. Generate it once, persist it with the order, and send the same key on every retry. The gateway (Stripe's `Idempotency-Key` header, or the unique order/reference id that most Indian PSPs require) returns the original result instead of charging again.
- **Never mark the order failed on a timeout.** Mark it `PAYMENT_PENDING` and settle the real status via the gateway's status API, a webhook, or a periodic **reconciliation job** that compares your records with the provider's.
- **Retry with backoff**, and only for retryable outcomes (timeouts, 5xx, connection resets). A `400` or "card declined" must not be retried.
- On your own APIs, make the operation idempotent server-side so *your* clients can retry safely too.

The one-line principle: **retries are only safe when the operation is idempotent**.""",
      "Say \"a timeout means unknown, not failed\" before proposing any retry; it is the sentence payment interviewers wait for.",
      options=[
          "It failed, so it is safe to retry with a new request.",
          "It succeeded; the gateway is just slow.",
          "Unknown: it may or may not have happened, so retry with the same idempotency key or query its status before deciding.",
          "The gateway rolls it back automatically on timeout.",
      ], answer=2,
      fix=f"""```java
{RETRY_FIX}
```""",
      askedAt=["Razorpay", "PhonePe", "Paytm", "Stripe"]),

    T("trap-distributed-systems-exactly-once-myth", A, "\"Kafka gives exactly-once, so no dedupe needed\"", "Advanced", "Very common",
      """Your Kafka consumer credits wallet balances in MySQL. A teammate says: "Kafka has exactly-once semantics now, so we don't need to handle duplicates." Is that right?""",
      "Yes: with `enable.idempotence=true` and Kafka transactions, each message is processed exactly once.",
      """"Exactly-once" is a real Kafka feature name, so people take it literally. It covers the **Kafka-to-Kafka** path: read from a topic, write to a topic and commit offsets in one Kafka transaction. Writes to MySQL, emails or HTTP calls are outside that transaction. Candidates also confuse the idempotent **producer** (no duplicate appends on producer retry) with an idempotent **consumer**, which is your job.""",
      """No. A consumer can apply the side effect, then crash or get rebalanced before committing the offset. The message is redelivered and the wallet is credited twice.

Over an unreliable network you can choose **at-most-once** (commit first, so messages can be lost) or **at-least-once** (commit after, so messages can repeat). "Exactly-once processing" in practice means **at-least-once delivery + idempotent processing**:

- **Dedupe table**: insert the event id into `processed_events` (primary key) **in the same DB transaction** as the business change. On a duplicate, the insert fails and you skip.
- **Naturally idempotent writes**: `UPSERT`, or conditional updates like `SET status='PAID' WHERE status='PENDING'`.
- Or store consumer offsets in the same DB transaction as the effect.

Also avoid auto-commit for important consumers: it commits on a timer, regardless of whether processing succeeded.""",
      "Define it precisely: \"exactly-once effect = at-least-once delivery + idempotent consumer\", then show where the dedupe key lives.",
      options=[
          "True: idempotent producer + transactions guarantee each credit happens once.",
          "False: Kafka's exactly-once covers Kafka-to-Kafka transactions; a side effect in MySQL can repeat after a crash or rebalance, so the consumer must be idempotent (dedupe on event id in the same DB transaction).",
          "True, as long as auto-commit is enabled.",
          "False: Kafka only supports at-most-once.",
      ], answer=1,
      fix="""```sql
BEGIN;
INSERT INTO processed_events(event_id) VALUES (:eventId);    -- PRIMARY KEY: duplicate => rollback & skip
UPDATE wallets SET balance = balance + :amount WHERE user_id = :userId;
COMMIT;
-- then commit the Kafka offset; a crash before that only replays an event we will skip
```""",
      askedAt=["PhonePe", "CRED", "Uber", "Confluent"]),

    T("trap-distributed-systems-dual-write", A, "Dual write: DB + Kafka in one method", "Advanced", "Very common",
      f"""What can go wrong here?

```java
{DUAL_BUGGY}
```""",
      "Nothing: `@Transactional` makes the save and the send atomic, and if Kafka fails the transaction rolls back.",
      """`@Transactional` looks like it covers everything inside the method, but it only controls the **database connection**. Kafka is a separate system with its own commit. Candidates also miss that `send()` is **asynchronous**: it returns a future, so a broker failure often never throws inside the method at all. Moving the send "after commit" feels like the fix but only closes one of the two gaps.""",
      """There are two failure windows, because two systems cannot commit atomically without a shared protocol:

1. **Ghost event**: the send succeeds, then the DB transaction rolls back (a constraint violation at flush or commit). Consumers act on an order that does not exist.
2. **Lost event**: the DB commits, but the send fails, the broker is down, or the pod dies first. The order exists, but nobody downstream ever hears about it. Payment, inventory and email silently diverge.

**Transactional outbox**: in the same DB transaction, insert an `outbox` row describing the event. A relay publishes outbox rows to Kafka and marks them sent. The relay is either a poller using `SELECT ... FOR UPDATE SKIP LOCKED`, or CDC such as Debezium tailing the binlog. Now the event exists **if and only if** the order does.

The relay can publish twice (a crash between send and mark), so delivery is at-least-once and consumers dedupe on the event id. Key messages by aggregate id to keep per-order ordering.""",
      "Name both windows (ghost event and lost event); most candidates only see one.",
      fix=f"""```java
{OUTBOX_FIX}
```""",
      askedAt=["Razorpay", "Swiggy", "Walmart", "Zalando"]),

    T("trap-distributed-systems-saga-vs-2pc", A, "Cross-service transactions: @Transactional, 2PC or saga", "Advanced", "Common",
      """Order, Inventory and Payment are separate services with separate databases. Placing an order must reserve stock and charge the customer, or do neither. The candidate says: "I'll wrap the three calls in `@Transactional`; if payment fails everything rolls back." How do you actually keep them consistent?""",
      "Wrap the service calls in `@Transactional`, or use XA/two-phase commit across the three databases.",
      """In a monolith, `@Transactional` really did make everything atomic, so the habit carries over. But it only governs the local database connection: an HTTP call to Inventory that already committed will not be undone. 2PC sounds like the textbook answer, but candidates can't explain why almost nobody runs it across microservices. Interviewers want to see that you know **sagas trade isolation for availability**, and how to cope with that.""",
      """**2PC/XA** blocks: participants hold locks while waiting for the coordinator, a coordinator failure can leave them stuck, and many brokers and NoSQL stores don't support it. Availability suffers.

**Saga**: a sequence of local transactions, each with a **compensating action**. Reserve stock → charge payment → confirm order. If the charge fails, release the stock and cancel the order.
- **Orchestration** (a central state machine, for example Temporal or a custom orchestrator) is easier to reason about and monitor. **Choreography** (services react to each other's events) suits short flows.
- **No isolation**: others can see intermediate states. Model them explicitly (`PENDING`, `RESERVED`) and treat them as semantic locks.
- **Compensations must be idempotent and retryable**, and every step must be triggered reliably (outbox).
- Order the steps so that irreversible actions (sending an email, shipping) come **last**, after the point of no return.""",
      "Say \"there is no rollback across services, only compensation\" and walk the failure path step by step.",
      fix="""```text
Orchestrated saga: place order
1. Order:     create order (PENDING)
2. Inventory: reserve items         -- compensation: release reservation
3. Payment:   charge (idempotency key = orderId)  -- compensation: refund
4. Order:     mark CONFIRMED  -> only now send email / start shipping
Failure at 3 -> run compensations in reverse: release stock (2), cancel order (1)
Every command & compensation: idempotent, retried with backoff, state persisted per step
```""",
      askedAt=["Flipkart", "Uber", "Amazon", "Myntra"]),

    T("trap-distributed-systems-clock-ordering", A, "Ordering events by wall-clock timestamps", "Advanced", "Common",
      """Two app servers can update the same document. Conflicts are resolved by keeping the write with the larger `System.currentTimeMillis()` (last-write-wins). Server B's clock is 300 ms behind server A's. What happens?""",
      "Nothing serious: NTP keeps server clocks in sync, so timestamps are a reliable global order.",
      """On one machine, timestamps really do order events, and NTP sounds like it makes all machines one machine. In reality, clocks drift, NTP corrects in jumps (sometimes backwards), VMs pause, and skew of milliseconds to seconds is normal. Candidates also use `currentTimeMillis()` to measure durations, so a clock adjustment produces negative or huge latencies. Interviewers test whether you know that **physical time is not a reliable ordering mechanism across machines**.""",
      """A write from B that **really happened later** can carry a *smaller* timestamp and be **silently discarded**. Nothing errors; data just disappears.

Use ordering that does not depend on clocks:
- **Version numbers with conditional writes** (optimistic locking): `UPDATE ... SET v = v + 1 WHERE id = ? AND v = ?`. Zero rows updated means someone else won, so re-read and retry or report a conflict. JPA's `@Version` does exactly this.
- **A single sequencer per key**: route all events for a key to one Kafka partition, and its offset is the order. Or use a DB-assigned sequence.
- **Logical clocks**: Lamport clocks give a consistent order; vector clocks detect truly concurrent writes so you can merge instead of dropping one.

Measure durations with `System.nanoTime()`, which is monotonic, never `currentTimeMillis()`.""",
      "Say \"I won't order across machines by wall clock; I'll use a version check or a per-key sequencer\".",
      options=[
          "Nothing: NTP keeps clocks within microseconds.",
          "A later write from B can be silently discarded because its timestamp is smaller.",
          "The database rejects the out-of-order write.",
          "Only reads are affected, not writes.",
      ], answer=1,
      fix="""```sql
-- optimistic concurrency instead of timestamps
SELECT body, version FROM documents WHERE id = 42;          -- version = 7
UPDATE documents SET body = :newBody, version = version + 1
 WHERE id = 42 AND version = 7;
-- 1 row  -> you won
-- 0 rows -> someone else wrote first: re-read, merge or return 409 Conflict
```""",
      askedAt=["Google", "Atlassian", "Amazon"]),

    T("trap-distributed-systems-lock-fencing", A, "Distributed lock without a fencing token", "Advanced", "Common",
      """A nightly payout job runs on 3 instances; only one may process it. The candidate's lock:

```text
SET lock:payout <instanceId> NX PX 30000     -- acquire, 30 s lease
...process payouts...
DEL lock:payout                              -- release
```

The interviewer says: "Instance 1 hits a 40-second GC pause in the middle of the job." What breaks, and how do you make it safe?""",
      "Make the lease longer (5 minutes) or renew it in a background thread, and it's safe.",
      """A lock feels absolute because in-process locks *are*: the JVM cannot "forget" you hold a `synchronized` block. A distributed lock is only a **lease** that expires while you are paused, and the paused process cannot notice. Longer TTLs and watchdog renewal (like Redisson's) shrink the window but cannot close it: the renewal thread pauses too. Interviewers want the words **fencing token** and an idempotent fallback.""",
      """What breaks:
1. The lease expires at 30 s, instance 2 acquires the lock, and **both run payouts**.
2. Instance 1 wakes up, finishes and calls `DEL`, deleting **instance 2's** lock, so instance 3 can enter too.

Fixes, in increasing strength:
- **Release only your own lock**: compare-and-delete in a Lua script using a unique token per acquisition.
- **Fencing token**: each lock grant comes with a monotonically increasing number (ZooKeeper zxid, etcd revision, or a DB sequence). The **resource** rejects writes carrying an older token. Redis locks do not provide this natively.
- **Make the work idempotent**: a unique constraint on `(user_id, payout_date)` means a second run cannot pay twice. This is the real safety net, and the lock becomes an efficiency optimisation.

The same reasoning applies to split brain: two nodes that both believe they are leader must be fenced by the storage layer.""",
      "Say \"a distributed lock is a lease, so correctness must come from fencing or idempotency, not from the lock\".",
      fix="""```text
-- 1. release only if it is still yours (Lua, atomic)
if redis.call("GET", KEYS[1]) == ARGV[1] then
  return redis.call("DEL", KEYS[1])
else
  return 0
end

-- 2. fencing: the resource checks the token from the lock service
UPDATE job_runs SET last_token = :token, status = 'RUNNING'
 WHERE job = 'payout-2026-10-09' AND last_token < :token;   -- 0 rows => you lost the lock, stop

-- 3. idempotent effect: a second run cannot double-pay
UNIQUE KEY uk_payout (user_id, payout_date)
```""",
      askedAt=["Uber", "Razorpay", "Atlassian"]),

    T("trap-distributed-systems-retry-storm", A, "Retry storms: retries at every layer, no backoff", "Intermediate", "Very common",
      """The recommendation service has a 2-minute blip. The mobile client retries failed calls 3 times immediately, the API gateway retries 3 times, and the BFF's HTTP client retries 3 times. The service comes back up and **immediately falls over again**. Why?""",
      "The service needs more instances; retries are always good for reliability.",
      """Each team adds retries locally because one retry clearly helps one request. Nobody multiplies across layers, and nobody pictures thousands of clients retrying **in lockstep**. Candidates also retry everything, including 400s, and ignore `Retry-After`. Interviewers ask this to see whether you think about the system as a whole, which is a core senior signal.""",
      """**Retry amplification**: each layer makes 1 + 3 = 4 attempts, and the layers nest, so one user action can become 4 × 4 × 4 = **64 requests** to the struggling service. Immediate retries arrive as synchronised waves (a thundering herd) and crush it the moment it recovers.

Fixes:
- **Retry at one layer**, usually closest to the failing dependency, and make the other layers fail fast.
- **Exponential backoff with jitter**, so clients spread out instead of retrying in sync.
- **Retry budget**: retries limited to about 10% of normal traffic.
- **Circuit breaker** (Resilience4j): after repeated failures, stop calling for a cool-down period and probe with a few requests.
- Retry only **idempotent, retryable** errors (timeouts, 503, connection resets) and honour `Retry-After`.

The cache-stampede variant has the same cure: add **TTL jitter** so keys don't expire together, and use single-flight loading on a miss.""",
      "Multiply the attempts across layers out loud; showing the 64x number is what makes this answer memorable.",
      fix=f"""```java
{BACKOFF}
```
Attempt 0 → 0-200 ms, attempt 1 → 0-400 ms, attempt 2 → 0-800 ms ... capped at `capMs`.""",
      askedAt=["Amazon", "Netflix", "Swiggy", "Hotstar"]),

    T("trap-distributed-systems-missing-timeouts", A, "Missing timeouts cause cascading failure", "Intermediate", "Very common",
      """Service A (Tomcat, 200 worker threads, 50 req/s) calls service B with a `RestTemplate` built with `new RestTemplate()`. B's database slows down and B now takes **60 seconds** to respond. What happens to A?""",
      "A's calls to B just become slow, but A's other endpoints keep working; `RestTemplate` times out after 30 seconds anyway.",
      """Defaults feel safe, so nobody checks them. `new RestTemplate()` (and the JDK `HttpClient`) have **no** read timeout by default, so they wait indefinitely. Candidates think of latency per request, not of **threads as a finite pool**. Little's law makes the outage obvious, but few people apply it. Interviewers also check whether your timeouts are consistent across hops, because mismatched values cause wasted work.""",
      """By Little's law, the number of requests in flight = arrival rate × latency = 50/s × 60 s = **3,000**. A has 200 threads, so within about 4 seconds every thread is blocked waiting on B. Now **A is down for all endpoints**, including those that never touch B, and A's callers start piling up the same way. That is a **cascading failure**.

Defences:
- **Explicit timeouts on every outbound call**: a connect timeout around 1 s, and a read timeout based on B's p99.9 latency, not on hope.
- **Deadline propagation**: each hop's timeout must fit inside the caller's remaining budget. An inner timeout longer than the outer one wastes work nobody is waiting for.
- **Bulkhead**: cap concurrent calls per dependency (separate pool or semaphore) so one slow dependency cannot take all threads.
- **Circuit breaker + fallback**: fail fast while B is unhealthy and serve cached or default data.""",
      "Quote Little's law with numbers (\"50/s × 60 s = 3,000 in flight vs 200 threads\") to show the failure, then list the defences.",
      options=[
          "Only A's calls to B are slow; everything else in A is fine.",
          "A's threads all block waiting on B, so A stops serving every endpoint and the failure cascades to A's callers.",
          "RestTemplate times out after 30 s by default, so A recovers.",
          "Tomcat automatically sheds the calls to B.",
      ], answer=1,
      fix=f"""```java
{TIMEOUT_FIX}
```""",
      askedAt=["Amazon", "Walmart", "Flipkart", "Goldman Sachs"]),
]

STUBS = """
import java.util.*;
import java.util.concurrent.*;
import java.lang.annotation.*;
"""
ANNOS = """
@Retention(RetentionPolicy.RUNTIME) @interface Transactional {}
@Retention(RetentionPolicy.RUNTIME) @interface Scheduled { long fixedDelay(); }
"""

CHECKS = [
    {"name": "ds-retry-idem", "lang": "java", "code": "import java.util.*;\nimport java.util.concurrent.*;\npublic class Main {\n" + """
  enum PaymentResult { OK, PENDING }
  interface Gateway { PaymentResult charge(String orderId, long amount, String key) throws TimeoutException; }
  static final class Order { String status = "NEW"; String id() { return "o1"; } String paymentAttemptKey() { return "k-1"; } void markPaymentPending() { status = "PENDING"; } }
  Set<String> keysSeen = new HashSet<>(); int calls = 0;
  Gateway gateway = (id, amt, key) -> { keysSeen.add(key); calls++; throw new TimeoutException(); };
""" + "\n".join("  " + l for l in BACKOFF.splitlines()) + "\n" + "\n".join("  " + l for l in RETRY_FIX.splitlines()) + """
  public static void main(String[] a) throws Exception {
    Main m = new Main(); Order o = new Order();
    PaymentResult r = m.chargeWithRetry(o, 50_000);
    System.out.println(r + " " + o.status + " calls=" + m.calls + " keys=" + m.keysSeen);
  }
}""", "expect": ["PENDING PENDING calls=3 keys=[k-1]"]},
    {"name": "ds-outbox", "lang": "java", "code": STUBS + """
public class Main {
  record OutboxEvent(UUID id, String type, String aggregateId, String payload) {}
  static final class Order { String getId() { return "o1"; } }
  interface OrderRepository { void save(Order o); }
  interface OutboxRepository { void save(OutboxEvent e); List<OutboxEvent> lockNextBatch(int n); void markSent(UUID id); }
  interface KafkaTemplate { CompletableFuture<String> send(String topic, String key, String value); }
  List<OutboxEvent> table = new ArrayList<>(); List<String> sent = new ArrayList<>();
  OrderRepository orderRepository = o -> {};
  OutboxRepository outboxRepository = new OutboxRepository() {
    public void save(OutboxEvent e) { table.add(e); }
    public List<OutboxEvent> lockNextBatch(int n) { return new ArrayList<>(table); }
    public void markSent(UUID id) { table.removeIf(x -> x.id().equals(id)); }
  };
  KafkaTemplate kafkaTemplate = (t, k, v) -> { sent.add(t + ":" + k); return CompletableFuture.completedFuture("ok"); };
  String toJson(Order o) { return "{}"; }
""" + "\n".join("  " + l for l in OUTBOX_FIX.splitlines()) + """
  public static void main(String[] a) { Main m = new Main(); m.placeOrder(new Order()); m.relayOutbox(); System.out.println(m.sent + " left=" + m.table.size()); }
}""" + ANNOS, "expect": ["[order-placed:o1] left=0"]},
    {"name": "ds-dual-buggy-compiles", "lang": "java", "code": STUBS + """
public class Main {
  static final class Order { String getId() { return "o1"; } }
  interface OrderRepository { void save(Order o); }
  interface KafkaTemplate { CompletableFuture<String> send(String topic, String key, String value); }
  OrderRepository orderRepository = o -> {};
  KafkaTemplate kafkaTemplate = (t, k, v) -> CompletableFuture.completedFuture("ok");
  String toJson(Order o) { return "{}"; }
""" + "\n".join("  " + l for l in DUAL_BUGGY.splitlines()) + """
  public static void main(String[] a) { new Main().placeOrder(new Order()); System.out.println("compiled"); }
}""" + ANNOS, "expect": ["compiled"]},
    {"name": "ds-backoff", "lang": "java", "code": "import java.util.concurrent.*;\npublic class Main {\n" + BACKOFF + """
  public static void main(String[] a) {
    long max0 = 0, max2 = 0, max30 = 0, min = Long.MAX_VALUE;
    for (int i = 0; i < 100000; i++) { max0 = Math.max(max0, backoffMillis(0, 200, 2000)); max2 = Math.max(max2, backoffMillis(2, 200, 2000)); long x = backoffMillis(30, 200, 2000); max30 = Math.max(max30, x); min = Math.min(min, x); }
    System.out.println(max0 + " " + max2 + " " + max30 + " " + min);
  }
}""", "expect": ["200 800 2000 0"]},
    {"name": "ds-timeouts", "lang": "java", "code": "import java.net.URI;\nimport java.net.http.*;\nimport java.time.Duration;\npublic class Main {\n  public static void main(String[] a) {\n" + TIMEOUT_FIX + """
    System.out.println(client.connectTimeout().get() + " " + request.timeout().get() + " default=" + HttpRequest.newBuilder(URI.create("http://x")).build().timeout().isPresent() + " " + HttpClient.newHttpClient().connectTimeout().isPresent());
  }
}""", "expect": ["PT1S PT0.8S default=false false"]},
]
