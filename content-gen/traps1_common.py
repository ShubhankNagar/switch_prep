"""Shared helpers for traps-1.json generation (java, concurrency, spring, jpa-hibernate, sql)."""
import re

AREAS = {"java", "concurrency", "spring", "jpa-hibernate", "sql"}
LEVELS = {"Basic", "Intermediate", "Advanced"}
FREQS = {"Very common", "Common"}


def T(id, area, title, level, frequency, prompt, options, answer, wrong, why, correct, fix, tip, asked=()):
    return {
        "id": id,
        "area": area,
        "title": title,
        "level": level,
        "frequency": frequency,
        "prompt": prompt.strip(),
        "options": options,
        "answer": answer,
        "commonWrongAnswer": wrong.strip(),
        "whyPeopleGetItWrong": why.strip(),
        "correct": correct.strip(),
        "fix": fix.strip() if fix else None,
        "interviewTip": tip.strip(),
        "askedAt": list(asked),
    }


def words(md):
    # count words outside fenced code blocks
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    return len(md.split())


def check(traps):
    problems = []
    for t in traps:
        tid = t["id"]
        if not tid.startswith("trap-" + t["area"] + "-"):
            problems.append(f"{tid}: id/area mismatch")
        if t["area"] not in AREAS:
            problems.append(f"{tid}: bad area")
        if t["level"] not in LEVELS:
            problems.append(f"{tid}: bad level")
        if t["frequency"] not in FREQS:
            problems.append(f"{tid}: bad frequency")
        o, a = t["options"], t["answer"]
        if o is None:
            if a is not None:
                problems.append(f"{tid}: answer without options")
        else:
            if len(o) != 4 or len(set(o)) != 4:
                problems.append(f"{tid}: need 4 distinct options")
            if not isinstance(a, int) or not 0 <= a <= 3:
                problems.append(f"{tid}: bad answer index")
        w = words(t["whyPeopleGetItWrong"])
        if not 40 <= w <= 100:
            problems.append(f"{tid}: why words {w}")
        w = words(t["correct"])
        if not 60 <= w <= 180:
            problems.append(f"{tid}: correct words {w}")
        if t["prompt"].count("```") % 2 or (t["fix"] or "").count("```") % 2:
            problems.append(f"{tid}: unbalanced code fence")
    return problems
