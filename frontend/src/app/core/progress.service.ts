import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { firstValueFrom, timeout } from 'rxjs';
import { API_BASE } from './api.config';
import { TOKEN_KEY } from './auth.interceptor';
import { HabitData, ProgressItem, QuizAttempt, Section, User } from './models';

const STORAGE_KEY = 'switchprep.v1';

interface LocalState {
  startDate: string;
  items: Record<string, ProgressItem>;
  attempts: QuizAttempt[];
  theme?: 'light' | 'dark';
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

/**
 * Single source of truth for the user's progress. Works in two modes:
 * - local: everything lives in localStorage (no backend needed)
 * - server: logged in to the Spring Boot API; every change is written through to the API
 *   and also mirrored to localStorage so the UI loads instantly.
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

    if (this.mode() === 'server') {
      this.http.put(`${API_BASE}/api/progress/${encodeURIComponent(key)}`, { section, ...patch })
        .subscribe({ error: e => this.handleSyncError(e) });
    }
  }

  addAttempt(attempt: Omit<QuizAttempt, 'takenAt'>): void {
    const full: QuizAttempt = { ...attempt, takenAt: new Date().toISOString() };
    this.attempts.update(list => [full, ...list]);
    if (this.mode() === 'server') {
      const { takenAt: _ignored, ...body } = full;
      this.http.post(`${API_BASE}/api/quiz-attempts`, body).subscribe({ error: e => this.handleSyncError(e) });
    }
  }

  setStartDate(date: string): void {
    this.startDate.set(date);
    if (this.mode() === 'server') {
      this.http.put<User>(`${API_BASE}/api/me`, { startDate: date })
        .subscribe({ next: u => this.user.set(u), error: e => this.handleSyncError(e) });
    }
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

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.user.set(null);
    this.loadLocal();
  }

  /** Uploads progress made in browser-only mode to the logged-in account. */
  async uploadLocalToAccount(): Promise<number> {
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
    if (this.mode() === 'server') await this.pushToServer(file.items, newAttempts);
    return file.items.length;
  }

  async reset(): Promise<void> {
    this.items.set({});
    this.attempts.set([]);
    if (this.mode() === 'server') {
      await firstValueFrom(this.http.delete(`${API_BASE}/api/progress`));
    }
  }

  // ---------- internals ----------

  private async init(): Promise<void> {
    try {
      await firstValueFrom(this.http.get(`${API_BASE}/actuator/health`).pipe(timeout(3000)));
      this.backendAvailable.set(true);
    } catch {
      this.backendAvailable.set(false);
      return;
    }
    if (localStorage.getItem(TOKEN_KEY)) {
      try {
        await this.loadFromServer();
      } catch (e) {
        if (e instanceof HttpErrorResponse && e.status === 401) this.logout();
      }
    }
  }

  private async authenticate(path: 'login' | 'register', body: object): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.post<{ token: string; user: User }>(`${API_BASE}/api/auth/${path}`, body));
      localStorage.setItem(TOKEN_KEY, res.token);
      await this.loadFromServer();
    } catch (e) {
      const msg = e instanceof HttpErrorResponse ? e.error?.error ?? e.message : String(e);
      throw new Error(msg);
    }
  }

  private async loadFromServer(): Promise<void> {
    const [user, items, attempts] = await Promise.all([
      firstValueFrom(this.http.get<User>(`${API_BASE}/api/me`)),
      firstValueFrom(this.http.get<ProgressItem[]>(`${API_BASE}/api/progress`)),
      firstValueFrom(this.http.get<QuizAttempt[]>(`${API_BASE}/api/quiz-attempts`)),
    ]);
    this.user.set(user);
    this.startDate.set(user.startDate);
    this.items.set(Object.fromEntries(items.map(i => [i.key, i])));
    this.attempts.set(attempts);
    this.syncError.set(null);
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

  private handleSyncError(e: unknown): void {
    if (e instanceof HttpErrorResponse && e.status === 401) {
      this.syncError.set('Your session expired. Log in again to keep syncing.');
      this.logout();
    } else {
      this.syncError.set('Could not save to the server. Your change is kept in this browser.');
    }
  }

  private storageKey(): string {
    const u = this.user();
    return u ? `${STORAGE_KEY}.user.${u.id}` : STORAGE_KEY;
  }

  private readLocal(key: string): LocalState | null {
    try {
      const raw = localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as LocalState) : null;
    } catch {
      return null;
    }
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
