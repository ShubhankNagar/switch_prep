from senior1_common import build, B, I, A

NOTES = [
("The Test Pyramid in a Spring Boot Service", r"""
## The shape and why it matters
```text
                 /\        E2E / UI journeys      few      minutes   "can a user check out?"
                /  \
               /----\      Contract tests         some     seconds   "did we break the consumer's API?"
              /      \
             /--------\    Integration (real DB,  dozens   seconds   "does the SQL / migration /
            /          \   Kafka via Testcontainers)                  transaction really work?"
           /------------\  Slice tests (@WebMvcTest, @DataJpaTest)   "JSON, validation, queries"
          /              \
         /----------------\ Unit tests            hundreds milliseconds "is the business rule right?"
```
The idea (popularised by Mike Cohn; described in detail in Ham Vocke's *Practical Test Pyramid* on martinfowler.com): **many small, fast tests at the bottom, fewer slow, broad tests at the top.** Push each test as low as it can go while still catching the bug. Fast tests give feedback in seconds. Slow end-to-end suites become flaky and get ignored.

The anti-pattern is the **ice-cream cone**: mostly manual or UI tests, few unit tests, a 2-hour suite that nobody trusts.

## What each layer catches in a backend service
| Layer | Catches | Typical tools |
|---|---|---|
| Unit | Business rules, edge cases, calculations, state machines | JUnit 5, Mockito, AssertJ |
| Web slice | Request mapping, validation (400s), JSON shape, error handler, security rules | `@WebMvcTest`, MockMvc |
| Data slice | Custom queries, mappings, constraints | `@DataJpaTest` + Testcontainers |
| Integration | Real MySQL behaviour, Flyway migrations, transactions, Kafka wiring | `@SpringBootTest` + Testcontainers, WireMock |
| Contract | Field renamed, type changed, breaking consumers | Pact, Spring Cloud Contract |
| E2E / smoke | The deployed system wired together, config, infra | A few API journeys after deploy |

## A balanced view
For backend services that are mostly "HTTP in, SQL out", the expensive bugs live in the **integration seams**: the query, the transaction boundary, the JSON contract. Some teams use a "testing trophy" shape with a thicker integration middle. The interview-safe answer: **unit-test the logic, integration-test the seams with real dependencies, keep E2E minimal**, and choose based on where bugs actually happen in *your* service.

## Example: an order-service test plan
```text
Unit:         PricingService (discount rules, rounding), OrderStateMachine (allowed transitions),
              IdempotencyService (replay vs conflict)                          ~150 tests, <5 s
Web slice:    OrderController -> 201 / 400 validation / 404 / 409, ProblemDetail format
Data slice:   OrderRepository.findPageForUser (keyset query), unique(order_ref) constraint
Integration:  place order end-to-end with MySQL + Kafka containers; payment client against
              WireMock (success, timeout, 500); Flyway migrations run on a clean DB
Contract:     consumer contract from notification-service on the OrderPlaced event
Smoke:        after deploy: create test order, read it back, cancel it
```

## Principles of good tests
- **Test behaviour, not implementation.** Assert outcomes (return value, state, emitted event), not which private method was called. Then refactoring doesn't break the tests.
- **One reason to fail.** Each test checks one behaviour, and its name reads like a spec: `placeOrder_rejects_whenStockInsufficient()`.
- **Arrange, Act, Assert** (Given / When / Then) with clear blank-line separation.
- **Deterministic:** no real time, randomness, network or order dependence (see the chapter on flaky tests).
- **FIRST:** Fast, Isolated, Repeatable, Self-validating, Timely.
- **Don't test** trivial getters and setters, the framework itself, or private methods directly. If a private method needs its own tests, it probably wants to be its own class.

## In CI
```text
every push:    unit + slice tests                 (< 5 min, blocks merge)
every PR:      + integration with Testcontainers  (< 15 min)
pre-deploy:    contract verification, migration check
post-deploy:   smoke tests + canary metrics       (roll back automatically on failure)
```

## How to answer "How do you test your service?"
Name the layers, give one concrete example per layer from your project, mention **Testcontainers for real MySQL**, how you keep tests deterministic (injected `Clock`), and how the suite runs in CI. Interviewers mostly want to hear that you think about **what could break and where it's cheapest to catch**.
"""),

("Unit Testing with JUnit 5 and Mockito", r"""
## A complete, realistic example
```java
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class CouponServiceTest {
    // ---- production code (normally lives in src/main) ----
    record Coupon(String code, int percentOff, Instant expiresAt, boolean singleUse) {}
    interface CouponRepository { Optional<Coupon> findByCode(String code); void markUsed(String code); }
    static class CouponExpiredException extends RuntimeException {
        CouponExpiredException(String code) { super("coupon expired: " + code); }
    }
    static class CouponService {
        private final CouponRepository repo;
        private final Clock clock;                       // injected: tests control "now"
        CouponService(CouponRepository repo, Clock clock) { this.repo = repo; this.clock = clock; }

        BigDecimal apply(String code, BigDecimal total) {
            Coupon c = repo.findByCode(code)
                    .orElseThrow(() -> new IllegalArgumentException("unknown coupon " + code));
            if (!clock.instant().isBefore(c.expiresAt())) throw new CouponExpiredException(code);
            BigDecimal discount = total.multiply(BigDecimal.valueOf(c.percentOff()))
                    .divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
            if (c.singleUse()) repo.markUsed(code);
            return total.subtract(discount);
        }
    }

    // ---- tests ----
    static final Instant NOW = Instant.parse("2026-10-09T10:00:00Z");
    @Mock CouponRepository repo;
    CouponService service;

    @BeforeEach
    void setUp() { service = new CouponService(repo, Clock.fixed(NOW, ZoneOffset.UTC)); }

    @Test
    void appliesPercentageDiscount() {
        when(repo.findByCode("DIWALI10"))
                .thenReturn(Optional.of(new Coupon("DIWALI10", 10, NOW.plusSeconds(60), false)));

        BigDecimal result = service.apply("DIWALI10", new BigDecimal("999.00"));

        assertThat(result).isEqualByComparingTo("899.10");
        verify(repo, never()).markUsed(any());
    }

    @Test
    void rejectsCouponAtExactExpiryInstant() {                      // boundary value
        when(repo.findByCode("OLD")).thenReturn(Optional.of(new Coupon("OLD", 10, NOW, false)));
        assertThatThrownBy(() -> service.apply("OLD", BigDecimal.TEN))
                .isInstanceOf(CouponExpiredException.class).hasMessageContaining("OLD");
    }

    @Test
    void marksSingleUseCouponAsUsed() {
        when(repo.findByCode("ONCE")).thenReturn(Optional.of(new Coupon("ONCE", 50, NOW.plusSeconds(60), true)));
        service.apply("ONCE", new BigDecimal("200"));
        verify(repo).markUsed("ONCE");
    }

    @ParameterizedTest(name = "{0}% off {1} = {2}")
    @CsvSource({"10, 100.00, 90.00", "15, 99.99, 84.99", "100, 50.00, 0.00", "0, 50.00, 50.00"})
    void roundsHalfUpToPaise(int percent, String total, String expected) {
        when(repo.findByCode("X")).thenReturn(Optional.of(new Coupon("X", percent, NOW.plusSeconds(60), false)));
        assertThat(service.apply("X", new BigDecimal(total))).isEqualByComparingTo(expected);
    }
}
```
Things worth pointing out in an interview: the **injected `Clock`**, the **boundary test** (expiry at the exact instant), **parameterised cases** for rounding, `isEqualByComparingTo` for `BigDecimal` (`equals` would treat `90.0` and `90.00` as different), and **verifying a side effect only where it is the behaviour** (`markUsed`).

## Test doubles: get the vocabulary right
| Double | What it is | Example |
|---|---|---|
| Dummy | Passed in, never used | `null` or a placeholder argument |
| Stub | Returns canned answers | `when(repo.findByCode(..)).thenReturn(..)` |
| Spy | A real object that records calls (and can be partly stubbed) | `Mockito.spy(realList)` |
| Mock | Pre-programmed with expectations you verify | `verify(email).send(..)` |
| Fake | A working lightweight implementation | `InMemoryOrderRepository` backed by a `HashMap` |

## Mockito habits that keep tests healthy
- **Mock roles, not values.** Don't mock records, DTOs or `BigDecimal`. Build real ones.
- **Don't mock what you don't own.** Wrap the HTTP client or SDK in your own `PaymentGateway` interface and mock *that*. Test the adapter itself against WireMock.
- **Prefer fakes** for stateful collaborators used heavily (an in-memory repository). Long `when(...)` chains are a smell.
- **Verify sparingly.** Verify interactions that *are* the behaviour (an email was sent, a payment was charged once), not every call. Over-verification makes tests break on harmless refactors.
- `MockitoExtension` uses **strict stubs**: unused stubbing fails the test, which keeps tests honest.
- `ArgumentCaptor` when you need to inspect a complex argument (the event published); otherwise pass the expected value to `verify`.
- If a class needs 7 mocks to test, that's **design feedback**: it has too many responsibilities.

## Naming and structure
`methodUnderTest_expectedOutcome_whenCondition`, or a sentence with `@DisplayName`. Use `@Nested` classes to group cases ("when coupon expired", "when coupon single-use"). A reader should understand the rule from the test names alone.
"""),

("Spring Test Slices, Testcontainers and WireMock", r"""
## Choose the smallest context that can catch the bug
| Annotation | Loads | Speed | Use for |
|---|---|---|---|
| none (plain JUnit) | Nothing | ms | Services and domain logic with mocks or fakes |
| `@WebMvcTest(X.class)` | MVC layer for controller X: filters, advice, converters, validation | ~1-2 s | Status codes, validation, JSON shape, exception handlers, security rules |
| `@DataJpaTest` | JPA, repositories, DataSource, Flyway/Liquibase | ~2-5 s | Custom queries, mappings, constraints |
| `@JsonTest`, `@RestClientTest` | Jackson or the HTTP client slice | fast | Serialisation details, client mapping |
| `@SpringBootTest` | Whole application context | slowest | End-to-end flows inside the service |

## Web slice
```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mvc;
    @MockitoBean OrderService orderService;       // Spring Framework 6.2 / Boot 3.4+ (replaces @MockBean)

    @Test
    void returns201WithLocation() throws Exception {
        when(orderService.place(any())).thenReturn(new OrderView(42L, "PLACED"));
        mvc.perform(post("/api/orders").contentType(APPLICATION_JSON)
                .content("{\"sku\":\"PEN-1\",\"qty\":2}"))
           .andExpect(status().isCreated())
           .andExpect(header().string("Location", endsWith("/api/orders/42")))
           .andExpect(jsonPath("$.status").value("PLACED"));
    }

    @Test
    void rejectsNonPositiveQuantityWithProblemDetail() throws Exception {
        mvc.perform(post("/api/orders").contentType(APPLICATION_JSON)
                .content("{\"sku\":\"PEN-1\",\"qty\":0}"))
           .andExpect(status().isBadRequest())
           .andExpect(jsonPath("$.title").value("Validation failed"));   // set by our @RestControllerAdvice
        verifyNoInteractions(orderService);
    }
}
```
With Spring Security on the classpath, add `@WithMockUser` or `.with(jwt())` and test the **403 for the wrong role** too. Authorization rules are code, so they need tests.

## Data slice with a real MySQL
```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)   // don't swap in H2
@Testcontainers
class OrderRepositoryTest {
    @Container @ServiceConnection
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");

    @Autowired OrderRepository repo;
    @Autowired TestEntityManager em;

    @Test
    void duplicateOrderRefViolatesUniqueConstraint() {
        repo.saveAndFlush(new Order("REF-1"));
        assertThatThrownBy(() -> repo.saveAndFlush(new Order("REF-1")))
                .isInstanceOf(DataIntegrityViolationException.class);
    }
}
```
Notes:
- `@DataJpaTest` runs each test in a transaction that's **rolled back** afterwards, so tests stay isolated. Call `flush()` to force SQL (and constraint checks) to run inside the test.
- **Why not H2?** Different SQL dialect, functions, JSON columns, locking, `SKIP LOCKED`, collations and index behaviour. Tests pass on H2 and fail on MySQL, or the reverse. Testcontainers gives production parity, and your Flyway migrations get tested for free.
- `@ServiceConnection` (Boot 3.1+) wires the container's URL and credentials automatically.

## Full integration with external HTTP faked
```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class CheckoutFlowIT {
    @Container @ServiceConnection static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");
    @RegisterExtension static WireMockExtension payment = WireMockExtension.newInstance().build();

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry r) { r.add("payment.base-url", payment::baseUrl); }

    @Test
    void paymentTimeoutLeavesOrderPendingAndRetriable() {
        payment.stubFor(post("/charges").willReturn(ok().withFixedDelay(5_000)));   // slower than our 2 s timeout
        // act: call POST /api/checkout ... assert 202 + order status PENDING_PAYMENT, no duplicate charge
    }
}
```
WireMock lets you test the **unhappy paths** that are impossible to trigger against a real partner: timeouts, 500s, malformed bodies, slow responses. That's where resilience bugs hide.

## Keep the suite fast
- **Context caching:** Spring reuses an application context across test classes with the *same* configuration. Every distinct set of `@MockitoBean`s or properties creates a new context. `@DirtiesContext` throws the cache away, so use it rarely.
- **Singleton containers:** start MySQL once per JVM (a static container in a shared base class) rather than per class.
- Run unit and slice tests on every build; tag slower ones (`@Tag("integration")`) for a separate stage if needed.

## What interviewers want to hear
"Controllers with `@WebMvcTest` for status codes, validation and error format; repositories with `@DataJpaTest` against Testcontainers MySQL; one or two `@SpringBootTest` flows with WireMock for the payment provider, including timeout and 500 cases; plain unit tests for business rules." That's a complete, credible answer.
"""),

("Contract Tests and Testing Time, Async and Flaky Tests", r"""
## Contract tests: catching breaking API changes early
Microservices break each other in a familiar way: provider team renames `totalAmount` to `amount`, all *their* tests pass, and the consumer fails in production. End-to-end tests could catch it, but they're slow, flaky and need every service deployed.

**Consumer-driven contracts:** the consumer writes down what it needs (request, response fields and types). The provider's build **verifies** it can satisfy every consumer contract.
- **Pact:** the consumer test produces a pact file, a broker shares it, and provider verification runs in the provider's CI.
- **Spring Cloud Contract:** contracts (Groovy/YAML) in the provider generate both provider tests and consumer stubs.
- The same idea applies to **events**: the shape of a Kafka message is an API too. Schema registries (Avro/Protobuf with compatibility rules) are a form of contract enforcement.

Use them when several teams own services that evolve independently. With two services owned by the same team, good integration tests plus backward-compatible change rules may be enough.

## Testing time
```java
// Production: one Clock bean
@Bean Clock clock() { return Clock.systemUTC(); }

// Code under test asks the clock, never LocalDateTime.now()
boolean isExpired(Subscription s) { return !Instant.now(clock).isBefore(s.renewAt()); }

// Tests: fixed, or a mutable clock you advance
Clock fixed = Clock.fixed(Instant.parse("2026-03-29T01:30:00Z"), ZoneOffset.UTC);
```
- Test **boundaries**: exactly at expiry, one millisecond before or after, month ends, leap days, DST transitions in the user's zone (store `Instant`, convert at the edges).
- For random IDs, inject a `Supplier<UUID>` or a seeded `Random`.

## Testing async code
```java
await().atMost(Duration.ofSeconds(5))
       .untilAsserted(() -> assertThat(orderRepo.findByRef("R-1")).hasValueSatisfying(
               o -> assertThat(o.getStatus()).isEqualTo(PAID)));
```
- **Never `Thread.sleep(2000)` in tests.** It's slow when things are fast and flaky when CI is slow. Awaitility polls until a condition holds or a timeout expires.
- Unit-test the logic **synchronously** (call the listener method directly), then add one integration test proving the wiring (a real Kafka container).
- For consumers, test **idempotency**: deliver the same message twice and assert one effect.

## Testing retries and backoff without slow tests
Inject the waiting strategy so tests don't actually sleep:
```java
interface Sleeper { void sleep(Duration d) throws InterruptedException; }
// test: a recording sleeper -> assert delays were [100ms, 200ms, 400ms] (+/- jitter bounds)
// and the gateway was called exactly 4 times, then gave up with the last exception
```
Also test **what is not retried**: a 400 or validation error should fail immediately, with one call.

## Flaky tests: causes and fixes
| Cause | Symptom | Fix |
|---|---|---|
| Shared state / order dependence | Passes alone, fails in the suite | Fresh fixtures per test, no static mutable state, random ordering to expose it |
| Real time / timezone | Fails at midnight, month end or in CI's UTC | Inject `Clock`, pin the timezone |
| Sleeps for async | Fails on a slow CI machine | Awaitility with a condition |
| Concurrency races (real bugs!) | 1-in-50 failures | Treat as a product bug; reproduce with repetition |
| External services | Network blips | WireMock / Testcontainers, never real third parties |
| Data collisions | Unique constraint errors in parallel runs | Unique test data per test (random suffixes) |
| Leaky Spring context | Tests affect each other through cached beans | Reset fakes, avoid mutable singletons |

**Process:** reproduce first (`@RepeatedTest(100)`, run the class in a loop, randomise order). Quarantine with a ticket and an owner if it blocks the team, and **never "fix" it by adding automatic retries**. A flaky test is either a bad test or a real race. Both deserve a fix.
"""),

("Tests in Practical Coding Rounds (and Honest TDD)", r"""
## What the round grades
Practical rounds (TTL cache, rate limiter, task scheduler, idempotent webhook handler, booking service) look for **decomposition, correctness, tests, handling changing requirements and communication**. In AI-assisted rounds you're also graded on **verifying** generated code. Tests are the evidence that you did.

## A 60-minute plan
```text
00-05  clarify: inputs, outputs, limits, concurrency, failure behaviour  -> say test cases out loud
05-12  API + skeleton: class names, method signatures, data structures
12-40  implement in small steps; after each step run 1-2 tests (happy path first, then edges)
40-52  requirement change ("now add per-key TTL" / "make it thread-safe") -> tests first, then code
52-60  walk through edge cases, complexity, what you'd add with more time
```

## Say the test list before coding
For "LRU cache with TTL and capacity", list:
1. get after put returns the value
2. get of a missing key returns empty
3. an entry expires **exactly** at TTL (boundary)
4. a full cache evicts the **least recently used** entry, not the oldest inserted
5. a get refreshes recency
6. overwriting a key resets its TTL and doesn't grow the size
7. invalid inputs: null key, capacity 0
8. thread safety under concurrent puts and gets (follow-up)

That list turns ambiguity into agreed behaviour. It also shows the interviewer you think about edges before writing code.

## A complete example with injectable time
```java
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.LongSupplier;
import org.junit.jupiter.api.Test;

class TtlCacheTest {

    /** LRU + TTL cache. synchronized keeps it simple and thread-safe for the follow-up question. */
    static final class TtlCache<K, V> {
        private record Entry<T>(T value, long expiresAtMillis) {}

        private final int capacity;
        private final long ttlMillis;
        private final LongSupplier clock;
        private final LinkedHashMap<K, Entry<V>> map;

        TtlCache(int capacity, Duration ttl, LongSupplier clock) {
            if (capacity <= 0) throw new IllegalArgumentException("capacity must be > 0");
            this.capacity = capacity;
            this.ttlMillis = ttl.toMillis();
            this.clock = clock;
            this.map = new LinkedHashMap<>(16, 0.75f, true) {              // access order => LRU
                @Override
                protected boolean removeEldestEntry(Map.Entry<K, Entry<V>> eldest) {
                    return size() > TtlCache.this.capacity;
                }
            };
        }

        synchronized void put(K key, V value) {
            Objects.requireNonNull(key, "key");
            map.put(key, new Entry<>(value, clock.getAsLong() + ttlMillis));
        }

        synchronized Optional<V> get(K key) {
            Entry<V> e = map.get(key);
            if (e == null) return Optional.empty();
            if (clock.getAsLong() >= e.expiresAtMillis()) {                 // lazy expiry
                map.remove(key);
                return Optional.empty();
            }
            return Optional.ofNullable(e.value());
        }

        synchronized int size() { return map.size(); }
    }

    long now = 1_000;
    final TtlCache<String, String> cache = new TtlCache<>(2, Duration.ofSeconds(10), () -> now);

    @Test void returnsValueBeforeExpiry() {
        cache.put("a", "1");
        now += 9_999;
        assertThat(cache.get("a")).contains("1");
    }

    @Test void expiresExactlyAtTtl() {
        cache.put("a", "1");
        now += 10_000;
        assertThat(cache.get("a")).isEmpty();
    }

    @Test void evictsLeastRecentlyUsedNotOldestInserted() {
        cache.put("a", "1");
        cache.put("b", "2");
        cache.get("a");                 // a becomes most recently used
        cache.put("c", "3");            // evicts b
        assertThat(cache.get("b")).isEmpty();
        assertThat(cache.get("a")).contains("1");
        assertThat(cache.get("c")).contains("3");
    }

    @Test void overwriteResetsTtlWithoutGrowing() {
        cache.put("a", "1");
        now += 8_000;
        cache.put("a", "2");
        now += 8_000;
        assertThat(cache.get("a")).contains("2");
        assertThat(cache.size()).isEqualTo(1);
    }

    @Test void rejectsInvalidInput() {
        assertThatThrownBy(() -> cache.put(null, "x")).isInstanceOf(NullPointerException.class);
        assertThatThrownBy(() -> new TtlCache<String, String>(0, Duration.ofSeconds(1), () -> 0L))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
```
Talking points: time is a `LongSupplier`, so the tests run instantly and deterministically. Expired entries are removed **lazily** and still count toward capacity until touched (mention a periodic sweep as a follow-up). `synchronized` is simple and correct; for high read concurrency, discuss lock striping or Caffeine. If the round has no JUnit, write a `main` with small `check(condition, message)` helpers. The habit matters more than the framework.

## Edge-case checklist
Empty or null input, a single element, duplicates, boundaries (exactly at a limit, off by one), capacity 0 or 1, very large inputs, unicode or case, negative numbers, time boundaries, concurrent calls, failure of a dependency, and retries of the same request.

## TDD, honestly
**Red, green, refactor:** write a failing test, make it pass with the simplest code, then clean up with the tests as a safety net. Where it shines: logic-heavy code with clear rules (pricing, state machines, parsers), bug fixes (write the failing test that reproduces the bug first), and interviews, where test-first for the core rule shows discipline. Where strict TDD is less natural: exploratory spikes and UI layout. A credible answer: "I write tests first for business rules and bug fixes, and test-after for wiring code, but nothing merges without tests for the behaviour it changes."
"""),

("The Code Review Round: How to Review Out Loud", r"""
## The format
You get a pull request or a class (often a flawed Spring service, controller or scheduled job, 50-300 lines) and 30-45 minutes. You talk through it. Variants: "debug this code" (find why it fails) and "review this AI-generated change". The 2026 rubric rewards **ranking findings by production risk**, putting **correctness before style**, and making **specific, actionable** comments in a collaborative tone.

## The review order
```text
  1. INTENT          what is this change supposed to do? (read the description, tests, names)
  2. CORRECTNESS     does it do that? happy path, error paths, transactions, data integrity
  3. EDGE CASES      null/empty, zero/negative, boundaries, duplicates, large inputs, time zones
  4. CONCURRENCY     shared mutable state, check-then-act, idempotency, multiple instances
  5. SECURITY        authz (IDOR), injection, mass assignment, secrets/PII in logs, validation
  6. PERFORMANCE     N+1, findAll, unbounded results, remote calls in loops/transactions
  7. OPERABILITY     logging, metrics, timeouts, retries, error responses, config
  8. READABILITY     naming, structure, duplication, tests (are the risky paths tested?)
```
This order is about **risk**: a data-corruption bug matters more than a badly named variable, so look for it first and talk about it first.

## Severity tiers
| Tier | Meaning | Examples |
|---|---|---|
| **Blocker** | Can lose or corrupt data or money, breach security, or cause an outage | Missing transaction around debit and credit, SQL injection, IDOR, double charge on retry |
| **Major** | Real bug or scalability problem under realistic conditions | N+1 on a list endpoint, swallowed exceptions, no timeout on a remote call, missing tests for the critical path |
| **Minor** | Maintainability, clarity, small inefficiencies | Field injection, magic numbers, vague error messages |
| **Nit** | Style and taste | Formatting, naming preferences. Prefix with "nit:" or let the formatter handle it |

## Checklist prompts
- **Correctness:** `Optional.get()`, `==` on objects, `BigDecimal.equals`, money as `double`, off-by-one, missing `else`, exceptions swallowed, `@Transactional` on private or self-invoked methods, partial writes.
- **Concurrency:** mutable fields in singleton beans, `HashMap` shared across threads, check-then-act on the DB, retries without idempotency, `@Scheduled` on N instances.
- **Security:** string-concatenated SQL or JPQL, entities returned directly (leaking fields), `@RequestBody Entity` (mass assignment), missing ownership checks, logging tokens, cards or passwords, missing input limits.
- **Performance:** queries in loops, `findAll()` then filtering in Java, no pagination, remote calls inside transactions, unbounded caches or queues.
- **Operability:** no timeout, retry storms, `printStackTrace`, logs with no IDs, wrong HTTP status codes.

## Writing comments that get acted on
Each comment states **where**, **what's wrong**, **why it matters** (impact) and **a suggested fix**, or asks a question when you lack context.

| Weak | Strong |
|---|---|
| "This is wrong." | "**Blocker:** `transfer()` saves the debit, calls `notificationClient`, then saves the credit, with no transaction. If the HTTP call throws, the debit commits and the credit is lost. Suggest `@Transactional` on `transfer()` and sending the notification after commit (`@TransactionalEventListener`)." |
| "Use better names." | "**Minor:** `process(List<Object> l)` hides intent. `applyRefunds(List<RefundRequest> requests)` would make the call sites self-explanatory." |
| "Why not use a cache?" | "**Question:** this endpoint is called on every page load and runs 3 queries. Is caching the category tree (changes rarely) acceptable for 5 minutes?" |

Tone: comment on the **code, not the person** ("this method" instead of "you forgot"). Acknowledge good parts ("nice use of a keyset query here"). Distinguish **must-fix** from **suggestions**.

## Managing the 30-45 minutes
1. **Skim everything first** (2-3 minutes). Don't start nitpicking line 1.
2. **State the intent** back: "This endpoint transfers money between wallets and notifies the user."
3. **Call out the top blockers early**, so time pressure doesn't hide them.
4. Go deeper by category; ask clarifying questions ("Is this API public?", "How many rows can this table have?").
5. **Finish with a ranked summary:** "Three blockers: no transaction, no authorization, double spend under concurrency. Then money as double, missing idempotency, swallowed exceptions. Then minors." Suggest the **tests** you'd want to see.

## Common mistakes
Leading with formatting. Listing 25 issues with no priority. Vague comments with no fix. Rewriting the whole design in the review instead of the essentials. Missing security entirely. Never mentioning tests.
"""),

("Review Exercises: Flawed Spring Code, Findings Ranked", r"""
Try each one yourself first: set a 10-minute timer, write your findings in priority order, then compare.

## Exercise 1: wallet transfer
```java
@RestController
public class WalletController {
    @Autowired WalletService walletService;

    @PostMapping("/wallets/transfer")
    public String transfer(@RequestParam Long from, @RequestParam Long to, @RequestParam double amount) {
        try {
            walletService.transfer(from, to, amount);
            return "SUCCESS";
        } catch (Exception e) {
            e.printStackTrace();
            return "FAILED";
        }
    }
}

@Service
public class WalletService {
    @Autowired WalletRepository repo;
    @Autowired NotificationClient notificationClient;

    public void transfer(Long from, Long to, double amount) {
        Wallet src = repo.findById(from).get();
        Wallet dst = repo.findById(to).get();
        if (src.getBalance() >= amount) {
            src.setBalance(src.getBalance() - amount);
            dst.setBalance(dst.getBalance() + amount);
            repo.save(src);
            notificationClient.send(src.getUserId(), "Debited " + amount);   // HTTP call
            repo.save(dst);
        }
    }
}
```
**Ranked findings**
1. **Blocker, data integrity:** no transaction. `save(src)` commits, then an HTTP call, then `save(dst)`. If the notification throws or the pod dies, money is debited and never credited. Fix: `@Transactional` on `transfer()`, and send the notification **after commit** (event plus `@TransactionalEventListener`, or an outbox).
2. **Blocker, security (IDOR):** `from` comes from the request and nothing checks that the authenticated user owns that wallet. Anyone can drain anyone's wallet. Fix: derive the source wallet from the principal, or verify ownership.
3. **Blocker, concurrency:** read-check-write on balances. Two concurrent transfers both pass `balance >= amount`, so the wallet can be double-spent. Fix: conditional update (`UPDATE wallet SET balance = balance - ? WHERE id = ? AND balance >= ?`), or `@Version` / `SELECT ... FOR UPDATE` with **consistent lock ordering** to avoid deadlocks.
4. **Major, validation:** negative or zero `amount` is accepted (a negative transfer *steals* money), `from == to`, NaN. Fix: `@Positive`, `@Digits` and a same-wallet check.
5. **Major, money type:** `double` causes rounding errors (`0.1 + 0.2`). Use `BigDecimal` with a fixed scale, or `long` paise.
6. **Major, idempotency:** a client retry after a timeout performs a second transfer. Require an `Idempotency-Key`.
7. **Major, API and error handling:** insufficient funds silently does nothing and returns **"SUCCESS"** (there's no `else`!). All exceptions become HTTP 200 "FAILED". `printStackTrace` bypasses logging. Fix: domain exceptions mapped by `@RestControllerAdvice` to 422/404/409, a JSON response body, and structured logging.
8. **Minor:** `Optional.get()` throws `NoSuchElementException`, giving a 500. Use `orElseThrow(() -> new WalletNotFound(id))`, mapped to 404.
9. **Minor:** field injection. Use constructor injection (final fields, easy to test).

**Tests I'd ask for:** concurrent transfers can't overdraw; a failure after the debit rolls everything back; another user's wallet gets 403; negative amounts get 400; a retry with the same key performs one transfer.

## Exercise 2: order service with a "cache"
```java
@Service
public class OrderService {
    private static Map<Long, Order> cache = new HashMap<>();
    @Autowired OrderRepository orderRepository;
    @Autowired PaymentClient paymentClient;

    public Order getOrder(Long id) {
        if (!cache.containsKey(id)) cache.put(id, orderRepository.findById(id).orElse(null));
        return cache.get(id);
    }

    public void placeOrders(List<OrderRequest> requests) {
        for (OrderRequest r : requests) placeOrder(r);
    }

    @Transactional
    public void placeOrder(OrderRequest r) {
        Order o = orderRepository.save(new Order(r));
        paymentClient.charge(r.cardNumber(), r.amount());
        log.info("Charged card " + r.cardNumber() + " for order " + o.getId());
    }
}
```
**Ranked findings**
1. **Blocker, security/compliance:** the full card number is logged (PCI DSS violation, and logs spread everywhere). Never log PANs. Better still, the service shouldn't handle raw card numbers at all: use the provider's tokens.
2. **Blocker, transactions:** `placeOrders` calls `placeOrder` via `this`, so the **proxy is bypassed and `@Transactional` doesn't apply**. Each save auto-commits, so a charge failure leaves orders without payment. Even when the annotation does apply, the HTTP charge runs **inside** the transaction: if the charge succeeds and the commit fails, the customer is charged with no order. Fix: persist the order as `PENDING` (commit), charge with an **idempotency key**, then mark it `PAID`, with a reconciliation job for stuck states.
3. **Blocker, concurrency and memory:** a `static HashMap` shared by all request threads isn't thread-safe (lost entries, corrupted buckets), is **unbounded** (memory leak), is **never invalidated** (stale order status forever) and **caches nulls** for missing IDs. Fix: remove it, or use Caffeine/`@Cacheable` with size and TTL limits and eviction on update.
4. **Major, idempotency:** retrying `placeOrders` double-charges. Use a key per order.
5. **Major, partial batch failure:** one failing request aborts the loop midway, with no per-item result. Return per-item outcomes, or process items independently.
6. **Minor:** string concatenation in logging (use `{}` placeholders), `orElse(null)` returning null to callers (use `Optional` or throw 404), field injection.

**Tests I'd ask for:** a payment failure leaves the order `PENDING_PAYMENT`, not `PAID`; a retry with the same key charges once; a log-capture test asserts no card number appears.
"""),

("Clean Code and Refactoring Signals Interviewers Look For", r"""
## What interviewers notice in your code
In machine-coding and practical rounds, interviewers read your code the way a reviewer would:
- **Names that reveal intent:** `reserveSeats`, `RefundPolicy`, `isEligibleForFreeShipping()`, rather than `process`, `data` or `flag2`.
- **Small, focused methods** that do one thing at one level of abstraction.
- **Domain types:** `enum OrderStatus`, `record Money(BigDecimal amount, Currency currency)`, not raw strings and doubles.
- **Immutability by default:** records, `final` fields, unmodifiable collections returned.
- **Clear layering:** thin controller (HTTP concerns), service (business rules, transactions), repository (data access).
- **Explicit errors:** domain exceptions, no swallowed exceptions, no `null` returns where `Optional` or an exception fits.
- **Testability:** dependencies injected through constructors, time and randomness injected, side effects at the edges.

## Smell -> refactoring
| Smell | Signal | Refactoring |
|---|---|---|
| Long method | Scrolling, comments separating "sections" | Extract method, with names replacing the comments |
| Deep nesting | `if` inside `if` inside `for` | Guard clauses, early return, extract method |
| Switch on type repeated in many places | `if (type == GOLD) ... else if (type == SILVER)` everywhere | Polymorphism or a strategy map |
| Primitive obsession | `String email`, `double amount`, `int status` | Value objects (`Email`, `Money`), enums |
| Long parameter list / boolean flags | `create(a, b, c, d, true, false)` | Parameter object or record, separate methods instead of flags |
| Feature envy | A method mostly uses another object's data | Move the method to that object |
| God class | `OrderService` with 3,000 lines and 15 dependencies | Split by responsibility (pricing, payment, fulfilment) |
| Duplicated logic | The same validation in 4 places | Extract one function or validator |
| Shotgun surgery | One change touches 10 files | Bring related behaviour together |
| Comments explaining *what* | `// loop over items and add tax` | Better names; keep comments for *why* |

## Before and after
```java
// Before: nested conditionals, magic numbers, mixed concerns
public double shippingFee(Order o) {
    if (o != null) {
        if (o.getItems().size() > 0) {
            if (o.getCustomer().getTier().equals("GOLD")) {
                return 0;
            } else {
                if (o.getTotal() > 499) return 0;
                else return o.isExpress() ? 99 : 40;
            }
        }
    }
    return 0;
}
```
```java
// After: guard clauses, named rules, domain types
private static final Money FREE_SHIPPING_THRESHOLD = Money.inr("499");
private static final Money STANDARD_FEE = Money.inr("40");
private static final Money EXPRESS_FEE = Money.inr("99");

public Money shippingFee(Order order) {
    Objects.requireNonNull(order, "order");
    if (order.isEmpty()) return Money.ZERO;
    if (order.customer().tier() == Tier.GOLD) return Money.ZERO;
    if (order.total().isGreaterThan(FREE_SHIPPING_THRESHOLD)) return Money.ZERO;
    return order.isExpress() ? EXPRESS_FEE : STANDARD_FEE;
}
```
Each rule is now one readable line, easy to test separately, and the money type stops `double` rounding bugs. The original also hid a bug: a `null` order quietly cost **0** instead of failing.

## Refactoring safely
1. **Tests first.** If none exist, write **characterisation tests** that pin current behaviour (even the odd parts) before changing anything.
2. **Small steps:** rename, extract, move, one at a time, running the tests after each.
3. **Separate refactoring from behaviour changes:** different commits or PRs, so reviewers can check each.
4. Use the IDE's automated refactorings (rename, extract method, inline, change signature). They're safer than hand edits.

## When not to refactor
During an incident. Without tests on risky code. In a big-bang rewrite with no incremental path. When the code is stable, rarely touched and the change brings no value. And not as style churn mixed into a feature PR.

## The opposite failure: over-engineering
Interviewers also penalise **premature abstraction**: five interfaces with one implementation each, a `StrategyFactoryProvider` for two cases, generic frameworks for a 45-minute problem. Aim for the **simplest design that's easy to change**, and mention where you'd add an extension point if requirement X arrives. YAGNI and SOLID both apply. Saying which one you're applying, and why, is the senior signal.
"""),
]

QA = [
("Explain the test pyramid. How would you apply it to a Spring Boot microservice?", r"""
**The idea:** many fast, focused tests at the bottom and fewer slow, broad ones at the top. Push each test to the **lowest level that can catch the bug**, because low-level tests are fast, precise and stable. The anti-pattern is the ice-cream cone (mostly E2E or manual).

**For an order-service:**
- **Unit (hundreds, milliseconds):** pricing rules, state machine transitions, idempotency logic. JUnit 5 plus Mockito or fakes, with time injected through `Clock`.
- **Web slice (`@WebMvcTest`):** status codes, validation 400s, error-response format, security rules (403 for the wrong role).
- **Data slice (`@DataJpaTest` + Testcontainers MySQL):** custom queries, constraints, mappings, migrations.
- **Integration (`@SpringBootTest` + Testcontainers + WireMock):** a few full flows, including payment **timeouts and 500s**, transaction rollback, Kafka publishing.
- **Contract tests:** with consumers of our API or events (Pact / Spring Cloud Contract).
- **E2E / smoke:** a handful of critical journeys after deploy.

**Balance:** in CRUD-heavy services the costly bugs live at the seams (SQL, transactions, JSON), so I keep a solid integration layer with **real dependencies**, not just unit tests with mocks. Unit and slice tests run on every push in under 5 minutes; integration tests on every PR.
""", B, ["test-pyramid", "strategy", "spring"], True),

("Unit test vs integration test: where do you draw the line?", r"""
**Unit test:** checks one unit of behaviour (a class or a small cluster) **in isolation from I/O**: no database, network, filesystem or Spring context. Collaborators are mocks, stubs or fakes. It runs in milliseconds and fails for one clear reason.

**Integration test:** checks that components work **together with real infrastructure or framework wiring**: the SQL against real MySQL, Jackson serialisation through MockMvc, transaction boundaries, Kafka consumers, an HTTP client against WireMock.

**The practical line:** *Does the test cross a process or I/O boundary, or rely on framework behaviour?* Then it's an integration test, and it should use the **real** thing where it matters (Testcontainers MySQL, not H2).

**Choosing:**
- Business rules and edge cases → unit tests (cheap to cover many cases).
- "Does this query return the right rows and use the constraint?" → integration. Mocking the repository proves nothing about the SQL.
- "Does the endpoint return 400 with a ProblemDetail?" → a web slice test (a narrow integration test).

Note the "solitary vs sociable" distinction: a sociable unit test uses real collaborators (say, a real `PriceCalculator` inside `OrderService`) but still no I/O. That's often better than mocking everything, because tests survive refactoring.
""", B, ["unit-testing", "integration-testing"], True),

("What's the difference between a mock, a stub, a spy and a fake?", r"""
These are the test doubles from Gerard Meszaros' taxonomy:

- **Dummy:** passed only to satisfy a signature, never used.
- **Stub:** returns **canned answers** to calls; you assert on the result of the code under test. `when(repo.findById(1L)).thenReturn(Optional.of(order))`.
- **Mock:** an object with **expectations about interactions**, verified afterwards. `verify(emailClient).sendReceipt("O-1")`. Use it when the interaction itself *is* the behaviour (an email sent, a charge made once).
- **Spy:** wraps a **real object**, records calls and can override some methods. `Mockito.spy(realService)`. Useful with legacy code; often a design smell otherwise.
- **Fake:** a **working lightweight implementation**: `InMemoryOrderRepository` backed by a `HashMap`, an in-memory message bus. Great for stateful collaborators used across many tests; less brittle than long chains of stubbing.

(Mockito creates "mocks" for all of these; the names describe *how you use* the double.)

**Guidelines:**
- Stub queries, mock commands: verify side effects, not getters.
- Don't mock value objects or types you don't own (wrap third-party clients behind your own interface).
- Too many mocks in one test usually signals a class with too many responsibilities.
""", B, ["mockito", "test-doubles"], True),

("When does mocking hurt more than it helps?", r"""
1. **Mocking the thing you're actually testing:** mocking `OrderRepository` in a test that's meant to prove the query works. The test passes and the SQL is still broken. Use `@DataJpaTest` with Testcontainers.
2. **Over-specification:** `verify` on every call, in order. Any harmless refactor (caching a value, merging two calls) breaks the tests even though behaviour is unchanged. Tests should pin **behaviour**, not implementation.
3. **Mocking types you don't own:** stubbing `RestTemplate` or an AWS SDK encodes *your assumptions* about the library. Wrap it in your own `PaymentGateway` interface, mock that in service tests, and test the adapter against WireMock.
4. **Mocking value objects or data:** mocks for DTOs, `BigDecimal` or `List`. Just construct real ones.
5. **Deep stub chains:** `when(a.getB().getC().getD())`. This signals Law-of-Demeter violations; fix the design.
6. **Mock-heavy setup** (7 mocks, 30 lines of `when`) that's harder to read than the code. A fake or a slice test is usually clearer.
7. **False confidence:** a fully mocked suite where every unit passes, but the units don't fit together (wrong JSON field, wrong transaction boundary).

**Rule of thumb:** mock at **architectural boundaries** (outbound ports: payment, email, clock), use real objects inside the domain, and back it up with a few integration tests through the real seams.
""", I, ["mockito", "test-design"], False),

("@WebMvcTest vs @DataJpaTest vs @SpringBootTest: when do you use each?", r"""
**`@WebMvcTest(OrderController.class)`:** loads only the MVC layer for that controller: controller, `@ControllerAdvice`, filters, Jackson, validation, security config. Services are replaced with `@MockitoBean`. Test **HTTP concerns**: routes, status codes, request validation (400), JSON shape, error format, authorization rules. Fast (about a second).

**`@DataJpaTest`:** loads JPA, repositories, the DataSource and migrations. It runs each test in a transaction that's **rolled back**. By default it swaps in an embedded DB, so add `@AutoConfigureTestDatabase(replace = NONE)` with **Testcontainers MySQL** for real behaviour. Test **custom queries, mappings, constraints and migrations**. Remember to `flush()` so SQL actually executes.

**`@SpringBootTest`:** the **full application context** (optionally with a real server on `RANDOM_PORT`). Use it for **end-to-end flows inside the service**: controller → service → DB → Kafka, transaction boundaries, configuration wiring, with Testcontainers and WireMock for external systems. The slowest, so keep it to the critical paths.

**Plus plain JUnit** (no Spring) for domain logic: the fastest and the most tests.

**Speed tips:** Spring caches contexts between test classes with identical configuration. Varied `@MockitoBean` sets and `@DirtiesContext` multiply context startups, so standardise test base classes. (`@MockitoBean` replaced the deprecated `@MockBean` in Spring Boot 3.4+.)
""", I, ["spring-test", "slices", "testing"], True),

("Why use Testcontainers instead of H2 for integration tests?", r"""
**H2 isn't MySQL.** Tests against it can pass while production fails, or fail for reasons production never sees:
- **SQL dialect and functions:** JSON columns and functions, `ON DUPLICATE KEY UPDATE`, window-function quirks, date functions, native queries.
- **Locking and concurrency:** `SELECT ... FOR UPDATE SKIP LOCKED`, gap locks, deadlock detection and isolation behaviour all differ, which matters for any concurrency test.
- **Constraints, collations, case sensitivity:** unique checks with `utf8mb4` collations, strict mode, implicit conversions.
- **Migrations:** your Flyway scripts are written for MySQL. Running them on H2 needs compatibility hacks, or they don't run at all.

**Testcontainers** starts the **same database version** (say `mysql:8.4`) in Docker for the test run:
```java
@Container @ServiceConnection
static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");
```
`@ServiceConnection` (Boot 3.1+) wires the datasource automatically. The same approach covers Kafka, Redis, LocalStack and others.

**Costs and mitigations:** it needs Docker in CI, and containers take seconds to start. Use a **singleton container** shared across test classes (or reusable containers locally), keep pure logic in unit tests, and lean on Spring's context caching.

**Interview line:** "I want my integration tests to fail for the same reasons production would."
""", I, ["testcontainers", "integration-testing", "mysql"], True),

("How do you test code that depends on the current time?", r"""
**Never call `LocalDateTime.now()` or `Instant.now()` directly in business logic.** It makes tests non-deterministic (pass at noon, fail at midnight or at month end) and makes boundaries impossible to test.

**Inject a `java.time.Clock`:**
```java
@Bean Clock clock() { return Clock.systemUTC(); }            // production

class SubscriptionService {
    private final Clock clock;
    boolean isDue(Subscription s) { return !Instant.now(clock).isBefore(s.renewAt()); }
}

// test
Clock clock = Clock.fixed(Instant.parse("2026-10-31T23:59:59Z"), ZoneOffset.UTC);
```
For flows where time advances (TTL caches, retries, rate limiters), use a **mutable test clock** or a `LongSupplier` you can move forward: `now += 10_000`.

**What to test:**
- **Boundaries:** exactly at expiry, 1 ms before and after.
- **Calendar edge cases:** month ends (Jan 31 + 1 month), leap years, year end.
- **Time zones and DST:** the user's local day vs UTC; a 23-hour or 25-hour day. Store `Instant` (UTC) and convert to the user's `ZoneId` only for display or business-day rules.

**Related:** inject randomness (`Supplier<UUID>`, seeded `Random`) the same way, and inject the sleep or backoff strategy so retry tests don't really wait. In `@SpringBootTest`, override the `Clock` bean with a fixed one in a test configuration.
""", I, ["time", "testability", "clock"], False),

("How do you test asynchronous code, such as an @Async method or a Kafka consumer?", r"""
**1. Test the logic synchronously.** Keep the business logic in a plain method or class (`PaymentEventHandler.handle(event)`) and unit-test it directly, with no threads or broker. That covers most cases quickly and deterministically.

**2. One integration test for the wiring.** Prove the real async path works: a Kafka container (Testcontainers) or `@EmbeddedKafka`, publish a message, then wait for the observable outcome:
```java
kafkaTemplate.send("payments", "O-1", new PaymentCaptured("evt-1", "O-1"));
await().atMost(Duration.ofSeconds(10))
       .untilAsserted(() -> assertThat(orderRepo.findByRef("O-1").orElseThrow().getStatus()).isEqualTo(PAID));
```
**Use Awaitility, never `Thread.sleep`.** Sleeps are slow when things are fast and flaky when CI is slow.

**3. Test the at-least-once realities:**
- Deliver the **same message twice** and assert a single effect (idempotency).
- A **poison message** ends up in the DLT after N attempts, without blocking the partition forever.
- Out-of-order events are handled by the state machine.

**For `@Async`:** in unit tests, call the method directly. In integration tests, either configure a synchronous `TaskExecutor` for determinism, or keep the real one and use Awaitility. Also check that **context propagation** (MDC/trace ID, security context) reaches the async thread if your code relies on it.
""", I, ["async", "kafka", "awaitility"], False),

("What are contract tests, and when do you need them?", r"""
**Problem:** service A (consumer) depends on service B's API or events. B's team renames a field or changes a type, all of B's tests pass, and A breaks in production. Full E2E environments catch this late and flakily.

**Consumer-driven contract testing:**
1. The **consumer** writes a test describing the interactions it relies on: request, expected status, the response fields and types it actually uses.
2. That produces a **contract** (a Pact file, or Spring Cloud Contract DSL), shared through a broker or repository.
3. The **provider's CI verifies** it against the real provider code (with stubbed dependencies). A breaking change fails *the provider's* build before deploy.
4. Consumers get **stubs** generated from the same contracts, so their tests run against a realistic fake.

**Tools:** Pact (cross-language, with a broker and a "can-i-deploy" check), Spring Cloud Contract (JVM-centric, provider-first). For **events**, schema registries with compatibility rules (Avro/Protobuf) play a similar role.

**When you need them:** multiple teams, services deployed independently, public or internal APIs with several consumers, frequent changes. **When they're overkill:** one team owning both sides and deploying together. There, integration tests plus backward-compatible change discipline (additive changes, deprecate before removing) may be enough.

They **replace most E2E tests** for compatibility, keeping E2E for a few critical journeys.
""", I, ["contract-testing", "microservices", "pact"], False),

("A test passes locally but fails about 1 in 10 runs in CI. How do you debug it?", r"""
**1. Reproduce:** run it in a loop (`@RepeatedTest(100)`, or the class 50 times), run the **whole suite** (not just the test), randomise order, and try with CI's settings (timezone, CPU limits, parallelism). Get the failure rate up so you can confirm a fix.

**2. Classify the cause:**
- **Order dependence or shared state:** passes alone, fails in the suite. Static fields, singleton caches, leftover DB rows, Spring context reused with mutated beans.
- **Time:** `now()` near midnight or month end, CI running in UTC, a timeout assumption → inject `Clock`, pin the timezone.
- **Async waits:** `Thread.sleep(500)` too short on a slow runner → Awaitility with a condition.
- **Concurrency:** a real race in production code, which surfaces under CI's different scheduling. **Treat it as a product bug.**
- **Test data collisions:** fixed IDs or emails across parallel tests → unique data per test.
- **External dependencies:** a real network call → WireMock or Testcontainers.

**3. Fix the root cause, then prove it** with the loop. **Don't** add automatic retries or `@Disabled` without a ticket. If it blocks the team, quarantine it with an owner and a deadline.

**4. Prevent it:** random test ordering in CI, a ban on sleeps in review, isolated fixtures, and dashboards for test failure rates.
""", I, ["flaky-tests", "ci", "debugging"], False),

("How would you test a retry with exponential backoff without making the tests slow?", r"""
**Make waiting injectable.** The retry logic shouldn't call `Thread.sleep` directly:
```java
interface Sleeper { void sleep(Duration d) throws InterruptedException; }

class RetryingPaymentClient {
    RetryingPaymentClient(PaymentGateway gateway, Sleeper sleeper, BackoffPolicy policy) { ... }
}

// test
List<Duration> waits = new ArrayList<>();
Sleeper recording = waits::add;                       // records instead of sleeping
when(gateway.charge(any())).thenThrow(new GatewayTimeout()).thenThrow(new GatewayTimeout()).thenReturn(ok);
client.charge(req);
verify(gateway, times(3)).charge(any());
assertThat(waits).containsExactly(Duration.ofMillis(100), Duration.ofMillis(200));
```
With jitter, inject a seeded `Random` or assert that delays fall **within bounds**.

**Cases to cover:**
1. Succeeds after N transient failures, with the correct number of attempts and delays.
2. **Gives up** after max attempts and surfaces the last error (or a clear exception).
3. **Doesn't retry non-retriable errors** (400, validation, 401): exactly one call.
4. Honours `Retry-After` if supported.
5. **Idempotency:** every attempt sends the **same idempotency key**.
6. Respects an overall deadline or budget.

**If using Resilience4j or Spring Retry:** unit-test your configuration through the library with tiny wait durations (1 ms) in a test profile, and keep one integration test against WireMock scenarios (500, 500, 200) to prove the wiring and timeouts.
""", I, ["retries", "testability", "resilience"], False),

("Code coverage is 90%, but bugs still reach production. Why, and what would you do?", r"""
**Coverage measures which lines executed, not whether behaviour was verified.** Reasons high coverage still misses bugs:
- **Weak or missing assertions:** tests call the code but assert little (or only that "no exception" was thrown).
- **Mocked seams:** the repository is mocked, so the real SQL, transaction and serialisation never ran.
- **Untested combinations and boundaries:** each branch ran once, but not "expired coupon AND single-use" or "exactly at the limit".
- **Concurrency, time, and config differences** between test and production environments.
- **Integration gaps:** contract changes, migrations, infrastructure. The bug is between units.
- Coverage **targets get gamed** with tests written to hit lines.

**What I'd do:**
1. **Mutation testing** (PIT for Java): it changes the code (flips `>` to `>=`, removes calls) and checks that some test fails. Surviving mutants show where assertions are weak. Run it on critical modules (pricing, payments).
2. **Look at where escaped bugs came from** (postmortems): add tests at that layer, such as Testcontainers integration tests or contract tests.
3. **Boundary and property-based tests** (jqwik) for logic with many input combinations.
4. **Review tests in PRs:** do the assertions check the outcome? Is the risky path covered?
5. Track coverage as a **trend signal**, not a hard target, alongside escaped-defect rates.
""", A, ["coverage", "mutation-testing", "quality"], False),

("In a 60-minute practical coding round, how do you show good testing habits without running out of time?", r"""
1. **Turn requirements into test cases out loud** in the first 5 minutes: happy path, boundaries (exactly at the TTL or limit), invalid input, duplicates, the concurrency follow-up. This also clarifies ambiguity with the interviewer.
2. **Design for testability up front:** inject the clock (`LongSupplier`/`Clock`), randomness and external dependencies through the constructor. Keep logic in plain classes, not `main`.
3. **Work in small increments:** implement one behaviour, run one or two tests, move on. A working core with tests beats a complete but untested solution.
4. **Prioritise tests** by risk: the core rule and its boundary first, then eviction and edge cases. Write a parameterised test when many inputs share a rule.
5. **When the requirement changes**, write or adjust the test first, then the code. That shows the tests are a safety net, not decoration.
6. **No JUnit available?** A `main` with tiny `check(cond, msg)` helpers is fine. The habit matters.
7. **AI-assisted rounds:** let the tool draft code but **verify it with your own tests**, read every line, and point out what you caught ("it evicted by insertion order, not access order. The test caught it").
8. **Wrap up:** name the tests you'd add with more time (concurrency stress, property-based tests) and the complexity.

What interviewers see: structured thinking, confidence in correctness, and calm handling of change.
""", I, ["practical-coding", "tdd", "interview-strategy"], True),

("Walk me through how you review a pull request.", r"""
**1. Context first:** read the description and linked ticket. What should this change do, and how risky is the area (payments vs a log message)? Skim the whole diff before commenting.

**2. Review in risk order:**
- **Correctness:** does it do what it claims? Error paths, transaction boundaries, partial failures, data migrations.
- **Edge cases:** null or empty, boundaries, duplicates, time zones, big inputs.
- **Concurrency:** shared state in singletons, check-then-act, idempotency on retries, multiple instances.
- **Security:** authorization and ownership checks, injection, mass assignment, secrets or PII in logs, input validation.
- **Performance:** N+1, unbounded queries, remote calls in loops or transactions, missing indexes for new queries.
- **Operability:** logs with IDs, metrics, timeouts, backward-compatible API and DB changes.
- **Tests:** do they cover the risky paths, and would they fail if the code were wrong?
- **Readability:** naming, structure, duplication. Last, and usually suggestions.

**3. Write actionable comments:** location, problem, impact, suggested fix. Label severity (blocker / major / minor / nit) and ask questions when I lack context.

**4. Be kind and efficient:** praise good choices, comment on the code rather than the person, approve with nits rather than blocking on taste, and move long debates to a call.

**5. Summarise:** "Approve after fixing the two blockers" makes the next step clear.
""", B, ["code-review", "process"], True),

("Review exercise: this scheduled job renews subscriptions. Rank your findings by production risk.", r"""
```java
@Scheduled(fixedRate = 60000)
public void renew() {
    List<Subscription> due = repo.findAll().stream()
        .filter(s -> s.getRenewAt().isBefore(LocalDateTime.now())).toList();
    for (Subscription s : due) {
        try {
            gateway.charge(s.getCustomerId(), s.getPrice());
            s.setRenewAt(s.getRenewAt().plusMonths(1));
            repo.save(s);
            email.sendReceipt(s.getCustomerId());
        } catch (Exception e) { log.error("renewal failed"); }
    }
}
```
1. **Blocker, double charging:** `@Scheduled` runs on **every instance**, so 3 pods charge 3 times. Claim rows atomically (`UPDATE ... WHERE status='DUE'`) or use ShedLock, *and*
2. **Blocker, no idempotency:** if `charge` succeeds and `save` fails (or the pod dies), the next run charges again. Pass a key like `sub-{id}-{period}` to the gateway, and record the attempt before charging.
3. **Major, scalability:** `findAll()` loads the whole table every minute. Query `WHERE renew_at <= ?` with an index, in pages.
4. **Major, failure handling:** the swallowed exception has no ID or stack trace. Failed cards are retried **every minute forever**. Add attempt counts, backoff or dunning, and metrics.
5. **Major, time:** `LocalDateTime.now()` is zone-dependent and untestable. Inject `Clock`, use `Instant`.
6. **Minor:** the email is synchronous inside the loop (use an event after commit); no batching.

**Tests:** a second instance doesn't double-charge; a retry after a crash charges once; a failed charge backs off.
""", A, ["code-review", "exercise", "scheduling"], True),

("Review exercise: rank the issues in this user controller.", r"""
```java
@RestController @RequestMapping("/api/users")
public class UserController {
    @Autowired UserRepository repo;
    @Autowired JdbcTemplate jdbc;

    @GetMapping("/search")
    public List<User> search(@RequestParam String name) {
        return jdbc.query("SELECT * FROM users WHERE name LIKE '%" + name + "%'", userRowMapper);
    }
    @GetMapping("/{id}")
    public User get(@PathVariable Long id) { return repo.findById(id).get(); }

    @PutMapping("/{id}")
    public User update(@PathVariable Long id, @RequestBody User user) {
        user.setId(id);
        return repo.save(user);
    }
}
```
1. **Blocker, SQL injection:** string-concatenated SQL. Use bind parameters (`LIKE ?` with `"%" + name + "%"` as the argument).
2. **Blocker, mass assignment:** `@RequestBody User` lets a client set `role=ADMIN`, `emailVerified`, `balance`. Accept an `UpdateProfileRequest` DTO with only editable fields, plus `@Valid`.
3. **Blocker, IDOR / missing authorization:** any authenticated user can read or update any `id`. Check ownership or role (`@PreAuthorize("#id == principal.id or hasRole('ADMIN')")`).
4. **Blocker, data leak:** returning the entity exposes `passwordHash` and internal fields. Return response DTOs.
5. **Major, lost data:** `PUT` replaces the whole row, so omitted fields become null. Load, apply the allowed changes, save (and use `@Version`).
6. **Major, performance:** unbounded search with `SELECT *` and a leading wildcard means full scans. Paginate, limit, use full-text search.
7. **Minor:** `Optional.get()` gives a 500 instead of a 404; field injection.

**Tests:** 403 on another user's ID; injection payload treated as literal text; `role` in the body is ignored.
""", A, ["code-review", "security", "exercise"], True),

("A @Transactional service method calls an external payment API in the middle. What's wrong, and how do you fix it?", r"""
```java
@Transactional
public void checkout(Cart cart) {
    Order order = orderRepo.save(Order.pending(cart));
    PaymentResult r = paymentClient.charge(cart.total(), cart.cardToken());   // HTTP, 300 ms to 30 s
    order.markPaid(r.chargeId());
}
```
**Problems:**
1. **Connection held during network I/O:** each checkout holds a DB connection (and row locks) for the whole HTTP call. Under load, or when the provider slows down, the Hikari pool runs dry and *every* endpoint fails, not just checkout.
2. **No atomicity across systems:** the DB transaction can't roll back a charge. If the charge succeeds and the commit fails (deadlock, timeout, crash), the **customer is charged with no order**. If the charge times out *after* succeeding at the provider, we roll back and the user retries, so a **double charge** is possible.
3. Long transactions increase lock contention and undo-log growth.

**Fix:**
1. **Tx 1:** save the order as `PENDING_PAYMENT` and commit.
2. **Outside any transaction:** call the provider with an **idempotency key** (`order-{id}`) and **timeouts**.
3. **Tx 2:** CAS update `PENDING_PAYMENT → PAID` (`WHERE status = 'PENDING_PAYMENT'`).
4. **Recovery:** a reconciliation job checks stuck `PENDING_PAYMENT` orders against the provider using the same key. Webhooks also update status idempotently.
5. Publish events with an **outbox** in Tx 2.

General rule for reviews: **no remote calls inside transactions.**
""", I, ["code-review", "transactions", "payments"], True),

("How do you write review comments that actually get acted on, especially on code that works but is hard to read?", r"""
**Structure each comment:** *where* → *what* → *why it matters* → *suggested change*, with a severity label.

> **Minor (readability):** `handle()` mixes validation, pricing and persistence in 120 lines with 4 nesting levels, so it's hard to see which rule produced a price. Suggest extracting `validate(request)`, `priceFor(cart)` and guard clauses for the early exits. Happy to pair on it if useful.

**Principles:**
- **Specific and actionable:** point to lines and give a concrete alternative (a short snippet helps). "Clean this up" isn't actionable.
- **Explain impact:** for readability, the impact is future bugs and slower changes ("the next person adding a discount rule will need to understand all four branches").
- **Label severity:** blocker / major / minor / nit. Working-but-hard-to-read code is usually **minor**; don't block a release on taste.
- **Ask when unsure:** "Is there a reason this isn't using `OrderStatus`? If not, an enum would prevent typos."
- **Comment on the code, not the person:** "this method" instead of "you wrote".
- **Batch related points** instead of 15 separate nits. Leave formatting to the formatter and linter.
- **Offer to pair,** or suggest a follow-up refactor ticket if the PR is urgent.
- **Acknowledge good work:** it builds trust, and the critical comments land better.
""", B, ["code-review", "communication"], False),

("What do you look for in the tests during a code review?", r"""
1. **Do the tests cover the risky behaviour of *this change*?** Not just the happy path: the new edge cases, error paths and boundary values. If the PR fixes a bug, is there a test that **fails without the fix**?
2. **Would they fail if the code were wrong?** Look for real assertions on outcomes (return values, persisted state, emitted events). Red flags: no assertions, asserting only "not null", `verify` without checking results, catch-all `assertDoesNotThrow`.
3. **The right level:** SQL tested against a real DB (Testcontainers), not a mocked repository; controller validation tested with MockMvc; business rules in fast unit tests.
4. **Determinism:** no `Thread.sleep`, no `now()` (an injected `Clock`), no reliance on ordering of `HashMap` or unsorted SQL, no shared mutable fixtures, no real network.
5. **Readability:** test names that describe behaviour, AAA structure, minimal setup (builders or fixtures), one behaviour per test. Tests are documentation.
6. **Not over-coupled:** excessive `verify` calls or mocking internals will break on harmless refactors.
7. **Concurrency and idempotency** for code where it matters: a concurrent test for a booking change, a duplicate-delivery test for a consumer.
8. **Speed:** a new `@SpringBootTest` with unique `@MockitoBean`s adds a context startup. Could it be a slice or unit test?
""", I, ["code-review", "testing"], False),

("A teammate disagrees with your review comment. What do you do?", r"""
**1. Assume good intent and get curious.** Ask why. They may have context I don't (a deadline, a constraint, a past incident), or I may be wrong.

**2. Separate facts from preferences.**
- If it's **correctness, security or data integrity** (a missing transaction, an injection risk), explain the concrete failure scenario, ideally with a failing test or a short reproduction. Evidence ends most debates.
- If it's **style or taste**, defer to the team's conventions or linter. If none exist, let it go or propose a convention for later. Not worth blocking a PR.

**3. Move long threads offline.** After two rounds of back and forth, a 10-minute call resolves it faster and keeps the tone human. Summarise the outcome in the PR for the record.

**4. Find a middle path if needed:** merge now with a follow-up ticket for a non-critical improvement, or add a test that documents the behaviour we disagree about.

**5. Escalate rarely and transparently:** for important design disagreements, involve a tech lead or write a short decision record with both options. Then **commit to the decision**, even if it wasn't mine.

**In a behavioural interview,** pair this with a real example: what the disagreement was, how you used data, the outcome, and what you learned (including a time you changed your own mind).
""", B, ["code-review", "behavioral", "collaboration"], False),

("What refactoring signals (code smells) do you look for, and how do you fix them?", r"""
| Smell | Fix |
|---|---|
| **Long method** with comment-separated "sections" | Extract methods named after the comments |
| **Deep nesting** (`if` in `if` in `for`) | Guard clauses and early returns, extract method |
| **Repeated switch or if-chains on a type** | Polymorphism, a strategy map (`Map<Tier, ShippingRule>`), enum methods |
| **Primitive obsession** (`double amount`, `String status`) | Value objects (`Money`), enums, records |
| **Long parameter lists / boolean flags** | Parameter object or record; separate methods instead of `doThing(x, true)` |
| **God class** (2,000-line `OrderService`, 15 dependencies) | Split by responsibility: pricing, payment, fulfilment |
| **Feature envy** (a method mostly uses another object's data) | Move it to that object |
| **Duplicated logic** | Extract one function or validator |
| **Comments explaining *what*** | Better names; keep comments for *why* |

**How I refactor safely:** characterisation tests first if coverage is thin, then small automated IDE refactorings (rename, extract, move) with tests after each step, and **refactoring kept separate from behaviour changes** in commits or PRs.

**Balance:** I also watch for the opposite smell, **speculative generality** (interfaces with one implementation, factories for two cases). The goal is code that's easy to change, not maximum abstraction.
""", I, ["clean-code", "refactoring"], True),

("You're handed a 150-line method full of nested if/else for calculating a price. How do you refactor it?", r"""
**1. Pin the behaviour first.** Write **characterisation tests** covering the current outputs for representative and boundary inputs (customer tiers, thresholds, coupons, express shipping), including odd results. Parameterised tests make this quick. These tests are the safety net, and they also surface bugs to discuss before "fixing" anything.

**2. Make it readable without changing behaviour,** in small steps, running the tests after each:
- **Guard clauses** for early exits (`if (cart.isEmpty()) return Money.ZERO;`) to flatten nesting.
- **Extract methods** per rule: `tierDiscount()`, `couponDiscount()`, `shippingFee()`.
- **Replace magic numbers** with named constants or configuration (`FREE_SHIPPING_THRESHOLD`).
- **Introduce domain types:** `Money` instead of `double`, `enum Tier` instead of strings.

**3. Restructure where the variation lives:** if branches switch on type (tier, region), use a **strategy map** or enum-based polymorphism:
```java
Map<Tier, DiscountRule> rules = Map.of(Tier.GOLD, new GoldRule(), Tier.SILVER, new SilverRule());
Money discount = rules.getOrDefault(customer.tier(), DiscountRule.NONE).apply(cart);
```
If rules change often and are business-owned, consider an ordered **rule pipeline** (a list of `PricingRule` applied in sequence).

**4. Fix the bugs separately:** the characterisation tests may expose some (rounding with `double`, a wrong boundary). Change them in a separate, reviewed commit with updated tests.

Keep commits small so each step is easy to review and revert.
""", I, ["refactoring", "clean-code", "legacy"], False),

("How do you review code written by an AI assistant?", r"""
I review it **more** carefully than a teammate's code, because it looks confident and idiomatic whether or not it's right.

**1. Check intent and scope:** does it solve *our* problem, or a plausible-looking neighbour of it? AI often adds unrequested changes, so reject scope creep.

**2. Verify correctness with tests I trust:** run the tests, and add the edge-case tests myself (boundaries, nulls, duplicates, concurrency). Generated tests often mirror the generated code's assumptions, so they pass even when both are wrong.

**3. Hunt for typical AI failure modes:**
- **Hallucinated or outdated APIs:** deprecated Spring methods, nonexistent config properties, wrong library versions.
- **Subtle logic slips:** off-by-one, eviction by insertion order instead of access order, `BigDecimal.equals`, wrong time zones.
- **Missing non-functional concerns:** no timeouts, no transactions, no idempotency, swallowed exceptions.
- **Security:** string-built SQL, missing authorization checks, secrets or PII logged, permissive CORS, unvalidated input.
- **Concurrency:** shared mutable state, check-then-act.
- **Licensing or copied code** in larger snippets.

**4. Check fit:** does it follow our conventions, error-handling patterns and architecture, or does it add a new library for a five-line problem?

**5. Own it:** if I can't explain every line, it doesn't merge. In AI-assisted interview rounds, saying "the tool suggested X; my test caught Y" is exactly the signal interviewers want.
""", I, ["ai-assisted", "code-review"], True),

("Do you practise TDD? Give an honest view of its pros and cons.", r"""
**What it is:** red (write a failing test) → green (simplest code to pass) → refactor (clean up with tests as a safety net), in short cycles.

**Where I use it:**
- **Business rules with clear inputs and outputs:** pricing, eligibility, state machines, parsers. Tests drive a clean API, and edge cases get covered naturally.
- **Bug fixes:** first write a test that reproduces the bug (it fails), then fix it. That proves the fix and prevents regressions.
- **Practical interview rounds:** test-first for the core rule shows discipline and keeps me correct under time pressure.

**Pros:** forces thinking about behaviour and the API before implementation; results in testable, decoupled designs (dependencies injected); fast feedback; an always-green safety net for refactoring; tests that document intent.

**Cons / limits:** slower at first; awkward for exploratory spikes, UI layout or unclear requirements (I spike first, then write tests); can lead to over-mocked, implementation-coupled tests if done mechanically; doesn't replace integration tests for SQL, transactions and wiring.

**Honest answer for an interview:** "I don't follow strict TDD for every line. I write tests first for business rules and bug fixes, test-after for wiring code, and nothing merges without tests for the behaviour it changes. In my last project that meant ..." (give one concrete example).
""", B, ["tdd", "practices"], False),

("How do you test a custom repository query (JPQL or native SQL)?", r"""
**Test it against a real database,** because mocking a repository proves nothing about the query.

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryTest {
    @Container @ServiceConnection static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");
    @Autowired OrderRepository repo;
    @Autowired TestEntityManager em;

    @Test
    void findsOnlyThatUsersDeliveredOrdersNewestFirst() {
        em.persist(order(1L, DELIVERED, "2026-10-01"));
        em.persist(order(1L, CANCELLED, "2026-10-02"));   // excluded by status
        em.persist(order(2L, DELIVERED, "2026-10-03"));   // other user
        em.persist(order(1L, DELIVERED, "2026-10-04"));
        em.flush(); em.clear();                            // force SQL, avoid first-level-cache hits

        List<Order> page = repo.findDelivered(1L, PageRequest.of(0, 10));

        assertThat(page).extracting(Order::getCreatedOn)
                        .containsExactly(LocalDate.parse("2026-10-04"), LocalDate.parse("2026-10-01"));
    }
}
```
**What to cover:** filtering (include and exclude cases), **ordering**, pagination boundaries (exactly page size, empty page), null handling, and constraints (duplicate key raises `DataIntegrityViolationException` after `flush`).

**Tips:** `flush()` and `clear()` so you test the database, not the persistence context. Migrations (Flyway) run on the container, so the schema is the real one. For performance-critical queries, also run `EXPLAIN` in a test or review to check index usage.
""", B, ["datajpatest", "repository", "testcontainers"], False),

("You need to change a legacy class with no tests. How do you do it safely?", r"""
**1. Understand before touching:** read the code and its callers, check git history and production logs for how it's used, and identify the change point and its blast radius.

**2. Write characterisation tests** (Michael Feathers, *Working Effectively with Legacy Code*): tests that capture **what the code does today**, not what it should do. Feed representative and edge inputs, record the outputs, and assert them, odd behaviour included. For huge outputs, use golden-master or approval testing (snapshot the output, diff on change).

**3. Break dependencies to get it under test** with minimal, safe edits:
- **Extract interface / parameterise constructor** so you can pass fakes for the DB, HTTP or clock.
- **Extract and override** (subclass in the test to stub one problematic method).
- **Sprout method or class:** write the *new* behaviour in a new, fully tested unit, and call it from the legacy code with a one-line change.
- Use IDE automated refactorings, which are less risky than hand edits.

**4. Make the change** with the safety net in place, in small commits. Refactor only what the change needs, applying the boy-scout rule within reason.

**5. Protect production:** feature flag, canary rollout, or shadow mode comparing old and new results.

The senior signal: risk-managed, incremental change instead of "rewrite it" or "just be careful".
""", A, ["legacy-code", "refactoring", "characterization-tests"], False),

("Spot the bugs: money as double, BigDecimal.equals, and equals/hashCode on a JPA entity.", r"""
```java
double total = 0.1 + 0.2;                                            // 0.30000000000000004
new BigDecimal("2.0").equals(new BigDecimal("2.00"));                // false: scale differs
new BigDecimal(0.1);                                                 // 0.1000000000000000055511151231257827...

@Entity class Item {
    @Id @GeneratedValue Long id;
    @Override public boolean equals(Object o) { return o instanceof Item i && Objects.equals(id, i.id); }
    @Override public int hashCode() { return Objects.hashCode(id); }  // id changes on persist!
}
```
**1. `double` for money:** binary floating point can't represent 0.1 exactly, so rounding errors accumulate (invoice totals off by paise, failed reconciliation). Use `BigDecimal` with explicit scale and `RoundingMode`, or `long` minor units.

**2. `BigDecimal.equals` compares scale:** `2.0` ≠ `2.00`. Use `compareTo(...) == 0` (AssertJ: `isEqualByComparingTo`). Also: `new BigDecimal(0.1)` carries the double's error. Use `new BigDecimal("0.1")` or `BigDecimal.valueOf(0.1)`.

**3. Entity hashCode on a generated ID:** before persist `id == null`, after persist it changes, so an entity put into a `HashSet` before saving becomes **unfindable** afterwards (and every transient entity is "equal"). Fixes: a constant `hashCode()` (`getClass().hashCode()`) with equals that treats a null ID as not equal, or equality on an immutable **business key** (an order reference). Avoid Lombok `@Data` on entities: it builds equals/hashCode over lazy associations, triggering loads and recursion.
""", I, ["code-review", "java-pitfalls", "jpa"], False),

("What makes a good unit test?", r"""
**FIRST:**
- **Fast:** milliseconds, so the whole suite runs on every save or push.
- **Isolated / independent:** no shared mutable state, no dependence on order, no real DB, network or filesystem.
- **Repeatable:** same result anywhere: injected clock, seeded randomness, pinned locale and timezone.
- **Self-validating:** pass or fail with clear assertions, no reading logs.
- **Timely:** written with (or before) the code, not months later.

**Plus:**
- **Tests behaviour through the public API,** not private methods or internal call sequences, so refactoring doesn't break it.
- **One reason to fail:** a focused scenario; multiple assertions are fine if they describe one outcome.
- **A descriptive name:** `apply_rejectsCoupon_atExactExpiryInstant()` reads like a spec, and the failure message tells you what broke.
- **Clear Arrange-Act-Assert,** with minimal setup through builders or fixtures, and only the details that matter visible in the test.
- **Meaningful assertions** with good failure messages (AssertJ). `isEqualByComparingTo` for `BigDecimal`, `containsExactly` for ordered lists.
- **Covers edges:** boundaries, empty or null, error paths, not only the happy path.
- **Minimal mocking:** real value objects, mocks only at boundaries, verifying only meaningful interactions.

A quick self-check: *if I introduced a bug in this rule, would this test fail with a message that points straight at it?*
""", B, ["unit-testing", "best-practices"], False),
]

SOURCES = [
 ("Ham Vocke (martinfowler.com) - The Practical Test Pyramid", "https://martinfowler.com/articles/practical-test-pyramid.html"),
 ("Martin Fowler - Mocks Aren't Stubs", "https://martinfowler.com/articles/mocksArentStubs.html"),
 ("JUnit 5 User Guide", "https://junit.org/junit5/docs/current/user-guide/"),
 ("Mockito documentation", "https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html"),
 ("Spring Boot Reference - Testing (slices, @MockitoBean, Testcontainers)", "https://docs.spring.io/spring-boot/reference/testing/index.html"),
 ("Testcontainers for Java", "https://java.testcontainers.org/"),
 ("WireMock documentation", "https://wiremock.org/docs/"),
 ("Pact - Consumer-driven contract testing", "https://docs.pact.io/"),
 ("Awaitility", "https://github.com/awaitility/awaitility"),
 ("PIT Mutation Testing", "https://pitest.org/"),
 ("Google Engineering Practices - What to look for in a code review", "https://google.github.io/eng-practices/review/reviewer/looking-for.html"),
 ("Google Engineering Practices - How to write code review comments", "https://google.github.io/eng-practices/review/reviewer/comments.html"),
 ("OWASP Top 10 (injection, broken access control)", "https://owasp.org/www-project-top-ten/"),
 ("Martin Fowler - Refactoring catalog", "https://refactoring.com/catalog/"),
 ("Michael Feathers - Working Effectively with Legacy Code (characterization tests)", "https://www.oreilly.com/library/view/working-effectively-with/0131177052/"),
]

build("testing-code-review", "test", "Testing & Code Review", 15, "🧪",
      "Write tests that catch real bugs (unit, Spring slices, Testcontainers, contracts, time and async) and review code like a senior: ranked by production risk, with specific, actionable comments.",
      NOTES, QA, SOURCES)
