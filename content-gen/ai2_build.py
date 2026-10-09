"""Merge AI Engineer course part 2 (modules 7-14) into ai-course-2.json."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai2_m07, ai2_m08, ai2_m09, ai2_m10, ai2_m11, ai2_m12, ai2_m13, ai2_m14

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public", "content", "ai-course-2.json")
mods = [m.MODULE for m in (ai2_m07, ai2_m08, ai2_m09, ai2_m10, ai2_m11, ai2_m12, ai2_m13, ai2_m14)]

ids = set()
for m in mods:
    assert m["level"] in ("Beginner", "Intermediate", "Advanced")
    assert 3 <= len(m["outcomes"]) <= 5, m["id"]
    for l in m["lessons"]:
        assert l["id"] not in ids, l["id"]; ids.add(l["id"])
        w = len(re.findall(r"\S+", l["content"]))
        assert 500 <= w <= 1100, (l["id"], w)
        assert len(l["quiz"]) == 3 and all(len(q["options"]) == 4 for q in l["quiz"])
        assert l["resources"] and l["exercise"]
        assert l["content"].count("```") % 2 == 0, l["id"]

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"modules": mods}, f, ensure_ascii=False, indent=1)

d = json.load(open(OUT, encoding="utf-8"))
L = [l for m in d["modules"] for l in m["lessons"]]
words = [len(re.findall(r"\S+", l["content"])) for l in L]
print("modules", len(d["modules"]), "lessons", len(L), "quiz", sum(len(l["quiz"]) for l in L),
      "resources", sum(len(l["resources"]) for l in L), "words min/avg/max", min(words), sum(words)//len(words), max(words))
for m in d["modules"]:
    print(m["order"], m["id"], len(m["lessons"]))
