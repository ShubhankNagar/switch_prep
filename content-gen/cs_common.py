import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "cs_parts")
os.makedirs(PARTS, exist_ok=True)
B, I, A = "Basic", "Intermediate", "Advanced"


def build(sid, prefix, name, order, icon, desc, notes, qa, sources):
    subj = {
        "id": sid, "name": name, "order": order, "icon": icon, "description": desc,
        "notes": [{"id": f"{prefix}-n{i+1:02d}", "title": t, "content": c.strip()} for i, (t, c) in enumerate(notes)],
        "qa": [],
        "sources": [{"title": t, "url": u} for t, u in sources],
    }
    for i, item in enumerate(qa):
        q, a, level, tags, freq = item
        assert level in (B, I, A), q
        subj["qa"].append({"id": f"{prefix}-{i+1:03d}", "q": q.strip(), "a": a.strip(),
                           "level": level, "tags": tags, "frequent": bool(freq)})
    with open(os.path.join(PARTS, f"{sid}.json"), "w", encoding="utf-8") as f:
        json.dump(subj, f, ensure_ascii=False, indent=1)
    wc = [len(n["content"].split()) for n in subj["notes"]]
    aw = [len(x["a"].split()) for x in subj["qa"]]
    print(sid, "notes", len(subj["notes"]), "words", min(wc), max(wc), "| qa", len(subj["qa"]), "words", min(aw), max(aw))
    for n, w in zip(subj["notes"], wc):
        if w < 300 or w > 800: print("  note len warn:", n["title"], w)
    for x, w in zip(subj["qa"], aw):
        if w < 45 or w > 220: print("  qa len warn:", x["id"], w)
    return subj
