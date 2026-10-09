from dsa2_common import P

INTRO = r"""
**Dynamic Programming** = recursion + remembering answers to overlapping subproblems. 1D DP means the state is a single index (position in array/string, or an amount).

**How to recognize it**
- "Number of ways", "minimum/maximum cost", "is it possible", "longest/shortest ..." — and greedy choices clearly fail.
- The answer for position i depends on answers for smaller positions (i−1, i−2, or some j < i).

**The 4-step recipe (say this out loud in interviews)**
1. **State:** `dp[i]` = answer for the prefix ending at / starting from i (define it in words!).
2. **Recurrence:** how `dp[i]` is built from smaller states.
3. **Base cases:** `dp[0]`, `dp[1]`, empty string, amount 0.
4. **Order & answer:** fill left→right; answer is `dp[n]` or `max(dp)`.

**Template (bottom-up)**
```java
int[] dp = new int[n + 1];
dp[0] = BASE;
for (int i = 1; i <= n; i++) {
    dp[i] = INITIAL;                       // e.g. 0, Integer.MAX_VALUE
    for (/* each choice that leads to i */) {
        dp[i] = combine(dp[i], dp[prev] + cost);   // min / max / sum
    }
}
return dp[n];
```
Start with top-down (recursion + `memo[]`) if that's how you think, then convert. When `dp[i]` only needs `dp[i-1]` and `dp[i-2]`, replace the array with two variables (O(1) space) — interviewers love this follow-up.

**Families in this section**
- Fibonacci-style: climbing stairs, house robber, decode ways.
- Unbounded choices: coin change, word break.
- Subset sum (0/1 knapsack in 1D): partition equal subset — iterate the sum **backwards**.
- "Ending at i": LIS, max product subarray (track both min and max).
- Expand-around-centre: palindromic substrings.

**Pitfalls**
- `Integer.MAX_VALUE + 1` overflow in min-DP → use `amount + 1` as infinity.
- Off-by-one between `dp[i]` meaning "first i chars" vs "char at i".
- Forgetting the base case that makes everything else work (`dp[0] = 1` for counting ways, `true` for word break).
"""

PROBLEMS = [
P("climbing-stairs", "Climbing Stairs", "Easy", ["Amazon", "Google", "Adobe", "Microsoft", "Paytm"],
"""You climb a staircase of n steps, taking 1 or 2 steps at a time. Count the distinct ways to reach the top. For n = 3: `1+1+1, 1+2, 2+1` → 3.""",
"""**State:** `ways(i)` = number of ways to reach step i.

**Recurrence:** the last move was either 1 step (from i−1) or 2 steps (from i−2), so `ways(i) = ways(i−1) + ways(i−2)`. Base: `ways(0)=1, ways(1)=1`. It's Fibonacci.

Plain recursion is O(2^n); memoisation or bottom-up is O(n); two rolling variables bring space to O(1).""",
r"""
class Solution {
    public int climbStairs(int n) {
        int prev2 = 1, prev1 = 1; // ways(0), ways(1)
        for (int i = 2; i <= n; i++) {
            int cur = prev1 + prev2;
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
""", "O(n)", "O(1)", True),

P("house-robber", "House Robber", "Medium", ["Amazon", "Google", "Microsoft", "Flipkart", "Walmart", "Paytm"],
"""Houses in a row hold some money; you can't rob two adjacent houses. Return the maximum amount you can rob. For `[2,7,9,3,1]` → 2 + 9 + 1 = 12.""",
"""**State:** `dp[i]` = best total using houses `0..i`.

**Recurrence:** either skip house i (`dp[i−1]`) or rob it (`dp[i−2] + nums[i]`): `dp[i] = max(dp[i−1], dp[i−2] + nums[i])`.

Only two previous values are needed, so keep `prev2`, `prev1`. Brute force tries all non-adjacent subsets (O(2^n)).""",
r"""
class Solution {
    public int rob(int[] nums) {
        int prev2 = 0, prev1 = 0; // best up to i-2, best up to i-1
        for (int x : nums) {
            int cur = Math.max(prev1, prev2 + x);
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
""", "O(n)", "O(1)", True),

P("house-robber-ii", "House Robber II", "Medium", ["Amazon", "Google", "Microsoft", "Adobe"],
"""Same as House Robber, but the houses form a circle, so the first and last houses are adjacent. For `[2,3,2]` the answer is 3 (can't take both 2s).""",
"""**Key insight:** the first and last house can't both be robbed, so the answer is the better of two linear problems:
- rob among houses `0..n−2` (exclude last), or
- rob among houses `1..n−1` (exclude first).

Reuse the House Robber helper on index ranges. Edge case: a single house → return it.""",
r"""
class Solution {
    public int rob(int[] nums) {
        int n = nums.length;
        if (n == 1) return nums[0];
        return Math.max(robRange(nums, 0, n - 2), robRange(nums, 1, n - 1));
    }

    private int robRange(int[] nums, int lo, int hi) {
        int prev2 = 0, prev1 = 0;
        for (int i = lo; i <= hi; i++) {
            int cur = Math.max(prev1, prev2 + nums[i]);
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
""", "O(n)", "O(1)", False),

P("coin-change", "Coin Change", "Medium", ["Amazon", "Google", "Microsoft", "Flipkart", "Goldman Sachs", "PhonePe", "Paytm"],
"""Given coin denominations (unlimited supply) and an amount, return the fewest coins that make up the amount, or −1 if impossible. Coins `[1,2,5]`, amount 11 → 3 (5+5+1).""",
"""**Why not greedy?** Coins `[1,3,4]`, amount 6: greedy picks 4+1+1 (3 coins) but 3+3 (2 coins) is better.

**State:** `dp[a]` = min coins to make amount a.

**Recurrence:** `dp[a] = min over coins c ≤ a of dp[a − c] + 1`. Base `dp[0] = 0`. Use `amount + 1` as "infinity" (no answer can need more coins than the amount) to avoid overflow.

Answer: `dp[amount]` if it's ≤ amount, else −1.""",
r"""
import java.util.*;

class Solution {
    public int coinChange(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1);
        dp[0] = 0;
        for (int a = 1; a <= amount; a++) {
            for (int c : coins) {
                if (c <= a) dp[a] = Math.min(dp[a], dp[a - c] + 1);
            }
        }
        return dp[amount] > amount ? -1 : dp[amount];
    }
}
""", "O(amount · coins)", "O(amount)", True),

P("longest-increasing-subsequence", "Longest Increasing Subsequence", "Medium", ["Amazon", "Google", "Microsoft", "Flipkart", "Uber", "Adobe"],
"""Return the length of the longest strictly increasing subsequence (not necessarily contiguous). For `[10,9,2,5,3,7,101,18]` → 4, e.g. `[2,3,7,101]`.""",
"""**O(n²) DP:** `dp[i]` = length of the LIS ending at i. `dp[i] = 1 + max(dp[j])` over `j < i` with `nums[j] < nums[i]`. Answer = `max(dp)`.

**O(n log n) — patience sorting:** maintain `tails`, where `tails[k]` = smallest possible tail of an increasing subsequence of length k+1. For each number, binary-search the first tail ≥ it and replace it (or append if none). `tails` stays sorted; its size is the LIS length. Know both — interviewers usually start with O(n²) and ask for the optimization.""",
r"""
class Solution {
    public int lengthOfLIS(int[] nums) {
        int[] tails = new int[nums.length];
        int size = 0;
        for (int x : nums) {
            int lo = 0, hi = size;
            while (lo < hi) {               // first index with tails[idx] >= x
                int mid = (lo + hi) >>> 1;
                if (tails[mid] < x) lo = mid + 1;
                else hi = mid;
            }
            tails[lo] = x;
            if (lo == size) size++;
        }
        return size;
    }
}
""", "O(n log n)", "O(n)", True),

P("word-break", "Word Break", "Medium", ["Amazon", "Google", "Microsoft", "Uber", "Flipkart", "Walmart", "Salesforce"],
"""Given a string and a dictionary, decide whether the string can be split into a sequence of one or more dictionary words (words can repeat). `"leetcode"` with `["leet","code"]` → true.""",
"""**Brute force:** try every prefix that's a word and recurse on the rest — exponential because suffixes repeat.

**State:** `dp[i]` = true if the first i characters can be segmented.

**Recurrence:** `dp[i] = true` if some `j < i` has `dp[j] == true` and `s[j..i)` is in the dictionary. Base `dp[0] = true` (empty prefix).

Put the dictionary in a `HashSet`. Optionally limit `j` to `i − maxWordLen` to speed it up.""",
r"""
import java.util.*;

class Solution {
    public boolean wordBreak(String s, List<String> wordDict) {
        Set<String> dict = new HashSet<>(wordDict);
        int maxLen = 0;
        for (String w : wordDict) maxLen = Math.max(maxLen, w.length());
        int n = s.length();
        boolean[] dp = new boolean[n + 1];
        dp[0] = true;
        for (int i = 1; i <= n; i++) {
            for (int j = Math.max(0, i - maxLen); j < i; j++) {
                if (dp[j] && dict.contains(s.substring(j, i))) {
                    dp[i] = true;
                    break;
                }
            }
        }
        return dp[n];
    }
}
""", "O(n · L · L), L = max word length", "O(n)", True),

P("decode-ways", "Decode Ways", "Medium", ["Amazon", "Google", "Microsoft", "Uber", "Goldman Sachs"],
"""Letters are encoded as `A=1 ... Z=26`. Given a digit string, count how many ways it can be decoded. `"226"` → 3 (`2 2 6`, `22 6`, `2 26`); `"06"` → 0 because `06` isn't valid.""",
"""**State:** `dp[i]` = ways to decode the first i characters.

**Recurrence:**
- If `s[i−1] != '0'`, the last char alone is a letter: `dp[i] += dp[i−1]`.
- If the last two chars form 10..26: `dp[i] += dp[i−2]`.

Base: `dp[0] = 1`. Like climbing stairs but with validity conditions. Zeros are the trap — `'0'` can only appear as part of `10` or `20`. Rolling variables give O(1) space.""",
r"""
class Solution {
    public int numDecodings(String s) {
        int n = s.length();
        int prev2 = 1;                              // dp[0]
        int prev1 = s.charAt(0) == '0' ? 0 : 1;      // dp[1]
        for (int i = 2; i <= n; i++) {
            int cur = 0;
            if (s.charAt(i - 1) != '0') cur += prev1;
            int two = (s.charAt(i - 2) - '0') * 10 + (s.charAt(i - 1) - '0');
            if (two >= 10 && two <= 26) cur += prev2;
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
""", "O(n)", "O(1)", True),

P("partition-equal-subset-sum", "Partition Equal Subset Sum", "Medium", ["Amazon", "Google", "Microsoft", "Adobe", "Flipkart"],
"""Decide whether an array of positive integers can be split into two subsets with equal sums. `[1,5,11,5]` → true (`[1,5,5]` and `[11]`); `[1,2,3,5]` → false.""",
"""**Reduce:** if the total is odd → false. Otherwise ask: is there a subset summing to `total / 2`? That's **0/1 knapsack / subset sum**.

**State:** `dp[s]` = can some subset of the numbers seen so far sum to s.

**Recurrence:** for each number x, for s from target **down to** x: `dp[s] |= dp[s − x]`. Iterating backwards ensures each number is used at most once (iterating forward would let x be reused — that's the unbounded version). Base `dp[0] = true`.""",
r"""
class Solution {
    public boolean canPartition(int[] nums) {
        int total = 0;
        for (int x : nums) total += x;
        if (total % 2 != 0) return false;
        int target = total / 2;
        boolean[] dp = new boolean[target + 1];
        dp[0] = true;
        for (int x : nums) {
            for (int s = target; s >= x; s--) {
                dp[s] = dp[s] || dp[s - x];
            }
            if (dp[target]) return true;
        }
        return dp[target];
    }
}
""", "O(n · sum)", "O(sum)", True),

P("maximum-product-subarray", "Maximum Product Subarray", "Medium", ["Amazon", "Google", "Microsoft", "Goldman Sachs", "Adobe"],
"""Find the contiguous subarray with the largest product and return that product. `[2,3,-2,4]` → 6 (`[2,3]`); `[-2,0,-1]` → 0.""",
"""**Why Kadane alone fails:** a negative number can turn the *smallest* product into the *largest* one.

**State:** for the subarray ending at i, track both `maxEnd` and `minEnd`.

**Recurrence:** for current x, candidates are `x`, `maxEnd·x`, `minEnd·x`. New `maxEnd` = max of the three; new `minEnd` = min of the three (compute both from the old values). Answer = max `maxEnd` seen. Zero naturally resets both.""",
r"""
class Solution {
    public int maxProduct(int[] nums) {
        int maxEnd = nums[0], minEnd = nums[0], best = nums[0];
        for (int i = 1; i < nums.length; i++) {
            int x = nums[i];
            int a = maxEnd * x, b = minEnd * x;
            maxEnd = Math.max(x, Math.max(a, b));
            minEnd = Math.min(x, Math.min(a, b));
            best = Math.max(best, maxEnd);
        }
        return best;
    }
}
""", "O(n)", "O(1)", True),

P("longest-palindromic-substring", "Longest Palindromic Substring", "Medium", ["Amazon", "Microsoft", "Google", "Adobe", "Oracle", "Walmart"],
"""Return the longest contiguous substring that reads the same forwards and backwards. `"babad"` → `"bab"` (or `"aba"`); `"cbbd"` → `"bb"`.""",
"""**Brute force:** check all O(n²) substrings, each in O(n) → O(n³).

**DP:** `pal[i][j] = s[i]==s[j] && (j−i < 2 || pal[i+1][j−1])` → O(n²) time and space.

**Expand around centre (best in interviews):** every palindrome has a centre — either a character (odd length) or a gap between two characters (even length). For each of the 2n−1 centres, expand outward while both ends match, and track the longest. O(n²) time, O(1) space.""",
r"""
class Solution {
    public String longestPalindrome(String s) {
        int bestStart = 0, bestLen = 0;
        for (int c = 0; c < s.length(); c++) {
            int odd = expand(s, c, c);
            int even = expand(s, c, c + 1);
            int len = Math.max(odd, even);
            if (len > bestLen) {
                bestLen = len;
                bestStart = c - (len - 1) / 2;
            }
        }
        return s.substring(bestStart, bestStart + bestLen);
    }

    private int expand(String s, int l, int r) {
        while (l >= 0 && r < s.length() && s.charAt(l) == s.charAt(r)) {
            l--;
            r++;
        }
        return r - l - 1;
    }
}
""", "O(n^2)", "O(1)", True),

P("palindromic-substrings", "Palindromic Substrings", "Medium", ["Amazon", "Google", "Microsoft", "Adobe"],
"""Count how many substrings of a string are palindromes (substrings at different positions count separately). `"aaa"` → 6: three `a`, two `aa`, one `aaa`.""",
"""Same technique as Longest Palindromic Substring: **expand around each of the 2n−1 centres**. Every successful expansion step is one more palindrome, so add 1 to the count each time the ends match.

The DP table `pal[i][j]` also works (count the true cells) but uses O(n²) space.""",
r"""
class Solution {
    public int countSubstrings(String s) {
        int count = 0;
        for (int c = 0; c < s.length(); c++) {
            count += expand(s, c, c);     // odd length
            count += expand(s, c, c + 1); // even length
        }
        return count;
    }

    private int expand(String s, int l, int r) {
        int found = 0;
        while (l >= 0 && r < s.length() && s.charAt(l) == s.charAt(r)) {
            found++;
            l--;
            r++;
        }
        return found;
    }
}
""", "O(n^2)", "O(1)", False),
]

PATTERN = {"id": "dp-1d", "name": "Dynamic Programming 1D", "order": 13, "intro": INTRO.strip(), "problems": PROBLEMS}
