import { tag } from "./setup.ts";
import assert from "node:assert/strict";
import http from "node:http";
import { spawnSync } from "node:child_process";
import { after, before, test } from "node:test";
import { config } from "@aihot/backend/config";
import { sql, closeDb } from "@aihot/backend/db";
import { upsertMaterial } from "@aihot/backend/content/materials";
import { confirmedXBody, readKnownXBody } from "@aihot/backend/content/x-reader";
import { assertJinaTarget, jinaRead, xPostId } from "@aihot/backend/providers/jina";

const T = tag();
const sourceId = `test-jina-x-${T}`;
const postUrl = `https://x.com/example/status/${Date.now()}`;
const loginUrl = `https://x.com/example/status/${Date.now() + 1}`;
const text = "A complete public post about a new development tool, with its original context and a link https://example.org/release.";
const page = (url = postUrl, markdown = `# Example on X: "${text}"`) => ({ title: "Example on X", url, publishedTime: null, markdown });
let hits = 0;
let tokenHeader: string | undefined;
let savedBudget: Array<{ per_minute: number; per_hour: number; per_day: number }> = [];
const server = http.createServer((req, res) => {
  hits += 1;
  tokenHeader = req.headers["x-token-budget"] as string | undefined;
  const target = (req.url ?? "").slice(1);
  const markdown = target === loginUrl ? "# Log in to X\n\nContinue with Google" : `# Example on X: "${text}"\n\n## Log in or sign up\n\nUnrelated reply text`;
  res.writeHead(200, { "content-type": "text/plain", "x-usage-tokens": "50" });
  res.end(`Title: Example on X\nURL Source: ${target}\nMarkdown Content:\n${markdown}`);
});

before(async () => {
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  process.env.JINA_BASE_URL = `http://127.0.0.1:${(server.address() as { port: number }).port}`;
  process.env.JINA_API_KEY = "test-key";
  process.env.JINA_SCOPE = "x";
  process.env.JINA_BODY_FALLBACK = "false";
  process.env.JINA_MAX_TOKENS_PER_REQUEST = "10000";
  config.allowPrivateNetworkFetch = true;
  savedBudget = await sql`SELECT per_minute, per_hour, per_day FROM budgets WHERE service = 'jina'`;
  await sql`UPDATE budgets SET per_minute = 1000, per_hour = 1000, per_day = 1000 WHERE service = 'jina'`;
  await sql`INSERT INTO sources (id, name, kind, config, tier, participation_mode)
    VALUES (${sourceId}, ${sourceId}, 'external', '{}', 'T2', 'editorial')`;
});
after(async () => {
  for (const b of savedBudget) await sql`UPDATE budgets SET per_minute = ${b.per_minute}, per_hour = ${b.per_hour}, per_day = ${b.per_day} WHERE service = 'jina'`;
  await new Promise<void>((resolve) => server.close(() => resolve()));
  await closeDb();
});

test("X scope accepts individual HTTPS posts and refuses searches, timelines and URL disguises", () => {
  for (const url of [postUrl, "https://twitter.com/example/status/123?s=20", "https://mobile.twitter.com/example/status/123", "https://x.com/i/status/123"]) {
    assert.ok(xPostId(url));
    assert.doesNotThrow(() => assertJinaTarget(url, "x"));
  }
  for (const url of ["https://example.org/news", "https://x.com/search?q=ai", "https://x.com/example", "https://x.com/i/flow/login", "https://x.com.evil.org/example/status/123", "https://x.com@evil.org/example/status/123", "https://user@x.com/example/status/123", "http://x.com/example/status/123", "https://x.com:444/example/status/123", "https://x.com/example/status/123/photo/1"]) {
    assert.equal(xPostId(url), null);
    assert.throws(() => assertJinaTarget(url, "x"), /only HTTPS X/);
  }
  assert.throws(() => assertJinaTarget(postUrl, "typo"), /must be x or all/);
});

test("denied targets and malformed token limits create no receipt or network attempt", async () => {
  const before = await sql`SELECT count(*) AS count FROM receipts WHERE service = 'jina'`;
  await assert.rejects(jinaRead("https://example.org/news", { purpose: T, subject: T }), /only HTTPS X/);
  process.env.JINA_MAX_TOKENS_PER_REQUEST = "10000junk";
  await assert.rejects(jinaRead(postUrl, { purpose: T, subject: T }), /positive integer/);
  process.env.JINA_MAX_TOKENS_PER_REQUEST = "10000";
  assert.deepEqual(await sql`SELECT count(*) AS count FROM receipts WHERE service = 'jina'`, before);
  assert.equal(hits, 0);
});

test("only the matching post heading is content; login/replies, another post and truncation are unconfirmed", () => {
  const reference = text.slice(0, 70) + "…";
  assert.equal(confirmedXBody(page(postUrl, `## Post\n\nLog in\n\n# Example on X: "${text}"\n\n## Replies\n\nNoise`), postUrl, reference), text);
  assert.equal(confirmedXBody(page(loginUrl), postUrl, reference), null);
  assert.equal(confirmedXBody(page(postUrl, "# Log in to X\n\n" + text), postUrl, reference), null);
  assert.equal(confirmedXBody(page(), postUrl, "An unrelated search result with sufficient characters"), null);
  assert.equal(confirmedXBody(page(postUrl, `# Example on X: "${text}…"`), postUrl, reference), null);
});

test("on-demand enrichment keeps dates, summary and processing state; repeated reads buy no request", async () => {
  const result = await upsertMaterial({ sourceId, url: postUrl, title: text.slice(0, 70), excerpt: text.slice(0, 85) + "…", via: "import",
    publishedAt: new Date("2026-09-25T12:00:00Z"), discoveredAt: new Date("2026-09-26T12:00:00Z"), backfill: "hub-migration", bodyStatus: "unconfirmed" });
  await sql`UPDATE articles SET processing_state = 'skipped' WHERE id = ${result.articleId}`;
  const snapshot = () => sql`SELECT published_at, discovered_at, timeline_at, excerpt, title, processing_state, processing_queued_at FROM articles WHERE id = ${result.articleId}`;
  const before = await snapshot();
  assert.equal((await readKnownXBody(result.articleId)).status, "ok");
  assert.deepEqual(await snapshot(), before);
  const [stored] = await sql`SELECT body_text, body_html, revision FROM articles WHERE id = ${result.articleId}`;
  assert.equal(stored!.body_text, text);
  assert.equal(stored!.body_html, `<p>${text}</p>`);
  assert.equal(stored!.revision, 2);
  assert.equal(tokenHeader, "10000", "the token cap is sent to the provider, not applied after billing");
  assert.equal((await readKnownXBody(result.articleId)).status, "skipped");
  assert.equal(hits, 1);
});

test("a login-only response keeps the stored snippet and reuses its receipt without retrying", async () => {
  const result = await upsertMaterial({ sourceId, url: loginUrl, title: text, excerpt: text, via: "import", bodyStatus: "unconfirmed" });
  assert.equal((await readKnownXBody(result.articleId)).status, "unconfirmed");
  assert.equal((await readKnownXBody(result.articleId)).status, "unconfirmed");
  const [stored] = await sql`SELECT body_text, body_status, excerpt FROM articles WHERE id = ${result.articleId}`;
  assert.equal(stored!.body_text, null);
  assert.equal(stored!.excerpt, text);
  assert.equal(stored!.body_status, "unconfirmed");
  assert.equal(hits, 2);
});

test("budget CLI caps Jina independently, refuses unsafe allowances and resets omitted services", async () => {
  const original = await sql<{ service: string; per_minute: number; per_hour: number; per_day: number; note: string | null }[]>`
    SELECT service, per_minute, per_hour, per_day, note FROM budgets ORDER BY service`;
  const run = (args: string[], env = process.env) => spawnSync(process.execPath, ["scripts/muqiao-budget.ts", ...args], { env, encoding: "utf8", timeout: 15_000 });
  try {
    assert.notEqual(run(["--jina-x-cap", "51"]).status, 0);
    assert.notEqual(run(["--jina-x-cap", "50"], { ...process.env, JINA_SCOPE: "all" }).status, 0);
    assert.notEqual(run(["--jina-x-cap", "50"], { ...process.env, JINA_BODY_FALLBACK: "true" }).status, 0);
    assert.deepEqual(await sql`SELECT service, per_minute, per_hour, per_day, note FROM budgets ORDER BY service`, original);
    const opened = run(["--daily-cap", "300", "--jina-x-cap", "50"]);
    assert.equal(opened.status, 0, opened.stderr);
    assert.deepEqual(JSON.parse(opened.stdout), { modelAttemptsPer24h: 300, jinaXAttemptsPer24h: 50, otherPaidServices: 0 });
    const rows = await sql`SELECT service, per_minute, per_hour, per_day FROM budgets ORDER BY service`;
    assert.deepEqual(rows.find((r) => r.service === "jina"), { service: "jina", per_minute: 1, per_hour: 10, per_day: 50 });
    assert.equal(rows.find((r) => r.service === "llm")!.per_day, 300);
    assert.ok(rows.filter((r) => !["jina", "llm"].includes(r.service)).every((r) => r.per_day === 0));
    assert.equal(run([]).status, 0);
    assert.ok((await sql`SELECT per_minute, per_hour, per_day FROM budgets`).every((r) => r.per_minute === 0 && r.per_hour === 0 && r.per_day === 0));
  } finally {
    for (const b of original) await sql`UPDATE budgets SET per_minute = ${b.per_minute}, per_hour = ${b.per_hour}, per_day = ${b.per_day}, note = ${b.note} WHERE service = ${b.service}`;
  }
});
