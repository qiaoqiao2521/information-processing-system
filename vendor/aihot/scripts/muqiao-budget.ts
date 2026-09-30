// Explicit launch budget: new deployments start with every paid service stopped.
// Model and X-only Jina allowances are explicit and independent; omitted services stay stopped.
import { closeDb, sql } from "@aihot/backend/db";
const validating = process.argv.includes("--validate");
const capIndex = process.argv.indexOf("--daily-cap");
const productionCap = capIndex >= 0 ? Number(process.argv[capIndex + 1]) : 0;
const jinaIndex = process.argv.indexOf("--jina-x-cap");
const jinaCap = jinaIndex >= 0 ? Number(process.argv[jinaIndex + 1]) : 0;
if (capIndex >= 0 && (!Number.isInteger(productionCap) || productionCap < 1 || productionCap > 300 || validating)) {
  throw new Error("--daily-cap must be an integer from 1 to 300, without --validate");
}
if (jinaIndex >= 0 && (!Number.isInteger(jinaCap) || jinaCap < 1 || jinaCap > 50 || process.env.JINA_SCOPE !== "x" || process.env.JINA_BODY_FALLBACK !== "false")) {
  throw new Error("--jina-x-cap requires 1–50, JINA_SCOPE=x and JINA_BODY_FALLBACK=false");
}
const perDay = productionCap || (validating ? 40 : 0);
const note = productionCap ? `用户批准常态限额：连续24小时最多${productionCap}次模型请求` : validating ? '用户授权限量验证，最多40次尝试' : '模型处理暂停';
try {
  await sql.begin(async (tx) => {
    await tx`UPDATE budgets SET per_minute = 0, per_hour = 0, per_day = 0, note = '木乔：付费服务默认暂停', updated_at = now()`;
    await tx`UPDATE budgets SET per_minute = ${perDay ? 8 : 0}, per_hour = ${productionCap ? 60 : validating ? 40 : 0},
      per_day = ${perDay}, note = ${note}, updated_at = now() WHERE service = 'llm'`;
    if (jinaCap) await tx`UPDATE budgets SET per_minute = 1, per_hour = 10, per_day = ${jinaCap},
      note = ${`用户批准：仅X原帖正文，连续24小时最多${jinaCap}次；不搜索`}, updated_at = now() WHERE service = 'jina'`;
  });
  console.log(JSON.stringify({ modelAttemptsPer24h: perDay, jinaXAttemptsPer24h: jinaCap, otherPaidServices: 0 }));
} finally { await closeDb(); }
