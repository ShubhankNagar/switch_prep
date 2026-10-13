interface RuntimeConfig { SWITCHPREP_API?: string; SWITCHPREP_GOOGLE_CLIENT_ID?: string; }

// Set by public/config.js, which loads before the app.
const config = globalThis as RuntimeConfig;

/**
 * Base URL of the Spring Boot API. Empty string means "same origin": in development `ng serve`
 * proxies /api to http://localhost:8080 (see proxy.conf.json), and in the single-jar build the Angular
 * app is served by Spring Boot itself. When no backend is reachable (e.g. GitHub Pages without an API),
 * the app runs in browser-only mode and stores progress in localStorage.
 */
export const API_BASE = (config.SWITCHPREP_API ?? '').replace(/\/+$/, '');

/** OAuth client ID for Sign in with Google. Empty where it is not set up; the Account page then offers the password form. */
export const GOOGLE_CLIENT_ID = config.SWITCHPREP_GOOGLE_CLIENT_ID ?? '';
