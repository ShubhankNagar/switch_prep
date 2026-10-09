from fr2_common import M, C, T, save

mcqs = [
M("Java Output", r'''
What happens when this runs?
```java
Integer a = null;
boolean flag = false;
Integer r = flag ? 1 : a;
System.out.println(r);
```''', ["Prints null", "Prints 1", "Throws NullPointerException", "Compile error"], 2,
'''When one operand of `?:` is a primitive `int` and the other is an `Integer`, the whole expression has type `int`. So `a` gets unboxed, and unboxing null throws NPE before anything is assigned. Write `flag ? Integer.valueOf(1) : a` to avoid it.''', ["Goldman Sachs", "Atlassian", "Amazon"]),

M("Java Streams", r'''
What does this print?
```java
Stream.of(1, 2, 3, 4)
    .filter(x -> { System.out.print("f" + x + " "); return x % 2 == 0; })
    .map(x -> { System.out.print("m" + x + " "); return x * 10; })
    .findFirst();
```''', ["f1 f2 f3 f4 m2 m4", "f1 f2 m2", "f1 m1 f2 m2", "Nothing, because streams are lazy"], 1,
'''Streams process one element at a time through the whole pipeline. 1 fails the filter. 2 passes and gets mapped. Then `findFirst` short-circuits, so 3 and 4 are never touched. Without a terminal operation, nothing would print.''', ["JP Morgan", "Walmart", "Paytm"]),

M("Collections", '''Which of these runs **without** throwing an exception?''',
["`List.of(1, 2, 3).add(4)`", "`Arrays.asList(1, 2, 3).set(0, 9)`", "`Arrays.asList(1, 2, 3).add(4)`", "`Collections.emptyList().add(1)`"], 1,
'''`Arrays.asList` returns a fixed-size list backed by the array. `set` works and writes through to the array, but `add` and `remove` throw UnsupportedOperationException. `List.of` and `emptyList` are fully immutable.''', ["Oracle", "SAP", "Walmart"]),

M("Collections", '''A class overrides `equals()` but not `hashCode()`. Two logically equal objects are used as HashMap keys. What usually happens?''',
["The map treats them as the same key", "They usually land in different buckets, so `get` with an equal-but-different instance returns null and the map can hold duplicates",
 "Compile error", "HashMap calls equals only, so it works"], 1,
'''HashMap finds the bucket using `hashCode` first and only then checks `equals`. Object's default hashCode is identity-based, so equal objects end up in different buckets. The contract is that equal objects must have equal hash codes.''', ["Amazon", "Adobe", "Oracle"]),

M("Multithreading", '''You need mutual exclusion that can **give up after a timeout** instead of blocking forever, to reduce deadlock risk. What should you use?''',
["synchronized", "ReentrantLock.tryLock(timeout, unit)", "volatile", "Thread.yield()"], 1,
'''`tryLock` with a timeout returns false if the lock isn't acquired in time, so the caller can back off, release the locks it already holds, and retry. ReentrantLock also supports fairness and interruptible locking, which `synchronized` doesn't.''', ["Goldman Sachs", "PhonePe"]),

M("Spring Core", '''In Spring Boot 2.6+, `ServiceA` takes `ServiceB` through its constructor and `ServiceB` takes `ServiceA` through its constructor. What happens at startup?''',
["Spring resolves it with proxies automatically", "Startup fails with a circular dependency error (BeanCurrentlyInCreationException), since circular references are prohibited by default",
 "One of the beans is null", "It works only with @Lazy on the class"], 1,
'''Constructor injection can't satisfy a cycle, and since 2.6 Boot also turns off field-injection cycles by default. The right fix is to redesign: extract a third service or use events. `@Lazy` on one constructor parameter is a workaround.''', ["Walmart", "Salesforce"]),

M("Spring Data JPA", '''In Spring Data JPA, what does `repository.save(entity)` do when the entity has a non-null ID (and no @Version field)?''',
["It always INSERTs", "It treats the entity as existing and calls `em.merge()`, which runs a SELECT and then an UPDATE (or INSERT if the row isn't found)",
 "It throws EntityExistsException", "It does nothing"], 1,
'''`SimpleJpaRepository.save` checks `isNew()`. With a null ID it persists, otherwise it merges. When you assign IDs yourself, implement `Persistable` to avoid the extra SELECT that merge does.''', ["Paytm", "Myntra", "Intuit"]),

M("SQL", r'''
Salaries are 300, 300, 200. What are `RANK()` and `DENSE_RANK()` for 200 when ordered by salary DESC?
```sql
SELECT salary,
       RANK()       OVER (ORDER BY salary DESC) AS r,
       DENSE_RANK() OVER (ORDER BY salary DESC) AS dr
FROM emp;
```''', ["r = 2, dr = 2", "r = 3, dr = 2", "r = 3, dr = 3", "r = 2, dr = 3"], 1,
'''RANK leaves gaps after ties: 1, 1, 3. DENSE_RANK doesn't: 1, 1, 2. ROW_NUMBER would give 1, 2, 3. For "Nth highest distinct salary", filter on DENSE_RANK = N.''', ["Amazon", "Walmart", "Goldman Sachs"]),

M("SQL", '''In MySQL, which query deletes duplicate emails and keeps the row with the **lowest id**?''',
["`DELETE FROM users WHERE email IN (SELECT email FROM users)`", "`DELETE u1 FROM users u1 JOIN users u2 ON u1.email = u2.email AND u1.id > u2.id`",
 "`DELETE FROM users GROUP BY email`", "`DELETE DISTINCT email FROM users`"], 1,
'''The self-join pairs each row with any row that has the same email and a smaller id. Rows that have such a partner are duplicates and get deleted, which leaves the minimum id. This is LeetCode 196. MySQL won't let a subquery select from the table being deleted unless it's wrapped in a derived table.''', ["Amazon", "Paytm", "Oracle"]),

M("DBMS Indexing", '''In MySQL InnoDB, what does a secondary index leaf entry store?''',
["The full row", "The indexed column(s) plus the primary key value, which is used to look up the row in the clustered index",
 "A physical disk address", "Nothing but the indexed column"], 1,
'''InnoDB organizes the table as a clustered B+ tree on the PK. A secondary index stores the PK, so a non-covering query does a second lookup (often called a bookmark lookup). Covering indexes avoid it, and a large PK makes every secondary index larger.''', ["Oracle", "Intuit", "Flipkart"]),

M("Operating Systems", '''Which of these is NOT one of the four necessary conditions for deadlock?''',
["Mutual exclusion", "Hold and wait", "Preemption", "Circular wait"], 2,
'''The Coffman conditions are mutual exclusion, hold and wait, **no** preemption, and circular wait. Allowing preemption, meaning resources can be taken away, breaks deadlock, so it isn't a condition for it.''', ["Microsoft", "Oracle", "SAP"]),

M("Operating Systems", '''What is the purpose of the TLB (Translation Lookaside Buffer)?''',
["Storing swapped-out pages", "Caching recent virtual-to-physical page translations so that most memory accesses skip a page-table walk",
 "Buffering disk writes", "Scheduling threads"], 1,
'''Without a TLB, every memory access would need extra memory reads to walk the multi-level page table. TLB hit rates are usually above 99%. Context switches between processes may flush it, which is one reason process switches cost more.''', ["Microsoft", "Adobe"]),

M("Computer Networks", '''What is the main improvement of HTTP/2 over HTTP/1.1?''',
["It uses UDP", "It multiplexes many concurrent request/response streams over one TCP connection, using binary framing and HPACK header compression",
 "It removes the need for TLS", "It supports only GET requests"], 1,
'''HTTP/1.1 suffers from head-of-line blocking at the request level, so browsers open around 6 connections per host. HTTP/2 interleaves streams on one connection. TCP-level head-of-line blocking still exists, and HTTP/3 over QUIC fixes it.''', ["Google", "Atlassian"]),

M("REST / HTTP", '''A logged-in user calls an admin-only endpoint they aren't allowed to use. Which status code is correct?''',
["401 Unauthorized", "403 Forbidden", "404 Not Found", "400 Bad Request"], 1,
'''401 means unauthenticated: missing or invalid credentials. 403 means the user is authenticated but not authorized for this resource. Some APIs return 404 on purpose to hide that the resource exists.''', ["Paytm", "Salesforce", "Intuit"]),

M("System Design", '''You want to scale a Spring Boot service horizontally behind a load balancer, but it stores user sessions in memory. What's the cleanest fix?''',
["Sticky sessions forever", "Make the service stateless: move sessions to a shared store such as Redis (Spring Session) or use stateless JWTs",
 "Run only one instance", "Increase the heap size"], 1,
'''Stateless instances are interchangeable, so the load balancer can send any request anywhere and autoscaling or instance failures don't log users out. Sticky sessions work, but they cause uneven load and lose sessions when a node dies.''', ["Flipkart", "Walmart", "Swiggy"]),

M("System Design", '''A message broker guarantees **at-least-once** delivery. What must consumers do?''',
["Nothing", "Be idempotent: deduplicate by message or event ID, or make the operations naturally idempotent",
 "Commit offsets before processing", "Use only one partition"], 1,
'''At-least-once means duplicates will happen during retries and rebalances. Consumers should record processed IDs (for example in a unique-keyed table updated in the same transaction) or use upserts, so reprocessing doesn't double-apply effects.''', ["Razorpay", "PhonePe", "Uber"]),

M("DSA", '''Which sorting algorithm is both **stable** and **O(n log n) in the worst case**?''',
["Quick sort", "Heap sort", "Merge sort", "Selection sort"], 2,
'''Merge sort is stable and always O(n log n), at the cost of O(n) extra space. Quick sort degrades to O(n²) in the worst case and is unstable. Heap sort is O(n log n) but unstable. Java's `Arrays.sort` on objects uses TimSort, a stable merge-sort hybrid.''', ["Amazon", "Microsoft", "Adobe"]),

M("DSA", '''What is the most efficient way to find the k-th smallest element in a BST of height h?''',
["Collect all nodes into a list and sort it: O(n log n)", "An iterative in-order traversal that stops at the k-th visited node: O(h + k)",
 "BFS level order", "Always O(1)"], 1,
'''In-order traversal of a BST visits keys in sorted order, so you can stop after k pops from an explicit stack. If the tree is updated often, store subtree sizes in each node to get O(h) selection.''', ["Amazon", "Microsoft", "Uber"]),

M("Aptitude", '''A shopkeeper marks goods 40% above cost and then gives a 20% discount. What is the profit percentage?''',
["20%", "12%", "10%", "8%"], 1,
'''Take cost = 100. Marked price = 140. After the 20% discount the selling price is 140 × 0.8 = 112, so the profit is 12%. Shortcut: a + b + ab/100 = 40 − 20 − 8 = 12.''', ["Paytm", "Amazon"]),

M("Aptitude", '''A father is 4 times as old as his son. In 20 years, he'll be twice as old as his son. What is the father's current age?''',
["36", "40", "44", "48"], 1,
'''F = 4S and F + 20 = 2(S + 20). Substituting gives 4S + 20 = 2S + 40, so S = 10 and F = 40. Check: in 20 years they'll be 60 and 30.''', ["Oracle", "SAP"]),
]

coding = [
C("Rotting Oranges", "Medium", ["Amazon", "Microsoft", "Walmart", "Flipkart"], r'''
In an `m x n` grid, `0` is an empty cell, `1` is a fresh orange and `2` is a rotten orange. Every minute, any fresh orange next to a rotten one (up, down, left or right) becomes rotten. Return the minimum number of minutes until no fresh orange is left, or `-1` if that never happens.

**Example 1**
```
Input:  [[2,1,1],
         [1,1,0],
         [0,1,1]]
Output: 4
```
**Example 2**
```
Input:  [[2,1,1],
         [0,1,1],
         [1,0,1]]
Output: -1    // bottom-left orange is unreachable
```
**Constraints:** 1 ≤ m, n ≤ 10''',
["Start a BFS from all rotten oranges at once (multi-source BFS).",
 "Count the fresh oranges first. Each BFS level is one minute. If any fresh oranges remain at the end, return -1."],
r'''
import java.util.*;

class Solution {
    public int orangesRotting(int[][] grid) {
        int m = grid.length, n = grid[0].length, fresh = 0;
        Deque<int[]> queue = new ArrayDeque<>();
        for (int i = 0; i < m; i++)
            for (int j = 0; j < n; j++) {
                if (grid[i][j] == 2) queue.offer(new int[]{i, j});
                else if (grid[i][j] == 1) fresh++;
            }

        int minutes = 0;
        int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        while (!queue.isEmpty() && fresh > 0) {
            for (int size = queue.size(); size > 0; size--) {
                int[] cell = queue.poll();
                for (int[] d : dirs) {
                    int r = cell[0] + d[0], c = cell[1] + d[1];
                    if (r >= 0 && r < m && c >= 0 && c < n && grid[r][c] == 1) {
                        grid[r][c] = 2;
                        fresh--;
                        queue.offer(new int[]{r, c});
                    }
                }
            }
            minutes++;
        }
        return fresh == 0 ? minutes : -1;
    }
}''',
'''This is **multi-source BFS**. Every initially rotten orange goes into the queue at distance 0, so the rot spreads from all of them at the same time, and the BFS level count equals the elapsed minutes. Processing exactly `queue.size()` cells per round keeps the levels separate. Marking an orange rotten as it's enqueued stops it from being added twice. The loop also stops once `fresh` reaches 0, so we don't count an extra empty minute. If fresh oranges remain afterwards, they were unreachable. The same template solves "01 Matrix", "Walls and Gates" and "As Far from Land as Possible". Amazon and Walmart OAs reportedly use it often.''',
"O(m · n)", "O(m · n)", "https://leetcode.com/problems/rotting-oranges/"),

C("Search in Rotated Sorted Array", "Medium", ["Microsoft", "Amazon", "Adobe", "Paytm", "Google"], r'''
A sorted array of **distinct** integers was rotated at an unknown pivot, for example `[0,1,2,4,5,6,7]` became `[4,5,6,7,0,1,2]`. Given `target`, return its index, or `-1` if it isn't there, in **O(log n)** time.

**Example 1**
```
Input:  nums = [4,5,6,7,0,1,2], target = 0
Output: 4
```
**Example 2**
```
Input:  nums = [4,5,6,7,0,1,2], target = 3
Output: -1
```
**Constraints:** 1 ≤ n ≤ 5000, −10^4 ≤ nums[i], target ≤ 10^4''',
["At any mid, at least one of the two halves [lo..mid] or [mid..hi] is sorted.",
 "Work out which half is sorted, check whether the target is inside its range, and discard the other half."],
r'''
class Solution {
    public int search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = (lo + hi) >>> 1;
            if (nums[mid] == target) return mid;
            if (nums[lo] <= nums[mid]) {                       // left half sorted
                if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else {                                           // right half sorted
                if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1;
    }
}''',
'''Rotation breaks the global ordering, but every split point still leaves **one sorted half**. If `nums[lo] <= nums[mid]`, the left half has no break in it. Otherwise the right half is sorted. In a sorted half we can check with two comparisons whether the target is inside its range. If it is, search there, and if not, it must be in the other half. Each step halves the range, giving O(log n). The `<=` in `nums[lo] <= nums[mid]` handles the case lo == mid. Common follow-ups: the version **with duplicates** (LC 81), where `nums[lo] == nums[mid]` forces `lo++` and the worst case becomes O(n), and finding the rotation point (the minimum, LC 153).''',
"O(log n)", "O(1)", "https://leetcode.com/problems/search-in-rotated-sorted-array/"),

C("Next Permutation", "Medium", ["Google", "Adobe", "Goldman Sachs", "Microsoft", "Uber"], r'''
Rearrange `nums` **in place** into the lexicographically next greater permutation. If none exists because the array is in descending order, rearrange it into ascending order (the smallest permutation). Use only O(1) extra memory.

**Examples**
```
[1,2,3] -> [1,3,2]
[3,2,1] -> [1,2,3]
[1,1,5] -> [1,5,1]
[1,3,2] -> [2,1,3]
```
**Constraints:** 1 ≤ n ≤ 100, 0 ≤ nums[i] ≤ 100''',
["Scan from the right for the first index i where nums[i] < nums[i+1]. Everything after i is non-increasing.",
 "Swap nums[i] with the rightmost element greater than it, then reverse the suffix after i."],
r'''
class Solution {
    public void nextPermutation(int[] nums) {
        int i = nums.length - 2;
        while (i >= 0 && nums[i] >= nums[i + 1]) i--;     // find the pivot
        if (i >= 0) {
            int j = nums.length - 1;
            while (nums[j] <= nums[i]) j--;              // rightmost element > pivot
            swap(nums, i, j);
        }
        reverse(nums, i + 1, nums.length - 1);           // smallest suffix
    }

    private void swap(int[] a, int i, int j) {
        int t = a[i]; a[i] = a[j]; a[j] = t;
    }

    private void reverse(int[] a, int l, int r) {
        while (l < r) swap(a, l++, r--);
    }
}''',
'''The longest non-increasing suffix is already at its largest arrangement, so the next permutation has to change the element just before it, the **pivot** at index i. To increase it by as little as possible, swap it with the **smallest suffix element larger than it**. Because the suffix is non-increasing, that's the rightmost such element. After the swap the suffix is still non-increasing, so reversing it gives its smallest order. If there's no pivot, the whole array is descending, and reversing it all wraps around to the first permutation. Each step is linear, so the total is O(n) time and O(1) space. Interviewers often ask you to prove that the suffix stays sorted after the swap, and why `>=` and `<=` are needed for duplicates.''',
"O(n)", "O(1)", "https://leetcode.com/problems/next-permutation/"),

C("Largest Rectangle in Histogram", "Hard", ["Amazon", "Google", "Adobe", "Flipkart", "Microsoft"], r'''
Given `heights` of histogram bars, each 1 unit wide, return the area of the largest rectangle that fits inside the histogram.

**Example 1**
```
Input:  [2,1,5,6,2,3]
Output: 10      // bars 5 and 6, width 2
```
**Example 2**
```
Input:  [2,4]
Output: 4
```
**Constraints:** 1 ≤ n ≤ 10^5, 0 ≤ heights[i] ≤ 10^4''',
["For each bar, the largest rectangle using it as the shortest bar extends to the nearest smaller bar on each side.",
 "Use a monotonic increasing stack of indices. When a shorter bar arrives, pop and compute the area for each popped bar."],
r'''
import java.util.*;

class Solution {
    public int largestRectangleArea(int[] heights) {
        Deque<Integer> stack = new ArrayDeque<>();          // indices, heights increasing
        int best = 0, n = heights.length;
        for (int i = 0; i <= n; i++) {
            int h = (i == n) ? 0 : heights[i];              // sentinel flushes the stack
            while (!stack.isEmpty() && heights[stack.peek()] > h) {
                int height = heights[stack.pop()];
                int left = stack.isEmpty() ? -1 : stack.peek();   // previous smaller index
                best = Math.max(best, height * (i - left - 1));
            }
            stack.push(i);
        }
        return best;
    }
}''',
'''The stack holds bar indices in **increasing height order**. When bar `i` is shorter than the bar on top, that top bar has found its nearest smaller bar on the right, at `i`. Its nearest smaller bar on the left is the index now beneath it on the stack. The rectangle using that bar as the minimum height spans `i − left − 1` columns, so we compute its area when we pop it. A zero-height sentinel at `i = n` flushes the bars that are left. Every index is pushed and popped once, so the total is O(n). This monotonic stack is a core pattern. It powers "Maximal Rectangle" (run it on each row of a binary matrix), "Daily Temperatures" and "Sum of Subarray Minimums", which are common Hard follow-ups.''',
"O(n)", "O(n)", "https://leetcode.com/problems/largest-rectangle-in-histogram/"),
]

theory = [
T("HR: Tell me about yourself. (model answer for a 2-YOE Java developer)", '''Keep it to about 90 seconds and follow **present → past → future**:

*"I'm Raj, a backend-focused software engineer with two years of experience building Spring Boot microservices with MySQL, plus Angular on the front end. In my current role I own the order-management APIs. I reduced a slow reporting endpoint's response time from about 4 seconds to 600 ms by fixing N+1 queries and adding indexes, and I built a Kafka-based notification flow. Over the last few months I've been strengthening my DSA and system design, and I enjoy problems where correctness and scale both matter. That's why I'm excited about this role: product ownership, high-traffic systems, and engineers I can learn from."*

Tips: use **numbers**, mention **one or two projects**, tie the ending to **their** product, and don't recite your resume line by line.''', ["Amazon", "Flipkart", "Swiggy", "PhonePe"]),

T("HR: Why are you looking for a change?", '''Stay **positive and forward-looking**. Never criticize your current employer.

*"I've learned a lot in my current company: I shipped production features end to end and handled on-call. But most of our work is maintaining internal tools for a fixed set of clients, and the scale is limited. I want to work on a product used by millions, where performance, reliability and design decisions really matter, and where engineering quality is valued. I've been preparing seriously for this move by working on DSA, system design and deeper Spring and Kafka internals, and your team's work on [specific product or engineering blog post] is exactly the kind of challenge I'm looking for."*

Avoid saying "money" as the main reason, even if it's part of it. You can mention compensation alignment later, in the salary discussion. Keep the answer under a minute, and make sure it's consistent with what your resume says.''', ["Flipkart", "Paytm", "Myntra", "Meesho"]),

T("HR: What is your expected CTC? (targeting ~15 LPA)", '''**Research first**, using AmbitionBox, Glassdoor, Levels.fyi and your network, so you know the SDE-1/SDE-2 band at that company. **Try to let them name a number first**, and if you have to give one, give a **researched range** whose bottom is your real target.

*"Based on my research for this role and level in Bengaluru, and given my experience with Spring Boot microservices and Kafka in production, I'm looking for a fixed component in the range of 15 to 17 LPA. I'm flexible on the structure, and what matters most to me is the role and the growth. Could you share the band budgeted for this position?"*

Tips:
- Talk about **fixed pay** separately from variable pay, ESOPs and joining bonus.
- Don't inflate your current CTC. Companies verify it through payslips.
- A competing offer, if you have one, is your strongest lever. Mention it honestly.''', ["Flipkart", "Swiggy", "PhonePe", "Razorpay"]),

T("HR: They offer 12 LPA but you want 15 LPA. How do you negotiate?", '''Show you're keen, anchor the conversation on **value and market data**, and keep it **collaborative**:

*"Thank you, I'm genuinely excited about this team. Based on my research for SDE roles at this level, and the scope we discussed (owning payment-adjacent services and being on call), 12 is below what I was expecting. I'm also in the final stage at another company where the range is around 15. Is there flexibility to bring the fixed component closer to 15? If the fixed pay is capped, could we look at a joining bonus, more ESOPs, or an early compensation review at 6 months?"*

Principles:
1. Negotiate **after** the offer and before you sign. Be polite and specific.
2. Ask for a **number**, not "anything more".
3. Have backups ready: joining bonus, relocation, ESOP refresh, level change.
4. Never bluff about competing offers.
5. Once you agree, accept graciously and don't renegotiate.''', ["Amazon", "Flipkart", "Paytm", "CRED"]),

T("Behavioral: Describe the toughest production issue you handled. (STAR)", '''**Situation:** "On a sale day, our order API's p99 latency jumped from 300 ms to 8 seconds, and checkouts started timing out."

**Task:** "I was on call and had to bring it back quickly without losing orders."

**Action:** "Grafana showed the Hikari connection pool was exhausted. Thread dumps showed requests blocked on a new reporting query added the week before. It held a transaction open while it called an external tax API. I first scaled out the pods and reduced that endpoint's timeout to stop the bleeding. Then I moved the external call outside the @Transactional block, added a missing composite index, and set a statement timeout."

**Result:** "Latency was back under 400 ms within 40 minutes, with no lost orders. I wrote the RCA and added a pool-usage alert."

Use **one real story**, include numbers, and say "I", not "we".''', ["Amazon", "Uber", "Atlassian", "Walmart"]),

T("Behavioral: Tell me about a disagreement with a teammate or manager.", '''Show that you **disagree with data, commit to the decision, and keep the relationship intact** (Amazon calls this "Disagree and Commit").

*"My tech lead wanted to add a Redis cache in front of our product-details API to fix slow responses. I suspected the real cause was the query, so I profiled it and found an N+1 pattern plus a missing index. Rather than arguing in the meeting, I asked for a day and shared a short comparison: fixing the query brought p95 from 1.2 s to 180 ms with no new infrastructure, while the cache added invalidation complexity. He agreed to ship the query fix first and keep caching as a later option."*

Key points: stay **respectful**, base it on **evidence**, keep the **user or business goal** in focus, and show you'd commit fully even if the decision went the other way.''', ["Amazon", "Atlassian", "Microsoft", "Intuit"]),
]

save(14, "Final Mock + HR",
     "A final mixed mock across DSA, Java, Spring, SQL and CS fundamentals, plus model answers for the HR, behavioral and salary-negotiation rounds.",
     mcqs, coding, theory)
