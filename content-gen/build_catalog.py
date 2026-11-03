"""
Builds frontend/public/content/catalog.json: a small index of every trackable item (key, section, title, link,
group). The dashboard, revision list and site search load this one file instead of all the content files.

Keys must match frontend/src/app/core/catalog.service.ts `keys.*` exactly (as in build_focus.py): a mismatch makes
progress look missing. validate_content.py fails when catalog.json is out of date with the content.
Run after any content change: python3 content-gen/build_catalog.py
"""
import json, pathlib

C = pathlib.Path(__file__).resolve().parent.parent / "frontend/public/content"


def load(name):
    return json.loads((C / name).read_text())


def by_order(xs, field="order"):
    return sorted(xs, key=lambda x: x[field])


def build():
    plan = load("plan.json")
    dsa = by_order([p for f in ("dsa-part1.json", "dsa-part2.json") for p in load(f)["patterns"]])
    hld, lld, senior = load("system-design-hld.json"), load("system-design-lld.json"), load("system-design-senior.json")
    sd = [
        ("concepts", "HLD Concepts", hld["concepts"]),
        ("case-studies", "HLD Case Studies", hld["caseStudies"]),
        ("lld-fundamentals", "LLD Fundamentals", lld["fundamentals"]),
        ("lld-problems", "LLD / Machine Coding", lld["problems"]),
        ("senior", "Senior Design (2027)", senior["topics"]),
    ]
    subjects = by_order([s for f in ("core-backend.json", "core-cs.json", "core-senior-1.json", "core-senior-2.json")
                         for s in load(f)["subjects"]])
    final_days = by_order([d for f in ("final-round-1.json", "final-round-2.json") for d in load(f)["days"]], "day")
    ai = by_order([m for f in ("ai-course-1.json", "ai-course-2.json") for m in load(f)["modules"]])
    traps = [t for f in ("traps-1.json", "traps-2.json") for t in load(f)["traps"]]
    rounds = by_order(load("rounds.json")["rounds"])

    out = []
    add = lambda key, section, title, link, group: out.append(
        {"key": key, "section": section, "title": title, "link": link, "group": group})
    for d in plan["days"]:
        for t in d["tasks"]:
            add(f"plan:d{d['day']}:{t['id']}", "plan", f"Day {d['day']}: {t['title']}", f"/plan/{d['day']}", "Plan")
    for p in dsa:
        for q in p["problems"]:
            add(f"dsa:{q['id']}", "dsa", q["title"], f"/dsa/{p['id']}/{q['id']}", p["name"])
    for gid, gname, topics in sd:
        for t in by_order(topics):
            add(f"sd:{t['id']}", "sd", t["title"], f"/system-design/{gid}/{t['id']}", gname)
    for s in subjects:
        for i, n in enumerate(s["notes"]):
            add(f"note:{s['id']}:{n['id']}", "core", n["title"], f"/core/{s['id']}?chapter={i + 1}", f"{s['name']} notes")
        for q in s["qa"]:
            qid = q.get("id") or q["q"]
            add(f"qa:{qid}", "core", q["q"], f"/core/{s['id']}?view=qa&qa={qid}", f"{s['name']} Q&A")
    for d in final_days:
        for c in d["coding"]:
            add(f"fr:{c.get('id') or ''}", "final", c["title"], f"/final-round/{d['day']}?tab=coding&item={c['id']}",
                f"Final round day {d['day']}")
        for c in d["theory"]:
            add(f"fr:{c.get('id') or ''}", "final", c["q"], f"/final-round/{d['day']}?tab=theory&item={c['id']}",
                f"Final round day {d['day']}")
    for m in ai:
        for l in m["lessons"]:
            add(f"ai:{l['id']}", "ai", l["title"], f"/ai/{m['id']}/{l['id']}", m["title"])
        add(f"ai:{m['id']}:project", "ai", f"Project: {m['project']['title']}", f"/ai/{m['id']}", m["title"])
    for t in traps:
        add(f"trap:{t['id']}", "traps", t["title"], f"/traps/{t['id']}", "Common traps")
    for r in rounds:
        add(f"round:{r['id']}", "rounds", r["title"], f"/rounds/{r['id']}", "Interview rounds")
    return {"items": out}


def render(catalog):
    # one item per line: small, and diffs stay readable
    return "{\"items\": [\n" + ",\n".join(json.dumps(i, ensure_ascii=False) for i in catalog["items"]) + "\n]}\n"


if __name__ == "__main__":
    catalog = build()
    (C / "catalog.json").write_text(render(catalog))
    print(f"catalog.json: {len(catalog['items'])} items")
