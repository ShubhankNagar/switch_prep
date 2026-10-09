"""JPA / Hibernate traps (Hibernate 6 / Spring Data JPA 3 behaviour)."""
from traps1_common import T

A = "jpa-hibernate"

TRAPS = [
T("trap-jpa-hibernate-n-plus-one", A, "The N+1 select problem", "Intermediate", "Very common",
r"""
This endpoint is slow in production. Without looking at the logs, what's your guess? How would you confirm it, and
how would you fix it?

```java
@Entity
public class Order {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @ManyToOne(fetch = FetchType.LAZY) private Customer customer;
    @OneToMany(mappedBy = "order") private List<OrderItem> items;
}

@Transactional(readOnly = true)
public List<OrderSummary> recentOrders() {
    return orderRepository.findTop50ByOrderByIdDesc().stream()
            .map(o -> new OrderSummary(o.getId(), o.getCustomer().getName(), o.getItems().size()))
            .toList();
}
```
""",
None, None,
"Add an index, or switch the associations to FetchType.EAGER.",
r"""
The code looks like one query, and in dev with five rows it's fast. Candidates don't see that every
`getCustomer().getName()` and `getItems().size()` on a lazy association silently fires its own SELECT. EAGER sounds
like the fix, but it changes *when* the extra queries run, not *how many* there are.
""",
r"""
This is the **N+1 select problem**. One query loads 50 orders, then each lazy access triggers another query: up to 50
customer SELECTs (fewer if orders share customers, since the persistence context caches each customer) plus 50 item
SELECTs. That's around 101 round trips instead of one or two.

Confirm it with SQL logging or statistics (`spring.jpa.properties.hibernate.generate_statistics=true`, or a datasource
proxy that counts queries), and assert query counts in a test. Fixes depend on the situation: `JOIN FETCH` or
`@EntityGraph` loads what this use case needs in one query; batch fetching (`hibernate.default_batch_fetch_size=50`)
turns N queries into a few `IN (...)` queries; a DTO projection selects exactly the columns you need, which is best for
read-only list endpoints. Switching to EAGER makes it worse, because every query that loads orders now pays for
customers, everywhere.
""",
r"""
```java
// 1) Fetch what this use case needs, in one query
@EntityGraph(attributePaths = "customer")
List<Order> findTop50ByOrderByIdDesc();

// 2) Or a DTO projection: one query, only the columns you need
@Query("select new com.shop.OrderSummary(o.id, c.name, count(i)) " +
       "from Order o join o.customer c left join o.items i " +
       "group by o.id, c.name order by o.id desc")
List<OrderSummary> findSummaries(Pageable page);
```

```yaml
# 3) Safety net for the remaining lazy loads: batch them into IN (...) queries
spring:
  jpa:
    properties:
      hibernate.default_batch_fetch_size: 50
```
""",
"Say how you'd *prove* it (a query-count assertion in a test, or Hibernate statistics). Measuring before fixing is what interviewers look for.",
["Synechron"]),

T("trap-jpa-hibernate-lazy-initialization", A, "LazyInitializationException and the wrong fixes", "Intermediate", "Very common",
r"""
What happens when this job runs, and what's the right fix? Two teammates suggest `FetchType.EAGER` and
`hibernate.enable_lazy_load_no_trans=true`.

```java
@Service
public class OrderService {
    public Order getOrder(Long id) {                       // no @Transactional
        return orderRepository.findById(id).orElseThrow();
    }
}

@Component
public class InvoiceJob {
    @Scheduled(cron = "0 0 2 * * *")
    public void run() {
        Order o = orderService.getOrder(42L);
        log.info("items: {}", o.getItems().size());        // @OneToMany, LAZY by default
    }
}
```
""",
None, None,
"LazyInitializationException; fix it with FetchType.EAGER or enable_lazy_load_no_trans.",
r"""
Candidates name the exception correctly, then reach for global switches that make it go away. Both suggestions hide
the symptom by changing loading behaviour for the whole application. Both also create performance problems that are
harder to find than the original exception.
""",
r"""
`findById` runs in the repository's own transaction. When it returns, the persistence context closes and `o` is
detached. `getItems()` returns an uninitialized proxy collection, and `size()` throws `LazyInitializationException:
failed to lazily initialize a collection ... could not initialize proxy - no Session`. In a web request the same code
may have 'worked' only because open-in-view kept the session open.

The right fix is to decide per use case what to load, inside a transaction: a `JOIN FETCH` or `@EntityGraph` query,
or mapping to a DTO inside a `@Transactional` service method. `EAGER` on a collection makes every load of Order fetch
its items, and no query can turn it off, which causes N+1 queries or huge joins elsewhere. `enable_lazy_load_no_trans`
opens a fresh session and connection for every lazy access: N+1 with extra connection churn and no transactional
consistency. `Hibernate.initialize(o.getItems())` inside a transaction also works, but it's clumsy.
""",
r"""
```java
public interface OrderRepository extends JpaRepository<Order, Long> {
    @EntityGraph(attributePaths = "items")
    Optional<Order> findWithItemsById(Long id);
}

@Transactional(readOnly = true)
public InvoiceData invoiceData(Long id) {
    Order o = orderRepository.findWithItemsById(id).orElseThrow();
    return InvoiceData.from(o);          // map while the session is still open
}
```
""",
"Reject both global switches by name and explain why. Interviewers use this question precisely to see whether you'll reach for EAGER."),

T("trap-jpa-hibernate-entity-equals-hashcode", A, "equals/hashCode on entities with generated ids", "Advanced", "Common",
r"""
What does this print? Nothing has been persisted yet.

```java
@Entity
public class Tag {
    @Id @GeneratedValue private Long id;
    private String name;

    public Tag(String name) { this.name = name; }
    protected Tag() { }

    @Override public boolean equals(Object o) {
        return o instanceof Tag t && Objects.equals(id, t.id);
    }
    @Override public int hashCode() { return Objects.hash(id); }
}

Set<Tag> tags = new HashSet<>();
tags.add(new Tag("java"));
tags.add(new Tag("spring"));
System.out.println(tags.size());
```
""",
["2", "1", "0", "NullPointerException, because id is null"], 1,
"2: they are different tags with different names.",
r"""
Using the id for equality feels natural, because the id *is* the row's identity in the database. But generated ids
don't exist until the entity is persisted. Until then every new entity has `id == null`, and
`Objects.equals(null, null)` is `true`, so all new entities look equal to each other.
""",
r"""
Both tags have a null id, so `equals` returns true and the hashes match. The set treats the second tag as a duplicate
and keeps only one, so a post saved with these tags would silently lose one. The opposite problem appears after
persisting: the id changes from null to, say, 7, so `hashCode` changes while the entity sits in a `HashSet`, and
`contains`/`remove` stop finding it (both effects verified in a plain Java simulation).

Lombok's `@Data`/`@EqualsAndHashCode` on entities is worse. It uses every field, including mutable ones and lazy
collections, which can trigger lazy loading, or a `StackOverflowError` with bidirectional relations. Safe options:
equality on a stable business key (a unique `sku` or `email`, ideally `@NaturalId`), or id-based `equals` that treats
a null id as 'not equal', combined with a constant `hashCode()`. Use `instanceof` rather than `getClass()` so
Hibernate proxies (which are subclasses) still compare equal.
""",
r"""
```java
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof Tag other)) return false;      // instanceof also matches Hibernate proxies
    return id != null && id.equals(other.getId());    // unsaved entities are never equal; getter works on proxies
}

@Override
public int hashCode() {
    return Tag.class.hashCode();   // constant, so it survives id assignment; fine for small entity collections
}
```
""",
"Explain both failure modes (null ids collapse before persist, hash changes after persist). Most candidates only know one of them."),

T("trap-jpa-hibernate-dirty-checking", A, "Dirty checking: no save() needed (and accidental writes)", "Basic", "Very common",
r"""
Is the new name written to the database?

```java
@Transactional
public void rename(Long userId, String newName) {
    User u = userRepository.findById(userId).orElseThrow();
    u.setName(newName);
    // no save() call
}
```
""",
["No, you must call save() or nothing is written",
 "Yes, dirty checking flushes the change when the transaction commits",
 "Only if the entity class is annotated @DynamicUpdate",
 "Only after an explicit entityManager.flush()"], 1,
"No: without userRepository.save(u), nothing is persisted.",
r"""
Spring Data's `save()` appears everywhere in tutorials, so it looks like the only way to write. Candidates think of
JPA like JDBC, where you change an object and then 'send' it. But entities loaded inside a transaction are *managed*:
Hibernate tracks them and writes changes for you. The flip side surprises people even more: changes you never meant
to persist get written too.
""",
r"""
Inside a transaction, `findById` returns a **managed** entity, and Hibernate keeps a snapshot of its loaded state. At
flush time (before commit, and before queries that might be affected) it compares each managed entity with its
snapshot and issues an UPDATE for every one that changed. So the rename is persisted without any `save()`. Calling
`save()` on a managed entity is redundant, because it merges the entity into itself.

The dangerous flip side: changing a managed entity just for display, such as masking an email before returning it,
gets **written to the database** at commit. Without `@Transactional`, `findById` runs in its own short transaction, the
entity is detached when it returns, and the change is silently lost. `@DynamicUpdate` only limits the UPDATE to the
modified columns, and `readOnly = true` switches dirty checking off.
""",
r"""
```java
@Transactional
public void rename(Long userId, String newName) {
    userRepository.findById(userId).orElseThrow().setName(newName);   // persisted at commit
}

// Never mutate entities to shape a response; map to a DTO instead
public UserDto view(User u) {
    return new UserDto(u.getId(), mask(u.getEmail()));
}
```
""",
"Bring up the accidental-write flip side (masking a field on a managed entity). It shows you've debugged this in real code."),

T("trap-jpa-hibernate-save-merge-detached", A, "save() on a detached entity returns a different object", "Advanced", "Common",
r"""
`Order` has a generated `@Id` and **no** `@Version` field. `incoming` was deserialized from a JSON request body and
has `id = 42`. Is `CONFIRMED` stored in the database?

```java
@Transactional
public Order confirm(Order incoming) {
    orderRepository.save(incoming);
    incoming.setStatus(Status.CONFIRMED);   // changed after save()
    return incoming;
}
```
""",
["Yes: save() attached incoming, so the later change is flushed at commit",
 "No: save() merged a copy; incoming is still detached, so the later change is lost",
 "Yes, because the method is @Transactional",
 "It throws 'detached entity passed to persist'"], 1,
"Yes: after save() the object is managed, and the transaction flushes the later change.",
r"""
People assume `save()` always makes the object you pass in managed. That's true only for new entities, which go
through `persist`. For an entity that already has an id, Spring Data calls `merge`, which copies the state onto a
*different*, managed instance and returns that one. The argument stays detached, and later changes to it are ignored.
""",
r"""
`SimpleJpaRepository.save()` checks `isNew()`, which without a `@Version` field means 'the id is null'. Here the id is
42, so it calls `entityManager.merge(incoming)`. That loads (or finds) the managed Order 42, copies `incoming`'s state
onto it, and **returns the managed instance**. `incoming` itself stays detached, so setting CONFIRMED on it afterwards
is never flushed. Always continue with the return value: `order = repository.save(order)`.

Merging an entity built from JSON has another trap. Every field is copied, so fields the client didn't send (null in
the JSON) overwrite real column values with NULL. For updates, load the managed entity, apply only the allowed fields
from a DTO, and let dirty checking write the change. Related: with manually assigned ids, `isNew()` sees a non-null id
and `save()` merges as well, which costs an extra SELECT per insert.
""",
r"""
```java
@Transactional
public OrderDto confirm(Long id) {
    Order order = orderRepository.findById(id).orElseThrow();   // managed
    order.setStatus(Status.CONFIRMED);                          // change only what this use case may change
    return OrderDto.from(order);                                // dirty checking writes it at commit
}

// if you really must save a detached object, keep using the returned instance
Order managed = orderRepository.save(incoming);
managed.setStatus(Status.CONFIRMED);
```
""",
"Mention that nulls from partial JSON overwrite columns on merge. That's the production bug behind this question."),

T("trap-jpa-hibernate-manytoone-eager-default", A, "@ManyToOne is EAGER by default", "Intermediate", "Common",
r"""
With default Hibernate settings (no batch fetching configured), how many SQL statements does `findAll()` run, even if
nobody touches `customer`?

```java
@Entity
public class Order {
    @Id @GeneratedValue private Long id;

    @ManyToOne                      // no fetch attribute
    private Customer customer;
}

List<Order> orders = orderRepository.findAll();   // 100 orders, 100 different customers
```
""",
["1, with a join to customer", "101", "1, because customer stays lazy until accessed",
 "2: one for orders and one for all customers"], 1,
"1: associations are lazy by default, so customers load only when accessed.",
r"""
Candidates learn 'JPA is lazy by default' from `@OneToMany`. But the JPA defaults depend on the association type:
to-one associations (`@ManyToOne`, `@OneToOne`) are EAGER and to-many are LAZY. And EAGER doesn't mean 'joined'. A
JPQL or Criteria query such as `findAll` loads an eager association with separate SELECTs.
""",
r"""
JPA defaults: `@ManyToOne` and `@OneToOne` are `EAGER`; `@OneToMany` and `@ManyToMany` are `LAZY`. `findAll()` runs a
query on Order only (`select o from Order o`), and Hibernate must then load the EAGER `customer` straight away.
Without batch fetching it issues one SELECT per distinct customer: 1 + 100 = 101 statements, even if your code never
reads `customer`. A single `findById` would use a join instead, which is why this often goes unnoticed in simple tests.

EAGER is a mapping-level decision that every query pays for and no query can switch off. Best practice: declare every
association `fetch = FetchType.LAZY` and fetch explicitly per use case with `JOIN FETCH` or `@EntityGraph`. Setting
`hibernate.default_batch_fetch_size` limits the damage to a few `IN (...)` queries.
""",
r"""
```java
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "customer_id")
private Customer customer;

// load customers only where a use case needs them
@EntityGraph(attributePaths = "customer")
List<Order> findByStatus(Status status);
```
""",
"Recite the four defaults (to-one EAGER, to-many LAZY) and say you make every association LAZY from day one."),

T("trap-jpa-hibernate-orphan-removal-vs-cascade", A, "orphanRemoval vs CascadeType.REMOVE", "Intermediate", "Common",
r"""
What SQL does Hibernate run for the removed item at commit?

```java
@Entity
public class Order {
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)   // no orphanRemoval
    private List<OrderItem> items = new ArrayList<>();
}

@Transactional
public void removeFirstItem(Long orderId) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.getItems().remove(0);
}
```
""",
["DELETE FROM order_item ..., because CascadeType.ALL includes REMOVE",
 "Nothing: the row stays, and the item reappears when the order is reloaded",
 "UPDATE order_item SET order_id = NULL ...",
 "An exception, because the item is now orphaned"], 1,
"A DELETE, because CascadeType.ALL includes REMOVE.",
r"""
Candidates read `CascadeType.REMOVE` as 'children get deleted when they leave the parent'. It actually means 'when the
parent is removed with `em.remove`, remove the children too'. Taking a child out of the collection is a different
operation, and on the inverse (`mappedBy`) side Hibernate doesn't even use the collection to write the foreign key.
""",
r"""
`CascadeType.REMOVE` (part of `ALL`) only cascades `entityManager.remove(order)`. Removing an element from the
collection isn't a remove operation. The collection is the inverse side (`mappedBy`), and the foreign key is owned by
`OrderItem.order`, which still points at the order, so Hibernate generates no SQL at all. The row stays, and on the
next load the item is back.

With `orphanRemoval = true`, Hibernate deletes any child removed from the collection, here with
`DELETE FROM order_item WHERE id = ?`. Use it only for children that can't exist without their parent (order lines,
not tags). Two related traps. Replacing the collection (`order.setItems(new ArrayList<>())`) when orphanRemoval is on
throws 'A collection with cascade="all-delete-orphan" was no longer referenced'; change the existing collection with
`clear()`/`addAll()` instead. And `CascadeType.REMOVE` on `@ManyToMany` deletes shared entities that other parents
still use.
""",
r"""
```java
@OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
private List<OrderItem> items = new ArrayList<>();

public void removeItem(OrderItem item) {   // keep both sides in sync
    items.remove(item);
    item.setOrder(null);
}
```
""",
"Contrast the two in one line: REMOVE follows the parent's deletion, orphanRemoval follows a child leaving the collection."),

T("trap-jpa-hibernate-bidirectional-sync", A, "Bidirectional mapping: only the owning side writes the FK", "Intermediate", "Common",
r"""
What ends up in the `order_item` table?

```java
@Entity
public class Order {
    @Id @GeneratedValue private Long id;
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items = new ArrayList<>();
}

@Entity
public class OrderItem {
    @Id @GeneratedValue private Long id;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "order_id")
    private Order order;
}

Order order = new Order();
OrderItem item = new OrderItem();
order.getItems().add(item);          // only this side is set
orderRepository.save(order);
```
""",
["The item, with order_id set correctly", "The item with order_id = NULL (or a NOT NULL constraint error)",
 "No item row: cascade only works when both sides are set",
 "Hibernate sets item.order automatically, so the row is correct"], 1,
"The item row with the correct order_id, because the item is in the order's collection.",
r"""
In Java the relationship looks complete, since the order holds the item. But in a bidirectional mapping only the
**owning side** (the one with the `@JoinColumn`, here `OrderItem.order`) decides the foreign key. The `mappedBy`
collection is ignored when writing SQL, and Hibernate doesn't keep the two sides in sync for you.
""",
r"""
`cascade = ALL` makes Hibernate persist the item together with the order, so a row is inserted. But the `order_id`
value comes from `item.getOrder()`, which is null, so the row gets `order_id = NULL`, or fails with a constraint
violation if the column is NOT NULL. The collection side (`mappedBy = "order"`) is the inverse side: it's used for
reading, never for writing the foreign key. The object graph in the current persistence context is inconsistent too,
because `item.getOrder()` stays null until the data is reloaded.

The standard fix is helper methods on the parent that set both sides, and using only those. The same rule explains
why removing an item from the collection alone doesn't change the database.
""",
r"""
```java
@Entity
public class Order {
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();

    public void addItem(OrderItem item) {
        items.add(item);
        item.setOrder(this);      // owning side: this is what writes order_id
    }

    public void removeItem(OrderItem item) {
        items.remove(item);
        item.setOrder(null);
    }
}
```
""",
"Use the terms 'owning side' and 'inverse side', and show the add/remove helpers. That's the complete answer."),

T("trap-jpa-hibernate-pagination-join-fetch", A, "Pagination with JOIN FETCH happens in memory", "Advanced", "Common",
r"""
This works in tests with 50 orders. Production has 2 million orders. What happens?

```java
@Query(value = "select o from Order o join fetch o.items",
       countQuery = "select count(o) from Order o")
Page<Order> findAllWithItems(Pageable pageable);   // called with PageRequest.of(0, 20)
```
""",
None, None,
"The database returns 20 orders with their items, using LIMIT 20.",
r"""
Candidates assume Hibernate always turns a `Pageable` into `LIMIT`. But a collection fetch join returns one row per
*item*, not per order, so limiting rows would cut an order's items in half. Hibernate refuses to do that in SQL.
Instead it paginates in memory, after loading everything, and only logs a warning.
""",
r"""
With `join fetch` on a collection, the SQL result has one row per order item. A `LIMIT 20` would return 20 *rows*,
which might be 3 orders with partial item lists. So Hibernate drops the LIMIT, fetches **all** matching rows, builds
every entity in memory, and then returns the requested page. It logs `firstResult/maxResults specified with collection
fetch; applying in memory` (HHH000104 in Hibernate 5, HHH90003004 in Hibernate 6). In production that means millions of
rows loaded per request: slow queries, huge memory use, OOM.

Set `hibernate.query.fail_on_pagination_over_collection_fetch=true` so this fails fast in tests. Fix it with two
queries: page over order ids with a normal LIMIT query, then fetch those orders with their items. Alternatively, page
plain orders and let batch fetching (`@BatchSize` or `default_batch_fetch_size`) load the items in one or two `IN`
queries. Fetch-joining a to-one association (`join fetch o.customer`) works fine with pagination.
""",
r"""
```java
@Query("select o.id from Order o order by o.createdAt desc")
Page<Long> findPageOfIds(Pageable pageable);                       // real LIMIT/OFFSET in SQL

@Query("select distinct o from Order o join fetch o.items where o.id in :ids order by o.createdAt desc")
List<Order> findWithItems(@Param("ids") List<Long> ids);

// in the service
Page<Long> ids = orderRepository.findPageOfIds(PageRequest.of(0, 20));
List<Order> orders = orderRepository.findWithItems(ids.getContent());
```

```yaml
spring:
  jpa:
    properties:
      hibernate.query.fail_on_pagination_over_collection_fetch: true
```
""",
"Mention the fail_on_pagination_over_collection_fetch flag. It shows you prevent this whole class of bug rather than fixing one instance."),

T("trap-jpa-hibernate-optimistic-locking", A, "Lost updates and @Version", "Intermediate", "Common",
r"""
Two admins open the same product page (price 500). Admin A sets 450 and admin B sets 550; both press Save within
seconds of each other. The update endpoint:

```java
@Transactional
public void updatePrice(Long productId, BigDecimal newPrice) {
    Product p = productRepository.findById(productId).orElseThrow();
    p.setPrice(newPrice);
}
```

What's the final price? A teammate adds `@Version private Long version;` to `Product`. Does that solve it?
""",
None, None,
"@Transactional already prevents conflicting updates, and adding @Version locks the row so the second admin waits.",
r"""
Candidates treat a transaction as a lock on everything it reads. At READ COMMITTED, or MySQL's default REPEATABLE READ,
two transactions can both read the row and both update it, and the last commit simply wins. `@Version` is
misunderstood too: it doesn't lock anything. It only detects, at write time, that someone else changed the row first.
""",
r"""
Without a version column, both updates succeed and the last commit wins: a **lost update**, with no error anywhere.
With `@Version`, Hibernate adds `WHERE id = ? AND version = ?` to the UPDATE and increments the version. The second
writer's UPDATE matches 0 rows, so Hibernate throws an `OptimisticLockException`, which Spring surfaces as
`ObjectOptimisticLockingFailureException`. Your code must handle it: retry automatic operations, or return HTTP 409 so
the user reloads.

The subtle part: this endpoint re-loads the entity inside the PUT request, so the version check only covers the few
milliseconds between that load and the commit, not the minutes since the admin opened the page. To protect the whole
user 'conversation', send the version to the client and back and compare it (or use `If-Match` with an ETag). Also,
bulk JPQL `UPDATE` statements skip the version check unless you increment the version yourself.
""",
r"""
```java
@Entity
public class Product {
    @Id @GeneratedValue private Long id;
    private BigDecimal price;
    @Version private Long version;
}

public record PriceUpdate(BigDecimal price, long version) {}

@Transactional
public void updatePrice(Long id, PriceUpdate req) {
    Product p = productRepository.findById(id).orElseThrow();
    if (p.getVersion() != req.version()) {                       // Long vs long: compares values
        throw new ConflictException("Product changed since you loaded it");   // map to HTTP 409
    }
    p.setPrice(req.price());   // UPDATE ... WHERE id = ? AND version = ? still guards the last-millisecond race
}
```
""",
"Point out that the version has to travel to the client and back, or @Version only protects a millisecond window. That's the senior insight."),

T("trap-jpa-hibernate-identity-disables-batching", A, "IDENTITY ids disable JDBC batch inserts", "Advanced", "Common",
r"""
`spring.jpa.properties.hibernate.jdbc.batch_size` is set to 50. An import job calls `eventRepository.saveAll(events)`
with 10,000 new events. How many INSERT statements go to MySQL?

```java
@Entity
public class Event {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)   // MySQL AUTO_INCREMENT
    private Long id;
    private String type;
    private String payload;
}
```
""",
["200 batches of 50", "10,000 individual INSERTs: Hibernate disables insert batching for IDENTITY ids",
 "1 multi-row INSERT", "50"], 1,
"200 JDBC batches of 50, because batch_size is set to 50.",
r"""
Candidates set `batch_size` and assume the job is done. They don't connect id generation with batching. Hibernate has
to register every persisted entity in the persistence context under its id, and with IDENTITY the id exists only once
the row has been inserted. So each `persist` must execute its INSERT immediately, one at a time.
""",
r"""
With `GenerationType.IDENTITY`, the database assigns the id during the INSERT. Hibernate needs that id the moment you
call `persist`, so it executes each INSERT straight away and quietly disables JDBC insert batching for the entity:
10,000 round trips, whatever `batch_size` says. Batching works with ids Hibernate can know in advance: `SEQUENCE` with
a pooled optimizer (PostgreSQL, Oracle), or application-assigned ids such as UUIDv7 or TSID.

MySQL has no sequences, which is why so many MySQL apps use IDENTITY. For bulk loads there, use
`JdbcTemplate.batchUpdate` with `rewriteBatchedStatements=true` on the Connector/J URL, which rewrites a batch into
multi-row INSERTs. Also: without `hibernate.jdbc.batch_size` nothing is batched at all; `hibernate.order_inserts=true`
helps batches of mixed entities; and in big imports, flush and clear the persistence context every N entities so it
doesn't grow without bound.
""",
r"""
```java
// MySQL bulk insert: plain JDBC batching, rewritten by the driver into multi-row INSERTs
// spring.datasource.url=jdbc:mysql://host:3306/app?rewriteBatchedStatements=true
jdbcTemplate.batchUpdate(
        "INSERT INTO event (type, payload) VALUES (?, ?)",
        events,             // List<EventRow>
        500,                // batch size
        (ps, e) -> {
            ps.setString(1, e.type());
            ps.setString(2, e.payload());
        });
```
""",
"Mention rewriteBatchedStatements for MySQL. It's the detail that shows you've actually tuned a bulk import."),

T("trap-jpa-hibernate-flush-timing", A, "Constraint violation thrown at commit, not at save()", "Advanced", "Common",
r"""
`User` has `@Id @GeneratedValue(strategy = GenerationType.UUID) private UUID id;` and `email` has a UNIQUE
constraint. The email already exists. What does the client get?

```java
@Transactional
public void register(String email) {
    try {
        userRepository.save(new User(email));
    } catch (DataIntegrityViolationException e) {
        throw new EmailAlreadyTakenException(email);   // mapped to HTTP 409
    }
    welcomeService.queueWelcome(email);
}
```
""",
["HTTP 409, from EmailAlreadyTakenException",
 "HTTP 500: the duplicate is detected at commit, after the method body finishes, so the catch never runs",
 "HTTP 200: the duplicate is silently ignored",
 "HTTP 409, but the welcome message is still queued"], 1,
"409: save() throws DataIntegrityViolationException and the catch block converts it.",
r"""
Candidates assume `save()` runs an INSERT on the spot, like JDBC. Hibernate actually queues the INSERT in the
persistence context and sends it at flush time, which by default is at commit (or before a query that needs it). The
constraint violation therefore surfaces outside the try block, from the transaction proxy.
""",
r"""
With a UUID (or sequence) id, `persist` doesn't need the database to produce the id, so Hibernate just schedules the
INSERT. It runs at flush: at commit, after `register()`'s body has finished, or earlier if a query touching `users`
triggers an auto-flush. The constraint violation is thrown then and surfaces from the transaction proxy as a Spring
`DataAccessException` (typically `DataIntegrityViolationException`), which reaches the client as a 500. The catch
block never runs, and if `queueWelcome` has external side effects, they have already happened for a user that will
never exist. With IDENTITY ids the INSERT runs inside `save()`, so behaviour changes with the id strategy, which makes
this bug easy to introduce.

`saveAndFlush` forces the INSERT inside the try. After a failed flush the transaction is rollback-only, so translate
and rethrow; don't carry on. A cleaner design checks `existsByEmail` first for a friendly error, keeps the unique
constraint as the real guard, and maps `DataIntegrityViolationException` to 409 in a `@RestControllerAdvice`.
""",
r"""
```java
@Transactional
public void register(String email) {
    if (userRepository.existsByEmail(email)) throw new EmailAlreadyTakenException(email);  // friendly path
    try {
        userRepository.saveAndFlush(new User(email));    // INSERT runs here, inside the try
    } catch (DataIntegrityViolationException e) {        // race: someone registered in between
        throw new EmailAlreadyTakenException(email);     // tx is rollback-only now: rethrow, don't continue
    }
    eventPublisher.publishEvent(new UserRegistered(email)); // handle with @TransactionalEventListener(AFTER_COMMIT)
}
```
""",
"Explain that flush timing depends on the id strategy (IDENTITY inserts immediately, UUID/sequence at flush). That one detail separates people who've debugged this from people who haven't."),
]
