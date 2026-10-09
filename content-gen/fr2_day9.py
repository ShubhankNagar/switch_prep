from fr2_common import M, C, T, save

mcqs = [
M("Idempotency", '''A client calls `POST /payments`, times out, and retries the same request. What is the most robust server-side way to make sure the customer is charged only once?''',
["Rely on the client not to retry", "Have the client send an Idempotency-Key, store it under a unique constraint with the request's result, and return the stored response on a repeat",
 "Change POST to GET", "Put a 5-second sleep before processing"], 1,
'''The key ties every retry to a single logical operation. A unique index (or an atomic insert-if-absent) makes the first request win even when duplicates race each other. Later calls replay the saved response. Stripe and Razorpay both expose idempotency keys for exactly this reason.''', ["Razorpay", "PhonePe", "Paytm"]),

M("REST / HTTP", '''Under the HTTP specification, which set of methods are all **idempotent**?''',
["GET, POST, PUT", "GET, PUT, DELETE", "POST, PATCH, DELETE", "Only GET"], 1,
'''Sending GET, PUT or DELETE N times leaves the server in the same state as sending it once. POST is not idempotent, and PATCH is not guaranteed to be. Note that idempotent is about state: a second DELETE may return 404 and still be idempotent.''', ["Paytm", "PhonePe"]),

M("Spring Transactions", r'''
What happens when `placeOrder()` is called from another bean?
```java
@Service
public class OrderService {
    public void placeOrder() {
        saveOrder();          // self-invocation
    }
    @Transactional
    public void saveOrder() { /* two DB writes */ }
}
```''', ["saveOrder runs in a new transaction", "saveOrder runs without any transaction, because the call skips the Spring proxy",
 "Spring throws an exception at startup", "The transaction covers placeOrder as well"], 1,
'''Spring's @Transactional works through a proxy. An internal `this.saveOrder()` call goes straight to the target object, so the proxy never sees it and no transaction starts. Fixes include moving the method to another bean, injecting a self-proxy, or putting @Transactional on placeOrder.''', ["PhonePe", "Paytm", "Walmart"]),

M("Spring Transactions", '''A method annotated with `@Transactional` (default settings) throws a **checked** exception such as `IOException`. What happens?''',
["The transaction rolls back", "The transaction commits", "Spring wraps it and always rolls back", "The behavior depends on the database"], 1,
'''By default Spring only rolls back on RuntimeException and Error. A checked exception commits whatever was written. Use `@Transactional(rollbackFor = Exception.class)` if checked exceptions should trigger a rollback too.''', ["Razorpay", "PhonePe"]),

M("Spring Transactions", '''`transfer()` is transactional and calls `auditService.log()`, which is annotated `@Transactional(propagation = REQUIRES_NEW)`. Later in `transfer()` an exception rolls the outer transaction back. What happens to the audit row?''',
["It rolls back too", "It stays committed, because REQUIRES_NEW ran in its own independent transaction",
 "Spring throws IllegalTransactionStateException", "It is committed only if the outer transaction commits"], 1,
'''REQUIRES_NEW suspends the outer transaction and opens a separate physical transaction, which commits when log() returns. Rolling back the outer transaction doesn't affect it. That makes it a good fit for audit trails and failure logs.''', ["Paytm", "PhonePe"]),

M("Concurrency Output", r'''
What does this print?
```java
ConcurrentHashMap<String, Integer> m = new ConcurrentHashMap<>();
ExecutorService ex = Executors.newFixedThreadPool(4);
for (int i = 0; i < 1000; i++)
    ex.submit(() -> m.merge("k", 1, Integer::sum));
ex.shutdown();
ex.awaitTermination(1, TimeUnit.MINUTES);
System.out.println(m.get("k"));
```''', ["Always 1000", "Sometimes less than 1000", "ConcurrentModificationException", "null"], 0,
'''`ConcurrentHashMap.merge` runs atomically for each key, so no increments are lost. The same code using `get` followed by `put` would be a race and could undercount. `awaitTermination` makes sure all tasks have finished before the print.''', ["PhonePe", "Razorpay"]),

M("Deadlocks", '''Two threads run `transfer(A, B)` and `transfer(B, A)` at the same time. Each locks the source account first and then the destination account. They deadlock now and then. What is the standard fix?''',
["Make the account fields volatile", "Always acquire the two locks in a global order, such as lower account ID first",
 "Call Thread.sleep between the two locks", "Use a HashMap instead of objects"], 1,
'''With a consistent lock order, a circular wait can't form, and circular wait is one of the four Coffman conditions. Another option is `tryLock` with a timeout and backoff. This exact question is common in fintech interviews.''', ["PhonePe", "Razorpay", "Goldman Sachs"]),

M("Java Output", r'''
What does this print?
```java
System.out.println((0.1 + 0.2 == 0.3) + " "
    + new BigDecimal("2.0").equals(new BigDecimal("2.00")) + " "
    + (new BigDecimal("2.0").compareTo(new BigDecimal("2.00")) == 0));
```''', ["false true true", "false false true", "true false true", "false false false"], 1,
'''0.1 + 0.2 in binary floating point gives 0.30000000000000004. `BigDecimal.equals` compares the scale as well as the value, so 2.0 and 2.00 are not equal. `compareTo` compares only the numeric value. For money, use BigDecimal with compareTo, or a long in paise.''', ["Paytm", "Razorpay", "JP Morgan"]),

M("JPA / Hibernate", '''An entity has an `@Version int version` field. Two transactions read the same row (version 5) and both try to update it. What happens?''',
["Both updates succeed", "The second commit fails with an optimistic locking exception because the row is no longer at version 5",
 "The database deadlocks", "Hibernate merges the two changes automatically"], 1,
'''Hibernate issues `UPDATE ... SET version=6 WHERE id=? AND version=5`. The second writer's UPDATE matches 0 rows, and Spring raises `ObjectOptimisticLockingFailureException`. The usual response is to retry or tell the user. This works well when contention is low.''', ["Razorpay", "PhonePe"]),

M("SQL", '''Inside a transaction, what does `SELECT balance FROM wallet WHERE id = 7 FOR UPDATE;` do?''',
["It only reads the row", "It reads the row and takes an exclusive row lock until the transaction commits or rolls back",
 "It locks the whole table permanently", "It updates the balance"], 1,
'''This is pessimistic locking. Other transactions that try `FOR UPDATE` or an UPDATE on that row will block until this one finishes. That stops the lost-update problem in a read-modify-write on a wallet balance. JPA exposes it as `@Lock(PESSIMISTIC_WRITE)`.''', ["PhonePe", "Paytm"]),

M("DBMS", '''What is the default transaction isolation level of MySQL InnoDB?''',
["Read Uncommitted", "Read Committed", "Repeatable Read", "Serializable"], 2,
'''InnoDB defaults to Repeatable Read. It uses MVCC snapshots for consistent reads and next-key locks for locking reads. PostgreSQL and Oracle default to Read Committed instead, and interviewers often ask about that contrast.''', ["Paytm", "Razorpay"]),

M("Microservices", '''Order, Payment and Inventory are separate services, each with its own database. Which approach keeps the data consistent across them without a global lock?''',
["Two-phase commit across all three databases", "The Saga pattern: a series of local transactions, with compensating actions if a step fails",
 "One shared database", "Retrying forever"], 1,
'''A saga splits the workflow into local transactions. Each step publishes an event or is driven by an orchestrator. If a step fails, earlier steps are undone with compensations such as a refund or releasing stock. 2PC blocks while holding locks and copes badly with partitions.''', ["PhonePe", "Razorpay", "Swiggy"]),

M("Microservices", '''A service has to update its database **and** publish a Kafka event, and the two must never get out of sync. Which pattern handles this?''',
["Two separate calls inside try/catch", "The transactional outbox: write the event to an outbox table in the same DB transaction, and have a relay publish it",
 "Publish to Kafka first, then write to the DB", "Use a cron job that runs every hour"], 1,
'''Writing to two systems separately can fail halfway. With an outbox, the business row and the event row commit atomically in one local transaction. A poller or a CDC tool like Debezium then publishes the event, giving at-least-once delivery. Consumers need to be idempotent.''', ["Razorpay", "PhonePe"]),

M("Multithreading", '''What is the main production risk of `Executors.newFixedThreadPool(10)`?''',
["It creates unlimited threads", "Its work queue is an unbounded LinkedBlockingQueue, so a backlog of tasks can lead to an OutOfMemoryError",
 "It cannot run Callable tasks", "Its threads are daemon threads"], 1,
'''The thread count is capped, but the queue isn't. Under a traffic spike, pending tasks pile up in memory. In production, build a `ThreadPoolExecutor` with a bounded queue and a rejection policy such as CallerRunsPolicy.''', ["PhonePe", "Flipkart"]),

M("Java Output", r'''
What does this print?
```java
CompletableFuture<Integer> f = CompletableFuture.supplyAsync(() -> 10)
    .thenApply(x -> x * 2)
    .thenCompose(x -> CompletableFuture.supplyAsync(() -> x + 1))
    .exceptionally(e -> -1);
System.out.println(f.join());
```''', ["20", "21", "-1", "CompletableFuture[21]"], 1,
'''10 → thenApply gives 20 → thenCompose flattens the inner future to 21. No exception happens, so `exceptionally` is skipped. thenApply maps a value, while thenCompose chains a function that itself returns a future, much like flatMap.''', ["Paytm", "PhonePe"]),

M("Multithreading", '''A class has `static synchronized void a()` and `synchronized void b()`. Thread 1 calls `a()` and Thread 2 calls `obj.b()` at the same time. Can they run concurrently?''',
["No, both use the same lock", "Yes. a() locks the Class object and b() locks the instance, so they use different monitors",
 "Only if obj is null", "It is a compile-time error"], 1,
'''A static synchronized method locks `ClassName.class`, while an instance synchronized method locks `this`. The two locks are unrelated, so the methods can overlap. That's a problem if both touch the same static state.''', ["PhonePe", "Oracle"]),

M("Security / CN", '''How does HTTPS (TLS 1.2/1.3) protect the bulk of the request and response data?''',
["Only with RSA public-key encryption", "An asymmetric key exchange (such as ECDHE) agrees on a session key, then data is encrypted with a fast symmetric cipher such as AES-GCM",
 "With base64 encoding", "With hashing alone"], 1,
'''Asymmetric cryptography is too slow for bulk data, so it's used only to authenticate the server through its certificate and to agree on keys. Ephemeral Diffie-Hellman also provides forward secrecy. The actual payload uses symmetric AEAD ciphers.''', ["Razorpay", "PhonePe"]),

M("Spring Security", '''Which approach is recommended for storing user passwords in a Spring Boot application?''',
["AES-encrypt them with a key in application.properties", "Hash them with an adaptive salted function such as BCrypt (BCryptPasswordEncoder)",
 "MD5 hash", "Store them as plain text over TLS"], 1,
'''BCrypt adds a per-password salt and a tunable work factor, which slows down brute-force attempts. Anything encrypted can be decrypted if the key leaks. Fast hashes like MD5 or SHA-1 can be cracked at scale with GPUs.''', ["Paytm", "Intuit"]),

M("Aptitude", '''₹10,000 is invested at 10% per annum for 2 years. What is the difference between compound interest (compounded annually) and simple interest?''',
["₹0", "₹100", "₹200", "₹210"], 1,
'''SI = 10,000 × 0.10 × 2 = ₹2,000. CI = 10,000 × (1.1² − 1) = ₹2,100. The difference is ₹100. Shortcut for 2 years: P·(r/100)² = 10,000 × 0.01 = 100.''', ["Paytm", "PhonePe"]),

M("Aptitude", '''A can finish a job in 12 days and B can finish it in 18 days. How long do they take working together?''',
["7 days", "7.2 days", "15 days", "6 days"], 1,
'''Their combined rate is 1/12 + 1/18 = 3/36 + 2/36 = 5/36 of the job per day. So the time is 36/5 = 7.2 days.''', ["PhonePe", "Paytm"]),
]

coding = [
C("Print Odd and Even Numbers Using Two Threads", "Medium", ["PhonePe", "Paytm", "Goldman Sachs"], r'''
Write a program with **two threads**. One prints odd numbers and the other prints even numbers, and together they print `1..N` in order, strictly alternating.

**Example**
```
Input:  N = 6
Output: T-odd: 1, T-even: 2, T-odd: 3, T-even: 4, T-odd: 5, T-even: 6
```
**Constraints:** 1 ≤ N ≤ 10^5. Busy-waiting (spinning) is not allowed. Use proper synchronization.''',
["Share a counter and a lock between both threads. Each thread waits until it's its turn based on parity.",
 "Use wait()/notify() inside synchronized blocks, and always check the condition in a while loop to handle spurious wakeups."],
r'''
class OddEvenPrinter {
    private final int n;
    private int current = 1;
    private final Object lock = new Object();

    OddEvenPrinter(int n) { this.n = n; }

    private void print(int parity) {          // parity 1 = odd, 0 = even
        synchronized (lock) {
            while (current <= n) {
                while (current <= n && current % 2 != parity) {
                    try {
                        lock.wait();
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    }
                }
                if (current > n) break;
                System.out.println(Thread.currentThread().getName() + ": " + current);
                current++;
                lock.notifyAll();
            }
            lock.notifyAll();                  // release the other thread at the end
        }
    }

    public static void main(String[] args) throws InterruptedException {
        OddEvenPrinter p = new OddEvenPrinter(10);
        Thread odd = new Thread(() -> p.print(1), "T-odd");
        Thread even = new Thread(() -> p.print(0), "T-even");
        odd.start();
        even.start();
        odd.join();
        even.join();
    }
}''',
'''Both threads share one monitor (`lock`) and one counter. A thread prints only when `current % 2` matches its parity. Otherwise it calls `wait()`, which gives up the monitor so the other thread can go. After printing, it increments the counter and calls `notifyAll()`. The inner `while` guards against spurious wakeups and against waking up when it isn't this thread's turn. The extra `current <= n` check plus the final `notifyAll()` stop one thread from waiting forever once the last number is printed. Interviewers may ask for a version using `Semaphore` (two semaphores passing a permit back and forth) or `ReentrantLock` with two `Condition`s. You should be able to explain why `notify()` vs `notifyAll()` matters once there are more than two threads.''',
"O(N)", "O(1)", None),

C("Design a Bounded Blocking Queue", "Medium", ["PhonePe", "Uber", "Microsoft"], r'''
Implement a thread-safe bounded queue with:
- `BoundedBlockingQueue(int capacity)`
- `void enqueue(int element)`: blocks while the queue is full
- `int dequeue()`: blocks while the queue is empty
- `int size()`

Several producer and consumer threads will call these methods concurrently. You may not use `java.util.concurrent.BlockingQueue`.

**Example**
```
capacity = 2
enqueue(1); enqueue(2);   // queue full
enqueue(3);               // blocks until a consumer dequeues
dequeue() -> 1            // unblocks the producer; queue is now [2,3]
```
**Constraints:** 1 ≤ capacity ≤ 30, up to 8 threads, up to 40 calls in total.''',
["Use one ReentrantLock with two Conditions: notFull and notEmpty.",
 "Wait in a while loop. After enqueueing, signal notEmpty. After dequeueing, signal notFull."],
r'''
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

class BoundedBlockingQueue {
    private final int capacity;
    private final Deque<Integer> items = new ArrayDeque<>();
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notFull = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();

    public BoundedBlockingQueue(int capacity) {
        this.capacity = capacity;
    }

    public void enqueue(int element) throws InterruptedException {
        lock.lock();
        try {
            while (items.size() == capacity) notFull.await();
            items.addLast(element);
            notEmpty.signal();
        } finally {
            lock.unlock();
        }
    }

    public int dequeue() throws InterruptedException {
        lock.lock();
        try {
            while (items.isEmpty()) notEmpty.await();
            int value = items.removeFirst();
            notFull.signal();
            return value;
        } finally {
            lock.unlock();
        }
    }

    public int size() {
        lock.lock();
        try {
            return items.size();
        } finally {
            lock.unlock();
        }
    }
}''',
'''This is the classic producer-consumer monitor. Two separate `Condition`s mean producers only wake consumers and consumers only wake producers. That avoids the wasted wakeups you get with one `notifyAll()`. `await()` releases the lock atomically while it waits and takes it back before returning. That's why the size check must sit in a `while` loop: by the time a thread wakes up, another one may already have filled or emptied the queue. The `unlock()` goes in `finally` so an exception can't leave the lock held. Common follow-ups: how `ArrayBlockingQueue` does the same thing internally, and how to add a `offer(e, timeout)` using `awaitNanos`.''',
"O(1) per operation", "O(capacity)", "https://leetcode.com/problems/design-bounded-blocking-queue/"),

C("Thread-Safe Token Bucket Rate Limiter", "Medium", ["Razorpay", "PhonePe", "Uber"], r'''
Build a per-client rate limiter for a payments API:
- `RateLimiter(int capacity, double refillPerSecond, LongSupplier clockNanos)`
- `boolean tryAcquire(String clientId)` returns true and uses one token if the client has a token available, and false otherwise.

Each client starts with a full bucket of `capacity` tokens. Tokens refill continuously at `refillPerSecond` and never go above `capacity`. The limiter is called from many request threads. The clock is injected so the class can be tested.

**Example** (capacity = 2, refill = 1 token/sec)
```
t=0.0s  tryAcquire("m1") -> true
t=0.0s  tryAcquire("m1") -> true
t=0.0s  tryAcquire("m1") -> false   // bucket empty
t=1.0s  tryAcquire("m1") -> true    // 1 token refilled
t=1.0s  tryAcquire("m2") -> true    // separate bucket
```
**Constraints:** up to 10^5 clients and thousands of calls per second.''',
["Store a bucket per client in a ConcurrentHashMap and create it lazily with computeIfAbsent.",
 "Refill lazily on each call based on time elapsed since the last refill. Synchronize on the individual bucket, not the whole limiter."],
r'''
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.LongSupplier;

class RateLimiter {
    private final int capacity;
    private final double refillPerNano;
    private final LongSupplier clock;
    private final ConcurrentHashMap<String, Bucket> buckets = new ConcurrentHashMap<>();

    RateLimiter(int capacity, double refillPerSecond, LongSupplier clockNanos) {
        this.capacity = capacity;
        this.refillPerNano = refillPerSecond / 1_000_000_000.0;
        this.clock = clockNanos;
    }

    public boolean tryAcquire(String clientId) {
        Bucket b = buckets.computeIfAbsent(clientId, id -> new Bucket(capacity, clock.getAsLong()));
        return b.tryConsume();
    }

    private final class Bucket {
        private double tokens;
        private long lastRefill;

        Bucket(double tokens, long now) {
            this.tokens = tokens;
            this.lastRefill = now;
        }

        synchronized boolean tryConsume() {
            long now = clock.getAsLong();
            tokens = Math.min(capacity, tokens + (now - lastRefill) * refillPerNano);
            lastRefill = now;
            if (tokens >= 1.0) {
                tokens -= 1.0;
                return true;
            }
            return false;
        }
    }

    public static void main(String[] args) {
        long[] now = {0};
        RateLimiter rl = new RateLimiter(2, 1.0, () -> now[0]);
        System.out.println(rl.tryAcquire("m1") + " " + rl.tryAcquire("m1") + " " + rl.tryAcquire("m1"));
        now[0] = 1_000_000_000L;
        System.out.println(rl.tryAcquire("m1") + " " + rl.tryAcquire("m2"));   // true true
    }
}''',
'''The token bucket allows short bursts up to `capacity` while holding the average rate to `refillPerSecond`. That's why payment gateways like it. Rather than running a background thread to add tokens, each call adds `elapsed × rate` tokens lazily, capped at capacity. `computeIfAbsent` on a ConcurrentHashMap creates each client's bucket exactly once, even when requests race. Locking happens **per bucket**, so different merchants never contend with each other. Injecting the clock makes the class deterministic in unit tests. Interviewers usually follow up with: how to share this across multiple servers (Redis plus a Lua script for an atomic check-and-decrement), how it compares with sliding-window counters, and how to evict idle buckets (Caffeine with expireAfterAccess).''',
"O(1) per call", "O(number of clients)", None),

C("Minimize Cash Flow Among Friends (Settle Debts)", "Medium", ["Razorpay", "PhonePe", "Paytm", "Amazon"], r'''
`n` people (0..n-1) share expenses. You get a list of transactions `[from, to, amount]`, meaning `from` paid `amount` on behalf of `to`, so `to` owes `from`. Return a list of settlements `[debtor, creditor, amount]` that clears every balance using **at most n − 1 transfers**. Work out each person's net balance and greedily match the largest debtor with the largest creditor.

**Example**
```
Input:  n = 3, txns = [[0,1,1000],[1,2,500],[0,2,200]]
Net:    p0 = +1200, p1 = -500, p2 = -700
Output: [[2,0,700],[1,0,500]]
```
**Constraints:** 1 ≤ n ≤ 10^4, 0 ≤ txns.length ≤ 10^5, 1 ≤ amount ≤ 10^6. Amounts are integers (paise).''',
["Only net balances matter. Sum what each person paid minus what they owe.",
 "Keep two max-heaps, one for creditors and one for debtors. Settle min(credit, debt) and push the leftover back."],
r'''
import java.util.*;

class SettleDebts {
    public List<long[]> settle(int n, int[][] txns) {
        long[] net = new long[n];
        for (int[] t : txns) {
            net[t[0]] += t[2];      // paid for someone -> is owed money
            net[t[1]] -= t[2];      // was paid for -> owes money
        }
        // max-heaps on absolute amount: {person, amount}
        PriorityQueue<long[]> creditors = new PriorityQueue<>((a, b) -> Long.compare(b[1], a[1]));
        PriorityQueue<long[]> debtors = new PriorityQueue<>((a, b) -> Long.compare(b[1], a[1]));
        for (int i = 0; i < n; i++) {
            if (net[i] > 0) creditors.add(new long[]{i, net[i]});
            else if (net[i] < 0) debtors.add(new long[]{i, -net[i]});
        }
        List<long[]> result = new ArrayList<>();
        while (!creditors.isEmpty() && !debtors.isEmpty()) {
            long[] c = creditors.poll();
            long[] d = debtors.poll();
            long amt = Math.min(c[1], d[1]);
            result.add(new long[]{d[0], c[0], amt});
            if (c[1] > amt) creditors.add(new long[]{c[0], c[1] - amt});
            if (d[1] > amt) debtors.add(new long[]{d[0], d[1] - amt});
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] txns = {{0, 1, 1000}, {1, 2, 500}, {0, 2, 200}};
        for (long[] s : new SettleDebts().settle(3, txns))
            System.out.println(Arrays.toString(s));   // [2, 0, 700] then [1, 0, 500]
    }
}''',
'''First reduce everything to net balances. The individual transactions don't matter, only who is owed and who owes. Every settlement pairs the largest remaining creditor with the largest debtor and clears at least one of them, so there are never more than n − 1 transfers. Using long values for paise avoids floating-point rounding. Mention this in a fintech interview. Be ready for the follow-up: finding the true minimum number of transfers is NP-hard (LC 465, "Optimal Account Balancing"), which you solve with backtracking or bitmask DP over the non-zero balances when n is small. This settlement logic is also the core of the Splitwise machine-coding problem that Indian fintechs often report asking.''',
"O(T + n log n)", "O(n)", None),
]

theory = [
T("What is idempotency, and how would you implement an idempotent payment API?", '''An operation is **idempotent** if running it many times has the same effect as running it once. Networks fail and clients retry, so payment APIs have to be idempotent or customers get double-charged.

Implementation:
1. The client generates an `Idempotency-Key` (a UUID) for each logical payment and sends it on every retry.
2. The server inserts `(key, merchant_id, request_hash, status=IN_PROGRESS)` into a table with a **unique constraint**. If the insert fails because the key already exists, return the stored response, or 409 if it's still in progress.
3. Process the payment, then store the final response against the key in the same transaction as the business write.
4. If the same key arrives with a different request hash, reject it.
5. Expire keys after a TTL, for example 24 hours. Redis `SET NX` works as a fast front-line check.

Downstream Kafka consumers should also deduplicate by event ID.''', ["Razorpay", "PhonePe", "Paytm"]),

T("Explain Spring @Transactional propagation and isolation, and common pitfalls.", '''**Propagation** controls how a method joins an existing transaction:
- REQUIRED (default): join the current transaction, or start one if none exists.
- REQUIRES_NEW: suspend the current transaction and start an independent one, useful for audit logs.
- NESTED: use a savepoint inside the current transaction.
- Others: SUPPORTS, MANDATORY, NEVER, NOT_SUPPORTED.

**Isolation** (READ_COMMITTED, REPEATABLE_READ, and so on) maps to the database isolation level. DEFAULT uses whatever the database is configured with.

**Pitfalls:**
1. Self-invocation skips the proxy, so no transaction starts.
2. @Transactional on private or final methods is ignored by proxy-based AOP.
3. Checked exceptions don't trigger rollback unless you set `rollbackFor`.
4. Catching an exception inside the method hides it from Spring, so it commits.
5. Long transactions that make remote HTTP calls hold DB connections and locks for too long.
6. `readOnly = true` is a hint for optimization, not a security control.''', ["Paytm", "PhonePe", "Walmart"]),

T("Optimistic vs pessimistic locking: which would you use for a wallet balance update?", '''**Pessimistic locking** (`SELECT ... FOR UPDATE`, or JPA `PESSIMISTIC_WRITE`) locks the row up front. Other writers wait. It's safe and simple, but under heavy contention it adds waiting and a risk of deadlock.

**Optimistic locking** (a `@Version` column) takes no lock. The UPDATE includes `WHERE version = ?`. If 0 rows match, someone else changed the row, so you retry or fail. Throughput is high when conflicts are rare.

For a **wallet**: a single user's wallet rarely sees concurrent debits, so optimistic locking with a few retries works well. For a hot row, such as a merchant settlement account credited thousands of times per second, pessimistic locking or a **conditional atomic update** (`UPDATE wallet SET bal = bal - ? WHERE id = ? AND bal >= ?`) avoids retry storms. Very hot accounts can also be split into sub-ledgers.''', ["PhonePe", "Paytm", "Razorpay"]),

T("Saga vs Two-Phase Commit for distributed transactions?", '''**2PC:** a coordinator asks every participant to *prepare* (lock resources and vote), then tells them all to *commit*. It's atomic, but it's **blocking**: if the coordinator dies after prepare, participants hold locks indefinitely. It also needs XA support and couples services tightly. It's rarely used in microservices.

**Saga:** a chain of **local** transactions. Each step commits on its own. If a later step fails, **compensating transactions** undo the earlier ones, for example refunding a payment or releasing reserved stock. It can be coordinated two ways:
- *Choreography*: services react to each other's events. This is loosely coupled but harder to trace.
- *Orchestration*: a central orchestrator, such as a state machine or Temporal, drives the steps.

Sagas give **eventual consistency** without isolation. Intermediate states are visible, so you need semantic locks (for example status = PENDING), idempotent steps and retries. Payment and order flows almost always use orchestrated sagas.''', ["Razorpay", "PhonePe", "Swiggy"]),

T("How does ConcurrentHashMap achieve thread safety in Java 8+?", '''Java 7 used **segments**, which were 16 lock stripes by default. Java 8 replaced them with finer-grained locking:
- **Reads** use no locks. Table entries are read with volatile semantics, so `get` is lock-free.
- An **insert into an empty bucket** uses a **CAS** with no lock.
- An **insert into a non-empty bucket** synchronizes only on that bucket's **first node**, so writers to different buckets don't block each other.
- Large buckets become red-black trees, as in HashMap.
- **Resizing** is shared: threads that touch the map during a resize help move bins, and `ForwardingNode`s mark bins that have already moved.
- `size()` uses a striped counter (CounterCells, similar to LongAdder) to avoid contention.

It doesn't allow null keys or values, because `null` would make it impossible to tell "absent" from "mapped to null" in concurrent code. Use atomic methods (`merge`, `compute`, `putIfAbsent`) rather than a get-then-put sequence.''', ["Paytm", "PhonePe", "Walmart"]),

T("How would you rate-limit a public payments API across many servers?", '''Choose an algorithm:
- **Token bucket** allows controlled bursts and is the usual choice.
- **Sliding-window log or counter** is more precise.
- **Fixed window** is simple, but it allows bursts at window boundaries.

**Where to enforce it:** at the API gateway (Kong, Envoy, Spring Cloud Gateway), with keys per merchant, API key or IP.

**Distributed state:** keep counters in **Redis**. Use a Lua script that refills and decrements atomically, so all instances share the same view. Set a TTL on keys so idle clients don't take up memory.

**Response:** return HTTP **429** with `Retry-After` and `X-RateLimit-Remaining` headers.

**Resilience:** if Redis is down, decide whether to *fail open* (allow traffic) or *fail closed*. Add a local in-memory limiter as a fallback. Use different tiers for different plans, and stricter limits on sensitive endpoints such as OTP or login. Monitor rejection rates.''', ["Razorpay", "PhonePe", "Uber"]),
]

save(9, "PhonePe, Razorpay & Paytm (Fintech)",
     "Fintech-style rounds covering concurrency-aware coding, transactions and idempotency, and the Spring Boot details that keep money correct.",
     mcqs, coding, theory)
