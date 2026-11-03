import { Component, computed, inject, resource, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CatalogEntry, CatalogService } from '../core/catalog.service';
import { ProgressService } from '../core/progress.service';
import { REVIEW_AFTER_DAYS, daysSince, isDue } from '../core/review';
import { DoneToggle, LinkPipe, ReviseToggle } from '../shared/ui';

type View = 'due' | 'revise' | 'notes';

@Component({
  selector: 'app-revision',
  imports: [RouterLink, DoneToggle, ReviseToggle, LinkPipe],
  template: `
    <h1>Revision list</h1>
    <p class="muted">Everything you starred as "revise later", plus anything with a personal note. Re-solve DSA problems
      from scratch without looking at your old code. Spaced repetition beats re-reading: open each item from
      <b>Due now</b>, recall it, then press <b>Reviewed</b> and it comes back in {{ reviewDays }} days. Press
      <b>Mastered</b> once you no longer need it.</p>
    <div class="tabs" role="tablist">
      <button role="tab" [attr.aria-selected]="view() === 'due'" [class.active]="view() === 'due'" (click)="view.set('due')">
        Due now ({{ due().length }})</button>
      <button role="tab" [attr.aria-selected]="view() === 'revise'" [class.active]="view() === 'revise'" (click)="view.set('revise')">
        All starred ({{ starred().length }})</button>
      <button role="tab" [attr.aria-selected]="view() === 'notes'" [class.active]="view() === 'notes'" (click)="view.set('notes')">
        With notes ({{ noted().length }})</button>
    </div>
    @if (res.isLoading()) {
      <p class="muted">Loading…</p>
    } @else {
      @for (g of grouped(); track g.group) {
        <section class="card">
          <h3>{{ g.group }}</h3>
          <ul class="tasks">
            @for (e of g.items; track e.key) {
              <li [class.done]="progress.isDone(e.key)">
                <app-done-toggle [key]="e.key" [section]="e.section" />
                <div class="grow">
                  <a [routerLink]="e.link | link">{{ e.title }}</a>
                  @if (progress.isRevise(e.key)) {
                    <span class="muted small"> · {{ age(e.key) }}</span>
                  }
                  @if (progress.note(e.key)) { <div class="muted small note-preview">{{ progress.note(e.key) }}</div> }
                </div>
                @if (view() === 'due') {
                  <button class="btn small" (click)="reviewed(e)" title="Recalled it: bring it back in {{ reviewDays }} days">Reviewed</button>
                  <button class="btn small" (click)="progress.toggleRevise(e.key, e.section)" title="Remove the star">Mastered</button>
                } @else {
                  <app-revise-toggle [key]="e.key" [section]="e.section" />
                }
              </li>
            }
          </ul>
        </section>
      } @empty {
        <div class="card muted">
          @switch (view()) {
            @case ('due') {
              @if (starred().length) { Nothing due. Everything you starred was reviewed in the last {{ reviewDays }} days. }
              @else { Nothing here yet. Use the star on any problem, topic or question to add it. }
            }
            @case ('revise') { Nothing here yet. Use the star on any problem, topic or question to add it. }
            @case ('notes') { No notes yet. Every problem and topic page has a "My notes" box. }
          }
        </div>
      }
    }
  `,
})
export class RevisionPage {
  protected progress = inject(ProgressService);
  private catalog = inject(CatalogService);
  protected res = resource({ loader: () => this.catalog.all() });
  protected view = signal<View>('due');
  protected reviewDays = REVIEW_AFTER_DAYS;

  private updatedAt = (e: CatalogEntry) => this.progress.items()[e.key]?.updatedAt ?? '';
  protected starred = computed(() => (this.res.value() ?? []).filter(e => this.progress.isRevise(e.key)));
  /** Starred items not touched for a while, the longest-waiting first. */
  protected due = computed(() => {
    const now = Date.now();
    return this.starred()
      .filter(e => isDue(this.progress.items()[e.key]?.updatedAt, now))
      .sort((a, b) => this.updatedAt(a).localeCompare(this.updatedAt(b)));
  });
  protected noted = computed(() => (this.res.value() ?? []).filter(e => !!this.progress.note(e.key)));
  protected grouped = computed(() => {
    const v = this.view();
    const list = v === 'due' ? this.due() : v === 'revise' ? this.starred() : this.noted();
    const map = new Map<string, CatalogEntry[]>();
    list.forEach(e => map.set(e.group, [...(map.get(e.group) ?? []), e]));
    return [...map.entries()].map(([group, items]) => ({ group, items }));
  });

  age(key: string) {
    const d = daysSince(this.progress.items()[key]?.updatedAt);
    return d === undefined ? 'not reviewed yet' : d === 0 ? 'touched today' : `last touched ${d} day${d === 1 ? '' : 's'} ago`;
  }

  /** Any write restarts the review wait (updatedAt), locally and on the server. */
  reviewed(e: CatalogEntry) {
    this.progress.update(e.key, e.section, { revise: true });
  }
}
