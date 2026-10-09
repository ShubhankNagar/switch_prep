import { Component, computed, inject, input, signal } from '@angular/core';
import { keys } from '../core/catalog.service';
import { QA } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from './markdown.pipe';
import { DoneToggle, ReviseToggle } from './ui';

/** Expandable question/answer list. With trackKeys, each question has "I know this" + revise toggles. */
@Component({
  selector: 'app-qa-list',
  imports: [MarkdownPipe, DoneToggle, ReviseToggle],
  template: `
    @if (items().length > 3) {
      <div class="row wrap">
        <button class="btn small" (click)="toggleAll()">{{ allOpen() ? 'Collapse all' : 'Expand all' }}</button>
      </div>
    }
    <div class="qa-list">
      @for (item of items(); track $index; let i = $index) {
        <div class="qa card" [class.open]="isOpen(i)" [class.done]="trackKeys() && progress.isDone(k(item))">
          <div class="qa-q" (click)="toggle(i)" role="button" tabindex="0" (keydown.enter)="toggle(i)">
            <span class="chev">{{ isOpen(i) ? '▾' : '▸' }}</span>
            <span class="grow">{{ item.q }}</span>
            @if (item.frequent) { <span class="tag must">frequent</span> }
            @if (item.level) { <span class="tag" [class]="'tag lvl-' + item.level.toLowerCase()">{{ item.level }}</span> }
            @for (c of item.askedAt ?? []; track c) { <span class="tag company">{{ c }}</span> }
          </div>
          @if (isOpen(i)) {
            <div class="qa-a md" [innerHTML]="item.a | md"></div>
            @if (trackKeys()) {
              <div class="row qa-actions">
                <app-done-toggle [key]="k(item)" [section]="section()" label="I can answer this" doneLabel="I know this" />
                <app-revise-toggle [key]="k(item)" [section]="section()" [label]="true" />
              </div>
            }
          }
        </div>
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

  private open = signal<Set<number>>(new Set());
  allOpen = computed(() => this.open().size === this.items().length && this.items().length > 0);

  k(item: QA) { return this.keyFn()(item); }
  isOpen(i: number) { return this.open().has(i); }
  toggle(i: number) {
    this.open.update(s => { const n = new Set(s); n.has(i) ? n.delete(i) : n.add(i); return n; });
  }
  toggleAll() {
    this.open.set(this.allOpen() ? new Set() : new Set(this.items().map((_, i) => i)));
  }
}
