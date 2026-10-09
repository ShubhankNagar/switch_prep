from traps2_common import T

A = "os-networking"

SEM_DEMO = """ReentrantLock lock = new ReentrantLock();
lock.lock();                                      // owned by main thread
Thread other = new Thread(() -> {
    try {
        lock.unlock();                            // not the owner
    } catch (IllegalMonitorStateException e) {
        System.out.println("mutex: non-owner unlock rejected");
    }
});
other.start(); other.join();

Semaphore permits = new Semaphore(1);
permits.acquire();                                // main takes the only permit
Thread signaller = new Thread(permits::release);  // a different thread gives it back: allowed
signaller.start(); signaller.join();
System.out.println("semaphore permits = " + permits.availablePermits());   // 1"""

BULKHEAD = """// Semaphore as a bulkhead: at most 10 concurrent calls to a slow dependency
private final Semaphore inFlight = new Semaphore(10);

Quote fetchQuote(String sku) throws InterruptedException {
    if (!inFlight.tryAcquire(200, TimeUnit.MILLISECONDS))
        throw new RejectedExecutionException("pricing busy, fail fast");
    try {
        return pricingClient.quote(sku);
    } finally {
        inFlight.release();                       // always release in finally
    }
}"""

DEADLOCK_BUGGY = """void transfer(Account from, Account to, long amount) {
    synchronized (from) {
        synchronized (to) {
            from.debit(amount);
            to.credit(amount);
        }
    }
}
// Thread 1: transfer(a, b, 100)    Thread 2: transfer(b, a, 50)"""

DEADLOCK_FIX = """void transfer(Account from, Account to, long amount) {
    Account first  = from.id() < to.id() ? from : to;   // global order: lower id first
    Account second = from.id() < to.id() ? to : from;
    synchronized (first) {
        synchronized (second) {
            from.debit(amount);
            to.credit(amount);
        }
    }
}"""

TRAPS = [
    T("trap-os-networking-process-vs-thread", A, "What threads share (and what they don't)", "Basic", "Very common",
      """Which of these is **shared** between threads of the same process?""",
      "Each thread has its own copy of the process memory, so threads are isolated like processes.",
      """Candidates memorise "threads are lightweight processes" and conclude that threads are isolated like processes, only cheaper. Others swing the other way and think *everything*, including local variables, is shared. The precise answer (shared heap, private stack) is what explains race conditions, why local variables are thread-safe, and why one bad thread can crash the whole JVM. Interviewers use it as the entry point to concurrency questions.""",
      """**Heap objects and static fields** are shared. Threads in a process share one address space: the heap, static data, code, and open files and sockets.

Each thread has its **own stack** (local variables, call frames), **program counter and registers**, and **thread-local storage**. So a local `int` is safe, but the **object a local reference points to** lives on the heap and may be shared. That is where race conditions come from.

**Processes** have separate address spaces: strong isolation (one crashing doesn't kill the other) but communication requires IPC (pipes, sockets, shared memory). Context switches between processes cost more (page tables, TLB).

Consequences worth mentioning:
- A native crash or `OutOfMemoryError` affects the **whole JVM**. An uncaught exception ends only that thread, which is easy to miss in thread pools: log it, or check the `Future`.
- Java 21 **virtual threads** are scheduled onto a few carrier threads but still share the heap, so the same synchronisation rules apply.""",
      "Add \"locals are thread-confined, but the objects they reference may not be\"; it shows you understand where races come from.",
      options=[
          "The call stack",
          "The program counter and registers",
          "Heap objects and static fields",
          "ThreadLocal values",
      ], answer=2,
      askedAt=["Amazon", "Goldman Sachs", "JPMorgan", "Oracle"]),

    T("trap-os-networking-mutex-vs-semaphore", A, "Mutex vs semaphore", "Intermediate", "Common",
      """Which statement about mutexes and semaphores is correct?""",
      "A mutex is just a binary semaphore; the two are interchangeable.",
      """Textbooks often introduce a mutex as "a semaphore with value 1", and that line sticks. It ignores **ownership**: a mutex is locked and unlocked by the same thread, while a semaphore is a counter that any thread can increment. That difference changes what each one is *for* (protecting a critical section vs limiting concurrency or signalling). In Java, misusing `Semaphore` as a lock leads to bugs that no exception reveals.""",
      """A **mutex has an owner**. Only the thread that locked it can unlock it. It is used for mutual exclusion around a critical section, and is often re-entrant (`ReentrantLock`, `synchronized`). OS mutexes can also support priority inheritance.

A **semaphore has no owner**. It holds N permits; `acquire` takes one (blocking if none are left) and `release` returns one, **from any thread**, even one that never acquired. That makes it right for:
- **Limiting concurrency**: at most 10 calls to a slow dependency (a bulkhead), or a pool of N connections.
- **Signalling** between threads: a producer releases, a consumer acquires.

Java pitfalls:
- `Semaphore(1)` is **not re-entrant**. The same thread acquiring twice blocks itself forever.
- A stray extra `release()` silently raises the permit count above the intended limit.
- Unlocking a `ReentrantLock` from a non-owner throws `IllegalMonitorStateException`.

Both can deadlock if acquired in inconsistent orders.""",
      "Lead with ownership (\"a mutex has an owner, a semaphore is a counter\"), then give one real use of each.",
      options=[
          "A mutex is just a binary semaphore; they are interchangeable.",
          "A mutex has an owner (only the locking thread may unlock) and protects a critical section; a semaphore has no owner, holds N permits, and limits concurrency or signals between threads.",
          "A semaphore with one permit is re-entrant like ReentrantLock.",
          "Semaphores cannot cause deadlock.",
      ], answer=1,
      fix=f"""```java
{SEM_DEMO}
```

```java
{BULKHEAD}
```""",
      askedAt=["Qualcomm", "Goldman Sachs", "Oracle", "Samsung"]),

    T("trap-os-networking-deadlock", A, "Deadlock: conditions and the practical fix", "Intermediate", "Very common",
      f"""Two threads transfer money between the same two accounts in opposite directions. The app occasionally freezes:

```java
{DEADLOCK_BUGGY}
```

Explain why, and fix it.""",
      "Make `transfer` a `synchronized` method, or add a timeout and hope the threads give up.",
      """Candidates can recite the four Coffman conditions but can't map them to code or pick the one that is cheapest to break. "Synchronize the method" locks on `this` (the service), which either does nothing useful or serialises every transfer in the system. Timeouts sound reasonable but trade deadlock for livelock and retry complexity. Interviewers want the specific, standard fix: **a global lock order**.""",
      """Thread 1 holds `a` and waits for `b`; thread 2 holds `b` and waits for `a`. All four **Coffman conditions** hold:
1. **mutual exclusion** (monitors are exclusive);
2. **hold and wait** (holding one lock while requesting another);
3. **no preemption** (a lock can't be taken away);
4. **circular wait**.

Break one:
- **Lock ordering** (break circular wait): always lock the account with the lower id first. Simple, cheap and the standard answer.
- `tryLock` with a timeout and backoff (break hold and wait): works, but risks livelock and needs retry logic.
- One global lock: correct, but it kills concurrency.

**Diagnose** with a thread dump (`jstack <pid>`): the JVM prints "Found one Java-level deadlock" with the threads and monitors involved.

**Database analogue**: two transactions updating the same rows in opposite order. InnoDB detects the cycle and rolls one back (error 1213), so update rows in a consistent order (sorted ids) and retry on deadlock errors.""",
      "Name the condition you are breaking (\"I break circular wait with lock ordering by id\"), then mention jstack and the InnoDB analogue.",
      fix=f"""```java
{DEADLOCK_FIX}
```""",
      askedAt=["Goldman Sachs", "Morgan Stanley", "Amazon", "PhonePe"]),

    T("trap-os-networking-time-wait", A, "TIME_WAIT and ephemeral port exhaustion", "Advanced", "Common",
      """A Java service calls a partner API by opening a **new HTTP connection per request** (no pooling) at 2,000 req/s. After a few seconds, calls fail with `Cannot assign requested address`. `ss -s` shows about **28,000 sockets in TIME_WAIT on the calling service's host**. What is happening?""",
      "The partner's server isn't closing connections properly, or TIME_WAIT means the handshake failed.",
      """Most people learned TIME_WAIT as a "server-side" state, or as a sign that something is broken. Actually it belongs to **whichever side closes first**, and here that is the client. Candidates also don't connect TIME_WAIT to **ephemeral ports**: each outgoing connection to the same destination needs a unique local port, and closed connections hold theirs for a while. The interviewer wants to hear "pool and reuse connections".""",
      """The side that **actively closes** a TCP connection keeps it in **TIME_WAIT** for 2×MSL (fixed at 60 s on Linux). That serves two purposes: to resend the final ACK if it is lost, and to let delayed packets from the old connection expire so they can't corrupt a new connection with the same address/port tuple.

The client closes after each request, so each closed connection holds a local port for 60 s. Linux's default ephemeral range (32768-60999) gives about **28k ports**, which allows roughly 470 new connections per second to one destination. At 2,000 req/s the ports run out in seconds.

Fixes:
- **Reuse connections**: HTTP keep-alive with a connection pool (Apache HttpClient, OkHttp, a shared JDK `HttpClient`, WebClient). This is the real fix.
- Widen `ip_local_port_range`, and enable `net.ipv4.tcp_tw_reuse` for outgoing connections.
- Never use `tcp_tw_recycle`: it broke clients behind NAT and was removed in Linux 4.12.

Related: the 3-way handshake exists so **both** sides agree on initial sequence numbers and confirm both directions work.""",
      "Say \"TIME_WAIT is on the side that closes first\" and \"the fix is connection reuse\", then the numbers.",
      options=[
          "The partner server is not closing its connections.",
          "The side that actively closes keeps the socket in TIME_WAIT (60 s on Linux); the client closes every connection, so its ~28k ephemeral ports run out. Reuse connections with keep-alive and pooling.",
          "TIME_WAIT means the TCP handshake failed; increase SYN retries.",
          "The partner's accept backlog is full.",
      ], answer=1,
      askedAt=["Amazon", "Juspay", "Akamai", "Cloudflare"]),

    T("trap-os-networking-tcp-vs-udp", A, "TCP vs UDP: what each really guarantees", "Basic", "Very common",
      """Which statement is correct?""",
      "TCP guarantees the other application received and processed your data, and each send() arrives as one message.",
      """"TCP is reliable" gets stretched into "TCP guarantees the other app handled my data". Reliability ends at the peer's **kernel**, not its application. And because typical HTTP or JSON libraries hide framing, many developers have never noticed that TCP is a **byte stream** without message boundaries. On the UDP side, "faster" gets misread as "better for APIs", ignoring that you would have to rebuild reliability yourself.""",
      """**TCP** provides an ordered, reliable **byte stream** with flow and congestion control. It does **not** preserve message boundaries: two `send()` calls can arrive in one `recv()`, or one can arrive split across several. Protocols therefore need framing (length prefixes, delimiters, HTTP's `Content-Length` or chunking). When `send()` returns, your bytes are only in the local kernel buffer. Even a TCP ACK only proves the peer's kernel received them; the application may crash before processing. End-to-end guarantees need **application-level acknowledgements and idempotency**.

**UDP** sends independent datagrams: no connection setup, no ordering, no retransmission, and no head-of-line blocking. It suits DNS, voice and video, gaming, and **QUIC**, which builds reliable, multiplexed streams in user space on top of UDP. That is how HTTP/3 avoids TCP's head-of-line blocking, where one lost segment stalls everything behind it.""",
      "Mention \"byte stream, not messages\" and \"an ACK is not app-level processing\"; both separate you from rote answers.",
      options=[
          "Once TCP send() returns, the remote application has processed the data.",
          "TCP preserves message boundaries: two send() calls arrive as two recv() calls.",
          "TCP gives an ordered, reliable byte stream with no message boundaries; UDP gives independent datagrams that may be lost, duplicated or reordered, with reliability built on top if needed (as QUIC does).",
          "UDP is always faster, so it is the better default for APIs.",
      ], answer=2,
      askedAt=["Cisco", "Juniper", "Amazon", "Zoho"]),

    T("trap-os-networking-url-flow", A, "What happens when you type a URL", "Intermediate", "Very common",
      """"What happens when you type `https://shop.example.com/cart` into the browser and press Enter?" The interviewer will let you talk for a minute, then **drill into two layers of their choice**.""",
      "DNS gives the IP, the browser sends an HTTP request, and the server returns HTML that the browser shows.",
      """It is such a famous question that candidates give a rehearsed four-line summary. That skips the parts interviewers actually drill into: caching at every layer, the TCP and TLS handshakes (and their round-trip costs), what sits between the internet and the app server, and what the browser does after the first byte. Common factual slips: "DNS asks the root servers every time" and "HTTPS hides which site I'm visiting".""",
      """A strong answer walks through the layers and names the round trips:

1. **Browser**: parse the URL, check HSTS (forces https), then the HTTP cache and any service worker.
2. **DNS**: browser cache → OS cache and hosts file → recursive resolver. Only on a miss does the resolver walk root → `.com` → the authoritative server. TTLs control caching. The answer is often a **CDN edge** IP (GeoDNS or anycast).
3. **Connection**: TCP handshake (1 RTT) + TLS 1.3 (1 RTT: certificate check, SNI, ALPN picks HTTP/2). HTTP/3 over QUIC merges both into 1 RTT, or 0-RTT on resumption.
4. **Request path**: CDN → load balancer (often terminates TLS) → gateway or reverse proxy → app server (Tomcat thread, filters, controller) → cache and database.
5. **Response and render**: status, `Cache-Control`, `Set-Cookie`, compression. The browser builds the DOM and CSSOM, fetches subresources over the **same connection** (HTTP/2 multiplexing vs about 6 connections per host with HTTP/1.1), runs JS, then paints.

Privacy: HTTPS encrypts the path, headers and body, but the hostname is visible through DNS and SNI unless DoH and ECH are used.""",
      "Give the one-minute overview, then ask \"which layer should I go deeper on?\"; it shows structure and lets you steer to strengths.",
      fix="""```text
Round trips before the first byte (cold, no caches):
DNS (recursive miss)  ~1+ RTT to resolver (+ resolver's own lookups)
TCP handshake         1 RTT   (SYN, SYN-ACK, ACK)
TLS 1.3               1 RTT   (ClientHello+key share -> ServerHello+cert+Finished)
HTTP request          1 RTT
=> ~3-4 RTT. HTTP/3 (QUIC) merges TCP+TLS: ~2 RTT; resumed 0-RTT: ~1 RTT
Warm: DNS cached + reused keep-alive/HTTP2 connection => 1 RTT
```""",
      askedAt=["Amazon", "Google", "Microsoft", "Zoho"]),

    T("trap-os-networking-cors", A, "CORS is enforced by the browser", "Intermediate", "Very common",
      """Your Angular app at `https://app.shop.com` calls `https://api.shop.com/orders` with a JWT in the `Authorization` header. The browser console shows a **CORS error**, but the exact same request works in Postman. Which statement is correct?""",
      "CORS is a server-side security feature that protects the API from unauthorised clients; Postman simply bypasses it.",
      """CORS errors appear when calling the server and are fixed by changing server config, so people assume it is server-side protection. In fact the **browser** enforces it, to protect *users*. It stops a malicious site's JavaScript from reading responses from other origins using the user's session. Postman, curl and servers don't enforce it. Candidates also don't know which requests trigger a preflight, and why Spring Security sometimes rejects it.""",
      """The **browser** enforces the same-origin policy, where an origin is scheme + host + port, so `app.` and `api.` are different origins. The server must **opt in** with headers. Non-browser clients ignore all of this, so **CORS is not authentication** and doesn't protect your API from scripts.

Key mechanics:
- **Preflight**: a request with `Authorization`, a JSON `Content-Type`, or methods like PUT/DELETE triggers an automatic `OPTIONS` request first. The server must answer it with the allowed origin, methods and headers. The preflight carries **no credentials**, so if your security filter demands a JWT on `OPTIONS`, CORS fails. In Spring Security, enable `cors()` so preflights are handled before authentication.
- **Credentials** (cookies): the server must echo the exact origin and send `Access-Control-Allow-Credentials: true`. A `*` origin is not allowed with credentials.
- Simple requests still **reach the server**; the browser only hides the response. That is why CORS is not CSRF protection.
- In development, Angular's `proxy.conf.json` avoids cross-origin calls entirely.""",
      "Say \"CORS protects users, is enforced by browsers, and is not API security\", then explain preflight and credentials.",
      options=[
          "The API is broken; Postman is hiding the error.",
          "The browser enforces CORS: the API must return `Access-Control-Allow-Origin: https://app.shop.com` and handle the OPTIONS preflight. CORS does not restrict non-browser clients, so it is not an authentication mechanism.",
          "CORS protects the API from attackers using curl or scripts.",
          "Setting `Access-Control-Allow-Origin: *` together with credentials is the simplest correct fix.",
      ], answer=1,
      fix="""```text
Preflight sent by the browser:
OPTIONS /orders
Origin: https://app.shop.com
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: authorization, content-type

API response:
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.shop.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: authorization, content-type
Access-Control-Allow-Credentials: true      (only if you send cookies)
Access-Control-Max-Age: 3600                (cache the preflight)
Vary: Origin
```""",
      askedAt=["Thoughtworks", "Publicis Sapient", "Freshworks"]),

    T("trap-os-networking-jwt-storage", A, "Where to store tokens: localStorage vs HttpOnly cookie", "Intermediate", "Common",
      """Your Angular SPA receives a JWT after login. Where should it keep the token, and why?""",
      "localStorage is fine because a JWT is signed, so nobody can misuse it.",
      """"Signed" gets confused with "safe". A signature stops **tampering**, not **theft**: whoever holds the token *is* the user until it expires. And the payload is only base64url-encoded, readable by anyone. Candidates also present cookies vs localStorage as "secure vs insecure" instead of as a trade-off between **XSS exposure** and **CSRF exposure**. Interviewers want the trade-off and the common hybrid pattern.""",
      """There is no storage that is safe from XSS, only trade-offs:

- **localStorage / sessionStorage**: no CSRF risk (nothing is sent automatically), but **any XSS** can read the token and send it to an attacker, who can then use it from anywhere until it expires.
- **HttpOnly; Secure; SameSite cookie**: JavaScript can't read it, so XSS can't steal it, but the browser sends it automatically, so you need **CSRF protection**. `SameSite=Lax/Strict` blocks most cross-site sends; add CSRF tokens for state-changing requests if needed.

**Common pattern**: a short-lived access token (5-15 min) kept **in memory**, plus a refresh token in an **HttpOnly, Secure, SameSite=Strict cookie** scoped to the refresh endpoint and **rotated** on every use (reuse means theft, so revoke the token family).

Also: stateless JWTs are hard to revoke (keep expiry short, or use a denylist by `jti`). Never put secrets or PII in the payload. Fix XSS at the source: Angular escapes interpolation, so avoid `bypassSecurityTrust*` and raw `innerHTML` with untrusted data.""",
      "Frame it as \"XSS vs CSRF trade-off\" and describe the in-memory access token plus HttpOnly refresh cookie pattern.",
      options=[
          "localStorage: it is safe because JWTs are signed.",
          "No storage is XSS-proof: an HttpOnly, Secure, SameSite cookie keeps the token away from JavaScript but needs CSRF protection; localStorage avoids CSRF but any XSS can read it. A common pattern is a short-lived access token in memory plus a rotating refresh token in an HttpOnly cookie.",
          "A non-HttpOnly cookie so Angular can read it; cookies are immune to XSS.",
          "In the URL query string, so every request carries it.",
      ], answer=1,
      fix="""```text
Set-Cookie: refresh_token=8f3c...; HttpOnly; Secure; SameSite=Strict; Path=/api/auth/refresh; Max-Age=1209600
Access token: kept in a service field / signal (memory only), sent as Authorization: Bearer <token>
On 401 -> POST /api/auth/refresh (cookie sent automatically) -> new access token + rotated refresh cookie
```""",
      askedAt=["Razorpay", "CRED", "Okta", "Freshworks"]),
]

CHECKS = [
    {"name": "os-semaphore", "lang": "java", "code": """import java.util.concurrent.*;
import java.util.concurrent.locks.*;
public class Main {
  record Quote(String sku) {}
  interface PricingClient { Quote quote(String sku); }
  PricingClient pricingClient = Quote::new;
""" + "\n".join("  " + l for l in BULKHEAD.splitlines()) + """
  public static void main(String[] args) throws Exception {
""" + "\n".join("    " + l for l in SEM_DEMO.splitlines()) + """
    Main m = new Main();
    System.out.println(m.fetchQuote("sku-1") + " left=" + m.inFlight.availablePermits());
    m.inFlight.acquire(10);
    try { m.fetchQuote("x"); } catch (RejectedExecutionException e) { System.out.println("bulkhead full: " + e.getMessage()); }
  }
}""", "expect": ["mutex: non-owner unlock rejected", "semaphore permits = 1", "Quote[sku=sku-1] left=10", "bulkhead full: pricing busy, fail fast"]},
    {"name": "os-deadlock-fix", "lang": "java", "code": """import java.util.concurrent.*;
public class Main {
  static final class Account { final int id; long bal; Account(int id, long b) { this.id = id; bal = b; } int id() { return id; } void debit(long a) { bal -= a; } void credit(long a) { bal += a; } }
""" + "\n".join("  " + l for l in DEADLOCK_FIX.splitlines()) + """
  public static void main(String[] args) throws Exception {
    Main m = new Main(); Account a = new Account(1, 1_000_000), b = new Account(2, 1_000_000);
    Thread t1 = new Thread(() -> { for (int i = 0; i < 200_000; i++) m.transfer(a, b, 1); });
    Thread t2 = new Thread(() -> { for (int i = 0; i < 200_000; i++) m.transfer(b, a, 1); });
    t1.start(); t2.start(); t1.join(5000); t2.join(5000);
    System.out.println((t1.isAlive() || t2.isAlive()) ? "DEADLOCK" : "done total=" + (a.bal + b.bal) + " a=" + a.bal);
  }
}""", "expect": ["done total=2000000 a=1000000"]},
    {"name": "os-deadlock-buggy", "lang": "java", "code": """import java.util.concurrent.*;
public class Main {
  static final class Account { long bal; void debit(long a) { bal -= a; } void credit(long a) { bal += a; } }
""" + "\n".join("  " + l for l in DEADLOCK_BUGGY.split("// Thread 1")[0].splitlines()) + """
  public static void main(String[] args) throws Exception {
    Main m = new Main(); Account a = new Account(), b = new Account();
    Thread t1 = new Thread(() -> { for (int i = 0; i < 5_000_000; i++) m.transfer(a, b, 1); });
    Thread t2 = new Thread(() -> { for (int i = 0; i < 5_000_000; i++) m.transfer(b, a, 1); });
    t1.setDaemon(true); t2.setDaemon(true);
    t1.start(); t2.start(); t1.join(4000); t2.join(1000);
    System.out.println((t1.isAlive() && t2.isAlive()) ? "DEADLOCK observed" : "finished");
  }
}""", "expect": ["DEADLOCK observed"]},
]
