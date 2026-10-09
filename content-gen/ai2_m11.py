from ai2_common import Q, R, L, M

lessons = [
L("m11-when-to-fine-tune", "When to Fine-tune vs Prompt vs RAG", 35, r"""
## The adaptation ladder

You have three main ways to make a general LLM good at your task. Climb them in order of cost:

1. **Prompt engineering** (hours): instructions, few-shot examples, structured output.
2. **RAG / tools** (days): give the model the *knowledge* it lacks at query time.
3. **Fine-tuning** (days to weeks + ongoing maintenance): change the model's *weights* by training on examples.

A common mistake: fine-tuning to teach facts. **Fine-tuning is good at teaching behaviour, format and style, not at reliably injecting knowledge.** Facts learned by fine-tuning are hard to update, can't be cited and are easily hallucinated. Knowledge -> RAG. Behaviour -> prompting first, then fine-tuning.

### What fine-tuning is good for

- **Consistent format/style** that's hard to describe in a prompt: your company's tone, a specific JSON structure, a terse clinical note style.
- **Narrow, high-volume tasks** where a **small fine-tuned model** can match a big general model at a fraction of cost and latency (classification, extraction, routing, ticket triage). This is the biggest business case: distil the behaviour of an expensive model into a cheap one.
- **Shortening prompts**: bake long instructions and examples into weights, saving tokens per request.
- **Domain language** the base model handles poorly (specialised jargon, a low-resource language) - sometimes via continued pre-training on raw text first.
- **Privacy / on-prem**: fine-tune and run an open model inside your network.
- **Tool-use or reasoning patterns** for agents in a specific environment (advanced).

### What it's bad for

- Frequently changing knowledge (product catalogue, policies) -> RAG.
- Tasks where you have fewer than ~100 good examples and no way to get more.
- Fixing a problem you haven't diagnosed (maybe retrieval is the issue).
- Teams without evaluation in place: you can't tell if the tuned model is better.

### Types of fine-tuning (vocabulary)

| Type | What | Data |
|------|------|------|
| **Continued pre-training** | Next-token training on raw domain text | Large unlabelled corpus |
| **Supervised fine-tuning (SFT) / instruction tuning** | Train on (prompt, ideal response) pairs | Hundreds to tens of thousands of examples |
| **Preference tuning (RLHF, DPO, etc.)** | Teach which of two responses is better | (prompt, chosen, rejected) triples |
| **Reinforcement fine-tuning** | Optimise against a reward/grader (e.g. tests pass, answer correct) | Prompts + automatic graders |

And by *how many parameters change*:
- **Full fine-tuning**: update all weights. Needs lots of GPU memory (weights + gradients + optimizer states, roughly 16+ bytes per parameter in mixed precision with Adam).
- **Parameter-efficient fine-tuning (PEFT)**, e.g. **LoRA/QLoRA**: freeze the base model, train small adapter matrices. 10-100x less memory, adapters of a few MB. The default for most teams (lesson 3).

### Hosted vs self-managed

- **Hosted fine-tuning APIs** (OpenAI, Google, Amazon Bedrock, Together, Fireworks and others): upload JSONL, get a model endpoint. Fast to try; you don't own the weights; per-token inference pricing.
- **Open models** (Llama, Qwen, Mistral, Gemma, Phi and others): fine-tune with Hugging Face TRL/PEFT, Unsloth or Axolotl on your GPUs or rented cloud GPUs; full control, you handle serving.

Note: Anthropic doesn't offer general self-serve fine-tuning of Claude via its main API at the time of writing; Claude adaptation is done via prompting, RAG and tools (check current docs, as offerings change).

### A decision checklist

```text
1. Have I written a strong prompt and evaluated it on 50+ examples?      -> if no, do that
2. Is the gap about missing knowledge?                                   -> RAG
3. Is the gap about format/style/behaviour, or cost/latency at volume?   -> consider fine-tuning
4. Do I have (or can I generate) 500+ high-quality examples?             -> needed
5. Do I have an eval set and a baseline to beat?                         -> required
6. Can I maintain it (retrain when base models/data change)?             -> plan it
```

### Cost reality

Training cost is often small (a LoRA run on a 7-8B model can be a few dollars of GPU time). The real costs are **data creation**, **evaluation**, **serving infrastructure** and **maintenance**: when a better base model ships next quarter, your fine-tune may be obsolete, while a prompt + RAG system can switch models in minutes.

A quick break-even calculation helps frame the decision (plug in real prices from provider pages):

```python
def monthly_cost(requests, in_tok, out_tok, price_in, price_out, fixed=0.0):
    return requests * (in_tok * price_in + out_tok * price_out) / 1e6 + fixed

big_prompted = monthly_cost(2_000_000, 1500, 30, 3.00, 15.00)            # long few-shot prompt
small_tuned  = monthly_cost(2_000_000, 200, 30, 0.10, 0.40, fixed=800)   # short prompt + GPU/hosting
print(f"large prompted: ${big_prompted:,.0f}/month, small fine-tuned: ${small_tuned:,.0f}/month")
```

Only if the quality on your eval set holds does the cheaper number matter.

### Key takeaways
- Prompt -> RAG -> fine-tune, in that order.
- Fine-tune for behaviour, format, style and cheap specialised models; use RAG for knowledge.
- PEFT (LoRA/QLoRA) is the default technique; full fine-tuning is rarely needed.
- Data, evals and maintenance dominate cost, not GPU hours.
""", r"""
For each scenario, choose prompt / RAG / fine-tune / combination and justify in 3-4 sentences:
1. A bank wants answers about its 2,000-page, monthly-updated policy manual.
2. A startup classifies 2 million support tickets/month into 40 categories; the large model works but is too expensive.
3. A hospital wants discharge summaries in a strict house style from doctors' notes, on-premise.
4. An e-commerce chatbot must answer in a friendly Hinglish tone using live order data.
Then write the eval plan (metrics + dataset) you'd need before fine-tuning for scenario 2.
""", [
Q("A company wants the model to know its product catalogue, updated weekly. Best approach?", ["Fine-tune weekly", "RAG over the catalogue", "Increase temperature", "Continued pre-training"], 1, "Frequently changing knowledge belongs in retrieval, not weights."),
Q("Which is a strong business case for fine-tuning?", ["Teaching the model today's news", "Distilling a narrow high-volume task into a small, cheap, fast model", "Replacing evaluation", "Avoiding data collection"], 1, "Specialised small models can match large ones on narrow tasks at much lower cost."),
Q("What does PEFT (e.g. LoRA) change during training?", ["All model weights", "Only small added adapter parameters while the base model is frozen", "Only the tokenizer", "Nothing - it's prompting"], 1, "Parameter-efficient methods train a small number of extra parameters."),
], [
R("OpenAI - Model optimization / fine-tuning guide", "https://platform.openai.com/docs/guides/model-optimization", "docs"),
R("Hugging Face - LLM Course: fine-tuning chapter", "https://huggingface.co/learn/llm-course/chapter11/1", "course"),
R("Anyscale - Fine-tuning vs RAG considerations", "https://www.anyscale.com/blog/fine-tuning-is-for-form-not-facts", "article"),
R("Chip Huyen - AI Engineering, ch. 7 (Finetuning)", "https://www.oreilly.com/library/view/ai-engineering/9781098166298/", "book"),
]),

L("m11-datasets", "Building Fine-tuning Datasets", 45, r"""
## Data is the model

"Garbage in, garbage out" is truer for fine-tuning than anywhere else. A few hundred **excellent, consistent** examples beat tens of thousands of noisy ones. Most of your fine-tuning effort should go here.

### The chat format

Modern SFT datasets are conversations in JSONL, one example per line, matching how the model will be used:

```json
{"messages": [
  {"role": "system", "content": "Classify the support ticket. Reply with JSON."},
  {"role": "user", "content": "My UPI payment was debited but order shows failed"},
  {"role": "assistant", "content": "{\"category\": \"PAYMENT\", \"priority\": \"high\"}"}
]}
```

The training library applies the model's **chat template** (special tokens marking roles, which you saw in module 6) and usually computes loss only on the assistant tokens, so the model learns to *produce* responses, not to predict user text.

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
ex = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]
print(tok.apply_chat_template(ex, tokenize=False))
```

Always use the template of the model you fine-tune, and use the **same system prompt and format at inference** as in training.

### Where data comes from

1. **Production logs**: real inputs paired with outputs that humans approved or corrected. Best distribution match. Scrub PII.
2. **Expert-written examples**: highest quality, slowest. Use for seed sets and edge cases.
3. **Distillation from a strong model**: run a frontier model with a great prompt on real inputs, filter outputs with checks/judges, train a small model on them. Check the provider's terms of use regarding training competing models.
4. **Synthetic generation**: LLM generates inputs too (varied personas, edge cases). Useful for coverage; risk of low diversity and artefacts.
5. **Public datasets** on Hugging Face Hub as a base or for mixing.

### Quality over quantity

Checklist per example:
- **Correct**: the output is what an expert would accept.
- **Consistent**: the same kind of input always gets the same kind of output (labels, format, tone). Inconsistent labels teach the model to be random.
- **Representative**: covers the real distribution of inputs (lengths, languages, typos, rare categories).
- **Includes hard cases**: ambiguous inputs, refusals ("not enough information"), adversarial inputs.

```python
import json, collections
rows = [json.loads(l) for l in open("train.jsonl", encoding="utf-8")]

# basic hygiene
seen, clean = set(), []
for r in rows:
    user = r["messages"][-2]["content"].strip()
    ans = r["messages"][-1]["content"]
    if not user or user in seen:
        continue                                  # drop empty + exact duplicates
    try:
        json.loads(ans)                           # output must be valid JSON for this task
    except ValueError:
        continue
    seen.add(user); clean.append(r)

labels = collections.Counter(json.loads(r["messages"][-1]["content"])["category"] for r in clean)
print(len(rows), "->", len(clean), labels.most_common())
```

Look at the label distribution: if one class has 5 examples, the model will rarely predict it. Oversample, generate more, or merge classes.

### How many examples?

Rough guidance (varies by task and model):
- Format/style adaptation: 100-1,000 high-quality examples often show clear gains.
- Classification/extraction distillation: 1,000-10,000.
- Teaching a new complex skill: more, and maybe not feasible.

Do a **learning curve**: train on 25%, 50%, 100% of data and plot eval score. If it's still rising, more data helps; if flat, improve quality or the approach.

### Splits and leakage

- **Train / validation / test** (e.g. 80/10/10). Validation for picking checkpoints and hyperparameters, test touched only at the end.
- Avoid **leakage**: near-duplicate examples across splits inflate scores. Split by customer, document or time where appropriate (train on older tickets, test on newer).
- Keep the test set aligned with your **production eval set** from module 12.

### Preference data (for DPO)

For preference tuning you need `(prompt, chosen, rejected)`:

```json
{"prompt": "Explain recursion to a beginner",
 "chosen": "Recursion is when a function solves a problem by calling itself on a smaller version...",
 "rejected": "Recursion: a function f such that f is defined in terms of f. See also: recursion."}
```

Sources: human rankings of two model outputs, thumbs up/down in your app, or an LLM judge comparing pairs.

### Generating synthetic data responsibly

```python
PERSONAS = ["angry customer", "elderly first-time user", "Hinglish speaker", "terse developer"]
def synth_ticket(category, persona):
    return llm(f"Write a realistic support ticket about a {category} problem written by a {persona}. "
               "1-4 sentences, include realistic details, no greeting boilerplate.", temperature=1.0)
```

Vary personas, lengths and difficulty; deduplicate by embedding similarity; have a strong model or human label them; spot-check 5-10% manually.

### Key takeaways
- Use chat-format JSONL with the model's chat template; match training and inference formats.
- Quality and consistency beat volume; check label balance and hard cases.
- Combine logs, expert examples, distillation and synthetic data; dedupe and validate.
- Split carefully to avoid leakage; use learning curves to decide if more data helps.
""", r"""
1. Create a dataset for a task of your choice (e.g. classifying Indian e-commerce support tickets into 6 categories with priority) with 300+ examples using synthetic generation with personas plus 50 hand-written ones.
2. Write a cleaning script: dedupe (exact and embedding similarity > 0.95), validate JSON, print label distribution.
3. Split 80/10/10 and save `train.jsonl`, `val.jsonl`, `test.jsonl`.
4. Establish a baseline: evaluate a small instruct model with a prompt (no fine-tuning) on the test set. You'll beat this in lesson 4.
""", [
Q("Why compute loss only on assistant tokens during SFT?", ["To save disk space", "So the model learns to produce responses rather than to predict user/system text", "Because user text has no tokens", "It's required by JSON"], 1, "Masking non-assistant tokens focuses learning on the desired output."),
Q("What is data leakage in fine-tuning evaluation?", ["Uploading data to the internet", "Near-duplicate examples in both train and test sets, inflating test scores", "Using too little data", "Using JSONL"], 1, "Leakage makes the model look better than it is on unseen data."),
Q("Your eval score keeps rising from 25% to 50% to 100% of the data. What does that suggest?", ["Stop collecting data", "More data would likely help further", "The model is broken", "Use a higher learning rate"], 1, "A rising learning curve indicates the model hasn't saturated."),
], [
R("Hugging Face - Chat templates", "https://huggingface.co/docs/transformers/chat_templating", "docs"),
R("TRL - Dataset formats and types", "https://huggingface.co/docs/trl/dataset_formats", "docs"),
R("LIMA: Less Is More for Alignment (paper)", "https://arxiv.org/abs/2305.11206", "article"),
R("Argilla - open-source data labelling for LLMs", "https://docs.argilla.io/latest/", "docs"),
]),

L("m11-lora-qlora", "LoRA and QLoRA Explained", 40, r"""
## The problem with full fine-tuning

An 8B-parameter model in bf16 needs 16 GB just to hold weights. Full fine-tuning with Adam also stores gradients and two optimizer moments per parameter, plus activations: easily 100+ GB of GPU memory. And you'd save a full 16 GB copy per fine-tuned variant.

### LoRA: Low-Rank Adaptation

Key insight (Hu et al., 2021): the *change* in weights needed to adapt a model to a task has **low intrinsic rank**. So instead of learning a full update matrix dW (size d x k, e.g. 4096 x 4096 = 16.7M numbers), learn it as a product of two thin matrices:

dW = B x A, where B is d x r and A is r x k, with r small (8, 16, 32).

For r = 16: 4096x16 + 16x4096 = 131k parameters instead of 16.7M, which is about 0.8%.

During training:
- The original weight W is **frozen**.
- Forward pass: h = W x + (alpha / r) * B A x
- A is initialised randomly, B to zero, so training starts exactly from the base model.
- Only A and B get gradients and optimizer states.

```python
import torch, torch.nn as nn

class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r=16, alpha=32):
        super().__init__()
        self.base = base
        for p in self.base.parameters():
            p.requires_grad = False                         # freeze original
        self.A = nn.Parameter(torch.randn(r, base.in_features) * 0.01)
        self.B = nn.Parameter(torch.zeros(base.out_features, r))
        self.scale = alpha / r

    def forward(self, x):
        return self.base(x) + (x @ self.A.T @ self.B.T) * self.scale

layer = LoRALinear(nn.Linear(4096, 4096))
trainable = sum(p.numel() for p in layer.parameters() if p.requires_grad)
total = sum(p.numel() for p in layer.parameters())
print(trainable, total, f"{100*trainable/total:.2f}%")
```

That's genuinely all LoRA is. The PEFT library wraps chosen layers of a model this way.

### Benefits

- **Memory**: no gradients/optimizer state for frozen weights; fine-tune 7-8B models on a single 24 GB GPU (with QLoRA even smaller GPUs).
- **Storage**: adapters are a few MB to a few hundred MB. Keep one base model and many adapters (one per customer/task).
- **No inference latency** if you **merge**: W' = W + (alpha/r) B A, giving a normal model. Or keep adapters separate and hot-swap them; servers like vLLM can serve many LoRA adapters on one base model.
- Quality: for most SFT tasks, close to full fine-tuning.

### Hyperparameters that matter

| Param | Typical | Notes |
|-------|---------|-------|
| `r` (rank) | 8-64 | Higher = more capacity, more memory. 16 is a good default |
| `lora_alpha` | r to 2r | Scaling; with alpha = 2r a common heuristic |
| `target_modules` | attention q,k,v,o + MLP gate/up/down | Targeting all linear layers usually works best |
| `lora_dropout` | 0-0.1 | Regularisation |
| learning rate | 1e-4 to 2e-4 | Higher than full fine-tuning LR |
| epochs | 1-3 | More risks overfitting/forgetting |

### QLoRA: LoRA on a 4-bit base

QLoRA (Dettmers et al., 2023) goes further:
1. Load the frozen base model **quantised to 4 bits** using the **NF4** (NormalFloat4) data type, designed for normally distributed weights.
2. **Double quantisation**: quantise the quantisation constants too, saving more memory.
3. **Paged optimizers** to survive memory spikes.
4. Train LoRA adapters in bf16 on top; during the forward pass, weights are dequantised on the fly.

Result: an 8B model's weights take about 5-6 GB, so you can fine-tune on a free Colab T4 or a consumer GPU. Trade-off: somewhat slower training (dequantisation overhead) and a small quality cost vs 16-bit LoRA.

```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct",
                                             quantization_config=bnb, device_map="auto")
```

### GPU memory back-of-envelope (interview favourite)

- Inference weights: params x bytes per param (bf16 = 2, int8 = 1, 4-bit = 0.5). 8B in bf16 = 16 GB; 4-bit = about 4-5 GB.
- Plus **KV cache** for context (grows with batch x sequence length x layers x hidden size).
- Full fine-tuning with Adam in mixed precision: roughly 16-20 bytes/param plus activations -> 8B needs well over 128 GB.
- LoRA: base weights (16 GB in bf16) + small adapter states + activations -> fits 24-48 GB.
- QLoRA: about 5-6 GB base + adapters + activations -> fits 12-24 GB.

### Catastrophic forgetting

Fine-tuning narrowly can degrade general abilities. LoRA mitigates (base weights unchanged) but doesn't eliminate it. Mitigations: fewer epochs, lower LR, mixing in some general instruction data, and always evaluating on a few general tasks alongside your target task.

### Key takeaways
- LoRA learns a low-rank update B x A while freezing W; trains well under 1-2% of parameters.
- Adapters are small, swappable and can be merged for zero inference overhead.
- QLoRA puts the frozen base in 4-bit NF4, enabling fine-tuning on consumer GPUs.
- Know the memory math: params x bytes, plus KV cache/activations/optimizer states.
""", r"""
1. Run the `LoRALinear` code and verify that the output equals the base layer's output at initialisation (since B = 0).
2. Compute the percentage of trainable parameters if LoRA (r=16) is applied to q,k,v,o of a model with 32 layers and hidden size 4096 (ignore GQA). Show the arithmetic.
3. Estimate GPU memory for: inference of a 14B model in bf16 and in 4-bit; QLoRA fine-tuning of an 8B model. State your assumptions.
4. Load a 1.5B model in 4-bit with BitsAndBytes on Colab and print `model.get_memory_footprint()`.
""", [
Q("In LoRA, which parameters are trained?", ["All weights", "Only the low-rank matrices A and B added to selected layers", "Only biases", "Only the embedding layer"], 1, "The base weight W stays frozen; only A and B are learned."),
Q("Why is B initialised to zero in LoRA?", ["To save memory", "So the adapted model starts exactly equal to the base model", "Because zero is required for 4-bit", "To speed up inference"], 1, "B=0 makes the initial update B x A equal to zero."),
Q("What does QLoRA quantise?", ["The LoRA adapters to 1 bit", "The frozen base model weights to 4-bit NF4", "The dataset", "The tokenizer"], 1, "The base is stored in 4-bit; adapters train in higher precision."),
], [
R("LoRA paper (Hu et al.)", "https://arxiv.org/abs/2106.09685", "article"),
R("QLoRA paper (Dettmers et al.)", "https://arxiv.org/abs/2305.14314", "article"),
R("Hugging Face PEFT documentation", "https://huggingface.co/docs/peft/index", "docs"),
R("Sebastian Raschka - Practical tips for finetuning LLMs using LoRA", "https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms", "article"),
]),

L("m11-hf-trainer-peft", "Hands-on: Fine-tuning with Hugging Face TRL and PEFT", 60, r"""
## The toolchain

- **transformers**: models, tokenizers, `Trainer`.
- **datasets**: loading/processing data.
- **peft**: LoRA and other adapters.
- **trl**: `SFTTrainer` (supervised fine-tuning), `DPOTrainer`, `GRPOTrainer` and friends; handles chat templates and loss masking.
- **bitsandbytes**: 4/8-bit quantisation for QLoRA.
- Alternatives that wrap these with speed/memory optimisations: **Unsloth** (fast single-GPU, popular with free Colab), **Axolotl** (YAML configs), **LLaMA-Factory**.

You need a GPU. Free options: Google Colab (T4), Kaggle notebooks (T4/P100). For 7-8B models, rent an A10/L4/A100 for a few hours.

### Full SFT + QLoRA script

We'll fine-tune a small instruct model on the ticket-classification dataset from lesson 2.

```python
# pip install transformers datasets peft trl bitsandbytes accelerate
import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig

BASE = "Qwen/Qwen2.5-1.5B-Instruct"         # small enough for a free T4
ds = load_dataset("json", data_files={"train": "train.jsonl", "validation": "val.jsonl"})

tok = AutoTokenizer.from_pretrained(BASE)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
model = AutoModelForCausalLM.from_pretrained(BASE, quantization_config=bnb, device_map="auto")

peft_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                      target_modules="all-linear")

args = SFTConfig(
    output_dir="ticket-lora",
    num_train_epochs=2,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,          # effective batch 16
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    logging_steps=10,
    eval_strategy="steps", eval_steps=50,
    save_strategy="steps", save_steps=50,
    max_length=512,
    assistant_only_loss=True,               # loss on assistant tokens (needs a compatible chat template)
    gradient_checkpointing=True,            # trade compute for memory
    fp16=True,
    report_to="none",
)

trainer = SFTTrainer(model=model, args=args, train_dataset=ds["train"],
                     eval_dataset=ds["validation"], processing_class=tok, peft_config=peft_cfg)
trainer.train()
trainer.save_model("ticket-lora/final")     # saves only the adapter (a few MB)
```

TRL's argument names evolve between versions; if one errors, check the current `SFTConfig` docs. The structure stays the same.

### Reading the training curves

- **Training loss** should fall steadily. If it drops to near zero quickly, you may be overfitting/memorising.
- **Validation loss** should fall then flatten. If it rises while training loss falls: overfitting. Use the checkpoint with the lowest validation loss, fewer epochs or more data.
- Loss spikes/NaN: learning rate too high, or fp16 overflow (use bf16 on GPUs that support it).

But **loss isn't your metric**. Evaluate on the task.

### Evaluate on the test set

```python
import json
from peft import PeftModel
base = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float16, device_map="auto")
ft = PeftModel.from_pretrained(base, "ticket-lora/final").eval()

def predict(messages):
    prompt = tok.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True)
    ids = tok(prompt, return_tensors="pt").to(ft.device)
    out = ft.generate(**ids, max_new_tokens=60, do_sample=False)
    return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)

test = [json.loads(l) for l in open("test.jsonl", encoding="utf-8")]
correct = valid = 0
for ex in test:
    pred = predict(ex["messages"])
    gold = json.loads(ex["messages"][-1]["content"])
    try:
        p = json.loads(pred); valid += 1
        correct += p.get("category") == gold["category"]
    except ValueError:
        pass
print(f"valid JSON {valid/len(test):.1%}, accuracy {correct/len(test):.1%}")
```

Compare against: the same base model with a prompt (your lesson-2 baseline) and a frontier model with a prompt. A typical outcome for a narrow task: the fine-tuned small model approaches or beats the prompted large model on accuracy at a tiny fraction of the cost.

### Merge and export

```python
merged = ft.merge_and_unload()               # W' = W + scaled BA
merged.save_pretrained("ticket-merged"); tok.save_pretrained("ticket-merged")
# optional: merged.push_to_hub("your-username/ticket-classifier")
```

Merge into a 16-bit base (not the 4-bit one) for best quality. The merged model can be converted to GGUF for Ollama/llama.cpp or served by vLLM (next lessons).

### Preference tuning with DPO (next step)

After SFT, **DPO** (Direct Preference Optimization) aligns outputs with preferences without training a separate reward model:

```python
from trl import DPOTrainer, DPOConfig
dpo = DPOTrainer(model=sft_model, args=DPOConfig(output_dir="dpo", beta=0.1, learning_rate=5e-6),
                 train_dataset=pref_ds, processing_class=tok, peft_config=peft_cfg)
dpo.train()
```

`pref_ds` has `prompt`, `chosen`, `rejected` columns. Use it to fix style issues SFT doesn't (verbosity, tone, refusals).

### Experiment hygiene

- Fix seeds, log configs (Weights & Biases or MLflow), version datasets.
- Change one hyperparameter at a time; start with defaults above.
- Keep a results table: data version, base model, r, LR, epochs, val loss, task accuracy, JSON validity.

### Key takeaways
- TRL's `SFTTrainer` + PEFT LoRA + bitsandbytes 4-bit = QLoRA in ~40 lines.
- Watch train vs validation loss for overfitting, but judge by task metrics on a held-out test set.
- Compare against prompted baselines; merge adapters for deployment.
- DPO is the common next step for preference alignment.
""", r"""
1. Fine-tune `Qwen2.5-0.5B-Instruct` or `1.5B-Instruct` with QLoRA on your lesson-2 dataset on Colab/Kaggle.
2. Plot training and validation loss; identify the best checkpoint.
3. Evaluate on the test set: accuracy and valid-JSON rate. Compare with (a) the base model prompted, (b) a frontier API model prompted. Include cost per 1,000 predictions for each.
4. Run one ablation: r=8 vs r=32, or 1 vs 3 epochs. Record results in a table.
5. Merge the adapter and push the model (or adapter) to the Hugging Face Hub with a model card.
""", [
Q("Validation loss rises while training loss keeps falling. This indicates:", ["Underfitting", "Overfitting - pick an earlier checkpoint or use fewer epochs/more data", "A tokenizer bug", "Perfect training"], 1, "Diverging curves are the classic overfitting signal."),
Q("What does `merge_and_unload()` do?", ["Deletes the adapter", "Folds the LoRA update into the base weights, producing a standalone model", "Quantises the model to 1 bit", "Uploads to the Hub"], 1, "Merging gives a normal model with no adapter overhead."),
Q("What data does DPO require?", ["Raw text only", "Prompts with a chosen and a rejected response", "Images", "Only a reward model"], 1, "DPO learns from preference pairs directly."),
], [
R("TRL - SFTTrainer documentation", "https://huggingface.co/docs/trl/sft_trainer", "docs"),
R("Unsloth - Fine-tuning guide and free notebooks", "https://docs.unsloth.ai/", "docs"),
R("Hugging Face - Fine-tune LLMs in 2025 (Phil Schmid)", "https://www.philschmid.de/fine-tune-llms-in-2025", "article"),
R("DPO paper: Direct Preference Optimization", "https://arxiv.org/abs/2305.18290", "article"),
]),

L("m11-quantization", "Quantization: Running Big Models on Small Hardware", 35, r"""
## What quantization is

**Quantization** stores model weights (and sometimes activations) with fewer bits: 16-bit -> 8-bit -> 4-bit or lower. Benefits:
- **Less memory**: 8B params x 2 bytes = 16 GB in bf16; at 4-bit about 4.5-5 GB. Now it fits a laptop or a single consumer GPU.
- **Faster inference**: LLM decoding is usually **memory-bandwidth bound** (each token reads all weights), so fewer bytes per weight means more tokens/second.
- **Cheaper serving**: fewer/smaller GPUs.

Cost: some quality loss, small at 8-bit, usually modest at good 4-bit, significant below ~3 bits.

### The basic idea

Map floats in a range to integers:

```python
import numpy as np
w = np.random.randn(8).astype(np.float32)
scale = np.abs(w).max() / 127                     # symmetric int8
q = np.round(w / scale).astype(np.int8)           # store these + one scale
w_hat = q.astype(np.float32) * scale              # dequantise when computing
print(np.round(w, 3)); print(q); print("max error", np.abs(w - w_hat).max())
```

Real schemes quantise in **small groups/blocks** (e.g. 32-128 weights share one scale) so one outlier doesn't ruin precision for the whole tensor.

### Formats and methods you'll meet

| Name | What | Where used |
|------|------|-----------|
| **bf16 / fp16** | 16-bit floats, the "unquantised" baseline | Training, high-quality serving |
| **int8 (LLM.int8, bitsandbytes)** | 8-bit with outlier handling | Quick memory savings in transformers |
| **NF4 (bitsandbytes)** | 4-bit NormalFloat | QLoRA training |
| **GPTQ** | Post-training 4-bit using calibration data to minimise layer error | GPU serving (vLLM, TGI) |
| **AWQ** | Activation-aware 4-bit: protects the most important weights | GPU serving (vLLM) |
| **GGUF** (llama.cpp) | File format with many quant types: Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K... | CPU/Mac/consumer GPU, Ollama, LM Studio |
| **FP8** | 8-bit floats supported by recent GPUs | High-throughput production serving |

Rules of thumb:
- **Q4_K_M / AWQ / GPTQ 4-bit**: the sweet spot for local use; quality close to 16-bit for most tasks.
- **Q8_0 / int8 / FP8**: nearly lossless.
- **Below 4 bits**: noticeable degradation, especially for reasoning, maths and code.
- A **bigger model at 4-bit often beats a smaller model at 16-bit** for the same memory.

### Quantizing in practice

Most popular open models already have quantised versions on the Hugging Face Hub (search "GGUF", "AWQ", "GPTQ"). Loading a model in 8-bit or 4-bit on the fly with transformers:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
cfg = BitsAndBytesConfig(load_in_8bit=True)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct",
                                             quantization_config=cfg, device_map="auto")
print(f"{model.get_memory_footprint()/1e9:.1f} GB")
```

Converting your merged fine-tuned model to GGUF for Ollama (llama.cpp tools):

```bash
# in a llama.cpp checkout
python convert_hf_to_gguf.py ../ticket-merged --outfile ticket-f16.gguf --outtype f16
./llama-quantize ticket-f16.gguf ticket-Q4_K_M.gguf Q4_K_M
```

### KV cache quantization

At long contexts and high concurrency, the **KV cache** (stored keys/values for every past token) can exceed the weights in memory. Servers like vLLM support FP8 KV cache to fit more concurrent requests. Know the term for interviews.

### Always measure

Quantization affects tasks unevenly. Before deploying a quantised model:
1. Run your **task eval set** on 16-bit vs quantised versions.
2. Check structured output validity (quantised small models break JSON more often).
3. Measure throughput and latency on your actual hardware.

```python
results = {}
for variant in ["bf16", "awq-4bit", "gguf-q4_k_m"]:
    acc, p50 = run_eval(variant, test_set)       # your harness
    results[variant] = (acc, p50)
print(results)
```

### Key takeaways
- Quantization trades a little quality for big memory, speed and cost savings.
- Decoding is memory-bandwidth bound, so fewer bits per weight = faster tokens.
- 4-bit (Q4_K_M, AWQ, GPTQ) is the practical sweet spot; 8-bit is near lossless.
- Evaluate quantised models on your own tasks before shipping.
""", r"""
1. Implement symmetric int8 and 4-bit quantisation of a random weight matrix with and without grouping (group size 64). Compare reconstruction error.
2. Load a 1.5-3B model in bf16, 8-bit and 4-bit with transformers; record memory footprint and tokens/second for a fixed prompt.
3. Run your lesson-4 test set on the fine-tuned model in 16-bit vs 4-bit and compare accuracy and JSON validity.
4. Explain in 4 sentences why LLM decoding speed depends on memory bandwidth.
""", [
Q("Why does quantization usually speed up LLM token generation?", ["Fewer layers", "Decoding is memory-bandwidth bound, and fewer bytes per weight means less data to read per token", "It skips attention", "It reduces vocabulary size"], 1, "Each generated token requires reading the weights; smaller weights read faster."),
Q("Which format is typically used with Ollama and llama.cpp?", ["GGUF", "ONNX only", "SafeTensors int2", "TFRecord"], 0, "GGUF is llama.cpp's quantised model format."),
Q("For the same memory budget, which is often better?", ["A smaller model at 16-bit", "A larger model at good 4-bit quantization", "They're always identical", "A 1-bit model"], 1, "A bigger model quantised to 4-bit frequently outperforms a smaller full-precision one."),
], [
R("Hugging Face - Quantization overview", "https://huggingface.co/docs/transformers/main/en/quantization/overview", "docs"),
R("Maarten Grootendorst - A Visual Guide to Quantization", "https://newsletter.maartengrootendorst.com/p/a-visual-guide-to-quantization", "article"),
R("llama.cpp GitHub (GGUF, quantize tool)", "https://github.com/ggml-org/llama.cpp", "docs"),
R("AWQ paper: Activation-aware Weight Quantization", "https://arxiv.org/abs/2306.00978", "article"),
]),

L("m11-local-serving", "Running Open Models Locally and in Production: Ollama and vLLM", 45, r"""
## Why run open models?

- **Privacy/compliance**: data never leaves your servers (banks, hospitals, government).
- **Cost at scale**: for high, steady volume, self-hosting can be cheaper than per-token APIs.
- **Control**: pin versions, fine-tune, no surprise deprecations.
- **Offline/edge** use.

Trade-offs: you run GPUs, scaling, monitoring and upgrades; frontier proprietary models may still be stronger on hard tasks. Many teams use a **mix**: open models for high-volume simple tasks, APIs for complex ones.

Popular open-weight families include Llama (Meta), Qwen (Alibaba), Mistral, Gemma (Google), DeepSeek, Phi (Microsoft) and gpt-oss (OpenAI). Check each model's **licence** (some restrict commercial use or require attribution).

### Ollama: the easiest local runner

Ollama wraps llama.cpp with a model library, GGUF models and a simple API. Great for development, demos and small deployments.

```bash
# install from ollama.com, then:
ollama pull qwen2.5:7b          # downloads a 4-bit GGUF (~4.7 GB)
ollama run qwen2.5:7b "Explain Spring @Transactional in one paragraph"
ollama list
```

It serves an HTTP API on port 11434, including an **OpenAI-compatible** endpoint, so your existing code works by changing `base_url`:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")   # key ignored
r = client.chat.completions.create(model="qwen2.5:7b",
    messages=[{"role": "user", "content": "Give 3 tips for Java memory tuning"}], temperature=0.3)
print(r.choices[0].message.content)
```

Run your own fine-tuned GGUF with a `Modelfile`:

```text
FROM ./ticket-Q4_K_M.gguf
PARAMETER temperature 0
SYSTEM "Classify the support ticket. Reply with JSON."
```

```bash
ollama create ticket-classifier -f Modelfile
ollama run ticket-classifier "Refund not received after 10 days"
```

Ollama also supports embeddings models (e.g. `nomic-embed-text`), tool calling and JSON-schema structured output for capable models.

### vLLM: high-throughput production serving

When many users hit the model concurrently, you need a serving engine optimised for GPUs. **vLLM** is the most widely used open-source option (alternatives: SGLang, Hugging Face TGI, NVIDIA TensorRT-LLM/Triton, llama.cpp server for CPU).

Key techniques (good interview material):
- **PagedAttention**: manages the KV cache in fixed-size blocks like OS virtual memory pages, eliminating fragmentation, so many more concurrent sequences fit in GPU memory.
- **Continuous batching**: new requests join the running batch at every decoding step instead of waiting for a whole batch to finish. Huge throughput gains over static batching.
- **Prefix caching**: shared prompt prefixes (system prompts) reuse KV cache.
- **Speculative decoding**, tensor parallelism across GPUs, quantised models (AWQ/GPTQ/FP8), multi-LoRA serving.

```bash
pip install vllm          # Linux + NVIDIA GPU
vllm serve Qwen/Qwen2.5-7B-Instruct --max-model-len 8192 --gpu-memory-utilization 0.9
# serve a LoRA adapter on top of the base model:
vllm serve Qwen/Qwen2.5-1.5B-Instruct --enable-lora --lora-modules ticket=./ticket-lora/final
```

It exposes the same OpenAI-compatible API on port 8000:

```python
client = OpenAI(base_url="http://localhost:8000/v1", api_key="none")
r = client.chat.completions.create(model="ticket",     # the LoRA name
    messages=[{"role": "user", "content": "UPI debited but order failed"}])
```

Offline batch inference (no server) is also simple:

```python
from vllm import LLM, SamplingParams
llm = LLM(model="Qwen/Qwen2.5-1.5B-Instruct")
outs = llm.generate(["Summarise: ...", "Translate to Hindi: ..."], SamplingParams(temperature=0, max_tokens=200))
print([o.outputs[0].text for o in outs])
```

### Sizing hardware

Memory needed is roughly **weights + KV cache + overhead**:
- Weights: params x bytes (7-8B: about 16 GB bf16, about 5 GB 4-bit).
- KV cache per token is about 2 x layers x kv_heads x head_dim x bytes. For an 8B model with grouped-query attention this is on the order of 100+ KB per token in bf16, so 32 concurrent users x 8k tokens needs tens of GB.
- Rule of thumb: a 24 GB GPU (L4/A10/RTX 4090) serves a 7-8B model comfortably (quantised for more concurrency); 70B-class models need 2-4 A100/H100s or aggressive quantisation.

### Benchmark what matters

Measure under realistic concurrency: **TTFT**, **tokens/second per user**, **total throughput (tokens/s across users)**, p95 latency, and cost per million tokens (GPU $/hour / tokens per hour). vLLM ships benchmarking scripts; tools like `locust` or `k6` work too.

### Deployment pattern

```
Angular UI -> Spring Boot API (auth, rate limits, logging) -> LLM gateway (LiteLLM or similar: routing, fallbacks, keys)
          -> vLLM pods on Kubernetes GPU nodes (autoscaled)  |  hosted APIs for complex queries
```

The OpenAI-compatible API is the glue: your app code doesn't care whether the model is Ollama on a laptop, vLLM on Kubernetes, or a hosted API.

### Key takeaways
- Ollama: easiest local runner (GGUF, OpenAI-compatible API, Modelfiles) for dev and small deployments.
- vLLM: production throughput via PagedAttention, continuous batching, prefix caching, multi-LoRA.
- Both speak the OpenAI API, making models swappable.
- Size GPUs from weights + KV cache; benchmark TTFT, throughput and cost under realistic load.
""", r"""
1. Install Ollama, pull two models of different sizes (e.g. 3B and 7-8B), and compare answers and tokens/second on 5 prompts.
2. Point your module 7 support-ticket assistant at Ollama via the OpenAI-compatible endpoint; note what breaks (tool calling, JSON) and fix it.
3. Import your fine-tuned GGUF from lesson 5 into Ollama with a Modelfile and run the test set against it.
4. If you have GPU access (Colab/Kaggle/cloud), serve a model with vLLM and benchmark 1 vs 16 concurrent requests (throughput and p95 latency).
""", [
Q("What problem does PagedAttention solve in vLLM?", ["Tokenization speed", "KV cache memory fragmentation, allowing more concurrent sequences per GPU", "Model training", "Prompt injection"], 1, "Block-based KV cache management like virtual memory pages."),
Q("What is continuous batching?", ["Training in batches", "Adding new requests to the running batch at each decoding step instead of waiting for a batch to finish", "Batch API pricing", "Caching embeddings"], 1, "It keeps the GPU busy and greatly increases throughput."),
Q("Why is the OpenAI-compatible API important for open-model serving?", ["It's required by law", "Apps can switch between Ollama, vLLM and hosted APIs by changing base_url and model name", "It makes models smarter", "It removes the need for GPUs"], 1, "A common API makes backends interchangeable."),
], [
R("Ollama documentation", "https://docs.ollama.com/", "docs"),
R("vLLM documentation", "https://docs.vllm.ai/", "docs"),
R("vLLM blog - Easy, fast and cheap LLM serving with PagedAttention", "https://blog.vllm.ai/2023/06/20/vllm.html", "article"),
R("Hugging Face - Open LLM model hub (filter by GGUF/AWQ)", "https://huggingface.co/models?pipeline_tag=text-generation", "docs"),
]),
]

MODULE = M(
    "m11-fine-tuning", 11, "Fine-tuning & Open Models", "Advanced", 2.5,
    "Decide when fine-tuning is the right tool, build high-quality datasets, and adapt open models efficiently with LoRA and QLoRA. Quantize and serve models yourself with Ollama and vLLM behind an OpenAI-compatible API.",
    [
        "Choose correctly between prompting, RAG and fine-tuning for a use case",
        "Build, clean and split chat-format SFT and preference datasets",
        "Explain LoRA/QLoRA mathematically and estimate GPU memory needs",
        "Fine-tune and evaluate an open model with TRL + PEFT, then merge and export it",
        "Quantize and serve open models locally (Ollama) and at scale (vLLM)",
    ],
    lessons,
    ("Fine-tuned Ticket Classifier: Small Model vs Frontier API", r"""
Prove the business case for fine-tuning end to end:

1. **Dataset**: 1,000+ support tickets (synthetic with personas + hand-written edge cases), 6-10 categories + priority, cleaned and split, with a dataset card.
2. **Baselines**: a small open instruct model prompted, and a frontier API model prompted with few-shot examples.
3. **Fine-tune** the small model with QLoRA (TRL + PEFT) on Colab/Kaggle; run at least two ablations (rank, epochs or data size).
4. **Quantize** the merged model to GGUF Q4_K_M and serve it with Ollama (or AWQ with vLLM).
5. **Evaluate** all variants on the same test set: accuracy, macro-F1, valid-JSON rate, p50/p95 latency, cost per 1,000 tickets.
6. **Publish** the adapter/model on the Hugging Face Hub with a model card, and a README with the comparison table and a recommendation.

**Stretch:** add DPO on 200 preference pairs to fix a style issue (e.g. over-long justifications) and measure the effect.
"""),
)
