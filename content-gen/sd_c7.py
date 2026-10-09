from sd_common import *

topics = []

topics.append(T("video-streaming-youtube", "Design a Video Streaming Platform (YouTube / Hotstar)", "Advanced",
"Uploading, transcoding and streaming video to millions of viewers using object storage, a DAG-based processing pipeline, adaptive bitrate streaming and CDNs.",
r'''
## 1. Requirements

### Functional
- Creators upload videos (up to several GB).
- Videos are processed into multiple resolutions/formats and become watchable.
- Viewers stream videos smoothly on mobile/web/TV with quality adapting to their network.
- Video metadata: title, description, thumbnails; view counts, likes, comments.
- Search and recommendations (mention, not deep dive).
- (Hotstar twist) Live streaming of events like IPL with tens of millions of concurrent viewers.

### Non-functional
- Smooth playback: fast start (< 2 s), minimal rebuffering.
- High availability for playback; uploads can be processed asynchronously (minutes).
- Durable storage: uploaded videos never lost.
- Cost efficiency: storage and CDN bandwidth dominate costs.
- Scale: 500M DAU, 5 videos watched per user per day; 500k uploads/day.

## 2. Capacity estimates

- Views: 500M × 5 = 2.5B/day ≈ **30k video starts/s**.
- Bandwidth: if average stream is 2 Mbps and average concurrent viewers are ~50M at peak → **100 Tbps**. Only a CDN can serve this; origin must see a tiny fraction.
- Uploads: 500k/day × 300 MB average original = **150 TB/day** raw. After transcoding into ~6 renditions (240p to 4K) adds roughly 1-2x the original size → ~300 TB/day total → ~100 PB/year. Object storage with tiering (cold storage for rarely watched videos).
- Metadata: 500k videos/day × 5 KB = 2.5 GB/day: small, MySQL sharded by video_id.

## 3. API design

```text
POST /v1/videos                      {title, description, tags, visibility}
     -> {videoId, uploadUrls[] (pre-signed multipart), uploadId}
PUT  <presigned S3 part URL>         (direct upload, resumable)
POST /v1/videos/{id}/upload-complete {uploadId, parts[]}
GET  /v1/videos/{id}                 -> metadata, status (PROCESSING/READY), thumbnails,
                                        manifestUrl: https://cdn.example.com/v/{id}/master.m3u8
GET  /v1/videos/{id}/comments?cursor=..
POST /v1/videos/{id}/views           (heartbeat/progress events, batched)
GET  /v1/feed/recommendations?cursor=..
```

## 4. Data model

```sql
CREATE TABLE videos (
  id BIGINT PRIMARY KEY, channel_id BIGINT, title VARCHAR(200), description TEXT,
  status ENUM('UPLOADING','PROCESSING','READY','FAILED','BLOCKED'),
  duration_sec INT, visibility ENUM('PUBLIC','UNLISTED','PRIVATE'),
  original_key VARCHAR(512), manifest_key VARCHAR(512),
  created_at DATETIME, published_at DATETIME,
  INDEX (channel_id, published_at)
);
CREATE TABLE video_renditions (video_id BIGINT, resolution VARCHAR(10), codec VARCHAR(10),
  bitrate_kbps INT, playlist_key VARCHAR(512), PRIMARY KEY (video_id, resolution, codec));
```

View counts and likes: counters in Redis/Cassandra aggregated from events; comments in Cassandra partitioned by video_id; watch history in Cassandra by user_id.

Object storage layout:

```text
s3://raw-uploads/{videoId}/original.mp4
s3://videos/{videoId}/1080p/seg_00001.m4s ... + playlist.m3u8
s3://videos/{videoId}/master.m3u8
s3://thumbnails/{videoId}/default.jpg
```

## 5. High-level design

```text
UPLOAD PATH
 [Creator] --pre-signed multipart--> [S3 raw bucket]
     |                                     | ObjectCreated event
 [Upload API] -- metadata --> [MySQL]      v
                                  [Kafka: video-uploaded]
                                           |
                              [Processing orchestrator (DAG)]
              +-------------+--------------+---------------+------------------+
        [Validate/scan] [Split into chunks] [Transcode workers x 1000s] [Thumbnails] [Content moderation / Content ID]
                                           |  (parallel per chunk & per rendition)
                                    [Package HLS/DASH + DRM] -> [S3 videos bucket]
                                           |
                                 status READY -> MySQL, notify subscribers, index in search

PLAYBACK PATH
 [Viewer] -> [API: metadata, signed manifest URL] -> [MySQL/Redis cache]
     |
     +--> [CDN edge] --miss--> [Origin shield] --miss--> [S3 videos bucket]
     |
     +--> [View events -> Kafka -> counters / analytics / recommendations]
```

## 6. Deep dives

### Upload
Large files go straight to object storage via pre-signed multipart upload (e.g., 10 MB parts, parallel, resumable on flaky mobile networks). The API server never touches the bytes. Completion triggers processing via an event.

### Transcoding pipeline
Why transcode: originals come in many codecs and sizes; devices and networks need different resolutions; streaming requires segmented formats.

- **Split** the video into GOP-aligned chunks (e.g., 4-10 s) so many workers transcode in parallel; a 1-hour video finishes in minutes instead of hours.
- **Encode** each chunk into a **bitrate ladder**: 240p (400 kbps), 360p, 480p, 720p (2.5 Mbps), 1080p (5 Mbps), 4K; codecs H.264 for compatibility, plus VP9/AV1/HEVC for efficiency on supporting devices.
- **Package** into HLS (`.m3u8` + segments) and/or MPEG-DASH (`.mpd`), apply DRM (Widevine, FairPlay) for premium content.
- Generate thumbnails, audio tracks, subtitles; run moderation and copyright matching.

Model it as a **DAG** of tasks run by an orchestrator (Temporal, Airflow-like, or custom with Kafka/SQS queues). Workers are stateless, autoscaled on queue depth, often on spot instances (cheap; tasks are retryable and idempotent because outputs are deterministic and keyed by video/chunk/rendition). Popular-first: prioritise processing for big channels.

### Adaptive bitrate streaming (ABR)
The player downloads the master manifest listing renditions, starts with a lower bitrate for fast start, measures throughput and buffer level, and switches renditions segment by segment. A viewer on Jio 4G in a train gets 480p without stalling; on Wi-Fi it climbs to 1080p. Segments are plain HTTP files, so any CDN can cache them.

### CDN strategy
- Video segments are immutable → cache with long TTLs.
- Popularity is heavily skewed: the top few percent of videos make most views; those live at edges. Long-tail videos are served from regional caches or origin.
- Multi-CDN and ISP-embedded caches (Netflix Open Connect, YouTube Google Global Cache inside ISPs) cut transit costs.
- Signed URLs/cookies protect premium content.
- Pre-warm (push) CDN for scheduled big releases.

### Live streaming (Hotstar IPL)
- Ingest: broadcaster sends RTMP/SRT to ingest servers → real-time transcoding into the ladder → package into short segments (2-6 s; Low-Latency HLS for lower delay) → origin → CDN.
- Latency is typically 10-30 s behind real time with normal HLS; LL-HLS/WebRTC for lower.
- Concurrency of 25M+ viewers means **everything** must come from CDN; manifests refresh every few seconds (cache with very short TTL and request coalescing at the edge so millions of requests become one origin fetch).
- Pre-scale everything before the match (autoscaling is too slow for a toss-time spike); load test at multiples of expected peak; graceful degradation (disable non-essential features, cap max bitrate when CDN capacity is tight).

### View counts and analytics
Players send heartbeat events (start, every 30 s progress, end) to an ingestion endpoint → Kafka → stream processing aggregates view counts (with fraud filtering: one view per user per window) into counters; raw events go to a data lake for recommendations and creator analytics. Displayed counts are eventually consistent.

### Metadata and caching
Video page metadata is read-heavy: cache in Redis; MySQL sharded by video_id with replicas. Comments in Cassandra; search via Elasticsearch.

### Cost controls
Storage tiering (move old unpopular renditions to infrequent-access or regenerate on demand), encode high resolutions only for videos that become popular, efficient codecs (AV1 can save ~30% bandwidth vs H.264).

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Chunked parallel transcoding | Fast processing; orchestration complexity, chunk boundary handling |
| Many renditions & codecs | Better quality per device; more compute and storage |
| HLS/DASH over HTTP | CDN-friendly, scalable; higher latency than WebRTC for live |
| Heavy CDN reliance | Massive scale and low latency; large bandwidth bills, multi-CDN management |
| Async processing | Upload API stays fast; video not instantly available |

## 8. Follow-up questions

- How would you resume a failed upload? (Multipart upload: re-send only missing parts; upload ID persisted on client.)
- How do you prevent duplicate/copyrighted uploads? (Perceptual hashing/fingerprinting against a reference database.)
- How to reduce start-up time? (Lower initial bitrate, prefetch first segments, edge caching of manifests, smaller first segment.)
- How does "resume watching" work? (Progress heartbeats stored per user/video in Cassandra/Redis.)
- How to handle a video going viral suddenly? (CDN absorbs; origin shield + request coalescing; metadata cache.)
''',
["Upload directly to S3 via pre-signed multipart uploads; process asynchronously",
 "Transcoding as a DAG: split into chunks, encode a bitrate ladder in parallel, package HLS/DASH",
 "Adaptive bitrate: player switches renditions per segment based on bandwidth",
 "Segments are immutable HTTP files -> long CDN caching; CDN serves nearly all bytes",
 "Live: ingest RTMP/SRT, real-time transcode, short segments, request coalescing, pre-scaling",
 "View counts from heartbeat events via Kafka, eventually consistent",
 "Storage and bandwidth dominate cost: tiering, efficient codecs, ISP caches"],
[("Walk me through what happens when a video is uploaded.",
 "The client requests an upload and receives pre-signed multipart URLs, then uploads parts in parallel directly to an S3 raw bucket. Completion emits an event to Kafka. A processing orchestrator runs a DAG: validation and virus scan, splitting into chunks, parallel transcoding of each chunk into multiple resolutions and codecs, packaging into HLS/DASH with DRM, thumbnail generation and moderation. Outputs go to a serving bucket, and metadata status flips to READY."),
 ("What is adaptive bitrate streaming?",
 "The video is encoded at several bitrates and resolutions, each split into short segments with a manifest listing them. The player downloads the manifest, starts at a modest bitrate for quick start-up, monitors measured throughput and buffer health, and picks the best rendition for each next segment. This lets playback adapt to changing networks without stalling, and since segments are ordinary HTTP files, CDNs cache them efficiently."),
 ("How do you serve video to 25 million concurrent viewers during a live match?",
 "Nearly all traffic must be served from CDN edges, often multiple CDNs plus ISP-embedded caches. The origin is protected by an origin shield and request coalescing so millions of requests for the same new segment produce one origin fetch. Manifests use very short TTLs. Infrastructure is pre-scaled before the event and load tested, and the platform can degrade gracefully, for example capping max bitrate if CDN capacity is tight."),
 ("Why split videos into chunks before transcoding?",
 "Transcoding a long video sequentially on one machine can take hours. Splitting at keyframe boundaries into short chunks lets thousands of workers transcode in parallel, so processing finishes in minutes. Failures are cheaper too: only the failed chunk is retried. Workers can be stateless and run on cheap spot instances. The orchestrator stitches or packages chunk outputs into final renditions."),
 ("How would you count views accurately at this scale?",
 "Players send playback events such as start and periodic progress heartbeats to an ingestion service that writes to Kafka. A stream processor deduplicates (one view per user per video per time window), filters bots and short plays according to view rules, and aggregates counts into a fast counter store, flushing periodically to durable storage. The displayed count is eventually consistent; raw events go to the data lake for analytics.")],
[("Netflix Tech Blog", "https://netflixtechblog.com/"), ("ByteByteGo - Design YouTube", "https://bytebytego.com/courses/system-design-interview/design-youtube"), ("Apple - HTTP Live Streaming", "https://developer.apple.com/streaming/"), ("Hotstar (JioHotstar) tech blog - Scaling for IPL", "https://blog.hotstar.com/"), ("Netflix Open Connect", "https://openconnect.netflix.com/")]))

topics.append(T("search-autocomplete", "Design Search Autocomplete (Typeahead)", "Intermediate",
"Suggesting top query completions as the user types within ~100 ms, using tries with precomputed top-k, an offline aggregation pipeline and aggressive caching.",
r'''
## 1. Requirements

### Functional
- As the user types a prefix, return the top 5-10 suggestions (e.g., "iph" → "iphone 16", "iphone 15 cover"...).
- Ranking by popularity (search frequency), optionally personalised and trending-aware.
- Support multiple languages and handle typos (nice to have).
- Filter offensive or blocked suggestions.

### Non-functional
- Very low latency: results within **~100 ms** end-to-end (feels instant), so server time ~10-20 ms.
- Highly available; slightly stale suggestions are fine (updates within minutes/hours).
- Scale: 100M DAU, ~10 searches/day, each typing ~6-8 characters.

## 2. Capacity estimates

- Searches: 1B/day. With a request per keystroke (after debouncing, say 5 per search) → 5B requests/day ≈ **60k QPS**, peak ~150k QPS.
- Distinct queries: maybe 1B distinct over time, but we keep the top ~100M by frequency for suggestions.
- Trie size: 100M queries × ~20 chars average with shared prefixes; with precomputed top-10 lists per node, tens of GB. Fits in memory across a few shards/replicas.
- Query logs: 1B × 100 B = 100 GB/day for the aggregation pipeline.

## 3. API design

```text
GET /v1/suggest?q=iph&limit=10&lang=en&loc=IN
-> 200 {"prefix":"iph","suggestions":[{"text":"iphone 16","score":98231}, ...]}
Cache-Control: public, max-age=300
```

Client behaviour: debounce (send after ~100-150 ms pause), cancel in-flight requests when a new key is typed, cache prefix results locally (backspace is free), start after 1-2 characters.

## 4. Data model

**Trie** (prefix tree): each node = one character; a path from root spells a prefix. Store at each node the **precomputed top-k completions** for that prefix so a lookup is O(length of prefix), not a subtree traversal.

```text
root
 └─ i
     └─ p  top: [iphone 16, ipl live score, iphone 15, ...]
         └─ h  top: [iphone 16, iphone 15, iphone 16 pro max, ...]
             └─ o ...
```

Serialised storage (rebuilt periodically) — key-value form is convenient:

```text
prefix -> top-10 list
"i"    -> ["instagram", "ipl", "iphone 16", ...]
"ip"   -> ["ipl", "iphone 16", "ipl live score", ...]
"iph"  -> ["iphone 16", "iphone 15", ...]
```

Prefix → list in a key-value store (Redis, or in-memory maps in the suggestion service) is simple: limit prefixes to, say, 20 characters.

Aggregated frequencies (analytics store / Cassandra / Hive table):

```sql
CREATE TABLE query_counts (
  query VARCHAR(200), window_start DATE, lang CHAR(2), region CHAR(2), count BIGINT,
  PRIMARY KEY (query, window_start, lang, region)
);
```

## 5. High-level design

```text
 ONLINE (read path)
 [Client] --debounced--> [CDN / edge cache] --miss--> [LB] --> [Suggestion service x N]
                                                                 | in-memory trie / prefix map
                                                                 | (sharded by prefix range, replicated)
                                                                 +--> [Redis prefix cache] (optional)

 OFFLINE (write path)
 [Search service] --query logs--> [Kafka] --> [Data lake (S3/HDFS)]
                                     |              |
                     [Stream job: trending (Flink)] [Batch job (Spark), hourly/daily]
                                     |              | aggregate counts with time decay,
                                     |              | filter blocked words, build top-k per prefix
                                     v              v
                            [Trending overlay]   [Trie snapshot -> S3]
                                     \              /
                              [Suggestion service loads new snapshot (blue/green swap)]
```

## 6. Deep dives

### Why precompute top-k per node
Without precomputation, answering "iph" means traversing all descendants (potentially millions) and sorting. Storing the top-k at each node trades memory for O(p) lookups. Memory reduction: store references/IDs to query strings instead of full strings, cap k at 10, and cap prefix depth.

### Building the trie (offline)
1. Collect query logs via Kafka into the data lake.
2. Batch job aggregates counts per query with **time decay** (recent searches weigh more: score = Σ count × e^(−λ·age)), normalises (lowercase, trim), removes PII-like and blocked queries, keeps queries above a minimum frequency.
3. For each query, for each prefix of it, push into that prefix's top-k (a min-heap of size k). Distributed: map each (prefix, query, score), reduce by prefix keeping top-k.
4. Write the snapshot (prefix → top-k) to S3; suggestion servers load it into memory and atomically switch. Rebuild hourly or daily.

Updating the live trie on every search is unnecessary and expensive; suggestions don't need to be real time.

### Trending queries
For breaking events ("earthquake today", a cricket score), a streaming job (Flink) counts queries over sliding windows (last 15 min), detects spikes vs baseline, and publishes a small trending overlay merged into results at query time. This keeps the main trie batch-built but still fresh for spikes.

### Sharding the trie
If it doesn't fit on one machine (or for throughput), shard by prefix: e.g., by first 1-2 characters. Skew is real (many queries start with "s", "a", "i"), so use a shard map based on measured load rather than plain alphabet ranges. Each shard is replicated for throughput and availability; the stateless routing layer looks at the prefix to pick a shard. Most deployments simply replicate the full dataset on every server when it fits in RAM (simplest, fastest).

### Caching
- Results for short prefixes ("a", "s", "i") are requested constantly → cache at CDN/edge with a few minutes TTL and in the browser.
- Responses are identical for all users (non-personalised), making caching highly effective; personalisation is layered client-side or as a small separate call.

### Personalisation and context
Blend global suggestions with the user's recent searches (stored per user in Redis, last 50 queries) and context like location ("pizza" → "pizza near me" in Bhubaneswar). Final ranking: weighted score merging candidates from global trie, user history, trending.

### Typos and fuzzy matching
Edit-distance tolerant matching via a fuzzy automaton or by indexing common misspellings; Elasticsearch's completion suggester supports fuzzy prefix queries. For an interview, mention spelling correction as a separate service.

### Alternative: Elasticsearch
Use the completion suggester (FST in memory) or edge n-gram indexed fields with popularity boosting. Faster to build, flexible; a custom trie service gives more control over latency at massive scale.

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Precomputed top-k | O(prefix) reads; more memory and offline compute |
| Batch rebuild (hourly) | Simple, consistent; slow to reflect trends → add streaming overlay |
| Full replication vs sharding | Replication simpler; sharding needed when data exceeds RAM |
| CDN caching of prefixes | Massive offload; personalised results can't be cached the same way |
| Client debouncing | Fewer requests; slight delay in showing suggestions |

## 8. Follow-up questions

- How do you remove an offensive suggestion immediately? (Blocklist checked at serve time + filter in next build.)
- How would you support multiple languages/scripts (Hindi in Devanagari, Hinglish)? (Separate tries per language, transliteration.)
- How do you measure quality? (Click-through rate on suggestions, keystrokes saved.)
- How do you handle a prefix with no results? (Fall back to spelling correction or shorter prefix.)
- How to keep latency low globally? (Deploy suggestion replicas in multiple regions, edge caching.)
''',
["Latency budget ~100 ms end-to-end; client debouncing and local caching cut requests",
 "Trie with precomputed top-k per node gives O(prefix length) lookups",
 "Offline pipeline: query logs -> Kafka -> data lake -> Spark aggregation with time decay -> snapshot",
 "Servers load snapshots into memory and swap atomically",
 "Streaming overlay for trending queries",
 "Shard by measured prefix load or simply replicate the whole trie if it fits in RAM",
 "Cache short-prefix results at CDN/browser; personalise by blending user history"],
[("Why store top-k suggestions at every trie node?",
 "Without it, answering a prefix query requires traversing every descendant of that node, potentially millions of queries, and sorting them by frequency, which is too slow for a 100 ms budget. Precomputing the top-k at each node during the offline build makes a lookup simply walking down the prefix characters and returning the stored list, O(prefix length). The cost is extra memory and build time, which is acceptable."),
 ("How do you update the suggestions as search trends change?",
 "Query logs stream into Kafka and the data lake. A periodic batch job, hourly or daily, aggregates counts with time decay, filters blocked terms, builds the top-k per prefix and writes a snapshot; servers load and swap it atomically. For fast-moving events, a streaming job computes trending queries over sliding windows and provides a small overlay merged at query time, so trends appear within minutes."),
 ("How would you reduce load on the autocomplete service?",
 "On the client: debounce keystrokes, cancel stale requests, and cache results per prefix so backspacing is free. At the edge: cache responses for popular short prefixes at the CDN with a few minutes of TTL, since non-personalised results are identical for all users. On the server: keep the trie entirely in memory and replicate it across instances."),
 ("How would you shard the trie?",
 "If it fits in memory I'd replicate the whole thing on each server, which is simplest. Otherwise shard by prefix, but not naively by first letter, because query distribution is skewed. Instead build a shard map from measured traffic and data size so each shard gets balanced load, possibly splitting hot letters by two-character prefixes. Each shard is replicated, and a routing layer maps prefixes to shards."),
 ("How do you personalise suggestions?",
 "Fetch candidates from multiple sources: the global trie, the user's recent searches kept in Redis, location-based popular queries and trending queries. Merge them with a scoring function that weights personal history and context, removing duplicates. To keep caching effective, the global part can be served from cache and the personal part fetched separately and blended on the client or a thin layer.")],
[("ByteByteGo - Design a search autocomplete system", "https://bytebytego.com/courses/system-design-interview/design-a-search-autocomplete-system"), ("Elasticsearch - Completion suggester", "https://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters.html"), ("LinkedIn Engineering - Typeahead (Cleo)", "https://engineering.linkedin.com/open-source/cleo-open-source-technology-behind-linkedins-typeahead-search"), PRIMER]))

topics.append(T("distributed-cache", "Design a Distributed Cache (like Redis / Memcached)", "Advanced",
"Building a horizontally scalable in-memory key-value cache: partitioning with consistent hashing, replication, eviction, memory management and client-side routing.",
r'''
## 1. Requirements

### Functional
- `get(key)`, `set(key, value, ttl)`, `delete(key)`.
- TTL-based expiry and eviction when memory is full (LRU).
- Keys up to 250 bytes, values up to 1 MB.

### Non-functional
- Very low latency: sub-millisecond p99 within a datacenter.
- High throughput: millions of ops/s across the cluster.
- Horizontally scalable: add nodes to increase capacity with minimal disruption.
- Highly available; tolerate node failures. As a cache, occasional data loss is acceptable, but heavy loss would stampede the DB.
- Eventual consistency between replicas is acceptable.

## 2. Capacity estimates

- Target: 2M ops/s, 90% reads. One node with an efficient event loop does ~100-200k ops/s → **~20 primary nodes** (plus replicas), leaving headroom.
- Data: 1 billion keys × ~1 KB average = **1 TB**. With nodes of 64 GB RAM using ~50 GB for data, ~20 nodes for data → consistent with throughput sizing. With 1 replica each → 40 nodes.
- Network: 2M ops × 1 KB = 2 GB/s cluster-wide; ~100 MB/s per node, fine on 10 Gbps NICs.

## 3. API design

Text or binary protocol over TCP (like RESP or the memcached protocol), via a client library:

```text
GET key                     -> value | nil
SET key value EX 3600 [NX]  -> OK
DEL key                     -> 1|0
MGET k1 k2 k3               -> batched read
INCR key                    -> atomic counter
```

```java
CacheClient cache = CacheClient.builder().seeds("cache-1:7000","cache-2:7000").build();
cache.set("product:42", bytes, Duration.ofHours(1));
byte[] v = cache.get("product:42");
```

## 4. Data model (inside a node)

- A **hash table** from key → entry (value bytes, expiry timestamp, LRU pointers, flags). O(1) get/set.
- A **doubly linked list** for LRU order: on access, move the entry to the head; evict from the tail. (Redis uses approximated LRU by sampling keys to save memory; Memcached keeps per-slab-class LRU lists.)
- **Expiry**: lazy (check on access and delete if expired) + active (background task samples keys with TTL periodically and deletes expired ones).
- **Memory allocation**: Memcached uses a **slab allocator** (pre-allocated chunks of size classes: 96 B, 120 B, ...) to avoid fragmentation; Redis uses jemalloc.

```text
Node memory
 +---------------------------+
 | Hash table (buckets)      |---> entry {key, value*, expireAt, prev, next}
 +---------------------------+
 | LRU list head <-> ... <-> tail (evict here)
 +---------------------------+
```

## 5. High-level design

```text
  [App servers with cache client library]
     | client computes node via consistent hashing on key
     | (topology map fetched from config service, cached locally)
     v
 +-----------+   +-----------+   +-----------+        [Config/Coordination service]
 | Shard A   |   | Shard B   |   | Shard C   |  <---  (ZooKeeper/etcd: membership,
 | primary   |   | primary   |   | primary   |         shard map, failover decisions)
 |  |async   |   |  |        |   |  |        |
 | replica   |   | replica   |   | replica   |
 +-----------+   +-----------+   +-----------+
```

Two routing options:
1. **Smart client** (Memcached clients, Redis Cluster clients, Lettuce): the client holds the shard map and connects directly to the right node. Lowest latency.
2. **Proxy** (Twemproxy, Envoy, mcrouter at Facebook): clients talk to a proxy that routes. Simpler clients, connection pooling, extra hop (~0.1-0.2 ms).

## 6. Deep dives

### Partitioning
- **Consistent hashing with virtual nodes**: adding a node moves only ~1/N keys; vnodes balance load and spread a failed node's keys.
- Or **hash slots** (Redis Cluster: 16,384 slots, `CRC16(key) % 16384`, slots assigned to nodes; resharding migrates slots). A node replies `MOVED` if a client asks the wrong node, and clients refresh their maps.
- **Hash tags** (`{user42}:cart`, `{user42}:profile`) force related keys into the same slot so multi-key ops work.

### Replication and failover
- Each primary has 1-2 replicas, ideally in different AZs. Replication is **asynchronous** for speed → a failover can lose the last few writes (acceptable for a cache).
- Failure detection via heartbeats/gossip among nodes (Redis Cluster) or by a coordinator (Sentinel/ZooKeeper). When a majority of observers agree a primary is down, a replica is promoted and the shard map updated; clients learn via redirects or map refresh.
- Read from replicas to scale hot reads (accepting slight staleness).

### Eviction policies
LRU (default), LFU (better for stable popularity), TTL-based (`volatile-lru`: evict only keys with TTL), random, or no eviction (return errors when full — for use as a store). Memory overhead per key (~50-100 bytes of metadata) matters at a billion keys; small values should be packed (Redis hashes with ziplist/listpack encoding).

### Concurrency model
Redis runs commands on a **single thread** per node (I/O threads optional), so each command is atomic without locks, and throughput comes from an efficient event loop (epoll) and in-memory ops. Memcached is **multi-threaded** with fine-grained locks, scaling vertically on many cores. Either way, avoid slow commands (`KEYS *`, huge values) that block.

### Hot keys
A celebrity's profile key gets 500k reads/s, overwhelming one node. Mitigations: client-side near cache (local in-process cache with short TTL, e.g., 1-5 s), replicate the hot key under multiple suffixes (`key#1..#8`) and read randomly, or read from replicas. Detect hot keys via sampling/monitoring.

### Large values and big keys
Values near 1 MB block the event loop and network; split them or compress. Avoid huge collections (a list with 10M elements); deleting them can block (use async `UNLINK`).

### Persistence (optional)
A pure cache can be volatile, but restarting cold causes a DB stampede. Options: RDB snapshots (fork + copy-on-write) and AOF logs in Redis; or warm-up by replaying from replicas; or gradual traffic ramp-up for a new node.

### Consistency with the database
The cache is not the source of truth. Patterns: cache-aside with delete-on-write, TTL as safety net, CDC-driven invalidation. Facebook's memcache paper uses **leases** to prevent stale sets and thundering herds: on a miss the client gets a lease token; only the holder may set the value, and others wait briefly.

### Multi-region
Each region runs its own cache cluster; invalidations are propagated cross-region via the DB replication stream (Facebook's mcsqueal reads MySQL commit logs to broadcast deletes).

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Async replication | Sub-ms writes; possible loss of recent writes on failover |
| Smart client vs proxy | Client: lowest latency, complex clients; proxy: simpler clients, extra hop |
| Consistent hashing vs hash slots | Ring: automatic; slots: explicit control of migration |
| LRU vs LFU | LRU adapts to recency; LFU keeps steady popular items, slower to adapt |
| Single-threaded node | Simple atomicity; one slow command blocks everything |

## 8. Follow-up questions

- How do you add a node without causing a miss storm? (Consistent hashing moves 1/N keys; warm new node gradually.)
- How do you handle a cache node that's slow but not dead? (Timeouts, circuit breaking, eject from ring after thresholds.)
- How would you implement distributed LRU across nodes? (You don't; each node manages its own memory; global LRU unnecessary.)
- How to support atomic counters and rate limiting? (Single-key atomic INCR on the owning node; Lua scripts.)
- How is this different from a distributed database? (No durability guarantees, simpler consistency, memory-bound.)
''',
["Per node: hash table + LRU list, lazy + active TTL expiry, slab allocator/jemalloc",
 "Partition with consistent hashing (vnodes) or fixed hash slots (Redis: 16,384)",
 "Smart client routes directly; proxy (mcrouter/Twemproxy) simplifies clients at an extra hop",
 "Async replication + automatic failover via gossip/Sentinel/ZooKeeper; may lose recent writes",
 "Hot keys: near cache, key replication with suffixes, replica reads",
 "Avoid big values and slow commands that block a single-threaded node",
 "Leases (Facebook memcache) prevent stale sets and thundering herds"],
[("How would you partition data across cache nodes?",
 "Use consistent hashing with virtual nodes, so each key maps to a position on a ring and adding or removing a node only moves about 1/N of the keys, with vnodes keeping load balanced. Alternatively, use a fixed number of hash slots assigned to nodes as Redis Cluster does, moving slots during resharding. The client library or a proxy keeps the topology map and routes each request directly to the owning node."),
 ("How does the cache handle node failures?",
 "Each primary shard has asynchronous replicas in other availability zones. Nodes exchange heartbeats; when a majority of observers agree a primary is unreachable, a replica is promoted and the shard map is updated in the coordination service. Clients get redirects or refresh their maps. Some recent writes may be lost, acceptable for a cache, and missing keys fall back to the database."),
 ("How would you implement LRU eviction efficiently?",
 "Combine a hash map for O(1) lookup with a doubly linked list ordered by recency: on each access move the entry to the head, on insert add at the head, and when memory exceeds the limit evict from the tail. All operations are O(1). At massive scale the pointer overhead matters, so Redis approximates LRU by sampling a few random keys and evicting the least recently used among them."),
 ("What is a hot key problem and how do you solve it?",
 "When a single key receives a disproportionate share of traffic, the node owning it becomes saturated even though the cluster has spare capacity. Solutions: a near cache in application instances with a short TTL so most reads never reach the cache cluster; replicating the key under several suffixed names and reading a random one; and serving reads from replicas. Monitoring with key sampling helps detect hot keys early."),
 ("Redis vs Memcached architecture differences?",
 "Memcached is multi-threaded, stores opaque strings, uses a slab allocator, has no persistence or built-in replication, and relies on clients for sharding; it's simple and scales vertically on many cores. Redis executes commands on a single main thread for atomicity, supports rich data structures, persistence (RDB/AOF), replication, Sentinel failover and Redis Cluster with hash slots.")],
[("Facebook - Scaling Memcache at Facebook (NSDI 2013)", "https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf"), ("Redis Cluster specification", "https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/"), ("Redis - Key eviction", "https://redis.io/docs/latest/develop/reference/eviction/"), ("Memcached wiki", "https://github.com/memcached/memcached/wiki")]))

topics.append(T("payment-system-upi", "Design a Payment System (UPI / Payment Gateway)", "Advanced",
"Moving money correctly: payment flows, idempotency, double-entry ledgers, integrating with UPI/PSPs, handling unknown states, reconciliation and settlement.",
r'''
## 1. Requirements

Context: you're designing the payment platform for an Indian app (like PhonePe/Paytm wallet + merchant payments, or Razorpay-like gateway used by an e-commerce site). It accepts payments via UPI, cards, net banking and wallet, and pays out to merchants.

### Functional
- Create a payment for an order; customer pays via UPI (collect request or intent/QR) or card.
- Get payment status; receive asynchronous updates (webhooks) when final.
- Refunds (full/partial).
- Wallet: balance, top-up, pay from wallet.
- Settlement to merchants (T+1) and reconciliation with banks/NPCI reports.
- Transaction history.

### Non-functional
- **Correctness above all**: never double-charge, never lose money, every rupee accounted for.
- Strong consistency for balances and ledger; exactly-once effect of each payment.
- High availability (payments failing = lost revenue), but prefer failing safely over inconsistency.
- Auditability, security, compliance (PCI-DSS for cards, RBI data localisation, encryption).
- Scale: 50M transactions/day, peak ~5k TPS (festival sales ~10x).

## 2. Capacity estimates

- 50M/day ≈ 600 TPS average, peak 5k-10k TPS.
- Each payment produces ~5-10 rows (payment, attempts, ledger entries, events) → ~500M rows/day → MySQL sharded (by merchant or payment ID) plus archiving; ledger data kept for years (regulatory).
- Storage ≈ 1 KB per row → 500 GB/day → ~180 TB/year before compression/archival.

## 3. API design

```text
POST /v1/payments
Idempotency-Key: 3c1e...            (required)
{"orderId":"ord_991","amount":49900,"currency":"INR","method":"UPI",
 "upi":{"flow":"INTENT"}, "customerId":"cus_42", "callbackUrl":"..."}
-> 201 {"paymentId":"pay_77","status":"CREATED","upiIntentUrl":"upi://pay?pa=merchant@bank&am=499.00&tr=pay_77..."}

GET  /v1/payments/{id}                -> status: CREATED|PENDING|SUCCESS|FAILED
POST /v1/payments/{id}/refunds        Idempotency-Key ; {"amount":10000}
POST /internal/psp/callbacks/upi      (signed callback from PSP bank / NPCI path)
Webhooks to merchant: payment.captured, payment.failed, refund.processed (signed HMAC, retried)
```

Amounts are integers in paise.

## 4. Data model

```sql
CREATE TABLE payments (
  id VARCHAR(32) PRIMARY KEY,           -- pay_xxx (Snowflake-based)
  merchant_id BIGINT, order_ref VARCHAR(64), amount BIGINT, currency CHAR(3),
  method ENUM('UPI','CARD','NETBANKING','WALLET'),
  status ENUM('CREATED','PENDING','SUCCESS','FAILED','REFUNDED','PARTIALLY_REFUNDED'),
  idempotency_key VARCHAR(64), version INT,
  created_at DATETIME, updated_at DATETIME,
  UNIQUE KEY uk_idem (merchant_id, idempotency_key)
);

CREATE TABLE payment_attempts (            -- each call to a PSP/bank
  id BIGINT PRIMARY KEY, payment_id VARCHAR(32), psp VARCHAR(32),
  psp_txn_ref VARCHAR(64), rrn VARCHAR(20),   -- UPI reference number
  status ENUM('INITIATED','PENDING','SUCCESS','FAILED','UNKNOWN'),
  request_at DATETIME, response_code VARCHAR(16),
  UNIQUE KEY (psp, psp_txn_ref)
);

-- Double-entry ledger: immutable, append-only
CREATE TABLE ledger_entries (
  id BIGINT PRIMARY KEY, txn_id VARCHAR(32), account_id BIGINT,
  direction ENUM('DEBIT','CREDIT'), amount BIGINT, currency CHAR(3),
  created_at DATETIME, INDEX (account_id, created_at), INDEX (txn_id)
);
CREATE TABLE accounts (id BIGINT PRIMARY KEY, owner_type ENUM('USER_WALLET','MERCHANT','PSP_CLEARING','FEES','ESCROW'),
  owner_id BIGINT, balance BIGINT NOT NULL, version INT NOT NULL, CHECK (balance >= 0 OR owner_type <> 'USER_WALLET'));

CREATE TABLE outbox (id BIGINT PRIMARY KEY, aggregate_id VARCHAR(32), type VARCHAR(64), payload JSON, created_at DATETIME, sent BOOLEAN);
```

## 5. High-level design

```text
 [Merchant backend / App] --> [API Gateway: auth (API keys), rate limit, idempotency]
                                   |
                           [Payment Service]  -- state machine, MySQL (payments, attempts, outbox)
                              |        |  \
                 route/choose |        |   \--> [Risk/Fraud svc] (velocity, device, limits)
                              v        |
                    [PSP Connector svc] ----> PSP bank / UPI switch (NPCI) / Card network / Wallet
                              ^                         |
                              +--- callbacks / status --+
                                       |
                    outbox -> [Kafka: payment-events] -> [Ledger svc] (double-entry, MySQL)
                                                     -> [Merchant webhook dispatcher] (retries)
                                                     -> [Notifications], [Analytics]
 [Reconciliation svc] <-- daily settlement files from banks/NPCI/PSPs; compares with ledger
 [Settlement svc]     --> payouts to merchant bank accounts (T+1), fees ledgered
```

## 6. Deep dives

### UPI flow (intent/collect)
1. Merchant creates payment → our service creates `payments` row (CREATED) and an attempt, asks our PSP bank to generate an intent URL / collect request with our transaction reference.
2. Customer approves in their UPI app (PhonePe/GPay/BHIM) with UPI PIN; the payer's PSP sends the request through **NPCI's UPI switch**, which debits the payer's bank and credits the payee's bank (our merchant's/nodal account).
3. Our PSP bank gets the final status and sends a **callback**; we also poll the status API if no callback arrives within N seconds.
4. On SUCCESS: update payment (conditional transition PENDING → SUCCESS), write ledger entries, emit events, webhook to merchant.

Key fact: we never see bank credentials or the UPI PIN; the money moves bank-to-bank via NPCI. Our job is orchestration, state, ledgering and reconciliation.

### Idempotency everywhere
- Client → us: `Idempotency-Key` with a unique constraint `(merchant_id, idempotency_key)`; store the response; replays return it. In-progress duplicates get 409/202.
- Us → PSP: send our attempt ID as the unique transaction reference; PSPs reject or dedupe repeats.
- Callbacks: may arrive multiple times or out of order → apply with conditional updates (`WHERE status IN ('CREATED','PENDING')`) and ignore illegal transitions (SUCCESS can't go back to PENDING).
- Kafka consumers (ledger, webhooks): dedupe by event ID.

### The "unknown" state (timeouts)
The scariest case: we call the PSP and the request times out. Did the money move? **Never assume failure and retry blindly** (could double charge) and never assume success. Mark the attempt `UNKNOWN`/PENDING, then:
- Poll the PSP status API with backoff using our reference.
- If still unknown, wait for the callback or the next day's reconciliation file.
- Show the customer "payment pending; if debited, it will be confirmed or auto-refunded within X hours" (exactly what UPI apps show).

### Double-entry ledger
Every money movement is recorded as balanced entries: total debits = total credits for each transaction. Example customer pays ₹499 to a merchant with ₹10 fee:

```text
txn pay_77:
  DEBIT  PSP_CLEARING account   49900
  CREDIT MERCHANT_42 payable    48900
  CREDIT FEES revenue            1000
```

Ledger entries are **immutable**; corrections are new reversing entries. Balances are derived (or maintained in `accounts` within the same DB transaction using optimistic locking on `version`). This makes auditing and reconciliation possible: if debits ≠ credits, there's a bug.

Wallet debit in one transaction:

```sql
UPDATE accounts SET balance = balance - 49900, version = version + 1
WHERE id = :wallet AND balance >= 49900 AND version = :v;   -- 1 row or reject/retry
INSERT INTO ledger_entries ... (debit wallet, credit merchant)
INSERT INTO outbox ... ('WalletDebited')
COMMIT;
```

### Reliable events: outbox
Payment status change, ledger write and event insert happen in one local transaction; a relay publishes to Kafka. No "DB updated but webhook never sent" gaps.

### Merchant webhooks
Signed with HMAC (merchant secret) so merchants can verify; retried with exponential backoff for up to 24-72 hours; merchants must handle duplicates. Merchants should also verify via `GET /payments/{id}` before fulfilling.

### Reconciliation (non-negotiable)
Daily (and intraday) jobs ingest settlement files from PSPs/banks/NPCI and match each record with our payments by reference/RRN and amount:
- Matched: mark reconciled.
- In bank but not SUCCESS with us (we missed a callback): mark success, credit merchant, or auto-refund if the order was cancelled.
- SUCCESS with us but not in bank file: investigate; possibly reverse.
- Amount mismatch: flag for ops.
Many "money lost" incidents are found and fixed here.

### Settlement
Aggregate successful captured payments per merchant minus fees/refunds, initiate payouts (NEFT/IMPS/RTGS) T+1, record ledger entries for payouts, handle payout failures with retries.

### Routing and resilience
Multiple PSPs/acquirers: route based on success rates, cost and health (circuit breakers per PSP). If a bank's UPI handle is degraded (high failure rate), show warnings in the UI. Payment service and DB are multi-AZ; MySQL with semi-sync replication (no lost committed transactions).

### Security and compliance
TLS everywhere, mTLS to PSPs, HMAC-signed callbacks verified, card data never stored (tokenisation via card networks/PCI vault), encryption at rest, RBI data localisation (data stored in India), strict audit logs, fraud checks (velocity limits, device fingerprinting, risk scoring) before initiating.

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Strong consistency (MySQL, ACID) for ledger | Correctness over raw throughput; shard by account/merchant to scale |
| Async final status (callbacks + polling) | Real-world rails are async; UX must handle PENDING |
| Never auto-retry unknown outcomes | Safer; some payments stay pending longer |
| Outbox + Kafka | Reliable events; eventual delivery to downstream systems |
| Immutable ledger | Auditability; requires reversing entries rather than edits |

Hot spots: a huge merchant during a sale → hot merchant account row; mitigate by splitting into sub-accounts or batching credits to merchant balance asynchronously from the ledger.

## 8. Follow-up questions

- How do refunds work? (New refund record with idempotency key, call PSP refund API, ledger reverse entries, handle partial refunds and refund > original checks.)
- How do you prevent a wallet going negative under concurrent payments? (Conditional UPDATE with balance check / optimistic locking.)
- How do you handle a PSP outage? (Circuit breaker, route to alternate PSP, queue non-urgent operations.)
- What's the difference between authorization and capture for cards? (Auth holds funds; capture moves them; auto-capture or delayed capture.)
- How do you test payment systems? (Sandbox PSPs, chaos testing timeouts, reconciliation tests, ledger invariants checks.)
''',
["Correctness first: idempotency at every hop, strong consistency for money",
 "Amounts in integer paise; payment as a state machine with conditional transitions",
 "UPI: money moves bank-to-bank via NPCI; we orchestrate, track state, ledger, reconcile",
 "Timeouts create UNKNOWN state: poll status, wait for callback/recon, never blindly retry",
 "Double-entry, immutable, append-only ledger; debits = credits per transaction",
 "Outbox for reliable events; HMAC-signed, retried merchant webhooks",
 "Daily reconciliation against bank/NPCI files catches missed callbacks and mismatches",
 "Security: TLS/mTLS, tokenised cards, encryption, RBI data localisation, fraud checks"],
[("How do you guarantee a customer is never charged twice?",
 "Idempotency at every layer: clients send an Idempotency-Key enforced by a unique constraint and we return the stored result for retries; we pass our unique attempt reference to the PSP so it dedupes; callbacks are applied with conditional state transitions so duplicates are no-ops; consumers dedupe events by ID. We never blindly retry a timed-out charge; we query status first. Reconciliation catches anything that slips through and triggers refunds."),
 ("What do you do when the call to the bank times out?",
 "Treat the outcome as unknown, not failed. Mark the attempt PENDING or UNKNOWN, then poll the PSP's status API with backoff using our transaction reference, and also accept the asynchronous callback. If still unresolved, the next reconciliation file decides. The user sees a pending message with a promise of confirmation or automatic refund. Retrying immediately could cause a double debit."),
 ("What is a double-entry ledger and why use it?",
 "Every money movement is recorded as at least two entries, debits and credits across accounts, that sum to zero, like debiting a clearing account and crediting the merchant and fee accounts. Entries are immutable and append-only; corrections are reversing entries. This provides a complete audit trail, makes balances derivable and verifiable, and any imbalance immediately signals a bug, which is essential for financial correctness and regulatory audits."),
 ("Explain reconciliation in a payment system.",
 "Reconciliation compares our internal records with external sources of truth such as bank, PSP and NPCI settlement files, matching on references like RRN and amounts. It finds mismatches: payments the bank shows as successful but we marked pending or failed due to missed callbacks, payments we marked successful that the bank didn't settle, and amount differences. Each case is auto-corrected or routed to operations. It runs daily and often intraday."),
 ("How does a UPI payment flow work end to end?",
 "The merchant creates a payment with us and we generate a UPI intent or collect request via our PSP bank with our transaction reference. The customer approves in their UPI app with their PIN; the payer's PSP routes the request through NPCI's UPI switch, which debits the payer's bank and credits the payee's bank. Our PSP notifies us via callback; we update the payment state, write ledger entries, emit events and notify the merchant via webhook."),
 ("How do you keep a wallet balance consistent under concurrent payments?",
 "Keep wallet balance and ledger in one ACID database and debit with a conditional update: UPDATE accounts SET balance = balance - amount WHERE id = ? AND balance >= amount (optionally with a version check), inserting ledger entries and an outbox event in the same transaction. If zero rows are affected, the payment is rejected for insufficient funds or retried on version conflict, so the balance can never go negative.")],
[("Stripe - Designing robust and predictable APIs with idempotency", "https://stripe.com/blog/idempotency"), ("NPCI - Unified Payments Interface", "https://www.npci.org.in/what-we-do/upi/product-overview"), ("Uber Engineering - Payments platform (Gulfstream)", "https://www.uber.com/blog/payments-platform/"), ("Square - Books: an immutable double-entry accounting database", "https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/"), ("ByteByteGo - Payment system", "https://bytebytego.com/courses/system-design-interview/payment-system")]))

dump("sd_part7.json", topics)
