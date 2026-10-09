from fr2_common import M, C, T, save

mcqs = [
M("Design Patterns", r'''
Why must `instance` be declared `volatile` in double-checked locking?
```java
private static volatile Config instance;
public static Config get() {
    if (instance == null) {
        synchronized (Config.class) {
            if (instance == null) instance = new Config();
        }
    }
    return instance;
}
```''', ["To make the getter faster", "Without volatile, instruction reordering can publish the reference before the constructor finishes, so another thread might see a half-built object",
 "volatile makes the constructor synchronized", "It isn't needed in Java 8+"], 1,
'''`new Config()` breaks down into allocate, initialize and assign. Without volatile, the JIT or CPU may assign before initializing. A thread passing the first unsynchronized null check could then use a partially constructed object. volatile adds the happens-before edge that prevents this.''', ["Flipkart", "Paytm", "Oracle"]),

M("Design Patterns", '''A checkout supports UPI, cards, net-banking and wallets, and new methods get added often. The payment algorithm is chosen at runtime. Which pattern fits?''',
["Singleton", "Strategy", "Observer", "Prototype"], 1,
'''Strategy puts each algorithm (each payment method) behind a shared interface such as `PaymentStrategy.pay(amount)`. The context picks one at runtime. Adding a method means adding a class, with no if-else chain to edit (Open/Closed principle).''', ["PhonePe", "Razorpay", "Flipkart"]),

M("Design Patterns", '''When an order's status changes, SMS, email, push-notification and analytics modules all need to react. Which pattern decouples them?''',
["Observer (publish-subscribe)", "Decorator", "Adapter", "Builder"], 0,
'''The order (the subject) keeps a list of listeners and notifies them on each change. Listeners can be added without touching the order class. At larger scale, the same idea becomes event-driven messaging over Kafka.''', ["Swiggy", "Zomato", "Amazon"]),

M("Design Patterns", '''A parking system creates `Car`, `Bike` or `Truck` objects from a string read from input, and callers shouldn't know the concrete classes. Which pattern fits?''',
["Factory Method / Simple Factory", "Facade", "Composite", "Memento"], 0,
'''A factory centralizes object creation, for example `VehicleFactory.create(type)`, and returns the common `Vehicle` abstraction. Callers depend only on the interface, and a new vehicle type touches only the factory.''', ["Flipkart", "Uber", "Amazon"]),

M("Design Patterns", '''An `HttpRequest` has 2 required and 9 optional fields, and should be immutable. What's the cleanest way to construct it?''',
["A telescoping constructor with 11 parameters", "The Builder pattern", "Public setters", "A Singleton"], 1,
'''A builder gives readable, chainable construction (`.timeout(5).header(...)`), can validate in `build()`, and returns an immutable object. Lombok's `@Builder` and Java's `HttpRequest.newBuilder()` are everyday examples.''', ["Amazon", "Atlassian", "Myntra"]),

M("Design Patterns", '''A pizza ordering system has to add toppings (cheese, olives, jalapeño) on top of a base pizza in any combination, where each topping adds to the cost. Which pattern avoids a subclass for every combination?''',
["Decorator", "Strategy", "Bridge", "Flyweight"], 0,
'''Each decorator wraps a `Pizza` and adds to `cost()` before delegating to the wrapped object. Wrappers can be stacked at runtime, so you don't end up with 2^n subclasses. Java I/O streams (`new BufferedReader(new InputStreamReader(...))`) are the textbook example.''', ["Zomato", "Swiggy", "Adobe"]),

M("Design Patterns", '''Your code expects `PaymentGateway.charge(Order)`, but a new third-party SDK only offers `makePayment(String json)`. Which pattern lets you plug it in without changing your callers?''',
["Adapter", "Proxy", "Mediator", "Command"], 0,
'''An adapter implements your interface and translates each call into the SDK's API. This is common for integrating payment gateways like Razorpay, Stripe or PayU behind one internal interface.''', ["Razorpay", "PhonePe", "Paytm"]),

M("Design Patterns", '''A vending machine behaves differently in the Idle, HasMoney, Dispensing and OutOfStock states, and the same button does something different in each. Which pattern fits?''',
["State", "Template Method", "Iterator", "Visitor"], 0,
'''In the State pattern, each state is its own class implementing the same actions (`insertCoin`, `selectItem`). The machine delegates to its current state object, which changes state as needed. This replaces large switch statements. It's a popular machine-coding question.''', ["Amazon", "Flipkart", "Walmart"]),

M("SOLID", '''`Square extends Rectangle` overrides `setWidth` so that it also sets the height. Code that sets width = 5 and height = 4 on a `Rectangle` and expects area 20 now gets 16. Which principle is broken?''',
["Single Responsibility", "Open/Closed", "Liskov Substitution", "Dependency Inversion"], 2,
'''Liskov Substitution says a subtype must be usable anywhere its base type is expected without breaking correctness. Square strengthens the behavior of the setters, so code written against Rectangle breaks. Prefer composition or a common `Shape` interface.''', ["Microsoft", "Atlassian"]),

M("SOLID", '''A `Bird` interface declares `fly()`, `swim()` and `walk()`. `Penguin` has to implement `fly()` by throwing UnsupportedOperationException. Which principle does this break most directly?''',
["Interface Segregation", "Open/Closed", "DRY", "KISS"], 0,
'''Interface Segregation says clients shouldn't be forced to depend on methods they don't use. Split the interface into `Flyable`, `Swimmable` and `Walkable`. The throwing method is also a Liskov warning sign.''', ["Atlassian", "Intuit"]),

M("Design Patterns", '''An incoming request passes through authentication → rate limiting → validation → logging handlers, and any handler can stop it. Which pattern is this, as used in servlet filters?''',
["Chain of Responsibility", "Composite", "Observer", "Abstract Factory"], 0,
'''Each handler either processes the request and passes it to the next, or short-circuits. Servlet `FilterChain`, the Spring Security filter chain and Spring MVC interceptors all work this way.''', ["Atlassian", "Salesforce"]),

M("OOP", '''A `House` owns `Room` objects, and rooms can't exist without the house. Which relationship is this, and how is it drawn in UML?''',
["Aggregation, hollow diamond", "Composition, filled diamond", "Association, plain line", "Inheritance, hollow triangle"], 1,
'''Composition is strong ownership: the part's lifecycle is tied to the whole, so deleting the house deletes its rooms. Aggregation is weaker, for example a Team has Players who can exist independently.''', ["Adobe", "Amazon"]),

M("Java Output", r'''
What does this print?
```java
enum Level { LOW, MEDIUM, HIGH }
System.out.println(Level.valueOf("HIGH").ordinal() + " "
    + Level.MEDIUM.compareTo(Level.HIGH) + " " + Level.values().length);
```''', ["2 -1 3", "3 -1 3", "2 1 3", "HIGH -1 3"], 0,
'''Ordinals start at 0, so HIGH is 2. `compareTo` for enums returns the difference between ordinals, 1 − 2 = −1. `values()` returns a new array of all 3 constants. Don't persist ordinals; use `@Enumerated(EnumType.STRING)` in JPA.''', ["Flipkart", "Oracle"]),

M("Java OOP", '''Class `C implements I1, I2`, and both interfaces declare `default void hello()` with different bodies. C doesn't override `hello()`. What happens?''',
["I1's version wins because it's listed first", "Compile error: C must override hello(). It can call I1.super.hello() if it wants that version",
 "Runtime exception", "Both run"], 1,
'''Java won't pick between conflicting defaults for you. The class has to resolve the diamond by overriding the method, and it can explicitly delegate with `I1.super.hello()`. A class method always takes priority over interface defaults.''', ["Microsoft", "SAP"]),

M("Java Output", r'''
What does this print?
```java
class A { void f(Object o) { System.out.print("AO "); }
          void f(String s) { System.out.print("AS "); } }
class B extends A { void f(Object o) { System.out.print("BO "); } }

A x = new B();
Object o = "hi";
x.f(o);
x.f("hi");
```''', ["AS AS", "BO AS", "BO BO", "AO AS"], 1,
'''Overload resolution uses the static types at compile time. `f(o)` binds to `f(Object)`, which B overrides, so it prints BO. `f("hi")` binds to `f(String)`, which B doesn't override, so A's version prints AS.''', ["Adobe", "Microsoft"]),

M("Concurrency in LLD", '''In a parking lot design, two gate threads call `findFreeSpot()` at the same moment and both get spot #12. What is the best minimal fix?''',
["Put Thread.sleep() between finding and assigning", "Make 'find and mark occupied' atomic: poll free spots from a concurrent queue, or CAS an AtomicBoolean on the spot",
 "Use an ArrayList", "Make the spot field static"], 1,
'''The bug is a check-then-act race. `ConcurrentLinkedQueue.poll()` or `compareAndSet(false, true)` on a spot's occupied flag claims the spot atomically, so only one thread can win it. Interviewers want to hear thread safety addressed in machine-coding rounds.''', ["Flipkart", "Uber"]),

M("Design Patterns", '''How does Spring implement `@Transactional`, `@Cacheable` and `@Async`?''',
["Bytecode rewriting of every class at compile time", "Proxies (JDK dynamic proxies or CGLIB subclasses) that wrap the bean and add behavior around method calls",
 "Reflection at every field access", "Separate threads for each bean"], 1,
'''Spring AOP wraps the bean in a proxy, which is the Proxy pattern. The proxy starts the transaction, checks the cache or submits to an executor, then delegates to the real object. That's why self-invocation and private methods aren't intercepted.''', ["Swiggy", "Walmart"]),

M("Design Patterns", '''An abstract `ReportGenerator.generate()` runs fixed steps: `fetchData() → format() → export()`. Subclasses override only `format()` to produce CSV or PDF. Which pattern is this?''',
["Template Method", "Strategy", "Builder", "Command"], 0,
'''Template Method fixes the skeleton of the algorithm in a final method of the base class and leaves some steps for subclasses to override. Strategy, by contrast, swaps the whole algorithm through composition. `AbstractList` and `HttpServlet.service()` are examples from the JDK.''', ["Myntra", "SAP"]),

M("Logical Reasoning", '''Five people P, Q, R, S and T sit in a row. S is in the middle. R is at one end. Q sits immediately to the right of P. T isn't at either end, and P isn't at either end. Who sits at the other end from R?''',
["P", "Q", "T", "S"], 1,
'''S is in seat 3. If R is in seat 5, then P and Q must be in seats 1 and 2, which puts P at an end, so that fails. So R is in seat 1, P and Q are in 4 and 5, and T is in 2. The order is R T S P Q, so Q is at the other end.''', ["Oracle", "SAP", "Goldman Sachs"]),

M("Design Patterns", '''Which statement about the Singleton pattern in Java is TRUE?''',
["Reflection and deserialization can't break a classic singleton", "An enum singleton is protected against both reflection and serialization attacks",
 "A singleton must always be lazily initialized", "Spring singleton beans are one instance per JVM"], 1,
'''The JVM guarantees one instance per enum constant and stops reflection from creating enum instances. Classic singletons need a `readResolve()` method and a guard in the constructor. Spring's singleton scope means one instance per ApplicationContext, not per JVM.''', ["Paytm", "Oracle", "JP Morgan"]),
]

coding = [
C("Design a Parking Lot (Machine Coding)", "Medium", ["Flipkart", "Amazon", "Uber", "Walmart"], r'''
Build an in-memory parking lot:
- The lot has several floors. Each floor has spots of type `BIKE`, `CAR` or `TRUCK`.
- `park(vehicleNumber, type)` assigns the lowest-numbered free spot of the matching type, starting from the lowest floor, and returns a ticket ID such as `F1-S3`. It returns `null` if the lot is full for that type.
- `unpark(ticketId)` frees the spot and returns the fee: ₹20/hour for a bike, ₹50/hour for a car, ₹100/hour for a truck, where any part of an hour counts as a full hour.
- `freeCount(type)` returns the number of free spots of that type.
- `park` must be safe to call from several gate threads.

**Example**
```
Lot: floor 1 -> [CAR, CAR, BIKE]
park("KA01", CAR)     -> "F1-S1"
park("KA02", CAR)     -> "F1-S2"
park("KA03", CAR)     -> null
unpark("F1-S1") after 90 min -> 100
```''',
["Model classes: ParkingLot, Floor, Spot, Ticket, plus a VehicleType enum carrying its hourly rate.",
 "Keep a TreeSet of free spots per vehicle type, ordered by (floor, spot), and synchronize park/unpark. Inject the clock so it can be tested."],
r'''
import java.util.*;
import java.util.function.LongSupplier;

enum VehicleType {
    BIKE(20), CAR(50), TRUCK(100);
    final int hourlyRate;
    VehicleType(int rate) { this.hourlyRate = rate; }
}

record Spot(int floor, int number, VehicleType type) {
    String id() { return "F" + floor + "-S" + number; }
}

record Ticket(String id, String vehicleNumber, Spot spot, long entryMillis) { }

class ParkingLot {
    private static final Comparator<Spot> ORDER =
        Comparator.comparingInt(Spot::floor).thenComparingInt(Spot::number);

    private final Map<VehicleType, TreeSet<Spot>> free = new EnumMap<>(VehicleType.class);
    private final Map<String, Ticket> active = new HashMap<>();
    private final LongSupplier clock;

    /** floors.get(i) lists the spot types on floor i+1. */
    ParkingLot(List<List<VehicleType>> floors, LongSupplier clockMillis) {
        this.clock = clockMillis;
        for (VehicleType t : VehicleType.values()) free.put(t, new TreeSet<>(ORDER));
        for (int f = 0; f < floors.size(); f++) {
            List<VehicleType> spots = floors.get(f);
            for (int s = 0; s < spots.size(); s++) {
                free.get(spots.get(s)).add(new Spot(f + 1, s + 1, spots.get(s)));
            }
        }
    }

    public synchronized String park(String vehicleNumber, VehicleType type) {
        Spot spot = free.get(type).pollFirst();          // atomic under the lock
        if (spot == null) return null;
        Ticket t = new Ticket(spot.id(), vehicleNumber, spot, clock.getAsLong());
        active.put(t.id(), t);
        return t.id();
    }

    public synchronized long unpark(String ticketId) {
        Ticket t = active.remove(ticketId);
        if (t == null) throw new IllegalArgumentException("Invalid ticket " + ticketId);
        free.get(t.spot().type()).add(t.spot());
        long minutes = (clock.getAsLong() - t.entryMillis()) / 60_000;
        long hours = Math.max(1, (minutes + 59) / 60);    // round up, min 1 hour
        return hours * t.spot().type().hourlyRate;
    }

    public synchronized int freeCount(VehicleType type) {
        return free.get(type).size();
    }

    public static void main(String[] args) {
        long[] now = {0};
        ParkingLot lot = new ParkingLot(
            List.of(List.of(VehicleType.CAR, VehicleType.CAR, VehicleType.BIKE)), () -> now[0]);
        System.out.println(lot.park("KA01", VehicleType.CAR));   // F1-S1
        System.out.println(lot.park("KA02", VehicleType.CAR));   // F1-S2
        System.out.println(lot.park("KA03", VehicleType.CAR));   // null
        now[0] = 90 * 60_000L;
        System.out.println(lot.unpark("F1-S1"));                  // 100
        System.out.println(lot.freeCount(VehicleType.CAR));       // 1
    }
}''',
'''Machine-coding rounds are graded on **modeling, correctness and extensibility**. Here `VehicleType` holds its own rate, so pricing lives with the type. `Spot` and `Ticket` are immutable records. The free spots for each type sit in a `TreeSet` ordered by floor and then spot number, so "nearest free spot" is just `pollFirst()` in O(log n). `park` and `unpark` are `synchronized`, which makes the find-and-claim step atomic and removes the double-allocation race that interviewers check for. The clock is injected so fees can be unit tested. Good extension points to mention: a `PricingStrategy` interface for weekend or surge pricing, letting a bike use a car spot as a fallback, display boards as observers, and per-floor locks for better throughput.''',
"O(log S) per park/unpark", "O(S + active tickets)", None),

C("LRU Cache", "Medium", ["Amazon", "Microsoft", "Flipkart", "PhonePe", "Swiggy"], r'''
Design a Least Recently Used cache with a fixed `capacity`:
- `int get(int key)` returns the value, or −1 if the key is missing, and marks the key as most recently used.
- `void put(int key, int value)` inserts or updates the key. If that pushes the size over capacity, evict the least recently used key.

Both operations must run in **O(1)** time.

**Example**
```
LRUCache c = new LRUCache(2);
c.put(1,1); c.put(2,2);
c.get(1);      // 1
c.put(3,3);    // evicts key 2
c.get(2);      // -1
c.put(4,4);    // evicts key 1
c.get(1);      // -1
c.get(3);      // 3
c.get(4);      // 4
```
**Constraints:** 1 ≤ capacity ≤ 3000, up to 2·10^5 calls. Implement it yourself, without relying on LinkedHashMap.''',
["Combine a HashMap (key → node) with a doubly linked list ordered by recency.",
 "Sentinel head and tail nodes remove the null checks. On every access, move the node to just after head. Evict from just before tail."],
r'''
import java.util.HashMap;
import java.util.Map;

class LRUCache {
    private static final class Node {
        int key, value;
        Node prev, next;
        Node(int k, int v) { key = k; value = v; }
    }

    private final int capacity;
    private final Map<Integer, Node> map = new HashMap<>();
    private final Node head = new Node(0, 0);   // most recent after head
    private final Node tail = new Node(0, 0);   // least recent before tail

    public LRUCache(int capacity) {
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        Node n = map.get(key);
        if (n == null) return -1;
        unlink(n);
        addFront(n);
        return n.value;
    }

    public void put(int key, int value) {
        Node n = map.get(key);
        if (n != null) {
            n.value = value;
            unlink(n);
            addFront(n);
            return;
        }
        if (map.size() == capacity) {
            Node lru = tail.prev;
            unlink(lru);
            map.remove(lru.key);
        }
        n = new Node(key, value);
        map.put(key, n);
        addFront(n);
    }

    private void unlink(Node n) {
        n.prev.next = n.next;
        n.next.prev = n.prev;
    }

    private void addFront(Node n) {
        n.next = head.next;
        n.prev = head;
        head.next.prev = n;
        head.next = n;
    }
}''',
'''The HashMap gives O(1) lookup of a key's node. The doubly linked list keeps entries in recency order and supports O(1) removal from anywhere, because each node knows both of its neighbors. Every `get` or `put` moves the node to the front, so the least recently used entry is always `tail.prev`. Sentinel nodes mean we never special-case an empty list or the ends. Each node stores its key so eviction can also delete the map entry. Common follow-ups: the three-line `LinkedHashMap(cap, 0.75f, true)` version that overrides `removeEldestEntry`, making it thread-safe (a lock or a segmented design), adding TTL expiry, and LFU as a variant (LC 460).''',
"O(1) per operation", "O(capacity)", "https://leetcode.com/problems/lru-cache/"),

C("In-Memory Key-Value Store with Nested Transactions", "Medium", ["Atlassian", "Uber", "Razorpay", "Salesforce"], r'''
Implement an in-memory database that supports:
- `set(key, value)`, `get(key)` (returns null if missing), `delete(key)`
- `count(value)`: how many keys currently hold this value
- `begin()`: start a transaction. Transactions **can be nested**.
- `rollback()`: undo every change made in the innermost open transaction. Returns false if no transaction is open.
- `commit()`: make all open transactions permanent. Returns false if none are open.

**Example**
```
set a 10;  begin;  set a 20;  begin;  delete a;
get a          -> null
rollback;  get a -> 20
rollback;  get a -> 10
count 10       -> 1
```
**Constraints:** up to 10^5 operations. `get` and `count` must be O(1).''',
["Keep the live data in a map, plus a value → count map for count().",
 "For each open transaction, push a map of the original values of keys it touched (an undo log). Rollback restores them, and commit just clears the stack."],
r'''
import java.util.*;

class KeyValueStore {
    private final Map<String, String> data = new HashMap<>();
    private final Map<String, Integer> valueCounts = new HashMap<>();
    // each frame: key -> value before this transaction first touched it (null = absent)
    private final Deque<Map<String, String>> txStack = new ArrayDeque<>();

    public String get(String key) { return data.get(key); }

    public int count(String value) { return valueCounts.getOrDefault(value, 0); }

    public void set(String key, String value) {
        recordUndo(key);
        apply(key, value);
    }

    public void delete(String key) {
        recordUndo(key);
        apply(key, null);
    }

    public void begin() { txStack.push(new HashMap<>()); }

    public boolean rollback() {
        if (txStack.isEmpty()) return false;
        Map<String, String> undo = txStack.pop();
        for (Map.Entry<String, String> e : undo.entrySet()) apply(e.getKey(), e.getValue());
        return true;
    }

    public boolean commit() {
        if (txStack.isEmpty()) return false;
        txStack.clear();                       // changes are already live in data
        return true;
    }

    private void recordUndo(String key) {
        Map<String, String> frame = txStack.peek();
        if (frame != null && !frame.containsKey(key)) frame.put(key, data.get(key));
    }

    private void apply(String key, String newValue) {
        String old = newValue == null ? data.remove(key) : data.put(key, newValue);
        if (old != null) valueCounts.merge(old, -1, (a, b) -> a + b == 0 ? null : a + b);
        if (newValue != null) valueCounts.merge(newValue, 1, Integer::sum);
    }

    public static void main(String[] args) {
        KeyValueStore db = new KeyValueStore();
        db.set("a", "10");
        db.begin(); db.set("a", "20");
        db.begin(); db.delete("a");
        System.out.println(db.get("a"));      // null
        db.rollback(); System.out.println(db.get("a"));   // 20
        db.rollback(); System.out.println(db.get("a"));   // 10
        System.out.println(db.count("10"));   // 1
    }
}''',
'''Changes are written **directly to the live map**, and each open transaction keeps an **undo log**: the value a key had before that transaction first touched it. Recording only the first touch keeps each frame no larger than the number of distinct keys changed. Rollback replays the top frame through the same `apply` method, so `valueCounts` stays correct with no extra logic. Commit just discards the undo stack, which is O(1) apart from clearing. The other design is a stack of write-overlay maps, where reads check the frames from top to bottom. That makes commit and rollback cheap but `get` O(depth), which breaks the O(1) requirement. Interviewers ask candidates to explain this trade-off, and it's the same idea as undo logs in real databases.''',
"O(1) per op; rollback O(keys touched)", "O(n + total undo entries)", None),

C("Snake and Ladder Game (Machine Coding)", "Medium", ["Swiggy", "Flipkart", "Zomato", "Myntra"], r'''
Build a Snake and Ladder game:
- The board has cells `1..100`. Snakes map a head to a lower tail. Ladders map a bottom to a higher top.
- Players take turns in order and roll one die (1–6). The dice must be injectable so the game can be tested.
- If a roll would move a player past 100, they stay where they are.
- After moving, follow a snake or ladder if one starts on that cell.
- The first player to land exactly on 100 wins. `play()` returns the winner's name and logs each move.

**Example**
```
Snakes: 14->7, Ladders: 3->22
Players: Raj, Amit. Dice sequence: 3, 6, ...
Raj rolled 3: 0 -> 3 -> 22      (ladder)
Amit rolled 6: 0 -> 6
...
```''',
["Separate concerns: Board (jumps map), Dice (interface), Player, Game (turn queue).",
 "Use a Queue<Player> for turn order: poll the player, move them, and offer them back unless they've won."],
r'''
import java.util.*;

interface Dice { int roll(); }

class RandomDice implements Dice {
    private final Random random = new Random();
    public int roll() { return random.nextInt(6) + 1; }
}

class Board {
    private final int size;
    private final Map<Integer, Integer> jumps = new HashMap<>();   // snakes and ladders

    Board(int size, Map<Integer, Integer> snakes, Map<Integer, Integer> ladders) {
        this.size = size;
        snakes.forEach((h, t) -> { if (t >= h) throw new IllegalArgumentException("bad snake"); jumps.put(h, t); });
        ladders.forEach((b, t) -> { if (t <= b) throw new IllegalArgumentException("bad ladder"); jumps.put(b, t); });
    }

    int size() { return size; }
    int finalPosition(int cell) { return jumps.getOrDefault(cell, cell); }
}

class Player {
    final String name;
    int position = 0;
    Player(String name) { this.name = name; }
}

class Game {
    private final Board board;
    private final Dice dice;
    private final Deque<Player> turns = new ArrayDeque<>();

    Game(Board board, Dice dice, List<String> names) {
        this.board = board;
        this.dice = dice;
        names.forEach(n -> turns.offer(new Player(n)));
    }

    String play() {
        while (true) {
            Player p = turns.poll();
            int roll = dice.roll();
            int target = p.position + roll;
            if (target > board.size()) {
                System.out.println(p.name + " rolled " + roll + ": stays at " + p.position);
            } else {
                int landed = board.finalPosition(target);
                System.out.println(p.name + " rolled " + roll + ": " + p.position + " -> " + target
                    + (landed != target ? " -> " + landed : ""));
                p.position = landed;
                if (landed == board.size()) return p.name;
            }
            turns.offer(p);
        }
    }

    public static void main(String[] args) {
        Board board = new Board(100, Map.of(14, 7, 99, 10), Map.of(3, 22, 25, 98));
        Iterator<Integer> seq = List.of(3, 6, 3, 1, 2).iterator();     // scripted dice
        Dice dice = () -> seq.hasNext() ? seq.next() : 1;
        System.out.println("Winner: " + new Game(board, dice, List.of("Raj", "Amit")).play());
    }
}''',
'''The design splits responsibilities cleanly. `Board` holds the rules for jumps and validates that snakes go down and ladders go up. `Dice` is an interface, so tests inject a scripted sequence while production uses `RandomDice`. That's the Strategy/DI idea interviewers look for. `Game` handles turns with a queue, which also supports any number of players. Because snakes and ladders share one jump map, landing logic is a single lookup. Extensions candidates are asked about: multiple dice, rolling a 6 for an extra turn, continuing until all players finish, and preventing cycles in jump configurations. Always show a runnable `main` with deterministic input during a machine-coding round.''',
"O(1) per turn", "O(snakes + ladders + players)", None),
]

theory = [
T("How do you approach a 90-minute machine coding round?", '''1. **Clarify for about 5–10 minutes:** list the must-have features and confirm which are optional. Ask about concurrency, persistence (usually in-memory) and the input format.
2. **Model the entities** (nouns become classes, verbs become methods) and sketch the interfaces before writing code.
3. **Layer the code:** models → repository (in-memory maps) → services (business logic) → a driver or CLI. Keep `main` thin.
4. **Make the core flow work first**, end to end, then add the extras. Code that doesn't run is the biggest reason candidates get rejected.
5. Use **patterns where they fit naturally**, such as Strategy for pricing or Factory for creation. Don't force them.
6. Handle **edge cases and exceptions** with custom exceptions and validation.
7. Mention **thread safety** and extensibility.
8. Keep **readable names and small methods**, and run a demo with sample input.

Interviewers usually grade: runs correctly, modularity, extensibility, and code quality.''', ["Flipkart", "Swiggy", "PhonePe", "Razorpay"]),

T("Explain the SOLID principles with one example each.", '''- **S, Single Responsibility:** a class should have only one reason to change. `InvoiceService` computes totals, `InvoicePrinter` formats, `InvoiceRepository` persists.
- **O, Open/Closed:** open for extension, closed for modification. Add `UpiPayment implements PaymentStrategy` without editing a switch statement.
- **L, Liskov Substitution:** subtypes must honor the base contract. `Square extends Rectangle` breaks setter expectations.
- **I, Interface Segregation:** prefer small, specific interfaces. Use `Flyable` and `Swimmable` instead of a fat `Bird`.
- **D, Dependency Inversion:** high-level code depends on abstractions. `OrderService` depends on a `PaymentGateway` interface, and Spring injects `RazorpayGateway`.

In interviews, tie these to your own Spring Boot work. Constructor injection with interfaces is DIP in practice, and Spring profiles that swap implementations show OCP.''', ["Atlassian", "Intuit", "Walmart", "SAP"]),

T("What are the key classes and decisions when designing a parking lot?", '''**Entities:** `ParkingLot` (singleton or injected), `Floor`, `ParkingSpot` (type, size, occupied), `Vehicle` (abstract, with Car/Bike/Truck or a type enum), `Ticket`, `Payment`, `EntryGate`/`ExitGate` and `DisplayBoard`.

**Decisions:**
- **Spot allocation strategy** (Strategy pattern): nearest to the entrance, lowest floor first, or evenly spread. Keep free spots in a min-heap or TreeSet per type for O(log n) allocation.
- **Pricing strategy:** hourly, flat, weekend or EV-charging rates, behind a `PricingStrategy` interface.
- **Concurrency:** several gates allocate at the same time, so allocation has to be atomic (a lock per type, or CAS).
- **Observers:** display boards update when spot counts change.
- **Extensibility:** new vehicle types, reserved or handicap spots.

Walk through the flow: vehicle arrives → find a spot → issue a ticket → exit → calculate the fee → pay → free the spot.''', ["Amazon", "Flipkart", "Uber", "Walmart"]),

T("What is the difference between the Strategy and State patterns?", '''The class structures look the same: a context holds a reference to an interface, and concrete classes implement it. The **intent** is what differs.

**Strategy:** the *client* chooses an interchangeable algorithm, and it usually stays fixed for that operation. Strategies don't know about each other. Examples: payment methods, sorting comparators, pricing rules.

**State:** the object's *behavior changes as its internal state changes*, and the **state objects themselves trigger transitions**, such as `IdleState.insertCoin()` setting the machine to `HasMoneyState`. States know which state comes next. Examples: vending machines, order lifecycles (PLACED → PAID → SHIPPED), TCP connections.

One way to remember it: Strategy answers *how* to do something, and State answers *what I can do right now*. State replaces large if/switch blocks over a status field. Strategy replaces if/switch blocks over an algorithm type.''', ["Uber", "Atlassian", "Flipkart"]),

T("How do you make a Singleton thread-safe, and how can a Singleton be broken?", '''**Thread-safe options:**
1. *Eager initialization*: `private static final X INSTANCE = new X();`. Class loading is thread-safe.
2. *Bill Pugh holder idiom*: a static nested Holder class creates the instance on first access. It's lazy and needs no locks.
3. *Double-checked locking* with a **volatile** field.
4. *Enum singleton*: `enum X { INSTANCE; }`. This is the most robust option.

**How it gets broken:**
- **Reflection**: `setAccessible(true)` on the private constructor. Guard against it by throwing if the instance already exists.
- **Serialization**: deserializing creates a new object. Add `readResolve()` returning INSTANCE.
- **Cloning**: override `clone()` to throw.
- **Multiple classloaders**: each loader gets its own copy.

Enums avoid the reflection and serialization problems automatically. In Spring, prefer singleton-scoped beans over hand-written singletons because they're easier to test and mock.''', ["Paytm", "Oracle", "JP Morgan", "Goldman Sachs"]),

T("Composition vs inheritance: when do you prefer each?", '''**Inheritance** (is-a) reuses code by extending a class. It's tightly coupled: subclasses depend on parent internals (the fragile base class problem), the relationship is fixed at compile time, and Java allows only single class inheritance.

**Composition** (has-a) builds behavior by holding references to other objects, usually through interfaces. It's flexible: you can swap behavior at runtime, test with mocks, and combine capabilities without class explosion.

**Prefer composition** for most designs. Strategy, Decorator and DI all rely on it. A `Car` *has an* `Engine`, which lets you swap a PetrolEngine for an EVEngine.

**Use inheritance** when there's a true, stable is-a relationship that satisfies Liskov, or for framework hooks and template methods (for example extending `OncePerRequestFilter`).

Rule of thumb from *Effective Java*: "Favor composition over inheritance". Design for inheritance deliberately, or prevent it with `final`.''', ["Atlassian", "Adobe", "Salesforce"]),
]

save(11, "Machine Coding / LLD Day",
     "Low-level design practice: small machine-coding problems with full Java solutions, plus the design patterns and SOLID questions interviewers use to probe them.",
     mcqs, coding, theory)
