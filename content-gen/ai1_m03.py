from ai1_common import L, Q, R, M

lessons = []

lessons.append(L("m03-l1-vectors", "Vectors, Dot Products & Similarity", 45, r"""
## Why linear algebra?

Machine learning represents everything as lists of numbers: a house is `[size, rooms, age]`, an image is a grid of pixel intensities, a word is a 768-number **embedding**. Linear algebra is simply the maths of operating on these lists efficiently. You need intuition, not proofs.

## What a vector is

A **vector** is an ordered list of numbers. Two equally valid views:

1. **Data view:** a row in a table — `[1200 sqft, 3 rooms, 10 years]`.
2. **Geometric view:** an arrow from the origin to a point in space. `[3, 4]` is an arrow 3 right, 4 up.

```python
import numpy as np
v = np.array([3.0, 4.0])
w = np.array([1.0, 2.0])
```

The number of entries is the **dimension**. Embeddings live in 384- to 4096-dimensional space; you can't picture it, but the 2-D intuition carries over.

## Basic operations

```python
v + w          # [4, 6]   add arrows tip-to-tail
v - w          # [2, 2]   arrow from w to v
2 * v          # [6, 8]   same direction, twice as long (scaling)
```

A famous embedding example: `vector("king") - vector("man") + vector("woman")` lands near `vector("queen")`. Directions in embedding space encode meaning.

## Length (norm)

The length of `[3, 4]` is `sqrt(3^2 + 4^2) = 5` — Pythagoras. This is the **L2 norm**.

```python
np.linalg.norm(v)            # 5.0
np.sum(np.abs(v))            # 7.0  -> L1 norm (Manhattan distance)
unit = v / np.linalg.norm(v) # [0.6, 0.8]: a unit vector (length 1), direction only
```

Norms reappear as **regularization** (L1/L2 penalties keep model weights small) and in distance calculations.

## The dot product — the most important operation in ML

Algebraically: multiply matching entries and sum.

`v . w = 3*1 + 4*2 = 11`

```python
np.dot(v, w)    # 11.0
v @ w           # 11.0, same thing
```

Geometrically: `v . w = |v| * |w| * cos(theta)`, where theta is the angle between the arrows. So the dot product measures **how much two vectors point in the same direction**:

- Large positive: same direction.
- Zero: perpendicular (orthogonal) — unrelated.
- Negative: opposite directions.

### Why it is everywhere

- **A linear model's prediction is a dot product**: `price = w . x + b` — weights times features, summed. A neuron computes exactly this before its activation.
- **Matrix multiplication** is just many dot products (next lesson).
- **Attention** in transformers computes dot products between "query" and "key" vectors to decide which words relate.
- **Semantic search** ranks documents by dot product / cosine similarity with a query embedding.

## Cosine similarity

Rearranging the geometric formula gives the cosine of the angle — a similarity score between -1 and 1 that ignores length:

```python
def cosine_similarity(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))

cat    = np.array([0.8, 0.6, 0.1])
kitten = np.array([0.7, 0.7, 0.2])
car    = np.array([0.1, 0.2, 0.9])
print(cosine_similarity(cat, kitten))   # ~0.98 very similar
print(cosine_similarity(cat, car))      # ~0.30 not similar
```

If vectors are pre-normalized to unit length, cosine similarity is just the dot product — which is why vector databases often store normalized embeddings.

## Distance

Euclidean distance is the norm of the difference:

```python
np.linalg.norm(cat - kitten)    # small distance = similar
```

k-Nearest Neighbours classifies a point by looking at the labels of the closest points. Clustering (k-means) groups points by distance.

## Worked example: a recommender in 10 lines

Represent users and movies by how much they like/contain genres `[action, romance, sci-fi]`:

```python
user = np.array([0.9, 0.1, 0.8])           # loves action & sci-fi
movies = {
    "Interstellar": np.array([0.4, 0.3, 1.0]),
    "Notebook":     np.array([0.0, 1.0, 0.0]),
    "Mad Max":      np.array([1.0, 0.1, 0.4]),
}
scores = {name: user @ vec for name, vec in movies.items()}
for name, s in sorted(scores.items(), key=lambda kv: -kv[1]):
    print(f"{name:12s} {s:.2f}")
```

Real recommender systems learn these vectors from data (matrix factorization, two-tower models) — but scoring is still a dot product.

## Linear combinations and span (just the idea)

`a*v + b*w` (scaled vectors added) is a **linear combination**. Any 2-D point can be reached by combining two non-parallel 2-D vectors. A neural network layer outputs linear combinations of its inputs, then bends them with a non-linear activation — that bending is what lets networks model complex shapes.

## Java analogy

In Java, a dot product is:

```java
double dot = 0;
for (int i = 0; i < a.length; i++) dot += a[i] * b[i];
```

That loop runs trillions of times while training an LLM; GPUs exist largely to do it in parallel.

## Key takeaways

- Vectors are lists of numbers and arrows in space; embeddings are vectors where direction encodes meaning.
- Norm = length; unit vectors keep direction only.
- Dot product = "alignment" score; it powers linear models, neurons, attention and search.
- Cosine similarity = dot product of normalized vectors.
""", r"""
**Task: Similarity by hand and by code.**

1. On paper, compute the dot product, both norms and cosine similarity of `a=[1,2,2]` and `b=[2,0,1]`. Verify with NumPy.
2. Write `cosine_similarity` and `euclidean_distance` functions from scratch using only loops (Java-style), then using NumPy, and check they match.
3. Create 5 "sentence" vectors by hand for topics (sports, cooking, finance...) in 4 dimensions and a query vector. Rank sentences by cosine similarity.
4. Show that scaling a vector by 10 changes the dot product but not the cosine similarity.
""", [
    Q("What does a dot product of zero between two non-zero vectors mean?", ["They are identical", "They are perpendicular (orthogonal)", "One is the zero vector", "They point in opposite directions"], 1, "v . w = |v||w|cos(theta); for non-zero vectors this is zero only when cos(theta)=0, i.e. a 90 degree angle."),
    Q("What is the L2 norm of [6, 8]?", ["14", "10", "48", "100"], 1, "sqrt(6^2 + 8^2) = sqrt(100) = 10."),
    Q("Why is cosine similarity preferred over raw dot product for comparing embeddings?", ["It is faster", "It ignores vector length and compares only direction", "It always returns positive numbers", "It works only for 2-D vectors"], 1, "Cosine normalizes by the lengths, so a long document's vector doesn't dominate just by magnitude."),
], [
    R("3Blue1Brown: Essence of Linear Algebra (playlist)", "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab", "video"),
    R("Mathematics for Machine Learning (Deisenroth et al., free PDF)", "https://mml-book.github.io/", "book"),
    R("Khan Academy: Vectors and spaces", "https://www.khanacademy.org/math/linear-algebra/vectors-and-spaces", "course"),
]))

lessons.append(L("m03-l2-matrices", "Matrices as Transformations & Data", 45, r"""
## Two ways to see a matrix

A **matrix** is a 2-D grid of numbers with shape `(rows, columns)`.

1. **Data view:** a dataset. Rows are samples, columns are features. `X.shape == (n_samples, n_features)`.
2. **Transformation view:** a function that moves vectors. Multiplying a vector by a matrix rotates, scales, stretches or projects it.

Both views matter: the data view for datasets, the transformation view for understanding what neural network layers do.

## Matrix-vector multiplication

Each output entry is the **dot product of one matrix row with the vector**:

```python
import numpy as np
A = np.array([[2, 0],
              [0, 3]])
x = np.array([1, 1])
print(A @ x)     # [2*1 + 0*1, 0*1 + 3*1] = [2, 3]
```

This `A` stretches x by 2 horizontally and by 3 vertically. Some classic 2-D transformations:

```python
theta = np.pi / 2
rotate90 = np.array([[np.cos(theta), -np.sin(theta)],
                     [np.sin(theta),  np.cos(theta)]])
print(np.round(rotate90 @ np.array([1, 0])))   # [0, 1]: x-axis rotated to y-axis

shear = np.array([[1, 1],
                  [0, 1]])
project_x = np.array([[1, 0],
                      [0, 0]])      # squashes everything onto the x-axis
```

Intuition from 3Blue1Brown: **the columns of the matrix tell you where the basis vectors `[1,0]` and `[0,1]` land.** Everything else follows.

## Matrix-matrix multiplication

`A @ B` means "apply B, then A". Entry `(i, j)` of the result is the dot product of row `i` of A with column `j` of B.

```python
A = np.array([[1, 2],
              [3, 4]])
B = np.array([[0, 1],
              [1, 0]])
print(A @ B)   # [[2, 1], [4, 3]]
print(B @ A)   # [[3, 4], [1, 2]]  -> order matters! AB != BA in general
```

**Shape rule:** `(m, n) @ (n, p) -> (m, p)`. The inner dimensions must match. Shape mismatches are the most common deep-learning error, so practise reading shapes:

```python
X = np.random.rand(64, 784)     # batch of 64 flattened 28x28 images
W1 = np.random.rand(784, 128)   # layer 1 weights
W2 = np.random.rand(128, 10)    # layer 2 weights (10 classes)
h = X @ W1                      # (64, 128)
out = h @ W2                    # (64, 10): one score per class per image
```

That is the skeleton of a neural network: matrix multiplications with non-linear functions in between (Module 5).

## Why "linear" is limited

Stacking two linear transformations is still linear: `W2 @ (W1 @ x) = (W2 @ W1) @ x`, a single matrix. No matter how many layers, without non-linearities a network is just one matrix — it can only draw straight lines (hyperplanes). This is why activations like ReLU are essential.

## Special matrices

```python
I = np.eye(3)              # identity: I @ x == x  (like multiplying by 1)
D = np.diag([1, 2, 3])     # diagonal: scales each axis independently
At = A.T                   # transpose: rows become columns, (m,n) -> (n,m)
```

Transpose identity you will meet in gradient derivations: `(AB)^T = B^T A^T`.

## Inverse and solving equations

The **inverse** `A^-1` undoes A: `A^-1 @ A = I`. Not every matrix has one — projections squash information away (determinant 0), so you can't reverse them.

```python
A = np.array([[4.0, 7.0],
              [2.0, 6.0]])
print(np.linalg.det(A))           # 10.0: area scaling factor; 0 means not invertible
x = np.linalg.solve(A, np.array([1.0, 2.0]))   # solve A x = b
```

**Linear regression's closed-form solution** (the "normal equation") uses this: `w = (X^T X)^-1 X^T y`.

```python
rng = np.random.default_rng(0)
X = np.c_[np.ones(100), rng.random(100)]      # add a column of 1s for the bias
y = 3 + 5 * X[:, 1] + rng.normal(0, 0.1, 100)
w = np.linalg.solve(X.T @ X, X.T @ y)
print(w)       # approx [3, 5]: intercept and slope recovered!
```

## Eigenvectors: directions that don't turn

For most vectors, a matrix changes their direction. **Eigenvectors** are special directions that only get scaled; the scale factor is the **eigenvalue**: `A v = lambda v`.

```python
A = np.array([[3, 1],
              [0, 2]])
vals, vecs = np.linalg.eig(A)
print(vals)    # [3. 2.]
```

Where it matters in ML: **PCA (Principal Component Analysis)** finds the eigenvectors of the data's covariance matrix — the directions of greatest variance — to compress high-dimensional data into a few dimensions for visualization or speed.

## SVD in one paragraph

Singular Value Decomposition factors any matrix as `U S V^T`: rotate, scale, rotate. Keeping only the largest singular values gives the best low-rank approximation. This idea powers PCA, recommender systems, image compression, and **LoRA** — the popular technique for fine-tuning LLMs cheaply by learning low-rank weight updates.

```python
M = rng.random((100, 50))
U, S, Vt = np.linalg.svd(M, full_matrices=False)
k = 5
M_approx = U[:, :k] @ np.diag(S[:k]) @ Vt[:k]      # rank-5 approximation
print(np.linalg.norm(M - M_approx) / np.linalg.norm(M))   # relative error
```

## Tensors

A **tensor** generalizes to any number of dimensions: scalar (0-D), vector (1-D), matrix (2-D), and beyond. A batch of RGB images is a 4-D tensor `(batch, 3, height, width)`. PyTorch's `Tensor` is essentially a NumPy array that can live on a GPU and track gradients.

## Key takeaways

- A matrix is both a dataset and a transformation; columns show where basis vectors land.
- `(m,n) @ (n,p) -> (m,p)`; order matters.
- Stacked linear layers collapse to one — non-linear activations are required.
- Eigenvectors/SVD find important directions: PCA, compression, LoRA.
""", r"""
**Task: Transformations and regression.**

1. Apply rotation (45 degrees), scaling `diag(2, 0.5)` and shear matrices to the four corners of a unit square and plot the before/after shapes with matplotlib.
2. Verify numerically that `A @ B != B @ A` for two random 3x3 matrices, and that `(A @ B).T == B.T @ A.T`.
3. Generate data `y = 2 + 3*x1 - 1.5*x2 + noise` for 200 samples and recover the coefficients with the normal equation via `np.linalg.solve`.
4. Write out the shapes of every intermediate result for a 2-layer network with batch 32, input 20, hidden 64, output 3.
""", [
    Q("What is the shape of (32, 20) @ (20, 64) @ (64, 3)?", ["(32, 64)", "(20, 3)", "(32, 3)", "Invalid"], 2, "(32,20)@(20,64) gives (32,64); then @(64,3) gives (32,3)."),
    Q("Why do neural networks need non-linear activation functions between layers?", ["To make training faster", "Because stacked linear layers collapse into a single linear transformation", "To reduce memory use", "To normalize outputs"], 1, "W2(W1x) = (W2W1)x — without non-linearities depth adds no expressive power."),
    Q("What does an eigenvector of a matrix A satisfy?", ["A v = 0", "A v = lambda v (only scaled, not rotated)", "A v = v^T", "A v is perpendicular to v"], 1, "Eigenvectors keep their direction under A; they are scaled by the eigenvalue lambda."),
], [
    R("3Blue1Brown: Linear transformations and matrices", "https://www.youtube.com/watch?v=kYB8IZa5AuE", "video"),
    R("Immersive Linear Algebra (interactive free book)", "https://immersivemath.com/ila/index.html", "book"),
    R("DeepLearning.AI: Mathematics for ML and Data Science (Coursera)", "https://www.coursera.org/specializations/mathematics-for-machine-learning-and-data-science", "course"),
]))

lessons.append(L("m03-l3-derivatives", "Derivatives, Gradients & the Chain Rule", 50, r"""
## Why calculus?

Training a model means: **adjust the parameters so the error goes down**. To know which way to adjust each parameter, you need to know how the error changes when you nudge that parameter. That rate of change is a **derivative**. You never have to compute derivatives by hand in practice — PyTorch does it automatically — but you must understand what they mean to debug training.

## Derivative = slope = sensitivity

For a function `f(x)`, the derivative `f'(x)` tells you: if I increase x by a tiny amount, how much does f change, per unit of x?

```python
def f(x):
    return x ** 2

def numerical_derivative(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)    # slope over a tiny interval

print(numerical_derivative(f, 3.0))   # ~6.0
```

For `f(x) = x^2`, the slope at x=3 is 6: nudging x from 3 to 3.001 increases f by about 0.006.

- Positive derivative: f increases as x increases.
- Negative derivative: f decreases.
- Zero: flat — possibly a minimum or maximum.

## A few rules (enough for ML)

| Function | Derivative |
|---|---|
| constant `c` | 0 |
| `x^n` | `n * x^(n-1)` |
| `e^x` | `e^x` |
| `ln(x)` | `1/x` |
| `a*f(x) + b*g(x)` | `a*f'(x) + b*g'(x)` |

Examples: `d/dx (3x^2 + 2x + 1) = 6x + 2`; `d/dx (x - 5)^2 = 2(x - 5)`.

## Key activation-function derivatives

```python
import numpy as np

def sigmoid(z):
    return 1 / (1 + np.exp(-z))          # squashes to (0, 1)

def sigmoid_grad(z):
    s = sigmoid(z)
    return s * (1 - s)                   # max 0.25 at z=0; ~0 for large |z|

def relu(z):
    return np.maximum(0, z)

def relu_grad(z):
    return (z > 0).astype(float)         # 1 if positive else 0
```

Notice sigmoid's gradient is tiny for large |z|. Multiply many tiny numbers across layers and gradients vanish — the **vanishing gradient problem** that made ReLU popular.

## Partial derivatives and the gradient

Models have many parameters. A **partial derivative** measures sensitivity to one variable while holding the others fixed.

For `f(w, b) = (w*2 + b - 7)^2` (squared error for one data point x=2, y=7):

- `df/dw = 2 * (2w + b - 7) * 2`
- `df/db = 2 * (2w + b - 7) * 1`

The **gradient** is the vector of all partial derivatives: `grad f = [df/dw, df/db]`. It points in the direction of **steepest increase**. So to decrease the loss, step in the **opposite** direction of the gradient. That is gradient descent (next lesson).

```python
def loss(w, b):
    return (w * 2 + b - 7) ** 2

def grad(w, b):
    err = w * 2 + b - 7
    return np.array([2 * err * 2, 2 * err * 1])

print(grad(1.0, 1.0))    # [-16, -8]: increasing w or b would reduce the loss
```

An LLM has billions of parameters; its gradient is a vector with billions of entries — one "which way and how much" signal per weight.

## The chain rule — the heart of backpropagation

When functions are nested, derivatives multiply. If `y = f(g(x))`, then:

`dy/dx = f'(g(x)) * g'(x)`

Intuition: if g changes 3x as fast as x, and f changes 2x as fast as g, then f changes 6x as fast as x.

Worked example: `L = (sigmoid(w*x) - y)^2`. Break it into steps:

```
z = w * x          dz/dw = x
a = sigmoid(z)     da/dz = a * (1 - a)
L = (a - y)^2      dL/da = 2 * (a - y)

dL/dw = dL/da * da/dz * dz/dw = 2(a - y) * a(1 - a) * x
```

```python
x, y, w = 1.5, 1.0, 0.2
z = w * x
a = sigmoid(z)
L = (a - y) ** 2
dL_dw = 2 * (a - y) * a * (1 - a) * x
print(f"loss={L:.4f}  dL/dw={dL_dw:.4f}")

# check against the numerical derivative
num = (( sigmoid((w + 1e-5) * x) - y) ** 2 - (sigmoid((w - 1e-5) * x) - y) ** 2) / 2e-5
print(f"numerical={num:.4f}")      # matches
```

A neural network is a long chain of such steps. **Backpropagation** applies the chain rule from the loss backwards through every layer, reusing intermediate results, to get the gradient for every weight efficiently. Comparing an analytical gradient with a numerical one ("gradient checking") is a classic debugging technique.

## Automatic differentiation: let the computer do it

```python
import torch

w = torch.tensor(0.2, requires_grad=True)
x, y = torch.tensor(1.5), torch.tensor(1.0)
L = (torch.sigmoid(w * x) - y) ** 2
L.backward()            # chain rule applied automatically
print(w.grad)           # same value as our hand derivation
```

PyTorch records each operation in a **computational graph** during the forward pass and walks it backwards on `.backward()`. Karpathy's *micrograd* builds this engine in about 100 lines — a highly recommended exercise once you finish Module 5.

## Local minima, saddle points, convexity

A **convex** function (bowl-shaped, like linear regression's squared error) has one global minimum — gradient descent always finds it. Neural network losses are non-convex with many valleys and saddle points, yet in very high dimensions gradient descent with good tricks finds solutions that generalize well.

## Key takeaways

- Derivative = sensitivity of output to input; gradient = vector of partial derivatives pointing uphill.
- Chain rule: derivatives of nested functions multiply — backprop is the chain rule applied systematically.
- Sigmoid gradients vanish for large inputs; ReLU's don't (for positive inputs).
- Autograd (PyTorch) computes gradients for you; numerical gradients verify them.
""", r"""
**Task: Derivatives three ways.**

1. By hand, find derivatives of `f(x) = 4x^3 - 2x + 7` and `g(x) = (3x + 1)^2` (use the chain rule for g).
2. Write `numerical_derivative(f, x)` and check your answers at x = 2.
3. Plot sigmoid, its derivative, ReLU and its derivative on [-6, 6]. Where is the sigmoid derivative largest?
4. For `L = (relu(w*x + b) - y)^2` with x=2, y=3, w=0.5, b=0.1, derive `dL/dw` and `dL/db` by hand, check numerically, then check with PyTorch autograd.
""", [
    Q("What does the gradient of the loss with respect to the parameters point toward?", ["The direction of steepest decrease", "The direction of steepest increase", "The global minimum", "The origin"], 1, "The gradient points uphill; gradient descent moves in the negative gradient direction to reduce loss."),
    Q("If y = f(g(x)), what is dy/dx by the chain rule?", ["f'(x) + g'(x)", "f'(g(x)) * g'(x)", "f(x) * g(x)", "f'(x) / g'(x)"], 1, "Derivatives of composed functions multiply: outer derivative evaluated at the inner function, times the inner derivative."),
    Q("Why does the sigmoid activation cause vanishing gradients in deep networks?", ["Its output is negative", "Its derivative is at most 0.25 and near zero for large |z|, so products of many shrink fast", "It is not differentiable", "It outputs integers"], 1, "Backprop multiplies derivatives layer by layer; repeated factors below 0.25 shrink the gradient exponentially."),
], [
    R("3Blue1Brown: Essence of Calculus (playlist)", "https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr", "video"),
    R("Andrej Karpathy: The spelled-out intro to neural networks and backpropagation (micrograd)", "https://www.youtube.com/watch?v=VMj-3S1tku0", "video"),
    R("Khan Academy: Multivariable calculus - gradient", "https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives", "course"),
]))

lessons.append(L("m03-l4-gradient-descent", "Gradient Descent from Scratch", 50, r"""
## The algorithm that trains (almost) everything

From linear regression to GPT, models are trained with variations of one loop:

```
repeat:
    1. predict with current parameters
    2. measure the error (loss)
    3. compute the gradient of the loss w.r.t. each parameter
    4. parameter = parameter - learning_rate * gradient
```

Picture standing on a foggy hillside wanting to reach the valley. You can't see far, but you can feel the slope under your feet. Take a small step downhill, feel again, repeat. The **learning rate** is your step size.

## 1-D example

Minimize `f(x) = (x - 3)^2`. Derivative: `2(x - 3)`.

```python
x = 10.0
lr = 0.1
for step in range(25):
    grad = 2 * (x - 3)
    x = x - lr * grad
    if step % 5 == 0:
        print(f"step {step:2d}  x={x:.4f}  f={(x - 3) ** 2:.6f}")
print("final x:", round(x, 4))    # ~3.0
```

## Learning rate: the most important hyperparameter

```python
def run(lr, steps=20):
    x = 10.0
    for _ in range(steps):
        x -= lr * 2 * (x - 3)
    return x

for lr in [0.01, 0.1, 0.9, 1.1]:
    print(lr, run(lr))
```

- **Too small (0.01):** converges very slowly.
- **Good (0.1):** converges smoothly.
- **Large (0.9):** overshoots and oscillates, but still converges.
- **Too large (1.1):** diverges — the loss explodes to infinity (you'll see `nan` in real training).

When your training loss becomes `nan`, the first suspect is a learning rate that's too high.

## Linear regression with gradient descent

Model: `y_hat = w * x + b`. Loss: **Mean Squared Error** `MSE = mean((y_hat - y)^2)`.

Gradients (from the chain rule):

- `dMSE/dw = mean(2 * (y_hat - y) * x)`
- `dMSE/db = mean(2 * (y_hat - y))`

```python
import numpy as np

rng = np.random.default_rng(42)
x = rng.uniform(0, 10, 200)
y = 4.0 * x + 7.0 + rng.normal(0, 2, 200)     # true w=4, b=7, plus noise

w, b = 0.0, 0.0
lr = 0.01
history = []
for epoch in range(2000):
    y_hat = w * x + b
    error = y_hat - y
    loss = np.mean(error ** 2)
    dw = np.mean(2 * error * x)
    db = np.mean(2 * error)
    w -= lr * dw
    b -= lr * db
    history.append(loss)
    if epoch % 400 == 0:
        print(f"epoch {epoch:4d}  loss={loss:8.3f}  w={w:.3f}  b={b:.3f}")

print(f"learned w={w:.2f}, b={b:.2f}")          # close to 4 and 7
```

Plot `history` and you'll see the classic loss curve: steep drop, then flattening.

## Vectorized for many features

With feature matrix `X` of shape `(n, d)` and weights `w` of shape `(d,)`:

```python
def train_linear(X, y, lr=0.05, epochs=1000):
    n, d = X.shape
    w = np.zeros(d); b = 0.0
    for _ in range(epochs):
        y_hat = X @ w + b
        err = y_hat - y
        w -= lr * (2 / n) * (X.T @ err)       # gradient for all weights at once
        b -= lr * (2 / n) * err.sum()
    return w, b

X = rng.normal(size=(500, 3))
y = X @ np.array([2.0, -1.0, 0.5]) + 3.0 + rng.normal(0, 0.1, 500)
print(train_linear(X, y))     # approx ([2, -1, 0.5], 3)
```

`X.T @ err` computes every feature's gradient in one matrix multiplication — the same pattern used inside neural networks.

## Feature scaling matters

If one feature is in thousands (sqft) and another in single digits (rooms), the loss surface becomes a long narrow valley; gradient descent zig-zags and needs a tiny learning rate. **Standardize features** (mean 0, std 1) first and convergence becomes much faster. This is why scaling is a standard preprocessing step.

## Batch, stochastic and mini-batch

- **Batch GD:** gradient over the entire dataset per step. Accurate but slow for big data.
- **Stochastic GD (SGD):** gradient from one random sample per step. Noisy but cheap.
- **Mini-batch GD:** gradient from a batch (e.g. 32-512 samples). The standard in deep learning — efficient on GPUs, and the noise even helps escape poor regions.

```python
batch_size = 32
for epoch in range(20):
    idx = rng.permutation(len(X))            # shuffle each epoch
    for start in range(0, len(X), batch_size):
        batch = idx[start:start + batch_size]
        Xb, yb = X[batch], y[batch]
        # compute gradient on (Xb, yb) and update w, b
```

An **epoch** is one full pass over the training data; a **step/iteration** is one parameter update.

## Beyond plain gradient descent

- **Momentum:** keeps a running average of past gradients, like a ball rolling downhill, smoothing zig-zags.
- **Adam / AdamW:** adapts the step size per parameter using gradient history; the default optimizer for transformers.
- **Learning-rate schedules:** warm up, then decay the learning rate over training.

You'll use these via `torch.optim` in Module 5 — but they are all refinements of the four-line loop at the top.

## Key takeaways

- Gradient descent: predict, measure loss, compute gradient, step against it — repeated.
- The learning rate controls step size; too high diverges (`nan`), too low crawls.
- Vectorized gradients (`X.T @ err`) scale to many features; scaling features speeds convergence.
- Mini-batch SGD + Adam is how modern networks are trained.
""", r"""
**Task: Train a model with only NumPy.**

1. Implement gradient descent for linear regression on the California housing dataset (`fetch_california_housing`) using all 8 features.
2. Train once without standardizing features and once with standardization. Compare how many epochs each needs and which learning rates work.
3. Plot the loss curves for learning rates 0.001, 0.01, 0.1 and one that diverges.
4. Convert your loop to mini-batch SGD (batch size 64) and compare final loss and runtime.
5. Compare your learned weights to `np.linalg.lstsq` (the exact solution).
""", [
    Q("In gradient descent, what is the update rule for a parameter w?", ["w = w + lr * gradient", "w = w - lr * gradient", "w = gradient / lr", "w = w * gradient"], 1, "We step against the gradient (downhill) scaled by the learning rate."),
    Q("Your training loss suddenly becomes `nan` after a few steps. What is the most likely cause?", ["Learning rate too small", "Learning rate too large causing divergence", "Too much training data", "Features were standardized"], 1, "A step size that is too large overshoots, increasing loss until values overflow to inf/nan."),
    Q("What is mini-batch gradient descent?", ["Using one sample per update", "Using the full dataset per update", "Using a small random subset (e.g. 32-512 samples) per update", "Updating only some of the weights"], 2, "Mini-batches balance gradient accuracy and compute efficiency and are the standard in deep learning."),
], [
    R("Andrew Ng: Machine Learning Specialization (gradient descent lessons)", "https://www.coursera.org/specializations/machine-learning-introduction", "course"),
    R("3Blue1Brown: Gradient descent, how neural networks learn", "https://www.youtube.com/watch?v=IHZwWFHWa-w", "video"),
    R("Sebastian Ruder: An overview of gradient descent optimization algorithms", "https://www.ruder.io/optimizing-gradient-descent/", "article"),
]))

lessons.append(L("m03-l5-probability", "Probability: Uncertainty, Distributions & Bayes", 50, r"""
## Why probability?

ML models don't output certainties; they output **beliefs**. A spam filter says "92% spam". An LLM picks the next word from a probability distribution over ~100,000 tokens. Loss functions, sampling temperature, and evaluation all rest on probability.

## The basics

A probability is a number in [0, 1] measuring how likely an event is. For all outcomes of an experiment, probabilities sum to 1.

```python
import numpy as np
rng = np.random.default_rng(0)

rolls = rng.integers(1, 7, size=100_000)     # simulate a fair die
print((rolls == 6).mean())                   # ~0.1667 = 1/6
print((rolls % 2 == 0).mean())               # P(even) ~ 0.5
```

Simulation is a great way to check intuition — the frequency approaches the probability as samples grow (law of large numbers).

Rules:
- **Complement:** `P(not A) = 1 - P(A)`
- **Independent events:** `P(A and B) = P(A) * P(B)` — two coin flips both heads: 0.25.
- **Either event:** `P(A or B) = P(A) + P(B) - P(A and B)`

## Conditional probability

`P(A | B)` = probability of A **given** B happened = `P(A and B) / P(B)`.

Example from a dataset of emails:

```python
import pandas as pd
emails = pd.DataFrame({
    "has_free": [1, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    "spam":     [1, 1, 0, 0, 0, 0, 0, 1, 0, 1],
})
p_spam_given_free = emails[emails.has_free == 1].spam.mean()
print(p_spam_given_free)     # 0.75  (3 of 4 'free' emails are spam)
```

A classifier essentially estimates `P(label | features)`. Language models estimate `P(next token | previous tokens)`.

## Bayes' theorem

Bayes lets you flip a conditional:

`P(A | B) = P(B | A) * P(A) / P(B)`

**Classic example:** a disease affects 1% of people. A test detects it 99% of the time (sensitivity) but has a 5% false-positive rate. You test positive. What's the chance you're sick?

```python
p_d = 0.01
p_pos_given_d = 0.99
p_pos_given_not_d = 0.05
p_pos = p_pos_given_d * p_d + p_pos_given_not_d * (1 - p_d)
p_d_given_pos = p_pos_given_d * p_d / p_pos
print(round(p_d_given_pos, 3))     # 0.167 - only ~17%!
```

Because the disease is rare, most positives are false alarms. This **base-rate** effect is exactly why accuracy is misleading on imbalanced data (fraud, rare diseases), and why precision matters (Module 4). The **Naive Bayes** classifier applies this theorem directly to text classification.

## Random variables and distributions

A **distribution** describes how probability spreads over possible values.

### Discrete

- **Bernoulli:** one yes/no trial (click or not) with probability p.
- **Binomial:** number of successes in n trials.
- **Categorical:** one of k classes with probabilities `p1..pk` — an LLM's next-token output is a categorical distribution.

```python
probs = np.array([0.6, 0.3, 0.1])            # P(cat), P(dog), P(bird)
samples = rng.choice(["cat", "dog", "bird"], size=10, p=probs)
print(samples)
```

### Continuous

- **Uniform:** all values in a range equally likely.
- **Normal (Gaussian):** the bell curve, defined by mean `mu` and standard deviation `sigma`. About 68% of values fall within 1 sigma, 95% within 2, 99.7% within 3.

```python
heights = rng.normal(loc=170, scale=8, size=100_000)
print(heights.mean(), heights.std())
print(((heights > 162) & (heights < 178)).mean())   # ~0.68
```

Why normal everywhere? The **Central Limit Theorem**: averages of many independent effects tend toward a normal distribution, regardless of the original distribution. Neural network weights are commonly initialized from normal distributions too.

## Expectation and variance

- **Expected value** `E[X]`: the long-run average — sum of value x probability.
- **Variance** `Var[X] = E[(X - mu)^2]`: spread. Standard deviation is its square root.

```python
values = np.array([0, 10, 100])     # lottery payouts
p = np.array([0.89, 0.10, 0.01])
ev = (values * p).sum()             # 2.0
var = ((values - ev) ** 2 * p).sum()
print(ev, var ** 0.5)
```

## Softmax: turning scores into probabilities

Models produce raw scores ("logits"). **Softmax** converts them into a categorical distribution:

```python
def softmax(logits, temperature=1.0):
    z = logits / temperature
    z = z - z.max()                 # numerical stability trick
    e = np.exp(z)
    return e / e.sum()

logits = np.array([2.0, 1.0, 0.1])
print(softmax(logits))                    # [0.66 0.24 0.10]
print(softmax(logits, temperature=0.5))   # sharper: [0.86 0.12 0.02]
print(softmax(logits, temperature=2.0))   # flatter
```

This is exactly the **temperature** parameter in LLM APIs: low temperature makes the model pick the most likely tokens (deterministic), high temperature makes outputs more random/creative.

## Key takeaways

- Conditional probability `P(A|B)` is what classifiers and LLMs estimate.
- Bayes' theorem + base rates explain why rare-event detection is hard.
- Know Bernoulli, categorical and normal distributions; expectation and variance summarize them.
- Softmax converts logits to probabilities; temperature controls sharpness.
""", r"""
**Task: Probability lab.**

1. Simulate 1,000,000 pairs of dice rolls and estimate P(sum = 7) and P(at least one 6). Compare to exact answers (6/36 and 11/36).
2. Re-run the disease example with prevalence 0.1%, 1%, 10% and 30%. Plot P(sick | positive) vs prevalence.
3. Implement `softmax` with temperature and sample 1,000 "next tokens" from logits `[3.0, 2.5, 1.0, 0.2]` at temperatures 0.2, 1.0 and 2.0. Plot how often each token is chosen.
4. Show the Central Limit Theorem: take means of 30 samples from an exponential distribution, repeat 10,000 times, and plot the histogram of the means.
""", [
    Q("A test is 99% sensitive with a 5% false-positive rate for a disease with 1% prevalence. Roughly what is P(disease | positive)?", ["99%", "95%", "About 17%", "1%"], 2, "Bayes: 0.99*0.01 / (0.99*0.01 + 0.05*0.99) is about 0.167 — most positives are false because the disease is rare."),
    Q("What does lowering the softmax temperature do?", ["Makes the distribution flatter and more random", "Makes the distribution sharper, concentrating probability on top choices", "Changes which token has the highest score", "Has no effect"], 1, "Dividing logits by a small temperature exaggerates differences, so the highest-scoring options dominate."),
    Q("What does a language model's output layer represent at each step?", ["A normal distribution over words", "A categorical probability distribution over the vocabulary", "A single deterministic word", "The word's embedding"], 1, "After softmax, the model outputs P(next token | context) over every token in its vocabulary."),
], [
    R("Seeing Theory: a visual introduction to probability", "https://seeing-theory.brown.edu/", "article"),
    R("3Blue1Brown: Bayes theorem, the geometry of changing beliefs", "https://www.youtube.com/watch?v=HZGCoVF3YvM", "video"),
    R("Harvard Stat 110 (Joe Blitzstein) - free lectures", "https://projects.iq.harvard.edu/stat110/home", "course"),
]))

lessons.append(L("m03-l6-statistics", "Statistics for ML: Sampling, Likelihood & Loss Functions", 45, r"""
## From probability to statistics

Probability asks "given the model, what data do we expect?" **Statistics** asks the reverse: "given the data, what can we infer about the model?" Machine learning is applied statistics at scale.

## Descriptive statistics

```python
import numpy as np
rng = np.random.default_rng(1)
salaries = np.concatenate([rng.normal(80_000, 15_000, 990), [2_000_000] * 10])  # 10 executives

print(np.mean(salaries))      # pulled up by outliers
print(np.median(salaries))    # robust to outliers
print(np.std(salaries))
print(np.percentile(salaries, [25, 50, 75, 95]))
```

- **Mean** is sensitive to outliers; **median** is robust. Report medians for skewed data like salaries or latency (that's why systems use p50/p95/p99 latency).
- **Variance/std** measure spread; **percentiles** describe the shape.

## Correlation (and its limits)

Pearson correlation `r` in [-1, 1] measures linear association.

```python
x = rng.normal(size=500)
y = 2 * x + rng.normal(size=500)
print(np.corrcoef(x, y)[0, 1])     # ~0.9

y2 = x ** 2                        # perfect but non-linear relationship
print(np.corrcoef(x, y2)[0, 1])    # ~0: correlation misses it!
```

Correlation is not causation: ice-cream sales and drownings correlate because both rise in summer (a **confounder**).

## Samples, populations and the bias it causes

Your dataset is a **sample** from a larger population. Conclusions generalize only if the sample is representative. Models trained on biased samples inherit that bias — e.g. a hiring model trained on historical decisions. Train/validation/test splits exist precisely because performance on the training sample overestimates performance on new data.

## Confidence intervals and A/B tests (brief)

If model A scores 85.2% accuracy and model B 85.9% on 1,000 test examples, is B really better? Estimate uncertainty with a **bootstrap**: resample the test set with replacement many times and look at the spread.

```python
correct_b = rng.random(1000) < 0.859      # simulated per-example correctness
boot = [rng.choice(correct_b, size=1000, replace=True).mean() for _ in range(5000)]
lo, hi = np.percentile(boot, [2.5, 97.5])
print(f"accuracy {correct_b.mean():.3f}, 95% CI [{lo:.3f}, {hi:.3f}]")
```

The interval is about +/-2%, so a 0.7% difference is likely noise. A **p-value** is the probability of seeing a difference at least this large if there were truly no difference; a small p-value (< 0.05 by convention) suggests a real effect. AI engineers use these ideas when A/B testing prompts or models in production.

## Maximum Likelihood Estimation (MLE)

The core idea behind most loss functions: **choose parameters that make the observed data most probable.**

Coin example: you see 7 heads in 10 flips. Which bias p makes this most likely?

```python
ps = np.linspace(0.01, 0.99, 99)
likelihood = ps ** 7 * (1 - ps) ** 3
print(ps[likelihood.argmax()])     # 0.7 - the MLE is the observed frequency
```

Products of many small probabilities underflow, so we maximize the **log-likelihood** instead (sums instead of products), or equivalently **minimize the negative log-likelihood (NLL)**.

## Loss functions are negative log-likelihoods

### Mean Squared Error

If you assume targets are your prediction plus Gaussian noise, maximizing likelihood is equivalent to minimizing **MSE**. That is why regression uses MSE.

### Cross-entropy (log loss)

For classification, the model outputs probabilities. The likelihood of the data is the probability the model assigned to each **true** label. The negative log of that is **cross-entropy loss**:

```python
def cross_entropy(probs, true_idx):
    return -np.log(probs[true_idx])

print(cross_entropy(np.array([0.7, 0.2, 0.1]), 0))   # 0.36  confident & right: low loss
print(cross_entropy(np.array([0.1, 0.2, 0.7]), 0))   # 2.30  confident & wrong: high loss
print(cross_entropy(np.array([0.34, 0.33, 0.33]), 0))# 1.08  unsure
```

Cross-entropy punishes confident wrong answers severely. **LLM pretraining minimizes exactly this**: the cross-entropy of predicting each next token in trillions of tokens of text. The **perplexity** metric is just `exp(average cross-entropy)` — roughly "how many tokens the model is choosing between."

For binary classification (logistic regression), it becomes **binary cross-entropy**:

```python
def bce(p, y):
    p = np.clip(p, 1e-12, 1 - 1e-12)    # avoid log(0)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

print(bce(np.array([0.9, 0.2, 0.8]), np.array([1, 0, 1])))   # low
```

## Entropy and KL divergence (intuition)

- **Entropy** measures uncertainty of a distribution: a fair coin (1 bit) is more uncertain than a 99/1 coin.
- **KL divergence** measures how one distribution differs from another. It shows up in RLHF (keeping a fine-tuned LLM close to the original), in knowledge distillation, and in VAEs.

```python
def entropy(p):
    p = p[p > 0]
    return -(p * np.log2(p)).sum()

print(entropy(np.array([0.5, 0.5])), entropy(np.array([0.99, 0.01])))   # 1.0 vs 0.08
```

## The bias-variance trade-off (preview)

Prediction error comes from **bias** (model too simple to capture the pattern — underfitting) and **variance** (model too sensitive to the particular training sample — overfitting). Every technique in Module 4 — regularization, cross-validation, ensembles — manages this trade-off.

## Key takeaways

- Use medians/percentiles for skewed data; correlation only captures linear relationships and isn't causation.
- Quantify uncertainty (bootstrap, confidence intervals) before claiming one model beats another.
- MLE: pick parameters that make data most likely; MSE and cross-entropy are negative log-likelihoods.
- LLMs are trained by minimizing next-token cross-entropy; perplexity = exp(cross-entropy).
""", r"""
**Task: Losses and uncertainty.**

1. Implement `mse`, `binary_cross_entropy` and `categorical_cross_entropy` in NumPy (with clipping for numerical safety).
2. Plot binary cross-entropy for y=1 as the predicted p goes from 0.01 to 0.99. Explain the shape in two sentences.
3. Compute the perplexity of a "model" that assigns probabilities `[0.5, 0.25, 0.8, 0.1]` to the true next tokens in a 4-token sentence.
4. Simulate two classifiers with true accuracies 0.86 and 0.87 on a 500-example test set; use the bootstrap to compute 95% CIs for both. Are they distinguishable? How large would the test set need to be?
""", [
    Q("Why is cross-entropy preferred over accuracy as a training loss for classifiers?", ["It is easier to print", "It is differentiable and penalizes confident wrong predictions heavily", "It always equals zero", "Accuracy can't be computed during training"], 1, "Accuracy is a step function with zero gradient almost everywhere; cross-entropy is smooth and gives useful gradients."),
    Q("What is minimized during LLM pretraining?", ["Mean squared error of embeddings", "Cross-entropy of predicting the next token", "Number of parameters", "Perplexity of images"], 1, "Pretraining maximizes the likelihood of each next token, i.e. minimizes next-token cross-entropy."),
    Q("For a highly skewed variable like salary, which statistic best represents a 'typical' value?", ["Mean", "Median", "Max", "Variance"], 1, "The median is robust to extreme outliers that drag the mean upward."),
], [
    R("StatQuest with Josh Starmer (YouTube channel)", "https://www.youtube.com/@statquest", "video"),
    R("Think Stats, 3rd ed. (Allen Downey, free online)", "https://allendowney.github.io/ThinkStats/", "book"),
    R("Chris Olah: Visual Information Theory", "https://colah.github.io/posts/2015-09-Visual-Information/", "article"),
]))

MODULE = M("m03-math", 3, "Math for ML (just enough)", "Beginner", 2,
    "Build intuition-first understanding of the linear algebra, calculus, probability and statistics that make machine learning work. Every concept is shown in NumPy code and tied directly to where it appears in real models, from linear regression to LLMs.",
    [
        "Explain vectors, dot products, cosine similarity and matrix multiplication and read tensor shapes confidently",
        "Interpret derivatives, gradients and the chain rule as the basis of backpropagation",
        "Implement gradient descent from scratch and tune the learning rate",
        "Reason about probability, Bayes' theorem, distributions and softmax temperature",
        "Connect maximum likelihood to MSE and cross-entropy loss and quantify uncertainty with the bootstrap",
    ],
    lessons,
    ("Logistic Regression from Scratch (NumPy only)", r"""
## Goal
Prove you understand the maths by building a binary classifier with no ML libraries — just NumPy — and matching scikit-learn's result.

## Spec
- Dataset: scikit-learn's breast cancer dataset (`load_breast_cancer`), 30 features, binary target.
- Model: `p = sigmoid(X @ w + b)`.
- Loss: binary cross-entropy (with L2 regularization term `lambda * ||w||^2`).
- Training: mini-batch gradient descent with your own derived gradients: `dw = X.T @ (p - y) / n + 2*lambda*w`, `db = mean(p - y)`.

## Steps
1. Split 80/20 with a fixed seed; standardize features using **training** statistics only.
2. Derive the gradient on paper using the chain rule (include the derivation in the notebook in Markdown).
3. Implement gradient checking: compare analytical and numerical gradients on a small batch (relative error < 1e-6).
4. Train, plot the loss curve, and report test accuracy.
5. Compare against `sklearn.linear_model.LogisticRegression` — accuracy should be within ~1-2%.

## Stretch goals
- Extend to multi-class with softmax + categorical cross-entropy on the digits dataset.
- Add momentum and compare convergence speed.
- Bootstrap a 95% confidence interval for your test accuracy.
- Visualize the dataset in 2-D with PCA computed via `np.linalg.svd`.
"""))
