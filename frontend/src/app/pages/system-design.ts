import { Component, computed, inject, resource, signal } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { ProgressService } from '../core/progress.service';
import { DoneToggle, ProgressBar, ReviseToggle } from '../shared/ui';

@Component({
  selector: 'app-system-design',
  imports: [RouterLink, NgTemplateOutlet, ProgressBar, DoneToggle, ReviseToggle],
  template: `
    <h1>System design</h1>
    <p class="muted">SDE-2 interviews at product companies usually have one HLD round (design a system end to end) and
      often a LLD / machine-coding round (design classes and write working code in 60-90 min). Read the concepts in order,
      then practise the case studies out loud with a timer: 5 min requirements, 5 min estimates, 10 min API + data model,
      15 min high-level design, 10 min deep dives.</p>
    <div class="tabs">
      @for (g of groups(); track g.id) {
        <button [class.active]="tab() === g.id" (click)="tab.set(g.id)">
          {{ g.name }} <span class="muted small">{{ doneIn(g.topics) }}/{{ g.topics.length }}</span>
        </button>
      }
    </div>
    @if (current(); as g) {
      <app-progress-bar [done]="doneIn(g.topics)" [total]="g.topics.length" />
      <div class="topic-list">
        @for (t of coreOf(g.topics); track t.id) {
          <ng-container *ngTemplateOutlet="topicCard; context: { $implicit: t, g: g }" />
        }
      </div>
      @if (optionalOf(g.topics); as rest) {
        @if (rest.length) {
          <details class="optional-group">
            <summary>More {{ g.name }} (optional) · {{ rest.length }}</summary>
            <div class="topic-list">
              @for (t of rest; track t.id) {
                <ng-container *ngTemplateOutlet="topicCard; context: { $implicit: t, g: g }" />
              }
            </div>
          </details>
        }
      }
    }
    <ng-template #topicCard let-t let-g="g">
      <a class="card topic" [routerLink]="['/system-design', g.id, t.id]" [class.done]="progress.isDone(key(t.id))">
        <app-done-toggle [key]="key(t.id)" section="sd" />
        <div class="grow">
          <h3>{{ t.title }}</h3>
          <p class="muted small">{{ t.summary }}</p>
        </div>
        <div class="topic-meta">
          <span class="tag" [class]="'tag lvl-' + t.level.toLowerCase()">{{ t.level }}</span>
          <span class="muted small">{{ t.minutes }} min</span>
          <app-revise-toggle [key]="key(t.id)" section="sd" />
        </div>
      </a>
    </ng-template>
  `,
})
export class SystemDesignPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private res = resource({ loader: () => this.content.systemDesign() });
  protected key = keys.sd;
  protected tab = signal<string>('concepts');
  protected groups = computed(() => this.res.value() ?? []);
  private coaching = resource({ loader: () => this.content.coreCoaching() });
  private coreSd = computed(() => new Set(this.coaching.value()?.coreSd ?? []));
  /** Core topics are the ones the plan schedules; until the list loads, everything counts as core. */
  coreOf<T extends { id: string }>(topics: T[]) {
    return this.coreSd().size ? topics.filter(t => this.coreSd().has(t.id)) : topics;
  }
  optionalOf<T extends { id: string }>(topics: T[]) {
    return this.coreSd().size ? topics.filter(t => !this.coreSd().has(t.id)) : [];
  }
  protected current = computed(() => this.groups().find(g => g.id === this.tab()));
  doneIn(topics: { id: string }[]) { return this.progress.countDone(topics.map(t => keys.sd(t.id))); }
}
