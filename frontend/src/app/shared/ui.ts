import { Component, Pipe, PipeTransform, computed, effect, inject, input, output, signal } from '@angular/core';
import { Router, UrlTree } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ProgressService } from '../core/progress.service';
import { Section } from '../core/models';

@Component({
  selector: 'app-progress-bar',
  template: `
    <div class="pbar" [title]="done() + ' / ' + total()">
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
  pct = computed(() => (this.total() ? Math.round((this.done() / this.total()) * 100) : 0));
}

/** Done checkbox bound to a progress key. */
@Component({
  selector: 'app-done-toggle',
  template: `
    <button type="button" class="check" [class.on]="done()" (click)="toggle($event)"
            [attr.aria-pressed]="done()" [title]="done() ? 'Mark as not done' : 'Mark as done'">
      <span class="box">{{ done() ? '✓' : '' }}</span>
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
  template: `
    <button type="button" class="star" [class.on]="on()" (click)="toggle($event)"
            [title]="on() ? 'Remove from revision list' : 'Add to revision list'">
      {{ on() ? '★' : '☆' }} @if (label()) { <span>{{ on() ? 'In revision list' : 'Revise later' }}</span> }
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

/** Personal notes for an item, saved on blur. */
@Component({
  selector: 'app-note-box',
  imports: [FormsModule],
  template: `
    <label class="note-box">
      <span class="muted small">My notes {{ saved() ? '· saved' : '' }}</span>
      <textarea rows="4" [(ngModel)]="text" (blur)="save()" (ngModelChange)="saved.set(false)"
                placeholder="Key insight, mistakes you made, edge cases..."></textarea>
    </label>
  `,
})
export class NoteBox {
  private progress = inject(ProgressService);
  key = input.required<string>();
  section = input.required<Section>();
  text = '';
  saved = signal(false);
  constructor() {
    effect(() => { this.text = this.progress.note(this.key()); });
  }
  save() {
    if (this.text !== this.progress.note(this.key())) {
      this.progress.setNote(this.key(), this.section(), this.text);
      this.saved.set(true);
    }
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

/** Turns a content link like "/core/java?chapter=3" into a UrlTree so routerLink keeps the query string. */
@Pipe({ name: 'link' })
export class LinkPipe implements PipeTransform {
  private router = inject(Router);
  transform(link: string): UrlTree {
    return this.router.parseUrl(link);
  }
}
