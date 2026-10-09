"""
Builds frontend/public/content/focus.json: the High-Yield Focus list.

A short, opinionated checklist of what product companies ask most in 2026-27, split into two tiers:
  Tier 1 "Must master": the ~20% that covers most interview loops.
  Tier 2 "Should know": the next layer, once Tier 1 is solid.
Everything else on the site is optional depth.

Item keys must match frontend/src/app/core/catalog.service.ts `keys.*` (dsa:, sd:, note:, qa:, trap:, round:),
so ticking an item here is the same as ticking it on its own page. validate_content.py checks this.
Re-run after changing content: python3 content-gen/build_focus.py
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
C = ROOT / "frontend/public/content"

def load(name, default):
    p = C / name
    return json.loads(p.read_text()) if p.exists() else default

def first_sentence(text, limit=150):
    text = re.sub(r"[*_`#>]", "", (text or "").strip()).replace("\n", " ")
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    s = m.group(1) if m else text
    return s if len(s) <= limit else s[:limit - 1].rsplit(" ", 1)[0] + "…"

dsa = sorted(load("dsa-part1.json", {"patterns": []})["patterns"] + load("dsa-part2.json", {"patterns": []})["patterns"],
             key=lambda p: p["order"])
hld = load("system-design-hld.json", {"concepts": [], "caseStudies": []})
lld = load("system-design-lld.json", {"fundamentals": [], "problems": []})
senior_sd = load("system-design-senior.json", {"topics": []})["topics"]
subjects = {s["id"]: s for f in ("core-backend.json", "core-cs.json", "core-senior-1.json", "core-senior-2.json")
            for s in load(f, {"subjects": []})["subjects"]}
traps = load("traps-1.json", {"traps": []})["traps"] + load("traps-2.json", {"traps": []})["traps"]
rounds = sorted(load("rounds.json", {"rounds": []})["rounds"], key=lambda r: r["order"])

def dsa_item(p, q):
    return {"key": f"dsa:{q['id']}", "title": f"{q['title']} ({q['difficulty']})", "link": f"/dsa/{p['id']}/{q['id']}",
            "kind": p["name"], "why": ("Asked at " + ", ".join(q.get("companies", [])[:4])) if q.get("companies") else None}

def qa_items(sid, limit, skip=0, frequent_only=True):
    s = subjects.get(sid)
    if not s: return []
    qs = [q for q in s["qa"] if q.get("frequent") or not frequent_only][skip:skip + limit]
    return [{"key": f"qa:{q.get('id') or q['q']}", "title": q["q"], "link": f"/core/{sid}?view=qa&filter=frequent",
             "kind": s["name"]} for q in qs]

def note_items(sid, chapters=None):
    s = subjects.get(sid)
    if not s: return []
    idxs = chapters or range(1, len(s["notes"]) + 1)
    return [{"key": f"note:{sid}:{s['notes'][i - 1]['id']}", "title": s["notes"][i - 1]["title"],
             "link": f"/core/{sid}?chapter={i}", "kind": s["name"]} for i in idxs if i <= len(s["notes"])]

SD_GROUPS = {"concepts": hld["concepts"], "case-studies": hld["caseStudies"], "lld-fundamentals": lld["fundamentals"],
             "lld-problems": lld["problems"], "senior": senior_sd}
SD_KIND = {"concepts": "HLD concept", "case-studies": "Case study", "lld-fundamentals": "LLD", "lld-problems": "Machine coding",
           "senior": "Senior design"}
def sd_items(group, ids):
    by = {t["id"]: t for t in SD_GROUPS[group]}
    return [{"key": f"sd:{i}", "title": by[i]["title"], "link": f"/system-design/{group}/{i}", "kind": SD_KIND[group],
             "why": first_sentence(by[i].get("summary"))} for i in ids if i in by]

def trap_item(t):
    return {"key": f"trap:{t['id']}", "title": t["title"], "link": f"/traps/{t['id']}", "kind": t["area"],
            "why": f"{t.get('frequency', '')}. Most candidates answer this wrong."}

def round_item(r):
    return {"key": f"round:{r['id']}", "title": f"{r['icon']} {r['title']}", "link": f"/rounds/{r['id']}",
            "kind": "Round", "why": f"{r.get('frequency', '')} · {r.get('weight', '')}".strip(" ·")}

def clean(items):
    seen, out = set(), []
    for it in items:
        if it["key"] in seen: continue
        seen.add(it["key"])
        out.append({k: v for k, v in it.items() if v})
    return out

def group(gid, title, description, items):
    items = clean(items)
    return {"id": gid, "title": title, "description": description, "items": items} if items else None

# ---------- Tier 1 ----------
must = [dsa_item(p, q) for p in dsa for q in p["problems"] if q.get("mustDo")]
STACK = ["java", "spring-boot", "sql", "microservices"]
TOP_QA = 15
SD_T1 = {
    "concepts": ["back-of-envelope", "caching", "databases-sql-vs-nosql", "indexing-internals", "replication",
                 "sharding-partitioning", "consistent-hashing", "cap-pacelc-consistency", "message-queues", "api-design",
                 "rate-limiting", "microservices-patterns"],
    "case-studies": ["url-shortener", "rate-limiter-design", "notification-system", "chat-whatsapp", "ecommerce-flipkart-checkout"],
    "senior": ["failure-handling-resilience", "idempotency-exactly-once", "observability-slos-at-scale", "payment-processing-reliability"],
    "lld-problems": ["parking-lot", "splitwise", "rate-limiter-lld"],
}
ROUNDS_T1 = ["dsa-live-coding", "resume-deep-dive", "system-design-senior", "machine-coding-lld", "debugging-production-round",
             "behavioral-leadership"]
# Tier 1 traps: up to 3 "Very common" ones per area, so the list stays short; the rest go to Tier 2
TRAPS_PER_AREA = 3
very_common, per_area = [], {}
for t in traps:
    if t.get("frequency") == "Very common" and per_area.get(t["area"], 0) < TRAPS_PER_AREA:
        very_common.append(t)
        per_area[t["area"]] = per_area.get(t["area"], 0) + 1
t1_ids = {t["id"] for t in very_common}
other_traps = [t for t in traps if t["id"] not in t1_ids]

tier1 = [
    group("t1-dsa", "Must-do coding problems",
          "The problems behind most coding rounds. Re-solve each until you can explain it out loud in under 25 minutes.", must),
    group("t1-stack", "Your stack, in depth (the resume deep-dive)",
          "Interviewers probe the stack on your resume for 45-60 minutes. These are the most-asked questions on Java, "
          "Spring Boot, SQL and microservices.", [x for sid in STACK for x in qa_items(sid, TOP_QA)]),
    group("t1-senior", "Senior signals: concurrency and production debugging",
          "What separates a senior from a mid-level answer in 2026-27 loops: naming the exact race, and debugging a live incident calmly.",
          note_items("concurrency-practical") + note_items("production-debugging")),
    group("t1-design", "System design essentials",
          "The concepts that come up in almost every design round, the case studies asked most, and the production-flavoured "
          "topics seniors are judged on.", [x for g, ids in SD_T1.items() for x in sd_items(g, ids)]),
    group("t1-traps", "Traps most people get wrong",
          "Short questions with a tempting wrong answer. Getting these right is what makes an interviewer write \"strong\".",
          [trap_item(t) for t in very_common]),
    group("t1-rounds", "Know how each core round is scored",
          "Read the rubric before you practise, so you practise what earns points.",
          [round_item(r) for r in rounds if r["id"] in ROUNDS_T1]),
]

# ---------- Tier 2 ----------
selected_ids = {x["key"] for x in must}
plan_extra = []
for p in dsa:
    probs = sorted((q for q in p["problems"] if f"dsa:{q['id']}" not in selected_ids),
                   key=lambda q: -len(q.get("companies", [])))
    for q in probs[:2 if len(p["problems"]) >= 10 else 1]:
        plan_extra.append(dsa_item(p, q))
SENIOR_T2 = ["performance", "testing-code-review", "security", "cloud-devops", "ai-assisted-engineering", "senior-leadership"]
BREADTH = [("angular", 10), ("javascript-typescript", 8), ("oop-design-patterns", 8), ("cn", 8), ("os", 6), ("dbms", 5),
           ("behavioral", 10)]
SD_T2 = {
    "concepts": ["load-balancing", "transactions-isolation", "cdn-blob-storage", "observability", "security-auth",
                 "unique-id-generation", "search-elasticsearch"],
    "case-studies": ["news-feed", "ticket-booking-bookmyshow", "payment-system-upi", "ride-hailing-uber",
                     "food-delivery-swiggy", "search-autocomplete"],
    "senior": [t["id"] for t in senior_sd if t["id"] not in SD_T1["senior"]],
    "lld-problems": ["snake-and-ladder", "bookmyshow-lld", "elevator-system", "pub-sub-message-queue",
                     "in-memory-key-value-store", "cab-booking-lld"],
}
tier2 = [
    group("t2-dsa", "More frequently asked problems",
          "The most-asked problems after the must-dos (one or two per pattern), for range once the must-dos are solid.", plan_extra),
    group("t2-stack", "Your stack: the next layer of questions",
          "More frequently asked questions on your own stack.", [x for sid in STACK for x in qa_items(sid, 12, skip=TOP_QA)]),
    group("t2-senior", "Senior topics: performance, testing, security, cloud, AI, leadership",
          "The rest of the senior 2027 subjects. One chapter a day is plenty.", [x for sid in SENIOR_T2 for x in note_items(sid)]),
    group("t2-breadth", "Breadth that still gets asked",
          "Frontend, CS fundamentals and behavioral: only the questions that keep showing up.",
          [x for sid, n in BREADTH for x in qa_items(sid, n)]),
    group("t2-design", "More design practice", "Case studies, senior topics and machine-coding problems for range.",
          [x for g, ids in SD_T2.items() for x in sd_items(g, ids)]),
    group("t2-traps", "More traps", "The rest of the trap collection.", [trap_item(t) for t in other_traps]),
    group("t2-rounds", "The other rounds", "Rounds that some companies run: know the format before you walk in.",
          [round_item(r) for r in rounds if r["id"] not in ROUNDS_T1]),
]

focus = {
    "intro": "**Learn less, master more.** This list is the short version of the whole site: what most product companies "
             "actually ask in 2026-27, picked from the research behind the Interview Rounds guide. Finish **Tier 1** before "
             "anything else; it covers most of what a typical loop tests. **Tier 2** adds range. Everything not listed here is "
             "optional depth. Ticks here are the same as ticks on each item's own page.",
    "tiers": [
        {"id": "tier-1", "title": "Tier 1 · Must master",
         "description": "If you only have time for one thing each day, take it from here.",
         "groups": [g for g in tier1 if g]},
        {"id": "tier-2", "title": "Tier 2 · Should know",
         "description": "Once Tier 1 is mostly green, widen your range with these.",
         "groups": [g for g in tier2 if g]},
    ],
}
(C / "focus.json").write_text(json.dumps(focus, ensure_ascii=False, indent=1))
for t in focus["tiers"]:
    print(t["id"], sum(len(g["items"]) for g in t["groups"]), "items:",
          ", ".join(f"{g['id']}={len(g['items'])}" for g in t["groups"]))
