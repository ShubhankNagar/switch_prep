import { HttpClient, HttpResponse } from '@angular/common/http';
import { Injectable, computed, effect, inject, resource, signal, untracked } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { API_BASE } from './api.config';
import { keys } from './catalog.service';
import { ContentService } from './content.service';
import { HabitData, HabitDayLog, HabitDef } from './models';
import { ProgressService, toIso, todayIso } from './progress.service';

const STORAGE_KEY = 'switchprep.habits.v1';

/** A day counts towards the routine streak when at least this share of active habits is met. */
export const COMPLETE_DAY_THRESHOLD = 0.8;

export const DEFAULT_HABITS: HabitDef[] = [
  { id: 'plan', title: "Finish today's plan tasks", icon: '🗓️', kind: 'plan', target: 100, unit: '%', active: true,
    why: 'The plan is already balanced across DSA, theory and design. Finishing it daily is the whole strategy.' },
  { id: 'dsa', title: 'Solve 2 coding problems', icon: '🧩', kind: 'auto', target: 2, unit: 'problems', active: true,
    prefixes: ['dsa:', 'fr:'], why: 'Coding fluency decays fast. Two a day keeps patterns warm without burning out.' },
  { id: 'learn', title: 'Learn 1 topic deeply', icon: '📖', kind: 'auto', target: 1, unit: 'topic', active: true,
    prefixes: ['note:', 'sd:', 'ai:', 'round:'], why: 'One chapter or design topic a day adds up to the whole syllabus.' },
  { id: 'recall', title: 'Recall 10 interview questions', icon: '🧠', kind: 'auto', target: 10, unit: 'questions',
    active: true, prefixes: ['qa:'], countRevise: true,
    why: 'Active recall (flashcards, answering aloud) beats re-reading for retention.' },
  { id: 'trap', title: 'Beat 1 common trap', icon: '🪤', kind: 'auto', target: 1, unit: 'trap', active: true,
    prefixes: ['trap:'], why: 'These are the questions most candidates get wrong. One a day = 100+ wins before interviews.' },
  { id: 'focus', title: 'Focused study time', icon: '⏱️', kind: 'minutes', target: 120, unit: 'min', active: true,
    why: 'Use the focus timer: 25-50 minute blocks with phone away.' },
  { id: 'apply', title: 'Job search: apply or reach out', icon: '📬', kind: 'count', target: 5, unit: 'applications',
    active: true, why: 'Pipelines take weeks. Applying daily from week 3 means interviews line up when you are ready.' },
  { id: 'journal', title: "Write today's one-line learning", icon: '📝', kind: 'journal', target: 1, unit: 'line',
    active: true, why: 'Writing one sentence of what you learned makes it stick and shows your progress over time.' },
];


export interface HabitStatus { habit: HabitDef; value: number; met: boolean; pct: number; }
export interface DaySummary { date: string; statuses: HabitStatus[]; score: number; complete: boolean; minutes: number; journal: string; }

const emptyLog = (): HabitDayLog => ({ values: {}, minutes: 0, journal: '' });

/**
 * Daily routine tracker. Auto habits are computed from progress made anywhere on the site (completion
 * timestamps), so ticking a DSA problem also ticks "Solve 2 problems". Manual values, study minutes and
 * the journal are stored per day: in localStorage, and on the server when logged in.
 */
@Injectable({ providedIn: 'root' })
export class HabitService {
  private http = inject(HttpClient);
  private progress = inject(ProgressService);
  private content = inject(ContentService);
  private planRes = resource({ loader: () => this.content.plan() });

  readonly habits = signal<HabitDef[]>(DEFAULT_HABITS);
  readonly logs = signal<Record<string, HabitDayLog>>({});
  readonly activeHabits = computed(() => this.habits().filter(h => h.active));

  // focus timer
  readonly timerTotal = signal(0);
  readonly timerRemaining = signal(0);
  readonly timerRunning = computed(() => this.timerTotal() > 0);
  private timerHandle?: ReturnType<typeof setInterval>;
  private loadedFor: number | null | undefined = undefined;

  constructor() {
    this.loadLocal();
    effect(() => this.saveLocal());
    // switch storage when the user logs in or out (only when the account changes: the user object is
    // replaced on every profile refresh, and reloading then would race with writes still in flight)
    effect(() => {
      const id = this.progress.user()?.id ?? null;
      if (id === this.loadedFor) return;
      this.loadedFor = id;
      untracked(() => (id !== null ? void this.loadFromServer() : this.loadLocal()));
    });
  }

  // ---------- per-day computation ----------

  log(date: string): HabitDayLog {
    return this.logs()[date] ?? emptyLog();
  }

  /** Per-day counts for every auto habit, built in one pass over progress: date -> habitId -> count. */
  private autoCounts = computed(() => {
    const map = new Map<string, Map<string, number>>();
    const bump = (date: string, habitId: string) => {
      const day = map.get(date) ?? new Map<string, number>();
      day.set(habitId, (day.get(habitId) ?? 0) + 1);
      map.set(date, day);
    };
    const autos = this.habits().filter(h => h.kind === 'auto');
    for (const item of Object.values(this.progress.items())) {
      for (const habit of autos) {
        if (!(habit.prefixes ?? []).some(p => item.key.startsWith(p))) continue;
        const doneDay = item.done && item.completedAt ? toIso(new Date(item.completedAt)) : null;
        if (doneDay) bump(doneDay, habit.id);
        if (habit.countRevise && item.revise && item.updatedAt) {
          const revDay = toIso(new Date(item.updatedAt));
          if (revDay !== doneDay) bump(revDay, habit.id);
        }
      }
    }
    return map;
  });

  private autoCount(habit: HabitDef, date: string): number {
    return this.autoCounts().get(date)?.get(habit.id) ?? 0;
  }

  private planPct(date: string): number {
    const start = new Date(this.progress.startDate() + 'T00:00:00');
    const day = Math.floor((new Date(date + 'T00:00:00').getTime() - start.getTime()) / 86400000) + 1;
    const planDay = this.planRes.value()?.days.find(d => d.day === day);
    const tasks = (planDay?.tasks ?? []).filter(t => t.type !== 'ai'); // AI lessons are optional
    if (!tasks.length) return -1; // no plan that day (before start or after day 60)
    const done = this.progress.countDone(tasks.map(t => keys.plan(day, t.id)));
    return Math.round((done / tasks.length) * 100);
  }

  status(habit: HabitDef, date: string): HabitStatus | null {
    const log = this.log(date);
    let value: number;
    switch (habit.kind) {
      case 'auto': value = this.autoCount(habit, date); break;
      case 'plan': {
        value = this.planPct(date);
        if (value < 0) return null; // not applicable that day
        break;
      }
      case 'minutes': value = log.minutes; break;
      case 'journal': value = log.journal.trim() ? 1 : 0; break;
      default: value = log.values[habit.id] ?? 0;
    }
    const target = Math.max(1, habit.target);
    return { habit, value, met: value >= target, pct: Math.min(100, Math.round((value / target) * 100)) };
  }

  summary(date: string): DaySummary {
    const statuses = this.activeHabits().map(h => this.status(h, date)).filter((s): s is HabitStatus => !!s);
    const met = statuses.filter(s => s.met).length;
    const score = statuses.length ? met / statuses.length : 0;
    const log = this.log(date);
    return { date, statuses, score, complete: score >= COMPLETE_DAY_THRESHOLD, minutes: log.minutes, journal: log.journal };
  }

  readonly today = computed(() => {
    // read signals that summary() depends on so this recomputes
    this.progress.items(); this.logs(); this.habits(); this.planRes.value();
    return this.summary(todayIso());
  });

  /** Summaries for the last n days, oldest first. */
  history(n: number): DaySummary[] {
    const out: DaySummary[] = [];
    const d = new Date();
    d.setDate(d.getDate() - (n - 1));
    for (let i = 0; i < n; i++) {
      out.push(this.summary(toIso(d)));
      d.setDate(d.getDate() + 1);
    }
    return out;
  }

  readonly last84 = computed(() => {
    this.progress.items(); this.logs(); this.habits(); this.planRes.value(); this.progress.startDate();
    return this.history(84);
  });

  /** Consecutive complete days ending today (today counts only once it is complete). */
  readonly streak = computed(() => {
    const days = this.last84();
    let i = days.length - 1;
    if (!days[i].complete) i--;
    let n = 0;
    while (i >= 0 && days[i].complete) { n++; i--; }
    return n;
  });

  readonly bestStreak = computed(() => {
    let best = 0, run = 0;
    for (const d of this.last84()) { run = d.complete ? run + 1 : 0; best = Math.max(best, run); }
    return best;
  });

  /** Per-habit current streak and 30-day hit rate. */
  habitStats(habit: HabitDef): { streak: number; rate30: number } {
    const days = this.last84();
    let i = days.length - 1;
    const metOn = (d: DaySummary) => d.statuses.find(s => s.habit.id === habit.id)?.met ?? false;
    if (!metOn(days[i])) i--;
    let streak = 0;
    while (i >= 0 && metOn(days[i])) { streak++; i--; }
    const last30 = days.slice(-30).filter(d => d.statuses.some(s => s.habit.id === habit.id));
    const rate30 = last30.length ? Math.round((last30.filter(metOn).length / last30.length) * 100) : 0;
    return { streak, rate30 };
  }

  // ---------- mutations ----------

  setValue(habitId: string, value: number, date = todayIso()): void {
    const log = this.log(date);
    void this.writeLog(date, { ...log, values: { ...log.values, [habitId]: Math.max(0, value) } });
  }

  addMinutes(minutes: number, date = todayIso()): void {
    const log = this.log(date);
    void this.writeLog(date, { ...log, minutes: Math.min(1440, Math.max(0, log.minutes + minutes)) });
  }

  setMinutes(minutes: number, date = todayIso()): void {
    void this.writeLog(date, { ...this.log(date), minutes: Math.min(1440, Math.max(0, minutes)) });
  }

  setJournal(text: string, date = todayIso()): void {
    void this.writeLog(date, { ...this.log(date), journal: text.slice(0, 1000) });
  }

  saveHabits(habits: HabitDef[]): void {
    this.habits.set(habits);
    if (this.progress.mode() === 'server') {
      this.http.put(`${API_BASE}/api/habits`, { habitsJson: JSON.stringify(habits) })
        .subscribe({ error: () => this.progress.syncError.set('Could not save your routine to the server.') });
    }
  }

  resetHabitsToDefault(): void {
    this.saveHabits(DEFAULT_HABITS);
  }

  // ---------- focus timer ----------

  startTimer(minutes: number): void {
    this.stopTimer(false);
    this.timerTotal.set(minutes * 60);
    this.timerRemaining.set(minutes * 60);
    this.timerHandle = setInterval(() => {
      this.timerRemaining.update(r => r - 1);
      if (this.timerRemaining() <= 0) this.stopTimer(true);
    }, 1000);
  }

  /** Stops the timer and logs the elapsed whole minutes (when log is true). */
  stopTimer(log = true): void {
    clearInterval(this.timerHandle);
    const elapsed = Math.floor((this.timerTotal() - this.timerRemaining()) / 60);
    if (log && elapsed > 0) {
      this.addMinutes(elapsed);
      if (this.timerRemaining() <= 0 && typeof Notification !== 'undefined' && Notification.permission === 'granted') {
        new Notification('Focus block done', { body: `${elapsed} minutes logged. Take a 5-minute break.` });
      }
    }
    this.timerTotal.set(0);
    this.timerRemaining.set(0);
  }

  // ---------- export / import / reset ----------

  exportData(): HabitData {
    return { habits: this.habits(), logs: this.logs() };
  }

  async importData(data: HabitData | undefined): Promise<void> {
    if (!data) return;
    if (Array.isArray(data.habits) && data.habits.length) this.saveHabits(data.habits);
    const writes = Object.entries(data.logs ?? {}).map(([date, log]) => {
      const cur = this.log(date);
      return this.writeLog(date, {
        values: { ...log.values, ...cur.values },
        minutes: Math.max(cur.minutes, log.minutes ?? 0),
        journal: cur.journal || log.journal || '',
      });
    });
    await Promise.all(writes);
  }

  /** Copies the browser-only routine into the logged-in account. */
  async uploadLocalToAccount(): Promise<void> {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) await this.importData(JSON.parse(raw) as HabitData);
  }

  reset(): void {
    this.logs.set({});
  }

  // ---------- internals ----------

  private writeLog(date: string, log: HabitDayLog): Promise<void> {
    this.logs.update(all => ({ ...all, [date]: log }));
    if (this.progress.mode() !== 'server') return Promise.resolve();
    return firstValueFrom(this.http.put(`${API_BASE}/api/habit-logs/${date}`, {
      valuesJson: JSON.stringify(log.values), minutes: log.minutes, journal: log.journal,
    })).then(() => undefined, () => this.progress.syncError.set('Could not save your routine to the server.'));
  }

  private async loadFromServer(): Promise<void> {
    try {
      const [settings, logs] = await Promise.all([
        firstValueFrom(this.http.get<{ habitsJson: string }>(`${API_BASE}/api/habits`, { observe: 'response' })),
        firstValueFrom(this.http.get<{ date: string; valuesJson: string | null; minutes: number; journal: string | null }[]>(
          `${API_BASE}/api/habit-logs`)),
      ]);
      this.habits.set(this.parseHabits((settings as HttpResponse<{ habitsJson: string }>).body?.habitsJson));
      this.logs.set(Object.fromEntries(logs.map(l => [l.date, {
        values: l.valuesJson ? JSON.parse(l.valuesJson) : {}, minutes: l.minutes ?? 0, journal: l.journal ?? '',
      }])));
    } catch {
      this.progress.syncError.set('Could not load your routine from the server.');
    }
  }

  /** Merges saved habits with defaults so newly added built-in habits appear for existing users. */
  private parseHabits(json: string | undefined | null): HabitDef[] {
    if (!json) return DEFAULT_HABITS;
    try {
      const saved = JSON.parse(json) as HabitDef[];
      const ids = new Set(saved.map(h => h.id));
      return [...saved, ...DEFAULT_HABITS.filter(h => !ids.has(h.id))];
    } catch {
      return DEFAULT_HABITS;
    }
  }

  private loadLocal(): void {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const data = raw ? (JSON.parse(raw) as HabitData) : null;
      this.habits.set(this.parseHabits(data ? JSON.stringify(data.habits) : null));
      this.logs.set(data?.logs ?? {});
    } catch {
      this.habits.set(DEFAULT_HABITS);
      this.logs.set({});
    }
  }

  private saveLocal(): void {
    const data: HabitData = { habits: this.habits(), logs: this.logs() };
    if (this.progress.user()) return; // server mode: the API is the source of truth
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch {
      /* storage blocked */
    }
  }
}
