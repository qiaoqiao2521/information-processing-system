import { tag } from "./setup.ts";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { after, test } from "node:test";
import { sql, closeDb } from "@aihot/backend/db";
import { MCODE_PREFIX } from "../packages/backend/src/providers/mcode-stdio.ts";

after(closeDb);
test("local model uses its own budget and durable receipt, and reuses the saved answer", async () => {
  for (const [modelKey, service] of [["local-mcode", "mcode"], ["local-opencode", "opencode"]] as const) {
  const subject = `mcode-test-${tag()}`;
  await sql`INSERT INTO budgets (service, per_minute, per_hour, per_day) VALUES (${service}, 0, 0, 0)
    ON CONFLICT (service) DO UPDATE SET per_minute=0, per_hour=0, per_day=0`;
  const source = `
    import {chatJson} from '@aihot/backend/providers/llm';
    import {closeMcode} from './packages/backend/src/providers/mcode-stdio.ts';
    import {closeDb} from '@aihot/backend/db';
    import {z} from 'zod';
    try { const opts={model:${JSON.stringify(modelKey)},purpose:'test_local',subject:${JSON.stringify(subject)},promptVersion:'test',system:'test',user:'test',schema:z.object({value:z.number()})};
      const a=await chatJson(opts); const b=await chatJson(opts);
      console.log(JSON.stringify({result:a.data,reused:b.reused,receiptId:a.receiptId}));
    } catch(e) { console.log(JSON.stringify({error:e.message})); }
    finally {closeMcode();await closeDb();}`;
  async function execute() {
    const child = spawn(process.execPath, ["--input-type=module", "-e", source], {
      env: { ...process.env, MCODE_STDIO_ENABLED: "true", MODEL_CALLS_ENABLED: "true", LLM_BASE_URL: "http://127.0.0.1:1", LLM_API_KEY: "test-no-fallback" },
    });
    let calls = 0; let final: { error?: string; result?: { value: number }; reused?: boolean } = {};
    let stderr = ""; child.stderr.on("data", (b) => { stderr += String(b); });
    const lines = createInterface({ input: child.stdout });
    lines.on("line", (line) => {
      if (line.startsWith(MCODE_PREFIX)) {
        calls++; const request = JSON.parse(line.slice(MCODE_PREFIX.length));
        child.stdin.write(JSON.stringify({ id: request.id, response: { choices: [{ message: { content: '{"value":42}' } }], usage: { total_tokens: 10 } } }) + "\n");
      } else final = JSON.parse(line);
    });
    const code = await new Promise((resolve) => child.on("close", resolve));
    assert.equal(code, 0, stderr); return { calls, final };
  }
  const stopped = await execute();
  assert.equal(stopped.calls, 0); assert.match(stopped.final.error!, new RegExp(`Budget for ${service} exhausted`));
  await sql`UPDATE budgets SET per_minute=100,per_hour=100,per_day=100 WHERE service=${service}`;
  const completed = await execute();
  assert.equal(completed.calls, 1); assert.deepEqual(completed.final.result, { value: 42 }); assert.equal(completed.final.reused, true);
  const [row] = await sql`SELECT service, status, response FROM receipts WHERE subject=${subject}`;
  assert.equal(row!.service, service); assert.equal(row!.status, "received");
  assert.equal((await sql`SELECT count(*) AS n FROM receipt_attempts WHERE receipt_id IN (SELECT id FROM receipts WHERE subject=${subject})`)[0]!.n, 1);
  }
});
