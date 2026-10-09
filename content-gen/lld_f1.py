from lld_common import *

topics = []

topics.append(T(
"how-to-approach-lld", "How to Approach an LLD / Machine Coding Round", 1, "Basic", 25,
"A repeatable, time-boxed playbook for turning a vague prompt like 'design a parking lot' into clean, extensible, working Java code in 60-120 minutes.",
r'''
## What the round actually is

Indian product companies run two flavours of Low Level Design (LLD) rounds:

| Flavour | Duration | What you produce | Typical companies |
|---|---|---|---|
| **Machine coding** | 90-150 min | Working, runnable code (often in your own IDE), demoed at the end | Flipkart, PhonePe, Swiggy, Razorpay, Zeta, Udaan, Cred |
| **Design discussion (LLD)** | 45-60 min | Class diagram + key classes/methods on a doc or whiteboard, discussion of patterns | Atlassian, Uber, Walmart, Amazon, Microsoft |

Both judge the same things: **can you model a real problem as objects, write readable code, and keep it open for change?** Nobody expects a database or a UI. In-memory storage plus a `Main` class (or a small CLI) is the norm.

## What interviewers score

1. **Working code** - in machine coding, a non-running solution is usually a reject, no matter how pretty.
2. **Modularity and separation of concerns** - models vs services vs repositories/strategies.
3. **Extensibility** - "now add a new vehicle type / payment method / pricing rule". Can you do it by adding a class rather than editing ten `if` blocks?
4. **Naming and readability** - meaningful class and method names, small methods.
5. **Edge cases and error handling** - invalid input, full lot, double booking, concurrency.
6. **Use of OOP / SOLID / patterns** - applied naturally, not forced.
7. **Testability** - dependencies injected via constructors, logic not buried in `main`.

## The 7-step playbook

### Step 1: Clarify requirements (5-8 min)
Never start coding immediately. Ask and **write down** answers:
- What are the core use cases? (e.g., park, unpark, show free slots)
- Who are the actors? (customer, admin, system)
- Scale assumptions: single process? multiple threads? (usually single JVM, in-memory)
- Out of scope: payments? persistence? UI? (usually yes, out)
- Input format: CLI commands, method calls, a file? (workat.tech-style problems often give a command format; follow it exactly)

Then split into **must-have** (P0) and **good-to-have** (P1). Finish all P0 before touching P1.

### Step 2: Identify entities (5 min)
Underline the nouns in the requirements: *Parking lot, floor, slot, vehicle, ticket, payment*. Nouns become classes; verbs become methods (`park()`, `unpark()`); adjectives/categories become enums (`VehicleType.CAR`) or subclasses only if behaviour differs.

### Step 3: Relationships and class diagram (5-10 min)
Decide: *ParkingLot has many Floors* (composition), *Floor has many Slots*, *Ticket references a Vehicle and a Slot* (association). Sketch a quick text UML. Mark interfaces for anything likely to vary (pricing, slot allocation, notification).

### Step 4: Choose patterns where variation exists
| Smell / requirement | Pattern |
|---|---|
| Multiple algorithms for one job (pricing, slot selection, split type) | Strategy |
| Object behaviour depends on its state (vending machine, elevator, order) | State |
| Notify many listeners on change | Observer |
| Complex object creation from type | Factory |
| Many optional fields | Builder |
| Exactly one shared manager | Singleton (prefer DI) |
| Undo/redo, queued requests | Command |
| Handler pipeline (logging levels, ATM cash dispensing, validation) | Chain of Responsibility |

### Step 5: Code in layers, bottom up (50-70% of time)
A clean package layout that interviewers like:

```text
model/       -> plain entities (Vehicle, Slot, Ticket), enums
repository/  -> in-memory storage (Map-based)
strategy/    -> interfaces + implementations of variable logic
service/     -> business logic orchestrating models + repositories
exception/   -> custom exceptions (SlotNotAvailableException)
Main.java    -> driver / demo / command parser
```

Skeleton of a typical service with constructor injection:

```java
public class ParkingService {
    private final ParkingLotRepository repo;
    private final SlotAllocationStrategy allocation;
    private final PricingStrategy pricing;

    public ParkingService(ParkingLotRepository repo,
                          SlotAllocationStrategy allocation,
                          PricingStrategy pricing) {
        this.repo = repo;
        this.allocation = allocation;
        this.pricing = pricing;
    }

    public Ticket park(Vehicle v) {
        Slot slot = allocation.findSlot(repo.getAllFloors(), v.getType())
                .orElseThrow(() -> new SlotNotAvailableException(v.getType()));
        slot.occupy(v);
        Ticket t = new Ticket(UUID.randomUUID().toString(), v, slot, System.currentTimeMillis());
        repo.saveTicket(t);
        return t;
    }
}
```

Get a thin **end-to-end path working first** (one happy-path use case running from `Main`), then widen. A half-finished grand design loses to a smaller working one.

### Step 6: Edge cases, validation, concurrency (10 min)
- Throw meaningful custom exceptions, catch them in the driver and print friendly messages.
- Guard shared mutable state: `synchronized` on the allocation method, or `ConcurrentHashMap` + atomic operations. Mention it even if you do not fully implement it.

### Step 7: Demo and discuss extensions (5-10 min)
Run `Main` with a scripted scenario covering happy paths and failures. Then proactively say: *"To add electric charging slots I would add a new SlotType and a new strategy; no existing class changes."* That sentence is worth points.

## Time management for a 90-minute round

| Minute | Activity |
|---|---|
| 0-10 | Clarify, list P0/P1 |
| 10-20 | Entities, diagram, interfaces |
| 20-70 | Code models -> repo -> strategies -> service -> Main |
| 70-80 | Edge cases, exceptions, quick tests in Main |
| 80-90 | Refactor names, demo, explain extensibility |

## Common mistakes that cause rejections
- Everything in one 400-line class or in `main`.
- Using `public` fields and no encapsulation.
- `if (type == CAR) ... else if (type == BIKE) ...` scattered everywhere instead of polymorphism/strategy.
- Over-engineering: 6 patterns for a 1-hour problem; abstract factories nobody needs.
- Not running the code until the last 5 minutes.
- Ignoring the given input/output format.
- Silent failures (returning `null` without explanation).

## Practice strategy for Raj
Coming from a Spring Boot service background you already know layering (controller/service/repository). The shift is: **no framework, pure Java, in-memory, and design for change**. Practise each problem in this section twice: first with a 90-minute timer, then refactor and compare with the reference. Aim for 15-18 problems before interviews.
''',
["Clarify use cases, actors, scale and out-of-scope items before writing code; split P0 vs P1.",
 "Nouns become classes, verbs become methods, categories become enums (or subclasses only if behaviour differs).",
 "Use interfaces wherever behaviour varies (pricing, allocation, notification) and inject them via constructors.",
 "Layer the code: model, repository (in-memory maps), strategy, service, exception, Main driver.",
 "Get one end-to-end happy path running early, then widen; working code beats a grand unfinished design.",
 "Handle edge cases with custom exceptions and mention thread safety for shared state.",
 "Finish by demoing and explaining how a new requirement is added by adding classes, not editing many."],
[("How do you start a machine coding round when the problem statement is vague?",
  r'''I spend the first 5-10 minutes clarifying. I list the core use cases, actors, input/output format and constraints such as single-process in-memory storage and whether concurrency matters. I explicitly confirm what is out of scope (UI, DB, payments). Then I split features into must-have and good-to-have and confirm that list with the interviewer. Only after that do I identify entities and interfaces. This prevents building the wrong thing and shows structured thinking, which is itself scored.'''),
 ("What does 'extensible design' mean in an LLD interview?",
  r'''It means a new requirement can be added mostly by **adding new code instead of modifying existing, tested code** (Open/Closed Principle). Practically: variable behaviour sits behind interfaces (e.g., `PricingStrategy`, `PaymentMethod`), objects are created via factories, and services depend on abstractions injected through constructors. If the interviewer says "add a new vehicle type" and you only add an enum constant plus maybe one strategy class, your design is extensible.'''),
 ("How do you manage time if you realise you cannot finish everything?",
  r'''I prioritise a running end-to-end flow for the P0 use cases. Models and the main service come first, then the driver; secondary features are stubbed with clear interfaces and a `// TODO` or an explanation. I would rather demo three working commands with clean code than ten half-written ones. In the last 10 minutes I stop adding features, run the demo, fix names and explain how the remaining features would plug into the existing interfaces.'''),
 ("Should you use design patterns in every LLD solution?",
  r'''No. Patterns are tools to handle variation, not a checklist. I introduce one only when a requirement implies it: multiple pricing rules suggest Strategy, state-dependent behaviour suggests State, notifications suggest Observer. Forcing patterns adds indirection and wastes time. Interviewers penalise over-engineering as much as a god class. A good answer names the pattern, explains the specific change it protects against, and keeps the implementation small.''')],
[WAT, ALLD, {"title": "workat.tech - Machine Coding Practice Problems", "url": "https://workat.tech/machine-coding/practice"}]
))

topics.append(T(
"oop-pillars", "OOP Pillars: Encapsulation, Abstraction, Inheritance, Polymorphism", 2, "Basic", 20,
"The four pillars of object-oriented programming explained with Java examples and how each one shows up in LLD interviews.",
r'''
## Why OOP matters in LLD

Every LLD solution is a set of collaborating objects. Interviewers check whether you **hide data**, **depend on abstractions**, **reuse sensibly** and **replace conditionals with polymorphism**. Those are exactly the four pillars.

## 1. Encapsulation - protect your invariants

Encapsulation means bundling data with the methods that operate on it and **restricting direct access** so the object can enforce its rules (invariants).

Bad - anyone can break the account:

```java
class BankAccount {
    public double balance;   // anyone can set balance = -5000
}
```

Good - state changes only through validated methods:

```java
class BankAccount {
    private final String id;
    private double balance;

    BankAccount(String id, double opening) {
        if (opening < 0) throw new IllegalArgumentException("negative opening");
        this.id = id;
        this.balance = opening;
    }

    public void deposit(double amt) {
        if (amt <= 0) throw new IllegalArgumentException("amount must be > 0");
        balance += amt;
    }

    public void withdraw(double amt) {
        if (amt > balance) throw new IllegalStateException("insufficient funds");
        balance -= amt;
    }

    public double getBalance() { return balance; }   // no setter!
}
```

LLD tips: make fields `private`, prefer `final` for identity fields, avoid blind setters, return unmodifiable views (`Collections.unmodifiableList(list)`) instead of internal collections.

## 2. Abstraction - expose *what*, hide *how*

Abstraction lets callers depend on a simplified contract. In Java you express it with **interfaces** and **abstract classes**.

```java
interface PaymentMethod {
    boolean pay(double amount);
}

class UpiPayment implements PaymentMethod {
    private final String vpa;
    UpiPayment(String vpa) { this.vpa = vpa; }
    public boolean pay(double amount) {
        System.out.println("Paid " + amount + " via UPI " + vpa);
        return true;
    }
}

class CardPayment implements PaymentMethod {
    public boolean pay(double amount) {
        System.out.println("Charged card " + amount);
        return true;
    }
}

class CheckoutService {
    public void checkout(double total, PaymentMethod method) {
        if (!method.pay(total)) throw new RuntimeException("payment failed");
    }
}
```

`CheckoutService` neither knows nor cares how UPI works.

**Interface vs abstract class** (classic question):

| Interface | Abstract class |
|---|---|
| Pure contract; a class can implement many | Partial implementation; single inheritance only |
| Fields are `public static final` constants | Can hold state (instance fields) |
| Since Java 8: `default` and `static` methods; Java 9: `private` methods | Can have constructors |
| Use for capabilities ("can pay", "can notify") | Use when subclasses share code/state ("is-a" with common logic) |

## 3. Inheritance - reuse via "is-a"

A subclass inherits fields and methods of a superclass and can override behaviour.

```java
abstract class Vehicle {
    private final String number;
    protected Vehicle(String number) { this.number = number; }
    public String getNumber() { return number; }
    public abstract int wheels();
}

class Car extends Vehicle {
    Car(String n) { super(n); }
    public int wheels() { return 4; }
}

class Bike extends Vehicle {
    Bike(String n) { super(n); }
    public int wheels() { return 2; }
}
```

**Favour composition over inheritance.** Inheritance couples the subclass to the parent's internals (the fragile base class problem) and Java allows only one parent. If the relation is "has-a" or behaviour needs to change at runtime, compose:

```java
class Duck {
    private FlyBehaviour fly;                // composition
    Duck(FlyBehaviour f) { this.fly = f; }
    void setFly(FlyBehaviour f) { this.fly = f; }   // swap at runtime
    void performFly() { fly.fly(); }
}
interface FlyBehaviour { void fly(); }
```

Rule of thumb in LLD: use inheritance for a stable type hierarchy with shared state (e.g., `Account -> SavingsAccount`), composition for behaviours that vary.

## 4. Polymorphism - one interface, many forms

- **Compile-time (static) polymorphism**: method overloading - same name, different parameter lists, resolved by the compiler.
- **Runtime (dynamic) polymorphism**: method overriding - the JVM picks the implementation based on the actual object type (dynamic dispatch).

```java
class Calculator {
    int add(int a, int b) { return a + b; }            // overload
    double add(double a, double b) { return a + b; }   // overload
}

List<Vehicle> vehicles = List.of(new Car("KA01"), new Bike("KA02"));
for (Vehicle v : vehicles) {
    System.out.println(v.getNumber() + " has " + v.wheels() + " wheels"); // runtime dispatch
}
```

The interview payoff: **polymorphism replaces `if/else` and `switch` on type**.

```java
// Smell
double fee(String type, int hours) {
    if (type.equals("CAR")) return hours * 40;
    else if (type.equals("BIKE")) return hours * 20;
    else if (type.equals("TRUCK")) return hours * 100;
    throw new IllegalArgumentException();
}

// Polymorphic
interface FeeRule { double fee(int hours); }
class CarFee implements FeeRule { public double fee(int h) { return h * 40; } }
class BikeFee implements FeeRule { public double fee(int h) { return h * 20; } }
```

Adding a truck now means adding a class, not editing a method.

## Related concepts often asked alongside

- **Association / Aggregation / Composition**: "uses", "has-a (independent lifetime)", "owns (dependent lifetime)". Covered in the UML topic.
- **`equals()` and `hashCode()`**: if you put entities in a `HashSet` or as `HashMap` keys, override both consistently (usually on the ID).
- **Immutability**: `final` class, `private final` fields, no setters, defensive copies - great for value objects like `Money`, `Location`, `Ticket`.
- **Access modifiers**: `private` < package-private < `protected` < `public`.
''',
["Encapsulation: private fields + validated methods so the object protects its own invariants; avoid blind setters.",
 "Abstraction: callers depend on interfaces/abstract classes that expose what, not how.",
 "Interface = capability contract, multiple allowed; abstract class = shared state/code, single inheritance.",
 "Inheritance models stable is-a hierarchies; prefer composition for behaviour that varies or must change at runtime.",
 "Overloading is compile-time polymorphism; overriding is runtime polymorphism via dynamic dispatch.",
 "Polymorphism is the main tool to eliminate if/else or switch on type, enabling Open/Closed designs.",
 "Override equals and hashCode together for entities used in hash-based collections; make value objects immutable."],
[("What is the difference between abstraction and encapsulation?",
  r'''**Encapsulation** is about *hiding data and protecting state*: private fields, access only through methods that validate. **Abstraction** is about *hiding complexity*: exposing a simple contract (an interface like `PaymentMethod.pay()`) and hiding implementation details. Encapsulation is implemented with access modifiers; abstraction with interfaces and abstract classes. They work together: a `UpiPayment` class encapsulates its VPA field while the `PaymentMethod` interface abstracts the payment process away from the checkout code.'''),
 ("Why is composition preferred over inheritance?",
  r'''Inheritance creates tight coupling: subclasses depend on parent internals, changes in the parent can break children (fragile base class), Java allows only one parent, and behaviour is fixed at compile time. Composition holds a reference to another object behind an interface, so behaviour can be swapped at runtime, classes stay small, and testing with mocks is easy. Strategy, Decorator and State are all composition-based. Use inheritance only for a genuine, stable is-a relationship with shared code.'''),
 ("Can you override a static or private method in Java?",
  r'''No. `private` methods are not visible to subclasses, so a same-named method in a subclass is a brand new method. `static` methods belong to the class, not the instance; a same-signature static method in a subclass **hides** the parent's method (method hiding), and the call is resolved at compile time using the reference type, not the runtime object. Only non-static, non-private, non-final instance methods participate in runtime polymorphism.'''),
 ("When would you choose an abstract class over an interface?",
  r'''When subclasses share **state or a common algorithm** and need constructors, e.g., an abstract `Account` with `id`, `balance` and a concrete `withdraw()` that calls an abstract `withdrawLimit()`. Interfaces are better for capabilities that unrelated classes can have (`Comparable`, `Notifier`) and when a class must play several roles. A common modern approach is an interface for the contract plus an optional abstract base class implementing shared parts.''')],
[{"title": "Oracle Java Tutorials - Object-Oriented Programming Concepts", "url": "https://docs.oracle.com/javase/tutorial/java/concepts/index.html"},
 {"title": "Oracle Java Tutorials - Interfaces and Inheritance", "url": "https://docs.oracle.com/javase/tutorial/java/IandI/index.html"}, ALLD]
))

topics.append(T(
"solid-principles", "SOLID Principles with Bad vs Good Java", 3, "Basic", 30,
"The five SOLID principles, each shown as a realistic bad Java design and its refactored good version, the way interviewers expect you to explain them.",
r'''
SOLID is a set of five principles (popularised by Robert C. Martin) that keep object-oriented code easy to change. In LLD rounds you are expected to **apply** them and to **name** them when justifying decisions.

## S - Single Responsibility Principle (SRP)

> A class should have **one reason to change** (one actor it serves).

Bad - an invoice class that calculates, prints and saves:

```java
class Invoice {
    private List<Item> items;
    double total() { return items.stream().mapToDouble(Item::price).sum(); }
    void printInvoice() { System.out.println("Total: " + total()); }   // presentation
    void saveToDb() { /* JDBC code */ }                                // persistence
}
```

A change in print format, DB schema or tax logic all touch the same class.

Good - split by responsibility:

```java
class Invoice {
    private final List<Item> items;
    Invoice(List<Item> items) { this.items = items; }
    double total() { return items.stream().mapToDouble(Item::price).sum(); }
}
class InvoicePrinter {
    void print(Invoice inv) { System.out.println("Total: " + inv.total()); }
}
class InvoiceRepository {
    void save(Invoice inv) { /* persistence only */ }
}
```

## O - Open/Closed Principle (OCP)

> Software entities should be **open for extension, closed for modification**.

Bad - every new discount type edits this method:

```java
class DiscountCalculator {
    double discount(String customerType, double amount) {
        if (customerType.equals("REGULAR")) return 0;
        if (customerType.equals("PREMIUM")) return amount * 0.10;
        if (customerType.equals("EMPLOYEE")) return amount * 0.30;
        return 0;
    }
}
```

Good - new behaviour = new class:

```java
interface DiscountPolicy { double discount(double amount); }

class RegularDiscount implements DiscountPolicy {
    public double discount(double a) { return 0; }
}
class PremiumDiscount implements DiscountPolicy {
    public double discount(double a) { return a * 0.10; }
}
class FestiveDiscount implements DiscountPolicy {      // added later, nothing else changed
    public double discount(double a) { return Math.min(a * 0.20, 500); }
}

class Checkout {
    private final DiscountPolicy policy;
    Checkout(DiscountPolicy policy) { this.policy = policy; }
    double payable(double amount) { return amount - policy.discount(amount); }
}
```

This is the Strategy pattern in action.

## L - Liskov Substitution Principle (LSP)

> Objects of a subclass must be usable wherever the parent is expected **without breaking correctness**.

Bad - the textbook `Bird`/`Penguin` violation:

```java
class Bird {
    void fly() { System.out.println("flying"); }
}
class Penguin extends Bird {
    @Override
    void fly() { throw new UnsupportedOperationException("Penguins can't fly"); }
}

void migrate(List<Bird> birds) { birds.forEach(Bird::fly); }  // blows up on Penguin
```

Good - model capabilities correctly:

```java
abstract class Bird { abstract void eat(); }
interface Flyable { void fly(); }

class Sparrow extends Bird implements Flyable {
    void eat() { System.out.println("seeds"); }
    public void fly() { System.out.println("sparrow flying"); }
}
class Penguin extends Bird {
    void eat() { System.out.println("fish"); }
}

void migrate(List<Flyable> flyers) { flyers.forEach(Flyable::fly); }
```

LSP red flags: overriding a method to throw `UnsupportedOperationException`, strengthening preconditions (subclass rejects inputs the parent accepts), weakening postconditions, `instanceof` checks in client code. Another classic is `Square extends Rectangle` where `setWidth` silently changes height.

## I - Interface Segregation Principle (ISP)

> Clients should not be forced to depend on methods they do not use.

Bad - a fat interface:

```java
interface Machine {
    void print(Document d);
    void scan(Document d);
    void fax(Document d);
}
class BasicPrinter implements Machine {
    public void print(Document d) { /* ok */ }
    public void scan(Document d) { throw new UnsupportedOperationException(); }
    public void fax(Document d)  { throw new UnsupportedOperationException(); }
}
```

Good - small role interfaces, combine as needed:

```java
interface Printer { void print(Document d); }
interface Scanner { void scan(Document d); }
interface Fax { void fax(Document d); }

class BasicPrinter implements Printer {
    public void print(Document d) { System.out.println("printing"); }
}
class OfficeMachine implements Printer, Scanner, Fax {
    public void print(Document d) { }
    public void scan(Document d) { }
    public void fax(Document d) { }
}
```

In LLD: an `ATM` admin interface (`refill`, `audit`) should be separate from the customer interface (`withdraw`, `balance`).

## D - Dependency Inversion Principle (DIP)

> High-level modules should not depend on low-level modules; **both depend on abstractions**.

Bad - service hard-wires a concrete class:

```java
class EmailSender {
    void send(String to, String msg) { System.out.println("Email to " + to); }
}
class OrderService {
    private final EmailSender sender = new EmailSender();   // tight coupling
    void placeOrder(Order o) {
        // ... business logic
        sender.send(o.customerEmail(), "Order placed");
    }
}
```

Switching to SMS or mocking in a test requires editing `OrderService`.

Good - depend on an interface, inject the implementation:

```java
interface Notifier { void notify(String to, String msg); }

class EmailNotifier implements Notifier {
    public void notify(String to, String msg) { System.out.println("Email: " + msg); }
}
class SmsNotifier implements Notifier {
    public void notify(String to, String msg) { System.out.println("SMS: " + msg); }
}

class OrderService {
    private final Notifier notifier;
    OrderService(Notifier notifier) { this.notifier = notifier; }   // constructor injection
    void placeOrder(Order o) {
        notifier.notify(o.customerContact(), "Order placed");
    }
}

// wiring (in Main, or Spring does it for you)
OrderService svc = new OrderService(new SmsNotifier());
```

You already use DIP daily in Spring Boot: `@Autowired` constructor injection of an interface bean **is** dependency injection, a technique that implements DIP. In a machine-coding round there is no Spring, so you wire objects manually in `Main`.

## Quick revision table

| Principle | One-liner | Typical fix |
|---|---|---|
| SRP | One reason to change | Split class by actor/responsibility |
| OCP | Extend without editing | Interfaces + Strategy/Factory |
| LSP | Subtypes must honour parent contract | Rethink hierarchy, capability interfaces |
| ISP | No forced unused methods | Split fat interfaces into roles |
| DIP | Depend on abstractions | Constructor injection of interfaces |

## How to talk about SOLID in an interview
Do not recite definitions only. Point at your code: *"`ParkingService` depends on the `PricingStrategy` interface injected via the constructor - that's DIP; adding weekend pricing is a new class - that's OCP."* Concrete beats abstract every time.
''',
["SRP: a class should have one reason to change; split calculation, presentation and persistence.",
 "OCP: add behaviour by adding classes (strategies, subclasses) rather than editing existing if/else chains.",
 "LSP: subclasses must be substitutable; throwing UnsupportedOperationException in an override is a red flag.",
 "ISP: prefer small role interfaces over one fat interface so clients implement only what they use.",
 "DIP: high-level code depends on interfaces; concrete implementations are injected (constructor injection).",
 "Spring's dependency injection is a mechanism that implements DIP; in machine coding you wire objects in Main.",
 "In interviews, justify design decisions by pointing to specific classes that satisfy each principle."],
[("Explain the Open/Closed Principle with a real example.",
  r'''A class should be open for extension but closed for modification. Example: a `FareCalculator` with `if (rideType == MINI) ... else if (SEDAN) ...` must be edited (and retested) for every new ride type. Instead define `interface FareStrategy { double fare(Ride r); }` with `MiniFare`, `SedanFare`, and inject the right one (perhaps via a factory). Adding `AutoFare` means writing one new class; existing tested classes stay untouched. OCP is usually achieved through polymorphism, Strategy and Factory patterns.'''),
 ("What is the difference between Dependency Inversion and Dependency Injection?",
  r'''**Dependency Inversion** is a design *principle*: high-level modules and low-level modules should both depend on abstractions, and abstractions should not depend on details. **Dependency Injection** is a *technique* for supplying an object's dependencies from outside (constructor, setter or field) instead of the object creating them with `new`. DI is the most common way to achieve DIP. Spring's IoC container automates DI, but you can do it manually by passing interfaces into constructors.'''),
 ("Give an example of a Liskov Substitution violation and how to fix it.",
  r'''`Square extends Rectangle`: `Rectangle` lets you set width and height independently, but `Square.setWidth()` must also change height. Client code that sets width 5, height 4 and expects area 20 gets 16 - substitution broke correctness. Fix: do not model Square as a subtype of mutable Rectangle; make both implement a `Shape` interface with `area()`, or make them immutable value objects. The same applies to `Penguin extends Bird` with `fly()`: move flying into a `Flyable` interface.'''),
 ("How does SRP relate to cohesion and coupling?",
  r'''SRP increases **cohesion**: everything in a class serves one purpose, so its methods and fields are closely related. Smaller focused classes also reduce **coupling**, because other classes depend only on the narrow piece they need. High cohesion and low coupling make code easier to test and change. A practical test: if describing the class needs the word "and" (it validates **and** saves **and** emails), it probably has multiple responsibilities.''')],
[{"title": "Robert C. Martin - The Principles of OOD", "url": "http://butunclebob.com/ArticleS.UncleBob.PrinciplesOfOod"},
 {"title": "DigitalOcean - SOLID: The First 5 Principles of Object Oriented Design", "url": "https://www.digitalocean.com/community/conceptual-articles/s-o-l-i-d-the-first-five-principles-of-object-oriented-design"}, ALLD]
))

topics.append(T(
"design-patterns-creational", "Creational Patterns: Singleton, Factory, Abstract Factory, Builder, Prototype", 4, "Intermediate", 30,
"How to create objects flexibly: thread-safe Singleton variants, Factory Method, Abstract Factory, Builder and Prototype with Java code and when to use each in LLD.",
r'''
Creational patterns decouple **what you create** from **how and where it is created**. In LLD they show up constantly: a single `ParkingLot` instance, a `VehicleFactory`, a `Pizza.Builder`.

## 1. Singleton

**Intent:** exactly one instance, globally accessible. Use for a shared manager/registry (e.g., `ParkingLot`, `Logger`, configuration). Interviewers *always* ask about thread safety.

### a) Eager initialization - simple, thread-safe
```java
public class AppConfig {
    private static final AppConfig INSTANCE = new AppConfig();
    private AppConfig() { }
    public static AppConfig getInstance() { return INSTANCE; }
}
```
Thread-safe because class initialization is guaranteed by the JVM to happen once. Downside: created even if never used.

### b) Lazy, synchronized method - safe but slower
```java
public class Logger {
    private static Logger instance;
    private Logger() { }
    public static synchronized Logger getInstance() {
        if (instance == null) instance = new Logger();
        return instance;
    }
}
```
Every call acquires a lock, even after creation.

### c) Double-checked locking - lazy and fast
```java
public class ParkingLot {
    private static volatile ParkingLot instance;   // volatile is essential
    private ParkingLot() { }

    public static ParkingLot getInstance() {
        if (instance == null) {                    // 1st check, no lock
            synchronized (ParkingLot.class) {
                if (instance == null) {            // 2nd check, with lock
                    instance = new ParkingLot();
                }
            }
        }
        return instance;
    }
}
```
**Why `volatile`?** `instance = new ParkingLot()` is not atomic: allocate memory, run constructor, assign reference. Without `volatile`, reordering can publish the reference before the constructor finishes, so another thread sees a half-built object. `volatile` adds a happens-before edge that forbids this.

### d) Bill Pugh / holder idiom - recommended
```java
public class IdGenerator {
    private IdGenerator() { }
    private static class Holder {
        private static final IdGenerator INSTANCE = new IdGenerator();
    }
    public static IdGenerator getInstance() { return Holder.INSTANCE; }
}
```
Lazy (Holder is loaded on first `getInstance()` call), thread-safe via class loading, no synchronization cost.

### e) Enum singleton - safest
```java
public enum Registry {
    INSTANCE;
    private final Map<String, String> data = new ConcurrentHashMap<>();
    public void put(String k, String v) { data.put(k, v); }
}
```
Protected against reflection and serialization attacks (which break the other variants unless you guard the constructor and add `readResolve()`).

**Caution:** Singletons are global state, hard to mock in tests. In LLD, it is often better to create one instance in `Main` and inject it. Mention this trade-off - it shows maturity.

## 2. Factory Method / Simple Factory

**Intent:** centralise creation logic so clients ask for an object by type and depend only on the interface.

```java
interface Notification { void send(String msg); }
class EmailNotification implements Notification {
    public void send(String m) { System.out.println("Email: " + m); }
}
class SmsNotification implements Notification {
    public void send(String m) { System.out.println("SMS: " + m); }
}
class PushNotification implements Notification {
    public void send(String m) { System.out.println("Push: " + m); }
}

enum Channel { EMAIL, SMS, PUSH }

class NotificationFactory {
    public static Notification create(Channel c) {
        return switch (c) {
            case EMAIL -> new EmailNotification();
            case SMS -> new SmsNotification();
            case PUSH -> new PushNotification();
        };
    }
}
```

The `switch` lives in **one place** instead of being scattered. The GoF "Factory Method" proper defines an abstract creation method that subclasses override:

```java
abstract class Logistics {
    abstract Transport createTransport();          // factory method
    void planDelivery() { createTransport().deliver(); }
}
class RoadLogistics extends Logistics { Transport createTransport() { return new Truck(); } }
class SeaLogistics extends Logistics { Transport createTransport() { return new Ship(); } }
```

A registry-based factory avoids editing even the switch: `Map<Channel, Supplier<Notification>>` where new types register themselves.

## 3. Abstract Factory

**Intent:** create **families of related objects** that must be used together, without naming concrete classes.

```java
interface Button { void render(); }
interface Checkbox { void render(); }

class LightButton implements Button { public void render() { System.out.println("Light button"); } }
class DarkButton implements Button { public void render() { System.out.println("Dark button"); } }
class LightCheckbox implements Checkbox { public void render() { System.out.println("Light checkbox"); } }
class DarkCheckbox implements Checkbox { public void render() { System.out.println("Dark checkbox"); } }

interface UiFactory {
    Button createButton();
    Checkbox createCheckbox();
}
class LightUiFactory implements UiFactory {
    public Button createButton() { return new LightButton(); }
    public Checkbox createCheckbox() { return new LightCheckbox(); }
}
class DarkUiFactory implements UiFactory {
    public Button createButton() { return new DarkButton(); }
    public Checkbox createCheckbox() { return new DarkCheckbox(); }
}

class SettingsScreen {
    private final Button b; private final Checkbox c;
    SettingsScreen(UiFactory f) { b = f.createButton(); c = f.createCheckbox(); }
    void draw() { b.render(); c.render(); }
}
```
Swapping the factory swaps the whole family consistently. LLD example: a payment gateway family (`RazorpayFactory` creating `RazorpayClient` + `RazorpayRefundHandler`).

## 4. Builder

**Intent:** construct complex objects step by step, avoiding "telescoping constructors" with many optional parameters, and produce immutable objects.

```java
public final class User {
    private final String name;      // required
    private final String email;     // required
    private final String phone;     // optional
    private final int age;          // optional

    private User(Builder b) {
        this.name = b.name; this.email = b.email;
        this.phone = b.phone; this.age = b.age;
    }

    public static class Builder {
        private final String name, email;
        private String phone; private int age;

        public Builder(String name, String email) { this.name = name; this.email = email; }
        public Builder phone(String p) { this.phone = p; return this; }
        public Builder age(int a) { this.age = a; return this; }
        public User build() {
            if (!email.contains("@")) throw new IllegalArgumentException("bad email");
            return new User(this);
        }
    }
}

User u = new User.Builder("Raj", "raj@x.com").phone("98xxxx").age(26).build();
```
Validation happens once in `build()`. Lombok's `@Builder` generates this; know how to write it by hand. LLD uses: `Order`, `Booking`, `HttpRequest`, search filters.

## 5. Prototype

**Intent:** create new objects by **copying** an existing configured instance, useful when construction is expensive or the configuration is complex.

```java
interface Prototype<T> { T copy(); }

class ShapeStyle implements Prototype<ShapeStyle> {
    String color; int border; List<String> tags;
    ShapeStyle(String color, int border, List<String> tags) {
        this.color = color; this.border = border; this.tags = tags;
    }
    public ShapeStyle copy() {
        return new ShapeStyle(color, border, new ArrayList<>(tags)); // deep copy of list
    }
}

ShapeStyle base = new ShapeStyle("red", 2, new ArrayList<>(List.of("bold")));
ShapeStyle variant = base.copy();
variant.color = "blue";      // base unaffected
```
Prefer a copy constructor or `copy()` method over `Cloneable`/`clone()`, which is shallow by default and awkward. Know **shallow vs deep copy**: shallow copies share nested mutable objects.

## Choosing quickly

| Need | Pattern |
|---|---|
| One shared instance | Singleton (or single instance injected) |
| Create one of many subtypes by a key | Factory |
| Create consistent families | Abstract Factory |
| Many optional params, immutability | Builder |
| Clone a preconfigured template | Prototype |
''',
["Singleton options: eager, synchronized lazy, double-checked locking (needs volatile), holder idiom, enum.",
 "volatile in double-checked locking prevents another thread from seeing a partially constructed instance.",
 "Enum singleton resists reflection and serialization; holder idiom gives lazy, lock-free thread safety.",
 "Factory centralises creation by type so clients depend only on interfaces; a registry map avoids editing a switch.",
 "Abstract Factory produces families of related objects that must stay consistent (themes, gateway SDKs).",
 "Builder replaces telescoping constructors, validates once in build(), and yields immutable objects.",
 "Prototype copies a configured object; understand shallow vs deep copy and prefer copy constructors to clone()."],
[("How do you make a Singleton thread-safe, and which approach do you prefer?",
  r'''Options: eager initialization (thread-safe via class loading), `synchronized getInstance()` (simple but locks every call), double-checked locking with a `volatile` field, the Bill Pugh holder idiom, and an enum. I prefer the **holder idiom** for lazy loading without locking, or an **enum** when serialization/reflection safety matters. In double-checked locking, `volatile` is mandatory to prevent instruction reordering from exposing a partially constructed object.'''),
 ("How can a Singleton be broken?",
  r'''Three ways: **reflection** (`setAccessible(true)` on the private constructor) - guard by throwing if the instance already exists; **serialization** - deserializing creates a new object unless you implement `readResolve()` returning the instance; **cloning** - override `clone()` to throw. Multiple class loaders can also create separate instances. An enum singleton is immune to reflection and serialization by JVM guarantee, which is why Effective Java recommends it.'''),
 ("Factory vs Abstract Factory - what's the difference?",
  r'''A **Factory (Method)** creates **one product** whose concrete type varies, e.g., `NotificationFactory.create(SMS)`. An **Abstract Factory** is an interface with several factory methods that create a **family of related products** meant to be used together, e.g., `DarkUiFactory` creates a dark button *and* a dark checkbox. You swap the whole factory to switch families consistently. Abstract Factories are often implemented using factory methods internally.'''),
 ("When would you use the Builder pattern instead of constructors?",
  r'''When an object has several optional parameters, when parameter lists become long and error-prone (two adjacent `String` params are easy to swap), or when the result should be immutable and validated as a whole. Builder gives readable, named, chainable steps and one validation point in `build()`. For two or three required fields, a plain constructor is fine; Builder would be over-engineering.''')],
[RG, {"title": "Refactoring.Guru - Singleton", "url": "https://refactoring.guru/design-patterns/singleton"},
 {"title": "Refactoring.Guru - Builder", "url": "https://refactoring.guru/design-patterns/builder"}, ALLD]
))

save("f1", "fundamentals", topics)
