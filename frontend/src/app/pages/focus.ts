import { Component, computed, inject, resource, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ContentService } from '../core/content.service';
import { FocusTier, Section } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, LinkPipe, ProgressBar, ReviseToggle } from '../shared/ui';

const SECTION_BY_PREFIX: [string, Section][] = [
  ['dsa:', 'dsa'], ['sd:', 'sd'], ['note:', 'core'], ['qa:', 'core'], ['fr:', 'final'], ['ai', 'ai'],
  ['trap:', 'traps'], ['round:', 'rounds'], ['plan:', 'plan'],
];
export const sectionOf = (key: string): Section => SECTION_BY_PREFIX.find(([p]) => key.startsWith(p))?.[1] ?? 'core';

@Component({
  selector: 'app-focus',
  imports: [RouterLink, MarkdownPipe, DoneToggle, ReviseToggle, ProgressBar, LinkPipe],
  template: `
    <h1>🎯 High-Yield Focus</h1>
    @if (file(); as f) {
      <div class="md intro" [innerHTML]="f.intro | md"></div>
      <div class="tabs">
        @for (t of f.tiers; track t.id) {
          <button [class.active]="tierId() === t.id" (click)="tierId.set(t.id)">
            {{ t.title }} <span class="muted small">{{ doneIn(t) }}/{{ totalIn(t) }}</span></button>
        }
      </div>
      @if (tier(); as t) {
        <p class="muted">{{ t.description }}</p>
        <app-progress-bar [done]="doneIn(t)" [total]="totalIn(t)" />
        @for (g of t.groups; track g.id) {
          <section class="card focus-group">
            <div class="card-head">
              <h2>{{ g.title }}</h2>
              <span class="muted small">{{ doneOf(g.items) }}/{{ g.items.length }}</span>
            </div>
            <p class="muted small">{{ g.description }}</p>
            <ul class="tasks">
              @for (it of g.items; track it.key) {
                <li [class.done]="progress.isDone(it.key)">
                  <app-done-toggle [key]="it.key" [section]="section(it.key)" />
                  <div class="grow">
                    <span class="tag">{{ it.kind }}</span>
                    <a [routerLink]="it.link | link">{{ it.title }}</a>
                    @if (it.why) { <div class="muted small">{{ it.why }}</div> }
                  </div>
                  <app-revise-toggle [key]="it.key" [section]="section(it.key)" />
                </li>
              }
            </ul>
          </section>
        }
      }
    } @else {
      <p class="muted">Loading…</p>
    }
  `,
})
export class FocusPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private res = resource({ loader: () => this.content.focus() });
  protected file = computed(() => this.res.value());
  protected tierId = signal('tier-1');
  protected tier = computed(() => this.file()?.tiers.find(t => t.id === this.tierId()) ?? this.file()?.tiers[0]);
  section = sectionOf;
  totalIn(t: FocusTier) { return t.groups.reduce((n, g) => n + g.items.length, 0); }
  doneIn(t: FocusTier) { return t.groups.reduce((n, g) => n + this.doneOf(g.items), 0); }
  doneOf(items: { key: string }[]) { return this.progress.countDone(items.map(i => i.key)); }
}
