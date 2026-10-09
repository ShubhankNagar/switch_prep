import { Component, computed, effect, inject, input, resource, signal, untracked } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { ProgressService } from '../core/progress.service';
import { CodePipe, MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, NoteBox, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-dsa-problem',
  imports: [RouterLink, MarkdownPipe, CodePipe, DoneToggle, ReviseToggle, NoteBox],
  template: `
    @if (data(); as d) {
      <a [routerLink]="['/dsa', d.pattern.id]" class="back">← {{ d.pattern.name }}</a>
      <h1>{{ d.p.title }}</h1>
      <div class="row wrap">
        <span class="tag" [class]="'tag ' + d.p.difficulty.toLowerCase()">{{ d.p.difficulty }}</span>
        @if (d.p.mustDo) { <span class="tag must">must-do</span> }
        @for (c of d.p.companies; track c) { <span class="tag company">{{ c }}</span> }
      </div>
      <div class="row wrap actions">
        <app-done-toggle [key]="key()" section="dsa" label="Mark solved" doneLabel="Solved" />
        <app-revise-toggle [key]="key()" section="dsa" [label]="true" />
        <a class="btn" [href]="d.p.leetcode" target="_blank" rel="noopener">Practice on LeetCode ↗</a>
      </div>

      <section class="card">
        <h2>Problem</h2>
        <div class="md" [innerHTML]="d.p.summary | md"></div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Approach</h2>
          @if (!showApproach()) { <button class="btn small" (click)="showApproach.set(true)">Show approach</button> }
        </div>
        @if (showApproach()) {
          <div class="md" [innerHTML]="d.p.approach | md"></div>
          <p><b>Time:</b> {{ d.p.time }} · <b>Space:</b> {{ d.p.space }}</p>
        } @else {
          <p class="muted">Try for 20-25 minutes before peeking. Struggle is where the learning happens.</p>
        }
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Java solution</h2>
          @if (!showCode()) { <button class="btn small" (click)="showCode.set(true)">Show solution</button> }
          @else { <button class="btn small" (click)="copy(d.p.solution)">{{ copied() ? 'Copied' : 'Copy' }}</button> }
        </div>
        @if (showCode()) { <div [innerHTML]="d.p.solution | code"></div> }
      </section>

      <section class="card"><app-note-box [key]="key()" section="dsa" /></section>

      <div class="row">
        @if (d.prev; as prev) { <a class="btn" [routerLink]="['/dsa', d.pattern.id, prev.id]">← {{ prev.title }}</a> }
        @if (d.next; as next) { <a class="btn primary" [routerLink]="['/dsa', d.pattern.id, next.id]">{{ next.title }} →</a> }
      </div>
    }
  `,
})
export class DsaProblemPage {
  private content = inject(ContentService);
  protected progress = inject(ProgressService);
  pattern = input.required<string>();
  problem = input.required<string>();
  private res = resource({ loader: () => this.content.dsa() });

  protected showApproach = signal(false);
  protected showCode = signal(false);
  protected copied = signal(false);
  protected key = computed(() => keys.dsa(this.problem()));

  protected data = computed(() => {
    const pattern = (this.res.value() ?? []).find(p => p.id === this.pattern());
    if (!pattern) return undefined;
    const i = pattern.problems.findIndex(p => p.id === this.problem());
    return i < 0 ? undefined : { pattern, p: pattern.problems[i], prev: pattern.problems[i - 1], next: pattern.problems[i + 1] };
  });

  constructor() {
    effect(() => {
      this.problem();
      const solved = untracked(() => this.progress.isDone(this.key()));
      this.showApproach.set(solved);
      this.showCode.set(solved);
      this.copied.set(false);
    });
  }

  copy(text: string) {
    navigator.clipboard?.writeText(text).then(() => this.copied.set(true));
  }
}
