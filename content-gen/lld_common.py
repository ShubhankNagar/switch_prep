import json, os, re, subprocess, tempfile, shutil

PARTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lld_parts")
os.makedirs(PARTS, exist_ok=True)

RG = {"title": "Refactoring.Guru - Design Patterns", "url": "https://refactoring.guru/design-patterns"}
ALLD = {"title": "awesome-low-level-design (GitHub)", "url": "https://github.com/ashishps1/awesome-low-level-design"}
WAT = {"title": "workat.tech - Machine Coding Round Guide", "url": "https://workat.tech/machine-coding/article/how-to-practice-for-machine-coding-kp0oj3sw2jca"}
JDOC = {"title": "Java SE Docs - java.util.concurrent", "url": "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/package-summary.html"}


def T(id, title, order, level, minutes, summary, content, keyPoints, qa, sources):
    assert level in ("Basic", "Intermediate", "Advanced")
    assert 5 <= len(keyPoints) <= 8, (id, len(keyPoints))
    assert 3 <= len(qa) <= 5, (id, len(qa))
    return {
        "id": id, "title": title, "order": order, "level": level, "minutes": minutes,
        "summary": summary.strip(), "content": content.strip(),
        "keyPoints": keyPoints,
        "interviewQuestions": [{"q": q, "a": a.strip()} for q, a in qa],
        "sources": sources,
    }


def words(s):
    return len(re.findall(r"\S+", s))


def check_java(topic, run=True):
    """Concatenate java blocks of a topic into Main.java, compile and run."""
    blocks = re.findall(r"```java\n(.*?)```", topic["content"], re.S)
    src = "\n".join(blocks)
    if "public class Main" not in src:
        return "no-main"
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, "Main.java"), "w") as f:
            f.write(src)
        r = subprocess.run(["javac", "-nowarn", "Main.java"], cwd=d, capture_output=True, text=True)
        if r.returncode != 0:
            return "COMPILE FAIL\n" + r.stderr[:3000]
        if run:
            r = subprocess.run(["java", "Main"], cwd=d, capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                return "RUN FAIL\n" + r.stderr[:2000]
            return "OK: " + r.stdout.strip().replace("\n", " | ")[:700]
        return "OK"
    finally:
        shutil.rmtree(d)


def save(name, key, topics, verify=True):
    for t in topics:
        msg = check_java(t) if verify else ""
        aw = [words(qa["a"]) for qa in t["interviewQuestions"]]
        print(f"{t['id']}: {words(t['content'])} words, qa words {aw} :: {msg}")
    with open(os.path.join(PARTS, name + ".json"), "w") as f:
        json.dump({"key": key, "topics": topics}, f, ensure_ascii=False, indent=1)
