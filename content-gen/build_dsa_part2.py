import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsa2_p10_backtracking, dsa2_p11_graphs, dsa2_p12_advgraphs, dsa2_p13_dp1d, dsa2_p14_dp2d, dsa2_p15_greedy, dsa2_p16_intervals, dsa2_p17_mathbit

mods = [dsa2_p10_backtracking, dsa2_p11_graphs, dsa2_p12_advgraphs, dsa2_p13_dp1d, dsa2_p14_dp2d, dsa2_p15_greedy, dsa2_p16_intervals, dsa2_p17_mathbit]
data = {"patterns": [m.PATTERN for m in mods]}
NOT_MUST = {"palindrome-partitioning","n-queens","clone-graph","word-ladder","redundant-connection","alien-dictionary",
 "cheapest-flights-within-k-stops","decode-ways","partition-equal-subset-sum","maximum-product-subarray",
 "longest-increasing-path-in-a-matrix","target-sum","coin-change-ii","jump-game-ii","partition-labels","non-overlapping-intervals"}
for pat in data["patterns"]:
    for p in pat["problems"]:
        if p["id"] in NOT_MUST: p["mustDo"] = False
ids = [p["id"] for pat in data["patterns"] for p in pat["problems"]]
assert len(ids) == len(set(ids)), "duplicate slugs"
for pat in data["patterns"]:
    for p in pat["problems"]:
        assert p["difficulty"] in ("Easy", "Medium", "Hard")
out = "/home/claude/switch-prep/frontend/public/content/dsa-part2.json"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
for pat in data["patterns"]:
    ps = pat["problems"]
    print(pat["order"], pat["id"], len(ps), "mustDo", sum(p["mustDo"] for p in ps), "introWords", len(pat["intro"].split()))
print("total", len(ids), "mustDo", sum(p["mustDo"] for pat in data["patterns"] for p in pat["problems"]))
