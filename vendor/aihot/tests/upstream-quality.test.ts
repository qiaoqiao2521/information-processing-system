import { tag } from './setup.ts';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { after, test } from 'node:test';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { sql, closeDb } from '@aihot/backend/db';
import { MCODE_PREFIX } from '../packages/backend/src/providers/mcode-stdio.ts';
const dir=await mkdtemp(join(tmpdir(),'quality-test-'));
after(async()=>{await rm(dir,{recursive:true,force:true});await closeDb();});
test('two local calls publish only a passing draft and retain failed reviews without automatic retry',async()=>{
 const suffix=tag();const approved='quality-good-'+suffix;const held='quality-hold-'+suffix;
 const items=Object.fromEntries([approved,held].map((id,i)=>[id,{id,title:i?'未证实消息':'有条件的材料解读',summary:'原始材料明确说明某项功能的适用范围和限制，不提供真实测评。判断应局限于所附引用，不把推测写成事实。',
  links:{aihot:'https://aihot.news/items/'+id,original:'https://example.com/'+id},attribution:{name:'AIHOT',url:'https://aihot.news/items/'+id},
  category:'industry',score:80,selected:true,publishedAt:new Date(Date.now()-i*1000).toISOString(),source:{name:'test'}}]));
 const cache=join(dir,'snapshot.json');await writeFile(cache,JSON.stringify({checkedAt:new Date().toISOString(),complete:true,items,removed:[]}));
 await sql`INSERT INTO budgets(service,per_minute,per_hour,per_day) VALUES('opencode',1000,1000,1000) ON CONFLICT(service) DO UPDATE SET per_minute=1000,per_hour=1000,per_day=1000`;
 async function execute(changeDuringReview=false) {
  const child=spawn(process.execPath,['scripts/process-upstream-batch.ts','--next','2'],{env:{...process.env,UPSTREAM_REVIEW_CACHE:cache,MCODE_STDIO_ENABLED:'true',LOCAL_CLI_PROVIDER:'opencode',MODEL_CALLS_ENABLED:'true'}});
  let calls=0;let stderr='';child.stderr.on('data',data=>{stderr+=String(data);});
  const lines=createInterface({input:child.stdout});
  lines.on('line',line=>{if(!line.startsWith(MCODE_PREFIX))return;
   calls++;const frame=JSON.parse(line.slice(MCODE_PREFIX.length));
   const input=JSON.parse(frame.body.messages.find((m:{role:string})=>m.role==='user').content);
   const value=input.draft ? {decision:input.source.id===held?'hold':'approve',factsSupported:input.source.id!==held,addedValue:true,duplicate:false,reason:'引用支持与条件分析检查；不声称独立核实原文。'} :
    {title:'基于材料的有条件解读',summary:'根据所附引用整理适用条件，不声称已核实原文或进行实际测试。',analysis:'材料的价值在于揭示了特定使用情景的边界，是否适用于读者还取决于开放范围。若实际条件不同，应先对照原始来源核实，再决定是否采用。',uncertainties:'实际开放范围未独立核实。'};
   const respond=()=>child.stdin.write(JSON.stringify({id:frame.id,response:{choices:[{message:{content:JSON.stringify(value)}}],usage:{total_tokens:20}}})+'\n');
   if(input.draft && changeDuringReview) sql`UPDATE upstream_reviews SET version=version+1 WHERE id=${input.source.id}`.then(respond);else respond();
  });
  const code=await new Promise(resolve=>child.on('close',resolve));return {code,calls,stderr};
 }
 await sql`UPDATE budgets SET per_day=0 WHERE service='opencode'`;
 const paused=await execute();assert.equal(paused.code,0,paused.stderr);assert.equal(paused.calls,0);
 await sql`UPDATE budgets SET per_day=1000 WHERE service='opencode'`;
 const run=await execute();assert.equal(run.code,0,run.stderr);assert.equal(run.calls,4);
 const rows=await sql`SELECT id,status FROM upstream_reviews WHERE id IN ${sql([approved,held])} ORDER BY id`;
 assert.equal(rows.find(r=>r.id===approved)!.status,'approved');assert.equal(rows.find(r=>r.id===held)!.status,'draft');
 assert.equal((await sql`SELECT visibility FROM publications WHERE article_id=${'review-'+approved}`)[0]!.visibility,'public');
 assert.equal((await sql`SELECT * FROM publications WHERE article_id=${'review-'+held}`).length,0);
 assert.equal((await sql`SELECT * FROM receipts WHERE subject IN ${sql([approved,held])} AND status='completed'`).length,4);
 const repeat=await execute();assert.equal(repeat.calls,0);assert.equal(repeat.code,0,repeat.stderr);
 const drift='quality-drift-'+suffix;
 items[drift]={...items[approved]!,id:drift,links:{aihot:'https://aihot.news/items/'+drift,original:'https://example.com/'+drift}};
 await writeFile(cache,JSON.stringify({checkedAt:new Date().toISOString(),complete:true,items,removed:[]}));
 const changed=await execute(true);assert.equal(changed.calls,2);assert.equal(changed.code,1);
 assert.equal((await sql`SELECT status FROM upstream_reviews WHERE id=${drift}`)[0]!.status,'draft');
 assert.equal((await sql`SELECT * FROM publications WHERE article_id=${'review-'+drift}`).length,0);
});
