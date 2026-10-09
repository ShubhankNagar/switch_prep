from cs_common import build, B, I, A

notes = [
("The STAR Method & Building Your Story Bank", r"""
Behavioral rounds ("Tell me about a time when…") test **how you actually behave**: ownership, collaboration, handling conflict and pressure, learning. Product companies (Amazon, Flipkart, Swiggy, Razorpay, PhonePe, Atlassian, Uber) take these seriously — a weak behavioral round can reject a strong coder, and for SDE-2 it also influences your **level**.

### STAR
| Step | What to say | Share of answer |
|---|---|---|
| **S – Situation** | Context: project, team, timeline, why it mattered | ~10-15% |
| **T – Task** | Your specific responsibility or the problem to solve | ~10% |
| **A – Action** | What **you** did, step by step, and why (decisions, trade-offs) | **~60%** |
| **R – Result** | Measurable outcome + what you learned | ~15-20% |

Variants: **STAR-L** (add Learning), **CAR** (Context-Action-Result). Keep a single answer to **about 2 minutes**; the interviewer will drill down with follow-ups.

### Rules that make STAR work
1. **Say "I", not "we".** "We migrated the service" hides your contribution. Use "I proposed…", "I wrote…", "I convinced…". Credit the team briefly, then focus on you.
2. **Be specific.** Names of technologies, numbers, dates: "API p95 latency dropped from 1.8 s to 350 ms", "saved ~6 hours of manual work per week", "reduced production incidents from 4/month to 1".
3. **Explain your reasoning.** Interviewers care about *why* you chose an approach and what alternatives you rejected.
4. **Show reflection.** End with what you learned or would do differently. For failure stories this is mandatory.
5. **Real stories only.** Follow-ups (Why that approach? Who disagreed? What was the metric?) expose made-up stories immediately. You may polish and simplify, never invent.
6. **Don't badmouth** your manager, team, client or company — even when the story involves conflict.

### Build a story bank (do this in week 1)
Write **8-10 stories** from your 2 years, each in STAR bullet form with numbers. Each story can be reused for several questions. Cover these themes:

| Theme | Example story from a Spring Boot/Angular project |
|---|---|
| Technical challenge / complex bug | Production memory leak or slow query you diagnosed |
| Ownership beyond your role | Automated a manual deployment/report nobody asked you to |
| Performance improvement | Added indexes/caching/pagination; reduced API latency |
| Conflict / disagreement | Disagreed with a senior on design; resolved with data |
| Tight deadline / pressure | Delivered a client release with a reduced scope plan |
| Failure / mistake | A bug you shipped to production, how you fixed and prevented it |
| Learning something new fast | Picked up Angular signals / Kafka / Docker for a task |
| Helping others / mentoring | Onboarded a new joiner, wrote documentation |
| Customer focus | Talked to the client/business team to fix the real problem |
| Going above and beyond / innovation | Built an internal tool, proposed a process improvement |

Template to fill for each:
```
Title: Order search API latency fix
S: Client's order search page timing out (8-10 s) during month-end, 2M rows in MySQL.
T: I was asked to investigate within the sprint.
A: Used slow query log + EXPLAIN -> full table scan due to LIKE '%x%' and missing composite index;
   added (customer_id, status, created_at) index, moved free-text to prefix search, added
   server-side pagination in Spring Data + Angular table, cached static lookups.
R: p95 from 9 s to 400 ms; month-end tickets dropped to zero; documented the approach for the team.
Learning: always check EXPLAIN before adding hardware; added query review to our PR checklist.
Questions it answers: technical challenge, performance, ownership, customer impact.
```

### Practise out loud
Record yourself on your phone; 2 minutes per answer; cut filler. Do at least two mock behavioral rounds with a friend before real interviews. Rehearse the first 20 seconds of each story — a crisp start makes the rest flow.
"""),

("Presenting Service-Company Projects So They Sound Impactful", r"""
Product-company interviewers sometimes assume service-company work means "just tickets". Your job is to show **engineering depth, ownership and impact** — without exaggerating.

### Common mistakes
- Describing the **client's business** for 3 minutes instead of your work.
- "We developed a module…" — no clarity on your role.
- Listing technologies without problems: "I used Spring Boot, Angular, MySQL, Jenkins."
- No numbers, no outcomes.
- Saying "I just did what the client asked" or "I only fixed bugs".

### A 4-layer framework to describe any project
1. **One-line context (business + scale):** "An order management platform for a US-based retail client — about 50k orders a day, used by 300 store operators."
2. **Architecture in 2-3 sentences:** "Angular 15 front end, Spring Boot microservices (order, inventory, notification) on Java 17, MySQL, RabbitMQ for async events, deployed on AWS EKS via Jenkins."
3. **Your ownership:** "I own the order service and the Angular order dashboard — features end to end, from API design to UI, plus production support for my modules."
4. **2-3 highlights with impact (STAR-mini):** the hardest problem, a performance win, a process improvement.

### Turn tasks into impact — rewrite examples
| Weak | Strong |
|---|---|
| "Worked on REST APIs" | "Designed and built 12 REST endpoints for returns processing; introduced DTO validation and global exception handling that cut client-reported 500 errors by ~70%." |
| "Fixed bugs" | "Was the go-to person for the order module's production issues; root-caused a duplicate-order bug to a missing idempotency check on retries and fixed it with an idempotency key + unique constraint." |
| "Made UI screens in Angular" | "Built the order dashboard in Angular; moved the 2,000-row grid to OnPush + trackBy + server-side pagination, which made filtering instant instead of a 3-second lag." |
| "Wrote unit tests" | "Raised coverage of the pricing module from 35% to 80% with JUnit 5/Mockito, catching two rounding bugs before release." |
| "Did deployments" | "Automated the manual release checklist into a Jenkins pipeline stage, reducing release time from 2 hours to 20 minutes." |

### Finding numbers when you don't have dashboards
Estimate honestly and say so: "roughly", "about". Sources: JIRA ticket counts, release notes, log timestamps, before/after timings you measured locally, number of users/records, hours saved per week. Even "reduced a report from ~15 minutes to under 1 minute" is concrete.

### Show product thinking
Product companies love engineers who think about **users and business**:
- "I noticed operators were exporting to Excel to filter, so I proposed and built saved filters."
- "I pushed back on a requirement that would have doubled API calls and suggested a batch endpoint instead."

### Prepare deep-dive answers for your main project
Expect: *Draw the architecture. How does a request flow? How is authentication done? Biggest table size? How do you deploy? How do you monitor? What would you redesign? What happens if the DB goes down?* Know your project better than anything else in this site — it is the one topic you are guaranteed to be asked.

### Things to avoid saying
- Client/company confidential details (names of internal systems, revenue numbers). Use generic descriptions: "a leading US retailer".
- Negativity: "the code was garbage", "my team is useless".
- Exaggeration you can't defend: claiming you "designed the microservices architecture" if you joined after it existed. Say "I extended/improved…" instead.

### Your 60-second project pitch (practise until smooth)
"For the last two years I've been working on an order-management platform for a large retail client. It's Angular on the front end with Spring Boot microservices and MySQL on AWS. I own the order service and the Angular dashboard end to end. Two things I'm proud of: I cut the order search time from about 9 seconds to under half a second by fixing indexing and adding pagination, and I fixed a duplicate-order issue in payments by adding idempotency keys. I also automated our release checklist into Jenkins, saving about two hours per release."
"""),

("Tell Me About Yourself, Why Switch & Why This Company", r"""
These three questions appear in almost every round (recruiter screen, hiring manager, HR). Script them, practise them, but deliver them conversationally.

### "Tell me about yourself" — Present → Past → Future (60-90 seconds)
1. **Present:** current role, tech stack, what you own.
2. **Past:** education/joining, key achievements (1-2 with numbers).
3. **Future:** what you're looking for and why it fits this role.

**Example (Raj):**
> "I'm a full-stack Java developer with about two years of experience at [Company], where I work on an order-management platform for a large retail client. My stack is Spring Boot microservices, Angular and MySQL, deployed on AWS. I own the order service and the operator dashboard end to end.
> A couple of highlights: I brought the order search API from roughly 9 seconds down to under 500 ms through query and index optimisation and pagination, and I fixed a duplicate-payment issue by introducing idempotency keys.
> Alongside work I've been strengthening my DSA and system design, and I'm now looking for a product-company role where I can own features end to end, work at larger scale, and see the direct impact on users — which is why this SDE role on your [payments/merchant] team interested me."

Don't: recite your resume line by line, talk about hobbies first, or go beyond 2 minutes.

### "Why do you want to leave your current company?" / "Why switch?"
Principles: be **positive and forward-looking**; focus on what you want to **move towards**, not what you're running away from. Never criticise your employer, salary, manager or client.

Good themes for a service → product move:
- **Ownership:** want to own a product long-term, not just client deliverables.
- **Scale and engineering depth:** more users, distributed systems, performance, reliability.
- **Product thinking:** be closer to users and business metrics.
- **Growth:** learning from strong engineers, engineering culture (code reviews, design docs, on-call).

**Example:**
> "I've learned a lot in my current role — I got strong fundamentals in Spring Boot and Angular and handled production systems. But in a services setup, the roadmap and many technical decisions sit with the client, and projects change every year or two. I want to work on a product I can own long-term, where I'm involved from design to monitoring metrics, at a larger scale. That's what draws me to product companies like yours."

**If asked "Is it about money?":** "Compensation matters, and I expect it to be aligned to the market for this role, but the primary reason is the kind of work and ownership. Money alone wouldn't make me switch."

### "Why our company?"
Research for 20 minutes before every interview: the product (use it!), engineering blog, recent news/funding, tech stack (StackShare, job descriptions), Glassdoor/AmbitionBox reviews. Then connect **their product + their engineering challenges + your skills/interests**.
> "I use [product] for [use case] and I'm impressed by how [feature] works. I read your engineering blog post on [topic, e.g. how you scaled your payment reconciliation]; that's exactly the kind of high-scale backend problem I want to work on. My Spring Boot and MySQL experience, especially around performance and idempotent payment flows, maps directly to this role."

### "Why should we hire you?"
Three points: **relevant skills** (Java/Spring/Angular full-stack), **evidence of impact/ownership** (one achievement), **attitude** (learning fast, owning problems).

### "Where do you see yourself in 5 years?"
Show ambition aligned with the company, not "I'll start my own business" or "in your chair":
> "I'd like to grow into a senior engineer who owns a significant part of the system — making design decisions, mentoring juniors, and being someone the team relies on for production-critical areas. I'm also interested in going deeper on distributed systems."

### "Why are you looking for a change after only 2 years?"
"Two years gave me a solid foundation and I've delivered real outcomes. I now feel ready for a role with more ownership and scale, and I'd rather make that move now to grow faster in the right environment." If you've had a short stint elsewhere, give a brief, honest, non-negative reason.

### Career gap or bench time
Be honest and show what you did: courses, side projects, certifications (e.g. "I built a Spring Boot + Angular expense tracker, deployed on AWS").
"""),

("Salary Discussion & Negotiation (India Context)", r"""
Compensation comes up at the **recruiter screen** (current/expected CTC, notice period), **after the final round** (offer), and with **counter-offers**. Preparation here is worth lakhs per year.

### Know the Indian CTC vocabulary
- **CTC (Cost to Company)** = Fixed + Variable/Bonus + Employer PF + Gratuity + Insurance + Joining bonus + ESOPs/RSUs (some companies inflate CTC by including everything).
- **Fixed pay** – the part you get monthly regardless; **compare offers on fixed + realistic variable**, not headline CTC.
- **Variable/performance bonus** – 5-20%; ask how much is typically paid out.
- **Joining/sign-on bonus** – one-time; often has a clawback if you leave within 12 months.
- **ESOPs / RSUs** – usually vest over 4 years with a 1-year cliff; startup ESOP value is uncertain.
- **In-hand monthly** ≈ (Fixed − employee PF − professional tax − income tax) / 12. Use an online calculator under the new tax regime.
- **Notice period** – service companies commonly have 60-90 days; product companies prefer ≤ 30-60 days.

### Market reality for your switch (2-3 YOE, service → product)
- Product companies in India pay roughly **12-25 LPA** for SDE-1/early SDE-2 with 2-3 years depending on tier; top product companies and well-funded startups go higher. Check AmbitionBox, Glassdoor, levels.fyi (India), LinkedIn salary insights, Leetcode discuss compensation threads for recent data.
- Hikes of **40-100%** on current fixed are common for service → product switches. Some companies anchor to "current CTC + 30-50%"; a strong interview performance and a competing offer move this.
- Your target ~15 LPA is realistic for many mid-tier product companies and startups; aim for a range like **15-18 LPA** to leave room.

### Answering "What is your current CTC?"
Be **truthful** — companies verify via payslips, Form 16, and background checks; lying can get an offer revoked. Give the full breakdown: "My current CTC is X LPA: Y fixed, Z variable." If your current pay is low, shift focus to the role: "My current CTC is X, which reflects service-company pay bands. I'm evaluating this role based on market value for the skills and scope involved."

### Answering "What is your expected CTC?"
Options, in order of preference:
1. **Deflect early** (recruiter screen): "I'd like to understand the role and level first. I'm sure if I'm the right fit, we'll arrive at a fair number. Could you share the budgeted range for this role?"
2. **Give a researched range** if pressed, with the **bottom of your range at or slightly above your real target**: "Based on my research for SDE roles with 2-3 years at companies like yours, and my full-stack experience, I'm looking at 16-19 LPA fixed." Don't give a range whose lower end you'd be unhappy with — they'll pick the lower end.
3. Never say "whatever is your standard" or "any hike is fine".

### Negotiating the offer
1. **Get the offer in writing** with a full breakup before negotiating.
2. **Express enthusiasm first**: "I'm excited about the role and the team."
3. **Ask, with justification**: "Based on market data and my interview feedback, I was expecting fixed pay around 17 LPA. Is there flexibility on the fixed component?"
4. **Use competing offers honestly** — having 2-3 offers is the strongest lever. "I have another offer at X fixed; I'd prefer to join you — can you match or come closer?" Be ready to share the offer letter if asked; never fabricate one.
5. **Negotiate components** if base is capped: joining bonus, notice-period buyout reimbursement, relocation, ESOPs, earlier appraisal cycle, level (SDE-2 vs SDE-1).
6. **Be polite and concise**; one or two rounds of negotiation is normal and expected. Get the final revised offer in writing.

### Notice period
- State it clearly: "My notice period is 90 days, but I can try for an early release; I can also explore a buyout if the company supports it."
- Many product companies want joiners within 30-60 days — **resigning early** (once you have strong interview pipelines or an offer in hand) is common in India, but understand the risk. Ask your HR about **early release** (adjusting leave, completing handover) and **buyout** (paying the remaining notice salary — sometimes reimbursed by the new company).

### Counter-offers from your current employer
Service companies often counter with a hike when you resign. Consider:
- Why were you leaving? Money rarely fixes lack of ownership/growth — the original reasons usually remain.
- Counter-offers can mark you as a "flight risk"; future appraisals may be lower.
- Decline gracefully: "Thank you, but I've decided to move on for the kind of work I want to do."

### Avoid
Lying about CTC or offers, negotiating before you have an offer, accepting on the spot (ask for 24-48 hours), and comparing headline CTCs that include one-time bonuses or illiquid ESOPs.
"""),

("Amazon Leadership Principles & Behavioral Themes", r"""
Amazon builds its entire interview loop around its **Leadership Principles (LPs)**: each interviewer is assigned 2-3 LPs and asks behavioral questions mapped to them, alongside coding. A "**Bar Raiser**" from another team ensures the hire raises the bar. Even non-Amazon companies (Flipkart, Swiggy, Walmart, Atlassian with its values) ask very similar questions, so preparing LP stories prepares you for everyone.

### The 16 Leadership Principles (in brief, own words)
1. **Customer Obsession** – start from the customer and work backwards; earn and keep trust.
2. **Ownership** – think long term, act on behalf of the whole company, never say "that's not my job".
3. **Invent and Simplify** – innovate and find simpler ways; accept being misunderstood for a while.
4. **Are Right, A Lot** – good judgment and instincts; seek diverse perspectives and disconfirm your beliefs.
5. **Learn and Be Curious** – keep learning, explore new possibilities.
6. **Hire and Develop the Best** – raise the performance bar, mentor and coach others.
7. **Insist on the Highest Standards** – high bar for quality; fix defects so they stay fixed.
8. **Think Big** – bold direction that inspires results.
9. **Bias for Action** – speed matters; many decisions are reversible and don't need extensive study; take calculated risks.
10. **Frugality** – accomplish more with less; constraints breed resourcefulness.
11. **Earn Trust** – listen, speak candidly, treat others respectfully, admit mistakes.
12. **Dive Deep** – stay connected to details, audit frequently, be skeptical when metrics and anecdotes differ.
13. **Have Backbone; Disagree and Commit** – respectfully challenge decisions you disagree with; once decided, commit fully.
14. **Deliver Results** – focus on key inputs, deliver with quality and on time despite setbacks.
15. **Strive to be Earth's Best Employer** – create a safe, productive, empathetic work environment.
16. **Success and Scale Bring Broad Responsibility** – be humble and thoughtful about secondary effects of your actions.

For an SDE-1/SDE-2, the most frequently probed are **Customer Obsession, Ownership, Dive Deep, Deliver Results, Bias for Action, Earn Trust, Have Backbone, Learn and Be Curious, Insist on the Highest Standards, Invent and Simplify**.

### Map your story bank to LPs
| LP | Typical question | Your story idea |
|---|---|---|
| Customer Obsession | Time you went beyond what the customer asked | Saved filters for store operators after watching them use Excel |
| Ownership | Took on something outside your responsibility | Fixed flaky CI pipeline nobody owned |
| Dive Deep | Solved a problem by digging into data/details | Root-caused intermittent duplicate orders via logs and DB timestamps |
| Deliver Results | Delivered despite obstacles | Release with key dev on leave; re-planned scope |
| Bias for Action | Made a decision without complete info | Hotfix during an outage with rollback plan |
| Have Backbone | Disagreed with a senior/manager | Pushed back on skipping DB migration testing, using data |
| Earn Trust | Mistake you made / tough feedback | Shipped a bug, owned it, wrote a post-mortem |
| Learn & Be Curious | Learned a new technology quickly | Learned Kafka/Docker for a task in a week |
| Insist on Highest Standards | Improved quality when others were OK with less | Added integration tests & PR checklist |
| Invent & Simplify | Simplified a complex process | Automated release checklist in Jenkins |

Prepare **two stories per key LP** (stories can overlap); Amazon interviewers may ask "Tell me another example" and avoid repeating a story across interviewers in the same loop.

### What Amazon interviewers listen for
- Data and metrics in results.
- **Your** individual actions and decisions.
- Trade-offs and judgment (what you chose not to do).
- Self-awareness in failure stories (what changed afterwards).
- Customer impact.

### Other companies' value frameworks
- **Flipkart / Walmart Global Tech** – ownership, customer-first, bias for action.
- **Atlassian** – "Open company, no BS", "Don't #@!% the customer", "Play, as a team", "Be the change you seek", "Build with heart and balance" — they run a dedicated **values interview**.
- **Google** – "Googleyness" (comfort with ambiguity, collaboration, humility).
- **Razorpay, PhonePe, Swiggy, Zomato** – hiring-manager rounds probe ownership, handling ambiguity, production incidents, and culture fit.
"""),

("Questions to Ask the Interviewer & Round Etiquette", r"""
"Do you have any questions for me?" is not a formality — it's a final signal of your curiosity and seriousness. **Always ask 2-3 thoughtful questions.** "No, I'm good" sounds disinterested.

### Good questions by interviewer type
**To an engineer (technical rounds):**
- "What does a typical week look like for an engineer on your team?"
- "What's the tech stack, and what are the biggest technical challenges you're facing right now?"
- "How does code review and testing work? What does the path from a PR to production look like?"
- "How are on-call and production incidents handled?"
- "What's something you've learned recently in this role?"

**To a hiring manager / engineering manager:**
- "What would success look like for this role in the first 3-6 months?"
- "What are the team's priorities for the next couple of quarters?"
- "How do you support engineers' growth — mentorship, promotions from SDE-1 to SDE-2?"
- "How are product decisions made — how much do engineers influence the roadmap?"
- "What qualities distinguish the best engineers on your team?"

**To HR / recruiter:**
- "What's the team I'd be joining and its location/hybrid policy?"
- "What are the next steps and timeline?"
- "Could you walk me through the compensation structure — fixed, variable, ESOPs, benefits?"
- "What is the appraisal cycle and when would I be eligible for my first review?"

**A great closing question:**
- "Based on our conversation, is there anything about my background that makes you hesitant? I'd love the chance to address it." (Use with a confident tone; it can surface and fix a concern.)

### Questions to avoid
- Things easily found on the website ("What does your company do?").
- Salary/leave questions in technical rounds — save them for HR.
- "Did I pass?" / "How did I do?" (puts the interviewer on the spot).
- Negative framing ("Is the work-life balance as bad as Glassdoor says?") — rephrase: "How does the team manage workload around big launches?"

### Etiquette for virtual interviews (most first rounds in India)
- Stable internet, laptop charged, headphones with mic, quiet room, neutral background, camera at eye level.
- Test Zoom/Google Meet/Teams and any coding platform (CoderPad, HackerRank, CodeSignal) beforehand. Keep a pen and paper.
- Join 3-5 minutes early. Keep your resume, notes on your projects and a glass of water nearby.
- **Think out loud** in coding rounds; clarify requirements before coding; discuss brute force → optimise; test with examples; state complexity.
- If you don't know something: say so honestly and reason about it ("I haven't used Kafka Streams, but I'd expect it to work like…"). Bluffing is worse than "I don't know".
- Be polite and positive with everyone, including the recruiter coordinating your interviews — feedback is shared.

### After the interview
- Send a short thank-you note to the recruiter (optional but nice): "Thanks for coordinating; I enjoyed discussing X with the team."
- Write down every question you were asked the same day — they repeat across companies and reveal your weak spots.
- Follow up politely after 5-7 days if there's no update.
- Handle rejection professionally; ask for feedback; many companies allow re-applying after 6 months.

### HR round red flags to avoid
- Inconsistent stories between your resume and what you say.
- Badmouthing previous employers.
- Unrealistic salary demands with no justification.
- Unclear notice period or saying you'll join earlier than possible.
- Not knowing anything about the company.

### Final checklist before each interview
1. Re-read the job description; map 3 requirements to your experience.
2. Review your 60-second pitch and top 5 stories.
3. Use their product/app for 10 minutes; read one engineering blog post.
4. Prepare 3 questions for the interviewer.
5. Have current CTC breakup, expected range and notice-period answer ready.
"""),
]

qa = [
("Tell me about yourself.", r"""
**Framework – Present → Past → Future (60-90 s):** current role and stack → 1-2 achievements with numbers → what you want next and why this role fits. Don't narrate your resume or start with school.

**Example:**
> "I'm a full-stack Java developer with two years at [Company], working on an order-management platform for a large retail client. I build Spring Boot microservices, Angular front ends and MySQL schemas, deployed on AWS, and I own the order service and operator dashboard end to end.
> Two highlights: I reduced the order search API from about 9 seconds to under 500 ms through indexing and pagination, and fixed a duplicate-payment issue by introducing idempotency keys.
> I've also been sharpening my DSA and system design. I'm now looking for a product role where I can own features long term at larger scale — which is why this SDE role on your team excites me."

Tailor the last line to each company.
""", B, ["introduction", "hr"], True),

("Why do you want to leave your current company?", r"""
**Framework:** acknowledge what you gained → state what you're looking for (ownership, scale, product impact, growth) → connect to this company. Stay positive; never criticise your employer, manager, client or pay.

**Example:**
> "My current company gave me a strong foundation: I've worked on production Spring Boot and Angular systems, handled releases and support, and learned to work directly with clients. But in a services model the roadmap and many technical decisions sit with the client, and projects change every year or two. I want to own a product long term, be involved from design to monitoring metrics after release, and work on systems at a larger scale. That's why I'm focusing on product companies like yours."

If they probe about money: "Compensation should be fair for the role, but it isn't the main driver — the kind of work and ownership is."
""", B, ["why-switch", "hr"], True),

("Why do you want to join our company?", r"""
**Framework:** Product (you've used/researched it) + Engineering (a challenge from their blog/JD) + You (skills that fit) + Growth (what you'll learn). Spend 20 minutes researching before every interview.

**Example (fintech company):**
> "I use your app for UPI payments and bill reminders, and it's one of the smoothest experiences I've had. I read your engineering blog post on how you handle payment idempotency and reconciliation at scale — that's exactly the kind of reliable, high-volume backend work I want to do. In my current project I've built idempotent payment flows and optimised MySQL-heavy APIs in Spring Boot, so I can contribute from day one, while learning from engineers who've solved these problems at a much bigger scale."

Avoid generic answers like "It's a great company with good culture" — they show no research.
""", B, ["why-company", "hr"], True),

("Tell me about the most challenging technical problem you solved.", r"""
**Framework (STAR):** choose a problem with real depth (performance, concurrency, production bug), explain your debugging steps and reasoning, quantify the result, share the learning.

**Example:**
> **S:** During month-end, the order search page for 300 store operators started timing out — 8-10 seconds on a 2M-row MySQL table.
> **T:** I was asked to find and fix the cause within the sprint without new infrastructure.
> **A:** I enabled the slow query log and ran EXPLAIN: a full table scan due to a `LIKE '%term%'` and no index on our filter columns. I added a composite index on (customer_id, status, created_at), changed free-text search to prefix matching after confirming with the business team, introduced server-side pagination with Spring Data `Pageable`, and made the Angular grid OnPush with trackBy.
> **R:** p95 dropped from ~9 s to ~400 ms, month-end timeout tickets went to zero. I documented an "EXPLAIN before merging" checklist the team still uses.
""", I, ["technical-challenge", "star"], True),

("Tell me about a time you made a mistake or failed.", r"""
**Framework:** pick a **real, moderate** mistake (not catastrophic, not a fake "I work too hard"). Own it without excuses → how you fixed it quickly → what you changed so it doesn't recur. The learning is the point.

**Example:**
> **S:** I shipped a change to our order export API that worked in testing.
> **T:** After release, a client's nightly job failed because I'd renamed a JSON field I assumed was only used by our Angular UI.
> **A:** As soon as the alert came, I owned it in the incident call, rolled back within 30 minutes, and then re-released with both old and new field names. I wrote a short post-mortem: the root cause was that we had no contract tests for external consumers.
> **R:** I added API contract tests and a "breaking change" checkbox in our PR template, and we started versioning endpoints (`/v2`). We haven't had a similar incident since. My lesson: treat every public API field as a contract and check consumers before changing it.
""", I, ["failure", "star", "earn-trust"], True),

("Tell me about a time you disagreed with your manager or a senior colleague.", r"""
**Framework:** show **respectful disagreement backed by data**, openness to their view, and **commitment** once decided (Disagree and Commit). The outcome can go either way; the process matters.

**Example:**
> **S:** Before a release, my tech lead wanted to skip testing a DB migration on a production-sized dataset to save a day.
> **T:** I believed the migration (adding a NOT NULL column with default on a 5M-row table) could lock the table.
> **A:** Instead of arguing in the stand-up, I ran it on a staging copy that evening and measured a 12-minute table lock. I shared the numbers privately with my lead and proposed an alternative: add the column as nullable, backfill in batches, then add the constraint. I also offered to do the extra work myself.
> **R:** He agreed; the release went out with zero downtime. He later asked me to review other migrations. I learned that data persuades better than opinions — and if he had still decided otherwise, I'd have committed and prepared a rollback plan.
""", I, ["conflict", "star", "backbone"], True),

("Describe a conflict with a teammate and how you resolved it.", r"""
**Framework:** neutral description (no blaming) → you initiated a 1:1 conversation → understood their perspective → found a solution focused on the shared goal → relationship and outcome improved.

**Example:**
> **S:** A front-end teammate and I kept clashing because my API changes often broke his Angular screens late in the sprint.
> **T:** It was causing rework and tension in stand-ups; I wanted to fix the process, not win the argument.
> **A:** I set up a 1:1 and asked how it looked from his side. He felt changes arrived without warning. We agreed to define API contracts first: I'd share request/response DTOs and an OpenAPI spec before implementing, and he'd build against a mock. I also added him as a reviewer on API PRs.
> **R:** Integration issues in the next three sprints dropped to almost none, and we started pairing on features end to end. I learned that most conflicts are process problems — talking early and directly solves them.
""", I, ["conflict", "teamwork", "star"], True),

("Tell me about a time you worked under a tight deadline.", r"""
**Framework:** show **prioritisation, communication and trade-offs**, not heroics ("worked 18 hours a day"). Mention how you protected quality.

**Example:**
> **S:** Two weeks before a client go-live, a teammate went on emergency leave, leaving the returns module half done.
> **T:** I had to finish my own features and take over his work without slipping the date.
> **A:** I listed remaining stories with the PM, split them into must-have and nice-to-have, and proposed shipping a basic returns flow (initiate + approve) while deferring bulk returns to the next release. I wrote integration tests first for the critical paths, paired with QA daily to shorten the feedback loop, and gave a short daily status to the client so there were no surprises.
> **R:** We went live on time with zero P1 bugs; bulk returns followed two weeks later. The client appreciated the transparency. Learning: negotiating scope early beats overtime.
""", I, ["deadline", "pressure", "deliver-results"], True),

("Tell me about a time you took ownership of something outside your role.", r"""
**Framework (Ownership):** you noticed a problem nobody owned → acted without being asked → result for the team/customer.

**Example:**
> **S:** Our release process was a 40-step manual checklist taking about two hours, done by whoever was free; steps were often missed and caused hotfixes.
> **T:** It wasn't assigned to anyone — I decided to fix it.
> **A:** I spent a few evenings converting the checklist into Jenkins pipeline stages: build, unit tests, Flyway migration dry run, Docker image push, deployment, and a smoke test calling key APIs. I demoed it to my lead, got feedback, and wrote a one-page runbook.
> **R:** Release time dropped from ~2 hours to ~20 minutes and missed-step hotfixes stopped. Other teams in the account adopted the pipeline. It taught me that small automation can have outsized impact.
""", I, ["ownership", "star", "amazon-lp"], True),

("Give an example of when you went above and beyond for a customer.", r"""
**Framework (Customer Obsession):** understand the customer's real problem (not just the ticket) → action → measurable benefit to the customer.

**Example:**
> **S:** A ticket asked us to "add an Export to Excel button" to the order dashboard.
> **T:** While implementing it, I wanted to understand why operators needed it.
> **A:** I joined a call with two store operators and watched them work. They exported every morning only to filter orders by status and store, then re-type order IDs back into our app. So besides the export, I proposed saved filters and a bulk status-update action. I built a prototype in Angular in two days and showed it to the client PM, who prioritised it.
> **R:** Operators said it saved them ~30 minutes each daily, and export usage dropped significantly. I learned to ask "what problem are you solving?" before building what's literally asked.
""", I, ["customer-obsession", "star", "amazon-lp"], True),

("Tell me about a time you had to learn a new technology quickly.", r"""
**Framework (Learn and Be Curious):** the trigger → how you learned efficiently (docs, small prototype, asking experts) → applied it → result.

**Example:**
> **S:** Our client wanted order-status notifications to be asynchronous, and the architecture decision was to use RabbitMQ — which nobody on our team had used.
> **T:** I volunteered to build the first integration within a sprint.
> **A:** I spent two days on the official tutorials and built a small Spring Boot prototype covering exchanges, queues, dead-letter queues and retries. I wrote down the failure cases (duplicate messages, consumer crash) and designed the consumer to be idempotent using the order event ID. I shared a 30-minute walkthrough with the team.
> **R:** We shipped notifications on schedule with no message loss in production, and the prototype became our team's reference. Now I follow the same approach for any new tech — official docs, tiny prototype, failure cases, then share.
""", B, ["learning", "star", "amazon-lp"], True),

("What are your strengths?", r"""
**Framework:** pick 2-3 strengths relevant to the role, each backed by a **short proof**. Avoid generic adjectives without evidence.

**Example:**
> "First, **debugging and digging into production issues** — I'm usually the person who finds root causes in our order module, like tracing a duplicate-order bug to retries without idempotency.
> Second, **full-stack ownership** — I'm comfortable taking a feature from the MySQL schema and Spring Boot API to the Angular UI and the Jenkins deployment, which reduces hand-offs.
> Third, **learning quickly** — I picked up RabbitMQ in a week to deliver our notification service, and I'm currently deepening my system design skills."

Tie at least one strength to the job description.
""", B, ["strengths", "hr"], True),

("What is your biggest weakness?", r"""
**Framework:** a **real but non-critical** weakness → concrete steps you're taking → evidence of improvement. Avoid clichés ("I'm a perfectionist") and core-job weaknesses ("I'm bad at coding").

**Example 1:**
> "Earlier I hesitated to ask for help — I'd spend a day stuck on something a senior could unblock in ten minutes. I now time-box: if I'm stuck for more than an hour or two after genuine effort, I write down what I've tried and ask. It's made me faster and I've learned more from those conversations."

**Example 2:**
> "My exposure to large-scale distributed systems is limited, since my current project serves a few thousand users. I've been studying system design — caching, queues, sharding — and applying ideas where possible, like introducing idempotent consumers in our RabbitMQ flow. A product company role is partly about closing this gap."
""", B, ["weakness", "hr"], True),

("Where do you see yourself in five years?", r"""
**Framework:** show ambition and commitment aligned with the company's growth path — skills, impact and responsibility, not a specific title or leaving to start a business.

**Example:**
> "In five years I want to be a senior engineer whom the team trusts with critical parts of the system — someone who designs features end to end, makes sound trade-offs at scale, handles production ownership and mentors newer engineers. In the near term, I want to become very strong in your core backend domain and in distributed systems. Whether that leads to a staff-engineer track or engineering management, I'd decide based on where I add the most value, but I see myself growing within a product company like yours."
""", B, ["career-goals", "hr"], False),

("Why should we hire you?", r"""
**Framework:** 3 points — **skills match** (map to JD), **proven impact** (one quick achievement), **attitude/fit** (ownership, learning). Finish confidently.

**Example:**
> "Three reasons. First, my skills map directly to this role: two years building Spring Boot microservices, Angular UIs and MySQL schemas in production, so I can contribute quickly on both backend and front end. Second, I focus on outcomes — I've cut a key API's latency from ~9 s to under 500 ms and automated our release process from two hours to twenty minutes. Third, I take ownership and learn fast: I was the one who picked up RabbitMQ for our notification service and became the team's go-to for production issues. I'm looking for a place to grow long-term, and I'd bring that same ownership here."
""", B, ["hr", "pitch"], True),

("What is your current CTC and expected CTC?", r"""
**Framework:** current CTC – **truthful**, with breakup (it gets verified via payslips/background checks). Expected – a **researched range** with the **lower end at or above your real target**, tied to role and market, not to your current salary.

**Example (recruiter screen):**
> "My current CTC is X LPA — Y fixed and Z variable. For expectations, based on my research on SDE roles with 2-3 years of experience at product companies of your size and the scope of this role, I'm looking at 16 to 19 LPA fixed. I'm flexible on the structure, and of course open to discussing once I understand the level and full compensation."

If you'd rather defer: "Could you share the budgeted range for this role? I'm confident we'll find a fair number if I'm the right fit."

Avoid: "Any hike is fine", a single exact number too early, or lying about current pay.
""", I, ["salary", "negotiation", "hr"], True),

("Your expectation is a big jump from your current salary. How do you justify it?", r"""
**Framework:** decouple from current pay → anchor on **market value of the role** and **your skills/impact** → stay calm and flexible on structure.

**Example:**
> "I understand it's a significant jump. My current salary reflects service-company pay bands, which are typically lower than product companies for the same skills. My expectation is based on market data for this role and level — I've looked at AmbitionBox, Glassdoor and conversations with peers — and on what I'll bring: production experience with Spring Boot, Angular and MySQL, plus results like the latency and release-automation improvements we discussed. I'm open to discussing the structure — fixed, variable, joining bonus — to make it work for both sides."

If they cap the hike at a percentage, ask about the level (SDE-2 bands), a joining bonus, or an early appraisal review at 6 months. Competing offers are the strongest justification — mention them honestly if you have them.
""", A, ["salary", "negotiation", "hr"], True),

("What is your notice period? Can you join earlier?", r"""
**Framework:** be **clear and honest** about the official period → show proactive options (early release, buyout, leave adjustment) → never promise a date you can't meet.

**Example:**
> "My official notice period is 90 days. I've checked with my HR: if the handover is planned well, an early release around 45-60 days is possible, and I can also adjust my pending leave. If your company supports a notice buyout, I'm open to that as well. I'll start knowledge transfer as soon as I resign so the transition is smooth."

Notes:
- Many product companies prefer ≤ 60 days; a long notice can lose you an offer, so explore early release options **before** interviews.
- Some candidates resign before having an offer to become "immediate joiners" — powerful, but risky; do it only with a strong pipeline and savings.
- Get the agreed joining date in the offer letter.
""", B, ["notice-period", "hr"], True),

("You have a competing offer / counter-offer. How would you handle it?", r"""
**With a competing offer (to the new company):**
> "I'm genuinely more excited about this role because of [team/product]. I do have another offer at X LPA fixed with a joining date of [date]. Is there flexibility to come closer on the fixed component? If we can align, I'd be happy to accept."
Be honest; share the offer letter if asked; don't fabricate offers.

**Counter-offer from current employer (if asked by the new company: "What if they counter?"):**
> "I made this decision for the kind of work and ownership I want, not only compensation. A counter-offer wouldn't change those reasons, so I don't intend to consider it."

Personal guidance: counter-offers rarely fix the reasons you wanted to leave, and accepting one can mark you as a flight risk. Also, accepting an offer and then backing out (offer-shopping) damages your reputation with recruiters — decide carefully, communicate promptly and professionally.
""", I, ["negotiation", "counter-offer", "hr"], False),

("Have you ever had to make a decision without complete information?", r"""
**Framework (Bias for Action):** situation with time pressure → what you knew/didn't know → how you reduced risk (reversible decision, rollback plan) → outcome and learning.

**Example:**
> **S:** One evening our order service started throwing timeouts in production; the on-call senior was unreachable for an hour.
> **T:** Orders were failing, so I had to act without full root-cause analysis.
> **A:** From logs and the DB monitoring dashboard, the connection pool was exhausted, correlated with a reporting query deployed that day. I couldn't prove causation in minutes, but disabling the report via its feature flag was **reversible and low-risk**. I informed my lead on chat, disabled it, and watched metrics.
> **R:** Errors stopped within five minutes. Next day we confirmed the report held connections during a long query; we moved it to a read replica with its own pool. My learning: when a decision is reversible, act quickly with a rollback plan and communicate; save deep analysis for after the bleeding stops.
""", I, ["bias-for-action", "amazon-lp", "star"], True),

("Tell me about a time you dove deep into data or logs to find a root cause.", r"""
**Framework (Dive Deep):** symptom that others couldn't explain → your methodical investigation (logs, metrics, queries, reproduction) → the non-obvious root cause → fix and prevention.

**Example:**
> **S:** About once a week, customers were charged twice for the same order; the team had attributed it to "payment gateway glitches".
> **T:** I took it up to find the real cause.
> **A:** I correlated application logs, gateway callbacks and DB timestamps for 15 affected orders. Each had two payment requests ~30 s apart — exactly our Angular HTTP timeout, after which the user clicked "Pay" again while the first request was still processing. The backend had no idempotency check.
> **R:** I added an idempotency key generated per checkout, a unique constraint on (order_id, idempotency_key), disabled the button during processing using `exhaustMap`, and handled timeouts by polling payment status. Duplicate charges dropped to zero, and we saved hours of manual refund work every week.
""", A, ["dive-deep", "amazon-lp", "star"], True),

("Tell me about a time you improved a process or simplified something complex.", r"""
**Framework (Invent and Simplify):** a painful/complex process → your simpler idea → how you got buy-in → measurable impact.

**Example:**
> **S:** Adding a new field to the order screen required changes in six places: entity, DTO, mapper, validation, Angular model and form — and people often missed one, causing bugs.
> **T:** I wanted to cut the effort and errors.
> **A:** I introduced MapStruct to generate DTO mappers, centralised validation with Bean Validation annotations on DTOs, and generated TypeScript interfaces from our OpenAPI spec using openapi-generator in the build. I demoed it with a real story and wrote a short guide.
> **R:** Adding a field went from ~half a day to about an hour, and mapping-related bugs nearly disappeared from QA reports. Lesson: removing repetitive manual steps improves both speed and quality.
""", I, ["invent-simplify", "amazon-lp", "star"], False),

("How do you handle feedback or criticism?", r"""
**Framework:** show you **seek** feedback, listen without being defensive, act on it, and show the change. Give a real example.

**Example:**
> "I treat feedback as the fastest way to improve. In my first year, a senior reviewer left many comments on my PRs about large methods and missing tests. Initially it felt like a lot, but I set up a 20-minute call to understand his reasoning. I started breaking changes into smaller PRs, writing tests first for business logic, and running a self-review checklist before requesting review.
> Within a couple of months my PRs were getting approved with far fewer comments, and in my appraisal my lead specifically mentioned code quality as an improvement. Now I actively ask for feedback after major tasks, and I try to give thoughtful reviews to others the same way."
""", B, ["feedback", "growth"], True),

("Tell me about a time you helped or mentored a teammate.", r"""
**Framework (Hire and Develop the Best):** who needed help → what you did specifically (pairing, docs, reviews) → their growth and team impact.

**Example:**
> **S:** Two freshers joined our team mid-project and were struggling with our Spring Boot + Angular codebase; their first tasks were taking weeks.
> **T:** My lead asked me to help them ramp up while continuing my own work.
> **A:** I wrote a one-page architecture overview and a "first week" setup guide, picked small, well-defined starter tasks for them, and did 30-minute pairing sessions twice a week. In code reviews I explained *why* behind comments and linked examples in our codebase.
> **R:** Within a month both were independently delivering stories; one later owned the notifications module. The onboarding guide became the team's standard and cut setup time for later joiners from days to a few hours. It also improved my own understanding of the system.
""", I, ["mentoring", "teamwork", "star"], False),

("Tell me about a time you insisted on high quality when others were okay with less.", r"""
**Framework (Insist on the Highest Standards):** a quality gap → you raised the bar with a practical approach (not perfectionism) → outcome.

**Example:**
> **S:** Our pricing module had about 30% test coverage, and the team considered manual QA "good enough". Rounding bugs in discounts kept reaching UAT.
> **T:** Before a major GST-related change, I felt we needed a safety net.
> **A:** I proposed covering pricing rules with parameterised JUnit 5 tests before touching the logic. To keep it practical, I focused only on the pricing package, used `BigDecimal` with explicit rounding modes, and added a SonarQube quality gate (80% coverage on new code) for that module. I wrote the first set of tests myself to show the effort was manageable.
> **R:** The tests caught two rounding bugs during the GST change, before UAT. Coverage rose to ~80% for the module, and pricing-related UAT defects dropped sharply. The team adopted the quality gate for other critical modules.
""", I, ["high-standards", "amazon-lp", "quality"], False),

("How do you prioritise when you have multiple tasks or stakeholders?", r"""
**Framework:** explain a **method** (impact × urgency, dependencies) + **communication** with stakeholders + an example.

**Example:**
> "I list everything and rank by business impact and urgency: production issues affecting customers first, then commitments with fixed deadlines, then items that unblock teammates, then improvements. When two stakeholders both say 'urgent', I don't decide silently — I bring both items to my lead or PM with impact estimates and let them choose.
> For instance, during one sprint I had a client feature due Friday, a P2 production bug and a request from QA for test data scripts. I fixed the bug first because it affected operators daily, shared a 30-minute script to unblock QA, and told the PM that the feature might slip by a day unless we dropped a minor sub-task. We dropped the sub-task and delivered on time. Clear, early communication is the key part."
""", B, ["prioritization", "time-management"], True),

("Describe a situation where you had to deal with ambiguity.", r"""
**Framework:** unclear requirement → you clarified proactively (questions, prototypes, assumptions documented) → delivered → feedback loop.

**Example:**
> **S:** The client asked for a "dashboard showing order health", with no definition of metrics.
> **T:** I was asked to build it in two sprints.
> **A:** I listed questions — who uses it, what decisions they make from it — and scheduled a 30-minute call with the operations manager. From that I drafted three metrics (orders stuck > 24 h, failed payments, delayed shipments), built a quick Angular mock with dummy data, and shared it for feedback before writing any backend code. I documented assumptions in the ticket.
> **R:** The client changed one metric after seeing the mock, which saved us from rework later. The dashboard went live on time and became their daily stand-up screen. Learning: in ambiguity, make assumptions explicit and get feedback on something visible early.
""", I, ["ambiguity", "star"], False),

("Do you have any questions for us?", r"""
**Framework:** always ask 2-3 genuine questions tailored to the interviewer's role. It signals curiosity, seriousness and helps you evaluate the company.

**To an engineer:**
- "What does the path from a PR to production look like here, and how is on-call handled?"
- "What's the most interesting technical challenge your team solved recently?"

**To a hiring manager:**
- "What would success look like for this role in the first 3-6 months?"
- "How do engineers grow from SDE-1 to SDE-2 here — what distinguishes those who grow fastest?"

**To HR:**
- "Could you walk me through the compensation structure and the appraisal cycle?"
- "What are the next steps and timeline?"

Optional closer: "Is there anything in my background you'd like me to clarify?" Avoid asking about salary in technical rounds, or anything easily found on their website.
""", B, ["questions-to-ask", "hr"], True),

("Why are you switching after only two years?", r"""
**Framework:** two years = meaningful experience, not job-hopping → you achieved things → you're ready for more scope → this move is deliberate and long-term.

**Example:**
> "Two years gave me a solid foundation — I've owned modules in production, handled releases and incidents, and delivered measurable improvements like the API latency fix. I've reached a point where the next level of growth — larger scale, product ownership, stronger engineering practices — isn't available in my current setup. I'd rather make a deliberate move now to the right environment than stay where my learning has plateaued. I'm looking for a place where I can grow for the long term, which is why I'm being selective about product companies like yours."

Avoid sounding like you're escaping something, and don't imply you'll leave the next company quickly too.
""", B, ["why-switch", "hr"], False),

("How do you handle stress or pressure, for example during a production outage?", r"""
**Framework:** a calm, structured approach + a real example + what you do to prevent recurring stress.

**Example:**
> "I try to stay structured rather than reactive. In an outage I first focus on impact — what's broken and for whom — then stabilise (rollback, feature flag, scaling), communicate status at regular intervals, and only then do the deep root-cause analysis.
> For instance, when our order service ran out of DB connections during a sale, I joined the incident call, identified a slow reporting query from metrics, and we disabled that feature within minutes while I posted updates every 15 minutes to the channel. Afterwards I wrote the post-mortem and we moved reporting to a read replica.
> Outside incidents, I manage pressure by breaking work into small tasks, flagging risks early and keeping a healthy routine. Pressure is easier when nothing is a surprise."
""", B, ["pressure", "incident"], False),

("What are your salary expectations if we can only offer a 30% hike on your current CTC?", r"""
**Framework:** stay polite, restate value and market data, explore **alternatives** (level, components, review timeline), and know your walk-away number in advance.

**Example:**
> "I appreciate the transparency. I understand companies have hike policies, but my current CTC reflects service-company bands rather than the market value for this role. Based on market data and the feedback from my rounds, I believe the role's range is more appropriate as a reference. Could we look at a few options? For example, evaluating me for the higher band if my interviews support it, a joining bonus to bridge the gap, or a compensation review after six months based on performance."

If they can't move and the offer is below your minimum, decline gracefully: "Thank you for the offer. I'm very interested in the role, but I'm unable to accept at this level. If there's flexibility in the future, I'd love to reconnect." Having another offer in hand changes this conversation completely — try to run 2-3 interview processes in parallel.
""", A, ["salary", "negotiation", "hr"], False),

("Tell me about a project you are most proud of.", r"""
**Framework:** pick a project where you had **clear ownership** and **measurable impact**. Cover: context (1 line) → your role → hardest part → result → what you learned. Prepare to draw its architecture.

**Example:**
> "I'm most proud of building the returns-and-refunds module for our retail client. Earlier, returns were handled through emails and spreadsheets, taking 5-7 days per refund.
> I owned it end to end: designed the MySQL schema and state machine (REQUESTED → APPROVED → PICKED_UP → REFUNDED), built Spring Boot APIs with idempotent refund calls to the payment gateway, used RabbitMQ events to notify the warehouse, and built the Angular screens for operators with reactive forms and role-based guards.
> The hardest part was keeping refunds consistent when the gateway call timed out — I added a status-check job and idempotency keys so refunds never duplicated.
> Result: refund turnaround dropped to about 48 hours and manual effort for operators went down significantly. It taught me how to design a feature from data model to UI with failure cases in mind."
""", I, ["project", "star", "ownership"], True),
]

sources = [
("Amazon Jobs - Leadership Principles", "https://www.amazon.jobs/content/en/our-workplace/leadership-principles"),
("Amazon Jobs - Interviewing at Amazon (STAR method)", "https://www.amazon.jobs/content/en/how-we-hire/interview-prep"),
("Atlassian - Company values", "https://www.atlassian.com/company/values"),
("AmbitionBox - Salary insights (India)", "https://www.ambitionbox.com/salaries"),
("Levels.fyi - India compensation data", "https://www.levels.fyi/"),
("GeeksforGeeks - HR Interview Questions", "https://www.geeksforgeeks.org/hr-interview-questions/"),
("InterviewBit - HR Interview Questions", "https://www.interviewbit.com/hr-interview-questions/"),
("Tech Interview Handbook - Behavioral interviews", "https://www.techinterviewhandbook.org/behavioral-interview/"),
("Tech Interview Handbook - Negotiation", "https://www.techinterviewhandbook.org/negotiation/"),
]

build("behavioral", "hr", "Behavioral & HR", 11, "🤝",
      "STAR stories, pitching service-company work, why-switch answers, salary and notice-period negotiation in India, Amazon LPs and questions to ask.",
      notes, qa, sources)
