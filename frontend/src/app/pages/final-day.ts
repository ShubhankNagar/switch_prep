import { Component, computed, inject, input, resource, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { QA } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { CodePipe, MarkdownPipe } from '../shared/markdown.pipe';
import { QaList } from '../shared/qa-list';
import { Quiz } from '../shared/quiz';
import { DoneToggle, NoteBox, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-final-day',
  imports: [RouterLink, MarkdownPipe, CodePipe, Quiz, QaList, DoneToggle, ReviseToggle, NoteBox],
  template: `
    <a routerLink="/final-round" class="back">← Final Round</a>
    @if (data(); as d) {
      <p class="eyebrow">Final Round · Day {{ d.day.day }}</p>
      <h1>{{ d.day.title }}</h1>
      <p class="muted">{{ d.day.theme }}</p>
      <div class="tabs">
        <button [class.active]="tab() === 'mcq'" (click)="tab.set('mcq')">MCQ test ({{ d.day.mcqs.length }})</button>
        <button [class.active]="tab() === 'coding'" (click)="tab.set('coding')">Coding ({{ d.day.coding.length }})</button>
        <button [class.active]="tab() === 'theory'" (click)="tab.set('theory')">Theory ({{ d.day.theory.length }})</button>
      </div>
      @switch (tab()) {
        @case ('mcq') {
          <app-quiz [questions]="d.day.mcqs" [quizKey]="quizKey()" [timed]="true" [secondsPerQuestion]="72" />
        }
        @case ('coding') {
          @for (c of d.day.coding; track c.id; let i = $index) {
            <section class="card coding" [class.done]="isDone(c.id)">
              <div class="card-head">
                <h2>{{ i + 1 }}. {{ c.title }}</h2>
                <div class="row">
                  <app-done-toggle [key]="k(c.id)" section="final" label="Solved" doneLabel="Solved" />
                  <app-revise-toggle [key]="k(c.id)" section="final" />
                </div>
              </div>
              <div class="row wrap">
                <span class="tag" [class]="'tag ' + c.difficulty.toLowerCase()">{{ c.difficulty }}</span>
                @for (co of c.askedAt; track co) { <span class="tag company">{{ co }}</span> }
                @if (c.leetcode) { <a [href]="c.leetcode" target="_blank" rel="noopener" class="small">Practice link ↗</a> }
              </div>
              <div class="md" [innerHTML]="c.statement | md"></div>
              <div class="row wrap">
                <button class="btn small" (click)="reveal(c.id, 'h1')">Hint 1</button>
                <button class="btn small" (click)="reveal(c.id, 'h2')">Hint 2</button>
                <button class="btn small" (click)="reveal(c.id, 'sol')">Show solution</button>
              </div>
              @if (shown(c.id, 'h1')) { <p class="hint">💡 {{ c.hints[0] }}</p> }
              @if (shown(c.id, 'h2')) { <p class="hint">💡 {{ c.hints[1] }}</p> }
              @if (shown(c.id, 'sol')) {
                <div class="md" [innerHTML]="c.explanation | md"></div>
                <p><b>Time:</b> {{ c.time }} · <b>Space:</b> {{ c.space }}</p>
                <div [innerHTML]="c.solution | code"></div>
              }
              <app-note-box [key]="k(c.id)" section="final" />
            </section>
          }
        }
        @case ('theory') {
          <p class="muted">Answer each out loud first (as you would in the interview), then open the model answer.</p>
          <app-qa-list [items]="d.day.theory" section="final" [keyFn]="theoryKey" />
        }
      }
      <div class="row">
        @if (d.day.day > 1) { <a class="btn" [routerLink]="['/final-round', d.day.day - 1]">← Day {{ d.day.day - 1 }}</a> }
        @if (d.day.day < d.count) { <a class="btn primary" [routerLink]="['/final-round', d.day.day + 1]">Day {{ d.day.day + 1 }} →</a> }
      </div>
    }
  `,
})
export class FinalDayPage {
  private content = inject(ContentService);
  private progress = inject(ProgressService);
  private progressKeys = keys;
  day = input.required<string>();
  private res = resource({ loader: () => this.content.finalRound() });
  protected tab = signal<'mcq' | 'coding' | 'theory'>('mcq');
  private revealed = signal<Set<string>>(new Set());

  protected data = computed(() => {
    const all = this.res.value() ?? [];
    const d = all.find(x => x.day === Number(this.day()));
    return d ? { day: d, count: all.length } : undefined;
  });
  protected quizKey = computed(() => keys.finalQuiz(Number(this.day())));
  protected theoryKey = (q: QA) => keys.final(q.id ?? q.q);

  k(id: string) { return this.progressKeys.final(id); }
  isDone(id: string) { return this.progress.isDone(keys.final(id)); }
  reveal(id: string, what: string) { this.revealed.update(s => new Set(s).add(id + what)); }
  shown(id: string, what: string) { return this.revealed().has(id + what); }
}
