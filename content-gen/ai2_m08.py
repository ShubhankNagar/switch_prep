from ai2_common import Q, R, L, M

lessons = [
L("m08-what-are-embeddings", "What Embeddings Are and How to Create Them", 45, r"""
## Meaning as a vector

An **embedding** is a fixed-length list of numbers (a vector, e.g. 384 or 1536 floats) that represents the *meaning* of a piece of text. Texts with similar meaning get vectors that point in similar directions, even when they share no words:

- "How do I reset my password?"
- "I forgot my login credentials"

These two have almost no word overlap, yet their embeddings are close. That is what makes **semantic search** possible, and semantic search is the heart of RAG (module 9), recommendation, deduplication, clustering and classification.

### Where embeddings come from

You already met embeddings in module 6: the token embedding table at the bottom of a transformer. **Sentence embedding models** go further: they run a transformer encoder over the whole text and **pool** the token vectors (mean pooling or a special token) into one vector. They are trained with **contrastive learning**: pairs that should match (question and its answer, a title and its paragraph) are pulled together, random non-matching pairs pushed apart. That training objective is why distance in the space reflects semantic relatedness.

Key point: an embedding model is *not* a chat model. It's smaller, faster, cheaper, and outputs a vector instead of text.

### Creating embeddings locally (free)

```python
# pip install sentence-transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-en-v1.5")   # 384-dim, runs on CPU

sentences = [
    "How do I reset my password?",
    "I forgot my login credentials",
    "What is the delivery time to Bhubaneswar?",
]
emb = model.encode(sentences, normalize_embeddings=True)
print(emb.shape)                 # (3, 384)
print(emb @ emb.T)               # cosine similarity matrix (vectors are normalised)
```

You'll see sentence 0 and 1 scoring much higher with each other than with sentence 2.

### Creating embeddings with an API

```python
from openai import OpenAI
client = OpenAI()
r = client.embeddings.create(model="text-embedding-3-small",
                             input=["How do I reset my password?", "Forgot my login"])
vecs = [d.embedding for d in r.data]
print(len(vecs[0]))    # 1536 by default; this model also supports shorter 'dimensions'
```

Other popular options: Voyage AI (recommended by Anthropic, which has no own embedding endpoint), Cohere Embed, Google Gemini embeddings, and open models like BGE, E5, GTE, Nomic and Qwen3-Embedding hosted yourself. The **MTEB leaderboard** on Hugging Face compares them across tasks.

### Choosing an embedding model

| Factor | Why it matters |
|--------|----------------|
| Retrieval quality on *your* data | Leaderboards are a start; test on your own queries |
| Dimensions | More dims = more storage/RAM and slower search. 384-1024 is common |
| Max input length | Many models truncate at 512 tokens; longer text is silently cut |
| Languages | Need Hindi + English? Pick a multilingual model |
| Cost / hosting | API per-token pricing vs running a GPU/CPU yourself |
| Query/document prefixes | Some models (E5, BGE, Nomic) expect prefixes like `"query: "` or an instruction for queries. Read the model card |

**Critical rule:** queries and documents must be embedded with the **same model** (and version). Vectors from different models live in different spaces and can't be compared. Changing models means re-embedding your whole corpus, so store the model name alongside each vector.

### Matryoshka and dimension reduction

Some modern models are trained so the first N dimensions are a usable smaller embedding ("Matryoshka" embeddings). You can truncate 1024-dim vectors to 256 and keep most of the quality while using 4x less storage. Combined with quantisation (store float32 as int8 or even binary), this matters at the scale of millions of chunks.

### What embeddings are bad at

- **Exact matches**: product codes, error numbers, names ("ERR-4041" vs "ERR-4014" look nearly identical). Keyword search handles these better, which is why we'll add hybrid search later.
- **Negation and fine logic**: "flights not via Delhi" may embed close to "flights via Delhi".
- **Domain jargon** unseen in training. Fine-tuning an embedding model on your pairs can help (module 11 ideas apply).

### Visualising the space

```python
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
pts = PCA(n_components=2).fit_transform(emb)
plt.scatter(pts[:, 0], pts[:, 1])
for i, s in enumerate(sentences):
    plt.annotate(s[:25], pts[i])
plt.show()
```

### Key takeaways
- Embeddings map text to vectors where distance approximates meaning.
- Use the same embedding model for queries and documents; record which one.
- Pick a model by testing on your data, considering dims, length limit, language and cost.
- Embeddings struggle with exact identifiers and negation.
""", r"""
1. Embed 30 sentences from three topics (Java, cricket, cooking) with `bge-small-en-v1.5`. Plot them in 2D with PCA and check whether they cluster.
2. Build a tiny "FAQ matcher": 15 FAQ questions with answers; for any user question, return the FAQ with highest cosine similarity. Test with paraphrases.
3. Compare two embedding models (e.g. `all-MiniLM-L6-v2` vs `bge-small-en-v1.5`) on 10 query to correct-FAQ pairs; compute how often the correct one is ranked first.
4. Test failure cases: error codes and negation. Write down what you observe.
""", [
Q("Why must queries and documents use the same embedding model?", ["To save money", "Different models produce vectors in incompatible spaces, so distances are meaningless", "APIs require it", "It's faster"], 1, "Each model learns its own coordinate system."),
Q("How are sentence embedding models usually trained?", ["Next-token prediction only", "Contrastive learning: pull matching pairs together, push non-matching apart", "Reinforcement learning from human feedback", "They are not trained"], 1, "Contrastive objectives make distance reflect semantic similarity."),
Q("Which query is pure embedding search worst at?", ["Paraphrased questions", "Finding the exact error code ERR-4041", "Synonyms", "Cross-lingual meaning"], 1, "Exact identifiers are better served by keyword (lexical) search."),
], [
R("Sentence Transformers documentation", "https://sbert.net/", "docs"),
R("MTEB leaderboard (Hugging Face)", "https://huggingface.co/spaces/mteb/leaderboard", "docs"),
R("OpenAI - Embeddings guide", "https://platform.openai.com/docs/guides/embeddings", "docs"),
R("Vicki Boykis - What are embeddings? (free book)", "https://vickiboykis.com/what_are_embeddings/", "book"),
]),

L("m08-similarity-search", "Similarity Metrics and Brute-Force Search", 35, r"""
## Measuring "closeness"

Given a query vector **q** and document vectors **d**, we need a score. Three metrics dominate:

**Cosine similarity**: the cosine of the angle between vectors, from -1 to 1. Ignores length, cares only about direction.

cos(q, d) = (q . d) / (|q| |d|)

**Dot product (inner product)**: q . d. Equals cosine when vectors are normalised to length 1. Fastest to compute.

**Euclidean (L2) distance**: straight-line distance. Smaller is closer. For normalised vectors, L2 distance and cosine give the **same ranking** (|q - d|^2 = 2 - 2 cos).

```python
import numpy as np
q = np.array([0.2, 0.9, 0.1])
d = np.array([0.25, 0.8, 0.3])
cos = q @ d / (np.linalg.norm(q) * np.linalg.norm(d))
dot = q @ d
l2 = np.linalg.norm(q - d)
print(round(cos, 4), round(dot, 4), round(l2, 4))
```

**Practical rule:** normalise embeddings once at write time and use dot product (or cosine). Check your model card: most sentence models are designed for cosine. Configure your vector DB with the matching metric; a mismatch silently degrades results.

### Brute-force (exact) search

For up to roughly 100k vectors, you don't need a vector database. A matrix multiply is enough and is *exact*:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

docs = [
    "Spring Boot auto-configuration creates beans based on the classpath.",
    "Use @Transactional to wrap a method in a database transaction.",
    "Angular services are singletons provided via dependency injection.",
    "MySQL indexes speed up WHERE clauses on large tables.",
    "Kafka partitions enable parallel consumption.",
]
D = model.encode(docs, normalize_embeddings=True)          # (N, 384)

def search(query, k=3):
    qv = model.encode([query], normalize_embeddings=True)[0]
    scores = D @ qv                                         # (N,)
    top = np.argsort(-scores)[:k]
    return [(round(float(scores[i]), 3), docs[i]) for i in top]

for s, d in search("how to make a query faster in a relational db"):
    print(s, d)
```

`D @ qv` computes N dot products in one vectorised call. With 100k x 384 float32 vectors (about 150 MB), it takes milliseconds on a laptop. Use `np.argpartition` for top-k on large N to avoid a full sort.

### Score interpretation

Similarity scores are **relative, not absolute**. A cosine of 0.6 might be a great match in one model and mediocre in another. Avoid hard-coded thresholds until you've looked at score distributions on your data. When you do need a threshold ("no relevant document, say I don't know"), calibrate it on labelled examples.

### Evaluating retrieval: recall@k and MRR

Before choosing models or indexes, build a small **labelled set**: queries plus the id(s) of the correct document(s). Then:

- **Recall@k / hit rate@k**: fraction of queries where a correct doc appears in the top k.
- **MRR** (mean reciprocal rank): average of 1/rank of the first correct doc. Rewards putting it at position 1.
- **nDCG**: handles graded relevance (very relevant vs somewhat relevant).

```python
def evaluate(queries, gold_ids, k=3):
    hits, rr = 0, 0.0
    for q, gold in zip(queries, gold_ids):
        qv = model.encode([q], normalize_embeddings=True)[0]
        ranked = list(np.argsort(-(D @ qv)))
        if gold in ranked[:k]: hits += 1
        rr += 1 / (ranked.index(gold) + 1)
    return {"recall@k": hits / len(queries), "mrr": rr / len(queries)}

print(evaluate(["db query slow", "consume messages in parallel"], [3, 4]))
```

You will reuse this harness throughout modules 8 and 9: every change (chunk size, model, hybrid, reranker) should move these numbers.

### Key takeaways
- Cosine = direction; dot = cosine on normalised vectors; L2 ranks the same on normalised vectors.
- Normalise once, use the metric your model expects, configure the DB to match.
- Brute force is exact and fine for small corpora; ANN indexes (lesson 5) are for scale.
- Measure retrieval with recall@k and MRR on a labelled set.
""", r"""
1. Implement cosine, dot and L2 yourself and verify that on normalised vectors the top-5 rankings agree.
2. Create 50 short docs about your Spring Boot project (or any tech notes) and 20 labelled queries. Compute recall@1, recall@5 and MRR.
3. Time brute-force search for 10k, 100k and 500k random 384-dim vectors. At what size does it exceed 50 ms?
4. Plot a histogram of similarity scores for relevant vs irrelevant pairs. Where would you put a "no answer" threshold?
""", [
Q("When vectors are L2-normalised, cosine similarity equals:", ["Euclidean distance", "Dot product", "Manhattan distance", "Zero"], 1, "Dividing by norms of 1 leaves just the dot product."),
Q("What does recall@5 measure?", ["Average similarity score", "Fraction of queries whose correct document appears in the top 5 results", "Search latency", "Number of documents"], 1, "It's the hit rate within the top k results."),
Q("Why avoid hard-coding a similarity threshold like 0.8?", ["Thresholds are illegal", "Score scales differ by model and data; calibrate on labelled examples", "Scores are always 1", "It slows search"], 1, "Similarity values are relative to each model's space."),
], [
R("Pinecone Learn - Vector similarity explained", "https://www.pinecone.io/learn/vector-similarity/", "article"),
R("Sentence Transformers - Semantic search", "https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html", "docs"),
R("Weaviate - Distance metrics", "https://weaviate.io/blog/distance-metrics-in-vector-search", "article"),
]),

L("m08-chunking", "Chunking Documents", 40, r"""
## Why chunk?

You can't embed a 200-page PDF as one vector: embedding models truncate long input (often at 512 tokens), and one vector for a whole book averages away all detail. So we split documents into **chunks**, embed each, and retrieve the relevant chunks. Chunking is one of the highest-leverage and most underrated decisions in a RAG system.

The tension:
- **Too small** (one sentence): precise matches, but chunks lack context ("It was fixed in v2" - what was?).
- **Too large** (5 pages): context is there, but the vector is diluted, retrieval is fuzzy, and you waste prompt tokens.

Typical starting point: **200-500 tokens per chunk with 10-20% overlap**, then tune using your retrieval eval.

### Strategy 1: Fixed-size with overlap

```python
def chunk_fixed(text, size=800, overlap=100):        # characters
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

Simple and predictable but cuts sentences and tables in half.

### Strategy 2: Recursive character splitting

Try to split on the biggest natural boundary first (paragraphs), then lines, then sentences, then words, until each piece fits. This is the default in LangChain and a strong baseline:

```python
# pip install langchain-text-splitters
from langchain_text_splitters import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""])
chunks = splitter.split_text(long_text)
```

You can measure size in tokens instead of characters with `RecursiveCharacterTextSplitter.from_tiktoken_encoder(...)`.

### Strategy 3: Structure-aware

Real documents have structure; use it.
- **Markdown/HTML**: split by headings and keep the heading path as metadata ("Installation > Linux > Ubuntu").
- **Code**: split by class/function (language-aware splitters exist for Java, Python, etc.).
- **PDFs**: extraction is the hard part. Tools like `pymupdf`, `unstructured`, `docling` or LlamaParse recover headings, tables and reading order. Garbage extraction means garbage retrieval.
- **Tables**: keep a table together, or convert rows to sentences ("Plan Gold: price 999 INR, 50GB").

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter
md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")])
docs = md_splitter.split_text(markdown_text)
for d in docs[:3]:
    print(d.metadata, d.page_content[:80])
```

### Strategy 4: Semantic chunking

Embed each sentence, and start a new chunk where similarity between consecutive sentences drops sharply (a topic change). More expensive, sometimes better for unstructured prose; benchmark before adopting.

### Make chunks self-contained: contextual enrichment

A chunk like "Revenue grew 3% over the previous quarter" is useless without knowing *which company and quarter*. Fixes:
1. **Prepend metadata**: document title + section heading to every chunk before embedding.
2. **Contextual retrieval**: use an LLM to write a 1-2 sentence context for each chunk ("This chunk is from ACME's Q2 2025 report, section on revenue") and prepend it. Anthropic reported this substantially reduces retrieval failures, especially combined with BM25 and reranking. Prompt caching makes it affordable since the full document is the shared prefix.

```python
def enrich(chunk, doc_title, heading):
    return f"Document: {doc_title}\nSection: {heading}\n\n{chunk}"
```

### Parent-child (small-to-big) retrieval

Embed **small** chunks for precise matching, but when one matches, send its **parent** (the surrounding section) to the LLM for context. LlamaIndex and LangChain both provide this pattern. It decouples "unit of retrieval" from "unit of context".

### Always keep metadata

Every chunk should carry: `doc_id`, `source` (URL/file), `title`, `section`, `page`, `chunk_index`, `created_at`, access-control info (`tenant_id`, `allowed_roles`), and the embedding model name. You'll need these for filtering, citations and permissions (module 9).

```python
records = [{
    "id": f"{doc_id}-{i}",
    "text": enrich(c, title, heading),
    "metadata": {"doc_id": doc_id, "source": url, "chunk_index": i,
                 "tenant_id": tenant, "embed_model": "bge-small-en-v1.5"},
} for i, c in enumerate(chunks)]
```

### Key takeaways
- Chunk size is a precision vs context trade-off; start at 200-500 tokens with overlap and tune with evals.
- Respect document structure; good PDF/HTML extraction matters as much as the splitter.
- Make chunks self-contained with titles, headings or LLM-generated context.
- Store rich metadata with every chunk.
""", r"""
1. Take 3 long Markdown docs (e.g. Spring Boot reference pages saved as markdown). Chunk them three ways: fixed 500 chars, recursive 1000/150, and header-based.
2. Write 15 questions with the known answer location. Using your recall@k harness from the previous lesson, compare the three strategies.
3. Add title + heading prefixes to chunks and re-measure. Did recall change?
4. Stretch: implement parent-child retrieval: embed 200-token children, return the 1000-token parent.
""", [
Q("What is the main problem with very large chunks?", ["They can't be stored", "One vector dilutes many topics, making retrieval imprecise and wasting tokens", "They are always more accurate", "Overlap becomes impossible"], 1, "Big chunks average away specific meaning."),
Q("What does recursive character splitting do?", ["Splits at a random position", "Tries to split on larger natural boundaries (paragraphs, lines, sentences) before smaller ones", "Embeds each character", "Summarises the document"], 1, "It preserves natural boundaries while respecting the size limit."),
Q("What problem does contextual enrichment of chunks solve?", ["Chunks that lack context like which company or section they come from", "Slow embedding", "High storage cost", "Tokenizer errors"], 0, "Prepending context makes each chunk understandable on its own."),
], [
R("Anthropic - Introducing Contextual Retrieval", "https://www.anthropic.com/news/contextual-retrieval", "article"),
R("LangChain - Text splitters", "https://python.langchain.com/docs/concepts/text_splitters/", "docs"),
R("Pinecone - Chunking strategies for LLM applications", "https://www.pinecone.io/learn/chunking-strategies/", "article"),
R("Docling - document conversion toolkit", "https://github.com/docling-project/docling", "docs"),
]),

L("m08-vector-databases", "Vector Databases: pgvector, Qdrant and Chroma", 50, r"""
## What a vector database adds

A vector DB stores vectors plus metadata and answers "give me the k nearest vectors to this one, optionally filtered by metadata", fast, at scale, with persistence, updates and access control. Think of it as a database whose main index type is "nearest neighbour".

Landscape (2026):
- **pgvector**: a PostgreSQL extension. Vectors live next to your relational data, with SQL, transactions and joins. Excellent default for teams already on Postgres, up to many millions of vectors.
- **Qdrant**, **Weaviate**, **Milvus**: dedicated open-source vector DBs with rich filtering, quantisation, distributed scaling. Qdrant is written in Rust and popular for its filtering performance.
- **Pinecone**: fully managed serverless SaaS.
- **Chroma**: lightweight, embedded, great for prototypes and notebooks.
- Search engines (**Elasticsearch/OpenSearch**) and many databases (MongoDB Atlas, Redis, MySQL HeatWave, Oracle) now support vectors too.

For a Java/MySQL developer: **start with pgvector** unless you have a reason not to. One fewer system to operate.

### Chroma: prototype in 10 lines

```python
# pip install chromadb
import chromadb
from chromadb.utils import embedding_functions

ef = embedding_functions.SentenceTransformerEmbeddingFunction("BAAI/bge-small-en-v1.5")
client = chromadb.PersistentClient(path="./chroma_db")
col = client.get_or_create_collection("docs", embedding_function=ef,
                                      metadata={"hnsw:space": "cosine"})
col.add(ids=["1", "2"],
        documents=["Use @Transactional for DB transactions", "Kafka partitions scale consumers"],
        metadatas=[{"topic": "spring"}, {"topic": "kafka"}])
res = col.query(query_texts=["how do I roll back on error?"], n_results=1,
                where={"topic": "spring"})
print(res["documents"], res["distances"])
```

### pgvector: vectors in SQL

```sql
-- docker run -e POSTGRES_PASSWORD=pw -p 5432:5432 pgvector/pgvector:pg17
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE chunks (
  id          bigserial PRIMARY KEY,
  doc_id      text NOT NULL,
  tenant_id   text NOT NULL,
  content     text NOT NULL,
  embedding   vector(384) NOT NULL
);
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON chunks (tenant_id);
```

Operators: `<=>` cosine distance, `<->` L2 distance, `<#>` negative inner product.

```python
# pip install psycopg[binary] pgvector
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
conn = psycopg.connect("postgresql://postgres:pw@localhost:5432/postgres", autocommit=True)
register_vector(conn)

def add(doc_id, tenant, text):
    v = model.encode(text, normalize_embeddings=True)
    conn.execute("INSERT INTO chunks (doc_id, tenant_id, content, embedding) VALUES (%s,%s,%s,%s)",
                 (doc_id, tenant, text, v))

def search(query, tenant, k=5):
    v = model.encode(query, normalize_embeddings=True)
    return conn.execute(
        '''SELECT doc_id, content, 1 - (embedding <=> %s) AS score
           FROM chunks WHERE tenant_id = %s
           ORDER BY embedding <=> %s LIMIT %s''',
        (v, tenant, v, k)).fetchall()
```

Because it's Postgres, you get joins ("only chunks from documents the user can access"), backups, replication and transactions for free.

### Qdrant: dedicated engine

```python
# docker run -p 6333:6333 qdrant/qdrant ; pip install qdrant-client
from qdrant_client import QdrantClient, models
qc = QdrantClient("http://localhost:6333")
qc.create_collection("docs", vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))
qc.upsert("docs", points=[
    models.PointStruct(id=1, vector=model.encode("Use @Transactional").tolist(),
                       payload={"topic": "spring", "tenant_id": "acme"})])
hits = qc.query_points("docs", query=model.encode("rollback on error").tolist(), limit=3,
    query_filter=models.Filter(must=[models.FieldCondition(key="tenant_id",
                                     match=models.MatchValue(value="acme"))])).points
for h in hits: print(h.score, h.payload)
```

### Choosing: questions to ask

| Question | Leaning |
|----------|---------|
| Already on Postgres, < tens of millions of vectors? | pgvector |
| Heavy filtering, multi-tenancy, very large scale, quantisation? | Qdrant / Milvus / Weaviate |
| No ops team, want managed? | Pinecone, or managed Qdrant/Weaviate, cloud Postgres with pgvector |
| Notebook prototype? | Chroma or in-memory numpy |
| Need strong keyword search too? | Elasticsearch/OpenSearch, or a DB with built-in hybrid |

### Operational concerns
- **Upserts and deletes**: when a source doc changes, delete its old chunks by `doc_id` and re-insert. Keep a content hash to skip unchanged docs.
- **Multi-tenancy**: filter by tenant on every query (enforced in code, not by the LLM). Some DBs offer per-tenant collections or partitions.
- **Re-embedding**: model upgrades require reindexing; plan a blue-green collection swap.
- **Backups and monitoring**: like any DB.

### Key takeaways
- Vector DBs = nearest-neighbour index + metadata filters + persistence.
- pgvector is the pragmatic default for Postgres shops; dedicated engines shine at scale and heavy filtering.
- Always store and filter on metadata like tenant and doc id; plan for updates and re-embedding.
""", r"""
1. Run pgvector in Docker. Create the `chunks` table and load 200+ chunks from the previous lesson's docs.
2. Implement `search(query, tenant, k)` and verify tenant filtering by loading the same docs under two tenants with different content.
3. Load the same chunks into Chroma or Qdrant and compare results and latency for 20 queries.
4. Implement idempotent ingestion: store a SHA-256 of each document; re-running ingestion should skip unchanged docs and replace changed ones.
""", [
Q("Which pgvector operator returns cosine distance?", ["<->", "<=>", "<#>", "@@"], 1, "<=> is cosine distance, <-> is L2, <#> is negative inner product."),
Q("A strong reason to choose pgvector for a Spring Boot + Postgres team is:", ["It's the only vector DB", "Vectors live with relational data, so you get SQL joins, transactions and existing ops", "It doesn't need indexes", "It's always fastest at billions of vectors"], 1, "Avoiding a new system and joining with existing data is a big operational win."),
Q("How should multi-tenant isolation be enforced in vector search?", ["Ask the LLM to ignore other tenants' data", "Apply a tenant filter in the query from application code on every search", "Use a bigger embedding model", "Shuffle results"], 1, "Access control must be enforced deterministically in code/DB."),
], [
R("pgvector GitHub README", "https://github.com/pgvector/pgvector", "docs"),
R("Qdrant documentation - Quickstart", "https://qdrant.tech/documentation/quickstart/", "docs"),
R("Chroma documentation", "https://docs.trychroma.com/", "docs"),
R("DeepLearning.AI - Vector Databases: from Embeddings to Applications", "https://www.deeplearning.ai/short-courses/vector-databases-embeddings-applications/", "course"),
]),

L("m08-ann-indexes", "Approximate Nearest Neighbour Indexes (HNSW, IVF, PQ)", 40, r"""
## Why approximate?

Exact search compares the query with every vector: O(N x d). At 50 million vectors of 1024 dims that's 50 billion multiply-adds per query - too slow for an interactive app. **Approximate nearest neighbour (ANN)** indexes trade a little accuracy (recall) for orders-of-magnitude speed. You'll be asked about this in interviews.

The key metric is **recall@k vs exact search**: of the true top-10 neighbours, how many did the index return? Good configs get 0.95-0.99 recall at a tiny fraction of the cost.

### HNSW: Hierarchical Navigable Small World

The most widely used ANN index (pgvector, Qdrant, Weaviate, Elasticsearch, Chroma all support it).

Intuition: a **multi-layer graph**, like a skip list for vectors.
- Every vector is a node connected to its M nearest neighbours.
- Upper layers contain fewer nodes with long-range links (motorways); the bottom layer contains all nodes with short links (local streets).
- **Search**: start at the top layer's entry point, greedily move to the neighbour closest to the query until no improvement, drop a layer, repeat. At the bottom, keep a candidate list of size `ef_search` to explore more thoroughly.

Parameters:

| Param | Effect |
|-------|--------|
| `M` (links per node, e.g. 16) | Higher = better recall, more memory, slower build |
| `ef_construction` (e.g. 64-200) | Build-time candidate list; higher = better graph, slower build |
| `ef_search` (e.g. 40-200) | Query-time candidate list; **the main recall vs latency knob** |

Pros: excellent recall/latency, supports incremental inserts. Cons: memory hungry (the graph plus full vectors usually in RAM), deletes are awkward, builds are slow on huge sets.

```sql
-- pgvector
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
SET hnsw.ef_search = 100;   -- per session/transaction
```

### IVF: Inverted File Index

- Run k-means to create `nlist` clusters (centroids).
- Each vector is stored in its nearest cluster's list.
- At query time, find the `nprobe` closest centroids and search only those lists.

`nprobe` is the recall vs speed knob. IVF builds faster and uses less memory than HNSW but needs training data (build after loading data) and recall drops if clusters drift. pgvector calls it `ivfflat`:

```sql
CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);
SET ivfflat.probes = 10;
```

### Product Quantization (PQ) and other compression

To cut memory, compress vectors:
- **Scalar quantisation**: float32 to int8 (4x smaller) with small quality loss.
- **Binary quantisation**: 1 bit per dimension (32x smaller), then re-score the top candidates with full vectors. Works well with high-dim modern models.
- **Product quantisation**: split each vector into m sub-vectors, replace each with the id of the nearest of 256 sub-centroids. A 1024-dim float vector (4 KB) becomes e.g. 64 bytes. Common combo: IVF-PQ (FAISS).

### Experiment with FAISS

```python
# pip install faiss-cpu
import faiss, numpy as np, time
d, N = 384, 200_000
xb = np.random.randn(N, d).astype("float32"); faiss.normalize_L2(xb)
xq = np.random.randn(100, d).astype("float32"); faiss.normalize_L2(xq)

flat = faiss.IndexFlatIP(d); flat.add(xb)
_, gt = flat.search(xq, 10)                         # exact ground truth

hnsw = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
hnsw.hnsw.efConstruction = 64; hnsw.add(xb)
for ef in (16, 64, 256):
    hnsw.hnsw.efSearch = ef
    t = time.perf_counter(); _, I = hnsw.search(xq, 10); dt = time.perf_counter() - t
    recall = np.mean([len(set(I[i]) & set(gt[i])) / 10 for i in range(len(xq))])
    print(f"ef={ef} recall@10={recall:.3f} {dt*10:.2f} ms/query")
```

You'll see recall climb and latency rise as `ef_search` grows: the fundamental trade-off.

### Filtering and ANN

Filters ("tenant = acme") interact badly with naive ANN: if you search top-10 then filter, you may end with 0 results (**post-filtering**). Pre-filtering with a brute-force scan is exact but slow for broad filters. Modern engines (Qdrant, Weaviate, newer pgvector with iterative scans) integrate filters into graph traversal. Test your real filter selectivity.

### When not to bother

Under ~100k vectors, exact search (or pgvector without an index) is often fast enough and has perfect recall. Add ANN when latency demands it.

### Key takeaways
- ANN trades a bit of recall for big speed gains; measure recall against exact search.
- HNSW: layered graph, tune `ef_search` at query time; memory heavy.
- IVF: clusters + `nprobe`; quantisation (scalar, binary, PQ) shrinks memory.
- Filters + ANN need care; test with realistic filters.
""", r"""
1. Run the FAISS experiment with N = 200k and plot recall@10 vs latency for efSearch in [8, 16, 32, 64, 128, 256].
2. Build an IVF index (`faiss.IndexIVFFlat`) with nlist=1024 and plot recall vs nprobe.
3. In pgvector, load 100k random vectors, compare query plans (`EXPLAIN ANALYZE`) with and without an HNSW index.
4. Write a one-paragraph interview answer: "Explain HNSW and how you'd tune it."
""", [
Q("In HNSW, which parameter is the main query-time recall vs latency knob?", ["M", "ef_construction", "ef_search", "nlist"], 2, "ef_search sets the size of the candidate list during search."),
Q("How does an IVF index speed up search?", ["By using GPUs only", "Clustering vectors and searching only the nprobe nearest clusters", "Removing metadata", "Sorting vectors alphabetically"], 1, "It limits comparisons to a few clusters."),
Q("What is the risk of post-filtering ANN results by tenant?", ["Higher recall", "You may get far fewer than k results (even zero) after filtering", "It's illegal", "Vectors get corrupted"], 1, "The top-k may contain no rows matching the filter."),
], [
R("Pinecone Learn - HNSW explained", "https://www.pinecone.io/learn/series/faiss/hnsw/", "article"),
R("FAISS wiki - Getting started", "https://github.com/facebookresearch/faiss/wiki/Getting-started", "docs"),
R("HNSW original paper (Malkov & Yashunin)", "https://arxiv.org/abs/1603.09320", "article"),
R("Qdrant - Vector quantization guide", "https://qdrant.tech/documentation/guides/quantization/", "docs"),
]),

L("m08-hybrid-search", "Keyword Search, BM25 and Hybrid Search", 40, r"""
## Lexical search is not dead

Embedding search finds *meaning*; keyword search finds *exact terms*. Real users search for both: "refund policy" (semantic) and "ERR_CONN_4041" or "Order A-99812" (exact). The production standard in 2026 is **hybrid search**: run both and fuse the results.

### BM25 in one page

BM25 is the classic ranking function behind Lucene, Elasticsearch and OpenSearch. For a query with terms t, a document's score sums over terms:

score(D, Q) = sum over t of IDF(t) x [ f(t,D) x (k1 + 1) ] / [ f(t,D) + k1 x (1 - b + b x |D| / avgdl) ]

- **f(t, D)**: how often the term appears in the doc (more is better, but with diminishing returns controlled by `k1`, about 1.2-2.0).
- **IDF(t)**: rare terms matter more ("pgvector" beats "the").
- **Length normalisation** `b` (about 0.75): long docs don't win just by being long.

It's fast (inverted index), needs no GPU, handles exact identifiers perfectly and is highly interpretable. It fails on synonyms and paraphrases ("car" vs "automobile").

```python
# pip install rank-bm25
from rank_bm25 import BM25Okapi
import re
docs = ["Use @Transactional to roll back on RuntimeException",
        "Error ERR_CONN_4041 means the database pool is exhausted",
        "HikariCP is the default connection pool in Spring Boot"]
tok = lambda s: re.findall(r"\w+", s.lower())
bm25 = BM25Okapi([tok(d) for d in docs])
print(bm25.get_scores(tok("ERR_CONN_4041")))   # doc 1 wins decisively
```

### Hybrid: combine lexical + semantic

Run both retrievers, then **fuse**. Scores from BM25 (unbounded) and cosine (-1 to 1) aren't comparable, so the most robust fusion uses only ranks: **Reciprocal Rank Fusion (RRF)**.

RRF_score(d) = sum over retrievers of 1 / (k + rank_r(d)), with k typically 60.

```python
def rrf(result_lists, k=60):
    scores = {}
    for results in result_lists:            # each is a list of doc ids, best first
        for rank, doc_id in enumerate(results, start=1):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)

bm25_ids = ["d7", "d2", "d9", "d4"]
vector_ids = ["d2", "d5", "d7", "d1"]
print(rrf([bm25_ids, vector_ids]))          # d2 and d7 rise to the top
```

Alternative: normalise each score list to 0-1 and take a weighted sum (alpha x vector + (1 - alpha) x bm25). Needs tuning; RRF is a great default.

### Hybrid in Postgres

Postgres has full-text search (`tsvector`, `ts_rank`). Combine it with pgvector in one SQL query using RRF:

```sql
WITH semantic AS (
  SELECT id, row_number() OVER (ORDER BY embedding <=> :qvec) AS r
  FROM chunks ORDER BY embedding <=> :qvec LIMIT 50),
keyword AS (
  SELECT id, row_number() OVER (ORDER BY ts_rank(tsv, q) DESC) AS r
  FROM chunks, plainto_tsquery('english', :qtext) q
  WHERE tsv @@ q ORDER BY ts_rank(tsv, q) DESC LIMIT 50)
SELECT coalesce(s.id, k.id) AS id,
       coalesce(1.0/(60+s.r), 0) + coalesce(1.0/(60+k.r), 0) AS rrf
FROM semantic s FULL OUTER JOIN keyword k ON s.id = k.id
ORDER BY rrf DESC LIMIT 10;
```

(`tsv` is a generated `tsvector` column with a GIN index.) Many vector DBs (Qdrant, Weaviate, Elasticsearch, OpenSearch, Pinecone) offer hybrid queries natively, often via sparse vectors.

### Sparse vectors and learned sparse retrieval

BM25 can be seen as a **sparse vector** (one dimension per vocabulary word, mostly zeros). Learned sparse models like **SPLADE** expand queries/documents with related terms while staying sparse and fast. Some vector DBs store dense + sparse vectors together for hybrid queries.

### When does hybrid help most?
- Queries with identifiers, codes, names, acronyms.
- Domain-specific vocabulary poorly covered by the embedding model.
- Short keyword-style queries.

Anthropic's contextual retrieval experiments, and many public benchmarks, show embeddings + BM25 beating either alone. But always confirm on your eval set.

### Key takeaways
- BM25 excels at exact terms and rare words; embeddings at meaning. Combine them.
- Fuse with Reciprocal Rank Fusion: rank-based, no score calibration needed.
- Postgres can do hybrid in SQL (tsvector + pgvector); many vector DBs support it natively.
""", r"""
1. Add a generated `tsvector` column and GIN index to your pgvector `chunks` table.
2. Implement three retrievers: BM25/full-text only, vector only, hybrid with RRF.
3. Extend your eval set with 10 queries containing exact identifiers (class names, error codes, config keys). Compare recall@5 for the three retrievers on both query types.
4. Try weighted-sum fusion with alpha in {0.3, 0.5, 0.7} and compare with RRF.
""", [
Q("Which query is BM25 likely to handle better than dense embeddings?", ["'how do I make my app faster'", "'ERR_CONN_4041'", "'synonym for happy'", "'explain like I'm five'"], 1, "Exact rare tokens get high IDF weight in BM25."),
Q("Why is Reciprocal Rank Fusion popular for hybrid search?", ["It uses GPUs", "It uses only ranks, so incomparable score scales don't need normalising", "It's the only way to combine results", "It removes duplicates automatically from the DB"], 1, "RRF avoids calibrating BM25 vs cosine scores."),
Q("What does IDF in BM25 capture?", ["Document length", "How rare a term is across the corpus", "Embedding dimension", "Query latency"], 1, "Rare terms are more informative and get higher weight."),
], [
R("Elastic - Practical BM25 (how scoring works)", "https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables", "article"),
R("Weaviate - Hybrid search explained", "https://weaviate.io/blog/hybrid-search-explained", "article"),
R("PostgreSQL - Full text search docs", "https://www.postgresql.org/docs/current/textsearch.html", "docs"),
R("Qdrant - Hybrid queries", "https://qdrant.tech/documentation/concepts/hybrid-queries/", "docs"),
]),

L("m08-reranking", "Reranking with Cross-Encoders", 35, r"""
## Two-stage retrieval

Embedding search uses a **bi-encoder**: query and document are embedded *separately*, then compared. That's what makes it fast (documents are embedded once, offline), but the model never sees the query and document together, so it misses fine-grained relevance.

A **cross-encoder (reranker)** takes the *pair* (query, document) as one input and outputs a relevance score. Every query token can attend to every document token, so it's far more accurate, but you must run it for every candidate at query time, so it's too slow for millions of docs.

The standard pattern combines both:

1. **Retrieve** a broad set cheaply: top 50-100 candidates via hybrid search (high recall).
2. **Rerank** those candidates with a cross-encoder (high precision).
3. Send the top 3-8 to the LLM.

```
query -> [hybrid retrieval: 100 candidates, ~20 ms] -> [cross-encoder rerank: top 5, ~100-300 ms] -> LLM
```

### Reranking locally

```python
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-base")          # or "cross-encoder/ms-marco-MiniLM-L-6-v2"

query = "How do I roll back a transaction when an exception occurs?"
candidates = [
    "Kafka transactions guarantee exactly-once delivery.",
    "By default, Spring rolls back on unchecked exceptions in @Transactional methods; use rollbackFor for checked ones.",
    "MySQL InnoDB supports ACID transactions.",
    "Angular HttpClient returns Observables.",
]
scores = reranker.predict([(query, c) for c in candidates])
for s, c in sorted(zip(scores, candidates), reverse=True):
    print(round(float(s), 3), c[:70])
```

### Reranking via API

Hosted rerankers (Cohere Rerank, Voyage rerank, Jina) need no GPU:

```python
import cohere
co = cohere.ClientV2()
r = co.rerank(model="rerank-v3.5", query=query, documents=candidates, top_n=3)
for item in r.results:
    print(item.relevance_score, candidates[item.index][:60])
```

### LLM as reranker

You can also ask an LLM to score or order candidates ("Rate relevance 0-3 for each passage"). Flexible (can follow custom relevance rules), but slower and costlier; useful for small candidate sets or offline evaluation.

### Putting the pipeline together

```python
def retrieve(query, k_candidates=50, k_final=5):
    candidates = hybrid_search(query, k=k_candidates)        # from previous lesson
    pairs = [(query, c["text"]) for c in candidates]
    scores = reranker.predict(pairs, batch_size=32)
    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    return [c for s, c in ranked[:k_final]]
```

### Tuning and costs
- **Candidate count**: more candidates = higher chance the right doc is present, but more reranking latency. Measure recall@50 of stage 1; if the right doc isn't in the candidates, no reranker can save you.
- **Latency**: cross-encoders cost roughly linear in candidates x length. Truncate passages, batch on GPU, or use a small reranker.
- **Thresholding**: reranker scores are better calibrated than cosine; you can drop candidates below a score to avoid sending irrelevant context (and say "I don't know").
- **Diversity**: if top results are near-duplicates, apply MMR (maximal marginal relevance) to pick relevant but different chunks.

### Measuring the gain

Compare MRR and recall@5 before/after reranking on your labelled set. It's common to see a big improvement in *precision at the top*, which is exactly what matters because the LLM only sees the top few chunks.

### Key takeaways
- Bi-encoders: fast, independent embeddings, good recall. Cross-encoders: joint scoring, high precision, slow.
- Retrieve many cheaply, rerank few precisely, send the best to the LLM.
- Stage-1 recall caps the whole system; measure both stages.
""", r"""
1. Add a cross-encoder reranking stage to your hybrid retriever.
2. On your eval set, report recall@5 and MRR for: vector only, hybrid, hybrid + rerank. Put the numbers in a table.
3. Measure latency for reranking 20, 50 and 100 candidates on CPU. Choose a candidate count that keeps p95 under 500 ms.
4. Implement MMR on the reranked list and inspect whether results become more diverse.
""", [
Q("What distinguishes a cross-encoder from a bi-encoder?", ["Cross-encoders are smaller", "A cross-encoder scores the query and document together in one forward pass", "Bi-encoders can't be used for search", "Cross-encoders produce embeddings stored in the DB"], 1, "Joint encoding allows full attention between query and document tokens."),
Q("Why not use a cross-encoder over the whole corpus?", ["It's inaccurate", "It must run once per (query, document) pair at query time, too slow for millions of docs", "It needs labelled data", "It only works for English"], 1, "No precomputation is possible for pairs."),
Q("Your reranker isn't improving results. Stage-1 recall@50 is 40%. What's the real issue?", ["Reranker model too small", "The correct documents are often not in the candidate set, so retrieval must improve first", "Temperature too high", "Too many tokens in the prompt"], 1, "A reranker can only reorder what it's given."),
], [
R("Sentence Transformers - Cross-encoders / retrieve & re-rank", "https://sbert.net/examples/cross_encoder/applications/README.html", "docs"),
R("Cohere - Rerank overview", "https://docs.cohere.com/docs/rerank-overview", "docs"),
R("Pinecone Learn - Rerankers and two-stage retrieval", "https://www.pinecone.io/learn/series/rag/rerankers/", "article"),
]),
]

MODULE = M(
    "m08-embeddings-vectordb", 8, "Embeddings & Vector Databases", "Intermediate", 2,
    "Understand how embeddings turn text into vectors that capture meaning, and how to search them efficiently. Build a production-grade retrieval layer with chunking, pgvector/Qdrant, ANN indexes, hybrid BM25 search and reranking.",
    [
        "Generate and compare embeddings from open and hosted models",
        "Chunk real documents with metadata and contextual enrichment",
        "Store and query vectors in pgvector, Qdrant and Chroma with metadata filters",
        "Explain and tune HNSW/IVF indexes and quantisation",
        "Implement hybrid search with RRF and cross-encoder reranking, measured with recall@k and MRR",
    ],
    lessons,
    ("Semantic Search Engine for Engineering Docs", r"""
Build a search service over a real corpus (e.g. Spring Boot + Angular docs, or your own team's wiki exported as Markdown):

1. **Ingestion pipeline**: load Markdown/PDF, structure-aware chunking with title/heading prefixes, content hashing for incremental updates.
2. **Storage**: Postgres + pgvector with an HNSW index, a full-text `tsvector` column, and `tenant_id`/`source` metadata.
3. **Retrieval API** (FastAPI): `/search?q=&k=` supporting `mode=vector|keyword|hybrid|hybrid_rerank`.
4. **Evaluation**: a labelled set of at least 40 queries (including exact-identifier queries) and a script printing recall@1/5, MRR and p50/p95 latency for each mode.
5. **README** with your results table and a short write-up of which choices mattered most.

**Stretch:** try two embedding models and binary quantisation in Qdrant; report quality vs memory.
"""),
)
