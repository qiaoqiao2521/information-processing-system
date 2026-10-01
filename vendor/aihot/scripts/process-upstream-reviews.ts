// Operator-started local OpenCode session only; answers become private drafts.
import { processReview } from '@aihot/backend/admin/upstream-reviews';
import { sql, closeDb } from '@aihot/backend/db';
import { closeMcode } from '../packages/backend/src/providers/mcode-stdio.ts';
const ids=process.argv.slice(2);
if(process.env.MCODE_STDIO_ENABLED!=='true' || process.env.LOCAL_CLI_PROVIDER!=='opencode') throw new Error('Use local_opencode.py --review');
if(!ids.length || ids.length>10 || ids.some(id=>!/^\w[\w-]{0,79}$/.test(id))) throw new Error('Pass 1–10 review IDs');
try {
  await sql`INSERT INTO budgets(service,per_minute,per_hour,per_day,note) VALUES('opencode',8,60,300,'本地OpenCode按需；含新闻与加工审批共享预算') ON CONFLICT(service) DO NOTHING`;
  for(const id of ids) console.log(JSON.stringify(await processReview(id)));
} finally {closeMcode();await closeDb();}
