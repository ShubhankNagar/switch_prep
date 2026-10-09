from lld_common import *

topics = []

topics.append(T(
"inventory-order-management", "Design an Inventory & Order Management System", 16, "Advanced", 50,
"An e-commerce core (Flipkart/Amazon style): products, warehouse inventory with reservations, cart, order lifecycle with State transitions, payment and Observer notifications.",
r'''
## Problem
Design the backend core of an e-commerce platform: sellers add products and stock per warehouse; customers add items to a cart and place orders; inventory must never oversell; orders move through a lifecycle; stakeholders get notified.

## Requirements
**P0**
1. Product catalogue (id, name, price) and stock per warehouse.
2. Cart: add/remove items, compute total.
3. Place order: **reserve** stock atomically for all items (all-or-nothing), then pay; on success **commit** (deduct), on failure **release**.
4. Order lifecycle: `CREATED -> PAID -> SHIPPED -> DELIVERED`, cancellation allowed before shipping (stock returned).
5. Notify customer on status changes; alert when stock drops below a threshold.
6. Concurrent orders for the last unit: exactly one succeeds.

**P1:** multiple warehouses with nearest-warehouse selection, coupons, returns/refunds, partial shipments.

## Entities
`Product`, `InventoryItem` (available + reserved), `Warehouse`, `InventoryService`, `Cart`, `CartItem`, `Order`, `OrderItem`, `OrderStatus`, `PaymentGateway`, `OrderService`, `OrderObserver`.

## Class diagram
```text
Product      - id, name, price (paise)
InventoryItem- productId, available, reserved, lowStockThreshold
               + reserve(q), release(q), commit(q)    (synchronized)
InventoryService
  - items: ConcurrentHashMap<productId, InventoryItem>
  + reserveAll(Map<productId, qty>): boolean   (all-or-nothing, ordered locking)
  + releaseAll(...), commitAll(...)

Cart - userId, items: Map<productId, qty>   + add, remove, total(catalog)
Order - id, userId, items: List<OrderItem>, amount, status: OrderStatus
        + transitionTo(next)  (validated by OrderStatus.canMoveTo)

<<interface>> PaymentGateway   + pay(orderId, amount): boolean   ^.. FakeGateway
<<interface>> OrderObserver    + onStatusChange(order, old, new)  ^.. CustomerNotifier, ^.. AnalyticsObserver
<<interface>> StockObserver    + onLowStock(productId, available)

OrderService (facade)
  + placeOrder(cart): Order
  + ship(orderId), deliver(orderId), cancel(orderId)
```

## Key design decisions
- **Reserve-then-commit** (two-phase) prevents overselling while payment is in progress, and lets failures roll back cleanly.
- **All-or-nothing across items:** lock inventory items in a **consistent order (sorted product id)** to avoid deadlocks when two carts contain the same products in different orders; roll back partial reservations on failure.
- **Order status as an enum with allowed transitions** - a lightweight State pattern; illegal transitions throw.
- **Observers** decouple notifications/analytics/low-stock alerts from core logic.
- **Money in paise** (long) to avoid floating point errors.

## Java implementation
```java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

record Product(String id, String name, long price) { }

class InventoryItem {
    final String productId; private int available, reserved; final int lowStockThreshold;
    InventoryItem(String productId, int available, int threshold) { this.productId = productId; this.available = available; this.lowStockThreshold = threshold; }
    boolean tryReserve(int q) { if (available < q) return false; available -= q; reserved += q; return true; }
    void release(int q) { reserved -= q; available += q; }
    void commit(int q) { reserved -= q; }
    void restock(int q) { available += q; }
    int available() { return available; }
}

interface StockObserver { void onLowStock(String productId, int available); }

class InventoryService {
    private final Map<String, InventoryItem> items = new ConcurrentHashMap<>();
    private final List<StockObserver> observers = new CopyOnWriteArrayList<>();

    void addStock(String productId, int qty, int threshold) {
        items.computeIfAbsent(productId, k -> new InventoryItem(k, 0, threshold));
        InventoryItem it = items.get(productId);
        synchronized (it) { it.restock(qty); }
    }
    void addObserver(StockObserver o) { observers.add(o); }
    int available(String pid) { InventoryItem it = items.get(pid); synchronized (it) { return it.available(); } }

    /** All-or-nothing reservation. Locks items in sorted order to avoid deadlock. */
    boolean reserveAll(Map<String, Integer> req) {
        List<String> ids = new ArrayList<>(new TreeSet<>(req.keySet()));
        return reserveRec(ids, 0, req);
    }
    private boolean reserveRec(List<String> ids, int i, Map<String, Integer> req) {
        if (i == ids.size()) return true;
        InventoryItem it = items.get(ids.get(i));
        if (it == null) return false;
        synchronized (it) {                             // nested locks, acquired in sorted order
            if (!it.tryReserve(req.get(it.productId))) return false;
            if (reserveRec(ids, i + 1, req)) return true;
            it.release(req.get(it.productId));          // roll back this one if later items failed
            return false;
        }
    }
    void releaseAll(Map<String, Integer> req) {
        req.forEach((pid, q) -> { InventoryItem it = items.get(pid); synchronized (it) { it.release(q); } });
    }
    void commitAll(Map<String, Integer> req) {
        req.forEach((pid, q) -> {
            InventoryItem it = items.get(pid);
            int left;
            synchronized (it) { it.commit(q); left = it.available(); }
            if (left <= it.lowStockThreshold) observers.forEach(o -> o.onLowStock(pid, left));
        });
    }
}

class Cart {
    final String userId; final Map<String, Integer> items = new LinkedHashMap<>();
    Cart(String userId) { this.userId = userId; }
    Cart add(String pid, int q) { if (q <= 0) throw new IllegalArgumentException("qty > 0"); items.merge(pid, q, Integer::sum); return this; }
    void remove(String pid) { items.remove(pid); }
}

enum OrderStatus {
    CREATED, PAID, SHIPPED, DELIVERED, CANCELLED, PAYMENT_FAILED;
    boolean canMoveTo(OrderStatus next) {
        return switch (this) {
            case CREATED -> next == PAID || next == PAYMENT_FAILED || next == CANCELLED;
            case PAID -> next == SHIPPED || next == CANCELLED;
            case SHIPPED -> next == DELIVERED;
            default -> false;                            // terminal states
        };
    }
}

record OrderItem(String productId, int qty, long unitPrice) { }

class Order {
    final String id, userId; final List<OrderItem> items; final long amount;
    private OrderStatus status = OrderStatus.CREATED;
    Order(String id, String userId, List<OrderItem> items) {
        this.id = id; this.userId = userId; this.items = List.copyOf(items);
        this.amount = items.stream().mapToLong(i -> i.qty() * i.unitPrice()).sum();
    }
    OrderStatus status() { return status; }
    synchronized OrderStatus transitionTo(OrderStatus next) {
        if (!status.canMoveTo(next)) throw new IllegalStateException("Order " + id + ": " + status + " -> " + next + " not allowed");
        OrderStatus old = status; status = next; return old;
    }
    Map<String, Integer> quantities() {
        Map<String, Integer> m = new HashMap<>();
        items.forEach(i -> m.merge(i.productId(), i.qty(), Integer::sum));
        return m;
    }
}
```

```java
interface PaymentGateway { boolean pay(String orderId, long amount); }
interface OrderObserver { void onStatusChange(Order o, OrderStatus from, OrderStatus to); }

class OutOfStockException extends RuntimeException { OutOfStockException(String m) { super(m); } }

class OrderService {
    private final Map<String, Product> catalog;
    private final InventoryService inventory;
    private final PaymentGateway payments;
    private final List<OrderObserver> observers = new CopyOnWriteArrayList<>();
    private final Map<String, Order> orders = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong();

    OrderService(Map<String, Product> catalog, InventoryService inv, PaymentGateway pg) { this.catalog = catalog; inventory = inv; payments = pg; }
    void addObserver(OrderObserver o) { observers.add(o); }

    Order placeOrder(Cart cart) {
        if (cart.items.isEmpty()) throw new IllegalArgumentException("Cart is empty");
        List<OrderItem> items = new ArrayList<>();
        cart.items.forEach((pid, q) -> items.add(new OrderItem(pid, q, catalog.get(pid).price())));
        Order order = new Order("O" + seq.incrementAndGet(), cart.userId, items);
        Map<String, Integer> qty = order.quantities();

        if (!inventory.reserveAll(qty)) throw new OutOfStockException("Insufficient stock for order of " + cart.userId);
        orders.put(order.id, order);
        if (payments.pay(order.id, order.amount)) {
            inventory.commitAll(qty);
            move(order, OrderStatus.PAID);
        } else {
            inventory.releaseAll(qty);
            move(order, OrderStatus.PAYMENT_FAILED);
        }
        cart.items.clear();
        return order;
    }

    void ship(String id) { move(get(id), OrderStatus.SHIPPED); }
    void deliver(String id) { move(get(id), OrderStatus.DELIVERED); }

    void cancel(String id) {
        Order o = get(id);
        move(o, OrderStatus.CANCELLED);
        o.quantities().forEach((pid, q) -> inventory.addStock(pid, q, 0));   // return stock (and refund in real life)
    }

    private void move(Order o, OrderStatus to) {
        OrderStatus from = o.transitionTo(to);
        observers.forEach(obs -> obs.onStatusChange(o, from, to));
    }
    private Order get(String id) {
        Order o = orders.get(id);
        if (o == null) throw new IllegalArgumentException("No order " + id);
        return o;
    }
}

public class Main {
    public static void main(String[] args) throws Exception {
        Map<String, Product> catalog = Map.of(
            "P1", new Product("P1", "iPhone", 7_999_900),
            "P2", new Product("P2", "Case", 49_900));
        InventoryService inv = new InventoryService();
        inv.addStock("P1", 1, 0);
        inv.addStock("P2", 10, 3);
        inv.addObserver((pid, left) -> System.out.println("  [ALERT] low stock " + pid + " left=" + left));

        PaymentGateway pg = (orderId, amount) -> !orderId.equals("O99");   // fake: everything succeeds except O99
        OrderService svc = new OrderService(catalog, inv, pg);
        svc.addObserver((o, from, to) -> System.out.println("  [notify " + o.userId + "] " + o.id + " " + from + " -> " + to));

        // Two users race for the single iPhone
        ExecutorService pool = Executors.newFixedThreadPool(2);
        List<Future<String>> res = new ArrayList<>();
        for (String user : List.of("raj", "anu")) {
            res.add(pool.submit(() -> {
                try { return user + ": " + svc.placeOrder(new Cart(user).add("P1", 1).add("P2", 2)).id; }
                catch (OutOfStockException e) { return user + ": " + e.getMessage(); }
            }));
        }
        for (Future<String> f : res) System.out.println(f.get());
        pool.shutdown();
        System.out.println("iPhone left=" + inv.available("P1") + ", cases left=" + inv.available("P2"));

        Order o2 = svc.placeOrder(new Cart("meera").add("P2", 5));
        svc.ship(o2.id);
        try { svc.cancel(o2.id); } catch (IllegalStateException e) { System.out.println("Error: " + e.getMessage()); }
        svc.deliver(o2.id);
        Order o3 = svc.placeOrder(new Cart("dev").add("P2", 1));
        svc.cancel(o3.id);
        System.out.println("cases left after cancel=" + inv.available("P2"));
    }
}
```

## Extension questions
1. **Multiple warehouses:** `WarehouseSelectionStrategy` (nearest with full stock, or split shipments); inventory keyed by `(warehouseId, productId)`.
2. **Reservation expiry:** if payment is asynchronous, reservations carry a TTL and a scheduler releases them (like seat locks).
3. **Distributed inventory:** atomic SQL `UPDATE inventory SET available = available - ? WHERE product_id = ? AND available >= ?` (check affected rows), or Redis `DECRBY` with Lua; flash sales use pre-allocated tokens and queues.
4. **Saga for microservices:** order, inventory and payment services coordinate via events with compensating actions (release stock, refund).
5. **Coupons/pricing:** `DiscountRule` chain (Chain of Responsibility) or Strategy composed into the cart total.
''',
["Reserve stock first, then pay; commit on success, release on failure (two-phase, no overselling).",
 "Reserve all cart items all-or-nothing, locking items in sorted product-id order to avoid deadlocks.",
 "Order status enum with canMoveTo encodes the lifecycle; illegal transitions throw.",
 "Observers handle customer notifications, analytics and low-stock alerts without coupling to core logic.",
 "OrderService is a Facade over catalog, inventory, payment and observers.",
 "Store prices in paise (long) and snapshot unit prices into OrderItems at order time.",
 "At scale: conditional SQL updates or Redis atomic ops for stock, and Sagas with compensations across services."],
[("How do you prevent overselling when many users order the last unit simultaneously?",
  r'''Make the check-and-decrement atomic. In-memory, each inventory item is locked while checking `available >= qty` and moving units to `reserved`; only one thread can take the last unit. Across multiple items, I lock in a sorted order and roll back partial reservations. In a database, a conditional update - `UPDATE inventory SET available = available - 1 WHERE id = ? AND available >= 1` - succeeds for exactly one transaction (check affected rows). Flash sales add Redis counters and queues in front.'''),
 ("Why reserve inventory before payment instead of deducting directly?",
  r'''Payment takes time and can fail. Deducting only after payment risks selling the same unit twice; deducting before payment and failing leaves inventory wrong unless carefully reverted. Reservation moves units from `available` to `reserved`: other buyers cannot take them, and the outcome is explicit - commit on success, release on failure or timeout. Reservations with expiry also protect against abandoned checkouts.'''),
 ("How do you model the order lifecycle?",
  r'''As a state machine. I use an `OrderStatus` enum where each state declares its allowed next states (`CREATED -> PAID | PAYMENT_FAILED | CANCELLED`, `PAID -> SHIPPED | CANCELLED`, `SHIPPED -> DELIVERED`). `Order.transitionTo` validates and records the change, then observers are notified. If states gain rich behaviour (refund rules, SLA timers), I would upgrade to full State pattern classes. Persisting each transition gives an audit trail.'''),
 ("How would this work across microservices (order, inventory, payment)?",
  r'''Distributed transactions with 2PC are avoided; instead use a **Saga**. The order service creates a PENDING order and emits an event; inventory reserves stock and emits StockReserved or StockFailed; payment charges and emits PaymentDone or PaymentFailed. Each failure triggers compensating actions (release stock, cancel order, refund). Use the outbox pattern for reliable event publishing and idempotent consumers to handle duplicate events.''')],
[ALLD, {"title": "microservices.io - Saga pattern", "url": "https://microservices.io/patterns/data/saga.html"},
 {"title": "Refactoring.Guru - Observer", "url": "https://refactoring.guru/design-patterns/observer"}]
))

topics.append(T(
"cab-booking-lld", "Design a Cab Booking System (Uber/Ola LLD)", 17, "Advanced", 50,
"Design ride booking with riders, drivers, location-based driver matching, ride lifecycle, fare strategies and concurrency-safe driver assignment.",
r'''
## Problem
Design the core of a ride-hailing app: riders request a ride from a pickup to a drop location; the system finds a nearby available driver, the driver's state changes, the ride goes through its lifecycle, and the fare is calculated at the end.

## Requirements
**P0**
1. Register riders and drivers (vehicle type: MINI, SEDAN, SUV); drivers update location and go online/offline.
2. Rider requests a ride with pickup, drop and vehicle type.
3. Match the nearest available driver of that type within a radius (pluggable matching strategy).
4. Ride lifecycle: `REQUESTED -> ACCEPTED -> STARTED -> COMPLETED`, or `CANCELLED` before start.
5. Fare = base + per-km x distance (by vehicle type), with surge multiplier (pluggable).
6. A driver can never be assigned to two rides at once (concurrent requests).

**P1:** ratings, ride history, driver acceptance/rejection with fallback to next driver, ETA, payment methods, scheduled rides.

## Entities
`Location`, `Rider`, `Driver` (`DriverStatus`), `VehicleType`, `Ride` (`RideStatus`), `DriverMatchingStrategy`, `FareStrategy`, `RideService`, `DriverRepository`.

## Class diagram
```text
Location (record) - lat, lng   + distanceKm(other)  (Haversine)
Rider  - id, name
Driver - id, name, vehicleType, location, status: AVAILABLE/ON_TRIP/OFFLINE
         + tryAssign(): boolean   (atomic AVAILABLE -> ON_TRIP)
Ride   - id, rider, driver, pickup, drop, type, status, fare

<<interface>> DriverMatchingStrategy
  + match(candidates, pickup, type): List<Driver>   (ordered best first)
   ^.. NearestDriverStrategy(radiusKm)   ^.. HighestRatedStrategy

<<interface>> FareStrategy  + fare(ride): long
   ^.. StandardFare   ^.. SurgeFare (decorates another FareStrategy)

RideService
  - drivers, rides, matching, fareStrategy
  + requestRide(riderId, pickup, drop, type): Ride
  + startRide(id), completeRide(id), cancelRide(id)
```

## Patterns used and why
- **Strategy** for matching and fare: matching logic (nearest, rating, ETA via maps API) and pricing change constantly.
- **Decorator** for surge: `SurgeFare` wraps any base fare strategy and multiplies it - stackable with promotions.
- **State-like lifecycle** for `Ride` via guarded transitions; `Driver` availability via atomic compare-and-set.
- **Observer (extension)** for pushing ride updates to rider and driver apps.

## Concurrency
Two riders requesting at the same moment may both see the same nearest driver. The fix: matching returns an **ordered candidate list**, and assignment uses an **atomic `compareAndSet(AVAILABLE, ON_TRIP)`** on the driver's status. The loser simply tries the next candidate. No global lock is needed.

## Finding nearby drivers at scale
A linear scan is fine for an interview demo. In production, index driver locations with a **geospatial index**: geohash prefixes, a quadtree, or Uber's H3 hexagonal grid. Query the rider's cell and neighbouring cells, then rank the few candidates by actual road ETA.

## Java implementation
```java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.stream.*;

record Location(double lat, double lng) {
    double distanceKm(Location o) {                     // Haversine formula
        double R = 6371, dLat = Math.toRadians(o.lat - lat), dLng = Math.toRadians(o.lng - lng);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                 + Math.cos(Math.toRadians(lat)) * Math.cos(Math.toRadians(o.lat)) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
        return 2 * R * Math.asin(Math.sqrt(a));
    }
}

enum VehicleType {
    MINI(50, 12), SEDAN(80, 16), SUV(120, 22);
    final long base, perKm;
    VehicleType(long base, long perKm) { this.base = base; this.perKm = perKm; }
}
enum DriverStatus { AVAILABLE, ON_TRIP, OFFLINE }
enum RideStatus { REQUESTED, ACCEPTED, STARTED, COMPLETED, CANCELLED }

record Rider(String id, String name) { }

class Driver {
    final String id, name; final VehicleType type;
    private volatile Location location;
    private final AtomicReference<DriverStatus> status = new AtomicReference<>(DriverStatus.OFFLINE);
    Driver(String id, String name, VehicleType type, Location loc) { this.id = id; this.name = name; this.type = type; this.location = loc; }
    Location location() { return location; }
    void updateLocation(Location l) { location = l; }
    DriverStatus status() { return status.get(); }
    void goOnline() { status.compareAndSet(DriverStatus.OFFLINE, DriverStatus.AVAILABLE); }
    boolean tryAssign() { return status.compareAndSet(DriverStatus.AVAILABLE, DriverStatus.ON_TRIP); }
    void release() { status.set(DriverStatus.AVAILABLE); }
}

class Ride {
    final String id; final Rider rider; final Driver driver; final Location pickup, drop; final VehicleType type;
    private RideStatus status = RideStatus.ACCEPTED; long fare;
    Ride(String id, Rider r, Driver d, Location p, Location dr, VehicleType t) { this.id = id; rider = r; driver = d; pickup = p; drop = dr; type = t; }
    RideStatus status() { return status; }
    synchronized void transition(RideStatus from, RideStatus to) {
        if (status != from) throw new IllegalStateException("Ride " + id + " is " + status + ", cannot go to " + to);
        status = to;
    }
    double distanceKm() { return pickup.distanceKm(drop); }
}

interface DriverMatchingStrategy { List<Driver> match(Collection<Driver> drivers, Location pickup, VehicleType type); }

class NearestDriverStrategy implements DriverMatchingStrategy {
    private final double radiusKm;
    NearestDriverStrategy(double radiusKm) { this.radiusKm = radiusKm; }
    public List<Driver> match(Collection<Driver> drivers, Location pickup, VehicleType type) {
        return drivers.stream()
            .filter(d -> d.type == type && d.status() == DriverStatus.AVAILABLE)
            .filter(d -> d.location().distanceKm(pickup) <= radiusKm)
            .sorted(Comparator.comparingDouble(d -> d.location().distanceKm(pickup)))
            .collect(Collectors.toList());
    }
}

interface FareStrategy { long fare(Ride r); }

class StandardFare implements FareStrategy {
    public long fare(Ride r) { return r.type.base + Math.round(r.type.perKm * r.distanceKm()); }
}

class SurgeFare implements FareStrategy {                 // Decorator
    private final FareStrategy inner; private final double multiplier;
    SurgeFare(FareStrategy inner, double multiplier) { this.inner = inner; this.multiplier = multiplier; }
    public long fare(Ride r) { return Math.round(inner.fare(r) * multiplier); }
}

class NoDriverAvailableException extends RuntimeException { NoDriverAvailableException(String m) { super(m); } }
```

```java
class RideService {
    private final Map<String, Driver> drivers = new ConcurrentHashMap<>();
    private final Map<String, Rider> riders = new ConcurrentHashMap<>();
    private final Map<String, Ride> rides = new ConcurrentHashMap<>();
    private final DriverMatchingStrategy matching;
    private volatile FareStrategy fareStrategy;
    private final AtomicLong seq = new AtomicLong();

    RideService(DriverMatchingStrategy m, FareStrategy f) { matching = m; fareStrategy = f; }
    void setFareStrategy(FareStrategy f) { fareStrategy = f; }
    void addDriver(Driver d) { drivers.put(d.id, d); d.goOnline(); }
    void addRider(Rider r) { riders.put(r.id(), r); }

    Ride requestRide(String riderId, Location pickup, Location drop, VehicleType type) {
        Rider rider = riders.get(riderId);
        if (rider == null) throw new IllegalArgumentException("Unknown rider " + riderId);
        for (Driver d : matching.match(drivers.values(), pickup, type)) {
            if (d.tryAssign()) {                          // atomic; loser tries next candidate
                Ride ride = new Ride("R" + seq.incrementAndGet(), rider, d, pickup, drop, type);
                rides.put(ride.id, ride);
                return ride;
            }
        }
        throw new NoDriverAvailableException("No " + type + " driver near pickup for " + rider.name());
    }

    void startRide(String id) { get(id).transition(RideStatus.ACCEPTED, RideStatus.STARTED); }

    long completeRide(String id) {
        Ride r = get(id);
        r.transition(RideStatus.STARTED, RideStatus.COMPLETED);
        r.fare = fareStrategy.fare(r);
        r.driver.updateLocation(r.drop);
        r.driver.release();
        return r.fare;
    }

    void cancelRide(String id) {
        Ride r = get(id);
        r.transition(RideStatus.ACCEPTED, RideStatus.CANCELLED);
        r.driver.release();
    }

    private Ride get(String id) {
        Ride r = rides.get(id);
        if (r == null) throw new IllegalArgumentException("No ride " + id);
        return r;
    }
}

public class Main {
    public static void main(String[] args) throws Exception {
        RideService svc = new RideService(new NearestDriverStrategy(5.0), new StandardFare());
        Location koramangala = new Location(12.9352, 77.6245), hsr = new Location(12.9116, 77.6474),
                 indiranagar = new Location(12.9784, 77.6408), whitefield = new Location(12.9698, 77.7500);
        svc.addDriver(new Driver("d1", "Ravi", VehicleType.SEDAN, new Location(12.9360, 77.6250)));
        svc.addDriver(new Driver("d2", "Suresh", VehicleType.SEDAN, new Location(12.9300, 77.6300)));
        svc.addDriver(new Driver("d3", "Kiran", VehicleType.SUV, whitefield));
        for (String r : List.of("raj", "anu", "dev")) svc.addRider(new Rider(r, r.toUpperCase()));

        // Three riders request SEDANs at the same time; only two sedans exist
        ExecutorService pool = Executors.newFixedThreadPool(3);
        List<Future<String>> out = new ArrayList<>();
        for (String r : List.of("raj", "anu", "dev")) out.add(pool.submit(() -> {
            try { Ride ride = svc.requestRide(r, koramangala, indiranagar, VehicleType.SEDAN); return r + " -> " + ride.id + " with " + ride.driver.name; }
            catch (NoDriverAvailableException e) { return r + " -> " + e.getMessage(); }
        }));
        for (Future<String> f : out) System.out.println(f.get());
        pool.shutdown();

        try { svc.requestRide("raj", koramangala, hsr, VehicleType.SUV); }
        catch (NoDriverAvailableException e) { System.out.println(e.getMessage() + " (SUV is ~13 km away)"); }

        Ride r1 = svc.requestRide("raj", whitefield, indiranagar, VehicleType.SUV);
        svc.startRide(r1.id);
        System.out.printf("Ride %s distance %.1f km, fare Rs %d%n", r1.id, r1.distanceKm(), svc.completeRide(r1.id));

        svc.setFareStrategy(new SurgeFare(new StandardFare(), 1.5));   // peak hours
        Ride r2 = svc.requestRide("dev", indiranagar, koramangala, VehicleType.SUV);
        svc.startRide(r2.id);
        System.out.println("Surge fare Rs " + svc.completeRide(r2.id));
        try { svc.cancelRide(r2.id); } catch (IllegalStateException e) { System.out.println("Error: " + e.getMessage()); }
    }
}
```

## Extension questions
1. **Driver accept/reject:** send offers to candidates one by one with a timeout (e.g., 15s) via a scheduled executor; on reject/timeout move to the next driver.
2. **Geospatial index:** replace the linear scan with a geohash/quadtree index updated on location pings (every 4-5 s).
3. **Surge pricing:** compute per-zone demand/supply ratio; `SurgeFare` reads the multiplier for the pickup zone.
4. **Ride sharing (pool):** match riders with overlapping routes; capacity per vehicle.
5. **Payments, ratings, history:** `PaymentStrategy`, rating aggregates on driver/rider, ride repository queries.
6. **Scale:** location updates through a stream (Kafka) to a location service; matching service reads the in-memory geo index sharded by city.
''',
["Driver availability is assigned atomically with compareAndSet(AVAILABLE, ON_TRIP); losers try the next candidate.",
 "Matching returns an ordered candidate list from a pluggable DriverMatchingStrategy (nearest, rating, ETA).",
 "Fare is a Strategy; surge pricing is a Decorator wrapping any base fare.",
 "Ride lifecycle transitions are guarded: ACCEPTED -> STARTED -> COMPLETED, or CANCELLED before start.",
 "Haversine distance is fine for demos; production uses geohash, quadtrees or H3 plus road ETA.",
 "Releasing the driver and updating their location happen on completion or cancellation.",
 "Extensions: accept/reject with timeouts, pooling, per-zone surge, location streaming."],
[("How do you ensure a driver is not assigned to two riders at once?",
  r'''Driver status is an `AtomicReference<DriverStatus>`; assignment calls `compareAndSet(AVAILABLE, ON_TRIP)`, which succeeds for exactly one thread. Matching returns a ranked list of candidates, and each request walks the list until a CAS succeeds or the list is exhausted. There is no global lock, so unrelated requests proceed in parallel. In a distributed system the same idea becomes a conditional update in the database or a Redis `SET driver:lock NX` with TTL.'''),
 ("How would you find nearby drivers efficiently for millions of drivers?",
  r'''Use a spatial index instead of scanning. Geohash encodes lat/long into a string where shared prefixes mean proximity; store drivers in buckets by geohash cell and query the rider's cell plus its 8 neighbours. Alternatives: quadtrees (adaptive cell sizes for dense cities) or Uber's H3 hexagonal grid. Drivers send location pings every few seconds, updating their cell. Candidates are then ranked by road ETA from a routing service rather than straight-line distance.'''),
 ("Why model surge pricing as a Decorator?",
  r'''Surge multiplies whatever the base fare is, independent of how the base is calculated (per km, per minute, flat airport fare). As a decorator implementing `FareStrategy`, `SurgeFare` wraps any base strategy and can be combined with others, such as a `PromoDiscount` decorator, in any order. The ride service still calls `fareStrategy.fare(ride)` and does not know whether surge applies. Adding or removing surge is a configuration change.'''),
 ("How would you implement drivers accepting or rejecting ride offers?",
  r'''After matching, the ride enters a `SEARCHING` state and the system offers it to the best candidate, tentatively reserving them with the CAS. A scheduled task times out the offer after N seconds. On accept, the ride moves to `ACCEPTED`; on reject or timeout, the driver is released and the next candidate is offered the ride. After exhausting candidates or a global timeout, the ride is cancelled with "no drivers". Offer events are pushed to driver apps via WebSockets or push notifications.''')],
[ALLD, {"title": "Uber Engineering - H3: Uber's Hexagonal Hierarchical Spatial Index", "url": "https://www.uber.com/blog/h3/"},
 {"title": "Wikipedia - Haversine formula", "url": "https://en.wikipedia.org/wiki/Haversine_formula"}]
))

topics.append(T(
"in-memory-key-value-store", "Design an In-Memory Key-Value Store", 18, "Advanced", 45,
"A Redis-like in-memory store with typed attribute values, TTL expiry, secondary-index search, transactions and thread safety - a popular machine-coding problem.",
r'''
## Problem
Build an in-memory key-value store. A well-known machine-coding variant (workat.tech) stores, for each key, a set of **attributes** (`name -> value`) with types inferred on first use; you can `get`, `put`, `delete`, and `search` keys by attribute value. Interviewers then add TTL, transactions and concurrency.

## Requirements
**P0**
1. `put(key, List<Pair<attribute, value>>)` - values are String, Integer, Double or Boolean.
2. **Type consistency:** an attribute's type is fixed the first time it is seen (`age` as Integer); later puts with a different type fail.
3. `get(key)` returns attributes; `delete(key)`.
4. `search(attribute, value)` returns all keys whose attribute equals value - efficiently (secondary index).
5. `keys()` lists all keys.
6. Thread-safe for concurrent clients.

**P1:** TTL per key with expiry, transactions (`begin/commit/rollback`), persistence snapshot, eviction under memory pressure.

## Entities
`AttributeType`, `Value` (typed wrapper), `Entry` (attributes + expiry), `TypeRegistry`, `SecondaryIndex`, `KVStore` (interface), `InMemoryKVStore`, `Transaction`.

## Class diagram
```text
<<interface>> KVStore
  + put(key, attrs, ttlMs?)  + get(key)  + delete(key)  + search(attr, value)  + keys()

InMemoryKVStore implements KVStore
  - data: Map<String, Entry>
  - types: TypeRegistry               (attribute -> AttributeType, fixed on first use)
  - index: Map<attr, Map<value, Set<key>>>
  - lock: ReentrantReadWriteLock
  - sweeper: ScheduledExecutorService (expires TTL keys)

Entry - attributes: Map<String, Object>, expiresAt (Long.MAX_VALUE if none)
TypeRegistry + validate(attr, value)  (putIfAbsent)
Transaction  - writes buffer: Map<key, attrs or TOMBSTONE>  + commit(), rollback()
```

## Design decisions
- **Secondary index** `attr -> value -> keys` makes `search` O(1) to locate matching keys, at the cost of updating the index on every put/delete.
- **Read-write lock:** many concurrent `get`/`search` readers, exclusive writers - good for read-heavy workloads. Index and data must change together, so they share one lock (a `ConcurrentHashMap` alone cannot keep them consistent).
- **TTL with lazy + active expiry** (the Redis approach): check expiry on read; a background sweeper removes expired keys periodically so unread keys do not leak memory.
- **Transactions** buffer writes locally and apply them atomically under the write lock on commit.
- **Clock injection** for deterministic TTL tests.

## Java implementation
```java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.locks.*;
import java.util.function.LongSupplier;

enum AttributeType {
    STRING, INTEGER, DOUBLE, BOOLEAN;
    static AttributeType of(Object v) {
        if (v instanceof String) return STRING;
        if (v instanceof Integer) return INTEGER;
        if (v instanceof Double) return DOUBLE;
        if (v instanceof Boolean) return BOOLEAN;
        throw new IllegalArgumentException("Unsupported type " + v.getClass());
    }
}

class TypeMismatchException extends RuntimeException { TypeMismatchException(String m) { super(m); } }

class Entry {
    final Map<String, Object> attributes; final long expiresAt;
    Entry(Map<String, Object> attrs, long expiresAt) { attributes = Map.copyOf(attrs); this.expiresAt = expiresAt; }
    boolean expired(long now) { return now >= expiresAt; }
}

interface KVStore {
    void put(String key, Map<String, Object> attrs, long ttlMs);
    Optional<Map<String, Object>> get(String key);
    boolean delete(String key);
    List<String> search(String attr, Object value);
    List<String> keys();
}

class InMemoryKVStore implements KVStore {
    private final Map<String, Entry> data = new HashMap<>();
    private final Map<String, AttributeType> types = new ConcurrentHashMap<>();
    private final Map<String, Map<Object, Set<String>>> index = new HashMap<>();
    private final ReentrantReadWriteLock rw = new ReentrantReadWriteLock();
    private final LongSupplier clock;
    private final ScheduledExecutorService sweeper = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "ttl-sweeper"); t.setDaemon(true); return t; });

    InMemoryKVStore(LongSupplier clock, long sweepEveryMs) {
        this.clock = clock;
        sweeper.scheduleAtFixedRate(this::sweep, sweepEveryMs, sweepEveryMs, TimeUnit.MILLISECONDS);
    }

    private void validateTypes(Map<String, Object> attrs) {
        for (Map.Entry<String, Object> a : attrs.entrySet()) {
            AttributeType t = AttributeType.of(a.getValue());
            AttributeType existing = types.putIfAbsent(a.getKey(), t);   // fixed on first use
            if (existing != null && existing != t)
                throw new TypeMismatchException("Attribute '" + a.getKey() + "' is " + existing + ", got " + t);
        }
    }

    public void put(String key, Map<String, Object> attrs, long ttlMs) {
        validateTypes(attrs);
        long expiresAt = ttlMs <= 0 ? Long.MAX_VALUE : clock.getAsLong() + ttlMs;
        rw.writeLock().lock();
        try { putUnlocked(key, attrs, expiresAt); } finally { rw.writeLock().unlock(); }
    }

    // caller holds write lock
    void putUnlocked(String key, Map<String, Object> attrs, long expiresAt) {
        removeUnlocked(key);
        data.put(key, new Entry(attrs, expiresAt));
        attrs.forEach((a, v) -> index.computeIfAbsent(a, k -> new HashMap<>()).computeIfAbsent(v, k -> new HashSet<>()).add(key));
    }

    // caller holds write lock
    boolean removeUnlocked(String key) {
        Entry old = data.remove(key);
        if (old == null) return false;
        old.attributes.forEach((a, v) -> {
            Map<Object, Set<String>> byVal = index.get(a);
            Set<String> ks = byVal.get(v);
            ks.remove(key);
            if (ks.isEmpty()) byVal.remove(v);
        });
        return true;
    }

    public Optional<Map<String, Object>> get(String key) {
        rw.readLock().lock();
        try {
            Entry e = data.get(key);
            if (e == null || e.expired(clock.getAsLong())) return Optional.empty();   // lazy expiry on read
            return Optional.of(e.attributes);
        } finally { rw.readLock().unlock(); }
    }

    public boolean delete(String key) {
        rw.writeLock().lock();
        try { return removeUnlocked(key); } finally { rw.writeLock().unlock(); }
    }

    public List<String> search(String attr, Object value) {
        rw.readLock().lock();
        try {
            long now = clock.getAsLong();
            Set<String> ks = index.getOrDefault(attr, Map.of()).getOrDefault(value, Set.of());
            List<String> out = new ArrayList<>();
            for (String k : ks) if (!data.get(k).expired(now)) out.add(k);
            Collections.sort(out);
            return out;
        } finally { rw.readLock().unlock(); }
    }

    public List<String> keys() {
        rw.readLock().lock();
        try {
            long now = clock.getAsLong();
            List<String> out = new ArrayList<>();
            data.forEach((k, e) -> { if (!e.expired(now)) out.add(k); });
            Collections.sort(out);
            return out;
        } finally { rw.readLock().unlock(); }
    }

    void sweep() {                                        // active expiry
        rw.writeLock().lock();
        try {
            long now = clock.getAsLong();
            List<String> dead = new ArrayList<>();
            data.forEach((k, e) -> { if (e.expired(now)) dead.add(k); });
            dead.forEach(this::removeUnlocked);
            if (!dead.isEmpty()) System.out.println("  [sweeper] expired " + dead);
        } finally { rw.writeLock().unlock(); }
    }

    Lock writeLock() { return rw.writeLock(); }
    void validate(Map<String, Object> attrs) { validateTypes(attrs); }
    void shutdown() { sweeper.shutdownNow(); }
}
```

```java
/** Buffers writes; applies them atomically on commit. */
class Transaction {
    private static final Map<String, Object> TOMBSTONE = Map.of();
    private final InMemoryKVStore store;
    private final Map<String, Map<String, Object>> writes = new LinkedHashMap<>();
    private boolean open = true;
    Transaction(InMemoryKVStore store) { this.store = store; }

    void put(String key, Map<String, Object> attrs) { check(); store.validate(attrs); writes.put(key, attrs); }
    void delete(String key) { check(); writes.put(key, TOMBSTONE); }
    Optional<Map<String, Object>> get(String key) {          // read-your-own-writes
        check();
        if (writes.containsKey(key)) return writes.get(key) == TOMBSTONE ? Optional.empty() : Optional.of(writes.get(key));
        return store.get(key);
    }
    void commit() {
        check();
        store.writeLock().lock();
        try {
            writes.forEach((k, v) -> { if (v == TOMBSTONE) store.removeUnlocked(k); else store.putUnlocked(k, v, Long.MAX_VALUE); });
        } finally { store.writeLock().unlock(); open = false; }
    }
    void rollback() { writes.clear(); open = false; }
    private void check() { if (!open) throw new IllegalStateException("Transaction closed"); }
}

public class Main {
    public static void main(String[] args) throws Exception {
        long[] now = {0};                                     // fake clock
        InMemoryKVStore kv = new InMemoryKVStore(() -> now[0], 50);

        kv.put("sde_bootcamp", Map.of("title", "SDE-Bootcamp", "price", 30000.0, "enrolled", false, "estimated_time", 30), 0);
        kv.put("sde_kickstart", Map.of("title", "SDE-Kickstart", "price", 4000.0, "enrolled", true, "estimated_time", 8), 0);
        kv.put("sde_mock", Map.of("title", "SDE-Mock", "price", 1000.0, "enrolled", true), 0);
        System.out.println("get sde_kickstart -> " + new TreeMap<>(kv.get("sde_kickstart").get()));
        System.out.println("search enrolled=true -> " + kv.search("enrolled", true));
        try { kv.put("bad", Map.of("price", "free"), 0); } catch (TypeMismatchException e) { System.out.println("Error: " + e.getMessage()); }

        kv.put("otp:raj", Map.of("code", 4821), 1000);       // TTL 1s
        System.out.println("keys -> " + kv.keys());
        now[0] = 1500;                                       // advance fake time
        System.out.println("get otp:raj after 1.5s -> " + kv.get("otp:raj"));
        Thread.sleep(120);                                   // let the sweeper run

        Transaction tx = new Transaction(kv);
        tx.put("sde_mock", Map.of("title", "SDE-Mock v2", "price", 1500.0, "enrolled", false));
        tx.delete("sde_kickstart");
        System.out.println("inside tx, kickstart -> " + tx.get("sde_kickstart") + ", outside -> " + kv.get("sde_kickstart").isPresent());
        tx.commit();
        System.out.println("after commit keys -> " + kv.keys() + ", enrolled=true -> " + kv.search("enrolled", true));

        Transaction tx2 = new Transaction(kv);
        tx2.delete("sde_bootcamp");
        tx2.rollback();
        System.out.println("after rollback keys -> " + kv.keys());

        // concurrent writers
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int i = 0; i < 100; i++) { final int n = i; pool.submit(() -> kv.put("user" + n, Map.of("active", n % 2 == 0), 0)); }
        pool.shutdown(); pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("active users -> " + kv.search("active", true).size());
        kv.shutdown();
    }
}
```

## Extension questions
1. **Eviction (maxmemory):** combine with an LRU policy (see the LRU cache topic) - evict least recently used keys when the count exceeds a limit.
2. **Persistence:** append-only log of write commands (like Redis AOF) replayed on startup, plus periodic snapshots (RDB).
3. **Higher concurrency:** shard the store into N segments by key hash, each with its own lock and index; a search fans out across shards.
4. **Isolation for transactions:** current design gives atomic commit but no conflict detection; add optimistic concurrency with per-key versions checked at commit (abort on conflict).
5. **Range queries:** use a `TreeMap` index for numeric attributes (`price between 1000 and 5000`).
6. **Distributed:** consistent hashing for partitioning, leader-follower replication, and a quorum or Raft for consistency.
''',
["Fix each attribute's type on first use with ConcurrentHashMap.putIfAbsent and reject later mismatches.",
 "A secondary index attr -> value -> keys makes search fast but must be updated on every put and delete.",
 "Data and index change together, so guard both with one ReentrantReadWriteLock (many readers, one writer).",
 "TTL uses lazy expiry on reads plus an active background sweeper, like Redis.",
 "Transactions buffer writes (with tombstones for deletes) and apply them atomically under the write lock.",
 "Inject a clock so TTL behaviour is testable without sleeping.",
 "Scale via sharding by key hash; persistence via append-only logs and snapshots."],
[("How does your design support fast search by attribute value?",
  r'''I maintain a secondary (inverted) index: `Map<attribute, Map<value, Set<key>>>`. On `put`, I first remove the key's old attributes from the index, then add the new ones; on `delete`, I remove them. `search(attr, value)` is then two hash lookups plus copying the matching keys, instead of scanning every entry. The trade-off is extra memory and write cost, which is acceptable for read-heavy workloads. Index and data are updated under the same write lock to stay consistent.'''),
 ("Why a ReadWriteLock instead of ConcurrentHashMap?",
  r'''A `ConcurrentHashMap` makes single-map operations thread-safe, but a put here touches several structures - the data map and multiple index buckets - which must change atomically together, otherwise a concurrent search could see a key in the index whose data is gone. A `ReentrantReadWriteLock` lets many readers (`get`, `search`) run in parallel while writers get exclusive access. For heavy write throughput, I would shard the store so each shard has its own lock.'''),
 ("How do you implement key expiry (TTL)?",
  r'''Each entry stores an absolute `expiresAt`. **Lazy expiry**: every read checks it and treats expired keys as absent. **Active expiry**: a `ScheduledExecutorService` periodically removes expired keys so keys that are never read again do not leak memory. Redis does both, and its active cycle samples random keys to bound CPU. Alternatively, keep a min-heap or `TreeMap` of expiry times to remove only the keys that are due.'''),
 ("How would you implement transactions with rollback?",
  r'''A transaction keeps a private write buffer: puts store the new attributes, deletes store a tombstone. Reads inside the transaction check the buffer first (read-your-own-writes) and fall back to the store. `commit` acquires the store's write lock and applies all buffered operations at once, so other clients see all or none of them; `rollback` simply discards the buffer. For isolation against concurrent writers, record key versions at read time and abort the commit if any changed (optimistic concurrency control).''')],
[{"title": "workat.tech - Key-Value Store Machine Coding Problem", "url": "https://workat.tech/machine-coding/practice/design-key-value-store-6gz6cq124k65"},
 {"title": "Redis docs - EXPIRE (how Redis expires keys)", "url": "https://redis.io/docs/latest/commands/expire/"},
 {"title": "Java SE Docs - ReentrantReadWriteLock", "url": "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html"}]
))

save("p5", "problems", topics)
