// Shapes of the JSON files in public/content/. See docs/CONTENT.md for the full schema.

export interface Source { title: string; url: string; }
export interface QA { id?: string; q: string; a: string; level?: string; tags?: string[]; frequent?: boolean; askedAt?: string[]; }
export interface Mcq { id: string; topic?: string; q: string; options: string[]; answer: number; explanation: string; askedAt?: string[]; }

export interface DsaProblem {
  id: string; title: string; difficulty: 'Easy' | 'Medium' | 'Hard'; companies: string[]; leetcode: string;
  summary: string; approach: string; solution: string; time: string; space: string; mustDo: boolean;
}
export interface DsaPattern { id: string; name: string; order: number; intro: string; problems: DsaProblem[]; }

export interface SdTopic {
  id: string; title: string; order: number; level: string; minutes: number; summary: string; content: string;
  keyPoints: string[]; interviewQuestions: QA[]; sources: Source[];
}
export interface SdHld { concepts: SdTopic[]; caseStudies: SdTopic[]; }
export interface SdLld { fundamentals: SdTopic[]; problems: SdTopic[]; }
export interface SdGroup { id: 'concepts' | 'case-studies' | 'lld-fundamentals' | 'lld-problems' | 'senior'; name: string; topics: SdTopic[]; }
export interface SdSenior { topics: (SdTopic & { kind: 'concept' | 'case-study' })[]; }

export interface Note { id: string; title: string; content: string; }
export interface Subject {
  id: string; name: string; order: number; icon: string; description: string; notes: Note[]; qa: QA[]; sources: Source[];
}

export interface CodingQuestion {
  id: string; title: string; difficulty: string; askedAt: string[]; statement: string; hints: string[];
  solution: string; explanation: string; time: string; space: string; leetcode: string | null;
}
export interface FinalDay { day: number; title: string; theme: string; mcqs: Mcq[]; coding: CodingQuestion[]; theory: QA[]; }

export interface Resource { title: string; url: string; type?: string; }
export interface AiLesson {
  id: string; title: string; minutes: number; content: string; exercise: string; quiz: Mcq[] | Omit<Mcq, 'id'>[]; resources: Resource[];
}
export interface AiModule {
  id: string; order: number; title: string; level: string; weeks: number; description: string; outcomes: string[];
  lessons: AiLesson[]; project: { title: string; description: string };
}

export type TaskType = 'dsa' | 'core' | 'sd' | 'ai' | 'mock' | 'revise' | 'career' | 'trap' | 'round';
export interface PlanTask { id: string; type: TaskType; title: string; link?: string; minutes: number; detail?: string; }
export interface PlanDay { day: number; week: number; title: string; focus: string; tasks: PlanTask[]; }
export interface PlanWeek { week: number; title: string; goal: string; }
export interface Plan { intro: string; hoursPerDay: string; weeks: PlanWeek[]; days: PlanDay[]; }

export interface GuideSection { id: string; title: string; icon: string; content: string; }
export interface Guide { sections: GuideSection[]; }

export type Section = 'plan' | 'dsa' | 'sd' | 'core' | 'final' | 'ai' | 'traps' | 'rounds';

export interface ProgressItem {
  key: string; section: Section; done: boolean; revise: boolean; note?: string | null;
  completedAt?: string | null; updatedAt?: string;
}
export interface QuizAttempt {
  id?: number; quizKey: string; score: number; total: number; answersJson?: string; durationSeconds?: number; takenAt: string;
}
export interface User { id: number; username: string; displayName: string; startDate: string; }

export interface Trap {
  id: string; area: string; title: string; level: string; frequency: string; prompt: string;
  options: string[] | null; answer: number | null; commonWrongAnswer: string; whyPeopleGetItWrong: string;
  correct: string; fix: string | null; interviewTip: string; askedAt: string[];
}

export interface InterviewRound {
  id: string; order: number; title: string; icon: string; summary: string; whoRunsIt: string[]; frequency: string;
  weight: string; format: string; whatTheyTest: string[]; rubric: string; howToAce: string; walkthrough: string;
  commonFailures: string[]; practice: { title: string; link: string }[]; sources: Source[];
}
export interface RoundsFile { trends: string; rounds: InterviewRound[]; }

export interface FocusItem { key: string; title: string; link: string; kind: string; why?: string; }
export interface FocusGroup { id: string; title: string; description: string; items: FocusItem[]; }
export interface FocusTier { id: string; title: string; description: string; groups: FocusGroup[]; }
export interface FocusFile { intro: string; tiers: FocusTier[]; }

/** A daily-routine habit. "auto" habits count progress you make elsewhere on the site; others are entered by hand. */
export type HabitKind = 'auto' | 'plan' | 'count' | 'check' | 'minutes' | 'journal';
export interface HabitDef {
  id: string; title: string; icon: string; kind: HabitKind; target: number; unit: string; active: boolean;
  /** For auto habits: progress-key prefixes that count (e.g. "dsa:"). */
  prefixes?: string[];
  /** For auto habits: also count items flagged for revision that day (e.g. flashcards you missed). */
  countRevise?: boolean;
  why?: string;
  custom?: boolean;
}
export interface HabitDayLog { values: Record<string, number>; minutes: number; journal: string; }

/** Routine settings + daily logs, as stored in localStorage and in export files. */
export interface HabitData { habits: HabitDef[]; logs: Record<string, HabitDayLog>; }
