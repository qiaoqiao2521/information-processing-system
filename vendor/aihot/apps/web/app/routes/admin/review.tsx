import { useState } from 'react';
import { Link } from 'react-router';
import type { Route } from './+types/review';
import { adminGet } from '../../lib/admin.server';
import { useAdminAction } from '../../features/admin/action';
import { AdminPage, Badge, Button, Card, Input } from '../../features/admin/ui';
import { toast } from '../../features/admin/toast';
import { STATUS, type ReviewRow } from './reviews';
interface Detail {row:ReviewRow;current:ReviewRow['source']|null;currentHash:string|null;syncError:string|null;duplicates:Array<{id:string;title:string}>;}
export async function loader({request,params}:Route.LoaderArgs){return adminGet<Detail>(request,'/api/admin/upstream-reviews/'+encodeURIComponent(params.id));}
export default function Review({loaderData}:Route.ComponentProps){return <Editor key={loaderData.row.version} detail={loaderData}/>;}
function Editor({detail}:{detail:Detail}){
 const {row,current,syncError,duplicates}=detail;const action=useAdminAction();
 const [draft,setDraft]=useState({title:row.draft.title||row.source.title,summary:row.draft.summary||'',analysis:row.draft.analysis||'',uncertainties:row.draft.uncertainties||''});
 const [reason,setReason]=useState('');const [checks,setChecks]=useState({facts:false,addedValue:false,duplicates:false});const [selected,setSelected]=useState(false);
 const source=current??row.source;
 const base='/api/admin/upstream-reviews/'+row.id;
 async function save(){return action.run<ReviewRow>('POST',base+'/save',{version:row.version,sourceHash:detail.currentHash,draft},{success:'已保存，重新待审'});}
 async function approve(){const saved=await action.run<ReviewRow>('POST',base+'/save',{version:row.version,sourceHash:detail.currentHash,draft},{revalidate:false});if(saved)await action.run('POST',base+'/decision',{version:saved.version,decision:'approve',reason,selected,checks},{success:'已审批发布到网站'});}
 async function copy(){try{await navigator.clipboard.writeText('python3 tools/aihot/local_opencode.py --review '+row.id);toast('已复制本地加工命令','ok');}catch{toast('无法复制，请手动选择下方命令','error');}}
 return <AdminPage title="引用与加工稿" subtitle="阅读原文、确认新增价值，再决定发布。来源变化后会退出公开层，重新待审。" actions={<><Link to="/admin/reviews" className="text-sm text-accent">返回稿件</Link><Badge>{STATUS[row.status]}</Badge>{row.article_id&&<Link to={'/items/'+row.article_id} className="text-sm text-accent">查看网站版本</Link>}</>}>
  {syncError&&<p role="alert" className="mb-4 text-hot">{syncError}</p>}
  {!!duplicates.length&&<p className="mb-4 text-amber">本站已有同一原文：{duplicates.map(d=><Link key={d.id} to={'/admin/content/'+d.id} className="ml-2 underline">{d.title}</Link>)}。请处理已有文章，避免重复发布。</p>}
  <div className="grid items-start gap-5 xl:grid-cols-2">
   <Card title="来源引用 · 原样保留" right={<span>AIHOT</span>}>
    <h2 className="text-lg font-semibold text-ink">{source.title}</h2><blockquote className="mt-4 whitespace-pre-wrap border-l-2 border-line-strong pl-4 text-[15px] leading-7 text-ink-2">{source.summary||'上游未提供摘要'}</blockquote>
    <div className="mt-5 flex gap-4 text-sm text-accent"><a href={source.links.aihot} target="_blank" rel="noreferrer">AIHOT 阅读入口 ↗</a>{source.links.original&&<a href={source.links.original} target="_blank" rel="noreferrer">原始来源 ↗</a>}</div>
    <p className="mt-3 text-xs text-ink-4">上游评分 {source.score??'未提供'}；不作为本站模型评分。</p>
   </Card>
   <Card title="二次加工稿" right={<Button disabled={action.busy} onClick={copy}>复制本地AI加工命令</Button>}>
    <p className="mb-4 break-all font-mono text-xs text-ink-3">python3 tools/aihot/local_opencode.py --review {row.id}</p>
    {(['title','summary','analysis','uncertainties'] as const).map(field=><label key={field} className="mb-4 block text-sm text-ink-2"><span className="mb-1.5 block">{{title:'标题',summary:'阅读摘要',analysis:'分析：影响、条件与限制',uncertainties:'待核实事项'}[field]}</span>{field==='title'?<Input value={draft[field]} onChange={e=>setDraft({...draft,[field]:e.target.value})}/>:<textarea rows={field==='analysis'?10:4} className="w-full rounded-control border border-line bg-bg p-3 text-sm leading-6 text-ink focus:border-accent focus:outline-none" value={draft[field]} onChange={e=>setDraft({...draft,[field]:e.target.value})}/>}</label>)}
    {row.receipt_id&&<p className="mb-4 text-xs text-ink-4">本地 OpenCode 加工回执 #{row.receipt_id}</p>}
    <div className="space-y-2 border-t border-line pt-4">{(['facts','addedValue','duplicates'] as const).map(key=><label key={key} className="flex gap-2 text-sm text-ink-2"><input type="checkbox" checked={checks[key]} onChange={e=>setChecks({...checks,[key]:e.target.checked})}/>{{facts:'已核对关键事实，推测明确标记',addedValue:'有新增分析价值，不是仅换措辞',duplicates:'已检查重复内容，适合本站'}[key]}</label>)}<label className="flex gap-2 text-sm text-ink-2"><input type="checkbox" checked={selected} onChange={e=>setSelected(e.target.checked)}/>人工精选（同时进入首页）</label></div>
    {row.reason&&<p className="mt-4 text-sm leading-6 text-ink-3">最近复核 / 审批说明：{row.reason}</p>}
    <label className="mt-4 block text-sm text-ink-2">审批或退回说明<Input className="mt-1.5" value={reason} onChange={e=>setReason(e.target.value)} placeholder="记录判断依据"/></label>
    <div className="mt-5 flex flex-wrap gap-2"><Button disabled={action.busy||!!syncError||!current} onClick={save}>保存，重新待审</Button><Button tone="primary" disabled={action.busy||!!syncError||!current||!!duplicates.length||!reason.trim()||Object.values(checks).some(v=>!v)} onClick={approve}>通过并发布</Button><Button disabled={action.busy||!reason.trim()} onClick={()=>action.run('POST',base+'/decision',{version:row.version,decision:'reject',reason},{success:'已退回并退出公开层'})}>退回</Button></div>
   </Card>
  </div>
 </AdminPage>;
}
