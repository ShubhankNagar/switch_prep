import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
def T(id, title, level, summary, content, keyPoints, qa, sources, minutes=None):
    words = len(content.split())
    return {"id": id, "title": title, "order": 0, "level": level,
            "minutes": minutes or max(4, round(words / 180)),
            "summary": summary, "content": content.strip(),
            "keyPoints": keyPoints,
            "interviewQuestions": [{"q": q, "a": a.strip()} for q, a in qa],
            "sources": [{"title": t, "url": u} for t, u in sources]}
def dump(name, topics):
    p = os.path.join(HERE, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=1)
    for t in topics:
        print(t["id"], len(t["content"].split()), "words", len(t["keyPoints"]), "kp", len(t["interviewQuestions"]), "qa")
PRIMER = ("System Design Primer (donnemartin)", "https://github.com/donnemartin/system-design-primer")
DDIA = ("Designing Data-Intensive Applications - Martin Kleppmann", "https://dataintensive.net/")
BBG = ("ByteByteGo Blog", "https://blog.bytebytego.com/")
HI = ("Hello Interview - System Design in a Hurry", "https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction")
