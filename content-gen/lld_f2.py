from lld_common import *

topics = []

topics.append(T(
"design-patterns-structural", "Structural Patterns: Adapter, Decorator, Facade, Proxy, Composite", 5, "Intermediate", 25,
"How to compose classes and objects into larger structures: Adapter, Decorator, Facade, Proxy and Composite with Java code and LLD use cases.",
r'''
Structural patterns describe **how objects are wired together**. They mostly use composition: one object wraps or holds others behind a shared interface.

## 1. Adapter - make incompatible interfaces work together

**Problem:** your code expects `PaymentGateway.pay(amountInRupees)`, but a third-party SDK offers `makePayment(long paise, String currency)`.

```java
interface PaymentGateway { boolean pay(double rupees); }

// Third-party class you cannot change
class StripeSdk {
    public String makePayment(long paise, String currency) {
        System.out.println("Stripe charged " + paise + " " + currency);
        return "SUCCESS";
    }
}

class StripeAdapter implements PaymentGateway {
    private final StripeSdk sdk;
    StripeAdapter(StripeSdk sdk) { this.sdk = sdk; }
    public boolean pay(double rupees) {
        long paise = Math.round(rupees * 100);
        return "SUCCESS".equals(sdk.makePayment(paise, "INR"));
    }
}

PaymentGateway gw = new StripeAdapter(new StripeSdk());
gw.pay(499.0);
```
Real Java examples: `Arrays.asList()` (array -> List), `InputStreamReader` (byte stream -> char reader). In LLD: integrating multiple payment providers or legacy services behind one interface.

## 2. Decorator - add responsibilities dynamically

**Problem:** a coffee can have any combination of milk, sugar, whipped cream. Subclassing every combination explodes (`CoffeeWithMilkAndSugar`...). Decorator wraps an object implementing the **same interface** and adds behaviour before/after delegating.

```java
interface Beverage { double cost(); String description(); }

class Espresso implements Beverage {
    public double cost() { return 100; }
    public String description() { return "Espresso"; }
}

abstract class AddOn implements Beverage {
    protected final Beverage inner;
    AddOn(Beverage inner) { this.inner = inner; }
}
class Milk extends AddOn {
    Milk(Beverage b) { super(b); }
    public double cost() { return inner.cost() + 20; }
    public String description() { return inner.description() + ", milk"; }
}
class Caramel extends AddOn {
    Caramel(Beverage b) { super(b); }
    public double cost() { return inner.cost() + 35; }
    public String description() { return inner.description() + ", caramel"; }
}

Beverage order = new Caramel(new Milk(new Espresso()));
System.out.println(order.description() + " = " + order.cost()); // Espresso, milk, caramel = 155.0
```
Java I/O is built on decorators: `new BufferedReader(new InputStreamReader(new FileInputStream(f)))`. LLD uses: pizza toppings, adding logging/metrics/retry around a service, pricing add-ons (insurance, GST) on a booking.

## 3. Facade - one simple entry point to a complex subsystem

**Problem:** placing an order requires inventory check, payment, invoice and shipping services. Clients should not orchestrate all of them.

```java
class InventoryService { boolean reserve(String sku, int qty) { return true; } }
class PaymentService { boolean charge(String user, double amt) { return true; } }
class ShippingService { String ship(String sku, String addr) { return "TRK-1"; } }
class InvoiceService { void generate(String user, double amt) { System.out.println("Invoice sent"); } }

class OrderFacade {
    private final InventoryService inv = new InventoryService();
    private final PaymentService pay = new PaymentService();
    private final ShippingService ship = new ShippingService();
    private final InvoiceService invoice = new InvoiceService();

    public String placeOrder(String user, String sku, int qty, double amt, String addr) {
        if (!inv.reserve(sku, qty)) throw new IllegalStateException("out of stock");
        if (!pay.charge(user, amt)) throw new IllegalStateException("payment failed");
        invoice.generate(user, amt);
        return ship.ship(sku, addr);
    }
}
```
Facade does not hide the subsystem completely - advanced clients may still use it directly. Your Spring `@Service` classes that call several repositories and clients are often facades. LLD uses: `ATM` class over card reader, cash dispenser, bank service; `BookMyShowFacade`.

## 4. Proxy - a stand-in that controls access

Same interface as the real object, but adds **access control, lazy loading, caching, logging or remote access**.

```java
interface ReportService { String getReport(String id); }

class RealReportService implements ReportService {
    public String getReport(String id) {
        System.out.println("Expensive DB call for " + id);
        return "Report-" + id;
    }
}

class CachingReportProxy implements ReportService {
    private final ReportService real;
    private final Map<String, String> cache = new HashMap<>();
    CachingReportProxy(ReportService real) { this.real = real; }
    public String getReport(String id) {
        return cache.computeIfAbsent(id, real::getReport);
    }
}

class SecuredReportProxy implements ReportService {
    private final ReportService real; private final String role;
    SecuredReportProxy(ReportService real, String role) { this.real = real; this.role = role; }
    public String getReport(String id) {
        if (!"ADMIN".equals(role)) throw new SecurityException("forbidden");
        return real.getReport(id);
    }
}
```

**Proxy vs Decorator** (common question): structurally identical (wrap + same interface). The difference is **intent**: Decorator *adds features* and is usually stacked by the client; Proxy *controls access* to the real subject and often manages its lifecycle. Spring AOP (`@Transactional`, `@Cacheable`) works by generating proxies around your beans - a great connection to make from your experience. Hibernate lazy-loaded entities are proxies too.

## 5. Composite - treat individual objects and groups uniformly

**Problem:** a file system has files and folders; folders contain files and other folders. You want `size()` to work on both.

```java
interface FileSystemNode {
    String name();
    long size();
    void print(String indent);
}

class FileNode implements FileSystemNode {
    private final String name; private final long size;
    FileNode(String name, long size) { this.name = name; this.size = size; }
    public String name() { return name; }
    public long size() { return size; }
    public void print(String indent) { System.out.println(indent + name + " (" + size + ")"); }
}

class Folder implements FileSystemNode {
    private final String name;
    private final List<FileSystemNode> children = new ArrayList<>();
    Folder(String name) { this.name = name; }
    public Folder add(FileSystemNode n) { children.add(n); return this; }
    public String name() { return name; }
    public long size() { return children.stream().mapToLong(FileSystemNode::size).sum(); }
    public void print(String indent) {
        System.out.println(indent + name + "/");
        children.forEach(c -> c.print(indent + "  "));
    }
}

Folder root = new Folder("root")
    .add(new FileNode("a.txt", 100))
    .add(new Folder("img").add(new FileNode("logo.png", 2048)));
System.out.println(root.size()); // 2148
```
LLD uses: file systems, org charts (employee/manager), menu with sub-menus, product bundles (a combo meal that contains items), expression trees.

## Summary

| Pattern | Keyword | Wraps? | LLD example |
|---|---|---|---|
| Adapter | convert interface | one adaptee | Multiple payment SDKs |
| Decorator | add behaviour | same interface, stackable | Pizza toppings, logging wrapper |
| Facade | simplify | many subsystems | Order placement, ATM |
| Proxy | control access | same interface, one subject | Caching, auth, lazy load, rate limiting |
| Composite | tree, uniform | children of same type | File system, bundles |
''',
["Adapter converts one interface into another expected by the client; ideal for third-party SDK integration.",
 "Decorator wraps an object with the same interface to add behaviour; decorators can be stacked (Java I/O streams).",
 "Facade provides one simple method over a complex subsystem of services without forbidding direct access.",
 "Proxy shares the subject's interface but controls access: caching, security, lazy loading, remote calls.",
 "Proxy and Decorator look identical structurally; they differ by intent (control access vs add features).",
 "Spring AOP features like @Transactional and @Cacheable are implemented with proxies around beans.",
 "Composite lets clients treat leaves and containers uniformly; use it for trees like file systems and bundles."],
[("What is the difference between Adapter and Facade?",
  r'''**Adapter** makes an existing class usable through a *different, already expected* interface - it converts one interface to another, usually wrapping a single object (e.g., `StripeAdapter implements PaymentGateway`). **Facade** defines a *new, simpler* interface over a *subsystem of many classes* to reduce complexity for clients (e.g., `OrderFacade.placeOrder()` calling inventory, payment and shipping). Adapter is about compatibility; Facade is about simplification.'''),
 ("Proxy vs Decorator - how do you tell them apart?",
  r'''Both implement the same interface as the wrapped object and delegate to it. The difference is intent and control. A **Decorator** adds responsibilities and is composed by the client, often in stacks (`new Caramel(new Milk(espresso))`). A **Proxy** controls access to a real subject - caching, authorization, lazy creation, remoting - and the client usually does not know it is talking to a proxy. Spring's `@Transactional` is a proxy because it manages access around the method call.'''),
 ("Where have you seen the Decorator pattern in the JDK?",
  r'''Java I/O: `BufferedInputStream`, `DataInputStream`, `GZIPInputStream` all extend `FilterInputStream` and wrap another `InputStream`, adding buffering, typed reads or decompression. You stack them: `new DataInputStream(new BufferedInputStream(new FileInputStream("f")))`. Also `Collections.unmodifiableList()` and `Collections.synchronizedList()` wrap a list with the same interface while adding read-only or synchronized behaviour.'''),
 ("How would you model a combo meal containing items and other combos?",
  r'''Use Composite. Define `interface MenuComponent { String name(); double price(); }`. `MenuItem` is a leaf with a fixed price. `Combo` holds a `List<MenuComponent>` and computes `price()` as the sum of children minus a combo discount. Because a `Combo` is itself a `MenuComponent`, combos can contain combos, and the cart treats single items and combos identically when computing totals.''')],
[RG, {"title": "Refactoring.Guru - Decorator", "url": "https://refactoring.guru/design-patterns/decorator"},
 {"title": "Refactoring.Guru - Proxy", "url": "https://refactoring.guru/design-patterns/proxy"}, ALLD]
))

topics.append(T(
"design-patterns-behavioral", "Behavioral Patterns: Strategy, Observer, Command, State, Template Method, Chain of Responsibility, Iterator", 6, "Intermediate", 35,
"The behavioural patterns that dominate LLD rounds, with compact Java implementations and the problems in which each one appears.",
r'''
Behavioral patterns are about **how objects communicate and divide responsibilities**. They are the most used patterns in machine coding because most variation is in *behaviour*.

## 1. Strategy - interchangeable algorithms

```java
interface PricingStrategy { double price(long minutes); }
class HourlyPricing implements PricingStrategy {
    public double price(long m) { return Math.ceil(m / 60.0) * 50; }
}
class FlatPricing implements PricingStrategy {
    public double price(long m) { return 100; }
}
class BillingService {
    private PricingStrategy strategy;
    BillingService(PricingStrategy s) { this.strategy = s; }
    void setStrategy(PricingStrategy s) { this.strategy = s; }  // swap at runtime
    double bill(long minutes) { return strategy.price(minutes); }
}
```
Appears in: parking fees, Splitwise split types (equal/exact/percent), elevator scheduling, cab matching, rate limiting algorithms, cache eviction.

## 2. Observer - publish/subscribe inside a process

```java
interface StockObserver { void onPriceChange(String symbol, double price); }

class StockTicker {
    private final List<StockObserver> observers = new CopyOnWriteArrayList<>();
    void subscribe(StockObserver o) { observers.add(o); }
    void unsubscribe(StockObserver o) { observers.remove(o); }
    void update(String sym, double price) {
        observers.forEach(o -> o.onPriceChange(sym, price));
    }
}

ticker.subscribe((s, p) -> System.out.println("Mobile alert " + s + " " + p));
```
Appears in: notifications (order status, seat available), pub-sub, auction bids, stock alerts. `CopyOnWriteArrayList` avoids `ConcurrentModificationException` if listeners unsubscribe during notification.

## 3. Command - encapsulate a request as an object

Enables undo/redo, queuing, logging and macro operations.

```java
interface Command { void execute(); void undo(); }

class TextEditor { StringBuilder text = new StringBuilder(); }

class AppendCommand implements Command {
    private final TextEditor ed; private final String s;
    AppendCommand(TextEditor ed, String s) { this.ed = ed; this.s = s; }
    public void execute() { ed.text.append(s); }
    public void undo() { ed.text.setLength(ed.text.length() - s.length()); }
}

class CommandManager {
    private final Deque<Command> history = new ArrayDeque<>();
    void run(Command c) { c.execute(); history.push(c); }
    void undo() { if (!history.isEmpty()) history.pop().undo(); }
}
```
Appears in: text editors, remote controls/smart home, transaction rollback, CLI command parsing in machine coding (`Map<String, CommandHandler>` instead of a giant switch).

## 4. State - behaviour changes with internal state

Replace `if (state == IDLE) ... else if (state == HAS_COIN)` sprinkled across every method with state objects.

```java
interface MachineState {
    void insertCoin(VendingMachine m);
    void dispense(VendingMachine m);
}

class IdleState implements MachineState {
    public void insertCoin(VendingMachine m) {
        System.out.println("Coin accepted");
        m.setState(new HasCoinState());
    }
    public void dispense(VendingMachine m) { System.out.println("Insert coin first"); }
}

class HasCoinState implements MachineState {
    public void insertCoin(VendingMachine m) { System.out.println("Already has coin"); }
    public void dispense(VendingMachine m) {
        System.out.println("Dispensing item");
        m.setState(new IdleState());
    }
}

class VendingMachine {
    private MachineState state = new IdleState();
    void setState(MachineState s) { state = s; }
    void insertCoin() { state.insertCoin(this); }
    void dispense() { state.dispense(this); }
}
```
**State vs Strategy:** same structure, different intent. Strategy is chosen by the client and rarely changes itself; State objects **trigger transitions** to other states. Appears in: vending machine, ATM, elevator, order lifecycle, traffic light, document workflow.

## 5. Template Method - fixed skeleton, variable steps

```java
abstract class DataExporter {
    // template method: final so subclasses cannot change the order
    public final void export() {
        List<String> rows = fetch();
        String body = format(rows);
        write(body);
    }
    protected List<String> fetch() { return List.of("a", "b"); }   // common step
    protected abstract String format(List<String> rows);           // varies
    protected void write(String body) { System.out.println(body); } // hook, overridable
}
class CsvExporter extends DataExporter {
    protected String format(List<String> r) { return String.join(",", r); }
}
class JsonExporter extends DataExporter {
    protected String format(List<String> r) { return "[\"" + String.join("\",\"", r) + "\"]"; }
}
```
Uses inheritance (Strategy uses composition). Seen in Spring's `JdbcTemplate`, `AbstractList`. Appears in: game turn loop (board games), report generation, payment flows with common validation steps.

## 6. Chain of Responsibility - pass a request along handlers

```java
abstract class CashHandler {
    private CashHandler next;
    private final int note;
    CashHandler(int note) { this.note = note; }
    CashHandler setNext(CashHandler n) { this.next = n; return n; }

    void dispense(int amount) {
        int count = amount / note;
        int rest = amount % note;
        if (count > 0) System.out.println(count + " x Rs " + note);
        if (rest > 0) {
            if (next == null) throw new IllegalStateException("Cannot dispense " + rest);
            next.dispense(rest);
        }
    }
}
class TwoThousand extends CashHandler { TwoThousand() { super(2000); } }
class FiveHundred extends CashHandler { FiveHundred() { super(500); } }
class Hundred extends CashHandler { Hundred() { super(100); } }

CashHandler chain = new TwoThousand();
chain.setNext(new FiveHundred()).setNext(new Hundred());
chain.dispense(3700); // 1 x 2000, 3 x 500, 2 x 100
```
Appears in: ATM dispensing, logger levels, request validation/filters (Servlet filter chain, Spring Security filter chain), approval workflows (manager -> director -> VP), discount rule pipelines.

## 7. Iterator - traverse without exposing internals

```java
class Playlist implements Iterable<String> {
    private final String[] songs;
    Playlist(String... s) { songs = s; }
    public Iterator<String> iterator() {
        return new Iterator<>() {
            int i = 0;
            public boolean hasNext() { return i < songs.length; }
            public String next() {
                if (!hasNext()) throw new NoSuchElementException();
                return songs[i++];
            }
        };
    }
}
for (String s : new Playlist("A", "B")) System.out.println(s);
```
Implementing `Iterable` makes your class work with for-each. Appears in: custom collections, paginated results, tree traversal (in-order iterator), shuffled/repeat playlists (different iterators over the same data).

## Picking the right behavioural pattern

| Requirement phrase | Pattern |
|---|---|
| "support multiple algorithms/rules, choose at runtime" | Strategy |
| "notify users/systems when X changes" | Observer |
| "undo", "queue requests", "macro", "replay" | Command |
| "machine behaves differently in each status" | State |
| "same steps, some steps differ per type" | Template Method |
| "try handlers in order until one handles it" | Chain of Responsibility |
| "traverse in different orders without exposing structure" | Iterator |
''',
["Strategy encapsulates interchangeable algorithms behind an interface and is the most common LLD pattern.",
 "Observer lets many subscribers react to a subject's changes; use CopyOnWriteArrayList for safe iteration.",
 "Command turns requests into objects, enabling undo/redo, queuing and clean CLI command handling.",
 "State replaces status if/else chains; each state class handles events and decides the next state.",
 "Template Method fixes an algorithm skeleton in a final method and lets subclasses override specific steps.",
 "Chain of Responsibility passes a request through linked handlers: ATM notes, log levels, filter chains.",
 "Iterator exposes traversal without exposing internals; implementing Iterable enables for-each loops."],
[("What is the difference between the State and Strategy patterns?",
  r'''Structurally both delegate to an interface implementation. **Strategy** represents *how* to do one task; the client picks a strategy and strategies are independent and unaware of each other. **State** represents *what the object currently is*; state objects know about the context and trigger transitions (`HasCoinState` sets the machine to `IdleState` after dispensing). Use State when the set of allowed operations changes with the object's lifecycle; use Strategy for pluggable algorithms.'''),
 ("How would you implement undo/redo?",
  r'''With the Command pattern. Every user action becomes a `Command` with `execute()` and `undo()`. A manager keeps two stacks: after executing, push onto `undoStack` and clear `redoStack`. On undo, pop from `undoStack`, call `undo()`, push onto `redoStack`. On redo, pop from `redoStack`, call `execute()`, push back to `undoStack`. Commands store enough data (or a memento of previous state) to reverse themselves.'''),
 ("Template Method vs Strategy - when to choose which?",
  r'''Template Method uses **inheritance**: the base class owns the algorithm's skeleton and subclasses fill in steps; it is fixed at compile time. Strategy uses **composition**: the whole algorithm is a pluggable object that can be swapped at runtime and combined freely. Prefer Strategy when variations are independent or must change at runtime; Template Method when steps and their order are invariant and only a few steps differ, and you want to enforce the order with a `final` method.'''),
 ("Give a real-world example of Chain of Responsibility in Java frameworks.",
  r'''The Servlet `FilterChain`: each `Filter.doFilter()` performs its work (authentication, logging, CORS) and calls `chain.doFilter()` to pass the request to the next filter, or stops the chain by not calling it. Spring Security builds a `SecurityFilterChain` of such filters. Benefits: handlers are decoupled, independently testable, and the chain can be reordered or extended without modifying existing handlers.''')],
[RG, {"title": "Refactoring.Guru - Strategy", "url": "https://refactoring.guru/design-patterns/strategy"},
 {"title": "Refactoring.Guru - State", "url": "https://refactoring.guru/design-patterns/state"},
 {"title": "Refactoring.Guru - Chain of Responsibility", "url": "https://refactoring.guru/design-patterns/chain-of-responsibility"}]
))

topics.append(T(
"uml-class-diagrams", "UML Class Diagrams for LLD Interviews", 7, "Basic", 20,
"How to read and quickly draw class diagrams (classes, visibility, relationships, multiplicity) and translate them into Java code during an interview.",
r'''
## Why bother with UML?

In a 45-minute LLD discussion (Atlassian, Uber, Walmart, Amazon), the class diagram **is** the deliverable. In machine coding, a 5-minute sketch prevents rework. You do not need full UML - just classes, key members and correct relationships. Interviewers mostly check whether you pick the **right relationship type and multiplicity**.

## Drawing a class

```text
+-------------------------------+
|          ParkingSlot          |   <- class name (italic or <<abstract>> if abstract)
+-------------------------------+
| - id: String                  |   <- attributes: visibility name: type
| - type: SlotType              |
| - vehicle: Vehicle            |
+-------------------------------+
| + isFree(): boolean           |   <- methods: visibility name(params): return
| + park(v: Vehicle): void      |
| + unpark(): Vehicle           |
+-------------------------------+
```

Visibility symbols: `+` public, `-` private, `#` protected, `~` package-private. Static members are underlined; abstract ones in italics. Interfaces are marked `<<interface>>`, enums `<<enumeration>>`.

## The six relationships (strongest notation first)

| Relationship | Meaning | Arrow | Java shape |
|---|---|---|---|
| **Inheritance (generalization)** | is-a | solid line, hollow triangle `--|>` | `class Car extends Vehicle` |
| **Realization** | implements | dashed line, hollow triangle `..|>` | `class Upi implements Payment` |
| **Composition** | owns; part dies with whole | filled diamond `*--` on whole side | `Building` creates and owns `Room`s |
| **Aggregation** | has-a; part can live alone | hollow diamond `o--` on whole side | `Team` has `Player`s |
| **Association** | uses / knows about, long-lived | solid line `-->` | `Ticket` references `Vehicle` |
| **Dependency** | uses temporarily (param/local) | dashed arrow `..>` | method param `print(Invoice i)` |

### Composition vs aggregation in code

```java
// Composition: House creates its rooms; rooms have no meaning without the house
class House {
    private final List<Room> rooms = new ArrayList<>();
    House(int n) { for (int i = 0; i < n; i++) rooms.add(new Room(i)); }
}

// Aggregation: Department receives existing professors; they outlive the department
class Department {
    private final List<Professor> professors;
    Department(List<Professor> profs) { this.professors = profs; }
}

// Association: a Ticket permanently refers to a Vehicle
class Ticket { private final Vehicle vehicle; Ticket(Vehicle v) { vehicle = v; } }

// Dependency: used only inside a method
class ReportPrinter { void print(Invoice inv) { System.out.println(inv); } }
```

Practical rule: **who creates and destroys it?** If the whole creates it and nothing else holds it -> composition. If it is passed in and shared -> aggregation/association.

## Multiplicity

Written near each end of an association:

| Notation | Meaning |
|---|---|
| `1` | exactly one |
| `0..1` | optional |
| `*` or `0..*` | many |
| `1..*` | at least one |

Example: `ParkingLot 1 *-- 1..* ParkingFloor` reads "a lot owns one or more floors".

## A complete text diagram (how to write it in an interview doc)

Since whiteboard tools vary, a clean text format works everywhere:

```text
<<interface>> PaymentMethod
  + pay(amount: double): boolean
      ^                  ^
      .                  .   (realization)
   UpiPayment         CardPayment

ParkingLot (singleton)
  - floors: List<ParkingFloor>
  - entryGates: List<Gate>
  1 *-- 1..* ParkingFloor            (composition)

ParkingFloor
  - number: int
  - slots: List<ParkingSlot>
  1 *-- 1..* ParkingSlot             (composition)

ParkingSlot
  - id, type: SlotType
  0..1 --> Vehicle                   (association: current vehicle)

<<abstract>> Vehicle  <|-- Car, Bike, Truck   (inheritance)

Ticket
  --> Vehicle, --> ParkingSlot       (association)
  - entryTime: long

ParkingService ..> PricingStrategy   (depends on interface)
```

Some candidates use **PlantUML** or **Mermaid** syntax in a doc; interviewers are fine with any unambiguous notation:

```text
classDiagram
  Vehicle <|-- Car
  ParkingLot "1" *-- "1..*" ParkingFloor
  ParkingFloor "1" *-- "1..*" ParkingSlot
  ParkingSlot "0..1" --> Vehicle
  PaymentMethod <|.. UpiPayment
```

## Other UML diagrams worth knowing (briefly)

- **Sequence diagram**: object lifelines left-to-right and messages top-to-bottom. Useful to explain a flow like "user books a seat": `User -> BookingService: book() -> SeatLockService: lock() -> PaymentService: pay()`.
- **Use case diagram**: actors and their use cases; handy when clarifying requirements.
- **State diagram**: states and transitions; great for vending machine, elevator, order lifecycle - and it maps 1:1 to the State pattern.

## Interview workflow

1. List entities and enums.
2. Draw classes with only the **important** fields/methods (do not list every getter).
3. Draw relationships with multiplicities.
4. Mark interfaces where variation exists (`<<interface>> PricingStrategy`).
5. Walk the interviewer through one use case on the diagram before coding.

Common mistakes: using inheritance for has-a relationships (`ParkingLot extends ParkingFloor`), missing interfaces for pluggable behaviour, drawing 30 classes for a 1-hour problem, and bidirectional associations everywhere (prefer one direction unless navigation is needed both ways).
''',
["Class box: name, attributes (visibility name: type), methods; + public, - private, # protected, ~ package.",
 "Inheritance uses a hollow triangle on a solid line; realization (implements) uses a hollow triangle on a dashed line.",
 "Composition (filled diamond) means the whole owns and creates the part; the part dies with the whole.",
 "Aggregation (hollow diamond) is has-a where the part exists independently and may be shared.",
 "Association is a long-lived reference; dependency is temporary use via a parameter or local variable.",
 "Always mark multiplicities (1, 0..1, *, 1..*) and interfaces where behaviour varies.",
 "A text or Mermaid diagram with correct relationships is acceptable and fast in interviews."],
[("What is the difference between aggregation and composition?",
  r'''Both are whole-part "has-a" relationships. In **composition** the whole owns the part's lifecycle: it creates the part, the part is not shared, and it is destroyed with the whole (an `Order` and its `OrderLineItem`s). In **aggregation** the part has an independent lifecycle and can be shared or outlive the whole (a `Team` and its `Player`s). In Java, composition typically means the parts are created inside the whole's constructor; aggregation means they are passed in from outside.'''),
 ("How do you show that a class implements an interface in UML?",
  r'''With a **realization** relationship: a dashed line from the implementing class to the interface ending in a hollow triangle at the interface. The interface box is labeled with the `<<interface>>` stereotype. In Mermaid that is `PaymentMethod <|.. UpiPayment`. Inheritance between classes uses the same triangle but a solid line (`Vehicle <|-- Car`).'''),
 ("How much detail should a class diagram have in an LLD interview?",
  r'''Enough to show the design decisions, not every getter. Include core entities, enums, interfaces for pluggable behaviour, key fields that define relationships, and the main methods that implement use cases. Show relationship types and multiplicities correctly. Skip boilerplate like constructors and getters. Typically 8-15 classes for a 45-60 minute problem. Then walk through one use case on the diagram to prove it supports the requirements.'''),
 ("When would you draw a sequence diagram instead of a class diagram?",
  r'''A class diagram shows static structure; a sequence diagram shows **runtime interaction order**. I use a sequence diagram when the interesting part is the flow, e.g., booking a seat (lock seats, create pending booking, call payment, confirm or release on timeout) or an ATM withdrawal, to clarify which object calls which and where failures and timeouts are handled. In interviews, a quick sequence sketch for the most complex use case complements the class diagram.''')],
[{"title": "Visual Paradigm - UML Class Diagram Tutorial", "url": "https://www.visual-paradigm.com/guide/uml-unified-modeling-language/uml-class-diagram-tutorial/"},
 {"title": "Mermaid - Class Diagram Syntax", "url": "https://mermaid.js.org/syntax/classDiagram.html"}, ALLD]
))

topics.append(T(
"concurrency-for-lld", "Concurrency for LLD: Making Designs Thread-Safe", 8, "Advanced", 35,
"The Java concurrency toolkit you need to make LLD solutions thread-safe: synchronized, locks, atomics, ConcurrentHashMap, executors, CompletableFuture and producer-consumer.",
r'''
## Why concurrency shows up in LLD

Follow-up questions like *"two users book the same seat at the same moment"*, *"many cars enter from multiple gates"*, or *"make your rate limiter thread-safe"* are standard at Flipkart, PhonePe, Uber and Atlassian. You need to (1) spot **shared mutable state**, (2) protect **check-then-act** sequences, and (3) choose the right tool.

## The core problem: race conditions

```java
class Counter {
    private int count = 0;
    void increment() { count++; }   // read-modify-write: NOT atomic
}
```
Two threads can read 5 at the same time and both write 6. The classic LLD equivalent is **check-then-act**:

```java
if (seat.isAvailable()) {   // thread A and B both see true
    seat.book(user);        // both book -> double booking
}
```

## Tool 1: `synchronized`

Every object has an intrinsic lock (monitor). `synchronized` provides **mutual exclusion and visibility** (changes made inside are visible to the next thread acquiring the same lock).

```java
class Seat {
    private String bookedBy;
    public synchronized boolean tryBook(String user) {
        if (bookedBy != null) return false;
        bookedBy = user;
        return true;
    }
}
```
Lock granularity matters: locking the whole `Theatre` serialises all bookings; locking per `Seat` (or per show) allows parallelism. Prefer the smallest scope that protects the invariant.

## Tool 2: `volatile`

Guarantees visibility and ordering for a single variable, **not atomicity**. Good for flags (`volatile boolean running`) and the double-checked-locking singleton. Not enough for `count++`.

## Tool 3: Atomic classes

Lock-free compare-and-swap (CAS) operations:

```java
AtomicInteger available = new AtomicInteger(10);
boolean tryAcquire() {
    while (true) {
        int cur = available.get();
        if (cur == 0) return false;
        if (available.compareAndSet(cur, cur - 1)) return true;
    }
}
AtomicLong idGen = new AtomicLong();
long nextId = idGen.incrementAndGet();
```
Use for counters, ID generators, simple state flags. `LongAdder` is faster for very high-contention counters.

## Tool 4: `ReentrantLock` and `ReadWriteLock`

Explicit locks give features `synchronized` lacks: `tryLock(timeout)`, fairness, interruptible waits, multiple `Condition`s.

```java
class BankAccount {
    private final ReentrantLock lock = new ReentrantLock();
    private double balance;

    boolean withdraw(double amt) throws InterruptedException {
        if (lock.tryLock(1, TimeUnit.SECONDS)) {
            try {
                if (balance < amt) return false;
                balance -= amt;
                return true;
            } finally {
                lock.unlock();          // ALWAYS in finally
            }
        }
        return false;                   // could not get lock in time
    }
}
```

`ReentrantReadWriteLock` allows many concurrent readers but one writer - ideal for read-heavy caches or a config store.

**Deadlock avoidance** (e.g., transfer between two accounts): always acquire locks in a **consistent global order** (by account id), use `tryLock` with timeout, and keep critical sections small.

```java
void transfer(Account a, Account b, double amt) {
    Account first = a.id() < b.id() ? a : b;
    Account second = first == a ? b : a;
    synchronized (first) {
        synchronized (second) {
            a.debit(amt); b.credit(amt);
        }
    }
}
```

## Tool 5: Concurrent collections

| Collection | Use |
|---|---|
| `ConcurrentHashMap` | Thread-safe map; bucket-level locking/CAS; atomic `putIfAbsent`, `computeIfAbsent`, `compute`, `merge` |
| `CopyOnWriteArrayList` | Read-mostly lists like observer/subscriber lists |
| `ConcurrentLinkedQueue` | Non-blocking queue |
| `BlockingQueue` (`ArrayBlockingQueue`, `LinkedBlockingQueue`) | Producer-consumer with blocking `put`/`take` |
| `ConcurrentSkipListMap` | Sorted concurrent map |

Key trick: replace check-then-act on a map with **one atomic method**:

```java
ConcurrentHashMap<String, String> seatOwner = new ConcurrentHashMap<>();
boolean book(String seatId, String user) {
    return seatOwner.putIfAbsent(seatId, user) == null;   // atomic
}

ConcurrentHashMap<String, AtomicInteger> hits = new ConcurrentHashMap<>();
hits.computeIfAbsent(userId, k -> new AtomicInteger()).incrementAndGet();
wordCount.merge(word, 1, Integer::sum);
```
Note: `if (!map.containsKey(k)) map.put(k, v);` on a `ConcurrentHashMap` is **still a race** - the individual calls are safe, the combination is not.

## Tool 6: ExecutorService

Never create raw threads per task in production; use a pool.

```java
ExecutorService pool = Executors.newFixedThreadPool(4);
List<Future<Integer>> futures = new ArrayList<>();
for (int i = 0; i < 10; i++) {
    final int n = i;
    futures.add(pool.submit(() -> n * n));     // Callable
}
for (Future<Integer> f : futures) System.out.println(f.get());
pool.shutdown();
pool.awaitTermination(5, TimeUnit.SECONDS);
```
Also: `ScheduledExecutorService` for periodic jobs (expiring seat locks, TTL cleanup in a KV store, refilling token buckets). `CountDownLatch` to wait for N tasks; `Semaphore` to cap concurrent access (e.g., N parking spots, N DB connections).

## Tool 7: CompletableFuture

Composable async pipelines - handy for "fetch price, availability and offers in parallel".

```java
ExecutorService io = Executors.newFixedThreadPool(3);
CompletableFuture<Double> price = CompletableFuture.supplyAsync(() -> 499.0, io);
CompletableFuture<Integer> stock = CompletableFuture.supplyAsync(() -> 12, io);

String result = price.thenCombine(stock, (p, s) -> "price=" + p + ", stock=" + s)
        .exceptionally(ex -> "fallback")
        .join();

CompletableFuture.allOf(price, stock).join();   // wait for all
```
Methods to know: `supplyAsync`, `thenApply` (map), `thenCompose` (flatMap for dependent async calls), `thenCombine` (join two), `allOf`/`anyOf`, `exceptionally`/`handle`, `orTimeout` (Java 9+).

## Producer-consumer with BlockingQueue

The backbone of message queues, logger async appenders and order processing:

```java
BlockingQueue<String> queue = new ArrayBlockingQueue<>(5);

Thread producer = new Thread(() -> {
    try {
        for (int i = 1; i <= 10; i++) { queue.put("order-" + i); }   // blocks when full
        queue.put("POISON");                                            // stop signal
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});

Thread consumer = new Thread(() -> {
    try {
        while (true) {
            String msg = queue.take();                                  // blocks when empty
            if (msg.equals("POISON")) break;
            System.out.println("processed " + msg);
        }
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});
producer.start(); consumer.start();
```
Interviewers sometimes ask for the `wait()/notifyAll()` version: guard with `while (queue.isEmpty()) wait();` (a `while`, never `if`, because of spurious wake-ups), and call `notifyAll()` after changing state, all inside `synchronized`.

## Thread-safe design checklist for LLD answers

1. **Identify shared mutable state** (seat status, slot occupancy, balances, counters, caches).
2. **Prefer immutability** for value objects (`Ticket`, `Money`), so they need no locks.
3. **Use concurrent collections and atomic map operations** for registries.
4. **Lock at the right granularity**: per seat/slot/account rather than global.
5. **Make check-then-act atomic** (synchronized block, `putIfAbsent`, `compareAndSet`).
6. **Avoid deadlocks** with lock ordering and `tryLock` timeouts.
7. **Use executors** for background work (expiry, retries, async notifications).
8. **Optimistic locking** (version numbers) is the database-level equivalent - mention it for distributed setups, along with distributed locks (Redis) when multiple servers are involved.
''',
["Look for shared mutable state and check-then-act sequences; they cause double booking and lost updates.",
 "synchronized gives mutual exclusion and visibility; volatile gives only visibility, not atomicity.",
 "Atomic classes use CAS for lock-free counters and ID generators; LongAdder for heavy contention.",
 "ReentrantLock adds tryLock with timeout, fairness and conditions; always unlock in finally.",
 "ConcurrentHashMap individual calls are thread-safe but combinations are not; use putIfAbsent/compute/merge.",
 "Use ExecutorService/ScheduledExecutorService instead of raw threads; CompletableFuture for async composition.",
 "BlockingQueue implements producer-consumer cleanly; with wait/notify always wait inside a while loop.",
 "Avoid deadlocks via consistent lock ordering and keep lock granularity as small as the invariant allows."],
[("How would you prevent two users from booking the same seat simultaneously?",
  r'''Make the check-and-book step atomic. In a single JVM: keep seat status in a `ConcurrentHashMap<seatId, bookingId>` and use `putIfAbsent`, which returns non-null if someone else already holds it; or synchronize per show/seat. For multi-seat bookings, lock seats in sorted order to avoid deadlocks and roll back on partial failure. Add a temporary lock with expiry (via a scheduled executor) while payment happens. In a distributed setup, use a DB unique constraint, optimistic locking with a version column, or a Redis lock with TTL.'''),
 ("What is the difference between synchronized and ReentrantLock?",
  r'''Both are reentrant mutual-exclusion locks with the same memory-visibility guarantees. `synchronized` is simpler: block-structured and released automatically, even on exceptions. `ReentrantLock` is explicit: you must call `unlock()` in `finally`, but you gain `tryLock()` (with timeout), `lockInterruptibly()`, an optional fairness policy, and multiple `Condition` objects. Use `synchronized` by default and `ReentrantLock` when you need timeouts, interruptibility or several wait conditions.'''),
 ("Why is HashMap not thread-safe and how does ConcurrentHashMap solve it?",
  r'''Concurrent `put`s on `HashMap` can lose updates or corrupt internal structure during resize, and readers may see stale data. `Collections.synchronizedMap` fixes this with one global lock, which kills concurrency. `ConcurrentHashMap` (Java 8+) uses CAS for empty buckets and synchronizes on individual bucket heads otherwise, so different buckets update in parallel and reads are mostly lock-free. It also provides atomic compound operations like `putIfAbsent`, `computeIfAbsent` and `merge`. It does not allow null keys or values.'''),
 ("Explain the producer-consumer problem and how you'd implement it in Java.",
  r'''Producers create work items and consumers process them via a bounded buffer; producers must wait when it is full and consumers when it is empty. The cleanest Java implementation is a `BlockingQueue` such as `ArrayBlockingQueue`: `put()` blocks when full, `take()` blocks when empty, and all synchronization is internal. Shutdown is handled with a poison-pill message or by interrupting consumers. A manual version uses `synchronized`, `wait()` inside a `while` loop and `notifyAll()`.'''),
 ("What is a deadlock and how do you avoid it?",
  r'''A deadlock occurs when threads wait forever for each other's locks, e.g., T1 holds lock A and wants B while T2 holds B and wants A. It requires mutual exclusion, hold-and-wait, no preemption and circular wait. Break circular wait by acquiring locks in a **consistent global order** (e.g., by account id in a money transfer). Other strategies: `tryLock` with timeout and retry, holding fewer locks, and keeping critical sections short. Thread dumps (`jstack`) reveal deadlocks in practice.''')],
[JDOC, {"title": "Oracle Java Tutorials - Concurrency", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/index.html"},
 {"title": "Baeldung - Guide to java.util.concurrent", "url": "https://www.baeldung.com/java-util-concurrent"}]
))

save("f2", "fundamentals", topics)
