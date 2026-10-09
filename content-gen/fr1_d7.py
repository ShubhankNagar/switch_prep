from fr1_common import M, C, T, build

mcqs = [
M("DSA", '''What is the time complexity of searching for a target in a sorted array that has been rotated at an unknown pivot (distinct values)?''',
["O(n)", "O(log n)", "O(n log n)", "O(sqrt n)"], 1,
'''A modified binary search works: at each step at least one half, either [lo, mid] or [mid, hi], is sorted. Check whether the target falls inside the sorted half's range and discard the other half. With duplicates, the worst case degrades to O(n).''',
["Amazon", "Microsoft", "Adobe"]),

M("DSA", '''Which sorting algorithm is BOTH stable and guaranteed O(n log n) in the worst case?''',
["Quick sort", "Heap sort", "Merge sort", "Selection sort"], 2,
'''Merge sort is stable and always O(n log n), at the cost of O(n) extra space. Quick sort is O(n^2) in the worst case and not stable. Heap sort is O(n log n) but not stable. Java sorts objects with TimSort, a stable merge-sort hybrid, and primitives with dual-pivot quicksort.''',
["Microsoft", "Oracle", "Walmart"]),

M("DSA", '''To find the kth largest element in a stream of n numbers, you keep a min-heap of size k. What is the total time complexity?''',
["O(n log n)", "O(n log k)", "O(k log n)", "O(n + k)"], 1,
'''Each element costs at most one offer and one poll on a heap of size k, which is O(log k), so the total is O(n log k) with O(k) memory. The heap's top is always the kth largest seen so far. Quickselect averages O(n) but needs the whole array in memory.''',
["Amazon", "Flipkart", "Swiggy"]),

M("Java streams", '''What does this print?
```java
Stream.of(1, 2, 3, 4)
      .filter(x -> { System.out.print(x); return x % 2 == 0; })
      .findFirst();
```''', ["1234", "12", "2", "Nothing"], 1,
'''Streams are lazy and process elements one at a time through the pipeline. `findFirst` short-circuits: 1 fails the filter, 2 passes and is returned, so 3 and 4 are never pulled. The output is "12". Without a terminal operation, nothing would print at all.''',
["Walmart", "Swiggy", "Paytm"]),

M("Java core", '''Which statement about `record Point(int x, int y) {}` (Java 16+) is TRUE?''',
["Its fields can be reassigned with setters", "It automatically gets a canonical constructor, accessors x() and y(), and equals, hashCode and toString; its fields are private final",
 "It can extend another class", "It cannot implement interfaces"], 1,
'''Records are transparent, immutable data carriers. They are implicitly final, already extend `java.lang.Record` (so they cannot extend anything else), may implement interfaces, and can add compact constructors for validation. They are ideal for DTOs, but not for JPA entities, which need a no-args constructor and mutability.''',
["Atlassian", "Razorpay"]),

M("Spring Boot", '''A prototype-scoped bean is injected via `@Autowired` into a singleton bean. What happens on every call to the singleton?''',
["A new prototype instance is created on every method call", "The same prototype instance (injected once at startup) is reused",
 "Spring throws an exception at startup", "The prototype becomes request-scoped"], 1,
'''Injection happens only once, when the singleton is created, so it holds a single prototype instance forever. To get a fresh instance each time, inject `ObjectProvider<T>` (or `Provider<T>`) and call `getObject()`, use `@Lookup` method injection, or use a scoped proxy.''',
["Walmart", "Oracle", "PhonePe"]),

M("Spring Boot", '''`@Transactional` is placed on a PRIVATE method of a Spring bean (default proxy-based AOP). What is the effect?''',
["The method runs in a transaction", "No transaction is applied, because proxies only intercept public methods called from outside the bean",
 "The application fails to start", "A transaction is applied only when the method throws"], 1,
'''Spring's proxies intercept external calls to public methods (Spring 6 also allows protected and package-private methods with class-based proxies). Private methods and self-invocation through `this` bypass the proxy, so the annotation is silently ignored. Put transactional logic on public methods of a separate service, or use AspectJ weaving.''',
["PhonePe", "Razorpay", "Walmart", "Paytm"]),

M("Spring Boot", '''By default, which exceptions cause a `@Transactional` method to ROLL BACK?''',
["All exceptions", "Only checked exceptions", "Unchecked exceptions (RuntimeException and Error); checked exceptions commit by default",
 "Only SQLException"], 2,
'''Spring follows the EJB convention: a RuntimeException or Error triggers rollback, while a checked exception such as IOException commits the transaction. Use `@Transactional(rollbackFor = Exception.class)` to roll back on checked exceptions. Catching and swallowing an exception inside the method also prevents rollback.''',
["Razorpay", "PhonePe", "Walmart"]),

M("Spring Boot", '''`@RestController` is equivalent to which combination?''',
["@Controller + @ResponseBody", "@Component + @RequestMapping", "@Service + @ResponseBody", "@Controller + @RequestBody"], 0,
'''With `@ResponseBody` applied to every handler method, return values are written straight to the HTTP response body through HttpMessageConverters (Jackson for JSON) instead of being resolved as view names. `@RequestBody` is a parameter annotation that binds the incoming body.''',
["Paytm", "Swiggy", "Oracle"]),

M("Spring Boot", '''`server.port` is set to 8081 in application.properties, to 8082 in an environment variable `SERVER_PORT`, and to 8083 via `--server.port=8083` on the command line. Which port is used?''',
["8081", "8082", "8083", "8080"], 2,
'''Spring Boot's externalized configuration has an order of precedence: command-line arguments override OS environment variables, which override application properties files packaged in the jar. This lets the same artifact run unchanged across dev, QA and prod.''',
["Walmart", "Swiggy"]),

M("JPA / Hibernate", '''You load 50 `Order` entities and then access `order.getItems()` (a LAZY `@OneToMany`) for each one inside a loop. How many SQL queries run, and what is this called?''',
["1, eager join", "51, the N+1 select problem", "50, batch fetching", "2, a Cartesian product"], 1,
'''There is one query for the orders and then one query per order for its items, which makes 51. Fix it with `JOIN FETCH` in JPQL, an `@EntityGraph`, `@BatchSize` or `hibernate.default_batch_fetch_size` (which uses IN queries), or a DTO projection. Detect it by enabling SQL logs or using Hibernate statistics.''',
["Swiggy", "Zomato", "Paytm", "Walmart"]),

M("JPA / Hibernate", '''What are the DEFAULT fetch types for `@ManyToOne` and `@OneToMany` in JPA?''',
["Both LAZY", "Both EAGER", "@ManyToOne EAGER, @OneToMany LAZY", "@ManyToOne LAZY, @OneToMany EAGER"], 2,
'''Single-valued associations (`@ManyToOne`, `@OneToOne`) default to EAGER, and collections (`@OneToMany`, `@ManyToMany`) default to LAZY. Best practice is to mark `@ManyToOne(fetch = LAZY)` explicitly and fetch what each use case needs, so eager chains do not run hidden queries.''',
["Paytm", "Walmart", "Oracle"]),

M("JPA / Hibernate", '''When does `LazyInitializationException` typically occur?''',
["When saving a new entity", "When a lazy association is accessed after the persistence context (session) has closed, for example in the controller or during JSON serialization",
 "When two transactions update the same row", "When an entity has no @Id"], 1,
'''A lazy proxy can load its data only while its session is open. Returning entities from a `@Transactional` service and serializing them later triggers the error. Fetch the needed data inside the transaction (JOIN FETCH or EntityGraph) and map it to DTOs. Avoid relying on Open Session in View.''',
["Swiggy", "Paytm", "PhonePe"]),

M("SQL", '''Which query correctly lists email addresses that appear more than once in `users`?''',
["SELECT email FROM users WHERE COUNT(email) > 1",
 "SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1",
 "SELECT DISTINCT email FROM users",
 "SELECT email, COUNT(*) FROM users ORDER BY 2 > 1"], 1,
'''Grouping by email collapses identical values, and HAVING filters on the aggregate count. Aggregates are not allowed in WHERE. To delete duplicates while keeping one row, use `ROW_NUMBER() OVER (PARTITION BY email ORDER BY id)` and delete rows with rn > 1, or a self-join on a smaller id.''',
["Amazon", "Walmart", "Oracle"]),

M("Operating systems", '''What is a zombie process?''',
["A process stuck in an infinite loop", "A child process that has terminated, but whose exit status has not yet been collected by its parent via wait()",
 "A process whose parent died, now adopted by init", "A process swapped out to disk"], 1,
'''The process table entry stays until the parent reads the exit code. Many zombies can exhaust PIDs. An orphan is the opposite case: a running child whose parent died, which init or systemd adopts and reaps. The fix for zombies is for the parent to call wait or handle SIGCHLD.''',
["Oracle", "Microsoft", "Goldman Sachs"]),

M("Computer networks", '''A browser re-requests a cached resource and sends `If-None-Match: "abc123"`. The resource has not changed. What does the server return?''',
["200 OK with the full body", "304 Not Modified with no body", "204 No Content", "412 Precondition Failed"], 1,
'''The ETag acts as a version fingerprint. If it still matches, the server replies 304 and the browser reuses its cached copy, which saves bandwidth. `Cache-Control: max-age` avoids the request entirely while the copy is fresh. Spring offers `ShallowEtagHeaderFilter` for ETag support.''',
["Atlassian", "Uber"]),

M("System design", '''Under the CAP theorem, which database is usually described as AP: it favours availability and becomes eventually consistent during a network partition?''',
["A single-node MySQL instance", "Apache Cassandra (with default tunable consistency)", "Apache ZooKeeper", "HBase"], 1,
'''During a partition, a distributed system must choose between consistency and availability. Cassandra (and DynamoDB-style stores) keeps accepting reads and writes and reconciles later. ZooKeeper and HBase choose consistency. Cassandra's consistency levels, such as QUORUM, let you move along that trade-off per query.''',
["Uber", "Atlassian", "Walmart"]),

M("System design", '''What ordering guarantee does Apache Kafka provide?''',
["Global ordering across all partitions of a topic", "Ordering within a single partition only; use the same key to keep related events together",
 "No ordering at all", "Ordering only for consumers in different groups"], 1,
'''Messages with the same key hash to the same partition and are appended in order, so a consumer reads them in sequence. Across partitions there is no global order. Example: key events by orderId so each order's status changes stay ordered while still scaling across many partitions.''',
["Swiggy", "Uber", "Flipkart", "PhonePe"]),

M("System design", '''You scale a Spring Boot app from 1 to 5 instances behind a round-robin load balancer, and users keep getting logged out. What is the BEST fix?''',
["Increase the server's heap", "Make the service stateless: use stateless JWT tokens or keep sessions in a shared store such as Redis (Spring Session)",
 "Disable the load balancer", "Use bigger machines (vertical scaling)"], 1,
'''HTTP sessions in local memory exist only on the instance that created them. Externalizing session state, or removing it with signed tokens, lets any instance handle any request, which is what makes horizontal scaling work. Sticky sessions are a stopgap that breaks when an instance dies.''',
["Flipkart", "Swiggy", "Walmart"]),

M("Aptitude", '''What is the next number in the series 2, 6, 12, 20, 30, ?''',
["40", "42", "44", "36"], 1,
'''The differences are 4, 6, 8, 10, so the next difference is 12, giving 30 + 12 = 42. Equivalently, each term is n(n + 1): 1x2, 2x3, 3x4, 4x5, 5x6, and then 6x7 = 42.''',
["Goldman Sachs", "Oracle", "Paytm"]),
]

coding = [
C("Best Time to Buy and Sell Stock", "Easy", ["Amazon", "Walmart", "Goldman Sachs", "Microsoft"],
'''`prices[i]` is a stock's price on day i. Choose one day to buy and a LATER day to sell so the profit is as large as possible, and return that profit. Return 0 if no profitable trade exists.

**Example**
```
Input:  [7,1,5,3,6,4]   Output: 5   // buy at 1, sell at 6
Input:  [7,6,4,3,1]     Output: 0
```
**Constraints**
- 1 <= prices.length <= 10^5
- 0 <= prices[i] <= 10^4''',
["For each selling day, the best buying day is the cheapest price seen so far.",
 "Track the running minimum and the best (price - min) in a single pass."],
r'''
class Solution {
    public int maxProfit(int[] prices) {
        int minPrice = Integer.MAX_VALUE, best = 0;
        for (int p : prices) {
            if (p < minPrice) minPrice = p;
            else best = Math.max(best, p - minPrice);
        }
        return best;
    }
}
''',
'''Trying every buy and sell pair is O(n^2). The useful observation is that selling on day i is best when you bought at the minimum price before day i. So one pass that tracks the running minimum and the best difference so far gives the answer in O(n) time and O(1) space. Mock tests often use this as the warm-up question, and then ask the variants: unlimited transactions (add every positive day-to-day difference), at most two transactions, k transactions, or a cooldown or transaction fee, all of which are state-machine DP. Explain the brute force briefly, then optimise, which is how interviewers expect you to work through it.''',
"O(n)", "O(1)", "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/"),

C("Number of Islands", "Medium", ["Amazon", "Microsoft", "Uber", "Walmart"],
'''Given an m x n grid of '1' (land) and '0' (water), count the islands. An island is a group of land cells connected horizontally or vertically. Assume everything outside the grid is water.

**Example**
```
Input:
[["1","1","0","0","0"],
 ["1","1","0","0","0"],
 ["0","0","1","0","0"],
 ["0","0","0","1","1"]]
Output: 3
```
**Constraints**
- 1 <= m, n <= 300''',
["Each time you find unvisited land, you have found a new island. Then mark its whole component as visited.",
 "Use DFS or BFS flood fill, sinking visited land to '0'. Union-Find also works."],
r'''
import java.util.*;

class Solution {
    public int numIslands(char[][] grid) {
        int m = grid.length, n = grid[0].length, islands = 0;
        int[][] dirs = {{1,0},{-1,0},{0,1},{0,-1}};
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                if (grid[i][j] != '1') continue;
                islands++;
                Deque<int[]> stack = new ArrayDeque<>();     // iterative DFS
                stack.push(new int[]{i, j});
                grid[i][j] = '0';
                while (!stack.isEmpty()) {
                    int[] c = stack.pop();
                    for (int[] d : dirs) {
                        int r = c[0] + d[0], col = c[1] + d[1];
                        if (r >= 0 && r < m && col >= 0 && col < n && grid[r][col] == '1') {
                            grid[r][col] = '0';
                            stack.push(new int[]{r, col});
                        }
                    }
                }
            }
        }
        return islands;
    }
}
''',
'''This means counting connected components on an implicit graph. Scan every cell. When you find land that has not been visited, add one to the count and flood-fill its whole island so it is not counted again. "Sinking" cells to '0' marks them visited without an extra matrix. If changing the input is not allowed, use a `boolean[][]` instead. The iterative stack avoids StackOverflowError on a 300x300 grid that is all land, which is a point worth raising, since recursive DFS could reach a depth of 90,000. Follow-ups: number of distinct island shapes, max area of an island, islands added over time (Union-Find, "Number of Islands II"), and counting with diagonal connectivity.''',
"O(m * n)", "O(m * n) worst case for the stack", "https://leetcode.com/problems/number-of-islands/"),

C("Kth Largest Element in an Array", "Medium", ["Amazon", "Flipkart", "Microsoft", "Swiggy"],
'''Given an integer array `nums` and an integer `k`, return the kth largest element in sorted order (not the kth distinct element). Try to do better than sorting.

**Example**
```
Input:  nums = [3,2,1,5,6,4], k = 2         Output: 5
Input:  nums = [3,2,3,1,2,4,5,5,6], k = 4   Output: 4
```
**Constraints**
- 1 <= k <= nums.length <= 10^5
- -10^4 <= nums[i] <= 10^4''',
["A min-heap that keeps only the k largest elements seen so far has the answer at its top.",
 "For an O(n) average, use Quickselect: partition around a random pivot and recurse into one side only."],
r'''
import java.util.*;

class Solution {
    public int findKthLargest(int[] nums, int k) {
        PriorityQueue<Integer> minHeap = new PriorityQueue<>(k + 1);
        for (int x : nums) {
            minHeap.offer(x);
            if (minHeap.size() > k) minHeap.poll();   // drop smallest
        }
        return minHeap.peek();
    }
}
''',
'''The min-heap keeps the k largest values seen so far, and its root is the smallest of them, which is the kth largest. Each element costs O(log k), so the total is O(n log k) with O(k) memory, and it also works on streams. That is the "Kth Largest Element in a Stream" design question. Quickselect, the partition step of quicksort with a random pivot, recurses into only the side that contains index n - k. It averages O(n) time and O(1) space, but it is O(n^2) in the worst case and needs the whole array. Given the value range here (-10^4 to 10^4), a counting sort is O(n + range). Mention all three and their trade-offs.''',
"O(n log k)", "O(k)", "https://leetcode.com/problems/kth-largest-element-in-an-array/"),

C("Merge k Sorted Lists", "Hard", ["Amazon", "Microsoft", "Uber", "Google"],
'''You are given an array of `k` linked lists, each sorted in ascending order. Merge them into one sorted linked list and return its head.

**Example**
```
Input:  [[1,4,5],[1,3,4],[2,6]]
Output: 1->1->2->3->4->4->5->6
Input:  []        Output: null
```
**Constraints**
- 0 <= k <= 10^4
- total nodes N <= 10^4; each list sorted ascending''',
["Merging the lists one by one costs O(kN). Can you always pick the smallest current head quickly?",
 "Put each list's head in a min-heap ordered by value; pop the smallest, append it, then push its next node."],
r'''
import java.util.*;

/* class ListNode { int val; ListNode next; ListNode(int v) { val = v; } } */
class Solution {
    public ListNode mergeKLists(ListNode[] lists) {
        PriorityQueue<ListNode> pq = new PriorityQueue<>(Comparator.comparingInt(n -> n.val));
        for (ListNode head : lists) if (head != null) pq.offer(head);
        ListNode dummy = new ListNode(0), tail = dummy;
        while (!pq.isEmpty()) {
            ListNode smallest = pq.poll();
            tail.next = smallest;
            tail = smallest;
            if (smallest.next != null) pq.offer(smallest.next);
        }
        return dummy.next;
    }
}
''',
'''The heap always holds at most one node from each list, namely its current head, so the global minimum is at the top. Each of the N nodes is pushed and popped once at O(log k), giving O(N log k). The alternative is divide and conquer: merge the lists in pairs, as in the merge step of merge sort, over log k rounds, which is also O(N log k) with O(1) extra space apart from recursion. Merging the lists one by one is O(kN), and interviewers expect you to explain why that is worse. This is the same pattern as external sorting, merging sorted log files from many servers, and the merge step of LSM-tree compaction, a good link for a design follow-up.''',
"O(N log k)", "O(k) for the heap", "https://leetcode.com/problems/merge-k-sorted-lists/"),
]

theory = [
T("How does Spring Boot auto-configuration work?",
'''`@SpringBootApplication` includes `@EnableAutoConfiguration`, which imports the auto-configuration classes listed in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (earlier versions used `spring.factories`). Each class is an ordinary `@Configuration` guarded by **conditions**: `@ConditionalOnClass` (for example, configure a DataSource only if a JDBC driver and HikariCP are on the classpath), `@ConditionalOnMissingBean` (back off if you defined your own bean), `@ConditionalOnProperty`, and `@ConditionalOnWebApplication`. Starters such as `spring-boot-starter-web` just bring in dependencies; their presence on the classpath triggers configurations like the embedded Tomcat and Jackson setup. Values come from `@ConfigurationProperties` bound to `application.yml`. To debug, run with `--debug` to see the condition evaluation report, or use the Actuator `/conditions` endpoint. To customize, define your own bean or exclude a class with `exclude = DataSourceAutoConfiguration.class`.''',
["Walmart", "Paytm", "Swiggy", "Oracle"]),

T("How does @Transactional work internally? Explain propagation and common pitfalls.",
'''Spring wraps the bean in a **proxy** (JDK dynamic proxy or CGLIB). On an external call, the `TransactionInterceptor` asks the `PlatformTransactionManager` to begin or join a transaction, binds the connection to the thread, invokes the method, then commits, or rolls back on a RuntimeException. **Propagation:** `REQUIRED` (the default; join the existing transaction or create one), `REQUIRES_NEW` (suspend the outer one and start an independent transaction, useful for audit logs that must persist even if the main transaction fails), `NESTED` (savepoints), `SUPPORTS`, `MANDATORY` and `NEVER`. **Pitfalls:** self-invocation and private methods bypass the proxy; checked exceptions do not roll back unless you add `rollbackFor`; catching an exception without rethrowing it causes a commit; long transactions that include remote calls hold DB locks; `readOnly = true` is a hint that helps Hibernate skip dirty checking; and work done on `@Async` threads does not join the caller's transaction.''',
["PhonePe", "Razorpay", "Walmart", "Paytm"]),

T("What is the N+1 query problem in Hibernate/JPA and how do you fix it?",
'''It happens when you run 1 query to load N parent entities and then trigger N more queries when you access a lazy association on each one, such as `order.getItems()` in a loop or during JSON serialization. The page works in development with 10 rows and collapses in production with 10,000. **Detect it** with `spring.jpa.show-sql`, Hibernate statistics, or by asserting query counts in tests. **Fix it** with: `JOIN FETCH` in JPQL (`select o from Order o join fetch o.items where ...`); an `@EntityGraph(attributePaths = "items")` on the repository method; `@BatchSize(size = 50)` or `hibernate.default_batch_fetch_size`, which loads children with IN queries in groups; or DTO projections that select only the columns you need. Watch out for fetch-joining collections together with pagination (Hibernate paginates in memory, warning HHH000104), and for joining multiple bags, which causes MultipleBagFetchException or Cartesian products.''',
["Swiggy", "Zomato", "Paytm", "Walmart"]),

T("Monolith vs microservices: what are the trade-offs, and how do services communicate?",
'''A **monolith** is one deployable unit. It is simple to build, test, debug and run transactions in (ACID in one DB), and it is the right start for small teams. Its pain points are a slow build and deploy cycle, scaling everything together, tight coupling, and one bug taking down the whole application. **Microservices** are independently deployable services, each owning its data. They enable team autonomy, independent scaling (for example scaling search separately from checkout), fault isolation and different technology choices. The costs are network failures, distributed transactions (Sagas), eventual consistency, and the need for tracing, service discovery and DevOps maturity. **Communication** is either synchronous (REST or gRPC through Feign or WebClient, with timeouts, retries and circuit breakers) or asynchronous (Kafka or RabbitMQ events, which decouple services and absorb load spikes). A good answer: start with a modular monolith and extract services where scaling or team boundaries require it.''',
["Swiggy", "Flipkart", "Uber", "Razorpay"]),

T("Explain the CAP theorem with real examples.",
'''In a distributed data store, when a **network partition (P)** happens, which you must assume in any multi-node system, you can guarantee either **Consistency (C)**, meaning every read sees the latest write, or **Availability (A)**, meaning every request gets a non-error response, but not both. **CP systems** refuse or block some requests during a partition to stay correct: ZooKeeper, etcd, HBase, and MongoDB with majority writes. They suit leader election, inventory counts and bank balances. **AP systems** keep serving and reconcile later (eventual consistency): Cassandra, DynamoDB and DNS. They suit shopping carts, likes, feeds and driver location. When there is no partition, the trade-off is latency versus consistency (the PACELC extension). Many systems are tunable per query: Cassandra lets you choose ONE, QUORUM or ALL. In interviews, link the choice to the business need, for example "payments need CP; showing a restaurant's rating can be AP".''',
["Uber", "Atlassian", "Walmart", "PhonePe"]),

T("What is dependency injection in Spring? Why is constructor injection preferred, and what are the bean scopes?",
'''**Dependency injection** means the container creates objects and supplies their dependencies, instead of classes calling `new` on their collaborators. That makes code loosely coupled and easy to test with mocks (Inversion of Control). Spring supports constructor, setter and field injection. **Constructor injection** is preferred because dependencies can be `final` (immutable), required dependencies are explicit and checked at startup, classes are testable without Spring (`new Service(mockRepo)`), and circular dependencies fail fast instead of hiding. With a single constructor, `@Autowired` is optional. Lombok's `@RequiredArgsConstructor` removes the boilerplate. **Scopes:** `singleton` (the default, one instance per container, so it must be stateless or thread-safe), `prototype` (a new instance per injection or lookup), and the web scopes `request`, `session` and `application`. When several beans implement the same interface, resolve the ambiguity with `@Qualifier` or `@Primary`.''',
["Walmart", "Oracle", "SAP", "Paytm"]),
]

DAY = build(7, "Mock Test 1", "A full mixed-difficulty mock covering DSA, Java, Spring Boot, JPA, SQL, OS, networking and system-design concepts, timed like a real product-company round.", mcqs, coding, theory)
