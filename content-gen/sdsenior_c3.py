"""Senior SD chunk 3: payment reliability, distributed job scheduler, metrics monitoring system."""
from sdsenior_common import *

topics = []

# ---------------------------------------------------------------- 7
topics.append(T("payment-processing-reliability", "Payment Processing Reliability (PSP Orchestration)", 7, "case-study", "Advanced",
"A payment orchestrator in front of several PSPs that survives timeouts, unknown outcomes, PSP outages and duplicate callbacks, without double-charging, and proves it with a ledger and reconciliation.",
r'''
## 1. Requirements

The prompt sounds like "design payments for our checkout", but a senior interviewer cares about the **failure paths**: the PSP times out, the callback arrives twice, the user taps Pay again, a whole PSP goes down. Scope it as a **payment orchestrator** that routes between several PSPs (for example Razorpay, PayU and Stripe) for cards and UPI.

**Functional**
- Create a payment for an order and charge it through a chosen PSP. Return status, synchronously where possible, asynchronously otherwise.
- Handle PSP webhooks, refunds and status queries.
- Route by method, bank and PSP health, and fail over when a PSP degrades.
- Keep a double-entry ledger, and reconcile daily against PSP settlement reports.

**Non-functional**
- **Never double-charge, and never lose a successful charge** (customer debited but order not confirmed).
- 99.95% availability for payment initiation. Orchestrator overhead under 300 ms p99, excluding PSP time.
- 20M payments a day, with peaks of 3k TPS (10x on sale days). Fully auditable.

## 2. Estimates

- 20M a day is about 230 TPS on average, with 3k TPS at peak.
- PSP latency: p50 about 1.5 s, p99 over 10 s. UPI collect flows can take minutes, so they are async by nature.
- **Little's law** (in-flight = arrival rate × latency): 3k TPS × 3 s means about 9k concurrent PSP calls. Blocking 200-thread Tomcat pools won't cope. Use a non-blocking client (WebClient) or Java 21 virtual threads, with a **bulkhead per PSP**.
- Storage: about 10 rows per payment (intent, attempts, ledger lines, events), so 200M rows a day. Shard by `merchant_id` and archive to cold storage after the regulatory hot period.

## 3. API

```text
POST /v1/payments            Idempotency-Key: <uuid>
  {"orderId":"ord_91","amount":149900,"currency":"INR","method":"CARD","customerId":"c_7"}
  -> 201 {"paymentId":"pi_55","status":"PROCESSING|REQUIRES_ACTION|SUCCEEDED|FAILED",
          "nextAction":{"type":"REDIRECT_3DS","url":"..."}}
GET  /v1/payments/{id}                      (client polls / or SSE push)
POST /v1/payments/{id}/refunds   Idempotency-Key  {"amount":50000}
POST /internal/psp/{psp}/webhooks           (signature-verified, ack fast)
Kafka: payment.succeeded / payment.failed / refund.processed  (from outbox)
```

Amounts are integers in paise. Never use floats for money.

## 4. Data model (MySQL, sharded by merchant)

```sql
CREATE TABLE payment_intents (            -- one per order: the business object
  id VARCHAR(32) PRIMARY KEY, merchant_id BIGINT, order_id VARCHAR(64),
  amount BIGINT, currency CHAR(3),
  status ENUM('CREATED','PROCESSING','SUCCEEDED','FAILED','REFUNDED') NOT NULL,
  version INT NOT NULL,
  UNIQUE KEY uk_order (merchant_id, order_id)        -- no second intent for the same order
);
CREATE TABLE payment_attempts (           -- one per PSP call
  id VARCHAR(32) PRIMARY KEY,             -- also sent to the PSP as ITS idempotency key
  intent_id VARCHAR(32), psp VARCHAR(16), psp_ref VARCHAR(64),
  status ENUM('CREATED','SENT','UNKNOWN','SUCCEEDED','FAILED') NOT NULL,
  error_code VARCHAR(32), sent_at DATETIME(3), resolved_at DATETIME(3),
  next_check_at DATETIME(3),              -- status-poll schedule for UNKNOWN
  INDEX (status, next_check_at)
);
CREATE TABLE ledger_lines (               -- append-only double entry
  journal_id VARCHAR(32), account VARCHAR(64), direction ENUM('DR','CR'),
  amount BIGINT, created_at DATETIME(3),
  UNIQUE KEY (journal_id, account, direction)
);
-- plus idempotency_keys, outbox, psp_webhook_events(event_id PK), recon_breaks
```

## 5. High-level design

```text
 App/Web --> API Gateway --> [Payment Orchestrator]---MySQL (intents, attempts, ledger, outbox)
                                 |       ^
                    route        |       | webhook events (deduped)
                                 v       |
                       [PSP Router: health score per PSP x method x bank]
                          |             |              |
                   [Razorpay adapter] [PayU adapter] [Stripe adapter]   <- bulkhead + breaker each
                          |             |              |
                        PSPs  ------ webhooks ------> [Webhook Ingress] -> Kafka -> Orchestrator
 [Status Resolver]: polls PSP status API for UNKNOWN attempts with backoff
 [Outbox relay] -> Kafka -> Order svc, Notifications, Analytics
 [Recon jobs]  <- PSP settlement files (S3/SFTP) + bank statements -> recon_breaks -> ops UI
```

## 6. Deep dives on failure paths

### 6.1 The unknown outcome

The PSP call times out after 10 s. Did the charge happen? **You don't know.** Both obvious reactions are wrong. Treating it as failed lets the user pay again, which risks a double charge. Treating it as succeeded ships unpaid orders.

1. Mark the attempt `UNKNOWN` and keep the intent `PROCESSING`. Tell the client "processing" and show a status screen. Don't show a retry button.
2. Resolve it through three channels, whichever comes first: the PSP **webhook**; the **status resolver** polling the PSP's status API at 5 s, 15 s, 1 min, 5 min and 30 min; and finally **reconciliation**.
3. Allow a new attempt (possibly on another PSP) **only after** the previous one is confirmed `FAILED`. Never fail over while an attempt is unknown.
4. If a late success shows up for an intent that already succeeded through another attempt, the system detects two successful attempts and **auto-refunds** one, then alerts.

### 6.2 Idempotency at every hop

- **Client to us**: an `Idempotency-Key` per checkout click, plus `UNIQUE(merchant_id, order_id)` on intents. A double tap from two devices maps to the same intent.
- **Us to PSP**: the `attempt.id` is sent as the PSP's idempotency key or merchant reference. A retry after a connection reset reuses the same attempt ID, so the PSP dedupes it.
- **PSP to us**: webhooks are deduped by `event_id` (primary key insert), and state changes are conditional, so a duplicate or out-of-order callback is a no-op and a terminal state never goes backwards:

```sql
UPDATE payment_attempts SET status='SUCCEEDED', psp_ref=?, resolved_at=NOW(3)
 WHERE id=? AND status IN ('SENT','UNKNOWN');     -- 0 rows => already resolved
```

### 6.3 No DB transaction across the network

Following Airbnb's Orpheus pattern, split the work. **Transaction 1**: insert the attempt as `SENT` and commit. **Then** make the PSP call with no locks held. **Transaction 2**: apply the result, update the intent, write ledger lines and the outbox event atomically. A crash between the steps leaves a `SENT` attempt, which the resolver treats like `UNKNOWN`.

### 6.4 Retry rules

| Failure | Retry? |
|---|---|
| Connection refused / DNS failure (request never sent) | Yes, same PSP, same attempt ID, with backoff |
| Timeout after send | Status query first. Retry only if the PSP honours idempotency keys |
| 5xx from PSP | Same attempt ID with backoff, within the retry budget |
| Hard decline (insufficient funds, 4xx) | No. Mark FAILED and let the user pick another method |

Retries happen only in the adapter layer, never also at the gateway and in the client.

### 6.5 PSP degradation and routing

The router keeps a sliding-window success rate and latency per PSP × method × bank. When a PSP's breaker opens (error rate or slow-call rate), **new** payments route to the next PSP by preference and cost. In-flight unknowns stay with their original PSP. A bulkhead per PSP stops a slow Razorpay from consuming the threads PayU needs. During a sale, respect the TPS limits agreed with each PSP.

### 6.6 Ledger and reconciliation

On capture, write one journal: `DR psp_receivable 1499.00`, `CR merchant_payable 1470.00`, `CR fee_revenue 29.00`. The lines sum to zero, are never updated, and corrections are reversing journals. Every day, ingest the PSP settlement file and match on `psp_ref` and amount:

- PSP says success, we have no success: mark it succeeded and fulfil (or refund, per policy). This is the "customer charged, no order" case.
- We say success, the PSP doesn't: escalate and hold the merchant payout.
- Amount or fee mismatch: create a break for finance.

Run intraday recon too: any attempt still `UNKNOWN` after 15 minutes goes to an ops queue.

## 7. Observability

- **Payment success rate** per PSP × method × bank compared with the same hour last week. This is the primary business SLI, and a 10-point drop pages.
- Count and age of `UNKNOWN` attempts. Time-to-final-state p99.
- **Invariant monitors**: intents with more than one successful attempt (should be 0, pages immediately), ledger journals that don't sum to zero (0), and recon break count and value.
- PSP latency and errors per adapter, breaker state, outbox and webhook lag.
- Each `paymentId` carries the trace ID through adapter calls and webhooks, so support can see the full timeline.

## 8. Trade-offs

- **Automatic PSP failover** raises success rates but adds double-charge risk. Allowing it only after a confirmed failure keeps it safe.
- **Hand-rolled state machine vs a workflow engine** (Temporal/Cadence): an engine gives durable timers and retries for free, but adds infrastructure to operate.
- **Sync vs async API**: sync is simpler for clients, async is honest about UPI and 3DS realities. Support both: sync fast path, async status updates.
- **Build vs buy**: payment orchestrators exist as products (for example Juspay). Building pays off at large volume, when routing gains and PSP fees justify a team.
''',
[
 "Scope it as an orchestrator over several PSPs. The interview is about failure paths, not the happy path.",
 "A timeout is an unknown outcome. Mark the attempt UNKNOWN and resolve via webhook, status polling with backoff, then reconciliation.",
 "Never start a new attempt or fail over to another PSP until the previous attempt is confirmed failed. Auto-refund if two attempts succeed.",
 "Idempotency at every hop: client key plus a unique intent per order, the attempt ID as the PSP idempotency key, and webhook event ID dedup with conditional transitions.",
 "Keep network calls outside DB transactions (record intent, call, record outcome). A crash leaves SENT, which the resolver treats as unknown.",
 "Retry only transient failures, in one layer, reusing the attempt ID. Hard declines are final.",
 "An append-only double-entry ledger plus daily and intraday reconciliation catch whatever slips through.",
 "Monitor success rate per PSP/method/bank, UNKNOWN age, and invariants (double success, unbalanced journals) that page at zero tolerance."
],
[
 ("The PSP call times out after 10 seconds. What exactly do you do?",
  r'''I don't treat it as success or failure. The attempt moves to UNKNOWN, the intent stays PROCESSING, and the client sees a "confirming your payment" screen with no retry button. Resolution comes from whichever arrives first: the PSP webhook, my status resolver polling the PSP status API with backoff (5 s, 15 s, 1 min, 5 min), or reconciliation. Only when the PSP confirms failure do I allow a new attempt, possibly on another PSP. If it confirms success, the normal success path runs. Attempts unknown after 15 minutes go to an ops queue.'''),
 ("How do you prevent a double charge if the user taps Pay twice, or retries from a second device?",
  r'''Three layers. Each click carries an idempotency key, so the same request replays the stored response. Intents are unique per (merchant, order), so a second device lands on the same intent, and a new attempt is only allowed when no attempt is SENT or UNKNOWN. That check is a conditional update on the intent's status and version, so two concurrent requests can't both start attempts. Each attempt ID goes to the PSP as its idempotency key. As a safety net, a monitor flags any intent with two successful attempts and auto-refunds one.'''),
 ("Razorpay is degraded for 20 minutes during a sale. What happens?",
  r'''The router's sliding-window metrics show Razorpay's success rate dropping and latency rising, and its circuit breaker opens. New payments route to the next PSP for that method and bank, within the TPS limits we agreed with them. Razorpay's bulkhead keeps its slow calls from starving other adapters. Payments already in flight on Razorpay stay there as UNKNOWN until its webhooks or status API confirm. When half-open probes succeed, traffic gradually shifts back. Dashboards show success rate per PSP, and payments on-call gets a page because the overall success-rate SLI dropped.'''),
 ("How would you know money is going wrong, before customers tell you?",
  r'''Invariants plus reconciliation. Real-time monitors check that no intent has two successful attempts, every ledger journal sums to zero, UNKNOWN attempts are resolved within N minutes, and success rate per PSP and bank stays within baseline. Daily reconciliation matches our ledger against PSP settlement files and bank statements and records breaks: charged but no order, order but no charge, amount mismatches. Their count and rupee value are tracked and paged on. Intraday status sweeps catch problems before the daily file. Each check exists because some failure path can slip past idempotency.'''),
 ("The primary region fails in the middle of payments. What is lost and how do you recover?",
  r'''Payment data stays in India, so DR is a second Indian region with replicated MySQL. With semi-sync replication, committed attempts reach the replica, so after fencing and promotion the attempt table is intact. Attempts in SENT or UNKNOWN are resolved by the status resolver in the new region, which queries the PSPs, because the PSP is the source of truth for whether money moved. Clients retry with the same idempotency key and get the stored result. PSP webhooks follow DNS to the new region. Reconciliation the next day confirms nothing slipped through.'''),
 ("Why a double-entry ledger instead of just updating a balance column?",
  r'''A balance column only tells you the current number, not why it is what it is, and an UPDATE bug silently destroys history. A double-entry ledger records every movement as an immutable journal whose debits and credits sum to zero. Balances are derived, so you can rebuild them, audit them and reconcile them line by line against PSP and bank files. Corrections are reversing entries, which keeps the audit trail regulators expect. It also makes idempotency simple: a unique journal ID means replays can't post twice.''')
],
[AIRBNB_PAY, STRIPE_IDEM,
 ("Hello Interview - Design a Payment System like Stripe", "https://www.hellointerview.com/learn/system-design/problem-breakdowns/payment-system"),
 ("Square Engineering - Books: an immutable double-entry accounting database service", "https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/"),
 ("Uber Engineering - Payments Platform (Gulfstream)", "https://www.uber.com/blog/payments-platform/"),
 AWS_RETRY]))

# ---------------------------------------------------------------- 8
topics.append(T("distributed-job-scheduler", "Distributed Job Scheduler", 8, "case-study", "Advanced",
"Cron at scale: durable one-off and recurring jobs that start within seconds of schedule, run 'exactly-once-ish' through leases, fencing and idempotent handlers, with retries, priorities and tenant fairness.",
r'''
## 1. Requirements

**Functional**
- Schedule one-off jobs ("run at 2026-11-01T09:00 IST") and recurring jobs (cron with time zone).
- A job targets a handler: an HTTP callback, a Kafka topic or a registered worker type, plus a payload.
- Retries with a backoff policy, a maximum number of attempts, and a dead-letter state.
- Priorities (P0 billing over P2 report emails), plus pause, resume and cancel.
- Execution history and status for each job.

**Non-functional**
- **Start within 5 s** of the scheduled time for 99% of executions.
- Never miss an execution if a scheduler node dies. At-least-once execution, with duplicates minimised ("exactly-once-ish").
- 100M executions a day, with **spikes of 10k+/s at the top of each hour** (midnight is the worst).
- Multi-tenant: one tenant's 1M-job burst must not delay everyone else.

## 2. Estimates

- 100M a day is about 1.2k/s on average, but cron clusters on round times, so plan for **10-20k/s** peaks.
- An execution row is about 500 B, so 50 GB a day. Keep 30 days hot (1.5 TB) using daily partitions, and drop old partitions instead of running `DELETE`.
- 10M recurring definitions. Materialising the next 10 minutes of occurrences is a few million rows, which is easy.

## 3. API

```text
POST /v1/jobs   Idempotency-Key
 {"name":"invoice-run","schedule":{"type":"CRON","expr":"0 0 * * *","tz":"Asia/Kolkata"},
  "target":{"type":"HTTP","url":"https://billing/internal/run","timeoutSec":60},
  "payload":{...},"priority":"P0",
  "retry":{"maxAttempts":5,"backoff":"EXPONENTIAL","initialSec":10},
  "concurrency":"FORBID"}                  -> 201 {"jobId":"job_1"}
POST /v1/jobs/{id}:pause | :resume     DELETE /v1/jobs/{id}
GET  /v1/jobs/{id}/executions?status=FAILED
Worker protocol: claim -> heartbeat(executionId, leaseToken) -> complete/fail(executionId, leaseToken)
```

## 4. Data model

```sql
CREATE TABLE jobs (                         -- definitions
  id BIGINT PRIMARY KEY, tenant_id BIGINT, schedule_type ENUM('ONCE','CRON'),
  cron_expr VARCHAR(64), tz VARCHAR(40), target JSON, payload JSON,
  priority TINYINT, retry_policy JSON, concurrency ENUM('ALLOW','FORBID','REPLACE'),
  state ENUM('ACTIVE','PAUSED','DELETED'), next_fire_at DATETIME(3), INDEX (state, next_fire_at)
);
CREATE TABLE executions (                   -- instances, partitioned by day of scheduled_at
  id BIGINT, job_id BIGINT, tenant_id BIGINT, scheduled_at DATETIME(3), priority TINYINT,
  status ENUM('SCHEDULED','QUEUED','RUNNING','SUCCEEDED','FAILED','DEAD'),
  attempt INT, next_attempt_at DATETIME(3),
  lease_owner VARCHAR(64), lease_expires_at DATETIME(3), lease_token BIGINT,   -- fencing
  PRIMARY KEY (id, scheduled_at),
  UNIQUE KEY uk_occurrence (job_id, scheduled_at),      -- same occurrence can't be created twice
  INDEX idx_due (status, next_attempt_at)
);
```

`UNIQUE(job_id, scheduled_at)` is the key idempotency guard. If two planners race on the same cron occurrence, one insert fails harmlessly.

## 5. High-level design

```text
 Clients --> [Job API] --> MySQL: jobs, executions (source of truth)
                               ^            |
   [Planner] (every 30s): for jobs with next_fire_at < now+10min
      INSERT executions (idempotent), advance next_fire_at
                                            |
   [Dispatcher shards] (every 1s): due rows  FOR UPDATE SKIP LOCKED
      -> status QUEUED -> Kafka topics jobs.p0 / jobs.p1 / jobs.p2 (key = tenant)
                                            |
   [Worker pool]  consume (weighted: p0 > p1 > p2, per-tenant caps)
      claim lease (conditional UPDATE) -> run handler(idempotency key = executionId)
      -> heartbeat extends lease -> complete with lease_token check
   [Reaper] (every 10s): RUNNING with expired lease -> SCHEDULED (attempt+1, backoff)
   [Metrics/alerts]: schedule lag, queue depth, DEAD count, canary job
```

The **two-tier timing** design keeps durability and precision apart. The database holds everything for any future date. The planner materialises only the next few minutes, and dispatchers poll a small, hot index, so the 5 s precision target doesn't need scans over months of future jobs.

## 6. Deep dives

### 6.1 "Exactly-once-ish": leases, fencing and idempotent handlers

True exactly-once is impossible: a worker can finish the side effect and die before recording success. So aim for **at-least-once with rare duplicates, absorbed by idempotent handlers**.

```sql
-- claim: only one worker can move QUEUED -> RUNNING
UPDATE executions SET status='RUNNING', lease_owner=?, lease_token=lease_token+1,
       lease_expires_at = NOW(3) + INTERVAL 60 SECOND
 WHERE id=? AND status='QUEUED';               -- 0 rows -> someone else got it
-- complete: rejected if the lease was taken over (stale worker = zombie)
UPDATE executions SET status='SUCCEEDED' WHERE id=? AND lease_token=? AND status='RUNNING';
```

- Workers **heartbeat** every 15 s to extend the lease. Dropbox's ATF has executors terminate themselves after three consecutive failed heartbeats, and sizes the heartbeat timeout above that. A paused or partitioned worker stops before its job is handed to someone else.
- The `lease_token` is a **fencing token**. Pass it to downstream systems where possible, so writes from a zombie are rejected.
- Every handler receives `executionId` as an idempotency key (for example, the billing service keeps `UNIQUE(execution_id)` on invoice runs).

### 6.2 Scaling the dispatcher

`SELECT ... WHERE status='SCHEDULED' AND next_attempt_at <= NOW(3) + INTERVAL 2 SECOND ORDER BY priority, next_attempt_at LIMIT 500 FOR UPDATE SKIP LOCKED` (MySQL 8) lets several dispatchers pull from the same table without blocking each other. Beyond one database, shard executions by `hash(job_id) % N`. Each dispatcher owns a set of shards through a lease in etcd or ZooKeeper, or a `shard_owners` table with expiring leases. A Redis sorted set (score = fire time) is a faster near-term queue, but treat it as a cache that can be rebuilt from MySQL.

### 6.3 The midnight thundering herd

- Ask producers for **tolerance windows** ("any time between 00:00 and 00:15") and spread those jobs with deterministic per-job jitter.
- Pre-materialise midnight's executions an hour ahead.
- Apply **per-tenant concurrency caps** and weighted fair consumption, so one tenant's 1M jobs queue behind its own quota.
- Rate-limit **per target** so the scheduler doesn't DDoS the billing service it calls.

### 6.4 Retries and dead letters

Failures are classified: timeouts and 5xx are retryable with exponential backoff plus jitter, while 4xx and validation errors fail immediately. After `maxAttempts` the execution becomes `DEAD`, and the owning team gets an alert with a replay button. A per-execution timeout stops a poison job from holding a worker forever.

### 6.5 Cron semantics people forget

- **Time zones and DST**: compute fire times in the job's zone. A 02:30 job doesn't exist on a spring-forward day in Europe and runs twice on the fall-back day. IST has no DST, but global tenants do.
- **Misfire policy** after an outage: fire once now (the default), fire every missed run, or skip.
- **Overlap policy** (like Kubernetes CronJob `concurrencyPolicy`): `FORBID` skips a new run while the previous one is still running, and `REPLACE` cancels the old one.

## 7. Observability

- **Schedule lag** (`started_at - scheduled_at`) p50 and p99 by priority. This is the core SLI (99% under 5 s), with burn-rate alerts on it.
- Queue depth and age per priority and per tenant, and dispatcher poll duration.
- Expired leases per minute (worker crashes or GC pauses), retry rate and DEAD count per job type.
- **Canary job** every minute that writes a heartbeat row. If it's missing for 3 minutes, page. This catches "the planner silently stopped".
- Duplicate detection: count completions rejected because of a stale lease token.

## 8. Trade-offs

- **DB polling vs Redis ZSET vs Kafka**: MySQL is durable and queryable but limited by polling cost. Redis is fast but needs rebuild logic. Kafka has no native per-message delay.
- **Quartz cluster mode or Spring `@Scheduled` + ShedLock** work for hundreds of jobs inside one app. They aren't a multi-tenant platform at 10k/s.
- **Managed or workflow engines** (AWS EventBridge Scheduler, Temporal schedules) remove most of this work, at the price of lock-in or new infrastructure.
- **At-least-once vs at-most-once**: offer both per job. A "send marketing push" job may prefer skipping to duplicating.
''',
[
 "Two-tier timing: MySQL stores all future executions durably, and a planner materialises the next few minutes so dispatchers poll a small, hot index.",
 "UNIQUE(job_id, scheduled_at) makes occurrence creation idempotent even when planners race.",
 "Exactly-once is impossible. Use at-least-once with leases, heartbeats, fencing tokens and handlers keyed by execution ID.",
 "Claim and complete with conditional UPDATEs (status and lease_token checks), so zombie workers can't overwrite results.",
 "FOR UPDATE SKIP LOCKED lets several dispatchers share a table. Shard by job ID, with shard ownership held as leases.",
 "Tame the top-of-hour spike with tolerance windows plus jitter, pre-materialisation, per-tenant caps and per-target rate limits.",
 "Cron correctness: time zones and DST, misfire policy, and overlap policy (forbid or replace).",
 "Schedule lag is the SLI. Add a canary job heartbeat, plus expired-lease and DEAD-count alerts."
],
[
 ("How do you guarantee a job doesn't run twice?",
  r'''I can't guarantee it absolutely: a worker might finish the side effect and crash before recording success, and then the job reruns. What I guarantee is that two workers never hold a valid lease at the same time, and that duplicates are harmless. Claims are conditional updates from QUEUED to RUNNING, completion checks the lease token, and workers that miss heartbeats stop themselves before the lease expires. Each handler gets the execution ID as an idempotency key, so a rerun of the same execution is a no-op downstream. That's "exactly-once-ish".'''),
 ("A worker dies in the middle of a job. Walk me through recovery.",
  r'''The worker stops heartbeating, so its lease isn't extended. When `lease_expires_at` passes, the reaper conditionally moves the execution from RUNNING back to SCHEDULED, increments the attempt, and sets `next_attempt_at` with backoff. A dispatcher re-queues it, and a new worker claims it with a fresh lease token. If the old worker was only paused (a GC pause or network partition) and wakes up, its completion call carries the old token and is rejected. Because the handler is idempotent on execution ID, partial work from the first run doesn't double-apply.'''),
 ("Do you miss jobs if the scheduler or the database goes down?",
  r'''Scheduler nodes are stateless: planner and dispatcher shards are owned via expiring leases, so if one dies another takes its shards within seconds. Due executions are still in MySQL and get picked up late, not lost. If the primary database fails, scheduling pauses until failover completes (Multi-AZ, under a minute). When it's back, due rows show past timestamps and run according to each job's misfire policy: fire once now by default. The schedule-lag alert and the canary job make the gap visible.'''),
 ("A tenant schedules a million jobs for midnight. How does the system cope?",
  r'''First, their executions are pre-materialised well before midnight, so creating them doesn't compete with the spike. Second, dispatch respects per-tenant concurrency caps and weighted fair consumption, so their million jobs drain at their quota while other tenants' P0 jobs keep their schedule lag. Third, if the jobs declared a tolerance window, I spread them with deterministic jitter. Fourth, per-target rate limits protect the service they call. I'd also push back on the API design: a million identical jobs is often better as one batch job that fans out internally.'''),
 ("How do you know the scheduler is broken or running late?",
  r'''The core SLI is schedule lag, actual start minus scheduled time, measured per priority, with burn-rate alerts against "99% start within 5 s". Silent failures are the dangerous ones, such as the planner stopping, so a canary job runs every minute and writes a heartbeat, and its absence for 3 minutes pages. I also watch queue depth and age per priority, expired leases (crashing workers), stale-token rejections (duplicates), retry rate and DEAD counts per job type, and dispatcher poll latency. Owners get alerts for their own dead jobs.'''),
 ("Why not just use Spring @Scheduled or Quartz?",
  r'''For a single application with a few dozen jobs, `@Scheduled` plus ShedLock (so only one instance runs each job), or Quartz in JDBC cluster mode, is the right answer, with no new platform. They fall short as a shared, multi-tenant service: Quartz's cluster mode relies on database row locks that limit throughput, and neither gives you tenant isolation, priorities across teams, per-target rate limits, execution history APIs or 10k/s top-of-hour bursts. I'd also consider EventBridge Scheduler or Temporal before building, and build only if scale, cost or control justify a team.''')
],
[("Dropbox Tech - Asynchronous task scheduling at Dropbox (ATF)", "https://dropbox.tech/infrastructure/asynchronous-task-scheduling-at-dropbox"),
 ("Hello Interview - Design a Distributed Job Scheduler", "https://www.hellointerview.com/learn/system-design/problem-breakdowns/job-scheduler"),
 ("Martin Kleppmann - How to do distributed locking (fencing tokens)", "https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html"),
 ("Kubernetes Docs - CronJob (concurrency policy, missed schedules)", "https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/"),
 ("MySQL 8.0 Reference - Locking Read Concurrency with NOWAIT and SKIP LOCKED", "https://dev.mysql.com/doc/refman/8.0/en/innodb-locking-reads.html")]))

# ---------------------------------------------------------------- 9
topics.append(T("metrics-monitoring-system", "Metrics Monitoring & Alerting System", 9, "case-study", "Advanced",
"A Prometheus/Datadog-style platform: high-throughput ingestion, a compressed time-series store, downsampling and retention, fast PromQL-style queries, and alerting that stays reliable when everything else is on fire.",
r'''
## 1. Requirements

**Functional**
- Ingest metrics (counters, gauges, histograms) with labels from agents on hosts and pods.
- Query by metric and label filters with aggregations over time ranges, for dashboards.
- Alert rules ("p99 latency > 500 ms for 5 min"), with notifications to PagerDuty, Slack and email, plus silencing and grouping.
- Retention: raw data for 15 days, 5-minute rollups for 90 days, 1-hour rollups for 2 years.

**Non-functional**
- 500k hosts × 200 series each = **100M active series**. A 10 s interval gives **10M samples/s**.
- Alerts fire within about 1 minute of the event. Last-hour queries return in under 1 s, 30-day queries in under 5 s.
- Ingestion stays highly available. Dashboards may be eventually consistent, but **alert evaluation must be reliable**.
- Multi-tenant, with per-team limits.

## 2. Estimates

- 10M samples/s × 86,400 s = **864B samples a day**.
- Raw (8-byte timestamp + 8-byte float) that's 16 B × 864B ≈ **13.8 TB a day**. Gorilla-style compression averages about 1.37 B per point, and Prometheus quotes 1-2 B per sample, so about **1.2-1.7 TB a day**.
- 15 days raw ≈ 25 TB, × 3 replicas in ingesters/WAL ≈ 75 TB. Long-term blocks go to object storage (S3) with lifecycle tiers.
- Series index: 100M series × about 500 B of labels ≈ 50 GB, which must be mostly in memory and cache for fast label lookups.

## 3. API

```text
POST /api/v1/write            (Prometheus remote-write: snappy-compressed protobuf batches)
     headers: X-Scope-OrgID: <tenant>
GET  /api/v1/query?query=sum(rate(http_requests_total{svc="checkout",code=~"5.."}[5m]))&time=...
GET  /api/v1/query_range?query=...&start=...&end=...&step=60s
GET  /api/v1/series?match[]=...       (label discovery for dashboards)
PUT  /api/v1/rules/{namespace}        (alert + recording rules, YAML)
```

## 4. Data model

- **Series identity** = metric name + sorted label set, for example `http_requests_total{svc="checkout",method="POST",code="200",pod="p-17"}`, hashed to a `series_id`.
- **Sample** = `(series_id, timestamp_ms, float64)`.
- **Inverted index**: `label=value` maps to a sorted posting list of series IDs. A query intersects the posting lists (`svc=checkout ∩ code=~5..`).
- **Chunks**: for each series, about 120 samples or 2 hours compressed together, with **delta-of-delta** timestamps (regular intervals cost about 1 bit) and **XOR-encoded** floats (slowly changing values cost a few bits). Two-hour **blocks** hold chunks plus an index, and are immutable once flushed.

Why not MySQL or a generic wide-row table? 10M row inserts a second, a B+tree index entry per sample, and range scans across billions of rows. A TSDB is append-only, partitioned by time, and compresses each series' values together, which turns 16 bytes into about 1-2.

## 5. High-level design

```text
 Agents (OTel Collector / Prometheus agent, batch + retry + local buffer)
      |  remote-write (per-tenant auth)
 [Distributors] -- validate, rate/series limits per tenant, hash(tenant, series) --+
      |                                                                          |
      | replicate x3 via consistent-hash ring (or via Kafka partitions for buffering)
      v
 [Ingesters]  in-memory head block + WAL on disk; cut 2h blocks --> [Object store S3]
      ^                                                                 |
      | recent data (last ~2-4h)                       [Compactor]: merge blocks, dedupe replicas,
      |                                                 build 5m/1h rollups, apply retention
 [Queriers] <---- old data ---- [Store gateways] (block index + chunk cache)
      ^
 [Query frontend]: split long ranges by day, results cache (memcached), per-tenant fairness
      ^
  Dashboards (Grafana)              [Ruler] evaluates alert/recording rules every 15-30s
                                       |  (own query capacity, reads ingesters directly)
                                    [Alertmanager cluster]: dedupe, group, silence, route
                                       -> PagerDuty / Slack / email
```

This follows the shape of horizontally scaled Prometheus systems such as Cortex, Grafana Mimir and Thanos.

## 6. Deep dives

### 6.1 Write path and durability

Agents batch samples (every few seconds), compress them and retry with backoff, and buffer locally for a few minutes if the backend is unreachable. Distributors are stateless. They enforce tenant limits and replicate each series to 3 ingesters chosen by consistent hashing, acknowledging after a **quorum of 2**. Ingesters append to a WAL before acknowledging, so a crash replays the WAL. Putting **Kafka** between distributors and ingesters is a valid alternative: it absorbs spikes, lets you replay, and decouples deploys, at the cost of extra latency and infrastructure. Mention both options.

### 6.2 Cardinality: the number-one operational risk

One deploy that adds `user_id` as a label can create millions of new series, blow up ingester memory and slow every query. Defences:

- Per-tenant active-series limits and per-metric label-value limits. Reject new series beyond the limit with a clear error, but keep accepting existing series.
- Per-tenant cardinality dashboards (top metrics and labels by series count) and relabel rules to drop bad labels at the agent.
- Since histograms multiply series by the bucket count, prefer native or exponential histograms where supported.

### 6.3 Downsampling and retention

The compactor merges 2-hour blocks into larger ones, removes replica duplicates, and writes rollups at 5-minute and 1-hour resolution. Each rollup stores **min, max, sum and count**, so averages stay correct (sum/count). Never average percentiles: keep histogram bucket counts summed and compute quantiles at query time. The query layer picks a resolution from the range and step: a 1-year panel reads 1-hour rollups (8,760 points per series instead of 3.1M). Retention is cheap because it **deletes whole blocks**, another benefit of partitioning by time.

### 6.4 Fast queries

The query frontend splits a 30-day range into daily sub-queries, runs them in parallel, and caches each completed day. Past days never change, so the cache hit rate is high. Queriers limit series and samples scanned per query and return a clear error instead of running out of memory. Popular dashboard panels become **recording rules** that precompute expensive aggregations (`job:http_errors:rate5m`).

### 6.5 Alerting that survives a bad day

- The ruler evaluates rules against ingesters (the freshest data) every 15-30 s, using **its own query capacity**, so a dashboard stampede during an incident can't starve alert evaluation. When overloaded, shed dashboard queries before rule evaluation or ingestion.
- `for: 5m` pending states reduce flapping. `absent()` rules catch metrics that disappear, which a threshold alert would miss.
- Run two rulers per rule group for HA, and let the Alertmanager cluster deduplicate notifications (its replicas gossip notification state), group related alerts and apply silences.
- **Late data**: agents buffer during network blips, so accept out-of-order samples within a window (for example 10 minutes), and alert on ingestion lag itself so nobody trusts stale "all green" data.

## 7. Monitoring the monitoring system

- Ingestion: samples/s accepted vs rejected per tenant and reason, distributor-to-ingester latency, WAL replay time.
- Active series per tenant against its limit. Query latency and timeouts by tenant.
- Ruler: evaluation duration vs interval and **missed evaluations**. Alertmanager: notification failures per integration.
- A **dead man's switch**: an always-firing watchdog alert routed to an external service that pages if the heartbeat stops. Run meta-monitoring in a separate region or account.

## 8. Trade-offs

- **Pull vs push**: pull (Prometheus scraping) gives a free "is the target up" signal and server-side rate control. Push suits short-lived jobs, serverless and agents behind NAT. Large platforms often use agents that scrape locally and push remotely.
- **Raw precision vs cost**: longer raw retention makes investigations easier and storage pricier. Rollups lose spikes unless min and max are kept.
- **Kafka in the write path**: more durability and replay, more latency and cost.
- **Build vs buy**: Datadog-style SaaS prices per host and per custom metric, and cardinality makes the bill grow fast. Self-hosted Mimir or Thanos needs a platform team. At 500k hosts, self-hosting usually wins.
''',
[
 "Scale target: 100M active series at a 10 s interval means 10M samples/s, about 864B samples a day.",
 "A TSDB beats row stores: append-only, time-partitioned blocks, and per-series chunks with delta-of-delta timestamps and XOR floats (about 1.37 bytes per point in Gorilla).",
 "Write path: agents batch and buffer, stateless distributors enforce tenant limits, ingesters replicate x3 with quorum writes and a WAL, and blocks flush to S3.",
 "An inverted index of label to posting lists drives queries. Cardinality is the number-one risk, so enforce per-tenant series and label limits.",
 "The compactor builds 5m/1h rollups storing min/max/sum/count. Never average percentiles. Retention deletes whole blocks.",
 "The query frontend splits long ranges by day and caches past days. Recording rules precompute hot dashboard aggregations.",
 "Alert evaluation gets isolated capacity and priority over dashboards, HA rulers plus Alertmanager dedup, absent() rules, and ingestion-lag alerts.",
 "Monitor the monitor: rejected samples, missed rule evaluations, and an external dead man's switch."
],
[
 ("Why not store metrics in MySQL or as plain Cassandra rows?",
  r'''At 10M samples a second, a row per sample means 10M inserts a second with index maintenance on each, and range queries scanning billions of rows. Rows also store timestamp and value uncompressed: 16+ bytes plus row overhead. A time-series store keeps each series' samples together in compressed chunks, with delta-of-delta timestamps and XOR-encoded values, bringing it to roughly 1-2 bytes per sample. It's append-only, partitioned into time blocks so retention is just deleting blocks, and it uses an inverted label index for selection. The access pattern decides the storage engine.'''),
 ("Push or pull for collecting metrics?",
  r'''Pull, where the server scrapes targets, gives an automatic "up" signal and lets the server control load, and it's simple to debug: you can curl `/actuator/prometheus`. It struggles with short-lived jobs, serverless functions and targets behind NAT or firewalls. Push handles those, but the backend must defend itself with per-tenant rate limits. At scale I'd use a hybrid: an agent on each node or cluster scrapes local targets (keeping pull semantics) and pushes batches with remote-write to the central platform, with local buffering during outages.'''),
 ("One team's deploy suddenly adds 20 million new series. What happens and how do you protect the platform?",
  r'''Without limits, ingester memory climbs, index lookups slow down, and every tenant's queries and alerts degrade. That's a noisy-neighbour outage. Protection is layered: distributors enforce a per-tenant active-series limit and per-metric label limits, rejecting only new series beyond the cap while existing series keep flowing. The team gets a clear error and a cardinality dashboard showing which metric and label exploded. Agents can apply relabel rules to drop the offending label. Afterwards, add a CI lint for unbounded labels and alert tenants as they approach their limit.'''),
 ("How do alerts stay reliable when ingestion lags or the system is overloaded?",
  r'''Isolate and prioritise them. The ruler has dedicated query capacity against ingesters, and overload shedding drops dashboard queries first, then rule evaluation, with ingestion last. Two ruler replicas evaluate each group, and the Alertmanager cluster deduplicates, so one failure doesn't silence alerts. Lag is a failure mode in its own right: I alert on ingestion delay and missed rule evaluations, and use `absent()` rules so missing data doesn't look healthy. An external dead man's switch pages if the whole alerting path stops.'''),
 ("How do you serve a dashboard showing one year of data quickly?",
  r'''Don't read raw samples. The compactor has precomputed 1-hour rollups (min, max, sum, count per series), so a year is 8,760 points per series instead of about 3 million at 10 s resolution. The query layer picks the resolution from the requested step. The frontend splits the range into day or week shards, runs them in parallel across queriers, and caches finished shards, since past data is immutable. Expensive panels use recording rules. Percentiles come from summed histogram buckets, never from averaging stored p99s.'''),
 ("What if the region running the monitoring platform goes down? How would you even know?",
  r'''You would know through meta-monitoring that runs outside that region: a watchdog alert that is always firing and must reach an external heartbeat service every minute, plus synthetic checks from another region. For resilience, agents buffer locally for several minutes and can fail over remote-write to a standby region. Long-term blocks in S3 can be replicated across regions. The critical piece is alerting, so a minimal ruler and Alertmanager in a second region, evaluating the most important SLO alerts, keeps paging working even if dashboards are offline.''')
],
[("Facebook - Gorilla: A Fast, Scalable, In-Memory Time Series Database (VLDB 2015)", "https://www.vldb.org/pvldb/vol8/p1816-teller.pdf"),
 ("Prometheus Docs - Storage", "https://prometheus.io/docs/prometheus/latest/storage/"),
 ("Hello Interview - Design a Metrics Monitoring Platform like Datadog", "https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring"),
 ("Grafana Mimir - Architecture", "https://grafana.com/docs/mimir/latest/references/architecture/"),
 SRE_ALERT_SLO]))

if __name__ == "__main__":
    report(topics)
