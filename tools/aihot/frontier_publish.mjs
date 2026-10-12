// Reuse the official public projection after an external collector successfully ingests.
// No score, editorial override, model call or historical date is fabricated here.
import { sql, closeDb } from "@aihot/backend/db";
import { publishArticle, republishSource } from "@aihot/backend/publication/publish";
import { stopBoss } from "@aihot/backend/jobs/queue";
const ids = ["frontier-epoch", "frontier-forethought", "frontier-metr", "frontier-arc-prize", "frontier-sakana"];
const id = process.argv[2];
if (!ids.includes(id ?? "")) throw new Error("unsupported frontier source");
try {
  const [source] = await sql`SELECT id FROM sources WHERE id=${id} AND enabled AND first_party
    AND participation_mode='editorial' AND config->'_aihot'->>'publishPending'='true'`;
  if (!source) throw new Error("frontier source paused or no longer eligible");
  if (process.argv.includes("--check")) {
    console.log(JSON.stringify({ sourceId: id, enabled: true }));
  } else {
  const rows = await sql`SELECT a.id FROM articles a LEFT JOIN publications p ON p.article_id=a.id
    WHERE a.source_id=${id} AND p.article_id IS NULL`;
  for (const row of rows) await publishArticle(row.id);
  console.log(JSON.stringify({ sourceId: id, newlyIndexed: rows.length, ...await republishSource(id) }));
  }
} finally { await stopBoss(); await closeDb(); }
