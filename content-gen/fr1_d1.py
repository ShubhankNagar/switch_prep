from fr1_common import M, C, T, build

mcqs = [
M("Java output prediction", '''What does this print?
```java
String s1 = "Java";
String s2 = new String("Java");
String s3 = s2.intern();
System.out.println((s1 == s2) + " " + (s1 == s3));
```''', ["true true", "false true", "false false", "true false"], 1,
'''`s1` points to the pooled literal, while `new String` always creates a separate heap object, so `s1 == s2` is false. `intern()` returns the canonical pooled instance, which is the same object `s1` refers to, so `s1 == s3` is true.''',
["Amazon", "Paytm"]),

M("Java collections", '''In Java 8+, when does a single `HashMap` bucket switch from a linked list to a red-black tree?''',
["As soon as two keys collide in the bucket",
 "When the bucket holds at least 8 nodes and the table capacity is at least 64",
 "When the load factor exceeds 0.75",
 "Only when keys implement Comparable"], 1,
'''`TREEIFY_THRESHOLD` is 8 and `MIN_TREEIFY_CAPACITY` is 64. If the table is smaller than 64, the map resizes instead of treeifying. Trees turn worst-case bucket lookup from O(n) to O(log n). Comparable is used for ordering when available, but is not required.''',
["Amazon", "Walmart", "PhonePe"]),

M("Hashing", '''You must report whether any two numbers in an unsorted array of n integers add up to a target. Using a `HashSet` in a single pass, what is the expected time complexity?''',
["O(n log n)", "O(n^2)", "O(n)", "O(log n)"], 2,
'''For each element you check whether `target - x` is already in the set and then insert `x`. Each lookup and insert is expected O(1), so one pass costs O(n) time and O(n) extra space. Sorting plus two pointers would be O(n log n).''',
["Amazon", "Microsoft"]),

M("Java collections", '''What does this print?
```java
Map<String, Integer> m = new HashMap<>();
m.put(null, 1);
m.put(null, 2);
System.out.println(m.size() + " " + m.get(null));
```''', ["2 1", "1 1", "1 2", "NullPointerException"], 2,
'''`HashMap` allows exactly one null key (it is stored in bucket 0). The second `put` with the same null key replaces the value, so the size stays 1 and `get(null)` returns 2. `Hashtable` and `ConcurrentHashMap` would throw NullPointerException.''',
["Amazon", "Oracle"]),

M("Java output prediction", '''What does this print?
```java
char c = 'A';
c += 2;
System.out.println(c + 1);
System.out.println("" + c + 1);
```''', ["C1 then C1", "68 then C1", "D then C1", "68 then 68"], 1,
'''The compound assignment `c += 2` casts back to char, giving 'C'. `c + 1` promotes to int: 67 + 1 = 68. In `"" + c + 1`, evaluation is left to right with a String on the left, so it becomes "C" and then "C1".''',
["Amazon", "Adobe"]),

M("Java output prediction", '''What does this print?
```java
Integer a = 127, b = 127;
Integer c = 128, d = 128;
System.out.println((a == b) + " " + (c == d));
```''', ["true true", "false false", "true false", "false true"], 2,
'''Autoboxing uses `Integer.valueOf`, which returns cached objects for values from -128 to 127. So `a` and `b` are the same object, while 128 creates two different objects and `==` compares references. Always compare wrapper objects with `equals`.''',
["Amazon", "JP Morgan", "Paytm"]),

M("Java core", '''What does this print?
```java
String s = "abc";
s.toUpperCase();
s.concat("d");
System.out.println(s);
```''', ["ABCD", "abcd", "abc", "ABC"], 2,
'''Strings are immutable. `toUpperCase()` and `concat()` return new String objects, and both results are thrown away here. `s` still refers to "abc". To keep the change you must reassign, for example `s = s.concat("d");`.''',
["Amazon", "SAP"]),

M("Java collections", '''What happens at runtime?
```java
List<Integer> list = Arrays.asList(1, 2, 3);
list.set(0, 9);
list.add(4);
```''', ["Works; list becomes [9, 2, 3, 4]", "Compilation error at add", "UnsupportedOperationException at add", "UnsupportedOperationException at set"], 2,
'''`Arrays.asList` returns a fixed-size list backed by the array. `set` is allowed because it does not change the size, but `add` and `remove` throw `UnsupportedOperationException`. Wrap it in `new ArrayList<>(...)` to get a resizable list.''',
["Amazon", "Walmart"]),

M("Java core", '''A class overrides `equals()` but NOT `hashCode()`. Two logically equal instances are added to a `HashSet`. What usually happens?''',
["The set contains 1 element, because equals is used first",
 "The set usually contains 2 elements",
 "A compile-time error occurs",
 "A ClassCastException is thrown"], 1,
'''`HashSet` first uses `hashCode()` to choose a bucket. The default identity hash codes almost always differ, so the two objects land in different buckets and `equals` is never called. That breaks the contract that equal objects must have equal hash codes.''',
["Amazon", "Goldman Sachs", "Oracle"]),

M("Aptitude", '''A 150 m long train passes a pole in 15 seconds. How long will it take to completely cross a 250 m long platform at the same speed?''',
["25 s", "30 s", "40 s", "45 s"], 2,
'''Speed = 150 / 15 = 10 m/s. To cross a platform, the train covers its own length plus the platform length: 150 + 250 = 400 m. Time = 400 / 10 = 40 seconds.''',
["Oracle", "SAP", "Paytm"]),

M("Logical reasoning", '''In a code language, AMAZON is written as BNBAPO. How is GOOGLE written in that language?''',
["HPPHMF", "FNNFKD", "HPPGMF", "HOPHMF"], 0,
'''Each letter is shifted forward by one: A to B, M to N, Z to A (wrap-around), and so on. Applying +1 to G, O, O, G, L, E gives H, P, P, H, M, F, so the answer is HPPHMF.''',
["Amazon", "Paytm"]),

M("Two pointers", '''For a SORTED array, you want a pair that sums to a target using two pointers (one at each end). What are the time and extra-space complexities?''',
["O(n) time, O(n) space", "O(n) time, O(1) space", "O(n log n) time, O(1) space", "O(log n) time, O(1) space"], 1,
'''When the sum is too small, move the left pointer right; when it is too large, move the right pointer left. Each pointer moves at most n times, so the scan is O(n), and it only needs two index variables, which is O(1) extra space.''',
["Amazon", "Microsoft", "Flipkart"]),

M("Java output prediction", '''What does this print?
```java
System.out.println(1 + 2 + "3" + 4 + 5);
```''', ["15", "3345", "12345", "339"], 1,
'''`+` is evaluated left to right. `1 + 2` is integer addition, giving 3. Then `3 + "3"` becomes the String "33", and after that every `+` is concatenation: "334" and then "3345".''',
["Amazon", "Oracle", "Myntra"]),

M("Java core", '''Which of these is mutable AND thread-safe because its methods are synchronized?''',
["String", "StringBuilder", "StringBuffer", "StringJoiner"], 2,
'''`StringBuffer` synchronizes its public methods, so it is thread-safe but slower. `StringBuilder` has the same API without synchronization and is preferred in single-threaded code. `String` is immutable. `StringJoiner` is a non-synchronized helper.''',
["Amazon", "SAP", "Paytm"]),

M("Spring Boot", '''`@SpringBootApplication` is a convenience annotation equivalent to which combination?''',
["@Configuration + @EnableAutoConfiguration + @ComponentScan",
 "@Component + @Autowired + @Bean",
 "@EnableWebMvc + @RestController + @ComponentScan",
 "@Configuration + @EnableTransactionManagement + @EntityScan"], 0,
'''It is a meta-annotation for `@SpringBootConfiguration` (a specialized `@Configuration`), `@EnableAutoConfiguration` and `@ComponentScan` on the package of the main class. That is why beans outside that package tree are not picked up by default.''',
["Amazon", "Paytm", "Swiggy"]),

M("Java collections", '''A `HashMap` is created with the default constructor (capacity 16, load factor 0.75). When does the FIRST resize happen?''',
["When the 16th entry is inserted", "When the 13th entry is inserted", "When the 12th entry is inserted", "When the 9th entry is inserted"], 1,
'''The threshold is capacity x load factor = 16 x 0.75 = 12. Resizing happens when the size goes above the threshold, so inserting the 13th mapping doubles the table to 32. Pre-size the map if you know the entry count, to avoid repeated rehashing.''',
["Amazon", "Walmart", "Razorpay"]),

M("Hashing", '''When counting subarrays whose sum equals k with a prefix-sum `HashMap<sum, count>`, why do we put `(0, 1)` into the map before the loop?''',
["To avoid a NullPointerException on the first get",
 "To count subarrays that start at index 0",
 "To handle negative numbers",
 "It is an optimisation that does not change the answer"], 1,
'''A subarray from index 0 to i has sum k exactly when the prefix sum equals k, which means `prefix - k = 0`. Seeding the map with sum 0 seen once represents the empty prefix, so those subarrays are counted. Without it, the answer would be too small.''',
["Amazon", "Flipkart", "Meesho"]),

M("Java core", '''What is the result?
```java
final int[] arr = {1, 2, 3};
arr[0] = 10;
System.out.println(arr[0]);
```''', ["Compile error: cannot assign to final", "10", "1", "Runtime exception"], 1,
'''`final` makes the reference `arr` unchangeable, so you cannot point it at a new array. The array's contents are still mutable, so `arr[0] = 10` is legal and the code prints 10. The same applies to final collections.''',
["Amazon", "JP Morgan"]),

M("Bit manipulation", '''Every element of `[4, 1, 2, 1, 2]` appears twice except one. What does XOR-ing all elements return, and why is this approach popular in OAs?''',
["0; XOR cancels everything", "4; pairs cancel because x ^ x = 0, giving O(n) time and O(1) space", "1; it returns the smallest element", "2; it returns the most frequent element"], 1,
'''XOR is commutative and associative, `x ^ x = 0` and `x ^ 0 = x`. Pairs cancel out and only the single element, 4, remains. It needs no extra memory, unlike a HashMap frequency count.''',
["Amazon", "Adobe"]),

M("Strings", '''What is the best time complexity to check whether two lowercase strings of length n are anagrams?''',
["O(n^2)", "O(n log n) only", "O(n) using a 26-size count array", "O(1)"], 2,
'''Increment counts for one string and decrement for the other in a fixed array of 26 ints, then check that every count is zero. That is O(n) time and O(1) extra space. Sorting both strings also works, but costs O(n log n).''',
["Amazon", "Microsoft", "Goldman Sachs"]),
]

coding = [
C("Group Anagrams", "Medium", ["Amazon", "Microsoft", "Goldman Sachs", "Uber"],
'''Given an array of strings `strs`, put all anagrams together. Two words are anagrams if one is a rearrangement of the other's letters. Return the groups in any order.

**Example 1**
```
Input:  strs = ["eat","tea","tan","ate","nat","bat"]
Output: [["eat","tea","ate"],["tan","nat"],["bat"]]
```
**Example 2**
```
Input:  strs = [""]
Output: [[""]]
```
**Constraints**
- 1 <= strs.length <= 10^4
- 0 <= strs[i].length <= 100
- strs[i] contains only lowercase English letters''',
["All anagrams share the same 'signature'. What signature could you use as a HashMap key?",
 "Instead of sorting each word (k log k), build a key from 26 letter counts in O(k)."],
r'''
import java.util.*;

class Solution {
    public List<List<String>> groupAnagrams(String[] strs) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String s : strs) {
            int[] cnt = new int[26];
            for (char ch : s.toCharArray()) cnt[ch - 'a']++;
            StringBuilder key = new StringBuilder();
            for (int c : cnt) key.append('#').append(c);   // e.g. "#1#0#0...#1"
            groups.computeIfAbsent(key.toString(), k -> new ArrayList<>()).add(s);
        }
        return new ArrayList<>(groups.values());
    }
}
''',
'''Anagrams have identical letter frequencies, so a frequency signature is a natural grouping key. For each word, count its 26 letters and encode the counts as a string such as `#1#0#0...`. The separator matters, because without it the counts 1,11 and 11,1 would produce the same key. `computeIfAbsent` creates the bucket list on first use. You could also use the sorted word as the key, which is simpler to write but costs O(k log k) per word. In an interview, mention both and say why the counting key is faster for long words.''',
"O(n * k), where k is the max word length", "O(n * k)", "https://leetcode.com/problems/group-anagrams/"),

C("Longest Substring Without Repeating Characters", "Medium", ["Amazon", "Microsoft", "Adobe", "Walmart"],
'''Given a string `s`, return the length of the longest substring (a contiguous block) in which no character repeats.

**Example 1**
```
Input:  s = "abcabcbb"
Output: 3        // "abc"
```
**Example 2**
```
Input:  s = "pwwkew"
Output: 3        // "wke"; "pwke" is a subsequence, not a substring
```
**Constraints**
- 0 <= s.length <= 5 * 10^4
- s may contain letters, digits, symbols and spaces''',
["Keep a window [left, right] that never contains duplicates, and grow it to the right.",
 "Store the last index of every character, so you can jump `left` directly past the previous occurrence."],
r'''
import java.util.*;

class Solution {
    public int lengthOfLongestSubstring(String s) {
        int[] last = new int[128];          // last index + 1 of each ASCII char
        int best = 0, left = 0;
        for (int right = 0; right < s.length(); right++) {
            char ch = s.charAt(right);
            left = Math.max(left, last[ch]);  // jump past previous occurrence
            best = Math.max(best, right - left + 1);
            last[ch] = right + 1;
        }
        return best;
    }
}
''',
'''This is a sliding window. `last[ch]` stores one past the index where `ch` was last seen. When we see `ch` again, the window must start after that previous occurrence, so `left` becomes `max(left, last[ch])`. The `max` matters: an old occurrence that is already outside the window must not move `left` backwards. After each step, the window `[left, right]` has only distinct characters, and we update the best length. Each index is visited once, so the scan is linear. Using an `int[128]` instead of a HashMap keeps the space constant for ASCII input.''',
"O(n)", "O(1) (fixed 128-size array)", "https://leetcode.com/problems/longest-substring-without-repeating-characters/"),

C("Subarray Sum Equals K", "Medium", ["Amazon", "Flipkart", "Meesho", "Google"],
'''Given an integer array `nums` (which may contain negative numbers) and an integer `k`, return how many contiguous, non-empty subarrays have a sum equal to `k`.

**Example 1**
```
Input:  nums = [1,1,1], k = 2
Output: 2
```
**Example 2**
```
Input:  nums = [1,2,3], k = 3
Output: 2        // [1,2] and [3]
```
**Constraints**
- 1 <= nums.length <= 2 * 10^4
- -1000 <= nums[i] <= 1000
- -10^7 <= k <= 10^7''',
["Sliding window fails when negative numbers are present. Think about prefix sums instead.",
 "sum(i..j) = prefix[j] - prefix[i-1]. For each prefix value, how many earlier prefixes equal `prefix - k`?"],
r'''
import java.util.*;

class Solution {
    public int subarraySum(int[] nums, int k) {
        Map<Integer, Integer> seen = new HashMap<>();
        seen.put(0, 1);                      // empty prefix
        int prefix = 0, count = 0;
        for (int x : nums) {
            prefix += x;
            count += seen.getOrDefault(prefix - k, 0);
            seen.merge(prefix, 1, Integer::sum);
        }
        return count;
    }
}
''',
'''The array may contain negative numbers, so the window sum is not monotonic and two pointers cannot decide when to shrink. Use prefix sums instead. A subarray ending at the current index has sum `k` exactly when some earlier prefix equals `prefix - k`. The map counts how many times each prefix sum has appeared so far, so each step adds that count to the answer. Seeding `(0, 1)` covers subarrays that start at index 0. Check the map before inserting the current prefix, so you never count an empty subarray. This pattern also solves "subarrays divisible by K" and "longest subarray with sum K".''',
"O(n)", "O(n)", "https://leetcode.com/problems/subarray-sum-equals-k/"),

C("Trapping Rain Water", "Hard", ["Amazon", "Goldman Sachs", "Microsoft", "Adobe"],
'''You are given `n` non-negative integers that represent an elevation map, where every bar has width 1. Compute how many units of rain water are trapped between the bars after it rains.

**Example 1**
```
Input:  height = [0,1,0,2,1,0,1,3,2,1,2,1]
Output: 6
```
**Example 2**
```
Input:  height = [4,2,0,3,2,5]
Output: 9
```
**Constraints**
- 1 <= n <= 2 * 10^4
- 0 <= height[i] <= 10^5''',
["Water above bar i = min(maxLeft(i), maxRight(i)) - height[i].",
 "With two pointers, the side with the smaller running maximum is the bottleneck, so you can settle that side immediately."],
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
''',
'''The water above a bar is `min(highest bar to its left, highest bar to its right) - its height`. The simple approach precomputes leftMax and rightMax arrays, which uses O(n) space. The two-pointer version gets rid of those arrays. If `height[l] < height[r]`, some bar on the right is at least as tall as anything we could pair with, so the water at `l` depends only on `leftMax` and we can settle it immediately. The same reasoning applies to the right side. In Goldman Sachs CoderPad rounds, interviewers often ask for the prefix-array version first and then for this O(1)-space optimisation.''',
"O(n)", "O(1)", "https://leetcode.com/problems/trapping-rain-water/"),
]

theory = [
T("How does HashMap work internally in Java?",
'''A `HashMap` is an array of buckets (`Node<K,V>[] table`). On `put`, it computes `hash = h ^ (h >>> 16)` from `key.hashCode()` and finds the bucket with `(n - 1) & hash`. If the bucket is empty, the node goes in directly. Otherwise it walks the chain and uses `equals()` to either replace the value of a matching key or append a new node. Since Java 8, a chain longer than 8 becomes a red-black tree when the capacity is at least 64, which makes the worst-case lookup O(log n). When size exceeds capacity x load factor (0.75 by default), the table doubles. During that resize, each node either stays at the same index or moves to index + oldCapacity. `get` follows the same hash, index and equals path. `HashMap` allows one null key and is not thread-safe.''',
["Amazon", "Walmart", "Paytm", "PhonePe"]),

T("What is the contract between equals() and hashCode()? What breaks if you violate it?",
'''The rules are: (1) if `a.equals(b)` is true, then `a.hashCode() == b.hashCode()` must be true; (2) equal hash codes do NOT require the objects to be equal, because collisions are allowed; (3) both methods must give consistent results as long as the fields they use do not change. If you override `equals` without `hashCode`, hash-based collections put equal objects into different buckets. You then get duplicate entries in a `HashSet`, and `map.get()` returns null for a key that is logically present. Another common bug is a mutable field used in `hashCode`: if it changes after the object is inserted, the entry becomes unreachable. Build both methods from the same immutable fields, or use Java records, which generate them for you.''',
["Amazon", "Oracle", "JP Morgan", "Goldman Sachs"]),

T("Why is String immutable in Java?",
'''There are several reasons. **String pool:** many references share one literal, which is only safe if nobody can change it. **Security:** strings carry class names, file paths, URLs and DB credentials, and immutability stops someone from changing them after validation. **Thread safety:** immutable objects can be shared across threads without synchronization. **Hash caching:** `String` caches its `hashCode`, which makes it a fast and reliable HashMap key; a mutable key could change its hash and get lost inside the map. **Class loading:** the JVM relies on class names not changing. The downside is that repeated concatenation in loops creates many temporary objects, so use `StringBuilder` there.''',
["Amazon", "Goldman Sachs", "SAP", "Oracle"]),

T("Compare String, StringBuilder and StringBuffer. When would you use each?",
'''`String` is immutable. Every change creates a new object, which is ideal for constants, keys and values shared between threads. `StringBuilder` is mutable and not synchronized. It is the fastest choice for building strings in loops or inside a method, which covers most cases. `StringBuffer` is mutable with synchronized methods. It is thread-safe but slower, and is rarely needed today because a string being built is seldom shared between threads. Note that `javac` compiles a single expression like `a + b + c` efficiently; recent JDKs use `invokedynamic` and `StringConcatFactory`. The problem case is `s += x` inside a loop, which produces O(n^2) copying. For example, "I used StringBuilder to generate CSV exports in a loop and cut the time from seconds to milliseconds."''',
["Oracle", "Paytm", "Amazon"]),

T("Which Java 8+ features do you use in your project? Explain streams and Optional.",
'''I use lambdas and functional interfaces (`Function`, `Predicate`, `Supplier`), the Stream API, `Optional`, method references, default methods in interfaces, the `java.time` API and `CompletableFuture`. **Streams** process collections declaratively through a pipeline: a source, then lazy intermediate operations (`filter`, `map`, `sorted`), then a terminal operation (`collect`, `reduce`, `count`). Nothing executes until the terminal operation runs. For example, `orders.stream().filter(o -> o.getStatus() == PAID).collect(groupingBy(Order::getCustomerId, summingDouble(Order::getAmount)))`. **Optional** makes the possibility of a missing value explicit in a return type, as in `repo.findById(id).orElseThrow(() -> new NotFoundException(id))`, which avoids null checks. Avoid `Optional` for fields or parameters, and avoid calling `get()` without first checking for a value. From Java 17, I also use records, `var`, switch expressions and text blocks.''',
["Walmart", "Swiggy", "Razorpay", "Amazon"]),

T("Walk me through the most challenging problem you solved in your current project.",
'''Use the STAR structure and keep it to about two minutes. **Situation:** "Our Spring Boot order API's p95 latency rose to 3 s during month-end reports." **Task:** "I owned finding the cause and fixing it without downtime." **Action:** "I enabled Hibernate SQL logs and found an N+1 query when loading order items. I replaced it with a `JOIN FETCH` / `@EntityGraph`, added a composite index on `(customer_id, created_at)` after reading the `EXPLAIN` plan, and added pagination to the Angular grid." **Result:** "p95 fell to 250 ms and DB CPU dropped 40%. I documented the pattern for the team." Amazon interviewers then dig into details (the Dive Deep principle): why that index column order, what you measured, and what you would do differently. Use real numbers you can defend.''',
["Amazon", "Flipkart", "Atlassian"]),
]

DAY = build(1, "Amazon-style OA", "Arrays, strings and hashing problems of the kind seen in Amazon online assessments, plus core Java MCQs on strings, wrappers and HashMap internals.", mcqs, coding, theory)
