from cs_common import build, B, I, A

notes = [
("OSI and TCP/IP Models", r"""
Network models split communication into **layers**, each providing services to the layer above and using the one below. This makes protocols modular and replaceable.

### OSI model (7 layers) — "Please Do Not Throw Sausage Pizza Away" (bottom-up)
| # | Layer | Responsibility | PDU | Examples / devices |
|---|---|---|---|---|
| 7 | **Application** | Network services to apps | Data | HTTP, FTP, SMTP, DNS, SSH |
| 6 | **Presentation** | Encoding, encryption, compression | Data | TLS (often placed here), JSON/XML, JPEG |
| 5 | **Session** | Establish/maintain/terminate sessions | Data | RPC, NetBIOS, session checkpoints |
| 4 | **Transport** | Process-to-process delivery, ports, reliability, flow control | Segment (TCP) / Datagram (UDP) | TCP, UDP, QUIC |
| 3 | **Network** | Logical addressing, routing between networks | Packet | IP, ICMP, routers |
| 2 | **Data Link** | Node-to-node delivery on the same link, MAC addressing, error detection (CRC) | Frame | Ethernet, Wi-Fi (802.11), ARP*, switches |
| 1 | **Physical** | Bits over the medium | Bits | Cables, fibre, radio, hubs, repeaters |

*ARP sits between L2 and L3.

### TCP/IP model (4 layers — what the internet actually uses)
| TCP/IP layer | Maps to OSI | Protocols |
|---|---|---|
| Application | 5, 6, 7 | HTTP, DNS, TLS, SMTP |
| Transport | 4 | TCP, UDP |
| Internet | 3 | IP, ICMP |
| Network Access / Link | 1, 2 | Ethernet, Wi-Fi |

(Some books use a 5-layer hybrid: Application, Transport, Network, Data Link, Physical.)

### OSI vs TCP/IP
- OSI is a **conceptual reference model** (designed before protocols); TCP/IP is a **practical model** built around existing protocols.
- OSI separates session and presentation; TCP/IP folds them into application.
- OSI clearly distinguishes services, interfaces and protocols.

### Encapsulation
As data goes down the stack each layer adds its header:
```
HTTP data
→ [TCP header | data]                          (segment: src/dst port, seq, ack)
→ [IP header | TCP header | data]               (packet: src/dst IP, TTL)
→ [Eth header | IP | TCP | data | Eth trailer]  (frame: src/dst MAC, CRC)
→ bits on the wire
```
The receiver **decapsulates** in reverse.

### Devices by layer
- **Hub** (L1) – repeats bits to all ports; one collision domain.
- **Switch** (L2) – forwards frames using a MAC address table; each port its own collision domain. L3 switches also route.
- **Router** (L3) – forwards packets between networks using IP routing tables; separates broadcast domains.
- **Load balancer / proxy / firewall** – L4 (ports/IP) or L7 (HTTP paths, headers).
- **Gateway** – translates between different protocols/networks.

### Addressing per layer
- Port number (L4) identifies the **process** (e.g. 443 HTTPS, 8080 Spring Boot, 3306 MySQL).
- IP address (L3) identifies the **host** across networks.
- MAC address (L2) identifies the **network interface** on the local link (48-bit, e.g. `3C:52:82:1A:9F:00`).

**ARP** maps IP → MAC on the local network: "Who has 192.168.1.1? Tell 192.168.1.20." The reply is cached in the ARP table.

### Interview framing
When asked "at which layer does X work?", answer with the layer **and** what that layer's job is — e.g. "An L7 load balancer like Nginx/ALB can route `/api/orders` to the order service because it understands HTTP; an L4 load balancer only sees IPs and ports."
"""),

("TCP vs UDP, Three-Way Handshake & Reliability", r"""
### TCP (Transmission Control Protocol)
**Connection-oriented, reliable, ordered byte stream.**
- **Three-way handshake** to set up, four-step teardown.
- **Sequence numbers & acknowledgements** – every byte numbered; receiver ACKs; lost segments retransmitted after a timeout or 3 duplicate ACKs (fast retransmit).
- **Ordering** – out-of-order segments reassembled.
- **Flow control** – receiver advertises a **window** (rwnd); sender never overwhelms the receiver (sliding window).
- **Congestion control** – sender adapts to network capacity: **slow start** (cwnd doubles each RTT), **congestion avoidance** (additive increase), **multiplicative decrease** on loss (AIMD); algorithms: Reno, CUBIC (Linux default), BBR (Google).
- **Error detection** – checksum.
- Header ≥ 20 bytes.

### UDP (User Datagram Protocol)
**Connectionless, unreliable, message-oriented.** No handshake, no ACKs, no ordering, no flow/congestion control. 8-byte header (src port, dst port, length, checksum). Fast and lightweight; apps add reliability if needed.

| | TCP | UDP |
|---|---|---|
| Connection | Yes (handshake) | No |
| Reliability | Guaranteed delivery, retransmits | Best-effort |
| Order | Preserved | Not guaranteed |
| Speed / overhead | Slower, 20+ B header | Faster, 8 B header |
| Data unit | Byte stream | Datagrams (message boundaries kept) |
| Broadcast/multicast | No | Yes |
| Use cases | HTTP/1.1 & 2, HTTPS, SSH, SMTP, DB connections (MySQL 3306) | DNS queries, video calls, live streaming, online games, VoIP, DHCP, **QUIC/HTTP3** |

### Three-way handshake
```
Client                           Server (LISTEN)
  | ---- SYN, seq=x ------------> |
  | <--- SYN-ACK, seq=y, ack=x+1 -|
  | ---- ACK, ack=y+1 ----------> |   ESTABLISHED
```
Why three and not two? Both sides must **choose and confirm initial sequence numbers** (ISNs, randomised for security). Two steps would let the server think a connection exists from an old duplicate SYN, and the client's ISN acknowledgement would be missing.

### Connection termination (four-way)
```
Client: FIN →         (client done sending)
Server: ← ACK
Server: ← FIN         (server done sending)
Client: ACK →         client enters TIME_WAIT (2×MSL) then CLOSED
```
**TIME_WAIT** ensures the final ACK can be retransmitted if lost and old duplicate segments die out. Many short connections → lots of TIME_WAIT sockets → why we use **connection pooling / keep-alive** (HikariCP for DB, HTTP keep-alive).

### SYN flood attack
Attacker sends many SYNs without completing the handshake, filling the server's half-open queue. Mitigation: **SYN cookies**, rate limiting, firewalls.

### Other transport concepts
- **Ports:** 0–1023 well-known (22 SSH, 25 SMTP, 53 DNS, 80 HTTP, 443 HTTPS), 1024–49151 registered (3306 MySQL, 5432 Postgres, 6379 Redis, 8080), 49152–65535 ephemeral (client side).
- A connection is identified by the 5-tuple: (protocol, src IP, src port, dst IP, dst port).
- **Nagle's algorithm** batches small writes (disable with `TCP_NODELAY` for latency-sensitive apps).
- **Head-of-line blocking** in TCP: one lost segment stalls all later data in the stream — the motivation for QUIC.

### Stop-and-wait vs sliding window
Stop-and-wait sends one packet and waits for its ACK (poor utilisation). Sliding window allows N unacknowledged packets in flight. Retransmission strategies: **Go-Back-N** (resend from the lost one) and **Selective Repeat** (resend only lost ones).
"""),

("HTTP: Methods, Status Codes, HTTP/1.1 vs HTTP/2 vs HTTP/3", r"""
**HTTP** is a stateless, request–response, application-layer protocol.

### Request anatomy
```
POST /api/orders HTTP/1.1
Host: shop.example.com
Content-Type: application/json
Authorization: Bearer eyJ...
Cookie: SESSION=abc123

{"productId": 42, "qty": 2}
```
Response: status line (`HTTP/1.1 201 Created`), headers (`Location`, `Set-Cookie`, `Cache-Control`), body.

### Methods
| Method | Purpose | Safe | Idempotent |
|---|---|---|---|
| GET | Read | Yes | Yes |
| HEAD | Headers only | Yes | Yes |
| POST | Create / action | No | **No** |
| PUT | Replace whole resource | No | Yes |
| PATCH | Partial update | No | Not guaranteed |
| DELETE | Delete | No | Yes |
| OPTIONS | Capabilities, **CORS preflight** | Yes | Yes |

**Idempotent** = repeating the request has the same effect as doing it once — important for retries (use an `Idempotency-Key` header for payment POSTs).

### Status codes
- **1xx** informational (101 Switching Protocols – WebSocket upgrade).
- **2xx** success: 200 OK, 201 Created, 202 Accepted, 204 No Content.
- **3xx** redirection: 301 Moved Permanently, 302 Found, 304 Not Modified (cache), 307/308 (keep method).
- **4xx** client error: 400 Bad Request, **401 Unauthorized (not authenticated)**, **403 Forbidden (authenticated but not allowed)**, 404 Not Found, 405 Method Not Allowed, 409 Conflict, 415 Unsupported Media Type, 422 Unprocessable, 429 Too Many Requests.
- **5xx** server error: 500 Internal, 502 Bad Gateway (upstream invalid response), 503 Service Unavailable, 504 Gateway Timeout.

### Caching headers
`Cache-Control: max-age=3600, public | no-cache | no-store`, `ETag` + `If-None-Match` → 304, `Last-Modified` + `If-Modified-Since`. Angular build output uses hashed filenames so it can be cached for a year.

### HTTP/1.0 → 1.1
- 1.0: new TCP connection per request.
- **1.1 (1997)**: persistent connections (**keep-alive** by default), `Host` header (virtual hosting), chunked transfer encoding, pipelining (rarely used due to **head-of-line blocking**). Browsers open ~6 parallel connections per host as a workaround. Text-based headers repeated on every request.

### HTTP/2 (2015)
- **Binary framing** instead of text.
- **Multiplexing**: many concurrent **streams** over **one TCP connection** — no need for domain sharding or sprite hacks.
- **Header compression (HPACK)**.
- **Stream prioritisation**.
- Server push (deprecated in browsers now).
- Practically requires TLS in browsers.
- Still suffers **TCP-level head-of-line blocking**: one lost packet stalls all streams.

### HTTP/3 (2022, RFC 9114)
- Runs over **QUIC**, which runs over **UDP**.
- QUIC implements reliability, congestion control and **TLS 1.3 built in** in user space.
- **Independent streams** — loss on one stream doesn't block others (no TCP HOL blocking).
- **Faster setup**: 1-RTT handshake (transport + TLS combined), **0-RTT** resumption.
- **Connection migration** via connection IDs — switching Wi-Fi to 4G keeps the connection (great for mobile users in India).
- Header compression: QPACK.

| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| Transport | TCP | TCP | QUIC over UDP |
| Format | Text | Binary | Binary |
| Multiplexing | No | Yes | Yes |
| HOL blocking | HTTP + TCP level | TCP level | None (per stream) |
| Header compression | No | HPACK | QPACK |
| Handshake (with TLS 1.3) | TCP 1 RTT + TLS 1 RTT | same | 1 RTT (0-RTT resume) |

### REST quick notes
Stateless, resource-based URLs (`/users/42/orders`), HTTP verbs for actions, proper status codes, versioning (`/v1/`), pagination (`?page=0&size=20`). HTTP being stateless is why we need cookies, sessions or tokens for login state.
"""),

("HTTPS, TLS Handshake & Certificates", r"""
**HTTPS = HTTP over TLS.** TLS (Transport Layer Security; SSL is its deprecated predecessor) provides:
1. **Confidentiality** – encryption, so eavesdroppers on public Wi-Fi can't read traffic.
2. **Integrity** – tampering is detected (AEAD ciphers / MACs).
3. **Authentication** – the server proves its identity with a **certificate**.

Default port 443. Current versions: **TLS 1.2** and **TLS 1.3** (1.0/1.1 deprecated).

### Symmetric vs asymmetric encryption
- **Asymmetric** (RSA, ECDSA, ECDH): public/private key pair; slow; used for **key exchange and authentication**.
- **Symmetric** (AES-GCM, ChaCha20): one shared key; fast; used for **bulk data**.
TLS uses asymmetric crypto to agree on a symmetric **session key**, then encrypts data symmetrically — the best of both.

### TLS 1.2 handshake (2 RTT)
1. **ClientHello** – supported versions, cipher suites, random number.
2. **ServerHello** – chosen cipher, server random; **Certificate**; key exchange params (ECDHE); ServerHelloDone.
3. Client **verifies certificate**, sends its key share (ClientKeyExchange); both derive the **pre-master → master secret → session keys**.
4. ChangeCipherSpec + Finished messages (both sides) – encrypted from now on.

### TLS 1.3 handshake (1 RTT, 0-RTT on resumption)
1. **ClientHello** + **key share** (client guesses the ECDHE group upfront).
2. **ServerHello** + key share + encrypted certificate + Finished.
3. Client Finished → application data.
Improvements: one fewer round trip, removed insecure algorithms (RSA key exchange, SHA-1, CBC), mandatory **forward secrecy** (ephemeral Diffie-Hellman: stealing the server's private key later can't decrypt past sessions), encrypts more of the handshake.

### Certificates & chain of trust
A certificate (X.509) contains the domain name (CN/SAN), the server's **public key**, issuer, validity period and the issuer's **digital signature**.
- Issued by a **Certificate Authority (CA)** (Let's Encrypt, DigiCert).
- Browser/OS ships a **trust store of root CAs**. Server sends its leaf certificate + intermediates; browser verifies each signature up to a trusted root, checks domain match, expiry, and revocation (OCSP/CRL).
- Self-signed certificates aren't trusted by default (fine for local dev).

### Digital signature vs encryption
- Encrypt with **recipient's public key** → only private-key holder decrypts (confidentiality).
- Sign with **sender's private key** (hash then sign) → anyone verifies with public key (authenticity + integrity).

### Hashing vs encryption vs encoding
- **Hashing** – one-way (SHA-256); passwords stored with slow salted hashes (**bcrypt**, Argon2) — Spring Security's `BCryptPasswordEncoder`.
- **Encryption** – reversible with a key.
- **Encoding** – reversible without a key (Base64) — not security. JWT payloads are Base64URL encoded, **not encrypted**.

### Related concepts
- **HSTS** header forces browsers to use HTTPS for a domain (prevents SSL-stripping).
- **Mutual TLS (mTLS)** – client also presents a certificate; common in service-to-service auth (service meshes, banking APIs).
- **TLS termination** at a load balancer/Nginx/API gateway; internal traffic may be plain HTTP or re-encrypted.
- **SNI** (Server Name Indication) – client sends hostname in ClientHello so one IP can serve many HTTPS sites.
- **Man-in-the-middle attack** – prevented by certificate validation; corporate proxies install their own root CA to inspect traffic.

### Java/Spring angle
Configure HTTPS in Spring Boot with `server.ssl.key-store` (PKCS12), or more commonly terminate TLS at Nginx/ALB. `PKIX path building failed` errors in Java mean the JVM truststore doesn't trust the server's CA — add it with `keytool`.
"""),

("DNS & What Happens When You Type a URL", r"""
### DNS (Domain Name System)
DNS translates human-readable names (`www.flipkart.com`) to IP addresses. It is a **distributed, hierarchical database**, mostly over **UDP port 53** (TCP for large responses and zone transfers; DNS-over-HTTPS/TLS for privacy).

**Hierarchy:** root (`.`) → TLD (`.com`, `.in`) → authoritative servers for `flipkart.com`.

**Resolution steps:**
1. Browser cache → OS cache (`/etc/hosts`, stub resolver) → router.
2. Query the **recursive resolver** (ISP, 8.8.8.8, 1.1.1.1).
3. Resolver asks a **root server** → referral to `.com` TLD servers.
4. Asks **TLD server** → referral to `flipkart.com`'s **authoritative nameservers**.
5. Asks authoritative server → gets the A/AAAA record.
6. Resolver caches it for the **TTL** and returns it.

Client → resolver is a **recursive** query; resolver → root/TLD/authoritative are **iterative** queries.

**Record types:**
| Record | Purpose |
|---|---|
| A / AAAA | Name → IPv4 / IPv6 |
| CNAME | Alias to another name (`www` → `app.cdn.net`) |
| MX | Mail servers |
| NS | Authoritative nameservers for the zone |
| TXT | Arbitrary text (SPF, domain verification) |
| SOA | Zone metadata |
| PTR | Reverse lookup (IP → name) |
| SRV | Service location (host + port) |

DNS is also used for **load balancing** (multiple A records, GeoDNS, latency-based routing in Route 53) and failover. Low TTLs allow faster changes but more queries.

### What happens when you type `https://www.amazon.in` and press Enter (the classic)
1. **URL parsing** – browser identifies scheme (https), host, path; checks **HSTS** list (forces HTTPS); may autocomplete from history.
2. **DNS lookup** – caches, then recursive resolution as above → IP address (often a CDN edge).
3. **TCP connection** – 3-way handshake with the server's IP on port 443 (or QUIC over UDP for HTTP/3).
4. **TLS handshake** – negotiate version/ciphers, verify certificate, derive session keys (1 RTT with TLS 1.3).
5. **HTTP request** – `GET / HTTP/2` with headers: `Host`, `User-Agent`, `Accept`, cookies.
6. **Server side** – request hits a **CDN**/**load balancer** → reverse proxy (Nginx) → application server (e.g. Spring Boot on Tomcat) → may call caches (Redis), databases (MySQL), other microservices → builds response.
7. **HTTP response** – status (200/301/304), headers (`Content-Type`, `Cache-Control`, `Set-Cookie`), body (HTML), possibly compressed (gzip/brotli).
8. **Browser rendering** –
   - Parse HTML → **DOM**; parse CSS → **CSSOM**.
   - Discover sub-resources (CSS, JS, images, fonts) → more requests (reusing the HTTP/2 connection).
   - JS execution (blocking scripts pause parsing unless `defer`/`async`).
   - DOM + CSSOM → **render tree** → **layout** (positions/sizes) → **paint** → **composite** layers.
   - For an Angular SPA: `index.html` loads `main.js`, Angular bootstraps, router renders components, which call APIs via XHR/fetch.
9. **Connection reuse** – keep-alive keeps the connection open for further requests.

Lower layers along the way: ARP to find the gateway's MAC, routing across ISPs via routers using BGP, NAT at your home router translating your private IP.

### How to answer
Go layer by layer, keep it structured, then **go deep where the interviewer probes** (DNS caching, TLS, load balancing, or browser rendering). For a full-stack role, adding the server-side journey (LB → Spring Boot → DB) is a strong differentiator.
"""),

("Cookies, Sessions, Tokens & CORS", r"""
HTTP is **stateless**, so apps need a way to remember who the user is.

### Cookies
Small key-value data the server sets via `Set-Cookie`; the browser automatically sends matching cookies back in the `Cookie` header.
```
Set-Cookie: SESSION=8f2a...; Path=/; Max-Age=1800; HttpOnly; Secure; SameSite=Lax; Domain=example.com
```
Attributes:
- `Expires`/`Max-Age` – persistent; without them it's a **session cookie** (deleted when browser closes).
- `HttpOnly` – not accessible from JavaScript → protects against XSS stealing it.
- `Secure` – only sent over HTTPS.
- `SameSite=Strict | Lax | None` – controls cross-site sending; key **CSRF** defence. `None` requires `Secure`. Browsers default to `Lax`.
- `Domain`, `Path` – scope.
Limits: ~4 KB per cookie.

**Browser storage comparison:** cookies (sent with every request, 4 KB), `localStorage` (5–10 MB, persists, JS-accessible, never sent automatically), `sessionStorage` (per tab, cleared on close).

### Sessions (stateful)
1. User logs in; server creates a session record (user id, roles) in memory/Redis and returns a random **session ID** in a cookie (`JSESSIONID` in Java).
2. Each request carries the cookie; server looks up the session.
- ✅ Easy revocation (delete session), small cookie.
- ❌ Server state; with multiple instances you need **sticky sessions** or a shared store (**Spring Session + Redis**).

### Tokens (stateless) — JWT
A **JWT** = `header.payload.signature` (Base64URL). The payload holds claims (`sub`, `roles`, `exp`). Server signs with a secret (HS256) or private key (RS256); any service can verify without a DB lookup.
- ✅ Stateless, scales horizontally, works across services and mobile clients.
- ❌ Hard to revoke before expiry → short-lived **access tokens** (5–15 min) + **refresh tokens** (stored HttpOnly cookie, rotated, revocable). Payload is readable — never put secrets in it.
Sent usually as `Authorization: Bearer <token>`.

**OAuth 2.0** is an authorization framework (delegated access, "Login with Google" via OpenID Connect on top). Authorization Code + PKCE is the recommended flow for SPAs.

### CSRF vs XSS
- **XSS** – attacker injects script into your page; it can read localStorage tokens/non-HttpOnly cookies. Defences: output encoding (Angular does it), CSP, HttpOnly cookies.
- **CSRF** – attacker's site makes the victim's browser send a request to your site with the victim's cookies. Defences: `SameSite` cookies, CSRF tokens (Spring Security), checking `Origin`. Bearer tokens in headers aren't sent automatically, so they're not CSRF-prone (but are XSS-prone if stored in JS-accessible storage).

### Same-Origin Policy & CORS
**Origin** = scheme + host + port. `http://localhost:4200` and `http://localhost:8080` are **different origins**. The browser's **Same-Origin Policy** blocks JS from reading responses from other origins.

**CORS (Cross-Origin Resource Sharing)** lets a server opt in by sending headers:
```
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 3600
```
- **Simple requests** (GET/HEAD/POST with simple headers and form content types) are sent directly; the browser checks the response header.
- **Preflighted requests** – for PUT/DELETE, JSON `Content-Type`, or custom headers like `Authorization`, the browser first sends an **OPTIONS** request; the actual request proceeds only if allowed.
- With credentials (cookies), `Allow-Origin` can't be `*`.
- CORS is enforced **by the browser**; Postman/curl ignore it. It is not a server security mechanism against non-browser clients.

**Spring Boot fix:**
```java
@Bean
CorsConfigurationSource corsConfigurationSource() {
  var c = new CorsConfiguration();
  c.setAllowedOrigins(List.of("https://app.example.com"));
  c.setAllowedMethods(List.of("GET","POST","PUT","DELETE","OPTIONS"));
  c.setAllowedHeaders(List.of("*"));
  c.setAllowCredentials(true);
  var s = new UrlBasedCorsConfigurationSource();
  s.registerCorsConfiguration("/**", c);
  return s;
}
```
plus `http.cors(Customizer.withDefaults())` in Spring Security. In local Angular development you can avoid CORS entirely with `proxy.conf.json`.
"""),

("Real-Time Communication: Polling, SSE, WebSockets", r"""
HTTP is client-initiated: the server can't push data on its own. For notifications, chats, live dashboards, stock tickers or delivery tracking we need other techniques.

### 1. Short polling
Client calls `GET /notifications` every N seconds.
- ✅ Simple, works everywhere.
- ❌ Wasteful (most responses empty), latency up to N seconds, load on server.

### 2. Long polling
Client sends a request; the server **holds it open** until new data arrives or a timeout (e.g. 30 s), then responds; client immediately re-requests.
- ✅ Near real-time, uses plain HTTP.
- ❌ Server holds many open connections; reconnect overhead per message; ordering complexities.

### 3. Server-Sent Events (SSE)
A long-lived HTTP response with `Content-Type: text/event-stream`; the server streams events **one-way (server → client)**.
```js
const es = new EventSource('/api/orders/stream');
es.onmessage = e => console.log(JSON.parse(e.data));
```
```java
@GetMapping(value = "/orders/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<OrderEvent> stream() { return orderEvents.asFlux(); }   // or SseEmitter in Spring MVC
```
- ✅ Simple, auto-reconnect with `Last-Event-ID`, works over HTTP/2, text-based. Great for notifications, live feeds, **LLM token streaming**.
- ❌ One-direction only; text only.

### 4. WebSockets
A **full-duplex, persistent** connection over a single TCP connection. Starts as an HTTP request that is **upgraded**:
```
GET /chat HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```
After that, both sides send lightweight **frames** (text/binary) anytime. URLs use `ws://` or `wss://` (TLS).
- ✅ Lowest latency, bidirectional, low per-message overhead. Chats, multiplayer games, collaborative editing, trading.
- ❌ Stateful connections make **horizontal scaling** harder (need sticky sessions or a pub/sub backplane like Redis/Kafka to broadcast across instances); proxies/firewalls/load balancers must support upgrades and idle timeouts; must implement heartbeats (ping/pong) and reconnection yourself.

Spring: `spring-boot-starter-websocket` with **STOMP** over WebSocket (`@MessageMapping`, `SimpMessagingTemplate.convertAndSend("/topic/orders", ...)`), SockJS fallback. Angular: `rxjs/webSocket` or `@stomp/rx-stomp`.

### 5. WebRTC
Peer-to-peer audio/video/data between browsers (UDP-based), with signalling via a server and STUN/TURN for NAT traversal. Used by video calling apps.

### 6. Webhooks
Server-to-server push: provider makes an HTTP POST to your URL when an event occurs (Razorpay payment captured, GitHub push). Must verify signatures and be idempotent.

### Choosing
| Need | Choose |
|---|---|
| Occasional updates, simple | Polling |
| Server → client stream (notifications, feeds) | SSE |
| Bidirectional, low latency (chat, games) | WebSockets |
| Audio/video peer-to-peer | WebRTC |
| Third-party event notification to your backend | Webhooks |

A great system-design talking point: "For order-status updates I'd use SSE because data flows only server → client, it works over HTTP/2 and through our existing load balancer; I'd switch to WebSockets only if the client also needs to push frequent messages."
"""),

("IP Addressing, Subnetting, NAT, DHCP & ICMP", r"""
### IPv4
A 32-bit address written as four octets: `192.168.10.25`. ~4.3 billion addresses — exhausted, hence NAT and IPv6.

**Classful addressing (historical):**
| Class | First octet | Default mask | Use |
|---|---|---|---|
| A | 1–126 | /8 (255.0.0.0) | Huge networks |
| B | 128–191 | /16 | Medium |
| C | 192–223 | /24 | Small |
| D | 224–239 | – | Multicast |
| E | 240–255 | – | Experimental |
(127.x.x.x is loopback; `127.0.0.1` = localhost.)

**Private ranges (RFC 1918)** – not routable on the internet: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.

### CIDR & subnet masks
**CIDR** notation `/n` = first n bits are the **network** part; the rest are the **host** part. Replaced rigid classes.

For a `/n` network:
- Total addresses = 2^(32−n)
- Usable hosts = 2^(32−n) − 2 (network address and broadcast address reserved)

**Example:** `192.168.1.0/26`
- Mask: 255.255.255.192 (26 ones).
- Block size = 2^6 = 64 → subnets: .0, .64, .128, .192.
- First subnet: network `192.168.1.0`, hosts `.1–.62`, broadcast `.63` → **62 usable hosts**.

**Which subnet is 10.0.5.77/27 in?** Block size 32 in the last octet → 64–95 range → network `10.0.5.64`, broadcast `10.0.5.95`, hosts `.65–.94`.

**Subnetting question:** split `192.168.1.0/24` into 4 equal subnets → borrow 2 bits → `/26`, each with 62 hosts.

**Why subnet?** Smaller broadcast domains, security segmentation (public vs private subnets in an AWS VPC: load balancer in public, Spring Boot and MySQL in private), efficient address use.

Hosts in the same subnet communicate directly (ARP for MAC); otherwise packets go to the **default gateway** (router). A host decides by ANDing destination IP with its subnet mask.

### IPv6
128-bit addresses in hex: `2001:0db8:85a3::8a2e:0370:7334` (`::` compresses zeros). Huge space (no NAT needed), simplified header, built-in autoconfiguration (SLAAC), mandatory IPsec support in the spec, no broadcast (uses multicast). India has one of the highest IPv6 adoption rates thanks to mobile carriers.

### NAT (Network Address Translation)
A router translates private IPs to its public IP. **PAT/NAT overload** maps many private (IP, port) pairs to one public IP with different ports. Saves IPv4 addresses, hides internal structure, but breaks end-to-end connectivity (incoming connections need port forwarding; P2P apps need STUN/TURN).

### DHCP
Automatically assigns IP address, subnet mask, gateway and DNS servers to hosts. **DORA**: **D**iscover (broadcast) → **O**ffer → **R**equest → **A**cknowledge. Uses UDP ports 67/68. Leases expire and renew.

### ICMP
Network-layer protocol for diagnostics and errors: `ping` (Echo Request/Reply), `traceroute` (uses increasing **TTL**; each router that decrements TTL to 0 returns "Time Exceeded"), "Destination Unreachable". TTL prevents packets from looping forever.

### Routing basics
Routers forward packets using **routing tables** (longest prefix match). Protocols: **RIP** (distance vector, hop count), **OSPF** (link state, Dijkstra, within an organisation), **BGP** (path vector, between autonomous systems — the internet's routing protocol).

### Unicast, broadcast, multicast, anycast
- Unicast: one-to-one.
- Broadcast: one-to-all in a subnet (ARP request, DHCP discover).
- Multicast: one-to-group (IPTV).
- Anycast: one-to-nearest of many sharing an IP (Cloudflare's 1.1.1.1, root DNS servers, CDNs).

### Handy commands
`ping`, `traceroute`/`tracert`, `nslookup`/`dig`, `netstat`/`ss -tulpn` (open ports — find what's using 8080), `curl -v` (see TLS and headers), `ipconfig`/`ip addr`.
"""),
]

qa = [
("Explain the OSI model and the function of each layer.", r"""
The OSI model is a 7-layer conceptual model for network communication:

1. **Physical** – transmits raw bits over the medium (cables, radio). Devices: hubs, repeaters.
2. **Data Link** – node-to-node delivery within a network, framing, **MAC addresses**, error detection (CRC). Devices: switches. Protocols: Ethernet, Wi-Fi.
3. **Network** – logical addressing (**IP**) and **routing** across networks. Devices: routers. Protocols: IP, ICMP.
4. **Transport** – end-to-end process communication using **ports**; reliability, flow and congestion control. TCP, UDP.
5. **Session** – sets up, manages and terminates sessions between applications.
6. **Presentation** – data translation, encryption, compression (TLS, JSON, JPEG).
7. **Application** – network services to user apps (HTTP, DNS, SMTP, FTP).

Mnemonic (bottom-up): *Please Do Not Throw Sausage Pizza Away*. The internet actually uses the 4-layer TCP/IP model, which merges layers 5–7 into Application and 1–2 into Link.
""", B, ["osi"], True),

("What is the difference between the OSI and TCP/IP models?", r"""
| OSI | TCP/IP |
|---|---|
| 7 layers | 4 layers (Application, Transport, Internet, Link) |
| Conceptual reference model, created before protocols | Practical model based on protocols already in use |
| Separate Session and Presentation layers | Merged into Application |
| Separate Physical and Data Link | Combined into Network Access/Link |
| Clear distinction between services, interfaces, protocols | Less strict |
| Transport layer guarantees delivery (connection-oriented focus) | Transport offers both TCP (reliable) and UDP (unreliable) |

OSI is used for teaching and troubleshooting vocabulary ("it's a Layer 7 issue"), while TCP/IP is what real networks implement.
""", B, ["osi", "tcp-ip"], False),

("What is the difference between TCP and UDP? When would you use each?", r"""
| TCP | UDP |
|---|---|
| Connection-oriented (3-way handshake) | Connectionless |
| Reliable: ACKs, retransmissions | Best-effort, no guarantee |
| Ordered delivery | No ordering |
| Flow & congestion control | None |
| Heavier (20+ byte header) | Light (8-byte header) |
| Byte stream | Message/datagram based, supports broadcast/multicast |

**Use TCP** when correctness matters more than latency: web (HTTP/1.1, HTTP/2), REST APIs, database connections, file transfer, email, SSH.

**Use UDP** when low latency matters and occasional loss is acceptable or handled by the app: DNS queries, live video/voice calls, online games, streaming, DHCP, and **QUIC (HTTP/3)**, which builds its own reliability on top of UDP.
""", B, ["tcp", "udp"], True),

("Explain the TCP three-way handshake. Why is it three-way and not two-way?", r"""
1. **SYN** – client sends a segment with SYN flag and its initial sequence number `x`.
2. **SYN-ACK** – server replies with SYN + ACK, its own ISN `y`, and `ack = x + 1`.
3. **ACK** – client sends `ack = y + 1`. Both are now ESTABLISHED and data can flow (the third packet can carry data).

**Why three?** Both sides must **agree on each other's initial sequence numbers**: the client's ISN is acknowledged in step 2, the server's in step 3. With only two steps, the server couldn't know the client received its ISN, and an **old duplicate SYN** delayed in the network could make the server open a bogus connection and allocate resources.

Teardown uses four steps (FIN, ACK, FIN, ACK) because each direction closes independently; the closer waits in **TIME_WAIT** (2×MSL) to handle lost final ACKs.
""", B, ["tcp", "handshake"], True),

("How does TCP guarantee reliable delivery? Explain flow control vs congestion control.", r"""
Reliability mechanisms:
- **Sequence numbers** for every byte and **acknowledgements** from the receiver.
- **Retransmission** on timeout (RTO computed from RTT) or on 3 duplicate ACKs (fast retransmit).
- **Checksums** to detect corruption.
- **Reordering and duplicate removal** at the receiver using sequence numbers.

**Flow control** protects the **receiver**: the receiver advertises a **receive window** (free buffer space) in each ACK; the sender limits unacknowledged data to that window (sliding window). A zero window pauses the sender.

**Congestion control** protects the **network**: the sender maintains a **congestion window (cwnd)**. **Slow start** grows cwnd exponentially until a threshold, **congestion avoidance** grows it linearly, and on loss cwnd is cut (multiplicative decrease) — AIMD. Algorithms: Reno, CUBIC (Linux default), BBR.

Effective sending rate = min(rwnd, cwnd).
""", I, ["tcp", "flow-control", "congestion"], True),

("What are the differences between HTTP/1.1, HTTP/2 and HTTP/3?", r"""
- **HTTP/1.1** – text protocol over TCP; persistent (keep-alive) connections but **one request at a time per connection**, so browsers open ~6 connections per host; pipelining suffers head-of-line (HOL) blocking; headers repeated uncompressed.
- **HTTP/2** – binary framing, **multiplexing** many streams over **one TCP connection**, **HPACK header compression**, stream prioritisation. Fixes HTTP-level HOL blocking, but **TCP-level HOL blocking** remains: one lost packet stalls all streams.
- **HTTP/3** – runs over **QUIC on UDP**. QUIC provides per-stream reliability (no cross-stream HOL blocking), **built-in TLS 1.3**, **1-RTT setup and 0-RTT resumption**, and **connection migration** (survives switching from Wi-Fi to mobile data). Header compression via QPACK.

Net effect: lower latency, especially on lossy mobile networks. Most CDNs (Cloudflare, Akamai) and Google/Meta services already serve HTTP/3.
""", I, ["http", "http2", "http3"], True),

("What happens when you type a URL like https://www.google.com in the browser and press Enter?", r"""
1. **Parse URL** and check HSTS (force HTTPS), browser cache, service worker.
2. **DNS resolution**: browser cache → OS cache/hosts file → recursive resolver → root → `.com` TLD → Google's authoritative server → IP (cached per TTL).
3. **TCP 3-way handshake** with that IP on port 443 (or QUIC/UDP for HTTP/3).
4. **TLS handshake**: negotiate cipher, verify the certificate chain against trusted root CAs, derive session keys.
5. **HTTP request**: `GET /` with Host, cookies, User-Agent, Accept-Encoding.
6. **Server side**: CDN/edge → load balancer → reverse proxy → app servers → caches/DB → response.
7. **HTTP response**: status, headers (Content-Type, Cache-Control, Set-Cookie), compressed HTML.
8. **Rendering**: parse HTML → DOM, CSS → CSSOM → render tree → layout → paint → composite; fetch sub-resources (CSS/JS/images) over the same connection; execute JS (an SPA then bootstraps and calls APIs).
9. Connection kept alive for reuse.

Mention lower layers (ARP, routing, NAT) briefly and dive deeper wherever the interviewer probes.
""", I, ["url-journey", "dns", "tls"], True),

("How does DNS work? Explain recursive vs iterative queries and common record types.", r"""
DNS maps domain names to IP addresses through a hierarchical, distributed system.

**Resolution:** client checks local caches → asks a **recursive resolver** (ISP/8.8.8.8). The resolver queries a **root server** (referral to TLD), then the **TLD server** (`.com`, referral to authoritative), then the domain's **authoritative nameserver**, which returns the record. The resolver caches the answer for its **TTL**.

- **Recursive query** – the client asks the resolver to return the final answer (resolver does all the work).
- **Iterative query** – the server returns the best it knows (a referral), and the asker continues; resolver ↔ root/TLD/authoritative communication is iterative.

**Records:** A (IPv4), AAAA (IPv6), CNAME (alias), MX (mail), NS (nameservers), TXT (SPF/verification), PTR (reverse), SOA (zone info), SRV (service + port).

DNS mostly uses UDP port 53 (TCP for large responses/zone transfers). It's also used for load balancing and geo-routing.
""", I, ["dns"], True),

("How does HTTPS work? Explain the TLS handshake.", r"""
HTTPS is HTTP over **TLS**, providing encryption, integrity and server authentication.

**TLS 1.3 handshake (1 RTT):**
1. **ClientHello** – supported versions, cipher suites, random value, and a **key share** (ephemeral ECDHE public key).
2. **ServerHello** – chosen cipher and server key share. Both sides now compute the same shared secret via **Diffie-Hellman** and derive symmetric session keys. Server then sends its **certificate**, a **CertificateVerify** signature (proving it owns the private key) and **Finished** — all encrypted.
3. Client **validates the certificate** (signed by a trusted CA chain, domain matches, not expired/revoked), sends **Finished**, and encrypted application data flows (AES-GCM/ChaCha20).

TLS 1.2 needed 2 RTTs and allowed weaker options (RSA key exchange without forward secrecy). Asymmetric crypto is used only for key agreement/authentication; bulk data uses fast **symmetric** encryption. Session resumption allows 0-RTT in TLS 1.3.
""", I, ["https", "tls", "security"], True),

("What is the difference between symmetric and asymmetric encryption? Where does HTTPS use each?", r"""
- **Symmetric encryption** – the same secret key encrypts and decrypts. Fast, suitable for large data. Examples: AES, ChaCha20. Problem: securely sharing the key.
- **Asymmetric encryption** – a **public/private key pair**. Data encrypted with the public key can only be decrypted by the private key; data signed with the private key can be verified with the public key. Slow. Examples: RSA, ECC (ECDSA, ECDH).

HTTPS uses both:
1. **Asymmetric** during the TLS handshake – server authentication (certificate + signature) and key exchange (ephemeral Diffie-Hellman) to agree on a shared secret.
2. **Symmetric** for the actual data transfer using session keys derived from that secret.

This hybrid approach gives the security of public-key crypto with the speed of symmetric ciphers.
""", B, ["encryption", "https"], True),

("What are cookies? Explain HttpOnly, Secure and SameSite attributes.", r"""
Cookies are small pieces of data the server sets via the `Set-Cookie` header; the browser stores them and automatically attaches them to subsequent requests to the matching domain/path. They're used for sessions, preferences and tracking.

```
Set-Cookie: SESSION=abc; Max-Age=1800; Path=/; HttpOnly; Secure; SameSite=Lax
```
- **HttpOnly** – JavaScript (`document.cookie`) can't read it, protecting session cookies from theft via **XSS**.
- **Secure** – sent only over HTTPS, preventing interception on plain HTTP.
- **SameSite** – controls cross-site sending, mitigating **CSRF**:
  - `Strict` – never sent on cross-site requests.
  - `Lax` (browser default) – sent on top-level GET navigations, not on cross-site POSTs/iframes/XHR.
  - `None` – always sent (must be `Secure`), needed for third-party/cross-site use.
- `Expires`/`Max-Age` make it persistent; `Domain`/`Path` set scope.
""", B, ["cookies", "security"], True),

("Session-based authentication vs token-based (JWT) authentication — compare them.", r"""
**Session-based (stateful):** after login, the server stores session data (in memory/Redis) and sends a **session ID cookie** (`JSESSIONID`). Each request's cookie is looked up server-side.
- ✅ Easy logout/revocation, tiny cookie, server controls everything.
- ❌ Server state; scaling requires sticky sessions or a shared store (Spring Session + Redis); CSRF protection needed with cookies.

**Token-based (stateless, JWT):** server issues a signed token containing claims (user id, roles, expiry). Client sends it in `Authorization: Bearer`. Any service verifies the signature without a lookup.
- ✅ Scales horizontally, good for microservices and mobile apps, no session store.
- ❌ Can't easily revoke before expiry (use short-lived access tokens + refresh tokens, or a denylist), larger payload, payload readable (only signed, not encrypted), XSS risk if stored in localStorage.

Common production approach: short-lived JWT access token in memory + refresh token in an HttpOnly, Secure, SameSite cookie.
""", I, ["auth", "jwt", "sessions"], True),

("What is CORS? Why do you get a CORS error and how do you fix it?", r"""
Browsers enforce the **Same-Origin Policy**: JS from origin A (scheme + host + port) can't read responses from origin B. **CORS** is the mechanism by which server B can explicitly allow origin A through response headers like `Access-Control-Allow-Origin`, `-Methods`, `-Headers`, `-Credentials`.

For non-simple requests (PUT/DELETE, `Content-Type: application/json`, `Authorization` header) the browser first sends a **preflight `OPTIONS`** request; if the response doesn't allow the origin/method/headers, the browser blocks the real request and shows a CORS error.

Typical case: Angular on `localhost:4200` calling Spring Boot on `localhost:8080`.

**Fixes (server side):** `@CrossOrigin(origins = "http://localhost:4200")` on controllers, or a global `CorsConfigurationSource` bean plus `http.cors()` in Spring Security (so preflight isn't rejected as unauthenticated). **Dev-only:** Angular `proxy.conf.json` to make calls same-origin. Never use `*` with credentials. Remember CORS is browser-enforced; curl/Postman aren't affected.
""", I, ["cors", "security"], True),

("What are WebSockets? How are they different from HTTP and long polling?", r"""
**WebSocket** is a protocol providing a **persistent, full-duplex** channel over a single TCP connection. It starts with an HTTP `GET` carrying `Upgrade: websocket`; the server answers **101 Switching Protocols**, and from then both sides exchange small frames at any time (`ws://`, `wss://`).

- **vs HTTP:** HTTP is request–response and client-initiated; each request carries full headers. WebSockets let the **server push** instantly with tiny per-message overhead.
- **vs long polling:** long polling simulates push by holding a request open until data arrives, then the client reconnects — extra latency and header overhead per message. WebSockets keep one open connection.
- **vs SSE:** SSE is server→client only over HTTP; WebSockets are bidirectional.

Use cases: chat, live trading, multiplayer games, collaborative editing. Challenges: scaling stateful connections (sticky sessions, Redis/Kafka pub-sub to fan out across instances), heartbeats, reconnection logic, proxy/LB timeouts. Spring supports it via STOMP over WebSocket.
""", I, ["websockets", "real-time"], True),

("Compare short polling, long polling, Server-Sent Events and WebSockets.", r"""
| Technique | How | Direction | Pros | Cons |
|---|---|---|---|---|
| **Short polling** | Client requests every N sec | Client pull | Simple | Wasteful, delayed |
| **Long polling** | Server holds request until data/timeout, client re-requests | Pseudo push | Near real-time, plain HTTP | Reconnect overhead, many open requests |
| **SSE** | One long HTTP response streaming `text/event-stream` | Server → client | Simple, auto-reconnect, works over HTTP/2 | One-way, text only |
| **WebSocket** | Upgraded persistent TCP connection | Bidirectional | Lowest latency, low overhead | Stateful scaling, custom reconnect/heartbeat |

Choose by need: dashboards refreshing every minute → polling; notifications/order status/live feeds → SSE; chat, games, collaborative tools → WebSockets.
""", I, ["real-time", "websockets", "sse"], False),

("Explain HTTP methods. What does idempotent mean? Is PUT idempotent? Is POST?", r"""
- **GET** – retrieve; **HEAD** – headers only; **OPTIONS** – capabilities/CORS preflight.
- **POST** – create a resource or trigger an action.
- **PUT** – create/replace the entire resource at a known URI.
- **PATCH** – partial update.
- **DELETE** – remove.

**Safe** = doesn't modify state (GET, HEAD, OPTIONS). **Idempotent** = making the same request N times leaves the server in the same state as making it once.

- **PUT is idempotent**: `PUT /users/7 {name:"Raj"}` twice → same final state.
- **DELETE is idempotent**: second call may return 404 but state is the same.
- **POST is not idempotent**: two `POST /orders` create two orders.
- **PATCH** is not guaranteed (e.g. `{"op":"increment"}`).

Why it matters: clients/proxies can safely retry idempotent requests on timeouts. For POST payments use an **idempotency key** header that the server stores to dedupe retries.
""", B, ["http", "rest"], True),

("What is the difference between GET and POST?", r"""
| GET | POST |
|---|---|
| Retrieves data | Sends data to create a resource / perform an action |
| Parameters in the **URL query string** (visible, logged, bookmarked) | Data in the **request body** |
| **Safe and idempotent** – can be retried, prefetched | Not idempotent – retry may create duplicates |
| **Cacheable** by browsers/CDNs | Not cached by default |
| URL length limits (~2 KB–8 KB practical) | Large payloads allowed (files, JSON) |
| Stays in browser history | Not stored in history; browser warns on resend |

Security note: POST is **not** inherently secure — the body is just less visible. Sensitive data (passwords, tokens) must go over HTTPS and never in query strings, since URLs end up in server logs, proxies and browser history.

In REST: `GET /orders?status=PAID&page=0` to search, `POST /orders` with a JSON body to create. For complex searches with large filters, some APIs use `POST /orders/search`.
""", B, ["http", "rest"], True),

("What is the difference between 401 and 403? Name other important HTTP status codes.", r"""
- **401 Unauthorized** – the request lacks valid **authentication** (missing/expired/invalid token). Client should log in/refresh. Should include `WWW-Authenticate`.
- **403 Forbidden** – the server **knows who you are**, but you're **not authorised** for this resource (e.g. USER calling an ADMIN endpoint). Re-authenticating won't help.

Other key codes:
- 200 OK, 201 Created (+`Location`), 202 Accepted (async processing), 204 No Content.
- 301 permanent / 302 temporary redirect, 304 Not Modified (cache validation).
- 400 Bad Request (validation), 404 Not Found, 405 Method Not Allowed, 409 Conflict (duplicate/optimistic lock), 415 Unsupported Media Type, 422 Unprocessable Entity, 429 Too Many Requests (rate limit).
- 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout.
""", B, ["http", "status-codes"], True),

("What is a subnet mask? Calculate the network, broadcast and host range for 192.168.10.70/27.", r"""
A **subnet mask** marks which bits of an IP address are the **network** portion (1s) and which are the **host** portion (0s). CIDR `/27` = 27 network bits = `255.255.255.224`.

For /27: host bits = 5 → 2^5 = **32 addresses per subnet**, 30 usable.
Subnets in the last octet start at multiples of 32: 0, 32, 64, 96, …
70 falls in **64–95**.

- **Network address:** 192.168.10.64
- **Broadcast address:** 192.168.10.95
- **Usable hosts:** 192.168.10.65 – 192.168.10.94 (30 hosts)

Shortcut: block size = 256 − last mask octet (256 − 224 = 32). To check whether two hosts are on the same subnet, AND each IP with the mask and compare network addresses.
""", I, ["subnetting", "ip"], True),

("What is the difference between public and private IP addresses? What is NAT?", r"""
- **Public IP** – globally unique and routable on the internet; assigned by ISPs/RIRs.
- **Private IP** – reserved ranges for internal networks, not routable on the internet (RFC 1918): `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Many networks reuse them.

**NAT (Network Address Translation)** on a router rewrites private source IPs (and ports, for PAT) to its public IP for outgoing traffic, and maps replies back using a translation table. Many devices share one public IPv4 address.

Benefits: conserves IPv4 addresses, hides internal topology. Drawbacks: breaks end-to-end connectivity — inbound connections need port forwarding; P2P apps need STUN/TURN; adds state on the router. In AWS, instances in a private subnet reach the internet via a **NAT Gateway**. IPv6 largely removes the need for NAT.
""", B, ["ip", "nat"], False),

("What is ARP? How does a packet reach a host on the same LAN vs a different network?", r"""
**ARP (Address Resolution Protocol)** maps an IPv4 address to a MAC address on the local network. A host broadcasts "Who has 192.168.1.1? Tell 192.168.1.20"; the owner replies with its MAC (unicast). Results are cached in the ARP table (`arp -a`). IPv6 uses Neighbor Discovery instead.

**Same subnet:** the sender ANDs the destination IP with its subnet mask; if it matches its own network, it ARPs for the destination's MAC and sends the frame directly via the switch.

**Different network:** it ARPs for the **default gateway's** MAC and sends the frame to the router with the **destination IP unchanged** but the destination MAC = router's MAC. Each router hop rewrites the L2 header (new source/destination MAC) while the IP header stays the same end-to-end (except TTL decrement and NAT).

Security note: **ARP spoofing** lets attackers intercept LAN traffic — another reason for TLS.
""", I, ["arp", "routing"], False),

("What is DHCP? Explain the DORA process.", r"""
**DHCP (Dynamic Host Configuration Protocol)** automatically assigns network configuration — IP address, subnet mask, default gateway, DNS servers, lease time — to devices joining a network. Uses UDP (server port 67, client port 68).

**DORA:**
1. **Discover** – client (no IP yet) broadcasts to find DHCP servers.
2. **Offer** – server offers an available IP and config.
3. **Request** – client broadcasts a request for the offered IP (informing other servers which offer it accepted).
4. **Acknowledge** – server confirms; client configures its interface.

The address is **leased**; the client renews at ~50% of lease time. Benefits: no manual configuration, avoids IP conflicts, central management. Static IPs/reservations are used for servers and printers.
""", B, ["dhcp"], False),

("What is the difference between a hub, a switch and a router?", r"""
- **Hub (Layer 1)** – a dumb repeater: any incoming signal is broadcast to **all ports**. All devices share one collision domain and bandwidth. Obsolete.
- **Switch (Layer 2)** – learns **MAC addresses** of connected devices and forwards frames **only to the destination port**. Each port is its own collision domain; full-duplex. Connects devices **within** a LAN. (Layer 3 switches can also route between VLANs.)
- **Router (Layer 3)** – forwards **packets between different networks** using **IP addresses** and routing tables; separates broadcast domains; often does NAT, DHCP and firewalling. Connects your LAN to the ISP/internet.

Bonus: a **modem** converts between digital data and the ISP's signal (DSL/cable/fibre ONT); home "routers" usually combine router + switch + Wi-Fi access point.
""", B, ["devices"], False),

("What is a proxy vs a reverse proxy? What is a load balancer?", r"""
- **Forward proxy** – sits in front of **clients**; clients send requests through it to the internet. Uses: corporate filtering, caching, anonymity, bypassing restrictions. The server sees the proxy's IP.
- **Reverse proxy** – sits in front of **servers**; clients think they're talking to the origin. Uses: TLS termination, caching static content, compression, routing to backend services, hiding internal topology, rate limiting. Examples: Nginx, HAProxy, Envoy, API gateways.
- **Load balancer** – a (usually reverse-proxy) component distributing requests across multiple backend instances for scalability and availability, using algorithms like round robin, least connections, IP hash, weighted. Performs **health checks** and removes unhealthy instances.
  - **L4 LB** – routes by IP/port (fast, protocol-agnostic; AWS NLB).
  - **L7 LB** – understands HTTP: path/host/header-based routing, cookies for sticky sessions (AWS ALB, Nginx).
""", I, ["proxy", "load-balancer"], True),

("What is a CDN and how does it improve performance?", r"""
A **Content Delivery Network** is a geographically distributed network of **edge servers** that cache content close to users (Cloudflare, Akamai, CloudFront).

How it helps:
1. **Lower latency** – a user in Chennai is served from a Chennai/Mumbai edge rather than a US origin.
2. **Reduced origin load** – static assets (Angular bundles, images, videos) are served from cache.
3. **Better availability** – edges absorb traffic spikes and **DDoS** attacks; failover if origin is slow.
4. Protocol optimisations – HTTP/2/3, TLS termination at the edge, compression, image optimisation.

Routing users to the nearest edge uses **GeoDNS** or **anycast** IPs. Caching is controlled by `Cache-Control`/`ETag` headers and TTLs; deploys use hashed filenames or **cache invalidation/purge**. Dynamic content can also be accelerated via persistent edge-to-origin connections.
""", I, ["cdn", "performance"], False),

("What is the difference between a MAC address and an IP address?", r"""
| MAC address | IP address |
|---|---|
| **Physical/hardware** address of a network interface | **Logical** address of a host on a network |
| Layer 2 (Data Link) | Layer 3 (Network) |
| 48-bit, hex: `00:1A:2B:3C:4D:5E` | IPv4 32-bit (`192.168.1.5`), IPv6 128-bit |
| Assigned by manufacturer (can be spoofed/randomised) | Assigned by network admin/DHCP; changes by network |
| Used for delivery **within a local network** | Used for routing **across networks** |
| Changes at every hop (L2 header rewritten) | Stays the same end-to-end (except NAT) |

ARP connects the two by resolving IP → MAC on the local network. Analogy: IP address = postal address (where), MAC = the person's unique ID at that address.
""", B, ["ip", "mac"], False),

("What are ping and traceroute? How does traceroute work?", r"""
- **ping** sends **ICMP Echo Request** packets to a host and waits for **Echo Reply**. It measures reachability, round-trip time and packet loss. (Some servers block ICMP, so no reply doesn't always mean down.)
- **traceroute** (`tracert` on Windows) discovers the **path (hops)** packets take to a destination.

How traceroute works: it sends packets with **TTL = 1**; the first router decrements TTL to 0, drops the packet, and returns an **ICMP Time Exceeded** message, revealing its IP. Then TTL = 2 reveals the second router, and so on, until the destination replies (ICMP Echo Reply on Windows, or "Port Unreachable" for Linux's UDP probes). It prints each hop with RTTs; `* * *` means a hop didn't respond.

Useful for diagnosing where latency or packet loss occurs between your server and a client or a third-party API.
""", B, ["icmp", "tools"], False),

("What is the difference between HTTP and HTTPS, and what is HSTS?", r"""
- **HTTP** sends data in **plain text** over port 80. Anyone on the path (public Wi-Fi, ISP) can read or modify it.
- **HTTPS** is HTTP over **TLS** on port 443: traffic is **encrypted**, **integrity-protected**, and the **server is authenticated** via a CA-signed certificate. It's required for HTTP/2 in browsers, service workers, geolocation and many modern APIs, and improves SEO ranking.

**HSTS (HTTP Strict Transport Security)**: the response header `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` tells the browser to **always use HTTPS** for the domain for the given duration — even if the user types `http://`. This prevents **SSL-stripping** man-in-the-middle attacks that downgrade the first request. Domains can be added to browsers' built-in HSTS preload list.
""", B, ["https", "security"], False),

("What is the difference between TCP's Go-Back-N and Selective Repeat?", r"""
Both are **sliding-window** ARQ (Automatic Repeat reQuest) protocols allowing multiple unacknowledged packets in flight.

- **Go-Back-N:** the receiver accepts only **in-order** packets and uses **cumulative ACKs**. If packet *n* is lost, the receiver discards later packets; on timeout the sender **retransmits n and all subsequent packets** in the window. Simple receiver (no buffering), but wasteful on lossy links. Sender window ≤ 2^k − 1.
- **Selective Repeat:** the receiver **buffers out-of-order** packets and ACKs each individually; the sender retransmits **only the lost packets**. More efficient bandwidth use, but needs receiver buffers and per-packet timers. Window ≤ 2^(k−1).

Modern TCP uses cumulative ACKs plus **SACK (Selective Acknowledgment)** options, effectively combining both approaches.
""", A, ["tcp", "arq"], False),

("What are common network attacks and how are they mitigated?", r"""
- **DDoS** – flood a service with traffic from many machines. Mitigate: CDN/edge protection (Cloudflare, AWS Shield), rate limiting, autoscaling, WAF.
- **SYN flood** – exhaust half-open TCP connections. Mitigate: SYN cookies, firewall limits.
- **Man-in-the-middle** – intercept/modify traffic. Mitigate: HTTPS/TLS with certificate validation, HSTS, certificate pinning in mobile apps.
- **DNS spoofing/cache poisoning** – fake DNS answers. Mitigate: DNSSEC, DoH/DoT, randomised ports/IDs.
- **ARP spoofing** – redirect LAN traffic. Mitigate: dynamic ARP inspection, TLS.
- **XSS / CSRF / SQL injection** (application layer) – output encoding, CSP, SameSite cookies, CSRF tokens, parameterised queries (JPA/`PreparedStatement`).
- **Brute force / credential stuffing** – rate limit, CAPTCHA, account lockout, MFA.

Defence in depth: firewalls/security groups, least privilege, TLS everywhere, monitoring and logging.
""", I, ["security", "attacks"], False),
]

sources = [
("Computer Networking: A Top-Down Approach (Kurose & Ross) - companion site", "https://gaia.cs.umass.edu/kurose_ross/index.php"),
("MDN - An overview of HTTP", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview"),
("MDN - Cross-Origin Resource Sharing (CORS)", "https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS"),
("MDN - Using HTTP cookies", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies"),
("RFC 9114 - HTTP/3", "https://www.rfc-editor.org/rfc/rfc9114"),
("RFC 8446 - TLS 1.3", "https://www.rfc-editor.org/rfc/rfc8446"),
("Cloudflare Learning Center - DNS, TLS, CDN", "https://www.cloudflare.com/learning/"),
("GeeksforGeeks - Computer Network Interview Questions", "https://www.geeksforgeeks.org/computer-network-interview-questions/"),
("InterviewBit - Networking Interview Questions", "https://www.interviewbit.com/networking-interview-questions/"),
("Spring docs - CORS", "https://docs.spring.io/spring-framework/reference/web/webmvc-cors.html"),
]

build("cn", "cn", "Computer Networks", 8, "🌐",
      "Networking fundamentals for backend and full-stack interviews: OSI/TCP-IP, TCP/UDP, HTTP versions, TLS, DNS, cookies, CORS, WebSockets and IP addressing.",
      notes, qa, sources)
