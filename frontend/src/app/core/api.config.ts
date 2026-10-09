/**
 * Base URL of the Spring Boot API. Empty string means "same origin": in development `ng serve`
 * proxies /api to http://localhost:8080 (see proxy.conf.json), and in production the Angular build
 * is served by Spring Boot itself. When no backend is reachable (e.g. GitHub Pages), the app runs
 * in browser-only mode and stores progress in localStorage.
 */
export const API_BASE = (globalThis as { SWITCHPREP_API?: string }).SWITCHPREP_API ?? '';
