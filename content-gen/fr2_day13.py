from fr2_common import M, C, T, save

mcqs = [
M("Java Output", r'''
What does this print?
```java
static int f() { int x = 1; try { return x; } finally { x = 5; } }
static int g() { try { throw new RuntimeException(); } finally { return 2; } }

System.out.println(f() + " " + g());
```''', ["5 2", "1 2", "1 then RuntimeException", "5 then RuntimeException"], 1,
'''In `f`, the value 1 is saved for return before `finally` runs, and changing the local `x` afterwards doesn't affect it. In `g`, a `return` inside finally throws away the pending exception, which is why that style is discouraged. The output is 1 2.''', ["Goldman Sachs", "Adobe", "Oracle"]),

M("Java Output", r'''
What does this print?
```java
System.out.println('a' + 'b' + "c" + 'd' + 1);
```''', ["abcd1", "195cd1", "195c100", "ab c d 1"], 1,
'''Evaluation runs left to right. `'a' + 'b'` is int addition, 97 + 98 = 195. Adding "c" switches to string concatenation, giving "195c", then 'd' and 1 are appended as text. The result is 195cd1.''', ["JP Morgan", "SAP"]),

M("Java Output", r'''
What does this print?
```java
class P { static { System.out.print("PS "); } { System.out.print("PI "); } P() { System.out.print("PC "); } }
class C extends P { static { System.out.print("CS "); } { System.out.print("CI "); } C() { System.out.print("CC "); } }

new C(); new C();
```''', ["PS PI PC CS CI CC PS PI PC CS CI CC", "PS CS PI PC CI CC PI PC CI CC", "CS PS CI CC PI PC CI CC PI PC", "PS CS PI CI PC CC PI CI PC CC"], 1,
'''Static blocks run once, at class initialization, parent first. For each object, the parent's instance initializer and constructor run before the child's. The second `new C()` skips the static blocks.''', ["Goldman Sachs", "Oracle", "Adobe"]),

M("Java Output", r'''
What does this print?
```java
List<Integer> l = new ArrayList<>(List.of(1, 2, 3));
for (Integer x : l) if (x == 2) l.remove(x);
System.out.println(l);
```''', ["ConcurrentModificationException", "[1, 3]", "[1, 2]", "[2, 3]"], 1,
'''`remove(x)` takes an Integer, so it removes the object 2, not index 2. Size drops to 2 and the cursor is also 2, so `hasNext()` returns false and the loop exits before `next()` can check modCount. Removing any other element here would throw CME.''', ["Microsoft", "Adobe"]),

M("Java Output", r'''
What does this print?
```java
Thread t = new Thread(() -> System.out.print(Thread.currentThread().getName() + " "));
t.setName("worker");
t.run();
t.start();
t.join();
```''', ["worker worker", "main worker", "worker main", "IllegalThreadStateException"], 1,
'''`run()` is an ordinary method call, so it executes on the calling thread, `main`. `start()` creates a new thread called "worker". Calling `start()` a second time on the same thread would throw IllegalThreadStateException.''', ["Goldman Sachs", "JP Morgan"]),

M("SQL", r'''
`emp(id, name, dept_id)` contains (1,'A',10), (2,'B',20), (3,'C',NULL). `dept(id, name)` contains (10,'Eng'), (30,'HR'). What does this return?
```sql
SELECT COUNT(*) FROM emp e
LEFT JOIN dept d ON e.dept_id = d.id
WHERE d.name <> 'HR';
```''', ["3", "2", "1", "0"], 2,
'''The LEFT JOIN produces A–Eng, B–NULL and C–NULL. `NULL <> 'HR'` evaluates to UNKNOWN, so WHERE drops those rows and only A is left. Filtering the right table in WHERE effectively turns the LEFT JOIN into an inner join. Move the condition into ON, or add `OR d.name IS NULL`.''', ["Goldman Sachs", "Amazon", "Intuit"]),

M("SQL", r'''
Table `t(v)` holds 1, NULL, 2, NULL. What does this return?
```sql
SELECT COUNT(*), COUNT(v), AVG(v) FROM t;
```''', ["4, 4, 0.75", "4, 2, 1.5", "2, 2, 1.5", "4, 2, 0.75"], 1,
'''`COUNT(*)` counts every row, giving 4. `COUNT(v)` skips NULLs, giving 2. `AVG` also ignores NULLs, so it's (1 + 2)/2 = 1.5, not 3/4. Use `COALESCE(v, 0)` if NULLs should count as zero.''', ["Oracle", "SAP", "Walmart"]),

M("DBMS", '''Relation R(A, B, C) has the functional dependencies A → B and B → C, and A is the only candidate key. What is the highest normal form R satisfies?''',
["1NF", "2NF", "3NF", "BCNF"], 1,
'''The key is a single attribute, so partial dependencies are impossible and R is in 2NF. But A → B → C is a transitive dependency of a non-prime attribute on the key, which breaks 3NF. Decompose into (A, B) and (B, C).''', ["Oracle", "Amazon", "Goldman Sachs"]),

M("Operating Systems", r'''
How many times is "hi" printed?
```c
int main() {
    fork(); fork(); fork();
    printf("hi\n");
}
```''', ["3", "6", "7", "8"], 3,
'''Each `fork()` doubles the number of processes: 1 → 2 → 4 → 8. All 8 processes, the original plus 7 children, reach printf. In general, n sequential forks give 2^n processes.''', ["Microsoft", "Adobe", "Oracle"]),

M("Operating Systems", '''Which CPU scheduling algorithm minimizes average waiting time when burst times are known, but can starve long jobs?''',
["FCFS", "Round Robin", "Shortest Job First (SJF/SRTF)", "Multilevel Feedback Queue with aging"], 2,
'''SJF is provably optimal for average waiting time, but a steady stream of short jobs can delay long jobs indefinitely. Aging, which raises priority over time, fixes starvation. Round Robin is fair but has higher average waiting time.''', ["Oracle", "SAP"]),

M("Computer Networks", '''How many usable host addresses are in a /26 IPv4 subnet?''',
["64", "62", "30", "126"], 1,
'''A /26 leaves 32 − 26 = 6 host bits, which is 2^6 = 64 addresses. Subtract the network and broadcast addresses to get 62 usable hosts. For comparison, a /24 has 254 usable and a /30 has 2.''', ["Oracle", "SAP", "ServiceNow"]),

M("Computer Networks", '''After you type a URL and press Enter, what is the correct order of events for a first HTTPS visit?''',
["TCP handshake → DNS → TLS → HTTP", "DNS resolution → TCP handshake → TLS handshake → HTTP request",
 "TLS → DNS → TCP → HTTP", "HTTP request → DNS → TCP → TLS"], 1,
'''The browser needs the IP first (from the browser, OS or resolver cache, then recursive DNS). Then comes the TCP 3-way handshake, the TLS handshake (certificate and keys), and finally the HTTP request. HTTP/3 merges transport and TLS over QUIC.''', ["Google", "Amazon", "Atlassian"]),

M("System Design", '''Which statement about a Bloom filter is TRUE?''',
["It can return false negatives", "It can return false positives but never false negatives",
 "It stores the actual elements", "It supports deletion by default"], 1,
'''A Bloom filter sets k hash bits per element. If any bit is 0, the element was definitely never added. If all bits are 1, it might have been. That makes it useful for cheap "definitely not present" checks, such as skipping disk reads in LSM trees or checking whether a username is taken. Counting Bloom filters add deletion support.''', ["Google", "Atlassian", "Uber"]),

M("System Design", '''A user updates their profile, refreshes, and sees the old data, because reads go to an asynchronous read replica. What is this problem called, and what is a common fix?''',
["Phantom read. Use SERIALIZABLE", "A read-your-writes violation caused by replication lag. Route that user's reads to the primary for a short time after a write, or use session or version tokens",
 "A deadlock. Add retries", "Cache poisoning. Clear the CDN"], 1,
'''Asynchronous replication means replicas lag behind the primary. To get read-your-writes consistency, pin a user's reads to the primary for a few seconds after a write, or only read from a replica that has reached the write's LSN/GTID.''', ["Atlassian", "Uber", "Flipkart"]),

M("DSA Complexity", r'''
What is the time complexity?
```java
for (int i = 1; i < n; i *= 2)
    for (int j = 0; j < i; j++)
        work();
```''', ["O(n log n)", "O(n)", "O(log n)", "O(n²)"], 1,
'''The inner loop runs 1 + 2 + 4 + … + 2^k times, where 2^k < n. That geometric series adds up to less than 2n, so the total is O(n). It's a classic trap, because the outer loop being O(log n) makes O(n log n) look right.''', ["Goldman Sachs", "Microsoft"]),

M("DSA Complexity", '''Solve the recurrence T(n) = 2T(n/2) + n log n.''',
["Θ(n log n)", "Θ(n log² n)", "Θ(n²)", "Θ(n)"], 1,
'''n^(log₂2) = n, and f(n) = n log n is larger than n only by a log factor. That's the extended Master theorem case 2 with k = 1, which gives Θ(n log^(k+1) n) = Θ(n log² n). A recursion tree confirms it: each of the log n levels costs about n log n.''', ["Google", "Goldman Sachs"]),

M("Java Output", r'''
What does this print?
```java
record P(int x) {}
class Q { int x; Q(int x) { this.x = x; } }

Set<Object> s = new HashSet<>();
s.add(new P(1)); s.add(new P(1));
s.add(new Q(1)); s.add(new Q(1));
System.out.println(s.size());
```''', ["2", "3", "4", "1"], 1,
'''Records automatically get value-based `equals` and `hashCode`, so the two `P(1)` objects are duplicates. `Q` inherits identity equality from Object, so both `Q` objects stay. That's 1 + 2 = 3.''', ["Oracle", "SAP", "Atlassian"]),

M("JVM", '''What is the default garbage collector for server-class machines in JDK 17?''',
["Serial GC", "Parallel GC", "G1 GC", "ZGC"], 2,
'''G1 has been the default since JDK 9. It splits the heap into regions and collects the regions with the most garbage first, aiming for a pause-time goal (`-XX:MaxGCPauseMillis`, 200 ms by default). ZGC and Shenandoah are low-latency options you turn on explicitly.''', ["Oracle", "SAP", "Goldman Sachs"]),

M("Aptitude", '''Two trains, 120 m and 80 m long, run in opposite directions at 54 km/h and 36 km/h. How long do they take to pass each other completely?''',
["10 s", "8 s", "12 s", "20 s"], 1,
'''Their relative speed is 54 + 36 = 90 km/h, which is 25 m/s. The distance to cover is the sum of their lengths, 200 m. Time = 200 / 25 = 8 seconds.''', ["Goldman Sachs", "JP Morgan"]),

M("Aptitude", '''Find the next term: 3, 10, 29, 66, 127, ?''',
["196", "216", "218", "225"], 2,
'''Each term is n³ + 2: 1+2, 8+2, 27+2, 64+2, 125+2. The next one is 6³ + 2 = 218. You can also see it from the differences 7, 19, 37, 61, 91, whose second differences grow by 6 each time.''', ["JP Morgan", "Goldman Sachs"]),
]

coding = [
C("Median of Two Sorted Arrays", "Hard", ["Google", "Microsoft", "Goldman Sachs", "Adobe", "Amazon"], r'''
Given two sorted arrays `nums1` (size m) and `nums2` (size n), return the median of all their elements combined. The expected time complexity is **O(log(min(m, n)))**.

**Example 1**
```
Input:  nums1 = [1,3], nums2 = [2]
Output: 2.0
```
**Example 2**
```
Input:  nums1 = [1,2], nums2 = [3,4]
Output: 2.5
```
**Constraints:** 0 ≤ m, n ≤ 1000, 1 ≤ m + n ≤ 2000, −10^6 ≤ values ≤ 10^6''',
["Binary search on how many elements to take from the smaller array for the combined left half.",
 "A partition (i, j) is valid when maxLeft1 ≤ minRight2 and maxLeft2 ≤ minRight1. Use ±infinity at the array ends."],
r'''
class Solution {
    public double findMedianSortedArrays(int[] a, int[] b) {
        if (a.length > b.length) return findMedianSortedArrays(b, a);   // search smaller
        int m = a.length, n = b.length;
        int half = (m + n + 1) / 2;
        int lo = 0, hi = m;
        while (lo <= hi) {
            int i = (lo + hi) >>> 1;          // elements taken from a
            int j = half - i;                 // elements taken from b
            int aLeft = i == 0 ? Integer.MIN_VALUE : a[i - 1];
            int aRight = i == m ? Integer.MAX_VALUE : a[i];
            int bLeft = j == 0 ? Integer.MIN_VALUE : b[j - 1];
            int bRight = j == n ? Integer.MAX_VALUE : b[j];

            if (aLeft <= bRight && bLeft <= aRight) {
                if (((m + n) & 1) == 1) return Math.max(aLeft, bLeft);
                return (Math.max(aLeft, bLeft) + (double) Math.min(aRight, bRight)) / 2.0;
            } else if (aLeft > bRight) {
                hi = i - 1;                   // took too many from a
            } else {
                lo = i + 1;                   // took too few from a
            }
        }
        throw new IllegalArgumentException("Input arrays not sorted");
    }
}''',
'''Instead of merging, we look for a **partition** that splits the combined elements into a left half and a right half, with every left element ≤ every right element. If we take `i` elements from the smaller array, the other array must contribute `j = half − i`, so the only real choice is `i`. Binary search adjusts it. If `a[i-1] > b[j]` we took too many from `a`, and if `b[j-1] > a[i]` we took too few. Sentinels (MIN/MAX) handle empty sides. Once the partition is valid, the median comes from the boundary values. Searching the smaller array gives O(log min(m, n)) and also keeps `j` in range. Interviewers expect you to start with the O(m + n) merge idea and then improve it.''',
"O(log min(m, n))", "O(1)", "https://leetcode.com/problems/median-of-two-sorted-arrays/"),

C("Minimum Window Substring", "Hard", ["Google", "Uber", "Flipkart", "Amazon", "Microsoft"], r'''
Given strings `s` and `t`, return the **shortest substring of `s`** that contains every character of `t`, including duplicates. Return `""` if there isn't one. The answer is guaranteed to be unique.

**Example 1**
```
Input:  s = "ADOBECODEBANC", t = "ABC"
Output: "BANC"
```
**Example 2**
```
Input:  s = "a", t = "aa"
Output: ""
```
**Constraints:** 1 ≤ |s|, |t| ≤ 10^5. Both strings contain upper and lowercase English letters.''',
["Use a sliding window. Expand the right end until the window covers t, then shrink the left end as much as possible.",
 "Keep a need[128] count array and a 'missing' counter so the coverage check is O(1)."],
r'''
class Solution {
    public String minWindow(String s, String t) {
        int[] need = new int[128];
        for (char c : t.toCharArray()) need[c]++;
        int missing = t.length();
        int bestStart = 0, bestLen = Integer.MAX_VALUE;

        for (int left = 0, right = 0; right < s.length(); right++) {
            char rc = s.charAt(right);
            if (need[rc]-- > 0) missing--;          // this char was still needed
            while (missing == 0) {                  // window covers t: try shrinking
                if (right - left + 1 < bestLen) {
                    bestLen = right - left + 1;
                    bestStart = left;
                }
                char lc = s.charAt(left++);
                if (++need[lc] > 0) missing++;      // removed a required char
            }
        }
        return bestLen == Integer.MAX_VALUE ? "" : s.substring(bestStart, bestStart + bestLen);
    }
}''',
'''`need[c]` counts how many more copies of `c` the window still requires. It goes negative for surplus characters. `missing` is the total number of required characters still uncovered, so "window is valid" is just `missing == 0`, an O(1) check. Each step expands the right end. While the window is valid, we record it and shrink from the left. Removing a character whose count goes back above zero means the window just lost a required character, so `missing` goes up and shrinking stops. Each index enters and leaves the window at most once, which gives O(|s| + |t|). This variable-size sliding-window template also solves "Longest Substring Without Repeating Characters" and "Find All Anagrams".''',
"O(|s| + |t|)", "O(1) (128-size array)", "https://leetcode.com/problems/minimum-window-substring/"),

C("Word Break", "Medium", ["Google", "Amazon", "Walmart", "Microsoft", "Uber"], r'''
Given a string `s` and a dictionary `wordDict`, return `true` if `s` can be split into a space-separated sequence of one or more dictionary words. Words can be reused.

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
**Constraints:** 1 ≤ |s| ≤ 300, 1 ≤ wordDict.length ≤ 1000, 1 ≤ word length ≤ 20''',
["dp[i] = true if the prefix s[0..i) can be segmented.",
 "dp[i] = OR over j of (dp[j] AND s[j..i) is in the dictionary). Only check j where i − j ≤ the longest word length."],
r'''
import java.util.*;

class Solution {
    public boolean wordBreak(String s, List<String> wordDict) {
        Set<String> dict = new HashSet<>(wordDict);
        int maxLen = 0;
        for (String w : wordDict) maxLen = Math.max(maxLen, w.length());

        boolean[] dp = new boolean[s.length() + 1];
        dp[0] = true;                                    // empty prefix
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
}''',
'''`dp[i]` says whether the first `i` characters can be split into words. A prefix is breakable if some shorter breakable prefix `dp[j]` is followed by a dictionary word `s[j..i)`. Limiting `j` to the longest word length cuts the inner loop from O(n) to O(L), and the `break` stops as soon as one split works. Plain recursion without memoization is exponential on inputs like "aaaa…b", which is why interviewers push for DP. Common follow-ups: **Word Break II**, which returns all sentences using memoized DFS (output can be exponential), and using a **Trie** to match dictionary words while scanning forward from each `j`.''',
"O(n · L · L) (substring hashing)", "O(n + dictionary)", "https://leetcode.com/problems/word-break/"),

C("Serialize and Deserialize Binary Tree", "Hard", ["Amazon", "Microsoft", "Google", "Uber", "Atlassian"], r'''
Write `serialize(TreeNode root)`, which turns a binary tree into a string, and `deserialize(String data)`, which rebuilds exactly the same tree. You choose the format. `deserialize(serialize(root))` must reproduce the original structure and values.

**Example**
```
Tree:      1
          / \
         2   3
            / \
           4   5
serialize   -> "1,2,#,#,3,4,#,#,5,#,#"   (one possible format)
deserialize -> the same tree
```
**Constraints:** up to 10^4 nodes, −1000 ≤ val ≤ 1000. Values can repeat.''',
["Preorder traversal with a null marker such as '#' captures the structure exactly.",
 "Deserialize by reading tokens in the same preorder from a queue or index, building recursively: node, left, right."],
r'''
import java.util.*;

class TreeNode {
    int val;
    TreeNode left, right;
    TreeNode(int v) { val = v; }
}

class Codec {
    private static final String NULL = "#";

    public String serialize(TreeNode root) {
        StringBuilder sb = new StringBuilder();
        build(root, sb);
        return sb.substring(0, sb.length() - 1);        // drop trailing comma
    }

    private void build(TreeNode node, StringBuilder sb) {
        if (node == null) {
            sb.append(NULL).append(',');
            return;
        }
        sb.append(node.val).append(',');
        build(node.left, sb);
        build(node.right, sb);
    }

    public TreeNode deserialize(String data) {
        Deque<String> tokens = new ArrayDeque<>(Arrays.asList(data.split(",")));
        return parse(tokens);
    }

    private TreeNode parse(Deque<String> tokens) {
        String tok = tokens.poll();
        if (NULL.equals(tok)) return null;
        TreeNode node = new TreeNode(Integer.parseInt(tok));
        node.left = parse(tokens);
        node.right = parse(tokens);
        return node;
    }
}''',
'''Preorder traversal **with explicit null markers** is enough to describe a binary tree uniquely, because every subtree's boundary is marked by its `#` leaves. Plain preorder or inorder alone can't do this, especially with duplicate values. Deserializing reads tokens in the same order: a token is either `#` (return null) or a value, followed by building its left and right subtrees recursively. Both directions touch each node once, so the total is O(n). A `StringBuilder` avoids quadratic string concatenation. For a 10^4-node skewed tree, recursion depth may matter, and a **level-order (BFS)** version with a queue avoids it. Interviewers often ask for the BFS version too, or a compact binary encoding.''',
"O(n)", "O(n)", "https://leetcode.com/problems/serialize-and-deserialize-binary-tree/"),
]

theory = [
T("Explain the Java Memory Model and the happens-before relationship.", '''The JMM defines **when one thread's writes are guaranteed to be visible to another thread**. Without that guarantee, the JIT and CPU can reorder instructions and keep values in registers or caches, so a thread might never see an update.

**Happens-before** is the guarantee: if action A happens-before B, B sees A's effects. The key rules:
- **Program order** within a single thread.
- **Monitor lock**: an unlock happens-before every later lock of the same monitor (synchronized, ReentrantLock).
- **volatile**: a write happens-before every later read of that variable.
- **Thread start/join**: `t.start()` happens-before anything in t, and everything in t happens-before `t.join()` returns.
- **Final fields** are visible once the constructor finishes, as long as `this` doesn't escape.
- The relationship is **transitive**.

Practical effects: a `volatile boolean running` flag works for stopping threads, double-checked locking needs volatile, and concurrent collections and `CompletableFuture` provide these guarantees internally.''', ["Goldman Sachs", "Oracle", "JP Morgan", "Microsoft"]),

T("How does garbage collection work in the JVM, and how does G1 differ?", '''The GC reclaims objects that can't be reached from **GC roots**: thread stacks, static fields and JNI references. It's based on the **generational hypothesis**, which says most objects die young.

- **Young generation** (Eden plus two Survivor spaces): new objects go to Eden. A *minor GC* copies live objects to a survivor space, and objects that survive several cycles get **promoted** to the old generation.
- **Old generation**: collected less often by a *major or mixed* GC.
-
**G1 (the default):** the heap is split into equal regions (1–32 MB) that act as Eden, Survivor, Old or Humongous. Marking runs concurrently, then G1 collects the regions with the **most garbage first** to meet a pause target (`MaxGCPauseMillis`). It compacts incrementally, so it avoids the long full GCs that CMS suffered from.

**ZGC/Shenandoah** do most of the work concurrently, with pauses under a millisecond even on huge heaps.''', ["Oracle", "SAP", "Goldman Sachs"]),

T("Explain ACID and how databases actually implement atomicity and durability.", '''- **Atomicity:** a transaction is all-or-nothing.
- **Consistency:** constraints and invariants hold before and after.
- **Isolation:** concurrent transactions behave as if they ran in some serial order, depending on the isolation level.
- **Durability:** once committed, data survives a crash.

**How it's done (InnoDB as the example):**
- **Write-ahead logging (redo log):** changes are written to a sequential log and fsynced *before* the commit is acknowledged. After a crash, the redo log replays committed changes to the data pages, which gives **durability**.
- **Undo log:** stores the previous versions of rows. A rollback or a crash-recovered uncommitted transaction uses it to reverse changes, which gives **atomicity**. The same versions power **MVCC** snapshot reads.
- **Locks and MVCC** provide **isolation**: row locks, gap locks and consistent snapshots.
- **Consistency** comes from constraints (PK, FK, CHECK) plus correct application logic.''', ["Goldman Sachs", "Intuit", "Oracle", "Amazon"]),

T("What happens when you type a URL into the browser and press Enter?", '''1. **URL parsing** and HSTS check. The browser may upgrade the request to HTTPS.
2. **DNS resolution:** browser cache → OS cache/hosts file → recursive resolver → root → TLD → authoritative server, which returns an A/AAAA record (cached according to its TTL).
3. **TCP 3-way handshake** with the server IP on port 443 (or QUIC over UDP for HTTP/3).
4. **TLS handshake:** ClientHello/ServerHello, certificate validation against trusted CAs, key exchange (ECDHE), and session keys.
5. **HTTP request** with headers and cookies. It may pass through a CDN, a load balancer (L4/L7) and a reverse proxy before reaching an app server, which queries caches and databases.
6. **Response:** status, headers (cache-control, set-cookie) and body, possibly compressed.
7. **Rendering:** parse HTML into the DOM and CSS into the CSSOM, fetch sub-resources (reusing connections, multiplexed over HTTP/2), run JavaScript, then layout, paint and composite.''', ["Google", "Amazon", "Atlassian", "Microsoft"]),

T("Explain the CAP theorem and PACELC with real examples.", '''**CAP:** when there's a network **Partition**, a distributed store has to choose between **Consistency**, where every read sees the latest write or gets an error, and **Availability**, where every request gets a non-error response that may be stale. Partitions can't be avoided in practice, so the real choice is CP or AP.

- **CP:** ZooKeeper, etcd, HBase, and MongoDB with majority writes. The minority side rejects requests.
- **AP:** Cassandra, DynamoDB (default), Couchbase. They accept writes on both sides and reconcile later using last-write-wins, vector clocks or CRDTs.

**PACELC** adds the normal case: *if Partitioned, choose A or C; Else, choose Latency or Consistency.* Even without failures, synchronous replication adds latency. Cassandra is PA/EL, tunable through consistency levels (QUORUM where R + W > N gives strong reads).

In design interviews, choose per feature: payments need CP, while a feed or likes counter is fine with AP.''', ["Atlassian", "Uber", "Flipkart", "Walmart"]),

T("How does a B+ tree index work, and why do databases prefer it over hash indexes?", '''A **B+ tree** is a balanced, high-fanout tree. Internal nodes hold only keys for routing, and **all the data pointers live in the leaves**, which are linked in sorted order. A node is about one disk page (16 KB in InnoDB), so fanout is in the hundreds. Even a billion rows need only 3–4 levels, meaning 3–4 page reads per lookup.

**Why it's preferred:**
- It supports **range queries, ORDER BY, prefix LIKE 'abc%', and MIN/MAX** by walking the linked leaves. A hash index only supports equality.
- Predictable O(log n) with self-balancing splits/merges.
- It works for composite keys using the leftmost-prefix rule.

In **InnoDB**, the primary key is a **clustered** B+ tree whose leaves store whole rows. Secondary indexes store the PK, so lookups through them need a second traversal unless the index is **covering**.''', ["Oracle", "Amazon", "Goldman Sachs", "Intuit"]),
]

save(13, "Mock Test 2",
     "A harder mixed mock covering tricky Java output, SQL NULL semantics, OS/CN/DBMS fundamentals and four hard-level coding problems under time pressure.",
     mcqs, coding, theory)
