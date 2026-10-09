"""Compiles every complete Java example (a ```java block that starts with 'import' or 'package')
found in senior1_parts/*.json, each in its own directory, against the jars in ~/.m2 (newest version per artifact)."""
import glob, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
M2 = os.path.expanduser("~/.m2/repository")


def vkey(v):
    return [int(p) if p.isdigit() else -1 for p in re.split(r"[.\-]", v)]


def classpath():
    best = {}
    for jar in glob.glob(f"{M2}/**/*.jar", recursive=True):
        if jar.endswith(("-sources.jar", "-javadoc.jar")):
            continue
        ver_dir = os.path.dirname(jar)
        art_dir, ver = os.path.dirname(ver_dir), os.path.basename(ver_dir)
        if art_dir not in best or vkey(ver) > vkey(best[art_dir][0]):
            best[art_dir] = (ver, jar)
    return ":".join(j for _, j in best.values())


def blocks(text):
    return re.findall(r"```java\n(.*?)```", text, re.S)


def main(files):
    cp = classpath()
    work = tempfile.mkdtemp(prefix="senior1_java_", dir=os.environ.get("JCHECK_DIR"))
    total = failed = 0
    for f in files:
        subj = json.load(open(f))
        items = [(n["id"], n["content"]) for n in subj["notes"]] + [(q["id"], q["a"]) for q in subj["qa"]]
        for iid, text in items:
            for k, code in enumerate(blocks(text)):
                if not code.lstrip().startswith(("import ", "package ")):
                    continue
                total += 1
                m = re.search(r"public\s+(?:final\s+|abstract\s+)?(?:class|interface|record|enum)\s+(\w+)", code)
                name = m.group(1) if m else "Example"
                d = os.path.join(work, f"{iid}_{k}")
                os.makedirs(d, exist_ok=True)
                src = os.path.join(d, f"{name}.java")
                open(src, "w").write(code)
                r = subprocess.run(["javac", "-proc:none", "-nowarn", "-cp", cp, "-d", d, src],
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    failed += 1
                    print(f"FAIL {iid} block {k} ({name}):\n{r.stderr[:3000]}")
    print(f"compiled {total} complete examples, {failed} failed")
    return failed


if __name__ == "__main__":
    fs = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "senior1_parts", "*.json")))
    sys.exit(1 if main(fs) else 0)
