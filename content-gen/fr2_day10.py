from fr2_common import M, C, T, save

mcqs = [
M("Heaps", '''What is the time complexity of building a binary heap from n unsorted elements using bottom-up heapify?''',
["O(n log n)", "O(n)", "O(log n)", "O(n²)"], 1,
'''Most nodes sit near the bottom and sift down only a short distance. Adding up the work, Σ (n/2^(h+1)) · h, gives O(n). Inserting the n elements one at a time would cost O(n log n). Java's `PriorityQueue(Collection)` constructor uses the O(n) heapify.''', ["Uber", "Amazon"]),

M("Java Output", r'''
What does this print?
```java
PriorityQueue<Integer> pq = new PriorityQueue<>(List.of(5, 1, 4, 2, 3));
System.out.println(pq.peek() + " " + pq);
```''', ["1 [1, 2, 3, 4, 5]", "1 [1, 2, 4, 5, 3]", "5 [5, 1, 4, 2, 3]", "1 [5, 1, 4, 2, 3]"], 1,
'''`toString()` prints the internal heap array, which is not sorted. Heapify sifts down index 1 (which stays) and then index 0: 5 swaps with 1, then with 2, leaving [1,2,4,5,3]. Only `peek()` and `poll()` guarantee the minimum.''', ["Swiggy", "Uber"]),

M("Heaps", '''You need the k largest values from a stream of n numbers, using as little memory as possible. What is the best approach?''',
["Sort everything: O(n log n) time, O(n) space", "A min-heap of size k: O(n log k) time, O(k) space",
 "A max-heap of all n elements", "A HashMap"], 1,
'''Keep a min-heap capped at k elements. If a new value is larger than the heap's top, the smallest of the current top-k, replace the top. The heap then holds exactly the k largest. This works on unbounded streams, such as top-rated restaurants in real time.''', ["Zomato", "Swiggy", "Amazon"]),

M("Intervals / Greedy", '''Balloons span the x-ranges `[[10,16],[2,8],[1,6],[7,12]]`. An arrow shot at x bursts every balloon whose range contains x. What is the minimum number of arrows needed?''',
["1", "2", "3", "4"], 1,
'''Sort by end: [1,6],[2,8],[7,12],[10,16]. Shoot at 6, which bursts the first two. The next balloon not yet burst is [7,12], so shoot at 12, which also gets [10,16]. That's 2 arrows. Greedy on the earliest end is optimal (LC 452).''', ["Uber", "Swiggy"]),

M("Greedy", '''To pick the maximum number of non-overlapping meetings (activity selection), what should you sort by?''',
["Start time", "Duration", "End time", "Number of attendees"], 2,
'''Choosing the meeting that ends earliest leaves the most room for the rest. An exchange argument shows this is optimal. Sorting by start time or by shortest duration both have counterexamples.''', ["Swiggy", "Zomato", "Flipkart"]),

M("Intervals", '''After merging all overlapping or touching intervals in `[[1,4],[4,5],[6,8],[7,7]]`, how many intervals are left?''',
["1", "2", "3", "4"], 1,
'''[1,4] and [4,5] touch at 4, which counts as overlapping, giving [1,5]. [7,7] lies inside [6,8]. The result is [[1,5],[6,8]]. Sort by start, then extend the last merged interval whenever `start <= lastEnd`.''', ["Zomato", "Swiggy", "Uber"]),

M("System Design", '''A food delivery app has to find available delivery partners within 3 km of a restaurant, out of millions of moving points. Which technique fits best?''',
["A full table scan with the haversine formula", "Geospatial indexing such as geohash, quadtree or Google S2 (for example Redis GEO)",
 "A B-tree index on latitude only", "A Bloom filter"], 1,
'''A geohash or S2 maps 2D coordinates to cell IDs, so nearby points share prefixes or cells. You query the target cell and its neighbors, then filter by exact distance. Redis GEOADD/GEOSEARCH handles frequent location updates well.''', ["Swiggy", "Uber", "Zomato"]),

M("System Design", '''A rider app shows the driver's live location, updated every 2 to 4 seconds. Which client-server mechanism is most efficient?''',
["The client polls a REST endpoint every second", "A persistent WebSocket (or SSE) connection that pushes updates from a pub/sub backend",
 "Email notifications", "Batch export every hour"], 1,
'''Short polling wastes requests and still lags behind. A persistent connection lets the server push each new location the moment it arrives, often fanned out through Redis Pub/Sub or Kafka. Uber and Swiggy describe this kind of push gateway in their engineering blogs.''', ["Uber", "Swiggy"]),

M("Caching", '''Restaurant menus are read millions of times and change only a few times a day. Which caching approach is the best fit?''',
["No cache", "Cache-aside (lazy loading) with a TTL, plus evicting the key when the menu is updated",
 "Write-around with no TTL", "Caching only in the browser"], 1,
'''With cache-aside, the app reads from the cache and on a miss loads from the DB and fills the cache. A TTL caps how stale data can get, and deleting the key on update gives near-immediate freshness. Use request coalescing or jittered TTLs to avoid stampedes.''', ["Zomato", "Swiggy"]),

M("CAP Theorem", '''During a network partition, a ride-tracking store keeps accepting writes on both sides and reconciles them later. Under CAP, what did it choose?''',
["CP: consistency over availability", "AP: availability over consistency (eventual consistency)", "CA", "None of these"], 1,
'''Accepting writes everywhere during a partition puts availability first. The replicas converge afterwards, through last-write-wins or CRDTs for example. Cassandra and DynamoDB-style stores lean AP. Systems like ZooKeeper or etcd are CP.''', ["Uber", "Swiggy"]),

M("Load Balancing", '''Requests to `/api/orders/*` must go to the order service and `/api/menu/*` to the menu service. Which load balancer can do that?''',
["L4 (TCP) load balancer", "L7 (HTTP) load balancer / API gateway", "A DNS round-robin", "A Layer-2 switch"], 1,
'''Only a Layer-7 balancer looks inside the HTTP request: path, headers and cookies. That lets it route by content and terminate TLS. L4 balancers route on IP and port only, which makes them faster but unaware of URLs.''', ["Swiggy", "Zomato"]),

M("Kafka", '''Order status events (PLACED → PREPARED → PICKED → DELIVERED) must be processed in sequence for each order. How do you get that ordering in Kafka?''',
["Use one consumer for the whole cluster", "Use orderId as the message key, so all of an order's events go to the same partition, where order is preserved",
 "Kafka orders messages globally by default", "Use a random key"], 1,
'''Kafka only guarantees order within a partition. Keying by orderId hashes every event for an order to one partition, which one consumer in the group reads in order. You keep parallelism across different orders.''', ["Swiggy", "Zomato", "Uber"]),

M("Java Output", r'''
What does this print?
```java
TreeMap<Integer, String> t = new TreeMap<>(Map.of(10, "a", 20, "b", 30, "c"));
System.out.println(t.floorKey(25) + " " + t.ceilingKey(25) + " "
    + t.headMap(20) + " " + t.firstEntry().getValue());
```''', ["20 30 {10=a, 20=b} a", "20 30 {10=a} a", "30 20 {10=a} a", "25 25 {10=a} a"], 1,
'''floorKey returns the greatest key ≤ 25, which is 20. ceilingKey returns the smallest key ≥ 25, which is 30. `headMap(20)` excludes 20 by default. TreeMap is useful for things like "nearest available slot" lookups in O(log n).''', ["Uber", "Swiggy"]),

M("Java Output", r'''
What does this print?
```java
Integer[] a = {Integer.MIN_VALUE, 1, -1};
Arrays.sort(a, (x, y) -> x - y);
System.out.println(Arrays.toString(a));
```''', ["[-2147483648, -1, 1]", "[-1, 1, -2147483648]", "[1, -1, -2147483648]", "IllegalArgumentException"], 1,
'''`1 - MIN_VALUE` overflows to a negative number, so the comparator claims 1 < MIN_VALUE. TimSort sees a descending run and reverses it, producing a wrong order. Always use `Integer.compare(x, y)` or `Comparator.naturalOrder()`.''', ["Uber", "Google"]),

M("SQL", r'''
You want restaurants whose average rating is above 4. What happens with this query?
```sql
SELECT restaurant_id, AVG(rating) FROM reviews
WHERE AVG(rating) > 4
GROUP BY restaurant_id;
```''', ["It works correctly", "It fails, because aggregates aren't allowed in WHERE. Use HAVING AVG(rating) > 4 after GROUP BY",
 "It returns all rows", "It returns only one row"], 1,
'''WHERE filters rows before grouping, so aggregates don't exist yet at that point. HAVING filters the groups after aggregation. The logical order is FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY.''', ["Zomato", "Swiggy"]),

M("DBMS Indexing", '''A table has a composite index on `(city, cuisine)`. Which query can use the index efficiently for lookup?''',
["WHERE cuisine = 'Thai'", "WHERE city = 'Pune' AND cuisine = 'Thai'", "WHERE cuisine LIKE '%ai'", "WHERE UPPER(city) = 'PUNE'"], 1,
'''B-tree composite indexes follow the leftmost-prefix rule: the leading column(s) must be constrained. Filtering on `cuisine` alone, using a leading wildcard, or wrapping the column in a function all prevent an index seek.''', ["Zomato", "Swiggy", "Flipkart"]),

M("Operating Systems", '''With 3 frames and LRU replacement, how many page faults does the reference string `7, 0, 1, 2, 0, 3, 0, 4` cause?''',
["5", "6", "7", "8"], 1,
'''7, 0 and 1 fault (3). 2 faults and evicts 7 (4). 0 hits. 3 faults and evicts 1 (5). 0 hits. 4 faults and evicts 2, the least recently used (6). Total: 6 faults.''', ["Uber", "Oracle"]),

M("Computer Networks", '''Which transport protocol and port do DNS queries normally use?''',
["TCP 80", "UDP 53, falling back to TCP 53 for large responses or zone transfers", "UDP 67", "TCP 443 only"], 1,
'''Small query/response exchanges fit in one UDP datagram, which avoids handshake latency. TCP 53 is used when responses are truncated (the TC bit is set) and for AXFR zone transfers. DoH and DoT carry DNS over HTTPS or TLS.''', ["Swiggy", "Microsoft"]),

M("Aptitude", '''A rider goes to a restaurant at 30 km/h and returns the same distance at 20 km/h. What is the average speed for the round trip?''',
["25 km/h", "24 km/h", "22 km/h", "26 km/h"], 1,
'''For equal distances, the average speed is the harmonic mean: 2·30·20 / (30 + 20) = 1200/50 = 24 km/h. The arithmetic mean of 25 is wrong because the rider spends more time at the slower speed.''', ["Swiggy", "Zomato"]),

M("Probability", '''Three orders are each late independently with probability 0.2. What is the probability that at least one is late?''',
["0.6", "0.488", "0.512", "0.2"], 1,
'''P(none late) = 0.8³ = 0.512. So P(at least one late) = 1 − 0.512 = 0.488. For "at least one" questions, calculating the complement is almost always quicker.''', ["Zomato", "Uber"]),
]

coding = [
C("Meeting Rooms II (Minimum Rooms / Delivery Slots)", "Medium", ["Uber", "Swiggy", "Google", "Amazon"], r'''
You get a list of time intervals `[start, end)`, such as meetings or delivery-agent bookings. Return the minimum number of rooms (or agents) needed so that no two overlapping intervals share one.

**Example 1**
```
Input:  [[0,30],[5,10],[15,20]]
Output: 2
```
**Example 2**
```
Input:  [[7,10],[2,4]]
Output: 1
```
An interval ending at time t and another starting at t do **not** overlap.

**Constraints:** 1 ≤ n ≤ 10^4, 0 ≤ start < end ≤ 10^6''',
["Sort by start time. Keep a min-heap holding the end times of rooms in use.",
 "If the earliest-ending room is free (end ≤ current start), reuse it by popping. The heap's size is the answer."],
r'''
import java.util.*;

class Solution {
    public int minMeetingRooms(int[][] intervals) {
        Arrays.sort(intervals, Comparator.comparingInt(a -> a[0]));
        PriorityQueue<Integer> ends = new PriorityQueue<>();
        for (int[] in : intervals) {
            if (!ends.isEmpty() && ends.peek() <= in[0]) {
                ends.poll();            // reuse the room that frees up first
            }
            ends.offer(in[1]);
        }
        return ends.size();
    }
}''',
'''After sorting by start time, the heap holds the end times of rooms currently booked. For each new interval, the only room worth checking is the one that frees up earliest, at the heap's top. If it's free by the new start time, we reuse it (poll, then offer the new end). Otherwise we open a new room. The heap never shrinks below the peak overlap, so its final size is the answer. A sweep-line version also works: sort the starts and ends into two separate arrays and walk them with two pointers, counting how many intervals are active. Uber and Swiggy candidates report it in contexts like "minimum number of drivers" or "parking slots needed".''',
"O(n log n)", "O(n)", "https://leetcode.com/problems/meeting-rooms-ii/"),

C("K Closest Delivery Partners (K Closest Points to Origin)", "Medium", ["Uber", "Swiggy", "Amazon", "Zomato"], r'''
You get `points[i] = [x, y]`, the positions of delivery partners relative to a restaurant at the origin, and an integer `k`. Return the `k` points closest to the origin by Euclidean distance. They can be in any order.

**Example 1**
```
Input:  points = [[1,3],[-2,2]], k = 1
Output: [[-2,2]]      // sqrt(8) < sqrt(10)
```
**Example 2**
```
Input:  points = [[3,3],[5,-1],[-2,4]], k = 2
Output: [[3,3],[-2,4]]
```
**Constraints:** 1 ≤ k ≤ n ≤ 10^4, −10^4 ≤ x, y ≤ 10^4''',
["Compare squared distances. You don't need sqrt.",
 "Keep a max-heap of size k. When it grows beyond k, remove the farthest point."],
r'''
import java.util.*;

class Solution {
    public int[][] kClosest(int[][] points, int k) {
        // max-heap by squared distance
        PriorityQueue<int[]> heap = new PriorityQueue<>(
            (a, b) -> Long.compare(dist(b), dist(a)));
        for (int[] p : points) {
            heap.offer(p);
            if (heap.size() > k) heap.poll();   // drop the farthest
        }
        int[][] res = new int[k][];
        for (int i = 0; i < k; i++) res[i] = heap.poll();
        return res;
    }

    private long dist(int[] p) {
        return (long) p[0] * p[0] + (long) p[1] * p[1];
    }
}''',
'''A max-heap capped at k keeps the k closest points seen so far, with the farthest of them on top, ready to be evicted. Each point costs O(log k), so the total is O(n log k). That's better than sorting when k is much smaller than n, and it works on a stream of location updates. Squared distance keeps the ordering, avoids floating point, and fits easily in a `long`. A `Long.compare` comparator avoids the subtraction-overflow bug. An alternative is **Quickselect**, which runs in O(n) on average but O(n²) in the worst case and needs all points in memory. In a real system the follow-up is usually how to find candidate partners quickly in the first place, using geohash or S2 cells.''',
"O(n log k)", "O(k)", "https://leetcode.com/problems/k-closest-points-to-origin/"),

C("Car Pooling", "Medium", ["Uber", "Swiggy", "Amazon"], r'''
A vehicle with `capacity` seats drives east only. `trips[i] = [numPassengers, from, to]` means that many passengers get in at km `from` and out at km `to`. Return `true` if every trip can be served without ever going over capacity.

**Example 1**
```
Input:  trips = [[2,1,5],[3,3,7]], capacity = 4
Output: false     // between km 3 and 5 there are 5 passengers
```
**Example 2**
```
Input:  trips = [[2,1,5],[3,5,7]], capacity = 3
Output: true      // drop-off at 5 happens before pick-up at 5
```
**Constraints:** 1 ≤ trips.length ≤ 1000, 1 ≤ numPassengers ≤ 100, 0 ≤ from < to ≤ 1000, 1 ≤ capacity ≤ 10^5''',
["Record only the changes: +p at `from` and −p at `to`.",
 "Locations are small (≤ 1000), so use a difference array and a running prefix sum. That's a sweep line."],
r'''
class Solution {
    public boolean carPooling(int[][] trips, int capacity) {
        int[] delta = new int[1001];
        for (int[] t : trips) {
            delta[t[1]] += t[0];   // pick up
            delta[t[2]] -= t[0];   // drop off
        }
        int onboard = 0;
        for (int d : delta) {
            onboard += d;
            if (onboard > capacity) return false;
        }
        return true;
    }
}''',
'''This is a **sweep line with a difference array**. Instead of adding passengers to every kilometre of a trip, we record +p at pick-up and −p at drop-off. A prefix sum over the array then gives the passenger count at each point. Because the drop-off at `to` and a pick-up at the same km fall into the same cell, the drop-off happens first automatically, which matches the half-open interval semantics. If coordinates were huge, such as timestamps, you would instead sort the events (ties going to drop-offs first) or use a TreeMap of deltas, giving O(n log n). Uber reportedly frames this as checking a shared-ride vehicle's feasibility. The same technique solves "My Calendar" and "Corporate Flight Bookings".''',
"O(n + maxLocation)", "O(maxLocation)", "https://leetcode.com/problems/car-pooling/"),

C("Minimum Number of Refueling Stops", "Hard", ["Uber", "Google", "Swiggy"], r'''
A car starts with `startFuel` litres and needs to travel `target` km, using 1 litre per km. `stations[i] = [position, fuel]` are sorted by position. Stopping at a station adds all of its fuel. Return the minimum number of stops needed to reach the target, or `-1` if it can't be reached.

**Example 1**
```
Input:  target = 100, startFuel = 10,
        stations = [[10,60],[20,30],[30,30],[60,40]]
Output: 2    // refuel at 10 (60L) and at 60 (40L)
```
**Example 2**
```
Input:  target = 100, startFuel = 1, stations = [[10,100]]
Output: -1
```
**Constraints:** 1 ≤ target, startFuel ≤ 10^9, 0 ≤ stations.length ≤ 500, positions strictly increasing and < target''',
["Drive as far as possible. Remember every station you passed as a stop you could have made.",
 "When you run out, retroactively refuel at the passed station with the most fuel, using a max-heap. Each refuel counts as one stop."],
r'''
import java.util.*;

class Solution {
    public int minRefuelStops(int target, int startFuel, int[][] stations) {
        PriorityQueue<Integer> passed = new PriorityQueue<>(Collections.reverseOrder());
        long reach = startFuel;
        int stops = 0, i = 0;
        while (reach < target) {
            // add every station we can already reach
            while (i < stations.length && stations[i][0] <= reach) {
                passed.offer(stations[i][1]);
                i++;
            }
            if (passed.isEmpty()) return -1;     // stuck
            reach += passed.poll();              // best retroactive refuel
            stops++;
        }
        return stops;
    }
}''',
'''The greedy idea is to **postpone the decision**. As we drive, every station within reach goes into a max-heap of fuel amounts. Only when we can't go further do we "go back in time" and refuel at the best station we passed, the one with the most fuel. Each stop is chosen to extend our reach as much as possible. An exchange argument shows no other choice of k stops can reach further than the greedy's k stops. If the heap is empty while we still haven't reached the target, it's impossible. An O(n²) DP also works, where `dp[k]` is the farthest distance reachable with k stops. Mention it as an alternative. Uber candidates report this as a "minimize stops on a route" problem.''',
"O(n log n)", "O(n)", "https://leetcode.com/problems/minimum-number-of-refueling-stops/"),
]

theory = [
T("How would you design a 'nearby restaurants / nearby drivers' service?", '''**Requirements:** find entities within radius R of a user, at low latency (under 100 ms), while drivers send location updates every few seconds (very write-heavy).

**Indexing:** use a **geohash** or **Google S2** cell ID. Points that are close together share a prefix or cell. For a query, compute the user's cell plus its 8 neighbors, fetch candidates, filter by exact haversine distance, then rank by distance, ETA or rating.

**Storage:**
- Restaurants are mostly static: Elasticsearch geo_point or PostGIS.
- Drivers change constantly: **Redis GEO** (GEOADD/GEOSEARCH), sharded by city, with a short TTL so offline drivers drop out.

**Pipeline:** driver app → WebSocket gateway → Kafka (keyed by driverId) → location service → Redis.

**Scale:** partition by city or region, pick the cell precision based on density, and cache popular query results for a few seconds.''', ["Swiggy", "Uber", "Zomato"]),

T("Explain how a binary heap / Java PriorityQueue works and its complexities.", '''A binary heap is a **complete binary tree stored in an array**. Node i has children at 2i+1 and 2i+2, and its parent is at (i−1)/2. In a min-heap, every parent is ≤ its children, so the minimum is at index 0.

- `offer`: add at the end, then **sift up**. O(log n).
- `poll`: move the last element to the root, then **sift down**. O(log n).
- `peek`: O(1).
- `remove(Object)` and `contains`: O(n), because a linear search is needed.
- Building a heap from a collection: O(n) with bottom-up heapify.

Java's `PriorityQueue` is a min-heap by default. Pass `Comparator.reverseOrder()` for a max-heap. It isn't thread-safe (use `PriorityBlockingQueue`), its iterator and toString aren't in sorted order, and it has no decrease-key. In Dijkstra, push a new entry and skip stale ones instead. Typical uses: top-k, merging k sorted lists, scheduling, running medians.''', ["Uber", "Swiggy", "Amazon"]),

T("Greedy vs dynamic programming: how do you know greedy will work?", '''Greedy commits to the locally best choice and never revisits it. It's correct only when the problem has:
1. **The greedy-choice property**: some optimal solution includes the greedy choice.
2. **Optimal substructure**: once that choice is made, the rest is a smaller instance of the same problem.

To be confident, use an **exchange argument**: take any optimal solution and show you can swap in the greedy choice without making it worse. Activity selection by earliest end time, Huffman coding and fractional knapsack all pass. **0/1 knapsack** and **coin change with arbitrary denominations** fail. For example, with coins {1, 3, 4} and amount 6, greedy picks 4+1+1 (3 coins) but 3+3 (2 coins) is optimal.

In interviews: propose greedy, then try to break it with a small counterexample. If you can break it, switch to DP, which explores every choice through overlapping subproblems.''', ["Zomato", "Swiggy", "Amazon"]),

T("Design real-time order tracking with ETA updates for a food delivery app.", '''**Flow:** order placed → restaurant accepts → partner assigned → picked up → delivered. Each transition is an **event** published to Kafka (keyed by orderId so events stay in order) by an order service that runs a state machine.

**Live location:** the partner app sends GPS every 3–5 seconds over a persistent connection → location service → Redis (latest position) plus Kafka for analytics.

**Push to the customer:** a WebSocket/SSE gateway subscribes to updates for that order (through Redis Pub/Sub) and pushes the status, map position and ETA. Mobile push notifications (FCM/APNs) cover milestones when the app is in the background.

**ETA:** an ETA service combines road-network routing, live traffic, the restaurant's prep-time model and historical data. It recomputes on significant location changes.

**Reliability:** idempotent event consumers, a fallback to polling if the socket drops, and graceful degradation (show the last known status).''', ["Swiggy", "Zomato", "Uber"]),

T("Explain caching strategies and how you avoid cache stampede / thundering herd.", '''**Strategies:**
- *Cache-aside*: the app reads the cache, and on a miss loads from the DB and fills the cache.
- *Read-through / write-through*: the cache layer loads and writes to the DB synchronously, so data stays fresher.
- *Write-behind*: write to the cache, and the DB is updated asynchronously. Fast, but writes can be lost.
- *Write-around*: writes skip the cache.

**Invalidation:** use a TTL plus explicit deletion when the source data changes. Delete the key rather than updating it, to avoid race conditions.

**Stampede:** a hot key expires and thousands of requests hit the DB at once. Fixes:
1. **Request coalescing / mutex**: only one request recomputes, using a Redis `SET NX` lock, and the rest wait or get the stale value.
2. **Jittered TTLs**, so keys don't all expire together.
3. **Refresh ahead of expiry** (proactive refresh).
4. **Serve stale while revalidating** in the background.''', ["Zomato", "Swiggy", "Flipkart"]),

T("What is database sharding and how do you choose a shard key?", '''**Sharding** splits one logical dataset across several database nodes by rows, so the system can scale writes and storage beyond what a single machine handles.

**Strategies:** *range-based* (by date or ID range, which is easy to query but creates hot spots), *hash-based* (even distribution, but range queries become harder), *directory/lookup-based* (flexible, but the lookup table must be highly available), and *geo-based* (by city, which suits Swiggy and Uber).

**A good shard key:**
1. Has high cardinality and spreads evenly.
2. Matches the **main access pattern**, so most queries hit a single shard. For example, shard orders by `customer_id` when "my orders" is the dominant query.
3. Avoids hot spots, such as a monotonically increasing timestamp.

**Costs:** cross-shard joins and transactions, resharding (consistent hashing helps), globally unique IDs (Snowflake), and fan-out queries for secondary lookups.''', ["Uber", "Swiggy", "Flipkart"]),
]

save(10, "Swiggy, Zomato & Uber (Consumer Tech)",
     "Consumer-tech rounds built around heaps, intervals, greedy algorithms and the system design ideas behind delivery and ride-hailing apps.",
     mcqs, coding, theory)
