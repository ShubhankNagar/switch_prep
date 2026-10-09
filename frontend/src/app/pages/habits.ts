import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { COMPLETE_DAY_THRESHOLD, HabitService, HabitStatus } from '../core/habit.service';
import { HabitDef, HabitKind } from '../core/models';
import { todayIso } from '../core/progress.service';

@Component({
  selector: 'app-habits',
  imports: [FormsModule, RouterLink],
  template: `
    <h1>Daily Routine</h1>
    <p class="muted">Small daily wins beat weekend marathons. Most habits tick themselves when you complete things
      on the site; enter the rest here. A day counts toward your streak when you hit
      {{ threshold }}% of your active habits.</p>

    <section class="hero card routine-hero">
      <div>
        <p class="eyebrow">Today · {{ today }}</p>
        <h2>{{ todayMet() }} of {{ habits.today().statuses.length }} habits done</h2>
        <div class="pbar big"><div class="pbar-fill" [style.width.%]="scorePct()"></div></div>
      </div>
      <div class="hero-stats">
        <div><b>{{ habits.streak() }}</b><span>day streak</span></div>
        <div><b>{{ habits.bestStreak() }}</b><span>best streak</span></div>
        <div><b>{{ perfect30() }}</b><span>complete days (30d)</span></div>
        <div><b>{{ hours30() }}</b><span>hours (30d)</span></div>
      </div>
    </section>

    <div class="grid two">
      <section class="card">
        <h2>Today's habits</h2>
        <ul class="habit-list">
          @for (s of habits.today().statuses; track s.habit.id) {
            <li [class.met]="s.met">
              <span class="habit-icon">{{ s.habit.icon }}</span>
              <div class="grow">
                <div class="habit-title">{{ s.habit.title }}</div>
                <div class="pbar"><div class="pbar-fill" [style.width.%]="s.pct"></div></div>
                <div class="muted small">{{ label(s) }}
                  @if (s.habit.kind === 'auto') { · ticks itself from your progress }
                </div>
              </div>
              <div class="habit-control">
                @switch (s.habit.kind) {
                  @case ('count') {
                    <button class="btn small" (click)="bump(s.habit, -1)">−</button>
                    <b>{{ s.value }}</b>
                    <button class="btn small" (click)="bump(s.habit, 1)">+</button>
                  }
                  @case ('check') {
                    <button class="check" [class.on]="s.met" (click)="habits.setValue(s.habit.id, s.met ? 0 : 1)">
                      <span class="box">{{ s.met ? '✓' : '' }}</span></button>
                  }
                  @case ('minutes') {
                    <input type="number" min="0" max="1440" class="mini-input" [ngModel]="s.value"
                           (change)="setMinutes($event)" aria-label="Minutes studied today" />
                  }
                  @case ('auto') { <span class="big-tick">{{ s.met ? '✓' : s.value + '/' + s.habit.target }}</span> }
                  @case ('plan') { <a routerLink="/plan" class="small">{{ s.value }}%</a> }
                  @case ('journal') { <span class="big-tick">{{ s.met ? '✓' : '' }}</span> }
                }
              </div>
            </li>
          }
        </ul>
        <label class="note-box">
          <span class="muted small">📝 What did you learn today? (one line)</span>
          <input type="text" maxlength="300" [ngModel]="habits.log(today).journal" (change)="setJournal($event)"
                 placeholder="e.g. Outbox pattern solves the DB + Kafka dual-write problem" />
        </label>
      </section>

      <section class="card">
        <h2>⏱️ Focus timer</h2>
        @if (habits.timerRunning()) {
          <p class="timer-big">{{ clock() }}</p>
          <p class="muted small">Phone away, one task only. Minutes are logged automatically.</p>
          <button class="btn" (click)="habits.stopTimer(true)">Stop and log {{ elapsedMin() }} min</button>
        } @else {
          <p class="muted">Start a block; when it ends the minutes go into today's study time.</p>
          <div class="row wrap">
            <button class="btn primary" (click)="start(25)">25 min</button>
            <button class="btn" (click)="start(50)">50 min</button>
            <button class="btn" (click)="start(90)">90 min deep work</button>
          </div>
        }
        <h3 class="section-title">Suggested routine</h3>
        <ul class="routine">
          <li><b>Morning, 20-30 min:</b> 1 trap + 10 flashcards (recall while fresh).</li>
          <li><b>Commute/lunch, 15 min:</b> re-read one key-points list or a revision-list item.</li>
          <li><b>Evening block 1, 50-60 min:</b> 2 coding problems, out loud, timed.</li>
          <li><b>Evening block 2, 50 min:</b> today's topic (core chapter or design topic).</li>
          <li><b>Before bed, 5 min:</b> one-line journal + 5 job applications (from week 3).</li>
          <li><b>Weekend:</b> one mock (coding or design), revise starred items, plan the week.</li>
        </ul>
      </section>
    </div>

    <section class="card">
      <h2>Consistency · last 12 weeks</h2>
      <div class="heatmap">
        @for (d of habits.last84(); track d.date) {
          <span class="cell" [attr.data-l]="level(d.score, d.statuses.length)"
                [class.complete-day]="d.complete" [title]="d.date + ': ' + pct(d.score) + '% of habits'"></span>
        }
      </div>
      <p class="muted small">Darker = more habits met. Outlined squares are complete days (≥ {{ threshold }}%).</p>

      <h3 class="section-title">Last 7 days</h3>
      <div class="table-wrap">
        <table class="table habit-table">
          <thead>
            <tr><th>Habit</th>
              @for (d of last7(); track d.date) { <th>{{ dayLabel(d.date) }}</th> }
              <th>Streak</th><th>30-day</th></tr>
          </thead>
          <tbody>
            @for (h of habits.activeHabits(); track h.id) {
              <tr>
                <td>{{ h.icon }} {{ h.title }}</td>
                @for (d of last7(); track d.date) {
                  <td class="center">{{ cell(d.statuses, h.id) }}</td>
                }
                <td class="center">{{ stats(h).streak }}</td>
                <td class="center">{{ stats(h).rate30 }}%</td>
              </tr>
            }
            <tr class="muted"><td>Study minutes</td>
              @for (d of last7(); track d.date) { <td class="center">{{ d.minutes || '' }}</td> }
              <td></td><td></td></tr>
          </tbody>
        </table>
      </div>
      @if (journalEntries().length) {
        <h3 class="section-title">Learning journal</h3>
        <ul class="journal">
          @for (j of journalEntries(); track j.date) { <li><span class="muted small">{{ j.date }}</span> {{ j.journal }}</li> }
        </ul>
      }
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Customize your routine</h2>
        <button class="btn small" (click)="editing.set(!editing())">{{ editing() ? 'Done' : 'Edit habits' }}</button>
      </div>
      @if (editing()) {
        <table class="table">
          <thead><tr><th>On</th><th>Habit</th><th>Daily target</th><th></th></tr></thead>
          <tbody>
            @for (h of draft(); track h.id; let i = $index) {
              <tr>
                <td><input type="checkbox" [checked]="h.active" (change)="patch(i, { active: !h.active })" /></td>
                <td>{{ h.icon }} {{ h.title }} <div class="muted small">{{ h.why }}</div></td>
                <td>
                  @if (h.kind !== 'journal') {
                    <input type="number" min="1" class="mini-input" [value]="h.target"
                           (change)="patch(i, { target: num($event) })" /> {{ h.unit }}
                  }
                </td>
                <td>@if (h.custom) { <button class="btn small danger" (click)="remove(i)">Remove</button> }</td>
              </tr>
            }
          </tbody>
        </table>
        <form class="row wrap" (ngSubmit)="addCustom()">
          <input name="t" placeholder="New habit, e.g. Read 1 engineering blog" [(ngModel)]="newTitle" class="grow" />
          <select name="k" [(ngModel)]="newKind">
            <option value="check">Yes / no</option><option value="count">Count</option>
          </select>
          <input name="n" type="number" min="1" class="mini-input" [(ngModel)]="newTarget" />
          <button class="btn" type="submit">Add</button>
        </form>
        <div class="row">
          <button class="btn primary" (click)="saveDraft()">Save routine</button>
          <button class="btn" (click)="resetDefaults()">Reset to defaults</button>
        </div>
      } @else {
        <p class="muted">Turn habits on or off, change targets, or add your own (e.g. "Read one engineering blog").</p>
      }
    </section>
  `,
})
export class HabitsPage {
  protected habits = inject(HabitService);
  protected today = todayIso();
  protected threshold = Math.round(COMPLETE_DAY_THRESHOLD * 100);
  protected editing = signal(false);
  protected draft = signal<HabitDef[]>([]);
  newTitle = '';
  newKind: HabitKind = 'check';
  newTarget = 1;

  protected todayMet = computed(() => this.habits.today().statuses.filter(s => s.met).length);
  protected scorePct = computed(() => Math.round(this.habits.today().score * 100));
  protected last7 = computed(() => this.habits.last84().slice(-7));
  protected perfect30 = computed(() => this.habits.last84().slice(-30).filter(d => d.complete).length);
  protected hours30 = computed(() => Math.round(this.habits.last84().slice(-30).reduce((s, d) => s + d.minutes, 0) / 6) / 10);
  protected journalEntries = computed(() => this.habits.last84().filter(d => d.journal.trim()).reverse().slice(0, 14));
  protected clock = computed(() => {
    const r = this.habits.timerRemaining();
    return `${Math.floor(r / 60)}:${String(r % 60).padStart(2, '0')}`;
  });
  protected elapsedMin = computed(() => Math.floor((this.habits.timerTotal() - this.habits.timerRemaining()) / 60));

  constructor() {
    this.draft.set(this.habits.habits());
  }

  label(s: HabitStatus) {
    if (s.habit.kind === 'journal') return s.met ? 'Written' : 'Not written yet';
    if (s.habit.kind === 'plan') return `${s.value}% of today's plan tasks`;
    return `${s.value} / ${s.habit.target} ${s.habit.unit}`;
  }
  bump(h: HabitDef, delta: number) {
    this.habits.setValue(h.id, (this.habits.log(this.today).values[h.id] ?? 0) + delta);
  }
  setMinutes(e: Event) { this.habits.setMinutes(Number((e.target as HTMLInputElement).value) || 0); }
  setJournal(e: Event) { this.habits.setJournal((e.target as HTMLInputElement).value); }
  start(min: number) {
    if (typeof Notification !== 'undefined' && Notification.permission === 'default') void Notification.requestPermission();
    this.habits.startTimer(min);
  }
  pct(score: number) { return Math.round(score * 100); }
  level(score: number, n: number) {
    if (!n || score === 0) return 0;
    return score < 0.4 ? 1 : score < 0.6 ? 2 : score < COMPLETE_DAY_THRESHOLD ? 3 : 4;
  }
  dayLabel(iso: string) {
    return new Date(iso + 'T00:00:00').toLocaleDateString(undefined, { weekday: 'short' });
  }
  cell(statuses: HabitStatus[], id: string) {
    const s = statuses.find(x => x.habit.id === id);
    return !s ? '–' : s.met ? '✓' : s.value > 0 ? '·' : '';
  }
  stats(h: HabitDef) { return this.habits.habitStats(h); }
  num(e: Event) { return Math.max(1, Number((e.target as HTMLInputElement).value) || 1); }

  patch(i: number, change: Partial<HabitDef>) {
    this.draft.update(list => list.map((h, j) => (j === i ? { ...h, ...change } : h)));
  }
  remove(i: number) { this.draft.update(list => list.filter((_, j) => j !== i)); }
  addCustom() {
    const title = this.newTitle.trim();
    if (!title) return;
    const id = 'custom-' + title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 30) + '-' + Date.now().toString(36);
    this.draft.update(list => [...list, {
      id, title, icon: '⭐', kind: this.newKind, target: this.newKind === 'check' ? 1 : Math.max(1, this.newTarget),
      unit: this.newKind === 'check' ? 'done' : 'times', active: true, custom: true,
    }]);
    this.newTitle = '';
  }
  saveDraft() {
    this.habits.saveHabits(this.draft());
    this.editing.set(false);
  }
  resetDefaults() {
    this.habits.resetHabitsToDefault();
    this.draft.set(this.habits.habits());
  }
}
