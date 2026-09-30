// Called only by tools/aihot/local_mcode.py through SSH. Normal workers do not enable this channel.
import { sql, closeDb } from "@aihot/backend/db";
import { analyzeArticle } from "@aihot/backend/editorial/analyze";
import { extractArticleBody } from "@aihot/backend/content/extract";
import { publishArticle } from "@aihot/backend/publication/publish";
import { groupArticle } from "@aihot/backend/events/group";
import { composeStoryDigest } from "@aihot/backend/events/digest";
import { computeHotRanking } from "@aihot/backend/events/hot";
import { stopBoss } from "@aihot/backend/jobs/queue";
import { closeMcode } from "../packages/backend/src/providers/mcode-stdio.ts";
import { BudgetExceededError } from "@aihot/backend/providers/receipts";

if (process.env.MCODE_STDIO_ENABLED !== "true") throw new Error("Use the local mcode runner");
const args = process.argv.slice(2);
const next = args[0] === "--next" ? Number(args[1]) : null;
if (next !== null && (!Number.isInteger(next) || next < 1 || next > 10 || args.length !== 2)) throw new Error("--next accepts 1–10 recent official articles");
if (next === null && (!args.length || args.length > 10 || args.some((id) => !/^[a-zA-Z0-9_-]{1,80}$/.test(id)))) throw new Error("Pass 1–10 article IDs");
async function withMinuteBudget<T>(id: string, work: () => Promise<T>): Promise<T> {
  // Refusal precedes sending; completed stage receipts are reused on the next pass.
  // CLI failures and unknown outcomes do not enter this bounded wait.
  for (let waits = 0; ; waits++) {
    try { return await work(); }
    catch (error) {
      if (!(error instanceof BudgetExceededError) || error.service !== 'mcode' || error.retryAfterSeconds !== 60 || waits >= 3) throw error;
      console.log(JSON.stringify({ articleId: id, waitingForLocalBudgetSeconds: 60 }));
      await new Promise((resolve) => setTimeout(resolve, 60_000));
    }
  }
}
try {
  // Distinct account/transport, distinct attempts. Never change the existing llm/Jina budgets.
  await sql`INSERT INTO budgets (service, per_minute, per_hour, per_day, note)
    VALUES ('mcode', 8, 60, 300, '本地mcode按需加工，独立回执；保守连续24小时上限300次') ON CONFLICT (service) DO NOTHING`;
  const ids = next === null ? args : (await sql<{ id: string }[]>`SELECT a.id FROM articles a JOIN sources s ON s.id=a.source_id
    WHERE s.enabled AND s.first_party AND s.config->'_aihot'->>'publishPending'='true'
      AND a.published_at > now()-interval '7 days' AND a.processing_state NOT IN ('analyzed','blocked')
    ORDER BY a.published_at DESC, a.id LIMIT ${next}`).map((row) => row.id);
  console.log(JSON.stringify({ localMcodeArticles: ids }));
  for (const id of ids) {
    if (!(await sql`SELECT id FROM articles WHERE id=${id}`).length) throw new Error(`Article missing: ${id}`);
    await extractArticleBody(id);
    const analysis = await withMinuteBudget(id, () => analyzeArticle(id));
    if (!analysis?.analysisId || analysis.stale) throw new Error(`No current analysis committed: ${id}`);
    await sql`DELETE FROM editorial_overrides WHERE article_id=${id} AND updated_by='hub-migration'`;
    await publishArticle(id);
    const grouping = await withMinuteBudget(id, () => groupArticle(id));
    if (grouping.storyId) await withMinuteBudget(id, () => composeStoryDigest(grouping.storyId!));
    const [publication] = await sql`SELECT article_id, title, score, selected, eligible FROM publications WHERE article_id=${id}`;
    console.log(JSON.stringify({ analysisId: analysis.analysisId, reused: analysis.reused, grouping, publication }));
  }
  await computeHotRanking();
} finally { closeMcode(); await stopBoss(); await closeDb(); }
