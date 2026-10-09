# Deployment

## 1. GitHub Pages (free, frontend only)
Progress stays in the browser (use Export/Import to move between devices).
1. Push the repo to GitHub.
2. Repo **Settings → Pages → Source: GitHub Actions**.
3. The workflow `.github/workflows/pages.yml` builds `frontend/` and publishes it on every push to `main`.
   The app uses relative paths and hash routing, so it works under `https://<user>.github.io/<repo>/`.

## 2. Single container (UI + API)
```bash
docker build -t switchprep .
docker run -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=mysql \
  -e DB_URL='jdbc:mysql://<host>:3306/switchprep?createDatabaseIfNotExist=true' \
  -e DB_USERNAME=... -e DB_PASSWORD=... \
  -e APP_JWT_SECRET='<random string of 32+ characters>' \
  switchprep
```
Works on Render, Railway, Fly.io, AWS (ECS/App Runner/Elastic Beanstalk) or any VM. Without
`SPRING_PROFILES_ACTIVE=mysql` it uses an H2 file inside the container (lost when the container is replaced).

## 3. Split hosting
Host the Angular build on any static host and the API elsewhere. Before `main.js` loads, set the API URL:
```html
<script>window.SWITCHPREP_API = 'https://api.example.com';</script>
```
(add it to `frontend/src/index.html`) and allow the static host's origin on the API:
`APP_CORS_ORIGINS=https://<user>.github.io`.

## Environment variables (backend)
| Variable | Default | Purpose |
|---|---|---|
| `SPRING_PROFILES_ACTIVE` | `dev` (H2 file) | `mysql` for MySQL |
| `DB_URL`, `DB_USERNAME`, `DB_PASSWORD` | local MySQL root/root | MySQL connection |
| `APP_JWT_SECRET` | dev value | **Set in production** (32+ chars) |
| `APP_JWT_EXPIRATION_DAYS` | 30 | Token lifetime |
| `APP_CORS_ORIGINS` | `http://localhost:4200` | Comma-separated allowed origins |
