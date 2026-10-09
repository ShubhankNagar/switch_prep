from ai1_common import L, Q, R, M

lessons = []

lessons.append(L("m05-l1-neurons", "Neurons, Activations & Neural Networks", 45, r"""
## From logistic regression to neural networks

You already know a neural network's building block. A single **neuron** computes a weighted sum of its inputs plus a bias, then applies an **activation function**:

`output = activation(w1*x1 + w2*x2 + ... + wn*xn + b) = activation(w . x + b)`

With a sigmoid activation, that's exactly logistic regression. A neural network stacks many neurons into **layers**, and layers into a **network**. Each layer learns new features from the previous layer's outputs — edges -> shapes -> objects in images; characters -> words -> meaning in text. That automatic feature learning is why deep learning beat hand-engineered features on images, audio and language.

## A layer is a matrix multiplication

A layer of `m` neurons, each looking at `n` inputs, is a weight matrix `W` of shape `(n, m)` plus a bias vector `b` of shape `(m,)`. For a batch of inputs `X` of shape `(batch, n)`:

`H = activation(X @ W + b)`  -> shape `(batch, m)`

```python
import numpy as np
rng = np.random.default_rng(0)

X = rng.normal(size=(4, 3))            # 4 samples, 3 features
W1 = rng.normal(size=(3, 5)) * 0.5     # hidden layer: 5 neurons
b1 = np.zeros(5)
W2 = rng.normal(size=(5, 1)) * 0.5     # output layer: 1 neuron
b2 = np.zeros(1)

def relu(z):
    return np.maximum(0, z)

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

H = relu(X @ W1 + b1)        # (4, 5)  hidden representation
out = sigmoid(H @ W2 + b2)   # (4, 1)  probability per sample
print(out.ravel())
```

That is a complete **forward pass** of a 2-layer **multi-layer perceptron (MLP)**. Training (next lessons) adjusts `W1, b1, W2, b2` to minimize a loss.

## Why activations?

Without non-linear activations, stacked layers collapse into a single linear transformation (Module 3). Activations let networks bend decision boundaries into any shape. The **Universal Approximation Theorem** says an MLP with one large enough hidden layer can approximate any continuous function — depth makes it far more efficient.

### Common activation functions

```python
def tanh(z):
    return np.tanh(z)                         # (-1, 1), zero-centred

def leaky_relu(z, a=0.01):
    return np.where(z > 0, z, a * z)          # small slope for negatives

def gelu(z):                                  # used in BERT/GPT (approximation)
    return 0.5 * z * (1 + np.tanh(np.sqrt(2 / np.pi) * (z + 0.044715 * z ** 3)))

def softmax(z):
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)
```

| Activation | Where used | Notes |
|---|---|---|
| ReLU `max(0, z)` | hidden layers (default) | cheap, no vanishing gradient for z > 0; neurons can "die" |
| GELU / SiLU (Swish) | transformers, modern nets | smooth ReLU-like curves |
| Sigmoid | binary output | squashes to (0, 1); vanishes in deep hidden layers |
| Softmax | multi-class output | turns scores into a probability distribution |
| Tanh | RNNs, older nets | zero-centred version of sigmoid |
| None (identity) | regression output | output any real number |

## Output layers and losses go together

| Task | Output layer | Loss |
|---|---|---|
| Regression | 1 neuron, no activation | MSE |
| Binary classification | 1 neuron, sigmoid | binary cross-entropy |
| Multi-class (k classes) | k neurons, softmax | cross-entropy |
| Next-token prediction (LLM) | vocab-size neurons, softmax | cross-entropy |

In PyTorch you usually output raw scores (**logits**) and use a loss that applies sigmoid/softmax internally for numerical stability (`BCEWithLogitsLoss`, `CrossEntropyLoss`).

## Counting parameters

Each dense layer has `n_in * n_out` weights plus `n_out` biases.

```python
layers = [784, 256, 128, 10]          # MNIST MLP
params = sum(a * b + b for a, b in zip(layers[:-1], layers[1:]))
print(params)                          # 235,146
```

GPT-3 has 175 billion parameters; the same formula, at a vastly bigger scale. Parameter count drives memory: at 4 bytes per float32 parameter, 7 billion parameters need ~28 GB just to store the weights — which is why quantization (8-bit, 4-bit) matters for running LLMs locally.

## The same network in PyTorch

```python
import torch
import torch.nn as nn

model = nn.Sequential(
    nn.Linear(3, 5),     # W1, b1
    nn.ReLU(),
    nn.Linear(5, 1),     # W2, b2
    nn.Sigmoid(),
)
x = torch.randn(4, 3)
print(model(x).shape)                                  # torch.Size([4, 1])
print(sum(p.numel() for p in model.parameters()))      # 3*5+5 + 5*1+1 = 26
```

`nn.Linear` holds the weight matrix and bias; PyTorch initializes them sensibly and tracks gradients for you.

## Width, depth and intuition

- **Width** (neurons per layer): capacity to represent many features at once.
- **Depth** (number of layers): ability to compose features hierarchically.
- Bigger networks fit more complex functions but need more data, compute and regularization.

Try the TensorFlow Playground (linked below): add hidden neurons and watch a network learn to separate a spiral dataset that a linear model cannot.

## Key takeaways

- Neuron = weighted sum + bias + activation; a layer = `activation(X @ W + b)`.
- Non-linear activations (ReLU, GELU) give networks their power; output activation and loss depend on the task.
- Parameters = `n_in * n_out + n_out` per dense layer; parameter count determines memory.
- `nn.Sequential` + `nn.Linear` builds the same MLP in a few lines.
""", r"""
**Task: Forward pass by hand.**

1. In NumPy, implement a 3-layer MLP (input 4 -> 8 -> 6 -> 3) with ReLU hidden layers and softmax output. Run a batch of 10 random inputs and verify each output row sums to 1.
2. Count its parameters by formula and verify against an equivalent `nn.Sequential` model.
3. Plot ReLU, sigmoid, tanh and GELU on [-4, 4] in one figure.
4. In the TensorFlow Playground, find the smallest network that separates the spiral dataset. Note the layers/neurons you needed.
5. Estimate the memory needed to store a 70B-parameter model in float32, bfloat16 and 4-bit.
""", [
    Q("Why are non-linear activation functions necessary in neural networks?", ["They speed up matrix multiplication", "Without them, stacked layers reduce to a single linear function", "They reduce the number of parameters", "They normalize the input data"], 1, "A composition of linear maps is linear; non-linearities let the network represent complex functions."),
    Q("How many parameters does nn.Linear(100, 50) have?", ["150", "5000", "5050", "5100"], 2, "100*50 weights plus 50 biases = 5050."),
    Q("Which output layer and loss suit a 10-class image classifier?", ["1 neuron + MSE", "10 neurons + softmax/cross-entropy", "10 neurons + sigmoid/MSE", "2 neurons + ReLU"], 1, "Multi-class classification uses one logit per class, softmax, and cross-entropy loss (combined in PyTorch's CrossEntropyLoss)."),
], [
    R("3Blue1Brown: But what is a neural network?", "https://www.youtube.com/watch?v=aircAruvnKk", "video"),
    R("TensorFlow Playground (interactive)", "https://playground.tensorflow.org/", "article"),
    R("Michael Nielsen: Neural Networks and Deep Learning (free book)", "http://neuralnetworksanddeeplearning.com/", "book"),
]))

lessons.append(L("m05-l2-backprop-autograd", "Backpropagation & PyTorch Autograd", 50, r"""
## The question backprop answers

A network might have millions of weights. To train it with gradient descent, we need `dLoss/dw` for **every** weight. Computing each separately would be hopelessly slow. **Backpropagation** computes all of them in one backward sweep using the chain rule, reusing intermediate results. Its cost is roughly the same as one forward pass.

## A tiny network, by hand

Network: `z = w*x + b`, `a = sigmoid(z)`, `L = (a - y)^2`. Take x = 2, y = 1, w = 0.5, b = 0.

**Forward pass** (compute and remember each value):

```
z = 0.5*2 + 0 = 1.0
a = sigmoid(1.0) = 0.731
L = (0.731 - 1)^2 = 0.072
```

**Backward pass** (chain rule from the loss backwards):

```
dL/da = 2(a - y)            = -0.538
da/dz = a(1 - a)            =  0.197
dL/dz = dL/da * da/dz       = -0.106
dL/dw = dL/dz * x           = -0.212
dL/db = dL/dz * 1           = -0.106
```

Both gradients are negative, so increasing w and b reduces the loss. Notice `dL/dz` was computed once and reused for both parameters — that reuse is the efficiency of backprop. In a deep network, each layer receives the gradient from the layer above (the "upstream gradient"), multiplies by its own local derivative, and passes the result down.

## The computational graph

Every operation becomes a node in a graph. Each node knows how to compute its output (forward) and its local derivative (backward):

| Operation | Local gradient rule |
|---|---|
| `c = a + b` | passes gradient unchanged to a and b |
| `c = a * b` | grad_a = grad_c * b, grad_b = grad_c * a |
| `c = relu(a)` | grad_a = grad_c if a > 0 else 0 |
| `C = A @ B` | grad_A = grad_C @ B.T, grad_B = A.T @ grad_C |

## Tensors in PyTorch

A `torch.Tensor` is like a NumPy array with two superpowers: it can run on a GPU and it can track gradients.

```python
import torch

t = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
print(t.shape, t.dtype)          # torch.Size([2, 2]) torch.float32
print(t @ t, t * 2, t.mean())    # same operations as NumPy
z = torch.zeros(3, 4); r = torch.randn(2, 3)
n = t.numpy(); back = torch.from_numpy(n)   # convert to/from NumPy
print(t.view(4), t.reshape(1, 4), t.unsqueeze(0).shape)   # reshaping
```

## Autograd: automatic backprop

Set `requires_grad=True` and PyTorch records every operation. Calling `.backward()` on a scalar loss runs backprop through the recorded graph and stores gradients in `.grad`.

```python
x = torch.tensor(2.0)
y = torch.tensor(1.0)
w = torch.tensor(0.5, requires_grad=True)
b = torch.tensor(0.0, requires_grad=True)

a = torch.sigmoid(w * x + b)
loss = (a - y) ** 2
loss.backward()

print(w.grad, b.grad)     # tensor(-0.2115) tensor(-0.1058) - matches our hand calculation
```

## Training with raw autograd

Here's linear regression trained with only tensors and autograd — no `nn` module yet:

```python
torch.manual_seed(0)
X = torch.rand(100, 1) * 10
y = 3 * X + 2 + torch.randn(100, 1)

w = torch.zeros(1, requires_grad=True)
b = torch.zeros(1, requires_grad=True)
lr = 0.01

for epoch in range(1000):
    y_hat = X * w + b
    loss = ((y_hat - y) ** 2).mean()

    loss.backward()               # compute gradients
    with torch.no_grad():         # update without recording these ops in the graph
        w -= lr * w.grad
        b -= lr * b.grad
    w.grad.zero_()                # IMPORTANT: gradients accumulate by default
    b.grad.zero_()

print(w.item(), b.item())         # ~3 and ~2
```

Three details every PyTorch user must know:

1. **Gradients accumulate.** Each `.backward()` *adds* to `.grad`. Forgetting to zero them is a classic bug (the optimizer's `zero_grad()` does this in the standard loop).
2. **`torch.no_grad()`** disables graph recording — use it for weight updates and for inference/evaluation (saves memory and time).
3. **`.item()`** extracts a Python number from a one-element tensor; `.detach()` gives a tensor cut off from the graph.

## Build your own autograd (micrograd idea)

To truly understand backprop, implement a scalar autograd engine. Here's the core of the idea, inspired by Karpathy's micrograd:

```python
class Value:
    def __init__(self, data, parents=()):
        self.data, self.grad = data, 0.0
        self._parents, self._backward = parents, lambda: None

    def __add__(self, other):
        out = Value(self.data + other.data, (self, other))
        def _backward():
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        out = Value(self.data * other.data, (self, other))
        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def backward(self):
        order, seen = [], set()
        def visit(v):                      # topological sort of the graph
            if v not in seen:
                seen.add(v)
                for p in v._parents:
                    visit(p)
                order.append(v)
        visit(self)
        self.grad = 1.0
        for v in reversed(order):
            v._backward()

a, b = Value(3.0), Value(4.0)
c = a * b + a          # c = ab + a
c.backward()
print(a.grad, b.grad)  # dc/da = b + 1 = 5.0, dc/db = a = 3.0
```

Notice the Python features from Module 1 at work: dunder methods for operators and closures storing each node's backward function. PyTorch does the same thing for tensors, in C++ and CUDA.

## Vanishing and exploding gradients

Backprop multiplies many local derivatives. If they're mostly < 1, gradients shrink exponentially in early layers (**vanishing**); if > 1, they blow up (**exploding**). Remedies you'll meet: ReLU-family activations, careful weight initialization (He/Xavier), normalization layers, residual connections (the "skip" connections in ResNets and transformers), and gradient clipping.

## Key takeaways

- Backprop = chain rule applied backwards through the computational graph, reusing intermediate gradients.
- PyTorch tensors track operations when `requires_grad=True`; `loss.backward()` fills `.grad`.
- Zero gradients each step, update weights under `torch.no_grad()`.
- Vanishing/exploding gradients are tamed by ReLU, good init, normalization and residual connections.
""", r"""
**Task: Backprop three ways.**

1. By hand, compute the forward and backward pass for `L = (relu(w1*x + b1) * w2 - y)^2` with x=1, y=2, w1=0.5, b1=0.5, w2=1.5.
2. Verify your gradients with PyTorch autograd.
3. Extend the `Value` class with `__pow__`, `relu()` and `__sub__`, and verify gradients on the same expression.
4. Train linear regression with raw autograd, then deliberately remove the `grad.zero_()` lines and describe what happens to training.
5. Watch Karpathy's micrograd video and use your `Value` class to train a 2-layer neuron network on 4 hand-made data points.
""", [
    Q("What happens if you call loss.backward() in a loop without zeroing gradients?", ["Gradients are overwritten each time", "Gradients accumulate (sum) across iterations", "PyTorch raises an error", "Weights reset to zero"], 1, "PyTorch adds new gradients into .grad by default, so you must zero them each step (optimizer.zero_grad())."),
    Q("Why wrap evaluation code in `torch.no_grad()`?", ["To make predictions more accurate", "To skip building the computational graph, saving memory and time", "To enable dropout", "To move tensors to the GPU"], 1, "No gradients are needed for inference, so disabling graph recording reduces memory use and speeds things up."),
    Q("For c = a * b, what is the gradient flowing to a during backprop?", ["grad_c", "grad_c * b", "grad_c * a", "b / grad_c"], 1, "The local derivative dc/da = b, multiplied by the upstream gradient grad_c."),
], [
    R("Andrej Karpathy: Neural Networks Zero to Hero - micrograd", "https://www.youtube.com/watch?v=VMj-3S1tku0", "video"),
    R("PyTorch: A Gentle Introduction to torch.autograd", "https://pytorch.org/tutorials/beginner/blitz/autograd_tutorial.html", "docs"),
    R("CS231n: Backpropagation, intuitions", "https://cs231n.github.io/optimization-2/", "article"),
]))

lessons.append(L("m05-l3-training-loop", "The PyTorch Training Loop: Modules, Datasets & DataLoaders", 55, r"""
## The four ingredients

Every PyTorch training script has the same four pieces:

1. **Data:** a `Dataset` (how to get one example) and a `DataLoader` (batching, shuffling).
2. **Model:** a class extending `nn.Module`.
3. **Loss function:** e.g. `nn.CrossEntropyLoss`.
4. **Optimizer:** e.g. `torch.optim.AdamW`, which updates the weights.

The loop itself never really changes — learn it once and you can read almost any PyTorch code, including LLM fine-tuning scripts.

## Defining a model with nn.Module

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class MLP(nn.Module):
    def __init__(self, in_dim=784, hidden=256, n_classes=10):
        super().__init__()                    # like calling super() in a Java constructor
        self.fc1 = nn.Linear(in_dim, hidden)
        self.fc2 = nn.Linear(hidden, hidden)
        self.out = nn.Linear(hidden, n_classes)

    def forward(self, x):                     # defines the forward pass
        x = x.flatten(start_dim=1)            # (B, 1, 28, 28) -> (B, 784)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.out(x)                    # raw logits; no softmax here

model = MLP()
print(model)
```

You implement `forward`; PyTorch derives the backward pass automatically. Layers assigned as attributes are registered, so `model.parameters()` finds all their weights. Call the model as `model(x)` (not `model.forward(x)`) so PyTorch's hooks run.

## Datasets and DataLoaders

A `Dataset` is like a Java `List<Example>`: it implements `__len__` and `__getitem__`. A `DataLoader` wraps it to produce shuffled mini-batches, optionally in parallel worker processes.

```python
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import datasets, transforms

transform = transforms.Compose([
    transforms.ToTensor(),                        # PIL image -> tensor in [0, 1], shape (1, 28, 28)
    transforms.Normalize((0.1307,), (0.3081,)),   # standardize with MNIST mean/std
])
full_train = datasets.MNIST("data", train=True, download=True, transform=transform)
test_ds = datasets.MNIST("data", train=False, download=True, transform=transform)
train_ds, val_ds = random_split(full_train, [55_000, 5_000],
                                generator=torch.Generator().manual_seed(42))

train_loader = DataLoader(train_ds, batch_size=128, shuffle=True, num_workers=2)
val_loader = DataLoader(val_ds, batch_size=512)
test_loader = DataLoader(test_ds, batch_size=512)

images, labels = next(iter(train_loader))
print(images.shape, labels.shape)        # torch.Size([128, 1, 28, 28]) torch.Size([128])
```

A custom dataset, e.g. for your own tabular data:

```python
class TabularDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]
```

## The training loop

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
model = MLP().to(device)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

def train_one_epoch(model, loader):
    model.train()                                   # enable dropout/batchnorm training mode
    total_loss = 0.0
    for X, y in loader:
        X, y = X.to(device), y.to(device)
        logits = model(X)                           # 1. forward
        loss = loss_fn(logits, y)                   # 2. loss
        optimizer.zero_grad()                       # 3. clear old gradients
        loss.backward()                             # 4. backprop
        optimizer.step()                            # 5. update weights
        total_loss += loss.item() * X.size(0)
    return total_loss / len(loader.dataset)

@torch.no_grad()
def evaluate(model, loader):
    model.eval()                                    # inference mode for dropout/batchnorm
    correct, total, loss_sum = 0, 0, 0.0
    for X, y in loader:
        X, y = X.to(device), y.to(device)
        logits = model(X)
        loss_sum += loss_fn(logits, y).item() * X.size(0)
        correct += (logits.argmax(dim=1) == y).sum().item()
        total += y.size(0)
    return loss_sum / total, correct / total

for epoch in range(1, 6):
    train_loss = train_one_epoch(model, train_loader)
    val_loss, val_acc = evaluate(model, val_loader)
    print(f"epoch {epoch}: train_loss={train_loss:.4f} val_loss={val_loss:.4f} val_acc={val_acc:.4f}")

print("test (loss, acc):", evaluate(model, test_loader))   # ~98% accuracy
```

Memorize the five steps inside the loop: **forward, loss, zero_grad, backward, step**.

### `model.train()` vs `model.eval()`

Some layers behave differently during training and inference: dropout randomly zeroes activations only during training; batch normalization uses batch statistics during training and running averages during evaluation. Forgetting `model.eval()` gives noisy, wrong evaluation numbers — a common interview question.

## Making predictions

```python
model.eval()
with torch.no_grad():
    logits = model(images[:5].to(device))
    probs = torch.softmax(logits, dim=1)
    print(probs.argmax(dim=1), labels[:5])
```

## Saving and loading

```python
torch.save(model.state_dict(), "mlp_mnist.pt")       # save weights only (recommended)

model2 = MLP().to(device)
model2.load_state_dict(torch.load("mlp_mnist.pt", map_location=device))
model2.eval()
```

`state_dict` is a dictionary mapping layer names to tensors. Save the optimizer's state too if you want to resume training (checkpointing).

## Higher-level helpers

Libraries like **PyTorch Lightning**, Hugging Face **Accelerate** and the Hugging Face **Trainer** wrap this loop (logging, multi-GPU, mixed precision, checkpointing) — similar to how Spring Boot wraps boilerplate. Learn the raw loop first so you can debug when the abstraction leaks.

## Debugging checklist

- Print shapes at each step of `forward`.
- **Overfit a single batch first:** a correct model should reach ~0 loss on one batch. If it can't, there's a bug.
- Check the initial loss: for 10 balanced classes it should be about `ln(10) = 2.30`.
- Loss is `nan`? Lower the learning rate; check for division by zero or log of zero.
- Labels for `CrossEntropyLoss` must be class indices (`long`), not one-hot vectors, and logits must not already be softmaxed.

## Key takeaways

- `nn.Module`: define layers in `__init__`, computation in `forward`.
- `Dataset` returns one example; `DataLoader` batches and shuffles.
- Loop: forward -> loss -> zero_grad -> backward -> step; evaluate under `model.eval()` + `torch.no_grad()`.
- Save `state_dict`; debug by overfitting one batch and checking the initial loss.
""", r"""
**Task: Fashion-MNIST classifier.**

1. Load `torchvision.datasets.FashionMNIST` with a train/val/test split.
2. Build an MLP as an `nn.Module` with two hidden layers.
3. Before training, check that the initial loss is about 2.30 and overfit a single batch to near-zero loss.
4. Train for 10 epochs with AdamW; log train loss, val loss and val accuracy per epoch and plot curves.
5. Evaluate on the test set, print a confusion matrix (use `sklearn.metrics.confusion_matrix`), and display 8 misclassified images with predicted/true labels.
6. Save the best model (by val accuracy) with `state_dict` and reload it to verify identical test accuracy.

Run it on Google Colab with a GPU if your laptop is slow.
""", [
    Q("What is the correct order of operations inside a PyTorch training step?", ["backward, forward, step, zero_grad", "forward, loss, zero_grad, backward, step", "step, forward, loss, backward", "zero_grad, step, forward, backward"], 1, "Compute predictions and loss, clear old gradients, backpropagate, then update weights with the optimizer."),
    Q("Why must you call model.eval() before evaluating?", ["It moves the model to the CPU", "It switches layers like dropout and batch norm to inference behaviour", "It freezes the learning rate", "It is required to save the model"], 1, "Dropout must be disabled and batch norm must use running statistics during evaluation."),
    Q("What should the target tensor look like for nn.CrossEntropyLoss in a 10-class problem?", ["One-hot float vectors of length 10", "Class indices of dtype long, shape (batch,)", "Softmax probabilities", "Strings with class names"], 1, "CrossEntropyLoss expects raw logits (batch, classes) and integer class indices (batch,)."),
], [
    R("PyTorch: Learn the Basics (official tutorial series)", "https://pytorch.org/tutorials/beginner/basics/intro.html", "docs"),
    R("Daniel Bourke: Learn PyTorch for Deep Learning (free book/course)", "https://www.learnpytorch.io/", "course"),
    R("fast.ai: Practical Deep Learning for Coders", "https://course.fast.ai/", "course"),
]))

lessons.append(L("m05-l4-optimization-regularization", "Optimizers, Regularization & Training Tricks", 50, r"""
## Making training work in practice

Getting a network to train well is part science, part craft. This lesson covers the toolbox: optimizers, learning-rate schedules, initialization, normalization and regularization. These same tools are used to train LLMs.

## Optimizers

All optimizers live in `torch.optim` and share the interface `optimizer.zero_grad()` / `optimizer.step()`.

### SGD with momentum

Plain SGD: `w = w - lr * grad`. **Momentum** keeps a running velocity, like a ball rolling downhill, so it speeds through flat regions and smooths oscillation:

```
v = beta * v + grad
w = w - lr * v
```

```python
import torch
opt = torch.optim.SGD(model.parameters(), lr=0.05, momentum=0.9, nesterov=True)
```

### Adam and AdamW

**Adam** keeps per-parameter running averages of gradients (momentum) and of squared gradients, giving each parameter its own adaptive step size. It works well with little tuning. **AdamW** fixes how weight decay is applied and is the default for transformers.

```python
opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01, betas=(0.9, 0.999))
```

Rule of thumb: start with AdamW (lr 1e-3 for small nets, 1e-4 to 3e-4 for transformers; 1e-5 to 5e-5 when fine-tuning pretrained models). Well-tuned SGD+momentum is still common in computer vision.

## Learning-rate schedules

A high learning rate early makes fast progress; a lower one later fine-tunes. Common schedules:

- **Step decay:** multiply by 0.1 every N epochs.
- **Cosine annealing:** smoothly decays following a cosine curve.
- **Warmup + decay:** start tiny, ramp up for the first few hundred/thousand steps, then decay — standard for transformers because Adam's statistics are unreliable at the start.
- **OneCycle:** ramp up then down; popularized by fast.ai.

```python
from torch.optim.lr_scheduler import OneCycleLR, CosineAnnealingLR

opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
sched = OneCycleLR(opt, max_lr=1e-3, total_steps=epochs * len(train_loader))
for epoch in range(epochs):
    for X, y in train_loader:
        loss = loss_fn(model(X), y)
        opt.zero_grad(); loss.backward(); opt.step()
        sched.step()                     # per-batch schedulers step every batch
```

**Learning-rate finder:** train briefly while exponentially increasing the lr; pick a value a bit below where the loss decreases fastest (before it explodes).

## Weight initialization

If weights start too large, activations explode; too small, they vanish. **Xavier/Glorot** init suits tanh/sigmoid; **He/Kaiming** init suits ReLU. PyTorch's `nn.Linear` and `nn.Conv2d` already use a sensible Kaiming-style default, so you rarely need to change it:

```python
def init_weights(m):
    if isinstance(m, torch.nn.Linear):
        torch.nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
        torch.nn.init.zeros_(m.bias)
model.apply(init_weights)
```

## Normalization layers

Normalization keeps activations in a healthy range, making training faster and more stable.

- **BatchNorm:** normalizes each feature across the batch; standard in CNNs. Behaves differently in train/eval mode.
- **LayerNorm:** normalizes across the features of each example; independent of batch size — the standard in transformers (with RMSNorm, a simpler variant used in many modern LLMs).

```python
block = torch.nn.Sequential(
    torch.nn.Linear(256, 256),
    torch.nn.LayerNorm(256),
    torch.nn.GELU(),
)
```

## Regularization: fighting overfitting

### Weight decay (L2)

Penalizes large weights, nudging toward simpler functions. Set via `weight_decay` in AdamW.

### Dropout

During training, randomly zero a fraction `p` of activations, forcing the network not to rely on any single neuron — like training an ensemble of sub-networks. Automatically disabled by `model.eval()`.

```python
class RegularizedMLP(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(784, 512), torch.nn.ReLU(), torch.nn.Dropout(0.3),
            torch.nn.Linear(512, 256), torch.nn.ReLU(), torch.nn.Dropout(0.3),
            torch.nn.Linear(256, 10),
        )
    def forward(self, x):
        return self.net(x)
```

### Data augmentation

Create varied training examples: random crops, flips, rotations, colour jitter for images; synonym replacement or back-translation for text. Often the most effective regularizer for vision.

```python
from torchvision import transforms
train_tf = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomCrop(32, padding=4),
    transforms.ToTensor(),
])
```

### Early stopping

Track validation loss; stop when it hasn't improved for `patience` epochs and restore the best weights.

```python
import copy
best_loss, best_state, patience, bad_epochs = float("inf"), None, 3, 0
for epoch in range(100):
    train_one_epoch(model, train_loader)
    val_loss, _ = evaluate(model, val_loader)
    if val_loss < best_loss:
        best_loss, best_state, bad_epochs = val_loss, copy.deepcopy(model.state_dict()), 0
    else:
        bad_epochs += 1
        if bad_epochs >= patience:
            print(f"early stop at epoch {epoch}")
            break
model.load_state_dict(best_state)
```

### Label smoothing

Instead of training toward 100% confidence on the true class, target e.g. 90%, spreading the rest over other classes. Reduces over-confidence: `nn.CrossEntropyLoss(label_smoothing=0.1)`.

## Gradient clipping

Caps the gradient norm to prevent exploding updates — standard for RNNs and transformers:

```python
loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
optimizer.step()
```

## A practical recipe (Karpathy's advice, condensed)

1. Get a simple baseline working end to end; verify initial loss and overfit one batch.
2. Overfit the training set with a big enough model (low bias first).
3. Then regularize: more data, augmentation, dropout, weight decay, early stopping.
4. Tune the learning rate first, then other hyperparameters; change one thing at a time.
5. Always plot training and validation curves.

## Key takeaways

- AdamW is the default optimizer; SGD+momentum is still strong for vision.
- Use LR schedules (warmup + cosine/OneCycle); the learning rate is the most important hyperparameter.
- BatchNorm for CNNs, LayerNorm/RMSNorm for transformers.
- Regularize with weight decay, dropout, augmentation, early stopping, label smoothing; clip gradients for stability.
""", r"""
**Task: Regularization experiments.** Using your Fashion-MNIST setup:

1. Train a large MLP (3 x 1024 hidden) without regularization for 30 epochs; plot train vs val loss and identify overfitting.
2. Add dropout (0.3), weight decay (0.01) and early stopping (patience 3). Compare curves and final test accuracy.
3. Compare optimizers: SGD (lr 0.1), SGD+momentum (0.9), Adam, AdamW — same epochs; plot val accuracy per epoch for each.
4. Add a OneCycleLR schedule to the best optimizer and report the change.
5. Summarize results in a Markdown table (config, best val acc, test acc, epochs).
""", [
    Q("What does dropout do during training?", ["Removes layers permanently", "Randomly zeroes a fraction of activations so the network can't rely on specific neurons", "Lowers the learning rate", "Drops training samples with high loss"], 1, "Dropout randomly disables activations each step, acting like an ensemble of sub-networks; it is turned off in eval mode."),
    Q("Which normalization layer is standard in transformer models?", ["BatchNorm", "LayerNorm (or RMSNorm)", "InstanceNorm", "No normalization"], 1, "LayerNorm normalizes each token's features independently of the batch, which suits variable-length sequences."),
    Q("Why use learning-rate warmup when training transformers?", ["To save memory", "Early adaptive-optimizer statistics are unreliable, so large initial steps can destabilize training", "To increase the batch size", "Warmup is only used for CNNs"], 1, "Starting with small learning rates and ramping up avoids destructive early updates."),
], [
    R("Andrej Karpathy: A Recipe for Training Neural Networks", "https://karpathy.github.io/2019/04/25/recipe/", "article"),
    R("Dive into Deep Learning (free interactive book): Optimization", "https://d2l.ai/chapter_optimization/index.html", "book"),
    R("DeepLearning.AI: Improving Deep Neural Networks (Coursera)", "https://www.coursera.org/learn/deep-neural-network", "course"),
]))

lessons.append(L("m05-l5-cnns", "Convolutional Neural Networks (CNNs)", 50, r"""
## Why MLPs struggle with images

An MLP flattens a 224x224 RGB image into 150,528 numbers and connects each to every hidden neuron — millions of weights in the first layer, and no notion that neighbouring pixels are related. Move a cat 10 pixels right and the MLP sees a completely different input. **Convolutional Neural Networks** fix this with two ideas:

1. **Local connectivity:** each neuron looks only at a small patch (e.g. 3x3).
2. **Weight sharing:** the same small filter slides across the whole image, detecting the same pattern anywhere.

## The convolution operation

A **filter (kernel)** is a small grid of weights. Slide it over the image; at each position, compute the dot product of the filter with the patch underneath. The result is a **feature map** showing where the pattern appears.

```python
import torch
import torch.nn.functional as F

img = torch.zeros(1, 1, 6, 6)
img[..., :, 3:] = 1.0                       # left half dark, right half bright

vertical_edge = torch.tensor([[[[-1., 0., 1.],
                                [-1., 0., 1.],
                                [-1., 0., 1.]]]])
out = F.conv2d(img, vertical_edge)
print(out.squeeze())       # strong response only where dark meets bright
```

Here we hand-wrote an edge detector. A CNN **learns** its filters by backprop: early layers learn edges and colours, middle layers textures and parts, deep layers whole objects.

### Key hyperparameters

- **Kernel size:** usually 3x3.
- **Stride:** step size of the slide; stride 2 halves the spatial size.
- **Padding:** add zeros around the border to preserve size (`padding=1` with 3x3 kernels).
- **Channels:** input channels (3 for RGB) and output channels (number of filters learned).

Output size: `out = (in + 2*padding - kernel) / stride + 1`.

```python
conv = torch.nn.Conv2d(in_channels=3, out_channels=16, kernel_size=3, padding=1)
x = torch.randn(8, 3, 32, 32)          # (batch, channels, height, width)
print(conv(x).shape)                   # torch.Size([8, 16, 32, 32])
print(sum(p.numel() for p in conv.parameters()))   # 16*3*3*3 + 16 = 448 parameters
```

448 parameters versus millions for an equivalent dense layer — that's weight sharing.

## Pooling

**Max pooling** takes the maximum over small windows (e.g. 2x2), halving height and width. It reduces computation and makes features robust to small shifts.

```python
pool = torch.nn.MaxPool2d(2)
print(pool(torch.randn(8, 16, 32, 32)).shape)   # torch.Size([8, 16, 16, 16])
```

## A complete CNN for CIFAR-10

CIFAR-10: 60,000 32x32 colour images in 10 classes (plane, car, bird, cat, ...). The classic pattern: [conv -> norm -> ReLU] blocks with pooling, channels increasing as spatial size shrinks, then a classifier head.

```python
import torch.nn as nn

class SmallCNN(nn.Module):
    def __init__(self, n_classes=10):
        super().__init__()
        def block(cin, cout):
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, padding=1), nn.BatchNorm2d(cout), nn.ReLU(),
                nn.Conv2d(cout, cout, 3, padding=1), nn.BatchNorm2d(cout), nn.ReLU(),
                nn.MaxPool2d(2),
            )
        self.features = nn.Sequential(
            block(3, 32),     # 32x32 -> 16x16
            block(32, 64),    # 16x16 -> 8x8
            block(64, 128),   # 8x8   -> 4x4
        )
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),     # global average pool -> (B, 128, 1, 1)
            nn.Flatten(),
            nn.Dropout(0.3),
            nn.Linear(128, n_classes),
        )
    def forward(self, x):
        return self.head(self.features(x))

model = SmallCNN()
print(model(torch.randn(4, 3, 32, 32)).shape)   # torch.Size([4, 10])
```

Train it with exactly the same loop as the previous lessons plus augmentation (random crop + flip) — you should reach ~85-90% test accuracy, versus ~50% for an MLP.

## Landmark architectures (know the names)

- **LeNet (1998):** digits; the original CNN.
- **AlexNet (2012):** won ImageNet by a huge margin using GPUs and ReLU, kicking off the deep learning boom.
- **VGG (2014):** deep stacks of 3x3 convs.
- **ResNet (2015):** **residual (skip) connections** `out = F(x) + x` let gradients flow through 100+ layers. The same trick appears in every transformer block.
- **EfficientNet, ConvNeXt:** modern efficient CNNs.
- **Vision Transformers (ViT, 2020):** split images into patches and treat them like tokens — transformers now compete with CNNs for vision, and power multimodal LLMs.

```python
class ResidualBlock(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.conv1 = nn.Conv2d(c, c, 3, padding=1); self.bn1 = nn.BatchNorm2d(c)
        self.conv2 = nn.Conv2d(c, c, 3, padding=1); self.bn2 = nn.BatchNorm2d(c)
    def forward(self, x):
        out = torch.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return torch.relu(out + x)             # the skip connection
```

## Transfer learning: don't train from scratch

Models pretrained on ImageNet (1.2M images) already know general visual features. For your own task with a few thousand images, reuse them:

```python
from torchvision import models

weights = models.ResNet18_Weights.DEFAULT
backbone = models.resnet18(weights=weights)
for p in backbone.parameters():
    p.requires_grad = False                         # freeze pretrained layers
backbone.fc = nn.Linear(backbone.fc.in_features, 5) # new head for 5 classes (trainable)
preprocess = weights.transforms()                   # matching resize/normalize
```

Train only the new head first; optionally unfreeze deeper layers later with a small learning rate (**fine-tuning**). This pretrain-then-fine-tune pattern is exactly how LLMs are adapted to new tasks.

## Beyond classification

CNN backbones power object detection (YOLO), segmentation (U-Net), face recognition, medical imaging, and the image encoders in multimodal models.

## Key takeaways

- Convolutions use small shared filters sliding over the image: few parameters, translation-aware.
- Output size = `(in + 2p - k)/s + 1`; pooling downsamples.
- Typical CNN: conv-BN-ReLU blocks, channels up, spatial size down, global pool, linear head.
- Residual connections enable very deep networks; transfer learning beats training from scratch on small data.
""", r"""
**Task: CIFAR-10 classifier.**

1. Load CIFAR-10 with torchvision; use random crop (padding 4) and horizontal flip augmentation for training only.
2. Train the `SmallCNN` from the lesson for 15-20 epochs on a Colab GPU with AdamW + OneCycleLR. Target >= 85% test accuracy.
3. Train an MLP on the same data for comparison and report the gap.
4. Visualize the 32 filters of the first conv layer as small images (normalize each to [0,1]).
5. Transfer learning: download a small dataset (e.g. torchvision `Flowers102` or a Kaggle cats-vs-dogs subset), fine-tune `resnet18` with a frozen backbone, then unfreeze the last block. Compare accuracies.
""", [
    Q("What is the output spatial size of a 32x32 input through Conv2d(kernel=3, stride=1, padding=1)?", ["30x30", "32x32", "16x16", "34x34"], 1, "(32 + 2*1 - 3)/1 + 1 = 32; padding 1 with a 3x3 kernel preserves size."),
    Q("Why do CNNs need far fewer parameters than MLPs for images?", ["They use smaller images", "Filters are small and shared across all spatial positions", "They don't use biases", "They skip backpropagation"], 1, "Weight sharing means the same few kernel weights are reused at every location."),
    Q("What does a residual (skip) connection compute?", ["out = F(x) * x", "out = F(x) + x", "out = F(x) - x", "out = x only"], 1, "Adding the input to the block output lets gradients flow directly through very deep networks."),
], [
    R("CS231n: Convolutional Neural Networks for Visual Recognition (notes)", "https://cs231n.github.io/convolutional-networks/", "article"),
    R("PyTorch tutorial: Training a Classifier (CIFAR-10)", "https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html", "docs"),
    R("PyTorch tutorial: Transfer Learning for Computer Vision", "https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html", "docs"),
    R("CNN Explainer (interactive)", "https://poloclub.github.io/cnn-explainer/", "article"),
]))

lessons.append(L("m05-l6-rnns", "Sequence Models: RNNs, LSTMs & Their Limits", 45, r"""
## Data with order

Text, speech, stock prices, sensor readings and user click streams are **sequences**: order matters and lengths vary. "Dog bites man" differs from "man bites dog." An MLP takes a fixed-size input and has no memory of order. **Recurrent Neural Networks (RNNs)** were the dominant answer before transformers — and understanding their limits explains why attention took over.

## The recurrent idea

An RNN processes a sequence one step at a time, keeping a **hidden state** `h` — a memory vector summarizing everything seen so far. At each step it combines the new input with the previous state:

`h_t = tanh(W_x @ x_t + W_h @ h_(t-1) + b)`

The **same weights** are used at every time step (weight sharing across time, like convolution shares across space).

```python
import torch

def simple_rnn(xs, W_x, W_h, b):
    h = torch.zeros(W_h.shape[0])
    for x_t in xs:                              # sequential loop over time
        h = torch.tanh(W_x @ x_t + W_h @ h + b)
    return h                                    # final state summarizes the sequence

torch.manual_seed(0)
input_dim, hidden_dim = 4, 8
xs = torch.randn(5, input_dim)                  # sequence of 5 steps
h_final = simple_rnn(xs, torch.randn(hidden_dim, input_dim) * 0.3,
                     torch.randn(hidden_dim, hidden_dim) * 0.3, torch.zeros(hidden_dim))
print(h_final.shape)                            # torch.Size([8])
```

In Java terms, it's a `for` loop with an accumulator object updated each iteration — except the update rule is learned.

## Using RNNs in PyTorch

```python
import torch.nn as nn

rnn = nn.RNN(input_size=4, hidden_size=8, batch_first=True)
x = torch.randn(3, 5, 4)            # (batch, seq_len, features)
outputs, h_n = rnn(x)
print(outputs.shape)                # (3, 5, 8): hidden state at every step
print(h_n.shape)                    # (1, 3, 8): final hidden state
```

Sequence tasks come in shapes:

- **Many-to-one:** sentiment of a review (use the final state).
- **Many-to-many (aligned):** tag each word with a part of speech (use every output).
- **Sequence-to-sequence:** translation — an encoder RNN reads the input, a decoder RNN generates the output.
- **One-to-many / generation:** generate text one character at a time, feeding each output back in.

## The problem: vanishing gradients through time

Training uses **backpropagation through time**: unroll the loop and backprop through every step. The gradient for step 1 gets multiplied by `W_h` (and tanh derivatives) once per step. Over 100 steps, it vanishes (or explodes). In practice, a vanilla RNN forgets information from more than ~10-20 steps back. In "The cat, which already ate a lot of food that the neighbours had left out, **was** full," the model must remember "cat" (singular) across many words.

## LSTM: gated memory

**Long Short-Term Memory** networks (1997) add a separate **cell state** — a conveyor belt that information can travel along with minimal change — controlled by learned **gates** (sigmoid values between 0 and 1):

- **Forget gate:** what to erase from memory.
- **Input gate:** what new information to write.
- **Output gate:** what to expose as the hidden state.

Because the cell state is updated additively (`c_t = f * c_(t-1) + i * candidate`), gradients flow much further back — the same insight as residual connections. The **GRU** is a simpler two-gate variant with similar performance.

```python
lstm = nn.LSTM(input_size=4, hidden_size=8, num_layers=2, batch_first=True, dropout=0.2)
outputs, (h_n, c_n) = lstm(torch.randn(3, 5, 4))
print(outputs.shape, h_n.shape, c_n.shape)   # (3,5,8) (2,3,8) (2,3,8)
```

## A complete sentiment classifier

Text is converted to integer token IDs (Module 6 explains tokenization), each mapped to a learned vector by an **embedding layer**, then fed into an LSTM.

```python
class SentimentLSTM(nn.Module):
    def __init__(self, vocab_size, embed_dim=64, hidden=128, n_classes=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden, batch_first=True, bidirectional=True)
        self.head = nn.Linear(hidden * 2, n_classes)       # *2 for both directions

    def forward(self, token_ids):                          # (B, T) integers
        x = self.embed(token_ids)                          # (B, T, E)
        _, (h_n, _) = self.lstm(x)                         # h_n: (2, B, H)
        h = torch.cat([h_n[0], h_n[1]], dim=1)             # forward + backward final states
        return self.head(h)                                # (B, n_classes)

model = SentimentLSTM(vocab_size=10_000)
fake_batch = torch.randint(1, 10_000, (16, 40))            # 16 reviews, 40 tokens each
print(model(fake_batch).shape)                             # torch.Size([16, 2])
```

**Bidirectional** LSTMs read the sequence both forwards and backwards, so each position sees past and future context — useful for classification (but not for generation, where the future is unknown).

Practical notes: sequences in a batch are **padded** to the same length (token 0 = padding); use gradient clipping (`clip_grad_norm_`) because RNN gradients can explode.

## Time-series forecasting example

```python
import numpy as np
series = np.sin(np.linspace(0, 50, 1000)).astype("float32")
window = 30
X = np.stack([series[i:i + window] for i in range(len(series) - window)])
y = series[window:]
X_t = torch.tensor(X).unsqueeze(-1)       # (N, 30, 1): 30 time steps, 1 feature
y_t = torch.tensor(y).unsqueeze(-1)

class Forecaster(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(1, 32, batch_first=True)
        self.out = nn.Linear(32, 1)
    def forward(self, x):
        outputs, _ = self.lstm(x)
        return self.out(outputs[:, -1])    # predict the next value from the last step
```

Train with MSE loss and the standard loop; it learns to continue the sine wave.

## Why transformers replaced RNNs

1. **Sequential bottleneck:** step t needs step t-1, so RNNs can't parallelize across time; GPUs sit idle. Transformers process all positions at once.
2. **Long-range dependencies:** even LSTMs struggle beyond a few hundred steps. Attention connects any two positions directly, in one hop.
3. **Information bottleneck:** seq2seq models squeezed the whole input into one vector. **Attention** (2014) let the decoder look back at all encoder states — and the 2017 paper "Attention Is All You Need" dropped recurrence entirely.

RNN ideas aren't dead: state-space models (Mamba) and hybrid architectures revisit recurrence for efficient long contexts. But for an AI engineer in 2026, transformers are the main event — Module 6.

## Key takeaways

- RNNs carry a hidden state through time with shared weights; outputs can be per-step or final.
- Vanilla RNNs suffer vanishing gradients; LSTMs/GRUs use gates and an additive cell state to remember longer.
- Embedding layers map token IDs to learned vectors.
- Sequential computation and limited long-range memory led to attention and transformers.
""", r"""
**Task: Sequences two ways.**

1. Build the sine-wave forecaster from the lesson, train for 20 epochs, and plot predictions vs truth on held-out data. Then make it predict 100 steps ahead autoregressively (feeding predictions back in) and observe error accumulation.
2. Load the IMDB reviews dataset (Hugging Face `datasets.load_dataset("imdb")`), build a simple word-level vocabulary of the 20,000 most frequent words, pad/truncate reviews to 256 tokens, and train the `SentimentLSTM`. Target > 85% test accuracy.
3. Compare a unidirectional vs bidirectional LSTM and a GRU on the same task.
4. In 5 sentences, explain to a Java colleague why transformers replaced RNNs.
""", [
    Q("What does an RNN's hidden state represent?", ["The final prediction only", "A learned summary of the sequence seen so far", "The input embedding", "The gradient of the loss"], 1, "The hidden state is updated at every step, carrying information from previous inputs forward."),
    Q("How do LSTMs mitigate vanishing gradients?", ["By using ReLU everywhere", "With gates and an additively updated cell state that lets gradients flow further back", "By removing recurrence", "By using larger batch sizes"], 1, "The cell state's additive updates, controlled by gates, provide a path along which gradients decay much more slowly."),
    Q("What is a key reason transformers outperform RNNs on modern hardware?", ["They use fewer parameters", "They process all sequence positions in parallel instead of step by step", "They don't need training data", "They only work on short sequences"], 1, "Self-attention has no step-to-step dependency, so GPUs can compute every position simultaneously."),
], [
    R("Chris Olah: Understanding LSTM Networks", "https://colah.github.io/posts/2015-08-Understanding-LSTMs/", "article"),
    R("Andrej Karpathy: The Unreasonable Effectiveness of Recurrent Neural Networks", "https://karpathy.github.io/2015/05/21/rnn-effectiveness/", "article"),
    R("Dive into Deep Learning: Recurrent Neural Networks", "https://d2l.ai/chapter_recurrent-neural-networks/index.html", "book"),
]))

lessons.append(L("m05-l7-gpu-scale", "GPUs, Mixed Precision & Training at Scale", 40, r"""
## Why GPUs?

Deep learning is dominated by matrix multiplications — billions of independent multiply-adds. A CPU has a handful of powerful cores optimized for sequential logic (your Spring Boot request handling). A GPU has thousands of simpler cores built to do the same operation on lots of data in parallel, plus very high memory bandwidth. Training that takes days on a CPU takes hours on a GPU. NVIDIA's **CUDA** platform is the de facto standard; PyTorch also supports Apple Silicon (`mps`) and AMD (ROCm).

## Moving work to the GPU

Tensors and models must be on the same device.

```python
import torch

device = (
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)
print("using", device)

model = torch.nn.Linear(1024, 1024).to(device)       # moves parameters
x = torch.randn(4096, 1024, device=device)           # create directly on device
y = model(x)
result = y.cpu().detach().numpy()                    # back to CPU for NumPy
```

The classic error `Expected all tensors to be on the same device` means you forgot a `.to(device)` — usually for the batch inside the training loop.

### Quick benchmark

```python
import time
a = torch.randn(4096, 4096)
t = time.perf_counter(); a @ a; print("cpu", time.perf_counter() - t)

if torch.cuda.is_available():
    g = a.to("cuda")
    g @ g; torch.cuda.synchronize()                 # warm-up
    t = time.perf_counter(); g @ g; torch.cuda.synchronize()
    print("gpu", time.perf_counter() - t)           # typically 20-100x faster
```

GPU operations are **asynchronous**; call `torch.cuda.synchronize()` before timing.

## Where to get a GPU

- **Google Colab / Kaggle Notebooks:** free GPUs with session limits — perfect for this course.
- **Cloud:** AWS, GCP, Azure, and GPU clouds (Lambda, RunPod, Modal) rent by the hour.
- **Local:** an NVIDIA RTX card with 12-24 GB of VRAM is enough to fine-tune small models and run quantized LLMs.

Check with `!nvidia-smi` in a notebook: it shows the GPU model, memory use and running processes.

## GPU memory: the real constraint

During training, GPU memory holds:

1. **Model weights.**
2. **Gradients** (same size as the weights).
3. **Optimizer state:** Adam stores two extra values per parameter.
4. **Activations** saved during the forward pass for backprop — grows with batch size and sequence length.

Rough rule for full fine-tuning with Adam in mixed precision: about **16 bytes per parameter** before activations. A 7B model therefore needs ~112 GB — more than any single consumer GPU. That's why techniques like LoRA and quantization exist.

When you hit `CUDA out of memory`:

- Reduce batch size (and use **gradient accumulation** to keep the effective batch size).
- Use mixed precision.
- Use **gradient checkpointing** (recompute activations in backward instead of storing them).
- Use parameter-efficient fine-tuning (LoRA/QLoRA) for large models.

## Mixed precision training

Float32 uses 4 bytes per number. **bfloat16/float16** use 2 bytes, halving memory and greatly speeding up math on modern GPUs' Tensor Cores. **Automatic Mixed Precision (AMP)** runs most operations in 16-bit while keeping sensitive ones in 32-bit:

```python
model = model.to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
scaler = torch.amp.GradScaler("cuda")      # needed for float16, not for bfloat16

for X, y in train_loader:
    X, y = X.to(device), y.to(device)
    with torch.autocast(device_type="cuda", dtype=torch.float16):
        loss = loss_fn(model(X), y)
    optimizer.zero_grad()
    scaler.scale(loss).backward()          # scale loss to avoid float16 underflow
    scaler.step(optimizer)
    scaler.update()
```

With **bfloat16** (supported on Ampere-generation GPUs and newer), the gradient scaler is unnecessary because bfloat16 has the same range as float32 — which is why LLM training generally uses bf16.

## Gradient accumulation

Simulate a large batch by summing gradients over several small batches before stepping:

```python
accum_steps = 4
optimizer.zero_grad()
for i, (X, y) in enumerate(train_loader):
    loss = loss_fn(model(X.to(device)), y.to(device)) / accum_steps
    loss.backward()                        # gradients accumulate across iterations
    if (i + 1) % accum_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

This finally makes good use of the "gradients accumulate" behaviour you learned about in lesson 2.

## Other speed-ups

- **DataLoader:** `num_workers > 0` and `pin_memory=True` so the GPU isn't waiting for data.
- **`torch.compile(model)`:** compiles the model graph into optimized kernels — often a free 1.3-2x speedup.
- **Efficient attention kernels** (FlashAttention, available via `F.scaled_dot_product_attention`) for transformers.

## Scaling beyond one GPU

- **Data parallelism (DDP):** each GPU holds a full model copy and processes a different slice of the batch; gradients are averaged. Launched with `torchrun`.
- **FSDP / ZeRO (DeepSpeed):** shard weights, gradients and optimizer state across GPUs so models too large for one GPU can train.
- **Tensor and pipeline parallelism:** split individual layers or groups of layers across GPUs — used for the largest LLMs, trained on thousands of GPUs.

Hugging Face **Accelerate** lets the same script run on CPU, one GPU or many with minimal changes.

## Inference considerations

In production, you'll often care more about inference than training:

- `model.eval()` + `torch.inference_mode()`.
- **Quantization** (int8, int4) shrinks models for faster, cheaper inference.
- Export to **ONNX** or use serving engines (TorchServe, Triton, and **vLLM** for LLMs) for high-throughput APIs.
- Measure **latency** (time per request) and **throughput** (requests per second) — familiar concerns from backend engineering.

## Key takeaways

- GPUs parallelize matrix math; move models and every batch to the same device.
- Memory = weights + gradients + optimizer state + activations; Adam fine-tuning costs ~16 bytes/parameter.
- Use AMP (bf16 preferred), gradient accumulation and gradient checkpointing to fit bigger models and batches.
- DDP/FSDP scale across GPUs; quantization and serving engines make inference efficient.
""", r"""
**Task: Speed up your CIFAR-10 training.** On Colab with a GPU:

1. Run `!nvidia-smi` and record the GPU type and memory.
2. Benchmark a 4096x4096 matrix multiply on CPU vs GPU (with `synchronize`).
3. Time one epoch of your SmallCNN in float32, then with AMP (float16 + GradScaler, or bfloat16 if supported). Compare time, peak memory (`torch.cuda.max_memory_allocated()`) and accuracy.
4. Increase batch size until you hit out-of-memory; then use gradient accumulation to reach an effective batch size of 1024.
5. Try `torch.compile(model)` and report the speedup.
6. Calculate the approximate training memory needed for 1B, 7B and 70B parameter models with Adam (16 bytes/param).
""", [
    Q("What does the error 'Expected all tensors to be on the same device' usually mean?", ["The GPU is broken", "A tensor (often the input batch) wasn't moved to the model's device", "The model is too large", "Mixed precision is enabled"], 1, "Model parameters and input tensors must live on the same device; add .to(device) for each batch."),
    Q("Why is bfloat16 preferred over float16 for training large models?", ["It uses less memory than float16", "It has the same exponent range as float32, avoiding overflow/underflow without loss scaling", "It is more precise than float32", "It runs on CPUs only"], 1, "bfloat16 keeps float32's 8 exponent bits, so gradient scaling is unnecessary."),
    Q("What does gradient accumulation achieve?", ["Faster convergence with smaller learning rates", "A larger effective batch size without needing more GPU memory", "Removes the need for an optimizer", "Prevents overfitting"], 1, "Summing gradients over several micro-batches before stepping simulates one big batch."),
], [
    R("PyTorch: Automatic Mixed Precision recipe", "https://pytorch.org/tutorials/recipes/recipes/amp_recipe.html", "docs"),
    R("Hugging Face: Efficient training on a single GPU", "https://huggingface.co/docs/transformers/perf_train_gpu_one", "docs"),
    R("Hugging Face: The Ultra-Scale Playbook (training on GPU clusters)", "https://huggingface.co/spaces/nanotron/ultrascale-playbook", "book"),
]))

MODULE = M("m05-deep-learning", 5, "Deep Learning with PyTorch", "Intermediate", 3,
    "Understand how neural networks learn — from single neurons and backpropagation to CNNs and RNNs — and build them in PyTorch. You will master the training loop, the optimization and regularization toolbox, and practical GPU training that every modern AI system, including LLMs, is built on.",
    [
        "Explain neurons, activations, backpropagation and autograd, and implement a mini autograd engine",
        "Write idiomatic PyTorch: nn.Module, Dataset/DataLoader, training/evaluation loops and checkpointing",
        "Apply optimizers, LR schedules, normalization and regularization to train models reliably",
        "Build CNNs for images (including transfer learning) and LSTMs for sequences",
        "Train efficiently on GPUs with mixed precision, gradient accumulation and memory budgeting",
    ],
    lessons,
    ("Image Classifier App with Transfer Learning", r"""
## Goal
Train, evaluate and ship a real image classifier — the deep learning equivalent of deploying your first Spring Boot service.

## Spec
- Choose a dataset with 5-10 classes and at least 1,000 images (e.g. Food-101 subset, a Kaggle plant-disease set, or photos you collect yourself).
- Baseline: the `SmallCNN` trained from scratch.
- Main model: fine-tune a pretrained `resnet18`/`resnet50` or `efficientnet_b0` from torchvision (or a ViT via `timm`).
- Proper train/val/test split, augmentation on train only, AdamW + OneCycle or cosine schedule, mixed precision, early stopping and checkpointing of the best model.
- Report: training curves, test accuracy, per-class precision/recall, confusion matrix, and a grid of the worst mistakes.
- Serve it: a **Gradio** or **Streamlit** app where a user uploads an image and sees the top-3 predictions with probabilities.

## Steps
1. Write `data.py` (datasets, transforms, loaders), `model.py`, `train.py` (CLI args with argparse), `evaluate.py`, `app.py`.
2. Overfit a single batch to verify the pipeline, then run the baseline.
3. Run transfer learning in two phases: frozen backbone, then unfreeze the last block with a 10x smaller LR.
4. Log experiments (CSV or Weights & Biases free tier).
5. Deploy the Gradio app to Hugging Face Spaces (free).

## Stretch goals
- Export the model to ONNX and run inference from a small **Java** program using ONNX Runtime — connect your old and new skills.
- Add Grad-CAM visualizations showing which image regions drove each prediction.
- Quantize the model to int8 and compare size, latency and accuracy.
"""))
