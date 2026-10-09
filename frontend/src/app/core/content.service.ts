import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import {
  AiModule, DsaPattern, FinalDay, FocusFile, Guide, Plan, RoundsFile, SdGroup, SdHld, SdLld, SdSenior, Subject, Trap,
} from './models';

/** Loads the static content JSON files from public/content (cached, loaded on first use). */
@Injectable({ providedIn: 'root' })
export class ContentService {
  private http = inject(HttpClient);
  private cache = new Map<string, Promise<unknown>>();

  private load<T>(file: string, fallback: T): Promise<T> {
    if (!this.cache.has(file)) {
      const p = firstValueFrom(this.http.get<T>(`content/${file}`)).catch(err => {
        console.warn(`Could not load content/${file}`, err);
        return fallback;
      });
      this.cache.set(file, p);
    }
    return this.cache.get(file) as Promise<T>;
  }

  async plan(): Promise<Plan> {
    return this.load<Plan>('plan.json', { intro: '', hoursPerDay: '', weeks: [], days: [] });
  }

  async guide(): Promise<Guide> {
    return this.load<Guide>('guide.json', { sections: [] });
  }

  async dsa(): Promise<DsaPattern[]> {
    const parts = await Promise.all([
      this.load<{ patterns: DsaPattern[] }>('dsa-part1.json', { patterns: [] }),
      this.load<{ patterns: DsaPattern[] }>('dsa-part2.json', { patterns: [] }),
    ]);
    return parts.flatMap(p => p.patterns).sort((a, b) => a.order - b.order);
  }

  async systemDesign(): Promise<SdGroup[]> {
    const [hld, lld, senior] = await Promise.all([
      this.load<SdHld>('system-design-hld.json', { concepts: [], caseStudies: [] }),
      this.load<SdLld>('system-design-lld.json', { fundamentals: [], problems: [] }),
      this.load<SdSenior>('system-design-senior.json', { topics: [] }),
    ]);
    const byOrder = <T extends { order: number }>(xs: T[]) => [...xs].sort((a, b) => a.order - b.order);
    return [
      { id: 'concepts', name: 'HLD Concepts', topics: byOrder(hld.concepts) },
      { id: 'case-studies', name: 'HLD Case Studies', topics: byOrder(hld.caseStudies) },
      { id: 'lld-fundamentals', name: 'LLD Fundamentals', topics: byOrder(lld.fundamentals) },
      { id: 'lld-problems', name: 'LLD / Machine Coding', topics: byOrder(lld.problems) },
      { id: 'senior', name: 'Senior Design (2027)', topics: byOrder(senior.topics) },
    ];
  }

  async subjects(): Promise<Subject[]> {
    const parts = await Promise.all([
      this.load<{ subjects: Subject[] }>('core-backend.json', { subjects: [] }),
      this.load<{ subjects: Subject[] }>('core-cs.json', { subjects: [] }),
      this.load<{ subjects: Subject[] }>('core-senior-1.json', { subjects: [] }),
      this.load<{ subjects: Subject[] }>('core-senior-2.json', { subjects: [] }),
    ]);
    return parts.flatMap(p => p.subjects).sort((a, b) => a.order - b.order);
  }

  async finalRound(): Promise<FinalDay[]> {
    const parts = await Promise.all([
      this.load<{ days: FinalDay[] }>('final-round-1.json', { days: [] }),
      this.load<{ days: FinalDay[] }>('final-round-2.json', { days: [] }),
    ]);
    return parts.flatMap(p => p.days).sort((a, b) => a.day - b.day);
  }

  async aiCourse(): Promise<AiModule[]> {
    const parts = await Promise.all([
      this.load<{ modules: AiModule[] }>('ai-course-1.json', { modules: [] }),
      this.load<{ modules: AiModule[] }>('ai-course-2.json', { modules: [] }),
    ]);
    return parts.flatMap(p => p.modules).sort((a, b) => a.order - b.order);
  }

  async traps(): Promise<Trap[]> {
    const parts = await Promise.all([
      this.load<{ traps: Trap[] }>('traps-1.json', { traps: [] }),
      this.load<{ traps: Trap[] }>('traps-2.json', { traps: [] }),
    ]);
    return parts.flatMap(p => p.traps);
  }

  async rounds(): Promise<RoundsFile> {
    const file = await this.load<RoundsFile>('rounds.json', { trends: '', rounds: [] });
    return { ...file, rounds: [...file.rounds].sort((a, b) => a.order - b.order) };
  }

  async focus(): Promise<FocusFile> {
    return this.load<FocusFile>('focus.json', { intro: '', tiers: [] });
  }
}
