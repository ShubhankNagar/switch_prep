import { Component, OnDestroy, computed, inject, input, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Mcq } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from './markdown.pipe';

type QuizQuestion = Omit<Mcq, 'id'> & { id?: string };

/**
 * Runs a set of MCQs. Practice mode reveals the answer after each pick; exam mode
 * (timed) reveals everything on submit. Every submitted attempt is saved via ProgressService.
 */
@Component({
  selector: 'app-quiz',
  imports: [MarkdownPipe, DatePipe],
  template: `
    @if (!started()) {
      <div class="quiz-start card">
        <p><strong>{{ questions().length }} questions.</strong>
          @if (best(); as b) { Best score: {{ b.score }}/{{ b.total }} ({{ b.takenAt | date: 'mediumDate' }}). }
        </p>
        <div class="row">
          <button class="btn primary" (click)="start(false)">Practice mode</button>
          @if (timed()) {
            <button class="btn" (click)="start(true)">Exam mode ({{ minutes() }} min timer)</button>
          }
        </div>
        <p class="muted small">Practice shows the answer as soon as you pick. Exam hides answers until you submit.</p>
      </div>
    } @else {
      <div class="quiz-bar">
        <span>Answered {{ answeredCount() }}/{{ questions().length }}</span>
        @if (exam() && !submitted()) { <span class="timer" [class.low]="remaining() < 60">⏱ {{ clock() }}</span> }
        @if (submitted()) { <span class="score">Score: {{ score() }}/{{ questions().length }} ({{ pct() }}%)</span> }
      </div>
      @for (q of questions(); track $index; let i = $index) {
        <div class="mcq card" [class.correct]="reveal(i) && picked()[i] === q.answer"
             [class.wrong]="reveal(i) && picked()[i] !== undefined && picked()[i] !== q.answer">
          <div class="mcq-head">
            <span class="qnum">Q{{ i + 1 }}</span>
            @if (q.topic) { <span class="tag">{{ q.topic }}</span> }
            @for (c of q.askedAt ?? []; track c) { <span class="tag company">{{ c }}</span> }
          </div>
          <div class="md" [innerHTML]="q.q | md"></div>
          <div class="options">
            @for (opt of q.options; track $index; let o = $index) {
              <button type="button" class="option"
                      [class.picked]="picked()[i] === o"
                      [class.right]="reveal(i) && o === q.answer"
                      [class.bad]="reveal(i) && picked()[i] === o && o !== q.answer"
                      [disabled]="reveal(i)"
                      (click)="pick(i, o)">
                <span class="letter">{{ 'ABCD'[o] }}</span> <span [innerHTML]="opt | md"></span>
              </button>
            }
          </div>
          @if (reveal(i)) {
            <div class="explain md" [innerHTML]="q.explanation | md"></div>
          }
        </div>
      }
      <div class="row">
        @if (!submitted()) {
          <button class="btn primary" (click)="submit()">Submit</button>
        } @else {
          <button class="btn" (click)="restart()">Try again</button>
        }
      </div>
    }
  `,
})
export class Quiz implements OnDestroy {
  private progress = inject(ProgressService);
  questions = input.required<QuizQuestion[]>();
  quizKey = input.required<string>();
  timed = input(false);
  /** Seconds per question in exam mode. */
  secondsPerQuestion = input(60);

  started = signal(false);
  exam = signal(false);
  submitted = signal(false);
  picked = signal<Record<number, number>>({});
  remaining = signal(0);
  private startedAt = 0;
  private timer?: ReturnType<typeof setInterval>;

  best = computed(() => this.progress.bestAttempt(this.quizKey()));
  minutes = computed(() => Math.ceil((this.questions().length * this.secondsPerQuestion()) / 60));
  answeredCount = computed(() => Object.keys(this.picked()).length);
  score = computed(() => this.questions().reduce((s, q, i) => s + (this.picked()[i] === q.answer ? 1 : 0), 0));
  pct = computed(() => Math.round((this.score() / Math.max(1, this.questions().length)) * 100));
  clock = computed(() => {
    const r = this.remaining();
    return `${Math.floor(r / 60)}:${String(r % 60).padStart(2, '0')}`;
  });

  reveal(i: number): boolean {
    return this.submitted() || (!this.exam() && this.picked()[i] !== undefined);
  }

  start(exam: boolean) {
    this.exam.set(exam);
    this.started.set(true);
    this.submitted.set(false);
    this.picked.set({});
    this.startedAt = Date.now();
    if (exam) {
      this.remaining.set(this.questions().length * this.secondsPerQuestion());
      this.timer = setInterval(() => {
        this.remaining.update(r => r - 1);
        if (this.remaining() <= 0) this.submit();
      }, 1000);
    }
  }

  pick(i: number, o: number) {
    if (this.reveal(i)) return;
    this.picked.update(p => ({ ...p, [i]: o }));
    if (!this.exam() && this.answeredCount() === this.questions().length) this.submit();
  }

  submit() {
    if (this.submitted()) return;
    clearInterval(this.timer);
    this.submitted.set(true);
    const answers: Record<string, number> = {};
    this.questions().forEach((q, i) => {
      if (this.picked()[i] !== undefined) answers[q.id ?? String(i)] = this.picked()[i];
    });
    this.progress.addAttempt({
      quizKey: this.quizKey(), score: this.score(), total: this.questions().length,
      answersJson: JSON.stringify(answers), durationSeconds: Math.round((Date.now() - this.startedAt) / 1000),
    });
  }

  restart() {
    this.started.set(false);
  }

  ngOnDestroy() {
    clearInterval(this.timer);
  }
}
