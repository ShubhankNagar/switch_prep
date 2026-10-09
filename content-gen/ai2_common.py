"""Shared helpers for the AI Engineer course (part 2) generators."""
import textwrap


def Q(q, options, answer, explanation):
    assert len(options) == 4 and 0 <= answer <= 3
    return {"q": q, "options": options, "answer": answer, "explanation": explanation}


def R(title, url, type_):
    assert type_ in ("video", "article", "course", "docs", "book")
    return {"title": title, "url": url, "type": type_}


def L(id, title, minutes, content, exercise, quiz, resources):
    assert len(quiz) == 3, id
    return {
        "id": id,
        "title": title,
        "minutes": minutes,
        "content": textwrap.dedent(content).strip(),
        "exercise": textwrap.dedent(exercise).strip(),
        "quiz": quiz,
        "resources": resources,
    }


def M(id, order, title, level, weeks, description, outcomes, lessons, project):
    assert 5 <= len(lessons) <= 7, id
    for l in lessons:
        assert l["id"].startswith(id.split("-")[0] + "-"), l["id"]
    return {
        "id": id,
        "order": order,
        "title": title,
        "level": level,
        "weeks": weeks,
        "description": description,
        "outcomes": outcomes,
        "lessons": lessons,
        "project": {"title": project[0], "description": textwrap.dedent(project[1]).strip()},
    }
