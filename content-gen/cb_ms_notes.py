NOTES = []

NOTES.append(("Monolith vs Microservices", r'''
## Monolith
A single deployable unit containing all modules (users, orders, payments) sharing one codebase and usually one database.
**Pros:** simple to develop, test, deploy and debug; in-process calls are fast; ACID transactions across modules are easy; low operational overhead.
**Cons:** as it grows — slow builds, risky big-bang deployments, one bug/memory leak can take down everything, scaling means scaling the whole app, tight coupling, hard for many teams to work in parallel, locked into one tech stack.

## Microservices
An architecture of small, independently deployable services, each owning a **business capability** and its **own data**, communicating over the network (HTTP/gRPC/messaging).
**Pros:**
- Independent deployment and release cadence per team.
- Independent scaling (scale only the search service on sale day).
- Fault isolation (with resilience patterns).
- Technology freedom per service.
- Smaller codebases, clearer ownership (Conway's law: architecture mirrors team structure).
**Cons:**
- Distributed system complexity: network latency/failures, partial failures, retries, timeouts.
- Data consistency without distributed ACID transactions (sagas, eventual consistency).
- Operational overhead: CI/CD per service, containers, orchestration, service discovery, centralised logging, tracing, monitoring.
- Harder testing (contract tests, integration environments) and debugging.
- Risk of a **distributed monolith** — services that must be deployed together because of tight coupling or shared DBs.

## When to choose what
Start with a **well-modularised monolith** ("modular monolith") for a new product or a small team. Move to microservices when you have clear domain boundaries, multiple teams stepping on each other, very different scaling needs, or deployment bottlenecks. Many Indian product companies (Swiggy, Flipkart, Razorpay) run hundreds of services, but they evolved there.

## Decomposition strategies
- **By business capability** (Order, Payment, Inventory, Notification).
- **By subdomain / bounded context** (Domain-Driven Design): each bounded context has its own model and ubiquitous language; "Customer" in Billing differs from "Customer" in Support.
- **Strangler Fig pattern** for migrating a monolith: put a gateway/router in front, carve out one capability at a time into a new service, route traffic to it, and retire the old code gradually.

## Key principles
- **Database per service** — no other service reads your tables directly; share data via APIs or events. Shared DBs create hidden coupling.
- **Loose coupling, high cohesion.**
- **Smart endpoints, dumb pipes.**
- **Design for failure** — timeouts, retries, circuit breakers, fallbacks.
- **Decentralised governance**, but standardise cross-cutting concerns (logging format, tracing, auth) via shared libraries/starters or a service mesh.
- **Automation** — CI/CD and infrastructure as code are mandatory, not optional.
- **Observability** — logs, metrics, traces from day one.

## The 12-factor app (quick recall)
Codebase in VCS, explicit dependencies, config in environment, backing services as attached resources, separate build/release/run, stateless processes, port binding, scale out via processes, disposability (fast start/graceful shutdown), dev/prod parity, logs as event streams, admin processes as one-off tasks.

## How to talk about your experience
If you've only worked on a monolith, say so honestly and explain how you'd split it: identify bounded contexts, extract the least-coupled module first (e.g. notifications), introduce an event bus, and migrate data ownership. Interviewers value trade-off reasoning more than buzzwords.
'''))

NOTES.append(("Service Discovery, API Gateway and Config Server", r'''
## Service discovery
In dynamic environments (autoscaling, containers), service instances' IPs change constantly. Hard-coding URLs doesn't work.
- **Service registry**: instances register themselves on startup (with heartbeats) and are removed when unhealthy. Examples: Netflix **Eureka**, Consul, Zookeeper, etcd.
- **Client-side discovery**: the caller queries the registry and load-balances itself (Eureka + Spring Cloud LoadBalancer). Feign/`@LoadBalanced` RestClient resolve `http://order-service/...`.
- **Server-side discovery**: caller hits a load balancer/router that knows instances (AWS ALB, **Kubernetes Service** + kube-proxy/DNS).

In Kubernetes you usually don't need Eureka: a `Service` gets a stable DNS name (`order-service.default.svc.cluster.local`) and load-balances to healthy pods.

```java
@SpringBootApplication @EnableDiscoveryClient   // optional in newer versions
public class OrderServiceApp {}
// application.yml: eureka.client.service-url.defaultZone: http://eureka:8761/eureka
@Bean @LoadBalanced RestClient.Builder lbBuilder() { return RestClient.builder(); }
```

## API Gateway
A single entry point for external clients that routes requests to backend services and handles cross-cutting concerns:
- Routing and path rewriting (`/api/orders/** -> order-service`)
- **Authentication** (validate JWT once at the edge) and coarse authorisation
- **Rate limiting** and throttling (token bucket with Redis)
- SSL termination, CORS, request/response transformation
- Load balancing, retries, circuit breaking
- Aggregation (one call fans out to many services) — "Backend for Frontend" (BFF) pattern gives each client type (web, mobile) its own gateway
- Logging, metrics, correlation IDs
Examples: **Spring Cloud Gateway** (reactive, Netty), Kong, NGINX, AWS API Gateway, Envoy, Apigee.

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: orders
          uri: lb://order-service
          predicates: [ Path=/api/orders/** ]
          filters:
            - StripPrefix=1
            - name: RequestRateLimiter
              args: { redis-rate-limiter.replenishRate: 10, redis-rate-limiter.burstCapacity: 20 }
            - name: CircuitBreaker
              args: { name: ordersCB, fallbackUri: forward:/fallback/orders }
```
Gateway risks: single point of failure (run multiple replicas behind a load balancer) and becoming a bottleneck or a place where business logic piles up — keep it thin.

**Gateway vs load balancer:** an LB distributes traffic among instances of one service (L4/L7); a gateway is an L7 smart router across many services with API management features.

## Centralised configuration
**Spring Cloud Config Server** serves configuration from a Git repo (or Vault/DB) to all services by application name and profile.
```yaml
# client
spring:
  application.name: order-service
  config.import: "optional:configserver:http://config-server:8888"
```
Benefits: one place to change config, versioned history in Git, environment-specific overrides, encryption of secrets. Runtime refresh with `@RefreshScope` + `/actuator/refresh`, or broadcast to all instances via **Spring Cloud Bus** (Kafka/RabbitMQ).

In Kubernetes, **ConfigMaps** and **Secrets** (mounted as env vars or files) often replace Config Server; external secret managers (Vault, AWS Secrets Manager) handle sensitive values.

## Service mesh (awareness)
A mesh (Istio, Linkerd) injects a sidecar proxy (Envoy) next to each pod to handle mTLS, retries, timeouts, circuit breaking, traffic splitting (canary) and telemetry at the infrastructure level — so application code stays simpler. Trade-off: operational complexity and extra latency.
'''))

NOTES.append(("Inter-service Communication: REST, Feign, WebClient, gRPC", r'''
## Synchronous vs asynchronous
| | Synchronous (REST/gRPC) | Asynchronous (Kafka/RabbitMQ) |
|---|---|---|
| Coupling | Temporal — callee must be up | Decoupled in time |
| Response | Immediate | Eventually (or never) |
| Use for | Queries needing immediate answers (get price, validate user) | Events, notifications, long workflows, fan-out |
| Failure mode | Cascading failures, latency adds up | Lag, duplicates, ordering issues |

Rule of thumb: commands that need an answer now -> sync; facts that happened ("OrderPlaced") -> async events. Minimise synchronous call chains (A -> B -> C -> D multiplies latency and failure probability).

## OpenFeign (declarative REST client)
```java
@EnableFeignClients
@SpringBootApplication class App {}

@FeignClient(name = "inventory-service", path = "/api/inventory",
             fallbackFactory = InventoryFallbackFactory.class)
public interface InventoryClient {
    @GetMapping("/{sku}") StockDto stock(@PathVariable String sku);
    @PostMapping("/reserve") ReservationDto reserve(@RequestBody ReserveRequest r);
}
```
Integrates with service discovery (`name` = service id), load balancing, Resilience4j circuit breakers, request interceptors (to forward JWT/correlation headers), custom error decoders (map 404 to domain exceptions). Configure timeouts:
```yaml
spring.cloud.openfeign.client.config.default:
  connect-timeout: 2000
  read-timeout: 3000
```
Note: Spring now recommends its own **HTTP interface clients** (`@HttpExchange` backed by RestClient/WebClient) for new code; Feign is in maintenance in Spring Cloud.

## WebClient (non-blocking)
```java
Mono<UserDto> user = webClient.get().uri("/users/{id}", id)
    .retrieve()
    .onStatus(HttpStatusCode::is4xxClientError, r -> Mono.error(new NotFoundException()))
    .bodyToMono(UserDto.class)
    .timeout(Duration.ofSeconds(2))
    .retryWhen(Retry.backoff(3, Duration.ofMillis(200)));

// parallel calls
Mono.zip(userMono, ordersMono).map(t -> new Profile(t.getT1(), t.getT2()));
```

## RestClient (Boot 3.2, synchronous fluent)
```java
OrderDto o = restClient.get().uri("/orders/{id}", id).retrieve().body(OrderDto.class);
```

## gRPC
HTTP/2 + Protocol Buffers binary serialisation; strongly typed contracts (`.proto`), code generation, bidirectional streaming, much smaller payloads and lower latency than JSON. Great for internal high-throughput service-to-service calls; less convenient for browsers (needs gRPC-Web) and harder to debug by hand.

## Asynchronous messaging overview
- **Point-to-point queues** (RabbitMQ, SQS): each message consumed by one consumer — work distribution.
- **Publish-subscribe topics** (Kafka, SNS): each subscriber group gets every event — event-driven architecture.
- Delivery semantics: at-most-once, **at-least-once** (most common — consumers must be idempotent), exactly-once (Kafka transactions within Kafka).

## API contracts and versioning
Define contracts with OpenAPI or `.proto`; use consumer-driven contract tests (Pact, Spring Cloud Contract). Make changes backward compatible: add optional fields, never rename/remove without a new version; consumers should ignore unknown fields (`FAIL_ON_UNKNOWN_PROPERTIES=false` is Boot's default).

## Timeouts are mandatory
Every remote call needs connect and read timeouts. Without them, a slow dependency exhausts your thread pool and cascades failure upstream. Set timeouts shorter than your caller's timeout (timeout budget), and combine with retries (only for idempotent operations, with exponential backoff and jitter) and circuit breakers.

## Propagating context
Forward `Authorization` (or exchange tokens), correlation/trace IDs (`traceparent`), and tenant headers via Feign `RequestInterceptor` or `ClientHttpRequestInterceptor`. Micrometer Tracing does trace propagation automatically.
'''))

NOTES.append(("Apache Kafka for Event-Driven Microservices", r'''
## Core concepts
- **Topic**: named stream of records; split into **partitions** (ordered, append-only logs). Ordering is guaranteed **only within a partition**.
- **Producer**: writes records (key, value, headers). Records with the same **key** go to the same partition (hash(key) % partitions) -> per-key ordering (e.g. all events for orderId 42 in order).
- **Broker**: Kafka server storing partitions. A cluster has many brokers. Since Kafka 3.3+/4.0, **KRaft** replaces ZooKeeper for metadata.
- **Replication**: each partition has a leader and followers (replication factor, typically 3). **ISR** = in-sync replicas.
- **Consumer group**: consumers sharing a `group.id` split partitions among themselves; each partition is consumed by exactly one consumer in the group. Max useful parallelism = number of partitions. Different groups each get all messages (pub-sub).
- **Offset**: position of a record in a partition. Consumers commit offsets (stored in the `__consumer_offsets` topic) to resume after restart.
- **Retention**: records are kept for a configured time/size regardless of consumption (default 7 days) — enables replay. **Log compaction** keeps the latest value per key.
- **Rebalance**: when consumers join/leave, partitions are reassigned (cooperative sticky assignor reduces disruption).

## Spring Kafka example
```java
// Producer
@Service @RequiredArgsConstructor
public class OrderEventPublisher {
    private final KafkaTemplate<String, OrderPlaced> kafka;
    public void publish(OrderPlaced e) {
        kafka.send("orders.placed", e.orderId().toString(), e)
             .whenComplete((res, ex) -> { if (ex != null) log.error("send failed", ex); });
    }
}
// Consumer
@KafkaListener(topics = "orders.placed", groupId = "inventory-service", concurrency = "3")
public void onOrder(OrderPlaced e, Acknowledgment ack) {
    if (processed.exists(e.eventId())) { ack.acknowledge(); return; }   // idempotency
    inventory.reserve(e);
    ack.acknowledge();                                                  // manual commit after processing
}
```
```yaml
spring.kafka:
  producer:
    acks: all
    properties: { enable.idempotence: true }
    value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
  consumer:
    enable-auto-commit: false
    auto-offset-reset: earliest
  listener.ack-mode: manual
```

## Delivery guarantees
- **Producer**: `acks=0` (fire and forget), `acks=1` (leader wrote), `acks=all` (all ISR wrote; with `min.insync.replicas=2` for durability). `enable.idempotence=true` prevents duplicates from producer retries.
- **Consumer**: commit **after** processing = at-least-once (duplicates possible on crash -> make handlers idempotent, e.g. store processed event IDs, use upserts). Commit before processing = at-most-once (possible loss).
- **Exactly-once**: Kafka transactions (`transactional.id`) for read-process-write within Kafka. With external DBs you still rely on idempotency or the outbox pattern.

## Error handling
- Retry with backoff: `DefaultErrorHandler` with `FixedBackOff`/`ExponentialBackOff`.
- **Dead Letter Topic (DLT)**: after retries, publish to `orders.placed.DLT` for inspection/replay (`DeadLetterPublishingRecoverer`). Non-blocking retries via `@RetryableTopic` (retry topics with delays).
- Poison pills (undeserialisable messages): use `ErrorHandlingDeserializer`.

## Kafka vs RabbitMQ
| Kafka | RabbitMQ |
|---|---|
| Distributed log; consumers pull; messages retained & replayable | Broker pushes; messages removed after ack |
| Very high throughput (millions/sec), horizontal scaling via partitions | Lower throughput, rich routing (exchanges: direct, topic, fanout, headers) |
| Ordering per partition | Ordering per queue |
| Event streaming, event sourcing, log aggregation, CDC | Task queues, RPC, complex routing, priority queues |

## Why is Kafka fast?
Sequential disk I/O (append-only), OS page cache, zero-copy (`sendfile`) from disk to network, batching and compression, partitioned parallelism.

## Common interview scenarios
- Consumer lag growing -> add partitions + consumers, optimise processing, batch.
- Need ordering per customer -> use customerId as key.
- Duplicate processing -> idempotent consumer with dedup table/unique constraint.
- Changing partition count changes key-to-partition mapping — plan partitions upfront.
'''))

NOTES.append(("Resilience Patterns with Resilience4j", r'''
In a distributed system, a slow or failing dependency can exhaust threads and cascade failures across services. Resilience patterns contain the damage. **Resilience4j** is the standard library in Spring Boot (Hystrix is retired).

## Timeouts
The first line of defence. Every remote call must have connect/read timeouts. `TimeLimiter` in Resilience4j bounds async calls.

## Retry
Retry transient failures (network blips, 503) — but:
- Only **idempotent** operations (or with idempotency keys).
- **Exponential backoff with jitter** to avoid synchronized retry storms.
- Limit attempts; don't retry on 4xx validation errors.
- Retries multiply load: 3 layers x 3 retries = 27 calls. Retry at one layer.
```yaml
resilience4j.retry.instances.inventory:
  max-attempts: 3
  wait-duration: 200ms
  enable-exponential-backoff: true
  exponential-backoff-multiplier: 2
  retry-exceptions: [java.io.IOException, org.springframework.web.client.ResourceAccessException]
  ignore-exceptions: [com.app.BusinessException]
```

## Circuit breaker
Stops calling a failing service so it can recover and your threads aren't wasted.
- **CLOSED**: calls pass through; failures are recorded in a sliding window (count-based or time-based).
- When failure rate (or slow-call rate) exceeds a threshold (e.g. 50% of last 20 calls) -> **OPEN**: calls fail fast immediately (go to fallback) for `wait-duration-in-open-state`.
- Then **HALF_OPEN**: a limited number of trial calls are allowed; if they succeed -> CLOSED, else back to OPEN.
```yaml
resilience4j.circuitbreaker.instances.inventory:
  sliding-window-type: COUNT_BASED
  sliding-window-size: 20
  minimum-number-of-calls: 10
  failure-rate-threshold: 50
  slow-call-duration-threshold: 2s
  slow-call-rate-threshold: 60
  wait-duration-in-open-state: 30s
  permitted-number-of-calls-in-half-open-state: 3
```
```java
@CircuitBreaker(name = "inventory", fallbackMethod = "stockFallback")
@Retry(name = "inventory")
public StockDto stock(String sku) { return inventoryClient.stock(sku); }

private StockDto stockFallback(String sku, Throwable t) {
    log.warn("inventory down for {}: {}", sku, t.toString());
    return StockDto.unknown(sku);        // cached value / default / degrade gracefully
}
```
Annotation order (default aspect order): Retry wraps CircuitBreaker wraps RateLimiter wraps TimeLimiter wraps Bulkhead — so each retry attempt is counted by the breaker.

## Bulkhead
Isolate resources so one slow dependency can't consume all threads (like watertight compartments in a ship).
- **Semaphore bulkhead**: limit concurrent calls (`max-concurrent-calls: 20`).
- **Thread-pool bulkhead**: separate thread pool per dependency.

## Rate limiter
Limit how many calls per period you make (protect a partner API with quotas) or accept (protect yourself). `limit-for-period: 100`, `limit-refresh-period: 1s`. At the edge, the gateway's Redis rate limiter (token bucket) protects services from clients.

## Fallback strategies
Return cached/stale data, a default, a reduced response (show product page without recommendations), queue the request for later, or a clear error. Fallbacks must be cheap and not call another fragile service.

## Other patterns
- **Fail fast** and **graceful degradation**.
- **Idempotency keys** so retries are safe.
- **Load shedding** — reject excess requests early (429/503).
- **Health checks** and readiness probes so LBs stop sending traffic to unhealthy instances.
- **Chaos engineering** to verify resilience (Chaos Monkey for Spring Boot).

## Observability of resilience
Resilience4j exports Micrometer metrics (`resilience4j_circuitbreaker_state`, failure rates, calls) and Actuator endpoints (`/actuator/circuitbreakers`). Alert when breakers open.
'''))

NOTES.append(("Distributed Transactions: Saga, Outbox, 2PC and Idempotency", r'''
With database-per-service, a business operation spanning services (place order -> reserve stock -> charge payment) can't use one ACID transaction.

## Two-Phase Commit (2PC)
A coordinator asks all participants to **prepare** (vote), then tells all to **commit** or **abort**. Gives atomicity but: blocking (participants hold locks while waiting), coordinator is a single point of failure, poor performance and availability, and not supported by most NoSQL stores/message brokers. Generally avoided in microservices (CAP: favours consistency over availability).

## Saga pattern
A sequence of **local transactions**; each publishes an event/message triggering the next step. If a step fails, previously completed steps are undone by **compensating transactions** (semantic undo: refund payment, release stock — not a DB rollback).

### Choreography
Services react to each other's events; no central controller.
```
OrderService: create order (PENDING) -> emit OrderCreated
InventoryService: on OrderCreated reserve stock -> emit StockReserved | StockFailed
PaymentService: on StockReserved charge -> emit PaymentCompleted | PaymentFailed
InventoryService: on PaymentFailed release stock
OrderService: on PaymentCompleted -> CONFIRMED; on *Failed -> CANCELLED
```
Pros: loose coupling, simple for few steps. Cons: hard to see/track the overall flow, risk of cyclic dependencies, harder to debug as steps grow.

### Orchestration
A central **orchestrator** (saga coordinator) tells each service what to do and handles failures/compensation. State machine persisted in the orchestrator's DB. Tools: Temporal, Camunda/Zeebe, Netflix Conductor, AWS Step Functions, or a hand-written state machine.
Pros: clear flow, easier monitoring, timeouts and retries in one place. Cons: orchestrator can become a "god service"; extra component.

Saga properties: **eventual consistency**, intermediate states visible (order PENDING) — design UI/semantics for it. Lack of isolation -> use semantic locks (status flags), commutative updates, re-reading values.

## Transactional Outbox pattern
Problem (dual write): saving to the DB and publishing to Kafka are two separate operations; if the app crashes between them, data and events diverge.
```java
@Transactional
public void placeOrder(Order o) {
    orderRepo.save(o);
    outboxRepo.save(new OutboxEvent("Order", o.getId(), "OrderPlaced", toJson(o))); // same DB tx
}
```
A separate relay reads unpublished outbox rows and publishes them to Kafka, then marks them sent:
- **Polling publisher** (scheduled job, `SELECT ... FOR UPDATE SKIP LOCKED`), or
- **Change Data Capture** with **Debezium** reading the MySQL binlog — lower latency, no polling load.
This gives at-least-once publishing, so consumers must be idempotent.

**Inbox pattern** on the consumer side: store processed message IDs in the same transaction as the business change to deduplicate.

## Idempotency
Retries and at-least-once delivery make duplicates inevitable. Techniques:
- Idempotency key from client (`Idempotency-Key` header) stored with the response; repeated requests return the stored response.
- Unique constraints (e.g. unique `(order_id, event_type)`), upserts (`INSERT ... ON DUPLICATE KEY UPDATE`).
- Processed-event table keyed by event ID.
- Conditional updates (`update ... where status = 'PENDING'`).

## Event sourcing and CQRS (awareness)
- **Event sourcing**: store state as an append-only sequence of events; current state = replaying events. Full audit trail, temporal queries; but complex (schema evolution, snapshots).
- **CQRS**: separate write model (commands) from read models (queries), often updated via events into denormalised views (Elasticsearch, Redis). Useful when read and write needs differ widely.

## CAP and PACELC
In the presence of a network **P**artition, a distributed system must choose **C**onsistency or **A**vailability. PACELC adds: **E**lse (normal operation) trade **L**atency vs **C**onsistency. Microservices with sagas choose availability + eventual consistency for most flows, but use strong consistency where money/inventory demands it (within a single service's DB).
'''))

NOTES.append(("Observability: Logging, Metrics and Distributed Tracing", r'''
Observability = being able to answer "what's wrong and where?" from outside. Three pillars: **logs, metrics, traces**.

## Centralised logging
Each pod's logs are ephemeral and scattered. Ship them to a central store:
- **ELK/EFK**: Elasticsearch + Logstash/Fluentd/Fluent Bit + Kibana.
- **Grafana Loki**, Splunk, Datadog, CloudWatch.
Best practices:
- Structured JSON logs (Boot 3.4: `logging.structured.format.console=ecs` or `logstash`).
- Include `traceId`, `spanId`, service name, user/tenant id in every line (MDC).
- Correct levels: ERROR (needs action), WARN, INFO (business events), DEBUG (off in prod).
- Never log secrets/PII (passwords, card numbers, tokens). Mask them.
- Log to stdout in containers; let the platform collect.

## Metrics
Numeric time-series for dashboards and alerts.
- **Micrometer** is the metrics facade in Spring Boot (like SLF4J for metrics). Actuator exposes `/actuator/prometheus`.
- **Prometheus** scrapes metrics; **Grafana** visualises; **Alertmanager** alerts.
- Golden signals (Google SRE): **latency, traffic, errors, saturation**. RED method for services: Rate, Errors, Duration. USE method for resources: Utilisation, Saturation, Errors.
- Built-in metrics: `http_server_requests_seconds` (with percentiles), JVM memory/GC/threads, HikariCP pool, Kafka consumer lag, Resilience4j states.
```java
Counter.builder("orders.placed").tag("channel", "app").register(registry).increment();
@Timed(value = "payment.charge", percentiles = {0.5, 0.95, 0.99})
public PaymentResult charge(...) {...}
```
Monitor p95/p99 latency, not just averages. Define **SLIs/SLOs** (e.g. 99.9% of requests < 300ms) and alert on error budget burn.

## Distributed tracing
A single user request may touch 10 services. Tracing records the full path.
- **Trace**: the whole request journey, with a unique `traceId`.
- **Span**: one unit of work (an HTTP call, a DB query), with `spanId`, parent id, timings, tags.
- Context propagates via headers (W3C `traceparent`, or B3) across HTTP and Kafka.
- Spring Boot 3: **Micrometer Tracing** with OpenTelemetry or Brave bridge; export to **Zipkin**, Jaeger, Grafana Tempo, or vendors (Datadog, New Relic). (Spring Cloud Sleuth was the Boot 2 solution.)
```yaml
management.tracing.sampling.probability: 0.1   # sample 10% in prod
management.zipkin.tracing.endpoint: http://zipkin:9411/api/v2/spans
```
- **OpenTelemetry** is the vendor-neutral standard for traces, metrics and logs; the OTel Java agent can instrument apps without code changes.

## Health checks
- **Liveness**: is the process alive? If failing, Kubernetes restarts the pod. Shouldn't depend on external systems.
- **Readiness**: can it serve traffic now (DB reachable, warmed up)? If failing, removed from Service endpoints.
- Actuator: `/actuator/health/liveness`, `/actuator/health/readiness`.

## Debugging a slow request in production (sample answer)
1. Check dashboards: which endpoint's p99 rose, error rate, saturation (CPU, pool usage, GC).
2. Find a slow trace by traceId -> see which span (service/DB query/external call) takes time.
3. Jump to logs filtered by that traceId.
4. Drill in: slow query log/EXPLAIN, thread dump for contention, heap/GC for memory issues, connection pool waits.
5. Mitigate (scale, roll back, toggle feature flag), then fix root cause and add an alert/test.

## Alerting
Alert on symptoms users feel (error rate, latency SLO burn), not every CPU spike. Use runbooks and on-call rotations (PagerDuty/Opsgenie).
'''))

NOTES.append(("Docker Essentials for Java Developers", r'''
## Why containers
A container packages the app with its runtime and dependencies into an image that runs the same everywhere ("works on my machine" solved). Containers share the host kernel (namespaces for isolation, cgroups for resource limits), so they're much lighter and faster to start than VMs, which each run a full guest OS.

## Key concepts
- **Image**: read-only template built from a Dockerfile, composed of **layers** (each instruction creates a layer; layers are cached and shared).
- **Container**: a running instance of an image with a writable layer.
- **Registry**: stores images (Docker Hub, AWS ECR, GCR, Harbor).
- **Volume**: persistent storage outside the container lifecycle.
- **Network**: containers on the same user-defined network resolve each other by name.

## Dockerfile for Spring Boot (multi-stage)
```dockerfile
# ---- build stage ----
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline          # cached layer unless pom changes
COPY src src
RUN ./mvnw package -DskipTests
RUN java -Djarmode=tools -jar target/app.jar extract --layers --launcher --destination extracted

# ---- runtime stage ----
FROM eclipse-temurin:21-jre
WORKDIR /app
RUN useradd -r -u 1001 appuser
COPY --from=build /app/extracted/dependencies/ ./
COPY --from=build /app/extracted/spring-boot-loader/ ./
COPY --from=build /app/extracted/snapshot-dependencies/ ./
COPY --from=build /app/extracted/application/ ./
USER appuser
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "org.springframework.boot.loader.launch.JarLauncher"]
```
Best practices:
- **Multi-stage builds** — final image has only the JRE + app, not Maven/JDK (smaller, more secure).
- Order instructions from least to most frequently changing to maximise layer caching; Spring Boot **layered jars** separate dependencies from app code.
- Small base images (JRE, distroless, Alpine with care); pin versions.
- Run as **non-root**; `.dockerignore` to exclude `target/`, `.git`.
- JVM is container-aware (Java 10+): use `-XX:MaxRAMPercentage` instead of fixed `-Xmx`.
- One process per container; log to stdout.
- Alternatively `./mvnw spring-boot:build-image` builds an optimised OCI image with Cloud Native Buildpacks, or use Jib — no Dockerfile needed.

## Essential commands
```bash
docker build -t order-service:1.0 .
docker run -d -p 8080:8080 -e SPRING_PROFILES_ACTIVE=dev --name orders order-service:1.0
docker ps / docker logs -f orders / docker exec -it orders sh
docker stop orders && docker rm orders
docker images / docker rmi / docker system prune
docker push registry.example.com/order-service:1.0
```
`CMD` vs `ENTRYPOINT`: ENTRYPOINT defines the executable; CMD provides default arguments (overridable at `docker run`). `COPY` vs `ADD`: prefer COPY; ADD also extracts archives/fetches URLs.

## Docker Compose (local multi-container setup)
```yaml
services:
  mysql:
    image: mysql:8.4
    environment: { MYSQL_ROOT_PASSWORD: root, MYSQL_DATABASE: orders }
    ports: ["3306:3306"]
    volumes: [mysql-data:/var/lib/mysql]
    healthcheck: { test: ["CMD", "mysqladmin", "ping", "-h", "localhost"], interval: 10s }
  app:
    build: .
    ports: ["8080:8080"]
    environment:
      SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/orders
    depends_on:
      mysql: { condition: service_healthy }
volumes:
  mysql-data:
```
Spring Boot 3.1+ can start `compose.yaml` services automatically in dev (`spring-boot-docker-compose`).
'''))

NOTES.append(("Kubernetes Basics", r'''
Kubernetes (K8s) orchestrates containers across a cluster: scheduling, scaling, self-healing, service discovery, rolling updates, config and secrets.

## Architecture
- **Control plane**: API server (all interaction goes through it), etcd (cluster state store), scheduler (places pods on nodes), controller manager (reconciliation loops to reach desired state).
- **Worker nodes**: kubelet (runs pods), container runtime (containerd), kube-proxy (service networking).
- Declarative model: you describe **desired state** in YAML; controllers continuously reconcile actual state to match.

## Core objects
| Object | Purpose |
|---|---|
| **Pod** | Smallest deployable unit — one or more containers sharing network/storage. Ephemeral. |
| **ReplicaSet** | Keeps N pod replicas running. |
| **Deployment** | Manages ReplicaSets; rolling updates and rollbacks for stateless apps. |
| **Service** | Stable virtual IP/DNS name load-balancing to pods selected by labels. Types: ClusterIP (internal), NodePort, LoadBalancer (cloud LB), Headless. |
| **Ingress** / Gateway API | HTTP(S) routing from outside to services by host/path; TLS termination (NGINX ingress controller). |
| **ConfigMap / Secret** | Non-sensitive config / sensitive data (base64 — enable encryption at rest or use external secret managers). |
| **StatefulSet** | Stable identities and persistent volumes for stateful apps (DBs, Kafka). |
| **DaemonSet** | One pod per node (log agents, monitoring). |
| **Job / CronJob** | Run-to-completion tasks / scheduled tasks. |
| **HPA** | Horizontal Pod Autoscaler — scales replicas on CPU/memory/custom metrics. |
| **Namespace** | Logical isolation (dev, qa, team-a). |
| PV / PVC | Persistent storage. |

## Deployment example
```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: order-service }
spec:
  replicas: 3
  selector: { matchLabels: { app: order-service } }
  strategy: { type: RollingUpdate, rollingUpdate: { maxUnavailable: 0, maxSurge: 1 } }
  template:
    metadata: { labels: { app: order-service } }
    spec:
      containers:
        - name: app
          image: registry/order-service:1.4.2
          ports: [{ containerPort: 8080 }]
          envFrom: [{ configMapRef: { name: order-config } }, { secretRef: { name: order-secrets } }]
          resources:
            requests: { cpu: "500m", memory: "768Mi" }
            limits:   { memory: "1Gi" }
          readinessProbe: { httpGet: { path: /actuator/health/readiness, port: 8080 }, periodSeconds: 5 }
          livenessProbe:  { httpGet: { path: /actuator/health/liveness,  port: 8080 }, initialDelaySeconds: 30 }
---
apiVersion: v1
kind: Service
metadata: { name: order-service }
spec:
  selector: { app: order-service }
  ports: [{ port: 80, targetPort: 8080 }]
```

## Important behaviours
- **Requests** are used for scheduling; **limits** cap usage. Exceeding a memory limit -> OOMKilled; CPU limit -> throttling.
- **Probes**: readiness controls traffic, liveness restarts stuck containers, startup probe protects slow-starting JVMs.
- **Rolling update**: new pods start, become ready, old ones terminate — zero downtime if readiness is correct. `kubectl rollout undo` to roll back.
- **Graceful shutdown**: on termination K8s sends SIGTERM, waits `terminationGracePeriodSeconds` (30s), then SIGKILL. Enable `server.shutdown=graceful` in Spring Boot so in-flight requests complete.
- **Self-healing**: crashed pods restart; pods on failed nodes reschedule.

## kubectl essentials
```bash
kubectl get pods -n orders -o wide
kubectl describe pod <pod>            # events: ImagePullBackOff, OOMKilled, probe failures
kubectl logs -f <pod> [-c container] [--previous]
kubectl exec -it <pod> -- sh
kubectl apply -f deploy.yaml
kubectl rollout status deploy/order-service ; kubectl rollout undo deploy/order-service
kubectl scale deploy/order-service --replicas=5
kubectl port-forward svc/order-service 8080:80
```
Common errors: **CrashLoopBackOff** (app keeps crashing — check logs/--previous), **ImagePullBackOff** (wrong image/registry auth), **OOMKilled** (raise memory or fix leak/heap settings), Pending (insufficient resources).

## Packaging
**Helm** charts template K8s manifests per environment; **Kustomize** overlays. GitOps with **Argo CD**/Flux syncs cluster state from Git.
'''))

NOTES.append(("CI/CD and Deployment Strategies", r'''
## Continuous Integration
Every push/PR triggers an automated pipeline: compile, unit tests, static analysis, build artifact. Goal: catch integration problems early, keep `main` always releasable.

## Continuous Delivery vs Deployment
- **Continuous Delivery**: every change that passes the pipeline is *deployable*; release to prod needs a manual approval.
- **Continuous Deployment**: every passing change goes to production automatically.

## Typical pipeline for a Spring Boot microservice
1. **Checkout** and set up JDK, cache Maven/Gradle dependencies.
2. **Build & unit test**: `./mvnw verify` (JUnit, Mockito), coverage with JaCoCo (enforce thresholds).
3. **Static analysis & security**: SonarQube (code smells, bugs, coverage gate), dependency vulnerability scan (OWASP Dependency-Check, Snyk, GitHub Dependabot), secret scanning.
4. **Integration tests** with Testcontainers; contract tests.
5. **Build image** (Dockerfile/Jib/buildpacks), tag with git SHA/semantic version, scan the image (Trivy), push to registry.
6. **Deploy to dev/staging** (Helm upgrade or update GitOps repo -> Argo CD syncs).
7. **Smoke/E2E/performance tests** (Postman/Newman, k6/JMeter/Gatling).
8. **Approval** -> **production deploy** with a safe strategy.
9. **Post-deploy verification**: monitor error rate/latency; automatic rollback on SLO breach.

## GitHub Actions example
```yaml
name: ci
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '21', cache: maven }
      - run: ./mvnw -B verify
      - run: docker build -t ghcr.io/acme/order-service:${{ github.sha }} .
```
Other tools: Jenkins (Jenkinsfile, very common in Indian service companies), GitLab CI, Azure DevOps, AWS CodePipeline, Argo CD/Flux for GitOps.

## Deployment strategies
| Strategy | How | Pros / Cons |
|---|---|---|
| **Recreate** | Stop old, start new | Simple; downtime |
| **Rolling update** | Replace instances gradually | No downtime, K8s default; both versions run together briefly — must be backward compatible |
| **Blue-Green** | Two identical environments; switch traffic from blue (old) to green (new) at once | Instant rollback by switching back; double resources |
| **Canary** | Send a small % of traffic (1% -> 10% -> 50% -> 100%) to the new version while monitoring | Limits blast radius; needs traffic splitting (Istio, Argo Rollouts, ingress weights) and good metrics |
| **Feature flags** | Deploy code dark; enable per user/percentage at runtime (LaunchDarkly, Unleash, Togglz) | Decouples deploy from release; flag debt |
| Shadow / dark launch | Mirror production traffic to new version without returning its responses | Safe testing under real load |

## Database migrations in CD
Use **Flyway** or **Liquibase**, versioned scripts run at startup or as a pipeline step. With rolling/blue-green deployments both versions hit the same DB, so use the **expand-and-contract** pattern: (1) add new column (nullable) and write to both, (2) backfill, (3) switch reads, (4) remove old column in a later release. Never rename/drop in one step.

## Branching
Trunk-based development (short-lived branches, frequent merges, feature flags) is favoured by product companies; GitFlow (develop/release/hotfix branches) is heavier. Use PR reviews, required checks, and semantic versioning for libraries.

## Rollback plan
Keep previous image tags, `helm rollback` / `kubectl rollout undo`, backward-compatible DB changes, and feature flags as kill switches.
'''))
