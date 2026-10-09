import { Component, computed, inject, input, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { keys } from '../core/catalog.service';
import { ContentService } from '../core/content.service';
import { MarkdownPipe } from '../shared/markdown.pipe';
import { DoneToggle, LinkPipe, NoteBox } from '../shared/ui';

@Component({
  selector: 'app-round',
  imports: [RouterLink, MarkdownPipe, DoneToggle, NoteBox, LinkPipe],
  template: `
    <a routerLink="/rounds" class="back">← Interview rounds</a>
    @if (data(); as d) {
      <p class="eyebrow">{{ d.r.frequency }} · {{ d.r.weight }}</p>
      <h1>{{ d.r.icon }} {{ d.r.title }}</h1>
      <p>{{ d.r.summary }}</p>
      <div class="row wrap">
        @for (c of d.r.whoRunsIt; track c) { <span class="tag company">{{ c }}</span> }
      </div>
      <div class="row wrap actions">
        <app-done-toggle [key]="key()" section="rounds" label="I'm ready for this round" doneLabel="Ready" />
      </div>

      <div class="grid two">
        <section class="card"><h2>Format</h2><div class="md" [innerHTML]="d.r.format | md"></div></section>
        <section class="card"><h2>What they test</h2>
          <ul>@for (w of d.r.whatTheyTest; track $index) { <li>{{ w }}</li> }</ul></section>
      </div>
      <section class="card"><h2>How it's scored</h2><div class="md" [innerHTML]="d.r.rubric | md"></div></section>
      <section class="card"><h2>How to ace it</h2><div class="md article" [innerHTML]="d.r.howToAce | md"></div></section>
      <section class="card"><h2>Walkthrough: a strong candidate in action</h2>
        <div class="md article" [innerHTML]="d.r.walkthrough | md"></div></section>
      <section class="card fail-list"><h2>⚠️ Where most candidates fail</h2>
        <ul>@for (f of d.r.commonFailures; track $index) { <li>{{ f }}</li> }</ul></section>
      @if (d.r.practice.length) {
        <section class="card"><h2>Practise on SwitchPrep</h2>
          <ul class="resources">
            @for (p of d.r.practice; track p.link) { <li><a [routerLink]="p.link | link">{{ p.title }}</a></li> }
          </ul>
        </section>
      }
      <section class="card"><app-note-box [key]="key()" section="rounds" /></section>
      @if (d.r.sources.length) {
        <section class="sources muted small"><b>Sources:</b>
          @for (s of d.r.sources; track s.url) { <a [href]="s.url" target="_blank" rel="noopener">{{ s.title }}</a> }
        </section>
      }
      <div class="row">
        @if (d.prev; as prev) { <a class="btn" [routerLink]="['/rounds', prev.id]">← {{ prev.title }}</a> }
        @if (d.next; as next) { <a class="btn primary" [routerLink]="['/rounds', next.id]">{{ next.title }} →</a> }
      </div>
    }
  `,
})
export class RoundPage {
  private content = inject(ContentService);
  id = input.required<string>();
  private res = resource({ loader: () => this.content.rounds() });
  protected key = computed(() => keys.round(this.id()));
  protected data = computed(() => {
    const all = this.res.value()?.rounds ?? [];
    const i = all.findIndex(r => r.id === this.id());
    return i < 0 ? undefined : { r: all[i], prev: all[i - 1], next: all[i + 1] };
  });
}
