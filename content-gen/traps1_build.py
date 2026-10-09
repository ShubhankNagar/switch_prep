"""Merge trap chunks into frontend/public/content/traps-1.json and validate."""
import json
import random
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traps1_common import check  # noqa: E402
import traps1_java, traps1_concurrency, traps1_spring, traps1_jpa, traps1_sql  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public", "content", "traps-1.json")

traps = (traps1_java.TRAPS + traps1_concurrency.TRAPS + traps1_spring.TRAPS
         + traps1_jpa.TRAPS + traps1_sql.TRAPS)

# Chunks are authored with the correct option mostly at index 1. Spread answers evenly over 0..3
# (deterministic, so ids/answers are stable between runs). Options that are query labels (A/B/C/D)
# keep their authored order.
KEEP_ORDER = {"trap-sql-index-sargability", "trap-sql-composite-index-leftmost-prefix"}
movable = [t for t in traps if t["options"] and t["id"] not in KEEP_ORDER]
targets = ([0, 1, 2, 3] * (len(movable) // 4 + 1))[:len(movable)]
random.Random(20261009).shuffle(targets)
for t, target in zip(movable, targets):
    opts = list(t["options"])
    right = opts.pop(t["answer"])
    opts.insert(target, right)
    t["options"], t["answer"] = opts, target

problems = check(traps)
dupes = [i for i, n in Counter(t["id"] for t in traps).items() if n > 1]
if dupes:
    problems.append(f"duplicate ids: {dupes}")
if problems:
    print("\n".join(problems))
    sys.exit(1)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"traps": traps}, f, ensure_ascii=False, indent=1)
    f.write("\n")

with open(OUT, encoding="utf-8") as f:
    data = json.load(f)

counts = Counter(t["area"] for t in data["traps"])
print(f"wrote {os.path.normpath(OUT)}: {len(data['traps'])} traps")
for area in ["java", "concurrency", "spring", "jpa-hibernate", "sql"]:
    print(f"  {area}: {counts[area]}")
print("  MCQ:", sum(1 for t in data["traps"] if t["options"]), " open:", sum(1 for t in data["traps"] if not t["options"]))
