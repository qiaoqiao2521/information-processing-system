import { tag } from "./setup.ts";
import assert from "node:assert/strict";
import http from "node:http";
import { before, after, test } from "node:test";
import { sql, closeDb } from "@aihot/backend/db";
import { config } from "@aihot/backend/config";
import { upsertMaterial } from "@aihot/backend/content/materials";
import { publishArticle } from "@aihot/backend/publication/publish";
import { queueProcessing, processArticle } from "@aihot/backend/jobs/content";
import { stopBoss } from "@aihot/backend/jobs/queue";
import { collectSource } from "@aihot/backend/sources/collect";

const T = tag();
const official = `test-official-${T}`;
const personal = `test-personal-${T}`;
let server: http.Server;
before(async () => {
  process.env.PROCESS_HISTORY_ENABLED = "false";
  await sql`INSERT INTO sources (id, name, kind, config, tier, first_party, participation_mode)
    VALUES (${official}, 'Official', 'rss', ${sql.json({ _aihot: { publishPending: true } })}, 'T1', true, 'editorial'),
           (${personal}, 'Personal', 'rss', ${sql.json({ _aihot: { publishPending: true } })}, 'T2', false, 'editorial')`;
});
after(async () => {
  if (server) await new Promise<void>((resolve) => server.close(() => resolve()));
  await stopBoss();
  await closeDb();
});

test("opted-in official pending news is readable without fake analysis, scores or selection", async () => {
  const { articleId } = await upsertMaterial({ sourceId: official, url: `https://example.org/${T}/release`, title: "Introducing a frontier model", excerpt: "Original publisher summary", via: "fetch", publishedAt: new Date() });
  await publishArticle(articleId);
  const [p] = await sql`SELECT eligible, selected, score, tags, title, summary, analysis_id FROM publications WHERE article_id = ${articleId}`;
  assert.deepEqual(p, { eligible: true, selected: false, score: null, tags: ["待AI处理"], title: "Introducing a frontier model", summary: "Original publisher summary", analysis_id: null });
  assert.equal((await sql`SELECT count(*) AS n FROM selected_ledger WHERE article_id = ${articleId}`)[0]!.n, 0);
  await sql`INSERT INTO analyses (article_id, input_revision, origin, relevance) VALUES (${articleId}, 1, 'rule', 'block')`;
  await publishArticle(articleId);
  const [blocked] = await sql`SELECT eligible, tags FROM publications WHERE article_id = ${articleId}`;
  assert.equal(blocked!.eligible, false, "pending fallback cannot undo an actual judgement");
  assert.ok(!blocked!.tags.includes("待AI处理"));
  const other = await upsertMaterial({ sourceId: personal, url: `https://example.org/${T}/personal`, title: "Personal pending post", excerpt: "Excerpt", via: "fetch" });
  await publishArticle(other.articleId);
  assert.equal((await sql`SELECT eligible FROM publications WHERE article_id = ${other.articleId}`)[0]!.eligible, false);
});

test("queued history is paused before model calls, while recent first-import news still routes", async () => {
  const old = await upsertMaterial({ sourceId: official, url: `https://example.org/${T}/old`, title: "Historical post", excerpt: "Excerpt", via: "fetch", backfill: "first-import", publishedAt: new Date(Date.now() - 10 * 86400000) });
  const before = (await sql`SELECT count(*) AS n FROM receipt_attempts`)[0]!.n;
  assert.equal(await queueProcessing(old.articleId), null);
  assert.deepEqual(await processArticle(old.articleId), { state: "history-paused" });
  assert.equal((await sql`SELECT count(*) AS n FROM receipt_attempts`)[0]!.n, before);
  const fresh = await upsertMaterial({ sourceId: official, url: `https://example.org/${T}/new`, title: "Recent post", bodyText: "Confirmed body", bodyStatus: "ok", via: "fetch", backfill: "first-import", publishedAt: new Date() });
  assert.ok(await queueProcessing(fresh.articleId));
});

test("RSS import chooses newest entries before its limit and publishes pending official entries", async () => {
  server = http.createServer((_req, res) => {
    res.writeHead(200, { "content-type": "application/rss+xml" });
    res.end(`<rss><channel>${[5, 3, 0].map((days) => `<item><title>Item ${days}</title><link>https://example.org/${T}/rss-${days}</link><description>Publisher excerpt ${days}</description><pubDate>${new Date(Date.now() - days * 86400000 - 3600000).toUTCString()}</pubDate></item>`).join("")}</channel></rss>`);
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  config.allowPrivateNetworkFetch = true;
  const id = `test-official-rss-${T}`;
  await sql`INSERT INTO sources (id, name, kind, config, tier, first_party, participation_mode)
    VALUES (${id}, 'Official RSS', 'rss', ${sql.json({ feedUrl: `http://127.0.0.1:${(server.address() as { port: number }).port}`, _aihot: { initialBackfillLimit: 1, publishPending: true } })}, 'T1', true, 'editorial')`;
  assert.equal((await collectSource(id, { force: true })).status, "ok");
  const rows = await sql`SELECT a.title, p.eligible, p.score FROM articles a JOIN publications p ON p.article_id=a.id WHERE a.source_id=${id}`;
  assert.deepEqual([...rows], [{ title: "Item 0", eligible: true, score: null }]);
});
