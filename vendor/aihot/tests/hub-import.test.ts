import { tag } from './setup.ts';
import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { closeDb, sql } from '@aihot/backend/db';
const run = promisify(execFile);
after(closeDb);

test('historic hub import preserves dates, publishes without model analysis and is idempotent', async () => {
  const t = tag();
  const source = `hub-import-${t}`;
  await sql`INSERT INTO sources (id, name, kind, participation_mode) VALUES (${source}, 'Migrated source', 'external', 'editorial')`;
  const directory = await mkdtemp(path.join(tmpdir(), 'hub-import-'));
  try {
    const file = path.join(directory, 'library.json');
    const item = { id: `hub-${t}`, sourceId: `import-${t}`, title: '旧站摘要', summary: '保留原日期', body: '',
      url: `https://example.org/hub-import/${t}`, publishedAt: '2026-09-26T00:00:00Z',
      collectedAt: '2026-09-30T08:00:00Z', author: '' };
    await writeFile(file, JSON.stringify({ items: [item] }));
    const first = await run(process.execPath, ['scripts/import-hub.ts', file]);
    assert.equal(JSON.parse(first.stdout.trim()).created, 1);
    const second = await run(process.execPath, ['scripts/import-hub.ts', file]);
    assert.equal(JSON.parse(second.stdout.trim()).created, 0);
    const [row] = await sql`SELECT p.published_at, p.discovered_at, p.timeline_at, p.score, p.selected,
      p.analysis_id, p.eligible, a.processing_state FROM publications p JOIN articles a ON a.id=p.article_id WHERE p.article_id=${item.id}`;
    assert.equal(row.published_at.toISOString(), '2026-09-26T00:00:00.000Z');
    assert.equal(row.discovered_at.toISOString(), '2026-09-30T08:00:00.000Z');
    assert.equal(row.timeline_at.toISOString(), '2026-09-26T00:00:00.000Z');
    assert.equal(row.score, null);
    assert.equal(row.analysis_id, null);
    assert.equal(row.selected, false);
    assert.equal(row.eligible, true);
    assert.equal(row.processing_state, 'skipped');
    const [alias] = await sql`SELECT value->>'articleId' AS id FROM settings WHERE key=${`hub.legacy.${item.id}`}`;
    assert.equal(alias.id, item.id);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
