import { Component, computed, inject, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CatalogService, keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { Section } from '../core/models';
import { HabitService } from '../core/habit.service';
import { ProgressService, toIso, todayIso } from '../core/progress.service';
import { trapOfTheDay } from '../shared/trap-card';
import { DoneToggle, LinkPipe, ProgressBar } from '../shared/ui';

interface SectionCard { section: Section; title: string; icon: string; link: string; unit: string; }

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, ProgressBar, DoneToggle, LinkPipe],
  template: `
    <section class="hero card">
      <div>
        <p class="eyebrow">{{ phase() }}</p>
        <h1>{{ greeting() }}</h1>
        <p class="muted">Goal: product-company offer (~15 LPA) in 60 days of study + 14 days of final-round practice.
          Started {{ progress.startDate() }} · <a routerLink="/account">change</a></p>
      </div>
      <div class="hero-stats">
        <div><b>{{ progress.streak() }}</b><span>day streak</span></div>
        <div><b>{{ totalDone() }}</b><span>items done</span></div>
        <div><b>{{ overallPct() }}%</b><span>overall</span></div>
      </div>
    </section>

    @if (behind() > 0) {
      <div class="banner warn">You have {{ behind() }} unfinished plan task(s) from earlier days.
        <a routerLink="/plan">Catch up in the plan</a>.</div>
    }

    <div class="grid two">
      <section class="card">
        <div class="card-head">
          <h2>Today · {{ todayLabel() }}</h2>
          <a [routerLink]="todayLink()" class="muted small">Open →</a>
        </div>
        @if (today(); as d) {
          <p class="muted">{{ d.title }} — {{ d.focus }}</p>
          <ul class="tasks">
            @for (t of d.tasks; track t.id) {
              <li [class.done]="progress.isDone(planKey(d.day, t.id))">
                <app-done-toggle [key]="planKey(d.day, t.id)" section="plan" />
                <div>
                  @if (t.link) { <a [routerLink]="t.link | link">{{ t.title }}</a> } @else { {{ t.title }} }
                  <span class="muted small"> · {{ t.minutes }} min</span>
                </div>
              </li>
            }
          </ul>
        } @else if (progress.currentDay() > 60 && progress.currentDay() <= 74) {
          <p>You're in the Final Round. Today's set: <a [routerLink]="['/final-round', progress.currentDay() - 60]">
            Day {{ progress.currentDay() - 60 }}</a>.</p>
        } @else if (progress.currentDay() > 74) {
          <p>You've completed the full journey. Keep revising your <a routerLink="/revision">revision list</a> and take mocks again.</p>
        } @else {
          <p class="muted">Loading plan…</p>
        }
      </section>

      <section class="card">
        <div class="card-head">
          <h2>🔥 Today's routine</h2>
          <a routerLink="/habits" class="muted small">Open →</a>
        </div>
        <p class="muted small">Streak {{ habits.streak() }} day(s) · {{ routineMet() }}/{{ habits.today().statuses.length }} habits done today</p>
        <ul class="habit-list compact">
          @for (st of habits.today().statuses; track st.habit.id) {
            <li [class.met]="st.met">
              <span class="habit-icon">{{ st.habit.icon }}</span>
              <span class="grow">{{ st.habit.title }}</span>
              <span class="muted small">{{ st.met ? '✓' : (st.habit.kind === 'plan' ? st.value + '%' : st.habit.kind === 'journal' ? '' : st.value + '/' + st.habit.target) }}</span>
            </li>
          }
        </ul>
        @if (!habits.timerRunning()) {
          <button class="btn small" (click)="habits.startTimer(25)">⏱️ Start a 25-min focus block</button>
        }
      </section>
    </div>

    @if (trap(); as t) {
      <section class="card trap-teaser">
        <div class="card-head">
          <h2>🪤 Trap of the day</h2>
          <a [routerLink]="['/traps', t.id]" class="btn small primary">Try it →</a>
        </div>
        <p><b>{{ t.title }}</b> <span class="muted small">· {{ t.frequency }} · most candidates get this wrong</span></p>
      </section>
    }

    <h2 class="section-title">Progress by section</h2>
    <div class="grid three">
      @for (c of cards; track c.section) {
        <a class="card stat-card" [routerLink]="c.link">
          <div class="stat-top"><span class="big-icon">{{ c.icon }}</span><h3>{{ c.title }}</h3></div>
          <app-progress-bar [done]="doneFor(c.section)" [total]="totalFor(c.section)" />
          <p class="muted small">{{ doneFor(c.section) }} of {{ totalFor(c.section) }} {{ c.unit }}</p>
        </a>
      }
      <a class="card stat-card" routerLink="/final-round">
        <div class="stat-top"><span class="big-icon">📝</span><h3>Quiz attempts</h3></div>
        <p class="big-number">{{ progress.attempts().length }}</p>
        <p class="muted small">Average score {{ avgScore() }}%</p>
      </a>
    </div>
    <section class="card section-title">
      <h2>Activity (last 12 weeks)</h2>
      <div class="heatmap">
        @for (cell of heatmap(); track cell.date) {
          <span class="cell" [attr.data-l]="cell.level" [title]="cell.date + ': ' + cell.count"></span>
        }
      </div>
      <p class="muted small">Each square is a day; darker means more items completed.</p>
      <p><a routerLink="/revision">★ {{ reviseCount() }} item(s) in your revision list</a></p>
    </section>
  `,
})
export class Dashboard {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private catalog = inject(CatalogService);
  protected habits = inject(HabitService);
  protected planKey = keys.plan;
  private trapsRes = resource({ loader: () => this.content.traps() });
  protected trap = computed(() => trapOfTheDay(this.trapsRes.value() ?? [], k => this.progress.isDone(k), todayIso()));
  protected routineMet = computed(() => this.habits.today().statuses.filter(x => x.met).length);

  private planRes = resource({ loader: () => this.content.plan() });
  private catalogRes = resource({ loader: () => this.catalog.all() });

  protected cards: SectionCard[] = [
    { section: 'plan', title: '60-Day Plan', icon: '🗓️', link: '/plan', unit: 'tasks' },
    { section: 'dsa', title: 'DSA Problems', icon: '🧩', link: '/dsa', unit: 'problems' },
    { section: 'sd', title: 'System Design', icon: '🏗️', link: '/system-design', unit: 'topics' },
    { section: 'core', title: 'Core Subjects', icon: '📚', link: '/core', unit: 'notes & questions' },
    { section: 'traps', title: 'Common Traps', icon: '🪤', link: '/traps', unit: 'traps beaten' },
    { section: 'rounds', title: 'Interview Rounds', icon: '🧭', link: '/rounds', unit: 'rounds ready' },
    { section: 'final', title: 'Final Round', icon: '🏁', link: '/final-round', unit: 'coding & theory items' },
    { section: 'ai', title: 'AI Engineer Course', icon: '🤖', link: '/ai', unit: 'lessons & projects' },
  ];

  private totals = computed(() => {
    const map = new Map<Section, string[]>();
    for (const e of this.catalogRes.value() ?? []) {
      map.set(e.section, [...(map.get(e.section) ?? []), e.key]);
    }
    return map;
  });

  totalFor(s: Section) { return this.totals().get(s)?.length ?? 0; }
  doneFor(s: Section) { return this.progress.countDone(this.totals().get(s) ?? []); }

  protected totalDone = computed(() => Object.values(this.progress.items()).filter(i => i.done).length);
  protected overallPct = computed(() => {
    const all = this.catalogRes.value()?.length ?? 0;
    return all ? Math.round((this.progress.countDone((this.catalogRes.value() ?? []).map(e => e.key)) / all) * 100) : 0;
  });
  protected reviseCount = computed(() => Object.values(this.progress.items()).filter(i => i.revise).length);

  protected today = computed(() => this.planRes.value()?.days.find(d => d.day === this.progress.currentDay()));
  protected todayLabel = computed(() => {
    const d = this.progress.currentDay();
    return d <= 60 ? `Day ${d} of 60` : d <= 74 ? `Final Round day ${d - 60}` : 'Journey complete';
  });
  protected todayLink = computed(() => {
    const d = this.progress.currentDay();
    return d <= 60 ? `/plan/${d}` : d <= 74 ? `/final-round/${d - 60}` : '/revision';
  });
  protected phase = computed(() => {
    const d = this.progress.currentDay();
    if (d <= 60) return `Study phase · Week ${Math.ceil(d / 7)}`;
    if (d <= 74) return 'Final round phase';
    return 'Interview mode';
  });
  protected greeting = computed(() => {
    const name = this.progress.user()?.displayName ?? 'Raj';
    return `Let's go, ${name}.`;
  });

  protected behind = computed(() => {
    const days = this.planRes.value()?.days ?? [];
    const cur = Math.min(this.progress.currentDay(), 61);
    let n = 0;
    for (const d of days) {
      if (d.day >= cur) break;
      d.tasks.forEach(t => { if (t.type !== 'ai' && !this.progress.isDone(keys.plan(d.day, t.id))) n++; });
    }
    return n;
  });

  protected avgScore = computed(() => {
    const a = this.progress.attempts();
    return a.length ? Math.round((a.reduce((s, x) => s + x.score / x.total, 0) / a.length) * 100) : 0;
  });

  protected heatmap = computed(() => {
    const act = this.progress.activity();
    const cells: { date: string; count: number; level: number }[] = [];
    const d = new Date();
    d.setDate(d.getDate() - 83);
    for (let i = 0; i < 84; i++) {
      const iso = toIso(d);
      const count = act.get(iso) ?? 0;
      cells.push({ date: iso, count, level: count === 0 ? 0 : count < 3 ? 1 : count < 6 ? 2 : count < 10 ? 3 : 4 });
      d.setDate(d.getDate() + 1);
    }
    return cells;
  });
}
