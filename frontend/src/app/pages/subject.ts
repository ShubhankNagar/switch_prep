import { Component, computed, effect, inject, input, resource, signal, untracked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { QA } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { QaList } from '../shared/qa-list';
import { DoneToggle, ProgressBar, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-subject',
  imports: [RouterLink, FormsModule, MarkdownPipe, QaList, DoneToggle, ReviseToggle, ProgressBar],
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
            <nav class="toc card">
              @for (n of s.notes; track n.id; let i = $index) {
                <button [class.active]="noteIdx() === i" (click)="noteIdx.set(i)">
                  <span [class.ok]="progress.isDone(noteKey(n.id))">{{ progress.isDone(noteKey(n.id)) ? '✓' : (i + 1) + '.' }}</span>
                  {{ n.title }}
                </button>
              }
            </nav>
            @if (s.notes[noteIdx()]; as n) {
              <article class="card md article">
                <h2>{{ n.title }}</h2>
                <div [innerHTML]="n.content | md"></div>
                <div class="row actions">
                  <app-done-toggle [key]="noteKey(n.id)" section="core" label="Mark chapter read" doneLabel="Read" />
                  <app-revise-toggle [key]="noteKey(n.id)" section="core" [label]="true" />
                  @if (noteIdx() < s.notes.length - 1) {
                    <button class="btn primary" (click)="noteIdx.set(noteIdx() + 1)">Next chapter →</button>
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
            <input type="search" placeholder="Search questions…" [ngModel]="q()" (ngModelChange)="q.set($event)" />
            <select [ngModel]="level()" (ngModelChange)="level.set($event)">
              <option value="">All levels</option><option>Basic</option><option>Intermediate</option><option>Advanced</option>
            </select>
            <select [ngModel]="status()" (ngModelChange)="status.set($event)">
              <option value="">Any status</option><option value="frequent">Frequently asked</option>
              <option value="frequent-todo">Frequently asked, not yet known</option>
              <option value="todo">Not yet known</option><option value="done">Known</option><option value="revise">Revise later</option>
            </select>
          </div>
          <app-progress-bar [done]="qaDone()" [total]="s.qa.length" />
          <app-qa-list [items]="filtered()" />
        }
        @case ('cards') {
          @if (card(); as c) {
            <div class="flashcard card">
              <p class="muted small">Card {{ cardPos() + 1 }} of {{ deck().length }} · unknown questions first</p>
              <h2>{{ c.q }}</h2>
              @if (revealed()) {
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
            <div class="card"><p>Deck finished. 🎉</p><button class="btn" (click)="startCards()">Shuffle again</button></div>
          }
        }
      }
      @if (s.sources.length) {
        <section class="sources muted small"><b>Sources:</b>
          @for (src of s.sources; track src.url) { <a [href]="src.url" target="_blank" rel="noopener">{{ src.title }}</a> }
        </section>
      }
    }
  `,
})
export class SubjectPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  subject_ = input.required<string>({ alias: 'subject' });
  /** Optional query params from plan links: ?view=qa, ?chapter=3 (1-based), ?filter=frequent-todo. */
  view = input<string>();
  chapter = input<string>();
  filter = input<string>();
  private res = resource({ loader: () => this.content.subjects() });

  protected subject = computed(() => (this.res.value() ?? []).find(s => s.id === this.subject_()));
  protected tab = signal<'notes' | 'qa' | 'cards'>('notes');
  protected noteIdx = signal(0);
  protected q = signal('');
  protected level = signal('');
  protected status = signal('');

  constructor() {
    effect(() => {
      const view = this.view();
      const chapter = Number(this.chapter());
      const filter = this.filter();
      untracked(() => {
        this.status.set(filter ?? '');
        if (view === 'qa' || view === 'cards') this.tab.set('qa');
        else this.tab.set('notes');
        this.noteIdx.set(chapter > 0 ? chapter - 1 : 0);
      });
    });
  }

  noteKey(id: string) { return keys.note(this.subject_(), id); }
  private qaKey(item: QA) { return keys.qa(item.id ?? item.q); }

  protected notesDone = computed(() => this.progress.countDone((this.subject()?.notes ?? []).map(n => this.noteKey(n.id))));
  protected qaDone = computed(() => this.progress.countDone((this.subject()?.qa ?? []).map(x => this.qaKey(x))));

  protected filtered = computed(() => {
    const q = this.q().toLowerCase();
    return (this.subject()?.qa ?? []).filter(item => {
      const k = this.qaKey(item);
      if (q && !(item.q.toLowerCase().includes(q) || item.a.toLowerCase().includes(q))) return false;
      if (this.level() && item.level !== this.level()) return false;
      switch (this.status()) {
        case 'frequent': return !!item.frequent;
        case 'frequent-todo': return !!item.frequent && !this.progress.isDone(k);
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

  startCards() {
    const qa = [...(this.subject()?.qa ?? [])].sort(() => Math.random() - 0.5);
    qa.sort((a, b) => Number(this.progress.isDone(this.qaKey(a))) - Number(this.progress.isDone(this.qaKey(b))));
    this.deck.set(qa);
    this.cardPos.set(0);
    this.revealed.set(false);
    this.tab.set('cards');
  }

  answerCard(knew: boolean) {
    const c = this.card();
    if (!c) return;
    const k = this.qaKey(c);
    this.progress.update(k, 'core', knew ? { done: true } : { revise: true });
    this.revealed.set(false);
    this.cardPos.update(p => p + 1);
  }
}
