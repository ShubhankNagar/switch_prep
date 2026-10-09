import { Component, computed, inject, resource, signal } from '@angular/core';
import { ContentService } from '../core/content.service';
import { MarkdownPipe } from '../shared/markdown.pipe';

@Component({
  selector: 'app-guide',
  imports: [MarkdownPipe],
  template: `
    <h1>💼 Job Switch Guide</h1>
    <p class="muted">Everything outside of studying: resume, where to apply, referrals, interview process by company,
      and how to negotiate to 15 LPA+.</p>
    <div class="notes-layout">
      <nav class="toc card">
        @for (s of sections(); track s.id; let i = $index) {
          <button [class.active]="idx() === i" (click)="idx.set(i)">{{ s.icon }} {{ s.title }}</button>
        }
      </nav>
      @if (sections()[idx()]; as s) {
        <article class="card md article">
          <h2>{{ s.icon }} {{ s.title }}</h2>
          <div [innerHTML]="s.content | md"></div>
        </article>
      }
    </div>
  `,
})
export class GuidePage {
  private content = inject(ContentService);
  private res = resource({ loader: () => this.content.guide() });
  protected sections = computed(() => this.res.value()?.sections ?? []);
  protected idx = signal(0);
}
