import { Component, computed, effect, inject, input, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { PlanDay } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, LinkPipe, ProgressBar } from '../shared/ui';

@Component({
  selector: 'app-plan',
  imports: [RouterLink, DoneToggle, ProgressBar, MarkdownPipe, LinkPipe],
  template: `
    <h1>60-Day Study Plan</h1>
    @if (plan(); as p) {
      <div class="md intro" [innerHTML]="p.intro | md"></div>
      <p class="muted">Time budget: {{ p.hoursPerDay }}</p>
      <app-progress-bar [done]="doneAll()" [total]="totalAll()" />

      @if (selected(); as d) {
        <section class="card day-detail" id="day">
          <div class="card-head">
            <h2>Day {{ d.day }} · {{ d.title }}</h2>
            <div class="row">
              @if (d.day > 1) { <a class="btn small" [routerLink]="['/plan', d.day - 1]">← Day {{ d.day - 1 }}</a> }
              @if (d.day < 60) { <a class="btn small" [routerLink]="['/plan', d.day + 1]">Day {{ d.day + 1 }} →</a> }
              @if (d.day === 60) { <a class="btn small primary" routerLink="/final-round">Final Round →</a> }
            </div>
          </div>
          <p class="muted">{{ d.focus }}</p>
          <ul class="tasks big">
            @for (t of d.tasks; track t.id) {
              <li [class.done]="progress.isDone(key(d.day, t.id))">
                <app-done-toggle [key]="key(d.day, t.id)" section="plan" />
                <div>
                  <span class="tag" [class]="'tag t-' + t.type">{{ t.type }}</span>
                  @if (t.link) { <a [routerLink]="t.link | link">{{ t.title }}</a> } @else { <strong>{{ t.title }}</strong> }
                  <span class="muted small"> · {{ t.minutes }} min</span>
                  @if (t.detail) { <div class="muted small md" [innerHTML]="t.detail | md"></div> }
                </div>
              </li>
            }
          </ul>
        </section>
      }

      @for (w of p.weeks; track w.week) {
        <section class="week">
          <h2>Week {{ w.week }} · {{ w.title }}</h2>
          <p class="muted">{{ w.goal }}</p>
          <div class="day-grid">
            @for (d of daysOf(p.days, w.week); track d.day) {
              <a class="day-cell card" [routerLink]="['/plan', d.day]"
                 [class.today]="d.day === progress.currentDay()" [class.active]="d.day === selected()?.day"
                 [class.complete]="dayDone(d) === required(d).length">
                <span class="day-num">Day {{ d.day }}</span>
                <span class="day-title">{{ d.title }}</span>
                <app-progress-bar [done]="dayDone(d)" [total]="required(d).length" [showLabel]="false" />
              </a>
            }
          </div>
        </section>
      }
    } @else {
      <p class="muted">Loading…</p>
    }
  `,
})
export class PlanPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  day = input<string>();

  private res = resource({ loader: () => this.content.plan() });
  protected plan = computed(() => this.res.value());
  protected key = keys.plan;

  protected selected = computed(() => {
    const p = this.plan();
    if (!p) return undefined;
    const n = this.day() ? Number(this.day()) : Math.min(this.progress.currentDay(), 60);
    return p.days.find(d => d.day === n);
  });

  private allKeys = computed(() => (this.plan()?.days ?? []).flatMap(d => d.tasks.map(t => keys.plan(d.day, t.id))));
  protected totalAll = computed(() => this.allKeys().length);
  protected doneAll = computed(() => this.progress.countDone(this.allKeys()));

  constructor() {
    effect(() => {
      if (this.day() && this.selected()) {
        setTimeout(() => document.getElementById('day')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
      }
    });
  }

  daysOf(days: PlanDay[], week: number) { return days.filter(d => d.week === week); }
  /** Tasks that count toward finishing a day (AI-course lessons are optional). */
  required(d: PlanDay) { return d.tasks.filter(t => t.type !== 'ai'); }
  dayDone(d: PlanDay) { return this.progress.countDone(this.required(d).map(t => keys.plan(d.day, t.id))); }
}
