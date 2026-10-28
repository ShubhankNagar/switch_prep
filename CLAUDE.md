# CLAUDE.md

Guidance for Claude (and any AI coding assistant) working in this repository.

## What this is

**SwitchPrep**: an all-in-one interview-prep website and progress tracker for one goal: a Java/Spring Boot/Angular
developer with 2 years at a service company switching to a product company (~15 LPA) in 60 days, followed by a
14-day "final round" of real previously-asked interview questions, plus a beginner-to-advanced AI engineer course.
Since v1.1 it targets the senior (SDE-2/senior) bar of 2026-27 loops: senior subjects, senior system design, common
traps, an interview-rounds guide, a High-Yield Focus list, and a daily-routine (habit) tracker.
The site is meant to be the owner's **only** prep source, so content lives inside the repo (written notes, Q&A,
solutions), not as bare links. The owner can't absorb everything, so **be selective**: the plan and focus list
schedule the high-yield subset; don't bloat them when adding content.

## Layout

```
frontend/   Angular 20 app (standalone components, signals, hash routing). All UI.
  public/content/*.json   ALL study content (DSA, system design, core + senior subjects, traps, rounds, final round,
                          AI course, plan, focus list, guide)
  public/config.js        runtime settings (API address, Google client ID); overwritten by the Pages workflow
  src/app/core/           models, ContentService (loads JSON), ProgressService (tracking + sync), CatalogService (progress keys),
                          HabitService (daily routine), google-identity (Sign in with Google button)
  src/app/shared/         reusable UI: markdown pipe, quiz runner, Q&A list, trap card, done/revise toggles, notes
  src/app/pages/          one file per route (inline templates; styles are global in src/styles.scss)
backend/    Spring Boot 3.5 / Java 21 API: Google + password sign-in (JWT), progress, quiz attempts, stats, habits.
            Profiles: dev (H2), mysql (local MySQL), prod (public deployment: Google only, settings from env).
content-gen/ Python generators for the content JSON + validate_content.py (RESEARCH_2026.md: interview research)
docs/       AI_CONTEXT.md (start here), ARCHITECTURE.md, CONTENT.md (JSON schemas), API.md, DEPLOYMENT.md,
            PRODUCTION_PLAN.md (go-live runbook)
scripts/build-all.sh   builds Angular into the Spring Boot jar
```

Read `docs/ARCHITECTURE.md` before structural changes and `docs/CONTENT.md` before touching content.

## Commands

```bash
# frontend (http://localhost:4200, proxies /api and /actuator to :8080)
cd frontend && npm install && npx ng serve
cd frontend && npx ng build                  # must pass with no errors
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless   # sync tests (core/sync.spec.ts)

# backend (http://localhost:8080, H2 file db in backend/data/)
cd backend && mvn spring-boot:run
cd backend && mvn spring-boot:run -Dspring-boot.run.profiles=mysql   # needs MySQL (docker compose up -d)
cd backend && mvn test

# content
python3 content-gen/validate_content.py      # run after ANY content change
python3 content-gen/build_plan.py            # regenerate the 60-day plan after changing any content ids/titles
python3 content-gen/build_focus.py           # regenerate the High-Yield Focus list (same rule)
python3 content-gen/build_guide.py           # regenerate the job switch guide
```

## Conventions

- **Progress keys are a contract.** They are built only in `frontend/src/app/core/catalog.service.ts` (`keys.*`) and
  stored in localStorage and the `item_progress` table. Renaming a content `id` or a key format orphans users'
  saved progress. Add new ids freely; don't rename existing ones. Plan task keys use each task's stable `id`
  (`plan:d{day}:{taskId}`); system-design ids must be unique across groups (`sd:{id}` has no group).
- **Two storage modes.** `ProgressService` works without a backend (localStorage) and, when logged in, writes through
  to the API. Any new tracked feature must work in both modes.
- **The API may be asleep.** Signed-in changes go through the queue in `ProgressService` / `HabitService`
  (`online()`, `reportSyncFailure`), never straight to `HttpClient` from a page. See "Sync" in ARCHITECTURE.md and
  keep `core/sync.spec.ts` passing.
- **Content is data, not code.** Add/modify content by editing the generator in `content-gen/` (or the JSON directly
  for small fixes), then run `validate_content.py`. Markdown is rendered with `marked` + highlight.js
  (java, python, sql, ts/js, bash, json, yaml, xml).
- Angular: standalone components, signals + `resource()` for async content, `input()` for route params
  (`withComponentInputBinding`), new control flow (`@if/@for`). Keep component files self-contained with inline
  templates; put CSS in `src/styles.scss` using the existing CSS variables (light/dark themes).
- Backend: package-by-feature (`auth`, `user`, `progress`, `quiz`, `stats`, `habit`), constructor injection, records for DTOs,
  no Lombok. Every endpoint under `/api/**` except `/api/auth/**` requires a JWT. Add a MockMvc test for new endpoints.
  Anything a user can create needs a per-account cap (`app.limits.*`): sign-in is open to any Google account.
- Secrets and deployment values never get defaults in the `prod` profile and never go in the repo.
- Write original explanations. Don't paste copyrighted problem statements or articles; paraphrase and link the source.
- Don't commit `node_modules`, `dist`, `target`, `backend/data` (see `.gitignore`).

## Gotchas

- `day` is a reserved word in H2; that's why `activity_day` uses the column `activity_date`.
- Spring leaves an unset `${VAR}` in a `@ConfigurationProperties` value as literal text instead of failing. `prod`
  therefore sets `app.production: true`, and `AppProperties` validates the settings itself.
- Google accounts have `username` `g:<google id>` (password usernames cannot contain `:`) and no password hash.
  Show `email`, not `username`, for them.
- Router uses hash URLs (`#/dsa/...`) so the build works on GitHub Pages and from the Spring Boot jar without rewrites.
- Content links in the plan can contain query strings (`/core/java?chapter=3`); render them with the `link` pipe
  (`[routerLink]="t.link | link"`), not a raw string.
- Final-round solutions are Java except a few day-4 SQL ones (start with `-- SQL`); `CodePipe` auto-detects SQL.
- "Auto" habits in the daily routine are derived from progress `completedAt` (and `updatedAt` for starred items), so
  un-ticking an item lowers that day's habit count. Plan-habit % uses the journey start date to map dates to plan days.
- The plan builder fills core subjects into a per-day minute budget in priority order; anything that doesn't fit is
  printed as "left optional". Check that output after content changes.
