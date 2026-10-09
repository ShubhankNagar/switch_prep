from sd_common import *

topics = []

topics.append(T("observability", "Observability: Logs, Metrics, Tracing, SLOs", "Intermediate",
"How to know what a distributed system is doing in production: structured logs, metrics, distributed tracing, alerting, and SLI/SLO/SLA definitions.",
r'''
## Monitoring vs observability

**Monitoring** tells you *that* something is wrong (error rate alert fired). **Observability** lets you ask *why* without shipping new code: which service, which endpoint, which customer, which query. In a microservice system where one request touches 10 services, you need three complementary signals: **logs, metrics and traces** (the "three pillars").

## Logs

Discrete, timestamped records of events.

- Use **structured logging** (JSON) rather than free text so logs are searchable by field:
```text
{"ts":"2026-10-08T10:15:02Z","level":"ERROR","service":"payment","traceId":"4bf92f35","userId":42,
 "orderId":991,"msg":"Gateway timeout","latencyMs":3001}
```
- Include a **correlation/trace ID** in every log line (Spring Boot 3 with Micrometer Tracing puts `traceId`/`spanId` in the MDC automatically).
- Levels: ERROR (needs attention), WARN, INFO (business events), DEBUG (off in prod).
- Never log passwords, OTPs, card numbers, full Aadhaar/PAN, or tokens. Mask PII.
- Pipeline: app → stdout → agent (Fluent Bit/Filebeat) → Kafka (buffer) → Elasticsearch/OpenSearch or Loki → Kibana/Grafana. Set retention (e.g., 7-30 days hot, archive to S3).
- Logs are expensive at volume; sample noisy INFO logs and avoid logging inside tight loops.

## Metrics

Numeric time series, cheap to store and fast to query, ideal for dashboards and alerts.

Types:
- **Counter**: only increases (requests_total, errors_total).
- **Gauge**: goes up and down (active connections, queue depth, JVM heap used).
- **Histogram/summary**: distribution of values (request latency) → compute **percentiles** p50, p95, p99.

Why percentiles, not averages: if 99 requests take 50 ms and one takes 5 s, the average (~100 ms) hides the user who waited 5 s. **p99 latency** reflects tail experience; at scale, 1% is thousands of users, and fan-out requests hit the tail often.

Frameworks:
- **RED** method for services: **R**ate, **E**rrors, **D**uration.
- **USE** method for resources: **U**tilisation, **S**aturation, **E**rrors (CPU, disk, connection pools).
- **Four golden signals** (Google SRE): latency, traffic, errors, saturation.

Spring Boot stack: Actuator + Micrometer exposes `/actuator/prometheus`; **Prometheus** scrapes every 15 s; **Grafana** dashboards; Alertmanager routes alerts to Slack/PagerDuty. Useful built-in metrics: `http_server_requests_seconds`, `hikaricp_connections_pending`, `jvm_gc_pause_seconds`, Kafka consumer lag.

Watch out for **high cardinality**: a label like `userId` creates millions of time series and crashes Prometheus. Use bounded labels (endpoint, status code, region).

## Distributed tracing

A **trace** follows one request across services; it consists of **spans** (one per operation: HTTP call, DB query, Kafka publish), each with start time, duration and parent span.

```text
Trace 4bf92f35 (total 820 ms)
|- api-gateway            GET /checkout           820 ms
   |- order-service       POST /orders            790 ms
      |- mysql            INSERT orders            12 ms
      |- inventory-svc    POST /reserve            45 ms
      |- payment-svc      POST /charge            700 ms   <- bottleneck
         |- razorpay      HTTP                    690 ms
```

- Context propagates via headers (W3C `traceparent`). Spring Boot 3 uses Micrometer Tracing with an OpenTelemetry bridge; collectors export to Jaeger, Zipkin, Tempo or vendor tools (Datadog, New Relic).
- **Sampling**: tracing every request is costly; sample 1-10% plus always keep errors and slow requests (tail-based sampling).
- Tracing answers "which service made checkout slow?" in seconds.

**OpenTelemetry** is the vendor-neutral standard for all three signals; mention it.

## Alerting

- Alert on **symptoms users feel** (error rate, latency SLO burn), not on every cause (CPU 80% is not necessarily a problem).
- Every alert must be actionable and link to a runbook. Too many noisy alerts → alert fatigue → real incidents missed.
- Severity tiers: page someone at night only for user-impacting issues.

## SLI, SLO, SLA

- **SLI (Service Level Indicator)**: a measured metric, e.g., "proportion of checkout requests that succeed in under 300 ms".
- **SLO (Objective)**: internal target for an SLI over a window: "99.9% of checkout requests succeed under 300 ms over 30 days".
- **SLA (Agreement)**: contractual promise to customers with penalties (credits) if missed, typically looser than the SLO (e.g., 99.5%).

**Error budget** = 1 − SLO. At 99.9% over 30 days, you can "spend" 43 minutes of unavailability or 0.1% failed requests. If the budget is exhausted, freeze risky releases and focus on reliability; if lots remain, ship faster. Alert on **burn rate** (e.g., spending a month's budget in 2 days).

| SLO | Allowed downtime / 30 days |
|---|---|
| 99% | 7.2 hours |
| 99.9% | 43.2 minutes |
| 99.95% | 21.6 minutes |
| 99.99% | 4.3 minutes |

## Health checks, dashboards and incident response

- Liveness/readiness endpoints (`/actuator/health`), synthetic monitoring (probe the login flow every minute from outside).
- A service dashboard: traffic, error %, p50/p95/p99 latency, saturation (CPU, heap, DB pool, queue lag), dependency health.
- Incidents: detect → mitigate first (rollback, feature flag off, scale up) → investigate with traces/logs → blameless postmortem with action items.

## Interview phrasing

"Each service exports RED metrics via Micrometer to Prometheus, with Grafana dashboards and alerts on SLO burn rate: checkout SLO is 99.9% success under 500 ms p99. Logs are structured JSON with traceId shipped through Fluent Bit to OpenSearch. OpenTelemetry traces across services in Tempo with 5% sampling plus all errors. Business metrics like orders per minute have anomaly alerts too."
''',
["Three pillars: logs (events), metrics (numbers over time), traces (request path)",
 "Structured JSON logs with traceId; never log secrets or PII",
 "Metric types: counter, gauge, histogram; track p95/p99, not averages",
 "RED for services, USE for resources, four golden signals",
 "Tracing: spans across services, W3C traceparent, OpenTelemetry, sample smartly",
 "SLI = measurement, SLO = internal target, SLA = contract with penalties",
 "Error budget = 1 - SLO; alert on burn rate and user-facing symptoms",
 "Avoid high-cardinality metric labels like userId"],
[("What is the difference between logs, metrics and traces?",
 "Logs are detailed, timestamped event records useful for debugging specific failures. Metrics are aggregated numeric time series (request rate, error count, latency histograms) that are cheap to store and ideal for dashboards and alerting. Traces follow a single request across services as a tree of spans, showing where time was spent. Together: metrics tell you something is wrong, traces show where, logs explain why."),
 ("Why use p99 latency instead of average?",
 "Averages hide outliers: a few very slow requests barely move the mean but ruin those users' experience. p99 means 99% of requests are faster than this value, so it captures tail latency. At high scale, 1% is many users, and when a page calls many services, the chance that at least one call hits the tail is high, so tail latency dominates perceived performance."),
 ("Explain SLI, SLO, SLA and error budgets.",
 "An SLI is a measured indicator, like the percentage of requests served successfully under 300 ms. An SLO is the target for it, like 99.9% over 30 days. An SLA is an external contract with consequences if missed, usually looser than the SLO. The error budget is 1 minus the SLO, e.g., 0.1% of requests or about 43 minutes a month, and it guides whether to prioritise releases or reliability work."),
 ("How does distributed tracing work?",
 "When a request enters the system, a trace ID is created and propagated to each downstream call via headers such as W3C traceparent. Each service records spans with start time, duration, parent span and metadata, and exports them to a collector like Jaeger or Tempo, which reassembles the tree. In Spring Boot 3, Micrometer Tracing with OpenTelemetry instruments HTTP clients, servers, JDBC and Kafka automatically and adds traceId to logs."),
 ("What would you monitor for a Spring Boot microservice?",
 "RED metrics per endpoint: request rate, error rate and latency percentiles. Resource metrics: CPU, JVM heap and GC pauses, thread pool usage, HikariCP active and pending connections, and Kafka consumer lag. Dependency metrics: DB query latency, circuit breaker states, downstream error rates. Business metrics like orders per minute. Alerts on SLO burn rate and saturation, with dashboards and runbooks.")],
[("Google SRE Book - Monitoring Distributed Systems", "https://sre.google/sre-book/monitoring-distributed-systems/"), ("Google SRE Book - Service Level Objectives", "https://sre.google/sre-book/service-level-objectives/"), ("OpenTelemetry documentation", "https://opentelemetry.io/docs/"), ("Spring Boot - Observability", "https://docs.spring.io/spring-boot/reference/actuator/observability.html"), ("Prometheus documentation", "https://prometheus.io/docs/introduction/overview/")]))

topics.append(T("security-auth", "Security and Authentication: Sessions, JWT, OAuth2, HTTPS, OWASP", "Intermediate",
"How users and services prove who they are and what they may do: sessions vs JWT, OAuth2/OIDC flows, HTTPS/TLS, password storage and the OWASP basics every backend must handle.",
r'''
## Authentication vs authorization

- **Authentication (AuthN)**: who are you? (password, OTP, OAuth login).
- **Authorization (AuthZ)**: what are you allowed to do? (roles, permissions, ownership checks).

A classic bug: user 42 is authenticated but calls `GET /orders/991` belonging to user 77 and the API returns it. That is broken object-level authorization, #1 in OWASP API Security Top 10. Always check ownership in the service layer.

## Session-based authentication

1. User logs in; server verifies password, creates a session in a store, returns a `Set-Cookie: SESSIONID=...; HttpOnly; Secure; SameSite=Lax`.
2. Browser sends the cookie on every request; server looks up the session.

- Pros: easy revocation (delete session), small cookie, server controls everything.
- Cons: requires a shared session store when horizontally scaled (Spring Session + Redis), a lookup per request, CSRF protection needed because cookies are sent automatically.

## Token-based authentication with JWT

A **JWT** (JSON Web Token) has three base64url parts: `header.payload.signature`.

```text
header:  {"alg":"RS256","typ":"JWT","kid":"key-2026-10"}
payload: {"sub":"42","roles":["USER"],"iat":1759900000,"exp":1759900900,"iss":"auth.myapp.com"}
signature: RS256(header.payload, private key)
```

- The server (or any service with the public key) verifies the signature and expiry **without a database lookup**: stateless, ideal for microservices and the API gateway.
- The payload is only encoded, **not encrypted**: never put secrets or sensitive PII in it.
- **HS256** uses a shared secret (every verifier can also forge tokens); **RS256/ES256** use a private key to sign and public key to verify (published at a JWKS endpoint). Prefer asymmetric in microservices.

### The revocation problem and access/refresh tokens

A stateless JWT is valid until it expires, even if the user logs out or is banned. Standard solution:

- **Short-lived access token** (5-15 min) sent as `Authorization: Bearer ...`.
- **Long-lived refresh token** (days/weeks), stored securely (HttpOnly cookie on web, secure storage on mobile), kept in a DB so it can be revoked; used only at `/token/refresh` to get a new access token. **Rotate** refresh tokens on each use and detect reuse (indicates theft).
- For immediate revocation: a small denylist of token IDs (`jti`) in Redis until their expiry.

### Where to store tokens in the browser

`localStorage` is readable by any injected script (XSS steals it). HttpOnly cookies can't be read by JS but need CSRF defences (SameSite cookies, CSRF tokens). Many teams use an HttpOnly cookie for the refresh token and keep the access token in memory.

| | Sessions | JWT |
|---|---|---|
| State | Server-side store | Stateless (self-contained) |
| Revocation | Immediate | Hard; short expiry + denylist |
| Scaling | Shared store needed | Easy; verify with public key |
| Size | Small cookie | Larger header per request |
| Best for | Traditional web apps | APIs, mobile, microservices |

## OAuth 2.0 and OpenID Connect

**OAuth 2.0** is a framework for **delegated authorization**: letting an application access resources on a user's behalf without getting their password (e.g., an app reading your Google Calendar). **OpenID Connect (OIDC)** adds **authentication** on top: an `id_token` (JWT) describing who the user is. "Login with Google" is OIDC.

Roles: **Resource owner** (user), **Client** (your app), **Authorization server** (Google, Keycloak, Auth0, Okta), **Resource server** (the API).

### Authorization Code flow with PKCE (for web and mobile apps)

```text
1. App redirects user to auth server: /authorize?client_id&redirect_uri&scope=openid profile
                                       &code_challenge=SHA256(verifier)&state=xyz
2. User logs in and consents at the auth server
3. Auth server redirects back: redirect_uri?code=AUTH_CODE&state=xyz
4. App backend (or mobile app) POSTs /token with code + code_verifier
5. Auth server returns access_token (+ refresh_token, id_token)
6. App calls API with Authorization: Bearer access_token
```

PKCE prevents an intercepted code from being exchanged by an attacker. The `state` parameter prevents CSRF on the callback.

### Client Credentials flow (service-to-service)

A backend service authenticates with its own client ID/secret (or certificate) to get a token for calling another service. No user involved. Used for internal APIs and partner integrations.

The old **Implicit** and **Password** grants are deprecated.

In Spring: `spring-boot-starter-oauth2-resource-server` validates JWTs against the issuer's JWKS; `spring-security-oauth2-client` handles login flows. Keycloak is a popular self-hosted auth server.

## HTTPS and TLS

TLS provides **encryption** (no eavesdropping on public Wi-Fi), **integrity** (no tampering) and **server authentication** (certificates signed by a trusted CA prove you're talking to the real bank).

Handshake simplified (TLS 1.3): client hello with supported ciphers and key share → server responds with its certificate and key share → both derive a symmetric session key (ECDHE) → encrypted traffic with fast symmetric crypto (AES-GCM). TLS 1.3 needs one round trip (0-RTT for resumption).

Practices: HTTPS everywhere, HSTS header, TLS terminated at LB/CDN, **mTLS** between internal services (both sides present certificates; service meshes automate it), auto-renewing certificates (Let's Encrypt, ACM).

## Password storage

Never store plain or simply hashed (MD5/SHA-256) passwords. Use a slow, salted, adaptive hash: **bcrypt** (Spring's `BCryptPasswordEncoder`, cost 10-12), **scrypt** or **Argon2**. Add rate limiting and lockouts on login, and MFA/OTP for sensitive actions.

## OWASP Top 10 basics (what to mention)

| Risk | Defence |
|---|---|
| Broken access control / IDOR | Check ownership and roles on every request, deny by default |
| Injection (SQL, command) | Parameterised queries / JPA, never concatenate user input |
| XSS | Output encoding, Content-Security-Policy, Angular's built-in sanitisation |
| CSRF | SameSite cookies, CSRF tokens (Spring Security), or bearer tokens |
| Cryptographic failures | TLS everywhere, encrypt sensitive data at rest, strong hashing |
| Security misconfiguration | No default creds, disable stack traces in responses, least privilege |
| Vulnerable components | Dependency scanning (OWASP Dependency-Check, Dependabot) |
| SSRF | Validate/allowlist outbound URLs, block internal IP ranges |
| Auth failures | MFA, rate-limit login, secure session handling |
| Logging/monitoring failures | Audit logs for auth events, alerts on anomalies |

Also: secrets in a vault (AWS Secrets Manager, HashiCorp Vault), not in Git; input validation; rate limiting; principle of least privilege for DB users and IAM roles.

## Interview phrasing

"Users log in through an OIDC provider (Keycloak) using Authorization Code + PKCE. The gateway validates RS256 access tokens (15-min expiry) via JWKS and forwards user ID and roles; services still enforce object-level authorization. Refresh tokens are rotated and stored server-side for revocation. Internal traffic uses mTLS, passwords use bcrypt, and all queries are parameterised."
''',
["AuthN = who you are; AuthZ = what you can do; always check object ownership",
 "Sessions: server-side state, easy revocation, need shared store (Redis) and CSRF protection",
 "JWT: signed (not encrypted), stateless verification; prefer RS256 with JWKS",
 "Short-lived access token + rotating revocable refresh token",
 "OAuth2 = delegated authorization; OIDC adds identity (id_token)",
 "Authorization Code + PKCE for apps; Client Credentials for service-to-service",
 "TLS gives encryption, integrity, server authentication; mTLS internally",
 "Hash passwords with bcrypt/Argon2; parameterised queries; OWASP Top 10"],
[("Sessions vs JWT: which would you choose?",
 "Sessions keep state on the server and send only an ID cookie: easy revocation and small cookies, but every request needs a session-store lookup and horizontally scaled apps need a shared store like Redis. JWTs are self-contained and verified with a key, so any service can authenticate without a lookup, which suits APIs, mobile and microservices, but revocation is hard. I'd use short-lived JWT access tokens with revocable refresh tokens for an API platform."),
 ("How do you log out a user when using JWTs?",
 "Since a JWT stays valid until expiry, keep access tokens short-lived (5-15 minutes). On logout, delete or revoke the refresh token in the database so no new access tokens can be issued, and clear the client cookies or storage. For immediate revocation, add the access token's jti to a Redis denylist with TTL equal to its remaining lifetime and check it at the gateway."),
 ("Explain the OAuth2 Authorization Code flow with PKCE.",
 "The app generates a random code verifier and sends its hash as a code challenge when redirecting the user to the authorization server. The user logs in and consents, and the server redirects back with a short-lived authorization code. The app exchanges the code plus the original verifier at the token endpoint and receives access, refresh and id tokens. PKCE ensures a stolen code is useless without the verifier."),
 ("How do you securely store passwords?",
 "Never store plaintext or fast hashes like MD5 or SHA-256. Use an adaptive, salted, deliberately slow algorithm such as bcrypt, scrypt or Argon2, which makes brute forcing expensive; each password gets a unique random salt stored with the hash. In Spring Security, BCryptPasswordEncoder with cost around 10-12. Add login rate limiting, account lockouts and MFA."),
 ("How do you prevent SQL injection and IDOR?",
 "For SQL injection, never concatenate user input into SQL; use parameterised queries or prepared statements, which JPA and JdbcTemplate do with bind parameters, plus input validation and least-privilege DB users. For IDOR, always authorise access to specific objects: after loading the order, verify order.userId equals the authenticated user or the user has an admin role; prefer queries like findByIdAndUserId."),
 ("Why use HTTPS everywhere, even internally?",
 "TLS encrypts traffic, protects integrity and authenticates the server. Externally it stops eavesdropping and tampering on untrusted networks. Internally, zero-trust thinking assumes attackers may get inside the network, so mTLS between services prevents snooping and impersonation, and certificates double as service identity. Service meshes like Istio automate certificate rotation.")],
[("OWASP Top 10", "https://owasp.org/www-project-top-ten/"), ("OWASP API Security Top 10", "https://owasp.org/API-Security/"), ("OAuth 2.0 Simplified (Aaron Parecki)", "https://www.oauth.com/"), ("RFC 7636 - PKCE", "https://datatracker.ietf.org/doc/html/rfc7636"), ("jwt.io introduction", "https://jwt.io/introduction"), ("Spring Security reference", "https://docs.spring.io/spring-security/reference/")]))

topics.append(T("unique-id-generation", "Unique ID Generation in Distributed Systems", "Intermediate",
"Generating globally unique, often sortable IDs without a single database bottleneck: auto-increment, UUIDs, ticket servers, Snowflake, ULID/UUIDv7.",
r'''
## The problem

With one MySQL database, `AUTO_INCREMENT` gives unique, increasing IDs. Once you shard across many databases or many services generate IDs, each shard's counter collides with the others. Requirements usually are:

- **Globally unique**.
- **Fast**: generated without a network round trip, thousands to millions per second.
- **Roughly time-sortable**: newer IDs are larger, so B+ tree inserts are sequential and "latest first" queries can sort by ID.
- **Compact**: fits in 64 bits (BIGINT) ideally.
- Sometimes **not guessable** (public order IDs shouldn't reveal business volume or allow enumeration).

## Option 1: Database auto-increment

- Single DB: simple and perfect at small scale.
- **Multiple DBs with offsets**: server 1 generates 1, 3, 5...; server 2 generates 2, 4, 6... (`auto_increment_increment=2`, `auto_increment_offset`). Adding servers later is painful; IDs aren't time-ordered across servers.
- Exposes counts and enables enumeration if used publicly.

## Option 2: UUID

128-bit identifiers generated locally, e.g., `550e8400-e29b-41d4-a716-446655440000`.

- **UUIDv4**: 122 random bits. Collision probability negligible (you'd need ~2.7 × 10^18 IDs for a 50% chance). No coordination at all.
- Downsides: 128 bits (16 bytes binary, 36 chars as string), **not sortable**, random inserts fragment InnoDB's clustered index (page splits, poor cache locality), larger secondary indexes.
- **UUIDv7** (RFC 9562, 2024): 48-bit Unix millisecond timestamp prefix + random bits → time-ordered, index-friendly, still generated locally. A great modern default when 128 bits is acceptable. Store as `BINARY(16)` in MySQL.
- **ULID**: similar idea (48-bit time + 80-bit random), encoded as 26-char Crockford base32, lexicographically sortable.

## Option 3: Ticket server (centralised counter)

A dedicated service (Flickr used two MySQL "ticket" servers with `REPLACE INTO` and odd/even offsets) hands out IDs.

- Numeric, sequential, simple.
- Single point of failure/bottleneck; network hop per ID.
- **Batching (segment/range allocation)**: each app instance fetches a range (e.g., 1,000 IDs) at once and hands them out locally; only goes back when exhausted. This makes it fast (used by Meituan's Leaf "segment" mode). Ranges get lost if an instance crashes (gaps are fine). Redis `INCRBY key 1000` works the same way.

## Option 4: Twitter Snowflake (the interview favourite)

A 64-bit integer composed of:

```text
| 1 bit | 41 bits timestamp (ms since custom epoch) | 10 bits machine id | 12 bits sequence |
|   0   |            ~69 years of milliseconds        | 1,024 machines     | 4,096 per ms     |
```

- **Sign bit**: 0, keeps it positive in signed BIGINT/Java long.
- **Timestamp**: milliseconds since a custom epoch (e.g., 2020-01-01), 41 bits ≈ 69 years.
- **Machine/worker ID**: 10 bits = 1,024 generators (often split into 5 bits datacenter + 5 bits worker).
- **Sequence**: 12 bits = 4,096 IDs per millisecond per machine → **~4 million IDs/sec per machine**.

Properties: 64-bit, roughly time-sortable (k-sorted across machines), generated locally with no coordination, and the timestamp can be extracted from the ID (useful for debugging and range queries).

```java
public final class Snowflake {
    private static final long EPOCH = 1577836800000L; // 2020-01-01
    private final long workerId;          // 0..1023
    private long lastTs = -1L, seq = 0L;

    public Snowflake(long workerId) { this.workerId = workerId; }

    public synchronized long nextId() {
        long ts = System.currentTimeMillis();
        if (ts < lastTs) throw new IllegalStateException("Clock moved backwards");
        if (ts == lastTs) {
            seq = (seq + 1) & 4095;              // 12 bits
            if (seq == 0) {                       // exhausted this ms, wait for next
                while ((ts = System.currentTimeMillis()) <= lastTs) { }
            }
        } else {
            seq = 0;
        }
        lastTs = ts;
        return ((ts - EPOCH) << 22) | (workerId << 12) | seq;
    }
}
```

### Snowflake challenges

- **Assigning worker IDs**: must be unique among live generators. Use config per pod (StatefulSet ordinal), or lease IDs from ZooKeeper/etcd/Redis on startup with a TTL heartbeat.
- **Clock skew/backwards clock** (NTP adjustments): duplicates are possible if time goes back. Options: refuse to generate until the clock catches up (if small), or use last timestamp and keep incrementing, alert on large drift.
- **Not strictly ordered** across machines within the same millisecond, only roughly; good enough for feeds and indexes.
- **Predictability**: IDs reveal creation time and approximate volume. For public URLs, you may encode/obfuscate or use a random public ID alongside.

Variants: Instagram's IDs (41-bit time + 13-bit logical shard ID + 10-bit sequence, generated inside PostgreSQL), Sony's Sonyflake (39-bit time in 10 ms units, 16-bit machine, 8-bit sequence, longer lifespan), Baidu UidGenerator, Discord snowflakes.

## Comparison

| Approach | Size | Sortable | Coordination | Throughput | Notes |
|---|---|---|---|---|---|
| Auto-increment | 64-bit | Yes (single DB) | DB | DB-bound | Breaks with sharding |
| UUIDv4 | 128-bit | No | None | Very high | Index fragmentation |
| UUIDv7 / ULID | 128-bit | Yes | None | Very high | Modern default |
| Ticket server + ranges | 64-bit | Mostly | Central service | High with batching | Simple, needs HA |
| Snowflake | 64-bit | Roughly | Worker ID assignment | ~4M/s per node | Clock skew care |

## Choosing in interviews

- URL shortener codes: counter/range allocation → base62 encode, or hash + collision check.
- Tweets, messages, orders in sharded DBs: **Snowflake** (64-bit, sortable, fits BIGINT; can embed shard ID).
- Internal entities where 128 bits is fine: **UUIDv7**.
- Payment/order references shown to users: a separate human-friendly unique reference, not the internal sequence.

## Interview phrasing

"I'll use Snowflake-style 64-bit IDs: 41 bits of milliseconds, 10 bits worker ID leased from ZooKeeper at startup, 12 bits sequence, giving ~4M IDs/s per node with no coordination on the hot path. IDs are time-ordered so InnoDB inserts are sequential and I can paginate by ID. I'll handle clock rollback by waiting or failing fast with an alert."
''',
["Auto-increment breaks once data is sharded or multiple writers generate IDs",
 "UUIDv4: no coordination but 128-bit, random, fragments InnoDB clustered index",
 "UUIDv7/ULID: time-prefixed, sortable, generated locally",
 "Ticket server with range/segment allocation is simple and fast with batching",
 "Snowflake: 1 sign + 41 time + 10 worker + 12 sequence bits = 64-bit",
 "Snowflake gives ~4,096 IDs/ms per worker (~4M/s), roughly time-sorted",
 "Worker ID assignment and clock rollback are Snowflake's main challenges",
 "Use separate non-guessable public references when needed"],
[("Explain Twitter Snowflake ID structure.",
 "It's a 64-bit integer: 1 unused sign bit, 41 bits of milliseconds since a custom epoch (about 69 years), 10 bits of machine or worker ID (1,024 generators), and 12 bits of per-millisecond sequence (4,096 IDs per ms per worker). Each node generates IDs locally without coordination, IDs are roughly time-ordered, fit in a BIGINT, and the creation time can be extracted from the ID."),
 ("Why not just use UUIDs as primary keys in MySQL?",
 "Random UUIDv4 keys are 16 bytes (36 as strings) and inserted at random positions in InnoDB's clustered B+ tree, causing page splits, fragmentation and poor buffer pool locality, which slows inserts at scale. Every secondary index stores the PK, so they grow too. If I need UUIDs, I'd use time-ordered UUIDv7 stored as BINARY(16); otherwise a 64-bit Snowflake ID."),
 ("How do you assign worker IDs in Snowflake on Kubernetes?",
 "Options: use a StatefulSet and derive the worker ID from the pod ordinal; or on startup lease a free worker ID from ZooKeeper, etcd or Redis using an ephemeral node or a key with TTL renewed by heartbeat, releasing it on shutdown. The key requirement is that no two live generators share an ID, including during restarts, so leases must expire safely before reuse."),
 ("What happens if the system clock moves backwards?",
 "A Snowflake generator could produce timestamps it already used, risking duplicate IDs. Mitigations: detect that the current time is less than the last timestamp; for small drift, wait until the clock catches up; for large drift, refuse to generate and alert, or switch to a backup worker ID. Run NTP in slew mode to avoid sudden jumps, and some implementations keep a logical clock that never goes backwards."),
 ("How would you generate IDs for a URL shortener?",
 "One approach: a distributed counter with range allocation. Each app server reserves a block of numbers (say 10,000) from a ticket service, ZooKeeper or Redis INCRBY, then converts each number to base62, giving short unique codes with no collisions. Alternatively hash the long URL (MD5/Base62, take 7 chars) and check for collisions in the DB. Counters are simpler and collision-free but codes are guessable; adding a shuffle or bijective obfuscation helps.")],
[("Twitter Engineering - Announcing Snowflake", "https://blog.x.com/engineering/en_us/a/2010/announcing-snowflake"), ("Instagram Engineering - Sharding & IDs at Instagram", "https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c"), ("RFC 9562 - UUID versions including v7", "https://www.rfc-editor.org/rfc/rfc9562"), ("Flickr - Ticket Servers", "https://code.flickr.net/2010/02/08/ticket-servers-distributed-unique-primary-keys-on-the-cheap/"), ("ByteByteGo - Design a unique ID generator", "https://bytebytego.com/courses/system-design-interview/design-a-unique-id-generator-in-distributed-systems")]))

topics.append(T("search-elasticsearch", "Search and Elasticsearch", "Intermediate",
"How full-text search works: inverted indexes, analyzers, relevance scoring, Elasticsearch architecture (shards, replicas), and keeping it in sync with MySQL.",
r'''
## Why not just SQL LIKE?

`SELECT * FROM products WHERE name LIKE '%red shoe%'` can't use a B+ tree index (leading wildcard), scans every row, doesn't match "shoes" or "Red Shoes for men", has no typo tolerance and no relevance ranking. Product search, log search, autocomplete and filtering by many facets need a **search engine**: Elasticsearch/OpenSearch, Apache Solr (both built on Apache Lucene), or managed options like Algolia.

## The inverted index

Like the index at the back of a book: term → list of documents (postings) containing it.

```text
Doc1: "Red running shoes"
Doc2: "Blue running jacket"
Doc3: "Red jacket"

Term      -> Postings (docId: positions)
red       -> 1:[0], 3:[0]
running   -> 1:[1], 2:[1]
shoe      -> 1:[2]          (after stemming "shoes" -> "shoe")
blue      -> 2:[0]
jacket    -> 2:[2], 3:[1]
```

Query "red jacket": look up both terms, intersect/union posting lists, score → Doc3 first (both terms), then Doc1 and Doc2. Posting lists are sorted and compressed, so intersections are fast even over millions of documents. Positions enable phrase queries ("running shoes" in order).

## Analysis: turning text into terms

At index time and query time, text passes through an **analyzer**:

1. **Character filters**: strip HTML, normalise characters.
2. **Tokenizer**: split into tokens (standard tokenizer splits on whitespace/punctuation).
3. **Token filters**: lowercase, remove stop words ("the", "for"), **stemming** ("running" → "run"), synonyms ("tv" ↔ "television", "mobile" ↔ "phone"), ASCII folding.

Special analyzers: **edge n-grams** for search-as-you-type ("iph" matches "iphone"), language analyzers (Hindi, etc.), phonetic matching.

**Field types matter**: `text` fields are analyzed for full-text search; `keyword` fields are stored as-is for exact match, sorting and aggregations (brand, category, SKU). Often a field is mapped as both.

## Relevance scoring

Elasticsearch uses **BM25** by default (an improved TF-IDF):
- **Term frequency**: more occurrences in a doc → more relevant (with saturation).
- **Inverse document frequency**: rare terms matter more than common ones ("iphone" outweighs "phone").
- **Field length normalisation**: a match in a short title beats one in a long description.

Business ranking on top: boost title over description (`title^3`), `function_score` to boost by popularity, rating, in-stock, recency, sponsored listings. Large e-commerce sites add learning-to-rank models.

## Elasticsearch architecture

```text
Cluster
 |- Node 1: [products P0 primary] [products P1 replica]
 |- Node 2: [products P1 primary] [products P2 replica]
 |- Node 3: [products P2 primary] [products P0 replica]
```

- **Index**: a collection of documents (like a table), with a **mapping** (schema).
- **Document**: JSON object with an `_id`.
- **Shard**: an index is split into primary shards (each is a Lucene index); number of primaries is fixed at creation (resizing needs reindex/split). Target shard size ~10-50 GB.
- **Replica**: copy of a primary on another node, for high availability and read throughput.
- **Routing**: `shard = hash(_id or routing) % number_of_primary_shards`.
- **Query execution (scatter-gather)**: the coordinating node sends the query to one copy of every shard, each returns top-N doc IDs with scores (query phase), the coordinator merges and fetches the documents (fetch phase).
- **Near real-time**: new documents become searchable after a **refresh** (default 1 s), when the in-memory buffer becomes a new Lucene segment. Segments are immutable and merged in the background; updates are delete + reindex.
- Durability via a **translog** (write-ahead log).

## Example query

```text
GET /products/_search
{
  "query": {
    "bool": {
      "must":   [{ "multi_match": { "query": "red running shoes",
                                    "fields": ["title^3", "description"],
                                    "fuzziness": "AUTO" } }],
      "filter": [{ "term": { "brand": "nike" } },
                 { "range": { "price": { "lte": 5000 } } },
                 { "term": { "inStock": true } }]
    }
  },
  "aggs": { "brands": { "terms": { "field": "brand" } } },
  "sort": ["_score", { "popularity": "desc" }],
  "size": 20
}
```

`must` affects scoring; `filter` doesn't score and is cached, so put exact constraints in filters. `aggs` produce facet counts (brand: Nike 120, Puma 80) for the sidebar filters.

## Keeping Elasticsearch in sync with MySQL

Elasticsearch is a **secondary index**, not the source of truth (no multi-document transactions, eventual consistency). Sync options:

1. **Dual write** from the application: write MySQL then ES. Simple but risks inconsistency if one fails; avoid for important data.
2. **Outbox/events**: service publishes `ProductUpdated` to Kafka; an indexer consumer updates ES. Reliable, decoupled.
3. **CDC**: Debezium reads the MySQL binlog → Kafka → Kafka Connect ES sink or a custom indexer. Captures every change, including those made outside the app.
4. **Batch reindex**: nightly full rebuild into a new index, then switch an **alias** atomically (zero-downtime reindex, also used for mapping changes).

Lag is usually under a few seconds. The UI should tolerate it (e.g., after creating a product, the admin's own view reads from MySQL).

## Scaling and performance tips

- Separate hot and warm data (time-based indices for logs with ILM rollover).
- Avoid deep pagination (`from + size` beyond 10,000); use `search_after` with a sort key.
- Use filters and `keyword` fields for exact matches; avoid leading wildcards and huge `terms` lists.
- Size heap ≤ 50% of RAM (and < ~31 GB) so the OS file cache can hold segments.
- Replicas improve read throughput; more primaries improve indexing parallelism.

## Other uses

- **Log analytics** (ELK/EFK stack: Elasticsearch, Logstash/Fluent Bit, Kibana).
- **Geo search** (`geo_point`, distance queries: restaurants within 5 km).
- **Autocomplete** (completion suggester, edge n-grams).
- **Vector search** (dense_vector, kNN) for semantic search and recommendations.

## Interview phrasing

"Product search uses Elasticsearch with an index sharded into 6 primaries with 1 replica each. Titles use an analyzer with lowercase, synonyms and stemming plus an edge n-gram subfield for typeahead; brand and category are keyword fields for filters and facets. MySQL is the source of truth; Debezium streams changes through Kafka to an indexer, with about a second of lag. Ranking is BM25 boosted by popularity and stock."
''',
["SQL LIKE '%x%' can't use indexes and has no relevance or typo tolerance",
 "Inverted index: term -> sorted postings list of documents (+ positions)",
 "Analyzers: tokenize, lowercase, stop words, stemming, synonyms, n-grams",
 "text fields for full-text; keyword fields for exact filter, sort, aggregations",
 "BM25 relevance: term frequency, inverse document frequency, field length",
 "ES: index -> primary shards + replicas; scatter-gather query; ~1s refresh (near real-time)",
 "ES is a secondary index; sync from MySQL via outbox/CDC (Debezium + Kafka)",
 "Use filters (cached, no scoring), search_after for deep paging, aliases for reindex"],
[("What is an inverted index?",
 "It maps each term to the list of documents containing it, usually with positions and frequencies, like a book's index. Text is analyzed into terms at index time; at query time the query is analyzed the same way, posting lists are fetched and intersected or unioned, and documents are scored. This makes full-text search fast over millions of documents, unlike scanning rows with LIKE."),
 ("How would you keep Elasticsearch in sync with MySQL?",
 "Treat MySQL as the source of truth and update Elasticsearch asynchronously. The most reliable approach is CDC: Debezium reads the MySQL binlog and publishes row changes to Kafka, and an indexer consumer upserts documents into Elasticsearch idempotently using the primary key as _id. Alternatively, use the transactional outbox. For mapping changes or recovery, do a full reindex into a new index and switch an alias atomically."),
 ("Explain shards and replicas in Elasticsearch.",
 "An index is split into a fixed number of primary shards, each a self-contained Lucene index distributed across nodes, enabling horizontal scaling of data and indexing. Each primary can have replicas on other nodes for fault tolerance and extra read capacity. A search fans out to one copy of every shard and the coordinating node merges results. Document routing uses a hash of the id modulo the number of primaries."),
 ("Why is Elasticsearch called near real-time?",
 "Indexed documents first go to an in-memory buffer and the translog. They become searchable only after a refresh, by default every second, which writes the buffer into a new immutable Lucene segment. So there's up to about a one-second delay between indexing and visibility. You can refresh explicitly or wait for refresh on a request, but frequent refreshes hurt indexing throughput."),
 ("How does relevance scoring work?",
 "Elasticsearch uses BM25 by default. A document scores higher when the query terms appear more often in it (with diminishing returns), when those terms are rare across the whole index (inverse document frequency), and when the matching field is shorter. On top, you can boost fields like title over description and combine text score with business signals such as popularity, rating or freshness using function_score.")],
[("Elasticsearch Guide", "https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html"), ("Elastic - How search works (inverted index)", "https://www.elastic.co/guide/en/elasticsearch/reference/current/documents-indices.html"), ("Debezium documentation", "https://debezium.io/documentation/"), ("Introduction to Information Retrieval (Manning et al.)", "https://nlp.stanford.edu/IR-book/")]))

topics.append(T("distributed-coordination", "Distributed Coordination: Leader Election, ZooKeeper and Distributed Locks", "Advanced",
"How multiple nodes agree on things: consensus (Raft), leader election, ZooKeeper/etcd, distributed locks with Redis and their pitfalls, and fencing tokens.",
r'''
## Why coordination is hard

On one machine, a `synchronized` block or a MySQL row lock makes one thread win. Across machines, there is no shared memory, messages can be delayed or lost, nodes pause (a 10-second GC pause looks like death), and clocks drift. Yet we often need nodes to **agree**:

- Which node is the **leader** (only one scheduler instance should run the nightly settlement job).
- Who holds a **lock** (only one worker processes this payment).
- What the **cluster membership and configuration** is (which Kafka broker leads partition 7, which shard lives where).

## Consensus: Raft and Paxos

Consensus algorithms let a group of nodes agree on a sequence of values even when some nodes fail, as long as a **majority (quorum)** is alive. With 5 nodes, it tolerates 2 failures; with 3, 1 failure. That's why coordination clusters have odd sizes (3 or 5).

**Raft** (easier to understand than Paxos):
1. Nodes are followers, candidates or a leader. Time is divided into **terms**.
2. If a follower hears no heartbeat within a randomized timeout (150-300 ms), it becomes a candidate, increments the term and requests votes. A node votes once per term. Majority → leader.
3. The leader receives all writes, appends them to its log and replicates to followers. An entry is **committed** once a majority has it; then it's applied to the state machine.
4. A network partition: the minority side can't elect a leader or commit writes (CP behaviour). An old leader in the minority can't commit anything because it lacks a majority.

Used by **etcd** (Kubernetes' brain), Consul, CockroachDB, TiKV, Kafka KRaft (replacing ZooKeeper). **ZooKeeper** uses ZAB, a Paxos-like protocol.

You won't implement Raft in an interview; you should explain why majorities guarantee a single leader and committed data.

## ZooKeeper and etcd

Both are small, strongly consistent, highly available key-value stores for **coordination metadata** (not application data; keep values small, a few KB).

ZooKeeper concepts:
- Hierarchical namespace of **znodes** (`/services/payment/instance-1`).
- **Ephemeral znodes**: deleted automatically when the client's session ends (crash or network loss). Perfect for liveness and locks.
- **Sequential znodes**: ZooKeeper appends a monotonically increasing counter (`lock-0000000042`).
- **Watches**: clients get notified when a znode changes.

etcd offers similar primitives: keys with **leases** (TTL kept alive by heartbeats), revisions, watches, and transactions (compare-and-swap).

Typical uses: leader election, service discovery, configuration, distributed locks, cluster membership (HBase, old Kafka, Hadoop, Kubernetes via etcd).

## Leader election recipes

**With ZooKeeper**: each candidate creates an ephemeral sequential znode under `/election`. The node with the smallest sequence number is the leader. Each other node watches the node just before it (avoids a herd of notifications). If the leader dies, its ephemeral znode vanishes and the next node becomes leader. Apache Curator's `LeaderLatch`/`LeaderSelector` implement this in Java.

**With etcd/Kubernetes**: candidates try to create a key with a lease (`PUT /leader nodeA` if not exists); the holder renews the lease; if it stops renewing, the key expires and someone else wins. Kubernetes `Lease` objects do this for controllers. Spring Integration offers leader election backed by ZooKeeper, etcd, Hazelcast or JDBC.

**With a database**: a `leader_lock` row updated with an expiry timestamp using conditional updates; ShedLock for Spring `@Scheduled` jobs works this way (MySQL, Redis or Mongo backed), ensuring a scheduled job runs on only one instance.

## Distributed locks

### Redis lock (simple)

```text
SET lock:order:991 <random-uuid> NX PX 30000     # acquire only if absent, 30 s expiry
... do work ...
# release only if we still own it (Lua script for atomic check-and-delete)
if redis.call("GET", KEYS[1]) == ARGV[1] then return redis.call("DEL", KEYS[1]) else return 0 end
```

- `NX` ensures only one acquirer; `PX` expiry prevents a crashed holder from locking forever.
- The random value prevents deleting someone else's lock after yours expired.
- In Java, **Redisson** provides `RLock` with automatic lease extension (watchdog).

**Redlock** acquires the lock on a majority of N independent Redis masters to survive one Redis failing. It's controversial: Martin Kleppmann showed it depends on timing assumptions (bounded clock drift and pauses) and lacks fencing.

### The fundamental problem: pauses and expiry

```text
Client A acquires lock (TTL 30 s) -> long GC pause 40 s -> lock expires
Client B acquires lock -> writes to storage
Client A wakes up, still thinks it holds the lock -> writes too  => corruption
```

No lock service can prevent A from waking up late. The fix is a **fencing token**: the lock service returns a monotonically increasing number with each grant (ZooKeeper's zxid or znode version, etcd revision). The **resource** (database, storage) rejects writes with a token lower than the highest it has seen.

```sql
UPDATE accounts SET balance = ?, fence = :token
WHERE id = ? AND fence < :token;
```

### Choosing a lock approach

| Need | Approach |
|---|---|
| Efficiency only (avoid duplicate work; occasional double execution harmless) | Redis `SET NX PX` / Redisson |
| Correctness (double execution corrupts data) | ZooKeeper/etcd lock + fencing tokens, or rely on DB constraints/transactions |
| Data already in one DB | Use the DB itself: `SELECT ... FOR UPDATE`, conditional updates, unique constraints |
| One instance runs a scheduled job | ShedLock or leader election |

Senior insight: **the best distributed lock is often no lock**: design idempotent operations, conditional writes (compare-and-set with version numbers), unique constraints, or partition work so each key is owned by one consumer (Kafka partitions give you single-threaded processing per key without locks).

## Other coordination concepts

- **Heartbeats and failure detection**: timeouts are a trade-off between fast detection and false positives; phi-accrual detectors adapt to network conditions (Cassandra, Akka).
- **Gossip protocols**: nodes periodically exchange state with random peers; membership spreads epidemically (Cassandra, Consul's Serf, Redis Cluster). Scales well, eventually consistent.
- **Leases**: time-bound ownership; the basis of leader election and locks.
- **Split brain prevention**: quorum + fencing.
- **Clocks**: physical clocks drift; ordering uses logical clocks (Lamport timestamps, vector clocks) or hybrid logical clocks; Google Spanner uses TrueTime with bounded uncertainty.

## Interview phrasing

"For the nightly payout job across 6 instances, I'll use leader election via a Kubernetes Lease (or ShedLock on MySQL) so only one runs. For processing a specific order, I avoid locks by partitioning Kafka by orderId so one consumer owns each order, and make writes conditional on a version column. If a lock is truly needed for correctness, I'd use etcd with a lease and pass its revision as a fencing token to the storage layer."
''',
["Coordination = agreeing on leader, locks, membership despite failures and pauses",
 "Consensus (Raft, ZAB, Paxos) needs a majority; clusters of 3 or 5 nodes",
 "Raft: terms, randomized election timeouts, leader replicates log, commit on majority",
 "ZooKeeper: ephemeral + sequential znodes and watches; etcd: leases, revisions, watches",
 "Leader election: smallest sequential znode, lease-based keys, ShedLock for scheduled jobs",
 "Redis lock: SET key uuid NX PX ttl; release with atomic check-and-delete",
 "Lock expiry + process pause breaks locks; fencing tokens protect the resource",
 "Prefer no lock: idempotency, conditional writes, partition ownership"],
[("How does leader election work with ZooKeeper?",
 "Each candidate creates an ephemeral sequential znode under an election path. The one with the lowest sequence number is the leader. Every other candidate watches the znode immediately before its own. If the leader crashes or loses its session, its ephemeral node is deleted and the next candidate is notified and becomes leader. Watching only the predecessor avoids a herd effect. Apache Curator provides LeaderLatch for this."),
 ("How do you implement a distributed lock with Redis and what are the pitfalls?",
 "Acquire with SET lock-key random-value NX PX ttl so only one client succeeds and the lock auto-expires if the holder crashes. Release with a Lua script that deletes the key only if the value matches, so you don't release someone else's lock. Pitfalls: if the holder pauses longer than the TTL, another client acquires it and both proceed; Redis failover with async replication can lose the lock. For correctness, add fencing tokens or use a consensus-based store."),
 ("What is a fencing token?",
 "A monotonically increasing number issued by the lock service each time the lock is granted. The client sends it with every write to the protected resource, and the resource rejects any write with a token lower than the highest it has already seen. So if a paused client with an expired lock wakes up and tries to write with an old token, the write is rejected, preventing corruption that expiry-based locks alone cannot."),
 ("Why do consensus clusters use an odd number of nodes?",
 "Consensus needs a majority to elect a leader and commit writes. A 3-node cluster needs 2 and tolerates 1 failure; a 4-node cluster needs 3 and still tolerates only 1 failure, so the extra node adds cost and network overhead without improving fault tolerance. 5 nodes tolerate 2 failures. Odd sizes also avoid tie situations when the network splits evenly."),
 ("How would you ensure a scheduled job runs on only one of many Spring Boot instances?",
 "Use ShedLock: annotate the @Scheduled method with @SchedulerLock; before running, each instance tries to insert or update a row in a shared lock table (MySQL) or a Redis key with a lockAtMostFor expiry. Only one succeeds. Alternatively, use leader election through a Kubernetes Lease, ZooKeeper via Spring Integration, or move the job to a dedicated scheduler. The job itself should be idempotent in case it runs twice.")],
[("Raft consensus algorithm (visualisation and paper)", "https://raft.github.io/"), ("Apache ZooKeeper - Recipes", "https://zookeeper.apache.org/doc/current/recipes.html"), ("Martin Kleppmann - How to do distributed locking", "https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html"), ("Redis - Distributed locks", "https://redis.io/docs/latest/develop/use/patterns/distributed-locks/"), ("etcd documentation", "https://etcd.io/docs/"), DDIA]))

dump("sd_part4.json", topics)
