NOTES = []

NOTES.append(("OOP in Java: The Four Pillars and Beyond", r'''
Interviewers at product companies rarely want textbook definitions. They want to see that you can **apply** OOP to design clean code. Know the four pillars, and be ready to explain each with a real example from your own project.

## 1. Encapsulation
Bundle data and the behaviour that changes it, and hide internal state behind a controlled API.

```java
public class BankAccount {
    private BigDecimal balance = BigDecimal.ZERO;   // hidden state

    public void deposit(BigDecimal amt) {
        if (amt.signum() <= 0) throw new IllegalArgumentException("amount must be > 0");
        balance = balance.add(amt);                 // invariant enforced in one place
    }
    public BigDecimal getBalance() { return balance; }
}
```
The point is not "private fields + getters/setters". The point is that **invariants are enforced in one place**. Blind setters for every field break encapsulation.

## 2. Abstraction
Expose *what* an object does, hide *how*. In Java this is done with interfaces and abstract classes.

```java
public interface PaymentGateway { PaymentResult charge(Order o); }
class RazorpayGateway implements PaymentGateway { ... }
class StripeGateway implements PaymentGateway { ... }
```
The calling service depends only on `PaymentGateway` (this is also the Dependency Inversion principle, which Spring DI is built on).

## 3. Inheritance
An "is-a" relationship that lets a subclass reuse and extend a parent. Java supports single class inheritance but multiple interface inheritance. Prefer **composition over inheritance**: inheritance couples child to parent internals (the "fragile base class" problem). Use it only when the subtype truly is substitutable (Liskov Substitution Principle).

## 4. Polymorphism
- **Compile-time (static)**: method overloading — same name, different parameter lists. Resolved by the compiler.
- **Runtime (dynamic)**: method overriding — the JVM picks the implementation based on the actual object type via dynamic dispatch (vtable lookup).

```java
Shape s = new Circle(2);
s.area();        // Circle.area() runs, even though reference type is Shape
```

### Overriding rules (frequently asked)
- Same signature; return type can be covariant (a subtype).
- Access cannot be more restrictive (`protected` -> `public` ok, not reverse).
- Cannot throw broader **checked** exceptions.
- `static`, `private`, and `final` methods are not overridden (static methods are *hidden*).

## Abstract class vs Interface (Java 8+)
| | Abstract class | Interface |
|---|---|---|
| State | Can have instance fields | Only `public static final` constants |
| Constructors | Yes | No |
| Methods | Any | abstract, `default`, `static`, `private` (Java 9) |
| Inheritance | Single | Multiple |
| Use when | Sharing code/state among closely related classes | Defining a capability/contract (`Comparable`, `Runnable`) |

If two interfaces provide the same `default` method, the implementing class **must** override it and can call `A.super.method()`.

## SOLID in one line each
- **S**ingle Responsibility: one reason to change per class.
- **O**pen/Closed: extend behaviour by adding classes (strategy), not editing `if-else` chains.
- **L**iskov Substitution: a subclass must work wherever the parent is expected.
- **I**nterface Segregation: many small interfaces beat one fat one.
- **D**ependency Inversion: depend on abstractions; inject implementations.

## Other keywords worth knowing
- `final` class cannot be extended (`String`), `final` method cannot be overridden, `final` variable assigned once.
- `static` belongs to the class, not instances; static blocks run once at class initialisation.
- `this()` / `super()` must be the first statement in a constructor.
- Association, aggregation (has-a, independent lifecycle) and composition (has-a, owned lifecycle — a `Order` owns its `OrderLine`s).

**Interview tip:** When asked "explain polymorphism", follow the definition with a 2-line example from your Spring Boot project, e.g. multiple `NotificationSender` beans (email, SMS) injected as a `List<NotificationSender>`.
'''))

NOTES.append(("Strings, Immutability and the String Pool", r'''
`String` is the most-asked class in Java interviews. Understand why it is immutable and how the pool works.

## Why is String immutable?
`String` is `final` and its internal `byte[] value` (Java 9+, "compact strings"; it was `char[]` before) is `private final` and never modified.
1. **String pool** — literals are shared; if one reference could mutate the value, every other reference would see it.
2. **Security** — class names, file paths, DB URLs, and usernames are passed as strings; they cannot be changed after validation.
3. **Thread safety** — immutable objects can be shared across threads freely.
4. **Hash caching** — `hashCode()` is computed once and cached, which makes String a great `HashMap` key.

## String pool
```java
String a = "java";             // goes to pool
String b = "java";             // reuses the same pooled object
String c = new String("java"); // new object on heap (pooled literal also exists)
System.out.println(a == b);    // true  (same reference)
System.out.println(a == c);    // false (different objects)
System.out.println(a.equals(c));// true (same content)
System.out.println(a == c.intern()); // true
```
- Since Java 7 the pool lives in the **heap** (it used to be in PermGen), so it is garbage-collected.
- `new String("java")` creates **one or two** objects: the heap object always, plus the literal in the pool if not already present.
- `intern()` returns the pooled instance, adding it if absent.

## Concatenation
```java
String s = "a" + "b" + "c";   // compile-time constant -> single literal "abc"
String t = s + x;             // runtime: uses StringBuilder / invokedynamic (Java 9+)
```
In a loop, `+=` creates a new String every iteration — O(n^2). Use `StringBuilder`.

## String vs StringBuilder vs StringBuffer
| | String | StringBuilder | StringBuffer |
|---|---|---|---|
| Mutable | No | Yes | Yes |
| Thread-safe | Yes (immutable) | No | Yes (synchronized methods) |
| Speed | Slow for repeated edits | Fastest | Slower than builder |

## Useful modern methods
- Java 11: `isBlank()`, `strip()`, `lines()`, `repeat(n)`.
- Java 15: text blocks `""" ... """`.
- `String.join(",", list)`, `chars()` stream.

## How to make your own class immutable
```java
public final class Money {                         // 1. final class
    private final String currency;                 // 2. private final fields
    private final List<String> tags;
    public Money(String currency, List<String> tags) {
        this.currency = currency;
        this.tags = List.copyOf(tags);             // 3. defensive copy in
    }
    public List<String> getTags() { return tags; } // 4. already unmodifiable (else copy out)
    // 5. no setters; "withX" methods return new objects
    public Money withCurrency(String c) { return new Money(c, tags); }
}
```
In Java 16+, a `record` gives you most of this for free (but you still need defensive copies for mutable components).

## Common gotchas
- `==` compares references; `equals()` compares content. Never use `==` for strings.
- `"abc".equals(input)` is null-safe; `input.equals("abc")` can throw NPE.
- `substring` no longer shares the parent array (since 7u6), so no memory leak.
- Storing passwords: prefer `char[]` because you can wipe it; a String stays in memory until GC.

## Classic coding questions
```java
// Reverse a string
new StringBuilder(s).reverse().toString();
// Character frequency
Map<Character, Long> freq = s.chars().mapToObj(c -> (char) c)
    .collect(Collectors.groupingBy(Function.identity(), LinkedHashMap::new, Collectors.counting()));
// First non-repeated character
Character first = freq.entrySet().stream().filter(e -> e.getValue() == 1)
    .map(Map.Entry::getKey).findFirst().orElse(null);
// Anagram check
Arrays.equals(sorted(a), sorted(b));
```
'''))

NOTES.append(("equals(), hashCode() and the Object Class", r'''
Every class extends `java.lang.Object`, which provides `equals`, `hashCode`, `toString`, `getClass`, `clone`, `finalize` (deprecated), and `wait/notify/notifyAll`.

## Default behaviour
- `equals()` — reference equality (`this == obj`).
- `hashCode()` — an identity-based int (often derived from an internal address/random number), *not* guaranteed unique.

## The contract
1. If `a.equals(b)` is true, then `a.hashCode() == b.hashCode()` **must** be true.
2. Equal hash codes do **not** imply equal objects (collisions are allowed).
3. `equals` must be reflexive, symmetric, transitive, consistent, and `x.equals(null)` returns false.
4. `hashCode` must return the same value across calls as long as the fields used in `equals` do not change.

## What breaks if you override only equals?
```java
class Emp { int id; Emp(int id){this.id=id;}
  @Override public boolean equals(Object o){ return o instanceof Emp e && e.id == id; } }

Set<Emp> set = new HashSet<>();
set.add(new Emp(1));
set.contains(new Emp(1)); // false! different hashCode -> looks in a different bucket
set.add(new Emp(1));      // duplicate gets added
```
HashMap first uses `hashCode()` to find the bucket and *then* `equals()` inside the bucket. Without matching hash codes, equal objects land in different buckets.

## Correct implementation
```java
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    Employee that = (Employee) o;
    return id == that.id && Objects.equals(email, that.email);
}
@Override
public int hashCode() { return Objects.hash(id, email); }
```
- `getClass()` check gives strict symmetry; `instanceof` allows subclasses but can break symmetry if a subclass adds fields.
- Lombok `@EqualsAndHashCode` or a `record` generates both.

## Mutable keys are dangerous
If you put an object into a `HashMap` and then change a field used in `hashCode`, the entry becomes unreachable — `get` looks in the wrong bucket. Use immutable keys (String, Integer, records).

## JPA entities and equals/hashCode
For Hibernate entities, do **not** use the auto-generated id in `hashCode` if it is null before persist — the hash changes after save, breaking sets. Common approaches: use a natural/business key, or return a constant `getClass().hashCode()` and compare id only when non-null.

## Comparable vs Comparator
```java
class Emp implements Comparable<Emp> {
    public int compareTo(Emp o) { return Integer.compare(id, o.id); } // natural order
}
list.sort(Comparator.comparing(Emp::getDept)
        .thenComparing(Emp::getSalary, Comparator.reverseOrder()));
```
- `Comparable` — one natural ordering inside the class (`compareTo`).
- `Comparator` — any number of external orderings (`compare`).
- `TreeMap`/`TreeSet` use compareTo/compare, **not** equals, to detect duplicates — keep them consistent.

## toString and clone
- Override `toString()` for logging, but never log sensitive fields.
- `clone()` is shallow by default and requires `Cloneable`; prefer copy constructors or static factories.

## Shallow vs deep copy
Shallow copy copies field references (nested objects shared). Deep copy recursively copies nested mutable objects.

**Interview line:** "HashMap uses hashCode to find the bucket and equals to find the key within the bucket, so both must agree."
'''))

NOTES.append(("Collections Framework and HashMap Internals", r'''
## Hierarchy
- `Collection` -> `List` (ArrayList, LinkedList, Vector), `Set` (HashSet, LinkedHashSet, TreeSet), `Queue`/`Deque` (ArrayDeque, PriorityQueue, LinkedList).
- `Map` is separate: HashMap, LinkedHashMap, TreeMap, Hashtable, ConcurrentHashMap, EnumMap, WeakHashMap.

## HashMap internals (Java 8+) — the #1 asked question
- Backed by an array `Node<K,V>[] table`; each node has `hash, key, value, next`.
- Default capacity **16**, load factor **0.75**, so resize happens when size > 12.
- **put(k, v)**:
  1. `hash = h ^ (h >>> 16)` where `h = key.hashCode()` (spreads high bits).
  2. `index = (n - 1) & hash` (works because capacity is always a power of 2).
  3. Empty bucket -> place node. Otherwise walk the bucket; if a key `equals` the new key, replace value; else append.
  4. If a bucket has more than **8** nodes (and table size >= 64), it is converted to a **red-black tree** (treeification) -> worst case lookup O(log n) instead of O(n). It reverts to a list at 6.
  5. If size exceeds threshold -> **resize** to 2x, and nodes are split into "same index" or "index + oldCap" lists (no full rehash computation needed).
- One `null` key allowed (stored at bucket 0), many null values.
- Not thread-safe; concurrent resize in Java 7 could create an infinite loop. Java 8 fixed the loop but data loss is still possible.

```java
Map<String, Integer> m = new HashMap<>(64); // pre-size if you know volume
m.merge("apple", 1, Integer::sum);           // word count idiom
m.computeIfAbsent("k", x -> new ArrayList<>()).add(v);
```

## LinkedHashMap
HashMap + a doubly linked list of entries -> predictable insertion order (or access order with `accessOrder=true`). Override `removeEldestEntry` to build an **LRU cache**:
```java
class Lru<K,V> extends LinkedHashMap<K,V> {
    private final int cap;
    Lru(int cap){ super(16, 0.75f, true); this.cap = cap; }
    protected boolean removeEldestEntry(Map.Entry<K,V> e){ return size() > cap; }
}
```

## TreeMap
Red-black tree; keys sorted by natural order or a Comparator. `get/put/remove` O(log n). Navigation methods: `floorKey`, `ceilingKey`, `headMap`, `tailMap`, `firstEntry`. No null key (with natural ordering).

## HashSet
Internally a `HashMap<E, Object>` with a dummy `PRESENT` value. So uniqueness depends on equals/hashCode.

## ArrayList vs LinkedList
| | ArrayList | LinkedList |
|---|---|---|
| Structure | Dynamic array | Doubly linked list |
| get(i) | O(1) | O(n) |
| add at end | Amortised O(1) | O(1) |
| insert/remove middle | O(n) shift | O(n) to find + O(1) relink |
| Memory | Compact, cache friendly | Extra 2 pointers per node |
ArrayList grows by **1.5x** (`newCap = old + old>>1`), default capacity 10 (allocated lazily on first add). In practice ArrayList wins almost always; use `ArrayDeque` for queue/stack.

## Fail-fast vs fail-safe iterators
- **Fail-fast** (ArrayList, HashMap): track `modCount`; structural modification during iteration throws `ConcurrentModificationException`. Use `iterator.remove()` or `removeIf`.
- **Fail-safe / weakly consistent** (ConcurrentHashMap, CopyOnWriteArrayList): iterate over a snapshot or tolerate concurrent changes; no exception.

## Other useful ones
- `PriorityQueue` — binary min-heap; O(log n) offer/poll. Use for top-K problems.
- `ArrayDeque` — faster than `Stack` and `LinkedList` for stack/queue.
- `EnumMap` — array-backed, very fast for enum keys.
- `WeakHashMap` — entries removed when keys are no longer strongly referenced.
- `Collections.unmodifiableList` (view) vs `List.of` (truly immutable, no nulls).

## Big-O cheat sheet
HashMap get/put O(1) avg, O(log n) worst (tree bin). TreeMap O(log n). PriorityQueue offer/poll O(log n), peek O(1). ArrayList contains O(n). HashSet contains O(1).
'''))

NOTES.append(("ConcurrentHashMap and Concurrent Collections", r'''
## Why not Hashtable or synchronizedMap?
`Hashtable` and `Collections.synchronizedMap` lock the **entire map** for every operation, so only one thread can read or write at a time. `ConcurrentHashMap` (CHM) allows high concurrency.

## CHM in Java 7 (segment locking)
The map was divided into 16 `Segment`s (each a mini hash table extending `ReentrantLock`). Writes locked only one segment, so up to 16 writers could work in parallel ("concurrency level").

## CHM in Java 8+ (CAS + bucket-level synchronization)
- Segments were removed. The structure is like HashMap: array of nodes, with tree bins.
- **Reads are lock-free** — fields are `volatile`, so `get` never blocks.
- **Insert into empty bucket** uses a **CAS** (compare-and-swap) — no lock.
- **Insert into non-empty bucket** does `synchronized` on the **first node of that bucket** only.
- **Resize** is cooperative: multiple threads help transfer buckets; moved buckets are marked with a `ForwardingNode`.
- `size()` uses a `LongAdder`-like set of counter cells, so it is an estimate under concurrent updates. Prefer `mappingCount()` for large maps.

## Nulls not allowed
CHM rejects null keys and values. Reason: ambiguity. In a concurrent map, `get(k) == null` could mean "absent" or "mapped to null", and you cannot call `containsKey` atomically afterwards to disambiguate.

## Atomic compound operations
A common bug:
```java
// NOT atomic - two threads can both see null and both put
if (!map.containsKey(k)) map.put(k, 1); else map.put(k, map.get(k) + 1);

// Atomic alternatives
map.merge(k, 1, Integer::sum);
map.compute(k, (key, v) -> v == null ? 1 : v + 1);
map.computeIfAbsent(k, key -> new ConcurrentLinkedQueue<>()).add(item);
map.putIfAbsent(k, v);
```
Keep the lambda in `compute*` short; it runs while the bucket is locked.

## Iterators
Weakly consistent: never throw `ConcurrentModificationException`, reflect some state at or after iterator creation.

## Other concurrent collections
| Class | Notes |
|---|---|
| `CopyOnWriteArrayList` | Every write copies the array. Great for read-heavy, rarely-modified lists (listeners). |
| `ConcurrentLinkedQueue` | Lock-free unbounded queue (CAS). |
| `ArrayBlockingQueue` | Bounded, single lock; `put` blocks when full, `take` when empty. |
| `LinkedBlockingQueue` | Optionally bounded, separate put/take locks. Default queue of `newFixedThreadPool` (unbounded - OOM risk). |
| `PriorityBlockingQueue` | Heap-based blocking queue. |
| `DelayQueue` | Elements become available after delay. |
| `SynchronousQueue` | No capacity; hand-off. Used by `newCachedThreadPool`. |
| `ConcurrentSkipListMap` | Sorted concurrent map (concurrent TreeMap alternative). |

## Producer-consumer with BlockingQueue
```java
BlockingQueue<Order> q = new ArrayBlockingQueue<>(100);
Runnable producer = () -> { while (true) q.put(fetchOrder()); };
Runnable consumer = () -> { while (true) process(q.take()); };
```
(wrap `put/take` in try-catch for `InterruptedException`.)

## Interview questions you should be able to answer
- How does CHM achieve thread safety without locking the whole map? (CAS for empty bins, synchronized on bin head, volatile reads.)
- Is `chm.get()` blocking? (No.)
- Can two threads write simultaneously? (Yes, if they hit different buckets.)
- Is `if (!containsKey) put` safe on CHM? (No — use `putIfAbsent`/`computeIfAbsent`.)
'''))

NOTES.append(("Generics and Type Erasure", r'''
Generics give compile-time type safety and remove casts.

```java
List<String> names = new ArrayList<>();
names.add("raj");
String n = names.get(0);   // no cast
```

## Generic classes and methods
```java
public class Box<T> { private T value; public T get(){ return value; } }

public static <T extends Comparable<T>> T max(List<T> list) {
    T best = list.get(0);
    for (T t : list) if (t.compareTo(best) > 0) best = t;
    return best;
}
```
`<T extends Comparable<T>>` is a **bounded type parameter**. Multiple bounds: `<T extends Number & Comparable<T>>` (class first).

## Wildcards and PECS
- `List<?>` — unknown type; you can read as `Object`, cannot add (except null).
- `List<? extends Number>` — **upper bound**; a *producer*: you can read `Number`s but not add.
- `List<? super Integer>` — **lower bound**; a *consumer*: you can add `Integer`s, reads give `Object`.

**PECS: Producer Extends, Consumer Super.**
```java
public static <T> void copy(List<? super T> dest, List<? extends T> src) {
    for (T t : src) dest.add(t);
}
```

## Invariance
`List<Integer>` is **not** a subtype of `List<Number>` even though Integer is a Number. Otherwise you could add a Double into a list of Integers. Arrays are covariant (`Integer[]` is a `Number[]`) which is why they can throw `ArrayStoreException` at runtime.

## Type erasure
Generics exist only at compile time. The compiler:
1. Replaces type parameters with their bound (or `Object`).
2. Inserts casts where needed.
3. Generates **bridge methods** to preserve polymorphism.

Consequences:
- `List<String>` and `List<Integer>` have the same runtime class -> `list.getClass()` is `ArrayList`.
- You cannot do `new T()`, `new T[10]`, `instanceof List<String>`, or have static fields of type `T`.
- You cannot overload `void f(List<String>)` and `void f(List<Integer>)` — same erasure.
- Primitives are not allowed: `List<int>` is invalid; use `List<Integer>` (autoboxing).

Workaround for creating instances: pass a `Class<T>` token or `Supplier<T>`.
```java
<T> T create(Supplier<T> factory) { return factory.get(); }
```
Jackson uses `TypeReference<List<User>>(){}` (an anonymous subclass keeps the generic info in its superclass signature) to work around erasure.

## Raw types
`List list = new ArrayList();` is a raw type — kept for backward compatibility; loses type safety and produces unchecked warnings. Avoid.

## Generic interfaces in Spring
`JpaRepository<User, Long>` is a generic interface; Spring Data reads the actual type arguments via reflection on the interface declaration (which is retained in class metadata, unlike erasure of local variables).
'''))

NOTES.append(("Exception Handling", r'''
## Hierarchy
```
Throwable
 |- Error            (OutOfMemoryError, StackOverflowError) - don't catch
 |- Exception
     |- RuntimeException (unchecked: NPE, IllegalArgumentException, ArithmeticException,
     |                    IndexOutOfBounds, ConcurrentModificationException, ClassCastException)
     |- checked: IOException, SQLException, ClassNotFoundException, InterruptedException
```
- **Checked** exceptions must be caught or declared with `throws` — compiler enforced. Represent recoverable conditions outside program control.
- **Unchecked** (RuntimeException) represent programming bugs or business rule violations; no compile-time enforcement.

## try / catch / finally
```java
try {
    risky();
} catch (FileNotFoundException e) {   // more specific first
    log.warn("missing", e);
} catch (IOException | SQLException e) { // multi-catch (Java 7)
    throw new DataAccessException("failed", e); // wrap & preserve cause
} finally {
    cleanup();                          // always runs (except System.exit / JVM crash)
}
```
**Gotchas:**
- A `return` in `finally` overrides the return/exception in `try` — never do it.
- If `finally` throws, the original exception is lost.
- `finally` does not run on `System.exit()` or if the thread is killed.

## try-with-resources (Java 7)
```java
try (Connection c = ds.getConnection();
     PreparedStatement ps = c.prepareStatement(sql)) {
    ...
} // closed automatically in reverse order
```
Resources must implement `AutoCloseable`. If both the body and `close()` throw, the close exception is added as a **suppressed** exception (`e.getSuppressed()`).

## throw vs throws
`throw` actually throws an instance; `throws` in a method signature declares possible checked exceptions.

## Custom exceptions
```java
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String resource, Object id) {
        super(resource + " not found with id " + id);
    }
}
```
In Spring Boot, custom runtime exceptions + `@RestControllerAdvice` produce clean HTTP error responses. Also remember Spring's `@Transactional` rolls back by default only on **unchecked** exceptions.

## Overriding and exceptions
An overriding method may throw fewer or narrower checked exceptions, or any unchecked ones, but not new/broader checked exceptions.

## Best practices
- Never swallow exceptions (`catch (Exception e) {}`).
- Catch the most specific type; don't catch `Throwable`/`Error`.
- Always keep the cause when wrapping (`new X(msg, e)`).
- Log once, at the boundary — not at every layer.
- Restore interrupt status when catching `InterruptedException`: `Thread.currentThread().interrupt();`
- Don't use exceptions for normal control flow; they are expensive (stack trace capture).

## ClassNotFoundException vs NoClassDefFoundError
- `ClassNotFoundException` (checked): explicit loading by name (`Class.forName`) failed.
- `NoClassDefFoundError` (Error): class was present at compile time but missing at runtime, or its static initialiser failed earlier.

## StackOverflowError vs OutOfMemoryError
SOE: thread stack exhausted (usually infinite recursion). OOM: heap/metaspace exhausted (memory leak, too-large data, unbounded caches/queues).
'''))

NOTES.append(("Java 8: Lambdas, Functional Interfaces and Optional", r'''
## Lambdas
A lambda is a concise implementation of a **functional interface** (an interface with exactly one abstract method).
```java
Comparator<Emp> bySalary = (a, b) -> Double.compare(a.getSalary(), b.getSalary());
Runnable r = () -> System.out.println("hi");
```
Lambdas can capture local variables only if they are **effectively final** (because the value is copied into the lambda, and allowing mutation would create race conditions). Unlike anonymous classes, `this` inside a lambda refers to the enclosing instance, and lambdas don't create a new scope for variable names. Lambdas compile to `invokedynamic`, not to separate `.class` files.

## Built-in functional interfaces (java.util.function)
| Interface | Method | Use |
|---|---|---|
| `Predicate<T>` | `boolean test(T)` | filter |
| `Function<T,R>` | `R apply(T)` | map |
| `Consumer<T>` | `void accept(T)` | forEach |
| `Supplier<T>` | `T get()` | lazy creation, `orElseGet` |
| `BiFunction<T,U,R>` | `R apply(T,U)` | merge |
| `UnaryOperator<T>` / `BinaryOperator<T>` | same type in/out | `reduce` |
Primitive variants (`IntPredicate`, `ToIntFunction`) avoid boxing. Compose them: `p1.and(p2).negate()`, `f.andThen(g)`, `f.compose(g)`.

Mark your own with `@FunctionalInterface` — the compiler then errors if a second abstract method is added. Default and static methods don't count, nor do methods from `Object` like `equals`.

## Method references
```java
list.forEach(System.out::println);      // instance method of particular object
list.stream().map(String::toUpperCase);  // instance method of arbitrary object
list.stream().map(Integer::parseInt);    // static method
Supplier<List<String>> s = ArrayList::new; // constructor
```

## Default and static methods in interfaces
Added so that interfaces like `Collection` could gain `stream()` and `forEach` without breaking every implementation. Diamond problem resolution: class methods win over interface defaults; a more specific interface wins; otherwise you must override.

## Optional
A container that may or may not hold a value — designed as a **return type** to make "no result" explicit.
```java
Optional<User> u = repo.findById(id);
String city = u.map(User::getAddress)
               .map(Address::getCity)
               .orElse("Unknown");
User user = u.orElseThrow(() -> new ResourceNotFoundException("User", id));
u.ifPresentOrElse(this::send, () -> log.info("none")); // Java 9
```
- `orElse(x)` always evaluates `x`; `orElseGet(() -> x)` evaluates lazily. Use `orElseGet` when the default is expensive (DB call).
- `Optional.of(null)` throws NPE; use `ofNullable`.
- **Don't**: use Optional for fields, method parameters, or collections (return empty list instead), or call `get()` without checking. Optional is not `Serializable`.

## Other Java 8 additions
- **New Date/Time API** (`java.time`): `LocalDate`, `LocalDateTime`, `ZonedDateTime`, `Instant`, `Duration`, `Period`, `DateTimeFormatter`. Immutable and thread-safe, unlike `Date`/`SimpleDateFormat`.
- `CompletableFuture` for async composition.
- Metaspace replaced PermGen.
- `ConcurrentHashMap` rework, `Map.merge/compute/getOrDefault`.
- `String.join`, `StringJoiner`, `Base64`.
'''))

NOTES.append(("Streams API Deep Dive with Coding Patterns", r'''
A stream is a lazy pipeline over a data source: **source -> intermediate ops -> terminal op**. Streams don't store data, don't modify the source, and can be consumed only once.

## Intermediate (lazy, return a Stream)
`filter, map, flatMap, distinct, sorted, peek, limit, skip, takeWhile, dropWhile (9), mapToInt, boxed`.
Stateless (`filter`, `map`) vs stateful (`sorted`, `distinct` — need to see many elements).

## Terminal (trigger execution)
`collect, forEach, reduce, count, min, max, anyMatch, allMatch, noneMatch, findFirst, findAny, toList() (16), toArray`.
Nothing runs until a terminal op is called. Short-circuiting ops (`limit`, `findFirst`, `anyMatch`) stop early.

## map vs flatMap
```java
List<List<Integer>> nested = List.of(List.of(1,2), List.of(3));
nested.stream().flatMap(List::stream).toList();   // [1, 2, 3]
```

## Collectors you must know
```java
record Emp(String name, String dept, double salary, String gender) {}

// group by department
Map<String, List<Emp>> byDept = emps.stream().collect(Collectors.groupingBy(Emp::dept));
// count per department
Map<String, Long> cnt = emps.stream().collect(Collectors.groupingBy(Emp::dept, Collectors.counting()));
// average salary per department
Map<String, Double> avg = emps.stream()
    .collect(Collectors.groupingBy(Emp::dept, Collectors.averagingDouble(Emp::salary)));
// highest paid per department
Map<String, Optional<Emp>> top = emps.stream()
    .collect(Collectors.groupingBy(Emp::dept, Collectors.maxBy(Comparator.comparingDouble(Emp::salary))));
// names per department
Map<String, List<String>> names = emps.stream()
    .collect(Collectors.groupingBy(Emp::dept, Collectors.mapping(Emp::name, Collectors.toList())));
// partition
Map<Boolean, List<Emp>> rich = emps.stream().collect(Collectors.partitioningBy(e -> e.salary() > 50000));
// to map (handle duplicate keys!)
Map<String, Double> m = emps.stream()
    .collect(Collectors.toMap(Emp::name, Emp::salary, (a, b) -> a, LinkedHashMap::new));
// joining
String csv = emps.stream().map(Emp::name).collect(Collectors.joining(", ", "[", "]"));
// statistics
DoubleSummaryStatistics st = emps.stream().mapToDouble(Emp::salary).summaryStatistics();
```

## Most-asked stream coding questions
```java
// Second highest salary
Optional<Double> second = emps.stream().map(Emp::salary).distinct()
    .sorted(Comparator.reverseOrder()).skip(1).findFirst();

// Nth highest salary employee(s)
double nth = emps.stream().map(Emp::salary).distinct()
    .sorted(Comparator.reverseOrder()).skip(n - 1).findFirst().orElseThrow();

// Find duplicates in a list
Set<Integer> seen = new HashSet<>();
Set<Integer> dups = nums.stream().filter(x -> !seen.add(x)).collect(Collectors.toSet());
// or (pure, no side effects)
Set<Integer> dups2 = nums.stream().collect(Collectors.groupingBy(Function.identity(), Collectors.counting()))
    .entrySet().stream().filter(e -> e.getValue() > 1).map(Map.Entry::getKey).collect(Collectors.toSet());

// First non-repeating character
Character c = s.chars().mapToObj(ch -> (char) ch)
    .collect(Collectors.groupingBy(Function.identity(), LinkedHashMap::new, Collectors.counting()))
    .entrySet().stream().filter(e -> e.getValue() == 1).map(Map.Entry::getKey).findFirst().orElse(null);

// Sum of even numbers / squares
int sum = nums.stream().filter(x -> x % 2 == 0).mapToInt(Integer::intValue).sum();

// Sort map by value desc
map.entrySet().stream().sorted(Map.Entry.<String,Integer>comparingByValue().reversed()).toList();

// Word frequency
Map<String, Long> wf = Arrays.stream(text.split("\\s+"))
    .collect(Collectors.groupingBy(String::toLowerCase, Collectors.counting()));
```

## reduce
```java
int total = nums.stream().reduce(0, Integer::sum);
Optional<Integer> max = nums.stream().reduce(Integer::max);
```

## Parallel streams
`list.parallelStream()` splits work using the common `ForkJoinPool` (size = cores - 1). Use only for large, CPU-bound, stateless, easily-splittable data (ArrayList, arrays — not LinkedList). Avoid for I/O or in web servers sharing the common pool, and never mutate shared state inside. `findAny` is faster than `findFirst` in parallel.

## Common mistakes
- Reusing a stream -> `IllegalStateException`.
- `Collectors.toMap` with duplicate keys -> `IllegalStateException` unless you pass a merge function.
- Side effects in `map`/`filter`; using `peek` for business logic.
- `Stream.toList()` (Java 16) returns an unmodifiable list; `Collectors.toList()` returns a mutable ArrayList (unspecified).
'''))

NOTES.append(("Modern Java (11 to 21): Records, Sealed Classes, Pattern Matching, Virtual Threads", r'''
Product companies increasingly run Java 17 or 21 (LTS). Know what each LTS added.

## Java 9-11 highlights
- `List.of`, `Set.of`, `Map.of` immutable factories (9).
- `var` local type inference (10) — still statically typed; only for locals with initialisers.
- Module system (JPMS) (9), JShell (9).
- `Optional.ifPresentOrElse`, `or`, `stream` (9); `Optional.isEmpty` (11).
- String: `isBlank`, `strip`, `lines`, `repeat` (11). `Files.readString` (11).
- Standard `HttpClient` (11). Run single file: `java Hello.java` (11).

## Java 14-17
**Switch expressions (14)**
```java
int days = switch (month) {
    case FEB -> 28;
    case APR, JUN, SEP, NOV -> 30;
    default -> { log("x"); yield 31; }
};
```
No fall-through, returns a value, compiler checks exhaustiveness for enums.

**Text blocks (15)**
```java
String json = """
    {"name": "raj", "role": "dev"}
    """;
```

**Pattern matching for instanceof (16)**
```java
if (obj instanceof String s && !s.isBlank()) System.out.println(s.length());
```

**Records (16)** — immutable data carriers.
```java
public record UserDto(Long id, String email) {
    public UserDto {                       // compact constructor for validation
        Objects.requireNonNull(email);
    }
    public String domain() { return email.substring(email.indexOf('@') + 1); }
}
```
Records get `private final` fields, canonical constructor, accessors `id()`, `email()`, and `equals/hashCode/toString`. They are implicitly `final`, cannot extend a class (they extend `java.lang.Record`) but can implement interfaces. Great for DTOs, API responses, map keys. Not suitable as JPA entities (entities need no-arg constructor, mutability, proxies).

**Sealed classes (17)** — restrict who can extend.
```java
public sealed interface Shape permits Circle, Square {}
public record Circle(double r) implements Shape {}
public record Square(double side) implements Shape {}
```
Subclasses must be `final`, `sealed`, or `non-sealed`. Enables exhaustive pattern matching.

Also 17: helpful NullPointerExceptions (14) tell you exactly which variable was null; strong encapsulation of JDK internals.

## Java 21 (current widely-adopted LTS)
**Pattern matching for switch + record patterns**
```java
double area(Shape s) {
    return switch (s) {
        case Circle c -> Math.PI * c.r() * c.r();
        case Square(double side) -> side * side;   // record deconstruction
    };                                            // exhaustive: no default needed (sealed)
}
// guards
String classify(Object o) {
    return switch (o) {
        case null -> "null";
        case Integer i when i > 100 -> "big int";
        case Integer i -> "int";
        case String s -> "string " + s;
        default -> "other";
    };
}
```

**Virtual threads (Project Loom)**
- Lightweight threads managed by the JVM, not 1:1 with OS threads. Millions can exist.
- When a virtual thread blocks on I/O, it is **unmounted** from its carrier (platform) thread, which then runs another virtual thread.
- Perfect for the thread-per-request style with blocking I/O (JDBC, REST calls) — high throughput without reactive code.
```java
try (var exec = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> exec.submit(() -> callApi(i)));
}
Thread.ofVirtual().start(() -> work());
```
Spring Boot 3.2+: `spring.threads.virtual.enabled=true`.
- Caveats: no benefit for CPU-bound work; don't pool them; **pinning** happens when blocking inside `synchronized` (fixed in Java 24 by JEP 491) or native code — prefer `ReentrantLock` on Java 21; avoid heavy `ThreadLocal` usage.

**Sequenced collections (21)**: `SequencedCollection` adds `getFirst()`, `getLast()`, `reversed()` to List, Deque, LinkedHashSet, LinkedHashMap.

**Other 21**: Generational ZGC, String templates (preview, later dropped), structured concurrency and scoped values (preview).

## Beyond 21 (good to mention)
Java 22-25: unnamed variables `_` (22), stream gatherers (24), and Java 25 is the next LTS (Sept 2025) with scoped values finalised, compact source files / instance main methods, and flexible constructor bodies.
'''))

NOTES.append(("Multithreading Basics: Threads, synchronized, volatile", r'''
## Creating threads
```java
Thread t1 = new Thread(() -> work());           // Runnable (preferred)
class MyThread extends Thread { public void run(){...} }
Callable<Integer> c = () -> 42;                  // returns value, can throw
Future<Integer> f = executor.submit(c);
```
Prefer `Runnable`/`Callable` with an `ExecutorService`; extending `Thread` wastes your single inheritance.
`start()` creates a new call stack and calls `run()` on it. Calling `run()` directly just runs on the current thread. Calling `start()` twice throws `IllegalThreadStateException`.

## Thread lifecycle (Thread.State)
`NEW` -> `RUNNABLE` (running or ready) -> `BLOCKED` (waiting for a monitor lock) / `WAITING` (`wait()`, `join()`, `LockSupport.park`) / `TIMED_WAITING` (`sleep(ms)`, `wait(ms)`) -> `TERMINATED`.

## sleep vs wait vs join vs yield
| | sleep | wait | join |
|---|---|---|---|
| Class | Thread (static) | Object | Thread |
| Releases lock? | **No** | **Yes** | (uses wait internally) |
| Needs synchronized? | No | Yes, else `IllegalMonitorStateException` | No |
| Woken by | Timeout/interrupt | `notify/notifyAll`/timeout | Target thread finishes |
Always call `wait()` in a `while` loop to guard against spurious wakeups.

## Race conditions and synchronized
```java
class Counter {
    private int count;
    public synchronized void inc() { count++; }  // count++ is read-modify-write, not atomic
}
```
- `synchronized` method locks `this` (or the `Class` object for static methods).
- `synchronized (lock) { ... }` block locks a specific object — smaller critical section, better.
- Intrinsic locks are **reentrant**: a thread holding the lock can re-enter.
- Gives both **mutual exclusion** and **visibility** (happens-before on unlock -> lock).

## volatile
- Guarantees **visibility**: writes go to main memory and reads come from it; prevents reordering around the variable.
- Does **not** give atomicity: `volatile int x; x++` is still a race.
- Typical use: stop flags, and the double-checked locking singleton.
```java
private volatile boolean running = true;
public void stop(){ running = false; }
public void run(){ while (running) { ... } }
```

## Java Memory Model (happens-before)
Each thread may cache variables. The JMM defines happens-before edges that guarantee visibility: unlock -> subsequent lock of same monitor, volatile write -> subsequent read, `Thread.start()` -> actions in the started thread, thread actions -> `join()` returning.

## Atomic classes
`AtomicInteger`, `AtomicLong`, `AtomicReference`, `LongAdder`. Use CAS (compare-and-swap) CPU instructions — lock-free.
```java
AtomicInteger c = new AtomicInteger();
c.incrementAndGet();
c.updateAndGet(x -> x * 2);
```
`LongAdder` is faster than `AtomicLong` under high contention (spreads updates over cells).

## Thread-safe singleton
```java
public class Config {
    private static volatile Config instance;
    private Config() {}
    public static Config get() {
        if (instance == null) {                 // 1st check (no lock)
            synchronized (Config.class) {
                if (instance == null) instance = new Config(); // 2nd check
            }
        }
        return instance;
    }
}
```
`volatile` prevents another thread seeing a partially constructed object (reordering of allocate/assign/construct). Simpler alternatives: enum singleton, or the holder-class idiom (lazy, thread-safe via class loading).

## Interrupts
`t.interrupt()` sets a flag; blocking methods throw `InterruptedException` and clear it. Handle by restoring: `Thread.currentThread().interrupt();`.

## Daemon threads
Background threads (GC) that don't prevent JVM exit. `t.setDaemon(true)` before start.

## ThreadLocal
Per-thread copy of a variable (used for user context, transaction context, `SimpleDateFormat`). In thread pools, always `remove()` in `finally` to avoid leaks and data bleeding between requests.

## Printing odd/even with two threads (classic)
```java
class Printer {
    private int n = 1; private final int max = 10;
    synchronized void print(boolean odd) throws InterruptedException {
        while (n <= max) {
            while (n <= max && (n % 2 == 1) != odd) wait();
            if (n <= max) { System.out.println(Thread.currentThread().getName() + " " + n++); notifyAll(); }
        }
    }
}
```
'''))

NOTES.append(("Concurrency Utilities: Locks, Executors, CompletableFuture, Deadlock", r'''
## Lock interface (java.util.concurrent.locks)
```java
private final ReentrantLock lock = new ReentrantLock(true); // fair
void transfer() {
    if (lock.tryLock(1, TimeUnit.SECONDS)) {
        try { ... } finally { lock.unlock(); }   // always unlock in finally
    }
}
```
Advantages over `synchronized`: `tryLock` with timeout, interruptible lock acquisition (`lockInterruptibly`), fairness option, multiple `Condition`s (`await/signal`). Downside: must unlock manually.
- `ReentrantReadWriteLock`: many readers OR one writer — read-heavy caches.
- `StampedLock`: optimistic reads, not reentrant.

## Synchronizers
| Tool | Purpose |
|---|---|
| `CountDownLatch(n)` | One or more threads wait until n events happen (`countDown`, `await`). Not reusable. |
| `CyclicBarrier(n)` | n threads wait for each other at a barrier, then all proceed. Reusable. |
| `Semaphore(k)` | Limit concurrent access to k permits (connection limits, rate limiting). |
| `Phaser` | Flexible, multi-phase barrier. |
| `Exchanger` | Two threads swap objects. |

## Executor framework
Creating a thread per task is expensive; thread pools reuse threads.
```java
ExecutorService pool = Executors.newFixedThreadPool(10);
Future<String> f = pool.submit(() -> fetch());
String r = f.get(2, TimeUnit.SECONDS);
pool.shutdown();                      // no new tasks, finish queued
pool.awaitTermination(30, TimeUnit.SECONDS);
```
Factory pools: `newFixedThreadPool` (unbounded `LinkedBlockingQueue`), `newCachedThreadPool` (unbounded threads, `SynchronousQueue`), `newSingleThreadExecutor`, `newScheduledThreadPool`, `newWorkStealingPool` (ForkJoin), `newVirtualThreadPerTaskExecutor` (21). In production, prefer a hand-configured `ThreadPoolExecutor` to avoid unbounded queues/threads causing OOM.

### ThreadPoolExecutor parameters
`corePoolSize, maximumPoolSize, keepAliveTime, workQueue, threadFactory, rejectionHandler`.
Flow: new task -> if running threads < core, new thread; else enqueue; if queue full and threads < max, new thread; else **reject**.
Rejection policies: `AbortPolicy` (default, throws), `CallerRunsPolicy` (back-pressure), `DiscardPolicy`, `DiscardOldestPolicy`.
Sizing rule of thumb: CPU-bound ~ cores + 1; I/O-bound ~ cores * (1 + wait/compute).

`submit()` returns a Future and captures exceptions inside it; `execute()` has no result and exceptions go to the thread's uncaught handler.

## CompletableFuture
`Future.get()` blocks and cannot be chained. `CompletableFuture` supports non-blocking pipelines.
```java
CompletableFuture<User> userF = CompletableFuture.supplyAsync(() -> userClient.get(id), pool);
CompletableFuture<List<Order>> ordersF = CompletableFuture.supplyAsync(() -> orderClient.list(id), pool);

CompletableFuture<Profile> profile = userF
    .thenCombine(ordersF, Profile::new)          // run both in parallel, combine
    .orTimeout(2, TimeUnit.SECONDS)
    .exceptionally(ex -> Profile.empty());       // fallback

CompletableFuture.allOf(f1, f2, f3).join();      // wait for all
CompletableFuture.anyOf(f1, f2);                 // first to complete
```
- `thenApply` (map), `thenCompose` (flatMap — chain another async call), `thenAccept` (consume), `thenCombine` (two independent futures).
- `exceptionally`, `handle` (result + exception), `whenComplete`.
- `*Async` variants run on a pool; default is `ForkJoinPool.commonPool()` — **pass your own executor** for I/O work.

## Fork/Join
Divide-and-conquer with work stealing: `RecursiveTask<T>` / `RecursiveAction`, `fork()`, `join()`. Powers parallel streams.

## Deadlock
Two or more threads wait forever for locks held by each other.
```java
// T1: lock(A) then lock(B)     T2: lock(B) then lock(A)  -> deadlock
```
**Four Coffman conditions** (all needed): mutual exclusion, hold-and-wait, no preemption, circular wait.
**Prevention:** acquire locks in a global consistent order (e.g. by account id), use `tryLock` with timeout, minimise lock scope, avoid nested locks, use higher-level concurrency utilities.
**Detection:** `jstack <pid>` or a thread dump shows "Found one Java-level deadlock"; `ThreadMXBean.findDeadlockedThreads()`.

Related: **livelock** (threads keep responding to each other but make no progress), **starvation** (a thread never gets CPU/lock — e.g. unfair locks).
'''))

NOTES.append(("JVM Internals: Memory, Class Loading, Garbage Collection", r'''
## JDK vs JRE vs JVM
JVM executes bytecode; JRE = JVM + libraries; JDK = JRE + dev tools (javac, jdb, jcmd). Java is "write once, run anywhere" because `.class` bytecode runs on any platform's JVM.

## Execution pipeline
`.java` -> `javac` -> `.class` bytecode -> ClassLoader -> Bytecode verifier -> Interpreter + **JIT compiler** (C1/C2 compile hot methods to native code; tiered compilation) -> execution.

## Memory areas
| Area | Shared? | Holds |
|---|---|---|
| **Heap** | All threads | Objects, arrays, String pool. Divided into Young (Eden + 2 Survivors) and Old generation. |
| **Metaspace** (Java 8+, native memory) | All | Class metadata, method bytecode, static variable references live with the Class object on heap. Replaced PermGen. |
| **JVM Stack** | Per thread | Frames: local variables, operand stack, references. `StackOverflowError` when full. |
| **PC register** | Per thread | Current instruction address. |
| **Native method stack** | Per thread | For JNI calls. |
| Code cache | All | JIT-compiled native code. |

```java
void m() {
    int x = 5;              // primitive in stack frame
    User u = new User();    // reference 'u' in stack, object in heap
}
```

## Class loading
Phases: **Loading** -> **Linking** (verify, prepare default static values, resolve) -> **Initialization** (static blocks, static field initialisers run).
ClassLoader hierarchy: **Bootstrap** (core `java.*`), **Platform** (formerly Extension), **Application/System** (classpath). Custom loaders are used by app servers and Spring Boot's fat-jar launcher.
**Parent delegation model:** a loader first asks its parent; only if the parent can't find the class does it load itself. This prevents someone from replacing `java.lang.String` with a malicious copy, and avoids duplicate loading.
A class is identified by (fully-qualified name + its class loader).

## Garbage collection basics
- An object is eligible when it is unreachable from **GC roots** (local variables on stacks, static fields, active threads, JNI refs). Reference counting is not used, so cycles are collected.
- **Generational hypothesis:** most objects die young.
  - New objects go to **Eden**. A **Minor GC** copies live objects to a Survivor space; after surviving N cycles (tenuring threshold, default up to 15) they are promoted to **Old gen**.
  - **Major/Full GC** cleans the old generation — slower, longer pauses.
- Basic algorithm: **mark** live objects, **sweep** dead ones, **compact** to remove fragmentation. Young gen uses copying.
- "Stop-the-world" pauses freeze application threads.

## Collectors
| GC | Notes |
|---|---|
| Serial | Single thread; small heaps/clients. |
| Parallel | Multi-threaded, throughput-focused (default in Java 8). |
| CMS | Concurrent mark-sweep; deprecated (9) and removed (14). |
| **G1** (default since Java 9) | Heap divided into equal-sized **regions**; collects regions with most garbage first ("Garbage First"); target pause via `-XX:MaxGCPauseMillis=200`; concurrent marking; mixed collections; compacts incrementally. Good balance for 4GB+ heaps. |
| **ZGC** | Ultra-low pause (<1ms typically), scales to TB heaps, concurrent compaction using coloured pointers and load barriers. Generational from Java 21 (`-XX:+UseZGC -XX:+ZGenerational`; default generational in 23). |
| Shenandoah | Low-pause, concurrent compaction (Red Hat). |
| Epsilon | No-op GC for testing. |

## Reference types
Strong (normal), **Soft** (cleared only under memory pressure — caches), **Weak** (cleared at next GC — `WeakHashMap`), **Phantom** (post-mortem cleanup, `Cleaner`).

## Important flags & tools
`-Xms` initial heap, `-Xmx` max heap, `-Xss` thread stack size, `-XX:MaxMetaspaceSize`, `-XX:+HeapDumpOnOutOfMemoryError`.
Tools: `jps`, `jstack` (thread dump), `jmap`/`jcmd GC.heap_dump` (heap dump), `jstat` (GC stats), VisualVM, JFR + JMC, Eclipse MAT for leak analysis.

## Memory leaks in Java
Even with GC, leaks happen when objects stay reachable: static collections that grow, unbounded caches, unremoved listeners, `ThreadLocal` in pools, unclosed resources, inner classes holding outer references. Diagnose with heap dumps and the dominator tree.
'''))

NOTES.append(("Serialization, Cloning and Misc Core Topics", r'''
## Serialization
Converting an object to a byte stream (to save to disk/send over network) and back (deserialization).
```java
class User implements Serializable {
    private static final long serialVersionUID = 1L;
    private String name;
    private transient String password;   // not serialized -> null after deserialization
}
try (var out = new ObjectOutputStream(new FileOutputStream("u.ser"))) { out.writeObject(user); }
try (var in = new ObjectInputStream(new FileInputStream("u.ser"))) { User u = (User) in.readObject(); }
```
- `Serializable` is a **marker interface** (no methods).
- `serialVersionUID` — version check. If not declared, the JVM computes one from the class structure; any change (adding a field) changes it and deserialization throws `InvalidClassException`. Always declare it.
- `transient` and `static` fields are not serialized.
- If a parent class is not Serializable, it must have a no-arg constructor; its fields get re-initialised by that constructor.
- All referenced objects must be Serializable, otherwise `NotSerializableException`.
- Customise with `private void writeObject/readObject`, or `Externalizable` (`writeExternal/readExternal`, needs public no-arg constructor, full control, faster).
- `readResolve()` preserves singletons during deserialization.
- **Security:** Java native deserialization of untrusted data is a well-known RCE vector. Modern systems use JSON (Jackson), Protobuf, or Avro. Use deserialization filters (`ObjectInputFilter`) if you must.

## Jackson (the serialization you actually use in Spring)
```java
ObjectMapper om = new ObjectMapper();
String json = om.writeValueAsString(dto);
UserDto dto = om.readValue(json, UserDto.class);
List<UserDto> list = om.readValue(json, new TypeReference<List<UserDto>>() {});
```
Annotations: `@JsonIgnore`, `@JsonProperty`, `@JsonFormat`, `@JsonInclude(NON_NULL)`, `@JsonIgnoreProperties(ignoreUnknown = true)`. Bidirectional JPA relations need `@JsonManagedReference/@JsonBackReference` or DTOs to avoid infinite recursion.

## Pass by value
Java is **always pass-by-value**. For objects, the value passed is a copy of the reference. So a method can mutate the object's fields, but reassigning the parameter does not affect the caller.
```java
void change(StringBuilder sb) { sb.append("x"); sb = new StringBuilder("new"); }
```
Caller sees the appended "x" but not "new".

## Wrapper classes and autoboxing
```java
Integer a = 127, b = 127;  a == b  // true  (Integer cache -128..127)
Integer c = 128, d = 128;  c == d  // false (different objects)
```
Always compare wrappers with `equals`. Unboxing a null `Integer` throws NPE.

## Static vs instance initialisation order
1. Static blocks/fields of parent, then child (once, at class load).
2. On `new`: parent instance blocks + constructor, then child instance blocks + constructor.

## Inner classes
- Static nested class — no reference to outer instance (preferred).
- Inner (non-static) — holds implicit outer reference (can cause leaks).
- Local and anonymous classes. Lambdas replaced most anonymous class uses.

## Reflection
`Class.forName`, `getDeclaredMethods`, `setAccessible(true)`, `method.invoke`. Used by Spring (DI, annotations), Hibernate, Jackson, JUnit. Slower and bypasses encapsulation. Annotations with `@Retention(RUNTIME)` are readable by reflection.

## Immutable collections & defensive copies
`List.of`, `List.copyOf`, `Collections.unmodifiableList` (view — the backing list can still change).

## final, finally, finalize
`final` keyword (constant/no override/no inherit); `finally` block always executes; `finalize()` was a GC callback — deprecated for removal (Java 9/18), use `try-with-resources` or `Cleaner`.

## Enum
Type-safe constants; can have fields, constructors (private), methods, and implement interfaces. Enum singletons are serialization- and reflection-safe. `EnumMap`/`EnumSet` are highly efficient.
'''))
