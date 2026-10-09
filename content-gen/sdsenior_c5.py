"""Senior SD chunk 5: webhook delivery system, collaborative editor."""
from sdsenior_common import *

topics = []

# ---------------------------------------------------------------- 12
topics.append(T("webhook-delivery-system", "Reliable Webhook Delivery System", 12, "case-study", "Intermediate",
"Outbound webhooks done properly: at-least-once delivery with backoff over days, HMAC signing with replay protection, per-endpoint isolation so one dead URL can't slow everyone, dead-lettering, replay, and SSRF-safe egress.",
r'''
## 1. Requirements

You are the platform (think Razorpay or Stripe) sending events such as `payment.captured` to thousands of merchant servers that you don't control. Some will be slow, some down for hours, and some deliberately malicious.

**Functional**
- Tenants register endpoints (HTTPS URL, subscribed event types) and get a signing secret.
- Each event is POSTed to every subscribed endpoint, and failures are retried with backoff for up to about 3 days.
- Payloads are signed so receivers can verify them. Delivery logs, manual and bulk replay, secret rotation.
- Endpoints that keep failing are auto-disabled, and the tenant is notified.

**Non-functional**
- **At-least-once** delivery. No event lost once accepted.
- First attempt within 5 s p99 of the event.
- 50k events/s peak, about 1M registered endpoints.
- **Isolation**: a slow or dead endpoint must not delay other tenants.
- Security: unforgeable, replay-resistant, SSRF-safe.

## 2. Estimates

- 50k events/s × 2 subscriptions on average = **100k deliveries/s**.
- Little's law decides the worker design. Healthy endpoints answer in about 300 ms, so 100k/s × 0.3 s = 30k requests in flight. If just 10% of traffic goes to endpoints that hang until a 10 s timeout, that adds 10k/s × 10 s = **100k extra in-flight requests**. Thread-per-request designs collapse, so use non-blocking HTTP (Netty/WebClient) and **cap in-flight requests per endpoint**.
- Attempt logs: 100k/s × 1 KB ≈ 8.6 TB a day. Keep 7 days hot in ClickHouse or Elasticsearch and 30 days in S3.

## 3. API

```text
POST /v1/webhook-endpoints {"url":"https://shop.example/hooks","events":["payment.*"]}
     -> {"id":"we_12","secret":"whsec_..."}
POST /v1/webhook-endpoints/{id}/rotate-secret   {"expireOldAfterHours":24}
GET  /v1/events/{eventId}/deliveries            -> attempts, status codes, latency
POST /v1/webhook-endpoints/{id}/replay          {"from":"...","to":"...","status":"FAILED"}

Outbound request (Standard Webhooks style headers):
POST https://shop.example/hooks
webhook-id: evt_8f2...            (stable across retries -> receiver dedupes)
webhook-timestamp: 1760000000
webhook-signature: v1,<base64 HMAC-SHA256(secret, id + "." + timestamp + "." + body)>
{"id":"evt_8f2","type":"payment.captured","created":1760000000,"data":{...}}
```

## 4. Data model

```sql
CREATE TABLE endpoints (id VARCHAR(32) PRIMARY KEY, tenant_id BIGINT, url VARCHAR(2048),
  events JSON, status ENUM('ACTIVE','DEGRADED','DISABLED'), failing_since DATETIME,
  INDEX (tenant_id));
CREATE TABLE endpoint_secrets (endpoint_id VARCHAR(32), version INT, secret_enc VARBINARY(256),
  expires_at DATETIME NULL, PRIMARY KEY (endpoint_id, version));   -- 2 active during rotation
CREATE TABLE deliveries (id BIGINT PRIMARY KEY, event_id VARCHAR(32), endpoint_id VARCHAR(32),
  status ENUM('PENDING','SUCCEEDED','RETRYING','DEAD'), attempt INT, next_attempt_at DATETIME(3),
  last_code INT, last_error VARCHAR(255),
  UNIQUE KEY (event_id, endpoint_id), INDEX (status, next_attempt_at));
-- events are immutable, stored once (payload) and referenced by deliveries
```

## 5. High-level design

```text
 Payment/Order services --(outbox, same DB txn)--> Kafka: events
                                                      |
                                    [Fan-out]: subscription cache (tenant, type) -> endpoints
                                                      |   create delivery (event_id, endpoint_id)
                                     Kafka: deliveries  (key = endpoint_id)
                                                      |
             [Dispatchers]: per-endpoint in-flight cap + token bucket + breaker, non-blocking HTTP
                 | sign (HMAC)            | fail
                 v                         v
    [Egress proxy: SSRF filter,     [Retry tiers]: delay topics 1m/5m/30m/2h/6h/12h ... (≈3 days)
     fixed egress IPs, TLS>=1.2]          | exhausted -> DEAD + tenant email + replay UI
                 |
        Merchant endpoints
 Attempt logs -> ClickHouse/S3     Metrics -> Prometheus     Endpoint health -> endpoints.status
```

## 6. Deep dives

### 6.1 Capture events reliably

Never send webhooks from the request thread. The payment service writes the event to an **outbox** in the same transaction as the payment state change, and a relay publishes to Kafka. Fan-out creates one delivery per endpoint, with `UNIQUE(event_id, endpoint_id)` making fan-out retries idempotent.

### 6.2 Retry policy

- Success means **2xx within the timeout** (connect 3 s, total 10-15 s). Treat redirects as failures (Stripe does) and don't follow them, because redirects are an SSRF vector.
- Back off exponentially with jitter: immediately, then 1 min, 5 min, 30 min, 2 h, 6 h, 12 h, and so on, for about 3 days. Stripe retries live-mode events for up to three days.
- `410 Gone` disables the endpoint. Everything else retries until the schedule runs out, then the delivery goes **DEAD**, the tenant is emailed, and the replay UI shows it.
- Retries go to separate **delay topics** so the main partition never waits on a failing delivery.

### 6.3 Isolation and per-tenant fairness

This is the core of a senior answer. Problems: **head-of-line blocking** (a partition stuck behind one slow endpoint), and **worker exhaustion** (hung connections occupying everything).

- **Per-endpoint in-flight cap** (say 10) and a token bucket, enforced in the dispatcher, plus non-blocking I/O so waiting costs memory, not threads.
- **Endpoint circuit breaker**: after N consecutive failures, mark the endpoint `DEGRADED`. Its new events skip the live lane and go straight to retry tiers, with only an occasional probe attempt. When a probe succeeds, it returns to `ACTIVE` and its backlog drains **at a limited rate**.
- **Lanes (bulkheads)**: healthy endpoints and degraded endpoints use separate consumer groups and worker pools.
- **Weighted fairness** across tenants, so a tenant that emits 10M events in a batch job drains at its quota without starving others.

### 6.4 Ordering

Default: **no ordering guarantee**, and say so in the docs. Stripe explicitly doesn't guarantee order and tells receivers to dedupe by event ID. Retries reorder events anyway. Better options for receivers:

- **Thin events**: send `{type, resourceId}` and let the receiver fetch the latest state with the API. This removes both staleness and ordering issues.
- Include a per-resource `sequence` or `version`, so receivers can ignore older events.
- If strict ordering is a product requirement, partition by `(endpoint, resourceId)` and deliver serially. Then one failing event blocks later events for that resource, which is the explicit trade-off.

### 6.5 Signing, replay protection and rotation

HMAC-SHA256 over `id.timestamp.body` with the endpoint secret. Receivers recompute it over the **raw** body, compare in **constant time**, and reject timestamps outside a tolerance window (Stripe's libraries default to 5 minutes). Every attempt gets a fresh timestamp and signature, while `webhook-id` stays the same across retries so receivers can dedupe. Rotation: keep two secrets active for up to 24 hours and send a signature for each, so tenants can deploy the new secret without downtime. Store secrets encrypted with KMS.

### 6.6 SSRF and abuse

Tenants control the URL, so someone will register `http://169.254.169.254/` (cloud metadata) or an internal hostname. Defences: HTTPS only. Resolve DNS **and validate the IP at connect time**, blocking private, loopback and link-local ranges, which also prevents DNS-rebinding tricks. Don't follow redirects. Send through an **egress proxy** in an isolated network with fixed public IPs that customers can allowlist. Cap response size and read time.

### 6.7 Recovering from your own outage

If dispatch was down for an hour, don't fire the whole backlog at once: you would DDoS every merchant at the same moment. Drain with per-endpoint rate limits, newest-first or oldest-first per tenant policy, and alert tenants proactively. Deliveries are idempotent on the receiver side by `webhook-id`, so a second region can take over dispatch safely, even if that causes some duplicates.

## 7. Observability: "Is it us or them?"

- First-attempt latency p99 (event created to first attempt), the oldest pending delivery per retry tier, and backlog size.
- Success rate **per endpoint** (shown to the tenant) and **globally**. Key insight: one endpoint failing is *their* problem. Thousands failing at once, or errors clustered by type (DNS, TLS handshake, connect timeouts from one egress IP), is **our** problem: proxy, NAT, an expired certificate, a DNS resolver. Alert on a global success-rate drop against the baseline.
- DEAD deliveries per hour, auto-disabled endpoints, and replay volume.
- Dispatcher saturation: in-flight connections, event-loop lag and breaker states.

## 8. Trade-offs

- **Ordering vs throughput and isolation**: serial per-resource delivery blocks on failures.
- **Fat vs thin payloads**: fat payloads mean no extra API calls but stale and ordering-sensitive data. Thin payloads are always fresh but add load on your API.
- **Retry window length**: longer windows recover more customer outages but grow backlog storage and duplicate risk.
- **Build vs buy**: Svix and Hookdeck sell exactly this. Build it when webhooks are core to your product and the scale justifies a team.
''',
[
 "Capture events with an outbox and fan out to deliveries with UNIQUE(event_id, endpoint_id). Never send webhooks inline from the request thread.",
 "At-least-once delivery: 2xx within a timeout is success. Exponential backoff with jitter for about 3 days (as Stripe does), then DEAD, notify and allow replay.",
 "Little's law shows hung endpoints exhaust thread-per-request designs. Use non-blocking HTTP with per-endpoint in-flight caps.",
 "Isolation: endpoint circuit breakers, separate lanes for healthy and degraded endpoints, delay topics for retries, weighted tenant fairness, and rate-limited backlog drains.",
 "No ordering guarantee by default. Offer thin events, per-resource versions, or serial per-resource delivery as an explicit trade-off.",
 "Sign HMAC-SHA256 over id.timestamp.body. Receivers verify the raw body in constant time with a 5-minute tolerance. Keep two secrets active during rotation.",
 "SSRF defence: HTTPS only, IP validation at connect time, no redirects, an isolated egress proxy with fixed IPs.",
 "Observability answers 'us or them': per-endpoint vs global success rate, error-type clustering, first-attempt latency and oldest-pending age."
],
[
 ("A merchant's endpoint is down for six hours. What happens to their events?",
  r'''Deliveries fail and move through the retry tiers with exponential backoff and jitter. After a few consecutive failures the endpoint's breaker marks it DEGRADED, so new events skip the live lane and queue in retry tiers instead of tying up dispatchers, with occasional probe attempts. Nothing is lost: deliveries persist with their next attempt time. When a probe succeeds, the endpoint returns to ACTIVE and the backlog drains at a capped rate so we don't flatten their recovering server. Throughout, the dashboard shows failures and we email the tenant. Anything still failing after about 3 days goes DEAD with a replay button.'''),
 ("One customer's endpoint takes 30 seconds to respond. How do you stop it slowing everyone else?",
  r'''Several layers. A total timeout of 10-15 seconds means we never wait 30. Dispatchers use non-blocking HTTP, so a slow request costs a connection and memory, not a thread. Each endpoint has an in-flight cap (around 10), so it can occupy at most 10 slots no matter how many events it has. Repeated timeouts trip its breaker and move it to the degraded lane with its own worker pool and retry topics, so healthy endpoints' partitions keep flowing. Tenant-level weighted fairness stops any single tenant's volume from monopolising dispatch capacity.'''),
 ("How does a receiver know a webhook really came from you and isn't a replay?",
  r'''Each request carries a webhook ID, a timestamp and an HMAC-SHA256 signature computed with the endpoint's secret over the ID, timestamp and raw body. The receiver recomputes it over the unparsed body and compares in constant time, so a forged or modified payload fails. Because the timestamp is signed, an attacker can't refresh an old request; receivers reject timestamps more than about 5 minutes old. Retries get a new timestamp and signature but the same ID, so receivers dedupe on it. We can also publish fixed egress IPs for allowlisting.'''),
 ("Do you guarantee events are delivered in order?",
  r'''Not by default, and I'd document that, as Stripe does. Retries, parallel dispatch and failures all reorder events, and strict ordering would let one failed delivery block everything behind it. Instead I'd give receivers tools: a stable event ID for dedupe, a per-resource version or sequence number so they can ignore stale updates, and thin events, where the receiver fetches the current state of the resource. If a customer truly needs ordering, I'd partition by endpoint and resource and deliver serially, accepting head-of-line blocking for that resource.'''),
 ("How do you know webhook delivery is broken, and whether it's your fault or the customer's?",
  r'''Look at the shape of the failures. One endpoint failing while others succeed points to the customer, so it shows on their dashboard and their email, with no page for us. A global drop in success rate against the baseline, many endpoints failing at once, or errors clustered by type (DNS resolution, TLS handshakes, connect timeouts from one egress IP) points to us: the egress proxy, NAT, resolver or an expired certificate. That pages on-call. I'd also alert on first-attempt latency p99 and on the age of the oldest pending delivery per tier, which catch stuck dispatchers even when nothing is failing.'''),
 ("Your dispatch region goes down for an hour. How do you recover without hurting customers?",
  r'''Events keep accumulating safely in the producers' outboxes and in replicated Kafka. A standby dispatcher fleet in the second region starts consuming, which is safe because deliveries are idempotent on the receiver side by webhook ID, and a few duplicates are acceptable. The backlog is the danger: firing an hour of events at once could overwhelm thousands of merchants. So the drain is rate-limited per endpoint and per tenant, the first-attempt latency SLO is suspended, and the status page and proactive emails explain the delay. Afterwards, check that no delivery is stuck in PENDING without a next attempt.''')
],
[STRIPE_WEBHOOKS,
 ("Standard Webhooks - Open specification for webhook signing and delivery", "https://www.standardwebhooks.com/"),
 ("Shopify Dev Docs - About webhooks (delivery, retries, verification)", "https://shopify.dev/docs/apps/build/webhooks"),
 ("OWASP - Server-Side Request Forgery Prevention Cheat Sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html"),
 AWS_RETRY]))

# ---------------------------------------------------------------- 13
topics.append(T("collaborative-editor", "Collaborative Document Editor (Google Docs-like)", 13, "case-study", "Advanced",
"Real-time co-editing at interview depth: operation-based sync with OT or CRDTs, one authoritative server per document over WebSockets, persist-before-ack durability, snapshots and compaction, presence, and detecting divergence.",
r'''
## 1. Requirements

**Functional**
- Create and open a document. Several users edit it at the same time and see each other's changes in real time.
- Presence: who is viewing, with live cursors and selections.
- Version history (restore earlier versions) and permissions (viewer, commenter, editor).
- Stretch goal: offline edits that sync on reconnect.

**Non-functional**
- **Convergence**: once all edits are delivered, every replica shows exactly the same document.
- Remote edits appear in under 200 ms for users in the same region. Local typing is always instant (optimistic).
- **Durability**: an acknowledged edit is never lost.
- Scale: 10M DAU, about 1M documents open at once, usually 1-10 editors per doc, with occasional docs (all-hands notes) at hundreds.

## 2. Estimates

- Clients batch keystrokes every 50-100 ms, so an active typist sends about 1-2 ops/s. With 1M active sessions, peak is about **500k ops/s**, at about 100 B each = 50 MB/s.
- Storing every op: 500k × 86,400 × 100 B ≈ **4 TB a day**. Snapshots and compaction are mandatory.
- WebSockets: 1M connections at about 25-50k per tuned server means 20-40 collaboration servers, plus headroom.

## 3. API

```text
REST
POST /v1/docs                         -> {docId}
GET  /v1/docs/{id}                    -> {snapshot, version, permissions}
GET  /v1/docs/{id}/history?before=v   -> versions list;  POST /v1/docs/{id}/restore {version}

WebSocket  wss://collab/docs/{id}?token=...
client -> {"t":"op","clientOpId":"c7-41","baseVersion":1207,"ops":[{"ins":"Hi","pos":0}]}
server -> {"t":"ack","clientOpId":"c7-41","version":1208}
server -> {"t":"op","version":1209,"author":"u2","ops":[{"del":3,"pos":17}]}
both   -> {"t":"presence","user":"u2","cursor":{"pos":42,"sel":[40,45]}}   (ephemeral)
```

## 4. Data model

```sql
CREATE TABLE documents (id VARCHAR(32) PRIMARY KEY, owner_id BIGINT, title VARCHAR(255),
  snapshot_version BIGINT, snapshot_key VARCHAR(255), updated_at DATETIME(3));
CREATE TABLE doc_ops (doc_id VARCHAR(32), version BIGINT, author_id BIGINT,
  client_op_id VARCHAR(64), ops BLOB, created_at DATETIME(3),
  PRIMARY KEY (doc_id, version),                 -- exactly one op per version
  UNIQUE KEY (doc_id, client_op_id));            -- dedupe client resends
CREATE TABLE doc_permissions (doc_id VARCHAR(32), user_id BIGINT,
  role ENUM('VIEWER','COMMENTER','EDITOR','OWNER'), PRIMARY KEY (doc_id, user_id));
-- snapshots: S3 objects  snapshots/{docId}/{version}
-- presence: in memory on the doc's server (optionally Redis with TTL), never in the op log
```

At large scale, `doc_ops` lives in a wide-column store (Cassandra or Bigtable) partitioned by `doc_id` and clustered by `version`. The access pattern is append and read a range for one doc.

## 5. High-level design

```text
 Browser (editor model + pending ops queue)
     |  WebSocket
 [Edge LB] --route by doc_id--> [Collaboration server: OWNER of doc D]
     |                               - in-memory doc state + recent ops
     |                               - assign version, transform/merge op
     |                               - append to op log (conditional on version) THEN ack
     |                               - broadcast to all sockets of D (+ presence)
     |                                         |
     |                              [Op log: Cassandra/MySQL]   [Snapshotter -> S3]
     |
 [Doc service (REST)]: metadata, permissions, load snapshot + ops since snapshot
 [Routing registry]: doc_id -> owner server (lease in etcd/Redis), consistent hashing fallback
```

## 6. Deep dives

### 6.1 Why the obvious approaches fail

Saving the whole document with last-writer-wins loses one person's paragraph. Locking paragraphs kills real-time collaboration. Sending raw positions breaks too: if A inserts "Hi" at position 0 while B deletes the character at position 5 (based on the old text), applying B's delete as-is removes the wrong character. You need **operation-based sync with a convergence algorithm**.

### 6.2 OT vs CRDT at interview depth

**Operational Transformation (OT)**, used by Google Docs: operations such as `insert(pos, text)` and `delete(pos, len)` are **transformed** against concurrent operations. In the example above, B's delete shifts from 5 to 7 because of A's two-character insert. Google's 2010 post describes exactly this kind of position adjustment. With a **central server**, OT stays manageable:

1. The client sends an op with the `baseVersion` it was based on, and keeps at most one batch in flight.
2. The server transforms the op against every op committed since `baseVersion`, assigns `version = latest + 1`, persists it, acks the author and broadcasts it to the others.
3. Each client transforms incoming ops against its own pending, unacked ops, so local typing never waits.

**CRDTs** (Yjs, Automerge): every character gets a unique ID (`clientId:counter`) and is positioned relative to its neighbours' IDs. Merges are commutative, associative and idempotent, so replicas converge **without a central order**. That's great for offline and peer-to-peer use. The cost is metadata: IDs and tombstones for deleted characters, which need garbage collection. Modern libraries keep it small.

| | OT | CRDT |
|---|---|---|
| Ordering | Needs a central server | Any order, any topology |
| Offline / P2P | Hard (long transforms) | Natural |
| Metadata | Small | IDs + tombstones |
| Complexity | Transform functions are subtle | Library-heavy but proven |

**Figma** went a third way. Its server is the authority, it uses CRDT-inspired, **last-writer-wins per property** for design objects, and it skipped OT as overkill for a non-text editor. A good interview line: *"With a central server I'd use server-ordered OT-style ops, or a CRDT library like Yjs if offline-first matters. Either way, the server architecture below stays the same."*

### 6.3 One owner per document

All editors of document D must reach the **same server**, which orders D's ops in memory. Route through a registry that maps `doc_id` to the owner (a lease in etcd or Redis), or consistent hashing on `doc_id` at the load balancer. When an owner dies, the lease expires. A new owner loads the latest snapshot plus the ops after it, and clients reconnect and **resend unacked ops**, which are deduped by `client_op_id`.

Split-brain guard: the op log's `PRIMARY KEY(doc_id, version)` makes every append conditional. If a zombie owner and a new owner both try to write version 1208, only one succeeds. The loser learns it is stale and drops its sockets.

### 6.4 Durability: persist before ack

The server appends the op to the op log **before** acknowledging it. To keep throughput up, it group-commits the ops of one doc every 10-30 ms. If it crashes after persisting but before acking, the client resends, and the unique `client_op_id` makes the resend a no-op that returns the existing version. Acking before persisting would be faster, but a crash would then lose edits the user saw confirmed.

### 6.5 Taming storage

- The snapshotter writes a full document snapshot to S3 every N ops (for example 500) or after 30 s idle, and updates `snapshot_version`. Loading a doc means fetching the snapshot plus a short tail of ops.
- Version history doesn't need every keystroke forever. Keep fine-grained ops for 30 days, then compact them into periodic checkpoints (hourly or daily), which is what users actually browse.
- CRDT tombstones are garbage-collected once all replicas have seen the deletion.

### 6.6 Presence and cursors

Presence is high-frequency and disposable, so **never persist it**. Throttle it to about 10 updates/s per user, send it through the doc's owner server, and expire it on missed heartbeats so ghost cursors disappear. Cursor positions shift as text changes, so transform them like ops, or anchor them to CRDT character IDs.

### 6.7 Hot docs, offline and permissions

- **Hundreds of viewers**: the owner handles editors, while read-only viewers get updates through a fan-out tier (pub/sub broadcasters). Cap simultaneous editors per document.
- **Offline**: queued ops replay on reconnect. OT transforms them against everything since `baseVersion` (expensive after days offline), while CRDTs merge naturally. Figma's approach is to reload a fresh copy and reapply local edits.
- **Permissions** are checked when the socket connects and on every op. When an editor is downgraded, the server pushes a revocation and closes the socket.

## 7. Observability: "How do we know it's broken?"

- Op round-trip latency (send to ack) and broadcast lag, p99 per region. Op-log append latency.
- **Divergence detection**: clients periodically send a checksum of their document at a given version, and the server compares it with its own. Any mismatch increments a metric, which is a serious bug, and forces that client to reload from the server state.
- WebSocket connections per server, the reconnect rate (a spike means a deploy or network issue), and owner failovers per hour.
- Ops since the last snapshot (snapshotter lag) and document load time p99.

## 8. Trade-offs

- **OT vs CRDT**: central and compact vs decentralised and offline-friendly.
- **Stateful owner servers** (simple ordering, harder failover and rebalancing) vs **stateless servers plus a per-doc ordered log** such as a Kafka partition (easier scaling, extra latency).
- **Persist-before-ack** (durable, adds a few ms) vs ack-first (fast, risks loss).
- **Full history vs compaction**: fine-grained undo and audit vs storage cost.
''',
[
 "Requirements that matter: convergence, instant local typing, under 200 ms remote propagation, and no lost acknowledged edits.",
 "Whole-document last-writer-wins and paragraph locks both fail. Use operation-based sync with OT or CRDTs.",
 "OT (Google Docs) transforms concurrent ops against each other, and stays tractable with a central server assigning versions.",
 "CRDTs (Yjs, Automerge) give characters unique IDs and merge in any order: offline and P2P friendly, at the cost of metadata and tombstones. Figma uses server-authoritative last-writer-wins per property.",
 "Route every editor of a doc to one owner server via a lease registry or consistent hashing. PRIMARY KEY(doc_id, version) fences zombie owners.",
 "Persist before ack, with group commits per doc. client_op_id dedupes resends after crashes or reconnects.",
 "Control storage with periodic snapshots to S3, compaction of old ops into checkpoints, and tombstone GC. Presence is ephemeral and throttled.",
 "Detect divergence with client checksums at a version, and watch op round-trip latency, reconnect rate and snapshot lag."
],
[
 ("OT or CRDT: which would you pick and why?",
  r'''It depends on the topology and offline needs. With a central server owning each document, which is how most products work, OT is a solid choice: the server totally orders ops, the transform logic stays bounded, and metadata is small. That's how Google Docs works. If offline-first editing or peer-to-peer sync matters, I'd choose a CRDT library such as Yjs, because replicas merge in any order without a coordinator, at the cost of per-character IDs and tombstones. In an interview I'd say both, pick one, and keep the server design the same.'''),
 ("How do all editors of one document end up seeing the same order of changes?",
  r'''Each open document has a single owner server. A routing registry (a lease in etcd or Redis, or consistent hashing on the doc ID) sends every WebSocket for that doc to the same server. The owner assigns monotonically increasing versions, transforms or merges each incoming op against what was committed since the client's base version, persists it, and broadcasts it in version order. Clients transform remote ops against their own pending ops. Because one authority orders everything and the transforms preserve intent, all replicas converge to the same document.'''),
 ("The collaboration server owning a document crashes. What happens to in-flight edits?",
  r'''Edits that were acked are safe, because they were persisted to the op log before the ack. The lease for that document expires, a new server becomes owner and loads the latest snapshot plus subsequent ops. Clients notice the dropped socket, reconnect (routed to the new owner), and resend their unacked ops with the original client op IDs. If an op had been persisted just before the crash, its ID is already in the log, so the server returns the existing version instead of applying it twice. Users see a brief "reconnecting" state and no data loss.'''),
 ("Every keystroke becomes an op. How do you stop storage from exploding?",
  r'''Three things. Clients batch keystrokes into ops every 50-100 ms, which cuts volume a lot. A snapshotter writes the full document to S3 every few hundred ops or when the doc goes idle, so loading needs only a snapshot plus a short tail. Then retention: fine-grained ops are kept for about 30 days for detailed history and undo, after which they're compacted into hourly or daily checkpoints, which is the granularity users browse. With CRDTs I'd also garbage-collect tombstones once all replicas have acknowledged them.'''),
 ("How would you detect that users' copies of a document have diverged?",
  r'''Divergence is the worst silent failure, because everyone thinks they're looking at the same text. Clients periodically send a hash of their document state with the version it corresponds to. The server computes the hash for that version and compares. A mismatch increments a divergence metric and forces that client to reload from the authoritative state, possibly keeping their unsynced text for manual recovery. Any non-zero divergence rate pages the team, since it points to a transform or merge bug. Fuzz tests with random concurrent ops catch these before release.'''),
 ("Users in India and the US edit the same document, and a region goes down. What happens?",
  r'''A document is homed in one region where its owner server runs, typically the creator's or most active editors' region. Remote editors still type instantly thanks to optimistic local application. Only their round trip is slower, around 200-250 ms between India and the US, which is acceptable for collaboration. The op log replicates asynchronously to a second region. If the home region fails, ownership moves there after failover, losing at most the replication lag. Clients resend unacked ops, deduped by client op ID, so most of that gap is filled.''')
],
[("Google Drive Blog - What's different about the new Google Docs: Conflict resolution", "https://drive.googleblog.com/2010/09/whats-different-about-new-google-docs_22.html"),
 ("Figma Blog - How Figma's multiplayer technology works", "https://www.figma.com/blog/how-figmas-multiplayer-technology-works/"),
 ("crdt.tech - Conflict-free Replicated Data Types resources (Kleppmann et al.)", "https://crdt.tech/"),
 ("Yjs documentation", "https://docs.yjs.dev/"),
 ("Hello Interview - Design Google Docs", "https://www.hellointerview.com/learn/system-design/problem-breakdowns/google-docs")]))

if __name__ == "__main__":
    report(topics)
