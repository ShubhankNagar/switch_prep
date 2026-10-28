// Minimal typing for the part of Google Identity Services this app uses.
interface GoogleIdApi {
  initialize(options: { client_id: string; callback: (response: { credential: string }) => void }): void;
  renderButton(host: HTMLElement, options: Record<string, string | number>): void;
}

const SCRIPT_URL = 'https://accounts.google.com/gsi/client';

let script: Promise<GoogleIdApi> | undefined;
let onCredential: (credential: string) => void = () => undefined;

function load(clientId: string): Promise<GoogleIdApi> {
  script ??= new Promise<GoogleIdApi>((resolve, reject) => {
    const el = document.createElement('script');
    el.src = SCRIPT_URL;
    el.async = true;
    el.onload = () => {
      const api = (globalThis as { google?: { accounts: { id: GoogleIdApi } } }).google?.accounts.id;
      if (!api) return reject(new Error('Google sign-in did not load.'));
      // initialise once per page; the handler is swapped through onCredential
      api.initialize({ client_id: clientId, callback: response => onCredential(response.credential) });
      resolve(api);
    };
    el.onerror = () => {
      script = undefined; // let a later visit to the page try again
      reject(new Error('Could not load Google sign-in. Check your connection, or an ad blocker may be stopping it.'));
    };
    document.head.appendChild(el);
  });
  return script;
}

/**
 * Draws the "Sign in with Google" button inside `host`. `handler` receives the ID token ("credential") after the
 * user picks an account; the API verifies it (POST /api/auth/google).
 */
export async function renderGoogleButton(host: HTMLElement, clientId: string, handler: (credential: string) => void,
                                         dark: boolean): Promise<void> {
  const api = await load(clientId);
  onCredential = handler;
  api.renderButton(host, { type: 'standard', theme: dark ? 'filled_black' : 'outline', size: 'large', text: 'signin_with', shape: 'rectangular' });
}
