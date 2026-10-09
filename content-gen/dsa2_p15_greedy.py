from dsa2_common import P

INTRO = r"""
A **greedy** algorithm makes the locally best choice at each step and never revisits it. It's fast and short — but only correct when you can argue that a local choice never hurts the global answer.

**How to recognize it**
- You can sort or scan once and decide on the spot (furthest reach, earliest end time, largest frequency first).
- A DP solution exists but feels like overkill, and there's a simple "always pick X" rule.
- Phrases: "minimum number of jumps/arrows/rooms", "can you reach", "maximize by choosing".

**How to justify a greedy choice (interviewers will ask "why does this work?")**
- *Exchange argument:* take any optimal solution; swapping its choice for the greedy choice doesn't make it worse.
- *Stays-ahead argument:* after every step, greedy is at least as good as any other strategy.
- If you can't argue it, try a counterexample of size 3–4. If greedy breaks, switch to DP.

**Common greedy shapes**
```java
// 1. Track the furthest reachable point (Jump Game)
int reach = 0;
for (int i = 0; i < n; i++) {
    if (i > reach) return false;
    reach = Math.max(reach, i + nums[i]);
}

// 2. Running balance that resets (Gas Station, Kadane)
int tank = 0, start = 0;
for (int i = 0; i < n; i++) {
    tank += gain[i];
    if (tank < 0) { start = i + 1; tank = 0; }
}

// 3. Sort, then sweep (intervals, hand of straights)
Arrays.sort(arr);
```

**Pitfalls**
- Greedy feels right for Coin Change but is wrong for arbitrary coins — always test a small counterexample.
- Track a *range* when a single value isn't enough (Valid Parenthesis String keeps min/max open count).
- Off-by-one in BFS-like greedy (Jump Game II: don't jump at the last index).
"""

PROBLEMS = [
P("jump-game", "Jump Game", "Medium", ["Amazon", "Microsoft", "Google", "Adobe", "Flipkart"],
"""Each array element is the maximum jump length from that position. Starting at index 0, decide whether you can reach the last index. `[2,3,1,1,4]` → true; `[3,2,1,0,4]` → false (everyone gets stuck at the 0).""",
"""**DP (O(n²)):** `canReach[i]` if some earlier reachable j has `j + nums[j] ≥ i`.

**Greedy (O(n)):** keep `reach` = furthest index reachable so far. Scan left to right: if `i > reach`, index i is unreachable → false. Otherwise update `reach = max(reach, i + nums[i])`. If `reach ≥ n − 1`, return true.

Why it works: every index ≤ reach is reachable, so the furthest reach is all that matters.""",
r"""
class Solution {
    public boolean canJump(int[] nums) {
        int reach = 0;
        for (int i = 0; i < nums.length; i++) {
            if (i > reach) return false;
            reach = Math.max(reach, i + nums[i]);
            if (reach >= nums.length - 1) return true;
        }
        return true;
    }
}
""", "O(n)", "O(1)", True),

P("jump-game-ii", "Jump Game II", "Medium", ["Amazon", "Microsoft", "Google", "Uber", "Walmart"],
"""Same setup as Jump Game, but the last index is always reachable; return the minimum number of jumps to get there. `[2,3,1,1,4]` → 2 (0 → 1 → 4).""",
"""**Think of it as BFS by levels without a queue.** All indices reachable with `jumps` jumps form a window `[.., curEnd]`. While scanning that window, track `farthest = max(i + nums[i])` — the end of the next window. When `i` hits `curEnd`, you must jump: `jumps++`, `curEnd = farthest`.

Loop only to `n − 2`; jumping from the last index would overcount.""",
r"""
class Solution {
    public int jump(int[] nums) {
        int jumps = 0, curEnd = 0, farthest = 0;
        for (int i = 0; i < nums.length - 1; i++) {
            farthest = Math.max(farthest, i + nums[i]);
            if (i == curEnd) {
                jumps++;
                curEnd = farthest;
            }
        }
        return jumps;
    }
}
""", "O(n)", "O(1)", True),

P("gas-station", "Gas Station", "Medium", ["Amazon", "Microsoft", "Google", "Goldman Sachs", "PhonePe"],
"""Stations sit on a circular road; station i gives `gas[i]` fuel and driving to the next costs `cost[i]`. Starting with an empty tank, return the station index from which you can complete the circle, or −1. The answer is unique if it exists.""",
"""**Fact 1:** if `sum(gas) < sum(cost)`, no start works → −1. Otherwise a valid start exists.

**Fact 2 (key insight):** if you start at s and run out of fuel just before station i, then **no station between s and i** can be a valid start either (they'd arrive at i with even less fuel). So jump the candidate start to `i + 1` and reset the tank.

One pass: accumulate `tank += gas[i] − cost[i]`; when it goes negative, set `start = i + 1`, `tank = 0`.""",
r"""
class Solution {
    public int canCompleteCircuit(int[] gas, int[] cost) {
        int total = 0, tank = 0, start = 0;
        for (int i = 0; i < gas.length; i++) {
            int diff = gas[i] - cost[i];
            total += diff;
            tank += diff;
            if (tank < 0) {
                start = i + 1;
                tank = 0;
            }
        }
        return total < 0 ? -1 : start;
    }
}
""", "O(n)", "O(1)", True),

P("hand-of-straights", "Hand of Straights", "Medium", ["Amazon", "Google", "Microsoft"],
"""Decide whether an array of card values can be rearranged into groups of exactly `groupSize` consecutive values. `[1,2,3,6,2,3,4,7,8]` with size 3 → true: `[1,2,3],[2,3,4],[6,7,8]`.""",
"""**Key insight:** the smallest card left must start a group (nothing smaller can contain it). So repeatedly take the smallest remaining value x and consume `x, x+1, ..., x+groupSize−1`; if any is missing, fail.

Use a `TreeMap<value, count>`: `firstKey()` gives the smallest. Consume `count(x)` groups at once to be efficient. Early exit: `n % groupSize != 0` → false.""",
r"""
import java.util.*;

class Solution {
    public boolean isNStraightHand(int[] hand, int groupSize) {
        if (hand.length % groupSize != 0) return false;
        TreeMap<Integer, Integer> count = new TreeMap<>();
        for (int card : hand) count.merge(card, 1, Integer::sum);
        while (!count.isEmpty()) {
            int first = count.firstKey();
            int need = count.get(first);
            for (int v = first; v < first + groupSize; v++) {
                Integer have = count.get(v);
                if (have == null || have < need) return false;
                if (have == need) count.remove(v);
                else count.put(v, have - need);
            }
        }
        return true;
    }
}
""", "O(n log n)", "O(n)", False),

P("partition-labels", "Partition Labels", "Medium", ["Amazon", "Microsoft", "Google", "Flipkart", "Swiggy"],
"""Split a string into as many parts as possible so each letter appears in at most one part; return the part sizes. `"ababcbacadefegdehijhklij"` → `[9,7,8]`.""",
"""**Step 1:** record the last index of every character.

**Step 2:** scan with a window. Extend `end = max(end, last[s[i]])` — the current part must reach at least as far as the last occurrence of every char in it. When `i == end`, nothing inside reaches beyond, so close the part, record its length, and start a new one.

Greedy is optimal because we cut at the earliest possible point every time.""",
r"""
import java.util.*;

class Solution {
    public List<Integer> partitionLabels(String s) {
        int[] last = new int[26];
        for (int i = 0; i < s.length(); i++) last[s.charAt(i) - 'a'] = i;
        List<Integer> res = new ArrayList<>();
        int start = 0, end = 0;
        for (int i = 0; i < s.length(); i++) {
            end = Math.max(end, last[s.charAt(i) - 'a']);
            if (i == end) {
                res.add(end - start + 1);
                start = i + 1;
            }
        }
        return res;
    }
}
""", "O(n)", "O(1)", True),

P("valid-parenthesis-string", "Valid Parenthesis String", "Medium", ["Amazon", "Google", "Microsoft", "Salesforce"],
"""A string contains `(`, `)` and `*`, where `*` can act as `(`, `)` or nothing. Decide whether it can be a valid balanced string. `"(*)"` → true, `"(*))"` → true, `")("` → false.""",
"""**Brute force:** try 3 options for every `*` → 3^k.

**Greedy with a range:** track the possible number of open brackets as an interval `[lo, hi]`.
- `(` → `lo++, hi++`
- `)` → `lo--, hi--`
- `*` → `lo--` (treat as `)`), `hi++` (treat as `(`)

If `hi < 0`, too many `)` even in the best case → false. Clamp `lo` at 0 (we can't have negative opens; choose `*` as empty instead). At the end, valid iff `lo == 0`.""",
r"""
class Solution {
    public boolean checkValidString(String s) {
        int lo = 0, hi = 0;
        for (char c : s.toCharArray()) {
            if (c == '(') {
                lo++;
                hi++;
            } else if (c == ')') {
                lo--;
                hi--;
            } else {
                lo--;
                hi++;
            }
            if (hi < 0) return false;
            lo = Math.max(lo, 0);
        }
        return lo == 0;
    }
}
""", "O(n)", "O(1)", False),

P("task-scheduler", "Task Scheduler", "Medium", ["Amazon", "Microsoft", "Google", "Uber", "Atlassian", "Salesforce"],
"""CPU tasks are letters; each takes one unit, and identical tasks must be at least n units apart (idle slots allowed). Return the minimum total time. `["A","A","A","B","B","B"]`, n = 2 → 8 (`A B idle A B idle A B`).""",
"""**Key insight — the most frequent task dictates the layout.** Let `maxFreq` be the highest count and `maxCount` the number of tasks with that count. Arrange the most frequent task into `maxFreq − 1` blocks of size `n + 1`, plus a final partial block of size `maxCount`:

`slots = (maxFreq − 1) · (n + 1) + maxCount`.

Other tasks fill the idle gaps. If there are more tasks than slots, no idling is needed → answer is `max(slots, tasks.length)`.

(A max-heap + cooldown queue simulation also works and is easier to extend if the interviewer changes rules.)""",
r"""
class Solution {
    public int leastInterval(char[] tasks, int n) {
        int[] freq = new int[26];
        for (char t : tasks) freq[t - 'A']++;
        int maxFreq = 0, maxCount = 0;
        for (int f : freq) {
            if (f > maxFreq) {
                maxFreq = f;
                maxCount = 1;
            } else if (f == maxFreq) {
                maxCount++;
            }
        }
        int slots = (maxFreq - 1) * (n + 1) + maxCount;
        return Math.max(slots, tasks.length);
    }
}
""", "O(n)", "O(1)", True),
]

PATTERN = {"id": "greedy", "name": "Greedy", "order": 15, "intro": INTRO.strip(), "problems": PROBLEMS}
