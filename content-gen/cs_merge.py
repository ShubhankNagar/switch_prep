"""Builds frontend/public/content/core-cs.json from the gen_cs_*.py part files."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "cs_parts")
OUT = os.path.join(HERE, "..", "frontend", "public", "content", "core-cs.json")
SCRIPTS = ["gen_cs_angular.py", "gen_cs_js.py", "gen_cs_os.py", "gen_cs_cn.py",
           "gen_cs_dbms.py", "gen_cs_oop.py", "gen_cs_behavioral.py"]
ORDER = {"angular": 5, "javascript-typescript": 6, "os": 7, "cn": 8, "dbms": 9,
         "oop-design-patterns": 10, "behavioral": 11}

if "--no-gen" not in sys.argv:
    for s in SCRIPTS:
        subprocess.run([sys.executable, os.path.join(HERE, s)], check=True, cwd=HERE)

subjects = []
for sid in ORDER:
    with open(os.path.join(PARTS, f"{sid}.json"), encoding="utf-8") as f:
        subjects.append(json.load(f))
subjects.sort(key=lambda s: s["order"])

# sanity checks
ids = set()
for s in subjects:
    assert s["order"] == ORDER[s["id"]], s["id"]
    for k in ("id", "name", "order", "icon", "description", "notes", "qa", "sources"):
        assert s.get(k) not in (None, "", []), (s["id"], k)
    for x in s["notes"] + s["qa"]:
        assert x["id"] not in ids, x["id"]
        ids.add(x["id"])
    for q in s["qa"]:
        assert q["level"] in ("Basic", "Intermediate", "Advanced") and isinstance(q["frequent"], bool)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"subjects": subjects}, f, ensure_ascii=False, indent=1)

with open(OUT, encoding="utf-8") as f:
    data = json.load(f)
for s in data["subjects"]:
    print(f'{s["order"]:>2} {s["id"]:<22} notes={len(s["notes"]):<3} qa={len(s["qa"]):<3} '
          f'frequent={sum(q["frequent"] for q in s["qa"]):<3} sources={len(s["sources"])}')
print("total qa", sum(len(s["qa"]) for s in data["subjects"]), "->", os.path.abspath(OUT))
