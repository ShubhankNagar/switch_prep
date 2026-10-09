# Interview research notes (2026-10, for the senior 2027 upgrade)

Sources: techinterview.org "What actually changed in tech interviews in 2026"; interviewdb.com "Senior software interviews beyond LeetCode 2026";
prachub.com "Backend engineer interview guide 2026"; devrimozcay "The senior backend interview in 2026 (47 loops)";
customcareer.miami.edu "Google's AI-assisted coding interview (2026)"; prepfully "Software engineer interview rubric 2026".

- Coding rounds still exist (often AI-off, "explain as you go"; interviewers interrupt to check reasoning is yours), but weigh less
  for seniors (~17% vs ~45% in 2020) and questions are easier/medium. Big tech keeps standardized AI-off algorithm loops.
- NEW: AI-assisted coding rounds (Google, Meta and AI-native startups): you get an AI tool; graded on how you decompose,
  prompt, verify, test and catch AI mistakes, not on typing speed.
- NEW/GROWING: debug-this-code, code review (rank findings by production risk, correctness before style), practical coding
  (build a component with changing requirements + tests: task scheduler with pause/retry/cancel, per-user + global rate
  limiter, TTL cache with capacity, idempotent webhook handler, booking without double booking, small rules engine).
- Concurrency round: race conditions, CAS / conditional DB update ("UPDATE ... WHERE status='QUEUED'"), idempotency, ordering,
  two workers claiming the same task. Strong answers name the exact race, the broken invariant, the prevention and the test.
- System design is the dominant senior signal (~30%): production-flavoured prompts (payment failure handling, notifications
  during regional outage, real-time personalization), failure paths, observability, cost. Appears even in mid-level loops.
- Deep technical round on YOUR resume stack (~25%): 45-60 min probing e.g. Spring Boot internals, MySQL/InnoDB, Angular change
  detection. Can't be bluffed.
- Execution / operations round: production debugging method: confirm symptom -> latency/traffic/errors/saturation -> correlate
  recent deploy/config -> split healthy vs unhealthy -> mitigate (rollback, shed load, feature flag) -> verify -> add guardrail.
  Scenarios: regression after deploy, one bad shard/host, cache-driven DB overload, cold cache after incident.
- AI system design (when relevant): RAG, permissions, stale docs, evals, guardrails, cost/latency, fallbacks.
- Behavioral is structured with follow-up probes: ownership, ambiguity, disagreement, incidents, mentoring, changed decisions.
  Stories need stakes, specific actions, measured outcomes. Communication affects level/offer size.
- India: Flipkart/PhonePe/Swiggy/Razorpay/Uber/Atlassian/CRED keep machine-coding (LLD) rounds; Amazon keeps LP-heavy loops;
  Walmart/Goldman/JPMC are Java-heavy (collections, concurrency, Spring, JPA).
- Suggested senior prep split: ~25% coding fluency, 20% practical coding + tests, 20% LLD + concurrency, 20% system design
  (incl. AI), 15% project deep dives, code review, behavioral.
