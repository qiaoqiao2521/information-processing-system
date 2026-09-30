// Enable pending indexes only for the official sources explicitly opted in by the industry pack.
// Seed adds missing sources first. Preserve existing URLs/selectors and administrator edits.
import { readFileSync } from "node:fs";
import { REPO_ROOT } from "@aihot/backend/config";
import { sql, closeDb } from "@aihot/backend/db";
import { publishArticle, republishSource } from "@aihot/backend/publication/publish";
import { stopBoss } from "@aihot/backend/jobs/queue";

const { sources } = JSON.parse(readFileSync(`${REPO_ROOT}/industry/sources.json`, "utf8"));
try {
  for (const source of sources.filter((s: { first_party?: boolean; config?: { _aihot?: { publishPending?: boolean } } }) => s.first_party && s.config?._aihot?.publishPending === true)) {
    const rows = await sql`UPDATE sources SET
      config = jsonb_set(jsonb_set(config, '{_aihot}', coalesce(config->'_aihot', '{}') || '{"publishPending":true}'), '{sortByPublishedAt}', 'true'),
      interval_minutes = LEAST(interval_minutes, 60), next_fetch_at = now(), updated_at = now()
      WHERE id = ${source.id} AND first_party AND participation_mode = 'editorial' RETURNING id`;
    if (!rows.length) throw new Error(`Official source missing or no longer eligible: ${source.id}`);
    const unpublished = await sql<{ id: string }[]>`SELECT a.id FROM articles a LEFT JOIN publications p ON p.article_id=a.id
      WHERE a.source_id=${source.id} AND p.article_id IS NULL ORDER BY a.id`;
    for (const article of unpublished) await publishArticle(article.id);
    console.log(JSON.stringify({ sourceId: source.id, newlyIndexed: unpublished.length, ...await republishSource(source.id) }));
  }
} finally { await stopBoss(); await closeDb(); }
