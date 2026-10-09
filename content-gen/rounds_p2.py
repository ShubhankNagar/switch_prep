"""Interview Rounds 2027, part 2: machine coding, concurrency, code review, production debugging."""
from rounds_common import ROUND, S, P
from rounds_p1 import (SRC_FLIPKART_2026, SRC_UBER, SRC_TECHINT_2026, SRC_HI_META, SRC_STRIPE, SRC_AMAZON_2025,
                       SRC_LEVELOP_GOOGLE)

SRC_FLIPKART_OFFER = S("Flipkart SDE-2 interview experience [Offer] (LeetCode Discuss)",
                       "https://leetcode.com/discuss/post/6160355/flipkart-sde-2-interview-experience-offer")
SRC_RAZORPAY = S("Razorpay SDE-2 / SSE Bangalore interview experience, Dec 2024 (LeetCode Discuss)",
                 "https://leetcode.com/discuss/interview-question/6179716/")
SRC_PHONEPE = S("PhonePe backend software engineer (3-5 yrs) interview, Oct 2025 (LeetCode Discuss)",
                "https://leetcode.com/discuss/post/7539137/phonepe-backend-software-engineer-3-5-ye-n5mi/")
SRC_WORKAT = S("What is a machine coding round? (workat.tech)",
               "https://workat.tech/machine-coding/article/what-is-a-machine-coding-round-omfn1w54ojlg")
SRC_PRACHUB_MC = S("Machine coding round guide 2026 (PracHub)",
                   "https://prachub.com/resources/machine-coding-round-guide-2026-requirements-architecture-tests-and-working-code")
SRC_MYSQL_LOCKING = S("InnoDB Locking (MySQL 8.0 Reference Manual)",
                      "https://dev.mysql.com/doc/refman/8.0/en/innodb-locking.html")
SRC_JUC = S("java.util.concurrent package summary (Java SE 21 API)",
            "https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/package-summary.html")
SRC_JEP491 = S("JEP 491: Synchronize Virtual Threads without Pinning (OpenJDK)", "https://openjdk.org/jeps/491")
SRC_WALMART = S("Walmart SDE-3 interview experience (Roundz)",
                "https://roundz.substack.com/p/interview-experience-149-walmart-sde3-l3")
SRC_GOOGLE_CR = S("What to look for in a code review (Google Engineering Practices)",
                  "https://google.github.io/eng-practices/review/reviewer/looking-for.html")
SRC_HR_CR = S("Code review questions in interviews (HackerRank knowledge base)",
              "https://hackerrank-knowledge-base.help.usepylon.com/articles/4634293009-code-review-questions-in-interviews")
SRC_LEVELOP_CR = S("Why companies are moving from 'solve this problem' to 'explain this code' (Levelop)",
                   "https://levelop.dev/blog/why-companies-are-moving-from-solve-this-problem-to-explain-this-code")
SRC_SPRING_TX = S("Using @Transactional (Spring Framework reference)",
                  "https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html")
SRC_SRE_TROUBLE = S("Effective Troubleshooting (Google SRE book)", "https://sre.google/sre-book/effective-troubleshooting/")
SRC_SRE_MON = S("Monitoring Distributed Systems: the four golden signals (Google SRE book)",
                "https://sre.google/sre-book/monitoring-distributed-systems/")
SRC_USE = S("The USE Method (Brendan Gregg)", "https://www.brendangregg.com/usemethod.html")

# ---------------------------------------------------------------------------
MACHINE_CODING = ROUND(
    id="machine-coding-lld", order=5, title="Machine Coding / LLD", icon="🧩",
    summary="""
    India's signature product-company round: 90-120 minutes to build a working, extensible, in-memory system (BNPL
    wallet, cab booking, Splitwise) in your own IDE. A review follows where interviewers stress-test your code and add
    a requirement live.
    """,
    whoRunsIt=["Flipkart", "PhonePe", "Uber", "Swiggy", "Razorpay", "CRED", "Myntra", "Udaan",
               "Amazon (LLD discussion)"],
    frequency="Most product companies",
    weight="~25% of the SDE-2 decision at Flipkart, PhonePe and Razorpay; usually an elimination round",
    format="""
    - **Coding:** 90-120 minutes on your own laptop in IntelliJ or similar, in person at Flipkart's offline drives. You get a problem document with **mandatory** and **bonus** requirements. No database, no UI: in-memory storage and a driver `main` or tests.
    - **Review:** 30-90 minutes with one or two engineers. You walk through layers and patterns, they feed in edge cases ("this should never throw an unexpected exception"), you implement an extra strategy or a new requirement live, and sometimes draw a UML class diagram (Flipkart, Jan 2026).
    - **Take-home variant:** PhonePe (Oct 2025) sent a 90-minute unproctored problem to email back, then held a 30-minute call on concurrency and design patterns.
    - **Amazon-style LLD:** a 60-minute class-design discussion (Digital Wallet in a July 2025 SDE-2 loop) with less code and more modelling, plus two Leadership Principle questions.
    - **Recent problems:** BNPL with credit limits and dues (Flipkart, 2026), phonebook (Flipkart), survey service and an in-memory blog search engine (Razorpay), customer-issue assignment (PhonePe), cab booking (Swiggy), plus classics like parking lot, Splitwise and elevator.
    """,
    whatTheyTest=[
        "A working demo: the code runs end to end with a driver or tests",
        "Entity modelling and clean layers (model, repository, service, strategy)",
        "Extensibility: adding a new rule or strategy touches one or two classes",
        "Edge cases and errors handled with clear custom exceptions",
        "Concurrency awareness (two users booking the last seat)",
        "Readable code: naming, small methods, no god class",
        "Explaining and defending design choices in the review",
    ],
    rubric="""
    | Criterion | Strong hire | Hire | No hire |
    |---|---|---|---|
    | Runs | Demo works first time; driver covers every mandatory flow | Works with small fixes during review | Doesn't compile or crashes on the main flow |
    | Requirements | All mandatory plus some bonus | All or nearly all mandatory | Major mandatory features missing |
    | Modularity | Clear layers; services depend on interfaces | Mostly separated, a few leaks | Everything in `Main` or one service class |
    | Extensibility | New requirement in the review lands in minutes, in one place | Lands with moderate edits | Needs rewiring across files, or `if-else` chains on type |
    | Edge cases | Validation and custom exceptions; nothing unexpected escapes | Main edge cases covered | Raw `NullPointerException`s and `RuntimeException`s |
    | Review | Explains trade-offs, admits shortcuts, knows the concurrency fix | Explains when probed | Can't justify the structure |

    Working code is the gate. A beautifully layered design that doesn't run usually fails, while a slightly plain
    design that runs and extends cleanly passes.
    """,
    howToAce="""
    **The 90-minute plan**

    1. **0-10 min: read, clarify, list.** Underline every noun (entities) and verb (operations). Ask what's mandatory and what's bonus, and confirm uniqueness rules, limits and what to show for invalid input. Write the operation list as comments in `Main`.
    2. **10-20 min: skeleton.** Packages `model`, `repository`, `service`, `strategy`, `exception`. Models with fields and enums for states. Repositories as interfaces with an in-memory implementation backed by `ConcurrentHashMap` and `AtomicLong` ids.
    3. **20-60 min: vertical slices.** Implement one mandatory operation end to end (service, repository, driver call), **run it**, then the next. Never have more than 15 minutes of unrun code.
    4. **60-75 min: harden.** Validation, custom exceptions (`InsufficientCreditException`, `AgentUnavailableException`), and state-transition guards.
    5. **75-85 min: bonus features,** chosen for value rather than ease.
    6. **85-90 min: demo script.** The driver prints a readable story of the main flows and one or two failures. Delete dead code.

    **Patterns: use the ones the problem asks for, no more**

    - *Strategy* for anything that says "based on" (pricing, assignment, splitting, ranking).
    - *State* (or an enum with guarded transitions) for lifecycles: order, ride, issue, booking.
    - *Observer* for notifications.
    - *Factory* when objects are created by type.
    - *Singleton* only if asked. Prefer passing dependencies through constructors.

    **Concurrency, in two sentences you can say in any review**

    "Repositories use `ConcurrentHashMap`. Where a check-then-act decides a scarce resource (the last seat, a free
    agent, the credit limit), I lock per entity or use a compare-and-set on the status, so two threads can't both
    win."

    **The review is half the score**

    Expect "add X". Before answering, say *where* it plugs in: "That's a new `AssignmentStrategy` implementation and
    one line in the factory." Then expect stress tests on invalid ids, double actions and empty states. Admit your
    shortcuts plainly: "I skipped persistence of history; here's where it would go."

    **Practise on SwitchPrep**

    One problem a week from the LLD list, timed at 90 minutes in IntelliJ. Afterwards, give yourself an unseen
    requirement (a bonus feature you invent) and time how long it takes to add. If it takes more than 15 minutes, the
    design needs work.
    """,
    walkthrough="""
    **Problem (original, similar in spirit to a 2025 PhonePe prompt):** build an in-memory customer-issue resolution
    system. Mandatory: create an issue (transaction id, type such as PAYMENT or GOLD, subject, email); add agents with
    expertise in issue types; assign an issue to an agent; an agent resolves an issue; view an agent's history; search
    issues by email or type. Bonus: if no agent is free, put the issue on a waitlist and assign it when one frees up.

    **Minute 0-8: clarify.**

    > **Candidate:** Can an agent work on more than one issue at a time?
    >
    > **Interviewer:** One active issue at a time.
    >
    > **Candidate:** If several agents qualify, how do we choose? I'll make it pluggable. Default: the first free agent with that expertise.
    >
    > **Interviewer:** Fine.
    >
    > **Candidate:** Can a resolved issue be reopened?
    >
    > **Interviewer:** Out of scope.

    **Minute 8-18: skeleton.** Entities: `Issue` (id, txnId, type, status, assignedAgentId), `Agent` (id, email,
    expertise set, activeIssueId, history), and an `IssueStatus` enum with OPEN, ASSIGNED, RESOLVED and WAITING.
    Interfaces `IssueRepository` and `AgentRepository` with in-memory implementations. `IssueService` handles create
    and search, and `AssignmentService` handles assign, resolve and the waitlist.

    ```java
    public interface AssignmentStrategy {
        Optional<Agent> pick(Issue issue, Collection<Agent> agents);
    }

    public final class FirstFreeAgentStrategy implements AssignmentStrategy {
        public Optional<Agent> pick(Issue issue, Collection<Agent> agents) {
            return agents.stream()
                .filter(a -> a.isFree() && a.handles(issue.getType()))
                .findFirst();
        }
    }
    ```

    **Minute 18-60: slices, each run immediately.** The candidate builds create-and-search first and runs it, then
    assign and resolve, then history. The status transition lives in one guarded method on `Issue`:

    ```java
    void markAssigned(String agentId) {
        if (status != IssueStatus.OPEN && status != IssueStatus.WAITING)
            throw new InvalidStateException(id, status, IssueStatus.ASSIGNED);
        this.status = IssueStatus.ASSIGNED;
        this.assignedAgentId = agentId;
    }
    ```

    **Minute 60-85: hardening and the bonus.** Unknown ids throw `NotFoundException`. Resolving an issue that isn't
    assigned throws `InvalidStateException`. For the waitlist, an `EnumMap<IssueType, Deque<Issue>>` holds waiting
    issues. When an agent resolves an issue, the service polls the first waiting issue matching that agent's
    expertise. The driver prints the whole story, including two deliberate failures.

    **The review.**

    > **Interviewer:** New requirement: assign to the agent with the fewest resolved issues today, to balance load.
    >
    > **Candidate:** That's a new `AssignmentStrategy`. `LeastLoadedStrategy` filters the same way, then takes `min` by `resolvedToday()`. One new class plus the constructor argument in `Main`. The services don't change.

    They write it in about six minutes and switch the driver over.

    > **Interviewer:** Two requests call `assign` at the same moment and both see agent A as free. What happens?
    >
    > **Candidate:** With my current code, both could assign to A. That's a check-then-act race between `isFree()` and `markBusy()`. The smallest fix is to make the claim atomic on the agent: `activeIssueId` becomes an `AtomicReference<String>`, and claiming is `compareAndSet(null, issueId)`. If the CAS fails, the strategy tries the next candidate. The alternative is `synchronized` on the agent object. The CAS avoids holding a lock while I scan the other agents. In a real service with a database, it would be a conditional update: `UPDATE agent SET active_issue = ? WHERE id = ? AND active_issue IS NULL`, checking that one row changed.
    >
    > **Interviewer:** Why didn't you use a Singleton for the services?
    >
    > **Candidate:** Constructor injection keeps them testable and lets me swap the strategy. `Main` wires everything once, which gives one instance without the global state.

    **Moments that earned points:** the clarifications changed the model (one active issue per agent). The code ran
    after every slice, so the demo worked first time. The lifecycle sits in one guarded method instead of being
    scattered. The new requirement took one class. The race was named precisely (check-then-act between `isFree` and
    `markBusy`), fixed with the smallest correct primitive, and mapped to its database equivalent. Pattern questions
    were answered with reasons, not pattern names.
    """,
    commonFailures=[
        "Code that doesn't run at the end because everything was integrated in the last 10 minutes",
        "Over-design: ten interfaces and five patterns for a 90-minute problem",
        "A god service class, or all the logic in Main",
        "if-else or switch on type where a strategy was obviously requested",
        "No validation, so raw NullPointerExceptions escape during the review's edge-case tests",
        "Chasing bonus features before every mandatory one works",
        "Being unable to say where a new requirement would plug in",
        "No answer when asked what happens if two threads do the same action",
    ],
    practice=[
        P("How to approach LLD and machine coding", "/system-design/lld-fundamentals/how-to-approach-lld"),
        P("Behavioral patterns: Strategy, State, Observer", "/system-design/lld-fundamentals/design-patterns-behavioral"),
        P("Splitwise", "/system-design/lld-problems/splitwise"),
        P("Cab booking", "/system-design/lld-problems/cab-booking-lld"),
        P("BookMyShow (seat locking)", "/system-design/lld-problems/bookmyshow-lld"),
        P("Inventory and order management", "/system-design/lld-problems/inventory-order-management"),
        P("Parking lot", "/system-design/lld-problems/parking-lot"),
        P("Final Round Day 11: Machine Coding / LLD day", "/final-round/11"),
    ],
    sources=[SRC_FLIPKART_2026, SRC_FLIPKART_OFFER, SRC_RAZORPAY, SRC_PHONEPE, SRC_AMAZON_2025, SRC_WORKAT,
             SRC_PRACHUB_MC],
)

# ---------------------------------------------------------------------------
CONCURRENCY = ROUND(
    id="concurrency-round", order=6, title="Concurrency Round", icon="⚙️",
    summary="""
    Sometimes its own round, more often a 15-20 minute segment inside machine coding or a Java round: find the race,
    name the invariant it breaks, fix it in Java or SQL, and show how you'd test it.
    """,
    whoRunsIt=["Uber", "PhonePe", "Walmart Global Tech", "Goldman Sachs", "JPMorgan", "Flipkart", "Razorpay",
               "Atlassian"],
    frequency="Most product companies",
    weight="Often decides SDE-2 vs SDE-1 level at Java-heavy companies",
    format="""
    - **As a segment (most common):** inside a machine-coding review ("two requests assign the same agent"), a Java fundamentals round (`wait` vs `sleep`, `synchronized`, `volatile`), or a design round ("two workers pick the same job").
    - **As a dedicated round (45-60 min):** implement something thread-safe (bounded blocking queue, rate limiter, LRU cache, a scheduler), or review a snippet and explain the race. Uber's SDE-2 machine coding explicitly covered asynchronous programming, thread synchronisation and parallel execution.
    - **Database flavour:** conditional updates, optimistic locking with `@Version`, `SELECT ... FOR UPDATE` and `SKIP LOCKED` job claiming, isolation levels, deadlocks.
    - **Modern Java:** `CompletableFuture` composition and timeouts; virtual threads (Java 21) and pinning, which JDK 24's JEP 491 largely removed for `synchronized`.
    """,
    whatTheyTest=[
        "Naming race shapes precisely: check-then-act, read-modify-write, unsafe publication, lazy init",
        "Choosing the smallest correct primitive (Atomic*, ConcurrentHashMap.compute, lock, semaphore, queue)",
        "Knowing that a JVM lock does nothing across multiple service instances, and moving the guard to the DB or Redis",
        "Database concurrency: isolation levels, row locks, optimistic vs pessimistic locking",
        "Crash and retry semantics: leases, idempotency, at-least-once processing",
        "Deadlock causes and prevention (lock ordering, timeouts)",
        "Testing concurrent code with latches, thread pools and repeated runs",
    ],
    rubric="""
    | Signal | Strong hire | No hire |
    |---|---|---|
    | Diagnosis | Describes the exact interleaving: "T1 reads QUEUED, T2 reads QUEUED, both write RUNNING" | "There might be a race somewhere" |
    | Invariant | States what must stay true: "a job has at most one active owner" | Talks about threads, not about correctness |
    | Fix | Smallest correct scope, and right for the deployment (single JVM vs many instances) | `synchronized` on everything, or `volatile` on a counter |
    | Trade-offs | Contention, lock hold time, throughput, failure modes | One answer, no alternatives |
    | Failure thinking | Worker crash, retries, duplicate delivery, idempotency | Assumes nothing ever dies mid-operation |
    | Proof | A concrete test: N threads, a latch, an assertion on the invariant | "I'd test it manually" |

    The phrase interviewers listen for is a four-part answer: **the race, the broken invariant, the prevention, the
    test.**
    """,
    howToAce="""
    **Answer every concurrency question in four beats**

    1. **Race:** the interleaving, step by step.
    2. **Invariant:** what must always be true, in business terms.
    3. **Prevention:** the primitive, its scope, and why it's enough.
    4. **Proof:** how a test would fail before the fix and pass after.

    **The race shapes to recognise on sight**

    - *Check-then-act:* `if (!map.containsKey(k)) map.put(k, v)`, `if (seat.isFree()) seat.book()`.
    - *Read-modify-write:* `count++`, `balance = balance - amount`, an entity loaded, modified and saved.
    - *Unsafe publication / lazy init:* double-checked locking without `volatile`, a shared `HashMap` or `SimpleDateFormat` in a singleton bean.
    - *Lost update in the database:* two transactions read the same row and both write. The default REPEATABLE READ does **not** stop this for read-then-write code.

    **Java toolbox you should be able to write from memory**

    - `ConcurrentHashMap.merge` and `compute` for atomic per-key updates. `AtomicLong` and `LongAdder` for counters.
    - A bounded blocking queue with `ReentrantLock` and two `Condition`s (`notFull`, `notEmpty`), using `while` loops around `await()`.
    - `ExecutorService` plus `CountDownLatch` to release N threads at once in a test.
    - `CompletableFuture.allOf(...)` with `orTimeout`, and `exceptionally` for fallbacks.
    - Lock ordering (always lock the lower account id first) to prevent deadlock in transfers.

    **Database toolbox (this is what makes it work across instances)**

    - **Conditional update:** `UPDATE ... SET status='RUNNING' WHERE id=? AND status='QUEUED'`, then check that exactly one row changed.
    - **Optimistic locking:** a `@Version` column. JPA adds `AND version=?` and throws on conflict, so you retry or reject.
    - **Pessimistic locking:** `SELECT ... FOR UPDATE` inside a short transaction. Add `SKIP LOCKED` (MySQL 8+) so workers grab different rows.
    - **Unique constraints** as the last line of defence for idempotency (one refund per request id).

    **Decide the scope out loud**

    "Is this one JVM or several instances?" If several, a Java lock protects nothing and the guard must live in the
    database, in Redis, or in a single-partition queue. Saying this early is a strong senior signal.

    **Practise on SwitchPrep**

    Work through the practical concurrency subject and the concurrency traps. Then take every LLD problem you've
    solved and ask yourself: "Which operation decides a scarce resource, and what happens if two threads do it at
    once?"
    """,
    walkthrough="""
    **Prompt:** "Our Spring Boot job runner has three instances. Each one polls like this. What's wrong, and how do you
    fix it?"

    ```java
    @Scheduled(fixedDelay = 1000)
    public void poll() {
        Job job = jobRepository.findFirstByStatusOrderByCreatedAt(Status.QUEUED);
        if (job == null) return;
        job.setStatus(Status.RUNNING);
        jobRepository.save(job);
        processor.process(job);              // sends an email and charges a card
    }
    ```

    > **Candidate:** The race is a check-then-act across instances. Instance A reads job 42 as QUEUED. Before A saves, instance B runs the same query and also gets job 42. Both set RUNNING, both save, and both process. The customer gets charged twice. The invariant is: *a job has at most one active owner, and its side effects happen once*. A `synchronized` method wouldn't help, because the three instances are separate JVMs. The guard has to be in the database.
    >
    > **Interviewer:** What would you change?
    >
    > **Candidate:** Make the claim atomic with a conditional update and check how many rows changed:

    ```java
    @Modifying
    @Query(nativeQuery = true, value =
        "UPDATE job SET status = 'RUNNING', owner = :owner, lease_until = :lease " +
        "WHERE id = :id AND status = 'QUEUED'")
    int claim(@Param("id") long id, @Param("owner") String owner, @Param("lease") Instant lease);
    ```

    > **Candidate:** The worker calls `claim(...)` in its own short transaction and processes the job only if it returns 1. InnoDB takes a row lock for the update, so the second instance's update waits, then re-checks the condition, finds RUNNING, and changes 0 rows. For throughput, instead of every instance fighting over the oldest row, I'd claim a batch with `SELECT id FROM job WHERE status='QUEUED' ORDER BY created_at LIMIT 10 FOR UPDATE SKIP LOCKED` inside a short transaction, then update those ids. Each instance gets different rows without waiting.
    >
    > **Interviewer:** Why not `@Version` optimistic locking?
    >
    > **Candidate:** That works too. The second save throws `OptimisticLockException` and we skip the job. But under contention most attempts fail and retry, which wastes queries. For a hot queue, `SKIP LOCKED` is better. For rare conflicts, like editing a profile, `@Version` is simpler.
    >
    > **Interviewer:** Instance A claims job 42 and then crashes halfway through processing.
    >
    > **Candidate:** That's why I added `leaseUntil`. A sweeper re-queues RUNNING jobs whose lease has expired. Long jobs extend the lease with a heartbeat. But it means a job can now run twice: once by the crashed worker, which might have sent the email before dying, and once after the re-queue. So delivery is at-least-once, and the side effects must be idempotent. The charge call passes the job id as an idempotency key to the payment provider. The email table has a unique constraint on `(job_id, template)`, so the insert that records "sent" fails on the second attempt.
    >
    > **Interviewer:** How would you test the claim?

    ```java
    @Test
    void onlyOneWorkerWinsTheClaim() throws Exception {
        long id = jobs.save(Job.queued()).getId();
        int workers = 8;
        ExecutorService pool = Executors.newFixedThreadPool(workers);
        CountDownLatch go = new CountDownLatch(1);
        List<Future<Integer>> results = new ArrayList<>();
        for (int i = 0; i < workers; i++) {
            String owner = "w" + i;
            results.add(pool.submit(() -> { go.await(); return claimer.claim(id, owner, Instant.now().plusSeconds(60)); }));
        }
        go.countDown();
        int winners = 0;
        for (Future<Integer> f : results) winners += f.get();
        assertEquals(1, winners);
    }
    ```

    > **Candidate:** I'd run it against real MySQL in Testcontainers, not H2, because locking behaviour differs. And I'd repeat it a few hundred times with `@RepeatedTest`. The original code fails this test intermittently, which is exactly the point.

    **Moments that earned points:** the interleaving was spelled out with concrete instances and a job id. The
    invariant was stated in business terms (a double charge). "Separate JVMs" ruled out Java locks before the
    interviewer could ask. Two database strategies were compared on contention. The crash follow-up led naturally to
    leases and then idempotency, and the candidate pointed out the cost (at-least-once). The test was concrete, ran
    against the real database, and was repeated.
    """,
    commonFailures=[
        "Adding synchronized to a service that runs on several instances",
        "Using volatile for a counter (volatile gives visibility, not atomicity for count++)",
        "containsKey then put on a ConcurrentHashMap, which is still a check-then-act race",
        "Holding a lock or a DB transaction while calling a remote service",
        "Assuming @Transactional or REPEATABLE READ prevents lost updates in read-modify-write code",
        "Inconsistent lock ordering in transfers, leading to deadlock",
        "Ignoring crashes and retries, so the fix still allows duplicate side effects",
        "No test, or a single-threaded test that can't fail",
    ],
    practice=[
        P("Practical concurrency (senior subject)", "/core/concurrency-practical"),
        P("Concurrency utilities: locks, executors, CompletableFuture", "/core/java?chapter=12"),
        P("ConcurrentHashMap and concurrent collections", "/core/java?chapter=5"),
        P("Concurrency for LLD", "/system-design/lld-fundamentals/concurrency-for-lld"),
        P("InnoDB locking, MVCC and deadlocks", "/core/sql?chapter=8"),
        P("Distributed job scheduler", "/system-design/senior/distributed-job-scheduler"),
        P("Concurrency traps", "/traps?area=concurrency"),
    ],
    sources=[SRC_UBER, SRC_PHONEPE, SRC_WALMART, SRC_MYSQL_LOCKING, SRC_JUC, SRC_JEP491],
)

# ---------------------------------------------------------------------------
CODE_REVIEW = ROUND(
    id="code-review-round", order=7, title="Code Review Round", icon="🔍",
    summary="""
    You get a pull request or a file with planted bugs and design problems. You score by finding the issues that would
    break production first, then explaining impact and fixes like a reviewer people trust.
    """,
    whoRunsIt=["Google (code comprehension)", "Meta (bug phase of the AI round)", "Atlassian",
               "Teams using HackerRank or CoderPad review tasks", "AI-first startups"],
    frequency="Some companies",
    weight="~10-15% where it appears; growing because AI made writing code cheap and judging it valuable",
    format="""
    - **Duration:** 30-60 minutes, sometimes as a segment of a coding or HM round.
    - **Setup:** a diff view with inline comments (HackerRank's code-review question shows split or unified diffs, and the interviewer's rubric is hidden from you), or a file shared on screen. Usually 80-300 lines. For Raj's profile, expect Java with Spring Boot and JPA.
    - **Variants:** "explain this code", then "what's wrong with it", then "fix the worst issue". Increasingly the code is AI-generated and looks clean: confident, idiomatic, subtly wrong.
    - **Follow-ups:** "Are you sure that's a bug?", "Which one would you block the PR for?", "How would you phrase that comment to a junior?"
    """,
    whatTheyTest=[
        "Reading unfamiliar code fast and stating its intent correctly",
        "Ranking findings by production risk: correctness, data loss, security before style",
        "Concrete impact and a concrete fix for each finding",
        "Spring, JPA and Java pitfalls: transaction boundaries, N+1, thread-safety, resource leaks",
        "Reviewing tests: what's missing, what's tested wrongly",
        "Tone: separating blockers from nits, collaborating rather than lecturing",
        "Holding a position under pushback when right, and updating when wrong",
    ],
    rubric="""
    | Signal | Strong hire | Hire | No hire |
    |---|---|---|---|
    | Prioritisation | Top 3 findings are the top 3 risks, called out first | Finds them, but mixed in with nits | Leads with formatting and naming |
    | Depth | Explains the failure scenario ("two retries both refund") | Names the issue | "This looks off" |
    | Fixes | Specific and proportionate | Generic ("add validation") | None, or "rewrite it" |
    | Coverage | Correctness, security, failure handling, performance, tests | Two or three areas | Style only |
    | Communication | Blocker vs nit labels; kind, precise wording | Clear | Harsh or vague |

    Google's review guide orders concerns as design, functionality, complexity, tests, then naming, comments and
    style, and says personal preferences should be marked "Nit:". Interview rubrics follow the same order.
    """,
    howToAce="""
    **A fixed order of passes (about 25 minutes for 150 lines)**

    1. **Intent (2 min).** Read the PR description, the method names and the tests. Say in one sentence what the code is meant to do. Many planted bugs are mismatches between intent and behaviour.
    2. **Correctness and data integrity.** Business rules, boundaries, null and empty cases, money arithmetic, state transitions, idempotency, transaction boundaries, races.
    3. **Security.** Injection (string-built SQL or JPQL), missing authorisation checks, secrets or personal data in logs, unvalidated input.
    4. **Failure handling.** Swallowed exceptions, remote calls without timeouts, retries without backoff or idempotency, partial failure between the DB and an external call.
    5. **Performance.** N+1 queries, `findAll()` then filtering in memory, unbounded caches and collections, work inside loops.
    6. **Tests.** Is the risky path tested? Are the assertions meaningful?
    7. **Design and readability.** Layering, naming, duplication. Mark these as nits unless they hide bugs.

    **Comment template**

    `[blocker] What: refund amount isn't checked against what was already refunded. Impact: repeated partial refunds can exceed the payment. Fix: check amount <= paid - refunded inside the same locked update.`

    **Finish with a ranked summary:** "I'd block on 1-3, want 4-5 fixed before release, and 6+ are suggestions."

    **The Spring and Java bugs that get planted most often**

    - `@Transactional` on a private method, or called from the same class, so no proxy and no transaction.
    - A remote HTTP call inside a DB transaction.
    - `catch (Exception e)` that logs and returns success.
    - `double` for money, `new BigDecimal(0.1)`, or `BigDecimal.equals` where scale differs.
    - `equals` without `hashCode` on a class used as a map key or in a set.
    - Shared mutable state in a singleton bean (`HashMap`, `SimpleDateFormat`).
    - `Optional.get()` without a check. Streams or connections never closed.
    - N+1 lazy loading in a loop. `findAll()` on a large table.
    - Missing idempotency on a POST that moves money.
    - `LocalDateTime` used for instants across time zones.

    **When challenged**

    Re-derive the bug from a concrete input instead of repeating yourself. If you were wrong, say so quickly. Updating
    gracefully is itself a positive signal.

    **Practise on SwitchPrep**

    Use the testing and code review subject and the Spring and JPA traps as a bug catalogue. Then review real open
    source PRs, or your own old code, out loud with a 25-minute timer, and write a ranked summary every time.
    """,
    walkthrough="""
    **The code (original, condensed):** a refund method written for an order service.

    ```java
    @Service
    public class RefundService {
        private static final Map<Long, Order> cache = new HashMap<>();
        @Autowired private OrderRepository orders;
        @Autowired private PaymentGatewayClient gateway;

        public ResponseEntity<String> refund(Long orderId, double amount) {
            try {
                return doRefund(orderId, amount);
            } catch (Exception e) {
                log.error("refund failed");
                return ResponseEntity.ok("REFUND_QUEUED");
            }
        }

        @Transactional
        private ResponseEntity<String> doRefund(Long orderId, double amount) {
            Order order = cache.computeIfAbsent(orderId, id -> orders.findById(id).get());
            log.info("Refunding card {} amount {}", order.getCardNumber(), amount);
            if (amount <= order.getPaidAmount()) {
                gateway.refund(order.getPaymentId(), amount);          // HTTP call, 2-8 s
                order.setRefundedAmount(order.getRefundedAmount() + amount);
                order.setStatus("REFUNDED");
                orders.save(order);
            }
            return ResponseEntity.ok("OK");
        }
    }
    ```

    > **Candidate:** Intent first: refund part or all of an order's payment through the gateway and record it. I'll go correctness first, then security, then the rest. I'll rank at the end.
    >
    > **Candidate:** **One, money can be lost.** The check compares the amount against `paidAmount` and ignores `refundedAmount`. Three refunds of 400 on a 1,000 order all pass. On top of that, there's no idempotency key, so a client retry after a timeout refunds again. And two concurrent requests can both pass the check. Fix: accept an idempotency key with a unique constraint on the refunds table, check `amount <= paid - refunded`, and make the update conditional (or use `@Version`). Pass the same key to the gateway so its side is idempotent too.
    >
    > **Candidate:** **Two, there's no transaction at all.** `@Transactional` sits on a private method called from inside the same class. Spring's proxy only intercepts external calls through the proxy, so this annotation does nothing. And if it did work, it would hold a DB connection open during a 2-8 second HTTP call. Fix: a short transaction to reserve the refund (status REFUND_PENDING), the gateway call outside any transaction, then a second short transaction to mark it complete or failed. A reconciliation job picks up stuck PENDING rows.
    >
    > **Candidate:** **Three, failures are reported as success.** Any exception, including `NoSuchElementException` from `findById(...).get()` on a bad id, returns 200 "REFUND_QUEUED", but nothing is queued. Support will tell customers their refund is coming when it isn't. Fix: a 404 for an unknown order, a real error for a gateway failure, and log the exception with the order id.
    >
    > **Interviewer:** What about the cache? Is that really a problem or just style?
    >
    > **Candidate:** It's real. Four things. A static `HashMap` shared across request threads isn't thread-safe, and concurrent `computeIfAbsent` can corrupt it. It never evicts, so it grows until the JVM runs out of memory. It returns stale orders, so the second refund reads an old `refundedAmount`, which makes bug one worse. And it holds JPA entities outside their persistence context. I'd delete it. Reading one order by primary key is cheap.
    >
    > **Candidate:** **Five, compliance:** the full card number is logged at INFO. That's a PCI problem and likely a security incident in itself. Log the order id and a masked token instead.
    >
    > **Candidate:** **Six,** `double` for money gives rounding errors. Use `BigDecimal` with an explicit scale, or a `long` in paise.
    >
    > **Candidate:** **Nits:** field injection instead of constructor injection. A service returning `ResponseEntity`, so HTTP concerns leak into the service layer. Status as a raw string where an enum belongs. And no tests: I'd want at least repeated partial refunds, the same idempotency key twice, and a gateway timeout.
    >
    > **Candidate:** **Ranked:** I'd block on 1, 2, 3 and 5. Four and six must be fixed before release. The rest are suggestions.

    **Moments that earned points:** stating intent first. Opening with the issue that loses money, with a concrete
    scenario (three refunds of 400). Knowing *why* the annotation fails (proxy, self-invocation), not just that it
    "might not work". Explaining the real-world cost of the swallowed exception. Defending the cache finding with four
    specific failure modes when challenged. Ranking at the end, and saving the style comments for last, labelled as
    nits.
    """,
    commonFailures=[
        "Opening with formatting, naming and missing comments",
        "A flat list of 15 findings with no severity",
        "Vague comments (\"this could be better\") without impact or fix",
        "Missing the business-logic bug because only Java-level issues were checked",
        "Not reading the tests, or not noticing that there are none",
        "Proposing a full rewrite instead of targeted fixes",
        "Folding immediately under pushback, or digging in without re-checking",
    ],
    practice=[
        P("Testing and code review (senior subject)", "/core/testing-code-review"),
        P("@Transactional: propagation, isolation and pitfalls", "/core/spring-boot?chapter=8"),
        P("Spring AOP and proxies (why self-invocation fails)", "/core/spring-boot?chapter=12"),
        P("The N+1 problem and JPA performance", "/core/spring-boot?chapter=7"),
        P("Spring traps", "/traps?area=spring"),
        P("JPA / Hibernate traps", "/traps?area=jpa-hibernate"),
        P("Security for backend engineers", "/core/security"),
        P("Payment processing reliability", "/system-design/senior/payment-processing-reliability"),
    ],
    sources=[SRC_GOOGLE_CR, SRC_HR_CR, SRC_LEVELOP_CR, SRC_TECHINT_2026, SRC_SPRING_TX, SRC_HI_META],
)

# ---------------------------------------------------------------------------
DEBUGGING = ROUND(
    id="debugging-production-round", order=8, title="Debugging & Production Incident Round", icon="🚨",
    summary="""
    Either fix a failing test in an unfamiliar repo (a "bug squash") or talk through a live incident such as "p99
    latency tripled after the deploy". Either way you are scored on method: hypotheses, evidence, mitigation first,
    prevention after.
    """,
    whoRunsIt=["Stripe (bug squash)", "Google (code comprehension)", "Meta (bug phase)", "Amazon (Dive Deep)",
               "Uber", "Razorpay", "PhonePe", "Atlassian"],
    frequency="Some companies",
    weight="~10-20% where it's a round; incident questions also feed Ownership and Dive Deep signals in HM rounds",
    format="""
    **Flavour A: hands-on bug squash (45-60 min).** An unfamiliar repository with a failing test or an issue
    description. Stripe lets you use your own IDE and language and look up docs and StackOverflow. A clear diagnosis
    can count for more than a finished fix. AI is usually off.

    **Flavour B: incident scenario (30-45 min, whiteboard).** The interviewer describes symptoms and reveals dashboards,
    logs and recent changes only when you ask for them. Common scenarios: a regression after a deploy, one bad host or
    shard, cache-driven DB overload, a cold cache after a restart, connection pool exhaustion, a retry storm.

    **Flavour C: embedded.** "Tell me about the worst production issue you handled" in HM and behavioral rounds,
    followed by a technical drill into it.
    """,
    whatTheyTest=[
        "A systematic method instead of random poking",
        "Asking for the right signals: latency, traffic, errors, saturation, and what changed",
        "Mitigating impact before chasing the root cause",
        "Reading stack traces, logs, thread dumps and query plans",
        "Knowing JVM, Spring and MySQL failure modes (pool exhaustion, GC, locks, slow queries)",
        "Verifying the fix and adding guardrails so it doesn't recur",
        "Calm, clear communication while under pressure",
    ],
    rubric="""
    | Signal | Strong hire | No hire |
    |---|---|---|
    | Opening | Confirms the symptom and scope: who, since when, how bad | Names a cause in the first 30 seconds |
    | Evidence | Asks for golden signals, recent changes, healthy-vs-unhealthy comparison | Guesses, or asks for "all the logs" |
    | Priorities | Mitigates first (rollback, flag off, shed load), then diagnoses | Debugs while users keep failing |
    | Hypotheses | Ranked by likelihood and cost to test; each test can rule one out | Changes several things at once |
    | Depth | Connects symptom to mechanism ("threads blocked on the pool because...") | Stops at "the DB was slow" |
    | Closure | Verifies recovery, adds an alert, a test, a runbook, a postmortem | Stops once the graph goes green |

    Google's SRE book makes the same point. In a major outage your first job is to make the system work, even before
    you know why it broke, like a pilot who lands the plane before troubleshooting.
    """,
    howToAce="""
    **The incident loop (say it, then walk it)**

    1. **Confirm the symptom.** Which endpoints, users, regions? Since when? What's the error rate or latency versus the baseline?
    2. **Check the four golden signals:** latency, traffic, errors, saturation. For each resource, check the **USE** method: utilisation, saturation, errors (CPU, memory, threads, DB connections, disk, network).
    3. **Ask what changed:** deploys, config or feature flags, traffic pattern, dependency releases, data growth, certificate expiry.
    4. **Compare healthy with unhealthy:** one host or all? One shard? One customer? One endpoint?
    5. **Mitigate:** roll back, switch a flag off, scale out, shed or rate-limit load, fail over, drain a bad host.
    6. **Verify** that the metrics recover and the symptom is gone for users.
    7. **Find the root cause and add a guardrail:** a fix plus a regression test, an alert on the leading signal, a timeout or limit, and a blameless postmortem.

    **The hands-on loop (bug squash)**

    Reproduce by running the failing test. Read the assertion and the stack trace, starting from the first frame in
    *your* code. Narrow down by bisecting inputs or commits, or by adding a log line. State a hypothesis, make the
    minimal fix, add a regression test, and explain. Narrate what you've **ruled out**. That counts even if time runs
    out.

    **The Spring Boot and MySQL failure catalogue to know cold**

    | Symptom | Likely mechanism | Evidence |
    |---|---|---|
    | `Connection is not available, request timed out` | Hikari pool exhausted by long transactions or slow queries | Pool active/pending metrics, thread dump |
    | Latency grows with data size | Missing index or full scan, OFFSET pagination | Slow query log, `EXPLAIN` |
    | Spike in queries per request after a release | New lazy relation causing N+1 | SQL logs, query count per request |
    | Periodic latency spikes, rising memory | GC pressure, unbounded cache, leak | GC logs, heap dump |
    | Everything slow when one dependency is slow | No timeout, thread pool saturated | Thread dump: threads in socket read |
    | DB overload just after a cache flush | Cache stampede, no request coalescing | Cache hit ratio, DB QPS |
    | Errors multiply during a partial outage | Retry storm without backoff or jitter | Request rate per client |
    | Intermittent `Deadlock found` | Inconsistent lock order across transactions | `SHOW ENGINE INNODB STATUS` |

    **Tools to name:** Spring Boot Actuator and Micrometer metrics, Prometheus and Grafana, structured logs with trace
    ids, `jcmd` or `jstack` thread dumps, heap dumps, `EXPLAIN`, MySQL's slow query log and `performance_schema`.

    **Practise on SwitchPrep**

    Work through the production debugging and performance subjects. Then, once a week, pick one row from the
    catalogue above and tell the incident story out loud from first page to postmortem, in under eight minutes.
    """,
    walkthrough="""
    **Prompt:** "It's Tuesday evening. After this afternoon's deploy, checkout API p99 went from 300 ms to 4 s, and
    about 5% of requests return 503 at peak. You're on call. Go."

    > **Candidate:** First, scope. Is it only checkout, or every endpoint? All instances, or some? Did traffic change?
    >
    > **Interviewer:** Only the checkout endpoints. All six instances look the same. Traffic is a normal Tuesday peak.
    >
    > **Candidate:** All instances and normal traffic points away from a bad host or a load spike, and towards the deploy or a dependency. Saturation next: CPU, heap, Tomcat threads, DB pool, and what are the 503s actually saying?
    >
    > **Interviewer:** CPU is 30%. The heap looks normal. Tomcat busy threads are pinned at 200, the maximum. The logs show `HikariPool-1 - Connection is not available, request timed out after 30000ms`. DB CPU is moderate, about 40%.

    > **Candidate:** So the app threads are all busy waiting for DB connections, but the database itself isn't struggling. That pattern usually means connections are being *held* too long, not that queries are slow. Something is keeping a connection checked out while it does other work. Before I dig in, though, I'd mitigate, because we're losing checkouts. The deploy correlates in time, and rolling back is cheap and reversible, so I'd roll back now and watch p99 and pool pending threads. If the change sits behind a feature flag, switching the flag off is even faster.
    >
    > **Interviewer:** You roll back. p99 returns to 320 ms within five minutes.
    >
    > **Candidate:** Good. That confirms the deploy and buys us time. Now the root cause. What changed in checkout in that release?
    >
    > **Interviewer:** The diff adds a call to a new fraud-scoring service from `CheckoutService.placeOrder`.
    >
    > **Candidate:** Is `placeOrder` annotated `@Transactional`, and where is the call?
    >
    > **Interviewer:** Yes, and the call is in the middle of the method, after the order insert.
    >
    > **Candidate:** That's the mechanism. The transaction opens at the start of `placeOrder` and takes a pool connection. The fraud call is an HTTP request. If its p99 is, say, 2-3 seconds, each checkout holds a DB connection for that long while doing no DB work. With a pool of 10 per instance, at peak we run out of connections. Requests queue for 30 seconds, then time out, and the 503s follow. Tomcat threads fill up waiting, which is why they're pinned at 200. To confirm in staging, a thread dump would show many threads in a socket read inside the fraud client, each holding a connection, and the rest waiting in `HikariPool.getConnection`. I'd also check the fraud client's timeout. I'd bet it's the default, which can be very long or infinite.
    >
    > **Interviewer:** How do you fix it?
    >
    > **Candidate:** Three layers. **The fix:** move the fraud call *before* the transaction starts, or split the work into a short transaction to create the order as PENDING, the fraud call with no transaction open, and a second short transaction to confirm or reject. **Resilience:** a strict timeout on the fraud client (say 500 ms) and a circuit breaker with an explicit fallback. Whether we fail open or fail closed is a business decision I'd confirm with the risk team. **Guardrails:** an alert on Hikari pending threads and on connection acquisition time, which would have fired minutes before the 503s. A load test in the pipeline for checkout. And a code review checklist item: no remote calls inside `@Transactional`. Then a blameless postmortem with the timeline.
    >
    > **Interviewer:** Would you just increase the pool size?
    >
    > **Candidate:** Not as the fix. A bigger pool only means more connections idling during HTTP calls, and six instances times a bigger pool can exceed MySQL's `max_connections` and hurt every other service. It might be a stop-gap if a rollback were impossible, but it treats the symptom.

    **Moments that earned points:** scope first, which removed whole classes of causes. Saturation signals read
    correctly (the app waiting on the pool while the DB is calm means connections held, not slow queries). Rollback
    *before* root cause, with the reason it's safe. Specific evidence named for each hypothesis. The fix layered as
    code, resilience and guardrails. And a confident, reasoned "no" to the tempting pool-size answer.
    """,
    commonFailures=[
        "Naming a root cause before asking a single scoping question",
        "Debugging while users keep failing, instead of rolling back or switching a flag off first",
        "Never asking \"what changed?\"",
        "Restarting servers as the whole answer",
        "Reflexively increasing pool sizes, timeouts or instance counts",
        "Stopping when the graph goes green: no verification, alert, test or postmortem",
        "In hands-on rounds: editing code before reproducing the failure, or ignoring the stack trace",
    ],
    practice=[
        P("Production debugging (senior subject)", "/core/production-debugging"),
        P("Performance engineering (senior subject)", "/core/performance"),
        P("Observability and SLOs at scale", "/system-design/senior/observability-slos-at-scale"),
        P("Failure handling and resilience", "/system-design/senior/failure-handling-resilience"),
        P("Observability: logging, metrics, tracing", "/core/microservices?chapter=7"),
        P("EXPLAIN and query optimisation", "/core/sql?chapter=5"),
        P("JVM internals: memory and GC", "/core/java?chapter=13"),
        P("Distributed systems traps", "/traps?area=distributed-systems"),
    ],
    sources=[SRC_SRE_TROUBLE, SRC_SRE_MON, SRC_USE, SRC_STRIPE, SRC_HI_META, SRC_LEVELOP_GOOGLE],
)

ROUNDS_P2 = [MACHINE_CODING, CONCURRENCY, CODE_REVIEW, DEBUGGING]
