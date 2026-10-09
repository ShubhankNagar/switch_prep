from sd_common import *

topics = []

topics.append(T("message-queues", "Message Queues and Event Streaming (Kafka vs RabbitMQ)", "Intermediate",
"How asynchronous messaging decouples services, absorbs spikes and enables retries; Kafka vs RabbitMQ, delivery semantics, ordering, and idempotent consumers.",
r'''
## Why queues

A message queue lets a **producer** hand off work to a **consumer** without waiting. Benefits:

- **Decoupling**: Order service publishes `OrderPlaced`; email, invoice, analytics and loyalty services consume it independently. Adding a consumer needs no change in the producer.
- **Absorbing spikes (load levelling)**: a flash sale produces 50k orders/s; downstream workers process at their own pace from the backlog.
- **Reliability and retries**: if the email provider is down, messages wait and are retried.
- **Lower latency for users**: the API returns as soon as the message is durably queued.

Cost: eventual consistency, harder debugging, duplicate messages, ordering issues, one more system to operate.

## Two models

### Message queue (point-to-point): RabbitMQ, ActiveMQ, Amazon SQS
A message is delivered to one consumer, acknowledged, then deleted. Workers compete for messages. Ideal for **task distribution**: send this email, resize this image.

### Log-based streaming (publish-subscribe): Apache Kafka, Pulsar, Kinesis
Messages are appended to a durable, ordered **log** and retained (days or forever). Many independent **consumer groups** read the same stream at their own pace, each tracking its own **offset**. Consumers can replay history.

## Kafka essentials

```text
Topic "orders" (3 partitions, replication factor 3)
  P0: [m0][m1][m2][m3] ...   leader on broker 1, followers on 2,3
  P1: [m0][m1][m2] ...       leader on broker 2
  P2: [m0][m1] ...           leader on broker 3

Consumer group "email-svc":  C1 <- P0, C2 <- P1, C3 <- P2
Consumer group "analytics":  A1 <- P0,P1,P2 (independent offsets)
```

- **Topic** split into **partitions**; each partition is an ordered, append-only log stored on disk.
- **Ordering is guaranteed only within a partition.** Choose the message key (e.g., `orderId`, `userId`) so related events go to the same partition: `partition = hash(key) % numPartitions`.
- **Consumer group**: each partition is consumed by exactly one consumer in the group, so parallelism ≤ number of partitions. Plan partitions for peak throughput (e.g., 30-100).
- **Offsets**: the consumer commits its position; after a crash, it resumes from the last committed offset.
- **Durability**: `acks=all` + `min.insync.replicas=2` + replication factor 3 means a write is acknowledged only after 2 replicas have it.
- **Throughput**: sequential disk I/O, batching, zero-copy transfer: hundreds of MB/s per broker.
- Retention is time/size based; **log compaction** keeps the latest value per key (useful for state/changelogs).

## RabbitMQ essentials

- Producers publish to **exchanges** (direct, topic, fanout, headers) which route to **queues** via bindings.
- Consumers receive pushed messages and **ack**; unacked messages are redelivered.
- Rich routing, per-message TTL, priorities, delayed messages (plugin), **dead letter exchanges**.
- Messages are typically removed once consumed; not designed for replay or very long retention.

## Kafka vs RabbitMQ

| | Kafka | RabbitMQ |
|---|---|---|
| Model | Distributed commit log | Broker with queues |
| Retention | Retained, replayable | Deleted after ack |
| Ordering | Per partition | Per queue (with single consumer) |
| Throughput | Very high (millions/s cluster) | High (tens of thousands/s per node) |
| Consumers | Pull, track own offset | Push, broker tracks acks |
| Routing | Topic + key only | Flexible exchanges |
| Best for | Event streaming, CDC, analytics pipelines, event sourcing, many consumers of same data | Task queues, complex routing, request/reply, per-message priority/delay |

Interview shortcut: **"Many consumers, replay, high volume, ordering by key → Kafka. Job queue with routing, retries, priorities → RabbitMQ/SQS."**

## Delivery semantics

- **At-most-once**: commit offset before processing; a crash loses the message. Fine for metrics sampling.
- **At-least-once** (the practical default): process, then commit/ack. A crash after processing but before commit causes **redelivery**, i.e., duplicates.
- **Exactly-once**: Kafka supports exactly-once within Kafka (idempotent producer + transactions for read-process-write between topics). End-to-end exactly-once with external side effects (sending an SMS, charging a card) is not possible from the broker alone; you get **effectively-once** by combining at-least-once delivery with **idempotent consumers**.

## Idempotent consumers

Make processing a message twice have the same effect as once:

```java
@KafkaListener(topics = "payments")
@Transactional
public void handle(PaymentEvent e) {
    // processed_messages has PRIMARY KEY(message_id)
    int inserted = jdbc.update(
        "INSERT IGNORE INTO processed_messages(message_id) VALUES (?)", e.getId());
    if (inserted == 0) return;            // duplicate, skip
    walletService.credit(e.getUserId(), e.getAmount());
}
```

Other techniques: natural idempotency (`SET status='SHIPPED'` is idempotent; `balance = balance + 10` is not), upserts, conditional updates with version numbers, unique constraints on business keys.

## Reliability patterns

- **Retries with exponential backoff** and a **dead letter queue (DLQ)** for messages that keep failing (poison messages). Alert on DLQ growth. Spring Kafka offers `@RetryableTopic`.
- **Transactional outbox**: write the business row and an `outbox` row in the same DB transaction; a relay (polling or Debezium CDC) publishes to Kafka. Avoids the dual-write problem where the DB commit succeeds but publishing fails (or vice versa).
- **Consumer lag monitoring**: lag = latest offset − committed offset. Autoscale consumers on lag (KEDA).
- **Backpressure**: bounded queues; producers slow down or shed load when consumers can't keep up.
- **Schema management**: Avro/Protobuf with a schema registry for compatible evolution.

## Ordering pitfalls

- Global ordering requires one partition, which kills parallelism. Usually you only need per-entity ordering (per order, per chat), so key by entity.
- Retries can reorder messages; for strict per-key order, retry in place (block that partition) or use version numbers so consumers ignore older events.

## Typical uses in designs

- Notifications fan-out, email/SMS sending.
- Order pipeline: payment → inventory → shipment events.
- Activity streams and analytics into a data lake.
- CDC from MySQL to Elasticsearch/caches.
- Buffering writes (likes, views) and aggregating in batches.
- Ride location updates streamed to matching services.

## Interview phrasing

"The checkout API writes the order and an outbox row in one MySQL transaction, Debezium publishes OrderPlaced to Kafka keyed by orderId (order preserved per order). Inventory, notification and analytics are separate consumer groups. Consumers are at-least-once and idempotent via a processed-message table; failures go to a retry topic, then a DLQ with alerts."
''',
["Queues decouple services, absorb spikes, enable retries, cut user latency",
 "RabbitMQ/SQS: task queues, deleted after ack, flexible routing",
 "Kafka: partitioned durable log, consumer groups, offsets, replay",
 "Kafka ordering only within a partition; key by entity id",
 "Parallelism in a consumer group ≤ number of partitions",
 "At-least-once + idempotent consumer = effectively once",
 "Outbox pattern solves the DB + publish dual-write problem",
 "Use retries with backoff, DLQ, and monitor consumer lag"],
[("Kafka vs RabbitMQ: when would you use each?",
 "Kafka is a distributed log: messages are retained, many consumer groups read independently, it supports replay and very high throughput with per-partition ordering. I'd use it for event streaming, CDC, analytics pipelines and fan-out of domain events. RabbitMQ is a traditional broker with flexible routing, acknowledgements, priorities and delayed messages, where messages disappear after consumption. I'd use it (or SQS) for job/task queues and complex routing."),
 ("How does Kafka guarantee ordering?",
 "Kafka guarantees order only within a partition. Producers choose a key, and all messages with the same key hash to the same partition, so they're stored and consumed in order by one consumer in the group. To keep order for an order's lifecycle events, use orderId as key. Enable the idempotent producer so retries don't reorder or duplicate within a partition. Global ordering requires a single partition, which limits throughput."),
 ("What is exactly-once delivery and is it achievable?",
 "Exactly-once means each message affects the system once. Kafka provides exactly-once semantics for read-process-write within Kafka using idempotent producers and transactions. But when consumers cause external side effects (DB writes, payments, SMS), the broker can't guarantee it. In practice we use at-least-once delivery and make consumers idempotent, using deduplication tables, unique constraints or conditional updates, achieving effectively-once processing."),
 ("What is the transactional outbox pattern?",
 "It solves the dual-write problem: updating the DB and publishing to a broker aren't atomic, so one can succeed while the other fails. Instead, the service writes the business change and an event row into an outbox table in the same local transaction. A separate relay, either a poller or CDC with Debezium reading the binlog, publishes outbox rows to Kafka and marks them sent. Delivery is at-least-once, so consumers must be idempotent."),
 ("How do you handle a message that keeps failing?",
 "Retry a limited number of times with exponential backoff, ideally via retry topics so the main partition isn't blocked. After the limit, move it to a dead letter queue with error details, alert on DLQ growth, and provide tooling to inspect, fix and replay. Distinguish transient errors (timeouts, retry) from permanent ones (validation, send straight to DLQ)."),
 ("How would you scale consumers when lag increases?",
 "Add consumer instances to the group, up to the number of partitions, since each partition is consumed by one group member. If already at the limit, increase partitions (noting that key-to-partition mapping changes for new messages) or optimise processing with batching and async I/O. Autoscale on consumer lag using tools like KEDA, and check whether a slow downstream such as the DB is the real bottleneck.")],
[("Apache Kafka documentation", "https://kafka.apache.org/documentation/"), ("RabbitMQ tutorials", "https://www.rabbitmq.com/tutorials"), ("microservices.io - Transactional outbox", "https://microservices.io/patterns/data/transactional-outbox.html"), ("Confluent - Exactly-once semantics", "https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/"), DDIA]))

topics.append(T("api-design", "API Design: REST, gRPC, GraphQL and Real-Time Protocols", "Intermediate",
"Designing clean, evolvable APIs: REST conventions, pagination, versioning, idempotency, and when to use gRPC, GraphQL, WebSockets, SSE or long polling.",
r'''
## REST basics done right

REST models the system as **resources** identified by URLs, manipulated with HTTP methods.

| Method | Use | Idempotent? | Example |
|---|---|---|---|
| GET | Read | Yes | `GET /v1/orders/123` |
| POST | Create / action | No | `POST /v1/orders` |
| PUT | Replace entire resource | Yes | `PUT /v1/users/42` |
| PATCH | Partial update | Not necessarily | `PATCH /v1/users/42 {"name":"Raj"}` |
| DELETE | Remove | Yes | `DELETE /v1/cart/items/9` |

Guidelines:
- Nouns, plural, hierarchical: `/users/42/orders`, not `/getOrdersOfUser`.
- Actions that don't fit CRUD: `POST /v1/orders/123/cancel`.
- Correct status codes: 200 OK, 201 Created (with `Location`), 202 Accepted (async), 204 No Content, 400 validation, 401 unauthenticated, 403 forbidden, 404, 409 conflict (version mismatch, duplicate), 422, 429 rate limited, 500, 503 (with `Retry-After`).
- Consistent error body: `{"code":"INSUFFICIENT_STOCK","message":"...","traceId":"..."}`.
- Filtering/sorting via query params: `GET /v1/products?category=phones&sort=-price`.

## Idempotency for unsafe operations

Networks fail; clients retry. A retried `POST /payments` must not charge twice. Pattern: the client sends an `Idempotency-Key: <uuid>` header. The server stores key → result (in Redis or a DB table with a unique constraint, TTL 24h). On a repeat with the same key, return the stored result instead of re-executing. Stripe and Razorpay APIs work this way.

```text
POST /v1/payments
Idempotency-Key: 7f9c...e1
{"orderId": 991, "amount": 49900, "currency": "INR"}
```

## Pagination

### Offset pagination
`GET /products?page=500&size=20` → `LIMIT 20 OFFSET 9980`.
Simple, supports jumping to page N. But MySQL still reads and discards 9,980 rows, so it gets slow for deep pages, and inserts during browsing cause duplicates/skips.

### Cursor (keyset) pagination
`GET /feed?limit=20&cursor=eyJpZCI6MTIzNDV9` where the cursor encodes the last seen sort key.
```sql
SELECT * FROM posts WHERE user_id = ? AND id < :lastId ORDER BY id DESC LIMIT 20;
```
Constant time per page using the index, stable under inserts. Can't jump to arbitrary pages. **Use cursor pagination for feeds, chats, infinite scroll, and large tables.** Return `nextCursor` in the response.

## Versioning

APIs evolve; mobile apps stay installed for years.
- **URI versioning**: `/v1/orders`, `/v2/orders`. Most common, explicit, cache-friendly.
- **Header versioning**: `Accept: application/vnd.myapp.v2+json`.
- **Query param**: `?version=2`.

Prefer **backward-compatible changes** (add optional fields, never remove/rename, don't change meaning). Bump the major version only for breaking changes, and run old and new in parallel with a deprecation timeline.

## Other API concerns

- **Authentication** via `Authorization: Bearer <JWT>`; rate limits per API key/user (429).
- **Request validation** (Bean Validation `@Valid`), size limits.
- **Compression** (gzip/brotli), **caching** with `ETag`/`If-None-Match` and `Cache-Control`.
- **HATEOAS**: rarely required in interviews.
- **Async APIs**: long jobs return `202 Accepted` with a status URL or a webhook callback.
- **Documentation**: OpenAPI/Swagger (springdoc).

## gRPC

An RPC framework using **Protocol Buffers** (binary, schema-first) over **HTTP/2**.

```text
service OrderService {
  rpc GetOrder (GetOrderRequest) returns (Order);
  rpc StreamUpdates (OrderId) returns (stream OrderEvent);
}
```

- Pros: compact binary payloads (often 3-10x smaller than JSON), fast serialization, strongly typed generated clients, HTTP/2 multiplexing, built-in streaming (client, server, bidirectional), deadlines.
- Cons: not human-readable, limited direct browser support (needs gRPC-Web), harder debugging, load balancers must handle long-lived HTTP/2 connections (use L7/client-side balancing).
- Use for **internal service-to-service** calls with high volume or low latency needs.

## GraphQL

A query language where the client asks for exactly the fields it needs from a single endpoint.

```text
query { user(id: 42) { name orders(last: 3) { id total items { name } } } }
```

- Pros: no over-fetching/under-fetching, one round trip for nested data (great for mobile), strongly typed schema, fast frontend iteration.
- Cons: caching is harder (single POST endpoint), N+1 resolver problem (use DataLoader batching), expensive arbitrary queries need depth/complexity limits, more complex authorization per field.
- Use for **client-facing aggregation** (BFF) where many screens need different shapes of data.

## REST vs gRPC vs GraphQL

| | REST | gRPC | GraphQL |
|---|---|---|---|
| Format | JSON over HTTP/1.1 or 2 | Protobuf over HTTP/2 | JSON over HTTP |
| Best for | Public APIs, CRUD | Internal microservices | Flexible client queries |
| Caching | Easy (HTTP) | Custom | Harder |
| Streaming | Limited | Native | Subscriptions |

## Real-time communication

How does the server push updates to clients?

### Short polling
Client asks every N seconds. Simple, wasteful, latency up to N.

### Long polling
Client sends a request; the server holds it open until data is available or a timeout (e.g., 30 s), then the client immediately reconnects. Works everywhere over plain HTTP; each message costs a new request; servers must hold many open requests.

### Server-Sent Events (SSE)
One long-lived HTTP response where the server streams events (`text/event-stream`). **Server → client only**, auto-reconnect with `Last-Event-ID` built into browsers, text only. Great for live scores, notifications, stock tickers, order status updates, LLM token streaming. In Spring: `SseEmitter` or WebFlux `Flux<ServerSentEvent>`.

### WebSockets
A full-duplex, persistent TCP connection after an HTTP upgrade handshake. Low-overhead **bidirectional** messaging. Use for chat, multiplayer games, collaborative editing, live driver location. Challenges: stateful connections (need connection registry to know which server holds which user), sticky/least-connection load balancing, reconnection logic, heartbeats, scaling to millions of connections (each server ~50k-100k+ connections).

| Need | Choose |
|---|---|
| Occasional updates, simple infra | Long polling |
| Server push only (notifications, feeds, live scores) | SSE |
| Two-way, low latency (chat, games, ride tracking) | WebSocket |
| Mobile app in background | Push notifications (FCM/APNs) |

## Interview phrasing

"Public REST API with /v1 versioning, JWT auth, cursor-based pagination for the feed, Idempotency-Key on payment creation. Internal calls between order and inventory use gRPC for lower latency. Clients get live order status through SSE; chat uses WebSockets."
''',
["Resources as plural nouns; correct methods and status codes; consistent error body",
 "GET, PUT, DELETE are idempotent; POST is not, so use Idempotency-Key for payments/orders",
 "Offset pagination is simple but slow for deep pages; cursor/keyset is fast and stable",
 "Version via /v1 URI; prefer backward-compatible additive changes",
 "gRPC: Protobuf + HTTP/2, fast, typed, streaming; ideal for internal services",
 "GraphQL: client picks fields, one endpoint; watch N+1 and caching",
 "Long polling < SSE (server push) < WebSocket (bidirectional)",
 "Async jobs: 202 Accepted + status URL or webhook"],
[("Offset vs cursor pagination: which would you use for a news feed and why?",
 "Cursor pagination. With offset, MySQL must scan and discard all skipped rows, so deep pages get slower, and new posts inserted while scrolling shift results, causing duplicates or skipped items. A cursor encodes the last seen sort key (e.g., post id or timestamp+id), and the next query uses WHERE id < lastId ORDER BY id DESC LIMIT 20, which uses the index and is stable. Feeds don't need jumping to page N."),
 ("How do you make a payment API safe against retries?",
 "Require an Idempotency-Key header generated by the client per logical payment. On first request, atomically store the key with status IN_PROGRESS (unique constraint or Redis SET NX), process, then save the response. On a retry with the same key, return the saved response or 409 if still in progress. Keys expire after ~24 hours. Downstream calls to the gateway also pass an idempotency reference."),
 ("When would you choose gRPC over REST?",
 "For internal service-to-service communication where performance and strong contracts matter: high request volume, low latency, polyglot services needing generated clients, or streaming. Protobuf payloads are smaller and faster to parse, and HTTP/2 multiplexes calls. For public or browser-facing APIs I'd keep REST/JSON since it's human-readable, cacheable and universally supported."),
 ("WebSocket vs SSE vs long polling?",
 "Long polling holds an HTTP request open until data arrives, then reconnects; it's simple and universally supported but has per-message overhead. SSE keeps one HTTP response open for server-to-client streaming with built-in reconnection, ideal for notifications or live scores. WebSockets provide a persistent full-duplex connection, best for chat, games or live location where both sides send frequently. WebSockets need connection management and stateful routing."),
 ("How do you version an API without breaking mobile clients?",
 "Make changes backward-compatible whenever possible: add optional fields, never remove or rename fields, and keep semantics stable; clients should ignore unknown fields. For breaking changes, introduce /v2 alongside /v1, migrate clients, monitor v1 traffic, and deprecate with a timeline and Sunset headers. Force-upgrade very old app versions if needed."),
 ("What problems does GraphQL solve and what does it introduce?",
 "It solves over-fetching and under-fetching: clients request exactly the fields they need, often in one round trip, useful for mobile apps and varied screens. It introduces challenges: HTTP caching is harder, naive resolvers cause N+1 queries (solved with DataLoader batching), malicious deep queries need depth and cost limits, and field-level authorization adds complexity.")],
[("Microsoft REST API Guidelines", "https://github.com/microsoft/api-guidelines"), ("Stripe - Idempotent requests", "https://docs.stripe.com/api/idempotent_requests"), ("gRPC documentation", "https://grpc.io/docs/what-is-grpc/introduction/"), ("GraphQL - Learn", "https://graphql.org/learn/"), ("MDN - Server-sent events", "https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events")]))

topics.append(T("rate-limiting", "Rate Limiting Algorithms", "Intermediate",
"Controlling how many requests a client can make: token bucket, leaky bucket, fixed and sliding windows, and implementing distributed limits with Redis.",
r'''
## Why rate limit

- Protect services from overload and cascading failures.
- Prevent abuse: brute-force login, scraping, OTP spam (an SMS costs money).
- Fairness among tenants; enforce pricing tiers (free plan 100 req/min).
- Control costs of downstream paid APIs.

Limits are keyed by something: user ID, API key, IP address, device, or endpoint (e.g., `POST /login` 5 per minute per IP+username). When exceeded, return **HTTP 429 Too Many Requests** with headers such as `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## Where to enforce

- **Edge/CDN/WAF**: coarse IP-based limits, DDoS protection (Cloudflare, AWS WAF).
- **API gateway**: per-user/API-key limits (Spring Cloud Gateway `RequestRateLimiter` uses Redis, Kong, Envoy).
- **In the service**: fine-grained business limits (OTP per phone per hour), e.g., Resilience4j RateLimiter or Bucket4j.
- **Client side**: be a good citizen when calling third-party APIs.

## The algorithms

### 1. Token bucket (most popular)

A bucket holds up to **capacity** tokens; tokens are added at a **refill rate**. Each request consumes one token; if none are left, reject.

```text
capacity = 10, refill = 5 tokens/sec
Burst of 10 requests at once: allowed (bucket empties)
Then sustained rate: 5 req/s
```

- Allows short **bursts** up to capacity while enforcing an average rate.
- Memory: two numbers per key (tokens, last refill timestamp).
- Lazy refill: on each request, `tokens = min(capacity, tokens + (now - last) * rate)`.
- Used by AWS API Gateway, Stripe, Bucket4j.

### 2. Leaky bucket

Requests enter a FIFO queue (the bucket) and are processed at a constant rate; if the queue is full, new requests are dropped. Produces a **smooth output rate**; bursts are queued rather than served instantly. Good for protecting a downstream with fixed capacity (e.g., an SMS vendor allowing 100/s). Nginx `limit_req` is leaky-bucket-like.

### 3. Fixed window counter

Count requests per key per window: key `rl:user42:202610081230` (minute bucket), `INCR` and `EXPIRE 60`. Reject if count > limit.

- Very simple and memory-cheap.
- **Boundary problem**: limit 100/min; client sends 100 at 12:30:59 and 100 at 12:31:00 → 200 requests in two seconds.

### 4. Sliding window log

Store a timestamp for every request (Redis sorted set). On each request, remove entries older than now−window, count remaining, allow if count < limit.

- Exact.
- Memory heavy: stores every request (100 req/min limit × 1M users = 100M entries).

### 5. Sliding window counter (approximation)

Combine the current and previous fixed windows weighted by overlap:

```text
estimate = prev_count * (1 - elapsed_fraction_of_current_window) + curr_count
limit 100/min, prev minute 80, current minute 30, 25% into current minute
estimate = 80 * 0.75 + 30 = 90  -> allowed
```

- Smooths the boundary problem with only two counters per key.
- Slight approximation (assumes uniform distribution in the previous window); Cloudflare reported very low error in practice.

| Algorithm | Burst handling | Memory | Accuracy |
|---|---|---|---|
| Token bucket | Allows bursts up to capacity | O(1) | Good |
| Leaky bucket | Smooths, queues bursts | O(queue) | Good |
| Fixed window | 2x burst at boundary | O(1) | Weak at edges |
| Sliding log | Exact | O(requests) | Exact |
| Sliding counter | Smooth | O(1) | Approximate, good |

## Distributed rate limiting with Redis

With 20 API instances, each instance counting locally would allow 20x the limit. Use a shared store: Redis (fast, atomic operations, TTLs).

The race: two instances read count=99, both increment to 100 and both allow. Solve with atomic operations:

**Fixed window with INCR** (atomic by itself):
```text
count = INCR rl:{user42}:1730000000
if count == 1: EXPIRE rl:{user42}:1730000000 60
if count > 100: reject
```

**Token bucket with a Lua script** (runs atomically in Redis):

```text
-- KEYS[1]=bucket key, ARGV: capacity, refill_per_sec, now_ms, requested
local b = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local cap, rate, now, req = tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3]), tonumber(ARGV[4])
local tokens = tonumber(b[1]) or cap
local ts = tonumber(b[2]) or now
tokens = math.min(cap, tokens + (now - ts) / 1000 * rate)
local allowed = tokens >= req
if allowed then tokens = tokens - req end
redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now)
redis.call('PEXPIRE', KEYS[1], math.ceil(cap / rate * 1000) * 2)
return allowed and 1 or 0
```

**Sliding log** with a sorted set: `ZREMRANGEBYSCORE key 0 now-60000`, `ZCARD key`, `ZADD key now reqId`, `EXPIRE`, all inside `MULTI` or a Lua script.

### Practical concerns

- **Latency**: each request adds a Redis round trip (~0.5 ms). Acceptable; or batch by keeping a small local allowance per instance and syncing periodically (less exact).
- **Redis failure**: decide **fail-open** (allow traffic, risk overload) or **fail-closed** (reject, risk outage). Most choose fail-open for general APIs, fail-closed for security-sensitive endpoints like login/OTP.
- **Hot keys/scale**: shard counters across a Redis Cluster by key; use hash tags so a user's keys stay in one slot.
- **Clock**: use Redis server time (`TIME`) inside scripts to avoid skew between app servers.
- **Multi-region**: per-region limits, or async sync of counts accepting slight overshoot.

## Beyond simple limits

- **Concurrency limits**: max in-flight requests (bulkheads), not just per-second rate.
- **Adaptive / load shedding**: drop low-priority traffic when CPU or latency crosses thresholds.
- **Quotas**: daily/monthly caps for billing tiers.

## Interview phrasing

"Token bucket per user in Redis via a Lua script at the API gateway, capacity 20 with refill 10/s to allow small bursts. Login gets a stricter fixed-window limit per IP+username, fail-closed. Exceeded requests get 429 with Retry-After."
''',
["Rate limit to prevent overload, abuse and runaway cost; return 429 + Retry-After",
 "Token bucket: capacity + refill rate; allows bursts; O(1) memory",
 "Leaky bucket: constant output rate, queues bursts",
 "Fixed window is simple but allows 2x burst at window boundaries",
 "Sliding log is exact but memory heavy; sliding counter approximates cheaply",
 "Distributed: shared Redis with atomic INCR or Lua scripts",
 "Decide fail-open vs fail-closed when the limiter store is down",
 "Enforce at edge (IP), gateway (user/API key) and service (business rules)"],
[("Explain the token bucket algorithm.",
 "Each client has a bucket with a maximum capacity of tokens that refills at a fixed rate. Every request takes a token; if the bucket is empty, the request is rejected or delayed. It allows short bursts up to the capacity while enforcing an average rate equal to the refill rate. Implementation stores only the token count and last refill time, computing refills lazily on each request."),
 ("What is the problem with fixed window rate limiting?",
 "Counts reset at window boundaries, so a client can send the full limit at the end of one window and again at the start of the next, effectively doubling the allowed rate in a short period. Sliding window log or sliding window counter fixes this; the counter version weights the previous window's count by how much of it overlaps the sliding window, using only two counters."),
 ("How do you implement rate limiting across multiple servers?",
 "Store counters in a shared, fast store like Redis so all instances see the same state. Use atomic operations to avoid races: INCR with EXPIRE for fixed windows, or a Lua script for token bucket or sliding window so read-compute-write happens atomically. Use Redis server time, a Redis Cluster for scale, and choose fail-open or fail-closed behaviour if Redis is unavailable."),
 ("Fail-open or fail-closed when Redis is down?",
 "It depends on what the limiter protects. For general API traffic, fail-open is common: briefly allowing unlimited traffic is better than a full outage, especially with other protections like autoscaling and circuit breakers. For security-sensitive or costly endpoints like login, OTP or SMS sending, fail-closed (or fall back to a conservative local in-memory limit) prevents abuse and unexpected bills."),
 ("What headers should a rate-limited API return?",
 "On rejection, HTTP 429 Too Many Requests with a Retry-After header telling the client when to retry. On all responses, informative headers like X-RateLimit-Limit (allowed quota), X-RateLimit-Remaining and X-RateLimit-Reset help well-behaved clients pace themselves. Clients should then retry with exponential backoff and jitter.")],
[("Cloudflare - How we built rate limiting capable of scaling to millions of domains", "https://blog.cloudflare.com/counting-things-a-lot-of-different-things/"), ("Stripe - Scaling your API with rate limiters", "https://stripe.com/blog/rate-limiters"), ("Redis - Rate limiting patterns", "https://redis.io/glossary/rate-limiting/"), ("ByteByteGo - Design a rate limiter", "https://bytebytego.com/courses/system-design-interview/design-a-rate-limiter")]))

topics.append(T("cdn-blob-storage", "CDN and Blob/Object Storage", "Basic",
"Storing large files in object stores like S3 and serving them fast worldwide through CDNs, with pre-signed uploads, caching headers and invalidation.",
r'''
## Blob (object) storage

Images, videos, PDFs, backups and logs are large, immutable-ish binary objects. They do **not** belong in MySQL: they bloat the database, hurt buffer pool efficiency, make backups slow, and databases are expensive per GB. Instead, store them in **object storage** (Amazon S3, Google Cloud Storage, Azure Blob, MinIO self-hosted) and keep only metadata and the object key in the DB.

```sql
CREATE TABLE media (
  id BIGINT PRIMARY KEY,
  owner_id BIGINT NOT NULL,
  s3_key VARCHAR(512) NOT NULL,     -- e.g. users/42/2026/10/abc123.jpg
  content_type VARCHAR(100),
  size_bytes BIGINT,
  checksum CHAR(64),
  status ENUM('UPLOADING','READY','FAILED'),
  created_at DATETIME
);
```

### Properties of object stores (S3 as reference)

- Flat namespace of **buckets** and **keys** (the "/" is just part of the key name).
- Virtually unlimited capacity, pay per GB stored (~$0.023/GB-month standard) and per request/egress.
- **Durability** of 99.999999999% (11 nines) by replicating across multiple facilities; availability ~99.99%.
- Objects are immutable: you overwrite the whole object, no partial edits.
- Strong read-after-write consistency (S3 since Dec 2020).
- **Storage classes**: Standard → Infrequent Access → Glacier/Deep Archive, with lifecycle rules (move logs older than 90 days to Glacier, delete after 1 year).
- Versioning, server-side encryption, access policies.
- Throughput scales with parallelism; S3 supports thousands of requests/sec per prefix.

### Uploading: pre-signed URLs

Don't stream large uploads through your Spring Boot servers (ties up threads, bandwidth, memory). Instead:

```text
1. Client  -> API:  POST /v1/uploads {fileName, size, contentType}
2. API     -> validates, creates media row (UPLOADING), generates pre-signed PUT URL (valid 15 min)
3. Client  -> S3:   PUT <presigned URL> with file bytes (direct)
4. S3      -> event (S3 notification -> SQS/Lambda) or client calls POST /v1/uploads/{id}/complete
5. Backend -> marks READY, triggers processing (thumbnails, virus scan, transcoding)
```

For large files (>100 MB) use **multipart upload**: split into parts (e.g., 5-100 MB), upload in parallel, retry failed parts individually, then complete. Enables resumable uploads.

Downloads of private files use **pre-signed GET URLs** with short expiry, or CDN signed URLs/cookies.

## CDN (Content Delivery Network)

A CDN is a network of **edge servers** (Points of Presence) around the world that cache content close to users. A user in Bhubaneswar fetching an image from a server in Mumbai might take 30-50 ms; from US-East, 250 ms. With a CDN edge in the same city, maybe 5-10 ms, and your origin is shielded from most traffic.

```text
User --> [CDN edge Chennai] --hit--> returns cached file
              | miss
              v
         [Regional/shield cache] --miss--> [Origin: S3 bucket or app server]
```

Examples: CloudFront, Akamai, Cloudflare, Fastly, Google Cloud CDN.

### Push vs pull CDN

- **Pull** (most common): the edge fetches from origin on first request (cache miss), then caches per TTL. Easy; first user pays the latency.
- **Push**: you upload content to the CDN ahead of time. Good for large, predictable content (a new movie release, app update), more management.

### Controlling caching

- `Cache-Control: public, max-age=31536000, immutable` for versioned static assets (`app.3f9a1c.js`, `img_abc123_v2.jpg`).
- `Cache-Control: no-store` or short `max-age` for personalised or sensitive responses.
- `ETag` / `Last-Modified` for revalidation.
- `Vary` header (e.g., `Accept-Encoding`) to cache variants.

### Invalidation

- **Versioned filenames** (fingerprinting): the preferred approach. A new deploy references new file names, so no invalidation is needed and old files can stay cached forever.
- **Explicit invalidation/purge** API: slower (seconds to minutes) and sometimes costs money; use for mistakes or takedowns.
- Short TTLs for content that changes.

### What CDNs do beyond caching

- **TLS termination at the edge**, HTTP/2 and HTTP/3.
- **DDoS protection and WAF**.
- **Image optimisation** (resize, WebP/AVIF conversion on the fly).
- **Video streaming**: caching HLS/DASH segments; the backbone of YouTube/Hotstar-like delivery.
- **Edge compute** (Cloudflare Workers, Lambda@Edge) for auth checks, A/B routing.
- **Dynamic content acceleration**: optimised routes and persistent connections to origin even for uncacheable APIs.
- **Origin shield**: a middle cache layer so a miss in 200 edges results in one origin fetch.

### Cost and numbers

Egress (bandwidth out) is often the largest bill for media-heavy apps. CDN egress is usually cheaper than origin egress at scale, and high cache hit ratios (95%+) for static media drastically cut origin load. Hotstar-style events (IPL finals, 20M+ concurrent viewers) are only possible because nearly all video bytes come from CDN edges, often with multiple CDN vendors.

## Putting it together: image upload and display

1. Client gets pre-signed URL, uploads original to `s3://media-raw/`.
2. S3 event triggers a worker (via SQS) that creates thumbnails (150px, 600px, 1080px) and WebP variants, writes them to `s3://media-public/` with content-hashed names.
3. DB row updated with variant keys, status READY.
4. Clients load `https://cdn.example.com/img/<hash>_600.webp`; CDN caches with a one-year TTL.
5. Delete: remove DB reference, delete S3 objects asynchronously, purge CDN if needed (or rely on unguessable names and short-lived signed URLs for private content).

## Interview phrasing

"Media goes to S3 via pre-signed multipart uploads directly from the client; the DB stores only metadata and the object key. An async pipeline generates thumbnails. All media is served via CloudFront with long TTLs and content-hashed file names, so we never need to invalidate; private files use signed URLs that expire in 10 minutes."
''',
["Never store large files in the DB; store them in S3 and keep metadata + key in the DB",
 "S3: 11 nines durability, flat key space, storage classes, lifecycle rules",
 "Use pre-signed URLs so clients upload/download directly to S3",
 "Multipart upload for large files: parallel, resumable",
 "CDN edges cache content near users; pull CDN is the default",
 "Version file names (content hash) instead of invalidating caches",
 "Cache-Control headers decide what the CDN caches and for how long",
 "CDNs also provide TLS at edge, DDoS protection, image/video optimisation"],
[("Why shouldn't you store images in MySQL?",
 "Images are large binary blobs that bloat tables, push useful rows out of the InnoDB buffer pool, slow replication and backups, and make the DB the bandwidth bottleneck. Databases cost far more per GB than object storage. Instead, store files in S3 with high durability and cheap storage, keep metadata and the object key in MySQL, and serve the files through a CDN."),
 ("How would you design a file upload flow for large files?",
 "The client asks the API to start an upload; the API validates the user, size and type, creates a metadata row with status UPLOADING and returns pre-signed URLs for an S3 multipart upload. The client uploads parts in parallel directly to S3, retrying failed parts, then completes the upload. An S3 event or a client callback marks the file READY and triggers async processing like virus scanning or thumbnails. App servers never handle the bytes."),
 ("What is a CDN and how does it improve performance?",
 "A CDN is a globally distributed network of edge caches. User requests go to the nearest edge; if the content is cached it's returned with low latency, otherwise the edge fetches from the origin and caches it. This reduces latency for distant users, offloads traffic and bandwidth from origin servers, absorbs traffic spikes and DDoS attacks, and terminates TLS close to users."),
 ("How do you handle CDN cache invalidation when a file changes?",
 "Preferably avoid invalidation by using versioned or content-hashed file names: a changed file gets a new URL, so the page references the new name and the old cached copy expires naturally. Static assets can then use max-age of a year with immutable. When you must change content under the same URL, use short TTLs or the CDN's purge API, which takes time and may cost money."),
 ("Push CDN vs pull CDN?",
 "With a pull CDN, edges fetch content from the origin on the first request and cache it according to TTLs; it's simple and works for most sites. With a push CDN, you upload content to the CDN proactively; it suits large, predictable content like a movie launch or a game patch, avoiding a thundering herd of misses on the origin, but requires managing what's on the CDN.")],
[PRIMER, ("Amazon S3 User Guide", "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html"), ("Amazon S3 - Uploading with presigned URLs", "https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html"), ("Cloudflare - What is a CDN", "https://www.cloudflare.com/learning/cdn/what-is-a-cdn/"), ("MDN - HTTP caching", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching")]))

topics.append(T("microservices-patterns", "Microservices Patterns", "Advanced",
"The core patterns for building microservice systems: API gateway, service discovery, circuit breakers, retries, outbox, CQRS, event sourcing, and when not to use microservices.",
r'''
## Monolith vs microservices

A **monolith** is one deployable unit (your typical Spring Boot app with all modules). A **microservices** architecture splits the system into independently deployable services, each owning one business capability and **its own database**.

| | Monolith | Microservices |
|---|---|---|
| Deploy | One unit | Independent per service |
| Scaling | Whole app | Per service |
| Team | Works for small teams | Many teams own services |
| Data | One DB, joins, ACID | DB per service, eventual consistency |
| Complexity | In code | In network, ops, observability |
| Failure | One bug can crash all | Partial failures, cascading risk |

Advice interviewers like: **start with a modular monolith**, split when team size, deployment friction or scaling needs justify it. Microservices trade code complexity for distributed-systems complexity.

Split by **business domain** (bounded contexts from Domain-Driven Design): User, Catalog, Cart, Order, Payment, Inventory, Notification. Avoid splitting by technical layer.

## API gateway

The single entry point for clients.

```text
Mobile/Web --> [API Gateway] --> /users/**   -> User Service
                   |          --> /orders/** -> Order Service
     auth, rate limit,        --> /catalog/**-> Catalog Service
     routing, TLS, logging
```

Responsibilities: routing, authentication (validate JWT once), rate limiting, request/response transformation, aggregation, CORS, observability. Examples: Spring Cloud Gateway, Kong, AWS API Gateway, Envoy.

**Backend for Frontend (BFF)**: a gateway tailored per client type (mobile BFF returns compact aggregated data; web BFF richer).

Risks: gateway becoming a bottleneck or a "god service" with business logic. Keep it thin and horizontally scaled.

## Service discovery

Instances come and go (autoscaling, deployments), so their IPs change. Services need to find each other.

- **Client-side discovery**: services register with a registry (Eureka, Consul); clients query it and load-balance themselves (Spring Cloud LoadBalancer).
- **Server-side discovery**: clients call a stable address; the platform routes. In **Kubernetes**, a `Service` gets a DNS name (`order-service.default.svc.cluster.local`) and kube-proxy balances across pods. This is the most common today.
- **Service mesh** (Istio, Linkerd): sidecar proxies handle discovery, mTLS, retries, timeouts, and metrics without app code.

## Resilience patterns

In a call chain A → B → C, if C slows down, threads in B pile up waiting, then A's threads pile up: a **cascading failure**.

### Timeouts
Every remote call needs a timeout (connect ~1 s, read based on SLO, e.g., 2 s). The default "wait forever" is the root of many outages.

### Retries with exponential backoff and jitter
Retry transient errors (timeouts, 503) a few times: 100 ms, 200 ms, 400 ms + random jitter. Only retry **idempotent** operations (or with idempotency keys). Beware **retry storms**: three layers each retrying 3 times = 27x load. Use retry budgets.

### Circuit breaker
Like an electrical fuse. States:

```text
CLOSED --(failure rate > 50% in window)--> OPEN --(wait 30s)--> HALF_OPEN
   ^                                                              |
   +------------------(trial calls succeed)-----------------------+
                       (trial calls fail) -> OPEN again
```

When OPEN, calls fail fast (or return a **fallback**: cached data, default value, "recommendations unavailable") without hitting the failing service, giving it time to recover. In Spring Boot: **Resilience4j** `@CircuitBreaker(name="inventory", fallbackMethod="...")`, combined with `@Retry`, `@TimeLimiter`, `@Bulkhead`.

### Bulkhead
Isolate resources (separate thread pools or connection pools per dependency) so one slow dependency can't consume all threads.

### Graceful degradation
Homepage still loads if the recommendation service is down; show bestsellers instead.

## Data patterns

### Database per service
Each service owns its tables; others access data only via its API or events. Enables independent evolution, but no cross-service joins or transactions. Shared databases create hidden coupling.

### Transactional outbox
Write the domain change and an event into an outbox table in the same local transaction; a relay (poller or Debezium CDC) publishes to Kafka. Guarantees an event is published if and only if the DB change committed (at-least-once).

```sql
BEGIN;
INSERT INTO orders(id, user_id, status, total) VALUES (991, 42, 'PLACED', 49900);
INSERT INTO outbox(id, aggregate_id, type, payload) VALUES (uuid(), 991, 'OrderPlaced', '{...}');
COMMIT;
```

### Saga
Distributed business transactions as a sequence of local transactions with compensations (see the transactions chapter). Orchestration or choreography.

### API composition
To show "order with product details and shipment status", a composer (gateway/BFF) calls several services and merges results. Simple, but latency adds up and availability multiplies.

### CQRS (Command Query Responsibility Segregation)
Separate the **write model** (normalised, transactional, validates commands) from one or more **read models** (denormalised, optimised for queries), kept in sync via events.

```text
Commands -> [Order Service] -> MySQL (write model) -> events -> [Projector]
                                                                   |
Queries  <- [Query Service] <- Elasticsearch / Redis / read tables <-+
```

Use when read and write patterns differ hugely (e.g., search across orders by many filters, dashboards). Cost: eventual consistency between write and read sides, more moving parts.

### Event sourcing
Instead of storing current state, store the **sequence of events** that led to it (`AccountOpened`, `MoneyDeposited 500`, `MoneyWithdrawn 200`); current state = replay of events (with periodic snapshots).

- Pros: complete audit trail, rebuild any past state, natural fit with CQRS and event-driven systems, easy to add new projections.
- Cons: complex, event schema evolution is hard, queries need projections, eventual consistency, a learning curve. Used in banking ledgers, trading, some order systems. Don't propose it casually.

## Other patterns worth knowing

- **Strangler fig**: migrate a monolith gradually by routing feature by feature to new services behind the gateway.
- **Sidecar**: helper container next to the app (logging agent, Envoy proxy).
- **Anti-corruption layer**: translate between a legacy model and the new domain model.
- **Config server** (Spring Cloud Config) and feature flags.
- **Distributed tracing** with correlation IDs: essential for debugging (see observability).

## When microservices hurt

Small team, unclear domain boundaries, heavy cross-service transactions, no DevOps maturity (CI/CD, monitoring, containers). The "distributed monolith" (services that must be deployed together and call each other synchronously everywhere) has the costs of both and benefits of neither.

## Interview phrasing

"Clients hit Spring Cloud Gateway which validates JWTs and rate-limits. Services discover each other via Kubernetes DNS. Synchronous calls have timeouts, retries with backoff for idempotent calls, and Resilience4j circuit breakers with fallbacks. Each service owns its MySQL schema; cross-service workflows use an orchestrated saga with the outbox pattern, and the order search screen is a CQRS read model in Elasticsearch."
''',
["Start with a modular monolith; split by business domain when justified",
 "API gateway: routing, auth, rate limiting, aggregation; keep it thin",
 "Service discovery: Eureka/Consul (client-side) or Kubernetes DNS (server-side)",
 "Timeouts + retries with backoff/jitter (idempotent only) + circuit breaker + bulkhead",
 "Circuit breaker states: closed, open, half-open; fail fast with fallback",
 "Database per service; outbox for reliable events; saga for distributed workflows",
 "CQRS separates write and read models; event sourcing stores events as source of truth",
 "Avoid the distributed monolith"],
[("How does a circuit breaker work?",
 "It wraps calls to a dependency and tracks failures over a sliding window. While CLOSED, calls pass through. If the failure rate or slow-call rate crosses a threshold, it OPENS and immediately fails calls or returns a fallback without contacting the dependency. After a wait period it goes HALF_OPEN and lets a few trial calls through; if they succeed it closes, otherwise it opens again. In Spring Boot I'd use Resilience4j."),
 ("What does an API gateway do and what are its risks?",
 "It's the single entry point that routes requests to services and handles cross-cutting concerns: TLS, authentication, rate limiting, CORS, request transformation, response aggregation and logging. Risks: it can become a bottleneck or single point of failure (so run multiple instances behind an LB), add latency, and become a dumping ground for business logic, recreating a monolith. Keep it thin."),
 ("Explain CQRS and when you'd use it.",
 "CQRS separates the write side, which handles commands and enforces business rules on a normalised transactional store, from read side models that are denormalised for specific queries, updated via events. I'd use it when read and write patterns diverge significantly, such as complex search and dashboards over orders, or when reads vastly outnumber writes. The trade-off is eventual consistency between the sides and extra infrastructure."),
 ("What is event sourcing and its downsides?",
 "Event sourcing stores every state change as an immutable event in an append-only log; current state is derived by replaying events, often with snapshots. It gives a perfect audit trail, temporal queries and easy new projections. Downsides: complexity, harder querying (requires projections), event versioning and schema evolution, eventual consistency, and storage growth. It fits ledgers and audit-heavy domains, not simple CRUD."),
 ("Why should each microservice have its own database?",
 "So services are loosely coupled: each can change its schema, choose the right storage technology and scale independently without breaking others. A shared database creates hidden dependencies where one team's migration breaks another's service. The cost is no cross-service joins or ACID transactions, so we use APIs, events, CQRS read models and sagas instead."),
 ("How would you migrate a monolith to microservices?",
 "Use the strangler fig pattern: put a gateway in front of the monolith, pick a well-bounded, high-value domain (e.g., notifications), build it as a service, route its traffic to the new service, and move its data with CDC or dual writes. Repeat domain by domain. Invest first in CI/CD, containerisation, monitoring and tracing. Avoid a big-bang rewrite.")],
[("microservices.io - Pattern language (Chris Richardson)", "https://microservices.io/patterns/"), ("Martin Fowler - Microservices", "https://martinfowler.com/articles/microservices.html"), ("Martin Fowler - CQRS", "https://martinfowler.com/bliki/CQRS.html"), ("Resilience4j documentation", "https://resilience4j.readme.io/docs"), ("Martin Fowler - Event Sourcing", "https://martinfowler.com/eaaDev/EventSourcing.html")]))

dump("sd_part3.json", topics)
