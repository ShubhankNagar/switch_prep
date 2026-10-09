"""Compile/run every code check declared by traps2_* chunk modules.
Usage: python3 traps2_verify.py [module ...]   (default: all chunks)"""
import importlib, json, os, subprocess, sys, tempfile

CHUNKS = ["traps2_dsa", "traps2_sd", "traps2_ds", "traps2_api", "traps2_ng", "traps2_os", "traps2_beh"]
SCRATCH = os.environ.get("TRAPS2_SCRATCH", tempfile.gettempdir())
FRONT = "/home/claude/switch-prep/frontend"


def run_check(c):
    d = tempfile.mkdtemp(prefix="t2_", dir=SCRATCH)
    lang = c["lang"]
    if lang == "java":
        p = os.path.join(d, "Main.java")
        open(p, "w").write(c["code"])
        cmd = ["java", p]
    elif lang == "js":
        p = os.path.join(d, "main.js")
        open(p, "w").write(c["code"])
        cmd = ["node", p]
    elif lang == "ts":  # type-check only, against the Angular app's node_modules
        p = os.path.join(d, "main.ts")
        open(p, "w").write(c["code"])
        cfg = {"compilerOptions": {"strict": True, "target": "ES2022", "module": "ES2022", "moduleResolution": "bundler",
                                   "experimentalDecorators": True, "useDefineForClassFields": False, "noEmit": True,
                                   "skipLibCheck": True, "lib": ["ES2022", "DOM"], "baseUrl": FRONT + "/node_modules",
                                   "paths": {"*": [FRONT + "/node_modules/*"]}, "typeRoots": [FRONT + "/node_modules/@types"]},
               "files": [p]}
        json.dump(cfg, open(os.path.join(d, "tsconfig.json"), "w"))
        cmd = [FRONT + "/node_modules/.bin/tsc", "-p", os.path.join(d, "tsconfig.json")]
    else:
        raise ValueError(lang)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    out = (r.stdout + r.stderr).replace("Picked up JAVA_TOOL_OPTIONS", "")
    ok = all(e in out for e in c.get("expect", []))
    if lang == "ts":
        ok = ok and r.returncode == 0
    if c.get("expect_fail"):
        ok = r.returncode != 0 and all(e in out for e in c.get("expect", []))
    elif lang != "ts" and r.returncode != 0 and not c.get("allow_nonzero"):
        ok = False
    return ok, out


def main():
    mods = sys.argv[1:] or CHUNKS
    bad = 0
    total = 0
    for m in mods:
        mod = importlib.import_module(m)
        for c in getattr(mod, "CHECKS", []):
            total += 1
            ok, out = run_check(c)
            status = "OK  " if ok else "FAIL"
            print(f"{status} {c['name']}")
            if not ok:
                bad += 1
                print("   expected:", c.get("expect"))
                print("   " + out.strip().replace("\n", "\n   ")[:3000])
    print(f"{total - bad}/{total} checks passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
