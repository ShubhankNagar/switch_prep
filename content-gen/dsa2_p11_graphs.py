from dsa2_common import P

INTRO = r"""
A **graph** is nodes + edges. In interviews it appears either explicitly (edge list, adjacency list, prerequisites) or implicitly (a 2D grid where each cell is a node connected to its 4 neighbours, or words connected by one-letter changes).

**How to recognize it**
- "connected", "islands", "regions", "reachable", "spread", "minimum steps", "order of tasks", "dependencies".
- Grid + "count groups" → DFS/BFS flood fill. Grid + "minimum time/steps" → **BFS** (multi-source if many starts).
- "Can all tasks finish / give an order" → **topological sort** (Kahn's BFS on in-degrees).

**DFS vs BFS**
- DFS: simpler to write, good for counting components and marking regions.
- BFS: gives the **shortest path in an unweighted graph** — level by level.

**Grid BFS template**
```java
int[][] DIRS = {{1,0},{-1,0},{0,1},{0,-1}};
Deque<int[]> q = new ArrayDeque<>();
boolean[][] seen = new boolean[m][n];
q.offer(new int[]{sr, sc}); seen[sr][sc] = true;
int steps = 0;
while (!q.isEmpty()) {
    for (int size = q.size(); size > 0; size--) {   // one level
        int[] cur = q.poll();
        if (isTarget(cur)) return steps;
        for (int[] d : DIRS) {
            int r = cur[0] + d[0], c = cur[1] + d[1];
            if (r < 0 || c < 0 || r >= m || c >= n || seen[r][c] || blocked(r, c)) continue;
            seen[r][c] = true;                 // mark when ENQUEUING
            q.offer(new int[]{r, c});
        }
    }
    steps++;
}
```

**Building an adjacency list**
```java
List<List<Integer>> adj = new ArrayList<>();
for (int i = 0; i < n; i++) adj.add(new ArrayList<>());
for (int[] e : edges) { adj.get(e[0]).add(e[1]); adj.get(e[1]).add(e[0]); }
```

**Pitfalls**
- Marking visited when *dequeuing* instead of enqueuing → same node queued many times (TLE).
- Recursive DFS on a 10^5-node path can overflow the stack — mention iterative BFS as backup.
- Directed cycle detection needs 3 states (unvisited / visiting / done), not just a visited flag.
- Complexity is O(V + E); for a grid that's O(m·n).
"""

PROBLEMS = [
P("number-of-islands", "Number of Islands", "Medium", ["Amazon", "Microsoft", "Google", "Flipkart", "Uber", "Swiggy", "PhonePe", "Walmart"],
"""Given a grid of `'1'` (land) and `'0'` (water), count the islands, where an island is a group of land cells joined horizontally or vertically. A grid with two separate blobs of 1s returns 2.""",
"""**Intuition:** scan every cell; when you hit unvisited land, that's a new island — increment the count and flood-fill (DFS/BFS) all land connected to it so it's never counted again.

**Trick:** sink visited land by setting it to `'0'` — no extra visited array needed (mention you're mutating input; copy it if that's not allowed).

Each cell is visited a constant number of times → O(m·n). Union-Find is an alternative and shines when cells are added dynamically (Number of Islands II).""",
r"""
class Solution {
    public int numIslands(char[][] grid) {
        int count = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == '1') {
                    count++;
                    sink(grid, r, c);
                }
            }
        }
        return count;
    }

    private void sink(char[][] g, int r, int c) {
        if (r < 0 || c < 0 || r >= g.length || c >= g[0].length || g[r][c] != '1') return;
        g[r][c] = '0';
        sink(g, r + 1, c);
        sink(g, r - 1, c);
        sink(g, r, c + 1);
        sink(g, r, c - 1);
    }
}
""", "O(m · n)", "O(m · n) worst-case recursion", True),

P("max-area-of-island", "Max Area of Island", "Medium", ["Amazon", "Microsoft", "Google", "Paytm"],
"""In a 0/1 grid, the area of an island is its number of connected 1-cells (4-directional). Return the largest area, or 0 if there's no land.""",
"""Same skeleton as Number of Islands, but the DFS **returns the size** of what it sinks: `1 + dfs(up) + dfs(down) + dfs(left) + dfs(right)`. Track the maximum over all starting cells.""",
r"""
class Solution {
    public int maxAreaOfIsland(int[][] grid) {
        int best = 0;
        for (int r = 0; r < grid.length; r++)
            for (int c = 0; c < grid[0].length; c++)
                if (grid[r][c] == 1) best = Math.max(best, area(grid, r, c));
        return best;
    }

    private int area(int[][] g, int r, int c) {
        if (r < 0 || c < 0 || r >= g.length || c >= g[0].length || g[r][c] != 1) return 0;
        g[r][c] = 0;
        return 1 + area(g, r + 1, c) + area(g, r - 1, c) + area(g, r, c + 1) + area(g, r, c - 1);
    }
}
""", "O(m · n)", "O(m · n)", False),

P("clone-graph", "Clone Graph", "Medium", ["Amazon", "Microsoft", "Google", "Uber", "Salesforce"],
"""Given a reference to one node of a connected undirected graph (each node has a value and a list of neighbours), return a deep copy of the whole graph. The copy must use brand-new node objects with the same structure.""",
"""**Intuition:** traverse the graph and keep a `HashMap<Node, Node>` from original to clone. The map does double duty: it's the visited set *and* lets you wire up edges to clones that already exist (cycles!).

DFS: if the node is in the map, return its clone; otherwise create the clone, put it in the map **before** recursing (prevents infinite loops), then clone each neighbour and add it.""",
r"""
import java.util.*;

/*
// Definition for a Node (provided by LeetCode).
class Node {
    public int val;
    public List<Node> neighbors;
    public Node() { val = 0; neighbors = new ArrayList<Node>(); }
    public Node(int _val) { val = _val; neighbors = new ArrayList<Node>(); }
    public Node(int _val, ArrayList<Node> _neighbors) { val = _val; neighbors = _neighbors; }
}
*/

class Solution {
    private final Map<Node, Node> copies = new HashMap<>();

    public Node cloneGraph(Node node) {
        if (node == null) return null;
        if (copies.containsKey(node)) return copies.get(node);
        Node copy = new Node(node.val);
        copies.put(node, copy); // register before visiting neighbours
        for (Node nb : node.neighbors) {
            copy.neighbors.add(cloneGraph(nb));
        }
        return copy;
    }
}
""", "O(V + E)", "O(V)", True),

P("rotting-oranges", "Rotting Oranges", "Medium", ["Amazon", "Microsoft", "Google", "Flipkart", "Zomato", "Walmart"],
"""A grid has empty cells (0), fresh oranges (1) and rotten oranges (2). Each minute, every fresh orange next to a rotten one rots. Return the minutes until no fresh orange remains, or −1 if some can never rot.""",
"""**Intuition:** rot spreads simultaneously from *all* rotten oranges — that's **multi-source BFS**. Put every rotten orange in the queue at time 0 and count fresh oranges.

Process level by level; each level is one minute. When you rot a neighbour, decrement `fresh`. At the end, return `minutes` if `fresh == 0`, else −1.

**Pitfall:** only increment minutes if the level actually rotted something (or loop while `fresh > 0`), otherwise you'll overcount by one.""",
r"""
import java.util.*;

class Solution {
    public int orangesRotting(int[][] grid) {
        int m = grid.length, n = grid[0].length, fresh = 0;
        Deque<int[]> q = new ArrayDeque<>();
        for (int r = 0; r < m; r++)
            for (int c = 0; c < n; c++) {
                if (grid[r][c] == 2) q.offer(new int[]{r, c});
                else if (grid[r][c] == 1) fresh++;
            }
        int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        int minutes = 0;
        while (!q.isEmpty() && fresh > 0) {
            for (int size = q.size(); size > 0; size--) {
                int[] cur = q.poll();
                for (int[] d : dirs) {
                    int r = cur[0] + d[0], c = cur[1] + d[1];
                    if (r < 0 || c < 0 || r >= m || c >= n || grid[r][c] != 1) continue;
                    grid[r][c] = 2;
                    fresh--;
                    q.offer(new int[]{r, c});
                }
            }
            minutes++;
        }
        return fresh == 0 ? minutes : -1;
    }
}
""", "O(m · n)", "O(m · n)", True),

P("01-matrix", "01 Matrix", "Medium", ["Amazon", "Google", "Microsoft", "Uber"],
"""Given a binary matrix, return a matrix where each cell holds the distance (in 4-directional steps) to its nearest 0. Cells that are 0 have distance 0.""",
"""**Brute force:** BFS from every 1 → O((mn)^2).

**Optimal — reverse the direction:** run one multi-source BFS starting from **all zeros** at distance 0. Initialize 1-cells to −1 (unvisited). When BFS first reaches a cell, that's its shortest distance: `dist[nb] = dist[cur] + 1`.

This "start from targets, not sources" trick appears often (walls and gates, nearest exit).""",
r"""
import java.util.*;

class Solution {
    public int[][] updateMatrix(int[][] mat) {
        int m = mat.length, n = mat[0].length;
        int[][] dist = new int[m][n];
        Deque<int[]> q = new ArrayDeque<>();
        for (int r = 0; r < m; r++)
            for (int c = 0; c < n; c++) {
                if (mat[r][c] == 0) q.offer(new int[]{r, c});
                else dist[r][c] = -1;
            }
        int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        while (!q.isEmpty()) {
            int[] cur = q.poll();
            for (int[] d : dirs) {
                int r = cur[0] + d[0], c = cur[1] + d[1];
                if (r < 0 || c < 0 || r >= m || c >= n || dist[r][c] != -1) continue;
                dist[r][c] = dist[cur[0]][cur[1]] + 1;
                q.offer(new int[]{r, c});
            }
        }
        return dist;
    }
}
""", "O(m · n)", "O(m · n)", False),

P("course-schedule", "Course Schedule", "Medium", ["Amazon", "Microsoft", "Google", "Uber", "Flipkart", "Atlassian", "PhonePe"],
"""There are `numCourses` courses and pairs `[a, b]` meaning you must take b before a. Decide whether it's possible to finish all courses. `[[1,0],[0,1]]` is impossible because the two courses depend on each other.""",
"""**Reframe:** courses are nodes, prerequisites are directed edges `b → a`. All courses can be finished iff the graph has **no cycle**.

**Kahn's algorithm (BFS topological sort):** compute in-degrees; push every node with in-degree 0; repeatedly pop a node, count it, and decrement neighbours' in-degree, pushing any that drop to 0. If the count of processed nodes equals `numCourses`, there's no cycle.

Alternative: DFS with 3 colours — a back edge to a "visiting" node means a cycle.""",
r"""
import java.util.*;

class Solution {
    public boolean canFinish(int numCourses, int[][] prerequisites) {
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < numCourses; i++) adj.add(new ArrayList<>());
        int[] indeg = new int[numCourses];
        for (int[] p : prerequisites) {
            adj.get(p[1]).add(p[0]);
            indeg[p[0]]++;
        }
        Deque<Integer> q = new ArrayDeque<>();
        for (int i = 0; i < numCourses; i++) if (indeg[i] == 0) q.offer(i);
        int done = 0;
        while (!q.isEmpty()) {
            int cur = q.poll();
            done++;
            for (int next : adj.get(cur)) {
                if (--indeg[next] == 0) q.offer(next);
            }
        }
        return done == numCourses;
    }
}
""", "O(V + E)", "O(V + E)", True),

P("course-schedule-ii", "Course Schedule II", "Medium", ["Amazon", "Microsoft", "Google", "Uber", "Flipkart"],
"""Same setup as Course Schedule, but return one valid order in which to take all courses, or an empty array if it's impossible. For 4 courses with `[[1,0],[2,0],[3,1],[3,2]]`, `[0,1,2,3]` and `[0,2,1,3]` are both valid.""",
"""Run Kahn's algorithm exactly as in Course Schedule, but **append each popped node to the result**. The pop order is a topological order. If the result has fewer than `numCourses` entries, a cycle blocked some courses → return an empty array.

This is the standard **topological sort** template; it also solves build-order, task dependency and "parallel courses" questions.""",
r"""
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
        Deque<Integer> q = new ArrayDeque<>();
        for (int i = 0; i < numCourses; i++) if (indeg[i] == 0) q.offer(i);
        int[] order = new int[numCourses];
        int idx = 0;
        while (!q.isEmpty()) {
            int cur = q.poll();
            order[idx++] = cur;
            for (int next : adj.get(cur)) {
                if (--indeg[next] == 0) q.offer(next);
            }
        }
        return idx == numCourses ? order : new int[0];
    }
}
""", "O(V + E)", "O(V + E)", True),

P("pacific-atlantic-water-flow", "Pacific Atlantic Water Flow", "Medium", ["Amazon", "Google", "Microsoft", "Uber"],
"""A height grid touches the Pacific on its top/left edges and the Atlantic on its bottom/right edges. Water flows from a cell to a neighbour of equal or lower height. Return all cells from which water can reach both oceans.""",
"""**Brute force:** DFS from every cell to see whether it reaches both oceans → O((mn)^2).

**Key insight — reverse the flow:** start from the ocean borders and walk **uphill** (to neighbours with height ≥ current). Every cell reached from the Pacific border can drain into the Pacific. Do the same for the Atlantic. The answer is the intersection of the two visited sets.

Two DFS passes, each O(m·n).""",
r"""
import java.util.*;

class Solution {
    private int m, n;

    public List<List<Integer>> pacificAtlantic(int[][] heights) {
        m = heights.length;
        n = heights[0].length;
        boolean[][] pac = new boolean[m][n], atl = new boolean[m][n];
        for (int r = 0; r < m; r++) {
            dfs(heights, pac, r, 0, Integer.MIN_VALUE);
            dfs(heights, atl, r, n - 1, Integer.MIN_VALUE);
        }
        for (int c = 0; c < n; c++) {
            dfs(heights, pac, 0, c, Integer.MIN_VALUE);
            dfs(heights, atl, m - 1, c, Integer.MIN_VALUE);
        }
        List<List<Integer>> res = new ArrayList<>();
        for (int r = 0; r < m; r++)
            for (int c = 0; c < n; c++)
                if (pac[r][c] && atl[r][c]) res.add(List.of(r, c));
        return res;
    }

    private void dfs(int[][] h, boolean[][] seen, int r, int c, int prev) {
        if (r < 0 || c < 0 || r >= m || c >= n || seen[r][c] || h[r][c] < prev) return;
        seen[r][c] = true;
        dfs(h, seen, r + 1, c, h[r][c]);
        dfs(h, seen, r - 1, c, h[r][c]);
        dfs(h, seen, r, c + 1, h[r][c]);
        dfs(h, seen, r, c - 1, h[r][c]);
    }
}
""", "O(m · n)", "O(m · n)", False),

P("surrounded-regions", "Surrounded Regions", "Medium", ["Amazon", "Google", "Microsoft", "Adobe"],
"""A board contains `'X'` and `'O'`. Flip every `'O'` that is completely enclosed by `'X'` into `'X'` (in place). An `'O'` region that touches the border, directly or through other `'O'`s, survives.""",
"""**Key insight — think in reverse:** instead of finding enclosed regions, find the *safe* ones. Any `'O'` connected to the border can't be captured.

1. DFS from every border `'O'`, marking reachable cells as a temporary `'#'`.
2. Sweep the board: remaining `'O'` → `'X'` (captured), `'#'` → `'O'` (restored).

Same "start from the boundary" idea as Pacific Atlantic.""",
r"""
class Solution {
    public void solve(char[][] board) {
        int m = board.length, n = board[0].length;
        for (int r = 0; r < m; r++) {
            mark(board, r, 0);
            mark(board, r, n - 1);
        }
        for (int c = 0; c < n; c++) {
            mark(board, 0, c);
            mark(board, m - 1, c);
        }
        for (int r = 0; r < m; r++)
            for (int c = 0; c < n; c++) {
                if (board[r][c] == 'O') board[r][c] = 'X';
                else if (board[r][c] == '#') board[r][c] = 'O';
            }
    }

    private void mark(char[][] b, int r, int c) {
        if (r < 0 || c < 0 || r >= b.length || c >= b[0].length || b[r][c] != 'O') return;
        b[r][c] = '#';
        mark(b, r + 1, c);
        mark(b, r - 1, c);
        mark(b, r, c + 1);
        mark(b, r, c - 1);
    }
}
""", "O(m · n)", "O(m · n)", False),

P("word-ladder", "Word Ladder", "Hard", ["Amazon", "Google", "Microsoft", "Uber", "Salesforce"],
"""Given a start word, an end word and a dictionary, find the length of the shortest transformation sequence where each step changes exactly one letter and every intermediate word is in the dictionary (count includes both ends). `hit → hot → dot → dog → cog` gives 5; return 0 if impossible.""",
"""**Intuition:** words are nodes, an edge joins words differing by one letter, and we want the shortest path → **BFS**.

Don't build the graph explicitly (O(N²·L)). Instead, for each word popped, try replacing every position with `'a'..'z'` and check the dictionary `HashSet` — O(26·L) neighbours. Remove words from the set when enqueued (acts as visited).

Return the level when you reach `endWord`. Bidirectional BFS is a good follow-up optimization.""",
r"""
import java.util.*;

class Solution {
    public int ladderLength(String beginWord, String endWord, List<String> wordList) {
        Set<String> dict = new HashSet<>(wordList);
        if (!dict.contains(endWord)) return 0;
        Deque<String> q = new ArrayDeque<>();
        q.offer(beginWord);
        dict.remove(beginWord);
        int level = 1;
        while (!q.isEmpty()) {
            for (int size = q.size(); size > 0; size--) {
                char[] w = q.poll().toCharArray();
                for (int i = 0; i < w.length; i++) {
                    char orig = w[i];
                    for (char ch = 'a'; ch <= 'z'; ch++) {
                        if (ch == orig) continue;
                        w[i] = ch;
                        String next = new String(w);
                        if (next.equals(endWord)) return level + 1;
                        if (dict.remove(next)) q.offer(next);
                    }
                    w[i] = orig;
                }
            }
            level++;
        }
        return 0;
    }
}
""", "O(N · L · 26)", "O(N · L)", True),

P("is-graph-bipartite", "Is Graph Bipartite?", "Medium", ["Amazon", "Google", "Microsoft", "Uber"],
"""Given an undirected graph as an adjacency list, decide whether its nodes can be split into two groups so that every edge connects nodes from different groups. A triangle is not bipartite; a square is.""",
"""**Intuition:** try to 2-colour the graph. BFS/DFS from each uncoloured node (the graph may be disconnected), colour it 0, and give every neighbour the opposite colour. If you ever find a neighbour already painted the **same** colour as the current node, the graph isn't bipartite.

Equivalent fact: a graph is bipartite iff it has no odd-length cycle.""",
r"""
import java.util.*;

class Solution {
    public boolean isBipartite(int[][] graph) {
        int n = graph.length;
        int[] color = new int[n];
        Arrays.fill(color, -1);
        for (int start = 0; start < n; start++) {
            if (color[start] != -1) continue;
            Deque<Integer> q = new ArrayDeque<>();
            q.offer(start);
            color[start] = 0;
            while (!q.isEmpty()) {
                int u = q.poll();
                for (int v : graph[u]) {
                    if (color[v] == -1) {
                        color[v] = 1 - color[u];
                        q.offer(v);
                    } else if (color[v] == color[u]) {
                        return false;
                    }
                }
            }
        }
        return true;
    }
}
""", "O(V + E)", "O(V)", False),

P("shortest-path-in-binary-matrix", "Shortest Path in Binary Matrix", "Medium", ["Amazon", "Google", "Microsoft", "Swiggy"],
"""In an n×n 0/1 grid, find the length (number of cells) of the shortest path from the top-left to the bottom-right moving through 0-cells in any of 8 directions. Return −1 if no such path exists.""",
"""Unweighted shortest path → **BFS**. Start at (0,0) with distance 1 (if it's 0). Explore 8 neighbours; mark visited by setting the cell to 1 when enqueuing. The first time you pop (n−1, n−1), its distance is the answer.

**Edge cases:** start or end blocked → −1; a 1×1 grid with `0` → 1.""",
r"""
import java.util.*;

class Solution {
    public int shortestPathBinaryMatrix(int[][] grid) {
        int n = grid.length;
        if (grid[0][0] == 1 || grid[n - 1][n - 1] == 1) return -1;
        Deque<int[]> q = new ArrayDeque<>();
        q.offer(new int[]{0, 0});
        grid[0][0] = 1;
        int dist = 1;
        while (!q.isEmpty()) {
            for (int size = q.size(); size > 0; size--) {
                int[] cur = q.poll();
                if (cur[0] == n - 1 && cur[1] == n - 1) return dist;
                for (int dr = -1; dr <= 1; dr++)
                    for (int dc = -1; dc <= 1; dc++) {
                        int r = cur[0] + dr, c = cur[1] + dc;
                        if (r < 0 || c < 0 || r >= n || c >= n || grid[r][c] != 0) continue;
                        grid[r][c] = 1;
                        q.offer(new int[]{r, c});
                    }
            }
            dist++;
        }
        return -1;
    }
}
""", "O(n^2)", "O(n^2)", False),
]

PATTERN = {"id": "graphs", "name": "Graphs (BFS/DFS)", "order": 11, "intro": INTRO.strip(), "problems": PROBLEMS}
