import { Component, OnDestroy, computed, inject, resource, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { QA } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from '../shared/markdown.pipe';

type Grade = 'nailed' | 'partly' | 'missed';
type Pool = 'core' | 'unknown' | 'all';
interface Asked { qa: QA; subjectId: string; subjectName: string; grade?: Grade; seconds?: number; }

/** The stack most interviews probe first; preselected for a quick start. */
const DEFAULT_SUBJECTS = ['java', 'spring-boot', 'sql', 'microservices'];
const QUIZ_KEY = 'mock:core';

/**
 * Mock technical interview: questions from the chosen subjects, one at a time, answered out loud against a timer,
 * then compared with the model answer and self-graded. Misses go to the revision list.
 */
@Component({
  selector: 'app-mock',
  imports: [RouterLink, MarkdownPipe],
  template: `
    <h1>🎤 Mock Interview</h1>
    @switch (phase()) {
      @case ('setup') {
        <p class="muted">Practise the way the round actually works: a question, you answer out loud with a timer
          running, then compare with the model answer and grade yourself honestly. Questions you miss go to your
          <a routerLink="/revision">revision list</a>.</p>
        <section class="card">
          <h2>1. Subjects</h2>
          <div class="area-chips">
            @for (s of subjects(); track s.id) {
              <button class="chip" [class.active]="chosen().has(s.id)" (click)="toggleSubject(s.id)"
                      [attr.aria-pressed]="chosen().has(s.id)">{{ s.icon }} {{ s.name }}</button>
            } @empty { <span class="muted">Loading subjects…</span> }
          </div>
          <h2>2. Which questions</h2>
          <div class="area-chips">
            <button class="chip" [class.active]="pool() === 'core'" (click)="pool.set('core')">Core questions</button>
            <button class="chip" [class.active]="pool() === 'unknown'" (click)="pool.set('unknown')">Not yet known</button>
            <button class="chip" [class.active]="pool() === 'all'" (click)="pool.set('all')">All</button>
          </div>
          <h2>3. Length</h2>
          <div class="area-chips">
            @for (n of [5, 10, 15]; track n) {
              <button class="chip" [class.active]="count() === n" (click)="count.set(n)">{{ n }} questions</button>
            }
            @for (t of [60, 120, 180]; track t) {
              <button class="chip" [class.active]="seconds() === t" (click)="seconds.set(t)">{{ t / 60 }} min each</button>
            }
          </div>
          <p class="muted small">{{ available() }} questions match. Answering format that scores well: the one-line answer
            first, then how it works, one example from your project, and the trade-off.</p>
          <button class="btn primary" [disabled]="available() === 0" (click)="start()">Start the interview</button>
        </section>
      }
      @case ('asking') {
        @if (current(); as a) {
          <div class="quiz-bar">
            <span>Question {{ pos() + 1 }} of {{ asked().length }} · {{ a.subjectName }}</span>
            <span class="timer" [class.low]="remaining() <= 15">
              {{ remaining() > 0 ? '⏱ ' + clock() : "⏱ Time's up: wrap up in one sentence" }}</span>
          </div>
          <section class="card mock-q">
            <div class="md mock-question" [innerHTML]="a.qa.q | md"></div>
            @if (!revealed()) {
              <p class="muted">Answer out loud now, as if the interviewer were listening.</p>
              <button class="btn primary" (click)="reveal()">I've answered, show the model answer</button>
            } @else {
              @if (a.qa.id && coaching.value()?.qa?.[a.qa.id]; as s) {
                <div class="say-first"><span class="say-label">Strong opening</span>{{ s }}</div>
              }
              <div class="md" [innerHTML]="a.qa.a | md"></div>
              <p><b>How did you do?</b></p>
              <div class="row wrap">
                <button class="btn primary" (click)="grade('nailed')">Nailed it</button>
                <button class="btn" (click)="grade('partly')">Partly: revise it</button>
                <button class="btn" (click)="grade('missed')">Missed it: revise it</button>
              </div>
            }
          </section>
          <button class="link" (click)="finish()">End the interview now</button>
        }
      }
      @case ('done') {
        <section class="card hero">
          <div>
            <p class="eyebrow">Result</p>
            <h2>{{ nailed() }} of {{ graded().length }} nailed</h2>
            <p class="muted">{{ verdict() }}</p>
          </div>
          <div class="hero-stats">
            <div><b>{{ nailed() }}</b><span>nailed</span></div>
            <div><b>{{ partly() }}</b><span>partly</span></div>
            <div><b>{{ missed() }}</b><span>missed</span></div>
          </div>
        </section>
        <section class="card">
          <h2>Review</h2>
          <ul class="tasks">
            @for (a of graded(); track a.qa.id) {
              <li>
                <span class="tag" [class]="'tag grade-' + a.grade">{{ a.grade }}</span>
                <div class="grow">
                  <a [routerLink]="['/core', a.subjectId]" [queryParams]="{ view: 'qa', qa: a.qa.id }">{{ a.qa.q }}</a>
                  <span class="muted small"> · {{ a.subjectName }} · {{ a.seconds }} s</span>
                </div>
              </li>
            }
          </ul>
          <div class="row wrap">
            <button class="btn primary" (click)="phase.set('setup')">Another round</button>
            <a class="btn" routerLink="/revision">Open the revision list</a>
          </div>
        </section>
      }
    }
  `,
})
export class MockPage implements OnDestroy {
  private content = inject(ContentService);
  private progress = inject(ProgressService);
  private res = resource({ loader: () => this.content.subjects() });
  protected coaching = resource({ loader: () => this.content.coreCoaching() });

  protected phase = signal<'setup' | 'asking' | 'done'>('setup');
  protected chosen = signal<Set<string>>(new Set(DEFAULT_SUBJECTS));
  protected pool = signal<Pool>('core');
  protected count = signal(10);
  protected seconds = signal(120);

  protected asked = signal<Asked[]>([]);
  protected pos = signal(0);
  protected revealed = signal(false);
  protected remaining = signal(0);
  private questionStart = 0;
  private startedAt = 0;
  private timer?: ReturnType<typeof setInterval>;

  protected subjects = computed(() => this.res.value() ?? []);
  private coreQa = computed(() => new Set(this.coaching.value()?.core ?? []));
  private candidates = computed(() => {
    const out: Asked[] = [];
    for (const s of this.subjects()) {
      if (!this.chosen().has(s.id)) continue;
      for (const qa of s.qa) {
        const known = this.progress.isDone(keys.qa(qa.id ?? qa.q));
        const pool = this.pool();
        if (pool === 'core' && !this.coreQa().has(qa.id ?? '')) continue;
        if (pool === 'unknown' && known) continue;
        out.push({ qa, subjectId: s.id, subjectName: s.name });
      }
    }
    return out;
  });
  protected available = computed(() => this.candidates().length);
  protected current = computed(() => this.asked()[this.pos()]);
  protected graded = computed(() => this.asked().filter(a => a.grade));
  protected nailed = computed(() => this.graded().filter(a => a.grade === 'nailed').length);
  protected partly = computed(() => this.graded().filter(a => a.grade === 'partly').length);
  protected missed = computed(() => this.graded().filter(a => a.grade === 'missed').length);
  protected clock = computed(() => {
    const r = Math.max(0, this.remaining());
    return `${Math.floor(r / 60)}:${String(r % 60).padStart(2, '0')}`;
  });
  protected verdict = computed(() => {
    const n = this.graded().length;
    const ratio = n ? this.nailed() / n : 0;
    if (ratio >= 0.8) return 'Interview-ready on these topics. Move on to weaker subjects or harder questions.';
    if (ratio >= 0.5) return 'Close. Revise the partly and missed ones today, then run another round tomorrow.';
    return 'Read the notes for these subjects first, then retry. The missed questions are in your revision list.';
  });

  toggleSubject(id: string) {
    this.chosen.update(s => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  }

  start() {
    // questions you do not know yet come first, shuffled within each group
    const shuffled = [...this.candidates()].sort(() => Math.random() - 0.5);
    const isKnown = (a: Asked) => Number(this.progress.isDone(keys.qa(a.qa.id ?? a.qa.q)));
    shuffled.sort((a, b) => isKnown(a) - isKnown(b));
    this.asked.set(shuffled.slice(0, this.count()).map(a => ({ ...a })));
    this.pos.set(0);
    this.startedAt = Date.now();
    this.phase.set('asking');
    this.beginQuestion();
  }

  reveal() {
    this.revealed.set(true);
    clearInterval(this.timer);
  }

  grade(g: Grade) {
    const a = this.current();
    if (!a) return;
    const key = keys.qa(a.qa.id ?? a.qa.q);
    this.progress.update(key, 'core', g === 'nailed' ? { done: true } : { revise: true });
    const seconds = Math.round((Date.now() - this.questionStart) / 1000);
    this.asked.update(list => list.map((x, i) => (i === this.pos() ? { ...x, grade: g, seconds } : x)));
    if (this.pos() + 1 < this.asked().length) {
      this.pos.update(p => p + 1);
      this.beginQuestion();
    } else {
      this.finish();
    }
  }

  finish() {
    clearInterval(this.timer);
    const done = this.graded();
    if (done.length) {
      this.progress.addAttempt({
        quizKey: QUIZ_KEY, score: this.nailed(), total: done.length,
        answersJson: JSON.stringify(Object.fromEntries(done.map(a => [a.qa.id, a.grade]))),
        durationSeconds: Math.round((Date.now() - this.startedAt) / 1000),
      });
    }
    this.phase.set('done');
  }

  private beginQuestion() {
    this.revealed.set(false);
    this.remaining.set(this.seconds());
    this.questionStart = Date.now();
    clearInterval(this.timer);
    this.timer = setInterval(() => this.remaining.update(r => r - 1), 1000);
  }

  ngOnDestroy() {
    clearInterval(this.timer);
  }
}
