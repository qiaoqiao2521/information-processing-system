import { tag } from './setup.ts';
import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { sql, closeDb } from '@aihot/backend/db';
import { nextNativeArticles, recordNativeOutcome } from '@aihot/backend/editorial/workflow';
import { relatedReviewArticles } from '@aihot/backend/admin/upstream-reviews';
const suffix=tag(), source='workflow-'+suffix;
after(closeDb);
async function article(label:string) {
  const id=label+'-'+suffix;
  await sql`INSERT INTO articles(id,source_id,identity_key,url,title,excerpt,discovered_at,published_at,timeline_at)
    VALUES(${id},${source},${'https://example.com/'+id},${'https://example.com/'+id},'Claude recreates Adobe applications','公开材料中的功能说明',now(),now(),now())`;
  return id;
}
test('workflow selects own subscriptions but excludes history, human edits, paused sources and failed requests',async()=>{
  await sql`INSERT INTO sources(id,name,kind,first_party) VALUES(${source},'Own feed','rss',true)`;
  const good=await article('good'),old=await article('old'),baseline=await article('baseline'),failed=await article('failed'),manual=await article('manual');
  await sql`UPDATE articles SET published_at=now()-interval '8 days' WHERE id=${old}`;
  await sql`UPDATE articles SET backfill=true WHERE id=${baseline}`;
  await sql`INSERT INTO receipts(logical_key,service,subject,purpose,status) VALUES(${failed},'opencode',${'article:'+failed+'@1'},'prefilter_article','unknown')`;
  await sql`INSERT INTO editorial_overrides(article_id,updated_by,reason) VALUES(${manual},'human','Keep existing decision')`;
  const selected=await nextNativeArticles(10);
  assert.ok(selected.includes(good));
  for(const id of [old,baseline,failed,manual]) assert.ok(!selected.includes(id));
  await sql`UPDATE sources SET enabled=false WHERE id=${source}`;
  assert.ok(!(await nextNativeArticles(10)).includes(good));
  await sql`UPDATE sources SET enabled=true WHERE id=${source}`;
  await sql`UPDATE articles SET processing_state='analyzed' WHERE id=${good}`;
  await recordNativeOutcome(good,'pause');
  assert.ok((await nextNativeArticles(10)).includes(good),'budget-paused grouping can resume');
  await recordNativeOutcome(good,'complete');
  assert.ok(!(await nextNativeArticles(10)).includes(good));
});
test('event recall finds a translated report through its original title and excludes withdrawn copy',async()=>{
  const id=await article('translated');
  await sql`INSERT INTO publications(article_id,title,summary,eligible,source_id,channel,url,discovered_at,timeline_at,sort_at)
    VALUES(${id},'专业创作工具替代方案的条件','某工具替代方案的实际兼容性仍需验证',true,${source},'news',${'https://example.com/'+id},now(),now(),now())`;
  const material={id:'candidate',title:'Claude recreates Adobe applications',summary:'Original English account of the same launch.',
    links:{aihot:'https://aihot.news/items/candidate',original:'https://example.com/different-url'},attribution:{name:'AIHOT',url:'https://aihot.news/'},
    source:{name:'Test'},category:'opinion',score:80,selected:true,publishedAt:new Date().toISOString()};
  const draft={title:'大模型重新编写软件引起讨论',summary:'根据新材料评估不同的创作工作流',analysis:'该分析讨论兼容性与迁移条件，没有新增真实测试结论。',uncertainties:'未实测'};
  assert.ok((await relatedReviewArticles(material,draft)).some(row=>row.article_id===id));
  assert.ok(!(await relatedReviewArticles(material,draft,id)).some(row=>row.article_id===id));
  await sql`UPDATE publications SET visibility='withdrawn' WHERE article_id=${id}`;
  assert.ok(!(await relatedReviewArticles(material,draft)).some(row=>row.article_id===id));
});
