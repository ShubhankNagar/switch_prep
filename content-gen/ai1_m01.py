from ai1_common import L, Q, R, M

lessons = []

lessons.append(L("m01-l1-syntax", "Python Syntax: A Java Developer's Translation Guide", 45, r"""
## Why Python for AI?

Almost every AI library you will use — PyTorch, scikit-learn, Hugging Face, LangChain, the OpenAI and Anthropic SDKs — is Python-first. The heavy maths runs in C/C++/CUDA underneath; Python is the friendly "glue" language on top. Your Java background is a big advantage: you already understand types, classes, collections, and clean code. You mainly need to *unlearn* ceremony.

## Hello, World — side by side

```java
// Java
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, Raj");
    }
}
```

```python
# Python: a file is a script. No class, no main required.
print("Hello, Raj")
```

When you need a "main", the convention is:

```python
def main():
    print("Hello, Raj")

if __name__ == "__main__":   # true only when the file is run directly
    main()
```

## Variables and dynamic typing

Python has no type declarations. A variable is just a **name bound to an object**; the object carries the type.

```python
age = 26            # int (arbitrary precision - no overflow like Java int!)
salary = 85_000.50  # float (= Java double)
name = "Raj"        # str (immutable, like Java String)
is_ready = True     # bool - capital T/F
nothing = None      # Python's null

print(type(age))    # <class 'int'>
age = "twenty-six"  # legal! the name now points to a str
```

Python is **dynamically typed but strongly typed**: `"5" + 5` raises `TypeError` instead of silently producing `"55"` like Java's string concatenation does.

## Indentation is syntax

Braces are replaced by a colon and indentation (4 spaces by convention). Semicolons are not needed.

```python
score = 82
if score >= 90:
    grade = "A"
elif score >= 75:          # elif, not else if
    grade = "B"
else:
    grade = "C"

# Ternary: Java's  cond ? a : b
label = "pass" if score >= 40 else "fail"
```

Logical operators are words: `and`, `or`, `not` (instead of `&&`, `||`, `!`).

## Loops

There is no C-style `for (int i = 0; ...)`. Python's `for` is always a "for-each".

```python
for i in range(5):            # 0,1,2,3,4  (like i < 5)
    print(i)

names = ["Asha", "Ravi", "Raj"]
for name in names:
    print(name)

for idx, name in enumerate(names):   # index + value, very common
    print(idx, name)

count = 3
while count > 0:
    count -= 1               # no ++ or -- in Python!
```

## Strings and f-strings

```python
lang = "Python"
years = 2
msg = f"I have used Java for {years} years and now learn {lang}."   # like String.format
print(msg.upper(), len(msg))
print("a,b,c".split(","))        # ['a', 'b', 'c']
print("-".join(["x", "y"]))      # 'x-y'  (join is called on the separator)
multi = '''Triple quotes
span lines'''
```

## Equality and truthiness

| Java | Python |
|---|---|
| `a.equals(b)` | `a == b` (value equality) |
| `a == b` (reference) | `a is b` (identity; use only for `None`) |
| `x == null` | `x is None` |

Python treats "empty" values as false: `0`, `0.0`, `""`, `[]`, `{}`, `None` are all **falsy**. So you can write:

```python
items = []
if not items:
    print("list is empty")   # idiomatic; no items.isEmpty()
```

## Integer vs float division

```python
print(7 / 2)    # 3.5  (true division ALWAYS returns float - differs from Java!)
print(7 // 2)   # 3    (floor division, like Java int division for positives)
print(7 % 2)    # 1
print(2 ** 10)  # 1024 (power operator)
```

## Running Python

Install Python 3.12+ from python.org (or via `uv`, covered later). Then:

```bash
python3 hello.py      # run a script
python3               # interactive REPL - great for quick experiments
```

The REPL is your new best friend: instead of writing a test class to check how something behaves, just type it in.

## Key takeaways

- No classes or types required to start; indentation defines blocks.
- `None`, `True`, `False`, `and/or/not`, `elif`, `//` vs `/` are the main surprises.
- Use `==` for value equality and `is` only for `None` checks.
- f-strings are the standard way to format text.
""", r"""
**Task: FizzBuzz plus.** Write `fizz.py` that:

1. Loops from 1 to 30 and prints `Fizz` for multiples of 3, `Buzz` for multiples of 5, `FizzBuzz` for both, else the number.
2. Then, given `marks = [45, 92, 78, 30, 88]`, prints each mark with its index and grade (A >= 90, B >= 75, C >= 40, else F) using `enumerate` and an f-string like `#2 -> 78 (B)`.
3. Prints the average using `/` and the integer average using `//`.

Bonus: put the logic in a `main()` function guarded by `if __name__ == "__main__":`. Write the same program in Java mentally and count how many fewer lines Python needed.
""", [
    Q("What does `7 / 2` evaluate to in Python 3?", ["3", "3.5", "4", "TypeError"], 1, "In Python 3 `/` is always true division and returns a float. Use `//` for floor division."),
    Q("Which is the idiomatic way to check that a variable is null in Python?", ["x == null", "x.equals(None)", "x is None", "isNull(x)"], 2, "`None` is a singleton, so identity comparison with `is` is the recommended check."),
    Q("What happens when you run `\"5\" + 5`?", ["Returns \"55\"", "Returns 10", "Raises TypeError", "Returns None"], 2, "Python is strongly typed: it will not implicitly convert between str and int, unlike Java's string concatenation."),
], [
    R("The Python Tutorial (official)", "https://docs.python.org/3/tutorial/index.html", "docs"),
    R("Python for Everybody (Dr. Chuck) - free course", "https://www.py4e.com/", "course"),
    R("Real Python: Python vs Java", "https://realpython.com/java-vs-python/", "article"),
]))

lessons.append(L("m01-l2-collections", "Lists, Dicts, Sets, Tuples & Comprehensions", 50, r"""
## The four built-in collections

Python ships with four collection types built into the language syntax — no imports and no generics.

| Python | Literal | Closest Java | Mutable? |
|---|---|---|---|
| `list` | `[1, 2, 3]` | `ArrayList` | yes |
| `tuple` | `(1, 2, 3)` | immutable record / `List.of` | no |
| `dict` | `{"a": 1}` | `HashMap` (but insertion-ordered like `LinkedHashMap`) | yes |
| `set` | `{1, 2, 3}` | `HashSet` | yes |

Collections can hold mixed types, though in practice you keep them homogeneous.

## Lists

```python
nums = [5, 3, 8]
nums.append(1)          # add to end   -> [5, 3, 8, 1]
nums.insert(0, 10)      # insert at index
nums.pop()              # remove & return last
nums.sort()             # in-place sort
sorted_copy = sorted(nums, reverse=True)   # new list
print(len(nums), 8 in nums)   # length, membership test
```

### Slicing — you will use this constantly in NumPy

`seq[start:stop:step]`, where `stop` is exclusive and negative indices count from the end.

```python
a = [0, 1, 2, 3, 4, 5]
a[1:4]    # [1, 2, 3]
a[:3]     # [0, 1, 2]   first three
a[-2:]    # [4, 5]      last two
a[::2]    # [0, 2, 4]   every second
a[::-1]   # reversed copy
a[-1]     # 5  (no more list.get(list.size()-1)!)
```

## Tuples and unpacking

Tuples are immutable sequences, often used to return multiple values.

```python
point = (3, 4)
x, y = point             # unpacking
a, b = 1, 2
a, b = b, a              # swap without a temp variable

def min_max(values):
    return min(values), max(values)   # returns a tuple

lo, hi = min_max([4, 9, 1])
first, *rest = [1, 2, 3, 4]   # first=1, rest=[2,3,4]
```

In Java you would create a `Pair` class or a `record`. In Python, tuples do the job.

## Dictionaries

```python
emp = {"name": "Raj", "role": "Java Dev", "years": 2}
emp["years"] = 3                 # update
emp["skill"] = "Spring Boot"     # insert
print(emp["name"])               # KeyError if missing
print(emp.get("salary", 0))      # default instead of exception (like getOrDefault)

for key, value in emp.items():   # iterate entries
    print(key, "->", value)

"role" in emp                    # key membership
```

Counting words — a classic interview task — becomes tiny:

```python
from collections import Counter, defaultdict

text = "the cat and the hat"
counts = Counter(text.split())
print(counts.most_common(1))     # [('the', 2)]

groups = defaultdict(list)       # auto-creates empty list for new keys
for word in text.split():
    groups[len(word)].append(word)
```

## Sets

```python
skills_raj = {"java", "sql", "angular"}
skills_job = {"python", "sql", "pytorch"}
print(skills_raj & skills_job)   # intersection {'sql'}
print(skills_job - skills_raj)   # what to learn: {'python', 'pytorch'}
print(skills_raj | skills_job)   # union
```

## Comprehensions: Python's answer to Streams

A Java stream pipeline:

```java
List<Integer> squares = nums.stream()
    .filter(n -> n % 2 == 0)
    .map(n -> n * n)
    .collect(Collectors.toList());
```

The Python equivalent is a **list comprehension**: `[expression for item in iterable if condition]`.

```python
nums = [1, 2, 3, 4, 5, 6]
squares = [n * n for n in nums if n % 2 == 0]       # [4, 16, 36]

# dict comprehension
word_len = {w: len(w) for w in ["ai", "java", "python"]}

# set comprehension
first_letters = {w[0] for w in ["apple", "avocado", "banana"]}

# nested: flatten a matrix
matrix = [[1, 2], [3, 4]]
flat = [x for row in matrix for x in row]          # [1, 2, 3, 4]
```

Read nested comprehensions left-to-right exactly like nested for-loops.

## Generators: lazy sequences

Replace the brackets with parentheses and you get a **generator expression** — values are produced one at a time, like a lazy Java `Stream`. This matters when processing huge datasets that do not fit in memory.

```python
total = sum(n * n for n in range(10_000_000))   # never builds the full list

def read_batches(rows, size):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]       # 'yield' makes this a generator function

for batch in read_batches(list(range(10)), 4):
    print(batch)     # [0..3], [4..7], [8, 9]
```

That `read_batches` pattern is exactly how ML data loaders feed mini-batches to a model.

## Useful built-ins

`zip` pairs sequences, `any`/`all` test conditions, `sum`/`min`/`max` aggregate:

```python
names = ["a", "b"]; scores = [90, 70]
for n, s in zip(names, scores):
    print(n, s)
print(any(s > 80 for s in scores), all(s > 80 for s in scores))
best = max(zip(scores, names))   # (90, 'a') - tuples compare element-wise
```

## Key takeaways

- list/dict/set/tuple cover 95% of needs; `collections` adds `Counter`, `defaultdict`, `deque`.
- Slicing `[start:stop:step]` is essential — NumPy and PyTorch extend it.
- Comprehensions replace most stream pipelines; generators give laziness.
""", r"""
**Task: Log analyzer.** Given

```python
logs = ["INFO login raj", "ERROR db timeout", "INFO logout raj",
        "WARN slow query", "ERROR db timeout", "INFO login asha"]
```

1. Use a comprehension to get only `ERROR` lines.
2. Use `Counter` to count log levels.
3. Build a dict `{user: number_of_events}` for INFO lines (user = last word).
4. Use a set to list unique users.
5. Write a generator `chunks(seq, n)` and print the logs in chunks of 4.

Bonus: rewrite step 1 and 3 as Java streams on paper and compare readability.
""", [
    Q("What does `[1, 2, 3, 4, 5][-2:]` return?", ["[1, 2]", "[4, 5]", "[3, 4]", "[5]"], 1, "A negative start counts from the end, so `-2:` means the last two elements."),
    Q("Which expression builds a list of squares of even numbers in `nums`?", ["[n*n if n%2==0 for n in nums]", "[n*n for n in nums if n%2==0]", "(n*n for n in nums where n%2==0)", "map(n*n, filter(nums))"], 1, "The syntax is `[expr for x in iterable if condition]`; the filter goes at the end."),
    Q("Why would you use a generator expression instead of a list comprehension?", ["It is always faster for small data", "It produces values lazily, saving memory for large sequences", "It allows indexing with []", "It sorts the data automatically"], 1, "Generators yield one item at a time without materializing the whole collection, like a lazy Java Stream."),
], [
    R("Python docs: Data Structures", "https://docs.python.org/3/tutorial/datastructures.html", "docs"),
    R("Real Python: List Comprehensions", "https://realpython.com/list-comprehension-python/", "article"),
    R("Corey Schafer: Python Tutorials playlist", "https://www.youtube.com/playlist?list=PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU", "video"),
]))

lessons.append(L("m01-l3-functions", "Functions, Lambdas, Closures & Decorators", 50, r"""
## Defining functions

```python
def greet(name, greeting="Hello"):       # default argument
    return f"{greeting}, {name}!"

greet("Raj")                       # positional
greet(greeting="Hi", name="Raj")   # keyword arguments - order no longer matters
```

There is no method overloading in Python. Default and keyword arguments cover what overloading does in Java. A function without `return` returns `None`.

> **Gotcha:** never use a mutable default like `def f(items=[])`. The list is created **once** when the function is defined and shared across calls. Use `items=None` and create the list inside.

## *args and **kwargs

```python
def total(*args):            # collects extra positional args into a tuple (like Java varargs)
    return sum(args)

def configure(**kwargs):     # collects extra keyword args into a dict
    for k, v in kwargs.items():
        print(k, "=", v)

total(1, 2, 3)                          # 6
configure(lr=0.001, epochs=10)

params = {"lr": 0.01, "epochs": 5}
configure(**params)                     # unpack a dict into keyword args
```

You will see `**kwargs` everywhere in ML libraries, e.g. `model.generate(**inputs, max_new_tokens=50)`.

## Functions are first-class objects

In Java you need a functional interface (`Function<T,R>`) to pass behaviour. In Python, a function is just an object:

```python
def shout(s):
    return s.upper()

def apply(fn, value):
    return fn(value)

apply(shout, "hi")            # 'HI'
apply(len, "hello")           # 5 - built-ins work too

square = lambda x: x * x      # single-expression anonymous function
people = [("Raj", 26), ("Asha", 31), ("Ravi", 22)]
people.sort(key=lambda p: p[1])          # sort by age, like Comparator.comparing
```

Keep lambdas tiny; if it needs more than one expression, write a `def`.

## Scope and closures

A nested function can "remember" variables from the enclosing function, even after it returned. That is a **closure**.

```python
def make_multiplier(factor):
    def multiply(x):
        return x * factor      # 'factor' captured from the outer scope
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5), triple(5))   # 10 15

def counter():
    count = 0
    def inc():
        nonlocal count         # needed to REASSIGN an outer variable
        count += 1
        return count
    return inc
```

## Decorators: Python's AOP

If you have used Spring's `@Transactional` or `@Cacheable`, you already know the idea: wrap a method with extra behaviour. In Python, a decorator is simply **a function that takes a function and returns a new function**.

```python
import time
import functools

def timed(fn):
    @functools.wraps(fn)                  # keeps fn's name/docstring
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)      # call the original
        elapsed = time.perf_counter() - start
        print(f"{fn.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timed                     # same as: slow_sum = timed(slow_sum)
def slow_sum(n):
    return sum(range(n))

slow_sum(10_000_000)       # prints: slow_sum took 0.2xs
```

The `@timed` line is pure syntactic sugar for `slow_sum = timed(slow_sum)`. No proxies, no annotation processors.

### Decorators with arguments

Add one more layer: a function that returns a decorator.

```python
def retry(times=3):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    print(f"attempt {attempt} failed: {e}")
            raise RuntimeError("all retries failed")
        return wrapper
    return decorator

@retry(times=2)
def call_llm_api():
    raise ConnectionError("rate limited")
```

Retrying flaky LLM API calls is a real AI-engineering need, and this is how libraries like `tenacity` work.

### Built-in decorators you will meet

```python
from functools import lru_cache

@lru_cache(maxsize=None)          # memoization in one line
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(fib(80))                    # instant
```

Others: `@staticmethod`, `@classmethod`, `@property` (next lesson), `@torch.no_grad()` (PyTorch), `@app.get("/")` (FastAPI routes — very similar to Spring's `@GetMapping`).

## Docstrings

Instead of Javadoc, Python uses a string as the first statement in a function:

```python
def area(r):
    '''Return the area of a circle with radius r.'''
    return 3.14159 * r * r

help(area)    # prints the docstring
```

## Key takeaways

- Keyword/default arguments replace overloading; avoid mutable defaults.
- `*args`/`**kwargs` collect and spread arguments.
- Functions are objects: pass them, return them, store them.
- Decorators = functions wrapping functions; `@x` is sugar for `f = x(f)`.
""", r"""
**Task: Build your own toolkit.**

1. Write `@timed` (from the lesson) and `@log_calls` which prints the function name and its arguments before calling it.
2. Stack both decorators on a function `def train(epochs, lr=0.01)` that just sleeps `epochs * 0.1` seconds. Observe the order in which they run.
3. Write `@retry(times=3)` and apply it to a function that randomly fails 70% of the time (`random.random() < 0.7`).
4. Write `make_counter()` using a closure and `nonlocal`.

Bonus: use `@lru_cache` on a recursive function that counts ways to climb `n` stairs taking 1 or 2 steps, and compare runtime with and without the cache for n=35.
""", [
    Q("What is `@timed` above `def f(): ...` equivalent to?", ["f = timed()", "f = timed(f)", "timed = f(timed)", "f.timed = True"], 1, "Decorator syntax is sugar for passing the function to the decorator and rebinding the name to the result."),
    Q("Why is `def add(item, items=[])` dangerous?", ["Lists cannot be default values", "The default list is created once and shared across calls", "It causes a syntax error", "It makes the function slower"], 1, "Default values are evaluated once at definition time, so mutations persist between calls. Use `None` as a default instead."),
    Q("Inside a function, `**kwargs` is a ...", ["tuple of positional arguments", "list of keyword names", "dict of extra keyword arguments", "set of default values"], 2, "`**kwargs` collects extra keyword arguments into a dictionary mapping names to values."),
], [
    R("Real Python: Primer on Python Decorators", "https://realpython.com/primer-on-python-decorators/", "article"),
    R("Python docs: Defining Functions", "https://docs.python.org/3/tutorial/controlflow.html#defining-functions", "docs"),
    R("Corey Schafer: Decorators explained", "https://www.youtube.com/watch?v=FsAPt_9Bf3U", "video"),
]))

lessons.append(L("m01-l4-oop", "OOP the Pythonic Way: Classes, Dataclasses & Exceptions", 50, r"""
## A class, Java vs Python

```java
public class Account {
    private final String owner;
    private double balance;
    public Account(String owner, double balance) { this.owner = owner; this.balance = balance; }
    public void deposit(double amt) { balance += amt; }
    @Override public String toString() { return owner + ": " + balance; }
}
```

```python
class Account:
    bank_name = "Raj Bank"            # class attribute (like static field)

    def __init__(self, owner, balance=0.0):   # constructor
        self.owner = owner            # instance attributes are created on assignment
        self._balance = balance       # leading underscore = "private by convention"

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._balance += amount

    def __repr__(self):               # like toString()
        return f"Account({self.owner!r}, {self._balance})"

acc = Account("Raj", 100)
acc.deposit(50)
print(acc)            # Account('Raj', 150.0)
```

Key differences:

- `self` is explicit — every instance method takes it as the first parameter (Java's `this` is implicit).
- No `new` keyword: `Account("Raj")`.
- No access modifiers. `_name` signals "internal"; `__name` triggers name mangling. Python's philosophy: "we are all consenting adults."
- No fields declared up front; attributes appear when assigned in `__init__`.

## Properties instead of getters/setters

Don't write `getBalance()`. Start with a plain attribute; if you later need logic, convert it to a `@property` without changing callers.

```python
class Account:
    def __init__(self, owner, balance=0.0):
        self.owner = owner
        self._balance = balance

    @property
    def balance(self):              # read like an attribute: acc.balance
        return self._balance

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise ValueError("negative balance")
        self._balance = value
```

## Static and class methods

```python
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius

    @classmethod
    def from_fahrenheit(cls, f):      # alternative constructor (factory)
        return cls((f - 32) * 5 / 9)

    @staticmethod
    def is_valid(c):                  # no self/cls - like Java static
        return c > -273.15

t = Temperature.from_fahrenheit(98.6)
```

## Inheritance and abstract classes

```python
from abc import ABC, abstractmethod

class Model(ABC):                     # like a Java abstract class
    @abstractmethod
    def predict(self, x): ...

class MeanModel(Model):
    def __init__(self):
        self.mean = 0
    def fit(self, ys):
        self.mean = sum(ys) / len(ys)
        return self                    # returning self enables chaining
    def predict(self, x):
        return self.mean

class ScaledMeanModel(MeanModel):
    def __init__(self, scale):
        super().__init__()             # call parent constructor
        self.scale = scale
    def predict(self, x):
        return super().predict(x) * self.scale
```

Python supports multiple inheritance, but in practice use it sparingly (mixins). There are no `interface`s; Python relies on **duck typing**: "if it has a `predict` method, I can call `predict`." scikit-learn is built on this — every model just has `fit` and `predict`.

## Dunder (magic) methods

Double-underscore methods let your objects work with Python syntax — like implementing `Comparable` or `Iterable` in Java, but for operators too.

```python
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __add__(self, other):          # v1 + v2
        return Vector(self.x + other.x, self.y + other.y)
    def __mul__(self, k):              # v * 3
        return Vector(self.x * k, self.y * k)
    def __eq__(self, other):           # == (like equals)
        return (self.x, self.y) == (other.x, other.y)
    def __len__(self):                 # len(v)
        return 2
    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

print(Vector(1, 2) + Vector(3, 4) * 2)   # Vector(7, 10)
```

This is exactly how NumPy arrays and PyTorch tensors support `a + b` and `a @ b`. Also notable: `__call__` makes an object callable — a PyTorch model is called as `model(x)` because `nn.Module` implements `__call__`.

## Dataclasses: Python's records/Lombok

```python
from dataclasses import dataclass, field

@dataclass
class TrainingConfig:
    model_name: str
    lr: float = 1e-3
    epochs: int = 10
    tags: list[str] = field(default_factory=list)

cfg = TrainingConfig("bert-base", epochs=3)
print(cfg)    # TrainingConfig(model_name='bert-base', lr=0.001, epochs=3, tags=[])
```

`@dataclass` generates `__init__`, `__repr__` and `__eq__` — like a Java `record` or Lombok's `@Data`. Add `frozen=True` for immutability.

## Exceptions

```python
try:
    value = int("abc")
except ValueError as e:              # catch
    print("bad input:", e)
except (KeyError, IndexError):
    print("lookup problem")
else:
    print("runs only if no exception")
finally:
    print("always runs")

class ModelNotTrainedError(Exception):   # custom exception
    pass
```

There are no checked exceptions — nothing forces you to declare `throws`.

## Context managers: try-with-resources

```python
with open("data.txt", "w") as f:     # file closed automatically, like try-with-resources
    f.write("hello")
```

You will write `with torch.no_grad():` constantly in PyTorch.

## Key takeaways

- `__init__` + explicit `self`; no access modifiers, just conventions.
- Use `@property` instead of getters/setters and `@dataclass` instead of boilerplate classes.
- Dunder methods make objects work with operators — the foundation of NumPy and PyTorch.
- Duck typing replaces interfaces; `with` replaces try-with-resources.
""", r"""
**Task: Mini model library.**

1. Create an abstract base class `Regressor` with abstract `fit(xs, ys)` and `predict(x)`.
2. Implement `MeanRegressor` (always predicts mean of ys) and `LinearRegressor` that fits `y = a*x + b` with the closed-form least-squares formulas: `a = sum((x-mx)*(y-my)) / sum((x-mx)**2)`, `b = my - a*mx`.
3. `fit` should return `self`; `predict` should raise a custom `NotFittedError` if called before `fit`.
4. Add `__repr__` and make the model callable via `__call__` (so `model(5)` works).
5. Store hyperparameters in a `@dataclass` called `Config`.

Test with `xs=[1,2,3,4]`, `ys=[3,5,7,9]` — the linear model should predict 11 for x=5.
""", [
    Q("What is the Python equivalent of Java's `toString()` for developer-facing output?", ["__str__ only", "__repr__", "__init__", "__call__"], 1, "`__repr__` returns an unambiguous developer representation; `__str__` is for end-user display and falls back to `__repr__`."),
    Q("What does the `@dataclass` decorator generate automatically?", ["Database mappings", "__init__, __repr__ and __eq__", "Getters and setters only", "Thread safety"], 1, "Dataclasses auto-generate the constructor, representation and equality methods from type-annotated fields."),
    Q("Why can you call a PyTorch model like a function, `model(x)`?", ["Python treats all objects as functions", "nn.Module implements __call__", "It is a lambda internally", "Because of the @model decorator"], 1, "Defining `__call__` makes instances callable; nn.Module's `__call__` runs hooks and then your `forward` method."),
], [
    R("Python docs: Classes", "https://docs.python.org/3/tutorial/classes.html", "docs"),
    R("Real Python: Data Classes in Python", "https://realpython.com/python-data-classes/", "article"),
    R("Fluent Python, 2nd ed. (Ramalho) - the book for deep Python", "https://www.oreilly.com/library/view/fluent-python-2nd/9781492056348/", "book"),
]))

lessons.append(L("m01-l5-tooling", "Environments, Packages, uv & Jupyter Notebooks", 40, r"""
## The problem: dependency isolation

In Java, Maven or Gradle downloads JARs into `~/.m2` and each project's `pom.xml` decides which versions go on the classpath. Python historically installed packages **globally**, so two projects needing different versions of `numpy` would clash. The fix is a **virtual environment**: a per-project folder containing its own Python interpreter and installed packages.

| Java world | Python world |
|---|---|
| `pom.xml` / `build.gradle` | `pyproject.toml` (or older `requirements.txt`) |
| Maven Central | PyPI (pypi.org) |
| `mvn install` | `pip install` / `uv add` |
| classpath per project | virtual environment (`.venv/`) |
| `mvnw` wrapper | `uv` manages Python versions too |

## The classic way: venv + pip

```bash
python3 -m venv .venv              # create environment in ./.venv
source .venv/bin/activate          # activate (Windows: .venv\Scripts\activate)
pip install numpy pandas           # install into the venv only
pip freeze > requirements.txt      # pin exact versions
pip install -r requirements.txt    # recreate elsewhere
deactivate
```

Always add `.venv/` to `.gitignore`, just like `target/`.

## The modern way: uv (recommended in 2026)

`uv` (by Astral) is a very fast Rust-based tool that replaces `pip`, `venv`, `pip-tools` and `pyenv`. It feels closer to Maven/Gradle: one tool, a lock file, reproducible builds.

```bash
# install uv once (see docs.astral.sh/uv for your OS)
uv init ai-playground          # creates project with pyproject.toml
cd ai-playground
uv add numpy pandas matplotlib # adds deps + writes uv.lock
uv add --dev pytest ruff       # dev-only dependencies (like <scope>test</scope>)
uv run python main.py          # runs inside the project's venv automatically
uv run pytest
uv python install 3.12         # manage Python versions
```

A generated `pyproject.toml` looks like:

```toml
[project]
name = "ai-playground"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "numpy>=2.0",
    "pandas>=2.2",
]
```

`uv.lock` pins every transitive version — commit it, like a Gradle lock file.

## Modules and packages

A **module** is any `.py` file; a **package** is a folder of modules (traditionally with an `__init__.py`).

```
ai_playground/
  pyproject.toml
  src/ai_playground/
      __init__.py
      data.py
      models/
          __init__.py
          linear.py
  tests/
      test_linear.py
```

```python
import math                          # whole module
from math import sqrt, pi            # specific names
import numpy as np                   # alias - universal convention
import pandas as pd
from ai_playground.models.linear import LinearRegressor
```

Avoid `from module import *` — like wildcard imports in Java, it hides where names come from.

## Jupyter notebooks: the data scientist's REPL

A notebook (`.ipynb`) mixes runnable code cells, output (tables, charts) and Markdown notes. It is the standard way to explore data and prototype models.

```bash
uv add --dev jupyterlab ipykernel
uv run jupyter lab               # opens in the browser
```

Alternatives: VS Code's built-in notebook support, or **Google Colab** (colab.research.google.com) — free, zero install, and offers free GPUs, which you will want for the deep learning module.

Useful notebook habits:

```python
# Cell 1
import pandas as pd
df = pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6]})
df            # the last expression in a cell is displayed automatically

# Cell 2 - "magic" commands start with % or !
%timeit sum(range(1000))      # micro-benchmark
!uv pip list                  # run a shell command
```

> **Gotcha:** cells can be run in any order, so hidden state builds up. Before trusting a result, use *Restart Kernel and Run All*. Move stable code into `.py` modules and import it — notebooks for exploration, modules for production.

## Code quality tools

| Purpose | Java | Python |
|---|---|---|
| Formatter | google-java-format | `ruff format` (or black) |
| Linter | Checkstyle / SpotBugs | `ruff check` |
| Type checker | javac | `mypy` / `pyright` |
| Tests | JUnit | `pytest` |

A pytest test is just a function starting with `test_` using plain `assert`:

```python
# tests/test_math.py
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
```

Run with `uv run pytest`. No annotations, no test classes needed.

## Key takeaways

- Always work inside a virtual environment; `uv` makes this automatic.
- `pyproject.toml` + `uv.lock` are your `pom.xml` + lock file.
- Use notebooks (Jupyter/Colab) for exploration; restart-and-run-all before trusting results.
- `ruff` + `pytest` + a type checker give you a Java-grade quality setup.
""", r"""
**Task: Set up your AI workspace.**

1. Install `uv` and create a project `ai-playground` with `uv init`.
2. Add `numpy`, `pandas`, `matplotlib` and dev deps `pytest`, `ruff`, `jupyterlab`.
3. Create package `src/ai_playground/stats.py` with functions `mean(xs)` and `variance(xs)`.
4. Write `tests/test_stats.py` with at least 3 tests; run `uv run pytest`.
5. Launch Jupyter Lab, import your module in a notebook, and plot `[x**2 for x in range(10)]` with matplotlib.
6. Run `uv run ruff check .` and fix any warnings.

Also open a Google Colab notebook and run `!nvidia-smi` after enabling a GPU runtime (Runtime > Change runtime type) — you will use this later.
""", [
    Q("What is the main purpose of a Python virtual environment?", ["To speed up Python code", "To isolate each project's interpreter and installed packages", "To compile Python to bytecode", "To run Python in the browser"], 1, "A venv gives each project its own set of packages so versions do not clash, like a per-project classpath."),
    Q("Which file plays the role of Maven's pom.xml in a modern Python project?", ["setup.cfg", "requirements.lock", "pyproject.toml", "__init__.py"], 2, "`pyproject.toml` declares project metadata and dependencies; uv adds `uv.lock` for exact pins."),
    Q("Why should you 'Restart Kernel and Run All' before trusting a notebook's results?", ["To free GPU memory", "Cells may have been run out of order, leaving hidden state", "Jupyter caches outputs incorrectly", "It updates installed packages"], 1, "Out-of-order execution can make results depend on deleted or modified cells; a clean top-to-bottom run proves reproducibility."),
], [
    R("uv documentation (Astral)", "https://docs.astral.sh/uv/", "docs"),
    R("Python Packaging User Guide", "https://packaging.python.org/en/latest/tutorials/installing-packages/", "docs"),
    R("Google Colab: Welcome notebook", "https://colab.research.google.com/", "docs"),
    R("pytest: Get Started", "https://docs.pytest.org/en/stable/getting-started.html", "docs"),
]))

lessons.append(L("m01-l6-typing-async", "Type Hints, Pydantic & Async Basics", 50, r"""
## Type hints: getting some Java safety back

Python 3 lets you annotate types. They are **not enforced at runtime** — they are documentation plus input for static checkers (`mypy`, `pyright`) and your IDE's autocomplete. Modern AI libraries (FastAPI, Pydantic, the OpenAI/Anthropic SDKs) depend heavily on them, so write them everywhere.

```python
def average(values: list[float]) -> float:
    return sum(values) / len(values)

name: str = "Raj"
scores: dict[str, int] = {"math": 90}
pair: tuple[int, str] = (1, "a")
maybe: str | None = None          # Optional[String] in Java terms
```

### Common typing tools

```python
from typing import Any, Callable, Iterator, Literal, TypedDict, Protocol

Role = Literal["user", "assistant", "system"]   # like a tiny enum

class Message(TypedDict):          # typed shape for a dict (great for JSON)
    role: Role
    content: str

def apply(fn: Callable[[int], int], x: int) -> int:   # Function<Integer,Integer>
    return fn(x)

def count_up(n: int) -> Iterator[int]:
    yield from range(n)

class Predictor(Protocol):         # structural interface: anything with predict()
    def predict(self, x: float) -> float: ...
```

`Protocol` is the closest thing to a Java `interface` — but satisfied by *shape* (duck typing), not by an `implements` clause.

Generics look like this (Python 3.12+ syntax):

```python
def first[T](items: list[T]) -> T:       # <T> T first(List<T> items)
    return items[0]
```

Run `uv run mypy src/` or enable Pylance strict mode in VS Code to catch type errors before runtime.

## Pydantic: runtime validation (think Bean Validation + Jackson)

Type hints don't validate data at runtime. **Pydantic** does: it parses and validates input, and serializes to/from JSON. It is the backbone of FastAPI and of "structured output" from LLMs.

```python
from pydantic import BaseModel, Field, ValidationError

class Employee(BaseModel):
    name: str
    years: int = Field(ge=0)          # like @Min(0)
    skills: list[str] = []

e = Employee(name="Raj", years="2", skills=["java"])   # "2" coerced to int
print(e.model_dump_json())   # {"name":"Raj","years":2,"skills":["java"]}

try:
    Employee(name="X", years=-1)
except ValidationError as err:
    print(err)               # clear error: years must be >= 0
```

You will later ask an LLM to return JSON matching an `Employee` schema and let Pydantic validate it.

## Async basics: why AI engineers need it

LLM API calls take seconds. If you call 100 prompts sequentially, you wait 100x. Java solves this with threads, `CompletableFuture`, or virtual threads. Python's main tool for I/O-bound concurrency is **asyncio**: a single thread runs an event loop that switches between tasks whenever one is waiting on the network.

```python
import asyncio
import time

async def fake_llm_call(prompt: str) -> str:
    await asyncio.sleep(1)            # simulates network wait; yields control
    return f"answer to {prompt!r}"

async def main() -> None:
    start = time.perf_counter()
    prompts = ["q1", "q2", "q3", "q4", "q5"]
    results = await asyncio.gather(*(fake_llm_call(p) for p in prompts))
    print(results)
    print(f"took {time.perf_counter() - start:.1f}s")   # ~1s, not 5s

asyncio.run(main())
```

Rules of thumb:

- `async def` defines a **coroutine function**; calling it returns a coroutine object — it does nothing until awaited.
- `await` can only be used inside `async def`.
- `asyncio.gather(...)` runs many coroutines concurrently — like `CompletableFuture.allOf`.
- Never call blocking code (e.g. `time.sleep`, `requests.get`) inside async functions; use async libraries (`httpx.AsyncClient`, `AsyncAnthropic`, `AsyncOpenAI`).

### Limiting concurrency (rate limits!)

```python
async def limited_calls(prompts: list[str], max_parallel: int = 3) -> list[str]:
    sem = asyncio.Semaphore(max_parallel)       # like java.util.concurrent.Semaphore

    async def one(p: str) -> str:
        async with sem:
            return await fake_llm_call(p)

    return await asyncio.gather(*(one(p) for p in prompts))
```

### What about threads and CPU-bound work?

Python (CPython) has historically had the **GIL** (Global Interpreter Lock), so threads don't run Python bytecode in parallel. Free-threaded builds exist since 3.13 but are not yet the default everywhere. Practical guidance:

| Work type | Tool |
|---|---|
| Many network/API calls | `asyncio` (or threads) |
| Heavy number crunching | NumPy/PyTorch (run in C, release the GIL) |
| CPU-bound pure Python | `multiprocessing` / `concurrent.futures.ProcessPoolExecutor` |

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=8) as pool:      # like ExecutorService
    lengths = list(pool.map(len, ["a", "bb", "ccc"]))
```

## Putting it together

A typical AI-engineer function in 2026 looks like this: typed, validated, async.

```python
from pydantic import BaseModel

class Summary(BaseModel):
    title: str
    bullet_points: list[str]

async def summarize(text: str) -> Summary:
    raw_json = await call_model(text)          # some async LLM client
    return Summary.model_validate_json(raw_json)
```

## Key takeaways

- Type hints are optional at runtime but essential for tooling; write them.
- Pydantic validates data at runtime and powers FastAPI and structured LLM output.
- `asyncio` gives cheap concurrency for I/O-bound work like API calls; use `gather` + `Semaphore`.
- For CPU-heavy work, rely on NumPy/PyTorch or processes, not threads.
""", r"""
**Task: Concurrent "LLM" batcher.**

1. Define a Pydantic model `Review(text: str, rating: int)` with `rating` between 1 and 5.
2. Write `async def fake_classify(review: Review) -> str` that sleeps `random.uniform(0.5, 1.5)` seconds and returns `"positive"` if rating >= 4 else `"negative"`.
3. Create 20 reviews and classify them sequentially (await one at a time) and then concurrently with `asyncio.gather` limited by a `Semaphore(5)`. Print both timings.
4. Add full type hints and run `mypy` on the file with no errors.
5. Try constructing `Review(text="bad", rating=9)` and print the validation error.
""", [
    Q("Are Python type hints enforced at runtime?", ["Yes, always", "No, they are used by static checkers and tools", "Only in Python 3.12+", "Only for function arguments"], 1, "Type hints are metadata. Tools like mypy check them statically; libraries like Pydantic can choose to use them for runtime validation."),
    Q("What does `asyncio.gather(a(), b(), c())` do?", ["Runs them one after another", "Runs the coroutines concurrently and returns all results", "Starts three OS processes", "Cancels them"], 1, "gather schedules the coroutines concurrently on the event loop and returns their results in order, like CompletableFuture.allOf."),
    Q("Which approach suits making 200 LLM API calls quickly?", ["A for-loop with time.sleep", "asyncio with an async HTTP client and a semaphore", "multiprocessing with 200 processes", "Increasing recursion limit"], 1, "API calls are I/O-bound; asyncio handles many concurrent waits cheaply, and a semaphore respects rate limits."),
], [
    R("mypy: Type hints cheat sheet", "https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html", "docs"),
    R("Pydantic documentation", "https://docs.pydantic.dev/latest/", "docs"),
    R("Real Python: Async IO in Python", "https://realpython.com/async-io-python/", "article"),
    R("Python docs: asyncio", "https://docs.python.org/3/library/asyncio.html", "docs"),
]))

MODULE = M("m01-python", 1, "Python for Java Developers", "Beginner", 2,
    "Translate your Java and Spring Boot experience into idiomatic Python, the language of the entire AI ecosystem. You will learn syntax, data structures, functions, OOP, tooling, typing and async by constantly comparing with what you already know.",
    [
        "Write idiomatic Python using comprehensions, unpacking, f-strings and built-in collections",
        "Use functions as first-class objects and write your own decorators and closures",
        "Model domain objects with classes, dataclasses, properties and dunder methods",
        "Set up reproducible projects with uv, pyproject.toml, pytest and Jupyter",
        "Write typed, validated, concurrent code with type hints, Pydantic and asyncio",
    ],
    lessons,
    ("Python Port of a Spring Boot Mini-Service", r"""
## Goal
Rebuild a small piece of familiar Java work in Python so the syntax sticks: a **CLI expense tracker** with typed models, persistence and async "currency conversion".

## Spec
- `Expense` as a Pydantic model: `id`, `title`, `amount (>0)`, `category`, `date`.
- `ExpenseRepository` class that loads/saves a JSON file (use `with open(...)`, `json`).
- Commands via `argparse`: `add`, `list`, `summary` (totals per category using `defaultdict` or `Counter`), `top N`.
- A `@timed` decorator on repository methods and a `@retry` decorator on a fake async `convert(amount, to_currency)` function that randomly fails.
- `summary --currency USD` converts all totals concurrently using `asyncio.gather` with a `Semaphore`.

## Steps
1. `uv init expense-tracker`, add `pydantic`, dev deps `pytest`, `ruff`, `mypy`.
2. Write the models and repository with full type hints.
3. Write the CLI in `main.py` with `if __name__ == "__main__":`.
4. Write at least 6 pytest tests (repository round-trip, summary math, validation errors).
5. Make `ruff check` and `mypy --strict` pass.

## Stretch goals
- Expose the same functionality as a REST API with **FastAPI** (compare to a Spring `@RestController`).
- Add a Jupyter notebook that loads the JSON into pandas and plots spending per category.
- Package it so `uv run expenses add ...` works via a `[project.scripts]` entry.
"""))
