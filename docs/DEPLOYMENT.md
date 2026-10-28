# Deployment

To put the site live for free with Google sign-in, follow the step-by-step [go-live runbook](PRODUCTION_PLAN.md).
This page is the reference: the hosting options, every setting, and what changes between them.

## 1. GitHub Pages (free, frontend only)
Progress stays in the browser (use Export/Import to move between devices).
1. Push the repo to GitHub.
2. Repo **Settings → Pages → Source: GitHub Actions**.
3. The workflow `.github/workflows/pages.yml` builds `frontend/` and publishes it on every push to `main`.
   The app uses relative paths and hash routing, so it works under `https://<user>.github.io/<repo>/`.

## 2. Split hosting: static site + API (the free public setup)
The site stays on a static host and talks to the API on another origin. This is what the runbook sets up:
GitHub Pages + the API on Render (`Dockerfile.api`, `render.yaml`) + TiDB Cloud or any MySQL.

- **Site → API.** `frontend/public/config.js` is loaded before the app and sets `window.SWITCHPREP_API` (the API
  address) and `window.SWITCHPREP_GOOGLE_CLIENT_ID`. The Pages workflow writes it from the repository variables
  `SWITCHPREP_API_URL` and `SWITCHPREP_GOOGLE_CLIENT_ID`. Both unset means a browser-only site.
- **API → site.** Set `APP_CORS_ORIGINS` to the site's origin, for example `https://<user>.github.io`.
- **Profile.** Run the API with `SPRING_PROFILES_ACTIVE=prod`: database and secrets come only from the
  environment, password accounts are off (Google only), the H2 console does not exist, and the app refuses to
  start if `APP_JWT_SECRET`, `APP_GOOGLE_CLIENT_ID` or `APP_CORS_ORIGINS` is missing.
- **A sleeping API is fine.** Free hosts stop an idle service. A signed-in user sees their own copy from the
  browser at once; changes are queued and sent when the API answers (see ARCHITECTURE.md, "Sync").

## 3. Single container (UI + API)
```bash
docker build -t switchprep .
docker run -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=mysql \
  -e DB_URL='jdbc:mysql://<host>:3306/switchprep?createDatabaseIfNotExist=true' \
  -e DB_USERNAME=... -e DB_PASSWORD=... \
  -e APP_JWT_SECRET='<random string of 32+ characters>' \
  switchprep
```
Works on any Docker host or VM. Without a profile it uses an H2 file inside the container (lost when the container
is replaced). The `mysql` profile keeps username + password accounts; use `prod` for a public site. On a host that
sleeps, prefer option 2, where only sync waits for the wake-up and not the whole site.

## Environment variables (backend)
| Variable | Default | Purpose |
|---|---|---|
| `SPRING_PROFILES_ACTIVE` | `dev` (H2 file) | `mysql` for local MySQL, `prod` for a public deployment |
| `PORT` | `8080` | Port to listen on (set by hosts such as Render) |
| `DB_URL`, `DB_USERNAME`, `DB_PASSWORD` | `mysql`: local root/root. `prod`: none, required | Database connection. TiDB Cloud: `jdbc:mysql://<host>:4000/switchprep?sslMode=VERIFY_IDENTITY` |
| `APP_JWT_SECRET` | dev value. `prod`: none, required | Signs login tokens. Random, 32+ characters |
| `APP_JWT_EXPIRATION_DAYS` | 30 | Token lifetime |
| `APP_CORS_ORIGINS` | `http://localhost:4200`. `prod`: none, required | Comma-separated allowed site origins (no wildcards in `prod`) |
| `APP_GOOGLE_CLIENT_ID` | empty (Google sign-in off). `prod`: required | OAuth client ID from Google Cloud console |
| `APP_AUTH_PASSWORD_LOGIN` | `true`; always `false` in `prod` | Username + password accounts |
| `APP_MAX_PROGRESS_ITEMS` | 5000 | Tracked items per account |
| `APP_MAX_NOTE_CHARS_TOTAL` | 2000000 | Total size of one account's notes |
| `APP_MAX_QUIZ_ATTEMPTS` | 2000 | Saved quiz attempts per account |
| `APP_MAX_REQUEST_BYTES` | 2097152 | Largest request body accepted |

## Upgrading a database created before Google sign-in
Google accounts have no password, so `app_user.password_hash` became optional. Hibernate adds the new columns by
itself but does not relax an existing NOT NULL. For a local H2 database, delete `backend/data/`. For MySQL:
```sql
ALTER TABLE app_user MODIFY password_hash VARCHAR(255) NULL;
```
A new database needs nothing.
