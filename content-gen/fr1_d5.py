from fr1_common import M, C, T, build

mcqs = [
M("Java output prediction", '''What do `f()` and `g()` return?
```java
static int f() {
    try { return 1; } finally { return 2; }
}
static int g() {
    int x = 10;
    try { return x; } finally { x = 20; }
}
```''', ["1 and 10", "2 and 20", "2 and 10", "1 and 20"], 2,
'''In `f`, a `return` inside finally overrides the try's return value (it would also swallow exceptions), so it returns 2. In `g`, the value 10 is saved when `return x` runs. Changing the local `x` in finally does not change that saved value, so it returns 10.''',
["Goldman Sachs", "JP Morgan", "Oracle"]),

M("Java output prediction", '''What does this print?
```java
static void change(StringBuilder sb) {
    sb.append("B");
    sb = new StringBuilder("C");
    sb.append("D");
}
// in main
StringBuilder s = new StringBuilder("A");
change(s);
System.out.println(s);
```''', ["A", "AB", "CD", "ABCD"], 1,
'''Java is always pass-by-value. For objects, the value passed is a copy of the reference. `append("B")` changes the shared object, giving "AB". Reassigning `sb` only changes the local copy, so "C" and "D" go to a new object that main never sees.''',
["JP Morgan", "Goldman Sachs", "SAP"]),

M("Java output prediction", '''What does this print?
```java
System.out.println(5 / 2 + 5 % 2 + 5.0 / 2);
```''', ["5.0", "5.5", "6.0", "4.5"], 1,
'''`5 / 2` is integer division, giving 2. `5 % 2` gives 1. `5.0 / 2` is floating-point division, giving 2.5. Left to right: 2 + 1 = 3 (int), then 3 + 2.5 = 5.5 (the int is promoted to double).''',
["Goldman Sachs", "JP Morgan"]),

M("Java output prediction", '''What does this print?
```java
int i = 5;
i = i++ + ++i;
System.out.println(i);
```''', ["10", "11", "12", "13"], 2,
'''`i++` yields 5 and then sets i to 6. `++i` sets i to 7 and yields 7. The sum is 5 + 7 = 12, and that is assigned to i, overwriting the increments. Code like this is unreadable in practice, but it appears often in OA output questions.''',
["Goldman Sachs", "JP Morgan", "Oracle"]),

M("Java output prediction", '''What does `System.out.println((byte) 130);` print?''',
["130", "-126", "126", "Compile error"], 1,
'''A byte holds -128 to 127. Casting keeps the low 8 bits: 130 is 1000 0010 in binary, which is -126 in two's complement (130 - 256). Narrowing casts silently wrap around instead of throwing.''',
["JP Morgan", "Goldman Sachs"]),

M("Java output prediction", '''What does this print?
```java
System.out.println(Math.round(-2.5) + " " + Math.round(2.5));
```''', ["-3 3", "-2 3", "-2 2", "-3 2"], 1,
'''`Math.round(x)` is defined as `floor(x + 0.5)`. For -2.5 that is floor(-2.0) = -2, and for 2.5 it is floor(3.0) = 3. Halves always round toward positive infinity. Use `BigDecimal` with `RoundingMode.HALF_EVEN` for banker's rounding, which matters in financial code.''',
["Goldman Sachs", "JP Morgan"]),

M("Java output prediction", '''What does `System.out.println(true ? 1 : 2.0);` print?''',
["1", "1.0", "2.0", "Compile error"], 1,
'''When the two branches of a conditional expression have different numeric types, binary numeric promotion applies, so the int 1 becomes the double 1.0. The type of the whole expression is double, even though the false branch is never evaluated.''',
["Goldman Sachs", "Oracle"]),

M("Java output prediction", '''What does `System.out.println('a' + 'b' + "c");` print?''',
["abc", "195c", "ab c", "97b c"], 1,
'''Evaluation goes left to right. `'a' + 'b'` is char + char, which is numeric addition: 97 + 98 = 195. Then `195 + "c"` is string concatenation, giving "195c". Writing `"" + 'a' + 'b' + "c"` would print "abc".''',
["JP Morgan", "Goldman Sachs", "Paytm"]),

M("Java exceptions", '''What happens when this compiles?
```java
try {
    readFile();               // throws IOException
} catch (Exception e) {
    System.out.println("E");
} catch (IOException e) {
    System.out.println("IO");
}
```''', ["Prints E", "Prints IO", "Compile error: IOException catch is unreachable", "Runtime error"], 2,
'''Catch blocks are checked in order, and `Exception` already catches every IOException. The compiler rejects the later, more specific block as unreachable. Order catches from most specific to most general, or use a multi-catch `catch (A | B e)` for unrelated exceptions.''',
["Goldman Sachs", "JP Morgan", "Oracle"]),

M("Java output prediction", '''What does `System.out.println(0.1 + 0.2 == 0.3);` print, and what should you use for money?''',
["true; double is exact", "false; use BigDecimal (built from Strings) for currency", "false; use float instead", "true; but only on 64-bit JVMs"], 1,
'''0.1 and 0.2 have no exact binary representation, so the sum is 0.30000000000000004. For money, use `BigDecimal` created with `new BigDecimal("0.1")` (not from a double), or store amounts in paise as `long`. Compare doubles with a tolerance.''',
["Goldman Sachs", "JP Morgan", "Razorpay"]),

M("Operating systems", '''Which resources do threads of the SAME process share?''',
["Stack and registers", "Heap, code and open file descriptors, but each thread has its own stack and registers",
 "Nothing; each thread is isolated", "Only the program counter"], 1,
'''Threads share the process's address space (heap, globals, code) and OS resources such as files and sockets. Each thread has its own stack, program counter and register set. Sharing makes communication cheap, but it creates race conditions that need synchronization.''',
["Goldman Sachs", "JP Morgan", "Microsoft"]),

M("Operating systems", '''What is thrashing?''',
["The CPU overheating", "The system spends more time paging than executing, because the working sets of processes do not fit in RAM",
 "A deadlock between two processes", "Frequent context switches caused by a small time quantum"], 1,
'''When too many processes compete for too few frames, each page fault evicts a page that is needed soon, causing more faults. CPU utilisation drops, and the scheduler may make it worse by admitting more processes. Fixes include a working-set model, page-fault-frequency control, adding RAM, and reducing the degree of multiprogramming.''',
["Goldman Sachs", "Oracle", "Microsoft"]),

M("Operating systems", '''Belady's anomaly, where giving MORE frames causes MORE page faults, can occur with which page replacement algorithm?''',
["LRU", "Optimal (OPT)", "FIFO", "All of them"], 2,
'''FIFO is not a stack algorithm, so the set of pages in memory with n frames is not always a subset of the set with n + 1 frames. The reference string 1,2,3,4,1,2,5,1,2,3,4,5 gives 9 faults with 3 frames and 10 faults with 4 frames. LRU and OPT are stack algorithms and never show the anomaly.''',
["Goldman Sachs", "JP Morgan"]),

M("Operating systems", '''Which CPU scheduling algorithm gives the minimum AVERAGE waiting time for a given set of processes?''',
["FCFS", "Round Robin", "Shortest Job First (preemptive SRTF is optimal)", "Priority scheduling"], 2,
'''Running shorter jobs first reduces the total time other jobs spend waiting, and preemptive SJF (Shortest Remaining Time First) is provably optimal for average waiting time. Its weaknesses are that burst times are hard to predict and long jobs can starve, which aging can fix. Round Robin optimises response time instead.''',
["Goldman Sachs", "Oracle", "SAP"]),

M("Operating systems", '''What is the key difference between a mutex and a binary semaphore?''',
["None; they are identical", "A mutex has ownership: only the thread that locked it may unlock it. A semaphore can be signalled by any thread",
 "A semaphore can only be used between processes", "A mutex allows N concurrent holders"], 1,
'''A mutex is a locking mechanism with an owner, and it often supports priority inheritance and reentrancy. A semaphore is a signalling counter: one thread can `wait()` and a different thread can `signal()`. That suits producer-consumer slot counting. In Java, `ReentrantLock` behaves like a mutex and `Semaphore` is a counting semaphore.''',
["Goldman Sachs", "Microsoft", "JP Morgan"]),

M("Operating systems", '''Why is a context switch between two threads of the same process usually cheaper than one between two processes?''',
["Threads do not have registers", "No address-space switch is needed, so the page table and TLB stay valid",
 "Threads do not use the scheduler", "Process switches involve disk I/O"], 1,
'''Both kinds of switch save and restore registers and the program counter. A process switch also changes the memory mapping (page tables), which usually flushes or invalidates TLB entries and pollutes caches, so the new process starts with cold caches. Threads share the address space, so that cost is avoided.''',
["Goldman Sachs", "Oracle"]),

M("Operating systems", '''A system uses 32-bit virtual addresses and 4 KB pages with a single-level page table. How many entries does each process's page table have?''',
["2^12", "2^20", "2^32", "2^10"], 1,
'''A 4 KB page needs 12 offset bits (2^12 = 4096). The remaining 32 - 12 = 20 bits form the page number, so the table has 2^20, about one million, entries. At 4 bytes each, that is 4 MB per process, which is why multi-level page tables are used.''',
["Goldman Sachs", "Microsoft"]),

M("Aptitude", '''How many trailing zeros does 100! (100 factorial) have?''',
["20", "24", "25", "11"], 1,
'''Trailing zeros come from factors of 10 = 2 x 5, and 2s are plentiful, so count the 5s: floor(100/5) + floor(100/25) + floor(100/125) = 20 + 4 + 0 = 24. This is also the LeetCode problem "Factorial Trailing Zeroes", O(log n).''',
["Goldman Sachs", "JP Morgan", "Microsoft"]),

M("Aptitude", '''What is the angle between the hour hand and the minute hand of a clock at 3:15?''',
["0°", "7.5°", "15°", "22.5°"], 1,
'''The minute hand is at 15 x 6 = 90°. The hour hand moves 0.5° per minute: 3 x 30 + 15 x 0.5 = 97.5°. The difference is 7.5°. The general formula is |30H - 5.5M|.''',
["Goldman Sachs", "JP Morgan", "Oracle"]),

M("Aptitude", '''A sum of money doubles in 5 years at simple interest. In how many years will it become 4 times the original amount at the same rate?''',
["10", "15", "20", "12"], 1,
'''Doubling means the interest equals the principal P in 5 years, so the rate is 20% per year. Becoming 4P needs interest of 3P, which takes 3 x 5 = 15 years. With compound interest the answer would be 10 years, which is a common trap.''',
["JP Morgan", "Goldman Sachs", "SAP"]),
]

coding = [
C("Highest Average Score", "Easy", ["Goldman Sachs", "JP Morgan"],
'''You are given a list of `[studentName, score]` pairs, and a student may appear multiple times. Return the highest average score among all students, rounded DOWN to an integer (floor). Return 0 for empty input. Scores may be negative.

**Example**
```
Input: [["Bob","87"],["Mike","35"],["Bob","52"],["Jason","35"],["Mike","55"],["Jessica","99"]]
Averages: Bob 69.5, Mike 45, Jason 35, Jessica 99
Output: 99
```
**Constraints**
- 0 <= records <= 10^5
- -100 <= score <= 100''',
["Aggregate the sum and count per student in a HashMap.",
 "Watch out: the floor of a negative average is not the same as integer division (which truncates toward zero)."],
r'''
import java.util.*;

class Solution {
    public int highestAverage(String[][] scores) {
        if (scores == null || scores.length == 0) return 0;
        Map<String, long[]> agg = new HashMap<>();          // name -> {sum, count}
        for (String[] rec : scores) {
            long[] sc = agg.computeIfAbsent(rec[0], k -> new long[2]);
            sc[0] += Integer.parseInt(rec[1].trim());
            sc[1]++;
        }
        double best = Double.NEGATIVE_INFINITY;
        for (long[] sc : agg.values()) best = Math.max(best, (double) sc[0] / sc[1]);
        return (int) Math.floor(best);
    }
}
''',
'''This is a well-known Goldman Sachs CoderPad warm-up, where clean code and edge cases matter more than the algorithm. Accumulate the sum and count per name in one pass. `long` guards against overflow, and a two-element array avoids creating a separate class. Then compute each average as a double and take the maximum. The trap is rounding: `(int) -2.5` gives -2, but the floor is -3, so use `Math.floor`. Interviewers watch for empty input, whitespace in the score strings, and unit-test style checks (write a small `main` with asserts). Follow-ups include returning the student's name and handling ties.''',
"O(n)", "O(s), where s = number of distinct students", None),

C("Decode Ways", "Medium", ["Goldman Sachs", "Amazon", "Microsoft", "JP Morgan"],
'''A message of letters A-Z is encoded as numbers, with 'A' = 1 and 'Z' = 26. Given a digit string `s`, return the number of ways to decode it. A code with a leading zero, such as "06", is invalid.

**Example**
```
"12"  -> 2   ("AB" or "L")
"226" -> 3   ("BZ", "VF", "BBF")
"06"  -> 0
```
**Constraints**
- 1 <= s.length <= 100
- s contains only digits; the answer fits in a 32-bit integer''',
["dp[i] = ways to decode the first i characters. The last step uses either one digit or two digits.",
 "A single digit is valid if it is not '0'; a two-digit number is valid if it is between 10 and 26."],
r'''
class Solution {
    public int numDecodings(String s) {
        int prev2 = 1;                                   // dp[i-2], empty prefix
        int prev1 = s.charAt(0) == '0' ? 0 : 1;          // dp[i-1]
        for (int i = 2; i <= s.length(); i++) {
            int cur = 0;
            char one = s.charAt(i - 1);
            int two = (s.charAt(i - 2) - '0') * 10 + (one - '0');
            if (one != '0') cur += prev1;                // decode single digit
            if (two >= 10 && two <= 26) cur += prev2;    // decode pair
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
''',
'''This works like climbing stairs with validity rules. The number of ways to decode a prefix ending at position i is the sum of two cases: the last character decoded alone (if it is not '0'), plus the last two characters decoded as one letter (if they form 10 to 26). Zeros are the tricky part. "30" gives 0, because '0' cannot stand alone and 30 > 26, while "10" can only be decoded as 'J'. Two variables replace the dp array, so the space is O(1). A Goldman candidate reported this in the CoderPad round. Be ready for "Decode Ways II", where '*' is a wildcard and the answer is taken modulo 1e9+7.''',
"O(n)", "O(1)", "https://leetcode.com/problems/decode-ways/"),

C("Pow(x, n)", "Medium", ["Goldman Sachs", "JP Morgan", "Amazon", "Microsoft"],
'''Implement `myPow(x, n)`, which computes x raised to the integer power n, without using `Math.pow`.

**Example**
```
myPow(2.00000, 10)  -> 1024.00000
myPow(2.10000, 3)   -> 9.26100
myPow(2.00000, -2)  -> 0.25000
```
**Constraints**
- -100.0 < x < 100.0
- -2^31 <= n <= 2^31 - 1
- the result fits in a double''',
["Binary exponentiation: x^n = (x^2)^(n/2), multiplied by one extra x when n is odd.",
 "Negating Integer.MIN_VALUE overflows, so convert n to long first."],
r'''
class Solution {
    public double myPow(double x, int n) {
        long N = n;                    // avoid overflow on -Integer.MIN_VALUE
        if (N < 0) {
            x = 1 / x;
            N = -N;
        }
        double result = 1;
        while (N > 0) {
            if ((N & 1) == 1) result *= x;  // current bit set
            x *= x;                          // square for next bit
            N >>= 1;
        }
        return result;
    }
}
''',
'''Multiplying x by itself n times is O(n), which is too slow for n near 2^31. Binary (fast) exponentiation looks at the bits of n. At each step, x is squared to represent x^(2^k), and it is multiplied into the result only when bit k of n is set. That takes O(log n) multiplications. Negative exponents are handled by inverting x. The classic bug is `n = -n` when n is `Integer.MIN_VALUE`, which overflows back to itself, so widen to `long` first. The same technique powers modular exponentiation `(a^b) % m` in number-theory questions and fast matrix exponentiation for Fibonacci.''',
"O(log n)", "O(1)", "https://leetcode.com/problems/powx-n/"),

C("Count Primes", "Medium", ["JP Morgan", "Goldman Sachs", "Microsoft", "Amazon"],
'''Given an integer `n`, return the number of prime numbers that are strictly less than `n`.

**Example**
```
n = 10 -> 4    (2, 3, 5, 7)
n = 0  -> 0
n = 1  -> 0
```
**Constraints**
- 0 <= n <= 5 * 10^6''',
["Checking each number by trial division is about O(n * sqrt(n)), which is too slow. Mark the composites instead.",
 "Sieve of Eratosthenes: for each prime p with p * p < n, cross out p*p, p*p + p, and so on."],
r'''
class Solution {
    public int countPrimes(int n) {
        if (n < 3) return 0;
        boolean[] composite = new boolean[n];
        int count = 0;
        for (int i = 2; i < n; i++) {
            if (composite[i]) continue;
            count++;
            if ((long) i * i < n) {
                for (int j = i * i; j < n; j += i) composite[j] = true;
            }
        }
        return count;
    }
}
''',
'''The Sieve of Eratosthenes takes each number not yet crossed out (a prime) and crosses out its multiples. Crossing starts at `p * p`, because smaller multiples such as 2p and 3p were already crossed out by smaller primes. Only primes up to sqrt(n) do any crossing, and the `(long)` cast stops `i * i` from overflowing. The total work is n x (1/2 + 1/3 + 1/5 + ...) = O(n log log n). The answer is counted in the same pass. For memory, a `BitSet` or an odd-numbers-only sieve halves the space. Banks like JP Morgan often pair this with "check whether a single number is prime" (trial division up to sqrt(n)) and the follow-up "segmented sieve" for very large ranges.''',
"O(n log log n)", "O(n)", "https://leetcode.com/problems/count-primes/"),
]

theory = [
T("What is the difference between a process and a thread?",
'''A **process** is an independent program in execution with its own virtual address space, heap, code, file descriptors and security context. Processes are isolated, so a crash in one does not corrupt another, but creating them and communicating between them (IPC through pipes, sockets or shared memory) is expensive. A **thread** is a unit of execution inside a process. Threads share the heap, code and open resources, but each has its own stack, program counter and registers. Threads are cheap to create and switch between, and communicate through shared memory, which brings race conditions and the need for synchronization. A JVM is one process. Your Spring Boot application handles requests on a Tomcat thread pool (200 threads by default), with GC and JIT threads running alongside. Chrome uses separate processes per tab for isolation, a classic example of the trade-off.''',
["Goldman Sachs", "JP Morgan", "Oracle", "Microsoft"]),

T("Explain virtual memory, paging and what happens on a page fault.",
'''**Virtual memory** gives each process the illusion of a large private, contiguous address space, mapped onto physical RAM and backed by disk. Memory is divided into fixed-size **pages** (virtual) and **frames** (physical), typically 4 KB. The **page table** maps page numbers to frame numbers, and the **TLB** caches recent translations so most lookups avoid walking the table. A **page fault** happens when the page is not in RAM: the CPU traps to the OS, which checks that the access is valid (if not, the process gets a segmentation fault), finds a free frame or evicts one using LRU-like replacement (writing it to disk first if it is dirty), loads the page from disk, updates the page table and restarts the instruction. The benefits are isolation, running programs larger than RAM, shared libraries, and copy-on-write `fork()`. Too many faults leads to thrashing.''',
["Goldman Sachs", "Microsoft", "JP Morgan"]),

T("Describe the JVM memory areas. When do you get StackOverflowError vs OutOfMemoryError?",
'''The **heap** is shared by all threads and holds objects and arrays. It is split into the young generation (Eden plus survivor spaces) and the old generation, and is sized with `-Xms` and `-Xmx`. Each thread has its own **stack** of frames holding local variables, operand stacks and return addresses, sized with `-Xss`. **Metaspace** (native memory since Java 8, replacing PermGen) stores class metadata. There are also PC registers, native method stacks and the code cache for JIT-compiled code. **StackOverflowError** happens when a thread's stack is exhausted, almost always by unbounded or very deep recursion. **OutOfMemoryError** comes in several forms: "Java heap space" (a leak, such as an ever-growing static map or cache, or a heap that is simply too small), "Metaspace" (classloader leaks), "GC overhead limit exceeded", or "unable to create native thread". To diagnose, take a heap dump (`-XX:+HeapDumpOnOutOfMemoryError`) and analyse it with Eclipse MAT.''',
["JP Morgan", "Goldman Sachs", "Oracle", "PhonePe"]),

T("How does garbage collection work in Java? Name the collectors you know.",
'''The GC reclaims objects that are no longer reachable from **GC roots**: thread stacks, static fields, JNI references and active monitors. Reference counting is not used, so cycles are collected too. It relies on the **generational hypothesis**: most objects die young. New objects go into Eden. A **minor GC** copies the survivors into survivor spaces, and objects that survive several cycles are promoted to the old generation. **Major or full GCs** clean the old generation and are more expensive. The phases are mark, sweep and compact, or copy. Collectors: **Serial** (single-threaded), **Parallel** (throughput-focused), **G1** (the default since Java 9; splits the heap into regions, collects the most-garbage regions first, and targets a pause goal via `-XX:MaxGCPauseMillis`), and **ZGC/Shenandoah** (concurrent, with sub-millisecond pauses on very large heaps). To tune, read GC logs, size the heap correctly, and reduce allocation rather than just switching flags.''',
["JP Morgan", "Goldman Sachs", "Oracle", "Walmart"]),

T("Is Java pass-by-value or pass-by-reference? Explain with an example.",
'''Java is **strictly pass-by-value**. For primitives, the value itself is copied. For objects, the *reference* is copied: the method gets its own copy of a pointer to the same object. So a method **can mutate** the object's state (`list.add(x)` is visible to the caller) but **cannot reassign** the caller's variable (`list = new ArrayList<>()` inside the method only changes the local copy). For example, a `swap(Integer a, Integer b)` method never swaps the caller's variables. That is why swapping needs an array or a holder object. Immutable types such as String and Integer can look like pass-by-value of the content, because they cannot be mutated at all. Interviewers usually show a `change(StringBuilder sb)` snippet that both appends and reassigns, and ask for the output.''',
["JP Morgan", "Goldman Sachs", "SAP"]),

T("Explain the producer-consumer problem and how you would solve it in Java.",
'''Producers add items to a bounded buffer and consumers remove them. Producers must wait when the buffer is full, consumers must wait when it is empty, and access to the buffer must be mutually exclusive. The classic OS solution uses three semaphores: `empty = N`, `full = 0` and a `mutex`. In Java, the low-level version uses `synchronized` with `while (queue.size() == cap) wait();` and `notifyAll()` after every change. Use `while` rather than `if`, because of spurious wakeups. The cleaner version is `ReentrantLock` with two `Condition`s, `notFull` and `notEmpty`. The production answer is `BlockingQueue` (`ArrayBlockingQueue` or `LinkedBlockingQueue`) with `put()` and `take()`, which block automatically. This is how `ThreadPoolExecutor` hands tasks to workers. At the system level, Kafka or RabbitMQ play the role of the buffer between microservices, with backpressure.''',
["Goldman Sachs", "Microsoft", "JP Morgan", "Oracle"]),
]

DAY = build(5, "Goldman Sachs & JP Morgan", "Math and aptitude-style coding from Goldman Sachs CoderPad and JP Morgan rounds, tricky Java output prediction, and operating-systems MCQs.", mcqs, coding, theory)
