// A mobile sync may lose its response. Replaying it must retain one private draft.
import "./setup.ts";
import assert from "node:assert/strict";
import { createHash, randomUUID } from "node:crypto";
import { after, test } from "node:test";
import { buildApp } from "../apps/api/src/app.ts";
import { config } from "@aihot/backend/config";
import { closeDb, sql } from "@aihot/backend/db";

const token = "lifegame-sync-test-token-0123456789";
const previousToken = process.env.LIFEGAME_SITE_SYNC_TOKEN;
const previousAdmin = config.devAdmin;
const previousPassword = config.adminPassword;
process.env.LIFEGAME_SITE_SYNC_TOKEN = token;
config.devAdmin = null;
config.adminPassword = "lifegame-test-admin-password";
const app = await buildApp();
const endpoint = "/api/integrations/lifegame/distillations";

function draft() {
  const request_id = randomUUID();
  const item_id = `lifegame-${request_id}`;
  return {
    request_id, item_id, title: "LifeGame 私有整理", source: "公开测试信源",
    source_url: `https://intel.muqiao.xyz/items/${item_id}`,
    fingerprint: "a".repeat(64), basis: "public_summary", truncated: false,
    model: "MiniMax-M3.1-Flash-Preview", conclusion: "所附摘要说明了一个公开变化。",
    key_points: ["第一条看点", "第二条看点", "第三条看点"], entities: ["MiniMax"],
  };
}

function push(payload: unknown, authorization: string | undefined = `Bearer ${token}`) {
  return app.inject({ method: "POST", url: endpoint, payload: JSON.stringify(payload),
    headers: { "content-type": "application/json", ...(authorization ? { authorization } : {}) } });
}

after(async () => {
  await app.close();
  await closeDb();
  config.devAdmin = previousAdmin;
  config.adminPassword = previousPassword;
  if (previousToken === undefined) delete process.env.LIFEGAME_SITE_SYNC_TOKEN;
  else process.env.LIFEGAME_SITE_SYNC_TOKEN = previousToken;
});

test("a lost-response replay and concurrent submissions return the same single draft", async () => {
  const payload = draft();
  const responses = await Promise.all(Array.from({ length: 5 }, () => push(payload)));
  const expected = { id: createHash("sha256").update(payload.request_id).digest("hex").slice(0, 24), request_id: payload.request_id, status: "draft" };
  for (const response of responses) {
    assert.equal(response.statusCode, 200, response.body);
    assert.deepEqual(response.json(), expected);
    assert.equal(response.headers["cache-control"], "no-store");
  }
  const rows = await sql`SELECT * FROM lifegame_distillations WHERE request_id=${payload.request_id}`;
  assert.equal(rows.length, 1);
  assert.equal(rows[0]!.status, "draft");
  assert.deepEqual(rows[0]!.key_points, payload.key_points);
  assert.equal((await sql`SELECT id FROM articles WHERE id=${payload.item_id}`).length, 0);
  assert.equal((await app.inject({ url: `/api/site/items/${payload.item_id}` })).statusCode, 404);
});

test("reusing a request ID with different content returns 409 and preserves the original", async () => {
  const payload = draft();
  assert.equal((await push(payload)).statusCode, 200);
  for (const changed of [{ conclusion: "不同结果" }, { fingerprint: "b".repeat(64) }, { key_points: ["变更", "第二条看点", "第三条看点"] }]) {
    assert.equal((await push({ ...payload, ...changed })).statusCode, 409);
  }
  const [row] = await sql`SELECT conclusion,fingerprint,key_points FROM lifegame_distillations WHERE request_id=${payload.request_id}`;
  assert.equal(row!.conclusion, payload.conclusion);
  assert.equal(row!.fingerprint, payload.fingerprint);
  assert.deepEqual(row!.key_points, payload.key_points);
});

test("UUID case differences replay the same request", async () => {
  const payload = draft();
  const first = await push(payload);
  const second = await push({ ...payload, request_id: payload.request_id.toUpperCase() });
  assert.equal(second.statusCode, 200, second.body);
  assert.deepEqual(first.json(), second.json());
});

test("missing, incorrect or disabled service tokens reject writes", async () => {
  const payload = draft();
  for (const authorization of [undefined, "Bearer incorrect", `Basic ${token}`]) {
    const response = await push(payload, authorization ?? "");
    assert.equal(response.statusCode, 401, response.body);
  }
  process.env.LIFEGAME_SITE_SYNC_TOKEN = "";
  try { assert.equal((await push(payload)).statusCode, 401); }
  finally { process.env.LIFEGAME_SITE_SYNC_TOKEN = token; }
  assert.equal((await sql`SELECT id FROM lifegame_distillations WHERE request_id=${payload.request_id}`).length, 0);
});

test("invalid metadata, arbitrary URLs, raw full text and oversized bodies do not write", async () => {
  const payload = draft();
  const invalid = [null, [], {}, { ...payload, text: "不得同步原文" },
    { ...payload, source_url: "https://example.org/article" },
    { ...payload, source_url: `${payload.source_url}?token=untrusted` },
    { ...payload, source_url: "https://intel.muqiao.xyz/items/different" },
    { ...payload, key_points: ["只有一条"] }, { ...payload, conclusion: " " },
    { ...payload, model: "different-model-3.1" }, { ...payload, fingerprint: "x".repeat(64) },
    { ...payload, status: "published" }, { ...payload, entities: Array(41).fill("entity") }];
  for (const body of invalid) {
    const response = await push(body);
    assert.equal(response.statusCode, 400, response.body);
  }
  assert.equal((await push({ ...payload, conclusion: "a".repeat(70_000) })).statusCode, 413);
  assert.equal((await sql`SELECT id FROM lifegame_distillations WHERE request_id=${payload.request_id}`).length, 0);
});

test("only a live admin session can read drafts; the sync token cannot read them", async () => {
  const payload = draft();
  assert.equal((await push(payload)).statusCode, 200);
  for (const headers of [{}, { authorization: `Bearer ${token}` }]) {
    const denied = await app.inject({ url: "/api/admin/lifegame-drafts", headers });
    assert.equal(denied.statusCode, 401, denied.body);
    assert.equal(denied.headers["cache-control"], "no-store");
    assert.equal(denied.body.includes(payload.conclusion), false);
  }
  const login = await app.inject({ method: "POST", url: "/api/auth/password", payload: { password: config.adminPassword, return: "/admin/lifegame" } });
  assert.equal(login.statusCode, 303, login.body);
  const cookie = String(login.headers["set-cookie"]).split(";")[0]!;
  const allowed = await app.inject({ url: "/api/admin/lifegame-drafts", headers: { cookie } });
  assert.equal(allowed.statusCode, 200, allowed.body);
  assert.equal(allowed.headers["cache-control"], "no-store");
  const row = allowed.json().rows.find((value: { request_id: string }) => value.request_id === payload.request_id);
  assert.equal(row.conclusion, payload.conclusion);
  assert.equal(row.status, "draft");
  assert.equal("text" in row, false);
});
