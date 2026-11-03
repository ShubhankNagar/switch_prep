import { Component, computed, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { GOOGLE_CLIENT_ID } from './core/api.config';
import { ContentService } from './core/content.service';
import { SearchDialog, SearchService } from './shared/search';
import { HabitService } from './core/habit.service';
import { ProgressService } from './core/progress.service';
import { isDue } from './core/review';
import { Icon } from './shared/icon';

interface NavItem { path: string; label: string; icon: string; tone: string; exact?: boolean; }
interface NavGroup { label: string; items: NavItem[]; }

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, SearchDialog, Icon],
  host: { '(document:keydown.escape)': 'menuOpen.set(false)' },
  template: `
    <a class="skip-link" href="#main" (click)="skipToMain($event)">Skip to content</a>
    <header class="topbar">
      <button class="icon-btn menu" (click)="menuOpen.set(!menuOpen())" aria-label="Menu" aria-controls="sidebar"
              [attr.aria-expanded]="menuOpen()"><app-icon name="menu" /></button>
      <a routerLink="/" class="brand"><span class="brand-mark"><app-icon name="check" /></span>SwitchPrep</a>
      <button class="search-btn" (click)="search.open.set(true)" aria-label="Search (press /)">
        <app-icon name="search" /><span class="hide-sm">Search</span><kbd class="hide-sm">/</kbd>
      </button>
      <span class="spacer"></span>
      @if (habits.timerRunning()) {
        <a routerLink="/habits" class="timer-pill" title="Focus timer running"><app-icon name="timer" />{{ timerClock() }}</a>
      }
      @if (progress.user() && progress.connection() === 'connecting') {
        <a routerLink="/account" class="sync-pill"
           title="Your changes are saved in this browser and will be sent when the sync server answers">
          {{ progress.waking() ? 'Waking sync server' : 'Connecting' }}</a>
      }
      <a [routerLink]="journey().link" class="journey-chip" [title]="journey().title">
        {{ journey().label }}<span class="of">{{ journey().of }}</span></a>
      <a routerLink="/habits" class="streak hide-sm"
         [title]="'Routine streak: ' + habits.streak() + ' day(s). Today ' + todayPct() + '% of habits done'">
        <app-icon name="flame" />{{ habits.streak() }}d</a>
      <span class="topbar-sep"></span>
      <a routerLink="/account" class="who">
        {{ progress.user()?.displayName ?? (canSignIn() ? 'Sign in' : 'Saved in this browser') }}
      </a>
      <button class="icon-btn" (click)="progress.toggleTheme()"
              [attr.aria-label]="progress.theme() === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'">
        <app-icon [name]="progress.theme() === 'dark' ? 'sun' : 'moon'" />
      </button>
    </header>
    <div class="layout">
      <nav class="sidebar" id="sidebar" [class.open]="menuOpen()" aria-label="Sections">
        @for (g of nav; track g.label) {
          <div class="nav-group">{{ g.label }}</div>
          @for (item of g.items; track item.path) {
            <a [routerLink]="item.path" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: !!item.exact }"
               [attr.data-tone]="item.tone">
              <span class="nav-icon"><app-icon [name]="item.icon" /></span>{{ item.label }}
              @if (item.path === '/revision' && dueCount()) {
                <span class="nav-count" title="Due for review">{{ dueCount() }}</span>
              }
            </a>
          }
        }
      </nav>
      @if (menuOpen()) { <div class="scrim" (click)="menuOpen.set(false)"></div> }
      <main class="content" id="main" tabindex="-1" [attr.data-tone]="section()?.item?.tone ?? 'today'">
        @if (section(); as sec) {
          @if (sec.item.path !== '/' && sec.index) {
            <a class="page-crumb" [routerLink]="sec.item.path">
              <span class="tile sm"><app-icon [name]="sec.item.icon" /></span>
              <span class="group">{{ sec.group }}</span><span class="group">/</span>{{ sec.item.label }}</a>
          }
        }
        @if (content.failed()) {
          <div class="banner warn" role="alert">Some study material could not be loaded. Check your connection.
            <button class="link" (click)="reload()">Retry</button></div>
        }
        @if (progress.syncError(); as err) {
          <div class="banner warn">{{ err }} <button class="link" (click)="progress.syncError.set(null)">Dismiss</button></div>
        }
        <router-outlet />
      </main>
    </div>
    <app-search />
  `,
})
export class App {
  protected progress = inject(ProgressService);
  protected habits = inject(HabitService);
  protected content = inject(ContentService);
  protected search = inject(SearchService);
  protected menuOpen = signal(false);
  protected canSignIn = computed(() => !!GOOGLE_CLIENT_ID || this.progress.backendAvailable());
  protected todayPct = computed(() => Math.round(this.habits.today().score * 100));
  protected timerClock = computed(() => {
    const r = this.habits.timerRemaining();
    return `${Math.floor(r / 60)}:${String(r % 60).padStart(2, '0')}`;
  });
  /** Grouped by what the learner is doing: today's work, studying, practising under interview conditions, reviewing. */
  protected nav: NavGroup[] = [
    { label: 'Today', items: [
      { path: '/', label: 'Dashboard', icon: 'dashboard', tone: 'today', exact: true },
      { path: '/plan', label: '60-day plan', icon: 'calendar', tone: 'plan' },
      { path: '/habits', label: 'Daily routine', icon: 'routine', tone: 'today' },
      { path: '/focus', label: 'High-yield focus', icon: 'target', tone: 'today' },
    ] },
    { label: 'Learn', items: [
      { path: '/dsa', label: 'DSA', icon: 'code', tone: 'dsa' },
      { path: '/system-design', label: 'System design', icon: 'network', tone: 'sd' },
      { path: '/core', label: 'Core subjects', icon: 'book', tone: 'core' },
      { path: '/ai', label: 'AI engineer course', icon: 'cpu', tone: 'ai' },
    ] },
    { label: 'Practice', items: [
      { path: '/traps', label: 'Common traps', icon: 'alert', tone: 'traps' },
      { path: '/mock', label: 'Mock interview', icon: 'mic', tone: 'mock' },
      { path: '/rounds', label: 'Interview rounds', icon: 'compass', tone: 'rounds' },
      { path: '/final-round', label: 'Final round', icon: 'flag', tone: 'final' },
    ] },
    { label: 'Review', items: [
      { path: '/revision', label: 'Revision list', icon: 'star', tone: 'review' },
      { path: '/guide', label: 'Job switch guide', icon: 'briefcase', tone: 'neutral' },
      { path: '/account', label: 'Account and data', icon: 'user', tone: 'neutral' },
    ] },
  ];
  protected dueCount = computed(() => {
    const now = Date.now();
    return Object.values(this.progress.items()).filter(i => i.revise && isDue(i.updatedAt, now)).length;
  });
  /** The journey position, shown in the top bar on every page. */
  protected journey = computed(() => {
    const d = this.progress.currentDay();
    if (d <= 60) return { label: `Day ${d}`, of: ' / 60', link: `/plan/${d}`, title: `Study plan, day ${d} of 60` };
    if (d <= 74) return { label: `Final ${d - 60}`, of: ' / 14', link: `/final-round/${d - 60}`, title: `Final round, day ${d - 60} of 14` };
    return { label: 'Done', of: '', link: '/revision', title: 'Plan and final round complete' };
  });

  private url = signal('/');
  /** The nav entry that owns the current page, by its first path segment; it sets the page's colour. */
  protected section = computed(() => {
    const first = '/' + (this.url().split(/[?#]/)[0].split('/')[1] ?? '');
    for (const g of this.nav) {
      const item = g.items.find(i => i.path === first);
      // the crumb shows on a section's own page; deeper pages have their own back link
      if (item) return { group: g.label, item, index: this.url().split(/[?#]/)[0].split('/').filter(Boolean).length <= 1 };
    }
    return undefined;
  });

  constructor() {
    const router = inject(Router);
    router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe(() => {
      this.menuOpen.set(false);
      this.url.set(router.url);
    });
  }

  /** Hash routing owns "#", so the skip link moves focus itself instead of following its href. */
  skipToMain(e: Event) {
    e.preventDefault();
    document.getElementById('main')?.focus();
  }

  reload() {
    location.reload();
  }
}
