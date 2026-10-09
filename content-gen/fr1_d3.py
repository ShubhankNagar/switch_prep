from fr1_common import M, C, T, build

mcqs = [
M("Java concurrency", '''`private volatile int count;` is incremented with `count++` by 4 threads, 1000 times each. What is guaranteed about the final value?''',
["Exactly 4000, because volatile makes ++ atomic", "At most 4000, and it may be less", "Always less than 4000", "Compilation error"], 1,
'''`volatile` guarantees visibility and ordering, but `count++` is a read-modify-write made of three steps. Two threads can read the same value and both write value + 1, so updates get lost. Use `AtomicInteger.incrementAndGet()`, `LongAdder` or a lock to make it exact.''',
["Flipkart", "PhonePe", "Goldman Sachs"]),

M("Java concurrency", '''What does this print when run from `main`?
```java
Thread t = new Thread(() ->
    System.out.print(Thread.currentThread().getName()), "worker");
t.run();
```''', ["worker", "main", "Thread-0", "Nothing; IllegalThreadStateException"], 1,
'''Calling `run()` directly is just an ordinary method call on the current thread, so it prints "main". Only `start()` creates a new thread of execution that then calls `run()`, and that would print "worker".''',
["Flipkart", "Myntra", "Oracle"]),

M("Java concurrency", '''What happens if you call `start()` twice on the same Thread object?''',
["The thread runs twice", "The second call is silently ignored", "IllegalThreadStateException is thrown", "A deadlock occurs"], 2,
'''A thread's lifecycle goes one way: NEW to RUNNABLE to TERMINATED. `start()` is only valid in the NEW state, so a second call throws `IllegalThreadStateException`. To run a task again, submit it to an ExecutorService or create a new Thread.''',
["Flipkart", "SAP"]),

M("Java concurrency", '''Calling `obj.wait()` outside a `synchronized(obj)` block results in…''',
["The thread waits normally", "IllegalMonitorStateException at runtime", "A compile-time error", "The call returns immediately"], 1,
'''`wait`, `notify` and `notifyAll` require the calling thread to own the object's monitor. Otherwise the JVM throws `IllegalMonitorStateException`. The compiler cannot check this. Always call wait inside a `while (!condition)` loop to handle spurious wakeups.''',
["Flipkart", "Goldman Sachs", "Oracle"]),

M("Java concurrency", '''What is the key difference between `Thread.sleep()` and `Object.wait()`?''',
["sleep releases the monitor lock; wait does not", "wait releases the monitor lock; sleep keeps any locks held",
 "Both release the lock", "Neither can be interrupted"], 1,
'''`wait()` releases the monitor and suspends until it is notified or times out, then reacquires the lock before returning. `sleep()` pauses the thread but keeps every lock it holds. Both throw `InterruptedException` if the thread is interrupted.''',
["Flipkart", "Myntra", "Paytm"]),

M("Operating systems", '''Which of these is NOT one of the four necessary (Coffman) conditions for deadlock?''',
["Mutual exclusion", "Hold and wait", "Circular wait", "Preemption of resources"], 3,
'''The four conditions are mutual exclusion, hold and wait, NO preemption, and circular wait. If resources can be preempted, the "no preemption" condition fails and deadlock cannot occur. A common prevention technique is breaking circular wait by always acquiring locks in a fixed global order.''',
["Flipkart", "Oracle", "Microsoft"]),

M("Java concurrency", '''How does `ConcurrentHashMap` in Java 8+ achieve thread-safe writes?''',
["One global lock on the whole map", "16 fixed Segment locks", "CAS for empty bins and synchronized on the first node of a non-empty bin",
 "Copy-on-write of the whole table"], 2,
'''Java 7 used segments. Java 8 removed them: inserting into an empty bin uses a lock-free CAS, and a collision locks only that bin's head node. Reads are mostly lock-free through volatile reads. Resizing is shared among threads. It allows neither null keys nor null values.''',
["Myntra", "Walmart", "Flipkart"]),

M("Java concurrency", '''Why can `Executors.newFixedThreadPool(10)` cause an OutOfMemoryError under heavy load?''',
["It creates unlimited threads", "Its LinkedBlockingQueue is unbounded, so queued tasks can grow without limit",
 "It never reuses threads", "It uses a SynchronousQueue"], 1,
'''A fixed pool caps the number of threads but queues extra tasks in an unbounded `LinkedBlockingQueue`. If producers outpace the workers, the queue grows until the heap runs out. In production, build a `ThreadPoolExecutor` with a bounded queue and a rejection policy such as `CallerRunsPolicy`.''',
["Flipkart", "Swiggy", "PhonePe"]),

M("Java concurrency", '''`getUser(id)` returns `CompletableFuture<User>` and `getOrders(user)` returns `CompletableFuture<List<Order>>`. Which call chains them without producing a nested `CompletableFuture<CompletableFuture<...>>`?''',
["thenApply", "thenAccept", "thenCompose", "thenRun"], 2,
'''`thenCompose` is the flatMap of futures: it takes a function that returns another CompletableFuture and flattens the result. `thenApply` would wrap that result again, giving a nested future. Use `thenCombine` or `allOf` to run independent futures in parallel.''',
["Myntra", "Swiggy", "Flipkart"]),

M("Java concurrency", '''What mechanism does `AtomicInteger.incrementAndGet()` mainly rely on?''',
["synchronized blocks", "Compare-And-Swap (CAS) CPU instructions in a retry loop", "ReentrantLock", "Thread priorities"], 1,
'''Atomic classes use hardware CAS: read the current value, compute the new one, and swap only if the value is unchanged, otherwise retry. This is lock-free and fast when contention is low. Under very high contention, `LongAdder` scales better by spreading updates across cells.''',
["Flipkart", "PhonePe"]),

M("Java concurrency", '''Which statement correctly distinguishes `CountDownLatch` from `CyclicBarrier`?''',
["CountDownLatch can be reset and reused; CyclicBarrier cannot", "CyclicBarrier can be reused after all parties arrive; CountDownLatch is one-shot",
 "Both are reusable", "CountDownLatch requires all waiting threads to call countDown"], 1,
'''A latch counts down once: threads wait until the count reaches zero, and it can never be reset. A barrier makes a fixed number of parties wait for each other, can run a barrier action, and then resets for the next round. Use a latch for "start after N services are ready".''',
["Flipkart", "Goldman Sachs"]),

M("Java concurrency", '''Thread T1 calls a `synchronized` instance method on object `x`, while T2 calls a `static synchronized` method of the same class. Can they run at the same time?''',
["No, both lock the class", "Yes, because they lock different monitors: the instance x and the Class object",
 "Only if x is null", "No, static methods block all instance methods"], 1,
'''A synchronized instance method locks `this`, while a static synchronized method locks `ClassName.class`. These are different monitors, so the two threads do not block each other. If both methods touch the same shared static data, that data is not protected.''',
["Myntra", "Oracle", "Paytm"]),

M("Spring Boot", '''A `@Async` method `sendEmail()` is called from another method INSIDE the same bean. What happens?''',
["It runs asynchronously on the task executor", "It runs synchronously, because the call bypasses the Spring proxy",
 "Spring throws BeanCreationException", "It runs twice"], 1,
'''`@Async`, like `@Transactional`, works through a proxy around the bean. A call through `this` never goes through the proxy, so the method runs on the caller's thread. Move the method to another bean, or inject the proxy. `@EnableAsync` must also be present.''',
["Flipkart", "Swiggy", "Razorpay"]),

M("Dynamic programming", '''What is the time complexity of the standard DP for 0/1 Knapsack with n items and capacity W, and how is it classified?''',
["O(2^n), exponential", "O(n x W), pseudo-polynomial", "O(n log n), polynomial", "O(W), linear"], 1,
'''The table has n x W cells, each filled in O(1). It is called pseudo-polynomial because W is a numeric value: its input size is log W bits, so the running time is exponential in the input length. Space can be reduced to O(W) by iterating capacity from high to low.''',
["Flipkart", "Myntra", "Amazon"]),

M("Dynamic programming", '''You can climb 1 or 2 steps at a time. In how many distinct ways can you climb 5 steps?''',
["5", "8", "10", "13"], 1,
'''ways(n) = ways(n-1) + ways(n-2), with ways(1) = 1 and ways(2) = 2. That gives 1, 2, 3, 5, 8, so ways(5) = 8. It is the Fibonacci sequence shifted by one, solvable in O(n) time and O(1) space.''',
["Flipkart", "Adobe", "Amazon"]),

M("Dynamic programming", '''What is the best known time complexity for Longest Increasing Subsequence (length only)?''',
["O(n^2)", "O(n log n)", "O(n)", "O(2^n)"], 1,
'''Keep `tails[i]`, the smallest possible tail of an increasing subsequence of length i + 1. For each number, binary search for its position in tails and replace that entry, or append if it is larger than all tails. That gives n binary searches, so O(n log n). The basic DP is O(n^2).''',
["Flipkart", "Google", "Myntra"]),

M("Graphs", '''Why can Dijkstra's algorithm give wrong answers with negative edge weights?''',
["It cannot handle cycles", "It finalises a node when popped, assuming later paths cannot be cheaper, which negative edges violate",
 "It only works on trees", "Priority queues cannot store negative numbers"], 1,
'''Dijkstra's greedy step assumes that adding edges never decreases a path's cost. A negative edge found later could make an already settled node cheaper. Use Bellman-Ford, O(VE), which also detects negative cycles, or SPFA.''',
["Flipkart", "Uber", "Swiggy"]),

M("Graphs", '''In Kahn's algorithm for topological sort, how do you detect that the directed graph has a cycle?''',
["The queue becomes empty immediately", "The number of nodes processed is less than V", "Some node has in-degree 0", "The result contains duplicates"], 1,
'''Nodes on a cycle never reach in-degree 0, so they are never enqueued. If fewer than V nodes appear in the output when the queue empties, a cycle exists. That is exactly the "Course Schedule" check.''',
["Flipkart", "Swiggy", "Amazon"]),

M("Graphs", '''Union-Find with BOTH path compression and union by rank performs each operation in…''',
["O(log n) worst case exactly", "Amortised O(α(n)), the inverse Ackermann function, effectively constant", "O(n)", "O(1) strictly"], 1,
'''Using both optimisations gives an amortised cost of O(α(n)) per operation, and α(n) is at most 4 for any practical n. It is used in Kruskal's MST, counting connected components, redundant connection and accounts merge.''',
["Flipkart", "Google"]),

M("Aptitude", '''A bag has 3 red and 5 blue balls. Two balls are drawn without replacement. What is the probability that both are red?''',
["9/64", "3/28", "3/8", "1/4"], 1,
'''Favourable outcomes: C(3,2) = 3. Total outcomes: C(8,2) = 28. So P = 3/28. Equivalently, (3/8) x (2/7) = 6/56 = 3/28. The answer 9/64 would be correct only if the first ball were put back before the second draw.''',
["Myntra", "Goldman Sachs", "Oracle"]),
]

coding = [
C("Word Break", "Medium", ["Flipkart", "Myntra", "Amazon", "Google"],
'''Given a string `s` and a dictionary `wordDict`, return `true` if `s` can be split into a sequence of one or more dictionary words. A word may be used multiple times.

**Example 1**
```
Input:  s = "leetcode", wordDict = ["leet","code"]
Output: true
```
**Example 2**
```
Input:  s = "catsandog", wordDict = ["cats","dog","sand","and","cat"]
Output: false
```
**Constraints**
- 1 <= s.length <= 300
- 1 <= wordDict.length <= 1000, words up to 20 chars''',
["dp[i] = can the prefix s[0..i) be segmented?",
 "dp[i] is true if some j < i has dp[j] true and s[j..i) in the dictionary. Limit j by the max word length."],
r'''
import java.util.*;

class Solution {
    public boolean wordBreak(String s, List<String> wordDict) {
        Set<String> dict = new HashSet<>(wordDict);
        int maxLen = 0;
        for (String w : wordDict) maxLen = Math.max(maxLen, w.length());
        boolean[] dp = new boolean[s.length() + 1];
        dp[0] = true;                                   // empty prefix
        for (int i = 1; i <= s.length(); i++) {
            for (int j = i - 1; j >= Math.max(0, i - maxLen); j--) {
                if (dp[j] && dict.contains(s.substring(j, i))) {
                    dp[i] = true;
                    break;
                }
            }
        }
        return dp[s.length()];
    }
}
''',
'''Plain recursion re-checks the same suffixes exponentially many times, so memoise on the prefix length. `dp[i]` is true when the first i characters can be split into dictionary words. To compute it, try every possible last word `s[j..i)`. If `dp[j]` is true and that word is in the set, then `dp[i]` is true. Bounding j by the longest dictionary word removes needless substring checks. The follow-up "Word Break II" (return all sentences) is a DFS with memoisation over start indices. For a large dictionary, a Trie lets you stop extending j as soon as no word matches the current prefix.''',
"O(n * L * L) where L = max word length (substring + hash)", "O(n + dictionary size)", "https://leetcode.com/problems/word-break/"),

C("Rotting Oranges", "Medium", ["Flipkart", "Amazon", "Myntra", "Microsoft"],
'''In an m x n grid, each cell is 0 (empty), 1 (fresh orange) or 2 (rotten orange). Every minute, any fresh orange next to a rotten one (up, down, left or right) becomes rotten. Return the minimum number of minutes until no fresh orange is left, or -1 if that can never happen.

**Example 1**
```
Input:  [[2,1,1],[1,1,0],[0,1,1]]
Output: 4
```
**Example 2**
```
Input:  [[2,1,1],[0,1,1],[1,0,1]]
Output: -1   // bottom-left orange can never rot
```
**Constraints**
- 1 <= m, n <= 10''',
["All initially rotten oranges spread at the same time, so start a BFS from ALL of them together.",
 "Process the queue level by level; each level is one minute. Count fresh oranges to detect -1."],
r'''
import java.util.*;

class Solution {
    public int orangesRotting(int[][] grid) {
        int m = grid.length, n = grid[0].length, fresh = 0;
        Deque<int[]> q = new ArrayDeque<>();
        for (int i = 0; i < m; i++)
            for (int j = 0; j < n; j++) {
                if (grid[i][j] == 2) q.offer(new int[]{i, j});
                else if (grid[i][j] == 1) fresh++;
            }
        int[][] dirs = {{1,0},{-1,0},{0,1},{0,-1}};
        int minutes = 0;
        while (!q.isEmpty() && fresh > 0) {
            for (int size = q.size(); size > 0; size--) {
                int[] cell = q.poll();
                for (int[] d : dirs) {
                    int r = cell[0] + d[0], c = cell[1] + d[1];
                    if (r >= 0 && r < m && c >= 0 && c < n && grid[r][c] == 1) {
                        grid[r][c] = 2;
                        fresh--;
                        q.offer(new int[]{r, c});
                    }
                }
            }
            minutes++;
        }
        return fresh == 0 ? minutes : -1;
    }
}
''',
'''This is a multi-source BFS. All rotten oranges go into the queue first, because they spread at the same time. Each BFS level is one minute, during which the current rotten oranges infect their fresh neighbours. Mark a neighbour as rotten when you enqueue it, so it is never added twice. A `fresh` counter avoids a second scan at the end and also stops the loop as soon as nothing fresh is left, which avoids counting an extra minute. If fresh oranges remain once the queue empties, they are unreachable and the answer is -1. The same pattern solves "walls and gates" and "distance to nearest 0".''',
"O(m * n)", "O(m * n) for the queue", "https://leetcode.com/problems/rotting-oranges/"),

C("Course Schedule II", "Medium", ["Flipkart", "Swiggy", "Amazon", "Uber"],
'''There are `numCourses` courses labelled 0 to numCourses-1. Each `prerequisites[i] = [a, b]` means you must take course `b` before course `a`. Return any valid order in which you can take all courses, or an empty array if no such order exists.

**Example**
```
Input:  numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]
Output: [0,1,2,3]  (or [0,2,1,3])

Input:  numCourses = 2, prerequisites = [[1,0],[0,1]]
Output: []         // cycle
```
**Constraints**
- 1 <= numCourses <= 2000
- 0 <= prerequisites.length <= numCourses * (numCourses - 1)''',
["Model it as a directed graph b -> a and look for a topological order.",
 "Kahn's BFS: start from courses with in-degree 0; if you cannot output all courses, there is a cycle."],
r'''
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
            int c = q.poll();
            order[idx++] = c;
            for (int next : adj.get(c)) {
                if (--indeg[next] == 0) q.offer(next);
            }
        }
        return idx == numCourses ? order : new int[0];
    }
}
''',
'''Prerequisites form a directed graph, and a valid schedule is a topological ordering, which exists only if the graph has no cycle. Kahn's algorithm repeatedly takes a course with no remaining prerequisites (in-degree 0), adds it to the order, and lowers the in-degree of the courses that depend on it. Courses on a cycle never reach in-degree 0, so if fewer than `numCourses` courses get output, return an empty array. A DFS with three colours (unvisited, visiting, done) also works: reverse the post-order, and treat a back edge to a "visiting" node as a cycle. Mention real uses such as build systems, task schedulers with dependencies, and Spring bean initialisation order.''',
"O(V + E)", "O(V + E)", "https://leetcode.com/problems/course-schedule-ii/"),

C("Edit Distance", "Hard", ["Flipkart", "Google", "Amazon", "Microsoft"],
'''Given two strings `word1` and `word2`, return the minimum number of operations needed to turn word1 into word2. The allowed operations are inserting a character, deleting a character, and replacing a character.

**Example**
```
Input:  word1 = "horse", word2 = "ros"
Output: 3   // horse -> rorse (replace h) -> rose (delete r) -> ros (delete e)

Input:  word1 = "intention", word2 = "execution"
Output: 5
```
**Constraints**
- 0 <= word1.length, word2.length <= 500
- lowercase English letters''',
["dp[i][j] = min operations to convert the first i chars of word1 into the first j chars of word2.",
 "If the last chars match, take dp[i-1][j-1]; otherwise 1 + min(insert dp[i][j-1], delete dp[i-1][j], replace dp[i-1][j-1])."],
r'''
class Solution {
    public int minDistance(String a, String b) {
        int m = a.length(), n = b.length();
        int[] prev = new int[n + 1], cur = new int[n + 1];
        for (int j = 0; j <= n; j++) prev[j] = j;          // insert j chars
        for (int i = 1; i <= m; i++) {
            cur[0] = i;                                    // delete i chars
            for (int j = 1; j <= n; j++) {
                if (a.charAt(i - 1) == b.charAt(j - 1)) {
                    cur[j] = prev[j - 1];
                } else {
                    cur[j] = 1 + Math.min(prev[j - 1],     // replace
                                 Math.min(prev[j],         // delete
                                          cur[j - 1]));    // insert
                }
            }
            int[] t = prev; prev = cur; cur = t;
        }
        return prev[n];
    }
}
''',
'''This is the classic Levenshtein DP. The base cases are converting a prefix to or from an empty string, which costs its length. For each pair of prefixes: if the last characters match, no operation is needed, so take the diagonal value. Otherwise pay 1 and take the cheapest of replace (diagonal), delete from word1 (the cell above) and insert into word1 (the cell to the left). Each row depends only on the previous row, so two arrays reduce the space to O(n). Interviewers often ask you to explain the recurrence before coding, and may follow up by asking you to reconstruct the actual operations, which needs the full 2D table and a backtrack.''',
"O(m * n)", "O(n) with rolling arrays", "https://leetcode.com/problems/edit-distance/"),
]

theory = [
T("synchronized vs ReentrantLock: what does ReentrantLock add?",
'''Both give mutual exclusion and reentrancy, and both establish happens-before. **synchronized** is built into the language: the lock is released automatically even on exceptions, and the JVM optimises it well. However, it cannot be interrupted while waiting, has no timeout, is always non-fair, and supports only one wait-set per monitor. **ReentrantLock** adds `tryLock()` and `tryLock(timeout)` to avoid deadlocks, `lockInterruptibly()`, an optional fairness policy, multiple `Condition` objects (for example separate notFull and notEmpty conditions in a bounded buffer), and introspection such as `isLocked`. The cost is that you must call `unlock()` in a `finally` block. For read-heavy data, use `ReentrantReadWriteLock` or `StampedLock`. Default to synchronized, and switch to ReentrantLock when you need one of these features.''',
["Flipkart", "PhonePe", "Myntra", "Goldman Sachs"]),

T("What does the volatile keyword guarantee? Explain happens-before.",
'''A `volatile` field guarantees **visibility**: a write is flushed so other threads see the latest value instead of a cached copy. It also guarantees **ordering**: the compiler and CPU cannot reorder operations across the volatile read or write. Under the Java Memory Model, a write to a volatile variable *happens-before* every later read of it. So everything a thread did before writing the volatile is visible to a thread that later reads it. Typical uses are a `volatile boolean running` stop flag, and safe publication in double-checked locking. volatile does **not** make compound actions such as `count++` or check-then-act atomic; those need Atomic classes or locks. Other happens-before edges are: unlocking a monitor before the next lock of it, `Thread.start()`, `Thread.join()`, and writes to final fields in a constructor.''',
["Flipkart", "Goldman Sachs", "Microsoft"]),

T("Explain ThreadPoolExecutor's parameters. How would you size a thread pool?",
'''`ThreadPoolExecutor(corePoolSize, maximumPoolSize, keepAliveTime, unit, workQueue, threadFactory, rejectionHandler)`. A new task gets a new thread until there are core threads. After that, tasks are queued. Only when the queue is full are extra threads created, up to the maximum. When even that is full, the rejection policy runs (Abort, CallerRuns, Discard or DiscardOldest). Idle threads above core are removed after the keep-alive time. **Sizing:** for CPU-bound work, use about the number of cores (+1). For I/O-bound work, use cores x (1 + wait time / compute time). For example, if calls spend 90% waiting on 8 cores, about 80 threads. Always use a bounded queue, name threads with a ThreadFactory for easier debugging, and watch the queue depth. In Spring, configure a `ThreadPoolTaskExecutor` bean for `@Async`. With Java 21, virtual threads change sizing for blocking I/O.''',
["Flipkart", "Swiggy", "Myntra", "Uber"]),

T("How does ConcurrentHashMap differ from Hashtable and Collections.synchronizedMap?",
'''`Hashtable` and `synchronizedMap` wrap every method in one lock on the whole map, so only one thread can work on it at a time. They also need external locking for iteration and for compound operations. `ConcurrentHashMap` (Java 8+) uses CAS to insert into empty bins and `synchronized` only on the head node of a single bin. Reads are almost always lock-free, so many threads can read and write different bins at once. Its iterators are weakly consistent: they never throw `ConcurrentModificationException`, but they may not reflect the latest updates. It offers atomic compound operations, `putIfAbsent`, `computeIfAbsent`, `merge` and `compute`, which you should use instead of get-then-put. It rejects null keys and values, because a null return from `get` would be ambiguous under concurrency. `size()` is an estimate under concurrent updates. Example: `map.merge(word, 1, Integer::sum)` for thread-safe counting.''',
["Myntra", "Walmart", "Flipkart", "Paytm"]),

T("What is a deadlock? How would you detect and prevent it in a Java application?",
'''A deadlock happens when two or more threads each hold a lock and wait for a lock held by another, so none of them can proceed. Example: T1 locks account A and then waits for B, while T2 locks B and then waits for A, in two crossing money transfers. **Detection:** take a thread dump (`jstack <pid>` or VisualVM), which reports "Found one Java-level deadlock" along with the lock owners. You can also check `ThreadMXBean.findDeadlockedThreads()` programmatically. **Prevention:** acquire locks in a consistent global order (for example, by lower account ID first); use `tryLock` with a timeout and back off; keep critical sections small and never call external services while holding a lock; prefer higher-level concurrency utilities. In databases, deadlocks also happen between transactions. MySQL InnoDB detects them and rolls back one transaction, so the application should retry.''',
["Flipkart", "Oracle", "Goldman Sachs"]),

T("How would you call three downstream services in parallel and combine the results in Spring Boot?",
'''Use `CompletableFuture` with a dedicated bounded executor: `var u = supplyAsync(() -> userClient.get(id), ioPool); var o = supplyAsync(() -> orderClient.list(id), ioPool); var r = supplyAsync(() -> recoClient.get(id), ioPool);` and then `CompletableFuture.allOf(u, o, r).join()` and build the response from `u.join()`, `o.join()` and `r.join()`. Total latency becomes roughly the slowest call instead of the sum of all three. Add `orTimeout(...)` per call and `exceptionally(...)` to fall back to defaults, so one slow dependency, such as recommendations, degrades gracefully instead of failing the page. Do not use the common ForkJoinPool for blocking I/O. Pass MDC and trace context to the worker threads. For resilience, wrap the calls with Resilience4j circuit breakers. With WebFlux, use `Mono.zip` for the same effect.''',
["Myntra", "Swiggy", "Flipkart", "Zomato"]),
]

DAY = build(3, "Flipkart & Myntra", "Dynamic programming and graph problems from Flipkart and Myntra PS/DS rounds, plus Java concurrency MCQs.", mcqs, coding, theory)
