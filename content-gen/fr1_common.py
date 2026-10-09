import json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))


def M(topic, q, options, answer, explanation, asked):
    return dict(topic=topic, q=q.strip(), options=options, answer=answer,
                explanation=explanation.strip(), askedAt=asked)


def C(title, difficulty, asked, statement, hints, solution, explanation, time, space, leetcode):
    return dict(title=title, difficulty=difficulty, askedAt=asked, statement=statement.strip(),
                hints=hints, solution=solution.strip("\n"), explanation=explanation.strip(),
                time=time, space=space, leetcode=leetcode)


def T(q, a, asked):
    return dict(q=q, a=a.strip(), askedAt=asked)


def wc(s):
    return len(s.split())


def build(day, title, theme, mcqs, coding, theory):
    d = {"day": day, "title": title, "theme": theme, "mcqs": [], "coding": [], "theory": []}
    for i, m in enumerate(mcqs):
        assert len(m["options"]) == 4 and 0 <= m["answer"] <= 3, m["q"]
        assert len(set(m["options"])) == 4, m["q"]
        assert m["askedAt"], m["q"]
        mid = f"fr-d{day}-m{i+1}"
        # deterministic shuffle so correct answers are spread across A-D
        correct = m["options"][m["answer"]]
        opts = list(m["options"])
        random.Random(mid + "-fr1").shuffle(opts)
        m = {**m, "options": opts, "answer": opts.index(correct)}
        d["mcqs"].append({"id": mid, **m})
    for i, c in enumerate(coding):
        assert c["difficulty"] in ("Easy", "Medium", "Hard")
        assert len(c["hints"]) == 2
        d["coding"].append({"id": f"fr-d{day}-c{i+1}", **c})
    for i, t in enumerate(theory):
        d["theory"].append({"id": f"fr-d{day}-t{i+1}", **t})
    assert len(d["mcqs"]) == 20, len(d["mcqs"])
    assert len(d["coding"]) == 4
    assert len(d["theory"]) == 6
    me = [wc(m["explanation"]) for m in d["mcqs"]]
    ce = [wc(c["explanation"]) for c in d["coding"]]
    te = [wc(t["a"]) for t in d["theory"]]
    print(f"day{day}: mcq expl {min(me)}-{max(me)} | coding expl {min(ce)}-{max(ce)} | theory {min(te)}-{max(te)}")
    for m in d["mcqs"]:
        if not 20 <= wc(m["explanation"]) <= 80:
            print("  WARN mcq", m["id"], wc(m["explanation"]))
    for c in d["coding"]:
        if not 50 <= wc(c["explanation"]) <= 150:
            print("  WARN coding", c["id"], wc(c["explanation"]))
    for t in d["theory"]:
        if not 50 <= wc(t["a"]) <= 150:
            print("  WARN theory", t["id"], wc(t["a"]))
    return d
