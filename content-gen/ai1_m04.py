from ai1_common import L, Q, R, M

lessons = []

lessons.append(L("m04-l1-what-is-ml", "What Machine Learning Is & the ML Workflow", 40, r"""
## Rules vs learning

As a Java developer you write **rules**: `if (amount > 10000 && country != homeCountry) flagFraud();`. That works until the rules become too many, too fuzzy, or change constantly. **Machine learning** flips the process: you provide **examples** (inputs with correct answers) and an algorithm **learns the rules** — a function mapping inputs to outputs.

```
Traditional programming:  rules + data  -> answers
Machine learning:         data + answers -> rules (a model)
```

## Vocabulary

| Term | Meaning | Example (house prices) |
|---|---|---|
| Sample / example / row | one observation | one house |
| Feature (X) | input variable | size, rooms, location |
| Label / target (y) | what we predict | price |
| Model | learned function f(X) -> y | a fitted regression |
| Training | finding parameters from data | `model.fit(X, y)` |
| Inference / prediction | applying the model to new data | `model.predict(X_new)` |
| Hyperparameter | setting chosen before training | tree depth, learning rate |

## Types of machine learning

### Supervised learning (labels available)

- **Regression:** predict a number — house price, delivery time, demand.
- **Classification:** predict a category — spam/not spam, churn/stay, digit 0-9.

### Unsupervised learning (no labels)

- **Clustering:** group similar customers.
- **Dimensionality reduction:** compress 100 features into 2 for visualization.
- **Anomaly detection:** spot unusual transactions.

### Others you'll hear about

- **Self-supervised learning:** labels come from the data itself — "predict the next word" needs no human labelling. This is how LLMs are pretrained.
- **Reinforcement learning:** an agent learns from rewards (games, robotics, and RLHF for LLMs).

## The ML workflow

1. **Frame the problem:** what decision will the prediction support? What's the metric of success? Is ML even needed?
2. **Get data** and do EDA (Module 2).
3. **Split** into train / validation / test sets.
4. **Prepare features:** clean, encode, scale.
5. **Train** a simple baseline first, then better models.
6. **Evaluate** on validation data with the right metric; tune.
7. **Test** once on held-out test data.
8. **Deploy and monitor** — data drifts over time.

## Why split the data?

The goal is **generalization**: performing well on data the model has never seen. If you evaluate on training data, a model that memorizes scores perfectly but fails in production. So hold data back:

- **Training set (~60-80%):** the model learns from this.
- **Validation set (~10-20%):** used to compare models and tune hyperparameters.
- **Test set (~10-20%):** touched once at the very end for an honest estimate.

Think of it like exam prep: practice questions (train), mock tests (validation), the real exam (test). If you study the real exam paper, your score means nothing.

## scikit-learn: one API for everything

scikit-learn is the standard library for classical ML. Every model follows the same interface — like a Java interface every class implements:

```python
model = SomeModel(hyperparams)   # construct
model.fit(X_train, y_train)      # learn
model.predict(X_test)            # infer
model.score(X_test, y_test)      # default metric
```

## Your first model in 15 lines

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

X, y = load_iris(return_X_y=True)          # 150 flowers, 4 features, 3 species
print(X.shape, y.shape)                    # (150, 4) (150,)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)   # stratify keeps class ratios

model = KNeighborsClassifier(n_neighbors=5)
model.fit(X_train, y_train)
preds = model.predict(X_test)
print("accuracy:", accuracy_score(y_test, preds))   # ~0.97
```

k-Nearest Neighbours classifies a flower by looking at the 5 most similar training flowers (by distance — Module 3) and taking a majority vote. Simple, but a great baseline.

## Always start with a baseline

Before any clever model, measure a trivial one. If 70% of customers don't churn, a model that always predicts "no churn" is 70% accurate. Your model must beat that.

```python
from sklearn.dummy import DummyClassifier
baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
print("baseline:", baseline.score(X_test, y_test))   # ~0.33 for 3 balanced classes
```

## When NOT to use ML

- A clear deterministic rule exists (tax calculation).
- You lack data or can't get labels.
- Errors are unacceptable and must be fully explainable.
- An LLM API call with a good prompt solves it faster — a very real option for AI engineers in 2026 (e.g. classifying support tickets with few examples). Classical ML still wins for tabular data, high volume, low latency and low cost.

## Key takeaways

- ML learns a function from examples; supervised = labelled, unsupervised = not.
- Regression predicts numbers; classification predicts categories.
- Split into train/validation/test to measure generalization honestly.
- scikit-learn's `fit` / `predict` API is universal; always compare to a baseline.
""", r"""
**Task: Your first ML experiment.**

1. Load the wine dataset (`sklearn.datasets.load_wine`). Print feature names, shape and class balance.
2. Split 80/20 with stratification and a fixed random state.
3. Train a `DummyClassifier` baseline and a `KNeighborsClassifier` with k = 1, 3, 5, 15. Record test accuracy for each.
4. Now standardize features with `StandardScaler` (fit on train only) and repeat. Why does accuracy jump for kNN? (Hint: distances and feature scales.)
5. For 5 real-world problems you know from your Java job (e.g. ticket routing, invoice fraud), classify each as regression/classification/clustering/not-ML and justify.
""", [
    Q("Predicting the number of days until a customer churns is which type of problem?", ["Classification", "Regression", "Clustering", "Dimensionality reduction"], 1, "The target is a continuous number, so it is regression."),
    Q("Why should the test set be used only once at the end?", ["It is too small to use repeatedly", "Repeatedly tuning on it leaks information and makes its score an over-optimistic estimate", "scikit-learn forbids it", "It contains no labels"], 1, "Decisions made by looking at test performance effectively train on the test set, so it no longer measures generalization."),
    Q("How are large language models pretrained?", ["Supervised learning with human labels for every token", "Self-supervised learning predicting the next token", "Unsupervised clustering", "Pure reinforcement learning"], 1, "The text itself provides the labels: the next token is the target, so no manual labelling is needed."),
], [
    R("scikit-learn: Getting Started", "https://scikit-learn.org/stable/getting_started.html", "docs"),
    R("Google Machine Learning Crash Course", "https://developers.google.com/machine-learning/crash-course", "course"),
    R("Andrew Ng: Machine Learning Specialization", "https://www.coursera.org/specializations/machine-learning-introduction", "course"),
]))

lessons.append(L("m04-l2-regression-classification", "Linear & Logistic Regression in Practice", 50, r"""
## Linear regression

Linear regression models the target as a weighted sum of features plus a bias:

`y_hat = w1*x1 + w2*x2 + ... + wd*xd + b`

Training finds weights that minimize Mean Squared Error (you built this from scratch in Module 3). In scikit-learn:

```python
import numpy as np
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

data = fetch_california_housing(as_frame=True)
X, y = data.data, data.target                  # target in $100k units
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

lin = LinearRegression().fit(X_train, y_train)
pred = lin.predict(X_test)
print("MAE:", mean_absolute_error(y_test, pred))   # ~0.53 -> about $53k average error
print("R2 :", r2_score(y_test, pred))               # ~0.58
```

### Interpreting coefficients

```python
import pandas as pd
coefs = pd.Series(lin.coef_, index=X.columns).sort_values()
print(coefs)
```

Each coefficient says: holding other features fixed, a one-unit increase in this feature changes the prediction by this much. `MedInc` (median income) has a strong positive coefficient. Caveats: coefficients are only comparable if features are on the same scale, and correlated features make them unstable.

### Polynomial features: curves with a linear model

A linear model can fit curves if you give it non-linear features:

```python
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

rng = np.random.default_rng(0)
x = rng.uniform(-3, 3, 100).reshape(-1, 1)     # sklearn expects 2-D X
y_curve = 0.5 * x.ravel() ** 2 - x.ravel() + rng.normal(0, 0.3, 100)

poly_model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
poly_model.fit(x, y_curve)
print(poly_model.score(x, y_curve))   # R2 close to 1
```

Higher degrees fit training data better — and eventually overfit (lesson 4).

## Logistic regression: linear model for classification

Despite its name, logistic regression is a **classifier**. It computes a linear score and squashes it through the sigmoid to get a probability:

`P(y=1 | x) = sigmoid(w . x + b) = 1 / (1 + e^-(w.x + b))`

It's trained with binary cross-entropy (Module 3). The **decision boundary** is where the probability equals 0.5 — a straight line (hyperplane) in feature space.

```python
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

X, y = load_breast_cancer(return_X_y=True)     # 1 = benign, 0 = malignant
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
clf.fit(X_train, y_train)
print("accuracy:", clf.score(X_test, y_test))      # ~0.98

probs = clf.predict_proba(X_test[:3])             # [[P(class0), P(class1)], ...]
print(probs.round(3))
print(clf.predict(X_test[:3]))                    # threshold 0.5 applied
```

### Probabilities and thresholds

`predict` uses a 0.5 threshold, but you can choose another based on business cost. For cancer screening, missing a malignant tumour is far worse than a false alarm, so you might flag anything with P(malignant) > 0.2:

```python
p_malignant = clf.predict_proba(X_test)[:, 0]
flag = p_malignant > 0.2
print("flagged:", flag.sum(), "of", len(flag))
```

Choosing thresholds is a product decision, not just a technical one — and it's a common interview discussion.

### Multi-class

`LogisticRegression` handles multiple classes automatically using softmax (multinomial) — one weight vector per class:

```python
from sklearn.datasets import load_iris
Xi, yi = load_iris(return_X_y=True)
multi = LogisticRegression(max_iter=1000).fit(Xi, yi)
print(multi.predict_proba(Xi[:1]).round(3))   # three probabilities summing to 1
```

## Regularized linear models

When there are many features, plain linear regression overfits. **Regularization** adds a penalty on large weights:

- **Ridge (L2):** penalty `alpha * sum(w^2)` — shrinks all weights smoothly.
- **Lasso (L1):** penalty `alpha * sum(|w|)` — drives some weights to exactly 0 (automatic feature selection).
- **ElasticNet:** a mix.

```python
from sklearn.linear_model import Ridge, Lasso
# back to the housing regression data
Xh_tr, Xh_te, yh_tr, yh_te = train_test_split(data.data, data.target, test_size=0.2, random_state=42)
ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(Xh_tr, yh_tr)
lasso = make_pipeline(StandardScaler(), Lasso(alpha=0.05)).fit(Xh_tr, yh_tr)
print("non-zero lasso weights:", (lasso[-1].coef_ != 0).sum(), "of", Xh_tr.shape[1])
```

In `LogisticRegression`, regularization strength is `C` — the **inverse** of alpha (smaller C = stronger regularization). A classic trick question.

## Why linear models still matter

- Fast to train and predict, even on millions of rows.
- Interpretable — regulators and stakeholders can read the coefficients.
- Strong baseline; with good features, often hard to beat.
- A neural network's final layer is literally a logistic regression on learned features.

## Key takeaways

- Linear regression: weighted sum, MSE loss; coefficients interpretable when features are scaled.
- Logistic regression: linear score -> sigmoid -> probability; choose thresholds by business cost.
- `predict_proba` gives probabilities; `predict` applies a threshold.
- Ridge/Lasso regularize; `C` in LogisticRegression is inverse strength.
""", r"""
**Task: Two models, two problems.**

1. On California housing, train `LinearRegression`, `Ridge` and `Lasso` (with scaling). Compare MAE and R2 on the test set and show which features Lasso zeroed out at `alpha=0.05`.
2. Add polynomial features of degree 2 and 3 to a linear model; report train vs test R2. What happens at degree 3?
3. On breast cancer, train logistic regression. For thresholds 0.1 to 0.9, compute how many malignant cases are missed. Pick a threshold and justify it in one paragraph.
4. Print the 5 most influential features (largest absolute coefficients after scaling).
""", [
    Q("What does logistic regression output before thresholding?", ["A class label only", "A probability between 0 and 1 via the sigmoid", "A cluster id", "A continuous unbounded number as the final output"], 1, "It computes a linear score then applies sigmoid to give P(y=1|x); a threshold turns that into a label."),
    Q("Which regularization tends to set some coefficients exactly to zero?", ["Ridge (L2)", "Lasso (L1)", "No regularization", "Dropout"], 1, "The L1 penalty's geometry produces sparse solutions, effectively selecting features."),
    Q("In scikit-learn's LogisticRegression, what does decreasing C do?", ["Weakens regularization", "Strengthens regularization", "Increases the number of classes", "Changes the solver"], 1, "C is the inverse of regularization strength; smaller C means a stronger penalty on weights."),
], [
    R("scikit-learn user guide: Linear Models", "https://scikit-learn.org/stable/modules/linear_model.html", "docs"),
    R("StatQuest: Logistic Regression", "https://www.youtube.com/watch?v=yIYKR4sgzI8", "video"),
    R("An Introduction to Statistical Learning with Python (free PDF)", "https://www.statlearning.com/", "book"),
]))

lessons.append(L("m04-l3-metrics", "Evaluation Metrics: Beyond Accuracy", 50, r"""
## The right metric is a business decision

A model is only "good" relative to a metric that reflects real costs. Choosing the wrong metric is how teams ship models that look great and do harm. Interviewers love this topic.

## Regression metrics

```python
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

y_true = np.array([300, 250, 400, 500, 150])   # house prices in $k
y_pred = np.array([310, 230, 420, 380, 160])

mae = mean_absolute_error(y_true, y_pred)         # 34.0
rmse = mean_squared_error(y_true, y_pred) ** 0.5  # ~55.0
r2 = r2_score(y_true, y_pred)
print(mae, rmse, r2)
```

- **MAE** (mean absolute error): average error in the target's units. Easy to explain: "we're off by $34k on average."
- **RMSE** (root mean squared error): squares errors first, so it **punishes big misses** more. The 120k miss dominates it.
- **R2** (coefficient of determination): fraction of variance explained; 1 is perfect, 0 equals predicting the mean, negative is worse than the mean.
- **MAPE**: percentage error — intuitive, but breaks when true values are near zero.

## The confusion matrix

For binary classification, every prediction falls into one of four cells. Let "positive" = the thing we're trying to detect (fraud, disease, spam).

|  | Predicted positive | Predicted negative |
|---|---|---|
| **Actually positive** | True Positive (TP) | False Negative (FN) - missed |
| **Actually negative** | False Positive (FP) - false alarm | True Negative (TN) |

```python
from sklearn.metrics import confusion_matrix, classification_report

y_true = np.array([1, 0, 1, 1, 0, 0, 0, 1, 0, 0])
y_pred = np.array([1, 0, 0, 1, 0, 1, 0, 1, 0, 0])
print(confusion_matrix(y_true, y_pred))
# [[5 1]     row 0: TN=5, FP=1
#  [1 3]]    row 1: FN=1, TP=3
```

## Precision, recall, F1

- **Accuracy** = (TP + TN) / all. Misleading on imbalanced data.
- **Precision** = TP / (TP + FP): "when the model says positive, how often is it right?" — matters when false alarms are costly (spam filter deleting real email).
- **Recall** (sensitivity) = TP / (TP + FN): "of all real positives, how many did we catch?" — matters when misses are costly (cancer, fraud).
- **F1** = harmonic mean of precision and recall: a single balanced number.

```python
print(classification_report(y_true, y_pred, digits=3))
```

### The imbalance trap, demonstrated

```python
y_true = np.array([0] * 990 + [1] * 10)          # 1% fraud
y_lazy = np.zeros(1000, dtype=int)               # always "not fraud"
from sklearn.metrics import accuracy_score, recall_score
print(accuracy_score(y_true, y_lazy))            # 0.99 - looks great
print(recall_score(y_true, y_lazy))              # 0.0  - catches no fraud
```

### The precision-recall trade-off

Raising the threshold makes the model more conservative: precision goes up, recall goes down. You choose the operating point based on costs.

```python
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score

X, y = make_classification(n_samples=5000, weights=[0.95], random_state=0)  # imbalanced
X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, random_state=0)
proba = LogisticRegression(max_iter=1000).fit(X_tr, y_tr).predict_proba(X_te)[:, 1]

for t in [0.2, 0.5, 0.8]:
    p = (proba >= t).astype(int)
    print(f"t={t}: precision={precision_score(y_te, p):.2f} recall={recall_score(y_te, p):.2f}")
```

## ROC-AUC and PR-AUC

Instead of judging one threshold, threshold-independent metrics summarize all of them:

- **ROC curve:** true positive rate (recall) vs false positive rate across thresholds. **ROC-AUC** = probability that the model ranks a random positive above a random negative. 0.5 = random, 1.0 = perfect.
- **PR curve / PR-AUC (average precision):** precision vs recall. More informative than ROC-AUC under heavy imbalance.

```python
from sklearn.metrics import roc_auc_score, average_precision_score
print("ROC-AUC:", roc_auc_score(y_te, proba))
print("PR-AUC :", average_precision_score(y_te, proba))
```

Also worth knowing: **log loss** evaluates the quality of the probabilities themselves; **calibration** checks whether "70% confident" really means right 70% of the time.

## Multi-class metrics

Per-class precision/recall are averaged:

- **macro:** simple average across classes — treats rare classes equally.
- **weighted:** weighted by class frequency.
- **micro:** pools all decisions (equals accuracy for single-label problems).

## Choosing a metric — cheat sheet

| Scenario | Primary metric |
|---|---|
| Balanced classes, equal costs | accuracy, F1 |
| Missing positives is costly (disease, fraud) | recall (with a precision floor) |
| False alarms costly (spam, auto-blocking) | precision |
| Ranking quality / imbalanced | PR-AUC, ROC-AUC |
| Regression with outliers you can tolerate | MAE |
| Regression where big misses are disasters | RMSE |

## Connecting to LLM evaluation

The same thinking applies to AI systems: a RAG retriever is measured with recall@k and precision@k; an LLM classifier with precision/recall per label; and LLM-as-judge setups are checked for agreement with humans. Metrics thinking transfers directly.

## Key takeaways

- MAE is interpretable; RMSE punishes big errors; R2 compares to predicting the mean.
- Confusion matrix -> precision (trust in positives) and recall (coverage of positives).
- Accuracy lies on imbalanced data; use recall, precision, F1, PR-AUC.
- Thresholds trade precision for recall; choose based on costs.
""", r"""
**Task: Metric detective.**

1. Using `make_classification(n_samples=10000, weights=[0.98])`, train logistic regression and print the confusion matrix, classification report, ROC-AUC and PR-AUC.
2. Plot precision and recall versus threshold (`precision_recall_curve`). Find the threshold that gives recall >= 0.8 with the highest precision.
3. Assume a missed fraud costs $500 and a false alarm costs $5. Write a function computing total cost for each threshold and pick the cheapest.
4. Write the formulas for precision, recall and F1 from memory, and compute them by hand for the 10-example confusion matrix in the lesson.
""", [
    Q("A cancer screening model should rarely miss actual cancer cases. Which metric matters most?", ["Precision", "Recall", "Accuracy", "R2"], 1, "Recall = TP/(TP+FN) measures how many actual positives are caught; missing cases (FN) is the costly error."),
    Q("Precision is defined as ...", ["TP / (TP + FN)", "TP / (TP + FP)", "(TP + TN) / total", "FP / (FP + TN)"], 1, "Precision answers: of everything predicted positive, what fraction was truly positive."),
    Q("Why might RMSE be much larger than MAE on the same predictions?", ["RMSE ignores small errors", "Squaring errors gives large misses disproportionate weight", "RMSE is in different units", "MAE is always zero"], 1, "RMSE squares residuals before averaging, so a few big errors dominate it."),
], [
    R("scikit-learn: Metrics and scoring", "https://scikit-learn.org/stable/modules/model_evaluation.html", "docs"),
    R("Google ML Crash Course: Classification metrics", "https://developers.google.com/machine-learning/crash-course/classification", "course"),
    R("StatQuest: ROC and AUC, clearly explained", "https://www.youtube.com/watch?v=4jRBRDbJemM", "video"),
]))

lessons.append(L("m04-l4-overfitting", "Overfitting, Cross-Validation & Hyperparameter Tuning", 50, r"""
## The central problem of ML

A model can fail in two opposite ways:

- **Underfitting (high bias):** too simple to capture the pattern. Bad on training AND test data. Example: a straight line for a curved relationship.
- **Overfitting (high variance):** memorizes training noise. Great on training data, poor on new data. Example: a degree-15 polynomial wiggling through every point.

The **bias-variance trade-off**: more model complexity reduces bias but increases variance. The goal is the sweet spot that generalizes.

## Seeing it happen

```python
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

rng = np.random.default_rng(0)
X = rng.uniform(0, 1, 40).reshape(-1, 1)
y = np.sin(2 * np.pi * X.ravel()) + rng.normal(0, 0.2, 40)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=0)

for degree in [1, 3, 15]:
    m = make_pipeline(PolynomialFeatures(degree), LinearRegression()).fit(X_tr, y_tr)
    tr = mean_squared_error(y_tr, m.predict(X_tr))
    te = mean_squared_error(y_te, m.predict(X_te))
    print(f"degree {degree:2d}: train MSE {tr:.3f}  test MSE {te:.3f}")
# degree 1 : both high      -> underfit
# degree 3 : both low       -> good
# degree 15: train ~0, test huge -> overfit
```

**Diagnosis rule:** compare training and validation error.

| Train error | Validation error | Diagnosis | Fixes |
|---|---|---|---|
| high | high | underfitting | more complex model, better features, train longer |
| low | high | overfitting | more data, regularization, simpler model, early stopping |
| low | low (close) | good fit | ship it (after testing) |

## Fighting overfitting

1. **More data** — the most reliable fix.
2. **Regularization** — penalize complexity (L1/L2, tree depth limits, dropout in neural nets).
3. **Simpler models / fewer features.**
4. **Early stopping** — stop training when validation error starts rising.
5. **Ensembles** — averaging many models reduces variance (next lesson).

## Cross-validation: a more reliable estimate

A single validation split is noisy — you might get a lucky or unlucky split. **k-fold cross-validation** splits training data into k folds; trains k times, each time validating on a different fold; and averages the scores.

```
Fold 1: [VAL][trn][trn][trn][trn]
Fold 2: [trn][VAL][trn][trn][trn]
...
Fold 5: [trn][trn][trn][trn][VAL]
```

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

X, y = load_breast_cancer(return_X_y=True)
model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=cv, scoring="f1")
print(scores.round(3), "mean:", scores.mean().round(3), "+/-", scores.std().round(3))
```

The standard deviation tells you how stable the model is. Variants:

- **StratifiedKFold:** keeps class proportions in each fold (use for classification).
- **GroupKFold:** keeps all rows of a group (e.g. same customer/patient) in one fold — prevents leakage.
- **TimeSeriesSplit:** always trains on the past and validates on the future. Never shuffle time series!

## Hyperparameter tuning

Parameters (weights) are learned; **hyperparameters** (regularization strength, tree depth, k in kNN) are chosen by you. Tune them with cross-validation on the training set only.

### Grid search

```python
from sklearn.model_selection import GridSearchCV

pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))
param_grid = {
    "logisticregression__C": [0.01, 0.1, 1, 10, 100],
    "logisticregression__penalty": ["l1", "l2"],
    "logisticregression__solver": ["liblinear"],
}
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=0)
search = GridSearchCV(pipe, param_grid, cv=5, scoring="f1", n_jobs=-1)
search.fit(X_tr, y_tr)
print(search.best_params_, round(search.best_score_, 3))
print("test F1:", round(search.score(X_te, y_te), 3))     # final honest check
```

Note the `stepname__param` syntax for parameters inside pipelines.

### Random search and Bayesian optimization

Grid search explodes combinatorially. **RandomizedSearchCV** samples combinations and usually finds good settings faster. Libraries like **Optuna** use smarter Bayesian search and are popular for both classical ML and deep learning.

```python
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import loguniform
rs = RandomizedSearchCV(pipe, {"logisticregression__C": loguniform(1e-3, 1e3)},
                        n_iter=30, cv=5, scoring="f1", random_state=0, n_jobs=-1)
rs.fit(X_tr, y_tr)
```

## Learning curves

Plot score versus training-set size to decide whether more data would help:

```python
from sklearn.model_selection import learning_curve
sizes, train_sc, val_sc = learning_curve(model, X, y, cv=5,
                                         train_sizes=np.linspace(0.1, 1.0, 5))
print(train_sc.mean(axis=1).round(3), val_sc.mean(axis=1).round(3))
```

If validation score is still climbing at full size, collect more data. If the curves have converged at a low score, you need a better model or features.

## Data leakage: the silent killer

Leakage makes validation scores look better than reality. Common causes:

- Fitting a scaler/imputer on the full dataset before splitting (use pipelines — lesson 6).
- Features that encode the target or future information.
- Duplicate or related rows split across train and test.

## Key takeaways

- Underfitting = high bias; overfitting = high variance; diagnose by comparing train vs validation error.
- Use k-fold (stratified/group/time-series) CV for reliable estimates.
- Tune hyperparameters with GridSearchCV/RandomizedSearchCV on training data, then test once.
- Learning curves tell you whether more data will help; guard against leakage.
""", r"""
**Task: Tame a decision tree.**

1. On the breast cancer dataset, train `DecisionTreeClassifier` with `max_depth` from 1 to 20. Plot training accuracy and 5-fold CV accuracy against depth. Identify underfitting and overfitting zones.
2. Use `GridSearchCV` over `max_depth`, `min_samples_leaf` and `criterion`; report best params and test accuracy.
3. Repeat with `RandomizedSearchCV` (20 iterations) and compare time and result.
4. Plot a learning curve for the best model. Would more data help?
5. Deliberately create leakage: scale the full dataset before splitting and add a feature equal to `y + noise`. Show how the CV score becomes unrealistically high.
""", [
    Q("A model has 99% training accuracy but 70% validation accuracy. What is happening?", ["Underfitting", "Overfitting", "Perfect fit", "Data is too small to tell"], 1, "A large gap between training and validation performance indicates high variance — overfitting."),
    Q("Which cross-validation strategy should you use for time-series forecasting?", ["Shuffled KFold", "StratifiedKFold", "TimeSeriesSplit", "LeaveOneOut with shuffling"], 2, "TimeSeriesSplit trains on the past and validates on the future, avoiding leakage of future information."),
    Q("What is the difference between a parameter and a hyperparameter?", ["There is none", "Parameters are learned from data; hyperparameters are set before training", "Hyperparameters are learned; parameters are set manually", "Parameters only exist in neural networks"], 1, "Weights are learned during fit; settings like regularization strength or tree depth are chosen by the practitioner."),
], [
    R("scikit-learn: Cross-validation", "https://scikit-learn.org/stable/modules/cross_validation.html", "docs"),
    R("scikit-learn: Tuning hyperparameters", "https://scikit-learn.org/stable/modules/grid_search.html", "docs"),
    R("StatQuest: Bias and Variance", "https://www.youtube.com/watch?v=EuBBz3bI-aA", "video"),
]))

lessons.append(L("m04-l5-trees-ensembles", "Decision Trees, Random Forests & Gradient Boosting", 55, r"""
## Decision trees: a learned if-else chain

A decision tree is something every programmer already understands — nested if/else statements, except the algorithm chooses the conditions:

```java
if (income > 5.0) {
    if (latitude < 34.5) return 4.2; else return 3.1;
} else {
    if (rooms > 6) return 2.0; else return 1.3;
}
```

At each node, the algorithm tries every feature and threshold and picks the split that best separates the target:

- **Classification:** minimize **Gini impurity** or **entropy** (how mixed the classes are).
- **Regression:** minimize variance (MSE) within each side.

```python
from sklearn.datasets import load_breast_cancer
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import train_test_split

data = load_breast_cancer()
X_tr, X_te, y_tr, y_te = train_test_split(data.data, data.target, stratify=data.target, random_state=0)

tree = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_tr, y_tr)
print(export_text(tree, feature_names=list(data.feature_names)))
print("test acc:", tree.score(X_te, y_te))
```

### Strengths and weaknesses

Strengths: interpretable, no feature scaling needed, handles non-linear relationships and interactions, works with mixed feature types.

Weakness: an unrestricted tree grows until every leaf is pure — memorizing the training data (high variance). Small data changes can produce a completely different tree. Control it with `max_depth`, `min_samples_leaf`, `max_leaf_nodes`.

## Ensembles: wisdom of crowds

Combining many imperfect models often beats any single one. Two main strategies:

### Bagging and Random Forests

**Bagging** trains many trees on random bootstrap samples (sampling rows with replacement) and averages their predictions. Averaging cancels out individual trees' errors, reducing variance.

A **Random Forest** adds another twist: each split only considers a random subset of features, so trees are less correlated and the average is even more robust.

```python
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_estimators=300, max_features="sqrt",
                            n_jobs=-1, random_state=0)
rf.fit(X_tr, y_tr)
print("RF test acc:", rf.score(X_te, y_te))      # typically higher than a single tree
```

Random forests are hard to break: few hyperparameters, little tuning, no scaling, resistant to overfitting as you add trees. A superb default for tabular data.

### Boosting and Gradient Boosting

**Boosting** builds trees **sequentially**: each new small tree focuses on correcting the errors of the ensemble so far. **Gradient boosting** fits each tree to the residuals (more precisely, the negative gradient of the loss) — gradient descent in "function space".

```
prediction = tree1(x) + lr * tree2(x) + lr * tree3(x) + ...
             (each tree fits what the previous ones got wrong)
```

```python
from sklearn.ensemble import HistGradientBoostingClassifier

gb = HistGradientBoostingClassifier(learning_rate=0.1, max_iter=300,
                                    early_stopping=True, random_state=0)
gb.fit(X_tr, y_tr)
print("GB test acc:", gb.score(X_te, y_te))
```

Gradient boosting libraries — **XGBoost**, **LightGBM**, **CatBoost** — dominate tabular-data competitions and industry use cases (fraud, credit risk, ranking, churn). Even in the LLM era, for structured/tabular data, gradient boosted trees are usually the first serious model to try.

```python
# pip/uv add xgboost  (shown for reference)
from xgboost import XGBClassifier
xgb = XGBClassifier(n_estimators=500, learning_rate=0.05, max_depth=4,
                    subsample=0.8, colsample_bytree=0.8, eval_metric="logloss")
xgb.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
```

Key boosting hyperparameters: `learning_rate` (smaller = more trees needed but better generalization), number of trees (use early stopping), `max_depth` (3-8 typical), subsampling of rows/columns.

### Bagging vs boosting

| | Bagging / Random Forest | Boosting |
|---|---|---|
| Trees built | independently, in parallel | sequentially |
| Each tree | deep, low bias / high variance | shallow, "weak learner" |
| Mainly reduces | variance | bias (and variance) |
| Overfitting risk | low | higher; needs early stopping |
| Tuning effort | low | moderate |

## Feature importance and explainability

```python
import pandas as pd
imp = pd.Series(rf.feature_importances_, index=data.feature_names).sort_values(ascending=False)
print(imp.head(5))
```

Impurity-based importances can be biased toward high-cardinality features. More reliable: **permutation importance** (shuffle a feature and measure the score drop) and **SHAP values**, which explain individual predictions — important when a stakeholder asks "why was this loan rejected?"

```python
from sklearn.inspection import permutation_importance
r = permutation_importance(rf, X_te, y_te, n_repeats=10, random_state=0)
print(pd.Series(r.importances_mean, index=data.feature_names).nlargest(5))
```

## Other classic algorithms worth knowing

- **k-Nearest Neighbours:** predicts from closest training points; needs scaling; slow at prediction time on large data.
- **Support Vector Machines:** find the maximum-margin boundary; kernels allow non-linear boundaries; strong on small/medium datasets.
- **Naive Bayes:** applies Bayes' theorem with an independence assumption; fast baseline for text classification.

## Which model when? (tabular data)

1. Baseline: Dummy, then logistic/linear regression.
2. Random forest: strong with almost no tuning.
3. Gradient boosting (LightGBM/XGBoost/CatBoost): usually the best accuracy with some tuning.
4. Neural networks: rarely better on small tabular data; shine on images, text and audio.

## Key takeaways

- Trees learn if/else splits; unrestricted trees overfit.
- Random forests average decorrelated trees (bagging) to cut variance.
- Gradient boosting adds shallow trees sequentially to fix errors; it's the tabular-data champion.
- Use permutation importance or SHAP for explanations.
""", r"""
**Task: Model bake-off.** Use the Titanic data you cleaned in Module 2 (or `fetch_openml("titanic", version=1)`).

1. Compare with 5-fold stratified CV (metric: ROC-AUC): Dummy, LogisticRegression, DecisionTree (depth 4), RandomForest, HistGradientBoosting.
2. Tune the gradient boosting model with RandomizedSearchCV over `learning_rate`, `max_depth`, `max_iter`, `min_samples_leaf`.
3. Print the depth-3 decision tree with `export_text` and explain its first two splits in plain English.
4. Compute permutation importances for the best model and plot the top 8.
5. Write a short table summarizing CV mean +/- std per model and your final choice.
""", [
    Q("How does a random forest reduce overfitting compared to a single deep tree?", ["By using shallower trees only", "By averaging many trees trained on bootstrap samples with random feature subsets", "By boosting misclassified samples", "By scaling features"], 1, "Bagging plus feature randomness yields decorrelated trees whose averaged prediction has much lower variance."),
    Q("What does each new tree in gradient boosting try to do?", ["Predict the target from scratch independently", "Correct the residual errors (negative gradient) of the current ensemble", "Cluster the data", "Remove irrelevant features"], 1, "Boosting is sequential: each tree fits what the ensemble so far gets wrong."),
    Q("Which statement about decision trees is TRUE?", ["They require feature scaling", "They cannot model non-linear relationships", "Unrestricted trees tend to overfit", "They only work for regression"], 2, "Without depth or leaf-size limits a tree can grow until it memorizes the training data."),
], [
    R("scikit-learn: Ensemble methods", "https://scikit-learn.org/stable/modules/ensemble.html", "docs"),
    R("StatQuest: Gradient Boost (series)", "https://www.youtube.com/watch?v=3CC4N4z3GJc", "video"),
    R("XGBoost: Introduction to Boosted Trees", "https://xgboost.readthedocs.io/en/stable/tutorials/model.html", "docs"),
    R("Kaggle Learn: Intermediate Machine Learning", "https://www.kaggle.com/learn/intermediate-machine-learning", "course"),
]))

lessons.append(L("m04-l6-pipelines-features", "Feature Engineering & scikit-learn Pipelines", 50, r"""
## Features matter more than algorithms

"Applied machine learning is basically feature engineering" — Andrew Ng. A mediocre algorithm with great features beats a great algorithm with poor features. Feature engineering means transforming raw data into inputs that expose the pattern to the model.

## Preprocessing building blocks

### Scaling numeric features

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
# StandardScaler: (x - mean) / std     -> linear models, kNN, SVM, neural nets
# MinMaxScaler:   to [0, 1]
# RobustScaler:   uses median/IQR      -> data with outliers
```

Tree-based models don't need scaling; distance- and gradient-based models do.

### Imputing missing values

```python
from sklearn.impute import SimpleImputer
num_imputer = SimpleImputer(strategy="median", add_indicator=True)  # adds a "was missing" flag
cat_imputer = SimpleImputer(strategy="most_frequent")
```

### Encoding categorical features

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
ohe = OneHotEncoder(handle_unknown="ignore")     # unseen categories at prediction time -> all zeros
ordinal = OrdinalEncoder(categories=[["low", "medium", "high"]])   # only when order is meaningful
```

High-cardinality categories (thousands of cities or product IDs) blow up one-hot encoding. Options: group rare values (`min_frequency=` in OneHotEncoder), **target encoding** (`TargetEncoder`, with built-in cross-fitting to avoid leakage), or learned embeddings (neural nets).

## Hand-crafted features

Domain knowledge creates the most valuable features:

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "signup": pd.to_datetime(["2025-01-03", "2025-06-15", "2026-02-01"]),
    "last_login": pd.to_datetime(["2026-09-30", "2026-03-01", "2026-10-01"]),
    "total_spend": [1200.0, 40.0, 310.0],
    "orders": [24, 2, 5],
    "income": [50000, 82000, 30000],
})
df["tenure_days"] = (df["last_login"] - df["signup"]).dt.days      # durations
df["days_since_login"] = (pd.Timestamp("2026-10-08") - df["last_login"]).dt.days
df["avg_order_value"] = df["total_spend"] / df["orders"].clip(lower=1)   # ratios
df["signup_month"] = df["signup"].dt.month                         # date parts
df["log_income"] = np.log1p(df["income"])                          # tame skew
df["month_sin"] = np.sin(2 * np.pi * df["signup_month"] / 12)      # cyclical encoding
```

Common patterns: ratios, differences, counts and aggregates per entity (orders per customer in the last 30 days), date parts, cyclical encodings (December is close to January), log transforms, interaction terms, and text length/keyword flags.

Every feature must be computable **at prediction time** with only information available then — otherwise it's leakage.

## The problem pipelines solve

Without pipelines, you might write:

```python
scaler = StandardScaler().fit(X)          # BUG: fit on ALL data, including test
X_scaled = scaler.transform(X)
X_tr, X_te = train_test_split(X_scaled)
```

The scaler has seen test-set statistics — leakage. And in production you must replicate every preprocessing step exactly. A **Pipeline** bundles preprocessing and model into one object that is fit only on training data, cross-validated as a unit, and saved/deployed as one artifact. Think of it as a chain of responsibility pattern in Java.

## ColumnTransformer + Pipeline: the professional template

```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.datasets import fetch_openml

titanic = fetch_openml("titanic", version=1, as_frame=True).frame
X = titanic[["pclass", "sex", "age", "sibsp", "parch", "fare", "embarked"]]
y = titanic["survived"].astype(int)

numeric = ["age", "sibsp", "parch", "fare"]
categorical = ["pclass", "sex", "embarked"]

preprocess = ColumnTransformer([
    ("num", Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ]), numeric),
    ("cat", Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]), categorical),
])

model = Pipeline([
    ("prep", preprocess),
    ("clf", LogisticRegression(max_iter=1000)),
])

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
print("CV AUC:", cross_val_score(model, X_tr, y_tr, cv=5, scoring="roc_auc").mean().round(3))
model.fit(X_tr, y_tr)
print("test accuracy:", round(model.score(X_te, y_te), 3))
```

During cross-validation, the imputers, scaler and encoder are re-fit **inside each fold** on that fold's training portion only. No leakage, by construction.

### Swapping models and tuning everything together

```python
from sklearn.model_selection import GridSearchCV
grid = GridSearchCV(model, {
    "clf": [LogisticRegression(max_iter=1000), HistGradientBoostingClassifier()],
    "prep__num__impute__strategy": ["mean", "median"],
}, cv=5, scoring="roc_auc")
grid.fit(X_tr, y_tr)
print(grid.best_params_)
```

### Custom transformers

Wrap your own feature logic so it lives inside the pipeline:

```python
from sklearn.preprocessing import FunctionTransformer

def add_family(df):
    df = df.copy()
    df["family_size"] = df["sibsp"] + df["parch"] + 1
    return df

family = FunctionTransformer(add_family)
full = Pipeline([("family", family), ("prep", preprocess), ("clf", LogisticRegression(max_iter=1000))])
```

(Remember to add `family_size` to the `numeric` list so the ColumnTransformer uses it.) For stateful logic, write a class with `fit` and `transform` inheriting `BaseEstimator, TransformerMixin`.

## Saving and serving the pipeline

```python
import joblib
joblib.dump(model, "titanic_model.joblib")
loaded = joblib.load("titanic_model.joblib")
new_passenger = pd.DataFrame([{"pclass": 1, "sex": "female", "age": 29, "sibsp": 0,
                               "parch": 0, "fare": 100.0, "embarked": "S"}])
print(loaded.predict_proba(new_passenger))
```

This single file can be loaded in a FastAPI service — the Python equivalent of a Spring Boot REST endpoint wrapping a service bean. Pin library versions: a model pickled with one scikit-learn version may not load in another. (Formats like ONNX allow serving outside Python — even from Java.)

## Key takeaways

- Feature engineering (ratios, aggregates, dates, logs, encodings) often beats model tuning.
- Scale for linear/distance models; impute with indicators; one-hot with `handle_unknown="ignore"`.
- ColumnTransformer + Pipeline prevents leakage and makes deployment a single artifact.
- Tune preprocessing and model together; save with joblib and pin versions.
""", r"""
**Task: Production-grade pipeline.** Use the Kaggle "Telco Customer Churn" CSV (or Titanic if offline).

1. Build a `ColumnTransformer` with separate numeric and categorical pipelines (imputation, scaling, one-hot).
2. Add a custom `FunctionTransformer` creating at least 3 engineered features (e.g. average monthly charge, tenure buckets, number of services).
3. Wrap it with `HistGradientBoostingClassifier` and run 5-fold CV ROC-AUC.
4. Tune 3 hyperparameters (including one preprocessing option) with `RandomizedSearchCV`.
5. Save the best pipeline with joblib, reload it in a separate script, and predict for 2 hand-written customers.
6. Write a short FastAPI endpoint `POST /predict` that loads the pipeline and returns churn probability (optional if you haven't used FastAPI yet).
""", [
    Q("Why should a StandardScaler be fit inside a Pipeline rather than on the full dataset before splitting?", ["It is faster", "Fitting on all data leaks test-set statistics into training", "Pipelines skip scaling", "Scalers cannot be used outside pipelines"], 1, "The scaler's mean and std would include validation/test rows; pipelines fit preprocessing on training folds only."),
    Q("What does `OneHotEncoder(handle_unknown='ignore')` do with a category unseen during training?", ["Raises an error", "Encodes it as all zeros", "Maps it to the most frequent category", "Drops the row"], 1, "Unknown categories become a zero vector, so production data with new values doesn't crash the model."),
    Q("Which model type generally does NOT need feature scaling?", ["k-Nearest Neighbours", "Logistic regression with regularization", "Random forest", "Support vector machine"], 2, "Tree splits are threshold comparisons on single features, so monotonic rescaling doesn't change them."),
], [
    R("scikit-learn: Pipelines and composite estimators", "https://scikit-learn.org/stable/modules/compose.html", "docs"),
    R("scikit-learn: Preprocessing data", "https://scikit-learn.org/stable/modules/preprocessing.html", "docs"),
    R("Kaggle Learn: Feature Engineering", "https://www.kaggle.com/learn/feature-engineering", "course"),
]))

lessons.append(L("m04-l7-unsupervised", "Unsupervised Learning: Clustering, PCA & Anomalies", 45, r"""
## Learning without labels

Most real-world data is unlabelled. Unsupervised learning finds structure on its own: groups (clustering), compact representations (dimensionality reduction), and outliers (anomaly detection). These techniques are also everyday tools for AI engineers working with embeddings — clustering support tickets, visualizing document embeddings, or detecting unusual inputs to an LLM system.

## k-Means clustering

k-Means partitions data into k groups:

1. Pick k random centroids.
2. Assign each point to its nearest centroid.
3. Move each centroid to the mean of its assigned points.
4. Repeat 2-3 until assignments stop changing.

It minimizes **inertia**: the sum of squared distances from points to their centroid.

```python
import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

X, _ = make_blobs(n_samples=600, centers=4, cluster_std=1.0, random_state=7)
X = StandardScaler().fit_transform(X)       # distance-based -> scale first!

km = KMeans(n_clusters=4, n_init=10, random_state=0).fit(X)
print(km.labels_[:10])           # cluster id per point
print(km.cluster_centers_)       # centroid coordinates
```

### Choosing k

There's no label to tell you the right k. Two heuristics:

```python
from sklearn.metrics import silhouette_score
for k in range(2, 8):
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(X)
    print(k, round(km.inertia_, 1), round(silhouette_score(X, km.labels_), 3))
```

- **Elbow method:** inertia always decreases with k; look for the "elbow" where improvements flatten.
- **Silhouette score** (-1 to 1): how much closer points are to their own cluster than to the next one. Pick k with a high score.

Ultimately, clusters must be **useful**: can the business name and act on each segment?

### Limitations

k-Means assumes roughly spherical, similar-sized clusters and needs k in advance. Alternatives:

- **DBSCAN / HDBSCAN:** density-based; finds arbitrary shapes, marks noise points, no k needed. HDBSCAN is popular for clustering text embeddings (topic modelling tools like BERTopic use it).
- **Agglomerative (hierarchical) clustering:** builds a tree of merges you can cut at any level.
- **Gaussian Mixture Models:** soft (probabilistic) cluster membership.

```python
from sklearn.cluster import DBSCAN
db = DBSCAN(eps=0.3, min_samples=10).fit(X)
print(set(db.labels_))           # -1 means noise/outlier
```

## Worked example: customer segmentation

```python
rng = np.random.default_rng(0)
customers = pd.DataFrame({
    "recency_days": np.concatenate([rng.integers(1, 30, 200), rng.integers(100, 365, 200)]),
    "frequency":    np.concatenate([rng.integers(10, 50, 200), rng.integers(1, 5, 200)]),
    "monetary":     np.concatenate([rng.normal(2000, 400, 200), rng.normal(150, 50, 200)]),
})
Xc = StandardScaler().fit_transform(customers)
customers["segment"] = KMeans(n_clusters=2, n_init=10, random_state=0).fit_predict(Xc)
print(customers.groupby("segment").mean().round(0))
```

Profiling clusters by their feature means turns them into named personas ("loyal big spenders" vs "lapsed occasional buyers") that marketing can target. This RFM (recency, frequency, monetary) analysis is a classic.

## PCA: dimensionality reduction

**Principal Component Analysis** finds new axes (principal components) — directions of maximum variance — and projects data onto the top few. It's the eigenvector idea from Module 3 in action.

Uses: visualization in 2-D/3-D, compression, speeding up models, removing correlated features, denoising.

```python
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

digits = load_digits()                   # 1797 images, 8x8 = 64 features
X_d = StandardScaler().fit_transform(digits.data)

pca = PCA(n_components=2)
X_2d = pca.fit_transform(X_d)
print(pca.explained_variance_ratio_)     # variance captured by each component

plt.scatter(X_2d[:, 0], X_2d[:, 1], c=digits.target, cmap="tab10", s=8)
plt.colorbar(label="digit"); plt.title("64-D digits projected to 2-D")
```

How many components to keep? Choose enough to explain e.g. 95% of variance:

```python
pca95 = PCA(n_components=0.95).fit(X_d)
print(pca95.n_components_, "components keep 95% of variance")   # ~40 of 64
```

### t-SNE and UMAP

PCA is linear. **t-SNE** and **UMAP** are non-linear methods that preserve local neighbourhoods, producing much clearer 2-D cluster pictures. They're the standard way to visualize embedding spaces (e.g. seeing that documents about similar topics cluster together). Use them for visualization only — distances between far-apart clusters aren't meaningful.

```python
from sklearn.manifold import TSNE
X_tsne = TSNE(n_components=2, perplexity=30, random_state=0).fit_transform(X_d)
```

## Anomaly detection

Find rare, unusual points: fraud, defective products, server incidents, abnormal API traffic.

```python
from sklearn.ensemble import IsolationForest

rng = np.random.default_rng(1)
normal = rng.normal(0, 1, (500, 2))
outliers = rng.uniform(-6, 6, (15, 2))
X_a = np.vstack([normal, outliers])

iso = IsolationForest(contamination=0.03, random_state=0).fit(X_a)
pred = iso.predict(X_a)              # 1 = normal, -1 = anomaly
print((pred == -1).sum(), "anomalies flagged")
```

**Isolation Forest** randomly splits the data; anomalies are isolated in fewer splits because they sit far from the crowd. Simpler alternatives: z-scores or IQR rules on single features.

## Unsupervised + supervised together

- Cluster IDs or PCA components can become features for a supervised model.
- Clustering helps you **label efficiently**: label a few examples per cluster.
- In AI engineering, you'll cluster LLM conversation logs to discover common user intents and failure modes.

## Key takeaways

- k-Means groups by distance to centroids; scale features, pick k with elbow/silhouette, and validate usefulness.
- DBSCAN/HDBSCAN handle arbitrary shapes and noise.
- PCA projects onto directions of maximum variance; t-SNE/UMAP for visualizing embeddings.
- Isolation Forest flags anomalies by how easily points are isolated.
""", r"""
**Task: Discover structure.**

1. Load the "Mall Customers" dataset from Kaggle (or generate RFM data as in the lesson). Scale features, run k-Means for k=2..10, plot inertia and silhouette, and choose k.
2. Profile each cluster with `groupby().mean()` and give each segment a business name and one marketing action.
3. Run PCA on the digits dataset: plot cumulative explained variance and the 2-D projection. Then train logistic regression on 10, 20 and all 64 components and compare accuracy and training time.
4. Compare the PCA and t-SNE 2-D plots of digits. Which separates digits better?
5. Use IsolationForest on credit-card-like synthetic data and inspect the 10 most anomalous points.
""", [
    Q("What does k-Means minimize?", ["The number of clusters", "The sum of squared distances from points to their assigned centroid", "Classification error", "The variance between clusters only"], 1, "k-Means minimizes inertia, the within-cluster sum of squared distances."),
    Q("What do PCA's principal components represent?", ["Randomly chosen features", "Orthogonal directions of maximum variance in the data", "The cluster centroids", "The original features ranked by importance"], 1, "PCA finds orthogonal axes ordered by how much variance in the data they capture."),
    Q("Which algorithm can find arbitrarily shaped clusters and label noise points without specifying k?", ["k-Means", "PCA", "DBSCAN", "Linear regression"], 2, "DBSCAN groups dense regions and marks low-density points as noise (-1), with no need to set the number of clusters."),
], [
    R("scikit-learn: Clustering", "https://scikit-learn.org/stable/modules/clustering.html", "docs"),
    R("StatQuest: PCA main ideas", "https://www.youtube.com/watch?v=HMOI_lkzW08", "video"),
    R("Distill: How to Use t-SNE Effectively", "https://distill.pub/2016/misread-tsne/", "article"),
]))

MODULE = M("m04-ml-basics", 4, "Machine Learning Fundamentals", "Intermediate", 3,
    "Learn the core ideas and tools of classical machine learning with scikit-learn: supervised and unsupervised learning, the models that power most tabular-data products, and how to evaluate them honestly. You will finish able to build, tune, explain and package a leak-free ML pipeline end to end.",
    [
        "Frame business problems as regression, classification, clustering or not-ML, and set baselines",
        "Train and interpret linear/logistic regression, decision trees, random forests and gradient boosting",
        "Choose the right evaluation metric and threshold for imbalanced and cost-sensitive problems",
        "Diagnose overfitting and tune models with cross-validation and hyperparameter search",
        "Build leak-free scikit-learn pipelines with feature engineering and save them for deployment",
    ],
    lessons,
    ("Customer Churn Predictor, End to End", r"""
## Goal
Build a complete, deployable churn model — the kind of project that maps directly to interview discussions about the full ML lifecycle.

## Dataset
Kaggle "Telco Customer Churn" (about 7,000 customers, ~20 features, binary `Churn` target, imbalanced ~26% positive).

## Spec
- EDA notebook (reuse Module 2 skills) with a data dictionary and leakage review.
- A `ColumnTransformer` + `Pipeline` with at least 4 engineered features.
- Compare at least 4 models with 5-fold stratified CV on ROC-AUC and PR-AUC: Dummy, logistic regression, random forest, gradient boosting (LightGBM or XGBoost optional).
- Tune the best model with RandomizedSearchCV or Optuna.
- Choose a decision threshold using a cost matrix (e.g. retention offer costs $20, lost customer costs $300) and report expected savings versus no model.
- Explain the model: permutation importance plus 3 individual predictions explained (SHAP optional).
- Persist the pipeline with joblib and serve it with a FastAPI `POST /predict` endpoint validated by a Pydantic model.

## Steps
1. Set up the project with uv; separate `src/` (features, train, serve) from notebooks.
2. Write unit tests for feature functions and an API test with FastAPI's `TestClient`.
3. Log every experiment's params and scores in a CSV (or MLflow as a stretch).
4. Write a README with results table, threshold rationale and how to run.

## Stretch goals
- Track experiments with **MLflow** and register the best model.
- Containerize the API with Docker (compare to packaging a Spring Boot JAR).
- Add a Streamlit dashboard where a user enters customer details and sees churn probability and top drivers.
- Simulate data drift: shift a feature's distribution and show how monitoring would detect it.
"""))
