"""Merges sd_part1..8.json into frontend/public/content/system-design-hld.json."""
import json, os
from sd_common import HERE
CONCEPTS = ["how-to-approach","back-of-envelope","scalability-basics","load-balancing","caching",
 "databases-sql-vs-nosql","indexing-internals","replication","sharding-partitioning","consistent-hashing",
 "cap-pacelc-consistency","transactions-isolation","message-queues","api-design","rate-limiting",
 "cdn-blob-storage","microservices-patterns","observability","security-auth","unique-id-generation",
 "search-elasticsearch","distributed-coordination"]
CASES = ["url-shortener","rate-limiter-design","chat-whatsapp","news-feed","notification-system",
 "ride-hailing-uber","ecommerce-flipkart-checkout","ticket-booking-bookmyshow","video-streaming-youtube",
 "search-autocomplete","distributed-cache","payment-system-upi","file-storage-dropbox",
 "food-delivery-swiggy","web-crawler"]
allt = {}
for i in range(1, 9):
    for t in json.load(open(os.path.join(HERE, f"sd_part{i}.json"), encoding="utf-8")):
        assert t["id"] not in allt, t["id"]
        allt[t["id"]] = t
def build(ids):
    out = []
    for n, i in enumerate(ids, 1):
        t = dict(allt.pop(i)); t["order"] = n; out.append(t)
    return out
data = {"concepts": build(CONCEPTS), "caseStudies": build(CASES)}
assert not allt, allt.keys()
out = os.path.join(HERE, "..", "frontend", "public", "content", "system-design-hld.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
d = json.load(open(out, encoding="utf-8"))
for k in ("concepts", "caseStudies"):
    for t in d[k]:
        assert t["level"] in ("Basic","Intermediate","Advanced")
        assert 5 <= len(t["keyPoints"]) <= 8, t["id"]
        assert 4 <= len(t["interviewQuestions"]) <= 6, t["id"]
        for q in t["interviewQuestions"]:
            w = len(q["a"].split())
            if not 40 <= w <= 120: print("WARN answer words", t["id"], w)
        assert t["sources"]
    print(k, len(d[k]), "topics,", sum(len(t["content"].split()) for t in d[k]), "words,",
          sum(len(t["interviewQuestions"]) for t in d[k]), "questions")
