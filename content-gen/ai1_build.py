"""Merge AI course part 1 modules into ai-course-1.json and validate."""
import importlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = "/home/claude/switch-prep/frontend/public/content/ai-course-1.json"
NAMES = [n for n in ["ai1_m01", "ai1_m02", "ai1_m03", "ai1_m04", "ai1_m05", "ai1_m06"]
         if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), n + ".py"))]

modules = [importlib.import_module(n).MODULE for n in NAMES]
problems = []
ids = set()
for m in modules:
    if not 5 <= len(m["lessons"]) <= 7:
        problems.append(f"{m['id']} has {len(m['lessons'])} lessons")
    for l in m["lessons"]:
        assert l["id"].startswith(m["id"][:3]), l["id"]
        assert l["id"] not in ids, l["id"]
        ids.add(l["id"])
        wc = len(re.findall(r"\S+", l["content"]))
        flag = "" if 500 <= wc <= 1100 else "  <-- OUT OF RANGE"
        if flag:
            problems.append(f"{l['id']} words={wc}")
        print(f"{l['id']:40s} words={wc}{flag}  py={'```python' in l['content']}")
        assert "```python" in l["content"], l["id"]
        assert len(l["resources"]) >= 2

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"modules": modules}, f, ensure_ascii=False, indent=1)

with open(OUT, encoding="utf-8") as f:
    data = json.load(f)
nm = len(data["modules"])
nl = sum(len(m["lessons"]) for m in data["modules"])
nq = sum(len(l["quiz"]) for m in data["modules"] for l in m["lessons"])
nr = sum(len(l["resources"]) for m in data["modules"] for l in m["lessons"])
print(f"modules={nm} lessons={nl} quizzes={nq} resources={nr} projects={nm}")
print("PROBLEMS:", problems or "none")
