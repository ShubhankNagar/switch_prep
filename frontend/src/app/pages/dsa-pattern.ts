import { Component, computed, inject, input, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, ProgressBar, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-dsa-pattern',
  imports: [RouterLink, MarkdownPipe, DoneToggle, ReviseToggle, ProgressBar],
  template: `
    <a routerLink="/dsa" class="back">← All patterns</a>
    @if (data(); as d) {
      <h1>{{ d.p.order }}. {{ d.p.name }}</h1>
      <app-progress-bar [done]="done()" [total]="d.p.problems.length" />
      <section class="card md" [innerHTML]="d.p.intro | md"></section>
      <h2 class="section-title">Problems</h2>
      <table class="table">
        <thead><tr><th></th><th>Problem</th><th>Difficulty</th><th class="hide-sm">Companies</th><th></th></tr></thead>
        <tbody>
          @for (p of d.p.problems; track p.id) {
            <tr [class.done]="progress.isDone(key(p.id))">
              <td><app-done-toggle [key]="key(p.id)" section="dsa" /></td>
              <td><a [routerLink]="['/dsa', d.p.id, p.id]">{{ p.title }}</a>
                @if (p.mustDo) { <span class="tag must">must-do</span> }</td>
              <td><span class="tag" [class]="'tag ' + p.difficulty.toLowerCase()">{{ p.difficulty }}</span></td>
              <td class="hide-sm muted small">{{ p.companies.slice(0, 5).join(', ') }}</td>
              <td><app-revise-toggle [key]="key(p.id)" section="dsa" /></td>
            </tr>
          }
        </tbody>
      </table>
      <div class="row">
        @if (d.prev; as prev) { <a class="btn" [routerLink]="['/dsa', prev.id]">← {{ prev.name }}</a> }
        @if (d.next; as next) { <a class="btn primary" [routerLink]="['/dsa', next.id]">{{ next.name }} →</a> }
      </div>
    }
  `,
})
export class DsaPatternPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  pattern = input.required<string>();
  private res = resource({ loader: () => this.content.dsa() });
  protected key = keys.dsa;

  protected data = computed(() => {
    const all = this.res.value() ?? [];
    const i = all.findIndex(p => p.id === this.pattern());
    return i < 0 ? undefined : { p: all[i], prev: all[i - 1], next: all[i + 1] };
  });
  protected done = computed(() => this.progress.countDone((this.data()?.p.problems ?? []).map(p => keys.dsa(p.id))));
}
