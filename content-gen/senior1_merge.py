"""Builds every senior1 subject, merges them into frontend/public/content/core-senior-1.json and validates the result.
Run: python3 content-gen/senior1_merge.py   (then python3 content-gen/senior1_javacheck.py to compile the Java examples)"""
import glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "frontend", "public", "content", "core-senior-1.json")
ORDER = [("senior1_dbg.py", "production-debugging"), ("senior1_perf.py", "performance"),
         ("senior1_conc.py", "concurrency-practical"), ("senior1_test.py", "testing-code-review")]

for script, _ in ORDER:
    subprocess.run([sys.executable, os.path.join(HERE, script)], check=True, cwd=HERE)

subjects = [json.load(open(os.path.join(HERE, "senior1_parts", f"{sid}.json"), encoding="utf-8")) for _, sid in ORDER]
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"subjects": subjects}, f, ensure_ascii=False, indent=1)

# ---- validate ----
data = json.load(open(OUT, encoding="utf-8"))
errors = []
expected = {"production-debugging": (12, "dbg"), "performance": (13, "perf"),
            "concurrency-practical": (14, "conc"), "testing-code-review": (15, "test")}
other_ids, other_qa, other_orders = set(), set(), set()
for p in glob.glob(os.path.join(os.path.dirname(OUT), "core-*.json")):
    if os.path.samefile(p, OUT):
        continue
    for s in json.load(open(p, encoding="utf-8")).get("subjects", []):
        other_ids.add(s["id"]); other_orders.add(s.get("order"))
        other_qa.update(q["id"] for q in s["qa"])
seen = set()
for s in data["subjects"]:
    sid = s["id"]
    order, prefix = expected[sid]
    for k in ("id", "name", "order", "icon", "description", "notes", "qa", "sources"):
        if k not in s or s[k] in ("", [], None):
            errors.append(f"{sid}: missing {k}")
    if s["order"] != order: errors.append(f"{sid}: order {s['order']} != {order}")
    if sid in other_ids: errors.append(f"{sid}: subject id already used elsewhere")
    if s["order"] in other_orders: errors.append(f"{sid}: order {s['order']} already used elsewhere")
    if not 6 <= len(s["notes"]) <= 8: errors.append(f"{sid}: {len(s['notes'])} notes")
    if not 24 <= len(s["qa"]) <= 30: errors.append(f"{sid}: {len(s['qa'])} qa")
    for n in s["notes"]:
        if n["id"] in seen: errors.append(f"dup id {n['id']}")
        seen.add(n["id"])
        if n["content"].count("```") % 2: errors.append(f"{n['id']}: unbalanced code fences")
    for i, q in enumerate(s["qa"], 1):
        if q["id"] != f"{prefix}-{i:03d}": errors.append(f"{sid}: bad qa id {q['id']}")
        if q["id"] in seen or q["id"] in other_qa: errors.append(f"dup qa id {q['id']}")
        seen.add(q["id"])
        if q["level"] not in ("Basic", "Intermediate", "Advanced"): errors.append(f"{q['id']}: level")
        if not isinstance(q["frequent"], bool) or not q["tags"]: errors.append(f"{q['id']}: frequent/tags")
        if q["a"].count("```") % 2: errors.append(f"{q['id']}: unbalanced code fences")
    for src in s["sources"]:
        if not re.match(r"^https://", src["url"]): errors.append(f"{sid}: bad source url {src['url']}")
    print(f"{sid:24s} order={s['order']} notes={len(s['notes'])} qa={len(s['qa'])} "
          f"frequent={sum(q['frequent'] for q in s['qa'])} sources={len(s['sources'])}")
if errors:
    print("\n".join(errors)); sys.exit(1)
print("OK ->", os.path.normpath(OUT), os.path.getsize(OUT), "bytes")
