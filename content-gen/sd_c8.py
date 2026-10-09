from sd_common import *

topics = []

topics.append(T("file-storage-dropbox", "Design File Storage and Sync (Dropbox / Google Drive)", "Advanced",
"Storing and syncing files across devices efficiently using chunking, content-addressed deduplication, metadata versioning, and change notifications.",
r'''
## 1. Requirements

### Functional
- Upload and download files (up to 10-50 GB) from web, desktop and mobile.
- Automatic sync: a change on one device appears on the user's other devices.
- Folder hierarchy, rename/move/delete, file version history (restore previous versions for 30 days).
- Share files/folders with other users (view/edit permissions) and via links.
- Offline edits sync when reconnected; conflicts handled.

### Non-functional
- **Durability**: never lose a file (11 nines via object storage).
- Efficient bandwidth: sync only what changed; resumable uploads.
- Consistency: metadata must be strongly consistent (a file shouldn't appear twice or lose versions); sync latency of a few seconds is fine.
- Scale: 500M registered users, 100M DAU, files from a few KB to tens of GB.

## 2. Capacity estimates

- 500M total users, 100M DAU; each DAU modifies/uploads 10 files/day → 1B file writes/day ≈ **12k/s** (peak ~30k/s).
- Average file 1 MB, but only changed chunks upload. Assume 200 KB new data per write → 200 TB/day new data before dedup; maybe 100 TB after dedup.
- Total storage: 500M users × 5 GB average = **2.5 EB** logical; dedup and compression reduce physical significantly.
- Metadata: ~100 billion files × 1 KB = 100 TB of metadata, sharded.
- Sync notifications: 100M connected devices holding long-poll/WebSocket connections.

## 3. API design

```text
POST /v1/files/upload-session      {path, size, chunkHashes:[sha256...]}
   -> {sessionId, missingChunks:[idx...], uploadUrls:{idx: presignedUrl}}   // dedup: only missing chunks
PUT  <presigned chunk URL>         (chunk bytes, ~4 MB)
POST /v1/files/commit              {sessionId, baseRevision}               // creates new file version
   -> 200 {fileId, revision} | 409 CONFLICT {latestRevision}
GET  /v1/files/{fileId}            -> metadata + chunk list (hash + download URL)
GET  /v1/changes?cursor=..         -> list of changes since cursor (delta sync)
GET  /v1/changes/longpoll?cursor=..  (or WebSocket) -> returns when something changed
POST /v1/files/{id}/move | /delete | /restore {revision}
POST /v1/shares  {fileId|folderId, granteeEmail, role}
```

## 4. Data model

Metadata (strongly consistent; MySQL sharded by namespace/user, like Dropbox's Edgestore on MySQL):

```sql
CREATE TABLE namespaces (id BIGINT PRIMARY KEY, owner_id BIGINT, type ENUM('USER_ROOT','SHARED_FOLDER'));

CREATE TABLE file_entries (
  ns_id BIGINT, file_id BIGINT, parent_id BIGINT, name VARCHAR(255),
  is_folder BOOLEAN, latest_revision BIGINT, size BIGINT, deleted BOOLEAN,
  updated_at DATETIME,
  PRIMARY KEY (ns_id, file_id),
  UNIQUE KEY uk_path (ns_id, parent_id, name)
);

CREATE TABLE file_versions (
  ns_id BIGINT, file_id BIGINT, revision BIGINT, size BIGINT,
  chunk_hashes JSON,            -- ordered list of SHA-256 chunk hashes ("blocklist")
  device_id BIGINT, created_at DATETIME,
  PRIMARY KEY (ns_id, file_id, revision)
);

CREATE TABLE ns_journal (        -- append-only change log per namespace, drives sync
  ns_id BIGINT, seq BIGINT, file_id BIGINT, op ENUM('ADD','MODIFY','DELETE','MOVE'), revision BIGINT,
  PRIMARY KEY (ns_id, seq)
);

CREATE TABLE chunks (hash CHAR(64) PRIMARY KEY, size INT, storage_key VARCHAR(256), ref_count BIGINT);

CREATE TABLE acl (ns_id BIGINT, user_id BIGINT, role ENUM('OWNER','EDITOR','VIEWER'), PRIMARY KEY (ns_id, user_id));
```

Chunk data lives in object storage (S3 or an in-house block store like Dropbox's Magic Pocket), keyed by content hash.

## 5. High-level design

```text
 [Desktop client: watcher + chunker + local DB]       [Mobile/Web]
        |  1. metadata/commit           2. chunks           |
        v                                  |                 v
 [API Gateway / LB] ------------------------+----------------
        |                                   |
 [Metadata Service] --- MySQL shards        +--> [Block/Chunk Service] --> [Object store: chunks by hash]
        |   (files, versions, journal, ACL)                                     (S3 / Magic Pocket)
        | commit -> append ns_journal -> publish event
        v
 [Kafka: namespace-changes] --> [Notification Service] --long-poll/WebSocket--> other devices
                            --> [Search indexer], [Thumbnail/preview workers], [Audit]
```

## 6. Deep dives

### Chunking
Split files into blocks (Dropbox historically used 4 MB). Benefits:
- **Resumable** uploads: retry only failed chunks.
- **Parallel** upload/download.
- **Delta sync**: editing one paragraph of a 100 MB file changes one or two chunks; only those upload.
- **Deduplication**: identical chunks (same SHA-256) are stored once across all users and versions.

Fixed-size chunks shift all boundaries when bytes are inserted at the start. **Content-defined chunking** (rolling hash such as Rabin fingerprinting picks boundaries based on content) keeps most chunks unchanged after insertions; better dedup at the cost of variable sizes.

### Upload flow with dedup
1. Client computes chunk hashes locally.
2. Sends the list to the server; server checks which hashes it already has (`chunks` table / Bloom filter) and returns only missing ones.
3. Client uploads missing chunks directly to storage via pre-signed URLs; storage verifies the hash.
4. Client commits the new version: metadata service in **one transaction** inserts `file_versions` (revision N+1 with chunk list), updates `file_entries.latest_revision`, appends `ns_journal`, increments chunk ref counts. The commit is the atomic moment the new version exists.

Security note on cross-user dedup: attackers could probe whether a file exists by its hash; mitigate by requiring proof of possession or deduping only within a user/organisation.

### Sync and notifications
- Each device keeps a **cursor** (last journal seq per namespace).
- Notification service holds a long-poll or WebSocket per device. When a namespace changes, it signals subscribed devices "something changed".
- Device calls `GET /changes?cursor=` to fetch the delta (list of changed file entries with revisions), downloads needed chunks (skipping ones it already has locally), updates its local DB and cursor.
- Pull-after-notify keeps notifications tiny and makes clients self-healing (if a notification is missed, the next poll catches up).

### Conflict handling
Optimistic concurrency: commit includes `baseRevision`. If the server's latest revision differs (another device edited first), the commit returns 409. The client keeps both: saves its version as `report (Raj's laptop's conflicted copy).docx`. Automatic merging is only feasible for specific formats (Google Docs uses operational transforms/CRDTs for real-time collaboration, a different design).

### Versioning and deletes
Every commit creates a new revision referencing chunks; old revisions retained for 30 days (or plan limit). Deletion is a soft delete (tombstone) in metadata. A background garbage collector decrements ref counts when versions expire and deletes chunks whose ref count reaches zero (carefully, with a grace period, because a concurrent upload may be about to reference the chunk again).

### Sharing
Shared folders are separate namespaces mounted into users' trees; ACL checks on every metadata access. Changes in a shared namespace notify all members' devices. Public links map a random token → (ns_id, file_id, permissions, expiry).

### Metadata scaling
Shard by namespace ID so a user's tree and its journal live together (path operations, listing and journal appends are single-shard). Hot shared namespaces (company-wide folders) may need dedicated shards. Cache folder listings in Redis/memcache.

### Durability and storage efficiency
Object store replicates/erasure-codes chunks across zones (11 nines). Compress chunks (zstd); cold data tiering for files not accessed for months. Dropbox moved from S3 to its own Magic Pocket to reduce cost at exabyte scale.

### Client design (worth mentioning)
Desktop client: filesystem watcher (inotify/FSEvents), local SQLite DB of known state, chunker/hasher, upload/download queues with bandwidth throttling, retry with backoff, LAN sync (fetch chunks from peers on same network).

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| 4 MB chunks | Good dedup/parallelism; small files have per-chunk overhead (pack small files) |
| Content-defined chunking | Better dedup on edits; more CPU, variable chunk sizes |
| Global dedup | Big storage savings; privacy/side-channel concerns |
| Strongly consistent metadata (MySQL) | Correct versions/paths; must shard carefully |
| Notify-then-pull sync | Simple, robust; extra round trip per change |
| Conflicted copies | Never lose data; users resolve manually |

## 8. Follow-up questions

- How do you handle a 50 GB upload over flaky mobile network? (Chunks + session resume + background upload.)
- How would you show thumbnails/previews? (Async workers generating previews on commit, cached via CDN.)
- How do you support "selective sync"? (Client subscribes to subset of tree; server-side unaffected.)
- How to implement file search? (Index names and extracted text into Elasticsearch per user, ACL-filtered.)
- How does restore of a deleted folder with 100k files work? (Batch metadata operations, journal entries, async job.)
''',
["Split files into ~4 MB chunks identified by SHA-256 for resumable, parallel, delta uploads",
 "Content-defined chunking (rolling hash) keeps chunk boundaries stable after insertions",
 "Dedup: server returns only missing chunks; chunks stored once in object storage",
 "Commit new version atomically in metadata DB with chunk list + journal entry",
 "Sync: notify (long-poll/WebSocket) then pull deltas using a per-device cursor",
 "Conflicts via baseRevision check; create conflicted copies instead of losing data",
 "Metadata sharded by namespace; GC chunks by ref count after version retention",
 "Shared folders are separate namespaces with ACLs"],
[("Why split files into chunks?",
 "Chunking enables resumable uploads (retry only failed chunks), parallel transfers, and delta sync, since editing part of a large file changes only a few chunks so only those are uploaded. Chunks addressed by content hash also enable deduplication across versions and users, saving huge storage. Downloads also benefit, as devices fetch only chunks they don't already have locally."),
 ("How does a change on my laptop reach my phone?",
 "The laptop uploads missing chunks and commits a new file version; the metadata service atomically records the version and appends an entry to the namespace's change journal, then publishes an event. The notification service, which holds a long-poll or WebSocket connection for the phone, signals that the namespace changed. The phone calls the changes API with its cursor, receives the delta, downloads needed chunks and updates its local state and cursor."),
 ("How do you handle two devices editing the same file offline?",
 "Each commit includes the base revision the edit started from. The first device to sync succeeds and creates the next revision. The second device's commit fails with a conflict because its base revision is stale. Rather than overwrite, the client saves its version as a separate 'conflicted copy' file and syncs that, so no data is lost and the user resolves it. Real-time merging requires a different collaborative-editing design."),
 ("How does deduplication work and what are the risks?",
 "The client hashes each chunk with SHA-256 and sends the hash list first; the server checks which hashes already exist and requests only missing chunks. Stored chunks are referenced by many file versions via ref counts. The risk with cross-user dedup is a side channel: an attacker can learn whether someone else has a specific file by observing that no upload was needed. Mitigations include deduping only within a user or organisation, or requiring proof of possession."),
 ("Why is metadata stored in a relational database?",
 "Metadata needs strong consistency and transactions: committing a new version must atomically update the file entry, add the version, append to the change journal and update chunk references, and path uniqueness must be enforced. MySQL provides ACID and unique constraints. Sharding by namespace keeps each user's tree and journal on one shard, so most operations remain single-shard transactions.")],
[("Dropbox Tech Blog - Streaming file synchronization", "https://dropbox.tech/infrastructure/streaming-file-synchronization"), ("Dropbox - Inside the Magic Pocket", "https://dropbox.tech/infrastructure/inside-the-magic-pocket"), ("Dropbox - Rewriting the heart of our sync engine", "https://dropbox.tech/infrastructure/rewriting-the-heart-of-our-sync-engine"), ("ByteByteGo - Design Google Drive", "https://bytebytego.com/courses/system-design-interview/design-google-drive")]))

topics.append(T("food-delivery-swiggy", "Design a Food Delivery Platform (Swiggy / Zomato)", "Advanced",
"A three-sided marketplace connecting customers, restaurants and delivery partners: restaurant discovery, ordering, delivery assignment, live tracking and ETAs.",
r'''
## 1. Requirements

### Functional
- Customers discover restaurants near their location (filters: cuisine, rating, veg, delivery time), view menus, add to cart, pay, and place orders.
- Restaurants receive orders, accept/reject, mark food ready; manage menu availability.
- Delivery partners (DPs) go online, receive assignment offers, pick up and deliver; share live location.
- Customers track order status and the DP's live location with ETA.
- Ratings, cancellations and refunds.

### Non-functional
- Restaurant listing/search fast (p99 < 300 ms) and highly available; can be slightly stale.
- Order placement and payment correct (no duplicate orders/charges); order state strongly consistent.
- Assignment within seconds; ETAs reasonably accurate.
- Scale: 3M orders/day in India, peak dinner hour ~3x; 300k active delivery partners at peak; 250k restaurants.

## 2. Capacity estimates

- Orders: 3M/day; dinner peak (8-9 PM) holds ~20% of orders → 600k/hour ≈ **170 orders/s** peak.
- Browsing: ~20 sessions per order and many API calls per session → ~**50-100k read QPS** at peak; listing and menus must be cached.
- DP location: 300k DPs updating every 5 s → **60k updates/s**.
- Customer tracking: active orders at peak (~200k) polling or streaming location every few seconds.
- Storage: orders ~3 KB × 3M = 9 GB/day; location history ~60k × 100 B × 86,400 ≈ 500 GB/day (cold storage).

## 3. API design

```text
GET  /v1/restaurants?lat=..&lng=..&cuisine=..&sort=eta&cursor=..   (serviceable only)
GET  /v1/restaurants/{id}/menu
POST /v1/cart/items ; GET /v1/cart
POST /v1/orders   Idempotency-Key: ..  {cartId, addressId, paymentMethod, tip}
     -> {orderId, status:"PAYMENT_PENDING"|"PLACED", etaMinutes}
GET  /v1/orders/{id} ; SSE /v1/orders/{id}/events   (status + DP location)

Restaurant app:  WS/SSE order stream; POST /v1/restaurant/orders/{id}/accept {prepTimeMin} | /reject | /ready
DP app:          POST /v1/dp/me/status ; location stream every 5s ;
                 offers via push/WS; POST /v1/dp/assignments/{id}/accept | /picked-up | /delivered
```

## 4. Data model

```sql
-- Restaurants & menus (MySQL, cached; indexed into Elasticsearch with geo_point)
CREATE TABLE restaurants (id BIGINT PRIMARY KEY, name VARCHAR(200), lat DECIMAL(9,6), lng DECIMAL(9,6),
  city_id INT, cuisines JSON, rating DECIMAL(2,1), is_open BOOLEAN, avg_prep_min INT, geohash6 CHAR(6));
CREATE TABLE menu_items (id BIGINT PRIMARY KEY, restaurant_id BIGINT, name VARCHAR(200), price_paise INT,
  is_veg BOOLEAN, in_stock BOOLEAN, category VARCHAR(100), INDEX (restaurant_id));

-- Orders (MySQL, sharded by order_id or customer_id; state machine)
CREATE TABLE orders (id BIGINT PRIMARY KEY, customer_id BIGINT, restaurant_id BIGINT, dp_id BIGINT NULL,
  status ENUM('PAYMENT_PENDING','PLACED','ACCEPTED','PREPARING','READY','PICKED_UP','DELIVERED','CANCELLED'),
  items JSON, total_paise INT, delivery_fee_paise INT, idempotency_key VARCHAR(64),
  promised_eta DATETIME, version INT, created_at DATETIME,
  UNIQUE (customer_id, idempotency_key), INDEX (restaurant_id, created_at), INDEX (customer_id, created_at));

CREATE TABLE order_events (order_id BIGINT, seq INT, status VARCHAR(20), at DATETIME, actor VARCHAR(20),
  PRIMARY KEY (order_id, seq));
```

DP real-time state in Redis: `GEOADD dps:{city} lng lat dp:55`, `HSET dp:55 status AVAILABLE|ASSIGNED load 1`.

## 5. High-level design

```text
 [Customer app]      [Restaurant app]        [Delivery partner app]
       |                   ^  WS/push               |  location WS, offers
 [API Gateway / BFFs] -----+-------------------------+
       |
  +----+-------------+------------------+-----------------+-----------------+
 [Discovery/Search] [Cart & Pricing]  [Order Service]   [Delivery/Dispatch] [Location svc]
  ES (geo + filters) Redis, promos     state machine     assignment engine   Kafka -> Redis GEO
  + Redis cache                        MySQL + outbox    (batching, ETA)     + history store
       |                                   |                  |
 [Serviceability/ETA svc] <--------- [ETA/ML models: prep time, travel time]
                                           |
                     Kafka: order-events -> [Notifications] [Restaurant gateway] [Analytics] [Payments]
```

## 6. Deep dives

### Restaurant discovery
- Precompute serviceability: a restaurant serves a polygon/radius; for a customer's location (geohash/H3 cell), cache the list of serviceable restaurants with distance and estimated delivery time.
- Elasticsearch with `geo_point`, filters (cuisine, veg, rating, open now), sorting by relevance/ETA/rating; personalised ranking layered on top.
- Cache listing results per cell + filter set for 1-2 minutes; menus cached per restaurant (invalidated on menu updates, item stock toggles).
- Graceful degradation: if ranking service is slow, return a cached default ranking.

### Order placement
1. Validate cart server-side (prices, item stock, restaurant open, serviceability) and compute fees/discounts.
2. Create order with idempotency key; for online payment → PAYMENT_PENDING and payment flow (UPI/cards); on success webhook → PLACED (conditional transition).
3. Outbox event `OrderPlaced` → restaurant gateway pushes to the restaurant tablet (WebSocket + fallback push/IVR call if not acknowledged within 60-90 s).
4. Restaurant accepts with prep time → ACCEPTED/PREPARING; rejection triggers cancellation and refund (saga compensation).

### Delivery assignment (the core problem)
Goal: assign a DP so they arrive at the restaurant just as food is ready, minimising customer wait and DP idle time.

- **When** to assign: not immediately; time it based on predicted prep time and DP travel time to restaurant (assign when `prep_remaining ≈ dp_travel_time + buffer`).
- **Candidates**: nearby available DPs from Redis GEO within a radius, plus DPs about to finish a nearby delivery.
- **Scoring**: travel ETA to restaurant (road network), DP's current load, fairness (earnings distribution), acceptance probability, vehicle type.
- **Batching**: run the assignment engine every 10-30 seconds per zone, solving a matching problem (Hungarian algorithm or heuristics) across all pending orders and DPs — globally better than greedy first-come assignment. Also **order batching**: one DP picks two orders from the same restaurant/area going in similar directions.
- **Offer/accept**: send offer to the chosen DP with timeout; atomic claim on the DP (`SET dp:55:lock orderId NX PX` or conditional DB update) prevents double assignment; on decline/timeout, reassign.

### ETA prediction
Total ETA = restaurant prep time (ML on restaurant, items, time of day, current load) + DP to restaurant + restaurant to customer (road routing with live traffic) + handover buffers (parking, apartment gates). Shown at listing (coarse), at checkout (refined) and live during delivery (recomputed on events/location). Accurate ETAs drive customer trust and assignment timing.

### Live tracking
DP app streams location every 5 s → location gateway → Kafka → Redis GEO (latest) + order tracking channel. The customer app subscribes via SSE/WebSocket to `order:{id}` channel for status changes and DP location (or polls every 5-10 s, simpler and fine at this scale). Location history stored for disputes and ETA model training.

### Order state machine and consistency
States with allowed transitions enforced with optimistic locking (`version`); every transition written to `order_events` (audit) and emitted via outbox. Cancellation rules depend on state (free before restaurant accepts; partial charge after preparing). Refunds via payment service, idempotent.

### Peak handling (dinner rush, rain, IPL nights)
- Autoscale stateless services ahead of known peaks; cache warming.
- **Surge/dynamic fee and serviceability throttling**: when DP supply is low in a zone (rain), increase delivery fees, reduce serviceable radius, or temporarily mark distant restaurants unavailable — protects delivery promises.
- Queue-based load levelling for non-critical work (notifications, analytics).

### Restaurant reliability
Restaurant tablets can go offline; heartbeat monitoring, auto-pause restaurants that miss heartbeats or ignore orders, escalation calls.

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Cached listings per location cell | Fast browsing; up to 1-2 min staleness (closed restaurant may show briefly; re-validated at checkout) |
| Batched assignment every 10-30 s | Better global efficiency; adds seconds of delay |
| Delayed assignment based on prep ETA | Less DP idle time at restaurant; risk if prep prediction is wrong |
| Redis GEO for DP locations | Fast proximity queries; ephemeral (rebuilt from updates) |
| Saga for order + payment + restaurant | Decoupled services; intermediate states, compensations needed |

## 8. Follow-up questions

- How do you handle a restaurant that doesn't respond? (Timeout → call/auto-reject → refund, penalise ranking.)
- How do you assign when no DP accepts? (Expand radius, increase incentive, escalate to ops.)
- How do you design the promo/coupon system? (Rules engine, usage limits with atomic counters, budget caps.)
- How would you support scheduled orders? (Store with scheduled time; trigger restaurant notification and assignment ahead.)
- How do you compute "delivery in 25 mins" for 250k restaurants quickly? (Precomputed per cell-restaurant pair, refreshed every few minutes with current load.)
''',
["Three-sided marketplace: customers, restaurants, delivery partners each with their own app/channel",
 "Discovery: geo-indexed Elasticsearch + serviceability per location cell, cached 1-2 min",
 "Order: server-side cart validation, idempotency key, payment saga, outbox events",
 "Assignment timed by predicted prep time; batched matching per zone; atomic DP claim",
 "ETA = prep time + DP to restaurant + restaurant to customer + buffers (ML + routing)",
 "Live tracking: DP location -> Kafka -> Redis GEO + per-order channel via SSE/polling",
 "Peak handling: dynamic fees, shrink serviceability radius, pre-scale"],
[("How would you assign delivery partners to orders?",
 "Rather than assigning greedily on order placement, the dispatch engine runs every few seconds per zone. For orders whose predicted remaining prep time is close to a DP's travel time to the restaurant, it gathers candidate DPs from Redis GEO, including those finishing nearby deliveries, scores pairs by ETA, load, fairness and acceptance likelihood, and solves an assignment problem across all pending orders. Offers go out with a timeout and an atomic claim prevents double assignment."),
 ("How do you compute delivery ETA?",
 "ETA is the sum of components: predicted restaurant preparation time from an ML model using restaurant history, items, time of day and current load; travel time for the DP to reach the restaurant; travel time from restaurant to customer using a road graph with live traffic; and buffers for pickup and handover. It's estimated coarsely at listing, refined at checkout and continuously updated during delivery as events and locations arrive."),
 ("How do you show restaurants that can deliver to a customer quickly?",
 "Map the customer's location to a geo cell (geohash or H3). For each cell, precompute and cache the list of serviceable restaurants with distance and estimated delivery time, refreshed every few minutes. Filtering, sorting and search queries use Elasticsearch with geo_point and filters, and results are cached per cell and filter combination. At checkout, serviceability and opening status are re-validated."),
 ("How do you handle the dinner peak or heavy rain when delivery partners are scarce?",
 "Pre-scale services before predictable peaks and warm caches. When the supply-demand ratio in a zone degrades, apply dynamic delivery fees and DP incentives, reduce the serviceable radius, and show longer ETAs or temporarily hide distant restaurants, so the platform doesn't accept orders it can't fulfil on time. Non-critical processing is pushed to queues."),
 ("How does live order tracking work?",
 "The delivery partner app sends location every few seconds to a location gateway that publishes to Kafka. Consumers update the DP's latest location in Redis and publish to the active order's tracking channel. The customer app either subscribes via SSE or WebSocket to receive status changes and location, or simply polls every few seconds. ETA is recomputed as locations and status events arrive.")],
[("Swiggy Bytes - Engineering blog", "https://bytes.swiggy.com/"), ("Zomato Engineering blog", "https://blog.zomato.com/category/technology"), ("DoorDash Engineering - Dispatch optimization", "https://careersatdoordash.com/blog/next-generation-optimization-for-dasher-dispatch-at-doordash/"), ("Uber H3", "https://h3geo.org/")]))

topics.append(T("web-crawler", "Design a Web Crawler", "Intermediate",
"Crawling billions of web pages politely and efficiently: URL frontier with priorities and per-host queues, DNS caching, deduplication, robots.txt and distributed workers.",
r'''
## 1. Requirements

### Functional
- Start from seed URLs, download pages, extract links, and recursively crawl.
- Store page content for downstream use (search indexing, ML datasets, price monitoring).
- Re-crawl pages periodically based on how often they change.
- Respect `robots.txt` and crawl-delay rules.

### Non-functional
- **Scalable**: billions of pages; crawl 1B pages/month.
- **Polite**: never overload any single website.
- **Robust**: handle malformed HTML, timeouts, crawler traps, huge pages, server errors.
- **Extensible**: plug in new content types (PDFs, images) and processors.
- Freshness priority: important/changing pages re-crawled more often.

## 2. Capacity estimates

- 1B pages/month → 1B / 2.6M s ≈ **400 pages/s**, peak ~1,000/s.
- Average page 500 KB (HTML ~100 KB compressed less) → 400 × 500 KB = **200 MB/s** download bandwidth (~1.6 Gbps).
- Storage: 1B × 500 KB = 500 TB/month raw; compressed (~5x) ~100 TB/month → object storage / HDFS. 5 years ≈ 6 PB.
- URL frontier: tens of billions of discovered URLs; seen-URL set: 10B URLs × 8-byte hash = 80 GB (fits a distributed set or Bloom filter).
- DNS: thousands of lookups/s without caching → must cache.

## 3. API design

Internal system, not a public API. Control-plane endpoints:

```text
POST /v1/crawl-jobs   {seeds:[...], scope:{domains:[...]}, maxDepth, recrawlPolicy}
GET  /v1/crawl-jobs/{id}/stats
POST /v1/urls/priority  {url, priority}        // e.g., boost news homepages
```

Output: pages written to storage + `PageFetched` events (url, fetch time, content hash, storage key) on Kafka for indexers.

## 4. Data model

```sql
-- URL metadata (Cassandra/HBase/Bigtable: huge, key-value by URL hash)
CREATE TABLE urls (
  url_hash blob PRIMARY KEY,        -- 64/128-bit hash of normalised URL
  url text, host text,
  last_fetched timestamp, next_fetch timestamp,
  status int, content_hash blob, change_rate double, priority int, depth int
);

CREATE TABLE hosts (
  host text PRIMARY KEY, robots_txt text, robots_fetched_at timestamp,
  crawl_delay_ms int, ip inet, last_access timestamp, error_rate double
);
```

Content store: `s3://crawl/{yyyy-mm-dd}/{url_hash}.warc.gz` (WARC format bundles many pages per file).

## 5. High-level design

```text
 [Seed URLs] --> [URL Frontier] --(next URL per host, respecting politeness)--> [Fetcher workers x N]
                   ^   priority queues (front)                                  |  DNS resolver + cache
                   |   per-host queues (back)                                   |  robots.txt cache
                   |                                                            v
                   |                                                   [Content store (S3/HDFS)]
                   |                                                            |
                   |                                                   [Parser/Extractor workers]
                   |                                                    - content dedup (simhash)
                   |                                                    - extract links
                   |                                                            |
                   +----- [URL filter + normaliser + seen-URL check (Bloom/DB)] <+
                                                                                |
                                                        [Kafka: page-events] -> [Indexer], [Analytics]
```

## 6. Deep dives

### URL frontier: priority + politeness
The frontier decides **what** to crawl next and **when**. A classic design (Mercator):

- **Front queues (priority)**: a prioritiser assigns each URL to one of F queues by priority (PageRank-like importance, domain quality, freshness need, depth). Selection is biased toward high-priority queues.
- **Back queues (politeness)**: B queues, each containing URLs of a **single host**. A mapping table host → back queue. A min-heap keyed by "earliest time this host may be contacted again" chooses the next host; after fetching, set its next allowed time = now + crawl delay (e.g., 1-10 s or the robots.txt `Crawl-delay`, adaptive to server response time).
- Each fetcher thread takes from one back queue at a time, so a host is only fetched by one worker concurrently.

Distributed version: partition the frontier by **host hash** across crawler nodes (consistent hashing). Each node owns certain hosts, which keeps politeness local (no cross-node coordination) and DNS/robots caches effective. Discovered URLs for hosts owned by other nodes are forwarded (batched via Kafka).

Frontier storage: mostly on disk (billions of URLs) with in-memory buffers at queue heads (Kafka topics, RocksDB, or a custom disk-backed queue).

### Robots.txt
Fetch `/robots.txt` per host before crawling, cache it (e.g., 24 h), obey `Disallow`, `Allow`, `Crawl-delay`, and identify with a clear User-Agent and contact URL. Also honour `noindex`/`nofollow` meta tags if the use case is indexing.

### DNS
DNS lookups can take 10-200 ms and become a bottleneck. Use a local caching resolver per node, cache host → IP with TTL, and resolve asynchronously ahead of fetch time.

### Fetching
- Async I/O (Netty/Java HttpClient async, thousands of concurrent connections per node).
- Timeouts (connect 5 s, read 30 s), max page size (e.g., 10 MB), follow limited redirects (5), handle compression.
- Conditional requests on re-crawl (`If-Modified-Since`, `ETag`) to save bandwidth (304 Not Modified).
- Retries with backoff for 5xx/timeouts; back off a host with high error rates; respect 429.

### Deduplication
- **URL dedup**: normalise (lowercase host, remove default ports, fragments, sort query params, strip tracking params like `utm_*`), hash, check seen-set before enqueuing. Bloom filter in memory for fast "definitely not seen" checks, with an authoritative store for confirmation; a false positive just means skipping a URL (acceptable).
- **Content dedup**: ~30% of the web is duplicate or near-duplicate (mirrors, print versions). Exact duplicates via content hash (SHA-256); near-duplicates via **SimHash/MinHash** fingerprints compared by Hamming distance. Skip storing/indexing duplicates, record canonical URL.

### Crawler traps and bad content
Infinite calendars (`/calendar?date=...` forever), session IDs in URLs, endlessly deep paths, auto-generated link farms. Defences: max URL length, max depth per site, max pages per host per crawl cycle, detect repeating path segments, URL pattern blacklists, prioritising by quality signals.

### Re-crawl scheduling (freshness)
Track how often a page changes (compare content hashes across fetches). Schedule `next_fetch` adaptively: news homepages every few minutes, rarely changing pages monthly. Sitemaps (`sitemap.xml` with `lastmod`) and RSS feeds help discover new and updated URLs efficiently.

### Storage
Raw pages in WARC files on S3/HDFS (append-only, compressed, batch-friendly). Metadata in Cassandra/HBase keyed by URL hash. Parsed outputs (text, links, structured data) go to downstream pipelines via Kafka.

### Fault tolerance
Workers are stateless consumers of their frontier partition; if a node dies, its host partitions are reassigned (consistent hashing) and the durable frontier is replayed. Checkpointing ensures in-flight URLs are retried. Idempotent writes keyed by URL hash + fetch time.

### JavaScript-heavy sites
Many modern sites render content with JavaScript. Use a headless browser pool (Chromium) for selected domains only, since rendering is 10-100x more expensive than plain HTTP fetching.

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Partition frontier by host | Politeness and caching stay local; uneven host sizes cause skew |
| Bloom filter for seen URLs | Tiny memory, fast; false positives skip a few URLs |
| BFS with priorities vs pure BFS/DFS | Better coverage of important pages; more complex frontier |
| Adaptive re-crawl | Fresher important content; needs change-rate tracking |
| Headless rendering | Captures JS content; very expensive, use selectively |

## 8. Follow-up questions

- How do you crawl only one domain (e.g., for price monitoring of competitor sites)? (Scope filter, stricter politeness, legal/ToS considerations.)
- How do you prioritise which pages to crawl first? (Importance scores, inbound links, domain authority, freshness needs.)
- How would you detect that a site is blocking you? (Spikes in 403/429/captcha pages; back off.)
- How do you avoid storing the same page twice in different URLs? (Canonical tags, content hashing, SimHash.)
- How would you scale to 10x? (More fetcher nodes and frontier partitions; bandwidth and storage costs dominate.)
''',
["~400 pages/s for 1B pages/month; bandwidth and storage dominate",
 "URL frontier: front queues for priority, back queues per host for politeness",
 "Partition frontier by host hash so politeness and DNS/robots caches stay local",
 "Respect robots.txt and crawl-delay; identify with a clear User-Agent",
 "Cache DNS; use async fetching with timeouts, size limits, conditional GETs",
 "URL dedup with normalisation + Bloom filter; content dedup with SHA-256 and SimHash",
 "Defend against traps: max depth, URL length, pages per host, pattern filters",
 "Adaptive re-crawl based on observed change rate; sitemaps help discovery"],
[("How do you make the crawler polite?",
 "Obey robots.txt rules and crawl-delay, and identify with a clear User-Agent. Architecturally, the frontier keeps a separate queue per host and a schedule of when each host may next be contacted, so only one fetch per host happens at a time with a delay between requests, adapted to the server's response times and error rates. Partitioning hosts across nodes keeps this enforcement local without global coordination."),
 ("How does the URL frontier work?",
 "It has two layers. Front queues hold URLs by priority, assigned from importance, freshness needs and depth, and the selector favours higher-priority queues. URLs then move into back queues, each holding URLs from a single host. A heap keyed by each host's next allowed fetch time decides which host's queue a fetcher takes from next. The frontier is mostly disk-backed with in-memory buffers, and partitioned across nodes by host hash."),
 ("How do you avoid crawling the same URL or content repeatedly?",
 "Normalise URLs (lowercase host, strip fragments and tracking parameters, sort query params) and check a hash against a seen-set, using a Bloom filter in memory for quick negative answers backed by a persistent store. For content, compute an exact hash to detect identical pages and SimHash fingerprints to detect near-duplicates via Hamming distance, storing only the canonical version."),
 ("What are crawler traps and how do you avoid them?",
 "Traps are URL spaces that generate infinite unique URLs, such as calendars with endless next links, session IDs in URLs or recursively deep paths, which can consume a crawler's resources. Defences include limits on URL length, crawl depth and pages per host per cycle, detecting repeating path patterns, stripping session parameters during normalisation, and lowering priority for low-quality hosts."),
 ("How do you decide when to re-crawl a page?",
 "Track each page's change history by comparing content hashes across fetches and estimate its change rate. Schedule the next fetch adaptively: frequently changing, important pages like news homepages every few minutes, static pages weeks apart. Use conditional requests with ETag or If-Modified-Since to avoid downloading unchanged pages, and use sitemaps' lastmod and RSS feeds to discover updates quickly.")],
[("Mercator: A Scalable, Extensible Web Crawler (Heydon & Najork)", "https://courses.cs.washington.edu/courses/cse454/15wi/papers/mercator.pdf"), ("ByteByteGo - Design a web crawler", "https://bytebytego.com/courses/system-design-interview/design-a-web-crawler"), ("Introduction to Information Retrieval - Web crawling", "https://nlp.stanford.edu/IR-book/html/htmledition/web-crawling-and-indexes-1.html"), ("Google Search Central - robots.txt", "https://developers.google.com/search/docs/crawling-indexing/robots/intro")]))

dump("sd_part8.json", topics)
