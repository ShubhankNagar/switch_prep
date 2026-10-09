import { Component, computed, inject, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { AiModule } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { ProgressBar } from '../shared/ui';

@Component({
  selector: 'app-ai-course',
  imports: [RouterLink, ProgressBar],
  template: `
    <h1>AI Engineer Course · Beginner to Advanced</h1>
    <p class="muted">A full path from zero Python to building production LLM apps (RAG, agents, fine-tuning, evals) and doing
      it in Java with Spring AI. Your interview prep comes first: during the 60-day plan, do one lesson on weekends.
      After you switch, go module by module (about {{ totalWeeks() }} weeks at 8-10 hours a week).</p>
    <app-progress-bar [done]="doneAll()" [total]="totalAll()" />
    <div class="module-list">
      @for (m of modules(); track m.id) {
        <a class="card module" [routerLink]="['/ai', m.id]">
          <span class="module-num">{{ m.order }}</span>
          <div class="grow">
            <h3>{{ m.title }}</h3>
            <p class="muted small">{{ m.description }}</p>
            <app-progress-bar [done]="done(m)" [total]="m.lessons.length + 1" />
          </div>
          <div class="topic-meta">
            <span class="tag" [class]="'tag lvl-' + m.level.toLowerCase()">{{ m.level }}</span>
            <span class="muted small">{{ m.lessons.length }} lessons · {{ m.weeks }} wk</span>
          </div>
        </a>
      } @empty { <p class="muted">Loading…</p> }
    </div>
  `,
})
export class AiCoursePage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private res = resource({ loader: () => this.content.aiCourse() });
  protected modules = computed(() => this.res.value() ?? []);
  protected totalWeeks = computed(() => Math.round(this.modules().reduce((s, m) => s + m.weeks, 0)));
  private allKeys = computed(() => this.modules().flatMap(m => this.keysOf(m)));
  protected totalAll = computed(() => this.allKeys().length);
  protected doneAll = computed(() => this.progress.countDone(this.allKeys()));
  private keysOf(m: AiModule) { return [...m.lessons.map(l => keys.aiLesson(l.id)), keys.aiProject(m.id)]; }
  done(m: AiModule) { return this.progress.countDone(this.keysOf(m)); }
}
