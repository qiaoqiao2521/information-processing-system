import { closeDb, sql } from '@aihot/backend/db';
import { analyzeArticle } from '@aihot/backend/editorial/analyze';
import { extractArticleBody } from '@aihot/backend/content/extract';
import { groupArticle } from '@aihot/backend/events/group';
import { composeStoryDigest } from '@aihot/backend/events/digest';
import { publishArticle } from '@aihot/backend/publication/publish';
import { computeHotRanking } from '@aihot/backend/events/hot';
import { stopBoss } from '@aihot/backend/jobs/queue';
const ids = process.argv.slice(2);
if (!ids.length || ids.length > 3) throw new Error('Pass 1–3 existing article IDs; bulk validation is refused');
try {
  for (const id of ids) {
    const [article] = await sql`SELECT id, body_text, body_status FROM articles WHERE id = ${id}`;
    if (!article) throw new Error(`Article not found: ${id}`);
    if (!article.body_text) await extractArticleBody(id);
    const analysis = await analyzeArticle(id);
    if (!analysis?.analysisId) throw new Error(`Analysis not completed: ${id}`);
    // Replace migration overrides only after a real analysis commits successfully.
    await sql`DELETE FROM editorial_overrides WHERE article_id = ${id} AND updated_by = 'hub-migration'`;
    await publishArticle(id);
    const grouping = await groupArticle(id);
    if (grouping.storyId) await composeStoryDigest(grouping.storyId);
    console.log(JSON.stringify({ id, analysisId: analysis.analysisId, reused: analysis.reused, grouping }));
  }
  await computeHotRanking();
  const rows = await sql`SELECT article_id, score, selected, title FROM publications WHERE article_id IN ${sql(ids)}`;
  console.log(JSON.stringify(rows));
} finally { await stopBoss(); await closeDb(); }
