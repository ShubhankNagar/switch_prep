from fr1_common import M, C, T, build

mcqs = [
M("Computer networks", '''What is the correct sequence of the TCP three-way handshake?''',
["SYN, ACK, SYN-ACK", "SYN, SYN-ACK, ACK", "ACK, SYN, FIN", "SYN, SYN, ACK"], 1,
'''The client sends SYN with its initial sequence number. The server replies SYN-ACK, acknowledging the client's number and sending its own. The client then sends ACK. Both sides have now agreed on sequence numbers. Closing a connection normally takes four segments: FIN, ACK, FIN, ACK.''',
["Uber", "Atlassian", "Amazon"]),

M("Computer networks", '''Which of these commonly runs over UDP rather than TCP?''',
["HTTP/1.1", "SMTP", "DNS queries", "SSH"], 2,
'''Ordinary DNS lookups use UDP port 53 because they are small and a lost packet is simply retried, which avoids handshake latency. DNS falls back to TCP for large responses and zone transfers. Video calls, gaming and QUIC (HTTP/3) also use UDP.''',
["Uber", "Atlassian", "Oracle"]),

M("Computer networks", '''At which OSI layer does a router primarily operate?''',
["Layer 2 (Data link)", "Layer 3 (Network)", "Layer 4 (Transport)", "Layer 7 (Application)"], 1,
'''Routers forward packets between networks using IP addresses, which is Layer 3. Switches forward frames by MAC address at Layer 2. An L4 load balancer works with TCP/UDP ports, and an L7 load balancer or API gateway inspects HTTP paths and headers.''',
["Atlassian", "Uber"]),

M("Computer networks", '''A logged-in user calls an admin-only endpoint they are not permitted to use. Which HTTP status code is correct?''',
["401 Unauthorized", "403 Forbidden", "404 Not Found", "400 Bad Request"], 1,
'''401 means "not authenticated": credentials are missing or invalid, and the client should log in. 403 means the server knows who you are but you do not have permission. Some APIs return 404 to hide that a resource exists, but 403 is the standard answer.''',
["Atlassian", "Razorpay", "Uber"]),

M("REST API design", '''Which HTTP method is NOT idempotent by definition?''',
["GET", "PUT", "DELETE", "POST"], 3,
'''Repeating GET, PUT or DELETE leaves the server in the same state as doing it once. POST typically creates a new resource each time, so a retried payment POST could charge twice. Payment APIs such as Razorpay and Stripe accept an `Idempotency-Key` header to make POST retries safe.''',
["Atlassian", "Uber", "Razorpay", "PhonePe"]),

M("Computer networks", '''Why does the side that actively closes a TCP connection enter the TIME_WAIT state for 2 x MSL?''',
["To keep the port reserved forever", "To make sure the final ACK can be retransmitted and that old duplicate segments expire before the same 4-tuple is reused",
 "To wait for the application to flush logs", "To perform slow start"], 1,
'''If the last ACK is lost, the peer retransmits its FIN, and the closer must still be able to respond. Waiting also stops delayed packets from an old connection being taken as part of a new one on the same ports. Many TIME_WAIT sockets on busy clients are a sign that connection pooling is needed.''',
["Uber", "Atlassian"]),

M("Computer networks", '''How many usable host addresses does a /26 IPv4 subnet provide?''',
["64", "62", "30", "126"], 1,
'''A /26 leaves 32 - 26 = 6 host bits, so 2^6 = 64 addresses. Subtract the network address and the broadcast address to get 62 usable hosts. Similarly, a /24 gives 254 and a /30 gives 2 (used for point-to-point links).''',
["Oracle", "Uber"]),

M("Computer networks", '''What does a browser try first when resolving `www.example.com`, before any DNS server is queried?''',
["The root name server", "The TLD (.com) server", "Its own DNS cache, then the OS cache or hosts file", "The authoritative server"], 2,
'''Resolution checks the local caches first: the browser cache, then the OS resolver cache and the hosts file. Only on a miss does a query go to the recursive resolver (ISP, 8.8.8.8), which, if needed, asks a root server, then the .com TLD server, then the authoritative server. Each answer is cached according to its TTL.''',
["Atlassian", "Uber", "Google"]),

M("Computer networks", '''In HTTPS (TLS 1.2/1.3), how is cryptography used?''',
["Only symmetric encryption for everything", "Asymmetric cryptography (certificates, key exchange) to authenticate and agree on keys, then fast symmetric encryption for the data",
 "Only asymmetric RSA encryption for all data", "Hashing only"], 1,
'''The server proves its identity with a certificate signed by a trusted CA. An (EC)DHE key exchange produces a shared secret with forward secrecy. Bulk traffic is then encrypted with symmetric ciphers such as AES-GCM or ChaCha20, because asymmetric crypto is far too slow for streaming data.''',
["Uber", "Razorpay", "PhonePe"]),

M("Computer networks", '''Which HTTP version runs over QUIC on top of UDP?''',
["HTTP/1.0", "HTTP/1.1", "HTTP/2", "HTTP/3"], 3,
'''HTTP/2 multiplexed streams over one TCP connection, but a single lost packet still blocks every stream (TCP head-of-line blocking). HTTP/3 uses QUIC over UDP, which handles loss per stream, combines the transport and TLS 1.3 handshakes, and survives network changes such as moving from Wi-Fi to mobile data.''',
["Uber", "Atlassian"]),

M("Computer networks", '''TCP flow control and congestion control differ because…''',
["They are the same mechanism", "Flow control protects the RECEIVER (advertised window, rwnd); congestion control protects the NETWORK (cwnd, slow start, AIMD)",
 "Flow control is done by routers", "Congestion control uses the receiver window only"], 1,
'''The receiver advertises how much buffer space it has, which is flow control. The sender separately estimates network capacity with a congestion window: exponential slow start, then additive increase and multiplicative decrease on loss. The effective send window is min(rwnd, cwnd).''',
["Uber", "Microsoft"]),

M("Computer networks", '''Which statement about WebSockets is TRUE?''',
["They are one-way, server to client only", "They start as an HTTP request with an `Upgrade` header and then provide full-duplex messaging over one TCP connection",
 "They run over UDP", "Each message opens a new TCP connection"], 1,
'''After the HTTP/1.1 Upgrade handshake (101 Switching Protocols), both sides can send frames at any time with low overhead. They are used for live location (Uber driver tracking), chat and collaborative editing. Server-Sent Events are the simpler option for one-way streams.''',
["Uber", "Atlassian", "Swiggy"]),

M("Computer networks", '''Which port mapping is WRONG?''',
["HTTPS: 443", "SSH: 22", "DNS: 53", "MySQL: 5432"], 3,
'''MySQL listens on 3306 by default, and 5432 is PostgreSQL. Other ports worth remembering: HTTP 80, SMTP 25 or 587, Redis 6379, Kafka 9092, MongoDB 27017, and Spring Boot's embedded Tomcat on 8080 by default.''',
["Oracle", "Atlassian"]),

M("Computer networks", '''What does ARP do?''',
["Maps domain names to IP addresses", "Maps an IP address to a MAC address on the local network", "Assigns IP addresses dynamically", "Encrypts packets"], 1,
'''When a host knows a destination IP on its subnet (or the gateway's IP), it broadcasts an ARP request asking who has that IP, and the owner replies with its MAC address so Ethernet frames can be built. DNS maps names to IPs, and DHCP assigns IPs.''',
["Oracle", "Uber"]),

M("System design", '''Which rate-limiting algorithm allows short bursts up to a capacity while enforcing a long-term average rate?''',
["Fixed window counter", "Token bucket", "Leaky bucket with a constant drain only", "Round robin"], 1,
'''Tokens are added at rate r up to a capacity b, and each request uses one token. A full bucket lets b requests through at once, and after that requests are limited to r per second. A leaky bucket smooths output to a constant rate. A fixed window allows bursts at window edges.''',
["Atlassian", "Uber", "Razorpay"]),

M("System design", '''A fixed-window rate limiter allows 100 requests per minute. What is the worst-case number of requests it can accept within any 2-second span?''',
["100", "101", "200", "50"], 2,
'''A client can send 100 requests in the last second of one window and another 100 in the first second of the next, because the counter resets at the boundary. Sliding-window logs or sliding-window counters (a weighted mix of the previous and current windows) fix this.''',
["Atlassian", "Uber"]),

M("System design", '''With consistent hashing across N servers holding K keys, roughly how many keys move when one server is added?''',
["All K keys", "About K / N keys", "About N keys", "None"], 1,
'''Only the keys between the new node and its predecessor on the ring move to it, which is roughly K/N. With `hash % N`, nearly every key would be remapped. Virtual nodes spread the load evenly. It is used in Cassandra, DynamoDB, CDNs and distributed caches.''',
["Uber", "Atlassian", "Amazon"]),

M("System design", '''In the cache-aside pattern, what is the commonly recommended order when UPDATING data?''',
["Update the cache, then the DB", "Update the DB, then delete (invalidate) the cache entry",
 "Delete the cache, never touch the DB", "Update the DB and never touch the cache"], 1,
'''Writing the DB first keeps it as the source of truth. Deleting rather than updating the cache avoids two concurrent writers leaving a stale value behind, and the next read reloads fresh data. Short TTLs or a delayed second delete shrink the remaining race window.''',
["Atlassian", "Swiggy", "Uber"]),

M("System design", '''What can an L7 (application) load balancer do that an L4 load balancer cannot?''',
["Balance TCP connections", "Route by URL path, host header or cookie, and terminate TLS", "Use round robin", "Perform health checks"], 1,
'''An L4 load balancer sees only IPs and ports, so it is fast but blind to content. An L7 load balancer (Nginx, ALB, an API gateway) parses HTTP, so it can send `/api/payments` to one service and `/static` to another, use cookies for sticky sessions, rewrite headers and terminate TLS.''',
["Uber", "Atlassian", "Flipkart"]),

M("Spring Boot", '''An Angular app on `localhost:4200` calls a Spring Boot API on `localhost:8080` with a `PUT` and a JSON body. What does the browser send first?''',
["Nothing extra", "A preflight OPTIONS request that checks the CORS headers", "A HEAD request", "A WebSocket handshake"], 1,
'''A different port means a different origin. A non-simple request (PUT, or a JSON content type) triggers a CORS preflight OPTIONS request. The server must reply with `Access-Control-Allow-Origin` and allowed methods and headers, configured in Spring with `@CrossOrigin` or a `CorsConfigurationSource`, including in Spring Security.''',
["Atlassian", "Razorpay"]),
]

coding = [
C("LRU Cache", "Medium", ["Atlassian", "Uber", "Amazon", "Microsoft"],
'''Design an `LRUCache` with a fixed capacity:
- `get(key)` returns the value if the key is present, otherwise -1, and marks the key as recently used.
- `put(key, value)` inserts or updates the key. If the cache is over capacity, evict the least recently used key.

Both operations must run in **O(1)** average time.

**Example**
```
LRUCache c = new LRUCache(2);
c.put(1,1); c.put(2,2);
c.get(1);    // 1
c.put(3,3);  // evicts key 2
c.get(2);    // -1
c.put(4,4);  // evicts key 1
c.get(1);    // -1   c.get(3) -> 3   c.get(4) -> 4
```
**Constraints**
- 1 <= capacity <= 3000; up to 2 * 10^5 calls''',
["A HashMap gives O(1) lookup, but it does not track order. What gives O(1) move-to-front and remove-from-tail?",
 "Use a doubly linked list with sentinel head and tail nodes, plus a map from key to node."],
r'''
import java.util.*;

class LRUCache {
    private static final class Node {
        int key, val;
        Node prev, next;
        Node(int k, int v) { key = k; val = v; }
    }
    private final int capacity;
    private final Map<Integer, Node> map = new HashMap<>();
    private final Node head = new Node(0, 0), tail = new Node(0, 0); // sentinels

    public LRUCache(int capacity) {
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        Node n = map.get(key);
        if (n == null) return -1;
        unlink(n);
        addFront(n);
        return n.val;
    }

    public void put(int key, int value) {
        Node n = map.get(key);
        if (n != null) {
            n.val = value;
            unlink(n);
            addFront(n);
            return;
        }
        if (map.size() == capacity) {
            Node lru = tail.prev;
            unlink(lru);
            map.remove(lru.key);
        }
        n = new Node(key, value);
        map.put(key, n);
        addFront(n);
    }

    private void unlink(Node n) {
        n.prev.next = n.next;
        n.next.prev = n.prev;
    }
    private void addFront(Node n) {
        n.next = head.next;
        n.prev = head;
        head.next.prev = n;
        head.next = n;
    }
}
''',
'''The HashMap finds a node in O(1), and the doubly linked list keeps the nodes in recency order, most recent at the front. Because each node knows its neighbours, unlinking it and moving it to the front are pointer changes, which is O(1). The sentinel head and tail nodes remove null checks for an empty list or the first and last elements. The node stores its key so that eviction can also delete the map entry. Atlassian and Uber interviewers then ask follow-ups: thread safety (a single lock is simplest; segmented or lock-striped caches scale better), TTL expiry, LFU instead of LRU, and why `LinkedHashMap(accessOrder = true)` alone may not be enough for the interview.''',
"O(1) per operation", "O(capacity)", "https://leetcode.com/problems/lru-cache/"),

C("Sliding Window Rate Limiter", "Medium", ["Atlassian", "Uber", "Razorpay"],
'''Implement a per-client rate limiter. `RateLimiter(int maxRequests, long windowMillis)` allows each client at most `maxRequests` requests in ANY rolling window of `windowMillis` milliseconds. `boolean allow(String clientId, long timestampMillis)` returns true and records the request if it is allowed, otherwise returns false. Timestamps for a single client arrive in non-decreasing order.

**Example**
```
RateLimiter rl = new RateLimiter(3, 1000);
rl.allow("u1", 0)    -> true
rl.allow("u1", 100)  -> true
rl.allow("u1", 200)  -> true
rl.allow("u1", 300)  -> false   // 4th within 1000 ms
rl.allow("u2", 300)  -> true    // separate client
rl.allow("u1", 1000) -> true    // request at 0 has expired (window is (t-1000, t])
```
**Follow-ups**: make it thread-safe; reduce memory; distribute it across servers.''',
["Store the timestamps of accepted requests per client, and drop the ones that have fallen out of the window.",
 "A Deque per client gives O(1) amortised eviction from the front. Use ConcurrentHashMap plus a per-client lock for thread safety."],
r'''
import java.util.*;
import java.util.concurrent.*;

class RateLimiter {
    private final int maxRequests;
    private final long windowMillis;
    private final Map<String, Deque<Long>> log = new ConcurrentHashMap<>();

    public RateLimiter(int maxRequests, long windowMillis) {
        this.maxRequests = maxRequests;
        this.windowMillis = windowMillis;
    }

    public boolean allow(String clientId, long now) {
        Deque<Long> q = log.computeIfAbsent(clientId, k -> new ArrayDeque<>());
        synchronized (q) {                                  // per-client lock
            while (!q.isEmpty() && q.peekFirst() <= now - windowMillis) {
                q.pollFirst();                              // expire old requests
            }
            if (q.size() < maxRequests) {
                q.addLast(now);
                return true;
            }
            return false;
        }
    }
}
''',
'''This is the sliding-window log algorithm. Each client keeps a deque of the timestamps of its accepted requests. On every call, timestamps at or before `now - window` are removed from the front, and the request is allowed only if fewer than `maxRequests` remain. It is exact, with no burst at window boundaries, but it uses O(maxRequests) memory per client. Locking each client's deque separately lets different clients proceed in parallel. In the Atlassian LLD round, the expected discussion goes further: a token bucket (O(1) memory, allows bursts), a sliding-window counter approximation, a `RateLimitStrategy` interface for the different algorithms, and a distributed version using a Redis sorted set or Lua script, keyed by user or API key.''',
"O(1) amortised per call", "O(clients * maxRequests)", None),

C("Snapshot Array", "Medium", ["Google", "Atlassian", "Uber"],
'''Implement `SnapshotArray(int length)`, an array of the given length where every element starts at 0:
- `set(index, val)` sets the element at index.
- `snap()` takes a snapshot and returns its id, which is the number of times `snap()` has been called minus 1.
- `get(index, snapId)` returns the value at index as it was when snapshot `snapId` was taken.

**Example**
```
SnapshotArray a = new SnapshotArray(3);
a.set(0, 5);
a.snap();        // 0
a.set(0, 6);
a.get(0, 0);     // 5
```
**Constraints**
- 1 <= length <= 5 * 10^4; up to 5 * 10^4 calls in total''',
["Copying the whole array on every snap uses O(length) memory per snap. Store only the changes instead.",
 "For each index, keep a TreeMap snapId -> value; get() uses floorEntry(snapId)."],
r'''
import java.util.*;

class SnapshotArray {
    private final TreeMap<Integer, Integer>[] history;
    private int snapId = 0;

    @SuppressWarnings("unchecked")
    public SnapshotArray(int length) {
        history = new TreeMap[length];
        for (int i = 0; i < length; i++) {
            history[i] = new TreeMap<>();
            history[i].put(0, 0);
        }
    }

    public void set(int index, int val) {
        history[index].put(snapId, val);      // overwrite within current snap
    }

    public int snap() {
        return snapId++;
    }

    public int get(int index, int snapId) {
        return history[index].floorEntry(snapId).getValue();
    }
}
''',
'''Storing only changes keeps memory proportional to the number of `set` calls instead of `length x snaps`. Each index has a sorted map from snapshot id to the value written during that snapshot period. Repeated sets before the next `snap()` overwrite the same entry, so only the last value counts. To read index i at snapshot s, find the most recent change made at or before s using `floorEntry`, which is O(log k). An ArrayList of (snapId, value) pairs with binary search uses less memory than a TreeMap. This is the same idea as MVCC in databases and versioned config stores, which makes a good system-design connection to mention at Atlassian or Uber.''',
"set O(log k), snap O(1), get O(log k)", "O(length + number of set calls)", "https://leetcode.com/problems/snapshot-array/"),

C("File Collections: Total Size and Top K", "Medium", ["Atlassian"],
'''You process a stream of files. Each file has a name, a size, and zero or more collections it belongs to (a file can be in several collections). Build a class with:
- `addFile(String name, long size, List<String> collections)`
- `long totalSize()`: the total size of all files processed.
- `List<String> topK(int k)`: the k collections with the largest total size, largest first.

**Example**
```
addFile("file1.txt", 100, [])
addFile("file2.txt", 200, ["collection1"])
addFile("file3.txt", 200, ["collection1"])
addFile("file4.txt", 300, ["collection2"])
addFile("file5.txt", 10,  [])
totalSize() -> 810
topK(2)     -> ["collection1", "collection2"]   // 400, 300
```
**Constraints**
- up to 10^5 files; k <= number of collections''',
["Keep a running total and a HashMap from collection name to its accumulated size.",
 "For top K, a min-heap of size k gives O(C log k), which is better than sorting all C collections."],
r'''
import java.util.*;

class FileCollectionStats {
    private long total = 0;
    private final Map<String, Long> collectionSize = new HashMap<>();

    public void addFile(String name, long size, List<String> collections) {
        total += size;
        if (collections == null) return;
        for (String c : new HashSet<>(collections)) {          // ignore duplicates
            collectionSize.merge(c, size, Long::sum);
        }
    }

    public long totalSize() {
        return total;
    }

    public List<String> topK(int k) {
        PriorityQueue<Map.Entry<String, Long>> heap = new PriorityQueue<>(
            (a, b) -> !a.getValue().equals(b.getValue())
                      ? Long.compare(a.getValue(), b.getValue())
                      : b.getKey().compareTo(a.getKey()));     // min-heap
        for (Map.Entry<String, Long> e : collectionSize.entrySet()) {
            heap.offer(e);
            if (heap.size() > k) heap.poll();
        }
        List<String> result = new ArrayList<>();
        while (!heap.isEmpty()) result.add(heap.poll().getKey());
        Collections.reverse(result);
        return result;
    }
}
''',
'''A candidate reported this as Atlassian's "code design" round, so readable class design matters as much as complexity. Keep a running total, plus a map from each collection to its accumulated size, updated with `merge`. Deduplicating a file's collection list stops a file from counting twice in the same collection. For `topK`, keep a min-heap of size k: push each entry and pop the smallest whenever the heap grows past k. That is O(C log k), and the heap's contents are then reversed to give largest first. The tie-breaking on name keeps output deterministic. Expected follow-ups: nested collections (a parent's size includes its children, so walk up the hierarchy or aggregate with a DFS), frequent topK calls (maintain a TreeMap or sorted structure incrementally), and concurrency.''',
"addFile O(m) per file; topK O(C log k)", "O(C) for C collections", None),
]

theory = [
T("What happens when you type a URL like https://www.atlassian.com into the browser and press Enter?",
'''1) **Parse** the URL (scheme, host, path; HSTS may force HTTPS). 2) **DNS**: check the browser cache, the OS cache and hosts file, then the recursive resolver, then root, TLD and authoritative servers, and get the IP (often a CDN edge). 3) **TCP** three-way handshake with that IP on port 443 (or QUIC over UDP for HTTP/3). 4) **TLS** handshake: the certificate is validated, keys are exchanged and a symmetric session key is derived. 5) The **HTTP request** is sent with headers and cookies. 6) **Server side**: the CDN serves a cached response or forwards to a load balancer, then the web or app servers (for example a Spring Boot service), caches and DB, and a response comes back with a status, headers and body. 7) **Rendering**: parse the HTML into the DOM and CSS into the CSSOM, fetch sub-resources, run JS, then layout, paint and composite.''',
["Atlassian", "Uber", "Google", "Amazon"]),

T("Compare TCP and UDP. When would you choose UDP?",
'''**TCP** is connection-oriented (handshake). It delivers data reliably and in order, with acknowledgements, retransmission, flow control (receiver window) and congestion control. It is a byte stream, has a 20+ byte header, and suffers head-of-line blocking. It is used for HTTP/1.1 and 2, databases, SSH and email. **UDP** is connectionless, sends independent datagrams, has an 8-byte header and gives no reliability, ordering or congestion control. It is lower latency and supports broadcast and multicast. Choose UDP when **freshness beats completeness** or the application handles reliability itself: live video and voice (a late packet is useless), online gaming, DNS lookups, telemetry and metrics (StatsD), and QUIC/HTTP/3, which builds its own reliability and per-stream ordering on top of UDP. For example, Uber driver location pings tolerate an occasional loss because a newer ping follows within seconds.''',
["Uber", "Atlassian", "Oracle"]),

T("How does the HTTPS/TLS handshake work?",
'''In TLS 1.2 (simplified): the **ClientHello** sends supported versions, cipher suites and a random value. The **ServerHello** picks a cipher and sends the server's random value and its **certificate** chain. The client checks the certificate: it must chain to a trusted CA, match the hostname and not be expired or revoked. Both sides run an **(EC)DHE key exchange** to get a shared pre-master secret, then derive symmetric session keys from it and the two random values. **Finished** messages, carrying a MAC of the whole handshake, prove nothing was tampered with. After that, application data is encrypted with AES-GCM or ChaCha20. **TLS 1.3** cuts this to one round trip: the key share goes in the ClientHello, old insecure ciphers and RSA key exchange are removed, forward secrecy is mandatory, and 0-RTT resumption is supported. In microservices, mTLS adds a client certificate, which a service mesh such as Istio typically handles.''',
["Uber", "Razorpay", "PhonePe", "Atlassian"]),

T("What are your REST API design best practices?",
'''Model **resources as nouns** with HTTP verbs: `GET /orders/{id}`, `POST /orders`, `PATCH /orders/{id}`. Return **correct status codes**: 201 with a Location header on create, 204 for an empty response, 400 or 422 for validation errors, 401 vs 403, 404, 409 for conflicts, 429 when rate-limited. Use a consistent error body such as `{code, message, details, traceId}` from a `@ControllerAdvice`. Keep PUT and DELETE **idempotent**, and accept an `Idempotency-Key` for POSTs that charge money. **Paginate** lists, with cursor-based pagination for large or fast-changing data, and support filtering and sorting through query parameters. **Version** the API in the path or a header. Validate input with `@Valid`. Never expose JPA entities directly; map them to DTOs. Secure endpoints with OAuth2/JWT and rate limiting. Document them with OpenAPI/Swagger, and use ETags or Cache-Control for cacheable GETs.''',
["Atlassian", "Razorpay", "Uber", "Swiggy"]),

T("How would you design a rate limiter for an API that runs on many servers?",
'''Start with the requirements: the limit key (user, API key or IP), the rules (for example 100 requests per minute per API key), hard or soft limits, and very low added latency. **Algorithm:** token bucket (allows bursts, O(1) state) or sliding-window counter (accurate and cheap); a sliding-window log is exact but memory-heavy. **Placement:** an API gateway or a filter (Spring `OncePerRequestFilter` or Bucket4j). **Distributed state:** in-memory counters per server are inaccurate behind a load balancer, so use a central **Redis**. Use `INCR` with `EXPIRE` for fixed windows, or a **Lua script** that atomically refills and takes a token, so there is no race between read and write. A sorted set of timestamps works for a sliding-window log. **Response:** HTTP 429 with `Retry-After` and `X-RateLimit-Remaining` headers. **Resilience:** decide whether to fail open if Redis is down, and shard Redis by key.''',
["Atlassian", "Uber", "Razorpay", "Flipkart"]),

T("Which data structures does an LRU cache use, and what are the pros and cons of hash-based structures?",
'''An LRU cache combines a **HashMap** (key to node) for O(1) lookup with a **doubly linked list** that keeps recency order. Accessing a node moves it to the head, and eviction removes the tail, both O(1) pointer operations. In Java, `LinkedHashMap` with `accessOrder = true` and `removeEldestEntry` gives you this out of the box. **Pros of hashing:** average O(1) insert, lookup and delete, and simple key-based access. **Cons:** O(n) worst case under heavy collisions or adversarial keys (Java 8 limits this with tree bins), no ordering (range queries need a TreeMap), memory overhead from load factor and node objects, occasional costly rehash pauses, and dependence on a good, stable `hashCode`, since mutable keys break the map. A candidate reported this exact question in an Atlassian round, together with "design an in-memory cache for a stream of integers".''',
["Atlassian", "Uber", "Swiggy", "Amazon"]),
]

DAY = build(6, "Atlassian & Uber", "Design-heavy coding (LRU cache, rate limiter, snapshot array, code-design problems) from Atlassian and Uber rounds, plus computer-networks and system-design MCQs.", mcqs, coding, theory)
