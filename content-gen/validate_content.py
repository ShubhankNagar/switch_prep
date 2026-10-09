"""
Validates frontend/public/content/*.json: required files and fields, unique ids (per progress-key namespace),
MCQ answer indexes, that every site link in the plan, rounds and focus list points at real content, and that
every focus-list key resolves to a trackable item. Exit code 1 on any error.
Run: python3 content-gen/validate_content.py
"""
import json, pathlib, sys

C = pathlib.Path(__file__).resolve().parent.parent / "frontend/public/content"
errors, counts = [], {}

def load(name, optional=False):
    p = C / name
    if not p.exists():
        if not optional:
            errors.append(f"missing file {name}")
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"{name}: invalid JSON ({e})")
        return None

def need(obj, fields, where):
    for f in fields:
        if f not in obj or obj[f] in (None, "", []) and f not in ("leetcode", "askedAt", "companies", "sources", "resources", "quiz", "interviewQuestions"):
            errors.append(f"{where}: missing '{f}'")

def check_mcq(m, where):
    need(m, ["q", "options", "answer", "explanation"], where)
    if not isinstance(m.get("options"), list) or len(m.get("options", [])) != 4:
        errors.append(f"{where}: needs exactly 4 options")
    elif not isinstance(m.get("answer"), int) or not 0 <= m["answer"] < 4:
        errors.append(f"{where}: answer must be 0-3")

def unique(ids, where):
    seen = set()
    for i in ids:
        if i in seen:
            errors.append(f"{where}: duplicate id {i}")
        seen.add(i)

# DSA
dsa = []
for f in ("dsa-part1.json", "dsa-part2.json"):
    d = load(f)
    if d: dsa += d["patterns"]
unique([p["id"] for p in dsa], "dsa patterns")
unique([q["id"] for p in dsa for q in p["problems"]], "dsa problems")
for p in dsa:
    need(p, ["id", "name", "order", "intro", "problems"], f"dsa/{p.get('id')}")
    for q in p["problems"]:
        need(q, ["id", "title", "difficulty", "leetcode", "summary", "approach", "solution", "time", "space"], f"dsa/{p['id']}/{q.get('id')}")
        if q.get("difficulty") not in ("Easy", "Medium", "Hard"):
            errors.append(f"dsa/{q['id']}: bad difficulty")
counts["dsa problems"] = sum(len(p["problems"]) for p in dsa)

# System design
sd_ids = {}
hld, lld = load("system-design-hld.json"), load("system-design-lld.json")
for group, data, key in (("concepts", hld, "concepts"), ("case-studies", hld, "caseStudies"),
                         ("lld-fundamentals", lld, "fundamentals"), ("lld-problems", lld, "problems")):
    topics = (data or {}).get(key, [])
    sd_ids[group] = {t["id"] for t in topics}
    unique([t["id"] for t in topics], f"sd/{group}")
    for t in topics:
        need(t, ["id", "title", "order", "level", "minutes", "summary", "content", "keyPoints"], f"sd/{group}/{t.get('id')}")
    counts[f"sd {group}"] = len(topics)
senior = load("system-design-senior.json")
topics = (senior or {}).get("topics", [])
sd_ids["senior"] = {t["id"] for t in topics}
for t in topics:
    need(t, ["id", "title", "order", "level", "minutes", "summary", "content", "keyPoints", "kind"], f"sd/senior/{t.get('id')}")
    if t.get("kind") not in ("concept", "case-study"):
        errors.append(f"sd/senior/{t.get('id')}: kind must be concept or case-study")
counts["sd senior"] = len(topics)
# progress keys are sd:{id} without the group, so ids must be unique across groups
unique([i for g in sd_ids.values() for i in g], "sd (all groups)")

# Core subjects
subjects = []
for f in ("core-backend.json", "core-cs.json", "core-senior-1.json", "core-senior-2.json"):
    d = load(f)
    if d: subjects += d["subjects"]
unique([s["id"] for s in subjects], "subjects")
unique([q.get("id") for s in subjects for q in s["qa"]], "core qa")
for s in subjects:
    need(s, ["id", "name", "order", "notes", "qa"], f"core/{s.get('id')}")
    unique([n["id"] for n in s["notes"]], f"core/{s['id']} notes")
    for q in s["qa"]:
        need(q, ["id", "q", "a"], f"core/{s['id']}/{q.get('id')}")
counts["core notes"] = sum(len(s["notes"]) for s in subjects)
counts["core questions"] = sum(len(s["qa"]) for s in subjects)

# Final round
days = []
for f in ("final-round-1.json", "final-round-2.json"):
    d = load(f)
    if d: days += d["days"]
if sorted(d["day"] for d in days) != list(range(1, 15)):
    errors.append(f"final round: expected days 1-14, got {sorted(d['day'] for d in days)}")
unique([x["id"] for d in days for x in d["mcqs"] + d["coding"] + d["theory"]], "final round items")
for d in days:
    for m in d["mcqs"]:
        check_mcq(m, f"final/d{d['day']}/{m.get('id')}")
    for c in d["coding"]:
        need(c, ["id", "title", "difficulty", "statement", "hints", "solution", "explanation"], f"final/d{d['day']}/{c.get('id')}")
    for t in d["theory"]:
        need(t, ["id", "q", "a"], f"final/d{d['day']}/{t.get('id')}")
counts["final mcqs"] = sum(len(d["mcqs"]) for d in days)
counts["final coding"] = sum(len(d["coding"]) for d in days)
counts["final theory"] = sum(len(d["theory"]) for d in days)

# AI course
mods = []
for f in ("ai-course-1.json", "ai-course-2.json"):
    d = load(f)
    if d: mods += d["modules"]
unique([m["id"] for m in mods], "ai modules")
unique([l["id"] for m in mods for l in m["lessons"]], "ai lessons")
for m in mods:
    need(m, ["id", "order", "title", "level", "lessons", "project"], f"ai/{m.get('id')}")
    for l in m["lessons"]:
        need(l, ["id", "title", "content", "exercise"], f"ai/{m['id']}/{l.get('id')}")
        for i, qz in enumerate(l.get("quiz", [])):
            check_mcq(qz, f"ai/{l['id']}/quiz{i}")
counts["ai modules"] = len(mods)
counts["ai lessons"] = sum(len(m["lessons"]) for m in mods)

# Traps
TRAP_AREAS = {"java", "concurrency", "spring", "jpa-hibernate", "sql", "dsa", "system-design", "distributed-systems",
              "api-design", "angular-js", "os-networking", "behavioral"}
traps = []
for f in ("traps-1.json", "traps-2.json"):
    d = load(f)
    if d: traps += d["traps"]
unique([t["id"] for t in traps], "traps")
for t in traps:
    w = f"traps/{t.get('id')}"
    need(t, ["id", "area", "title", "level", "frequency", "prompt", "commonWrongAnswer", "whyPeopleGetItWrong", "correct",
             "interviewTip"], w)
    if t.get("area") not in TRAP_AREAS:
        errors.append(f"{w}: unknown area {t.get('area')}")
    if t.get("options") is not None:
        opts, ans = t["options"], t.get("answer")
        if not isinstance(opts, list) or not 2 <= len(opts) <= 5:
            errors.append(f"{w}: options must be a list of 2-5")
        elif not isinstance(ans, int) or not 0 <= ans < len(opts):
            errors.append(f"{w}: answer must index into options")
counts["traps"] = len(traps)

# Interview rounds
rounds_file = load("rounds.json")
rounds = (rounds_file or {}).get("rounds", [])
unique([r["id"] for r in rounds], "rounds")
for r in rounds:
    need(r, ["id", "order", "title", "icon", "summary", "format", "whatTheyTest", "rubric", "howToAce", "walkthrough",
             "commonFailures", "practice"], f"rounds/{r.get('id')}")
if rounds_file and not rounds_file.get("trends"):
    errors.append("rounds.json: missing 'trends'")
counts["interview rounds"] = len(rounds)

# ---------- links and keys ----------
dsa_index = {p["id"]: {q["id"] for q in p["problems"]} for p in dsa}
subject_ids = {s["id"] for s in subjects}
ai_index = {m["id"]: {l["id"] for l in m["lessons"]} for m in mods}
trap_ids = {t["id"] for t in traps}
round_ids = {r["id"] for r in rounds}
STATIC = {"/guide", "/revision", "/system-design", "/final-round", "/plan", "/dsa", "/core", "/ai", "/traps", "/rounds",
          "/habits", "/focus", "/account", "/"}

def link_ok(link):
    path = link.split("?")[0]
    if path in STATIC:
        return True
    parts = path.strip("/").split("/")
    if parts[0] == "dsa":
        return parts[1] in dsa_index and (len(parts) == 2 or parts[2] in dsa_index[parts[1]])
    if parts[0] == "system-design":
        return len(parts) == 3 and parts[2] in sd_ids.get(parts[1], set())
    if parts[0] == "core":
        return len(parts) == 2 and parts[1] in subject_ids
    if parts[0] == "ai":
        return parts[1] in ai_index and (len(parts) == 2 or parts[2] in ai_index[parts[1]])
    if parts[0] == "final-round":
        return len(parts) == 2 and parts[1].isdigit() and 1 <= int(parts[1]) <= 14
    if parts[0] == "traps":
        return len(parts) == 2 and parts[1] in trap_ids
    if parts[0] == "rounds":
        return len(parts) == 2 and parts[1] in round_ids
    return False

for r in rounds:
    for pr in r.get("practice", []):
        if not link_ok(pr.get("link", "")):
            errors.append(f"rounds/{r['id']}: broken practice link {pr.get('link')}")

# Plan
plan = load("plan.json")
if plan:
    for d in plan["days"]:
        unique([t.get("id") for t in d["tasks"]], f"plan day {d['day']} task ids")
        for t in d["tasks"]:
            if not t.get("id"):
                errors.append(f"plan day {d['day']}: task without id ({t.get('title')})")
            if t.get("link") and not link_ok(t["link"]):
                errors.append(f"plan day {d['day']}: broken link {t['link']}")
    counts["plan tasks"] = sum(len(d["tasks"]) for d in plan["days"])

# Focus list: keys must be real progress keys (same format as catalog.service.ts keys.*)
valid_keys = {f"dsa:{q}" for qs in dsa_index.values() for q in qs}
valid_keys |= {f"sd:{i}" for g in sd_ids.values() for i in g}
valid_keys |= {f"note:{s['id']}:{n['id']}" for s in subjects for n in s["notes"]}
valid_keys |= {f"qa:{q.get('id') or q['q']}" for s in subjects for q in s["qa"]}
valid_keys |= {f"trap:{i}" for i in trap_ids} | {f"round:{i}" for i in round_ids}
focus = load("focus.json")
if focus:
    n = 0
    for tier in focus["tiers"]:
        for g in tier["groups"]:
            unique([it["key"] for it in g["items"]], f"focus/{g['id']}")
            for it in g["items"]:
                n += 1
                if it["key"] not in valid_keys:
                    errors.append(f"focus/{g['id']}: unknown key {it['key']}")
                if not link_ok(it.get("link", "")):
                    errors.append(f"focus/{g['id']}: broken link {it.get('link')}")
    counts["focus items"] = n

guide = load("guide.json")
counts["guide sections"] = len((guide or {}).get("sections", []))

for k, v in counts.items():
    print(f"{k:>22}: {v}")
if errors:
    print(f"\n{len(errors)} problem(s):")
    for e in errors[:100]:
        print(" -", e)
    sys.exit(1)
print("\nAll content valid.")
