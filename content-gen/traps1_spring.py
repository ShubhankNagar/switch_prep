"""Spring / Spring Boot traps (behaviour per Spring Framework 6.x / Boot 3.x docs)."""
from traps1_common import T

A = "spring"

TRAPS = [
T("trap-spring-transactional-self-invocation", A, "@Transactional self-invocation (proxy bypass)", "Intermediate", "Very common",
r"""
The controller calls `placeOrders()`. The payment for the 3rd request fails. What gets rolled back?

```java
@Service
public class OrderService {

    public void placeOrders(List<OrderRequest> requests) {
        for (OrderRequest r : requests) {
            placeOrder(r);
        }
    }

    @Transactional
    public void placeOrder(OrderRequest r) {
        orderRepository.save(toOrder(r));
        paymentClient.charge(r);          // throws RuntimeException for the 3rd request
    }
}
```
""",
["Only the 3rd order's insert", "All three orders",
 "Nothing: placeOrder() ran without a transaction, so the 3rd order stays saved with no payment",
 "Spring fails at startup because of the self-call"], 2,
"Only the 3rd order is rolled back, because placeOrder() is @Transactional.",
r"""
Candidates think the annotation changes the method itself. In Spring's default proxy mode, a proxy object wrapped
around the bean starts the transaction, and only calls that go **through the proxy** are intercepted. Inside the same
class, `placeOrder(r)` is just `this.placeOrder(r)`, a plain Java call that never touches the proxy.
""",
r"""
Spring wraps `OrderService` in a proxy (a CGLIB subclass by default in Boot). The controller calls
`proxy.placeOrders()`, which has no annotation, so no transaction starts. The real object then calls
`this.placeOrder(r)` directly, and the transaction interceptor never runs. Each `orderRepository.save()` runs in the
repository's own short transaction (Spring Data repository methods are transactional) and commits immediately. When
`charge` throws there's nothing to roll back: orders 1 to 3 are all saved, and order 3 has no payment.

The same proxy rule means the annotation does nothing on `private` or `final` methods. Since Spring 6, class-based
proxies also intercept `protected` and package-private methods, but the call still has to come from outside the bean.
`@Async`, `@Cacheable`, `@Retryable` and `@PreAuthorize` all behave the same way.
""",
r"""
```java
@Service
public class OrderBatchService {
    private final OrderService orderService;   // a different bean, so calls go through its proxy

    public OrderBatchService(OrderService orderService) { this.orderService = orderService; }

    public void placeOrders(List<OrderRequest> requests) {
        requests.forEach(orderService::placeOrder);   // each order gets its own transaction
    }
}

// or, inside one class, make the boundary explicit
transactionTemplate.executeWithoutResult(status -> placeOrderInternal(r));
```
""",
"After explaining the proxy, point out the second smell: a remote payment call inside a DB transaction holds a connection and locks during network I/O. That's the senior-level observation."),

T("trap-spring-rollback-checked-exception", A, "No rollback on checked exceptions by default", "Intermediate", "Very common",
r"""
When the exception is thrown, is the balance change rolled back?

```java
public class InsufficientFundsException extends Exception { }   // checked

@Transactional
public void withdraw(long accountId, long amount) throws InsufficientFundsException {
    Account acc = accountRepository.findById(accountId).orElseThrow();
    acc.setBalance(acc.getBalance() - amount);
    auditRepository.save(new Audit(accountId, amount));
    if (acc.getBalance() < 0) {
        throw new InsufficientFundsException();
    }
}
```
""",
["Yes, any exception thrown out of a @Transactional method rolls back",
 "No, the transaction commits: by default only RuntimeException and Error trigger a rollback",
 "Yes, but the audit row is kept", "It depends on the database isolation level"], 1,
"Yes: an exception escaping a @Transactional method always rolls back.",
r"""
'Exception means failure means rollback' feels obvious. Spring's default, inherited from EJB conventions, treats
checked exceptions as expected business outcomes that the caller can handle, so it **commits**. Many codebases use only
unchecked exceptions, so people never see this behaviour until a checked exception sneaks in.
""",
r"""
By default Spring rolls back only for `RuntimeException` and `Error`. A checked exception that propagates out of the
method still **commits** the transaction. Here the negative balance and the audit row are both written, and then the
caller gets the exception. Fixes: declare `rollbackFor = Exception.class` (or the specific type), make domain
exceptions extend `RuntimeException`, or, since Spring 6.2, change the global default with
`@EnableTransactionManagement(rollbackOn = RollbackOn.ALL_EXCEPTIONS)`.

An even more common variant: catching an exception inside the transactional method and only logging it. Spring never
sees the exception, so it commits whatever partial work was done. Either rethrow it, or mark the transaction explicitly
with `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`.
""",
r"""
```java
@Transactional(rollbackFor = InsufficientFundsException.class)
public void withdraw(long accountId, long amount) throws InsufficientFundsException { /* ... */ }

// or make business exceptions unchecked
public class InsufficientFundsException extends RuntimeException { }

// better still: validate before writing anything
if (acc.getBalance() < amount) throw new InsufficientFundsException();
```
""",
"Mention the 'catch and log' variant as well. It's the version you actually find when reviewing legacy code."),

T("trap-spring-unexpected-rollback", A, "Caught exception, yet UnexpectedRollbackException", "Advanced", "Common",
r"""
Loyalty fails. What happens to the order?

```java
@Service
public class OrderService {
    @Transactional
    public void placeOrder(Order order) {
        orderRepository.save(order);
        try {
            loyaltyService.addPoints(order);   // other bean, @Transactional (REQUIRED), throws RuntimeException
        } catch (RuntimeException e) {
            log.warn("Loyalty failed, continuing", e);
        }
    }
}
```
""",
["The order is saved; only the loyalty work is skipped",
 "The order is rolled back and the caller gets UnexpectedRollbackException",
 "Only the loyalty changes are rolled back; the order commits",
 "The order is saved and the exception is logged twice"], 1,
"The order is saved, because the exception was caught.",
r"""
Candidates picture `addPoints` as having its own transaction that fails on its own. With the default propagation,
`REQUIRED`, it **joins** the caller's transaction: one physical transaction, one fate. When the exception passes
through the inner proxy, Spring marks that shared transaction rollback-only, and catching the exception later can't
remove the mark.
""",
r"""
`addPoints` joins the existing transaction. Its proxy sees the RuntimeException, but as a mere participant it can't
roll back on its own, so it marks the whole transaction **rollback-only**. `placeOrder` catches the exception and
returns normally, so its proxy tries to commit. It finds the flag, rolls everything back (the order included) and
throws `UnexpectedRollbackException: Transaction silently rolled back because it has been marked as rollback-only`.

Options: give `addPoints` `propagation = REQUIRES_NEW` so it runs in its own physical transaction and its failure can't
affect the order; add `noRollbackFor` on `addPoints` if its failure is harmless; or, often best, run non-critical side
effects after the commit with `@TransactionalEventListener(phase = AFTER_COMMIT)` or an outbox. The same trap appears
when you catch a repository exception, such as a constraint violation, inside a service transaction.
""",
r"""
```java
// LoyaltyService: an independent transaction, so its failure can't doom the order
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void addPoints(Order order) { /* ... */ }

// or decouple: publish an event inside placeOrder and handle it once the order is committed
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onOrderPlaced(OrderPlacedEvent e) {
    loyaltyService.addPoints(e.order());   // REQUIRES_NEW above, so it commits on its own
}
```
""",
"Explain 'participating transaction, rollback-only flag' in one sentence, then offer the after-commit event as the design fix."),

T("trap-spring-requires-new-pool-exhaustion", A, "REQUIRES_NEW: same-class calls and connection-pool deadlock", "Advanced", "Common",
r"""
`AuditService.record` is annotated `@Transactional(propagation = Propagation.REQUIRES_NEW)`.

```java
@Service
public class PaymentService {
    @Transactional
    public void pay(Payment p) {
        paymentRepository.save(p);
        auditService.record("PAY_ATTEMPT", p.getId());   // REQUIRES_NEW
        gateway.charge(p);                                // may throw
    }
}
```

1. If `charge` throws, is the audit row kept?
2. The Hikari pool has 10 connections, and during a spike more than 10 `pay()` calls run at once. What can go wrong?
""",
None, None,
"(1) Yes, REQUIRES_NEW always commits separately. (2) Nothing special: it's still one request using the database.",
r"""
Candidates learn REQUIRES_NEW as 'an independent transaction' and stop there. They don't picture what it means
physically: the outer transaction is suspended but **keeps its connection and its row locks**, and the inner one needs a
second connection from the same pool. Under load, that doubles the connections each request needs.
""",
r"""
(1) Yes, as long as `record` lives in another bean. The inner transaction commits on its own before `charge` runs, so
the audit row survives the outer rollback. If `record` were in the same class, the self-call would bypass the proxy, no
new transaction would start, and the audit row would roll back with the payment.

(2) Each `pay()` holds one connection and then asks for a second. If 10 threads each hold one of the 10 connections
and all wait for another, none can continue. This pool deadlock ends only when Hikari's `connectionTimeout` (30 s by
default) throws `SQLTransientConnectionException`. A related trap: if the inner transaction touches rows the outer one
has already locked, it waits on a lock held by its own suspended caller until `innodb_lock_wait_timeout` expires.
Keep REQUIRES_NEW rare, size the pool for it, never use it in a loop, and consider writing audit data after completion
or through an outbox.
""",
r"""
```java
// Record the attempt once the outcome is known: no second connection while the first is held
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMPLETION)   // after commit OR rollback
public void onPaymentAttempted(PaymentAttempted e) {
    auditService.record(e.type(), e.paymentId());    // REQUIRES_NEW, in its own bean
}

// If REQUIRES_NEW must stay on the hot path, size the pool for peak concurrency x 2:
// spring.datasource.hikari.maximum-pool-size=...
```
""",
"Draw the connection math (N requests x 2 connections against a pool of N). Interviewers rarely hear candidates reason about pools."),

T("trap-spring-async-self-invocation", A, "@Async self-invocation, void return and the default executor", "Intermediate", "Very common",
r"""
`@EnableAsync` is configured. Roughly how long does `signup()` take, and what happens if `mailClient.send` throws?

```java
@Service
public class SignupService {

    public void signup(User u) {
        userRepository.save(u);
        sendWelcomeEmail(u);          // takes ~3 seconds
    }

    @Async
    public void sendWelcomeEmail(User u) {
        mailClient.send(welcomeMail(u));
    }
}
```
""",
["Almost instant: the email goes to a background thread, and its exception is rethrown into signup()",
 "About 3 seconds: the self-call bypasses the proxy, so the email is sent synchronously and its exception propagates into signup()",
 "Almost instant, and the exception is silently lost",
 "Startup fails: @Async methods must return a Future"], 1,
"Almost instant, because @Async moves the email to a background thread.",
r"""
It's the same proxy misconception as with @Transactional: people believe the annotation changes the method. `@Async`
works only when the call goes through the Spring proxy, which hands the invocation to an executor. A call from another
method of the same bean is a direct Java call, so it runs on the caller's thread.
""",
r"""
`sendWelcomeEmail(u)` is really `this.sendWelcomeEmail(u)`. It skips the proxy and runs synchronously, so signup takes
about 3 s and a mail failure propagates straight into `signup()`. Move the method to a separate bean and it really does
run on an executor, which brings the next set of traps.

A `void` @Async method's exceptions never reach the caller. They go to the `AsyncUncaughtExceptionHandler` (which logs
them by default), so return a `CompletableFuture` if you need the outcome. The async thread doesn't inherit the
caller's transaction, security context or MDC. And the executor matters: Spring Boot auto-configures a
`ThreadPoolTaskExecutor` with 8 core threads and an unbounded queue (or virtual threads when
`spring.threads.virtual.enabled=true`). Plain Spring with no executor bean falls back to `SimpleAsyncTaskExecutor`,
which starts a new thread per task.
""",
r"""
```java
@Service
public class WelcomeMailer {
    @Async("mailExecutor")
    public CompletableFuture<Void> sendWelcomeEmail(User u) {
        mailClient.send(welcomeMail(u));
        return CompletableFuture.completedFuture(null);
    }
}

@Bean
ThreadPoolTaskExecutor mailExecutor() {
    ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
    ex.setCorePoolSize(4);
    ex.setMaxPoolSize(8);
    ex.setQueueCapacity(500);          // bounded
    ex.setThreadNamePrefix("mail-");
    return ex;
}
```
""",
"Add that you'd send the email only after the signup transaction commits (an AFTER_COMMIT event or an outbox), so a rollback never emails a user who doesn't exist."),

T("trap-spring-prototype-in-singleton", A, "Prototype bean injected into a singleton", "Intermediate", "Common",
r"""
1,000 checkout requests call `quote()`. How many `PriceCalculator` instances are created?

```java
@Component
@Scope("prototype")
public class PriceCalculator {
    private final List<String> appliedRules = new ArrayList<>();
    public Quote calculate(Cart cart) { /* fills appliedRules, returns a quote */ }
}

@Service                                  // default singleton scope
public class CheckoutService {
    private final PriceCalculator calculator;
    public CheckoutService(PriceCalculator calculator) { this.calculator = calculator; }
    public Quote quote(Cart cart) { return calculator.calculate(cart); }
}
```
""",
["1,000, one per call, because it's a prototype", "1, created when CheckoutService was created",
 "One per HTTP worker thread", "None until the first call, then one per request"], 1,
"1,000: prototype means a new instance every time it is used.",
r"""
'Prototype means a new instance each time' is true only for each time the container is **asked** for the bean.
Injection into a singleton happens exactly once, when the singleton is built. After that the singleton just holds an
ordinary Java reference, and Spring is never consulted again.
""",
r"""
Dependencies are resolved when a bean is created. `CheckoutService` is created once, so the container creates one
`PriceCalculator` for it, and every request reuses that instance. Here that also means `appliedRules` is shared by all
concurrent requests: rules from one customer's quote leak into another's, and many threads modify the list at once.

To get a fresh instance per use, ask the container each time: inject `ObjectProvider<PriceCalculator>` and call
`getObject()`, or use a `@Lookup` method. A scoped proxy (`proxyMode = ScopedProxyMode.TARGET_CLASS`) also works, but
it creates a new target on *every method call*, which surprises people. For one instance per HTTP request, use
`@RequestScope`. Simplest of all: make the calculator stateless and keep per-call state in local variables. Also note
that Spring doesn't call destroy callbacks on prototype beans.
""",
r"""
```java
@Service
public class CheckoutService {
    private final ObjectProvider<PriceCalculator> calculators;

    public CheckoutService(ObjectProvider<PriceCalculator> calculators) { this.calculators = calculators; }

    public Quote quote(Cart cart) {
        return calculators.getObject().calculate(cart);   // a new prototype instance per call
    }
}
```
""",
"Say the cleanest fix is usually to make the bean stateless, and that you'd reach for ObjectProvider only when per-use state is really needed."),

T("trap-spring-circular-dependency", A, "Circular dependencies in Spring Boot 2.6+", "Intermediate", "Common",
r"""
What happens when this Spring Boot 3 application starts?

```java
@Service
public class OrderService {
    private final InvoiceService invoiceService;
    public OrderService(InvoiceService invoiceService) { this.invoiceService = invoiceService; }
}

@Service
public class InvoiceService {
    @Autowired
    private OrderService orderService;    // field injection
}
```
""",
["It starts fine: Spring resolves cycles automatically with early references",
 "Startup fails: Boot rejects circular references by default (since 2.6) and reports the cycle",
 "It starts, but orderService is null inside InvoiceService",
 "It starts, but one of the services is created twice"], 1,
"It starts fine: Spring resolves circular dependencies through its three-level cache, as long as one side uses field injection.",
r"""
Many tutorials, and older experience, describe Spring's early-reference cache that can resolve setter and field
cycles. That was the default until Spring Boot 2.5. Since Boot 2.6, circular references are **prohibited by default**.
Even when they're allowed, a cycle involving constructor injection resolves only if beans happen to be created in the
'lucky' order.
""",
r"""
Spring Boot 2.6+ sets `spring.main.allow-circular-references=false`, so the context fails to start with a report that
"the dependencies of some of the beans in the application context form a cycle" (a `BeanCurrentlyInCreationException`
underneath).

Even with the property set to `true`, the result depends on creation order. If `OrderService` is created first, its
constructor needs `InvoiceService`, which in turn needs an `OrderService` that doesn't exist yet, so startup fails. If
`InvoiceService` is created first, its early reference can be handed over and startup succeeds. A design that only
starts in one bean order is fragile. A cycle is usually a design smell: two services that each know too much about the
other. Fix it by extracting the shared logic into a third bean or publishing an event instead of calling back. As a
last resort, inject one side with `@Lazy`, which gives a proxy resolved on first use.
""",
r"""
```java
@Service
public class PricingRules { /* the logic both services were borrowing from each other */ }

@Service
public class OrderService {
    public OrderService(InvoiceService invoiceService, PricingRules rules) { /* ... */ }
}

@Service
public class InvoiceService {
    public InvoiceService(PricingRules rules) { /* ... */ }   // no back-reference to OrderService
}

// last resort: a lazy proxy breaks the cycle at runtime
public InvoiceService(@Lazy OrderService orderService) { /* ... */ }
```
""",
"Treat the cycle as a design problem and refactor; mention @Lazy and allow-circular-references only as escape hatches."),

T("trap-spring-field-vs-constructor-injection", A, "Field injection vs constructor injection", "Basic", "Very common",
r"""
Your team puts `@Autowired` on private fields everywhere. In code review, someone asks you to switch to constructor
injection. Is that just a matter of style? Make the case either way.

```java
@Service
public class ReportService {
    @Autowired private OrderRepository orderRepository;
    @Autowired private PdfRenderer pdfRenderer;
    @Autowired private MailClient mailClient;
}
```
""",
None, None,
"It's just style: field injection is shorter, and Spring injects both the same way.",
r"""
Field injection works, so the differences only show up later: in unit tests, in null-pointer bugs, and in classes that
quietly grow to a dozen dependencies. Candidates who haven't written many plain unit tests don't feel that pain. Many
also still believe a constructor needs `@Autowired`, or that constructor injection becomes unworkable with many
dependencies.
""",
r"""
Constructor injection is the recommended default, for concrete reasons:

- **Immutability**: fields can be `final`, so nobody ever sees a half-wired bean.
- **Fail fast**: a missing dependency stops startup instead of causing an NPE later, and the object can't exist
  without its dependencies.
- **Testability**: `new ReportService(fakeRepo, fakeRenderer, fakeMail)` works in a plain JUnit test, with no Spring
  context and no reflection-based `@InjectMocks`.
- **Design feedback**: an eight-parameter constructor makes a class that does too much impossible to miss.
- **Cycles** are detected at startup instead of being hidden.

Since Spring 4.3, a class with a single constructor needs no `@Autowired` at all. Field injection hides dependencies
and ties the class to a DI container. Setter injection still makes sense for genuinely optional dependencies, and field
injection is acceptable in test classes.
""",
r"""
```java
@Service
public class ReportService {
    private final OrderRepository orderRepository;
    private final PdfRenderer pdfRenderer;
    private final MailClient mailClient;

    public ReportService(OrderRepository orderRepository, PdfRenderer pdfRenderer, MailClient mailClient) {
        this.orderRepository = orderRepository;
        this.pdfRenderer = pdfRenderer;
        this.mailClient = mailClient;
    }
}
```
""",
"Lead with testability and the 'too many constructor parameters' design signal. Those are the arguments seniors use, not 'the docs say so'."),

T("trap-spring-primary-vs-qualifier", A, "@Primary vs @Qualifier: which wins?", "Basic", "Common",
r"""
Which gateway is injected into `IndiaCheckoutService`?

```java
@Configuration
public class GatewayConfig {
    @Bean @Primary
    PaymentGateway stripeGateway() { return new StripeGateway(); }

    @Bean
    PaymentGateway razorpayGateway() { return new RazorpayGateway(); }
}

@Service
public class IndiaCheckoutService {
    public IndiaCheckoutService(@Qualifier("razorpayGateway") PaymentGateway gateway) { /* ... */ }
}
```
""",
["stripeGateway, because @Primary always wins",
 "razorpayGateway, because @Qualifier narrows the candidates before @Primary is considered",
 "NoUniqueBeanDefinitionException at startup",
 "Startup fails because @Primary and @Qualifier conflict"], 1,
"stripeGateway, because @Primary has the highest priority.",
r"""
`@Primary` is described as 'the default bean', and people read 'default' as 'overrides everything'. It's actually a
tie-breaker, used only when several candidates are still left. An explicit `@Qualifier` at the injection point is a
more specific request, so it filters the candidates first.
""",
r"""
Spring resolves by type first and finds both gateways. The `@Qualifier("razorpayGateway")` at the injection point then
filters the candidates down to the bean with that qualifier or name, so Razorpay is injected. `@Primary` matters only
when more than one candidate is left after qualifiers: an unqualified `PaymentGateway` parameter gets Stripe. With
neither annotation, Spring falls back to matching the parameter name against bean names, and if that fails it throws
`NoUniqueBeanDefinitionException`. Relying on parameter names is fragile.

For a strategy pattern you don't need to pick a bean at all. Inject `List<PaymentGateway>` (all beans, ordered by
`@Order`) or `Map<String, PaymentGateway>` (keyed by bean name) and choose at runtime. Spring Boot also disables bean
definition overriding by default, so two beans with the same name fail at startup.
""",
r"""
```java
@Service
public class CheckoutService {
    private final Map<String, PaymentGateway> gateways;   // {"stripeGateway"=..., "razorpayGateway"=...}

    public CheckoutService(Map<String, PaymentGateway> gateways) { this.gateways = gateways; }

    public Receipt pay(Order o) {
        String name = o.country().equals("IN") ? "razorpayGateway" : "stripeGateway";
        return gateways.get(name).charge(o);
    }
}
```
""",
"Show the Map<String, Bean> strategy injection. It turns a resolution-rules question into a design answer."),

T("trap-spring-transactional-readonly", A, "@Transactional(readOnly = true) misconceptions", "Intermediate", "Common",
r"""
Spring Boot 3, Hibernate, MySQL. What happens when this runs?

```java
@Transactional(readOnly = true)
public void deactivate(Long userId) {
    User u = userRepository.findById(userId).orElseThrow();
    u.setActive(false);
    userRepository.save(u);
}
```
""",
["An exception: 'cannot write in a read-only transaction'",
 "The change is saved; readOnly is only documentation",
 "No error, but the change is silently not saved",
 "Startup fails: save() can't be called from a read-only method"], 2,
"Either it throws an error, or readOnly is just a hint and the update goes through.",
r"""
Candidates treat readOnly as either a strict guard or a no-op. It's neither. It's an optimisation hint whose effect
depends on the stack. With Hibernate it turns off flushing and dirty checking, so entity changes simply never become
SQL: no error, no write, no log line.
""",
r"""
With JPA/Hibernate, Spring marks the session read-only and sets its flush mode to `MANUAL`. Hibernate keeps no
snapshots for dirty checking and never flushes, so `setActive(false)` produces no UPDATE. Calling `save()` doesn't
help: its own `@Transactional` joins the outer read-only transaction, and merging an already-managed entity changes
nothing. The method returns normally, and the change is lost.

Spring also marks the JDBC connection read-only, and some drivers enforce that. An explicit JPQL or native UPDATE
through MySQL Connector/J can fail with "Connection is read-only. Queries leading to data modification are not
allowed". Use `readOnly = true` on query methods: it saves memory (no snapshots) and CPU (no flush), and lets a routing
DataSource send queries to a replica. Never put it on a method that writes. A good, common pattern is read-only at
class level with writes overridden per method.
""",
r"""
```java
@Service
@Transactional(readOnly = true)           // class default: queries
public class UserService {

    public UserDto find(Long id) { /* ... */ }

    @Transactional                         // override for writes
    public void deactivate(Long userId) {
        userRepository.findById(userId).orElseThrow().setActive(false);   // flushed at commit by dirty checking
    }
}
```
""",
"Mention replica routing and Hibernate's skipped snapshots as the real benefits. That turns a gotcha into a performance answer."),

T("trap-spring-open-in-view", A, "Open Session in View (spring.jpa.open-in-view)", "Intermediate", "Common",
r"""
At startup Spring Boot logs a warning: `spring.jpa.open-in-view is enabled by default...`. Lazy collections load fine
in your controllers, but the same code throws `LazyInitializationException` in a `@Scheduled` job.

Why the difference? Should you leave open-in-view switched on?
""",
None, None,
"OSIV keeps a transaction open for the whole request, which is convenient and harmless, so leave it on.",
r"""
Because lazy loading 'just works' in controllers, people assume it's normal Hibernate behaviour, or that the
transaction lasts for the whole request. OSIV actually keeps the EntityManager (and, once it has one, a JDBC
connection) open for the whole HTTP request, **outside** any transaction. Scheduled jobs, message listeners and @Async
threads have no web request, so they get no such help.
""",
r"""
Boot registers `OpenEntityManagerInViewInterceptor` by default. It binds one EntityManager to the request thread, so
entities stay attached after the service transaction ends, and lazy associations load during controller code or JSON
serialization. Those loads run outside any transaction (auto-commit), one query per association: N+1 queries hidden
in your serializer. Once the request first touches the database, the connection is held until the response is
written, including during slow remote calls, so under load the pool runs dry. Dirty entities can also be flushed by a
later, unrelated transaction in the same request.

A `@Scheduled` job has no request, so its EntityManager closes together with the repository's transaction, and the
lazy access fails. Set `spring.jpa.open-in-view=false`, and load what each use case needs inside the service
transaction with fetch joins, `@EntityGraph` or DTO projections.
""",
r"""
```yaml
spring:
  jpa:
    open-in-view: false
```

```java
@Transactional(readOnly = true)
public OrderDetailsDto getOrder(Long id) {
    Order o = orderRepository.findWithItemsById(id).orElseThrow();  // @EntityGraph(attributePaths = "items")
    return OrderDetailsDto.from(o);                                  // map while the session is still open
}
```
""",
"Say you switch it off on new projects, and explain the connection-holding cost under load. That's the senior reason, not just 'it's an anti-pattern'."),

T("trap-spring-singleton-thread-safety", A, "Are Spring singleton beans thread-safe?", "Basic", "Very common",
r"""
Is this bean safe when 50 requests call `format()` at the same time? Are Spring beans thread-safe in general?

```java
@Service
public class InvoiceFormatter {
    private final SimpleDateFormat fmt = new SimpleDateFormat("dd-MM-yyyy");
    private final List<String> lines = new ArrayList<>();

    public String format(Invoice inv) {
        lines.clear();
        lines.add("Date: " + fmt.format(inv.date()));
        lines.add("Total: " + inv.total());
        return String.join("\n", lines);
    }
}
```
""",
None, None,
"Yes: Spring manages the bean's lifecycle, so its beans are thread-safe.",
r"""
Spring manages creation and wiring, so people assume it manages concurrency too. A singleton bean is one plain Java
object shared by every request thread, and Spring adds no locking. Code like this is fine in a single-threaded test
and fails only under concurrent load, which is exactly why it reaches production.
""",
r"""
Singleton scope means one instance per container, shared by all threads, and Spring does nothing to make it
thread-safe. Two kinds of shared mutable state break here under load. Many threads clear and fill `lines` at once, so
one customer's invoice can contain another's lines (or throw `ConcurrentModificationException`). And
`SimpleDateFormat` keeps internal mutable state, so concurrent `format`/`parse` calls produce wrong dates or
exceptions.

Stateless beans, holding only final references to other thread-safe beans and keeping per-call data in local
variables, are safe by design. That's why typical services and repositories are fine. Fixes: move per-call state into
local variables, use the immutable, thread-safe `DateTimeFormatter`, or use thread-safe structures when state really
must be shared. Changing the scope to prototype doesn't help if the bean is injected into a singleton.
""",
r"""
```java
@Service
public class InvoiceFormatter {
    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("dd-MM-yyyy"); // immutable

    public String format(Invoice inv) {                 // inv.date() is a LocalDate here
        List<String> lines = new ArrayList<>();          // per call, never shared
        lines.add("Date: " + FMT.format(inv.date()));
        lines.add("Total: " + inv.total());
        return String.join("\n", lines);
    }
}
```
""",
"Answer 'singletons are shared, so they must be stateless or guard their state', and name SimpleDateFormat as the classic real-world offender."),
]
