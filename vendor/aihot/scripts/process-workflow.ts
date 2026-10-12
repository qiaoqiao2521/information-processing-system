// One scheduled workflow, shared CLI model budget, no coding tools or notifications.
import { sql, closeDb } from '@aihot/backend/db';
import { nextNativeArticles, processLocalArticle, recordNativeOutcome } from '@aihot/backend/editorial/workflow';
import { nextAutomaticReviews, createReview, reviewDetail, processReview, qualityReview, ReviewDraft } from '@aihot/backend/admin/upstream-reviews';
import { BudgetExceededError } from '@aihot/backend/providers/receipts';
import { computeHotRanking } from '@aihot/backend/events/hot';
import { stopBoss } from '@aihot/backend/jobs/queue';
import { closeMcode } from '../packages/backend/src/providers/mcode-stdio.ts';
const args=process.argv.slice(2), limit=Number(args[1]);
if (process.env.MCODE_STDIO_ENABLED!=='true' || process.env.LOCAL_CLI_PROVIDER!=='opencode') throw new Error('Use local_opencode.py --workflow-next');
if (args.length!==2 || args[0]!=='--next' || !Number.isInteger(limit) || limit<1 || limit>10) throw new Error('--next accepts 1–10');
const runId='workflow-'+new Date().toISOString();
console.log(JSON.stringify({workflow:runId,status:'started'}));
try {
  await sql`INSERT INTO budgets(service,per_minute,per_hour,per_day,note) VALUES('opencode',8,60,300,'信息加工workflow共享预算') ON CONFLICT(service) DO NOTHING`;
  const connection=await sql.reserve();
  let acquired=false;
  try {
    // Use the old batch lock too, so an explicitly invoked legacy batch cannot race approvals.
    const [lock]=await connection`SELECT pg_try_advisory_lock(hashtext('upstream-auto-batch')) AS acquired`;
    acquired=lock!.acquired;
    if (!lock!.acquired) {console.log(JSON.stringify({workflow:runId,status:'busy'}));}
    else {
      let paused=false, nativeCompleted=0, nativePublic=0, upstreamSelected=0, upstreamApproved=0, held=0;
      const ids=await nextNativeArticles(limit);
      console.log(JSON.stringify({workflow:runId,nativeBatch:ids}));
      for (const id of ids) {
        try {const result=await processLocalArticle(id);await recordNativeOutcome(id,'complete');nativeCompleted++;if(result.publication?.eligible) nativePublic++;console.log(JSON.stringify({workflow:runId,native:result}));}
        catch(error) {
          paused=error instanceof BudgetExceededError;
          await recordNativeOutcome(id,paused?'pause':'failed');
          // A failed/unknown answer is retained for diagnosis, never retried by the timer.
          if (!paused) {await sql`UPDATE articles SET processing_state='failed',processing_error='workflow stage failed; inspect receipts' WHERE id=${id} AND processing_state='new'`;process.exitCode=1;}
          console.log(JSON.stringify({workflow:runId,articleId:id,status:paused?'budget-paused':'failed',errorType:error instanceof Error?error.constructor.name:'UnknownError'}));
          if (paused) break;
        }
      }
      if (!paused) {
        const upstream=await nextAutomaticReviews(limit);upstreamSelected=upstream.length;
        console.log(JSON.stringify({workflow:runId,upstreamBatch:upstream}));
        for (const id of upstream) {
          try {
            await createReview(id,'local:opencode:batch');
            const detail=await reviewDetail(id);
            if (detail?.row.status!=='draft' || !ReviewDraft.safeParse(detail.row.draft).success) console.log(JSON.stringify(await processReview(id)));
            const result=await qualityReview(id);if(result.status==='approved') upstreamApproved++;else held++;console.log(JSON.stringify(result));
          } catch(error) {
            paused=error instanceof BudgetExceededError;
            console.log(JSON.stringify({workflow:runId,reviewId:id,status:paused?'budget-paused':'failed',errorType:error instanceof Error?error.constructor.name:'UnknownError'}));
            if (paused) break;
            process.exitCode=1;
          }
        }
      }
      await computeHotRanking();
      console.log(JSON.stringify({workflow:runId,status:paused?'budget-paused':process.exitCode?'failed':ids.length||upstreamSelected?'completed':'idle',nativeSelected:ids.length,nativeCompleted,nativePublic,upstreamSelected,upstreamApproved,held}));
    }
  } finally {if(acquired) await connection`SELECT pg_advisory_unlock(hashtext('upstream-auto-batch'))`;connection.release();}
} finally {closeMcode();await stopBoss();await closeDb();}
