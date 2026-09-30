// Explicit launch budget: new deployments start with every paid service stopped.
// Validation may temporarily allow at most 40 model attempts, then this script closes it again.
import { closeDb, sql } from "@aihot/backend/db";
const validating = process.argv.includes("--validate");
const capIndex = process.argv.indexOf("--daily-cap");
const productionCap = capIndex >= 0 ? Number(process.argv[capIndex + 1]) : 0;
if (capIndex >= 0 && (!Number.isInteger(productionCap) || productionCap < 1 || productionCap > 300 || validating)) {
  throw new Error("--daily-cap must be an integer from 1 to 300, without --validate");
}
const perDay = productionCap || (validating ? 40 : 0);
const note = productionCap ? `用户批准常态限额：连续24小时最多${productionCap}次模型请求` : validating ? '用户授权限量验证，最多40次尝试' : '模型处理暂停';
await sql`UPDATE budgets SET per_minute = 0, per_hour = 0, per_day = 0, note = '木乔：付费服务默认暂停', updated_at = now()`;
await sql`UPDATE budgets SET per_minute = ${perDay ? 8 : 0}, per_hour = ${productionCap ? 60 : validating ? 40 : 0},
  per_day = ${perDay}, note = ${note}, updated_at = now() WHERE service = 'llm'`;
console.log(JSON.stringify({ modelAttemptsPer24h: perDay, otherPaidServices: 0 }));
await closeDb();
