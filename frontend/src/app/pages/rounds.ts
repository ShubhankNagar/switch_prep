import { Component, computed, inject, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, ProgressBar } from '../shared/ui';

@Component({
  selector: 'app-rounds',
  imports: [RouterLink, MarkdownPipe, DoneToggle, ProgressBar],
  template: `
    <h1>🧭 Interview Rounds 2027</h1>
    <p class="muted">Every round you're likely to face, how it's scored, how strong candidates handle it, and where
      most people fail. Mark a round "ready" once you can do its walkthrough without notes.</p>
    <app-progress-bar [done]="readyCount()" [total]="rounds().length" />
    @if (file()?.trends; as trends) {
      <details class="card trends">
        <summary><b>What changed in 2025-2027 and what it means for you</b></summary>
        <div class="md" [innerHTML]="trends | md"></div>
      </details>
    }
    <div class="topic-list">
      @for (r of rounds(); track r.id) {
        <a class="card topic" [routerLink]="['/rounds', r.id]" [class.done]="progress.isDone(key(r.id))">
          <app-done-toggle [key]="key(r.id)" section="rounds" />
          <span class="big-icon">{{ r.icon }}</span>
          <div class="grow">
            <h3>{{ r.title }}</h3>
            <p class="muted small">{{ r.summary }}</p>
          </div>
          <div class="topic-meta">
            <span class="tag must">{{ r.frequency }}</span>
            <span class="muted small">{{ r.weight }}</span>
          </div>
        </a>
      } @empty { <p class="muted">Loading…</p> }
    </div>
  `,
})
export class RoundsPage {
  protected progress = inject(ProgressService);
  private content = inject(ContentService);
  private res = resource({ loader: () => this.content.rounds() });
  protected file = computed(() => this.res.value());
  protected rounds = computed(() => this.res.value()?.rounds ?? []);
  protected key = keys.round;
  protected readyCount = computed(() => this.progress.countDone(this.rounds().map(r => keys.round(r.id))));
}
