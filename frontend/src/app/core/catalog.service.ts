import { Injectable, inject } from '@angular/core';
import { ContentService } from './content.service';
import { CatalogEntry } from './models';

export type { CatalogEntry } from './models';

/**
 * Progress keys used across the app. Changing these orphans saved progress, so keep them stable.
 * content-gen/build_catalog.py and build_focus.py write the same formats into catalog.json and focus.json.
 */
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

/**
 * Flat list of every trackable item, used for totals, the revision list and search. It comes from the small
 * catalog.json index, so these pages do not download all the content files.
 */
@Injectable({ providedIn: 'root' })
export class CatalogService {
  private content = inject(ContentService);

  all(): Promise<CatalogEntry[]> {
    return this.content.catalog();
  }
}
