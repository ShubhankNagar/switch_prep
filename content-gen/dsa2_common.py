def P(slug, title, diff, companies, summary, approach, solution, time, space, must):
    return {
        "id": slug,
        "title": title,
        "difficulty": diff,
        "companies": companies,
        "leetcode": f"https://leetcode.com/problems/{slug}/",
        "summary": summary.strip(),
        "approach": approach.strip(),
        "solution": solution.strip("\n"),
        "time": time,
        "space": space,
        "mustDo": must,
    }
