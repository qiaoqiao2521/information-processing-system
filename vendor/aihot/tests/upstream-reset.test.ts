import "./setup.ts";
import assert from "node:assert/strict";
import { after, test } from "node:test";
import { sql, closeDb } from "@aihot/backend/db";
import { readUpstreamReset, refreshUpstreamReset, validateUpstreamReset, UPSTREAM_RESET_URL } from "@aihot/backend/monitor/upstream";
import type { guardedFetch } from "@aihot/backend/lib/http-fetch";
import { codexResetsSnapshot, codexResetVersion } from "@aihot/backend/monitor/read";
const value = { schemaVersion: 1, timezone: "Asia/Shanghai", today: "2026-10-01", checkedAt: new Date().toISOString(),
  historyFrom: "2026-06-12T00:00:00+08:00", count: 0, events: [], activities: [], monitor: null, outage: null };
const response = (status: number, body: unknown = value) => ({ status, url: UPSTREAM_RESET_URL, headers: new Headers({ etag: 'W/"test"' }),
  body: Buffer.from(JSON.stringify(body)), text: () => JSON.stringify(body) });
after(async () => { delete process.env.CODEX_RESET_UPSTREAM_ENABLED; await sql`DELETE FROM settings WHERE key = 'monitor.upstream'`; await closeDb(); });
test("public-result mirror validates, conditionally refreshes, and retains last good data", async () => {
  process.env.CODEX_RESET_UPSTREAM_ENABLED = "true";
  process.env.COLLECT_ENABLED = "true";
  await sql`DELETE FROM settings WHERE key = 'monitor.upstream'`;
  assert.throws(() => validateUpstreamReset({ ...value, schemaVersion: 2 }));
  assert.throws(() => validateUpstreamReset({ ...value, count: 1 }));
  let calls = 0;
  const fetcher: typeof guardedFetch = async (url, opts) => {
    calls++;
    assert.equal(url, UPSTREAM_RESET_URL);
    assert.equal(opts?.maxBytes, 4 * 1024 * 1024);
    assert.equal(opts?.headers?.["If-None-Match"], calls === 1 ? undefined : 'W/"test"');
    return response(calls === 1 ? 200 : 304);
  };
  await refreshUpstreamReset(fetcher);
  const first = await readUpstreamReset();
  assert.equal(first.upstream.stale, false);
  assert.equal((await refreshUpstreamReset(fetcher) as {status: number}).status, 304);
  assert.deepEqual((await codexResetsSnapshot()).events, []);
  assert.match((await codexResetVersion(Date.now() + 46 * 60_000)).version, /-stale$/);
  assert.equal((await readUpstreamReset(Date.now() + 46 * 60_000)).upstream.stale, true);
  for (const bad of [response(503), response(200, { ...value, count: 1 })]) {
    await assert.rejects(refreshUpstreamReset(async () => bad));
    assert.deepEqual((await readUpstreamReset()).events, first.events);
  }
  process.env.COLLECT_ENABLED = "false";
  await refreshUpstreamReset(async () => { throw new Error("disabled collection must not fetch"); });
});
