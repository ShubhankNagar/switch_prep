NOTES = []

NOTES.append(("IoC, Dependency Injection and the ApplicationContext", r'''
## Inversion of Control
Normally your code creates its dependencies (`new OrderRepository()`). With IoC, a **container** creates objects (beans), wires their dependencies, and manages their lifecycle. Your class just declares what it needs. Benefits: loose coupling, easy testing with mocks, central configuration, and cross-cutting features (transactions, security) via proxies.

## Dependency Injection types
```java
@Service
public class OrderService {
    private final OrderRepository repo;
    private final PaymentClient payment;

    // Constructor injection - recommended. @Autowired optional with a single constructor.
    public OrderService(OrderRepository repo, PaymentClient payment) {
        this.repo = repo; this.payment = payment;
    }
}
```
| Type | Pros | Cons |
|---|---|---|
| **Constructor** | Immutable (`final`), mandatory deps explicit, easy unit testing without Spring, fails fast, detects circular deps at startup | Many params = smell (class does too much) |
| Setter | Optional deps, re-configurable | Object can be in partial state |
| Field (`@Autowired` on field) | Concise | Can't be final, hidden deps, needs reflection to test - avoid |

Lombok's `@RequiredArgsConstructor` generates the constructor for `final` fields.

## BeanFactory vs ApplicationContext
`BeanFactory` is the basic container (lazy bean creation). `ApplicationContext` extends it with eager singleton initialisation, event publishing, i18n (`MessageSource`), resource loading, environment/profiles, and AOP integration. Spring Boot creates an `AnnotationConfigServletWebServerApplicationContext` for web apps.

## Declaring beans
- **Stereotype annotations** + component scanning: `@Component`, `@Service`, `@Repository` (adds exception translation to `DataAccessException`), `@Controller`/`@RestController`.
- **@Bean methods** in `@Configuration` classes — for third-party classes you can't annotate, or when creation needs logic.
```java
@Configuration
public class HttpConfig {
    @Bean
    public RestClient restClient(RestClient.Builder b) {
        return b.baseUrl("https://api.partner.com").build();
    }
}
```
`@Configuration` classes are CGLIB-proxied so calling one `@Bean` method from another returns the same singleton (`proxyBeanMethods = true`). `@Component` with `@Bean` methods ("lite mode") doesn't do this.

## Resolving ambiguity
When two beans implement the same interface:
```java
@Primary @Component class SmsSender implements Sender {}
@Component("email") class EmailSender implements Sender {}

public Notifier(@Qualifier("email") Sender sender) {...}
public Notifier(List<Sender> all) {...}           // inject all implementations
public Notifier(Map<String, Sender> byName) {...} // bean name -> bean
```
Resolution order: by type, then `@Qualifier`, then `@Primary`, then parameter name matching bean name. Otherwise `NoUniqueBeanDefinitionException`.

## Circular dependencies
A -> B -> A. With constructor injection Spring fails at startup (`BeanCurrentlyInCreationException`). Spring Boot 2.6+ prohibits circular references by default even for field injection. Fix by redesigning (extract a third class, use events), or as a last resort `@Lazy` on one injection point (injects a proxy).

## @Autowired details
- `@Autowired(required = false)` or `Optional<T>` / `ObjectProvider<T>` for optional deps.
- `@Value("${app.timeout:5s}")` injects properties with defaults.
- `@Resource` (by name, JSR-250) and `@Inject` (JSR-330) are alternatives.
'''))

NOTES.append(("Bean Scopes and Bean Lifecycle", r'''
## Scopes
| Scope | Instances | Notes |
|---|---|---|
| `singleton` (default) | One per ApplicationContext | Must be stateless/thread-safe — shared across all requests |
| `prototype` | New instance every time it is requested | Spring doesn't manage destruction |
| `request` | One per HTTP request | Web only |
| `session` | One per HTTP session | Web only |
| `application` | One per ServletContext | Web only |
| `websocket` | One per WebSocket session | |

```java
@Component @Scope("prototype") class ReportBuilder {}
@Component @RequestScope class RequestContext {}
```
Spring singleton != GoF singleton: it's one per container per bean definition, and you can still `new` the class.

### Prototype inside singleton (classic question)
A prototype injected into a singleton is created **only once** — at singleton creation — so you effectively get one instance. Fixes:
```java
@Component class Invoice {
    private final ObjectProvider<ReportBuilder> builders;
    void run() { ReportBuilder b = builders.getObject(); }   // fresh each call
}
```
Or use `@Lookup` method injection, or a scoped proxy: `@Scope(value = "prototype", proxyMode = ScopedProxyMode.TARGET_CLASS)`. Request/session beans injected into singletons are proxies automatically when using `@RequestScope`.

## Bean lifecycle
1. **Instantiate** (constructor).
2. **Populate properties** (DI via setters/fields).
3. **Aware callbacks**: `BeanNameAware`, `BeanFactoryAware`, `ApplicationContextAware`.
4. `BeanPostProcessor.postProcessBeforeInitialization`.
5. **Init**: `@PostConstruct` -> `InitializingBean.afterPropertiesSet()` -> custom `initMethod`.
6. `BeanPostProcessor.postProcessAfterInitialization` — **AOP proxies are created here**, so the bean in the context may be a proxy.
7. Bean is ready for use.
8. On shutdown: `@PreDestroy` -> `DisposableBean.destroy()` -> custom `destroyMethod`.

```java
@Component
public class CacheWarmer {
    @PostConstruct void warm() { /* load reference data */ }
    @PreDestroy void flush() { /* release resources */ }
}
```
`@PostConstruct` runs after injection, so dependencies are available (unlike in the constructor for field-injected beans). For work after the whole app is ready, use `ApplicationRunner`/`CommandLineRunner` or `@EventListener(ApplicationReadyEvent.class)`.

## BeanPostProcessor vs BeanFactoryPostProcessor
- `BeanFactoryPostProcessor` modifies **bean definitions** before any bean is instantiated (e.g. `PropertySourcesPlaceholderConfigurer` resolves `${}`).
- `BeanPostProcessor` modifies **bean instances** after creation (e.g. `AutowiredAnnotationBeanPostProcessor`, AOP auto-proxy creator).

## Lazy initialisation
Singletons are created eagerly at startup (fail-fast). `@Lazy` defers creation until first use; `spring.main.lazy-initialization=true` makes all lazy (faster startup, but errors surface later).

## Thread safety of singletons
Singletons are shared; never store request-specific data in instance fields of a `@Service`. Keep them stateless, or use thread-safe structures.
'''))

NOTES.append(("Spring Boot: Auto-configuration, Starters and Startup", r'''
Spring Boot is opinionated Spring: starters for dependencies, auto-configuration, embedded server, externalised configuration, and production features (Actuator). It removes boilerplate XML/Java config.

## @SpringBootApplication
Combines three annotations:
- `@SpringBootConfiguration` (a `@Configuration`)
- `@EnableAutoConfiguration` — turns on auto-configuration
- `@ComponentScan` — scans the package of the main class and sub-packages (keep the main class in the root package!)

## Starters
Curated dependency bundles with compatible versions managed by the Boot BOM: `spring-boot-starter-web` (Spring MVC + Jackson + Tomcat), `-data-jpa` (Hibernate + HikariCP), `-security`, `-validation`, `-actuator`, `-test` (JUnit 5, Mockito, AssertJ), `-webflux`, `-cache`. You don't specify versions; the parent/BOM does.

## How auto-configuration works
1. `@EnableAutoConfiguration` imports `AutoConfigurationImportSelector`.
2. It reads candidate classes from `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (Boot 2.7+/3; older versions used `spring.factories`).
3. Each auto-config class is guarded by **conditions**:
```java
@AutoConfiguration
@ConditionalOnClass(DataSource.class)
@ConditionalOnMissingBean(DataSource.class)
@EnableConfigurationProperties(DataSourceProperties.class)
public class DataSourceAutoConfiguration {
    @Bean DataSource dataSource(DataSourceProperties p) { ... }  // Hikari by default
}
```
Common conditions: `@ConditionalOnClass`, `@ConditionalOnMissingBean` (back off if the user defined their own), `@ConditionalOnProperty`, `@ConditionalOnBean`, `@ConditionalOnWebApplication`.

So adding `spring-boot-starter-data-jpa` + a MySQL driver puts classes on the classpath -> DataSource, EntityManagerFactory, TransactionManager, and repositories are configured automatically. Define your own bean and Boot's backs off.

Debug: run with `--debug` or `debug=true` to print the **Conditions Evaluation Report**, or use the `/actuator/conditions` endpoint. Exclude: `@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)`.

## Writing a custom starter
Create an auto-config module with `@AutoConfiguration` classes + conditions + `@ConfigurationProperties`, register it in the `.imports` file, and wrap with a starter POM. Used in companies for shared logging/security/tracing setups.

## Startup sequence (what `SpringApplication.run` does)
1. Determine app type (servlet/reactive/none), load `ApplicationContextInitializer`s and listeners.
2. Prepare the `Environment` (properties, profiles).
3. Print banner, create the ApplicationContext.
4. Load bean definitions (component scan + auto-config).
5. **Refresh** the context: instantiate singletons, start embedded Tomcat.
6. Call `ApplicationRunner`/`CommandLineRunner` beans.
7. Publish `ApplicationReadyEvent`.

## Embedded server
Tomcat by default (Jetty/Undertow alternatives by excluding Tomcat). Packaged as an executable **fat jar** (`java -jar app.jar`) with nested jars loaded by Boot's launcher. Configure with `server.port`, `server.servlet.context-path`, `server.tomcat.threads.max` (default 200).

## Spring vs Spring Boot (one-liner)
Spring is the framework (DI, MVC, data, etc.); Spring Boot is a layer that auto-configures Spring with sensible defaults so you can build production-ready apps quickly.

## Boot 3 notes
Requires Java 17+, Jakarta EE 9+ (`javax.*` -> `jakarta.*`), Hibernate 6, native image support (GraalVM AOT), Micrometer Observation/Tracing, `ProblemDetail`, `RestClient` (3.2), virtual threads (3.2), Docker Compose support (3.1). Boot 3.4/3.5 are current in 2025, with Boot 4 / Spring 7 arriving late 2025.
'''))

NOTES.append(("Configuration, Profiles and Externalised Properties", r'''
## Property sources (higher wins)
Roughly: command-line args > `SPRING_APPLICATION_JSON` > OS environment variables > Java system properties > `application-{profile}.yml` outside jar > inside jar > `application.yml` outside jar > inside jar > `@PropertySource` > defaults.
So `java -jar app.jar --server.port=9090` or env var `SERVER_PORT=9090` overrides the file. Env vars use relaxed binding (`SPRING_DATASOURCE_URL` -> `spring.datasource.url`).

## application.yml example
```yaml
spring:
  application.name: order-service
  datasource:
    url: jdbc:mysql://localhost:3306/orders
    username: ${DB_USER}
    password: ${DB_PASS}
    hikari.maximum-pool-size: 20
  jpa:
    hibernate.ddl-auto: validate
    open-in-view: false
app:
  payment:
    base-url: https://pay.example.com
    timeout: 3s
    retries: 2
```

## @Value vs @ConfigurationProperties
```java
@Value("${app.payment.timeout:5s}") Duration timeout;

@ConfigurationProperties(prefix = "app.payment")
@Validated
public record PaymentProps(@NotBlank String baseUrl, Duration timeout, int retries) {}
// enable: @EnableConfigurationProperties(PaymentProps.class) or @ConfigurationPropertiesScan
```
`@ConfigurationProperties` is type-safe, groups related properties, supports validation, relaxed binding, nested objects, lists/maps, and IDE metadata. Prefer it over scattering `@Value`.

## Profiles
Profiles separate environment-specific config: `application-dev.yml`, `application-prod.yml`.
```bash
java -jar app.jar --spring.profiles.active=prod
SPRING_PROFILES_ACTIVE=prod
```
```java
@Profile("!prod") @Bean CommandLineRunner seedData() {...}
@Profile("test") @Configuration class FakePaymentConfig {...}
```
Multi-document YAML with `spring.config.activate.on-profile: prod`. Profile groups: `spring.profiles.group.prod=prod-db,prod-mq`. `@ActiveProfiles("test")` in tests.

## Secrets
Never commit secrets. Use environment variables, Kubernetes Secrets, Vault (Spring Cloud Vault), AWS Secrets Manager/Parameter Store, or Spring Cloud Config with encryption. `spring.config.import=optional:configserver:` or `vault://`.

## Refreshing config at runtime
`@RefreshScope` beans (Spring Cloud) re-bind when `/actuator/refresh` is called or a Spring Cloud Bus event arrives. `@ConfigurationProperties` beans are rebound too.

## Conditional beans by property
```java
@Bean
@ConditionalOnProperty(name = "app.cache.enabled", havingValue = "true", matchIfMissing = false)
CacheManager cacheManager() {...}
```
Feature flags at startup are a common use case.

## Logging config
`logging.level.org.hibernate.SQL=debug`, `logging.level.com.myco=info`, `logging.pattern.console`, `logback-spring.xml` with `<springProfile>`. Use structured JSON logging in prod (Boot 3.4 has built-in structured logging: `logging.structured.format.console=ecs`).

## Debugging "which value won?"
When a property doesn't take the value you expect, check `/actuator/env` (shows every property source in precedence order and which one supplied the value) and `/actuator/configprops` (shows bound `@ConfigurationProperties` beans). A common surprise in Kubernetes: an environment variable like `SERVER_PORT` injected by the platform silently overrides `application.yml`.

## Relaxed binding cheat sheet
| Form | Example |
|---|---|
| Kebab case (recommended in files) | `app.payment.base-url` |
| Camel case | `app.payment.baseUrl` |
| Environment variable | `APP_PAYMENT_BASEURL` (dots -> underscores, dashes removed, upper case) |
| List index in env var | `APP_SERVERS_0_HOST` |

## Interview angle
Expect "how do you keep the same artifact across environments?" Answer: build one immutable jar/image, keep environment-specific values outside it (env vars, ConfigMaps, Secrets, Config Server), select behaviour with profiles, validate required properties at startup with `@Validated` so a missing value fails fast instead of failing on the first request.
'''))

NOTES.append(("Building REST APIs: Controllers, Exception Handling, Validation", r'''
## Controller basics
```java
@RestController                       // @Controller + @ResponseBody
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
public class OrderController {
    private final OrderService service;

    @GetMapping("/{id}")
    public OrderDto get(@PathVariable Long id) { return service.get(id); }

    @GetMapping
    public Page<OrderDto> list(@RequestParam(defaultValue = "PLACED") Status status,
                               Pageable pageable) {          // ?page=0&size=20&sort=createdAt,desc
        return service.list(status, pageable);
    }

    @PostMapping
    public ResponseEntity<OrderDto> create(@Valid @RequestBody CreateOrderRequest req) {
        OrderDto dto = service.create(req);
        return ResponseEntity.created(URI.create("/api/v1/orders/" + dto.id())).body(dto);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) { service.delete(id); }
}
```
- `@PathVariable` (resource identity), `@RequestParam` (filters/pagination), `@RequestBody` (JSON -> object via Jackson `HttpMessageConverter`), `@RequestHeader`, `@CookieValue`.
- Return DTOs, never JPA entities (lazy-loading issues, leaking internals, recursion).

## Request flow in Spring MVC
Client -> Tomcat thread -> Filters (incl. Security) -> **DispatcherServlet** -> `HandlerMapping` finds the controller method -> `HandlerInterceptor.preHandle` -> `HandlerAdapter` invokes method (argument resolvers, message converters) -> return value converted to JSON -> interceptors post/after -> response. Exceptions go to `HandlerExceptionResolver`s (which call your `@ExceptionHandler`).

## REST design essentials
- Nouns for resources, HTTP verbs for actions: `GET /orders/42`, `POST /orders`, `PUT` (full replace, idempotent), `PATCH` (partial), `DELETE` (idempotent).
- Status codes: 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized (not authenticated), 403 Forbidden (no permission), 404, 409 Conflict, 422, 429 Too Many Requests, 500, 503.
- Versioning (`/v1/` path or header), pagination, filtering, idempotency keys for payments, HATEOAS optional.

## Global exception handling
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail notFound(ResourceNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> invalid(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors()
          .forEach(fe -> errors.put(fe.getField(), fe.getDefaultMessage()));
        return ResponseEntity.badRequest().body(errors);
    }
    @ExceptionHandler(Exception.class)
    public ProblemDetail generic(Exception ex) {
        log.error("Unhandled", ex);
        return ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Something went wrong");
    }
}
```
Other options: `@ResponseStatus` on exception classes, `ResponseStatusException`, controller-local `@ExceptionHandler`. Enable RFC 7807 globally: `spring.mvc.problemdetails.enabled=true`.

## Bean Validation (jakarta.validation)
```java
public record CreateOrderRequest(
    @NotNull Long customerId,
    @NotEmpty List<@Valid LineItem> items,
    @Email String notifyEmail,
    @Size(max = 200) String note) {}
public record LineItem(@NotBlank String sku, @Min(1) @Max(100) int qty) {}
```
- `@Valid` on `@RequestBody` triggers validation -> `MethodArgumentNotValidException` (400).
- `@Validated` on the class enables validation of `@PathVariable`/`@RequestParam` (-> `ConstraintViolationException` / Boot 3.2 `HandlerMethodValidationException`).
- Validation groups for create vs update; custom constraints via `@Constraint(validatedBy = ...)` + `ConstraintValidator`.
- Requires `spring-boot-starter-validation`.

## Calling other APIs
`RestTemplate` (maintenance mode), `WebClient` (reactive, non-blocking), `RestClient` (Boot 3.2, fluent synchronous), and declarative HTTP interfaces (`@HttpExchange`) or OpenFeign. Always set connect/read timeouts.

## Filters vs Interceptors
Filters (Servlet level, before DispatcherServlet, see raw request — security, logging, CORS). Interceptors (Spring MVC level, know the handler method — auth checks, timing, locale).
'''))

NOTES.append(("Spring Data JPA and Hibernate Essentials", r'''
## Layers
JPA is the specification (`jakarta.persistence`), Hibernate is the implementation (ORM), Spring Data JPA is an abstraction on top that generates repositories. JDBC sits underneath, with HikariCP as the connection pool.

## Entities
```java
@Entity
@Table(name = "orders", indexes = @Index(columnList = "customer_id, created_at"))
public class Order {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) // MySQL auto_increment
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY) @JoinColumn(name = "customer_id")
    private Customer customer;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();

    @Enumerated(EnumType.STRING) private Status status;
    @Version private Long version;   // optimistic locking
    @CreationTimestamp private Instant createdAt;
}
```
- `mappedBy` marks the inverse side; the side with the foreign key (`@ManyToOne`) is the owner.
- ID strategies: `IDENTITY` (DB auto-increment, disables JDBC batch inserts in Hibernate), `SEQUENCE` (best with batching; Postgres/Oracle), `TABLE`, `UUID`.
- Always use `EnumType.STRING` (ORDINAL breaks when you reorder enum).

## Repositories
```java
public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByStatusAndCreatedAtAfter(Status s, Instant t);   // derived query
    Optional<Order> findTopByCustomerIdOrderByCreatedAtDesc(Long cid);

    @Query("select o from Order o join fetch o.items where o.id = :id")
    Optional<Order> findWithItems(@Param("id") Long id);

    @Query(value = "select * from orders where status = ?1", nativeQuery = true)
    List<Order> nativeByStatus(String status);

    @Modifying @Query("update Order o set o.status = :s where o.id in :ids")
    int bulkUpdate(@Param("s") Status s, @Param("ids") List<Long> ids);

    Page<OrderSummary> findByCustomerId(Long id, Pageable p);           // interface projection
}
```
Hierarchy: `Repository` -> `CrudRepository` -> `ListCrudRepository` -> `PagingAndSortingRepository` -> `JpaRepository` (adds `flush`, `saveAll`, batch deletes, `getReferenceById`). Dynamic queries: `Specification` (JPA Criteria), Querydsl, or Query by Example.

## Persistence context and entity states
The `EntityManager` holds a **persistence context** (first-level cache) for the transaction.
- **Transient** (new, not tracked) -> `persist` -> **Managed** -> transaction ends/`detach` -> **Detached** -> `merge` -> Managed; `remove` -> **Removed**.
- **Dirty checking**: changes to managed entities are flushed automatically at commit — no `save()` needed.
- `save()` calls `persist` for new entities and `merge` for detached ones (an extra SELECT).
- First-level cache: two `findById(1)` calls in one transaction hit the DB once. Second-level cache (Ehcache/Caffeine/Redis via JCache) is shared across sessions and optional.

## Fetch types
Defaults: `@ManyToOne`/`@OneToOne` = **EAGER**, `@OneToMany`/`@ManyToMany` = **LAZY**. Best practice: make everything LAZY and fetch explicitly per use case. Accessing a lazy association outside a session throws `LazyInitializationException`. Fix with `JOIN FETCH`, `@EntityGraph`, DTO projections, or loading within a `@Transactional` service method — **not** with `open-in-view` (default true; set `spring.jpa.open-in-view=false`) or `enable_lazy_load_no_trans`.

## getReferenceById vs findById
`findById` hits the DB and returns `Optional`. `getReferenceById` returns a lazy proxy without querying — useful to set a foreign key: `item.setOrder(repo.getReferenceById(orderId))`.

## Batch inserts
`spring.jpa.properties.hibernate.jdbc.batch_size=50`, `order_inserts=true`; doesn't work with IDENTITY ids. For huge loads, use JDBC `batchUpdate` or `LOAD DATA`.

## ddl-auto
`none`/`validate` in prod (use Flyway/Liquibase for migrations), `update` only for local, `create-drop` for tests.
'''))

NOTES.append(("The N+1 Problem, Fetching Strategies and JPA Performance", r'''
## What is N+1?
You load N parents with one query, then lazily touching each parent's association fires one more query per parent — N+1 queries total.
```java
List<Order> orders = orderRepo.findAll();          // 1 query
for (Order o : orders) {
    o.getItems().size();                           // N queries (one per order)
}
```
It also happens with **EAGER** `@ManyToOne` when using JPQL/derived queries: Hibernate runs the main query and then one select per distinct customer. EAGER doesn't fix N+1; it often causes it.

## How to detect
- `spring.jpa.show-sql=true` or `logging.level.org.hibernate.SQL=debug` and count queries.
- `spring.jpa.properties.hibernate.generate_statistics=true`.
- Tools: Hypersistence Optimizer, datasource-proxy, or asserting query count in tests.

## Fixes
**1. JOIN FETCH**
```java
@Query("select distinct o from Order o join fetch o.items where o.status = :s")
List<Order> findWithItems(@Param("s") Status s);
```
(Hibernate 6 de-duplicates parents automatically; `distinct` was needed in 5.) Caveat: fetching two `List` (bag) collections at once throws `MultipleBagFetchException` — use `Set` or fetch in separate queries. JOIN FETCH with pagination applies limit **in memory** (warning HHH90003004) — paginate IDs first, then fetch.

**2. @EntityGraph**
```java
@EntityGraph(attributePaths = {"items", "customer"})
List<Order> findByStatus(Status s);
```

**3. Batch fetching** — loads lazy collections for many parents in one `IN` query:
```properties
spring.jpa.properties.hibernate.default_batch_fetch_size=50
```
or `@BatchSize(size = 50)` on the association. Turns N+1 into 1 + N/50.

**4. DTO projections** — select only what the screen needs:
```java
@Query("select new com.app.OrderView(o.id, c.name, o.total) from Order o join o.customer c")
List<OrderView> views();
```
Fastest for read-only lists; no dirty checking overhead.

**5. `@Fetch(FetchMode.SUBSELECT)`** — second query uses a subselect of the original.

## Other JPA performance tips
- Prefer LAZY everywhere; fetch per use case.
- Use `@Transactional(readOnly = true)` on read services — Hibernate skips dirty checking snapshots, and routing to read replicas is possible.
- Avoid loading entities just to update a field — use `@Modifying` bulk queries (remember they bypass the persistence context; use `clearAutomatically = true`).
- Paginate with `Pageable`; for deep pages use keyset pagination (`where id > :lastId order by id limit 50`). `Page` triggers a count query; `Slice` avoids it.
- Index foreign keys and filter columns.
- Watch `Cascade.ALL` + `orphanRemoval` on large collections; avoid huge `@OneToMany` collections — query the child side instead.
- Bidirectional relationships: keep both sides in sync with helper methods (`addItem`).
- `equals/hashCode` on entities: don't use generated id naively; avoid Lombok `@Data` on entities (lazy-loading toString/hashCode recursion).
- Connection pool sizing (HikariCP `maximum-pool-size`, default 10). Formula of thumb: cores * 2 + effective spindles; more isn't better.

## Open Session in View (OSIV)
Boot enables it by default (warning logged). It keeps the session open until the view renders, so lazy loading works in controllers — but holds DB connections for the whole request and hides N+1 problems. Disable with `spring.jpa.open-in-view=false` and fetch what you need in the service layer.
'''))

NOTES.append(("Transactions: @Transactional, Propagation, Isolation and Pitfalls", r'''
## How @Transactional works
Spring creates an **AOP proxy** around the bean. When a `@Transactional` method is called through the proxy, `TransactionInterceptor` asks the `PlatformTransactionManager` (JPA: `JpaTransactionManager`) to begin a transaction, binds the connection/EntityManager to the thread (ThreadLocal), calls your method, then commits — or rolls back on exception.

```java
@Service
public class TransferService {
    @Transactional
    public void transfer(Long from, Long to, BigDecimal amt) {
        Account a = repo.findById(from).orElseThrow();
        Account b = repo.findById(to).orElseThrow();
        a.debit(amt); b.credit(amt);          // dirty checking -> UPDATEs at commit
    }
}
```

## Rollback rules
Default: rollback on **RuntimeException and Error**; **commit on checked exceptions**. Change with `@Transactional(rollbackFor = Exception.class)` or `noRollbackFor`. Catching the exception inside the method means no rollback (unless you call `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`).

## Propagation
| Propagation | Behaviour |
|---|---|
| **REQUIRED** (default) | Join existing transaction or create a new one |
| **REQUIRES_NEW** | Suspend current, always start a new independent transaction (audit logs that must persist even if the outer fails) |
| NESTED | Savepoint within the current transaction (JDBC only, not JPA by default) |
| SUPPORTS | Join if exists, else run non-transactionally |
| NOT_SUPPORTED | Suspend current, run without a transaction |
| MANDATORY | Must have an existing transaction, else exception |
| NEVER | Must not have one, else exception |

**Gotcha:** with REQUIRED, if an inner method throws a RuntimeException that the outer catches, the shared transaction is already marked rollback-only, so the outer commit throws `UnexpectedRollbackException`.

## Isolation
`@Transactional(isolation = Isolation.READ_COMMITTED)`. Levels: READ_UNCOMMITTED, READ_COMMITTED, REPEATABLE_READ (MySQL InnoDB default), SERIALIZABLE, DEFAULT (use DB default). See the SQL chapter for anomalies.

## Other attributes
`readOnly = true` (optimisation hint; Hibernate sets flush mode MANUAL), `timeout = 5` seconds.

## Pitfalls (very frequently asked)
1. **Self-invocation**: calling a `@Transactional` method from another method of the same class bypasses the proxy -> no transaction.
```java
public void placeAll(List<Order> os) { os.forEach(this::place); } // place() not transactional here!
@Transactional public void place(Order o) {...}
```
Fixes: move the method to another bean, inject self (`@Lazy` self-reference), use `TransactionTemplate`, or AspectJ weaving.
2. **Non-public methods**: proxies only intercept public methods (Spring 6 supports protected/package-private for class-based proxies, but keep it public).
3. **Checked exceptions** don't roll back by default.
4. **Swallowing exceptions** inside the method -> commit.
5. **final methods/classes** can't be proxied by CGLIB.
6. Calling from a `@PostConstruct` — proxy may not be ready.
7. **Long transactions** that make remote HTTP calls or send Kafka messages — they hold DB connections and locks; and the external side-effect can't be rolled back (use the outbox pattern).
8. `@Transactional` on a `private` method or on a class not managed by Spring — ignored.
9. Multiple data sources: specify `transactionManager`.
10. Async methods run in another thread -> different transaction.

## Programmatic transactions
```java
transactionTemplate.execute(status -> {
    repo.save(x);
    if (bad) status.setRollbackOnly();
    return null;
});
```

## Transaction events
`@TransactionalEventListener(phase = AFTER_COMMIT)` — send emails/publish events only after a successful commit.

## Optimistic vs pessimistic locking in JPA
- Optimistic: `@Version` column; update checks `where version = ?`; conflict -> `OptimisticLockException` (retry). Best for low contention.
- Pessimistic: `@Lock(LockModeType.PESSIMISTIC_WRITE)` -> `SELECT ... FOR UPDATE`. For high contention like inventory/seat booking.
'''))

NOTES.append(("Spring Security: Filter Chain, Authentication, JWT and OAuth2", r'''
## Architecture
- Servlet container calls `DelegatingFilterProxy` -> `FilterChainProxy` -> one of the `SecurityFilterChain`s (matched by request).
- The chain contains ordered filters: `SecurityContextHolderFilter`, `CorsFilter`, `CsrfFilter`, `LogoutFilter`, `UsernamePasswordAuthenticationFilter` / `BearerTokenAuthenticationFilter`, `ExceptionTranslationFilter`, `AuthorizationFilter`, etc.
- **Authentication flow**: filter extracts credentials -> creates an unauthenticated `Authentication` -> `AuthenticationManager` (`ProviderManager`) -> `AuthenticationProvider` (e.g. `DaoAuthenticationProvider` uses `UserDetailsService` + `PasswordEncoder`) -> authenticated `Authentication` stored in `SecurityContextHolder` (ThreadLocal).
- **Authorization**: `AuthorizationFilter` checks URL rules; method security (`@PreAuthorize`) via AOP.
- 401 vs 403: `AuthenticationEntryPoint` (not logged in) vs `AccessDeniedHandler` (logged in, no permission).

## Configuration (Spring Security 6 style — no WebSecurityConfigurerAdapter)
```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {
    @Bean
    SecurityFilterChain api(HttpSecurity http, JwtAuthFilter jwtFilter) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())                         // stateless REST with tokens
            .cors(Customizer.withDefaults())
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**", "/actuator/health").permitAll()
                .requestMatchers(HttpMethod.DELETE, "/api/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }
    @Bean PasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(); }
}
```

## JWT authentication (custom filter)
1. `POST /api/auth/login` -> authenticate via `AuthenticationManager` -> issue signed JWT (header.payload.signature; claims `sub`, `roles`, `exp`).
2. Client sends `Authorization: Bearer <token>` on every request.
3. A `OncePerRequestFilter` validates signature and expiry, builds `UsernamePasswordAuthenticationToken`, sets it in `SecurityContextHolder`.
```java
@Component
public class JwtAuthFilter extends OncePerRequestFilter {
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String h = req.getHeader("Authorization");
        if (h != null && h.startsWith("Bearer ")) {
            Claims c = jwtService.parse(h.substring(7));          // throws if invalid/expired
            var auth = new UsernamePasswordAuthenticationToken(c.getSubject(), null,
                    jwtService.authorities(c));
            SecurityContextHolder.getContext().setAuthentication(auth);
        }
        chain.doFilter(req, res);
    }
}
```
Better in production: use the built-in **resource server** support: `http.oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))` with `spring.security.oauth2.resourceserver.jwt.issuer-uri` (Keycloak, Auth0, Cognito).

**JWT trade-offs:** stateless and scalable, but can't be revoked before expiry — keep access tokens short (5-15 min) and use **refresh tokens** (stored server-side, rotated) for renewal; blacklist in Redis if instant logout is needed. Never put secrets in the payload (it's only Base64-encoded). Use strong keys (RS256 with key rotation via JWKS).

## OAuth2 and OpenID Connect
- **OAuth2** = delegated authorization. Roles: resource owner (user), client (your app), authorization server (Google/Keycloak), resource server (your API).
- **Authorization Code + PKCE**: for web/mobile apps; user logs in at the auth server, client gets a code, exchanges it for tokens.
- **Client Credentials**: service-to-service, no user.
- **OIDC** adds authentication on top (ID token with user identity).
- Spring: `oauth2Login()` for "Login with Google" in apps, `oauth2ResourceServer()` for APIs, `oauth2Client` for calling other APIs with tokens.

## CSRF and CORS
- **CSRF**: attack that uses the victim's browser cookies. Needed for cookie/session auth; usually disabled for stateless token APIs.
- **CORS**: browser restriction on cross-origin requests; configure allowed origins (your Angular app at `localhost:4200`) via `CorsConfigurationSource` bean or `@CrossOrigin`.

## Method security
```java
@PreAuthorize("hasRole('ADMIN') or #userId == authentication.name")
public UserDto get(String userId) {...}
```
`hasRole('ADMIN')` expects authority `ROLE_ADMIN`; `hasAuthority` uses the exact string.

## Password storage
Never store plain or MD5/SHA hashes. Use BCrypt/Argon2/SCrypt (salted, slow). `DelegatingPasswordEncoder` supports `{bcrypt}` prefixed upgrades.
'''))

NOTES.append(("Testing Spring Boot Apps: JUnit 5, Mockito, Slices", r'''
## Testing pyramid
Many fast **unit tests** (no Spring), fewer **slice tests** (part of the context), few **integration tests** (full context + real infrastructure via Testcontainers), and minimal E2E.

## JUnit 5 essentials
```java
class PriceCalculatorTest {
    PriceCalculator calc = new PriceCalculator();

    @Test
    @DisplayName("applies 10% discount above 1000")
    void discount() {
        assertEquals(new BigDecimal("990.00"), calc.price(new BigDecimal("1100")));
    }

    @ParameterizedTest
    @CsvSource({"100,100", "1100,990.00"})
    void prices(BigDecimal in, BigDecimal out) { assertEquals(out, calc.price(in)); }

    @Test void invalid() {
        assertThrows(IllegalArgumentException.class, () -> calc.price(BigDecimal.valueOf(-1)));
    }
}
```
Lifecycle: `@BeforeAll` (static), `@BeforeEach`, `@AfterEach`, `@AfterAll`. Others: `@Nested`, `@Disabled`, `@Tag`, `@Timeout`, `assertAll`, `@ExtendWith`. AssertJ (`assertThat(x).isEqualTo(y)`) gives fluent assertions.

## Mockito
```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock OrderRepository repo;
    @Mock PaymentClient payment;
    @InjectMocks OrderService service;
    @Captor ArgumentCaptor<Order> captor;

    @Test
    void placesOrder() {
        when(payment.charge(any())).thenReturn(PaymentResult.ok("tx1"));
        when(repo.save(any(Order.class))).thenAnswer(inv -> inv.getArgument(0));

        service.place(new CreateOrderRequest(1L, List.of()));

        verify(repo).save(captor.capture());
        assertEquals(Status.PAID, captor.getValue().getStatus());
        verify(payment, times(1)).charge(any());
        verifyNoMoreInteractions(payment);
    }
}
```
- `@Mock` — fake with stubbed behaviour; `@Spy` — real object with selective stubbing (`doReturn(x).when(spy).m()`).
- `when(...).thenThrow(...)`, `doNothing().when(mock).voidMethod()`.
- Mock static methods: `try (MockedStatic<UUID> m = mockStatic(UUID.class)) {...}` (mockito-inline is default in Mockito 5).
- Don't mock what you don't own (value objects, JDK); don't over-verify.

## Spring Boot test slices
| Annotation | Loads | Use |
|---|---|---|
| `@SpringBootTest` | Full context | Integration tests; `webEnvironment = RANDOM_PORT` + `TestRestTemplate`/`WebTestClient` for real HTTP |
| `@WebMvcTest(OrderController.class)` | MVC layer only (controllers, advice, filters, converters) | Controller tests with `MockMvc`; services mocked |
| `@DataJpaTest` | JPA repos, EntityManager, embedded DB / Testcontainers; each test transactional + rolled back | Repository queries |
| `@JsonTest`, `@RestClientTest`, `@WebFluxTest` | Specific slices | |

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mvc;
    @MockitoBean OrderService service;   // Boot 3.4+; earlier @MockBean (now deprecated)

    @Test
    void returns404() throws Exception {
        when(service.get(9L)).thenThrow(new ResourceNotFoundException("Order 9"));
        mvc.perform(get("/api/v1/orders/9"))
           .andExpect(status().isNotFound());
    }
    @Test
    void validates() throws Exception {
        mvc.perform(post("/api/v1/orders").contentType(MediaType.APPLICATION_JSON).content("{}"))
           .andExpect(status().isBadRequest());
    }
}
```
`@MockBean`/`@MockitoBean` replaces a bean in the Spring context with a Mockito mock (unlike `@Mock`, which is plain Mockito). Each distinct set of mock beans creates a new cached context — too many variations slow the suite.

## Testcontainers
Run real MySQL/Kafka/Redis in Docker for integration tests:
```java
@SpringBootTest @Testcontainers
class RepoIT {
    @Container @ServiceConnection   // Boot 3.1+: auto-wires datasource properties
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");
}
```
Better than H2, which differs from MySQL in SQL dialect and behaviour.

## Security in tests
`@WithMockUser(roles = "ADMIN")`, or `mvc.perform(get(..).with(jwt()))` from spring-security-test.

## Other
- Code coverage with JaCoCo; mutation testing with PIT.
- Contract tests (Spring Cloud Contract / Pact) between microservices.
- WireMock to stub external HTTP APIs.
'''))

NOTES.append(("Actuator, Caching, Async and Scheduling", r'''
## Spring Boot Actuator
Production-ready endpoints: `/actuator/health` (liveness/readiness groups for Kubernetes probes), `/info`, `/metrics`, `/prometheus` (with micrometer-registry-prometheus), `/env`, `/loggers` (change log level at runtime), `/threaddump`, `/heapdump`, `/mappings`, `/beans`, `/conditions`.
```yaml
management:
  endpoints.web.exposure.include: health,info,prometheus,metrics
  endpoint.health.probes.enabled: true
  endpoint.health.show-details: when-authorized
```
Only `health` is exposed over HTTP by default. Secure sensitive endpoints, or run on a separate `management.server.port`. Custom health indicator: implement `HealthIndicator`. Custom metrics: inject `MeterRegistry` and use `Counter`, `Timer`, `@Timed`, `@Observed`.

## Caching abstraction
```java
@EnableCaching
@Configuration class CacheConfig {}

@Service
public class ProductService {
    @Cacheable(value = "products", key = "#id", unless = "#result == null")
    public ProductDto get(Long id) { return repo.findById(id).map(mapper::toDto).orElse(null); }

    @CachePut(value = "products", key = "#p.id")
    public ProductDto update(ProductDto p) {...}

    @CacheEvict(value = "products", key = "#id")
    public void delete(Long id) {...}

    @CacheEvict(value = "products", allEntries = true)
    public void reload() {...}
}
```
- Providers: `ConcurrentMapCache` (default, no TTL), **Caffeine** (in-memory, size/TTL), **Redis** (distributed, shared across instances), Hazelcast, Ehcache.
- Proxy-based: same **self-invocation** pitfall as `@Transactional`.
- Considerations: TTL and eviction, cache stampede (use `sync = true`), serialisation for Redis (JSON), consistency (cache-aside: update DB then evict), don't cache huge or highly volatile data.
```yaml
spring.cache.type: redis
spring.cache.redis.time-to-live: 10m
```

## @Async
```java
@EnableAsync
@Configuration
class AsyncConfig {
    @Bean(name = "mailExecutor")
    ThreadPoolTaskExecutor mailExecutor() {
        var ex = new ThreadPoolTaskExecutor();
        ex.setCorePoolSize(4); ex.setMaxPoolSize(8); ex.setQueueCapacity(200);
        ex.setThreadNamePrefix("mail-"); ex.initialize();
        return ex;
    }
}
@Service class MailService {
    @Async("mailExecutor")
    public CompletableFuture<Void> send(Mail m) {...; return CompletableFuture.completedFuture(null); }
}
```
- Return `void`, `Future`, or `CompletableFuture`. Exceptions in void methods go to `AsyncUncaughtExceptionHandler`.
- Pitfalls: self-invocation (no proxy), must be public, runs in a different thread so `@Transactional` context and `SecurityContext`/MDC don't propagate automatically (use `TaskDecorator`), default executor in Boot is `ThreadPoolTaskExecutor` (core 8) — or virtual threads if enabled.

## Scheduling
```java
@EnableScheduling
@Component class Jobs {
    @Scheduled(fixedRate = 60_000)            // every minute from start of previous run
    void poll() {}
    @Scheduled(fixedDelay = 30_000, initialDelay = 10_000) // 30s after previous finished
    void cleanup() {}
    @Scheduled(cron = "0 0 2 * * *", zone = "Asia/Kolkata") // 2 AM daily (sec min hour dom mon dow)
    void nightlyReport() {}
}
```
- Default scheduler has **one thread** — a long job delays others. Set `spring.task.scheduling.pool.size`.
- In a multi-instance deployment, every instance runs the job. Use **ShedLock** (DB/Redis lock) or Quartz clustering, or a Kubernetes CronJob, to run once.

## Events
`ApplicationEventPublisher.publishEvent(new OrderPlaced(id))` + `@EventListener` (sync by default; add `@Async`), `@TransactionalEventListener` for after-commit side effects. Decouples modules inside a monolith.
'''))

NOTES.append(("Spring AOP and Proxies", r'''
## Concepts
AOP modularises **cross-cutting concerns** — logging, transactions, security, caching, metrics, retries — that would otherwise be duplicated across classes.
- **Aspect**: class holding cross-cutting logic (`@Aspect`).
- **Join point**: a point in execution; in Spring AOP always a **method execution** on a Spring bean.
- **Pointcut**: expression selecting join points.
- **Advice**: action at a join point: `@Before`, `@AfterReturning`, `@AfterThrowing`, `@After` (finally), `@Around` (most powerful — controls whether/how the method runs).
- **Weaving**: linking aspects with targets. Spring AOP weaves at **runtime using proxies**; AspectJ can weave at compile/load time and intercept fields, constructors, private methods.

## Example: execution-time logging
```java
@Target(ElementType.METHOD) @Retention(RetentionPolicy.RUNTIME)
public @interface LogExecutionTime {}

@Aspect
@Component
@Slf4j
public class TimingAspect {
    @Around("@annotation(com.app.LogExecutionTime)")
    public Object time(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.nanoTime();
        try {
            return pjp.proceed();
        } finally {
            log.info("{} took {} ms", pjp.getSignature().toShortString(),
                     (System.nanoTime() - start) / 1_000_000);
        }
    }

    @AfterThrowing(pointcut = "execution(* com.app.service..*(..))", throwing = "ex")
    public void logError(JoinPoint jp, Exception ex) {
        log.error("Error in {}: {}", jp.getSignature(), ex.getMessage());
    }
}
```
Pointcut designators: `execution(modifiers? return-type package.Class.method(params))`, `within(com.app.service..*)`, `@annotation(...)`, `@within(...)`, `bean(orderService)`, `args(...)`. Combine with `&&`, `||`, `!`. Reuse via `@Pointcut` methods.

## Proxies: JDK dynamic vs CGLIB
- **JDK dynamic proxy**: implements the bean's interfaces; works only via interface types.
- **CGLIB**: generates a subclass at runtime; can proxy classes without interfaces; can't proxy `final` classes/methods.
- Spring Boot defaults to **CGLIB** (`spring.aop.proxy-target-class=true`).

## Why self-invocation bypasses advice
The container gives other beans a reference to the **proxy**. The proxy runs advice, then calls the real target. Inside the target, `this.otherMethod()` is a plain call on the real object, so no advice (`@Transactional`, `@Cacheable`, `@Async`, custom aspects) runs. Solutions: move the method to another bean, inject the proxy of self, `AopContext.currentProxy()` with `exposeProxy=true`, or use AspectJ.

## Ordering
Multiple aspects on the same join point: `@Order(1)` — lower runs first (outermost). Transaction interceptor order matters relative to retry: you usually want **retry outside** the transaction so each attempt gets a new transaction.

## Where Spring itself uses AOP
`@Transactional`, `@Cacheable`, `@Async`, `@PreAuthorize`, `@Retryable` (Spring Retry), `@Validated` method validation, Resilience4j annotations, `@Timed`/`@Observed`.

## When not to use AOP
Business logic that a reader needs to see should not be hidden in aspects. Keep aspects for genuinely cross-cutting, generic behaviour.
'''))
