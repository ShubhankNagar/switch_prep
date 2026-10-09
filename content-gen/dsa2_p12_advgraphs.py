from dsa2_common import P

INTRO = r"""
Once BFS/DFS is comfortable, three more tools cover almost every remaining graph question at SDE-1/SDE-2 level.

**1. Dijkstra — shortest path with non-negative weights.** Recognize: "minimum time/cost/effort", weighted edges. Use a min-heap of `{dist, node}`; pop the smallest, skip stale entries, relax neighbours.
```java
int[] dist = new int[n]; Arrays.fill(dist, Integer.MAX_VALUE); dist[src] = 0;
PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[0], b[0]));
pq.offer(new int[]{0, src});
while (!pq.isEmpty()) {
    int[] top = pq.poll(); int d = top[0], u = top[1];
    if (d > dist[u]) continue;                       // stale entry
    for (int[] e : adj.get(u)) {                      // e = {v, w}
        if (d + e[1] < dist[e[0]]) { dist[e[0]] = d + e[1]; pq.offer(new int[]{dist[e[0]], e[0]}); }
    }
}
```
O((V + E) log V). Doesn't work with negative weights (use Bellman-Ford). If the path has an extra constraint like "at most K edges", Bellman-Ford with K rounds is simpler.

**2. Union-Find (Disjoint Set Union).** Recognize: "connected groups", "merge", "is there a cycle in an undirected graph", "redundant edge", Kruskal's MST.
```java
int[] parent, rank;
int find(int x) { return parent[x] == x ? x : (parent[x] = find(parent[x])); } // path compression
boolean union(int a, int b) {
    int ra = find(a), rb = find(b);
    if (ra == rb) return false;                       // already connected → cycle
    if (rank[ra] < rank[rb]) { int t = ra; ra = rb; rb = t; }
    parent[rb] = ra;
    if (rank[ra] == rank[rb]) rank[ra]++;
    return true;
}
```
Near O(1) per operation (inverse Ackermann).

**3. Minimum Spanning Tree.** Connect all nodes with minimum total cost: **Kruskal** (sort edges + union-find) or **Prim** (min-heap growing from one node — better for dense graphs).

**Pitfalls**
- Forgetting the `if (d > dist[u]) continue;` stale check (still correct, but slower).
- Integer overflow when adding to `Integer.MAX_VALUE` — check for "unreached" first.
- Topological sort on characters (Alien Dictionary): handle the invalid prefix case (`"abc"` before `"ab"`).
"""

PROBLEMS = [
P("network-delay-time", "Network Delay Time", "Medium", ["Amazon", "Google", "Microsoft", "Uber", "Flipkart"],
"""A network has n nodes and directed weighted edges `(u, v, time)`. A signal starts at node k; return the time until every node has received it, or −1 if some node is unreachable.""",
"""**Intuition:** each node receives the signal at its shortest-path distance from k; the answer is the **maximum** of those distances. Weights are non-negative → **Dijkstra**.

Build an adjacency list, run Dijkstra from k, then take the max distance; if any is still infinity, return −1.""",
r"""
import java.util.*;

class Solution {
    public int networkDelayTime(int[][] times, int n, int k) {
        List<List<int[]>> adj = new ArrayList<>();
        for (int i = 0; i <= n; i++) adj.add(new ArrayList<>());
        for (int[] t : times) adj.get(t[0]).add(new int[]{t[1], t[2]});

        int[] dist = new int[n + 1];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[k] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[0], b[0]));
        pq.offer(new int[]{0, k});
        while (!pq.isEmpty()) {
            int[] top = pq.poll();
            int d = top[0], u = top[1];
            if (d > dist[u]) continue;
            for (int[] e : adj.get(u)) {
                int v = e[0], nd = d + e[1];
                if (nd < dist[v]) {
                    dist[v] = nd;
                    pq.offer(new int[]{nd, v});
                }
            }
        }
        int ans = 0;
        for (int i = 1; i <= n; i++) {
            if (dist[i] == Integer.MAX_VALUE) return -1;
            ans = Math.max(ans, dist[i]);
        }
        return ans;
    }
}
""", "O((V + E) log V)", "O(V + E)", True),

P("cheapest-flights-within-k-stops", "Cheapest Flights Within K Stops", "Medium", ["Amazon", "Google", "Microsoft", "Uber", "Swiggy", "Zomato"],
"""Given flights `[from, to, price]`, find the cheapest price from `src` to `dst` using at most k intermediate stops (i.e. at most k+1 flights). Return −1 if no such route exists.""",
"""**Why plain Dijkstra fails:** the cheapest path might use too many stops; a pricier path with fewer stops can still be the right answer, but Dijkstra discards it.

**Bellman-Ford limited to k+1 rounds:** after round i, `dist[v]` is the cheapest cost using at most i edges. In each round, relax all edges using a **copy** of the previous round's array — otherwise one round could chain several edges and break the stop limit.

O(k·E), simple and bug-resistant. (A BFS by levels or Dijkstra with state `(node, stops)` also work.)""",
r"""
import java.util.*;

class Solution {
    public int findCheapestPrice(int n, int[][] flights, int src, int dst, int k) {
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[src] = 0;
        for (int round = 0; round <= k; round++) {
            int[] next = dist.clone();
            for (int[] f : flights) {
                int u = f[0], v = f[1], w = f[2];
                if (dist[u] == Integer.MAX_VALUE) continue;
                if (dist[u] + w < next[v]) next[v] = dist[u] + w;
            }
            dist = next;
        }
        return dist[dst] == Integer.MAX_VALUE ? -1 : dist[dst];
    }
}
""", "O(k · E)", "O(V)", True),

P("min-cost-to-connect-all-points", "Min Cost to Connect All Points", "Medium", ["Amazon", "Google", "Microsoft", "Uber"],
"""Given points on a 2D plane, connecting two points costs their Manhattan distance `|x1-x2| + |y1-y2|`. Return the minimum total cost to connect all points so there's a path between every pair.""",
"""This is a textbook **Minimum Spanning Tree** on a complete graph (every pair is an edge).

**Prim's algorithm (O(n²), no heap):** since the graph is dense, keep `minDist[i]` = cheapest edge from the growing tree to point i. Repeat n times: pick the unvisited point with the smallest `minDist`, add it to the tree (add its cost), and update `minDist` for the rest using distances from the new point.

Kruskal (sort all n² edges + union-find) works too but is O(n² log n).""",
r"""
import java.util.*;

class Solution {
    public int minCostConnectPoints(int[][] points) {
        int n = points.length, total = 0;
        int[] minDist = new int[n];
        Arrays.fill(minDist, Integer.MAX_VALUE);
        boolean[] inTree = new boolean[n];
        minDist[0] = 0;
        for (int iter = 0; iter < n; iter++) {
            int u = -1;
            for (int i = 0; i < n; i++)
                if (!inTree[i] && (u == -1 || minDist[i] < minDist[u])) u = i;
            inTree[u] = true;
            total += minDist[u];
            for (int v = 0; v < n; v++) {
                if (inTree[v]) continue;
                int d = Math.abs(points[u][0] - points[v][0]) + Math.abs(points[u][1] - points[v][1]);
                if (d < minDist[v]) minDist[v] = d;
            }
        }
        return total;
    }
}
""", "O(n^2)", "O(n)", False),

P("redundant-connection", "Redundant Connection", "Medium", ["Amazon", "Google", "Microsoft", "Uber"],
"""A tree with n nodes had one extra edge added, creating exactly one cycle. Given the edge list, return the edge that can be removed to make it a tree again; if several qualify, return the one appearing last in the input.""",
"""**Union-Find** is the cleanest tool: process edges in order and union their endpoints. The first edge whose endpoints are **already in the same set** closes a cycle — that's the redundant one (and, being the edge that completes the cycle, it's the last cycle edge in input order).

With path compression + union by rank, each operation is nearly O(1).""",
r"""
class Solution {
    private int[] parent, rank;

    public int[] findRedundantConnection(int[][] edges) {
        int n = edges.length;
        parent = new int[n + 1];
        rank = new int[n + 1];
        for (int i = 0; i <= n; i++) parent[i] = i;
        for (int[] e : edges) {
            if (!union(e[0], e[1])) return e;
        }
        return new int[0];
    }

    private int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]);
        return parent[x];
    }

    private boolean union(int a, int b) {
        int ra = find(a), rb = find(b);
        if (ra == rb) return false;
        if (rank[ra] < rank[rb]) { int t = ra; ra = rb; rb = t; }
        parent[rb] = ra;
        if (rank[ra] == rank[rb]) rank[ra]++;
        return true;
    }
}
""", "O(n · α(n))", "O(n)", True),

P("number-of-provinces", "Number of Provinces", "Medium", ["Amazon", "Google", "Microsoft", "Goldman Sachs", "Flipkart"],
"""Given an n×n adjacency matrix where `isConnected[i][j] = 1` means cities i and j are directly connected, count the provinces — groups of cities connected directly or indirectly.""",
"""Count connected components. Two equally good approaches:

- **DFS:** for each unvisited city, start a DFS over the matrix row and increment the count.
- **Union-Find:** start with n components; every successful union reduces the count by 1.

Shown below with Union-Find since it's the reusable template. Only scan `j > i` because the matrix is symmetric.""",
r"""
class Solution {
    private int[] parent;

    public int findCircleNum(int[][] isConnected) {
        int n = isConnected.length, components = n;
        parent = new int[n];
        for (int i = 0; i < n; i++) parent[i] = i;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++)
                if (isConnected[i][j] == 1) {
                    int ri = find(i), rj = find(j);
                    if (ri != rj) {
                        parent[ri] = rj;
                        components--;
                    }
                }
        return components;
    }

    private int find(int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]]; // path halving
            x = parent[x];
        }
        return x;
    }
}
""", "O(n^2 · α(n))", "O(n)", True),

P("accounts-merge", "Accounts Merge", "Medium", ["Amazon", "Google", "Microsoft", "Atlassian", "Walmart"],
"""Each account is `[name, email1, email2, ...]`. Two accounts belong to the same person if they share any email. Merge them and return each person as `[name, sorted unique emails...]`.""",
"""**Intuition:** emails are nodes; all emails in one account are connected. Merged people = connected components.

**Union-Find on email strings:** map each email to an id (first time seen) and remember its owner name. For every account, union each email with the account's first email. Then group emails by their root, sort each group, and prepend the name.

DFS on an email graph works equally well; Union-Find avoids building the adjacency list.""",
r"""
import java.util.*;

class Solution {
    private int[] parent;

    public List<List<String>> accountsMerge(List<List<String>> accounts) {
        Map<String, Integer> id = new HashMap<>();
        Map<String, String> owner = new HashMap<>();
        int total = 0;
        for (List<String> acc : accounts) total += acc.size() - 1;
        parent = new int[total];
        for (int i = 0; i < total; i++) parent[i] = i;

        for (List<String> acc : accounts) {
            String name = acc.get(0);
            for (int i = 1; i < acc.size(); i++) {
                String email = acc.get(i);
                id.putIfAbsent(email, id.size());
                owner.put(email, name);
                union(id.get(acc.get(1)), id.get(email));
            }
        }

        Map<Integer, List<String>> groups = new HashMap<>();
        for (String email : id.keySet()) {
            groups.computeIfAbsent(find(id.get(email)), k -> new ArrayList<>()).add(email);
        }
        List<List<String>> res = new ArrayList<>();
        for (List<String> emails : groups.values()) {
            Collections.sort(emails);
            List<String> row = new ArrayList<>();
            row.add(owner.get(emails.get(0)));
            row.addAll(emails);
            res.add(row);
        }
        return res;
    }

    private int find(int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    }

    private void union(int a, int b) {
        parent[find(a)] = find(b);
    }
}
""", "O(N log N), N = total emails (sorting dominates)", "O(N)", True),

P("alien-dictionary", "Alien Dictionary", "Hard", ["Amazon", "Google", "Microsoft", "Uber", "Flipkart", "Atlassian"],
"""A list of words is sorted according to an unknown alphabet. Derive a valid ordering of the letters that appear, or return `""` if the order is contradictory. From `["wrt","wrf","er","ett","rftt"]` one valid answer is `"wertf"`. (LeetCode Premium; the same problem is free on GeeksforGeeks / NeetCode.)""",
"""**Intuition:** compare each pair of adjacent words. The first position where they differ tells you `a[j]` comes before `b[j]` → a directed edge. Everything after that position tells you nothing.

**Invalid case:** if `a` is longer than `b` and `b` is a prefix of `a` (e.g. `"abc"` before `"ab"`), no alphabet works → return `""`.

Then **topological sort** (Kahn's) over all letters that appear. If the output contains fewer letters than exist, there's a cycle → `""`.""",
r"""
import java.util.*;

class Solution {
    public String alienOrder(String[] words) {
        Map<Character, Set<Character>> adj = new HashMap<>();
        Map<Character, Integer> indeg = new HashMap<>();
        for (String w : words)
            for (char c : w.toCharArray()) {
                adj.putIfAbsent(c, new HashSet<>());
                indeg.putIfAbsent(c, 0);
            }

        for (int i = 0; i + 1 < words.length; i++) {
            String a = words[i], b = words[i + 1];
            if (a.length() > b.length() && a.startsWith(b)) return "";
            for (int j = 0; j < Math.min(a.length(), b.length()); j++) {
                char x = a.charAt(j), y = b.charAt(j);
                if (x != y) {
                    if (adj.get(x).add(y)) indeg.merge(y, 1, Integer::sum);
                    break;
                }
            }
        }

        Deque<Character> q = new ArrayDeque<>();
        for (Map.Entry<Character, Integer> e : indeg.entrySet())
            if (e.getValue() == 0) q.offer(e.getKey());
        StringBuilder sb = new StringBuilder();
        while (!q.isEmpty()) {
            char c = q.poll();
            sb.append(c);
            for (char nb : adj.get(c)) {
                if (indeg.merge(nb, -1, Integer::sum) == 0) q.offer(nb);
            }
        }
        return sb.length() == indeg.size() ? sb.toString() : "";
    }
}
""", "O(C), C = total characters in all words", "O(1) (at most 26 letters)", True),

P("swim-in-rising-water", "Swim in Rising Water", "Hard", ["Amazon", "Google", "Microsoft", "Uber"],
"""In an n×n grid of distinct elevations, at time t you can swim between adjacent cells if both elevations are ≤ t. Return the minimum t at which you can get from the top-left to the bottom-right.""",
"""**Reframe:** the cost of a path is the **maximum** elevation on it; minimize that. This is Dijkstra where the path cost is `max` instead of `sum` (a "minimax" path).

Min-heap of `{maxSoFar, r, c}`: pop the cell with the smallest bottleneck, mark it visited; when you pop the destination, its value is the answer. Push each unvisited neighbour with `max(maxSoFar, grid[nr][nc])`.

Alternatives: binary search on t + BFS (O(n² log n)), or Union-Find adding cells in elevation order.""",
r"""
import java.util.*;

class Solution {
    public int swimInWater(int[][] grid) {
        int n = grid.length;
        boolean[][] seen = new boolean[n][n];
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[0], b[0]));
        pq.offer(new int[]{grid[0][0], 0, 0});
        seen[0][0] = true;
        int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        while (!pq.isEmpty()) {
            int[] cur = pq.poll();
            int t = cur[0], r = cur[1], c = cur[2];
            if (r == n - 1 && c == n - 1) return t;
            for (int[] d : dirs) {
                int nr = r + d[0], nc = c + d[1];
                if (nr < 0 || nc < 0 || nr >= n || nc >= n || seen[nr][nc]) continue;
                seen[nr][nc] = true;
                pq.offer(new int[]{Math.max(t, grid[nr][nc]), nr, nc});
            }
        }
        return -1;
    }
}
""", "O(n^2 log n)", "O(n^2)", False),
]

PATTERN = {"id": "advanced-graphs", "name": "Advanced Graphs", "order": 12, "intro": INTRO.strip(), "problems": PROBLEMS}
