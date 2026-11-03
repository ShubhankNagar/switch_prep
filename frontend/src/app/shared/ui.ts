import { Component, OnDestroy, Pipe, PipeTransform, computed, effect, inject, input, output, signal, untracked } from '@angular/core';
import { Router, RouterLink, UrlTree } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ProgressService } from '../core/progress.service';
import { Section } from '../core/models';
import { Icon } from './icon';

@Component({
  selector: 'app-progress-bar',
  template: `
    <div class="pbar" [class.accent]="accent()" [title]="done() + ' / ' + total()">
      <div class="pbar-fill" [style.width.%]="pct()"></div>
    </div>
    @if (showLabel()) { <span class="pbar-label">{{ done() }}/{{ total() }} · {{ pct() }}%</span> }
  `,
  host: { class: 'pbar-wrap' },
})
export class ProgressBar {
  done = input.required<number>();
  total = input.required<number>();
  showLabel = input(true);
  accent = input(false);
  pct = computed(() => (this.total() ? Math.round((this.done() / this.total()) * 100) : 0));
}

/** Done checkbox bound to a progress key. */
@Component({
  selector: 'app-done-toggle',
  imports: [Icon],
  template: `
    <button type="button" class="check" [class.on]="done()" (click)="toggle($event)"
            [attr.aria-pressed]="done()" [title]="done() ? 'Mark as not done' : 'Mark as done'">
      <span class="box">@if (done()) { <app-icon name="check" /> }</span>
      @if (label()) { <span>{{ done() ? doneLabel() : label() }}</span> }
    </button>
  `,
})
export class DoneToggle {
  private progress = inject(ProgressService);
  key = input.required<string>();
  section = input.required<Section>();
  label = input('');
  doneLabel = input('Done');
  done = computed(() => this.progress.isDone(this.key()));
  toggle(e: Event) {
    e.stopPropagation();
    e.preventDefault();
    this.progress.toggleDone(this.key(), this.section());
  }
}

/** "Revise later" star bound to a progress key. */
@Component({
  selector: 'app-revise-toggle',
  imports: [Icon],
  template: `
    <button type="button" class="star" [class.on]="on()" (click)="toggle($event)" [attr.aria-pressed]="on()"
            [title]="on() ? 'Remove from revision list' : 'Add to revision list'">
      <app-icon name="star" /> @if (label()) { <span>{{ on() ? 'In revision list' : 'Revise later' }}</span> }
    </button>
  `,
})
export class ReviseToggle {
  private progress = inject(ProgressService);
  key = input.required<string>();
  section = input.required<Section>();
  label = input(false);
  on = computed(() => this.progress.isRevise(this.key()));
  toggle(e: Event) {
    e.stopPropagation();
    e.preventDefault();
    this.progress.toggleRevise(this.key(), this.section());
  }
}

/** Personal notes for an item, saved a moment after typing stops, on blur, and when the page changes. */
@Component({
  selector: 'app-note-box',
  imports: [FormsModule],
  template: `
    <label class="note-box">
      <span class="muted small">My notes {{ saved() ? '· saved' : '' }}</span>
      <textarea rows="4" [(ngModel)]="text" (blur)="save()" (ngModelChange)="changed()"
                placeholder="Key insight, mistakes you made, edge cases..."></textarea>
    </label>
  `,
})
export class NoteBox implements OnDestroy {
  private progress = inject(ProgressService);
  key = input.required<string>();
  section = input.required<Section>();
  text = '';
  saved = signal(false);
  /** The item `text` belongs to; prev/next navigation reuses this component for another item. */
  private shownKey = '';
  private shownSection: Section = 'core';
  private timer?: ReturnType<typeof setTimeout>;

  constructor() {
    effect(() => {
      const key = this.key();
      const section = this.section();
      untracked(() => {
        if (key !== this.shownKey) this.save(); // keep what was typed for the previous item
        this.shownKey = key;
        this.shownSection = section;
        this.text = this.progress.note(key);
        this.saved.set(false);
      });
    });
  }

  changed() {
    this.saved.set(false);
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.save(), 1200);
  }

  save() {
    clearTimeout(this.timer);
    if (this.shownKey && this.text !== this.progress.note(this.shownKey)) {
      this.progress.setNote(this.shownKey, this.shownSection, this.text);
      this.saved.set(true);
    }
  }

  ngOnDestroy() {
    this.save();
  }
}

@Component({
  selector: 'app-tag',
  template: `<ng-content />`,
  host: { class: 'tag', '[class]': '"tag " + kind()' },
})
export class Tag {
  kind = input<string>('');
}

export const difficultyClass = (d: string) => (d || '').toLowerCase();

@Component({
  selector: 'app-empty',
  template: `<div class="empty"><ng-content /></div>`,
})
export class Empty {
  dismiss = output<void>();
}

/** What a detail page shows while its content loads, or when the address points at nothing. */
@Component({
  selector: 'app-page-state',
  imports: [RouterLink],
  template: `
    @if (loading()) {
      <div class="skeleton" aria-busy="true" aria-label="Loading">
        <span class="sk sk-title"></span><span class="sk"></span><span class="sk"></span><span class="sk sk-short"></span>
      </div>
    } @else {
      <div class="card empty">
        <h2>Nothing here</h2>
        <p>This page does not exist, or its address has changed.</p>
        <a class="btn primary" [routerLink]="backLink()">{{ backLabel() }}</a>
      </div>
    }
  `,
})
export class PageState {
  loading = input.required<boolean>();
  backLink = input('/');
  backLabel = input('Back to the dashboard');
}

/** Turns a content link like "/core/java?chapter=3" into a UrlTree so routerLink keeps the query string. */
@Pipe({ name: 'link' })
export class LinkPipe implements PipeTransform {
  private router = inject(Router);
  transform(link: string): UrlTree {
    return this.router.parseUrl(link);
  }
}
