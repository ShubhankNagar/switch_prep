from fr2_common import M, C, T, save

mcqs = [
M("JPA / Hibernate", r'''
Loading 50 `Order` entities and then calling `order.getItems()` on each one fires 51 SQL queries. What is this called, and what's the usual fix?
```java
List<Order> orders = orderRepo.findAll();
orders.forEach(o -> o.getItems().size());
```''', ["A Cartesian product. Fix it with DISTINCT", "The N+1 select problem. Fix it with JOIN FETCH or @EntityGraph (or batch fetching)",
 "A deadlock. Fix it with @Lock", "A first-level cache miss. Fix it with @Cacheable"], 1,
'''One query loads the orders, then each lazy collection triggers its own query. `@Query("select o from Order o join fetch o.items")`, an `@EntityGraph(attributePaths="items")`, or `@BatchSize`/`hibernate.default_batch_fetch_size` cuts it to one or a few queries.''', ["Myntra", "Paytm", "Walmart"]),

M("JPA / Hibernate", '''What are the default fetch types in JPA?''',
["All associations are LAZY", "@ManyToOne and @OneToOne are EAGER. @OneToMany and @ManyToMany are LAZY",
 "All associations are EAGER", "@OneToMany is EAGER, everything else is LAZY"], 1,
'''Single-valued associations default to EAGER and collections default to LAZY. Best practice is to make @ManyToOne LAZY explicitly too, and fetch what you need for each use case, because eager defaults quietly cause N+1 queries and over-fetching.''', ["Walmart", "Oracle", "PhonePe"]),

M("JPA / Hibernate", '''A controller returns an entity, and Jackson's serialization of a lazy collection fails with `LazyInitializationException: could not initialize proxy - no Session`. What's the root cause?''',
["The database is down", "The lazy association is accessed after the persistence context (transaction) has closed",
 "Jackson can't serialize Lists", "The entity has no @Id"], 1,
'''A lazy proxy needs an open session to load. Once the @Transactional service method returns, the session is closed. Fix it by fetching what you need inside the transaction (fetch join or a DTO projection). Avoid patching it with open-in-view or EAGER.''', ["Paytm", "Myntra", "Intuit"]),

M("JPA / Hibernate", r'''
`e1` is a **detached** `Employee`. After this runs inside a transaction, which object is managed?
```java
Employee e2 = entityManager.merge(e1);
e1.setName("X");   // change A
e2.setName("Y");   // change B
```''', ["e1. Change A is saved", "e2. Change B is saved at flush, and change A is not", "Both are managed", "Neither. merge throws for detached entities"], 1,
'''`merge` copies the detached object's state onto a managed instance and returns that instance. The argument stays detached. Dirty checking only tracks managed entities, so only `e2`'s change gets flushed.''', ["Oracle", "SAP"]),

M("JPA / Hibernate", '''What is the scope of Hibernate's first-level cache?''',
["The whole application (JVM)", "One Session / EntityManager (persistence context)", "One HTTP session", "One database connection pool"], 1,
'''The first-level cache is always on and lives inside a persistence context. Calling `find(id)` twice in the same transaction hits the database once. A second-level cache, such as Ehcache or Hazelcast, is optional and shared across sessions.''', ["JP Morgan", "Oracle", "Walmart"]),

M("Spring Core", '''A `prototype`-scoped bean is injected with `@Autowired` into a `singleton` service. How many prototype instances does the service actually use over its lifetime?''',
["A new one for each method call", "One. It's injected once when the singleton is created",
 "One per thread", "It fails at startup"], 1,
'''Dependencies are injected once, when the singleton is built, so the prototype acts like a singleton inside it. To get a fresh instance each time, use `ObjectProvider<T>.getObject()`, `@Lookup` methods or a scoped proxy.''', ["Walmart", "JP Morgan", "Salesforce"]),

M("Spring Transactions", '''What does `@Transactional(readOnly = true)` mainly do with Hibernate?''',
["It blocks INSERT statements at the database level", "It sets the flush mode to MANUAL and skips dirty checking, which is a performance hint. Some drivers also route the query to a read replica",
 "It opens no transaction at all", "It caches all results"], 1,
'''Hibernate skips snapshotting and flushing, which saves memory and CPU. The driver or routing DataSource may also treat the connection as read-only. It's an optimization hint, not a security guarantee.''', ["Intuit", "Walmart"]),

M("Spring Security", '''In a stateless JWT setup, where is the token usually validated in a Spring Boot app?''',
["In every controller method", "In a custom `OncePerRequestFilter` added before `UsernamePasswordAuthenticationFilter`, which puts the Authentication into the SecurityContextHolder",
 "In the database trigger", "In application.properties"], 1,
'''The filter reads the `Authorization: Bearer` header, checks the signature and expiry, loads the authorities and sets the SecurityContext for that request. Later authorization (`@PreAuthorize`, URL rules) relies on it. Spring's built-in `oauth2ResourceServer().jwt()` does the same thing.''', ["Intuit", "PhonePe", "Salesforce"]),

M("Spring Security", '''Why do teams often disable CSRF protection for stateless REST APIs that authenticate with a JWT in the Authorization header?''',
["CSRF only affects GET requests", "CSRF exploits credentials the browser sends automatically (cookies). A header token isn't attached by the browser, so a forged cross-site request can't carry it",
 "JWTs are encrypted", "Spring doesn't support CSRF for REST"], 1,
'''CSRF works because browsers attach session cookies to cross-site requests automatically. If authentication comes only from a header that JavaScript sets explicitly, an attacker's site can't make the browser add it. Keep CSRF on if the JWT is stored in a cookie.''', ["Intuit", "Atlassian"]),

M("Kafka", '''A topic has 6 partitions. One consumer group has 8 consumer instances. What happens?''',
["Each partition is shared by several consumers", "6 consumers get one partition each and 2 sit idle",
 "Kafka creates 2 new partitions automatically", "Every consumer reads every message"], 1,
'''Within a group, each partition is assigned to exactly one consumer. Consumers beyond the partition count stay idle, acting as hot standbys. Parallelism in a group is capped by the number of partitions.''', ["Walmart", "Swiggy", "PhonePe"]),

M("Kafka", '''A consumer commits offsets **before** it processes each batch, and it crashes in the middle of a batch. Which delivery semantic results?''',
["Exactly-once", "At-most-once: the unprocessed messages are skipped after restart", "At-least-once", "Messages are reprocessed twice"], 1,
'''The committed offset already points past the batch, so the restarted consumer skips messages that were never processed. Committing after processing gives at-least-once, which needs idempotent consumers. Exactly-once needs idempotent producers plus transactions (read-process-write).''', ["Walmart", "Razorpay", "Uber"]),

M("Kafka", '''Which producer settings stop duplicate writes caused by producer retries?''',
["acks=0", "enable.idempotence=true (with acks=all). The broker de-duplicates using the producer ID and sequence numbers",
 "linger.ms=0", "compression.type=gzip"], 1,
'''An idempotent producer stamps each batch with a PID and a sequence number per partition. The broker drops repeats caused by retries. It's on by default since Kafka 3.0. Duplicates on the consumer side still need idempotent handling.''', ["PhonePe", "Walmart"]),

M("Docker", '''A Dockerfile has `ENTRYPOINT ["java","-jar","app.jar"]` and `CMD ["--spring.profiles.active=dev"]`. What happens with `docker run img --spring.profiles.active=prod`?''',
["The ENTRYPOINT is replaced", "The CMD is replaced, so the container runs java -jar app.jar --spring.profiles.active=prod",
 "Both args are appended", "Docker errors out"], 1,
'''Arguments passed to `docker run` replace CMD. CMD acts as the default arguments to ENTRYPOINT. Overriding the ENTRYPOINT itself needs the `--entrypoint` flag. This pattern lets one image run with different profiles.''', ["ServiceNow", "SAP", "Walmart"]),

M("Kubernetes", '''A pod's **readiness** probe fails while its **liveness** probe passes. What does Kubernetes do?''',
["It restarts the container", "It removes the pod from Service endpoints so it gets no traffic, and doesn't restart it",
 "It deletes the Deployment", "Nothing"], 1,
'''Readiness controls whether a pod receives traffic, which is useful during warm-up or when a dependency is down. Liveness failures restart the container. Spring Boot Actuator exposes `/actuator/health/readiness` and `/liveness` for these probes.''', ["ServiceNow", "Walmart", "Salesforce"]),

M("Kubernetes", '''A Kafka or Zookeeper cluster needs stable pod names (kafka-0, kafka-1), ordered startup and a persistent volume per pod. Which workload object fits?''',
["Deployment", "StatefulSet", "DaemonSet", "ReplicaSet"], 1,
'''StatefulSets give each pod a sticky identity, a stable DNS name through a headless service, ordered rollout, and its own PersistentVolumeClaim. Deployments are for stateless, interchangeable pods. A DaemonSet runs one pod on each node.''', ["ServiceNow", "SAP"]),

M("Microservices", '''In Resilience4j's circuit breaker, what happens in the HALF_OPEN state?''',
["All calls are rejected", "A limited number of trial calls go through. If they succeed the breaker closes, and if they fail it opens again",
 "All calls go through without monitoring", "The service restarts"], 1,
'''CLOSED: calls pass and failures are counted. OPEN: calls fail fast for a wait period. HALF_OPEN: a few probe calls test whether the downstream service has recovered. Pair it with timeouts, retries with backoff and fallbacks.''', ["Walmart", "Salesforce", "Swiggy"]),

M("Spring Boot", '''How does Spring Boot decide which auto-configurations to apply (Boot 3.x)?''',
["It applies every configuration class on the classpath", "It reads auto-configuration classes listed in `META-INF/spring/...AutoConfiguration.imports` and applies those whose `@Conditional...` checks pass",
 "Only from application.yml", "From a hardcoded list in SpringApplication"], 1,
'''`@EnableAutoConfiguration` loads candidate classes (older versions used `spring.factories`). Conditions such as `@ConditionalOnClass`, `@ConditionalOnMissingBean` and `@ConditionalOnProperty` decide which apply, so beans you define yourself override the defaults. Run with `--debug` to see the condition report.''', ["Walmart", "JP Morgan", "Oracle"]),

M("Spring Boot", '''With Spring Boot 3 defaults and the `spring-boot-starter-actuator` dependency added, which actuator endpoint is exposed over HTTP?''',
["All endpoints", "Only /actuator/health", "/actuator/env and /actuator/beans", "None"], 1,
'''Only `health` is exposed over the web by default. Others need `management.endpoints.web.exposure.include=...`. Exposing `env`, `heapdump` or `beans` publicly can leak secrets, so secure them with Spring Security.''', ["Intuit", "ServiceNow"]),

M("REST", '''A `@Valid @RequestBody` DTO fails bean validation (for example `@NotBlank` on email). What does Spring MVC do by default?''',
["Returns 500", "Throws MethodArgumentNotValidException, which becomes 400 Bad Request (customize it with @RestControllerAdvice)",
 "Ignores the error", "Returns 422 always"], 1,
'''Validation fails before the controller method runs. Handle `MethodArgumentNotValidException` in a `@RestControllerAdvice` to return field-level error details, for example as a ProblemDetail (RFC 7807, built in since Boot 3).''', ["Paytm", "Walmart"]),

M("Microservices", '''In a microservices setup, which of these is a job for the API gateway rather than an individual service?''',
["Business logic for calculating discounts", "Cross-cutting concerns such as routing, authentication/token validation, rate limiting and request aggregation",
 "Owning the order database", "Running batch jobs"], 1,
'''A gateway like Spring Cloud Gateway or Kong is the single entry point. It handles routing, TLS, auth, throttling, CORS and sometimes response aggregation. Business rules belong in the domain services, not the edge.''', ["Salesforce", "Swiggy", "Myntra"]),
]

coding = [
C("Design Hit Counter (Requests in Last 5 Minutes)", "Medium", ["Google", "Atlassian", "Uber", "Microsoft"], r'''
Build a hit counter that counts requests to an endpoint over the **last 300 seconds**:
- `hit(int timestamp)` records one hit at that second.
- `getHits(int timestamp)` returns the number of hits in `(timestamp − 300, timestamp]`.

Calls arrive in non-decreasing timestamp order. Many hits can share the same timestamp.

**Example**
```
hit(1); hit(2); hit(3);
getHits(4)   -> 3
hit(300);
getHits(300) -> 4
getHits(301) -> 3     // hit at t=1 has expired
```
**Follow-up:** the endpoint gets millions of hits per second. Memory must not grow with the number of hits.''',
["A simple version stores timestamps in a queue and drops old ones from the front.",
 "For constant memory, use two circular arrays of size 300: times[i] and counts[i] for bucket timestamp % 300."],
r'''
class HitCounter {
    private static final int WINDOW = 300;
    private final int[] times = new int[WINDOW];
    private final int[] counts = new int[WINDOW];

    public void hit(int timestamp) {
        int idx = timestamp % WINDOW;
        if (times[idx] != timestamp) {   // bucket holds a stale second: reset it
            times[idx] = timestamp;
            counts[idx] = 0;
        }
        counts[idx]++;
    }

    public int getHits(int timestamp) {
        int total = 0;
        for (int i = 0; i < WINDOW; i++) {
            if (timestamp - times[i] < WINDOW) total += counts[i];
        }
        return total;
    }

    public static void main(String[] args) {
        HitCounter c = new HitCounter();
        c.hit(1); c.hit(2); c.hit(3);
        System.out.println(c.getHits(4));     // 3
        c.hit(300);
        System.out.println(c.getHits(300));   // 4
        System.out.println(c.getHits(301));   // 3
    }
}''',
'''This is a **circular bucket** (ring buffer) design. Each second maps to slot `t % 300`. If the slot holds an older second, it's stale and gets reset before counting. `getHits` adds up only the buckets whose timestamp falls inside the window. Memory is fixed at 600 ints however heavy the traffic, which answers the follow-up. A queue-based version is simpler but stores every hit. For concurrency, use `AtomicIntegerArray` or a lock per bucket, or `LongAdder` per bucket. This is the same sliding-window counter idea behind API rate limiters and Micrometer metrics. Interviewers at Atlassian and Uber reportedly extend it to a distributed version using Redis sorted sets or time-bucketed keys.''',
"hit O(1), getHits O(300)", "O(300)", "https://leetcode.com/problems/design-hit-counter/"),

C("Time Based Key-Value Store (Config Versioning)", "Medium", ["Google", "Uber", "Atlassian", "Walmart"], r'''
Design a store that keeps multiple versions of a value, such as a feature-flag config:
- `set(String key, String value, int timestamp)`
- `get(String key, int timestamp)` returns the value set at the **largest timestamp ≤ the given timestamp**, or `""` if there isn't one.

For a given key, `set` calls come with strictly increasing timestamps.

**Example**
```
set("foo","bar",1)
get("foo",1) -> "bar"
get("foo",3) -> "bar"
set("foo","bar2",4)
get("foo",4) -> "bar2"
get("foo",5) -> "bar2"
get("foo",0) -> ""
```
**Constraints:** 1 ≤ timestamp ≤ 10^7, up to 2·10^5 calls.''',
["Each key maps to a list of (timestamp, value) pairs that is already sorted, because timestamps increase.",
 "Binary search for the floor timestamp. A TreeMap's floorEntry works too."],
r'''
import java.util.*;

class TimeMap {
    private record Version(int ts, String value) { }
    private final Map<String, List<Version>> store = new HashMap<>();

    public void set(String key, String value, int timestamp) {
        store.computeIfAbsent(key, k -> new ArrayList<>()).add(new Version(timestamp, value));
    }

    public String get(String key, int timestamp) {
        List<Version> versions = store.get(key);
        if (versions == null) return "";
        int lo = 0, hi = versions.size() - 1, ans = -1;
        while (lo <= hi) {                       // last index with ts <= timestamp
            int mid = (lo + hi) >>> 1;
            if (versions.get(mid).ts() <= timestamp) {
                ans = mid;
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return ans == -1 ? "" : versions.get(ans).value();
    }
}''',
'''Since each key's timestamps arrive in increasing order, appending to an ArrayList keeps the versions sorted at no extra cost. `get` is then a **floor binary search**: find the last version whose timestamp is ≤ the query. A `TreeMap<Integer,String>` per key with `floorEntry` gives the same O(log n) with less code, at a higher memory cost per entry. You'll find this pattern in config services, MVCC snapshot reads, price histories and audit trails. Reported follow-ups: making it thread-safe (a `ConcurrentHashMap` of `ConcurrentSkipListMap`, which has lock-free floor lookups), handling out-of-order writes (the skip list handles that too), and expiring old versions to bound memory.''',
"set O(1), get O(log n)", "O(total sets)", "https://leetcode.com/problems/time-based-key-value-store/"),

C("Find Median from Data Stream (Live Latency Median)", "Hard", ["Amazon", "Google", "Microsoft", "Uber"], r'''
A monitoring service receives response latencies one at a time and has to report the running median at any point:
- `addNum(int num)`
- `double findMedian()`: the middle value, or the average of the two middle values when the count is even.

**Example**
```
addNum(1); addNum(2);
findMedian() -> 1.5
addNum(3);
findMedian() -> 2.0
```
**Constraints:** −10^5 ≤ num ≤ 10^5, up to 5·10^4 calls, and findMedian is only called on a non-empty stream.

**Follow-up:** what if 99% of the values fall in [0, 100]?''',
["Split the numbers into a lower half and an upper half.",
 "Use a max-heap for the lower half and a min-heap for the upper half. Rebalance so their sizes differ by at most 1."],
r'''
import java.util.*;

class MedianFinder {
    private final PriorityQueue<Integer> low = new PriorityQueue<>(Collections.reverseOrder()); // max-heap
    private final PriorityQueue<Integer> high = new PriorityQueue<>();                          // min-heap

    public void addNum(int num) {
        low.offer(num);
        high.offer(low.poll());            // move the largest of low to high
        if (high.size() > low.size()) {
            low.offer(high.poll());        // keep low.size() >= high.size()
        }
    }

    public double findMedian() {
        if (low.size() > high.size()) return low.peek();
        return (low.peek() + (long) high.peek()) / 2.0;
    }
}''',
'''The two heaps split the stream so every element in `low` is ≤ every element in `high`, and `low` holds at most one extra element. Each insertion routes through `low` and then `high`, which maintains the ordering invariant without any comparisons in our own code. A final rebalance fixes the sizes. The median is then at the top of `low` (odd count) or the average of the two tops (even count), which is O(1). The `(long)` cast avoids overflow. For the follow-up, when values fall in a small range, a **counting array/histogram** with 101 buckets plus overflow heaps gives near O(1) inserts. Production monitoring tools usually approximate percentiles with t-digest or HDRHistogram instead.''',
"addNum O(log n), findMedian O(1)", "O(n)", "https://leetcode.com/problems/find-median-from-data-stream/"),

C("Employee Analytics with Java Streams", "Easy", ["JP Morgan", "Goldman Sachs", "Oracle", "Walmart", "SAP"], r'''
You get a `List<Employee>` where `record Employee(String name, String dept, double salary, int age)`. Using **Java Streams only (no loops)**, write methods that:
1. Return the **highest-paid employee in each department**: `Map<String, Employee>`.
2. Return the **average salary per department**, with departments sorted by name: `Map<String, Double>`.
3. Return the **names of employees older than 30**, sorted by salary descending: `List<String>`.
4. Return the **second-highest distinct salary** overall: `Optional<Double>`.

**Example**
```
[Raj, Eng, 90000, 27], [Amit, Eng, 120000, 32], [Neha, HR, 60000, 35], [Sara, HR, 75000, 29]
1 -> {Eng=Amit, HR=Sara}
2 -> {Eng=105000.0, HR=67500.0}
3 -> [Amit, Neha]
4 -> Optional[90000.0]
```''',
["groupingBy(dept, collectingAndThen(maxBy(comparing(salary)), Optional::get)), or toMap with a BinaryOperator.maxBy merge.",
 "Pass TreeMap::new as the map factory to groupingBy to get sorted keys. Use distinct + sorted(reverseOrder) + skip(1) for the second-highest."],
r'''
import java.util.*;
import java.util.function.BinaryOperator;
import java.util.stream.Collectors;

record Employee(String name, String dept, double salary, int age) { }

class EmployeeAnalytics {

    static Map<String, Employee> topEarnerByDept(List<Employee> emps) {
        return emps.stream().collect(Collectors.toMap(
            Employee::dept,
            e -> e,
            BinaryOperator.maxBy(Comparator.comparingDouble(Employee::salary))));
    }

    static Map<String, Double> avgSalaryByDept(List<Employee> emps) {
        return emps.stream().collect(Collectors.groupingBy(
            Employee::dept, TreeMap::new, Collectors.averagingDouble(Employee::salary)));
    }

    static List<String> olderThan30BySalaryDesc(List<Employee> emps) {
        return emps.stream()
            .filter(e -> e.age() > 30)
            .sorted(Comparator.comparingDouble(Employee::salary).reversed())
            .map(Employee::name)
            .toList();
    }

    static Optional<Double> secondHighestSalary(List<Employee> emps) {
        return emps.stream()
            .map(Employee::salary)
            .distinct()
            .sorted(Comparator.reverseOrder())
            .skip(1)
            .findFirst();
    }

    public static void main(String[] args) {
        List<Employee> emps = List.of(
            new Employee("Raj", "Eng", 90000, 27), new Employee("Amit", "Eng", 120000, 32),
            new Employee("Neha", "HR", 60000, 35), new Employee("Sara", "HR", 75000, 29));
        topEarnerByDept(emps).forEach((d, e) -> System.out.println(d + "=" + e.name()));
        System.out.println(avgSalaryByDept(emps));          // {Eng=105000.0, HR=67500.0}
        System.out.println(olderThan30BySalaryDesc(emps));  // [Amit, Neha]
        System.out.println(secondHighestSalary(emps));      // Optional[90000.0]
    }
}''',
'''Questions like this come up constantly in Java backend interviews at banks and enterprise product companies. `toMap` with a `BinaryOperator.maxBy` merge function keeps the top earner per key without wrapping it in an Optional. The `groupingBy(..., maxBy)` version returns `Optional<Employee>` values that need unwrapping with `collectingAndThen`. Passing `TreeMap::new` as the map factory gives sorted keys. `Comparator.comparingDouble(...).reversed()` avoids subtraction-based comparators. `distinct().sorted(reverseOrder()).skip(1).findFirst()` returns an empty Optional when fewer than two distinct salaries exist, so there's no exception. `Stream.toList()` (Java 16+) returns an unmodifiable list. Be ready to explain lazy evaluation and when `parallelStream()` is a bad idea, such as small lists or blocking I/O.''',
"O(n log n)", "O(n)", None),
]

theory = [
T("How does Spring Boot auto-configuration work?", '''`@SpringBootApplication` combines `@Configuration`, `@ComponentScan` and `@EnableAutoConfiguration`. The last one imports every class listed in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` across all jars on the classpath. Before Boot 2.7 this list lived in `spring.factories`.

Each auto-configuration class is guarded by **conditions**:
- `@ConditionalOnClass(DataSource.class)`: apply only if the library is present.
- `@ConditionalOnMissingBean`: back off if you defined your own bean.
- `@ConditionalOnProperty`: toggle through configuration.

So adding `spring-boot-starter-data-jpa` brings in Hibernate and HikariCP, and the conditions match, which auto-creates a DataSource, an EntityManagerFactory and a TransactionManager using `spring.datasource.*` properties bound through `@ConfigurationProperties`.

To debug, run with `--debug` or use the `/actuator/conditions` endpoint to see which configurations matched. To exclude one, use `@SpringBootApplication(exclude = ...)`. You can write custom starters the same way.''', ["Walmart", "JP Morgan", "Oracle", "PhonePe"]),

T("What is the N+1 select problem and how do you solve it in Spring Data JPA?", '''It happens when you load N parent entities in one query and then a lazy association on each parent triggers its own query, giving **1 + N** round trips. It's easy to miss in development and very slow in production.

**Detect it:** set `spring.jpa.show-sql`, use Hibernate statistics, or use tools like p6spy and Hypersistence Optimizer. Tests can assert the query count.

**Fixes:**
1. **JOIN FETCH** in JPQL: `select o from Order o join fetch o.items where ...`.
2. **@EntityGraph(attributePaths = {"items"})** on repository methods.
3. **Batch fetching**: `@BatchSize(size = 50)` or `hibernate.default_batch_fetch_size`, which loads the collections with `IN (...)` queries.
4. **DTO projections** that select only the columns you need.

Watch out: fetch-joining collections together with pagination makes Hibernate paginate **in memory** (warning HHH000104). In that case, page the IDs first, then fetch-join. Don't fix N+1 by switching to EAGER.''', ["Myntra", "Paytm", "Walmart", "Intuit"]),

T("How does JWT-based authentication work in Spring Security?", '''1. **Login:** the client POSTs credentials. `AuthenticationManager` checks them through `UserDetailsService` and a `PasswordEncoder` (BCrypt). The server issues a **signed JWT** (HS256 or RS256) with claims such as sub, roles and exp, often alongside a long-lived refresh token.
2. **Requests:** the client sends `Authorization: Bearer <token>`.
3. **Filter:** a `OncePerRequestFilter`, or `oauth2ResourceServer().jwt()`, checks the signature and expiry, builds an `Authentication` with the user's authorities, and sets it in the `SecurityContextHolder`.
4. **Authorization:** URL rules in the `SecurityFilterChain` bean, or method-level `@PreAuthorize("hasRole('ADMIN')")`.

The session policy is **STATELESS** and CSRF is disabled when the token travels in a header.

Trade-offs: a JWT can't easily be revoked before it expires. Keep access tokens short-lived (5–15 minutes) and use refresh-token rotation or a denylist. Never put secrets in the payload, because it's only base64-encoded, not encrypted.''', ["Intuit", "PhonePe", "Salesforce", "Paytm"]),

T("How does Kafka guarantee ordering, and what happens during a consumer group rebalance?", '''**Ordering:** Kafka keeps order only **within a partition**. The producer picks a partition by hashing the message key, so all events for the same key, such as an orderId, go to one partition in order. To keep that order when retries happen, enable the idempotent producer (`max.in.flight.requests ≤ 5` is safe with idempotence).

**Consumer groups:** each partition is assigned to exactly one consumer in a group. Consumers record their progress by committing offsets to `__consumer_offsets`.

**Rebalance:** triggered when a consumer joins or leaves, misses heartbeats (`session.timeout.ms`), or exceeds `max.poll.interval.ms` because processing is slow. Partitions get reassigned. With eager rebalancing, everything stops. **Cooperative incremental** rebalancing (CooperativeStickyAssignor) moves only the affected partitions.

**Pitfalls:** messages being processed when a rebalance hits get processed again, so commit after processing and make consumers idempotent. Use static membership (`group.instance.id`) to avoid rebalances during rolling restarts.''', ["Walmart", "Swiggy", "PhonePe", "Uber"]),

T("How do microservices communicate, and how do you handle failures between them?", '''**Synchronous:** REST over HTTP (with RestClient, WebClient or OpenFeign) or gRPC. It's simple, but it couples the services in time: if the downstream service is down, the caller fails.

**Asynchronous:** events and messages through Kafka or RabbitMQ. Services are decoupled and can absorb load spikes, but the system becomes eventually consistent and is harder to trace.

**Handling failures:**
1. **Timeouts** on every remote call. Never wait indefinitely.
2. **Retries with exponential backoff and jitter**, only for idempotent operations.
3. A **circuit breaker** (Resilience4j) to fail fast while a dependency is unhealthy.
4. **Bulkheads**, meaning separate thread pools or connection pools per dependency.
5. **Fallbacks**, such as cached data or a degraded response.
6. **Dead-letter queues** for poison messages.
7. **Idempotency keys** so retries are safe.

**Observability:** distributed tracing (Micrometer Tracing/OpenTelemetry with a traceId), centralized logs and metrics, plus health checks for Kubernetes probes.''', ["Salesforce", "Walmart", "Swiggy", "Myntra"]),

T("What is the difference between Docker containers and VMs, and what are the key Kubernetes objects?", '''A **VM** virtualizes hardware. Each VM runs a full guest OS on a hypervisor, so it's heavy (GBs in size, boots in minutes) but strongly isolated. A **container** shares the host kernel and isolates processes using namespaces and cgroups. Containers are lightweight (MBs in size, start in milliseconds) and ship the app plus its dependencies as an **image** built from a Dockerfile in layers.

**Kubernetes core objects:**
- **Pod**: the smallest deployable unit, one or more containers sharing a network and volumes.
- **Deployment**: manages ReplicaSets of stateless pods and handles rolling updates and rollbacks.
- **Service**: a stable virtual IP or DNS name that load-balances across pods (ClusterIP, NodePort, LoadBalancer).
- **Ingress**: L7 HTTP routing into the cluster.
- **ConfigMap / Secret**: external configuration.
- **StatefulSet**: for stateful workloads.

For Spring Boot, add liveness and readiness probes and set resource limits.''', ["ServiceNow", "SAP", "Walmart", "Salesforce"]),
]

save(12, "Spring Boot + Microservices Deep Dive",
     "A backend deep dive covering JPA, transactions, security, Kafka and Docker/Kubernetes, with coding problems in the style of REST and stream processing.",
     mcqs, coding, theory)
