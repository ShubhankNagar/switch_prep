from dsa1_common import P, PAT

TP_INTRO = r'''
**Two Pointers** uses two indices that move through a sequence in a coordinated way, replacing a nested loop with a single linear pass.

**Two flavours**
1. **Opposite ends** (`l = 0`, `r = n - 1`, move inward) - works when the array is **sorted** or when the answer depends on both ends (pair sums, palindromes, container area, trapping water).
2. **Same direction / fast-slow** (`read` and `write` pointers) - in-place compaction: remove duplicates, move zeroes, partitioning.

**How to recognize it**
- Input is sorted (or you can sort it) and you look for pairs/triplets with a target sum.
- "In place" with O(1) extra space.
- Comparing characters from both ends (palindromes).

**Template - opposite ends on a sorted array**
```java
int l = 0, r = nums.length - 1;
while (l < r) {
    int sum = nums[l] + nums[r];
    if (sum == target) { /* record */ l++; r--; }
    else if (sum < target) l++;   // need a bigger sum
    else r--;                     // need a smaller sum
}
```

**Template - read/write compaction**
```java
int write = 0;
for (int read = 0; read < nums.length; read++) {
    if (keep(nums[read])) nums[write++] = nums[read];
}
// first `write` elements are the answer
```

**Why it works:** in a sorted array, if `nums[l] + nums[r]` is too small, no pair using `nums[l]` with any index `<= r` can reach the target, so `l` can be safely discarded. Every move eliminates a whole row/column of the brute-force search space.

**Pitfalls**
- Skipping duplicates in 3Sum/4Sum (both for the fixed element and after finding a match).
- Overflow in 4Sum - use `long` for the sum.
- Forgetting to sort first (sorting costs O(n log n), and destroys original indices - Two Sum on unsorted input needs a HashMap instead).
'''

tp = [
P("valid-palindrome", "Valid Palindrome", "Easy", "Facebook, Microsoft, Amazon, Apple, Wayfair",
"After lowercasing and removing every non-alphanumeric character, decide whether the string reads the same forwards and backwards. Example: \"A man, a plan, a canal: Panama\" -> true; \"race a car\" -> false.",
r'''
**Naive:** build a cleaned string and compare with its reverse - O(n) extra space.

**Two pointers:** `l` at start, `r` at end. Skip characters that are not letters/digits (`Character.isLetterOrDigit`). Compare `Character.toLowerCase` of both; mismatch -> false. Move inward. O(n) time, O(1) space.
''',
r'''
class Solution {
    public boolean isPalindrome(String s) {
        int l = 0, r = s.length() - 1;
        while (l < r) {
            while (l < r && !Character.isLetterOrDigit(s.charAt(l))) l++;
            while (l < r && !Character.isLetterOrDigit(s.charAt(r))) r--;
            if (Character.toLowerCase(s.charAt(l)) != Character.toLowerCase(s.charAt(r))) {
                return false;
            }
            l++;
            r--;
        }
        return true;
    }
}
''', "O(n)", "O(1)"),

P("two-sum-ii-input-array-is-sorted", "Two Sum II - Input Array Is Sorted", "Medium", "Amazon, Google, Adobe, Microsoft",
"Given a 1-indexed sorted array, return the 1-based indices of the two numbers that add up to target using only O(1) extra space. Example: [2,7,11,15], target 9 -> [1,2].",
r'''
The HashMap solution works but uses O(n) space. Because the array is **sorted**, use opposite-end pointers: if the sum is too small, move `l` right to increase it; if too big, move `r` left. Each step discards one candidate permanently, so it is O(n) with O(1) space.

Remember to return 1-based indices.
''',
r'''
class Solution {
    public int[] twoSum(int[] numbers, int target) {
        int l = 0, r = numbers.length - 1;
        while (l < r) {
            int sum = numbers[l] + numbers[r];
            if (sum == target) return new int[]{l + 1, r + 1};
            if (sum < target) l++;
            else r--;
        }
        return new int[0];
    }
}
''', "O(n)", "O(1)"),

P("3sum", "3Sum", "Medium", "Facebook, Amazon, Microsoft, Google, Apple, Adobe, Flipkart",
"Find all unique triplets in the array whose sum is zero; the result must not contain duplicate triplets. Example: [-1,0,1,2,-1,-4] -> [[-1,-1,2],[-1,0,1]].",
r'''
**Brute force:** three loops plus a set to dedupe, O(n³).

**Optimal:** sort, then fix the first element `nums[i]` and run Two Sum II (two pointers) on the rest for target `-nums[i]`. O(n²).

**Deduplication (the real test):**
- Skip `i` if `nums[i] == nums[i-1]`.
- After a match, move both pointers and skip equal neighbours.
- Early exit when `nums[i] > 0` (sorted, so no zero sum possible).
''',
r'''
class Solution {
    public List<List<Integer>> threeSum(int[] nums) {
        Arrays.sort(nums);
        List<List<Integer>> res = new ArrayList<>();
        for (int i = 0; i < nums.length - 2; i++) {
            if (nums[i] > 0) break;
            if (i > 0 && nums[i] == nums[i - 1]) continue;
            int l = i + 1, r = nums.length - 1;
            while (l < r) {
                int sum = nums[i] + nums[l] + nums[r];
                if (sum == 0) {
                    res.add(Arrays.asList(nums[i], nums[l], nums[r]));
                    l++;
                    r--;
                    while (l < r && nums[l] == nums[l - 1]) l++;
                    while (l < r && nums[r] == nums[r + 1]) r--;
                } else if (sum < 0) {
                    l++;
                } else {
                    r--;
                }
            }
        }
        return res;
    }
}
''', "O(n^2)", "O(1) extra (ignoring sort/output)", True),

P("4sum", "4Sum", "Medium", "Amazon, Google, Adobe, Microsoft",
"Return all unique quadruplets [a,b,c,d] of distinct indices whose values sum to target. Example: [1,0,-1,0,-2,2], target 0 -> [[-2,-1,1,2],[-2,0,0,2],[-1,0,0,1]].",
r'''
Generalize 3Sum: sort, fix two elements with nested loops (`i`, `j`), and two-pointer the remaining range for `target - nums[i] - nums[j]`. O(n³).

Apply the same duplicate skipping at **every** level (`i`, `j`, and after each match). Values go up to 10^9, so compute the sum as `long` to avoid overflow - a classic hidden test case.
''',
r'''
class Solution {
    public List<List<Integer>> fourSum(int[] nums, int target) {
        Arrays.sort(nums);
        List<List<Integer>> res = new ArrayList<>();
        int n = nums.length;
        for (int i = 0; i < n - 3; i++) {
            if (i > 0 && nums[i] == nums[i - 1]) continue;
            for (int j = i + 1; j < n - 2; j++) {
                if (j > i + 1 && nums[j] == nums[j - 1]) continue;
                int l = j + 1, r = n - 1;
                while (l < r) {
                    long sum = (long) nums[i] + nums[j] + nums[l] + nums[r];
                    if (sum == target) {
                        res.add(Arrays.asList(nums[i], nums[j], nums[l], nums[r]));
                        l++;
                        r--;
                        while (l < r && nums[l] == nums[l - 1]) l++;
                        while (l < r && nums[r] == nums[r + 1]) r--;
                    } else if (sum < target) {
                        l++;
                    } else {
                        r--;
                    }
                }
            }
        }
        return res;
    }
}
''', "O(n^3)", "O(1) extra"),

P("container-with-most-water", "Container With Most Water", "Medium", "Amazon, Google, Microsoft, Adobe, Goldman Sachs",
"height[i] is the height of a vertical line at x = i. Choose two lines that, together with the x-axis, hold the most water and return that area. Example: [1,8,6,2,5,4,8,3,7] -> 49.",
r'''
**Brute force:** every pair, O(n²).

**Two pointers:** start with the widest container (`l = 0`, `r = n-1`). Area = `min(h[l], h[r]) * (r - l)`. Now move the pointer at the **shorter** line inward. Why? The area is capped by the shorter line; moving the taller one can only shrink width without raising that cap, so it can never help. Moving the shorter one is the only chance to improve. O(n).
''',
r'''
class Solution {
    public int maxArea(int[] height) {
        int l = 0, r = height.length - 1, best = 0;
        while (l < r) {
            int area = Math.min(height[l], height[r]) * (r - l);
            best = Math.max(best, area);
            if (height[l] < height[r]) l++;
            else r--;
        }
        return best;
    }
}
''', "O(n)", "O(1)", True),

P("trapping-rain-water", "Trapping Rain Water", "Hard", "Amazon, Google, Goldman Sachs, Microsoft, Flipkart, Uber, Adobe",
"Given bar heights of width 1, compute how much rain water is trapped between the bars. Example: [0,1,0,2,1,0,1,3,2,1,2,1] -> 6.",
r'''
Water above bar `i` = `min(maxLeft[i], maxRight[i]) - height[i]`.

**Approach 1:** precompute `maxLeft` and `maxRight` arrays, O(n) space.

**Optimal two pointers:** keep `leftMax` and `rightMax`. If `height[l] < height[r]`, the left side is the bottleneck: the right side has something at least as tall, so water at `l` depends only on `leftMax`. Add `leftMax - height[l]` and move `l`. Symmetric for the right. O(n) time, O(1) space.

(A monotonic stack solution also exists - it computes water layer by layer.)
''',
r'''
class Solution {
    public int trap(int[] height) {
        int l = 0, r = height.length - 1;
        int leftMax = 0, rightMax = 0, water = 0;
        while (l < r) {
            if (height[l] < height[r]) {
                leftMax = Math.max(leftMax, height[l]);
                water += leftMax - height[l];
                l++;
            } else {
                rightMax = Math.max(rightMax, height[r]);
                water += rightMax - height[r];
                r--;
            }
        }
        return water;
    }
}
''', "O(n)", "O(1)", True),

P("remove-duplicates-from-sorted-array", "Remove Duplicates from Sorted Array", "Easy", "Microsoft, Amazon, Facebook, Adobe",
"Remove duplicates in place from a sorted array so each value appears once, keeping relative order, and return the count k of unique values (the first k slots must hold them). Example: [0,0,1,1,1,2,2,3,3,4] -> 5, array starts [0,1,2,3,4].",
r'''
Classic read/write pointers. `write` marks where the next unique value goes. Because the array is sorted, a value is new exactly when it differs from the last written one (`nums[write - 1]`). Copy it and advance `write`. Return `write`. O(n) time, O(1) space.

Variation (LC 80, allow at most two copies): compare against `nums[write - 2]` instead.
''',
r'''
class Solution {
    public int removeDuplicates(int[] nums) {
        int write = 1;
        for (int read = 1; read < nums.length; read++) {
            if (nums[read] != nums[write - 1]) {
                nums[write++] = nums[read];
            }
        }
        return write;
    }
}
''', "O(n)", "O(1)"),

P("move-zeroes", "Move Zeroes", "Easy", "Facebook, Amazon, Microsoft, Apple, Paytm",
"Move all zeros to the end of the array in place while keeping the order of non-zero elements. Example: [0,1,0,3,12] -> [1,3,12,0,0].",
r'''
Read/write pointers again. Walk with `read`; whenever `nums[read] != 0`, swap it into position `write` and advance `write`. Swapping (instead of overwrite + zero-fill) does it in one pass and minimizes writes. Non-zeros keep their order because `write <= read` always.
''',
r'''
class Solution {
    public void moveZeroes(int[] nums) {
        int write = 0;
        for (int read = 0; read < nums.length; read++) {
            if (nums[read] != 0) {
                int t = nums[write];
                nums[write] = nums[read];
                nums[read] = t;
                write++;
            }
        }
    }
}
''', "O(n)", "O(1)"),
]

SW_INTRO = r'''
**Sliding Window** maintains a contiguous range `[left, right]` over an array or string and slides it forward, updating a running state (sum, counts, distinct chars) in O(1) per step instead of recomputing each subarray.

**How to recognize it**
- "Longest / shortest / count of **contiguous** subarray or substring such that ..."
- The constraint is **monotonic**: if a window is invalid, growing it keeps it invalid (or shrinking keeps it valid). Typically: all positive numbers, "at most K distinct", "at most K replacements", "contains all chars of T".
- Fixed size `k` windows (max of each window, anagram of length k).

**Variable-size template (longest valid window)**
```java
int left = 0, best = 0;
int[] count = new int[128];          // window state
for (int right = 0; right < s.length(); right++) {
    count[s.charAt(right)]++;        // 1. expand: add s[right]
    while (windowInvalid()) {        // 2. shrink until valid again
        count[s.charAt(left)]--;
        left++;
    }
    best = Math.max(best, right - left + 1); // 3. record answer
}
```
For **shortest** valid window, record the answer *inside* the while loop (while it is still valid) and then shrink.

**Fixed-size template**
```java
for (int right = 0; right < n; right++) {
    add(nums[right]);
    if (right >= k) remove(nums[right - k]);
    if (right >= k - 1) record();
}
```

**Pitfalls**
- Sliding window fails with **negative numbers** for sum targets - use prefix sums + HashMap.
- Off-by-one: window length is `right - left + 1`.
- For "exactly K" problems use `atMost(K) - atMost(K - 1)`.
- Each element enters and leaves the window once, so total time is O(n) even with the inner `while`.
'''

sw = [
P("longest-substring-without-repeating-characters", "Longest Substring Without Repeating Characters", "Medium", "Amazon, Google, Microsoft, Bloomberg, Adobe, Flipkart, Paytm",
"Return the length of the longest substring that contains no repeated character. Example: \"abcabcbb\" -> 3 (\"abc\"); \"pwwkew\" -> 3 (\"wke\").",
r'''
**Brute force:** check every substring for uniqueness, O(n³) or O(n²).

**Sliding window:** expand `right`; if `s[right]` already appears inside the window, jump `left` to one past its last occurrence. Store each char's last index in an `int[128]` so the jump is O(1). Use `max(left, last+1)` semantics (here via the `>= left` check) so `left` never moves backward.

**Key insight:** the window always holds a valid answer candidate; record its length each step.
''',
r'''
class Solution {
    public int lengthOfLongestSubstring(String s) {
        int[] last = new int[128];
        Arrays.fill(last, -1);
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            if (last[c] >= left) left = last[c] + 1;
            last[c] = right;
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
''', "O(n)", "O(1) (128-size array)", True),

P("longest-repeating-character-replacement", "Longest Repeating Character Replacement", "Medium", "Google, Amazon, Microsoft, Uber",
"You may change at most k characters of an uppercase string to any letter. Return the length of the longest substring that can be made of one repeated letter. Example: s = \"AABABBA\", k = 1 -> 4.",
r'''
A window is valid if `windowLength - maxFreq <= k` (replace everything except the most frequent letter).

Expand `right`, update the count and `maxFreq`. While invalid, shrink from the left. Record the window length.

**Subtle trick:** we never need to decrease `maxFreq` when shrinking. A stale (too-large) `maxFreq` only keeps the window from shrinking, and the answer can only improve when a genuinely larger `maxFreq` appears. Still O(n).
''',
r'''
class Solution {
    public int characterReplacement(String s, int k) {
        int[] count = new int[26];
        int left = 0, maxFreq = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            maxFreq = Math.max(maxFreq, ++count[s.charAt(right) - 'A']);
            while (right - left + 1 - maxFreq > k) {
                count[s.charAt(left) - 'A']--;
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
''', "O(n)", "O(1)", True),

P("permutation-in-string", "Permutation in String", "Medium", "Microsoft, Amazon, Facebook, Oracle",
"Return true if some permutation of s1 appears as a contiguous substring of s2. Example: s1 = \"ab\", s2 = \"eidbaooo\" -> true (\"ba\").",
r'''
A permutation of `s1` is any window of length `|s1|` with the **same character counts**. Use a **fixed-size window** over `s2`: maintain counts for the current window, add the incoming char, remove the char that falls out, and compare with `s1`'s counts.

Comparing two `int[26]` arrays is O(26), so total O(26·n). (An optimization keeps a `matches` counter of equal slots to make each step O(1).)
''',
r'''
class Solution {
    public boolean checkInclusion(String s1, String s2) {
        int k = s1.length();
        if (k > s2.length()) return false;
        int[] need = new int[26], window = new int[26];
        for (char c : s1.toCharArray()) need[c - 'a']++;
        for (int right = 0; right < s2.length(); right++) {
            window[s2.charAt(right) - 'a']++;
            if (right >= k) window[s2.charAt(right - k) - 'a']--;
            if (right >= k - 1 && Arrays.equals(need, window)) return true;
        }
        return false;
    }
}
''', "O(26 * n)", "O(1)"),

P("minimum-window-substring", "Minimum Window Substring", "Hard", "Facebook, Amazon, Google, Microsoft, LinkedIn, Uber, Atlassian",
"Return the shortest substring of s that contains every character of t (including duplicates); return \"\" if none exists. Example: s = \"ADOBECODEBANC\", t = \"ABC\" -> \"BANC\".",
r'''
Keep `need[c]` = how many more of `c` the window still requires, and `missing` = total characters still required.

- **Expand** `right`: if `need[c] > 0`, this char was useful, so `missing--`. Then `need[c]--` (may go negative = surplus).
- **While `missing == 0`** the window is valid: record it if smaller, then remove `s[left]`: `need[d]++`; if it becomes positive we lost a needed char, so `missing++`. Advance `left`.

Each index enters/leaves once: O(|s| + |t|).
''',
r'''
class Solution {
    public String minWindow(String s, String t) {
        int[] need = new int[128];
        for (char c : t.toCharArray()) need[c]++;
        int missing = t.length();
        int left = 0, bestStart = 0, bestLen = Integer.MAX_VALUE;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            if (need[c] > 0) missing--;
            need[c]--;
            while (missing == 0) {
                if (right - left + 1 < bestLen) {
                    bestLen = right - left + 1;
                    bestStart = left;
                }
                char d = s.charAt(left++);
                need[d]++;
                if (need[d] > 0) missing++;
            }
        }
        return bestLen == Integer.MAX_VALUE ? "" : s.substring(bestStart, bestStart + bestLen);
    }
}
''', "O(|s| + |t|)", "O(1)", True),

P("sliding-window-maximum", "Sliding Window Maximum", "Hard", "Amazon, Google, Microsoft, Uber, Flipkart, Zomato",
"For a window of size k sliding one step at a time from left to right, return the maximum of each window. Example: nums = [1,3,-1,-3,5,3,6,7], k = 3 -> [3,3,5,5,6,7].",
r'''
**Brute force:** scan each window, O(nk). **Heap:** O(n log n) with lazy deletion.

**Optimal - monotonic deque:** store **indices** with values in decreasing order.
- Pop from the front if that index has left the window (`<= i - k`).
- Pop from the back while the back value `<= nums[i]` - those can never be a max again (a newer, bigger element dominates them).
- Push `i`. Front of deque is the window max.

Each index is pushed/popped once: O(n).
''',
r'''
class Solution {
    public int[] maxSlidingWindow(int[] nums, int k) {
        int n = nums.length;
        int[] res = new int[n - k + 1];
        Deque<Integer> dq = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            if (!dq.isEmpty() && dq.peekFirst() <= i - k) dq.pollFirst();
            while (!dq.isEmpty() && nums[dq.peekLast()] <= nums[i]) dq.pollLast();
            dq.offerLast(i);
            if (i >= k - 1) res[i - k + 1] = nums[dq.peekFirst()];
        }
        return res;
    }
}
''', "O(n)", "O(k)", True),

P("max-consecutive-ones-iii", "Max Consecutive Ones III", "Medium", "Facebook, Amazon, Google, Microsoft",
"In a binary array you may flip at most k zeros to ones. Return the length of the longest run of ones you can obtain. Example: [1,1,1,0,0,0,1,1,1,1,0], k = 2 -> 6.",
r'''
Reframe: find the longest window containing **at most k zeros**. Expand `right`, counting zeros. While zeros exceed `k`, move `left` forward (decrementing the zero count when a zero leaves). The window length is a candidate answer. O(n), O(1).

This "longest window with at most K bad elements" shape appears constantly - memorize it.
''',
r'''
class Solution {
    public int longestOnes(int[] nums, int k) {
        int left = 0, zeros = 0, best = 0;
        for (int right = 0; right < nums.length; right++) {
            if (nums[right] == 0) zeros++;
            while (zeros > k) {
                if (nums[left] == 0) zeros--;
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
''', "O(n)", "O(1)"),

P("fruit-into-baskets", "Fruit Into Baskets", "Medium", "Google, Amazon, Microsoft",
"Trees in a row produce fruit types fruits[i]. With two baskets that each hold a single type, you pick one fruit from every tree starting at some tree and moving right, stopping when a third type appears. Return the maximum fruits collected. Example: [1,2,3,2,2] -> 4.",
r'''
Strip the story: find the **longest subarray with at most 2 distinct values**.

Sliding window with a `HashMap<type, count>`. Add `fruits[right]`; while the map has more than 2 keys, decrement `fruits[left]` (removing the key when its count hits 0) and advance `left`. Track the max window. O(n).

Generalizes to "at most K distinct" (LC 340).
''',
r'''
class Solution {
    public int totalFruit(int[] fruits) {
        Map<Integer, Integer> count = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < fruits.length; right++) {
            count.merge(fruits[right], 1, Integer::sum);
            while (count.size() > 2) {
                int f = fruits[left++];
                if (count.merge(f, -1, Integer::sum) == 0) count.remove(f);
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
''', "O(n)", "O(1) (at most 3 keys)"),

P("minimum-size-subarray-sum", "Minimum Size Subarray Sum", "Medium", "Amazon, Facebook, Google, Goldman Sachs",
"Given positive integers and a target, return the minimal length of a contiguous subarray whose sum is at least target, or 0 if none exists. Example: target = 7, [2,3,1,2,4,3] -> 2 ([4,3]).",
r'''
All numbers are **positive**, so adding grows the sum and removing shrinks it - perfect for a variable window. Expand `right` adding to `sum`. While `sum >= target`, record `right - left + 1` and shrink from the left. This is the "shortest valid window" form: record inside the loop.

O(n). (An O(n log n) prefix sum + binary search alternative exists as a follow-up.)
''',
r'''
class Solution {
    public int minSubArrayLen(int target, int[] nums) {
        int left = 0, sum = 0, best = Integer.MAX_VALUE;
        for (int right = 0; right < nums.length; right++) {
            sum += nums[right];
            while (sum >= target) {
                best = Math.min(best, right - left + 1);
                sum -= nums[left++];
            }
        }
        return best == Integer.MAX_VALUE ? 0 : best;
    }
}
''', "O(n)", "O(1)"),
]

ST_INTRO = r'''
**Stack** problems involve matching or "most recent unresolved item" logic (LIFO). A **monotonic stack** is a stack kept in increasing or decreasing order; it answers "next greater / next smaller element" questions for every index in O(n) total.

**How to recognize it**
- Matching pairs: brackets, tags, undo operations, expression evaluation.
- "For each element find the next/previous greater/smaller element" (daily temperatures, stock span).
- "Largest rectangle", "how far can I see", "collisions" - things resolved when a bigger/smaller element arrives.
- Design problems needing O(1) extras (min stack).

**Java tip:** use `Deque<Integer> st = new ArrayDeque<>()` with `push/pop/peek`. Avoid the legacy `Stack` class (synchronized, slower).

**Monotonic stack template - next greater element to the right**
```java
int[] next = new int[n];
Arrays.fill(next, -1);
Deque<Integer> st = new ArrayDeque<>();  // holds indices, values decreasing
for (int i = 0; i < n; i++) {
    while (!st.isEmpty() && nums[st.peek()] < nums[i]) {
        next[st.pop()] = nums[i];        // i is the answer for the popped index
    }
    st.push(i);
}
```
Variants: change `<` to `>` for next smaller; iterate right-to-left for "previous"; use `<=`/`>=` carefully when duplicates exist.

**Why it's O(n):** every index is pushed once and popped at most once.

**Pitfalls**
- Store **indices**, not values, when you need distances or widths.
- Remember to process what is left in the stack at the end (often by appending a sentinel like height 0).
- In circular arrays, iterate `2n` times using `i % n`.
- Operand order in expression evaluation: pop `b` first, then `a`, compute `a op b`.
'''

st = [
P("valid-parentheses", "Valid Parentheses", "Easy", "Amazon, Google, Microsoft, Facebook, Flipkart, Paytm, Oracle",
"A string contains only ()[]{}; decide whether every opening bracket is closed by the same type in the correct order. Example: \"()[]{}\" -> true; \"(]\" -> false; \"([)]\" -> false.",
r'''
Push each opening bracket. For a closing bracket the stack top must be the matching opener; otherwise invalid. At the end the stack must be empty.

**Neat trick:** push the *expected closing* bracket instead of the opener. Then a closing char just has to equal `pop()`. O(n) time and space. Odd length can return false immediately.
''',
r'''
class Solution {
    public boolean isValid(String s) {
        Deque<Character> st = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            if (c == '(') st.push(')');
            else if (c == '[') st.push(']');
            else if (c == '{') st.push('}');
            else if (st.isEmpty() || st.pop() != c) return false;
        }
        return st.isEmpty();
    }
}
''', "O(n)", "O(n)", True),

P("min-stack", "Min Stack", "Medium", "Amazon, Microsoft, Google, Bloomberg, Goldman Sachs, Walmart",
"Design a stack supporting push, pop, top and getMin, all in O(1) time. Example: push(-2), push(0), push(-3), getMin() -> -3, pop(), top() -> 0, getMin() -> -2.",
r'''
The minimum changes as elements are pushed/popped, so store it **alongside each element**: every stack entry is a pair `(value, minAtThisPoint)`. Push computes `min(val, currentMin)`. Pop removes both together, automatically restoring the previous min.

Alternative: a second stack that only pushes when a new value `<=` current min. Both are O(1) per operation.
''',
r'''
class MinStack {
    private final Deque<int[]> st = new ArrayDeque<>(); // {value, minSoFar}

    public MinStack() { }

    public void push(int val) {
        int min = st.isEmpty() ? val : Math.min(val, st.peek()[1]);
        st.push(new int[]{val, min});
    }

    public void pop() {
        st.pop();
    }

    public int top() {
        return st.peek()[0];
    }

    public int getMin() {
        return st.peek()[1];
    }
}
''', "O(1) per op", "O(n)", True),

P("evaluate-reverse-polish-notation", "Evaluate Reverse Polish Notation", "Medium", "Amazon, LinkedIn, Google, Microsoft",
"Evaluate an arithmetic expression given in postfix (Reverse Polish) notation with + - * / on integers; division truncates toward zero. Example: [\"2\",\"1\",\"+\",\"3\",\"*\"] -> 9.",
r'''
Postfix is designed for a stack: numbers are pushed; an operator pops the top two operands, applies itself, and pushes the result.

**Order matters:** the first pop is the *right* operand `b`, the second is the *left* operand `a` -> compute `a - b`, `a / b`. Java integer division already truncates toward zero. Use a `switch` for readability.
''',
r'''
class Solution {
    public int evalRPN(String[] tokens) {
        Deque<Integer> st = new ArrayDeque<>();
        for (String t : tokens) {
            switch (t) {
                case "+" -> st.push(st.pop() + st.pop());
                case "*" -> st.push(st.pop() * st.pop());
                case "-" -> { int b = st.pop(), a = st.pop(); st.push(a - b); }
                case "/" -> { int b = st.pop(), a = st.pop(); st.push(a / b); }
                default -> st.push(Integer.parseInt(t));
            }
        }
        return st.pop();
    }
}
''', "O(n)", "O(n)"),

P("daily-temperatures", "Daily Temperatures", "Medium", "Amazon, Google, Facebook, Uber, Flipkart",
"For each day, return how many days you must wait until a strictly warmer temperature, or 0 if it never comes. Example: [73,74,75,71,69,72,76,73] -> [1,1,4,2,1,1,0,0].",
r'''
**Brute force:** for each day scan forward, O(n²).

**Monotonic decreasing stack of indices:** days still waiting for a warmer day. When today's temperature beats the stack top, that earlier day has found its answer: `ans[j] = i - j`. Keep popping while it beats; then push today. Anything left at the end stays 0. O(n).

This is the canonical "next greater element" template.
''',
r'''
class Solution {
    public int[] dailyTemperatures(int[] temperatures) {
        int n = temperatures.length;
        int[] ans = new int[n];
        Deque<Integer> st = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            while (!st.isEmpty() && temperatures[st.peek()] < temperatures[i]) {
                int j = st.pop();
                ans[j] = i - j;
            }
            st.push(i);
        }
        return ans;
    }
}
''', "O(n)", "O(n)", True),

P("next-greater-element-i", "Next Greater Element I", "Easy", "Amazon, Bloomberg, Microsoft, Adobe",
"nums1 is a subset of nums2 (distinct values). For each x in nums1, find the first element to the right of x in nums2 that is greater than x, or -1. Example: nums1 = [4,1,2], nums2 = [1,3,4,2] -> [-1,3,-1].",
r'''
Precompute the next greater element for **every** value of `nums2` using a monotonic stack, storing results in a `HashMap<value, nextGreater>`. Then answer each query from `nums1` by lookup (default -1).

O(n + m) instead of O(n·m). Follow-ups: Next Greater Element II (circular - loop `2n` times with `i % n`).
''',
r'''
class Solution {
    public int[] nextGreaterElement(int[] nums1, int[] nums2) {
        Map<Integer, Integer> next = new HashMap<>();
        Deque<Integer> st = new ArrayDeque<>();
        for (int x : nums2) {
            while (!st.isEmpty() && st.peek() < x) next.put(st.pop(), x);
            st.push(x);
        }
        int[] res = new int[nums1.length];
        for (int i = 0; i < nums1.length; i++) {
            res[i] = next.getOrDefault(nums1[i], -1);
        }
        return res;
    }
}
''', "O(n + m)", "O(n)"),

P("largest-rectangle-in-histogram", "Largest Rectangle in Histogram", "Hard", "Amazon, Google, Microsoft, Uber, Flipkart, Goldman Sachs",
"Given histogram bar heights (each width 1), return the area of the largest rectangle that fits inside the histogram. Example: [2,1,5,6,2,3] -> 10 (bars 5 and 6, width 2).",
r'''
For each bar, the largest rectangle using it as the **shortest** bar extends left and right until a smaller bar. So we need previous-smaller and next-smaller indices.

**One-pass monotonic increasing stack:** when bar `i` is lower than the stack top, the top has found its *next smaller* (`i`), and its *previous smaller* is the element beneath it in the stack. Width = `i - newTop - 1`. Pop and compute. Append a sentinel height 0 at `i = n` to flush the stack. O(n).
''',
r'''
class Solution {
    public int largestRectangleArea(int[] heights) {
        int n = heights.length, best = 0;
        Deque<Integer> st = new ArrayDeque<>();
        for (int i = 0; i <= n; i++) {
            int h = (i == n) ? 0 : heights[i];
            while (!st.isEmpty() && heights[st.peek()] >= h) {
                int height = heights[st.pop()];
                int leftBoundary = st.isEmpty() ? -1 : st.peek();
                best = Math.max(best, height * (i - leftBoundary - 1));
            }
            st.push(i);
        }
        return best;
    }
}
''', "O(n)", "O(n)", True),

P("car-fleet", "Car Fleet", "Medium", "Google, Amazon, Uber",
"Cars at given positions drive toward a target with given speeds; a faster car that catches a slower one ahead joins it and moves at the slower speed, forming a fleet. Count how many fleets arrive. Example: target 12, position [10,8,0,5,3], speed [2,4,1,1,3] -> 3.",
r'''
Compute each car's arrival time if alone: `(target - pos) / speed`. Process cars **from closest to the target to farthest**. A car behind can't pass; if its time is `<=` the time of the fleet ahead, it merges into that fleet. If it takes longer, it forms a new fleet (and becomes the new blocker).

So sort by position descending and count how many times a strictly larger time appears - a stack in spirit (only the top matters). O(n log n).
''',
r'''
class Solution {
    public int carFleet(int target, int[] position, int[] speed) {
        int n = position.length;
        Integer[] idx = new Integer[n];
        for (int i = 0; i < n; i++) idx[i] = i;
        Arrays.sort(idx, (a, b) -> position[b] - position[a]); // closest to target first
        int fleets = 0;
        double slowest = 0;
        for (int i : idx) {
            double time = (double) (target - position[i]) / speed[i];
            if (time > slowest) {
                fleets++;
                slowest = time;
            }
        }
        return fleets;
    }
}
''', "O(n log n)", "O(n)"),

P("asteroid-collision", "Asteroid Collision", "Medium", "Amazon, Uber, Lyft, Salesforce, Flipkart",
"Asteroids move along a line: the sign is direction (+ right, - left) and absolute value is size. When two meet, the smaller explodes; equal sizes both explode. Return the final state. Example: [5,10,-5] -> [5,10]; [8,-8] -> [].",
r'''
Only a **right-moving** asteroid followed by a **left-moving** one collide. Use a stack of survivors. For each new asteroid `a`:
- While `a < 0` and the top is positive: if top is smaller, pop it and continue; if equal, pop and `a` dies; if larger, `a` dies.
- If `a` survived, push it.

Finally copy the stack bottom-to-top into an array. O(n) since each asteroid is pushed/popped once.
''',
r'''
class Solution {
    public int[] asteroidCollision(int[] asteroids) {
        Deque<Integer> st = new ArrayDeque<>();
        for (int a : asteroids) {
            boolean alive = true;
            while (alive && a < 0 && !st.isEmpty() && st.peek() > 0) {
                if (st.peek() < -a) {
                    st.pop();
                } else if (st.peek() == -a) {
                    st.pop();
                    alive = false;
                } else {
                    alive = false;
                }
            }
            if (alive) st.push(a);
        }
        int[] res = new int[st.size()];
        for (int i = res.length - 1; i >= 0; i--) res[i] = st.pop();
        return res;
    }
}
''', "O(n)", "O(n)"),

P("online-stock-span", "Online Stock Span", "Medium", "Amazon, Microsoft, Adobe, Goldman Sachs",
"Design a class that receives daily stock prices one by one and returns, for each day, the span: the number of consecutive days up to and including today with price <= today's price. Example: prices 100,80,60,70,60,75,85 -> spans 1,1,1,2,1,4,6.",
r'''
This is "previous greater element", but online. Keep a monotonic decreasing stack of `(price, span)` pairs. For a new price, pop every entry with price `<=` today and **add their spans** to today's span (they're all covered). Push `(price, span)`.

Each price is pushed and popped once -> amortized O(1) per call.
''',
r'''
class StockSpanner {
    private final Deque<int[]> st = new ArrayDeque<>(); // {price, span}

    public StockSpanner() { }

    public int next(int price) {
        int span = 1;
        while (!st.isEmpty() && st.peek()[0] <= price) {
            span += st.pop()[1];
        }
        st.push(new int[]{price, span});
        return span;
    }
}
''', "O(1) amortized", "O(n)"),
]

TP = PAT("two-pointers", "Two Pointers", 2, TP_INTRO, tp)
SW = PAT("sliding-window", "Sliding Window", 3, SW_INTRO, sw)
ST = PAT("stack", "Stack & Monotonic Stack", 4, ST_INTRO, st)
