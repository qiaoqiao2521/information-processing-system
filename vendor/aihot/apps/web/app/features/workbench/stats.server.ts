import type { SiteStats } from '@aihot/contracts/site';
import { apiGet } from '../../lib/api.server';

// Optional public telemetry must not hide the feed when the stats endpoint fails.
export async function loadWorkbenchStats(signal: AbortSignal): Promise<SiteStats | null> {
  try {
    return await apiGet<SiteStats>('/api/site/stats', { signal });
  } catch {
    return null;
  }
}
