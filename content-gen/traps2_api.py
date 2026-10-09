from traps2_common import T

A = "api-design"

IDOR_BUGGY = """@GetMapping("/api/orders/{orderId}")
public OrderDto getOrder(@PathVariable Long orderId) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(NotFoundException::new);
    return mapper.toDto(order);
}"""

IDOR_FIX = """@GetMapping("/api/orders/{orderId}")
public OrderDto getOrder(@PathVariable Long orderId, @AuthenticationPrincipal AppUser me) {
    Order order = orderRepository.findByIdAndCustomerId(orderId, me.getId())  // ownership in the query
            .orElseThrow(NotFoundException::new);   // 404, not 403: don't confirm the order exists
    return mapper.toDto(order);
}"""

TRAPS = [
    T("trap-api-design-idempotency-keys", A, "Making POST retries safe with idempotency keys", "Intermediate", "Very common",
      """`POST /v1/payments` creates a charge. Mobile clients on flaky networks retry when a request times out, and some users double-tap "Pay". The candidate's plan: "Before inserting, check whether this user made a payment with the same amount in the last 60 seconds." What is the correct design?""",
      "Detect duplicates heuristically: same user, same amount, within a short time window.",
      """The heuristic is easy to explain and seems to catch the obvious case. But it blocks **legitimate** repeats (two ₹100 recharges in a minute), misses retries that arrive after the window, and races when two duplicates arrive at the same instant (both checks pass). Candidates also forget that the retry must get the **same response** as the original. The client needs to know what happened, not just avoid a second charge.""",
      """Use an **idempotency key** chosen by the client for each logical operation (a UUID sent in an `Idempotency-Key` header, reused on every retry):

1. **Atomically claim the key**: insert `(client_id, key, request_hash, status=IN_PROGRESS)` relying on a UNIQUE constraint. Only one request wins, even under concurrency.
2. Process the payment, then store the **status code and response body** with the key.
3. **Retry with the same key** after completion → return the stored response unchanged (same status, same body).
4. **Same key while still in progress** → `409 Conflict` (the client retries later).
5. **Same key with a different body** → `422`: that is a client bug, not a retry.
6. Expire keys after a period (for example 24-72 hours), and scope them per client or merchant.

PUT and DELETE are idempotent by definition when designed properly. POST is not, so it needs this. Pass the same key downstream to the payment provider.""",
      "Walk through the concurrent double-tap case (two requests, same key, same millisecond) and show the unique constraint deciding the winner.",
      fix="""```sql
CREATE TABLE idempotency_keys (
  client_id     BIGINT       NOT NULL,
  idem_key      VARCHAR(64)  NOT NULL,
  request_hash  CHAR(64)     NOT NULL,      -- SHA-256 of the request body
  status        VARCHAR(16)  NOT NULL,      -- IN_PROGRESS | COMPLETED
  response_code INT          NULL,
  response_body JSON         NULL,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (client_id, idem_key)         -- the race is decided here
);
```""",
      askedAt=["Razorpay", "Stripe", "PhonePe", "Juspay"]),

    T("trap-api-design-offset-pagination", A, "Offset pagination drift and deep-page slowness", "Intermediate", "Very common",
      """`GET /feed?page=3&size=20` is implemented as `ORDER BY created_at DESC LIMIT 20 OFFSET 40`. Users report **seeing the same post twice** while scrolling, and `page=5000` takes 4 seconds. Explain both, and what you would change.""",
      "Add an index on `created_at`; that fixes both the speed and the duplicates.",
      """Offset pagination is what every tutorial and Spring Data `Pageable` shows, so it feels standard. The drift bug only appears when data changes **between** page requests, which never happens in local testing. On speed, candidates assume an index lets the DB "jump" to row 100,000. It can't: `OFFSET` still walks through and discards every skipped row. And many forget a unique tie-breaker, so rows with equal timestamps shuffle between pages.""",
      """**Duplicates**: new posts are inserted at the top while the user scrolls, so everything shifts down. The item that was at position 40 is now at 41 and appears again on the next page. Deletes cause **skipped** items the same way.

**Slowness**: `OFFSET 100000` makes the DB read and throw away 100,000 rows, so cost grows with the page number.

**Fix: keyset (cursor) pagination.** Remember the last row you returned and ask for rows *after* it: `WHERE (created_at, id) < (last_created_at, last_id)`, ordered by `created_at DESC, id DESC`, with a composite index on `(created_at, id)`. The `id` breaks ties. Return an **opaque cursor** (base64 of those values) as `next_cursor`, and fetch `size + 1` rows to know whether there is a next page.

Trade-offs: no "jump to page 57" and no cheap total count, which is fine for feeds and infinite scroll. Always enforce a **maximum page size** (for example 100). An unbounded list endpoint is a production incident waiting to happen.""",
      "Mention the tie-breaker column; it is the detail that shows you have actually implemented cursor pagination.",
      fix="""```sql
-- first page
SELECT id, created_at, body FROM posts
 ORDER BY created_at DESC, id DESC
 LIMIT 21;                                  -- size + 1 => hasMore

-- next page: cursor = base64({"t":"2026-10-09T10:15:00Z","id":81234})
SELECT id, created_at, body FROM posts
 WHERE created_at < :t OR (created_at = :t AND id < :id)
 ORDER BY created_at DESC, id DESC
 LIMIT 21;
-- INDEX (created_at, id)
```""",
      askedAt=["Instagram", "Slack", "Flipkart", "Swiggy"]),

    T("trap-api-design-status-codes", A, "Status codes: 200-with-error, 401 vs 403", "Basic", "Very common",
      """A logged-in user with a valid JWT calls `DELETE /projects/42`, but they only have **viewer** access to that project. What should the API return?""",
      "401 Unauthorized, because the user is not authorised to delete; or 200 with `{\"success\": false}`.",
      """The names are misleading: "401 Unauthorized" really means **unauthenticated**. Many service-company codebases also return `200 OK` with an error flag because "the request reached the server successfully", and that habit sticks. Candidates don't connect status codes to the machinery that depends on them: client retry logic, caches, API gateways, monitoring dashboards and alerting all read the status code, not your JSON body.""",
      """**403 Forbidden**: the server knows who you are, and you are not allowed. Return **404** instead if revealing that project 42 even exists is itself a leak (GitHub does this for private repositories).

- **401**: missing, invalid or expired credentials ("who are you?"). Send a `WWW-Authenticate` header; the client should re-authenticate.
- **200 with an error body** breaks clients and observability: error-rate dashboards show 0%, caches may store the error, and retries can't tell what failed.

Other codes interviewers check: **400** malformed request vs **422** semantically invalid (either is fine if you are consistent); **409** conflict (version mismatch, duplicate); **429** rate limited; **503** temporary, retry later vs **500** bug; **201 + Location** for create; **204** for a successful delete with no body.

Use one consistent error format, for example RFC 9457 Problem Details, which Spring 6 supports through `ProblemDetail`.""",
      "Say \"401 is authentication, 403 is authorisation\" and mention the 404-to-hide option; that covers what the interviewer is checking.",
      options=[
          "200 OK with `{\"success\": false, \"error\": \"not allowed\"}`",
          "401 Unauthorized",
          "403 Forbidden (or 404 if you don't want to reveal the project exists)",
          "400 Bad Request",
      ], answer=2,
      fix="""```text
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Viewers cannot delete projects.",
  "instance": "/projects/42"
}
```""",
      askedAt=["Atlassian", "Amazon", "Freshworks", "Zoho"]),

    T("trap-api-design-put-vs-patch", A, "PUT vs PATCH semantics", "Basic", "Very common",
      """A user resource has `{name, email, phone}`. The client sends `PUT /users/7` with body `{"phone": "9876543210"}`, and the server maps the body onto the entity and saves it. What happens, and which statement is correct?""",
      "Only the phone changes; PUT and PATCH both mean \"update\" and are interchangeable.",
      """In CRUD-style codebases, "PUT = update" is the whole mental model, so the distinction between **replace** and **modify** never comes up until data disappears. Naive DTO-to-entity mapping turns every missing field into `null`. Candidates also memorise "PATCH is idempotent too" without asking what the patch *does*: an "append" or "increment" applied twice is not the same as applied once.""",
      """Under **PUT** semantics the body **is the complete new representation**, so `name` and `email` become `null`. Naive mapping does exactly that. PUT means create-or-replace at a known URI, and repeating it leaves the same state, so it is **idempotent**.

**PATCH** applies a change set:
- **JSON Merge Patch** (RFC 7396): fields present are set, `null` means remove, absent means untouched.
- **JSON Patch** (RFC 6902): a list of operations (`add`, `replace`, `remove`, `test`).

PATCH is **not guaranteed idempotent**: adding to an array or incrementing a counter changes the state each time.

Implementation details that come up in follow-ups:
- In Spring, distinguish **absent** from **explicitly null**: read a `JsonNode`, or use a wrapper such as `JsonNullable`.
- Prevent lost updates when two clients edit concurrently: `ETag` + `If-Match` (412 on mismatch) or a version field.
- Never let PATCH change protected fields (`id`, `role`, `ownerId`).""",
      "Say \"PUT replaces, PATCH modifies; PUT is idempotent, PATCH depends on the operation\", then mention absent vs null handling.",
      options=[
          "Only `phone` changes; PUT and PATCH are interchangeable.",
          "With PUT the body is the full new state, so `name`/`email` become null; partial updates belong in PATCH. PUT is idempotent; PATCH is not guaranteed to be.",
          "PUT is not idempotent, but PATCH always is.",
          "PATCH must always contain the full resource.",
      ], answer=1,
      fix="""```text
PUT /users/7            {"name":"Raj","email":"raj@x.com","phone":"9876543210"}   -> full replace
PATCH /users/7          Content-Type: application/merge-patch+json
                        {"phone":"9876543210"}            -> only phone changes
                        {"phone":null}                    -> phone removed
PATCH /users/7          Content-Type: application/json-patch+json
                        [{"op":"replace","path":"/phone","value":"9876543210"}]
Concurrency: GET returns ETag: "v7"; PATCH with If-Match: "v7" -> 412 if someone changed it
```""",
      askedAt=["TCS Digital", "Walmart", "Amazon"]),

    T("trap-api-design-idor", A, "IDOR / broken object-level authorization", "Intermediate", "Very common",
      f"""The endpoint below requires a valid JWT (Spring Security is configured). A security review flags it as **critical**. Why?

```java
{IDOR_BUGGY}
```""",
      "It's secure because every request must carry a valid JWT; use UUIDs instead of numeric ids if you're worried.",
      """Candidates treat **authentication** (who are you?) and **authorisation** (may you touch *this* object?) as one thing. Endpoint-level rules like `.anyRequest().authenticated()` feel complete, and tests are written with one user, so they never try user B's id. UUIDs feel like a fix because they are hard to guess, but ids leak through URLs, logs, emails and shared links. Obscurity is not access control.""",
      """Any logged-in user can change `orderId` and read **anyone's** order. That is **IDOR / Broken Object Level Authorization**, the #1 item in the OWASP API Security Top 10 (API1:2023), and it is behind many real data leaks. Sequential ids make enumeration trivial, but the bug is the **missing ownership check**, not the id format.

Fix:
- **Scope every lookup by owner or tenant in the query** (`findByIdAndCustomerId`), so another user's object is simply not found.
- Return **404**, not 403, so attackers cannot confirm the object exists.
- Centralise it: method security (`@PreAuthorize` calling an ownership check), or a tenant filter applied to every query.
- Apply the same rule to **writes**, and block mass assignment: never accept `customerId`, `role` or `price` from the request body.
- Add an automated test: user A requests user B's resource and expects 404.""",
      "Say \"authentication is not authorisation\", then show the ownership check living inside the query.",
      fix=f"""```java
{IDOR_FIX}
```
Spring Data derives `findByIdAndCustomerId` from the method name (`customer.id` or a `customerId` field).""",
      askedAt=["Razorpay", "CRED", "Paytm", "Swiggy"]),

    T("trap-api-design-breaking-changes", A, "What counts as a breaking API change", "Intermediate", "Common",
      """Mobile app v3.2 consumes `GET /v1/orders/{id}`, and you **cannot force everyone to upgrade**. Which change can you ship to `v1` without breaking those users?""",
      "Renaming `amount` to `totalAmount` is fine as long as the docs are updated.",
      """Inside one codebase, a rename is a refactor: the IDE updates every caller. Across a network, old clients are frozen binaries you cannot update, and mobile users keep old versions for months. Candidates also don't realise that *tightening* things (new required fields, stricter validation, new enum values) breaks clients just like removing things does. They also overlook that clients must be written to ignore unknown fields.""",
      """**Adding a new optional response field** is backward compatible, provided clients are **tolerant readers** that ignore unknown fields. Spring Boot's auto-configured `ObjectMapper` ignores them, but a plain `new ObjectMapper()` fails on unknown properties.

Breaking changes include: removing or renaming a field; changing a type, format or unit (number → string, paise → rupees); making an input required; stricter validation; changing defaults or meaning; and adding enum values that strict clients `switch` on.

For a necessary breaking change, use **expand and contract**:
1. Add the new field and keep the old one, populating both.
2. Migrate clients and **measure** usage of the old field.
3. Remove the old field only when usage reaches zero, or after the announced deadline.

For large changes, ship `/v2` (or a version header) **alongside** v1, announce a timeline with `Deprecation` and `Sunset` headers, and run contract tests (for example Pact) in CI to catch accidental breaks.""",
      "List both kinds: \"removing or renaming breaks, but so does tightening\"; that shows real API ownership experience.",
      options=[
          "Rename `amount` to `totalAmount`.",
          "Add a new optional field `deliveryEta` to the response.",
          "Change `id` from a number to a string.",
          "Make the optional request field `couponCode` required.",
      ], answer=1,
      fix="""```text
Expand and contract: rename amount -> totalAmount
v1 response today      : {"id": 9, "amount": 49900}
Step 1 (expand)        : {"id": 9, "amount": 49900, "totalAmount": 49900}
Step 2 (migrate)       : new app versions read totalAmount; dashboard tracks old-field reads
Step 3 (contract)      : remove "amount" after usage ~0 or the announced Sunset date
```""",
      askedAt=["Atlassian", "Swiggy", "Uber"]),

    T("trap-api-design-chatty-n-plus-one", A, "Chatty APIs: N+1 calls from the client", "Intermediate", "Common",
      """The order-history screen calls `GET /orders` (20 orders), then `GET /orders/{id}/items` for each order, then `GET /products/{pid}` for each item to show names and images. The screen takes **3+ seconds on 4G**. What is the problem, and how would you redesign the API?""",
      "Make each endpoint faster with caching, or fire all the calls in parallel.",
      """Resource-per-table REST design feels "clean" and maps neatly to JPA entities, so the API mirrors the database instead of the screen. Backend developers test on localhost, where a round trip is under 1 ms, and never feel what about 80 calls at 100-300 ms each do on mobile. Parallelising helps less than expected: connections are limited, every call pays auth and serialisation, and each endpoint may hit the database N+1 times again.""",
      """It is the **N+1 problem at the API layer**: 1 + 20 + roughly 60 requests for one screen. Latency is dominated by round trips, not by server time.

Redesign around the **use case**:
- **Embed what the screen needs**: `GET /orders?include=items` returns orders with their items, each carrying a product snapshot (name, image, price at purchase time). You need that snapshot anyway: the product's current price is not what the customer paid.
- **Batch endpoints** for lookups: `GET /products?ids=1,2,3`.
- A **BFF** (backend-for-frontend) that aggregates server-side, where calls between services are fast and parallel.
- **GraphQL** with a DataLoader-style batcher, if many clients need different shapes.

Guard the other side too: **sparse fieldsets** (`fields=`) to keep payloads small, a maximum page size, and server-side batch queries (`WHERE id IN (...)` or fetch joins), so the aggregated endpoint does not just move the N+1 into the database.""",
      "Count the round trips out loud (\"81 requests × 150 ms\") and then propose an endpoint shaped like the screen.",
      fix="""```text
Before: GET /orders -> 20 × GET /orders/{id}/items -> 60 × GET /products/{pid}   (81 round trips)
After : GET /orders?include=items&limit=20                                       (1 round trip)
{
  "orders": [{
    "id": 9001, "placedAt": "2026-10-01T10:00:00Z", "total": 129900,
    "items": [{"productId": 55, "name": "USB-C cable", "imageUrl": "...", "unitPrice": 49900, "qty": 1}]
  }],
  "nextCursor": "eyJpZCI6OTAwMX0"
}
```""",
      askedAt=["Swiggy", "Myntra", "Flipkart"]),

    T("trap-api-design-rate-limiting", A, "Rate limiting: per-instance counters and wrong status", "Intermediate", "Very common",
      """Requirement: each API key gets **100 requests per minute**. The service runs **6 instances** behind a load balancer. The candidate's design: an in-memory `ConcurrentHashMap<apiKey, counter>` in each instance, reset every minute; when the limit is exceeded, return `500`. What is wrong?""",
      "An in-memory counter per instance is fine, and the status code doesn't matter as long as the request is blocked.",
      """Candidates design for one JVM because that is how they test locally. They forget the load balancer spreads one client's traffic across instances. Fixed windows look exact until you check the boundary. Status codes feel cosmetic, but clients, SDKs and gateways decide whether and when to retry from them. This is also one of the most popular practical-coding and design prompts in 2026 loops, so interviewers know every weak spot.""",
      """Problems:
1. **Per-instance counters**: with 6 instances, the effective limit is up to **600/min**, and it is uneven.
2. **Fixed window bursts**: 100 requests at 0:59 and 100 at 1:00 means 200 in about 2 seconds.
3. **Wrong status**: return **429 Too Many Requests** with `Retry-After`, ideally with limit/remaining headers. A `500` tells clients the server is broken and may trigger immediate retries.

Better:
- **Shared state** in Redis with atomic operations (a Lua script), implementing a **token bucket** (allows bursts, smooth refill) or a **sliding-window counter**: `prev × (1 − elapsed/60) + current`.
- Enforce at the **edge** (API gateway) as well as per user, per tenant and globally. Give expensive endpoints lower limits.
- Decide **fail-open vs fail-closed** when Redis is unavailable (usually fail-open with a local fallback limit), and alert on it.""",
      "State the multi-instance problem first (\"6 instances means 600/min\"); then the algorithm choice and 429 + Retry-After.",
      fix="""```text
Sliding-window counter (per key, Redis):
  curr = INCR rl:{key}:{minute}         (+ EXPIRE 120 on first write, inside one Lua script)
  prev = GET  rl:{key}:{minute-1}
  estimate = prev * (60 - secondsIntoMinute) / 60 + curr
  if estimate > 100 -> reject

HTTP/1.1 429 Too Many Requests
Retry-After: 12
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
```""",
      askedAt=["Stripe", "Razorpay", "Atlassian", "Uber"]),
]

CHECKS = [
    {"name": "api-idor", "lang": "java", "code": """import java.util.*;
import java.lang.annotation.*;
public class Main {
  static final class AppUser { long id; AppUser(long id) { this.id = id; } long getId() { return id; } }
  static final class Order { long id, customerId; Order(long i, long c) { id = i; customerId = c; } }
  record OrderDto(long id) {}
  static final class NotFoundException extends RuntimeException {}
  interface OrderRepository { Optional<Order> findById(Long id); Optional<Order> findByIdAndCustomerId(Long id, long customerId); }
  interface Mapper { OrderDto toDto(Order o); }
  static Map<Long, Order> db = Map.of(1L, new Order(1, 100), 2L, new Order(2, 200));
  OrderRepository orderRepository = new OrderRepository() {
    public Optional<Order> findById(Long id) { return Optional.ofNullable(db.get(id)); }
    public Optional<Order> findByIdAndCustomerId(Long id, long c) { return findById(id).filter(o -> o.customerId == c); }
  };
  Mapper mapper = o -> new OrderDto(o.id);
""" + "\n".join("  " + l for l in IDOR_FIX.splitlines()) + """
""" + "\n".join("  " + l for l in IDOR_BUGGY.replace("getOrder(", "getOrderOld(").splitlines()) + """
  public static void main(String[] a) {
    Main m = new Main(); AppUser me = new AppUser(100);
    System.out.println(m.getOrder(1L, me));
    try { m.getOrder(2L, me); System.out.println("LEAK"); } catch (NotFoundException e) { System.out.println("404 for other user's order"); }
    System.out.println("old " + m.getOrderOld(2L));
  }
}
@Retention(RetentionPolicy.RUNTIME) @interface GetMapping { String value(); }
@Retention(RetentionPolicy.RUNTIME) @interface PathVariable {}
@Retention(RetentionPolicy.RUNTIME) @interface AuthenticationPrincipal {}
""", "expect": ["OrderDto[id=1]", "404 for other user's order", "old OrderDto[id=2]"]},
]
