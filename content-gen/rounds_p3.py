"""Interview Rounds 2027, part 3: system design, resume deep dive, project deep dive, behavioral, HM & HR."""
from rounds_common import ROUND, S, P
from rounds_p1 import SRC_AMAZON_2025, SRC_UBER, SRC_FLIPKART_2026, SRC_ATLASSIAN, SRC_LEVELOP_GOOGLE, SRC_PREPFULLY
from rounds_p2 import SRC_RAZORPAY, SRC_WALMART, SRC_SPRING_TX, SRC_MYSQL_LOCKING, SRC_FLIPKART_OFFER

SRC_HI_LEVELS = S("The system design interview: what is expected at each level (Hello Interview)",
                  "https://hellointerview.com/blog/the-system-design-interview-what-is-expected-at-each-level")
SRC_HI_DELIVERY = S("System design delivery framework (Hello Interview)",
                    "https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery")
SRC_WHY_FAIL = S("Why senior engineers fail system design interviews (Deep Engineering)",
                 "https://deepengineering.substack.com/p/why-senior-engineers-fail-system-design-interviews")
SRC_STRIPE_IDEM = S("Designing robust and predictable APIs with idempotency (Stripe)",
                    "https://stripe.com/blog/idempotency")
SRC_SWIGGY = S("Swiggy SDE-2 interview experience, 4 yrs (LeetCode Discuss)",
               "https://leetcode.com/discuss/interview-experience/7197132")
SRC_ANGULAR_ZONELESS = S("Angular without ZoneJS (zoneless) guide (angular.dev)", "https://angular.dev/guide/zoneless")
SRC_TIH_SENIOR = S("Behavioral interviews for senior candidates (Tech Interview Handbook)",
                   "https://www.techinterviewhandbook.org/behavioral-interview-senior-candidates/")
SRC_SENIOR_BEH = S("What senior engineers say differently in behavioral rounds (techinterview.org)",
                   "https://www.techinterview.org/post/3233476405/senior-engineers-behavioral-interview-answers/")
SRC_AI_BEH = S("AI-era behavioral interviews 2026: how the questions shifted (techinterview.org)",
               "https://www.techinterview.org/post/3233475312/ai-era-behavioral-interviews-2026-shifted/")
SRC_AMAZON_LP = S("Amazon Leadership Principles (amazon.jobs)",
                  "https://www.amazon.jobs/content/en/our-workplace/leadership-principles")
SRC_ATLASSIAN_VALUES = S("Atlassian company values", "https://www.atlassian.com/company/values")
SRC_HI_BEH = S("Why the behavioral interview matters (Hello Interview)",
               "https://www.hellointerview.com/learn/behavioral/overview/introduction")
SRC_NOTICE = S("The 90-day notice period debate: is it hurting Indian tech hiring? (The People's Board)",
               "https://www.thepeoplesboard.com/hr-voices/the-90-day-notice-period-debate-is-it-hurting-indian-tech-hiring/")

# ---------------------------------------------------------------------------
SYSTEM_DESIGN = ROUND(
    id="system-design-senior", order=9, title="System Design (HLD) at SDE-2 / Senior", icon="🏗️",
    summary="""
    45-60 minutes designing a production system (payments, notifications, booking, delivery) from vague requirements
    to failure handling. It is now standard in SDE-2 loops and the biggest single signal for your level.
    """,
    whoRunsIt=["Amazon", "Flipkart", "Uber", "Razorpay", "PhonePe", "Swiggy", "Atlassian", "Walmart Global Tech",
               "Google", "Goldman Sachs"],
    frequency="Almost every loop",
    weight="~25-30% of a senior decision; the main driver of SDE-1 vs SDE-2 levelling",
    format="""
    - **Duration:** 45-60 minutes. Amazon's SDE-2 HLD round ran 1 hour 45 minutes in a July 2025 report because about 35 minutes of Leadership Principle questions were folded in. Flipkart combined it with the hiring manager round.
    - **Tools:** a virtual whiteboard (Excalidraw, Whimsical, Miro) or a physical board in onsite drives. No code, though you may sketch an API or a table.
    - **Prompts are production-flavoured:** subscription billing on top of a payment gateway (Razorpay), food delivery with four actor types (Amazon), an UrbanClap-style services marketplace (Flipkart), Twitter search (Walmart), monitoring tool (Goldman Sachs), plus the classics: URL shortener, notification system, ticket booking, chat.
    - **Expect follow-ups on** failure paths, idempotency, consistency, observability, cost, and "what would you change if traffic grew 10x?" Some interviewers change a constraint mid-way on purpose.
    """,
    whatTheyTest=[
        "Scoping: functional requirements, non-functional targets, and rough numbers",
        "A clean API and data model, including keys and indexes",
        "A high-level design that actually satisfies the requirements",
        "Depth in two or three areas: consistency, idempotency, partitioning, caching, queues",
        "Failure handling: timeouts, retries, dead letters, outbox, reconciliation",
        "Trade-off reasoning tied to the requirements, not to buzzwords",
        "Adapting calmly when the interviewer changes a constraint",
    ],
    rubric="""
    Hello Interview's levelling guidance matches what Indian SDE-2 loops ask for:

    | | SDE-1 / mid-level | SDE-2 / senior (Raj's target) |
    |---|---|---|
    | Driving | Leads requirements, API and the high-level design; the interviewer drives the deep dives | Drives the whole session, picks the deep dives, and flags limits in their own design |
    | Breadth | Knows what each box does and why it's there | Assumed; fundamentals are only probed if something sounds wrong |
    | Depth | Textbook level | Experience-based detail in about two areas ("we hit this with MySQL locks when...") |
    | Trade-offs | Names the options | Chooses, justifies with the requirements, and states the cost |
    | Failure thinking | Mentions retries | Walks the failure paths: what happens when X is slow, down, or duplicated |

    **No hire signals:** boxes before requirements, technology names that can't be explained, no data model, no
    failure handling, designing Google scale for a small problem, and defending the design when the constraint changes.
    """,
    howToAce="""
    **A time plan for 45-60 minutes** (adapted from Hello Interview's delivery framework)

    1. **Requirements (5 min).** Three to five functional requirements, explicitly out-of-scope items, and non-functional targets: availability, latency, consistency, scale. Do back-of-envelope maths only where it changes a decision ("2M renewals on the 1st of the month is about 25/s spread over a day, but 500/s if we run it all in the first hour").
    2. **Core entities (2 min)** and **API (5 min).** REST endpoints with request and response shapes. Put an **idempotency key** on anything that moves money or creates records.
    3. **High-level design (10-15 min).** Draw the simplest design that satisfies the functional requirements, then walk one request through it end to end.
    4. **Deep dives (15-20 min).** Pick the two or three hardest parts of *this* problem: usually correctness under retries and concurrency, the hot path's scaling, and failure handling. Raise them yourself: "The riskiest part here is double charging, so let me start with that."
    5. **Wrap-up (3 min).** Observability (SLOs, key metrics, alerts), the biggest remaining risk, and what you would build next.

    **Components every SDE-2 answer should include**

    - Numbers: QPS (average and peak), storage growth, read/write ratio.
    - A schema with primary keys, unique constraints and the indexes your queries need.
    - A clear line between synchronous and asynchronous work, and why.
    - A failure table: "If the gateway times out... if the worker crashes... if the queue is down..."
    - The consistency choice for each piece of data (strong for balances, eventual for feeds).

    **Topics to master, in priority order for 2027**

    Caching patterns and invalidation; SQL schema design and indexing; replication and read replicas; partitioning
    and sharding keys; queues, the outbox pattern and idempotent consumers; rate limiting; state machines for payments
    and orders; observability and SLOs; then multi-region and cost as stretch topics.

    **Use your own experience.** Raj has built Spring Boot and MySQL systems. Saying "in my current project, a
    synchronous chain of three services caused cascading timeouts, so here I'd make step 2 asynchronous" is exactly the
    experience-based depth the senior bar asks for.

    **Practise on SwitchPrep**

    One design a week, timed at 45 minutes, drawn in Excalidraw and explained out loud. Alternate between case
    studies and the senior group (payments, idempotency, failure handling, job scheduler). After each one, write
    the failure table from memory.
    """,
    walkthrough="""
    **Prompt (original, similar in spirit to a Razorpay SDE-2 question):** "Design recurring subscriptions on top of
    our existing one-time payment gateway. Merchants create plans (for example a monthly meal plan), customers
    subscribe, and we charge them automatically every cycle until they cancel."

    **Requirements.**

    > **Candidate:** Functional: merchants create plans; customers subscribe with a saved payment mandate; we charge each cycle; we retry failed charges; customers can cancel; merchants get webhooks. Out of scope for now: proration, plan upgrades, and taxes. Is that the right cut?
    >
    > **Interviewer:** Yes.
    >
    > **Candidate:** Scale?
    >
    > **Interviewer:** Assume 2 million active subscriptions. Most renew on the 1st of the month.
    >
    > **Candidate:** So about 1.5 million charges land on one day. Spread over 12 hours, that's roughly 35 per second, but merchants will want them early in the day, so I'll design for a few hundred per second at peak and rate-limit ourselves towards the gateway and banks. The most important non-functional requirement is **never charge twice for the same cycle**. Next is never silently skipping a cycle. Latency barely matters: it's a batch.

    **Entities and API.** Plan, Subscription (status ACTIVE, PAST_DUE, CANCELLED; `next_charge_at`), Invoice (one per
    subscription per period), and PaymentAttempt (several per invoice). `POST /subscriptions` takes an
    `Idempotency-Key` header. `POST /subscriptions/{id}/cancel`. Merchants receive webhooks for `invoice.paid` and
    `invoice.failed`.

    **High-level design.** A scheduler scans subscriptions whose `next_charge_at` is due, partitioned by id range so
    several scheduler instances can share the work. It creates Invoices and publishes `charge-invoice` messages to a
    queue. Charge workers call the gateway. A webhook receiver records asynchronous results from the gateway. A
    notifier sends the merchant webhooks with retries.

    **Deep dive 1: no double charges.**

    > **Candidate:** Three layers. First, the Invoice has a unique key on `(subscription_id, period_start)`, so even if the scheduler runs twice, the second insert fails and no second invoice exists. Second, workers claim an attempt with a conditional update (`status` from PENDING to PROCESSING) and pass `invoice_id + attempt_no` as the idempotency key to the gateway, so a retried request can't create a second charge. Third, the queue is at-least-once, so the consumer is idempotent on that same claim.
    >
    > **Interviewer:** The gateway call times out. Did the customer get charged?
    >
    > **Candidate:** We don't know, and that's the dangerous case. I'd mark the attempt UNKNOWN, never blindly retry it, and query the gateway's status API with the same idempotency key, or wait for its webhook. A reconciliation job compares our UNKNOWN and PROCESSING attempts against the gateway's settlement report every hour. Only a confirmed failure moves to the retry schedule.

    **Deep dive 2: the 1st-of-month spike.**

    > **Candidate:** Pre-generate invoices the night before, so the scheduler isn't on the critical path. Charge workers pull from the queue with a concurrency cap per gateway and per bank, since banks throttle. Add jitter across the morning, and process merchants with earlier promised times first. If the gateway is degraded, a circuit breaker pauses the workers and the queue absorbs the backlog. Nothing is lost, only delayed.

    **Deep dive 3: failed payments.** A dunning schedule retries after 1, 3 and 5 days at different times of day. After
    the final failure, the subscription moves to PAST_DUE and the merchant gets a webhook. Every state change is an
    event in an append-only `subscription_events` table, which helps with support questions and audits.

    **Constraint change.**

    > **Interviewer:** New regulation: customers must be notified 24 hours before every auto-debit, and can object.
    >
    > **Candidate:** That adds a state before charging: invoice created leads to NOTIFIED, and only after the 24-hour window does it become CHARGEABLE. The scheduler now runs two days ahead: it creates invoices and sends notices on day minus 1, and the charge workers only pick up CHARGEABLE invoices. Objections cancel the invoice. The good news is the rest of the design holds, because the invoice state machine was already the backbone.

    **Observability.** SLOs on charge success rate per gateway and per bank, an alert on invoices stuck in UNKNOWN for
    more than an hour, queue lag, and the reconciliation mismatch count, which should be zero.

    **Moments that earned points:** the numbers changed the design (batch, not latency). The top non-functional
    requirement was named and then designed for in three layers. The timeout question was answered with "we don't
    know", followed by a safe procedure. The spike was handled with pre-generation and throttling. The constraint change
    slotted in as one new state because the core abstraction was right. And observability was specific to this system,
    not a generic "add monitoring".
    """,
    commonFailures=[
        "Drawing boxes before agreeing on requirements and scale",
        "No numbers at all, so no decision is justified",
        "Buzzword soup: Kafka, CQRS, sharding and microservices with no reason tied to the problem",
        "No data model, or tables without keys and indexes",
        "Only the happy path: nothing on timeouts, retries, duplicates or crashes",
        "Designing global scale for a modest problem",
        "Waiting for the interviewer to drive the deep dives",
        "Defending the original design when a constraint changes instead of adapting it",
    ],
    practice=[
        P("How to approach system design", "/system-design/concepts/how-to-approach"),
        P("Back-of-envelope estimation", "/system-design/concepts/back-of-envelope"),
        P("Payment system (UPI)", "/system-design/case-studies/payment-system-upi"),
        P("Notification system", "/system-design/case-studies/notification-system"),
        P("Ticket booking (BookMyShow)", "/system-design/case-studies/ticket-booking-bookmyshow"),
        P("Payment processing reliability", "/system-design/senior/payment-processing-reliability"),
        P("Idempotency and exactly-once", "/system-design/senior/idempotency-exactly-once"),
        P("Failure handling and resilience", "/system-design/senior/failure-handling-resilience"),
    ],
    sources=[SRC_HI_LEVELS, SRC_HI_DELIVERY, SRC_WHY_FAIL, SRC_RAZORPAY, SRC_AMAZON_2025, SRC_UBER, SRC_STRIPE_IDEM],
)

# ---------------------------------------------------------------------------
RESUME = ROUND(
    id="resume-deep-dive", order=10, title="Resume Deep Dive (your own stack)", icon="📄",
    summary="""
    45-60 minutes where an engineer picks lines from your resume (Spring Boot, JPA, MySQL, Angular) and keeps asking
    "why?" and "how does that work underneath?" until they find the edge of your knowledge. It can't be bluffed.
    """,
    whoRunsIt=["Walmart Global Tech", "Goldman Sachs", "JPMorgan", "Swiggy", "Flipkart", "PhonePe", "Paytm",
               "Oracle", "Amazon (Dive Deep)"],
    frequency="Almost every loop",
    weight="~20-25% of the decision at Java-heavy companies; often the first technical round",
    format="""
    - **Duration:** 45-80 minutes. Walmart's SDE-3 round 1 ran 80 minutes and covered projects, Java Streams coding, Java 8 interface rules, collections, Spring DI and bean scopes, Hibernate mapping, an SQL query without subqueries, a REST endpoint, and AWS IAM, because it was on the resume.
    - **Setup:** a conversation with small live tasks: write a Streams pipeline, an SQL query, a controller, a JPA mapping.
    - **Style:** the interviewer reads your resume beforehand and drills any keyword. Swiggy's SDE-2 hiring manager went into Kafka, Redis optimisations and database internals. Each answer becomes the next question.
    - **At senior level** they care less about definitions and more about "when does it break, how would you know, what did you do?"
    """,
    whatTheyTest=[
        "Genuine ownership of the work your resume claims",
        "Internals of your own stack: Spring proxies, transactions, JPA, InnoDB, Angular change detection",
        "Production judgement: when a feature breaks and how you'd detect it",
        "Trade-offs between the alternatives you could have chosen",
        "Numbers about your own systems: traffic, data size, latency",
        "Honesty about the limits of what you know",
    ],
    rubric="""
    Interviewers push each topic down a depth ladder and note where you stop:

    | Level | What you can do | Signal |
    |---|---|---|
    | 1. What | Define it | Junior |
    | 2. How used | Show how you used it in your project | SDE-1 |
    | 3. How it works | Explain the mechanism underneath | SDE-1 to SDE-2 |
    | 4. When it breaks | Name failure modes and how you'd detect them | SDE-2 |
    | 5. Alternatives | Compare options and choose for a given constraint | Senior |

    **Strong hire:** reaches level 4-5 on the core of your own stack, with real numbers and at least one production
    story. **No hire:** stays at level 1-2 on things listed as achievements, or bluffs and gets caught. A clear
    "I haven't gone that deep, but here's how I'd reason about it" scores far better than a confident wrong answer.
    """,
    howToAce="""
    **Prepare like this**

    1. **Audit the resume.** Every keyword is a question. Remove what you can't defend at level 3.
    2. **For each bullet, prepare:** the problem, your part, the mechanism, one number, one thing that went wrong.
    3. **Answer in three layers:** a one-line definition, then the internals, then "in my project...".
    4. **Know your own numbers:** requests per day, table sizes, p95 latency, team size, release cadence.

    **The 20 questions Raj must answer alone, without notes**

    *Spring Boot*

    1. What happens between `SpringApplication.run()` and the first request? (context, auto-configuration, bean creation, embedded Tomcat)
    2. How does auto-configuration decide to create a `DataSource`, and how do you see why a bean was or wasn't created? (`@Conditional*`, the `--debug` conditions report)
    3. Why does `@Transactional` do nothing on a private method or a call from the same class? (proxies, self-invocation)
    4. REQUIRED vs REQUIRES_NEW: the inner call throws. What happens to the outer transaction? (rollback-only; checked exceptions don't roll back by default)
    5. Trace a request: filter chain, `DispatcherServlet`, interceptors, controller, `@ControllerAdvice`.
    6. How does your JWT filter validate tokens, and how would you revoke one before it expires?
    7. A singleton bean holds a mutable field and Tomcat runs 200 threads. What breaks?

    *JPA / Hibernate*

    8. Show an N+1 in your code and three fixes. (fetch join, `@EntityGraph`, batch size, DTO projection)
    9. Why does `LazyInitializationException` happen, and why might you disable open-in-view?
    10. What does the persistence context do? (dirty checking, flush timing, first-level cache; why managed entities need no `save()`)
    11. Prevent a lost update on stock count: optimistic `@Version` or pessimistic lock? When would you pick each?

    *MySQL / InnoDB*

    12. Why does the primary key choice matter in InnoDB? (clustered index, random UUID inserts, secondary indexes store the PK)
    13. Index on `(a, b, c)`: which `WHERE` and `ORDER BY` combinations use it? (leftmost prefix, range stops, covering)
    14. Read the `EXPLAIN` of your slowest query: `type`, `key`, `rows`, `Using filesort`.
    15. What does REPEATABLE READ guarantee in InnoDB? (MVCC snapshots, next-key locks, what it doesn't prevent)
    16. How would you diagnose and prevent a deadlock? (`SHOW ENGINE INNODB STATUS`, lock order, retry)
    17. Paginating 10 million rows: why is `OFFSET` slow, and how does keyset pagination fix it?

    *Angular*

    18. Default vs `OnPush` change detection: what triggers a check, and what changes with signals and zoneless (the default from v21)?
    19. `switchMap` vs `mergeMap` vs `concatMap` vs `exhaustMap` for a search box and a save button; how you avoid subscription leaks.
    20. How does an interceptor attach the JWT and refresh on 401 without firing five refresh calls at once?

    **Practise on SwitchPrep:** answer each question out loud in under two minutes, then check the matching core
    chapter and its Q&A.
    """,
    walkthrough="""
    **The resume line:** "Reduced order-search API latency from 2.1 s to 180 ms by optimising JPA queries and adding
    MySQL indexes."

    > **Interviewer:** Tell me about this one. How did you know it was slow, and why?
    >
    > **Candidate:** Support tickets first. Then we confirmed it with Actuator metrics: the p95 for `/orders/search` was about 2.1 seconds for customers with large histories. I turned on SQL logging in a staging copy with production-like data. One search ran 1 query for orders plus 1 per order for its items: a classic N+1. A customer with 300 orders meant 301 queries.
    >
    > **Interviewer:** How did you fix it?
    >
    > **Candidate:** First attempt: `JOIN FETCH o.items` in the repository query. Query count dropped to 1, but Hibernate logged a warning, "firstResult/maxResults specified with collection fetch; applying in memory". Because we paginated, it was fetching *all* of the customer's orders and items and paging in the JVM. That's worse at scale, so I switched to two queries: page the order ids first, then fetch those orders with their items using `WHERE o.id IN (:ids)` and a fetch join. Two queries, correctly paginated.
    >
    > **Interviewer:** And the index?
    >
    > **Candidate:** The page query filtered by `customer_id` and sorted by `created_at DESC`. `EXPLAIN` showed it using the single-column `customer_id` index, followed by `Using filesort`. I added a composite index on `(customer_id, created_at)`. The sort then comes from the index order and the filesort disappeared. Rows examined dropped from thousands to the page size.
    >
    > **Interviewer:** Why not add `status` to the index too? The search filters by status sometimes.
    >
    > **Candidate:** Status has five values, and the filter is optional. Putting it before `created_at` would break the sort for queries without a status filter, because of the leftmost-prefix rule. Putting it after `created_at` doesn't help the range much. With the customer filter, we're already down to at most a few hundred rows, so filtering status from those is cheap. Every extra index also costs on writes, and orders are write-heavy at peak.
    >
    > **Interviewer:** Did you measure that write cost?
    >
    > **Candidate:** Honestly, no. At the time I only checked that insert latency on the dashboard didn't move. If I did it again, I'd run a load test on the insert path before and after, and look at the index size in `information_schema`.
    >
    > **Interviewer:** The orders table grows 50 times. What breaks first?
    >
    > **Candidate:** Deep pages. OFFSET pagination makes MySQL walk and discard all the skipped rows, so page 200 gets slow. I'd move to keyset pagination: `WHERE customer_id = ? AND created_at < :lastSeen ORDER BY created_at DESC LIMIT 20`, with the id as a tiebreaker. After that, archiving orders older than two years into a separate table, and sending search reads to a replica if the primary gets busy.
    >
    > **Interviewer:** You said 180 ms. Where does the remaining time go?
    >
    > **Candidate:** About 40 ms in the two queries, and most of the rest serialising a large DTO graph to JSON. We trimmed the response with a projection for the list view. I didn't take that further because 180 ms met the target we'd agreed with the product team.

    **Moments that earned points**

    - **Evidence:** the latency came from metrics, and the cause from SQL logs on realistic data.
    - **The second-order bug:** the candidate knew why the fetch join plus pagination was wrong, which shows real experience. That's level 4 on the ladder.
    - **Index reasoning** used the leftmost-prefix rule and the write cost, not "more indexes are faster".
    - **Honesty:** "Honestly, no" about the write-cost measurement, followed by exactly how they'd measure it. That earned more trust than a made-up number.
    - **Growth:** the 50x question was answered with the next three steps in the right order.
    - **The full latency budget** was known, and stopping at the agreed target showed judgement.
    """,
    commonFailures=[
        "Resume keywords (Kafka, Docker, AWS, Redis) that can't survive two follow-up questions",
        "Textbook definitions with no project story or numbers behind them",
        "\"We did\" everything, so the interviewer can't find your part",
        "Bluffing internals, then getting caught on the next question",
        "Not knowing your own system's scale: traffic, data size, latency",
        "Dismissing Angular questions with \"I'm mostly backend\" when Angular is on the resume",
        "Listing features used (\"@Transactional, JPA, caching\") without knowing how they fail",
    ],
    practice=[
        P("Transactions: @Transactional, propagation, isolation", "/core/spring-boot?chapter=8"),
        P("N+1, fetching strategies and JPA performance", "/core/spring-boot?chapter=7"),
        P("Auto-configuration, starters and startup", "/core/spring-boot?chapter=3"),
        P("InnoDB indexes: B+trees, composite, covering", "/core/sql?chapter=4"),
        P("InnoDB locking, MVCC and deadlocks", "/core/sql?chapter=8"),
        P("Angular change detection: OnPush, zoneless", "/core/angular?chapter=3"),
        P("Final Round Day 12: Spring Boot + microservices deep dive", "/final-round/12"),
        P("JPA / Hibernate traps", "/traps?area=jpa-hibernate"),
    ],
    sources=[SRC_WALMART, SRC_SWIGGY, SRC_SPRING_TX, SRC_MYSQL_LOCKING, SRC_ANGULAR_ZONELESS, SRC_PREPFULLY],
)

# ---------------------------------------------------------------------------
PROJECT = ROUND(
    id="project-deep-dive", order=11, title="Project Deep Dive", icon="🗂️",
    summary="""
    You present one project end to end and defend its architecture: why it was built that way, what failed, and what
    you'd change. It is often folded into the hiring manager or system design round, and it strongly shapes your level.
    """,
    whoRunsIt=["Razorpay", "Uber", "Flipkart", "Google (Googleyness round, 2026)", "Atlassian", "Swiggy",
               "Walmart Global Tech", "Amazon"],
    frequency="Almost every loop",
    weight="~15% on its own, but it colours how every other round is read",
    format="""
    - **Duration:** 20-45 minutes, usually inside another round. Razorpay's SDE-2 HM round spent its first half on the current project's flaws and how the candidate would redesign it today. Uber's system design round opened with "explain a project you built from scratch". Flipkart's HM round went deep into the candidate's main project.
    - **Google (2026):** the Googleyness and Leadership round now includes a technical discussion of a system or decision from your past work, including its trade-offs.
    - **Setup:** you draw the architecture (whiteboard or Excalidraw). The interviewer then zooms into one component and keeps asking "why?", "what if?" and "how did you know?"
    """,
    whatTheyTest=[
        "Real ownership: what you personally designed, built and decided",
        "Architecture reasoning: why these components and boundaries",
        "Constraints and trade-offs that shaped the design",
        "Impact in numbers: latency, cost, incidents, time saved, users",
        "Self-critique: honest flaws and a credible redesign",
        "Zooming between the big picture and code-level detail on demand",
    ],
    rubric="""
    | Signal | Strong hire | No hire |
    |---|---|---|
    | Framing | 60-second context (users, scale, why it mattered), then architecture | Five minutes on the client's business |
    | Ownership | Clear "I designed / I decided / I fixed", with "we" used honestly for team work | "We" throughout, can't isolate their part |
    | Depth | Explains adjacent components and why they talk the way they do | Knows only their own module |
    | Numbers | Traffic, data size, before-and-after metrics | "It became much faster" |
    | Hindsight | Names a real flaw, explains its cost, proposes a fix that fits the constraints | "Nothing, it was well designed" |
    | Composure | Handles "what if 10x?" by reasoning out loud | Gets defensive or vague |
    """,
    howToAce="""
    **Pick the right project.** Choose the one with the biggest scope *you* drove, ideally with a hard technical
    problem, an incident or a measurable improvement. Not the whole client programme, and not a trivial CRUD
    screen.

    **Build a one-page brief (and rehearse it)**

    1. **Context:** the business problem, users, scale (requests per day, data volume), team size, your role.
    2. **Architecture:** 5-7 boxes you can draw in three minutes. Services, databases, queues, external systems.
    3. **Your part:** two or three things you designed or decided, with the alternatives you rejected.
    4. **Hard problems:** two, each with the symptom, the cause, the fix and a number.
    5. **One incident:** what broke, how you found it, what changed afterwards.
    6. **Hindsight:** one decision you'd reverse, why, and what it cost.
    7. **Results:** before-and-after metrics.

    **The five-minute pitch structure**

    Problem, constraints, architecture, my part, the hard part, the result, what I'd change. Stop at five minutes and
    invite questions: "Which part should I go deeper on?"

    **Service-company framing**

    Client NDAs are real, but they're no excuse for saying nothing. Anonymise ("a US insurance client, about 8,000
    claims a day") and keep the focus on the engineering. Product companies know service work. What they test is
    whether you understood and influenced the system or only closed tickets. If you didn't own the design, own a slice
    of it deeply, and show you understand the rest well enough to critique it.

    **Prepare for the zoom questions**

    - "How does service A know service B failed?"
    - "What happens if this call times out halfway?"
    - "Where is this data cached, and how is it invalidated?"
    - "What happens at 10x traffic?"
    - "How do you deploy it, and how do you roll back?"
    - "How did you test it?"

    **Answering "what would you change?"**

    Pick something real, with a reason and a cost. Good examples: a synchronous call chain that should be
    event-driven; a shared database between services; no idempotency on a retried endpoint; missing observability.
    Avoid "I'd rewrite it in microservices". Also say what you'd *keep*, which shows balanced judgement.

    **Practise on SwitchPrep:** write the brief using the guide on presenting service-company projects, then explain
    the project to a friend who interrupts every 90 seconds with "why?".
    """,
    walkthrough="""
    **Setting:** the second half of a hiring manager round.

    > **Interviewer:** Pick one project and walk me through it.
    >
    > **Candidate:** A claims-processing platform for a US insurance client. Agents and customers submit claims with documents, and adjusters review them. About 8,000 claims a day, peaking at around 40 submissions a minute on Mondays. Angular front end, three Spring Boot services (claims, documents, policy), MySQL, and S3 for files. Five developers. I owned the documents service and the submission flow end to end, and I did most of the Angular work for submission.

    They draw it: Angular to an API gateway, then the claims service, which calls the policy service synchronously
    to validate coverage and the documents service to attach files. MySQL sits behind the claims service, and S3
    behind the documents service.

    > **Interviewer:** Zoom into document upload. What happens if the upload to S3 succeeds but your DB insert fails?
    >
    > **Candidate:** In the first version, exactly that happened: orphaned files in S3 with no record. We found it when storage costs crept up. I changed the flow so that we create the document row first with status PENDING, generate a pre-signed S3 URL so the browser uploads directly, and then an S3 event marks the row as UPLOADED. A nightly job deletes PENDING rows older than 24 hours and their objects. That also took large file traffic off our service.
    >
    > **Interviewer:** What was the hardest bug?
    >
    > **Candidate:** Duplicate claims. About 0.5% of submissions created two claims, which caused double payouts that finance had to reverse manually. Two causes. Users double-clicked submit, and our Angular HTTP interceptor retried on gateway timeouts. I fixed it in three places: the button disables on submit and uses `exhaustMap`, the client generates an idempotency key per form submission, and the claims table has a unique constraint on that key. A duplicate request now returns the original claim. Duplicates went to zero, and the manual reversals stopped.
    >
    > **Interviewer:** If you could redesign one thing, what would it be?
    >
    > **Candidate:** The synchronous call from claims to policy on submission. When the policy service slowed down during their batch window, our submission p95 went from 400 ms to over 5 seconds, and we had a couple of cascading timeouts. If I did it again, I'd accept the claim immediately as SUBMITTED and validate coverage asynchronously through an event, using an outbox table so the event can't be lost. Adjusters only need the coverage result before review, not at submission. I'd keep the modular monolith-ish split we had: three services was the right size for five developers.
    >
    > **Interviewer:** Why didn't you do that at the time?
    >
    > **Candidate:** The client's requirement was to reject uncovered claims at submission. I didn't push back with data then. Now I'd show them the timeout incidents and propose "accept, then notify within a minute" as an alternative.
    >
    > **Interviewer:** How did you measure the effect of your changes?
    >
    > **Candidate:** Duplicate rate from a daily SQL report, orphaned objects from an S3 inventory, and submission p95 from Actuator metrics in Grafana.

    **Moments that earned points:** context with numbers in under a minute. Clear ownership ("I owned...") with honest
    team boundaries. The S3 failure question answered with a real past bug and its evolution, not a textbook pattern.
    The hardest bug came with its cost (double payouts), its causes and a three-layer fix. The redesign was specific,
    tied to an observed incident, kept what worked, and acknowledged the original constraint. And the candidate
    admitted a missed chance to push back, which is a senior trait.
    """,
    commonFailures=[
        "Spending five minutes on the client's business before any engineering",
        "\"We\" throughout, so your contribution is invisible",
        "No diagram, or a diagram that changes as you talk",
        "No numbers for scale or impact",
        "Not understanding components next to your own module",
        "Claiming the design had no flaws",
        "Choosing a trivial project with no hard problem in it",
        "Using the NDA as a reason to say nothing concrete",
    ],
    practice=[
        P("Presenting service-company projects so they sound impactful", "/core/behavioral?chapter=2"),
        P("Distributed transactions: saga, outbox, idempotency", "/core/microservices?chapter=6"),
        P("Resilience patterns with Resilience4j", "/core/microservices?chapter=5"),
        P("Microservices patterns", "/system-design/concepts/microservices-patterns"),
        P("Idempotency and exactly-once", "/system-design/senior/idempotency-exactly-once"),
        P("Senior leadership and influence (senior subject)", "/core/senior-leadership"),
        P("Job switch guide: resume and stories", "/guide"),
    ],
    sources=[SRC_RAZORPAY, SRC_UBER, SRC_FLIPKART_2026, SRC_LEVELOP_GOOGLE, SRC_TIH_SENIOR],
)

# ---------------------------------------------------------------------------
BEHAVIORAL = ROUND(
    id="behavioral-leadership", order=12, title="Behavioral & Leadership", icon="🤝",
    summary="""
    Structured "tell me about a time" questions (Amazon Leadership Principles, Atlassian values, Google's Googleyness)
    with deep follow-up probes. At SDE-2 this round can downlevel or reject a technically strong candidate.
    """,
    whoRunsIt=["Amazon", "Atlassian", "Google", "Uber", "Flipkart", "Walmart Global Tech", "Microsoft", "PhonePe"],
    frequency="Almost every loop",
    weight="~15-20%; frequently decides level (Atlassian and Amazon both downlevel on it)",
    format="""
    - **Dedicated round (45-60 min):** Atlassian's values interview plus a separate managerial round. Amazon's Bar Raiser is heavy on Leadership Principles. Expect 2-4 stories with 3-5 follow-ups each.
    - **Segments in every round:** Amazon asks about two Leadership Principles in each technical round (for example Deliver Results and Learn and Be Curious alongside DSA, Ownership and Earn Trust alongside HLD).
    - **Follow-ups are the real test:** "What exactly did *you* do?", "What would you do differently?", "What did your manager think?", "How did you measure it?"
    - **New in 2026:** AI-related prompts such as "How do you use AI in your daily work?", "Tell me about a teammate over-relying on AI-generated code", "Describe a time AI-generated code failed".
    """,
    whatTheyTest=[
        "Ownership: acting beyond your assigned tasks and owning outcomes",
        "Handling ambiguity: defining the problem and the scope yourself",
        "Disagreement and conflict: data, respect, disagree-and-commit",
        "Failure and learning: a real mistake and a lasting behaviour change",
        "Influence without authority, and mentoring others",
        "Customer and business focus, with impact in numbers",
        "Calibrated use of AI tools and judgement about their output",
    ],
    rubric="""
    | Theme | Mid-level answer | Senior answer (target) |
    |---|---|---|
    | Disagreeing with a lead | Pushed until they agreed; ends in vindication | Made the case with data, lost, committed fully, and named the risk in writing |
    | Conflict with a peer | The peer was wrong | Describes the peer's reasoning fairly; the resolution changed how they work together |
    | Failure | A disguised strength | A real failure with a cost, and a specific habit changed since |
    | Ambiguity | Volunteered for extra work | Defined the problem, set scope, said what they would *not* do |
    | Impact | Worked the weekend and saved the launch | Unblocked others and multiplied the team's output |
    | Mentoring | "I enjoy helping juniors" | A specific person, what they were stuck on, what changed |

    **Weak signals that sink candidates:** passive ownership ("I was assigned..."), noticing problems without acting,
    one-way communication, "we" with no "I", hypothetical answers ("I would..."), and verbose stories that repeat the
    same point.
    """,
    howToAce="""
    **Build a story bank of 8-10 stories** that cover: a disagreement with a lead; a conflict with a peer or another
    team; a real failure; an ambiguous problem you scoped; a production incident you owned; a time you went beyond
    your role; helping or mentoring someone; a tight deadline with a trade-off; learning something fast; a decision
    you changed your mind on. One story can answer several prompts if you change the emphasis.

    **Tell each one as STAR plus a lesson**

    - **Situation (2 sentences):** the context and the stakes. Why did it matter?
    - **Task (1 sentence):** your responsibility, or the gap you chose to fill.
    - **Action (60% of the time):** what *you* did, with the reasoning and the alternatives you rejected.
    - **Result:** numbers (latency, incidents, hours saved, money, customers) and what happened to the people involved.
    - **Lesson:** a behaviour you still use.

    Aim for a two-minute first telling, then let the follow-ups pull out detail. Long monologues lose points.

    **Mining stories from service-company work**

    You have more material than you think: a client escalation you handled; pushing back on an unrealistic estimate; a
    production defect you traced; introducing code review, tests or CI where there were none; onboarding a new joiner;
    a migration (Java 8 to 17, AngularJS to Angular); a design you questioned. Small scope is fine if the behaviour is
    senior.

    **Prepare the follow-up layers for each story**

    What did others think? What would you do differently? How did you measure it? What did your manager say? What
    happened next? If you haven't rehearsed these, the story collapses at the second question.

    **Company specifics**

    - **Amazon:** 16 Leadership Principles. Map at least two stories to each of Ownership, Customer Obsession, Dive Deep, Deliver Results, Have Backbone; Disagree and Commit, Earn Trust, Insist on the Highest Standards, and Learn and Be Curious.
    - **Atlassian:** values such as "Don't #@!% the customer", "Open company, no bullshit" and "Play, as a team". Stories about candour and team play land well there.

    **The AI question:** answer candidly and with calibration. For example: "I use it heavily for boilerplate, tests
    and exploring unfamiliar APIs. I write and review transaction and security code myself, and I never merge
    generated code I can't explain."

    **Practise on SwitchPrep:** draft the bank using the STAR chapter, check it against the Amazon LP chapter, then
    tell each story out loud to a timer.
    """,
    walkthrough="""
    **Question:** "Tell me about a time you disagreed with your tech lead."

    > **Candidate:** Two days before a release, our monthly report endpoint was timing out for large clients: 12 seconds against a 5-second gateway limit. My tech lead proposed adding a Redis cache in front of it. I'd profiled it the day before and found that 80% of the time came from an N+1 query: around 2,000 queries per report. My concern was that a cache would hide the problem, serve stale numbers to finance users, and add a new moving part two days before release.
    >
    > **Candidate:** I wrote a one-page comparison: the cache would take about a day plus invalidation logic, with a stale-data risk. The query fix would take about half a day, with a risk of changing report results, which we could mitigate by comparing outputs for 20 real clients. I showed him the profiler output in a 15-minute call.
    >
    > **Interviewer:** And?
    >
    > **Candidate:** He still chose the cache for this release. His reasoning was fair: the query change touched the reporting logic finance had signed off, and re-certifying it in two days was risky. I disagreed, but I committed. I implemented the cache with a 10-minute TTL and explicit eviction when the underlying data changed, added a test for the eviction, and wrote the stale-data risk into the release note so product knew.
    >
    > **Interviewer:** What happened?
    >
    > **Candidate:** The release went out on time, and timeouts dropped to zero. A week later, a finance user saw yesterday's figures after a late adjustment, because one write path didn't trigger the eviction. Because the risk was already documented, it was a quick conversation rather than an escalation. In the next sprint, my lead asked me to do the query fix. I cut it to 3 queries per report, verified the outputs against the 20 clients, report time went to about 900 ms, and we removed the cache.
    >
    > **Interviewer:** What would you do differently?
    >
    > **Candidate:** Raise it earlier. I'd seen the slow report in a test environment a week before, but didn't flag it because it wasn't my ticket. Now I raise performance concerns in stand-up when I see them, even if they're outside my task. And I try to bring data plus an option the other person can say yes to, rather than just objecting.
    >
    > **Interviewer:** What would your lead say about how you handled it?
    >
    > **Candidate:** I think he'd say I pushed back with evidence, didn't sulk when he decided, and made his decision work. He picked me to lead the performance work in the next quarter, so I think it landed well.

    **Moments that earned points**

    - **Stakes and numbers** in the first 20 seconds: 12 seconds, 2,000 queries, two days to release.
    - **Data, not opinion,** and a written comparison that made the trade-off easy to discuss.
    - **No villain:** the lead's reasoning was described fairly, and it was a reasonable call.
    - **Disagree and commit, done properly:** they built the cache *well* and documented the risk.
    - **An honest outcome,** including the stale-data bug, and how documenting the risk paid off.
    - **The lesson is a behaviour** (raising concerns early, outside their own ticket) rather than a platitude.
    - **The final answer** gives external evidence (being chosen to lead later) instead of self-praise.
    """,
    commonFailures=[
        "Hypothetical answers (\"I would...\") instead of a real past example",
        "\"We\" everywhere, so the interviewer can't credit you",
        "Stories with no tension, no stakes and no numbers",
        "Villain stories that make the other person look stupid",
        "Fake failures (\"I work too hard\")",
        "Six-minute monologues, or one story reused for every question",
        "Collapsing at the second follow-up because only the headline was prepared",
        "Badmouthing the current employer or client",
    ],
    practice=[
        P("The STAR method and building your story bank", "/core/behavioral?chapter=1"),
        P("Amazon Leadership Principles and behavioral themes", "/core/behavioral?chapter=5"),
        P("Behavioral interview Q&A", "/core/behavioral?view=qa"),
        P("Senior leadership: influence, mentoring, ownership", "/core/senior-leadership"),
        P("Behavioral traps", "/traps?area=behavioral"),
        P("Final Round Day 14: final mock + HR", "/final-round/14"),
    ],
    sources=[SRC_AMAZON_LP, SRC_ATLASSIAN_VALUES, SRC_TIH_SENIOR, SRC_SENIOR_BEH, SRC_AI_BEH, SRC_AMAZON_2025,
             SRC_ATLASSIAN, SRC_HI_BEH],
)

# ---------------------------------------------------------------------------
HM_HR = ROUND(
    id="hiring-manager-and-hr", order=13, title="Hiring Manager & HR (incl. CTC and notice period)", icon="💼",
    summary="""
    The final rounds: the hiring manager checks team fit, ownership and motivation, while HR checks CTC, notice period
    and how likely you are to actually join. Weak answers here lose offers or shrink the package.
    """,
    whoRunsIt=["Flipkart", "Swiggy", "Uber", "Walmart Global Tech", "Razorpay", "Amazon", "Atlassian (managerial)",
               "PhonePe"],
    frequency="Almost every loop",
    weight="Pass/fail, and it sets your level and package",
    format="""
    - **Hiring manager (45-60 min):** usually a mix: a project deep dive, a design or techno-managerial discussion, behavioral questions, and the team's work. Swiggy's SDE-2 HM covered system design, design patterns, Kafka, Redis and database internals. Uber's HM went through past projects in depth plus teamwork, conflict and ownership. Walmart's HM asked about urgent last-minute requirements and building a new team.
    - **HR (20-30 min):** why you're switching, why this company, current CTC and its breakup, expected CTC, notice period and buyout, other offers, location, joining date. Then documents: payslips, offer and relieving letters, and background verification.
    - **After the offer:** negotiation on fixed pay, joining bonus, ESOPs, joining date.
    """,
    whatTheyTest=[
        "Motivation: pull towards this role, not just escape from the current one",
        "Stability: tenure pattern and the reasons behind each move",
        "Fit with the team's work, pace and on-call expectations",
        "Ownership and maturity in how you describe past teams",
        "Realistic, well-researched compensation expectations",
        "Joining probability: notice period, competing offers, counter-offer risk",
    ],
    rubric="""
    | Signal | Strong | Red flag |
    |---|---|---|
    | Why switch | Specific pull: product ownership, scale, engineering depth, this team's problems | "Salary" alone, or complaints about the current company |
    | Tenure | Moves explained in a sentence each; 2+ years in the current role | Very short stints with no story (one Swiggy SDE-2 candidate was rejected for switching within 3 months) |
    | CTC | Exact breakup known; expectations anchored to the role's band | Inflated numbers (background checks verify payslips) or "anything is fine" |
    | Notice | Precise, with a realistic plan to shorten it | Vague, or a promise you can't keep |
    | Offers | Honest, no bluffing | Invented offers to create pressure |
    | Questions | Thoughtful questions about the team and success criteria | None |

    Context: in 2025, offer dropout reportedly reached about 38% at Indian product startups, and roughly three
    quarters of dropped offers traced back to the notice period (counter-offers and competing offers). That's why HR
    probes how firmly you intend to join.
    """,
    howToAce="""
    **Hiring manager round**

    1. **Research the team:** product, scale, recent engineering blog posts, the tech stack in the job description.
    2. **Why switch, as a pull:** "I want to own a product end to end, at a scale where design decisions matter, with engineers who'll raise my bar. This team's work on X is exactly that." One sentence about what you've outgrown is fine. A complaint list isn't.
    3. **Expect techno-managerial depth:** a project deep dive, a design discussion, an incident story.
    4. **Ask good questions:** "What would make someone successful in the first six months?", "What's the team's biggest technical challenge this year?", "How does on-call work?", "How are engineers levelled and promoted?"

    **HR round: compensation in India**

    - **Know your CTC breakup exactly:** fixed salary, variable or bonus, employer PF, gratuity, insurance, other allowances. Quote fixed and variable separately. Product companies compare fixed pay.
    - **Expected CTC: anchor to the role, not to a percentage hike.** Product companies pay by level band. A service-company salary plus 30% is a weak anchor when the SDE-2 band starts well above it. Research the band (AmbitionBox, Glassdoor, levels.fyi, friends inside), then give a range whose bottom you'd accept happily: "Based on the role's scope and my research, I'm looking for 16-19 LPA fixed."
    - **If pushed for one number,** give the upper-middle of your range and say it's open to discussion with the full structure.
    - **Never inflate current CTC.** Payslips and bank statements get checked during background verification, and offers are withdrawn over it.
    - **Other offers:** mention real ones, with the figures if they help. Never invent them.

    **Notice period**

    - State it exactly: "90 days per my contract."
    - Show a plan: "My manager has agreed in principle to release me in 60 days after handover. Buyout of the remainder is possible, and I'd ask for a joining bonus to cover it."
    - Start interviewing so that offers land as your notice can start. Many companies prefer candidates with 30-60 day notice, and notice length can be a tie-breaker.
    - **Decide your counter-offer stance before you resign.** If you accept an offer, honour it. Accepting and then backing out burns bridges with recruiters, who talk to each other.

    **Reading the offer letter**

    Fixed vs variable split and how the variable is paid; joining bonus clawback terms; ESOP grant, vesting schedule
    and cliff; notice period at the new company; relocation support; your level or title in writing.

    **Practise on SwitchPrep:** script your "why switch", your CTC breakup and your notice-period answer with the
    salary negotiation chapter, then rehearse them out loud until they take under a minute each.
    """,
    walkthrough="""
    **An HR call after the final technical round (Raj's situation, illustrative numbers).**

    > **HR:** Congratulations on clearing the technical rounds. Can you share your current CTC?
    >
    > **Candidate:** Sure. My CTC is 7.8 LPA: 7.0 fixed, including employer PF, and up to 0.8 variable, paid annually based on performance. I can share payslips whenever you need them.
    >
    > **HR:** And your expectation?
    >
    > **Candidate:** I've researched SDE-2 compensation for backend roles at similar product companies in Bangalore, and I'm looking at 16 to 19 LPA fixed, depending on the overall structure, including any variable and stock.
    >
    > **HR:** That's more than double your current salary. Usually we look at 30-40% on current.
    >
    > **Candidate:** I understand. My current number reflects a service-company band. I'm being evaluated for SDE-2 here, and I cleared the same loop as other SDE-2 candidates. I'd like the offer to reflect the role's band rather than my past employer's pay structure. If the role is levelled lower, I'd want to understand the gap.

    This is the key move: anchoring to the **level**, not a percentage, calmly and without ultimatums.

    > **HR:** What's your notice period?
    >
    > **Candidate:** 90 days per contract. I've already discussed it with my manager: they'll release me in 60 days once handover is done, and the remaining 30 days can be bought out. If we agree on an offer, I can resign within two days and confirm my last working day in writing within a week.
    >
    > **HR:** We'd really prefer 45 days.
    >
    > **Candidate:** I'll ask for 45 with a buyout of the rest. I can't promise it until my manager agrees, and I'd rather give you a date I can keep. Would a joining bonus to cover the buyout be possible? That would make 45 days realistic.
    >
    > **HR:** I'll check. Any other offers?
    >
    > **Candidate:** I'm in the final stage with one other company and expect their decision next week. This role is my first preference because of the team's work on the payments platform, so I'd like to close here if the numbers work.
    >
    > **HR:** Why are you leaving after only two years?
    >
    > **Candidate:** Two years taught me to deliver for clients and work across time zones, but I don't own product decisions or see the impact of my design choices at scale. That's what I want next, and this team works on exactly those problems.

    **A week later: the offer** is 15.5 LPA fixed plus 10% variable. The candidate replies by email: thanks for the
    offer; it's excited about the role; based on its research and the other process, would a fixed component of 17 be
    possible, or alternatively 16 fixed plus a joining bonus that covers the notice buyout. The final offer comes back
    at 16.2 fixed with a 1 lakh joining bonus.

    **Moments that earned points:** an exact, verifiable CTC breakup. An expectation anchored to the level and backed by
    research. A calm reframe of the "percentage hike" objection. A notice-period plan with what's already agreed and
    what isn't, and no false promise. An honest picture of the other offer, plus a stated preference, which lowers the
    company's dropout fear. A "why switch" built on pull, not complaint. And negotiation in writing, with two options
    for HR to choose from.
    """,
    commonFailures=[
        "Inflating current CTC, which background verification catches",
        "\"Any reasonable hike is fine\", which anchors you at the bottom of the band",
        "Quoting expectations only as a percentage of a service-company salary",
        "Vague or over-promised notice periods",
        "Negative talk about the current company or manager",
        "No questions for the hiring manager",
        "Accepting verbally, then quietly shopping the offer or not joining",
        "Not reading variable pay, joining-bonus clawback or ESOP vesting terms",
    ],
    practice=[
        P("Salary discussion and negotiation (India)", "/core/behavioral?chapter=4"),
        P("Tell me about yourself, why switch, why this company", "/core/behavioral?chapter=3"),
        P("Questions to ask the interviewer and round etiquette", "/core/behavioral?chapter=6"),
        P("Behavioral and HR Q&A", "/core/behavioral?view=qa"),
        P("Job switch guide", "/guide"),
        P("Final Round Day 14: final mock + HR", "/final-round/14"),
    ],
    sources=[SRC_NOTICE, SRC_SWIGGY, SRC_WALMART, SRC_UBER, SRC_FLIPKART_OFFER, SRC_ATLASSIAN],
)

ROUNDS_P3 = [SYSTEM_DESIGN, RESUME, PROJECT, BEHAVIORAL, HM_HR]
