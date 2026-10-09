import { Component, computed, effect, inject, input, resource, signal, untracked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { ProgressService, todayIso } from '../core/progress.service';
import { TRAP_AREAS, TrapCard, trapOfTheDay } from '../shared/trap-card';
import { ProgressBar } from '../shared/ui';

@Component({
  selector: 'app-traps',
  imports: [FormsModule, RouterLink, TrapCard, ProgressBar],
  template: `
    <h1>🪤 Common Traps</h1>
    <p class="muted">The questions and scenarios most candidates get wrong, picked from what interviewers repeatedly
      probe. Commit to an answer first, then reveal. Each one you beat is a point most other candidates lose.</p>
    <app-progress-bar [done]="doneCount()" [total]="traps().length" />

    @if (daily(); as t) {
      <h2 class="section-title">Trap of the day</h2>
      <app-trap-card [trap]="t" />
    }

    <h2 class="section-title">All traps</h2>
    <div class="area-chips">
      <button class="chip" [class.active]="!areaSel()" (click)="areaSel.set('')">All ({{ traps().length }})</button>
      @for (a of areas(); track a.id) {
        <button class="chip" [class.active]="areaSel() === a.id" (click)="areaSel.set(a.id)">
          {{ a.name }} <span class="muted">{{ a.done }}/{{ a.total }}</span></button>
      }
    </div>
    <div class="filters">
      <select [ngModel]="status()" (ngModelChange)="status.set($event)">
        <option value="">Any status</option><option value="todo">Not attempted</option>
        <option value="done">Beaten</option><option value="revise">In revision list</option>
      </select>
      <select [ngModel]="freq()" (ngModelChange)="freq.set($event)">
        <option value="">Any frequency</option><option>Very common</option><option>Common</option>
      </select>
    </div>
    <div class="trap-index">
      @for (t of filtered(); track t.id) {
        <a class="card topic" [routerLink]="['/traps', t.id]" [class.done]="progress.isDone(key(t.id))">
          <span class="check" [class.on]="progress.isDone(key(t.id))"><span class="box">{{ progress.isDone(key(t.id)) ? '✓' : '' }}</span></span>
          <div class="grow"><h3>{{ t.title }}</h3><p class="muted small">{{ areaName(t.area) }} · {{ t.frequency }}</p></div>
          <span class="tag" [class]="'tag lvl-' + t.level.toLowerCase()">{{ t.level }}</span>
        </a>
      } @empty { <p class="muted">No traps match.</p> }
    </div>
  `,
})
export class TrapsPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  area = input<string>();
  private res = resource({ loader: () => this.content.traps() });
  protected traps = computed(() => this.res.value() ?? []);
  protected key = keys.trap;
  protected areaSel = signal('');
  protected status = signal('');
  protected freq = signal('');

  constructor() {
    effect(() => {
      const a = this.area();
      untracked(() => this.areaSel.set(a ?? ''));
    });
  }

  areaName(a: string) { return TRAP_AREAS[a] ?? a; }
  protected doneCount = computed(() => this.progress.countDone(this.traps().map(t => keys.trap(t.id))));
  protected daily = computed(() => trapOfTheDay(this.traps(), k => this.progress.isDone(k), todayIso()));
  protected areas = computed(() => Object.keys(TRAP_AREAS)
    .map(id => {
      const list = this.traps().filter(t => t.area === id);
      return { id, name: TRAP_AREAS[id], total: list.length, done: this.progress.countDone(list.map(t => keys.trap(t.id))) };
    })
    .filter(a => a.total > 0));
  protected filtered = computed(() => this.traps().filter(t => {
    const k = keys.trap(t.id);
    if (this.areaSel() && t.area !== this.areaSel()) return false;
    if (this.freq() && t.frequency !== this.freq()) return false;
    switch (this.status()) {
      case 'todo': return !this.progress.isDone(k);
      case 'done': return this.progress.isDone(k);
      case 'revise': return this.progress.isRevise(k);
    }
    return true;
  }));
}
