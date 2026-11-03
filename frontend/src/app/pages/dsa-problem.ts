import { Component, computed, effect, inject, input, resource, signal, untracked } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { RecentService } from '../core/recent.service';
import { ProgressService } from '../core/progress.service';
import { CodePipe, MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, NoteBox, PageState, ReviseToggle } from '../shared/ui';
import { Icon } from '../shared/icon';

/** How far the learner has unlocked help on an unsolved problem. Each step reveals one more layer. */
type Step = 0 | 1 | 2 | 3 | 4;

@Component({
  selector: 'app-dsa-problem',
  imports: [Icon, RouterLink, MarkdownPipe, CodePipe, DoneToggle, ReviseToggle, NoteBox, PageState],
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

      <details class="card interview-flow">
        <summary><b>How to run this in an interview</b> <span class="muted small">(the 45-minute shape)</span></summary>
        <ol>
          <li><b>Clarify</b> inputs, sizes and output; restate the problem in one sentence.</li>
          <li><b>Examples and edge cases</b>: walk one example by hand and say the edge cases out loud.</li>
          <li><b>Brute force first</b> with its complexity, then say why it is too slow.</li>
          <li><b>Optimise</b>: name the pattern and the data structure, and agree the plan before coding.</li>
          <li><b>Code</b> in small, named pieces while explaining.</li>
          <li><b>Dry-run</b> your code on the example and one edge case; fix bugs you find.</li>
          <li><b>Complexity</b>: time and space, and what you would change for a follow-up.</li>
        </ol>
      </details>

      @if (coach(); as c) {
        <section class="card coach">
          <h2>Before you code</h2>
          <div class="coach-block">
            <h3>Edge cases to say out loud</h3>
            <ul>@for (e of c.edge; track $index) { <li [innerHTML]="e | md"></li> }</ul>
          </div>
          @if (step() >= 1) {
            <div class="coach-block">
              <h3><app-icon name="search" />How to recognise it</h3>
              <div class="md" [innerHTML]="c.cue | md"></div>
            </div>
          }
          @if (step() >= 2) {
            <div class="coach-block">
              <h3><app-icon name="wrench" />Brute force (start here in the interview)</h3>
              <div class="md" [innerHTML]="c.brute | md"></div>
            </div>
          }
          @if (step() < 2) {
            <div class="row wrap">
              <button class="btn small" (click)="nextHint()">
                {{ step() === 0 ? 'Stuck? Hint 1: how to recognise it' : 'Hint 2: the brute force' }}</button>
              <span class="muted small">Try 20-25 minutes before each hint. Struggle is where the learning happens.</span>
            </div>
          }
        </section>
      }

      <section class="card">
        <div class="card-head">
          <h2>Approach</h2>
          @if (step() < 3) { <button class="btn small" (click)="step.set(3)">Show approach</button> }
        </div>
        @if (step() >= 3) {
          <div class="md" [innerHTML]="d.p.approach | md"></div>
          <p><b>Time:</b> {{ d.p.time }} · <b>Space:</b> {{ d.p.space }}</p>
        } @else {
          <p class="muted">Write your own plan first, even three lines, then compare.</p>
        }
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Java solution</h2>
          @if (step() < 4) { <button class="btn small" (click)="step.set(4)">Show solution</button> }
          @else { <button class="btn small" (click)="copy(d.p.solution)">{{ copied() ? 'Copied' : 'Copy' }}</button> }
        </div>
        @if (step() >= 4) {
          <div [innerHTML]="d.p.solution | code"></div>
          @if (coach(); as c) {
            <div class="coach-block bug">
              <h3><app-icon name="alert" />The bug most people write</h3>
              <div class="md" [innerHTML]="c.bug | md"></div>
            </div>
            @if (c.follow; as f) {
              <div class="coach-block">
                <h3><app-icon name="message" />Likely follow-up</h3>
                <p><b>{{ f.q }}</b></p>
                @if (showFollow()) { <div class="md" [innerHTML]="f.a | md"></div> }
                @else { <button class="btn small" (click)="showFollow.set(true)">Think first, then show the answer</button> }
              </div>
            }
          }
        }
      </section>

      <section class="card"><app-note-box [key]="key()" section="dsa" /></section>

      <div class="row">
        @if (d.prev; as prev) { <a class="btn" [routerLink]="['/dsa', d.pattern.id, prev.id]">← {{ prev.title }}</a> }
        @if (d.next; as next) { <a class="btn primary" [routerLink]="['/dsa', d.pattern.id, next.id]">{{ next.title }} →</a> }
      </div>
    } @else {
      <app-page-state [loading]="res.isLoading()" backLink="/dsa" backLabel="All DSA problems" />
    }
  `,
})
export class DsaProblemPage {
  private content = inject(ContentService);
  protected progress = inject(ProgressService);
  pattern = input.required<string>();
  problem = input.required<string>();
  protected res = resource({ loader: () => this.content.dsa() });
  private coachRes = resource({ loader: () => this.content.dsaCoaching() });

  protected step = signal<Step>(0);
  protected showFollow = signal(false);
  protected copied = signal(false);
  protected key = computed(() => keys.dsa(this.problem()));
  protected coach = computed(() => this.coachRes.value()?.[this.problem()]);

  protected data = computed(() => {
    const pattern = (this.res.value() ?? []).find(p => p.id === this.pattern());
    if (!pattern) return undefined;
    const i = pattern.problems.findIndex(p => p.id === this.problem());
    return i < 0 ? undefined : { pattern, p: pattern.problems[i], prev: pattern.problems[i - 1], next: pattern.problems[i + 1] };
  });

  constructor() {
    inject(RecentService).track(() => {
      const d = this.data();
      return d ? d.p.title : undefined;
    });
    // a solved problem opens fully revealed, for revision; an unsolved one starts with no help shown
    effect(() => {
      this.problem();
      const solved = untracked(() => this.progress.isDone(this.key()));
      this.step.set(solved ? 4 : 0);
      this.showFollow.set(false);
      this.copied.set(false);
    });
  }

  nextHint() {
    this.step.update(s => (s < 4 ? s + 1 : s) as Step);
  }

  copy(text: string) {
    navigator.clipboard?.writeText(text).then(() => this.copied.set(true));
  }
}
