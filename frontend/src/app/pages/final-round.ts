import { Component, computed, inject, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { FinalDay } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { ProgressBar } from '../shared/ui';

@Component({
  selector: 'app-final-round',
  imports: [RouterLink, ProgressBar],
  template: `
    <h1>Final Round · 14 Days of Real Interview Questions</h1>
    <p class="muted">After the 60-day plan, spend two weeks on questions reported from real online assessments and
      interviews at product companies. Each day has an MCQ test (take it in exam mode), coding questions to solve
      on a timer (35-40 min each, no peeking), and verbal theory questions to answer out loud.
      @if (progress.currentDay() <= 60) { You can start early, but it's most useful after day 60. }</p>
    <div class="grid two">
      @for (d of days(); track d.day) {
        <a class="card day-card" [routerLink]="['/final-round', d.day]"
           [class.today]="d.day === progress.currentDay() - 60">
          <p class="eyebrow">Day {{ d.day }} · journey day {{ d.day + 60 }}</p>
          <h3>{{ d.title }}</h3>
          <p class="muted small">{{ d.theme }}</p>
          <app-progress-bar [done]="itemsDone(d)" [total]="d.coding.length + d.theory.length" />
          <p class="small">
            {{ d.mcqs.length }} MCQs
            @if (progress.bestAttempt(quizKey(d.day)); as b) { · <b>best {{ b.score }}/{{ b.total }}</b> } @else { · not attempted }
            · {{ d.coding.length }} coding · {{ d.theory.length }} theory
          </p>
        </a>
      } @empty {
        <p class="muted">Loading…</p>
      }
    </div>
  `,
})
export class FinalRoundPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private res = resource({ loader: () => this.content.finalRound() });
  protected days = computed(() => this.res.value() ?? []);
  protected quizKey = keys.finalQuiz;
  itemsDone(d: FinalDay) {
    return this.progress.countDone([...d.coding, ...d.theory].map(x => keys.final(x.id ?? '')));
  }
}
