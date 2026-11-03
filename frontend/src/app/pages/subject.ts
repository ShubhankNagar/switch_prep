import { Component, computed, effect, inject, input, resource, signal, untracked } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { QA } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { RecentService } from '../core/recent.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { QaList } from '../shared/qa-list';
import { DoneToggle, PageState, ProgressBar, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-subject',
  imports: [RouterLink, NgTemplateOutlet, FormsModule, MarkdownPipe, QaList, DoneToggle, ReviseToggle, ProgressBar, PageState],
  host: { '(document:keydown)': 'onKey($event)' },
  template: `
    <a routerLink="/core" class="back">← Core Subjects</a>
    @if (subject(); as s) {
      <h1>{{ s.icon }} {{ s.name }}</h1>
      <p class="muted">{{ s.description }}</p>
      <div class="tabs">
        <button [class.active]="tab() === 'notes'" (click)="tab.set('notes')">Notes ({{ notesDone() }}/{{ s.notes.length }})</button>
        <button [class.active]="tab() === 'qa'" (click)="tab.set('qa')">Interview Q&A ({{ qaDone() }}/{{ s.qa.length }})</button>
        <button [class.active]="tab() === 'cards'" (click)="startCards()">Flashcards</button>
      </div>

      @switch (tab()) {
        @case ('notes') {
          <div class="notes-layout">
            <nav class="toc card" aria-label="Chapters">
              @for (i of chapterGroups().core; track i) {
                <ng-container *ngTemplateOutlet="tocItem; context: { $implicit: i }" />
              }
              @if (chapterGroups().optional.length) {
                <details class="toc-more" [open]="!isCoreChapter(noteIdx()) || !chapterGroups().core.length">
                  <summary>More chapters (optional) · {{ chapterGroups().optional.length }}</summary>
                  @for (i of chapterGroups().optional; track i) {
                    <ng-container *ngTemplateOutlet="tocItem; context: { $implicit: i }" />
                  }
                </details>
              }
              <ng-template #tocItem let-i>
                <button [class.active]="noteIdx() === i" (click)="goChapter(i)">
                  <span [class.ok]="progress.isDone(noteKey(s.notes[i].id))">{{ progress.isDone(noteKey(s.notes[i].id)) ? '✓' : (i + 1) + '.' }}</span>
                  {{ s.notes[i].title }}
                </button>
              </ng-template>
            </nav>
            @if (s.notes[noteIdx()]; as n) {
              <article class="card md article">
                <h2>{{ n.title }}</h2>
                @if (guide(n.id); as g) {
                  <aside class="takeaways">
                    <h3>🎯 What to take away</h3>
                    <ul>@for (t of g.takeaways; track $index) { <li [innerHTML]="t | md"></li> }</ul>
                  </aside>
                }
                <div [innerHTML]="n.content | md"></div>
                @if (guide(n.id); as g) {
                  <section class="self-check">
                    <h3>🧠 Check yourself</h3>
                    <p class="muted small">Answer each out loud before revealing. Recalling beats re-reading.</p>
                    @for (c of g.check; track $index; let i = $index) {
                      <div class="check-q">
                        <p><b>{{ i + 1 }}. {{ c.q }}</b></p>
                        @if (checkOpen().has(i)) { <div class="check-a" [innerHTML]="c.a | md"></div> }
                        @else { <button class="btn small" (click)="revealCheck(i)">Reveal</button> }
                      </div>
                    }
                  </section>
                }
                <div class="row actions">
                  <app-done-toggle [key]="noteKey(n.id)" section="core" label="Mark chapter read" doneLabel="Read" />
                  <app-revise-toggle [key]="noteKey(n.id)" section="core" [label]="true" />
                  @if (nextChapter(); as next) {
                    <button class="btn primary" (click)="goChapter(next)">Next chapter →</button>
                  } @else {
                    <button class="btn primary" (click)="tab.set('qa')">Go to Q&A →</button>
                  }
                </div>
              </article>
            }
          </div>
        }
        @case ('qa') {
          <div class="filters">
            <input type="search" placeholder="Search questions…" aria-label="Search questions"
                   [ngModel]="q()" (ngModelChange)="q.set($event); onlyId.set('')" />
            <select [ngModel]="level()" (ngModelChange)="level.set($event)">
              <option value="">All levels</option><option>Basic</option><option>Intermediate</option><option>Advanced</option>
            </select>
            <select [ngModel]="status()" (ngModelChange)="statusChoice.set($event)" aria-label="Which questions">
              @if (coreCount()) {
                <option value="core">Core ({{ coreCount() }})</option>
                <option value="core-todo">Core, not yet known</option>
              }
              <option value="">All questions</option>
              <option value="todo">Not yet known</option><option value="done">Known</option><option value="revise">Revise later</option>
            </select>
          </div>
          <app-progress-bar [done]="qaDone()" [total]="s.qa.length" />
          @if (!onlyId() && (status() === 'core' || status() === 'core-todo')) {
            <p class="muted small">The {{ coreCount() }} core questions are the ones worth knowing cold.
              <button class="link" (click)="statusChoice.set('')">Show all {{ s.qa.length }}</button></p>
          }
          @if (onlyId()) {
            <p class="banner">Showing one question. <button class="link" (click)="onlyId.set('')">Show all {{ s.qa.length }} questions</button></p>
          }
          <app-qa-list [items]="filtered()" [openIds]="onlyId() ? [onlyId()] : []" />
        }
        @case ('cards') {
          @if (card(); as c) {
            <div class="flashcard card">
              <p class="muted small">Card {{ cardPos() + 1 }} of {{ deck().length }} · unknown questions first
                <span class="hide-sm"> · keys: Space to reveal, 1 knew it, 2 didn't</span></p>
              <h2>{{ c.q }}</h2>
              @if (revealed()) {
                @if (c.id && coaching.value()?.qa?.[c.id]; as s) {
                  <div class="say-first"><span class="say-label">Say this first</span>{{ s }}</div>
                }
                <div class="md" [innerHTML]="c.a | md"></div>
                <div class="row">
                  <button class="btn primary" (click)="answerCard(true)">I knew it ✓</button>
                  <button class="btn" (click)="answerCard(false)">Didn't know → revise</button>
                </div>
              } @else {
                <button class="btn primary" (click)="revealed.set(true)">Show answer</button>
              }
            </div>
          } @else {
            <div class="card">
              <p>Deck finished. 🎉 You knew {{ knewCount() }} of {{ deck().length }}.
                @if (deck().length - knewCount() > 0) { The rest are in your <a routerLink="/revision">revision list</a>. }</p>
              <button class="btn" (click)="startCards()">Shuffle again</button>
            </div>
          }
        }
      }
      @if (s.sources.length) {
        <section class="sources muted small"><b>Sources:</b>
          @for (src of s.sources; track src.url) { <a [href]="src.url" target="_blank" rel="noopener">{{ src.title }}</a> }
        </section>
      }
    } @else {
      <app-page-state [loading]="res.isLoading()" backLink="/core" backLabel="All core subjects" />
    }
  `,
})
export class SubjectPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private router = inject(Router);
  subject_ = input.required<string>({ alias: 'subject' });
  /** Optional query params from plan links: ?view=qa, ?chapter=3 (1-based), ?filter=frequent-todo, ?qa=<id>. */
  view = input<string>();
  chapter = input<string>();
  filter = input<string>();
  qa = input<string>();
  protected res = resource({ loader: () => this.content.subjects() });
  protected coaching = resource({ loader: () => this.content.coreCoaching() });
  /** Revealed self-check answers in the current chapter. */
  protected checkOpen = signal<Set<number>>(new Set());

  protected subject = computed(() => (this.res.value() ?? []).find(s => s.id === this.subject_()));
  protected tab = signal<'notes' | 'qa' | 'cards'>('notes');
  /** The chapter picked through the address; without one the first core chapter opens. */
  private chosenIdx = signal<number | null>(null);
  protected noteIdx = computed(() => this.chosenIdx() ?? this.chapterGroups().core[0] ?? 0);
  protected q = signal('');
  protected level = signal('');
  /** null means "not chosen": the list then starts on the core questions when the subject has any. */
  protected statusChoice = signal<string | null>(null);
  protected status = computed(() => this.statusChoice() ?? (this.coreCount() ? 'core' : ''));
  /** Set by a ?qa=<id> link: the list shows only that question, opened. */
  protected onlyId = signal('');

  constructor() {
    effect(() => {
      this.subject_(); // another subject reuses this component: start on its notes, not the old deck
      const view = this.view();
      const chapter = Number(this.chapter());
      const filter = this.filter();
      const qa = this.qa();
      untracked(() => {
        this.statusChoice.set(filter === 'frequent-todo' ? 'core-todo' : filter === 'frequent' ? 'core' : filter ?? null);
        this.onlyId.set(qa ?? '');
        if (view === 'qa' || view === 'cards' || qa) this.tab.set('qa');
        else this.tab.set('notes');
        this.chosenIdx.set(chapter > 0 ? chapter - 1 : null);
        this.checkOpen.set(new Set());
        this.q.set('');
        this.deck.set([]);
      });
    });
    inject(RecentService).track(() => {
      const s = this.subject();
      if (!s) return undefined;
      return this.tab() === 'notes' && s.notes[this.noteIdx()] ? `${s.notes[this.noteIdx()].title} · ${s.name}` : s.name;
    });
  }

  /** Chapters go through the address, so refresh, back and shared links keep the reader's place. */
  goChapter(i: number) {
    void this.router.navigate(['/core', this.subject_()], { queryParams: { chapter: i + 1 } });
  }

  noteKey(id: string) { return keys.note(this.subject_(), id); }
  private coreQa = computed(() => new Set(this.coaching.value()?.core ?? []));
  protected coreCount = computed(() => (this.subject()?.qa ?? []).filter(q => this.coreQa().has(q.id ?? '')).length);
  /** Chapter indexes split into core (scheduled in the plan) and optional depth. */
  protected chapterGroups = computed(() => {
    const core = new Set(this.coaching.value()?.coreNotes ?? []);
    const groups = { core: [] as number[], optional: [] as number[] };
    (this.subject()?.notes ?? []).forEach((n, i) => (core.has(`${this.subject_()}:${n.id}`) ? groups.core : groups.optional).push(i));
    return groups;
  });
  isCoreChapter(i: number) { return this.chapterGroups().core.includes(i); }
  /** Within the core chapters, next goes to the next core chapter; elsewhere, to the next chapter in order. */
  protected nextChapter = computed(() => {
    const { core } = this.chapterGroups();
    const i = this.noteIdx();
    const pos = core.indexOf(i);
    if (pos >= 0) return pos + 1 < core.length ? core[pos + 1] : undefined;
    return i + 1 < (this.subject()?.notes.length ?? 0) ? i + 1 : undefined;
  });
  guide(noteId: string) { return this.coaching.value()?.notes[`${this.subject_()}:${noteId}`]; }
  revealCheck(i: number) { this.checkOpen.update(s => new Set(s).add(i)); }
  private qaKey(item: QA) { return keys.qa(item.id ?? item.q); }

  protected notesDone = computed(() => this.progress.countDone((this.subject()?.notes ?? []).map(n => this.noteKey(n.id))));
  protected qaDone = computed(() => this.progress.countDone((this.subject()?.qa ?? []).map(x => this.qaKey(x))));

  protected filtered = computed(() => {
    const q = this.q().toLowerCase();
    const only = this.onlyId();
    if (only) return (this.subject()?.qa ?? []).filter(item => item.id === only);
    return (this.subject()?.qa ?? []).filter(item => {
      const k = this.qaKey(item);
      if (q && !(item.q.toLowerCase().includes(q) || item.a.toLowerCase().includes(q))) return false;
      if (this.level() && item.level !== this.level()) return false;
      switch (this.status()) {
        case 'core': return this.coreQa().has(item.id ?? '');
        case 'core-todo': return this.coreQa().has(item.id ?? '') && !this.progress.isDone(k);
        case 'todo': return !this.progress.isDone(k);
        case 'done': return this.progress.isDone(k);
        case 'revise': return this.progress.isRevise(k);
      }
      return true;
    });
  });

  // flashcards
  protected deck = signal<QA[]>([]);
  protected cardPos = signal(0);
  protected revealed = signal(false);
  protected card = computed(() => this.deck()[this.cardPos()]);
  protected knewCount = signal(0);

  /** The deck follows the question list's current filter, so by default it drills the core questions. */
  startCards() {
    const qa = [...this.filtered()].sort(() => Math.random() - 0.5);
    qa.sort((a, b) => Number(this.progress.isDone(this.qaKey(a))) - Number(this.progress.isDone(this.qaKey(b))));
    this.deck.set(qa);
    this.cardPos.set(0);
    this.knewCount.set(0);
    this.revealed.set(false);
    this.tab.set('cards');
  }

  answerCard(knew: boolean) {
    const c = this.card();
    if (!c) return;
    const k = this.qaKey(c);
    this.progress.update(k, 'core', knew ? { done: true } : { revise: true });
    if (knew) this.knewCount.update(n => n + 1);
    this.revealed.set(false);
    this.cardPos.update(p => p + 1);
  }

  /** Flashcard shortcuts: Space or Enter reveals, 1 = knew it, 2 = didn't. */
  onKey(e: KeyboardEvent) {
    if (this.tab() !== 'cards' || !this.card() || e.ctrlKey || e.metaKey || e.altKey) return;
    const target = e.target as HTMLElement | null;
    if (target?.closest('input, textarea, select, button, a')) return;
    if (!this.revealed() && (e.key === ' ' || e.key === 'Enter')) {
      e.preventDefault();
      this.revealed.set(true);
    } else if (this.revealed() && (e.key === '1' || e.key === '2')) {
      this.answerCard(e.key === '1');
    }
  }
}
