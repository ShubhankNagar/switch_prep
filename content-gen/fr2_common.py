import json, os, random
PARTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fr2_parts')
os.makedirs(PARTS, exist_ok=True)

def M(topic, q, options, answer, explanation, askedAt):
    assert len(options) == 4 and 0 <= answer <= 3
    return {"topic": topic, "q": q.strip(), "options": options, "answer": answer,
            "explanation": explanation.strip(), "askedAt": askedAt}

def C(title, difficulty, askedAt, statement, hints, solution, explanation, time, space, leetcode):
    assert difficulty in ("Easy", "Medium", "Hard") and len(hints) == 2
    return {"title": title, "difficulty": difficulty, "askedAt": askedAt, "statement": statement.strip(),
            "hints": hints, "solution": solution.strip('\n'), "explanation": explanation.strip(),
            "time": time, "space": space, "leetcode": leetcode}

def T(q, a, askedAt):
    return {"q": q, "a": a.strip(), "askedAt": askedAt}

def save(day, title, theme, mcqs, coding, theory):
    assert len(mcqs) == 20, len(mcqs)
    assert len(coding) == 4, len(coding)
    assert len(theory) == 6, len(theory)
    out_m = []
    for i, m in enumerate(mcqs, 1):
        mid = f"fr-d{day}-m{i}"
        opts = list(m["options"]); correct = opts[m["answer"]]
        random.Random(mid).shuffle(opts)
        m = dict(m, options=opts, answer=opts.index(correct))
        out_m.append({"id": mid, **m})
    out_c = [{"id": f"fr-d{day}-c{i}", **c} for i, c in enumerate(coding, 1)]
    out_t = [{"id": f"fr-d{day}-t{i}", **t} for i, t in enumerate(theory, 1)]
    d = {"day": day, "title": title, "theme": theme, "mcqs": out_m, "coding": out_c, "theory": out_t}
    with open(os.path.join(PARTS, f'day{day}.json'), 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print('saved day', day)
