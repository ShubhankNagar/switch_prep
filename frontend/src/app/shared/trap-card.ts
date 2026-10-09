import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { keys } from '../core/catalog.service';
import { Trap } from '../core/models';
import { ProgressService } from '../core/progress.service';
import { MarkdownPipe } from './markdown.pipe';
import { ReviseToggle } from './ui';

export const TRAP_AREAS: Record<string, string> = {
  java: 'Core Java', concurrency: 'Concurrency', spring: 'Spring', 'jpa-hibernate': 'JPA / Hibernate', sql: 'SQL',
  dsa: 'DSA & coding', 'system-design': 'System design', 'distributed-systems': 'Distributed systems',
  'api-design': 'API design', 'angular-js': 'Angular & JS', 'os-networking': 'OS & networking', behavioral: 'Behavioral',
};

/** Picks a stable "trap of the day": the same unsolved trap all day, a different one tomorrow. */
export function trapOfTheDay(traps: Trap[], isDone: (key: string) => boolean, dateIso: string): Trap | undefined {
  const open = traps.filter(t => !isDone(keys.trap(t.id)));
  const pool = open.length ? open : traps;
  if (!pool.length) return undefined;
  let h = 0;
  for (const ch of dateIso) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return pool[h % pool.length];
}

/** Guess-first card: commit to an answer, then see what most people get wrong and why. */
@Component({
  selector: 'app-trap-card',
  imports: [MarkdownPipe, ReviseToggle],
  template: `
    @let t = trap();
    <div class="trap card" [class.solved]="done()">
      <div class="mcq-head">
        <span class="tag must">{{ areaName(t.area) }}</span>
        <span class="tag" [class]="'tag lvl-' + t.level.toLowerCase()">{{ t.level }}</span>
        <span class="tag">{{ t.frequency }}</span>
        @for (c of t.askedAt; track c) { <span class="tag company">{{ c }}</span> }
        <span class="spacer"></span>
        <app-revise-toggle [key]="key()" section="traps" />
      </div>
      <h3>🪤 {{ t.title }}</h3>
      <div class="md" [innerHTML]="t.prompt | md"></div>

      @if (t.options) {
        <div class="options">
          @for (opt of t.options; track $index; let o = $index) {
            <button type="button" class="option" [disabled]="revealed()"
                    [class.picked]="picked() === o"
                    [class.right]="revealed() && o === t.answer"
                    [class.bad]="revealed() && picked() === o && o !== t.answer"
                    (click)="pick(o)">
              <span class="letter">{{ 'ABCD'[o] }}</span> <span [innerHTML]="opt | md"></span>
            </button>
          }
        </div>
      } @else if (!revealed()) {
        <p class="muted small">Say your answer out loud (or jot it in your head) before revealing.</p>
        <button class="btn primary" (click)="revealed.set(true)">I have my answer, reveal</button>
      }

      @if (revealed()) {
        <div class="trap-reveal">
          @if (t.options && picked() !== null) {
            <p class="verdict" [class.good]="picked() === t.answer">
              {{ picked() === t.answer ? '✓ You avoided the trap.' : '✗ You fell for it, like most people.' }}</p>
          }
          <div class="trap-block wrong"><b>What most people say:</b> {{ t.commonWrongAnswer }}</div>
          <div class="trap-block"><b>Why it trips people up</b><div class="md" [innerHTML]="t.whyPeopleGetItWrong | md"></div></div>
          <div class="trap-block right"><b>The correct answer</b><div class="md" [innerHTML]="t.correct | md"></div></div>
          @if (t.fix) { <div class="trap-block"><b>The fix</b><div class="md" [innerHTML]="t.fix | md"></div></div> }
          <p class="tip">💡 <b>Interview tip:</b> {{ t.interviewTip }}</p>
          <div class="row wrap">
            @if (!done()) {
              <button class="btn primary" (click)="finish(true)">Got it right</button>
              <button class="btn" (click)="finish(false)">Got it wrong, add to revision</button>
            } @else {
              <span class="muted small">✓ Marked as beaten{{ progress.isRevise(key()) ? ' · in your revision list' : '' }}</span>
              <button class="btn small" (click)="retry()">Try again</button>
            }
          </div>
        </div>
      }
    </div>
  `,
})
export class TrapCard {
  protected progress = inject(ProgressService);
  trap = input.required<Trap>();
  protected key = computed(() => keys.trap(this.trap().id));
  protected done = computed(() => this.progress.isDone(this.key()));
  protected picked = signal<number | null>(null);
  protected revealed = signal(false);

  constructor() {
    effect(() => {
      this.trap();
      this.picked.set(null);
      this.revealed.set(false);
    });
  }

  areaName(a: string) { return TRAP_AREAS[a] ?? a; }
  pick(o: number) {
    this.picked.set(o);
    this.revealed.set(true);
  }
  finish(right: boolean) {
    this.progress.update(this.key(), 'traps', right ? { done: true } : { done: true, revise: true });
  }
  retry() {
    this.picked.set(null);
    this.revealed.set(false);
  }
}
