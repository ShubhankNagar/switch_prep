"""Shared helpers for the AI Engineer course (part 1) generators."""
import hashlib
import random
import textwrap


def Q(q, options, answer, explanation):
    assert len(options) == 4 and 0 <= answer <= 3
    # deterministic shuffle so correct answers are spread across positions
    rng = random.Random(int(hashlib.md5(q.encode()).hexdigest(), 16))
    order = list(range(4))
    rng.shuffle(order)
    shuffled = [options[i] for i in order]
    return {"q": q, "options": shuffled, "answer": order.index(answer), "explanation": explanation}


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
