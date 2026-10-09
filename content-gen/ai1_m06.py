from ai1_common import L, Q, R, M

lessons = []

lessons.append(L("m06-l1-tokenization", "Tokenization: How Models Read Text", 45, r"""
## Models only see numbers

A neural network can't read "Hello". Text must become a sequence of integers. **Tokenization** splits text into units called **tokens** and maps each to an ID in a fixed **vocabulary**. Tokens are the currency of LLMs: context windows, API pricing and rate limits are all measured in tokens, so an AI engineer must understand them.

## Three approaches

### Word-level

Split on spaces: `"I love AI" -> ["I", "love", "AI"]`. Problems: huge vocabularies (every form of every word: run, runs, running), and unknown words at inference time (`[UNK]`) — new names, typos, code.

### Character-level

`"love" -> ["l", "o", "v", "e"]`. Tiny vocabulary, no unknowns — but sequences get very long and each token carries little meaning, so models must work harder.

### Subword-level (what modern models use)

Common words stay whole; rare words split into meaningful pieces: `"unbelievably" -> ["un", "believ", "ably"]`. Best of both worlds: a manageable vocabulary (30k-200k), no unknown words, and reasonable sequence lengths.

## Byte-Pair Encoding (BPE)

BPE, used by GPT models, Llama and many others, **learns** its vocabulary from data:

1. Start with individual characters (or bytes) as the vocabulary.
2. Count every adjacent pair of tokens in the training corpus.
3. Merge the most frequent pair into a new token; add it to the vocabulary.
4. Repeat until the vocabulary reaches the target size.

```python
from collections import Counter

def get_pair_counts(words):
    counts = Counter()
    for word, freq in words.items():
        symbols = word.split()
        for a, b in zip(symbols, symbols[1:]):
            counts[(a, b)] += freq
    return counts

def merge(words, pair):
    a, b = pair
    return {w.replace(f"{a} {b}", f"{a}{b}"): f for w, f in words.items()}

# corpus: word (as space-separated characters) -> frequency
words = {"l o w": 5, "l o w e r": 2, "n e w e s t": 6, "w i d e s t": 3}
for step in range(5):
    pair = get_pair_counts(words).most_common(1)[0][0]
    words = merge(words, pair)
    print(f"merge {step + 1}: {pair} -> {words}")
```

After a few merges, frequent sequences like `es`, `est` and `low` become single tokens. Byte-level BPE starts from the 256 possible bytes, so any text — emoji, Hindi, code — can be encoded without unknowns.

Related algorithms: **WordPiece** (BERT) and **Unigram/SentencePiece** (T5, many multilingual models) — same idea, different merge criteria.

## Using real tokenizers

### tiktoken (OpenAI's tokenizers)

```python
import tiktoken

enc = tiktoken.get_encoding("o200k_base")       # used by recent OpenAI models
ids = enc.encode("Raj is learning transformers!")
print(ids)                                      # list of integers
print(len(ids), "tokens")
print([enc.decode([i]) for i in ids])           # see each token's text
print(enc.decode(ids))                          # round-trip back to text
```

### Hugging Face tokenizers

```python
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("bert-base-uncased")
enc = tok("Tokenization is fascinating!", return_tensors="pt")
print(enc["input_ids"])
print(tok.convert_ids_to_tokens(enc["input_ids"][0]))
# ['[CLS]', 'token', '##ization', 'is', 'fascinating', '!', '[SEP]']
```

`##` marks a WordPiece continuation. `[CLS]` and `[SEP]` are **special tokens** BERT expects. Chat LLMs have special tokens too, marking where system, user and assistant messages begin and end.

### Batches: padding, truncation, attention masks

```python
batch = tok(["Short text.", "A much longer piece of text that goes on."],
            padding=True, truncation=True, max_length=16, return_tensors="pt")
print(batch["input_ids"].shape)       # (2, length_of_longest)
print(batch["attention_mask"])        # 1 = real token, 0 = padding to ignore
```

## Why tokenization matters to an AI engineer

- **Cost and limits:** APIs charge per input/output token; a context window of 200k tokens is roughly 150k English words. Rule of thumb: 1 token is about 4 characters or 0.75 words in English.
- **Languages:** non-English text, including Hindi, often needs more tokens per word — higher cost and less effective context.
- **Quirks:** many odd LLM behaviours come from tokenization — difficulty counting letters in a word ("strawberry"), reversing strings, or arithmetic on long numbers, because the model sees chunks, not characters.
- **Chunking for RAG:** documents are split into chunks measured in tokens to fit embedding models and context windows.
- **Matching:** always use the tokenizer that matches the model — IDs mean nothing to a different model.

```python
def estimate_cost(text, price_per_million=3.0):
    n = len(tiktoken.get_encoding("o200k_base").encode(text))
    return n, n / 1_000_000 * price_per_million     # (tokens, dollars)
```

(Prices vary by provider and model; always check the current pricing page.)

## From IDs to vectors

Token IDs are just indices. The model's first layer is an **embedding table** of shape `(vocab_size, d_model)`; each ID selects one row — a learned vector. That's where meaning starts to live, and it's the topic of the next lesson.

```python
import torch
embedding = torch.nn.Embedding(num_embeddings=50_000, embedding_dim=768)
vectors = embedding(torch.tensor([[464, 3290, 318]]))
print(vectors.shape)                  # torch.Size([1, 3, 768])
```

## Key takeaways

- Tokenization maps text to integer IDs from a fixed vocabulary; modern models use subword tokenizers (BPE, WordPiece, SentencePiece).
- BPE repeatedly merges the most frequent adjacent pairs; byte-level BPE never hits unknown tokens.
- Tokens drive cost, context limits and some surprising LLM failures.
- Always use the model's own tokenizer; padding + attention masks enable batching.
""", r"""
**Task: Tokenizer explorer.**

1. Extend the BPE code to train on a paragraph of real text (e.g. a Wikipedia intro) for 50 merges, and write `encode(word)` that applies the learned merges in order.
2. With tiktoken, compare token counts for the same sentence in English, Hindi and a snippet of Java code. Compute tokens-per-word for each.
3. With Hugging Face, tokenize the same sentence with `bert-base-uncased`, `gpt2` and `t5-small`. Print the tokens and explain the differences (special tokens, `##`, `G`-prefixed spaces).
4. Show why an LLM might struggle to count the r's in "strawberry" by printing its tokens.
5. Write a function that splits a long document into chunks of at most 500 tokens with 50-token overlap.
""", [
    Q("Why do modern LLMs use subword tokenization instead of whole words?", ["It is the only method computers support", "It balances vocabulary size with sequence length and avoids unknown words", "It makes models multilingual automatically", "It removes the need for embeddings"], 1, "Subwords keep frequent words whole and split rare ones into pieces, so the vocabulary stays manageable and no word is out-of-vocabulary."),
    Q("What does each BPE training step do?", ["Splits words into characters", "Merges the most frequent adjacent pair of tokens into a new token", "Removes rare words", "Assigns random IDs"], 1, "BPE iteratively merges the most frequent adjacent symbol pair, growing the vocabulary."),
    Q("What is the attention_mask returned by a tokenizer used for?", ["To hide sensitive words", "To mark real tokens (1) versus padding (0) so padding is ignored", "To select which layers to train", "To store token frequencies"], 1, "Padding makes sequences equal length; the mask tells the model which positions to ignore."),
], [
    R("Andrej Karpathy: Let's build the GPT Tokenizer", "https://www.youtube.com/watch?v=zduSFxRajkE", "video"),
    R("Hugging Face LLM Course: Tokenizers chapter", "https://huggingface.co/learn/llm-course/chapter6/1", "course"),
    R("Tiktokenizer (interactive token visualizer)", "https://tiktokenizer.vercel.app/", "article"),
]))

lessons.append(L("m06-l2-embeddings", "Embeddings: Meaning as Vectors", 45, r"""
## The idea

An **embedding** is a dense vector (e.g. 384-3072 numbers) that represents a piece of text — a token, sentence or document — so that **similar meanings are close together** in vector space. Embeddings are the foundation of semantic search, RAG (retrieval-augmented generation), recommendations, clustering and classification. As an AI engineer, you'll use them constantly.

## From one-hot to dense vectors

Old-school NLP represented words as **one-hot** vectors: a 50,000-long vector with a single 1. Every word is equally distant from every other — "cat" is as different from "kitten" as from "carburettor". Dense embeddings compress words into a few hundred dimensions where geometry carries meaning.

## Word2Vec: you shall know a word by the company it keeps

Word2Vec (2013) learned word vectors by training a shallow network to predict a word from its neighbours (CBOW) or neighbours from a word (skip-gram). Words appearing in similar contexts ("coffee"/"tea" both appear near "cup", "drink", "hot") end up with similar vectors. Famous result: `king - man + woman = queen`.

```python
import numpy as np
# toy 3-D "embeddings" to illustrate the arithmetic
E = {
    "king":  np.array([0.9, 0.8, 0.1]),
    "queen": np.array([0.9, 0.1, 0.8]),
    "man":   np.array([0.1, 0.9, 0.1]),
    "woman": np.array([0.1, 0.2, 0.8]),
}
target = E["king"] - E["man"] + E["woman"]
def cos(a, b): return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
print(max(E, key=lambda w: cos(E[w], target)))    # 'queen'
```

### The limitation: one vector per word

Word2Vec gives "bank" one vector whether you mean a river bank or a savings bank. **Contextual embeddings** from transformers fix this: each token's vector depends on the whole sentence, thanks to attention (next lesson).

## Sentence embeddings

For search and RAG you need one vector per sentence or passage. **Embedding models** (e.g. the sentence-transformers family, BGE, E5, GTE, Nomic, and commercial APIs from OpenAI, Cohere, Voyage, Google) are transformers trained with **contrastive learning**: pull matching pairs (question/answer, paraphrases) together and push unrelated pairs apart.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")   # small, fast, 384-dim
sentences = [
    "How do I reset my password?",
    "I forgot my login credentials.",
    "What is the refund policy?",
    "Spring Boot uses dependency injection.",
]
emb = model.encode(sentences, normalize_embeddings=True)
print(emb.shape)                # (4, 384)

sim = emb @ emb.T               # cosine similarity (vectors are normalized)
print(np.round(sim, 2))         # sentences 0 and 1 score high despite sharing no words
```

That's **semantic** similarity: "reset my password" matches "forgot my login credentials" with no keyword overlap — something SQL `LIKE` or keyword search can't do.

## Building semantic search

```python
docs = [
    "Our office is open Monday to Friday, 9am to 6pm.",
    "Refunds are processed within 5-7 business days.",
    "To change your password, go to Settings > Security.",
    "We ship to India, the US and Europe.",
    "Premium members get 24/7 phone support.",
]
doc_emb = model.encode(docs, normalize_embeddings=True)

def search(query, k=2):
    q = model.encode([query], normalize_embeddings=True)[0]
    scores = doc_emb @ q
    top = np.argsort(-scores)[:k]
    return [(docs[i], round(float(scores[i]), 3)) for i in top]

print(search("how long until I get my money back?"))
print(search("can I call someone at midnight?"))
```

This retrieve-by-meaning step is the "R" in RAG: find the most relevant chunks, then pass them to an LLM to answer from. At scale (millions of vectors), you store embeddings in a **vector database** (pgvector in Postgres, Qdrant, Weaviate, Pinecone, Milvus, Elasticsearch/OpenSearch) that uses approximate nearest-neighbour indexes like HNSW to search quickly.

## Practical considerations

- **Use the same model** for documents and queries; vectors from different models aren't comparable.
- **Dimensions vs cost:** bigger vectors can be more accurate but cost more storage and search time. Some models support truncating dimensions (Matryoshka embeddings).
- **Chunking:** embed passages of a few hundred tokens, not whole books — one vector can't capture everything in a long document.
- **Domain fit:** check benchmarks like MTEB, but always evaluate on your own data (recall@k on a set of real queries).
- **Hybrid search:** combine vector similarity with keyword search (BM25) for exact terms like product codes and names; often the best of both.
- **Re-ranking:** retrieve 50 candidates with embeddings, then re-score the best with a more accurate **cross-encoder** model.

## Embeddings as features

Embeddings also make great inputs for classical ML:

```python
from sklearn.linear_model import LogisticRegression
texts = ["great product", "terrible service", "loved it", "awful, never again"]
labels = [1, 0, 1, 0]
X = model.encode(texts)
clf = LogisticRegression().fit(X, labels)
print(clf.predict(model.encode(["absolutely fantastic", "worst purchase ever"])))
```

A logistic regression on top of good embeddings is a cheap, fast, strong text classifier — often good enough before reaching for LLM calls or fine-tuning. You can also cluster embeddings (k-means, HDBSCAN) to discover topics in support tickets, and visualize them with UMAP.

## Inside the model: the embedding layer

Inside a transformer, the first layer is a lookup table `nn.Embedding(vocab_size, d_model)`. These vectors start random and are learned during training. Sentence embeddings are typically produced by **pooling** (averaging) the final-layer contextual token vectors, or by using a special token's vector.

## Key takeaways

- Embeddings map text to vectors where distance reflects meaning.
- Word2Vec gives static word vectors; transformers give contextual ones; embedding models give sentence/passage vectors trained contrastively.
- Semantic search = embed documents, embed query, rank by cosine similarity — the core of RAG.
- In production: vector databases, chunking, hybrid search and re-ranking; evaluate with recall@k.
""", r"""
**Task: FAQ semantic search.**

1. Write 20 FAQ entries for an imaginary product (or scrape a real FAQ page you're allowed to use).
2. Embed them with `all-MiniLM-L6-v2` and implement `search(query, k=3)`.
3. Create 10 test queries phrased differently from the FAQ text, with the correct FAQ index for each. Compute recall@1 and recall@3.
4. Compare against a keyword baseline (TF-IDF with `sklearn.feature_extraction.text.TfidfVectorizer`) on the same test set.
5. Try a second embedding model (e.g. `BAAI/bge-small-en-v1.5`) and compare recall.
6. Visualize all FAQ embeddings in 2-D with PCA or UMAP, coloured by topic.
""", [
    Q("What property makes embeddings useful for semantic search?", ["They are always 2-dimensional", "Texts with similar meanings map to nearby vectors", "They store the exact original text", "They are sorted alphabetically"], 1, "Embedding models are trained so that semantic similarity corresponds to geometric closeness (high cosine similarity)."),
    Q("What limitation of Word2Vec do contextual (transformer) embeddings fix?", ["Word2Vec vectors are too large", "Word2Vec gives each word one vector regardless of context (e.g. 'bank')", "Word2Vec can't handle English", "Word2Vec requires labels"], 1, "Static embeddings conflate word senses; transformer embeddings depend on surrounding words."),
    Q("Why combine keyword (BM25) search with vector search?", ["Vector search can't handle long documents", "Keyword search catches exact terms like codes and names that embeddings may miss", "BM25 is required by vector databases", "To reduce embedding dimensions"], 1, "Hybrid search pairs semantic matching with exact lexical matching for better overall retrieval."),
], [
    R("Jay Alammar: The Illustrated Word2vec", "https://jalammar.github.io/illustrated-word2vec/", "article"),
    R("Sentence Transformers documentation", "https://sbert.net/", "docs"),
    R("MTEB Leaderboard (embedding model benchmark)", "https://huggingface.co/spaces/mteb/leaderboard", "docs"),
]))

lessons.append(L("m06-l3-attention", "The Attention Mechanism, Step by Step", 55, r"""
## The core question attention answers

In "The animal didn't cross the street because **it** was too tired," what does "it" refer to? To build a good representation of "it", the model must look at "animal". **Self-attention** lets every token look at every other token in the sequence and pull in the information it needs, weighted by relevance. It's the single most important idea behind transformers and LLMs.

## Queries, keys and values: a lookup analogy

Think of a Java `HashMap<String, Value>` lookup — but **soft**:

- Each token produces a **query** (Q): "what am I looking for?"
- Each token produces a **key** (K): "what do I contain?"
- Each token produces a **value** (V): "what information do I pass on if selected?"

A hard hashmap returns the value whose key exactly equals the query. Attention compares the query to **all** keys (via dot products — similarity from Module 3), turns the scores into weights with softmax, and returns a **weighted average of all values**.

Q, K and V are produced by three learned linear projections of each token's embedding:

```python
import torch
import torch.nn.functional as F

torch.manual_seed(0)
T, d_model, d_k = 4, 8, 8           # 4 tokens, embedding size 8
x = torch.randn(T, d_model)         # token embeddings (one row per token)

W_q = torch.randn(d_model, d_k)
W_k = torch.randn(d_model, d_k)
W_v = torch.randn(d_model, d_k)

Q, K, V = x @ W_q, x @ W_k, x @ W_v   # each (T, d_k)
```

## Scaled dot-product attention

`Attention(Q, K, V) = softmax(Q @ K^T / sqrt(d_k)) @ V`

Step by step:

```python
scores = Q @ K.T                     # (T, T): how much token i's query matches token j's key
scores = scores / d_k ** 0.5         # scale so softmax doesn't saturate
weights = F.softmax(scores, dim=-1)  # each row sums to 1: attention distribution
out = weights @ V                    # (T, d_k): weighted mix of values per token
print(weights.round(decimals=2))
```

1. **Scores:** row i, column j = how relevant token j is to token i.
2. **Scaling by sqrt(d_k):** dot products grow with dimension; large values push softmax into regions with near-zero gradients. Dividing keeps them in a healthy range.
3. **Softmax:** turns each row into probabilities — the attention weights.
4. **Weighted sum:** each token's output is a context-aware blend of all tokens' values.

The output for "it" becomes a mix weighted heavily toward "animal" — a **contextual** representation.

## Causal masking: no peeking at the future

A GPT-style model generates text left to right, predicting the next token. During training, token i must not see tokens after it — otherwise predicting the next word is trivial. We apply a **causal mask** by setting future scores to negative infinity before softmax (so their weights become 0):

```python
mask = torch.tril(torch.ones(T, T))                 # lower-triangular matrix of 1s
scores = (Q @ K.T) / d_k ** 0.5
scores = scores.masked_fill(mask == 0, float("-inf"))
weights = F.softmax(scores, dim=-1)
print(weights.round(decimals=2))   # upper triangle is all zeros
```

Row 0 attends only to itself; row 3 attends to tokens 0-3. Encoder models like BERT use no causal mask (they see the whole sentence at once); padding masks still hide pad tokens.

## Multi-head attention

One attention operation captures one kind of relationship. **Multi-head attention** runs several attention "heads" in parallel, each with its own Q/K/V projections and smaller dimension, then concatenates and projects the results. Different heads learn different patterns: one might track the previous word, another subject-verb agreement, another coreference ("it" -> "animal").

```python
class MultiHeadSelfAttention(torch.nn.Module):
    def __init__(self, d_model=64, n_heads=4, causal=True):
        super().__init__()
        assert d_model % n_heads == 0
        self.h, self.d_k, self.causal = n_heads, d_model // n_heads, causal
        self.qkv = torch.nn.Linear(d_model, 3 * d_model)   # Q, K, V in one matmul
        self.proj = torch.nn.Linear(d_model, d_model)

    def forward(self, x):                                  # x: (B, T, d_model)
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=-1)
        # reshape to (B, heads, T, d_k) so each head attends independently
        q, k, v = (t.view(B, T, self.h, self.d_k).transpose(1, 2) for t in (q, k, v))
        att = (q @ k.transpose(-2, -1)) / self.d_k ** 0.5  # (B, h, T, T)
        if self.causal:
            mask = torch.tril(torch.ones(T, T, device=x.device, dtype=torch.bool))
            att = att.masked_fill(~mask, float("-inf"))
        att = att.softmax(dim=-1)
        out = att @ v                                      # (B, h, T, d_k)
        out = out.transpose(1, 2).contiguous().view(B, T, C)   # concat heads
        return self.proj(out)

mha = MultiHeadSelfAttention()
print(mha(torch.randn(2, 10, 64)).shape)                   # torch.Size([2, 10, 64])
```

In practice, use PyTorch's fused, memory-efficient kernel (FlashAttention under the hood):

```python
out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
```

## Self-attention vs cross-attention

- **Self-attention:** Q, K and V all come from the same sequence.
- **Cross-attention:** queries come from one sequence and keys/values from another — e.g. a translation decoder attending to the encoded source sentence, or an image-captioning model attending to image features.

## Cost: the quadratic problem

The score matrix is T x T. Double the context length and attention compute and memory roughly quadruple. That's why long context windows are expensive, and why research focuses on efficient attention (FlashAttention, sliding-window attention, grouped-query attention, KV caching during generation). The **KV cache** stores past keys and values so generating each new token doesn't recompute attention over the whole prefix — a key inference optimization you'll hear about in LLM serving.

## Why attention won

- **Direct connections:** any token reaches any other in one step (RNNs needed many steps).
- **Parallelism:** all positions computed at once with matrix multiplications — perfect for GPUs.
- **Interpretability (partial):** attention weights can be visualized to see what tokens attend to.

## Key takeaways

- Attention = softmax(QK^T / sqrt(d_k)) V: a soft, learned lookup over all tokens.
- Q, K, V are learned linear projections of token embeddings.
- Causal masks prevent looking at future tokens in decoder (GPT) models.
- Multi-head attention captures multiple relationship types; cost grows quadratically with sequence length.
""", r"""
**Task: Attention from scratch.**

1. Implement `attention(Q, K, V, mask=None)` in NumPy (no PyTorch) and verify it matches `F.scaled_dot_product_attention` on random inputs (within 1e-5).
2. Show the effect of the scaling factor: with d_k = 512, compare softmax outputs with and without dividing by sqrt(d_k). What happens to the distribution?
3. Apply a causal mask and print the attention weights matrix; explain why the first row is `[1, 0, 0, ...]`.
4. Use `bertviz` (or `output_attentions=True` in Hugging Face) on `bert-base-uncased` for the sentence "The animal didn't cross the street because it was too tired" and find a head where "it" attends strongly to "animal".
5. Compute how the T x T attention matrix memory grows for T = 1k, 8k, 128k tokens (float16, one head).
""", [
    Q("What is the formula for scaled dot-product attention?", ["softmax(Q + K) V", "softmax(Q K^T / sqrt(d_k)) V", "Q K V / d_k", "sigmoid(Q V^T) K"], 1, "Scores are query-key dot products scaled by sqrt(d_k), normalized with softmax, then used to weight the values."),
    Q("Why do GPT-style models use a causal mask?", ["To speed up training", "To prevent each token from attending to future tokens it is supposed to predict", "To hide padding tokens only", "To reduce the vocabulary size"], 1, "Next-token prediction would be trivial if a position could see the tokens after it."),
    Q("How does attention's cost scale with sequence length T?", ["Linearly, O(T)", "Quadratically, O(T^2)", "Logarithmically", "It is constant"], 1, "Every token attends to every other token, producing a T x T score matrix."),
], [
    R("Jay Alammar: The Illustrated Transformer", "https://jalammar.github.io/illustrated-transformer/", "article"),
    R("3Blue1Brown: Attention in transformers, step-by-step", "https://www.youtube.com/watch?v=eMlx5fFNoYc", "video"),
    R("Vaswani et al. (2017): Attention Is All You Need", "https://arxiv.org/abs/1706.03762", "article"),
]))

lessons.append(L("m06-l4-transformer", "The Transformer Architecture: Build a Mini GPT", 60, r"""
## The big picture

A **transformer** is a stack of identical blocks. Each block lets tokens **communicate** (attention) and then **think individually** (a feed-forward network). Residual connections and normalization keep the deep stack trainable. A decoder-only transformer (GPT, Llama, Claude-style models) looks like this:

```
token IDs -> token embedding + position information
          -> [ Transformer block ] x N
                 x = x + Attention(LayerNorm(x))     # communicate
                 x = x + FeedForward(LayerNorm(x))   # compute per token
          -> final LayerNorm
          -> linear "LM head" -> logits over vocabulary -> softmax -> next token
```

## The pieces

### 1. Token embeddings

`nn.Embedding(vocab_size, d_model)` turns each ID into a vector (lesson 2).

### 2. Positional information

Attention is order-blind: "dog bites man" and "man bites dog" contain the same tokens. We must inject position:

- **Learned absolute embeddings** (GPT-2): a second table `nn.Embedding(max_len, d_model)` added to token embeddings.
- **Sinusoidal encodings** (original transformer): fixed sine/cosine patterns.
- **RoPE (rotary position embeddings):** rotates Q and K vectors by position-dependent angles so attention depends on relative distance; used by Llama and most modern LLMs, and helps with extending context length.

### 3. Feed-forward network (MLP)

After attention mixes information across tokens, each token passes independently through a 2-layer MLP, typically expanding to 4x the width: `Linear(d, 4d) -> GELU -> Linear(4d, d)`. Modern models often use the SwiGLU variant. Most of a transformer's parameters live here, and research suggests much factual knowledge is stored in these layers.

### 4. Residual connections + LayerNorm

`x = x + sublayer(norm(x))` — the "pre-norm" arrangement used by modern models. The residual stream is a highway that every block reads from and writes to; gradients flow straight through it (same idea as ResNet). LayerNorm (or RMSNorm) keeps activations stable.

### 5. Output head

A final linear layer maps each position's vector to `vocab_size` logits. During training, position t predicts token t+1, and the loss is cross-entropy averaged over all positions — every position is a training example, which is part of why transformers train so efficiently.

## A complete mini GPT in PyTorch

This compact model (in the spirit of Karpathy's nanoGPT) trains on characters of any text file.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class Block(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.1):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, 4 * d_model), nn.GELU(),
            nn.Linear(4 * d_model, d_model), nn.Dropout(dropout),
        )

    def forward(self, x):
        T = x.size(1)
        causal = torch.triu(torch.ones(T, T, dtype=torch.bool, device=x.device), diagonal=1)
        h = self.ln1(x)
        attn_out, _ = self.attn(h, h, h, attn_mask=causal, need_weights=False)
        x = x + attn_out                   # residual 1: communicate
        x = x + self.ffn(self.ln2(x))      # residual 2: compute
        return x

class MiniGPT(nn.Module):
    def __init__(self, vocab_size, d_model=128, n_heads=4, n_layers=4, max_len=128):
        super().__init__()
        self.max_len = max_len
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_len, d_model)
        self.blocks = nn.Sequential(*[Block(d_model, n_heads) for _ in range(n_layers)])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, idx, targets=None):           # idx: (B, T) token IDs
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)    # (B, T, d_model)
        x = self.ln_f(self.blocks(x))
        logits = self.head(x)                        # (B, T, vocab)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.max_len:]           # crop to context window
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature     # last position only
            if top_k:
                v, _ = torch.topk(logits, top_k)
                logits[logits < v[:, [-1]]] = float("-inf")
            probs = F.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)   # sample
            idx = torch.cat([idx, next_id], dim=1)
        return idx
```

### Training it on text

```python
text = open("input.txt", encoding="utf-8").read()     # e.g. tiny Shakespeare
chars = sorted(set(text))
stoi = {c: i for i, c in enumerate(chars)}; itos = {i: c for c, i in stoi.items()}
data = torch.tensor([stoi[c] for c in text], dtype=torch.long)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = MiniGPT(vocab_size=len(chars)).to(device)
opt = torch.optim.AdamW(model.parameters(), lr=3e-4)
block = 128

def get_batch(batch_size=32):
    ix = torch.randint(len(data) - block - 1, (batch_size,))
    x = torch.stack([data[i:i + block] for i in ix])
    y = torch.stack([data[i + 1:i + block + 1] for i in ix])    # shifted by one
    return x.to(device), y.to(device)

for step in range(3000):
    xb, yb = get_batch()
    _, loss = model(xb, yb)
    opt.zero_grad(); loss.backward(); opt.step()
    if step % 500 == 0:
        print(step, round(loss.item(), 3))

start = torch.tensor([[stoi["\n"]]], device=device)
print("".join(itos[i] for i in model.generate(start, 300, temperature=0.8)[0].tolist()))
```

Note the targets: `y` is `x` shifted by one position — that is all "next-token prediction" means. After a few minutes on a GPU, the model produces Shakespeare-looking text. It's the same recipe as GPT, minus scale: real LLMs use subword tokenizers, dozens of layers, d_model in the thousands, and trillions of training tokens.

## Decoding strategies

`generate` shows how text comes out of an LLM: one token at a time, appended and fed back (**autoregressive** generation).

- **Greedy:** always pick the most likely token — deterministic, can be repetitive.
- **Temperature:** scale logits; lower = more focused, higher = more random.
- **Top-k:** sample only among the k most likely tokens.
- **Top-p (nucleus):** sample from the smallest set whose probabilities sum to p.

These are exactly the `temperature` and `top_p` parameters in LLM APIs.

## Scale: the same architecture, bigger

| Model | Layers | d_model | Parameters |
|---|---|---|---|
| Our MiniGPT | 4 | 128 | ~0.8M |
| GPT-2 small | 12 | 768 | 124M |
| GPT-3 | 96 | 12,288 | 175B |

Modern open models add refinements — RoPE, RMSNorm, SwiGLU, grouped-query attention, mixture-of-experts layers (only some FFN "experts" active per token) — but the block structure is recognizably the same.

## Key takeaways

- A transformer block: `x + Attention(LN(x))`, then `x + FFN(LN(x))`, stacked N times.
- Position must be injected (learned, sinusoidal or RoPE) because attention ignores order.
- Training = predict token t+1 from tokens up to t with cross-entropy at every position.
- Generation is autoregressive sampling controlled by temperature, top-k and top-p.
""", r"""
**Task: Train your own MiniGPT.**

1. Download tiny Shakespeare (`https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt`) and train the MiniGPT from the lesson on a Colab GPU for 5,000 steps. Hold out the last 10% as validation and print validation loss every 500 steps.
2. Generate 500 characters at temperatures 0.5, 1.0 and 1.5 and describe the differences.
3. Count the model's parameters and identify which component (embeddings, attention, FFN) holds the most.
4. Experiment: change `n_layers` to 2 and 8, and `d_model` to 64 and 256. Record validation loss in a table.
5. Replace character tokens with tiktoken's `gpt2` encoding and retrain. How does the output change?
6. Watch Karpathy's "Let's build GPT" video and compare his implementation to yours.
""", [
    Q("In a pre-norm transformer block, what is the attention sublayer's update?", ["x = Attention(x)", "x = x + Attention(LayerNorm(x))", "x = LayerNorm(x) * Attention(x)", "x = Attention(x) - x"], 1, "The residual connection adds the attention output (computed on normalized input) back to the stream."),
    Q("Why do transformers need positional information?", ["To reduce memory", "Self-attention by itself is order-invariant, so word order would be lost", "To normalize embeddings", "To enable dropout"], 1, "Without position embeddings, permuting the input tokens would permute outputs identically — order would be invisible."),
    Q("During language model training, what are the targets for input tokens x[0..T-1]?", ["The same tokens x[0..T-1]", "Tokens shifted by one: x[1..T]", "Random tokens", "Sentence labels"], 1, "Each position learns to predict the next token, so targets are the input sequence shifted one step left."),
], [
    R("Andrej Karpathy: Let's build GPT from scratch, in code, spelled out", "https://www.youtube.com/watch?v=kCc8FmEb1nY", "video"),
    R("Karpathy: nanoGPT repository", "https://github.com/karpathy/nanoGPT", "docs"),
    R("Transformer Explainer (interactive GPT-2 visualization)", "https://poloclub.github.io/transformer-explainer/", "article"),
    R("The Annotated Transformer (Harvard NLP)", "https://nlp.seas.harvard.edu/annotated-transformer/", "article"),
]))

lessons.append(L("m06-l5-bert-gpt", "Encoders, Decoders & Model Families: BERT vs GPT vs T5", 45, r"""
## One architecture, three shapes

The original 2017 transformer had an **encoder** (reads the input) and a **decoder** (generates output). Researchers soon found that each half works brilliantly on its own. Knowing which family a model belongs to tells you what it's good at — a frequent interview topic.

| Family | Attention | Pretraining objective | Examples | Best at |
|---|---|---|---|---|
| Encoder-only | bidirectional (sees whole input) | masked language modelling | BERT, RoBERTa, DeBERTa, ModernBERT | understanding: classification, NER, embeddings, retrieval |
| Decoder-only | causal (left-to-right) | next-token prediction | GPT series, Llama, Mistral, Qwen, Claude, Gemini | generation, chat, reasoning, general-purpose LLMs |
| Encoder-decoder | encoder bidirectional + decoder causal with cross-attention | span corruption / denoising | T5, BART, Whisper | input-to-output transformation: translation, summarization, speech-to-text |

## BERT: the encoder

BERT (2018) is trained with **masked language modelling (MLM)**: randomly hide ~15% of tokens and predict them using context from **both** sides.

```
Input : The [MASK] sat on the mat because it was [MASK].
Target: The  cat   sat on the mat because it was  tired.
```

Because each token sees left and right context, BERT builds rich representations of the input — but it can't naturally generate text left to right.

```python
from transformers import pipeline

fill = pipeline("fill-mask", model="bert-base-uncased")
for r in fill("Raj is learning to become an AI [MASK]."):
    print(r["token_str"], round(r["score"], 3))      # engineer, researcher, ...
```

### How BERT is used

You add a small task-specific head and **fine-tune** on labelled data:

- **Sequence classification** (sentiment, intent, spam): a linear layer on the `[CLS]` token's final vector.
- **Token classification** (named entity recognition): a linear layer on every token.
- **Extractive question answering:** predict the start and end positions of the answer span.
- **Embeddings / retrieval:** sentence-transformer and cross-encoder models are mostly BERT-style encoders.

Encoders are small (100-400M parameters), fast and cheap — for a high-volume classification job, a fine-tuned encoder often beats calling a giant LLM on cost and latency.

## GPT: the decoder

GPT models are trained only to predict the next token with a causal mask (lesson 4). The surprise of the GPT-2/GPT-3 era: with enough scale, a next-token predictor learns grammar, facts, translation, coding and reasoning, and can perform new tasks from instructions or a few examples in the prompt (**in-context learning**), with no fine-tuning.

```python
generator = pipeline("text-generation", model="gpt2")
out = generator("The best way to learn machine learning is", max_new_tokens=30,
                do_sample=True, temperature=0.8)
print(out[0]["generated_text"])
```

GPT-2 (2019) is tiny by today's standards, so the output is rambly — but it's the same architecture as modern LLMs.

### Why decoder-only won for general AI

- **One simple objective** that scales to any amount of raw text.
- **Every task becomes text generation:** classification, extraction, translation, code, tool calls — all expressed as "continue this text".
- **Efficient generation** with KV caching.

Almost all frontier LLMs today are decoder-only (some use mixture-of-experts variants).

## T5 and BART: encoder-decoder

T5 ("Text-to-Text Transfer Transformer") frames every task as text in, text out: `"translate English to German: That is good."` -> `"Das ist gut."`. The encoder reads the full input bidirectionally; the decoder generates the output, cross-attending to the encoder states.

```python
t5 = pipeline("text2text-generation", model="google/flan-t5-small")
print(t5("Translate English to French: I am learning transformers.")[0]["generated_text"])
print(t5("Is this review positive or negative? Review: The food was cold and bland.")[0]["generated_text"])
```

Encoder-decoders remain strong for translation, summarization and speech recognition (OpenAI's Whisper is encoder-decoder: audio encoder, text decoder).

## Comparing them side by side

```python
from transformers import AutoModel, AutoTokenizer
import torch

tok = AutoTokenizer.from_pretrained("bert-base-uncased")
bert = AutoModel.from_pretrained("bert-base-uncased")
inputs = tok("The river bank was muddy.", return_tensors="pt")
with torch.no_grad():
    hidden = bert(**inputs).last_hidden_state       # (1, T, 768): contextual vector per token
print(hidden.shape)
```

An encoder gives you **vectors** (representations). A decoder gives you **next-token logits** (generation). An encoder-decoder gives you **generated text conditioned on an input**.

## Choosing a model as an AI engineer

| Need | Good starting choice |
|---|---|
| Classify 10M support tickets per day cheaply | fine-tuned encoder (DeBERTa/ModernBERT) or embeddings + logistic regression |
| Semantic search / RAG retrieval | embedding model (encoder) + optional cross-encoder re-ranker |
| Chatbot, agent, open-ended Q&A, code | decoder-only LLM via API or open weights |
| Translation or speech-to-text | encoder-decoder (or a strong general LLM) |
| Few labelled examples, varied tasks | prompt a decoder LLM with few-shot examples |

## Multimodal transformers

The same ideas extend beyond text. **Vision Transformers** split images into patches treated as tokens; **CLIP** trains an image encoder and text encoder so matching images and captions have similar embeddings; multimodal LLMs connect an image (or audio) encoder to a decoder LLM so it can "see" and "hear".

## Key takeaways

- Encoder-only (BERT): bidirectional, masked-LM pretraining, best for understanding and embeddings.
- Decoder-only (GPT): causal, next-token pretraining, best for generation; today's LLMs.
- Encoder-decoder (T5, BART, Whisper): sequence-to-sequence transformations.
- Pick by task, cost and latency — a small encoder often beats a large LLM for narrow, high-volume tasks.
""", r"""
**Task: Model family tour.**

1. Use the `fill-mask` pipeline with `bert-base-uncased` on 5 sentences of your own; note where it succeeds and fails.
2. Generate continuations with `gpt2` and `distilgpt2` using greedy decoding vs sampling (temperature 0.7, top_p 0.9). Compare repetitiveness.
3. Use `google/flan-t5-base` for translation, summarization of a paragraph, and yes/no questions.
4. Extract BERT's contextual vector for "bank" in "river bank" vs "bank account" vs "savings bank". Compute cosine similarities and explain the result.
5. For 6 real use cases from your company or imagination, choose encoder / decoder / encoder-decoder and justify the choice in one sentence each.
""", [
    Q("What pretraining objective does BERT use?", ["Next-token prediction", "Masked language modelling (predict hidden tokens using both sides of context)", "Image captioning", "Reinforcement learning from human feedback"], 1, "BERT masks ~15% of tokens and predicts them bidirectionally."),
    Q("Which model family do most modern chat LLMs belong to?", ["Encoder-only", "Decoder-only", "Encoder-decoder", "Convolutional"], 1, "GPT, Llama, Claude and similar LLMs are decoder-only transformers trained on next-token prediction."),
    Q("You need to classify millions of short texts per day with low latency and cost. A strong first choice is ...", ["A 400B-parameter LLM via API for every text", "A fine-tuned small encoder model like DeBERTa, or embeddings + a linear classifier", "An RNN trained from scratch", "A T5 model for translation"], 1, "Small encoders are fast, cheap and highly accurate on narrow classification tasks once fine-tuned."),
], [
    R("Jay Alammar: The Illustrated BERT, ELMo and co.", "https://jalammar.github.io/illustrated-bert/", "article"),
    R("Hugging Face LLM Course: How do Transformers work?", "https://huggingface.co/learn/llm-course/chapter1/4", "course"),
    R("Sebastian Raschka: Build a Large Language Model (From Scratch)", "https://www.manning.com/books/build-a-large-language-model-from-scratch", "book"),
]))

lessons.append(L("m06-l6-huggingface", "Hugging Face: Pipelines, Models & Fine-Tuning", 55, r"""
## The GitHub of AI

**Hugging Face** hosts over a million open models, datasets and demo apps (Spaces), plus the libraries everyone uses: `transformers`, `datasets`, `tokenizers`, `peft`, `accelerate` and `trl`. Think of the Hub as Maven Central for models: you reference a model by name (`"bert-base-uncased"`) and the library downloads and caches it.

## Level 1: pipelines (zero ML code)

`pipeline()` bundles tokenizer, model and post-processing for a task:

```python
from transformers import pipeline

sentiment = pipeline("sentiment-analysis",
                     model="distilbert-base-uncased-finetuned-sst-2-english")
print(sentiment(["I love this course!", "The deployment failed again."]))
# [{'label': 'POSITIVE', 'score': 0.99...}, {'label': 'NEGATIVE', 'score': 0.99...}]

zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
print(zero_shot("My invoice shows the wrong amount",
                candidate_labels=["billing", "technical issue", "sales"]))

ner = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
print(ner("Raj works at Infosys in Bengaluru."))

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
asr = pipeline("automatic-speech-recognition", model="openai/whisper-small")
```

Always pin a specific `model=`; the default can change between library versions. Pass `device=0` to use the first GPU.

## Level 2: Auto classes (what pipelines do inside)

```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

name = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(name)
model = AutoModelForSequenceClassification.from_pretrained(name)
model.eval()

inputs = tokenizer(["Great work!", "This is broken."], padding=True, return_tensors="pt")
with torch.no_grad():
    logits = model(**inputs).logits             # (2, 2)
probs = logits.softmax(dim=-1)
for p in probs:
    print(model.config.id2label[p.argmax().item()], round(p.max().item(), 3))
```

The `AutoModelFor...` classes attach the right head: `...ForSequenceClassification`, `...ForTokenClassification`, `...ForQuestionAnswering`, `...ForCausalLM` (generation), `...ForMaskedLM`. These models are ordinary PyTorch `nn.Module`s — everything from Module 5 applies.

### Generating with a chat model

Instruction-tuned decoder models expect a **chat template** that wraps messages in their special tokens:

```python
from transformers import AutoModelForCausalLM

name = "Qwen/Qwen2.5-0.5B-Instruct"          # small enough for a laptop/Colab
tok = AutoTokenizer.from_pretrained(name)
llm = AutoModelForCausalLM.from_pretrained(name, torch_dtype="auto")

messages = [
    {"role": "system", "content": "You are a concise tutor."},
    {"role": "user", "content": "Explain overfitting in one sentence."},
]
prompt_ids = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
out = llm.generate(prompt_ids, max_new_tokens=60, do_sample=True, temperature=0.7)
print(tok.decode(out[0][prompt_ids.shape[1]:], skip_special_tokens=True))
```

## The datasets library

```python
from datasets import load_dataset

ds = load_dataset("imdb")                  # train/test splits of movie reviews
print(ds)
print(ds["train"][0]["text"][:200], ds["train"][0]["label"])

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, max_length=256)

tokenized = ds.map(tokenize, batched=True)        # fast, cached, memory-mapped (Arrow)
small_train = tokenized["train"].shuffle(seed=42).select(range(5000))
small_test = tokenized["test"].shuffle(seed=42).select(range(2000))
```

## Level 3: fine-tuning with the Trainer

Fine-tuning a pretrained encoder on your labelled data is one of the most valuable practical skills. The `Trainer` wraps the training loop you wrote in Module 5 (with mixed precision, evaluation, checkpointing, logging):

```python
import numpy as np
from transformers import (AutoModelForSequenceClassification, TrainingArguments,
                          Trainer, DataCollatorWithPadding)
import evaluate

base = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(base)
tokenized = ds.map(lambda b: tokenizer(b["text"], truncation=True, max_length=256), batched=True)
model = AutoModelForSequenceClassification.from_pretrained(
    base, num_labels=2, id2label={0: "NEG", 1: "POS"}, label2id={"NEG": 0, "POS": 1})

accuracy = evaluate.load("accuracy")
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    return accuracy.compute(predictions=np.argmax(logits, axis=-1), references=labels)

args = TrainingArguments(
    output_dir="imdb-distilbert",
    learning_rate=2e-5,                    # small LR: we're nudging pretrained weights
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    num_train_epochs=2,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    bf16=True,                             # use fp16=True on older GPUs; remove on CPU
)

trainer = Trainer(
    model=model, args=args,
    train_dataset=tokenized["train"].shuffle(seed=42).select(range(5000)),
    eval_dataset=tokenized["test"].shuffle(seed=42).select(range(2000)),
    processing_class=tokenizer,
    data_collator=DataCollatorWithPadding(tokenizer),   # pads each batch dynamically
    compute_metrics=compute_metrics,
)
trainer.train()
print(trainer.evaluate())                  # ~88-91% accuracy with just 5k examples
trainer.save_model("imdb-distilbert/best")
```

Then load it like any Hub model: `pipeline("text-classification", model="imdb-distilbert/best")`. You can `push_to_hub()` to share it.

## Parameter-efficient fine-tuning (PEFT) and LoRA

Fully fine-tuning a 7B-parameter LLM needs huge GPU memory (Module 5). **LoRA** freezes the original weights and trains small low-rank matrices added to some layers — often under 1% of the parameters — with quality close to full fine-tuning. **QLoRA** additionally loads the frozen base model in 4-bit, making it possible to fine-tune 7-8B models on a single consumer or Colab GPU.

```python
from peft import LoraConfig, get_peft_model

lora_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                      target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM")
peft_model = get_peft_model(llm, lora_cfg)
peft_model.print_trainable_parameters()     # e.g. "trainable params: ~1M || all params: ~500M"
```

The `trl` library's `SFTTrainer` (supervised fine-tuning) and `DPOTrainer` build on this for LLMs — next lesson explains what those stages do.

## When to fine-tune vs prompt vs RAG

- **Prompting** first: fastest, no training. Use few-shot examples.
- **RAG** when the model needs your private or fresh knowledge.
- **Fine-tuning** when you need a consistent format/style/behaviour, a smaller cheaper model for a narrow task, or lower latency — and you have hundreds to thousands of quality examples.

## Practical tips

- Model files are cached in `~/.cache/huggingface`; large models take gigabytes.
- Check the model card: license (some forbid commercial use), intended use, training data, limitations.
- Gated models (e.g. Llama) require accepting a license and a Hugging Face access token (`huggingface-cli login`).
- Load big models with `torch_dtype="auto"` and `device_map="auto"` to use bf16 and spread across available devices.

## Key takeaways

- `pipeline()` gives one-line inference for dozens of tasks; pin model names.
- `AutoTokenizer` + `AutoModelFor<Task>` are regular PyTorch modules with the right head.
- `datasets` + `Trainer` fine-tune pretrained models efficiently with a small learning rate.
- LoRA/QLoRA make LLM fine-tuning affordable; prefer prompting and RAG first.
""", r"""
**Task: Fine-tune your own classifier.**

1. Pick a text classification dataset from the Hub (e.g. `ag_news`, `emotion`, or `banking77` for intent detection).
2. Establish baselines: (a) zero-shot classification pipeline, (b) sentence embeddings + logistic regression.
3. Fine-tune `distilbert-base-uncased` (or `answerdotai/ModernBERT-base`) with the Trainer on a Colab GPU. Report accuracy and macro-F1.
4. Compare all three approaches in a table: accuracy, inference time per 1,000 texts, and training cost/time.
5. Push the best model to your Hugging Face account and build a small Gradio demo in a Space.

Bonus: load `Qwen/Qwen2.5-0.5B-Instruct` and prompt it few-shot for the same task — how does it compare?
""", [
    Q("What does `AutoModelForSequenceClassification.from_pretrained(name, num_labels=3)` give you?", ["A tokenizer", "A pretrained transformer body with a (new) 3-class classification head", "A dataset", "A pipeline"], 1, "The Auto class loads the pretrained weights and attaches a task head sized for your labels, which is then fine-tuned."),
    Q("Why is the learning rate for fine-tuning pretrained transformers small (e.g. 2e-5)?", ["Large learning rates are not supported", "To gently adapt pretrained weights without destroying learned knowledge", "To save GPU memory", "Because the dataset is large"], 1, "Big updates would overwrite the useful representations learned during pretraining (catastrophic forgetting)."),
    Q("What is the main benefit of LoRA?", ["It makes models more accurate than full fine-tuning in all cases", "It trains a small number of low-rank adapter parameters while freezing the base model, drastically cutting memory", "It removes the need for a tokenizer", "It speeds up tokenization"], 1, "LoRA trains tiny adapter matrices instead of all weights, enabling fine-tuning of large models on modest hardware."),
], [
    R("Hugging Face LLM Course (free)", "https://huggingface.co/learn/llm-course/chapter1/1", "course"),
    R("Transformers docs: Fine-tuning a pretrained model", "https://huggingface.co/docs/transformers/training", "docs"),
    R("PEFT documentation (LoRA and more)", "https://huggingface.co/docs/peft/index", "docs"),
]))

lessons.append(L("m06-l7-llm-training", "How LLMs Are Trained: Pretraining, SFT, RLHF & DPO", 55, r"""
## From text predictor to helpful assistant

A chat assistant isn't trained in one go. It goes through a pipeline of stages, each solving a different problem:

```
1. Pretraining         -> base model: knows language and the world, but just continues text
2. Supervised fine-tuning (SFT) -> follows instructions in a chat format
3. Preference tuning (RLHF / DPO) -> more helpful, honest and harmless; matches human preferences
4. (Increasingly) RL on verifiable tasks -> stronger reasoning on maths and code
```

Understanding these stages explains much LLM behaviour and is a classic interview topic.

## Stage 1: Pretraining

**Objective:** next-token prediction (cross-entropy) on an enormous corpus — trillions of tokens of web pages, books, code, papers and more.

**Data work is most of the job:** crawling, extracting text, deduplication, quality filtering (often using smaller models as classifiers), removing personal data and toxic content, and choosing the data mix (how much code, maths, multilingual text).

**Compute:** thousands of GPUs for weeks to months, using the parallelism techniques from Module 5 (data, tensor, pipeline parallelism, FSDP). Costs range from millions to hundreds of millions of dollars for frontier models.

**Scaling laws:** loss falls predictably as a power law with more parameters, data and compute. The "Chinchilla" result (2022) showed many models were undertrained; a compute-optimal rule of thumb is roughly 20 training tokens per parameter; many modern models train on far more because smaller models are cheaper to serve.

**The result — a base model:** ask it "What is the capital of France?" and it might continue with "What is the capital of Germany? What is the capital of..." because on the internet, questions often appear in lists. It has knowledge but no notion of being an assistant.

```python
from transformers import pipeline
base = pipeline("text-generation", model="gpt2")      # a base model
print(base("Q: What is the capital of France?\nA:", max_new_tokens=10)[0]["generated_text"])
```

## Stage 2: Supervised Fine-Tuning (SFT)

**Objective:** still next-token prediction, but on curated **demonstrations** — prompt/response pairs written or vetted by people (and increasingly generated and filtered with strong models), formatted as conversations with a **chat template**:

```python
example = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain recursion to a Java developer."},
        {"role": "assistant", "content": "Recursion is when a method calls itself..."},
    ]
}
```

Typically, the loss is computed only on the **assistant's tokens** (the prompt tokens are masked out), so the model learns to produce responses, not to imitate users. Tens of thousands to millions of high-quality examples teach instruction-following, conversational format, tool-call syntax and refusal style. Quality beats quantity: a small set of excellent examples can outperform a large noisy one.

```python
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

dataset = load_dataset("trl-lib/Capybara", split="train")   # chat-formatted examples
trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",                                # a small base model
    train_dataset=dataset,
    args=SFTConfig(output_dir="qwen-sft", max_steps=500, per_device_train_batch_size=4,
                   learning_rate=2e-5),
)
trainer.train()
```

This is the same stage you'd use to fine-tune an open model on your company's support conversations.

## Stage 3: Learning from human preferences

SFT teaches the format, but it's hard to write a perfect demonstration for everything. It's much easier for people to **compare** two responses and say which is better. Preference tuning exploits that.

### RLHF (Reinforcement Learning from Human Feedback)

1. **Collect comparisons:** for a prompt, sample two or more responses from the SFT model; labelers rank them (more helpful, accurate, safe).
2. **Train a reward model:** a transformer that takes (prompt, response) and outputs a scalar score, trained so preferred responses score higher.
3. **Optimize the policy with RL:** generate responses, score them with the reward model, and update the LLM (classically with **PPO**) to increase reward — while a **KL-divergence penalty** keeps it close to the SFT model, so it doesn't drift into gibberish that happens to fool the reward model (**reward hacking**).

RLHF powered InstructGPT and ChatGPT. It's also complex: four models in memory (policy, reference, reward, value) and finicky RL training. Variants use AI feedback instead of (or in addition to) human labels — e.g. Anthropic's **Constitutional AI**, where a model critiques and revises outputs according to a written set of principles.

### DPO (Direct Preference Optimization)

DPO (2023) showed you can skip the separate reward model and RL loop. Using the same preference pairs (prompt, chosen, rejected), DPO directly adjusts the model to raise the probability of the chosen response relative to the rejected one, compared with a frozen reference model. The loss looks like a simple classification loss:

`loss = -log sigmoid( beta * [ (log p(chosen) - log p_ref(chosen)) - (log p(rejected) - log p_ref(rejected)) ] )`

```python
from trl import DPOTrainer, DPOConfig

prefs = load_dataset("trl-lib/ultrafeedback_binarized", split="train")  # prompt/chosen/rejected
trainer = DPOTrainer(
    model="qwen-sft",                          # start from the SFT checkpoint
    train_dataset=prefs,
    args=DPOConfig(output_dir="qwen-dpo", beta=0.1, max_steps=300,
                   per_device_train_batch_size=2, learning_rate=5e-7),
)
trainer.train()
```

DPO is stable, cheap and widely used for open models; variants include IPO, KTO and ORPO.

## Stage 4: Reinforcement learning for reasoning

Since 2024, "reasoning models" (OpenAI's o-series, DeepSeek-R1 and others) add large-scale RL on tasks with **verifiable rewards**: a maths answer can be checked; code can be run against tests. The model is rewarded for correct final answers and learns to produce long chains of thought — exploring, checking and backtracking — before answering. Algorithms like **GRPO** (Group Relative Policy Optimization) compare a group of sampled answers to each other instead of training a separate value model. This is why reasoning models "think" (spending extra tokens and time at inference) and excel at maths and coding.

## What this means for you as an AI engineer

- **Base vs instruct models:** use instruct/chat models for applications; base models are for further training.
- **Hallucinations** come from pretraining's objective: the model learned to produce plausible text, not to know what it doesn't know. Mitigate with RAG, tools, and verification.
- **Knowledge cutoff:** facts stop at the pretraining data date; RAG and tools supply fresh information.
- **Sycophancy** can be a side effect of preference tuning (raters may favour agreeable answers).
- **Your own fine-tuning** typically means SFT (and sometimes DPO) with LoRA on an open model — rarely pretraining.
- **Evaluation:** every stage needs evals; you'll build them for your own LLM apps later in the course.

## Key takeaways

- Pretraining: next-token prediction on trillions of tokens -> a knowledgeable base model.
- SFT: train on curated chat demonstrations (loss on assistant tokens) -> instruction following.
- RLHF: reward model from human comparisons + RL with a KL penalty; DPO optimizes preferences directly without RL.
- RL with verifiable rewards (e.g. GRPO) trains reasoning models; these stages explain hallucinations, cutoffs and sycophancy.
""", r"""
**Task: Walk the training pipeline in miniature.**

1. Compare a base and an instruct model of the same family (e.g. `Qwen/Qwen2.5-0.5B` vs `Qwen/Qwen2.5-0.5B-Instruct`) on 5 identical prompts. Record how their behaviour differs.
2. Run a short SFT job with `trl`'s `SFTTrainer` and LoRA (via `peft_config`) on 1,000 examples of a chat dataset on Colab. Compare outputs before and after.
3. Create 20 preference pairs yourself (prompt, chosen, rejected) for a style you want (e.g. "concise answers with a code example") and run a few hundred steps of DPO. Does the style shift?
4. Implement the DPO loss for one example in plain PyTorch given four log-probabilities, and check how it changes as the chosen/rejected margin grows.
5. Write a one-page explanation of the four training stages, aimed at your Java team lead.
""", [
    Q("What does a base (pretrained-only) model do when given a question?", ["Always answers helpfully", "Continues the text in a statistically plausible way, which may not be an answer", "Refuses to respond", "Asks for clarification"], 1, "A base model only predicts likely continuations; answering helpfully is learned later in SFT and preference tuning."),
    Q("What is the role of the KL penalty in RLHF?", ["To speed up training", "To keep the tuned model close to the reference (SFT) model and prevent reward hacking", "To increase the vocabulary", "To reduce the context length"], 1, "Without it, the policy could drift to degenerate outputs that exploit flaws in the reward model."),
    Q("How does DPO differ from classic RLHF?", ["DPO needs no preference data", "DPO optimizes directly on preference pairs without training a separate reward model or running an RL loop", "DPO is only used for pretraining", "DPO uses images"], 1, "DPO reformulates preference learning as a simple loss on chosen vs rejected log-probabilities relative to a reference model."),
], [
    R("Andrej Karpathy: Deep Dive into LLMs like ChatGPT", "https://www.youtube.com/watch?v=7xTGNNLPyMI", "video"),
    R("Hugging Face blog: Illustrating RLHF", "https://huggingface.co/blog/rlhf", "article"),
    R("Rafailov et al. (2023): Direct Preference Optimization", "https://arxiv.org/abs/2305.18290", "article"),
    R("TRL documentation (SFT, DPO, GRPO trainers)", "https://huggingface.co/docs/trl/index", "docs"),
]))

MODULE = M("m06-nlp-transformers", 6, "NLP & Transformers", "Advanced", 3,
    "Go from raw text to the transformer architecture that powers every modern LLM: tokenization, embeddings, attention, and a GPT you build yourself. You will learn to use and fine-tune Hugging Face models and understand exactly how LLMs are pretrained and aligned with SFT, RLHF and DPO.",
    [
        "Explain and implement tokenization (BPE), embeddings and semantic search",
        "Derive and code scaled dot-product and multi-head attention with causal masking",
        "Build and train a mini GPT and explain every component of a transformer block",
        "Choose between encoder, decoder and encoder-decoder models and fine-tune them with Hugging Face (including LoRA)",
        "Describe the LLM training pipeline: pretraining, SFT, RLHF, DPO and RL for reasoning",
    ],
    lessons,
    ("Fine-Tuned Support Assistant: Classifier + Semantic Search + Small LLM", r"""
## Goal
Combine everything from this module into one working system — a portfolio project that previews the AI-engineering work (RAG, agents, evals) in the next part of the course.

## Scenario
A company receives customer support messages. Build a service that (1) classifies the intent, (2) retrieves the most relevant help-centre articles, and (3) drafts a reply with a small open LLM.

## Spec
- **Intent classifier:** fine-tune `distilbert-base-uncased` or ModernBERT on the `banking77` dataset (77 intents). Report accuracy and macro-F1 vs an embeddings + logistic regression baseline.
- **Semantic search:** write or collect ~50 help articles, chunk them by tokens, embed with a sentence-transformer, and implement top-k retrieval. Evaluate recall@3 on 20 hand-written queries.
- **Reply drafting:** prompt `Qwen/Qwen2.5-0.5B-Instruct` (or similar small instruct model) with the user message, predicted intent and retrieved articles using its chat template. Optionally LoRA-SFT it on 200 example replies.
- **API:** a FastAPI endpoint `POST /assist` returning `{intent, confidence, articles, draft_reply}` with a Pydantic response model.
- **Demo:** a Gradio UI deployed to Hugging Face Spaces.

## Steps
1. Set up the project with uv; separate modules: `classify.py`, `retrieve.py`, `generate.py`, `api.py`.
2. Train and save the classifier; push it to the Hub.
3. Build and evaluate retrieval; experiment with chunk size and with hybrid (BM25 + vector) search.
4. Write prompts; compare greedy vs sampled decoding; make the model cite article titles.
5. Write tests (classifier loads, retrieval returns k results, API schema) and a README with metrics.

## Stretch goals
- Store embeddings in Postgres with **pgvector** (you know SQL already).
- Add a cross-encoder re-ranker and measure the recall improvement.
- Run DPO on 50 preference pairs to make replies more concise.
- Call the FastAPI service from a small Spring Boot app to show end-to-end Java + Python integration.
"""))
