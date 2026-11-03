import { Injectable, effect, inject, signal, untracked } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';

const RECENT_KEY = 'switchprep.recent';
const MAX = 5;

export interface RecentPage { url: string; title: string; at: string; }

/**
 * Remembers the study pages opened last on this device, so the dashboard can offer "continue where you left off".
 * Device-local on purpose: it is a convenience, not progress.
 */
@Injectable({ providedIn: 'root' })
export class RecentService {
  private router = inject(Router);
  private title = inject(Title);
  readonly pages = signal<RecentPage[]>(this.read());

  /**
   * Call from a detail page's constructor. Whenever `label` returns a name, it becomes the browser tab title
   * and the page is remembered as recently studied.
   */
  track(label: () => string | undefined): void {
    effect(() => {
      const name = label();
      if (!name) return;
      // untracked: remember() reads and writes `pages`, which must not re-run this effect
      untracked(() => {
        this.title.setTitle(`${name} · SwitchPrep`);
        this.remember(this.router.url, name);
      });
    });
  }

  private remember(url: string, title: string): void {
    const entry: RecentPage = { url, title, at: new Date().toISOString() };
    const list = [entry, ...this.pages().filter(p => p.url !== url)].slice(0, MAX);
    this.pages.set(list);
    try {
      localStorage.setItem(RECENT_KEY, JSON.stringify(list));
    } catch {
      /* storage blocked: the list still works for this visit */
    }
  }

  private read(): RecentPage[] {
    try {
      const list = JSON.parse(localStorage.getItem(RECENT_KEY) ?? '[]');
      return Array.isArray(list) ? list.filter(p => typeof p?.url === 'string' && typeof p?.title === 'string') : [];
    } catch {
      return [];
    }
  }
}
