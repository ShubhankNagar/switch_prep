"""
Builds frontend/public/content/plan.json: the 60-day study plan.

The plan is deliberately selective ("learn less, master more"): it schedules the high-yield subset of the site's
content and leaves the rest as optional depth on each section page.

  * DSA: every must-do problem plus the most-asked others (about half of each pattern), in pattern order, days 1-46;
    then must-do re-solves.
  * Core: chapters of the owner's stack (Java, Spring Boot, SQL, microservices) and the senior 2027 subjects, a
    selected few chapters of CS fundamentals / Angular / JS, plus batches of *frequently asked* questions
    (links use ?filter=frequent-todo, so each batch is simply "the next ~10 you don't know yet").
    Core items fill each day up to a minute budget, in priority order; anything that doesn't fit stays optional.
  * System design: all HLD concepts, the most-asked case studies, the India machine-coding favourites, and the
    senior (production-flavoured) topics.
  * One "trap" (a question most candidates get wrong) per day, matched to what you're studying.
  * Interview-round playbooks on the day the matching material starts; career, mock and revision tasks.

Every task has a stable `id` (unique within its day); progress keys are plan:d{day}:{id}.
Re-run after changing content: python3 content-gen/build_plan.py
"""
import json, math, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
C = ROOT / "frontend/public/content"

def load(name, default):
    p = C / name
    return json.loads(p.read_text()) if p.exists() else default

dsa = sorted(load("dsa-part1.json", {"patterns": []})["patterns"] + load("dsa-part2.json", {"patterns": []})["patterns"],
             key=lambda p: p["order"])
hld = load("system-design-hld.json", {"concepts": [], "caseStudies": []})
lld = load("system-design-lld.json", {"fundamentals": [], "problems": []})
senior_sd = load("system-design-senior.json", {"topics": []})["topics"]
subjects = {s["id"]: s for f in ("core-backend.json", "core-cs.json", "core-senior-1.json", "core-senior-2.json")
            for s in load(f, {"subjects": []})["subjects"]}
ai = sorted(load("ai-course-1.json", {"modules": []})["modules"] + load("ai-course-2.json", {"modules": []})["modules"], key=lambda m: m["order"])
traps = load("traps-1.json", {"traps": []})["traps"] + load("traps-2.json", {"traps": []})["traps"]
rounds = {r["id"]: r for r in load("rounds.json", {"rounds": []})["rounds"]}

DAYS = 60
LONG_DAYS = {d for d in range(1, DAYS + 1) if d % 7 in (6, 0)}  # days 6,7,13,14,... are weekend-style long days
MOCK_DAYS = {28, 35, 42, 49, 53, 56, 59}
REVISE_DAYS = {7, 14, 21, 28, 35, 42, 49, 54, 57, 60}
NEW_CONTENT_LAST = 55            # days 56-60 are revision + mocks only
BUDGET_NORMAL, BUDGET_LONG = 200, 320   # minutes per day, excluding optional AI lessons

days = {d: [] for d in range(1, DAYS + 1)}

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]

def task(day, type_, title, minutes, link=None, detail=None, key=None):
    """Adds a task. `key` seeds the stable id (defaults to the link, else the title)."""
    base = f"{type_}-{slug(key or link or title)}"
    used = {t["id"] for t in days[day]}
    tid, n = base, 2
    while tid in used:
        tid, n = f"{base}-{n}", n + 1
    t = {"id": tid, "type": type_, "title": title, "minutes": minutes}
    if link: t["link"] = link
    if detail: t["detail"] = detail
    days[day].append(t)

def load_of(day):
    return sum(t["minutes"] for t in days[day] if t["type"] != "ai")

def budget(day):
    return BUDGET_LONG if day in LONG_DAYS else BUDGET_NORMAL

# ---------- DSA: must-do + most-asked, days 1-46 ----------
DSA_SHARE = 0.5
DSA_LAST = 46
selected = {}
for p in dsa:
    probs = p["problems"]
    want = max(sum(1 for q in probs if q.get("mustDo")), math.ceil(len(probs) * DSA_SHARE))
    ranked = sorted(range(len(probs)), key=lambda i: (not probs[i].get("mustDo"), -len(probs[i].get("companies", [])), i))
    selected[p["id"]] = set(sorted(ranked[:want]))
queue = []
for p in dsa:
    queue.append(("intro", p, None))
    for i, q in enumerate(p["problems"]):
        if i in selected[p["id"]]:
            queue.append(("problem", p, q))
weights = {d: (4 if d in LONG_DAYS else 3) for d in range(1, DSA_LAST + 1)}
for d in MOCK_DAYS:
    if d in weights: weights[d] = 1
total_problems = sum(1 for k, _, _ in queue if k == "problem")
total_w = sum(weights.values())
cum, bounds = 0, []
for d in range(1, DSA_LAST + 1):
    cum += weights[d]
    bounds.append((d, cum / total_w * total_problems))
i = 0
for kind, p, q in queue:
    d = next(dd for dd, b in bounds if i < b or dd == DSA_LAST)
    if kind == "intro":
        task(d, "dsa", f"Learn pattern: {p['name']} (read intro + template)", 20, f"/dsa/{p['id']}")
        continue
    task(d, "dsa", f"Solve: {q['title']} ({q['difficulty']})", 40 if q["difficulty"] != "Easy" else 25,
         f"/dsa/{p['id']}/{q['id']}", "Explain your approach out loud before coding; interviewers grade the reasoning."
         if q.get("mustDo") else None)
    i += 1
# must-do re-solves, days 47-60: the most-asked must-do Medium/Hard problems first, two a day
must = [(p, q) for p in dsa for q in p["problems"] if q.get("mustDo")]
must.sort(key=lambda pq: (pq[1]["difficulty"] == "Easy", -len(pq[1].get("companies", []))))
mi = 0
for dd in range(DSA_LAST + 1, DAYS + 1):
    for _ in range(1 if dd in MOCK_DAYS else 2):
        if mi < len(must):
            p, q = must[mi]; mi += 1
            task(dd, "revise", f"Re-solve from scratch, timed: {q['title']}", 30, f"/dsa/{p['id']}/{q['id']}")

# ---------- System design: selective queue ----------
CASES = ["url-shortener", "rate-limiter-design", "notification-system", "chat-whatsapp", "news-feed",
         "ecommerce-flipkart-checkout", "ticket-booking-bookmyshow", "payment-system-upi", "ride-hailing-uber",
         "food-delivery-swiggy", "search-autocomplete"]
LLD_FUND = ["how-to-approach-lld", "solid-principles", "design-patterns-creational", "design-patterns-structural",
            "design-patterns-behavioral", "concurrency-for-lld"]
LLD_PROB = ["parking-lot", "splitwise", "rate-limiter-lld", "snake-and-ladder", "bookmyshow-lld", "elevator-system",
            "pub-sub-message-queue", "in-memory-key-value-store", "cab-booking-lld"]
by_id = lambda items: {t["id"]: t for t in items}
case_map, fund_map, prob_map = by_id(hld["caseStudies"]), by_id(lld["fundamentals"]), by_id(lld["problems"])
concepts = [("concepts", t) for t in sorted(hld["concepts"], key=lambda t: t["order"])]
cases = [("case-studies", case_map[x]) for x in CASES if x in case_map]
llds = [("lld-fundamentals", fund_map[x]) for x in LLD_FUND if x in fund_map] + \
       [("lld-problems", prob_map[x]) for x in LLD_PROB if x in prob_map]
seniors = [("senior", t) for t in sorted(senior_sd, key=lambda t: t.get("order", 0))]
# Track A (one a day): concepts, with LLD fundamentals woven in early, then case studies alternating with senior topics.
# Track B (long days only): machine-coding problems, which need a 90-minute block.
design = []
ci = si = 0
while ci < len(cases) or si < len(seniors):
    for _ in range(2 if ci < 4 else 1):
        if ci < len(cases): design.append(cases[ci]); ci += 1
    if si < len(seniors): design.append(seniors[si]); si += 1
funds = [x for x in llds if x[0] == "lld-fundamentals"]
probs = [x for x in llds if x[0] == "lld-problems"]
track_a = concepts[:6]
rest_c = concepts[6:]
while funds or rest_c:
    if rest_c: track_a.append(rest_c.pop(0))
    if funds: track_a.append(funds.pop(0))
track_a += design
sd_queue = track_a + probs
KIND = {"concepts": "HLD", "case-studies": "Design", "lld-fundamentals": "LLD", "lld-problems": "Machine coding",
        "senior": "Senior design"}
first_day = {}

def sd_minutes(g, t):
    m = int(t.get("minutes", 30))   # content minutes are pure reading time; a study task needs more
    return {"concepts": max(m, 25), "case-studies": max(m, 40), "lld-fundamentals": max(m, 25),
            "lld-problems": 90, "senior": max(m, 40)}[g]

def add_sd(day, g, t):
    first_day.setdefault(g, day)
    task(day, "sd", f"{KIND[g]}: {t['title']}", sd_minutes(g, t), f"/system-design/{g}/{t['id']}",
         "Code it yourself in Java with a 60-minute timer, then compare with the solution." if g == "lld-problems" else
         "Say the design out loud as if to an interviewer: requirements, numbers, API, data, then failures." if g in ("case-studies", "senior") else None)

study_days = [x for x in range(1, NEW_CONTENT_LAST + 1) if x not in MOCK_DAYS]
LLD_FROM = 13
b_days = [x for x in study_days if x in LONG_DAYS and x >= LLD_FROM]
b_slots = dict(zip(b_days, probs))
for x, (g, t) in b_slots.items():
    add_sd(x, g, t)
extra_probs = probs[len(b_days):]
# track A: one slot per study day, plus a second slot on long days that have no machine-coding problem
slots = []
for x in study_days:
    slots.append(x)
    if x in LONG_DAYS and x not in b_slots: slots.append(x)
for (g, t), x in zip(track_a, slots):
    add_sd(x, g, t)
overflow = track_a[len(slots):] + extra_probs
for g, t in overflow:   # rare: put leftovers on the lightest study days near the end
    x = min(study_days[-10:], key=load_of)
    add_sd(x, g, t)

# ---------- Traps: one a day (two on long days), matched to what you're studying ----------
FREQ_RANK = {"Very common": 0, "Common": 1}

# ---------- Fixed tasks (career, mocks, revision, rounds) are placed before the core fill ----------
CAREER = {
    2: ("Read the strategy guide and set your start date", "/guide"),
    3: ("Rewrite your resume: every bullet = action + tech + measurable result", "/guide"),
    5: ("Update LinkedIn headline, About, and Naukri profile; turn on Open to Work", "/guide"),
    10: ("Write your 2-minute project story and practise it out loud", "/guide"),
    14: ("Build a target list of 40 companies; find 2 referral contacts at each", "/guide"),
    18: ("Prepare 6 STAR stories from your work (incident, conflict, ownership, ambiguity, mentoring, failure)", "/guide"),
    21: ("Start applying: 10-15 applications + 3-5 referral requests per day from today", "/guide"),
    30: ("Review the application tracker; follow up on pending referrals", "/guide"),
    40: ("Research salary bands for your target companies; set walk-away and target numbers", "/guide"),
    50: ("Read the negotiation guide; prepare answers for expected CTC and notice period", "/guide"),
}
for dd, (title, link) in CAREER.items():
    task(dd, "career", title, 30, link, key=title)

MOCKS = {
    28: [("DSA mock, AI-off: 2 unseen Mediums in 60 minutes, explaining out loud", 60, "/rounds/dsa-live-coding")],
    35: [("DSA mock: 1 Medium + 1 Medium/Hard in 60 minutes, out loud", 60, "/rounds/dsa-live-coding"),
         ("System design mock: an unseen case study in 45 minutes", 45, "/rounds/system-design-senior")],
    42: [("Machine coding mock: an unseen LLD problem in 90 minutes, running code + tests", 90, "/rounds/machine-coding-lld")],
    49: [("Code review + debugging drill: review one snippet, debug one incident scenario", 45, "/rounds/code-review-round"),
         ("System design mock: a production-flavoured senior prompt in 45 minutes", 45, "/rounds/system-design-senior")],
    53: [("Practical coding mock: build a small component with changing requirements and tests", 75, "/rounds/practical-coding")],
    56: [("Full mock loop: coding (45m) + design (45m) + behavioral (30m) back to back", 120, "/rounds")],
    59: [("DSA mock: 2 unseen problems in 60 minutes", 60, "/rounds/dsa-live-coding"),
         ("Behavioral mock: answer 5 questions with your STAR stories, recorded", 30, "/rounds/behavioral-leadership")],
}
for dd, items in MOCKS.items():
    for title, minutes, link in items:
        task(dd, "mock", title, minutes, link, key=title)
for dd in sorted(REVISE_DAYS):
    task(dd, "revise", "Revise your starred items and notes", 40, "/revision")
for dd in range(56, DAYS + 1):
    task(dd, "revise", "Flashcards: frequently asked questions you haven't nailed (Java, Spring, SQL)", 40,
         "/core/java?view=cards&filter=frequent-todo")
    task(dd, "revise", "High-yield focus list: close the gaps in Tier 1", 45, "/focus")

# ---------- Core: priority queue filled into each day's remaining budget ----------
# (subject id, chapters to schedule (1-based) or None for all[, max batches of frequent questions])
CORE_ORDER = [
    ("java", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]),
    ("concurrency-practical", [1, 2, 3, 4, 5, 6, 7]),
    ("spring-boot", None),
    ("sql", [1, 2, 3, 4, 5, 6, 7, 8, 10]),
    ("microservices", [1, 2, 3, 4, 5, 6, 7]),
    ("production-debugging", [1, 2, 4, 5, 6, 8]),
    ("angular", [3, 4, 6, 7, 11]),        # on the resume: change detection, signals, DI, RxJS, performance
    ("performance", [1, 2, 4, 5, 6]),
    ("testing-code-review", [1, 2, 3, 5, 6, 7]),
    ("behavioral", [1, 2, 3, 4, 5]),
    ("ai-assisted-engineering", [1, 2, 3, 5, 6]),
    ("security", [1, 3, 4, 5]),
    ("senior-leadership", [1, 2, 4, 8]),
    ("javascript-typescript", [2, 5, 6]), # closures, event loop, promises
    # CS fundamentals: lower yield for senior backend loops beyond OAs: the few chapters that keep coming up, plus one
    # batch of the most-asked questions each
    ("cn", [3, 5, 6], 1),                 # HTTP versions, what happens when you type a URL, cookies/CORS
    ("os", [1, 4], 1),                    # processes vs threads, deadlocks
    ("oop-design-patterns", [], 1),       # the theory is covered by the LLD fundamentals in the design track
    ("dbms", [], 1),
    ("cloud-devops", [1, 3, 4, 5, 6]),    # AWS map, Docker, Kubernetes essentials + production, CI/CD
]
QA_BATCH = 10
core_queue = []   # (subject id, kind, payload)
qa_cap = {}
for sid, chapters, *cap in CORE_ORDER:
    s = subjects.get(sid)
    if not s:
        continue
    idxs = list(range(1, len(s["notes"]) + 1)) if chapters is None else [c for c in chapters if c <= len(s["notes"])]
    freq = sum(1 for q in s["qa"] if q.get("frequent"))
    batches = math.ceil(freq / QA_BATCH)
    if cap:
        batches = qa_cap[sid] = min(batches, cap[0])
    every = max(1, math.ceil(len(idxs) / max(1, batches))) if idxs else 1
    b = 0
    for k, idx in enumerate(idxs, 1):
        core_queue.append((sid, "chapter", idx))
        if k % every == 0 and b < batches:
            core_queue.append((sid, "qa", b)); b += 1
    while b < batches:
        core_queue.append((sid, "qa", b)); b += 1

# Interview-round playbooks: placed on the day their material starts (computed below), else a fixed day.
ROUND_FIXED = {"dsa-live-coding": 1, "online-assessment": 4, "project-deep-dive": 10, "resume-deep-dive": 12,
               "practical-coding": 26, "hiring-manager-and-hr": 50}
ROUND_ON_SUBJECT = {"concurrency-round": "concurrency-practical", "debugging-production-round": "production-debugging",
                    "code-review-round": "testing-code-review", "behavioral-leadership": "behavioral",
                    "ai-assisted-coding": "ai-assisted-engineering"}
ROUND_ON_SD = {"machine-coding-lld": "lld-problems", "system-design-senior": "case-studies"}

def add_round(day, rid):
    r = rounds.get(rid)
    title = r["title"] if r else rid.replace("-", " ").title()
    task(day, "round", f"Round playbook: {title} (how it's scored, how to ace it)", 25, f"/rounds/{rid}")

for rid, dd in ROUND_FIXED.items():
    add_round(dd, rid)
for rid, g in ROUND_ON_SD.items():
    if g in first_day: add_round(first_day[g], rid)

subject_start = {}
dropped = []
qi = 0
for dd in range(1, NEW_CONTENT_LAST + 1):
    pending_rounds = []
    while qi < len(core_queue):
        sid, kind, payload = core_queue[qi]
        s = subjects[sid]
        if kind == "chapter":
            n = s["notes"][payload - 1]
            minutes = 20 if len(n["content"].split()) < 600 else 25   # dense notes: ~25 words a minute with code
            title, link = f"{s['name']}: read \"{n['title']}\"", f"/core/{sid}?chapter={payload}"
        else:
            freq = sum(1 for q in s["qa"] if q.get("frequent"))
            batches = qa_cap.get(sid, math.ceil(freq / QA_BATCH))
            n_q = freq // batches + (1 if payload < freq % batches else 0) if batches * QA_BATCH >= freq else QA_BATCH
            title = f"{s['name']}: answer {n_q} frequently asked questions out loud" + \
                    (f" (set {payload + 1} of {batches})" if batches > 1 else " (the most-asked ones)")
            minutes, link = 5 * math.ceil(2.5 * n_q / 5), f"/core/{sid}?view=qa&filter=frequent-todo"
        # always place at least one core item per day; otherwise stop at the budget
        has_core = any(t["type"] == "core" for t in days[dd])
        reserve = 20 if dd in LONG_DAYS else 10   # the day's trap(s), added below
        if has_core and load_of(dd) + minutes > budget(dd) - reserve:
            break
        if sid not in subject_start:
            subject_start[sid] = dd
            for rid, subj in ROUND_ON_SUBJECT.items():
                if subj == sid: pending_rounds.append(rid)
        task(dd, "core", title, minutes, link, "Open the model answer only after saying yours. Tick the ones you nail."
             if kind == "qa" else None, key=f"{sid}-{kind}-{payload}")
        qi += 1
    for rid in pending_rounds:
        add_round(dd, rid)
while qi < len(core_queue):
    dropped.append(core_queue[qi]); qi += 1
for rid, subj in ROUND_ON_SUBJECT.items():
    if subj not in subject_start:
        add_round(NEW_CONTENT_LAST, rid)

# ---------- Traps ----------
SUBJECT_AREA = {"java": "java", "concurrency-practical": "concurrency", "spring-boot": "spring", "sql": "sql",
                "microservices": "distributed-systems", "production-debugging": "system-design", "performance": "jpa-hibernate",
                "testing-code-review": "api-design", "behavioral": "behavioral", "security": "api-design",
                "senior-leadership": "behavioral", "cloud-devops": "distributed-systems", "ai-assisted-engineering": "dsa",
                "angular": "angular-js", "javascript-typescript": "angular-js", "cn": "os-networking", "os": "os-networking",
                "dbms": "sql", "oop-design-patterns": "java"}
trap_pool = sorted(traps, key=lambda t: (FREQ_RANK.get(t.get("frequency"), 2)))
used_traps = set()
def next_trap(areas):
    for area in areas:
        for t in trap_pool:
            if t["id"] not in used_traps and t["area"] == area:
                return t
    return next((t for t in trap_pool if t["id"] not in used_traps), None)
for dd in range(1, DAYS + 1):
    core_sid = next((t["link"].split("/")[2].split("?")[0] for t in days[dd] if t["type"] == "core"), None)
    pats = [t["link"].split("/")[2] for t in days[dd] if t["type"] == "dsa"]
    areas = [SUBJECT_AREA.get(core_sid)] if core_sid else []
    if any(t["type"] == "sd" for t in days[dd]): areas.append("system-design")
    areas += ["dsa"] if pats else []
    if core_sid == "spring-boot": areas.insert(1, "jpa-hibernate")
    for _ in range(2 if dd in LONG_DAYS else 1):
        t = next_trap([a for a in areas if a])
        if not t: break
        used_traps.add(t["id"])
        task(dd, "trap", f"Trap: {t['title']}", 10, f"/traps/{t['id']}",
             "Commit to an answer before revealing. Most candidates get this one wrong.")

# ---------- AI course (optional, long days only) ----------
lessons = [(m, l) for m in ai for l in m["lessons"]]
li = 0
for dd in sorted(LONG_DAYS):
    if li < len(lessons) and dd <= NEW_CONTENT_LAST:
        m, l = lessons[li]
        task(dd, "ai", f"(Optional) AI course: {l['title']}", int(l.get("minutes", 30)), f"/ai/{m['id']}/{l['id']}")
        li += 1

# ---------- day titles ----------
WEEKS = [
    (1, "Foundations", "Arrays, hashing, two pointers, sliding window; Core Java; how design interviews work; fix your resume."),
    (2, "Java depth and concurrency", "Stacks, binary search, linked lists; collections, JVM, practical concurrency; caching, sharding."),
    (3, "Spring and data", "Trees, tries, heaps; Spring Boot, JPA, transactions; SQL and InnoDB; replication and consistency."),
    (4, "Distributed systems", "Backtracking and graphs; microservices; queues, APIs, rate limiting; first LLD and case studies. Start applying."),
    (5, "Senior signals", "Graphs and DP; production debugging, performance, testing and code review; senior design topics."),
    (6, "Breadth that gets asked", "DP, greedy, intervals; behavioral stories, security, cloud, AI-assisted engineering; machine coding."),
    (7, "Interview mode", "Remaining patterns and re-solves; Angular, JS and networking essentials; mocks every few days."),
    (8, "Polish", "Re-solve must-dos; behavioral and leadership stories; LLD practice; mocks."),
    (9, "Final revision", "Re-solve, flashcards, the focus list, mocks. Then start the 14-day Final Round."),
]
out_days = []
order = {"career": 0, "round": 1, "trap": 2, "dsa": 3, "core": 4, "sd": 5, "mock": 6, "revise": 7, "ai": 8}
for dd in range(1, DAYS + 1):
    ts = sorted(days[dd], key=lambda t: order[t["type"]])
    pats = []
    for t in ts:
        if t["type"] == "dsa" and t.get("link", "").count("/") >= 2:
            pid = t["link"].split("/")[2]
            name = next((p["name"] for p in dsa if p["id"] == pid), pid)
            if name not in pats: pats.append(name)
    cores = []
    for t in ts:
        if t["type"] == "core":
            name = t["title"].split(":")[0]
            if name not in cores: cores.append(name)
    sd = next((t["title"].split(": ", 1)[1] for t in ts if t["type"] == "sd"), None)
    if dd in MOCK_DAYS: title = "Mock day"
    elif dd > NEW_CONTENT_LAST: title = "Final revision"
    elif pats: title = " + ".join(pats[:2])
    elif cores: title = " + ".join(cores[:2])
    else: title = "Revision"
    focus_bits = []
    if pats: focus_bits.append("DSA: " + ", ".join(pats))
    if cores: focus_bits.append(", ".join(cores))
    if sd: focus_bits.append("Design: " + sd)
    focus_bits.append(f"~{round(load_of(dd) / 60, 1)} h")
    out_days.append({"day": dd, "week": (dd - 1) // 7 + 1, "title": title, "focus": " · ".join(focus_bits), "tasks": ts})

normal_loads = [load_of(x) for x in range(1, DAYS + 1) if x not in LONG_DAYS]
long_loads = [load_of(x) for x in range(1, DAYS + 1) if x in LONG_DAYS]
def hours(loads):
    lo, hi = round(min(loads) / 60 * 2) / 2, round(max(loads) / 60 * 2) / 2
    fmt = lambda h: f"{h:g}"
    return fmt(lo) if lo == hi else f"{fmt(lo)}-{fmt(hi)}"

plan = {
    "intro": "This plan is **selective on purpose**: it schedules the high-yield part of the site (must-do problems, "
             "frequently asked questions, the senior topics product companies probe in 2026-27) and leaves the rest as "
             "optional depth. Each day has **DSA**, a **core** block, a **design** topic and one **trap** (a question most "
             "people get wrong). Interview-round playbooks appear on the day their material starts. Long days (6th and 7th "
             "of each week) carry more and an optional AI lesson. The last week before revision is lighter on purpose: use "
             "it to catch up. Tick tasks as you go; the **Daily Routine** page tracks your streak. After day 60, move to "
             "the **Final Round**.",
    "hoursPerDay": f"About {hours(normal_loads)} hours on normal days and {hours(long_loads)} on long days (optional AI "
                   "lessons not counted). If a day runs over, finish it the next morning; the dashboard tracks what is pending.",
    "weeks": [{"week": w, "title": t, "goal": g} for w, t, g in WEEKS],
    "days": out_days,
}
(C / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))
loads = [load_of(x) for x in range(1, DAYS + 1)]
print("days:", len(out_days), "tasks:", sum(len(x["tasks"]) for x in out_days),
      "| dsa problems:", total_problems, "| sd topics:", len(sd_queue), "| traps:", len(used_traps), "of", len(traps),
      "| core items:", len(core_queue) - len(dropped), "of", len(core_queue))
print("minutes/day min/avg/max:", min(loads), round(sum(loads) / len(loads)), max(loads))
if dropped:
    print("left optional (did not fit):", ", ".join(f"{s}:{k}{p}" for s, k, p in dropped))
for x in out_days[:3] + out_days[-2:]:
    print(x["day"], x["title"], "|", x["focus"], "|", len(x["tasks"]))
