import { Injectable, inject } from '@angular/core';
import { ContentService } from './content.service';
import { Section } from './models';

export interface CatalogEntry { key: string; section: Section; title: string; link: string; group: string; }

/** Progress keys used across the app. Changing these orphans saved progress, so keep them stable. */
export const keys = {
  plan: (day: number, taskId: string) => `plan:d${day}:${taskId}`,
  trap: (id: string) => `trap:${id}`,
  round: (id: string) => `round:${id}`,
  dsa: (id: string) => `dsa:${id}`,
  sd: (id: string) => `sd:${id}`,
  note: (subject: string, id: string) => `note:${subject}:${id}`,
  qa: (id: string) => `qa:${id}`,
  final: (id: string) => `fr:${id}`,
  finalQuiz: (day: number) => `final:d${day}`,
  aiLesson: (id: string) => `ai:${id}`,
  aiProject: (moduleId: string) => `ai:${moduleId}:project`,
  aiQuiz: (lessonId: string) => `ai-quiz:${lessonId}`,
};

/** Flat list of every trackable item, used for totals, the revision list and search. */
@Injectable({ providedIn: 'root' })
export class CatalogService {
  private content = inject(ContentService);
  private cached?: Promise<CatalogEntry[]>;

  all(): Promise<CatalogEntry[]> {
    this.cached ??= this.build();
    return this.cached;
  }

  private async build(): Promise<CatalogEntry[]> {
    const [plan, dsa, sd, subjects, finalDays, ai, traps, rounds] = await Promise.all([
      this.content.plan(), this.content.dsa(), this.content.systemDesign(), this.content.subjects(),
      this.content.finalRound(), this.content.aiCourse(), this.content.traps(), this.content.rounds(),
    ]);
    const out: CatalogEntry[] = [];
    for (const d of plan.days) {
      d.tasks.forEach(t => out.push({
        key: keys.plan(d.day, t.id), section: 'plan', title: `Day ${d.day}: ${t.title}`, link: `/plan/${d.day}`, group: 'Plan',
      }));
    }
    for (const p of dsa) {
      for (const q of p.problems) {
        out.push({ key: keys.dsa(q.id), section: 'dsa', title: q.title, link: `/dsa/${p.id}/${q.id}`, group: p.name });
      }
    }
    for (const g of sd) {
      for (const t of g.topics) {
        out.push({ key: keys.sd(t.id), section: 'sd', title: t.title, link: `/system-design/${g.id}/${t.id}`, group: g.name });
      }
    }
    for (const s of subjects) {
      for (const n of s.notes) {
        out.push({ key: keys.note(s.id, n.id), section: 'core', title: n.title, link: `/core/${s.id}`, group: `${s.name} notes` });
      }
      for (const q of s.qa) {
        out.push({ key: keys.qa(q.id ?? q.q), section: 'core', title: q.q, link: `/core/${s.id}`, group: `${s.name} Q&A` });
      }
    }
    for (const d of finalDays) {
      for (const c of [...d.coding, ...d.theory]) {
        out.push({
          key: keys.final(c.id ?? ''), section: 'final', title: 'title' in c ? c.title : c.q,
          link: `/final-round/${d.day}`, group: `Final round day ${d.day}`,
        });
      }
    }
    for (const m of ai) {
      for (const l of m.lessons) {
        out.push({ key: keys.aiLesson(l.id), section: 'ai', title: l.title, link: `/ai/${m.id}/${l.id}`, group: m.title });
      }
      out.push({ key: keys.aiProject(m.id), section: 'ai', title: `Project: ${m.project.title}`, link: `/ai/${m.id}`, group: m.title });
    }
    for (const t of traps) {
      out.push({ key: keys.trap(t.id), section: 'traps', title: t.title, link: `/traps/${t.id}`, group: 'Common traps' });
    }
    for (const r of rounds.rounds) {
      out.push({ key: keys.round(r.id), section: 'rounds', title: r.title, link: `/rounds/${r.id}`, group: 'Interview rounds' });
    }
    return out;
  }
}
