/** Days after which a starred item comes back for review. Reviewing it (or any change to it) restarts the wait. */
export const REVIEW_AFTER_DAYS = 3;

/** True when a starred item was last touched at least REVIEW_AFTER_DAYS ago (or has never been dated). */
export function isDue(updatedAt: string | undefined, now = Date.now()): boolean {
  if (!updatedAt) return true;
  return now - new Date(updatedAt).getTime() >= REVIEW_AFTER_DAYS * 86400000;
}

/** Whole days since an ISO time, for "reviewed 4 days ago". */
export function daysSince(iso: string | undefined, now = Date.now()): number | undefined {
  return iso ? Math.max(0, Math.floor((now - new Date(iso).getTime()) / 86400000)) : undefined;
}
