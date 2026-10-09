# Content

All study content is JSON in `frontend/public/content/`. Long text fields are **Markdown** (GFM tables, fenced code
blocks with a language: `java`, `python`, `sql`, `ts`, `js`, `bash`, `json`, `yaml`, `xml`, `text`).

| File | What | Generator |
|---|---|---|
| `plan.json` | 60-day plan (selective, high-yield) | `content-gen/build_plan.py` |
| `focus.json` | High-Yield Focus list (Tier 1 / Tier 2) | `content-gen/build_focus.py` |
| `guide.json` | Job switch guide | `content-gen/build_guide.py` |
| `dsa-part1.json`, `dsa-part2.json` | DSA patterns 1-9 and 10-17 | `gen_dsa_part1.py`, `build_dsa_part2.py` |
| `system-design-hld.json` | HLD concepts + case studies | `sd*`/`hld*` scripts |
| `system-design-lld.json` | LLD fundamentals + machine-coding problems | `lld*` scripts |
| `core-backend.json` | Java, Spring Boot, Microservices, SQL | `core*` scripts |
| `core-cs.json` | Angular, JS/TS, OS, CN, DBMS, OOP, Behavioral | `core*`/`cs*` scripts |
| `core-senior-1.json` | Senior 2027: production debugging, performance, practical concurrency, testing & code review | `senior1_merge.py` (`senior1_*.py`) |
| `core-senior-2.json` | Senior 2027: cloud & DevOps, security, AI-assisted engineering, senior leadership | `senior2_merge.py` (`senior2_*.py`) |
| `system-design-senior.json` | Senior design topics (production-flavoured concepts + case studies), group `senior` | `sdsenior_merge.py` (`sdsenior_*.py`) |
| `traps-1.json`, `traps-2.json` | Common traps (questions most candidates get wrong): backend areas / design, DSA and more | `traps1_build.py`, `traps2_merge.py` |
| `rounds.json` | Interview rounds guide (2026-27 formats, rubrics, walkthroughs) + trends | `rounds_build.py` |
| `final-round-1.json`, `final-round-2.json` | Final round days 1-7 and 8-14 | `fr1_merge.py`, `fr2_merge.py` |
| `ai-course-1.json`, `ai-course-2.json` | AI modules 1-6 and 7-14 | `ai1_*`, `ai2_*` |

After any change: `python3 content-gen/validate_content.py` (and `build_plan.py` + `build_focus.py` if ids/titles changed).

**Never rename an existing `id`**: ids are part of users' saved progress keys (see ARCHITECTURE.md).

## Schemas

### DSA (`dsa-part*.json`)
```jsonc
{ "patterns": [ {
  "id": "sliding-window", "name": "Sliding Window", "order": 3,
  "intro": "markdown: when to use, Java template, pitfalls",
  "problems": [ {
    "id": "longest-substring-without-repeating-characters",   // LeetCode slug
    "title": "...", "difficulty": "Easy|Medium|Hard", "companies": ["Amazon"],
    "leetcode": "https://leetcode.com/problems/<slug>/",
    "summary": "paraphrased problem", "approach": "markdown", "solution": "Java code",
    "time": "O(n)", "space": "O(k)", "mustDo": true
  } ]
} ] }
```

### System design (`system-design-hld.json` → `concepts`, `caseStudies`; `system-design-lld.json` → `fundamentals`, `problems`; `system-design-senior.json` → `topics`, each with `"kind": "concept|case-study"`)
Ids must be unique across **all** groups (progress key is `sd:{id}`). `minutes` is reading time.
```jsonc
{ "id": "caching", "title": "...", "order": 5, "level": "Basic|Intermediate|Advanced", "minutes": 15,
  "summary": "one line", "content": "markdown", "keyPoints": ["..."],
  "interviewQuestions": [ { "q": "...", "a": "markdown" } ],
  "sources": [ { "title": "...", "url": "..." } ] }
```

### Core subjects (`core-*.json`)
```jsonc
{ "subjects": [ {
  "id": "java", "name": "Core Java", "order": 1, "icon": "☕", "description": "...",
  "notes": [ { "id": "collections", "title": "...", "content": "markdown" } ],
  "qa": [ { "id": "java-001", "q": "...", "a": "markdown", "level": "Basic|Intermediate|Advanced",
            "tags": ["collections"], "frequent": true } ],
  "sources": [ ... ]
} ] }
```

### Final round (`final-round-*.json`)
```jsonc
{ "days": [ {
  "day": 1, "title": "...", "theme": "...",
  "mcqs":   [ { "id": "fr-d1-m1", "topic": "Java", "q": "markdown", "options": ["a","b","c","d"],
                "answer": 2, "explanation": "markdown", "askedAt": ["Amazon"] } ],
  "coding": [ { "id": "fr-d1-c1", "title": "...", "difficulty": "Medium", "askedAt": [...],
                "statement": "markdown", "hints": ["...","..."], "solution": "Java (or SQL starting with -- SQL)",
                "explanation": "markdown", "time": "O(n)", "space": "O(1)", "leetcode": "url or null" } ],
  "theory": [ { "id": "fr-d1-t1", "q": "...", "a": "markdown", "askedAt": [...] } ]
} ] }
```

### AI course (`ai-course-*.json`)
```jsonc
{ "modules": [ {
  "id": "m08-rag", "order": 9, "title": "...", "level": "Beginner|Intermediate|Advanced", "weeks": 2,
  "description": "...", "outcomes": ["..."],
  "lessons": [ { "id": "m08-rag-01", "title": "...", "minutes": 40, "content": "markdown", "exercise": "markdown",
                 "quiz": [ { "q": "...", "options": [4], "answer": 0, "explanation": "..." } ],
                 "resources": [ { "title": "...", "url": "...", "type": "video|article|course|docs|book" } ] } ],
  "project": { "title": "...", "description": "markdown" }
} ] }
```

### Traps (`traps-*.json`)
```jsonc
{ "traps": [ {
  "id": "hashmap-mutable-key", "area": "java",   // java|concurrency|spring|jpa-hibernate|sql|dsa|system-design|
                                                  // distributed-systems|api-design|angular-js|os-networking|behavioral
  "title": "...", "level": "Intermediate", "frequency": "Very common|Common|Occasional",
  "prompt": "markdown: the question as an interviewer asks it",
  "options": ["...", "..."] | null, "answer": 1 | null,       // MCQ form is optional
  "commonWrongAnswer": "markdown", "whyPeopleGetItWrong": "markdown", "correct": "markdown",
  "fix": "markdown or null", "interviewTip": "one or two sentences", "askedAt": ["Amazon"]
} ] }
```

### Interview rounds (`rounds.json`)
```jsonc
{ "trends": "markdown",
  "rounds": [ { "id": "machine-coding-lld", "order": 5, "title": "...", "icon": "🛠️", "summary": "...",
    "whoRunsIt": ["Flipkart"], "frequency": "...", "weight": "...", "format": "markdown",
    "whatTheyTest": ["..."], "rubric": "markdown", "howToAce": "markdown", "walkthrough": "markdown",
    "commonFailures": ["..."], "practice": [ { "title": "...", "link": "/system-design/lld-problems/parking-lot" } ],
    "sources": [ { "title": "...", "url": "..." } ] } ] }
```

### Focus list (`focus.json`, generated)
```jsonc
{ "intro": "markdown",
  "tiers": [ { "id": "tier-1", "title": "...", "description": "...",
    "groups": [ { "id": "t1-dsa", "title": "...", "description": "...",
      "items": [ { "key": "dsa:two-sum", "title": "...", "link": "/dsa/arrays-hashing/two-sum", "kind": "Arrays & Hashing",
                   "why": "optional" } ] } ] } ] }
```
`key` must be a real progress key (see ARCHITECTURE.md); the validator checks it.

### Plan (`plan.json`, generated)
```jsonc
{ "intro": "markdown", "hoursPerDay": "...",
  "weeks": [ { "week": 1, "title": "...", "goal": "..." } ],
  "days": [ { "day": 1, "week": 1, "title": "...", "focus": "...",
              "tasks": [ { "id": "dsa-dsa-arrays-hashing-two-sum",   // stable, unique within the day
                           "type": "dsa|core|sd|trap|round|ai|mock|revise|career", "title": "...", "minutes": 40,
                           "link": "/dsa/arrays-hashing/two-sum", "detail": "optional markdown" } ] } ] }
```
Links may carry query strings: `/core/java?chapter=3`, `/core/java?view=qa&filter=frequent-todo` (the Q&A tab filtered
to frequently asked questions not yet ticked), `/core/java?view=cards`.

### Guide (`guide.json`)
```jsonc
{ "sections": [ { "id": "resume", "title": "...", "icon": "📄", "content": "markdown" } ] }
```
