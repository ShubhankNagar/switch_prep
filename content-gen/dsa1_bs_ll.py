from dsa1_common import P, PAT

BS_INTRO = r'''
**Binary Search** repeatedly halves a search space whose elements satisfy a **monotonic** condition: everything on one side is "false", everything on the other is "true". It turns O(n) into O(log n).

**Two kinds of questions**
1. **Search in a sorted (or rotated / 2D) array** - find a target, first/last occurrence, insertion point, peak.
2. **Binary search on the answer** - the answer is a number in a range `[lo, hi]`, and there is a `feasible(x)` check that is monotonic ("if speed x works, any faster speed works too"). Examples: Koko eating bananas, ship packages in D days, split array largest sum, aggressive cows, allocate books.

**How to recognize "search on answer":** the question says *minimize the maximum* / *maximize the minimum* / *smallest X such that...*, and checking a candidate is easy (greedy O(n)).

**Template - first index where condition is true (lower bound)**
```java
int lo = 0, hi = n;              // hi = n means "not found"
while (lo < hi) {
    int mid = lo + (hi - lo) / 2; // avoids overflow
    if (condition(mid)) hi = mid; // mid might be the answer, keep it
    else lo = mid + 1;            // mid is definitely not it
}
return lo;
```

**Template - minimum feasible answer**
```java
int lo = minPossible, hi = maxPossible;
while (lo < hi) {
    int mid = lo + (hi - lo) / 2;
    if (feasible(mid)) hi = mid;
    else lo = mid + 1;
}
return lo;
```

**Pitfalls**
- `(lo + hi) / 2` can overflow - use `lo + (hi - lo) / 2`.
- Infinite loops: with `lo < hi` and `lo = mid`, use an upper mid `lo + (hi - lo + 1) / 2`.
- Mixing styles: `while (lo <= hi)` pairs with `hi = mid - 1`; `while (lo < hi)` pairs with `hi = mid`. Pick one style and stick to it.
- Feasibility sums can overflow `int` - use `long`.
'''

bs = [
P("binary-search", "Binary Search", "Easy", "Microsoft, Amazon, Google, Adobe",
"Given an ascending array of distinct integers and a target, return the target's index or -1, in O(log n). Example: [-1,0,3,5,9,12], target 9 -> 4.",
r'''
Classic closed-interval search: keep `[lo, hi]`. Compare the middle element: equal -> return; smaller than target -> the answer lies right (`lo = mid + 1`); bigger -> left (`hi = mid - 1`). Stop when the interval is empty.

Write it bug-free in under two minutes - it's the base of every other problem in this section.
''',
r'''
class Solution {
    public int search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }
}
''', "O(log n)", "O(1)"),

P("search-a-2d-matrix", "Search a 2D Matrix", "Medium", "Amazon, Microsoft, Facebook, Bloomberg, Adobe",
"Each row of the matrix is sorted and each row's first value is greater than the previous row's last value. Determine whether target exists, in O(log(m*n)). Example: [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target 3 -> true.",
r'''
The matrix is really one sorted array of length `m*n` laid out row by row. Binary search over virtual indices `0..m*n-1` and map index `k` to `matrix[k / n][k % n]`.

(For LC 240, where only rows and columns are sorted independently, start from the top-right corner and move left/down - O(m + n).)
''',
r'''
class Solution {
    public boolean searchMatrix(int[][] matrix, int target) {
        int m = matrix.length, n = matrix[0].length;
        int lo = 0, hi = m * n - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            int val = matrix[mid / n][mid % n];
            if (val == target) return true;
            if (val < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return false;
    }
}
''', "O(log(m*n))", "O(1)"),

P("search-in-rotated-sorted-array", "Search in Rotated Sorted Array", "Medium", "Amazon, Microsoft, Google, Facebook, Flipkart, Adobe, Paytm",
"A sorted array of distinct values was rotated at an unknown pivot (e.g. [0,1,2,4,5,6,7] -> [4,5,6,7,0,1,2]). Find target's index or -1 in O(log n). Example: target 0 -> 4.",
r'''
At any `mid`, **at least one half is sorted**. Check which:
- If `nums[lo] <= nums[mid]`, the left half is sorted. If target lies in `[nums[lo], nums[mid])`, go left; else go right.
- Otherwise the right half is sorted. If target lies in `(nums[mid], nums[hi]]`, go right; else go left.

Each step still halves the range: O(log n). With duplicates (LC 81), when `nums[lo] == nums[mid] == nums[hi]` you can only shrink both ends by one.
''',
r'''
class Solution {
    public int search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[lo] <= nums[mid]) {                 // left half sorted
                if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else {                                     // right half sorted
                if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1;
    }
}
''', "O(log n)", "O(1)", True),

P("find-minimum-in-rotated-sorted-array", "Find Minimum in Rotated Sorted Array", "Medium", "Amazon, Microsoft, Facebook, Goldman Sachs",
"Return the minimum element of a rotated sorted array of unique values in O(log n). Example: [3,4,5,1,2] -> 1; [11,13,15,17] -> 11.",
r'''
Compare `nums[mid]` with `nums[hi]`:
- `nums[mid] > nums[hi]`: the drop (minimum) is strictly right of mid -> `lo = mid + 1`.
- Otherwise mid..hi is sorted, so the minimum is at mid or to its left -> `hi = mid`.

Loop while `lo < hi`; `lo` ends on the minimum. Comparing with `hi` (not `lo`) avoids the special case of an unrotated array.
''',
r'''
class Solution {
    public int findMin(int[] nums) {
        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] > nums[hi]) lo = mid + 1;
            else hi = mid;
        }
        return nums[lo];
    }
}
''', "O(log n)", "O(1)"),

P("find-first-and-last-position-of-element-in-sorted-array", "Find First and Last Position of Element in Sorted Array", "Medium", "Facebook, Amazon, Microsoft, Google, LinkedIn, Uber",
"In a non-decreasing array, return the first and last index of target, or [-1,-1], in O(log n). Example: [5,7,7,8,8,10], target 8 -> [3,4].",
r'''
Write one **lower-bound** helper: the first index with `nums[i] >= x`.
- first = `lowerBound(target)`; if it's out of range or not equal to target, return `[-1,-1]`.
- last = `lowerBound(target + 1) - 1`.

Two O(log n) searches. Reusing one helper avoids writing two subtly different loops - a common source of bugs.
''',
r'''
class Solution {
    public int[] searchRange(int[] nums, int target) {
        int first = lowerBound(nums, target);
        if (first == nums.length || nums[first] != target) return new int[]{-1, -1};
        int last = lowerBound(nums, target + 1) - 1;
        return new int[]{first, last};
    }

    private int lowerBound(int[] nums, int x) {
        int lo = 0, hi = nums.length;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] >= x) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }
}
''', "O(log n)", "O(1)", True),

P("koko-eating-bananas", "Koko Eating Bananas", "Medium", "Google, Amazon, Facebook, Airbnb, Flipkart",
"Koko has piles of bananas and h hours. Each hour she picks a pile and eats up to k bananas from it. Find the minimum integer speed k that lets her finish all piles within h hours. Example: piles [3,6,7,11], h = 8 -> 4.",
r'''
**Binary search on the answer.** Speed lies in `[1, max(pile)]`. At speed `k`, hours needed = sum of `ceil(p / k)` = `(p + k - 1) / k`. Hours decrease as `k` grows - monotonic! So find the smallest `k` with `hours(k) <= h`.

Each check is O(n), and there are O(log max) checks. Use `long` for the hour total.
''',
r'''
class Solution {
    public int minEatingSpeed(int[] piles, int h) {
        int lo = 1, hi = 0;
        for (int p : piles) hi = Math.max(hi, p);
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (hours(piles, mid) <= h) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    private long hours(int[] piles, int k) {
        long total = 0;
        for (int p : piles) total += (p + k - 1) / k;
        return total;
    }
}
''', "O(n log M)", "O(1)", True),

P("capacity-to-ship-packages-within-d-days", "Capacity To Ship Packages Within D Days", "Medium", "Amazon, Google, Flipkart, Microsoft, Swiggy",
"Packages with given weights must be shipped in order within `days` days; each day the ship loads consecutive packages without exceeding its capacity. Find the least capacity that works. Example: weights [1..10], days 5 -> 15.",
r'''
Search on capacity in `[max(weight), sum(weights)]` - below the max weight a package could never ship; at the sum, one day suffices.

`feasible(cap)`: greedily fill each day until adding the next package would exceed `cap`, then start a new day. If days used `<= days`, it's feasible. Larger capacity never needs more days -> monotonic -> binary search for the smallest feasible capacity.

Same template solves "Allocate Books", "Painter's Partition", "Split Array Largest Sum".
''',
r'''
class Solution {
    public int shipWithinDays(int[] weights, int days) {
        int lo = 0, hi = 0;
        for (int w : weights) {
            lo = Math.max(lo, w);
            hi += w;
        }
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (daysNeeded(weights, mid) <= days) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    private int daysNeeded(int[] weights, int cap) {
        int days = 1, load = 0;
        for (int w : weights) {
            if (load + w > cap) {
                days++;
                load = 0;
            }
            load += w;
        }
        return days;
    }
}
''', "O(n log(sum))", "O(1)", True),

P("split-array-largest-sum", "Split Array Largest Sum", "Hard", "Google, Amazon, Facebook, Microsoft, Adobe",
"Split an array of non-negative integers into k non-empty contiguous parts so that the largest part-sum is as small as possible; return that value. Example: [7,2,5,10,8], k = 2 -> 18 ([7,2,5] and [10,8]).",
r'''
"Minimize the maximum" -> binary search on the answer `limit` in `[max, sum]`.

`pieces(limit)`: greedily extend the current part while its sum stays `<= limit`; otherwise start a new part. If pieces `<= k`, `limit` is achievable (you can always split further to reach exactly k, since parts are non-empty and k <= n). Find the smallest achievable limit.

This is identical to Ship Packages, and to the Striver "Book Allocation" problem.
''',
r'''
class Solution {
    public int splitArray(int[] nums, int k) {
        int lo = 0, hi = 0;
        for (int x : nums) {
            lo = Math.max(lo, x);
            hi += x;
        }
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (pieces(nums, mid) <= k) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    private int pieces(int[] nums, int limit) {
        int count = 1, sum = 0;
        for (int x : nums) {
            if (sum + x > limit) {
                count++;
                sum = 0;
            }
            sum += x;
        }
        return count;
    }
}
''', "O(n log(sum))", "O(1)"),

P("find-peak-element", "Find Peak Element", "Medium", "Google, Facebook, Amazon, Microsoft, Uber",
"Return the index of any element strictly greater than its neighbours (treat out-of-bounds as negative infinity; adjacent values differ) in O(log n). Example: [1,2,1,3,5,6,4] -> 1 or 5.",
r'''
The array isn't sorted, but there's still a monotonic signal: compare `nums[mid]` with `nums[mid + 1]`.
- If `nums[mid] < nums[mid + 1]`, we're on an **uphill**; a peak must exist to the right (it either keeps rising to the end, which counts as a peak, or turns down somewhere). `lo = mid + 1`.
- Otherwise a peak is at `mid` or to its left. `hi = mid`.

Converges to a peak in O(log n).
''',
r'''
class Solution {
    public int findPeakElement(int[] nums) {
        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] < nums[mid + 1]) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }
}
''', "O(log n)", "O(1)"),

P("time-based-key-value-store", "Time Based Key-Value Store", "Medium", "Google, Amazon, Netflix, Uber, Atlassian",
"Design a store where set(key, value, timestamp) saves a value at a time, and get(key, timestamp) returns the value set at the largest timestamp <= the given one (or \"\"). Timestamps for set calls are strictly increasing. Example: set(\"foo\",\"bar\",1); get(\"foo\",3) -> \"bar\".",
r'''
Map each key to a list of `(timestamp, value)` pairs. Because set timestamps only increase, each list is **already sorted** - appends keep it sorted for free.

`get` = binary search for the **last** timestamp `<= t` (an upper-bound search, then step back one). O(1) set, O(log n) get.

Alternative: `TreeMap<Integer, String>` per key with `floorEntry(t)` - simpler, also O(log n), worth mentioning.
''',
r'''
class TimeMap {
    private final Map<String, List<Integer>> times = new HashMap<>();
    private final Map<String, List<String>> values = new HashMap<>();

    public TimeMap() { }

    public void set(String key, String value, int timestamp) {
        times.computeIfAbsent(key, k -> new ArrayList<>()).add(timestamp);
        values.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
    }

    public String get(String key, int timestamp) {
        List<Integer> ts = times.get(key);
        if (ts == null) return "";
        int lo = 0, hi = ts.size();          // first index with time > timestamp
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (ts.get(mid) > timestamp) hi = mid;
            else lo = mid + 1;
        }
        return lo == 0 ? "" : values.get(key).get(lo - 1);
    }
}
''', "O(1) set, O(log n) get", "O(n)"),

P("median-of-two-sorted-arrays", "Median of Two Sorted Arrays", "Hard", "Google, Amazon, Microsoft, Goldman Sachs, Adobe, Apple, Uber",
"Return the median of two sorted arrays combined, in O(log(m+n)). Example: [1,3] and [2] -> 2.0; [1,2] and [3,4] -> 2.5.",
r'''
**Brute force:** merge then pick the middle, O(m+n).

**Optimal - binary search a partition** on the smaller array `a`. Choose `i` elements from `a` and `j = half - i` from `b` for the left half, where `half = (m + n + 1) / 2`. The partition is correct when `aLeft <= bRight` and `bLeft <= aRight` (use ±infinity at edges).
- If `aLeft > bRight`, too many from `a`: `hi = i - 1`.
- Else too few: `lo = i + 1`.

Median = max of left side (odd total) or average of max-left and min-right (even). O(log(min(m, n))).
''',
r'''
class Solution {
    public double findMedianSortedArrays(int[] a, int[] b) {
        if (a.length > b.length) return findMedianSortedArrays(b, a);
        int m = a.length, n = b.length, half = (m + n + 1) / 2;
        int lo = 0, hi = m;
        while (lo <= hi) {
            int i = lo + (hi - lo) / 2;   // taken from a
            int j = half - i;             // taken from b
            int aLeft = i == 0 ? Integer.MIN_VALUE : a[i - 1];
            int aRight = i == m ? Integer.MAX_VALUE : a[i];
            int bLeft = j == 0 ? Integer.MIN_VALUE : b[j - 1];
            int bRight = j == n ? Integer.MAX_VALUE : b[j];
            if (aLeft <= bRight && bLeft <= aRight) {
                int leftMax = Math.max(aLeft, bLeft);
                if (((m + n) & 1) == 1) return leftMax;
                return (leftMax + (double) Math.min(aRight, bRight)) / 2.0;
            } else if (aLeft > bRight) {
                hi = i - 1;
            } else {
                lo = i + 1;
            }
        }
        return 0.0;
    }
}
''', "O(log(min(m, n)))", "O(1)", True),
]

LL_INTRO = r'''
**Linked List** problems test pointer manipulation without losing references. Almost every question is built from a few primitives: **dummy head**, **reverse**, **fast/slow pointers**, and **merge**.

**How to recognize the technique**
- Head might change (delete/insert at front, merging) -> use a **dummy node** pointing at head; return `dummy.next`.
- Middle of list, cycle detection, "nth from end" -> **fast & slow pointers**.
- Palindrome check, reorder, k-group -> **reverse** part of the list.
- Sorted lists combined -> **merge** (two pointers or a heap for k lists).
- O(1) get/put with order (LRU) -> **HashMap + doubly linked list**.

LeetCode's node: `class ListNode { int val; ListNode next; ListNode(int val) {...} ListNode(int val, ListNode next) {...} }` (already defined in the judge).

**Core templates**
```java
// Reverse a list iteratively
ListNode prev = null, cur = head;
while (cur != null) {
    ListNode next = cur.next;
    cur.next = prev;
    prev = cur;
    cur = next;
}
// prev is the new head

// Find middle (slow ends at the 2nd middle for even length)
ListNode slow = head, fast = head;
while (fast != null && fast.next != null) {
    slow = slow.next;
    fast = fast.next.next;
}

// Dummy head for building a result
ListNode dummy = new ListNode(0), tail = dummy;
// ... tail.next = node; tail = tail.next;
return dummy.next;
```

**Pitfalls**
- Save `cur.next` **before** you overwrite it.
- Check `fast != null && fast.next != null` in that order to avoid NPEs.
- Draw the pointers for a 3-node list on paper before coding - interviewers expect you to walk through an example.
- Remember to terminate lists (set `tail.next = null`) when splitting, or you'll create cycles.
'''

ll = [
P("reverse-linked-list", "Reverse Linked List", "Easy", "Amazon, Microsoft, Apple, Google, Adobe, Flipkart, Paytm",
"Reverse a singly linked list and return the new head. Example: 1->2->3->4->5 -> 5->4->3->2->1.",
r'''
**Iterative (preferred):** walk the list with `prev` and `cur`; for each node save `next`, point `cur.next` back to `prev`, then advance both. When `cur` is null, `prev` is the new head. O(n) time, O(1) space.

**Recursive:** reverse the rest, then make `head.next.next = head` and `head.next = null`. O(n) stack space. Know both - interviewers often ask for the second after the first.
''',
r'''
class Solution {
    public ListNode reverseList(ListNode head) {
        ListNode prev = null, cur = head;
        while (cur != null) {
            ListNode next = cur.next;
            cur.next = prev;
            prev = cur;
            cur = next;
        }
        return prev;
    }
}
''', "O(n)", "O(1)", True),

P("merge-two-sorted-lists", "Merge Two Sorted Lists", "Easy", "Amazon, Microsoft, Apple, Google, Adobe, Oracle",
"Splice two sorted linked lists into one sorted list and return its head. Example: 1->2->4 and 1->3->4 -> 1->1->2->3->4->4.",
r'''
Use a **dummy** node and a `tail` pointer. While both lists are non-empty, attach the smaller head to `tail` and advance that list. When one list runs out, attach the remainder of the other in one step (it's already sorted). Return `dummy.next`. O(n + m) time, O(1) extra space (we reuse nodes).
''',
r'''
class Solution {
    public ListNode mergeTwoLists(ListNode list1, ListNode list2) {
        ListNode dummy = new ListNode(0), tail = dummy;
        while (list1 != null && list2 != null) {
            if (list1.val <= list2.val) {
                tail.next = list1;
                list1 = list1.next;
            } else {
                tail.next = list2;
                list2 = list2.next;
            }
            tail = tail.next;
        }
        tail.next = (list1 != null) ? list1 : list2;
        return dummy.next;
    }
}
''', "O(n + m)", "O(1)", True),

P("linked-list-cycle", "Linked List Cycle", "Easy", "Amazon, Microsoft, Goldman Sachs, Oracle, Paytm",
"Determine whether a linked list contains a cycle (some node's next eventually points back to an earlier node). Example: 3->2->0->-4 with -4 pointing back to 2 -> true.",
r'''
**HashSet** of visited nodes works in O(n) space.

**Floyd's tortoise and hare:** `slow` moves 1 step, `fast` moves 2. If there's no cycle, `fast` hits null. If there is, `fast` gains one node per step on `slow` inside the cycle, so they must meet. O(n) time, O(1) space.
''',
r'''
public class Solution {
    public boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }
}
''', "O(n)", "O(1)"),

P("linked-list-cycle-ii", "Linked List Cycle II", "Medium", "Amazon, Microsoft, Google, Goldman Sachs, Adobe",
"Return the node where a cycle begins in a linked list, or null if there's no cycle, without modifying the list. Example: 3->2->0->-4 with tail linking to node 2 -> returns node 2.",
r'''
Run Floyd's algorithm until `slow` and `fast` meet. Then reset one pointer to `head` and move **both one step at a time**; they meet exactly at the cycle start.

**Why:** if `a` = distance from head to start and `b` = distance from start to meeting point, with cycle length `c`, then `2(a + b) = a + b + kc`, so `a = kc - b`: walking `a` steps from the meeting point lands on the start. O(n), O(1).
''',
r'''
public class Solution {
    public ListNode detectCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                ListNode p = head;
                while (p != slow) {
                    p = p.next;
                    slow = slow.next;
                }
                return p;
            }
        }
        return null;
    }
}
''', "O(n)", "O(1)", True),

P("remove-nth-node-from-end-of-list", "Remove Nth Node From End of List", "Medium", "Amazon, Facebook, Microsoft, Google, Adobe",
"Delete the n-th node counted from the end of a linked list and return the head, ideally in one pass. Example: 1->2->3->4->5, n = 2 -> 1->2->3->5.",
r'''
**Two passes:** count length L, then remove node L-n+1.

**One pass:** start a `fast` pointer `n + 1` steps ahead of `slow`, both starting at a **dummy** node. Move both until `fast` is null; now `slow` sits just **before** the target, so `slow.next = slow.next.next`. The dummy handles removing the head itself (n = length).
''',
r'''
class Solution {
    public ListNode removeNthFromEnd(ListNode head, int n) {
        ListNode dummy = new ListNode(0, head);
        ListNode fast = dummy, slow = dummy;
        for (int i = 0; i <= n; i++) fast = fast.next;
        while (fast != null) {
            fast = fast.next;
            slow = slow.next;
        }
        slow.next = slow.next.next;
        return dummy.next;
    }
}
''', "O(n)", "O(1)"),

P("reorder-list", "Reorder List", "Medium", "Amazon, Microsoft, Facebook, Adobe",
"Rearrange L0->L1->...->Ln into L0->Ln->L1->Ln-1->L2->... in place (change links, not values). Example: 1->2->3->4->5 -> 1->5->2->4->3.",
r'''
Combine three primitives:
1. **Find the middle** with slow/fast pointers.
2. **Reverse the second half** (and cut it off from the first half).
3. **Merge alternately**: take one from the first half, one from the reversed second half.

O(n) time, O(1) space. (Using a stack/array is simpler but O(n) space.)
''',
r'''
class Solution {
    public void reorderList(ListNode head) {
        if (head == null || head.next == null) return;
        ListNode slow = head, fast = head;
        while (fast.next != null && fast.next.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        // reverse second half
        ListNode prev = null, cur = slow.next;
        slow.next = null;
        while (cur != null) {
            ListNode next = cur.next;
            cur.next = prev;
            prev = cur;
            cur = next;
        }
        // merge
        ListNode first = head, second = prev;
        while (second != null) {
            ListNode n1 = first.next, n2 = second.next;
            first.next = second;
            second.next = n1;
            first = n1;
            second = n2;
        }
    }
}
''', "O(n)", "O(1)"),

P("add-two-numbers", "Add Two Numbers", "Medium", "Amazon, Microsoft, Bloomberg, Adobe, Apple, Flipkart",
"Two non-negative numbers are stored as linked lists of digits in reverse order. Return their sum as a linked list in the same format. Example: 2->4->3 + 5->6->4 (342 + 465) -> 7->0->8 (807).",
r'''
Simulate grade-school addition. Walk both lists together with a `carry`. At each step `sum = carry + (l1 digit or 0) + (l2 digit or 0)`; append `sum % 10`, set `carry = sum / 10`. Continue while either list remains **or carry is non-zero** (e.g. 5 + 5 = 10 needs an extra node). Dummy head keeps it clean.
''',
r'''
class Solution {
    public ListNode addTwoNumbers(ListNode l1, ListNode l2) {
        ListNode dummy = new ListNode(0), tail = dummy;
        int carry = 0;
        while (l1 != null || l2 != null || carry != 0) {
            int sum = carry;
            if (l1 != null) { sum += l1.val; l1 = l1.next; }
            if (l2 != null) { sum += l2.val; l2 = l2.next; }
            tail.next = new ListNode(sum % 10);
            tail = tail.next;
            carry = sum / 10;
        }
        return dummy.next;
    }
}
''', "O(max(n, m))", "O(1) extra"),

P("copy-list-with-random-pointer", "Copy List with Random Pointer", "Medium", "Amazon, Microsoft, Facebook, Bloomberg, Goldman Sachs, Oracle",
"Each node has next and a random pointer (to any node or null). Return a deep copy where the new nodes' pointers reference only new nodes, mirroring the original structure.",
r'''
**HashMap approach:** map each original node to its clone in one pass, then set `clone.next = map.get(orig.next)` and `clone.random = map.get(orig.random)`. O(n) space.

**O(1) space interleaving:**
1. Insert each clone right after its original: A->A'->B->B'.
2. Set `clone.random = orig.random.next` (the clone of the random target).
3. Unweave: restore originals and extract clones.
''',
r'''
class Solution {
    public Node copyRandomList(Node head) {
        if (head == null) return null;
        // 1. interleave clones
        for (Node cur = head; cur != null; cur = cur.next.next) {
            Node clone = new Node(cur.val);
            clone.next = cur.next;
            cur.next = clone;
        }
        // 2. set random pointers of clones
        for (Node cur = head; cur != null; cur = cur.next.next) {
            if (cur.random != null) cur.next.random = cur.random.next;
        }
        // 3. separate the two lists
        Node dummy = new Node(0), tail = dummy;
        for (Node cur = head; cur != null; cur = cur.next) {
            Node clone = cur.next;
            cur.next = clone.next;
            tail.next = clone;
            tail = clone;
        }
        return dummy.next;
    }
}
''', "O(n)", "O(1) extra", True),

P("lru-cache", "LRU Cache", "Medium", "Amazon, Microsoft, Google, Facebook, Uber, Flipkart, PhonePe, Swiggy, Atlassian, Salesforce",
"Design a fixed-capacity cache with get(key) and put(key, value), both O(1). When full, inserting a new key evicts the least recently used key; both get and put count as a use.",
r'''
Need O(1) lookup **and** O(1) reorder/evict:
- `HashMap<key, Node>` for lookup.
- **Doubly linked list** ordered by recency, with sentinel `head` (most recent side) and `tail` (least recent side). Unlinking and inserting a node is O(1) given the node.

`get`: if present, move node to front. `put`: update + move to front, or insert new at front; if size exceeds capacity, remove `tail.prev` and delete it from the map.

In Java you can mention `LinkedHashMap(cap, 0.75f, true)` with `removeEldestEntry`, but interviewers usually want the manual version.
''',
r'''
class LRUCache {
    private static class Node {
        int key, val;
        Node prev, next;
        Node(int k, int v) { key = k; val = v; }
    }

    private final int capacity;
    private final Map<Integer, Node> map = new HashMap<>();
    private final Node head = new Node(0, 0), tail = new Node(0, 0);

    public LRUCache(int capacity) {
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        Node node = map.get(key);
        if (node == null) return -1;
        remove(node);
        addFront(node);
        return node.val;
    }

    public void put(int key, int value) {
        Node node = map.get(key);
        if (node != null) {
            node.val = value;
            remove(node);
            addFront(node);
            return;
        }
        if (map.size() == capacity) {
            Node lru = tail.prev;
            remove(lru);
            map.remove(lru.key);
        }
        Node fresh = new Node(key, value);
        map.put(key, fresh);
        addFront(fresh);
    }

    private void remove(Node n) {
        n.prev.next = n.next;
        n.next.prev = n.prev;
    }

    private void addFront(Node n) {
        n.next = head.next;
        n.prev = head;
        head.next.prev = n;
        head.next = n;
    }
}
''', "O(1) per op", "O(capacity)", True),

P("merge-k-sorted-lists", "Merge k Sorted Lists", "Hard", "Amazon, Google, Microsoft, Facebook, Uber, Flipkart, Atlassian",
"Merge k sorted linked lists into one sorted linked list. Example: [1->4->5, 1->3->4, 2->6] -> 1->1->2->3->4->4->5->6.",
r'''
**Naive:** merge lists one by one, O(kN).

**Min-heap:** push the head of every list into a `PriorityQueue` ordered by value. Repeatedly poll the smallest, append it, and push its `next`. The heap never holds more than k nodes, so each of N nodes costs O(log k): **O(N log k)**.

**Alternative:** divide and conquer - pair up and merge lists like merge sort, also O(N log k) with O(1) extra space.
''',
r'''
class Solution {
    public ListNode mergeKLists(ListNode[] lists) {
        PriorityQueue<ListNode> pq = new PriorityQueue<>((a, b) -> Integer.compare(a.val, b.val));
        for (ListNode node : lists) {
            if (node != null) pq.offer(node);
        }
        ListNode dummy = new ListNode(0), tail = dummy;
        while (!pq.isEmpty()) {
            ListNode node = pq.poll();
            tail.next = node;
            tail = node;
            if (node.next != null) pq.offer(node.next);
        }
        return dummy.next;
    }
}
''', "O(N log k)", "O(k)", True),

P("reverse-nodes-in-k-group", "Reverse Nodes in k-Group", "Hard", "Amazon, Microsoft, Facebook, Google, Adobe, Flipkart",
"Reverse the nodes of a linked list k at a time; a final group with fewer than k nodes stays as is. Only links may change. Example: 1->2->3->4->5, k = 2 -> 2->1->4->3->5; k = 3 -> 3->2->1->4->5.",
r'''
Process group by group with a `groupPrev` pointer (starts at a dummy).
1. Walk k steps from `groupPrev` to find `kth`. If fewer than k nodes remain, stop.
2. Remember `groupNext = kth.next`. Reverse the group, initializing `prev = groupNext` so the reversed group's tail automatically links to the rest.
3. Connect: `groupPrev.next = kth` (new group head); the old first node is now the group's tail - it becomes the next `groupPrev`.

O(n) time, O(1) space.
''',
r'''
class Solution {
    public ListNode reverseKGroup(ListNode head, int k) {
        ListNode dummy = new ListNode(0, head);
        ListNode groupPrev = dummy;
        while (true) {
            ListNode kth = groupPrev;
            for (int i = 0; i < k && kth != null; i++) kth = kth.next;
            if (kth == null) break;
            ListNode groupNext = kth.next;

            ListNode prev = groupNext, cur = groupPrev.next;
            while (cur != groupNext) {
                ListNode next = cur.next;
                cur.next = prev;
                prev = cur;
                cur = next;
            }
            ListNode oldFirst = groupPrev.next;
            groupPrev.next = kth;
            groupPrev = oldFirst;
        }
        return dummy.next;
    }
}
''', "O(n)", "O(1)", True),

P("palindrome-linked-list", "Palindrome Linked List", "Easy", "Amazon, Facebook, Microsoft, Adobe, Paytm",
"Decide whether a singly linked list reads the same forwards and backwards, ideally in O(n) time and O(1) space. Example: 1->2->2->1 -> true; 1->2 -> false.",
r'''
Copying to an array is O(n) space. For O(1):
1. Find the middle with slow/fast pointers.
2. Reverse the second half.
3. Compare the first half with the reversed second half node by node.
4. (Good practice) reverse the second half back to restore the input.

For odd length, the middle node ends up in the second half and is simply compared against nothing extra - the loop runs while the reversed half is non-null.
''',
r'''
class Solution {
    public boolean isPalindrome(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        ListNode second = reverse(slow);
        ListNode p1 = head, p2 = second;
        boolean ok = true;
        while (p2 != null) {
            if (p1.val != p2.val) { ok = false; break; }
            p1 = p1.next;
            p2 = p2.next;
        }
        reverse(second); // restore (optional)
        return ok;
    }

    private ListNode reverse(ListNode head) {
        ListNode prev = null;
        while (head != null) {
            ListNode next = head.next;
            head.next = prev;
            prev = head;
            head = next;
        }
        return prev;
    }
}
''', "O(n)", "O(1)"),

P("intersection-of-two-linked-lists", "Intersection of Two Linked Lists", "Easy", "Amazon, Microsoft, Bloomberg, Goldman Sachs, Flipkart",
"Return the node at which two singly linked lists merge (same node object, not same value), or null if they never meet. Lists have no cycles.",
r'''
**HashSet:** store all nodes of A, scan B - O(n) space. **Length difference:** advance the longer list by the difference, then walk together.

**Elegant two pointers:** `a` walks A then B; `b` walks B then A. Both travel `lenA + lenB` steps, so they arrive at the intersection at the same time - or both reach null together if there is none. O(n + m), O(1).
''',
r'''
public class Solution {
    public ListNode getIntersectionNode(ListNode headA, ListNode headB) {
        ListNode a = headA, b = headB;
        while (a != b) {
            a = (a == null) ? headB : a.next;
            b = (b == null) ? headA : b.next;
        }
        return a;
    }
}
''', "O(n + m)", "O(1)"),
]

BS = PAT("binary-search", "Binary Search", 5, BS_INTRO, bs)
LL = PAT("linked-list", "Linked List", 6, LL_INTRO, ll)
