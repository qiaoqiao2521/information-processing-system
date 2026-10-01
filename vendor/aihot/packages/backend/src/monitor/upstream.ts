// Public-result mirror: no account access, model calls, X scraping or notification delivery.
import { z } from "zod";
import type { CodexResetsSnapshot } from "@aihot/contracts/monitor";
import { sql } from "../db.ts";
import { guardedFetch } from "../lib/http-fetch.ts";

export const UPSTREAM_RESET_URL = "https://aihot.news/api/v1/codex-resets";
export const upstreamResetEnabled = () => process.env.CODEX_RESET_UPSTREAM_ENABLED === "true";
const KEY = "monitor.upstream";
const text = z.string().max(100_000);
const date = z.string().refine((v) => Number.isFinite(Date.parse(v)), "Invalid date").nullable();
const url = z.string().url().refine((v) => new URL(v).protocol === "https:", "HTTPS required");
const context = z.object({ id: text, author: text, relation: z.enum(["reply", "quote"]), text: text.nullable(), originalText: text, url }).passthrough();
const post = z.object({ id: text, publishedAt: date, stage: text, text, originalText: text,
  fullText: text.nullable(), fullOriginalText: text.nullable(), context: z.array(context), url }).passthrough();
const window = z.object({ from: date, through: date, label: text }).passthrough();
const event = z.object({ id: text, type: z.enum(["direct_reset", "reset_credit"]), status: z.enum(["announced", "confirmed"]),
  title: text, label: text, displayLabel: text, scope: text, createdAt: date, updatedAt: date, confirmedAt: date,
  occurredOn: date, confirmationBasis: z.enum(["source_post", "receipt_review"]).nullable(),
  schedule: window.extend({ precision: text }).nullable(), estimate: window.extend({ basis: text, reason: text }).nullable(),
  presentation: z.object({ status: z.enum(["announced", "in_progress", "confirmed", "expired_unconfirmed", "likely_completed"]),
    scopeKnown: z.boolean(), scopeLabel: text.nullable(), kindExplicit: z.boolean(), timeInferred: z.boolean(),
    audienceZh: text.nullable(), productsZh: text.nullable() }).passthrough().nullable(), posts: z.array(post), url }).passthrough();
const snapshot = z.object({ schemaVersion: z.literal(1), timezone: z.literal("Asia/Shanghai"), today: text,
  checkedAt: date, historyFrom: date, count: z.number().int().nonnegative(), events: z.array(event).max(5000),
  activities: z.array(z.object({ id: text, publishedAt: date, eventIds: z.array(text), kind: z.enum(["event_update", "related"]),
    text: text.nullable(), originalText: text, context: z.array(context), statusChanged: z.boolean(), action: text.nullable(), url }).passthrough()),
  monitor: z.object({ status: z.enum(["healthy", "delayed", "attention", "unknown"]), lastAttemptAt: date, lastCollectedAt: date,
    lastVerifiedAt: date, heldWindowCount: z.number(), pendingCount: z.number(), reviewCount: z.number() }).passthrough().nullable(),
  outage: z.object({ postId: text, publishedAt: date, text: text.nullable(), originalText: text, recoveredAt: date,
    resetEventId: text.nullable(), url }).passthrough().nullable() }).passthrough();

export function validateUpstreamReset(value: unknown): CodexResetsSnapshot {
  const parsed = snapshot.parse(value);
  if (parsed.count !== parsed.events.length || new Set(parsed.events.map((e) => e.id)).size !== parsed.events.length) {
    throw new Error("Upstream event count or IDs are inconsistent");
  }
  return parsed as unknown as CodexResetsSnapshot;
}
interface Mirror { snapshot: CodexResetsSnapshot; etag: string | null; fetchedAt: string }
export async function readUpstreamReset(now = Date.now()) {
  const [row] = await sql<{ value: Mirror }[]>`SELECT value FROM settings WHERE key = ${KEY}`;
  if (!row) throw new Error("Upstream reset snapshot has not been collected yet");
  const m = row.value;
  return { ...m.snapshot, upstream: { url: UPSTREAM_RESET_URL, fetchedAt: m.fetchedAt,
    stale: now - Date.parse(m.fetchedAt) > 45 * 60_000 || !m.snapshot.checkedAt || now - Date.parse(m.snapshot.checkedAt) > 45 * 60_000 } };
}

export async function refreshUpstreamReset(fetcher: typeof guardedFetch = guardedFetch) {
  if (!upstreamResetEnabled() || process.env.COLLECT_ENABLED === "false") return { skipped: true };
  const [row] = await sql<{ value: Mirror }[]>`SELECT value FROM settings WHERE key = ${KEY}`;
  const old = row?.value;
  const res = await fetcher(UPSTREAM_RESET_URL, { timeoutMs: 30_000, maxBytes: 4 * 1024 * 1024,
    maxRedirects: 0, headers: { accept: "application/json", ...(old?.etag ? { "If-None-Match": old.etag } : {}) } });
  // Validate before writing; a failed or malformed response leaves the last good snapshot untouched.
  const next = res.status === 304 && old ? old : res.status === 200
    ? { snapshot: validateUpstreamReset(JSON.parse(res.text())), etag: res.headers.get("etag"), fetchedAt: "" }
    : null;
  if (!next) throw new Error(`Upstream reset collection failed: HTTP ${res.status}`);
  const value = { ...next, fetchedAt: new Date().toISOString() };
  await sql`INSERT INTO settings (key, value) VALUES (${KEY}, ${sql.json(value as never)})
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()`;
  return { status: res.status, events: value.snapshot.count, fetchedAt: value.fetchedAt };
}
