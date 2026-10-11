import type { FeedItemSummary, TimelineCard } from '@aihot/contracts/site';
import { CATEGORIES } from '@aihot/industry/taxonomy';
import { beijingDate, beijingTime } from '@aihot/contracts/time';

export type Item = { id: string; dataKey?: string; title: string; summary: string; source: string; tag: string; date: string; time: string; raw: FeedItemSummary; group?: TimelineCard['group'] }
export function toWorkbenchItem(raw: FeedItemSummary, group?: TimelineCard['group'], dataKey?: string): Item {
  const at = raw.publishedAt ?? raw.timelineAt
  return { id: raw.id, dataKey, title: raw.title, summary: raw.summary ?? raw.reason ?? '', source: raw.source.name,
    tag: CATEGORIES.find(c => c.key === raw.category)?.section ?? (raw.channel === 'x' ? 'X' : '待AI处理'),
    date: beijingDate(at), time: beijingTime(at), raw, group }
}
/** Filters are URL state. A filter change resets paging and retains the other criteria. */
export function filterHref(base: string, params: URLSearchParams, patch: Record<string, string | null>) {
  const next = new URLSearchParams(params);
  for (const key of ['page', 'deep', 'anchorAt', 'search']) next.delete(key);
  for (const [key, value] of Object.entries(patch)) value ? next.set(key, value) : next.delete(key);
  const query = next.toString();
  return `${base}${query ? `?${query}` : ''}`;
}
