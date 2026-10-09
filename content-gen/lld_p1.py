from lld_common import *

topics = []

topics.append(T(
"parking-lot", "Design a Parking Lot", 1, "Intermediate", 45,
"The most frequently asked LLD problem: a multi-floor parking lot with typed slots, tickets, pluggable slot allocation and pricing, and thread-safe parking.",
r'''
## Problem
Design a parking lot system with multiple floors. Vehicles of different types enter, get a ticket and a suitable slot, and pay on exit based on duration.

## Requirements
**Functional (P0)**
1. The lot has multiple floors; each floor has slots of types `SMALL` (bike), `MEDIUM` (car), `LARGE` (truck).
2. On entry, assign the nearest free compatible slot and issue a ticket.
3. On exit, compute the fee from the duration and vehicle type, free the slot.
4. Show free slot counts per floor and type.

**Good to have (P1):** multiple entry gates (concurrency), different pricing (hourly, flat weekend), larger vehicles allowed in bigger slots, payment modes.

**Out of scope:** UI, real payments, persistence.

## Entities
`ParkingLot`, `ParkingFloor`, `ParkingSlot`, `Vehicle` (`VehicleType`), `SlotType`, `Ticket`, `SlotAllocationStrategy`, `PricingStrategy`, `ParkingService`.

## Class diagram
```text
ParkingLot 1 *-- 1..* ParkingFloor 1 *-- 1..* ParkingSlot
ParkingSlot  - id, floor, type: SlotType, vehicle: Vehicle (0..1)
Vehicle      - number, type: VehicleType
Ticket       --> Vehicle, --> ParkingSlot, entryTime

<<interface>> SlotAllocationStrategy  + find(floors, VehicleType): Optional<ParkingSlot>
     ^.. BestFitStrategy
<<interface>> PricingStrategy  + fee(Ticket, exitTime): double
     ^.. HourlyPricing

ParkingService
  - lot: ParkingLot
  - allocation: SlotAllocationStrategy
  - pricing: PricingStrategy
  - activeTickets: Map<String, Ticket>
  + park(Vehicle): Ticket
  + unpark(ticketId, exitTime): double
```

## Patterns used and why
- **Strategy** for slot allocation and pricing: business keeps changing these ("fill top floor first", "weekend flat fee"). New rules = new classes (OCP).
- **Enum with behaviour** maps vehicle types to allowed slot types, avoiding `if/else` chains.
- **Dependency injection** via constructors keeps `ParkingService` testable (DIP).
- **Singleton (optional)**: a single `ParkingLot` - here created once in `Main` and injected, which is easier to test than a static singleton.
- **Thread safety**: `park` and `unpark` are `synchronized` on the service (simple), and the slot's `occupy` is atomic per slot. For high throughput, lock per floor.

## Java implementation
```java
import java.util.*;
import java.util.concurrent.*;

enum SlotType { SMALL, MEDIUM, LARGE }

enum VehicleType {
    BIKE(List.of(SlotType.SMALL, SlotType.MEDIUM, SlotType.LARGE)),
    CAR(List.of(SlotType.MEDIUM, SlotType.LARGE)),
    TRUCK(List.of(SlotType.LARGE));

    private final List<SlotType> allowed;   // preferred order: smallest fitting first
    VehicleType(List<SlotType> allowed) { this.allowed = allowed; }
    List<SlotType> allowedSlots() { return allowed; }
}

class Vehicle {
    private final String number;
    private final VehicleType type;
    Vehicle(String number, VehicleType type) { this.number = number; this.type = type; }
    String getNumber() { return number; }
    VehicleType getType() { return type; }
}

class ParkingSlot {
    private final String id;
    private final int floor;
    private final SlotType type;
    private Vehicle vehicle;

    ParkingSlot(String id, int floor, SlotType type) { this.id = id; this.floor = floor; this.type = type; }
    synchronized boolean isFree() { return vehicle == null; }
    synchronized boolean occupy(Vehicle v) {
        if (vehicle != null) return false;
        vehicle = v;
        return true;
    }
    synchronized void release() { vehicle = null; }
    String getId() { return id; }
    int getFloor() { return floor; }
    SlotType getType() { return type; }
}

class ParkingFloor {
    private final int number;
    private final List<ParkingSlot> slots = new ArrayList<>();
    ParkingFloor(int number, int small, int medium, int large) {
        this.number = number;
        int id = 1;
        for (int i = 0; i < small; i++) slots.add(new ParkingSlot("F" + number + "-S" + id++, number, SlotType.SMALL));
        for (int i = 0; i < medium; i++) slots.add(new ParkingSlot("F" + number + "-S" + id++, number, SlotType.MEDIUM));
        for (int i = 0; i < large; i++) slots.add(new ParkingSlot("F" + number + "-S" + id++, number, SlotType.LARGE));
    }
    int getNumber() { return number; }
    List<ParkingSlot> getSlots() { return Collections.unmodifiableList(slots); }
    long freeCount(SlotType t) { return slots.stream().filter(s -> s.getType() == t && s.isFree()).count(); }
}

class ParkingLot {
    private final String name;
    private final List<ParkingFloor> floors = new ArrayList<>();
    ParkingLot(String name) { this.name = name; }
    void addFloor(ParkingFloor f) { floors.add(f); }
    List<ParkingFloor> getFloors() { return Collections.unmodifiableList(floors); }
}

class Ticket {
    private final String id;
    private final Vehicle vehicle;
    private final ParkingSlot slot;
    private final long entryTime;
    Ticket(String id, Vehicle v, ParkingSlot s, long entryTime) {
        this.id = id; this.vehicle = v; this.slot = s; this.entryTime = entryTime;
    }
    String getId() { return id; }
    Vehicle getVehicle() { return vehicle; }
    ParkingSlot getSlot() { return slot; }
    long getEntryTime() { return entryTime; }
}

class ParkingFullException extends RuntimeException {
    ParkingFullException(VehicleType t) { super("No slot available for " + t); }
}
class InvalidTicketException extends RuntimeException {
    InvalidTicketException(String id) { super("Invalid ticket " + id); }
}
```

```java
interface SlotAllocationStrategy {
    Optional<ParkingSlot> find(List<ParkingFloor> floors, VehicleType type);
}

// Best fit: search every floor for the smallest fitting slot type before
// falling back to a bigger type, so LARGE slots stay free for trucks.
class BestFitStrategy implements SlotAllocationStrategy {
    public Optional<ParkingSlot> find(List<ParkingFloor> floors, VehicleType type) {
        for (SlotType st : type.allowedSlots())
            for (ParkingFloor f : floors)
                for (ParkingSlot s : f.getSlots())
                    if (s.getType() == st && s.isFree()) return Optional.of(s);
        return Optional.empty();
    }
}

interface PricingStrategy { double fee(Ticket t, long exitTime); }

class HourlyPricing implements PricingStrategy {
    private final Map<VehicleType, Double> ratePerHour = Map.of(
        VehicleType.BIKE, 20.0, VehicleType.CAR, 50.0, VehicleType.TRUCK, 100.0);
    public double fee(Ticket t, long exitTime) {
        long millis = Math.max(0, exitTime - t.getEntryTime());
        long hours = Math.max(1, (millis + 3_599_999) / 3_600_000);   // ceil, minimum 1 hour
        return hours * ratePerHour.get(t.getVehicle().getType());
    }
}

class ParkingService {
    private final ParkingLot lot;
    private final SlotAllocationStrategy allocation;
    private final PricingStrategy pricing;
    private final Map<String, Ticket> activeTickets = new ConcurrentHashMap<>();
    private int ticketSeq = 0;

    ParkingService(ParkingLot lot, SlotAllocationStrategy a, PricingStrategy p) {
        this.lot = lot; this.allocation = a; this.pricing = p;
    }

    public synchronized Ticket park(Vehicle v, long entryTime) {
        ParkingSlot slot = allocation.find(lot.getFloors(), v.getType())
            .orElseThrow(() -> new ParkingFullException(v.getType()));
        slot.occupy(v);
        Ticket t = new Ticket("T" + (++ticketSeq), v, slot, entryTime);
        activeTickets.put(t.getId(), t);
        return t;
    }

    public synchronized double unpark(String ticketId, long exitTime) {
        Ticket t = activeTickets.remove(ticketId);
        if (t == null) throw new InvalidTicketException(ticketId);
        t.getSlot().release();
        return pricing.fee(t, exitTime);
    }

    public void printAvailability() {
        for (ParkingFloor f : lot.getFloors()) {
            StringBuilder sb = new StringBuilder("Floor " + f.getNumber() + ": ");
            for (SlotType st : SlotType.values()) sb.append(st).append('=').append(f.freeCount(st)).append(' ');
            System.out.println(sb.toString().trim());
        }
    }
}

public class Main {
    public static void main(String[] args) {
        ParkingLot lot = new ParkingLot("Phoenix Mall");
        lot.addFloor(new ParkingFloor(0, 1, 1, 1));
        lot.addFloor(new ParkingFloor(1, 1, 2, 0));
        ParkingService svc = new ParkingService(lot, new BestFitStrategy(), new HourlyPricing());

        long now = 0;
        Ticket t1 = svc.park(new Vehicle("KA01AB1234", VehicleType.CAR), now);
        Ticket t2 = svc.park(new Vehicle("KA02CD5678", VehicleType.CAR), now);
        Ticket t3 = svc.park(new Vehicle("KA03EF9012", VehicleType.TRUCK), now);
        System.out.println(t1.getId() + " -> " + t1.getSlot().getId());
        System.out.println(t2.getId() + " -> " + t2.getSlot().getId());
        System.out.println(t3.getId() + " -> " + t3.getSlot().getId());
        try {
            svc.park(new Vehicle("KA04GH0000", VehicleType.TRUCK), now);
        } catch (ParkingFullException e) {
            System.out.println("Error: " + e.getMessage());
        }
        svc.printAvailability();
        double fee = svc.unpark(t1.getId(), now + 150 * 60 * 1000L); // 2.5 hours
        System.out.println("Fee for " + t1.getId() + " = " + fee);
        try { svc.unpark(t1.getId(), now); } catch (InvalidTicketException e) { System.out.println("Error: " + e.getMessage()); }
    }
}
```

With best-fit allocation the two cars take MEDIUM slots on floors 0 and 1, leaving floor 0's LARGE slot for the truck; the second truck is rejected with a clear error. A naive "lowest floor first" strategy would have put the second car in the LARGE slot and blocked the first truck. That trade-off is exactly what interviewers want you to discuss - and switching between the two is a one-line change in `Main` because allocation is a Strategy.

## Extension questions
1. **Multiple entry gates in parallel?** Replace the service-level `synchronized` with per-slot atomic `occupy()` (already returns `false` if lost) and retry allocation in a loop; or keep a `ConcurrentLinkedQueue` of free slots per type per floor and `poll()` atomically - O(1) allocation.
2. **O(1) free-slot lookup?** Maintain `Map<SlotType, TreeSet<ParkingSlot>>` (ordered by floor/distance) or a min-heap per gate.
3. **Electric charging slots?** Add `SlotType.EV` and update `VehicleType` mapping; pricing adds a charging component via a decorator on `PricingStrategy`.
4. **Payments?** `PaymentMethod` interface (UPI, card, cash) - Strategy again.
5. **Display boards per floor?** Observer: slots publish occupancy changes to `DisplayBoard` subscribers.
6. **Lost ticket?** Look up by vehicle number via `Map<String, Ticket>` and charge a maximum daily fee.
''',
["Typed slots and a VehicleType enum that lists allowed SlotTypes avoids scattered if/else.",
 "SlotAllocationStrategy and PricingStrategy are Strategy pattern hooks for changing business rules.",
 "ParkingService orchestrates; models stay simple; dependencies are injected via the constructor.",
 "Tickets map ticketId to vehicle, slot and entry time; unpark removes the ticket and frees the slot.",
 "Custom exceptions (ParkingFull, InvalidTicket) make failure paths explicit in the demo.",
 "Thread safety: synchronized service methods for simplicity, or atomic per-slot occupy plus free-slot queues for scale.",
 "Extensions like EV slots, display boards (Observer) and payment modes plug in without modifying core classes."],
[("How would you make slot allocation O(1) instead of scanning all slots?",
  r'''Maintain free slots in per-type data structures: for each `SlotType`, a `TreeSet` or `PriorityQueue` ordered by floor/distance from the gate (or a `ConcurrentLinkedDeque` if order does not matter). Parking polls the first free slot of the best allowed type; unparking adds the slot back. With a heap that is O(log n), with a queue O(1). This trades extra memory and bookkeeping for speed, and each structure must be updated atomically with the slot's state.'''),
 ("How do you handle two cars entering from different gates at the same time?",
  r'''The race is in find-then-occupy. Options: (1) synchronize `park()` - simple but serialises all gates; (2) make `ParkingSlot.occupy()` an atomic compare-and-set that returns `false` if someone else took it, and retry allocation on failure; (3) keep concurrent free-slot queues where `poll()` atomically hands a slot to exactly one gate. Option 3 gives the best throughput. Ticket IDs come from an `AtomicLong` and active tickets live in a `ConcurrentHashMap`.'''),
 ("Why use the Strategy pattern for pricing?",
  r'''Pricing rules change often and independently of parking logic: hourly, first-hour-free, weekend flat, peak surcharge, monthly passes. With `PricingStrategy`, `ParkingService` computes fees via an interface, and each rule is a separate, testable class. A new rule needs no change to existing code (OCP), and we can even pick a strategy at runtime based on day or customer. Rules can be combined using a decorator (e.g., `GstDecorator` wrapping any base strategy).'''),
 ("Should ParkingLot be a Singleton?",
  r'''Conceptually there is one lot per deployment, so Singleton is a common answer, and if used it should be thread-safe (holder idiom or enum). However, static singletons are global state and hard to test or extend to multiple lots. I prefer creating one instance in `Main` (or via a DI container) and passing it to services. If the interviewer insists, I would implement the holder idiom and mention the testability trade-off.''')],
[ALLD, {"title": "awesome-low-level-design - Parking Lot", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/parking-lot.md"}, RG]
))

topics.append(T(
"elevator-system", "Design an Elevator System", 2, "Advanced", 50,
"Design a multi-elevator controller that dispatches hall requests using a pluggable scheduling strategy and moves cars with the SCAN (elevator) algorithm.",
r'''
## Problem
A building has N floors and M elevators. Passengers press **hall buttons** (up/down on a floor) and **car buttons** (destination inside an elevator). The controller assigns hall requests to elevators and each elevator serves its stops efficiently.

## Requirements
**P0**
1. Accept external requests `(floor, direction)` and internal requests `(elevatorId, floor)`.
2. A dispatcher assigns each external request to the best elevator.
3. Each elevator moves one floor per tick, stops at requested floors, and keeps serving in its current direction before reversing (SCAN/LOOK).
4. Show each elevator's state: floor, direction, stops.

**P1:** capacity/weight limits, maintenance mode, door states, emergency stop, different dispatch strategies.

**Out of scope:** real hardware timing (we simulate with `step()` ticks).

## Entities
`Direction`, `ElevatorState` (IDLE, MOVING, MAINTENANCE), `Request`, `Elevator`, `DispatchStrategy`, `ElevatorController`, `Building`.

## Class diagram
```text
ElevatorController
  - elevators: List<Elevator>
  - strategy: DispatchStrategy
  + requestElevator(floor, dir)      (hall call)
  + selectFloor(elevatorId, floor)   (car call)
  + step()                           (advance simulation one tick)

Elevator
  - id, currentFloor, direction: Direction, state: ElevatorState
  - upStops: TreeSet<Integer>, downStops: TreeSet<Integer>
  + addStop(floor), step(), costTo(floor, dir)

<<interface>> DispatchStrategy  + select(elevators, floor, dir): Elevator
   ^.. NearestCarStrategy (direction-aware cost)

enum Direction { UP, DOWN, IDLE }
```

## Patterns used and why
- **Strategy** for dispatching: "nearest car", "least loaded", "zone-based" are all plausible interview follow-ups.
- **State** (light version via enum): behaviour differs in IDLE / MOVING / MAINTENANCE. A full State pattern with classes is a good extension when doors, emergency and maintenance are added.
- **Observer (extension):** floor displays subscribe to elevator position changes.
- **Two TreeSets per elevator** implement the LOOK algorithm cleanly: `upStops.ceiling(current)` gives the next stop above, `downStops.floor(current)` the next stop below.

## Java implementation
```java
import java.util.*;

enum Direction { UP, DOWN, IDLE }
enum ElevatorState { IDLE, MOVING, MAINTENANCE }

class Elevator {
    private final int id;
    private int currentFloor = 0;
    private Direction direction = Direction.IDLE;
    private ElevatorState state = ElevatorState.IDLE;
    private final TreeSet<Integer> upStops = new TreeSet<>();
    private final TreeSet<Integer> downStops = new TreeSet<>();

    Elevator(int id) { this.id = id; }

    int getId() { return id; }
    int getCurrentFloor() { return currentFloor; }
    Direction getDirection() { return direction; }
    ElevatorState getState() { return state; }
    void setMaintenance(boolean on) { state = on ? ElevatorState.MAINTENANCE : ElevatorState.IDLE; }

    synchronized void addStop(int floor) {
        if (floor == currentFloor && direction == Direction.IDLE) {
            System.out.println("  Elevator " + id + " opens doors at " + floor);
            return;
        }
        if (floor > currentFloor) upStops.add(floor); else if (floor < currentFloor) downStops.add(floor);
        else return;
        if (direction == Direction.IDLE) direction = floor > currentFloor ? Direction.UP : Direction.DOWN;
        state = ElevatorState.MOVING;
    }

    /** Lower cost = better candidate for a hall call. */
    int costTo(int floor, Direction reqDir) {
        int distance = Math.abs(currentFloor - floor);
        if (direction == Direction.IDLE) return distance;
        boolean onTheWay = (direction == Direction.UP && floor >= currentFloor && reqDir == Direction.UP)
                        || (direction == Direction.DOWN && floor <= currentFloor && reqDir == Direction.DOWN);
        int pending = upStops.size() + downStops.size();
        return onTheWay ? distance + pending : distance + 2 * 20 + pending; // penalise reversing
    }

    /** Move one floor (one simulation tick) using the LOOK algorithm. */
    synchronized void step() {
        if (state == ElevatorState.MAINTENANCE || direction == Direction.IDLE) return;
        currentFloor += (direction == Direction.UP) ? 1 : -1;
        TreeSet<Integer> stops = direction == Direction.UP ? upStops : downStops;
        if (stops.remove(currentFloor)) {
            System.out.println("  Elevator " + id + " stops at floor " + currentFloor);
        }
        if (direction == Direction.UP && upStops.isEmpty()) {
            direction = downStops.isEmpty() ? Direction.IDLE : Direction.DOWN;
        } else if (direction == Direction.DOWN && downStops.isEmpty()) {
            direction = upStops.isEmpty() ? Direction.IDLE : Direction.UP;
        }
        if (direction == Direction.IDLE) state = ElevatorState.IDLE;
    }

    @Override public String toString() {
        return "E" + id + "[floor=" + currentFloor + ", dir=" + direction + ", up=" + upStops + ", down=" + downStops + "]";
    }
}

interface DispatchStrategy {
    Elevator select(List<Elevator> elevators, int floor, Direction dir);
}

class NearestCarStrategy implements DispatchStrategy {
    public Elevator select(List<Elevator> elevators, int floor, Direction dir) {
        return elevators.stream()
            .filter(e -> e.getState() != ElevatorState.MAINTENANCE)
            .min(Comparator.comparingInt(e -> e.costTo(floor, dir)))
            .orElseThrow(() -> new IllegalStateException("No elevator available"));
    }
}
```

```java
class ElevatorController {
    private final List<Elevator> elevators = new ArrayList<>();
    private final DispatchStrategy strategy;
    private final int minFloor, maxFloor;

    ElevatorController(int count, int minFloor, int maxFloor, DispatchStrategy strategy) {
        for (int i = 1; i <= count; i++) elevators.add(new Elevator(i));
        this.minFloor = minFloor; this.maxFloor = maxFloor; this.strategy = strategy;
    }

    private void validate(int floor) {
        if (floor < minFloor || floor > maxFloor) throw new IllegalArgumentException("Invalid floor " + floor);
    }

    public Elevator requestElevator(int floor, Direction dir) {
        validate(floor);
        Elevator e = strategy.select(elevators, floor, dir);
        System.out.println("Hall call floor " + floor + " " + dir + " -> Elevator " + e.getId());
        e.addStop(floor);
        return e;
    }

    public void selectFloor(int elevatorId, int floor) {
        validate(floor);
        System.out.println("Car call in Elevator " + elevatorId + " -> floor " + floor);
        elevators.get(elevatorId - 1).addStop(floor);
    }

    public void step() { elevators.forEach(Elevator::step); }

    public void status() { elevators.forEach(e -> System.out.println("  " + e)); }

    public Elevator get(int id) { return elevators.get(id - 1); }
}

public class Main {
    public static void main(String[] args) {
        ElevatorController ctrl = new ElevatorController(2, 0, 10, new NearestCarStrategy());
        ctrl.requestElevator(5, Direction.UP);    // goes to E1 (both idle, tie -> first)
        ctrl.selectFloor(1, 8);                   // passenger wants 8
        for (int i = 0; i < 3; i++) ctrl.step();
        ctrl.requestElevator(2, Direction.DOWN);  // E1 is moving up away, so E2 is chosen
        ctrl.status();
        for (int i = 0; i < 6; i++) ctrl.step();
        ctrl.selectFloor(2, 0);
        ctrl.get(1).setMaintenance(true);
        for (int i = 0; i < 3; i++) ctrl.step();
        ctrl.status();
        try { ctrl.requestElevator(42, Direction.UP); } catch (IllegalArgumentException e) { System.out.println("Error: " + e.getMessage()); }
    }
}
```

## How the scheduling works
- **FCFS** (serve requests in arrival order) causes lots of back-and-forth.
- **SCAN** moves end to end like a disk head; **LOOK** (implemented here) reverses as soon as there are no more stops in the current direction.
- The dispatcher's cost function prefers an idle car or a car already moving toward the floor in the same direction, and penalises cars that would need to reverse.

## Extension questions
1. **Capacity:** track current load; `costTo` returns `Integer.MAX_VALUE` when full.
2. **Full State pattern:** `IdleState`, `MovingUpState`, `MovingDownState`, `DoorsOpenState`, `MaintenanceState`, each handling `step()` and `addStop()`.
3. **Real-time:** run each elevator in its own thread or a `ScheduledExecutorService` ticking every second; requests come through a `BlockingQueue`.
4. **Peak-hour strategy:** in the morning, park idle cars at the lobby (zone strategy).
5. **VIP / fire mode:** a priority request that clears other stops - Command objects in a priority queue.
''',
["Separate hall calls (floor + direction, dispatched) from car calls (destination inside a specific elevator).",
 "DispatchStrategy (Strategy pattern) picks the elevator; a cost function favours idle or on-the-way cars.",
 "Each elevator keeps upStops and downStops TreeSets to implement the LOOK algorithm efficiently.",
 "Simulate time with step() ticks so behaviour is deterministic and demoable in Main.",
 "Elevator state (IDLE, MOVING, MAINTENANCE) controls behaviour; upgrade to full State pattern when doors and emergencies are added.",
 "Validate floors and exclude maintenance cars in dispatch; synchronize per-elevator mutations.",
 "Discuss FCFS vs SCAN vs LOOK trade-offs and peak-hour or zone strategies as extensions."],
[("Which scheduling algorithm would you use for an elevator and why?",
  r'''LOOK, a refinement of SCAN: the car keeps moving in its current direction serving all stops on the way and reverses only when there are no more requests ahead. FCFS causes excessive travel and unfair waits; Shortest-Seek-First can starve far floors. LOOK bounds waiting time and minimises direction changes. Implementation: two sorted sets per elevator (`upStops`, `downStops`); `ceiling()` and `floor()` give the next stop in O(log n).'''),
 ("How does the controller choose which elevator serves a hall call?",
  r'''Through a pluggable `DispatchStrategy`. My default computes a cost per elevator: distance if idle; distance plus pending stops if the car is moving toward the floor in the requested direction; a large penalty if the car must first reverse. Elevators in maintenance or at full capacity are excluded. The minimum-cost car wins. Alternative strategies - least loaded, zone-based, or predictive for peak hours - can be swapped in without touching the controller.'''),
 ("How would you model door opening, closing and emergencies?",
  r'''With the State pattern. States such as `Idle`, `MovingUp`, `MovingDown`, `DoorsOpen`, `Maintenance` and `Emergency` implement a common interface with `onTick()`, `onRequest()`, `openDoor()` and `closeDoor()`. Each state decides legal actions and the next state: for example, `MovingUp` ignores `openDoor()`, and `Emergency` rejects new requests and moves to the nearest floor. This removes nested `if (state == ...)` checks from the `Elevator` class.'''),
 ("How do you make this work concurrently with real time?",
  r'''Each elevator runs its movement loop on a `ScheduledExecutorService` tick. Requests arrive from many threads, so `addStop` and `step` are synchronized per elevator (or use a lock), and the dispatcher reads elevator state under that lock or from a consistent snapshot. Requests can be submitted to a `BlockingQueue` that a dispatcher thread consumes, decoupling button presses from scheduling decisions.''')],
[ALLD, {"title": "awesome-low-level-design - Elevator System", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/elevator-system.md"},
 {"title": "Wikipedia - Elevator algorithm (SCAN)", "url": "https://en.wikipedia.org/wiki/Elevator_algorithm"}]
))

topics.append(T(
"splitwise", "Design Splitwise (Expense Sharing)", 3, "Intermediate", 50,
"A favourite Flipkart/PhonePe machine-coding problem: track shared expenses with equal, exact and percentage splits, maintain balances and simplify debts.",
r'''
## Problem
Users add expenses paid by one person and shared among several. The app tracks who owes whom and can show balances per user. Classic workat.tech command format:

```text
EXPENSE u1 1000 4 u1 u2 u3 u4 EQUAL
EXPENSE u1 1250 2 u2 u3 EXACT 370 880
EXPENSE u4 1200 4 u1 u2 u3 u4 PERCENT 40 20 20 20
SHOW
SHOW u1
```

## Requirements
**P0**
1. Users with id, name, email, phone.
2. Add expense: payer, amount, participants and split type `EQUAL`, `EXACT`, `PERCENT`.
3. Validate: exact amounts sum to total; percents sum to 100.
4. Show all non-zero balances, or balances of one user (`u2 owes u1: 250`).
5. Equal split rounding: 100 split 3 ways = 33.34, 33.33, 33.33 (first person absorbs remainder).

**P1:** groups, expense name/notes, passbook per user, simplify debts (minimise transactions), `SHARE` split type.

## Entities
`User`, `Expense`, `Split` (participant + amount), `SplitType`, `SplitStrategy`, `BalanceSheet`, `ExpenseService`.

## Class diagram
```text
User  - id, name, email

Expense - id, paidBy: User, amount, splits: List<Split>, type: SplitType
Split   - user: User, amount

<<interface>> SplitStrategy
  + split(amount, participants, values): List<Split>
  ^.. EqualSplit   ^.. ExactSplit   ^.. PercentSplit

SplitStrategyFactory  + get(SplitType): SplitStrategy

BalanceSheet
  - balances: Map<String, Map<String, Double>>   // balances[a][b] > 0 => b owes a
  + update(expense), show(), show(userId), simplify()

ExpenseService --> BalanceSheet, SplitStrategyFactory, Map<String, User>
```

## Patterns used and why
- **Strategy** for split types: each has its own computation and validation; adding `SHARE` (ratio-based) is a new class.
- **Factory** returns the right strategy from the parsed `SplitType`.
- **Balance sheet as nested map** gives O(1) update per participant, and keeps the invariant `balances[a][b] == -balances[b][a]`.
- **Money in paise (long)** avoids floating point errors - a detail interviewers love. We convert to rupees only for display.

## Java implementation
```java
import java.util.*;

class User {
    private final String id, name, email;
    User(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
    String getId() { return id; }
    String getName() { return name; }
}

enum SplitType { EQUAL, EXACT, PERCENT }

class Split {
    private final User user;
    private final long amountPaise;
    Split(User user, long amountPaise) { this.user = user; this.amountPaise = amountPaise; }
    User getUser() { return user; }
    long getAmount() { return amountPaise; }
}

class Expense {
    private final String id;
    private final User paidBy;
    private final long amountPaise;
    private final List<Split> splits;
    Expense(String id, User paidBy, long amountPaise, List<Split> splits) {
        this.id = id; this.paidBy = paidBy; this.amountPaise = amountPaise; this.splits = List.copyOf(splits);
    }
    User getPaidBy() { return paidBy; }
    List<Split> getSplits() { return splits; }
}

class InvalidSplitException extends RuntimeException {
    InvalidSplitException(String m) { super(m); }
}

interface SplitStrategy {
    List<Split> split(long totalPaise, List<User> users, List<Double> values);
}

class EqualSplit implements SplitStrategy {
    public List<Split> split(long total, List<User> users, List<Double> values) {
        long share = total / users.size();
        long remainder = total - share * users.size();
        List<Split> res = new ArrayList<>();
        for (int i = 0; i < users.size(); i++)
            res.add(new Split(users.get(i), share + (i == 0 ? remainder : 0)));  // first absorbs remainder
        return res;
    }
}

class ExactSplit implements SplitStrategy {
    public List<Split> split(long total, List<User> users, List<Double> values) {
        if (values.size() != users.size()) throw new InvalidSplitException("Need one amount per user");
        List<Split> res = new ArrayList<>();
        long sum = 0;
        for (int i = 0; i < users.size(); i++) {
            long p = Math.round(values.get(i) * 100);
            sum += p;
            res.add(new Split(users.get(i), p));
        }
        if (sum != total) throw new InvalidSplitException("Exact amounts do not add up to total");
        return res;
    }
}

class PercentSplit implements SplitStrategy {
    public List<Split> split(long total, List<User> users, List<Double> values) {
        if (values.size() != users.size()) throw new InvalidSplitException("Need one percent per user");
        double pctSum = values.stream().mapToDouble(Double::doubleValue).sum();
        if (Math.abs(pctSum - 100.0) > 1e-6) throw new InvalidSplitException("Percents must add to 100");
        List<Split> res = new ArrayList<>();
        long allocated = 0;
        for (int i = 0; i < users.size(); i++) {
            long p = (i == users.size() - 1) ? total - allocated : Math.round(total * values.get(i) / 100.0);
            allocated += p;
            res.add(new Split(users.get(i), p));
        }
        return res;
    }
}

class SplitStrategyFactory {
    private final Map<SplitType, SplitStrategy> map = new EnumMap<>(SplitType.class);
    SplitStrategyFactory() {
        map.put(SplitType.EQUAL, new EqualSplit());
        map.put(SplitType.EXACT, new ExactSplit());
        map.put(SplitType.PERCENT, new PercentSplit());
    }
    SplitStrategy get(SplitType t) { return map.get(t); }
}
```

```java
class BalanceSheet {
    // balances.get(a).get(b) > 0 means b owes a that much
    private final Map<String, Map<String, Long>> balances = new HashMap<>();

    void apply(Expense e) {
        String payer = e.getPaidBy().getId();
        for (Split s : e.getSplits()) {
            String debtor = s.getUser().getId();
            if (debtor.equals(payer)) continue;
            add(payer, debtor, s.getAmount());
            add(debtor, payer, -s.getAmount());
        }
    }

    private void add(String a, String b, long amt) {
        balances.computeIfAbsent(a, k -> new HashMap<>()).merge(b, amt, Long::sum);
    }

    List<String> show(String userId) {
        List<String> out = new ArrayList<>();
        Map<String, Long> m = balances.getOrDefault(userId, Map.of());
        for (Map.Entry<String, Long> en : new TreeMap<>(m).entrySet()) {
            long v = en.getValue();
            if (v > 0) out.add(en.getKey() + " owes " + userId + ": " + fmt(v));
            else if (v < 0) out.add(userId + " owes " + en.getKey() + ": " + fmt(-v));
        }
        return out;
    }

    List<String> showAll() {
        List<String> out = new ArrayList<>();
        for (String a : new TreeSet<>(balances.keySet()))
            for (Map.Entry<String, Long> en : new TreeMap<>(balances.get(a)).entrySet())
                if (en.getValue() > 0) out.add(en.getKey() + " owes " + a + ": " + fmt(en.getValue()));
        return out;
    }

    /** Minimise number of transactions using net balances + greedy max-creditor/max-debtor matching. */
    List<String> simplify() {
        Map<String, Long> net = new HashMap<>();
        for (String a : balances.keySet())
            for (long v : balances.get(a).values()) net.merge(a, v, Long::sum);
        PriorityQueue<Map.Entry<String, Long>> creditors = new PriorityQueue<>((x, y) -> Long.compare(y.getValue(), x.getValue()));
        PriorityQueue<Map.Entry<String, Long>> debtors = new PriorityQueue<>((x, y) -> Long.compare(x.getValue(), y.getValue()));
        for (Map.Entry<String, Long> e : net.entrySet()) {
            if (e.getValue() > 0) creditors.add(new AbstractMap.SimpleEntry<>(e));
            else if (e.getValue() < 0) debtors.add(new AbstractMap.SimpleEntry<>(e));
        }
        List<String> tx = new ArrayList<>();
        while (!creditors.isEmpty() && !debtors.isEmpty()) {
            Map.Entry<String, Long> c = creditors.poll(), d = debtors.poll();
            long amt = Math.min(c.getValue(), -d.getValue());
            tx.add(d.getKey() + " pays " + c.getKey() + ": " + fmt(amt));
            if (c.getValue() - amt > 0) creditors.add(new AbstractMap.SimpleEntry<>(c.getKey(), c.getValue() - amt));
            if (d.getValue() + amt < 0) debtors.add(new AbstractMap.SimpleEntry<>(d.getKey(), d.getValue() + amt));
        }
        return tx;
    }

    static String fmt(long paise) { return String.format("%.2f", paise / 100.0); }
}

class ExpenseService {
    private final Map<String, User> users = new HashMap<>();
    private final BalanceSheet sheet = new BalanceSheet();
    private final SplitStrategyFactory factory = new SplitStrategyFactory();
    private int seq = 0;

    void addUser(User u) { users.put(u.getId(), u); }

    private User user(String id) {
        User u = users.get(id);
        if (u == null) throw new IllegalArgumentException("Unknown user " + id);
        return u;
    }

    void addExpense(String payerId, double amount, List<String> participantIds, SplitType type, List<Double> values) {
        if (amount <= 0) throw new IllegalArgumentException("Amount must be positive");
        long total = Math.round(amount * 100);
        List<User> parts = new ArrayList<>();
        for (String id : participantIds) parts.add(user(id));
        List<Split> splits = factory.get(type).split(total, parts, values);
        sheet.apply(new Expense("E" + (++seq), user(payerId), total, splits));
    }

    BalanceSheet sheet() { return sheet; }
}

public class Main {
    static void print(List<String> lines) {
        if (lines.isEmpty()) System.out.println("No balances"); else lines.forEach(System.out::println);
    }
    public static void main(String[] args) {
        ExpenseService svc = new ExpenseService();
        for (int i = 1; i <= 4; i++) svc.addUser(new User("u" + i, "User" + i, "u" + i + "@mail.com"));

        print(svc.sheet().showAll());
        svc.addExpense("u1", 1000, List.of("u1", "u2", "u3", "u4"), SplitType.EQUAL, List.of());
        print(svc.sheet().show("u4"));
        svc.addExpense("u1", 1250, List.of("u2", "u3"), SplitType.EXACT, List.of(370.0, 880.0));
        svc.addExpense("u4", 1200, List.of("u1", "u2", "u3", "u4"), SplitType.PERCENT, List.of(40.0, 20.0, 20.0, 20.0));
        System.out.println("--- all ---");
        print(svc.sheet().showAll());
        System.out.println("--- simplified ---");
        print(svc.sheet().simplify());
        try {
            svc.addExpense("u1", 100, List.of("u2", "u3"), SplitType.EXACT, List.of(50.0, 40.0));
        } catch (InvalidSplitException e) { System.out.println("Error: " + e.getMessage()); }
    }
}
```

## Extension questions
1. **Groups:** `Group` with members and its own `BalanceSheet`; global view aggregates across groups.
2. **Simplify debts:** the greedy algorithm above reduces transactions to at most `n-1`; the true minimum is NP-hard (subset-sum flavour), so greedy is the accepted answer.
3. **Passbook / history:** store `List<Expense>` per user; show expenses involving them.
4. **Concurrency:** many users adding expenses at once - synchronize `BalanceSheet.apply()` or use `ConcurrentHashMap` with `merge` (atomic per key; both directions must update together, so a lock per user pair or a single lock is simpler).
5. **Settle up:** a `Payment` is just an expense with one participant paying the payer back.
''',
["Store money as long paise to avoid floating-point errors; format only for display.",
 "SplitStrategy (EQUAL, EXACT, PERCENT) plus a factory keyed by SplitType keeps split logic extensible.",
 "Each strategy validates its own input: exact amounts must sum to total, percents to 100.",
 "Handle rounding deterministically: one participant absorbs the remainder.",
 "BalanceSheet as Map<user, Map<user, amount>> updates both directions symmetrically in O(1) per participant.",
 "Debt simplification uses net balances and greedy matching of largest creditor and debtor.",
 "Groups, passbook, settle-up and concurrency are the standard follow-ups."],
[("How do you simplify debts in Splitwise?",
  r'''Compute each user's **net balance** (total owed to them minus total they owe). Users with positive net are creditors, negative are debtors. Repeatedly match the largest creditor with the largest debtor (two heaps), transfer `min(credit, -debt)`, and push back any remainder. This needs at most n-1 transactions and runs in O(n log n). Finding the absolute minimum number of transactions is NP-hard, so the greedy approach is the standard practical answer.'''),
 ("Why should you not use double for money?",
  r'''Binary floating point cannot represent most decimal fractions exactly, so `0.1 + 0.2` is `0.30000000000000004`, and errors accumulate across many expenses, causing balances that do not net to zero. Use integer minor units (`long` paise) or `BigDecimal` with an explicit `RoundingMode`. In machine coding, `long` paise is simpler and faster; convert to rupees only for display.'''),
 ("How do you handle 100 split equally among 3 people?",
  r'''Integer division gives 3333 paise each with 1 paise remainder. Assign the remainder deterministically, typically to the first participant (or the payer), giving 33.34, 33.33, 33.33. The key requirement is that the splits always sum exactly to the total, so balances stay consistent. The same idea applies to percent splits: compute all but the last participant by rounding and give the last one `total - allocated`.'''),
 ("How would you add a new split type like SHARE (ratio-based)?",
  r'''Create `ShareSplit implements SplitStrategy` that takes share counts, computes `total * share / sumShares` for each participant with remainder handling, and validates that shares are positive. Register it in the factory under `SplitType.SHARE` and extend the parser. No changes to `BalanceSheet`, `Expense` or other strategies are needed - that is the Open/Closed benefit of the Strategy pattern.''')],
[{"title": "workat.tech - Splitwise Machine Coding Problem", "url": "https://workat.tech/machine-coding/practice/splitwise-problem-0kp2yneec2q2"}, ALLD,
 {"title": "awesome-low-level-design - Splitwise", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/splitwise.md"}]
))

topics.append(T(
"bookmyshow-lld", "Design BookMyShow (Movie Ticket Booking)", 4, "Advanced", 55,
"Design a movie ticket booking system with cities, theatres, shows and seats, focusing on preventing double booking with seat locks and timeouts.",
r'''
## Problem
Users browse movies in a city, pick a show at a theatre, select seats and pay. The core challenge interviewers probe: **two users selecting the same seat at the same time.**

## Requirements
**P0**
1. Admin adds cities, theatres (with screens), movies and shows (movie + screen + start time).
2. Users search shows by city and movie.
3. View available seats for a show.
4. Book multiple seats: seats are **temporarily locked** for the user during payment (e.g., 5 min); confirm on payment success, release on failure/timeout.
5. No double booking under concurrency.

**P1:** seat categories with different prices, cancellation/refund, coupons, notifications.

## Entities
`City`, `Theatre`, `Screen`, `Seat` (`SeatCategory`), `Movie`, `Show`, `Booking` (`BookingStatus`), `SeatLockProvider`, `PaymentService`, `BookingService`, `ShowService`.

## Class diagram
```text
Theatre 1 *-- * Screen 1 *-- * Seat(id, row, category)
Show --> Movie, --> Screen, startTime
Booking - id, show, seats, user, status (PENDING/CONFIRMED/CANCELLED), amount

<<interface>> SeatLockProvider
  + lock(show, seats, user): boolean
  + unlock(show, seats, user)
  + isLockedByOther(show, seat, user): boolean
  ^.. InMemorySeatLockProvider (ConcurrentHashMap + expiry)

BookingService
  - bookings: Map<String, Booking>
  - lockProvider: SeatLockProvider
  + createBooking(user, show, seats): Booking     // locks seats -> PENDING
  + confirm(bookingId, paymentOk)                  // CONFIRMED or release
  + availableSeats(show): List<Seat>

PricingStrategy (by SeatCategory)
```

## Patterns used and why
- **Strategy** for seat locking (`SeatLockProvider`): in-memory for the interview, Redis/DB-backed in production - the booking flow does not change.
- **Strategy** for pricing per seat category / time of day.
- **State** via `BookingStatus` enum transitions: `PENDING -> CONFIRMED | EXPIRED | CANCELLED`.
- **Observer (extension):** notify users on confirmation, or wait-listed users when seats free up.
- **Facade:** a `BookingService` exposes a simple API over locks, payment and booking storage.

## Concurrency approach
The lock step must be **all-or-nothing** for multiple seats. The in-memory provider synchronizes on the show while checking all seats and then locking them all, so two users cannot both partially succeed. Locks carry an expiry timestamp so abandoned payments free seats automatically. In production: a unique constraint on `(show_id, seat_id)` in a `booked_seats` table or Redis `SET key value NX PX 300000` per seat.

## Java implementation
```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

enum SeatCategory { SILVER, GOLD, PLATINUM }
enum BookingStatus { PENDING, CONFIRMED, CANCELLED, EXPIRED }

class Seat {
    final String id; final SeatCategory category;
    Seat(String id, SeatCategory c) { this.id = id; this.category = c; }
    public String toString() { return id; }
}

class Screen {
    final String id; final List<Seat> seats = new ArrayList<>();
    Screen(String id) { this.id = id; }
}

class Theatre {
    final String id, name, city; final List<Screen> screens = new ArrayList<>();
    Theatre(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

class Movie {
    final String id, title; final int durationMin;
    Movie(String id, String title, int d) { this.id = id; this.title = title; this.durationMin = d; }
}

class Show {
    final String id; final Movie movie; final Screen screen; final Theatre theatre; final long startTime;
    Show(String id, Movie m, Theatre t, Screen s, long start) {
        this.id = id; this.movie = m; this.theatre = t; this.screen = s; this.startTime = start;
    }
}

class Booking {
    final String id, userId; final Show show; final List<Seat> seats; final double amount;
    BookingStatus status = BookingStatus.PENDING;
    Booking(String id, String userId, Show show, List<Seat> seats, double amount) {
        this.id = id; this.userId = userId; this.show = show; this.seats = seats; this.amount = amount;
    }
}

class SeatUnavailableException extends RuntimeException {
    SeatUnavailableException(String m) { super(m); }
}

interface SeatLockProvider {
    boolean lock(Show show, List<Seat> seats, String userId);
    void unlock(Show show, List<Seat> seats, String userId);
    boolean isLocked(Show show, Seat seat);
}

class InMemorySeatLockProvider implements SeatLockProvider {
    private record Lock(String userId, long expiresAt) { }
    private final Map<String, Map<String, Lock>> locks = new ConcurrentHashMap<>(); // showId -> seatId -> lock
    private final long ttlMillis;
    InMemorySeatLockProvider(long ttlMillis) { this.ttlMillis = ttlMillis; }

    public boolean lock(Show show, List<Seat> seats, String userId) {
        Map<String, Lock> showLocks = locks.computeIfAbsent(show.id, k -> new HashMap<>());
        synchronized (showLocks) {                       // all-or-nothing for this show
            long now = System.currentTimeMillis();
            for (Seat s : seats) {
                Lock l = showLocks.get(s.id);
                if (l != null && l.expiresAt() > now && !l.userId().equals(userId)) return false;
            }
            for (Seat s : seats) showLocks.put(s.id, new Lock(userId, now + ttlMillis));
            return true;
        }
    }

    public void unlock(Show show, List<Seat> seats, String userId) {
        Map<String, Lock> showLocks = locks.get(show.id);
        if (showLocks == null) return;
        synchronized (showLocks) {
            for (Seat s : seats) {
                Lock l = showLocks.get(s.id);
                if (l != null && l.userId().equals(userId)) showLocks.remove(s.id);
            }
        }
    }

    public boolean isLocked(Show show, Seat seat) {
        Map<String, Lock> showLocks = locks.get(show.id);
        if (showLocks == null) return false;
        synchronized (showLocks) {
            Lock l = showLocks.get(seat.id);
            return l != null && l.expiresAt() > System.currentTimeMillis();
        }
    }
}

interface PricingStrategy { double price(Seat seat, Show show); }
class CategoryPricing implements PricingStrategy {
    private final Map<SeatCategory, Double> base = Map.of(
        SeatCategory.SILVER, 150.0, SeatCategory.GOLD, 250.0, SeatCategory.PLATINUM, 400.0);
    public double price(Seat seat, Show show) { return base.get(seat.category); }
}
```

```java
class BookingService {
    private final Map<String, Booking> bookings = new ConcurrentHashMap<>();
    private final Map<String, Set<String>> bookedSeats = new ConcurrentHashMap<>(); // showId -> seatIds
    private final SeatLockProvider lockProvider;
    private final PricingStrategy pricing;
    private int seq = 0;

    BookingService(SeatLockProvider lp, PricingStrategy p) { this.lockProvider = lp; this.pricing = p; }

    private Set<String> booked(Show s) { return bookedSeats.computeIfAbsent(s.id, k -> ConcurrentHashMap.newKeySet()); }

    public List<Seat> availableSeats(Show show) {
        return show.screen.seats.stream()
            .filter(s -> !booked(show).contains(s.id) && !lockProvider.isLocked(show, s))
            .collect(Collectors.toList());
    }

    public synchronized Booking createBooking(String userId, Show show, List<Seat> seats) {
        for (Seat s : seats)
            if (booked(show).contains(s.id)) throw new SeatUnavailableException("Seat " + s.id + " already booked");
        if (!lockProvider.lock(show, seats, userId))
            throw new SeatUnavailableException("Seats " + seats + " are being booked by someone else");
        double amount = seats.stream().mapToDouble(s -> pricing.price(s, show)).sum();
        Booking b = new Booking("B" + (++seq), userId, show, seats, amount);
        bookings.put(b.id, b);
        return b;
    }

    public synchronized void confirm(String bookingId, boolean paymentSuccess) {
        Booking b = bookings.get(bookingId);
        if (b == null || b.status != BookingStatus.PENDING) throw new IllegalStateException("Booking not pending");
        if (paymentSuccess) {
            b.seats.forEach(s -> booked(b.show).add(s.id));
            b.status = BookingStatus.CONFIRMED;
        } else {
            b.status = BookingStatus.CANCELLED;
        }
        lockProvider.unlock(b.show, b.seats, b.userId);
    }
}

class ShowService {
    private final List<Show> shows = new ArrayList<>();
    void add(Show s) { shows.add(s); }
    List<Show> search(String city, String movieTitle) {
        return shows.stream()
            .filter(s -> s.theatre.city.equalsIgnoreCase(city) && s.movie.title.equalsIgnoreCase(movieTitle))
            .collect(Collectors.toList());
    }
}

public class Main {
    public static void main(String[] args) throws Exception {
        Theatre pvr = new Theatre("T1", "PVR Forum", "Bengaluru");
        Screen screen = new Screen("SCR1");
        for (int i = 1; i <= 3; i++) screen.seats.add(new Seat("A" + i, SeatCategory.SILVER));
        for (int i = 1; i <= 2; i++) screen.seats.add(new Seat("P" + i, SeatCategory.PLATINUM));
        pvr.screens.add(screen);
        Movie movie = new Movie("M1", "Interstellar", 169);
        ShowService shows = new ShowService();
        shows.add(new Show("S1", movie, pvr, screen, System.currentTimeMillis() + 3_600_000));

        BookingService svc = new BookingService(new InMemorySeatLockProvider(5 * 60 * 1000), new CategoryPricing());
        Show show = shows.search("bengaluru", "interstellar").get(0);
        System.out.println("Available: " + svc.availableSeats(show));

        // Two users race for seats A1, P1
        List<Seat> wanted = List.of(screen.seats.get(0), screen.seats.get(3));
        ExecutorService pool = Executors.newFixedThreadPool(2);
        Callable<String> attempt1 = () -> tryBook(svc, "alice", show, wanted);
        Callable<String> attempt2 = () -> tryBook(svc, "bob", show, wanted);
        List<Future<String>> results = pool.invokeAll(List.of(attempt1, attempt2));
        for (Future<String> f : results) System.out.println(f.get());
        pool.shutdown();
        System.out.println("Available now: " + svc.availableSeats(show));
    }

    static String tryBook(BookingService svc, String user, Show show, List<Seat> seats) {
        try {
            Booking b = svc.createBooking(user, show, seats);
            svc.confirm(b.id, true);
            return user + " booked " + b.seats + " for Rs " + b.amount + " -> " + b.status;
        } catch (SeatUnavailableException e) {
            return user + " failed: " + e.getMessage();
        }
    }
}
```

Exactly one of Alice or Bob succeeds; the other gets a clear error, and the confirmed seats disappear from availability.

## Extension questions
1. **Lock expiry cleanup:** a `ScheduledExecutorService` scans expired locks and marks related `PENDING` bookings as `EXPIRED`.
2. **Distributed deployment:** move locks to Redis (`SET NX PX`) or rely on a DB unique index on `(show_id, seat_id)`; optimistic locking with a version column on the show-seat row.
3. **Scaling reads:** cache seat maps per show; invalidate on booking events.
4. **Cancellation & refunds:** `CONFIRMED -> CANCELLED`, release seats, `RefundPolicy` strategy based on time to show.
5. **Waitlist notifications:** Observer on seat release events.
6. **Payment integration:** `PaymentGateway` interface with adapters for Razorpay/PayU; idempotency key per booking.
''',
["Model City/Theatre/Screen/Seat/Movie/Show/Booking; a Show binds a movie to a screen at a time.",
 "Book in two phases: lock seats (PENDING) then confirm on payment success or release on failure/timeout.",
 "Seat locking must be all-or-nothing across multiple seats to avoid partial bookings.",
 "Locks carry an expiry so abandoned checkouts free seats automatically.",
 "SeatLockProvider interface lets in-memory locks be swapped for Redis or DB constraints in production.",
 "Pricing per seat category is a Strategy; booking status transitions model the lifecycle.",
 "Production safety nets: DB unique constraint on (show, seat), optimistic locking, idempotent payments."],
[("How do you prevent double booking of the same seat?",
  r'''Two layers. First, a temporary **seat lock** taken atomically for all requested seats when the user proceeds to pay: in-memory with a synchronized check-then-lock per show, or in Redis with `SET seatKey user NX PX 300000`. Second, a **final guarantee** at confirmation: a database unique constraint on `(show_id, seat_id)` in the booked-seats table, or optimistic locking with a version column, so even if locks fail only one insert succeeds. Losers get a clear "seat unavailable" error.'''),
 ("Why do seat locks need a timeout?",
  r'''Users abandon payment, close the app or lose connectivity. Without expiry, those seats stay locked forever and the show looks sold out. A TTL (typically 5-10 minutes) automatically frees them. Expiry is checked lazily on every availability query and actively by a scheduled cleanup job that also moves the related bookings from `PENDING` to `EXPIRED`. If payment succeeds after expiry, the system must re-verify seat availability or refund.'''),
 ("How would you scale this to millions of users on a blockbuster release?",
  r'''Cache show listings and seat maps (read-heavy) with short TTLs or event-based invalidation. Shard booking data by show id so locks for a show live on one partition. Use Redis for seat locks for low latency, and a queue/virtual waiting room to throttle traffic spikes. Keep payment asynchronous with idempotency keys and confirm via webhooks. The DB unique constraint stays as the correctness backstop.'''),
 ("Which design patterns did you use and why?",
  r'''Strategy for `SeatLockProvider` (in-memory vs distributed) and `PricingStrategy` (category, weekend or dynamic pricing). A State-like lifecycle for `Booking` (`PENDING -> CONFIRMED / CANCELLED / EXPIRED`) with guarded transitions. Facade: `BookingService` hides locking, pricing and persistence behind `createBooking` and `confirm`. Observer as an extension for notifications and waitlists. Each pattern isolates something likely to change.''')],
[ALLD, {"title": "awesome-low-level-design - Movie Ticket Booking System", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/movie-ticket-booking-system.md"},
 {"title": "Redis docs - SET with NX and PX options", "url": "https://redis.io/docs/latest/commands/set/"}]
))

save("p1", "problems", topics)
