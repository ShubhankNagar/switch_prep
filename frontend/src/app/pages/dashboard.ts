import { Component, computed, inject, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CatalogService, keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { PlanDay, Section } from '../core/models';
import { HabitService } from '../core/habit.service';
import { ProgressService, toIso, todayIso } from '../core/progress.service';
import { RecentService } from '../core/recent.service';
import { GOOGLE_CLIENT_ID } from '../core/api.config';
import { isDue } from '../core/review';
import { trapOfTheDay } from '../shared/trap-card';
import { DoneToggle, LinkPipe, ProgressBar } from '../shared/ui';
import { Icon, habitIcon, habitTone } from '../shared/icon';

interface SectionCard { section: Section; title: string; icon: string; link: string; unit: string; }
interface JourneyCell { day: number; link: string; state: 'full' | 'part' | 'none'; past: boolean; today: boolean; title: string; }

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, ProgressBar, DoneToggle, LinkPipe, Icon],
  template: `
    <section class="today-panel" aria-labelledby="today-title">
      <div class="panel-top">
        <div>
          <p class="eyebrow">{{ phase() }}</p>
          <h1 id="today-title">{{ headline() }}</h1>
          <p>Started {{ startLabel() }} · <a routerLink="/account">change</a></p>
        </div>
        <div class="panel-stats">
          <div class="panel-stat" style="--glyph: #ffb38a"><span class="tile"><app-icon name="flame" /></span>
            <span><b>{{ progress.streak() }}</b><span>day streak</span></span></div>
          <div class="panel-stat" style="--glyph: #7dd3a8"><span class="tile"><app-icon name="check" /></span>
            <span><b>{{ totalDone() }}</b><span>items done</span></span></div>
          <div class="panel-stat" style="--glyph: #a9c4ff"><span class="tile"><app-icon name="target" /></span>
            <span><b>{{ overallPct() }}%</b><span>of everything</span></span></div>
        </div>
      </div>
      <div class="journey">
        <div class="journey-head">
          <b>Your 74 days</b>
          <span><span class="num">{{ daysComplete() }}</span> of 60 study days complete</span>
        </div>
        <div class="journey-track">
          @for (w of journeyWeeks(); track w.label) {
            <div class="jweek" [class.final]="w.final" [class.current]="w.current" [style.flex-grow]="w.cells.length">
              <div class="jcells">
                @for (c of w.cells; track c.day) {
                  <a class="jcell" [routerLink]="c.link" [class.full]="c.state === 'full'" [class.part]="c.state === 'part'"
                     [class.past]="c.past" [class.today]="c.today" [title]="c.title" [attr.aria-label]="c.title"></a>
                }
              </div>
              <span class="jlabel">@if (w.final) { Final<span class="hide-sm"> round</span> } @else { <span class="hide-sm">Week </span>{{ w.num }} }</span>
            </div>
          }
        </div>
        <p class="journey-legend">
          <span><i class="jcell full"></i>Complete</span><span><i class="jcell part"></i>Started</span>
          <span><i class="jcell past"></i>Missed</span><span><i class="jcell today"></i>Today</span>
        </p>
      </div>
    </section>

    @if (isNew()) {
      <section class="card start-here">
        <h2>Start here</h2>
        <p class="muted small">The goal: a product-company offer (~15 LPA) after 60 days of study and 14 days of
          final-round practice.</p>
        <ol>
          <li><b>Set your day 1</b>It is today, {{ startLabel() }}. Started earlier or starting later?
            <a routerLink="/account">Change the start date</a></li>
          <li><b>Work through today's plan</b>Tick each task as you finish it. Every item on the site has a done box
            and a star for revising later</li>
          <li><b>Find weak spots fast</b>Press <kbd>/</kbd> to search everything, or try the
            <a routerLink="/traps">trap of the day</a>, the questions most candidates get wrong</li>
        </ol>
        <p class="muted small">Progress saves in this browser.
          @if (canSync()) { <a routerLink="/account">Sign in with Google</a> to keep it on every device. }</p>
      </section>
    }

    @if (resume(); as r) {
      <a class="card resume" [routerLink]="r.link | link" [attr.data-tone]="sectionOf(r.link)">
        <span class="tile"><app-icon name="book" /></span>
        <span class="grow"><span class="muted small">Continue where you left off</span><br /><b>{{ r.title }}</b></span>
        <span class="btn small primary">Resume</span>
      </a>
    }

    @if (behind() > 0) {
      <div class="banner warn">{{ behind() }} plan {{ behind() === 1 ? 'task' : 'tasks' }} from earlier days still open.
        <a routerLink="/plan">Catch up in the plan</a></div>
    }

    <div class="dash-main">
      <div class="dash-side">
        <section class="card tone-plan">
          <div class="card-head">
            <h2 class="with-tile"><span class="tile"><app-icon name="calendar" /></span>Today's plan</h2>
            <a [routerLink]="todayLink()" class="card-link">Open {{ todayLabel() }} <app-icon name="chevron" /></a>
          </div>
          @if (today(); as d) {
            <p class="muted small">{{ d.focus }}</p>
            <div class="today-meta">
              <span><span class="num">{{ todayDone() }}/{{ d.tasks.length }}</span> done</span>
              <app-progress-bar [done]="todayDone()" [total]="d.tasks.length" [showLabel]="false" />
              <span><span class="num">{{ todayMinutes() }}</span> min</span>
            </div>
            <ul class="tasks">
              @for (t of d.tasks; track t.id) {
                <li [class.done]="progress.isDone(planKey(d.day, t.id))">
                  <app-done-toggle [key]="planKey(d.day, t.id)" section="plan" />
                  <div class="task-body">
                    <span class="task-type" [class]="'task-type tone-' + t.type"><span class="dot"></span><span class="tlabel">{{ typeLabel(t.type) }}</span></span>
                    <span class="task-title">@if (t.link) { <a [routerLink]="t.link | link">{{ t.title }}</a> } @else { <strong>{{ t.title }}</strong> }</span>
                    <span class="task-min">{{ t.minutes }} min</span>
                  </div>
                </li>
              }
            </ul>
          } @else if (progress.currentDay() > 60 && progress.currentDay() <= 74) {
            <p>You're in the final round. Today's set is
              <a [routerLink]="['/final-round', progress.currentDay() - 60]">day {{ progress.currentDay() - 60 }}</a>.</p>
          } @else if (progress.currentDay() > 74) {
            <p>You've finished the plan and the final round. Keep working through your
              <a routerLink="/revision">revision list</a> and take mock interviews again.</p>
          } @else {
            <p class="muted">Loading plan…</p>
          }
        </section>

        <a class="card side-row tone-mock" routerLink="/mock">
          <span class="tile"><app-icon name="mic" /></span>
          <span class="grow"><b>Mock interview</b><br />
            <span class="muted small">10 questions out loud, timed, graded against the model answer</span></span>
          <app-icon name="chevron" class="muted" />
        </a>
      </div>

      <div class="dash-side">
        <section class="card">
          <div class="card-head">
            <h2 class="with-tile tone-today"><span class="tile"><app-icon name="routine" /></span>Routine</h2>
            <a routerLink="/habits" class="card-link">Open <app-icon name="chevron" /></a>
          </div>
          <p class="muted small"><span class="num">{{ routineMet() }}/{{ habits.today().statuses.length }}</span> habits today
            · <span class="num">{{ habits.streak() }}</span>-day streak</p>
          <ul class="habit-list compact">
            @for (st of habits.today().statuses; track st.habit.id) {
              <li [class.met]="st.met">
                <span class="tile sm" [attr.data-tone]="habitTone(st.habit.id)"><app-icon [name]="habitIcon(st.habit.id)" /></span>
                <span class="grow">{{ st.habit.title }}</span>
                <span class="num">{{ st.met ? 'done' : (st.habit.kind === 'plan' ? st.value + '%' : st.habit.kind === 'journal' ? '' : st.value + '/' + st.habit.target) }}</span>
              </li>
            }
          </ul>
          @if (!habits.timerRunning()) {
            <button class="btn small" (click)="habits.startTimer(25)"><app-icon name="timer" />Start a 25-min focus block</button>
          }
        </section>

        @if (trap(); as t) {
          <section class="card trap-teaser tone-traps">
            <div class="card-head">
              <h2 class="with-tile"><span class="tile"><app-icon name="alert" /></span>Trap of the day</h2>
              <a [routerLink]="['/traps', t.id]" class="btn small">Try it</a>
            </div>
            <p><b>{{ t.title }}</b></p>
            <p class="muted small">Most candidates get this one wrong</p>
          </section>
        }
      </div>
    </div>

    <div class="dash-bottom">
      <section class="card">
        <h2>Progress by section</h2>
        <ul class="section-list">
          @for (c of cards; track c.section) {
            <li [attr.data-tone]="c.section"><a [routerLink]="c.link">
              <span class="tile sm"><app-icon [name]="c.icon" /></span>
              <span>{{ c.title }}</span>
              <app-progress-bar [done]="doneFor(c.section)" [total]="totalFor(c.section)" [showLabel]="false" />
              <span class="count" [title]="c.unit"><b>{{ doneFor(c.section) }}</b>/{{ totalFor(c.section) }}</span>
            </a></li>
          }
          <li data-tone="neutral"><a routerLink="/final-round">
            <span class="tile sm"><app-icon name="flask" /></span>
            <span>Quiz attempts</span>
            <span class="muted small">average score {{ avgScore() }}%</span>
            <span class="count"><b>{{ progress.attempts().length }}</b></span>
          </a></li>
        </ul>
      </section>
      <section class="card">
        <h2>Activity · last 12 weeks</h2>
        <div class="heatmap" role="img" aria-label="Items completed per day over the last 12 weeks">
          @for (cell of heatmap(); track cell.date) {
            <span class="cell" [attr.data-l]="cell.level" [title]="cell.date + ': ' + cell.count"></span>
          }
        </div>
        <p class="muted small">One square per day. Darker means more items completed</p>
        <a routerLink="/revision" class="revise-link tone-review"><span class="tile sm"><app-icon name="star" /></span>
          <span><span class="num">{{ reviseCount() }}</span> in your revision list</span>
          @if (dueCount() > 0) { <span class="due">{{ dueCount() }} due</span> }</a>
      </section>
    </div>
  `,
})
export class Dashboard {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private catalog = inject(CatalogService);
  protected habits = inject(HabitService);
  protected planKey = keys.plan;
  private recent = inject(RecentService);
  protected trap = computed(() => {
    const traps = (this.catalogRes.value() ?? [])
      .filter(e => e.section === 'traps')
      .map(e => ({ id: e.key.slice('trap:'.length), title: e.title }));
    return trapOfTheDay(traps, k => this.progress.isDone(k), todayIso());
  });
  /** Nothing tracked yet on this device: show the getting-started steps. */
  protected isNew = computed(() =>
    Object.keys(this.progress.items()).length === 0 && this.progress.attempts().length === 0 && !this.recent.pages().length);
  protected canSync = computed(() => !!GOOGLE_CLIENT_ID || this.progress.backendAvailable());
  protected resume = computed(() => {
    const r = this.recent.pages()[0];
    return r ? { link: r.url, title: r.title } : undefined;
  });
  protected dueCount = computed(() => {
    const now = Date.now();
    return Object.values(this.progress.items()).filter(i => i.revise && isDue(i.updatedAt, now)).length;
  });
  protected habitIcon = habitIcon;
  protected habitTone = habitTone;
  private static TYPE_LABELS: Record<string, string> = {
    dsa: 'DSA', core: 'Core', sd: 'Design', ai: 'AI', mock: 'Mock', revise: 'Revise', career: 'Career', trap: 'Trap', round: 'Round',
  };
  protected typeLabel(t: string) { return Dashboard.TYPE_LABELS[t] ?? t; }
  /** Colour of the area a link points into, e.g. "/dsa/..." is DSA. */
  protected sectionOf(link: string) {
    const first = link.split(/[?#]/)[0].split('/')[1] ?? '';
    return ({ dsa: 'dsa', 'system-design': 'sd', core: 'core', ai: 'ai', traps: 'traps', rounds: 'rounds', 'final-round': 'final',
      plan: 'plan', mock: 'mock' } as Record<string, string>)[first] ?? 'today';
  }
  protected routineMet = computed(() => this.habits.today().statuses.filter(x => x.met).length);

  private planRes = resource({ loader: () => this.content.plan() });
  private catalogRes = resource({ loader: () => this.catalog.all() });

  protected cards: SectionCard[] = [
    { section: 'plan', title: '60-day plan', icon: 'calendar', link: '/plan', unit: 'tasks' },
    { section: 'dsa', title: 'DSA problems', icon: 'code', link: '/dsa', unit: 'problems' },
    { section: 'sd', title: 'System design', icon: 'network', link: '/system-design', unit: 'topics' },
    { section: 'core', title: 'Core subjects', icon: 'book', link: '/core', unit: 'items' },
    { section: 'traps', title: 'Common traps', icon: 'alert', link: '/traps', unit: 'beaten' },
    { section: 'rounds', title: 'Interview rounds', icon: 'compass', link: '/rounds', unit: 'ready' },
    { section: 'final', title: 'Final round', icon: 'flag', link: '/final-round', unit: 'items' },
    { section: 'ai', title: 'AI engineer course', icon: 'cpu', link: '/ai', unit: 'items' },
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
    return d <= 60 ? `day ${d}` : d <= 74 ? `final day ${d - 60}` : 'revision list';
  });
  protected todayLink = computed(() => {
    const d = this.progress.currentDay();
    return d <= 60 ? `/plan/${d}` : d <= 74 ? `/final-round/${d - 60}` : '/revision';
  });
  protected phase = computed(() => {
    const d = this.progress.currentDay();
    if (d <= 60) return `Study phase · week ${Math.ceil(d / 7)} of 9`;
    if (d <= 74) return 'Final round';
    return 'Interview mode';
  });
  protected headline = computed(() => {
    const d = this.progress.currentDay();
    const t = this.today();
    if (d <= 60) return t ? `Day ${d} · ${t.title}` : `Day ${d}`;
    if (d <= 74) return `Final round · day ${d - 60}`;
    return 'Plan complete';
  });
  protected startLabel = computed(() =>
    new Date(this.progress.startDate() + 'T00:00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }));
  protected todayDone = computed(() => {
    const d = this.today();
    return d ? this.progress.countDone(d.tasks.map(t => keys.plan(d.day, t.id))) : 0;
  });
  protected todayMinutes = computed(() => (this.today()?.tasks ?? []).reduce((m, t) => m + t.minutes, 0));

  /** Plan days count as complete when every non-AI task is done, the same rule the plan page uses. */
  private dayState(d: PlanDay): 'full' | 'part' | 'none' {
    const req = d.tasks.filter(t => t.type !== 'ai');
    const n = this.progress.countDone(req.map(t => keys.plan(d.day, t.id)));
    return n && n === req.length ? 'full' : n ? 'part' : 'none';
  }
  protected daysComplete = computed(() => (this.planRes.value()?.days ?? []).filter(d => this.dayState(d) === 'full').length);
  /** The 60 study days by week, then the 14 final-round days, for the journey strip. */
  protected journeyWeeks = computed(() => {
    const cur = this.progress.currentDay();
    const days = this.planRes.value()?.days ?? [];
    const weeks: { label: string; num: number; final: boolean; current: boolean; cells: JourneyCell[] }[] = [];
    for (const d of days) {
      let w = weeks[d.week - 1];
      if (!w) w = weeks[d.week - 1] = { label: `Week ${d.week}`, num: d.week, final: false, current: false, cells: [] };
      if (d.day === cur) w.current = true;
      w.cells.push({ day: d.day, link: `/plan/${d.day}`, state: this.dayState(d), past: d.day < cur, today: d.day === cur,
        title: `Day ${d.day}: ${d.title}` });
    }
    const final: JourneyCell[] = [];
    for (let i = 1; i <= 14; i++) {
      const day = 60 + i;
      final.push({ day, link: `/final-round/${i}`, state: 'none', past: false, today: day === cur, title: `Final round day ${i}` });
    }
    weeks.push({ label: 'Final round', num: 0, final: true, current: cur > 60 && cur <= 74, cells: final });
    return weeks.filter(Boolean);
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
