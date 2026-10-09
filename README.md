# SwitchPrep 🚀

**Service company → product company in 60 days, at the senior bar companies hire for in 2027.** One website with
everything needed to prepare, a daily routine that keeps you consistent, and a tracker that shows exactly where you are.
The plan is selective on purpose: it schedules what most product companies actually ask and leaves the rest optional.

Built with **Angular 20** + **Spring Boot 3.5 (Java 21)** + **MySQL/H2**.

## What's inside

| Section | Contents |
|---|---|
| 🔥 **Daily Routine** | Habit tracker built for prep: most habits tick themselves from your progress (2 problems, 1 topic, 10 recall cards, 1 trap), plus study minutes (focus timer), applications and a one-line learning journal. Streaks, 12-week consistency heatmap, 7-day table, customisable habits. |
| 🎯 **High-Yield Focus** | The short version of the whole site: Tier 1 "must master" (must-do problems, most-asked stack questions, design essentials, top traps, core rounds) and Tier 2 "should know". |
| 🗓️ **60-Day Plan** | Selective day-by-day tasks within a daily time budget (DSA, core, design, one trap a day, interview-round playbooks, career, mocks, revision), each linking to the material. Dashboard shows today's tasks and what you're behind on. |
| 🪤 **Common Traps** | Questions most candidates get wrong (Java, concurrency, Spring, JPA, SQL, DSA, design, distributed systems, APIs, Angular/JS, OS/networking, behavioral). Commit to an answer first, then see the common wrong answer, why people fall for it, the correct answer and the interview tip. Trap of the day on the dashboard. |
| 🧭 **Interview Rounds** | How 2026-27 loops actually work: online assessment, AI-off live coding, AI-assisted coding, practical coding, machine coding, concurrency, code review, production debugging, senior system design, resume and project deep dives, behavioral, HR. Format, rubric, playbook, a worked walkthrough and the common failures for each. |
| 🧩 **DSA** | ~170 curated problems in 17 patterns (NeetCode 150 / Blind 75 / Striver SDE sheet classics) with pattern templates, approach, Java solution, complexity, company tags, must-do flags and filters. |
| 🏗️ **System Design** | HLD concepts (caching, sharding, Kafka, rate limiting, CAP...), 15 HLD case studies (URL shortener, WhatsApp, Uber, BookMyShow, UPI...), LLD fundamentals (SOLID, design patterns), machine-coding problems with full Java code, and **Senior Design (2027)**: failure handling, idempotency, multi-region, SLOs, cost, RAG system design, payments reliability, job scheduler, flash sales, webhooks and more. |
| 📚 **Core Subjects** | Notes + interview Q&A for Core Java, Spring Boot, Microservices, SQL/MySQL, Angular, JS/TS, OS, CN, DBMS, OOP, Behavioral/HR, plus the **senior 2027 subjects**: production debugging, performance, practical concurrency, testing & code review, cloud & DevOps, security, AI-assisted engineering, senior leadership. Flashcard mode, "frequently asked, not yet known" filter. |
| 🎯 **Final Round (14 days)** | Questions reported from real interviews/OAs at Amazon, Microsoft, Google, Flipkart, Walmart, PhonePe, Atlassian, Uber, Goldman Sachs and more: 280 MCQs (timed exam mode), 56 coding problems with hints and solutions, 84 verbal questions. |
| 🤖 **AI Engineer Course** | 14 modules from Python for Java devs → ML → deep learning → transformers → LLM APIs → RAG → agents/MCP → fine-tuning → evals/LLMOps → Spring AI → AI system design. Lessons, exercises, quizzes, projects. |
| ★ **Revision list** | Everything you starred or wrote notes on. |
| 💼 **Job Switch Guide** | Resume, where to apply, referrals, interview process by company, project story, salary negotiation. |

Progress tracking: done/revise flags and personal notes on every item, quiz scores, daily routine and streaks,
activity heatmap, export/import (includes the routine), optional account sync.

## Run it

### Option A: frontend only (no backend, progress in your browser)
```bash
cd frontend
npm install
npx ng serve        # open http://localhost:4200
```

### Option B: full stack (accounts + progress saved in the database)
```bash
# terminal 1: API on :8080 (H2 file database, no setup needed)
cd backend
mvn spring-boot:run

# terminal 2: UI on :4200 (proxies /api to :8080)
cd frontend
npm install
npx ng serve
```
Then open **Account & Data** in the app and create an account.

To use **MySQL** instead of H2:
```bash
docker compose up -d                                  # or use your own MySQL 8
cd backend
mvn spring-boot:run -Dspring-boot.run.profiles=mysql  # DB_URL / DB_USERNAME / DB_PASSWORD env vars override defaults
```

### Option C: one jar / one Docker image
```bash
./scripts/build-all.sh && java -jar backend/target/switchprep-api-1.0.0.jar   # http://localhost:8080
# or
docker build -t switchprep . && docker run -p 8080:8080 switchprep
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for GitHub Pages and cloud hosting.

## Documentation
- [CLAUDE.md](CLAUDE.md) – conventions for working on the repo (for humans and AI assistants)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) – how the app is structured
- [docs/CONTENT.md](docs/CONTENT.md) – content JSON schemas and how to add content
- [docs/API.md](docs/API.md) – REST API reference
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) – hosting options

## Content sources
Content is written originally for this project, informed by public resources that are credited inside each topic
(LeetCode, NeetCode, Striver's SDE sheet, system-design-primer, ByteByteGo, Hello Interview, Baeldung, official
Spring/Angular/Java docs, GeeksforGeeks and LeetCode Discuss interview experiences, DeepLearning.AI, fast.ai,
Hugging Face, Karpathy's Zero to Hero, Spring AI docs, and others). Problem statements are paraphrased; each DSA
problem links to its LeetCode page for practice. Company tags reflect commonly reported interview experiences and
aren't guaranteed.
