import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HabitService } from './habit.service';
import { ProgressItem, User } from './models';
import { ProgressService } from './progress.service';

// Sync with an API that may be asleep, drop out, refuse a change or end the session.

const USER: User = { id: 7, username: 'g:1', email: 'asha@example.com', displayName: 'Asha', startDate: '2026-10-01' };
const MIRROR = 'switchprep.v1.user.7';
const HABIT_MIRROR = 'switchprep.habits.v1.user.7';
const TWO_SUM: ProgressItem = { key: 'dsa:two-sum', section: 'dsa', done: true, revise: false };
const THREE_SUM_URL = '/api/progress/dsa%3A3sum';

function seedSession(items: Record<string, ProgressItem> = {}): void {
  localStorage.setItem('switchprep.token', 'jwt');
  localStorage.setItem('switchprep.user', JSON.stringify(USER));
  localStorage.setItem(MIRROR, JSON.stringify({ startDate: USER.startDate, items, attempts: [] }));
}

function setup() {
  TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
  return { http: TestBed.inject(HttpTestingController), progress: TestBed.inject(ProgressService) };
}

function health(http: HttpTestingController, up: boolean): void {
  const req = http.expectOne('/actuator/health');
  if (up) req.flush({ status: 'UP' });
  else req.error(new ProgressEvent('error'));
  tick();
}

function serveAccount(http: HttpTestingController, items: ProgressItem[]): void {
  http.expectOne('/api/me').flush(USER);
  http.expectOne('/api/progress').flush(items);
  http.expectOne('/api/quiz-attempts').flush([]);
  tick();
}

const stored = (key: string) => JSON.parse(localStorage.getItem(key) ?? 'null');

describe('sync with the API', () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => localStorage.clear());

  it('signed out: keeps everything in the browser and sends nothing', fakeAsync(() => {
    const { http, progress } = setup();
    health(http, false);
    progress.toggleDone('dsa:3sum', 'dsa');
    TestBed.tick();

    expect(progress.connection()).toBe('local');
    expect(stored('switchprep.v1').items['dsa:3sum'].done).toBeTrue();
    http.verify();
  }));

  it('server asleep at startup: shows the account copy at once, queues changes, sends them when it wakes', fakeAsync(() => {
    seedSession({ [TWO_SUM.key]: TWO_SUM });
    const { http, progress } = setup();

    // before any answer from the server
    expect(progress.user()?.id).toBe(7);
    expect(progress.isDone('dsa:two-sum')).toBeTrue();
    expect(progress.connection()).toBe('connecting');

    health(http, false);
    expect(progress.waking()).toBeTrue();

    progress.toggleDone('dsa:3sum', 'dsa');
    http.expectNone(THREE_SUM_URL);
    expect(progress.pendingCount()).toBe(1);
    TestBed.tick();
    expect(stored(MIRROR).pending.keys).toEqual(['dsa:3sum']); // survives closing the tab

    tick(3000);
    health(http, false);
    tick(5000);
    health(http, true);

    const put = http.expectOne(THREE_SUM_URL);
    expect(put.request.body).toEqual({ section: 'dsa', done: true, revise: false, note: '' });
    put.flush({});
    tick();
    serveAccount(http, [TWO_SUM, { key: 'dsa:3sum', section: 'dsa', done: true, revise: false }]);

    expect(progress.connection()).toBe('online');
    expect(progress.waking()).toBeFalse();
    expect(progress.pendingCount()).toBe(0);
    expect(progress.isDone('dsa:3sum')).toBeTrue();
    http.verify();
  }));

  it('queued changes from an earlier visit are sent on the next one', fakeAsync(() => {
    seedSession({ 'dsa:3sum': { key: 'dsa:3sum', section: 'dsa', done: true, revise: false } });
    localStorage.setItem(MIRROR, JSON.stringify({ ...stored(MIRROR), pending: { keys: ['dsa:3sum'], attempts: [], startDate: false } }));
    const { http, progress } = setup();

    health(http, true);
    http.expectOne(THREE_SUM_URL).flush({});
    tick();
    serveAccount(http, [{ key: 'dsa:3sum', section: 'dsa', done: true, revise: false }]);

    expect(progress.online()).toBeTrue();
    expect(progress.pendingCount()).toBe(0);
    http.verify();
  }));

  it('server drops out while online: the change is kept and sent after reconnecting', fakeAsync(() => {
    seedSession();
    const { http, progress } = setup();
    health(http, true);
    serveAccount(http, []);
    expect(progress.online()).toBeTrue();

    progress.toggleDone('dsa:3sum', 'dsa');
    http.expectOne(THREE_SUM_URL).error(new ProgressEvent('error'));
    tick();
    expect(progress.connection()).toBe('connecting');
    expect(progress.pendingCount()).toBe(1);
    expect(progress.isDone('dsa:3sum')).toBeTrue();

    health(http, true);
    http.expectOne(THREE_SUM_URL).flush({});
    tick();
    serveAccount(http, [{ key: 'dsa:3sum', section: 'dsa', done: true, revise: false }]);
    expect(progress.online()).toBeTrue();
    expect(progress.pendingCount()).toBe(0);
    http.verify();
  }));

  it('a change made while the account is loading is not overwritten by the load', fakeAsync(() => {
    seedSession();
    const { http, progress } = setup();
    health(http, true);

    progress.toggleDone('dsa:3sum', 'dsa'); // account is still loading
    serveAccount(http, []);                 // server knows nothing about it yet
    expect(progress.isDone('dsa:3sum')).toBeTrue();

    http.expectOne(THREE_SUM_URL).flush({});
    tick();
    serveAccount(http, [{ key: 'dsa:3sum', section: 'dsa', done: true, revise: false }]);
    expect(progress.online()).toBeTrue();
    http.verify();
  }));

  it('server refuses a change: the user is told and it is not retried', fakeAsync(() => {
    seedSession();
    const { http, progress } = setup();
    health(http, true);
    serveAccount(http, []);

    progress.toggleDone('dsa:3sum', 'dsa');
    http.expectOne(THREE_SUM_URL).flush({ error: 'This account has reached its limit' }, { status: 422, statusText: 'Unprocessable' });
    tick();

    expect(progress.syncError()).toBe('This account has reached its limit');
    expect(progress.pendingCount()).toBe(0);
    expect(progress.online()).toBeTrue();
    http.verify();
  }));

  it('session expires: signs out, keeps the unsent change, and sends it after signing in again', fakeAsync(() => {
    seedSession();
    const { http, progress } = setup();
    health(http, true);
    serveAccount(http, []);

    progress.toggleDone('dsa:3sum', 'dsa');
    http.expectOne(THREE_SUM_URL).flush({}, { status: 401, statusText: 'Unauthorized' });
    tick();
    TestBed.tick();

    expect(progress.user()).toBeNull();
    expect(progress.connection()).toBe('local');
    expect(progress.syncError()).toContain('expired');
    expect(progress.isDone('dsa:3sum')).toBeFalse(); // back to this browser's signed-out copy
    expect(stored(MIRROR).pending.keys).toEqual(['dsa:3sum']);
    expect(localStorage.getItem('switchprep.token')).toBeNull();

    let signedIn = false;
    void progress.loginWithGoogle('google-credential').then(() => (signedIn = true));
    health(http, true);
    const login = http.expectOne('/api/auth/google');
    expect(login.request.body).toEqual({ credential: 'google-credential' });
    login.flush({ token: 'jwt-2', user: USER });
    tick();
    health(http, true);
    http.expectOne(THREE_SUM_URL).flush({});
    tick();
    serveAccount(http, [{ key: 'dsa:3sum', section: 'dsa', done: true, revise: false }]);

    expect(signedIn).toBeTrue();
    expect(progress.online()).toBeTrue();
    expect(progress.isDone('dsa:3sum')).toBeTrue();
    expect(progress.syncError()).toBeNull();
    http.verify();
  }));

  it('signing in waits for a sleeping server instead of failing', fakeAsync(() => {
    const { http, progress } = setup();
    health(http, false); // the signed-out look at startup

    let error: Error | null = null;
    void progress.loginWithGoogle('google-credential').catch(e => (error = e));
    health(http, false);
    expect(progress.waking()).toBeTrue();
    http.expectNone('/api/auth/google');
    tick(3000);
    health(http, true);
    http.expectOne('/api/auth/google').flush({ token: 'jwt', user: USER });
    tick();
    health(http, true);
    serveAccount(http, [TWO_SUM]);

    expect(error).toBeNull();
    expect(progress.user()?.email).toBe('asha@example.com');
    expect(progress.online()).toBeTrue();
    expect(progress.isDone('dsa:two-sum')).toBeTrue();
    http.verify();
  }));

  it('signing out shows the browser copy again and leaves the account copy alone', fakeAsync(() => {
    localStorage.setItem('switchprep.v1', JSON.stringify({ startDate: '2026-09-01', items: { 'dsa:lru-cache': { key: 'dsa:lru-cache', section: 'dsa', done: true, revise: false } }, attempts: [] }));
    seedSession({ [TWO_SUM.key]: TWO_SUM });
    const { http, progress } = setup();
    health(http, true);
    serveAccount(http, [TWO_SUM]);
    TestBed.tick();

    progress.logout();
    TestBed.tick();

    expect(progress.isDone('dsa:lru-cache')).toBeTrue();
    expect(progress.isDone('dsa:two-sum')).toBeFalse();
    expect(stored(MIRROR).items['dsa:two-sum'].done).toBeTrue();
    expect(stored('switchprep.v1').items['dsa:two-sum']).toBeUndefined();
    http.verify();
  }));

  it('deleting the account removes it on the server and its copies in this browser', fakeAsync(() => {
    seedSession({ [TWO_SUM.key]: TWO_SUM });
    localStorage.setItem(HABIT_MIRROR, JSON.stringify({ habits: [], logs: { '2026-10-10': { values: {}, minutes: 30, journal: '' } } }));
    const { http, progress } = setup();
    const habits = TestBed.inject(HabitService);
    health(http, true);
    serveAccount(http, [TWO_SUM]);
    TestBed.tick();
    http.match(r => r.url.startsWith('content/')).forEach(r => r.flush({ intro: '', hoursPerDay: '', weeks: [], days: [] }));
    http.expectOne('/api/habits').flush(null, { status: 204, statusText: 'No Content' });
    http.expectOne('/api/habit-logs').flush([]);
    tick();

    let done = false;
    void progress.deleteAccount().then(() => { habits.forgetAccount(USER.id); done = true; });
    http.expectOne(r => r.method === 'DELETE' && r.url === '/api/me').flush(null);
    tick();
    TestBed.tick();

    expect(done).toBeTrue();
    expect(progress.user()).toBeNull();
    expect(localStorage.getItem(MIRROR)).toBeNull();
    expect(localStorage.getItem(HABIT_MIRROR)).toBeNull();
    expect(localStorage.getItem('switchprep.token')).toBeNull();
    http.verify();
  }));

  it('daily routine: shows the account copy while the server sleeps and sends queued days when it wakes', fakeAsync(() => {
    seedSession();
    localStorage.setItem(HABIT_MIRROR, JSON.stringify({ habits: [], logs: { '2026-10-09': { values: {}, minutes: 45, journal: 'outbox' } } }));
    const { http, progress } = setup();
    const habits = TestBed.inject(HabitService);
    TestBed.tick();
    http.match(r => r.url.startsWith('content/')).forEach(r => r.flush({ intro: '', hoursPerDay: '', weeks: [], days: [] }));

    expect(habits.log('2026-10-09').minutes).toBe(45);
    health(http, false);

    habits.setJournal('learned idempotency keys', '2026-10-10');
    TestBed.tick();
    http.expectNone('/api/habit-logs/2026-10-10');
    expect(stored(HABIT_MIRROR).pending.dates).toEqual(['2026-10-10']);

    tick(3000);
    health(http, true);
    serveAccount(http, []);
    expect(progress.online()).toBeTrue();
    TestBed.tick();

    const put = http.expectOne('/api/habit-logs/2026-10-10');
    expect(put.request.body.journal).toBe('learned idempotency keys');
    put.flush({});
    tick();
    http.expectOne('/api/habits').flush(null, { status: 204, statusText: 'No Content' });
    http.expectOne('/api/habit-logs').flush([
      { date: '2026-10-09', valuesJson: null, minutes: 45, journal: 'outbox' },
      { date: '2026-10-10', valuesJson: '{}', minutes: 0, journal: 'learned idempotency keys' },
    ]);
    tick();
    TestBed.tick();

    expect(habits.log('2026-10-10').journal).toBe('learned idempotency keys');
    expect(stored(HABIT_MIRROR).pending.dates).toEqual([]);
    http.verify();
  }));
});
