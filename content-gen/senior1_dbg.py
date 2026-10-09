from senior1_common import build, B, I, A

NOTES = [
("The Debugging Method: From Page to Guardrail", r"""
## Why this round exists
Many 2026 loops have an **execution / operations round**. You get a page, something like *"Checkout p99 went from 200 ms to 2 s at 14:05"*, and the interviewer plays your dashboards. Nobody expects you to guess the cause. They are grading whether you have a **method** that is fast, keeps customers safe and follows evidence. A junior jumps to a theory ("must be the DB"). A senior narrows the search with data, stops the bleeding early and leaves the system harder to break.

## The seven-step loop
```text
 1. CONFIRM SYMPTOM   what exactly? since when? who is affected? how bad?
        |
 2. GOLDEN SIGNALS    latency / traffic / errors / saturation, per service and per dependency
        |
 3. RECENT CHANGES    deploys, flags, config, migrations, infra, traffic mix, cron, certs
        |
 4. ISOLATE           split healthy vs unhealthy: host, AZ, version, endpoint, tenant, shard
        |
 5. MITIGATE          rollback, flag off, shed load, scale out, fail over (stop the bleeding)
        |
 6. VERIFY            same signal back to baseline? business metric OK? no new errors?
        |
 7. GUARDRAIL         root cause, test, alert, limit, runbook, postmortem
```

**1. Confirm the symptom.** Is it real or a monitoring glitch? All endpoints or one? All users or one region or app version? Pin the start time. A **sharp step** at 14:05 points to a change. A **slow ramp** points to a leak, data growth or a queue building up.

**2. Read the golden signals** (from the Google SRE book): latency (successes and failures tracked separately, because a fast 500 can hide a slow one), traffic, errors and saturation. For resources (CPU, pools, disks, locks) use Brendan Gregg's **USE** method: Utilization, Saturation, Errors. Always compare against the same time yesterday or last week.

**3. Ask "what changed?"** This is the most useful single question, because most incidents follow a change. Check the deploy history, the feature-flag audit log, config pushes, DB migrations, deploys of your dependencies, certificate rotations and marketing campaigns.

**4. Isolate.** Divide and conquer on dimensions. Only pods on v2.31 slow? Regression. Only one AZ? Infrastructure. Only one tenant? Data shape, such as a customer with 2 million orders. Every instance degrading at the same moment? A shared dependency. Traces show which span grew.

**5. Mitigate.** Customer impact matters more than root cause. Prefer **reversible** actions: rollback, flag off, scale out, shed non-critical traffic, fail over. If a change lines up with the start time, *roll back first and debug later*.

**6. Verify.** Watch the signal that paged you **and** a business metric (orders per minute). Recovered latency with zero orders is not a recovery.

**7. Guardrail.** Once the bleeding stops, find the root cause and ask *why we didn't catch it earlier*. The answer becomes a test, a canary metric, an alert, a limit (timeout, pool size, queue bound) or a runbook.

## A worked timeline
| Time | Evidence / action |
|---|---|
| 14:05 | v2.31 rolled out |
| 14:09 | Alert: checkout p99 2.1 s (baseline 200 ms), errors 0.4% -> 3% (timeouts) |
| 14:10 | Traffic flat, DB CPU normal, **hikaricp_connections_pending 0 -> 150** |
| 14:11 | Split by version: only v2.31 pods affected |
| 14:12 | Decision: rollback (3 min) instead of debugging forward |
| 14:17 | p99 back to 210 ms, orders/min back to baseline |
| Later | Root cause: new fraud-check HTTP call inside `@Transactional` held DB connections ~800 ms each |
| Guardrails | Move remote call out of the transaction, alert on pending connections, automated canary analysis on p99 |

## What makes you sound senior
- State **hypotheses with tests**: "If it's the pool, pending connections will be above zero and thread dumps will show threads parked in `HikariPool.getConnection`."
- Keep **mitigation** separate from **fix**.
- Ask about **blast radius** before risky actions. Restarting the DB primary at peak can make things worse.
- **Preserve evidence**: grab a thread or heap dump from one pod before restarting the rest.
- Change **one thing at a time**, and **communicate** with short, timestamped status updates.

## Anti-patterns interviewers notice
Restarting everything at once and losing evidence. Spending an hour debugging forward when a rollback takes three minutes. Saying "I'd add more logs" as the first step. Increasing the pool size or heap without knowing why. Declaring victory without checking.
"""),

("Observability: Logs, Metrics, Traces and Correlation IDs", r"""
## Three signals, three questions
| Signal | Answers | Cost | Typical tools |
|---|---|---|---|
| **Metrics** | Is something wrong, and how much? | Cheap: numbers aggregated over time | Micrometer, Prometheus, Grafana |
| **Logs** | What exactly happened to *this* request? | Expensive at volume | Logback JSON, ELK / Loki |
| **Traces** | Where did the time go across services? | Sampled | OpenTelemetry, Jaeger, Tempo, Zipkin |

The flow during an incident: a **metric** alerts you, a **trace** shows which hop is slow, and **logs** for that trace ID tell you why.

## Structured logging
```java
// Bad: string concatenation, unsearchable, built even when the level is off
log.info("Order " + orderId + " failed for user " + userId + ": " + e);
// Good: parameterised, with the exception as the last argument so the stack trace is kept
log.warn("order payment failed orderId={} provider={} attempt={}", orderId, provider, attempt, e);
```
Emit **JSON** so the log platform can index fields. Spring Boot 3.4+ supports this natively: `logging.structured.format.console=ecs` (or `logstash`, `gelf`). One line looks like:
```text
{"@timestamp":"2026-10-09T14:05:31.120Z","log.level":"WARN","service.name":"order-service",
 "trace.id":"4bf92f3577b34da6a3ce929d0e0e4736","message":"order payment failed","orderId":"O-981",...}
```
Rules: log at **boundaries** (request in/out, external calls, state transitions, retries). Log **IDs, not PII** (no card numbers, OTPs or tokens). Levels need clear meanings: ERROR means someone should look, WARN means degraded but handled. Don't log inside tight loops.

## Correlation IDs with MDC
```java
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class CorrelationIdFilter extends OncePerRequestFilter {
    static final String HEADER = "X-Correlation-Id";

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String id = req.getHeader(HEADER);
        if (id == null || id.isBlank() || id.length() > 64) {   // never trust unbounded input
            id = UUID.randomUUID().toString();
        }
        MDC.put("correlationId", id);
        res.setHeader(HEADER, id);
        try {
            chain.doFilter(req, res);
        } finally {
            MDC.remove("correlationId");   // pooled threads: always clean up
        }
    }
}
```
Pitfalls: MDC is a `ThreadLocal`, so the value is **lost on `@Async`, `CompletableFuture` and executor hops** unless you propagate it (a `TaskDecorator`, or Micrometer's context-propagation library). Forward the header on outgoing HTTP and Kafka calls. With **Micrometer Tracing** on the classpath, `traceId` and `spanId` go into the MDC automatically, so the trace ID usually *is* the correlation ID.

## Metrics: Micrometer -> Prometheus -> Grafana
Actuator plus `micrometer-registry-prometheus` exposes `/actuator/prometheus`. You get useful metrics for free: `http_server_requests_seconds` (by uri, method, status), `jvm_memory_used_bytes`, `jvm_gc_pause_seconds`, `hikaricp_connections_active` and `_pending`, `tomcat_threads_busy_threads`, `executor_queued_tasks`.
```java
Timer.builder("payment.gateway.call")
     .tag("provider", provider)            // low-cardinality values only
     .publishPercentileHistogram()
     .register(registry)
     .record(() -> gateway.charge(request));
```
p99 per endpoint in PromQL:
```text
histogram_quantile(0.99, sum by (le, uri) (rate(http_server_requests_seconds_bucket[5m])))
```
**Cardinality trap:** never tag with `userId`, `orderId` or a raw URL. Each unique value creates a new time series and can take down Prometheus. Use templated URIs (`/orders/{id}`).

## Distributed tracing with OpenTelemetry
A trace is a tree of **spans**. Context travels in the W3C `traceparent` header (`00-<traceId>-<spanId>-<flags>`). In Spring Boot 3 you either use Micrometer Tracing with the OTel bridge and an OTLP exporter, or attach the OTel Java agent for zero-code instrumentation.
```text
traceId 4bf9...
[api-gateway ] |=================================| 1900 ms
  [order-svc ]  |===============================|  1850 ms
    [SELECT  ]   |=|                                  40 ms
    [fraud-svc]     |==========================|     1700 ms   <-- the culprit
```
Sampling: **head-based** (keep 1-10%, decided at the start) is cheap. **Tail-based** (decided after the trace completes) keeps all errors and slow traces. **Exemplars** attach trace IDs to histogram buckets, so you can click from a latency spike to a real slow trace.

## Day-one checklist for a new service
RED metrics (rate, errors, duration) per endpoint. Client metrics per downstream dependency. Saturation gauges for pools and queues. JSON logs with trace IDs. Liveness and readiness probes. Dashboards plus SLO alerts. A `build_info{version=...}` metric so you can split everything by version.
"""),

("SLIs, SLOs, Error Budgets and Alerting", r"""
## Vocabulary
- **SLI (indicator):** a measured ratio, *good events / valid events*. Example: the share of `POST /checkout` requests that return non-5xx **in under 500 ms**, measured at the load balancer.
- **SLO (objective):** a target for that SLI over a window. Example: **99.9% over a rolling 28 days**.
- **SLA (agreement):** a contractual promise with penalties, deliberately looser than the SLO.
- **Error budget:** `1 - SLO`. At 99.9% on 10M requests a month you may fail **10,000** requests. In time, it is about **43 minutes** per 30 days.

| SLO | Allowed bad time per 30 days |
|---|---|
| 99% | 7.2 hours |
| 99.9% | 43.2 minutes |
| 99.95% | 21.6 minutes |
| 99.99% | 4.3 minutes |

## Choosing good SLIs
- **Measure close to the user**: gateway or load balancer, not inside the JVM, which misses requests that never reached it.
- Use **request-based** ratios: availability (non-5xx / all) and latency as a threshold ("% under 300 ms"), not an average.
- Pipelines: **freshness** ("99% of events processed within 5 minutes"). Payments: **correctness** (reconciliation mismatches).
- Not every endpoint needs its own SLO. Cover the critical user journeys: login, search, add to cart, pay.

A compact SLO spec:
```text
Service: order-api            Owner: checkout-team         Window: 28 days rolling
SLI availability: count(status != 5xx) / count(all) at the gateway, POST /orders     SLO 99.9%
SLI latency:      count(duration < 400ms) / count(all), POST /orders                 SLO 99%
Exclusions: synthetic traffic, 4xx (client errors), planned maintenance with notice
```

## Error budget policy: the real point
The budget turns the "reliability vs features" argument into data. **Budget left?** Ship features and run experiments. **Budget exhausted?** Freeze risky launches and put the team on reliability work until it recovers. Without an agreed policy an SLO is only a dashboard.

Dependencies compound: if checkout synchronously needs three services at 99.9% each, the best you can expect is about 0.999^3, roughly **99.7%**. That's why you add timeouts, fallbacks and async paths.

## Alerting on SLOs with burn rates
**Burn rate** is how fast you spend the budget relative to spending it evenly. A burn rate of 1 uses exactly the whole budget by the end of the window. A burn rate of 14.4 sustained for one hour uses **2%** of a 30-day budget.

The Google SRE Workbook recommends **multiwindow, multi-burn-rate** alerts:
| Severity | Long window | Short window | Burn rate | Budget used |
|---|---|---|---|---|
| Page | 1 h | 5 min | 14.4 | 2% |
| Page | 6 h | 30 min | 6 | 5% |
| Ticket | 3 days | 6 h | 1 | 10% |

Both windows must be over the threshold. The long window shows the burn is significant. The short window shows it's *still happening*, so the alert clears quickly after recovery.
```text
# 99.9% SLO -> budget 0.001; fast-burn page condition
(
  sum(rate(http_server_requests_seconds_count{uri="/orders",status=~"5.."}[1h]))
  / sum(rate(http_server_requests_seconds_count{uri="/orders"}[1h]))
) > 14.4 * 0.001
and
(
  sum(rate(http_server_requests_seconds_count{uri="/orders",status=~"5.."}[5m]))
  / sum(rate(http_server_requests_seconds_count{uri="/orders"}[5m]))
) > 14.4 * 0.001
```
Why not simply "error rate > 1% for 5 minutes"? It pages on short blips that barely touch the budget, and it never fires on a slow 0.5% burn that quietly uses the whole month's budget.

## Page on symptoms, not causes
**Page** when users are hurting (SLO burn, checkout failing). **Ticket or dashboard** for causes such as CPU at 85%, one pod restarting or disk at 70%. The exception is a cause that will *certainly* become an outage soon: disk at 95% and filling, a certificate expiring in 7 days, or replication lag growing without bound.

## Alert hygiene
Every page must be **actionable**, **owned** and **linked to a runbook**. Review pages every week: delete or downgrade any alert that fired without needing action. Alert fatigue is how real incidents get missed.

## How to answer "Define SLOs for a payments API"
Start with the user journey (authorize a payment). Pick an availability SLI at the gateway, a latency threshold SLI and a correctness check through daily reconciliation. Set a tighter target for `authorize` than for `payment-history`. Mention dependency math, the error budget policy and burn-rate alerts. That covers what interviewers listen for.
"""),

("JVM Forensics: Thread Dumps, Heap Dumps, JFR and async-profiler", r"""
## The toolbox (memorise these)
Inside a container: `kubectl exec -it <pod> -- jcmd` lists JVMs (the PID is often 1).
```text
jcmd <pid> Thread.print -l > threads.txt          # thread dump, with lock info
jcmd <pid> GC.heap_info                           # heap regions and usage
jcmd <pid> GC.class_histogram | head -30          # quick "what is filling the heap"
jcmd <pid> GC.heap_dump /tmp/heap.hprof           # full heap dump (pauses the JVM!)
jcmd <pid> JFR.start name=inc duration=120s settings=profile filename=/tmp/inc.jfr
jcmd <pid> VM.native_memory summary               # needs -XX:NativeMemoryTracking=summary
jstack <pid>  |  kill -3 <pid>                    # older ways to get a thread dump
```
Production JVM flags that pay for themselves:
```text
-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/dumps
-Xlog:gc*:file=/logs/gc.log:time,uptime:filecount=5,filesize=20M
-XX:StartFlightRecording=maxage=1h,disk=true      # continuous JFR, dump it when needed
```

## Reading a thread dump
```text
"http-nio-8080-exec-37" #112 daemon prio=5 tid=0x00007f... nid=0x7a waiting on condition
   java.lang.Thread.State: TIMED_WAITING (parking)
        at jdk.internal.misc.Unsafe.park(Native Method)
        at java.util.concurrent.locks.LockSupport.parkNanos(LockSupport.java:269)
        at com.zaxxer.hikari.util.ConcurrentBag.borrow(ConcurrentBag.java:151)
        at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:181)
        ...
        at com.shop.order.OrderService.placeOrder(OrderService.java:58)
```
**States:** `RUNNABLE` means on CPU *or* blocked in native I/O, so a thread stuck in a socket read still shows RUNNABLE. `BLOCKED` means waiting to enter a `synchronized` monitor. `WAITING` and `TIMED_WAITING` mean parked, sleeping or in `Object.wait`.

| Pattern in the dump | Likely meaning |
|---|---|
| 180 of 200 Tomcat threads in `HikariPool.getConnection` | Pool exhaustion: connections held too long or leaked |
| Many threads `BLOCKED` "waiting to lock <0x..>", all on one owner | Lock contention (synchronized hot path, sync log appender) |
| Many `RUNNABLE` in `SocketInputStream.read` / `NioSocketImpl.read` | Slow downstream with no read timeout |
| "Found one Java-level deadlock" at the bottom | Two threads taking locks in opposite order |
| Same `RUNNABLE` frames (regex, JSON, HashMap) in every dump | CPU hotspot or infinite loop |
| Thread count keeps growing (`pool-731-thread-1`) | An executor created per request: thread leak |

**Technique:** take **three dumps 5-10 s apart**. Frames that persist across dumps tell the story. Group identical stacks (`grep -A3 'State' threads.txt | sort | uniq -c | sort -rn`, or a viewer like fastThread). To map a CPU-hungry thread: `top -H -p <pid>` gives the thread ID; convert it to hex and match `nid=0x...` in the dump.

## Heap dumps and leak hunting
Open the `.hprof` in **Eclipse MAT**: run the *Leak Suspects* report, then the **Dominator Tree** sorted by **retained heap** (memory freed if that object were collected), then *Path to GC Roots* (excluding weak references) to see *who keeps it alive*.

Classic leaks:
- A `static Map` used as a cache with no size limit or eviction.
- A `ThreadLocal` never `remove()`d on pooled threads.
- Listeners or callbacks registered but never unregistered.
- An unbounded `LinkedBlockingQueue` behind an executor that can't keep up.
- A batch job keeping 2 million entities in one Hibernate persistence context (no `flush()`/`clear()`).

**Caution:** a heap dump pauses the JVM for seconds and the file is about the size of the used heap. Take it from a pod already **removed from the load balancer**, and treat it as sensitive data (it holds PII and secrets).

## JFR: the always-on flight recorder
Built into the JDK and free since 11. Overhead is roughly 1-2% with the default settings. It records CPU samples, allocation hotspots, GC pauses, lock contention (`jdk.JavaMonitorEnter`), socket and file I/O, thrown exceptions and virtual-thread pinning. Analyse in **JDK Mission Control**, or on the command line:
```text
jfr summary inc.jfr
jfr print --events jdk.GCPhasePause inc.jfr | head
jcmd <pid> JFR.dump filename=/tmp/last-hour.jfr             # from a continuous recording
```

## async-profiler and flame graphs
```text
asprof -e cpu   -d 30 -f cpu.html   <pid>     # where CPU is burned
asprof -e alloc -d 30 -f alloc.html <pid>     # who allocates (GC pressure)
asprof -e wall  -d 30 -f wall.html  <pid>     # wall clock: includes waiting threads
asprof -e lock  -d 30 -f lock.html  <pid>     # contended locks
```
Reading a flame graph: the **x-axis is the share of samples, not time order**. The y-axis is stack depth. Look for **wide plateaus near the top**: those frames are on-CPU themselves. async-profiler avoids the *safepoint bias* of older JVMTI samplers, so it reports where time is really spent. Use **wall mode** for "slow but the CPU is idle". It shows threads waiting on locks, pools and sockets.

## Which tool when
| Symptom | First tool |
|---|---|
| Hung / slow, CPU low | Thread dumps (x3), wall-clock profile |
| CPU high | `top -H` + thread dump, CPU flame graph |
| Memory climbing / OOM | GC log, class histogram, heap dump in MAT |
| GC pauses | GC log, JFR GC events, allocation profile |
| Intermittent latency spikes | Continuous JFR, dumped after the spike |
"""),

("Incident Playbook I: Deploy Regressions, Leaks, Pools and Thread Pools", r"""
Each scenario follows **signature -> confirm -> mitigate -> fix -> guardrail**. Learn the signatures. They let you recognise a problem in the first two minutes.

## 1. Regression after a deploy
**Signature:** a step change lined up with the deploy time, affecting only new-version pods during a canary or rolling deploy.
**Confirm:** split latency and errors by the `version` label, and compare traces before and after.
**Mitigate:** roll back or turn the flag off. Don't debug forward while customers are hurting.
**Usual root causes:** a new N+1 query; a new query with no index; a remote call added to a hot path; DEBUG logging left on; a cache key format change that drops the hit ratio to 0%; a changed timeout or pool setting; a heavier serializer config.
**Guardrails:** canary with automated analysis (compare canary p99 and error rate with the baseline), performance tests for the hottest endpoints, migration review.

## 2. Memory leak and OutOfMemoryError
| Error | Meaning |
|---|---|
| `OutOfMemoryError: Java heap space` | Live data exceeds `-Xmx` (a leak, or a working set that is really too big) |
| `GC overhead limit exceeded` | Parallel GC spending >98% of time collecting and recovering <2% |
| `Metaspace` | Class-loader leak (dynamic proxies, script engines, hot redeploys) |
| `unable to create native thread` | Thread leak, or ulimit / container PID limit reached |
| Pod `OOMKilled`, exit code 137, **no** Java OOM | Total process memory > container limit: heap + metaspace + thread stacks + direct buffers + code cache |

```text
old gen used after each GC
  healthy:  ___/\___/\___/\___/\___/\___      (flat floor)
  leak:     __/\__/\_/\_/\/\/\/\/\/\/|  OOM   (floor rises, GCs get closer together)
```
**Signature of a heap leak:** the *after-GC* floor keeps rising, GC frequency rises, latency rises, then OOM, often hours or days after a deploy.
**Mitigate:** a rolling restart buys time and is a valid mitigation. **Capture a heap dump first** from one instance.
**Fix:** MAT dominator tree, then path to GC roots (see the JVM forensics chapter).
**Container OOMKilled:** use `-XX:MaxRAMPercentage=70-75` rather than a hard-coded `-Xmx` equal to the limit, leave headroom for non-heap memory, and use Native Memory Tracking to find off-heap growth.

## 3. HikariCP connection pool exhaustion
**Signature:**
```text
HikariPool-1 - Connection is not available, request timed out after 30000ms
  (total=10, active=10, idle=0, waiting=87)
```
In metrics: `hikaricp_connections_pending > 0` and `active == max`. In thread dumps: request threads parked in `HikariPool.getConnection`.

**Causes, most common first:**
1. **Connections held across slow work**: a remote call inside `@Transactional`.
2. **Slow queries**: a DB problem, so every connection stays busy longer.
3. **Open Session in View** (`spring.jpa.open-in-view=true`, the default) holds the connection for the whole request.
4. A **real leak**: manual JDBC without try-with-resources.
5. A genuine traffic spike.

```java
@Transactional
public void placeOrder(OrderRequest r) {
    Order o = orderRepo.save(Order.pending(r));
    PaymentResult p = paymentClient.charge(r);   // 800 ms HTTP call while holding a DB connection
    o.markPaid(p.id());
}
```
**Fix:** keep transactions short. Save the order as PENDING (tx 1), call the payment provider **outside** any transaction with an idempotency key, then mark it PAID (tx 2), or use an outbox/saga. Set `open-in-view=false`. Turn on `leakDetectionThreshold` (for example 20000 ms) temporarily to log the stack trace of whoever holds a connection too long.

**Don't just raise the pool size.** 30 pods x 50 connections = 1,500 connections, far beyond what MySQL can serve well (and above its default `max_connections` of 151). A bigger pool moves the queue into the database, where it hurts everyone.

## 4. Thread pool saturation
**Signature:** latency rises while **CPU is low**. `tomcat_threads_busy_threads` sits at the max (200 by default) and requests queue in the accept backlog. Or an `@Async` executor's queue grows without bound.
**Typical cause:** blocking calls to a slow dependency **with no timeout**. Every thread ends up waiting on the same sick service, so healthy endpoints starve too.
```java
// Resilience basics for an outbound client
var factory = new SimpleClientHttpRequestFactory();
factory.setConnectTimeout(Duration.ofMillis(500));
factory.setReadTimeout(Duration.ofSeconds(2));
RestClient client = RestClient.builder().requestFactory(factory).baseUrl(fraudUrl).build();
```
**Mitigate:** shed load (return 503 fast), scale out, turn off the non-critical feature that calls the sick dependency.
**Guardrails:** timeouts on every remote call; **bulkheads** (a separate, bounded pool or semaphore per dependency so one slow service can't take every thread); circuit breakers; **bounded queues with a rejection policy** instead of `Executors.newFixedThreadPool` and its unbounded queue; dashboards for `executor_queued_tasks` and `executor_active_threads`.

## Signatures at a glance
| You see | Think |
|---|---|
| Step change at deploy time | Regression: roll back |
| After-GC floor rising | Heap leak |
| Pending connections > 0 | Pool exhaustion: who holds connections? |
| Busy threads = max, CPU idle | Blocking on a dependency: timeouts, bulkheads |
"""),

("Incident Playbook II: Caches, Databases, Bad Hosts, Retry Storms, Disk and Certs", r"""
## 5. Cache stampede and cold cache
**Story:** Redis restarts, or a deploy changes the cache key format. The hit ratio drops from 95% to 0% and DB queries jump 20x. The DB saturates, requests time out, and **the cache can never refill because the DB is too slow to answer**. This self-sustaining state is a *metastable failure*: removing the trigger doesn't bring the system back.
```text
cache miss storm -> DB overloaded -> slow responses -> client retries -> more DB load
        ^                                                                    |
        +---------------------- cache stays empty <--------------------------+
```
**Mitigate:** shed or rate-limit traffic at the edge so the DB can breathe; warm the top N keys; serve stale values if you have them; add read replicas.
**Prevent:** single-flight per key (only one loader per key, others wait), **TTL jitter** so keys don't expire together, soft TTL with background refresh, warm-up before a node takes traffic, and **load tests with an empty cache**.

## 6. DB lock contention and slow queries
**Signature:** DB `Threads_running` high, app errors `Lock wait timeout exceeded; try restarting transaction` (`innodb_lock_wait_timeout` defaults to 50 s), deadlock errors, or a migration stuck on `Waiting for table metadata lock`.
```sql
SHOW FULL PROCESSLIST;                                   -- long runners, lock waits
SELECT trx_id, trx_started, trx_mysql_thread_id, trx_query
FROM information_schema.innodb_trx ORDER BY trx_started; -- oldest open transactions
SELECT * FROM sys.innodb_lock_waits\G                    -- who blocks whom (MySQL 8)
SHOW ENGINE INNODB STATUS\G                              -- LATEST DETECTED DEADLOCK section
```
**Usual causes:** a long-open transaction (often an app that called an external API mid-transaction); a batch `UPDATE` with no usable index that locks huge ranges; a **hot row** such as a shared counter; an `ALTER TABLE` queued behind a long transaction, which then blocks every new query on that table.
**Mitigate:** `KILL <thread_id>` the blocker, pause the batch job, revert the migration.
**Fix:** index the predicate, chunk batch updates (1,000 rows per transaction), shorten transactions, and run schema changes with online tools during low traffic.

## 7. One bad host or shard
**Signature:** the aggregate error rate is 5%, but split by instance one pod is at 100% errors (or one shard is at 100% CPU).
**Causes:** a bad node (disk, noisy neighbour), stale config or DNS, a pod that never warmed up, clock skew, a **hot shard** (a celebrity tenant or a sale on one seller).
**Mitigate:** take the host out of the load balancer, cordon the node, restart. For a hot shard, throttle that tenant or move it.
**Lesson:** always break metrics down by **host, AZ, version, endpoint and shard**. Averages hide outliers.

## 8. Retry storm
A downstream service slows down. Each layer retries 3 times. With 5 layers the bottom service sees up to **3^5 = 243x** load and can't recover.
```text
client x3 -> gateway x3 -> order x3 -> payment x3 -> bank-adapter x3   => 243 attempts per user click
```
**Mitigate:** disable retries through config or a flag, open circuit breakers, shed load.
**Prevent:** retry at **one layer** only; exponential backoff **with jitter**; a **retry budget** (a token bucket that caps retries at about 10% of requests); circuit breakers; retry only idempotent operations or ones carrying idempotency keys; honour `Retry-After`.

## 9. Disk full
**Signature:** `No space left on device`; MySQL stops accepting writes; logging blocks and the app hangs.
**Culprits:** logs with no rotation, forgotten heap dumps, temp files, MySQL binlogs, Kafka retention.
```text
df -h                                   # which filesystem
du -xh /var --max-depth=2 | sort -h | tail
lsof +L1                                # deleted files still held open (space not freed!)
```
**Prevent:** log rotation and retention, purge binlogs by policy, alerts at 80% and 90%, plus a "fills within 4 hours" alert using `predict_linear` on the disk metric.

## 10. Certificate expiry
**Signature:** at an exact time, 100% of calls to one dependency fail with `PKIX path building failed`, `certificate_expired` or a handshake failure.
**Mitigate:** renew or rotate the certificate, or roll the truststore. **Never** "fix" it by turning off TLS verification.
**Prevent:** automated renewal (ACME / cert-manager), expiry alerts at 30/14/7 days, an inventory of every certificate and Java truststore, including client mTLS certificates and partner CAs.

## The pattern behind all ten
```text
symptom  ->  saturated resource  ->  why is it saturated?  ->  what changed?
            (DB, pool, threads,      (more work, slower work,   (deploy, data,
             cache, disk, CPU)        held longer, lost cache)   traffic, time)
```
"""),

("Incident Response and Blameless Postmortems", r"""
## Roles during an incident
| Role | Does | Does NOT |
|---|---|---|
| **Incident Commander (IC)** | Coordinates, assigns work, makes the call (rollback? failover?), sets the update cadence | Debug with their own hands |
| **Ops / SME leads** | Investigate and run the mitigations they're assigned | Run untracked changes |
| **Communications lead** | Status page, stakeholder and support updates | Speculate about the root cause publicly |
| **Scribe** | Keeps a timestamped timeline of findings and actions | |

In a small team one person may hold several roles, but say explicitly who the IC is. The most common failure is five engineers changing things in parallel with nobody coordinating.

## Severity levels (a typical scheme)
- **SEV1:** major customer-facing outage, payments failing, data loss or a security breach. All hands, exec updates every 30 minutes.
- **SEV2:** significant degradation for a subset (one region, one feature).
- **SEV3:** minor or internal impact. Fix in working hours.

Declare early and downgrade later. Under-declaring costs more than over-declaring.

## Flow and communication
```text
detect -> triage (declare, severity, IC) -> mitigate -> resolve -> postmortem -> action items
```
A good status update is short and complete:
```text
[14:30] SEV2 - Checkout errors
Impact: ~12% of checkout attempts failing (South region) since 14:05.
Current: rolled back order-service v2.31 at 14:14; error rate falling (3% -> 0.6%).
Next: confirming recovery, checking payment reconciliation. Next update 15:00.
```

## The postmortem document
Write one when the agreed triggers fire. The Google SRE book's examples: user-visible impact above a threshold, *any* data loss, on-call intervention (rollback, rerouting), resolution time above a threshold, or a monitoring failure (a human found the problem before the alerts did).

Template:
1. **Summary**: two or three sentences.
2. **Impact**: users affected, duration, failed orders or revenue, SLO budget used.
3. **Timeline** (UTC): trigger, detection, key decisions, mitigation, resolution.
4. **Root cause and contributing factors**: usually several.
5. **What went well / what went poorly / where we got lucky.**
6. **Action items**: each with an **owner, due date and priority**, grouped into *prevent*, *detect* and *mitigate*.

## Blameless means systems, not people
Assume everyone acted reasonably with the information they had. Write "the pipeline allowed a migration to run without review", not "Ravi ran a bad migration". As the SRE book says, you can't fix people, but you can fix systems and processes. Blame teaches people to hide problems, which makes the next incident worse.

**5 Whys, used carefully:**
```text
Why did checkout fail?          DB CPU hit 100%.
Why?                            Cache hit ratio fell to 0% and every read went to the DB.
Why?                            Redis restarted during maintenance and came back empty.
Why did that overload the DB?   No request coalescing and no warm-up; all keys missed together.
Why wasn't it caught?           We never load-tested with a cold cache.
```
Real incidents rarely have **one** root cause. List the contributing factors: maintenance timing, missing alert, no load shedding.

## Good vs bad action items
| Bad | Good |
|---|---|
| "Be more careful with deploys" | "Add automated canary analysis on p99 and 5xx for order-service (owner Raj, due 20 Oct, P1)" |
| "Improve monitoring" | "Alert when hikaricp_connections_pending > 0 for 2 min, with a runbook link (owner Priya, due 15 Oct)" |
| "Fix the cache" | "Add single-flight loading for product cache + TTL jitter of +/-10%; load test with flushed cache" |

Track action items to completion. An unfinished postmortem action item is a known future incident.

## Telling your incident story in an interview
Behavioural rounds almost always ask for one. Use **context -> detection -> your actions and decisions -> result in numbers -> what changed afterwards**. Coming from a service company, you can still tell strong stories: a production support ticket you drove to root cause, a slow report or batch job you fixed, a UAT outage, a bad release you rolled back. Show the decision points: why you rolled back instead of hot-fixing, how you communicated, what guardrail you added. Interviewers want to see the **guardrail**: it shows ownership beyond "I fixed the bug".
"""),

("Mock Round: Debugging Out Loud", r"""
This is a condensed mock of a 2026-style execution round. Read it out loud once. The aim is to make the method a habit.

**Interviewer:** You're on call for `order-service` (Spring Boot, MySQL, Redis, Kafka, 12 pods). At 19:10 alerts fire: 5xx at 8%, p99 at 4 s. Go.

**Candidate:** First I'll confirm scope and impact. Is it every endpoint or just some? Did the business metric, orders per minute, drop? I'll also check whether the client-side or gateway metrics agree, so I know it isn't a monitoring artifact. Then I'll look at the golden signals for order-service and its dependencies, and ask what changed around 19:05.

**Interviewer:** All write endpoints, reads look fine. Orders per minute down 30%. No deploy today.

**Candidate:** Writes only narrows it: DB primary, Kafka producer, or the payment dependency. No deploy, so I'll check other changes: feature flags, config pushes, DB migrations, cron jobs starting at 19:00, a marketing push, and deploys by teams we depend on. Meanwhile I'll split the errors by exception type.

**Interviewer:** Errors are mostly `CannotCreateTransactionException: Connection is not available, request timed out after 30000ms`.

**Candidate:** That's HikariCP exhaustion. Either connections are held longer or queries got slower. I'll check `hikaricp_connections_active`, `_pending` and `_usage_seconds`, and on the DB: CPU, `Threads_running`, lock waits and the slow-query log.

**Interviewer:** Pending 100+ on all pods. DB CPU 35%, normal. But `innodb_row_lock_time` is spiking.

**Candidate:** Normal CPU with row lock waits points to **lock contention**, not load. Something holds row locks that our writes need. I'll run `SELECT * FROM sys.innodb_lock_waits` and look at `information_schema.innodb_trx` ordered by `trx_started` to find the oldest transaction and what it's blocking.

**Interviewer:** There's a transaction open 9 minutes from host `reporting-batch-1`, running `UPDATE orders SET archived=1 WHERE created_at < ...`.

**Candidate:** That matches: a batch job that started at 19:00 is updating a big range of `orders` in one transaction. If `created_at` isn't indexed it scans and locks far more rows. **Mitigation:** confirm with the owning team, or the IC if I can't reach them in a couple of minutes, then stop the job and `KILL` that connection. The rollback of a 9-minute transaction can itself take a while, so I'll watch it. I'll post an update in the incident channel before acting.

**Interviewer:** You kill it. Rollback takes 3 minutes, then pending connections drop to 0 and errors stop.

**Candidate:** I'll verify that p99, the 5xx rate *and* orders per minute are back to baseline. Then I'll check for side effects: were orders lost or stuck as PENDING during the window? Did clients retry and create duplicates? If idempotency keys are in place, they protect us there. I'll also check the Kafka lag for order events.

**Interviewer:** What follow-ups would you file?

**Candidate:**
1. **Prevent:** rewrite the archiver to work in **chunks** (for example 1,000 rows by primary key per transaction, with a short sleep), make sure `created_at` is indexed, and schedule it off-peak. Move reporting reads to a **replica**.
2. **Detect:** alert on the age of the oldest transaction (over 60 s) and on Hikari pending connections. Each would have paged us before customers noticed.
3. **Mitigate faster:** set a per-session `innodb_lock_wait_timeout` of a few seconds for OLTP paths so requests fail fast instead of holding threads for 50 s. Add a runbook entry "how to find and kill a blocking transaction".
4. **Process:** batch jobs that touch OLTP tables get a review checklist. Then a blameless postmortem.

## Why this answer scores well
| Rubric item | What the candidate did |
|---|---|
| Structured method | Scope -> signals -> changes -> isolate -> mitigate -> verify -> guardrail |
| Hypothesis-driven | Each data request had a reason ("writes only narrows it to...") |
| Correct signal reading | Normal CPU + lock waits = contention, not load |
| Safe mitigation | Checked blast radius, communicated, knew rollback takes time |
| Thorough verification | Business metric, data consistency, duplicates, lag |
| Systemic follow-ups | Prevent / detect / mitigate, with specific numbers |

## Common twists to rehearse
- "Rolling back didn't help." The change was elsewhere (data, traffic, a dependency) or the rollback didn't fully happen. Check that pods are really on the old version.
- "Only one pod." A bad host: drain it, keep it aside for forensics.
- "It recovers by itself every 20 minutes." A cache TTL, cron, GC cycle or autoscaler oscillation.
- "Errors are zero but customers complain." Look for implicit errors: a 200 with an empty body, a client-side failure, or a monitoring blind spot.
"""),
]

QA = [
("Your API p99 jumped from 200 ms to 2 s right after a deploy. Walk me through it.", r"""
**1. Confirm and scope:** which endpoints, all users or a segment, when exactly it started, and whether errors rose too. A step that lines up with the deploy is strong evidence.

**2. Mitigate first:** if the timing matches and a rollback is cheap, **roll back (or flag off) now** and debug from data afterwards. Customer impact beats curiosity.

**3. Confirm the regression:** split latency by `version` label (canary vs old pods). Compare traces before and after to see which span grew.

**4. Usual suspects in the diff:**
- A new query with no index, or an N+1 (check query count per request, slow log).
- A remote call added to a hot path or inside `@Transactional`, so pool waits show up (`hikaricp_connections_pending`).
- A cache key change that dropped the hit ratio to zero.
- Changed timeout, pool or serializer config; DEBUG logging left on.

**5. Verify** p99, the error rate and a business metric after the rollback.

**6. Guardrail:** a regression test or perf test for that endpoint, automated canary analysis comparing canary p99 against baseline, and an alert on the saturation metric that moved.
""", I, ["method", "deploy-regression", "latency"], True),

("What are the four golden signals, and how do they relate to the RED and USE methods?", r"""
**Golden signals** (Google SRE book), for any user-facing service:
- **Latency**: time to serve requests. Track **successful and failed requests separately**, because fast errors can make average latency look better.
- **Traffic**: demand, such as requests/sec or messages/sec.
- **Errors**: rate of failures. These can be explicit (5xx), implicit (200 with wrong content) or by policy (slower than the SLO).
- **Saturation**: how "full" the most constrained resource is (pool, threads, CPU, queue depth). Often it predicts trouble before errors appear.

**RED** (Rate, Errors, Duration) is the golden signals minus saturation, applied **per endpoint or service**. It's the right default dashboard for request-driven microservices.

**USE** (Brendan Gregg: Utilization, Saturation, Errors) is applied **per resource**: CPU, memory, disk, NIC, and software resources like connection pools, thread pools and locks. For a pool, utilization is busy connections, saturation is waiting threads, errors are acquisition timeouts.

In practice: RED and golden signals tell you **that** users are hurting and which service. USE tells you **which resource** is the bottleneck.
""", B, ["observability", "golden-signals"], True),

("Logs, metrics and traces: when would you reach for each during an incident?", r"""
They answer different questions, and an investigation usually moves through them in order:

| | Question | Strength | Weakness |
|---|---|---|---|
| **Metrics** | Is something wrong? How much? Since when? | Cheap, aggregated, great for alerts and trends | No per-request detail; high-cardinality tags are expensive |
| **Traces** | Where did the time go across services? | Shows the slow hop and fan-out | Sampled; needs propagation everywhere |
| **Logs** | What exactly happened to this request? | Full context, exceptions, business IDs | Expensive at volume; hard to aggregate |

**Typical flow:** an SLO burn alert fires (metrics). The p99 dashboard by endpoint shows `/checkout` is slow (metrics). An exemplar or trace search for slow checkout traces shows a 1.7 s span in `fraud-service` (traces). Filtering logs by that `traceId` shows `ReadTimeoutException` and a retry loop (logs).

Make this possible up front: **structured JSON logs that include trace IDs**, Micrometer metrics with exemplars, and OpenTelemetry context propagation over HTTP and Kafka.
""", B, ["observability", "logging", "tracing"], True),

("How would you implement correlation IDs across microservices in Spring Boot?", r"""
**Goal:** one ID that follows a request through every service, thread and log line.

1. **Prefer tracing:** add Micrometer Tracing (OTel bridge) or the OpenTelemetry agent. Spring Boot then puts `traceId` and `spanId` in the **MDC** and propagates the W3C `traceparent` header through `RestClient`, `WebClient` and Kafka templates that are built from Spring's auto-configured builders.
2. **Custom header if needed:** a `OncePerRequestFilter` reads `X-Correlation-Id` (generating a UUID if it's missing or invalid), puts it in the MDC, echoes it in the response and **removes it in `finally`**, since pooled threads reuse ThreadLocals.
3. **Outgoing calls:** an interceptor copies the ID into HTTP headers and Kafka record headers. Consumers read it back into the MDC.
4. **Async hops:** MDC is a ThreadLocal, so it is lost on `@Async`, executors and `CompletableFuture`. Use a `TaskDecorator` or Micrometer **context-propagation** to copy it.
5. **Logging:** JSON logs include the field, so a search on one ID shows the whole journey.

Pitfalls: building clients with `new RestTemplate()` (skips the instrumented builder), unbounded or untrusted header values, and forgetting Kafka.
""", I, ["observability", "spring", "correlation-id"], False),

("Define SLI, SLO, SLA and error budget with a concrete example.", r"""
Take an **Order API** for checkout:

- **SLI**: a measured ratio of good events to valid events. *"Share of `POST /orders` requests, measured at the gateway, that return non-5xx within 400 ms."*
- **SLO**: an internal target for the SLI over a window. *"99.9% over a rolling 28 days."*
- **SLA**: an external, contractual promise with consequences (credits). It's looser than the SLO, say 99.5%, so you get warning before you breach it.
- **Error budget**: `1 - SLO`. At 99.9% and 20M requests per 28 days, you may fail **20,000** requests. In time, that's about **40 minutes** of full outage.

**Why it matters:** the budget is a decision tool. While budget remains, the team ships features and takes calculated risks. When it's spent, the **error budget policy** applies: freeze risky releases and prioritise reliability work. Alerts fire on **burn rate** (how fast the budget is being spent), not on raw thresholds.

Common mistakes: SLOs at 100% (impossible and paralysing), averages instead of thresholds for latency, and measuring inside the app, which misses requests that never arrived.
""", B, ["slo", "sre"], True),

("Why alert on SLO burn rate instead of 'error rate > 1% for 5 minutes'?", r"""
A fixed threshold fails in both directions:
- **Too sensitive**: a 2-minute blip at 2% pages someone at 3 a.m. but uses a tiny slice of the monthly budget.
- **Too blind**: a steady 0.5% error rate never trips it, yet over a week it can spend the entire budget.

**Burn rate** = how fast you spend budget relative to spending it evenly. A burn rate of 1 exhausts the budget exactly at the end of the window. The SRE Workbook's **multiwindow, multi-burn-rate** setup for a 99.9% SLO:

| Severity | Windows | Burn rate | Budget used |
|---|---|---|---|
| Page | 1 h **and** 5 min | 14.4 | 2% |
| Page | 6 h **and** 30 min | 6 | 5% |
| Ticket | 3 d **and** 6 h | 1 | 10% |

The long window proves the burn is significant. The short window proves it's **still happening**, so the alert resets quickly after recovery. The result: pages map to real user impact, slow burns still get caught as tickets, and severity scales with how fast you're losing reliability.
""", A, ["slo", "alerting"], False),

("Your service logs 'HikariPool-1 - Connection is not available, request timed out after 30000ms'. Diagnose it.", r"""
That's **connection pool exhaustion**: every connection is busy and callers waited the full `connectionTimeout`.

**Confirm:** `hikaricp_connections_active == max`, `pending > 0`. Thread dumps show request threads parked in `HikariPool.getConnection`. The question is **why connections are held so long**:

1. **Slow work inside transactions**, the most common cause: an HTTP call, file upload or Kafka send inside `@Transactional`. Thread dumps show the holders in socket reads *within* a transactional method.
2. **Slow queries**: check the slow-query log, lock waits and DB CPU. The pool is just where the DB problem shows up.
3. **Open Session in View** keeps the connection for the whole request.
4. **A real leak**: manual JDBC without try-with-resources. `leakDetectionThreshold=20000` logs the holder's stack.
5. **A traffic spike** beyond capacity.

**Mitigate:** roll back if it's new; shed load; restart only after taking a thread dump.
**Fix:** move remote calls out of transactions, fix the query or index, set `spring.jpa.open-in-view=false`.

**Don't** just raise `maximumPoolSize`. Pods x pool size can exceed what the DB handles, which moves the queue into MySQL and slows everyone down.
""", I, ["hikaricp", "incident", "database"], True),

("Pods are being OOMKilled every few hours since a release. Walk me through it.", r"""
**First, which "OOM"?** Exit code **137 / OOMKilled** with no Java `OutOfMemoryError` means the **container** limit was hit by total process memory. A Java OOM in the logs means the heap (or metaspace) filled. The debugging paths differ.

**Mitigate:** roll back if the release correlates. Otherwise raise the memory limit or schedule rolling restarts to buy time. **Capture evidence first** from one pod: heap dump, `GC.class_histogram`, GC log.

**If it's a Java heap leak:** the GC log shows the *after-GC* floor rising. Open the heap dump in Eclipse MAT, look at the Dominator Tree by retained size, then follow *path to GC roots*. Typical culprits: an unbounded static map cache, ThreadLocals never removed, an unbounded executor queue, or a huge persistence context in a batch job. Diff the release for any of these.

**If it's container-only (heap looks fine):** non-heap memory grew: thread stacks (thread leak?), direct buffers (Netty), metaspace (class-loader leak), code cache. Enable `-XX:NativeMemoryTracking=summary` and compare `VM.native_memory` over time. Make sure the heap is sized with `-XX:MaxRAMPercentage=70-75`, not `-Xmx` equal to the limit.

**Guardrails:** memory alerts on the after-GC old gen, `HeapDumpOnOutOfMemoryError`, bounded caches and queues, and a soak test in CI before release.
""", A, ["memory-leak", "oom", "kubernetes"], True),

("How do you take and read a thread dump? What patterns do you look for?", r"""
**Take it:** `jcmd <pid> Thread.print -l > dump.txt` (or `jstack`, or `kill -3`). Take **three, 5-10 seconds apart**. What persists across dumps is the story; one dump is a single snapshot.

**Read it:** for each thread, check its **state** and **top frames**:
- `RUNNABLE`: on CPU *or* blocked in native I/O (socket reads show as RUNNABLE).
- `BLOCKED`: waiting for a `synchronized` monitor ("waiting to lock <0x...>").
- `WAITING`/`TIMED_WAITING`: parked (locks, pools, queues) or sleeping.

**Patterns:**
| Seen | Meaning |
|---|---|
| Most request threads in `HikariPool.getConnection` | Pool exhaustion |
| Many BLOCKED on one lock owner | Contention on a synchronized hot path |
| Many RUNNABLE in socket read to one host | Slow downstream, missing read timeout |
| "Found one Java-level deadlock" | Lock ordering bug |
| Same RUNNABLE frames every time | CPU hotspot or infinite loop |
| Thread count growing | Thread or executor leak |

**Tips:** group identical stacks (`uniq -c` or a viewer). For high CPU, use `top -H -p <pid>`, convert the thread ID to hex and match `nid=0x...`. Look at *your* package frames to find the business code involved.
""", I, ["jvm", "thread-dump", "tools"], True),

("How do you find a memory leak from a heap dump?", r"""
1. **Capture safely:** `jcmd <pid> GC.heap_dump /tmp/h.hprof`, or automatically with `-XX:+HeapDumpOnOutOfMemoryError`. It pauses the JVM and the file is about the size of the used heap, so take it from an instance **out of the load balancer**, and treat it as sensitive (it holds PII and secrets).
2. **Quick look first:** `jcmd <pid> GC.class_histogram`, taken twice an hour apart, shows which classes are *growing*.
3. **Eclipse MAT:**
   - **Leak Suspects** report for a first hypothesis.
   - **Dominator Tree** sorted by **retained heap** (what would be freed if this object died). Look for one collection retaining most of the heap, like a `HashMap` holding 3 GB.
   - **Path to GC Roots** (excluding weak/soft references) shows **who keeps it alive**: a static field, a ThreadLocal on a pool thread, a listener list.
4. **Map it to code** and confirm with a second dump that the suspect is growing.

**Usual causes:** a static map cache with no eviction (use Caffeine with `maximumSize` and a TTL), ThreadLocals not removed, listeners not unregistered, unbounded queues, a Hibernate session accumulating entities (`flush()`/`clear()` every N rows), and a cache key that includes a timestamp, so it never hits.
""", I, ["memory-leak", "heap-dump", "jvm"], False),

("One service is at 100% CPU but traffic hasn't increased. How do you find the hot code?", r"""
**Rule out the JVM first:** check the GC log and `jvm_gc_pause_seconds`. A heap close to full makes GC run constantly and burn CPU. If it's GC, it's a memory problem, not a code problem.

**Find the hot threads:**
1. `top -H -p <pid>` lists the busiest native threads. Convert the TID to hex.
2. `jcmd <pid> Thread.print` and match `nid=0x...`. Repeat 3 times. A thread stuck in the same frames is the hotspot.

**Profile properly:** `asprof -e cpu -d 30 -f cpu.html <pid>` (async-profiler) or a JFR recording with the `profile` settings. Look for **wide plateaus near the top** of the flame graph.

**Common culprits:**
- Catastrophic regex backtracking on certain inputs.
- An infinite loop on unexpected data.
- `Pattern.compile`, or `new ObjectMapper()`, on every request.
- Exceptions used for control flow (stack trace capture is expensive).
- Huge JSON (de)serialization; string concatenation in logging.
- A busy-spin retry loop with no backoff.

**Then ask "what changed?":** a new data shape (one tenant sending 50 MB payloads), a config change or a dependency upgrade. Mitigate by rolling back or blocking the bad input, and add input size limits and a regression test.
""", I, ["cpu", "profiling", "jvm"], False),

("Only 1 of 20 pods shows a high error rate. What do you do?", r"""
**Mitigate first:** take that pod **out of rotation** (fail its readiness, or cordon/drain the node). Users stop seeing errors immediately. Keep the pod alive if possible for forensics rather than deleting it.

**Investigate what makes it different:**
- **Version/config:** is it on a different image, a stale ConfigMap, a different feature-flag state? A half-finished rollout?
- **Node:** noisy neighbour, disk errors, network packet loss, CPU throttling. Check node metrics and `kubectl describe node`.
- **Startup:** did it fail to warm a cache, miss a secret, or fail to connect to one Redis or DB replica? Check its startup logs.
- **Dependencies:** is it pinned to a bad DB replica or a DNS entry that changed? Compare connection targets.
- **JVM state:** heap close to full or a thread stuck. Take a thread dump and a GC log.
- **Clock skew:** JWT validation or signature failures.

**Lesson to state:** this is why dashboards must be **breakable by instance, AZ, version and shard**, and why readiness probes should check real dependencies. The fleet-wide average showed only 5% errors and hid a pod at 100%. Guardrails: outlier detection in the load balancer or service mesh (automatic ejection), and per-instance error alerts.
""", I, ["incident", "isolation", "kubernetes"], False),

("After a Redis restart, DB CPU hit 100% and the site went down, even after Redis came back. Explain and prevent it.", r"""
**What happened:** a **cold cache stampede** that became a **metastable failure**. With an empty cache, every read missed and went to MySQL, often many requests for the same hot key at once. The DB saturated, responses slowed and clients retried. The loaders that should have refilled the cache kept timing out, so the cache stayed empty even though Redis was healthy.

**Mitigate:**
- **Shed or rate-limit** traffic at the gateway so the DB can recover and the cache can fill.
- **Warm** the top N hot keys with a script.
- Temporarily turn off expensive non-critical features. Add read replicas.

**Prevent:**
- **Single-flight / request coalescing:** one DB load per key, other callers wait for that result (Caffeine's `get(key, loader)` locally, a short Redis lock per key in a distributed setup).
- **TTL jitter** so keys don't expire together; **soft TTL** with background refresh; serve stale on errors.
- **Two-level cache:** a small in-process Caffeine cache in front of Redis takes the hottest keys.
- **Warm before traffic:** readiness waits for warm-up after deploys or Redis failover.
- **Load test with a flushed cache**, and alert on hit ratio. The system has to survive without its cache, perhaps degraded but not dead.
""", A, ["cache", "stampede", "incident"], True),

("A downstream service slowed down and now your service is down too. Why, and how do you prevent cascading failure?", r"""
**Why:** your request threads block on the slow dependency. With a 30 s (or infinite) read timeout, every Tomcat thread ends up waiting on it. New requests queue, **even endpoints that never call that service** starve, health checks time out and pods get restarted. Your callers then see you as slow, and the failure climbs up the chain. Retries at each layer multiply the load on the sick service.

**Prevent:**
1. **Timeouts on every remote call** (connect ~0.5 s; read set from the dependency's p99.9 plus margin), plus an overall request deadline.
2. **Bulkheads:** a bounded pool or semaphore per dependency, so a slow fraud service can only use, say, 20 threads.
3. **Circuit breaker** (Resilience4j): after a failure or slow-call threshold, fail fast for a cool-down period, then probe.
4. **Fallbacks:** cached or default response, degrade the feature ("recommendations unavailable"), or accept async ("payment confirmation will follow").
5. **Retries done right:** one layer, backoff with jitter, a retry budget.
6. **Load shedding:** reject early with 503 when saturated instead of queueing until everything times out.
7. **Health checks:** liveness must not depend on downstreams, or Kubernetes will restart healthy pods.
""", A, ["resilience", "cascading-failure", "timeouts"], True),

("What is a retry storm? How do you stop one in progress and prevent the next one?", r"""
**What:** a dependency slows down or errors, every client retries, and the extra load keeps it down. Retries **multiply across layers**: 3 attempts at each of 5 layers means up to **3^5 = 243 calls** per user action reaching the bottom service. Synchronised retries (no jitter) arrive in waves.

**Stop it now:**
- Turn retries off or down through config or a feature flag. This is why retry settings should be dynamic.
- Let circuit breakers open, or force them open.
- Shed load at the edge (rate limits, 503 with `Retry-After`).
- Scale the struggling dependency only if it is *capacity*-bound. Scaling doesn't help a lock problem.

**Prevent:**
- **Retry at one layer only**, usually the one closest to the failing call or the client.
- **Exponential backoff with full jitter**, a capped max delay and a small max attempt count.
- A **retry budget**: a token bucket limiting retries to ~10% of normal traffic.
- Retry only **idempotent** operations, or ones with **idempotency keys**.
- Don't retry errors that can't succeed (4xx, validation).
- Honour `Retry-After` and 429s, and use circuit breakers.
""", A, ["retries", "resilience", "incident"], False),

("A query that was fast last week now takes 8 seconds. How do you investigate?", r"""
**1. Confirm and find it:** the slow-query log, or `performance_schema.events_statements_summary_by_digest` ranked by total latency. Is it every execution or only some parameter values?

**2. EXPLAIN (and EXPLAIN ANALYZE)** with real parameters. Compare against what you expect: `type=ALL` (full scan), the wrong `key`, `rows` far bigger than before, `Using filesort` or `Using temporary`.

**3. What changed?**
- **Data growth or skew:** the table grew from 1M to 50M rows, or one tenant now has 5M rows and the plan that worked for small tenants doesn't.
- **Plan change:** stale statistics. Run `ANALYZE TABLE`, then compare.
- **Code change:** a new predicate, a function on an indexed column (`DATE(created_at) = ?`), an implicit type conversion (comparing a VARCHAR column to a number), `OR` across columns, or a leading-wildcard `LIKE`.
- **Schema change:** an index dropped or altered by a migration.
- **Contention, not the plan:** the query waits on locks, so check lock waits and long transactions.

**4. Fix:** add or adjust a composite index (equality columns first, then range or sort), rewrite the predicate, use keyset pagination, and as a last resort an index hint.

**5. Guardrail:** slow-query alerting, EXPLAIN review of new queries in PRs, and tests on production-sized data.
""", I, ["mysql", "slow-query", "explain"], True),

("Users report intermittent 'Lock wait timeout exceeded' errors on checkout. How do you approach it?", r"""
`Lock wait timeout exceeded; try restarting transaction` means a transaction waited longer than `innodb_lock_wait_timeout` (default **50 s**) for a row lock held by another transaction. Note: that's not a deadlock. InnoDB detects deadlocks immediately and rolls one victim back.

**Find the blocker** while it's happening:
```sql
SELECT * FROM sys.innodb_lock_waits\G      -- waiting query, blocking trx, blocking thread
SELECT * FROM information_schema.innodb_trx ORDER BY trx_started;
```
Usually the blocker is a **long transaction**: an app that holds a transaction open across an HTTP call, a batch job updating many rows in one transaction, or a session left idle in a transaction.

**Look for hot rows:** checkout updating one shared row (a global inventory or counter row) serialises every buyer behind it.

**Fixes:**
- Keep transactions short, with no remote calls inside them.
- Chunk batch updates; give their predicates proper indexes (unindexed `UPDATE`s lock far more rows, plus gaps under REPEATABLE READ).
- Use conditional single-statement updates (`UPDATE stock SET qty = qty - 1 WHERE sku = ? AND qty > 0`) instead of read-then-write with `FOR UPDATE`.
- Shard hot counters.
- Set a short per-session lock wait timeout on OLTP paths so requests fail fast.
- Retry the transaction once with backoff, safely, using idempotency.
""", A, ["mysql", "locking", "incident"], False),

("A production host's disk is full. What do you do now, and how do you prevent it?", r"""
**Now:**
1. **Impact:** what's on that disk? A full DB volume stops writes. A full log volume can block the app's logging threads and hang requests. Take the host out of rotation if it's serving errors.
2. **Find the space:** `df -h` for the filesystem, `du -xh /var --max-depth=2 | sort -h | tail` for the culprit directory. Usual suspects: application logs without rotation, old heap dumps, temp or upload files, MySQL binlogs, Docker images and layers.
3. **Free it safely:** compress or move old logs, delete old dumps, `PURGE BINARY LOGS BEFORE ...` only once replicas no longer need them.
4. **Gotcha:** deleting a file that a process still holds open doesn't free the space. `lsof +L1` shows deleted-but-open files; truncate them (`: > file`) or restart that process.

**Prevent:**
- Log rotation with size and age limits (logback `SizeAndTimeBasedRollingPolicy`); ship logs off-host.
- Retention policies for binlogs, Kafka and temp directories.
- Alerts at 80% and 90%, plus a **"disk will fill within 4 hours"** alert (`predict_linear`), because the fill rate matters more than the level.
- Keep heap dumps on a separate volume with cleanup.
""", B, ["incident", "disk", "operations"], False),

("At midnight every call to a partner API starts failing with SSL handshake errors. What's your hypothesis and response?", r"""
**Hypothesis:** an exact-time, 100%-failure pattern against one dependency is almost always a **certificate problem**: their server certificate expired, our **client mTLS certificate** expired, or they rotated to a certificate chain whose CA isn't in our Java truststore. Errors look like `PKIX path building failed`, `certificate_expired` or `bad_certificate`.

**Confirm:** `openssl s_client -connect partner:443 -servername partner -showcerts` shows the expiry and the chain. Check our client certificate's `notAfter`. Compare against the JVM truststore (`keytool -list`).

**Respond:**
- Our client certificate expired: renew and redeploy the keystore/secret.
- Their certificate expired: escalate to the partner.
- New CA: add the CA to our truststore and roll it out.
- Meanwhile, queue outbound requests for retry if the business flow allows (payouts, webhooks) instead of losing them.
- **Never** turn off certificate validation as a "fix".

**Prevent:** automated renewal (ACME / cert-manager); an inventory of every certificate *and* truststore, client certificates included; expiry alerts at 30/14/7 days; synthetic checks against critical partners so you find out before customers do.
""", B, ["tls", "certificates", "incident"], False),

("When do you roll back versus debug forward with a hotfix?", r"""
**Default to rolling back** when the impact lines up with a change and the rollback is known-safe. It's usually the fastest way to stop customer harm, and it restores a known-good state. Debugging continues on a staging copy or from the evidence you captured.

**Debug forward or hotfix** only when:
- **The rollback isn't safe:** the release included an irreversible or non-backward-compatible **DB migration**, or data has already been written in a new format the old code can't read. This is why migrations should follow expand -> migrate -> contract and stay backward compatible for one release.
- **The change isn't the cause:** the evidence points elsewhere (dependency, data, traffic), so rolling back won't help.
- **The fix is trivial and low-risk**, for example flipping a feature flag, which is effectively a rollback.
- **Rolling back reintroduces a worse problem**, like a security vulnerability the release fixed.

**State the decision criteria out loud:** blast radius, time to roll back vs time to fix, confidence in the hypothesis, and data safety. Mention that you'd **capture evidence first** (thread dump, logs, traces from a canary pod) so the rollback doesn't destroy what you need for the root cause.
""", I, ["incident", "rollback", "deployment"], True),

("What is a blameless postmortem, and what goes into one?", r"""
A **postmortem** is a written review after a significant incident. It records what happened, its impact and the root causes, and drives **action items that make recurrence less likely**. **Blameless** means it assumes people acted reasonably with the information they had, and looks for the **systemic** gaps that allowed the failure: "the pipeline let an unreviewed migration run", not "Amit broke prod". Blame teaches people to hide mistakes, which makes the next incident worse.

**When:** user-visible impact above a threshold, any data loss, on-call intervention such as a rollback, a long resolution time, or a monitoring miss.

**Contents:**
1. Summary and **impact** (users, duration, revenue, SLO budget used).
2. **Timeline** in UTC: trigger, detection, decisions, mitigation, resolution.
3. **Root cause and contributing factors.** There's rarely just one.
4. What went well, what went poorly, where we got lucky.
5. **Action items** with owner, due date and priority, grouped as prevent / detect / mitigate.

**Make it count:** review it in a meeting, share it widely, store it where it's searchable, and **track the action items to completion**. A postmortem with vague items like "be more careful" is a warning sign.
""", B, ["postmortem", "incident-response", "culture"], False),

("Tell me about a production incident you handled.", r"""
Interviewers grade **structure, ownership, decisions and the guardrail**, not how dramatic the incident was. A skeleton:

1. **Context (1-2 lines):** system, scale, your role. *"Order-processing service for a retail client, Spring Boot and MySQL, about 40k orders a day. I was the on-call developer."*
2. **Detection:** how you found out. *"Support escalated failed payments; our dashboards showed 6% 5xx on /payments."*
3. **Investigation (your actions):** signals you checked, hypotheses you rejected. *"Pool metrics showed pending connections; thread dumps showed threads in a bank API call inside @Transactional."*
4. **Decision and mitigation:** *"I proposed rolling back the morning release instead of hot-fixing, because the rollback was 5 minutes and safe; errors cleared in 8 minutes."*
5. **Result with numbers:** duration, orders affected, recovery (reprocessed 312 orders).
6. **Guardrails you drove:** *"Moved external calls out of transactions, added a pending-connection alert, added a checklist item for remote calls in PR review. No recurrence in 6 months."*

From a service company, good sources include production support tickets, batch failures, slow reports and UAT outages. Be honest about your role, and use **I** for your actions and **we** for the team.
""", I, ["behavioral", "incident", "storytelling"], True),

("Your error-rate dashboard is flat, but customers are complaining. What could be going on?", r"""
Your monitoring may not be measuring what users experience. Possibilities:

- **Implicit errors:** HTTP 200 with wrong or empty content (an empty search result because a fallback returned `[]`, a stale price from a cache). Error metrics only count 5xx.
- **Errors before your service:** CDN, WAF, gateway, DNS or TLS failures, or requests rejected by a load balancer. The app never sees them. Check edge and gateway metrics and synthetic probes.
- **Client-side failures:** a mobile app version with a bug, JavaScript errors, a timeout on the client that's shorter than your latency. Check RUM and crash reporting.
- **Segment-specific:** one region, one tenant, one payment method, one app version. A 100% failure for 1% of users looks like 1% in the aggregate.
- **4xx that are really your fault:** an auth change returning 401/403, validation rejecting legitimate input. Many dashboards exclude 4xx.
- **Latency, not errors:** p50 is fine but p99 is 10 s, or a background flow (emails, refunds) is delayed. Check queue lag.
- **Correctness:** duplicate charges, missing notifications.

**Action:** reproduce with a real affected user's ID and trace it. Long term, add SLIs measured at the edge or client, business-level metrics (orders/min, payment success rate by method) and synthetic journeys.
""", I, ["observability", "slo", "incident"], False),

("Latency spikes every day around 2 PM and then recovers by itself. How do you investigate?", r"""
A **periodic** pattern means something periodic: look for what happens at 2 PM.

**Candidates:**
- **Scheduled jobs:** a cron/batch job, a report export, a cache rebuild or data sync competing for DB, CPU or locks. Check job schedules (yours *and* other teams' on shared DBs).
- **Traffic peak:** lunch-hour traffic or a daily marketing push. Compare traffic curves. If latency tracks traffic, it's a capacity problem: find the saturated resource with USE.
- **Synchronised cache expiry:** keys loaded at a fixed time with a 24h TTL all expire together. Fix with jitter.
- **GC:** the heap fills on a cycle, then a long old-gen or full GC. Check GC logs at 2 PM.
- **Infrastructure:** backups, snapshots, log rotation and compression, DB statistics jobs, autoscaler reacting late (a scale-up lag of several minutes).
- **Dependencies:** a downstream with its own daily job.

**Method:** overlay the latency graph with traffic, DB metrics, GC pauses and the list of scheduled jobs. Pull traces from the spike window to see which span grows. A continuous JFR recording dumped right after the spike shows lock and GC behaviour.

**Fix** depends on the cause: move or throttle the job, use a replica, add jitter, scale ahead of the predictable peak.
""", I, ["latency", "investigation", "method"], False),

("How do you debug an issue you can't reproduce locally?", r"""
Narrow the gap between production and your laptop with **evidence**, not guesses.

1. **Characterise it precisely:** which users, endpoints, data, regions, times, versions? What do failing requests share? (Search traces and logs by attributes.) Intermittent often means concurrency, specific data, a specific instance, or timing.
2. **Use production telemetry:** pull a full trace and its logs for a failing request using the trace ID. Compare it with a successful one.
3. **Increase visibility temporarily:** raise the log level for one package at runtime through `POST /actuator/loggers/{name}`, or targeted logging behind a feature flag for one tenant. Take JFR recordings or thread dumps when it happens.
4. **Recreate conditions:** production-like data volume (anonymised dump), the same config and flags, the same dependency versions, Testcontainers with the real MySQL version, concurrency (run the flow 100x in parallel), the same timezone and locale.
5. **Form hypotheses and test them one at a time:** "fails only when the cart has more than 50 items" -> write a test that does that.
6. **Once found:** write a failing test first, then fix.

Common culprits for "works on my machine": race conditions, timezone or DST handling, data that only exists in production, caching layers, different config, and memory or volume limits.
""", I, ["debugging", "method"], False),

("You're launching a new service next month. What would you add on day one to make it debuggable in production?", r"""
**Metrics:** RED per endpoint (Micrometer `http.server.requests` comes free), client metrics per downstream (latency, errors, timeouts), saturation gauges (Hikari pending, executor queue, Tomcat busy threads), JVM and GC metrics, Kafka consumer lag, a `build_info` metric with version, and **business metrics** (orders created, payments failed by reason).

**Logs:** structured JSON with `traceId`, service, version and key business IDs; no PII; meaningful levels; logging at boundaries and state transitions.

**Traces:** OpenTelemetry / Micrometer Tracing with propagation over HTTP and Kafka; tail sampling that keeps errors and slow traces.

**Health:** separate liveness (process OK) and readiness (can serve; dependencies reachable) probes.

**SLOs and alerts:** an SLO per critical journey, burn-rate alerts, every alert linked to a **runbook**.

**JVM safety nets:** `HeapDumpOnOutOfMemoryError`, GC logging, continuous JFR.

**Operability:** runtime log-level changes (actuator loggers), feature flags or kill switches for risky paths, timeouts and circuit breakers configured from properties, and dashboards **split by version, instance and AZ**.

This list doubles as a strong answer to "how is your service production ready?".
""", B, ["observability", "production-readiness"], False),

("Requests are timing out, but CPU is only 20% and the DB looks healthy. Where is the time going?", r"""
Low CPU with high latency means requests are **waiting**, not working. Find what they wait on:

1. **Thread dumps (x3):** where are request threads parked?
   - `HikariPool.getConnection` -> pool exhaustion (connections held across slow work).
   - Socket read to one host -> a slow downstream with long or no timeouts.
   - `BLOCKED` on one monitor -> lock contention (synchronized cache, sync logger).
   - `LinkedBlockingQueue.take` or futures `get()` -> waiting on an executor that's saturated.
2. **Saturation metrics:** Tomcat busy threads at max, executor queue size, Hikari pending, HTTP client pool pending (Apache HttpClient's per-route default is small).
3. **Wall-clock profile:** `asprof -e wall` shows waiting time, which a CPU profile can't.
4. **Traces:** the gap between spans may be queueing inside your own service.
5. **Other hidden waits:** DNS resolution, TLS handshakes per request (no connection reuse), GC safepoint pauses, CPU **throttling** by container limits (CPU looks low on average but gets throttled in bursts; check `container_cpu_cfs_throttled_seconds_total`), and virtual threads pinned while blocking.

**Fix** depends on the wait: timeouts and bulkheads, shorter transactions, a bigger client pool, removing the synchronized hot spot, or raising CPU limits.
""", A, ["latency", "thread-pool", "saturation"], False),

("Kafka consumer lag is growing steadily. How do you investigate?", r"""
Lag grows when **produce rate > consume rate**. Find which side changed.

**1. Producer side:** did inbound traffic spike (a campaign, a backfill, a replay)? Compare `records-in` per topic with the baseline.

**2. Consumer throughput:**
- **Processing got slower:** a slow DB write, a downstream HTTP call, a lock. Check processing-time metrics and traces per message. This is the most common cause.
- **Rebalance loops:** consumers exceeding `max.poll.interval.ms` (slow batch processing) get kicked out, rebalance, reprocess, repeat. Check logs for rebalances and `CommitFailedException`.
- **Stuck partition:** one partition's lag grows while the others are fine. Either a **poison message** retrying forever (send it to a dead-letter topic after N attempts), or a **hot key** sending all its traffic to one partition.
- **Not enough parallelism:** consumers ≤ partitions; a consumer count above the partition count sits idle. Consider increasing partitions (it changes key-to-partition mapping), or parallel processing within a partition while keeping per-key order.
- **Consumer instances down or crash-looping.**

**Mitigate:** scale consumers up to the partition count, skip or park poison messages to a DLT, pause non-critical work, temporarily raise `max.poll.interval.ms` or lower `max.poll.records`.

**Guardrails:** alert on lag in **time** (how old the oldest message is), not just count; a DLT strategy; idempotent consumers so reprocessing is safe.
""", I, ["kafka", "lag", "incident"], False),

("Why are high-cardinality metric labels dangerous, and where should that data go instead?", r"""
In Prometheus-style systems, **every unique combination of label values is a separate time series**, stored in memory and on disk. Tag `http_requests_total` with `userId` and 2M users becomes 2M series *per* method, status and URI combination. The result: memory explosion on Prometheus, slow queries, dropped scrapes, a big bill from managed vendors, and sometimes a monitoring outage *during* your incident.

**Common offenders:** user/order/session IDs, raw URLs with path params (`/orders/98123` instead of `/orders/{id}`), full error messages, timestamps, pod names on high-churn workloads.

**Rules:**
- Labels must be **bounded and low-cardinality**: endpoint template, method, status class, region, dependency name, error *type*.
- Micrometer's `http.server.requests` uses the URI **template** by default. Don't defeat it by building metric names or tags from raw paths.
- Use Micrometer `MeterFilter`s to cap or deny risky tags.

**Where per-entity detail belongs:**
- **Traces:** span attributes can carry `orderId`, `tenantId`.
- **Logs:** structured fields, searchable by ID.
- **Exemplars:** link a histogram bucket to a sample trace ID.
- **Analytics store** (ClickHouse, BigQuery) for per-tenant breakdowns.
""", A, ["metrics", "observability", "prometheus"], False),

("How can you safely gather more information from production without redeploying or causing harm?", r"""
**Built into Spring Boot:**
- **Runtime log levels:** `POST /actuator/loggers/com.shop.payment` with `{"configuredLevel":"DEBUG"}`. Revert afterwards, and be careful with volume and PII.
- **Actuator endpoints** (secured, internal port): `/metrics`, `/threaddump`, `/heapdump` (heavy: take it from a drained pod), `/env` (masked), `/conditions`.

**JVM tools with low overhead:**
- `jcmd Thread.print`, `GC.class_histogram`, JFR (about 1-2% overhead), async-profiler for 30-60 s.
- Continuous JFR so you can dump the last hour *after* a spike.

**Targeted exposure:**
- **Feature flags** to switch on extra logging or a new code path for a single tenant or test account.
- **Canary pods** with extra instrumentation for a small slice of traffic.
- **Traffic shadowing / replay** into a non-prod copy for risky experiments.

**Safety rules:**
- Treat heap dumps and debug logs as **sensitive data** (PII, secrets).
- Prefer read-only investigation. Never run ad hoc `UPDATE`s on prod without review and a backup plan.
- Run heavy diagnostics on one instance removed from the load balancer.
- Time-box elevated logging, and announce what you're doing in the incident channel.
""", I, ["debugging", "actuator", "operations"], False),
]

SOURCES = [
 ("Google SRE Book - Monitoring Distributed Systems (four golden signals)", "https://sre.google/sre-book/monitoring-distributed-systems/"),
 ("Google SRE Book - Service Level Objectives", "https://sre.google/sre-book/service-level-objectives/"),
 ("Google SRE Workbook - Alerting on SLOs (burn rates)", "https://sre.google/workbook/alerting-on-slos/"),
 ("Google SRE Book - Postmortem Culture: Learning from Failure", "https://sre.google/sre-book/postmortem-culture/"),
 ("Google SRE Book - Managing Incidents", "https://sre.google/sre-book/managing-incidents/"),
 ("Brendan Gregg - The USE Method", "https://www.brendangregg.com/usemethod.html"),
 ("HikariCP - About Pool Sizing", "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing"),
 ("AWS Builders' Library - Timeouts, retries and backoff with jitter", "https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/"),
 ("AWS Builders' Library - Caching challenges and strategies", "https://aws.amazon.com/builders-library/caching-challenges-and-strategies/"),
 ("Spring Boot Reference - Observability and Actuator", "https://docs.spring.io/spring-boot/reference/actuator/observability.html"),
 ("Spring Boot Reference - Structured logging", "https://docs.spring.io/spring-boot/reference/features/logging.html#features.logging.structured"),
 ("OpenTelemetry - Java instrumentation", "https://opentelemetry.io/docs/languages/java/"),
 ("Oracle - jcmd and JDK Flight Recorder troubleshooting guide", "https://docs.oracle.com/en/java/javase/21/troubleshoot/diagnostic-tools.html"),
 ("async-profiler (GitHub)", "https://github.com/async-profiler/async-profiler"),
 ("Eclipse Memory Analyzer (MAT)", "https://eclipse.dev/mat/"),
 ("MySQL 8.4 Reference - InnoDB Locking and Transaction Model", "https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-transaction-model.html"),
]

build("production-debugging", "dbg", "Production Debugging & Incidents", 12, "🚨",
      "A repeatable method for debugging live systems: golden signals, observability, SLOs, JVM forensics, common incident playbooks and blameless postmortems.",
      NOTES, QA, SOURCES)
