from cb_common import B, I, A

QA = [
("What are microservices? What are their advantages and disadvantages compared to a monolith?", r'''
Microservices are small, independently deployable services, each owning a business capability and its own data, communicating via APIs or events.

**Advantages:** independent deployments per team, independent scaling, fault isolation, technology choice per service, smaller codebases and clear ownership.

**Disadvantages:** distributed-system complexity (network failures, latency), no simple ACID transactions across services (sagas, eventual consistency), heavy operational needs (CI/CD per service, Kubernetes, centralised logging, tracing), harder end-to-end testing and debugging, and the risk of a distributed monolith.

A monolith is simpler and faster for small teams and early products; a modular monolith is a good starting point, splitting later along proven domain boundaries.
''', B, ["architecture"], True),

("How would you decompose a monolith into microservices?", r'''
1. **Identify bounded contexts** using DDD — business capabilities like Catalog, Order, Payment, Inventory, Notification. Look at team ownership and data cohesion.
2. **Modularise first** inside the monolith: enforce package/module boundaries, remove cross-module DB joins.
3. Apply the **Strangler Fig pattern**: put an API gateway/router in front; extract the least coupled, highest-value module first (often notifications or search); route its traffic to the new service.
4. **Split the data**: the new service owns its tables; others access it via APIs/events. Use CDC/dual-write carefully during migration.
5. Introduce async events (Kafka) to decouple.
6. Add observability, CI/CD, and resilience from the start.
7. Repeat incrementally; avoid a big-bang rewrite.
''', I, ["architecture"], True),

("What is the database-per-service pattern? How do you handle queries that need data from multiple services?", r'''
Each service owns its schema; no other service reads or writes its tables directly. This enables independent evolution, deployment and scaling, and avoids hidden coupling through shared tables.

For cross-service queries:
- **API composition**: an aggregator/BFF calls multiple services and joins results in memory (simple, but latency and partial failure).
- **CQRS read model**: services publish events; a query service builds a denormalised view (e.g. Elasticsearch or a reporting DB) optimised for the query.
- **Data replication via events**: a service keeps a local read-only copy of the fields it needs (e.g. Order keeps customer name) updated from events.
- For analytics, stream data into a warehouse (CDC to BigQuery/Snowflake).
''', I, ["architecture", "data"], True),

("What is service discovery? Client-side vs server-side discovery?", r'''
Service discovery lets services find the network locations of other services whose instances change dynamically (autoscaling, restarts).

- **Service registry** (Eureka, Consul): instances register on startup and send heartbeats; unhealthy ones are evicted.
- **Client-side discovery**: the caller fetches instances from the registry and load-balances itself (Spring Cloud LoadBalancer with `lb://order-service`, Feign). Fewer hops, but discovery logic lives in each client.
- **Server-side discovery**: the caller sends requests to a router/load balancer that queries the registry (AWS ALB, Kubernetes Service). Clients stay simple.

In Kubernetes, the built-in Service + DNS (`order-service.namespace.svc`) handles discovery and load balancing, so Eureka is usually unnecessary.
''', B, ["service-discovery"], True),

("What is an API Gateway and why is it needed? What's the difference from a load balancer?", r'''
An API Gateway is the single entry point for clients. It routes requests to backend services and centralises cross-cutting concerns: authentication (JWT validation), rate limiting, SSL termination, CORS, request/response transformation, aggregation, caching, logging/metrics, and circuit breaking. It hides internal service topology from clients and enables the Backend-for-Frontend pattern.

Examples: Spring Cloud Gateway, Kong, NGINX, AWS API Gateway, Envoy.

A **load balancer** distributes traffic across instances of the same service (L4/L7), focused on availability. A **gateway** is an L7 smart router across many services with API-management features. Typically: cloud LB -> gateway (multiple replicas) -> services. Keep the gateway thin — no business logic.
''', B, ["api-gateway"], True),

("REST vs messaging (Kafka) for inter-service communication — how do you choose?", r'''
Use **synchronous REST/gRPC** when the caller needs an immediate answer to continue (validate a coupon, fetch price, check stock for display). Downsides: temporal coupling (callee must be up), latency adds up in chains, cascading failures.

Use **asynchronous messaging** for events and workflows where the caller doesn't need to wait: OrderPlaced -> inventory, notifications, analytics, loyalty points. Benefits: decoupling in time, buffering load spikes, easy fan-out to many consumers, replay (Kafka). Downsides: eventual consistency, duplicates/ordering to handle, harder debugging, broker to operate.

Most systems use both: sync for queries, async for state-change propagation. Avoid long synchronous call chains.
''', I, ["communication", "kafka"], True),

("What is Feign client? How do you configure timeouts and error handling?", r'''
OpenFeign is a declarative HTTP client: you write an annotated interface and Spring generates the implementation, integrated with service discovery and load balancing.
```java
@FeignClient(name = "payment-service", fallbackFactory = PaymentFallbackFactory.class)
public interface PaymentClient {
    @PostMapping("/api/payments") PaymentDto charge(@RequestBody ChargeRequest r);
}
```
Configure timeouts per client:
```yaml
spring.cloud.openfeign.client.config.payment-service:
  connect-timeout: 2000
  read-timeout: 5000
```
Error handling: a custom `ErrorDecoder` maps HTTP status codes to domain exceptions (404 -> `NotFoundException`, 503 -> retryable). Add a `RequestInterceptor` to forward JWT/correlation headers. Combine with Resilience4j circuit breaker and fallbacks. Spring now recommends `@HttpExchange` interface clients for new projects.
''', I, ["feign", "communication"], True),

("Explain Kafka architecture: topics, partitions, consumer groups and offsets.", r'''
- **Topic**: a named stream of events, split into **partitions** — ordered, append-only logs distributed across **brokers**. Each partition has a leader and replicas (replication factor, usually 3).
- **Producer** writes records; the record **key** determines the partition (`hash(key) % n`), so events for the same key stay ordered.
- **Consumer group**: consumers with the same `group.id` share partitions; each partition is read by only one consumer in the group, so parallelism is limited by partition count. Different groups each receive all events.
- **Offset**: a record's position in a partition. Consumers commit offsets so they can resume after restarts/rebalances.
- Messages are **retained** for a configured period regardless of consumption, allowing replay.
- Metadata is managed by KRaft (ZooKeeper removed in Kafka 4.0).
''', I, ["kafka"], True),

("How does Kafka guarantee message ordering? What happens if you need global ordering?", r'''
Kafka guarantees order **only within a partition**. To keep related events in order, use the same **message key** (e.g. `orderId`, `customerId`) so they go to the same partition, and process each partition sequentially in one consumer thread.

Producer settings matter: with retries, `max.in.flight.requests.per.connection > 1` could reorder messages unless `enable.idempotence=true` (default in modern clients), which preserves order up to 5 in-flight requests.

Global ordering across all events requires a **single partition**, which limits throughput to one consumer — usually you don't need it; per-entity ordering is enough. Increasing partition count later changes key-to-partition mapping, temporarily breaking ordering for existing keys.
''', I, ["kafka"], True),

("What delivery semantics does Kafka offer? How do you avoid duplicate processing?", r'''
- **At-most-once**: commit offset before processing; a crash loses messages.
- **At-least-once** (most common): process then commit; a crash after processing but before commit causes reprocessing -> duplicates.
- **Exactly-once**: idempotent producer (`enable.idempotence=true`) + transactions (`transactional.id`, consumer `isolation.level=read_committed`) for read-process-write pipelines within Kafka.

Producer durability: `acks=all` with `min.insync.replicas=2`.

To handle duplicates with external side effects (DB writes, emails), make consumers **idempotent**: store processed event IDs (inbox table with a unique constraint) in the same DB transaction as the business change, use upserts/conditional updates, or idempotency keys with downstream APIs.
''', A, ["kafka"], True),

("How do you handle failures and poison messages in a Kafka consumer?", r'''
- **Retry with backoff** for transient errors: Spring Kafka `DefaultErrorHandler` with `ExponentialBackOff`. Blocking retries hold up the partition, so keep them short.
- **Non-blocking retries**: `@RetryableTopic` sends failed records to retry topics with increasing delays (`orders-retry-1`, `-retry-2`), letting the main topic continue.
- **Dead Letter Topic**: after max retries, publish to `orders.DLT` with error headers (`DeadLetterPublishingRecoverer`); alert, inspect, fix, and replay.
- **Don't retry** non-transient errors (validation) — send straight to DLT.
- **Poison pills** (undeserialisable payloads): wrap deserializers in `ErrorHandlingDeserializer` so they don't crash the consumer in a loop.
- Monitor consumer lag and DLT size.
''', A, ["kafka", "resilience"], False),

("Kafka vs RabbitMQ?", r'''
| Kafka | RabbitMQ |
|---|---|
| Distributed commit log; consumers **pull** and track offsets | Message broker; **pushes** to consumers, deletes after ack |
| Messages retained for days -> replay, multiple independent consumer groups | Messages gone after consumption |
| Very high throughput, scales via partitions | Moderate throughput, lower latency for small volumes |
| Ordering per partition | Ordering per queue |
| Simple routing (topics/keys) | Rich routing: direct, topic, fanout, headers exchanges; priorities; TTL; delayed messages |
| Event streaming, event sourcing, CDC, log/metrics pipelines | Task queues, work distribution, RPC, complex routing |

Choose Kafka for event-driven architectures and high-volume streams; RabbitMQ for traditional job queues and flexible routing.
''', I, ["kafka", "messaging"], True),

("What is the circuit breaker pattern? Explain its states.", r'''
A circuit breaker wraps calls to a remote dependency and stops calling it when it's failing, so you fail fast instead of tying up threads and the dependency gets time to recover.

States (Resilience4j):
- **CLOSED** — normal; calls pass; outcomes recorded in a sliding window.
- **OPEN** — failure or slow-call rate exceeded the threshold (e.g. 50% of last 20 calls); calls are rejected immediately (`CallNotPermittedException`) and the fallback runs, for a configured wait duration.
- **HALF_OPEN** — after the wait, a few trial calls are allowed; success -> CLOSED, failure -> OPEN.

```java
@CircuitBreaker(name = "inventory", fallbackMethod = "fallback")
public Stock check(String sku) { return client.stock(sku); }
Stock fallback(String sku, Throwable t) { return Stock.unknown(sku); }
```
Fallbacks: cached data, default response, or graceful degradation.
''', I, ["resilience", "resilience4j"], True),

("What are retry, bulkhead and rate limiter patterns? How do they work together?", r'''
- **Retry**: re-attempt transient failures with exponential backoff + jitter; only for idempotent operations; cap attempts and don't retry 4xx.
- **Bulkhead**: limit concurrent calls (semaphore) or give each dependency its own thread pool so one slow service can't exhaust all threads.
- **Rate limiter**: cap calls per time window, to respect a partner's quota or protect your service.
- **Time limiter**: bound how long a call may take.

Together: the time limiter bounds each attempt, the circuit breaker records outcomes and fails fast when the dependency is unhealthy, retry wraps the breaker for transient blips, and the bulkhead caps concurrency. In Resilience4j's default aspect order, Retry is outermost: Retry(CircuitBreaker(RateLimiter(TimeLimiter(Bulkhead(call))))). Avoid retrying at every layer — retries multiply load (retry storms).
''', I, ["resilience"], True),

("How do you handle distributed transactions in microservices?", r'''
Avoid distributed ACID (2PC/XA) — it's blocking, slow, and the coordinator is a single point of failure; most brokers and NoSQL stores don't support it.

Instead:
- **Saga pattern**: break the operation into local transactions per service; each step publishes an event/command; failures trigger **compensating transactions** (refund, release stock). Implemented via choreography (events) or orchestration (central coordinator like Temporal/Camunda).
- **Transactional outbox**: write the business change and the outgoing event in the same local DB transaction; a relay (poller or Debezium CDC) publishes to Kafka — fixes the dual-write problem.
- **Idempotent consumers** for at-least-once delivery.
- Accept **eventual consistency** and model intermediate states (`PENDING`, `PAYMENT_FAILED`).
Keep strongly consistent invariants inside a single service boundary where possible.
''', A, ["saga", "transactions"], True),

("Explain the Saga pattern: choreography vs orchestration with an e-commerce example.", r'''
Order flow: create order -> reserve inventory -> charge payment -> confirm.

**Choreography**: no central controller.
OrderService saves order `PENDING`, emits `OrderCreated` -> InventoryService reserves, emits `StockReserved` -> PaymentService charges, emits `PaymentCompleted` -> OrderService marks `CONFIRMED`. If payment fails, `PaymentFailed` -> Inventory releases stock and Order is `CANCELLED`.
Pros: loose coupling, simple for 2-4 steps. Cons: flow is implicit and hard to trace; cyclic event dependencies.

**Orchestration**: an `OrderSagaOrchestrator` sends commands (`ReserveStock`, `ChargePayment`) and handles replies, persisting saga state; on failure it issues compensations (`ReleaseStock`).
Pros: explicit flow, centralised timeouts/retries/monitoring. Cons: an extra component that can become too smart.

Compensations must be idempotent and retryable; sagas lack isolation, so use status flags (semantic locks).
''', A, ["saga"], True),

("What is the Transactional Outbox pattern and why is it needed?", r'''
Problem: a service must update its DB **and** publish an event. Doing both separately (dual write) is unsafe — if the app crashes after the DB commit but before `kafka.send`, the event is lost; if you send first and the DB commit fails, you publish a lie.

Solution: in the **same local transaction**, insert the business row and an `outbox` row (aggregate id, event type, payload). A separate relay publishes outbox rows to Kafka and marks them sent:
- **Polling publisher**: scheduled job reading unsent rows (`FOR UPDATE SKIP LOCKED`).
- **CDC**: Debezium tails the MySQL binlog and streams outbox inserts to Kafka (Outbox Event Router).

This guarantees **at-least-once** publishing, so consumers must be idempotent (inbox table / dedupe by event id). Clean up old outbox rows periodically.
''', A, ["outbox", "kafka"], True),

("What is idempotency and how do you implement an idempotent payment API?", r'''
An operation is idempotent if performing it multiple times has the same effect as once. Networks fail and clients/gateways retry, so non-idempotent POSTs (payments, orders) can be duplicated.

Implementation:
1. Client generates a unique `Idempotency-Key` (UUID) per logical operation and sends it in a header.
2. Server checks a store (DB table with a unique key or Redis `SETNX` with TTL):
   - Key absent -> insert key with status `IN_PROGRESS`, process, store the response with status `DONE`.
   - Key present and `DONE` -> return the stored response without reprocessing.
   - Key present and `IN_PROGRESS` -> return 409/202 (or wait).
3. Validate that the same key isn't reused with a different payload (store a request hash).
4. Downstream calls (to a payment gateway) also pass idempotency keys.
A unique DB constraint is the final safety net against races.
''', A, ["idempotency", "api-design"], True),

("What is Spring Cloud Config Server? How do you refresh configuration without restart?", r'''
Config Server centralises externalised configuration for all services, typically backed by a Git repo (also Vault, JDBC). Clients fetch config by `application name` + `profile` + `label` (branch) at startup via `spring.config.import=configserver:http://config:8888`. Benefits: single source of truth, versioning/audit via Git, per-environment overrides, encrypted secrets (`{cipher}`).

Refresh at runtime:
- Annotate beans with `@RefreshScope` (and `@ConfigurationProperties` beans rebind automatically).
- Call `POST /actuator/refresh` on an instance to reload.
- For all instances, use **Spring Cloud Bus** (Kafka/RabbitMQ) and `/actuator/busrefresh`, often triggered by a Git webhook.
In Kubernetes, ConfigMaps/Secrets with Spring Cloud Kubernetes or a rolling restart are common alternatives.
''', I, ["config"], False),

("What is distributed tracing and how do you implement it in Spring Boot 3?", r'''
Distributed tracing follows a request across services. A **trace** (unique `traceId`) consists of **spans** (each unit of work: an HTTP call, DB query, Kafka publish) with timings and parent-child relationships. Trace context is propagated via headers (W3C `traceparent`).

Spring Boot 3: add Actuator + **Micrometer Tracing** with a bridge (OpenTelemetry or Brave) + an exporter (Zipkin, Jaeger, Tempo, or OTLP to a vendor):
```xml
<dependency><groupId>io.micrometer</groupId><artifactId>micrometer-tracing-bridge-otel</artifactId></dependency>
<dependency><groupId>io.opentelemetry</groupId><artifactId>opentelemetry-exporter-zipkin</artifactId></dependency>
```
```yaml
management.tracing.sampling.probability: 0.1
```
RestClient/WebClient/Kafka templates built from Spring's auto-configured builders propagate context automatically, and `traceId`/`spanId` are added to logs via MDC. (Spring Cloud Sleuth was the Boot 2 equivalent.) Use it to find which service/span causes latency.
''', I, ["observability", "tracing"], True),

("How do you implement centralised logging and monitoring for microservices?", r'''
**Logging**: services write structured JSON logs to stdout with `traceId`, service name and level; an agent (Fluent Bit/Filebeat) ships them to Elasticsearch/Loki; Kibana/Grafana for search. Correlate with trace IDs, mask PII.

**Metrics**: Micrometer + Actuator expose `/actuator/prometheus`; Prometheus scrapes; Grafana dashboards for golden signals (latency p95/p99, traffic, errors, saturation), JVM, connection pools, Kafka lag, circuit breaker states. Alertmanager/PagerDuty alerts on SLO breaches.

**Tracing**: Micrometer Tracing/OpenTelemetry -> Zipkin/Jaeger/Tempo.

**Health**: Actuator liveness/readiness for Kubernetes probes.

Together these let you go from an alert -> dashboard -> slow trace -> logs for that trace -> root cause.
''', I, ["observability"], True),

("What is the difference between Docker image and container? VM vs container?", r'''
- **Image**: an immutable, layered template (filesystem + metadata) built from a Dockerfile and stored in a registry.
- **Container**: a running instance of an image with its own writable layer, process namespace, network and resource limits. Many containers can run from one image.

**VM vs container**: a VM virtualises hardware and runs a full guest OS on a hypervisor — strong isolation but GBs in size and minutes to boot. A container shares the host kernel, isolating processes with namespaces and limiting resources with cgroups — MBs in size, starts in seconds, higher density. Isolation is weaker than VMs, so run as non-root, use minimal images and scan them.
''', B, ["docker"], True),

("How do you write an optimised Dockerfile for a Spring Boot application?", r'''
```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY pom.xml mvnw ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline
COPY src src
RUN ./mvnw package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app
RUN useradd -r appuser
COPY --from=build /app/target/*.jar app.jar
USER appuser
EXPOSE 8080
ENTRYPOINT ["java","-XX:MaxRAMPercentage=75","-jar","app.jar"]
```
Practices: **multi-stage** (no JDK/Maven in final image), copy `pom.xml` before `src` for layer caching, Spring Boot **layered jars** to cache dependencies separately, minimal JRE/distroless base, pinned versions, non-root user, `.dockerignore`, container-aware heap (`MaxRAMPercentage`), exec-form ENTRYPOINT so the JVM receives SIGTERM for graceful shutdown. Alternatives: `spring-boot:build-image` (buildpacks) or Jib.
''', I, ["docker"], True),

("Explain core Kubernetes objects: Pod, Deployment, Service, Ingress, ConfigMap, Secret.", r'''
- **Pod**: smallest deployable unit; one or more containers sharing an IP and volumes. Ephemeral.
- **Deployment**: declares desired replicas and pod template; manages ReplicaSets for rolling updates and rollbacks of stateless apps.
- **Service**: stable DNS name/virtual IP that load-balances to pods matching a label selector (ClusterIP internal, NodePort, LoadBalancer external).
- **Ingress**: L7 HTTP routing from outside the cluster to Services by host/path, with TLS (needs an ingress controller like NGINX).
- **ConfigMap**: non-sensitive configuration injected as env vars or files.
- **Secret**: sensitive data (passwords, keys), base64-encoded — enable encryption at rest or use external secret managers.
Also: StatefulSet (databases), HPA (autoscaling), Job/CronJob, Namespace.
''', B, ["kubernetes"], True),

("What are liveness, readiness and startup probes?", r'''
- **Liveness probe**: "Is the container alive?" If it fails repeatedly, kubelet **restarts** the container. Should check only the app itself (not the DB), otherwise a DB outage restarts all pods.
- **Readiness probe**: "Can it serve traffic now?" If failing, the pod is **removed from Service endpoints** but not restarted. Use for warm-up, dependency availability, or during graceful shutdown.
- **Startup probe**: protects slow-starting apps (JVM warm-up); liveness/readiness checks are disabled until it succeeds.

Spring Boot Actuator provides `/actuator/health/liveness` and `/actuator/health/readiness` (auto-enabled on Kubernetes). Combined with `server.shutdown=graceful`, they enable zero-downtime rolling deployments.
''', I, ["kubernetes"], True),

("How does Kubernetes autoscaling work? What are requests and limits?", r'''
- **Requests**: resources guaranteed to a container; the scheduler places pods on nodes with enough unreserved capacity.
- **Limits**: hard caps. Exceeding memory limit -> container **OOMKilled**; exceeding CPU limit -> throttled. Many teams set memory limit = request and omit CPU limits to avoid throttling.

**HPA (Horizontal Pod Autoscaler)** adjusts replica count to keep a metric near target — e.g. average CPU at 70% of requests, or custom metrics (requests/sec, Kafka lag via KEDA).
**VPA** adjusts requests/limits. **Cluster Autoscaler/Karpenter** adds nodes when pods are pending.

For JVM apps, set heap via `-XX:MaxRAMPercentage=75` so heap + metaspace + threads fit under the memory limit, and account for slow JVM warm-up when scaling.
''', I, ["kubernetes"], False),

("A pod is in CrashLoopBackOff. How do you debug it?", r'''
CrashLoopBackOff means the container starts, exits, and Kubernetes keeps restarting it with increasing backoff.

Steps:
1. `kubectl describe pod <pod>` — check events, exit code, last state (`OOMKilled` = exit 137, probe failures, missing ConfigMap/Secret).
2. `kubectl logs <pod> --previous` — logs from the crashed container (Spring startup exception, e.g. can't connect to DB, missing property, port conflict).
3. Verify env vars/secrets/config, image tag, and command/entrypoint.
4. Check probes: an aggressive liveness probe can kill a slow-starting JVM — add a startup probe or increase `initialDelaySeconds`.
5. Check resources: memory limit too low for heap -> raise limit or tune `MaxRAMPercentage`.
6. Reproduce locally with the same image (`docker run` with same env).
''', I, ["kubernetes", "debugging"], True),

("What is CI/CD? Describe a pipeline you would set up for a Spring Boot microservice.", r'''
**CI**: every commit is built and tested automatically. **CD**: every change that passes is deployable (delivery) or deployed automatically (deployment).

Pipeline (Jenkins/GitHub Actions/GitLab):
1. Checkout, set up JDK, cache dependencies.
2. `mvn verify` — compile, unit tests, JaCoCo coverage gate.
3. SonarQube quality gate; dependency (OWASP/Snyk) and secret scanning.
4. Integration tests with Testcontainers; contract tests.
5. Build Docker image tagged with the commit SHA; scan with Trivy; push to ECR/registry.
6. Deploy to staging via Helm/Argo CD; run smoke and API tests.
7. Manual approval (or automatic) -> production with rolling/canary strategy.
8. Monitor metrics; automatic rollback on errors.
Flyway migrations run as part of deployment using expand-and-contract.
''', I, ["cicd"], True),

("Explain blue-green, canary and rolling deployments.", r'''
- **Rolling**: replace instances gradually (Kubernetes default). No downtime, no extra full environment; old and new versions run simultaneously, so changes must be backward compatible. Rollback is another rollout.
- **Blue-Green**: run two identical environments; deploy to idle **green**, test it, then switch the router from **blue** to green instantly. Rollback = switch back. Costs double resources; DB schema must work for both.
- **Canary**: route a small percentage of real traffic (1-5%) to the new version, watch error rates/latency, then progressively increase to 100%; abort automatically if metrics degrade. Needs traffic splitting (Istio, Argo Rollouts, weighted ingress) and good observability.
- **Feature flags** complement these by decoupling deployment from release.
''', I, ["cicd", "deployment"], True),

("What is eventual consistency? How do you explain it to a product manager?", r'''
In eventual consistency, after an update, different parts of the system may temporarily show different values, but if no new updates occur, all copies converge to the same value — usually within milliseconds to seconds.

It arises when services own separate databases and propagate changes asynchronously (events), or with replicated databases/caches. It trades immediate consistency for availability, scalability and decoupling (CAP theorem).

PM explanation: "When a customer places an order, the order is saved immediately and shows as 'Processing'. Inventory and loyalty points update a second or two later. If payment fails, the order is automatically cancelled and stock released." Design the UX with intermediate states, and keep strongly consistent operations (wallet balance) within one service's transaction.
''', I, ["data", "architecture"], False),

("What is the CAP theorem?", r'''
In a distributed data store, when a **network partition** (P) occurs, you can guarantee either **Consistency** (every read sees the latest write or gets an error) or **Availability** (every request gets a non-error response, possibly stale) — not both. Partitions are unavoidable in distributed systems, so the real choice is CP vs AP during a partition.

- **CP**: ZooKeeper/etcd, HBase, MongoDB with majority writes, traditional RDBMS clusters with synchronous replication — may reject requests to stay consistent.
- **AP**: Cassandra, DynamoDB (default), Couchbase — stay available and reconcile later.

**PACELC** extends it: Else (no partition), choose between Latency and Consistency. For microservices: use strong consistency for money/inventory within a service; accept eventual consistency across services.
''', I, ["distributed-systems"], True),

("How do you secure communication between microservices?", r'''
- **Edge authentication**: the API gateway validates user JWTs (from an identity provider like Keycloak/Auth0/Cognito) and forwards them or a derived token.
- **Service-level authorisation**: each service is an OAuth2 resource server validating the JWT signature, issuer, audience and scopes — zero trust, don't rely solely on the gateway.
- **Service-to-service identity**: OAuth2 **client credentials** tokens, or **mTLS** (mutual TLS) — often handled by a service mesh (Istio/Linkerd) that issues and rotates certificates automatically.
- **Network policies** in Kubernetes to restrict which pods can talk.
- **Secrets** in Vault/Kubernetes Secrets/cloud secret managers, never in code.
- TLS everywhere, input validation, rate limiting, and audit logging.
''', I, ["security"], True),

("How would you implement rate limiting in a distributed system?", r'''
Algorithms:
- **Token bucket**: tokens refill at a fixed rate up to a capacity; each request consumes one. Allows bursts. Most common.
- **Leaky bucket**: processes at a constant rate; smooths traffic.
- **Fixed window counter**: count per minute window — simple but bursty at boundaries.
- **Sliding window log/counter**: more accurate.

Distributed implementation: keep counters in **Redis** so all gateway instances share state — atomic `INCR` + `EXPIRE` or a Lua script implementing token bucket (Spring Cloud Gateway's `RequestRateLimiter` uses Redis). Key by user id, API key, or IP. Return **429 Too Many Requests** with `Retry-After` and `X-RateLimit-*` headers.

Apply at the gateway for clients; use Resilience4j `RateLimiter` client-side to respect partner API quotas.
''', A, ["rate-limiting", "api-gateway"], True),

("What is the Strangler Fig pattern?", r'''
A strategy for incrementally migrating a legacy monolith to a new architecture without a risky big-bang rewrite. Named after a fig vine that gradually envelops a tree.

Steps:
1. Put a facade (API gateway/reverse proxy) in front of the monolith; all traffic flows through it.
2. Build a new service for one capability (e.g. notifications).
3. Route that capability's endpoints to the new service; the rest still go to the monolith.
4. Migrate data ownership (sync via CDC/events during transition).
5. Repeat until the monolith is empty or small enough, then retire it.

Benefits: continuous delivery of value, low risk, easy rollback by re-routing. Watch out for long-lived dual-write periods and shared database coupling.
''', I, ["architecture", "migration"], False),

("What is CQRS and event sourcing? When would you use them?", r'''
- **CQRS (Command Query Responsibility Segregation)**: separate the write model (commands, validation, transactions on a normalised DB) from read models (queries served from denormalised stores like Elasticsearch, Redis or materialised views). Read models are updated from events. Use when read and write loads/shapes differ greatly — e.g. product search over a catalog, dashboards. Cost: eventual consistency and more moving parts.
- **Event sourcing**: instead of storing current state, store an append-only log of domain events (`MoneyDeposited`, `MoneyWithdrawn`); current state = replay (with snapshots for speed). Gives a full audit trail and time travel; natural fit for ledgers/banking. Cost: complexity, event schema evolution, harder queries (usually needs CQRS).
Don't use either for simple CRUD services.
''', A, ["cqrs", "architecture"], False),

("What is a service mesh? Do you need one?", r'''
A service mesh (Istio, Linkerd, Consul Connect) adds a **sidecar proxy** (often Envoy) to every pod, intercepting all network traffic. A control plane configures proxies to provide:
- mTLS encryption and service identity automatically
- Retries, timeouts, circuit breaking at the network layer
- Traffic shifting (canary, A/B), fault injection
- Uniform metrics and tracing without code changes
- Fine-grained access policies

You need one when you have many services in multiple languages and want consistent security/traffic policies without library code. For a few Spring Boot services, Resilience4j + Micrometer + Kubernetes NetworkPolicies are often enough; a mesh adds operational complexity, resource overhead and latency. Ambient (sidecar-less) modes reduce overhead.
''', I, ["service-mesh", "kubernetes"], False),

("How do you handle versioning and backward compatibility of APIs and events between services?", r'''
- **Additive changes only**: add optional fields; never remove/rename or change types in place. Consumers ignore unknown fields (tolerant reader).
- **Version when breaking**: `/v2/` endpoints or new event types (`OrderPlacedV2`), run both until consumers migrate, then deprecate.
- **Schema registry** (Confluent/Apicurio) with Avro/Protobuf for Kafka events enforces compatibility rules (backward/forward) at publish time.
- **Consumer-driven contract tests** (Pact, Spring Cloud Contract) in CI catch breaking changes before deployment.
- **Expand-and-contract** for DB schemas.
- Communicate deprecation timelines and monitor usage of old versions before removal.
''', A, ["api-design", "kafka"], False),

("How do you make a microservice handle a sudden 10x traffic spike (e.g. a flash sale)?", r'''
- **Horizontal scaling**: stateless services + HPA; pre-scale before known events (warm JVMs).
- **Caching**: CDN for static content, Redis for hot product/price data, local Caffeine for reference data.
- **Queue-based load levelling**: accept orders quickly into Kafka and process asynchronously at a sustainable rate.
- **Rate limiting and load shedding** at the gateway; virtual waiting rooms.
- **Protect the database**: read replicas, connection pool limits, avoid N+1, indexes; atomic inventory decrements (`UPDATE ... WHERE qty > 0`) or Redis counters with Lua for stock.
- **Resilience**: timeouts, circuit breakers, bulkheads; degrade non-critical features (recommendations off).
- **Load test** beforehand (k6/Gatling) and monitor saturation dashboards during the event.
''', A, ["scalability", "scenario"], True),
]

QA += [
("What is the Backend-for-Frontend (BFF) pattern and API composition?", r'''
**API composition**: a component (gateway, aggregator service) calls several services and combines their responses into one, e.g. an order-details page needing order, customer, shipment and payment data. Call downstream services **in parallel** (CompletableFuture/WebClient `Mono.zip`), set timeouts, and return partial results with fallbacks if a non-critical service fails.

**BFF**: a separate backend per client type (web, mobile, partner API), each shaping data for its UI — mobile gets compact payloads and fewer round trips, web gets richer data. Each BFF is owned by the frontend team that uses it. It prevents a one-size-fits-all gateway from bloating with client-specific logic.

Trade-offs: more services to maintain and possible duplicated logic across BFFs; keep business rules in domain services, not in the BFF.
''', I, ["api-gateway", "architecture"], False),

("How do you achieve graceful shutdown and zero-downtime deployments for a Spring Boot service?", r'''
1. `server.shutdown=graceful` and `spring.lifecycle.timeout-per-shutdown-phase=30s`: on SIGTERM, Tomcat stops accepting new requests and lets in-flight requests finish.
2. Readiness probe flips to OUT_OF_SERVICE during shutdown so Kubernetes removes the pod from Service endpoints. A small `preStop` sleep (5-10s) covers the endpoint propagation delay.
3. Use exec-form `ENTRYPOINT` so the JVM (PID 1) actually receives SIGTERM.
4. Kafka consumers: stop polling, finish the current batch and commit offsets (Spring Kafka handles this on context close).
5. Rolling update with `maxUnavailable: 0` and correct readiness probes so new pods take traffic only when ready.
6. Backward-compatible APIs and DB migrations (expand-and-contract), because old and new versions run together during the rollout.
''', I, ["kubernetes", "deployment"], True),
]
