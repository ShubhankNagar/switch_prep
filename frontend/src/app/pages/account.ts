import { Component, ElementRef, NgZone, effect, inject, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { GOOGLE_CLIENT_ID } from '../core/api.config';
import { renderGoogleButton } from '../core/google-identity';
import { HabitService } from '../core/habit.service';
import { ExportFile, ProgressService } from '../core/progress.service';

@Component({
  selector: 'app-account',
  imports: [FormsModule],
  template: `
    <h1>Account & Data</h1>

    <section class="card">
      <h2>Journey start date</h2>
      <p class="muted">Day 1 of the 60-day plan. The dashboard uses this to show today's tasks.</p>
      <div class="row">
        <input type="date" [ngModel]="progress.startDate()" (ngModelChange)="progress.setStartDate($event)" />
        <span class="muted">Today is day {{ progress.currentDay() }}.</span>
      </div>
    </section>

    <section class="card">
      <h2>Sync across devices</h2>
      @if (progress.user(); as u) {
        <p>Signed in as <b>{{ u.displayName }}</b> ({{ u.email ?? u.username }}).
          @if (progress.online()) { Progress is saved to the server. }</p>
        @if (!progress.online()) {
          <p class="banner warn">
            {{ progress.waking()
              ? 'The sync server is waking up. This can take a few minutes after it has been idle.'
              : 'Connecting to the sync server…' }}
            You can keep studying: your changes are saved in this browser and sent when it answers.
            @if (progress.pendingCount(); as n) { <b>{{ n }} change(s) waiting.</b> }
          </p>
        }
        @if (offlineItems() > 0) {
          <p class="muted">This browser also holds {{ offlineItems() }} item(s) tracked before you signed in.</p>
        }
        <div class="row wrap">
          <button class="btn" (click)="upload()" [disabled]="!progress.online()">Upload this browser's offline progress to my account</button>
          <button class="btn" (click)="progress.logout()">Sign out</button>
        </div>
      } @else if (googleSignIn) {
        <p class="muted">Sign in with your Google account to save progress on the server and use it on any device.
          Without signing in, everything still works and stays in this browser.</p>
        @if (busy()) {
          <p class="banner">
            {{ progress.waking()
              ? 'Signing in. The sync server is waking up, which can take a few minutes after it has been idle. Keep this tab open.'
              : 'Signing in…' }}
          </p>
        } @else {
          <div #googleButton class="google-button"></div>
        }
        <p class="muted small">Signing in stores your name, your email address and your progress, notes, quiz scores and
          routine on the sync server. Nothing else is collected, and you can delete your account and all of it below at any time.
          <a href="privacy.html" target="_blank" rel="noopener">Privacy details</a></p>
      } @else if (progress.backendAvailable()) {
        <p class="muted">The SwitchPrep API is running. Log in to save progress in the database (MySQL/H2) instead of only this browser.</p>
        <div class="tabs">
          <button [class.active]="authTab() === 'login'" (click)="authTab.set('login')">Log in</button>
          <button [class.active]="authTab() === 'register'" (click)="authTab.set('register')">Create account</button>
        </div>
        <form class="auth-form" (ngSubmit)="submit()">
          <input name="username" placeholder="Username" [(ngModel)]="username" required autocomplete="username" />
          @if (authTab() === 'register') {
            <input name="displayName" placeholder="Display name" [(ngModel)]="displayName" />
          }
          <input name="password" type="password" placeholder="Password (min 6 chars)" [(ngModel)]="password" required
                 [attr.autocomplete]="authTab() === 'login' ? 'current-password' : 'new-password'" />
          <button class="btn primary" type="submit" [disabled]="busy()">{{ authTab() === 'login' ? 'Log in' : 'Create account' }}</button>
        </form>
      } @else {
        <p class="muted">Browser-only mode: no backend is reachable, so progress is stored in this browser's local storage.
          Run the Spring Boot API (see README) to enable accounts and database sync, or use export/import below to move
          progress between devices.</p>
      }
      @if (message(); as m) { <p class="banner" [class.warn]="isError()">{{ m }}</p> }
    </section>

    <section class="card">
      <h2>Backup</h2>
      <p class="muted">Download all progress, notes and quiz attempts as a JSON file, or restore from one (merges with what's here).</p>
      <div class="row wrap">
        <button class="btn" (click)="exportFile()">Export progress</button>
        <label class="btn">Import progress <input type="file" accept="application/json" hidden (change)="importFile($event)" /></label>
      </div>
    </section>

    <section class="card danger">
      <h2>Reset</h2>
      <p class="muted">Deletes all progress, notes and quiz attempts{{ progress.user() ? ' on the server' : ' in this browser' }}. Export first.</p>
      <button class="btn danger" (click)="reset()">Reset all progress</button>
      @if (progress.user()) {
        <h2>Delete account</h2>
        <p class="muted">Removes your account from the sync server together with everything stored for it. Progress kept
          in this browser from before you signed in is not touched.</p>
        <button class="btn danger" (click)="deleteAccount()" [disabled]="!progress.online()">Delete my account</button>
      }
    </section>
  `,
})
export class AccountPage {
  protected progress = inject(ProgressService);
  private habits = inject(HabitService);
  private zone = inject(NgZone);
  protected googleSignIn = !!GOOGLE_CLIENT_ID;
  protected authTab = signal<'login' | 'register'>('login');
  protected busy = signal(false);
  protected message = signal<string | null>(null);
  protected isError = signal(false);
  protected offlineItems = signal(0);
  private googleButton = viewChild<ElementRef<HTMLElement>>('googleButton');
  username = '';
  password = '';
  displayName = '';

  constructor() {
    // the button's element only exists while signed out and idle, so draw it whenever it appears
    effect(() => {
      const host = this.googleButton()?.nativeElement;
      if (!host) return;
      renderGoogleButton(host, GOOGLE_CLIENT_ID, credential => this.zone.run(() => void this.googleSignedIn(credential)),
        this.progress.theme() === 'dark').catch(e => this.say((e as Error).message, true));
    });
    effect(() => {
      this.progress.user(); // recount after signing in or out
      this.offlineItems.set(this.progress.offlineItemCount());
    });
  }

  private say(msg: string, error = false) {
    this.message.set(msg);
    this.isError.set(error);
  }

  private async googleSignedIn(credential: string) {
    this.busy.set(true);
    this.message.set(null);
    try {
      await this.progress.loginWithGoogle(credential);
      this.say('Signed in. Your progress now syncs to the server.');
    } catch (e) {
      this.say((e as Error).message, true);
    } finally {
      this.busy.set(false);
    }
  }

  async submit() {
    this.busy.set(true);
    try {
      if (this.authTab() === 'login') await this.progress.login(this.username, this.password);
      else await this.progress.register(this.username, this.password, this.displayName);
      this.say('Logged in. Your progress now syncs to the server.');
      this.password = '';
    } catch (e) {
      this.say((e as Error).message, true);
    } finally {
      this.busy.set(false);
    }
  }

  async upload() {
    try {
      const n = await this.progress.uploadLocalToAccount();
      await this.habits.uploadLocalToAccount();
      this.say(`Uploaded ${n} item(s) and your daily routine from this browser.`);
    } catch (e) {
      this.say((e as Error).message, true);
    }
  }

  exportFile() {
    const blob = new Blob([JSON.stringify({ ...this.progress.exportData(), habits: this.habits.exportData() }, null, 1)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `switchprep-progress-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async importFile(ev: Event) {
    const file = (ev.target as HTMLInputElement).files?.[0];
    if (!file) return;
    try {
      const data = JSON.parse(await file.text()) as ExportFile;
      const n = await this.progress.importData(data);
      await this.habits.importData(data.habits);
      this.say(`Imported ${n} item(s).`);
    } catch (e) {
      this.say(`Import failed: ${(e as Error).message}`, true);
    }
  }

  async reset() {
    if (!confirm('Delete ALL progress, notes, quiz attempts and routine logs? This cannot be undone.')) return;
    try {
      await this.progress.reset();
      this.habits.reset();
      this.say('Progress reset.');
    } catch (e) {
      this.say((e as Error).message, true);
    }
  }

  async deleteAccount() {
    const user = this.progress.user();
    if (!user) return;
    if (!confirm('Delete your account and everything stored for it on the server? This cannot be undone.')) return;
    try {
      await this.progress.deleteAccount();
      this.habits.forgetAccount(user.id);
      this.say('Your account and its data have been deleted.');
    } catch (e) {
      this.say((e as Error).message, true);
    }
  }
}
