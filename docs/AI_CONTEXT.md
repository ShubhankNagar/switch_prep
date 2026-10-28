# AI context: SwitchPrep in one file

Read this first instead of exploring the repo. It is a compressed map: what the project is for, where everything
lives, the contracts you must not break, and the state of the work to take it public. Deeper detail is in
`CLAUDE.md` (conventions), `docs/ARCHITECTURE.md`, `docs/CONTENT.md` (JSON schemas), `docs/API.md`,
`docs/DEPLOYMENT.md` (settings) and `docs/PRODUCTION_PLAN.md` (go-live runbook).

Last verified against the code: 2026-10-28, branch `feat/shubhank` (commit `4efdf16`, pushed to the fork, on top of `2196c09`).

## 1. Why it exists

SwitchPrep is a self-contained interview-prep site and progress tracker. The target learner is a Java / Spring Boot /
Angular developer with about 2 years at a service company who wants to move to a product company (~15 LPA) in 60
days, at the senior (SDE-2) bar of 2026-27 interview loops. Three ideas drive every design choice:

1. **One source.** All study material (notes, Q&A, solutions) is written into the repo, so the learner never has to
   leave the site. External links are for practice and credit only.
2. **Selective, not exhaustive.** A 60-day plan and a two-tier "High-Yield Focus" list schedule the subset that is
   asked most. Adding content must not bloat those two.
3. **Consistency is tracked.** Done/revise flags, notes, quiz scores, streaks and a daily-routine (habit) tracker
   show exactly where the learner stands.

After day 60 comes a 14-day "final round" of real reported interview questions. A 14-module AI engineer course is an
optional parallel track.

## 2. Repository facts

| Fact | Value |
|---|---|
| Local path | `~/Shubhank Codes/Learning website/switch_prep` (the parent folder is not a git repo) |
| Remotes | `origin` = `github.com/ShubhankNagar/switch_prep` (the local user's fork; **deploy from here**, site at `https://shubhanknagar.github.io/switch_prep/`) · `upstream` = `github.com/raj-alpha-swain/switch_prep` (the partner's original, public, no LICENSE) |
| People | raj-alpha-swain wrote the first commit and is the local user's project partner. The local user is Shubhank Nagar, working on `feat/shubhank` |
| Size | ~17 MB: 4.7 MB content JSON, 6.7 MB Python generators, ~4,400 lines TypeScript, ~2,000 lines Java (tests included) |
| Toolchain required | Node >= 20.19 (CI uses 22), JDK 21, Maven 3.9, Python 3 |

## 3. Stack and layout

```
frontend/                 Angular 20, standalone components, signals, hash routing, no NgRx, no UI library
  public/content/*.json   19 files, ALL study content (static, fetched on first use, cached in memory)
  public/config.js        runtime settings: API address + Google client ID (Pages workflow overwrites it)
  public/privacy.html     static privacy page (linked from the Account page and Google's consent screen)
  src/app/core/           models.ts (types) · content.service.ts (load + merge split files)
                          catalog.service.ts (keys.* = progress-key contract, flat catalog)
                          progress.service.ts (state, per-user localStorage copy, sync queue, auth, export/import)
                          habit.service.ts (daily routine, auto habits, focus timer, its own copy + queue)
                          api.config.ts (API_BASE, GOOGLE_CLIENT_ID) · auth.interceptor.ts (Bearer token)
                          google-identity.ts (Sign in with Google button) · sync.spec.ts (11 sync tests)
  src/app/shared/         markdown.pipe.ts (marked + highlight.js) · quiz.ts · qa-list.ts · trap-card.ts · ui.ts
  src/app/pages/          23 route components, inline templates; all CSS is global in src/styles.scss
backend/                  Spring Boot 3.5.6, Java 21, package-by-feature under com.switchprep
  auth/ user/ progress/ quiz/ stats/ habit/ config/ common/     no Lombok, records for DTOs
  src/test/...                                                  25 tests: ApiFlowTest (flows), PublicDeploymentRulesTest
                                                                (prod switches + per-account caps),
                                                                NimbusGoogleTokenVerifierTest (real token check)
content-gen/              141 Python generators + validate_content.py + RESEARCH_2026.md
docs/                     ARCHITECTURE, CONTENT, API, DEPLOYMENT, this file, PRODUCTION_PLAN
.github/workflows/        ci.yml (mvn test, ng build, ng test, validate content) · pages.yml (site to GitHub Pages on main)
Dockerfile                3-stage: builds Angular, packs it into the Spring Boot jar, runs on :8080
Dockerfile.api            API only, sized for a 512 MB host · render.yaml (Render Blueprint for it)
docker-compose.yml        local MySQL 8.4 only
scripts/build-all.sh      same as the Dockerfile but local
```

## 4. How it runs

```
Browser (Angular SPA)
  ContentService  -> GET content/*.json           static, no backend involved
  ProgressService -> signed out: localStorage "switchprep.v1"
                     signed in:  localStorage "switchprep.v1.user.{id}" + REST, queued while the API is unreachable
  HabitService    -> same pattern, "switchprep.habits.v1[.user.{id}]"
        |
        v  (optional) Spring Boot API, stateless JWT (HS256, 30 days)
           /api/auth/{google,register,login}  /api/me  /api/progress  /api/quiz-attempts  /api/stats
           /api/habits  /api/habit-logs  /actuator/health[/liveness]
        v
     H2 file (profile dev, default) · local MySQL (profile mysql) · MySQL or TiDB Cloud (profile prod)
     schema by Hibernate ddl-auto=update
```

Two modes, one service: **local** (no backend, everything in the browser) and **server** (signed in). The site is
fully usable in local mode; the backend only adds accounts and cross-device sync.

Sign-in: in production Google only. The browser gets an ID token from Google's button, `POST /api/auth/google`
verifies it against Google's keys and issues the app's JWT. Username + password accounts exist for local
development and are off in the `prod` profile.

The API may be asleep (free hosting). A signed-in user is shown their browser copy immediately,
`ProgressService.connection` is `connecting` until `/actuator/health` answers, and changes made meanwhile are
queued and sent on reconnect. Details: "Sync" in ARCHITECTURE.md.

Tables: `app_user`, `item_progress` (unique user_id+item_key), `quiz_attempt`, `activity_day`, `habit_settings`,
`habit_log`. All user data is small text; there is no content in the database. Per-account caps: `app.limits.*`.

## 5. Content inventory (validator output, 2026-10-13: "All content valid")

| Area | Count | Files |
|---|---|---|
| DSA | 17 patterns, 171 problems (75 must-do), Java solutions | `dsa-part1/2.json` |
| System design | 22 HLD concepts, 15 HLD case studies, 8 LLD fundamentals, 18 LLD problems, 13 senior topics | `system-design-{hld,lld,senior}.json` |
| Core subjects | 19 subjects, 166 note chapters, 682 Q&A (11 classic + 8 senior-2027 subjects) | `core-{backend,cs,senior-1,senior-2}.json` |
| Common traps | 117 | `traps-1/2.json` |
| Interview rounds | 13 round playbooks + trends | `rounds.json` |
| Final round | 14 days: 280 MCQs, 56 coding, 84 verbal | `final-round-1/2.json` |
| AI course | 14 modules, 92 lessons, 14 projects | `ai-course-1/2.json` |
| Plan / focus / guide | 60 days and 487 tasks / 217 tier-1 + 290 tier-2 items / 9 sections | `plan.json`, `focus.json`, `guide.json` |

About 1,960 trackable items per user, so one user's progress is at most ~2,000 small rows.

## 6. Contracts you must not break

- **Progress keys** are built only in `catalog.service.ts` (`keys.*`): `plan:d{day}:{taskId}`, `dsa:{id}`, `sd:{id}`,
  `note:{subject}:{id}`, `qa:{id}`, `fr:{id}`, `ai:{id}`, `ai:{module}:project`, `trap:{id}`, `round:{id}`; quiz keys
  `final:d{day}` and `ai-quiz:{lessonId}`. They are stored in localStorage and in `item_progress.item_key`. Never
  rename an existing content `id` or key format: it orphans saved progress. System-design ids are unique across all
  groups.
- **Both storage modes** must keep working for any tracked feature.
- **Content is data.** Change the generator in `content-gen/` (or the JSON for small fixes), then run
  `python3 content-gen/validate_content.py`; if ids or titles changed, also `build_plan.py` and `build_focus.py`.
- **REST shapes** in `docs/API.md` are used by `progress.service.ts` and `habit.service.ts`; change both sides together
  and add a MockMvc test.
- Angular: standalone components, signals + `resource()`, `input()` route params, `@if/@for`, CSS variables in
  `styles.scss`. Backend: constructor injection, records, no Lombok.
- Write original explanations; paraphrase problem statements and link the source.

## 7. Commands

```bash
cd frontend && npm install && npx ng serve       # http://localhost:4200, proxies /api and /actuator to :8080
cd frontend && npx ng build                      # must pass with no errors
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless
cd backend && mvn spring-boot:run                # http://localhost:8080, H2 file DB in backend/data/
cd backend && mvn test
python3 content-gen/validate_content.py          # after any content change
```

## 8. Public deployment: state on 2026-10-13

Target (chosen by the owner): GitHub Pages (site) + Render free web service (API, `prod` profile) + TiDB Cloud
Starter (database) + Google sign-in, open to any Google account, no keep-alive pinger. The runbook is
`docs/PRODUCTION_PLAN.md`.

Everything is deployed from the fork (`origin`), not the partner's repo. Code for it is complete on `feat/shubhank`,
tested locally, committed and pushed to the fork. **Not yet done:** merge to the fork's `main`, and the
account setup (Google OAuth client, TiDB instance, Render service, two GitHub repository variables).
**Not yet proven**, because they need those services: a real Google sign-in, the API against TiDB, the Docker
build on Render, the real wake-up time, and the changed GitHub workflows.

Review findings and what became of them:

| Finding | Status |
|---|---|
| Real-looking MySQL password committed as a default (`application.yml`) | Removed from the file. Still in git history: whoever uses it should change it |
| No production profile; H2 console reachable without auth | `prod` profile added; console only permitted where it is enabled (dev) |
| JWT secret silently falls back to a dev value | `prod` refuses to start without a real one (`AppProperties`) |
| Open, unthrottled registration; unlimited rows per user | Password accounts off in `prod`; per-account caps and a request size limit |
| No Google sign-in, no account deletion | `POST /api/auth/google`, `DELETE /api/me` |
| Sleeping backend silently dropped a signed-in user to anonymous mode; local mirror written but never read | Per-user copy loaded at startup, sync queue, reconnect loop; covered by `core/sync.spec.ts` |
| API URL had to be hand-edited into `index.html` | `public/config.js`, written by the Pages workflow from repository variables |
| `activity_day` uses the server's date (UTC) while the UI uses the browser's | Open, cosmetic: the UI does not call `/api/stats` |
| No LICENSE file | Open: the owners should add one |

Not problems: user notes are plain text in a textarea, and Markdown is only rendered from the repo's own content
through Angular's sanitiser, so there is no stored-XSS path from user input.
