"""Shared helpers for the Interview Rounds 2027 content (rounds.json)."""
import re
import textwrap

FREQ = ("Almost every loop", "Most product companies", "Some companies")


def md(s):
    return textwrap.dedent(s).strip("\n").strip()


def words(s):
    return len(re.findall(r"\S+", s))


def S(title, url):
    assert url.startswith("https://"), url
    return {"title": title, "url": url}


def P(title, link):
    assert link.startswith("/"), link
    return {"title": title, "link": link}


def ROUND(id, order, title, icon, summary, whoRunsIt, frequency, weight, format, whatTheyTest,
          rubric, howToAce, walkthrough, commonFailures, practice, sources):
    assert frequency in FREQ, (id, frequency)
    assert 4 <= len(whatTheyTest) <= 7, (id, "whatTheyTest", len(whatTheyTest))
    assert 5 <= len(commonFailures) <= 8, (id, "commonFailures", len(commonFailures))
    assert 4 <= len(practice) <= 8, (id, "practice", len(practice))
    assert len(sources) >= 3, (id, "sources")
    r = {
        "id": id,
        "order": order,
        "title": title,
        "icon": icon,
        "summary": " ".join(md(summary).split()),
        "whoRunsIt": whoRunsIt,
        "frequency": frequency,
        "weight": weight,
        "format": md(format),
        "whatTheyTest": whatTheyTest,
        "rubric": md(rubric),
        "howToAce": md(howToAce),
        "walkthrough": md(walkthrough),
        "commonFailures": commonFailures,
        "practice": practice,
        "sources": sources,
    }
    return r
