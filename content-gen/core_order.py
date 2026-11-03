"""
The core set of study material: what the 60-day plan schedules and what the site shows first.
Shared by build_plan.py (scheduling) and build_learn.py (learn-core.json, which tells the site what is core).
Everything not listed stays on the site as optional depth.
"""

# (subject id, chapters to schedule (1-based) or None for all[, max batches of core questions])
# Chapters are left out when another scheduled chapter or the core Q&A already teaches the same thing.
CORE_ORDER = [
    ("java", [1, 3, 4, 5, 8, 9, 10, 11, 12, 13]),        # strings, exceptions: the core Q&A covers them
    ("concurrency-practical", [1, 2, 3, 4, 5, 6, 7, 8]),
    ("spring-boot", [1, 2, 3, 5, 6, 7, 8, 9, 12]),      # testing is its own subject; profiles are one core question
    ("sql", [2, 3, 4, 5, 7, 8, 10]),                    # joins and normalization: covered by core Q&A
    ("microservices", [1, 2, 3, 4, 5, 6]),              # observability: production-debugging chapter 2
    ("production-debugging", [1, 2, 3, 4, 5, 6, 7, 8]),
    ("angular", [3, 4, 6, 7, 11]),        # on the resume: change detection, signals, DI, RxJS, performance
    ("performance", [1, 2, 6]),                         # EXPLAIN and N+1: SQL chapter 5 and Spring chapter 7
    ("testing-code-review", [1, 2, 3, 5, 6, 7]),
    ("behavioral", [1, 2, 3, 5]),                       # negotiation: the job switch guide
    ("ai-assisted-engineering", [1, 2, 3, 6]),
    ("security", [1, 3, 4, 5]),
    ("senior-leadership", [1, 4, 8]),
    ("javascript-typescript", [2, 5, 6]), # closures, event loop, promises
    # CS fundamentals: lower yield for senior backend loops beyond OAs: the few chapters that keep coming up, plus one
    # batch of the most-asked questions each
    ("cn", [3, 5], 1),                 # HTTP versions, what happens when you type a URL
    ("os", [1], 1),                    # processes vs threads
    ("oop-design-patterns", [], 1),       # the theory is covered by the LLD fundamentals in the design track
    ("dbms", [], 1),
    ("cloud-devops", [1, 3, 4, 6]),    # AWS map, Docker, Kubernetes essentials, CI/CD
]
CASES = ["url-shortener", "rate-limiter-design", "notification-system", "chat-whatsapp", "news-feed",
         "ecommerce-flipkart-checkout", "ticket-booking-bookmyshow", "payment-system-upi", "ride-hailing-uber",
         "food-delivery-swiggy", "search-autocomplete"]
LLD_FUND = ["how-to-approach-lld", "solid-principles", "design-patterns-creational", "design-patterns-structural",
            "design-patterns-behavioral", "concurrency-for-lld"]
LLD_PROB = ["parking-lot", "splitwise", "rate-limiter-lld", "snake-and-ladder", "bookmyshow-lld", "elevator-system",
            "pub-sub-message-queue", "in-memory-key-value-store", "cab-booking-lld"]
# Left out of the plan (still on the site): covered elsewhere or rarely asked at this level.
#   transactions-isolation: SQL and Spring cover it; search-elasticsearch, distributed-coordination: niche at SDE-2;
#   food-delivery-swiggy: repeats ride-hailing; cab-booking-lld: repeats parking-lot and ride-hailing;
#   collaborative-editor, metrics-monitoring-system, multi-region-disaster-recovery: rare in SDE-2 loops.
SD_SKIP = {"transactions-isolation", "search-elasticsearch", "distributed-coordination", "food-delivery-swiggy",
           "cab-booking-lld", "collaborative-editor", "metrics-monitoring-system", "multi-region-disaster-recovery"}
CASES = [x for x in CASES if x not in SD_SKIP]
LLD_PROB = [x for x in LLD_PROB if x not in SD_SKIP]
