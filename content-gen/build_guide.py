"""Builds frontend/public/content/guide.json (Job Switch Guide). Run: python3 content-gen/build_guide.py"""
import json, pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "frontend/public/content/guide.json"

sections = []
def add(id, title, icon, content):
    sections.append({"id": id, "title": title, "icon": icon, "content": content.strip()})

add("strategy", "The 74-day strategy", "🧭", r"""
You have two years of Spring Boot, Angular and MySQL. That is a real advantage: most product-company backend roles for
SDE-1/SDE-2 at 2-4 YOE are Java/Spring shops (Walmart, PhonePe, Flipkart, Swiggy, Razorpay, Paytm, Intuit, Oracle,
SAP Labs, Atlassian, Uber, Zeta, Juspay, CRED...). What separates you from an offer is mostly **DSA speed** and
**system design vocabulary**, plus being able to talk about your project like an owner.

### How the time is split

| Phase | Days | What you do | Daily time |
|---|---|---|---|
| Foundation | 1-21 | DSA patterns 1-7, Core Java, practical concurrency, Spring Boot, SQL, HLD basics + LLD fundamentals, first machine-coding problems, resume | ~3 h weekdays, 5-6 h weekends |
| Depth | 22-42 | Trees to DP, microservices, production debugging, Angular, performance, testing and code review, behavioral, case studies, senior design topics; **start applying** | same |
| Interview mode | 43-60 | Remaining patterns + must-do re-solves, AI-assisted engineering, security, leadership, breadth questions, mocks every few days | same |
| Final round | 61-74 | Real past questions: MCQ tests, timed coding, verbal theory | 3-4 h |

### Rules that make this work

1. **Apply from day 21, not day 60.** Hiring pipelines take 3-6 weeks. If you wait until you feel ready, you lose a month.
   Your first 3-4 interviews are practice anyway; schedule dream companies for weeks 7-10.
2. **Never skip the daily plan two days in a row.** The dashboard shows how far behind you are. Catch up on weekends.
3. **DSA: 25-minute rule.** Try a problem for 25 minutes. If stuck, read the approach only, then code it yourself.
   Mark it ☆ "revise later" and re-solve it 3 days later without looking.
4. **Speak while you code.** Interviewers grade communication. Practise explaining your approach out loud before typing.
5. **Write things down.** Use the notes box on every problem: the key insight in one line, and the bug you made.
6. **Sleep 7 hours.** Retention drops sharply without sleep; a tired 3 hours is worth less than a rested 2.
7. **Run on routine, not motivation.** The Daily Routine page ticks most habits for you as you study. A day counts as
   complete at 80% of habits; protect the streak, and on a bad day do the minimum (1 trap, 10 flashcards, 1 problem).
8. **Short on time? Use the High-Yield Focus list.** Tier 1 is the part of this site that most loops actually test.
9. **Read the round before you practise it.** The Interview Rounds pages show how each round is scored, so you
   practise what earns points (talking through trade-offs, naming failure modes, writing tests).

### What "ready" looks like
- Must-do DSA problems solved without hints, Mediums in ~25 minutes.
- Can design URL shortener, chat, news feed, rate limiter and a booking system on a whiteboard in 45 minutes.
- Can write a working parking lot / splitwise style LLD in Java in 75 minutes.
- Can answer "Tell me about your project" in 2 minutes with numbers, and survive 15 minutes of follow-ups.
- Can debug a production incident out loud (symptom, metrics, recent change, mitigate, root cause, guardrail).
- Can name the exact race in a concurrency question and the guard that fixes it (constraint, conditional update, lock).
- Can review a flawed Spring snippet and rank the findings by production risk.
- 70%+ on Final Round MCQ tests in exam mode.
""")

add("resume", "Resume that gets shortlisted", "📄", r"""
Recruiters spend under 10 seconds on the first pass, and most product companies run an ATS keyword filter first.

### Format
- **One page**, single column, PDF, simple font (no photos, no skill bars, no tables for layout).
- Sections in this order: Header (name, phone, email, LinkedIn, GitHub, city) → Summary (2 lines, optional) →
  Experience → Projects → Skills → Education → Achievements.
- File name: `Raj_<Surname>_Backend_Engineer.pdf`.

### Bullet formula: Action verb + what you built + technology + measurable impact
Weak (service-company style):
> - Worked on REST APIs for client application using Spring Boot.

Strong:
> - Built 14 REST APIs in **Spring Boot + MySQL** for an order-management module used by **3,000+ daily users**;
>   cut p95 latency from **1.2 s to 280 ms** by adding composite indexes and fixing N+1 queries in JPA.
> - Designed a **JWT + Spring Security** role-based auth layer replacing session auth, enabling horizontal scaling to 4 instances.
> - Implemented an **Angular** dashboard with lazy-loaded modules and OnPush change detection; reduced initial bundle by **38%**.
> - Introduced **JUnit 5 + Mockito** tests raising coverage from 20% to 65%; caught 2 production regressions pre-release.

If you don't know the exact numbers, estimate honestly (requests/day, records in table, response time before/after)
and be ready to explain how you measured them.

### Keywords to include (only if you can talk about them)
Java 17, Spring Boot, Spring Data JPA, Hibernate, Spring Security, JWT, REST, Microservices, MySQL, Redis, Kafka,
Docker, Kubernetes (basic), AWS (EC2/S3/RDS), CI/CD (Jenkins/GitHub Actions), JUnit, Mockito, Angular, TypeScript, RxJS,
Data Structures & Algorithms, System Design, Git.

### Projects section
Service-company work is often under NDA or unglamorous, so add **one strong personal project** that shows
product thinking. This SwitchPrep app is a good one: *Angular + Spring Boot + MySQL, JWT auth, progress analytics,
deployed on Render/Railway with Docker*. Later, add an AI project from the AI course (a RAG chatbot over docs with Spring AI).

### Common mistakes
- Listing responsibilities instead of outcomes.
- "Familiar with" 25 technologies. List what you would be comfortable being grilled on.
- Objective statements ("Seeking a challenging role..."). Delete.
- Typos and inconsistent tense. Past tense for past roles.
""")

add("where-to-apply", "Where and how to apply", "📬", r"""
### Channels, ranked by response rate
1. **Employee referrals** (5-10x better than cold applying). Use LinkedIn: search `<Company> software engineer`,
   filter 2nd-degree connections and alumni of your college. Message template below.
2. **Recruiter outreach on LinkedIn**: set "Open to work" (visible to recruiters only), headline like
   `Backend Engineer | Java, Spring Boot, Microservices, MySQL | Angular`.
3. **Job portals**: Naukri (update profile every 2-3 days, it boosts ranking), LinkedIn Jobs, Instahyre, Cutshort,
   Hirist, Wellfound (startups), iimjobs/hirist for tech, company career pages.
4. **Hiring events / drives**: many companies (Walmart, PhonePe, Swiggy, Flipkart, Amazon) run weekend hiring drives
   for 2-5 YOE; watch LinkedIn posts by their recruiters.

### Referral message template
> Hi <Name>, I'm a backend engineer with 2 years in Java/Spring Boot and MySQL at <Company>. I saw the
> <Role, Job ID/link> opening on your team and I think I'm a strong fit: I recently <one impressive bullet>.
> Would you be open to referring me? I've attached my resume and I'm happy to share anything else. Thank you!

Keep it short, attach the job link and resume, and follow up once after 4-5 days.

### Volume
Target **10-15 targeted applications per day from day 21** and 3-5 referral requests per day. Track them in a sheet
(company, role, date, channel, status, next step).

### Which companies pay ~15 LPA+ for 2-3 YOE (India, typical ranges, verify on AmbitionBox/Glassdoor/levels.fyi)
| Tier | Examples | Typical fixed CTC for 2-3 YOE |
|---|---|---|
| Top product / FAANG-like | Google, Microsoft, Amazon (SDE-1/2), Atlassian, Uber, LinkedIn, Salesforce | 22-45 LPA |
| Strong product / unicorns | Flipkart, PhonePe, Swiggy, Razorpay, CRED, Meesho, Zomato, Walmart Global Tech, Intuit, Adobe | 18-35 LPA |
| Product + GCCs / fintech | Paytm, Oracle, SAP Labs, ServiceNow, Visa, Goldman Sachs, JP Morgan, Morgan Stanley, Zeta, Juspay, Myntra | 14-28 LPA |
| Mid-size product / SaaS startups | Freshworks, Zoho, Postman, BrowserStack, Chargebee, Groww, Dream11, Urban Company | 12-25 LPA |

Numbers vary by year, city and negotiation; treat them as directional. 15 LPA is very achievable in the third and
fourth tiers and a floor in the first two.
""")

add("process", "Interview process by company type", "🧪", r"""
Most product companies for 2-4 YOE backend roles follow a variant of this:

1. **Online assessment (OA)** — HackerRank / HackerEarth / CodeSignal / Codility. 2-3 DSA questions in 60-90 min,
   sometimes MCQs (Java, SQL, OS, CN, aptitude). Final Round days 1, 4 and 5 simulate this.
2. **DSA round(s)** — 1-2 rounds, 45-60 min each, 2 problems (usually Medium, sometimes Medium-Hard). They grade:
   problem understanding, approach, complexity, clean code, testing with edge cases, communication.
3. **LLD / machine coding** — common at Flipkart, PhonePe, Swiggy, Razorpay, Uber, Atlassian, Zeta, Cred, Udaan.
   60-120 min to build a working, extensible program (parking lot, splitwise, rate limiter, snake & ladder...).
4. **HLD / system design** — for SDE-2. 45-60 min design discussion (URL shortener, notification system, BookMyShow...).
5. **Hiring manager / project deep dive** — your project architecture, decisions, failures, conflicts, ownership.
6. **HR / culture fit** — motivation, expected CTC, notice period.

### Company notes (reported patterns)
| Company | What to expect |
|---|---|
| Amazon | OA (2 coding + work-style survey), 3-4 rounds each mixing DSA and **Leadership Principles** stories; bar raiser |
| Microsoft | 4-5 rounds: DSA heavy (trees, linked lists, DP), one design round for SDE-2, AA (as-appropriate) round |
| Google | 4-5 DSA rounds (graphs, DP, tricky reasoning), Googlyness round; team match afterwards |
| Flipkart | Machine coding (90 min) → DSA (PS/DS) → HLD (SDE-2) → HM |
| Walmart Global Tech | DSA + Java/Spring deep dive + LLD/HLD + HM; Java-heavy |
| PhonePe | Machine coding is a big filter; then DSA, design, HM |
| Atlassian | Coding (practical, design-flavoured like rate limiter, snake game), values round, system design, management round |
| Uber | DSA + machine coding/LLD + HLD + collaboration round |
| Goldman Sachs / JPMC | HackerRank OA, then CoderPad DSA, Java/OOP/multithreading, some system design |
| Razorpay / Paytm / fintechs | Machine coding, DSA, Java concurrency, transactions & idempotency, HLD |
| Oracle / SAP / Adobe | DSA + Java + CS fundamentals (OS, DBMS, CN) + project |

### During any coding round
1. Repeat the problem in your words; ask about input size, edge cases, duplicates, negative numbers, empty input.
2. State brute force and its complexity first, then optimise.
3. Agree on the approach **before** coding.
4. Write clean code with meaningful names; talk while you write.
5. Dry-run with an example; test edge cases; state final complexity.
""")

add("project-story", "Talking about your project", "🗣️", r"""
"Tell me about your current project" is asked in nearly every round and decides how senior you sound.

### 2-minute structure
1. **Context (20s)**: what the product does, who uses it, scale (users, requests/day, data size).
2. **Architecture (40s)**: Angular frontend → Spring Boot services → MySQL (+ Redis/Kafka if any); how it's deployed.
3. **Your ownership (40s)**: 2-3 things *you* built or decided, with numbers.
4. **A hard problem (20s)**: a performance bug, production incident, or design trade-off and how you solved it.

### Prepare answers to these follow-ups
- Draw the architecture. Where are the bottlenecks? What breaks at 10x traffic?
- How is authentication done? How are passwords stored? Session vs JWT trade-offs?
- Show a table schema you designed. Which indexes exist and why?
- How do you handle transactions across two tables? Across two services?
- What happens if the DB goes down? Retries? Timeouts?
- How is it deployed? CI/CD? How do you roll back?
- How do you monitor it? What alerts exist?
- What would you redesign if you started again?
- Hardest bug you fixed and how you found it.

### Turning service-company work into product-company stories
- Emphasise **ownership** ("I proposed / designed / led"), not assignment ("I was given").
- Talk about **users and impact**, not tickets.
- If the work was maintenance, pick the most technical improvements you made: query optimisation, caching,
  refactoring to clean architecture, test automation, performance tuning, a migration.
- Your personal projects (this app, the AI project) are fair game: talk about them with the same depth.
""")

add("negotiation", "Salary negotiation (target 15 LPA+)", "💰", r"""
### Before interviews
- Know your **current CTC breakdown**: fixed, variable, bonus, ESOPs, benefits. Recruiters ask early.
- Research the role's band on AmbitionBox, Glassdoor, levels.fyi, LinkedIn posts, and by asking friends.
- Decide your **walk-away number** (e.g. 14 LPA fixed) and your **target** (e.g. 18 LPA fixed).

### "What is your expected CTC?"
Indian recruiters always ask. Options, best to worst:
1. Deflect politely early: *"I'm focused on finding the right role; I'm sure we can agree on a fair number if
   there's a fit. Could you share the budget for this position?"*
2. If pushed, give a researched range anchored high: *"Based on my research for SDE-2 backend roles with my
   skills, I'm looking at 18-22 LPA fixed."* (The bottom of your range should still be above your target.)
3. Avoid quoting a % hike on your current CTC. Service-company salaries are low; a "50% hike" may still undersell you.
   Focus on **market value for the role**.

### After the offer
- Thank them, ask for the written breakdown, and say you need 2-3 days.
- **Competing offers are the strongest lever.** Try to have interviews converge in the same 2-week window.
- Negotiate fixed pay first, then joining bonus (to cover notice-period buyout or lost bonus), then ESOPs/RSUs.
- Script: *"I'm excited about the role and the team. I have another offer at X fixed. If you can get to Y,
  I'm ready to accept and can start on <date>."*
- Be polite and concise; never lie about offers (companies sometimes ask for proof).

### Notice period
Most service companies have 60-90 day notice. Many product companies prefer < 30-60 days.
- Ask your manager early about **buyout** or early release policy.
- Some companies will pay a joining bonus to buy out notice; ask.
- Resign only after a **written offer letter** (and ideally after background verification starts).

### Counter-offers from your current company
They are common after resignation. Accepting one is rarely a good idea: the reasons you wanted to leave usually remain,
and your loyalty is now in question. Decide in advance.
""")

add("behavioral", "Behavioral rounds quick reference", "🤝", r"""
Use **STAR**: Situation (1-2 lines) → Task (your responsibility) → Action (what *you* did, the bulk) → Result (numbers, learning).

Prepare **6-8 stories** from your work that you can reuse:
1. A project you're proud of (ownership, impact)
2. A tight deadline you delivered on
3. A production bug/incident you debugged
4. A disagreement with a teammate or manager and how it resolved
5. A time you failed or made a mistake, and what changed after
6. A time you went beyond your role (mentoring, improving a process, automation)
7. A time you learned a new technology quickly
8. A time you received critical feedback

For Amazon, map stories to Leadership Principles (Customer Obsession, Ownership, Dive Deep, Bias for Action,
Deliver Results, Earn Trust, Learn and Be Curious, Have Backbone; Disagree and Commit).

### "Why do you want to leave your current company?"
Stay positive; never criticise your employer.
> *"I've learned a lot in two years, especially in Spring Boot and building REST services for clients. I now want
> to work on a product I own end-to-end, at a larger scale, with stronger engineering practices like design reviews
> and on-call ownership. <Company>'s work on <specific product> is exactly that."*

### Questions to ask at the end
- What does the first 90 days look like for this role?
- How does the team ship to production? How often? How is on-call handled?
- What's the biggest technical challenge the team is facing this year?
- How do you measure success for an engineer at my level?

The Core Subjects → Behavioral & HR section has 30 questions with model answers.
""")

add("mock-interviews", "Mock interviews & practice platforms", "🎤", r"""
Mocks are the closest thing to the real interview. Do at least **6** before your important interviews.

### Free / low-cost options
- **Pramp / Exponent peer mocks**: free peer-to-peer DSA and system design mocks.
- **interviewing.io**: anonymous mocks with engineers (some free slots).
- **LeetCode weekly / biweekly contests** (Sun 8 AM, alternate Sat 8 PM IST): best timed practice; aim to solve 2-3.
- **Friends**: swap mocks with a friend who is also switching; use problems from this site.
- **Yourself**: record a 45-minute screen + voice session solving 2 problems. Watch it back. Painful but very effective.

### Self-mock routine (used in the plan on mock days)
1. Pick 2 unseen problems (1 Medium + 1 Medium/Hard) from the DSA list filtered to "To do".
2. Set a 60-minute timer; explain out loud as if an interviewer is present.
3. After: write in the notes what went wrong (approach, bugs, time management, communication).

### System design self-mock
Pick a case study you haven't read, set 45 minutes, and design on paper/Excalidraw following the framework in
"How to approach a system design interview". Then read the case study and compare.

### Where to practise code on this site
Each DSA problem links to LeetCode to run tests. Write the solution there first, then compare with the solution here.
""")

add("after-offer", "After the offer: first 90 days & the AI path", "🚀", r"""
### Before joining
- Get the offer letter, complete background verification documents, serve notice professionally, hand over well.
- Take a few days off between jobs if you can.

### First 90 days at a product company
- Days 1-30: learn the codebase, set up local env, ship a small bug fix in week 1-2, understand on-call and deployment.
- Days 31-60: own a small feature end-to-end; write a design doc for it.
- Days 61-90: take on a larger piece; start reviewing others' code thoughtfully.
- Keep a "brag document" of what you shipped and its impact: it makes appraisals and the next switch easy.

### Becoming an AI engineer
The AI Engineer Course on this site goes from Python to RAG, agents, fine-tuning and production LLMOps, and ends with
doing it in Java via Spring AI so you can apply it at work immediately. A realistic path:
1. Months 1-3 after joining: modules 1-6 (Python, ML, deep learning, transformers), 8-10 h/week.
2. Months 4-6: modules 7-10 (LLM APIs, embeddings, RAG, agents); build 2 portfolio projects.
3. Months 7-9: modules 11-14 (fine-tuning, evals, Spring AI, AI system design); look for AI features to build in
   your product team, or apply for AI engineer roles with your projects.
""")

OUT.write_text(json.dumps({"sections": sections}, ensure_ascii=False, indent=1))
print("guide sections:", len(sections))
