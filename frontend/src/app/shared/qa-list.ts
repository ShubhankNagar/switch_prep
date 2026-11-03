import { Component, computed, effect, inject, input, resource, signal, untracked } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { QA, subjectOfQa } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from './markdown.pipe';
import { DoneToggle, ReviseToggle } from './ui';

/** Expandable question/answer list. With trackKeys, each question has "I know this" + revise toggles. */
@Component({
  selector: 'app-qa-list',
  imports: [RouterLink, MarkdownPipe, DoneToggle, ReviseToggle],
  template: `
    @if (items().length > 3) {
      <div class="row wrap">
        <button class="btn small" (click)="toggleAll()">{{ allOpen() ? 'Collapse all' : 'Expand all' }}</button>
      </div>
    }
    <div class="qa-list">
      @for (item of items(); track id(item)) {
        <div class="qa card" [id]="'item-' + id(item)" [class.open]="isOpen(item)" [class.done]="trackKeys() && progress.isDone(k(item))">
          <div class="qa-q" (click)="toggle(item)" role="button" tabindex="0" [attr.aria-expanded]="isOpen(item)"
               (keydown.enter)="toggle(item)" (keydown.space)="$event.preventDefault(); toggle(item)">
            <span class="chev" aria-hidden="true">{{ isOpen(item) ? '▾' : '▸' }}</span>
            <span class="grow">{{ item.q }}</span>
            @if (isCore(item)) { <span class="tag must">core</span> }
            @if (item.level) { <span class="tag" [class]="'tag lvl-' + item.level.toLowerCase()">{{ item.level }}</span> }
            @for (c of item.askedAt ?? []; track c) { <span class="tag company">{{ c }}</span> }
          </div>
          @if (isOpen(item)) {
            @if (dupOf(item); as main) {
              <p class="dup-note">Same question as in
                <a [routerLink]="['/core', subjectOf(main)]" [queryParams]="{ view: 'qa', qa: main }">{{ subjectName(main) }}</a>,
                which is the copy to study. The answer below is kept for reference.</p>
            }
            @if (short(item); as s) {
              <div class="say-first"><span class="say-label">Say this first</span>{{ s }}</div>
              @if (fullOpen().has(id(item))) {
                <div class="qa-a md" [innerHTML]="item.a | md"></div>
              } @else {
                <button class="link more-link" (click)="showFull(item)">Full answer: how it works, examples, trade-offs ▾</button>
              }
            } @else {
              <div class="qa-a md" [innerHTML]="item.a | md"></div>
            }
            @if (trackKeys()) {
              <div class="row qa-actions">
                <app-done-toggle [key]="k(item)" [section]="section()" label="I can answer this" doneLabel="I know this" />
                <app-revise-toggle [key]="k(item)" [section]="section()" [label]="true" />
              </div>
            }
          }
        </div>
      } @empty {
        <p class="muted">No questions match.</p>
      }
    </div>
  `,
})
export class QaList {
  protected progress = inject(ProgressService);
  items = input.required<QA[]>();
  trackKeys = input(true);
  section = input<'core' | 'final'>('core');
  /** Builds the progress key for an item. */
  keyFn = input<(q: QA) => string>(q => keys.qa(q.id ?? q.q));
  /** Opens every item whose id is listed (used by deep links from search and the revision list). */
  openIds = input<string[]>([]);

  private open = signal<Set<string>>(new Set());
  private content = inject(ContentService);
  private coaching = resource({ loader: () => this.content.coreCoaching() });
  allOpen = computed(() => this.items().length > 0 && this.items().every(i => this.open().has(this.id(i))));

  constructor() {
    effect(() => {
      const ids = this.openIds();
      untracked(() => { if (ids.length) this.open.update(s => new Set([...s, ...ids])); });
    });
  }

  id(item: QA) { return item.id ?? item.q; }
  /** The one or two sentences to lead with, when the question has one (learn-core.json). */
  short(item: QA) { return item.id ? this.coaching.value()?.qa[item.id] : undefined; }
  private coreSet = computed(() => new Set(this.coaching.value()?.core ?? []));
  isCore(item: QA) { return !!item.id && this.coreSet().has(item.id); }
  dupOf(item: QA) { return item.id ? this.coaching.value()?.dupOf[item.id] : undefined; }
  subjectOf = subjectOfQa;
  subjectName(qaId: string) { return subjectOfQa(qaId).replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()); }

  /** Full answers opened under a short answer. The short answer is what to learn; the full one is depth. */
  protected fullOpen = signal<Set<string>>(new Set());
  showFull(item: QA) { this.fullOpen.update(s => new Set(s).add(this.id(item))); }
  k(item: QA) { return this.keyFn()(item); }
  isOpen(item: QA) { return this.open().has(this.id(item)); }
  toggle(item: QA) {
    const id = this.id(item);
    this.open.update(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }
  toggleAll() {
    this.open.set(this.allOpen() ? new Set() : new Set(this.items().map(i => this.id(i))));
  }
}
