from dsa2_common import P

INTRO = r"""
**Backtracking** is a controlled brute force: you build a candidate answer one choice at a time, and as soon as a partial choice can't lead to a valid answer you *undo* it and try the next option. Think of it as DFS over a "decision tree".

**How to recognize it**
- The question says *all*, *every*, *generate*, *list all combinations/permutations/partitions*.
- Constraints are small (n ≤ 10–20) because output itself is exponential.
- You need to place things under constraints (N-Queens, Sudoku, word on a grid).

**Reusable template**
```java
void backtrack(int start, List<Integer> path, List<List<Integer>> res, int[] nums) {
    if (isComplete(path)) {               // base case
        res.add(new ArrayList<>(path));   // COPY the path!
        return;
    }
    for (int i = start; i < nums.length; i++) {
        if (i > start && nums[i] == nums[i - 1]) continue; // skip duplicates (sorted input)
        if (!isValid(nums[i])) continue;                     // prune
        path.add(nums[i]);                // choose
        backtrack(i + 1, path, res, nums); // explore (i for reuse, i+1 for no reuse)
        path.remove(path.size() - 1);     // un-choose
    }
}
```

**Three questions to answer before coding**
1. What is one *choice* at each level? (include/exclude, which number next, where to cut the string)
2. When is the path *complete*?
3. What can I *prune* early? (sum exceeded, invalid placement)

**Pitfalls**
- Adding `path` itself instead of `new ArrayList<>(path)` — all results end up empty.
- Forgetting to undo state (remove from path, unmark visited, restore grid cell).
- Duplicates: sort first, then skip `nums[i] == nums[i-1]` only when `i > start`.
- `start` index vs `used[]` array: combinations/subsets use `start`; permutations use `used[]`.

**Complexity talk**: subsets O(n·2^n), permutations O(n·n!). Interviewers accept this — just state it.
"""

PROBLEMS = [
P("subsets", "Subsets", "Medium", ["Amazon", "Microsoft", "Google", "Flipkart", "Adobe"],
"""Given an array of distinct integers, return every possible subset (the power set) in any order. For `[1,2,3]` the answer has 8 subsets: `[], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]`.""",
"""**Intuition:** every element is either in or out, so there are 2^n subsets. Backtracking with a `start` index generates each subset exactly once: at each call, the current path *is* a valid subset, so record it, then try extending it with each later element.

**Key insight:** record the path at every node of the recursion tree, not only at leaves. Using `start` prevents generating `[2,1]` after `[1,2]`.

An alternative is the bitmask approach: for `mask` from 0 to 2^n − 1, include `nums[i]` when bit `i` is set.""",
r"""
import java.util.*;

class Solution {
    public List<List<Integer>> subsets(int[] nums) {
        List<List<Integer>> res = new ArrayList<>();
        backtrack(nums, 0, new ArrayList<>(), res);
        return res;
    }

    private void backtrack(int[] nums, int start, List<Integer> path, List<List<Integer>> res) {
        res.add(new ArrayList<>(path));
        for (int i = start; i < nums.length; i++) {
            path.add(nums[i]);
            backtrack(nums, i + 1, path, res);
            path.remove(path.size() - 1);
        }
    }
}
""", "O(n · 2^n)", "O(n) recursion (excluding output)", True),

P("subsets-ii", "Subsets II", "Medium", ["Amazon", "Microsoft", "Adobe"],
"""Same as Subsets, but the array may contain duplicates and the result must not contain duplicate subsets. For `[1,2,2]` the answer is `[], [1], [1,2], [1,2,2], [2], [2,2]`.""",
"""**Intuition:** sort the array so equal values sit together. In the loop of a given recursion level, picking the second `2` at the same level as the first `2` would produce an identical subtree — so skip it.

**Rule:** `if (i > start && nums[i] == nums[i-1]) continue;` The `i > start` condition still allows using a duplicate as the *next deeper* element (that's how `[2,2]` appears), but blocks using it as an alternative at the same level.""",
r"""
import java.util.*;

class Solution {
    public List<List<Integer>> subsetsWithDup(int[] nums) {
        Arrays.sort(nums);
        List<List<Integer>> res = new ArrayList<>();
        backtrack(nums, 0, new ArrayList<>(), res);
        return res;
    }

    private void backtrack(int[] nums, int start, List<Integer> path, List<List<Integer>> res) {
        res.add(new ArrayList<>(path));
        for (int i = start; i < nums.length; i++) {
            if (i > start && nums[i] == nums[i - 1]) continue;
            path.add(nums[i]);
            backtrack(nums, i + 1, path, res);
            path.remove(path.size() - 1);
        }
    }
}
""", "O(n · 2^n)", "O(n)", False),

P("permutations", "Permutations", "Medium", ["Amazon", "Microsoft", "Google", "Uber", "Goldman Sachs"],
"""Given an array of distinct integers, return all possible orderings. For `[1,2,3]` there are 6: `[1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], [3,2,1]`.""",
"""**Intuition:** at each position you may place any number not already used. Unlike subsets, order matters, so the loop always starts from index 0 and a `boolean[] used` tracks what's in the path.

**Base case:** path length equals n → record a copy.

Alternative: swap-based permutation (swap `nums[start]` with each `nums[i]`, recurse on `start+1`, swap back) which avoids the extra `used` array.""",
r"""
import java.util.*;

class Solution {
    public List<List<Integer>> permute(int[] nums) {
        List<List<Integer>> res = new ArrayList<>();
        backtrack(nums, new boolean[nums.length], new ArrayList<>(), res);
        return res;
    }

    private void backtrack(int[] nums, boolean[] used, List<Integer> path, List<List<Integer>> res) {
        if (path.size() == nums.length) {
            res.add(new ArrayList<>(path));
            return;
        }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            used[i] = true;
            path.add(nums[i]);
            backtrack(nums, used, path, res);
            path.remove(path.size() - 1);
            used[i] = false;
        }
    }
}
""", "O(n · n!)", "O(n)", True),

P("combination-sum", "Combination Sum", "Medium", ["Amazon", "Microsoft", "Uber", "Adobe", "Walmart"],
"""Given distinct positive candidates and a target, return all unique combinations that add up to the target; each candidate can be used unlimited times. For `candidates = [2,3,6,7], target = 7` the answer is `[[2,2,3],[7]]`.""",
"""**Intuition:** choose a number, subtract it from the remaining target, recurse. Because reuse is allowed, recurse with the *same* index `i` (not `i+1`). Passing `start` prevents the same combination in different orders (`[2,2,3]` vs `[3,2,2]`).

**Pruning:** sort candidates; once `candidates[i] > remaining`, every later candidate is also too large, so `break`.

**Base cases:** remaining == 0 → record; the sort+break handles the negative case.""",
r"""
import java.util.*;

class Solution {
    public List<List<Integer>> combinationSum(int[] candidates, int target) {
        Arrays.sort(candidates);
        List<List<Integer>> res = new ArrayList<>();
        backtrack(candidates, 0, target, new ArrayList<>(), res);
        return res;
    }

    private void backtrack(int[] c, int start, int remain, List<Integer> path, List<List<Integer>> res) {
        if (remain == 0) {
            res.add(new ArrayList<>(path));
            return;
        }
        for (int i = start; i < c.length; i++) {
            if (c[i] > remain) break;
            path.add(c[i]);
            backtrack(c, i, remain - c[i], path, res); // i: reuse allowed
            path.remove(path.size() - 1);
        }
    }
}
""", "O(2^t) roughly, t = target / min(candidate)", "O(target / min)", True),

P("combination-sum-ii", "Combination Sum II", "Medium", ["Amazon", "Microsoft", "Adobe"],
"""Candidates may contain duplicates and each element can be used at most once; return unique combinations that sum to target. For `[10,1,2,7,6,1,5], target = 8` → `[[1,1,6],[1,2,5],[1,7],[2,6]]`.""",
"""This is Combination Sum + Subsets II combined.

- Each element used once → recurse with `i + 1`.
- Duplicates in input → sort and skip `c[i] == c[i-1]` when `i > start` so that the same value isn't tried twice at one level.
- Prune with `break` when `c[i] > remain` (sorted).""",
r"""
import java.util.*;

class Solution {
    public List<List<Integer>> combinationSum2(int[] candidates, int target) {
        Arrays.sort(candidates);
        List<List<Integer>> res = new ArrayList<>();
        backtrack(candidates, 0, target, new ArrayList<>(), res);
        return res;
    }

    private void backtrack(int[] c, int start, int remain, List<Integer> path, List<List<Integer>> res) {
        if (remain == 0) {
            res.add(new ArrayList<>(path));
            return;
        }
        for (int i = start; i < c.length; i++) {
            if (i > start && c[i] == c[i - 1]) continue;
            if (c[i] > remain) break;
            path.add(c[i]);
            backtrack(c, i + 1, remain - c[i], path, res);
            path.remove(path.size() - 1);
        }
    }
}
""", "O(2^n)", "O(n)", False),

P("letter-combinations-of-a-phone-number", "Letter Combinations of a Phone Number", "Medium", ["Amazon", "Google", "Uber", "Microsoft", "Swiggy"],
"""Given a string of digits 2–9, return all letter strings it could represent on an old phone keypad (2 = abc, 3 = def, ...). For `"23"` → `["ad","ae","af","bd","be","bf","cd","ce","cf"]`. Empty input returns an empty list.""",
"""**Intuition:** the recursion depth equals the number of digits; at depth `i` you branch over the 3–4 letters mapped to `digits[i]`. Use a `StringBuilder` and delete the last char after recursing.

**Edge case:** empty input must return `[]`, not `[""]`.

Total outputs are up to 4^n, each of length n.""",
r"""
import java.util.*;

class Solution {
    private static final String[] MAP = {"", "", "abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"};

    public List<String> letterCombinations(String digits) {
        List<String> res = new ArrayList<>();
        if (digits == null || digits.isEmpty()) return res;
        backtrack(digits, 0, new StringBuilder(), res);
        return res;
    }

    private void backtrack(String digits, int idx, StringBuilder sb, List<String> res) {
        if (idx == digits.length()) {
            res.add(sb.toString());
            return;
        }
        for (char ch : MAP[digits.charAt(idx) - '0'].toCharArray()) {
            sb.append(ch);
            backtrack(digits, idx + 1, sb, res);
            sb.deleteCharAt(sb.length() - 1);
        }
    }
}
""", "O(n · 4^n)", "O(n)", False),

P("palindrome-partitioning", "Palindrome Partitioning", "Medium", ["Amazon", "Google", "Adobe", "Microsoft"],
"""Split a string into pieces so every piece is a palindrome, and return all such splits. For `"aab"` → `[["a","a","b"],["aa","b"]]`.""",
"""**Intuition:** the choice at each step is *where to cut next*. From index `start`, try every end `i`; if `s[start..i]` is a palindrome, take it and recurse from `i+1`. When `start == n`, the path is a full partition.

**Optimization:** precompute `isPal[i][j]` with DP (`isPal[i][j] = s[i]==s[j] && (j-i<2 || isPal[i+1][j-1]`) so each palindrome check is O(1). The two-pointer check also passes for interview purposes.""",
r"""
import java.util.*;

class Solution {
    public List<List<String>> partition(String s) {
        int n = s.length();
        boolean[][] pal = new boolean[n][n];
        for (int i = n - 1; i >= 0; i--) {
            for (int j = i; j < n; j++) {
                pal[i][j] = s.charAt(i) == s.charAt(j) && (j - i < 2 || pal[i + 1][j - 1]);
            }
        }
        List<List<String>> res = new ArrayList<>();
        backtrack(s, 0, pal, new ArrayList<>(), res);
        return res;
    }

    private void backtrack(String s, int start, boolean[][] pal, List<String> path, List<List<String>> res) {
        if (start == s.length()) {
            res.add(new ArrayList<>(path));
            return;
        }
        for (int end = start; end < s.length(); end++) {
            if (!pal[start][end]) continue;
            path.add(s.substring(start, end + 1));
            backtrack(s, end + 1, pal, path, res);
            path.remove(path.size() - 1);
        }
    }
}
""", "O(n · 2^n)", "O(n^2)", True),

P("word-search", "Word Search", "Medium", ["Amazon", "Microsoft", "Uber", "Atlassian", "Flipkart", "PhonePe"],
"""Given a grid of letters and a word, decide whether the word can be traced through horizontally/vertically adjacent cells without reusing a cell. Grid `[["A","B"],["C","D"]]` contains `"ABD"` but not `"ABCD"` (C isn't adjacent to B).""",
"""**Intuition:** try every cell as a starting point and run DFS that matches `word[k]` at step k. Mark the current cell as visited (e.g. overwrite it with `'#'`) before exploring its 4 neighbors, and restore it afterwards — that's the backtracking step.

**Prune:** return false immediately on out-of-bounds or character mismatch. Return true as soon as `k == word.length()`.

Optional speedups: if the word has more of some letter than the board, return false; or reverse the word if its last char is rarer than its first.""",
r"""
class Solution {
    public boolean exist(char[][] board, String word) {
        for (int r = 0; r < board.length; r++) {
            for (int c = 0; c < board[0].length; c++) {
                if (dfs(board, word, r, c, 0)) return true;
            }
        }
        return false;
    }

    private boolean dfs(char[][] b, String word, int r, int c, int k) {
        if (k == word.length()) return true;
        if (r < 0 || c < 0 || r >= b.length || c >= b[0].length || b[r][c] != word.charAt(k)) return false;
        char saved = b[r][c];
        b[r][c] = '#'; // mark visited
        boolean found = dfs(b, word, r + 1, c, k + 1) || dfs(b, word, r - 1, c, k + 1)
                     || dfs(b, word, r, c + 1, k + 1) || dfs(b, word, r, c - 1, k + 1);
        b[r][c] = saved; // backtrack
        return found;
    }
}
""", "O(m · n · 3^L)", "O(L) recursion", True),

P("n-queens", "N-Queens", "Hard", ["Amazon", "Microsoft", "Google", "Adobe", "Goldman Sachs"],
"""Place n queens on an n×n board so that no two attack each other (same row, column or diagonal) and return every valid board as a list of strings using `'Q'` and `'.'`. For n = 4 there are 2 solutions.""",
"""**Intuition:** each row gets exactly one queen, so recurse row by row and choose a column. A placement is safe if its column, its main diagonal (`r - c`) and anti-diagonal (`r + c`) are all free.

**Key insight:** keep three boolean arrays — `cols[n]`, `diag1[2n]` indexed by `r - c + n`, `diag2[2n]` indexed by `r + c` — giving O(1) safety checks instead of scanning the board.

When `row == n`, convert the board to strings and record it. Undo all three marks on return.""",
r"""
import java.util.*;

class Solution {
    public List<List<String>> solveNQueens(int n) {
        List<List<String>> res = new ArrayList<>();
        char[][] board = new char[n][n];
        for (char[] row : board) Arrays.fill(row, '.');
        place(0, n, board, new boolean[n], new boolean[2 * n], new boolean[2 * n], res);
        return res;
    }

    private void place(int r, int n, char[][] board, boolean[] cols, boolean[] d1, boolean[] d2,
                       List<List<String>> res) {
        if (r == n) {
            List<String> snapshot = new ArrayList<>();
            for (char[] row : board) snapshot.add(new String(row));
            res.add(snapshot);
            return;
        }
        for (int c = 0; c < n; c++) {
            if (cols[c] || d1[r - c + n] || d2[r + c]) continue;
            cols[c] = d1[r - c + n] = d2[r + c] = true;
            board[r][c] = 'Q';
            place(r + 1, n, board, cols, d1, d2, res);
            board[r][c] = '.';
            cols[c] = d1[r - c + n] = d2[r + c] = false;
        }
    }
}
""", "O(n!)", "O(n^2)", True),
]

PATTERN = {"id": "backtracking", "name": "Backtracking", "order": 10, "intro": INTRO.strip(), "problems": PROBLEMS}
