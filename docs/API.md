# REST API

Base URL: same origin (`/api`). JSON in and out. All endpoints except `/api/auth/**` and `/actuator/health`
need `Authorization: Bearer <token>`. Errors look like `{"error": "message"}`.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/auth/register` | `{username, password, displayName?}` (username 3-50 chars `[a-zA-Z0-9_.-]`, password ≥ 6) | `201 {token, user}`; `409` if taken |
| POST | `/api/auth/login` | `{username, password}` | `{token, user}`; `401` if wrong |
| GET | `/api/me` | – | `{id, username, displayName, startDate}` |
| PUT | `/api/me` | `{displayName?, startDate?}` | updated user |
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
| GET | `/actuator/health` | – | `{status: "UP"}` (the UI uses this to detect the backend) |

JWTs are HS256, valid `APP_JWT_EXPIRATION_DAYS` (default 30) days.

Example:
```bash
TOKEN=$(curl -s localhost:8080/api/auth/register -H 'Content-Type: application/json' \
  -d '{"username":"raj","password":"secret123"}' | jq -r .token)
curl -s -X PUT localhost:8080/api/progress/dsa:two-sum -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"section":"dsa","done":true}'
curl -s localhost:8080/api/stats -H "Authorization: Bearer $TOKEN"
```
