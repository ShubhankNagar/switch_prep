from sd_common import *

topics = []

topics.append(T("notification-system", "Design a Notification System", "Intermediate",
"A multi-channel system (push, SMS, email, in-app) that delivers transactional and marketing notifications reliably, respecting user preferences and rate limits.",
r'''
## 1. Requirements

### Functional
- Send notifications via **push** (FCM for Android, APNs for iOS), **SMS**, **email**, and **in-app** inbox.
- Triggered by other services (order shipped, OTP, payment received) and by marketing campaigns (bulk sends to segments).
- Templates with variables and localisation (English, Hindi, Odia...).
- User preferences: opt-out per channel/category, quiet hours (no promos 10 PM-8 AM).
- Scheduling (send at 9 AM) and delivery tracking (sent, delivered, opened, failed).

### Non-functional
- Transactional notifications (OTP, payment) are **high priority**, low latency (< 5 s); marketing can be delayed.
- At-least-once delivery, but avoid duplicates (no user wants 3 identical OTPs).
- Scalable to bursts: a sale campaign to 50M users.
- Highly available; one failing provider must not stop delivery (failover between SMS vendors).

## 2. Capacity estimates

- Daily: 100M push, 20M SMS, 30M email, 100M in-app ≈ 250M/day ≈ **3k/s average**.
- Campaign burst: 50M pushes in 30 minutes ≈ **28k/s**.
- Storage: each notification log ~500 B → 125 GB/day; keep 90 days hot (~11 TB) in Cassandra, then archive.
- External limits: SMS vendors often allow a few hundred to a few thousand msgs/s per account; FCM handles batching (up to 500 tokens per multicast request).

## 3. API design

```text
POST /v1/notifications            (internal, from other services)
Idempotency-Key: order-991-shipped
{
  "userId": 42,
  "templateId": "ORDER_SHIPPED",
  "channels": ["PUSH","SMS"],          // optional; else use template defaults + preferences
  "priority": "HIGH",                 // HIGH | NORMAL | LOW
  "params": {"orderId":"991","eta":"Tomorrow"},
  "sendAt": null
}
-> 202 Accepted {"notificationId":"n-123"}

POST /v1/campaigns   {segmentId, templateId, sendAt, throttlePerSec}
GET  /v1/users/{id}/inbox?cursor=..        (in-app notifications)
PUT  /v1/users/{id}/preferences  {"PROMO":{"SMS":false,"PUSH":true}, "quietHours":"22:00-08:00"}
POST /v1/devices  {userId, platform, token}     (register FCM/APNs token)
```

## 4. Data model

```sql
-- MySQL
CREATE TABLE templates (id VARCHAR(64), channel ENUM('PUSH','SMS','EMAIL','INAPP'), locale VARCHAR(10),
  title VARCHAR(200), body TEXT, category ENUM('TRANSACTIONAL','PROMO'), version INT,
  PRIMARY KEY (id, channel, locale));

CREATE TABLE user_preferences (user_id BIGINT, category VARCHAR(32), channel VARCHAR(16),
  enabled BOOLEAN, PRIMARY KEY (user_id, category, channel));

CREATE TABLE devices (id BIGINT PRIMARY KEY, user_id BIGINT, platform ENUM('ANDROID','IOS','WEB'),
  token VARCHAR(512), last_seen DATETIME, active BOOLEAN, INDEX (user_id));

-- Cassandra: notification log / in-app inbox
CREATE TABLE notifications_by_user (
  user_id bigint, notification_id timeuuid, channel text, template_id text,
  status text, payload text, read boolean,
  PRIMARY KEY ((user_id), notification_id)
) WITH CLUSTERING ORDER BY (notification_id DESC) AND default_time_to_live = 7776000;
```

Dedup keys in Redis: `notif:idem:{key}` with 24 h TTL.

## 5. High-level design

```text
 [Order svc] [Payment svc] [Auth svc (OTP)] [Campaign scheduler]
        \          |            |               /
         +----> [Notification API] <-----------+
                    | validate, idempotency check (Redis), persist (status=PENDING)
                    | resolve user prefs, quiet hours, device tokens, render template
                    v
     [Kafka topics by channel & priority]
      push-high | push-low | sms-high | sms-low | email | inapp
         |          |          |                     |        |
   [Push workers] [SMS workers]               [Email workers] [In-app writer]
       |               |  rate limiter per vendor   |              |
   FCM / APNs    SMS vendor A / B (failover)    SES / SendGrid   Cassandra + WebSocket/SSE
       |               |                            |
       +---- delivery callbacks / webhooks ---------+--> [Status updater] -> Cassandra
                                                                  |
                                              [Retry topic] -> [DLQ] -> alerts
```

## 6. Deep dives

### Priority isolation
Separate topics (or queues) per priority so a 50M-user marketing blast doesn't delay OTPs. High-priority consumers have dedicated capacity. OTPs could even bypass Kafka with a direct synchronous call to the SMS vendor plus a fallback queue.

### Reliability and retries
- Persist the notification request before acknowledging (202), so nothing is lost.
- Workers are at-least-once consumers; on transient failure (timeout, 5xx, 429 from vendor) retry with exponential backoff using retry topics (1 min, 5 min, 30 min); after max attempts send to DLQ and mark FAILED.
- **Vendor failover**: if SMS vendor A has elevated errors (circuit breaker open), route to vendor B. Many Indian companies use multiple SMS gateways for reliability and cost.

### Deduplication
- Idempotency key from the caller (`order-991-shipped`) checked in Redis with SET NX; repeat requests return the existing notificationId.
- Workers record `(notificationId, channel)` as sent before/after calling the provider; on redelivery they check status first. Some duplicates remain possible if a crash happens between provider call and status update; acceptable for push/email, minimised for SMS with provider-side idempotent reference IDs.

### Preferences, quiet hours and frequency capping
- Preference service cached in Redis (read for every notification).
- Transactional notifications ignore promo opt-outs (regulations like TRAI DND allow transactional SMS) but promo respects them.
- Quiet hours: delay low-priority messages via a scheduler (delayed queue or a time-bucketed table polled every minute).
- Frequency caps: no more than 3 promo pushes/day per user (Redis counter per user per day).

### Campaigns at scale
Campaign service resolves a segment (e.g., 50M user IDs from the analytics warehouse), splits into batches of 1,000, and enqueues them gradually with a throttle (e.g., 20k/s) to protect downstream systems and app backends (users opening the app all at once cause a traffic spike). Push workers use FCM multicast batching.

### Device token management
Users have multiple devices; tokens change. Register/refresh tokens on app start. When FCM/APNs report a token invalid/unregistered, mark it inactive. Prune devices not seen for 90 days.

### In-app notifications
Write to Cassandra inbox; if the user is online, push in real time via the existing WebSocket/SSE connection; unread badge count kept in Redis (`INCR`, reset on open).

### Scheduling
`sendAt` in the future: store in a `scheduled_notifications` table partitioned by minute bucket; a scheduler polls the current bucket every few seconds and enqueues due items. Alternatives: Kafka delay topics, Redis sorted set by timestamp, or Quartz/ShedLock.

### Tracking and analytics
Providers send delivery webhooks (SMS DLRs, SES bounces/complaints); push open events come from the app. A status updater writes to Cassandra and emits events to analytics (delivery rate, open rate per template). Bounced emails and invalid numbers are suppressed in future sends.

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Async via Kafka (202 Accepted) | Resilient and scalable; callers don't get immediate delivery confirmation |
| At-least-once + dedup | Rare duplicates possible vs never losing OTPs |
| Separate topics per channel/priority | More topics to operate, but isolation |
| Multiple SMS vendors | Higher availability, cost optimisation; more integration work |
| Cassandra for logs/inbox | Massive write volume, TTL support; limited querying (use analytics store for reports) |

Bottlenecks: vendor rate limits (respect with per-vendor token buckets), preference lookups (cache), campaign spikes (throttle), and hot users (bots triggering many notifications → per-user rate limits).

## 8. Follow-up questions

- How do you guarantee ordering (e.g., "order shipped" before "order delivered")? (Key Kafka by userId/orderId; include sequence numbers.)
- How would you support rich push (images, action buttons)? (Template types per channel, payload size limits.)
- How do you A/B test templates? (Template variants with weighted assignment, track open/click rates.)
- How to digest notifications ("5 people liked your post")? (Aggregate events in a window per user before sending.)
- What if FCM is down? (Retry with backoff, fall back to SMS for critical alerts.)
''',
["Channels: push (FCM/APNs), SMS, email, in-app; templates + localisation",
 "Accept with 202 after persisting; process asynchronously via Kafka",
 "Separate queues by priority so campaigns never delay OTPs",
 "Retries with backoff via retry topics, then DLQ; vendor failover with circuit breakers",
 "Idempotency keys in Redis to avoid duplicate notifications",
 "Respect preferences, quiet hours, frequency caps; transactional vs promotional",
 "Throttle campaigns and batch FCM sends",
 "Track delivery via provider webhooks; prune invalid device tokens"],
[("How do you ensure OTPs are not delayed by a marketing campaign?",
 "Isolate by priority: separate Kafka topics or queues for high-priority transactional messages and low-priority promotional ones, each with dedicated consumers and capacity. Campaign sends are also throttled at enqueue time. For OTPs specifically, I might call the SMS provider synchronously with a short timeout and use the queue only as a fallback, and keep multiple SMS vendors for failover."),
 ("How do you avoid sending duplicate notifications?",
 "Callers send an idempotency key such as order-991-shipped; the API does SET NX in Redis with a TTL and returns the existing notification if the key was seen. Workers check the notification's channel status before sending and update it after the provider call. Since Kafka is at-least-once, a tiny window remains; for SMS, passing a unique reference ID to the provider helps it deduplicate."),
 ("How would you send a push notification to 50 million users?",
 "The campaign service resolves the segment into user IDs, splits it into batches, and enqueues them gradually with a configured rate (e.g., 20k/s) to protect both the push infrastructure and our backend from the resulting app-open spike. Workers look up device tokens, apply preferences and frequency caps, and use FCM multicast with up to 500 tokens per request. Invalid tokens from responses are deactivated."),
 ("How do you handle a failing SMS provider?",
 "Wrap each provider in a circuit breaker and track error rates and latency. When vendor A fails or returns throttling errors, route traffic to vendor B. Transient failures are retried with exponential backoff via retry topics; permanent failures go to a DLQ with alerts. Delivery reports from vendors update status, and repeated failures for a number suppress future sends."),
 ("How do you respect user preferences and quiet hours?",
 "Before sending, the pipeline looks up cached preferences per category and channel. Transactional messages bypass promotional opt-outs but promos are dropped if the user opted out. If the user is in quiet hours, low-priority messages are scheduled for the end of the window via a delayed queue. Frequency caps are enforced with per-user daily counters in Redis.")],
[("ByteByteGo - Design a notification system", "https://bytebytego.com/courses/system-design-interview/design-a-notification-system"), ("Firebase Cloud Messaging documentation", "https://firebase.google.com/docs/cloud-messaging"), ("Apple Push Notification service", "https://developer.apple.com/documentation/usernotifications"), ("Uber Engineering - Real-time push platform", "https://www.uber.com/blog/real-time-push-platform/")]))

topics.append(T("ride-hailing-uber", "Design a Ride-Hailing System (Uber / Ola)", "Advanced",
"Matching riders with nearby drivers in real time: location ingestion, geospatial indexing with geohash/H3, dispatch, trip state machines and surge pricing.",
r'''
## 1. Requirements

### Functional
- Rider requests a ride from pickup to drop; sees fare estimate and ETA.
- System matches the rider with a nearby available driver; driver accepts/declines.
- Rider sees the driver's live location; both see trip status.
- Trip lifecycle: requested → driver assigned → arrived → in progress → completed → paid; cancellations.
- Drivers go online/offline and send location updates.
- Payments and ratings after the trip.

### Non-functional
- Matching latency < a few seconds; location updates near real-time.
- High availability (a down system strands people); location data can be eventually consistent, but **a driver must not be assigned to two trips** (strong consistency on assignment).
- Scale: 20M rides/day, 2M drivers online at peak in a country-sized market.

## 2. Capacity estimates

- Driver location updates every 4 s: 2M / 4 = **500k updates/s**. This is the dominant write load.
- Rides: 20M/day ≈ 230/s average, peak ~1-2k requests/s.
- Location payload ~100 bytes → 50 MB/s ingestion. Storing all history: 500k × 86,400 × 100 B ≈ 4 TB/day → keep only recent in hot store; trip routes archived to cheap storage.
- Current locations in memory: 2M drivers × ~200 B = 400 MB. Fits easily in Redis.

Conclusion: the hard parts are high-frequency location writes and fast nearby-driver queries, not ride volume.

## 3. API design

```text
Driver app
  POST /v1/drivers/me/status      {"status":"ONLINE"|"OFFLINE"}
  WS   /v1/drivers/me/stream      -> sends {"lat":20.29,"lng":85.82,"heading":90,"ts":...} every 4 s
                                  <- receives ride offers {"tripId", "pickup", "fare", "expiresIn":15}
  POST /v1/trips/{id}/accept | /decline | /arrived | /start | /complete

Rider app
  POST /v1/fare-estimates  {pickup, drop, vehicleType} -> {fare, surgeMultiplier, etaMin, quoteId}
  POST /v1/trips           {quoteId, pickup, drop, paymentMethod}   Idempotency-Key: ...
                           -> {tripId, status:"MATCHING"}
  GET  /v1/trips/{id}      ; WS/SSE /v1/trips/{id}/events (driver location, status changes)
  POST /v1/trips/{id}/cancel
```

## 4. Data model

```sql
-- MySQL / PostgreSQL (sharded by city or trip_id)
CREATE TABLE trips (
  id BIGINT PRIMARY KEY,                -- Snowflake
  rider_id BIGINT NOT NULL, driver_id BIGINT NULL,
  city_id INT, vehicle_type VARCHAR(20),
  status ENUM('MATCHING','ASSIGNED','ARRIVED','IN_PROGRESS','COMPLETED','CANCELLED'),
  pickup_lat DECIMAL(9,6), pickup_lng DECIMAL(9,6), drop_lat DECIMAL(9,6), drop_lng DECIMAL(9,6),
  quoted_fare INT, final_fare INT, surge DECIMAL(3,2),
  version INT NOT NULL DEFAULT 0,       -- optimistic locking for state transitions
  created_at DATETIME, updated_at DATETIME,
  INDEX (rider_id, created_at), INDEX (driver_id, created_at)
);

CREATE TABLE drivers (id BIGINT PRIMARY KEY, name VARCHAR(100), vehicle_type VARCHAR(20),
  city_id INT, rating DECIMAL(2,1), current_trip_id BIGINT NULL, version INT);
```

Real-time state in Redis:

```text
GEOADD drivers:bbsr:sedan 85.82 20.29 driver:123     -- geo index (geohash-based sorted set)
HSET driver:123:state status AVAILABLE lat 20.29 lng 85.82 ts 1759900000 tripId -
```

Location history → Kafka → Cassandra/S3 (`(driver_id, day)` partition, clustered by timestamp) for trip route reconstruction, fraud checks and analytics.

## 5. High-level design

```text
 [Driver app] --WS--> [Location Gateway] --> [Kafka: driver-locations (key=driverId)]
                             |                         |              \
                             | update                  v               --> [Location history -> Cassandra/S3]
                             +-----------------> [Location Service] --> Redis GEO (by city + vehicle type)
                                                                         ^
 [Rider app] -> [API Gateway] -> [Trip Service] --request match--> [Dispatch/Matching Service]
                    |                 |  (state machine, MySQL)         | query nearby drivers (Redis GEO)
                    |                 |                                  | rank by ETA (Routing/ETA svc)
                    |                 |                                  | offer to driver (via Gateway WS)
                    |                 |<----- driver accepted ----------+  lock driver (Redis/DB CAS)
                    |                 |
                    |            [Pricing/Surge svc]    [Payment svc]   [Notification svc]
                    |
                    +--> [Trip events WS/SSE] <-- driver location stream for active trip
```

## 6. Deep dives

### Geospatial indexing: finding nearby drivers

A naive `SELECT ... WHERE lat BETWEEN .. AND lng BETWEEN ..` over 2M rows updated 500k times/s won't work. Options:

- **Geohash**: encodes lat/lng into a string where shared prefixes mean nearby (`tdnu2` area; 6 chars ≈ 1.2 km × 0.6 km cell). To find nearby drivers, query the rider's cell plus its 8 neighbours (to handle edges). Redis GEO uses a 52-bit geohash in a sorted set: `GEOSEARCH drivers:bbsr:sedan FROMLONLAT 85.82 20.29 BYRADIUS 3 km ASC COUNT 20`.
- **Quadtree**: recursively splits regions into 4 until each cell holds ≤ N drivers; adapts to density (dense Bengaluru vs sparse rural). Kept in memory; updates are costlier.
- **Uber's H3**: hexagonal hierarchical grid; hexagons have uniform neighbour distances, good for surge zones and supply/demand analytics.
- **Google S2**: sphere-based cells (used by many mapping systems).

Choice: Redis GEO keyed per city and vehicle type for simplicity and speed; each location update is `GEOADD` (O(log n)). Remove offline/busy drivers from the available set. Shard Redis by city (cities are natural partitions).

### Location ingestion at 500k/s
- Drivers keep a WebSocket (or send UDP/HTTP2) to location gateways; gateways batch and publish to Kafka keyed by driverId.
- Location service consumers update Redis (pipelined). Drop stale updates (older ts than stored).
- Only the latest location matters for matching, so this path can tolerate occasional loss; history goes to cold storage asynchronously.
- Adaptive frequency: every 4 s when available, more often during a trip, less when stationary.

### Matching (dispatch)
1. Trip service creates trip (MATCHING), calls dispatch.
2. Dispatch fetches ~20 nearest available drivers, computes **ETA via road network** (routing service, not straight-line distance), filters by vehicle type, rating, acceptance rate.
3. Offers the trip to the best driver with a 15 s timeout (or to a few drivers in sequence). Batched matching (collect requests for 2 s and solve as an assignment problem) improves global efficiency; mention as advanced.
4. **Preventing double assignment**: atomic claim on the driver: `UPDATE drivers SET current_trip_id = ?, version = version + 1 WHERE id = ? AND current_trip_id IS NULL` or a Redis `SET driver:123:lock tripId NX PX 20000`. Only one trip can claim the driver. Similarly a trip can only be accepted once (conditional status update MATCHING → ASSIGNED).
5. On decline/timeout, offer to the next driver; after N failures, expand radius or tell the rider no drivers available.

### Trip state machine
Explicit states with allowed transitions enforced in the trip service with optimistic locking (`version`). Every transition emits an event (Kafka, outbox pattern) consumed by notifications, billing, analytics. Idempotent APIs because mobile networks retry.

### Live tracking for the rider
During a trip, the driver's location updates for that trip are forwarded to the rider's connection: location service publishes to a channel `trip:{id}` (Redis pub/sub or Kafka) that the rider's WebSocket/SSE gateway subscribes to. Client-side interpolation makes movement smooth.

### Surge pricing
Per H3 hexagon/geohash zone, compute demand (requests in last 5 min) vs supply (available drivers) with a stream processor (Flink) every minute; multiplier stored in Redis per zone. The fare estimate returns a **quote ID** locking the price for a few minutes so the rider pays what they saw.

### Payments
After completion, trip service emits TripCompleted → payment service charges via stored method or UPI, idempotent per trip ID; driver earnings ledger updated; failures retried and reconciled.

### Fault tolerance
- Location gateways stateless besides sockets; drivers reconnect.
- If Redis geo shard fails: replica failover; locations repopulate within seconds from the next updates (self-healing state).
- Trip data in a durable replicated DB; multi-AZ.
- Region-level: cities served from the nearest region.

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Redis GEO per city | Fast and simple; memory-bound, need sharding by city |
| Geohash vs quadtree vs H3 | Geohash simple with edge issues (query neighbours); quadtree adapts to density; H3 uniform for analytics |
| Kafka for locations | Buffering and fan-out to many consumers; adds a little latency |
| Strong consistency only on assignment | Locations eventually consistent, but no double booking of drivers |
| Sequential offers | Fair and simple; batched optimisation gives better global matching |

## 8. Follow-up questions

- How do you calculate ETA? (Road graph with traffic-aware edge weights, contraction hierarchies, ML corrections from historical trips.)
- How do you handle a driver's phone losing connectivity mid-trip? (Buffer locations on device, upload on reconnect; trip continues.)
- How would you implement ride pooling? (Match riders with overlapping routes, constrained detour; harder optimisation.)
- How to detect GPS spoofing fraud? (Speed/jump checks, sensor data, history analysis.)
- How do you shard trips? (By city or trip ID; rider/driver history via secondary indexes.)
''',
["Location updates (~500k/s) dominate load; ingest via WebSocket gateways + Kafka",
 "Keep only latest location in Redis GEO per city/vehicle type; history to cold storage",
 "Geospatial options: geohash (query cell + 8 neighbours), quadtree, H3 hexagons, S2",
 "Rank candidate drivers by road-network ETA, not straight-line distance",
 "Prevent double assignment with atomic conditional update or Redis SET NX",
 "Trip is a state machine with optimistic locking and outbox events",
 "Surge computed per zone from demand/supply via stream processing; price locked by quote ID",
 "Live tracking via pub/sub channel per trip to the rider's connection"],
[("How do you find nearby drivers efficiently?",
 "Index current driver locations with a geospatial structure in memory. I'd use Redis GEO, which stores geohash-encoded positions in a sorted set, partitioned by city and vehicle type, and query GEOSEARCH by radius sorted by distance. Geohash cells share prefixes when close, so nearby search is a range lookup; to avoid edge misses we check neighbouring cells. Alternatives are quadtrees, which adapt to density, or Uber's H3 hexagonal grid."),
 ("How do you handle 500k location updates per second?",
 "Drivers stream updates over persistent connections to stateless location gateways, which batch and publish to Kafka keyed by driver ID. Consumers update Redis GEO with pipelining and discard out-of-order updates. Only the latest position matters for matching, so loss of an occasional update is tolerable. History is written asynchronously to Cassandra or S3. Update frequency adapts to driver state."),
 ("How do you prevent a driver from being assigned two trips?",
 "Assignment must be strongly consistent. When dispatch picks a driver, it atomically claims them: a conditional update such as UPDATE drivers SET current_trip_id = ? WHERE id = ? AND current_trip_id IS NULL, or a Redis SET with NX on a driver lock key with expiry. Only one claim succeeds; the loser moves to the next candidate. The trip's own transition from MATCHING to ASSIGNED is also conditional, so it can't be accepted twice."),
 ("How would you implement surge pricing?",
 "Divide the city into zones such as H3 hexagons. A stream processor consumes ride requests and driver availability events and computes, per zone every minute, the demand-to-supply ratio, mapping it to a multiplier with smoothing and caps. Multipliers live in Redis. The fare estimate applies the zone's multiplier and returns a quote ID that locks the price for a few minutes so the rider pays the shown amount."),
 ("How does the rider see the driver moving in real time?",
 "Once a trip is assigned, the rider's app opens a WebSocket or SSE connection subscribed to that trip. The location service, when it receives updates from the assigned driver, also publishes them to a trip channel via Redis pub/sub or Kafka, which the rider's gateway forwards. The app interpolates between points for smooth animation and shows ETA updates from the routing service.")],
[("Uber Engineering - H3 hexagonal hierarchical spatial index", "https://www.uber.com/blog/h3/"), ("Uber Engineering blog", "https://www.uber.com/blog/engineering/"), ("Redis - Geospatial indexes", "https://redis.io/docs/latest/develop/data-types/geospatial/"), ("Hello Interview - Uber", "https://www.hellointerview.com/learn/system-design/problem-breakdowns/uber"), ("ByteByteGo - Proximity service", "https://bytebytego.com/courses/system-design-interview/proximity-service")]))

topics.append(T("ecommerce-flipkart-checkout", "Design E-commerce Checkout (Flipkart / Amazon)", "Advanced",
"The cart-to-order path of an e-commerce platform: inventory reservation without overselling, order and payment saga, flash sale handling, and idempotency.",
r'''
## 1. Requirements

### Functional
- Users add items to a cart, view it, and check out.
- Checkout validates price and stock, applies coupons, calculates totals (tax, delivery).
- Payment via UPI, cards, wallets, COD; order is confirmed only on successful payment (or COD).
- Inventory must not be oversold.
- Order history and status (placed, packed, shipped, delivered, cancelled, returned).
- Flash sales (Big Billion Days): limited stock at huge concurrency.

### Non-functional
- **Correctness**: no overselling, no double charging, no lost orders.
- Checkout latency p99 < 1-2 s (excluding the user's time on the payment page).
- High availability, especially during sales; graceful degradation (recommendations can fail, checkout can't).
- Scale: 10M orders/day normally; flash sale peak 100k+ checkout attempts/s for a few minutes.

## 2. Capacity estimates

- 10M orders/day ≈ **115 orders/s** average; normal peak ~500/s.
- Flash sale: 10M users trying to buy 100k phones in the first minute → **~150k requests/s** hitting product/stock checks, mostly failing.
- Order row + items ≈ 2 KB → 20 GB/day → 7 TB/year: MySQL sharded by user_id over time.
- Cart: 50M active carts × 2 KB = 100 GB → Redis cluster (with persistence) or DynamoDB-like store.

## 3. API design

```text
POST /v1/cart/items          {skuId, qty}
GET  /v1/cart
POST /v1/checkout/preview    {cartId, addressId, couponCode}
     -> {items, priceBreakup, deliveryEta, checkoutToken (price lock, 10 min)}
POST /v1/orders              Idempotency-Key: <uuid>
     {checkoutToken, paymentMethod}
     -> 201 {orderId, status:"PAYMENT_PENDING", paymentRedirect/upiIntent}
POST /v1/payments/webhook    (from payment gateway: success/failure, signed)
GET  /v1/orders/{id}         ; GET /v1/orders?cursor=..
POST /v1/orders/{id}/cancel
```

## 4. Data model

```sql
-- Order service (MySQL, sharded by user_id)
CREATE TABLE orders (
  id BIGINT PRIMARY KEY,                 -- Snowflake, embeds shard bits
  user_id BIGINT NOT NULL,
  status ENUM('CREATED','PAYMENT_PENDING','CONFIRMED','PACKED','SHIPPED','DELIVERED','CANCELLED','FAILED'),
  total_paise BIGINT, currency CHAR(3),
  idempotency_key VARCHAR(64) NOT NULL,
  address_snapshot JSON,                 -- copy, not a reference
  created_at DATETIME, updated_at DATETIME, version INT,
  UNIQUE KEY uk_user_idem (user_id, idempotency_key),
  INDEX idx_user_time (user_id, created_at)
);
CREATE TABLE order_items (order_id BIGINT, sku_id BIGINT, seller_id BIGINT, qty INT,
  unit_price_paise BIGINT, PRIMARY KEY (order_id, sku_id));

-- Inventory service (MySQL, sharded by sku_id / warehouse)
CREATE TABLE inventory (
  sku_id BIGINT, warehouse_id INT,
  available INT NOT NULL, reserved INT NOT NULL DEFAULT 0,
  PRIMARY KEY (sku_id, warehouse_id),
  CHECK (available >= 0)
);
CREATE TABLE reservations (
  id BIGINT PRIMARY KEY, order_id BIGINT, sku_id BIGINT, warehouse_id INT, qty INT,
  status ENUM('HELD','CONFIRMED','RELEASED'), expires_at DATETIME,
  UNIQUE (order_id, sku_id)
);
```

Prices stored as integers (paise) to avoid floating point errors. Address and price are **snapshotted** into the order.

Cart: Redis hash `cart:{userId}` → `{skuId: qty}` with persistence, plus async backup to a DB for logged-in users.

## 5. High-level design

```text
 [Web/App] -> [CDN] -> [API Gateway: auth, rate limit, bot protection]
                  |
   +--------------+-------------+-------------------+------------------+
 [Cart svc]   [Catalog/Pricing svc]   [Checkout/Order svc]        [Coupon svc]
  Redis        ES + MySQL + cache      (saga orchestrator)          MySQL+Redis
                                          |        |        \
                              reserve     |        | pay     \ events (outbox -> Kafka)
                                          v        v          v
                                  [Inventory svc] [Payment svc] -> [PG: Razorpay/PayU/UPI]
                                     MySQL          MySQL ledger       |
                                                       ^----webhook----+
                                          |
                     Kafka: OrderConfirmed -> [Fulfilment/WMS] [Notification] [Analytics] [Search stock sync]
```

## 6. Deep dives

### Checkout flow as an orchestrated saga

```text
1. Create order (CREATED) with idempotency key           -- local txn in Order DB
2. Reserve inventory (HELD, expires in 10-15 min)        -- compensation: release
3. Apply coupon (mark redeemed, pending)                 -- compensation: unredeem
4. Initiate payment -> PAYMENT_PENDING, redirect user
5a. Payment success webhook -> confirm reservation, order CONFIRMED, emit OrderConfirmed
5b. Payment failure / timeout -> release reservation, unredeem coupon, order FAILED
```

The order service orchestrates and persists saga state, so it can resume after crashes. Each step is idempotent (keyed by orderId). Events are published via the transactional outbox. COD orders skip step 4.

### Preventing overselling

Inventory decrement must be atomic at the source of truth:

```sql
UPDATE inventory
SET available = available - :qty, reserved = reserved + :qty
WHERE sku_id = :sku AND warehouse_id = :wh AND available >= :qty;
-- rows affected = 1 -> reserved; 0 -> out of stock
```

No read-then-write race, no long locks. Insert the reservation row in the same transaction. A sweeper (or delayed message) releases expired HELD reservations, returning stock (`available += qty`). Displayed stock on product pages comes from cache/Elasticsearch and may be stale; the real check happens here.

### Reserve at checkout vs at payment
Reserving when the user starts payment guarantees they won't pay for an out-of-stock item, but abandoned payments hold stock (mitigated by short expiry). Reserving after payment risks refunding users. Most platforms reserve at order creation with a short hold.

### Flash sales (the classic interview twist)

Problem: 10M users, 100k units, everyone clicks at 12:00:00. MySQL row for that SKU becomes a massive hot spot.

Techniques:
1. **Front-door protection**: CDN serves static product pages; a pre-sale "registration" or token; CAPTCHA and bot detection; per-user limits (1 unit per user).
2. **Virtual waiting room / queue**: admit users at a rate the backend can handle; others see "you're in queue".
3. **Stock counter in Redis**: preload `stock:sku123 = 100000`; each attempt runs an atomic Lua script `if stock >= qty and not purchased(user) then DECRBY; SADD buyers user; return OK`. Redis handles ~100k ops/s per shard; split the stock into N sub-counters across shards (`stock:sku123:0..9`, 10k each) to parallelise.
4. Winners get an order-creation token and proceed asynchronously: requests go to a Kafka queue; order workers create orders and DB reservations at a sustainable rate. Users see "order processing".
5. Reconcile: Redis is the gate, DB is the source of truth. If a payment fails, return the unit to the Redis counter (or a waitlist).

### Idempotency and double charging
- `POST /orders` requires an Idempotency-Key; unique `(user_id, idempotency_key)` returns the existing order on retry.
- Payment initiation uses orderId as the merchant reference; the gateway rejects duplicates.
- Webhooks can arrive multiple times or out of order: process idempotently using state transitions (`UPDATE orders SET status='CONFIRMED' WHERE id=? AND status='PAYMENT_PENDING'`).
- If a webhook never arrives, a reconciliation job polls the gateway for status of orders stuck in PAYMENT_PENDING after N minutes.

### Price and coupon integrity
Never trust client-sent prices. The checkout preview computes prices server-side and issues a signed `checkoutToken` (price lock with expiry). Order creation verifies the token. Coupons with usage limits use the same atomic conditional update pattern (`used < max_uses`).

### Cart design
Redis for speed; merge guest cart into user cart on login. Cart shows current price and stock (may change since adding); revalidated at checkout.

### Degradation during sales
Feature flags turn off non-essential calls (recommendations, reviews, personalised widgets) to reserve capacity for the checkout path. Bulkheads isolate thread pools so slow coupon service doesn't block order creation (skip coupon if unavailable, with user consent).

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| Saga instead of 2PC | Available and decoupled; intermediate states visible (PAYMENT_PENDING) |
| Conditional UPDATE for stock | Simple, correct; hot rows under extreme contention → Redis gate for flash sales |
| Reservation with expiry | No paying for unavailable items; abandoned carts temporarily lock stock |
| Async order creation in flash sales | Survives spikes; users wait a few seconds for confirmation |
| Sharding orders by user_id | Fast "my orders"; seller/ops queries need a separate store |

## 8. Follow-up questions

- How do you handle multiple sellers/warehouses for one order? (Split into shipments; reserve per warehouse; partial fulfilment.)
- How do you choose the warehouse? (Nearest with stock to the pincode, delivery SLA, cost.)
- How do refunds work on cancellation? (Compensating payment refund, idempotent, ledger entries.)
- What if Redis loses flash-sale counters? (Rebuild from DB reservations; pause sale briefly; Redis with AOF + replica.)
- How would you show "only 3 left"? (Cached approximate stock; exact check at reservation.)
''',
["Checkout = orchestrated saga: create order, reserve stock, apply coupon, pay, confirm or compensate",
 "Prevent overselling with atomic conditional UPDATE (available >= qty)",
 "Reservations expire (10-15 min) and are released by a sweeper",
 "Idempotency key on order creation; idempotent webhook handling via state transitions",
 "Store money as integers (paise); snapshot price and address in the order",
 "Flash sales: waiting room, Redis atomic stock gate (sharded counters), async order creation",
 "Reconciliation job for orders stuck in PAYMENT_PENDING",
 "Degrade non-critical features to protect the checkout path"],
[("How do you prevent overselling?",
 "Make the stock check and decrement a single atomic operation at the inventory source of truth: UPDATE inventory SET available = available - qty, reserved = reserved + qty WHERE sku_id = ? AND available >= qty, and check that one row was affected. There's no read-then-write race and no long-held lock. The reservation expires if payment doesn't complete and stock is returned. Product page stock can be cached and stale; correctness is enforced here."),
 ("How would you handle a flash sale of 100k phones with 10M users?",
 "Protect the backend in layers: static pages on CDN, bot detection and per-user limits, and a virtual waiting room admitting users at a sustainable rate. Use Redis as the stock gate: an atomic Lua script decrements a preloaded counter (split across shards) and records the buyer, rejecting most requests in memory. Winners are queued via Kafka for asynchronous order creation and DB reservation. Failed payments return units to the pool."),
 ("Why use a saga for checkout instead of a distributed transaction?",
 "Order, inventory, payment and coupon services own separate databases, and payment involves an external gateway that can't participate in 2PC. 2PC would also hold locks during a slow user-facing payment step and couple availability of all services. A saga runs local transactions with compensations, such as releasing stock and refunding, which keeps services decoupled and available, at the cost of visible intermediate states."),
 ("How do you avoid charging a user twice?",
 "Use idempotency at every layer: the client sends an Idempotency-Key when creating the order, enforced by a unique constraint, so retries return the same order. Payment is initiated with the order ID as the merchant reference so the gateway rejects duplicates. Webhooks are processed idempotently with conditional status transitions. A reconciliation job compares our records with gateway settlement reports and refunds any duplicates."),
 ("What happens if the payment webhook never arrives?",
 "The order stays in PAYMENT_PENDING with a timestamp. A scheduled reconciliation job finds orders pending longer than a threshold and queries the payment gateway's status API. If paid, it confirms the order; if failed or expired, it marks the order failed and releases the reservation. The reservation itself has an expiry slightly longer than the payment window as a safety net.")],
[("Shopify Engineering - Surviving flashes of high-write traffic", "https://shopify.engineering/surviving-flashes-of-high-write-traffic-using-scriptable-load-balancers-part-i"), ("microservices.io - Saga pattern", "https://microservices.io/patterns/data/saga.html"), ("Flipkart Tech Blog", "https://blog.flipkart.tech/"), ("Stripe - Designing robust and predictable APIs with idempotency", "https://stripe.com/blog/idempotency")]))

topics.append(T("ticket-booking-bookmyshow", "Design a Ticket Booking System (BookMyShow)", "Advanced",
"Selling seats for movies and events without double booking: seat maps, temporary seat holds with expiry, payment integration, and handling high-demand on-sales.",
r'''
## 1. Requirements

### Functional
- Browse cities, movies/events, theatres, and show times.
- View the seat map for a show with real-time availability.
- Select seats and hold them for a limited time (e.g., 10 minutes) while paying.
- Pay and receive a booking confirmation (e-ticket/QR code).
- Cancel bookings per policy; refunds.

### Non-functional
- **No double booking** (strong consistency for seat allocation).
- Browsing must be fast and highly available (can be slightly stale).
- Handle spikes: a big release or concert on-sale (Coldplay India tour) with millions of users in minutes.
- Scale: 50M monthly users, 2M bookings/day normally.

## 2. Capacity estimates

- Bookings: 2M/day ≈ 23/s average; peak (Friday evening) ~500/s.
- Browsing: ~100x bookings → ~50k reads/s at peak → cache heavily.
- Shows: 10k theatres × 5 screens × 5 shows/day = 250k shows/day × ~200 seats = 50M seat-show rows/day. A `show_seats` table grows ~50M rows/day; partition by show date and archive old shows.
- Mega on-sale: 5M users for 50k concert tickets → 100x oversubscribed; requires a queue.

## 3. API design

```text
GET  /v1/cities/{cityId}/movies?date=2026-10-10
GET  /v1/movies/{movieId}/shows?cityId=..&date=..
GET  /v1/shows/{showId}/seats       -> seat map with status AVAILABLE | HELD | BOOKED
POST /v1/shows/{showId}/holds       {seatIds:["A1","A2"]}   Idempotency-Key: ..
     -> 201 {holdId, expiresAt, amount}   | 409 SEATS_UNAVAILABLE {seatIds}
DELETE /v1/holds/{holdId}           (user leaves)
POST /v1/bookings                   {holdId, paymentMethod}  -> {bookingId, paymentUrl}
POST /v1/payments/webhook
GET  /v1/bookings/{id}              -> status, QR code
POST /v1/bookings/{id}/cancel
```

## 4. Data model

```sql
-- Catalog (read-heavy, cached): movies, theatres, screens, shows
CREATE TABLE shows (id BIGINT PRIMARY KEY, movie_id BIGINT, screen_id BIGINT,
  start_time DATETIME, city_id INT, status VARCHAR(20), INDEX (movie_id, city_id, start_time));

CREATE TABLE screen_seats (screen_id BIGINT, seat_id VARCHAR(8), row_label CHAR(2),
  category ENUM('RECLINER','PRIME','CLASSIC'), x INT, y INT, PRIMARY KEY (screen_id, seat_id));

-- Inventory per show: source of truth for seat status (MySQL, sharded/partitioned by show_id)
CREATE TABLE show_seats (
  show_id BIGINT, seat_id VARCHAR(8),
  status ENUM('AVAILABLE','HELD','BOOKED') NOT NULL DEFAULT 'AVAILABLE',
  hold_id BIGINT NULL, held_until DATETIME NULL, booking_id BIGINT NULL,
  price_paise INT, version INT NOT NULL DEFAULT 0,
  PRIMARY KEY (show_id, seat_id)
);

CREATE TABLE holds (id BIGINT PRIMARY KEY, show_id BIGINT, user_id BIGINT,
  status ENUM('ACTIVE','CONVERTED','EXPIRED','RELEASED'), expires_at DATETIME,
  idempotency_key VARCHAR(64), UNIQUE (user_id, idempotency_key));

CREATE TABLE bookings (id BIGINT PRIMARY KEY, hold_id BIGINT UNIQUE, user_id BIGINT, show_id BIGINT,
  amount_paise INT, status ENUM('PENDING_PAYMENT','CONFIRMED','CANCELLED','FAILED'),
  payment_ref VARCHAR(64), created_at DATETIME, INDEX (user_id, created_at));
```

`UNIQUE (hold_id)` on bookings ensures one hold becomes at most one booking.

## 5. High-level design

```text
 [App/Web] -> [CDN: posters, static]
     |
 [API Gateway: auth, rate limit] ---- [Virtual waiting room (for hot shows)]
     |
     +--> [Catalog svc] -> Redis cache -> MySQL/ES (movies, theatres, shows, search)
     |
     +--> [Seat Inventory svc] ----> MySQL show_seats (source of truth)
     |          |   \--> Redis seat-map cache (bitmap per show) + pub/sub for live updates
     |          |
     +--> [Booking svc] --> [Payment svc] --> [Payment gateway (UPI/cards)]
                |                ^                     |
                |                +------ webhook ------+
                +--> Kafka (outbox): BookingConfirmed -> [Ticket/QR generator] [Notification] [Analytics]

 [Hold expiry worker] -- releases expired holds (sweeper or delayed queue)
```

## 6. Deep dives

### Seat holds without double booking (core problem)

Two users click seat A1 at the same moment. Exactly one must win.

**Approach 1: Conditional update in MySQL (recommended).** In one transaction:

```sql
UPDATE show_seats
SET status = 'HELD', hold_id = :holdId, held_until = NOW() + INTERVAL 10 MINUTE, version = version + 1
WHERE show_id = :showId AND seat_id IN ('A1','A2')
  AND (status = 'AVAILABLE' OR (status = 'HELD' AND held_until < NOW()));
-- if rows affected != 2 -> ROLLBACK, return 409 with unavailable seats
```

All-or-nothing for the selected seats; only one transaction can flip a seat. Rows are small and contention is per show, so this scales well for normal traffic. Lock order (sort seat IDs) avoids deadlocks.

**Approach 2: Pessimistic locking** with `SELECT ... FOR UPDATE` on the seats, check, then update. Correct but holds locks longer.

**Approach 3: Redis hold** with `SET hold:{show}:{seat} holdId NX EX 600` for each seat (Lua script for multiple seats atomically). Very fast and auto-expiring; but Redis isn't the source of truth, so confirm into MySQL at booking time with the conditional update too. Useful as a front gate for hot shows.

### Hold expiry
- The conditional update already treats expired holds as available (lazy expiry), so correctness doesn't depend on a background job.
- A sweeper runs every minute: `UPDATE show_seats SET status='AVAILABLE', hold_id=NULL WHERE status='HELD' AND held_until < NOW()` (batched, indexed on held_until), and marks holds EXPIRED, publishing seat-map updates.
- Alternatively schedule a delayed message per hold (Kafka delay topic/RabbitMQ TTL + DLX).

### Payment and confirmation
1. `POST /bookings` with holdId: verify hold ACTIVE and not expired, create booking PENDING_PAYMENT, initiate payment with bookingId as reference.
2. Webhook success: in one transaction, `UPDATE show_seats SET status='BOOKED', booking_id=? WHERE hold_id=? AND status='HELD'` and booking CONFIRMED; emit event via outbox → QR ticket + SMS/email.
3. **Edge case**: payment succeeds after the hold expired and someone else took the seat. Detect (rows affected mismatch) → auto-refund and notify, or extend holds slightly beyond the payment gateway's timeout to make this rare. Payment window (e.g., 8 min) < hold (10 min).
4. Reconciliation job for bookings stuck in PENDING_PAYMENT.

### Seat map reads at scale
Seat maps are read far more than written. Cache per show in Redis (e.g., a bitmap or hash of seat statuses), updated on every hold/release/booking event; TTL short. Clients poll every few seconds or subscribe via SSE/WebSocket to seat changes for the show they're viewing. A stale map just means the hold attempt may return 409, which the UI handles gracefully ("seat just got taken, pick another").

### Hot on-sales (concerts, first-day-first-show)
- **Virtual waiting room**: users get a queue position (Redis sorted set or a token service); they're admitted at a controlled rate (e.g., 2,000 users/minute) with a signed admission token checked by the gateway. Protects all downstream services and gives fairness.
- Per-user limits (max 4-6 tickets), CAPTCHA, bot detection.
- Pre-warm caches, scale out inventory service and DB read replicas, isolate the event's inventory on its own shard.
- For general admission (no seat selection), use a counter in Redis with atomic decrement, then async booking creation.

### Sharding and partitioning
`show_seats` is accessed by show_id → shard by show_id (or by city). Each booking touches a single show, so seat transactions stay single-shard. Old shows are archived (partition by date, drop partitions).

### Search and browsing
Catalog in MySQL with Elasticsearch for search (movie names, filters by language/genre/format) and Redis caching for city → movies → shows listings; heavily cacheable, invalidated when schedules change.

## 7. Bottlenecks and trade-offs

| Decision | Trade-off |
|---|---|
| DB conditional update for holds | Strongly consistent and simple; DB is the bottleneck for mega events |
| Redis hold gate | Handles spikes; must reconcile with DB, extra complexity |
| 10-minute hold | Gives time to pay; abandoned holds block seats temporarily |
| Cached seat maps | Fast browsing; users may see stale availability (handled with 409) |
| Waiting room | Fairness and protection; adds wait time for users |

## 8. Follow-up questions

- How to support "best available" seat suggestions? (Algorithm over seat map picking contiguous seats closest to the centre.)
- How to handle partial failure when holding 4 seats and 1 is taken? (All-or-nothing transaction; return which seats are unavailable.)
- How to handle cancellations and resale? (Booking CANCELLED, seats AVAILABLE, refund via payment service, publish seat-map update.)
- How do theatres with their own systems integrate? (Partner APIs; inventory sync with locking at the theatre's system as source of truth.)
- How do you price dynamically? (Price per seat category per show; demand-based pricing for events.)
''',
["Seat allocation must be strongly consistent; browsing can be cached and stale",
 "Hold seats with an atomic conditional UPDATE (AVAILABLE or expired HELD -> HELD), all-or-nothing",
 "Lazy expiry in the update condition + sweeper job releases expired holds",
 "Payment window shorter than hold; refund if payment lands after hold expiry",
 "Unique hold_id on bookings and idempotent webhooks prevent double booking",
 "Seat maps cached in Redis; live updates via SSE/WebSocket or polling",
 "Virtual waiting room + per-user limits for hot on-sales",
 "Shard show_seats by show_id; archive old shows"],
[("How do you prevent two users from booking the same seat?",
 "The seat inventory table is the source of truth, and holding seats is a single conditional update: set status to HELD where show and seat match and status is AVAILABLE or an expired hold, inside a transaction covering all selected seats. If the number of affected rows doesn't match the number requested, roll back and return 409. Only one transaction can flip each seat, so double booking is impossible regardless of concurrency."),
 ("How do seat holds expire?",
 "Each held seat has a held_until timestamp. The hold query treats expired holds as available, so correctness never depends on a cleanup job. A background sweeper periodically resets expired holds to AVAILABLE in batches, marks the hold record expired and publishes seat-map updates. Alternatively a delayed message per hold triggers release. The payment window is kept shorter than the hold duration."),
 ("What if payment succeeds after the hold expired?",
 "On the success webhook, confirming the booking uses a conditional update that requires the seats to still be HELD by that hold ID. If another user already took them, the update affects fewer rows, so we mark the booking failed, trigger an automatic refund via the payment service and notify the user. To make this rare, the gateway payment timeout is set shorter than the hold, and holds can be extended once payment has started."),
 ("How would you handle millions of users for a concert on-sale?",
 "Put a virtual waiting room in front: users get queue positions and are admitted at a rate the inventory service can handle, with signed admission tokens checked at the gateway. Enforce per-user ticket limits and bot protection. Cache the event page on CDN, isolate the event's inventory on dedicated capacity, and optionally use Redis as a fast atomic gate for holds, reconciled into MySQL as the source of truth."),
 ("Why not use Redis as the main store for seat status?",
 "Redis is fast and supports atomic operations and expiry, which suits holds, but bookings involve money and must be durable and auditable. Redis replication is asynchronous, so a failover could lose recent holds or bookings, leading to double booking. I'd keep MySQL as the source of truth and use Redis only for caching seat maps or as a front-line gate during extreme spikes.")],
[("Hello Interview - Ticketmaster", "https://www.hellointerview.com/learn/system-design/problem-breakdowns/ticketmaster"), ("ByteByteGo - Hotel reservation system", "https://bytebytego.com/courses/system-design-interview/hotel-reservation-system"), ("Vlad Mihalcea - Optimistic vs pessimistic locking", "https://vladmihalcea.com/optimistic-vs-pessimistic-locking/"), ("Cloudflare - Waiting Room", "https://developers.cloudflare.com/waiting-room/")]))

dump("sd_part6.json", topics)
