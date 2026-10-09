from dsa1_common import P, PAT

INTRO = r'''
**Arrays & Hashing** is the foundation of almost every interview. The idea: trade a little memory for speed by remembering what you have already seen (in a `HashMap`/`HashSet`, a count array, or a running prefix value) so a brute-force O(n²) scan becomes one O(n) pass.

**How to recognize it**
- "Find a pair / count subarrays / check duplicates" -> HashMap of value -> index or count.
- "Sum of a subarray equals K" -> **prefix sums** + HashMap of prefix -> frequency.
- "Maximum subarray sum" -> **Kadane** (extend the current run or restart).
- "Sort 0/1/2 in place" -> **Dutch National Flag** (three pointers).
- "Element appearing more than n/2 times" -> **Boyer-Moore voting**.
- Matrix questions (rotate, spiral, set zeroes) -> careful index bookkeeping, often using the first row/column as storage.

**Reusable templates**
```java
// 1. Seen-map (pair problems)
Map<Integer, Integer> seen = new HashMap<>();
for (int i = 0; i < nums.length; i++) {
    int need = target - nums[i];
    if (seen.containsKey(need)) { /* found pair (seen.get(need), i) */ }
    seen.put(nums[i], i);
}

// 2. Prefix sum + frequency map (count subarrays with sum k)
Map<Integer, Integer> freq = new HashMap<>();
freq.put(0, 1);
int prefix = 0, count = 0;
for (int x : nums) {
    prefix += x;
    count += freq.getOrDefault(prefix - k, 0);
    freq.merge(prefix, 1, Integer::sum);
}

// 3. Kadane
int cur = 0, best = Integer.MIN_VALUE;
for (int x : nums) { cur = Math.max(x, cur + x); best = Math.max(best, cur); }
```

**Common pitfalls**
- Forgetting `freq.put(0, 1)` in prefix-sum problems (misses subarrays starting at index 0).
- Using a sliding window when the array has negative numbers - it breaks; use prefix sums instead.
- Integer overflow in sums/products - use `long` when values can be large.
- For character problems, an `int[26]` is faster and cleaner than a HashMap.
- Inserting into the map *before* checking (two-sum) can pair an element with itself.
'''

problems = [
P("two-sum", "Two Sum", "Easy", "Amazon, Google, Microsoft, Adobe, Flipkart, Paytm",
"Given an integer array and a target, return the indices of the two numbers that add up to the target (exactly one valid answer exists, and you cannot use the same index twice). Example: nums = [2,7,11,15], target = 9 -> [0,1].",
r'''
**Brute force:** check every pair, O(n²).

**Optimal:** while scanning, ask "have I already seen `target - nums[i]`?" A HashMap from value to index answers that in O(1). Check *before* inserting the current element so an element never pairs with itself. One pass, O(n) time.

**Key insight:** turn a search for a pair into a lookup of the complement.
''',
r'''
class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int need = target - nums[i];
            if (seen.containsKey(need)) {
                return new int[]{seen.get(need), i};
            }
            seen.put(nums[i], i);
        }
        return new int[0];
    }
}
''', "O(n)", "O(n)", True),

P("contains-duplicate", "Contains Duplicate", "Easy", "Amazon, Apple, Adobe, Microsoft",
"Return true if any value occurs at least twice in the array, false if all values are distinct. Example: [1,2,3,1] -> true; [1,2,3,4] -> false.",
r'''
**Brute force:** compare every pair, O(n²). **Better:** sort and check neighbours, O(n log n).

**Optimal:** push elements into a `HashSet`. `Set.add` returns `false` if the element was already present - that is your duplicate. O(n) time, O(n) space.

Mention the trade-off in an interview: sorting uses O(1) extra space but mutates the input and is slower.
''',
r'''
class Solution {
    public boolean containsDuplicate(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int x : nums) {
            if (!seen.add(x)) return true;
        }
        return false;
    }
}
''', "O(n)", "O(n)"),

P("valid-anagram", "Valid Anagram", "Easy", "Amazon, Microsoft, Bloomberg, Uber",
"Given two strings s and t, decide whether t is a rearrangement of the letters of s (same characters with the same counts). Example: s = \"anagram\", t = \"nagaram\" -> true; s = \"rat\", t = \"car\" -> false.",
r'''
**Brute force:** sort both strings and compare, O(n log n).

**Optimal:** lengths must match. Use an `int[26]` counter: increment for each char of `s`, decrement for each char of `t`. If every slot ends at zero, they are anagrams. O(n) time, O(1) space (fixed 26 slots).

**Follow-up (Unicode):** replace the array with a `HashMap<Character, Integer>`.
''',
r'''
class Solution {
    public boolean isAnagram(String s, String t) {
        if (s.length() != t.length()) return false;
        int[] count = new int[26];
        for (int i = 0; i < s.length(); i++) {
            count[s.charAt(i) - 'a']++;
            count[t.charAt(i) - 'a']--;
        }
        for (int c : count) {
            if (c != 0) return false;
        }
        return true;
    }
}
''', "O(n)", "O(1)"),

P("group-anagrams", "Group Anagrams", "Medium", "Amazon, Microsoft, Google, Uber, Goldman Sachs, Salesforce",
"Given a list of strings, group together the words that are anagrams of each other; groups may be returned in any order. Example: [\"eat\",\"tea\",\"tan\",\"ate\",\"nat\",\"bat\"] -> [[\"eat\",\"tea\",\"ate\"],[\"tan\",\"nat\"],[\"bat\"]].",
r'''
**Idea:** anagrams share a *canonical key*. Two choices:
1. Sort each word's characters -> key (O(k log k) per word).
2. Build a 26-letter frequency signature like `"1#0#0#...#"` -> key (O(k) per word).

Put each word into `Map<String, List<String>>` under its key, then return the map values. Using `computeIfAbsent` keeps the code short.

**Key insight:** grouping = hashing by an invariant that all members share.
''',
r'''
class Solution {
    public List<List<String>> groupAnagrams(String[] strs) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String word : strs) {
            int[] count = new int[26];
            for (char c : word.toCharArray()) count[c - 'a']++;
            StringBuilder key = new StringBuilder();
            for (int c : count) key.append(c).append('#');
            groups.computeIfAbsent(key.toString(), k -> new ArrayList<>()).add(word);
        }
        return new ArrayList<>(groups.values());
    }
}
''', "O(n * k)", "O(n * k)", True),

P("top-k-frequent-elements", "Top K Frequent Elements", "Medium", "Amazon, Facebook, Google, Microsoft, Flipkart, Swiggy",
"Return the k values that occur most often in an integer array, in any order (the answer is guaranteed unique). Example: nums = [1,1,1,2,2,3], k = 2 -> [1,2].",
r'''
**Step 1:** count frequencies with a HashMap.

**Option A - heap:** keep a min-heap of size k keyed by frequency, O(n log k).

**Option B - bucket sort (optimal):** a frequency can be at most `n`, so create `n + 1` buckets where `bucket[f]` lists numbers occurring `f` times. Walk buckets from high to low and collect until you have k numbers. O(n) time.

**Key insight:** bounded frequency range lets you replace sorting with bucketing.
''',
r'''
class Solution {
    public int[] topKFrequent(int[] nums, int k) {
        Map<Integer, Integer> freq = new HashMap<>();
        for (int x : nums) freq.merge(x, 1, Integer::sum);

        List<Integer>[] buckets = new List[nums.length + 1];
        for (Map.Entry<Integer, Integer> e : freq.entrySet()) {
            int f = e.getValue();
            if (buckets[f] == null) buckets[f] = new ArrayList<>();
            buckets[f].add(e.getKey());
        }

        int[] result = new int[k];
        int idx = 0;
        for (int f = nums.length; f > 0 && idx < k; f--) {
            if (buckets[f] == null) continue;
            for (int val : buckets[f]) {
                if (idx == k) break;
                result[idx++] = val;
            }
        }
        return result;
    }
}
''', "O(n)", "O(n)", True),

P("product-of-array-except-self", "Product of Array Except Self", "Medium", "Amazon, Microsoft, Apple, Uber, Goldman Sachs, Walmart",
"Build an output array where each position holds the product of every other element of the input, without using division and in O(n). Example: [1,2,3,4] -> [24,12,8,6].",
r'''
**Brute force:** for each index multiply all others, O(n²). Division fails with zeros and is banned anyway.

**Optimal:** `answer[i] = (product of everything left of i) * (product of everything right of i)`.
- Pass 1 (left to right): store the running left product in `answer[i]`.
- Pass 2 (right to left): keep a running `right` product and multiply it in.

This uses the output array as storage, so extra space is O(1).
''',
r'''
class Solution {
    public int[] productExceptSelf(int[] nums) {
        int n = nums.length;
        int[] answer = new int[n];
        answer[0] = 1;
        for (int i = 1; i < n; i++) {
            answer[i] = answer[i - 1] * nums[i - 1];
        }
        int right = 1;
        for (int i = n - 1; i >= 0; i--) {
            answer[i] *= right;
            right *= nums[i];
        }
        return answer;
    }
}
''', "O(n)", "O(1) extra", True),

P("longest-consecutive-sequence", "Longest Consecutive Sequence", "Medium", "Google, Amazon, Microsoft, Uber, Flipkart, PhonePe",
"Given an unsorted integer array, return the length of the longest run of consecutive integers (in value, not position), in O(n) time. Example: [100,4,200,1,3,2] -> 4 because of 1,2,3,4.",
r'''
**Brute force:** sort and scan, O(n log n) - not allowed by the O(n) requirement.

**Optimal:** put everything in a `HashSet`. Only start counting from a number `x` if `x - 1` is **not** in the set (so `x` is the start of a run). From there, walk `x+1, x+2, ...` while present. Each number is visited at most twice overall, so it is O(n).

**Key insight:** only expand from sequence starts to avoid repeated work.
''',
r'''
class Solution {
    public int longestConsecutive(int[] nums) {
        Set<Integer> set = new HashSet<>();
        for (int x : nums) set.add(x);
        int best = 0;
        for (int x : set) {
            if (set.contains(x - 1)) continue; // not the start of a run
            int len = 1;
            while (set.contains(x + len)) len++;
            best = Math.max(best, len);
        }
        return best;
    }
}
''', "O(n)", "O(n)", True),

P("subarray-sum-equals-k", "Subarray Sum Equals K", "Medium", "Facebook, Amazon, Google, Microsoft, Goldman Sachs, Atlassian",
"Count how many contiguous subarrays have a sum exactly equal to k (values may be negative). Example: nums = [1,1,1], k = 2 -> 2; nums = [1,2,3], k = 3 -> 2.",
r'''
**Brute force:** all O(n²) subarrays with running sums.

**Why not sliding window?** Negative numbers mean shrinking the window doesn't guarantee the sum decreases.

**Optimal - prefix sums:** sum(i..j) = prefix[j] - prefix[i-1]. So for each running prefix `p`, the number of subarrays ending here with sum k equals how many earlier prefixes equal `p - k`. Keep a HashMap of prefix -> frequency, seeded with `{0: 1}` for subarrays that start at index 0.
''',
r'''
class Solution {
    public int subarraySum(int[] nums, int k) {
        Map<Integer, Integer> freq = new HashMap<>();
        freq.put(0, 1);
        int prefix = 0, count = 0;
        for (int x : nums) {
            prefix += x;
            count += freq.getOrDefault(prefix - k, 0);
            freq.merge(prefix, 1, Integer::sum);
        }
        return count;
    }
}
''', "O(n)", "O(n)", True),

P("maximum-subarray", "Maximum Subarray (Kadane)", "Medium", "Amazon, Microsoft, LinkedIn, Apple, Paytm, Zomato",
"Find the contiguous non-empty subarray with the largest sum and return that sum. Example: [-2,1,-3,4,-1,2,1,-5,4] -> 6 from [4,-1,2,1].",
r'''
**Brute force:** try all subarrays, O(n²).

**Kadane's algorithm:** at each index decide: is it better to *extend* the best subarray ending at the previous index, or *start fresh* here? `cur = max(x, cur + x)`. Track the global best. If `cur` becomes negative it can only hurt future sums, which is why restarting works.

**Follow-up:** to return the subarray itself, record the start index whenever you restart and the end when best improves. Initialise `best` with the first element so all-negative arrays work.
''',
r'''
class Solution {
    public int maxSubArray(int[] nums) {
        int cur = nums[0], best = nums[0];
        for (int i = 1; i < nums.length; i++) {
            cur = Math.max(nums[i], cur + nums[i]);
            best = Math.max(best, cur);
        }
        return best;
    }
}
''', "O(n)", "O(1)", True),

P("sort-colors", "Sort Colors (Dutch National Flag)", "Medium", "Microsoft, Amazon, Adobe, Flipkart, Paytm",
"An array contains only 0s, 1s and 2s (red, white, blue). Sort it in place in a single pass without a library sort. Example: [2,0,2,1,1,0] -> [0,0,1,1,2,2].",
r'''
**Simple:** count 0s/1s/2s then overwrite - two passes.

**One pass - Dutch National Flag:** keep three pointers.
- `[0, low)` holds 0s, `[low, mid)` holds 1s, `(high, end]` holds 2s.
- If `nums[mid] == 0`: swap with `low`, advance both.
- If `1`: just advance `mid`.
- If `2`: swap with `high`, decrement `high` but **don't** advance `mid` (the swapped-in value is unchecked).

Loop while `mid <= high`.
''',
r'''
class Solution {
    public void sortColors(int[] nums) {
        int low = 0, mid = 0, high = nums.length - 1;
        while (mid <= high) {
            if (nums[mid] == 0) {
                swap(nums, low++, mid++);
            } else if (nums[mid] == 1) {
                mid++;
            } else {
                swap(nums, mid, high--);
            }
        }
    }

    private void swap(int[] a, int i, int j) {
        int t = a[i]; a[i] = a[j]; a[j] = t;
    }
}
''', "O(n)", "O(1)", True),

P("majority-element", "Majority Element", "Easy", "Amazon, Google, Microsoft, Adobe, Zomato",
"Return the element that appears more than n/2 times in the array; it is guaranteed to exist. Example: [2,2,1,1,1,2,2] -> 2.",
r'''
**Options:** HashMap counts (O(n) space) or sort and take the middle (O(n log n)).

**Optimal - Boyer-Moore voting:** keep a `candidate` and a `count`. When count is 0, adopt the current element as candidate. Same element -> count++, different -> count--. Since the majority outnumbers all others combined, it survives the cancellations. O(n) time, O(1) space.

If the majority is not guaranteed, do a second pass to verify the candidate's count.
''',
r'''
class Solution {
    public int majorityElement(int[] nums) {
        int candidate = 0, count = 0;
        for (int x : nums) {
            if (count == 0) candidate = x;
            count += (x == candidate) ? 1 : -1;
        }
        return candidate;
    }
}
''', "O(n)", "O(1)"),

P("majority-element-ii", "Majority Element II", "Medium", "Amazon, Google, Zenefits, Adobe",
"Return all elements that appear more than n/3 times in the array (there can be at most two). Example: [3,2,3] -> [3]; [1,2] -> [1,2].",
r'''
**Observation:** at most two values can exceed n/3.

**Extended Boyer-Moore:** keep two candidates with two counts. For each number: if it matches a candidate, bump that count; else if a count is 0, take over that slot; else decrement both counts (cancel a triple of distinct values).

The survivors are only *possible* answers, so do a **second pass** to count them and keep those with count > n/3. O(n) time, O(1) space.
''',
r'''
class Solution {
    public List<Integer> majorityElement(int[] nums) {
        int c1 = 0, c2 = 1, n1 = 0, n2 = 0; // distinct dummy candidates
        for (int x : nums) {
            if (x == c1) n1++;
            else if (x == c2) n2++;
            else if (n1 == 0) { c1 = x; n1 = 1; }
            else if (n2 == 0) { c2 = x; n2 = 1; }
            else { n1--; n2--; }
        }
        n1 = 0; n2 = 0;
        for (int x : nums) {
            if (x == c1) n1++;
            else if (x == c2) n2++;
        }
        List<Integer> res = new ArrayList<>();
        if (n1 > nums.length / 3) res.add(c1);
        if (n2 > nums.length / 3) res.add(c2);
        return res;
    }
}
''', "O(n)", "O(1)"),

P("next-permutation", "Next Permutation", "Medium", "Google, Amazon, Microsoft, Adobe, Goldman Sachs, Uber",
"Rearrange the array into the next lexicographically larger ordering of its numbers, in place; if it is already the largest, wrap around to the smallest (sorted ascending). Example: [1,2,3] -> [1,3,2]; [3,2,1] -> [1,2,3].",
r'''
**Brute force:** generate all permutations - factorial, useless.

**Optimal (3 steps):**
1. From the right, find the first index `i` with `nums[i] < nums[i+1]` (the "pivot"). Everything right of it is descending.
2. If such `i` exists, find from the right the first `j` with `nums[j] > nums[i]` and swap them.
3. Reverse the suffix after `i` to make it ascending (smallest possible).

If no pivot exists the whole array is descending, so reversing it gives the smallest permutation.
''',
r'''
class Solution {
    public void nextPermutation(int[] nums) {
        int i = nums.length - 2;
        while (i >= 0 && nums[i] >= nums[i + 1]) i--;
        if (i >= 0) {
            int j = nums.length - 1;
            while (nums[j] <= nums[i]) j--;
            swap(nums, i, j);
        }
        reverse(nums, i + 1, nums.length - 1);
    }

    private void reverse(int[] a, int l, int r) {
        while (l < r) swap(a, l++, r--);
    }

    private void swap(int[] a, int i, int j) {
        int t = a[i]; a[i] = a[j]; a[j] = t;
    }
}
''', "O(n)", "O(1)", True),

P("merge-sorted-array", "Merge Sorted Array", "Easy", "Microsoft, Amazon, Facebook, Apple, Oracle",
"nums1 has length m + n with its first m elements sorted and n trailing zeros; nums2 has n sorted elements. Merge nums2 into nums1 in place so it is fully sorted. Example: [1,2,3,0,0,0], m=3, [2,5,6], n=3 -> [1,2,2,3,5,6].",
r'''
**Naive:** copy nums2 into the tail and sort, O((m+n) log(m+n)).

**Optimal:** fill nums1 **from the back**. Use pointers at the end of the real data in both arrays and a write pointer at the very end. Put the larger of the two values at the write pointer. Writing from the back never overwrites unread nums1 values. When nums2 is exhausted you're done (remaining nums1 values are already in place).
''',
r'''
class Solution {
    public void merge(int[] nums1, int m, int[] nums2, int n) {
        int i = m - 1, j = n - 1, write = m + n - 1;
        while (j >= 0) {
            if (i >= 0 && nums1[i] > nums2[j]) {
                nums1[write--] = nums1[i--];
            } else {
                nums1[write--] = nums2[j--];
            }
        }
    }
}
''', "O(m + n)", "O(1)"),

P("merge-intervals", "Merge Intervals", "Medium", "Google, Facebook, Amazon, Microsoft, Uber, Atlassian, Swiggy",
"Given a list of [start, end] intervals, merge all overlapping ones and return the non-overlapping result. Example: [[1,3],[2,6],[8,10],[15,18]] -> [[1,6],[8,10],[15,18]].",
r'''
**Key step:** sort by start time. After sorting, overlapping intervals are adjacent.

Walk the sorted list keeping the "current" merged interval. If the next interval starts at or before the current end, extend `end = max(end, next.end)`. Otherwise push the current one and start a new one.

**Pitfall:** use `Integer.compare` (or `a[0] - b[0]` only when values can't overflow) in the comparator, and remember touching intervals like [1,4],[4,5] count as overlapping here.
''',
r'''
class Solution {
    public int[][] merge(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        List<int[]> merged = new ArrayList<>();
        int[] cur = intervals[0];
        merged.add(cur);
        for (int[] next : intervals) {
            if (next[0] <= cur[1]) {
                cur[1] = Math.max(cur[1], next[1]);
            } else {
                cur = next;
                merged.add(cur);
            }
        }
        return merged.toArray(new int[0][]);
    }
}
''', "O(n log n)", "O(n)", True),

P("set-matrix-zeroes", "Set Matrix Zeroes", "Medium", "Microsoft, Amazon, Facebook, Oracle, Adobe",
"In an m x n matrix, whenever a cell is 0, set its entire row and column to 0, doing it in place. Example: [[1,1,1],[1,0,1],[1,1,1]] -> [[1,0,1],[0,0,0],[1,0,1]].",
r'''
**Brute force:** copy the matrix, O(mn) space. **Better:** two boolean arrays for rows/cols, O(m+n) space.

**Optimal O(1) space:** use the **first row and first column as the marker arrays**. Since they themselves may contain zeros, first record in two booleans whether row 0 / column 0 originally had a zero. Then mark, then zero out the inner cells based on markers, and finally zero row 0 / column 0 if needed. Order matters - handle the first row/column last.
''',
r'''
class Solution {
    public void setZeroes(int[][] matrix) {
        int m = matrix.length, n = matrix[0].length;
        boolean firstRow = false, firstCol = false;
        for (int i = 0; i < m; i++) if (matrix[i][0] == 0) firstCol = true;
        for (int j = 0; j < n; j++) if (matrix[0][j] == 0) firstRow = true;

        for (int i = 1; i < m; i++) {
            for (int j = 1; j < n; j++) {
                if (matrix[i][j] == 0) {
                    matrix[i][0] = 0;
                    matrix[0][j] = 0;
                }
            }
        }
        for (int i = 1; i < m; i++) {
            for (int j = 1; j < n; j++) {
                if (matrix[i][0] == 0 || matrix[0][j] == 0) matrix[i][j] = 0;
            }
        }
        if (firstCol) for (int i = 0; i < m; i++) matrix[i][0] = 0;
        if (firstRow) for (int j = 0; j < n; j++) matrix[0][j] = 0;
    }
}
''', "O(m * n)", "O(1)"),

P("rotate-image", "Rotate Image", "Medium", "Microsoft, Amazon, Apple, Adobe, Cisco",
"Rotate an n x n matrix 90 degrees clockwise, modifying it in place. Example: [[1,2,3],[4,5,6],[7,8,9]] -> [[7,4,1],[8,5,2],[9,6,3]].",
r'''
**With extra space:** `rotated[j][n-1-i] = matrix[i][j]` - but in-place is required.

**Trick:** a clockwise rotation = **transpose** (swap `[i][j]` with `[j][i]` for j > i) followed by **reversing each row**. Both steps are easy in place.

(Counter-clockwise = transpose then reverse each column.) O(n²) time, O(1) space.
''',
r'''
class Solution {
    public void rotate(int[][] matrix) {
        int n = matrix.length;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                int t = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = t;
            }
        }
        for (int[] row : matrix) {
            for (int l = 0, r = n - 1; l < r; l++, r--) {
                int t = row[l]; row[l] = row[r]; row[r] = t;
            }
        }
    }
}
''', "O(n^2)", "O(1)"),

P("spiral-matrix", "Spiral Matrix", "Medium", "Microsoft, Amazon, Google, Apple, Paytm",
"Return all elements of an m x n matrix in clockwise spiral order starting from the top-left. Example: [[1,2,3],[4,5,6],[7,8,9]] -> [1,2,3,6,9,8,7,4,5].",
r'''
Maintain four boundaries: `top`, `bottom`, `left`, `right`. Repeat while `top <= bottom && left <= right`:
1. Go right along `top`, then `top++`.
2. Go down along `right`, then `right--`.
3. If `top <= bottom`, go left along `bottom`, then `bottom--`.
4. If `left <= right`, go up along `left`, then `left++`.

The two `if` checks prevent double-counting when only a single row or column remains - the most common bug.
''',
r'''
class Solution {
    public List<Integer> spiralOrder(int[][] matrix) {
        List<Integer> res = new ArrayList<>();
        int top = 0, bottom = matrix.length - 1;
        int left = 0, right = matrix[0].length - 1;
        while (top <= bottom && left <= right) {
            for (int j = left; j <= right; j++) res.add(matrix[top][j]);
            top++;
            for (int i = top; i <= bottom; i++) res.add(matrix[i][right]);
            right--;
            if (top <= bottom) {
                for (int j = right; j >= left; j--) res.add(matrix[bottom][j]);
                bottom--;
            }
            if (left <= right) {
                for (int i = bottom; i >= top; i--) res.add(matrix[i][left]);
                left++;
            }
        }
        return res;
    }
}
''', "O(m * n)", "O(1) extra"),

P("best-time-to-buy-and-sell-stock", "Best Time to Buy and Sell Stock", "Easy", "Amazon, Microsoft, Facebook, Goldman Sachs, Flipkart, PhonePe",
"prices[i] is a stock's price on day i. Pick one day to buy and a later day to sell to maximize profit; return 0 if no profit is possible. Example: [7,1,5,3,6,4] -> 5 (buy at 1, sell at 6).",
r'''
**Brute force:** every buy/sell pair, O(n²).

**Optimal:** scan once, tracking the **minimum price seen so far**. At each day, the best profit if you sell today is `price - minSoFar`. Keep the maximum of those. O(n) time, O(1) space.

This is Kadane in disguise: it maximizes the sum of daily price differences.
''',
r'''
class Solution {
    public int maxProfit(int[] prices) {
        int minPrice = Integer.MAX_VALUE, best = 0;
        for (int p : prices) {
            minPrice = Math.min(minPrice, p);
            best = Math.max(best, p - minPrice);
        }
        return best;
    }
}
''', "O(n)", "O(1)", True),

P("valid-sudoku", "Valid Sudoku", "Medium", "Amazon, Apple, Uber, Microsoft, Snapchat",
"Check whether a partially filled 9x9 Sudoku board is valid: no digit repeats in any row, column, or 3x3 box (empty cells are '.'). You don't need to check solvability.",
r'''
Single pass with three `boolean[9][9]` tables: `rows[r][d]`, `cols[c][d]`, `boxes[b][d]`, where the box index is `b = (r / 3) * 3 + c / 3`.

For each filled cell with digit `d`, if any of the three flags is already set, the board is invalid; otherwise set all three. O(81) = O(1) time and space.

**Alternative:** a single `HashSet<String>` with keys like `"5 in row 0"`, `"5 in col 3"`, `"5 in box 1"` - concise but slower.
''',
r'''
class Solution {
    public boolean isValidSudoku(char[][] board) {
        boolean[][] rows = new boolean[9][9];
        boolean[][] cols = new boolean[9][9];
        boolean[][] boxes = new boolean[9][9];
        for (int r = 0; r < 9; r++) {
            for (int c = 0; c < 9; c++) {
                char ch = board[r][c];
                if (ch == '.') continue;
                int d = ch - '1';
                int b = (r / 3) * 3 + c / 3;
                if (rows[r][d] || cols[c][d] || boxes[b][d]) return false;
                rows[r][d] = cols[c][d] = boxes[b][d] = true;
            }
        }
        return true;
    }
}
''', "O(1)", "O(1)"),
]

PATTERN = PAT("arrays-hashing", "Arrays & Hashing", 1, INTRO, problems)
