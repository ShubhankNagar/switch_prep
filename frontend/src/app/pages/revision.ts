import { Component, computed, inject, resource, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CatalogService } from '../core/catalog.service';
import { ProgressService } from '../core/progress.service';
import { DoneToggle, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-revision',
  imports: [RouterLink, DoneToggle, ReviseToggle],
  template: `
    <h1>★ Revision List</h1>
    <p class="muted">Everything you starred as "revise later", plus anything with a personal note. Re-solve DSA problems
      from scratch without looking at your old code. Spaced repetition beats re-reading: revisit each item after 1, 3 and 7 days.</p>
    <div class="tabs">
      <button [class.active]="view() === 'revise'" (click)="view.set('revise')">Starred ({{ starred().length }})</button>
      <button [class.active]="view() === 'notes'" (click)="view.set('notes')">With notes ({{ noted().length }})</button>
    </div>
    @for (g of grouped(); track g.group) {
      <section class="card">
        <h3>{{ g.group }}</h3>
        <ul class="tasks">
          @for (e of g.items; track e.key) {
            <li [class.done]="progress.isDone(e.key)">
              <app-done-toggle [key]="e.key" [section]="e.section" />
              <div class="grow">
                <a [routerLink]="e.link">{{ e.title }}</a>
                @if (progress.note(e.key)) { <div class="muted small note-preview">📝 {{ progress.note(e.key) }}</div> }
              </div>
              <app-revise-toggle [key]="e.key" [section]="e.section" />
            </li>
          }
        </ul>
      </section>
    } @empty {
      <div class="card muted">Nothing here yet. Use ☆ on any problem, topic or question to add it.</div>
    }
  `,
})
export class RevisionPage {
  protected progress = inject(ProgressService);
  private catalog = inject(CatalogService);
  private res = resource({ loader: () => this.catalog.all() });
  protected view = signal<'revise' | 'notes'>('revise');

  protected starred = computed(() => (this.res.value() ?? []).filter(e => this.progress.isRevise(e.key)));
  protected noted = computed(() => (this.res.value() ?? []).filter(e => !!this.progress.note(e.key)));
  protected grouped = computed(() => {
    const list = this.view() === 'revise' ? this.starred() : this.noted();
    const map = new Map<string, typeof list>();
    list.forEach(e => map.set(e.group, [...(map.get(e.group) ?? []), e]));
    return [...map.entries()].map(([group, items]) => ({ group, items }));
  });
}
