from traps2_common import T

A = "angular-js"

RX = "/home/claude/switch-prep/frontend/node_modules/rxjs"

VAR_LOOP = """for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}"""

VAR_FIX = """for (let i = 0; i < 3; i++) {          // new binding per iteration
  setTimeout(() => console.log(i), 0); // 0 1 2
}"""

THIS_PROMPT = """export class CartComponent {
  total = 0;
  constructor(private api: CartApi) {}

  load() {
    this.api.getTotal().then(this.onTotal);
  }

  onTotal(value: number) {
    this.total = value;   // TypeError: Cannot set properties of undefined (setting 'total')
  }
}"""

THIS_FIX = """load() {
  this.api.getTotal().then(v => this.onTotal(v));   // arrow keeps lexical `this`
}

// or define the handler as an arrow-function property
onTotal = (value: number) => {
  this.total = value;
};

// or bind explicitly: .then(this.onTotal.bind(this))"""

LOOP_ORDER = """console.log('A');
setTimeout(() => console.log('B'), 0);
Promise.resolve().then(() => console.log('C'));
(async () => {
  console.log('D');
  await null;
  console.log('E');
})();
console.log('F');"""

ASYNC_FOREACH = """async function saveAll(items) {
  items.forEach(async (item) => {
    await save(item);
  });
  console.log('all saved');
}"""

ASYNC_FIX = """// sequential, in order, stops at the first error
async function saveAllSequential(items) {
  for (const item of items) {
    await save(item);
  }
  console.log('all saved');
}

// parallel, waits for all, rejects on the first failure
async function saveAllParallel(items) {
  await Promise.all(items.map(item => save(item)));
  console.log('all saved');
}

// parallel, report every failure instead of failing fast
async function saveAllSettled(items) {
  const results = await Promise.allSettled(items.map(item => save(item)));
  return results.filter(r => r.status === 'rejected').length;   // number of failures
}"""

EQ_FIX = """[] == false          // true  ([] -> '' -> 0, false -> 0)
null == 0            // false (null only == undefined)
null == undefined    // true  (the one idiomatic use: x == null)
NaN === NaN          // false -> use Number.isNaN(x)
'5' === 5            // false (no coercion)
({}) === ({})        // false: objects compare by reference
typeof null          // 'object' (historic bug)"""

ONPUSH_PROMPT = """@Component({
  selector: 'app-todo-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<ul>@for (t of todos; track t.id) { <li>{{ t.title }}</li> }</ul>`,
})
export class TodoListComponent {
  @Input() todos: Todo[] = [];
}

// parent component
addTodo(title: string) {
  this.todos.push({ id: Date.now(), title });   // the child list does not update
}"""

ONPUSH_FIX = """// Option 1: immutable update -> new reference, OnPush child sees a changed input
addTodo(title: string) {
  this.todos = [...this.todos, { id: Date.now(), title }];
}

// Option 2: signals (works with zoneless Angular too)
todos = signal<Todo[]>([]);
addTodoWithSignal(title: string) {
  this.todos.update(list => [...list, { id: Date.now(), title }]);
}
// child: todos = input.required<Todo[]>();  template reads todos()"""

LEAK_PROMPT = """ngOnInit() {
  this.route.paramMap.subscribe(params => {
    this.api.getUser(params.get('id')!).subscribe(user => {
      this.user = user;
    });
  });

  interval(5000).subscribe(() => this.refreshNotifications());
}"""

LEAK_FIX = """private route = inject(ActivatedRoute);
private api = inject(UserApi);
private destroyRef = inject(DestroyRef);

// template: @if (user$ | async; as user) { ... }  -> async pipe subscribes AND unsubscribes
user$ = this.route.paramMap.pipe(
  map(params => params.get('id')!),
  switchMap(id => this.api.getUser(id)),        // a new id cancels the previous request
);

ngOnInit() {
  interval(5000)
    .pipe(takeUntilDestroyed(this.destroyRef))  // stops when the component is destroyed
    .subscribe(() => this.refreshNotifications());
}"""

SEARCH_FIX = """results$ = this.searchCtrl.valueChanges.pipe(
  debounceTime(300),
  map(q => (q ?? '').trim()),
  distinctUntilChanged(),
  switchMap(q => q.length < 2
    ? of([])
    : this.api.search(q).pipe(catchError(() => of([])))),   // catch INSIDE so the stream survives
);

saveClicks$.pipe(concatMap(form => this.api.save(form)));     // ordered, none dropped
payClicks$.pipe(exhaustMap(() => this.api.pay(this.orderId))); // ignore double-clicks while paying"""

TRAPS = [
    T("trap-angular-js-var-closure-loop", A, "Closures in loops: var vs let", "Basic", "Very common",
      f"""What does this print?

```js
{VAR_LOOP}
```""",
      "0 1 2, because each callback captures the value of `i` at the time it was created.",
      """People think a closure captures the **value** at creation time. It captures the **variable** (the binding). With `var` there is only one `i` for the whole function, and the callbacks run after the loop has finished, when `i` is 3. Developers coming from Java expect block scoping everywhere, and the similar-looking `let` version behaves differently, which makes this a favourite quick filter question.""",
      """It prints **3 3 3**.

- `var` is **function-scoped**: the loop shares one `i`. `setTimeout` callbacks run only after the current synchronous code (the whole loop) completes, so each one reads `i === 3`.
- `let` is **block-scoped**, and a `for (let ...)` loop creates a **fresh binding per iteration**, so each callback closes over its own `i`, printing 0 1 2.
- The pre-ES6 fix was an IIFE that passed `i` as a parameter.

Why it matters in Angular code: the same capture rules apply to callbacks created in loops (event listeners, subscriptions, `setTimeout` inside `forEach` with mutable outer variables). Prefer `const`/`let`, avoid `var`, and keep in mind that a closure sees the variable's **current** value when it runs, not the value when it was created.

Follow-up interviewers like: "What if it's `setTimeout(console.log, 0, i)`?" That prints 0 1 2, because `i` is passed as an argument, evaluated immediately.""",
      "Say \"closures capture bindings, not values\" and explain per-iteration bindings for `let`.",
      options=["0 1 2", "3 3 3", "2 2 2", "undefined undefined undefined"], answer=1,
      fix=f"""```js
{VAR_FIX}
```""",
      askedAt=["Infosys", "Accenture", "Paytm", "Zoho"]),

    T("trap-angular-js-this-in-callbacks", A, "Losing `this` when passing a method as a callback", "Intermediate", "Very common",
      f"""Why does this throw?

```ts
{THIS_PROMPT}
```""",
      "Promises run outside Angular's zone, so the component's fields are not accessible.",
      """In Java, `this` is fixed to the object, so a method reference always remembers its owner. In JavaScript, a regular function's `this` is decided by **how it is called**, not where it was defined. `this.onTotal` without parentheses passes a bare function. The promise later calls it as a plain function, and class bodies run in strict mode, so `this` is `undefined`. Blaming zones or change detection is the common guess.""",
      """`.then(this.onTotal)` **detaches** the method from the instance. When the promise invokes it as a plain function, `this` is `undefined` (class code is always strict mode), so assigning `this.total` throws.

Fixes:
- **Arrow wrapper**: `.then(v => this.onTotal(v))`. Arrow functions don't have their own `this`; they use the surrounding one.
- **Arrow-function class property**: `onTotal = (v: number) => { ... }`, permanently bound to the instance.
- **`bind`**: `.then(this.onTotal.bind(this))`.

The same trap appears with `subscribe(this.handle)`, `addEventListener('click', this.onClick)`, and `setTimeout(this.tick, 1000)`. With `setTimeout`, browsers call the callback with `this` = `window`, so instead of a crash you get a **silent** bug that writes to the wrong object.

The reverse mistake: using an arrow function as an object method that *needs* a dynamic `this`.""",
      "Explain the four `this` rules (call site, method call, `new`, explicit bind) plus \"arrows inherit `this`\" in one breath.",
      options=[
          "Promises run outside Angular's zone.",
          "`this.onTotal` is passed as a plain function reference, so when the promise calls it `this` is `undefined` (class code is strict mode).",
          "`total` must be declared as a signal to be assignable.",
          "TypeScript compiles `this` to `window` inside classes.",
      ], answer=1,
      fix=f"""```ts
{THIS_FIX}
```""",
      askedAt=["Walmart", "Publicis Sapient", "Thoughtworks"]),

    T("trap-angular-js-event-loop-order", A, "Event loop: microtasks vs macrotasks", "Intermediate", "Very common",
      f"""What is the output order?

```js
{LOOP_ORDER}
```""",
      "A B C D E F, in source order, because `setTimeout(..., 0)` runs immediately.",
      """`setTimeout(fn, 0)` *reads* like "now", and `async` *reads* like "runs later in the background". Both readings are wrong. Candidates also lump all async callbacks together, not knowing there are two queues with different priority. Interviewers use this exact puzzle because the answer shows whether you understand why a promise callback beats a timer, and why Angular's change detection runs when it does.""",
      """Output: **A D F C E B**.

1. **Synchronous code runs first**: `A`, then the async function's body up to its first `await` (`D`), then `F`.
2. When the call stack is empty, the **microtask queue is drained completely**: promise callbacks (`C`) and code after an `await` (`E`), in the order they were queued.
3. Only then does the event loop take the next **macrotask**: timers (`B`), I/O, UI events.

Rules worth stating: `await x` suspends the function and resumes it in a microtask, even if `x` is not a promise. `setTimeout(fn, 0)` means "at the earliest, after the current task and all microtasks" (browsers clamp nested timers to at least 4 ms). An endless chain of microtasks **starves** rendering and timers.

Angular link: Zone.js patches these async APIs to know when to run change detection. In zoneless Angular, signals and `markForCheck` schedule updates instead.""",
      "Narrate the three phases (sync → drain microtasks → one macrotask) instead of just giving the order.",
      options=["A B C D E F", "A D F C E B", "A F D B C E", "A D F B C E"], answer=1,
      askedAt=["Flipkart", "Microsoft", "Swiggy", "Paytm"]),

    T("trap-angular-js-async-foreach", A, "`async` callback inside forEach is not awaited", "Intermediate", "Common",
      f"""A bulk-save helper:

```js
{ASYNC_FOREACH}
```

What actually happens, and how do you fix it?""",
      "It saves each item one by one and logs 'all saved' after the last save, because of the `await`.",
      """The `await` is right there in the code, so it *looks* sequential. But it is inside the callback, and it only pauses that callback. `forEach` ignores the promise each callback returns and moves on. Candidates also wrap the `forEach` in `try/catch` expecting to catch save errors, which can't work because the rejections happen later. In Node 15+, an unhandled rejection crashes the process by default, which makes this a production bug, not just a style issue.""",
      """`forEach` fires all callbacks synchronously and returns `undefined`. So:
- **'all saved' logs before any save finishes**.
- All saves run **concurrently** with no limit (500 items = 500 simultaneous requests).
- Rejections are **unhandled**: the caller's `try/catch` and `.catch` never see them.

Pick the behaviour you actually want:
- **Sequential** (order matters, or to protect the backend): `for (const item of items) await save(item);`
- **Parallel**: `await Promise.all(items.map(save))`. It rejects on the first failure; the other saves keep running.
- **Parallel with a full report**: `Promise.allSettled`.
- **Bounded concurrency** for large batches: process in chunks, or use a limiter.

RxJS equivalents: `from(items).pipe(concatMap(save))` for sequential, and `mergeMap(save, 5)` for at most 5 at a time.

The same trap applies to `map` without `Promise.all`, and to `filter` or `reduce` with async callbacks.""",
      "Ask \"sequential or parallel?\" before fixing; choosing deliberately is the senior signal.",
      fix=f"""```js
{ASYNC_FIX}
```""",
      askedAt=["Razorpay", "Atlassian", "Postman"]),

    T("trap-angular-js-equality-coercion", A, "`==` vs `===` and coercion surprises", "Basic", "Common",
      """Which of these evaluates to `true`?""",
      "`null == 0`, because null is \"empty\" like 0.",
      """Candidates know "`===` is stricter" but not the actual coercion rules, so they guess from intuition about "empty" values. The rules are not intuitive: objects convert to primitives, booleans convert to numbers, and `null` only loosely equals `undefined`. Interviewers ask it to check whether you rely on habits (always `===`) that you can justify, and whether you know related traps such as `NaN` and object reference comparison.""",
      """**`[] == false` is `true`**: `false` becomes `0`, `[]` becomes `''` and then `0`, so `0 == 0`.

The others are false:
- `NaN === NaN` is false, because NaN is not equal to anything, including itself. Use `Number.isNaN`.
- `null == 0` is false: under `==`, `null` equals only `null` and `undefined`.
- `'5' === 5` is false, because strict equality never coerces.

Practical rules:
- Use `===` and `!==` everywhere. The one idiomatic exception is `x == null`, which checks both `null` and `undefined`.
- Objects and arrays compare **by reference**: `{} === {}` is false. In Angular this is why mutating an array does not trigger OnPush or `ngOnChanges`, and why `distinctUntilChanged()` on objects needs a comparator.
- `typeof null === 'object'` is a historic quirk; check `x === null` explicitly.""",
      "Mention the reference-equality consequence for OnPush and `distinctUntilChanged`; it connects trivia to real Angular bugs.",
      options=["`NaN === NaN`", "`[] == false`", "`null == 0`", "`'5' === 5`"], answer=1,
      fix=f"""```js
{EQ_FIX}
```""",
      askedAt=["TCS", "Infosys", "Zoho"]),

    T("trap-angular-js-onpush-mutation", A, "OnPush not updating after mutation", "Intermediate", "Very common",
      f"""The child uses `OnPush`. The parent adds a todo, but the list on screen does not change:

```ts
{ONPUSH_PROMPT}
```

Why, and what are the correct fixes?""",
      "OnPush is broken or buggy here; just call `detectChanges()` everywhere or switch back to Default.",
      """With Default change detection, mutation "just works", so developers never learn that Angular compares inputs **by reference** (`Object.is`). After turning on OnPush for performance, mutated arrays and objects stop updating, and the reflex is to sprinkle `detectChanges()` around or turn OnPush off. Interviewers probe exactly when an OnPush component is checked, because it is the core of Angular performance questions.""",
      """`push()` mutates the **same array**, so the child's `@Input` reference is unchanged. OnPush skips the child.

An OnPush component is checked only when:
1. an **input reference changes**;
2. an **event** fires in the component or its children (a template-bound handler);
3. an **`async` pipe** in its template emits;
4. a **signal** read in its template changes;
5. you call **`markForCheck()`** (marks it and its ancestors for the next check).

Fixes: use **immutable updates** (`[...list, item]`, `{...obj, field}`), or **signals** (`todos.update(...)`), or expose an observable consumed with the `async` pipe.

A related trap: inside an OnPush component, a `setTimeout` or a manual `subscribe` callback that assigns a plain field will **not** render. Zone.js runs change detection, but the component is not marked dirty. Use a signal, the `async` pipe or `markForCheck()`. In zoneless Angular (stable since v20.2), signals and `markForCheck` are the only triggers.""",
      "List the OnPush triggers from memory; that list is what the interviewer is checking.",
      fix=f"""```ts
{ONPUSH_FIX}
```""",
      askedAt=["Publicis Sapient", "Thoughtworks", "Walmart", "Deloitte"]),

    T("trap-angular-js-subscription-leaks", A, "Subscription leaks and nested subscribes", "Intermediate", "Very common",
      f"""Review this component code. What are the problems?

```ts
{LEAK_PROMPT}
```""",
      "Every subscribe leaks, including the HttpClient call, so add `unsubscribe()` calls for all three in `ngOnDestroy`.",
      """Candidates have heard "always unsubscribe" and apply it mechanically, without knowing **which** observables complete on their own. They also nest `subscribe` calls because it mirrors callback-style code, missing that nesting loses cancellation and ordering. The interviewer wants you to spot the *real* leak (the `interval`), explain the race in the nested subscribe, and know that the async pipe and `takeUntilDestroyed` exist.""",
      """**The real leak is `interval(5000)`**. It never completes, so it keeps calling `refreshNotifications()` after the component is destroyed, and each visit to the page adds **another** interval.

**The nested subscribe is a race**: if the route id changes quickly (user A → user B), both requests run, and if A's response arrives last, the page shows **the wrong user**. There is no cancellation, and error handling is scattered.

What does *not* leak: `HttpClient` observables complete after one response, and `ActivatedRoute` observables are cleaned up by the router when the component is destroyed.

Fixes:
- Flatten with **`switchMap`**: a new id cancels the in-flight request.
- Prefer the **`async` pipe** (or `toSignal`) in the template: it subscribes and unsubscribes for you.
- For long-lived manual subscriptions, use **`takeUntilDestroyed()`**. Call it with no argument in an injection context (field initialiser or constructor), or pass a `DestroyRef` when calling it in `ngOnInit`.""",
      "Distinguish completing observables (HTTP) from infinite ones (interval, valueChanges, store selects) before saying \"unsubscribe\".",
      fix=f"""```ts
{LEAK_FIX}
```""",
      askedAt=["Thoughtworks", "Publicis Sapient", "Walmart", "EPAM"]),

    T("trap-angular-js-switchmap-vs-mergemap", A, "Choosing switchMap / mergeMap / concatMap / exhaustMap", "Advanced", "Very common",
      """Pick the right flattening operator for each case:

1. Search-as-you-type that calls an API.
2. Auto-saving form edits, where every save must reach the server in order.
3. A "Pay" button that must ignore extra clicks while a payment request is in flight.""",
      "Use switchMap everywhere, because cancelling the previous request is always the safest choice.",
      """Many tutorials only teach `switchMap` for search, so it becomes the default for everything. Others reach for `mergeMap` because it "just works" in demos where responses come back instantly and in order. The subtle part candidates miss: `switchMap` cancels by **unsubscribing**, which aborts the browser request, but the server may already have processed it. So with saves you silently lose or reorder writes, and with payments you risk duplicate charges.""",
      """**switchMap, concatMap, exhaustMap.**

- **switchMap**: only the latest result matters. Search, typeahead, loading data for the current route parameter. Old requests are cancelled, so stale responses can't overwrite new ones.
- **concatMap**: queue and preserve order, none dropped. Saves, sequential writes, ordered uploads.
- **exhaustMap**: ignore new triggers while one is running. Submit, login and pay buttons, pull-to-refresh.
- **mergeMap**: run in parallel, order doesn't matter. Independent operations such as deleting several selected items. Pass a concurrency limit (`mergeMap(fn, 4)`).

Why the wrong choices fail: **mergeMap for search** lets a slow response for "ja" arrive after "java" and overwrite the newer results. **switchMap for saves** cancels in-flight saves client-side, while the server may or may not have applied them.

For search, also add `debounceTime`, `distinctUntilChanged`, and `catchError` **inside** the inner observable, because an error in the outer stream completes it and search stops working forever.""",
      "Give one real use case per operator; interviewers remember \"exhaustMap for the pay button\".",
      options=[
          "mergeMap, mergeMap, mergeMap",
          "switchMap, concatMap, exhaustMap",
          "switchMap, switchMap, switchMap",
          "concatMap, switchMap, mergeMap",
      ], answer=1,
      fix=f"""```ts
{SEARCH_FIX}
```""",
      askedAt=["Walmart", "Publicis Sapient", "Thoughtworks", "Microsoft"]),
]

TS_HEADER = """import { Component, ChangeDetectionStrategy, Input, DestroyRef, inject, signal, input, Injectable } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { FormControl } from '@angular/forms';
import { Observable, Subject, interval, of } from 'rxjs';
import { map, switchMap, debounceTime, distinctUntilChanged, catchError, concatMap, exhaustMap } from 'rxjs/operators';
interface Todo { id: number; title: string; }
interface User { id: string; name: string; }
interface Hit { id: string; }
@Injectable() class UserApi { getUser(id: string): Observable<User> { return of({ id, name: 'x' }); } }
@Injectable() class SearchApi { search(q: string): Observable<Hit[]> { return of([]); } save(f: unknown): Observable<void> { return of(undefined); } pay(id: number): Observable<void> { return of(undefined); } }
interface CartApi { getTotal(): Promise<number>; }
"""

def _indent(s, n=2):
    return "\n".join((" " * n + l) if l else l for l in s.splitlines())

CHECKS = [
    {"name": "ng-var-loop", "lang": "js", "code": VAR_LOOP + "\nsetTimeout(() => console.log('--'), 1);\nsetTimeout(() => {\n" + VAR_FIX + "\n}, 5);",
     "expect": ["3\n3\n3\n--\n0\n1\n2"]},
    {"name": "ng-this", "lang": "js", "code": """class CartComponent {
  total = 0;
  constructor(api) { this.api = api; }
  load() { return this.api.getTotal().then(this.onTotal); }
  load2() { return this.api.getTotal().then(v => this.onTotal(v)); }
  onTotal(value) { this.total = value; }
}
const c = new CartComponent({ getTotal: () => Promise.resolve(42) });
c.load().catch(e => console.log(e.constructor.name + ': ' + e.message)).then(() => c.load2()).then(() => console.log('total', c.total));
""", "expect": ["TypeError: Cannot set properties of undefined (setting 'total')", "total 42"]},
    {"name": "ng-this-ts", "lang": "ts", "code": TS_HEADER + "export class CartComponent {\n  total = 0;\n  constructor(private api: CartApi) {}\n" +
     _indent(THIS_FIX.replace("onTotal = (value: number)", "onTotal2 = (value: number)")) + "\n  onTotal(value: number) { this.total = value; }\n}\n" +
     THIS_PROMPT.replace("CartComponent", "CartComponentBuggy").replace("export class", "class") + "\n", "expect": []},
    {"name": "ng-loop-order", "lang": "js", "code": LOOP_ORDER, "expect": ["A\nD\nF\nC\nE\nB"]},
    {"name": "ng-async-foreach", "lang": "js", "code": """const log = [];
const save = (item) => new Promise((res, rej) => setTimeout(() => { if (item === 'bad') rej(new Error('fail ' + item)); else { log.push('saved ' + item); res(); } }, 10));
""" + ASYNC_FOREACH + "\n" + ASYNC_FIX + """
(async () => {
  await saveAll(['a', 'b']);
  console.log('after saveAll, saved so far:', log.length);
  await new Promise(r => setTimeout(r, 50));
  log.length = 0; await saveAllSequential(['x', 'y']); console.log(log.join(','));
  log.length = 0; await saveAllParallel(['p', 'q']); console.log(log.length);
  console.log('failures', await saveAllSettled(['ok', 'bad', 'bad']));
})();
""", "expect": ["all saved\nafter saveAll, saved so far: 0", "saved x,saved y", "all saved\n2", "failures 2"]},
    {"name": "ng-equality", "lang": "js", "code": "const r = [\n" + ",\n".join(l.split("//")[0].strip() for l in EQ_FIX.splitlines()) + "\n];\nconsole.log(JSON.stringify(r));",
     "expect": ['[true,false,true,false,false,false,"object"]']},
    {"name": "ng-onpush-ts", "lang": "ts", "code": TS_HEADER + ONPUSH_PROMPT.split("// parent component")[0] + """
@Component({ selector: 'app-parent', template: '' })
export class ParentComponent {
  todosArr: Todo[] = [];
  addTodoMutating(title: string) { this.todosArr.push({ id: Date.now(), title }); }
""" + _indent(ONPUSH_FIX.replace("this.todos = [...this.todos", "this.todosArr = [...this.todosArr")) + """
}
@Component({ selector: 'app-todo-list2', template: '' })
export class TodoList2 { todos = input.required<Todo[]>(); }
""", "expect": []},
    {"name": "ng-leak-ts", "lang": "ts", "code": TS_HEADER + """
@Component({ selector: 'app-user', template: '' })
export class UserPage {
  user?: User;
  refreshNotifications() {}
""" + _indent(LEAK_FIX) + """
}
@Component({ selector: 'app-user-old', template: '' })
export class UserPageOld {
  user?: User;
  constructor(private route: ActivatedRoute, private api: UserApi) {}
  refreshNotifications() {}
""" + _indent(LEAK_PROMPT) + """
}
""", "expect": []},
    {"name": "ng-search-ts", "lang": "ts", "code": TS_HEADER + """
@Component({ selector: 'app-search', template: '' })
export class SearchBox {
  api = inject(SearchApi);
  searchCtrl = new FormControl<string | null>('');
  orderId = 7;
  saveClicks$ = new Subject<unknown>();
  payClicks$ = new Subject<void>();
  init() {
""" + _indent(SEARCH_FIX.replace("results$ = ", "const results$: Observable<Hit[]> = ").replace("saveClicks$.pipe", "this.saveClicks$.pipe").replace("payClicks$.pipe", "this.payClicks$.pipe"), 4) + """
    return results$;
  }
}
""", "expect": []},
    {"name": "ng-switch-vs-merge", "lang": "js", "code": f"""const {{ Subject, timer, of }} = require('{RX}');
const {{ switchMap, mergeMap, concatMap, exhaustMap, map }} = require('{RX}/operators');
const delays = {{ ja: 50, java: 10 }};
const api = q => timer(delays[q]).pipe(map(() => 'results:' + q));
for (const [name, op] of [['mergeMap', mergeMap], ['switchMap', switchMap]]) {{
  const s = new Subject(); const seen = [];
  s.pipe(op(api)).subscribe(v => seen.push(v));
  s.next('ja'); setTimeout(() => s.next('java'), 5);
  setTimeout(() => console.log(name, 'last shown =', seen[seen.length - 1]), 100);
}}
const clicks = new Subject(); let pays = 0;
clicks.pipe(exhaustMap(() => timer(30).pipe(map(() => ++pays)))).subscribe();
clicks.next(); clicks.next(); clicks.next();
setTimeout(() => console.log('exhaustMap pays =', pays), 100);
const saves = new Subject(); const order = [];
saves.pipe(concatMap(x => timer(x === 1 ? 30 : 5).pipe(map(() => x)))).subscribe(x => order.push(x));
saves.next(1); saves.next(2); saves.next(3);
setTimeout(() => console.log('concatMap order =', order.join(',')), 150);
""", "expect": ["mergeMap last shown = results:ja", "switchMap last shown = results:java", "exhaustMap pays = 1", "concatMap order = 1,2,3"]},
]
