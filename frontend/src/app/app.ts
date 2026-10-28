import { Component, computed, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { GOOGLE_CLIENT_ID } from './core/api.config';
import { HabitService } from './core/habit.service';
import { ProgressService } from './core/progress.service';

interface NavItem { path: string; label: string; icon: string; exact?: boolean; }

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="topbar">
      <button class="icon-btn menu" (click)="menuOpen.set(!menuOpen())" aria-label="Menu">☰</button>
      <a routerLink="/" class="brand">Switch<span>Prep</span></a>
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
      <button class="icon-btn" (click)="progress.toggleTheme()" [attr.aria-label]="'Toggle theme'">
        {{ progress.theme() === 'dark' ? '☀' : '☾' }}
      </button>
    </header>
    <div class="layout">
      <nav class="sidebar" [class.open]="menuOpen()">
        @for (item of nav; track item.path) {
          <a [routerLink]="item.path" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: !!item.exact }">
            <span class="nav-icon">{{ item.icon }}</span>{{ item.label }}
          </a>
        }
        <div class="sidebar-foot muted small">
          Day {{ progress.currentDay() }} of your journey
        </div>
      </nav>
      @if (menuOpen()) { <div class="scrim" (click)="menuOpen.set(false)"></div> }
      <main class="content">
        @if (progress.syncError(); as err) {
          <div class="banner warn">{{ err }} <button class="link" (click)="progress.syncError.set(null)">Dismiss</button></div>
        }
        <router-outlet />
      </main>
    </div>
  `,
})
export class App {
  protected progress = inject(ProgressService);
  protected habits = inject(HabitService);
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
}
