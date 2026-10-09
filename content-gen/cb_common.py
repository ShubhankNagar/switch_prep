import json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def build(sid, name, order, icon, desc, notes, qa, sources):
    subj = {
        "id": sid, "name": name, "order": order, "icon": icon, "description": desc,
        "notes": [{"id": f"{sid}-n{i+1:02d}", "title": t, "content": c.strip()} for i, (t, c) in enumerate(notes)],
        "qa": [],
        "sources": [{"title": t, "url": u} for t, u in sources],
    }
    for i, item in enumerate(qa):
        q, a, level, tags, freq = item
        assert level in ("Basic", "Intermediate", "Advanced"), q
        subj["qa"].append({"id": f"{sid}-{i+1:03d}", "q": q.strip(), "a": a.strip(),
                           "level": level, "tags": tags, "frequent": bool(freq)})
    path = os.path.join(HERE, f"cb_part_{sid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(subj, f, ensure_ascii=False, indent=1)
    wc = [len(n["content"].split()) for n in subj["notes"]]
    print(sid, "notes", len(subj["notes"]), "words min/max", min(wc), max(wc), "qa", len(subj["qa"]))
    return subj


B, I, A = "Basic", "Intermediate", "Advanced"
