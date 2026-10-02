// Ordinary scheduled script: two tool-free local model calls per new upstream item.
import { createReview, nextAutomaticReviews, processReview, qualityReview, reviewDetail, ReviewDraft } from '@aihot/backend/admin/upstream-reviews';
import { sql, closeDb } from '@aihot/backend/db';
import { closeMcode } from '../packages/backend/src/providers/mcode-stdio.ts';
import { BudgetExceededError } from '@aihot/backend/providers/receipts';
const args=process.argv.slice(2);
const limit=Number(args[1]);
if(process.env.MCODE_STDIO_ENABLED!=='true' || process.env.LOCAL_CLI_PROVIDER!=='opencode') throw new Error('Use local_opencode.py --upstream-next');
if(args.length!==2 || args[0]!=='--next' || !Number.isInteger(limit) || limit<1 || limit>10) throw new Error('--next accepts 1–10 items');
try {
  await sql`INSERT INTO budgets(service,per_minute,per_hour,per_day,note) VALUES('opencode',8,60,300,'本地新闻加工与独立复核，共享连续24小时预算') ON CONFLICT(service) DO NOTHING`;
  // Session lock prevents a second local runner from processing the same batch.
  await sql.reserve().then(async connection=>{
    try {
      const [lock]=await connection`SELECT pg_try_advisory_lock(hashtext('upstream-auto-batch')) AS acquired`;
      if(!lock!.acquired) {console.log(JSON.stringify({skipped:'batch-already-running'}));return;}
      const ids=await nextAutomaticReviews(limit);
      console.log(JSON.stringify({upstreamBatch:ids}));
      for(const id of ids) {
        try {
          await createReview(id,'local:opencode:batch');
          const detail=await reviewDetail(id);
          if(detail?.row.status!=='draft' || !ReviewDraft.safeParse(detail.row.draft).success)
            console.log(JSON.stringify(await processReview(id)));
          console.log(JSON.stringify(await qualityReview(id)));
        } catch(error) {
          if(error instanceof BudgetExceededError) {
            console.log(JSON.stringify({stopped:'budget',service:error.service,retryAfterSeconds:error.retryAfterSeconds}));break;
          }
          console.log(JSON.stringify({id,status:'draft',error:'processing-or-review-failed; inspect admin receipts'}));
          process.exitCode=1;
        }
      }
    } finally {await connection`SELECT pg_advisory_unlock(hashtext('upstream-auto-batch'))`;connection.release();}
  });
} finally {closeMcode();await closeDb();}
