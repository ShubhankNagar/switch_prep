# REST API

Base URL: same origin (`/api`), or the address in `window.SWITCHPREP_API` when the site is hosted apart from the API.
JSON in and out. All endpoints except `/api/auth/**` and `/actuator/health/**` need `Authorization: Bearer <token>`.
Errors look like `{"error": "message"}`.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/auth/register` | `{username, password, displayName?}` (username 3-50 chars `[a-zA-Z0-9_.-]`, password ≥ 6) | `201 {token, user}`; `409` if taken |
| POST | `/api/auth/login` | `{username, password}` | `{token, user}`; `401` if wrong |
| POST | `/api/auth/google` | `{credential}`: the ID token from the Sign in with Google button | `{token, user}`, creating the account on first use; `401` if the token is not valid for this app; `503` if `APP_GOOGLE_CLIENT_ID` is not set |
| GET | `/api/me` | – | `{id, username, email?, displayName, startDate}` (`email` for Google accounts; their `username` is `g:<google id>`) |
| PUT | `/api/me` | `{displayName?, startDate?}` | updated user |
| DELETE | `/api/me` | – | `204`, deletes the account and everything stored for it; its tokens stop working |
| GET | `/api/progress` | – | `[{key, section, done, revise, note, completedAt, updatedAt}]` |
| PUT | `/api/progress/{key}` | `{section, done?, revise?, note?}` (partial update; `note: ""` clears) | the item |
| DELETE | `/api/progress/{key}` | – | `204` |
| POST | `/api/progress/import` | `[ProgressItem]` (merge: done/revise are OR-ed, notes overwrite) | `{imported: n}` |
| DELETE | `/api/progress` | – | `204`, deletes all progress, activity, quiz attempts and routine logs (habit settings are kept) |
| GET | `/api/quiz-attempts` | – | attempts, newest first |
| POST | `/api/quiz-attempts` | `{quizKey, score, total, answersJson?, durationSeconds?, takenAt?}` (`takenAt` only for imports) | `201` attempt |
| GET | `/api/stats` | – | `{doneBySection, totalDone, currentStreak, longestStreak, activity:[{date,count}]}` |
| GET | `/api/habits` | – | `{habitsJson, updatedAt}`; `204` if the user never customised their routine (UI uses defaults) |
| PUT | `/api/habits` | `{habitsJson}` (JSON array of habit definitions, ≤ 50 KB) | `{habitsJson, updatedAt}` |
| GET | `/api/habit-logs?from=YYYY-MM-DD&to=YYYY-MM-DD` | – (both params optional) | `[{date, valuesJson, minutes, journal, updatedAt}]`, oldest first |
| PUT | `/api/habit-logs/{date}` | `{valuesJson?, minutes? (0-1440), journal? (≤ 1000)}` (partial update) | the day's log |
| GET | `/actuator/health` | – | `{status: "UP"}` (the UI uses this to detect the backend and to wait for a sleeping one) |
| GET | `/actuator/health/liveness` | – | `{status: "UP"}` without touching the database (for the host's health check) |

`register` and `login` return `403` when password accounts are off (`APP_AUTH_PASSWORD_LOGIN=false`, always in the
`prod` profile).

Per-account limits (see DEPLOYMENT.md for the variables): creating a tracked item beyond the cap, exceeding the
total note size, or saving a quiz attempt beyond the cap returns `422`; a body over the request limit returns
`413`; an item key over 150 characters or a routine date more than 5 years back or 2 days ahead returns `400`.

JWTs are HS256, valid `APP_JWT_EXPIRATION_DAYS` (default 30) days.

Example:
```bash
TOKEN=$(curl -s localhost:8080/api/auth/register -H 'Content-Type: application/json' \
  -d '{"username":"raj","password":"secret123"}' | jq -r .token)
curl -s -X PUT localhost:8080/api/progress/dsa:two-sum -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"section":"dsa","done":true}'
curl -s localhost:8080/api/stats -H "Authorization: Bearer $TOKEN"
```
