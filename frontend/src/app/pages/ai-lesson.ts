import { Component, computed, inject, input, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { Quiz } from '../shared/quiz';
import { DoneToggle, NoteBox, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-ai-lesson',
  imports: [RouterLink, MarkdownPipe, Quiz, DoneToggle, ReviseToggle, NoteBox],
  template: `
    @if (data(); as d) {
      <a [routerLink]="['/ai', d.m.id]" class="back">← {{ d.m.title }}</a>
      <p class="eyebrow">Module {{ d.m.order }} · Lesson {{ d.index + 1 }} of {{ d.m.lessons.length }} · {{ d.l.minutes }} min</p>
      <h1>{{ d.l.title }}</h1>
      <div class="row wrap actions">
        <app-done-toggle [key]="key()" section="ai" label="Mark lesson complete" doneLabel="Completed" />
        <app-revise-toggle [key]="key()" section="ai" [label]="true" />
      </div>
      <article class="card md article" [innerHTML]="d.l.content | md"></article>
      <section class="card">
        <h2>🧪 Exercise</h2>
        <div class="md" [innerHTML]="d.l.exercise | md"></div>
      </section>
      @if (d.l.quiz.length) {
        <h2 class="section-title">Check your understanding</h2>
        <app-quiz [questions]="d.l.quiz" [quizKey]="quizKey()" />
      }
      <section class="card"><app-note-box [key]="key()" section="ai" /></section>
      @if (d.l.resources.length) {
        <section class="card">
          <h2>Go deeper (free)</h2>
          <ul class="resources">
            @for (r of d.l.resources; track r.url) {
              <li><span class="tag">{{ r.type }}</span> <a [href]="r.url" target="_blank" rel="noopener">{{ r.title }}</a></li>
            }
          </ul>
        </section>
      }
      <div class="row">
        @if (d.prev; as prev) { <a class="btn" [routerLink]="['/ai', d.m.id, prev.id]">← {{ prev.title }}</a> }
        @if (d.next; as next) { <a class="btn primary" [routerLink]="['/ai', d.m.id, next.id]">{{ next.title }} →</a> }
        @else { <a class="btn primary" [routerLink]="['/ai', d.m.id]">Module project →</a> }
      </div>
    }
  `,
})
export class AiLessonPage {
  private content = inject(ContentService);
  module = input.required<string>();
  lesson = input.required<string>();
  private res = resource({ loader: () => this.content.aiCourse() });
  protected key = computed(() => keys.aiLesson(this.lesson()));
  protected quizKey = computed(() => keys.aiQuiz(this.lesson()));
  protected data = computed(() => {
    const m = (this.res.value() ?? []).find(x => x.id === this.module());
    if (!m) return undefined;
    const index = m.lessons.findIndex(l => l.id === this.lesson());
    return index < 0 ? undefined : { m, l: m.lessons[index], index, prev: m.lessons[index - 1], next: m.lessons[index + 1] };
  });
}
