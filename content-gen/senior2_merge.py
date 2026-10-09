"""Build frontend/public/content/core-senior-2.json from the senior2_* chunk scripts.

Subjects: cloud-devops (16), security (17), ai-assisted-engineering (18), senior-leadership (19).
Run: python3 content-gen/senior2_merge.py   (then python3 content-gen/validate_content.py)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import senior2_cloud, senior2_security, senior2_ai, senior2_lead  # noqa: E402
from senior2_common import report  # noqa: E402

OUT = os.path.join(HERE, "..", "frontend", "public", "content", "core-senior-2.json")
EXPECTED = {"cloud-devops": (16, "cloud-"), "security": (17, "sec-"),
            "ai-assisted-engineering": (18, "aie-"), "senior-leadership": (19, "lead-")}

subjects = [m.subject() for m in (senior2_cloud, senior2_security, senior2_ai, senior2_lead)]
subjects.sort(key=lambda s: s["order"])

problems = []
for s in subjects:
    problems += [f"{s['id']}: {p}" for p in report(s)]
    order, prefix = EXPECTED[s["id"]]
    if s["order"] != order:
        problems.append(f"{s['id']}: order {s['order']} != {order}")
    if not all(q["id"].startswith(prefix) for q in s["qa"]):
        problems.append(f"{s['id']}: qa id prefix must be {prefix}")
    if not all(src["url"].startswith("https://") for src in s["sources"]):
        problems.append(f"{s['id']}: non-https source url")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"subjects": subjects}, f, ensure_ascii=False, indent=1)

# validate the written file and check id uniqueness against the other core files
data = json.load(open(OUT, encoding="utf-8"))
content_dir = os.path.dirname(OUT)
other_qa, other_subjects = set(), set()
for name in ("core-backend.json", "core-cs.json", "core-senior-1.json"):
    p = os.path.join(content_dir, name)
    if os.path.exists(p):
        for s in json.load(open(p, encoding="utf-8"))["subjects"]:
            other_subjects.add(s["id"])
            other_qa.update(q["id"] for q in s["qa"])
qa_ids = [q["id"] for s in data["subjects"] for q in s["qa"]]
if len(qa_ids) != len(set(qa_ids)):
    problems.append("duplicate qa ids inside core-senior-2.json")
clash = (set(qa_ids) & other_qa) | ({s["id"] for s in data["subjects"]} & other_subjects)
if clash:
    problems.append(f"ids clash with other core files: {sorted(clash)[:10]}")

print(f"\nwrote {os.path.relpath(OUT, HERE)}: {len(data['subjects'])} subjects, "
      f"{sum(len(s['notes']) for s in data['subjects'])} notes, {len(qa_ids)} qa")
if problems:
    print(f"{len(problems)} problem(s):")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("core-senior-2.json OK")
