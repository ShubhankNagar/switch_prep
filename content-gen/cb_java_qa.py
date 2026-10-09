from cb_common import B, I, A

QA = [
("What are the four pillars of OOP? Explain each with a Java example.", r'''
- **Encapsulation**: hide state behind methods that enforce rules. `BankAccount` keeps `balance` private and validates in `deposit()`.
- **Abstraction**: expose *what*, hide *how*. A `PaymentGateway` interface with `charge()`; callers don't know if Razorpay or Stripe is used.
- **Inheritance**: reuse via "is-a". `SavingsAccount extends Account`. Java allows one superclass but many interfaces.
- **Polymorphism**: one reference type, many behaviours. Overloading is compile-time; overriding is runtime (dynamic dispatch).

```java
PaymentGateway g = new RazorpayGateway();
g.charge(order);   // runtime decides which implementation runs
```
Tie it to your project: e.g. multiple `NotificationSender` beans injected as a list and chosen by type.
''', B, ["oop"], True),

("What is the difference between an abstract class and an interface in Java 8+?", r'''
| Abstract class | Interface |
|---|---|
| Can have instance fields and constructors | Only `public static final` constants, no constructors |
| Any access modifiers on methods | Abstract, `default`, `static`, `private` (Java 9) methods |
| Single inheritance | A class can implement many |
| Models "is-a" with shared state/code | Models a capability/contract ("can-do") |

Use an abstract class when related classes share state and partial implementation (template method pattern). Use an interface to define a contract that unrelated classes can implement (`Comparable`, `Runnable`), and for DI in Spring. Default methods were added so existing interfaces (like `Collection`) could evolve without breaking implementations. If two interfaces have the same default method, the class must override and pick with `A.super.m()`.
''', B, ["oop", "interface"], True),

("Method overloading vs overriding — what are the rules?", r'''
**Overloading** (compile-time polymorphism): same method name, different parameter list (number/type/order) in the same class. Return type alone can't differ.

**Overriding** (runtime polymorphism): subclass redefines a parent method with the same signature.
Rules for overriding:
- Return type same or covariant (subtype).
- Access can't be narrower (`protected` -> `public` allowed).
- Can't throw new or broader **checked** exceptions.
- `final`, `static` and `private` methods can't be overridden. Static methods with the same signature are **hidden**, chosen by reference type.
- Use `@Override` to let the compiler catch mistakes.

```java
class A { static void s(){print("A");} void i(){print("A");} }
class B extends A { static void s(){print("B");} void i(){print("B");} }
A x = new B(); x.s(); /* A */ x.i(); /* B */
```
''', B, ["oop"], True),

("Can we override a static or private method? Can we overload main()?", r'''
- **Static methods**: No. Declaring the same static method in a subclass *hides* the parent's; the call is resolved by the reference type at compile time, not the object type.
- **Private methods**: No. They're not visible to subclasses; a same-named method in the subclass is an unrelated new method.
- **main()**: Yes, it can be overloaded (`main(int x)`), but the JVM only calls `public static void main(String[] args)` as the entry point. It can't be overridden in the polymorphic sense because it's static.
- **Constructors**: can be overloaded, never overridden (not inherited).
''', B, ["oop"], False),

("Why is String immutable in Java?", r'''
`String` is `final` and its internal `byte[]` is `private final` with no mutators. Reasons:
1. **String pool** — literals are shared between references; mutation would affect everyone.
2. **Security** — DB URLs, file paths, class names, usernames can't be altered after validation.
3. **Thread safety** — immutable objects need no synchronization.
4. **Hash caching** — `hashCode` is computed once and cached, making Strings fast and safe `HashMap` keys.
5. **Class loading** relies on string names that must not change.

The trade-off is that repeated modification creates garbage; use `StringBuilder` for that.
''', B, ["string"], True),

("How many objects are created by `String s = new String(\"hello\")`? What's the String pool?", r'''
**One or two.** The literal `"hello"` is placed in the String pool if not already present (one object), and `new` always creates a separate object on the heap (second object). `s` refers to the heap object.

The **String pool** is a special area (in the heap since Java 7) where string literals are interned so identical literals share one object.
```java
String a = "hello", b = "hello";
String c = new String("hello");
a == b;            // true
a == c;            // false
a == c.intern();   // true - intern returns pooled copy
a.equals(c);       // true
```
Always use `equals()` for content comparison.
''', B, ["string"], True),

("String vs StringBuilder vs StringBuffer?", r'''
| | String | StringBuilder | StringBuffer |
|---|---|---|---|
| Mutability | Immutable | Mutable | Mutable |
| Thread safety | Safe (immutable) | Not synchronized | Synchronized methods |
| Performance | Each change = new object | Fastest | Slower due to locking |
| Since | 1.0 | 1.5 | 1.0 |

Use `String` for fixed values, `StringBuilder` for building strings in a loop (local variable — no sharing), and `StringBuffer` rarely (legacy). Concatenation with `+` in a loop is O(n^2) because each iteration copies.
```java
StringBuilder sb = new StringBuilder();
for (String w : words) sb.append(w).append(',');
```
''', B, ["string"], True),

("What is the equals() and hashCode() contract? What happens if you override only equals()?", r'''
Contract: if `a.equals(b)` then `a.hashCode() == b.hashCode()`. Equal hash codes do not imply equality. `equals` must be reflexive, symmetric, transitive, consistent, and false for null.

If you override only `equals`, two logically equal objects will usually have different identity hash codes. Hash-based collections look up the **bucket by hashCode first**, so:
```java
Set<Emp> s = new HashSet<>();
s.add(new Emp(1));
s.contains(new Emp(1)); // false
s.add(new Emp(1));      // duplicate stored
```
Fix: override both, using the same fields, e.g. `Objects.hash(id, email)`. Records and Lombok `@EqualsAndHashCode` generate them consistently.
''', B, ["equals-hashcode", "collections"], True),

("Explain the internal working of HashMap in Java 8.", r'''
- Backed by `Node<K,V>[] table` (default capacity 16, load factor 0.75).
- **put**: compute `hash = h ^ (h >>> 16)` of `key.hashCode()`; index = `(n-1) & hash`. If bucket empty, insert. Else traverse: if a node's key `equals` the new key, replace the value; otherwise append to the list.
- **Treeification**: when a bucket exceeds 8 nodes and capacity >= 64, it becomes a red-black tree (O(log n) lookups); it untreeifies at 6. If capacity < 64 it resizes instead.
- **Resize**: when size > capacity x load factor (12 by default), capacity doubles; each node either stays at index `i` or moves to `i + oldCap`.
- **get**: same hash/index, then `equals` within the bucket.
- Allows one null key (bucket 0) and many null values. Not thread-safe.

Average O(1) get/put; worst case O(log n) with tree bins.
''', I, ["hashmap", "collections"], True),

("Why is HashMap capacity always a power of two? What is the load factor?", r'''
With capacity `n` a power of two, `(n - 1) & hash` is equivalent to `hash % n` but much faster (a bitwise AND), and it uses all low bits evenly. That's also why HashMap spreads the hash with `h ^ (h >>> 16)` — so high bits influence the index. If you pass `new HashMap<>(100)`, it rounds up to 128.

The **load factor** (default 0.75) controls when to resize: threshold = capacity x load factor. 0.75 is a trade-off — lower means fewer collisions but more memory; higher saves memory but increases collisions. If you know the expected size, pre-size to avoid repeated resizing: `new HashMap<>((int)(expected / 0.75f) + 1)` or Java 19's `HashMap.newHashMap(expected)`.
''', I, ["hashmap"], False),

("What is a hash collision and how does HashMap handle it?", r'''
A collision happens when two different keys map to the same bucket index (either the same hashCode or different hashCodes that produce the same index). HashMap uses **separate chaining**: entries in the same bucket are stored as a linked list, and from Java 8 the list converts to a **red-black tree** once it exceeds 8 nodes (with table size >= 64). Lookups in the bucket compare hash first, then `equals()`.

A poor `hashCode()` (e.g. returning a constant) puts everything in one bucket, degrading performance to O(n) (or O(log n) with treeification if keys are `Comparable`). Good hashCode implementations use all significant fields, e.g. `Objects.hash(...)`.
''', I, ["hashmap"], False),

("HashMap vs Hashtable vs ConcurrentHashMap vs synchronizedMap?", r'''
| | HashMap | Hashtable | synchronizedMap | ConcurrentHashMap |
|---|---|---|---|---|
| Thread-safe | No | Yes | Yes | Yes |
| Locking | None | Whole table (every method synchronized) | Whole map (wrapper mutex) | Bucket-level (CAS + synchronized on bin head), lock-free reads |
| Null key/values | 1 null key, null values | None | Depends on backing map | None |
| Iterator | Fail-fast | Fail-fast (enumerator not) | Fail-fast (must sync manually) | Weakly consistent |
| Performance | Best single-threaded | Poor | Poor under contention | Excellent under contention |

Use HashMap for single-thread/local use, ConcurrentHashMap for shared maps. Hashtable is legacy.
''', I, ["hashmap", "concurrency"], True),

("How does ConcurrentHashMap work internally in Java 8? Why doesn't it allow null?", r'''
Java 7 used 16 lock-striped segments. Java 8+ removed segments:
- Same array-of-bins structure as HashMap with tree bins.
- **Reads** are lock-free: node values and next pointers are `volatile`.
- **Writes to an empty bin** use **CAS**.
- **Writes to a non-empty bin** `synchronized` on the bin's first node — only that bucket is locked.
- **Resizing** is done cooperatively by multiple threads using `ForwardingNode` markers.
- `size()` uses striped counter cells (like `LongAdder`).

**No nulls** because in concurrent code `get(k) == null` would be ambiguous (absent vs mapped to null), and checking `containsKey` afterwards isn't atomic. Use `computeIfAbsent`, `merge`, `putIfAbsent` for atomic compound actions.
''', A, ["concurrenthashmap", "concurrency"], True),

("ArrayList vs LinkedList — when would you use each?", r'''
- **ArrayList**: dynamic array. O(1) random access, amortised O(1) append, O(n) insert/delete in the middle (shifting). Compact and CPU-cache friendly. Grows by 1.5x.
- **LinkedList**: doubly linked list. O(n) access by index, O(1) insert/remove at ends or at a known iterator position, but finding the position is O(n). Each node has extra overhead (two pointers + object header).

In practice ArrayList is faster for almost all workloads, even many middle insertions, due to cache locality. Use `ArrayDeque` for queue/stack operations instead of LinkedList. LinkedList is mainly useful when you frequently remove/insert via an `Iterator`/`ListIterator` while traversing.
''', B, ["collections"], True),

("How does ArrayList grow internally?", r'''
ArrayList holds an `Object[] elementData`. `new ArrayList<>()` starts with a shared empty array; the first `add` allocates capacity **10**. When full, `grow()` creates a new array of size `old + (old >> 1)` (i.e. **1.5x**) and copies elements with `Arrays.copyOf` (System.arraycopy). That's why append is amortised O(1).

Tips: if you know the size, use `new ArrayList<>(n)` or `ensureCapacity(n)` to avoid repeated copying; `trimToSize()` releases unused capacity. Removing elements does not shrink the array automatically.
''', I, ["collections"], False),

("Fail-fast vs fail-safe iterators? How do you avoid ConcurrentModificationException?", r'''
**Fail-fast** iterators (ArrayList, HashMap, HashSet) record `modCount` when created. If the collection is structurally modified other than through the iterator, the next `next()` throws `ConcurrentModificationException`. It's best-effort, not guaranteed.

**Fail-safe / weakly consistent** iterators (CopyOnWriteArrayList, ConcurrentHashMap) work on a snapshot or tolerate concurrent changes and never throw CME.

Avoiding CME while removing:
```java
list.removeIf(x -> x < 0);                         // best
Iterator<Integer> it = list.iterator();
while (it.hasNext()) if (it.next() < 0) it.remove(); // iterator's own remove
```
Don't call `list.remove()` inside a for-each loop.
''', I, ["collections"], True),

("HashSet vs LinkedHashSet vs TreeSet? How does HashSet ensure uniqueness?", r'''
- **HashSet**: backed by a `HashMap` (elements are keys, value is a dummy `PRESENT` object). No order, O(1) ops, allows one null.
- **LinkedHashSet**: backed by LinkedHashMap — keeps **insertion order**.
- **TreeSet**: backed by TreeMap (red-black tree) — **sorted** order, O(log n), uses `compareTo`/Comparator (not equals) for uniqueness, no null with natural ordering.

Uniqueness in HashSet comes from `HashMap.put`: `add(e)` returns false if a key with the same `hashCode` and `equals` already exists. So custom objects need correct equals/hashCode.
''', B, ["collections"], True),

("How does TreeMap work, and when would you use it over HashMap?", r'''
TreeMap is a **red-black tree** (self-balancing BST) that keeps keys sorted by natural order or a supplied Comparator. `get/put/remove` are O(log n). It offers navigation APIs: `firstKey`, `lastKey`, `floorKey`, `ceilingKey`, `headMap`, `tailMap`, `subMap`, `descendingMap`.

Use it when you need sorted keys or range queries: leaderboards, time-based buckets, finding the nearest price slab, scheduling.
```java
TreeMap<Integer, String> slabs = new TreeMap<>(Map.of(0,"NIL", 250000,"5%", 500000,"20%"));
slabs.floorEntry(320000).getValue(); // "5%"
```
It doesn't permit null keys with natural ordering, and isn't thread-safe (use `ConcurrentSkipListMap`).
''', I, ["collections", "treemap"], False),

("How would you implement an LRU cache in Java?", r'''
Easiest: extend `LinkedHashMap` with access-order and override `removeEldestEntry`.
```java
class LRUCache<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;
    LRUCache(int capacity) { super(capacity, 0.75f, true); this.capacity = capacity; }
    @Override protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;
    }
}
```
`accessOrder = true` moves an entry to the tail on every `get`/`put`; the head is least recently used.

In a DSA round they may want it from scratch: a `HashMap<K, Node>` plus a doubly linked list with dummy head/tail; `get` moves node to front; `put` inserts at front and evicts the tail when over capacity — all O(1). For thread safety, wrap with locks or use Caffeine in production.
''', I, ["collections", "design"], True),

("Comparable vs Comparator?", r'''
- `Comparable<T>` is implemented by the class itself: `int compareTo(T o)` — the **natural ordering** (one per class). Used by `Collections.sort(list)`, TreeMap keys.
- `Comparator<T>` is an external strategy: `int compare(T a, T b)` — you can define many orderings without modifying the class.

```java
emps.sort(Comparator.comparing(Emp::dept)
        .thenComparing(Emp::salary, Comparator.reverseOrder())
        .thenComparing(Emp::name));
```
Keep `compareTo` consistent with `equals`, because sorted collections treat `compareTo == 0` as duplicate. Avoid `a - b` style comparisons (overflow); use `Integer.compare`.
''', B, ["collections"], True),

("What are generics and what is type erasure?", r'''
Generics provide compile-time type safety and eliminate casts: `List<String>` only accepts Strings.

**Type erasure**: generic type info is removed by the compiler. Type parameters are replaced with their bound (or `Object`), casts are inserted, and bridge methods are generated. At runtime `List<String>` and `List<Integer>` are both just `ArrayList`.

Consequences:
- Can't do `new T()`, `new T[]`, `instanceof List<String>`.
- Can't overload methods differing only in generic type (`f(List<String>)` vs `f(List<Integer>)`).
- Can't use primitives as type arguments.
- Static fields can't be of type `T`.
It was chosen for backward compatibility with pre-Java-5 code. Workarounds: pass `Class<T>` tokens or `TypeReference`.
''', I, ["generics"], False),

("Explain wildcards `? extends` and `? super` (PECS).", r'''
- `List<? extends Number>`: any list of Number or subtype. You can **read** elements as `Number`, but can't add (compiler can't know the exact type). It's a **producer**.
- `List<? super Integer>`: list of Integer or a supertype. You can **add** Integers, but reads return `Object`. It's a **consumer**.

**PECS** — Producer Extends, Consumer Super:
```java
static double sum(List<? extends Number> nums) { double s=0; for (Number n: nums) s+=n.doubleValue(); return s; }
static void fill(List<? super Integer> out) { out.add(1); out.add(2); }
```
`Collections.copy(List<? super T> dest, List<? extends T> src)` is the classic JDK example. Generics are invariant: `List<Integer>` is not a `List<Number>`.
''', I, ["generics"], False),

("Checked vs unchecked exceptions? When do you use each?", r'''
- **Checked** (subclasses of `Exception` but not `RuntimeException`): compiler forces catch or `throws`. Examples: `IOException`, `SQLException`. Use for recoverable conditions outside your control.
- **Unchecked** (`RuntimeException` and subclasses): no compile-time enforcement. Examples: `NullPointerException`, `IllegalArgumentException`. Represent programming errors or business rule violations.
- **Errors** (`OutOfMemoryError`, `StackOverflowError`): serious JVM problems; don't catch.

Modern Spring code mostly uses unchecked custom exceptions (e.g. `ResourceNotFoundException`) handled centrally by `@RestControllerAdvice`. Note: `@Transactional` rolls back by default only for unchecked exceptions and Errors, not checked ones (unless `rollbackFor` is set).
''', B, ["exceptions"], True),

("Does finally always execute? What happens with return in try and finally?", r'''
`finally` runs after `try`/`catch` whether or not an exception occurs, even if `try` has a `return`. It does **not** run if the JVM exits (`System.exit`), crashes, or the thread is killed, or in an infinite loop in try.

```java
static int f() {
    try { return 1; }
    finally { return 2; }   // returns 2; also swallows any exception from try!
}
static int g() {
    int x = 1;
    try { return x; }       // value 1 is saved
    finally { x = 5; }      // doesn't change the returned value -> 1
}
```
Never `return` or throw from `finally` — it hides the original result/exception. Prefer try-with-resources for cleanup.
''', I, ["exceptions"], True),

("What is try-with-resources and what are suppressed exceptions?", r'''
Introduced in Java 7, it automatically closes resources that implement `AutoCloseable`, in reverse order of declaration, even if exceptions occur.
```java
try (BufferedReader br = Files.newBufferedReader(path);
     Connection con = ds.getConnection()) {
    ...
}
```
If the body throws and then `close()` also throws, the close exception doesn't replace the original — it's attached as a **suppressed** exception, retrievable with `e.getSuppressed()`. With old try/finally, the close exception would hide the real one. Java 9 allows effectively final variables: `try (br) { ... }`.
''', B, ["exceptions"], False),

("How do you create a custom exception, and how do you handle exceptions globally in a Spring Boot app?", r'''
```java
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String msg) { super(msg); }
}

@RestControllerAdvice
public class GlobalHandler {
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ProblemDetail> notFound(ResourceNotFoundException ex) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        return ResponseEntity.status(404).body(pd);
    }
}
```
Extend `RuntimeException` for business errors (no forced `throws`), add useful context (ids), keep the cause when wrapping. Spring 6 / Boot 3 support RFC 7807 `ProblemDetail` responses.
''', B, ["exceptions", "spring"], True),

("What is a functional interface? Name the important ones in java.util.function.", r'''
An interface with exactly **one abstract method** (SAM); it can be the target of a lambda or method reference. `@FunctionalInterface` makes the compiler enforce this. Default/static methods and `Object` methods don't count.

| Interface | Abstract method |
|---|---|
| `Predicate<T>` | `boolean test(T)` |
| `Function<T,R>` | `R apply(T)` |
| `Consumer<T>` | `void accept(T)` |
| `Supplier<T>` | `T get()` |
| `BiFunction<T,U,R>` | `R apply(T,U)` |
| `UnaryOperator<T>`, `BinaryOperator<T>` | same-type operations |

Older examples: `Runnable`, `Callable`, `Comparator`. Composition: `Predicate.and/or/negate`, `Function.andThen/compose`.
''', B, ["java8", "lambda"], True),

("Why must local variables used in a lambda be effectively final?", r'''
A lambda captures the **value** of a local variable, not the variable itself (locals live on the stack frame, which may be gone when the lambda runs later, possibly on another thread). If mutation were allowed, the lambda's copy and the original could diverge and you'd get race conditions. So Java requires captured locals to be final or effectively final (never reassigned).

```java
int count = 0;
list.forEach(x -> count++);         // compile error
AtomicInteger c = new AtomicInteger();
list.forEach(x -> c.incrementAndGet()); // ok - reference is final, object mutable
```
Instance and static fields can be modified because they live on the heap (accessed via `this`). Better: use `stream().count()` instead of mutating.
''', I, ["java8", "lambda"], False),

("What is Optional? What is the difference between orElse and orElseGet?", r'''
`Optional<T>` is a container that may hold a value, intended as a **method return type** to signal "may be absent" and avoid null checks/NPEs.

```java
String name = repo.findById(id).map(User::getName).orElse("guest");
User u = repo.findById(id).orElseThrow(() -> new NotFoundException(id));
```
- `orElse(x)`: `x` is **always evaluated**, even if a value is present.
- `orElseGet(supplier)`: supplier runs **only** when empty — use it for expensive defaults (DB/API calls, object creation).

Best practices: don't use Optional for fields, parameters or collections; never call `get()` without a check (prefer `orElseThrow()`); use `Optional.ofNullable` for possibly-null values.
''', B, ["java8", "optional"], True),

("map() vs flatMap() in streams?", r'''
- `map` transforms each element to exactly one element: `Stream<T> -> Stream<R>`.
- `flatMap` transforms each element to a **stream** and flattens them into one: one-to-many.

```java
List<String> sentences = List.of("hello world", "java streams");
sentences.stream().map(s -> s.split(" "));                 // Stream<String[]>
sentences.stream().flatMap(s -> Arrays.stream(s.split(" ")))
         .toList();                                          // [hello, world, java, streams]

orders.stream().flatMap(o -> o.getItems().stream())          // all items across orders
      .mapToDouble(Item::price).sum();
```
Same idea for Optional: `Optional.flatMap` avoids `Optional<Optional<T>>`.
''', B, ["streams"], True),

("Intermediate vs terminal operations; what is lazy evaluation in streams?", r'''
- **Intermediate** ops (`filter`, `map`, `sorted`, `distinct`, `limit`) return a new Stream and are **lazy** — they only build the pipeline.
- **Terminal** ops (`collect`, `forEach`, `reduce`, `count`, `findFirst`, `anyMatch`) trigger processing and close the stream.

Elements flow one at a time through the whole pipeline (vertical processing), so short-circuiting ops stop early:
```java
Stream.of(1,2,3,4,5)
    .filter(x -> { System.out.println("f" + x); return x % 2 == 0; })
    .findFirst();   // prints f1, f2 only
```
A stream can be consumed only once; reusing throws `IllegalStateException`. Stateful ops like `sorted` must consume all input before emitting.
''', I, ["streams"], True),

("Using streams, group employees by department and count them; also find the average salary per department.", r'''
```java
record Emp(String name, String dept, double salary) {}

Map<String, Long> countByDept = emps.stream()
    .collect(Collectors.groupingBy(Emp::dept, Collectors.counting()));

Map<String, Double> avgByDept = emps.stream()
    .collect(Collectors.groupingBy(Emp::dept, Collectors.averagingDouble(Emp::salary)));

// sorted by dept name
Map<String, Long> sorted = emps.stream()
    .collect(Collectors.groupingBy(Emp::dept, TreeMap::new, Collectors.counting()));

// department with max employees
String biggest = countByDept.entrySet().stream()
    .max(Map.Entry.comparingByValue()).map(Map.Entry::getKey).orElse(null);
```
`groupingBy(classifier, mapFactory, downstream)` — the downstream collector (counting, averaging, mapping, maxBy, summingDouble) decides what each group becomes.
''', I, ["streams", "coding"], True),

("Find the second highest salary using Java streams.", r'''
```java
Optional<Double> second = emps.stream()
    .map(Emp::salary)
    .distinct()                              // handle duplicate top salaries
    .sorted(Comparator.reverseOrder())
    .skip(1)
    .findFirst();

// the employee(s) earning it
List<Emp> who = second.map(s -> emps.stream().filter(e -> e.salary() == s).toList())
                      .orElse(List.of());
// Nth highest: skip(n - 1)
```
For a plain `int[]`: `Arrays.stream(a).boxed().distinct().sorted(Comparator.reverseOrder()).skip(1).findFirst()`.
Interviewers often follow up: complexity is O(n log n) due to sorting; an O(n) approach tracks `first` and `second` in a single loop.
''', I, ["streams", "coding"], True),

("Find duplicate elements in a list using streams.", r'''
```java
List<Integer> nums = List.of(1, 2, 3, 2, 4, 3, 5);

// Approach 1: Set.add returns false for repeats
Set<Integer> seen = new HashSet<>();
Set<Integer> dups = nums.stream().filter(n -> !seen.add(n)).collect(Collectors.toSet());

// Approach 2: frequency map (no external state - preferred)
Set<Integer> dups2 = nums.stream()
    .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()))
    .entrySet().stream()
    .filter(e -> e.getValue() > 1)
    .map(Map.Entry::getKey)
    .collect(Collectors.toSet());

// Approach 3: Collections.frequency (O(n^2))
nums.stream().filter(n -> Collections.frequency(nums, n) > 1).distinct().toList();
```
Approach 1 is not safe for parallel streams because of the shared HashSet.
''', I, ["streams", "coding"], True),

("Find the first non-repeating character in a string using streams.", r'''
```java
String s = "swiss";
Character result = s.chars()
    .mapToObj(c -> (char) c)
    .collect(Collectors.groupingBy(Function.identity(),
             LinkedHashMap::new,          // preserve encounter order
             Collectors.counting()))
    .entrySet().stream()
    .filter(e -> e.getValue() == 1)
    .map(Map.Entry::getKey)
    .findFirst()
    .orElse(null);   // 'w'
```
The key is `LinkedHashMap::new` — a plain HashMap loses order. First *repeating* character: change the filter to `> 1`. Non-stream O(n): `int[256]` counts then a second pass over the string.
''', I, ["streams", "coding", "string"], True),

("Stream coding: highest-paid employee in each department, and names of employees grouped by department.", r'''
```java
Map<String, Emp> topPerDept = emps.stream()
    .collect(Collectors.toMap(Emp::dept, Function.identity(),
             BinaryOperator.maxBy(Comparator.comparingDouble(Emp::salary))));

// or with groupingBy + collectingAndThen to unwrap Optional
Map<String, Emp> top2 = emps.stream().collect(Collectors.groupingBy(Emp::dept,
    Collectors.collectingAndThen(
        Collectors.maxBy(Comparator.comparingDouble(Emp::salary)), Optional::get)));

Map<String, List<String>> namesByDept = emps.stream()
    .collect(Collectors.groupingBy(Emp::dept,
             Collectors.mapping(Emp::name, Collectors.toList())));
```
`collectingAndThen` applies a finishing function to the downstream result.
''', I, ["streams", "coding"], True),

("Stream coding: partition numbers into even/odd, sum of squares of odd numbers, and sort a map by value.", r'''
```java
Map<Boolean, List<Integer>> parts = nums.stream()
    .collect(Collectors.partitioningBy(n -> n % 2 == 0));   // true -> evens

int sumSqOdd = nums.stream().filter(n -> n % 2 != 0).mapToInt(n -> n * n).sum();

LinkedHashMap<String, Integer> byValueDesc = map.entrySet().stream()
    .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue,
             (a, b) -> a, LinkedHashMap::new));   // keep sorted order

// Count words, top 3 most frequent
Arrays.stream(text.toLowerCase().split("\\W+"))
    .collect(Collectors.groupingBy(w -> w, Collectors.counting()))
    .entrySet().stream()
    .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
    .limit(3).map(Map.Entry::getKey).toList();
```
''', I, ["streams", "coding"], True),

("Stream coding: join list of strings, find max/min, check palindromes, and convert a List to a Map.", r'''
```java
String joined = names.stream().collect(Collectors.joining(", ", "[", "]"));

int max = nums.stream().mapToInt(Integer::intValue).max().orElseThrow();
Optional<String> longest = names.stream().max(Comparator.comparingInt(String::length));

List<String> palindromes = words.stream()
    .filter(w -> new StringBuilder(w).reverse().toString().equalsIgnoreCase(w)).toList();

// List -> Map: id -> employee (merge function avoids IllegalStateException on duplicate keys)
Map<Long, Emp> byId = emps.stream()
    .collect(Collectors.toMap(Emp::id, Function.identity(), (a, b) -> a));

// Reverse each word in a sentence
String rev = Arrays.stream(s.split(" "))
    .map(w -> new StringBuilder(w).reverse()).collect(Collectors.joining(" "));
```
''', B, ["streams", "coding"], True),

("What is the difference between Collectors.toList() and Stream.toList()?", r'''
- `Collectors.toList()` (Java 8): returns a list with no guarantees on type/mutability; in practice a mutable `ArrayList`, and it accepts nulls.
- `Stream.toList()` (Java 16): returns an **unmodifiable** list (calling `add` throws `UnsupportedOperationException`), allows nulls, and is slightly more efficient.
- `Collectors.toUnmodifiableList()` (Java 10): unmodifiable and **rejects nulls**.

Choose `toList()` for read-only results (most cases) and `Collectors.toCollection(ArrayList::new)` when the caller must modify the list.
''', B, ["streams"], False),

("When should you use parallel streams? What are the pitfalls?", r'''
`parallelStream()` splits data with a `Spliterator` and processes chunks on the common `ForkJoinPool` (parallelism = cores - 1).

Use when: large data sets (tens of thousands+), CPU-intensive, stateless and independent operations, easily-splittable sources (arrays, ArrayList, ranges).

Pitfalls:
- Overhead makes small collections slower.
- Shared common pool — blocking I/O in one parallel stream starves others (bad in web servers).
- Side effects/shared mutable state cause race conditions.
- Ordering costs: `findFirst`, `forEachOrdered`, `limit` on ordered streams are expensive; use `findAny` / `unordered()`.
- LinkedList and `Stream.iterate` split poorly.
Always measure before using.
''', I, ["streams", "concurrency"], False),

("What are records in Java? Can a record be a JPA entity?", r'''
Records (Java 16) are immutable data carriers:
```java
public record OrderDto(Long id, BigDecimal amount) {
    public OrderDto { if (amount.signum() < 0) throw new IllegalArgumentException(); }
}
```
The compiler generates private final fields, a canonical constructor, accessor methods (`id()`, not `getId()`), and `equals`, `hashCode`, `toString`. Records are implicitly final, extend `java.lang.Record`, can implement interfaces, have static fields/methods and compact constructors, but no extra instance fields.

They are ideal for DTOs, API request/response bodies, Kafka event payloads, and map keys. They **can't be JPA entities** because entities need a no-arg constructor, non-final mutable fields, and must be proxyable (subclassed). They work fine for JPA projections and `@Embeddable` (Hibernate 6.2+).
''', B, ["java17", "records"], True),

("What are sealed classes and how do they combine with pattern matching for switch?", r'''
Sealed classes/interfaces (Java 17) restrict which classes may extend them:
```java
sealed interface Payment permits Card, Upi, Wallet {}
record Card(String last4) implements Payment {}
record Upi(String vpa) implements Payment {}
final class Wallet implements Payment {}
```
Permitted subclasses must be `final`, `sealed`, or `non-sealed`.

Because the compiler knows all subtypes, Java 21's switch can be **exhaustive without a default**:
```java
String describe(Payment p) {
    return switch (p) {
        case Card c -> "card " + c.last4();
        case Upi(String vpa) when vpa.endsWith("@okhdfc") -> "HDFC UPI";
        case Upi u -> "UPI " + u.vpa();
        case Wallet w -> "wallet";
    };
}
```
Adding a new subtype makes non-exhaustive switches fail to compile — a safer alternative to the visitor pattern.
''', I, ["java17", "java21"], False),

("What are virtual threads in Java 21? How are they different from platform threads?", r'''
Virtual threads are lightweight threads scheduled by the JVM, multiplexed onto a small pool of **carrier** (platform/OS) threads.
- Platform thread: 1:1 with an OS thread, ~1MB stack, expensive; thousands max.
- Virtual thread: a heap object with a growable stack; millions possible. When it blocks on I/O (socket, JDBC, `sleep`), it **unmounts** and the carrier runs another virtual thread.

```java
try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
    ids.forEach(id -> ex.submit(() -> client.fetch(id)));
}
```
Spring Boot 3.2+: `spring.threads.virtual.enabled=true` makes Tomcat use them.
Benefits: simple blocking code with reactive-level throughput for I/O-bound apps. Caveats: no speedup for CPU-bound work; don't pool them; **pinning** inside `synchronized` blocks in Java 21-23 (fixed in 24); limit downstream concurrency with semaphores since DB pools are still finite.
''', I, ["java21", "concurrency"], True),

("What new features came in Java 11, 17 and 21 that you have used or know about?", r'''
**Java 11**: `var` in lambdas, `String.isBlank/strip/lines/repeat`, `Files.readString/writeString`, standard `HttpClient`, `Optional.isEmpty`, run single-file programs.

**Java 17**: records, sealed classes, pattern matching for `instanceof`, switch expressions, text blocks, helpful NPE messages, strong encapsulation of JDK internals.

**Java 21**: virtual threads, pattern matching for switch, record patterns, sequenced collections (`getFirst/getLast/reversed`), generational ZGC.

Spring Boot 3 requires Java 17+, so most product companies run 17 or 21 now. Mention which you actually used (e.g. "records for DTOs and switch expressions in our order-status mapper").
''', B, ["java11", "java17", "java21"], True),

("What is the difference between a process and a thread? Explain the thread lifecycle.", r'''
A **process** is an independent program with its own memory space; a **thread** is a unit of execution within a process that shares the heap with other threads but has its own stack and PC. Threads are cheaper to create and switch, but shared memory requires synchronization.

Thread states (`Thread.State`):
1. **NEW** — created, `start()` not called.
2. **RUNNABLE** — running or ready to run.
3. **BLOCKED** — waiting to enter a `synchronized` block held by another thread.
4. **WAITING** — `wait()`, `join()`, `LockSupport.park()` without timeout.
5. **TIMED_WAITING** — `sleep(ms)`, `wait(ms)`, `join(ms)`.
6. **TERMINATED** — `run()` finished.
''', B, ["multithreading"], True),

("What is the difference between calling start() and run() on a thread?", r'''
`start()` asks the JVM to create a new thread with its own call stack, moves it to RUNNABLE, and that new thread invokes `run()`. Calling `run()` directly is just a normal method call on the **current** thread — no concurrency.
```java
Thread t = new Thread(() -> System.out.println(Thread.currentThread().getName()));
t.run();   // prints "main"
t.start(); // prints "Thread-0"
```
Calling `start()` twice on the same Thread throws `IllegalThreadStateException`.
''', B, ["multithreading"], False),

("Runnable vs Callable? execute() vs submit()?", r'''
- `Runnable.run()` returns nothing and can't throw checked exceptions.
- `Callable<V>.call()` returns a value and can throw checked exceptions.

`ExecutorService`:
- `execute(Runnable)` — fire-and-forget; an exception goes to the thread's `UncaughtExceptionHandler` (and the worker thread dies and is replaced).
- `submit(Runnable/Callable)` — returns a `Future`; exceptions are captured inside it and rethrown as `ExecutionException` on `future.get()`. If you never call `get()`, the exception is silently lost — a common production bug.
```java
Future<Integer> f = pool.submit(() -> compute());
try { f.get(1, TimeUnit.SECONDS); } catch (ExecutionException e) { log.error("failed", e.getCause()); }
```
''', B, ["multithreading", "executor"], False),

("Difference between wait() and sleep()?", r'''
| wait() | sleep() |
|---|---|
| Method of `Object` | Static method of `Thread` |
| **Releases** the monitor lock | **Keeps** any locks held |
| Must be called inside `synchronized` (else `IllegalMonitorStateException`) | Can be called anywhere |
| Woken by `notify/notifyAll`, timeout, or interrupt | Wakes after timeout or interrupt |
| Used for inter-thread communication | Used to pause execution |

Always call `wait()` in a loop that re-checks the condition because of spurious wakeups:
```java
synchronized (lock) { while (!ready) lock.wait(); }
```
''', B, ["multithreading"], True),

("What does synchronized do? Method vs block synchronization?", r'''
`synchronized` acquires an object's intrinsic (monitor) lock, giving **mutual exclusion** (one thread in the critical section) and **visibility** (changes made before releasing are visible to the next thread acquiring the same lock). Locks are reentrant.

- Synchronized **instance method** locks `this`.
- Synchronized **static method** locks the `Class` object.
- Synchronized **block** locks any chosen object and covers only the needed code — finer-grained, better throughput.
```java
private final Object lock = new Object();
void add(Item i) {
    validate(i);                 // outside lock
    synchronized (lock) { items.add(i); }
}
```
Use a private final lock object so external code can't lock on it and cause deadlocks. Note: in Java 21-23, blocking inside synchronized pins virtual threads.
''', I, ["multithreading", "synchronization"], True),

("What is volatile? Is volatile enough to make count++ thread-safe?", r'''
`volatile` guarantees **visibility** (every read sees the latest write, values aren't cached in CPU registers/caches) and **ordering** (prevents reordering around the variable, establishing happens-before). It does **not** provide atomicity.

`count++` is three steps — read, add, write — so two threads can read the same value and lose an update even if `count` is volatile. Fix with `AtomicInteger.incrementAndGet()`, `LongAdder`, or `synchronized`.

Good uses of volatile: a shutdown flag read by a worker loop; publishing an immutable object reference; double-checked locking singletons.
''', I, ["multithreading", "volatile"], True),

("What are atomic classes and how does CAS work?", r'''
`java.util.concurrent.atomic` (`AtomicInteger`, `AtomicLong`, `AtomicBoolean`, `AtomicReference`, `LongAdder`) provides lock-free thread-safe operations built on **Compare-And-Swap** — a CPU instruction that atomically sets a variable to a new value *only if* it still holds the expected value.
```java
// conceptually, incrementAndGet:
do { old = value; next = old + 1; } while (!compareAndSet(old, next));
```
No blocking, no context switches; under heavy contention spins retry. `LongAdder` reduces contention by spreading updates across cells and summing on read — better for high-write counters (metrics).

The **ABA problem** (value changes A->B->A unnoticed) is solved with `AtomicStampedReference`.
''', I, ["concurrency"], False),

("ReentrantLock vs synchronized?", r'''
Both provide mutual exclusion, reentrancy and visibility. `ReentrantLock` adds:
- `tryLock()` / `tryLock(timeout)` — avoid waiting forever (deadlock avoidance).
- `lockInterruptibly()` — waiting can be interrupted.
- **Fairness** option (longest waiting thread gets the lock).
- Multiple `Condition` objects (`await/signal`) vs a single wait-set.
- Query methods (`isLocked`, `getQueueLength`).

Downside: you must `unlock()` in `finally`, otherwise the lock leaks.
```java
lock.lock();
try { balance -= amt; } finally { lock.unlock(); }
```
Use `synchronized` for simple cases (less error-prone); use `ReentrantLock` when you need timeouts, fairness, or conditions — and with virtual threads on Java 21. `ReadWriteLock` allows concurrent readers.
''', I, ["concurrency", "locks"], True),

("What is a deadlock? How do you detect and prevent it?", r'''
A deadlock occurs when threads wait forever for locks held by each other:
```java
// Thread 1                 // Thread 2
synchronized (a) {          synchronized (b) {
  synchronized (b) {...}      synchronized (a) {...}
}                           }
```
Required conditions: mutual exclusion, hold-and-wait, no preemption, circular wait.

**Prevention:**
- Acquire locks in a consistent global order (e.g. lock the account with the smaller id first in a transfer).
- Use `tryLock(timeout)` and back off.
- Keep lock scope small; avoid calling external code while holding locks.
- Prefer concurrent utilities over manual locks.

**Detection:** take a thread dump (`jstack <pid>`, `jcmd <pid> Thread.print`, or VisualVM) — it reports "Found one Java-level deadlock" with the cycle. Programmatically, `ThreadMXBean.findDeadlockedThreads()`. In databases, deadlocks are detected by the DB and one transaction is rolled back.
''', I, ["concurrency", "deadlock"], True),

("Write a program where two threads print odd and even numbers alternately.", r'''
```java
public class OddEven {
    private int n = 1;
    private final int max = 10;

    private synchronized void print(int parity) {
        while (n <= max) {
            while (n <= max && n % 2 != parity) {
                try { wait(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); return; }
            }
            if (n <= max) {
                System.out.println(Thread.currentThread().getName() + ": " + n++);
                notifyAll();
            }
        }
    }
    public static void main(String[] args) {
        OddEven p = new OddEven();
        new Thread(() -> p.print(1), "odd").start();
        new Thread(() -> p.print(0), "even").start();
    }
}
```
Key points: shared monitor, condition checked in a `while`, `notifyAll` after each print. Alternatives: two `Semaphore`s, or `ReentrantLock` with two `Condition`s.
''', I, ["multithreading", "coding"], True),

("Implement producer-consumer in Java.", r'''
Simplest and production-grade: a `BlockingQueue`, which handles waiting internally.
```java
BlockingQueue<Integer> q = new ArrayBlockingQueue<>(5);

Thread producer = new Thread(() -> {
    try { for (int i = 0; i < 20; i++) q.put(i); }      // blocks when full
    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});
Thread consumer = new Thread(() -> {
    try { while (true) System.out.println(q.take()); }  // blocks when empty
    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});
producer.start(); consumer.start();
```
If asked to do it with `wait/notify`: guard with `synchronized`, producer waits `while (queue.size() == cap)`, consumer waits `while (queue.isEmpty())`, both `notifyAll()` after changing the queue. In distributed systems the same pattern is Kafka/RabbitMQ.
''', I, ["multithreading", "coding"], True),

("Explain the Executor framework and ThreadPoolExecutor parameters. Why avoid Executors.newFixedThreadPool in production?", r'''
Executors decouple task submission from thread management and reuse threads. `ThreadPoolExecutor(core, max, keepAlive, unit, workQueue, threadFactory, rejectedHandler)`:
1. Threads < core -> create a new thread.
2. Else -> put the task in the queue.
3. Queue full and threads < max -> create a thread.
4. Else -> rejection policy (`AbortPolicy` default, `CallerRunsPolicy`, `DiscardPolicy`, `DiscardOldestPolicy`).

`newFixedThreadPool` uses an **unbounded** `LinkedBlockingQueue` — under load, tasks pile up until OutOfMemoryError (and `max` is never used). `newCachedThreadPool` allows unbounded threads. Prefer:
```java
new ThreadPoolExecutor(8, 16, 60, TimeUnit.SECONDS,
    new ArrayBlockingQueue<>(500),
    new ThreadFactoryBuilder().setNameFormat("order-%d").build(), // Guava, or custom
    new ThreadPoolExecutor.CallerRunsPolicy());
```
Name threads, bound queues, and always `shutdown()` gracefully.
''', A, ["concurrency", "executor"], True),

("What is CompletableFuture? How do you call two services in parallel and combine results?", r'''
`CompletableFuture` is a `Future` you can complete manually and chain non-blocking callbacks on.
```java
ExecutorService io = Executors.newFixedThreadPool(20);
CompletableFuture<User> u = CompletableFuture.supplyAsync(() -> userSvc.get(id), io);
CompletableFuture<List<Order>> o = CompletableFuture.supplyAsync(() -> orderSvc.byUser(id), io);

Dashboard d = u.thenCombine(o, Dashboard::new)
    .completeOnTimeout(Dashboard.empty(), 2, TimeUnit.SECONDS)
    .exceptionally(ex -> { log.warn("fallback", ex); return Dashboard.empty(); })
    .join();
```
- `thenApply` = map, `thenCompose` = flatMap (dependent async call), `thenCombine` = merge two independent futures, `allOf/anyOf` for many.
- Error handling: `exceptionally`, `handle`, `whenComplete`.
- Without an executor, `*Async` uses the common ForkJoinPool — always pass a dedicated pool for blocking I/O.
''', A, ["concurrency", "completablefuture"], True),

("CountDownLatch vs CyclicBarrier vs Semaphore?", r'''
- **CountDownLatch(n)**: one or more threads `await()` until `countDown()` has been called n times. One-shot, not reusable. Example: main thread waits until 3 services are warmed up.
- **CyclicBarrier(n)**: n threads call `await()` and all block until the last arrives, then proceed together (optional barrier action). **Reusable**. Example: parallel simulation steps.
- **Semaphore(k)**: maintains k permits; `acquire()` blocks when none left, `release()` returns one. Limits concurrency, e.g. max 10 concurrent calls to a third-party API.
```java
Semaphore s = new Semaphore(10);
s.acquire(); try { callApi(); } finally { s.release(); }
```
''', I, ["concurrency"], False),

("What is ThreadLocal and what problems can it cause?", r'''
`ThreadLocal<T>` gives each thread its own independent copy of a variable.
```java
private static final ThreadLocal<String> TENANT = new ThreadLocal<>();
TENANT.set("acme"); ... TENANT.get(); ... TENANT.remove();
```
Uses: request/user context, MDC logging, Spring's `SecurityContextHolder` and transaction synchronization, non-thread-safe objects like `SimpleDateFormat`.

Problems:
- **Memory leaks / data bleed in thread pools**: pooled threads live forever, so values stay (and the next request may see the previous user's data). Always `remove()` in a `finally` / filter.
- Doesn't propagate to child/async threads automatically (`InheritableThreadLocal` or `TaskDecorator` needed).
- Virtual threads make heavy ThreadLocal use costly; Java's **ScopedValue** is the modern alternative.
''', I, ["concurrency"], False),

("How do you create a thread-safe Singleton?", r'''
Options:
1. **Eager**: `private static final Config INSTANCE = new Config();` — thread-safe via class init.
2. **Double-checked locking** with `volatile`:
```java
private static volatile Config inst;
public static Config get() {
    if (inst == null) synchronized (Config.class) { if (inst == null) inst = new Config(); }
    return inst;
}
```
`volatile` prevents another thread seeing a reference to a not-yet-constructed object due to reordering.
3. **Bill Pugh holder** — lazy and lock-free:
```java
private static class Holder { static final Config I = new Config(); }
public static Config get() { return Holder.I; }
```
4. **Enum** — `enum Config { INSTANCE; }` — also safe against reflection and serialization attacks (Effective Java's recommendation).
In Spring, beans are singletons per container by default, so you rarely write this manually.
''', I, ["design-patterns", "multithreading"], True),

("Explain JVM memory areas. Where are objects, local variables and static variables stored?", r'''
- **Heap** (shared): all objects and arrays, the String pool; split into Young (Eden, S0, S1) and Old generations. GC operates here.
- **Metaspace** (native memory, Java 8+): class metadata, method bytecode, constant pool. Replaced PermGen, grows dynamically (cap with `-XX:MaxMetaspaceSize`).
- **Stack** (per thread): one frame per method call holding local primitives, object references, partial results. `StackOverflowError` on deep recursion.
- **PC register** and **native method stack** (per thread).

Where things live: objects -> heap; local primitives and references -> stack; static variables -> with the `Class` object on the heap (since Java 8; metadata in Metaspace). Instance fields -> inside the object on the heap.
''', I, ["jvm"], True),

("How does garbage collection work? Explain young and old generations.", r'''
GC frees memory of objects **unreachable from GC roots** (thread stacks' locals, static fields, JNI refs, active threads). It uses tracing, not reference counting, so cycles are collected.

Generational heap (most objects die young):
1. New objects are allocated in **Eden**.
2. When Eden fills, a **Minor GC** marks live objects and copies them to a Survivor space (S0/S1), incrementing their age. Eden is then wiped — cheap because most objects are dead.
3. Objects surviving enough cycles (tenuring threshold) are **promoted** to the **Old generation**.
4. When old gen fills, a **Major/Full GC** runs mark-sweep-compact — slower with longer stop-the-world pauses.

You can't force GC; `System.gc()` is just a hint. Tune with `-Xms/-Xmx`, choose collectors (`-XX:+UseG1GC`, `-XX:+UseZGC`), and analyse with GC logs (`-Xlog:gc*`).
''', I, ["jvm", "gc"], True),

("Compare G1 GC and ZGC. Which is the default?", r'''
**G1 (Garbage First)** — default since Java 9.
- Heap split into equal regions (1-32 MB) that can be Eden, Survivor, Old or Humongous.
- Concurrent marking; then evacuates regions with the most garbage first.
- Pause-time goal (`-XX:MaxGCPauseMillis`, default 200ms); typical pauses tens of ms.
- Good general-purpose choice for heaps from a few GB.

**ZGC** — production since Java 15, generational in Java 21 (default mode from 23).
- Almost everything (marking, relocation/compaction) is concurrent using coloured pointers and load barriers.
- Sub-millisecond pauses independent of heap size (up to 16 TB).
- Slightly lower throughput / higher CPU and memory overhead.
- Use for latency-sensitive services (trading, real-time APIs) and huge heaps.

Others: Parallel GC (max throughput, batch jobs), Serial (tiny heaps), Shenandoah (low-pause alternative).
''', A, ["jvm", "gc"], False),

("Explain class loading and the parent delegation model.", r'''
Class loading happens lazily, on first active use:
1. **Loading** — find the `.class` bytes and create a `Class` object.
2. **Linking** — *verify* bytecode, *prepare* static fields with defaults, *resolve* symbolic references.
3. **Initialization** — run static initialisers and static blocks.

Loaders: **Bootstrap** (core JDK, native), **Platform** (Java 9+, formerly Extension), **Application/System** (your classpath), plus custom ones (Tomcat, Spring Boot's `LaunchedURLClassLoader`).

**Parent delegation**: a loader delegates to its parent first and only loads itself if the parent fails. This guarantees core classes like `java.lang.String` always come from Bootstrap (security) and avoids loading duplicates. A class's identity is its name + its loader, so the same class loaded by two loaders gives `ClassCastException` between them.
''', A, ["jvm"], False),

("What causes OutOfMemoryError and how would you debug a memory leak in production?", r'''
Types: `Java heap space`, `GC overhead limit exceeded`, `Metaspace` (too many classes / classloader leaks), `unable to create native thread`, `Direct buffer memory`.

Common leak causes: unbounded static maps/caches, `ThreadLocal`s not removed in pools, listeners never deregistered, unbounded executor queues, holding large result sets (loading a whole table), unclosed resources.

Debug steps:
1. Enable `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/dumps`.
2. Watch heap/GC metrics (Actuator + Prometheus/Grafana, `jstat -gcutil`). A rising "floor" after each full GC indicates a leak.
3. Take a heap dump (`jcmd <pid> GC.heap_dump file.hprof`).
4. Analyse in Eclipse MAT/VisualVM: Leak Suspects report, dominator tree, path to GC roots.
5. Fix the code (bound caches with Caffeine, paginate queries), and add tests/alerts.
''', A, ["jvm", "debugging"], True),

("StackOverflowError vs OutOfMemoryError?", r'''
- **StackOverflowError**: a thread's stack is exhausted, usually by infinite or very deep recursion (also cyclic `toString`/`hashCode` in bidirectional JPA entities or Jackson serialization loops). Fix the recursion or increase `-Xss`.
- **OutOfMemoryError**: the heap (or metaspace, native memory) can't satisfy an allocation even after GC. Caused by leaks or genuinely too much data. Fix by finding the leak, paginating/streaming data, or increasing `-Xmx`.

Both are `Error`s — don't catch them as normal flow.
''', B, ["jvm"], False),

("What is the JIT compiler?", r'''
The JVM starts by **interpreting** bytecode. The Just-In-Time compiler profiles execution and compiles **hot** methods (called frequently or with hot loops) into optimised native machine code stored in the code cache.

HotSpot uses **tiered compilation**: C1 (client compiler) compiles quickly with light optimisation; C2 (server compiler) later recompiles the hottest code with aggressive optimisations like inlining, escape analysis (allocating objects on the stack or eliminating them), loop unrolling, dead-code elimination, and lock elision. If assumptions break, code is deoptimised.

This is why Java apps "warm up" — early requests are slower. GraalVM native image (AOT) and CDS/CRaC are used to reduce startup time.
''', I, ["jvm"], False),

("What is serialization? What is serialVersionUID and transient?", r'''
Serialization converts an object graph into a byte stream (`ObjectOutputStream.writeObject`), and deserialization rebuilds it. Classes must implement the marker interface `Serializable`.
- **serialVersionUID**: a version number checked during deserialization. If the sender's and receiver's IDs differ, `InvalidClassException` is thrown. If you don't declare it, it's computed from the class structure, so any change breaks compatibility — always declare `private static final long serialVersionUID = 1L;`.
- **transient**: field is skipped (e.g. passwords, caches); it gets its default value after deserialization. `static` fields are also not serialized.
- A non-serializable field type causes `NotSerializableException`.
- `Externalizable` gives full manual control.
Java native serialization is a security risk with untrusted data; real systems use JSON/Protobuf/Avro.
''', B, ["serialization"], True),

("Is Java pass-by-value or pass-by-reference?", r'''
Java is **always pass-by-value**. For primitives the value is copied. For objects, the **reference** (a pointer value) is copied — so the method can mutate the object the reference points to, but reassigning the parameter doesn't change the caller's variable.
```java
void modify(List<Integer> list) {
    list.add(1);                 // visible to caller
    list = new ArrayList<>();    // only local copy changes
    list.add(2);                 // not visible to caller
}
```
That's why a classic `swap(a, b)` of two objects can't work in Java.
''', B, ["basics"], True),

("What is the Integer cache? Why does `Integer a = 128, b = 128; a == b` return false?", r'''
Autoboxing uses `Integer.valueOf(int)`, which returns cached instances for values from **-128 to 127** (upper bound configurable with `-XX:AutoBoxCacheMax`). So `Integer a = 127, b = 127; a == b` is `true` (same object), but for 128 two different objects are created and `==` compares references, giving `false`.

`Long`, `Short`, `Byte`, `Character` (0-127) have similar caches; `Double`/`Float` don't.

Lesson: always compare wrapper objects with `equals()` or unbox first. Also, unboxing `null` (e.g. `int x = map.get(key)` when absent) throws `NullPointerException`.
''', B, ["basics", "wrappers"], True),

("final vs finally vs finalize?", r'''
- **final** (keyword): a final variable can be assigned once; a final method can't be overridden; a final class can't be extended (e.g. `String`). A final reference can still point to a mutable object.
- **finally** (block): executes after try/catch regardless of exceptions — used for cleanup (now mostly replaced by try-with-resources).
- **finalize()** (method in `Object`): was called by the GC before reclaiming an object. Unpredictable, slow, could resurrect objects; deprecated since Java 9 and marked for removal. Use `AutoCloseable` or `java.lang.ref.Cleaner` instead.
''', B, ["basics"], False),

("What is the difference between shallow copy and deep copy? How does clone() work?", r'''
- **Shallow copy** copies the object's fields as-is; reference fields still point to the same nested objects, so changes to nested objects are shared.
- **Deep copy** recursively copies nested mutable objects so the copy is fully independent.

`Object.clone()` performs a shallow, field-by-field copy and requires the class to implement `Cloneable` (otherwise `CloneNotSupportedException`). To deep copy you override `clone()` and clone mutable fields manually.

`clone()` is widely considered broken-ish (no constructor call, checked exception, casts). Prefer copy constructors or static factories:
```java
public Order(Order o) { this.id = o.id; this.items = new ArrayList<>(o.items); }
```
Or serialize/deserialize (e.g. via Jackson) for complex graphs.
''', I, ["basics"], False),

("What are the main SOLID principles? Give an example of the Open/Closed principle.", r'''
- **S**ingle Responsibility — a class has one reason to change.
- **O**pen/Closed — open for extension, closed for modification.
- **L**iskov Substitution — subtypes must be usable wherever the base type is.
- **I**nterface Segregation — prefer small, focused interfaces.
- **D**ependency Inversion — depend on abstractions, not concrete classes.

Open/Closed example: replace an `if/else` on payment type with a strategy interface.
```java
interface DiscountPolicy { boolean supports(Customer c); BigDecimal apply(BigDecimal amt); }
@Component class PremiumDiscount implements DiscountPolicy { ... }
@Component class FestiveDiscount implements DiscountPolicy { ... }

@Service class PricingService {
    private final List<DiscountPolicy> policies;   // Spring injects all
    BigDecimal price(Customer c, BigDecimal amt) {
        return policies.stream().filter(p -> p.supports(c)).findFirst()
                       .map(p -> p.apply(amt)).orElse(amt);
    }
}
```
Adding a new discount means adding a class, not editing `PricingService`.
''', I, ["oop", "design"], True),

("What design patterns have you used in Java/Spring applications?", r'''
Pick ones you can explain with a real example:
- **Singleton** — Spring beans by default.
- **Factory** — `BeanFactory`, or a `PaymentProcessorFactory` returning an implementation by type.
- **Builder** — Lombok `@Builder`, `ResponseEntity.ok().header(...).body(...)`, `WebClient.builder()`.
- **Strategy** — interchangeable algorithms behind an interface (discounts, notification channels).
- **Template Method** — `JdbcTemplate`, `RestTemplate`: fixed skeleton, you supply callbacks.
- **Proxy** — Spring AOP proxies for `@Transactional`, `@Cacheable`, Hibernate lazy-loading proxies.
- **Observer** — Spring `ApplicationEvent`/`@EventListener`, Kafka pub-sub.
- **Adapter** — wrapping a third-party SMS SDK behind your own interface.
- **Decorator** — `BufferedInputStream` wrapping `InputStream`.
- **Chain of Responsibility** — Servlet filters / Spring Security filter chain.
Explain the problem it solved, not just the name.
''', I, ["design-patterns"], True),

("What is the difference between `==` and `equals()`?", r'''
- `==` compares **primitive values** or, for objects, **references** (are both variables pointing to the same object in memory?).
- `equals()` compares **logical content**, as defined by the class. `Object.equals` defaults to `==`; `String`, `Integer`, collections, records override it.
```java
String a = new String("x"), b = new String("x");
a == b;        // false
a.equals(b);   // true
```
For enums, `==` is fine and null-safe (singletons). For null-safe comparisons use `Objects.equals(a, b)`.
''', B, ["basics"], True),

("What's new with interfaces in Java 8 and 9 (default, static, private methods)?", r'''
- **Default methods (8)**: methods with a body that implementations inherit, allowing interfaces to evolve without breaking existing implementers (`Collection.stream()`, `Iterable.forEach`).
- **Static methods (8)**: utility methods on the interface itself, called as `Comparator.naturalOrder()`; not inherited by implementing classes.
- **Private methods (9)**: share code between default methods without exposing it.

Diamond rule: if a class inherits the same default method from two interfaces, it must override it and can call a specific one with `InterfaceA.super.method()`. A class's own (or superclass's) method always wins over interface defaults.
''', B, ["java8", "interface"], False),
]
