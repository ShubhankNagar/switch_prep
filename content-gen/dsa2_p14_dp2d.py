from dsa2_common import P

INTRO = r"""
**2D DP** uses two indices for the state. It shows up in three main shapes:

1. **Grid DP** — `dp[r][c]` = answer for reaching cell (r, c). (Unique Paths, min path sum.)
2. **Two-sequence DP** — `dp[i][j]` = answer for the first i chars of A and first j chars of B. (LCS, Edit Distance, Interleaving String, Distinct Subsequences.)
3. **Item × capacity (knapsack)** — `dp[i][s]` = using the first i items, can we / how many ways to reach s. (Target Sum, Coin Change II.)
4. Plus two special ones: **interval DP** `dp[l][r]` over a range (Burst Balloons) and **state-machine DP** `dp[i][state]` (stock with cooldown).

**How to recognize it**: two strings compared character by character; a grid with only right/down moves; "number of ways to pick items to reach a sum"; choosing the *last* operation in a range.

**Two-string template**
```java
int m = a.length(), n = b.length();
int[][] dp = new int[m + 1][n + 1];          // row 0 / col 0 = empty prefix
for (int i = 0; i <= m; i++) dp[i][0] = BASE_COL;
for (int j = 0; j <= n; j++) dp[0][j] = BASE_ROW;
for (int i = 1; i <= m; i++) {
    for (int j = 1; j <= n; j++) {
        if (a.charAt(i - 1) == b.charAt(j - 1)) dp[i][j] = dp[i - 1][j - 1] + MATCH;
        else dp[i][j] = combine(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
}
return dp[m][n];
```

**Space optimization**: if row i only reads row i−1, keep one or two 1D arrays. Explain it after giving the 2D version — clarity first.

**Knapsack loop order (very common trap)**
- 0/1 (each item once): items outer, sum loop **descending**.
- Unbounded (reuse allowed), counting *combinations*: coins outer, sum **ascending**.
- Counting *permutations* (order matters): sum outer, coins inner.

**Pitfalls**
- Using `i`/`j` directly on the string instead of `i−1`/`j−1` when dp has a padding row.
- Drawing the table on paper for a tiny example before coding catches 90% of bugs — do it in the interview too.
"""

PROBLEMS = [
P("unique-paths", "Unique Paths", "Medium", ["Amazon", "Google", "Microsoft", "Walmart", "Paytm"],
"""A robot starts at the top-left of an m×n grid and can only move right or down. Count the distinct paths to the bottom-right corner. For a 3×7 grid the answer is 28.""",
"""**State:** `dp[r][c]` = number of paths to cell (r, c).

**Recurrence:** you arrive from above or from the left: `dp[r][c] = dp[r−1][c] + dp[r][c−1]`. First row and first column are all 1.

**Space:** each row only needs the previous row, so a single 1D array works: `dp[c] += dp[c−1]`.

Math alternative: choose which (m−1) of the (m+n−2) moves are "down" → C(m+n−2, m−1).""",
r"""
import java.util.*;

class Solution {
    public int uniquePaths(int m, int n) {
        int[] dp = new int[n];
        Arrays.fill(dp, 1);
        for (int r = 1; r < m; r++) {
            for (int c = 1; c < n; c++) {
                dp[c] += dp[c - 1]; // from above (old dp[c]) + from left
            }
        }
        return dp[n - 1];
    }
}
""", "O(m · n)", "O(n)", True),

P("longest-common-subsequence", "Longest Common Subsequence", "Medium", ["Amazon", "Google", "Microsoft", "Adobe", "Goldman Sachs", "Oracle"],
"""Return the length of the longest sequence of characters that appears in both strings in the same relative order (not necessarily contiguous). `"abcde"` and `"ace"` → 3.""",
"""**State:** `dp[i][j]` = LCS of `a[0..i)` and `b[0..j)`.

**Recurrence:**
- If `a[i−1] == b[j−1]`: `dp[i][j] = dp[i−1][j−1] + 1` (use the match).
- Else: `dp[i][j] = max(dp[i−1][j], dp[i][j−1])` (drop one char from either string).

Base: row/column 0 = 0. This is the **parent problem** of many string DPs (shortest common supersequence, min deletions to make strings equal, longest palindromic subsequence = LCS(s, reverse(s))).""",
r"""
class Solution {
    public int longestCommonSubsequence(String text1, String text2) {
        int m = text1.length(), n = text2.length();
        int[][] dp = new int[m + 1][n + 1];
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (text1.charAt(i - 1) == text2.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }
        return dp[m][n];
    }
}
""", "O(m · n)", "O(m · n)", True),

P("edit-distance", "Edit Distance", "Medium", ["Amazon", "Google", "Microsoft", "Uber", "Goldman Sachs", "Adobe"],
"""Return the minimum number of single-character insertions, deletions or replacements to convert word1 into word2. `"horse"` → `"ros"` takes 3 operations.""",
"""**State:** `dp[i][j]` = min edits to turn `word1[0..i)` into `word2[0..j)`.

**Base:** `dp[i][0] = i` (delete everything), `dp[0][j] = j` (insert everything).

**Recurrence:**
- Last chars equal → `dp[i][j] = dp[i−1][j−1]` (no cost).
- Else `1 + min(dp[i−1][j] (delete), dp[i][j−1] (insert), dp[i−1][j−1] (replace))`.

Classic interview DP — be able to explain what each of the three neighbours means.""",
r"""
class Solution {
    public int minDistance(String word1, String word2) {
        int m = word1.length(), n = word2.length();
        int[][] dp = new int[m + 1][n + 1];
        for (int i = 0; i <= m; i++) dp[i][0] = i;
        for (int j = 0; j <= n; j++) dp[0][j] = j;
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (word1.charAt(i - 1) == word2.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    dp[i][j] = 1 + Math.min(dp[i - 1][j - 1], Math.min(dp[i - 1][j], dp[i][j - 1]));
                }
            }
        }
        return dp[m][n];
    }
}
""", "O(m · n)", "O(m · n)", True),

P("target-sum", "Target Sum", "Medium", ["Amazon", "Google", "Microsoft", "Adobe", "Flipkart"],
"""Put a `+` or `-` sign in front of each number and count the sign assignments whose expression equals target. `[1,1,1,1,1]`, target 3 → 5.""",
"""**Brute force:** 2^n sign choices.

**Key insight — reduce to subset sum:** let P = sum of numbers with `+`, N = those with `−`. Then `P − N = target` and `P + N = total`, so `P = (total + target) / 2`. Count subsets with that sum. If `total + target` is odd or `|target| > total`, the answer is 0.

**0/1 knapsack counting:** `dp[s]` = number of subsets with sum s; `dp[0] = 1`; for each x, for s from P down to x: `dp[s] += dp[s − x]`. (Zeros are handled correctly — they double the count.)""",
r"""
class Solution {
    public int findTargetSumWays(int[] nums, int target) {
        int total = 0;
        for (int x : nums) total += x;
        if (Math.abs(target) > total || (total + target) % 2 != 0) return 0;
        int p = (total + target) / 2;
        int[] dp = new int[p + 1];
        dp[0] = 1;
        for (int x : nums) {
            for (int s = p; s >= x; s--) {
                dp[s] += dp[s - x];
            }
        }
        return dp[p];
    }
}
""", "O(n · sum)", "O(sum)", True),

P("coin-change-ii", "Coin Change II", "Medium", ["Amazon", "Google", "Microsoft", "Walmart", "PhonePe"],
"""Given coin denominations with unlimited supply, count the number of **combinations** that make up an amount (order doesn't matter). Amount 5 with `[1,2,5]` → 4: `5, 2+2+1, 2+1+1+1, 1+1+1+1+1`.""",
"""**State:** `dp[i][a]` = ways to make a using the first i coin types → compresses to `dp[a]`.

**Recurrence:** for each coin c (outer loop), for a from c up to amount (ascending, because reuse is allowed): `dp[a] += dp[a − c]`. Base `dp[0] = 1`.

**Why coins outer?** It fixes an order of coin types, so `1+2` and `2+1` are counted once. Swapping the loops counts permutations instead (that's Combination Sum IV) — a favourite follow-up question.""",
r"""
class Solution {
    public int change(int amount, int[] coins) {
        int[] dp = new int[amount + 1];
        dp[0] = 1;
        for (int c : coins) {
            for (int a = c; a <= amount; a++) {
                dp[a] += dp[a - c];
            }
        }
        return dp[amount];
    }
}
""", "O(coins · amount)", "O(amount)", True),

P("interleaving-string", "Interleaving String", "Medium", ["Amazon", "Google", "Microsoft"],
"""Decide whether s3 can be formed by interleaving s1 and s2 — i.e. merging them while keeping each string's own character order. `s1="aabcc"`, `s2="dbbca"`, `s3="aadbbcbcac"` → true.""",
"""**State:** `dp[i][j]` = can the first i chars of s1 and first j chars of s2 form the first i+j chars of s3.

**Recurrence:** the last char of `s3[0..i+j)` came from s1 or from s2:
`dp[i][j] = (dp[i−1][j] && s1[i−1] == s3[i+j−1]) || (dp[i][j−1] && s2[j−1] == s3[i+j−1])`.

Base `dp[0][0] = true`. If lengths don't add up, return false immediately. Greedy (take from whichever matches) fails when both match.""",
r"""
class Solution {
    public boolean isInterleave(String s1, String s2, String s3) {
        int m = s1.length(), n = s2.length();
        if (m + n != s3.length()) return false;
        boolean[][] dp = new boolean[m + 1][n + 1];
        dp[0][0] = true;
        for (int i = 0; i <= m; i++) {
            for (int j = 0; j <= n; j++) {
                if (i > 0 && dp[i - 1][j] && s1.charAt(i - 1) == s3.charAt(i + j - 1)) dp[i][j] = true;
                if (j > 0 && dp[i][j - 1] && s2.charAt(j - 1) == s3.charAt(i + j - 1)) dp[i][j] = true;
            }
        }
        return dp[m][n];
    }
}
""", "O(m · n)", "O(m · n)", False),

P("distinct-subsequences", "Distinct Subsequences", "Hard", ["Amazon", "Google", "Microsoft"],
"""Count how many distinct subsequences of s are equal to t (distinct by the positions chosen). `s = "rabbbit"`, `t = "rabbit"` → 3 (pick any two of the three b's).""",
"""**State:** `dp[i][j]` = number of ways the first i chars of s can form the first j chars of t.

**Base:** `dp[i][0] = 1` (empty t is formed once by deleting everything); `dp[0][j>0] = 0`.

**Recurrence:**
- Always: `dp[i][j] = dp[i−1][j]` (don't use `s[i−1]`).
- If `s[i−1] == t[j−1]`: also add `dp[i−1][j−1]` (use it to match `t[j−1]`).

1D version: iterate j **backwards** so `dp[j−1]` still holds the previous row.""",
r"""
class Solution {
    public int numDistinct(String s, String t) {
        int m = s.length(), n = t.length();
        int[] dp = new int[n + 1];
        dp[0] = 1;
        for (int i = 1; i <= m; i++) {
            for (int j = Math.min(i, n); j >= 1; j--) {
                if (s.charAt(i - 1) == t.charAt(j - 1)) dp[j] += dp[j - 1];
            }
        }
        return dp[n];
    }
}
""", "O(m · n)", "O(n)", False),

P("longest-increasing-path-in-a-matrix", "Longest Increasing Path in a Matrix", "Hard", ["Amazon", "Google", "Microsoft", "Uber", "Flipkart"],
"""In an integer matrix, move up/down/left/right to a strictly larger neighbour. Return the length of the longest such increasing path. For `[[9,9,4],[6,6,8],[2,1,1]]` → 4 (`1→2→6→9`).""",
"""**Brute force:** DFS from every cell exploring all increasing paths — exponential.

**Key insight:** because moves must strictly increase, there are **no cycles**, so the longest path starting at a cell is fixed → **DFS + memoisation**.

**State:** `memo[r][c]` = longest increasing path starting at (r, c).
**Recurrence:** `memo[r][c] = 1 + max(memo[neighbour])` over neighbours with a larger value.

Each cell is computed once → O(m·n). No visited array needed (strict increase prevents revisiting).""",
r"""
class Solution {
    private static final int[][] DIRS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    private int[][] memo;

    public int longestIncreasingPath(int[][] matrix) {
        int m = matrix.length, n = matrix[0].length, best = 0;
        memo = new int[m][n];
        for (int r = 0; r < m; r++)
            for (int c = 0; c < n; c++)
                best = Math.max(best, dfs(matrix, r, c));
        return best;
    }

    private int dfs(int[][] g, int r, int c) {
        if (memo[r][c] != 0) return memo[r][c];
        int longest = 1;
        for (int[] d : DIRS) {
            int nr = r + d[0], nc = c + d[1];
            if (nr < 0 || nc < 0 || nr >= g.length || nc >= g[0].length || g[nr][nc] <= g[r][c]) continue;
            longest = Math.max(longest, 1 + dfs(g, nr, nc));
        }
        return memo[r][c] = longest;
    }
}
""", "O(m · n)", "O(m · n)", True),

P("burst-balloons", "Burst Balloons", "Hard", ["Amazon", "Google", "Microsoft", "Flipkart"],
"""Balloons have numbers; bursting balloon i earns `left · nums[i] · right`, where left/right are its current neighbours (treat outside as 1). Burst all balloons in the best order and return the maximum coins. `[3,1,5,8]` → 167.""",
"""**Why it's hard:** choosing which balloon to burst *first* changes neighbours unpredictably.

**Key insight — think about the LAST balloon burst in a range.** Pad the array with 1 at both ends. For an open interval `(l, r)`, if k is the last balloon burst inside it, its neighbours at that moment are exactly `l` and `r`, and the two sides are independent.

**State:** `dp[l][r]` = max coins from bursting all balloons strictly between l and r.
**Recurrence:** `dp[l][r] = max over l<k<r of dp[l][k] + a[l]·a[k]·a[r] + dp[k][r]`.

Fill by increasing interval length. Answer `dp[0][n+1]`. This is the template for **interval DP** (matrix chain multiplication is the same shape).""",
r"""
class Solution {
    public int maxCoins(int[] nums) {
        int n = nums.length;
        int[] a = new int[n + 2];
        a[0] = a[n + 1] = 1;
        for (int i = 0; i < n; i++) a[i + 1] = nums[i];
        int[][] dp = new int[n + 2][n + 2];
        for (int len = 2; len <= n + 1; len++) {
            for (int l = 0; l + len <= n + 1; l++) {
                int r = l + len;
                for (int k = l + 1; k < r; k++) {
                    dp[l][r] = Math.max(dp[l][r], dp[l][k] + a[l] * a[k] * a[r] + dp[k][r]);
                }
            }
        }
        return dp[0][n + 1];
    }
}
""", "O(n^3)", "O(n^2)", False),

P("best-time-to-buy-and-sell-stock-with-cooldown", "Best Time to Buy and Sell Stock with Cooldown", "Medium", ["Amazon", "Google", "Microsoft", "Goldman Sachs", "Paytm"],
"""Given daily prices, make as many buy/sell transactions as you like (one share at a time), but after selling you must wait one day before buying again. Return the max profit. `[1,2,3,0,2]` → 3 (buy, sell, cooldown, buy, sell).""",
"""**State-machine DP.** On each day you're in one of three states:
- `hold` — you own a share,
- `sold` — you sold today (tomorrow is cooldown),
- `rest` — you own nothing and are free to buy.

**Transitions for price p:**
- `hold' = max(hold, rest − p)` (keep holding, or buy from rest)
- `sold' = hold + p` (sell today)
- `rest' = max(rest, sold)` (stay idle, or finish cooldown)

Start `hold = −∞, sold = 0, rest = 0`. Answer `max(sold, rest)`. This framework solves the whole stock series (fees, k transactions) by changing states.""",
r"""
class Solution {
    public int maxProfit(int[] prices) {
        int hold = Integer.MIN_VALUE / 2, sold = 0, rest = 0;
        for (int p : prices) {
            int prevSold = sold;
            sold = hold + p;
            hold = Math.max(hold, rest - p);
            rest = Math.max(rest, prevSold);
        }
        return Math.max(sold, rest);
    }
}
""", "O(n)", "O(1)", False),
]

PATTERN = {"id": "dp-2d", "name": "Dynamic Programming 2D", "order": 14, "intro": INTRO.strip(), "problems": PROBLEMS}
