// Bounded orchestration over the existing editorial and event engines.
import { sql } from '../db.ts';
import { analyzeArticle } from './analyze.ts';
import { extractArticleBody } from '../content/extract.ts';
import { publishArticle } from '../publication/publish.ts';
import { groupArticle } from '../events/group.ts';
import { composeStoryDigest } from '../events/digest.ts';
import { BudgetExceededError } from '../providers/receipts.ts';

export async function nextNativeArticles(limit: number) {
  if (!Number.isInteger(limit) || limit < 1 || limit > 10) throw new Error('Workflow batch size must be 1–10');
  const rows = await sql<{id: string}[]>`WITH candidates AS (
    SELECT a.id, s.first_party, coalesce(a.published_at,a.discovered_at) AS at,
      row_number() OVER (PARTITION BY s.id ORDER BY coalesce(a.published_at,a.discovered_at) DESC,a.id) AS source_rank
    FROM articles a JOIN sources s ON s.id=a.source_id
    WHERE s.enabled AND s.participation_mode='editorial' AND s.tier<>'EXCLUDE_MP'
      AND s.kind<>'x_search' AND s.id<>'hub-x' AND NOT a.backfill
      AND coalesce(a.published_at,a.discovered_at) BETWEEN now()-interval '7 days' AND now()
      AND (a.processing_state='new' OR (
        SELECT l.action FROM audit_log l WHERE l.subject='workflow-native:'||a.id
        ORDER BY l.id DESC LIMIT 1)='workflow.native.pause')
      AND NOT EXISTS(SELECT 1 FROM receipts r WHERE r.service='opencode' AND (r.subject=a.id OR r.subject='article:'||a.id||'@'||a.revision::text OR r.subject='article:'||a.id OR r.subject LIKE 'article:'||a.id||':%') AND r.status IN ('pending','failed','unknown'))
      AND NOT EXISTS(SELECT 1 FROM editorial_overrides e WHERE e.article_id=a.id AND e.updated_by IS DISTINCT FROM 'hub-migration')
    ) SELECT id FROM candidates ORDER BY source_rank,first_party DESC,at DESC,id LIMIT ${limit}`;
  return rows.map(row => row.id);
}

export async function recordNativeOutcome(id: string, outcome: 'pause'|'failed'|'complete') {
  await sql`INSERT INTO audit_log(actor,action,subject,reason,after)
    VALUES('local:opencode:workflow',${'workflow.native.'+outcome},${'workflow-native:'+id},${outcome},'{}')`;
}

export async function processLocalArticle(id: string, service = 'opencode') {
  async function stage<T>(work: () => Promise<T>): Promise<T> {
    for (let waits=0;;waits++) {
      try { return await work(); }
      catch (error) {
        if (!(error instanceof BudgetExceededError) || error.service!==service || error.retryAfterSeconds!==60 || waits>=3) throw error;
        console.log(JSON.stringify({articleId:id,waitingForLocalBudgetSeconds:60}));
        await new Promise(resolve=>setTimeout(resolve,60_000));
      }
    }
  }
  if (!(await sql`SELECT id FROM articles WHERE id=${id}`).length) throw new Error(`Article missing: ${id}`);
  await extractArticleBody(id);
  const analysis=await stage(()=>analyzeArticle(id));
  if (!analysis?.analysisId || analysis.stale) throw new Error(`No current analysis committed: ${id}`);
  await sql`DELETE FROM editorial_overrides WHERE article_id=${id} AND updated_by='hub-migration'`;
  await publishArticle(id);
  const grouping=await stage(()=>groupArticle(id));
  if (grouping.storyId) await stage(()=>composeStoryDigest(grouping.storyId!));
  const [publication]=await sql`SELECT article_id,title,score,selected,eligible,category,story_id,fact_id FROM publications WHERE article_id=${id}`;
  return {articleId:id,analysisId:analysis.analysisId,reused:analysis.reused,grouping,publication};
}
