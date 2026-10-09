"""Merge traps2_* chunks into frontend/public/content/traps-2.json and validate."""
import importlib, json, sys
from collections import Counter
from traps2_common import validate, words

CHUNKS = ["traps2_dsa", "traps2_sd", "traps2_ds", "traps2_api", "traps2_ng", "traps2_os", "traps2_beh"]
OUT = "/home/claude/switch-prep/frontend/public/content/traps-2.json"


def main():
    only = sys.argv[1:]
    traps = []
    for m in (only or CHUNKS):
        traps += importlib.import_module(m).TRAPS
    errs = validate(traps)
    for e in errs:
        print("ERR", e)
    if only:
        for t in traps:
            print(f"{t['id']}: why={words(t['whyPeopleGetItWrong'])} correct={words(t['correct'])}")
        return
    if errs:
        sys.exit(1)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"traps": traps}, f, ensure_ascii=False, indent=1)
    data = json.load(open(OUT, encoding="utf-8"))
    c = Counter(t["area"] for t in data["traps"])
    print("total", len(data["traps"]), dict(c))


if __name__ == "__main__":
    main()
