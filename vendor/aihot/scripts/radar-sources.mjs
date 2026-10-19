// Narrow source reconciliation and pending indexes for the public API adapters.
// Uses the same source/ingest/publication contracts; never calls a model.
import { readFileSync } from 'node:fs';
import { sql, closeDb } from '@aihot/backend/db';
import { publishArticle } from '@aihot/backend/publication/publish';
import { stopBoss } from '@aihot/backend/jobs/queue';
const ids = ['hub-hacker-news', 'hub-github-releases', 'hub-oss-insight'];
const [mode, id] = process.argv.slice(2);
try {
  if (mode === '--seed' && !id) {
    const seeds = JSON.parse(readFileSync('industry/sources.json', 'utf8')).sources;
    await sql.begin(async tx => {
      for (const sourceId of ids) {
        const source = seeds.find(s => s.id === sourceId);
        if (!source || source.kind !== 'external' || source.participation_mode !== 'editorial') throw new Error('Invalid radar source seed');
        await tx`INSERT INTO sources(id,name,kind,config,tier,first_party,participation_mode,interval_minutes,enabled,tags,site_fulltext,syndicate_fulltext)
          VALUES(${source.id},${source.name},'external',${tx.json(source.config)},${source.tier},${source.first_party ?? false},'editorial',120,true,${source.tags},false,false)
          ON CONFLICT(id) DO NOTHING`;
      }
      // The old default name only; preserve administrator configuration and paused sources.
      await tx`UPDATE sources SET name='Hacker News · 讨论' WHERE id='hub-hacker-news' AND name='Hacker News'`;
    });
    console.log(JSON.stringify({sources: await sql`SELECT id,name,enabled,first_party,participation_mode FROM sources WHERE id IN ${sql(ids)}`}));
  } else if (mode === '--publish' && id === 'hub-github-releases') {
    const [source] = await sql`SELECT id FROM sources WHERE id=${id} AND enabled AND first_party
      AND kind='external' AND participation_mode='editorial' AND config->'_aihot'->>'publishPending'='true'`;
    if (!source) throw new Error('Release source paused or pending publication disabled');
    const rows = await sql`SELECT a.id FROM articles a LEFT JOIN publications p ON p.article_id=a.id
      WHERE a.source_id=${id} AND p.article_id IS NULL`;
    for (const row of rows) await publishArticle(row.id);
    console.log(JSON.stringify({sourceId: id, newlyIndexed: rows.length}));
  } else throw new Error('Use --seed or --publish hub-github-releases');
} finally { await stopBoss(); await closeDb(); }
