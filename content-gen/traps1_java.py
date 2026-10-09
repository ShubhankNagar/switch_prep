"""Java language traps (all code verified with javac/java 21)."""
from traps1_common import T

A = "java"

TRAPS = [
T("trap-java-integer-cache", A, "Integer cache and ==", "Basic", "Very common",
r"""
What does this print?

```java
Integer a = 127, b = 127;
Integer c = 128, d = 128;
System.out.println(a == b);
System.out.println(c == d);
```
""",
["true / true", "true / false", "false / false", "Compile error: cannot compare Integer objects with =="], 1,
"true and true, because both pairs hold the same number.",
r"""
Because `==` compares values for `int`, candidates assume it does the same for `Integer`, and small test values
(1, 42, 100) always seem to 'work'. They don't realise that autoboxing calls `Integer.valueOf()`, which hands out
cached objects only for a fixed range. So `==` on wrappers is really an identity check that only happens to look like
value equality for small numbers.
""",
r"""
`Integer a = 127` compiles to `Integer.valueOf(127)`. `valueOf` returns a shared instance from the internal
`IntegerCache` for values from -128 to 127, so `a` and `b` are the **same object** and `a == b` is `true`. 128 is
outside the cache, so `c` and `d` are two different objects and `c == d` is `false`. On references, `==` always
compares identity, never value.

The upper bound can be raised with `-XX:AutoBoxCacheMax`, one more reason never to depend on it. `Byte`, `Short`,
`Long` (-128..127) and `Character` (0..127) cache too; `Float`/`Double` don't. A related trap:
`Long.valueOf(127L).equals(127)` is `false`, because the argument boxes to an `Integer`, which is a different type.
""",
r"""
```java
a.equals(b);                    // value comparison
Objects.equals(c, d);           // null-safe value comparison
c.intValue() == d.intValue();   // explicit unboxing (NPE if either is null)
```
""",
"Mention how this bites in production: IDs or counts compared with == pass tests with small values and break once real data goes past 127."),

T("trap-java-string-pool", A, "String pool, intern() and ==", "Basic", "Very common",
r"""
What does this print?

```java
String s1 = "hello";
String s2 = new String("hello");
String s3 = s2.intern();
String part = "hel";
String s4 = part + "lo";
System.out.println((s1 == s2) + " " + (s1 == s3) + " " + (s1 == s4));
```
""",
["true true true", "false true false", "false false false", "false true true"], 1,
"false true true: they assume any concatenation that produces \"hello\" ends up in the pool.",
r"""
Most people know that `new String()` creates a separate object, but they think every string equal to a literal gets
pooled automatically. Pooling is automatic only for **compile-time constants**. A concatenation involving a non-final
variable is evaluated at runtime (through `invokedynamic` string concatenation) and always produces a new heap object.
""",
r"""
String literals are interned, so `s1` points to the pooled "hello". `new String("hello")` always allocates a new
object, so `s1 == s2` is `false`. `intern()` returns the canonical pooled instance, so `s3` is the same object as `s1`:
`true`. `part + "lo"` is not a constant expression because `part` is an ordinary variable. It is built at runtime into
a new object, so `false`.

If `part` were declared `final String part = "hel";` it would become a compile-time constant. The compiler would then
fold `part + "lo"` into the literal "hello", and `s1 == s4` would be `true`. Since Java 7 the pool lives on the main
heap, not in PermGen. The rule: compare strings with `equals()`, and use `==` only when you really want identity.
""",
r"""
```java
s1.equals(s4);              // true
"hello".equals(input);      // literal first: no NPE when input is null
s1.equalsIgnoreCase(other);
```
""",
"Bring up the `final` variable case yourself. Knowing that constant folding changes the answer shows you understand compile time versus runtime, not just the rule.",
["Goldman Sachs"]),

T("trap-java-equals-without-hashcode", A, "equals() without hashCode() in a HashSet", "Basic", "Very common",
r"""
What does this print?

```java
class Person {
    private final String name;
    Person(String name) { this.name = name; }
    @Override public boolean equals(Object o) {
        return o instanceof Person p && p.name.equals(name);
    }
    // hashCode() NOT overridden
}

Set<Person> set = new HashSet<>();
set.add(new Person("Raj"));
set.add(new Person("Raj"));
System.out.println(set.size() + " " + set.contains(new Person("Raj")));
```
""",
["1 true", "2 false", "2 true", "1 false"], 1,
"1 true, because equals() says the two people are equal, so the set rejects the duplicate.",
r"""
Candidates think `HashSet` and `HashMap` decide equality with `equals()` alone. In fact the hash is used first to pick
a bucket, and `equals()` is called only for entries in that same bucket. If `hashCode()` doesn't match, two 'equal'
objects almost always land in different buckets, and `equals()` is never called at all.
""",
r"""
`HashSet` is backed by a `HashMap`. On `add` it computes `hashCode()` to choose a bucket. Only for entries in that
bucket with the same hash does it call `equals()`. `Object.hashCode()` is identity-based, so the two `Person` objects
get different hashes and both are stored. The size is 2 (in practice; only a freak identity-hash collision could
change that). `contains(new Person("Raj"))` computes yet another identity hash, looks in the wrong bucket and returns
`false`.

This breaks the contract in `Object`: equal objects **must** have equal hash codes. The reverse doesn't hold: unequal
objects may share a hash (a collision), and the bucket handles that. Since Java 8 a heavily collided bucket turns into
a balanced tree, which helps performance but changes nothing about correctness. Use the same fields in `equals` and
`hashCode`.
""",
r"""
```java
@Override public int hashCode() { return Objects.hash(name); }

// or let the compiler generate equals/hashCode/toString for a value type:
record Person(String name) {}
```
""",
"State the contract in both directions (equal means same hash; same hash does not mean equal) and mention that records generate both methods for value types.",
["Goldman Sachs"]),

T("trap-java-mutable-hashmap-key", A, "Mutating a HashMap key after put()", "Intermediate", "Common",
r"""
What does this print?

```java
class Key {
    int id;
    Key(int id) { this.id = id; }
    @Override public boolean equals(Object o) { return o instanceof Key k && k.id == id; }
    @Override public int hashCode() { return Integer.hashCode(id); }
}

Map<Key, String> map = new HashMap<>();
Key k = new Key(1);
map.put(k, "order-1");
k.id = 2;
System.out.println(map.get(k) + " " + map.get(new Key(1)) + " " + map.size());
```
""",
["order-1 null 1", "null order-1 1", "null null 1", "order-1 order-1 1"], 2,
"order-1 for get(k), because it is literally the same object that was put in.",
r"""
People picture a HashMap as holding on to the key object and finding it again by identity. They forget that the entry
was filed under the hash computed **at put time**. Changing a field used by `hashCode()` changes where lookups go, but
the entry stays where it was. A lookup with the old value reaches the right bucket but then fails the `equals()` check.
""",
r"""
At `put`, the entry is stored in the bucket for hash(1). After `k.id = 2`, `get(k)` computes hash(2), looks in a
different bucket and finds nothing, so it returns `null`. `get(new Key(1))` reaches the right bucket, but the stored key
now has id 2, so `equals()` fails and that's `null` too. The entry is still there (`size()` is 1 and
`containsValue("order-1")` is `true`), but no key can reach it. That's a silent leak and a source of 'lost' data.

The same applies to `HashSet` elements and to `TreeMap`/`TreeSet` entries whose `compareTo` fields change. Keys should
be immutable: `String`, `Integer`, records with immutable components, or classes whose hash fields are `final`. JPA
entities with generated ids hit this when they are added to a `HashSet` before the id is assigned.
""",
r"""
```java
record Key(int id) {}            // immutable key: equals/hashCode generated

// if a key really must change: take it out, change it, put it back
String v = map.remove(k);
k.id = 2;
map.put(k, v);
```
""",
"Say 'hash-based collections need keys whose hashCode never changes while they are inside', and connect it to why String is immutable.",
["Goldman Sachs"]),

T("trap-java-cme-foreach-remove", A, "Removing inside for-each (and the second-to-last quirk)", "Intermediate", "Very common",
r"""
What happens here? Would the answer change if we removed `"A"` instead of `"B"`?

```java
List<String> list = new ArrayList<>(List.of("A", "B", "C"));
for (String s : list) {
    if (s.equals("B")) list.remove(s);
}
System.out.println(list);
```
""",
["Throws ConcurrentModificationException", "Prints [A, C]", "Prints [A, B, C]", "Throws IndexOutOfBoundsException"], 1,
"It throws ConcurrentModificationException, because you can never remove from a list inside a for-each loop.",
r"""
'Removing inside for-each throws CME' is taught as an absolute rule, so people pattern-match on it. The exception
actually comes from the iterator's `next()`, when it notices that `modCount` has changed. If the loop ends before
`next()` is called again, nothing checks, and the bug stays hidden. Silent wrong behaviour is worse than an exception.
""",
r"""
The for-each loop uses an `Iterator`. `hasNext()` only checks `cursor != size`. `next()` checks
`modCount == expectedModCount` and throws CME on a mismatch. When "B" (index 1) is removed, the cursor is already 2
and the size drops to 2. `hasNext()` returns `false`, the loop exits without calling `next()` again, there's no
exception, and `[A, C]` is printed. Removing the **second-to-last** element always behaves like this, and the last
element is never visited, so a check on it would silently be skipped.

Remove "A" instead, and the next `next()` call throws CME. Removing "C" throws too: `hasNext()` sees cursor 3 != size 2,
so the loop calls `next()`, which throws. CME is a best-effort, fail-fast bug detector, not a guarantee, and it happens in a single
thread. It has nothing to do with multithreading.
""",
r"""
```java
list.removeIf(s -> s.equals("B"));                 // simplest and clearest

Iterator<String> it = list.iterator();              // when you need more logic
while (it.hasNext()) {
    if (it.next().equals("B")) it.remove();         // iterator's own remove keeps modCount in sync
}

List<String> kept = list.stream().filter(s -> !s.equals("B")).toList(); // build a new list
```
""",
"Explain modCount/expectedModCount and say CME is only 'best effort', so a passing test doesn't prove the loop is correct."),

T("trap-java-aslist-listof-immutability", A, "Arrays.asList vs List.of vs unmodifiable views", "Intermediate", "Common",
r"""
What happens? And what does `List.of("a").contains(null)` do?

```java
List<String> list = Arrays.asList("x", "y", "z");
list.set(0, "X");
list.add("w");
System.out.println(list);
```
""",
["Prints [X, y, z, w]", "Throws UnsupportedOperationException at set()", "Throws UnsupportedOperationException at add()", "Prints [x, y, z, w]"], 2,
"It prints [X, y, z, w], because Arrays.asList returns an ArrayList.",
r"""
The returned class really is called `ArrayList`, but it's the private nested class `java.util.Arrays$ArrayList`: a
fixed-size view over the array, not `java.util.ArrayList`. Candidates also treat all the 'read-only' factories as the
same thing, without knowing that `Arrays.asList`, `List.of`, `Collections.unmodifiableList` and `Stream.toList()` each
follow different rules.
""",
r"""
`Arrays.asList` returns a **fixed-size list backed by the array**. `set()` works and writes through to the array (and
changes to the array show up in the list), but `add`/`remove` throw `UnsupportedOperationException`. So the `set`
succeeds and the `add` throws.

`List.of(...)` is fully immutable. `set`, `add` and `remove` all throw, null elements are rejected with
`NullPointerException`, and even `contains(null)` throws NPE. `Collections.unmodifiableList(src)` is a read-only
**view**: you can't change the list through it, but later changes to `src` still show through. `Stream.toList()`
(Java 16) returns an unmodifiable list that does allow nulls. `Collectors.toList()` currently returns a mutable
`ArrayList` but doesn't promise to. Finally, `Arrays.asList(new int[]{1,2,3})` is a `List<int[]>` of size 1.
""",
r"""
```java
List<String> list = new ArrayList<>(Arrays.asList("x", "y", "z")); // mutable copy
List<String> safe = List.copyOf(input);                             // immutable defensive copy for APIs
List<Integer> ints = Arrays.stream(new int[]{1, 2, 3}).boxed().toList();
```
""",
"Contrast unmodifiable views with truly immutable copies (List.copyOf). It shows you think about defensive copying at API boundaries."),

T("trap-java-finally-return", A, "finally vs return", "Intermediate", "Common",
r"""
What does this print?

```java
static int a() {
    int x = 1;
    try { return x; }
    finally { x = 2; }
}

static int b() {
    try { return 1; }
    finally { return 2; }
}

System.out.println(a() + " " + b());
```
""",
["2 2", "1 1", "1 2", "2 1"], 2,
"2 2: since finally runs last, they reason that its changes win in both methods.",
r"""
Candidates know that `finally` always runs after `try`, so they assume it 'has the last word' on the result. They
don't separate two different cases: changing a local variable after the return value has **already been evaluated**,
and executing a new `return` statement that replaces the pending one.
""",
r"""
In `a()`, `return x` evaluates `x` (1) and saves that value before the finally block runs. Assigning `x = 2` changes
the local variable, not the saved return value, so `a()` returns 1. If `x` were a mutable object such as a
`StringBuilder`, changes to the object *would* be visible, because the saved value is the reference.

In `b()`, `return 2` inside finally completes the method abruptly and discards the pending `return 1`, so it returns 2.
A `return` in finally also **swallows exceptions**: `try { throw new RuntimeException(); } finally { return 3; }`
returns 3 and the exception disappears. That's why javac (`-Xlint:finally`) and linters warn about it. A finally
block is skipped only if the JVM halts (`System.exit`, a crash, `kill -9`) or the thread never leaves the try.
""",
r"""
Never `return` or `throw` from finally. Use finally only for cleanup, and prefer try-with-resources:

```java
try (BufferedReader in = Files.newBufferedReader(path)) {
    return in.readLine();
} // close() runs automatically; an exception from close() is attached as a suppressed exception
```
""",
"Mention that a return in finally silently swallows exceptions. That's the production consequence interviewers want to hear."),

T("trap-java-overload-resolution", A, "Overloading with null, widening, boxing, varargs", "Intermediate", "Common",
r"""
What does this print?

```java
static void m(Object o)  { System.out.println("Object"); }
static void m(String s)  { System.out.println("String"); }

static void n(long x)    { System.out.println("long"); }
static void n(Integer x) { System.out.println("Integer"); }
static void n(int... x)  { System.out.println("varargs"); }

public static void main(String[] args) {
    m(null);
    n(5);
}
```
""",
["Object / Integer", "String / long", "Compile error: ambiguous call m(null)", "String / Integer"], 1,
"Object / Integer: null 'is an Object', and 5 is 'closest to' Integer.",
r"""
People treat overload resolution as 'pick the closest-looking type' instead of the actual compile-time algorithm. Two
rules surprise them. With `null`, the **most specific** applicable type wins, and `String` is a subclass of `Object`.
And the compiler tries widening before boxing, and boxing before varargs, so widening the primitive to `long` beats
boxing it to `Integer`.
""",
r"""
Overloads are chosen at compile time in three phases: (1) exact match or primitive widening, with no boxing or
varargs; (2) boxing/unboxing allowed; (3) varargs allowed. For `n(5)`, phase 1 already finds `n(long)` through
int-to-long widening, so boxing to `Integer` is never considered. Remove `n(long)` and you get `Integer`; remove that
too and you get varargs.

For `m(null)`, both `m(Object)` and `m(String)` accept null, and Java picks the most specific one, `String`. Add
`m(Integer)` and the call no longer compiles ("reference to m is ambiguous"), because `String` and `Integer` are
unrelated and neither is more specific. Overriding is different: it is resolved at runtime from the object's actual
class, while overloading uses the declared (static) types of the arguments.
""",
r"""
Avoid overloads that differ only by primitive/boxed or related parameter types. Give them distinct names, or cast to
choose explicitly:

```java
static void logId(long id) { /* ... */ }
static void logIds(int... ids) { /* ... */ }

m((Object) null);   // explicit choice when an overload set is unavoidable
```
""",
"Name the three phases (widening, then boxing, then varargs) and contrast compile-time overloading with runtime overriding."),

T("trap-java-int-overflow-math-abs", A, "Integer overflow and Math.abs(Integer.MIN_VALUE)", "Intermediate", "Common",
r"""
A service routes keys to one of 10 shards:

```java
int shard = Math.abs(key.hashCode()) % 10;
```

Can `shard` ever be negative? What does `System.out.println(Math.abs(Integer.MIN_VALUE));` print?
""",
["No; it prints 2147483648", "No; it throws ArithmeticException", "Yes; it prints -2147483648", "No; it prints 2147483647"], 2,
"Math.abs always returns a non-negative number, so shard is always between 0 and 9.",
r"""
Developers think of `int` as a mathematical integer. The two's-complement range is asymmetric, -2,147,483,648 to
2,147,483,647, so the absolute value of `Integer.MIN_VALUE` doesn't fit. Java integer arithmetic silently wraps around
instead of throwing, so the bug never shows up in tests that use 'normal' keys.
""",
r"""
`Math.abs(Integer.MIN_VALUE)` overflows and returns `Integer.MIN_VALUE` itself, which is still negative. If a key's
`hashCode()` is exactly `Integer.MIN_VALUE` (the string "polygenelubricants" is a known example),
`Math.abs(h) % 10` is -8 and you route to a shard that doesn't exist. Java `int`/`long` arithmetic never throws on
overflow: `Integer.MAX_VALUE + 1` is `Integer.MIN_VALUE`.

The same family of bugs: binary search's `(low + high) / 2` goes negative for large indices (use
`low + (high - low) / 2` or `(low + high) >>> 1`), and `24 * 60 * 60 * 1000 * 1000` is computed in `int` (giving
500654080 instead of 86400000000) even when the result is assigned to a `long`.
""",
r"""
```java
int shard = Math.floorMod(key.hashCode(), 10);   // always 0..9
int mid   = low + (high - low) / 2;
long micros = 24L * 60 * 60 * 1000 * 1000;        // force long arithmetic from the first operand
int total = Math.addExact(a, b);                  // throws ArithmeticException on overflow
int abs   = Math.absExact(x);                     // Java 15+: throws for Integer.MIN_VALUE
```
""",
"Use the shard/bucket example. It shows you have seen the bug in a real system rather than memorised a puzzle."),

T("trap-java-bigdecimal-equals", A, "BigDecimal equals vs compareTo, new BigDecimal(0.1)", "Intermediate", "Common",
r"""
In a payments service, what does this print?

```java
BigDecimal a = new BigDecimal("2.0");
BigDecimal b = new BigDecimal("2.00");
System.out.println(a.equals(b) + " " + (a.compareTo(b) == 0));
System.out.println(new BigDecimal(0.1));
```
""",
["true true / 0.1", "false true / 0.1000000000000000055511151231257827021181583404541015625",
 "true true / 0.1000000000000000055511151231257827021181583404541015625", "false false / 0.1"], 1,
"true true and 0.1: BigDecimal is 'exact', so 2.0 equals 2.00 and 0.1 stays 0.1.",
r"""
Candidates know BigDecimal is the right type for money, so they assume it behaves like a mathematical number
everywhere. But `equals()` compares the value **and the scale**. And the `double` constructor faithfully copies the
binary approximation of 0.1, which was already inexact before BigDecimal ever saw it.
""",
r"""
`BigDecimal.equals` takes scale into account: 2.0 (scale 1) and 2.00 (scale 2) are not equal. `compareTo` compares the
numeric value only and returns 0. In practice, a `HashSet<BigDecimal>` keeps both values (size 2) while a `TreeSet`,
which uses compareTo, keeps one. And `assertEquals(new BigDecimal("2.0"), amountFromDb)` fails when the DB column has
scale 2.

`new BigDecimal(0.1)` converts the exact binary value of the double, giving
0.1000000000000000055511151231257827021181583404541015625. `BigDecimal.valueOf(0.1)` (which goes through
`Double.toString`) and `new BigDecimal("0.1")` both give 0.1. Also, `divide` without a scale and rounding mode throws
`ArithmeticException` for non-terminating results such as 1/3.
""",
r"""
```java
a.compareTo(b) == 0;                              // value equality
BigDecimal price = new BigDecimal("0.10");        // build from String
BigDecimal p2 = BigDecimal.valueOf(0.1);          // if you only have a double
BigDecimal share = total.divide(BigDecimal.valueOf(3), 2, RoundingMode.HALF_EVEN);
BigDecimal stored = amount.setScale(2, RoundingMode.HALF_UP); // normalise scale before storing/comparing
```
""",
"Say you'd normalise money to a fixed scale (or store minor units such as paise in a long) and compare with compareTo. Fintech interviewers listen for exactly that."),

T("trap-java-stream-laziness", A, "Stream laziness, short-circuiting and reuse", "Intermediate", "Common",
r"""
What does this print?

```java
Stream<Integer> s = Stream.of(1, 2, 3, 4)
    .filter(x -> { System.out.print("F" + x + " "); return x % 2 == 0; })
    .map(x -> { System.out.print("M" + x + " "); return x * 10; });
System.out.print("start ");
System.out.println(s.findFirst().get());
```
""",
["F1 F2 F3 F4 M2 M4 start 20", "start F1 F2 F3 F4 M2 M4 20", "start F1 F2 M2 20", "start 20"], 2,
"F1 F2 F3 F4 M2 M4 start 20: each operation runs over the whole list as soon as it is declared, like one loop per step.",
r"""
People imagine a stream pipeline as a series of loops: filter everything into a new collection, then map everything.
Streams are lazy. Nothing runs until a terminal operation pulls elements, and then each element travels through the
whole chain one at a time. Short-circuiting operations stop pulling as soon as they have an answer.
""",
r"""
Intermediate operations (`filter`, `map`, `peek`, `sorted`, ...) only build a pipeline. Nothing runs until a terminal
operation (`findFirst`, `collect`, `count`, `forEach`), so "start" prints first. Then elements flow one by one: 1 fails
the filter, 2 passes and is mapped to 20, and `findFirst` short-circuits. 3 and 4 are never touched.

Two related traps. A stream can be consumed only once: a second terminal call throws
`IllegalStateException: stream has already been operated upon or closed`. And since Java 9, `count()` may skip the
pipeline entirely when the size is known in advance, so `List.of("a","b").stream().peek(System.out::println).count()`
prints nothing. Never put side effects you rely on inside `peek` or `map`.
""",
r"""
Keep lambdas side-effect free, create a new stream for each use, and do side effects in the terminal operation:

```java
Supplier<Stream<Order>> paid = () -> orders.stream().filter(Order::isPaid);
long n = paid.get().count();
List<Long> ids = paid.get().map(Order::getId).toList();
```
""",
"Mention the Java 9 count() shortcut with peek. It shows you know laziness is an optimisation contract, not just 'streams are lazy'."),

T("trap-java-optional-orelse-eager", A, "Optional.orElse is eager", "Intermediate", "Common",
r"""
```java
public User getUser(long id) {
    return cache.find(id)                 // returns Optional<User>
                .orElse(loadFromDb(id));  // loadFromDb queries MySQL
}
```

The user is almost always in the cache. How often is `loadFromDb` called?
""",
["Only when the cache misses", "On every call, even on a cache hit", "Never, because orElse is lazy", "Only the first time, because Optional memoizes it"], 1,
"Only on a cache miss, because orElse is the 'fallback'.",
r"""
`orElse` reads like an if/else, so people assume the fallback is evaluated only when needed. But it is an ordinary
method call. Java evaluates all arguments **before** calling a method, so `loadFromDb(id)` runs first and its result is
passed in, then quietly thrown away whenever the Optional already has a value.
""",
r"""
`orElse(T other)` takes a value, so the argument expression is evaluated eagerly on every call. The DB query runs on
every cache hit and its result is discarded. That's a hidden performance bug, and a correctness bug if the fallback has
side effects such as inserting a default record. `orElseGet(Supplier<T>)` takes a lambda and calls it only when the
Optional is empty. Use `orElse` only for constants or values you have already computed.

Related Optional traps: `Optional.of(null)` throws `NullPointerException` (use `ofNullable`); `get()` on an empty
Optional throws `NoSuchElementException` (prefer `orElseThrow()`); and Optional is meant as a return type, not for
fields, parameters or collections.
""",
r"""
```java
return cache.find(id).orElseGet(() -> loadFromDb(id));

User u = userRepository.findById(id)
        .orElseThrow(() -> new UserNotFoundException(id));
```
""",
"Point out the side-effect angle: an `orElse(createDefaultUser())` that inserts a row on every call is the version that causes real incidents."),

T("trap-java-list-remove-index-vs-object", A, "List.remove(int) vs remove(Object)", "Basic", "Common",
r"""
What does this print?

```java
List<Integer> ids = new ArrayList<>(List.of(10, 20, 30, 1));
ids.remove(1);
System.out.println(ids);
```
""",
["[10, 20, 30]", "[10, 30, 1]", "[20, 30, 1]", "Compile error: ambiguous call"], 1,
"[10, 20, 30]: remove(1) removes the element 1.",
r"""
Candidates expect autoboxing to turn `1` into an `Integer` and call `remove(Object)`. But `List` has two overloads,
`remove(int index)` and `remove(Object o)`, and overload resolution prefers an exact primitive match over boxing. So
the index version wins and a completely different element disappears, with no error and no warning.
""",
r"""
Overload resolution first tries methods that need no boxing. `remove(int)` matches the `int` literal exactly, so it
removes the element **at index 1** (20) and leaves `[10, 30, 1]`. To remove the value 1, pass an object:
`ids.remove(Integer.valueOf(1))` gives `[10, 20, 30]`.

The trap is nastier than it looks. `Collection` and `Set` have only `remove(Object)`, so the same line removes by value
when the variable is declared as `Collection<Integer>` or `Set<Integer>`, and by index once someone refactors it to
`List<Integer>`. With a `List<Long>` and a `long` argument it removes by value, because `long` can't narrow to `int`.
These differences come from compile-time types, not from the runtime object.
""",
r"""
```java
ids.remove(Integer.valueOf(1));      // remove by value
ids.removeIf(id -> id == 1);         // clearest intent; removes all matches
int removedAt = ids.indexOf(1);      // if you really mean an index, compute it explicitly
```
""",
"Mention the Set-to-List refactoring case. It shows you think about how code can silently change meaning, not just about the puzzle."),
]
