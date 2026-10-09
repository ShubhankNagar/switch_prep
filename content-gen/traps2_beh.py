from traps2_common import T

A = "behavioral"

TRAPS = [
    T("trap-behavioral-we-instead-of-i", A, "Saying \"we\" so the interviewer can't see you", "Basic", "Very common",
      """"Tell me about the most challenging project you worked on."

Candidate: "**We** were migrating the claims module to microservices. **We** decided to use Kafka, **we** built the retry flow, and **our team** cut latency in half..."

The interviewer follows up: "What did *you* specifically do?\"""",
      "Saying \"we\" shows I'm a team player, and claiming individual credit sounds arrogant.",
      """In Indian service companies, work is assigned to teams and credit is collective, so "we" feels humble and safe. But the interviewer is hiring **you**, not your team. Every "we" forces them to spend follow-up questions extracting your role, and if they can't find it, they assume it was small. At SDE-2 and senior level, the rubric looks for **your decisions, trade-offs and influence**, which "we" hides completely.""",
      """Use **"we" for context and "I" for actions**. Name exactly what you owned, decided and influenced:

- **Scope**: "The team of six owned the migration; I owned the payment-reconciliation service end to end."
- **Decisions**: "I proposed an outbox table instead of publishing to Kafka directly, because we were losing events on pod restarts."
- **Influence**: "I wrote the design doc, got the architect's sign-off, and paired with two juniors on the consumer."
- **Result you can attribute**: "Lost events went from roughly 40 a week to zero; reconciliation tickets dropped by 70%."

Don't overcorrect by claiming the whole team's work: interviewers probe ("how did the Kafka cluster get provisioned?"), and being precise about boundaries builds trust. A quick self-test for every story: if someone else had done your part, what would have been different?""",
      "Before each story, write down three sentences that start with \"I decided\", \"I built\" or \"I convinced\"; if you can't, choose another story.",
      fix="""```text
Weak : "We migrated the module and improved performance."
Strong: "The team of 6 migrated claims to microservices. I owned reconciliation:
         I found events were lost on pod restarts, proposed an outbox + poller,
         wrote the design doc, implemented it, and added a lag alert.
         Lost events: ~40/week -> 0; manual reconciliation tickets down ~70%."
```""",
      askedAt=["Amazon", "Flipkart", "Walmart", "Atlassian"]),

    T("trap-behavioral-blaming-current-company", A, "\"Why are you leaving?\" turned into a complaint", "Basic", "Very common",
      """"Why do you want to leave your current company?"

Candidate: "Honestly, it's a service company: no good work, my manager doesn't value me, the salary is low and there's no learning.\"""",
      "Be brutally honest about everything wrong with the current job; interviewers appreciate honesty.",
      """The frustrations are often real, and candidates believe that venting them counts as honesty. Interviewers hear something else: **will this person talk about us like this in two years?** Complaints also put the focus on what you are running *from*, when the question is a chance to show what you are moving *towards*. Salary as the headline reason invites the follow-up "so you'd leave us for more money too?\"""",
      """Answer with **pull, not push**, in 30-45 seconds:

1. **Appreciate what you gained**: "I learned to ship production Spring Boot services and handle client escalations."
2. **State the gap neutrally, as a fact about the work rather than a complaint about people**: "Requirements are fixed by the client, so I rarely own a product decision or see how users react after release."
3. **What you want next, specifically**: owning a product area end to end, working at a scale where design choices matter, and measuring the impact of your own changes.
4. **Why this company fits**: one concrete link (their payments scale, their engineering blog post, the team's domain).

Never criticise your manager, team or employer by name, even if asked directly. Facts like "service model" or "fixed client scope" are fine; judgements like "useless" or "no good work" are not. If compensation matters, address it in the salary conversation, not as your reason for leaving.""",
      "Rehearse the answer until it takes under 45 seconds and contains zero negative adjectives about people.",
      fix="""```text
"In two years at <company> I built and supported Spring Boot services for a large insurance client and
handled production issues directly with the client. In the service model the client fixes the scope,
so I rarely own product decisions or see metrics after release. I want to own a product area end to end
and work at a scale where design trade-offs really matter. Your payments platform team does exactly
that, and the problems in your engineering blog on idempotent retries are ones I've started solving myself."
```""",
      askedAt=["Amazon", "Flipkart", "Swiggy", "Razorpay"]),

    T("trap-behavioral-no-measurable-result", A, "Stories with no structure and no measurable result", "Intermediate", "Very common",
      """"Tell me about a time you improved the performance of a system."

The candidate spends three minutes on background (client, team, tech stack), one minute on what was done, and ends with: "...and after that it was working fine and the client was happy.\"""",
      "Explaining the background in depth shows understanding, and \"the client was happy\" is a good enough result.",
      """Candidates think context makes the story understandable, so the Situation grows until it eats the answer. Service-company work rarely tracks metrics, so people assume they have no numbers and end vaguely. But a story without an outcome sounds like a story without impact, and interviewers score **actions and results**. Rambling also burns the time the interviewer had planned for follow-up questions, which is where they would have found your best material.""",
      """Use **STAR with deliberate proportions**: Situation + Task about 20% (two or three sentences), **Action about 60%**, **Result about 20%**. Aim for about two minutes, then let the interviewer dig in.

Make the result **measurable**:
- Before and after numbers: "p95 latency 1.8 s → 350 ms", "batch job 4 h → 40 min", "incidents 6/month → 1".
- Business translation: hours saved, cost reduced, SLA met, users unblocked.
- If you lack exact numbers, give an honest estimate and say how you know: "from the Grafana dashboard, roughly 60% fewer timeouts". Never invent precision.
- End with **what you learned or changed afterwards** (a checklist, an alert, a new standard).

Prepare 6-8 stories in a story bank and write down each one's numbers now, while you still have access to the dashboards and tickets at your current job.""",
      "Practise with a timer: if the situation part goes past 30 seconds, cut it.",
      fix="""```text
S (2 lines): Claims search API, p95 1.8 s, timing out for 3k agents during peak hours.
T (1 line) : I was asked to bring p95 under 500 ms without new hardware.
A (core)   : Profiled with slow-query log -> two full scans + N+1 in JPA.
             Added a composite index, replaced N+1 with a fetch join, cached reference data (Caffeine, 10 min).
             Load-tested with JMeter at 2x peak before release; added a p95 alert.
R (numbers): p95 1.8 s -> 350 ms, timeouts ~0, DB CPU 85% -> 40%. Now I check query plans in code review.
```""",
      askedAt=["Amazon", "Google", "Uber", "Atlassian"]),

    T("trap-behavioral-fake-weakness", A, "The fake weakness (\"I'm a perfectionist\")", "Basic", "Very common",
      """"What is your biggest weakness?"

Candidate: "I'm a perfectionist. I work too hard and sometimes forget to take breaks.\"""",
      "Choose a weakness that is secretly a strength, so it can't hurt you.",
      """Candidates treat it as a trick question to survive rather than as a test of **self-awareness and growth**. Every interviewer has heard "perfectionist" hundreds of times, and it signals either low self-awareness or evasiveness, which is worse than an honest flaw. The opposite mistake also happens: naming a weakness that is a **core requirement** of the role ("I'm not good with databases" for a backend role).""",
      """Pick a **real, non-fatal** weakness, show **specific actions** you are taking, and give **evidence of progress**:

1. **Real but not core**: speaking up in large design discussions, over-committing on estimates, going deep before checking direction, delegating less than you should.
2. **Concrete example** of it costing something: "I stayed quiet in a design review even though I suspected the retry logic would double-post; it did."
3. **Actions**: "Now I write a one-page note before design meetings and share it in advance; I ask one question in every review."
4. **Evidence**: "Last quarter my proposal to use an outbox was adopted, and my manager mentioned it in my review."

Keep it under a minute, and say it calmly. Interviewers are checking whether you can look at yourself honestly, which is the same skill they need for incident retrospectives and feedback.""",
      "Choose a weakness you are actively fixing, so the answer ends on progress rather than confession.",
      fix="""```text
"I tend to go deep into implementation before validating the direction. On a reporting feature I spent
three days optimising a query before learning the client wanted a different report. Now I share a short
approach note or a rough prototype within the first day and confirm scope before optimising. On my last
two features that caught a requirement mismatch early, once saving about a week."
```""",
      askedAt=["Infosys", "Amazon", "Deloitte", "Walmart"]),

    T("trap-behavioral-failure-story", A, "No real failure story (or a disguised humblebrag)", "Intermediate", "Very common",
      """"Tell me about a time you made a mistake or failed."

Candidate A: "I can't think of a major failure."
Candidate B: "My failure was that I worked so hard on the release that I didn't delegate enough."
Candidate C: "The release failed because QA missed a bug and the client changed requirements.\"""",
      "Avoid admitting real mistakes; choose something minor, or explain why it wasn't really your fault.",
      """Admitting a mistake in an interview feels risky, so people dodge, humblebrag or shift blame. Interviewers read all three as **low ownership**: either you don't notice your mistakes, or you won't own them. Amazon-style rubrics ("Ownership", "Earn Trust") and senior rubrics explicitly look for how you **respond** to failure. A real story, well handled, scores higher than a perfect record nobody believes.""",
      """Choose a **genuine mistake with real but recoverable impact** where **you** were the cause, then spend most of the time on the response:

1. **What happened**, owned plainly: "I ran a schema migration during business hours that locked the orders table for four minutes."
2. **Immediate response**: how you detected it, mitigated it and communicated (rolled back, informed the on-call engineer and the client).
3. **Root cause**, honestly: "I tested on a small dataset and didn't check the lock behaviour of `ALTER TABLE` on 20M rows."
4. **Systemic fix**, not just "I'll be careful": an online schema-change tool, a migration checklist, production-like data in staging, a review rule.
5. **Evidence it stuck**: "Twelve migrations since, no locking incidents; the checklist is now the team standard."

Avoid failures that are catastrophic, ethical, or that you would obviously repeat. Keep blame of others out of it, even if they contributed.""",
      "Spend 20% on the mistake and 80% on detection, mitigation and the systemic fix; that ratio reads as ownership.",
      fix="""```text
Mistake : ran ALTER TABLE on a 20M-row table at 11 am -> orders table locked ~4 min, checkout errors
Response: spotted the error spike in 2 min, killed the migration, informed on-call + client within 10 min
Cause   : tested only on a tiny dataset; didn't know the ALTER needed a table copy and lock
Fix     : moved to gh-ost/pt-online-schema-change, off-peak window, migration checklist in PR template
Proof   : 12 migrations since, zero locking incidents; checklist adopted by two other teams
```""",
      askedAt=["Amazon", "Microsoft", "Uber", "Flipkart"]),

    T("trap-behavioral-project-tech-dump", A, "\"Walk me through your project\" answered with a tech-stack list", "Intermediate", "Very common",
      """"Walk me through your current project."

Candidate: "It's built with Spring Boot, Angular, MySQL, Kafka, Docker and Jenkins. It has modules for login, dashboard, reports and user management. I worked on the APIs and the UI.\"""",
      "Listing the tech stack and modules shows the breadth of my experience.",
      """The tech stack is the easiest thing to recall, and resumes are written that way, so candidates repeat their resume. But the interviewer can read your resume. They want to know **what problem the system solves, at what scale, what you owned and what was hard**. This question also sets up the 45-minute project deep dive common in 2026 senior loops: a shallow opening gives them nothing to probe, or invites probes you can't answer.""",
      """Use a two-minute structure that **invites the deep dive you want**:

1. **Business problem and users**: "An insurance claims platform used by about 3,000 agents across 400 branches; about 50k claims a day."
2. **Architecture in one breath**: "Angular front end, six Spring Boot services on MySQL, Kafka between claims and payments."
3. **Your ownership**: "I own the claims-intake and document-validation services."
4. **One hard problem with a trade-off**: "Duplicate claims from retries. I added idempotency keys and a unique constraint instead of a distributed lock, because..."
5. **Measured result**: "Duplicates dropped from about 200 a week to near zero."

Then prepare for the probes: why this design, what fails at 10x load, what you would change, how you debugged the worst incident, and how a request flows end to end. Service-company engineers should describe the **client's product** as the product. That is real production experience.""",
      "End your two-minute walkthrough on the hard problem you solved best, so the deep dive goes where you are strongest.",
      fix="""```text
"Claims platform for a large insurer: ~3k agents, ~50k claims/day, peak at month end.
Angular SPA -> API gateway -> 6 Spring Boot services on MySQL; Kafka from claims to payments.
I own claims intake + document validation.
Hardest problem: duplicate claims when agents retried on slow networks. I added an idempotency key
per submission + unique constraint, and made the Kafka consumer idempotent.
Result: duplicates ~200/week -> ~0, and month-end support tickets down ~30%.
Happy to go deeper into the idempotency design or the month-end scaling."
```""",
      askedAt=["Flipkart", "PhonePe", "Swiggy", "Walmart"]),

    T("trap-behavioral-conflict-villain", A, "Conflict stories with a villain (or no conflict at all)", "Intermediate", "Common",
      """"Tell me about a time you disagreed with your manager or a senior engineer."

Candidate: "My lead wanted to use a shared database between two services, which was obviously wrong. I told him it was a bad idea and escalated to the architect, who agreed with me. In the end we did it my way.\"""",
      "Show that you were right and won the argument, or say you never have conflicts.",
      """Candidates think the question is about **who was right**, so they tell a story where they win and the other person looks foolish. Others avoid conflict entirely ("I always agree with my team"), which reads as having no opinions or no backbone. The interviewer is actually evaluating **how** you disagree: respect, data, listening, and whether you can commit to a decision you argued against. Escalating as the first move is a red flag at any level.""",
      """A strong disagreement story shows:

1. **A real disagreement of substance** (design, priorities, quality vs deadline), not a personality clash.
2. **Understanding their view first**: "He wanted the shared database to hit a two-week deadline without a sync mechanism. That was a fair concern."
3. **Data over opinion**: a small prototype, a benchmark, a written comparison of risks, a proposal for a middle path.
4. **The right forum**: a one-to-one conversation first, then a design review if needed, and escalation only as a last resort, done transparently.
5. **Commitment either way**: if overruled, you **disagree and commit** and help it succeed, perhaps with safeguards you suggested. If persuaded, say so.
6. **Relationship and outcome**: what happened, and how you work with that person now.

A story where you were **partly wrong**, or where the compromise beat both original positions, is often the most convincing.""",
      "Describe the other person's position generously; interviewers score how you treat people you disagree with.",
      fix="""```text
Disagreement: lead wanted a shared DB between orders and billing to hit a deadline
Their view  : no time to build events; shared DB = 2 weeks faster
My concern  : schema coupling; billing changes would break orders deploys
What I did  : 1:1 first; wrote a half-page risk note; proposed a middle path: shared DB now,
              but billing reads only through a view + we add an outbox in the next sprint
Outcome     : lead agreed; deadline met; outbox shipped 3 weeks later, and the view
              prevented two breaking changes in the meantime. We still review designs together.
```""",
      askedAt=["Amazon", "Atlassian", "Microsoft", "Swiggy"]),

    T("trap-behavioral-ctc-anchoring", A, "Anchoring salary to current CTC too early (India)", "Intermediate", "Very common",
      """First recruiter call, before any technical round:

"What is your current CTC, and what are you expecting?"

Candidate: "Current is 6.5 LPA, I'm expecting a 30% hike.\"""",
      "Quote your current CTC plus a standard percentage hike, because that's how hikes work.",
      """Inside service companies, raises are a percentage of current pay, so candidates carry that model into the switch. Product companies budget by **level and role**, not by your old salary. Quoting "current + 30%" can pull you to the bottom of a band, or below it, before anyone has seen how good you are. Candidates also don't prepare, so they give a number on the spot, unaware of how fixed, variable, stock and bonus components change the real figure.""",
      """In India, current CTC is often asked and sometimes verified with payslips. **Never lie about it**. But anchor your **expectation** to the **role's market range**, not to a percentage:

- **Research before the call**: levels.fyi, AmbitionBox, Glassdoor, LinkedIn and peers at the target company, for the **level** you are interviewing for.
- **Defer if you can**: "I'd like to understand the role and level first; I'm confident we'll find a fair number if it's a match." Then ask for the band.
- If pressed, give a **researched range** whose bottom is a number you would happily accept, and say it is based on the role and market.
- **Compare offers on fixed pay**: separate fixed, variable (often not fully paid), ESOPs or RSUs (vesting schedule), joining bonus (clawback terms) and notice-period buyout.
- Use **competing offers** honestly as leverage, and negotiate after the offer, politely.

Service-to-product switches often land well above a standard 30% when the level is right, so don't cap yourself on the first call.""",
      "Prepare the deferral sentence and a researched range before the first recruiter call, and practise saying both out loud.",
      fix="""```text
Recruiter: "Current and expected CTC?"
You      : "Current is 6.5 LPA fixed, 7.1 with variable. For expected, I'd like to understand the level
            and responsibilities first. Could you share the band for this role?"
If pushed: "Based on my research for SDE-2 backend roles in Bangalore, I'm looking at 18-22 LPA fixed,
            depending on the overall structure. I'm flexible for the right role."
Always   : ask for the breakdown (fixed / variable / ESOP vesting / joining bonus clawback / notice buyout)
```""",
      askedAt=["Flipkart", "Swiggy", "PhonePe", "Walmart"]),
]

CHECKS = []
