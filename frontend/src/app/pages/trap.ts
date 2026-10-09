import { Component, computed, inject, input, resource } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ContentService } from '../core/content.service';
import { TrapCard } from '../shared/trap-card';

@Component({
  selector: 'app-trap',
  imports: [RouterLink, TrapCard],
  template: `
    <a routerLink="/traps" class="back">← All traps</a>
    @if (data(); as d) {
      <app-trap-card [trap]="d.t" />
      <div class="row">
        @if (d.prev; as prev) { <a class="btn" [routerLink]="['/traps', prev.id]">← {{ prev.title }}</a> }
        @if (d.next; as next) { <a class="btn primary" [routerLink]="['/traps', next.id]">{{ next.title }} →</a> }
      </div>
    }
  `,
})
export class TrapPage {
  private content = inject(ContentService);
  id = input.required<string>();
  private res = resource({ loader: () => this.content.traps() });
  protected data = computed(() => {
    const all = this.res.value() ?? [];
    const i = all.findIndex(t => t.id === this.id());
    if (i < 0) return undefined;
    // prev/next within the same area keeps practice focused
    const same = all.filter(t => t.area === all[i].area);
    const j = same.findIndex(t => t.id === this.id());
    return { t: all[i], prev: same[j - 1], next: same[j + 1] };
  });
}
