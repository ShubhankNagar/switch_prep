import { Component, ElementRef, Injectable, computed, effect, inject, resource, signal, viewChild } from '@angular/core';
import { Router } from '@angular/router';
import { CatalogService } from '../core/catalog.service';
import { CatalogEntry } from '../core/models';
import { ProgressService } from '../core/progress.service';

@Injectable({ providedIn: 'root' })
export class SearchService {
  readonly open = signal(false);
}

interface Hit { title: string; link: string; group: string; label: string; key?: string; }

const SECTION_LABEL: Record<string, string> = {
  dsa: 'DSA', sd: 'System design', core: 'Core', final: 'Final round', ai: 'AI course', traps: 'Trap', rounds: 'Round',
};
/** Pages that are not items but people look for by name. */
const PAGES: Hit[] = [
  ['Dashboard', '/'], ['Daily Routine', '/habits'], ['High-Yield Focus', '/focus'], ['60-Day Plan', '/plan'],
  ['Common Traps', '/traps'], ['Interview Rounds', '/rounds'], ['Mock Interview', '/mock'], ['DSA Problems', '/dsa'], ['System Design', '/system-design'],
  ['Core Subjects', '/core'], ['Final Round', '/final-round'], ['AI Engineer Course', '/ai'], ['Revision List', '/revision'],
  ['Job Switch Guide', '/guide'], ['Account & Data', '/account'],
].map(([title, link]) => ({ title, link, group: 'Go to page', label: 'Page' }));
const MAX_HITS = 30;

/** Ranks how well an entry matches: every word must appear; earlier and word-start matches rank higher. */
export function score(title: string, group: string, words: string[]): number {
  const t = title.toLowerCase();
  const g = group.toLowerCase();
  let total = 0;
  for (const w of words) {
    const i = t.indexOf(w);
    if (i < 0) {
      if (!g.includes(w)) return -1;
      total += 1;
    } else {
      total += i === 0 ? 10 : /\W/.test(t[i - 1]) ? 6 : 3;
    }
  }
  return total - t.length / 200; // shorter titles first on ties
}

/** Site-wide search over every topic, problem and question. Opens with "/" or Ctrl/Cmd+K. */
@Component({
  selector: 'app-search',
  host: { '(document:keydown)': 'onGlobalKey($event)' },
  template: `
    @if (search.open()) {
      <div class="search-scrim" (click)="close()"></div>
      <div class="search-dialog" role="dialog" aria-modal="true" aria-label="Search SwitchPrep">
        <input #box type="search" class="search-input" placeholder="Search problems, topics, questions, traps…"
               role="combobox" aria-expanded="true" aria-controls="search-results" aria-autocomplete="list"
               [attr.aria-activedescendant]="hits().length ? 'hit-' + active() : null"
               [value]="query()" (input)="setQuery($any($event.target).value)" (keydown)="onKey($event)" />
        <ul class="search-results" id="search-results" role="listbox">
          @for (h of hits(); track h.link + h.title; let i = $index) {
            <li [id]="'hit-' + i" role="option" [attr.aria-selected]="i === active()" [class.active]="i === active()"
                (mousemove)="active.set(i)" (click)="go(h)">
              <span class="tag">{{ h.label }}</span>
              <span class="grow">
                <span class="hit-title">{{ h.title }}</span>
                <span class="muted small hit-group">{{ h.group }}</span>
              </span>
              @if (h.key && progress.isDone(h.key)) { <span class="hit-done" title="Done">✓</span> }
            </li>
          } @empty {
            <li class="muted search-empty">
              @if (catalog.isLoading()) { Loading the index… }
              @else if (query().trim()) { Nothing matches "{{ query() }}". Try fewer or shorter words. }
              @else { Type to search {{ count() }} problems, topics and interview questions. }
            </li>
          }
        </ul>
        <p class="search-foot muted small"><kbd>↑</kbd><kbd>↓</kbd> move · <kbd>Enter</kbd> open · <kbd>Esc</kbd> close</p>
      </div>
    }
  `,
})
export class SearchDialog {
  protected search = inject(SearchService);
  protected progress = inject(ProgressService);
  private router = inject(Router);
  private catalogService = inject(CatalogService);
  private box = viewChild<ElementRef<HTMLInputElement>>('box');
  private returnFocus: HTMLElement | null = null;

  /** Loaded the first time search opens, not on every page view. */
  protected catalog = resource({
    params: () => (this.search.open() ? true : undefined),
    loader: () => this.catalogService.all(),
  });
  private entries = signal<CatalogEntry[]>([]);
  protected query = signal('');
  protected active = signal(0);
  protected count = computed(() => this.entries().length);

  protected hits = computed<Hit[]>(() => {
    const words = this.query().toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) return [];
    const items: Hit[] = this.entries()
      .filter(e => e.section !== 'plan') // plan tasks repeat the titles of the items they point at
      .map(e => ({ title: e.title, link: e.link, group: e.group, label: SECTION_LABEL[e.section] ?? e.section, key: e.key }));
    return [...PAGES, ...items]
      .map(h => ({ h, s: score(h.title, h.group, words) }))
      .filter(x => x.s >= 0)
      .sort((a, b) => b.s - a.s)
      .slice(0, MAX_HITS)
      .map(x => x.h);
  });

  constructor() {
    effect(() => {
      const v = this.catalog.value();
      if (v) this.entries.set(v);
    });
    effect(() => {
      if (this.search.open()) {
        this.returnFocus = document.activeElement as HTMLElement | null;
        document.body.classList.add('no-scroll');
        setTimeout(() => this.box()?.nativeElement.focus());
      } else {
        document.body.classList.remove('no-scroll');
      }
    });
  }

  setQuery(q: string) {
    this.query.set(q);
    this.active.set(0);
  }

  close() {
    this.search.open.set(false);
    this.returnFocus?.focus?.();
  }

  go(h: Hit) {
    this.search.open.set(false);
    this.query.set('');
    void this.router.navigateByUrl(h.link);
  }

  onKey(e: KeyboardEvent) {
    const n = this.hits().length;
    if (e.key === 'ArrowDown' && n) {
      e.preventDefault();
      this.active.update(i => (i + 1) % n);
      this.scrollActive();
    } else if (e.key === 'ArrowUp' && n) {
      e.preventDefault();
      this.active.update(i => (i - 1 + n) % n);
      this.scrollActive();
    } else if (e.key === 'Enter' && n) {
      e.preventDefault();
      this.go(this.hits()[this.active()]);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      this.close();
    }
  }

  onGlobalKey(e: KeyboardEvent) {
    const typing = (e.target as HTMLElement | null)?.closest?.('input, textarea, select, [contenteditable="true"]');
    if ((e.key === 'k' || e.key === 'K') && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      this.search.open.update(o => !o);
    } else if (e.key === '/' && !typing && !this.search.open()) {
      e.preventDefault();
      this.search.open.set(true);
    }
  }

  private scrollActive() {
    setTimeout(() => document.getElementById('hit-' + this.active())?.scrollIntoView({ block: 'nearest' }));
  }
}
