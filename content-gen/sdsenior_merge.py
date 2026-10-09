"""Merges sdsenior_c1..c5 into frontend/public/content/system-design-senior.json and validates it."""
import json, os
from sdsenior_common import HERE, report
import sdsenior_c1, sdsenior_c2, sdsenior_c3, sdsenior_c4, sdsenior_c5

EXPECTED = [
    ("failure-handling-resilience", "concept"), ("idempotency-exactly-once", "concept"),
    ("multi-region-disaster-recovery", "concept"), ("observability-slos-at-scale", "concept"),
    ("cost-and-capacity-planning", "concept"), ("ai-system-design-rag", "concept"),
    ("payment-processing-reliability", "case-study"), ("distributed-job-scheduler", "case-study"),
    ("metrics-monitoring-system", "case-study"), ("leaderboard-top-k-trending", "case-study"),
    ("flash-sale-inventory", "case-study"), ("webhook-delivery-system", "case-study"),
    ("collaborative-editor", "case-study"),
]

topics = []
for m in (sdsenior_c1, sdsenior_c2, sdsenior_c3, sdsenior_c4, sdsenior_c5):
    topics.extend(m.topics)
topics.sort(key=lambda t: t["order"])

out = os.path.join(HERE, "..", "frontend", "public", "content", "system-design-senior.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"topics": topics}, f, ensure_ascii=False, indent=1)

# ---- validate what was written
d = json.load(open(out, encoding="utf-8"))
ts = d["topics"]
assert [(t["id"], t["kind"]) for t in ts] == EXPECTED, [(t["id"], t["kind"]) for t in ts]
assert [t["order"] for t in ts] == list(range(1, 14))
hld = json.load(open(os.path.join(HERE, "..", "frontend", "public", "content", "system-design-hld.json"), encoding="utf-8"))
lld = json.load(open(os.path.join(HERE, "..", "frontend", "public", "content", "system-design-lld.json"), encoding="utf-8"))
other_ids = {t["id"] for k in hld for t in hld[k]} | {t["id"] for k in lld for t in lld[k]}
warn = 0
for t in ts:
    assert t["id"] not in other_ids, f"id clash with HLD/LLD: {t['id']}"
    assert t["level"] in ("Intermediate", "Advanced"), t["id"]
    assert isinstance(t["minutes"], int) and t["summary"] and t["title"]
    assert 6 <= len(t["keyPoints"]) <= 8, t["id"]
    assert 5 <= len(t["interviewQuestions"]) <= 6, t["id"]
    assert t["sources"] and all(s["url"].startswith("http") for s in t["sources"]), t["id"]
    assert t["content"].count("```") % 2 == 0, f"unbalanced code fence in {t['id']}"
    w = len(t["content"].split())
    lo, hi = (700, 1200) if t["kind"] == "concept" else (1100, 1700)
    if not lo <= w <= hi:
        print("WARN content words", t["id"], w); warn += 1
    for qa in t["interviewQuestions"]:
        aw = len(qa["a"].split())
        if not 50 <= aw <= 130:
            print("WARN answer words", t["id"], aw); warn += 1
report(ts)
print(f"\n{len(ts)} topics ({sum(t['kind']=='concept' for t in ts)} concepts, "
      f"{sum(t['kind']=='case-study' for t in ts)} case studies), "
      f"{sum(len(t['content'].split()) for t in ts)} content words, "
      f"{sum(len(t['keyPoints']) for t in ts)} key points, "
      f"{sum(len(t['interviewQuestions']) for t in ts)} interview questions, "
      f"{sum(len(t['sources']) for t in ts)} sources, {warn} warnings")
