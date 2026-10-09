from ai2_common import Q, R, L, M

lessons = [
L("m09-rag-fundamentals", "Why RAG? Architecture and Mental Model", 35, r"""
## The problem RAG solves

An LLM knows only what was in its training data, frozen at a cutoff date, and nothing about your company's private documents. Ask it about your HR leave policy and it will either refuse or, worse, **confidently invent** one. Options to fix that:

1. **Put the knowledge in the prompt** (context stuffing). Works for small, stable knowledge.
2. **Fine-tune** the model on your data. Expensive, slow to update, poor at memorising facts reliably, can't cite sources, doesn't respect per-user permissions.
3. **Retrieval-Augmented Generation (RAG)**: at question time, *search* your knowledge base for relevant passages and put only those in the prompt, instructing the model to answer from them.

RAG wins for most knowledge-heavy use cases because it is:
- **Fresh**: update a document and the next query sees it. No retraining.
- **Grounded and citable**: answers can point to sources, which builds trust and enables verification.
- **Permission-aware**: retrieve only what the current user may see.
- **Cheap**: only relevant chunks are sent, not the whole corpus.

It is arguably the most common pattern in enterprise AI, and the most common topic in AI engineer interviews.

### The two pipelines

**Offline / ingestion (indexing) pipeline** - like an ETL job:

```
sources (PDF, Confluence, DB, web) -> extract text -> clean -> chunk -> enrich (metadata, context)
      -> embed -> store in vector DB (+ keyword index)
```

**Online / query pipeline** - like a request handler:

```
user question -> (rewrite query) -> retrieve top-k (hybrid) -> (filter, rerank) -> build prompt
      with context -> LLM generates answer with citations -> (post-check) -> response
```

You built most of the retrieval half in module 8. This module connects it to generation and makes it robust.

### The augmented prompt

The core of RAG is a prompt like this:

```python
RAG_PROMPT = '''You are a helpful assistant for ACME employees.
Answer the question using ONLY the documents below.
If the documents don't contain the answer, say "I couldn't find that in the documentation."
Cite sources using their [id].

<documents>
{context}
</documents>

Question: {question}'''

context = "\n\n".join(f'<doc id="{c["id"]}" source="{c["source"]}">\n{c["text"]}\n</doc>'
                      for c in retrieved_chunks)
prompt = RAG_PROMPT.format(context=context, question=question)
```

### Where RAG fails (and the rest of this module)

Think of failures by stage, like debugging a layered Spring app:

| Stage | Failure | Fix (lesson) |
|-------|---------|--------------|
| Ingestion | Bad PDF extraction, tables mangled, chunks without context | Better parsers, contextual chunks (m08) |
| Query | Vague or conversational question ("what about the second one?") | Query rewriting (lesson 3) |
| Retrieval | Right chunk not in top-k | Hybrid search, better embeddings, metadata filters (lesson 4) |
| Ranking | Right chunk retrieved but ranked low | Reranking (lesson 4) |
| Generation | Model ignores context or hallucinates | Grounding prompts, citations (lesson 5) |
| Knowledge | Answer requires connecting many documents | GraphRAG / agentic RAG (lesson 6) |

You can only find which stage is broken by **evaluating each stage separately** (lesson 7).

### RAG vs long context

With million-token windows, why not paste everything? For small corpora (a few documents) that's often the best option: simpler and no retrieval errors. But for large or growing corpora, long context is slower, costlier per query, can't enforce permissions, and models still miss details in huge inputs. In practice teams combine them: retrieve generously (more, bigger chunks) and let the long context window absorb it. Prompt caching makes large shared context cheaper.

### Frameworks

- **LangChain / LangGraph**: broad integrations, composable chains and graphs.
- **LlamaIndex**: data-centric, strong ingestion/indexing/query-engine abstractions.
- **Haystack**, **DSPy**, and on the Java side **Spring AI** (module 13) and LangChain4j.

Frameworks speed you up, but first build RAG by hand once (next lesson) so you understand what they hide.

### Key takeaways
- RAG = search + prompt + generate; it adds fresh, private, citable knowledge without retraining.
- Two pipelines: offline ingestion and online query.
- Debug and evaluate per stage: ingestion, query, retrieval, ranking, generation.
""", r"""
1. Draw (on paper or excalidraw) the ingestion and query pipelines for a "company HR policy assistant", labelling the components and data stores.
2. For each failure stage in the table, write one concrete example question from the HR domain that would fail at that stage.
3. Decide: for a 30-page employee handbook that rarely changes, would you use RAG or long-context stuffing? Write a 5-sentence justification including cost and permissions.
""", [
Q("Which is a key advantage of RAG over fine-tuning for company knowledge?", ["RAG changes the model weights", "Documents can be updated instantly and answers can cite sources", "RAG needs no data", "RAG removes the need for prompts"], 1, "RAG keeps knowledge outside the model, making it fresh and citable."),
Q("The right chunk is retrieved at rank 40 but you only send the top 5. Which stage is failing?", ["Ingestion", "Ranking", "Generation", "Tokenization"], 1, "It was retrieved but ranked too low; a reranker addresses this."),
Q("Why tell the model to say 'I couldn't find that' when the documents lack the answer?", ["It saves tokens", "It gives the model an explicit alternative to hallucinating", "Providers require it", "It improves retrieval"], 1, "Without an out, models tend to fill gaps with invented answers."),
], [
R("Original RAG paper (Lewis et al., 2020)", "https://arxiv.org/abs/2005.11401", "article"),
R("LangChain - Build a RAG app tutorial", "https://python.langchain.com/docs/tutorials/rag/", "docs"),
R("LlamaIndex - High-level concepts (RAG)", "https://docs.llamaindex.ai/en/stable/getting_started/concepts/", "docs"),
R("Chip Huyen - AI Engineering, ch. 6 (RAG and Agents)", "https://www.oreilly.com/library/view/ai-engineering/9781098166298/", "book"),
]),

L("m09-naive-rag-end-to-end", "Build a Naive RAG System End-to-End", 60, r"""
## Goal

Build a complete question-answering system over a folder of Markdown files, from scratch, in about 100 lines: no framework, so every step is visible. We'll use sentence-transformers for embeddings, Chroma as the vector store (swap to pgvector later), and Claude for generation (any chat model works).

### Step 1: Load and chunk

```python
import pathlib, hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

def load_chunks(folder):
    for path in pathlib.Path(folder).rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        for i, chunk in enumerate(splitter.split_text(text)):
            yield {
                "id": hashlib.sha1(f"{path}:{i}".encode()).hexdigest()[:12],
                "text": f"Title: {title}\n\n{chunk}",
                "meta": {"source": str(path), "title": title, "chunk": i},
            }
```

### Step 2: Embed and index

```python
import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
db = chromadb.PersistentClient("./rag_db")
col = db.get_or_create_collection("kb", metadata={"hnsw:space": "cosine"})

def ingest(folder, batch=64):
    chunks = list(load_chunks(folder))
    for i in range(0, len(chunks), batch):
        b = chunks[i:i + batch]
        vecs = embedder.encode([c["text"] for c in b], normalize_embeddings=True)
        col.upsert(ids=[c["id"] for c in b], documents=[c["text"] for c in b],
                   metadatas=[c["meta"] for c in b], embeddings=vecs.tolist())
    print(f"indexed {len(chunks)} chunks")
```

Note `upsert` with deterministic ids: re-running ingestion doesn't duplicate data.

### Step 3: Retrieve

```python
def retrieve(question, k=5):
    q = embedder.encode(question, normalize_embeddings=True).tolist()
    r = col.query(query_embeddings=[q], n_results=k)
    return [{"id": i, "text": d, "source": m["source"], "score": 1 - dist}
            for i, d, m, dist in zip(r["ids"][0], r["documents"][0],
                                     r["metadatas"][0], r["distances"][0])]
```

### Step 4: Generate with grounding

```python
from anthropic import Anthropic
llm = Anthropic()

SYSTEM = '''You answer questions about our engineering documentation.
Use ONLY the provided documents. If they do not contain the answer, reply exactly:
"I don't know based on the documentation."
After each claim, cite the supporting document like [doc-3]. Be concise.'''

def answer(question, k=5):
    chunks = retrieve(question, k)
    context = "\n\n".join(f'<doc id="doc-{n}" source="{c["source"]}">\n{c["text"]}\n</doc>'
                          for n, c in enumerate(chunks, 1))
    msg = llm.messages.create(
        model="claude-sonnet-4-5", max_tokens=700, temperature=0.2, system=SYSTEM,
        messages=[{"role": "user",
                   "content": f"<documents>\n{context}\n</documents>\n\nQuestion: {question}"}])
    return {"answer": msg.content[0].text,
            "sources": [(f"doc-{n}", c["source"], round(c["score"], 3))
                        for n, c in enumerate(chunks, 1)],
            "usage": msg.usage}

if __name__ == "__main__":
    ingest("./docs")
    res = answer("How do I configure a connection pool size?")
    print(res["answer"]); print(res["sources"])
```

That's a working RAG system. Notice the decisions baked in: chunk size, overlap, embedding model, k, prompt wording, temperature. Each is a tunable parameter you'll evaluate later.

### Step 5: Wrap it in an API

```python
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

class Ask(BaseModel):
    question: str

@app.post("/ask")
def ask(body: Ask):
    r = answer(body.question)
    return {"answer": r["answer"], "sources": r["sources"]}
```

### The same thing in LangChain (for comparison)

```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

store = Chroma(collection_name="kb", embedding_function=HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"), persist_directory="./lc_db")
retriever = store.as_retriever(search_kwargs={"k": 5})
prompt = ChatPromptTemplate.from_messages([("system", SYSTEM),
    ("human", "<documents>{context}</documents>\n\nQuestion: {question}")])
model = ChatAnthropic(model="claude-sonnet-4-5")

def rag(question):
    docs = retriever.invoke(question)
    ctx = "\n\n".join(d.page_content for d in docs)
    return (prompt | model).invoke({"context": ctx, "question": question}).content
```

Same steps, different packaging. Knowing the hand-built version lets you debug the framework one.

### Why "naive"?

This pipeline breaks on: follow-up questions ("and for MySQL?"), queries with exact identifiers, questions whose answer spans several docs, docs a user shouldn't see, and irrelevant top-k results being stuffed in anyway. The next lessons fix each.

### Key takeaways
- A RAG system is load -> chunk -> embed -> store, then retrieve -> prompt -> generate.
- Deterministic ids + upsert give idempotent ingestion.
- Return sources and usage with every answer for transparency and cost tracking.
""", r"""
1. Build this exact pipeline over at least 30 Markdown files (Spring Boot guides, your own notes, or any docs).
2. Write 15 questions: 10 answerable, 5 not answerable from the docs. Check that the 5 produce "I don't know".
3. Swap Chroma for your pgvector table from module 8 behind the same `retrieve()` function.
4. Add `/ask` FastAPI endpoint and log question, retrieved ids, answer, tokens and latency to a JSONL file - this becomes your first trace log.
""", [
Q("Why use deterministic chunk ids with upsert during ingestion?", ["It improves embedding quality", "Re-running ingestion updates rather than duplicates chunks", "Chroma requires random ids", "It reduces tokens"], 1, "Idempotent ingestion avoids duplicate chunks polluting results."),
Q("Which parameter is NOT a typical RAG tuning knob?", ["Chunk size", "Top-k", "Embedding model", "The HTTP port of the API"], 3, "Chunking, k and model choice change retrieval quality; the port doesn't."),
Q("Why return sources alongside the answer?", ["To increase tokens", "So users and evaluators can verify claims and you can debug retrieval", "It is required by Chroma", "To hide the answer"], 1, "Sources enable trust, verification and debugging."),
], [
R("LangChain - RAG tutorial part 1", "https://python.langchain.com/docs/tutorials/rag/", "docs"),
R("LlamaIndex - Starter tutorial", "https://docs.llamaindex.ai/en/stable/getting_started/starter_example/", "docs"),
R("Anthropic Cookbook - RAG examples", "https://github.com/anthropics/anthropic-cookbook", "docs"),
R("freeCodeCamp - Learn RAG from scratch (LangChain engineer)", "https://www.youtube.com/watch?v=sVcwVQRHIc8", "video"),
]),

L("m09-query-transformation", "Query Rewriting, Multi-Query, HyDE and Routing", 45, r"""
## The user's question is rarely the best search query

Users type "what about for prod?", "it's not working", or 40-word rambling questions. Searching with that text directly gives poor retrieval. **Query transformation** uses an LLM (usually a cheap, fast one) to turn the raw input into better search queries before retrieval.

### 1. Conversational condensation (must-have for chat)

In a multi-turn chat, follow-ups depend on history. Rewrite them into standalone questions:

```python
CONDENSE = '''Given the conversation and a follow-up question, rewrite the follow-up
as a standalone search query containing all needed context. Return only the query.

<conversation>
{history}
</conversation>
Follow-up: {question}'''

history = "User: How do I set the Hikari pool size in Spring Boot?\nAssistant: Use spring.datasource.hikari.maximum-pool-size ..."
standalone = small_llm(CONDENSE.format(history=history, question="and the timeout?"))
# -> "How do I set the HikariCP connection timeout in Spring Boot?"
```

Without this step, retrieving with "and the timeout?" returns random chunks.

### 2. Query rewriting / expansion

Turn a messy question into a clean, keyword-rich query; add synonyms or the domain terms docs actually use ("leave" -> "paid time off, PTO, vacation policy").

### 3. Multi-query

Generate 3-5 differently phrased queries, retrieve for each, and fuse results with RRF (from module 8). Increases recall when the question is ambiguous or the docs use varied vocabulary.

```python
def multi_query_retrieve(question, n=4, k=5):
    prompt = f"Write {n} different search queries for: {question}\nOne per line, no numbering."
    queries = [question] + [q.strip() for q in small_llm(prompt).splitlines() if q.strip()]
    ranked_lists = [[c["id"] for c in retrieve(q, k=20)] for q in queries]
    fused = rrf(ranked_lists)[:k]
    return [chunk_by_id[i] for i in fused]
```

### 4. Decomposition

Complex questions ("Compare the parental leave policy in India and the US offices") need multiple retrievals. Ask the LLM to split into sub-questions, retrieve for each, then answer with all context. This is the stepping stone to agentic RAG.

### 5. HyDE: Hypothetical Document Embeddings

Questions and answers look different, so their embeddings can be far apart. HyDE asks the LLM to write a *hypothetical answer* (may be wrong in details) and embeds that instead, since a fake answer looks more like the real document than the question does.

```python
def hyde_retrieve(question, k=5):
    fake = small_llm(f"Write a short passage from technical documentation that answers: {question}")
    return retrieve(fake, k)
```

Helps for some domains, hurts when the LLM's guess is far off (very private or novel topics). Evaluate.

### 6. Routing

Not every question should hit the same index. A router classifies the query and picks a path:
- Which **index**: HR docs vs engineering docs vs product catalogue.
- Which **method**: vector search, SQL query on structured data (text-to-SQL), web search, or no retrieval at all (greetings, simple math).

```python
from pydantic import BaseModel
from typing import Literal

class Route(BaseModel):
    destination: Literal["hr_docs", "eng_docs", "orders_sql", "none"]
    reason: str

route = structured_llm("Route this question to the best data source.", question, schema=Route)
if route.destination == "orders_sql":
    rows = run_text_to_sql(question)          # with a read-only DB user!
elif route.destination == "none":
    ...
```

### 7. Self-query: extracting filters from the question

"Python incidents from last month with severity high" contains **structured filters** (`team=python`, `date>=...`, `severity=high`) plus a semantic part ("incidents"). Use structured output to extract both, then run a filtered vector search. Covered with metadata filters in the next lesson.

### Costs and latency

Each transformation is an extra LLM call (often 200-800 ms). Use a small model, run independent steps in parallel, cache rewrites for repeated queries, and only add a technique when evals show it helps. A common production combo is: **condense (if chat) -> route -> hybrid retrieve -> rerank**.

### Key takeaways
- Always condense follow-ups into standalone queries in conversational RAG.
- Multi-query and HyDE improve recall for ambiguous or vocabulary-mismatched questions; measure them.
- Decompose complex questions; route queries to the right source or method.
- Use small models and parallelism to keep latency in check.
""", r"""
1. Add conversational condensation to your RAG API. Create 5 two-turn conversations where the second question is a follow-up, and compare retrieval with and without condensing.
2. Implement multi-query with RRF and HyDE. Compare recall@5 against the baseline on your eval set.
3. Build a router with structured output that sends questions to "docs", "sql" (a small SQLite table of orders), or "none". Test with 15 mixed questions.
4. Measure the added latency of each technique and decide which to keep.
""", [
Q("A chat user asks 'and what about MySQL?' after a Postgres question. What step fixes retrieval?", ["Increase k", "Condense the follow-up with history into a standalone query", "Use HNSW", "Lower temperature"], 1, "The follow-up lacks context; rewriting makes it self-contained."),
Q("What does HyDE embed for retrieval?", ["The raw question", "A hypothetical answer generated by an LLM", "The system prompt", "Random noise"], 1, "Hypothetical answers resemble real documents more than questions do."),
Q("What is query routing used for?", ["Load balancing HTTP traffic", "Choosing the right data source or retrieval method for each question", "Encrypting queries", "Choosing temperature"], 1, "Routers send questions to the best index, SQL, web or no retrieval."),
], [
R("HyDE paper: Precise Zero-Shot Dense Retrieval without Relevance Labels", "https://arxiv.org/abs/2212.10496", "article"),
R("LangChain - Query analysis / rewriting how-tos", "https://python.langchain.com/docs/concepts/retrieval/", "docs"),
R("LlamaIndex - Routers", "https://docs.llamaindex.ai/en/stable/module_guides/querying/router/", "docs"),
R("DeepLearning.AI - Advanced Retrieval for AI with Chroma", "https://www.deeplearning.ai/short-courses/advanced-retrieval-for-ai/", "course"),
]),

L("m09-filters-reranking-context", "Metadata Filters, Permissions, Reranking and Context Assembly", 45, r"""
## Retrieval is more than nearest neighbours

Production RAG combines semantic similarity with **hard constraints** (who can see what, which product version, which date range) and then carefully assembles the context window.

### Metadata filtering

Every chunk carries metadata (module 8). Use it to narrow the search space *before* similarity ranking:

```python
# Chroma
col.query(query_embeddings=[qv], n_results=10,
          where={"$and": [{"product": "payments"}, {"version": {"$gte": 3}}]})
```

```sql
-- pgvector: filters are just SQL
SELECT id, content FROM chunks
WHERE tenant_id = %(tenant)s AND product = 'payments' AND published_at >= now() - interval '1 year'
ORDER BY embedding <=> %(q)s LIMIT 10;
```

### Self-query: let the LLM extract filters

```python
from pydantic import BaseModel
from typing import Literal, Optional

class SearchPlan(BaseModel):
    query: str                                    # semantic part
    product: Optional[Literal["payments", "orders", "auth"]] = None
    min_version: Optional[int] = None
    year: Optional[int] = None

plan = structured_llm("Extract a search plan. Use null when not specified.",
                      "How did refunds work in payments v3 in 2025?", SearchPlan)
# SearchPlan(query='how refunds work', product='payments', min_version=3, year=2025)
```

Validate extracted values against allowed enums. Never let the LLM produce raw SQL for filters without parameterisation.

### Permissions: the non-negotiable filter

In enterprise RAG, the biggest real-world bug is **leaking documents** the user isn't allowed to see. Rules:
1. Store ACL info on chunks (`tenant_id`, `allowed_groups`, `doc_id`).
2. Get the user's identity and groups from your auth system (the JWT in your Spring app), never from the prompt.
3. Apply the filter in the retrieval query, in code. The LLM never decides access.
4. Sync permission changes from the source system (e.g. SharePoint/Confluence) and handle deletions promptly.

```python
def secure_retrieve(question, user):
    return vector_search(question, k=50,
        filter={"tenant_id": user.tenant_id, "allowed_groups": {"$in": user.groups}})
```

### Reranking in RAG

From module 8: retrieve ~50 with hybrid search, rerank with a cross-encoder, keep the top 5-8. In RAG this matters doubly, because irrelevant chunks don't just waste tokens: they **distract the model** and can cause wrong answers. A reranker score threshold also gives you a principled "nothing relevant found" signal.

```python
def retrieve_for_rag(question, user, k_final=6, min_score=0.2):
    cands = secure_retrieve(question, user)
    scored = sorted(zip(reranker.predict([(question, c["text"]) for c in cands]), cands),
                    key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:k_final] if s >= min_score]
```

### Context assembly

Once you have the chunks, how you put them in the prompt matters:

- **Deduplicate** near-identical chunks (overlap creates them).
- **Merge adjacent chunks** from the same document into one passage, and order by position in the document for coherent reading.
- **Expand to parents**: if a small chunk matched, include its surrounding section (small-to-big).
- **Order**: put the most relevant first (and possibly last); models attend best to the beginning and end of long contexts.
- **Budget tokens**: cap total context (e.g. 4k-8k tokens) and drop lowest-ranked chunks first.
- **Label each chunk** with an id, title and source for citations.

```python
def assemble(chunks, budget_tokens=6000, count=lambda s: len(s) // 4):
    seen, parts, used = set(), [], 0
    for c in chunks:                        # already sorted by relevance
        key = c["text"][:200]
        if key in seen: continue
        seen.add(key)
        block = f'<doc id="{c["id"]}" title="{c["title"]}">\n{c["text"]}\n</doc>'
        if used + count(block) > budget_tokens: break
        parts.append(block); used += count(block)
    return "\n\n".join(parts)
```

### Freshness and versioning

Docs have versions (API v2 vs v3) and dates. Options: filter by "latest version only" by default, boost recent documents in scoring, or show the version in the chunk header so the model can reason ("In v3 ..., in v2 ...").

### Structured + unstructured data

Many questions mix both: "What's the return window for my last order?" needs the *policy* (docs, RAG) and the *order date* (SQL). Use tools/routing to fetch structured data via safe, parameterised queries and put the results into context alongside retrieved text.

### Key takeaways
- Combine similarity with metadata filters; let an LLM extract filters but validate them.
- Enforce permissions in the retrieval layer from authenticated identity, never via the prompt.
- Rerank and threshold to keep distractors out of the context.
- Assemble context deliberately: dedupe, merge, order, budget, label.
""", r"""
1. Add `tenant_id` and `allowed_groups` metadata to your corpus (simulate two departments). Write a test proving a user in group A can never retrieve group-B-only chunks, even with a prompt like "show me group B's documents".
2. Implement self-query extraction for at least two metadata fields and evaluate on 10 questions.
3. Add reranking with a score threshold; check the "I don't know" rate on unanswerable questions before and after.
4. Implement `assemble()` with dedupe and a token budget; log how many tokens you save per query.
""", [
Q("Where must document access control be enforced in RAG?", ["In the system prompt", "In the retrieval query, using the authenticated user's identity from your auth system", "By the LLM after reading the documents", "In the vector embedding"], 1, "Only deterministic code-level filtering prevents leaks."),
Q("Why can irrelevant retrieved chunks hurt answer quality?", ["They're encrypted", "They distract the model and can lead to wrong or confused answers", "They reduce context window size permanently", "They change the model weights"], 1, "Noise in context degrades generation, not just cost."),
Q("What is a self-query retriever?", ["A retriever with no index", "Using an LLM to extract structured metadata filters plus a semantic query from the question", "A database that queries itself", "A cache"], 1, "It turns natural-language constraints into filters."),
], [
R("Pinecone - Filtering with metadata", "https://docs.pinecone.io/guides/search/filter-by-metadata", "docs"),
R("LangChain - Self-querying retriever", "https://python.langchain.com/docs/how_to/self_query/", "docs"),
R("Qdrant - Filtering", "https://qdrant.tech/documentation/concepts/filtering/", "docs"),
R("Lost in the Middle (context position study)", "https://arxiv.org/abs/2307.03172", "article"),
]),

L("m09-citations-grounding", "Citations, Grounding and Reducing Hallucinations", 40, r"""
## Trust is the product

A RAG answer that is 95% right but occasionally invents a policy is dangerous in HR, legal, finance or medicine. Grounding techniques make answers **faithful to sources** and **verifiable**.

Two different failure types:
- **Unfaithful**: the answer says something *not supported* by the retrieved context (hallucination relative to sources).
- **Incorrect but faithful**: the context itself was wrong or outdated. That's a data/retrieval problem.

### 1. Grounding instructions

- "Answer only from the documents."
- "If the documents don't contain the answer, say so." (give the out)
- "Do not use prior knowledge about this company."
- "Quote exact figures; do not round or infer numbers."

### 2. Inline citations

Label each chunk with an id and require a citation after each claim:

```python
SYSTEM = '''Answer using only the documents. After every sentence that states a fact,
add the id(s) of supporting documents in square brackets, e.g. [d2] or [d1][d4].
Never cite a document that doesn't support the sentence.'''
```

Then **verify** citations in code: every cited id must exist among retrieved ids; strip or flag unknown ones.

```python
import re
def check_citations(answer, valid_ids):
    cited = set(re.findall(r"\[(d\d+)\]", answer))
    return {"unknown": cited - valid_ids, "uncited_sentences":
            [s for s in re.split(r"(?<=[.!?])\s+", answer) if s and "[" not in s]}
```

### 3. Quote-then-answer

For high-stakes answers, ask the model first to extract **verbatim quotes** relevant to the question, then answer using only those quotes. Quotes can be checked by exact string match against the source, giving strong evidence of grounding.

```python
PROMPT = '''First, inside <quotes>, copy word-for-word the sentences from the documents
that are relevant to the question (with their doc id). If none, write NONE.
Then, inside <answer>, answer using only those quotes, citing ids.'''

def verify_quotes(quotes, docs_by_id):
    ok = []
    for doc_id, quote in quotes:
        ok.append(quote.strip() in docs_by_id[doc_id])
    return all(ok)
```

### 4. Structured answers with citations

Return JSON so the UI can render clickable sources:

```python
from pydantic import BaseModel
class Claim(BaseModel):
    text: str
    source_ids: list[str]
class GroundedAnswer(BaseModel):
    claims: list[Claim]
    answerable: bool
```

Some providers also offer native citation features (e.g. Anthropic's citations mode returns character spans of the source text that support each part of the answer). Worth using when available.

### 5. Post-generation verification

Add a check after generation, especially for risky domains:
- **NLI / faithfulness check**: a model (or LLM judge) decides whether each claim is entailed by the cited chunk.
- If unsupported claims are found, regenerate, remove them, or fall back to "I'm not sure, here are the relevant documents".
- This costs latency; apply selectively (e.g. only for answers containing numbers or policies).

### 6. UX for trust

- Show sources with titles and links; highlight the quoted span.
- Show "last updated" dates of sources.
- Let users give thumbs up/down and report wrong answers: this feedback becomes eval data (module 12).
- For no-answer cases, show the closest documents rather than a dead end.

### Hallucination sources to know (interview favourite)

1. Retrieval returned nothing relevant, and the model filled the gap.
2. The context was ambiguous or contradictory (two policy versions).
3. The question had a false premise ("Why was the Bangalore office closed?").
4. Long context; the relevant fact was buried.
5. The model's prior knowledge overrode the context (e.g. public info about a similarly named product).
6. High temperature or an instruction to "always give an answer".

### Key takeaways
- Faithfulness (supported by sources) and correctness are different; measure both.
- Use grounding instructions, labelled chunks, required citations, and verify citations in code.
- Quote-then-answer and post-hoc verification raise trust for high-stakes domains.
- Design the UI to make verification easy and capture feedback.
""", r"""
1. Add inline citations to your RAG system and implement `check_citations`. Run 20 questions and count answers with invalid or missing citations.
2. Implement quote-then-answer and verify quotes by exact match. What fraction of quotes are truly verbatim?
3. Write 5 false-premise questions about your corpus and see whether the system corrects the premise. Improve the prompt until it does.
4. Return a `GroundedAnswer` JSON and render it as HTML with clickable sources.
""", [
Q("An answer is fully supported by retrieved docs, but the docs are outdated. This is:", ["Unfaithful generation", "Faithful but incorrect - a data/retrieval freshness problem", "A tokenizer issue", "Prompt injection"], 1, "The generator was faithful; the knowledge base was wrong."),
Q("What's the advantage of quote-then-answer?", ["Fewer tokens", "Quotes can be verified by exact string match, giving strong evidence of grounding", "It disables citations", "It speeds up retrieval"], 1, "Verbatim quotes are mechanically checkable."),
Q("Why verify citation ids in code?", ["The model may cite ids that don't exist or weren't retrieved", "To compress the answer", "Because JSON requires it", "To change temperature"], 0, "Models can fabricate or mis-assign citations."),
], [
R("Anthropic - Citations", "https://docs.anthropic.com/en/docs/build-with-claude/citations", "docs"),
R("Anthropic - Reduce hallucinations", "https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations", "docs"),
R("Eugene Yan - Patterns for building LLM-based systems", "https://eugeneyan.com/writing/llm-patterns/", "article"),
]),

L("m09-graphrag-agentic-rag", "Beyond Naive RAG: GraphRAG, Agentic RAG and Long Context", 40, r"""
## When chunk retrieval isn't enough

Chunk-based RAG answers "local" questions well: the answer sits in one or two passages. It struggles with:
- **Global questions**: "What are the main themes across all customer complaints this quarter?" No single chunk contains this.
- **Multi-hop questions**: "Which team owns the service that calls the payments API that failed last week?" Requires connecting facts across documents.
- **Questions needing iteration**: the first search reveals what to search next.

Three families of solutions: knowledge graphs (GraphRAG), agentic retrieval, and smarter use of long context.

### Knowledge graphs in 2 minutes

A knowledge graph stores **entities** (nodes: people, services, products) and **relationships** (edges: OWNS, CALLS, DEPENDS_ON) as triples: `(OrderService) -[CALLS]-> (PaymentsAPI)`. Graph databases (Neo4j, with its Cypher query language) make multi-hop traversal natural:

```
MATCH (t:Team)-[:OWNS]->(s:Service)-[:CALLS]->(:API {name: "payments"})
RETURN t.name, s.name
```

### GraphRAG

**GraphRAG** (popularised by Microsoft Research) uses an LLM to build the graph from unstructured text:

1. **Extract**: for each chunk, ask an LLM to output entities and relationships (structured output).
2. **Build**: merge them into a graph; dedupe entities ("ACME Corp" = "ACME").
3. **Cluster**: detect communities (groups of densely connected entities) and have an LLM write a **summary per community**, hierarchically.
4. **Query**:
   - *Local search*: find entities in the question, traverse their neighbourhood, gather related chunks and facts.
   - *Global search*: map-reduce over community summaries to answer corpus-wide questions.

```python
from pydantic import BaseModel
class Triple(BaseModel):
    subject: str
    relation: str
    object: str
class Extraction(BaseModel):
    triples: list[Triple]

def extract_triples(chunk_text):
    return structured_llm(
        "Extract factual (subject, relation, object) triples about services, teams and APIs. "
        "Use canonical names. Relations in UPPER_SNAKE_CASE.", chunk_text, Extraction).triples

# Store with networkx for a prototype
import networkx as nx
G = nx.MultiDiGraph()
for chunk in chunks:
    for t in extract_triples(chunk["text"]):
        G.add_edge(t.subject, t.object, relation=t.relation, source=chunk["id"])

def neighbourhood_facts(entity, hops=2):
    nodes = nx.single_source_shortest_path_length(G.to_undirected(), entity, cutoff=hops)
    return [(u, d["relation"], v) for u, v, d in G.edges(data=True) if u in nodes and v in nodes]
```

**Trade-offs**: graph construction is LLM-heavy and expensive for large corpora, extraction errors propagate, and keeping the graph updated is work. Lighter variants (e.g. LightRAG, or simply adding entity tags as metadata) capture much of the benefit. Use GraphRAG when your questions are truly relational or global; don't use it by default.

### Agentic RAG

Instead of a fixed retrieve-then-generate pipeline, give an LLM **retrieval as a tool** and let it decide what to search, read results, and search again (module 10 covers agents properly):

```python
TOOLS = [{
  "name": "search_docs",
  "description": "Search the engineering knowledge base. Use specific queries. Can be called multiple times.",
  "input_schema": {"type": "object", "properties": {
      "query": {"type": "string"},
      "product": {"type": "string", "enum": ["payments", "orders", "auth"]}},
      "required": ["query"]}}]
# The tool-calling loop from module 7 runs search_docs until the model answers.
```

Benefits: handles multi-hop and decomposition naturally, can combine sources (docs + SQL + web). Costs: more latency, more tokens, less predictability. Cap the number of iterations and log every step.

Related ideas: **corrective RAG** (grade retrieved docs; if poor, rewrite the query or fall back to web search) and **self-RAG** (model decides when retrieval is needed and critiques its own output).

### Long context + RAG

Large context windows change the design space:
- Retrieve more and bigger units (whole sections or documents instead of 300-token chunks).
- For small corpora, skip retrieval: load the corpus once, cache the prefix with prompt caching, ask many questions cheaply.
- Use RAG to choose *which documents*, then long context to read them fully.

### Choosing an approach

| Question type | Approach |
|--------------|----------|
| Fact in one passage | Naive/advanced RAG |
| Needs several searches or sources | Agentic RAG |
| Relationship traversal, corpus-wide themes | GraphRAG / knowledge graph |
| Small, stable corpus | Long context + caching |
| Numbers in tables/DB | Text-to-SQL or tools, not embeddings |

### Key takeaways
- Chunk RAG fails on global and multi-hop questions.
- GraphRAG extracts entities/relations with an LLM, clusters and summarises them; powerful but costly.
- Agentic RAG makes retrieval a tool the model can call repeatedly.
- Long context complements RAG; pick the approach by question type.
""", r"""
1. Take 20 chunks about a fictional microservice system (write them yourself: teams, services, APIs, incidents). Extract triples with structured output into networkx.
2. Answer 5 multi-hop questions with (a) naive RAG and (b) graph neighbourhood facts + chunks. Compare.
3. Implement agentic RAG with a `search_docs` tool and a max of 4 iterations. Log the queries the model issues for a multi-hop question.
4. Write a short decision memo: for your semantic search project from module 8, which approach fits and why.
""", [
Q("Which question is chunk-based RAG worst at?", ["'What is the refund window?'", "'What are the main themes across all 5,000 support tickets?'", "'What port does the service use?'", "'Who wrote this doc?'"], 1, "Global summarisation questions aren't answered by any single chunk."),
Q("In GraphRAG, what are community summaries used for?", ["Encrypting the graph", "Answering global questions by map-reducing over summaries of entity clusters", "Training the embedding model", "Replacing the LLM"], 1, "Hierarchical community summaries enable corpus-wide answers."),
Q("What does agentic RAG change compared with a fixed pipeline?", ["It removes retrieval", "The LLM decides when and what to retrieve via tools, possibly iterating", "It always uses a graph database", "It fine-tunes the model"], 1, "Retrieval becomes a tool in an agent loop."),
], [
R("Microsoft Research - GraphRAG project", "https://microsoft.github.io/graphrag/", "docs"),
R("From Local to Global: A Graph RAG Approach (paper)", "https://arxiv.org/abs/2404.16130", "article"),
R("LangGraph - Agentic RAG tutorial", "https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/", "docs"),
R("Neo4j GraphAcademy - free courses on knowledge graphs and LLMs", "https://graphacademy.neo4j.com/", "course"),
]),

L("m09-evaluating-rag", "Evaluating RAG Systems", 50, r"""
## You can't improve what you don't measure

Every RAG change (chunk size, embedding model, k, reranker, prompt) can help some questions and hurt others. Without evaluation, you are guessing. RAG evaluation splits into **retrieval** metrics and **generation** metrics, so you can locate the failing stage.

### Step 1: Build an eval dataset

Each item: a question, the **reference answer**, and the **relevant document/chunk ids**.

Sources for questions:
- Real user queries from logs (best).
- Subject-matter experts writing questions they get asked.
- **Synthetic generation**: ask an LLM to write questions from random chunks (the chunk id becomes the gold label). Fast, but review a sample, filter trivial questions, and add realistic messy phrasing.

```python
def synth_question(chunk):
    return structured_llm(
        "Write one realistic question a new employee might ask that this passage answers, "
        "and the short correct answer. Don't copy phrases verbatim.",
        chunk["text"], schema=QAItem)          # QAItem(question: str, answer: str)

eval_set = [{"question": qa.question, "reference": qa.answer, "gold_ids": [c["id"]]}
            for c in random.sample(chunks, 50) for qa in [synth_question(c)]]
```

Include **hard cases**: unanswerable questions, multi-hop questions, exact-identifier queries, follow-ups, and questions where two documents conflict. 50-200 items is a solid start; grow it from production failures.

### Step 2: Retrieval metrics

Already familiar from module 8:
- **Recall@k / hit rate**: is a gold chunk in the top k?
- **MRR / nDCG**: is it near the top?
- **Context precision**: what fraction of retrieved chunks are relevant (noise level)?

These are cheap, deterministic and fast: run them on every change.

### Step 3: Generation metrics

Most use an **LLM-as-judge** (module 12 goes deeper):

- **Faithfulness / groundedness**: are all claims in the answer supported by the retrieved context?
- **Answer relevance**: does it actually address the question?
- **Answer correctness**: does it match the reference answer?
- **Refusal correctness**: for unanswerable questions, did it say "I don't know"?

```python
from pydantic import BaseModel
from typing import Literal

class FaithJudgement(BaseModel):
    unsupported_claims: list[str]
    verdict: Literal["faithful", "partially", "unfaithful"]

JUDGE = '''You are grading a RAG answer. List every claim in the ANSWER that is not
supported by the CONTEXT. Then give a verdict.
<context>{context}</context>
<answer>{answer}</answer>'''

def judge_faithfulness(context, answer):
    return structured_llm(JUDGE.format(context=context, answer=answer), "", FaithJudgement)
```

Judge tips: use binary or 3-level scales (not 1-10), ask for reasoning/evidence, use a strong model, and **validate the judge against human labels** on 30-50 examples before trusting it.

### Step 4: Frameworks

- **Ragas**: metrics like faithfulness, answer relevancy, context precision/recall; test set generation.
- **DeepEval**, **TruLens**, **Arize Phoenix**, **LangSmith**, **Braintrust**: evaluation + tracing platforms.

```python
# pip install ragas  (API evolves; check the docs for the current version)
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

ds = Dataset.from_dict({
    "question": qs, "answer": answers, "contexts": contexts_lists, "ground_truth": refs})
print(evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision, context_recall]))
```

Frameworks are convenient, but understand what each metric's prompt does; a hand-written judge tuned to your domain is often better.

### Step 5: Run experiments like an engineer

```python
configs = [
    {"name": "baseline", "chunk": 1200, "k": 5, "rerank": False},
    {"name": "small_chunks", "chunk": 600, "k": 8, "rerank": False},
    {"name": "hybrid_rerank", "chunk": 1200, "k": 6, "rerank": True},
]
for cfg in configs:
    results = run_pipeline_on(eval_set, cfg)
    print(cfg["name"], retrieval_metrics(results), generation_metrics(results),
          avg_latency(results), avg_cost(results))
```

Track quality **and** latency **and** cost; a 2% quality gain that doubles latency may not be worth it. Store results with the config and git commit.

### Step 6: Error analysis beats dashboards

Hamel Husain's advice, widely adopted: **read your traces**. Look at 50 failures, categorise them (retrieval miss, wrong chunk ranked first, ignored context, formatting, refusal when it shouldn't), count categories, fix the biggest bucket first. Metrics tell you *that* something is wrong; reading tells you *why*.

### Key takeaways
- Build an eval set with questions, reference answers and gold chunk ids, including hard cases.
- Measure retrieval (recall@k, MRR, precision) and generation (faithfulness, relevance, correctness) separately.
- Validate LLM judges against human labels; prefer simple scales.
- Compare configs on quality, latency and cost, and do error analysis on real failures.
""", r"""
1. Generate 50 synthetic questions from your corpus, manually review and fix 20 of them, and add 10 unanswerable and 5 multi-hop questions.
2. Implement retrieval metrics and an LLM faithfulness judge. Hand-label 30 answers as faithful/unfaithful and measure the judge's agreement with you.
3. Run at least three pipeline configurations and produce a results table (recall@5, MRR, faithfulness %, refusal accuracy, avg latency, avg cost).
4. Do error analysis on 20 failures: categorise and count. What's the single biggest fix?
""", [
Q("Faithfulness in RAG evaluation measures:", ["Whether the answer matches the user's opinion", "Whether all claims in the answer are supported by the retrieved context", "Retrieval latency", "How many documents were indexed"], 1, "Faithfulness checks grounding in the provided context."),
Q("Why separate retrieval and generation metrics?", ["It's required by Ragas", "To locate which stage is causing failures", "Generation metrics are free", "Retrieval can't be measured"], 1, "Stage-wise metrics point to the component to fix."),
Q("Before relying on an LLM judge, you should:", ["Use a 1-100 scale", "Check its agreement with human labels on a sample", "Run it at temperature 1.5", "Never show it the context"], 1, "Judges must be validated like any measurement instrument."),
], [
R("Ragas documentation", "https://docs.ragas.io/", "docs"),
R("Hamel Husain - Your AI product needs evals", "https://hamel.dev/blog/posts/evals/", "article"),
R("Jason Liu - Levels of complexity: RAG applications", "https://jxnl.co/writing/2024/02/28/levels-of-complexity-rag-applications/", "article"),
R("DeepLearning.AI - Building and Evaluating Advanced RAG", "https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/", "course"),
]),
]

MODULE = M(
    "m09-rag", 9, "Retrieval-Augmented Generation", "Intermediate", 3,
    "Connect retrieval to generation to build assistants that answer from private, up-to-date knowledge with citations. Go from a hand-built naive RAG pipeline to advanced techniques and rigorous evaluation.",
    [
        "Build a complete RAG pipeline from scratch and with LangChain",
        "Improve retrieval with query rewriting, routing, metadata filters, permissions and reranking",
        "Produce grounded, cited answers and reduce hallucinations",
        "Explain when to use GraphRAG, agentic RAG or long context",
        "Evaluate RAG with retrieval metrics, LLM judges and error analysis",
    ],
    lessons,
    ("Company Knowledge Assistant with Citations", r"""
Build "AskDocs", a production-style RAG assistant over a realistic corpus (e.g. 100+ pages of a public company handbook, open-source project docs, or Indian government scheme FAQs):

1. **Ingestion**: structure-aware chunking with contextual headers, pgvector + full-text index, idempotent re-ingestion.
2. **Query pipeline**: conversational condensation, router (docs vs "no retrieval"), hybrid retrieval, cross-encoder reranking with threshold, token-budgeted context assembly.
3. **Security**: two simulated departments with ACL metadata enforced from a JWT; automated test proving no cross-department leakage.
4. **Generation**: inline citations verified in code; "I don't know" for unanswerable questions; streaming responses.
5. **Evaluation**: 80+ question eval set (incl. unanswerable and multi-hop), report of recall@5, MRR, faithfulness, refusal accuracy, latency and cost for baseline vs final pipeline.
6. **UI**: a minimal chat page showing answers with clickable sources and thumbs up/down feedback stored in the DB.

**Deliverable:** repo + README with architecture diagram, eval results table and an error-analysis section. This is a flagship portfolio project; polish it.
"""),
)
