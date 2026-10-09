from cs_common import build, B, I, A

notes = [
("Scope, Hoisting & the Temporal Dead Zone", r"""
### Scope types
- **Global scope** – declared outside any function/block.
- **Function scope** – `var` is scoped to the nearest function.
- **Block scope** – `let` and `const` are scoped to the nearest `{ }` (if, for, try…).
- **Lexical scope** – a function can access variables from where it was **defined**, not where it is called.

```js
function outer() {
  var a = 1;
  if (true) { var b = 2; let c = 3; }
  console.log(a, b); // 1 2
  console.log(c);    // ReferenceError: c is not defined
}
```

### var vs let vs const
| | var | let | const |
|---|---|---|---|
| Scope | Function | Block | Block |
| Hoisted | Yes, initialised to `undefined` | Yes, but uninitialised (TDZ) | Yes, TDZ |
| Re-declare in same scope | Allowed | Error | Error |
| Re-assign | Yes | Yes | No (but object contents can mutate) |
| Creates property on `window` (global) | Yes | No | No |

```js
const user = { name: 'Raj' };
user.name = 'Ravi';   // fine – binding is constant, object is not
user = {};            // TypeError
Object.freeze(user);  // shallow immutability
```

### Hoisting
During the **creation phase** of an execution context, the engine registers declarations before running code. It looks like declarations "move to the top".

```js
console.log(x);   // undefined (var hoisted + initialised)
var x = 5;

console.log(y);   // ReferenceError: Cannot access 'y' before initialization
let y = 5;

greet();          // "hi" – function declarations are fully hoisted
function greet() { console.log('hi'); }

sayBye();         // TypeError: sayBye is not a function (var hoisted as undefined)
var sayBye = function () { console.log('bye'); };
```

### Temporal Dead Zone (TDZ)
The period between entering a scope and the line where a `let`/`const`/`class` is declared. Accessing the variable there throws `ReferenceError`. TDZ exists to catch bugs where you use a variable before it is meaningful.

```js
let a = 'outer';
{
  console.log(a); // ReferenceError – inner `a` is in TDZ, it shadows outer
  let a = 'inner';
}
```

### Classic loop question
```js
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i));   // 3 3 3
for (let j = 0; j < 3; j++) setTimeout(() => console.log(j));   // 0 1 2
```
`var` creates one shared `i`; by the time callbacks run the loop has finished (i = 3). `let` creates a **new binding per iteration**, so each callback closes over its own `j`. Pre-ES6 fix: an IIFE `(function(k){ setTimeout(() => console.log(k)); })(i)`.

### Execution context & call stack
Each function call creates an execution context (variable environment, scope chain, `this`) pushed onto the **call stack**. Too-deep recursion → `RangeError: Maximum call stack size exceeded`.

### Strict mode
`'use strict'` (automatic in ES modules and classes): assigning to undeclared variables throws, `this` in plain functions is `undefined` instead of `window`, duplicate parameter names are errors. TypeScript output and Angular code are strict-mode modules.
"""),

("Closures", r"""
A **closure** is a function bundled together with references to its surrounding (lexical) variables. The inner function keeps access to those variables **even after the outer function has returned**.

```js
function makeCounter() {
  let count = 0;                 // private state
  return {
    inc: () => ++count,
    get: () => count
  };
}
const c = makeCounter();
c.inc(); c.inc();
console.log(c.get()); // 2
console.log(c.count); // undefined – truly private
```
The variable `count` lives on because the returned functions reference it; garbage collection can't free it.

### Practical uses
1. **Data privacy / module pattern** (before ES modules and `#private` fields).
2. **Function factories** – `const add5 = makeAdder(5)`.
3. **Memoisation**:
```js
function memoize(fn) {
  const cache = new Map();
  return (n) => cache.has(n) ? cache.get(n) : (cache.set(n, fn(n)), cache.get(n));
}
```
4. **Debounce / throttle** – the timer id is held in a closure:
```js
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
const onSearch = debounce(q => api.search(q), 300);
```
5. **Once**:
```js
function once(fn) { let done = false, result; return (...a) => done ? result : (done = true, result = fn(...a)); }
```
6. Event handlers and callbacks capturing loop variables, React hooks, Angular `effect` callbacks, currying.

### Currying
```js
const curry = fn => function c(...args) {
  return args.length >= fn.length ? fn(...args) : (...more) => c(...args, ...more);
};
const sum3 = curry((a, b, c) => a + b + c);
sum3(1)(2)(3); // 6
sum3(1, 2)(3); // 6
```
Infinite curry: `sum(1)(2)(3)()` → keep accumulating until called with no args.

### Pitfalls
- **Memory leaks** – closures holding large objects (DOM nodes, big arrays) prevent GC; e.g. an event listener never removed.
- **Stale closures** – a callback captures an old value (common with `var` loops or React state).

### Interview script
"A closure is when a function remembers the variables from the scope where it was created. Every function in JS forms a closure. I've used it for debounce on a search input and for keeping private state in a factory function."

Then be ready to **write debounce, throttle, memoize, or once** on the spot — these are top machine-coding warm-ups in Indian product-company frontend/full-stack rounds.

Throttle for completeness:
```js
function throttle(fn, limit) {
  let last = 0;
  return (...args) => {
    const now = Date.now();
    if (now - last >= limit) { last = now; fn(...args); }
  };
}
```
"""),

("The `this` Keyword, call/apply/bind & Arrow Functions", r"""
`this` is determined by **how a function is called**, not where it is defined (except arrow functions). Learn the rules in priority order:

1. **`new` binding** – `new Foo()` → `this` is the newly created object.
2. **Explicit binding** – `fn.call(obj, a, b)`, `fn.apply(obj, [a, b])`, `fn.bind(obj)` → `this` is `obj`.
3. **Implicit binding** – `obj.method()` → `this` is `obj` (the object left of the dot).
4. **Default binding** – plain `fn()` → `undefined` in strict mode, global object (`window`) in sloppy mode.

**Arrow functions** have no own `this`; they capture `this` from the enclosing lexical scope, and `call/apply/bind` can't change it.

```js
const user = {
  name: 'Raj',
  regular() { return this.name; },
  arrow: () => this?.name,           // `this` of module scope -> undefined
  delayed() { setTimeout(() => console.log(this.name), 0); } // arrow captures user
};
user.regular();  // 'Raj'
user.arrow();    // undefined
const f = user.regular;
f();             // undefined (strict) – lost implicit binding
```

### Losing `this` — the classic bug
```js
class Timer {
  seconds = 0;
  start() { setInterval(this.tick, 1000); }   // `this` inside tick is undefined
  tick() { this.seconds++; }
}
```
Fixes: `setInterval(() => this.tick(), 1000)`, `setInterval(this.tick.bind(this), 1000)`, or define `tick = () => { this.seconds++; }` as an arrow class field.

### call vs apply vs bind
```js
function intro(greet, punct) { return `${greet}, I am ${this.name}${punct}`; }
const p = { name: 'Asha' };
intro.call(p, 'Hi', '!');      // args individually, invokes now
intro.apply(p, ['Hi', '!']);   // args as array, invokes now
const bound = intro.bind(p, 'Hello'); // returns new function, partially applied
bound('.');                    // 'Hello, I am Asha.'
```

### Polyfill for bind (frequently asked)
```js
Function.prototype.myBind = function (ctx, ...preset) {
  const fn = this;
  return function (...later) { return fn.apply(ctx, [...preset, ...later]); };
};
```

### Arrow vs regular function differences
| Arrow | Regular |
|---|---|
| Lexical `this` | Dynamic `this` |
| No `arguments` object | Has `arguments` |
| Can't be used with `new` | Can be a constructor |
| No `prototype` property | Has `prototype` |
| Implicit return for expressions | Needs `return` |

Don't use arrow functions as **object methods** that need `this` or for prototype methods; do use them for callbacks.

### `this` in event handlers
`button.addEventListener('click', function () { this })` → `this` is the button. With an arrow function, `this` is the outer scope.

### `globalThis`
Standard way to reference the global object in any environment (window in browser, global in Node).
"""),

("Prototypes, Inheritance & Classes", r"""
JavaScript uses **prototypal inheritance**: objects inherit directly from other objects via an internal link `[[Prototype]]` (accessible via `Object.getPrototypeOf(obj)` or the legacy `__proto__`).

When you access `obj.prop`, the engine looks on `obj`, then its prototype, then the prototype's prototype… until `null`. This is the **prototype chain**.

```js
const animal = { eats: true, walk() { return 'walking'; } };
const dog = Object.create(animal);   // dog.[[Prototype]] = animal
dog.barks = true;
dog.walk();          // 'walking' (found on prototype)
dog.hasOwnProperty('eats'); // false
```

### Constructor functions and `prototype`
Every regular function has a `prototype` property. Objects created with `new F()` get `F.prototype` as their `[[Prototype]]`.
```js
function Person(name) { this.name = name; }
Person.prototype.greet = function () { return 'Hi ' + this.name; };
const p = new Person('Raj');
p.greet();                                    // 'Hi Raj'
Object.getPrototypeOf(p) === Person.prototype // true
Person.prototype.constructor === Person       // true
```
Methods on the prototype are **shared** by all instances (memory-efficient), unlike methods assigned in the constructor.

### What `new` does
1. Creates an empty object.
2. Sets its `[[Prototype]]` to `F.prototype`.
3. Calls `F` with `this` = the new object.
4. Returns the object (unless `F` returns another object).

```js
function myNew(F, ...args) {
  const obj = Object.create(F.prototype);
  const res = F.apply(obj, args);
  return res !== null && typeof res === 'object' ? res : obj;
}
```

### ES6 classes – syntactic sugar
```js
class Employee {
  #salary;                          // truly private field
  static count = 0;
  constructor(name, salary) { this.name = name; this.#salary = salary; Employee.count++; }
  get annual() { return this.#salary * 12; }
  describe() { return `${this.name} earns ${this.annual}`; }
}
class Manager extends Employee {
  constructor(name, salary, reports) { super(name, salary); this.reports = reports; }
  describe() { return super.describe() + ` and manages ${this.reports}`; }
}
```
Under the hood `Manager.prototype.__proto__ === Employee.prototype`. Differences from functions: classes are **not hoisted** usably (TDZ), always strict mode, must be called with `new`, methods are non-enumerable.

### Useful checks
- `obj instanceof C` – is `C.prototype` anywhere in obj's chain?
- `Object.hasOwn(obj, 'k')` – own property only.
- `for...in` iterates inherited enumerable props too; `Object.keys` only own.

### Prototype pollution & extending built-ins
Avoid modifying `Object.prototype` or `Array.prototype` in apps (except polyfills in interviews). Merging untrusted JSON into objects can lead to **prototype pollution** (`__proto__` keys) — a known security issue.

### Interview polyfill example
```js
Array.prototype.myMap = function (cb, thisArg) {
  const out = [];
  for (let i = 0; i < this.length; i++) if (i in this) out[i] = cb.call(thisArg, this[i], i, this);
  return out;
};
```
Be ready for `myFilter`, `myReduce` (handle missing initial value) and `Promise.all` polyfills.
"""),

("Event Loop, Call Stack, Microtasks & Macrotasks", r"""
JavaScript runs on a **single thread**: one call stack, one thing at a time. Async behaviour comes from the **runtime** (browser/Node) plus the **event loop**.

### Components
- **Call stack** – where function frames execute.
- **Web APIs / Node APIs** – timers, network, DOM events run outside the JS thread.
- **Macrotask (task) queue** – callbacks from `setTimeout`, `setInterval`, I/O, UI events, `MessageChannel`.
- **Microtask queue** – promise reactions (`.then/.catch/.finally`), `await` continuations, `queueMicrotask`, `MutationObserver`.

### The loop algorithm (browser)
1. Run the current script / one macrotask to completion (until the stack is empty).
2. **Drain the entire microtask queue** (microtasks added during this step also run).
3. Render if needed (requestAnimationFrame callbacks, style, layout, paint).
4. Take the next macrotask; repeat.

So **all microtasks run before the next macrotask**. An infinite chain of microtasks can starve rendering.

### Classic output question
```js
console.log('1');
setTimeout(() => console.log('2'), 0);
Promise.resolve().then(() => console.log('3'));
queueMicrotask(() => console.log('4'));
(async () => {
  console.log('5');
  await null;
  console.log('6');
})();
console.log('7');
```
Output: **1 5 7 3 4 6 2**
- Sync: 1, 5 (async function body runs synchronously until first `await`), 7.
- Microtasks in order queued: 3, 4, 6.
- Macrotask: 2.

### setTimeout(fn, 0)
Not "run immediately" — it means "run after at least 0 ms, as a macrotask after the current stack and all microtasks". Browsers clamp nested timers to ≥4 ms.

### Node.js specifics
Node's loop has phases: timers → pending callbacks → poll (I/O) → check (`setImmediate`) → close callbacks. `process.nextTick` callbacks run **before** promise microtasks. Order of `setTimeout(0)` vs `setImmediate` in the main module is non-deterministic, but inside an I/O callback `setImmediate` runs first.

```js
setTimeout(() => console.log('timeout'));
setImmediate(() => console.log('immediate'));
process.nextTick(() => console.log('nextTick'));
Promise.resolve().then(() => console.log('promise'));
// nextTick, promise, then timeout/immediate (order may vary)
```

### Why it matters
- Long synchronous work (big loops, JSON parsing of MBs) **blocks** the UI — split work, use Web Workers.
- Understanding microtasks explains why Angular's Zone.js / change detection or a promise resolves before a timeout.
- Explains "why does my `console.log` after an API call print `undefined`" – the callback hasn't run yet.

### Blocking demo
```js
setTimeout(() => console.log('timer'), 0);
const end = Date.now() + 2000;
while (Date.now() < end) {}   // blocks 2s
console.log('loop done');     // 'loop done' then 'timer'
```
"""),

("Promises & Async/Await", r"""
A **Promise** represents a value that will be available later. States: **pending → fulfilled** (resolved with a value) or **rejected** (with a reason). Once settled it never changes.

```js
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

fetchUser(1)
  .then(user => fetchOrders(user.id))   // return a promise to chain
  .then(orders => console.log(orders))
  .catch(err => console.error(err))     // catches any error above
  .finally(() => hideSpinner());
```
- `.then` always returns a **new promise**; returning a value resolves it, throwing rejects it.
- The executor function runs **synchronously**; callbacks run as microtasks.
- An unhandled rejection triggers `unhandledrejection` (browser) / crashes Node by default.

### Combinators
| Method | Resolves when | Rejects when |
|---|---|---|
| `Promise.all(ps)` | all fulfil → array of values in order | **first** rejection (fail-fast) |
| `Promise.allSettled(ps)` | all settle → `[{status, value/reason}]` | never |
| `Promise.race(ps)` | first to settle (either way) | first settles with rejection |
| `Promise.any(ps)` | first to **fulfil** | all reject → `AggregateError` |

Timeout pattern: `Promise.race([fetch(url), wait(5000).then(() => { throw new Error('timeout'); })])`. Better: `AbortController` with `AbortSignal.timeout(5000)`.

### async/await
Syntactic sugar over promises; makes async code read top-to-bottom.
```js
async function loadDashboard(id) {
  try {
    const user = await fetchUser(id);
    const [orders, wallet] = await Promise.all([fetchOrders(id), fetchWallet(id)]); // parallel
    return { user, orders, wallet };
  } catch (e) {
    console.error(e);
    throw e;
  }
}
```
- An `async` function **always returns a promise**.
- `await` pauses only that function; the rest of the program continues. Code after `await` runs as a microtask.
- **Sequential vs parallel trap:** `await a(); await b();` runs one after another. Start both first (`const pa = a(), pb = b(); await pa; await pb;`) or use `Promise.all`.
- `forEach` doesn't wait for async callbacks; use `for...of` with `await` (sequential) or `Promise.all(arr.map(async ...))` (parallel).
- Top-level `await` works in ES modules.

### Promise.all polyfill (frequently asked)
```js
function promiseAll(promises) {
  return new Promise((resolve, reject) => {
    const results = []; let done = 0;
    if (promises.length === 0) return resolve(results);
    promises.forEach((p, i) => {
      Promise.resolve(p).then(v => {
        results[i] = v;
        if (++done === promises.length) resolve(results);
      }, reject);
    });
  });
}
```

### Retry with exponential backoff
```js
async function retry(fn, times = 3, delay = 500) {
  try { return await fn(); }
  catch (e) { if (times <= 1) throw e; await wait(delay); return retry(fn, times - 1, delay * 2); }
}
```

### Callback hell → promises
Promises solved nesting (pyramid of doom) and inversion of control; async/await further improved readability and try/catch error handling.
"""),

("ES6+ Features Every Interviewer Expects", r"""
### Destructuring, spread & rest
```js
const { name, address: { city } = {}, role = 'dev' } = user;   // nested + default
const [first, , third, ...others] = [1, 2, 3, 4, 5];
const merged = { ...defaults, ...overrides };   // shallow copy/merge
const copy = [...arr];
function sum(...nums) { return nums.reduce((a, b) => a + b, 0); }  // rest params
[a, b] = [b, a];   // swap
```
Spread makes a **shallow** copy — nested objects are shared. Deep copy: `structuredClone(obj)` (handles Dates, Maps, cycles; not functions) or `JSON.parse(JSON.stringify(obj))` (loses Dates/undefined/functions).

### Template literals, default params, enhanced object literals
```js
const msg = `Hello ${user.name}, you have ${count} orders`;
function greet(name = 'Guest') {}
const key = 'id';
const obj = { name, [key + '1']: 5, greet() {} };
```

### Optional chaining & nullish coalescing
```js
const pin = user?.address?.pin ?? 'N/A';
user.getAge?.();
const port = config.port ?? 8080;   // only null/undefined fall back
const port2 = config.port || 8080;  // 0 or '' also fall back (bug-prone)
```
Logical assignment: `a ||= b`, `a &&= b`, `a ??= b`.

### Modules
```js
export const PI = 3.14; export default function area(r) {}
import area, { PI } from './math.js';
const mod = await import('./heavy.js');   // dynamic import -> code splitting
```
ES modules are static (tree-shakable), strict, and singleton per URL; CommonJS (`require`) is dynamic and synchronous.

### Collections
- `Map` – any key type, insertion-ordered, `size`; better than objects for frequent add/remove.
- `Set` – unique values: `[...new Set(arr)]` to dedupe.
- `WeakMap`/`WeakSet` – keys are objects held weakly (no memory leak), not iterable. Used for private data/caches keyed by DOM nodes.

### Iterators & generators
```js
function* idGen() { let i = 1; while (true) yield i++; }
const g = idGen(); g.next().value; // 1
```
Anything with `[Symbol.iterator]` works with `for...of`, spread and destructuring. `for...in` iterates keys (including inherited), `for...of` iterates values.

### Symbols, BigInt, other additions
- `Symbol('id')` – unique property keys.
- `BigInt` – `123n` for integers beyond 2^53 − 1 (IDs from Java `long`!).
- Array methods: `includes`, `flat`, `flatMap`, `at(-1)`, `findLast`, non-mutating `toSorted`, `toReversed`, `with` (ES2023), `Object.groupBy` (ES2024).
- `Object.entries/fromEntries`, `Object.freeze`, `String.padStart`, `replaceAll`.
- `Promise.allSettled`, `Promise.any`, `Promise.withResolvers` (ES2024).
- Private class fields `#x`, static blocks, `structuredClone`.

### Equality & type coercion quick hits
- `===` strict (no coercion), `==` coerces (`'5' == 5` true, `null == undefined` true, `NaN !== NaN`).
- Falsy values: `false, 0, -0, 0n, '', null, undefined, NaN`. Everything else truthy (including `[]`, `{}`, `'0'`).
- `typeof null === 'object'` (historic bug), `typeof []==='object'` → use `Array.isArray`.
- `0.1 + 0.2 !== 0.3` (IEEE-754 floating point) – use integers (paise) for money.

### Shallow vs deep equality
Objects compare by reference: `{} === {}` is false.
"""),

("TypeScript: Types, Generics & Utility Types", r"""
TypeScript is a **statically typed superset of JavaScript** that compiles to JS. Types are erased at runtime — they exist only to catch errors at compile time and improve tooling.

### Basic & special types
```ts
let id: number = 1; let name: string = 'Raj'; let ok: boolean = true;
let ids: number[] = [1, 2]; let pair: [string, number] = ['a', 1];  // tuple
let anything: any;      // opt out of checking (avoid)
let safe: unknown;      // must narrow before use (prefer over any)
function fail(): never { throw new Error(); }  // never returns
function log(): void {}
```

### interface vs type
```ts
interface User { id: number; name: string; email?: string; readonly createdAt: Date; }
interface Admin extends User { permissions: string[]; }
type Status = 'ACTIVE' | 'BLOCKED';            // union of literals
type Point = { x: number } & { y: number };     // intersection
```
- `interface` – object shapes, can be **extended and declaration-merged**; good for public APIs/classes (`implements`).
- `type` – can alias anything: unions, tuples, primitives, mapped/conditional types.
In practice: interfaces for object models, types for unions/compositions.

### Narrowing & type guards
```ts
function format(v: string | number) {
  if (typeof v === 'string') return v.toUpperCase();
  return v.toFixed(2);
}
type Shape = { kind: 'circle'; r: number } | { kind: 'square'; side: number };
function area(s: Shape) {
  switch (s.kind) {               // discriminated union
    case 'circle': return Math.PI * s.r ** 2;
    case 'square': return s.side ** 2;
    default: const _exhaustive: never = s; return _exhaustive;
  }
}
function isUser(x: unknown): x is User { return typeof x === 'object' && x !== null && 'id' in x; }
```
Other guards: `instanceof`, `in`, truthiness, equality.

### Generics
Reusable, type-safe code (like Java generics, but structural and erased).
```ts
function first<T>(arr: T[]): T | undefined { return arr[0]; }
interface ApiResponse<T> { data: T; status: number; }
function getProp<T, K extends keyof T>(obj: T, key: K): T[K] { return obj[key]; }
class Repo<T extends { id: number }> { private items: T[] = []; findById(id: number) { return this.items.find(i => i.id === id); } }
```

### Utility types (very frequently asked)
| Utility | Meaning |
|---|---|
| `Partial<T>` | all props optional (PATCH payloads) |
| `Required<T>` | all props required |
| `Readonly<T>` | all props readonly |
| `Pick<T, 'a'\|'b'>` | only selected props |
| `Omit<T, 'password'>` | remove props (DTOs) |
| `Record<K, V>` | object with keys K and values V |
| `Exclude<U, X>` / `Extract<U, X>` | filter union members |
| `NonNullable<T>` | remove null/undefined |
| `ReturnType<F>` / `Parameters<F>` | function types |
| `Awaited<T>` | unwrap Promise type |

```ts
type UserUpdate = Partial<Omit<User, 'id' | 'createdAt'>>;
const byRole: Record<Status, User[]> = { ACTIVE: [], BLOCKED: [] };
```

### Advanced: keyof, typeof, mapped & conditional types
```ts
type Keys = keyof User;                         // 'id' | 'name' | ...
const config = { apiUrl: '', retries: 3 }; type Config = typeof config;
type MyPartial<T> = { [K in keyof T]?: T[K] };  // mapped type
type IsString<T> = T extends string ? true : false;  // conditional
type ElementType<T> = T extends (infer U)[] ? U : T; // infer
```

### Other must-knows
- **Enums** (numeric/string) vs union of string literals (`'A' | 'B'` – lighter, no runtime code); `as const` objects.
- **Type assertion** `x as User` (no runtime check) vs non-null assertion `x!`.
- `strict` mode flags: `strictNullChecks`, `noImplicitAny`.
- Access modifiers `public/private/protected` (compile-time only) vs JS `#private` (runtime).
- **Structural typing**: compatibility is by shape, not by name (unlike Java's nominal typing).
- `satisfies` operator (TS 4.9): validate a value against a type while keeping its narrow inferred type.
- Decorators (used by Angular `@Component`) – TS 5 supports standard decorators.
"""),
]

qa = [
("What is a closure? Give a practical example.", r"""
A closure is a function that **remembers variables from its lexical scope** even after the outer function has finished executing.

```js
function createBankAccount(initial) {
  let balance = initial;                // private
  return {
    deposit: amt => (balance += amt),
    getBalance: () => balance
  };
}
const acc = createBankAccount(100);
acc.deposit(50);
acc.getBalance(); // 150
acc.balance;      // undefined
```
Practical uses: data privacy, function factories, memoisation, **debounce/throttle** (the timer id lives in a closure), event handlers, currying. Downside: closures can keep large objects alive and cause memory leaks if references (e.g. listeners) aren't cleaned up.
""", B, ["closures"], True),

("Predict the output and explain how to fix it.\n\n```js\nfor (var i = 0; i < 3; i++) {\n  setTimeout(() => console.log(i), 100);\n}\n```", r"""
Output: **`3 3 3`**.

`var` is function-scoped, so there is **one** `i` shared by all three callbacks. The callbacks run after the loop finishes (they're macrotasks), when `i` is already 3.

Fixes:
```js
// 1. let creates a new binding per iteration
for (let i = 0; i < 3; i++) setTimeout(() => console.log(i), 100);   // 0 1 2

// 2. IIFE captures the current value (pre-ES6)
for (var i = 0; i < 3; i++) ((j) => setTimeout(() => console.log(j), 100))(i);

// 3. setTimeout's extra args
for (var i = 0; i < 3; i++) setTimeout(console.log, 100, i);
```
""", B, ["closures", "output", "scope"], True),

("Explain hoisting with var, let, const and functions.", r"""
Hoisting is JavaScript registering declarations during the creation phase of a scope, before executing code.

- `var` – hoisted and initialised to `undefined`. Using it early gives `undefined`.
- `let`/`const`/`class` – hoisted but **not initialised**; accessing before the declaration line throws `ReferenceError` (Temporal Dead Zone).
- **Function declarations** – fully hoisted (name + body), callable before definition.
- **Function expressions / arrow functions** – follow the variable rule (`var` → `undefined`, so calling gives `TypeError: not a function`).

```js
console.log(a); var a = 1;      // undefined
console.log(b); let b = 2;      // ReferenceError
hello();                        // works
function hello() {}
bye();                          // TypeError
var bye = () => {};
```
""", B, ["hoisting", "scope"], True),

("Predict the output:\n\n```js\nconsole.log('A');\nsetTimeout(() => console.log('B'), 0);\nPromise.resolve().then(() => console.log('C')).then(() => console.log('D'));\nconsole.log('E');\n```", r"""
Output: **A E C D B**

1. Synchronous code runs first: `A`, `E`.
2. After the stack is empty, the **microtask queue** drains completely: `C` runs, its `.then` queues `D` as another microtask, which also runs before any macrotask.
3. Then the **macrotask** from `setTimeout`: `B`.

Rule: sync → all microtasks (promises, `queueMicrotask`, await continuations) → next macrotask (`setTimeout`, I/O, events) → microtasks again → …
""", I, ["event-loop", "output"], True),

("Explain the event loop in JavaScript.", r"""
JavaScript has a single call stack. Long-running operations (timers, network, events) are handled by the runtime's APIs; their callbacks are queued and the **event loop** pushes them onto the stack when it is empty.

Loop iteration (browser):
1. Execute one macrotask (initial script, timer callback, event handler) until the stack is empty.
2. Drain **all microtasks** (promise callbacks, `await` continuations, `queueMicrotask`, MutationObserver).
3. Render if needed (rAF, layout, paint).
4. Pick the next macrotask.

Implications: `setTimeout(fn, 0)` runs after pending promises; heavy synchronous code freezes the UI; infinite microtask chains starve rendering. In Node, `process.nextTick` runs even before promise microtasks, and the loop has phases (timers, poll, check for `setImmediate`).
""", I, ["event-loop"], True),

("Predict the output:\n\n```js\nasync function f() {\n  console.log(1);\n  await null;\n  console.log(2);\n}\nconsole.log(3);\nf();\nconsole.log(4);\n```", r"""
Output: **3 1 4 2**

- `3` – synchronous.
- Calling `f()` runs its body **synchronously until the first `await`** → `1`.
- `await null` suspends `f`; the rest (`console.log(2)`) is scheduled as a microtask. Control returns to the caller.
- `4` – synchronous.
- Stack empty → microtask runs → `2`.

Key point: `async` doesn't make the whole function asynchronous — only the part after each `await`.
""", I, ["async-await", "event-loop", "output"], True),

("What are the different ways `this` is bound? Predict the output.\n\n```js\nconst obj = {\n  name: 'Raj',\n  a() { return this.name; },\n  b: () => this?.name,\n  c() { return [1].map(function () { return this?.name; }); },\n  d() { return [1].map(() => this.name); }\n};\nconsole.log(obj.a(), obj.b(), obj.c(), obj.d());\n```", r"""
Output (module/strict mode): **`Raj undefined [undefined] ['Raj']`**

- `a()` – implicit binding: `this` = `obj`.
- `b` – arrow function, takes `this` from module scope (`undefined`).
- `c()` – the inner regular function is called by `map` without a receiver → default binding → `undefined` (strict).
- `d()` – inner arrow inherits `this` from `d`, which is `obj`.

Binding rules by priority: `new` > explicit (`call/apply/bind`) > implicit (`obj.fn()`) > default (`undefined`/global). Arrow functions ignore all of them and use lexical `this`.
""", I, ["this", "output"], True),

("What is the difference between call, apply and bind? Write a bind polyfill.", r"""
All three set `this` explicitly:
- `fn.call(ctx, a, b)` – invokes immediately, args listed.
- `fn.apply(ctx, [a, b])` – invokes immediately, args as array.
- `fn.bind(ctx, a)` – returns a **new function** with `this` (and optionally some args) fixed; invoke later.

```js
Function.prototype.myBind = function (ctx, ...preset) {
  const fn = this;
  if (typeof fn !== 'function') throw new TypeError('Not callable');
  return function bound(...args) {
    // support `new bound()` – ignore ctx when used as constructor
    return this instanceof bound ? new fn(...preset, ...args) : fn.apply(ctx, [...preset, ...args]);
  };
};
```
Use cases: borrowing methods (`Array.prototype.slice.call(arguments)`), `Math.max.apply(null, arr)` (now `Math.max(...arr)`), fixing `this` for callbacks.
""", I, ["this", "polyfill"], True),

("Arrow functions vs regular functions — what are the differences?", r"""
1. **`this`** – arrows use lexical `this` from the surrounding scope; regular functions get `this` from the call site.
2. **`arguments`** – arrows don't have their own `arguments`; use rest params `(...args)`.
3. **Constructors** – arrows can't be used with `new` and have no `prototype`.
4. **Syntax** – concise body with implicit return: `x => x * 2`; returning an object needs parentheses: `() => ({ a: 1 })`.
5. Arrows can't be generators, and `call/apply/bind` can't change their `this`.

When to use: arrows for callbacks (`map`, `setTimeout`, promise chains) where you want the outer `this`. Regular functions/methods for object methods, prototype methods, constructors, and DOM handlers that need `this` = element.
""", B, ["functions", "this"], True),

("Explain prototypal inheritance and the prototype chain.", r"""
Every object has an internal `[[Prototype]]` link to another object (or `null`). When a property isn't found on the object, JS looks up this chain until it finds it or reaches `null`.

```js
function Animal(name) { this.name = name; }
Animal.prototype.speak = function () { return `${this.name} makes a sound`; };
function Dog(name) { Animal.call(this, name); }
Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;

const d = new Dog('Tommy');
d.speak(); // found on Animal.prototype
// chain: d -> Dog.prototype -> Animal.prototype -> Object.prototype -> null
```
ES6 `class Dog extends Animal` builds the same chain with cleaner syntax. Difference from Java: inheritance is between **objects at runtime**, not classes at compile time, and you can change prototypes dynamically.

`__proto__` is an instance's link; `prototype` is a property of constructor functions used for instances created with `new`.
""", I, ["prototypes", "inheritance"], True),

("What is the difference between == and ===? Predict: `[] == false`, `null == 0`, `NaN === NaN`.", r"""
`===` compares type and value with **no coercion**. `==` performs **type coercion** using the abstract equality algorithm.

- `[] == false` → **true**. `false` → 0; `[]` → `''` → 0; `0 == 0`.
- `null == 0` → **false**. `null` only loosely equals `undefined` (and itself).
- `null == undefined` → **true**; `null === undefined` → false.
- `NaN === NaN` → **false**. NaN is not equal to anything; use `Number.isNaN(x)` or `Object.is(x, NaN)`.
- `'1' == 1` → true; `'1' === 1` → false.
- `Object.is(0, -0)` → false, though `0 === -0` is true.

Always use `===` (ESLint `eqeqeq`), except `x == null` as a shorthand for null-or-undefined.
""", B, ["coercion", "output"], True),

("Predict the output:\n\n```js\nvar x = 1;\nfunction foo() {\n  console.log(x);\n  var x = 2;\n  console.log(x);\n}\nfoo();\nlet y = 1;\n{\n  console.log(y);\n  let y = 2;\n}\n```", r"""
Output: **`undefined`**, **`2`**, then **`ReferenceError: Cannot access 'y' before initialization`**.

- Inside `foo`, `var x` is hoisted to the top of the function and initialised to `undefined`. It **shadows** the global `x`, so the first log prints `undefined`, not `1`. After assignment, `2`.
- In the block, `let y` is also hoisted to the top of the block but sits in the **Temporal Dead Zone** until its declaration line. Because the inner `y` shadows the outer one for the whole block, `console.log(y)` throws instead of printing `1`.

Lesson: declarations are scoped to their whole function/block, not from the line they appear on. Use `let`/`const` and declare at the top to avoid surprises.
""", I, ["hoisting", "tdz", "output"], True),

("What is the difference between null, undefined and undeclared?", r"""
- **undefined** – a variable is declared but not assigned; missing object property; function with no return; missing argument. `typeof undefined === 'undefined'`.
- **null** – an intentional "no value" assigned by the programmer. `typeof null === 'object'` (a long-standing language bug).
- **undeclared** – the variable was never declared in any accessible scope; reading it throws `ReferenceError` (in strict mode, assigning to it also throws). `typeof undeclaredVar` safely returns `'undefined'`.

```js
let a;            // undefined
let b = null;     // null
console.log(c);   // ReferenceError: c is not defined
null == undefined  // true
null === undefined // false
```
Default parameters and `??` treat both null and undefined as "missing" (default params only for `undefined`).
""", B, ["basics"], False),

("What are Promises? Explain Promise.all, allSettled, race and any.", r"""
A Promise is an object representing the eventual result of an async operation: **pending**, **fulfilled** or **rejected**.

- **`Promise.all([...])`** – fulfils with an array of all results (in input order) when all succeed; **rejects immediately** on the first failure. Use for dependent-on-all parallel calls.
- **`Promise.allSettled([...])`** – waits for all; returns `{status:'fulfilled', value}` / `{status:'rejected', reason}` for each. Use when partial failure is acceptable (dashboard widgets).
- **`Promise.race([...])`** – settles with the first promise to settle (success or failure). Use for timeouts.
- **`Promise.any([...])`** – fulfils with the first **success**; rejects with `AggregateError` if all fail. Use for fastest mirror/CDN.

```js
const [user, orders] = await Promise.all([getUser(id), getOrders(id)]);
```
""", I, ["promises"], True),

("Implement Promise.all from scratch.", r"""
```js
function promiseAll(iterable) {
  return new Promise((resolve, reject) => {
    const items = Array.from(iterable);
    const results = new Array(items.length);
    let remaining = items.length;
    if (remaining === 0) return resolve(results);

    items.forEach((item, index) => {
      Promise.resolve(item)            // handle non-promise values
        .then(value => {
          results[index] = value;      // preserve order, not completion order
          if (--remaining === 0) resolve(results);
        })
        .catch(reject);                // first rejection wins
    });
  });
}

promiseAll([1, Promise.resolve(2), new Promise(r => setTimeout(r, 100, 3))])
  .then(console.log); // [1, 2, 3]
```
Key points interviewers check: order preserved by index, empty input resolves immediately, non-promises wrapped with `Promise.resolve`, fail-fast rejection.
""", A, ["promises", "polyfill"], True),

("What is async/await? How do you run awaits in parallel?", r"""
`async/await` is syntax over promises. An `async` function always returns a promise; `await` pauses the function until the promise settles and returns its value (or throws its rejection, catchable with `try/catch`).

**Sequential (slow if independent):**
```js
const user = await getUser();      // 300ms
const products = await getProducts(); // 300ms  → total 600ms
```
**Parallel:**
```js
const [user, products] = await Promise.all([getUser(), getProducts()]); // ~300ms
```
**Loops:**
```js
for (const id of ids) await save(id);                 // sequential, ordered
await Promise.all(ids.map(id => save(id)));           // parallel
ids.forEach(async id => await save(id));              // BUG: forEach doesn't wait
```
For bounded concurrency (e.g. 5 at a time), process in chunks or use a small pool helper.
""", I, ["async-await", "promises"], True),

("Implement a debounce function. How is it different from throttle?", r"""
**Debounce** delays execution until the event has stopped firing for `delay` ms (search input, window resize end). **Throttle** executes at most once per interval during continuous firing (scroll, mousemove, button spam).

```js
function debounce(fn, delay = 300) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

function throttle(fn, interval = 200) {
  let last = 0;
  return function (...args) {
    const now = Date.now();
    if (now - last >= interval) { last = now; fn.apply(this, args); }
  };
}

input.addEventListener('input', debounce(e => search(e.target.value), 400));
window.addEventListener('scroll', throttle(updateProgress, 100));
```
Both rely on closures to keep `timer`/`last` between calls. In Angular you'd use RxJS `debounceTime`/`throttleTime`.
""", I, ["closures", "machine-coding"], True),

("Shallow copy vs deep copy in JavaScript — how do you do each?", r"""
A **shallow copy** duplicates top-level properties; nested objects are still **shared references**. A **deep copy** recursively copies everything.

```js
const user = { name: 'Raj', address: { city: 'Pune' } };
const shallow = { ...user };            // or Object.assign({}, user)
shallow.address.city = 'Bangalore';
console.log(user.address.city);          // 'Bangalore' – shared!

const deep = structuredClone(user);      // modern, handles Date, Map, Set, cycles
deep.address.city = 'Delhi';             // original unaffected
```
Options for deep copy:
- `structuredClone` – best built-in (not functions/DOM nodes/class prototypes).
- `JSON.parse(JSON.stringify(x))` – loses `undefined`, functions, Dates (become strings), Infinity; fails on cycles.
- Lodash `cloneDeep` or a custom recursive function.

Arrays: `[...arr]`, `arr.slice()` are shallow.
""", B, ["objects", "es6"], True),

("Predict the output:\n\n```js\nconst a = { x: 1 };\nconst b = a;\nb.x = 2;\nlet c = 5;\nlet d = c;\nd = 10;\nconsole.log(a.x, c);\nfunction change(o) { o.x = 3; o = { x: 4 }; }\nchange(a);\nconsole.log(a.x);\n```", r"""
Output: **`2 5`** then **`3`**

- Objects are assigned by **reference**: `b` and `a` point to the same object, so `b.x = 2` changes `a.x`.
- Primitives are copied by **value**: changing `d` doesn't affect `c`.
- In `change(o)`, `o` receives a copy of the **reference** (JS is pass-by-value, where the value is a reference — "call by sharing"). `o.x = 3` mutates the shared object. `o = { x: 4 }` only reassigns the local parameter, so the caller's `a` is unaffected.

This is the same as Java's behaviour with object references.
""", B, ["output", "references"], True),

("What are map, filter and reduce? Implement a reduce polyfill.", r"""
- `map(cb)` – returns a new array of transformed values (same length).
- `filter(cb)` – returns a new array of elements where `cb` returns truthy.
- `reduce(cb, init)` – folds the array into a single value.

```js
const orders = [{ amt: 500, paid: true }, { amt: 300, paid: false }, { amt: 200, paid: true }];
const paidTotal = orders.filter(o => o.paid).map(o => o.amt).reduce((s, a) => s + a, 0); // 700

Array.prototype.myReduce = function (cb, initial) {
  let i = 0, acc = initial;
  if (arguments.length < 2) {
    while (i < this.length && !(i in this)) i++;          // skip holes
    if (i >= this.length) throw new TypeError('Reduce of empty array with no initial value');
    acc = this[i++];
  }
  for (; i < this.length; i++) if (i in this) acc = cb(acc, this[i], i, this);
  return acc;
};
```
None of them mutate the original array; `forEach` returns `undefined`.
""", I, ["arrays", "polyfill"], True),

("What is event delegation and event bubbling/capturing?", r"""
DOM events propagate in three phases: **capturing** (window → target), **target**, then **bubbling** (target → window). `addEventListener(type, fn, true)` or `{ capture: true }` listens during capture; default is bubbling.

**Event delegation** – attach one listener to a common ancestor and use `event.target` to handle events from many (even dynamically added) children.

```js
document.querySelector('#todo-list').addEventListener('click', e => {
  const btn = e.target.closest('button.delete');
  if (btn) removeTodo(btn.dataset.id);
});
```
Benefits: fewer listeners (memory), works for elements added later. Use `e.stopPropagation()` to stop bubbling and `e.preventDefault()` to cancel default action (form submit, link navigation) — they're different things. Some events (`focus`, `blur`) don't bubble; use `focusin`/`focusout`.
""", I, ["dom", "events"], False),

("What is currying? Implement sum(1)(2)(3)() .", r"""
**Currying** transforms `f(a, b, c)` into `f(a)(b)(c)` — each call takes one (or some) argument and returns a function waiting for the rest. It enables partial application and function reuse.

```js
// fixed arity
const add = a => b => c => a + b + c;
add(1)(2)(3); // 6

// infinite: sum(1)(2)(3)() -> 6
function sum(a) {
  return function next(b) {
    if (b === undefined) return a;
    a += b;
    return next;
  };
}
sum(1)(2)(3)(); // 6

// generic curry
const curry = fn => function c(...args) {
  return args.length >= fn.length ? fn.apply(this, args) : (...more) => c.apply(this, [...args, ...more]);
};
```
Real use: `const logError = log('ERROR'); logError('DB down');`.
""", I, ["closures", "functional"], False),

("What are generators and iterators?", r"""
An **iterator** is an object with a `next()` method returning `{ value, done }`. An **iterable** has a `[Symbol.iterator]()` method returning an iterator — arrays, strings, Maps, Sets are iterables, enabling `for...of`, spread and destructuring.

A **generator** function (`function*`) produces an iterator whose execution can **pause at `yield`** and resume on the next `next()` call.

```js
function* range(start, end, step = 1) {
  for (let i = start; i < end; i += step) yield i;
}
[...range(0, 10, 3)]; // [0, 3, 6, 9]

const it = range(0, 2);
it.next(); // { value: 0, done: false }
it.next(); // { value: 1, done: false }
it.next(); // { value: undefined, done: true }
```
Uses: lazy/infinite sequences, custom iterables, pagination (`async function*` with `for await...of`), and historically the basis of async/await and Redux-Saga.
""", A, ["es6", "generators"], False),

("What is the difference between Map and Object, Set and Array, WeakMap and Map?", r"""
**Map vs Object**
- Map keys can be **any type** (objects, functions); object keys are strings/symbols.
- Map preserves insertion order and has `size`; iterable directly.
- Map is optimised for frequent additions/removals; no prototype key collisions (`'toString'`).
- Objects are better for fixed-shape records and JSON.

**Set vs Array** – Set stores **unique** values with O(1) average `has`; Array allows duplicates and has O(n) `includes`. Dedupe: `[...new Set(arr)]`.

**WeakMap vs Map** – WeakMap keys must be objects and are held **weakly**: if nothing else references the key, it's garbage-collected along with its value. Not iterable, no `size`. Use for caching metadata about DOM nodes/objects without causing memory leaks.
""", I, ["es6", "collections"], False),

("What is the difference between `interface` and `type` in TypeScript?", r"""
Both describe object shapes and are mostly interchangeable, but:

| interface | type |
|---|---|
| Only object/function shapes | Any type: unions, tuples, primitives, mapped/conditional |
| `extends` for inheritance | `&` intersection |
| **Declaration merging** (two `interface X` merge) | Cannot be re-declared |
| Classes can `implements` it | Classes can implement object-like types too |
| Better error messages for large hierarchies | Needed for `type Status = 'A' \| 'B'` |

```ts
interface Animal { name: string }
interface Animal { age: number }      // merged: { name; age }
type Id = string | number;            // only possible with type
type Admin = User & { perms: string[] };
```
Convention: `interface` for object models/public contracts (DTOs, service APIs), `type` for unions, utility compositions and function types.
""", B, ["typescript"], True),

("What are generics in TypeScript? Give an example with constraints.", r"""
Generics let you write reusable components that work with many types while keeping type safety — the type is a parameter.

```ts
function identity<T>(value: T): T { return value; }

interface Page<T> { content: T[]; totalElements: number; number: number; } // mirrors Spring Data Page
getOrders(): Observable<Page<Order>> { return this.http.get<Page<Order>>('/api/orders'); }

// constraint: T must have an id
function findById<T extends { id: number }>(items: T[], id: number): T | undefined {
  return items.find(i => i.id === id);
}

// keyof constraint
function pluck<T, K extends keyof T>(items: T[], key: K): T[K][] {
  return items.map(i => i[key]);
}
pluck(users, 'email');   // string[]
pluck(users, 'emial');   // compile error
```
Unlike Java, TS generics are purely compile-time (erased) and structural; default type params are allowed: `<T = string>`.
""", I, ["typescript", "generics"], True),

("Explain TypeScript utility types: Partial, Pick, Omit, Record, Readonly.", r"""
Built-in mapped types that transform existing types:

```ts
interface User { id: number; name: string; email: string; password: string; }

type UserPatch   = Partial<User>;                   // all optional – PATCH body
type UserCard    = Pick<User, 'id' | 'name'>;        // subset
type PublicUser  = Omit<User, 'password'>;           // remove sensitive field
type RoleMap     = Record<'ADMIN' | 'USER', User[]>; // keyed dictionary
type FrozenUser  = Readonly<User>;                   // can't reassign props
type Full        = Required<Partial<User>>;          // all required again
```
Others: `Exclude<'a'|'b', 'a'>` → `'b'`, `Extract`, `NonNullable<T>`, `ReturnType<typeof fn>`, `Parameters<typeof fn>`, `Awaited<Promise<X>>`.

Implementing one shows depth:
```ts
type MyPartial<T> = { [K in keyof T]?: T[K] };
type MyPick<T, K extends keyof T> = { [P in K]: T[P] };
```
""", I, ["typescript", "utility-types"], True),

("What is the difference between `any`, `unknown` and `never`?", r"""
- **`any`** – disables type checking; you can do anything with it, and it silently spreads. Avoid except when migrating JS.
- **`unknown`** – the type-safe counterpart: any value can be assigned to it, but you must **narrow** before using it. Ideal for `JSON.parse` results, `catch (e)` blocks, external input.
- **`never`** – the type with no values: functions that never return (throw/infinite loop), impossible branches, exhaustiveness checks.

```ts
function parse(json: string): unknown { return JSON.parse(json); }
const data = parse('{"id":1}');
data.id;                                   // error
if (typeof data === 'object' && data && 'id' in data) console.log(data.id); // ok

type Status = 'OPEN' | 'CLOSED';
function label(s: Status) {
  switch (s) { case 'OPEN': return 'Open'; case 'CLOSED': return 'Closed';
    default: const x: never = s; throw new Error(x); } // errors if a new status is added
}
```
""", I, ["typescript"], True),

("What are type guards and discriminated unions in TypeScript?", r"""
A **type guard** is a runtime check that lets TypeScript narrow a type within a block: `typeof`, `instanceof`, `in`, equality, truthiness, or a **user-defined guard** returning `x is T`.

```ts
function isApiError(e: unknown): e is { status: number; message: string } {
  return typeof e === 'object' && e !== null && 'status' in e;
}
```
A **discriminated union** is a union of object types sharing a literal "tag" property; checking the tag narrows the type:

```ts
type Payment =
  | { method: 'UPI'; vpa: string }
  | { method: 'CARD'; last4: string; network: 'VISA' | 'RUPAY' }
  | { method: 'COD' };

function describe(p: Payment) {
  switch (p.method) {
    case 'UPI':  return `UPI ${p.vpa}`;
    case 'CARD': return `${p.network} ****${p.last4}`;
    case 'COD':  return 'Cash on delivery';
  }
}
```
Great for modelling state machines (loading/success/error) and API responses safely.
""", A, ["typescript", "narrowing"], False),

("What is the difference between enum and a union of string literals in TypeScript?", r"""
```ts
enum Role { Admin = 'ADMIN', User = 'USER' }      // generates a runtime object
type RoleU = 'ADMIN' | 'USER';                     // compile-time only, zero JS
const ROLES = { Admin: 'ADMIN', User: 'USER' } as const;
type RoleC = typeof ROLES[keyof typeof ROLES];     // 'ADMIN' | 'USER'
```
- **Enums** create runtime JavaScript code (an object, with reverse mapping for numeric enums), can be iterated, and are nominal-ish (you must use `Role.Admin`, not `'ADMIN'`). Numeric enums are unsafe (`let r: NumEnum = 42` compiles in older TS).
- **String literal unions** emit no code, work directly with JSON values from APIs, and give great autocomplete.
- **`as const` objects** give both a runtime object and a union type.

Many teams prefer unions or `as const` objects; `const enum` inlines values but has issues with isolated module builds (esbuild/Vite).
""", I, ["typescript", "enums"], False),

("What does the `?.`, `??` and `!` operators do in TypeScript/JavaScript?", r"""
- **Optional chaining `?.`** – stops and returns `undefined` if the left side is `null`/`undefined`: `user?.address?.city`, `fn?.()`, `arr?.[0]`.
- **Nullish coalescing `??`** – returns right side only if left is `null` or `undefined` (unlike `||`, which also replaces `0`, `''`, `false`):
```js
const qty = input.qty ?? 1;     // 0 stays 0
const qty2 = input.qty || 1;    // 0 becomes 1 (bug)
```
- **Non-null assertion `!` (TS only)** – tells the compiler "trust me, this isn't null": `document.getElementById('app')!`. No runtime check — if wrong, you get a runtime error. Prefer narrowing.
- Related: definite assignment `name!: string;` in classes (common with Angular `@ViewChild`), and `??=`.
""", B, ["typescript", "es6"], False),

("Predict the output:\n\n```js\nconsole.log(typeof null, typeof [], typeof function(){}, typeof NaN);\nconsole.log([1,2,3] + [4,5]);\nconsole.log('5' - 2, '5' + 2, true + 1);\nconsole.log(0.1 + 0.2 === 0.3);\n```", r"""
Output:
```
object object function number
1,2,34,5
3 52 2
false
```
- `typeof null` is `'object'` (historic bug); arrays are objects (use `Array.isArray`); functions report `'function'`; `NaN` is of type number.
- `+` with arrays converts them to strings: `'1,2,3' + '4,5'` = `'1,2,34,5'`.
- `-` forces numeric conversion: `'5' - 2 = 3`. `+` with a string concatenates: `'52'`. `true` → 1, so `2`.
- Floating-point (IEEE-754) can't represent 0.1/0.2 exactly; sum is `0.30000000000000004`. Compare with `Math.abs(a - b) < Number.EPSILON`, or keep money in paise as integers.
""", I, ["coercion", "output"], True),

("What are ES modules vs CommonJS?", r"""
| ES Modules (ESM) | CommonJS (CJS) |
|---|---|
| `import` / `export` | `require()` / `module.exports` |
| **Static** structure – analysed at build time → tree-shaking | Dynamic – can `require` conditionally |
| Async loading, supports top-level `await` | Synchronous loading |
| Live bindings (imports reflect updated exports) | Copies of exported values at require time |
| Strict mode by default | Not strict by default |
| Standard in browsers and modern Node (`"type": "module"`, `.mjs`) | Node's original system (`.cjs`) |

Dynamic `import('./x.js')` returns a promise and enables code splitting — Angular's `loadComponent` uses it. Bundlers (esbuild, Vite, webpack) rely on ESM's static imports to remove unused code.
""", I, ["modules", "es6"], False),

("What is the difference between `for...in`, `for...of` and `forEach`?", r"""
- **`for...in`** – iterates **enumerable property keys** (strings) of an object, including **inherited** ones. Meant for objects; avoid for arrays (order and inherited props issues).
- **`for...of`** – iterates **values** of any iterable (arrays, strings, Maps, Sets, generators). Supports `break`, `continue`, and `await` inside async functions.
- **`forEach`** – array method calling a callback for each element. Can't `break` (except by throwing), ignores returned promises (doesn't wait for `async` callbacks), returns `undefined`.

```js
const arr = ['a', 'b'];
for (const i in arr) console.log(i);    // '0' '1'
for (const v of arr) console.log(v);    // 'a' 'b'
for (const [k, v] of Object.entries({ x: 1 })) console.log(k, v); // x 1
```
""", B, ["loops", "basics"], False),

("How does garbage collection work in JavaScript and what causes memory leaks?", r"""
JS engines (V8) use **automatic garbage collection** based on **reachability**: objects reachable from roots (global object, current call stack, closures in use) are kept; unreachable ones are freed. V8 uses a generational collector (young generation "scavenge" + old generation **mark-and-sweep/mark-compact**), so cyclic references are not a problem by themselves.

Common leaks in front-end apps:
1. **Forgotten event listeners / subscriptions** (`addEventListener` without remove, RxJS without unsubscribe).
2. **Timers** (`setInterval`) never cleared.
3. **Closures** holding large data unintentionally.
4. **Detached DOM nodes** still referenced from JS.
5. **Global variables** / caches that grow unbounded (use `WeakMap` or LRU).

Detect with Chrome DevTools → Memory → heap snapshots (compare before/after navigation) and the Performance monitor.
""", A, ["memory", "performance"], False),
]

sources = [
("MDN - Closures", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures"),
("MDN - The event loop / microtask guide", "https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide"),
("MDN - Inheritance and the prototype chain", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Inheritance_and_the_prototype_chain"),
("MDN - Using promises", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises"),
("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html"),
("TypeScript - Utility Types", "https://www.typescriptlang.org/docs/handbook/utility-types.html"),
("javascript.info - The Modern JavaScript Tutorial", "https://javascript.info/"),
("GeeksforGeeks - JavaScript Interview Questions", "https://www.geeksforgeeks.org/javascript-interview-questions/"),
("InterviewBit - TypeScript Interview Questions", "https://www.interviewbit.com/typescript-interview-questions/"),
]

build("javascript-typescript", "js", "JavaScript & TypeScript", 6, "🟨",
      "Core JavaScript internals (closures, this, prototypes, event loop, promises) and TypeScript's type system, with output-prediction practice.",
      notes, qa, sources)
