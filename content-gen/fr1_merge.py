import json, os, importlib, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = "/home/claude/switch-prep/frontend/public/content/final-round-1.json"
days = [importlib.import_module(f"fr1_d{i}").DAY for i in range(1, 8)]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"days": days}, f, ensure_ascii=False, indent=1)
data = json.load(open(OUT, encoding="utf-8"))
ids = set()
for d in data["days"]:
    for k in ("mcqs", "coding", "theory"):
        for it in d[k]:
            assert it["id"] not in ids, it["id"]; ids.add(it["id"])
print("days", len(data["days"]),
      "mcqs", sum(len(d["mcqs"]) for d in data["days"]),
      "coding", sum(len(d["coding"]) for d in data["days"]),
      "theory", sum(len(d["theory"]) for d in data["days"]))
from collections import Counter
print("answer dist", Counter(m["answer"] for d in data["days"] for m in d["mcqs"]))
