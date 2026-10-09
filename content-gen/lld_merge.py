import json, os, glob
from lld_common import PARTS
out = {"fundamentals": [], "problems": []}
for f in sorted(glob.glob(os.path.join(PARTS, "*.json"))):
    d = json.load(open(f))
    out[d["key"]].extend(d["topics"])
for k in out:
    out[k].sort(key=lambda t: t["order"])
    ids = [t["id"] for t in out[k]]
    assert len(ids) == len(set(ids)), k
path = "/home/claude/switch-prep/frontend/public/content/system-design-lld.json"
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
d = json.load(open(path))
req = {"id","title","order","level","minutes","summary","content","keyPoints","interviewQuestions","sources"}
for k in d:
    for t in d[k]:
        assert set(t) == req, t["id"]
        assert 5 <= len(t["keyPoints"]) <= 8 and 3 <= len(t["interviewQuestions"]) <= 5
print("fundamentals:", len(d["fundamentals"]), [t["id"] for t in d["fundamentals"]])
print("problems:", len(d["problems"]), [t["id"] for t in d["problems"]])
print("interviewQuestions:", sum(len(t["interviewQuestions"]) for k in d for t in d[k]))
print("bytes:", os.path.getsize(path))
