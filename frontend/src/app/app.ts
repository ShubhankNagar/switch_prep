import { Component, computed, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { GOOGLE_CLIENT_ID } from './core/api.config';
import { ContentService } from './core/content.service';
import { SearchDialog, SearchService } from './shared/search';
import { HabitService } from './core/habit.service';
import { ProgressService } from './core/progress.service';

interface NavItem { path: string; label: string; icon: string; exact?: boolean; }

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, SearchDialog],
  host: { '(document:keydown.escape)': 'menuOpen.set(false)' },
  template: `
    <a class="skip-link" href="#main" (click)="skipToMain($event)">Skip to content</a>
    <header class="topbar">
      <button class="icon-btn menu" (click)="menuOpen.set(!menuOpen())" aria-label="Menu" aria-controls="sidebar"
              [attr.aria-expanded]="menuOpen()">☰</button>
      <a routerLink="/" class="brand">Switch<span>Prep</span></a>
      <button class="search-btn" (click)="search.open.set(true)" aria-label="Search (press /)">
        <span aria-hidden="true">🔍</span><span class="hide-sm"> Search</span><kbd class="hide-sm">/</kbd>
      </button>
      <span class="spacer"></span>
      @if (habits.timerRunning()) {
        <a routerLink="/habits" class="timer-pill" title="Focus timer running">⏱️ {{ timerClock() }}</a>
      }
      <a routerLink="/habits" class="streak" title="Routine streak: days you hit your daily habits">
        🔥 {{ habits.streak() }} · {{ todayPct() }}%</a>
      @if (progress.user() && progress.connection() === 'connecting') {
        <a routerLink="/account" class="sync-pill"
           title="Your changes are saved in this browser and will be sent when the sync server answers">
          {{ progress.waking() ? 'Waking sync server…' : 'Connecting…' }}</a>
      }
      <a routerLink="/account" class="who">
        {{ progress.user()?.displayName ?? (canSignIn() ? 'Sign in to sync' : 'Browser mode') }}
      </a>
      <button class="icon-btn" (click)="progress.toggleTheme()"
              [attr.aria-label]="progress.theme() === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'">
        {{ progress.theme() === 'dark' ? '☀' : '☾' }}
      </button>
    </header>
    <div class="layout">
      <nav class="sidebar" id="sidebar" [class.open]="menuOpen()" aria-label="Sections">
        @for (item of nav; track item.path) {
          <a [routerLink]="item.path" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: !!item.exact }">
            <span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>{{ item.label }}
          </a>
        }
        <div class="sidebar-foot muted small">
          Day {{ progress.currentDay() }} of your journey
        </div>
      </nav>
      @if (menuOpen()) { <div class="scrim" (click)="menuOpen.set(false)"></div> }
      <main class="content" id="main" tabindex="-1">
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
  protected nav: NavItem[] = [
    { path: '/', label: 'Dashboard', icon: '🏠', exact: true },
    { path: '/habits', label: 'Daily Routine', icon: '🔥' },
    { path: '/focus', label: 'High-Yield Focus', icon: '🎯' },
    { path: '/plan', label: '60-Day Plan', icon: '🗓️' },
    { path: '/traps', label: 'Common Traps', icon: '🪤' },
    { path: '/rounds', label: 'Interview Rounds', icon: '🧭' },
    { path: '/mock', label: 'Mock Interview', icon: '🎤' },
    { path: '/dsa', label: 'DSA', icon: '🧩' },
    { path: '/system-design', label: 'System Design', icon: '🏗️' },
    { path: '/core', label: 'Core Subjects', icon: '📚' },
    { path: '/final-round', label: 'Final Round (14 days)', icon: '🏁' },
    { path: '/ai', label: 'AI Engineer Course', icon: '🤖' },
    { path: '/revision', label: 'Revision List', icon: '★' },
    { path: '/guide', label: 'Job Switch Guide', icon: '💼' },
    { path: '/account', label: 'Account & Data', icon: '⚙️' },
  ];

  constructor() {
    inject(Router).events.pipe(filter(e => e instanceof NavigationEnd)).subscribe(() => this.menuOpen.set(false));
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
