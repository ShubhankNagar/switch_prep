from cs_common import build, B, I, A

notes = [
("Angular Architecture: The Big Picture", r"""
Angular is a **full framework** (not just a view library like React). Out of the box you get a component model, dependency injection, a router, forms, an HTTP client, a CLI and a testing setup. Interviewers usually open with "explain Angular architecture", so have a crisp 60-second answer ready.

### Building blocks

| Block | What it is | Example |
|---|---|---|
| **Component** | Class + template + styles; owns a piece of UI | `ProductCardComponent` |
| **Template** | HTML with Angular syntax (bindings, control flow) | `@for (p of products(); track p.id)` |
| **Directive** | Adds behaviour to existing elements | `[appHighlight]`, `ngClass` |
| **Pipe** | Pure transformation for display | `{{ price \| currency:'INR' }}` |
| **Service** | Plain class for logic/data, shared via DI | `CartService` |
| **Injector / DI** | Creates and hands out instances | `inject(HttpClient)` |
| **Router** | Maps URL to component tree | `{ path: 'orders', component: OrdersPage }` |
| **NgModule** (legacy) | Grouping/compilation context | `AppModule` (pre-v15 style) |

Since Angular 14 components can be **standalone**, and since v19 standalone is the default; NgModules are now optional and mostly seen in older codebases (like the ones at service companies). Be ready to talk about both.

### How an app boots

```ts
// main.ts (modern)
bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideZonelessChangeDetection() // optional, default in new v21+ apps
  ]
});
```

1. `main.ts` bootstraps the root component.
2. Angular creates the **root environment injector** with the providers.
3. The root component is rendered into `<app-root>` in `index.html`.
4. The router reads the URL and renders routed components into `<router-outlet>`.

### Data flow

- **Parent → child:** `@Input()` / `input()` signal.
- **Child → parent:** `@Output()` / `output()` emitting events.
- **Siblings / far components:** a shared service (holding a signal or a `BehaviorSubject`) or a store (NgRx).

### Compilation

Angular uses **AOT (Ahead-of-Time)** compilation by default: templates are compiled to JavaScript instructions at build time by the **Ivy** compiler. Benefits: faster startup, template errors caught at build time, smaller bundles thanks to tree-shaking. JIT (compile in the browser) is now only used in some tests.

The build system since v17 uses **esbuild + Vite** (`@angular/build:application`) instead of webpack, giving much faster builds.

### Rendering modes

- **CSR** – classic SPA.
- **SSR** – server renders HTML (`@angular/ssr`), then the client **hydrates** it (non-destructive hydration since v16, incremental hydration with `@defer` since v19).
- **SSG / prerendering** – HTML generated at build time.

### Interview tip

Tie your answer to your project: "In my current project we have an Angular 15 app with feature modules lazy-loaded per business area, a core module with interceptors for JWT, and shared services talking to Spring Boot REST APIs. I have been migrating new screens to standalone components and signals." That shows you know both the legacy and the modern way, which is exactly what product companies look for.
"""),

("Components, Templates & Lifecycle Hooks", r"""
A component = **TypeScript class + template + styles + metadata** in `@Component`.

```ts
@Component({
  selector: 'app-user-card',
  standalone: true,               // default since v19, can be omitted
  imports: [DatePipe, RouterLink],
  template: `
    <h3>{{ user().name }}</h3>
    <p>Joined {{ user().joined | date }}</p>
    <button (click)="select.emit(user().id)">Select</button>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserCardComponent {
  user = input.required<User>();   // signal input
  select = output<number>();       // replaces @Output + EventEmitter
}
```

### Binding types
- Interpolation `{{ expr }}`
- Property binding `[disabled]="isBusy"`
- Event binding `(click)="save()"`
- Two-way binding `[(ngModel)]="name"` or with `model()` signals: `[(value)]="name"` (banana-in-a-box = property + event `valueChange`).
- Attribute/class/style: `[attr.aria-label]`, `[class.active]="isActive"`, `[style.width.px]="w"`.

### Built-in control flow (v17+)
```html
@if (user(); as u) { <p>{{ u.name }}</p> } @else { <p>Loading…</p> }
@for (item of items(); track item.id) { <li>{{ item.name }}</li> } @empty { <li>No items</li> }
@switch (status) { @case ('A') { Active } @default { Unknown } }
```
`track` is mandatory in `@for` — it replaces `trackBy`.

### Content projection
`<ng-content>` lets a parent pass markup into a child (like slots). Multi-slot: `<ng-content select="[header]">`. Access projected children with `@ContentChild`/`contentChild()`; access own template elements with `@ViewChild`/`viewChild()`.

### Lifecycle hooks (in order)

| Hook | When | Typical use |
|---|---|---|
| `constructor` | Class instantiated | Only DI; no input values yet |
| `ngOnChanges(changes)` | Before init and whenever an `@Input` reference changes | React to input changes |
| `ngOnInit` | Once, after first `ngOnChanges` | Fetch data, set up subscriptions |
| `ngDoCheck` | Every change detection run | Custom change detection (rare, expensive) |
| `ngAfterContentInit` | Once, after projected content initialised | Use `@ContentChild` |
| `ngAfterContentChecked` | After every check of projected content | |
| `ngAfterViewInit` | Once, after component view + child views ready | Use `@ViewChild`, DOM libs |
| `ngAfterViewChecked` | After every check of the view | |
| `ngOnDestroy` | Just before destroy | Unsubscribe, clear timers |

Newer APIs: `afterNextRender()` and `afterRender()`/`afterEveryRender()` run code after the DOM is painted (safe for SSR because they only run in the browser). `DestroyRef.onDestroy()` can replace `ngOnDestroy`.

### Classic gotchas
- **`ngOnChanges` only fires on reference change.** Mutating an array (`arr.push`) does not trigger it.
- **`ExpressionChangedAfterItHasBeenCheckedError`** – you changed a bound value inside `ngAfterViewInit` (dev-mode double check catches it). Fix by moving logic earlier, using signals, or deferring.
- **Constructor vs ngOnInit** – inputs are not set in the constructor; put initialisation that needs inputs in `ngOnInit`.

### Smart vs dumb components
*Container (smart)* components inject services and fetch data; *presentational (dumb)* components only take inputs and emit outputs and use OnPush. This split makes testing and reuse easy and is a common design question.
"""),

("Change Detection: Default, OnPush, Zone.js and Zoneless", r"""
Change detection (CD) is how Angular keeps the DOM in sync with component state. It is the #1 "advanced Angular" topic in product-company interviews.

### Default strategy
Angular represents the app as a **tree of component views**. When something *might* have changed, it walks the tree **top-down** and compares each template binding's current value with the previous one. If different, it updates the DOM. With the `Default` strategy **every component is checked on every CD cycle**.

### Who triggers CD? Zone.js
**Zone.js** monkey-patches async browser APIs (`setTimeout`, `addEventListener`, `Promise`, XHR/fetch). Angular runs the app inside `NgZone`; when any async task finishes, the zone notifies Angular and it calls `ApplicationRef.tick()` → CD from the root.

Downsides: ~30 KB extra, CD runs even when nothing changed (e.g. a `mousemove` listener), harder stack traces, does not understand native `async/await` (Angular down-levels it).

`ngZone.runOutsideAngular(() => ...)` lets you run noisy code (scroll listeners, animations) without triggering CD.

### OnPush
```ts
@Component({ changeDetection: ChangeDetectionStrategy.OnPush, ... })
```
An OnPush component (and its subtree) is checked **only when** it is marked dirty, which happens when:
1. An `@Input` **reference** changes (not mutation).
2. An event handler bound in its template (or child) fires.
3. The `async` pipe receives a new value.
4. A **signal** read in its template changes.
5. You call `cdr.markForCheck()` manually.

Because of rule 1 you must treat inputs as **immutable**:
```ts
this.items = [...this.items, newItem];   // works with OnPush
this.items.push(newItem);                // view will NOT update
```

`ChangeDetectorRef` methods:
- `markForCheck()` – marks this component and ancestors dirty for the next cycle.
- `detectChanges()` – runs CD synchronously for this component and children now.
- `detach()/reattach()` – take a subtree out of automatic CD.

### Signals and fine-grained CD
When a signal read in a template changes, Angular marks that specific view (and since v17, only its ancestors as "has dirty child") so that OnPush ancestors are traversed but not re-checked — "local change detection". This is far cheaper than a full tree check.

### Zoneless (stable in v20.2, default for new apps from v21)
```ts
bootstrapApplication(App, { providers: [provideZonelessChangeDetection()] });
```
and remove `zone.js` from polyfills. Without Zone.js, Angular schedules CD only when it is *told* something changed:
- a signal used in a template is updated,
- `markForCheck()` (the `async` pipe calls it),
- a template event listener fires,
- an input is set via `setInput`, a view is attached, etc.

So code like `setTimeout(() => this.count++)` with a plain field **won't update the UI** in zoneless mode — use a signal (`this.count.update(c => c + 1)`). Benefits: smaller bundle, better performance, cleaner stack traces, works with native async/await.

### How to answer "how would you optimise CD?"
1. Use `OnPush` everywhere (or make it default in schematics).
2. Prefer signals / `async` pipe over manual subscriptions.
3. Immutable updates.
4. `track` in `@for`.
5. Avoid function calls and heavy getters in templates — use pure pipes or `computed()`.
6. `runOutsideAngular` for high-frequency events.
7. Move toward zoneless.
"""),

("Signals: signal, computed, effect, linkedSignal, resource", r"""
Signals (developer preview v16, core APIs stable v17–v20) are Angular's new **reactive primitive**: a wrapper around a value that notifies consumers when it changes.

```ts
import { signal, computed, effect } from '@angular/core';

count = signal(0);                       // WritableSignal<number>
double = computed(() => this.count() * 2); // read-only, memoised, lazy

increment() {
  this.count.set(this.count() + 1);   // replace
  this.count.update(c => c + 1);      // derive from previous
}

constructor() {
  effect(() => console.log('count is', this.count())); // side effect
}
```
Read a signal by **calling it**: `count()`. In templates: `{{ double() }}`.

### Key properties
- **Synchronous & glitch-free** – reading always gives the latest value.
- **computed** is lazy and cached: recalculates only when a dependency changed *and* someone reads it. Dependencies are tracked **dynamically** (only signals actually read in the last run).
- **effect** runs at least once and re-runs when any signal it read changes. Use it for logging, syncing to `localStorage`, imperative DOM/3rd-party APIs — **not** for propagating state to other signals (use `computed` or `linkedSignal`). Effects need an injection context (constructor/field initialiser) or an explicit `injector`.
- Signals compare by `Object.is` by default; pass `{ equal: fn }` for custom equality. Mutating an object inside a signal will not notify — always set a new reference.
- `untracked(() => sig())` reads without creating a dependency.

### Component APIs built on signals
```ts
name = input<string>('');           // signal input
id = input.required<number>();
changed = output<string>();          // not a signal, but the modern output
value = model(0);                    // two-way bindable signal
panel = viewChild<ElementRef>('panel');
items = contentChildren(ItemDirective);
```

### linkedSignal (stable v20)
A writable signal that **resets** whenever a source changes — perfect for "selected item defaults to first item, but the user can change it":
```ts
selected = linkedSignal(() => this.options()[0]);
```

### resource / httpResource (experimental in v19–v21)
Async data as signals:
```ts
userId = input.required<number>();
user = httpResource<User>(() => `/api/users/${this.userId()}`);
// template: @if (user.isLoading()) {…} {{ user.value()?.name }}
```
It re-fetches automatically when `userId` changes and exposes `value`, `status`, `error`, `isLoading`.

### Interop with RxJS (`@angular/core/rxjs-interop`)
```ts
users = toSignal(this.http.get<User[]>('/api/users'), { initialValue: [] });
query$ = toObservable(this.query);  // signal -> observable
this.source$.pipe(takeUntilDestroyed()).subscribe(...);
```

### Signals vs RxJS — when to use which?
| Signals | RxJS |
|---|---|
| Synchronous **state** (current value) | **Events / streams over time** |
| Simple, no subscribe/unsubscribe | Rich operators: debounce, retry, switchMap |
| Fine-grained CD, zoneless-friendly | Cancellation, race conditions, websockets |

A good answer: "State in signals, async event orchestration in RxJS, bridged with `toSignal`/`toObservable`." E.g. a search box: `toObservable(query).pipe(debounceTime(300), switchMap(q => api.search(q)))` then `toSignal` the result.
"""),

("Standalone Components & Modern Angular Syntax", r"""
### What and why
A **standalone component** declares its own dependencies in `imports` instead of belonging to an `NgModule`. Introduced in v14, stable in v15, **default since v19** (`standalone: true` is implied; for the old style you write `standalone: false`).

```ts
@Component({
  selector: 'app-orders',
  imports: [CommonModule, OrderRowComponent, CurrencyPipe, RouterLink],
  templateUrl: './orders.component.html'
})
export class OrdersComponent {}
```

Benefits:
- Less boilerplate, easier mental model (each file says what it uses).
- Better tree-shaking and **lazy loading per component** (`loadComponent`).
- Simpler testing (`TestBed.configureTestingModule({ imports: [OrdersComponent] })`).

### NgModule recap (legacy, still asked)
```ts
@NgModule({
  declarations: [AppComponent, HeaderComponent], // components/directives/pipes owned
  imports: [BrowserModule, HttpClientModule, SharedModule],
  providers: [AuthService],
  exports: [HeaderComponent],
  bootstrap: [AppComponent]
})
export class AppModule {}
```
Common patterns: **CoreModule** (singletons, interceptors, imported once), **SharedModule** (reusable dumb components/pipes), **Feature modules** (lazy-loaded). `forRoot()/forChild()` pattern ensures singleton providers (e.g. `RouterModule.forRoot(routes)`).

### Bootstrapping standalone
```ts
bootstrapApplication(AppComponent, appConfig);

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideAnimationsAsync(),
  ]
};
```
`provide*` functions replace `XModule.forRoot()`. To reuse an old module's providers: `importProvidersFrom(SomeModule)`.

### Migrating an existing app
Angular CLI provides schematics:
```bash
ng generate @angular/core:standalone       # convert declarations, remove modules, switch bootstrap
ng generate @angular/core:control-flow     # *ngIf/*ngFor -> @if/@for
ng generate @angular/core:signal-input-migration
ng generate @angular/core:inject           # constructor DI -> inject()
```
Migration can be incremental: standalone components can be imported into NgModules and vice versa.

### Other modern syntax to know
- `inject()` function instead of constructor injection: `private http = inject(HttpClient);`
- Functional guards/resolvers/interceptors (plain functions instead of classes).
- `@if / @for / @switch / @defer` built-in control flow (v17).
- `@let` template variables (v18.1): `@let total = price() * qty();`
- Host bindings in the `host` property instead of `@HostBinding/@HostListener` (recommended by the style guide).
- Directive composition API: `hostDirectives: [CdkDrag]`.
- Self-closing tags: `<app-spinner />`.

### Interview angle
Product companies (Zoho, Freshworks, Razorpay etc.) often have modern Angular codebases or are migrating. Saying "I know how to migrate from modules to standalone and from `*ngFor` to `@for` with schematics, and I understand why — tree-shaking, lazy loading, simpler DI" signals that you keep up with the ecosystem even though your current project is older.
"""),

("Dependency Injection & Providers", r"""
**Dependency Injection (DI)** is a design pattern where a class asks for its dependencies instead of creating them. Angular's DI system creates instances, caches them in **injectors**, and supplies them on request.

```ts
@Injectable({ providedIn: 'root' })   // app-wide singleton, tree-shakable
export class CartService { items = signal<Item[]>([]); }

export class CartComponent {
  private cart = inject(CartService);   // or constructor(private cart: CartService)
}
```

### Injector hierarchy
1. **Environment injectors**
   - *Platform* injector (`providedIn: 'platform'`).
   - *Root* injector – `providedIn: 'root'` and `bootstrapApplication` providers.
   - *Route* injectors – `providers` on a lazy route create a child environment injector.
2. **Element (node) injectors** – created for each component/directive that has `providers` or `viewProviders`.

Resolution: Angular first walks **up the element injector tree** (component → parent → … ), then the **environment injector** chain. If nothing is found → `NullInjectorError: No provider for X`.

Providing a service in a component's `providers` gives **each instance of that component its own instance** of the service (useful for per-widget state, e.g. a form wizard).

### Provider recipes
```ts
providers: [
  CartService,                                          // shorthand for useClass
  { provide: Logger, useClass: ConsoleLogger },          // swap implementation
  { provide: API_URL, useValue: 'https://api.x.com' },   // constant
  { provide: Storage, useFactory: () => isBrowser() ? localStorage : memStorage },
  { provide: OldLogger, useExisting: Logger },           // alias, same instance
  { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true } // multi provider
]
```

### InjectionToken
For non-class dependencies (strings, config objects, functions):
```ts
export const API_URL = new InjectionToken<string>('API_URL');
private url = inject(API_URL);
```

### Resolution modifiers
- `@Optional()` / `inject(X, { optional: true })` – returns `null` instead of throwing.
- `@Self()` / `{ self: true }` – only look in this element's injector.
- `@SkipSelf()` / `{ skipSelf: true }` – start from the parent (used for "this module must be imported only once" guards).
- `@Host()` / `{ host: true }` – stop at the host component.

### providedIn: 'root' vs module providers
`providedIn: 'root'` is **tree-shakable**: if no one injects it, it is removed from the bundle. Listing a service in a lazy-loaded module's `providers` creates a **separate instance** for that lazy module — a classic bug where "my singleton has two instances".

### `inject()` function rules
Can only be called in an **injection context**: constructor, field initialisers, factory functions, functional guards/interceptors, or inside `runInInjectionContext(injector, fn)`. Calling it in `ngOnInit` or a click handler throws `NG0203`.

### viewProviders vs providers
`viewProviders` are visible to the component's own view children but **not** to content projected via `<ng-content>`.

### Interview analogy
If you come from Spring: `@Injectable({providedIn:'root'})` ≈ a singleton `@Service` bean; component-level providers ≈ prototype/request-scoped beans; `InjectionToken` ≈ `@Qualifier`/`@Value`. Interviewers like this bridge from a full-stack Java developer.
"""),

("RxJS Essentials: Observables, Operators, Subjects", r"""
**RxJS** is a library for composing async and event-based programs using **Observables**. Angular uses it in `HttpClient`, router events, reactive forms (`valueChanges`) and more.

### Observable vs Promise
| Observable | Promise |
|---|---|
| Lazy – nothing happens until `subscribe()` | Eager – starts immediately |
| 0..N values over time | Exactly one value |
| Cancellable (`unsubscribe`) | Not cancellable |
| Rich operators | `then/catch` only |
| Can be sync or async | Always async (microtask) |

**Cold** observable: each subscriber triggers its own execution (`http.get` – two subscribes = two HTTP calls). **Hot**: one shared source (DOM events, Subjects). Make cold → hot with `share()` / `shareReplay({ bufferSize: 1, refCount: true })`.

### Most-asked operators
- Transform: `map`, `pluck` (deprecated), `scan` (running total).
- Filter: `filter`, `take(n)`, `first`, `distinctUntilChanged`, `debounceTime`, `throttleTime`.
- Combine: `combineLatest` (latest from each, emits when any emits after all have emitted), `forkJoin` (wait for all to **complete**, like `Promise.all`), `merge`, `concat`, `withLatestFrom`, `zip`.
- Errors: `catchError`, `retry({ count: 3, delay: 1000 })`.
- Side effects: `tap`, `finalize`.

### Higher-order mapping operators (very frequently asked)
All map each outer value to an inner observable; they differ in **what happens when a new outer value arrives while an inner one is still running**:

| Operator | Behaviour | Use case |
|---|---|---|
| `switchMap` | **Cancels** previous inner, switches to new | Type-ahead search, route param → load data |
| `mergeMap` | Runs all inners **in parallel** | Delete many items, fire-and-forget |
| `concatMap` | **Queues**, runs one after another in order | Sequential saves where order matters |
| `exhaustMap` | **Ignores** new outer values while inner is active | Login/submit button double-click protection |

```ts
this.search.valueChanges.pipe(
  debounceTime(300),
  distinctUntilChanged(),
  filter(q => q.length > 2),
  switchMap(q => this.api.search(q).pipe(catchError(() => of([]))))
).subscribe(r => this.results.set(r));
```
Note: `catchError` inside the inner pipe keeps the outer stream alive after an error.

### Subjects
A Subject is both observable and observer (multicast).
- `Subject` – no initial value; late subscribers miss past values. Good for events.
- `BehaviorSubject(init)` – holds **current value**; new subscribers get it immediately; `.value` sync getter. Classic for service state.
- `ReplaySubject(n)` – replays last n values to new subscribers.
- `AsyncSubject` – emits only the last value on completion.

```ts
private user$ = new BehaviorSubject<User | null>(null);
readonly currentUser$ = this.user$.asObservable(); // expose read-only
```

### Unsubscribe strategies (memory leaks)
1. **`async` pipe** in template – auto subscribe/unsubscribe (best).
2. **`toSignal()`** – auto-unsubscribes on destroy.
3. **`takeUntilDestroyed()`** (v16+): `obs$.pipe(takeUntilDestroyed(this.destroyRef))`.
4. Classic `takeUntil(this.destroy$)` with `destroy$.next(); destroy$.complete()` in `ngOnDestroy` (place `takeUntil` **last** in the pipe).
5. Store `Subscription` and call `unsubscribe()` in `ngOnDestroy`.
6. `take(1)`/`first()` for one-shot streams.

You do **not** need to unsubscribe from `HttpClient` calls (they complete after one response), but cancelling is still useful to abort in-flight requests on navigation.
"""),

("Routing, Guards, Resolvers & Lazy Loading", r"""
### Basic routing
```ts
export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', component: HomeComponent },
  { path: 'products/:id', component: ProductDetailComponent, title: 'Product' },
  { path: 'admin', canActivate: [authGuard], loadChildren: () => import('./admin/admin.routes').then(m => m.ADMIN_ROUTES) },
  { path: 'reports', loadComponent: () => import('./reports.component').then(m => m.ReportsComponent) },
  { path: '**', component: NotFoundComponent }   // wildcard must be last
];
```
Order matters: the router uses **first-match-wins**. `pathMatch: 'full'` is required for empty-path redirects.

Template: `<a routerLink="/products/42" routerLinkActive="active">`, `<router-outlet />`. Programmatic: `router.navigate(['/products', id], { queryParams: { tab: 'reviews' } })`.

### Reading params
```ts
private route = inject(ActivatedRoute);
id$ = this.route.paramMap.pipe(map(p => Number(p.get('id'))));
// or with withComponentInputBinding(): id = input<string>(); // bound from :id
```
`snapshot.paramMap` gives a one-time value — but if the same component is reused for `/products/1` → `/products/2`, the snapshot won't update. Use the observable or input binding.

### Guards (functional style, v15+)
```ts
export const authGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.isLoggedIn() ? true : router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};
```
| Guard | Purpose |
|---|---|
| `canActivate` | Can enter this route? |
| `canActivateChild` | Can enter child routes? |
| `canDeactivate` | Can leave? ("unsaved changes" prompt) |
| `canMatch` | Should this route even match? (replaces `canLoad`; also prevents lazy chunk download; can pick between routes for same path, e.g. admin vs user dashboard) |
| `resolve` | Pre-fetch data before activation |

Guards can return `boolean`, `UrlTree` (redirect), `Observable` or `Promise` of those. Returning a `UrlTree` is preferred over calling `router.navigate` inside the guard. Remember: guards are a **UX** feature — real security must be enforced by the backend (your Spring Security).

### Resolver
```ts
export const productResolver: ResolveFn<Product> = route =>
  inject(ProductService).getById(+route.paramMap.get('id')!);
// route: { path: 'products/:id', resolve: { product: productResolver } }
```
Trade-off: page waits for data (no skeleton). Many teams prefer loading inside the component with a loader.

### Lazy loading
Splits the app into chunks downloaded on demand → smaller initial bundle, faster first load.
- `loadChildren` for a set of routes (or a legacy NgModule).
- `loadComponent` for a single standalone component.

**Preloading strategies**: `withPreloading(PreloadAllModules)` downloads lazy chunks in the background after app load; you can write a custom strategy (preload only routes with `data: { preload: true }`), or use quicklink-style libraries.

### Other router features
- Child routes and nested `<router-outlet>`; named/auxiliary outlets.
- `RouteReuseStrategy` to cache component state (e.g. keep a list page when going back).
- Router events (`NavigationStart`, `NavigationEnd`) for loaders/analytics.
- `HashLocationStrategy` (`/#/path`) vs default `PathLocationStrategy` (needs server fallback to `index.html` — e.g. Spring Boot forwarding unknown routes).
- View Transitions: `withViewTransitions()`.
"""),

("Forms: Reactive vs Template-Driven", r"""
Angular has two (and now an experimental third) form approaches.

### Template-driven forms
Logic lives in the template, uses `FormsModule` and `ngModel`.
```html
<form #f="ngForm" (ngSubmit)="save(f.value)">
  <input name="email" [(ngModel)]="user.email" required email #email="ngModel" />
  @if (email.invalid && email.touched) { <small>Invalid email</small> }
  <button [disabled]="f.invalid">Save</button>
</form>
```
Good for simple forms; asynchronous (model is created by directives), harder to unit test and to make dynamic.

### Reactive forms
Model defined in the class with `ReactiveFormsModule`; template just binds to it. **Synchronous, explicit, immutable-ish, testable** — the default choice for enterprise apps.
```ts
private fb = inject(NonNullableFormBuilder);
form = this.fb.group({
  name: ['', [Validators.required, Validators.minLength(3)]],
  email: ['', [Validators.required, Validators.email], [this.emailTakenValidator()]],
  address: this.fb.group({ city: [''], pin: ['', Validators.pattern(/^\d{6}$/)] }),
  phones: this.fb.array([this.fb.control('')])
});
```
```html
<form [formGroup]="form" (ngSubmit)="submit()">
  <input formControlName="name" />
  <div formGroupName="address"><input formControlName="pin" /></div>
  <div formArrayName="phones">
    @for (c of form.controls.phones.controls; track $index) { <input [formControlName]="$index" /> }
  </div>
</form>
```
Since v14 forms are **strictly typed**: `form.value.name` is `string | undefined` (`getRawValue()` gives full type incl. disabled controls). `NonNullableFormBuilder` makes `reset()` go back to initial values instead of `null`.

### Building blocks
- `FormControl` – single value; `FormGroup` – object of controls; `FormArray` – dynamic list; `FormRecord` – dynamic keys.
- State: `valid/invalid`, `pristine/dirty`, `touched/untouched`, `pending` (async validators running), `disabled`.
- `valueChanges` / `statusChanges` observables; v18 added unified `events` observable.
- `setValue` (must provide all fields) vs `patchValue` (partial).
- `updateOn: 'blur' | 'submit'` to reduce validation frequency.

### Custom validators
```ts
export function noSpaces(): ValidatorFn {
  return (c: AbstractControl): ValidationErrors | null =>
    /\s/.test(c.value ?? '') ? { noSpaces: true } : null;
}
// Cross-field validator on the group:
export const passwordMatch: ValidatorFn = g =>
  g.get('pwd')?.value === g.get('confirm')?.value ? null : { mismatch: true };
```
Async validator returns `Observable<ValidationErrors | null>` — combine with `timer(400).pipe(switchMap(...))` to debounce server checks (e.g. "username taken" via a Spring Boot endpoint).

### ControlValueAccessor
To make a custom component (star-rating, date picker) work with `formControlName`/`ngModel`, implement `ControlValueAccessor` (`writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`) and register it with `NG_VALUE_ACCESSOR` (`multi: true`). Frequently asked for SDE-2.

### Signal Forms (experimental, v21)
A new `@angular/forms/signals` API builds a form from a signal model: `form(signal({...}), schema => { required(schema.email) })` and binds with `[field]`/`[control]`. Mention it as awareness; reactive forms remain the production standard.

### Which to choose?
Reactive for anything non-trivial: dynamic fields, complex validation, unit tests, reacting to value changes with RxJS. Template-driven for tiny forms like a newsletter signup.
"""),

("HttpClient & Interceptors", r"""
### HttpClient basics
```ts
// app.config.ts
provideHttpClient(withInterceptors([authInterceptor, errorInterceptor]), withFetch())

@Injectable({ providedIn: 'root' })
export class OrderApi {
  private http = inject(HttpClient);
  list(page = 0) {
    const params = new HttpParams().set('page', page).set('size', 20);
    return this.http.get<Page<Order>>('/api/orders', { params });
  }
  create(o: NewOrder) { return this.http.post<Order>('/api/orders', o); }
}
```
- Returns **cold observables** – no request until subscribed; every subscribe = new request.
- Automatically parses JSON; `observe: 'response'` gives full `HttpResponse` (headers/status); `reportProgress` for upload progress.
- `withFetch()` uses the Fetch API (recommended with SSR).
- Old style: `HttpClientModule` (deprecated in v18 in favour of `provideHttpClient`).

### Interceptors
Interceptors sit between your code and the backend; every request/response passes through the chain. Requests are **immutable**, so you `clone()` them.

**Functional interceptor (modern):**
```ts
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).token();
  const authReq = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
  return next(authReq);
};

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  return next(req).pipe(
    retry({ count: 2, delay: 500, resetOnSuccess: true }),
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) router.navigate(['/login']);
      return throwError(() => err);
    })
  );
};
```
**Class-based interceptor (legacy):** implement `HttpInterceptor.intercept(req, next: HttpHandler)` and register with `{ provide: HTTP_INTERCEPTORS, useClass: X, multi: true }`; in standalone apps enable via `withInterceptorsFromDi()`.

Order: interceptors run in the order provided for requests and **reverse order** for responses.

### Common interceptor use cases
1. Attach JWT / auth headers.
2. Global error handling and toast messages.
3. Loading spinner (increment counter on request, decrement in `finalize`).
4. **Refresh token flow** – on 401, call refresh once (share it with `shareReplay`/a flag + `BehaviorSubject` queue), then retry original requests with the new token.
5. Caching GET responses (`Map<url, HttpResponse>` with `of(cached)`).
6. Logging/timing, adding correlation IDs (pairs well with Spring Boot MDC tracing).
7. Base URL prefixing.

### Passing metadata to interceptors
`HttpContextToken` lets a call opt out: `this.http.get(url, { context: new HttpContext().set(SKIP_AUTH, true) })`.

### Error handling layers
- Per-call `catchError` for screen-specific handling.
- Interceptor for cross-cutting handling.
- `ErrorHandler` provider for uncaught app errors (send to Sentry).

### Testing HTTP
`provideHttpClientTesting()` + `HttpTestingController`:
```ts
const req = httpMock.expectOne('/api/orders?page=0&size=20');
expect(req.request.method).toBe('GET');
req.flush(mockPage);
httpMock.verify();
```

### CORS reminder
If the browser blocks calls to your Spring Boot API, that is CORS — fixed on the **server** (`@CrossOrigin` / `CorsConfigurationSource`) or by using the Angular dev-server proxy (`proxy.conf.json`) locally. Interceptors cannot fix CORS.
"""),

("Performance Optimisation in Angular", r"""
A favourite SDE-2 question: "Your Angular app is slow — how do you diagnose and fix it?" Structure the answer as **load-time** vs **runtime** performance, and always mention **measuring first** (Chrome DevTools Performance tab, Lighthouse, Angular DevTools profiler, `ng build --stats-json` + bundle analyser / `source-map-explorer`).

### 1. Load-time (bundle size, first paint)
- **Lazy-load routes** (`loadChildren`, `loadComponent`) and use a preloading strategy.
- **`@defer` blocks** (v17) to lazy-load heavy parts of a template:
```html
@defer (on viewport; prefetch on idle) {
  <app-sales-chart [data]="data()" />
} @placeholder (minimum 300ms) {
  <div class="skeleton"></div>
} @loading (after 100ms) {
  <app-spinner />
} @error {
  <p>Could not load chart</p>
}
```
Triggers: `on idle` (default), `on viewport`, `on interaction`, `on hover`, `on immediate`, `on timer(2s)`, `when condition`. Dependencies inside must be standalone and not referenced elsewhere eagerly to be split into a separate chunk.
- AOT + production build (default), **tree-shakable providers** (`providedIn: 'root'`), avoid importing whole libraries (`lodash-es` per-function, `date-fns` instead of moment).
- Budgets in `angular.json` to fail builds when bundles grow.
- `NgOptimizedImage` (`<img ngSrc="..." width height priority>`) – lazy loading, `fetchpriority`, srcset, LCP warnings.
- SSR + hydration (incremental hydration with `@defer (hydrate on viewport)`) for faster LCP and SEO.
- Gzip/Brotli compression and HTTP caching (hashed file names) on the server/CDN.

### 2. Runtime (change detection & rendering)
- **OnPush** everywhere + immutable data.
- **Signals** and `computed()` instead of getters; moving toward **zoneless**.
- **`track` in `@for`** (or `trackBy` with `*ngFor`) so Angular reuses DOM nodes instead of recreating the whole list when the array reference changes:
```ts
// legacy
trackById(index: number, item: Order) { return item.id; }
// <tr *ngFor="let o of orders; trackBy: trackById">
```
- **Pure pipes** instead of method calls in templates (`{{ total(items) }}` runs on every CD cycle; a pure pipe runs only when input reference changes).
- **Virtual scrolling** for long lists: `<cdk-virtual-scroll-viewport itemSize="48">` with `*cdkVirtualFor` renders only visible rows.
- Pagination / infinite scroll on the API (Spring Data `Pageable`).
- `runOutsideAngular` for scroll/mousemove/websocket ticks; debounce/throttle user input.
- Avoid memory leaks: unsubscribe, remove manual event listeners, clear intervals.
- Web Workers for CPU-heavy work (`ng generate web-worker`).

### 3. Network
- Cache GET responses (interceptor or `shareReplay`), cancel stale requests with `switchMap`, batch calls with `forkJoin`, avoid N+1 API calls from the UI.

### Sample answer
"First I'd profile. In my project the orders grid with 2,000 rows was janky; Angular DevTools showed CD taking 120 ms per keystroke. I moved the grid to OnPush, added `trackBy`, replaced a template method computing totals with a pure pipe, and switched to server-side pagination. Typing latency dropped below 16 ms and the initial bundle fell 35% after lazy-loading the reports module." Quantify, even approximately — product interviewers love numbers.
"""),

("State Management: Services, NgRx and Signal Store", r"""
"How do you manage state?" has three levels of answers. Pick based on app complexity and say so.

### Level 1 — Service with signals (or BehaviorSubject)
```ts
@Injectable({ providedIn: 'root' })
export class CartStore {
  private readonly _items = signal<CartItem[]>([]);
  readonly items = this._items.asReadonly();
  readonly total = computed(() => this._items().reduce((s, i) => s + i.price * i.qty, 0));

  add(item: CartItem) { this._items.update(list => [...list, item]); }
  remove(id: number) { this._items.update(list => list.filter(i => i.id !== id)); }
}
```
Older equivalent: private `BehaviorSubject`, public `asObservable()`, update with `next()`. This is enough for most small/medium apps and is what you'll write in many interviews.

### Level 2 — NgRx Store (Redux pattern)
Single immutable state tree, changed only through **actions** processed by pure **reducers**.

```
Component --dispatch(action)--> Reducer --new state--> Store --select()--> Component
                     \--> Effect --API call--> dispatch(success/failure action)
```
```ts
export const loadOrders = createAction('[Orders Page] Load');
export const loadOrdersSuccess = createAction('[Orders API] Load Success', props<{ orders: Order[] }>());

export const ordersReducer = createReducer(initialState,
  on(loadOrders, s => ({ ...s, loading: true })),
  on(loadOrdersSuccess, (s, { orders }) => ({ ...s, loading: false, orders }))
);

export const selectOrders = createSelector(selectOrdersState, s => s.orders); // memoised

loadOrders$ = createEffect(() => this.actions$.pipe(
  ofType(loadOrders),
  switchMap(() => this.api.list().pipe(
    map(orders => loadOrdersSuccess({ orders })),
    catchError(e => of(loadOrdersFailure({ error: e.message })))
  ))
));
```
Pieces: **Store, Actions, Reducers, Selectors, Effects**, plus `@ngrx/entity` (normalised collections), Router Store, **Store DevTools** (time-travel debugging). Modern helpers: `createFeature`, `createActionGroup`, `store.selectSignal(selector)`.

**Pros:** predictable, traceable, great for large teams and complex cross-feature state, devtools. **Cons:** boilerplate, learning curve, overkill for simple CRUD.

### Level 3 — NgRx Signal Store / ComponentStore
`@ngrx/signals` provides `signalStore(withState(), withComputed(), withMethods(), withHooks())` — lightweight, signal-based, can be global or per-component. `ComponentStore` is the older RxJS-based local store.

```ts
export const TodoStore = signalStore(
  { providedIn: 'root' },
  withState({ todos: [] as Todo[], filter: 'all' }),
  withComputed(({ todos }) => ({ done: computed(() => todos().filter(t => t.done)) })),
  withMethods(store => ({ add(t: Todo) { patchState(store, s => ({ todos: [...s.todos, t] })); } }))
);
```

### Types of state
- **Server state** (orders from API) – consider caching, staleness (TanStack Query for Angular, `httpResource`).
- **Client/UI state** (sidebar open, selected tab) – local signals.
- **URL state** (filters, page number) – keep in query params so it survives refresh and is shareable.
- **Form state** – in the form model.

### Decision guide
- Small app / few shared pieces → services + signals.
- Medium app with some shared async state → Signal Store.
- Large app, many teams, complex flows, need for audit/devtools → NgRx Store.

Saying "I'd avoid NgRx unless the complexity justifies it" is a mature answer.
"""),

("Testing Angular Applications", r"""
### Tooling landscape (2025-26)
- **Unit tests:** historically **Karma + Jasmine** (Karma is deprecated). Angular v20+ supports **Jest** and **Vitest**; new projects from v21 use **Vitest** by default. The `TestBed` API is the same either way.
- **E2E:** **Cypress** or **Playwright** (Protractor is dead).
- **Component tests:** Angular Testing Library (`@testing-library/angular`) encourages testing from the user's perspective.

### Testing a service
```ts
describe('CartStore', () => {
  let store: CartStore;
  beforeEach(() => { TestBed.configureTestingModule({}); store = TestBed.inject(CartStore); });

  it('computes total', () => {
    store.add({ id: 1, price: 100, qty: 2 });
    expect(store.total()).toBe(200);
  });
});
```

### Testing a component
```ts
describe('UserCardComponent', () => {
  let fixture: ComponentFixture<UserCardComponent>;
  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [UserCardComponent] }).compileComponents();
    fixture = TestBed.createComponent(UserCardComponent);
    fixture.componentRef.setInput('user', { id: 7, name: 'Asha', joined: new Date() });
    fixture.detectChanges();   // trigger CD + ngOnInit
  });

  it('shows the name', () => {
    expect(fixture.nativeElement.querySelector('h3').textContent).toContain('Asha');
  });

  it('emits id on click', () => {
    let emitted: number | undefined;
    fixture.componentInstance.select.subscribe(v => (emitted = v));
    fixture.nativeElement.querySelector('button').click();
    expect(emitted).toBe(7);
  });
});
```
In zoneless/OnPush tests prefer `await fixture.whenStable()` after changes instead of relying on automatic CD.

### Mocking dependencies
```ts
const apiSpy = jasmine.createSpyObj<OrderApi>('OrderApi', ['list']); // or jest.fn()/vi.fn()
apiSpy.list.and.returnValue(of(mockOrders));
TestBed.configureTestingModule({ imports: [OrdersComponent], providers: [{ provide: OrderApi, useValue: apiSpy }] });
```
For HTTP, use `provideHttpClient()` + `provideHttpClientTesting()` and `HttpTestingController.expectOne(...).flush(data)`.

### Async utilities
- `fakeAsync` + `tick(ms)` / `flush()` – simulate time (debounceTime, setTimeout) synchronously (needs zone.js).
- `waitForAsync` – waits for real async tasks.
- With Vitest/Jest you can use fake timers (`vi.useFakeTimers()`).
- RxJS **marble testing** with `TestScheduler` for complex streams.

### Other things to test
- **Pipes** – plain class, just `new MyPipe().transform(x)`.
- **Guards/interceptors** – run inside `TestBed.runInInjectionContext(() => authGuard(route, state))`.
- **Router** – `RouterTestingHarness` to navigate and assert rendered components.
- **Component harnesses** (`@angular/cdk/testing`) – stable APIs for Material components.
- **Shallow vs deep** rendering – replace heavy child components with stubs or use `NO_ERRORS_SCHEMA` (careful: hides typos).

### What interviewers want to hear
- Test **behaviour, not implementation** (what the user sees and what gets emitted/called).
- AAA structure: Arrange, Act, Assert.
- Test pyramid: many unit tests, fewer integration, a few E2E for critical journeys (login, checkout).
- Coverage targets (~70–80%) with SonarQube gates — common in Indian product companies' CI pipelines.
"""),
]

qa = [
("What is Angular and how is it different from AngularJS and React?", r"""
**Angular** (v2+) is a TypeScript-based, component-driven **full framework** by Google: router, forms, HTTP, DI, CLI and testing are built in.

**vs AngularJS (1.x):** AngularJS used JavaScript, controllers + `$scope`, two-way binding with digest-cycle dirty checking, and was slow for large apps. Angular is a complete rewrite: components, TypeScript, AOT compilation, unidirectional data flow, mobile-friendly, much faster.

**vs React:** React is a UI *library* (view layer only); you pick router/state/forms libraries yourself. React uses JSX and a virtual DOM; Angular uses HTML templates compiled into incremental DOM instructions (Ivy) and now signals for fine-grained updates. Angular is more opinionated, which suits large enterprise teams; React offers more flexibility.
""", B, ["architecture", "basics"], True),

("Explain the difference between a component and a directive. What types of directives exist?", r"""
A **component is a directive with a template** — it renders its own view. A **directive** adds behaviour to an existing element without its own template.

Types:
1. **Components** – `@Component`, have a template.
2. **Attribute directives** – change appearance/behaviour: `ngClass`, `ngStyle`, `ngModel`, custom `[appHighlight]`.
3. **Structural directives** – change DOM layout by adding/removing elements, prefixed with `*`: `*ngIf`, `*ngFor`, `*ngSwitchCase` (now largely replaced by built-in `@if/@for/@switch`).

```ts
@Directive({ selector: '[appHighlight]', host: { '(mouseenter)': 'on()', '(mouseleave)': 'off()' } })
export class HighlightDirective {
  private el = inject(ElementRef);
  color = input('yellow', { alias: 'appHighlight' });
  on() { this.el.nativeElement.style.background = this.color(); }
  off() { this.el.nativeElement.style.background = ''; }
}
```
""", B, ["components", "directives"], True),

("List the Angular lifecycle hooks in order and give a use for each important one.", r"""
Order: `constructor` → `ngOnChanges` → `ngOnInit` → `ngDoCheck` → `ngAfterContentInit` → `ngAfterContentChecked` → `ngAfterViewInit` → `ngAfterViewChecked` → (repeat changes/checks) → `ngOnDestroy`.

- **ngOnChanges** – runs when an input *reference* changes; receives `SimpleChanges` (previous/current value, firstChange).
- **ngOnInit** – once; fetch initial data, set up subscriptions (inputs are available here, not in the constructor).
- **ngDoCheck** – custom change detection; runs every cycle, so keep it cheap.
- **ngAfterContentInit** – projected content (`@ContentChild`) is ready.
- **ngAfterViewInit** – view and child views ready; use `@ViewChild`, initialise chart libraries.
- **ngOnDestroy** – cleanup: unsubscribe, clear timers, detach listeners.

Modern alternatives: `DestroyRef.onDestroy()`, `afterNextRender()` for DOM work after rendering.
""", B, ["lifecycle"], True),

("What is the difference between constructor and ngOnInit?", r"""
- The **constructor** is a TypeScript/JS feature called when the class is instantiated. Angular uses it for **dependency injection**. Input values are **not yet set** here, and the view doesn't exist.
- **ngOnInit** is an Angular lifecycle hook called **once after the first `ngOnChanges`**, when inputs are bound.

Rule of thumb: constructor (or field `inject()`) only for wiring dependencies; put initialisation logic — API calls, reading inputs, subscriptions — in `ngOnInit`. This also keeps components easier to test because creating the instance has no side effects.

```ts
export class OrderComponent implements OnInit {
  orderId = input.required<number>();
  private api = inject(OrderApi);          // DI
  ngOnInit() { this.api.get(this.orderId()).subscribe(...); } // input available
}
```
""", B, ["lifecycle"], True),

("How do components communicate with each other in Angular?", r"""
1. **Parent → child:** `@Input()` / `input()` signals.
2. **Child → parent:** `@Output()` with `EventEmitter`, or `output()`.
3. **Two-way:** `model()` signal or `@Input() x` + `@Output() xChange` → `[(x)]`.
4. **Parent accessing child API:** `@ViewChild` / `viewChild()` or template reference variable `#child` and call `child.method()`.
5. **Unrelated/sibling components:** a shared **service** holding a signal or `BehaviorSubject`.
6. **Global complex state:** NgRx store / Signal Store.
7. **Via router:** route params, query params, `history.state` (`router.navigate([...], { state })`).

Choose the narrowest mechanism that works — inputs/outputs for direct relationships, services for cross-tree sharing.
""", B, ["components", "communication"], True),

("Explain Angular change detection. How does OnPush improve performance?", r"""
Change detection syncs component state with the DOM. With the **Default** strategy, after any async event (patched by Zone.js) Angular checks **every component** top-down, comparing template bindings to previous values.

**OnPush** limits checks: an OnPush component's subtree is checked only when
- an `@Input` **reference** changes,
- an event originates from its template/children,
- the `async` pipe emits,
- a signal read in the template changes,
- `markForCheck()` is called.

So if 200 rows use OnPush and only one row's input object changes, only that row is re-checked. The trade-off: you must use **immutable updates** (`items = [...items, x]`), otherwise mutations won't be reflected.
""", I, ["change-detection", "performance"], True),

("What is Zone.js and what does zoneless Angular mean?", r"""
**Zone.js** monkey-patches async APIs (`setTimeout`, DOM events, promises, XHR). Angular runs inside `NgZone`, and when an async task completes it automatically triggers change detection. That's why plain field updates "just work".

**Zoneless Angular** (`provideZonelessChangeDetection()`, stable since v20.2, default for new apps in v21) removes Zone.js. Change detection is scheduled only when Angular is notified: a template-read **signal** changes, `markForCheck()` is called (the `async` pipe does this), a bound template event fires, or inputs are set.

Benefits: smaller bundle, fewer unnecessary CD cycles, readable stack traces, native `async/await`. Migration requirement: components must be OnPush-compatible — state in signals or observables with `async`, not mutated plain fields inside `setTimeout` or subscriptions.
""", A, ["change-detection", "zonejs", "zoneless"], True),

("What is the difference between markForCheck() and detectChanges()?", r"""
Both are on `ChangeDetectorRef`:

- **`markForCheck()`** marks the current component **and all its ancestors** as dirty so they will be checked in the **next** change detection cycle. It doesn't run CD itself. Used in OnPush components when data changes outside Angular's knowledge (e.g. a manual subscription).
- **`detectChanges()`** runs change detection **synchronously, right now**, for this component and its children only (ancestors are not checked). Useful after `detach()`, or when you need the DOM updated immediately.

```ts
this.socket.messages$.subscribe(m => {
  this.messages = [...this.messages, m];
  this.cdr.markForCheck();   // OnPush component updates on next tick
});
```
With signals you rarely need either — updating the signal marks the view automatically.
""", I, ["change-detection"], False),

("What are signals in Angular? Explain signal, computed and effect.", r"""
A **signal** is a reactive wrapper around a value that tracks who reads it and notifies them on change.

- `signal(initial)` – writable; read with `count()`, change with `set()` / `update()`.
- `computed(() => ...)` – derived, read-only, **lazy and memoised**; recomputes only when a dependency changes.
- `effect(() => ...)` – runs side effects whenever signals it reads change (logging, localStorage sync, calling non-Angular APIs). Don't use it to set other signals — that's what `computed`/`linkedSignal` are for.

```ts
qty = signal(1);
price = signal(499);
total = computed(() => this.qty() * this.price());
constructor() { effect(() => localStorage.setItem('qty', String(this.qty()))); }
```
Why they matter: fine-grained change detection (only affected views update), no manual subscriptions, and they enable zoneless Angular.
""", I, ["signals"], True),

("Signals vs RxJS Observables — when would you use each?", r"""
| | Signals | Observables |
|---|---|---|
| Model | Current **value/state** | **Stream of events** over time |
| Read | Sync: `sig()` | Async: subscribe |
| Cleanup | None needed | Must unsubscribe (or async pipe) |
| Operators | `computed` only | 100+ (debounce, retry, switchMap) |
| CD | Fine-grained, zoneless-friendly | Needs async pipe/markForCheck |

Use **signals** for component and app state (selected item, cart, form flags, derived totals). Use **RxJS** for async orchestration: HTTP with retries, debouncing user input, cancelling stale requests, websockets, combining multiple streams.

They interoperate: `toSignal(obs$)` and `toObservable(sig)`. Typical pattern: `results = toSignal(toObservable(query).pipe(debounceTime(300), switchMap(q => api.search(q))))`.
""", I, ["signals", "rxjs"], True),

("What is linkedSignal and how does it differ from computed?", r"""
`computed` is **read-only** — you can't set it. `linkedSignal` (stable in v20) is a **writable** signal whose value is derived from a source but can also be overridden locally; when the source changes, it **resets** to the derived value.

```ts
options = input.required<Plan[]>();
selected = linkedSignal(() => this.options()[0]);  // default to first plan

choose(p: Plan) { this.selected.set(p); }          // user override
// If parent passes a new options list, selected resets to options()[0]
```
There's also an advanced form with `source` and `computation(newSource, previous)` so you can keep the previous selection if it still exists in the new list. Before `linkedSignal` people misused `effect` to copy values between signals, which causes extra CD cycles and bugs.
""", A, ["signals"], False),

("What are standalone components? What are their advantages over NgModules?", r"""
Standalone components declare their dependencies directly via `imports` in `@Component` and don't need to be declared in an `NgModule`. They are the **default since Angular 19**.

Advantages:
- Less boilerplate; each component is self-describing.
- Easy **lazy loading of a single component** with `loadComponent`.
- Better tree-shaking — unused things don't get pulled in via big shared modules.
- Simpler tests (`imports: [MyComponent]`).
- App bootstraps with `bootstrapApplication` and `provide*` functions (`provideRouter`, `provideHttpClient`).

They interoperate with modules: you can import a standalone component into an NgModule and import NgModules into a standalone component, so migration can be gradual (`ng g @angular/core:standalone`).
""", B, ["standalone"], True),

("Explain Angular's hierarchical dependency injection.", r"""
Angular has two injector hierarchies:

1. **Environment injectors:** platform → root (`providedIn: 'root'`, `bootstrapApplication` providers) → child environment injectors created for **lazy-loaded routes** with `providers`.
2. **Element injectors:** created for components/directives that declare `providers`/`viewProviders`.

When a dependency is requested, Angular walks up the **element tree** first, then up the **environment** chain. First match wins; if none, `NullInjectorError`.

Consequences:
- `providedIn: 'root'` → one app-wide singleton.
- Provided in a component → **new instance per component instance**, shared by its children.
- Provided in a lazy route/module → separate instance for that lazy section (a common "two singletons" bug).

Modifiers `@Self`, `@SkipSelf`, `@Optional`, `@Host` (or `inject(X, {self, skipSelf, optional, host})`) control the lookup.
""", I, ["di"], True),

("What are useClass, useValue, useFactory and useExisting providers?", r"""
They tell the injector **how to create** the value for a token:

```ts
{ provide: Logger, useClass: ProdLogger }            // new instance of a class
{ provide: APP_CONFIG, useValue: { apiUrl: '/api' } } // fixed value/object
{ provide: Storage, useFactory: () => inject(PLATFORM_ID) === 'browser' ? localStorage : new MemoryStorage() }
{ provide: AbstractLogger, useExisting: Logger }      // alias: same instance as Logger
```
- **useClass** – swap implementations (mock in tests, environment-specific).
- **useValue** – constants, config, already-built objects.
- **useFactory** – needs logic or other dependencies to build (can call `inject()` inside).
- **useExisting** – two tokens resolve to one instance (no duplicate created).

Add `multi: true` to collect multiple providers for one token into an array (e.g. `HTTP_INTERCEPTORS`, `APP_INITIALIZER`).
""", I, ["di", "providers"], True),

("What is an InjectionToken and when do you need it?", r"""
Angular DI uses class types as tokens, but **interfaces, strings, objects and functions don't exist at runtime** (TypeScript interfaces are erased). An `InjectionToken` creates a unique runtime token for such values.

```ts
export interface AppConfig { apiUrl: string; featureX: boolean; }
export const APP_CONFIG = new InjectionToken<AppConfig>('APP_CONFIG', {
  providedIn: 'root',
  factory: () => ({ apiUrl: '/api', featureX: false })   // optional default
});

// app.config.ts
providers: [{ provide: APP_CONFIG, useValue: environment.config }]

// usage
private config = inject(APP_CONFIG);
```
Using a string token (`'API_URL'`) risks name collisions and loses typing — `InjectionToken` is type-safe and unique.
""", I, ["di"], False),

("What is the inject() function and what is an injection context?", r"""
`inject(Token)` retrieves a dependency without constructor parameters:
```ts
export class OrdersComponent {
  private api = inject(OrderApi);
  private route = inject(ActivatedRoute);
}
```
It only works inside an **injection context**: during construction (constructor body, field initialisers), in provider factories, and in functional guards/resolvers/interceptors. Calling it later — in `ngOnInit`, a click handler or a `setTimeout` — throws **NG0203**. Use `runInInjectionContext(injector, () => inject(X))` if you really need it.

Advantages: works with functional APIs, easier inheritance (no `super(...)` with many args), type inference, and enables reusable "composable" helper functions like `injectQueryParam('id')`.
""", I, ["di"], False),

("What is the difference between Observable and Promise?", r"""
| Observable | Promise |
|---|---|
| **Lazy**: executes on `subscribe()` | **Eager**: executes on creation |
| Emits **0..many** values | Resolves **once** |
| **Cancellable** via `unsubscribe()` | Not cancellable |
| Operators (`map`, `filter`, `retry`, `switchMap`) | Only `then`/`catch`/`finally` |
| Can be synchronous | Always async (microtask) |
| Unicast (cold) by default | Shared result |

```ts
const p = fetch('/api'); // request fires now
const o = this.http.get('/api'); // nothing yet
o.subscribe(); o.subscribe(); // TWO requests (cold)
```
Convert with `from(promise)` or `firstValueFrom(obs$)` / `lastValueFrom(obs$)` (replacements for deprecated `toPromise()`).
""", B, ["rxjs"], True),

("Explain switchMap, mergeMap, concatMap and exhaustMap with real use cases.", r"""
All four map each source value to an inner observable and flatten it. They differ when a new value arrives while the previous inner observable is still active:

- **switchMap** – unsubscribes (cancels) the previous inner → only latest matters. *Type-ahead search, loading details when route param changes.*
- **mergeMap** – keeps all inners running concurrently; results may arrive out of order. *Bulk delete, parallel uploads* (limit with `mergeMap(fn, 3)`).
- **concatMap** – queues inners, runs them one by one in order. *Saving form autosaves sequentially, ordered transactions.*
- **exhaustMap** – ignores new values until current inner completes. *Login/Pay button double-click, refresh token call.*

```ts
this.payClicks$.pipe(
  exhaustMap(() => this.api.pay(this.order()))   // extra clicks ignored while paying
).subscribe();
```
Interview shortcut: switch = cancel, merge = parallel, concat = queue, exhaust = ignore.
""", I, ["rxjs", "operators"], True),

("What are Subject, BehaviorSubject, ReplaySubject and AsyncSubject?", r"""
Subjects are **multicast**: they are both an Observable and an Observer, so you can call `next()` on them and many subscribers share the same emissions.

- **Subject** – no initial value; subscribers only get values emitted **after** they subscribe. Use for events (e.g. "refresh clicked").
- **BehaviorSubject(initial)** – stores the **latest value**; new subscribers immediately get it; `.value` gives it synchronously. Use for state (current user, cart).
- **ReplaySubject(n, windowTime?)** – replays the last *n* values to new subscribers. Use for caches/history.
- **AsyncSubject** – emits only the **last** value, and only when it completes.

```ts
const s = new BehaviorSubject(0);
s.next(1);
s.subscribe(v => console.log(v)); // 1 immediately
s.next(2);                        // 2
```
Expose them as `subject.asObservable()` so consumers can't call `next()`.
""", I, ["rxjs", "subjects"], True),

("How do you prevent memory leaks from subscriptions in Angular?", r"""
Unclosed subscriptions to long-lived observables (store selects, `interval`, websocket, `valueChanges`, router events) keep components alive after they're destroyed.

Strategies (best first):
1. **`async` pipe** – `{{ orders$ | async }}` subscribes/unsubscribes automatically.
2. **`toSignal(obs$)`** – auto-cleans on destroy.
3. **`takeUntilDestroyed()`** from `@angular/core/rxjs-interop`:
```ts
constructor() { this.form.valueChanges.pipe(takeUntilDestroyed()).subscribe(...); }
// outside constructor: takeUntilDestroyed(this.destroyRef)
```
4. **`takeUntil(destroy$)`** with a Subject completed in `ngOnDestroy` (keep it as the last operator).
5. Keep a `Subscription` and call `unsubscribe()` in `ngOnDestroy` (`sub.add(other)` to group).
6. `take(1)`/`first()` for one-off reads.

HTTP observables complete after one response, so they don't leak, though cancelling on destroy avoids wasted work.
""", I, ["rxjs", "memory-leaks"], True),

("What is the difference between combineLatest, forkJoin, zip and withLatestFrom?", r"""
- **forkJoin([a$, b$])** – waits until **all complete**, emits once with their last values. Like `Promise.all`. Ideal for parallel HTTP calls on page load. If any errors, whole thing errors; if one never completes, it never emits.
- **combineLatest([a$, b$])** – after each source has emitted at least once, emits the latest of all **whenever any** emits. Ideal for filters + data streams.
- **zip(a$, b$)** – pairs values by index (1st with 1st, 2nd with 2nd).
- **a$.pipe(withLatestFrom(b$))** – emits only when **a$** emits, grabbing b$'s latest value. Ideal for "on save click, take current form value".

```ts
forkJoin({ user: api.user(), roles: api.roles() })
  .subscribe(({ user, roles }) => ...);
```
""", I, ["rxjs", "operators"], False),

("What is shareReplay and when would you use it?", r"""
`shareReplay` turns a **cold** observable into a shared (multicast) one and replays the last *n* values to late subscribers.

Problem: `countries$ = this.http.get('/api/countries')` used with three `async` pipes = **three HTTP calls**.

```ts
readonly countries$ = this.http.get<Country[]>('/api/countries').pipe(
  shareReplay({ bufferSize: 1, refCount: true })
);
```
Now there's one request and every subscriber gets the cached result.

- `bufferSize: 1` – keep the latest value.
- `refCount: true` – unsubscribe from the source when no subscribers remain (prevents leaks for infinite sources). With `refCount: false` (default for the number overload), the source stays subscribed forever — fine for a one-shot HTTP cache, risky for intervals/websockets.

`share()` multicasts without replaying to late subscribers.
""", A, ["rxjs", "caching"], False),

("How does lazy loading work in Angular? How do you implement it?", r"""
Lazy loading splits code into separate JS **chunks** that are downloaded only when the user navigates to that route, shrinking the initial bundle and improving first load.

```ts
export const routes: Routes = [
  { path: 'admin', loadChildren: () => import('./admin/admin.routes').then(m => m.ADMIN_ROUTES) },
  { path: 'reports', loadComponent: () => import('./reports/reports.component').then(m => m.ReportsComponent) },
  // legacy module: loadChildren: () => import('./orders/orders.module').then(m => m.OrdersModule)
];
```
The dynamic `import()` tells the bundler to create a separate chunk.

Extras:
- **Preloading** – `withPreloading(PreloadAllModules)` or a custom strategy fetches chunks in the background after startup.
- **`canMatch`** guard prevents downloading the chunk for unauthorised users.
- Don't import lazy feature code eagerly elsewhere, or it ends up in the main bundle.
- For template-level laziness, use `@defer`.
""", B, ["routing", "lazy-loading", "performance"], True),

("What are route guards? Explain CanActivate, CanDeactivate, CanMatch and resolvers.", r"""
Guards decide whether navigation can proceed. Modern guards are **functions**:

```ts
export const authGuard: CanActivateFn = (route, state) =>
  inject(AuthService).isLoggedIn() || inject(Router).createUrlTree(['/login']);

export const unsavedGuard: CanDeactivateFn<EditComponent> = c =>
  !c.form.dirty || confirm('Discard changes?');
```
- **canActivate** – allow entering the route (auth, role checks).
- **canActivateChild** – same for child routes.
- **canDeactivate** – allow leaving (unsaved changes).
- **canMatch** – whether the route config matches at all; blocks lazy chunk download and can route the same path to different components (replaces deprecated `canLoad`).
- **resolve** – fetch data before activation; available via `route.data` or component inputs.

Guards return `boolean | UrlTree` or Observable/Promise of them. Remember they are client-side only — the backend must still authorise every API call.
""", I, ["routing", "guards"], True),

("How do you read route parameters and query parameters? Why can snapshot be a problem?", r"""
```ts
private route = inject(ActivatedRoute);

// Observable — updates when params change
id$ = this.route.paramMap.pipe(map(p => +p.get('id')!));
tab$ = this.route.queryParamMap.pipe(map(q => q.get('tab') ?? 'details'));

// One-time snapshot
const id = this.route.snapshot.paramMap.get('id');

// Modern: provideRouter(routes, withComponentInputBinding())
id = input<string>();   // auto-bound from :id or ?id
```
**Snapshot problem:** Angular **reuses the component instance** when navigating between URLs matching the same route (`/products/1` → `/products/2`). `ngOnInit` doesn't run again and the snapshot stays at `1`. Subscribe to `paramMap` (with `switchMap` to load data) or use input binding so the component reacts to changes.
""", I, ["routing"], False),

("Reactive forms vs template-driven forms — which do you prefer and why?", r"""
| Reactive | Template-driven |
|---|---|
| Model defined in **class** (`FormGroup`, `FormControl`) | Model created by directives in **template** (`ngModel`) |
| Synchronous access to values/state | Asynchronous (created after view init) |
| Strongly typed (v14+) | Weakly typed |
| Easy dynamic fields (`FormArray`) | Awkward for dynamic forms |
| Easy unit testing without DOM | Needs DOM to test |
| `valueChanges` observable for RxJS | Limited reactivity |

I prefer **reactive forms** for anything beyond a trivial form — e.g. in my project the customer onboarding form has nested address groups, a dynamic list of documents, cross-field validation and an async "PAN already registered" validator hitting a Spring Boot endpoint. Template-driven is fine for a two-field search or login form.
""", B, ["forms"], True),

("How do you write a custom synchronous and asynchronous validator?", r"""
**Sync validator** – a function returning `ValidationErrors | null`:
```ts
export function forbiddenName(name: string): ValidatorFn {
  return (c: AbstractControl) => c.value?.toLowerCase() === name ? { forbiddenName: true } : null;
}
// cross-field on group
export const matchPasswords: ValidatorFn = g =>
  g.get('password')?.value === g.get('confirm')?.value ? null : { mismatch: true };
```
**Async validator** – returns `Observable<ValidationErrors | null>` (or Promise):
```ts
export function usernameTaken(api: UserApi): AsyncValidatorFn {
  return c => timer(400).pipe(                 // debounce
    switchMap(() => api.exists(c.value)),
    map(exists => (exists ? { taken: true } : null)),
    catchError(() => of(null))
  );
}
this.fb.control('', { validators: [Validators.required], asyncValidators: [usernameTaken(api)], updateOn: 'blur' });
```
While async validation runs, control status is `PENDING`. Async validators run only after sync validators pass.
""", I, ["forms", "validation"], True),

("What is ControlValueAccessor?", r"""
`ControlValueAccessor` (CVA) is the bridge between Angular forms and a DOM element or custom component. Implementing it lets your component work with `formControlName`, `[formControl]` and `ngModel`.

```ts
@Component({
  selector: 'app-rating',
  template: `@for (s of [1,2,3,4,5]; track s) { <span (click)="set(s)">{{ s <= value ? '★' : '☆' }}</span> }`,
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => RatingComponent), multi: true }]
})
export class RatingComponent implements ControlValueAccessor {
  value = 0; disabled = false;
  private onChange = (v: number) => {}; private onTouched = () => {};
  writeValue(v: number) { this.value = v ?? 0; }            // form -> view
  registerOnChange(fn: any) { this.onChange = fn; }        // view -> form
  registerOnTouched(fn: any) { this.onTouched = fn; }
  setDisabledState(d: boolean) { this.disabled = d; }
  set(v: number) { if (!this.disabled) { this.value = v; this.onChange(v); this.onTouched(); } }
}
```
Usage: `<app-rating formControlName="score" />`.
""", A, ["forms", "cva"], False),

("What are HTTP interceptors and what have you used them for?", r"""
Interceptors are middleware for `HttpClient`: every request and response passes through the chain, so cross-cutting concerns live in one place. Requests are immutable — use `req.clone()`.

```ts
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).token();
  return next(token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req);
};
// provideHttpClient(withInterceptors([authInterceptor, loaderInterceptor, errorInterceptor]))
```
Typical uses: attaching JWT, global error handling (401 → login, 5xx → toast), loading spinner with `finalize`, refresh-token retry, caching GETs, adding correlation IDs, prefixing base URLs.

Order: requests flow in provided order, responses in reverse. Legacy class interceptors implement `HttpInterceptor` and register with `HTTP_INTERCEPTORS` + `multi: true`.
""", I, ["http", "interceptors"], True),

("How would you implement a refresh-token flow in an Angular interceptor?", r"""
Goal: on a 401, refresh the access token **once**, queue concurrent failing requests, then retry them.

```ts
let refreshing$: Observable<string> | null = null;

export const refreshInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  return next(withToken(req, auth.token())).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status !== 401 || req.url.includes('/auth/refresh')) return throwError(() => err);
      refreshing$ ??= auth.refresh().pipe(          // single shared refresh call
        finalize(() => (refreshing$ = null)),
        shareReplay(1)
      );
      return refreshing$.pipe(
        switchMap(newToken => next(withToken(req, newToken))),
        catchError(e => { auth.logout(); return throwError(() => e); })
      );
    })
  );
};
const withToken = (r: HttpRequest<unknown>, t: string | null) =>
  t ? r.clone({ setHeaders: { Authorization: `Bearer ${t}` } }) : r;
```
Key points: exclude the refresh endpoint itself (avoid infinite loops), share one refresh request, logout if refresh fails. Prefer storing the refresh token in an HttpOnly cookie set by Spring Boot.
""", A, ["http", "interceptors", "auth"], True),

("What is trackBy (or track in @for) and why is it important?", r"""
When the array behind a list changes reference (e.g. a fresh API response), Angular by default identifies items by **object identity**. New objects → it destroys and recreates **all DOM nodes**, losing focus/scroll state and costing performance.

`trackBy` / `track` gives Angular a stable key so it re-uses DOM nodes for unchanged items and only touches added/removed/changed rows.

```html
<!-- modern (track is mandatory) -->
@for (order of orders(); track order.id) { <app-order-row [order]="order" /> }

<!-- legacy -->
<app-order-row *ngFor="let order of orders; trackBy: trackById" [order]="order" />
```
```ts
trackById = (_: number, o: Order) => o.id;
```
Use a unique business id; use `$index` only for static lists where items don't reorder.
""", B, ["performance", "templates"], True),

("What is @defer and how does it help performance?", r"""
`@defer` (v17) lazily loads a section of a template — its components, directives and pipes are split into a separate chunk and loaded only when a trigger fires.

```html
@defer (on viewport; prefetch on idle) {
  <app-reviews [productId]="id()" />
} @placeholder { <div class="skeleton"></div> }
  @loading (after 100ms; minimum 500ms) { <app-spinner /> }
  @error { <p>Failed to load reviews</p> }
```
Triggers: `on idle` (default), `on viewport`, `on interaction`, `on hover`, `on immediate`, `on timer(x)`, or `when <condition>`. `prefetch` downloads code earlier than rendering.

Benefits: smaller initial bundle, better LCP/TTI, no router setup needed. With SSR, `hydrate on ...` triggers enable **incremental hydration** (v19+). Requirement: deferred dependencies must be standalone and not referenced eagerly elsewhere in the same file.
""", I, ["performance", "defer"], True),

("Your Angular application is slow. How would you identify and fix the problem?", r"""
**1. Measure** – Lighthouse (LCP, TBT), Chrome Performance tab, Angular DevTools profiler (which components take CD time), bundle analysis (`ng build --stats-json`, source-map-explorer).

**2. Load-time fixes** – lazy-load routes, `@defer` heavy widgets, remove large libs (moment → date-fns), `NgOptimizedImage`, SSR/hydration, compression and caching, bundle budgets.

**3. Runtime fixes** – OnPush + immutable data, signals/`computed`, `track` in loops, pure pipes instead of template method calls, virtual scroll (`cdk-virtual-scroll-viewport`) for big lists, server-side pagination, `runOutsideAngular` for scroll/mousemove, debounce inputs, fix subscription leaks.

**4. Network** – cache with `shareReplay`, cancel stale requests (`switchMap`), parallelise with `forkJoin`, reduce payload sizes in Spring Boot DTOs.

Close with a real example and numbers ("reduced initial bundle from 3.1 MB to 1.4 MB by lazy-loading three modules").
""", A, ["performance"], True),

("What are pipes? Explain pure vs impure pipes and the async pipe.", r"""
Pipes transform values in templates: `{{ amount | currency:'INR' }}`, `{{ d | date:'dd MMM' }}`.

```ts
@Pipe({ name: 'initials' })   // pure by default
export class InitialsPipe implements PipeTransform {
  transform(name: string): string { return name.split(' ').map(p => p[0]).join(''); }
}
```
- **Pure pipe** (default) – re-executed only when the input **reference/primitive value** changes. Cheap, memoised-like. Won't detect array mutation.
- **Impure pipe** (`pure: false`) – runs on **every** change detection cycle. Needed for mutable inputs, but expensive.
- **async pipe** (impure) – subscribes to an Observable/Promise, returns latest value, calls `markForCheck()` (works with OnPush), and unsubscribes on destroy.

Prefer pure pipes over calling methods in templates, because methods run on every CD cycle.
""", B, ["pipes", "performance"], True),

("What is NgRx? Explain its core building blocks and when you would use it.", r"""
NgRx is a Redux-inspired state management library for Angular.

- **Store** – single immutable state tree.
- **Actions** – events describing what happened (`[Orders Page] Load`).
- **Reducers** – pure functions `(state, action) => newState`.
- **Selectors** – memoised queries over state (`createSelector`).
- **Effects** – side effects (API calls) listening to actions and dispatching new ones.
- Extras: Entity (normalised collections), DevTools (time travel), Router Store, Signal Store.

Flow: component dispatches action → reducer updates state → selectors emit → component re-renders; effects handle async work and dispatch success/failure.

Use it for large apps with shared, complex state, many developers and a need for traceability. For small/medium apps, a service with signals or NgRx Signal Store is simpler — NgRx adds boilerplate.
""", I, ["state-management", "ngrx"], True),

("How would you share state between components without NgRx?", r"""
Use a singleton service as a lightweight store.

**Signals version (modern):**
```ts
@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly _user = signal<User | null>(null);
  readonly user = this._user.asReadonly();
  readonly isLoggedIn = computed(() => !!this._user());
  login(u: User) { this._user.set(u); }
  logout() { this._user.set(null); }
}
```
**RxJS version:**
```ts
private user$ = new BehaviorSubject<User | null>(null);
readonly currentUser$ = this.user$.asObservable();
setUser(u: User) { this.user$.next(u); }
```
Keep the writable source private and expose read-only views so state changes only through methods (encapsulation). For component-subtree state, provide the service in the parent component's `providers` so each instance gets its own store.
""", I, ["state-management", "services"], True),

("What is AOT compilation? How does it differ from JIT?", r"""
- **JIT (Just-in-Time)** – the Angular compiler ships to the browser and compiles templates at runtime. Bigger bundles, slower startup, template errors appear only at runtime.
- **AOT (Ahead-of-Time)** – templates are compiled into JavaScript during the build (`ng build`). Default since Angular 9 (Ivy).

AOT benefits:
1. **Faster rendering** – the browser runs pre-compiled code.
2. **Smaller bundles** – compiler not shipped; better tree-shaking.
3. **Early error detection** – binding/type errors fail the build (with `strictTemplates`).
4. **Security** – fewer opportunities for template injection since templates aren't evaluated at runtime.

**Ivy** is the current compilation/rendering engine; it generates locality-based instructions per component, enabling incremental compilation and smaller output.
""", B, ["compilation", "architecture"], False),

("What is content projection? Difference between ViewChild and ContentChild?", r"""
**Content projection** lets a parent insert markup into a child's template using `<ng-content>`:
```html
<!-- card.component.html -->
<div class="card"><header><ng-content select="[card-title]" /></header><ng-content /></div>
<!-- usage -->
<app-card><h3 card-title>Orders</h3><p>Body text</p></app-card>
```
- **ViewChild / viewChild()** – queries elements/components declared in the component's **own template**. Available in `ngAfterViewInit`.
- **ContentChild / contentChild()** – queries elements **projected** into the component from outside. Available in `ngAfterContentInit`.

`@ViewChildren`/`@ContentChildren` return a `QueryList` of all matches. With `{ static: true }` a ViewChild is resolved before `ngOnInit` (only if not inside `@if`/`*ngIf`).
""", I, ["components", "content-projection"], False),

("What is ExpressionChangedAfterItHasBeenCheckedError and how do you fix it?", r"""
In dev mode Angular runs a second verification pass after change detection. If a binding's value differs between the two passes, it throws this error — it means your code changed state **during** change detection (usually in `ngAfterViewInit`, `ngAfterViewChecked`, or a child changing a parent's bound value), causing an inconsistent view.

Example:
```ts
ngAfterViewInit() { this.title = 'Loaded'; } // title is bound in template -> error
```
Fixes:
1. Move logic to `ngOnInit` or the constructor if possible.
2. Use signals/`computed` so derivations are consistent.
3. Avoid getters that return new values each call (e.g. `new Date()`, random).
4. If you must update after view init, schedule it (`queueMicrotask`/`afterNextRender`) or call `cdr.detectChanges()` explicitly.

Don't just wrap in `setTimeout` blindly — understand the data flow first.
""", A, ["change-detection", "debugging"], False),

("What is the difference between ng-template, ng-container and ng-content?", r"""
- **`<ng-template>`** – defines a chunk of template that is **not rendered** by default; rendered on demand via structural directives, `*ngTemplateOutlet`, or `ViewContainerRef.createEmbeddedView`. Used for `else` blocks, reusable snippets, customisable table cells.
- **`<ng-container>`** – a logical grouping element that **renders no DOM element**. Useful to apply `*ngIf` and `*ngFor` together, or as a host for `ngTemplateOutlet`.
- **`<ng-content>`** – a slot for **content projection** from the parent.

```html
<ng-container *ngTemplateOutlet="row; context: { $implicit: user }"></ng-container>
<ng-template #row let-u><td>{{ u.name }}</td></ng-template>
```
""", B, ["templates"], False),

("How do you unit test an Angular component that depends on a service making HTTP calls?", r"""
Mock the service (best for component tests) or mock HTTP (best for service tests).

```ts
describe('OrdersComponent', () => {
  const api = { list: vi.fn() };   // or jasmine.createSpyObj
  beforeEach(async () => {
    api.list.mockReturnValue(of([{ id: 1, total: 500 }]));
    await TestBed.configureTestingModule({
      imports: [OrdersComponent],
      providers: [{ provide: OrderApi, useValue: api }]
    }).compileComponents();
  });

  it('renders orders', async () => {
    const f = TestBed.createComponent(OrdersComponent);
    f.detectChanges(); await f.whenStable();
    expect(f.nativeElement.querySelectorAll('tr.order').length).toBe(1);
    expect(api.list).toHaveBeenCalled();
  });
});
```
For the service itself: `provideHttpClient(), provideHttpClientTesting()`, then `httpMock.expectOne('/api/orders').flush(data)` and `httpMock.verify()`.
""", I, ["testing"], True),

("What is a resolver vs fetching data in ngOnInit? Which is better?", r"""
- **Resolver** fetches data **before** the route activates; component receives ready data via `route.data` or input binding. Pros: component never renders an empty state, simple component code. Cons: navigation appears frozen until data arrives (no skeleton), errors must be handled in the resolver, slower perceived performance.
- **Fetching in component** (`ngOnInit`, `toSignal`, `httpResource`): page renders immediately with skeleton/spinner, progressively shows data, handles errors locally.

Modern UX generally prefers component fetching with skeleton loaders. Resolvers suit small, critical data where showing a partially-rendered page makes no sense (e.g. entity must exist, else redirect to 404).
""", I, ["routing", "resolvers"], False),

("How do you handle errors globally in an Angular application?", r"""
Layers:
1. **HTTP interceptor** – catch `HttpErrorResponse`, map status codes (401 → login/refresh, 403 → forbidden page, 5xx → toast), log, then rethrow.
2. **Global ErrorHandler** – catches all uncaught errors (template errors, exceptions in handlers):
```ts
@Injectable()
export class AppErrorHandler implements ErrorHandler {
  private logger = inject(LoggingService);
  handleError(error: unknown) { this.logger.send(error); console.error(error); }
}
// providers: [{ provide: ErrorHandler, useClass: AppErrorHandler }]
```
3. **Local `catchError`** in components/services for screen-specific fallbacks (`of([])`).
4. `@defer`'s `@error` block for lazy content, and router `withNavigationErrorHandler`.

Send errors to monitoring (Sentry, Datadog) with a correlation ID that matches Spring Boot logs.
""", I, ["error-handling", "http"], False),

("What is the async pipe and why is it preferred over manual subscribe?", r"""
The `async` pipe subscribes to an Observable or Promise in the template and returns its latest value.

```html
@if (orders$ | async; as orders) {
  @for (o of orders; track o.id) { <app-order [order]="o" /> }
} @else { <app-spinner /> }
```
Advantages over manual `subscribe()`:
1. **Auto-unsubscribe** on destroy — no leaks.
2. Calls **`markForCheck()`** on each emission — works perfectly with OnPush (and zoneless).
3. Less code; keeps component declarative ("data as streams").
4. Handles switching to a new observable reference automatically.

Pitfall: using `obs$ | async` multiple times creates multiple subscriptions (multiple HTTP calls for cold observables). Use `as` alias once, `@let`, or `shareReplay`. In modern code `toSignal()` is a good alternative.
""", B, ["rxjs", "templates"], True),

("What are some security best practices in Angular?", r"""
- **XSS:** Angular escapes interpolated values and sanitises `[innerHTML]`, `[href]`, `[src]` by default. Avoid `bypassSecurityTrustHtml` unless the content is trusted; never build templates from user input.
- **Tokens:** prefer **HttpOnly, Secure, SameSite cookies** for refresh tokens (JS can't read them); if storing access tokens in memory/`localStorage`, remember XSS can steal them.
- **CSRF/XSRF:** `HttpClient` supports reading an `XSRF-TOKEN` cookie and sending `X-XSRF-TOKEN` header (`withXsrfConfiguration`), matching Spring Security's `CookieCsrfTokenRepository`.
- **Route guards are UX only** – enforce authorisation in the backend.
- **Content Security Policy** headers; Angular supports CSP nonces (`ngCspNonce`).
- Keep Angular and dependencies updated (`npm audit`), don't commit secrets in `environment.ts` (it ships to the browser).
""", I, ["security"], False),
]

sources = [
("Angular official docs (angular.dev)", "https://angular.dev/overview"),
("Angular - Signals guide", "https://angular.dev/guide/signals"),
("Angular - Zoneless guide", "https://angular.dev/guide/zoneless"),
("Angular - Deferrable views (@defer)", "https://angular.dev/guide/templates/defer"),
("Angular - Hierarchical injectors", "https://angular.dev/guide/di/hierarchical-dependency-injection"),
("Angular - HTTP interceptors", "https://angular.dev/guide/http/interceptors"),
("RxJS official documentation", "https://rxjs.dev/guide/overview"),
("NgRx documentation", "https://ngrx.io/docs"),
("GeeksforGeeks - Angular Interview Questions", "https://www.geeksforgeeks.org/angular-interview-questions/"),
("InterviewBit - Angular Interview Questions", "https://www.interviewbit.com/angular-interview-questions/"),
]

build("angular", "ng", "Angular", 5, "🅰️",
      "Modern Angular (v17-v21) from components and change detection to signals, RxJS, routing, forms, performance and testing.",
      notes, qa, sources)
