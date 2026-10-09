"""Merge core-backend part files into frontend/public/content/core-backend.json."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "frontend", "public", "content", "core-backend.json")
for s in ["cb_java.py", "cb_spring.py", "cb_ms.py", "cb_sql.py"]:
    subprocess.run([sys.executable, os.path.join(HERE, s)], check=True, cwd=HERE)
subjects = []
for sid in ["java", "spring-boot", "microservices", "sql"]:
    with open(os.path.join(HERE, f"cb_part_{sid}.json"), encoding="utf-8") as f:
        subjects.append(json.load(f))
subjects.sort(key=lambda s: s["order"])
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"subjects": subjects}, f, ensure_ascii=False, indent=1)
# validate
data = json.load(open(OUT, encoding="utf-8"))
ids = set()
for s in data["subjects"]:
    for k in ["id","name","order","icon","description","notes","qa","sources"]:
        assert k in s, k
    for n in s["notes"]:
        assert n["id"] not in ids; ids.add(n["id"])
        w = len(n["content"].split())
        if not 300 <= w <= 800: print("  note words out of range:", n["id"], w)
    for q in s["qa"]:
        assert q["id"] not in ids; ids.add(q["id"])
        assert q["id"].startswith(s["id"])
        w = len(q["a"].split())
        if not 40 <= w <= 220: print("  qa words:", q["id"], w)
    print(s["id"], "notes", len(s["notes"]), "qa", len(s["qa"]), "frequent", sum(q["frequent"] for q in s["qa"]), "sources", len(s["sources"]))
