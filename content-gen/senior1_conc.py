from senior1_common import build, B, I, A

NOTES = [
("The Concurrency Round: Format and How to Answer", r"""
## What the round looks like in 2026
Concurrency shows up in three forms, sometimes all in one loop:
1. **Discussion:** "Two workers sometimes process the same job. Fix it." "Users get charged twice. Why?"
2. **Practical coding (45-60 min):** build a thread-safe component (booking service, per-user rate limiter, job scheduler with retry), then a follow-up: *"Now it runs on 3 instances."*
3. **Code review:** spot the race in a Spring service.

The follow-up is where seniors are separated from juniors. `synchronized` and `ConcurrentHashMap` protect **one JVM**. Production runs many instances, so the **database, the queue or an idempotency key** has to be the arbiter.

## The four-part answer
Strong answers name the race precisely. Use this template:
1. **The invariant:** "a seat has at most one confirmed booking", "stock never goes below zero", "a job runs on one worker at a time", "a payment intent is charged at most once".
2. **The interleaving that breaks it:** draw the timeline.
3. **The prevention, at the right layer:** constraint, conditional update, lock, idempotency key, partitioning. Say **why** that layer.
4. **The test and the fix's own failure modes:** deadlocks, retries, lease expiry, crash halfway.

```text
Invariant: seat A7 is booked at most once

 T1 (user Asha)                         T2 (user Ravi)
 SELECT status FROM seats WHERE A7 -> AVAILABLE
                                        SELECT status FROM seats WHERE A7 -> AVAILABLE
 UPDATE seats SET status='BOOKED', user=Asha
                                        UPDATE seats SET status='BOOKED', user=Ravi   <- overwrites
 both get "Booking confirmed!"  ->  invariant broken
```

## Two shapes behind most races
- **Check-then-act:** `if (seatFree) book()`. Two threads both pass the check before either acts.
- **Read-modify-write:** `stock = read(); write(stock - 1)`. Two threads read the same value, so one update is lost.

Both have a **gap between reading and writing** where another actor can step in. Every fix either **removes the gap** (one atomic statement), **detects the conflict** (version check, unique constraint) or **excludes others during the gap** (a lock).

## Choosing the layer
| Situation | First choice |
|---|---|
| Uniqueness (one booking per seat, one account per email) | `UNIQUE` constraint |
| Counter or stock decrement | Atomic conditional `UPDATE ... WHERE stock >= ?` |
| State machine transition (PENDING -> PAID) | Compare-and-set `UPDATE ... WHERE status = ?` |
| Edit a whole entity, low contention, user think-time | Optimistic locking (`@Version`) |
| Multi-step update on a few hot rows | `SELECT ... FOR UPDATE` in a short transaction |
| Duplicate requests, retries, redeliveries | Idempotency key with a unique constraint |
| Distributing work to many workers | Claim with conditional `UPDATE` or `SKIP LOCKED`; partition by key |
| Side effects outside the DB, across instances | Distributed lock **plus** fencing, as a last resort |
| In-memory state inside one JVM | `java.util.concurrent` atomics, concurrent maps, locks |

## Phrases that signal seniority
- "`synchronized` only protects one JVM. With three pods I need the database to arbitrate."
- "I'll check the **affected row count**. Zero rows means someone else won."
- "What happens if the process dies between charging and saving?"
- "Retries are inevitable, so the operation must be **idempotent**."
- "I'd prove it with a test that fires 50 threads through a start gate and asserts exactly one success."

## A lost update you can run
```java
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicLong;

public class LostUpdateDemo {
    static long plain = 0;                         // read-modify-write, unsafe
    static final AtomicLong atomic = new AtomicLong();

    public static void main(String[] args) throws InterruptedException {
        int threads = 8, perThread = 100_000;
        CountDownLatch start = new CountDownLatch(1), done = new CountDownLatch(threads);
        try (ExecutorService pool = Executors.newFixedThreadPool(threads)) {
            for (int t = 0; t < threads; t++) {
                pool.submit(() -> {
                    try {
                        start.await();                 // everyone starts together
                        for (int i = 0; i < perThread; i++) {
                            plain++;                   // load, add, store: not atomic
                            atomic.incrementAndGet();  // CAS loop: atomic
                        }
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    } finally {
                        done.countDown();
                    }
                });
            }
            start.countDown();
            done.await();
        }
        System.out.println("expected=" + (long) threads * perThread
                + " plain=" + plain + " atomic=" + atomic.get());
    }
}
```
A typical run prints something like `expected=800000 plain=231847 atomic=800000`. The same thing happens with database rows, just more slowly.
"""),

("Race Conditions in Real Systems", r"""
Interviewers like these because each one has caused real outages and money loss. For each, know the **invariant**, the **race** and the **impact**.

## 1. Double booking (BookMyShow, hotel, doctor slots)
Two users pick seat A7 within milliseconds. Both read `AVAILABLE`, both write `BOOKED`. Two tickets, one seat, an angry customer at the cinema. With "hold for 10 minutes" flows there's a second race: the hold expires while payment is in flight and someone else grabs the seat.

## 2. Double charge
Causes: the user **double-clicks** Pay; the mobile app **retries after a timeout** while the first request is still running; a load balancer retries; the payment provider **redelivers a webhook**. Without dedupe, each attempt charges the card. It's the classic case for **idempotency keys**.

## 3. Inventory oversell (flash sales)
```java
@Transactional
public void buy(long productId, int qty) {
    Product p = productRepo.findById(productId).orElseThrow();   // T1 and T2 both read stock = 1
    if (p.getStock() < qty) throw new OutOfStockException();     // both pass
    p.setStock(p.getStock() - qty);                              // both write stock = 0
    orderRepo.save(new Order(productId, qty));                   // two orders for one unit
}
```
**Why `@Transactional` and REPEATABLE READ don't save you:** InnoDB's plain `SELECT` is a **non-locking consistent read** from a snapshot, so both transactions see `stock = 1`. Hibernate's flush issues `UPDATE product SET stock = 0 WHERE id = ?`. T2's update waits for T1's row lock, then **overwrites** it. Both commit. This is a *lost update*, and the isolation level doesn't prevent it unless you use locking reads or version checks.

## 4. Two workers claim the same task
```sql
SELECT id FROM tasks WHERE status = 'QUEUED' ORDER BY id LIMIT 1;   -- both workers get id 42
UPDATE tasks SET status = 'RUNNING' WHERE id = 42;                  -- both "succeed"
```
The job runs twice: two emails, two exports, two payouts. Classic check-then-act across processes.

## 5. Lost update on edits
Two admins open the same product form, one changes the price and the other the description. The last save wins and silently undoes the first change, because the full entity was written back.

## 6. A scheduled job on every instance
`@Scheduled(cron = "0 0 9 * * *") sendDailyDigest()` runs on **all N pods**, so users get N emails. Fixes: a cluster lock (ShedLock), a single scheduler service, or claiming work rows atomically.

## 7. Ordering races
`OrderShipped` gets processed before `OrderPaid` because events for the same order landed on different partitions or consumers. The state machine rejects it, or worse, accepts an invalid transition.

## Two traps interviewers love
**Trap 1: `synchronized` with multiple instances.** It locks a monitor inside one JVM. Pod B never sees pod A's monitor.

**Trap 2: `synchronized` + `@Transactional` in the *same* JVM is still broken.**
```java
@Transactional
public synchronized void reserve(long id) { ... }   // the lock is released when the method returns,
                                                    // but the proxy commits AFTER that
```
Thread 2 enters as soon as thread 1 leaves the method body, **before thread 1's commit**, so it reads the old stock. The lock has to wrap the whole transaction (lock outside the proxy), or better, use the DB.

## How to spot races in code review
```text
read  ->  decide  ->  write          with no atomicity between them? (check-then-act / RMW)
"exists?" then "insert"              without a unique constraint?
entity.setX(entity.getX() - n)       on a shared row without @Version or a conditional UPDATE?
external call + DB write             not idempotent, no key? (retries -> duplicates)
@Scheduled / consumer                running on N instances or redelivered?
static / singleton mutable field     in a Spring bean (all requests share it)?
```
The last one is common in service-company code: a `private List<Item> cache = new ArrayList<>()` field in a `@Service`. The bean is a singleton shared by all request threads, so that's a data race and a memory leak at once.
"""),

("Database Guards: Constraints, Conditional Updates and Task Claiming", r"""
When several instances share a database, **let the database arbitrate**. It already has atomic statements, row locks and constraints, and it's the source of truth.

## Guard 1: unique constraints (uniqueness invariants)
```sql
CREATE TABLE seat_booking (
  show_id    BIGINT      NOT NULL,
  seat_no    VARCHAR(8)  NOT NULL,
  booking_id BIGINT      NOT NULL,
  created_at TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (show_id, seat_no)          -- at most one row per seat per show
);
```
```java
try {
    seatBookingRepo.saveAndFlush(new SeatBooking(showId, seatNo, bookingId));  // flush forces the INSERT now
    return BookingResult.confirmed(bookingId);
} catch (DataIntegrityViolationException e) {
    return BookingResult.seatTaken(seatNo);
}
```
No matter how many pods race, InnoDB lets exactly one `INSERT` win. Keep the application-level "is it free?" check as well, but only for **user-friendly errors**. The constraint is the guarantee.

## Guard 2: atomic conditional UPDATE (counters, stock)
```sql
UPDATE product SET stock = stock - :qty
WHERE id = :id AND stock >= :qty;          -- 1 row = reserved, 0 rows = sold out
```
```java
@Modifying
@Query("update Product p set p.stock = p.stock - :qty where p.id = :id and p.stock >= :qty")
int tryReserve(@Param("id") long id, @Param("qty") int qty);

@Transactional
public void buy(long id, int qty) {
    if (productRepo.tryReserve(id, qty) == 0) throw new OutOfStockException(id);
    orderRepo.save(new Order(id, qty));
}
```
The check and the write happen in **one statement** under the row lock, so there's no gap. Concurrent buyers queue on the row lock for microseconds. That's far simpler than distributed locks and it scales well. (A bulk JPQL update bypasses the persistence context, so don't rely on an already-loaded `Product` entity afterwards.)

## Guard 3: compare-and-set state transitions
```sql
UPDATE payment SET status = 'CAPTURED', captured_at = NOW()
WHERE id = :id AND status = 'AUTHORIZED';  -- only one caller can move it out of AUTHORIZED
```
Zero rows means it was already captured or cancelled, so reload and respond accordingly. This makes state machines safe against duplicate events and concurrent admins.

## Guard 4: task claiming (two workers, one job)
```java
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class TaskClaimer {
    private final Connection conn;
    private final String workerId;

    public TaskClaimer(Connection conn, String workerId) {
        this.conn = conn;
        this.workerId = workerId;
    }

    /** Option A: claim one known task. Whoever flips QUEUED -> RUNNING first wins; the loser updates 0 rows. */
    public boolean tryClaim(long taskId) throws SQLException {
        String sql = "UPDATE tasks SET status = 'RUNNING', owner = ?, attempts = attempts + 1, "
                + "lease_until = NOW() + INTERVAL 5 MINUTE WHERE id = ? AND status = 'QUEUED'";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, workerId);
            ps.setLong(2, taskId);
            return ps.executeUpdate() == 1;
        }
    }

    /** Option B: claim a batch. SKIP LOCKED (MySQL 8+) makes concurrent workers pick different rows. */
    public List<Long> claimBatch(int max) throws SQLException {
        List<Long> ids = new ArrayList<>();
        conn.setAutoCommit(false);
        try {
            String pick = "SELECT id FROM tasks WHERE status = 'QUEUED' AND run_at <= NOW() "
                    + "ORDER BY run_at LIMIT ? FOR UPDATE SKIP LOCKED";
            try (PreparedStatement ps = conn.prepareStatement(pick)) {
                ps.setInt(1, max);
                try (ResultSet rs = ps.executeQuery()) {
                    while (rs.next()) ids.add(rs.getLong(1));
                }
            }
            String mark = "UPDATE tasks SET status = 'RUNNING', owner = ?, attempts = attempts + 1, "
                    + "lease_until = NOW() + INTERVAL 5 MINUTE WHERE id = ?";
            try (PreparedStatement ps = conn.prepareStatement(mark)) {
                for (long id : ids) {
                    ps.setString(1, workerId);
                    ps.setLong(2, id);
                    ps.addBatch();
                }
                ps.executeBatch();
            }
            conn.commit();
            return ids;
        } catch (SQLException e) {
            conn.rollback();
            throw e;
        } finally {
            conn.setAutoCommit(true);
        }
    }

    /** Complete only if we still own it: a worker whose lease expired cannot overwrite the new owner. */
    public boolean complete(long taskId) throws SQLException {
        String sql = "UPDATE tasks SET status = 'DONE' WHERE id = ? AND owner = ? AND status = 'RUNNING'";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, taskId);
            ps.setString(2, workerId);
            return ps.executeUpdate() == 1;
        }
    }

    public static void main(String[] args) throws SQLException {
        // usage: java TaskClaimer jdbc:mysql://localhost:3306/jobs user password
        try (Connection c = DriverManager.getConnection(args[0], args[1], args[2])) {
            TaskClaimer worker = new TaskClaimer(c, "worker-" + ProcessHandle.current().pid());
            for (long id : worker.claimBatch(10)) {
                System.out.println("claimed " + id + ", completed=" + worker.complete(id));
            }
        }
    }
}
```
**Crash recovery:** a worker can die mid-task, so claims are **leases**. A reaper re-queues expired ones:
```sql
UPDATE tasks SET status = 'QUEUED', owner = NULL
WHERE status = 'RUNNING' AND lease_until < NOW() AND attempts < 5;   -- after 5 attempts: FAILED / dead letter
```
Because a task may run again after a crash, **the task itself must be idempotent** (dedupe its side effects with a key). Long tasks renew their lease with a heartbeat.

## What to say about trade-offs
- Constraints and conditional updates: simplest and strongest, but limited to single-row or single-table invariants.
- A hot row (one product in a flash sale) serialises writers. Fine up to thousands of updates per second; beyond that, shard the counter or allocate stock in batches.
- Always **check the affected row count**. Ignoring it is the most common bug in "fixed" code.
"""),

("Optimistic vs Pessimistic Locking in JPA", r"""
## Optimistic locking: detect conflicts at write time
```java
@Entity
public class Product {
    @Id private Long id;
    private String name;
    private int stock;
    @Version private long version;     // managed by Hibernate
}
```
On flush, Hibernate writes:
```sql
UPDATE product SET name = ?, stock = ?, version = 6 WHERE id = ? AND version = 5;
```
If another transaction already moved the row to version 6, the update affects **0 rows** and Hibernate throws `OptimisticLockException` (Spring translates it to `ObjectOptimisticLockingFailureException`). No locks are held while the user or code is "thinking".

**Handling a conflict:**
- **Interactive edit:** return **409 Conflict** ("someone else changed this, reload"). Send the version to the client (DTO field or `ETag`), and have it send the version back (`If-Match`) so the check spans HTTP requests.
- **Automatic operation:** retry in a **new transaction** with backoff:
```java
public void reserveWithRetry(long id, int qty) {
    for (int attempt = 1; ; attempt++) {
        try {
            tx.executeWithoutResult(status -> reserve(id, qty));   // TransactionTemplate: fresh tx per attempt
            return;
        } catch (ObjectOptimisticLockingFailureException e) {
            if (attempt == 3) throw e;
            sleepQuietly(20L * attempt + ThreadLocalRandom.current().nextInt(20));
        }
    }
}
```
Retrying *inside* the same `@Transactional` method doesn't work: the persistence context is stale and the transaction is marked rollback-only.

## Pessimistic locking: block others up front
```java
public interface AccountRepository extends JpaRepository<Account, Long> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)                 // SELECT ... FOR UPDATE
    @Query("select a from Account a where a.id = :id")
    Optional<Account> findForUpdate(@Param("id") long id);
}
```
The row stays locked until commit or rollback. Other `FOR UPDATE` readers and writers wait (plain snapshot `SELECT`s don't). On MySQL, Hibernate maps a lock timeout of 0 to `NOWAIT` (and the special SKIP_LOCKED value to `SKIP LOCKED`). Otherwise waits are bounded by `innodb_lock_wait_timeout` (default 50 s), which you can lower per session for OLTP paths.

**Rules:** keep the transaction **short**, never make remote calls while holding locks, and **always lock rows in a consistent order**.

## Deadlocks and lock ordering
```text
T1: transfer(A -> B)  locks A ...... wants B (held by T2)  \
T2: transfer(B -> A)  locks B ...... wants A (held by T1)  /  deadlock
```
InnoDB detects the cycle and rolls one back (`ERROR 1213: Deadlock found`). Prevent it by **locking in a global order** (lower account ID first). Still treat deadlocks as possible: retry the victim transaction once or twice.
```java
@Transactional
public void transfer(long from, long to, BigDecimal amount) {
    long first = Math.min(from, to), second = Math.max(from, to);
    Account a = accounts.findForUpdate(first).orElseThrow();
    Account b = accounts.findForUpdate(second).orElseThrow();
    Account src = (a.getId() == from) ? a : b, dst = (src == a) ? b : a;
    src.debit(amount);   // throws if insufficient funds
    dst.credit(amount);
}
```

## InnoDB details that come up in deep-dive rounds
- Under **REPEATABLE READ** (MySQL's default), locking reads take **next-key locks** (record plus the gap before it) on the index ranges they scan. `SELECT ... FOR UPDATE WHERE status = 'QUEUED'` on a non-unique or unindexed column can lock far more than you expect and block inserts.
- An equality lock on a **unique** index for an existing row locks only that record.
- `FOR UPDATE` on a **missing** row takes a gap lock. Two transactions doing "lock if exists, else insert" can deadlock on each other's gap locks. Prefer `INSERT ... ON DUPLICATE KEY UPDATE` or catching the duplicate-key error.
- Locks are taken on **index entries**. Without a usable index, an `UPDATE` can lock every scanned row.

## Which one to choose
| Factor | Optimistic (`@Version`) | Pessimistic (`FOR UPDATE`) |
|---|---|---|
| Contention | Low to moderate | High, on a few hot rows |
| Cost when no conflict | Nearly free | Lock overhead, blocked readers using locking reads |
| On conflict | Exception, so retry or 409 | Waiting, timeouts, possible deadlocks |
| Spans user think-time / HTTP requests | Yes (version in the DTO) | No: never hold DB locks across requests |
| Typical use | Edit forms, entity updates, carts | Money transfers, allocating from a small pool |

And remember the third option, often better than both: a **single conditional `UPDATE`** (`stock = stock - 1 WHERE stock >= 1`). It holds the lock for the shortest time possible and needs no retry loop.
"""),

("Idempotency Keys and Exactly-Once Effects", r"""
## Why idempotency is unavoidable
Networks fail **ambiguously**. When a payment call times out, the client can't tell whether the charge happened before or after the failure. The only safe choice is to **retry**, so the server must make retries harmless. In distributed systems you get **at-least-once delivery**. **At-least-once delivery + idempotent processing = effectively-once effects.** That's the realistic version of "exactly once".

An operation is **idempotent** if doing it N times has the same effect as doing it once. `PUT /users/7/email` (set to a value) is naturally idempotent. `POST /payments` (charge 500) is not, unless you add a key.

## The idempotency key pattern (as popularised by Stripe)
The client generates a unique key (a UUID) **per logical operation** and sends it as `Idempotency-Key`. Retries reuse the same key.
```sql
CREATE TABLE idempotency_record (
  client_id     BIGINT       NOT NULL,
  idem_key      VARCHAR(64)  NOT NULL,
  request_hash  CHAR(64)     NOT NULL,          -- SHA-256 of the canonical request body
  status        VARCHAR(16)  NOT NULL,          -- IN_PROGRESS | COMPLETED
  response_code INT          NULL,
  response_body JSON         NULL,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (client_id, idem_key)             -- the unique constraint is the arbiter
);
```
```text
request(key) --> INSERT (client, key, hash, IN_PROGRESS)
                  |                         |
              inserted                 duplicate key -> load existing row
                  |                         |-- COMPLETED, same hash   -> replay stored response
                  v                         |-- COMPLETED, other hash  -> 422 (key reused for a different request)
          do the work                       '-- IN_PROGRESS            -> 409 "still processing, retry later"
          (pass the key downstream too)
                  |
          UPDATE row -> COMPLETED + response code/body
```
```java
@Transactional
public PaymentResponse pay(long clientId, String key, PaymentRequest req) {
    String hash = sha256Hex(canonicalJson(req));        // fingerprint of the request body
    Optional<IdempotencyRecord> existing = records.tryInsertInProgress(clientId, key, hash);
    if (existing.isPresent()) return replayOrReject(existing.get(), hash);  // replay / 409 / 422

    Payment p = payments.save(Payment.pending(req));
    ChargeResult r = gateway.charge(req, key);   // provider dedupes on the same key
    p.markCaptured(r.chargeId());
    PaymentResponse resp = PaymentResponse.from(p);
    records.complete(clientId, key, 201, resp);
    return resp;
}
```
`tryInsertInProgress` runs `INSERT IGNORE` (or catches the duplicate-key error) and returns the existing row if one was already there.

## The details interviewers probe
- **Scope** keys per client or merchant, so two clients can't collide.
- Store a **request fingerprint**. Same key with a different body is a client bug, so reject it.
- **Concurrent duplicates:** the unique constraint lets one request win; the other sees `IN_PROGRESS` and gets 409 (or waits briefly and replays).
- **A crash halfway** leaves `IN_PROGRESS` rows behind. A recovery job asks the provider about that key, then completes or clears the row. That's why the key must go **downstream** too.
- **Long remote calls inside a DB transaction** hold a connection (see pool exhaustion). Production designs often split this: commit the key row and PENDING payment first, call the provider, then commit the result. They rely on the provider's idempotency and a reconciliation job.
- **Retention:** keep keys for 24 hours to a few days, matching how long clients may retry.
- **Only cache final results.** A 5xx from your side shouldn't be stored as the permanent answer unless the operation definitely failed without side effects.

## Idempotent consumers (Kafka, SQS, webhooks)
Brokers redeliver after rebalances, crashes and timeouts. Record processed message IDs **in the same transaction** as the business change:
```java
@Transactional
public void onPaymentCaptured(PaymentCaptured evt) {
    if (processed.insertIgnore(evt.eventId()) == 0) return;   // duplicate: already handled
    orders.markPaid(evt.orderId());                           // committed together with the dedupe row
}
```
If the transaction rolls back, the dedupe row rolls back too, so a retry processes it properly. This is the *inbox* pattern. Its mirror image is the **outbox**: write the business row and the event row in one transaction, and let a relay publish the event. That avoids the "DB committed but Kafka publish failed" dual-write problem.

## Natural idempotency is even better
Prefer operations that are idempotent by design:
- **Set** a value instead of incrementing it.
- **Upsert** by a business key (`INSERT ... ON DUPLICATE KEY UPDATE`).
- **CAS state transitions:** `WHERE status = 'AUTHORIZED'`, so a second capture is a no-op.
- **Deterministic IDs** from the business key (`order-{cartId}`), so duplicates collide on the primary key.
"""),

("Distributed Locks: Redis, Leases and Fencing Tokens", r"""
## First question: do you really need one?
Most "we need a distributed lock" problems are better solved by the **database** (unique constraint, conditional update, `FOR UPDATE`) or by **partitioning** (all events for an order go to one Kafka partition, so one consumer handles them). Reach for a distributed lock when you must coordinate something **outside** the database: calling a non-idempotent third-party API once, generating a nightly report on exactly one node, writing to a shared file.

Kleppmann's distinction helps:
- **Efficiency lock:** avoids duplicate *work*. A rare double execution is tolerable (two nodes generate the same cache entry).
- **Correctness lock:** a double execution *corrupts data or loses money*. This needs much stronger guarantees.

## A single-node Redis lock done right
```text
SET lock:payout:2026-10-09 <random-token> NX PX 30000      # acquire: only if absent, 30 s lease
... do the work ...
# release ONLY if we still own it (atomic compare-and-delete in Lua):
if redis.call("get", KEYS[1]) == ARGV[1] then return redis.call("del", KEYS[1]) else return 0 end
```
- `NX` gives mutual exclusion. `PX` gives a **lease**, so a crashed holder doesn't block everyone forever.
- The **random token** stops you from deleting someone else's lock after yours expired.
- **Redisson** wraps this: `RLock lock = redisson.getLock("lock:order:42"); if (lock.tryLock(2, TimeUnit.SECONDS)) { try { ... } finally { lock.unlock(); } }`. Without an explicit lease time, its **watchdog** keeps extending the lease (default 30 s) while the holder's JVM is alive.

## The lease problem
```text
Client A: acquire lock (lease 30 s) .... [ long GC pause / network stall: 40 s ] .... writes to storage  <- stale!
Redis:                               lease expires at 30 s
Client B:                                  acquire lock ........ writes to storage
```
Both A and B believe they hold the lock. Checking "do I still hold it?" just before writing doesn't help, because the pause can happen **between the check and the write**. Watchdog renewal shrinks the window but can't close it: a paused JVM can't renew anything.

## Fencing tokens
Have the lock service hand out a **monotonically increasing token** with each grant (33, then 34). The **protected resource** remembers the highest token it has accepted and rejects anything older:
```sql
UPDATE payout_batch SET status = 'SENT', fence = :token
WHERE id = :batchId AND fence < :token;     -- A arrives late with token 33 after B wrote with 34 -> 0 rows
```
Now safety no longer depends on timing. It depends on the resource checking the token. ZooKeeper (zxid / znode version) and etcd (revision) provide natural fencing tokens. Redis's random lock values aren't monotonic. (You can `INCR` a counter, but replication failover can still break the guarantees.)

## Redlock in one paragraph
Redlock acquires the lock on a majority of N independent Redis nodes. Kleppmann argued it's unsafe for correctness because it relies on bounded network delay, bounded pauses and well-behaved clocks, and it offers no fencing. Redis's author disputed parts of that argument. The interview-safe position: **use Redis locks for efficiency; for correctness, use the database or a consensus system (ZooKeeper / etcd) and fence every write**.

## Scheduled jobs across instances
```java
@Scheduled(cron = "0 0 2 * * *")
@SchedulerLock(name = "nightlyPayouts", lockAtMostFor = "PT30M", lockAtLeastFor = "PT1M")
public void nightlyPayouts() { payoutService.runBatch(); }
```
ShedLock stores the lock in a DB table (or Redis), so only one instance runs the job. `lockAtMostFor` is the lease if the node dies; `lockAtLeastFor` stops a fast job from running again on a node whose clock is slightly behind. The job should **still be idempotent** (claim payout rows with conditional updates), because leases can expire.

## Other options
- **DB lock row:** `SELECT * FROM job_lock WHERE name = 'payouts' FOR UPDATE` inside a transaction. Simple, but it holds a connection and transaction for the job's duration.
- **MySQL `GET_LOCK('payouts', 5)`:** a named, session-scoped lock. Careful with connection pools: the lock belongs to the *connection*, and it's released if the connection drops.
- **Leader election** (Kubernetes Lease objects, Spring Integration leader election) for "one active instance" roles.

## A decision ladder
```text
Can a UNIQUE constraint / conditional UPDATE express the invariant?   -> do that
Can partitioning give each key a single owner (Kafka partition)?      -> do that
Is it an efficiency concern (avoid duplicate work)?                   -> Redis lock / ShedLock
Is it correctness-critical outside the DB?                            -> consensus lock + fencing token
                                                                         + idempotent side effects
```
"""),

("Java-Level Concurrency for Practical Rounds", r"""
In machine-coding and practical rounds you'll build **in-memory** components: a rate limiter, an LRU/TTL cache, a booking service, a job scheduler. These are the tools and the traps.

## ConcurrentHashMap: use the atomic compound operations
```java
// BROKEN: check-then-act across two calls; another thread can slip in between
if (!seats.containsKey(seatId)) seats.put(seatId, userId);

// Atomic alternatives
String winner = seats.putIfAbsent(seatId, userId);           // null means we won
counts.merge(word, 1, Integer::sum);                         // atomic increment per key
sessions.computeIfAbsent(userId, id -> new Session(id));     // create exactly once per key
buckets.compute(userId, (id, b) -> refillAndTake(b));        // atomic read-modify-write per key
```
Rules for `compute*` and `merge`: the function runs **while holding that bin's lock**. Keep it short and pure: no I/O, no blocking, and **never modify the same map inside it** (that can deadlock or throw). `size()` and iteration are only weakly consistent.

## Atomics
- `AtomicLong` / `AtomicInteger`: lock-free CAS. `incrementAndGet`, `compareAndSet(expected, new)`, `updateAndGet(fn)`.
- `LongAdder`: spreads contended increments over cells. Much faster for **hot counters** (metrics), but `sum()` isn't an atomic snapshot, so don't use it for IDs or limits.
- `AtomicReference<ImmutableState>` with `updateAndGet`: replace a whole immutable object atomically. The function may run **more than once** under contention, so it must have no side effects.

## Locks
| Tool | Use when |
|---|---|
| `synchronized` | Simple critical sections. Less code and can't forget to unlock |
| `ReentrantLock` | You need `tryLock(timeout)`, interruptible waits, fairness or several `Condition`s |
| `ReadWriteLock` | Many readers, rare writers, and the read section is non-trivial |
| `Semaphore` | Limiting concurrency (at most 20 calls to a partner API) |

```java
private final ReentrantLock lock = new ReentrantLock();
if (lock.tryLock(200, TimeUnit.MILLISECONDS)) {
    try { /* critical section */ } finally { lock.unlock(); }   // ALWAYS unlock in finally
} else {
    throw new BusyException();                                 // fail fast instead of piling up
}
```
**Per-key locking** (lock one booking, not all bookings): `ConcurrentHashMap<String, ReentrantLock>` with `computeIfAbsent`, or a fixed array of lock stripes indexed by `hash(key) % N`, so the map doesn't grow forever.

## Executors
- Prefer a **bounded** `ThreadPoolExecutor` (bounded queue plus a rejection policy) over `Executors.newFixedThreadPool`, whose queue is unbounded and becomes a memory leak under overload.
- Shut executors down (try-with-resources works on `ExecutorService` from Java 19+). Name your threads so they're readable in dumps.
- **Virtual threads (Java 21):** `Executors.newVirtualThreadPerTaskExecutor()`. One cheap thread per task, **never pooled**. Limit access to scarce resources with a `Semaphore`. They don't make shared mutable state any safer: races are still races.

## A complete per-user rate limiter (a common practical prompt)
```java
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.LongSupplier;

public class TokenBucketLimiter {
    private record Bucket(double tokens, long lastRefillNanos) {}

    private final ConcurrentHashMap<String, Bucket> buckets = new ConcurrentHashMap<>();
    private final double capacity;
    private final double refillPerNano;
    private final LongSupplier clock;                     // injectable: tests control time

    public TokenBucketLimiter(int capacity, int refillPerSecond, LongSupplier clock) {
        this.capacity = capacity;
        this.refillPerNano = refillPerSecond / 1_000_000_000.0;
        this.clock = clock;
    }

    public boolean tryAcquire(String userId) {
        boolean[] allowed = new boolean[1];
        buckets.compute(userId, (id, b) -> {              // atomic per user, no global lock
            long now = clock.getAsLong();
            Bucket cur = (b == null) ? new Bucket(capacity, now) : b;
            double tokens = Math.min(capacity, cur.tokens() + (now - cur.lastRefillNanos()) * refillPerNano);
            allowed[0] = tokens >= 1.0;
            return new Bucket(allowed[0] ? tokens - 1.0 : tokens, now);
        });
        return allowed[0];
    }

    public static void main(String[] args) throws InterruptedException {
        long[] now = {0L};
        TokenBucketLimiter limiter = new TokenBucketLimiter(5, 1, () -> now[0]);
        System.out.println("burst of 100 concurrent calls, allowed = " + burst(limiter, 100));  // 5
        now[0] += 2_000_000_000L;                                                              // +2 s
        System.out.println("after 2 s, allowed = " + burst(limiter, 100));                     // 2
    }

    static int burst(TokenBucketLimiter limiter, int threads) throws InterruptedException {
        AtomicInteger ok = new AtomicInteger();
        CountDownLatch start = new CountDownLatch(1), done = new CountDownLatch(threads);
        try (ExecutorService pool = Executors.newFixedThreadPool(16)) {
            for (int i = 0; i < threads; i++) {
                pool.submit(() -> {
                    try {
                        start.await();
                        if (limiter.tryAcquire("raj")) ok.incrementAndGet();
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    } finally {
                        done.countDown();
                    }
                });
            }
            start.countDown();
            done.await();
        }
        return ok.get();
    }
}
```
Follow-ups to expect: **evicting idle buckets** (a scheduled sweep, or Caffeine with `expireAfterAccess`); a **global limit** as well (a second bucket checked *after* the per-user one, refunding on failure); and **multiple instances** (move the bucket into Redis with a Lua script so the check and update stay atomic).
"""),

("Testing Concurrency: Harnesses, Real Databases and jcstress", r"""
## Why normal tests miss races
A normal unit test is single-threaded, so a race can't happen. Even with threads, a race needs an unlucky interleaving that may show up once in 10,000 runs. A good concurrency test **maximises collisions** and **asserts an invariant**, not a timing.

## The start-gate harness
```java
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public class SeatRaceHarness {
    interface SeatService { boolean book(String seat, String user); }

    /** Broken: check-then-act across two map calls. */
    static class NaiveSeats implements SeatService {
        private final ConcurrentHashMap<String, String> seats = new ConcurrentHashMap<>();
        public boolean book(String seat, String user) {
            if (seats.containsKey(seat)) return false;
            Thread.yield();                        // widen the race window for the demo
            seats.put(seat, user);
            return true;
        }
    }

    /** Fixed: one atomic operation decides the winner. */
    static class AtomicSeats implements SeatService {
        private final ConcurrentHashMap<String, String> seats = new ConcurrentHashMap<>();
        public boolean book(String seat, String user) { return seats.putIfAbsent(seat, user) == null; }
    }

    static <T> List<T> runConcurrently(int threads, Callable<T> task) throws Exception {
        CountDownLatch ready = new CountDownLatch(threads), start = new CountDownLatch(1);
        try (ExecutorService pool = Executors.newFixedThreadPool(threads)) {
            List<Future<T>> futures = new ArrayList<>();
            for (int i = 0; i < threads; i++) {
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    start.await();                 // all threads released at the same instant
                    return task.call();
                }));
            }
            if (!ready.await(5, TimeUnit.SECONDS)) throw new IllegalStateException("threads not ready");
            start.countDown();
            List<T> results = new ArrayList<>();
            for (Future<T> f : futures) results.add(f.get(10, TimeUnit.SECONDS));  // fail, never hang
            return results;
        }
    }

    static long winners(SeatService svc) throws Exception {
        return runConcurrently(32, () -> svc.book("A7", Thread.currentThread().getName()))
                .stream().filter(b -> b).count();
    }

    public static void main(String[] args) throws Exception {
        int naiveBroken = 0;
        for (int run = 0; run < 200; run++) {
            if (winners(new NaiveSeats()) != 1) naiveBroken++;
            if (winners(new AtomicSeats()) != 1) throw new AssertionError("atomic version double-booked!");
        }
        System.out.println("naive version double-booked in " + naiveBroken + "/200 runs; atomic in 0/200");
    }
}
```
The key ingredients: **more threads than cores**, a **start gate** so they collide, **many repetitions**, **timeouts** so a deadlock fails the test instead of hanging CI, and an **invariant assertion** ("exactly one winner").

## Test against the real database
DB-level guards (unique constraints, `SKIP LOCKED`, gap locks, deadlocks) behave differently on H2. Use **Testcontainers with the same MySQL version**:
```java
@SpringBootTest
@Testcontainers
class SeatBookingConcurrencyIT {
    @Container @ServiceConnection
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");

    @Autowired BookingService booking;

    @RepeatedTest(10)
    void exactlyOneUserGetsTheSeat() throws Exception {
        long showId = fixtures.newShow();
        List<Boolean> results = Harness.runConcurrently(40,
                () -> booking.book(showId, "A7", UUID.randomUUID().toString()).confirmed());
        assertThat(results).filteredOn(ok -> ok).hasSize(1);
        assertThat(bookingRepo.countByShowIdAndSeatNo(showId, "A7")).isEqualTo(1);
    }
}
```
Don't put `@Transactional` on such a test class. Each worker thread needs its own real transaction that actually commits.

## Make the interleaving deterministic
Random collisions find bugs; **forced interleavings** prove fixes. Add a test seam between "check" and "act", for example a spy repository that waits on a latch after the read. Thread 1 reads and pauses, thread 2 runs fully, then thread 1 continues. If the fix is correct, thread 1's write must fail (0 rows updated, a version conflict or a duplicate key). That gives a fast, reliable regression test for the exact race from the incident.

## jcstress: testing the memory model itself
For lock-free code, custom synchronisers or "is this `volatile` enough?" questions, OpenJDK's **jcstress** runs small actor methods concurrently millions of times across JIT modes and CPU interleavings, then reports which outcomes happened:
```java
@JCStressTest
@Outcome(id = "1", expect = Expect.ACCEPTABLE, desc = "one increment won")   // lost update observed
@Outcome(id = "2", expect = Expect.ACCEPTABLE, desc = "both increments")
@State
public class PlainIncrement {
    int x;
    @Actor public void actor1() { x++; }
    @Actor public void actor2() { x++; }
    @Arbiter public void arbiter(I_Result r) { r.r1 = x; }
}
```
You'd rarely write these at work, but knowing the tool exists (and that `x++` produces outcome `1`) is a strong signal. JetBrains' **Lincheck** checks linearizability of concurrent data structures in a similar way.

## A checklist for concurrency tests
- Assert **invariants** (counts, sums, uniqueness), never `Thread.sleep`-based timing.
- Use start gates, threads > cores and repetitions (`@RepeatedTest`).
- Put a **timeout** on every wait.
- Run against the **real** database engine for DB-level guards.
- Add a deterministic interleaving test for any race that reached production.
- Use **Awaitility** (`await().atMost(5, SECONDS).until(...)`) for async outcomes instead of sleeps.
"""),
]

QA = [
("Two workers poll the same jobs table and sometimes both process the same job. How do you fix it?", r"""
**The race:** check-then-act across processes. Both run `SELECT id FROM jobs WHERE status='QUEUED' LIMIT 1`, get job 42, then both `UPDATE ... SET status='RUNNING'` and both "succeed". Invariant broken: a job should run on one worker at a time.

**Fix: make the claim atomic in the database.**
- **Conditional update (CAS):** `UPDATE jobs SET status='RUNNING', owner=?, lease_until=NOW()+INTERVAL 5 MINUTE WHERE id=? AND status='QUEUED'`. **Check the affected rows**: 1 means you own it, 0 means someone else won, so pick another.
- **Batch claim with `SELECT ... FOR UPDATE SKIP LOCKED`** (MySQL 8+) inside a short transaction, then mark the rows RUNNING. Concurrent workers skip locked rows and pick different jobs, with no blocking and no duplicates.

**Then handle failures:**
- **Leases:** a crashed worker's job gets re-queued by a reaper when `lease_until < NOW()`. Long jobs heartbeat to extend the lease.
- Complete with `WHERE id=? AND owner=?`, so a worker whose lease expired can't overwrite the new owner.
- Because a job can run again after a crash, **the job's side effects must be idempotent** (idempotency key per job).
- Cap attempts, then dead-letter.

**Test:** 20 workers against Testcontainers MySQL with 1,000 jobs; assert each job was processed exactly once.
""", I, ["task-claiming", "database", "race-condition"], True),

("Design seat booking so the same seat can never be booked twice, even with many app instances.", r"""
**Invariant:** at most one confirmed booking per (show, seat).

**The guarantee comes from the database:**
- A **unique key** `(show_id, seat_no)` on a `seat_booking` table. Whichever `INSERT` commits first wins; the others get a duplicate-key error, which you map to "seat just taken". It works across any number of pods.
- Or, with a `seats` table holding a status: `UPDATE seats SET status='HELD', held_by=?, hold_until=NOW()+INTERVAL 10 MINUTE WHERE show_id=? AND seat_no=? AND (status='AVAILABLE' OR hold_until < NOW())`, then check that affected rows = 1.

**Holds and payment (the realistic flow):**
1. Hold seats atomically (as above) for 10 minutes.
2. Take payment with an **idempotency key**.
3. Confirm: `UPDATE ... SET status='BOOKED' WHERE ... AND held_by=? AND status='HELD'`. If the hold expired and someone else took the seat, this updates 0 rows, so **refund automatically**.
4. Multiple seats: hold them all in one transaction, in a **consistent order** (sorted seat numbers) to avoid deadlocks, all or nothing.

**Why not `synchronized` or a Redis lock?** `synchronized` is per-JVM. A Redis lock adds a failure mode (lease expiry) and still needs the DB write to be correct. The constraint is simpler and stronger.

**Test:** 50 concurrent users booking A7 against real MySQL; assert exactly one success.
""", I, ["booking", "unique-constraint", "race-condition"], True),

("During a flash sale, stock went negative and you oversold. Why, and how do you fix it?", r"""
**Why:** the code did read-modify-write through JPA: `p = findById(); if (p.stock >= qty) p.setStock(p.stock - qty)`. Under REPEATABLE READ, InnoDB's plain `SELECT` is a **non-locking snapshot read**, so 100 concurrent buyers all read `stock = 1`, all pass the check, and Hibernate writes `stock = 0` (lost updates) or `stock = stock - 1` without a guard (negative stock). Either way, more orders than units.

**Fix, in order of preference:**
1. **Atomic conditional update:** `UPDATE product SET stock = stock - :qty WHERE id = :id AND stock >= :qty`. Affected rows 0 means sold out. One statement, row-locked, no gap. Pair it with a `CHECK (stock >= 0)` constraint (MySQL 8.0.16+) as a backstop.
2. **Optimistic locking** (`@Version`) with retries. It works, but under flash-sale contention most attempts conflict and retry, which wastes work.
3. **Pessimistic** `SELECT ... FOR UPDATE`: correct, but holds the lock longer than the single UPDATE.

**At flash-sale scale (one hot row):**
- Reserve stock first, take payment after, release reservations on timeout.
- **Pre-allocate stock tokens** in Redis (atomic `DECR` or Lua), and let only token holders proceed to the DB.
- **Queue** purchase requests and process them serially per SKU.
- Shard the counter into N sub-rows.

Mention **idempotency keys** too, because retries during the sale shouldn't double-reserve.
""", I, ["inventory", "lost-update", "flash-sale"], True),

("A user double-clicks Pay (or the app retries after a timeout) and gets charged twice. How do you prevent it?", r"""
**Root cause:** `POST /payments` isn't idempotent. Each attempt creates a new charge, and the client can't tell whether a timed-out request succeeded.

**Fix: idempotency keys end to end.**
1. **Client** generates a UUID **per checkout attempt** (not per HTTP request) and sends `Idempotency-Key` on every retry. Disabling the button helps the UX but isn't a guarantee.
2. **Server** stores `(client_id, key)` with a **unique constraint**, plus the request hash, status and stored response:
   - First request: insert `IN_PROGRESS`, process, save the response as `COMPLETED`.
   - Retry after completion: **replay the stored response**, with no new charge.
   - Concurrent duplicate: the unique constraint blocks it, so return 409 "processing".
   - Same key, different body: 422.
3. **Pass the key to the payment provider** (Stripe, Razorpay and others support idempotency keys), so a crash between "charged" and "saved" can't double-charge on retry.
4. **Model the payment as a state machine** with CAS transitions (`WHERE status='CREATED'`), so duplicate webhooks or events can't capture twice.
5. **A reconciliation job** compares provider records with ours and resolves `IN_PROGRESS` leftovers.

Natural guard: one payment intent per order (`UNIQUE(order_id)` on successful payments), so even a bug can't create two successful charges for the same order.
""", I, ["idempotency", "payments", "double-charge"], True),

("Optimistic vs pessimistic locking: when would you use each?", r"""
**Optimistic (`@Version`):** no locks while reading. At write time, `UPDATE ... WHERE id=? AND version=?` detects whether someone changed the row; 0 rows throws `OptimisticLockException`.
- **Use when** contention is low or moderate, conflicts are rare, and especially when the edit **spans user think-time or several HTTP requests** (send the version in the DTO or ETag, check it with `If-Match`).
- **On conflict:** return 409 to the user, or retry automatically in a new transaction with backoff.
- **Cost:** wasted work and retries under high contention.

**Pessimistic (`SELECT ... FOR UPDATE`, `@Lock(PESSIMISTIC_WRITE)`):** lock the row up front; others wait.
- **Use when** contention on a few hot rows is high and a multi-step read-decide-write must be serialised (debiting an account balance, allocating from a small pool).
- **Rules:** short transactions, no remote calls while locked, consistent lock order to avoid deadlocks, bounded wait times.
- **Cost:** blocking, possible deadlocks, reduced concurrency. Never hold DB locks across user requests.

**Often better than both:** a single **conditional UPDATE** (`stock = stock - 1 WHERE stock >= 1`). It does the check and write atomically with the shortest possible lock.

**Senior framing:** pick based on contention, conflict cost and whether the operation spans requests. Then name the failure mode you'll handle (retries vs timeouts and deadlocks).
""", I, ["locking", "jpa", "optimistic", "pessimistic"], True),

("How does @Version work in JPA, and how should you handle a conflict?", r"""
**Mechanics:** add `@Version private long version;` to the entity. Hibernate:
1. Reads the version along with the entity.
2. On flush, issues `UPDATE product SET ..., version = 6 WHERE id = ? AND version = 5`.
3. If the update count is **0**, another transaction changed the row first, so it throws `OptimisticLockException` (Spring: `ObjectOptimisticLockingFailureException`) and the transaction rolls back.
The version also increments on every successful update. Don't set it manually.

**Handling conflicts:**
- **User-facing edits:** include `version` in the response DTO (or as an `ETag`). The client sends it back (`If-Match` or a field), and you compare before applying, returning **409 Conflict** with the latest state so the user can merge or retry. Without this, the check only covers the server-side transaction window, not the user's think time.
- **Automatic operations:** retry the **whole unit of work in a new transaction** (a `TransactionTemplate` loop or `@Retryable` placed *outside* the `@Transactional` boundary), with a small max attempt count and jittered backoff. Retrying inside the same transaction fails because the persistence context is stale and the transaction is marked rollback-only.

**Gotchas:** bulk JPQL `UPDATE`s bypass versioning unless you increment it yourself. Detached entities merged from stale DTOs need the version carried through. Under heavy contention, switch to a conditional update or pessimistic locking.
""", B, ["jpa", "optimistic-locking", "version"], True),

("Why doesn't synchronized fix a race condition in a service running on 4 instances?", r"""
`synchronized` locks a **monitor inside one JVM's memory**. Instances on other pods have their own monitors and never see yours. Two requests for the same seat routed to different pods run the critical section at the same time. Even on one instance it fails if Spring creates more than one bean instance, or if you lock on a per-request object.

**A trap even inside one JVM:**
```java
@Transactional
public synchronized void reserve(long productId) { ... }
```
The `@Transactional` proxy commits **after** the method returns, and the monitor is released **at** return. Thread 2 enters and reads the row **before thread 1 commits**, so it sees the old stock. That's a lost update with no other instances involved.

**What to use instead:** let the **shared source of truth** arbitrate:
- Unique constraints for uniqueness.
- Conditional `UPDATE ... WHERE stock >= ?` or CAS on status for counters and state machines.
- `@Version` or `SELECT ... FOR UPDATE` for entity updates.
- Idempotency keys for retries.
- Partitioning (one Kafka partition per key) for ordered processing.
- A distributed lock (with fencing) only for coordinating non-DB side effects.

Use JVM locks only for **in-memory** state inside one process (caches, rate-limit buckets).
""", B, ["synchronized", "distributed", "transactions"], True),

("Explain check-then-act and read-modify-write races with real examples.", r"""
Both are **compound actions** that look atomic in code but aren't. Another thread or process can step into the gap.

**Check-then-act:** decide based on a check, then act. The check may be stale by the time you act.
- `if (!userRepo.existsByEmail(e)) userRepo.save(new User(e));` → two sign-ups with the same email both pass the check. **Fix:** a unique constraint on email; catch the duplicate.
- `if (!map.containsKey(k)) map.put(k, v);` → use `putIfAbsent` or `computeIfAbsent`.
- Lazy singleton initialisation without synchronisation → two instances.
- "Seat free? Then book" → unique key or conditional update.

**Read-modify-write:** read a value, compute a new one, write it back. Concurrent writers overwrite each other (lost update).
- `count++` on a shared field → `AtomicLong` or `LongAdder`.
- JPA `p.setStock(p.getStock() - 1)` → `UPDATE ... SET stock = stock - 1 WHERE stock >= 1`, or `@Version`.
- Two admins saving a whole form → optimistic locking with version checks.
- Redis `GET` then `SET` of a counter → `INCR` or a Lua script.

**General cure:** make the compound action **one atomic operation** (a single SQL statement, a CAS, an atomic map method), **detect conflicts** (version, constraint) or **exclude others** (a lock), and check the result (affected rows, return value).
""", B, ["race-condition", "fundamentals"], False),

("What is an idempotency key, and how would you implement it in a Spring Boot API?", r"""
**What:** a client-generated unique value (a UUID) sent with a non-idempotent request (`Idempotency-Key` header). Retries of the **same logical operation** reuse it, so the server performs the side effect **once** and returns the same response to every retry.

**Implementation:**
1. **Table** `idempotency_record(client_id, idem_key, request_hash, status, response_code, response_body, created_at)` with **PRIMARY KEY (client_id, idem_key)**.
2. **Filter or aspect** (or explicit service code) on mutating endpoints:
   - `INSERT` a row with status `IN_PROGRESS` (`INSERT IGNORE` or catch the duplicate-key error).
   - Inserted → run the handler, then store the response and mark it `COMPLETED`.
   - Duplicate → load the row. `COMPLETED` with the same hash replays the stored status and body. Different hash → **422**. `IN_PROGRESS` → **409** (or wait briefly and re-check).
3. **Pass the key downstream** (payment provider, other services) so their side effects are deduped too.
4. **Recovery:** a job resolves stale `IN_PROGRESS` rows by checking the downstream state.
5. **TTL cleanup:** delete rows after 24-72 hours.

**Also mention:** per-client key scope, storing only final outcomes, and keeping the record and business write in the **same transaction** when both are local.

```java
@PostMapping("/payments")
ResponseEntity<PaymentResponse> pay(@RequestHeader("Idempotency-Key") @Size(max = 64) String key,
                                    @Valid @RequestBody PaymentRequest req, Principal who) {
    return idempotency.execute(who.getName(), key, req, () -> paymentService.pay(req, key));
}
```
""", I, ["idempotency", "api-design", "spring"], True),

("Two requests with the same idempotency key arrive at exactly the same time. What happens in your design?", r"""
This is the case that separates a real design from a naive "check whether the key exists" lookup.

**Naive version (broken):** both requests `SELECT` the key, both find nothing, both process, and you get a double charge.

**Correct version: the insert is the lock.**
1. Both try `INSERT (client_id, key, hash, 'IN_PROGRESS')`. The **primary key** on `(client_id, key)` lets exactly **one** succeed. The second insert waits on the first's lock, then fails with a duplicate-key error (or succeeds if the first rolls back).
2. The winner processes the request.
3. The loser reads the existing row:
   - Still `IN_PROGRESS` → return **409 Conflict** with `Retry-After`, or poll briefly (say up to 2 s) for completion and then replay.
   - `COMPLETED` → replay the stored response.
   - Different request hash → **422**.

**Subtleties:**
- If the winner's transaction includes the processing and **rolls back**, the key row disappears too, so a retry can start fresh. Good.
- If processing calls an external provider **outside** the transaction, commit the `IN_PROGRESS` row first, so the loser sees it. Handle "winner crashed mid-flight" with a recovery job that checks the provider using the same key.
- Use the same pattern with Redis as a fast pre-check (`SET key NX`), but the DB constraint stays the source of truth.
""", A, ["idempotency", "concurrency", "payments"], False),

("A Kafka consumer processes the same message twice after a rebalance. How do you make it safe?", r"""
**Why it happens:** Kafka gives **at-least-once** delivery when you commit offsets after processing. If a consumer processes a message and then dies, or exceeds `max.poll.interval.ms` and gets kicked out before committing, the partition moves to another consumer, which **re-reads from the last committed offset**. Duplicates are normal; design for them.

**Make processing idempotent:**
1. **Dedupe table (inbox):** `processed_message(message_id PRIMARY KEY)`. In **one DB transaction**: `INSERT IGNORE` the message ID. If 0 rows, it's a duplicate, so skip. Otherwise apply the business change. Both commit or roll back together.
2. **Natural idempotency:** upserts by business key, set-to-value instead of increment, CAS state transitions (`UPDATE orders SET status='PAID' WHERE id=? AND status='PENDING'`). Duplicates become no-ops.
3. **Version or sequence checks:** ignore events older than the stored version (this also handles reordering).

**Message ID:** use a producer-assigned event ID (UUID in a header), not topic-partition-offset, which changes if the event is republished.

**Also fix the trigger:** tune `max.poll.records` and processing time to avoid rebalance storms, and use the cooperative-sticky assignor.

Kafka's transactions and idempotent producer give exactly-once **within Kafka** (read-process-write to topics). They don't cover side effects in your DB or external APIs, so consumer idempotency is still needed.
""", I, ["kafka", "idempotency", "consumers"], True),

("How would you implement a distributed lock with Redis, and what can go wrong?", r"""
**Implementation (single Redis node):**
- **Acquire:** `SET lock:{resource} {randomToken} NX PX 30000`. `NX` means only if absent; `PX` sets a lease, so a crashed holder can't block forever.
- **Release:** a Lua script that deletes the key **only if the value equals my token** (atomic compare-and-delete), so I never release someone else's lock.
- **Library:** Redisson `RLock`, whose watchdog renews the lease while the JVM is alive.

**What can go wrong:**
1. **Lease expiry while still working:** a GC pause or network stall longer than the lease lets another client acquire the lock, so two holders act at once. Re-checking before acting doesn't help: the pause can come right after the check.
2. **Failover:** Redis replication is asynchronous. The primary grants the lock, crashes before replicating, the replica is promoted without the key, and a second client gets the lock.
3. **Redlock** (majority of N nodes) relies on timing assumptions that Kleppmann argued are unsafe for correctness.
4. **Release bugs:** always unlock in `finally`, with the owner check.

**How to stay safe:**
- Use Redis locks for **efficiency** (avoiding duplicate work).
- For **correctness**, add **fencing tokens** checked by the resource, use a consensus store (ZooKeeper/etcd), or better, express the invariant as a **DB constraint or conditional update**.
- Make the protected side effects idempotent anyway.
""", A, ["distributed-lock", "redis", "redisson"], True),

("What are fencing tokens, and why are they needed?", r"""
**Problem:** a lock with a lease (Redis, ZooKeeper session, DB lease row) can expire while its holder is **paused**: GC, a VM freeze, network delay. Another client acquires the lock and writes. Then the paused client wakes up, still believing it holds the lock, and writes **stale** data. The client can't reliably detect this: the pause can hit between any check and the write.

**Fencing token:** the lock service returns a **monotonically increasing number** with each grant (A gets 33, later B gets 34). Every write to the protected resource includes the token, and **the resource rejects tokens lower than the highest it has seen**:
```sql
UPDATE ledger_batch SET status = 'POSTED', fence = :token
WHERE id = :id AND fence < :token;      -- A's late write with 33 after B's 34 -> 0 rows
```
Safety now depends on the **resource's check**, not on timing assumptions.

**Where tokens come from:** ZooKeeper (zxid or znode version), etcd (revision), a DB sequence or version column. Plain Redis lock values are random, not monotonic, which is part of why Redis locks are considered efficiency-only.

**Takeaway for interviews:** "Locks give you mutual exclusion only if nothing pauses. For correctness, the resource must enforce ordering with fencing tokens, or the invariant should live in the database as a constraint or conditional update."
""", A, ["distributed-lock", "fencing", "correctness"], False),

("A @Scheduled job runs on all 3 instances, so users get the daily email 3 times. How do you fix it?", r"""
`@Scheduled` fires in **every** JVM that has the bean. Options, from quickest to most robust:

1. **Cluster lock (ShedLock):** `@SchedulerLock(name = "dailyDigest", lockAtMostFor = "PT30M", lockAtLeastFor = "PT1M")`, backed by a DB table or Redis. Only the instance that acquires the lock runs the job. `lockAtMostFor` covers a node dying mid-run; `lockAtLeastFor` handles small clock differences between nodes.
2. **Make the work itself claimable and idempotent (do this anyway):** generate one row per user per day in a `digest_jobs` table with **`UNIQUE(user_id, digest_date)`**, then let workers claim rows with a conditional `UPDATE ... WHERE status='QUEUED'` or `SKIP LOCKED`. Even if two instances run, each email goes out once. Store `sent_at` so a re-run skips users already sent.
3. **Leader election:** only the leader runs schedulers (Kubernetes Lease, Spring Integration `LockRegistryLeaderInitiator`).
4. **Move scheduling out of the app:** a Kubernetes **CronJob** or a dedicated scheduler service that triggers once (with `concurrencyPolicy: Forbid`). The work still needs to be idempotent, since CronJobs can occasionally run twice.

**Senior point:** the lock reduces duplicates, but leases can expire (a long GC pause or slow job), so **idempotent, claimable work items** are the real guarantee. Also add metrics such as emails sent per day vs active users to catch duplicates.
""", I, ["scheduling", "shedlock", "distributed"], True),

("What does SELECT ... FOR UPDATE actually lock in InnoDB? What are gap locks?", r"""
`SELECT ... FOR UPDATE` is a **locking read**. It reads the **latest committed** row version (not the snapshot) and places **exclusive locks on the index records it scans**, held until the transaction ends.

**What gets locked depends on the index and the isolation level:**
- **Unique index, equality, row exists** (`WHERE id = 42`): only that **record** lock.
- **Range or non-unique index scans** under **REPEATABLE READ** (MySQL's default): **next-key locks**, meaning each scanned record **plus the gap before it**, plus a lock on the gap after the last record. This blocks other transactions from **inserting** into those gaps, which prevents phantoms.
- **Row doesn't exist** (`WHERE id = 999 FOR UPDATE`): a **gap lock**. Two transactions can both hold gap locks on the same gap (gap locks don't conflict with each other), then both try to `INSERT` → **deadlock**. That's the classic "lock if exists, else insert" bug.
- **No usable index:** InnoDB locks **every row it examines**.
- Under **READ COMMITTED**, gap locking is mostly disabled and locks on non-matching rows are released early.

**Practical advice:** lock by primary key or a unique key when possible; make sure predicates are indexed; keep locking transactions short; prefer `INSERT ... ON DUPLICATE KEY UPDATE` over check-then-insert; read `SHOW ENGINE INNODB STATUS` for deadlock details.
""", A, ["innodb", "locking", "mysql"], False),

("Two concurrent transfers, A→B and B→A, deadlock. Why, and how do you fix it?", r"""
**Why:** each transfer locks the source account first, then the destination:
```text
T1 (A→B): lock A ✓ ......... wait for B (held by T2)
T2 (B→A): lock B ✓ ......... wait for A (held by T1)   → circular wait
```
Mutual exclusion, hold-and-wait, no preemption and circular wait are all present, so it's a deadlock. InnoDB detects the cycle and rolls one transaction back with `ERROR 1213 (40001): Deadlock found`. In Java with `ReentrantLock` or `synchronized`, the threads would hang forever.

**Fixes:**
1. **Global lock ordering**, the standard answer: always lock the lower account ID first, regardless of direction.
```java
long first = Math.min(from, to), second = Math.max(from, to);
Account a = repo.findForUpdate(first).orElseThrow();
Account b = repo.findForUpdate(second).orElseThrow();
```
2. **Retry the victim:** deadlocks can still happen (other code paths, gap locks), so catch the deadlock exception (Spring's `CannotAcquireLockException` or `DeadlockLoserDataAccessException`, depending on version) and retry the whole transaction once or twice with jitter. The operation must be idempotent.
3. **Shorten lock duration:** no remote calls inside the transaction.
4. **Avoid multi-row locks entirely:** a ledger design (append debit and credit entries, with balances derived or updated by conditional statements) reduces contention.
5. In Java code: `tryLock(timeout)` instead of blocking forever.
""", I, ["deadlock", "locking", "transactions"], False),

("Is `if (!map.containsKey(k)) map.put(k, v)` safe on a ConcurrentHashMap?", r"""
**No.** Each call is thread-safe on its own, but the **pair isn't atomic**. It's check-then-act: two threads can both see `containsKey == false` and both `put`, so the second overwrites the first (and both think they "won"). `ConcurrentHashMap` guarantees each method call is safe, not sequences of calls.

**Use the atomic compound methods:**
```java
V prev = map.putIfAbsent(k, v);                  // null => we inserted
V val  = map.computeIfAbsent(k, key -> load(key)); // create once per key
map.merge(word, 1, Integer::sum);                // atomic per-key increment
map.compute(k, (key, old) -> old == null ? init() : old.next());
map.remove(k, expectedValue);                    // conditional remove
map.replace(k, expectedOld, newValue);           // CAS-style replace
```

**Caveats with `compute*` and `merge`:**
- The function runs while holding a lock on that hash bin, so keep it **short**: no I/O, no blocking calls, no long computations.
- **Don't modify the same map inside the function** (recursive updates can throw `IllegalStateException` or deadlock).
- `computeIfAbsent` with an expensive loader blocks other writers to that bin. For heavy loading, use a cache library (Caffeine) that handles it.

Same idea elsewhere: `get` then `put` on a counter, or `size() < limit` then `add()`, are also races. Use the atomic operation, or a lock around the compound action.
""", B, ["concurrenthashmap", "java", "atomicity"], False),

("AtomicLong vs LongAdder vs a synchronized counter: which and when?", r"""
**`synchronized` counter:** a mutex around `count++`. Correct and simple, but threads block and context-switch under contention. Fine at low contention, or when the counter must update **together with other state** atomically.

**`AtomicLong`:** lock-free **CAS** (`incrementAndGet` loops until its compare-and-swap succeeds). Fast at low to moderate contention. Supports `compareAndSet`, `getAndUpdate` and `accumulateAndGet`, so it works for **IDs, sequence numbers and limits** where every read must be exact and linearizable. Under heavy contention many threads spin on failed CASes on one cache line, so throughput drops.

**`LongAdder`:** spreads increments across **multiple cells** (per-thread-ish striping) and sums them on read. **Much higher throughput** for write-heavy hot counters (metrics, hit counters). But `sum()` is **not an atomic snapshot** taken during concurrent updates, and there's no CAS. **Don't** use it for "allow if count < limit" decisions or ID generation.

| Need | Pick |
|---|---|
| Statistics or metrics counter with heavy writes | `LongAdder` |
| Unique IDs, sequence, exact compare-and-set | `AtomicLong` |
| Counter plus other fields updated together | `synchronized` / lock, or `AtomicReference` to an immutable object |
| Across instances | Not a JVM counter: DB sequence, Redis `INCR` |

Also mention `AtomicReference.updateAndGet` for immutable state, and that its function must have no side effects, because it may run several times.
""", I, ["atomics", "java", "performance"], False),

("How would you test that your booking code has no race condition?", r"""
**1. Concurrent invariant test (the main one):**
- Fire N threads (more than cores, say 50) through a **start gate** (`CountDownLatch` released at once) so they collide, all booking the same seat.
- Assert the **invariant**: exactly one success, exactly one row in the DB, everyone else got "seat taken". Never assert on timing.
- **Repeat** (`@RepeatedTest(20)`) and put **timeouts** on every wait so a deadlock fails the test instead of hanging CI.

**2. Real database:** run it against **Testcontainers MySQL** (the production version). H2's locking and constraint behaviour differs, so the test can pass on H2 and fail in prod. Don't make the test itself `@Transactional`: each thread needs its own real committed transaction.

**3. Deterministic interleaving test:** inject a test seam (a spy repository that waits on a latch after the "check") to force the exact bad ordering: T1 checks and pauses, T2 books fully, T1 resumes. Assert T1 fails (duplicate key, 0 rows updated or a version conflict). This reliably reproduces the bug from an incident and guards against regressions.

**4. Failure paths:** a retry with the same idempotency key gives one booking; an expired hold can't be confirmed.

**5. For lock-free in-memory code:** jcstress or Lincheck.

Run the suite in CI: a flaky failure there is a real bug signal.
""", I, ["testing", "concurrency", "testcontainers"], True),

("What is jcstress, and when would you use it?", r"""
**jcstress** (Java Concurrency Stress tests) is an OpenJDK harness for testing **Java Memory Model-level** behaviour of small pieces of concurrent code. You write a test class with:
- `@State`: shared state (fields).
- `@Actor` methods: each runs on its own thread, concurrently, **millions of times**, under different JIT modes, CPU affinities and interleavings.
- `@Arbiter` (optional): runs after the actors to observe the final state.
- `@Outcome` annotations: classify each observed result as `ACCEPTABLE`, `FORBIDDEN` or `ACCEPTABLE_INTERESTING`.

Example: two actors doing `x++` on a plain `int` observe outcomes `1` and `2`. Outcome `1` is the lost update. With `AtomicInteger`, only `2` should appear, so you'd mark `1` as `FORBIDDEN`.

**When to use it:**
- Writing **lock-free** structures or custom synchronisers (CAS loops, `VarHandle` code).
- Verifying **publication safety** (is this `volatile` enough? can another thread see a partially constructed object?).
- Checking double-checked locking or flag-based handoffs.

**When not to:** business-level races across processes and databases (bookings, claims). Use multi-threaded integration tests against the real DB for those.

Related: JetBrains **Lincheck** checks linearizability of concurrent data structures against a sequential spec. Knowing these exist, and that a normal unit test can't prove thread safety, is the real signal.
""", A, ["jcstress", "testing", "jmm"], False),

("Events for the same order must be processed in order, but you have many consumers. How do you do it?", r"""
**Kafka approach: partition by key.** Use `orderId` as the record key. All events for an order go to the **same partition**, and a partition is consumed by **one consumer in the group at a time**, in offset order. Different orders spread across partitions for parallelism.

**Ways ordering still breaks, and the fixes:**
- **Producer retries reorder records:** enable the **idempotent producer** (`enable.idempotence=true`, the default in recent clients). It keeps order with retries and up to 5 in-flight requests.
- **Parallel processing inside a consumer** (a thread pool per poll) breaks per-key order. Process sequentially per partition, or use a key-aware parallel consumer that keeps per-key order.
- **Retries:** if processing event 2 fails, moving on to event 3 breaks order. Retry in place with backoff (blocking that partition), or park the **whole key** in a retry topic once one of its events is parked.
- **Adding partitions** changes the key-to-partition mapping, so plan for it.
- **Multiple producers** for the same order (different services) have no global order. Use a version or sequence per aggregate.

**Defensive consumers:** store `last_version` per order and ignore or park events with a lower or unexpected version; apply state transitions with CAS (`WHERE status = 'PAID'` before `SHIPPED`).

With a DB queue: allow one in-flight task per `order_id`.
""", I, ["ordering", "kafka", "partitioning"], False),

("Implement a thread-safe per-user rate limiter. Walk me through your design.", r"""
**Design:** token bucket per user, stored in a `ConcurrentHashMap<String, Bucket>`, with an **immutable** `Bucket(tokens, lastRefillNanos)` replaced atomically through `compute`. No global lock: contention is only per user.

```java
public boolean tryAcquire(String userId) {
    boolean[] allowed = new boolean[1];
    buckets.compute(userId, (id, b) -> {
        long now = clock.getAsLong();                       // injected for tests
        Bucket cur = (b == null) ? new Bucket(capacity, now) : b;
        double tokens = Math.min(capacity, cur.tokens() + (now - cur.lastRefillNanos()) * refillPerNano);
        allowed[0] = tokens >= 1.0;
        return new Bucket(allowed[0] ? tokens - 1 : tokens, now);
    });
    return allowed[0];
}
```

**Why it's correct:** `compute` runs atomically per key, so refill and take are one step: no lost updates for concurrent requests from one user.

**Talking points:**
- **Injectable clock** (`LongSupplier` around `System.nanoTime`) makes tests deterministic: 100 concurrent calls give exactly `capacity` allowed; advance 2 s and get exactly 2 more.
- **Memory:** evict idle buckets (a scheduled sweep or Caffeine `expireAfterAccess`).
- **Global limit:** a second shared bucket; take the user token first, then the global one, and refund the user token if the global take fails.
- **Multiple instances:** move state to Redis with a **Lua script** (atomic refill and take); decide fail-open vs fail-closed if Redis is down.
- **Alternatives:** fixed window (bursty at edges), sliding log (memory-heavy), sliding window counter.
""", I, ["rate-limiter", "machine-coding", "concurrenthashmap"], False),

("With Java 21 virtual threads, what changes for concurrency correctness?", r"""
**Short answer: correctness rules don't change. Resource limits and a few performance details do.**

**Unchanged:**
- Races, visibility and atomicity work exactly the same. `count++` is still a lost update. You still need atomics, concurrent collections, locks or DB-level guards.
- `synchronized`, `ReentrantLock`, `volatile` and `java.util.concurrent` all work.

**What changes:**
1. **Threads are cheap:** create one per task (`newVirtualThreadPerTaskExecutor`) and **don't pool them**. Pools were a concurrency limiter, so you now need **explicit limits**: a `Semaphore` for calls to a partner API, and the Hikari pool for the DB. Otherwise 10,000 virtual threads stampede a dependency.
2. **Pinning:** on JDK 21-23, blocking (I/O, `wait`) inside `synchronized` pins the carrier thread, which hurts throughput and can starve the scheduler. Prefer `ReentrantLock` around blocking sections. JDK 24 (JEP 491) removed most of this pinning. Detect it with the JFR `jdk.VirtualThreadPinned` event.
3. **ThreadLocals:** millions of threads times heavy ThreadLocal caches means memory pressure. Prefer passing context explicitly or `ScopedValue` (preview in 21).
4. **CPU-bound work** gains nothing. Keep it on platform threads or a bounded pool.
5. **Structured concurrency** (preview) makes fan-out with cancellation cleaner.

So virtual threads make blocking code scale, but they're **not** a fix for races.
""", I, ["virtual-threads", "java21", "concurrency"], False),

("How do you implement a state transition (PENDING → PAID) safely so it happens exactly once?", r"""
Use a **compare-and-set in SQL**: make the expected current state part of the `WHERE` clause and check the affected row count.

```sql
UPDATE orders
SET status = 'PAID', paid_at = NOW(), payment_id = :paymentId
WHERE id = :orderId AND status = 'PENDING';
```
```java
@Modifying
@Query("update Order o set o.status = 'PAID', o.paymentId = :pid where o.id = :id and o.status = 'PENDING'")
int markPaid(@Param("id") long id, @Param("pid") String paymentId);

if (orderRepo.markPaid(orderId, paymentId) == 0) {
    Order o = orderRepo.findById(orderId).orElseThrow();
    if (o.getStatus() == PAID && paymentId.equals(o.getPaymentId())) return;   // duplicate event: no-op
    throw new IllegalStateTransitionException(o.getStatus(), PAID);            // e.g. CANCELLED: refund flow
}
```

**Why it works:** the check and the write are one atomic statement under the row lock. Concurrent duplicate webhooks, retries or two admins race on it and **only one updates 1 row**. Everyone else gets 0 and handles it deliberately.

**Extras to mention:**
- Encode allowed transitions centrally (an enum with `canTransitionTo`) and always use CAS updates for them.
- Side effects that must follow the transition (send email, publish `OrderPaid`) go into an **outbox row in the same transaction**, so they happen once, exactly when the transition commits.
- `@Version` gives similar protection for whole-entity updates. CAS on status is more explicit and needs no retry loop.
""", I, ["state-machine", "cas", "sql"], False),

("The app already checks whether an email exists before inserting a user. Why insist on a database unique constraint too?", r"""
Because the application check is **check-then-act** and can't be atomic across requests or instances:

```text
Req 1: existsByEmail("a@x.com") -> false
Req 2: existsByEmail("a@x.com") -> false
Req 1: INSERT user(a@x.com)  ✓
Req 2: INSERT user(a@x.com)  ✓   -> duplicate accounts
```
A double-click, a retry, two pods or a batch import racing a sign-up will eventually hit this window. At scale, "eventually" means daily.

**The unique constraint is the guarantee:**
- It's enforced **atomically** by InnoDB at insert time, across every instance, code path, batch job and manual SQL fix.
- It also protects against **future code** that forgets the check.
- It enables **idempotent upserts** (`INSERT ... ON DUPLICATE KEY UPDATE`) and clean duplicate handling (catch `DataIntegrityViolationException` → 409 "email already registered").

**Keep the app check anyway**, but only for **UX**: a friendly validation message in the common case, without relying on an exception. The constraint covers the race.

**Watch-outs:** normalise before storing (lowercase or trim the email, or use a case-insensitive collation), so "A@x.com" and "a@x.com" collide as intended. With soft deletes, a plain unique index blocks re-registration. Use a design that allows it (a generated column that is NULL for deleted rows, included in the unique index).
""", B, ["unique-constraint", "data-integrity"], False),

("A worker claims a task and then crashes. How do you recover without processing the task twice?", r"""
**1. Claims are leases, not ownership forever.** When claiming, set `owner`, `lease_until = now + 5 min` and `attempts = attempts + 1`. Long-running tasks **heartbeat** (`UPDATE ... SET lease_until = ... WHERE id = ? AND owner = ?`).

**2. A reaper re-queues expired leases:**
```sql
UPDATE tasks SET status = 'QUEUED', owner = NULL
WHERE status = 'RUNNING' AND lease_until < NOW() AND attempts < 5;
UPDATE tasks SET status = 'FAILED' WHERE status = 'RUNNING' AND lease_until < NOW() AND attempts >= 5;
```
Failed tasks go to a dead-letter view with an alert.

**3. Accept that the task may run twice** (crash after doing the work but before marking it DONE, or a paused worker whose lease expired). So:
- **Side effects must be idempotent:** pass a deterministic key (`task-{id}`) to payment, email or other APIs, or record effects in a table with a unique constraint.
- **Ownership-checked completion:** `UPDATE tasks SET status='DONE' WHERE id=? AND owner=? AND status='RUNNING'`. A stale worker gets 0 rows and must not publish results. For stronger protection, use the attempt number as a **fencing token** on downstream writes.
- Split big tasks into **checkpointed steps** so a retry resumes rather than restarts.

**4. Observe:** lease expirations, attempts and DLQ size.

SQS visibility timeouts work the same way.
""", A, ["task-claiming", "leases", "fault-tolerance"], False),

("Is exactly-once message processing possible?", r"""
**Exactly-once *delivery*, in the sense of a message arriving and being handled exactly once despite crashes and network failures, isn't achievable in general.** A consumer can always crash after doing the work but before acknowledging it, so the broker has to redeliver (at-least-once) or risk losing the message (at-most-once).

**What we build instead is exactly-once *effects*:**
```text
at-least-once delivery  +  idempotent / deduplicated processing  =  effectively-once outcome
```
**Techniques:**
- **Dedupe table / inbox:** store processed message IDs in the **same transaction** as the business change.
- **Idempotent operations:** upserts, set-to-value, CAS state transitions, deterministic IDs.
- **Idempotency keys** passed to external APIs (payments, emails) so their side effects dedupe too.
- **Transactional outbox** on the producer side, so "DB commit + publish" can't half-happen.

**Kafka's "exactly-once semantics" (EOS):** the idempotent producer plus transactions give atomic **read-process-write within Kafka** (consume offsets and produced records commit together; consumers use `isolation.level=read_committed`). That's real and useful for stream processing (Kafka Streams), but it **doesn't extend to external side effects**: your MySQL write or HTTP call isn't part of the Kafka transaction.

**Interview line:** "I assume at-least-once and make every consumer and side effect idempotent. Then duplicates are harmless, which is what 'exactly once' means in practice."
""", A, ["exactly-once", "kafka", "idempotency"], False),

("Payment webhooks arrive up to 3 times and sometimes out of order. How do you handle them?", r"""
**Assume duplicates and reordering.** Providers retry until they get a 2xx, and deliveries race.

**1. Verify, persist, acknowledge fast:**
- Verify the **signature** (HMAC) and timestamp to reject forgeries and replays.
- Insert the raw event into `webhook_event(provider_event_id PRIMARY KEY, type, payload, received_at)` and return **200 quickly**. A duplicate ID means it was already stored, so just return 200.
- Process asynchronously (worker or queue), so slow processing doesn't trigger provider retries.

**2. Idempotent processing:** the worker marks events processed in the **same transaction** as the business update. Reprocessing is a no-op.

**3. Handle out-of-order delivery with a state machine and CAS:**
- `payment.succeeded` → `UPDATE payment SET status='CAPTURED' WHERE id=? AND status IN ('CREATED','AUTHORIZED')`.
- A late `payment.authorized` arriving after `succeeded` matches 0 rows, so it's ignored (the state already moved forward).
- `refund.created` before `succeeded` was processed: either park it and retry later, or **fetch the current object from the provider API** (often the most robust approach: treat the webhook as a hint, the API as the truth).
- Use the provider's event timestamps or object versions to ignore stale updates.

**4. Safety nets:** a reconciliation job comparing provider state with ours; alerts on events stuck unprocessed; a dead-letter queue for poison events.
""", I, ["webhooks", "idempotency", "ordering", "payments"], False),
]

SOURCES = [
 ("Martin Kleppmann - How to do distributed locking (fencing tokens)", "https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html"),
 ("Redis Docs - Distributed locks with Redis", "https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/"),
 ("Redisson Wiki - Distributed locks and synchronizers", "https://redisson.org/docs/data-and-services/locks-and-synchronizers/"),
 ("Stripe Engineering - Designing robust and predictable APIs with idempotency", "https://stripe.com/blog/idempotency"),
 ("MySQL 8.4 Reference - InnoDB Locking (record, gap, next-key locks)", "https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html"),
 ("MySQL 8.4 Reference - Locking Reads (FOR UPDATE, NOWAIT, SKIP LOCKED)", "https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html"),
 ("Vlad Mihalcea - Optimistic vs pessimistic locking", "https://vladmihalcea.com/optimistic-vs-pessimistic-locking/"),
 ("Baeldung - Optimistic Locking in JPA", "https://www.baeldung.com/jpa-optimistic-locking"),
 ("Baeldung - Pessimistic Locking in JPA", "https://www.baeldung.com/jpa-pessimistic-locking"),
 ("ShedLock (GitHub)", "https://github.com/lukas-krecan/ShedLock"),
 ("Java SE 21 API - java.util.concurrent package", "https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/package-summary.html"),
 ("OpenJDK jcstress (GitHub)", "https://github.com/openjdk/jcstress"),
 ("Microservices.io - Transactional outbox pattern", "https://microservices.io/patterns/data/transactional-outbox.html"),
 ("Confluent - Exactly-once semantics in Apache Kafka", "https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/"),
 ("Java Concurrency in Practice (Goetz et al.)", "https://jcip.net/"),
]

build("concurrency-practical", "conc", "Practical Concurrency & Idempotency", 14, "🔀",
      "Find, prevent and test real-world races (double booking, double charge, oversell, duplicate job claims) with DB constraints, conditional updates, locking, idempotency keys and Java concurrency tools.",
      NOTES, QA, SOURCES)
