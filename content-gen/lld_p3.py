from lld_common import *

topics = []

topics.append(T(
"lru-cache-lld", "Design an LRU Cache (with Pluggable Eviction)", 9, "Intermediate", 40,
"Build an O(1) LRU cache from a HashMap and a doubly linked list, then generalise it into an extensible, thread-safe cache with pluggable eviction policies.",
r'''
## Problem
Design an in-memory cache with fixed capacity. `get(key)` returns the value or null; `put(key, value)` inserts/updates. When full, evict the **least recently used** entry. Both operations must be **O(1)**. Then the LLD follow-up: make the eviction policy pluggable (LRU, LFU, FIFO) and the cache thread-safe.

## Requirements
**P0**
1. `get` and `put` in O(1).
2. Capacity-bound; evict LRU on overflow.
3. Generic keys and values.

**P1:** pluggable eviction policy, thread safety, TTL per entry, hit/miss stats.

## Entities
`Cache<K,V>` (interface), `Storage<K,V>`, `EvictionPolicy<K>`, `LRUEvictionPolicy<K>` (doubly linked list + map of nodes), `DoublyLinkedList<K>`, `Node<K>`.

## Class diagram
```text
<<interface>> Cache<K,V>   + get(K): V   + put(K,V)

GenericCache<K,V> implements Cache
  - storage: Map<K,V>
  - policy: EvictionPolicy<K>
  - capacity
  - lock: ReentrantLock

<<interface>> EvictionPolicy<K>
  + keyAccessed(K)       // on get/put
  + evictKey(): K        // victim
  + remove(K)
   ^.. LRUEvictionPolicy  (DoublyLinkedList + Map<K, Node>)
   ^.. FIFOEvictionPolicy (LinkedHashSet)

DoublyLinkedList<K>  - head, tail sentinels
  + addLast(node), remove(node), removeFirst()
```

## Why HashMap + doubly linked list?
- The **map** gives O(1) lookup from key to its list node.
- The **doubly linked list** keeps recency order; with a direct node reference, unlinking and appending are O(1) (a singly linked list would need the previous node, which is O(n) to find).
- Convention here: **head = least recent, tail = most recent**. Access moves a node to the tail; eviction removes from the head.
- Sentinel (dummy) head/tail nodes remove null checks.

## Patterns used and why
- **Strategy** for eviction: the cache asks the policy which key to evict; LRU/LFU/FIFO are interchangeable (exactly the structure used in the popular "design a cache" machine-coding problem).
- **Generics** for type safety.
- **Separation of concerns:** storage vs eviction bookkeeping.
- **Thread safety:** LRU mutates the list even on `get`, so a read-write lock gives little benefit; a single `ReentrantLock` around operations is correct and simple. For high concurrency, shard into N independent caches by key hash (as Caffeine/Guava do in spirit).

## Java implementation
```java
import java.util.*;
import java.util.concurrent.locks.ReentrantLock;

interface Cache<K, V> {
    V get(K key);
    void put(K key, V value);
    int size();
}

interface EvictionPolicy<K> {
    void keyAccessed(K key);
    K evictKey();
    void remove(K key);
}

class Node<K> {
    K key; Node<K> prev, next;
    Node(K key) { this.key = key; }
}

class DoublyLinkedList<K> {
    private final Node<K> head = new Node<>(null), tail = new Node<>(null);
    DoublyLinkedList() { head.next = tail; tail.prev = head; }

    void addLast(Node<K> n) {
        n.prev = tail.prev; n.next = tail;
        tail.prev.next = n; tail.prev = n;
    }
    void remove(Node<K> n) {
        n.prev.next = n.next; n.next.prev = n.prev;
        n.prev = n.next = null;
    }
    Node<K> removeFirst() {
        if (head.next == tail) return null;
        Node<K> n = head.next;
        remove(n);
        return n;
    }
}

class LRUEvictionPolicy<K> implements EvictionPolicy<K> {
    private final DoublyLinkedList<K> list = new DoublyLinkedList<>();
    private final Map<K, Node<K>> nodes = new HashMap<>();

    public void keyAccessed(K key) {
        Node<K> n = nodes.get(key);
        if (n != null) list.remove(n);
        else { n = new Node<>(key); nodes.put(key, n); }
        list.addLast(n);                     // most recently used at tail
    }
    public K evictKey() {
        Node<K> n = list.removeFirst();      // least recently used at head
        if (n == null) return null;
        nodes.remove(n.key);
        return n.key;
    }
    public void remove(K key) {
        Node<K> n = nodes.remove(key);
        if (n != null) list.remove(n);
    }
}

class FIFOEvictionPolicy<K> implements EvictionPolicy<K> {
    private final LinkedHashSet<K> order = new LinkedHashSet<>();
    public void keyAccessed(K key) { order.add(key); }       // re-access does not change order
    public K evictKey() {
        Iterator<K> it = order.iterator();
        if (!it.hasNext()) return null;
        K k = it.next(); it.remove(); return k;
    }
    public void remove(K key) { order.remove(key); }
}

class GenericCache<K, V> implements Cache<K, V> {
    private final int capacity;
    private final Map<K, V> storage = new HashMap<>();
    private final EvictionPolicy<K> policy;
    private final ReentrantLock lock = new ReentrantLock();
    private long hits, misses, evictions;
    private java.util.function.Consumer<K> evictionListener = k -> { };

    void onEvict(java.util.function.Consumer<K> listener) { this.evictionListener = listener; }

    GenericCache(int capacity, EvictionPolicy<K> policy) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be > 0");
        this.capacity = capacity; this.policy = policy;
    }

    public V get(K key) {
        lock.lock();
        try {
            if (!storage.containsKey(key)) { misses++; return null; }
            hits++;
            policy.keyAccessed(key);
            return storage.get(key);
        } finally { lock.unlock(); }
    }

    public void put(K key, V value) {
        lock.lock();
        try {
            if (!storage.containsKey(key) && storage.size() == capacity) {
                K victim = policy.evictKey();
                storage.remove(victim);
                evictions++;
                evictionListener.accept(victim);
            }
            storage.put(key, value);
            policy.keyAccessed(key);
        } finally { lock.unlock(); }
    }

    public int size() { return storage.size(); }
    String stats() { return "hits=" + hits + ", misses=" + misses + ", evictions=" + evictions; }
}
```

```java
public class Main {
    public static void main(String[] args) throws InterruptedException {
        GenericCache<Integer, String> lru = new GenericCache<>(2, new LRUEvictionPolicy<>());
        lru.onEvict(k -> System.out.println("  evicted " + k));
        lru.put(1, "one");
        lru.put(2, "two");
        System.out.println("get(1) = " + lru.get(1));   // 1 becomes most recent
        lru.put(3, "three");                             // evicts 2
        System.out.println("get(2) = " + lru.get(2));
        System.out.println("get(3) = " + lru.get(3));
        System.out.println(lru.stats());

        GenericCache<String, Integer> fifo = new GenericCache<>(2, new FIFOEvictionPolicy<>());
        fifo.onEvict(k -> System.out.println("  evicted " + k));
        fifo.put("a", 1); fifo.put("b", 2); fifo.get("a");
        fifo.put("c", 3);                                // FIFO evicts a despite recent access
        System.out.println("fifo get(a) = " + fifo.get("a"));

        // Concurrency smoke test
        GenericCache<Integer, Integer> shared = new GenericCache<>(100, new LRUEvictionPolicy<>());
        Thread[] ts = new Thread[4];
        for (int t = 0; t < 4; t++) {
            final int base = t * 1000;
            ts[t] = new Thread(() -> { for (int i = 0; i < 1000; i++) { shared.put(base + i, i); shared.get(base + i); } });
            ts[t].start();
        }
        for (Thread t : ts) t.join();
        System.out.println("shared size = " + shared.size() + " (never exceeds 100), " + shared.stats());
    }
}
```

The eviction listener (a tiny Observer hook) lets callers react to evictions - log them, emit metrics, or write the entry back to a database - without the cache knowing about any of that.

## The quick interview shortcut
If asked only for an LRU cache (LeetCode 146 style), `LinkedHashMap` with access order does it in a few lines - mention it, but be ready to hand-roll the list:

```text
class LRU<K,V> extends LinkedHashMap<K,V> {
    LRU(int cap) { super(cap, 0.75f, true); this.cap = cap; }   // true = access order
    protected boolean removeEldestEntry(Map.Entry<K,V> e) { return size() > cap; }
}
```

## Extension questions
1. **LFU policy:** `Map<K, freq>` + `Map<freq, LinkedHashSet<K>>` + `minFreq` for O(1) operations.
2. **TTL:** store `expiresAt` with values; lazily expire on `get`, plus a scheduled sweeper.
3. **Higher concurrency:** segment the cache (`N` caches, pick by `hash(key) % N`) to reduce lock contention.
4. **Write policies:** write-through vs write-back to a backing store via a `CacheLoader`/`CacheWriter` interface.
5. **Distributed cache:** consistent hashing across nodes (Redis Cluster/Memcached).
''',
["HashMap gives O(1) key-to-node lookup; a doubly linked list gives O(1) reordering and eviction.",
 "Keep head as least recently used and tail as most recently used; sentinel nodes avoid null checks.",
 "Both get and put count as access and move the node to the most-recent end.",
 "EvictionPolicy as a Strategy makes LRU, LFU and FIFO interchangeable without touching the cache.",
 "LRU mutates state on reads, so a single lock (or sharding) is simpler than a read-write lock.",
 "LinkedHashMap with accessOrder=true and removeEldestEntry is the quick built-in LRU.",
 "LFU uses frequency buckets with a minFreq pointer for O(1) operations."],
[("Why does an LRU cache need a doubly linked list rather than a singly linked one?",
  r'''To move or remove an arbitrary node in O(1) we must relink its predecessor. With a doubly linked list each node knows its `prev`, so given the node from the hash map we unlink it in constant time. A singly linked list would need an O(n) traversal to find the predecessor. Sentinel head and tail nodes further simplify insertion and removal at the ends.'''),
 ("How would you make the LRU cache thread-safe?",
  r'''Every `get` modifies recency order, so even reads mutate shared structure. The simplest correct solution guards `get` and `put` with one `ReentrantLock` or `synchronized`. For high throughput, shard into multiple independent LRU segments selected by key hash, so threads touching different segments do not contend. Production libraries like Caffeine buffer access events and apply them asynchronously to avoid locking on every read. `ConcurrentHashMap` alone is insufficient because the map and list must change atomically together.'''),
 ("How do you implement LFU in O(1)?",
  r'''Keep three maps: `key -> value`, `key -> frequency`, and `frequency -> LinkedHashSet<key>` (insertion order breaks ties by recency), plus `minFreq`. On access, move the key from bucket f to f+1 and bump `minFreq` if bucket f became empty and f was the minimum. On insert into a full cache, evict the first key of the `minFreq` bucket, then insert the new key with frequency 1 and set `minFreq = 1`. All steps are O(1).'''),
 ("How would you add per-entry TTL?",
  r'''Store each value with an `expiresAt` timestamp. On `get`, if the entry has expired, remove it from storage and the eviction policy, and return a miss (lazy expiry). Because unread entries would otherwise linger, run a `ScheduledExecutorService` sweeper periodically, or keep a min-heap ordered by expiry time and pop expired entries. Inject a clock for testability.''')],
[{"title": "LeetCode 146 - LRU Cache", "url": "https://leetcode.com/problems/lru-cache/"},
 {"title": "Java SE Docs - LinkedHashMap", "url": "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/LinkedHashMap.html"}, ALLD]
))

topics.append(T(
"logger-framework", "Design a Logger Framework", 10, "Intermediate", 40,
"Design a log4j/SLF4J-style logging library with levels, multiple appenders (console, file), formatters and optional async logging, using Chain of Responsibility, Strategy and Singleton.",
r'''
## Problem
Build a reusable logging library: application code calls `logger.info("...")`; messages at or above the configured level are formatted and written to one or more destinations (console, file, database).

## Requirements
**P0**
1. Levels: `DEBUG < INFO < WARN < ERROR < FATAL`; messages below the configured level are dropped.
2. Multiple destinations (appenders) - console, file (simulated in memory), and later DB/remote.
3. Configurable format: `[timestamp] [LEVEL] [thread] message`.
4. Different destinations can have different minimum levels (e.g., ERROR+ also goes to an alert sink).
5. Thread-safe.

**P1:** async logging with a background thread, per-class loggers, log rotation.

## Entities
`LogLevel`, `LogMessage`, `Formatter`, `Appender` (sink), `LogHandler` chain (per-level handling), `Logger`, `LoggerConfig`, `AsyncAppender`.

## Class diagram
```text
enum LogLevel { DEBUG(1), INFO(2), WARN(3), ERROR(4), FATAL(5) }

LogMessage - level, text, timestamp, threadName, loggerName

<<interface>> Formatter  + format(LogMessage): String
   ^.. SimpleFormatter   ^.. JsonFormatter

<<interface>> Appender   + append(LogMessage)
   ^.. ConsoleAppender(formatter, minLevel)
   ^.. FileAppender(formatter, minLevel)
   ^.. AsyncAppender(delegate)         (decorator, BlockingQueue + worker)

Logger (one per name, via LogManager)
  - config: LoggerConfig (level, appenders)
  + debug/info/warn/error(msg)

LogManager (singleton registry)  + getLogger(name): Logger
```

## Patterns used and why
- **Strategy** for `Formatter` and `Appender`: new destinations/formats without changing `Logger`.
- **Observer-ish fan-out:** a logger publishes each message to all registered appenders.
- **Chain of Responsibility (classic textbook variant):** handlers per level, each deciding to handle and/or pass on. Shown below as an alternative because many interviewers ask for it explicitly.
- **Decorator:** `AsyncAppender` wraps any appender to make it non-blocking.
- **Singleton:** `LogManager` registry so `getLogger("OrderService")` returns the same logger everywhere.

## Java implementation
```java
import java.time.*;
import java.util.*;
import java.util.concurrent.*;

enum LogLevel {
    DEBUG(1), INFO(2), WARN(3), ERROR(4), FATAL(5);
    final int severity;
    LogLevel(int s) { severity = s; }
    boolean isAtLeast(LogLevel other) { return severity >= other.severity; }
}

record LogMessage(LogLevel level, String text, String loggerName, String thread, LocalDateTime time) { }

interface Formatter { String format(LogMessage m); }

class SimpleFormatter implements Formatter {
    public String format(LogMessage m) {
        return "[" + m.time().withNano(0) + "] [" + m.level() + "] [" + m.thread() + "] " + m.loggerName() + " - " + m.text();
    }
}

class JsonFormatter implements Formatter {
    public String format(LogMessage m) {
        return String.format("{\"level\":\"%s\",\"logger\":\"%s\",\"msg\":\"%s\"}", m.level(), m.loggerName(), m.text().replace("\"", "\\\""));
    }
}

interface Appender { void append(LogMessage m); }

abstract class LevelFilteredAppender implements Appender {
    protected final Formatter formatter; private final LogLevel minLevel;
    LevelFilteredAppender(Formatter f, LogLevel min) { formatter = f; minLevel = min; }
    public final void append(LogMessage m) { if (m.level().isAtLeast(minLevel)) write(formatter.format(m)); }
    protected abstract void write(String line);       // template method hook
}

class ConsoleAppender extends LevelFilteredAppender {
    ConsoleAppender(Formatter f, LogLevel min) { super(f, min); }
    protected synchronized void write(String line) { System.out.println(line); }
}

class FileAppender extends LevelFilteredAppender {      // simulated file: in-memory list
    private final List<String> lines = Collections.synchronizedList(new ArrayList<>());
    private final String path;
    FileAppender(String path, Formatter f, LogLevel min) { super(f, min); this.path = path; }
    protected void write(String line) { lines.add(line); }
    List<String> contents() { return lines; }
    String path() { return path; }
}

/** Decorator: hands messages to a background thread so callers never block on I/O. */
class AsyncAppender implements Appender {
    private final BlockingQueue<LogMessage> queue = new LinkedBlockingQueue<>(10_000);
    private final Thread worker;
    private volatile boolean running = true;

    AsyncAppender(Appender delegate) {
        worker = new Thread(() -> {
            try {
                while (running || !queue.isEmpty()) {
                    LogMessage m = queue.poll(100, TimeUnit.MILLISECONDS);
                    if (m != null) delegate.append(m);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        }, "async-logger");
        worker.setDaemon(true);
        worker.start();
    }
    public void append(LogMessage m) {
        if (!queue.offer(m)) System.err.println("Log queue full, dropping message");
    }
    void shutdown() throws InterruptedException { running = false; worker.join(); }
}
```

```java
class Logger {
    private final String name;
    private volatile LogLevel level = LogLevel.INFO;
    private final List<Appender> appenders = new CopyOnWriteArrayList<>();

    Logger(String name) { this.name = name; }
    void setLevel(LogLevel l) { level = l; }
    void addAppender(Appender a) { appenders.add(a); }

    private void log(LogLevel l, String msg) {
        if (!l.isAtLeast(level)) return;                 // cheap early exit
        LogMessage m = new LogMessage(l, msg, name, Thread.currentThread().getName(), LocalDateTime.now());
        for (Appender a : appenders) a.append(m);
    }
    void debug(String m) { log(LogLevel.DEBUG, m); }
    void info(String m)  { log(LogLevel.INFO, m); }
    void warn(String m)  { log(LogLevel.WARN, m); }
    void error(String m) { log(LogLevel.ERROR, m); }
    void fatal(String m) { log(LogLevel.FATAL, m); }
}

/** Singleton registry (holder idiom) returning one Logger per name. */
class LogManager {
    private final Map<String, Logger> loggers = new ConcurrentHashMap<>();
    private LogManager() { }
    private static class Holder { static final LogManager INSTANCE = new LogManager(); }
    static LogManager getInstance() { return Holder.INSTANCE; }
    Logger getLogger(String name) { return loggers.computeIfAbsent(name, Logger::new); }
}

/** Classic Chain of Responsibility version often asked in interviews. */
abstract class LogHandler {
    private final LogLevel level; private LogHandler next;
    LogHandler(LogLevel level) { this.level = level; }
    LogHandler setNext(LogHandler n) { next = n; return n; }
    void handle(LogLevel l, String msg) {
        if (l == level) System.out.println("  " + getClass().getSimpleName() + " handles: " + msg);
        else if (next != null) next.handle(l, msg);
        else System.out.println("  No handler for " + l);
    }
}
class InfoHandler extends LogHandler { InfoHandler() { super(LogLevel.INFO); } }
class WarnHandler extends LogHandler { WarnHandler() { super(LogLevel.WARN); } }
class ErrorHandler extends LogHandler { ErrorHandler() { super(LogLevel.ERROR); } }

public class Main {
    public static void main(String[] args) throws Exception {
        FileAppender errorFile = new FileAppender("errors.log", new JsonFormatter(), LogLevel.ERROR);
        AsyncAppender asyncConsole = new AsyncAppender(new ConsoleAppender(new SimpleFormatter(), LogLevel.DEBUG));

        Logger log = LogManager.getInstance().getLogger("OrderService");
        log.setLevel(LogLevel.INFO);
        log.addAppender(asyncConsole);
        log.addAppender(errorFile);

        log.debug("not printed, below INFO");
        log.info("Order 42 created");
        log.warn("Inventory low for SKU-9");
        log.error("Payment failed for order 42");
        System.out.println("Same logger instance: " + (log == LogManager.getInstance().getLogger("OrderService")));
        asyncConsole.shutdown();
        System.out.println(errorFile.path() + " -> " + errorFile.contents());

        System.out.println("Chain of Responsibility demo:");
        LogHandler chain = new InfoHandler();
        chain.setNext(new WarnHandler()).setNext(new ErrorHandler());
        chain.handle(LogLevel.WARN, "disk 85% full");
        chain.handle(LogLevel.FATAL, "JVM crash");
    }
}
```

## Extension questions
1. **Log rotation:** `RollingFileAppender` that switches files by size/date - a new appender.
2. **Back-pressure in async mode:** bounded queue; policy when full (drop DEBUG first, block, or discard oldest).
3. **Hierarchical loggers:** `com.app.order` inherits level/appenders from `com.app` (log4j-style) - lookup walks up the name hierarchy.
4. **Structured logging / MDC:** attach a request id via `ThreadLocal` context and include it in the formatter.
5. **Configuration from file:** parse a properties/YAML config into `LoggerConfig` (Builder).
''',
["Levels as an enum with severity; drop messages below the logger's level early and cheaply.",
 "Appenders (console, file, DB) and Formatters (plain, JSON) are Strategies plugged into loggers.",
 "A logger fans out each message to all appenders; each appender can have its own minimum level.",
 "AsyncAppender decorates any appender with a BlockingQueue and a background worker so callers never block on I/O.",
 "LogManager is a singleton registry returning one Logger per name via computeIfAbsent.",
 "Classic Chain of Responsibility: level handlers linked so each handles its level or passes it on.",
 "Thread safety: CopyOnWriteArrayList for appenders, volatile level, synchronized writes."],
[("Where does Chain of Responsibility fit in a logger design?",
  r'''In the classic version each level has a handler (`InfoHandler -> WarnHandler -> ErrorHandler`); a message enters the chain and each handler either processes it or forwards it. Variants let a handler process **and** forward, so an ERROR is written to the console and also escalated to an alerting sink. Real frameworks use a related structure: logger hierarchies and filter chains decide which appenders receive an event. The pattern decouples the sender from the handlers and lets you reorder or add handlers freely.'''),
 ("How does asynchronous logging work and what are the risks?",
  r'''The calling thread just enqueues a log event into a bounded `BlockingQueue` and returns; a background worker dequeues and writes to slow destinations like files or the network. This removes I/O latency from request threads. Risks: losing buffered messages if the JVM crashes (flush on shutdown via a shutdown hook), memory pressure if producers outpace the writer (use a bounded queue with a drop or block policy), and reordering across threads. Log4j2's AsyncLogger uses the LMAX Disruptor for this.'''),
 ("Why should LogManager be a singleton and how do you make it thread-safe?",
  r'''All classes asking for `getLogger("OrderService")` should share the same logger and configuration, so a single registry is natural. I use the holder idiom for lazy, lock-free initialization, and a `ConcurrentHashMap` with `computeIfAbsent` so two threads requesting the same name get the same logger instance atomically. Loggers themselves use a `volatile` level and a `CopyOnWriteArrayList` of appenders, since configuration changes are rare compared with logging calls.'''),
 ("How would you add a new destination, like sending ERROR logs to Slack?",
  r'''Implement a new `Appender` - `SlackAppender extends LevelFilteredAppender` with minimum level ERROR - whose `write()` posts to a webhook, and wrap it in `AsyncAppender` so network latency never blocks callers. Register it on the relevant loggers through configuration. No changes to `Logger`, formatters or other appenders are needed, which demonstrates the Open/Closed Principle.''')],
[{"title": "Apache Log4j 2 - Architecture", "url": "https://logging.apache.org/log4j/2.x/manual/architecture.html"},
 {"title": "Refactoring.Guru - Chain of Responsibility", "url": "https://refactoring.guru/design-patterns/chain-of-responsibility"}, ALLD]
))

topics.append(T(
"rate-limiter-lld", "Design a Rate Limiter (LLD)", 11, "Advanced", 45,
"Implement per-client rate limiting with pluggable algorithms - fixed window, sliding window log and token bucket - in thread-safe Java.",
r'''
## Problem
Protect an API by limiting how many requests each client (user id, API key or IP) may make in a time window, e.g., 5 requests per second. Requests over the limit are rejected (HTTP 429). Interviewers expect you to know several algorithms and their trade-offs, and to write a thread-safe implementation.

## Requirements
**P0**
1. `allowRequest(clientId)` returns true/false.
2. Limits configurable per client tier (FREE: 5/min, PREMIUM: 100/min).
3. Support at least two algorithms behind one interface.
4. Thread-safe under concurrent requests from the same client.

**P1:** distributed limiting across servers (Redis), per-endpoint rules, returning `Retry-After`.

## Algorithms compared
| Algorithm | Idea | Pros | Cons |
|---|---|---|---|
| Fixed window counter | Count per window `floor(now/size)` | Tiny memory, simple | Burst at window edges (2x limit across boundary) |
| Sliding window log | Store timestamps of requests in last window | Exact | Memory O(limit) per client |
| Sliding window counter | Weighted mix of current and previous window counts | Smooth, O(1) memory | Approximate |
| Token bucket | Tokens refill at rate r up to capacity b; request takes a token | Allows controlled bursts, O(1) | Two params to tune |
| Leaky bucket | Queue drains at constant rate | Smooth output | Bursts queued/dropped, adds latency |

## Entities
`RateLimiter` (interface), `FixedWindowLimiter`, `SlidingWindowLogLimiter`, `TokenBucketLimiter`, `RateLimitConfig`, `RateLimiterService` (maps clients to limiters by tier), `Clock` abstraction.

## Class diagram
```text
<<interface>> RateLimiter  + tryAcquire(): boolean     (one instance per client)
   ^.. FixedWindowLimiter(limit, windowMs)
   ^.. SlidingWindowLogLimiter(limit, windowMs)
   ^.. TokenBucketLimiter(capacity, refillPerSec)

<<interface>> LimiterFactory  + create(RateLimitConfig): RateLimiter

RateLimiterService
  - limiters: ConcurrentHashMap<clientId, RateLimiter>
  - tierConfig: Map<Tier, RateLimitConfig>
  - factory: LimiterFactory
  + allowRequest(clientId, tier): boolean

<<interface>> TimeSource  + nowMillis()   (inject fake time in tests)
```

## Patterns used and why
- **Strategy** for the algorithm; **Factory** creates the configured limiter for each new client.
- **Per-client objects in `ConcurrentHashMap.computeIfAbsent`** so each client gets exactly one limiter even under races.
- **Per-limiter synchronization**: contention only among requests of the same client.
- **Injected time source** for deterministic tests (no `Thread.sleep` in unit tests).
- **Proxy/Decorator (extension):** wrap a service so every call passes through the limiter.

## Java implementation
```java
import java.util.*;
import java.util.concurrent.*;

interface TimeSource { long nowMillis(); }

class ManualClock implements TimeSource {           // deterministic time for demos/tests
    private long now = 0;
    public long nowMillis() { return now; }
    void advance(long ms) { now += ms; }
}

interface RateLimiter { boolean tryAcquire(); }

class FixedWindowLimiter implements RateLimiter {
    private final int limit; private final long windowMs; private final TimeSource clock;
    private long windowStart = -1; private int count = 0;
    FixedWindowLimiter(int limit, long windowMs, TimeSource clock) { this.limit = limit; this.windowMs = windowMs; this.clock = clock; }
    public synchronized boolean tryAcquire() {
        long now = clock.nowMillis();
        long currentWindow = now / windowMs * windowMs;
        if (currentWindow != windowStart) { windowStart = currentWindow; count = 0; }
        if (count < limit) { count++; return true; }
        return false;
    }
}

class SlidingWindowLogLimiter implements RateLimiter {
    private final int limit; private final long windowMs; private final TimeSource clock;
    private final Deque<Long> log = new ArrayDeque<>();
    SlidingWindowLogLimiter(int limit, long windowMs, TimeSource clock) { this.limit = limit; this.windowMs = windowMs; this.clock = clock; }
    public synchronized boolean tryAcquire() {
        long now = clock.nowMillis();
        while (!log.isEmpty() && log.peekFirst() <= now - windowMs) log.pollFirst();   // drop old
        if (log.size() < limit) { log.addLast(now); return true; }
        return false;
    }
}

class TokenBucketLimiter implements RateLimiter {
    private final long capacity; private final double refillPerMs; private final TimeSource clock;
    private double tokens; private long lastRefill;
    TokenBucketLimiter(long capacity, double refillPerSecond, TimeSource clock) {
        this.capacity = capacity; this.refillPerMs = refillPerSecond / 1000.0; this.clock = clock;
        this.tokens = capacity; this.lastRefill = clock.nowMillis();
    }
    public synchronized boolean tryAcquire() {
        long now = clock.nowMillis();
        tokens = Math.min(capacity, tokens + (now - lastRefill) * refillPerMs);   // lazy refill
        lastRefill = now;
        if (tokens >= 1) { tokens -= 1; return true; }
        return false;
    }
}

enum Algorithm { FIXED_WINDOW, SLIDING_LOG, TOKEN_BUCKET }
enum Tier { FREE, PREMIUM }

record RateLimitConfig(Algorithm algorithm, int limit, long windowMs) { }

class LimiterFactory {
    private final TimeSource clock;
    LimiterFactory(TimeSource clock) { this.clock = clock; }
    RateLimiter create(RateLimitConfig c) {
        return switch (c.algorithm()) {
            case FIXED_WINDOW -> new FixedWindowLimiter(c.limit(), c.windowMs(), clock);
            case SLIDING_LOG -> new SlidingWindowLogLimiter(c.limit(), c.windowMs(), clock);
            case TOKEN_BUCKET -> new TokenBucketLimiter(c.limit(), c.limit() * 1000.0 / c.windowMs(), clock);
        };
    }
}

class RateLimiterService {
    private final Map<String, RateLimiter> limiters = new ConcurrentHashMap<>();
    private final Map<Tier, RateLimitConfig> tiers;
    private final LimiterFactory factory;
    RateLimiterService(Map<Tier, RateLimitConfig> tiers, LimiterFactory factory) { this.tiers = tiers; this.factory = factory; }

    boolean allowRequest(String clientId, Tier tier) {
        RateLimiter rl = limiters.computeIfAbsent(clientId + ":" + tier, k -> factory.create(tiers.get(tier)));
        return rl.tryAcquire();
    }
}
```

```java
public class Main {
    static String run(RateLimiter rl, int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) sb.append(rl.tryAcquire() ? "Y" : "N");
        return sb.toString();
    }

    public static void main(String[] args) throws Exception {
        ManualClock clock = new ManualClock();

        // Boundary burst problem of fixed window: 3/sec limit
        FixedWindowLimiter fw = new FixedWindowLimiter(3, 1000, clock);
        SlidingWindowLogLimiter sw = new SlidingWindowLogLimiter(3, 1000, clock);
        clock.advance(900);
        System.out.println("t=900  fixed " + run(fw, 3) + "  sliding " + run(sw, 3));
        clock.advance(200);   // t=1100, new fixed window
        System.out.println("t=1100 fixed " + run(fw, 3) + "  sliding " + run(sw, 3) + "  <- fixed allowed 6 in 200ms");

        TokenBucketLimiter tb = new TokenBucketLimiter(5, 2, clock);   // burst 5, refill 2/sec
        System.out.println("token bucket burst: " + run(tb, 7));
        clock.advance(1000);
        System.out.println("after 1s refill:    " + run(tb, 3));

        // Service with tiers + concurrency
        RateLimiterService svc = new RateLimiterService(Map.of(
            Tier.FREE, new RateLimitConfig(Algorithm.SLIDING_LOG, 5, 60_000),
            Tier.PREMIUM, new RateLimitConfig(Algorithm.TOKEN_BUCKET, 100, 60_000)), new LimiterFactory(clock));
        ExecutorService pool = Executors.newFixedThreadPool(8);
        List<Future<Boolean>> results = new ArrayList<>();
        for (int i = 0; i < 50; i++) results.add(pool.submit(() -> svc.allowRequest("user-1", Tier.FREE)));
        int allowed = 0;
        for (Future<Boolean> f : results) if (f.get()) allowed++;
        pool.shutdown();
        System.out.println("50 concurrent FREE requests -> allowed " + allowed + " (expected 5)");
    }
}
```

## Extension questions
1. **Distributed rate limiting:** keep counters in Redis. Fixed window: `INCR key; EXPIRE key window` atomically via a Lua script. Token bucket: Lua script reading/updating tokens and timestamp atomically. Or use a sliding window with sorted sets (`ZADD`, `ZREMRANGEBYSCORE`, `ZCARD`).
2. **Memory cleanup:** idle client limiters accumulate - evict via a cache with expire-after-access (e.g., Caffeine) or a periodic sweep.
3. **Rules per endpoint:** key becomes `clientId + endpoint`; rules loaded from config.
4. **Response headers:** `X-RateLimit-Remaining`, `Retry-After` computed from the window start or token deficit.
5. **Where to place it:** API gateway (Kong, Nginx, Spring Cloud Gateway `RequestRateLimiter` uses Redis token bucket) vs in-service filter.
''',
["Know the algorithms: fixed window, sliding window log, sliding window counter, token bucket, leaky bucket.",
 "Fixed window suffers from boundary bursts of up to twice the limit; sliding log is exact but stores timestamps.",
 "Token bucket refills lazily based on elapsed time and allows controlled bursts up to capacity.",
 "One limiter object per client, created atomically with ConcurrentHashMap.computeIfAbsent.",
 "Synchronize per limiter so contention is limited to requests from the same client.",
 "Inject a time source to test time-based logic deterministically.",
 "Distributed limiting uses Redis with atomic Lua scripts or INCR+EXPIRE, typically at the API gateway."],
[("Compare token bucket and sliding window algorithms.",
  r'''A **token bucket** holds up to `capacity` tokens, refilled at a fixed rate; each request consumes one. It permits short bursts (up to capacity) while enforcing an average rate, uses O(1) memory, and is used by AWS API Gateway and Spring Cloud Gateway. A **sliding window log** stores request timestamps in the last window and allows a request if the count is below the limit - exact with no boundary bursts, but O(limit) memory per client. The **sliding window counter** approximates it with two counters.'''),
 ("What is the boundary problem with fixed window rate limiting?",
  r'''Counters reset at fixed boundaries. With a limit of 100/minute, a client can send 100 requests at 12:00:59 and another 100 at 12:01:00 - 200 requests within about one second, double the intended rate. Sliding window log or counter, and token bucket, avoid this by considering the last N seconds relative to now instead of calendar-aligned windows.'''),
 ("How do you make the rate limiter thread-safe without a global lock?",
  r'''Store one limiter per client in a `ConcurrentHashMap` and create it with `computeIfAbsent`, which is atomic, so racing threads share the same instance. Inside each limiter, `tryAcquire` is synchronized (or uses `AtomicLong` with CAS loops for the counter version). Requests for different clients never contend; only concurrent requests from the same client serialize briefly. My demo fires 50 concurrent requests and exactly 5 are allowed.'''),
 ("How would you rate limit across multiple application servers?",
  r'''Local limiters would allow N times the limit with N servers, so the state must be shared. Use Redis: for a fixed window, `INCR` a key such as `rl:user:minute` with `EXPIRE`; for a token bucket or sliding window, use a Lua script so the read-compute-write is atomic on the Redis server. Sorted sets work for sliding logs. Trade-offs: an extra network hop per request, and a fail-open or fail-closed decision when Redis is unavailable.''')],
[{"title": "Cloudflare Blog - How we built rate limiting capable of scaling to millions of domains", "url": "https://blog.cloudflare.com/counting-things-a-lot-of-different-things/"},
 {"title": "Wikipedia - Token bucket", "url": "https://en.wikipedia.org/wiki/Token_bucket"},
 {"title": "Stripe Blog - Scaling your API with rate limiters", "url": "https://stripe.com/blog/rate-limiters"}]
))

topics.append(T(
"atm-machine", "Design an ATM Machine", 12, "Intermediate", 45,
"Design an ATM with card authentication, balance enquiry, withdrawal and deposit, using the State pattern for the session flow and Chain of Responsibility for cash dispensing.",
r'''
## Problem
Design the software for an ATM. A user inserts a card, enters a PIN, chooses an operation (balance, withdraw, deposit), and ejects the card. The ATM talks to a bank service and dispenses notes from its cassettes.

## Requirements
**P0**
1. Card insertion and PIN validation (3 wrong attempts blocks the card).
2. Operations: balance enquiry, cash withdrawal, cash deposit.
3. Withdrawal checks account balance, the daily limit and whether the ATM can dispense the exact amount with available notes (2000, 500, 200, 100).
4. Only valid actions per state (cannot withdraw before PIN).
5. Eject card at any time.

**P1:** transfer, mini statement, admin refill, receipts, network failures with reversal.

## Entities
`Card`, `Account`, `BankService` (interface, simulated), `CashDispenser` with a chain of `NoteHandler`s, `ATMState` interface: `IdleState`, `CardInsertedState`, `AuthenticatedState`; `ATM` (context), `Transaction`.

## Class diagram
```text
ATM (context)
  - state: ATMState
  - bank: BankService
  - dispenser: CashDispenser
  - currentCard: Card
  + insertCard(card), enterPin(pin), checkBalance(), withdraw(amt), deposit(amt), ejectCard()

<<interface>> ATMState   (same operations, each takes ATM)
   ^.. IdleState   ^.. CardInsertedState   ^.. AuthenticatedState

<<interface>> BankService
  + validatePin(card, pin): boolean
  + balance(accountNo), debit(accountNo, amt), credit(accountNo, amt)
   ^.. InMemoryBank

CashDispenser
  - chain: NoteHandler (2000 -> 500 -> 200 -> 100)
  + canDispense(amt), dispense(amt): Map<note, count>

NoteHandler - note, count, next
```

## Patterns used and why
- **State** for the session: each state allows a subset of operations, and transitions are explicit (`Idle -> CardInserted -> Authenticated -> Idle`).
- **Chain of Responsibility** for dispensing: each note handler gives as many of its notes as possible and passes the remainder on - adding a 200 note cassette is one link.
- **Facade/Adapter** for `BankService`: the ATM does not know whether the bank is local or remote.
- **Two-phase withdrawal**: check that the dispenser can produce the amount *before* debiting the account, so a successful debit is never followed by "cannot dispense".

## Java implementation
```java
import java.util.*;

class Card {
    final String number, accountNo;
    Card(String number, String accountNo) { this.number = number; this.accountNo = accountNo; }
}

class AtmException extends RuntimeException { AtmException(String m) { super(m); } }

interface BankService {
    boolean validatePin(Card card, String pin);
    long balance(String accountNo);
    void debit(String accountNo, long amount);
    void credit(String accountNo, long amount);
}

class InMemoryBank implements BankService {
    private final Map<String, String> pins = new HashMap<>();
    private final Map<String, Long> balances = new HashMap<>();
    private final Map<String, Integer> failedAttempts = new HashMap<>();
    private final Set<String> blocked = new HashSet<>();

    void open(Card c, String pin, long balance) { pins.put(c.number, pin); balances.put(c.accountNo, balance); }

    public synchronized boolean validatePin(Card card, String pin) {
        if (blocked.contains(card.number)) throw new AtmException("Card blocked");
        if (pins.get(card.number).equals(pin)) { failedAttempts.remove(card.number); return true; }
        int f = failedAttempts.merge(card.number, 1, Integer::sum);
        if (f >= 3) { blocked.add(card.number); throw new AtmException("Card blocked after 3 wrong PINs"); }
        return false;
    }
    public synchronized long balance(String acc) { return balances.get(acc); }
    public synchronized void debit(String acc, long amt) {
        if (balances.get(acc) < amt) throw new AtmException("Insufficient balance");
        balances.merge(acc, -amt, Long::sum);
    }
    public synchronized void credit(String acc, long amt) { balances.merge(acc, amt, Long::sum); }
}

class NoteHandler {
    final int note; int count; NoteHandler next;
    NoteHandler(int note, int count) { this.note = note; this.count = count; }
    NoteHandler setNext(NoteHandler n) { next = n; return n; }

    /** Plans dispensing without mutating; returns false if amount cannot be made. */
    boolean plan(int amount, Map<Integer, Integer> out) {
        int use = Math.min(amount / note, count);
        if (use > 0) out.put(note, use);
        int rest = amount - use * note;
        if (rest == 0) return true;
        return next != null && next.plan(rest, out);
    }
}

class CashDispenser {
    private final NoteHandler head;
    private final Map<Integer, NoteHandler> byNote = new LinkedHashMap<>();
    CashDispenser(int c2000, int c500, int c200, int c100) {
        head = new NoteHandler(2000, c2000);
        NoteHandler h500 = new NoteHandler(500, c500), h200 = new NoteHandler(200, c200), h100 = new NoteHandler(100, c100);
        head.setNext(h500).setNext(h200).setNext(h100);
        for (NoteHandler h : List.of(head, h500, h200, h100)) byNote.put(h.note, h);
    }
    Optional<Map<Integer, Integer>> plan(int amount) {
        Map<Integer, Integer> out = new LinkedHashMap<>();
        return head.plan(amount, out) ? Optional.of(out) : Optional.empty();
    }
    void commit(Map<Integer, Integer> plan) { plan.forEach((note, n) -> byNote.get(note).count -= n); }
    long total() { return byNote.values().stream().mapToLong(h -> (long) h.note * h.count).sum(); }
}
```

```java
interface ATMState {
    default void insertCard(ATM atm, Card c) { throw new AtmException("Card already inserted"); }
    default void enterPin(ATM atm, String pin) { throw new AtmException("Insert card first"); }
    default void checkBalance(ATM atm) { throw new AtmException("Authenticate first"); }
    default void withdraw(ATM atm, int amount) { throw new AtmException("Authenticate first"); }
    default void deposit(ATM atm, int amount) { throw new AtmException("Authenticate first"); }
    default void ejectCard(ATM atm) { System.out.println("Card ejected"); atm.reset(); }
}

class IdleState implements ATMState {
    public void insertCard(ATM atm, Card c) {
        atm.setCard(c);
        System.out.println("Card inserted. Enter PIN.");
        atm.setState(new CardInsertedState());
    }
    public void ejectCard(ATM atm) { throw new AtmException("No card to eject"); }
}

class CardInsertedState implements ATMState {
    public void enterPin(ATM atm, String pin) {
        try {
            if (atm.bank().validatePin(atm.card(), pin)) {
                System.out.println("PIN OK");
                atm.setState(new AuthenticatedState());
            } else System.out.println("Wrong PIN, try again");
        } catch (AtmException e) {
            System.out.println(e.getMessage() + ". Card retained.");
            atm.reset();
        }
    }
}

class AuthenticatedState implements ATMState {
    private static final int DAILY_LIMIT = 25_000;
    public void checkBalance(ATM atm) {
        System.out.println("Balance: Rs " + atm.bank().balance(atm.card().accountNo));
    }
    public void withdraw(ATM atm, int amount) {
        if (amount <= 0 || amount % 100 != 0) throw new AtmException("Amount must be a positive multiple of 100");
        if (amount > DAILY_LIMIT) throw new AtmException("Exceeds daily limit");
        Map<Integer, Integer> plan = atm.dispenser().plan(amount)
            .orElseThrow(() -> new AtmException("ATM cannot dispense Rs " + amount + " with available notes"));
        atm.bank().debit(atm.card().accountNo, amount);   // throws if insufficient; nothing dispensed yet
        atm.dispenser().commit(plan);
        System.out.println("Dispensed Rs " + amount + " as " + plan);
    }
    public void deposit(ATM atm, int amount) {
        atm.bank().credit(atm.card().accountNo, amount);
        System.out.println("Deposited Rs " + amount);
    }
}

class ATM {
    private ATMState state = new IdleState();
    private final BankService bank; private final CashDispenser dispenser;
    private Card card;
    ATM(BankService bank, CashDispenser dispenser) { this.bank = bank; this.dispenser = dispenser; }

    public synchronized void insertCard(Card c) { state.insertCard(this, c); }
    public synchronized void enterPin(String pin) { state.enterPin(this, pin); }
    public synchronized void checkBalance() { state.checkBalance(this); }
    public synchronized void withdraw(int amt) { state.withdraw(this, amt); }
    public synchronized void deposit(int amt) { state.deposit(this, amt); }
    public synchronized void ejectCard() { state.ejectCard(this); }

    void setState(ATMState s) { state = s; }
    void setCard(Card c) { card = c; }
    Card card() { return card; }
    BankService bank() { return bank; }
    CashDispenser dispenser() { return dispenser; }
    void reset() { card = null; state = new IdleState(); }
}

public class Main {
    static void attempt(Runnable r) {
        try { r.run(); } catch (AtmException e) { System.out.println("Error: " + e.getMessage()); }
    }
    public static void main(String[] args) {
        InMemoryBank bank = new InMemoryBank();
        Card card = new Card("4111-1111", "ACC-1");
        bank.open(card, "1234", 10_000);
        ATM atm = new ATM(bank, new CashDispenser(5, 10, 0, 10));

        attempt(() -> atm.withdraw(500));        // not authenticated
        atm.insertCard(card);
        atm.enterPin("0000");
        atm.enterPin("1234");
        atm.checkBalance();
        atm.withdraw(3700);                       // 1x2000, 3x500, 2x100
        attempt(() -> atm.withdraw(150));         // not multiple of 100
        attempt(() -> atm.withdraw(9_000));       // ATM has the notes, account balance is short
        attempt(() -> atm.withdraw(20_000));      // ATM cannot make this amount from its cassettes
        atm.deposit(1000);
        atm.checkBalance();
        atm.ejectCard();

        Card c2 = new Card("4222-2222", "ACC-2");
        bank.open(c2, "9999", 500);
        atm.insertCard(c2);
        atm.enterPin("1"); atm.enterPin("2"); atm.enterPin("3");   // blocked
        attempt(() -> atm.checkBalance());
    }
}
```

## Extension questions
1. **Network failure after debit:** record the transaction as PENDING; if dispensing fails, issue a reversal (credit) - compensating transaction; idempotent transaction ids.
2. **Optimal note mix when greedy fails** (e.g., no 100s): bounded DP over note counts.
3. **Admin operations:** separate `AdminState` after admin card + PIN; refill cassettes, audit (ISP: separate admin interface).
4. **Transfer and mini statement:** new operations on `AuthenticatedState` plus `Transaction` history in the bank service.
5. **Session timeout:** auto-eject after 30s idle using a scheduled task.
''',
["Session flow is a State machine: Idle -> CardInserted -> Authenticated -> Idle on eject or block.",
 "Default methods in the state interface reject invalid actions; each state overrides only what it allows.",
 "Cash dispensing uses Chain of Responsibility across note handlers (2000 -> 500 -> 200 -> 100).",
 "Plan dispensing first, then debit the account, then commit notes, so money is never debited without cash.",
 "BankService interface hides the bank; PIN attempts and card blocking live on the bank side.",
 "Validate amounts (positive, multiple of 100, daily limit) before touching balances.",
 "Discuss reversals for network failures and idempotent transaction ids."],
[("Why use the State pattern in an ATM?",
  r'''The valid operations depend entirely on the session phase: you cannot enter a PIN without a card or withdraw before authentication. With State, each phase is a class that implements only its allowed operations and triggers transitions, while the `ATM` context delegates. Default interface methods throw meaningful errors for invalid actions. New phases (admin mode, out-of-service) are new classes rather than new branches in every method.'''),
 ("How does Chain of Responsibility help in dispensing cash?",
  r'''Each cassette is a handler for one note value. The request (amount) enters the 2000 handler, which uses as many notes as it can given its count and passes the remainder to the 500 handler, and so on. If the last handler still has a remainder, the amount cannot be dispensed. Adding or removing denominations means relinking handlers, not changing logic. I plan first without mutating counts and commit only after the account debit succeeds.'''),
 ("What if the bank debits the account but the ATM fails to dispense?",
  r'''That is a distributed consistency problem. First, minimise it by verifying that the dispenser can produce the amount before debiting. Second, record each withdrawal with a unique transaction id and state (INITIATED, DEBITED, DISPENSED). If dispensing fails after the debit, the ATM sends a reversal (compensating credit) referencing the same id; the bank processes it idempotently. Reconciliation jobs compare ATM journals with bank records to catch anything left over.'''),
 ("Where should PIN validation and attempt counting happen?",
  r'''On the bank side, not in the ATM. The ATM forwards the PIN (encrypted with hardware security modules in reality) and the bank validates it, increments failed attempts and blocks the card after three failures. This keeps the policy consistent across all ATMs and channels, so a user cannot reset the counter by moving to another machine. The ATM only reacts to the result: retry, proceed, or retain the card.''')],
[ALLD, {"title": "awesome-low-level-design - ATM", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/atm.md"},
 {"title": "Refactoring.Guru - Chain of Responsibility", "url": "https://refactoring.guru/design-patterns/chain-of-responsibility"}]
))

save("p3", "problems", topics)
