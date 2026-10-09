"""Subject 19: Senior Engineer Skills: Ownership, Design Docs & Leadership (prefix lead-)."""
from senior2_common import build, report, B, I, A

NOTES = []

NOTES.append(("lead-mid-to-senior", "What Changes from Mid-Level to Senior (SDE-2 and Beyond)", r"""
Senior interviews don't mainly test harder algorithms. They test whether you already **behave like a senior engineer within your scope**: you take a fuzzy problem, make sensible trade-offs, deliver it with others, and leave the team better. Every round (system design, project deep dive, behavioral, even code review) is looking for that evidence.

## The shift, dimension by dimension

| Dimension | Mid-level (doing the work well) | Senior (owning the outcome) |
|---|---|---|
| **Scope** | Features and tickets inside one service | A project or system end to end, often spanning services or teams |
| **Ambiguity** | Receives defined tasks | Turns a vague problem ("checkout is flaky") into a plan with milestones |
| **Technical judgement** | Picks a working solution | Compares options, names trade-offs, chooses for the context, writes it down |
| **Ownership** | Code merged = done | Done = in production, measured, monitored, documented, on-call ready |
| **Influence** | Own code and reviews | Shapes team decisions, design reviews, standards; aligns with PMs and other teams |
| **Multiplying others** | Helps when asked | Mentors, unblocks, reviews thoughtfully, writes docs that scale knowledge |
| **Communication** | Status in stand-up | Proactive written updates, risks raised early, explains tech in business terms |
| **Business sense** | Knows the feature | Knows why it matters: revenue, cost, users, risk |

A useful test from Amazon's senior expectations (paraphrased): the team is stronger because you're there, but doesn't depend on you being there. Heroics that make you a single point of failure are not seniority.

## How interviews probe it

- **System design**: do you ask about requirements, scale and failure before drawing boxes? Do you discuss trade-offs, observability, rollout and cost?
- **Project deep dive**: can you explain *why* the system looks the way it does, what alternatives existed, what failed, and what *you* specifically did?
- **Behavioral with follow-ups**: "What would you do differently?" "How did you measure it?" "Who disagreed?" Vague "we did X" stories collapse under two follow-up questions.
- **Code review / debugging rounds**: do you rank issues by production risk and think about operability, not just style?

The 2026 loops summarised in this site's research note weigh system design and resume deep dives heavily for seniors, and communication quality directly affects level and offer.

## The service-company translation problem

Developers from service companies often undersell themselves because the client "owned" the roadmap. Reframe honestly:

- Instead of "I worked on the payments module", say "I owned the refund flow for [Client]'s payments platform: designed the idempotency approach, wrote the migration, and led the rollout to [N] merchants."
- Pick moments where you **chose** something: a library, a schema, a retry policy, pushing back on a deadline, proposing a fix nobody asked for.
- Quantify: latency, error rates, hours saved, incidents avoided, cost, adoption. If you don't have exact numbers, give honest approximations and say how you'd measure.
- Show **ownership after release**: dashboards you added, alerts, runbooks, the 2 a.m. incident you handled.

## Behaviours to start practising now (they become interview stories)

1. Write a one-page design note before your next non-trivial change and get it reviewed.
2. Volunteer for the incident follow-up and drive the action items to closure.
3. Mentor one junior deliberately: pairing sessions, reviewed PRs, a learning plan.
4. Add one measurable improvement per quarter: a slow query fixed, a flaky test suite stabilised, a deploy step automated.
5. Send a short written status update weekly on your current project, with risks.
6. In reviews, comment on design and operability, not only formatting.

## Level calibration for 2027

At Indian product companies, SDE-2 roles typically ask for roughly 2-5 years of experience, while "Senior" titles usually expect more. With about three years by 2027, the realistic target is a **strong SDE-2** who demonstrates senior behaviours within a well-scoped area. Interviewers will level you on evidence: deep ownership of one system beats shallow exposure to ten.

Go deeper: Will Larson's StaffEng guides ("Work on what matters", "Manage technical quality") describe the next stage, and Gergely Orosz's writing on senior expectations at Big Tech and scaleups is a good calibration for what product companies mean by "senior".
"""))

NOTES.append(("lead-design-docs", "Writing Design Docs and RFCs (Template + Worked Example)", r"""
A design doc is how a senior engineer **thinks in public**: it surfaces trade-offs while change is cheap, builds agreement, and leaves a record of *why*. Google's design-doc culture describes the core sections as context and scope, goals and non-goals, the design, alternatives considered, and cross-cutting concerns. The most valuable part is usually the **alternatives**, because it shows the decision was made, not defaulted into.

## When to write one

Write one when the change is hard to reverse, touches several services or teams, changes a data model or API contract, carries real risk (money, data loss, security), or when people disagree. Skip it, or write a half-page note, when the solution is obvious and easily reversible. Small changes get a 1-3 page "mini doc"; big projects might reach 10+ pages, and beyond that the problem should be split.

## A template you can reuse

```text
Title / Author / Reviewers / Status (Draft -> In review -> Approved -> Implemented) / Date

1. Context        What exists today, with numbers. Why now?
2. Problem        The specific pain, who feels it, evidence (incidents, metrics, tickets).
3. Goals          Measurable outcomes.          Non-goals: tempting things we won't do.
4. Proposal       Overview diagram, components, data model, APIs, key flows, failure handling.
5. Alternatives   2-3 real options with pros/cons and why not chosen (incl. "do nothing").
6. Cross-cutting  Security & privacy, observability, performance & cost, operations/on-call.
7. Rollout        Migration plan, feature flags, backward compatibility, rollback plan.
8. Risks & open questions   What could go wrong; what we still need to decide.
9. Milestones     Slices with rough estimates and owners.
```

## Worked example (condensed)

**Title:** Make order-confirmation notifications asynchronous and reliable

**1. Context.** `order-service` (Spring Boot, MySQL) calls `notification-service` synchronously over REST inside the checkout transaction. Checkout p99 is [~1.8 s]; notification calls account for [~600 ms] of it.

**2. Problem.** When `notification-service` or the SMS provider is slow, checkout slows or times out. In the last quarter, [3] incidents in which [~2%] of checkouts failed traced back to notification timeouts. Retries sometimes sent duplicate SMS.

**3. Goals.** Remove notifications from the checkout critical path; no lost notifications; no duplicate sends for the same order event; checkout p99 below [1.2 s]. **Non-goals:** redesigning notification templates; supporting new channels.

**4. Proposal.**
```text
checkout tx: INSERT order + INSERT outbox_event (same MySQL transaction)
outbox relay (scheduled poller or Debezium CDC) --> Kafka topic order-events (key = orderId)
notification-service consumer --> dedupe table (event_id unique) --> send via provider
failures: retry with backoff (3x) --> DLQ topic --> alert + replay tool
```
Consumers are idempotent via a unique `event_id`; ordering per order is preserved by keying on `orderId`.

**5. Alternatives.**
| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Keep sync, add timeout + circuit breaker | Small change | Still couples checkout to notifications; drops messages when open | Short-term mitigation only |
| Publish to Kafka after commit (no outbox) | Simple | Event lost if the app crashes between commit and publish | Rejected |
| `@Async` in-process | Very simple | Lost on restart; no retry visibility | Rejected |
| **Outbox + Kafka** | Reliable, decoupled, replayable | New table, relay to operate | **Chosen** |

**6. Cross-cutting.** Outbox payload holds IDs only (no PII); consumer lag and DLQ size alerts; outbox rows purged after 7 days; added cost: one topic, small relay.

**7. Rollout.** Phase 1: write outbox rows behind flag `notify.async` while still calling sync. Phase 2: enable the consumer for 10% of orders, compare sends. Phase 3: 100% and remove the sync call. Rollback: flip the flag back.

**8. Risks.** Relay lag during sale peaks (mitigation: scale relay, alert on lag over [60 s]); duplicate sends if the dedupe insert and provider call aren't ordered correctly (insert first, mark sent after).

**9. Milestones.** Outbox + relay (4 days), consumer + dedupe (3), dashboards and alerts (1), staged rollout (1 week elapsed).

## Tips that make docs actually get read

- Put the **decision and the ask** at the top ("Proposing X; need approval from payments and SRE by Friday").
- Use diagrams and tables; write for skimming.
- Quantify the problem; opinions without data invite bikeshedding.
- Invite dissent explicitly and record open questions rather than hiding them.
- Keep it updated during implementation, and capture major choices as short **ADRs** (Architecture Decision Records) in the repo.

In interviews, saying "I wrote a design doc comparing three options and the reviewers changed my mind on X" is a strong senior signal.
"""))

NOTES.append(("lead-estimation-breakdown", "Estimating and Breaking Down Work", r"""
"How long will this take?" is one of the most consequential questions you answer as a senior engineer. Bad estimates aren't the problem; **unexplained** estimates and **late surprises** are. Interviewers probe this through behavioral questions ("tell me about an estimate that went wrong") and in design rounds ("how would you phase this?").

## A repeatable method

1. **Clarify the outcome.** What does done mean: merged, deployed behind a flag, rolled out to all users, old system deleted?
2. **Slice vertically.** Prefer thin end-to-end slices (API + DB + UI for one case) over horizontal layers ("all DB work first"). Each slice is demoable and de-risks integration early.
3. **Find the unknowns.** List what you don't know (a third-party API's behaviour, data quality, performance at volume). Time-box **spikes** to answer the biggest ones before committing.
4. **Estimate in ranges.** Give best / likely / worst for each piece. A three-point estimate `(best + 4 x likely + worst) / 6` is a handy weighted average; the spread tells you how risky the item is.
5. **Add the invisible work.** Code review rounds, tests, migrations, environment issues, security review, documentation, rollout, monitoring, and meetings. These often double "coding time".
6. **Sequence by risk.** Do the riskiest slice first so bad news arrives early.
7. **Communicate confidence**, not just a date: "Likely three weeks; could be five if the partner's sandbox is unreliable. I'll know more after Tuesday's spike."
8. **Track and re-estimate** at each milestone; tell stakeholders as soon as a range moves.

## Worked example: "Add partial refunds to the payments service"

| Slice | Notes | Best | Likely | Worst |
|---|---|---|---|---|
| Spike: gateway partial-refund API in sandbox | Unknown webhook behaviour | 0.5 | 1 | 2 |
| Schema: `refund` table, migration (expand only) | Backward compatible | 0.5 | 1 | 1 |
| `POST /refunds` with idempotency key, validation, authorization | Core logic | 2 | 3 | 5 |
| Webhook handler: status updates, dedupe | Out-of-order events | 1 | 2 | 4 |
| Ledger entries and reconciliation report | Finance sign-off | 1 | 2 | 4 |
| Tests: unit, Testcontainers integration, contract | | 1 | 2 | 3 |
| Dashboards, alerts, runbook | | 0.5 | 1 | 1 |
| Rollout: flag, 5% merchants, then all | Elapsed time, low effort | 1 | 2 | 3 |
| **Total (days)** | Plus review and waiting time | **7.5** | **14** | **23** |

Communicated as: "About three weeks of work, likely done in four calendar weeks with reviews and the staged rollout; worst case around five if gateway webhooks behave differently from the docs. The spike on day one will narrow it."

## Common failure modes

- **Single-point estimates** given under pressure in a meeting. It's fine to say "I'll come back by tomorrow with a range."
- **Estimating only the happy path** and forgetting migration, testing, rollout and support.
- **Anchoring** on the date the stakeholder hoped for.
- **Silent slippage**: knowing on day 5 you're behind and announcing it on day 14.
- **Hero estimates** that assume no interruptions, reviews or on-call duties.

## When the date is fixed

Often the deadline is real (a sale, a regulatory date, a client demo). Then negotiate **scope, not quality**:

```text
Option A: full feature by [date] -> not feasible without skipping tests/rollout (I don't recommend)
Option B: refunds for card payments only by [date]; UPI refunds two weeks later
Option C: manual refund tool for ops by [date]; self-serve API next sprint
```

Present options with consequences and a recommendation; let the stakeholder choose with eyes open. Record the decision.

## Breaking down work for others

When leading a project, split it so several people can work in parallel with clear interfaces (agree on API contracts and event schemas first, then build both sides against them). Give each person end-to-end ownership of a slice rather than a layer; it builds ownership and reduces hand-offs. Keep a simple visible tracker of slices, owners and risks, and review it weekly.
"""))

NOTES.append(("lead-tradeoffs-disagreement", "Making Trade-offs and Handling Disagreement", r"""
Seniority shows most clearly in **how you decide** when there's no obviously right answer, and in **how you disagree** without damaging relationships or the project.

## Framing a trade-off

1. **State the decision and the constraint** that makes it hard: "We need idempotent refunds before the sale in 3 weeks, and our team has no Kafka experience."
2. **List 2-4 real options**, including "do nothing" or "do the simple thing".
3. **Pick criteria that matter here**: time to deliver, operational risk, cost, performance, team skills, reversibility, consistency with the platform.
4. **Compare honestly**, then recommend and say what would change your mind.

```text
              Time   Ops risk   Cost   Fits skills   Reversible
DB unique key  2d     low        none   yes           easy        <- recommend now
Redis lock     3d     medium     small  yes           easy
Kafka + saga   3w     high       medium no            hard        <- revisit at 10x volume
```

**Reversibility** is a powerful lens. Amazon's framing of "one-way" versus "two-way doors" captures it: easily reversible decisions should be made quickly by the people closest to the work; hard-to-reverse ones (data models, public APIs, vendor lock-in, deleting data) deserve slower, wider review. Many teams record the outcome in a short **ADR**: context, decision, consequences.

## Disagreeing with a senior engineer or architect

1. **Understand first.** Ask what problem their approach optimises for. Often they know a constraint you don't (a past incident, a platform roadmap).
2. **Bring evidence, not adjectives.** "This query does a full scan on 40M rows; here's the EXPLAIN and a benchmark with the composite index" beats "I think it'll be slow".
3. **Make it cheap to test.** Propose a spike, a prototype, or a load test with agreed success criteria.
4. **Separate the person from the idea** and disagree in the right forum: the design review or a 1:1, not a public Slack thread.
5. **Escalate transparently if needed**, together: "We see it differently; let's take both options to [tech lead] with the trade-offs written down."
6. **Disagree and commit.** Once decided, support the decision fully, and if your concern was a risk, add monitoring so you'll both learn quickly if it materialises.

## Pushing back on a PM or business stakeholder

Translate technical concerns into **user and business impact**, and always arrive with options:

- Weak: "We can't do that, the code is a mess."
- Strong: "Shipping by the 15th means skipping the migration dry run. If the migration locks the orders table during the sale, checkout could be down for [~20 minutes], roughly [Rs X lakh] of orders. Option: ship the UI on the 15th behind a flag and the migration on the 18th after a dry run. Same customer launch date, much lower risk."

Then let them make an informed choice. Product owns *what* and *when*; engineering owns making the risks and costs visible. Put the decision in writing.

## Handling disagreement inside the team

- Time-box debates; if two options are both reasonable and reversible, pick one and move on.
- Use written proposals to depersonalise ("option A vs option B"), not "Rahul's idea vs mine".
- Notice when quieter people haven't spoken; ask them directly.
- Assume good intent; most disagreements come from different information or different priorities.

## What interviewers listen for in disagreement stories

- You **listened** and could state the other side's best argument.
- You used **data or experiments**, not seniority or volume.
- The relationship **survived or improved**.
- You **committed** once the decision was made, even when it wasn't yours.
- Bonus: a time **you were wrong** and changed your mind gracefully. Interviewers trust candidates who can say that.

Avoid stories where you were simply right and everyone else was foolish; they signal poor collaboration even when the technical point was correct.
"""))

NOTES.append(("lead-mentoring-code-review", "Mentoring and Code Review Culture", r"""
Seniors are measured partly by how much better they make everyone else. Two everyday tools do most of that work: **code review** and **deliberate mentoring**.

## What code review is for

1. **Correctness and safety**: bugs, edge cases, concurrency, security, data migrations.
2. **Design and maintainability**: does it fit the architecture, is it simpler than it could be?
3. **Knowledge sharing**: more than one person understands each part of the system.
4. **Consistency**: conventions, error handling, logging, testing patterns.

Style is mostly for automation (formatters, linters, static analysis), not humans.

## How to review well

- **Review in risk order**: tests and intent first, then correctness and security, then design, then readability.
- **Label comments** so the author knows what matters (inspired by the "Conventional Comments" convention):
  - `blocking:` must change before merge (bug, security, data risk)
  - `suggestion:` improvement worth considering
  - `question:` I'm trying to understand
  - `nit:` trivial, optional
- **Explain why** and suggest a direction, ideally with a snippet or link.
- **Praise specifically** when something is good; it teaches as much as criticism.
- **Be fast**: aim to respond within a working day; slow reviews kill flow and encourage giant PRs.
- **Keep PRs small** (a few hundred lines) and ask for splits kindly when they aren't.
- **Move big discussions offline**: if a thread passes three rounds, talk for ten minutes and summarise the outcome in the PR.

```text
Weak:  "This is wrong."
Weak:  "Why didn't you use a map here??"
Good:  "blocking: two concurrent requests can both pass the balance check before either
        writes (lost update). Could we use a conditional UPDATE ... WHERE balance >= ?
        or @Version optimistic locking? Happy to pair on it."
Good:  "nit: `processData` -> `reconcileSettlements` would make the intent clearer."
```

## Receiving review gracefully

Thank reviewers, ask clarifying questions, push back with reasons when you disagree, and don't take comments personally. Seniors model this; juniors copy it.

## Mentoring: practical techniques

- **Onboarding plan**: first week setup and a tiny PR, first month a real feature with a buddy, documented "how we work" notes. Track time to first meaningful PR.
- **I do, we do, you do**: demonstrate (you drive while they watch), pair (they drive while you guide), then delegate (they own it and you review).
- **Ask before telling**: "What do you think is happening?" builds debugging skill faster than giving answers.
- **Stretch assignments with a safety net**: let them own a slice of a project, with check-ins and a clear escalation path.
- **Feedback that lands**: use Situation-Behaviour-Impact. "In yesterday's incident call (situation), you posted the exact query and its plan (behaviour), which let us find the missing index in minutes (impact)." Corrective feedback uses the same structure, in private and soon.
- **Create space**: let others present the design, lead the retro, or answer the question in the meeting even if you could do it faster. Will Larson's StaffEng writing calls this creating space for others: your goal is the team's growth, not your visibility.
- **Write things down**: runbooks, ADRs, a "how to debug X" page. Documentation is mentoring that scales.

## Raising the team's quality bar without being the police

- Agree on a short **definition of done**: tests, observability, docs, feature flag, rollback plan.
- Add **automation** for what humans keep repeating in reviews (lint rules, ArchUnit tests, PR templates).
- Run occasional **review walkthroughs** where the team reviews one interesting PR together.
- Celebrate good catches in review publicly; it signals what the team values.

## Interview stories this produces

- "I mentored a junior from first PR to owning the reconciliation job in [N] months."
- "Our review turnaround was [3 days]; I proposed a rotation and smaller PRs, and it dropped to [under a day]."
- "I introduced Testcontainers and a PR template; escaped defects fell by [X%]."

Measured outcomes plus how you did it make these credible.
"""))

NOTES.append(("lead-incidents-postmortems", "Driving Incidents and Blameless Postmortems", r"""
Production incidents are where seniority is most visible: calm coordination, mitigation before root cause, clear communication and real follow-through. Almost every senior behavioral loop includes "tell me about an incident".

## The incident lifecycle

```text
detect -> triage & declare -> assign roles -> MITIGATE -> communicate (on a cadence)
       -> resolve -> verify -> postmortem -> action items tracked to closure
```

**Declare early.** Declaring an incident that turns out minor is cheap; a silent hour of three engineers debugging separately is expensive.

## Roles (even on a small team)

| Role | Responsibility |
|---|---|
| **Incident commander (IC)** | Owns coordination and decisions, not the debugging. Keeps the timeline, assigns tasks, decides on rollback. |
| **Operations / subject experts** | Investigate and apply mitigations. |
| **Communications** | Updates stakeholders and status page on a fixed cadence. |
| **Scribe** | Records actions and timestamps (often the IC on small teams). |

On a two-person team, one debugs and one coordinates and communicates. Splitting these is a senior move.

## Mitigate first, investigate second

Restore service using the fastest safe lever, then find the root cause:

- Roll back the latest deploy or config change.
- Turn off a feature flag or kill switch.
- Shed load or rate-limit the noisy client; scale out if the bottleneck is truly capacity.
- Fail over to a replica or another region.
- Drain a bad host or shard.

The debugging method from this site's production-debugging content applies: confirm the symptom, check latency, traffic, errors and saturation, correlate with recent changes, compare healthy and unhealthy instances, mitigate, verify, then add a guardrail.

## Communication template

```text
[INCIDENT SEV-2] Checkout failures for ~15% of users since 18:05 IST
Impact:  card payments failing with 502; UPI unaffected
Status:  mitigating - rolling back release 2026.10.08-2 (ETA 18:30)
Next update: 18:35 or sooner
IC: [name]  Channel: #inc-checkout-1008
```

Short, factual, impact-first, with a time for the next update. Stakeholders tolerate bad news far better than silence.

## Blameless postmortems

Google's SRE practice popularised the **blameless postmortem**: assume people acted reasonably with the information and tools they had, and fix the system that allowed the failure. Blame makes people hide information, and hidden information causes repeat incidents.

```text
Title, date, severity, authors
Summary         2-3 sentences: what happened, impact, duration
Impact          users affected, failed orders, revenue, SLO budget consumed
Timeline        detection, key decisions, mitigation, resolution (with timestamps)
Root cause and contributing factors   technical + process (why wasn't it caught?)
What went well / what went poorly / where we got lucky
Action items    specific, owned, dated, prioritised (prevent, detect faster, mitigate faster)
```

Good action items are concrete: "Add a canary step that blocks promotion if payment success rate drops more than 2% (owner, date)", not "be more careful". Track them like product work; incomplete action items are why the same incident happens twice.

**"Five whys"** is useful but can tunnel into a single root cause. Real incidents usually have several contributing factors: a bug, a missing test, an alert that didn't fire, a runbook that was out of date.

## What senior behaviour looks like in an incident

- You step up to coordinate when nobody is, or support the IC without taking over.
- You choose rollback over heroic live debugging when users are impacted.
- You communicate proactively upward and to support teams.
- You write or drive the postmortem, even if the bug wasn't yours.
- You follow up weeks later to confirm action items shipped.
- You turn the lesson into a systemic improvement (a test, an alert, a deployment guardrail) and share it beyond your team.

## Story structure for "tell me about an incident"

Stakes (what was breaking and for whom, with numbers), your role, how you diagnosed and mitigated (specific steps and decisions), the outcome (time to mitigate, impact contained), and the systemic fix afterwards. End with what you'd do differently. Practise saying it in under three minutes.
"""))

NOTES.append(("lead-stakeholder-communication", "Stakeholder Communication: Status, Risks and Saying No", r"""
Product companies promote engineers who make their work **legible**: people know what's happening, what's at risk and what's needed from them, without having to ask. Communication quality also directly affects how interviewers level you.

## Know your audience

| Audience | Cares about | Give them |
|---|---|---|
| Your team | How, details, blockers | Technical specifics, decisions, ownership |
| Engineering manager | Delivery, risks, people | Status vs plan, risks with mitigations, asks |
| Product manager | Scope, user impact, dates | Options with trade-offs in user/business terms |
| Other teams | What they need to do and when | Clear asks, interfaces, deadlines |
| Leadership | Outcome, risk, cost, decisions needed | One-paragraph summary, a decision request |

## Bottom line up front (BLUF)

Start with the conclusion or the ask, then the supporting detail.

```text
Weak:  "So we started looking at the slow queries last week and found that the orders
        table has grown a lot, and there were a few indexes... (eight sentences later)
        ...so we might need to delay."
Good:  "We need to move the bulk-export launch from the 10th to the 17th. Reason: the
        export query takes 40 s at current data volume and would time out for large
        merchants; the fix (summary table + async export) needs one more week.
        Decision needed from you: accept the new date, or launch on the 10th for
        merchants under 50k orders only."
```

## A weekly status update template

```text
Project: Partial refunds            Status: AMBER (was GREEN)
Done this week:   refund API in staging; webhook dedupe merged
Next week:        ledger entries; 5% merchant rollout behind flag
Risks:            gateway sandbox returns duplicate webhooks out of order
                  -> added dedupe + ordering by event timestamp; testing Tue
Asks:             finance sign-off on reconciliation report format by Thu
Dates:            full rollout 24th (unchanged, 3 days of buffer left)
```

Five lines that people can skim beat a long narrative. Colour status honestly; a project that is green until the day before launch and then red destroys trust.

## Raising risks early ("no surprises")

- Raise a risk when it's **likely enough to matter**, not when it's certain. Pair every risk with a mitigation or an ask.
- Quantify where possible: probability, impact, date.
- Escalating is not failing. Escalate when you need a decision or resources you can't get yourself, after trying the obvious routes, and frame it as a choice: "We can hit the date by dropping X, or keep X and move two weeks; which matters more?"

## Saying no (or "not now") well

1. **Acknowledge the goal** behind the request.
2. **Explain the cost** in their terms: what slips, what risk increases.
3. **Offer alternatives**: a smaller version, a later date, a workaround.
4. **Let them decide** if it's their call, and confirm in writing.

"I understand sales needs the custom report for the client demo. Building it properly takes two weeks and would push the refunds launch. Option: I export the data to a spreadsheet for the demo this week, and we prioritise the real report next sprint. Does that work?"

## Writing for leadership

Leaders read quickly and between meetings. Keep it to what changed, why it matters, what you recommend and what you need. Lead with numbers ("reduces checkout p99 from 1.8 s to 0.9 s; expected conversion lift based on last year's latency experiment"), and keep the technical appendix separate.

## Meetings and async habits

- Send an agenda beforehand and a summary with decisions and owners afterwards.
- Prefer a written proposal plus a short discussion over a long meeting.
- Document decisions where people will find them (design doc, ADR, ticket), not only in chat.

## In interviews

Communication questions appear directly ("tell me about delivering bad news", "how do you handle conflicting priorities?") and indirectly in every answer. Structure your answers the same way you'd structure a status update: headline first, then specifics, then outcome. Interviewers notice.
"""))

NOTES.append(("lead-project-deep-dive", "The Project Deep-Dive Round and Stakes-Action-Outcome Stories", r"""
Many senior loops include a 45-60 minute **project deep dive**: you present a project you led, and the interviewer probes until they find the edge of your understanding. Google, for example, has been adding a technical conversation about past work to its loops. You can't bluff it, but you can prepare thoroughly.

## A structure that works (aim for 10-12 minutes, then probes)

```text
1. Context      (1-2 min)  Business problem, users, scale. Why it mattered (numbers).
2. Constraints  (1 min)    Deadline, team size, legacy systems, compliance, budget.
3. Options      (2 min)    2-3 approaches you considered and the criteria.
4. Decision     (2 min)    What you chose and why; the architecture (draw it).
5. Failure      (1-2 min)  What went wrong or was hard, and how you handled it.
6. Results      (1 min)    Measured outcomes: latency, errors, cost, revenue, adoption.
7. Lessons      (1 min)    What you'd do differently now.
```

Throughout, make **your role** explicit. "We" is fine for team context; "I" must appear for decisions and actions. Interviewers' notes literally separate what the candidate did from what the team did.

## Example outline (adapt with your real details)

**Context:** At [Company], for [Client], the order reconciliation job (Spring Boot batch + MySQL) matched [~2M] daily transactions against bank settlement files. It ran [~6 hours] and failed [2-3 times a month], delaying merchant payouts and generating [~40] support tickets per failure.

**Constraints:** Two developers, a [6-week] window before peak season, no new infrastructure budget, data in a shared MySQL instance also serving the live app.

**Options:** (a) tune queries and add indexes; (b) partition the job by merchant and parallelise with Spring Batch partitioning; (c) move to a streaming design with Kafka. Criteria: delivery time, risk to the live database, operability.

**Decision:** I proposed (b) plus (a). I profiled the job, found [N+1 queries and a full scan on settlement_date], added a composite index after testing on a production-sized copy, and introduced chunked, partitioned processing with idempotent upserts so a failed partition could be retried alone. Streaming was rejected for now because of the team's skills and timeline; I documented it as the next step.

**Failure:** The first parallel run caused lock contention with the live checkout flow. I rolled back, reduced partition concurrency, scheduled the heaviest partitions off-peak, and added a read replica for the read-heavy phase.

**Results:** Runtime from [6 hours to 50 minutes], zero failed runs over [3 months], payout delays eliminated, support tickets down [~90%].

**Lessons:** I'd load-test against realistic concurrent traffic earlier, and I'd involve the DBA at design time rather than after the first contention issue.

## Probes to prepare for

- "Why not option C?" (know the trade-off, not just the choice)
- "What happens at 10x data?" (where it breaks next)
- "How did you measure that improvement?" (dashboards, before/after method)
- "What was the hardest bug?" (specifics: logs, queries, root cause)
- "What would you change now?" (shows growth)
- "Who disagreed, and how was it resolved?"
- "Draw the data flow / the schema / the failure path."

Rehearse by having a friend interrupt you with "why?" every two minutes.

## Stakes-Action-Outcome for behavioral answers

STAR (Situation, Task, Action, Result) is familiar but often produces long setups. **Stakes-Action-Outcome (SAO)** keeps answers tight and senior-sounding:

- **Stakes (20%)**: what was at risk and for whom, with a number. "Checkout errors at 4% during a sale; roughly [Rs X] of orders per hour at risk."
- **Action (60%)**: what *you* did, the decisions and trade-offs, how you worked with others. Specific verbs: diagnosed, proposed, negotiated, rolled back, mentored.
- **Outcome (20%)**: measured result, plus what you learned or changed systemically.

Keep answers to about two minutes, then let follow-ups pull detail.

## Build a story bank

Prepare 8-10 stories and map each to several themes, so one good story can answer multiple questions:

| Story | Ownership | Ambiguity | Conflict | Failure | Mentoring | Incident | Influence |
|---|---|---|---|---|---|---|---|
| Reconciliation job rewrite | x | x | | x | | | x |
| Checkout incident and postmortem | x | | | x | | x | |
| Pushback on launch date | | | x | | | | x |
| Onboarding a junior | | | | | x | | |

Write each in SAO bullets with real numbers. Mark which details are confidential and replace them with relative figures.

## Common mistakes

Too much context and not enough decisions; no numbers; a team story with no "I"; claiming you'd change nothing; defensive answers about failures; and memorised scripts that fall apart under the first probe. Know the project deeply instead of memorising sentences.
"""))

# ---------------------------------------------------------------- Q&A
QA = []

QA.append(("Tell me about the most technically complex project you've owned end to end.", r"""
**What they test:** scope, depth, ownership beyond coding, and whether "I" is real.

**Model answer (SAO, adapt):**
- **Stakes:** "At [Company], our [Client]'s settlement reconciliation job (Spring Boot batch, MySQL) took [~6 h] and failed [2-3x/month], delaying merchant payouts and creating [~40] tickets per failure. Peak season was [6 weeks] away."
- **Action:** "I owned the redesign. I profiled the job and found N+1 queries and a full scan on `settlement_date`. I compared three options (query tuning, partitioned parallel processing, Kafka streaming) in a short design doc; we chose partitioning plus indexes because it fit our timeline and skills. I implemented idempotent upserts so failed partitions could retry alone. The first parallel run caused lock contention with live checkout, so I rolled back, lowered concurrency, scheduled heavy partitions off-peak and moved reads to a replica. I added dashboards and a runbook."
- **Outcome:** "Runtime dropped to [~50 min], zero failed runs over [3 months], tickets down [~90%]. I'd load-test against concurrent production traffic earlier next time."

**Follow-ups to prepare:** why not streaming; what breaks at 10x; how you measured; the hardest bug.
""", I, ["project-deep-dive", "ownership", "behavioral"], True))

QA.append(("Walk me through a design decision where you had to choose between several options.", r"""
**What they test:** structured trade-off thinking, use of data, and willingness to write decisions down.

**Model answer (adapt):**
- **Stakes:** "Duplicate order-confirmation SMS and slow checkouts were traced to a synchronous call from `order-service` to `notification-service` inside the checkout transaction: [3] incidents in a quarter."
- **Action:** "I listed options in a one-page design doc: (1) keep the sync call with a timeout and circuit breaker, (2) publish to Kafka after commit, (3) `@Async` in-process, (4) transactional outbox plus Kafka. Criteria: no lost notifications, no duplicates, delivery time, operational load. Option 2 loses events if the app crashes between commit and publish; option 3 loses them on restart. I recommended (1) as an immediate mitigation and (4) as the real fix, with consumer deduplication on `event_id`. Reviewers pushed back on running Debezium, so we used a simple polling relay first; that was a good call for our team's skills."
- **Outcome:** "Checkout p99 improved from [1.8 s to 1.1 s], duplicate SMS dropped to zero, and the doc became the template for two other teams."

**Tip:** always mention an option you rejected and why, plus one thing reviewers changed.
""", I, ["trade-offs", "design-docs", "behavioral"], True))

QA.append(("Tell me about a time you disagreed with a senior engineer or architect on a technical approach.", r"""
**What they test:** listening, evidence over opinion, and commitment after the decision.

**Model answer (adapt):**
- **Stakes:** "Our architect at [Company] proposed caching all product-catalog reads in Redis to fix slow product pages before a sale. I was concerned we'd add cache invalidation bugs for prices, which had caused a pricing incident before."
- **Action:** "First I asked what problem he was optimising for; it was p99 latency under sale traffic. I profiled the endpoint and found 70% of the time was one query missing a composite index, plus an N+1 on variants. I shared the EXPLAIN plans and a quick load test showing p99 dropping from [900 ms to 180 ms] with the index and a fetch join. I suggested we fix the queries first and cache only the rarely changing category tree. He agreed to the query fix but still wanted price caching for the sale peak, with a short TTL and event-based eviction. I implemented it that way and added a price-mismatch alert."
- **Outcome:** "The sale ran with p99 under [250 ms] and no pricing errors. I learned his concern about peak load was valid; combining both approaches beat either alone."

**Key signals:** you understood their view, used data, and committed.
""", I, ["disagreement", "influence", "behavioral"], True))

QA.append(("Tell me about a time you pushed back on a product manager or business requirement.", r"""
**What they test:** whether you translate technical risk into business terms and offer options instead of just saying no.

**Model answer (adapt):**
- **Stakes:** "The PM wanted bulk order export for all merchants by [date] for a client demo. At our data volume, the naive query took [~40 s] and would time out for large merchants, and running it on the primary DB risked slowing checkout."
- **Action:** "I didn't just say it couldn't be done. I wrote a short note: the risk (timeouts, checkout impact), the cost of doing it properly (async export job, read replica, S3 download link, about one extra week), and options: (A) launch for merchants under [50k] orders on the date, (B) everyone a week later, (C) a manual export by our team for the demo. I recommended A plus the full version the following week. The PM chose A and C for the demo client."
- **Outcome:** "The demo went well, the full async export shipped [8] days later, and checkout latency was unaffected. The PM started involving me earlier in scoping, which reduced late surprises on later features."

**Key signals:** empathy for the goal, quantified risk, options, a recommendation, and the decision recorded.
""", I, ["pushback", "stakeholders", "behavioral"], True))

QA.append(("Describe a production incident you handled. What was your role?", r"""
**What they test:** calm coordination, mitigation before root cause, communication and follow-through.

**Model answer (adapt):**
- **Stakes:** "At [time] during a sale, card payments started failing for [~15%] of users with 502s. Orders were dropping at about [N] per minute."
- **Action:** "I was on call. I declared the incident in our channel, took the coordinator role and asked a teammate to investigate payment-service logs. Errors had started [10] minutes after a release, so I made the call to roll back rather than debug live, and posted updates every 15 minutes to support and the business. Errors cleared within [8] minutes of the rollback. Root cause: a new HTTP client config had a connection pool of 10 to the payment gateway, which exhausted under sale load."
- **Outcome:** "Impact was limited to [~25 minutes]. I wrote the blameless postmortem; action items included load-testing gateway calls at sale volume, alerts on pool saturation, and a canary step gated on payment success rate. I followed up until all three shipped. We haven't had a repeat."

**Tip:** separate what you did from what the team did, and name the systemic fix.
""", I, ["incident", "ownership", "behavioral"], True))

QA.append(("Tell me about a time you made a mistake that affected production.", r"""
**What they test:** honesty, ownership without excuses, and systemic learning. Pick a real mistake with real impact, not a disguised strength.

**Model answer (adapt):**
- **Stakes:** "I wrote a Flyway migration adding a NOT NULL column with a default to our `orders` table ([~30M] rows). On our MySQL version it rebuilt the table and held a lock; checkout writes queued for [~4 minutes] during business hours."
- **Action:** "I spotted the lock waits in the DB dashboard, told the team immediately that it was my migration, and we decided to let it finish rather than kill it mid-rebuild (which risked a longer rollback). I posted updates to support. Afterwards I wrote the postmortem: I'd tested on a small staging table and assumed the DDL was instant."
- **Outcome:** "I added a CI check that flags DDL on large tables, documented how to verify online/instant DDL support, and we adopted expand-and-contract migrations run off-peak with `lock_wait_timeout` set. Since then we've run [N] migrations on large tables with no locking incidents. Personally, I learned to test risky changes on production-sized data."

**Avoid:** blaming others, trivial mistakes, or ending without a systemic fix.
""", I, ["failure", "mistake", "ownership", "behavioral"], True))

QA.append(("Tell me about a time you worked on a problem with unclear or changing requirements.", r"""
**What they test:** turning ambiguity into a plan, and making progress without waiting for perfect information.

**Model answer (adapt):**
- **Stakes:** "Our [Client] asked for 'better visibility into failed payments'. No spec, a vague deadline before their quarterly review, and three stakeholder groups (support, finance, engineering) wanting different things."
- **Action:** "I spent two days interviewing each group and looking at the top support tickets. I wrote a one-page problem statement with three user stories, success metrics and explicit non-goals, and got sign-off from the client lead. I sliced delivery: first, a daily failed-payments report from existing data (one week); second, a searchable dashboard; third, automatic retry for gateway timeouts. Finance changed their reconciliation needs mid-way, so I absorbed it into slice two by adding a column rather than reopening slice one."
- **Outcome:** "Slice one shipped in [6] days and reduced support's investigation time from [~20 to ~5] minutes per ticket. Slice three recovered [~Rs X] per month in previously failed payments. The client used the problem statement format for later requests."

**Key signals:** you clarified, wrote it down, delivered in slices and adapted.
""", I, ["ambiguity", "requirements", "behavioral"], True))

QA.append(("Give an example of how you mentored someone or made your team better.", r"""
**What they test:** multiplying others, not just personal output.

**Model answer (adapt):**
- **Stakes:** "A new graduate joined our team at [Company]. Our onboarding was ad hoc; previous joiners took [~6 weeks] to ship their first meaningful change, and I was the only person who understood the settlement module, a bus-factor risk."
- **Action:** "I made a 30-60-90 day plan with her: environment setup and a small bug fix in week one, then a real feature with me pairing, then ownership of the settlement report. I used 'I do, we do, you do': I drove the first debugging session, we paired on the second, she led the third. In reviews I labelled comments as blocking or nit and explained the why. I also turned our tribal knowledge into a runbook and an onboarding doc."
- **Outcome:** "She shipped her first feature in [2 weeks] and took over on-call for the settlement module in [3 months]. The onboarding doc cut the next two joiners' ramp-up to [~3 weeks]. I was no longer the only person who could fix the module, which let me take on the reconciliation redesign."

**Tip:** show the method and a measurable result for the person and the team.
""", I, ["mentoring", "team", "behavioral"], True))

QA.append(("Tell me about a time you improved something nobody asked you to.", r"""
**What they test:** ownership and initiative, and whether you choose improvements that matter.

**Model answer (adapt):**
- **Stakes:** "Our CI pipeline at [Company] took [~35 minutes] and failed randomly about [1 in 5] runs due to flaky integration tests. Developers re-ran builds and merged with less testing, and two bugs had escaped to production the previous month."
- **Action:** "It wasn't on our roadmap, so I first quantified the cost: about [N] developer-hours a week lost to waiting and reruns. I shared that with my manager and proposed spending [20%] of my time for two sprints on it. I replaced the shared test database with Testcontainers so tests were isolated, fixed time-dependent tests by injecting a `Clock`, parallelised test modules and added Maven dependency caching."
- **Outcome:** "Build time dropped to [~12 minutes] and flaky failures to near zero. Developers stopped bypassing tests, and we had no escaped bugs from that area over the next quarter. I wrote a short guide so other teams could adopt the same setup; two did."

**Key signals:** you measured the problem first, got buy-in for your time, delivered, and spread the improvement.
""", I, ["ownership", "initiative", "behavioral"], True))

QA.append(("How do you estimate a feature? Tell me about an estimate that went wrong.", r"""
**What they test:** a realistic estimation method, honest communication when estimates slip, and learning.

**Method (brief):** clarify what done means; slice vertically; spike the biggest unknowns; estimate in ranges; add the invisible work (reviews, tests, migrations, rollout, monitoring); communicate confidence and re-estimate at milestones.

**Story (adapt):**
- **Stakes:** "I estimated an integration with a new payment gateway at two weeks, based on their documentation. The client had announced the launch date to merchants."
- **Action:** "By day four, the sandbox showed webhooks arriving out of order and duplicated, which the docs didn't mention. I told my manager and the client lead that day, not at the deadline, with a revised range of three to four weeks and options: launch with polling-based status checks (on time but slower updates), or wait for the robust webhook handling. They chose polling first. I then built idempotent, order-tolerant webhook processing as a fast follow."
- **Outcome:** "We launched on the original date, and the webhook version followed [10] days later. Since then I always start external integrations with a time-boxed spike against the real sandbox before committing to a date, and I give ranges instead of single numbers."
""", I, ["estimation", "planning", "behavioral"], True))

QA.append(("Tell me about delivering under a tight deadline. What did you cut, and what did you refuse to cut?", r"""
**What they test:** prioritisation, protecting quality where it matters, and negotiating scope instead of burning out quietly.

**Model answer (adapt):**
- **Stakes:** "Our [Client] needed GST invoice generation live by [date] because of a regulatory change. We had [3 weeks] for what we'd estimated at [5]."
- **Action:** "I listed scope items and classified them: legally required (correct tax calculation, invoice numbering without gaps, PDF generation), important but deferrable (email delivery, admin re-generation UI), and nice-to-have (custom templates per merchant). I proposed shipping the legally required set with merchants downloading invoices from the dashboard, and deferring email and templates by two weeks. I refused to cut automated tests for tax calculations and the idempotent invoice-number sequence, because errors there would be legal problems and expensive to fix. I wrote this up and got sign-off from the client and my manager."
- **Outcome:** "We went live on time with zero tax calculation defects; email delivery followed [12] days later. The client appreciated knowing the trade-offs upfront instead of discovering gaps after launch."

**Key signal:** you cut scope deliberately and in writing, never correctness or safety.
""", I, ["deadline", "prioritization", "behavioral"], False))

QA.append(("Describe a time you reduced technical debt. How did you justify it to the business?", r"""
**What they test:** connecting engineering work to business outcomes and getting buy-in, not just complaining about legacy code.

**Model answer (adapt):**
- **Stakes:** "Our order module at [Company] was a 4,000-line service class with no tests. Every change to discounts took [~2x] the estimate and caused a regression roughly every other release; [3] customer-facing pricing bugs in a quarter."
- **Action:** "I gathered data: lead time for discount-related tickets, regression count, and hours spent on hotfixes. I presented it to the PM in business terms: 'pricing bugs cost us [Rs X] in refunds and slow down every promotion launch'. I proposed an incremental plan rather than a rewrite: characterisation tests around current behaviour first, then extracting a `PricingEngine` with a strategy per discount type, one type per sprint, using about [20%] of capacity while features continued. Each step shipped behind the same API."
- **Outcome:** "Over [two months], discount-ticket lead time dropped [~40%], and pricing regressions went to zero for the next two quarters. The PM began reserving capacity for debt work each sprint because the results were visible."

**Tip:** quantify the cost of the debt, propose incremental delivery, and show the measured payoff.
""", A, ["tech-debt", "business-impact", "behavioral"], False))

QA.append(("How do you give code review feedback? Tell me about difficult feedback you had to give.", r"""
**What they test:** review judgement, kindness with candour, and raising the team's bar.

**How (brief):** review tests and intent first, then correctness, security and design, then readability; label comments (blocking, suggestion, question, nit); explain why and suggest a direction; respond within a day; take long debates to a quick call.

**Story (adapt):**
- **Stakes:** "A capable peer kept submitting large PRs (800+ lines) that mixed refactoring with features, and one of them nearly introduced a race condition in our wallet debit flow that two reviewers missed."
- **Action:** "I asked for a private chat rather than commenting publicly. I used situation-behaviour-impact: 'In the wallet PR last week, the refactor and the feature were combined, so the race in the balance check was hard to spot; we nearly shipped a double-spend bug.' I asked how he saw it; he felt reviews were slow, so he batched changes. We agreed to split PRs by concern, and I committed to reviewing his within a day. I also proposed a team PR-size guideline and template."
- **Outcome:** "His PRs dropped to a few hundred lines, our average review time fell from [~2 days] to [under one], and the template became standard. Our relationship improved because I addressed the cause, not just the symptom."
""", I, ["code-review", "feedback", "behavioral"], False))

QA.append(("Tell me about a time you received critical feedback. What did you do with it?", r"""
**What they test:** self-awareness, coachability and visible change.

**Model answer (adapt):**
- **Stakes:** "In a mid-year review, my manager at [Company] said my technical work was strong, but stakeholders often learned about delays late, and in design discussions I came across as defensive when people questioned my approach."
- **Action:** "My first reaction was to justify myself, but I asked for specific examples, and they were fair: I had flagged a two-week slip only three days before a deadline. I made two changes. First, a short written status update every Friday with risks, sent to the PM and my manager, even when everything was green. Second, in design reviews I started each response to a challenge by restating the other person's point and asking a question before answering. I asked a colleague to tell me when I slipped."
- **Outcome:** "At the next review, my manager specifically mentioned that the PM trusted my estimates more, and on the following project I raised a vendor delay four weeks early, which let us re-plan without missing the launch. Asking for examples has become my default response to feedback."

**Tip:** choose real feedback, show the concrete change, and give evidence it worked.
""", B, ["feedback", "growth", "behavioral"], False))

QA.append(("Tell me about a time you influenced a decision without having authority, for example across teams.", r"""
**What they test:** influence through data, relationships and making it easy for others to say yes.

**Model answer (adapt):**
- **Stakes:** "Three teams at [Company] each called the same payment gateway with their own retry logic. During a gateway slowdown, combined retries tripled traffic, the gateway throttled us, and payments failed for [~30 minutes]. Nobody owned the integration as a whole."
- **Action:** "I had no authority over the other teams, so I started with evidence: I correlated logs from all three services to show the retry storm and wrote a short incident analysis. I met each team's lead individually to understand their constraints; one needed different timeouts for refunds. I then wrote a proposal for a shared gateway client library with Resilience4j (bounded retries with jitter, circuit breaker, per-operation timeouts) and offered to build and maintain the first version myself, making adoption a small dependency change. I presented it at the architecture forum with the leads' input already included."
- **Outcome:** "All three teams adopted it within [6 weeks]. In the next gateway slowdown, traffic stayed flat and the circuit breaker failed fast, so failures were limited to [~2 minutes]."

**Key signals:** evidence, 1:1 alignment before the big meeting, and lowering the cost of saying yes.
""", A, ["influence", "cross-team", "behavioral"], True))

QA.append(("Tell me about a decision you made that you later reversed or changed your mind about.", r"""
**What they test:** intellectual honesty, learning from data, and comfort with being wrong. Seniors who never change their minds are a red flag.

**Model answer (adapt):**
- **Stakes:** "I championed moving our notification service from MySQL to MongoDB because templates and payloads were semi-structured and schema changes felt slow. I got approval and we migrated one notification type."
- **Action:** "After a month, the data told a different story: most queries were relational (notifications joined with user preferences and delivery status), we were duplicating data to avoid joins, and the team had no MongoDB operational experience, so on-call issues took longer to resolve. MySQL 8's JSON columns would have covered the flexible payload part. I wrote up the comparison, said plainly that my original recommendation was wrong for our context, and proposed reverting before more types were migrated."
- **Outcome:** "We reverted in [one sprint] with a JSON column for the payload, avoiding a second database to operate. I now insist on a time-boxed spike with real query patterns and an operational-readiness check before proposing a new datastore. My manager later cited this as an example of good judgement."

**Tip:** show the evidence that changed your mind and how fast you acted on it.
""", A, ["decision-making", "humility", "behavioral"], False))

QA.append(("Tell me about a time you had to learn a new technology quickly to deliver something.", r"""
**What they test:** learning strategy, pragmatism and delivering safely while learning.

**Model answer (adapt):**
- **Stakes:** "Our [Client] project needed an event-driven integration using Kafka within [three weeks]. Nobody on our team had used Kafka in production."
- **Action:** "I time-boxed learning to the parts on our critical path: topics and partitions, consumer groups, offsets and commit strategies, delivery semantics, and Spring Kafka's error handling. I built a small prototype with Testcontainers to see rebalancing and redelivery behaviour myself rather than trusting blog posts. I paired with an engineer from another team who ran Kafka in production for a one-hour review of my design, which caught that our consumer wasn't idempotent and that we needed a dead-letter topic. I documented what I learned in a short internal guide."
- **Outcome:** "We delivered on time with idempotent consumers, a DLT and lag alerts; no message-loss incidents in the first [six months]. Two teammates used my guide to ramp up, and I became the team's go-to person for Kafka."

**Key signals:** focused learning, hands-on verification, seeking expert review, and sharing knowledge.
""", B, ["learning", "adaptability", "behavioral"], False))

QA.append(("Describe a time you had to communicate a delay or bad news to stakeholders.", r"""
**What they test:** early, honest communication with options, not surprises.

**Model answer (adapt):**
- **Stakes:** "Two weeks before a committed launch of merchant payouts v2, load testing showed our payout batch would take [~5 hours] at projected volume, beyond the bank's cut-off window. Missing the cut-off would delay merchant money by a day."
- **Action:** "I told my manager and the PM the same day, in writing, starting with the bottom line: 'We will miss the cut-off at launch volumes; we need a decision by Thursday.' I explained the cause (row-by-row processing and a slow bank API) and gave three options: (A) launch on time for the [20%] of merchants on the new bank API, (B) delay [10] days to parallelise and batch the bank calls, (C) launch for everyone with an ops team manually splitting files (risky). I recommended A followed by B. I offered to join the call with the business head to answer questions."
- **Outcome:** "They chose A plus B. The partial launch went smoothly and the full rollout followed [9] days later within the cut-off. The PM said the early warning and clear options made the conversation easy."

**Tip:** bottom line first, cause in plain words, options with consequences, a recommendation.
""", I, ["communication", "stakeholders", "behavioral"], False))

QA.append(("How would you handle a teammate who consistently misses commitments or isn't pulling their weight?", r"""
**What they test:** empathy, directness, and knowing what's yours to handle versus your manager's.

**Model answer:**
"I'd start by assuming there's a reason I don't know: unclear expectations, a skill gap, too many parallel asks, or something personal.

1. **Talk privately and early**, with specific examples rather than labels: 'The last two API tickets slipped by about a week each, and the integration with the mobile team got blocked. What's getting in the way?'
2. **Listen and help remove obstacles**: if it's unclear requirements, help break tickets down; if it's a skill gap (say, unfamiliarity with JPA performance), pair on the next task or share resources; if they're overloaded, help them push back on extra asks.
3. **Agree on something concrete**: smaller tasks with check-ins, earlier flagging of risks.
4. **Follow up and recognise improvement.**
5. **Involve the manager** if there's no change after a fair attempt, or immediately if it's a conduct issue. Performance management is the manager's responsibility, and I'd share factual observations, not gossip.

Example (adapt): 'A teammate at [Company] kept missing estimates; it turned out he was getting direct requests from the client and didn't feel able to say no. We routed requests through the board, and his delivery became predictable.'"
""", A, ["team", "conflict", "people", "behavioral"], False))

QA.append(("Tell me about a time you simplified a system or stopped the team from over-engineering.", r"""
**What they test:** pragmatism and judgement: seniors are as valued for what they don't build.

**Model answer (adapt):**
- **Stakes:** "For a new internal feature-flag capability at [Company], the initial proposal was a dedicated microservice with its own database, Kafka-based change propagation and a React admin UI. We had [~15] flags and one team using them, and the estimate was [6 weeks]."
- **Action:** "I asked what problems we actually had: turning features on per environment and per merchant, without a deploy. I sketched a simpler option: a `feature_flag` table in our existing MySQL, a small Spring service class with a Caffeine cache refreshed every 30 seconds, and admin endpoints protected by roles. I compared the options in a short doc, including when the bigger design would make sense (many teams, real-time propagation, experimentation). The team agreed to start simple behind an interface so we could swap to a vendor tool later."
- **Outcome:** "It shipped in [4 days] and handled our needs for over a year. When a second team needed flags, we moved to an open-source tool through the same interface in [a week]. We saved roughly five weeks and avoided another service to operate."

**Key signal:** you defined the real requirements, kept an upgrade path, and named the trigger for revisiting.
""", A, ["simplicity", "pragmatism", "trade-offs", "behavioral"], False))

QA.append(("What's the difference between a mid-level and a senior engineer, and why do you think you're ready?", r"""
**What they test:** self-awareness and evidence, not just ambition.

**Model answer (adapt):**
"The biggest differences are scope, ambiguity and multiplying others. A mid-level engineer delivers well-defined work reliably. A senior engineer takes an ambiguous problem, breaks it down, makes and communicates trade-offs, owns the result in production, and makes the people around them more effective.

Why I'm ready for [SDE-2 / Senior] at [Company]:
- **Ownership:** I owned the redesign of [Client]'s reconciliation job end to end: design doc, implementation, rollout, dashboards; runtime went from [6 h to 50 min].
- **Ambiguity:** I turned a vague 'better visibility into failed payments' request into a three-slice plan that cut support investigation time by [~75%].
- **Influence:** I got three teams to adopt a shared gateway client after a retry-storm incident, without authority over them.
- **Multiplying others:** I mentored a new graduate to on-call ownership in [3 months] and wrote our onboarding guide.

Where I'm still growing: designing systems at much larger scale than my current traffic, and longer-term technical strategy. That's a big reason I want a product company with that scale."

**Tip:** define seniority briefly, then prove it with your stories, and name an honest growth area.
""", B, ["seniority", "self-awareness", "behavioral"], True))

QA.append(("Tell me about a time you used data or metrics to drive a decision.", r"""
**What they test:** evidence-based thinking and whether you measure outcomes.

**Model answer (adapt):**
- **Stakes:** "Our team wanted to rewrite the product search API from MySQL `LIKE` queries to Elasticsearch because users complained search was slow. The rewrite was estimated at [6 weeks]."
- **Action:** "Before committing, I added Micrometer timers and logged query patterns for a week. The data showed p95 latency of [1.2 s] came mostly from two issues: a leading-wildcard `LIKE` on one column and an unindexed sort, and [~80%] of searches were exact SKU or prefix matches. I proposed a two-step plan: fix the indexes, switch to prefix matching plus MySQL full-text search for names, and measure again; adopt Elasticsearch only if p95 stayed above our [300 ms] target or relevance complaints continued."
- **Outcome:** "p95 dropped to [~150 ms] within a week of work. Relevance complaints fell, and we postponed Elasticsearch, saving about five weeks and a new system to operate. A year later, when we added faceted search, we revisited it with real requirements. The approach of instrumenting before deciding became a team habit."

**Key signals:** measured first, set a threshold for the bigger decision, and checked results.
""", I, ["data-driven", "metrics", "decision-making", "behavioral"], False))

QA.append(("At a service company the client owns the roadmap. How did you show ownership in that environment?", r"""
**What they test:** that you're not just a ticket-taker, and that you'll thrive where engineers shape the product. Don't apologise for the service-company context; reframe it.

**Model answer (adapt):**
"The client set priorities, but I owned how well our part worked and often influenced what got built. Three examples:
- **Beyond tickets:** I noticed [Client]'s refund API had no idempotency, and retries from their mobile app created duplicate refunds a few times a month. It wasn't in any sprint. I quantified the cost ([Rs X] a month in manual reversals), proposed an idempotency-key design to the client's tech lead, and implemented it after approval. Duplicates went to zero.
- **Production ownership:** I set up dashboards and alerts for our services and wrote runbooks, so issues were caught by us, not reported by the client's customers.
- **Shaping scope:** when the client asked for a complex reporting feature, I suggested a phased version that delivered the most-used report in a week; they adopted that approach for later requests.

What I'm looking for now is an environment where that kind of ownership is the default expectation, with direct access to users and metrics."

**Tip:** show initiative, measurable impact and influence on the client; end with why a product company fits.
""", I, ["ownership", "service-company", "behavioral"], False))

QA.append(("How do you ramp up in a new team and codebase during your first 90 days?", r"""
**What they test:** a structured approach to becoming effective without bulldozing existing context.

**Model answer:**
"**First 30 days: learn and deliver something small.** Set up the environment and document gaps I hit. Read architecture docs, recent design docs and postmortems: postmortems show where the system really hurts. Trace one critical request end to end (for example checkout) through code, logs and dashboards. Ship a small bug fix or improvement in the first week or two to learn the deploy pipeline. Have 1:1s with my manager, teammates, the PM and on-call engineers: what's working, what's painful, what they expect from me.

**Days 30-60: take real ownership.** Own a meaningful feature or component end to end. Join the on-call rotation with a shadow period. Start contributing thoughtful reviews.

**Days 60-90: improve something.** Propose one improvement backed by what I've learned (a recurring incident cause, a slow pipeline, missing docs), written up and agreed with the team. Agree with my manager on goals for the next six months.

Throughout, I ask lots of questions, write down what I learn (onboarding docs help the next person), and avoid proposing big changes before I understand why things are the way they are."

**Tip:** mention postmortems and on-call; it signals production maturity.
""", I, ["onboarding", "ramp-up", "behavioral"], False))

QA.append(("Tell me about a time you had conflicting priorities from two stakeholders. How did you resolve it?", r"""
**What they test:** prioritisation by impact, transparency and escalating correctly.

**Model answer (adapt):**
- **Stakes:** "In the same sprint, the [Client] finance team wanted a reconciliation report fix for month-end close, and the product team wanted a checkout coupon feature for a marketing campaign. Both called it urgent, and I couldn't do both in time."
- **Action:** "Instead of quietly picking one, I clarified each deadline and impact: month-end close was a hard date with audit implications, while the campaign date could shift by a few days. The coupon work also had a simpler interim option: a fixed discount code that marketing could configure without new code. I wrote both stakeholders a short message with the trade-off and a proposal: report fix first, finished in [3 days], interim coupon via existing configuration, full coupon feature the following week. I copied my manager so the decision was visible and asked for objections by end of day."
- **Outcome:** "Both agreed. Month-end closed on time, the campaign launched on schedule with the interim code, and the full feature followed [5] days later. Finance and product started aligning on priorities with my manager directly in planning, which reduced these clashes."

**Key signals:** facts over loudness, creative options, transparency, and involving the manager.
""", I, ["prioritization", "stakeholders", "behavioral"], False))

QA.append(("Tell me about a time you raised the quality bar for your team.", r"""
**What they test:** improving team standards through systems and persuasion, not policing.

**Model answer (adapt):**
- **Stakes:** "Our team at [Company] had no consistent testing approach: some services had good coverage, others relied on manual QA. In one quarter, [5] production bugs came from untested edge cases in date handling and pagination."
- **Action:** "I proposed a lightweight 'definition of done' in a team retro: tests for new logic including edge cases, structured logging and a metric for new endpoints, and a rollback plan for risky changes. To make it easy rather than a burden, I added a PR template with those checkboxes, created a Testcontainers base class so integration tests against real MySQL took minutes to write, and added a CI gate for coverage on changed lines (not overall coverage, which just encourages useless tests). I ran a short session showing how to test time-dependent code with an injected `Clock`."
- **Outcome:** "Within two quarters, escaped defects dropped from [5] to [1], and review discussions shifted from 'did you test this?' to design questions. Two other teams copied the template."

**Key signals:** diagnosed with data, made the right thing easy, measured the result.
""", I, ["quality", "testing", "team", "behavioral"], False))

QA.append(("In a design review, you believe the proposed design won't handle expected load. The author is more senior than you. What do you do?", r"""
**What they test:** courage plus tact; raising concerns with evidence, in the right way.

**Model answer:**
"I'd raise it, because staying quiet about a scaling risk isn't respectful to anyone, but I'd do it constructively.

1. **Prepare evidence before the meeting**: rough capacity math (for example, the design does a synchronous fan-out to 4 services per request; at a projected [3,000] RPS peak that's [12,000] downstream calls per second, while one of those services is currently tested only to [2,000] RPS), or a quick load test if time allows.
2. **Ask first, then state the concern**: 'How do you see this behaving at the sale peak? My estimate suggests the inventory service becomes the bottleneck; here's my math, I may be missing something.'
3. **Offer options**: caching the read path, making the call async, or a load test as a gate before launch.
4. **If we still disagree**, propose an objective test with agreed pass criteria, and document the risk in the design doc so the decision is explicit.
5. **Commit** to whatever is decided, and add monitoring for the risk.

Example (adapt): at [Company], this approach led us to add a load test before launch; it confirmed the bottleneck and we added caching, with the author leading the fix."
""", I, ["design-review", "disagreement", "influence", "behavioral"], False))

QA.append(("You're asked to lead a migration (e.g. a monolith module to a new service, or MySQL 5.7 to 8). How do you plan and run it?", r"""
**What they test:** risk management, incremental delivery and stakeholder coordination on long projects.

**Model answer:**
"**1. Define why and what done means**: business reason (end of support, scaling, team autonomy), success metrics, and explicit non-goals. Done means the old path is turned off, not just that the new one exists.

**2. Inventory and de-risk**: list consumers, data flows, jobs and integrations; find the unknowns (unsupported SQL modes, collation differences, implicit behaviours) and spike them early.

**3. Plan incremental, reversible steps**: for a service extraction, the strangler pattern behind an API facade, routing traffic gradually with a flag; for a DB upgrade, a replica on the new version, test against production-like traffic, then a planned switchover with a rollback path. Use dual writes or change-data-capture with reconciliation checks where data moves.

**4. Make it observable**: dashboards comparing old and new paths (latency, errors, data mismatches).

**5. Communicate**: a design doc, a timeline with milestones, weekly status with risks, and early notice to dependent teams.

**6. Finish**: decommission the old path, clean up flags and docs, and write a short retrospective.

Example (adapt): 'I led our MySQL 5.7 to 8.0 upgrade at [Company]: found [3] queries broken by changed defaults in a replica test, fixed them, switched over in a [10-minute] window with zero data issues.'"
""", A, ["migration", "project-leadership", "planning"], False))

SOURCES = [
    ("Malte Ubl: Design Docs at Google", "https://www.industrialempathy.com/posts/design-docs-at-google/"),
    ("Google SRE Book: Postmortem Culture, Learning from Failure", "https://sre.google/sre-book/postmortem-culture/"),
    ("Google SRE Book: Managing Incidents", "https://sre.google/sre-book/managing-incidents/"),
    ("StaffEng (Will Larson): Guides", "https://staffeng.com/guides/"),
    ("StaffEng: Work on what matters", "https://staffeng.com/guides/work-on-what-matters/"),
    ("StaffEng: Create space for others", "https://staffeng.com/guides/create-space-for-others/"),
    ("The Pragmatic Engineer: What is a senior software engineer at Wise and Amazon?", "https://blog.pragmaticengineer.com/what-is-a-senior-software-engineer-at-wise-and-amazon/"),
    ("The Pragmatic Engineer: What is a senior engineer at scaleups?", "https://newsletter.pragmaticengineer.com/p/what-is-a-senior-software-engineer-at-scaleups"),
    ("Conventional Comments", "https://conventionalcomments.org/"),
    ("Michael Nygard: Documenting Architecture Decisions (ADRs)", "https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions"),
    ("Amazon 2015 shareholder letter (one-way vs two-way door decisions)", "https://s2.q4cdn.com/299287126/files/doc_financials/annual/2015-Letter-to-Shareholders.PDF"),
]


def subject():
    return build("senior-leadership", "Senior Engineer Skills: Ownership, Design Docs & Leadership", 19, "🧭",
                 "The non-coding skills senior interviews probe: ownership, design docs, estimation, trade-offs, incidents, stakeholder communication, the project deep dive and model answers to senior behavioral questions.",
                 "lead", NOTES, QA, SOURCES)


if __name__ == "__main__":
    report(subject())
