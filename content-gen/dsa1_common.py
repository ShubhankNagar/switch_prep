import textwrap


def P(id, title, diff, comp, summary, approach, sol, time, space, must=False):
    assert diff in ("Easy", "Medium", "Hard"), id
    return {
        "id": id,
        "title": title,
        "difficulty": diff,
        "companies": [c.strip() for c in comp.split(",") if c.strip()],
        "leetcode": f"https://leetcode.com/problems/{id}/",
        "summary": " ".join(summary.split()),
        "approach": textwrap.dedent(approach).strip(),
        "solution": textwrap.dedent(sol).strip("\n"),
        "time": time,
        "space": space,
        "mustDo": must,
    }


def PAT(id, name, order, intro, problems):
    return {"id": id, "name": name, "order": order,
            "intro": textwrap.dedent(intro).strip(), "problems": problems}
