import { Component, computed, inject, resource, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { ProgressService } from '../core/progress.service';
import { DoneToggle, ProgressBar, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-dsa',
  imports: [RouterLink, FormsModule, ProgressBar, DoneToggle, ReviseToggle],
  template: `
    <h1>DSA Problems</h1>
    <p class="muted">{{ total() }} hand-picked problems in {{ patterns().length }} patterns (NeetCode 150 / Blind 75 / Striver SDE
      sheet classics) with approach, Java solution and complexity. Learn a pattern's template first, then solve its problems.
      Aim: all <b>must-do</b> problems by day 45, the rest by day 60.</p>
    <div class="row wrap stats-row">
      <app-progress-bar [done]="solved()" [total]="total()" />
      <span class="tag easy">Easy {{ solvedBy('Easy') }}/{{ countBy('Easy') }}</span>
      <span class="tag medium">Medium {{ solvedBy('Medium') }}/{{ countBy('Medium') }}</span>
      <span class="tag hard">Hard {{ solvedBy('Hard') }}/{{ countBy('Hard') }}</span>
    </div>

    <div class="grid three">
      @for (p of patterns(); track p.id) {
        <a class="card stat-card" [routerLink]="['/dsa', p.id]">
          <h3>{{ p.order }}. {{ p.name }}</h3>
          <app-progress-bar [done]="doneIn(p.problems)" [total]="p.problems.length" />
        </a>
      }
    </div>

    <h2 class="section-title">All problems</h2>
    <div class="filters">
      <input type="search" placeholder="Search problems or companies…" [ngModel]="q()" (ngModelChange)="q.set($event)" />
      <select [ngModel]="difficulty()" (ngModelChange)="difficulty.set($event)">
        <option value="">All difficulties</option><option>Easy</option><option>Medium</option><option>Hard</option>
      </select>
      <select [ngModel]="company()" (ngModelChange)="company.set($event)">
        <option value="">All companies</option>
        @for (c of companies(); track c) { <option>{{ c }}</option> }
      </select>
      <select [ngModel]="status()" (ngModelChange)="status.set($event)">
        <option value="">Any status</option><option value="todo">To do</option><option value="done">Solved</option>
        <option value="revise">Revise later</option><option value="must">Must-do only</option>
      </select>
    </div>
    <table class="table">
      <thead><tr><th></th><th>Problem</th><th>Pattern</th><th>Difficulty</th><th class="hide-sm">Companies</th><th></th></tr></thead>
      <tbody>
        @for (r of rows(); track r.p.id) {
          <tr [class.done]="progress.isDone(key(r.p.id))">
            <td><app-done-toggle [key]="key(r.p.id)" section="dsa" /></td>
            <td><a [routerLink]="['/dsa', r.patternId, r.p.id]">{{ r.p.title }}</a>
              @if (r.p.mustDo) { <span class="tag must">must-do</span> }</td>
            <td class="muted small">{{ r.patternName }}</td>
            <td><span class="tag" [class]="'tag ' + r.p.difficulty.toLowerCase()">{{ r.p.difficulty }}</span></td>
            <td class="hide-sm muted small">{{ r.p.companies.slice(0, 4).join(', ') }}</td>
            <td><app-revise-toggle [key]="key(r.p.id)" section="dsa" /></td>
          </tr>
        } @empty {
          <tr><td colspan="6" class="muted">No problems match these filters.</td></tr>
        }
      </tbody>
    </table>
  `,
})
export class DsaPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private res = resource({ loader: () => this.content.dsa() });
  protected key = keys.dsa;

  protected q = signal('');
  protected difficulty = signal('');
  protected company = signal('');
  protected status = signal('');

  protected patterns = computed(() => this.res.value() ?? []);
  private flat = computed(() => this.patterns().flatMap(p => p.problems.map(pr => ({ p: pr, patternId: p.id, patternName: p.name }))));
  protected total = computed(() => this.flat().length);
  protected solved = computed(() => this.progress.countDone(this.flat().map(r => keys.dsa(r.p.id))));
  protected companies = computed(() => [...new Set(this.flat().flatMap(r => r.p.companies))].sort());

  protected rows = computed(() => {
    const q = this.q().toLowerCase();
    return this.flat().filter(r => {
      const k = keys.dsa(r.p.id);
      if (q && !(r.p.title.toLowerCase().includes(q) || r.p.companies.join(' ').toLowerCase().includes(q))) return false;
      if (this.difficulty() && r.p.difficulty !== this.difficulty()) return false;
      if (this.company() && !r.p.companies.includes(this.company())) return false;
      switch (this.status()) {
        case 'todo': return !this.progress.isDone(k);
        case 'done': return this.progress.isDone(k);
        case 'revise': return this.progress.isRevise(k);
        case 'must': return r.p.mustDo;
      }
      return true;
    });
  });

  countBy(d: string) { return this.flat().filter(r => r.p.difficulty === d).length; }
  solvedBy(d: string) { return this.progress.countDone(this.flat().filter(r => r.p.difficulty === d).map(r => keys.dsa(r.p.id))); }
  doneIn(problems: { id: string }[]) { return this.progress.countDone(problems.map(p => keys.dsa(p.id))); }
}
