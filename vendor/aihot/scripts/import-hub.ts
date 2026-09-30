// Import already-public reading snapshots without inventing model scores or new publication dates.
import { readFileSync } from "node:fs";
import { closeDb, sql } from "@aihot/backend/db";
import { upsertMaterial } from "@aihot/backend/content/materials";
import { publishArticle } from "@aihot/backend/publication/publish";
import { normalizeUrl } from "@aihot/backend/lib/url";

interface HubItem {
  id: string; sourceId: string; title: string; summary: string; body: string; url: string;
  publishedAt: string | null; collectedAt: string | null; author: string;
}
const input = process.argv[2];
if (!input) throw new Error("Usage: node scripts/import-hub.ts public-library.json");
const { items } = JSON.parse(readFileSync(input, "utf8")) as { items: HubItem[] };
let created = 0, skipped = 0;
for (const item of items) {
  const sourceId = `hub-${item.sourceId}`;
  const [source] = await sql`SELECT id FROM sources WHERE id = ${sourceId}`;
  if (!source || !item.url || !item.title) { skipped++; continue; }
  let url: string;
  try { url = normalizeUrl(item.url); } catch { skipped++; continue; }
  const date = (s: string | null) => s && Number.isFinite(Date.parse(s)) ? new Date(s) : null;
  const discovered = date(item.collectedAt) ?? date(item.publishedAt);
  // Unknown historic dates stay unknown; don't stamp them as newly discovered today.
  if (!discovered) { skipped++; continue; }
  const result = await upsertMaterial({
    id: item.id, sourceId, url, title: item.title, author: item.author || null,
    publishedAt: date(item.publishedAt), discoveredAt: discovered,
    excerpt: item.summary || null, bodyText: item.body || null, via: "import",
    bodyStatus: item.body ? "ok" : "unconfirmed", backfill: "hub-migration",
    raw: { legacyId: item.id, migration: "hub", modelProcessed: false },
  });
  await sql`INSERT INTO settings (key, value, updated_by)
    VALUES (${`hub.legacy.${item.id}`}, ${sql.json({ articleId: result.articleId })}, 'hub-migration')
    ON CONFLICT (key) DO NOTHING`;
  if (result.created) {
    created++;
    // Use the existing editorial mechanism; no fabricated analyses, scores, or selection.
    const summary = item.summary || "旧站内容索引，未经本轮模型评分。请查看原文。";
    const fields = { title: item.title, summary, relevance: "pass", selected: false, tags: ["迁移存量", "未重新评分"] };
    await sql`INSERT INTO editorial_overrides (article_id, fields, visibility, reason, updated_by)
      VALUES (${result.articleId}, ${sql.json(fields)}, 'public', '保留旧站公开摘要；未调用模型', 'hub-migration')`;
    await sql`UPDATE articles SET processing_state = 'skipped', processing_queued_at = NULL WHERE id = ${result.articleId}`;
    await publishArticle(result.articleId, { releasedAt: discovered });
  }
}
console.log(JSON.stringify({ received: items.length, created, skipped }));
await closeDb();
