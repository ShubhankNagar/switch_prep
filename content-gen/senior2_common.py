"""Shared helpers for the core-senior-2 subjects (cloud-devops, security, ai-assisted-engineering, senior-leadership).

Each chunk script (senior2_cloud.py, senior2_security.py, senior2_ai.py, senior2_lead.py) defines NOTES, QA and SOURCES
and exposes subject(); running a chunk directly prints its counts and word-range warnings.
senior2_merge.py imports every chunk and writes frontend/public/content/core-senior-2.json.
"""

B, I, A = "Basic", "Intermediate", "Advanced"


def build(sid, name, order, icon, desc, prefix, notes, qa, sources):
    """notes: list of (note_id, title, markdown). qa: list of (question, answer, level, tags, frequent)."""
    subj = {
        "id": sid, "name": name, "order": order, "icon": icon, "description": desc,
        "notes": [{"id": nid, "title": t, "content": c.strip()} for nid, t, c in notes],
        "qa": [],
        "sources": [{"title": t, "url": u} for t, u in sources],
    }
    for i, (q, a, level, tags, freq) in enumerate(qa):
        assert level in (B, I, A), q
        subj["qa"].append({"id": f"{prefix}-{i + 1:03d}", "q": q.strip(), "a": a.strip(),
                           "level": level, "tags": tags, "frequent": bool(freq)})
    return subj


def report(subj):
    """Print counts and any word-count problems for one subject; return list of problems."""
    problems = []
    ids = [n["id"] for n in subj["notes"]]
    if len(ids) != len(set(ids)):
        problems.append("duplicate note ids")
    for n in subj["notes"]:
        w = len(n["content"].split())
        if not 400 <= w <= 900:
            problems.append(f"note {n['id']} has {w} words")
    for q in subj["qa"]:
        w = len(q["a"].split())
        if not 80 <= w <= 220:
            problems.append(f"qa {q['id']} has {w} words")
    if not 6 <= len(subj["notes"]) <= 8:
        problems.append(f"{len(subj['notes'])} notes (want 6-8)")
    if not 24 <= len(subj["qa"]) <= 30:
        problems.append(f"{len(subj['qa'])} qa (want 24-30)")
    freq = sum(q["frequent"] for q in subj["qa"])
    nw = [len(n["content"].split()) for n in subj["notes"]]
    qw = [len(q["a"].split()) for q in subj["qa"]]
    print(f"{subj['id']}: notes={len(subj['notes'])} (words {min(nw)}-{max(nw)}), qa={len(subj['qa'])} "
          f"(words {min(qw)}-{max(qw)}), frequent={freq} ({100 * freq // len(subj['qa'])}%), sources={len(subj['sources'])}")
    for p in problems:
        print("  !", p)
    return problems
