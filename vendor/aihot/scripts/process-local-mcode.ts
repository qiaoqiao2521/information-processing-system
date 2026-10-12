// Called only by tools/aihot/local_mcode.py through SSH. Normal workers do not enable this channel.
import { processLocalArticle } from "@aihot/backend/editorial/workflow";
import { sql, closeDb } from "@aihot/backend/db";
import { computeHotRanking } from "@aihot/backend/events/hot";
import { stopBoss } from "@aihot/backend/jobs/queue";
import { closeMcode } from "../packages/backend/src/providers/mcode-stdio.ts";

if (process.env.MCODE_STDIO_ENABLED !== "true") throw new Error("Use the local mcode runner");
const localService = process.env.LOCAL_CLI_PROVIDER ?? "mcode";
if (!["mcode", "opencode"].includes(localService)) throw new Error("Unknown local CLI provider");
const args = process.argv.slice(2);
const next = args[0] === "--next" ? Number(args[1]) : null;
if (next !== null && (!Number.isInteger(next) || next < 1 || next > 10 || args.length !== 2)) throw new Error("--next accepts 1–10 recent official articles");
if (next === null && (!args.length || args.length > 10 || args.some((id) => !/^[a-zA-Z0-9_-]{1,80}$/.test(id)))) throw new Error("Pass 1–10 article IDs");
try {
  // Distinct account/transport, distinct attempts. Never change the existing llm/Jina budgets.
  await sql`INSERT INTO budgets (service, per_minute, per_hour, per_day, note)
    VALUES (${localService}, 8, 60, 300, ${`本地${localService}按需加工，独立回执；保守连续24小时上限300次`}) ON CONFLICT (service) DO NOTHING`;
  const ids = next === null ? args : (await sql<{ id: string }[]>`SELECT a.id FROM articles a JOIN sources s ON s.id=a.source_id
    WHERE s.enabled AND s.first_party AND s.config->'_aihot'->>'publishPending'='true'
      AND a.published_at > now()-interval '7 days' AND a.processing_state NOT IN ('analyzed','blocked')
    ORDER BY a.published_at DESC, a.id LIMIT ${next}`).map((row) => row.id);
  console.log(JSON.stringify({ localCli: localService, localCliArticles: ids }));
  for (const id of ids) {
    console.log(JSON.stringify(await processLocalArticle(id,localService)));
  }
  await computeHotRanking();
} finally { closeMcode(); await stopBoss(); await closeDb(); }
