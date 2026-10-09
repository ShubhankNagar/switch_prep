from cb_common import B, I, A

QA = [
("What is Inversion of Control and Dependency Injection?", r'''
**IoC** means the framework, not your code, controls object creation and wiring. **DI** is the way Spring implements IoC: a class declares its dependencies (constructor parameters), and the container supplies them.

```java
@Service
public class OrderService {
    private final OrderRepository repo;
    public OrderService(OrderRepository repo) { this.repo = repo; } // injected
}
```
Benefits: loose coupling (depend on interfaces), easy unit testing with mocks, central lifecycle and configuration management, and the ability to wrap beans in proxies for transactions, caching and security.
''', B, ["ioc", "di"], True),

("Constructor vs setter vs field injection — which is recommended and why?", r'''
**Constructor injection** is recommended:
- Dependencies can be `final` -> immutable, thread-safe.
- Required dependencies are explicit; object is never half-built.
- Unit tests just call `new OrderService(mockRepo)` — no Spring or reflection needed.
- Circular dependencies fail fast at startup.
- A long constructor signals the class has too many responsibilities.

**Setter injection** suits optional or re-configurable dependencies. **Field injection** (`@Autowired` on fields) is concise but hides dependencies, prevents `final`, and makes testing harder; avoid it in production code. With a single constructor, `@Autowired` is optional; Lombok `@RequiredArgsConstructor` generates it.
''', B, ["di"], True),

("What is the difference between BeanFactory and ApplicationContext?", r'''
`BeanFactory` is the root container interface: it creates and wires beans lazily on request.

`ApplicationContext` extends it and adds:
- Eager initialisation of singletons at startup (fail-fast).
- Event publishing (`ApplicationEventPublisher`).
- Internationalisation (`MessageSource`).
- Resource loading, `Environment` with profiles and properties.
- Automatic registration of `BeanPostProcessor`s (so AOP, `@Autowired`, `@Transactional` work).

In practice you always use an ApplicationContext; Spring Boot creates one for you (servlet, reactive, or plain).
''', B, ["ioc"], False),

("@Component vs @Service vs @Repository vs @Controller vs @Bean?", r'''
- `@Component` — generic stereotype for a Spring-managed class found by component scan.
- `@Service` — business layer; functionally the same as @Component but documents intent.
- `@Repository` — persistence layer; additionally enables **exception translation** (vendor exceptions -> Spring's `DataAccessException` hierarchy).
- `@Controller` — MVC controller returning views; `@RestController` = `@Controller` + `@ResponseBody` (JSON).
- `@Bean` — method-level, inside a `@Configuration` class; you construct the object yourself. Used for third-party classes (e.g. `RestClient`, `ObjectMapper`, `PasswordEncoder`) or when creation needs logic.
''', B, ["beans"], True),

("What are the bean scopes in Spring? Is a singleton bean thread-safe?", r'''
Scopes: **singleton** (default, one per container), **prototype** (new instance per request to the container), and web scopes **request**, **session**, **application**, **websocket**.

Singleton beans are **not automatically thread-safe** — the same instance serves all concurrent requests. They're safe only if they're stateless (only final references to other stateless beans). Never keep request data in instance fields:
```java
@Service class BadService { private User currentUser; } // shared between requests - bug!
```
Keep state in method locals, request-scoped beans, or thread-safe structures.
''', B, ["beans", "scope"], True),

("What happens when you inject a prototype bean into a singleton bean? How do you fix it?", r'''
The prototype is created **once**, when the singleton is created and injected, so the singleton keeps reusing that same instance — prototype behaviour is lost.

Fixes:
```java
@Service class ReportService {
    private final ObjectProvider<ReportBuilder> provider;     // 1. ObjectProvider
    void generate() { ReportBuilder b = provider.getObject(); }
}

@Component abstract class Svc {                             // 2. method injection
    @Lookup protected abstract ReportBuilder builder();
}

@Component @Scope(value = "prototype", proxyMode = ScopedProxyMode.TARGET_CLASS) // 3. scoped proxy
class ReportBuilder {}
```
Other options: `ApplicationContext.getBean()` (couples to Spring) or `Provider<T>` (JSR-330).
''', I, ["beans", "scope"], True),

("Explain the Spring bean lifecycle.", r'''
1. Bean definition loaded (scan/`@Bean`).
2. **Instantiation** via constructor (constructor injection here).
3. **Dependency injection** of fields/setters.
4. `*Aware` callbacks (`BeanNameAware`, `ApplicationContextAware`).
5. `BeanPostProcessor.postProcessBeforeInitialization`.
6. Initialisation: `@PostConstruct` -> `afterPropertiesSet()` -> custom `initMethod`.
7. `BeanPostProcessor.postProcessAfterInitialization` — AOP proxies are created here.
8. Bean in use.
9. Shutdown: `@PreDestroy` -> `DisposableBean.destroy()` -> `destroyMethod`.

Prototype beans don't get destroy callbacks. For logic after the whole application has started, use `ApplicationRunner`/`CommandLineRunner` or `@EventListener(ApplicationReadyEvent.class)`.
''', I, ["beans", "lifecycle"], True),

("How do you resolve 'NoUniqueBeanDefinitionException' when two beans implement the same interface?", r'''
Spring autowires by type; two candidates are ambiguous. Options:
- `@Primary` on the default implementation.
- `@Qualifier("beanName")` at the injection point (wins over @Primary).
- Name the parameter the same as the bean name (fallback match).
- Inject all: `List<Sender>` or `Map<String, Sender>` and choose at runtime (strategy pattern).
- Conditional beans (`@ConditionalOnProperty`, `@Profile`) so only one exists per environment.

```java
public NotificationService(@Qualifier("smsSender") Sender sender) { ... }
```
''', B, ["di"], True),

("How do you handle circular dependencies in Spring?", r'''
A circular dependency is A needing B while B needs A. With constructor injection, Spring can't create either and fails with `BeanCurrentlyInCreationException`. Since Spring Boot 2.6, circular references are disallowed by default even with field injection (`spring.main.allow-circular-references=false`).

Best fix is redesign: it's usually a sign of mixed responsibilities.
- Extract shared logic into a third bean both depend on.
- Use events (`ApplicationEventPublisher`) to decouple.
- Pass data as method parameters instead of holding references.
Workarounds: `@Lazy` on one constructor parameter (injects a proxy resolved on first use), or setter injection.
''', I, ["di"], False),

("What does @SpringBootApplication do?", r'''
It's a convenience annotation combining:
- `@SpringBootConfiguration` — marks the class as a configuration source (`@Configuration`).
- `@EnableAutoConfiguration` — enables auto-configuration based on classpath and properties.
- `@ComponentScan` — scans the class's package and sub-packages for components.

Because scanning starts from the main class's package, place it in the root package (e.g. `com.raj.orders`). You can exclude auto-configs: `@SpringBootApplication(exclude = SecurityAutoConfiguration.class)` and add `scanBasePackages` if needed.
''', B, ["spring-boot"], True),

("How does Spring Boot auto-configuration work internally?", r'''
1. `@EnableAutoConfiguration` imports `AutoConfigurationImportSelector`.
2. It loads candidate classes listed in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (Boot 3; `spring.factories` in Boot 2).
3. Each candidate is a `@AutoConfiguration` class guarded by **conditional annotations**: `@ConditionalOnClass` (library on classpath?), `@ConditionalOnMissingBean` (did the user already define one?), `@ConditionalOnProperty`, `@ConditionalOnWebApplication`.
4. Matching configs register beans with defaults bound from `@ConfigurationProperties` (e.g. `spring.datasource.*`).

So adding `spring-boot-starter-data-jpa` + MySQL driver triggers DataSource (Hikari), EntityManagerFactory and transaction manager beans. Defining your own bean makes Boot back off. See decisions with `--debug` (conditions report) or `/actuator/conditions`.
''', I, ["spring-boot", "auto-configuration"], True),

("What are Spring Boot starters? How would you create a custom starter?", r'''
Starters are dependency descriptors that bring a consistent, version-managed set of libraries for a capability — e.g. `spring-boot-starter-web` pulls Spring MVC, Jackson, validation-ready config and embedded Tomcat. Versions come from the Spring Boot BOM, avoiding conflicts.

Custom starter (common in companies for shared audit/logging/security):
1. Create an `...-autoconfigure` module with an `@AutoConfiguration` class that defines beans with `@ConditionalOnMissingBean`/`@ConditionalOnProperty`.
2. Bind settings via `@ConfigurationProperties(prefix = "acme.audit")`.
3. Register the class in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`.
4. Create a `...-starter` POM that depends on the autoconfigure module and required libraries.
Consumers just add the dependency and optionally override properties.
''', I, ["spring-boot"], False),

("How do Spring profiles work? How do you manage configuration across dev, QA and prod?", r'''
Profiles activate environment-specific beans and properties.
- Files: `application.yml` (common) + `application-dev.yml`, `application-prod.yml`.
- Activate: `--spring.profiles.active=prod`, env var `SPRING_PROFILES_ACTIVE=prod`, or `@ActiveProfiles` in tests.
- Beans: `@Profile("prod")`, `@Profile("!prod")`.

Precedence: command-line args > environment variables > external config files > packaged files. So the same jar/image is deployed everywhere, and environment specifics come from env vars, Kubernetes ConfigMaps/Secrets, Vault, or Spring Cloud Config Server. Secrets must never be committed to the repo.
''', B, ["configuration", "profiles"], True),

("@Value vs @ConfigurationProperties?", r'''
- `@Value("${app.timeout:5s}")` injects a single property; supports SpEL; fine for one or two values. No validation, no grouping, scattered across code.
- `@ConfigurationProperties(prefix = "app.payment")` binds a whole hierarchy into a typed object (class or record), supports relaxed binding (`base-url`, `BASE_URL`, `baseUrl`), nested objects, lists/maps, `Duration`/`DataSize` conversion, JSR-303 validation with `@Validated`, and IDE autocompletion metadata.

```java
@ConfigurationProperties(prefix = "app.payment") @Validated
public record PaymentProps(@NotBlank String baseUrl, Duration timeout, int retries) {}
```
Prefer `@ConfigurationProperties` for anything beyond trivial values.
''', B, ["configuration"], False),

("@Controller vs @RestController? @RequestParam vs @PathVariable?", r'''
- `@Controller` returns view names (Thymeleaf/JSP) unless methods use `@ResponseBody`.
- `@RestController` = `@Controller` + `@ResponseBody` on every method: return values are serialised to JSON/XML by `HttpMessageConverter`s.

- `@PathVariable` extracts part of the URI path that identifies a resource: `/orders/{id}`.
- `@RequestParam` reads query parameters, typically for filtering, sorting, pagination: `/orders?status=PAID&page=0`. Supports `required=false` and `defaultValue`.
```java
@GetMapping("/users/{id}/orders")
List<OrderDto> orders(@PathVariable Long id, @RequestParam(defaultValue = "10") int limit)
```
''', B, ["rest"], True),

("Explain the request flow in Spring MVC (DispatcherServlet).", r'''
1. Request hits embedded Tomcat; a worker thread handles it.
2. Servlet **filters** run (CORS, Spring Security's FilterChainProxy, logging).
3. **DispatcherServlet** (front controller) receives it.
4. `HandlerMapping` finds the matching controller method by URL/verb.
5. `HandlerInterceptor.preHandle` runs.
6. `HandlerAdapter` invokes the method: argument resolvers populate `@PathVariable`, `@RequestBody` (via Jackson `HttpMessageConverter`), validation runs.
7. Return value is converted (e.g. to JSON) and written to the response; `postHandle`/`afterCompletion` run.
8. If an exception occurs, `HandlerExceptionResolver`s delegate to `@ExceptionHandler`/`@RestControllerAdvice`.
''', I, ["rest", "mvc"], True),

("How do you implement global exception handling in Spring Boot?", r'''
Use `@RestControllerAdvice` with `@ExceptionHandler` methods:
```java
@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(ResourceNotFoundException.class)
    ResponseEntity<ErrorResponse> notFound(ResourceNotFoundException ex, HttpServletRequest req) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse(404, ex.getMessage(), req.getRequestURI(), Instant.now()));
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<Map<String,String>> validation(MethodArgumentNotValidException ex) {
        return ResponseEntity.badRequest().body(ex.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(FieldError::getField, FieldError::getDefaultMessage, (a,b)->a)));
    }
}
```
Benefits: consistent error format, no try/catch in controllers, correct HTTP status codes. Boot 3 supports RFC 7807 `ProblemDetail`. Also log unexpected exceptions with a catch-all handler but return a generic message (don't leak stack traces).
''', B, ["rest", "exceptions"], True),

("How does validation work in Spring Boot? How do you write a custom validator?", r'''
Add `spring-boot-starter-validation` (Hibernate Validator). Annotate DTO fields (`@NotNull`, `@NotBlank`, `@Size`, `@Email`, `@Min`, `@Pattern`, `@Past`) and put `@Valid` on the `@RequestBody`. Failures throw `MethodArgumentNotValidException` -> 400. Use `@Valid` on nested objects/lists. `@Validated` on the class enables validating `@RequestParam`/`@PathVariable` and service-method parameters; it also supports validation groups.

Custom constraint:
```java
@Target(FIELD) @Retention(RUNTIME)
@Constraint(validatedBy = IndianPhoneValidator.class)
public @interface IndianPhone { String message() default "invalid phone";
    Class<?>[] groups() default {}; Class<? extends Payload>[] payload() default {}; }

public class IndianPhoneValidator implements ConstraintValidator<IndianPhone, String> {
    public boolean isValid(String v, ConstraintValidatorContext c) {
        return v == null || v.matches("^[6-9]\\d{9}$");
    }
}
```
''', I, ["validation", "rest"], True),

("PUT vs PATCH vs POST? What does idempotent mean?", r'''
- **POST** — create a resource or trigger an action; not idempotent (two calls may create two orders).
- **PUT** — replace the entire resource at a known URI; idempotent (same request twice = same state).
- **PATCH** — partial update; not guaranteed idempotent (e.g. "increment quantity"), though often implemented idempotently.
- **GET/HEAD** — safe and idempotent; **DELETE** idempotent (second call returns 404/204 but state is the same).

**Idempotent** means repeating the request produces the same server state as doing it once. It matters for retries: clients/gateways retry on timeouts. For non-idempotent POSTs like payments, use an **Idempotency-Key** header stored with the result so duplicate requests return the original response.
''', B, ["rest", "api-design"], True),

("How do you implement pagination and sorting in Spring Data JPA?", r'''
Accept a `Pageable` and return `Page` (or `Slice`):
```java
@GetMapping
public Page<ProductDto> list(@RequestParam(required = false) String q,
        @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC) Pageable p) {
    return repo.findByNameContainingIgnoreCase(q, p).map(mapper::toDto);
}
// GET /products?page=2&size=20&sort=price,asc
```
`Page` runs an extra `COUNT` query for total pages; `Slice` only checks whether a next page exists (cheaper for infinite scroll). Offset pagination gets slow for deep pages because MySQL still scans skipped rows — use **keyset/cursor pagination** (`where id < :lastId order by id desc limit 20`) for large tables. Limit max page size to protect the DB.
''', I, ["jpa", "rest"], True),

("What is the difference between JPA, Hibernate and Spring Data JPA?", r'''
- **JPA** (Jakarta Persistence) is a *specification*: annotations (`@Entity`, `@Id`), `EntityManager` API, JPQL. No implementation.
- **Hibernate** is the most popular JPA *implementation* (ORM): it maps objects to tables, generates SQL, manages the persistence context, caching, dirty checking, lazy loading. It has extra features beyond JPA.
- **Spring Data JPA** is a Spring abstraction on top of JPA that removes boilerplate: you declare repository interfaces (`JpaRepository<User, Long>`) and Spring generates implementations, derived queries from method names, pagination, auditing, and integrates with Spring transactions.
''', B, ["jpa", "hibernate"], True),

("What is the N+1 select problem and how do you fix it?", r'''
Loading N parent entities with one query and then lazily accessing an association on each fires N additional queries.
```java
List<Order> orders = repo.findAll();         // 1
orders.forEach(o -> o.getItems().size());    // +N
```
It also happens with EAGER `@ManyToOne` in JPQL queries.

Fixes:
- `JOIN FETCH` in JPQL: `select o from Order o join fetch o.items`.
- `@EntityGraph(attributePaths = "items")` on the repository method.
- Batch fetching: `hibernate.default_batch_fetch_size=50` or `@BatchSize` — loads collections with `IN (...)`.
- DTO projections selecting just the needed columns.
Detect it by enabling SQL logging / Hibernate statistics and counting queries. Beware: JOIN FETCH with pagination paginates in memory, and two List collections cause `MultipleBagFetchException`.
''', I, ["jpa", "hibernate", "performance"], True),

("Lazy vs eager loading? What is LazyInitializationException and how do you fix it?", r'''
- **EAGER** loads the association immediately with the parent (default for `@ManyToOne`, `@OneToOne`).
- **LAZY** loads it on first access via a proxy (default for `@OneToMany`, `@ManyToMany`).
Best practice: make all associations LAZY and fetch explicitly per use case.

`LazyInitializationException` occurs when you access a lazy proxy after the persistence context (session) is closed — e.g. in a controller or Jackson serialisation after the `@Transactional` service returned.

Fixes: fetch what you need inside the transaction (`JOIN FETCH`, `@EntityGraph`), map to DTOs within the service, or use projections. Avoid anti-patterns: switching to EAGER, `open-in-view=true` (holds DB connections through the request), or `enable_lazy_load_no_trans`.
''', I, ["jpa", "hibernate"], True),

("Explain entity states and the persistence context in Hibernate. What is dirty checking?", r'''
States:
- **Transient** — new object, not associated with a persistence context.
- **Managed/Persistent** — tracked by the current `EntityManager` (after `persist`, `find`, or a query).
- **Detached** — was managed, but the context closed or `detach` was called.
- **Removed** — scheduled for deletion.

The **persistence context** is a first-level cache and identity map per transaction: loading the same id twice returns the same instance and hits the DB once.

**Dirty checking**: at flush/commit Hibernate compares managed entities with their loaded snapshots and issues UPDATEs for changed fields automatically:
```java
@Transactional
public void rename(Long id, String n) { repo.findById(id).orElseThrow().setName(n); } // no save() needed
```
`readOnly = true` transactions skip snapshotting.
''', I, ["hibernate"], True),

("What is the difference between save(), saveAndFlush(), persist() and merge()?", r'''
- `persist(entity)` (JPA): makes a transient entity managed; INSERT happens at flush. Throws if the entity is detached.
- `merge(entity)` (JPA): copies state of a detached entity onto a managed instance (SELECT if not in context) and **returns the managed copy** — the argument stays detached.
- `save(entity)` (Spring Data): calls `persist` if the entity is new (id null / `@Version` null / `Persistable.isNew()`), else `merge`. With manually assigned ids this means an extra SELECT — implement `Persistable` to avoid it.
- `saveAndFlush()`: `save` + immediate `flush()` so SQL executes now (useful to surface constraint violations early), but the transaction still isn't committed.
''', I, ["jpa"], False),

("findById vs getReferenceById (getOne)?", r'''
- `findById(id)` queries the database immediately and returns `Optional<T>` (empty if not found).
- `getReferenceById(id)` (formerly `getOne`/`getById`) returns an uninitialised **proxy** without hitting the DB. The query runs only when you access a non-id property; if the row doesn't exist you get `EntityNotFoundException` at that point.

Use `getReferenceById` when you only need the reference to set a foreign key:
```java
OrderItem item = new OrderItem();
item.setOrder(orderRepo.getReferenceById(orderId));   // no SELECT on orders
itemRepo.save(item);
```
''', I, ["jpa"], False),

("How does @Transactional work internally?", r'''
Spring wraps the bean in an **AOP proxy** (CGLIB by default). When an external caller invokes a `@Transactional` method, the proxy's `TransactionInterceptor`:
1. Reads the attributes (propagation, isolation, readOnly, timeout, rollback rules).
2. Asks the `PlatformTransactionManager` (e.g. `JpaTransactionManager`) to begin or join a transaction; the connection/EntityManager is bound to the current thread via `TransactionSynchronizationManager` (ThreadLocal).
3. Invokes the actual method.
4. On normal return -> flush + commit. On RuntimeException/Error -> rollback. On checked exception -> commit (by default).

Because it's proxy-based, internal `this.method()` calls, private methods, and objects not managed by Spring aren't transactional.
''', I, ["transactions"], True),

("What are the common pitfalls of @Transactional?", r'''
1. **Self-invocation** — calling a transactional method from within the same class skips the proxy.
2. **Private/final methods** — not intercepted.
3. **Checked exceptions** — commit by default; use `rollbackFor = Exception.class`.
4. **Catching exceptions** inside the method — transaction commits.
5. **UnexpectedRollbackException** — inner REQUIRED method failed and marked rollback-only while the outer caught the exception.
6. **Long transactions with remote calls** — hold DB connections/locks; HTTP or Kafka side effects can't be rolled back (use outbox / after-commit events).
7. **@Async / new threads** — the transaction doesn't propagate.
8. **Wrong transaction manager** with multiple datasources.
9. Putting `@Transactional` on controllers instead of the service layer.
10. Expecting `readOnly = true` to prevent writes — it's an optimisation hint, not enforcement (depends on driver).
''', A, ["transactions"], True),

("Explain transaction propagation types with examples.", r'''
- **REQUIRED** (default): join the existing transaction, or start one. Most service methods.
- **REQUIRES_NEW**: suspend the current transaction and start an independent one that commits/rolls back on its own. Example: write an audit/failure log that must persist even if the business transaction rolls back.
- **NESTED**: creates a savepoint in the current transaction; inner rollback goes back to the savepoint only (JDBC `DataSourceTransactionManager`; not supported by JPA by default).
- **SUPPORTS**: use a transaction if present, otherwise none (read methods).
- **NOT_SUPPORTED**: suspend any transaction and run without one (long reporting call).
- **MANDATORY**: throw if no transaction exists (enforce being called within one).
- **NEVER**: throw if a transaction exists.

```java
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void saveAudit(AuditEvent e) { auditRepo.save(e); }   // must be in a different bean!
```
''', A, ["transactions"], True),

("What are the transaction isolation levels and which anomalies do they prevent?", r'''
| Level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| READ_UNCOMMITTED | possible | possible | possible |
| READ_COMMITTED | prevented | possible | possible |
| REPEATABLE_READ (MySQL default) | prevented | prevented | possible in theory; InnoDB prevents most via MVCC snapshots + next-key locks |
| SERIALIZABLE | prevented | prevented | prevented |

- Dirty read: reading uncommitted data of another transaction.
- Non-repeatable read: same row read twice returns different values.
- Phantom: same range query returns new rows.
In Spring: `@Transactional(isolation = Isolation.READ_COMMITTED)`. Higher isolation = more locking/less concurrency. For classic lost-update problems, use optimistic locking (`@Version`) or `SELECT ... FOR UPDATE` rather than raising isolation globally.
''', A, ["transactions", "isolation"], True),

("Optimistic vs pessimistic locking in JPA — when to use which?", r'''
**Optimistic** — assume conflicts are rare. Add a `@Version` field; Hibernate updates with `WHERE id=? AND version=?` and increments it. If 0 rows are updated, it throws `OptimisticLockException` -> retry or show "data changed". No DB locks held; great for user-edited records, low contention.

**Pessimistic** — lock the row when reading:
```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("select p from Product p where p.id = :id")
Product lockById(Long id);   // SELECT ... FOR UPDATE
```
Others wait until commit. Use for high-contention critical sections: decrementing inventory in a flash sale, seat booking, wallet balance. Keep transactions short and lock rows in a consistent order to avoid deadlocks; set a lock timeout. An alternative is an atomic conditional update: `update stock set qty = qty - 1 where id = ? and qty > 0`.
''', A, ["jpa", "locking"], True),

("How does Spring Security work? Explain the filter chain.", r'''
Spring Security is a chain of servlet filters. `DelegatingFilterProxy` hands requests to `FilterChainProxy`, which picks the matching `SecurityFilterChain`. Key filters in order: security context loading, CORS, CSRF, logout, authentication filters (form login, basic, bearer token/JWT), `ExceptionTranslationFilter`, and `AuthorizationFilter`.

Authentication: a filter extracts credentials -> `AuthenticationManager` (`ProviderManager`) delegates to an `AuthenticationProvider` (e.g. `DaoAuthenticationProvider` using `UserDetailsService` + `PasswordEncoder`) -> on success the `Authentication` is stored in `SecurityContextHolder` (ThreadLocal) for the request.

Authorization: `AuthorizationFilter` checks `authorizeHttpRequests` rules; `@PreAuthorize` checks at method level. Failures: unauthenticated -> `AuthenticationEntryPoint` (401); forbidden -> `AccessDeniedHandler` (403).
''', I, ["security"], True),

("How do you implement JWT authentication in Spring Boot?", r'''
1. **Login endpoint**: authenticate username/password with `AuthenticationManager`; on success create a signed JWT (claims: `sub`, roles, `iat`, `exp`) using a secret (HS256) or private key (RS256).
2. **Client** stores the token and sends `Authorization: Bearer <jwt>`.
3. **Filter**: a `OncePerRequestFilter` registered before `UsernamePasswordAuthenticationFilter` parses and verifies the signature and expiry, then sets a `UsernamePasswordAuthenticationToken` with authorities in the `SecurityContextHolder`.
4. **Config**: `csrf().disable()`, `SessionCreationPolicy.STATELESS`, permit `/auth/**`, secure the rest.
5. **Refresh tokens**: short-lived access token (~15 min) + longer refresh token stored server-side (DB/Redis) and rotated on use; revoke on logout.

Alternative: use Spring's OAuth2 resource server (`oauth2ResourceServer().jwt()`) with an identity provider like Keycloak, so you don't hand-roll token logic.
''', I, ["security", "jwt"], True),

("What are the drawbacks of JWT and how do you handle logout/revocation?", r'''
Drawbacks:
- **Can't revoke** before expiry because servers don't store them.
- Payload is only Base64-encoded — readable by anyone; never put sensitive data inside.
- Larger than session ids; sent with every request.
- Stolen tokens are valid until expiry; XSS can steal tokens from localStorage.

Mitigations:
- Short access token TTL + **refresh token** rotation (refresh tokens stored server-side so they can be revoked).
- Logout = delete refresh token; for instant revocation keep a **denylist** of token ids (`jti`) in Redis until expiry, or a per-user "token version" claim checked against DB/cache.
- Store tokens in HttpOnly, Secure, SameSite cookies when possible.
- Use asymmetric signing (RS256/ES256) with key rotation via JWKS; validate `iss`, `aud`, `exp`.
''', A, ["security", "jwt"], False),

("What is OAuth2? Explain the Authorization Code flow and Client Credentials flow.", r'''
OAuth2 is a delegated **authorization** framework: a client gets an access token to call a resource server on behalf of a user (or itself) without handling the user's password. Roles: resource owner, client, authorization server, resource server. **OpenID Connect** adds authentication (ID token).

**Authorization Code + PKCE** (web/mobile apps with users):
1. App redirects the user to the auth server's login with `client_id`, `redirect_uri`, `scope`, `code_challenge`.
2. User logs in and consents; auth server redirects back with a short-lived `code`.
3. App exchanges the code (+ `code_verifier`) at the token endpoint for access/refresh/ID tokens.
4. App calls APIs with the access token.

**Client Credentials** (service-to-service, no user): the service posts its `client_id`/`client_secret` to the token endpoint and gets an access token.

Spring: `oauth2Login()`, `oauth2ResourceServer()`, `oauth2Client()`.
''', I, ["security", "oauth2"], True),

("What is CSRF and CORS? When can you disable CSRF?", r'''
**CSRF (Cross-Site Request Forgery)**: a malicious site makes the victim's browser send a request to your site, and the browser automatically attaches session cookies. Spring Security protects by requiring a CSRF token for state-changing requests. You can disable it for **stateless APIs that authenticate via Authorization headers** (JWT), since browsers don't attach those automatically. Keep it if you use cookie-based auth (or rely on SameSite cookies + tokens).

**CORS (Cross-Origin Resource Sharing)**: browsers block JS from calling a different origin unless the server allows it via `Access-Control-Allow-*` headers (with preflight `OPTIONS` requests). Configure allowed origins (e.g. your Angular app), methods and headers:
```java
http.cors(Customizer.withDefaults());  // + a CorsConfigurationSource bean
```
''', I, ["security"], True),

("How do you store passwords securely in Spring Boot?", r'''
Never store plain text or fast hashes (MD5/SHA-256). Use an adaptive, salted, slow hashing algorithm via a `PasswordEncoder`:
```java
@Bean PasswordEncoder encoder() { return new BCryptPasswordEncoder(12); }
user.setPassword(encoder.encode(rawPassword));
encoder.matches(raw, user.getPassword());
```
BCrypt embeds a random salt and cost factor in the hash. Argon2 and SCrypt are memory-hard alternatives. `PasswordEncoderFactories.createDelegatingPasswordEncoder()` stores an `{id}` prefix so you can upgrade algorithms over time. Also: rate-limit login attempts, lock accounts after failures, and never log passwords.
''', B, ["security"], False),

("How do you secure methods with @PreAuthorize? hasRole vs hasAuthority?", r'''
Enable with `@EnableMethodSecurity` (Spring Security 6). Then:
```java
@PreAuthorize("hasRole('ADMIN')")
public void deleteUser(Long id) {}

@PreAuthorize("hasAuthority('orders:write') or #ownerId == authentication.name")
public void update(String ownerId, OrderDto dto) {}

@PostAuthorize("returnObject.owner == authentication.name")
public Document get(Long id) {}
```
- `hasRole('ADMIN')` checks for authority `ROLE_ADMIN` (prefix added automatically).
- `hasAuthority('ROLE_ADMIN')` / `hasAuthority('orders:write')` matches the exact string — used for fine-grained permissions or OAuth2 scopes (`SCOPE_read`).
Method security is AOP-based, so self-invocation isn't checked.
''', I, ["security"], False),

("What's the difference between @Mock and @MockBean (@MockitoBean)?", r'''
- `@Mock` (Mockito) creates a plain mock in a unit test, with `@ExtendWith(MockitoExtension.class)` and `@InjectMocks`. No Spring context — fast.
- `@MockBean` (Spring Boot, deprecated in 3.4 in favour of `@MockitoBean`) creates a Mockito mock **and registers/replaces it as a bean in the Spring ApplicationContext**, so it's injected wherever that bean type is needed. Used in `@WebMvcTest` and `@SpringBootTest`.

Using many different `@MockBean` combinations across test classes prevents context caching (each combination builds a new context), slowing the suite. Prefer plain unit tests with `@Mock` for service logic.
''', B, ["testing"], True),

("@SpringBootTest vs @WebMvcTest vs @DataJpaTest?", r'''
- `@SpringBootTest`: loads the **full** application context — integration tests. With `webEnvironment = RANDOM_PORT` you can call real endpoints using `TestRestTemplate`/`WebTestClient`. Slowest.
- `@WebMvcTest(MyController.class)`: loads only the web layer — controllers, `@ControllerAdvice`, filters, converters, `MockMvc`. Services/repositories must be mocked. Test request mapping, validation, status codes, JSON.
- `@DataJpaTest`: loads JPA components — entities, repositories, `EntityManager`, `TestEntityManager`; each test runs in a rolled-back transaction; uses an embedded DB unless configured (`@AutoConfigureTestDatabase(replace = NONE)` with Testcontainers MySQL). Test custom queries.
''', I, ["testing"], True),

("How do you write a unit test for a service using Mockito?", r'''
```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock UserRepository repo;
    @Mock EmailClient email;
    @InjectMocks UserService service;

    @Test
    void register_savesAndSendsWelcomeMail() {
        when(repo.existsByEmail("a@b.com")).thenReturn(false);
        when(repo.save(any())).thenAnswer(i -> { User u = i.getArgument(0); u.setId(1L); return u; });

        UserDto dto = service.register(new RegisterRequest("a@b.com", "Raj"));

        assertThat(dto.id()).isEqualTo(1L);
        verify(email).sendWelcome("a@b.com");
    }

    @Test
    void register_duplicate_throws() {
        when(repo.existsByEmail("a@b.com")).thenReturn(true);
        assertThrows(DuplicateEmailException.class,
            () -> service.register(new RegisterRequest("a@b.com", "Raj")));
        verify(repo, never()).save(any());
    }
}
```
Follow Arrange-Act-Assert; test behaviour, both happy and failure paths.
''', B, ["testing", "mockito"], True),

("How do you test a REST controller with MockMvc?", r'''
```java
@WebMvcTest(ProductController.class)
class ProductControllerTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper om;
    @MockitoBean ProductService service;

    @Test
    void create_returns201() throws Exception {
        var req = new CreateProductRequest("Pen", new BigDecimal("10"));
        when(service.create(any())).thenReturn(new ProductDto(1L, "Pen", new BigDecimal("10")));

        mvc.perform(post("/api/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content(om.writeValueAsString(req)))
           .andExpect(status().isCreated())
           .andExpect(jsonPath("$.id").value(1))
           .andExpect(jsonPath("$.name").value("Pen"));
    }

    @Test
    void create_invalid_returns400() throws Exception {
        mvc.perform(post("/api/products").contentType(MediaType.APPLICATION_JSON).content("{}"))
           .andExpect(status().isBadRequest());
    }
}
```
If Spring Security is on the classpath, add `@WithMockUser` or `.with(jwt())`.
''', I, ["testing"], False),

("What is Testcontainers and why prefer it over H2 for integration tests?", r'''
Testcontainers starts real dependencies (MySQL, Postgres, Kafka, Redis, LocalStack) in throwaway Docker containers during tests.

Why over H2: H2 is a different database — SQL dialect, functions, locking, JSON columns, index behaviour, and native queries differ from MySQL, so tests can pass on H2 and fail in production (or vice versa). Testcontainers gives production parity.
```java
@SpringBootTest
@Testcontainers
class OrderRepositoryIT {
    @Container @ServiceConnection
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");
    @Autowired OrderRepository repo;
}
```
`@ServiceConnection` (Boot 3.1+) auto-configures the datasource. Use reusable/singleton containers to keep the suite fast. Requires Docker in CI.
''', I, ["testing"], False),

("What is Spring Boot Actuator? Which endpoints have you used?", r'''
Actuator adds production-ready operational endpoints:
- `/actuator/health` — app and dependency status (DB, disk, Redis); `liveness` and `readiness` groups for Kubernetes probes.
- `/actuator/metrics` and `/actuator/prometheus` — Micrometer metrics (JVM memory, GC, HTTP latency, Hikari pool) scraped by Prometheus and shown in Grafana.
- `/actuator/info` — build/git info.
- `/actuator/loggers` — view/change log levels at runtime without restart.
- `/actuator/env`, `/configprops`, `/beans`, `/mappings`, `/conditions` — debugging config.
- `/actuator/threaddump`, `/heapdump` — performance analysis.

Only `health` is exposed over HTTP by default; expose others with `management.endpoints.web.exposure.include` and protect them with security or a separate management port. Custom health checks implement `HealthIndicator`.
''', B, ["actuator", "observability"], True),

("How does caching work in Spring? @Cacheable vs @CachePut vs @CacheEvict?", r'''
Enable with `@EnableCaching`; Spring wraps beans in proxies that check a `CacheManager` before invoking methods.
- `@Cacheable("products")` — return cached value if present for the key; otherwise call the method and store the result.
- `@CachePut` — always call the method and update the cache with the result (on updates).
- `@CacheEvict` — remove an entry (`key = "#id"`) or all entries (`allEntries = true`) on delete/changes.
- `@Caching` combines several.

Options: `key` (SpEL), `condition`, `unless = "#result == null"`, `sync = true` (prevent stampede). Providers: Caffeine (local, TTL/size) or Redis (distributed across instances). Pitfalls: self-invocation, caching mutable objects, stale data (define TTLs, evict on writes), and serialisation of cached objects in Redis.
''', I, ["caching"], True),

("Local cache vs distributed cache (Caffeine vs Redis)?", r'''
**Local (Caffeine)**: in the JVM heap; nanosecond access, no network or serialisation. But each instance has its own copy -> inconsistency across instances, memory limited by heap, lost on restart. Good for small, read-heavy, rarely changing reference data (config, country lists).

**Distributed (Redis)**: shared by all instances; consistent view, survives app restarts, can be huge, supports TTL, pub/sub, atomic counters and distributed locks. Costs a network hop (~sub-ms to ms) and serialisation; Redis becomes a dependency to operate.

Often combined as a two-level cache: Caffeine L1 + Redis L2. Use cache-aside: read cache, else DB and populate; on write, update DB then evict cache.
''', I, ["caching", "redis"], False),

("How does @Async work? What are its pitfalls?", r'''
`@EnableAsync` + `@Async` on a public method makes Spring's proxy submit the call to a `TaskExecutor` and return immediately. Return `void` or `CompletableFuture<T>`.
```java
@Async("notificationExecutor")
public CompletableFuture<Void> sendSms(String phone) { ...; return CompletableFuture.completedFuture(null); }
```
Pitfalls:
- **Self-invocation** -> runs synchronously.
- Default executor may be unsuitable — define a bounded `ThreadPoolTaskExecutor` with a name prefix.
- Exceptions in `void` methods are lost unless you configure `AsyncUncaughtExceptionHandler`.
- `SecurityContext`, MDC and transactions don't propagate to the new thread (use a `TaskDecorator`, `DelegatingSecurityContextAsyncTaskExecutor`).
- Lost on crash — for reliable background work, use a message queue (Kafka/RabbitMQ) instead.
''', I, ["async"], True),

("How do you schedule jobs in Spring Boot, and how do you ensure a job runs only once across multiple instances?", r'''
`@EnableScheduling` + `@Scheduled`:
```java
@Scheduled(cron = "0 30 1 * * *", zone = "Asia/Kolkata")  // 1:30 AM daily
public void settleTransactions() {...}
@Scheduled(fixedDelay = 10_000) public void pollStatus() {...}
```
`fixedRate` measures from the start of the previous run; `fixedDelay` from its end. The default scheduler has a **single thread** — set `spring.task.scheduling.pool.size`.

With N instances, each runs the job. Options to run once:
- **ShedLock**: `@SchedulerLock(name = "settle", lockAtMostFor = "10m")` uses a DB/Redis row as a distributed lock.
- **Quartz** in clustered mode (JDBC job store).
- A Kubernetes **CronJob** or a single dedicated worker deployment.
- Make the job idempotent anyway.
''', I, ["scheduling"], True),

("What is Spring AOP? Explain aspect, advice, pointcut and join point.", r'''
AOP separates cross-cutting concerns (logging, transactions, security, metrics) from business logic.
- **Join point**: a point during execution — in Spring AOP, a method execution on a bean.
- **Pointcut**: expression selecting join points, e.g. `execution(* com.app.service.*.*(..))` or `@annotation(com.app.Audited)`.
- **Advice**: code to run — `@Before`, `@AfterReturning`, `@AfterThrowing`, `@After`, `@Around`.
- **Aspect**: a class combining pointcuts and advice (`@Aspect @Component`).
- **Weaving**: Spring does it at runtime with proxies (JDK dynamic for interfaces, CGLIB subclasses otherwise).

```java
@Around("@annotation(Audited)")
public Object audit(ProceedingJoinPoint pjp) throws Throwable {
    Object r = pjp.proceed();
    auditService.record(pjp.getSignature().getName());
    return r;
}
```
''', I, ["aop"], True),

("JDK dynamic proxy vs CGLIB proxy? Why doesn't self-invocation trigger AOP?", r'''
- **JDK dynamic proxy**: created at runtime implementing the target's interfaces; callers must use the interface type.
- **CGLIB**: generates a subclass of the target class at runtime, overriding methods to add advice. Works without interfaces but can't proxy `final` classes/methods. Spring Boot uses CGLIB by default.

Self-invocation: other beans hold a reference to the **proxy**, which applies advice and then delegates to the real target object. When the target calls `this.otherMethod()`, the call goes directly to the target, not through the proxy, so no `@Transactional`, `@Cacheable`, `@Async` or custom advice runs. Fix by moving the method to another bean, injecting the bean into itself lazily, or using AspectJ weaving.
''', A, ["aop", "proxy"], True),

("How do you call external REST APIs from Spring Boot? RestTemplate vs WebClient vs RestClient vs Feign?", r'''
- **RestTemplate**: classic synchronous client; in maintenance mode (no new features) but still widely used.
- **WebClient**: non-blocking, reactive (`Mono`/`Flux`) client from WebFlux; supports streaming and high concurrency; can be used in MVC apps with `.block()`.
- **RestClient** (Spring 6.1/Boot 3.2): modern fluent **synchronous** API sharing infrastructure with RestTemplate — recommended for new blocking code (and pairs well with virtual threads).
- **OpenFeign** / Spring **HTTP interfaces** (`@HttpExchange`): declarative interface-based clients.

```java
RestClient client = RestClient.builder().baseUrl("https://api.partner.com").build();
UserDto u = client.get().uri("/users/{id}", id).retrieve().body(UserDto.class);
```
Always configure connect/read timeouts, connection pooling, retries with backoff for idempotent calls, and circuit breakers.
''', I, ["rest", "http-client"], True),

("How would you handle file upload and large responses in Spring Boot?", r'''
Upload:
```java
@PostMapping(value = "/files", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public FileDto upload(@RequestParam("file") MultipartFile file) throws IOException {
    validate(file.getContentType(), file.getSize());
    return storage.store(file.getOriginalFilename(), file.getInputStream());
}
```
Limits: `spring.servlet.multipart.max-file-size=10MB`, `max-request-size`. Validate type/size, sanitise filenames, store in object storage (S3) rather than DB/disk, and process heavy files asynchronously. For very large files use pre-signed S3 URLs so clients upload directly.

Large responses: paginate; stream with `StreamingResponseBody` or `ResponseEntity<Resource>`; for JPA exports use `Stream<T>` repository methods with `@Transactional(readOnly = true)` and fetch size so you don't load everything into memory; compress (`server.compression.enabled=true`).
''', I, ["rest"], False),

("How do you implement API versioning and documentation in Spring Boot?", r'''
Versioning approaches:
- **URI**: `/api/v1/orders` — simplest, most common, cache-friendly.
- **Header**: `X-API-Version: 2` or media type `Accept: application/vnd.app.v2+json`.
- **Query param**: `?version=2`.
(Spring Framework 7 / Boot 4 adds built-in API versioning support via `version` attribute on mappings.)
Keep old versions for a deprecation period; avoid breaking changes in place (only add optional fields).

Documentation: **springdoc-openapi** generates OpenAPI 3 specs from controllers and serves Swagger UI at `/swagger-ui.html`. Enrich with `@Operation`, `@Schema`, `@ApiResponse`. Specs can generate client SDKs and support contract-first development.
''', B, ["rest", "api-design"], False),

("What is Spring Data JPA auditing?", r'''
Auditing automatically fills created/modified timestamps and users.
```java
@EnableJpaAuditing
@Configuration class JpaConfig {
    @Bean AuditorAware<String> auditor() {
        return () -> Optional.ofNullable(SecurityContextHolder.getContext().getAuthentication())
                             .map(Authentication::getName);
    }
}

@MappedSuperclass @EntityListeners(AuditingEntityListener.class)
public abstract class Auditable {
    @CreatedDate private Instant createdAt;
    @LastModifiedDate private Instant updatedAt;
    @CreatedBy private String createdBy;
    @LastModifiedBy private String updatedBy;
}
```
Entities extend `Auditable`. For full change history, use Hibernate Envers (`@Audited`) which writes revision tables.
''', B, ["jpa"], False),

("How do you configure multiple datasources in Spring Boot?", r'''
Disable reliance on single auto-configured datasource and define each explicitly:
```java
@Configuration
@EnableJpaRepositories(basePackages = "com.app.orders.repo",
    entityManagerFactoryRef = "ordersEmf", transactionManagerRef = "ordersTx")
class OrdersDbConfig {
    @Bean @Primary @ConfigurationProperties("app.datasource.orders")
    DataSourceProperties ordersProps() { return new DataSourceProperties(); }
    @Bean @Primary DataSource ordersDs() { return ordersProps().initializeDataSourceBuilder().build(); }
    @Bean @Primary LocalContainerEntityManagerFactoryBean ordersEmf(EntityManagerFactoryBuilder b) {
        return b.dataSource(ordersDs()).packages("com.app.orders.entity").build();
    }
    @Bean @Primary PlatformTransactionManager ordersTx(EntityManagerFactory ordersEmf) {
        return new JpaTransactionManager(ordersEmf);
    }
}
```
Repeat for the second DB with different packages. Use `@Transactional("reportsTx")` to choose. For read replicas, use `AbstractRoutingDataSource` routing on `readOnly` transactions.
''', A, ["jpa", "configuration"], False),

("What is HikariCP and how do you tune the connection pool?", r'''
HikariCP is Spring Boot's default JDBC connection pool — fast and lightweight. Opening a DB connection is expensive (TCP + auth), so a pool keeps connections ready.

Key settings (`spring.datasource.hikari.*`):
- `maximum-pool-size` (default 10) — max connections. More isn't better; DBs handle limited concurrent queries. Start ~ (cores x 2) and load test. Remember total = pool size x number of instances must stay under MySQL `max_connections`.
- `minimum-idle`, `idle-timeout`, `max-lifetime` (keep below MySQL `wait_timeout`).
- `connection-timeout` (default 30s) — how long a request waits for a connection; lower it to fail fast.
- `leak-detection-threshold` — logs connections held too long.

Symptoms of exhaustion: "Connection is not available, request timed out". Causes: long transactions, OSIV, slow queries, remote calls inside transactions. Monitor `hikaricp_connections_*` metrics.
''', I, ["jpa", "performance"], True),

("Spring MVC vs Spring WebFlux — when would you choose reactive?", r'''
- **Spring MVC**: servlet-based, thread-per-request, blocking I/O. Simple to write, debug and test; works with JPA/JDBC. With virtual threads (Boot 3.2+), it scales well for I/O-bound workloads.
- **Spring WebFlux**: non-blocking, event-loop (Netty), Reactor `Mono`/`Flux`, backpressure. Handles many concurrent connections with few threads.

Choose WebFlux for: API gateways, streaming (SSE/WebSockets), high-fan-out aggregators calling many slow services, and when the whole stack is non-blocking (R2DBC, reactive Mongo/Redis). Don't choose it with blocking JDBC/JPA (blocking the event loop is disastrous) or when the team lacks reactive experience — the learning curve and debugging cost are high. Spring Cloud Gateway is built on WebFlux.
''', I, ["webflux"], False),

("What is the difference between a Filter and a HandlerInterceptor?", r'''
- **Filter** (`jakarta.servlet.Filter`, often `OncePerRequestFilter`): part of the servlet container, runs **before** DispatcherServlet for every request (including static resources and errors). Can modify/wrap request and response bodies, short-circuit the chain. Used for security, CORS, request logging, correlation IDs, compression.
- **HandlerInterceptor**: part of Spring MVC, runs after the handler is determined and **knows which controller method** will execute. Hooks: `preHandle`, `postHandle`, `afterCompletion`. Used for auth checks per handler annotation, timing, locale, adding model attributes.

Spring Security is implemented as filters. AOP is a third option, working at the bean method level.
''', I, ["mvc"], False),

("How do you add a correlation/trace ID to every log line in a Spring Boot microservice?", r'''
Use MDC (Mapped Diagnostic Context) populated per request:
```java
@Component
public class CorrelationIdFilter extends OncePerRequestFilter {
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String id = Optional.ofNullable(req.getHeader("X-Correlation-Id"))
                            .orElse(UUID.randomUUID().toString());
        MDC.put("correlationId", id);
        res.setHeader("X-Correlation-Id", id);
        try { chain.doFilter(req, res); } finally { MDC.remove("correlationId"); }
    }
}
```
Log pattern: `%X{correlationId}`. Propagate the header on outgoing calls. In Boot 3, **Micrometer Tracing** (with OpenTelemetry/Brave) does this automatically: it adds `traceId`/`spanId` to MDC and propagates W3C `traceparent` headers through RestClient, WebClient and Kafka.
''', I, ["observability", "logging"], True),

("What are @Transactional(readOnly = true) benefits?", r'''
- Hibernate sets flush mode to MANUAL and (since 5.x with Spring) skips keeping dirty-checking snapshots, reducing memory and CPU for large reads.
- The JDBC connection may be set read-only, letting drivers/DBs optimise (MySQL can avoid assigning a transaction id).
- Enables routing to **read replicas** with a routing datasource.
- Documents intent.

It doesn't strictly prevent writes in all setups — treat it as an optimisation hint. A common pattern is `@Transactional(readOnly = true)` at class level of a service, overriding with `@Transactional` on write methods.
''', I, ["transactions", "performance"], False),
]
