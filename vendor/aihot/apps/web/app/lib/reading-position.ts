import type { LocalReadingItem } from "./local-state";

export async function hashReadingContent(content: string): Promise<string> {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(content));
  return Array.from(new Uint8Array(bytes), (v) => v.toString(16).padStart(2, "0")).join("");
}

export function canResumeReading(saved: LocalReadingItem | undefined, path: string, hash: string): boolean {
  return !!saved && saved.position > 0 && saved.path === path && saved.bodyHash === hash;
}

/** Fraction of the article's scrollable range, independent of the surrounding page chrome. */
export function readingFraction(top: number, height: number, viewport: number, scroll: number): number {
  const range = Math.max(0, height - viewport * 0.65);
  return range > 0 ? Math.max(0, Math.min(1, (scroll - top) / range)) : 0;
}
