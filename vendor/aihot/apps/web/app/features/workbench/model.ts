import type { FeedItemSummary, TimelineCard } from '@aihot/contracts/site';
import { CATEGORIES } from '@aihot/industry/taxonomy';
import { displayTitle } from '../../lib/item-display.ts';
import { beijingDate, beijingTime } from '@aihot/contracts/time';

export type Item = { id: string; dataKey?: string; title: string; summary: string; source: string; tag: string; date: string; time: string; raw: FeedItemSummary; group?: TimelineCard['group'] }
export function toWorkbenchItem(raw: FeedItemSummary, group?: TimelineCard['group'], dataKey?: string): Item {
  const at = raw.publishedAt ?? raw.timelineAt
  return { id: raw.id, dataKey, title: displayTitle(raw), summary: raw.summary ?? raw.reason ?? '', source: raw.source.name,
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

/** Generate paper links only from an arXiv identifier or official URL. */
export function arxivHubHref(value: string): string | null {
  const input = value.trim();
  let id = input;
  if (/^https?:/i.test(input)) {
    try {
      const url = new URL(input);
      if (url.protocol !== 'https:' || !['arxiv.org', 'www.arxiv.org'].includes(url.hostname) || url.username || url.password) return null;
      id = url.pathname.replace(/^\/(abs|pdf|html)\//, '').replace(/\.pdf$/, '');
    } catch { return null; }
  }
  return /^(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?\/\d{7})(?:v\d+)?$/.test(id)
    ? `https://papers.muqiao.xyz/p/${encodeURIComponent(id)}` : null;
}
