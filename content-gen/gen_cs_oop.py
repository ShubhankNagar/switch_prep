from cs_common import build, B, I, A

notes = [
("The Four Pillars of OOP", r"""
Object-Oriented Programming organises software around **objects** — bundles of state (fields) and behaviour (methods) — modelled after real-world or domain concepts. A **class** is the blueprint; an **object** is an instance.

### 1. Encapsulation
Bundling data with the methods that operate on it and **restricting direct access** to internal state. Expose behaviour, not data.
```java
public class BankAccount {
    private BigDecimal balance = BigDecimal.ZERO;   // hidden state

    public void deposit(BigDecimal amt) {
        if (amt.signum() <= 0) throw new IllegalArgumentException("Amount must be positive");
        balance = balance.add(amt);
    }
    public BigDecimal getBalance() { return balance; }   // no setter: invariants protected
}
```
Benefits: invariants enforced in one place, internal representation can change without breaking callers, easier debugging. Note: getters/setters for every field is *not* real encapsulation ("anemic" objects) — prefer meaningful methods like `deposit()`.

### 2. Abstraction
Exposing **what** an object does while hiding **how**. Achieved with **interfaces** and **abstract classes**.
```java
public interface PaymentGateway { PaymentResult charge(Order order); }
class RazorpayGateway implements PaymentGateway { ... }
class StripeGateway implements PaymentGateway { ... }
```
The checkout service depends only on `PaymentGateway`; it doesn't care about HTTP calls, signatures or retries.

*Encapsulation vs abstraction:* encapsulation is about **hiding data/implementation details inside a class** (access modifiers); abstraction is about **designing a simplified interface** that hides complexity (interfaces, abstract types). Encapsulation is a means; abstraction is a design view.

### 3. Inheritance
A class (subclass) acquires fields and methods of another (superclass) — an **is-a** relationship — enabling reuse and polymorphism.
```java
abstract class Notification {
    abstract void send(String to, String msg);
    void sendAll(List<String> to, String msg) { to.forEach(t -> send(t, msg)); }
}
class SmsNotification extends Notification { void send(String to, String msg) { /* SMS API */ } }
```
Types: single, multilevel, hierarchical; **multiple inheritance of classes is not allowed in Java** (diamond problem) but a class can implement multiple interfaces (default-method conflicts must be resolved explicitly). Use inheritance carefully — see "composition over inheritance".

### 4. Polymorphism
"Many forms": the same call behaves differently depending on the object.
- **Compile-time (static) polymorphism** – **method overloading**: same name, different parameter lists; resolved by the compiler.
```java
int add(int a, int b); double add(double a, double b); int add(int a, int b, int c);
```
- **Runtime (dynamic) polymorphism** – **method overriding**: subclass provides its own implementation; the JVM picks the method based on the **actual object type** at runtime (dynamic dispatch via vtable).
```java
Notification n = new SmsNotification();
n.send("98xxxx", "Order shipped");   // SmsNotification.send runs
```

### Overloading vs overriding
| Overloading | Overriding |
|---|---|
| Same class (or subclass), same name, **different parameters** | Subclass, **same signature** |
| Compile time | Runtime |
| Return type can differ | Same or covariant return type |
| Any access modifier | Can't reduce visibility |
| static methods can be overloaded | static methods are **hidden**, not overridden |

### Other OOP terms to know
- **Association** (uses-a), **aggregation** (has-a, independent lifecycle: Department has Employees), **composition** (strong has-a, dependent lifecycle: Order has OrderItems; delete the order, items go too).
- **Cohesion** (how focused a class is — want high) and **coupling** (how dependent classes are on each other — want low).
- **Constructor**, `this`, `super`, static vs instance members, `final` classes/methods, immutability (`String`, records).
- **Abstract class vs interface** — covered in Q&A; since Java 8 interfaces can have default/static methods and since Java 9 private methods.
"""),

("SOLID Principles", r"""
SOLID (Robert C. Martin) is a set of five design principles for maintainable, extensible OO code. Interviewers expect a definition **plus** a violation **plus** the fix — ideally from your own project.

### S — Single Responsibility Principle
*A class should have only one reason to change* (one actor/responsibility).

❌ Violation:
```java
class InvoiceService {
    Invoice calculate(Order o) { ... }
    void saveToDb(Invoice i) { ... }
    byte[] generatePdf(Invoice i) { ... }
    void email(Invoice i) { ... }
}
```
Changes to PDF layout, DB schema or email provider all touch this class.
✅ Split into `InvoiceCalculator`, `InvoiceRepository`, `InvoicePdfGenerator`, `InvoiceMailer`, orchestrated by a thin service.

### O — Open/Closed Principle
*Software entities should be open for extension, closed for modification.* Add new behaviour by adding code, not editing working code.

❌
```java
double discount(Customer c) {
    if (c.type() == GOLD) return 0.2;
    else if (c.type() == SILVER) return 0.1;
    // new tier = edit this method
}
```
✅
```java
interface DiscountPolicy { boolean supports(CustomerType t); double rate(); }
@Component class GoldDiscount implements DiscountPolicy { ... }
// Spring injects List<DiscountPolicy>; a new tier = a new class
```
This is the **Strategy pattern** — the usual way to achieve OCP.

### L — Liskov Substitution Principle
*Objects of a subclass must be usable wherever the superclass is expected without breaking correctness.* Subclasses must honour the parent's contract: not strengthen preconditions, not weaken postconditions, not throw unexpected exceptions.

❌ Classic: `Square extends Rectangle` — setting width on a square also changes height, breaking code that assumes `setWidth` leaves height unchanged. Another: `ReadOnlyList extends ArrayList` throwing `UnsupportedOperationException` from `add()` (Java's `Collections.unmodifiableList` is a real-world LSP compromise).
✅ Model them as separate types implementing a common `Shape` interface with `area()`.

### I — Interface Segregation Principle
*Clients shouldn't be forced to depend on methods they don't use.* Prefer several small, role-specific interfaces over one fat interface.

❌
```java
interface Worker { void work(); void eat(); void attendMeeting(); }
class RobotWorker implements Worker { public void eat() { throw new UnsupportedOperationException(); } }
```
✅ `Workable`, `Feedable`, `MeetingAttendee` interfaces. Spring Data's `CrudRepository`, `PagingAndSortingRepository`, `ListCrudRepository` are segregated this way.

### D — Dependency Inversion Principle
*High-level modules shouldn't depend on low-level modules; both should depend on abstractions. Abstractions shouldn't depend on details.*

❌
```java
class OrderService { private MySqlOrderRepository repo = new MySqlOrderRepository(); }
```
✅
```java
class OrderService {
    private final OrderRepository repo;           // abstraction
    OrderService(OrderRepository repo) { this.repo = repo; }   // injected
}
```
**DIP is a principle; Dependency Injection is a technique to achieve it; IoC containers (Spring) automate DI.** This enables swapping implementations and mocking in unit tests (Mockito).

### How to answer "Have you applied SOLID?"
Give one concrete story: "Our notification module had a giant `if (channel == SMS) ... else if (EMAIL)` block. I refactored it to a `NotificationSender` interface with SMS, Email and WhatsApp implementations registered as Spring beans in a map keyed by channel. Adding WhatsApp later was a new class plus config — no change to existing code (OCP), each sender has one job (SRP), and the service depends on the interface (DIP)."

### Caveat
Principles are guidelines, not laws. Over-applying them creates needless indirection (an interface for every class with one implementation). Balance with KISS and YAGNI.
"""),

("DRY, KISS, YAGNI, Coupling/Cohesion & Other Principles", r"""
### DRY — Don't Repeat Yourself
*Every piece of knowledge should have a single, authoritative representation.* Duplication of **knowledge** (business rules, validation logic, constants) means bugs get fixed in one place but not another.
- ✅ Extract the GST calculation into one `TaxCalculator`, share validation via a common DTO validator, keep constants in one place.
- ⚠ Don't over-DRY: two pieces of code that *look* similar but change for different reasons should stay separate. Premature abstraction creates coupling ("**WET** – write everything twice – is better than the wrong abstraction"; the "rule of three": abstract on the third occurrence).

### KISS — Keep It Simple, Stupid
Prefer the simplest solution that works. Readable code beats clever code.
```java
// clever
return list.stream().collect(Collectors.reducing(0, e -> e.getAmt(), Integer::sum));
// simple
return list.stream().mapToInt(Item::getAmt).sum();
```
Simple designs are easier to test, debug and onboard. Avoid microservices, Kafka or NgRx where a module, a method call or a service with a signal is enough.

### YAGNI — You Aren't Gonna Need It
Don't build features or abstractions for **hypothetical** future needs. Build for today's requirements; design so change is easy, but don't implement the change in advance. Speculative generality (plugin frameworks for one plugin, config flags no one uses) adds maintenance cost.

### Coupling & cohesion
- **Cohesion** – how strongly related the responsibilities inside a module are. **High cohesion** is good (an `OrderPricing` class only deals with pricing).
- **Coupling** – how much a module depends on others' internals. **Low (loose) coupling** is good — depend on interfaces, communicate via well-defined contracts/events.
Goal: **high cohesion, low coupling.** Microservices aim for this at the system level ("bounded contexts").

### Law of Demeter (principle of least knowledge)
A method should only talk to its immediate friends — avoid "train wrecks":
```java
order.getCustomer().getAddress().getCity().getPincode();   // ❌ knows the whole object graph
order.shippingPincode();                                    // ✅ ask, don't dig
```
Related: **Tell, Don't Ask** — tell objects what to do rather than querying their state and deciding for them.

### Separation of Concerns
Split a program into distinct sections each addressing one concern: controller (HTTP), service (business logic), repository (persistence); in Angular: components (UI), services (data/logic), interceptors (cross-cutting).

### Program to an interface, not an implementation
`List<String> names = new ArrayList<>();` — callers depend on `List`, so switching to `LinkedList` is trivial.

### Favour immutability
Immutable objects (`final` fields, no setters, Java `record`s) are thread-safe, easy to reason about, and safe as map keys.
```java
public record Money(BigDecimal amount, String currency) {}
```

### Fail fast
Validate inputs early and throw meaningful exceptions (`Objects.requireNonNull`, Bean Validation `@Valid`), rather than propagating bad state.

### Principle of Least Astonishment
APIs should behave as users expect — a method `getUser()` shouldn't create a user.

### GRASP (brief)
Information Expert (assign responsibility to the class with the data), Creator, Controller, Low Coupling, High Cohesion, Polymorphism, Pure Fabrication, Indirection, Protected Variations — another vocabulary for the same goals.

### Code smells to recognise
Long method, large class (God object), long parameter list, duplicated code, feature envy (a method using another class's data more than its own), switch statements on type, primitive obsession (using `String` for email/phone instead of value objects), shotgun surgery (one change touches many classes). Mentioning refactorings you applied (Extract Method, Replace Conditional with Polymorphism, Introduce Parameter Object) signals maturity.
"""),

("Composition vs Inheritance", r"""
Both let you reuse code, but they create very different relationships.

- **Inheritance** – **is-a**. `Car extends Vehicle`. The subclass gets the parent's implementation at compile time.
- **Composition** – **has-a**. `Car` has an `Engine` field and delegates to it. Behaviour is assembled from parts at runtime.

### Problems with inheritance
1. **Tight coupling / fragile base class** – changes in the parent can silently break subclasses. Subclasses depend on the parent's implementation details, breaking encapsulation.
2. **Rigid hierarchy** – behaviour is fixed at compile time; Java allows only single class inheritance.
3. **Class explosion** – combining features via subclasses multiplies classes: `SmsUrgentNotification`, `EmailUrgentNotification`, `SmsScheduledNotification`…
4. **Inherits everything**, including methods that don't make sense (Java's `Stack extends Vector` exposes `insertElementAt`, letting you break stack semantics).

Classic example (Effective Java): `InstrumentedHashSet extends HashSet` overrides `add` and `addAll` to count insertions — but `HashSet.addAll` internally calls `add`, so elements are counted twice. The subclass depended on an undocumented implementation detail.

### Composition solves it
```java
class InstrumentedSet<E> implements Set<E> {     // wrapper / decorator
    private final Set<E> inner;
    private int addCount = 0;
    InstrumentedSet(Set<E> inner) { this.inner = inner; }
    public boolean add(E e) { addCount++; return inner.add(e); }
    public boolean addAll(Collection<? extends E> c) { addCount += c.size(); return inner.addAll(c); }
    // other methods delegate to inner
}
```
Works with any `Set` implementation, and is immune to `HashSet` internals.

### Strategy via composition
```java
class NotificationService {
    private final MessageSender sender;          // SMS, Email, WhatsApp
    private final RetryPolicy retryPolicy;       // fixed, exponential
    NotificationService(MessageSender s, RetryPolicy r) { sender = s; retryPolicy = r; }
}
```
Any sender × any retry policy without creating subclasses for each combination; swap at runtime or in tests.

### Comparison
| Inheritance | Composition |
|---|---|
| is-a | has-a |
| Static, compile-time | Dynamic, can change at runtime |
| White-box reuse (sees internals) | Black-box reuse (via interface) |
| Tighter coupling | Looser coupling |
| Less code initially | A bit more delegation code |
| Natural for true taxonomies & frameworks (template method) | Default choice for behaviour reuse |

### When inheritance is right
- A genuine, stable **is-a** relationship that satisfies **Liskov substitution** (`ArrayList` is a `List` — via interface inheritance).
- Framework extension points designed for it (`extends OncePerRequestFilter`, `extends RuntimeException` for custom exceptions, abstract template classes).
- Shared state + behaviour among closely related types inside your own module, with a small hierarchy (≤ 2 levels).

Rule of thumb: **"Favour composition over inheritance"** (GoF). Inherit **interfaces** freely; inherit **implementations** sparingly. In Java, `sealed` interfaces + records give you closed hierarchies without implementation inheritance.

### Angular/Spring parallel
Spring beans are composed via DI rather than inherited; Angular discourages component inheritance and offers composition via services, directives (`hostDirectives`) and content projection — both frameworks are built around composition.
"""),

("Design Patterns: Creational", r"""
Design patterns are proven, reusable solutions to common design problems (Gang of Four catalogued 23, grouped as **creational, structural, behavioural**). Interviewers at product companies typically ask: Singleton (with thread safety), Factory, Builder, Strategy, Observer, Decorator, Adapter — and "where does Spring use them?"

### Singleton
Ensure **one instance** of a class with a global access point (config, cache manager, connection pool).
```java
// Thread-safe lazy singleton: double-checked locking
public final class ConfigManager {
    private static volatile ConfigManager instance;   // volatile prevents reordering
    private ConfigManager() {}
    public static ConfigManager getInstance() {
        if (instance == null) {
            synchronized (ConfigManager.class) {
                if (instance == null) instance = new ConfigManager();
            }
        }
        return instance;
    }
}
// Simplest & safest: enum singleton (serialization- and reflection-safe)
public enum IdGenerator { INSTANCE; private final AtomicLong seq = new AtomicLong(); public long next() { return seq.incrementAndGet(); } }
// Also good: Bill Pugh holder idiom
public class Registry { private Registry() {} private static class Holder { static final Registry I = new Registry(); } public static Registry get() { return Holder.I; } }
```
Breaking singletons: reflection (guard in constructor), serialization (`readResolve`), cloning, multiple class loaders. Downsides: global state, hard to test. In Spring, beans are **singleton-scoped by default per container** — prefer that over hand-written singletons.

### Factory Method / Simple Factory
Delegate object creation to a method/class so clients depend on an interface, not concrete classes.
```java
public class PaymentProcessorFactory {
    private final Map<PaymentMode, PaymentProcessor> processors;
    public PaymentProcessorFactory(List<PaymentProcessor> list) {   // Spring injects all beans
        processors = list.stream().collect(Collectors.toMap(PaymentProcessor::mode, p -> p));
    }
    public PaymentProcessor get(PaymentMode mode) {
        return Optional.ofNullable(processors.get(mode)).orElseThrow(() -> new IllegalArgumentException("Unsupported " + mode));
    }
}
```
JDK examples: `Calendar.getInstance()`, `List.of()`, `NumberFormat.getInstance()`. Spring: `BeanFactory`, `FactoryBean`.

### Abstract Factory
A factory of **families of related objects** (e.g. `UIFactory` producing `Button` + `Checkbox` for Light vs Dark themes; `DocumentBuilderFactory`).

### Builder
Construct complex objects step by step, avoiding telescoping constructors and enabling immutability.
```java
public final class HttpRequestSpec {
    private final String url; private final String method; private final Map<String,String> headers; private final Duration timeout;
    private HttpRequestSpec(Builder b) { url = b.url; method = b.method; headers = Map.copyOf(b.headers); timeout = b.timeout; }
    public static Builder builder(String url) { return new Builder(url); }
    public static class Builder {
        private final String url; private String method = "GET"; private final Map<String,String> headers = new HashMap<>(); private Duration timeout = Duration.ofSeconds(5);
        private Builder(String url) { this.url = url; }
        public Builder method(String m) { method = m; return this; }
        public Builder header(String k, String v) { headers.put(k, v); return this; }
        public Builder timeout(Duration t) { timeout = t; return this; }
        public HttpRequestSpec build() { return new HttpRequestSpec(this); }
    }
}
```
Examples: `StringBuilder`, `HttpClient.newBuilder()`, Lombok `@Builder`, Spring's `ResponseEntity.ok().header(...).body(...)`, `UriComponentsBuilder`.

### Prototype
Create new objects by **cloning** an existing instance (costly-to-create objects, templates). Java `Cloneable` is awkward; prefer copy constructors. Spring has **prototype scope** (new bean per injection/request from container).

### Object Pool (bonus)
Reuse expensive objects: DB connection pools (HikariCP), thread pools (`ExecutorService`).
"""),

("Design Patterns: Structural & Behavioural", r"""
### Structural patterns (how objects are composed)
**Adapter** – converts one interface into another that clients expect (a plug adapter). Wrap a legacy SOAP client or a third-party SDK behind your own interface.
```java
class LegacySmsAdapter implements SmsSender {
    private final OldTelcoClient client;
    public void send(String to, String msg) { client.dispatchMessage(new TelcoMsg(to, msg, "IN")); }
}
```
JDK: `Arrays.asList`, `InputStreamReader` (bytes → chars). Spring MVC: `HandlerAdapter`.

**Decorator** – adds responsibilities to an object **dynamically** by wrapping it, without subclassing.
```java
DataSource ds = new EncryptionDecorator(new CompressionDecorator(new FileDataSource("x.dat")));
```
JDK: `new BufferedReader(new InputStreamReader(new FileInputStream(f)))`, `Collections.synchronizedList`. Angular HTTP interceptors behave like a chain of decorators.

**Proxy** – a surrogate controlling access to another object: lazy loading, access control, caching, remote calls, logging. **Spring AOP** creates proxies (JDK dynamic proxies or CGLIB) to implement `@Transactional`, `@Cacheable`, `@Async` — which is why **self-invocation** inside the same class bypasses them. Hibernate lazy-loaded entities are proxies too.

**Facade** – a simplified interface over a complex subsystem. `CheckoutFacade.placeOrder()` hiding inventory, pricing, payment and notification services; `JdbcTemplate` is a facade over raw JDBC.

**Composite** – treat individual objects and groups uniformly via a tree (file/folder, menu/submenu, org charts, Angular component tree).

**Bridge**, **Flyweight** (share intrinsic state: `Integer.valueOf` cache −128..127, String pool) — know the one-line definitions.

### Behavioural patterns (how objects interact)
**Strategy** – define a family of interchangeable algorithms behind an interface and pick one at runtime. Kills `if/else` chains; enables OCP.
```java
interface ShippingCostStrategy { BigDecimal cost(Order o); }
class StandardShipping implements ShippingCostStrategy { ... }
class ExpressShipping implements ShippingCostStrategy { ... }
```
JDK: `Comparator` passed to `sort`. Spring: `PasswordEncoder` implementations, `ResourceLoader`.

**Observer (Publish–Subscribe)** – subjects notify registered observers on state change; loose coupling between producer and consumers.
```java
@Component class OrderService {
    private final ApplicationEventPublisher events;
    void place(Order o) { ...; events.publishEvent(new OrderPlacedEvent(o.getId())); }
}
@Component class EmailListener { @EventListener void on(OrderPlacedEvent e) { /* send mail */ } }
```
Also: RxJS Observables, Angular `EventEmitter`, Kafka at the system level.

**Template Method** – base class defines the algorithm skeleton, subclasses fill specific steps. Spring's `JdbcTemplate`, `RestTemplate` callbacks, `AbstractController`, JUnit lifecycle.

**Chain of Responsibility** – pass a request along a chain of handlers until one handles it. **Servlet filters / Spring Security filter chain**, Angular HTTP interceptors, approval workflows (manager → director → CFO by amount).

**Command** – encapsulate a request as an object (undo/redo, job queues, `Runnable` submitted to an executor).

**State** – an object changes behaviour when its internal state changes (Order: CREATED → PAID → SHIPPED → DELIVERED, each state class allowing valid transitions only; vending machine — a common LLD question).

**Iterator** – sequential access without exposing the representation (`Iterator`, `for-each`).

**Mediator** – centralise communication between components (chat room; air-traffic control).

### Patterns inside Spring (frequently asked)
| Pattern | Where in Spring |
|---|---|
| Singleton | Default bean scope |
| Factory | `BeanFactory`, `ApplicationContext`, `FactoryBean` |
| Proxy | AOP: `@Transactional`, `@Cacheable`, `@Async` |
| Template Method | `JdbcTemplate`, `RestTemplate`, `TransactionTemplate` |
| Observer | `ApplicationEvent` / `@EventListener` |
| Front Controller | `DispatcherServlet` |
| Strategy | `HandlerMapping`, `PasswordEncoder`, `Resource` impls |
| Chain of Responsibility | Security filter chain |
| Adapter | `HandlerAdapter` |
| Dependency Injection / IoC | The container itself |

### Anti-patterns to name
God object, singleton abuse (hidden global state), spaghetti code, golden hammer (using one tool for everything), premature optimisation, copy-paste programming, anemic domain model (debatable).
"""),
]

qa = [
("What are the four pillars of OOP? Explain each with an example.", r"""
1. **Encapsulation** – bundling state and behaviour and hiding internal details behind methods. `BankAccount` keeps `balance` private and exposes `deposit()`/`withdraw()` that enforce rules (no negative deposits).
2. **Abstraction** – exposing only essential behaviour via interfaces/abstract classes. `PaymentGateway.charge(order)` hides whether Razorpay or Stripe is used and how HTTP calls are made.
3. **Inheritance** – a class acquires properties/behaviour of a parent (is-a). `SavingsAccount extends Account` reuses common logic and adds interest calculation.
4. **Polymorphism** – one interface, many implementations. Compile-time via **overloading** (`add(int,int)` / `add(double,double)`), runtime via **overriding** (`Notification n = new SmsNotification(); n.send()` calls the SMS version).

Together they produce modular, reusable, maintainable code. Tie your answer to a project class you designed.
""", B, ["oop", "pillars"], True),

("What is the difference between abstraction and encapsulation?", r"""
| Abstraction | Encapsulation |
|---|---|
| Hides **complexity**; shows only **what** an object does | Hides **data/implementation**; controls **how** state is accessed |
| Design-level concept | Implementation-level concept |
| Achieved via **interfaces and abstract classes** | Achieved via **access modifiers** (`private`, getters/methods) |
| Focus: the outside view/contract | Focus: protecting internal state and invariants |

Example: a `Car` exposes `start()`, `accelerate()` — abstraction (you don't know about fuel injection). Inside, `engineTemperature` is `private` and only changed through methods — encapsulation.

They complement each other: encapsulation is one of the mechanisms that makes abstraction possible.
""", B, ["oop", "abstraction", "encapsulation"], True),

("What is the difference between an abstract class and an interface in Java?", r"""
| Abstract class | Interface |
|---|---|
| `extends` – only **one** | `implements` – **many** |
| Can have constructors and **instance fields (state)** | No instance state; only `public static final` constants |
| Abstract + concrete methods, any access modifier | Abstract, `default`, `static` and (Java 9+) `private` methods |
| Models **is-a** with shared code among closely related classes | Models a **capability/contract** (`Comparable`, `Runnable`) usable by unrelated classes |

When to use:
- **Interface** – define a contract for multiple implementations, enable loose coupling and DI (`PaymentGateway`), or add a role to unrelated classes.
- **Abstract class** – share state and partial implementation among related subclasses (template method: `AbstractReportGenerator` with `generate()` calling abstract `fetchData()`).

Since Java 8 the gap narrowed, but interfaces still can't hold mutable instance state. Java 17 adds `sealed` to restrict implementers.
""", B, ["oop", "java", "interface"], True),

("Explain method overloading vs method overriding.", r"""
**Overloading (compile-time polymorphism):** same method name, **different parameter list** (number, types or order) in the same class or subclass. Return type alone can't distinguish overloads. Resolved by the compiler.
```java
double area(double r) {...}
double area(double l, double w) {...}
```
**Overriding (runtime polymorphism):** a subclass provides a new implementation of a parent method with the **same signature**. Resolved at runtime based on the actual object (dynamic dispatch).
```java
class Animal { String sound() { return "..."; } }
class Dog extends Animal { @Override String sound() { return "Woof"; } }
Animal a = new Dog(); a.sound(); // "Woof"
```
Overriding rules: same signature, covariant return allowed, can't reduce visibility, can't throw broader checked exceptions; `static`, `private` and `final` methods can't be overridden (static ones are *hidden*). Use `@Override` to catch mistakes.
""", B, ["oop", "polymorphism"], True),

("What are the SOLID principles? Explain each briefly with an example.", r"""
- **S – Single Responsibility:** one reason to change. Split `InvoiceService` that calculates, saves, generates PDFs and emails into separate classes.
- **O – Open/Closed:** open for extension, closed for modification. Replace `if (type == GOLD)` chains with a `DiscountPolicy` interface and one class per tier.
- **L – Liskov Substitution:** subclasses must be substitutable for their base type without breaking behaviour. `Square extends Rectangle` violates it (setting width changes height).
- **I – Interface Segregation:** many small, client-specific interfaces instead of one fat interface. Don't force `RobotWorker` to implement `eat()`.
- **D – Dependency Inversion:** depend on abstractions, not concretions. `OrderService` depends on `OrderRepository` interface injected via constructor, not `new MySqlOrderRepository()`.

Benefit: code that is easier to extend, test (mock dependencies) and maintain. Back it with one real refactoring from your project.
""", I, ["solid", "design-principles"], True),

("Explain the Open/Closed Principle with a real example.", r"""
**Open for extension, closed for modification** — you should be able to add behaviour without editing tested, deployed code.

Violation (every new payment mode edits this method):
```java
public void pay(Order o, String mode) {
    if (mode.equals("UPI")) { ... }
    else if (mode.equals("CARD")) { ... }
    else if (mode.equals("NETBANKING")) { ... }
}
```
OCP-compliant with Strategy + Spring DI:
```java
public interface PaymentProcessor { String mode(); void pay(Order o); }
@Component class UpiProcessor implements PaymentProcessor { public String mode() { return "UPI"; } public void pay(Order o) { ... } }

@Service class PaymentService {
    private final Map<String, PaymentProcessor> byMode;
    PaymentService(List<PaymentProcessor> ps) { byMode = ps.stream().collect(toMap(PaymentProcessor::mode, p -> p)); }
    public void pay(Order o, String mode) { byMode.get(mode).pay(o); }
}
```
Adding "WALLET" = one new `@Component` class; `PaymentService` is untouched, existing tests stay valid.
""", I, ["solid", "ocp"], True),

("What is the Liskov Substitution Principle? Give a violation example.", r"""
LSP: **if S is a subtype of T, objects of T can be replaced with objects of S without altering the correctness of the program.** Subclasses must honour the base class's **contract** — they may not strengthen preconditions, weaken postconditions, or throw new unexpected exceptions.

Violation:
```java
class Rectangle { protected int w, h; void setWidth(int w){this.w=w;} void setHeight(int h){this.h=h;} int area(){return w*h;} }
class Square extends Rectangle {
    void setWidth(int w){ this.w = this.h = w; }
    void setHeight(int h){ this.w = this.h = h; }
}
void resize(Rectangle r) { r.setWidth(5); r.setHeight(4); assert r.area() == 20; } // fails for Square (16)
```
Another: a `ReadOnlyAccount extends Account` that throws on `withdraw()`.

Fix: don't force an is-a relationship that isn't behaviourally true. Use a common `Shape` interface with `area()`, or separate `Withdrawable` capability interfaces. Symptoms of LSP violations: `instanceof` checks and `UnsupportedOperationException` in overrides.
""", I, ["solid", "lsp"], True),

("What is the difference between Dependency Inversion, Dependency Injection and Inversion of Control?", r"""
- **Dependency Inversion Principle (DIP)** – a *design principle* (the D in SOLID): high-level modules and low-level modules should both depend on **abstractions**; details depend on abstractions.
- **Inversion of Control (IoC)** – a broader *concept*: control over object creation and flow is handed to a framework/container rather than your code ("don't call us, we'll call you"). Spring's container, servlet lifecycle, Angular bootstrapping.
- **Dependency Injection (DI)** – a *technique/pattern* that implements IoC for dependencies: objects receive their collaborators from outside (constructor, setter, field) instead of creating them with `new`.

```java
@Service
class OrderService {
    private final OrderRepository repo;      // abstraction (DIP)
    OrderService(OrderRepository repo) {     // injected by Spring (DI via IoC container)
        this.repo = repo;
    }
}
```
Prefer constructor injection: immutable dependencies, mandatory deps explicit, easy unit testing without Spring.
""", I, ["solid", "dip", "di", "spring"], True),

("What are DRY, KISS and YAGNI?", r"""
- **DRY (Don't Repeat Yourself):** each piece of knowledge (business rule, validation, constant) should exist in one place. Duplicate GST logic in three services → one fix gets missed. But don't merge code that only *looks* similar yet changes for different reasons — the wrong abstraction is worse than duplication (rule of three).
- **KISS (Keep It Simple, Stupid):** choose the simplest design that meets requirements; readable code over clever code. Don't introduce Kafka, microservices or NgRx when a direct call, a module or a service is enough.
- **YAGNI (You Aren't Gonna Need It):** don't build features/abstractions for imagined future requirements. Build for today, keep code easy to change.

They balance SOLID: SOLID pushes towards abstraction and extensibility; KISS/YAGNI push back against over-engineering. Good engineers apply abstractions when there's a real, present need (e.g. second payment provider arrives).
""", B, ["design-principles"], True),

("What is composition over inheritance? Why is it preferred?", r"""
"Favour composition over inheritance" (Gang of Four) means: reuse behaviour by **holding references to other objects (has-a) and delegating**, rather than extending classes (is-a).

Why:
1. **Loose coupling** – depends on an interface, not the parent's internals (no **fragile base class** problem).
2. **Flexibility** – behaviour can be swapped at runtime and combined freely (a `NotificationService` with any `MessageSender` × any `RetryPolicy`), avoiding class explosion.
3. **Java single inheritance** isn't a constraint for composition.
4. **Better encapsulation and testability** – inject mocks for collaborators.

Classic pitfall: `class CountingSet extends HashSet` overriding `add` and `addAll` double-counts because `HashSet.addAll` calls `add` internally. A wrapper (`implements Set`, delegating to an inner set) avoids it.

Use inheritance for true, stable is-a relationships that satisfy LSP (custom exceptions, framework extension points like `OncePerRequestFilter`).
""", I, ["composition", "inheritance"], True),

("What is the difference between association, aggregation and composition?", r"""
All three describe relationships between classes:

- **Association** – a general "uses/knows" relationship; objects have independent lifecycles. A `Teacher` and a `Student` are associated; neither owns the other.
- **Aggregation** – a **weak has-a** (whole–part) where parts can exist independently of the whole. A `Department` has `Employee`s; deleting the department doesn't delete employees. UML: hollow diamond.
- **Composition** – a **strong has-a** where the part's lifecycle is bound to the whole. An `Order` has `OrderItem`s; deleting the order deletes its items. A `House` has `Room`s. UML: filled diamond.

```java
class Order {
    private final List<OrderItem> items = new ArrayList<>();   // created & owned by Order (composition)
    private Customer customer;                                  // exists independently (association/aggregation)
}
```
JPA mirror: composition ≈ `@OneToMany(cascade = ALL, orphanRemoval = true)`.
""", B, ["oop", "relationships"], False),

("What is a design pattern? Name the three categories with examples.", r"""
A **design pattern** is a reusable, named solution to a commonly occurring design problem in a given context — a template, not finished code. The Gang of Four book catalogued 23 patterns in three categories:

1. **Creational** – object creation mechanisms: **Singleton**, **Factory Method**, **Abstract Factory**, **Builder**, **Prototype**.
2. **Structural** – composing classes/objects into larger structures: **Adapter**, **Decorator**, **Proxy**, **Facade**, **Composite**, Bridge, Flyweight.
3. **Behavioural** – communication and responsibility between objects: **Strategy**, **Observer**, **Template Method**, **Chain of Responsibility**, **Command**, **State**, Iterator, Mediator, Visitor, Memento, Interpreter.

Benefits: shared vocabulary ("let's use a strategy here"), proven designs, maintainability. Risk: forcing patterns where simple code suffices (violates KISS). Mention where you've seen them in Spring/Angular to stand out.
""", B, ["design-patterns"], True),

("Implement a thread-safe Singleton in Java. What are the ways to break it?", r"""
```java
public final class AppConfig {
    private static volatile AppConfig instance;
    private AppConfig() {
        if (instance != null) throw new IllegalStateException("Use getInstance()"); // reflection guard
    }
    public static AppConfig getInstance() {
        if (instance == null) {                          // 1st check, no lock
            synchronized (AppConfig.class) {
                if (instance == null) instance = new AppConfig();   // 2nd check
            }
        }
        return instance;
    }
    private Object readResolve() { return getInstance(); }   // serialization guard
}
```
`volatile` prevents another thread from seeing a partially constructed object due to instruction reordering.

Alternatives: **eager init** (`private static final AppConfig I = new AppConfig();`), **Bill Pugh holder** (lazy, thread-safe via class loading), and the **enum singleton** — the most robust (handles serialization and reflection automatically).

Ways to break: **reflection** (calling the private constructor), **serialization/deserialization**, **cloning**, **multiple class loaders**. In Spring apps, prefer singleton-scoped beans over manual singletons.
""", I, ["design-patterns", "singleton", "java"], True),

("Explain the Factory pattern. How is it different from Abstract Factory?", r"""
**Factory (Method / Simple Factory):** encapsulates object creation so clients request an object by type/parameter and get back an interface, without knowing concrete classes.
```java
public static Notification create(Channel c) {
    return switch (c) {
        case SMS -> new SmsNotification();
        case EMAIL -> new EmailNotification();
        case PUSH -> new PushNotification();
    };
}
```
Benefits: decouples clients from concrete classes, centralises creation logic, makes adding types easier.

**Abstract Factory:** a factory interface that creates **families of related objects** that must be used together.
```java
interface CloudFactory { Storage storage(); Queue queue(); }
class AwsFactory implements CloudFactory { /* S3Storage, SqsQueue */ }
class GcpFactory implements CloudFactory { /* GcsStorage, PubSubQueue */ }
```
Difference: Factory Method creates **one product**; Abstract Factory creates **a family of products** and ensures they're compatible. Spring's `BeanFactory` is a general-purpose factory.
""", I, ["design-patterns", "factory"], True),

("What is the Builder pattern and when would you use it?", r"""
The **Builder** pattern separates the construction of a complex object from its representation, building it step by step with a fluent API, then calling `build()`.

Use it when:
- A class has **many parameters**, especially optional ones (avoids **telescoping constructors** like `new User(a, b, null, null, true, 0)`).
- You want **immutable** objects with readable construction.
- You need validation before creation (in `build()`).

```java
User user = User.builder()
    .name("Raj")
    .email("raj@example.com")
    .phone("98xxxxxx")
    .role(Role.ADMIN)
    .build();
```
Examples: `StringBuilder`, `HttpClient.newBuilder()`, `HttpRequest.newBuilder()`, Lombok `@Builder`, Spring `ResponseEntity.status(201).header(...).body(...)`, `MockMvcRequestBuilders`. Downside: extra boilerplate (mitigated by Lombok or records for simple cases).
""", B, ["design-patterns", "builder"], True),

("Explain the Strategy pattern with an example.", r"""
**Strategy** defines a family of algorithms, encapsulates each one behind a common interface, and makes them interchangeable at runtime. The client (context) holds a reference to a strategy and delegates to it.

```java
public interface PricingStrategy { BigDecimal finalPrice(BigDecimal base); }
public class RegularPricing implements PricingStrategy { public BigDecimal finalPrice(BigDecimal b) { return b; } }
public class FestiveSalePricing implements PricingStrategy { public BigDecimal finalPrice(BigDecimal b) { return b.multiply(new BigDecimal("0.8")); } }
public class PrimeMemberPricing implements PricingStrategy { ... }

public class Checkout {
    private PricingStrategy pricing;
    public Checkout(PricingStrategy pricing) { this.pricing = pricing; }
    public void setPricing(PricingStrategy p) { this.pricing = p; }   // swap at runtime
    public BigDecimal total(BigDecimal base) { return pricing.finalPrice(base); }
}
```
Benefits: removes `if/else`/`switch` chains, follows **Open/Closed**, each algorithm testable in isolation. JDK: `Comparator` passed to `Collections.sort`. With Java 8, simple strategies can be lambdas: `Function<BigDecimal, BigDecimal>`.
""", I, ["design-patterns", "strategy"], True),

("Explain the Observer pattern. Where is it used in Spring and Angular?", r"""
**Observer** defines a one-to-many dependency: when a **subject** changes state, all registered **observers** are notified automatically. It decouples the producer from consumers.

```java
interface StockObserver { void onPriceChange(String symbol, double price); }
class StockTicker {
    private final List<StockObserver> observers = new CopyOnWriteArrayList<>();
    void subscribe(StockObserver o) { observers.add(o); }
    void unsubscribe(StockObserver o) { observers.remove(o); }
    void update(String s, double p) { observers.forEach(o -> o.onPriceChange(s, p)); }
}
```
**Spring:** `ApplicationEventPublisher.publishEvent(new OrderPlacedEvent(...))` with `@EventListener` / `@TransactionalEventListener` handlers (email, analytics) — the order service doesn't know who listens.

**Angular:** RxJS `Observable`/`Subject` (`subscribe`), `EventEmitter` for `@Output`, signals' `effect`. At system level, Kafka/pub-sub is the distributed form.

Pitfalls: memory leaks if observers aren't unsubscribed, unpredictable notification order, cascading updates.
""", I, ["design-patterns", "observer"], True),

("What is the Decorator pattern? How is it different from inheritance and Proxy?", r"""
**Decorator** attaches additional responsibilities to an object **dynamically** by wrapping it in an object of the same interface that adds behaviour before/after delegating.

```java
interface Notifier { void send(String msg); }
class EmailNotifier implements Notifier { public void send(String m) { ... } }
class SlackDecorator implements Notifier {
    private final Notifier inner;
    SlackDecorator(Notifier inner) { this.inner = inner; }
    public void send(String m) { inner.send(m); postToSlack(m); }
}
Notifier n = new SlackDecorator(new SmsDecorator(new EmailNotifier()));
```
**vs inheritance:** decorators compose at runtime and in any combination, avoiding a subclass per combination. Java I/O streams (`BufferedInputStream(new FileInputStream(...))`) are the textbook example.

**vs Proxy:** structurally similar (wrapper with the same interface), but intent differs: a **proxy controls access** to the object (lazy loading, security, remote, transactions — Spring AOP `@Transactional`), usually managing the real object's lifecycle; a **decorator adds features** and is typically stacked explicitly by the client.
""", I, ["design-patterns", "decorator", "proxy"], False),

("What is the Proxy pattern? Why does @Transactional not work when a method calls another method in the same class?", r"""
**Proxy** provides a surrogate object with the **same interface** as the real object to **control access** to it — adding lazy loading, access checks, caching, remote calls, logging or transactions around the real call.

Spring AOP creates a proxy (JDK dynamic proxy for interfaces, CGLIB subclass otherwise) around beans with `@Transactional`, `@Cacheable`, `@Async`, `@PreAuthorize`. Callers get the proxy; the proxy opens the transaction, then delegates to the real bean.

```java
@Service
public class OrderService {
    public void placeAll(List<Order> orders) {
        orders.forEach(this::place);      // 'this' = the real object, NOT the proxy
    }
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void place(Order o) { ... }    // transaction annotation ignored here
}
```
**Self-invocation** goes through `this`, bypassing the proxy, so no transaction starts. Fixes: move `place()` to another bean, inject the bean into itself (`@Lazy` self-reference), use `TransactionTemplate`, or AspectJ weaving. Also: proxies only intercept `public` methods (by default) and `final` methods can't be proxied by CGLIB.

Other proxies: Hibernate lazy-loading entity proxies, Java RMI stubs.
""", A, ["design-patterns", "proxy", "spring"], True),

("What is the Adapter pattern? Give a real use case.", r"""
**Adapter** converts the interface of an existing class into another interface clients expect, letting incompatible classes work together — like a travel plug adapter.

Use case: your app defines `SmsSender.send(String phone, String text)`, but a newly chosen vendor SDK exposes `VendorClient.dispatch(MessageRequest req)`.
```java
public class VendorSmsAdapter implements SmsSender {
    private final VendorClient client;
    public VendorSmsAdapter(VendorClient client) { this.client = client; }
    @Override public void send(String phone, String text) {
        client.dispatch(new MessageRequest("+91" + phone, text, Priority.HIGH));
    }
}
```
Business code keeps using `SmsSender`; switching vendors means writing another adapter (ties to OCP and DIP — also called an anti-corruption layer when wrapping legacy systems).

JDK examples: `Arrays.asList()` (array → List), `InputStreamReader` (byte stream → character stream). Spring MVC's `HandlerAdapter` lets `DispatcherServlet` invoke different handler types uniformly.
""", B, ["design-patterns", "adapter"], False),

("Which design patterns does the Spring Framework use?", r"""
- **Singleton** – default bean scope (one instance per container).
- **Factory** – `BeanFactory`/`ApplicationContext` create beans; `FactoryBean` for complex creation.
- **Prototype** – prototype bean scope.
- **Proxy** – Spring AOP proxies (JDK dynamic proxy/CGLIB) implement `@Transactional`, `@Cacheable`, `@Async`, `@PreAuthorize`. Explains why self-invocation skips them.
- **Template Method** – `JdbcTemplate`, `RestTemplate`, `TransactionTemplate`, `JmsTemplate` handle boilerplate and call your callbacks.
- **Observer** – `ApplicationEvent`, `ApplicationListener`, `@EventListener`.
- **Front Controller** – `DispatcherServlet` routes every request.
- **Strategy** – `PasswordEncoder`, `HandlerMapping`, `ViewResolver` implementations.
- **Chain of Responsibility** – Spring Security filter chain, `HandlerInterceptor`s.
- **Adapter** – `HandlerAdapter`.
- **Dependency Injection / IoC** – the core of the container.
- **MVC** – Spring Web MVC architecture.

Showing this mapping proves you understand patterns beyond textbook definitions.
""", I, ["design-patterns", "spring"], True),

("What is the Chain of Responsibility pattern?", r"""
**Chain of Responsibility** passes a request along a chain of handlers; each handler either processes it, passes it on, or both. The sender doesn't know which handler will handle it, decoupling sender and receivers.

```java
abstract class Approver {
    protected Approver next;
    Approver linkWith(Approver next) { this.next = next; return next; }
    abstract void approve(Expense e);
}
class Manager extends Approver {
    void approve(Expense e) { if (e.amount() <= 10_000) System.out.println("Manager approved"); else next.approve(e); }
}
class Director extends Approver { void approve(Expense e) { if (e.amount() <= 1_00_000) ... else next.approve(e); } }
class Cfo extends Approver { void approve(Expense e) { ... } }

Approver chain = new Manager(); chain.linkWith(new Director()).linkWith(new Cfo());
chain.approve(new Expense(50_000));   // Director approved
```
Real uses: **Servlet filters / Spring Security filter chain** (authentication, CORS, CSRF filters), Spring `HandlerInterceptor`s, **Angular HTTP interceptors**, logging levels, middleware in Express. Benefits: add/reorder handlers without changing the sender (OCP).
""", I, ["design-patterns", "chain-of-responsibility"], False),

("What is the State pattern? How would you model an order lifecycle?", r"""
**State** lets an object change its behaviour when its internal state changes, by delegating to a state object. It replaces large `switch(status)` blocks scattered across methods.

```java
interface OrderState {
    default OrderState pay(Order o)    { throw new IllegalStateException("Cannot pay in " + name()); }
    default OrderState ship(Order o)   { throw new IllegalStateException("Cannot ship in " + name()); }
    default OrderState cancel(Order o) { throw new IllegalStateException("Cannot cancel in " + name()); }
    String name();
}
class Created implements OrderState {
    public OrderState pay(Order o) { return new Paid(); }
    public OrderState cancel(Order o) { return new Cancelled(); }
    public String name() { return "CREATED"; }
}
class Paid implements OrderState {
    public OrderState ship(Order o) { return new Shipped(); }
    public OrderState cancel(Order o) { o.refund(); return new Cancelled(); }
    public String name() { return "PAID"; }
}
class Order { private OrderState state = new Created(); void pay() { state = state.pay(this); } ... }
```
Each state allows only valid transitions; adding a state (e.g. `RETURNED`) is a new class. Common in LLD rounds (vending machine, ATM, elevator). In practice, a simpler alternative is an enum with an allowed-transitions map, or Spring Statemachine.
""", A, ["design-patterns", "state", "lld"], False),

("What are coupling and cohesion? Why do we want low coupling and high cohesion?", r"""
- **Cohesion** – how closely related the responsibilities **within** a module/class are. High cohesion: an `InvoiceCalculator` does only invoice math. Low cohesion: a `Utils` class with date formatting, email sending and tax rules.
- **Coupling** – how much a module **depends on other modules'** internals. Tight coupling: `OrderService` instantiates `MySqlOrderRepository` and reads its fields. Loose coupling: depends on an `OrderRepository` interface injected via constructor, or communicates via events.

Why **high cohesion + low coupling**:
- Changes stay **localised** (one reason to change → SRP).
- Modules are **reusable** and **testable** in isolation (mock interfaces).
- Teams can work in parallel; easier to split into microservices later.
- Fewer ripple effects and regressions.

Techniques: interfaces + DI, SRP, Law of Demeter, events/message queues, clear module boundaries (packages by feature, not by layer).
""", B, ["design-principles"], True),

("What is the Template Method pattern? Give an example from a framework.", r"""
**Template Method** defines the **skeleton of an algorithm** in a base-class method, deferring some steps to subclasses (or callbacks). The overall sequence stays fixed; specific steps vary.

```java
public abstract class ReportGenerator {
    public final byte[] generate(ReportRequest req) {   // template method (final: order can't change)
        var data = fetchData(req);
        var rows = transform(data);
        return render(rows);                            // e.g. CSV vs PDF
    }
    protected abstract List<Record> fetchData(ReportRequest req);
    protected List<Row> transform(List<Record> d) { return d.stream().map(Row::from).toList(); } // hook (optional override)
    protected abstract byte[] render(List<Row> rows);
}
class SalesCsvReport extends ReportGenerator { ... }
```
Framework examples: Spring's **`JdbcTemplate`** (handles connection, statement, exceptions, closing; you supply SQL and a `RowMapper` callback), `RestTemplate`, `AbstractRoutingDataSource`, Servlet `HttpServlet.service()` dispatching to `doGet`/`doPost`, JUnit's setup → test → teardown.

Difference from Strategy: Template Method uses **inheritance** to vary steps; Strategy uses **composition** to swap the whole algorithm.
""", I, ["design-patterns", "template-method"], False),
]

sources = [
("Refactoring.Guru - Design Patterns catalogue", "https://refactoring.guru/design-patterns"),
("Refactoring.Guru - Code smells", "https://refactoring.guru/refactoring/smells"),
("Effective Java, 3rd Ed. (Joshua Bloch) - Item 18: Favor composition over inheritance", "https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/"),
("Robert C. Martin - The Principles of OOD", "http://butunclebob.com/ArticleS.UncleBob.PrinciplesOfOod"),
("Spring Framework Reference - Core Technologies (IoC, AOP)", "https://docs.spring.io/spring-framework/reference/core.html"),
("GeeksforGeeks - SOLID Principles", "https://www.geeksforgeeks.org/solid-principle-in-programming-understand-with-real-life-examples/"),
("InterviewBit - OOPs Interview Questions", "https://www.interviewbit.com/oops-interview-questions/"),
]

build("oop-design-patterns", "oop", "OOP & Design Principles", 10, "🧩",
      "OOP pillars, SOLID, DRY/KISS/YAGNI, composition vs inheritance and the GoF design patterns most asked in Java interviews.",
      notes, qa, sources)
