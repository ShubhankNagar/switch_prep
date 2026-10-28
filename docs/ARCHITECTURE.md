# Architecture

```text
┌──────────────────────────── Browser ────────────────────────────┐
│ Angular 20 SPA (hash routing)                                    │
│                                                                  │
│  pages/*  ──►  ContentService ──► GET content/*.json (static)    │
│     │                                                            │
│     ├──────►  ProgressService (signals)                          │
│     │           │  signed out: localStorage "switchprep.v1"      │
│     │           │  signed in:  "switchprep.v1.user.{id}"         │
│     └──────►  HabitService (daily routine, derives auto habits   │
│                 │  from progress; "switchprep.habits.v1[.user.{id}]")│
│                 │  signed in: write-through, queued while ─┐     │
│                 │  the API is unreachable                  │     │
└─────────────────┼──────────────────────────────────────┼─────────┘
                  │                                      ▼
                  │                    ┌──────── Spring Boot API ────────┐
                  │                    │ JwtAuthFilter → controllers      │
                  │                    │ auth / me / progress / quiz /    │
                  │                    │ stats  →  JPA repositories       │
                  │                    └───────────────┬─────────────────┘
                  │                                    ▼
                  │                         H2 (dev)  or  MySQL (prod)
```

## Design decisions

| Decision | Why |
|---|---|
| Content as static JSON in `frontend/public/content` | Content is read-only, versioned in git, cacheable, and the site works with no backend (GitHub Pages). |
| Backend stores only user data (progress, quiz attempts, activity) | Keeps the API small; content changes need no DB migration. |
| Progress keyed by string (`dsa:two-sum`) | One generic table covers every section; new content needs no schema change. |
| Two modes (local / server) in one `ProgressService` | Works offline and on static hosting; logging in adds multi-device sync. |
| Hash routing | No server rewrite rules needed on GitHub Pages or when served from the Spring Boot jar. |
| Signals + `resource()` | Simple reactive state without NgRx; computed totals update instantly when you tick something. |
| JWT (stateless) | No server sessions; easy to scale and to call from the SPA. |
| Google sign-in verified by the API | The browser gets an ID token from Google's button and posts it to `/api/auth/google`; the API checks it locally against Google's public keys and then issues its own JWT. No client secret, no redirect flow, no server session. |
| Per-user local copy + queue | The API may be asleep on free hosting. The UI never waits for it: it shows the user's copy from the browser and sends queued changes when the API answers. |
| Runtime config in `public/config.js` | The API address and Google client ID are deployment facts, not code; one build works anywhere. |

## Frontend (`frontend/src/app`)

| Path | Responsibility |
|---|---|
| `core/models.ts` | TypeScript types for every content file and for progress/quiz data |
| `core/content.service.ts` | Loads and caches content JSON; merges split files (dsa-part1 + part2, etc.) |
| `core/catalog.service.ts` | `keys.*` (the progress-key contract) and a flat catalog of every trackable item (totals, revision list) |
| `core/progress.service.ts` | Progress state, local persistence, API sync, streak/activity, export/import, auth |
| `core/habit.service.ts` | Daily routine: habit definitions, per-day logs, streaks, focus timer. "Auto" habits are computed from progress `completedAt` timestamps (e.g. 2 DSA problems a day), so they tick themselves |
| `core/auth.interceptor.ts` | Adds `Authorization: Bearer` to `/api/**` calls |
| `core/api.config.ts` | `API_BASE` and `GOOGLE_CLIENT_ID`, read from `public/config.js` |
| `core/google-identity.ts` | Loads Google Identity Services and draws the Sign in with Google button |
| `core/sync.spec.ts` | Tests for the sync behaviour below (sleeping API, drop-outs, refusals, expired session) |
| `shared/markdown.pipe.ts` | `md` (markdown → HTML with highlighted code) and `code` (raw code → highlighted HTML) |
| `shared/quiz.ts` | MCQ runner: practice mode, timed exam mode, scoring, saves attempts |
| `shared/qa-list.ts` | Expandable Q&A with "I know this" / revise toggles |
| `shared/ui.ts` | Progress bar, done toggle, revise star, notes box, `link` pipe |
| `shared/trap-card.ts` | Guess-first trap card (commit to an answer, then reveal the common wrong answer and why) and `trapOfTheDay()` |
| `pages/*` | One component per route; see `app.routes.ts` |

### Progress keys

| Item | Key | Section |
|---|---|---|
| Plan task | `plan:d{day}:{taskId}` | plan |
| DSA problem | `dsa:{problemId}` | dsa |
| System design topic | `sd:{topicId}` | sd |
| Core note chapter | `note:{subjectId}:{noteId}` | core |
| Core question | `qa:{questionId}` | core |
| Final-round coding/theory | `fr:{itemId}` | final |
| Final-round MCQ test (quiz key) | `final:d{day}` | – |
| AI lesson / project | `ai:{lessonId}` / `ai:{moduleId}:project` | ai |
| AI lesson quiz (quiz key) | `ai-quiz:{lessonId}` | – |
| Trap | `trap:{trapId}` | traps |
| Interview round ("I'm ready for this round") | `round:{roundId}` | rounds |

Plan task ids are stable slugs generated by `build_plan.py` from the task's link (e.g. `dsa-dsa-arrays-hashing-two-sum`),
unique within a day, so regenerating the plan keeps ticks on tasks that are still scheduled on the same day.
(Before v1.1 the key used the task's position, `t{index}`; those old ticks no longer match.)
SD keys have no group, so system-design ids must be unique across all groups (the validator checks this).

### Sync (signed in)

`ProgressService.connection` is `local` (signed out), `connecting` or `online`.

- **Startup.** With a saved token, the user and their copy (`switchprep.v1.user.{id}`) are loaded from localStorage
  before any network call. The service then polls `/actuator/health` until the API answers (`waking` turns true
  after the first miss), sends queued changes, loads the account, and goes `online`.
- **Changes.** Online: sent at once. Otherwise: applied locally and queued (`pending` in the user's copy: item
  keys, quiz attempts, start date). A queued item is sent as its full current state.
- **Failures.** `reportSyncFailure` decides: a refusal (4xx such as an account limit) is shown and dropped; `401`
  signs out but keeps the queue in the user's copy for the next sign-in; anything else (API asleep, network) queues
  the change and starts reconnecting.
- **Loading never overwrites unsent changes:** keys still queued keep their local value.
- `HabitService` follows the same pattern with its own copy and queue (routine settings, changed days), driven by
  `ProgressService.online`.

Any new tracked feature must queue the same way; do not call the API directly from a page.

### Daily routine (habits)

`HabitService` keeps a list of `HabitDef`s (8 defaults, user-editable) and one `HabitDayLog` per date.
Kinds: `auto` (counts progress items completed that day whose key starts with one of `prefixes`; `countRevise` also
counts items starred for revision that day), `plan` (% of that day's plan tasks done), `count`, `check`, `minutes`
(study time, fed by the focus timer), `journal` (one line). A day is "complete" when ≥ 80% of active habits are met;
streaks count consecutive complete days (today doesn't break the streak until it's over). In local mode everything is
in localStorage; logged in, settings and logs sync through `/api/habits` and `/api/habit-logs`.

## Backend (`backend/src/main/java/com/switchprep`)

| Package | Contents |
|---|---|
| `config` | `SecurityConfig` (stateless JWT, CORS, public routes), `AppProperties` (`app.jwt.*`, `app.cors.*`, `app.auth.*`, `app.limits.*`; with `app.production` it refuses to start on missing settings) |
| `auth` | `AuthController` (register/login/google), `GoogleTokenVerifier` + `NimbusGoogleTokenVerifier`, `JwtService`, `JwtAuthFilter`, `CurrentUser` helper |
| `user` | `AppUser` entity, `MeController` (profile, journey start date, delete account) |
| `progress` | `ItemProgress` + `ActivityDay` entities, `ProgressService`, `ProgressController` (CRUD, import, reset) |
| `quiz` | `QuizAttempt` entity, `QuizController` |
| `stats` | `StatsController` (done counts per section, streaks, activity) |
| `habit` | `HabitSettings` + `HabitLog` entities, `HabitController` (routine settings, per-day logs) |
| `common` | `ApiExceptionHandler` (JSON errors), `RequestSizeLimitFilter` (caps request bodies) |

### Data model

```text
app_user(id, username UNIQUE, password_hash NULL, google_sub UNIQUE NULL, email NULL, display_name, start_date, created_at)
    password accounts: username + password_hash.  Google accounts: google_sub (identity), email (display), username "g:{google_sub}"
item_progress(id, user_id, item_key, section, done, revise, note TEXT, completed_at, updated_at)
    UNIQUE(user_id, item_key), INDEX(user_id, section)
quiz_attempt(id, user_id, quiz_key, score, total, answers_json TEXT, duration_seconds, taken_at)
activity_day(id, user_id, activity_date, actions)  UNIQUE(user_id, activity_date)
habit_settings(user_id PK, habits_json TEXT, updated_at)
habit_log(id, user_id, log_date, values_json TEXT, minutes, journal, updated_at)  UNIQUE(user_id, log_date)
```
Schema is managed by Hibernate `ddl-auto: update` (fine for a personal app; switch to Flyway if it grows).

## Content pipeline

`content-gen/*.py` scripts produce the JSON files. `build_plan.py` reads the other content files to schedule a
selective, high-yield subset into the 60 days (within a daily minute budget), and `build_focus.py` builds the
two-tier High-Yield Focus list, so re-run both after content changes. `validate_content.py` checks schemas, unique
ids, MCQ answers, that every plan / rounds / focus link resolves and that every focus key is a real progress key;
CI runs it. `content-gen/RESEARCH_2026.md` records the interview research the senior content is based on.
