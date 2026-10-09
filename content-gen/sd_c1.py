from sd_common import *

topics = []

topics.append(T("how-to-approach", "How to Approach a System Design Interview", "Basic",
"A repeatable 45-minute framework that turns a vague prompt like 'design WhatsApp' into a structured, trade-off-driven conversation.",
r'''
## Why a framework matters

A system design round is not a quiz with one right answer. The interviewer gives you a deliberately vague prompt ("Design a URL shortener", "Design Swiggy") and watches **how you think**: do you clarify scope, reason with numbers, make decisions and defend them, and notice where the system will break? Candidates from service companies usually fail not because they lack knowledge but because they jump straight into drawing boxes, or they freeze. A fixed sequence of steps removes both problems.

For SDE-1 the bar is: produce a sensible working design, explain each component, and handle one or two deep dives. For SDE-2 the interviewer also expects you to drive the conversation, quantify things, and discuss trade-offs without being prompted.

## The 45-minute plan

| Phase | Time | Output on the whiteboard |
|---|---|---|
| 1. Requirements | 5 min | Functional list, non-functional list, out of scope |
| 2. Estimates | 3-5 min | QPS, storage, bandwidth (only what drives decisions) |
| 3. API design | 5 min | 3-6 endpoints with request/response |
| 4. Data model | 5 min | Entities, key fields, choice of DB |
| 5. High-level design | 10 min | Boxes and arrows covering every functional requirement |
| 6. Deep dives | 10-15 min | 2-3 hard parts solved properly |
| 7. Wrap-up | 2-3 min | Bottlenecks, failure modes, what you would add next |

### 1. Requirements (do not skip)

Ask questions until you can write two lists.

- **Functional**: what the user can do. Keep it to 3-5 core features. "Users can send 1:1 messages, see delivery/read receipts, see online status." Explicitly park extras: "Group calls and payments are out of scope."
- **Non-functional**: scale (DAU), latency targets, availability vs consistency, durability, read/write ratio. Example: "100M DAU, message delivery under 500 ms p99, messages must never be lost, 99.99% availability."

Good clarifying questions: Who are the users? How many? Read-heavy or write-heavy? Global or India-only? Is strong consistency needed anywhere (payments, inventory)? What is the latency expectation?

### 2. Back-of-envelope estimates

Only compute numbers that change a decision. "10M writes/day is ~115 writes/sec, a single MySQL instance handles that easily" is a valuable sentence. Computing bandwidth to three decimal places is not. See the dedicated back-of-envelope chapter.

### 3. API design

Write the endpoints in REST style. It forces you to pin down inputs and outputs.

```text
POST /v1/urls            {longUrl, customAlias?, expiry?} -> {shortUrl}
GET  /{code}             -> 302 Location: longUrl
GET  /v1/users/{id}/urls?cursor=..&limit=20
```

Mention auth (JWT in header), idempotency keys for POSTs that create money or orders, and pagination.

### 4. Data model

List the main entities and their important columns. Then choose storage with a reason: "Orders need transactions and joins, so MySQL. Chat messages are huge write volume, accessed by conversation id and time, so Cassandra." Name the partition key if you shard.

### 5. High-level design

Draw the request path end to end. A typical skeleton:

```text
Client -> CDN -> Load Balancer -> API Gateway -> Services -> Cache -> DB
                                              \-> Queue -> Workers
```

Walk through each functional requirement on the diagram ("when the user sends a message, it goes here, then here..."). If a requirement has no path in your diagram, the design is incomplete.

### 6. Deep dives

Either the interviewer picks, or you propose: "The interesting parts are generating unique short codes and handling 100k redirects/sec. Shall I go deeper into those?" Typical deep-dive topics: hot keys, cache invalidation, sharding key choice, exactly-once processing, consistency for inventory/payments, fan-out strategy, real-time delivery.

### 7. Trade-offs and wrap-up

State what you gave up. "I chose eventual consistency for the feed, so a new post may take a few seconds to appear for followers; that is acceptable for social content but would not be for a bank balance." Mention monitoring, failure handling and what you would build next.

## Habits that impress interviewers

- **Think aloud.** Silence is scored as "stuck".
- **Start simple, then scale.** A single server with MySQL first, then add cache, replicas, shards as numbers demand. This shows you do not over-engineer.
- **Justify every box.** Never add Kafka "because big companies use it". Say what problem it solves (decoupling, buffering spikes, async retries).
- **Use numbers.** "A Redis node does ~100k ops/sec, so 3 nodes cover our 200k peak with headroom."
- **Name the trade-off for each decision**: latency vs consistency, cost vs availability, complexity vs flexibility.
- **Relate to your experience.** "In my Spring Boot project we used @Cacheable with Redis; the same pattern applies here."

## Common mistakes

1. Designing without requirements, then being told "we don't need that".
2. Spending 15 minutes on estimates.
3. Drawing 20 boxes with no explanation of data flow.
4. Ignoring failure: what happens if the cache, DB primary, or a service dies?
5. Saying "it depends" without then choosing.

## Cheat template to memorise

```text
1. Clarify: features (3-5), users/scale, read:write, latency, consistency
2. Estimate: QPS (avg, peak = 2-3x), storage/yr, cache size
3. API: endpoints + auth + pagination + idempotency
4. Data: entities, DB choice + why, keys/indexes, shard key
5. HLD: LB, stateless services, cache, DB, queue, CDN, blob store
6. Deep dive: 2-3 hardest problems
7. Wrap: bottlenecks, failures, monitoring, future work
```
''',
["Spend the first 5 minutes on functional and non-functional requirements; write them down",
 "Estimate only numbers that drive decisions: QPS, peak QPS, storage, cache size",
 "Define APIs and data model before drawing the architecture",
 "Start with a simple design, then scale it step by step using numbers",
 "Every component must be justified by a requirement or bottleneck",
 "Proactively propose 2-3 deep dives on the hardest parts",
 "Always state trade-offs and failure handling at the end"],
[("How do you start when given a vague prompt like 'Design Instagram'?",
 "I clarify scope before designing. I list 3-5 core functional features (upload photo, follow, view feed), confirm what is out of scope (stories, DMs), and gather non-functional needs: DAU, read:write ratio, latency target, consistency needs, and global vs regional. I then do quick estimates for QPS and storage, define APIs and the data model, and only then draw the high-level design. This keeps the design anchored to requirements."),
 ("What are functional vs non-functional requirements? Give examples.",
 "Functional requirements describe what the system does: 'users can book a seat', 'users get an SMS on booking'. Non-functional requirements describe how well it does it: latency (p99 under 200 ms), availability (99.99%), consistency (no double booking), durability, scalability (10M DAU), security. Non-functional requirements usually drive the architecture: strong consistency pushes you to a relational DB with transactions; high read volume pushes you to caching and replicas."),
 ("Why should you start with a simple design?",
 "A simple design (one service, one database) proves you understand the core flow and gives a baseline. Then you scale it based on numbers: add a cache when reads exceed what the DB can serve, read replicas for read-heavy load, sharding when data or writes exceed one machine. This shows judgement and avoids over-engineering, which interviewers penalise because complexity has operational cost."),
 ("How do you handle a deep dive you don't know well?",
 "Be honest and reason from first principles. State what you know, propose an approach, and discuss its trade-offs. For example, if asked about Kafka internals, I would explain partitions, consumer groups and offsets at the level I know, then say how I would verify the rest. Interviewers value structured reasoning and honesty over bluffing."),
 ("What should you cover in the last few minutes?",
 "Summarise the design against the requirements, then list bottlenecks and single points of failure and how to mitigate them (replicas, multi-AZ, circuit breakers). Mention monitoring (metrics, alerts on p99 latency and error rate), and future improvements like analytics or multi-region. This shows ownership beyond just drawing boxes.")],
[HI, PRIMER, ("ByteByteGo - A framework for system design interviews", "https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews")]))

topics.append(T("back-of-envelope", "Back-of-the-Envelope Estimation", "Basic",
"Quick arithmetic to estimate QPS, storage, bandwidth and server counts so your design choices are grounded in numbers.",
r'''
## Why estimate?

Estimates tell you **which problems you actually have**. 50 writes/second needs nothing special; 50,000 writes/second means a single MySQL primary will not survive and you must think about sharding or a write-optimised store. Interviewers want rough, fast, order-of-magnitude numbers, rounded aggressively.

## Numbers to memorise

### Time and size

| Quantity | Value |
|---|---|
| Seconds in a day | 86,400 ≈ **10^5** (use 100k) |
| Seconds in a month | ≈ 2.5 million |
| Seconds in a year | ≈ 3 × 10^7 |
| 1 KB / 1 MB / 1 GB / 1 TB / 1 PB | 10^3 / 10^6 / 10^9 / 10^12 / 10^15 bytes |
| ASCII char | 1 byte; UUID 16 bytes (36 as string); long 8 bytes |

### Latency (approximate)

| Operation | Time |
|---|---|
| L1 cache reference | 1 ns |
| Main memory reference | 100 ns |
| Read 1 MB sequentially from memory | ~10 µs |
| SSD random read | ~100 µs |
| Round trip within same datacenter | ~0.5 ms |
| Read 1 MB sequentially from SSD | ~1 ms |
| HDD seek | ~10 ms |
| Round trip India to US | ~150-250 ms |

Takeaways: memory is ~1000x faster than SSD random reads; network within a datacenter is cheap; cross-continent calls are expensive, so keep users near their data (CDN, regional deployment).

### Typical capacity of a single component (rule of thumb)

| Component | Rough capacity |
|---|---|
| Spring Boot service instance (simple CRUD) | 1k-5k req/s |
| MySQL on good hardware | ~5k-10k simple writes/s, 10k-50k indexed reads/s |
| Redis single node | ~100k ops/s, sub-ms latency |
| Kafka broker | hundreds of MB/s, ~100k+ msgs/s |
| One WebSocket server | ~50k-100k concurrent connections |

These are not exact; they are good enough to decide "one box" vs "fifty boxes".

### Availability

| Availability | Downtime per year |
|---|---|
| 99% | 3.65 days |
| 99.9% | 8.8 hours |
| 99.99% | 52.6 minutes |
| 99.999% | 5.3 minutes |

## The standard recipe

1. **DAU** (given or assumed).
2. **Actions per user per day** for each type (reads, writes).
3. **Average QPS** = DAU × actions / 86,400 ≈ DAU × actions / 10^5.
4. **Peak QPS** = 2-3x average (10x for flash sales like Big Billion Days).
5. **Storage** = writes/day × object size × retention days (× replication factor 3).
6. **Bandwidth** = QPS × response size.
7. **Cache memory** = apply 80/20 rule: cache 20% of daily read data.
8. **Servers** = peak QPS / per-server capacity, plus headroom.

## Worked example: Twitter-like service

Assumptions: 200M DAU, each user posts 0.5 tweets/day and reads 100 tweets/day. Tweet = 300 bytes text + metadata ~ 1 KB. 10% of tweets have an image of 500 KB.

- Write QPS = 200M × 0.5 / 10^5 = **1,000 tweets/s**, peak ~3,000/s.
- Read QPS = 200M × 100 / 10^5 = **200,000 reads/s**, peak ~600k/s. Read:write = 200:1, so this is a read-heavy system: caching and precomputed feeds are mandatory.
- Text storage/day = 100M tweets × 1 KB = 100 GB/day; ×365 = ~36 TB/year; with 3x replication ~110 TB/year.
- Media/day = 10M × 500 KB = 5 TB/day ≈ 1.8 PB/year → blob storage (S3) + CDN, never in the database.
- Servers for reads: if one app instance does 2k req/s, 600k peak / 2k = 300 instances (before caching at CDN/edge reduces this).

## Worked example: URL shortener

100M new URLs/month, read:write 100:1.

- Writes: 100M / (30 × 10^5) ≈ **40/s**. Reads: **4,000/s**, peak ~10k/s.
- Each record ~500 bytes. Five years = 100M × 12 × 5 = 6 billion URLs × 500 B = **3 TB**. Fits on a few machines; sharding optional.
- Cache: daily reads = 4,000 × 10^5 = 400M; cache 20% hot = 80M × 500 B = **40 GB** → one or two Redis nodes.
- Code length: base62 with 7 chars = 62^7 ≈ 3.5 trillion, plenty for 6 billion.

## Tips for the interview

- Say your assumptions out loud and write them down.
- Round: 86,400 → 100k; 2.5M seconds a month; 3 × 10^7 a year.
- Use powers of ten: 10^6 × 10^3 = 10^9.
- Conclude every number with a decision: "3 TB fits in one sharded MySQL cluster", "600k reads/s means we need a cache layer in front of the DB".
- Do not spend more than 5 minutes here unless the interviewer wants it.

## Mapping to your experience

In a Spring Boot app with Tomcat's default 200 worker threads, if each request spends 50 ms (mostly waiting on MySQL), one instance handles roughly 200 / 0.05 = 4,000 req/s at best (Little's Law: concurrency = throughput × latency). If DB latency rises to 200 ms, throughput falls to 1,000 req/s. This is why slow queries cascade into capacity problems.
''',
["Seconds per day ≈ 10^5; average QPS = DAU × actions / 10^5",
 "Peak QPS is 2-3x average; flash sales can be 10x",
 "Storage = writes/day × size × retention × replication factor",
 "Cache roughly 20% of daily hot read data (80/20 rule)",
 "Memory ~100 ns, SSD ~100 µs, DC round trip ~0.5 ms, cross-continent ~200 ms",
 "Redis ~100k ops/s, MySQL ~5-10k writes/s, app server ~1-5k req/s",
 "Every estimate must end in a design decision",
 "Little's Law: concurrency = throughput × latency"],
[("Estimate the QPS for a service with 50M DAU where each user makes 20 requests a day.",
 "Total requests/day = 50M × 20 = 1 billion. Dividing by ~10^5 seconds gives about **10,000 QPS average**. Peak is typically 2-3x, so plan for **25-30k QPS**. If one Spring Boot instance handles ~2k req/s, I need about 15 instances at peak plus headroom for failures, so ~20 behind a load balancer. If most requests are reads, a cache could cut DB load by 80-90%."),
 ("How do you estimate storage for 5 years?",
 "Storage = new objects per day × average object size × 365 × 5, then multiply by replication (typically 3). For example 10M records/day × 1 KB = 10 GB/day → 3.6 TB/year → 18 TB over 5 years → ~54 TB with 3 replicas. I'd also separate large media into blob storage since it dominates size and should not live in the database."),
 ("What does 99.99% availability mean in practice?",
 "It allows about 52 minutes of downtime per year, or ~4.3 minutes per month. Achieving it needs redundancy at every layer (multiple app instances, DB replicas with automatic failover, multi-AZ deployment), health checks, and fast rollbacks. Note availability multiplies for serial dependencies: three 99.9% services in series give ~99.7%, so critical paths need fewer hard dependencies."),
 ("How large a cache do you need for a read-heavy service?",
 "Apply the 80/20 rule: about 20% of objects serve 80% of reads. Compute daily distinct reads × object size × 0.2. For 400M reads/day of 500-byte objects, that is 80M × 500 B ≈ 40 GB, which fits on one or two Redis nodes (with a replica each). Then validate with hit-ratio metrics in production and adjust."),
 ("Why are latency numbers important in design?",
 "They show where time is spent. Memory reads are ~100 ns while an SSD random read is ~100 µs and a cross-continent round trip ~200 ms. So caching in memory gives huge wins, chatty services calling each other many times per request add latency, and users far away need CDNs or regional deployments. They also justify batching and async processing.")],
[PRIMER, ("Latency numbers every programmer should know", "https://gist.github.com/jboner/2841832"), ("ByteByteGo - Back-of-the-envelope estimation", "https://bytebytego.com/courses/system-design-interview/back-of-the-envelope-estimation")]))

topics.append(T("scalability-basics", "Scalability Basics: Vertical, Horizontal and Stateless Services", "Basic",
"How systems grow from one server to many: scaling up vs out, why stateless services matter, and the standard evolution path.",
r'''
## What scalability means

A system is scalable if it can handle more load (users, requests, data) by adding resources, **without a redesign** and with roughly proportional cost. Related ideas: **performance** (how fast one request is) vs **scalability** (how well it stays fast as load grows). A system can be fast for one user but collapse at 10,000.

## Vertical scaling (scale up)

Give the machine more CPU, RAM, faster disks. Moving MySQL from 8 cores/32 GB to 64 cores/512 GB is vertical scaling.

- **Pros**: no code change, no distributed-systems complexity, strong consistency stays trivial.
- **Cons**: hard ceiling (the largest machine), cost grows faster than linearly, a single point of failure, upgrades often need downtime.

Vertical scaling is underrated. Many Indian startups run a large MySQL primary for years. Always mention it as the first, cheapest step, especially for databases.

## Horizontal scaling (scale out)

Add more machines and spread the load. Ten Spring Boot instances behind a load balancer instead of one big one.

- **Pros**: near-unlimited capacity, fault tolerance (one instance dying is fine), commodity hardware, rolling deployments with zero downtime.
- **Cons**: needs a load balancer, data consistency across nodes becomes hard, more operational complexity (deployment, monitoring, network failures).

| | Vertical | Horizontal |
|---|---|---|
| Limit | Hardware ceiling | Practically unlimited |
| Failure | Single point of failure | Redundant |
| Complexity | Low | High (distributed) |
| Best for | Databases early on, quick fix | Stateless app tier, caches, sharded data |

## Stateless services: the key to scaling the app tier

A service is **stateless** if any instance can serve any request because no request depends on memory left behind by a previous request on that same instance. State lives outside: in a database, Redis, or the client (JWT).

Bad (stateful) Spring Boot example:

```java
@RestController
class CartController {
    // State stored in instance memory - breaks with 2+ instances
    private final Map<String, Cart> carts = new ConcurrentHashMap<>();
}
```

If user A's first request hits instance 1 and the second hits instance 2, the cart is gone. Fixes:

1. Store state in Redis or MySQL (`spring-session-data-redis` for HTTP sessions).
2. Use JWT so the user identity travels with each request.
3. Sticky sessions at the load balancer (works, but uneven load and losing an instance loses sessions; avoid as primary strategy).

Once stateless, you can autoscale: Kubernetes HPA adds pods when CPU > 70%, and the load balancer spreads traffic. Deployments become rolling restarts.

## The typical evolution path

```text
Stage 1: [Client] -> [Single server: Spring Boot + MySQL]

Stage 2: [Client] -> [App server] -> [MySQL on separate machine]

Stage 3: [Client] -> [Load Balancer] -> [App x N (stateless)] -> [MySQL]

Stage 4:                         +-> [Redis cache]
         [LB] -> [App x N] ------+-> [MySQL primary] -> [Read replicas]

Stage 5: + CDN for static/media, + S3 for files, + Kafka for async work

Stage 6: + Sharded DB, + microservices split by domain, + multi-region
```

Each step is triggered by a measured bottleneck: CPU on app servers, DB read load, DB write load, data size, team size.

## Where the bottleneck usually is

The app tier is easy to scale because it is stateless. **The database is almost always the real bottleneck.** Tools in order of complexity:

1. Indexes and query optimisation (fix N+1 queries in JPA!).
2. Connection pooling (HikariCP sizing).
3. Caching (Redis) to remove reads.
4. Read replicas for read traffic.
5. Vertical scale the primary.
6. Move heavy writes to async queues.
7. Shard (partition) data across multiple primaries.
8. Move some data to a NoSQL store suited to the access pattern.

## Other scalability tools

- **Asynchronous processing**: send emails, generate invoices, resize images via a queue so the request returns fast.
- **Denormalisation and precomputation**: store the feed or counters ready-to-read.
- **CDN**: serve static content from edge locations.
- **Autoscaling**: scale on CPU, request count or queue lag.
- **Bulkheads and rate limits**: stop one noisy client or feature from taking down everything.

## Scalability vs other qualities

More machines mean more failure modes: network partitions, partial failures, clock skew, retries producing duplicates. That is why distributed design talks so much about idempotency, timeouts and consistency. Always balance: "Do we need this scale now?" A good engineer designs for 10x current load, not 1000x.
''',
["Vertical scaling = bigger machine; simple but has a ceiling and is a SPOF",
 "Horizontal scaling = more machines; needs LB and handles failure better",
 "Stateless services keep state in DB/Redis/JWT so any instance serves any request",
 "Sticky sessions are a workaround, not a scaling strategy",
 "The database is usually the bottleneck: index, cache, replicate, then shard",
 "Use async queues and CDNs to remove work from the request path",
 "Design for ~10x current load, not 1000x"],
[("What is the difference between vertical and horizontal scaling?",
 "Vertical scaling adds resources to one machine (more CPU/RAM). It is simple and keeps consistency easy, but has a hardware ceiling, rising cost and remains a single point of failure. Horizontal scaling adds more machines behind a load balancer. It offers near-unlimited capacity and fault tolerance but adds complexity: distributing data, keeping it consistent and handling partial failures. Typically the stateless app tier scales horizontally while databases scale vertically first and are sharded later."),
 ("What makes a service stateless and why does it matter?",
 "A stateless service keeps no client-specific data in its own memory between requests; sessions, carts and uploads live in external stores like Redis, a DB or the token itself (JWT). This lets any instance handle any request, so you can add or remove instances freely, autoscale, do rolling deploys and survive instance crashes without users losing data."),
 ("How would you store HTTP sessions in a horizontally scaled Spring Boot app?",
 "Use Spring Session with Redis: sessions are serialised into Redis keyed by session ID, so every instance can read them. Alternatively use stateless JWT access tokens validated by each instance with a shared public key. Sticky sessions at the load balancer also work but cause uneven load and lose sessions when an instance dies, so I'd avoid relying on them."),
 ("Your app is slow under load. How do you find and fix the bottleneck?",
 "First measure: check p99 latency, CPU, memory, thread pools, DB connection pool wait time and slow query logs. If app CPU is high, add instances. If DB is the issue, add missing indexes, fix N+1 JPA queries, cache hot reads in Redis, route reads to replicas, and move non-critical work to a queue. Only shard when a single primary truly cannot handle writes or data size."),
 ("When would you choose vertical scaling over horizontal?",
 "For a relational database early on, because a bigger box avoids sharding complexity and keeps transactions simple. Also for quick relief when there is no time to redesign. Horizontal scaling becomes necessary when hitting hardware limits, needing high availability, or when cost per unit of capacity of huge machines becomes too high.")],
[PRIMER, DDIA, ("AWS - Scale up vs scale out", "https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html")]))

topics.append(T("load-balancing", "Load Balancing", "Basic",
"How load balancers distribute traffic across servers, the L4 vs L7 difference, common algorithms, health checks and avoiding the LB itself as a single point of failure.",
r'''
## What a load balancer does

A load balancer (LB) sits between clients and a pool of servers and spreads incoming requests across them. It gives you:

- **Scalability**: add servers behind it.
- **Availability**: health checks remove dead servers automatically.
- **Single entry point**: one DNS name/IP for clients, TLS termination, central place for rate limits and WAF.

```text
               +-> [App 1]
Client -> LB --+-> [App 2]
               +-> [App 3]
```

Load balancers appear at several layers: DNS (GeoDNS routes India users to Mumbai region), edge/CDN, in front of web servers, between internal services (client-side LB in Spring Cloud LoadBalancer or service mesh), and in front of databases (ProxySQL for MySQL read replicas).

## L4 vs L7 load balancing

| | Layer 4 (transport) | Layer 7 (application) |
|---|---|---|
| Sees | IP, port, TCP/UDP | HTTP headers, URL path, cookies |
| Routing | Per connection | Per request (path `/api/orders` → order service) |
| Speed | Very fast, low CPU | Slower, parses HTTP |
| Features | Simple forwarding | TLS termination, path routing, header rewrite, caching, auth |
| Examples | AWS NLB, HAProxy (TCP mode), LVS | AWS ALB, Nginx, Envoy, HAProxy (HTTP mode) |

Use L4 for raw throughput or non-HTTP protocols (WebSocket TCP pass-through, database proxies). Use L7 for microservices routing, A/B testing and canary releases.

## Algorithms

- **Round robin**: each server in turn. Simple; good when servers and requests are similar.
- **Weighted round robin**: bigger servers get more traffic; useful during canary (5% to new version).
- **Least connections**: send to the server with fewest active connections. Good for long-lived connections (WebSockets) or varied request durations.
- **Least response time**: considers latency and connections.
- **IP hash / consistent hashing**: same client (or key) goes to the same server. Useful for cache locality or session affinity; consistent hashing minimises remapping when servers change.
- **Random / power of two choices**: pick two random servers, send to the less loaded. Surprisingly effective and cheap at scale.

## Health checks

The LB periodically calls something like `GET /actuator/health` on each instance. After N failures (e.g., 3 checks 10 s apart) it marks the instance unhealthy and stops routing. In Spring Boot, Actuator exposes **liveness** (is the JVM alive? restart if not) and **readiness** (can it take traffic? e.g., DB pool ready). Kubernetes uses both probes. Readiness must go false during graceful shutdown so in-flight requests finish while no new ones arrive.

## Sticky sessions

Session affinity sends a user to the same server, usually via a cookie. It helps legacy stateful apps but causes uneven load and loses session data when a server dies. Prefer stateless services with Redis-backed sessions or JWTs.

## Avoiding the LB as a single point of failure

The LB itself can fail. Solutions:

- **Active-passive pair** with a floating virtual IP (keepalived/VRRP): the standby takes the IP on failure.
- **Active-active** behind DNS with multiple IPs.
- **Managed cloud LBs** (AWS ALB/NLB) are internally redundant across availability zones.

## TLS termination

The LB decrypts HTTPS and forwards plain HTTP (or re-encrypted HTTPS) to backends. This offloads CPU-heavy handshakes from app servers and centralises certificate management. For strict compliance (payments), re-encrypt to the backend or use mTLS inside the network.

## Global load balancing

For multi-region systems: GeoDNS or anycast routes users to the nearest healthy region. Route 53 latency-based routing, Cloudflare anycast. Failover policies send traffic to another region if one is down.

## Reverse proxy vs load balancer vs API gateway

- **Reverse proxy** (Nginx): fronts servers, can cache, compress, terminate TLS; may have just one backend.
- **Load balancer**: specifically distributes across many backends.
- **API gateway**: L7 proxy with API concerns: authentication, rate limiting, request transformation, routing to microservices (Spring Cloud Gateway, Kong).

In practice Nginx or Envoy can do all three.

## Practical numbers

A single Nginx instance can handle tens of thousands of requests/second; an L4 balancer can push millions of packets/second. The LB is rarely the bottleneck; backends and the database are.

## Interview usage

In almost every design, draw an LB in front of stateless services and say: "L7 load balancer, round robin or least connections, health checks on /health, deployed redundantly across AZs, terminates TLS." For WebSocket chat, say: "L4 or WebSocket-aware L7 LB with least-connections, since connections are long-lived."
''',
["LB spreads traffic, removes unhealthy servers and provides one entry point",
 "L4 routes by IP/port (fast); L7 routes by HTTP path/headers (smart)",
 "Round robin, weighted, least connections, IP/consistent hash, power of two choices",
 "Health checks: liveness vs readiness (Spring Actuator, Kubernetes probes)",
 "Avoid sticky sessions; keep services stateless",
 "Make the LB redundant: active-passive with VIP, or managed multi-AZ LB",
 "LB often terminates TLS to offload backends"],
[("What is the difference between an L4 and L7 load balancer?",
 "An L4 LB works at the transport layer: it routes TCP/UDP connections based on IP and port without reading the payload, so it is very fast and protocol-agnostic. An L7 LB understands HTTP, so it can route by URL path, host or headers, terminate TLS, rewrite headers and do canary splits, at the cost of more CPU. Microservices typically use L7 (ALB, Nginx, Envoy); raw TCP or extreme throughput uses L4 (NLB)."),
 ("Which load balancing algorithm would you use for WebSocket servers and why?",
 "Least connections. WebSocket connections are long-lived, so round robin can leave some servers with many more active connections than others over time. Least connections sends new connections to the server currently holding the fewest, keeping memory and CPU balanced. Weighted variants help when servers have different capacities."),
 ("How do health checks work and what is the difference between liveness and readiness?",
 "The LB or orchestrator periodically probes an endpoint; after consecutive failures it stops routing to that instance. Liveness answers 'is the process alive?'; failing it causes a restart. Readiness answers 'can it serve traffic now?'; failing it removes the instance from rotation without restarting, useful during startup, warm-up or graceful shutdown. Spring Boot Actuator exposes both."),
 ("How do you prevent the load balancer from being a single point of failure?",
 "Run at least two LB instances. In active-passive mode a virtual IP floats to the standby using VRRP (keepalived) if the active fails. In active-active mode DNS returns multiple LB IPs. Cloud managed LBs like AWS ALB are distributed across availability zones internally. For regional failure, use DNS-based global load balancing to another region."),
 ("What are sticky sessions and why are they discouraged?",
 "Sticky sessions route a user to the same backend each time, typically via a cookie, so in-memory session state keeps working. They cause uneven load (heavy users pin to one server), complicate scaling down, and lose session data if that server dies. Externalising session state to Redis or using JWTs makes servers interchangeable, which is better.")],
[PRIMER, ("NGINX - What is load balancing", "https://www.nginx.com/resources/glossary/load-balancing/"), ("AWS Elastic Load Balancing docs", "https://docs.aws.amazon.com/elasticloadbalancing/")]))

topics.append(T("caching", "Caching", "Intermediate",
"Using fast in-memory stores like Redis to cut latency and database load: patterns, eviction, invalidation, and failure modes like stampedes.",
r'''
## Why cache

A cache stores copies of frequently read data in fast storage (memory) so you avoid recomputing it or re-reading it from a slower store. A MySQL query might take 5-20 ms; a Redis GET takes ~0.2-0.5 ms over the network; a local in-process cache lookup takes nanoseconds. For a read-heavy service with a 90% hit rate, the database sees only 10% of reads.

## Where caches live

| Layer | Example | Notes |
|---|---|---|
| Browser | HTTP Cache-Control, ETag | Free, per user |
| CDN | CloudFront, Akamai | Static assets, images, even API responses |
| API gateway / reverse proxy | Nginx cache | Whole responses |
| Application local | Caffeine, Guava | Fastest, but each instance has its own copy |
| Distributed cache | Redis, Memcached | Shared by all instances |
| Database | InnoDB buffer pool | Hot pages in memory |

## Caching patterns

### Cache-aside (lazy loading) – the default

```java
public Product get(long id) {
    String key = "product:" + id;
    Product p = redis.get(key);
    if (p != null) return p;                 // hit
    p = productRepo.findById(id).orElseThrow(); // miss
    redis.setex(key, 3600, p);               // populate with TTL
    return p;
}
```

In Spring: `@Cacheable(value="product", key="#id")` with a Redis CacheManager. On updates: write DB, then **delete** the cache key (`@CacheEvict`). Deleting is safer than updating because two concurrent updates could write stale values in the wrong order.

- Pros: only requested data is cached; cache failure just means slower reads.
- Cons: first request is a miss; possible stale data window.

### Read-through

The cache itself loads from the DB on a miss (application talks only to the cache). Same behaviour as cache-aside but logic lives in the cache provider.

### Write-through

Write goes to cache and DB synchronously. Cache always fresh; writes slower; cache fills with data that may never be read.

### Write-behind (write-back)

Write to cache, asynchronously flush to DB in batches. Very fast writes, but risk of data loss if the cache node dies before flushing. Used for counters (views, likes) where small loss is acceptable.

### Write-around

Write directly to DB, bypass the cache; data enters the cache only on read. Good when written data is rarely read soon.

## Eviction policies

Memory is limited, so something must go:

- **LRU** (least recently used): most common; Redis `allkeys-lru`.
- **LFU** (least frequently used): better when popularity is stable; Redis `allkeys-lfu`.
- **FIFO**, **random**.
- **TTL**: every key expires after a time. Always set a TTL as a safety net against stale data and memory leaks.

## Cache invalidation

"There are only two hard things in computer science: cache invalidation and naming things." Options:

1. **TTL only**: simple, tolerate staleness up to TTL (e.g., product catalog 10 min).
2. **Delete on write**: app deletes key after updating DB.
3. **Event-driven**: DB change events (Debezium CDC from MySQL binlog → Kafka → cache invalidator). Robust across many services.
4. **Versioned keys**: `product:42:v7`; bump version on change.

A classic race: thread A reads miss, loads old value from DB; thread B updates DB and deletes key; thread A writes old value into cache. Mitigations: short TTLs, delete twice with a small delay ("delayed double delete"), or CDC-based invalidation.

## Failure modes you must know

### Cache stampede (thundering herd)

A hot key expires and 10,000 concurrent requests all miss and hit the DB at once. Fixes:

- **Mutex / single flight**: only one request recomputes (Redis `SET lock NX EX 5`); others wait or serve stale.
- **Early probabilistic refresh**: refresh before expiry with some randomness.
- **Serve stale while revalidating** in the background.

### Cache penetration

Requests for keys that do not exist (e.g., attacker querying random IDs) always miss and hit the DB. Fix: cache negative results ("null" with short TTL) or use a **Bloom filter** of valid IDs.

### Cache avalanche

Many keys expire at the same moment (all set with TTL 3600 at startup) or the cache cluster crashes. Fix: add random jitter to TTLs (3600 ± 300 s), use replicated Redis, and rate-limit DB access with circuit breakers.

### Hot keys

One key (a celebrity profile, a flash-sale product) gets so much traffic that one Redis shard melts. Fix: local in-process cache in front of Redis for hot keys, or replicate the key with suffixes (`product:42#1..#10`) and pick randomly.

## Redis essentials

- In-memory key-value store, single-threaded command execution (so commands are atomic), ~100k+ ops/s per node.
- Data structures: strings, hashes, lists, sets, sorted sets (leaderboards, sliding-window rate limits), streams, HyperLogLog (unique counts), geo (nearby drivers).
- Persistence: RDB snapshots and AOF logs; still treat it as a cache unless designed otherwise.
- High availability: Redis Sentinel (primary-replica failover) or **Redis Cluster** (16,384 hash slots spread across shards).
- Memcached: simpler, multi-threaded, strings only, no persistence.

## What to cache and what not to

Cache: read-heavy, rarely changing, expensive-to-compute data (product details, user profiles, config, session, computed feeds). Avoid caching: rapidly changing data that must be exact (account balance, seat availability at the moment of booking) unless you accept staleness and re-check at the source of truth before committing.

## Interview phrasing

"Read:write is 100:1, so I'll put Redis in front of MySQL with cache-aside, TTL of one hour plus jitter, delete-on-update, LRU eviction. For hot keys I'll add a small Caffeine cache in each instance. To avoid stampedes on popular items I'll use a Redis lock so only one request rebuilds the value."
''',
["Cache-aside: read cache, on miss load DB and populate; on write update DB then delete key",
 "Write-through = sync both; write-behind = async flush (fast, may lose data)",
 "Always set TTLs; add jitter to avoid mass expiry (avalanche)",
 "Stampede fix: lock/single-flight, early refresh, serve stale",
 "Penetration fix: cache nulls or use a Bloom filter",
 "Hot keys: local cache in front of Redis or key replication",
 "Redis: single-threaded, ~100k ops/s, rich data structures, Cluster has 16,384 slots",
 "Never trust cache for final correctness checks (balances, seats)"],
[("Explain cache-aside and how you'd implement it in Spring Boot.",
 "In cache-aside the application checks the cache first; on a miss it reads from the DB and stores the result in the cache with a TTL. On updates it writes to the DB and then deletes the cache key so the next read reloads fresh data. In Spring Boot I'd enable caching with a RedisCacheManager, use `@Cacheable` on the read method, `@CacheEvict` on update/delete methods, and configure TTL per cache name."),
 ("Why delete the cache key on update instead of updating it?",
 "If two requests update the same record concurrently, their DB writes and cache writes may interleave in different orders, leaving the cache with the older value permanently (until TTL). Deleting is idempotent: the next reader loads the latest committed value from the DB. It also avoids computing cache values that may never be read."),
 ("What is a cache stampede and how do you prevent it?",
 "When a popular key expires, many concurrent requests miss simultaneously and all hit the database, which can overload it. Prevention: let only one request rebuild the value using a distributed lock (Redis SET NX with expiry) while others wait briefly or get the stale value; refresh hot keys proactively before expiry; and add random jitter to TTLs so keys don't expire together."),
 ("How would you handle cache invalidation across multiple microservices?",
 "Use change data capture: Debezium reads the MySQL binlog and publishes row changes to Kafka; a consumer in each service that caches the data deletes the relevant keys. This decouples writers from cache logic and catches updates made by any path, including manual SQL. Combine with TTLs as a safety net for missed events."),
 ("When should you not use a cache?",
 "When data changes constantly and must be exact at read time (wallet balance, inventory at checkout), when the access pattern has low reuse so the hit rate would be poor, or when the DB already serves the load comfortably. Caches add staleness, extra failure modes and operational cost; if used for critical data, always verify against the source of truth before committing."),
 ("Redis vs Memcached?",
 "Both are in-memory key-value stores. Redis supports rich data structures (hashes, sorted sets, streams, geo), persistence, replication, Lua scripting, pub/sub and clustering. Memcached is simpler, multi-threaded, stores only strings and has no persistence. Today Redis is the default choice; Memcached is used for very simple, large-scale object caching.")],
[PRIMER, ("Redis documentation", "https://redis.io/docs/latest/"), ("AWS - Caching best practices", "https://aws.amazon.com/caching/best-practices/"), ("Facebook - Scaling Memcache at Facebook", "https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf")]))

topics.append(T("databases-sql-vs-nosql", "Databases: SQL vs NoSQL", "Basic",
"How to choose between relational databases and NoSQL families (key-value, document, wide-column, graph) based on data shape, access patterns and consistency needs.",
r'''
## The core question

Choosing a database is choosing trade-offs. Interviewers do not want "NoSQL because it scales". They want: "Here is the data, here is how it is read and written, therefore this store." Start from **access patterns**.

## Relational databases (MySQL, PostgreSQL)

Data in tables with fixed schemas, related by foreign keys, queried with SQL.

Strengths:
- **ACID transactions**: transfer money, place an order and decrement stock atomically.
- **Joins and ad-hoc queries**: reporting, admin panels, flexible querying.
- **Mature tooling**: Spring Data JPA, Flyway migrations, decades of operational knowledge.
- **Constraints**: unique, foreign keys, NOT NULL protect data integrity.

Weaknesses:
- Horizontal write scaling needs manual sharding (Vitess for MySQL, Citus for Postgres).
- Schema changes on huge tables can be painful (use online tools like gh-ost, pt-online-schema-change).
- Rigid for highly variable attributes.

A single well-tuned MySQL instance handles thousands of writes/s and terabytes of data. Most systems at most companies can live on relational databases with replicas and caching.

## NoSQL families

### Key-value stores (Redis, DynamoDB, Riak)
Get/put by key. Extremely fast and easy to partition. Use for sessions, caches, carts, feature flags, rate-limit counters. No queries beyond the key (DynamoDB adds sort keys and secondary indexes).

### Document stores (MongoDB, Couchbase)
Store JSON-like documents; each can have different fields; nested data in one record.

```json
{ "_id": "p42", "name": "iPhone 16", "price": 79999,
  "attributes": {"color": "black", "storage": "256GB"},
  "variants": [{"sku": "A1", "stock": 10}] }
```

Good for product catalogs with varied attributes, CMS content, user profiles. Reads of a whole aggregate are a single fetch. Weaker for many-to-many relationships and cross-document transactions (Mongo supports multi-document transactions now, but with cost).

### Wide-column stores (Cassandra, HBase, ScyllaDB)
Rows grouped by a **partition key**, sorted by a **clustering key** within the partition. Built on LSM trees for very high write throughput, leaderless replication, linear horizontal scaling.

```sql
CREATE TABLE messages (
  conversation_id uuid,
  message_time timeuuid,
  sender_id bigint,
  body text,
  PRIMARY KEY ((conversation_id), message_time)
) WITH CLUSTERING ORDER BY (message_time DESC);
```

Ideal for chat messages, time-series, activity logs, IoT. You design tables **per query**; no joins, limited ad-hoc queries; tunable consistency.

### Graph databases (Neo4j, Amazon Neptune)
Nodes and edges; efficient multi-hop traversal ("friends of friends who like X"). Use for social graphs, recommendations, fraud rings.

### Others worth naming
- **Search engines** (Elasticsearch): full-text search, faceting.
- **Time-series DBs** (InfluxDB, Prometheus, TimescaleDB): metrics.
- **Object/blob storage** (S3): images, videos, backups. Never put big files in your DB.
- **NewSQL** (Google Spanner, CockroachDB, TiDB, YugabyteDB): SQL and ACID with automatic horizontal scaling, at the cost of higher write latency.

## Comparison table

| Factor | SQL | NoSQL (typical) |
|---|---|---|
| Schema | Fixed, enforced | Flexible / schema-on-read |
| Transactions | Multi-row ACID | Often single-key/partition atomicity |
| Joins | Yes | Usually no; denormalise |
| Scaling writes | Vertical, then manual sharding | Built-in partitioning |
| Consistency | Strong by default | Often eventual or tunable |
| Query flexibility | High | Limited to designed access paths |

## How to decide (interview heuristic)

1. **Need transactions across entities or strong consistency?** (payments, orders, inventory, bookings) → SQL.
2. **Massive write volume, simple access by key + time?** (messages, logs, events, location pings) → Cassandra/DynamoDB.
3. **Highly variable attributes, read as a whole?** → MongoDB, or MySQL JSON column.
4. **Relationship traversal?** → Graph DB.
5. **Text search?** → Elasticsearch alongside the primary DB.
6. **Ephemeral, super-fast access?** → Redis.

Real systems use **polyglot persistence**: Flipkart-like checkout uses MySQL for orders, Redis for carts and sessions, Elasticsearch for product search, Cassandra or HBase for user activity, S3 for images.

## Normalisation vs denormalisation

Normalisation removes duplication (third normal form), so updates touch one place but reads need joins. Denormalisation duplicates data (store `author_name` in each post) for faster reads but requires updating many copies. NoSQL designs denormalise heavily because there are no joins; SQL systems denormalise selectively for hot read paths.

## Common misconceptions

- "SQL doesn't scale": Facebook, YouTube, Uber and Shopify run huge sharded MySQL fleets.
- "NoSQL has no schema": the schema lives in your code; changing it still needs migration thinking.
- "MongoDB is always faster": only for access patterns it was modelled for.

## Interview phrasing

"Orders and payments need ACID and joins for reporting, so MySQL, sharded by user_id later if needed. Order-status events are high-volume and append-only, so they go to Kafka and then Cassandra keyed by order_id. Product search goes to Elasticsearch, kept in sync through CDC."
''',
["Choose storage from access patterns and consistency needs, not hype",
 "SQL: ACID, joins, constraints; scales writes via sharding (Vitess)",
 "Key-value: fast get/put by key (Redis, DynamoDB)",
 "Document: flexible JSON aggregates (MongoDB) for catalogs/profiles",
 "Wide-column: partition + clustering key, huge writes (Cassandra) for chat/time-series",
 "Graph DB for multi-hop relationships; Elasticsearch for text search",
 "Polyglot persistence is normal in real systems",
 "NoSQL means denormalise and design tables per query"],
[("When would you choose MySQL over MongoDB?",
 "When data is relational and integrity matters: orders, payments, inventory, bookings. MySQL gives multi-row ACID transactions, foreign keys, unique constraints, joins for reporting, and mature tooling like JPA and Flyway. MongoDB fits better for aggregates with varied attributes read as a whole, like product catalogs. If I mostly need joins and transactions, I choose MySQL."),
 ("Why is Cassandra good for storing chat messages?",
 "Chat is write-heavy and accessed by conversation and time. Cassandra partitions by conversation_id and sorts by message timestamp, so fetching the latest 50 messages is one sequential read from one partition. Its LSM-tree storage makes writes very fast, it scales linearly by adding nodes, and replication across nodes gives high availability. We don't need joins or multi-row transactions here."),
 ("What is polyglot persistence? Give an example.",
 "Using different databases for different parts of a system based on their access patterns. In an e-commerce app: MySQL for orders and payments (transactions), Redis for sessions and carts (speed), Elasticsearch for product search (full-text), S3 for images, and Cassandra for clickstream/activity data (high write volume). The cost is operational complexity and keeping data in sync, usually via events or CDC."),
 ("Can SQL databases scale horizontally?",
 "Yes, with effort. Reads scale with replicas. Writes scale through sharding: splitting data by a key like user_id across multiple primaries, often using a layer like Vitess (YouTube, Slack) or application-level routing. NewSQL databases like CockroachDB, TiDB and Spanner do automatic sharding with ACID. The trade-off is that cross-shard joins and transactions become hard or expensive."),
 ("What is denormalisation and when is it worth it?",
 "Denormalisation stores redundant copies of data to avoid joins at read time, for example storing author name and avatar in each post row or a precomputed order total. It's worth it for read-heavy hot paths where join latency matters, and essential in NoSQL stores without joins. The cost is more complex writes, since every copy must be updated, often asynchronously, introducing temporary inconsistency.")],
[PRIMER, DDIA, ("MongoDB - SQL vs NoSQL", "https://www.mongodb.com/resources/basics/databases/nosql-explained/nosql-vs-sql"), ("Apache Cassandra documentation", "https://cassandra.apache.org/doc/latest/")]))

dump("sd_part1.json", topics)
