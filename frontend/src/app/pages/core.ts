import { Component, computed, inject, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { Subject } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { ProgressBar } from '../shared/ui';

const SENIOR_FROM = 12;

@Component({
  selector: 'app-core',
  imports: [RouterLink, ProgressBar],
  template: `
    <h1>Core Subjects</h1>
    <p class="muted">Study notes + the interview questions actually asked for each subject. Product companies grill
      2-YOE backend candidates hardest on Core Java, Spring Boot, SQL and your project; CS fundamentals (OS, CN, DBMS)
      show up in OAs and the first technical round.</p>
    @for (g of groups(); track g.title) {
      @if (g.items.length) {
        <h2 class="section-title">{{ g.title }}</h2>
        <p class="muted small">{{ g.note }}</p>
        <div class="grid three">
          @for (s of g.items; track s.id) {
            <a class="card stat-card" [routerLink]="['/core', s.id]">
              <div class="stat-top"><span class="big-icon">{{ s.icon }}</span><h3>{{ s.name }}</h3></div>
              <p class="muted small">{{ s.description }}</p>
              <app-progress-bar [done]="done(s)" [total]="s.notes.length + s.qa.length" />
              <p class="muted small">{{ s.notes.length }} chapters · {{ s.qa.length }} questions</p>
            </a>
          }
        </div>
      }
    }
  `,
})
export class CorePage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private res = resource({ loader: () => this.content.subjects() });
  protected subjects = computed(() => this.res.value() ?? []);
  /** Subjects 12+ are the senior 2027 additions (production debugging, performance, ...). */
  protected groups = computed(() => [
    { title: 'Your stack and fundamentals', note: 'The resume deep-dive round probes these for 45-60 minutes.',
      items: this.subjects().filter(s => s.order < SENIOR_FROM) },
    { title: 'Senior signals (2027)', note: 'What separates a senior answer: debugging live systems, performance, '
      + 'concurrency, testing and review, cloud, security, working with AI tools, and leading without authority.',
      items: this.subjects().filter(s => s.order >= SENIOR_FROM) },
  ]);
  done(s: Subject) {
    return this.progress.countDone([...s.notes.map(n => keys.note(s.id, n.id)), ...s.qa.map(q => keys.qa(q.id ?? q.q))]);
  }
}
