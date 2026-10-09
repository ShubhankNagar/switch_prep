import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dsa1_arrays import PATTERN as AH
from dsa1_tp_sw_stack import TP, SW, ST
from dsa1_bs_ll import BS, LL
from dsa1_trees import TR, TRIE, HEAP

OUT = "/home/claude/switch-prep/frontend/public/content/dsa-part1.json"

patterns = [AH, TP, SW, ST, BS, LL, TR, TRIE, HEAP]

# These two also live in dsa-part2 (Intervals / Greedy), which is their canonical home; ids must be unique.
IN_PART2 = {"merge-intervals", "task-scheduler"}
for p in patterns:
    p["problems"] = [q for q in p["problems"] if q["id"] not in IN_PART2]
seen = set()
for p in patterns:
    words = len(re.findall(r"\S+", p["intro"]))
    print(f"{p['order']} {p['id']}: {len(p['problems'])} problems, intro {words} words")
    for q in p["problems"]:
        assert q["id"] not in seen, q["id"]
        seen.add(q["id"])
        for k in ("summary", "approach", "solution", "time", "space"):
            assert q[k], (q["id"], k)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"patterns": patterns}, f, ensure_ascii=False, indent=1)

allp = [q for p in patterns for q in p["problems"]]
print("total", len(allp), "mustDo", sum(q["mustDo"] for q in allp))
from collections import Counter
print(Counter(q["difficulty"] for q in allp))
