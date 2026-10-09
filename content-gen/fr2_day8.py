from fr2_common import M, C, T, save

mcqs = [
M("Java Output", r'''
What does this print?
```java
String s1 = "hello";
String s2 = "hel" + "lo";
String s3 = new String("hello");
final String a = "hel";
String s4 = a + "lo";
System.out.println((s1 == s2) + " " + (s1 == s3) + " "
    + (s1 == s4) + " " + (s1 == s3.intern()));
```''', ["true false false true", "true false true true", "false false true true", "true true true true"], 1,
'''`"hel" + "lo"` is folded at compile time, and so is `a + "lo"` because `a` is a `final` compile-time constant, so both point to the pooled literal. `new String` always creates a new heap object, while `intern()` hands back the pooled copy.''', ["Microsoft", "Adobe"]),

M("Binary Search on Answer", r'''
Koko eats bananas from piles `[3, 6, 7, 11]` and has `h = 8` hours. Each hour she eats up to `k` bananas from one pile. What is the minimum integer `k` that lets her finish in time?''',
["3", "4", "5", "6"], 1,
'''At k = 4 the hours are 1+2+2+3 = 8, which fits. At k = 3 they are 1+2+3+4 = 10, which does not. Hours never go up as k grows, so you can binary search k over [1, max pile].''', ["Google", "Amazon"]),

M("Graphs", '''A graph has some negative edge weights. You need single-source shortest paths and must report a negative cycle if one exists. Which algorithm fits?''',
["Dijkstra with a min-heap", "Bellman-Ford", "Prim's algorithm", "Plain BFS"], 1,
'''Bellman-Ford relaxes every edge V-1 times. If any edge can still be relaxed after that, a negative cycle exists. Dijkstra assumes a finalized node never gets cheaper, and negative edges break that.''', ["Google", "Microsoft"]),

M("Graphs", '''A DAG has the edges A→B, A→C, B→D and C→D. How many valid topological orderings does it have?''',
["1", "2", "3", "4"], 1,
'''A must come first and D must come last. B and C have no edge between them, so they can appear in either order. That gives A,B,C,D and A,C,B,D.''', ["Google"]),

M("DSA Complexity", '''Union-Find uses both path compression and union by rank. What is the amortized time per operation?''',
["O(log n)", "O(1) exactly", "O(α(n)), the inverse Ackermann function", "O(√n)"], 2,
'''With both optimizations together, the amortized cost per operation is O(α(n)). That value is at most 4 for any realistic input, so it behaves like a constant. Either optimization alone gives O(log n).''', ["Google", "Microsoft"]),

M("Dynamic Programming", '''How many structurally unique BSTs can be built from the keys 1..4?''',
["10", "12", "14", "16"], 2,
'''The count is the Catalan number: G(n) = Σ G(i-1)·G(n-i). The sequence runs G(0)=1, G(1)=1, G(2)=2, G(3)=5, G(4)=5+2+2+5 = 14. This is LeetCode 96.''', ["Microsoft", "Amazon"]),

M("Collections", r'''
What does this print?
```java
List<Integer> key = new ArrayList<>(List.of(1, 2));
Map<List<Integer>, String> m = new HashMap<>();
m.put(key, "x");
key.add(3);
System.out.println(m.get(key) + " "
    + m.containsKey(List.of(1, 2)) + " " + m.size());
```''', ["x true 1", "null true 1", "null false 1", "x false 1"], 2,
'''The entry was stored under the hash of [1,2]. Lookup with the mutated key computes the hash of [1,2,3], so it finds nothing. Lookup with a fresh [1,2] matches the stored hash, but equals() then compares it against the mutated key [1,2,3] and fails. The entry is still there, so size is 1.''', ["Google", "Microsoft"]),

M("Multithreading", '''Several threads run `count++` on a `volatile int count`. What does `volatile` guarantee here?''',
["count++ becomes atomic", "Visibility of writes and no reordering around the access, but not atomicity of count++",
 "Mutual exclusion, like synchronized", "Nothing. volatile only matters for long and double"], 1,
'''`count++` is three steps: read, add, write. volatile makes every write visible to other threads and sets up happens-before, but two threads can still interleave those steps and lose updates. Use AtomicInteger or a lock.''', ["Microsoft", "Uber"]),

M("Java Output", r'''
What does this print?
```java
int[] arr = {1, 2, 3};
int i = 0;
arr[i] = i = 2;
System.out.println(Arrays.toString(arr) + " " + i);
```''', ["[1, 2, 2] 2", "[2, 2, 3] 2", "[1, 2, 3] 2", "ArrayIndexOutOfBoundsException"], 1,
'''Java evaluates the left operand, including the array index, before the right side. So the target is fixed as arr[0] while i is still 0. Then `i = 2` runs and 2 is stored in arr[0].''', ["Google"]),

M("SQL", r'''
Table `emp(salary)` holds 100, 200, 300, 300. What does this return?
```sql
SELECT MAX(salary) FROM emp
WHERE salary < (SELECT MAX(salary) FROM emp);
```''', ["300", "200", "100", "NULL"], 1,
'''The inner query returns 300. The outer query keeps rows below 300, which are 100 and 200, and takes the max: 200. This is a standard way to get the second-highest distinct salary.''', ["Microsoft", "Amazon"]),

M("Operating Systems", '''Banker's algorithm is used for which deadlock strategy?''',
["Prevention", "Avoidance", "Detection and recovery", "Ignoring (the ostrich approach)"], 1,
'''Before granting a request, Banker's algorithm checks whether the system would still be in a safe state. That is avoidance. Prevention works differently: it structurally removes one of the four Coffman conditions.''', ["Microsoft", "Oracle"]),

M("Operating Systems", '''CPU utilization falls sharply while disk activity spikes, because processes spend most of their time servicing page faults. What is this called?''',
["Starvation", "Thrashing", "Belady's anomaly", "Convoy effect"], 1,
'''This is thrashing. The combined working sets don't fit in RAM, so pages keep getting evicted and faulted back in. The fix is to reduce the degree of multiprogramming or add memory, guided by the working-set model.''', ["Microsoft"]),

M("Computer Networks", '''In a TCP three-way handshake, which state does the server enter after it receives a SYN and replies with SYN-ACK?''',
["LISTEN", "SYN_SENT", "SYN_RECEIVED", "ESTABLISHED"], 2,
'''The server moves LISTEN → SYN_RECEIVED once it sends SYN-ACK. It reaches ESTABLISHED when the final ACK arrives. A SYN flood attack fills the queue of half-open SYN_RECEIVED connections.''', ["Google", "Microsoft"]),

M("DBMS", '''Under the SQL standard, which isolation level is the lowest one that prevents phantom reads?''',
["Read Uncommitted", "Read Committed", "Repeatable Read", "Serializable"], 3,
'''The standard only guarantees no phantoms at Serializable. Note that MySQL InnoDB also blocks most phantoms at Repeatable Read by using next-key (gap) locks.''', ["Microsoft", "Oracle"]),

M("System Design", '''A cache cluster with N nodes adds one more node. With consistent hashing, roughly what share of keys has to move?''',
["All keys", "About 1/(N+1) of the keys", "About half of the keys", "None"], 1,
'''Only keys on the arc the new node takes over get remapped, which is about K/(N+1) of K keys. With plain `hash % N`, nearly every key would move. Virtual nodes keep the load even across nodes.''', ["Google", "Amazon"]),

M("Aptitude", '''How many times do the hour and minute hands of a clock overlap in 24 hours?''',
["24", "22", "23", "44"], 1,
'''The hands overlap every 12/11 hours, which is 11 times in 12 hours. The 12 o'clock overlap is counted once, so a full day has 22 overlaps.''', ["Microsoft", "Google"]),

M("Puzzles", '''You have 25 horses and a track that races 5 at a time. There is no stopwatch. What is the minimum number of races to find the 3 fastest?''',
["6", "7", "8", "10"], 1,
'''Run 5 heats, then a 6th race of the heat winners. Only 5 horses can still be in the top 3: the 2nd and 3rd from the winner's heat, the 1st and 2nd from the runner-up's heat, and the winner of the 3rd-place heat. A 7th race among them settles 2nd and 3rd.''', ["Google", "Microsoft"]),

M("Graphs", '''Every edge in a graph has weight 0 or 1. What is the most efficient way to get single-source shortest paths?''',
["Dijkstra, O(E log V)", "0-1 BFS with a deque, O(V + E)", "Floyd-Warshall", "DFS"], 1,
'''Push the target to the front of the deque when crossing a 0-weight edge, and to the back for a 1-weight edge. The deque stays sorted by distance, so each node is finalized in O(1) time.''', ["Google"]),

M("Dynamic Programming", '''What is the length of the longest strictly increasing subsequence of `[10, 9, 2, 5, 3, 7, 101, 18]`, and what is the best known time complexity?''',
["4, O(n log n)", "4, O(n²) only", "5, O(n log n)", "3, O(n)"], 0,
'''One answer is 2, 3, 7, 18, so the length is 4. Patience sorting keeps a `tails` array and uses binary search to place each element. That gives O(n log n), better than the O(n²) DP.''', ["Microsoft", "Google"]),

M("Collections", r'''
What does this print?
```java
List<Integer> base = new ArrayList<>(List.of(1, 2));
List<Integer> view = Collections.unmodifiableList(base);
List<Integer> copy = List.copyOf(base);
base.add(3);
System.out.println(view.size() + " " + copy.size());
```''', ["2 2", "3 3", "3 2", "UnsupportedOperationException"], 2,
'''`unmodifiableList` is a read-only view, so changes to the backing list show through it. `List.copyOf` makes an independent immutable snapshot. Adding to `base` itself is allowed.''', ["Microsoft"]),
]

coding = [
C("Split Array Largest Sum", "Hard", ["Google", "Microsoft", "Amazon"], r'''
You get an array `nums` of non-negative integers and an integer `k`. Split the array into exactly `k` non-empty **contiguous** subarrays so that the **largest subarray sum** is as small as possible. Return that minimized largest sum.

**Example 1**
```
Input:  nums = [7,2,5,10,8], k = 2
Output: 18     // [7,2,5] | [10,8]
```
**Example 2**
```
Input:  nums = [1,2,3,4,5], k = 2
Output: 9      // [1,2,3] | [4,5]
```
**Constraints:** 1 ≤ nums.length ≤ 1000, 0 ≤ nums[i] ≤ 10^6, 1 ≤ k ≤ min(50, nums.length)''',
["The answer lies between max(nums) and sum(nums). Can you check one candidate value quickly?",
 "For a cap X, go left to right and start a new piece whenever adding the next element would exceed X. If you need at most k pieces, X works."],
r'''
class Solution {
    public int splitArray(int[] nums, int k) {
        long lo = 0, hi = 0;
        for (int x : nums) {
            lo = Math.max(lo, x);
            hi += x;
        }
        while (lo < hi) {
            long mid = lo + (hi - lo) / 2;
            if (piecesNeeded(nums, mid) <= k) hi = mid;   // feasible, try smaller
            else lo = mid + 1;
        }
        return (int) lo;
    }

    private int piecesNeeded(int[] nums, long cap) {
        int pieces = 1;
        long sum = 0;
        for (int x : nums) {
            if (sum + x > cap) {
                pieces++;
                sum = 0;
            }
            sum += x;
        }
        return pieces;
    }
}''',
'''This is the classic **binary search on the answer** pattern. If a cap X can be met with at most k pieces, any larger cap can be met too, so feasibility is monotonic. The search range starts at `max(nums)`, since no piece can be smaller than the biggest element, and ends at `sum(nums)`, which is one piece. The greedy check packs elements into the current piece until the cap would be exceeded. Packing as much as possible into each piece minimizes the piece count. Using fewer than k pieces is fine because you can always split further. Google and Microsoft interviewers often follow up with "Capacity to Ship Packages" (LC 1011) or "Koko Eating Bananas", which use the same template.''',
"O(n log(sum))", "O(1)", "https://leetcode.com/problems/split-array-largest-sum/"),

C("Course Schedule II", "Medium", ["Microsoft", "Google", "Amazon", "Uber"], r'''
There are `numCourses` courses labelled `0..numCourses-1`. Each `prerequisites[i] = [a, b]` means you must take `b` before `a`. Return any order that finishes all courses, or an empty array if that is impossible because of a cycle.

**Example 1**
```
Input:  numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]
Output: [0,1,2,3]   (or [0,2,1,3])
```
**Example 2**
```
Input:  numCourses = 2, prerequisites = [[1,0],[0,1]]
Output: []
```
**Constraints:** 1 ≤ numCourses ≤ 2000, 0 ≤ prerequisites.length ≤ numCourses·(numCourses−1)''',
["Model it as a directed graph with an edge b → a. A valid order is a topological sort.",
 "Kahn's algorithm: repeatedly take nodes with in-degree 0. If you take fewer than n nodes, there is a cycle."],
r'''
import java.util.*;

class Solution {
    public int[] findOrder(int numCourses, int[][] prerequisites) {
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < numCourses; i++) adj.add(new ArrayList<>());
        int[] indeg = new int[numCourses];
        for (int[] p : prerequisites) {
            adj.get(p[1]).add(p[0]);
            indeg[p[0]]++;
        }
        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 0; i < numCourses; i++) if (indeg[i] == 0) queue.offer(i);

        int[] order = new int[numCourses];
        int idx = 0;
        while (!queue.isEmpty()) {
            int u = queue.poll();
            order[idx++] = u;
            for (int v : adj.get(u)) {
                if (--indeg[v] == 0) queue.offer(v);
            }
        }
        return idx == numCourses ? order : new int[0];
    }
}''',
'''Kahn's algorithm builds the order layer by layer. A course with in-degree 0 has no remaining prerequisites, so it can go next. Taking it reduces the in-degree of its dependents. If the graph has a cycle, the nodes in that cycle never reach in-degree 0, so fewer than `numCourses` nodes get output and we return an empty array. A DFS with three colors (unvisited, visiting, done) also works: record each node in post-order and reverse the list at the end. Interviewers often ask for both versions and how each one detects a cycle. A common follow-up is the minimum number of semesters, which is a BFS level count.''',
"O(V + E)", "O(V + E)", "https://leetcode.com/problems/course-schedule-ii/"),

C("Cheapest Flights Within K Stops", "Medium", ["Google", "Microsoft", "Amazon", "Uber"], r'''
There are `n` cities and a list of `flights[i] = [from, to, price]`. Return the cheapest price from `src` to `dst` using **at most `k` stops** (so at most k+1 flights). Return `-1` if no such route exists.

**Example 1**
```
Input:  n = 4, flights = [[0,1,100],[1,2,100],[2,0,100],[1,3,600],[2,3,200]],
        src = 0, dst = 3, k = 1
Output: 700        // 0 → 1 → 3
```
(0 → 1 → 2 → 3 costs only 400, but it uses 2 stops.)

**Example 2**
```
Input:  n = 3, flights = [[0,1,100],[1,2,100],[0,2,500]], src = 0, dst = 2, k = 0
Output: 500
```
**Constraints:** 1 ≤ n ≤ 100, 0 ≤ flights.length ≤ n·(n−1)/2, 1 ≤ price ≤ 10^4, 0 ≤ k < n''',
["Plain Dijkstra breaks because a costlier path with fewer stops may still be needed later.",
 "Run Bellman-Ford for exactly k+1 rounds. In each round, relax from a copy of the previous round's distances."],
r'''
import java.util.*;

class Solution {
    public int findCheapestPrice(int n, int[][] flights, int src, int dst, int k) {
        final int INF = Integer.MAX_VALUE;
        int[] dist = new int[n];
        Arrays.fill(dist, INF);
        dist[src] = 0;

        for (int round = 0; round <= k; round++) {      // k stops = k+1 edges
            int[] next = dist.clone();
            for (int[] f : flights) {
                int u = f[0], v = f[1], w = f[2];
                if (dist[u] != INF && dist[u] + w < next[v]) {
                    next[v] = dist[u] + w;
                }
            }
            dist = next;
        }
        return dist[dst] == INF ? -1 : dist[dst];
    }
}''',
'''After round i, `dist[v]` holds the cheapest cost to reach v using at most i+1 edges. The important detail is reading from the previous round's array (`dist`) and writing to a copy (`next`). Relaxing in place would let one round chain several edges, which can silently go over the stop limit. That is a bug interviewers look for. Running k+1 rounds of E relaxations gives O(k·E). Another approach is BFS level by level with pruning, or Dijkstra on (node, stops) states. Explain why plain Dijkstra on node alone fails: a cheaper path that uses up its stops early can block a slightly costlier path that still has stops left.''',
"O(k · E)", "O(n)", "https://leetcode.com/problems/cheapest-flights-within-k-stops/"),

C("Longest Increasing Path in a Matrix", "Hard", ["Google", "Microsoft", "Uber"], r'''
Given an `m x n` integer matrix, return the length of the longest **strictly increasing** path. From each cell you can move up, down, left or right. Diagonal moves and wrapping around the edges are not allowed.

**Example 1**
```
Input:  [[9,9,4],
         [6,6,8],
         [2,1,1]]
Output: 4          // 1 → 2 → 6 → 9
```
**Example 2**
```
Input:  [[3,4,5],
         [3,2,6],
         [2,2,1]]
Output: 4          // 3 → 4 → 5 → 6
```
**Constraints:** 1 ≤ m, n ≤ 200, 0 ≤ matrix[i][j] ≤ 2^31 − 1''',
["The path must strictly increase, so it can never revisit a cell. The implicit graph is a DAG.",
 "DFS from every cell and memoize the longest path starting at each cell."],
r'''
class Solution {
    private static final int[][] DIRS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    private int[][] memo;
    private int[][] g;
    private int m, n;

    public int longestIncreasingPath(int[][] matrix) {
        g = matrix;
        m = matrix.length;
        n = matrix[0].length;
        memo = new int[m][n];
        int best = 0;
        for (int i = 0; i < m; i++)
            for (int j = 0; j < n; j++)
                best = Math.max(best, dfs(i, j));
        return best;
    }

    private int dfs(int r, int c) {
        if (memo[r][c] != 0) return memo[r][c];
        int len = 1;
        for (int[] d : DIRS) {
            int nr = r + d[0], nc = c + d[1];
            if (nr >= 0 && nr < m && nc >= 0 && nc < n && g[nr][nc] > g[r][c]) {
                len = Math.max(len, 1 + dfs(nr, nc));
            }
        }
        return memo[r][c] = len;
    }
}''',
'''The key insight is that strictly increasing moves can never form a cycle. That means no visited set is needed and memoization is safe: the longest path from a cell does not depend on how we got there. Each cell's answer is computed once, using up to four neighbors, so the total work is O(m·n). If an interviewer worries about recursion depth on a 200x200 grid, which can reach 40,000 frames, switch to the iterative version: run Kahn's topological sort over cells ordered by out-degree and count BFS layers. This problem shows up often in Google onsite reports as a "DFS + memo on a grid" question.''',
"O(m · n)", "O(m · n)", "https://leetcode.com/problems/longest-increasing-path-in-a-matrix/"),
]

theory = [
T("How does Dijkstra's algorithm work, and why does it fail with negative edge weights?", '''Dijkstra keeps a min-heap of (distance, node). It repeatedly pops the closest unsettled node, **finalizes** it, and relaxes its outgoing edges. With a binary heap this runs in O((V + E) log V).

Correctness depends on one invariant: once a node is popped, no later path can be cheaper, because every remaining path only adds non-negative weight. A negative edge breaks this. A node finalized at cost 5 could later be reached at cost 3 through a path that includes a -4 edge, and Dijkstra would never revisit it.

For negative weights, use **Bellman-Ford** (O(VE), and it detects negative cycles). For all-pairs on small graphs, use Floyd-Warshall. Interviewers also like the stale-entry check `if (d > dist[u]) continue;`. It replaces a decrease-key operation, which Java's PriorityQueue doesn't support.''', ["Google", "Microsoft", "Uber"]),

T("When do you use 'binary search on the answer', and how do you recognize it?", '''Use it when the question asks for the **minimum or maximum value that satisfies a condition**, and checking one candidate is easy while computing the answer directly is hard.

How to spot it:
- The answer is a number in a bounded range, such as a speed, capacity, day or distance.
- **Monotonic feasibility**: if X works, then every X' ≥ X also works (or every X' ≤ X does).
- The check usually runs in O(n), often as a greedy pass.

Template: set `lo` to the smallest possible answer and `hi` to the largest. While `lo < hi`, compute `mid`. If `feasible(mid)`, set `hi = mid`, otherwise set `lo = mid + 1`.

Classic examples: Koko Eating Bananas, Capacity to Ship Packages, Split Array Largest Sum, Minimum Days to Make Bouquets, Aggressive Cows. Total cost is O(n log range).''', ["Google", "Amazon", "Microsoft"]),

T("How do you detect a cycle in a directed graph versus an undirected graph?", '''**Undirected:** run a DFS and pass along the parent. If you reach a visited neighbor that isn't the parent, there's a cycle. You can also use **Union-Find**: for each edge (u, v), if find(u) == find(v), adding the edge creates a cycle.

**Directed:** a visited flag alone is not enough, because two separate paths reaching the same node is not a cycle. Use **three colors**: white (unvisited), gray (on the current recursion stack) and black (finished). An edge into a **gray** node is a back edge, which means a cycle. You can also run **Kahn's algorithm**: if the topological order contains fewer than V nodes, the graph has a cycle.

Both versions run in O(V + E). Interviewers often ask why the undirected parent trick fails on directed graphs, and how to detect a cycle in a linked list (Floyd's tortoise and hare).''', ["Microsoft", "Amazon", "Google"]),

T("Memoization vs tabulation: how do you choose, and how do you optimize DP space?", '''**Memoization** (top-down) is recursion plus a cache. It is easy to derive from the recurrence and only computes the states that are actually reached. Its downsides are recursion overhead and a risk of StackOverflowError when depth gets into the tens of thousands.

**Tabulation** (bottom-up) fills a table in dependency order. It has no recursion, often runs faster, and makes space optimization easy. If row `i` only depends on row `i-1`, you can keep two rows or even a single array. For example, 0/1 knapsack drops from O(nW) to O(W) space by looping capacity **backwards**.

A good interview approach: write the recurrence, code a memoized version quickly, then convert it to tabulation if asked about stack depth or memory. Always state the number of states and the transitions per state. Their product is the time complexity.''', ["Microsoft", "Google", "Adobe"]),

T("Explain how Java 8+ HashMap works internally.", '''A HashMap is an array of buckets, 16 by default. `put` calls `hashCode()`, mixes the bits (`h ^ (h >>> 16)`), and picks a bucket with `(n - 1) & hash`. Collisions go into a linked list in that bucket. When a bucket reaches **8 nodes** and the table has at least 64 slots, the list is converted to a **red-black tree**. That changes the worst-case lookup from O(n) to O(log n). It converts back to a list at 6 nodes.

Once size exceeds capacity × load factor (0.75), the table **doubles**. Each entry either stays at index i or moves to i + oldCap, so no full rehash is needed.

Things to know: keys need consistent `equals`/`hashCode`, mutable keys break lookups, one null key is allowed, and the map is not thread-safe. Use ConcurrentHashMap for concurrent access.''', ["Microsoft", "Adobe", "Amazon"]),

T("What is the difference between a process and a thread? Why is a thread context switch cheaper?", '''A **process** has its own virtual address space, heap, file descriptors and page tables. A **thread** is an execution unit inside a process. Threads share the heap and code, but each has its own stack, registers and program counter.

A **process switch** has to swap page tables and usually flushes the TLB (unless the CPU tags entries with an address-space ID). That leads to cache and TLB misses afterwards. A **thread switch** within the same process keeps the address space, so it only saves and restores registers and the stack pointer. That is much cheaper.

The trade-off is isolation. A crashing process doesn't take down others, but a bad thread can corrupt shared memory for the whole process. Processes talk via IPC (pipes, sockets); threads via shared memory plus synchronization. In Java, every thread maps to an OS thread, except virtual threads, which were added in Java 21.''', ["Microsoft", "Oracle", "Adobe"]),
]

save(8, "Google & Microsoft Hard Round",
     "Tough graph, binary-search-on-answer and DP questions in the style Google and Microsoft use in their onsite rounds.",
     mcqs, coding, theory)
