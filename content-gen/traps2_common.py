"""Shared helpers for traps-2.json generation (areas: dsa, system-design, distributed-systems,
api-design, angular-js, os-networking, behavioral)."""
import re

AREAS = ["dsa", "system-design", "distributed-systems", "api-design", "angular-js", "os-networking", "behavioral"]
LEVELS = ["Basic", "Intermediate", "Advanced"]
FREQS = ["Very common", "Common"]


def T(id, area, title, level, frequency, prompt, commonWrongAnswer, whyPeopleGetItWrong, correct,
      interviewTip, options=None, answer=None, fix=None, askedAt=None):
    return {
        "id": id,
        "area": area,
        "title": title,
        "level": level,
        "frequency": frequency,
        "prompt": prompt.strip(),
        "options": options,
        "answer": answer,
        "commonWrongAnswer": commonWrongAnswer.strip(),
        "whyPeopleGetItWrong": whyPeopleGetItWrong.strip(),
        "correct": correct.strip(),
        "fix": fix.strip() if fix else None,
        "interviewTip": interviewTip.strip(),
        "askedAt": askedAt or [],
    }


def words(md):
    # strip fenced code, count words of prose
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    return len(re.findall(r"[A-Za-z0-9₹'’/+.<>=%-]+", md))


def validate(traps):
    errs = []
    ids = set()
    for t in traps:
        tid = t["id"]
        if tid in ids:
            errs.append(f"dup id {tid}")
        ids.add(tid)
        if not tid.startswith(f"trap-{t['area']}-"):
            errs.append(f"{tid}: id prefix")
        if t["area"] not in AREAS:
            errs.append(f"{tid}: area")
        if t["level"] not in LEVELS:
            errs.append(f"{tid}: level")
        if t["frequency"] not in FREQS:
            errs.append(f"{tid}: frequency")
        if t["options"] is not None:
            if len(t["options"]) != 4 or not isinstance(t["answer"], int) or not 0 <= t["answer"] <= 3:
                errs.append(f"{tid}: options/answer")
        elif t["answer"] is not None:
            errs.append(f"{tid}: answer without options")
        w = words(t["whyPeopleGetItWrong"])
        if not 38 <= w <= 105:
            errs.append(f"{tid}: why words {w}")
        c = words(t["correct"])
        if not 58 <= c <= 185:
            errs.append(f"{tid}: correct words {c}")
        for f in ["commonWrongAnswer", "interviewTip"]:
            s = t[f]
            if s.count(". ") > 1:
                errs.append(f"{tid}: {f} more than one sentence?")
        for f in ["prompt", "correct", "fix", "whyPeopleGetItWrong"]:
            v = t[f] or ""
            if v.count("```") % 2:
                errs.append(f"{tid}: unbalanced fence in {f}")
    return errs
