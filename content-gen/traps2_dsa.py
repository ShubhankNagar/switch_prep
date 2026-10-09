from traps2_common import T

A = "dsa"

BS_BUGGY = """int lo = 0, hi = nums.length - 1;
while (lo < hi) {
    int mid = (lo + hi) / 2;
    if (nums[mid] < target) lo = mid;
    else hi = mid;
}
return lo;"""

BS_FIX = """// first index i with nums[i] >= target; returns nums.length if none
static int lowerBound(int[] nums, int target) {
    int lo = 0, hi = nums.length;            // answer lives in [lo, hi]
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;        // no overflow, rounds down
        if (nums[mid] < target) lo = mid + 1; // mid can't be the answer
        else hi = mid;                        // mid might be the answer
    }
    return lo;
}"""

BFS_BUGGY = """Deque<int[]> q = new ArrayDeque<>();
q.add(new int[]{0, 0});
while (!q.isEmpty()) {
    int[] cur = q.poll();
    seen[cur[0]][cur[1]] = true;              // marked here...
    for (int[] d : DIRS) {
        int r = cur[0] + d[0], c = cur[1] + d[1];
        if (inside(r, c) && grid[r][c] == 0 && !seen[r][c])
            q.add(new int[]{r, c});           // ...but not here
    }
}"""

BFS_FIX = """static int shortestPath(int[][] grid) {     // 0 = open, 1 = wall; steps from top-left to bottom-right
    int n = grid.length, m = grid[0].length;
    if (grid[0][0] == 1 || grid[n - 1][m - 1] == 1) return -1;
    boolean[][] seen = new boolean[n][m];
    Deque<int[]> q = new ArrayDeque<>();
    q.add(new int[]{0, 0});
    seen[0][0] = true;                            // mark the source too
    for (int steps = 0; !q.isEmpty(); steps++) {
        for (int size = q.size(); size > 0; size--) {   // one BFS level
            int[] cur = q.poll();
            if (cur[0] == n - 1 && cur[1] == m - 1) return steps;
            for (int[] d : DIRS) {
                int r = cur[0] + d[0], c = cur[1] + d[1];
                if (r >= 0 && c >= 0 && r < n && c < m && grid[r][c] == 0 && !seen[r][c]) {
                    seen[r][c] = true;            // mark on ENQUEUE: each cell enters once
                    q.add(new int[]{r, c});
                }
            }
        }
    }
    return -1;
}"""

DIJ_FIX = """static long[] dijkstra(List<List<int[]>> adj, int src) {   // adj.get(u) = {v, w}, all w >= 0
    long[] dist = new long[adj.size()];
    Arrays.fill(dist, Long.MAX_VALUE);
    dist[src] = 0;
    PriorityQueue<long[]> pq = new PriorityQueue<>(Comparator.comparingLong(e -> e[1]));
    pq.add(new long[]{src, 0});
    while (!pq.isEmpty()) {
        long[] top = pq.poll();
        int u = (int) top[0];
        if (top[1] > dist[u]) continue;           // stale entry: a shorter path was already found
        for (int[] e : adj.get(u)) {
            long nd = dist[u] + e[1];
            if (nd < dist[e[0]]) {
                dist[e[0]] = nd;
                pq.add(new long[]{e[0], nd});     // lazy insert instead of decrease-key
            }
        }
    }
    return dist;
}"""

OVF_PROMPT = """int[] nums = {2_000_000_000, 2_000_000_000};
int sum = 0;
for (int x : nums) sum += x;
long total = sum;              // "I store it in a long, so it's safe"
System.out.println(total);"""

OVF_FIX = """long sum = 0;
for (int x : nums) sum += x;                  // accumulate in long
long area = (long) width * height;            // widen BEFORE multiplying
long prod = (a % MOD) * (b % MOD) % MOD;      // a, b are long; MOD = 1_000_000_007
list.sort((x, y) -> Integer.compare(x, y));   // never (x, y) -> x - y
int checked = Math.addExact(p, q);            // throws ArithmeticException instead of wrapping"""

COIN_FIX = """static int minCoins(int[] coins, int amount) {
    int[] dp = new int[amount + 1];               // dp[a] = fewest coins to make a
    Arrays.fill(dp, Integer.MAX_VALUE);
    dp[0] = 0;
    for (int a = 1; a <= amount; a++)
        for (int c : coins)
            if (c <= a && dp[a - c] != Integer.MAX_VALUE)
                dp[a] = Math.min(dp[a], dp[a - c] + 1);
    return dp[amount] == Integer.MAX_VALUE ? -1 : dp[amount];
}"""

SW_BUGGY = """int count = 0, sum = 0, left = 0;
for (int right = 0; right < nums.length; right++) {
    sum += nums[right];
    while (sum > k && left <= right) sum -= nums[left++];
    if (sum == k) count++;
}
return count;"""

SW_FIX = """static int subarraySum(int[] nums, int k) {
    Map<Integer, Integer> seen = new HashMap<>();   // prefix sum -> how many times seen
    seen.put(0, 1);                                 // empty prefix: subarrays starting at index 0
    int prefix = 0, count = 0;
    for (int x : nums) {
        prefix += x;
        count += seen.getOrDefault(prefix - k, 0);  // earlier prefix p with prefix - p == k
        seen.merge(prefix, 1, Integer::sum);
    }
    return count;
}"""

CYC_FIX = """// 0 = unvisited, 1 = on the current DFS path, 2 = fully explored
static boolean hasCycle(List<List<Integer>> adj) {
    int[] state = new int[adj.size()];
    for (int i = 0; i < adj.size(); i++)
        if (state[i] == 0 && dfs(i, adj, state)) return true;
    return false;
}

static boolean dfs(int u, List<List<Integer>> adj, int[] state) {
    state[u] = 1;
    for (int v : adj.get(u)) {
        if (state[v] == 1) return true;            // back edge: v is an ancestor on this path
        if (state[v] == 0 && dfs(v, adj, state)) return true;
    }
    state[u] = 2;                                  // done: reaching u again is NOT a cycle
    return false;
}"""

REC_PROMPT = """int ways(int n) {              // climbing stairs: 1 or 2 steps at a time
    if (n <= 1) return 1;
    return ways(n - 1) + ways(n - 2);
}"""

REC_FIX = """// top-down: O(n) time, O(n) memo + O(n) stack
static long ways(int n, long[] memo) {
    if (n <= 1) return 1;
    if (memo[n] != 0) return memo[n];
    return memo[n] = ways(n - 1, memo) + ways(n - 2, memo);
}

// bottom-up: O(n) time, O(1) space, no stack-depth risk
static long waysIter(int n) {
    long prev = 1, cur = 1;                        // ways(0), ways(1)
    for (int i = 2; i <= n; i++) {
        long next = prev + cur;
        prev = cur;
        cur = next;
    }
    return cur;
}"""

TRAPS = [
    T("trap-dsa-binary-search-bounds", A, "Binary search: infinite loop and wrong bounds", "Intermediate", "Very common",
      f"""You need the **first index whose value is `>= target`** (lower bound) in a sorted array that may contain duplicates. The candidate writes:

```java
{BS_BUGGY}
```

What is wrong with it?""",
      "The only issue is `(lo + hi) / 2` overflowing; switch to `lo + (hi - lo) / 2` and it is fine.",
      """Candidates memorise one famous binary-search bug (overflow) and stop looking. The real killers are the **loop invariant** bugs: mixing `lo < hi` with `lo = mid` and a rounded-down `mid`, and choosing `hi = n - 1` when "not found" should be `n`. These pass the happy-path example the candidate traces by hand and fail only on two-element windows or when every element is smaller than the target, which is exactly what the interviewer tests next.""",
      """Three separate problems:

1. **Infinite loop.** When `hi == lo + 1`, `mid` rounds down to `lo`. If `nums[lo] < target`, then `lo = mid` changes nothing and the loop never ends. Rule: if a branch sets `lo = mid`, you must use the *upper* mid `lo + (hi - lo + 1) / 2`. Better: write `lo = mid + 1`, because `mid` is known not to be the answer.
2. **Wrong range.** Even after fixing the loop with `lo = mid + 1`, starting from `hi = nums.length - 1` means the function can never return `nums.length` ("insert at the end"), so `[1, 2, 3]` with target `4` returns `2`.
3. **Overflow.** `(lo + hi) / 2` overflows only when `lo + hi > 2^31 - 1`. That is rare on arrays but common in *binary search on the answer* over values up to 2 billion.

State the invariant out loud ("the answer is always in `[lo, hi]`") and every bound follows from it.""",
      "Say the invariant out loud before coding and test a 2-element array plus a target larger than every element.",
      options=[
          "Nothing, it is correct for every input.",
          "Only the midpoint can overflow; use `lo + (hi - lo) / 2`.",
          "`lo = mid` with a rounded-down `mid` can loop forever, and `hi = length - 1` can never return \"insert at end\"; use `lo = mid + 1` and `hi = nums.length`.",
          "It must use `while (lo <= hi)`; nothing else changes.",
      ], answer=2,
      fix=f"""```java
{BS_FIX}
```
Quick tests: `[1,2,2,2,5]`, 2 → 1; `[1,2,3]`, 4 → 3; `[]`, 1 → 0.""",
      askedAt=["Google", "Amazon", "Flipkart"]),

    T("trap-dsa-bfs-visited-on-enqueue", A, "BFS: mark visited on enqueue, not dequeue", "Basic", "Very common",
      f"""Shortest path in a grid (0 = open). The candidate's BFS returns correct answers on small grids but times out on a 50x50 grid with no walls:

```java
{BFS_BUGGY}
```

Why?""",
      "BFS on a grid is just slow; switch to DFS or use a LinkedList instead of ArrayDeque.",
      """Marking a node "visited" when you *process* it feels natural because that is how DFS is usually written. In BFS, though, a cell sits in the queue for a while before it is processed. During that time every neighbour that is expanded sees `seen == false` and adds *another* copy. Each copy then expands its neighbours again, so the copies multiply. Hand-tracing a 3x3 grid hides it, because the duplicates look harmless.""",
      """The number of queue entries grows like the number of shortest paths, which is combinatorial. Measured with exactly this code on an open grid: 10x10 → 184,755 polls for 100 cells; 14x14 → about 40 million polls for 196 cells.

**Fix:** set `seen = true` at the moment you **enqueue** (including the source). Then each cell enters the queue at most once, giving O(V + E) time and O(V) queue memory. Process the queue level by level (`for size = q.size()`) to count steps without storing distances.

Marking on dequeue *with* a `if (seen) continue;` skip is still correct, but it lets the queue hold up to E entries instead of V. On dense graphs (word ladder with many neighbours) that is a real memory problem. Interviewers see this bug constantly in Rotting Oranges, Word Ladder and Number of Islands.""",
      "Say \"I mark visited when I enqueue so each node enters the queue once\" while you write that line.",
      options=[
          "`ArrayDeque` is slower than `LinkedList` for BFS.",
          "Cells are marked only when dequeued, so the same cell is enqueued again and again before it is processed and the copies multiply; mark visited when enqueueing.",
          "BFS on a grid is inherently O(V^2).",
          "It needs DFS, which visits each cell once.",
      ], answer=1,
      fix=f"""```java
{BFS_FIX}
```""",
      askedAt=["Amazon", "Microsoft", "Uber"]),

    T("trap-dsa-dijkstra-assumptions", A, "Dijkstra: negative edges and stale queue entries", "Intermediate", "Common",
      """You implement Dijkstra with a `PriorityQueue` and lazy insertion. The interviewer then asks:

1. "Some edges now have **negative** weights (cashback legs on a route). Does your code still work?"
2. "Why do you need the line `if (d > dist[u]) continue;`?"

Which answer is correct?""",
      "Dijkstra works with negative edges as long as there is no negative cycle, and the stale check is only a micro-optimisation.",
      """People mix up the requirement of Bellman-Ford (no negative *cycles*) with Dijkstra's stronger one (no negative *edges*). The stale-entry line looks like an optimisation because removing it does not change the answer on small tests. Candidates also suggest "add a constant to every edge" as a quick fix without checking that it changes which path is shortest.""",
      """**Negative edges break Dijkstra's core guarantee**: once a node is popped, its distance is final. Example: A→B (2), A→C (3), C→B (−2), B→D (1). The visited-set version finalises B at 2 and D at 3, but the true values are B = 1 and D = 2. The lazy re-insertion version may correct itself by re-pushing nodes, but then it is no longer O(E log V), and the worst case becomes exponential. Use **Bellman-Ford** (O(VE), also detects negative cycles), or relax edges in topological order if the graph is a DAG.

**Adding a constant** to every edge penalises paths with more edges, so the shortest path can change.

**The stale check** matters because Java's `PriorityQueue` has no decrease-key. You push duplicates, and an outdated entry must be skipped. Otherwise every stale pop rescans the adjacency list, and the complexity degrades.""",
      "Before coding, say \"weights are non-negative, so Dijkstra applies; otherwise Bellman-Ford\", which shows you know the precondition.",
      options=[
          "Works with negative edges as long as there is no negative cycle.",
          "With negative edges a node can be finalised too early, so use Bellman-Ford (or topological relaxation on a DAG); the stale check skips outdated duplicate entries because PriorityQueue has no decrease-key.",
          "Removing the stale check changes nothing, not even running time.",
          "Add the absolute value of the most negative weight to every edge, then Dijkstra is correct.",
      ], answer=1,
      fix=f"""```java
{DIJ_FIX}
```""",
      askedAt=["Google", "Uber", "Ola"]),

    T("trap-dsa-int-overflow", A, "Integer overflow in sums, products and comparators", "Basic", "Very common",
      f"""What does this print?

```java
{OVF_PROMPT}
```""",
      "4000000000, because the result is stored in a `long`.",
      """The overflow happens **inside** the loop, in `int` arithmetic, before the value ever reaches the `long`. Assigning to a wider type afterwards cannot recover lost bits. The same mistake hides in `long area = w * h;` (an int multiply, then widened) and in comparators written as `(a, b) -> a - b`. Constraints like `nums[i] <= 10^9` with n up to `10^5` are the interviewer's hint that sums need `long`, and most candidates skim past them.""",
      """It prints **-294967296**. Java `int` arithmetic wraps silently: 4,000,000,000 − 2^32 = −294,967,296. No exception is thrown.

Where it bites in interviews:
- **Sums and prefix sums** over large values → accumulate in `long`.
- **Products** (`w * h`, `a * b % MOD`) → cast one operand *before* multiplying: `(long) w * h`.
- **Comparators**: `(a, b) -> a - b` overflows for large or negative values. For example, `Integer.MIN_VALUE - 1` becomes positive, so the sort order silently breaks. Use `Integer.compare(a, b)`.
- **Midpoints**: `(lo + hi) / 2` when searching over values up to 2^31 − 1.

`Math.addExact` and `Math.multiplyExact` throw `ArithmeticException` instead of wrapping, which is useful when correctness matters more than speed (money, quotas).""",
      "Read the constraints aloud and say \"max sum is 10^5 × 10^9 = 10^14, so I'll use long\" before writing the loop.",
      options=["4000000000", "-294967296", "It throws ArithmeticException", "2147483647"], answer=1,
      fix=f"""```java
{OVF_FIX}
```""",
      askedAt=["Goldman Sachs", "JPMorgan", "Amazon"]),

    T("trap-dsa-greedy-vs-dp", A, "Greedy coin change fails on arbitrary coins", "Intermediate", "Very common",
      """Coins = `{1, 3, 4}`, amount = `6`, minimise the number of coins. The candidate proposes: "Always take the largest coin that fits, it's O(n) and obviously optimal." What does greedy return, and what is optimal?""",
      "Greedy is optimal because taking the biggest coin first always minimises the count.",
      """Greedy works for real currencies (₹1, 2, 5, 10...), which are designed to be "canonical", so everyday intuition says it always works. Candidates also see greedy succeed on the interviewer's first example and never search for a counterexample. The deeper miss is not knowing that greedy needs a **proof** (an exchange argument). DP is the safe default when choices interact.""",
      """Greedy takes 4, then 1, then 1 = **3 coins**. The optimum is 3 + 3 = **2 coins**. Greedy can even fail to find a solution that exists: with coins `{5, 2}` and amount 6, it takes 5 and gets stuck, while 2 + 2 + 2 works.

Use DP: `dp[a] = min over coins c of dp[a - c] + 1`, with `dp[0] = 0`. That is O(amount × coins) time and O(amount) space.

When *is* greedy right? When you can prove that swapping the greedy choice into any optimal solution never makes it worse. Classic cases: interval scheduling by earliest end time, Huffman coding, and Jump Game reachability. In an interview, if you propose greedy, either give that argument in one sentence or try two or three small counterexamples out loud. That habit alone separates mid-level from senior signal.""",
      "Whenever you propose greedy, immediately say \"let me try to break it with a small counterexample\" and do it.",
      options=[
          "Greedy returns 2, which is optimal.",
          "Greedy returns 3 (4+1+1) but the optimum is 2 (3+3).",
          "Both return 3.",
          "Greedy finds no answer.",
      ], answer=1,
      fix=f"""```java
{COIN_FIX}
```
`minCoins({{1,3,4}}, 6) = 2`, `minCoins({{2,5}}, 6) = 3`, `minCoins({{2}}, 3) = -1`.""",
      askedAt=["Amazon", "Flipkart", "Walmart"]),

    T("trap-dsa-sliding-window-negatives", A, "Sliding window with negative numbers", "Intermediate", "Very common",
      f"""Count subarrays whose sum equals `k`. The array **can contain negative numbers**. The candidate uses a shrinking window:

```java
{SW_BUGGY}
```

For `nums = [1, -1, 1]`, `k = 1`, the correct answer is 3. What does this return, and why?""",
      "Sliding window is O(n) and works for any subarray-sum problem; just tweak the shrink condition.",
      """"Subarray" plus "sum" pattern-matches to sliding window, so candidates reach for it without checking its precondition: the window sum must change **monotonically**, growing when you extend right and shrinking when you move left. That only holds when all numbers are non-negative. With negatives, a window whose sum is too big can become valid again by *adding* elements, so shrinking throws away answers.""",
      """It returns **2** and misses `[1, -1, 1]`. When negatives are allowed, use **prefix sums + a hash map**:

- Let `prefix` be the sum of `nums[0..i]`. A subarray `(j, i]` sums to `k` exactly when `prefix_i - prefix_j = k`.
- Keep a map of `prefix value → count seen so far`. At each index, add `map[prefix - k]` to the answer.
- Seed the map with `{0: 1}` so subarrays starting at index 0 are counted. Forgetting this is the second most common bug.

This is O(n) time and O(n) space. The same idea solves "longest subarray with sum k" (store the *first* index of each prefix) and "subarray sum divisible by k" (store `prefix % k`, normalised to be non-negative).

Rule of thumb: sliding window for **non-negative** arrays or "at most K distinct" style constraints; prefix sum + hash map when negatives are possible.""",
      "Ask \"can values be negative?\" before choosing a window; the answer decides the algorithm.",
      options=["3", "2", "1", "It loops forever"], answer=1,
      fix=f"""```java
{SW_FIX}
```""",
      askedAt=["Amazon", "Meta", "PhonePe"]),

    T("trap-dsa-directed-cycle-detection", A, "Directed cycle detection with a single visited set", "Intermediate", "Common",
      """Course Schedule: edges are `0→1, 0→2, 1→3, 2→3`. The candidate runs a DFS with one `visited` set and reports "cycle" whenever it reaches an already-visited node. What does it report for this graph?""",
      "A visited set is enough: seeing a visited node again always means there is a cycle.",
      """The undirected version (visited + parent check) is what most people learn first, and they reuse it unchanged for directed graphs. In a directed graph, reaching a node twice through two different paths (a diamond) is completely normal. Only an edge back to a node that is **still on the current DFS path** forms a cycle. Small test cases without diamonds pass, so the bug survives until the interviewer draws one.""",
      """It reports a **false cycle**: DFS goes 0→1→3, backtracks, then 0→2→3, and node 3 is already visited.

Correct options for **directed** graphs:
- **Three colours**: unvisited, on the current path (gray), done (black). A cycle exists only if you hit a **gray** node. Once a node is black, reaching it again is fine.
- **Kahn's algorithm (BFS topological sort)**: repeatedly remove nodes with in-degree 0. If fewer than n nodes are removed, there is a cycle. It is iterative, so there is no stack-overflow risk at 10^5 nodes, and it also produces the course order (Course Schedule II).

For **undirected** graphs, use visited + "ignore the edge back to my parent", or union-find (an edge whose endpoints already share a root closes a cycle).

Both directed approaches are O(V + E).""",
      "When you hear \"dependencies\" or \"prerequisites\", say \"directed graph, so I need on-path tracking or Kahn's\" up front.",
      options=[
          "No cycle (correct).",
          "Cycle: a false positive, because node 3 is reached by two different paths.",
          "StackOverflowError.",
          "It depends on adjacency order but is never wrong.",
      ], answer=1,
      fix=f"""```java
{CYC_FIX}
```""",
      askedAt=["Amazon", "Atlassian", "Swiggy"]),

    T("trap-dsa-recursion-complexity", A, "Naive recursion: exponential time and hidden stack space", "Basic", "Very common",
      f"""The candidate writes this and says: "It's O(n) time and O(1) space since I don't allocate anything."

```java
{REC_PROMPT}
```

What is the real complexity?""",
      "O(n) time and O(1) space, because there is one call per value of n and no extra data structures.",
      """Candidates count the *distinct* inputs (n of them) instead of the *calls*, and forget that the same subproblem is recomputed again and again. They also treat the call stack as free, because nothing is "allocated". Interviewers specifically probe complexity claims, and a confident wrong answer hurts more than an honest "let me draw the recursion tree".""",
      """Each call branches into two, giving a recursion tree of depth n. Time is **O(2^n)** (tightly about O(1.618^n)). ways(40) makes over 300 million calls. Space is **O(n)** for the call stack, because the deepest chain is n frames.

The fixes:
- **Memoisation**: each state is computed once. Time = number of states × work per state = O(n). Space O(n) for the memo plus O(n) for the stack.
- **Bottom-up with two variables**: O(n) time, O(1) space, and no recursion depth.

Recursion depth is a practical concern too. With the default JVM stack, a recursive DFS on a 10^5-node linked list or skewed tree can throw `StackOverflowError`. Mention that an iterative version or an explicit stack avoids it.

General recipe to state complexity: **number of states × transitions per state**, plus the **maximum stack depth** for space.""",
      "Draw the first three levels of the recursion tree before stating complexity; the repetition becomes obvious to you and the interviewer.",
      options=[
          "O(n) time, O(1) space",
          "O(2^n) time (about 1.618^n), O(n) stack space",
          "O(n log n) time, O(n) space",
          "O(n^2) time, O(1) space",
      ], answer=1,
      fix=f"""```java
{REC_FIX}
```""",
      askedAt=["Amazon", "Infosys", "Paytm"]),
]

HEAD = "import java.util.*;\n"

CHECKS = [
    {"name": "dsa-binary-search", "lang": "java", "code": HEAD + "public class Main {\n" + BS_FIX + """
  static int buggy(int[] nums, int target, int maxIter) {
    int it = 0;
""" + "\n".join("    " + l for l in BS_BUGGY.replace("while (lo < hi) {", "while (lo < hi) { if (++it > maxIter) return -999;").splitlines()) + """
  }
  static int half(int[] nums, int target) { int lo = 0, hi = nums.length - 1; while (lo < hi) { int mid = lo + (hi - lo) / 2; if (nums[mid] < target) lo = mid + 1; else hi = mid; } return lo; }
  public static void main(String[] a) {
    System.out.println(lowerBound(new int[]{1,2,2,2,5}, 2) + " " + lowerBound(new int[]{1,2,3}, 4) + " " + lowerBound(new int[]{}, 1) + " " + lowerBound(new int[]{1,1}, 0));
    System.out.println("buggy " + buggy(new int[]{1,2}, 2, 1000) + " " + buggy(new int[]{1,2,3}, 4, 1000) + " half " + half(new int[]{1,2,3}, 4));
  }
}""", "expect": ["1 3 0 0", "buggy -999 -999 half 2"]},
    {"name": "dsa-bfs", "lang": "java", "code": HEAD + "public class Main {\n static int[][] DIRS = {{1,0},{-1,0},{0,1},{0,-1}};\n" + BFS_FIX + """
  public static void main(String[] a) {
    int[][] g = new int[50][50];
    System.out.println(shortestPath(g) + " " + shortestPath(new int[][]{{0,1},{1,0}}) + " " + shortestPath(new int[][]{{0,0,0},{1,1,0},{0,0,0}}));
  }
}""", "expect": ["98 -1 4"]},
    {"name": "dsa-dijkstra", "lang": "java", "code": HEAD + "public class Main {\n" + DIJ_FIX + """
  public static void main(String[] a) {
    List<List<int[]>> adj = new ArrayList<>();
    for (int i = 0; i < 4; i++) adj.add(new ArrayList<>());
    adj.get(0).add(new int[]{1, 4}); adj.get(0).add(new int[]{2, 1}); adj.get(2).add(new int[]{1, 2}); adj.get(1).add(new int[]{3, 1});
    System.out.println(Arrays.toString(dijkstra(adj, 0)));
  }
}""", "expect": ["[0, 3, 1, 4]"]},
    {"name": "dsa-overflow", "lang": "java", "code": HEAD + """public class Main {
  public static void main(String[] args) {
""" + OVF_PROMPT + """
    long MOD = 1_000_000_007L, a = 999_999_999L, b = 999_999_998L; int width = 100_000, height = 100_000, p = 1, q = 2;
    List<Integer> list = new ArrayList<>(List.of(Integer.MIN_VALUE, 1, -5));
    int[] nums2 = nums;
    { long sum2 = 0; for (int x : nums2) sum2 += x; System.out.println("sum " + sum2); }
    long area = (long) width * height;
    long prod = (a % MOD) * (b % MOD) % MOD;
    list.sort((x, y) -> Integer.compare(x, y));
    int checked = Math.addExact(p, q);
    System.out.println(area + " " + prod + " " + list + " " + checked);
    List<Integer> bad = new ArrayList<>(List.of(Integer.MIN_VALUE, 1)); bad.sort((x, y) -> x - y); System.out.println("bad " + bad);
  }
}""", "expect": ["-294967296", "sum 4000000000", "10000000000 ", "[-2147483648, -5, 1] 3", "bad [1, -2147483648]"]},
    {"name": "dsa-coins", "lang": "java", "code": HEAD + "public class Main {\n" + COIN_FIX + """
  public static void main(String[] a) {
    System.out.println(minCoins(new int[]{1,3,4}, 6) + " " + minCoins(new int[]{2,5}, 6) + " " + minCoins(new int[]{2}, 3));
  }
}""", "expect": ["2 3 -1"]},
    {"name": "dsa-sliding", "lang": "java", "code": HEAD + "public class Main {\n" + SW_FIX + """
  static int buggy(int[] nums, int k) {
""" + SW_BUGGY + """
  }
  public static void main(String[] a) {
    int[] n = {1, -1, 1};
    System.out.println(subarraySum(n, 1) + " " + buggy(n, 1) + " " + subarraySum(new int[]{1,1,1}, 2));
  }
}""", "expect": ["3 2 2"]},
    {"name": "dsa-cycle", "lang": "java", "code": HEAD + "public class Main {\n" + CYC_FIX + """
  static List<List<Integer>> g(int n, int[][] e) { List<List<Integer>> adj = new ArrayList<>(); for (int i = 0; i < n; i++) adj.add(new ArrayList<>()); for (int[] x : e) adj.get(x[0]).add(x[1]); return adj; }
  public static void main(String[] a) {
    System.out.println(hasCycle(g(4, new int[][]{{0,1},{0,2},{1,3},{2,3}})) + " " + hasCycle(g(3, new int[][]{{0,1},{1,2},{2,0}})));
  }
}""", "expect": ["false true"]},
    {"name": "dsa-recursion", "lang": "java", "code": HEAD + "public class Main {\n" + REC_FIX + """
  static long calls = 0;
  static int naive(int n) { calls++; if (n <= 1) return 1; return naive(n - 1) + naive(n - 2); }
  public static void main(String[] a) {
    naive(40);
    System.out.println(ways(40, new long[41]) + " " + waysIter(40) + " calls=" + calls);
  }
}""", "expect": ["165580141 165580141 calls=331160281"]},
]
