from dsa2_common import P

INTRO = r"""
**Interval** problems give you pairs `[start, end]` and ask you to merge, insert, count overlaps or remove the fewest to avoid overlaps. They are extremely common in product-company interviews because they map to real features (calendars, booking systems, rate windows).

**How to recognize it**: input is a list of `[start, end]`; words like *meeting*, *booking*, *overlap*, *merge*, *schedule*, *ranges*.

**The two sorting choices**
- **Sort by start** → merge/insert problems (scan and extend the last interval).
- **Sort by end** → "max number of non-overlapping intervals" / "min to remove" / "min arrows" (classic activity selection: always keep the interval that finishes earliest).

**Overlap test** for `a` and `b` (closed intervals): `a[0] <= b[1] && b[0] <= a[1]`. After sorting by start, it simplifies to `next[0] <= last[1]`. Read the problem to see if touching endpoints count as overlap!

**Merge template**
```java
Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
List<int[]> out = new ArrayList<>();
for (int[] cur : intervals) {
    if (out.isEmpty() || out.get(out.size() - 1)[1] < cur[0]) {
        out.add(cur);                                       // no overlap
    } else {
        int[] last = out.get(out.size() - 1);
        last[1] = Math.max(last[1], cur[1]);                // extend
    }
}
return out.toArray(new int[0][]);
```

**Counting simultaneous intervals** (meeting rooms, platforms): either a **min-heap of end times** or a **sweep line** — sort starts and ends separately and walk two pointers (+1 at a start, −1 at an end).

**Pitfalls**
- Comparator `(a, b) -> a[0] - b[0]` can overflow for values near ±2^31 — prefer `Integer.compare`.
- Forgetting `Math.max` when merging (a long interval can swallow later ones: `[1,10],[2,3]`).
- Not clarifying whether `[1,2]` and `[2,3]` overlap.
"""

PROBLEMS = [
P("merge-intervals", "Merge Intervals", "Medium", ["Amazon", "Google", "Microsoft", "Flipkart", "Uber", "Atlassian", "Salesforce", "Walmart"],
"""Given a list of intervals, merge every group of overlapping intervals and return the non-overlapping result. `[[1,3],[2,6],[8,10],[15,18]]` → `[[1,6],[8,10],[15,18]]`.""",
"""**Brute force:** compare every pair repeatedly until nothing merges → O(n²) or worse.

**Optimal:** sort by start. Now any interval that overlaps the current merged block must come right after it. Scan: if the next interval starts after the last merged one ends, start a new block; otherwise extend the last block's end with `max`.

Sorting dominates: O(n log n).""",
r"""
import java.util.*;

class Solution {
    public int[][] merge(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        List<int[]> merged = new ArrayList<>();
        for (int[] cur : intervals) {
            if (merged.isEmpty() || merged.get(merged.size() - 1)[1] < cur[0]) {
                merged.add(new int[]{cur[0], cur[1]});
            } else {
                int[] last = merged.get(merged.size() - 1);
                last[1] = Math.max(last[1], cur[1]);
            }
        }
        return merged.toArray(new int[0][]);
    }
}
""", "O(n log n)", "O(n)", True),

P("insert-interval", "Insert Interval", "Medium", ["Amazon", "Google", "Microsoft", "Uber", "Atlassian"],
"""Given non-overlapping intervals sorted by start and one new interval, insert it and merge as needed so the list stays sorted and non-overlapping. `[[1,3],[6,9]]` + `[2,5]` → `[[1,5],[6,9]]`.""",
"""Input is already sorted, so do it in **one linear pass in three phases**:
1. Copy every interval that ends **before** the new one starts.
2. Merge every interval that overlaps the new one: `new = [min(starts), max(ends)]`. Then add it.
3. Copy the rest.

No sort needed → O(n). (Adding then calling Merge Intervals is O(n log n) — mention it as the lazy option.)""",
r"""
import java.util.*;

class Solution {
    public int[][] insert(int[][] intervals, int[] newInterval) {
        List<int[]> res = new ArrayList<>();
        int i = 0, n = intervals.length;
        int start = newInterval[0], end = newInterval[1];
        while (i < n && intervals[i][1] < start) res.add(intervals[i++]);
        while (i < n && intervals[i][0] <= end) {
            start = Math.min(start, intervals[i][0]);
            end = Math.max(end, intervals[i][1]);
            i++;
        }
        res.add(new int[]{start, end});
        while (i < n) res.add(intervals[i++]);
        return res.toArray(new int[0][]);
    }
}
""", "O(n)", "O(n)", True),

P("non-overlapping-intervals", "Non-overlapping Intervals", "Medium", ["Amazon", "Google", "Microsoft", "Flipkart"],
"""Return the minimum number of intervals to remove so the rest don't overlap (touching at an endpoint is fine). `[[1,2],[2,3],[3,4],[1,3]]` → 1 (remove `[1,3]`).""",
"""**Flip the question:** removing the fewest = keeping the most non-overlapping intervals (activity selection).

**Greedy:** sort by **end**. Always keep the interval that finishes earliest, because it leaves the most room for the rest (exchange argument). Track `prevEnd`; if the next interval starts at or after `prevEnd`, keep it and update `prevEnd`; otherwise it overlaps → count a removal.

Answer = number of removals.""",
r"""
import java.util.*;

class Solution {
    public int eraseOverlapIntervals(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[1], b[1]));
        int removed = 0;
        int prevEnd = Integer.MIN_VALUE;
        for (int[] cur : intervals) {
            if (cur[0] >= prevEnd) {
                prevEnd = cur[1];
            } else {
                removed++;
            }
        }
        return removed;
    }
}
""", "O(n log n)", "O(1) (excluding sort)", True),

P("meeting-rooms-ii", "Meeting Rooms II", "Medium", ["Amazon", "Google", "Microsoft", "Uber", "Flipkart", "Atlassian", "Swiggy", "Zomato"],
"""Given meeting time intervals `[start, end)`, return the minimum number of conference rooms needed so no two overlapping meetings share a room. `[[0,30],[5,10],[15,20]]` → 2. (LeetCode Premium; the identical problem is free on GeeksforGeeks as "Minimum Platforms" and on NeetCode/LintCode 919.)""",
"""**Answer = maximum number of meetings happening at the same moment.**

**Min-heap approach:** sort by start. Keep a min-heap of end times of rooms in use. For each meeting, if the earliest-ending room is free (`heap.peek() <= start`), reuse it (poll). Push this meeting's end. Heap size at the end = rooms needed.

**Sweep-line alternative:** sort starts and ends separately; walk both — a start before the next end needs a new room, otherwise a room frees up. Both are O(n log n).""",
r"""
import java.util.*;

class Solution {
    public int minMeetingRooms(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        PriorityQueue<Integer> ends = new PriorityQueue<>();
        for (int[] m : intervals) {
            if (!ends.isEmpty() && ends.peek() <= m[0]) {
                ends.poll(); // reuse the room that freed up earliest
            }
            ends.offer(m[1]);
        }
        return ends.size();
    }
}
""", "O(n log n)", "O(n)", True),

P("minimum-number-of-arrows-to-burst-balloons", "Minimum Number of Arrows to Burst Balloons", "Medium", ["Amazon", "Google", "Microsoft"],
"""Balloons are horizontal ranges `[xstart, xend]`. A vertical arrow at x bursts every balloon whose range contains x (endpoints included). Return the minimum arrows to burst all balloons. `[[10,16],[2,8],[1,6],[7,12]]` → 2 (arrows at 6 and 11).""",
"""Same greedy as Non-overlapping Intervals. Sort by **end**. Shoot the first arrow at the end of the first balloon — the furthest right point that still bursts it, which can hit as many later balloons as possible. Skip every balloon that starts at or before that arrow; the first one starting after it needs a new arrow at its end.

**Pitfall:** values reach ±2^31, so `a[1] - b[1]` overflows — use `Integer.compare`.""",
r"""
import java.util.*;

class Solution {
    public int findMinArrowShots(int[][] points) {
        Arrays.sort(points, (a, b) -> Integer.compare(a[1], b[1]));
        int arrows = 1;
        int arrowX = points[0][1];
        for (int i = 1; i < points.length; i++) {
            if (points[i][0] > arrowX) {
                arrows++;
                arrowX = points[i][1];
            }
        }
        return arrows;
    }
}
""", "O(n log n)", "O(1) (excluding sort)", False),
]

PATTERN = {"id": "intervals", "name": "Intervals", "order": 16, "intro": INTRO.strip(), "problems": PROBLEMS}
