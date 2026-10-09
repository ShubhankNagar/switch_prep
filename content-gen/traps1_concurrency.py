"""Concurrency traps (race demos verified on Java 21; numbers quoted are from real runs)."""
from traps1_common import T

A = "concurrency"

TRAPS = [
T("trap-concurrency-volatile-not-atomic", A, "volatile is not atomic (count++)", "Intermediate", "Very common",
r"""
Two threads run this loop, and `main` joins both before printing. What is printed?

```java
class Stats {
    static volatile int count = 0;
}

// each of the two threads runs:
for (int i = 0; i < 100_000; i++) Stats.count++;

// after t1.join(); t2.join();
System.out.println(Stats.count);
```
""",
["Always 200000, because volatile makes every update visible",
 "Usually less than 200000 and different on each run (occasionally exactly 200000)",
 "Always 100000", "Throws IllegalMonitorStateException"], 1,
"Always 200000, because volatile makes the variable thread-safe.",
r"""
`volatile` handles visibility and ordering, and candidates stretch that into 'thread-safe'. But `count++` is three
steps: read, add one, write. volatile does nothing to make those three steps indivisible. Two threads can read the same
value and both write back value + 1, so one increment is lost.
""",
r"""
`volatile` guarantees that every read sees the latest write and that accesses aren't reordered around it (a
happens-before edge). It does **not** give mutual exclusion. `count++` is a read, an add and a write, and if two threads
interleave as read, read, write, write, one increment is lost. On Java 21 this printed values such as 159013 and
152672, and occasionally exactly 200000. That last case is why these bugs survive testing.

Use volatile for a flag (`volatile boolean running`), a value with a single writer, or safe publication of an
immutable object. For read-modify-write use `AtomicInteger` (a CAS loop), `LongAdder` for heavily contended counters,
or a lock. The database version of this bug is the same: read a value into Java, add to it, and write it back.
""",
r"""
```java
static final AtomicInteger count = new AtomicInteger();
count.incrementAndGet();

static final LongAdder hits = new LongAdder();   // scales better under heavy contention
hits.increment();
long total = hits.sum();
```
""",
"Separate the three guarantees (atomicity, visibility, ordering) and say that volatile gives only the last two.",
["Goldman Sachs"]),

T("trap-concurrency-synchronized-wrong-lock", A, "synchronized on the wrong monitor", "Intermediate", "Common",
r"""
What does this print after both threads finish?

```java
class Counter {
    private static int count = 0;
    public synchronized void increment() { count++; }
    static int get() { return count; }
}

// Thread 1: Counter c1 = new Counter(); 100_000 times c1.increment();
// Thread 2: Counter c2 = new Counter(); 100_000 times c2.increment();
System.out.println(Counter.get());
```
""",
["Always 200000, because the method is synchronized", "Can be less than 200000", "Deadlock", "Always 100000"], 1,
"Always 200000, because increment() is synchronized.",
r"""
Candidates see the `synchronized` keyword and stop there, without asking **which** monitor is locked. A synchronized
instance method locks `this`. Two different Counter instances therefore hold two different locks and never block each
other, while the data being protected is a static field that both of them share.
""",
r"""
A synchronized instance method is shorthand for `synchronized (this)`. `c1` and `c2` are different objects, so the two
threads take different monitors and run `count++` on the shared static field at the same time, and increments are
lost (real runs printed 131486 and 184604). Everyone who touches the data must lock the **same** object, and the lock's
scope must match the data's scope. For static data that means `static synchronized` (which locks `Counter.class`) or a
`static final` lock object.

The same family of bugs: `synchronized (new Object())` (a fresh lock on every call, so no exclusion at all); locking a
field that gets reassigned (`Integer lock; lock++` creates a new object); locking a String literal or boxed Integer
that unrelated code may share; and guarding writes while reading without the lock.
""",
r"""
```java
class Counter {
    private static final Object LOCK = new Object();
    private static int count = 0;
    public void increment() { synchronized (LOCK) { count++; } }
}

// or simply
private static final AtomicInteger count = new AtomicInteger();
```
""",
"Ask out loud: 'Which object is the monitor, and does every access to this data use that same monitor?'"),

T("trap-concurrency-double-checked-locking", A, "Double-checked locking without volatile", "Advanced", "Common",
r"""
Is this lazy singleton thread-safe? If not, what exactly can go wrong?

```java
public class ConfigHolder {
    private static Config instance;

    public static Config get() {
        if (instance == null) {
            synchronized (ConfigHolder.class) {
                if (instance == null) {
                    instance = new Config(loadFromDisk());
                }
            }
        }
        return instance;
    }
}
```
""",
None, None,
"Yes. The second null check inside synchronized prevents two instances, so it's safe.",
r"""
Candidates only think about the 'two instances' race, and the inner check does prevent that. They miss the visibility
problem. The outer `if` reads `instance` without any lock, so there is no happens-before relationship with the thread
that wrote it. That reader can see the reference before it sees the writes made inside the constructor.
""",
r"""
`instance = new Config(...)` is roughly: allocate memory, run the constructor (write the fields), publish the
reference. The JIT and the CPU may reorder these steps. Even without reordering, a thread that never enters
`synchronized` has no guarantee of seeing the constructor's writes. So thread B can pass the outer `if`, get a non-null
`instance`, and read default values (null or 0) from its fields: a **partially constructed object**.

The fix is to declare the field `volatile`. A volatile write happens-before every later volatile read of it, so the
constructor's writes become visible. Alternatives are the initialization-on-demand holder idiom (the JVM makes class
initialization lazy and thread-safe) and an `enum` singleton. If every field of `Config` is `final`, the Java Memory
Model guarantees other threads see them initialized, but relying on that is subtle. In Spring code, just make it a
singleton bean.
""",
r"""
```java
private static volatile Config instance;   // the one-word fix

// often cleaner: holder idiom, lazy and lock-free
public class ConfigHolder {
    private static class Holder {
        static final Config INSTANCE = new Config(loadFromDisk());
    }
    public static Config get() { return Holder.INSTANCE; }
}
```
""",
"Use the terms 'safe publication' and 'happens-before', and offer the holder idiom as the cleaner option.",
["Goldman Sachs"]),

T("trap-concurrency-chm-check-then-act", A, "ConcurrentHashMap check-then-act race", "Intermediate", "Very common",
r"""
Four threads each run the following line 50,000 times. What is printed at the end?

```java
ConcurrentHashMap<String, Integer> hits = new ConcurrentHashMap<>();

// each thread, 50_000 times:
hits.put("home", hits.getOrDefault("home", 0) + 1);

// after all threads finish:
System.out.println(hits.get("home"));
```
""",
["Always 200000, because ConcurrentHashMap is thread-safe", "Often less than 200000",
 "Throws ConcurrentModificationException", "Deadlock"], 1,
"Always 200000, because ConcurrentHashMap is thread-safe.",
r"""
'Thread-safe collection' gets heard as 'my code that uses it is thread-safe'. ConcurrentHashMap makes each single call
atomic, but a `get` followed by a `put` is two calls. Another thread can update the value between them, and one update
overwrites the other. That is a check-then-act (read-modify-write) race in your code, not in the map.
""",
r"""
Every individual method of ConcurrentHashMap is atomic, but compound actions built from several calls are not. Two
threads both read 41, both put 42, and one hit is gone. Real runs printed values such as 97642 and 82200 instead of
200000. The same race appears in `if (!map.containsKey(k)) map.put(k, create())`, which can create two values and
leave one caller holding an object that isn't in the map.

Use the atomic compound methods: `merge`, `compute`, `computeIfAbsent`, `putIfAbsent` and `replace(k, old, new)`. Keep
the functions you pass to `compute`/`computeIfAbsent` short. They run while part of the map is locked, so slow I/O
blocks other writers, and modifying the same map inside them can throw `IllegalStateException: Recursive update`.
ConcurrentHashMap also rejects null keys and values.
""",
r"""
```java
hits.merge("home", 1, Integer::sum);                                   // atomic increment

ConcurrentHashMap<String, LongAdder> counters = new ConcurrentHashMap<>();
counters.computeIfAbsent("home", k -> new LongAdder()).increment();    // best for hot counters

Lock lock = locks.computeIfAbsent(orderId, k -> new ReentrantLock());  // create-once, cheap factory
```
""",
"Say 'each call is atomic, sequences of calls are not', and reach for merge/computeIfAbsent before being prompted."),

T("trap-concurrency-hashmap-shared", A, "Plain HashMap shared between threads", "Intermediate", "Very common",
r"""
A singleton Spring service keeps a cache in a plain `HashMap`. Request threads `put` different ids and `get` them
back. No two threads ever write the same key. A teammate says: "Distinct keys, so there's no race." Is that true?
What can actually happen?

```java
@Service
public class PriceCache {
    private final Map<Long, BigDecimal> cache = new HashMap<>();
    public void put(Long id, BigDecimal price) { cache.put(id, price); }
    public BigDecimal get(Long id) { return cache.get(id); }
}
```
""",
None, None,
"With distinct keys the worst case is a slightly stale read; a HashMap can't actually break.",
r"""
People picture a HashMap as independent slots, one per key. Internally, all keys share one table array, a size
counter, and bucket lists or trees, and any put can trigger a resize that rebuilds the whole table. Unsynchronized
writers to *any* keys race on that shared structure, not just writers to the same key.
""",
r"""
HashMap's internal state (the `table` array, the bucket chains, `size`, `modCount`) is shared by all keys. Concurrent
puts can overwrite each other's bucket links, or both resize at once, and entries vanish. In a test, 4 threads
inserting 100,000 distinct keys ended with sizes like 63,912 and 78,173. Readers can also get `null` for a key that is
present, because without synchronization there's no visibility guarantee, and a resize may be half done.

In Java 7, a concurrent resize could create a cycle in a bucket's linked list, leaving `get()` spinning at 100% CPU
forever, a classic production incident. Java 8 changed resizing, but concurrent use is still undefined behaviour:
lost data, a wrong `size()`, even exceptions in tree bins. Use `ConcurrentHashMap`, or a cache library such as Caffeine
when you need size limits and expiry. `Collections.synchronizedMap` works, but it has one global lock, and you must
lock it yourself while iterating.
""",
r"""
```java
private final Map<Long, BigDecimal> cache = new ConcurrentHashMap<>();

// with eviction and expiry (Caffeine)
private final Cache<Long, BigDecimal> prices = Caffeine.newBuilder()
        .maximumSize(10_000)
        .expireAfterWrite(Duration.ofMinutes(5))
        .build();
```
""",
"Mention the Java 7 infinite-loop incident, then add that an unbounded map used as a cache is a memory leak anyway: size limits matter as much as thread safety."),

T("trap-concurrency-threadlocal-pool-leak", A, "ThreadLocal leaking across pooled requests", "Intermediate", "Common",
r"""
Tomcat runs requests on a pool of 200 threads. A request arrives **without** the `X-Tenant` header. What can
`TenantFilter.TENANT.get()` return while it is being processed?

```java
public class TenantFilter implements Filter {
    static final ThreadLocal<String> TENANT = new ThreadLocal<>();

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {
        String tenant = ((HttpServletRequest) req).getHeader("X-Tenant");
        if (tenant != null) TENANT.set(tenant);
        chain.doFilter(req, res);
    }
}
```
""",
["Always null, because ThreadLocal values are cleared when the request ends",
 "The tenant of an earlier request that ran on the same pooled thread",
 "Always null, because ThreadLocal keys are weak references and get garbage-collected",
 "It throws IllegalStateException"], 1,
"null: the value belonged to the previous request, and a ThreadLocal is cleaned up after each request.",
r"""
Developers treat a request and a thread as the same thing. With a thread pool, the thread outlives the request and gets
reused, and nothing in Java or Tomcat clears your ThreadLocal for you. Many also half-remember that ThreadLocalMap uses
weak references, and assume that means automatic cleanup.
""",
r"""
A ThreadLocal value lives in the `ThreadLocalMap` of the thread itself. Pooled threads are not destroyed between
requests, so the value set by request 1 is still there when request 2 runs on the same thread. Here, a request without
the header reads another tenant's id: a **data leak across customers**. (In a test, a one-thread pool handed 'alice'
to the next task.)

The map's *keys* are weak references to the ThreadLocal object, but the *values* are strong. While the static
ThreadLocal exists nothing is collected, and on redeploys stale values can pin whole classloaders in memory. Always
`remove()` in a finally block. The same applies to the logging MDC and the security context. Virtual threads (one per
task, never pooled) don't bleed values between tasks, but each thread gets its own copy, so heavy per-thread caches
multiply memory. `ScopedValue` (final in Java 25) is the modern alternative.
""",
r"""
```java
try {
    if (tenant != null) TENANT.set(tenant);
    chain.doFilter(req, res);
} finally {
    TENANT.remove();   // always, even when the chain throws
}
```
""",
"Frame it as a security bug (one customer seeing another's data), not just a memory leak. That framing is what makes the answer senior-level."),

T("trap-concurrency-deadlock-lock-ordering", A, "Deadlock from inconsistent lock order", "Intermediate", "Very common",
r"""
Two requests run at the same time: `transfer(a, b, 100)` and `transfer(b, a, 50)`. What can happen, and how would you
fix it?

```java
public void transfer(Account from, Account to, long amount) {
    synchronized (from) {
        synchronized (to) {
            from.debit(amount);
            to.credit(amount);
        }
    }
}
```
""",
None, None,
"It's fine: both blocks are synchronized, so the transfers just run one after the other.",
r"""
Candidates think more locking means more safety. Each lock on its own is fine; the danger is the **order**. Thread 1
holds `a` and waits for `b`, while thread 2 holds `b` and waits for `a`. `synchronized` has no timeout, so both wait
forever, and the code passes every single-threaded test.
""",
r"""
This is a classic deadlock. All four Coffman conditions hold: mutual exclusion, hold-and-wait, no preemption, and
circular wait (T1 goes a then b, T2 goes b then a). With a short pause between the two locks, both threads hang every
time. `ThreadMXBean.findDeadlockedThreads()` reports 2 threads, and a `jstack` thread dump prints "Found one Java-level
deadlock".

The standard fix breaks circular wait by taking locks in a **global order**, for example by account id, whatever the
transfer direction. Alternatives: `ReentrantLock.tryLock(timeout)` with back-off and retry, or one coarser lock if
throughput allows. In a real system the money lives in the database, and the same rule applies there: lock rows in a
consistent order (`SELECT ... WHERE id IN (?, ?) ORDER BY id FOR UPDATE`) or use one atomic conditional UPDATE, and
handle the database's deadlock errors with a retry.
""",
r"""
```java
public void transfer(Account from, Account to, long amount) {
    Account first  = from.getId() < to.getId() ? from : to;   // same order for every caller
    Account second = (first == from) ? to : from;
    synchronized (first) {
        synchronized (second) {
            from.debit(amount);
            to.credit(amount);
        }
    }
}
```
""",
"Name the four Coffman conditions, break circular wait with lock ordering, and then map the same idea to SELECT ... FOR UPDATE in MySQL."),

T("trap-concurrency-parallel-stream-shared-state", A, "parallelStream with shared mutable state", "Intermediate", "Common",
r"""
What does this print?

```java
List<Integer> out = new ArrayList<>();
IntStream.range(0, 100_000).parallel().forEach(out::add);
System.out.println(out.size());
```
""",
["Always 100000", "Always 100000, just in a random order",
 "Unpredictable: fewer than 100000, null elements inside, or an ArrayIndexOutOfBoundsException",
 "Compile error: forEach needs a thread-safe list"], 2,
"100000, just in a random order: parallel only changes the order.",
r"""
`parallel()` looks like a free speed-up switch, so people assume the program still means the same thing. In fact it
runs the lambda on several ForkJoinPool threads at once, and `ArrayList.add` changes shared state (the size field and
the backing array) with no synchronization at all.
""",
r"""
The pipeline splits the range across common-pool worker threads, and each of them calls `out.add` concurrently.
ArrayList's `size++` and array growth race with each other. Real runs gave 63,641 elements including 5,167 nulls, then
64,777, then an `ArrayIndexOutOfBoundsException`. The fix is to not mutate shared state from a stream at all: let the
stream build the result with `toList()`/`collect`, which gives each thread its own container and merges them safely.

A second trap: parallel streams run on `ForkJoinPool.commonPool()` (about cores - 1 threads), which the whole JVM shares,
including `CompletableFuture.supplyAsync` without an executor. Blocking I/O inside a parallel stream (HTTP or DB calls)
starves everyone else using that pool. Parallel streams only pay off for large, CPU-bound work on sources that split
well.
""",
r"""
```java
List<Integer> out = IntStream.range(0, 100_000).parallel().boxed().toList();   // safe

// I/O fan-out: use your own executor (here virtual threads), not parallelStream
try (ExecutorService ex = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Price>> futures = ids.stream()
            .map(id -> ex.submit(() -> client.price(id)))
            .toList();
    // ... collect results with future.get()
}
```
""",
"Say 'parallel streams share the common pool' and that you would never put blocking calls in them. That's the production lesson."),

T("trap-concurrency-completablefuture-swallowed", A, "CompletableFuture swallows exceptions", "Intermediate", "Common",
r"""
What shows up in the console or logs?

```java
CompletableFuture.runAsync(() -> {
    throw new IllegalStateException("payment callback failed");
});
Thread.sleep(500);
System.out.println("done");
```
""",
["A stack trace from the worker thread's uncaught-exception handler, then \"done\"",
 "Only \"done\": the exception is stored in the future and nobody ever sees it",
 "The exception propagates to the caller and \"done\" is never printed",
 "The JVM exits with a non-zero code"], 1,
"A stack trace gets printed, just like an exception in a plain Thread.",
r"""
With `new Thread(...)`, an uncaught exception reaches the default uncaught-exception handler, which prints a stack
trace, and candidates expect the same here. But CompletableFuture catches the exception and completes the future
exceptionally. If nobody calls `get`/`join` or attaches a handler, the failure is silently dropped.
""",
r"""
`runAsync`/`supplyAsync` wrap the task, so any exception completes the future exceptionally and stays inside it. The
program prints only `done`: no log line, no stack trace. You see the error only when you observe the future. `get()`
throws a checked `ExecutionException` and `join()` an unchecked `CompletionException`, both with the original exception
as the cause.

Exceptions that pass through dependent stages arrive wrapped as well. After a `thenApply`, an `exceptionally` handler
receives a `CompletionException` whose cause is the real error, and the `thenApply` body is skipped. Also, without an
executor argument the async methods run on `ForkJoinPool.commonPool()`, a poor place for blocking I/O. Fire-and-forget
futures need an explicit handler that logs, and production code should pass its own executor.
""",
r"""
```java
CompletableFuture.supplyAsync(() -> gateway.charge(req), paymentExecutor)  // dedicated executor
    .thenApply(this::toReceipt)
    .whenComplete((receipt, ex) -> {
        if (ex != null) log.error("charge failed for {}", req.id(), ex);
    });

// when you need the result, don't wait forever
Receipt r = future.get(2, TimeUnit.SECONDS);
```
""",
"Mention that fire-and-forget futures need whenComplete/exceptionally logging and a dedicated executor. Reviewers flag both in production code."),

T("trap-concurrency-wait-without-loop", A, "wait() in an if instead of a while", "Intermediate", "Common",
r"""
Two consumer threads are waiting in `take()` when a producer adds **one** job. What can go wrong?

```java
public synchronized Job take() throws InterruptedException {
    if (queue.isEmpty()) {
        wait();
    }
    return queue.remove();
}

public synchronized void put(Job job) {
    queue.add(job);
    notifyAll();
}
```
""",
["Nothing: wait() only returns when there is a job for this thread",
 "The second consumer to wake up can call remove() on an empty queue and get NoSuchElementException",
 "Deadlock, because wait() keeps holding the monitor",
 "IllegalMonitorStateException, because wait() is called inside synchronized"], 1,
"Nothing: the consumer waits until it is notified, and a notification means a job is available.",
r"""
Candidates read wait/notify as 'sleep until the condition becomes true'. A notification only means 'something
changed, check again'. By the time a woken thread gets the monitor back, another thread may already have taken the
item. Threads can also wake up spuriously, with no notification at all.
""",
r"""
`notifyAll()` wakes both consumers, and they compete for the monitor. The first removes the only job. Then the second
gets the monitor, returns from `wait()`, skips the check (it was an `if`), and `queue.remove()` throws
`NoSuchElementException`. Spurious wakeups, which the Java spec explicitly allows, cause the same failure. The rule:
always call `wait()` inside a `while` loop that re-checks the condition.

Other facts interviewers probe: `wait()` releases the monitor while waiting, so there's no deadlock here. Calling
`wait()`/`notify()` without holding the object's monitor compiles but throws `IllegalMonitorStateException` at
runtime. And using `notify()` instead of `notifyAll()` can wake the 'wrong' kind of waiter and stall the system. In
real code, use a `BlockingQueue`, which already gets all of this right.
""",
r"""
```java
public synchronized Job take() throws InterruptedException {
    while (queue.isEmpty()) {   // re-check after every wakeup
        wait();
    }
    return queue.remove();
}

// better: don't hand-roll it
BlockingQueue<Job> jobs = new LinkedBlockingQueue<>(1_000);   // bounded
Job next = jobs.take();
```
""",
"Say 'wait always goes in a while loop' before they ask, then suggest BlockingQueue to show you would never hand-roll this in production."),

T("trap-concurrency-executors-unbounded-queue", A, "Executors.newFixedThreadPool has an unbounded queue", "Advanced", "Common",
r"""
During an incident the downstream service slows from 200 ms to 5 seconds per call, while events keep arriving at
500 per second. What happens to this service?

```java
@Component
public class WebhookProcessor {
    private final ExecutorService pool = Executors.newFixedThreadPool(10);

    public void onEvent(Event e) {
        pool.submit(() -> callSlowDownstream(e));
    }
}
```
""",
None, None,
"Processing just gets slower; the pool has only 10 threads, so resource use is capped.",
r"""
The name 'fixed thread pool' suggests fixed resource use. The thread count is fixed, but the work queue behind it is an
unbounded `LinkedBlockingQueue`. Nothing pushes back on the callers, so tasks pile up in memory faster than 10 threads
can drain them, and latency and heap usage grow until something breaks.
""",
r"""
`newFixedThreadPool(10)` uses a `LinkedBlockingQueue` with capacity `Integer.MAX_VALUE`. At 5 s per task, 10 threads
finish 2 tasks per second while 500 arrive, so the queue grows by about 498 tasks every second. Each task holds its
event in memory, so the heap climbs until GC pauses get long or an `OutOfMemoryError` hits. Queued events are lost if
the pod restarts, and callers never see an error that would tell them to slow down.

`newCachedThreadPool()` fails the other way: its maximum pool size is `Integer.MAX_VALUE` with a `SynchronousQueue`, so
it keeps creating threads until "unable to create native thread". Instead, configure a `ThreadPoolExecutor` explicitly
with a bounded queue, a rejection policy (`CallerRunsPolicy` slows the producer down), named threads, metrics on queue
depth, and timeouts on downstream calls. Shut pools down too: leftover non-daemon threads stop the JVM from exiting.
""",
r"""
```java
ExecutorService pool = new ThreadPoolExecutor(
        10, 10, 0L, TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<>(1_000),                   // bounded backlog
        Thread.ofPlatform().name("webhook-", 0).factory(), // named threads (Java 21)
        new ThreadPoolExecutor.CallerRunsPolicy());        // back-pressure instead of OOM

// Spring: ThreadPoolTaskExecutor with setQueueCapacity(...) and graceful shutdown.
// Java 19+: try (ExecutorService ex = ...) { ... } shuts down and waits on exit.
```
""",
"Talk about back-pressure: a bounded queue plus a rejection policy turns a downstream outage into slower intake instead of an OOM in your own service."),

T("trap-concurrency-virtual-thread-pinning", A, "Virtual threads pinned by synchronized (Java 21)", "Advanced", "Common",
r"""
A Java 21 Spring Boot service turns on virtual threads (`spring.threads.virtual.enabled=true`). Each symbol has its
own lock, so there is no lock contention:

```java
private final Map<String, Object> locks = new ConcurrentHashMap<>();

public Quote fetch(String symbol) {
    synchronized (locks.computeIfAbsent(symbol, k -> new Object())) {
        return callPricingService(symbol);   // blocking HTTP call, ~100 ms
    }
}
```

With 1,000 concurrent requests for *different* symbols, throughput is as if only a handful run at a time. Why?
""",
["Virtual threads are slower than platform threads for I/O",
 "Each virtual thread that blocks inside synchronized pins its carrier thread, so only about as many calls as CPU cores run at once",
 "synchronized isn't allowed on virtual threads, so the JVM falls back to a single thread",
 "ConcurrentHashMap.computeIfAbsent serializes all callers"], 1,
"Virtual threads just don't help with I/O-bound work, or the ConcurrentHashMap is the bottleneck.",
r"""
Virtual threads are sold as 'write blocking code, get async scalability', so people assume every blocking call
unmounts the virtual thread. In Java 21 to 23, a virtual thread that blocks while holding a monitor (`synchronized`)
cannot unmount. It stays pinned to its carrier platform thread, and the scheduler has only about one carrier per core.
""",
r"""
Virtual threads run on a small ForkJoinPool of carrier threads (one per core by default). When a virtual thread blocks
on I/O or `sleep`, it normally unmounts and frees its carrier. In JDK 21 to 23, blocking inside a `synchronized` block
or method **pins** the carrier, so only about as many of these calls as you have cores make progress at once. In a
test with 2 carriers, 40 tasks each blocking for 100 ms took about 2,000 ms inside `synchronized` and about 100 ms
with `ReentrantLock`.

Fixes: use `ReentrantLock` around blocking sections on hot paths; upgrade to JDK 24+, where JEP 491 removed pinning for
`synchronized` (native frames still pin); and find pinning with the JFR event `jdk.VirtualThreadPinned` (or
`-Djdk.tracePinnedThreads` on 21 to 23). Also, don't pool virtual threads, and limit access to scarce resources such
as DB connections with a `Semaphore` or the connection pool itself.
""",
r"""
```java
private final Map<String, ReentrantLock> locks = new ConcurrentHashMap<>();

public Quote fetch(String symbol) {
    ReentrantLock lock = locks.computeIfAbsent(symbol, k -> new ReentrantLock());
    lock.lock();                 // a blocked virtual thread unmounts and frees the carrier
    try {
        return callPricingService(symbol);
    } finally {
        lock.unlock();
    }
}
```
""",
"Mention that JDK 24 (JEP 491) fixed synchronized pinning. Knowing the version history shows you actually follow the platform."),
]
