from ai2_common import Q, R, L, M

lessons = [
L("m14-design-llm-chatbot", "AI System Design: A Framework, Plus Designing a Support Chatbot", 55, r"""
## How AI system design interviews differ

Classic system design (you've practised it: load balancers, caches, sharding) still applies. AI system design adds new dimensions interviewers probe:
- **Model choice and routing** (quality vs cost vs latency).
- **Context engineering**: what goes into the prompt (retrieval, memory, tools).
- **Evaluation**: how you know it works, before and after launch.
- **Safety/guardrails**: hallucination, prompt injection, PII, harmful content.
- **Cost modelling**: tokens x requests x price.
- **Non-determinism and failure handling**: provider outages, bad outputs.

### A 7-step framework (45-60 minute interview)

1. **Clarify requirements** (5 min): users, use cases, scale (DAU, requests/day, peak QPS), latency targets, languages, data sources, compliance, what "good" means. Ask: "Is it OK to say I don't know? Can it take actions?"
2. **Define success metrics**: offline (eval pass rate, faithfulness, task accuracy) and online (resolution rate, escalation rate, CSAT, cost per conversation, p95 latency).
3. **High-level architecture**: draw the request path and offline pipelines.
4. **Deep dive on the AI core**: prompt/context design, retrieval, tools, model choice, memory.
5. **Evaluation and iteration plan**: eval sets, LLM judges, A/B testing, feedback loop.
6. **Scale, cost, latency, reliability**: estimates, caching, routing, fallbacks.
7. **Safety, privacy, risks** and trade-offs; what you'd build in v1 vs later.

Say trade-offs out loud; there's rarely one right answer.

### Worked example: customer-support chatbot for an e-commerce company

**Requirements (assumed after clarifying)**: 5M monthly users, 200k conversations/day, average 6 turns; English + Hindi; answers from policy/FAQ docs (about 2k pages) and order data; can create return requests; escalate to human agents; p95 time-to-first-token under 2 s; must not leak other customers' data.

**Metrics**: automated resolution rate (target 60%+), escalation rate, CSAT/thumbs, faithfulness on eval set (95%+), policy accuracy (99% on critical cases), cost per conversation, p95 TTFT.

**Architecture**

```
Mobile/Web -> API Gateway (auth, rate limit) -> Chat Orchestrator service (stateless, autoscaled)
   |-- Guardrails: input classifier (abuse, injection, PII masking), output checks
   |-- Router (small model): intent -> FAQ/policy | order status | return request | chit-chat | human
   |-- RAG: hybrid retrieval (pgvector + BM25) over policy docs -> reranker -> context
   |-- Tools: order service, returns service (with confirmation), ticketing (escalation)
   |-- LLM gateway: primary model, fallback model, prompt caching, budgets
   |-- Memory: conversation store (Redis hot + Postgres durable), summarisation after N turns
-> Streaming response (SSE) to client
Offline: doc ingestion pipeline, eval pipeline, analytics/traces, feedback review
```

**Deep dive choices**
- **Router first** with a small model: many messages ("where is my order?") need a tool call, not RAG. Cheap and fast.
- **RAG**: structure-aware chunks with section headers, metadata (policy version, region, language), hybrid search + rerank, top 5 into context with ids for citations.
- **Tools** with `ToolContext`-style trusted user id; return requests require explicit user confirmation in the UI.
- **Prompt**: stable system prompt + tool definitions + policy summary first (cached), then retrieved context, then conversation, then user message.
- **Multilingual**: multilingual embedding model; answer in the user's language; eval slices for Hindi and Hinglish.
- **Escalation**: on low confidence, repeated failure, user frustration (sentiment), or sensitive topics, hand off to a human with a conversation summary.

**Capacity and cost estimate**

```python
convs_per_day = 200_000
turns = 6
calls_per_turn = 1.4               # router + main call sometimes, tools add follow-ups
requests = convs_per_day * turns * calls_per_turn
in_tok, out_tok = 4_000, 250       # per main call, after caching/trimming
peak_qps = requests / 86_400 * 3   # assume 3x peak factor
print(f"{requests/1e6:.2f}M LLM calls/day, peak ~{peak_qps:.0f} QPS")
# cost = requests * (uncached_in*p_in + cached_in*p_cached + out*p_out) -> plug current prices
```

Talk through levers: prompt caching for the static prefix, small-model routing for simple intents, shorter outputs, semantic cache for generic FAQs (not personalised answers).

**Evaluation**: 300-case eval set from historical tickets (sliced by intent and language), binary judges for policy accuracy and faithfulness validated against agent labels, red-team set; shadow mode then 5% canary; weekly error analysis from thumbs-down and escalations.

**Reliability**: timeouts and fallback model via gateway; if LLMs are down, degrade to FAQ search + "contact agent"; circuit breakers on tools.

**Safety/privacy**: PII masking in logs, data residency, per-user authorisation in tools, injection defences on any user-provided content (e.g. order notes), output escaping.

**v1 vs later**: v1 = FAQ RAG + order status + escalation. v2 = returns with confirmation, proactive notifications. v3 = voice, agent-assist for human agents.

### Key takeaways
- Use a framework: requirements -> metrics -> architecture -> AI deep dive -> evals -> scale/cost -> safety.
- Show model routing, context design, guardrails, evaluation and cost reasoning, not just boxes.
- Quantify: requests/day, tokens, peak QPS, cost levers.
- Always discuss failure modes, fallbacks and a phased roadmap.
""", r"""
1. Practise the chatbot design out loud in 40 minutes with a timer, drawing the diagram on paper or excalidraw. Record yourself.
2. Redo the cost estimate with current real prices for two models and compute monthly cost with and without prompt caching and routing.
3. Write the top 10 eval cases you'd include for policy accuracy, including 3 tricky edge cases.
4. List 5 failure scenarios (provider outage, injection in order notes, wrong policy version, Hindi misunderstanding, tool timeout) and your mitigation for each.
""", [
Q("Which is usually the FIRST step in an AI system design interview?", ["Choose a vector database", "Clarify requirements, scale, latency, data sources and success criteria", "Draw Kubernetes pods", "Pick the largest model"], 1, "Requirements and success metrics drive every later choice."),
Q("Why put a small-model router before RAG in a support chatbot?", ["Routers are required by APIs", "Many messages need tools or simple answers, so routing saves cost and latency and picks the right path", "To avoid using embeddings", "It improves the reranker"], 1, "Routing sends each intent down the cheapest correct path."),
Q("A good online success metric for a support bot is:", ["Number of tokens generated", "Automated resolution rate with escalation rate and CSAT", "Embedding dimensions", "Model parameter count"], 1, "Business outcomes plus quality and cost define success."),
], [
R("Chip Huyen - Building a generative AI platform", "https://huyenchip.com/2024/07/25/genai-platform.html", "article"),
R("Chip Huyen - AI Engineering (book)", "https://www.oreilly.com/library/view/ai-engineering/9781098166298/", "book"),
R("ByteByteGo - System Design (YouTube)", "https://www.youtube.com/@ByteByteGo", "video"),
R("Eugene Yan - Patterns for building LLM-based systems", "https://eugeneyan.com/writing/llm-patterns/", "article"),
]),

L("m14-design-rag-at-scale", "Designing an Enterprise RAG / Knowledge Search System at Scale", 50, r"""
## The prompt

"Design an internal AI assistant that answers employee questions over all company documents (Confluence, Google Drive/SharePoint, Jira, Slack), for a 50,000-employee company." This (or a variation like "ChatGPT for our docs") is one of the most common AI system design questions.

### Clarify

- Corpus: about 20M documents, 200M chunks; 1% change per day; formats PDF/DOCX/HTML/slides.
- Users: 50k employees, 30k DAU, about 150k queries/day, peak around 10 QPS.
- Latency: first token under 2-3 s.
- **Permissions**: users must only see what they can access in the source system. (Critical: say this early.)
- Freshness: changes visible within 15 minutes.
- Citations required; "don't know" acceptable.

### Architecture

```
Connectors (Confluence, Drive, Jira, Slack APIs, webhooks + periodic sync)
   -> Ingestion queue (Kafka) -> Workers: fetch -> parse (PDF/OCR/tables) -> clean -> chunk + contextual headers
      -> embed (batch, GPU or API) -> upsert vector index + keyword index + metadata/ACL store
   -> ACL sync service (group memberships, doc permissions)

Query path:
User -> SSO auth -> Query service
   -> condense (chat) + query understanding (filters: team, date, source)
   -> resolve user's groups (cached)
   -> hybrid retrieval with ACL filter (vector + BM25), top 100
   -> rerank (cross-encoder on GPU), top 8, dedupe/merge
   -> LLM generation with citations (streaming), verify citations
   -> traces, feedback
```

### Key deep dives

**1. Permissions (where candidates fail)**
- Store ACLs with each chunk: allowed users/groups, inherited from the document.
- At query time, filter by the user's groups *inside* the vector/keyword search (pre-filtering or filtered HNSW), not after the LLM sees text.
- Group membership can be huge (users in hundreds of groups): cache memberships; some systems use per-document ACL ids and bitmap filters.
- Permission changes must propagate fast; deletions must remove chunks quickly (also a legal requirement).
- Alternative: query-time permission check against the source system for top candidates (accurate but slower).

**2. Index sizing**

```python
chunks = 200e6
dim = 1024
bytes_per = 4                                   # float32
raw_gb = chunks * dim * bytes_per / 1e9
print(f"raw vectors: {raw_gb:,.0f} GB")         # ~819 GB -> too big for one node's RAM
for name, factor in [("int8", 4), ("binary + rescoring", 32)]:
    print(name, f"{raw_gb/factor:,.0f} GB")
# HNSW graph adds memory (roughly M*2 links * 4-8 bytes per vector)
```

Options: shard the index across nodes (by tenant/department or hash), quantise (int8/binary with rescoring), reduce dimensions (Matryoshka), or use disk-based ANN indexes. Discuss recall vs memory trade-offs.

**3. Ingestion at scale**
- Incremental: webhooks and change feeds; content hashes to skip unchanged documents.
- Embedding throughput: 2M changed chunks/day is fine with batched API calls or a few GPUs; initial backfill of 200M chunks is a big batch job (estimate time and cost, use batch APIs or self-hosted embedding models).
- Parsing quality: tables, slides and scanned PDFs need specialised parsers/OCR; measure with retrieval evals per source type.
- Re-embedding when changing models: build a new index in parallel, switch traffic (blue-green).

**4. Retrieval quality**
- Hybrid search (acronyms, project codenames, ticket ids are common in enterprises).
- Metadata boosts: recency, source authority (official policy pages over Slack chatter), user's own team.
- Reranker for precision; query rewriting for conversational follow-ups.
- For "summarise everything about project X" questions: agentic retrieval or pre-computed summaries per project/space.

**5. Generation**
- Mid-tier model by default; route complex multi-document synthesis to a stronger model.
- Citations with links and verification; "not found" with nearest documents shown.
- Long context: send more chunks when needed, but cap tokens for cost.

**6. Evaluation**
- Per-source retrieval eval sets (Confluence, Slack, PDFs), plus permission-leak tests (must be 0 leaks).
- Faithfulness and answer-quality judges, validated with human labels.
- Online: click-through on citations, thumbs, query reformulation rate, "no answer" rate.

**7. Cost and latency budget**

| Step | p95 budget |
|------|-----------|
| Auth + group lookup (cached) | 30 ms |
| Query rewrite (small model) | 300 ms |
| Hybrid retrieval | 80 ms |
| Rerank 100 candidates (GPU) | 150 ms |
| LLM TTFT | 1,000 ms |
| **Total to first token** | about 1.6 s |

Parallelise rewrite with group lookup; skip rewrite for first-turn queries; cache frequent queries' retrieval results (careful with ACLs: cache key must include the permission set).

### Trade-offs to articulate
- Managed vector DB vs pgvector/OpenSearch you operate.
- Pre-filter vs post-filter for ACLs (correctness vs latency).
- Chunk size and contextual retrieval cost (LLM calls at ingestion) vs retrieval quality.
- API embeddings (simple) vs self-hosted (cheaper at scale, data stays in house).

### Key takeaways
- Lead with permissions, freshness and evaluation; they're what make enterprise RAG hard.
- Size the index (vectors x dims x bytes) and discuss sharding/quantisation.
- Design incremental ingestion with queues, hashing and blue-green re-embedding.
- Give a latency budget per stage and cost levers.
""", r"""
1. Present this design in 45 minutes with a diagram, including a latency budget table and an index-size estimate.
2. Write a 1-page deep dive on ACL-aware retrieval: data model, sync, query-time filtering, caching, deletion SLAs.
3. Estimate the one-time backfill cost and time for embedding 200M chunks of 300 tokens using a current embedding API price and a batch discount, vs self-hosted embedding on GPUs (state assumptions).
4. List 8 eval slices you'd track and why.
""", [
Q("What is the most critical requirement to raise early in enterprise document RAG?", ["Using the largest model", "Respecting source-system permissions so users only retrieve what they can access", "Choosing a font for citations", "Avoiding streaming"], 1, "Permission leaks are the most serious failure in enterprise RAG."),
Q("200M chunks x 1024 dims x float32 is roughly:", ["8 GB", "80 GB", "800 GB", "8 TB"], 2, "200e6 x 1024 x 4 bytes is about 819 GB, requiring sharding or quantisation."),
Q("Why must a retrieval cache key include the user's permission set?", ["For speed", "Otherwise cached results retrieved for one user could leak documents to another user without access", "Caches require it", "To reduce memory"], 1, "Caching must not bypass ACL filtering."),
], [
R("Glean - How enterprise AI search handles permissions (engineering blog)", "https://www.glean.com/blog", "article"),
R("Pinecone Learn - RAG series", "https://www.pinecone.io/learn/series/rag/", "article"),
R("Anthropic - Contextual Retrieval", "https://www.anthropic.com/news/contextual-retrieval", "article"),
R("Qdrant - Multitenancy guide", "https://qdrant.tech/documentation/guides/multiple-partitions/", "docs"),
]),

L("m14-ai-design-questions", "More AI System Design Questions with Model Answers", 50, r"""
## How to use this lesson

Below are frequently asked AI system design prompts with **condensed model answers**: the key points an interviewer listens for. Practise expanding each into a 30-45 minute discussion using the framework from lesson 1.

### 1. Design an AI coding assistant (like an IDE copilot)

- **Features**: inline completion (latency-critical, under ~300 ms), chat about code, agentic edits.
- **Context engineering**: current file, cursor position, open tabs, related files via code search (embeddings + symbol graph/LSP), repo conventions. Fill-in-the-middle prompts for completion.
- **Models**: small fast model for completions (possibly self-hosted, speculative decoding), strong model for chat/agent tasks.
- **Agent mode**: tools for read/search/edit/run tests in a sandbox; diffs shown to the user for approval.
- **Metrics**: acceptance rate of suggestions, retained code after N minutes, latency, task success on benchmark repos.
- **Privacy**: no training on customer code without consent, secret filtering, enterprise isolation.

### 2. Design a content moderation system using LLMs

- **Tiered pipeline**: cheap classifiers/hash matching for obvious cases -> small LLM for nuanced cases -> large LLM or human review for borderline/high-impact.
- **Policy as prompt**: detailed policy with examples; structured output (category, severity, rationale).
- **Throughput**: millions/day -> batching, async queues, mostly small models; LLMs only for the uncertain slice.
- **Evaluation**: precision/recall per category on labelled data, human appeal outcomes; adversarial users evolve, so monitor drift.
- **Latency**: pre-publish blocking for high-risk surfaces vs post-publish review for others.

### 3. Design a document extraction pipeline (invoices, KYC forms)

- OCR/vision model -> structured output with schemas -> validation (totals add up, GSTIN format, dates) -> confidence scoring -> human review queue for low confidence.
- Fine-tuned small model or vision LLM; compare on a labelled set; cost per document.
- Idempotent processing, audit trail, PII encryption, retention policies.
- Metrics: field-level accuracy, straight-through processing rate, reviewer time.

### 4. Design an LLM-powered semantic product search / recommendations

- Query understanding with an LLM (extract filters: "red cotton kurta under 1000" -> category, colour, material, price).
- Hybrid retrieval over product embeddings + BM25 + structured filters; learning-to-rank with behavioural signals; LLM reranking only for top results if latency allows.
- Generate explanations or comparisons with an LLM, cached per product pair.
- Metrics: CTR, conversion, zero-result rate, latency (search must be fast; keep the LLM off the critical path or use small models).

### 5. Design a multi-tenant agent platform (customers build their own agents)

- Tenant isolation: per-tenant data stores/namespaces, secrets vault, quotas and billing by tokens.
- Tool/MCP registry with permission scopes; human-approval policies per tool risk level.
- Execution: durable workflows (state checkpointing), sandboxes for code, step/time/cost limits.
- Observability per tenant: traces, cost dashboards; evaluation tooling for customers.
- Security: prompt injection via tool results, cross-tenant leakage tests, rate limiting.

### 6. Design a meeting summariser

- Speech-to-text (with diarisation) -> chunk transcript -> map-reduce summarisation (summaries per chunk, then combine) or long-context model -> structured output: decisions, action items with owners/dates.
- Integration: calendar, task tools via APIs/MCP; human review before sending.
- Evaluate with rubric judges (action item recall/precision vs human notes).

### Common follow-up questions and crisp answers

- **"How do you reduce hallucinations?"** Ground with retrieval, require citations and verify them, allow "don't know", lower temperature, post-check claims, evaluate faithfulness.
- **"How do you choose a model?"** Build an eval set; test several tiers; pick the cheapest that meets quality and latency; route per task; keep the provider abstracted.
- **"How would you handle a provider outage?"** Gateway with timeouts, retries, fallback model evaluated in advance, circuit breaker, graceful degradation.
- **"How do you know your change improved things?"** Offline evals with case-level diffs, then A/B test on online metrics.
- **"RAG or fine-tuning?"** RAG for knowledge and freshness; fine-tuning for behaviour/format and cost at scale; often both.
- **"How do you control cost?"** Routing, prompt caching, shorter prompts/outputs, caching, batch APIs, budgets.

### A reusable estimation helper

```python
def llm_capacity(daily_requests, in_tok, out_tok, peak_factor=3, tokens_per_sec_per_stream=60):
    peak_qps = daily_requests / 86_400 * peak_factor
    gen_seconds = out_tok / tokens_per_sec_per_stream
    concurrent_streams = peak_qps * gen_seconds            # Little's law: L = lambda * W
    daily_tokens = daily_requests * (in_tok + out_tok)
    return {"peak_qps": round(peak_qps, 1), "concurrent_streams": round(concurrent_streams),
            "daily_tokens_M": round(daily_tokens / 1e6, 1)}

print(llm_capacity(1_000_000, 3000, 300))
```

Using **Little's law** to estimate concurrent streams (and hence GPU or rate-limit needs) is a strong signal in interviews.

### Key takeaways
- Each design has a characteristic core: context engineering (coding), tiered pipelines (moderation), validation + human review (extraction), latency-critical retrieval (search), isolation + limits (platforms).
- Prepare crisp answers to recurring follow-ups: hallucinations, model choice, outages, measuring improvement, RAG vs fine-tuning, cost.
- Quantify with simple estimates and Little's law.
""", r"""
1. Pick three of the six designs. For each, write a one-page design (diagram + bullets) in 30 minutes.
2. Use `llm_capacity` to estimate peak QPS, concurrent streams and daily tokens for each design with assumed numbers; justify the numbers.
3. Practise answering the six follow-up questions out loud in under 90 seconds each.
4. Do a mock interview with a friend (or an LLM acting as interviewer with a strict rubric) on one design.
""", [
Q("Why use a tiered pipeline for LLM content moderation at scale?", ["LLMs can't classify", "Cheap classifiers handle obvious cases; expensive LLMs/humans handle only the uncertain slice, controlling cost and latency", "Tiers improve embeddings", "Regulation requires three tiers"], 1, "Escalating only hard cases balances cost and accuracy."),
Q("Little's law estimates concurrent streams as:", ["QPS / latency", "Arrival rate x time each request spends in the system", "Tokens x price", "Users x sessions"], 1, "L = lambda x W gives in-flight requests."),
Q("For latency-critical inline code completion, a good choice is:", ["The largest reasoning model with high effort", "A small fast model with tight context and possibly speculative decoding", "Batch API", "No model at all"], 1, "Completions need sub-second latency."),
], [
R("Chip Huyen - Designing Machine Learning Systems (book)", "https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/", "book"),
R("Evidently AI - ML system design case studies database", "https://www.evidentlyai.com/ml-system-design", "article"),
R("GitHub Blog - How GitHub Copilot is getting better at understanding your code", "https://github.blog/ai-and-ml/github-copilot/how-github-copilot-is-getting-better-at-understanding-your-code/", "article"),
]),

L("m14-portfolio-projects", "Portfolio Projects That Get AI Engineer Interviews", 35, r"""
## What hiring managers look for

A portfolio for an AI engineer role should prove you can **ship reliable AI features**, not just call an API. Recruiters skim; engineers dig. Each project should show:

1. **A real problem** with real (or realistic) data, not "chat with a PDF" with no twist.
2. **Engineering depth**: retrieval quality work, tools, streaming, auth, persistence, deployment.
3. **Evaluation**: an eval set and a results table. This is the single biggest differentiator; most candidates have none.
4. **Trade-off thinking**: model comparison, cost per request, latency, what you tried that didn't work.
5. **Clean repo**: README with diagram, demo GIF/video, setup in a few commands, tests, CI.

### Recommended project set for you (Java + AI profile)

You already have projects from this course. Polish 3 of them into flagship quality:

**Project A: Spring AI full-stack assistant (module 13)**. Your differentiator. Spring Boot + Angular + PgVector + tools + MCP + evals. Shows you can add AI to the stack enterprises actually run.

**Project B: Evaluated RAG system (module 9 + 12)**. Python, hybrid retrieval, reranking, citations, permission filtering, a results table comparing configurations, tracing and a cost analysis.

**Project C: Agent with MCP (module 10)** or **fine-tuned small model vs API (module 11)**. Pick based on target roles: agents for product companies building AI features; fine-tuning for ML-platform-leaning roles.

Optional extras that stand out:
- An **open-source contribution** to Spring AI, LangChain4j, LangChain, LlamaIndex or an MCP server (docs fixes and examples count).
- A **published MCP server** for a useful service (e.g. Indian railway PNR status, a public API) with good docs.
- A **blog post** per project: "What I learned evaluating 4 chunking strategies on Spring docs" travels far on LinkedIn.

### Domain ideas with an Indian context (memorable, realistic)

- GST/invoice extraction with validation (GSTIN format, tax totals) and a human-review queue.
- Government scheme eligibility assistant (RAG over scheme PDFs, Hindi + English, citations).
- Indian legal/RTI document Q&A with strict citation verification.
- Hinglish customer-support classifier: fine-tuned small model vs API cost comparison.
- Resume-to-job matcher with structured extraction and explainable scoring.

### README template

```markdown
# AskDocs - Permission-aware RAG over engineering docs

![demo](docs/demo.gif)

## Problem
## Architecture        (diagram + 5 bullet explanation)
## Results             (eval table: config | recall@5 | faithfulness | p95 latency | cost/1k)
## Key decisions & trade-offs
## What didn't work
## Run it              (docker compose up; .env.example)
## Tests & evals       (how to run; CI badge)
## Next steps
```

### Generate the results table automatically

```python
import json, pandas as pd
rows = [json.load(open(f"evals/summary_{name}.json")) for name in ["baseline", "hybrid", "hybrid_rerank"]]
df = pd.DataFrame(rows)[["config", "recall_at_5", "faithfulness", "p95_latency_s", "cost_per_1k_usd"]]
print(df.to_markdown(index=False))          # paste into README
```

### Presenting projects in interviews

Prepare a 2-minute story per project (STAR-like):
- **Context**: what problem, for whom.
- **Approach**: architecture in one sentence, then the interesting part.
- **Evidence**: "Hybrid + rerank raised recall@5 from 0.71 to 0.89; faithfulness 96%; cost INR 0.4 per query."
- **Trade-off/failure**: "Semantic caching caused wrong answers for order-specific questions, so I limited it to generic FAQs."
- **What next**: shows product thinking.

Be ready for deep follow-ups: "Why that chunk size?", "How did you validate your judge?", "What happens if the model provider is down?", "How would this scale to 100x users?"

### Common mistakes

- Ten shallow tutorial clones instead of three deep projects.
- No evals, no numbers.
- Hard-coded API keys in the repo (instant red flag; also a security incident).
- No deployment or demo; reviewers won't run your code.
- Over-engineering with multi-agent frameworks where a single call would do (interviewers notice).

### Key takeaways
- Three deep, evaluated, deployed projects beat ten shallow ones.
- Lead with your Java + Spring AI full-stack project as the differentiator.
- READMEs need diagram, demo, results table, trade-offs and easy setup.
- Practise a 2-minute story with numbers for each project.
""", r"""
1. Choose your 3 flagship projects and write a one-paragraph pitch for each (problem, approach, evidence).
2. Rewrite each README using the template, including a results table generated from your eval scripts and a demo GIF.
3. Deploy at least one project publicly (Render, Railway, Fly.io, a small VM or Hugging Face Spaces) with spending limits on API keys.
4. Write one blog post (LinkedIn or a personal blog) about a measured finding from a project.
""", [
Q("What most differentiates an AI engineering portfolio project?", ["Using the newest framework", "An evaluation set with a results table and documented trade-offs", "Many pages of code", "A dark-mode UI"], 1, "Evidence of measured quality shows engineering maturity."),
Q("Which is a red flag in a portfolio repo?", ["A docker-compose file", "API keys committed to the repository", "A CI badge", "An architecture diagram"], 1, "Committed secrets signal poor security practice."),
Q("In a 2-minute project story, what should you include?", ["Only the tech stack list", "Context, approach, measurable evidence, a trade-off or failure, and next steps", "Your full code walkthrough", "Model parameter counts"], 1, "A structured, evidence-based story shows impact and judgement."),
], [
R("Eugene Yan - How to write a good README / technical writing", "https://eugeneyan.com/writing/writing-docs-why-what-how/", "article"),
R("Hugging Face Spaces (free demo hosting)", "https://huggingface.co/docs/hub/spaces-overview", "docs"),
R("Spring AI GitHub - contributing", "https://github.com/spring-projects/spring-ai", "docs"),
R("MCP servers repository (examples to learn from)", "https://github.com/modelcontextprotocol/servers", "docs"),
]),

L("m14-backend-to-ai-transition", "From Backend Developer to AI Engineer: Your Transition Plan", 35, r"""
## The AI engineer role in 2026

"AI engineer" today mostly means a **software engineer who builds products on top of foundation models**: LLM APIs and open models, RAG, agents, evals, LLMOps. It's distinct from:
- **ML engineer / data scientist**: training and deploying custom models, feature pipelines, classical ML.
- **Research scientist**: new model architectures and training methods.

Chip Huyen's *AI Engineering* frames it as the shift from "train a model" to "adapt and evaluate foundation models", which makes **software engineers well-suited** for it. Your backend skills are not a detour; they're the foundation.

### Your unfair advantages as a Spring Boot developer

| You already know | It maps to |
|------------------|-----------|
| REST APIs, timeouts, retries | LLM API integration, resilience |
| SQL/MySQL, indexing | pgvector, hybrid search, metadata filters |
| Spring Security, JWT | Permission-aware RAG, tool authorisation, MCP auth |
| Caching (Redis), async, queues | Prompt/response caching, ingestion pipelines |
| Testing (JUnit, mocks) | Evals, test-driven prompt changes |
| Logging, Actuator, tracing | LLM observability |
| Angular | Streaming chat UIs, human-in-the-loop UIs |

Many "AI engineer" job posts at product companies ask for exactly this mix: strong backend + LLM integration + evaluation.

### Skill checklist (what interviewers test)

**Must have**
- Python fluency (async, typing, Pydantic, FastAPI) + one framework (LangChain/LangGraph or LlamaIndex) and plain SDK usage.
- LLM APIs: tokens, sampling, structured output, streaming, tool calling.
- RAG end to end with evaluation.
- Agents basics, MCP, guardrails.
- Evals: building datasets, LLM-as-judge validation, error analysis.
- Production: tracing, cost/latency optimisation, prompt injection defences, deployment.
- System design for AI applications.
- DSA + classic system design (still asked at product companies).

**Strong plus**
- Spring AI / LangChain4j (your differentiator for Java-heavy companies: banks, fintech, e-commerce, SaaS).
- Fine-tuning with LoRA, serving open models (vLLM/Ollama).
- ML fundamentals: you covered these in modules 3-6; be ready to explain attention, embeddings, overfitting, evaluation metrics.

### Positioning strategies

1. **Internal transition**: volunteer to build an AI feature at your current company (internal docs bot, ticket triage, test generation). Real production experience is the strongest signal. Even a pilot with measured results counts.
2. **"Java + AI" backend roles**: target roles titled Backend Engineer (AI/LLM), Software Engineer - GenAI, AI Platform Engineer at product companies. Easier entry than pure "AI Engineer" titles.
3. **Pure AI engineer roles** at AI-first startups: need strong Python portfolio and evals depth.

### Resume rewrite

- Title line: "Backend Engineer (Java, Spring Boot) | LLM Applications, RAG, Spring AI".
- Bullets with numbers: "Built a permission-aware RAG assistant over 5k docs (Spring AI, PgVector); hybrid retrieval + reranking improved recall@5 from 0.71 to 0.89; p95 TTFT 1.4 s."
- Skills section grouped: Languages | Backend | AI/LLM (RAG, agents, MCP, evals, LoRA) | Data (MySQL, Postgres/pgvector, Redis) | Cloud/DevOps.
- Projects section with links (GitHub, demo, blog).
- Keep existing Spring Boot experience prominent; frame any automation or integration work as relevant.

### A 12-week plan after finishing this course

```python
plan = {
    "weeks 1-4":  "Polish Spring AI full-stack project; deploy; write README + blog post",
    "weeks 5-7":  "Polish evaluated RAG (Python); add tracing and cost table; second blog post",
    "weeks 8-9":  "Agent + MCP project or fine-tuning project; small OSS contribution",
    "weeks 10-12": "Interview prep: AI system design (2/week mock), Q&A drills, DSA maintenance; apply 10-15 roles/week",
}
for k, v in plan.items():
    print(f"{k:11s} {v}")
```

### Staying current without drowning

The field moves monthly. Sustainable habits:
- Follow primary sources: provider docs/changelogs (Anthropic, OpenAI, Google), Spring AI releases, Hugging Face blog.
- A few high-signal writers: Simon Willison, Hamel Husain, Eugene Yan, Chip Huyen, Sebastian Raschka, Lilian Weng.
- Newsletters such as Latent Space or The Batch, skimmed weekly.
- Re-implement one new idea per month in your projects instead of reading 50 posts.

Focus on durable skills: evaluation, retrieval, system design, security, and clean engineering. Model names change; these don't.

### Key takeaways
- AI engineering = building products on foundation models; backend engineers are well positioned.
- Map your Spring/SQL/security/testing skills to AI engineering explicitly in your resume and interviews.
- Target "Java + AI" backend roles and internal AI projects for the fastest transition.
- Follow a 12-week plan: polish projects, publish, practise AI system design and Q&A, apply consistently.
""", r"""
1. Rewrite your resume headline, summary and 6 bullets using the guidance above (include numbers from your projects).
2. Identify one AI feature you could pitch at your current job; write a one-page proposal (problem, approach, metrics, risks, 4-week plan).
3. Collect 20 AI engineer / GenAI backend job descriptions; tally the most frequent skills and map each to a course module or project. Fill gaps.
4. Set up a weekly learning routine (sources, time slot) and a tracker for applications.
""", [
Q("How does the AI engineer role (as commonly defined in 2026) differ from an ML research scientist?", ["AI engineers invent new architectures", "AI engineers build products on top of foundation models (APIs, RAG, agents, evals) rather than inventing new models", "There is no difference", "AI engineers only label data"], 1, "The role focuses on adapting and evaluating foundation models in products."),
Q("Which backend skill maps most directly to permission-aware RAG?", ["CSS", "Spring Security / authorisation design", "Maven profiles", "Thread dumps"], 1, "Access control design is central to enterprise RAG."),
Q("What's the strongest signal for an internal transition?", ["Certificates only", "Shipping a measured AI feature (even a pilot) at your current company", "Reading many blogs", "Changing your title on LinkedIn"], 1, "Real production impact outweighs credentials."),
], [
R("Chip Huyen - AI Engineering (book)", "https://www.oreilly.com/library/view/ai-engineering/9781098166298/", "book"),
R("roadmap.sh - AI Engineer roadmap", "https://roadmap.sh/ai-engineer", "course"),
R("Latent Space - The Rise of the AI Engineer", "https://www.latent.space/p/ai-engineer", "article"),
R("Simon Willison's blog", "https://simonwillison.net/", "article"),
]),

L("m14-interview-qa", "AI Engineer Interview Q&A: The Questions You Will Be Asked", 60, r"""
## How to use this

These are high-frequency AI engineer interview questions with concise, interview-ready answers. Read the answer, then explain it out loud in your own words with an example from your projects. Aim for 60-90 seconds per answer.

### Fundamentals

**Q1. What is a token and why does it matter?**
A subword unit produced by the tokenizer. Pricing, context limits and latency are all measured in tokens; non-English text and code often use more tokens per character. I count tokens with the provider's tokenizer/count endpoint and budget prompts accordingly.

**Q2. Explain temperature and top-p.**
Temperature scales logits before softmax: low = peaky/deterministic, high = diverse. Top-p samples from the smallest token set whose cumulative probability reaches p. Low temperature for extraction/code, moderate for chat; tune one at a time. Even temperature 0 isn't perfectly deterministic on hosted APIs.

**Q3. How does self-attention work, briefly?**
Each token creates query, key and value vectors; attention weights are softmax(QK^T / sqrt(d)), used to mix values, so each token's representation incorporates relevant context. Multi-head attention learns different relations in parallel; causal masking prevents seeing future tokens in decoders.

**Q4. What are embeddings and how are they trained?**
Dense vectors capturing meaning; sentence embedding models are usually trained contrastively so related texts are close. Used for semantic search, clustering, dedup, classification.

### RAG

**Q5. Walk me through a RAG pipeline.**
Offline: parse, chunk with metadata and context, embed, index (vector + keyword). Online: condense/rewrite query, hybrid retrieve with permission filters, rerank, assemble context within a token budget, generate with citations, verify, log traces.

**Q6. Your RAG system gives wrong answers. How do you debug?**
Look at traces and separate stages: was the right chunk retrieved (recall@k)? Ranked high enough? Did the model use it faithfully? Then fix the failing stage: parsing/chunking, hybrid search, reranking, query rewriting, prompt grounding. Use an eval set to verify the fix.

**Q7. How do you choose chunk size?**
Trade-off between precision and context. Start around 200-500 tokens with overlap, respect document structure, add contextual headers, then tune using retrieval metrics on a labelled set. Consider parent-child retrieval.

**Q8. Why hybrid search and reranking?**
BM25 catches exact terms (IDs, acronyms); embeddings catch meaning; RRF fuses them. A cross-encoder reranker scores query-document pairs jointly for precision on the top candidates.

**Q9. How do you evaluate RAG?**
Retrieval: recall@k, MRR, context precision. Generation: faithfulness, answer relevance, correctness, refusal accuracy, using validated LLM judges. Plus online metrics and error analysis.

### LLM application engineering

**Q10. How do you get reliable JSON from an LLM?**
Schema-constrained structured outputs or tool-forcing; Pydantic/records for parsing; business-rule validation with error feedback retry; nullable fields for unknowns.

**Q11. Explain function/tool calling.**
The model receives tool schemas and returns a structured request; my code validates, authorises and executes it, returns results; loop until a final answer. The model never executes anything itself.

**Q12. How do you reduce latency?**
Streaming, smaller/faster models via routing, prompt caching, fewer sequential calls, parallel retrieval/tool calls, shorter outputs, region-close endpoints.

**Q13. How do you reduce cost?**
Measure per step, then: model routing/cascades, prompt caching, trimming context, response/semantic caching where safe, batch APIs, budgets and limits.

### Agents and MCP

**Q14. Workflow vs agent? When not to use agents?**
Workflows follow predefined code paths; agents let the model choose steps in a loop. Avoid agents when steps are known, latency is tight, errors are costly and hard to detect, or you can't evaluate outcomes.

**Q15. What is MCP?**
An open protocol (JSON-RPC) for connecting AI hosts to tools and data via servers exposing tools, resources and prompts over stdio or Streamable HTTP. It turns M x N integrations into M + N. I've built servers in Python (FastMCP) and Spring AI.

**Q16. How do you secure an agent?**
Least-privilege tools, server-side authorisation with trusted identity, human approval for risky actions, limits on steps/cost, sandboxing, treating tool outputs as untrusted, monitoring and audit logs.

**Q17. What is prompt injection and how do you mitigate it?**
Instructions smuggled via user input or retrieved content. Can't be fully prevented; mitigate by limiting capabilities, separating untrusted content, detection classifiers, dual-LLM isolation, output validation and avoiding the lethal trifecta.

### Fine-tuning and models

**Q18. When would you fine-tune instead of using RAG?**
For behaviour, format, style, or to distil a high-volume narrow task into a cheaper model. Not for frequently changing knowledge. Only after strong prompting and with an eval set.

**Q19. Explain LoRA and QLoRA.**
LoRA freezes weights and learns a low-rank update BA on selected layers (a tiny fraction of parameters); adapters can be merged. QLoRA loads the frozen base in 4-bit NF4 and trains LoRA adapters on top, enabling fine-tuning on a single consumer GPU.

**Q20. What makes vLLM fast?**
PagedAttention for KV cache memory management, continuous batching, prefix caching, quantisation support, tensor parallelism.

### Evals and production

**Q21. How do you build an eval set?**
Start from real traces; error analysis to find failure modes; cases for happy paths, edge cases, adversarial and regressions; tags for slices; deterministic checks plus validated LLM judges; run in CI.

**Q22. How do you validate an LLM judge?**
Compare with human labels on a held-out set; measure true positive and true negative rates (not just accuracy); iterate the rubric; use binary criteria; mitigate position and verbosity bias.

**Q23. How would you roll out a new prompt or model?**
Offline eval gate, shadow traffic, canary/A-B with online metrics, gradual rollout with feature flags, instant rollback via versioned config, pinned model versions.

### Behavioural / experience

**Q24. Tell me about an AI project you built.**
Use your 2-minute story: context, architecture, the interesting challenge, numbers, a trade-off or failure, next steps.

**Q25. Why move from backend to AI engineering?**
Connect your strengths (production systems, APIs, security, testing) with where products are heading; show you've done the work (projects, evals, Spring AI); keep it positive about your current role.

### Practice drill

```python
import random
questions = [f"Q{i}" for i in range(1, 26)]
random.shuffle(questions)
for q in questions[:5]:
    print("Answer out loud in 90 seconds:", q)
```

Do this daily in the last two weeks before interviews, and record yourself once a week.

### Key takeaways
- Know crisp answers across fundamentals, RAG, app engineering, agents/MCP, fine-tuning, evals and production.
- Always anchor answers in your own projects and numbers.
- Practise out loud with a timer; structure beats length.
""", r"""
1. Write your own 5-sentence answer to each of the 25 questions, adding one concrete example from your projects to at least 15 of them.
2. Run the random drill daily for 10 days; record and review two answers per day for clarity and length.
3. Ask an LLM to act as a tough interviewer on RAG and agents (give it a rubric); do two 30-minute mock sessions and note weak areas.
4. Create flashcards for the 10 answers you find hardest and review them with spaced repetition.
""", [
Q("Your RAG app answers wrongly. What's the best first debugging step?", ["Switch to a bigger model", "Inspect traces to determine whether retrieval, ranking or generation failed", "Increase temperature", "Fine-tune immediately"], 1, "Stage-wise diagnosis points to the right fix."),
Q("Which statement about prompt injection is accurate?", ["A good system prompt fully prevents it", "It can't be fully prevented, so systems must limit capabilities and isolate untrusted content", "It only affects open models", "It's solved by low temperature"], 1, "Defence relies on architecture and permissions, not prompts alone."),
Q("A strong answer to 'how would you roll out a new model?' includes:", ["Deploy to everyone on Friday", "Offline eval gate, shadow/canary testing with online metrics, and versioned rollback", "Ask users to test it", "Only check latency"], 1, "Safe rollout combines evals, gradual exposure and rollback."),
], [
R("Hamel Husain - LLM evals FAQ", "https://hamel.dev/blog/posts/evals-faq/", "article"),
R("Anthropic - Building effective agents", "https://www.anthropic.com/engineering/building-effective-agents", "article"),
R("Hugging Face - LLM Course (refresh fundamentals)", "https://huggingface.co/learn/llm-course/chapter1/1", "course"),
R("OWASP Top 10 for LLM Applications", "https://genai.owasp.org/llm-top-10/", "docs"),
]),
]

MODULE = M(
    "m14-ai-system-design-career", 14, "AI System Design & Career", "Advanced", 2,
    "Learn to design LLM chatbots, enterprise RAG and other AI systems at scale the way interviewers expect, with metrics, cost estimates and trade-offs. Turn your projects into a portfolio, plan your move from backend developer to AI engineer, and drill the most common interview questions.",
    [
        "Apply a structured framework to AI system design interviews",
        "Design a support chatbot and permission-aware enterprise RAG at scale with cost and latency estimates",
        "Answer common AI design follow-ups (hallucinations, model choice, outages, rollout)",
        "Build a portfolio of deep, evaluated, deployed projects",
        "Execute a concrete plan and interview preparation for the backend-to-AI-engineer transition",
    ],
    lessons,
    ("Capstone: AI Engineer Job-Ready Package", r"""
Bring everything together into an application-ready package:

1. **Three flagship projects** (from modules 9-13) polished with the README template: diagram, demo GIF, results table from eval scripts, trade-offs, "what didn't work", one-command setup, CI.
2. **At least one public deployment** with spending limits, and one blog post per flagship project with a measured finding.
3. **System design portfolio**: written designs (diagram + 1-2 pages each) for the support chatbot, enterprise RAG and two more designs from lesson 3, each with capacity/cost estimates and a latency budget.
4. **Interview bank**: your own answers to the 25 Q&A questions, with project examples; recordings of 3 mock interviews and notes on improvements.
5. **Updated resume and LinkedIn** positioned as "Backend Engineer (Java/Spring) | LLM Applications, RAG, Spring AI", plus a tracker of 50+ targeted applications.

**Definition of done:** a friend or mentor can open your GitHub and, within 5 minutes, see what you built, how well it works (numbers) and why you made your choices.
"""),
)
