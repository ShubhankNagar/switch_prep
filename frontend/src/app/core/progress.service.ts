import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { Observable, firstValueFrom, timeout } from 'rxjs';
import { API_BASE } from './api.config';
import { TOKEN_KEY } from './auth.interceptor';
import { HabitData, ProgressItem, QuizAttempt, Section, User } from './models';

const STORAGE_KEY = 'switchprep.v1';
/** The signed-in user, remembered so their progress can be shown before the server answers. */
const USER_KEY = 'switchprep.user';

const NOT_CONNECTED = 'Not connected to the server yet. Try again in a minute.';
/** How long a sign-in waits for a sleeping server before giving up. */
const SIGN_IN_WAIT_MS = 5 * 60 * 1000;

/** Changes made while signed in that the server has not confirmed yet. */
interface PendingChanges { keys: string[]; attempts: QuizAttempt[]; startDate: boolean; }

interface LocalState {
  startDate: string;
  items: Record<string, ProgressItem>;
  attempts: QuizAttempt[];
  theme?: 'light' | 'dark';
  /** Only in a signed-in user's copy. */
  pending?: PendingChanges;
}

export interface ExportFile {
  app: 'switchprep';
  version: 1;
  exportedAt: string;
  startDate: string;
  items: ProgressItem[];
  attempts: QuizAttempt[];
  /** Daily routine (added in v1.1; optional so older files still import). */
  habits?: HabitData;
}

export const todayIso = () => toIso(new Date());
export function toIso(d: Date): string {
  const tz = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - tz).toISOString().slice(0, 10);
}

const sleep = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms));
const isUnauthorized = (e: unknown) => e instanceof HttpErrorResponse && e.status === 401;
/** The server understood the request and said no (bad input, account limit). Retrying will not help. */
const isRefusal = (e: unknown) =>
  e instanceof HttpErrorResponse && e.status >= 400 && e.status < 500 && ![401, 408, 429].includes(e.status);

/**
 * Single source of truth for the user's progress. Works in two modes:
 * - local: everything lives in localStorage (no backend needed)
 * - server: signed in to the Spring Boot API. Every change is written through to the API and mirrored in
 *   localStorage per user, so the UI loads instantly.
 *
 * The API may be asleep (free hosting stops it when idle). A signed-in user then sees their mirrored copy at
 * once while `connection` is 'connecting'; changes made meanwhile are queued and sent when the API answers.
 */
@Injectable({ providedIn: 'root' })
export class ProgressService {
  private http = inject(HttpClient);

  readonly items = signal<Record<string, ProgressItem>>({});
  readonly attempts = signal<QuizAttempt[]>([]);
  readonly startDate = signal<string>(todayIso());
  readonly theme = signal<'light' | 'dark'>('light');
  readonly user = signal<User | null>(null);
  readonly backendAvailable = signal(false);
  readonly syncError = signal<string | null>(null);
  readonly mode = computed(() => (this.user() ? 'server' : 'local'));

  /** 'local' when signed out. Signed in: 'connecting' until the API has answered and is in step, then 'online'. */
  readonly connection = signal<'local' | 'connecting' | 'online'>('local');
  readonly online = computed(() => this.connection() === 'online');
  /** The API did not answer straight away, so it is probably waking from sleep. */
  readonly waking = signal(false);

  private pendingKeys = signal<string[]>([]);
  private pendingAttempts = signal<QuizAttempt[]>([]);
  private pendingStartDate = signal(false);
  /** Number of changes waiting to be sent to the server. */
  readonly pendingCount = computed(() =>
    this.pendingKeys().length + this.pendingAttempts().length + (this.pendingStartDate() ? 1 : 0));

  private connecting?: Promise<void>;

  /** Day number in the 74-day journey (1-60 study plan, 61-74 final round). */
  readonly currentDay = computed(() => {
    const start = new Date(this.startDate() + 'T00:00:00');
    const now = new Date(todayIso() + 'T00:00:00');
    return Math.max(1, Math.floor((now.getTime() - start.getTime()) / 86400000) + 1);
  });

  /** Count of completions per calendar day (from item completion times and quiz attempts). */
  readonly activity = computed(() => {
    const map = new Map<string, number>();
    const add = (iso?: string | null) => {
      if (!iso) return;
      const day = toIso(new Date(iso));
      map.set(day, (map.get(day) ?? 0) + 1);
    };
    Object.values(this.items()).forEach(i => i.done && add(i.completedAt));
    this.attempts().forEach(a => add(a.takenAt));
    return map;
  });

  readonly streak = computed(() => {
    const act = this.activity();
    const d = new Date();
    if (!act.has(toIso(d))) d.setDate(d.getDate() - 1);
    let n = 0;
    while (act.has(toIso(d))) {
      n++;
      d.setDate(d.getDate() - 1);
    }
    return n;
  });

  constructor() {
    this.loadLocal();
    this.resumeSession();
    effect(() => this.saveLocal());
    effect(() => document.documentElement.setAttribute('data-theme', this.theme()));
    void this.init();
  }

  // ---------- queries ----------

  isDone(key: string): boolean { return !!this.items()[key]?.done; }
  isRevise(key: string): boolean { return !!this.items()[key]?.revise; }
  note(key: string): string { return this.items()[key]?.note ?? ''; }

  countDone(keys: string[]): number {
    const items = this.items();
    return keys.reduce((n, k) => n + (items[k]?.done ? 1 : 0), 0);
  }

  doneInSection(section: Section): number {
    return Object.values(this.items()).filter(i => i.section === section && i.done).length;
  }

  bestAttempt(quizKey: string): QuizAttempt | undefined {
    return this.attempts()
      .filter(a => a.quizKey === quizKey)
      .sort((a, b) => b.score / b.total - a.score / a.total)[0];
  }

  /** Items saved in this browser while signed out (offered for upload after signing in). */
  offlineItemCount(): number {
    return Object.keys(this.readLocal(STORAGE_KEY)?.items ?? {}).length;
  }

  // ---------- mutations ----------

  toggleDone(key: string, section: Section): void {
    this.update(key, section, { done: !this.isDone(key) });
  }

  toggleRevise(key: string, section: Section): void {
    this.update(key, section, { revise: !this.isRevise(key) });
  }

  setNote(key: string, section: Section, note: string): void {
    this.update(key, section, { note });
  }

  update(key: string, section: Section, patch: { done?: boolean; revise?: boolean; note?: string }): void {
    const now = new Date().toISOString();
    const prev = this.items()[key] ?? { key, section, done: false, revise: false };
    const next: ProgressItem = { ...prev, section, updatedAt: now };
    if (patch.done !== undefined) {
      next.done = patch.done;
      next.completedAt = patch.done ? prev.completedAt ?? now : null;
    }
    if (patch.revise !== undefined) next.revise = patch.revise;
    if (patch.note !== undefined) next.note = patch.note;
    this.items.update(all => ({ ...all, [key]: next }));

    if (this.mode() !== 'server') return;
    if (!this.online()) {
      this.queueKey(key);
      return;
    }
    this.http.put(`${API_BASE}/api/progress/${encodeURIComponent(key)}`, { section, ...patch })
      .subscribe({ error: e => this.reportSyncFailure(e, () => this.queueKey(key)) });
  }

  addAttempt(attempt: Omit<QuizAttempt, 'takenAt'>): void {
    const full: QuizAttempt = { ...attempt, takenAt: new Date().toISOString() };
    this.attempts.update(list => [full, ...list]);
    if (this.mode() !== 'server') return;
    if (!this.online()) {
      this.pendingAttempts.update(list => [...list, full]);
      return;
    }
    const { takenAt: _ignored, ...body } = full;
    this.http.post(`${API_BASE}/api/quiz-attempts`, body).subscribe({
      error: e => this.reportSyncFailure(e, () => this.pendingAttempts.update(list => [...list, full])),
    });
  }

  setStartDate(date: string): void {
    this.startDate.set(date);
    if (this.mode() !== 'server') return;
    if (!this.online()) {
      this.pendingStartDate.set(true);
      return;
    }
    this.http.put<User>(`${API_BASE}/api/me`, { startDate: date }).subscribe({
      next: u => this.rememberUser(u),
      error: e => this.reportSyncFailure(e, () => this.pendingStartDate.set(true)),
    });
  }

  toggleTheme(): void {
    this.theme.update(t => (t === 'dark' ? 'light' : 'dark'));
  }

  // ---------- auth ----------

  async login(username: string, password: string): Promise<void> {
    await this.authenticate('login', { username, password });
  }

  async register(username: string, password: string, displayName: string): Promise<void> {
    await this.authenticate('register', { username, password, displayName });
  }

  /** `credential` is the ID token from the Sign in with Google button. */
  async loginWithGoogle(credential: string): Promise<void> {
    await this.authenticate('google', { credential });
  }

  /**
   * Signs out on this device. Changes still waiting for the server stay in this browser's copy for the account
   * and are sent the next time the same account signs in here.
   */
  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.user.set(null);
    this.connection.set('local');
    this.waking.set(false);
    this.pendingKeys.set([]);
    this.pendingAttempts.set([]);
    this.pendingStartDate.set(false);
    this.loadLocal();
  }

  /** Deletes the account and everything stored for it on the server, then signs out. */
  async deleteAccount(): Promise<void> {
    const user = this.user();
    if (!user || !this.online()) throw new Error(NOT_CONNECTED);
    await firstValueFrom(this.http.delete(`${API_BASE}/api/me`));
    localStorage.removeItem(`${STORAGE_KEY}.user.${user.id}`);
    this.logout();
  }

  /** Uploads progress made in browser-only mode to the logged-in account. */
  async uploadLocalToAccount(): Promise<number> {
    if (!this.online()) throw new Error(NOT_CONNECTED);
    const local = this.readLocal(STORAGE_KEY);
    if (!local) return 0;
    return this.pushToServer(Object.values(local.items), local.attempts);
  }

  // ---------- export / import / reset ----------

  exportData(): ExportFile {
    return {
      app: 'switchprep', version: 1, exportedAt: new Date().toISOString(), startDate: this.startDate(),
      items: Object.values(this.items()), attempts: this.attempts(),
    };
  }

  async importData(file: ExportFile): Promise<number> {
    if (file.app !== 'switchprep' || !Array.isArray(file.items)) throw new Error('Not a SwitchPrep export file');
    const merged = { ...this.items() };
    for (const it of file.items) {
      const cur = merged[it.key];
      merged[it.key] = cur
        ? { ...cur, done: cur.done || it.done, revise: cur.revise || it.revise, note: it.note || cur.note,
            completedAt: cur.completedAt ?? it.completedAt }
        : it;
    }
    this.items.set(merged);
    const seen = new Set(this.attempts().map(a => a.quizKey + a.takenAt));
    const newAttempts = (file.attempts ?? []).filter(a => !seen.has(a.quizKey + a.takenAt));
    this.attempts.update(list => [...newAttempts, ...list]);
    if (file.startDate) this.setStartDate(file.startDate);
    if (this.mode() === 'server') {
      if (this.online()) {
        await this.pushToServer(file.items, newAttempts);
      } else {
        file.items.forEach(it => this.queueKey(it.key));
        this.pendingAttempts.update(list => [...list, ...newAttempts]);
      }
    }
    return file.items.length;
  }

  async reset(): Promise<void> {
    if (this.mode() === 'server') {
      if (!this.online()) throw new Error(NOT_CONNECTED);
      await firstValueFrom(this.http.delete(`${API_BASE}/api/progress`));
    }
    this.items.set({});
    this.attempts.set([]);
    this.pendingKeys.set([]);
    this.pendingAttempts.set([]);
  }

  // ---------- sync ----------

  /**
   * Call when sending a change to the API fails. If the server rejected it, the user is told and 'refused' is
   * returned (retrying will not help). Otherwise the server could not be reached or the session ended: `requeue`
   * is run so the change is kept, a reconnect starts, and 'retry' is returned. Queued changes are sent when the
   * reconnect, or the next sign-in, succeeds.
   */
  reportSyncFailure(e: unknown, requeue: () => void = () => undefined): 'refused' | 'retry' {
    if (isRefusal(e)) {
      this.syncError.set((e as HttpErrorResponse).error?.error ?? 'The server did not accept that change.');
      return 'refused';
    }
    requeue();
    if (isUnauthorized(e)) this.sessionExpired();
    else void this.connect();
    return 'retry';
  }

  private queueKey(key: string): void {
    this.pendingKeys.update(keys => (keys.includes(key) ? keys : [...keys, key]));
  }

  /** Shows the signed-in user's own copy straight away, before any network call. */
  private resumeSession(): void {
    if (!localStorage.getItem(TOKEN_KEY)) return;
    const user = this.readJson<User>(USER_KEY);
    if (!user) return; // signed in before the user was remembered: init() loads everything from the server
    this.user.set(user);
    this.restoreMirror(user);
  }

  private async init(): Promise<void> {
    if (localStorage.getItem(TOKEN_KEY)) {
      await this.connect();
      return;
    }
    // Signed out: one quick look tells the Account page whether an API exists. It also starts waking a sleeping one.
    this.backendAvailable.set(await this.ping(3000));
  }

  /** Brings a signed-in session in step with the API, waiting for it to wake if needed. Safe to call repeatedly. */
  private connect(): Promise<void> {
    this.connecting ??= this.runConnect().finally(() => (this.connecting = undefined));
    return this.connecting;
  }

  private async runConnect(): Promise<void> {
    const signedIn = () => !!localStorage.getItem(TOKEN_KEY);
    for (let failures = 0; ; failures++) {
      if (!signedIn()) return;
      this.connection.set('connecting');
      if (!(await this.waitForServer(signedIn))) return; // signed out while waiting
      try {
        // send first so the reload does not overwrite local changes; repeat if more were made meanwhile
        do {
          await this.flushPending();
          await this.loadFromServer();
        } while (this.pendingCount() > 0 && signedIn());
        if (!signedIn()) return;
        this.connection.set('online');
        this.waking.set(false);
        return;
      } catch (e) {
        if (isUnauthorized(e)) {
          this.sessionExpired();
          return;
        }
        await sleep(Math.min(5000 * 2 ** failures, 60000)); // the API went away again mid-sync: start over
      }
    }
  }

  /** Polls until the API answers. Resolves false if `stillWanted` turns false or `maxMs` runs out. */
  private async waitForServer(stillWanted: () => boolean, maxMs = Infinity): Promise<boolean> {
    const started = Date.now();
    for (let attempt = 0; stillWanted(); attempt++) {
      if (await this.ping(10000)) {
        this.backendAvailable.set(true);
        return true;
      }
      if (Date.now() - started > maxMs) return false;
      this.waking.set(true);
      await sleep(Math.min(3000 + attempt * 2000, 15000));
    }
    return false;
  }

  private async ping(ms: number): Promise<boolean> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ status?: string }>(`${API_BASE}/actuator/health`).pipe(timeout(ms)));
      return res?.status === 'UP';
    } catch {
      return false;
    }
  }

  private async flushPending(): Promise<void> {
    if (this.pendingStartDate()) {
      await this.deliver(this.http.put(`${API_BASE}/api/me`, { startDate: this.startDate() }));
      this.pendingStartDate.set(false);
    }
    for (const key of this.pendingKeys()) {
      const it = this.items()[key];
      if (it) {
        await this.deliver(this.http.put(`${API_BASE}/api/progress/${encodeURIComponent(key)}`,
          { section: it.section, done: it.done, revise: it.revise, note: it.note ?? '' }));
      }
      this.pendingKeys.update(keys => keys.filter(k => k !== key));
    }
    for (const attempt of this.pendingAttempts()) {
      await this.deliver(this.http.post(`${API_BASE}/api/quiz-attempts`, attempt));
      this.pendingAttempts.update(list => list.filter(a => a !== attempt));
    }
  }

  /** Sends one queued change. A refusal is reported and the change dropped; any other failure is thrown. */
  private async deliver(request: Observable<unknown>): Promise<void> {
    try {
      await firstValueFrom(request);
    } catch (e) {
      if (!isRefusal(e)) throw e;
      this.syncError.set((e as HttpErrorResponse).error?.error ?? 'The server did not accept a saved change.');
    }
  }

  private async authenticate(path: 'login' | 'register' | 'google', body: object): Promise<void> {
    try {
      // the API may be asleep; `waking` lets the page say so while this waits
      if (!(await this.waitForServer(() => true, SIGN_IN_WAIT_MS))) {
        throw new Error('The server is not responding. Please try again in a few minutes.');
      }
      const res = await firstValueFrom(
        this.http.post<{ token: string; user: User }>(`${API_BASE}/api/auth/${path}`, body));
      localStorage.setItem(TOKEN_KEY, res.token);
      this.rememberUser(res.user);
      this.restoreMirror(res.user);
      this.syncError.set(null);
      await this.connect();
    } catch (e) {
      const msg = e instanceof HttpErrorResponse ? e.error?.error ?? e.message : e instanceof Error ? e.message : String(e);
      throw new Error(msg);
    } finally {
      if (!this.user()) this.waking.set(false);
    }
  }

  private sessionExpired(): void {
    this.saveLocal(); // keep unsent changes in this account's copy; logout() clears them from memory
    this.logout();
    this.syncError.set('Your session expired. Sign in again to keep syncing.');
  }

  private rememberUser(user: User): void {
    this.user.set(user);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  /** Loads this browser's copy of an account, including changes still waiting to be sent. */
  private restoreMirror(user: User): void {
    const state = this.readLocal(`${STORAGE_KEY}.user.${user.id}`);
    this.items.set(state?.items ?? {});
    this.attempts.set(state?.attempts ?? []);
    this.startDate.set(state?.startDate ?? user.startDate);
    this.pendingKeys.set(state?.pending?.keys ?? []);
    this.pendingAttempts.set(state?.pending?.attempts ?? []);
    this.pendingStartDate.set(state?.pending?.startDate ?? false);
  }

  private async loadFromServer(): Promise<void> {
    const token = localStorage.getItem(TOKEN_KEY);
    const [user, items, attempts] = await Promise.all([
      firstValueFrom(this.http.get<User>(`${API_BASE}/api/me`)),
      firstValueFrom(this.http.get<ProgressItem[]>(`${API_BASE}/api/progress`)),
      firstValueFrom(this.http.get<QuizAttempt[]>(`${API_BASE}/api/quiz-attempts`)),
    ]);
    if (localStorage.getItem(TOKEN_KEY) !== token) return; // signed out or switched account while loading
    // anything changed here while this was loading has not reached the server yet, so it wins
    const merged = Object.fromEntries(items.map(i => [i.key, i]));
    const local = this.items();
    for (const key of this.pendingKeys()) {
      if (local[key]) merged[key] = local[key];
    }
    this.rememberUser(user);
    if (!this.pendingStartDate()) this.startDate.set(user.startDate);
    this.items.set(merged);
    this.attempts.set([...this.pendingAttempts(), ...attempts]);
  }

  private async pushToServer(items: ProgressItem[], attempts: QuizAttempt[]): Promise<number> {
    if (this.mode() !== 'server') return 0;
    const res = await firstValueFrom(
      this.http.post<{ imported: number }>(`${API_BASE}/api/progress/import`, items));
    for (const a of attempts) {
      await firstValueFrom(this.http.post(`${API_BASE}/api/quiz-attempts`, a));
    }
    await this.loadFromServer();
    return res.imported;
  }

  private storageKey(): string {
    const u = this.user();
    return u ? `${STORAGE_KEY}.user.${u.id}` : STORAGE_KEY;
  }

  private readJson<T>(key: string): T | null {
    try {
      const raw = localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : null;
    } catch {
      return null;
    }
  }

  private readLocal(key: string): LocalState | null {
    return this.readJson<LocalState>(key);
  }

  private loadLocal(): void {
    const state = this.readLocal(STORAGE_KEY);
    this.items.set(state?.items ?? {});
    this.attempts.set(state?.attempts ?? []);
    this.startDate.set(state?.startDate ?? todayIso());
    const prefersDark = typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: dark)').matches;
    this.theme.set(state?.theme ?? (prefersDark ? 'dark' : 'light'));
  }

  private saveLocal(): void {
    const state: LocalState = {
      startDate: this.startDate(), items: this.items(), attempts: this.attempts(), theme: this.theme(),
    };
    if (this.user()) {
      state.pending = {
        keys: this.pendingKeys(), attempts: this.pendingAttempts(), startDate: this.pendingStartDate(),
      };
    }
    try {
      localStorage.setItem(this.storageKey(), JSON.stringify(state));
      if (this.user()) {
        // keep the theme preference shared across modes
        const local = this.readLocal(STORAGE_KEY);
        if (local) localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...local, theme: this.theme() }));
      }
    } catch {
      /* storage full or blocked: progress still lives in memory / on the server */
    }
  }
}
