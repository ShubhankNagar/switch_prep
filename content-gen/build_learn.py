"""
Builds the learning overlays in frontend/public/content/learn-*.json from content-gen/learn_*.py.

The overlays add interview coaching on top of the generated content, keyed by content id, so the content generators
stay untouched. The frontend merges them into the item when it loads that area:
  learn-dsa.json   per DSA problem: how to recognise it, brute force, edge cases, common bug, likely follow-up
  learn-core.json  per core Q&A: the short answer to say first; per note chapter: takeaways and self-test questions;
                   `core`: the questions shown first everywhere; `dupOf`: a duplicate question -> the copy to study
validate_content.py checks that every overlay id exists and that the files are up to date.
Run after editing any learn_*.py: python3 content-gen/build_learn.py
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
C = HERE.parent / "frontend/public/content"
sys.path.insert(0, str(HERE))


def dsa():
    import learn_dsa1, learn_dsa2
    out = {}
    for it in learn_dsa1.ITEMS + learn_dsa2.ITEMS:
        if it["id"] in out:
            raise SystemExit(f"learn-dsa: duplicate id {it['id']}")
        entry = {k: v for k, v in it.items() if k != "id" and v}
        if it.get("follow"):
            entry["follow"] = {"q": it["follow"][0], "a": it["follow"][1]}
        out[it["id"]] = entry
    return {"problems": out}


def core_qa():
    """The core questions: the focus list's Q&A without duplicates, plus the senior picks and new additions."""
    import learn_core
    focus = json.loads((C / "focus.json").read_text())
    ids = [it["key"][3:] for t in focus["tiers"] for g in t["groups"] for it in g["items"] if it["key"].startswith("qa:")]
    ids += learn_core.SENIOR_CORE + learn_core.EXTRA_CORE
    return sorted({i for i in ids if i not in learn_core.DUP_OF})


def core_notes():
    """The chapters the plan schedules, as "subjectId:noteId"."""
    from core_order import CORE_ORDER
    subjects = {s["id"]: s for f in ("core-backend.json", "core-cs.json", "core-senior-1.json", "core-senior-2.json")
                for s in json.loads((C / f).read_text())["subjects"]}
    out = []
    for sid, chapters, *_ in CORE_ORDER:
        notes = subjects[sid]["notes"]
        idxs = range(1, len(notes) + 1) if chapters is None else chapters
        out += [f"{sid}:{notes[i - 1]['id']}" for i in idxs if i <= len(notes)]
    return out


def core_sd():
    """The system design topics the plan schedules."""
    from core_order import CASES, LLD_FUND, LLD_PROB, SD_SKIP
    hld = json.loads((C / "system-design-hld.json").read_text())
    senior = json.loads((C / "system-design-senior.json").read_text())
    ids = [t["id"] for t in hld["concepts"] + senior["topics"] if t["id"] not in SD_SKIP]
    return sorted(set(ids + CASES + LLD_FUND + LLD_PROB))


def core():
    import learn_core
    return {"qa": learn_core.QA_SHORT, "notes": learn_core.NOTES, "core": core_qa(), "dupOf": learn_core.DUP_OF,
            "coreNotes": core_notes(), "coreSd": core_sd()}


FILES = {"learn-dsa.json": dsa, "learn-core.json": core}


def render(data):
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


def build_all():
    return {name: fn() for name, fn in FILES.items()}


if __name__ == "__main__":
    for name, data in build_all().items():
        (C / name).write_text(render(data))
        print(f"{name}: written")
