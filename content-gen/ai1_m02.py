from ai1_common import L, Q, R, M

lessons = []

lessons.append(L("m02-l1-numpy-arrays", "NumPy Arrays & Vectorization", 50, r"""
## Why NumPy exists

A Python `list` stores pointers to boxed objects scattered in memory, and a Python `for` loop interprets each step. That is slow — often 50-100x slower than Java for number crunching. **NumPy** fixes this with the `ndarray`: a contiguous block of same-typed numbers (like a Java `double[]`) plus operations implemented in optimized C. Every ML library — pandas, scikit-learn, PyTorch — is built on, or mirrors, NumPy.

```python
import numpy as np          # the universal alias

a = np.array([1, 2, 3, 4])
print(a.dtype, a.shape, a.ndim)   # int64 (4,) 1
```

## Creating arrays

```python
np.zeros((2, 3))            # 2 rows x 3 cols of 0.0
np.ones(5)
np.full((2, 2), 7)
np.arange(0, 10, 2)         # [0 2 4 6 8]  like range()
np.linspace(0, 1, 5)        # 5 evenly spaced: [0. .25 .5 .75 1.]
np.eye(3)                   # identity matrix
rng = np.random.default_rng(seed=42)   # reproducible random numbers
rng.normal(0, 1, size=(3, 2))          # Gaussian samples
rng.integers(0, 10, size=5)
```

Always seed randomness in ML experiments so results are reproducible.

## Shape: the most important attribute

An array's **shape** is a tuple of dimension sizes. Most bugs in ML code are shape bugs, so get used to printing `.shape`.

```python
m = np.arange(12)           # shape (12,)
m2 = m.reshape(3, 4)        # 3 rows, 4 columns
m3 = m.reshape(2, 3, 2)     # 3-D: 2 blocks of 3x2
m4 = m.reshape(-1, 6)       # -1 = "figure it out" -> (2, 6)
print(m2.T.shape)           # transpose -> (4, 3)
flat = m2.ravel()           # back to 1-D
```

Think of a dataset as a 2-D array of shape `(n_samples, n_features)`: rows are examples (e.g. houses), columns are features (size, rooms, age). A batch of colour images is 4-D: `(batch, channels, height, width)`.

## Vectorization: no more loops

Arithmetic applies **element-wise** to whole arrays.

```python
prices = np.array([100.0, 250.0, 80.0])
qty = np.array([2, 1, 5])

revenue = prices * qty            # [200. 250. 400.]
total = revenue.sum()             # 850.0
discounted = prices * 0.9
taxed = np.round(prices * 1.18, 2)
print(np.sqrt(prices), np.log(prices), np.exp(np.array([0, 1])))
```

Compare with Java:

```java
double total = 0;
for (int i = 0; i < prices.length; i++) total += prices[i] * qty[i];
```

Let's measure the speed difference:

```python
import time
n = 1_000_000
xs = list(range(n))
arr = np.arange(n)

t = time.perf_counter(); s1 = sum(x * x for x in xs); t1 = time.perf_counter() - t
t = time.perf_counter(); s2 = (arr * arr).sum();      t2 = time.perf_counter() - t
print(f"python {t1:.3f}s  numpy {t2:.4f}s  speedup {t1/t2:.0f}x")
```

Typical speedup: 30-100x. **Rule: if you write a Python `for` loop over array elements, look for the vectorized way.**

## Aggregations and the axis argument

```python
scores = np.array([[80, 90, 70],    # student 0: three subjects
                   [60, 85, 95]])   # student 1

scores.mean()          # 80.0 overall
scores.mean(axis=0)    # per column (subject): [70. 87.5 82.5]
scores.mean(axis=1)    # per row (student):    [80. 80.]
scores.max(axis=1), scores.argmax(axis=1)   # best score and WHICH subject
scores.std(), scores.sum(axis=0), scores.cumsum()
```

Mental model: `axis=0` **collapses the rows** (you move down the rows, getting one result per column); `axis=1` collapses the columns. `argmax` returns indices — you will use it to turn model output probabilities into a predicted class.

## Boolean masks and filtering

```python
temps = np.array([22, 35, 18, 40, 29])
hot = temps > 30              # array([False, True, False, True, False])
print(temps[hot])             # [35 40]
print(temps[(temps > 20) & (temps < 36)])   # use & | ~ , not and/or
print(hot.sum())              # count of True values = 2
temps_clipped = np.where(temps > 35, 35, temps)   # vectorized if/else
```

## dtypes and memory

```python
a = np.array([1, 2, 3], dtype=np.float32)   # 4 bytes each (vs float64 = 8)
print(a.nbytes)        # 12
b = a.astype(np.int8)
```

Deep learning uses `float32` (and lower precisions like `bfloat16`) to save memory and speed up GPUs — the same idea later decides how big an LLM fits on your machine.

## Views vs copies (Java reference semantics, revisited)

```python
a = np.arange(5)
v = a[1:4]        # slicing gives a VIEW: shares memory
v[0] = 99
print(a)          # [ 0 99  2  3  4]  - original changed!
c = a[1:4].copy() # explicit copy when you need independence
```

This is like two Java references to the same array. Boolean-mask and integer-list indexing (`a[[0, 2]]`) return copies.

## Key takeaways

- `ndarray` = fast, typed, contiguous array with element-wise operations.
- Always know your `.shape`; datasets are `(n_samples, n_features)`.
- Replace loops with vectorized expressions, aggregations with `axis`, and filtering with boolean masks.
- Slices are views; use `.copy()` when needed.
""", r"""
**Task: Vectorize everything.**

1. Generate 10,000 simulated exam scores `rng.normal(65, 12, 10_000)` clipped to [0, 100] with `np.clip`.
2. Compute mean, median (`np.median`), std, and the percentage of students who scored above 80 — without any loops.
3. Create a `(1000, 5)` array of scores for 1000 students x 5 subjects. Find each student's average, the best subject per student (`argmax`), and the hardest subject overall.
4. Write a loop version and a vectorized version of "normalize each column to mean 0 and std 1" and time both.
5. Demonstrate the view-vs-copy behaviour with a slice and with a boolean mask.
""", [
    Q("For an array of shape (100, 3), what is the shape of `arr.mean(axis=0)`?", ["(100,)", "(3,)", "(1,)", "()"], 1, "axis=0 collapses the rows, leaving one value per column: shape (3,)."),
    Q("What does `a[a > 5]` return?", ["A boolean array", "The elements of a greater than 5", "The indices of elements greater than 5", "An error"], 1, "Indexing with a boolean mask selects the elements where the mask is True."),
    Q("Why is `(arr * arr).sum()` much faster than a Python loop?", ["It uses multiple Python threads", "The operation runs in compiled C over contiguous memory", "It skips half the elements", "Python caches the result"], 1, "NumPy vectorized operations execute in optimized C over a typed contiguous buffer, avoiding per-element interpreter overhead."),
], [
    R("NumPy: the absolute basics for beginners", "https://numpy.org/doc/stable/user/absolute_beginners.html", "docs"),
    R("Python Data Science Handbook (Jake VanderPlas) - NumPy chapter, free online", "https://jakevdp.github.io/PythonDataScienceHandbook/02.00-introduction-to-numpy.html", "book"),
    R("freeCodeCamp: NumPy full course", "https://www.youtube.com/watch?v=QUT1VHiLmmI", "video"),
]))

lessons.append(L("m02-l2-broadcasting", "Broadcasting, Fancy Indexing & Matrix Operations", 45, r"""
## Broadcasting: operating on different shapes

What happens with `array + scalar`? NumPy "stretches" the scalar to the array's shape. **Broadcasting** generalizes this to arrays of different shapes, without copying data.

```python
import numpy as np

X = np.array([[1.0, 200.0],
              [2.0, 400.0],
              [3.0, 600.0]])      # shape (3, 2): 3 samples, 2 features

col_mean = X.mean(axis=0)          # shape (2,)  -> [2. 400.]
X_centered = X - col_mean          # (3,2) - (2,) works! row-wise subtraction
X_scaled = X_centered / X.std(axis=0)
```

That last line is **standardization** — one of the most common preprocessing steps in ML — in two lines, no loops.

### The rules

Compare shapes from the **right**. Two dimensions are compatible if they are equal or one of them is 1. Missing dimensions are treated as 1.

```
X        : 3 x 2
col_mean :     2   -> treated as 1 x 2 -> stretched to 3 x 2   OK

A : 3 x 1
B :     4          -> 1 x 4  -> result 3 x 4                    OK (outer op)

C : 3 x 2
D :     3          -> mismatch 2 vs 3                           ERROR
```

```python
row_mean = X.mean(axis=1)              # shape (3,)
# X - row_mean                         # ValueError: shapes (3,2) (3,)
X - row_mean[:, np.newaxis]            # (3,2) - (3,1) -> works
X - X.mean(axis=1, keepdims=True)      # same, cleaner
```

`np.newaxis` (or `None`) inserts a size-1 dimension. `keepdims=True` keeps the collapsed axis as size 1 so the result broadcasts back. You will use both in PyTorch too.

A neat broadcasting trick — all pairwise distances between points:

```python
pts = np.random.default_rng(0).random((5, 2))       # 5 points in 2-D
diff = pts[:, None, :] - pts[None, :, :]            # (5,1,2) - (1,5,2) -> (5,5,2)
dist = np.sqrt((diff ** 2).sum(axis=-1))            # (5,5) distance matrix
```

This is the core of k-nearest-neighbours and of vector search in RAG systems.

## Fancy indexing

```python
M = np.arange(20).reshape(4, 5)
M[1, 3]            # single element (row 1, col 3) - not M[1][3]
M[:, 0]            # first column
M[1:3, ::2]        # rows 1-2, every other column
M[[0, 2, 3]]       # rows 0, 2, 3 (integer list -> copy)
M[[0, 1], [2, 4]]  # elements (0,2) and (1,4)

labels = np.array([2, 0, 1])
probs = np.array([[0.1, 0.2, 0.7],
                  [0.8, 0.1, 0.1],
                  [0.3, 0.4, 0.3]])
probs[np.arange(3), labels]   # prob assigned to the correct class: [0.7 0.8 0.4]
```

That last line is exactly how **cross-entropy loss** picks out the predicted probability of the true label for each sample.

## Matrix operations

Element-wise `*` is NOT matrix multiplication. Use `@` (or `np.matmul` / `np.dot`).

```python
A = np.array([[1, 2],
              [3, 4]])        # (2,2)
B = np.array([[5, 6],
              [7, 8]])

A * B          # element-wise: [[ 5 12] [21 32]]
A @ B          # matrix product: [[19 22] [43 50]]
v = np.array([1, 1])
A @ v          # matrix-vector: [3 7]
np.dot(v, v)   # dot product: 2
```

Matrix multiplication rule: `(m, n) @ (n, p) -> (m, p)` — inner dimensions must match.

### A linear model in one line

A linear regression prediction for every sample at once:

```python
rng = np.random.default_rng(1)
X = rng.random((100, 3))           # 100 houses, 3 features
w = np.array([50.0, 20.0, -5.0])   # one weight per feature
b = 10.0
y_pred = X @ w + b                 # (100,3) @ (3,) -> (100,) then broadcast + b
print(y_pred.shape)                # (100,)
```

A neural network layer is the same thing: `X @ W + b` with `W` of shape `(in_features, out_features)`.

## Other linear algebra helpers

```python
np.linalg.inv(A)          # inverse
np.linalg.det(A)          # determinant
np.linalg.norm(v)         # vector length (L2 norm)
np.linalg.solve(A, v)     # solve Ax = v (better than inv(A) @ v)
vals, vecs = np.linalg.eig(A)
np.concatenate([A, B], axis=0)   # stack vertically -> (4,2)
np.stack([v, v])                 # new axis -> (2,2)
```

## Cosine similarity — your first AI-engineer formula

Embeddings (covered in Module 6) are vectors; similar meanings point in similar directions. Cosine similarity measures that:

```python
def cosine_sim(a, b):
    return (a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))

q = np.array([0.9, 0.1, 0.0])
docs = np.array([[1.0, 0.0, 0.0],
                 [0.0, 1.0, 0.0],
                 [0.7, 0.7, 0.0]])
sims = docs @ q / (np.linalg.norm(docs, axis=1) * np.linalg.norm(q))   # broadcasting!
print(sims.argsort()[::-1])      # documents ranked by similarity
```

That is a miniature semantic search engine.

## Key takeaways

- Broadcasting aligns shapes from the right; size-1 dims stretch. Use `keepdims` / `None` to fix mismatches.
- Integer-array indexing picks arbitrary elements (used in loss functions).
- `@` is matrix multiplication; `*` is element-wise. `(m,n) @ (n,p) -> (m,p)`.
- `X @ w + b` is a linear model and a neural network layer.
""", r"""
**Task: Build a tiny vector search.**

1. Create 1,000 random "document embeddings" of dimension 64 (`rng.normal(size=(1000, 64))`) and normalize each row to unit length using broadcasting (`keepdims=True`).
2. Create a query vector, normalize it, and compute cosine similarity to all documents with a single `@`.
3. Return the indices of the top 5 documents using `np.argsort` (or `np.argpartition` for speed).
4. Standardize a random `(500, 4)` feature matrix so each column has mean 0 / std 1, and verify with `.mean(axis=0)` and `.std(axis=0)`.
5. Predict values for that matrix with weights `w = [1, -2, 0.5, 3]` and bias 4 using `@`.

Bonus: compute the full 1000x1000 similarity matrix and find the most similar pair of distinct documents.
""", [
    Q("Can arrays of shape (4, 3) and (3,) be added?", ["No, shapes must match exactly", "Yes, the (3,) array is broadcast across the 4 rows", "Only with np.add", "Only if converted to lists"], 1, "Comparing from the right, 3 matches 3 and the missing dimension is treated as 1, so it broadcasts."),
    Q("What is the shape of (32, 128) @ (128, 10)?", ["(32, 128)", "(128, 128)", "(32, 10)", "Error"], 2, "Matrix multiplication (m,n)@(n,p) gives (m,p): inner 128s match, result (32,10)."),
    Q("For matrices A and B of shape (2,2), what does `A * B` compute?", ["Matrix product", "Element-wise product", "Dot product of first rows", "Determinant"], 1, "In NumPy `*` is always element-wise; use `@` for matrix multiplication."),
], [
    R("NumPy docs: Broadcasting", "https://numpy.org/doc/stable/user/basics.broadcasting.html", "docs"),
    R("NumPy docs: Indexing on ndarrays", "https://numpy.org/doc/stable/user/basics.indexing.html", "docs"),
    R("From Python to NumPy (Nicolas Rougier, free book)", "https://www.labri.fr/perso/nrougier/from-python-to-numpy/", "book"),
]))

lessons.append(L("m02-l3-pandas-basics", "Pandas Fundamentals: Series, DataFrames & Selection", 50, r"""
## What pandas is

If NumPy is a fast `double[]`, **pandas** is an in-memory SQL table / Excel sheet with a Python API. A `DataFrame` has labelled columns (each a typed array) and a row index. As a MySQL developer, think of it as a `SELECT` result you can keep querying, joining, grouping and modifying in memory.

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "name":   ["Raj", "Asha", "Ravi", "Meera", "Kiran"],
    "dept":   ["Eng", "Eng", "Sales", "Eng", "Sales"],
    "salary": [85000, 120000, 60000, 95000, 72000],
    "years":  [2, 6, 3, 4, 1],
})
print(df)
```

A single column is a `Series` — a 1-D labelled array:

```python
s = df["salary"]          # Series
print(type(s), s.mean(), s.max())
```

## Loading real data

```python
df = pd.read_csv("employees.csv")            # also read_json, read_excel, read_parquet
df = pd.read_sql("SELECT * FROM employees", conn)   # straight from MySQL via SQLAlchemy
df.to_csv("out.csv", index=False)
df.to_parquet("out.parquet")                 # columnar, compressed - preferred for big data
```

A famous practice dataset is available directly from a URL:

```python
url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv"
titanic = pd.read_csv(url)
```

## First look at any dataset

Always run these five lines first:

```python
titanic.shape          # (891, 15) rows, columns
titanic.head()         # first 5 rows
titanic.info()         # columns, dtypes, non-null counts (spot missing data!)
titanic.describe()     # count, mean, std, min, quartiles, max for numeric columns
titanic["class"].value_counts()   # frequency of each category
```

## Selecting data

```python
df["name"]                    # one column -> Series
df[["name", "salary"]]        # several columns -> DataFrame (note double brackets)

df.loc[0]                     # row by index LABEL
df.loc[0:2, ["name", "dept"]] # label-based slicing (end INCLUSIVE!)
df.iloc[0]                    # row by integer POSITION
df.iloc[:3, 1:3]              # position-based (end exclusive, like Python)
```

`loc` = labels, `iloc` = integer positions. With the default 0..n-1 index they look similar, but after filtering or sorting the labels no longer match positions — so be deliberate.

## Filtering rows — the WHERE clause

```python
# SELECT * FROM df WHERE dept = 'Eng' AND salary > 90000
df[(df["dept"] == "Eng") & (df["salary"] > 90000)]

df[df["dept"].isin(["Eng", "HR"])]          # IN (...)
df[df["name"].str.startswith("R")]          # LIKE 'R%'
df.query("years >= 3 and dept == 'Eng'")    # SQL-like string syntax
```

Same rules as NumPy masks: use `&`, `|`, `~` and wrap each condition in parentheses.

## Adding and modifying columns

```python
df["salary_lakh"] = df["salary"] / 100000          # vectorized, like NumPy
df["senior"] = df["years"] >= 4
df["level"] = np.where(df["years"] >= 4, "Senior", "Junior")
df["name_upper"] = df["name"].str.upper()          # .str for string methods
df = df.rename(columns={"years": "experience"})
df = df.drop(columns=["name_upper"])
```

Avoid `df.apply(lambda row: ..., axis=1)` for simple math — it loops in Python. Prefer vectorized column expressions.

## Sorting

```python
# ORDER BY salary DESC
df.sort_values("salary", ascending=False)
df.sort_values(["dept", "salary"], ascending=[True, False])
df.nlargest(3, "salary")       # top 3
```

## SQL-to-pandas cheat sheet

| SQL | pandas |
|---|---|
| `SELECT a, b FROM t` | `t[["a", "b"]]` |
| `WHERE x > 5` | `t[t["x"] > 5]` |
| `ORDER BY x DESC LIMIT 10` | `t.sort_values("x", ascending=False).head(10)` |
| `SELECT DISTINCT x` | `t["x"].unique()` |
| `COUNT(*)` | `len(t)` |
| `GROUP BY` | `t.groupby(...)` (next lesson) |
| `JOIN` | `pd.merge(...)` (next lesson) |

## The index

Each DataFrame has an index (row labels). You can promote a column to the index for fast label lookups, like a primary key:

```python
by_name = df.set_index("name")
by_name.loc["Raj", "salary"]
by_name.reset_index()          # back to a normal column
```

## Pandas vs NumPy

```python
X = df[["salary", "experience"]].to_numpy()   # (5, 2) ndarray for ML libraries
```

Most ML workflows: load and clean with pandas, then hand NumPy arrays (or the DataFrame directly) to scikit-learn or PyTorch.

## Key takeaways

- DataFrame = labelled, typed table; Series = one column.
- Start every dataset with `shape`, `head`, `info`, `describe`, `value_counts`.
- `loc` for labels, `iloc` for positions; boolean masks for WHERE.
- Create columns with vectorized expressions, not row loops.
""", r"""
**Task: Titanic exploration (part 1).** Load the Titanic CSV from the URL in the lesson and answer with pandas code:

1. How many rows and columns? Which columns have missing values (`info()` / `isna().sum()`)?
2. What fraction of passengers survived overall?
3. List the 10 oldest passengers with their class and survival.
4. How many women in first class survived?
5. Add a column `family_size = sibsp + parch + 1` and a boolean `is_alone`.
6. Select only the columns `survived, pclass, sex, age, fare, family_size` and convert to a NumPy array; print its shape.

Write the SQL you would use for questions 3 and 4 next to the pandas code.
""", [
    Q("What is the difference between `df.loc` and `df.iloc`?", ["loc is faster", "loc selects by labels, iloc by integer positions", "iloc only works on columns", "They are identical"], 1, "`loc` uses index labels (end-inclusive slicing), `iloc` uses integer positions (end-exclusive)."),
    Q("Which correctly filters rows where dept is 'Eng' and salary > 90000?", ["df[df.dept == 'Eng' and df.salary > 90000]", "df[(df['dept'] == 'Eng') & (df['salary'] > 90000)]", "df.where(dept='Eng', salary>90000)", "df.filter('Eng', 90000)"], 1, "Element-wise boolean logic needs `&` with each condition parenthesized; Python's `and` does not work on Series."),
    Q("Which method gives a quick statistical summary of numeric columns?", ["df.info()", "df.head()", "df.describe()", "df.summary()"], 2, "`describe()` reports count, mean, std, min, quartiles and max per numeric column."),
], [
    R("pandas: 10 minutes to pandas", "https://pandas.pydata.org/docs/user_guide/10min.html", "docs"),
    R("pandas: Comparison with SQL", "https://pandas.pydata.org/docs/getting_started/comparison/comparison_with_sql.html", "docs"),
    R("Kaggle Learn: Pandas (free micro-course)", "https://www.kaggle.com/learn/pandas", "course"),
]))

lessons.append(L("m02-l4-pandas-wrangling", "Data Cleaning, GroupBy, Joins & Reshaping", 55, r"""
## Real data is messy

In ML, data preparation often takes most of the time. "Garbage in, garbage out" applies: a model is only as good as the data it learns from. This lesson covers the cleaning and aggregation tools you will use daily.

```python
import pandas as pd
import numpy as np

url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv"
df = pd.read_csv(url)
```

## Missing values

Pandas represents missing data as `NaN` (or `None` / `pd.NA`). Unlike SQL `NULL`, NaN silently propagates through math.

```python
df.isna().sum()                       # missing count per column
df.isna().mean().round(3)             # missing fraction

df.dropna(subset=["embarked"])        # drop rows missing 'embarked'
df = df.drop(columns=["deck"])        # drop a column that is mostly empty

df["age"] = df["age"].fillna(df["age"].median())      # impute with median
df["embarked"] = df["embarked"].fillna(df["embarked"].mode()[0])  # most frequent
```

Strategy matters: dropping rows loses data; imputing with median is robust to outliers; sometimes "missingness" itself is informative, so you add a flag column:

```python
df["age_was_missing"] = df["age"].isna()   # do this BEFORE filling
```

## Duplicates, types and text cleanup

```python
df = df.drop_duplicates()
df["pclass"] = df["pclass"].astype("category")       # memory-efficient categorical
df["fare"] = pd.to_numeric(df["fare"], errors="coerce")   # bad strings -> NaN
df["sex"] = df["sex"].str.strip().str.lower()
dates = pd.to_datetime(pd.Series(["2026-01-05", "2026-02-10"]))
print(dates.dt.month, dates.dt.day_name())
```

## Outliers

```python
q1, q3 = df["fare"].quantile([0.25, 0.75])
iqr = q3 - q1
mask = df["fare"].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
print(f"{(~mask).sum()} fare outliers")
df["fare_capped"] = df["fare"].clip(upper=df["fare"].quantile(0.99))
```

## GroupBy: split-apply-combine

```sql
SELECT pclass, sex, AVG(survived), COUNT(*) FROM titanic GROUP BY pclass, sex;
```

```python
df.groupby(["pclass", "sex"])["survived"].agg(["mean", "count"])

# Named aggregations - clean column names
summary = df.groupby("pclass").agg(
    passengers=("survived", "size"),
    survival_rate=("survived", "mean"),
    avg_fare=("fare", "mean"),
    oldest=("age", "max"),
).round(2)
print(summary)
```

GroupBy splits the table into groups, applies a function to each, and combines the results. `transform` returns a result aligned with the original rows — great for features:

```python
# each passenger's fare relative to their class average
df["fare_vs_class"] = df["fare"] / df.groupby("pclass")["fare"].transform("mean")

# fill missing age with the median age of the same class and sex
df["age"] = df.groupby(["pclass", "sex"])["age"].transform(lambda s: s.fillna(s.median()))
```

## Joins with merge

```python
employees = pd.DataFrame({"emp_id": [1, 2, 3], "name": ["Raj", "Asha", "Ravi"], "dept_id": [10, 20, 30]})
depts = pd.DataFrame({"dept_id": [10, 20], "dept": ["Eng", "Sales"]})

pd.merge(employees, depts, on="dept_id", how="inner")   # INNER JOIN
pd.merge(employees, depts, on="dept_id", how="left")    # LEFT JOIN (Ravi gets NaN dept)
pd.merge(a, b, left_on="user_id", right_on="id")        # different key names
pd.concat([df_2025, df_2026], ignore_index=True)        # UNION ALL
```

Watch for row explosion: if keys are not unique on one side, merge produces a row per match — just like SQL. Use `validate="many_to_one"` to make pandas check.

## Reshaping: pivot and melt

```python
# wide "spreadsheet" view: rows = class, cols = sex, values = survival rate
pivot = df.pivot_table(index="pclass", columns="sex", values="survived", aggfunc="mean")

# crosstab = counts of combinations
pd.crosstab(df["pclass"], df["survived"], normalize="index")

# melt: wide -> long (useful for plotting)
scores = pd.DataFrame({"student": ["A", "B"], "math": [90, 70], "physics": [80, 85]})
long = scores.melt(id_vars="student", var_name="subject", value_name="score")
```

## Binning and encoding categories

Machine learning models need numbers, so text categories must be encoded.

```python
df["age_group"] = pd.cut(df["age"], bins=[0, 12, 18, 40, 60, 100],
                         labels=["child", "teen", "adult", "middle", "senior"])
df["fare_quartile"] = pd.qcut(df["fare"], 4, labels=False)

encoded = pd.get_dummies(df, columns=["sex", "embarked"], drop_first=True)   # one-hot
df["sex_code"] = df["sex"].map({"male": 0, "female": 1})
```

One-hot encoding turns a column with k categories into k (or k-1) binary columns. You will revisit this in Module 4 with scikit-learn's `OneHotEncoder`.

## Method chaining

Pandas reads best as a pipeline — similar to Java streams:

```python
result = (
    df
    .dropna(subset=["embarked"])
    .assign(family_size=lambda d: d["sibsp"] + d["parch"] + 1)
    .query("fare > 0")
    .groupby("family_size")["survived"]
    .mean()
    .sort_index()
)
```

## Performance tips

- Vectorize; avoid `iterrows()` and row-wise `apply`.
- Use `category` dtype for repeated strings and Parquet for storage.
- For data larger than memory, look at **Polars** or DuckDB (SQL directly on DataFrames/Parquet) — both are popular in 2026.

## Key takeaways

- Audit missing values first; choose drop vs impute deliberately and consider a missing-flag.
- `groupby(...).agg(...)` = SQL GROUP BY; `transform` gives per-row group statistics.
- `merge` = JOIN, `concat` = UNION; validate key cardinality.
- Encode categoricals (`get_dummies`, `map`) before modelling.
""", r"""
**Task: Titanic cleaning (part 2).** Starting from the raw Titanic data, write a function `clean_titanic(df) -> pd.DataFrame` that:

1. Drops `deck` and duplicate rows.
2. Adds `age_was_missing`, then fills `age` with the median of each (pclass, sex) group.
3. Fills `embarked` with the mode.
4. Adds `family_size`, `is_alone`, `age_group` (via `pd.cut`) and `fare_vs_class` (via `transform`).
5. One-hot encodes `sex` and `embarked`.

Then produce: (a) survival rate by `age_group` and `pclass` as a pivot table, (b) a crosstab of `is_alone` vs `survived`. Write 3 bullet-point insights you notice. Confirm the cleaned frame has zero missing values in the columns you will model on.
""", [
    Q("What does `df.groupby('pclass')['fare'].transform('mean')` return?", ["One row per class", "A Series aligned to the original rows, each holding its class's mean fare", "The overall mean fare", "A pivot table"], 1, "`transform` broadcasts each group's aggregate back to every row of that group, keeping the original shape."),
    Q("Which pandas call is the equivalent of a SQL LEFT JOIN?", ["pd.concat([a, b])", "pd.merge(a, b, on='key', how='left')", "a.join_left(b)", "a.append(b)"], 1, "`merge` with `how='left'` keeps all rows from the left frame and fills unmatched right columns with NaN."),
    Q("Why add an `age_was_missing` flag before imputing age?", ["Pandas requires it", "Missingness itself may carry predictive information", "It speeds up fillna", "To delete those rows later"], 1, "Whether a value was recorded can correlate with the target; the flag preserves that signal after imputation."),
], [
    R("pandas user guide: Group by", "https://pandas.pydata.org/docs/user_guide/groupby.html", "docs"),
    R("pandas user guide: Merge, join, concatenate", "https://pandas.pydata.org/docs/user_guide/merging.html", "docs"),
    R("Kaggle Learn: Data Cleaning", "https://www.kaggle.com/learn/data-cleaning", "course"),
    R("Python for Data Analysis, 3rd ed. (Wes McKinney, free online)", "https://wesmckinney.com/book/", "book"),
]))

lessons.append(L("m02-l5-visualization", "Visualization with Matplotlib & Seaborn", 45, r"""
## Why visualize?

Summary statistics can lie. Four datasets can share the same mean, variance and correlation yet look completely different (Anscombe's quartet). Plots reveal skew, outliers, clusters and relationships, and they are how you will diagnose model training (loss curves, confusion matrices). The core library is **Matplotlib**; **Seaborn** sits on top with statistical plots and nicer defaults.

```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

sns.set_theme(style="whitegrid")
titanic = sns.load_dataset("titanic")   # seaborn ships sample datasets
```

## Matplotlib's object model

Use the **object-oriented API**: a `Figure` (the window/canvas) contains one or more `Axes` (individual plots).

```python
x = np.linspace(0, 10, 100)
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(x, np.sin(x), label="sin(x)")
ax.plot(x, np.cos(x), label="cos(x)", linestyle="--")
ax.set_title("Trig functions")
ax.set_xlabel("x"); ax.set_ylabel("value")
ax.legend()
fig.tight_layout()
fig.savefig("trig.png", dpi=150)
plt.show()            # in Jupyter, plots also render automatically
```

Multiple plots in a grid:

```python
fig, axes = plt.subplots(1, 3, figsize=(15, 4))    # axes is a NumPy array of Axes
axes[0].hist(titanic["age"].dropna(), bins=30)
axes[0].set_title("Age distribution")
axes[1].scatter(titanic["age"], titanic["fare"], alpha=0.4)
axes[1].set_title("Age vs fare")
axes[2].bar(["Survived", "Died"], titanic["survived"].value_counts().sort_index(ascending=False))
fig.tight_layout()
```

## Choosing the right chart

| Question | Chart |
|---|---|
| How is one numeric variable distributed? | histogram, KDE, box plot |
| How do categories compare? | bar chart / count plot |
| How do two numeric variables relate? | scatter plot (+ regression line) |
| How does something change over time / epochs? | line plot |
| How do many variables correlate? | heatmap of the correlation matrix |
| How does a distribution differ by group? | box / violin plot |

## Seaborn: statistical plots in one line

Seaborn works directly with DataFrames: pass `data=` and column names.

```python
fig, axes = plt.subplots(2, 2, figsize=(12, 9))

sns.histplot(data=titanic, x="age", hue="survived", kde=True, ax=axes[0, 0])
sns.countplot(data=titanic, x="class", hue="survived", ax=axes[0, 1])
sns.boxplot(data=titanic, x="class", y="fare", ax=axes[1, 0])
sns.barplot(data=titanic, x="sex", y="survived", hue="class", ax=axes[1, 1])  # mean + CI
fig.tight_layout()
```

`barplot` shows the mean of `y` per category with a confidence interval — instantly visualizing a GROUP BY.

### Correlation heatmap

```python
num = titanic.select_dtypes("number")
corr = num.corr()                     # pairwise Pearson correlation
plt.figure(figsize=(7, 5))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
plt.title("Feature correlations")
```

Correlations near +1/-1 mean strong linear relationships; near 0 means none (but there could still be a non-linear one — always look at scatter plots too).

### Pair plot

```python
iris = sns.load_dataset("iris")
sns.pairplot(iris, hue="species")     # scatter for every pair of features
```

The pair plot shows at a glance that the iris species are separable by petal size — a hint that a simple classifier will work well.

## Plots you will make as an ML engineer

### Training loss curves

```python
epochs = np.arange(1, 31)
train_loss = 1.0 / epochs + 0.05
val_loss = 1.0 / epochs + 0.05 + np.maximum(0, (epochs - 15) * 0.01)   # starts rising

fig, ax = plt.subplots()
ax.plot(epochs, train_loss, label="train")
ax.plot(epochs, val_loss, label="validation")
ax.axvline(15, color="gray", linestyle=":", label="overfitting starts")
ax.set_xlabel("epoch"); ax.set_ylabel("loss"); ax.legend()
```

When validation loss rises while training loss keeps falling, the model is **overfitting** — you will learn to read this in Modules 4 and 5.

### Images

```python
img = np.random.default_rng(0).random((28, 28))    # a fake 28x28 grayscale image
plt.imshow(img, cmap="gray"); plt.axis("off")
```

`imshow` displays any 2-D array — used for images, confusion matrices and attention maps.

## Making plots honest and readable

- Always label axes and units, and add a title that states the takeaway.
- Start bar-chart axes at zero.
- Use `alpha` for overlapping scatter points; use log scale (`ax.set_yscale("log")`) for heavy-tailed data like prices.
- Use colour-blind-friendly palettes (Seaborn's defaults, or `palette="colorblind"`).

## Interactive alternative

**Plotly** (`plotly.express`) creates interactive HTML charts with hover and zoom in one line: `px.scatter(df, x="age", y="fare", color="class")`. Great for dashboards and Streamlit apps.

## Key takeaways

- Use `fig, ax = plt.subplots()` and the Axes methods; save with `fig.savefig`.
- Seaborn plots DataFrames directly: `histplot`, `countplot`, `boxplot`, `barplot`, `heatmap`, `pairplot`.
- Pick the chart by the question; correlation heatmaps and loss curves are daily tools.
""", r"""
**Task: Visual story of the Titanic.** In a notebook, create a single 2x3 figure that tells the story of who survived:

1. Histogram of age split by survival.
2. Count plot of class by survival.
3. Bar plot of survival rate by sex and class.
4. Box plot of fare by class (log scale on y).
5. Correlation heatmap of numeric columns.
6. A line plot of survival rate by `family_size`.

Give each subplot a title stating its takeaway (e.g. "Women in 1st class survived most"). Save the figure as `titanic_story.png` at 150 dpi. Then write a fake loss-curve plot showing overfitting and annotate where you would stop training.
""", [
    Q("In `fig, ax = plt.subplots()`, what is `ax`?", ["The whole window", "An Axes object representing one plot area", "A list of colours", "The data"], 1, "A Figure is the canvas; an Axes is an individual plot with its own axes, title and data."),
    Q("Which chart best shows how two numeric variables relate?", ["Pie chart", "Histogram", "Scatter plot", "Count plot"], 2, "A scatter plot places each observation at (x, y), revealing correlation, clusters and outliers."),
    Q("Training loss keeps falling but validation loss starts rising. What does this indicate?", ["Underfitting", "Overfitting", "A plotting bug", "The learning rate is zero"], 1, "The model is memorizing the training set and generalizing worse to unseen data — classic overfitting."),
], [
    R("Matplotlib: Quick start guide", "https://matplotlib.org/stable/users/explain/quick_start.html", "docs"),
    R("Seaborn: An introduction to seaborn", "https://seaborn.pydata.org/tutorial/introduction.html", "docs"),
    R("Kaggle Learn: Data Visualization", "https://www.kaggle.com/learn/data-visualization", "course"),
]))

lessons.append(L("m02-l6-eda-workflow", "End-to-End Exploratory Data Analysis (EDA)", 45, r"""
## What EDA is for

Before training any model, you must understand the data: what each column means, its quality, its distribution, and how features relate to the **target** (the thing you want to predict). Exploratory Data Analysis is a repeatable checklist. Skipping it is the number-one cause of models that look great in a notebook and fail in production.

We will walk through a real regression dataset: California housing (median house value per district).

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.datasets import fetch_california_housing

housing = fetch_california_housing(as_frame=True).frame
target = "MedHouseVal"          # in units of $100,000
```

## Step 1: Structure and meaning

```python
print(housing.shape)
print(housing.dtypes)
housing.head()
```

Write a short **data dictionary**: for each column, what it means, its unit, and whether it would be available at prediction time. That last point prevents **data leakage** — e.g. using "final sale price" to predict "asking price".

## Step 2: Data quality

```python
housing.isna().sum()                  # missing values
housing.duplicated().sum()            # duplicate rows
housing.describe().T                  # ranges: spot impossible values
```

Look for suspicious values: negative ages, prices exactly at a cap, placeholder values like `-1` or `999`. In this dataset, `MedHouseVal` is capped at 5.0 — many districts sit exactly at the ceiling:

```python
print((housing[target] >= 5.0).mean())   # ~5% of rows are capped
```

A model cannot learn values above the cap, so you must decide whether to drop or keep those rows and document the choice.

## Step 3: Univariate analysis (one variable at a time)

```python
housing.hist(bins=50, figsize=(14, 10))
plt.tight_layout()

print(housing.skew().sort_values())      # positive = long right tail
```

Income and population are right-skewed. Skewed features often benefit from a log transform before linear models:

```python
housing["log_population"] = np.log1p(housing["Population"])    # log(1 + x), safe at 0
```

## Step 4: Target analysis

```python
sns.histplot(housing[target], bins=50, kde=True)
print(housing[target].describe())
```

For classification problems, check **class balance** with `value_counts(normalize=True)`. If 99% of transactions are not fraud, a model that always says "not fraud" gets 99% accuracy and is useless — you will learn better metrics in Module 4.

## Step 5: Bivariate analysis (features vs target)

```python
corr = housing.corr()[target].sort_values(ascending=False)
print(corr)        # MedInc has the strongest correlation (~0.69)

fig, axes = plt.subplots(1, 3, figsize=(16, 4))
sns.scatterplot(data=housing.sample(2000, random_state=0), x="MedInc", y=target, alpha=0.3, ax=axes[0])
sns.scatterplot(data=housing.sample(2000, random_state=0), x="HouseAge", y=target, alpha=0.3, ax=axes[1])
axes[2].scatter(housing["Longitude"], housing["Latitude"], c=housing[target], cmap="viridis", s=2)
axes[2].set_title("Price by location")
```

The location map shows coastal districts are expensive — a non-linear pattern that a simple correlation would miss, and a hint that tree-based models may do well.

## Step 6: Feature relationships and multicollinearity

```python
sns.heatmap(housing.corr(), cmap="coolwarm", center=0)
```

`AveRooms` and `AveBedrms` are strongly correlated. Highly correlated features make linear model coefficients unstable. Options: drop one or combine them into a ratio.

## Step 7: Feature ideas

EDA should end with hypotheses for new features:

```python
housing["bedroom_ratio"] = housing["AveBedrms"] / housing["AveRooms"]
housing["rooms_per_person"] = housing["AveRooms"] / housing["AveOccup"]
print(housing[["bedroom_ratio", "rooms_per_person", target]].corr()[target])
```

## Step 8: Split before you peek too much

In real projects, set aside a **test set** early and do EDA only on the training portion, so your decisions are not influenced by data you will use for final evaluation.

```python
from sklearn.model_selection import train_test_split
train_df, test_df = train_test_split(housing, test_size=0.2, random_state=42)
```

## Automating the boring parts

Write a reusable helper so every new dataset gets the same first pass:

```python
def quick_eda(df: pd.DataFrame, target: str) -> None:
    print("shape:", df.shape)
    print("\nmissing:\n", df.isna().sum()[lambda s: s > 0])
    print("\ndescribe:\n", df.describe().T[["mean", "std", "min", "max"]])
    num = df.select_dtypes("number")
    print("\ncorrelation with target:\n", num.corr()[target].sort_values(ascending=False))
```

Tools such as `ydata-profiling` generate full HTML reports automatically, but knowing how to do it by hand is what interviewers test.

## The EDA report

Finish with a short written summary: data size and quality issues, how you handled them, the most predictive features, surprising findings, and modelling recommendations. This habit — turning analysis into a clear recommendation — is what separates engineers from notebook tinkerers.

## Key takeaways

- EDA = structure, quality, univariate, target, bivariate, correlations, feature ideas.
- Watch for leakage, caps/placeholders, skew, class imbalance and multicollinearity.
- Split off a test set early; summarize findings as recommendations.
""", r"""
**Task: Full EDA report.** Pick the Titanic dataset (classification) or California housing (regression) — ideally the one you have not used yet.

1. Write a data dictionary table in Markdown (column, meaning, type, leakage risk).
2. Run the `quick_eda` helper and fix data-quality issues.
3. Produce at least 6 plots covering univariate, target and bivariate analysis.
4. Engineer 3 new features and show their correlation (or survival rate difference) with the target.
5. End the notebook with a 6-8 bullet "Findings & Modelling Recommendations" section.

Keep the notebook clean: restart and run all before you finish.
""", [
    Q("What is data leakage?", ["Losing rows during cleaning", "Using information during training that would not be available at prediction time", "Storing data unencrypted", "Too many missing values"], 1, "Leakage gives the model access to future or target-derived information, inflating offline scores and failing in production."),
    Q("A dataset has 99% negative and 1% positive labels. Why is accuracy misleading?", ["Accuracy can't be computed", "Always predicting negative already gives 99% accuracy", "Accuracy only works for regression", "Positive labels are ignored"], 1, "With severe imbalance, a trivial majority-class predictor scores high accuracy while catching none of the positives."),
    Q("Why is `np.log1p` often applied to right-skewed features like population?", ["To remove missing values", "To compress the long tail and make the distribution more symmetric", "To convert to categories", "To normalize to [0,1]"], 1, "The log transform reduces the influence of very large values, which helps many models, and log1p is safe for zeros."),
], [
    R("Kaggle: Comprehensive data exploration with Python (Pedro Marcelino)", "https://www.kaggle.com/code/pmarcelino/comprehensive-data-exploration-with-python", "article"),
    R("Hands-On Machine Learning (Aurelien Geron), ch.2 notebook", "https://github.com/ageron/handson-ml3/blob/main/02_end_to_end_machine_learning_project.ipynb", "book"),
    R("Google ML Crash Course: Working with data", "https://developers.google.com/machine-learning/crash-course", "course"),
]))

MODULE = M("m02-data-tools", 2, "NumPy, Pandas & Visualization", "Beginner", 2,
    "Learn the data stack every AI engineer uses daily: NumPy for fast numerical arrays, pandas for table manipulation, and Matplotlib/Seaborn for visual insight. You will finish able to take any raw CSV and turn it into clean, understood, model-ready data.",
    [
        "Replace loops with vectorized NumPy code using broadcasting, masks and matrix operations",
        "Load, filter, clean, group, join and reshape tabular data with pandas (mapping SQL knowledge directly)",
        "Choose and build the right Matplotlib/Seaborn chart for a question",
        "Run a structured EDA and turn findings into modelling recommendations",
    ],
    lessons,
    ("EDA Report on a Real Dataset", r"""
## Goal
Produce a portfolio-quality exploratory analysis on a real dataset of your choice and publish it (GitHub + rendered notebook).

## Suggested datasets
- Kaggle "Telco Customer Churn" (classification)
- Kaggle "House Prices - Advanced Regression Techniques" (regression)
- NYC Taxi trips sample in Parquet (large-data practice)

## Spec
- A `src/cleaning.py` module with a tested `clean(df)` function (pytest with a small hand-made DataFrame).
- A notebook `eda.ipynb` that imports `clean`, runs the 8-step EDA workflow, and contains at least 10 well-labelled plots.
- At least 5 engineered features with justification.
- A `REPORT` section at the end: data quality issues, key drivers of the target, leakage risks, and which model family you would try first and why.

## Steps
1. Create the project with `uv`, add pandas, numpy, seaborn, matplotlib, scikit-learn, jupyterlab, pytest.
2. Write the data dictionary before any code.
3. Implement and test the cleaning function.
4. Do the analysis; keep only plots that support a finding.
5. Restart-and-run-all, then commit.

## Stretch goals
- Re-implement the cleaning in **Polars** or **DuckDB** and compare runtime.
- Build an interactive **Streamlit** page with Plotly charts and filters.
- Save the cleaned dataset as Parquet and reuse it in the Module 4 project.
"""))
