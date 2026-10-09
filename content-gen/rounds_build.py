"""Build frontend/public/content/rounds.json (Interview Rounds 2027) and validate it.

Run: python3 content-gen/rounds_build.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rounds_common import md, words  # noqa: E402
from rounds_p1 import ROUNDS_P1  # noqa: E402
from rounds_p2 import ROUNDS_P2  # noqa: E402
from rounds_p3 import ROUNDS_P3  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "frontend", "public", "content", "rounds.json")

TRENDS = md("""
**What changed between 2025 and 2027**

1. **AI split the loop into AI-off and AI-on rounds.** Live algorithm rounds stay AI-off almost everywhere, and
   interviewers now interrupt with "why this structure?" to check the reasoning is yours. At the same time, Meta
   (since October 2025) replaced one of its two coding rounds with an AI-enabled round, Google is piloting an
   AI-assisted code-comprehension round in 2026, and Canva expects candidates to use AI. Take-homes now come with a live walkthrough.
2. **"Real work" formats grew fast.** Debug-this-code, code review, and practical coding with changing requirements
   and tests are replacing some puzzle rounds. All ten Stripe experiences in one 2026 analysis were practical work.
3. **DSA didn't die. It became the gate.** In the same analysis, LinkedIn (8/8), Google (7/9) and Amazon (6/8)
   still asked classic DSA. In India, Flipkart, Uber, Swiggy, Amazon, PhonePe and Goldman Sachs loops in 2025-26 all
   included an OA or a DSA round. Problems are mostly medium, and *explaining* counts as much as solving.
4. **System design moved down to SDE-2.** Flipkart, Uber, Razorpay and Amazon SDE-2 loops in 2025-26 all had a
   high-level design round, with prompts about payments, failures and retries rather than "design Twitter".
5. **Depth rounds decide the level.** Resume and project deep dives, hiring manager rounds and behavioral rounds can
   downlevel a strong coder: Atlassian and Amazon both do it. India's machine-coding round (Flipkart, PhonePe,
   Razorpay, Uber, Swiggy) is still the main filter for SDE-2.
6. **The market got stricter.** Fewer openings and more applicants mean borderline rounds fail more often. With
   offer dropout high, companies probe notice periods and joining intent harder than before.

**What this means for Raj: priorities, in order**

1. **DSA fluency in Java for OAs and live rounds (about 25% of prep time).** Mediums across about 15 patterns,
   solved out loud. Don't grind hards: a few per pattern is enough.
2. **Machine coding plus concurrency (about 20%).** This is the round that separates SDE-2 offers at Indian product
   companies, and a Java developer can get very good at it. Build one system a week, timed, and always answer
   "what if two threads do this?".
3. **System design with failure paths (about 20%).** One design a week. Lead with idempotency, retries,
   consistency and observability, and use stories from your own Spring Boot and MySQL work for depth.
4. **Your own stack, deep (about 15%).** Spring transactions and proxies, JPA fetching, InnoDB indexes and locks,
   Angular change detection. These rounds can't be bluffed, and your two years are an advantage only if you can go
   five "whys" deep.
5. **Stories and HR (about 10%).** Eight to ten stories with numbers, one project brief, and a scripted answer on
   CTC and notice period.
6. **Code review, debugging and AI-assisted coding (about 10%).** Cheap to practise and growing: review one file
   a week out loud, and do one AI-pair session where you verify everything.

**What to skip:** staff-level design topics, exotic technologies you can't defend, LeetCode hards beyond a handful,
and memorising answers you can't explain. Each round below shows how it's scored, a worked example, the common ways
people fail, and exactly what to practise on this site.
""")

ROUNDS = ROUNDS_P1 + ROUNDS_P2 + ROUNDS_P3

EXPECTED_IDS = [
    "online-assessment", "dsa-live-coding", "ai-assisted-coding", "practical-coding", "machine-coding-lld",
    "concurrency-round", "code-review-round", "debugging-production-round", "system-design-senior",
    "resume-deep-dive", "project-deep-dive", "behavioral-leadership", "hiring-manager-and-hr",
]


def load_valid_routes():
    """Parse ID_INDEX.md plus the AI course JSON into sets of valid route targets."""
    text = open(os.path.join(HERE, "ID_INDEX.md"), encoding="utf-8").read()
    dsa, sd, core, trap_areas = {}, {}, set(), set()
    section = None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            # some sections list their ids on the header line itself
            m = re.search(r":\s*(.+)$", line)
            if m and section.startswith("new senior subjects"):
                core |= {x.strip() for x in m.group(1).split(",")}
            elif m and section.startswith("new trap areas"):
                trap_areas |= {x.strip() for x in m.group(1).split(",")}
            elif m and section.startswith("new senior system design"):
                sd.setdefault("senior", set()).update(x.strip() for x in m.group(1).split(","))
            continue
        if section and section.startswith("dsa") and line.startswith("- "):
            pat, probs = line[2:].split(":", 1)
            dsa[pat.strip()] = {p.strip() for p in probs.split(",")}
        elif section and section.startswith("system design") and line.startswith("- "):
            grp, topics = line[2:].split(":", 1)
            sd[grp.strip()] = {t.strip() for t in topics.split(",")}
        elif section and section.startswith("core subjects") and line.startswith("- "):
            core.add(line[2:].split(" ", 1)[0].strip())
        elif section and section.startswith("new senior subjects"):
            m = re.search(r":\s*(.+)$", line)
            if m:
                core |= {x.strip() for x in m.group(1).split(",")}
        elif section and section.startswith("new trap areas"):
            m = re.search(r"areas:\s*(.+)$", line) or re.search(r":\s*(.+)$", line)
            if m:
                trap_areas |= {x.strip() for x in m.group(1).split(",")}
        elif section and section.startswith("new senior system design"):
            m = re.search(r"reserved:\s*(.+)$", line)
            if m:
                sd.setdefault("senior", set()).update(x.strip() for x in m.group(1).split(","))
    ai = {}
    for f in ("ai-course-1.json", "ai-course-2.json"):
        p = os.path.join(ROOT, "frontend", "public", "content", f)
        d = json.load(open(p, encoding="utf-8"))
        mods = d["modules"] if isinstance(d, dict) and "modules" in d else d
        for m in mods:
            ai[m["id"]] = {l["id"] for l in m.get("lessons", [])}
    return dsa, sd, core, trap_areas, ai


def check_link(link, routes, round_ids):
    dsa, sd, core, trap_areas, ai = routes
    path, _, query = link.partition("?")
    parts = path.strip("/").split("/")
    if parts[0] == "dsa":
        return len(parts) == 3 and parts[2] in dsa.get(parts[1], set())
    if parts[0] == "system-design":
        return len(parts) == 3 and parts[2] in sd.get(parts[1], set())
    if parts[0] == "core":
        ok = len(parts) == 2 and parts[1] in core
        if query:
            ok = ok and (query in ("view=qa", "view=cards") or re.fullmatch(r"chapter=\d+", query) is not None)
        return ok
    if parts[0] == "final-round":
        return len(parts) == 2 and parts[1].isdigit() and 1 <= int(parts[1]) <= 14
    if parts[0] == "ai":
        return len(parts) == 3 and parts[2] in ai.get(parts[1], set())
    if parts[0] == "traps":
        return len(parts) == 1 and (not query or (query.startswith("area=") and query[5:] in trap_areas))
    if parts[0] == "rounds":
        return len(parts) == 2 and parts[1] in round_ids
    return len(parts) == 1 and parts[0] in ("guide", "habits", "focus") and not query


def validate(data):
    errors = []
    tw = words(data["trends"])
    if not 300 <= tw <= 600:
        errors.append(f"trends: {tw} words (want 300-600)")
    ids = [r["id"] for r in data["rounds"]]
    if ids != EXPECTED_IDS:
        errors.append(f"round ids/order mismatch: {ids}")
    routes = load_valid_routes()
    for i, r in enumerate(data["rounds"], 1):
        rid = r["id"]
        if r["order"] != i:
            errors.append(f"{rid}: order {r['order']} != {i}")
        h, w = words(r["howToAce"]), words(r["walkthrough"])
        if not 300 <= h <= 600:
            errors.append(f"{rid}: howToAce {h} words (want 300-600)")
        if not 400 <= w <= 900:
            errors.append(f"{rid}: walkthrough {w} words (want 400-900)")
        n_sent = len(re.findall(r"[.!?](\s|$)", r["summary"]))
        if n_sent > 2:
            errors.append(f"{rid}: summary has {n_sent} sentences")
        for p in r["practice"]:
            if not check_link(p["link"], routes, set(ids)):
                errors.append(f"{rid}: bad practice link {p['link']}")
        for s in r["sources"]:
            if not s["url"].startswith("https://"):
                errors.append(f"{rid}: bad source url {s['url']}")
        if r["walkthrough"].count("```") % 2 or r["howToAce"].count("```") % 2:
            errors.append(f"{rid}: unbalanced code fence")
    return errors


def total_words(data):
    def walk(x):
        if isinstance(x, str):
            return words(x)
        if isinstance(x, list):
            return sum(walk(i) for i in x)
        if isinstance(x, dict):
            return sum(walk(v) for k, v in x.items() if k not in ("id", "url", "link", "order", "icon"))
        return 0
    return walk(data)


def main():
    data = {"trends": TRENDS, "rounds": ROUNDS}
    errors = validate(data)
    for r in ROUNDS:
        print(f"{r['order']:>2} {r['id']:<28} howToAce={words(r['howToAce']):>3} "
              f"walkthrough={words(r['walkthrough']):>3} rubric={words(r['rubric']):>3}")
    print("trends words:", words(TRENDS))
    if errors:
        print("ERRORS:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(OUT, encoding="utf-8") as f:
        json.load(f)
    print(f"wrote {OUT}: {len(ROUNDS)} rounds, {total_words(data)} words")


if __name__ == "__main__":
    main()
