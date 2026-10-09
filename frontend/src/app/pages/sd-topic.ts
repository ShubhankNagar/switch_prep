import { Component, computed, inject, input, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, NoteBox, ReviseToggle } from '../shared/ui';
import { QaList } from '../shared/qa-list';

@Component({
  selector: 'app-sd-topic',
  imports: [RouterLink, MarkdownPipe, DoneToggle, ReviseToggle, NoteBox, QaList],
  template: `
    <a routerLink="/system-design" class="back">← System Design</a>
    @if (data(); as d) {
      <p class="eyebrow">{{ d.group.name }} · {{ d.t.level }} · {{ d.t.minutes }} min read</p>
      <h1>{{ d.t.title }}</h1>
      <div class="row wrap actions">
        <app-done-toggle [key]="key()" section="sd" label="Mark as learned" doneLabel="Learned" />
        <app-revise-toggle [key]="key()" section="sd" [label]="true" />
      </div>
      <article class="card md article" [innerHTML]="d.t.content | md"></article>

      <section class="card keypoints">
        <h2>Key points to revise</h2>
        <ul>@for (k of d.t.keyPoints; track $index) { <li>{{ k }}</li> }</ul>
      </section>

      @if (d.t.interviewQuestions.length) {
        <h2 class="section-title">Interview questions</h2>
        <app-qa-list [items]="d.t.interviewQuestions" [trackKeys]="false" />
      }

      <section class="card"><app-note-box [key]="key()" section="sd" /></section>

      @if (d.t.sources.length) {
        <section class="sources muted small">
          <b>Sources & further reading:</b>
          @for (s of d.t.sources; track s.url) { <a [href]="s.url" target="_blank" rel="noopener">{{ s.title }}</a> }
        </section>
      }
      <div class="row">
        @if (d.prev; as prev) { <a class="btn" [routerLink]="['/system-design', d.group.id, prev.id]">← {{ prev.title }}</a> }
        @if (d.next; as next) { <a class="btn primary" [routerLink]="['/system-design', d.group.id, next.id]">{{ next.title }} →</a> }
      </div>
    }
  `,
})
export class SdTopicPage {
  private content = inject(ContentService);
  group = input.required<string>();
  topic = input.required<string>();
  private res = resource({ loader: () => this.content.systemDesign() });
  protected key = computed(() => keys.sd(this.topic()));
  protected data = computed(() => {
    const group = (this.res.value() ?? []).find(g => g.id === this.group());
    if (!group) return undefined;
    const i = group.topics.findIndex(t => t.id === this.topic());
    return i < 0 ? undefined : { group, t: group.topics[i], prev: group.topics[i - 1], next: group.topics[i + 1] };
  });
}
