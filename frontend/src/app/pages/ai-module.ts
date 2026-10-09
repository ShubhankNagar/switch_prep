import { Component, computed, inject, input, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, NoteBox } from '../shared/ui';

@Component({
  selector: 'app-ai-module',
  imports: [RouterLink, MarkdownPipe, DoneToggle, NoteBox],
  template: `
    <a routerLink="/ai" class="back">← AI Engineer Course</a>
    @if (data(); as d) {
      <p class="eyebrow">Module {{ d.m.order }} · {{ d.m.level }} · {{ d.m.weeks }} week(s)</p>
      <h1>{{ d.m.title }}</h1>
      <p>{{ d.m.description }}</p>
      <section class="card">
        <h2>You will be able to</h2>
        <ul>@for (o of d.m.outcomes; track $index) { <li>{{ o }}</li> }</ul>
      </section>
      <h2 class="section-title">Lessons</h2>
      <div class="topic-list">
        @for (l of d.m.lessons; track l.id; let i = $index) {
          <a class="card topic" [routerLink]="['/ai', d.m.id, l.id]" [class.done]="progress.isDone(lessonKey(l.id))">
            <app-done-toggle [key]="lessonKey(l.id)" section="ai" />
            <div class="grow"><h3>{{ i + 1 }}. {{ l.title }}</h3></div>
            <span class="muted small">{{ l.minutes }} min
              @if (progress.bestAttempt(quizKey(l.id)); as b) { · quiz {{ b.score }}/{{ b.total }} }</span>
          </a>
        }
      </div>
      <section class="card project">
        <div class="card-head">
          <h2>🛠 Module project: {{ d.m.project.title }}</h2>
          <app-done-toggle [key]="projectKey()" section="ai" label="Mark complete" doneLabel="Completed" />
        </div>
        <div class="md" [innerHTML]="d.m.project.description | md"></div>
        <app-note-box [key]="projectKey()" section="ai" />
      </section>
      <div class="row">
        @if (d.prev; as prev) { <a class="btn" [routerLink]="['/ai', prev.id]">← {{ prev.title }}</a> }
        @if (d.next; as next) { <a class="btn primary" [routerLink]="['/ai', next.id]">{{ next.title }} →</a> }
      </div>
    }
  `,
})
export class AiModulePage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  module = input.required<string>();
  private res = resource({ loader: () => this.content.aiCourse() });
  protected lessonKey = keys.aiLesson;
  protected quizKey = keys.aiQuiz;
  protected projectKey = computed(() => keys.aiProject(this.module()));
  protected data = computed(() => {
    const all = this.res.value() ?? [];
    const i = all.findIndex(m => m.id === this.module());
    return i < 0 ? undefined : { m: all[i], prev: all[i - 1], next: all[i + 1] };
  });
}
