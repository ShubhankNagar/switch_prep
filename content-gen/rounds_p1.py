"""Interview Rounds 2027, part 1: online assessment, DSA live coding, AI-assisted coding, practical coding."""
from rounds_common import ROUND, S, P

# Shared sources
SRC_FLIPKART_2026 = S("Flipkart SDE-2 interview experience, Jan 2026 offline drive (LeetCode Discuss)",
                      "https://leetcode.com/discuss/post/8455829/flipkart-sde-2-interview-experience-jan-o8ngx/")
SRC_AMAZON_2025 = S("Amazon SDE-2 Bangalore, July 2025 [Offer] (LeetCode Discuss)",
                    "https://leetcode.com/discuss/post/7009755/amazon-sde-2-bangalore-4-yoe-july-2025-o-o826/")
SRC_UBER = S("Uber SDE-2 Bangalore interview experience (Roundz)",
             "https://roundz.substack.com/p/interview-experience-169-uber-sde2")
SRC_TECHINT_2026 = S("What actually changed in tech interviews in 2026 (techinterview.org)",
                     "https://www.techinterview.org/post/3233475417/what-changed-tech-interviews-2026/")
SRC_74 = S("Where LeetCode still matters in 2026: 74 interviews across 8 companies (LeetCode Discuss)",
           "https://leetcode.com/discuss/post/8446005/")
SRC_PREPFULLY = S("Software engineer interview rubric 2026 (Prepfully)",
                  "https://prepfully.com/interview-guides/software-engineer-interview-rubric-2026")
SRC_HI_META = S("Meta's AI-enabled coding interview (Hello Interview)",
                "https://www.hellointerview.com/blog/meta-ai-enabled-coding")
SRC_IIO_META = S("How to use AI in Meta's AI-assisted coding interview (interviewing.io)",
                 "https://interviewing.io/blog/how-to-use-ai-in-meta-s-ai-assisted-coding-interview-with-real-prompts-and-examples")
SRC_GOOGLE_AI = S("Google's AI-assisted coding interview, 2026 guide (University of Miami career blog)",
                  "https://customcareer.miami.edu/blog/2026/05/14/googles-ai-assisted-coding-interview-2026-guide/")
SRC_LEVELOP_GOOGLE = S("Google coding interviews in 2026: what changed and what didn't (Levelop)",
                       "https://levelop.dev/blog/google-coding-interviews-in-2026-what-changed-and-what-didnt")
SRC_CANVA = S("Yes, you can use AI in our interviews (Canva Engineering)",
              "https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews")
SRC_STRIPE = S("Stripe software engineer interview guide: coding, bug bash, integration (Aced)",
               "https://www.aced.io/guides/stripe-software-engineer-interview")
SRC_ATLASSIAN = S("Atlassian SDE3 India interview experience, 2024 [Offer] (LeetCode Discuss)",
                  "https://leetcode.com/discuss/interview-experience/4965703/")
SRC_ICF = S("CodeSignal Industry Coding Framework explained (Lodely)",
            "https://www.lodely.com/blog/industry-coding-framework")
SRC_CS_HR = S("CodeSignal vs HackerRank for candidates: scoring and proctoring (PracHub)",
              "https://prachub.com/resources/codesignal-vs-hackerrank-for-candidates-scoring-proctoring-question-formats-and-score-reports")

# ---------------------------------------------------------------------------
ONLINE_ASSESSMENT = ROUND(
    id="online-assessment", order=1, title="Online Assessment (OA)", icon="🧪",
    summary="""
    A timed, auto-graded coding test (HackerRank, CodeSignal, HackerEarth) that filters you before any engineer sees
    you. For SDE-2 it is usually two medium to medium-hard problems in 60-120 minutes, scored by hidden test cases.
    """,
    whoRunsIt=["Amazon", "Flipkart", "Uber", "Swiggy", "Goldman Sachs", "Walmart Global Tech", "Atlassian (Karat)",
               "Microsoft"],
    frequency="Most product companies",
    weight="Gate: pass/fail, rarely discussed later",
    format="""
    - **Duration:** 60-120 minutes. Usually 2 coding problems, sometimes 3, plus optional MCQs on Java, SQL, OS or aptitude.
    - **Platform:** HackerRank, CodeSignal, HackerEarth or the company's own portal. You run code against sample tests, then submit against hidden tests.
    - **Scoring:** automatic and per test case, so a brute force that passes 60% of cases scores more than a clever solution that times out.
    - **Proctoring:** tab-switch logs, full-screen mode, blocked paste, sometimes webcam and photo ID, and plagiarism comparison across candidates. **No AI tools.**
    - **Variants:**
      - Amazon adds a *work-style simulation*: scenario questions on trade-offs such as quick patch vs proper fix, or latency vs durability.
      - Atlassian uses a live **Karat** screen: about 20 minutes of rapid design questions, then two coding problems with a human watching. A retake within 48 hours was allowed in one 2024 report.
      - CodeSignal's *Industry Coding* format: one project (for example an in-memory store) extended over 4 levels in about 90 minutes.
    - **Difficulty in 2025-26 SDE-2 reports:** graph/BFS with a twist and a trie (Flipkart, Jan 2026), DP state transition and constrained shortest path (Amazon, Jul 2025), near-hard BST/deque/graph problems (Uber on CodeSignal).
    """,
    whatTheyTest=[
        "Spotting the pattern behind a disguised medium problem within 5-10 minutes",
        "Choosing a complexity that fits the constraints (n = 10^5 means O(n log n) or better)",
        "Edge cases that hidden tests always contain: empty input, one element, duplicates, negatives, maximum n, overflow",
        "Java fluency under a timer: collections, comparators, long arithmetic, fast input reading",
        "Splitting time across 2-3 problems to collect partial credit",
        "Integrity: flagged attempts are rejected whatever the score",
    ],
    rubric="""
    No engineer reads your code at this stage unless something is flagged. The platform produces a score, and the
    recruiter applies a cutoff set for the role. The cutoff rises in hiring drives with many applicants.

    | What you submit | Typical SDE-2 outcome |
    |---|---|
    | Both problems pass every hidden test | Clear pass, often fast-tracked |
    | One fully solved, one at 60%+ of tests | Usually passes; borderline in big drives |
    | One fully solved, nothing on the other | Coin flip, depends on the cutoff |
    | Only partial scores, or timeouts on large tests | Usually rejected |
    | Plagiarism, tab-switch or proctoring flags | Rejected regardless of score |

    **What silently costs points:** Time Limit Exceeded on the big cases (wrong complexity), `int` overflow in sums or
    counts, wrong output format, and code that only handles the sample. If you clear the OA, the next interviewer may
    open your submission and ask you to explain it, so write code you can defend.
    """,
    howToAce="""
    **Before the test**

    1. Do one practice test on the real platform (HackerRank and CodeSignal both have free practice areas) so the editor, input reading and the Run vs Submit buttons hold no surprises.
    2. Keep a Java toolkit in your head: `long` for sums and counts, `ArrayDeque` instead of `Stack`, `PriorityQueue` with `Integer.compare` comparators, `HashMap.merge` for counting, `BufferedReader` when input is large.
    3. Take the test when you are sharpest, on a stable connection, with notifications off. Invites usually stay open 3-7 days, so warm up with one timed medium that morning.

    **During the test**

    1. **Read every problem first (3-4 minutes)** and start with the one you recognise. All points count the same.
    2. **Read the constraints before you think about the algorithm.** They tell you the target complexity:

    | n up to | Aim for |
    |---|---|
    | 20 | O(2^n), backtracking |
    | 500 | O(n^3) |
    | 5,000 | O(n^2) |
    | 10^5 to 10^6 | O(n log n) or O(n) |
    | 10^9 and above | O(log n) or a formula |

    3. **Bank partial credit.** If the optimal idea hasn't come after about 10 minutes, submit a correct brute force, note the score, then optimise.
    4. **Run your own edge cases before every submit:** empty or size-1 input, all-equal values, negatives, the maximum n, and an answer that needs `long`.
    5. **Timebox.** Split the time evenly. When a problem stalls, move on and come back with fresh eyes.
    6. **Stay inside the test window.** No tab switching, no pasting from outside. A flag costs more than a missed problem.

    **After the test**

    Write both problems down from memory and solve them properly within 24 hours. Rounds are often scheduled within a
    week, and interviewers sometimes open with "walk me through your OA solution".

    **Weekly practice on SwitchPrep**

    Three times a week, solve two unseen mediums from the DSA section in 70 minutes with a timer and no hints. Once a
    week, take a full Final Round mock day. Log which patterns cost you the most time and revise those notes instead of
    starting new topics.
    """,
    walkthrough="""
    **The problem (paraphrased OA style):** A warehouse records a net stock change for every hour: positive for
    inbound, negative for dispatch. Count the contiguous stretches of hours whose net change is exactly `k`.
    Constraints: `n <= 2 * 10^5`, each value between `-10^4` and `10^4`.

    **Minute 0-3: read the constraints first.** n = 2 * 10^5 rules out O(n^2), which would be about 2 * 10^10
    operations. The target is O(n) or O(n log n). Values can be **negative**, which is the trap: a sliding window only
    works when growing the window can only increase the sum. With negatives, shrinking from the left can raise the sum
    too, so the window logic breaks.

    **Minute 3-8: bank points.** The strong candidate writes the obvious double loop first, runs the samples and
    submits. It passes 7 of 15 tests and times out on the rest. Those 7 tests are now banked.

    **Minute 8-15: the real idea.** Let `prefix[i]` be the sum of the first i hours. The stretch from hour j to hour
    i-1 sums to `prefix[i] - prefix[j]`, so we need the number of earlier prefixes equal to `prefix[i] - k`. That is
    one HashMap lookup per hour:

    ```java
    static long countStretches(int[] change, int k) {
        Map<Long, Integer> seen = new HashMap<>();
        seen.put(0L, 1);                 // empty prefix: a stretch may start at hour 0
        long prefix = 0, count = 0;
        for (int c : change) {
            prefix += c;
            count += seen.getOrDefault(prefix - k, 0);
            seen.merge(prefix, 1, Integer::sum);
        }
        return count;
    }
    ```

    **Minute 15-20: edge cases before submitting.** The candidate checks three things on paper:

    - `k = 0` with input `[0, 0, 0]`: the answer is 6 (three single hours, two pairs, one triple). The `seen.put(0L, 1)` seed is what makes the stretches that start at hour 0 count.
    - **Overflow:** the count can reach n(n+1)/2, which is about 2 * 10^10 and does not fit in an `int`. Hence `long count`. The prefix itself is bounded by 2 * 10^9, uncomfortably close to `Integer.MAX_VALUE`, so it is a `long` too.
    - A single hour equal to k, and an input where no stretch matches (answer 0).

    Submit: 15/15. Total time is about 20 minutes, which leaves 50+ minutes for the second problem.

    **Three days later, the first live round opens like this:**

    > **Interviewer:** I see your OA. Walk me through the second problem.
    >
    > **Candidate:** Brute force was O(n^2) over all start and end pairs, which is too slow for 2 * 10^5. I didn't use a sliding window because the values can be negative, so the window sum isn't monotonic. Instead I count, for each prefix sum, how many earlier prefixes equal `prefix - k`. That's O(n) time and O(n) space for the map.
    >
    > **Interviewer:** What if I asked for the *longest* such stretch instead of the count?
    >
    > **Candidate:** Then I'd store the *first* index where each prefix value appears, never overwriting it, and at each hour compute `i - firstIndex[prefix - k]`. Same complexity.

    **Why this earns points:** the constraints decided the algorithm before any code was written. Partial credit was
    banked early. The negative-values trap was named, not discovered by failing tests. Overflow was handled on
    purpose. And because the candidate understood the solution, the OA turned into an easy first five minutes of the
    next round instead of an awkward one.
    """,
    commonFailures=[
        "Spending 50 minutes on the first problem and never reading the second",
        "Passing the samples but failing hidden tests through int overflow, empty input or off-by-one",
        "An O(n^2) solution on n = 10^5 because the constraints were never read",
        "Using sliding window on arrays that contain negative numbers",
        "Submitting nothing on a hard problem instead of a brute force that scores partial points",
        "Switching tabs or pasting code, which triggers a proctoring flag and an automatic reject",
        "Taking the test in an unfamiliar language or editor for the first time",
    ],
    practice=[
        P("Subarray Sum Equals K (prefix sums + HashMap)", "/dsa/arrays-hashing/subarray-sum-equals-k"),
        P("Longest Substring Without Repeating Characters", "/dsa/sliding-window/longest-substring-without-repeating-characters"),
        P("Koko Eating Bananas (binary search on the answer)", "/dsa/binary-search/koko-eating-bananas"),
        P("Implement Trie", "/dsa/tries/implement-trie-prefix-tree"),
        P("Coin Change (DP state transitions)", "/dsa/dp-1d/coin-change"),
        P("Final Round Day 1: Amazon-style OA", "/final-round/1"),
        P("Final Round Day 7: timed mock test", "/final-round/7"),
        P("DSA traps that fail hidden tests", "/traps?area=dsa"),
    ],
    sources=[SRC_FLIPKART_2026, SRC_AMAZON_2025, SRC_UBER, SRC_ATLASSIAN, SRC_CS_HR, SRC_ICF],
)

# ---------------------------------------------------------------------------
DSA_LIVE = ROUND(
    id="dsa-live-coding", order=2, title="DSA Live Coding (AI off, explain as you go)", icon="🧠",
    summary="""
    45-60 minutes of live problem solving with an engineer, no AI, where you must think out loud. It is still in
    almost every loop, but you are judged on how you reason and communicate as much as on the final code.
    """,
    whoRunsIt=["Google", "Amazon", "Microsoft", "Flipkart", "Uber", "Swiggy", "PhonePe", "Goldman Sachs", "LinkedIn"],
    frequency="Almost every loop",
    weight="~15-25% of the SDE-2 decision; a clear fail usually vetoes the loop",
    format="""
    - **Duration:** 45-60 minutes, one or two problems (medium, sometimes medium-hard), often with a follow-up extension ("now also print every operation").
    - **Setup:** a shared editor (CoderPad, HackerRank CodePair, an internal tool). Some have no run button, so you dry-run by hand. Offline drives (Flipkart, Jan 2026) can mean pseudocode on a whiteboard.
    - **Rules:** AI off, often no autocomplete. Expect interruptions such as "why a deque here?" or "what's the invariant?" because interviewers now check that the reasoning is yours.
    - **Where it sits:** 1-2 rounds per loop. Amazon pairs each coding round with two Leadership Principle questions, and the Bar Raiser round can include a coding problem as well.
    """,
    whatTheyTest=[
        "Clarifying the problem: inputs, constraints, edge cases, a worked example",
        "Moving from a brute force to an optimal approach, with the reason each step is faster",
        "Clean, correct Java: sensible names, small helpers, the right collections",
        "Testing your own code by dry run before the interviewer finds the bug",
        "Accurate time and space complexity, plus how it changes under a follow-up",
        "Talking while thinking, and taking a hint without getting defensive",
    ],
    rubric="""
    Most companies score four dimensions independently and then combine them. Rough calibration for SDE-2:

    | Dimension | Strong hire | Hire | No hire |
    |---|---|---|---|
    | Problem solving | Finds the optimal approach on their own and explains *why* it works | Reaches the optimum with one small hint | Needs repeated hints or stays at brute force |
    | Coding | Idiomatic, bug-light, readable, finished with time to spare | Working, minor bugs fixed when pointed out | Messy, unfinished, or language struggles |
    | Verification | Dry-runs, finds own bugs, lists edge cases unprompted | Tests when asked | No testing; the interviewer finds the bugs |
    | Communication | Narrates intent, invites feedback, answers follow-ups crisply | Mostly clear with some silent stretches | Long silences, can't explain own code |

    A finished optimal solution delivered in silence often scores lower than a slightly slower one where the
    interviewer could follow every decision. Working code with no tests or edge-case reasoning can still be marked
    "lean no hire" in 2026 rubrics.
    """,
    howToAce="""
    **A 45-minute script you rehearse until it is automatic**

    1. **0-5 min, clarify.** Restate the problem in your own words. Ask about input size, value ranges, duplicates, empty input, and what to return when there is no answer. Write one small example and its expected output in the editor.
    2. **5-12 min, approach.** Say the brute force and its complexity in one sentence. Then name the bottleneck ("we recompute the window sum each time") and the structure that removes it. Get a nod before coding: "Does that sound reasonable, or should I go straight for X?"
    3. **12-32 min, code.** Narrate *intent*, not keystrokes: "Now I'm expanding the frontier one level at a time." Write helper methods for the noisy parts (bounds checks, neighbour generation). Use real names.
    4. **32-40 min, test.** Dry-run your example line by line, tracking variables in a comment. Then run 2-3 edge cases out loud. When you find a bug, say what was wrong before you fix it.
    5. **40-45 min, wrap up.** State time and space complexity, then pre-empt the follow-up: "If the grid were huge and sparse, I'd store only the active cells."

    **Patterns that cover most SDE-2 problems in Indian product-company loops**

    Hashing and prefix sums, two pointers, sliding window, binary search on the answer, BFS/DFS on grids and graphs
    (multi-source BFS, topological sort), heaps and top-k, intervals, tree recursion (LCA, path sums, level order),
    1D/2D DP basics, union-find and tries. Depth on these beats a scattering of hard problems.

    **When you are stuck**

    Say so, and show your search: "I'm looking for a way to avoid re-scanning; I've ruled out sorting because we need
    original indices." Try a smaller input, a different data structure, or reversing the direction of the problem.
    Interviewers give hints to people who show their thinking.

    **Java habits interviewers notice**

    `ArrayDeque` instead of `Stack`, `Integer.compare` in comparators (never `a - b`, which can overflow), `equals`
    for boxed `Integer`, `getOrDefault` and `merge` for counting, and marking a cell as visited when you *enqueue*
    it, not when you dequeue it.

    **How to practise**

    Solve out loud, always, even alone. Record one session a week and listen for silences longer than 30 seconds. Do
    one mock with a friend every week from the second month on. Mocks are where explain-as-you-go becomes natural.
    """,
    walkthrough="""
    **Prompt (original, in the style of a common grid BFS question):** A data-centre floor is a grid. `S` cells are
    servers that already have a config update, `H` cells are healthy servers without it, and `X` cells are dead racks.
    Every minute the update spreads from each updated server to its up/down/left/right neighbours that are healthy.
    Return the minutes until every healthy server is updated, or -1 if some can never be reached.

    > **Candidate:** Let me confirm a few things. Does the update spread diagonally? Do dead racks block it? And if there are no healthy servers at the start, is the answer 0?
    >
    > **Interviewer:** Four directions only, dead racks block, and yes, 0.
    >
    > **Candidate:** How big can the grid be?
    >
    > **Interviewer:** Up to 1000 by 1000.

    **The approach, stated before coding.**

    > **Candidate:** Brute force would simulate minute by minute and rescan the whole grid each time. That's O((mn)^2) in the worst case, a snake-shaped path, which is far too slow for a million cells. The rescan is the waste. The update moves outward like a wave from *all* seeds at once, so this is a **multi-source BFS**: put every `S` in the queue at time 0 and process level by level. Each level is one minute. Every cell is enqueued at most once, so it's O(mn) time and O(mn) space for the queue. I'll count healthy servers first, so the end check is just "did the count reach zero?"
    >
    > **Interviewer:** Go ahead.

    ```java
    int minutesToSpread(char[][] g) {
        int rows = g.length, cols = g[0].length, healthy = 0;
        Deque<int[]> queue = new ArrayDeque<>();
        for (int r = 0; r < rows; r++)
            for (int c = 0; c < cols; c++) {
                if (g[r][c] == 'S') queue.offer(new int[]{r, c});
                else if (g[r][c] == 'H') healthy++;
            }
        int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        int minutes = 0;
        while (!queue.isEmpty() && healthy > 0) {
            for (int size = queue.size(); size > 0; size--) {      // one BFS level = one minute
                int[] cell = queue.poll();
                for (int[] d : dirs) {
                    int nr = cell[0] + d[0], nc = cell[1] + d[1];
                    if (nr < 0 || nc < 0 || nr >= rows || nc >= cols || g[nr][nc] != 'H') continue;
                    g[nr][nc] = 'S';                               // mark on enqueue, not on poll
                    healthy--;
                    queue.offer(new int[]{nr, nc});
                }
            }
            minutes++;
        }
        return healthy == 0 ? minutes : -1;
    }
    ```

    While coding, the candidate says two things that matter. First: "I'm marking the cell when I *enqueue* it.
    Otherwise two neighbours could both add it and I'd double-count." Second: "I'm mutating the input grid. If the
    caller needs it unchanged, I'd copy it or keep a `visited` array. Is mutation OK here?"

    **Testing out loud.** The candidate dry-runs a 3x3 grid with one seed in the corner and gets 4, as expected. Then
    the edge cases:

    - No `H` cells: the loop condition `healthy > 0` is false straight away, so it returns 0. Correct.
    - An `H` walled in by `X`: the queue empties while `healthy` is 1, so it returns -1. Correct.
    - No seeds but some `H`: the queue is empty from the start, so it returns -1. Correct.

    > **Candidate:** Notice the `healthy > 0` check in the while loop. Without it I'd count one extra minute after the last server is updated, because the final level still runs.

    **The follow-up.**

    > **Interviewer:** Now each server takes a different number of seconds to apply and forward the update. Same question.
    >
    > **Candidate:** Then levels no longer equal time, and plain BFS is wrong. The edges have weights, so it becomes Dijkstra from multiple sources: a priority queue keyed by arrival time, seeded with every `S` at 0. The answer is the largest finalised arrival time, or -1 if a healthy server is never reached. That's O(mn log(mn)).

    **Moments that earned points:** clarifying questions that changed the code (diagonals, the empty case). Brute
    force stated and rejected *with a reason*. The complexity said before coding. Two subtle correctness choices
    explained while typing. Edge cases tested without being asked. And a follow-up answered by naming exactly which
    assumption broke (level = minute) and which algorithm fixes it.
    """,
    commonFailures=[
        "Coding in silence for 15 minutes, then presenting the result",
        "Jumping into code without a worked example or any clarifying questions",
        "Reproducing a memorised solution but not being able to say why it is correct",
        "Never stating the brute force, so the interviewer can't credit the optimisation",
        "No dry run: the interviewer finds the off-by-one you would have caught",
        "Arguing with a hint, or ignoring it and carrying on down the wrong path",
        "Java slips: `Stack`, `==` on boxed Integers, `a - b` comparators, int overflow",
        "Polishing an optimal idea for 30 minutes instead of first finishing a working one",
    ],
    practice=[
        P("Rotting Oranges (multi-source BFS)", "/dsa/graphs/rotting-oranges"),
        P("Number of Islands", "/dsa/graphs/number-of-islands"),
        P("All Nodes Distance K in Binary Tree", "/dsa/trees/all-nodes-distance-k-in-binary-tree"),
        P("Capacity to Ship Packages Within D Days", "/dsa/binary-search/capacity-to-ship-packages-within-d-days"),
        P("Top K Frequent Words (heap + comparator)", "/dsa/heap/top-k-frequent-words"),
        P("Network Delay Time (Dijkstra follow-up)", "/dsa/advanced-graphs/network-delay-time"),
        P("Merge Intervals", "/dsa/intervals/merge-intervals"),
        P("Final Round Day 8: Google & Microsoft hard round", "/final-round/8"),
    ],
    sources=[SRC_TECHINT_2026, SRC_74, SRC_PREPFULLY, SRC_FLIPKART_2026, SRC_AMAZON_2025],
)

# ---------------------------------------------------------------------------
AI_ASSISTED = ROUND(
    id="ai-assisted-coding", order=3, title="AI-Assisted Coding", icon="🤖",
    summary="""
    A newer round where an AI assistant sits inside the editor next to a multi-file codebase you didn't write. You
    are scored on how you understand, direct and verify the work, not on typing speed.
    """,
    whoRunsIt=["Meta", "Google (2026 pilot)", "Canva", "AI-native startups", "Startups with AI-allowed take-homes"],
    frequency="Some companies",
    weight="Replaces one of the two coding rounds at Meta (~20-25% of that loop)",
    format="""
    - **Meta (since October 2025, up to E7):** about 60 minutes in a three-panel CoderPad: file explorer, editor, and an AI chat that can see the files but only answers in chat. You paste or type the code yourself. Several models are offered (GPT, Claude, Gemini, Llama variants). Java is supported. Three phases on one problem: **fix a bug → implement the core feature → optimise** for larger hidden test data.
    - **Google (2026 pilot, junior and mid-level, select US teams):** a *code comprehension* round with Gemini: read, debug and extend an existing codebase. Described internally as "human-led, AI-assisted".
    - **Canva:** an AI-assisted round replaced the CS-fundamentals screen for backend and frontend roles, with deliberately ambiguous, realistic problems that one prompt can't solve.
    - **Take-homes:** AI use is often expected, followed by a live walkthrough where you must explain and change your own code.
    - **India in 2026:** rare in Indian product-company loops so far. Expect it at global companies' India offices and at AI-first startups. Most Indian loops stay AI-off.
    """,
    whatTheyTest=[
        "Reading an unfamiliar multi-file codebase quickly before touching it",
        "Breaking the task into small, well-specified prompts instead of asking for the whole solution",
        "Verifying every AI output: running tests, checking edge cases and complexity",
        "Catching confident-but-wrong AI code (wrong algorithm, hidden O(n^2), broken invariants)",
        "Owning the result: explaining every line, including lines the AI wrote",
        "Picking the algorithm yourself when larger test data exposes a slow solution",
        "Narrating decisions while juggling the tool and the interviewer",
    ],
    rubric="""
    Meta reportedly scores the same four competencies as its classic coding round: problem solving, code quality,
    verification and communication. Google's pilot looks for prompt clarity, output validation and debugging. How
    those show up with an AI in the room:

    | Signal | Strong | Weak |
    |---|---|---|
    | Orientation | Reads README, models and tests before the first prompt | Prompts "fix the failing test" in minute one |
    | Decomposition | Decides the approach, delegates bounded pieces (a helper, boilerplate, test data) | Asks for the full solution and pastes it |
    | Prompt quality | Gives types, signatures, constraints, invariants, "don't change X" | Vague one-liners, then several rounds of re-prompting |
    | Verification | Runs tests after every change, adds an edge-case test, checks complexity | Trusts the output because it compiles |
    | Catching errors | Spots and explains the AI's mistake, fixes it by hand or with a sharper prompt | Doesn't notice until the hidden tests fail |
    | Ownership | Explains and simplifies generated code on request | "The AI wrote that part" |

    One internal summary quoted by Hello Interview: you *should* use AI, but you must show you understand the code.
    Candidates were marked down both for over-reliance and for never using the tool at all.
    """,
    howToAce="""
    **Step by step in the room**

    1. **Orient for 5 minutes without AI.** Open the README, the domain classes and the test file. Say what you see: "Three classes. `Allocator` is the entry point, and the tests use a builder for orders." This is where most candidates lose time later.
    2. **State your plan before the first prompt.** "I'll fix the failing test, then implement the allocation with a sweep plus a heap, then check against the big dataset."
    3. **Bug phase: form the hypothesis yourself.** Read the failing assertion and the code path. Use the AI to confirm or to explain an unfamiliar API, not to find the bug for you. Some candidates report the assistant being deliberately unhelpful in this phase.
    4. **Implementation phase: delegate bounded work with rich prompts.** A good prompt has the goal, the signature, the types, the constraints, the invariant and the limits:

    > "In `Allocator.java`, write `assign(List<Order>, List<Slot>)` returning `Map<Integer,Integer>` (orderId to slotId). Sort slots by time. Sweep them, pushing orders with `readyAt <= slot.time` into a min-heap by deadline. Discard heap entries whose deadline is before the slot time. Fill up to capacity. Don't modify `Order` or `Slot`. Target O((n+m) log n)."

    5. **Review the output like a code review.** Read every line before pasting. Check loop bounds, inclusive or exclusive comparisons, mutation of shared lists, and hidden linear calls inside loops (`removeIf`, `contains` on a list).
    6. **Run tests after every paste.** Then ask the AI for edge-case tests, read them, and add your own counterexample for the greedy choice.
    7. **Optimisation phase: look at the data first.** Read the size of the large test inputs, compute your complexity, and pick the algorithm yourself. Use the AI to type it.
    8. **Narrate throughout.** Before each prompt, say what you're asking for. After it, say what you'll check. Silence while chatting with the model reads as lost control.

    **Preparation on SwitchPrep**

    - Once a week, take an LLD or practical-coding problem, give yourself 45 minutes with an AI assistant, and follow the steps above. Then close the AI and explain every line out loud.
    - Keep solving DSA by hand. The optimisation phase still needs you to recognise BFS, heaps, tries or DP quickly.
    - Prepare your answer to "How do you use AI in daily work, and where do you still write code by hand?" It now comes up in behavioral rounds too.
    """,
    walkthrough="""
    **Setup (original example in the Meta/Google style):** a Java repo `slot-allocator` with `Order(id, readyAt,
    deadline)`, `Slot(id, time, capacity)`, an `Allocator` class and `AllocatorTest`. Delivery slots leave at a fixed
    time. An order can go on any slot whose time falls inside its window (both ends inclusive), and the goal is to
    assign as many orders as possible.

    **Phase 1: the failing test.**

    > **Candidate:** Before I prompt anything, I'll read the models and the test. `Order`'s Javadoc says the window is inclusive on both ends. The failing test is `orderReadyExactlyAtSlotTimeIsEligible`. In `Allocator.isEligible` I see `slot.time() > order.readyAt()`. That's a strict comparison, so an order ready exactly at slot time is rejected. It should be `>=`.
    >
    > **Interviewer:** You didn't use the AI for that.
    >
    > **Candidate:** Reading was faster than prompting. I'll change it, run the suite... green. While I was reading I also noticed `assign` sorts the caller's list in place. That's a side effect worth flagging, so I'll copy the list in phase 2.

    **Phase 2: implement `assign`.** The candidate first asks the AI for a quick version to see its shape:

    > **Prompt:** "Implement `assign` so each order goes into the first eligible slot with capacity left. Return orderId to slotId."
    >
    > **Candidate (reading the output):** This processes orders in input order and takes the first eligible slot. It compiles, but greedy-by-input-order isn't optimal. Counterexample: order A has window [0,10], order B has [0,1], slot 1 is at t=1 with capacity 1, slot 2 is at t=5 with capacity 1. If A grabs t=1, B gets nothing, so we assign 1. The optimum is 2. I'll write that as a test first.

    The new test fails against the AI's version, which proves the point. The candidate then chooses the algorithm:

    > **Candidate:** The classic fix is earliest deadline first. Sweep the slots in time order. Keep the orders that are already ready in a min-heap by deadline. Drop any whose deadline has passed, and give each slot's capacity to the most urgent orders. An exchange argument shows that's optimal for unit-size orders. I'll ask the AI to type it with a precise prompt.

    The prompt names the signature, the sweep, the heap ordering, "copy the inputs, don't sort them in place", and the
    target complexity. The output comes back, and the candidate reads it before pasting:

    ```java
    while (!heap.isEmpty() && cap > 0) { ... }
    heap.removeIf(o -> o.deadline() < slot.time());   // AI put this inside the slot loop
    ```

    > **Candidate:** Logic's right, but `removeIf` scans the whole heap for every slot. That's O(n*m) hidden inside an O(log n)-looking loop. Expired orders always have the smallest deadlines, so they sit at the top of the heap. I'll replace it with a lazy pop: `while (!heap.isEmpty() && heap.peek().deadline() < t) heap.poll();`. Each order is then popped at most once.

    All tests pass, including the counterexample.

    **Phase 3: the large test.** It has 200,000 orders and 50,000 slots.

    > **Candidate:** Sorting both lists is O(n log n + m log m), and each order enters and leaves the heap once, so O(n log n) total. That should be well under a second. Let me run it... 0.4 s, passing. One more edge case: a slot with capacity 0. The inner loop just skips it. Fine.

    **Moments that earned points**

    - Reading before prompting solved phase 1 in four minutes, and spotted a side effect for free.
    - The candidate didn't accept AI code because it compiled. They **broke it with a counterexample test**, which is the clearest verification signal there is.
    - The algorithm choice and its justification came from the candidate. The AI did the typing.
    - The hidden `removeIf` was caught *in review*, before the big test exposed it, and the fix was explained in terms of the heap's invariant.
    - Every prompt was announced and every output was checked out loud, so the interviewer never had to guess who was in control.
    """,
    commonFailures=[
        "Prompting \"solve this problem\" and pasting the whole answer",
        "Pasting code without reading it, then debugging the AI's mistakes under time pressure",
        "Skipping orientation and spending 25 minutes on the phase-1 bug",
        "Letting the model choose the algorithm, then failing the large hidden tests",
        "Going silent while chatting with the AI, so the interviewer loses the thread",
        "Not running tests after each change; stacking three unverified edits",
        "Being unable to explain or simplify a generated block when asked",
        "Refusing to use the AI at all, which wastes the round's main signal",
    ],
    practice=[
        P("AI-assisted engineering (senior subject)", "/core/ai-assisted-engineering"),
        P("Testing and code review habits", "/core/testing-code-review"),
        P("Prompt engineering techniques that work", "/ai/m07-llm-apis-prompting/m07-prompt-techniques"),
        P("Non-overlapping Intervals (greedy proof practice)", "/dsa/intervals/non-overlapping-intervals"),
        P("Task Scheduler (greedy + heap)", "/dsa/greedy/task-scheduler"),
        P("In-memory key-value store (multi-file practice repo idea)", "/system-design/lld-problems/in-memory-key-value-store"),
        P("Java traps AI assistants commonly fall into", "/traps?area=java"),
    ],
    sources=[SRC_HI_META, SRC_IIO_META, SRC_GOOGLE_AI, SRC_LEVELOP_GOOGLE, SRC_CANVA, SRC_TECHINT_2026],
)

# ---------------------------------------------------------------------------
PRACTICAL = ROUND(
    id="practical-coding", order=4, title="Practical Coding (changing requirements + tests)", icon="🛠️",
    summary="""
    Build a small, working component (rate limiter, TTL cache, job scheduler, webhook handler) in a real editor while
    the interviewer adds a requirement every 15-20 minutes. Tests are expected, and adapting cleanly to each change is
    the main signal.
    """,
    whoRunsIt=["Stripe", "Atlassian (code design)", "Meta", "OpenAI", "Anthropic", "Uber",
               "Companies using CodeSignal's Industry Coding format"],
    frequency="Some companies",
    weight="~15-20% where it replaces a DSA round; growing fastest of all formats",
    format="""
    - **Duration:** 60-90 minutes.
    - **Setup:** your own IDE, or CoderPad with a run button. Sometimes a starter repo with interfaces and a few tests. Internet docs are often allowed. AI is usually not (Stripe's integration round explicitly bans AI assistants).
    - **Shape:** a progressive spec. Level 1 is the basic API. Each later level adds a twist: time windows, a second limit, capacity eviction, retries, cancellation, concurrency. CodeSignal's version runs 4 levels in about 90 minutes, and few people finish all four.
    - **Atlassian's code-design round:** function signatures provided, the code must pass test cases, then a discussion of internals and of how you would improve usability and efficiency.
    - **Typical prompts:** per-user + global rate limiter; TTL cache with max capacity; task scheduler with pause/retry/cancel; idempotent webhook receiver; booking without double booking; a small rules or discount engine; an in-memory key-value store with transactions; a bank ledger with scheduled transfers.
    """,
    whatTheyTest=[
        "Turning a vague spec into a small, clear API with defined semantics",
        "Getting a correct first version running fast, then improving it",
        "Absorbing new requirements with small refactors instead of rewrites",
        "Writing focused JUnit tests as you go, including boundary cases",
        "Making time and randomness injectable so the code is testable",
        "Thread-safety and failure semantics when the spec asks for them",
        "Explaining trade-offs (accuracy vs memory, strictness vs simplicity)",
    ],
    rubric="""
    | Area | Strong hire | Hire | No hire |
    |---|---|---|---|
    | Progress | Reaches level 3-4; every finished level works | Reaches level 2-3, solid | Stuck on level 1, or later levels break earlier ones |
    | Design | Small interfaces, logic separated from I/O, injectable clock | Reasonable structure, some coupling | God class, or a framework built up front for imagined needs |
    | Change handling | Restates the new rule, finds the affected seam, refactors in minutes | Gets there with some patching | Rewrites from scratch or piles up `if` flags |
    | Tests | Tests from level 1, reruns after each change, covers boundaries | A few tests, mostly happy path | None, or "I'd add tests later" |
    | Communication | Names semantics and trade-offs before coding | Explains when asked | Silent, or can't justify choices |

    Interviewers repeat one line in practical rounds: correctness and readability beat cleverness at every stage. A
    boring level-3 solution with tests beats a brilliant, untested level-2 one.
    """,
    howToAce="""
    **The playbook**

    1. **Pin down semantics before code (3-5 min).** For a limiter: what does "100 per minute" mean, a fixed window or rolling? What does the caller get on rejection, a boolean or a retry-after? Per user, per key, global? Write the answers as comments at the top of the file. They become your test names.
    2. **Write the interface first.** `boolean allow(String userId)` or `Optional<V> get(K key)`. Keep it tiny. Every later level should fit behind it.
    3. **Inject time.** Pass a `LongSupplier nowMs` or a `java.time.Clock` into the constructor. Hard-coding `System.currentTimeMillis()` makes window, TTL and retry logic untestable, and interviewers notice.
    4. **Simplest correct version, then a test immediately.** Have a JUnit 5 skeleton in your fingers: `@Test`, `assertEquals`, `assertTrue`, `assertThrows`. One happy-path test and one boundary test per level.
    5. **When the requirement changes, follow a small loop.** Restate it ("so a user under their own limit can still be rejected by the global limit"). Name what breaks. Make the smallest refactor that creates a seam: extract a strategy, add a wrapper, split a method. Rerun all tests, add one new test.
    6. **Separate the clock, the storage and the policy.** Most level-3 and level-4 twists change exactly one of them.
    7. **Concurrency only when asked, but mention it early:** "Single-threaded for now. I'll make the per-key state atomic if we need concurrency." When it comes, use `ConcurrentHashMap.compute` or per-key locks, and say what's atomic and what isn't.
    8. **Narrate trade-offs in one sentence each:** "A sliding log is exact but O(limit) memory per user. A token bucket is O(1) and allows controlled bursts."
    9. **Manage the clock.** If a level takes more than 25 minutes, finish a simpler correct version, say what you'd improve, and move on.

    **Practise on SwitchPrep**

    Pick an LLD problem and write your own 4-level spec (for example: LRU cache, then TTL, then per-entry
    weights, then thread-safety). Do it in 75 minutes in IntelliJ with JUnit. Repeat weekly with a different problem
    from the list above.
    """,
    walkthrough="""
    **Prompt, level 1:** "Build a rate limiter: each user may make at most N requests per second."

    > **Candidate:** A few semantics questions. Should a burst of N at the very end of one second, plus N at the start of the next, be allowed? That's the fixed-window problem. And on rejection, do you just need a boolean?
    >
    > **Interviewer:** A boolean is fine. Don't worry about the boundary yet.
    >
    > **Candidate:** Then I'll start with a fixed window per user, but behind an interface so I can swap the algorithm. I'll inject the clock so the tests can control time.

    ```java
    interface RateLimiter { boolean allow(String userId); }

    final class FixedWindowLimiter implements RateLimiter {
        private record Window(long start, int count) {}
        private final Map<String, Window> windows = new HashMap<>();
        private final int limit; private final long windowMs; private final LongSupplier now;

        FixedWindowLimiter(int limit, long windowMs, LongSupplier now) { ... }

        public boolean allow(String user) {
            long t = now.getAsLong();
            Window w = windows.get(user);
            if (w == null || t - w.start() >= windowMs) w = new Window(t, 0);
            if (w.count() >= limit) return false;
            windows.put(user, new Window(w.start(), w.count() + 1));
            return true;
        }
    }
    ```

    Two tests follow straight away: five calls allowed and the sixth rejected, then allowed again after advancing a
    fake clock by one second. The fake clock is just `long[] t = {0}; LongSupplier now = () -> t[0];`.

    **Level 2:** "Customers are abusing the boundary: 2N requests in 10 ms across two windows. Fix it."

    > **Candidate:** That's the known fixed-window weakness. Two options. A sliding log of timestamps is exact but stores up to N timestamps per user. A token bucket is O(1) per user and smooths bursts: capacity N, refilling N tokens per second. I'll go with the token bucket and keep the same interface, so the level 1 tests should still pass with the new class.

    ```java
    final class TokenBucket {
        private final double capacity, refillPerMs;
        private double tokens; private long last;
        TokenBucket(double capacity, double refillPerMs, long now) {
            this.capacity = capacity; this.refillPerMs = refillPerMs; this.tokens = capacity; this.last = now;
        }
        void refill(long now) { tokens = Math.min(capacity, tokens + (now - last) * refillPerMs); last = now; }
        boolean hasToken() { return tokens >= 1; }
        void take() { tokens -= 1; }
    }
    ```

    The new test is the exact abuse case: N calls at t=999 ms, then N at t=1001 ms. The second batch is now mostly
    rejected. The level 1 tests still pass.

    **Level 3:** "Add a global limit of G requests per second across all users."

    > **Candidate:** Restating: a request needs a token from *both* the user's bucket and the global bucket. The subtle part is ordering. If I take the user's token and the global check then fails, the user has been charged for a rejected request. So I check both first and take from both only if both have tokens.

    ```java
    public boolean allow(String user) {
        long t = now.getAsLong();
        TokenBucket mine = buckets.computeIfAbsent(user, u -> new TokenBucket(perUser, perUserRate, t));
        mine.refill(t); global.refill(t);
        if (!mine.hasToken() || !global.hasToken()) return false;
        mine.take(); global.take();
        return true;
    }
    ```

    The test: two users each under their own limit, but together over G. The last request is rejected, and the
    rejected user's bucket still has its token.

    **Level 4:** "This runs on a 200-thread server."

    > **Candidate:** `computeIfAbsent` on a `ConcurrentHashMap` makes bucket creation safe, but check-then-take across two buckets isn't atomic. The simplest correct fix is to synchronise on the global bucket, which serialises every request through one lock. That's fine at a few thousand requests per second. If it becomes the bottleneck, I'd shard the global budget into per-core buckets, accepting a slightly fuzzy global limit. Across several server instances this whole design moves to Redis with a Lua script, but that's a system-design conversation.

    Their test for level 4: 50 threads released together by a `CountDownLatch`, each calling `allow` 100 times. They
    assert that the total allowed never exceeds the global capacity plus the refill for the elapsed time.

    **Moments that earned points:** semantics questions before code. An injectable clock from the first minute. The
    same interface surviving three requirement changes. The token-ordering bug named *before* it was written. Tests
    added at every level. And a concurrency answer that gave the simple correct option first, then its cost, then the
    next step.
    """,
    commonFailures=[
        "Building a framework of interfaces and factories before anything runs",
        "No tests, or tests only in the last five minutes",
        "Hard-coded System.currentTimeMillis(), so time-based behaviour can't be tested",
        "Rewriting from scratch at each new level instead of extending a seam",
        "Ignoring semantics: inclusive vs exclusive boundaries, what happens on rejection",
        "Not reading the provided starter code and tests before writing new code",
        "Mixing console I/O and parsing into the core logic",
    ],
    practice=[
        P("Rate limiter (LLD)", "/system-design/lld-problems/rate-limiter-lld"),
        P("LRU cache (LLD)", "/system-design/lld-problems/lru-cache-lld"),
        P("LRU Cache (DSA implementation)", "/dsa/linked-list/lru-cache"),
        P("In-memory key-value store", "/system-design/lld-problems/in-memory-key-value-store"),
        P("Testing Spring Boot apps: JUnit 5, Mockito", "/core/spring-boot?chapter=10"),
        P("Testing and code review (senior subject)", "/core/testing-code-review"),
        P("Idempotency and exactly-once (webhook handler prompts)", "/system-design/senior/idempotency-exactly-once"),
        P("Rate limiter (distributed design follow-up)", "/system-design/case-studies/rate-limiter-design"),
    ],
    sources=[SRC_STRIPE, SRC_74, SRC_ATLASSIAN, SRC_ICF, SRC_PREPFULLY],
)

ROUNDS_P1 = [ONLINE_ASSESSMENT, DSA_LIVE, AI_ASSISTED, PRACTICAL]
