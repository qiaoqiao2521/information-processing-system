import { Link, useNavigate } from 'react-router';
import type { Route } from './+types/reviews';
import { adminGet } from '../../lib/admin.server';
import { useAdminAction } from '../../features/admin/action';
import { AdminPage, Badge, Button, Card, Empty } from '../../features/admin/ui';
export interface ReviewRow {id:string;version:number;status:string;source:{title:string;summary:string|null;score:number|null;links:{aihot:string;original?:string|null}};draft:{title?:string;summary?:string;analysis?:string;uncertainties?:string};article_id:string|null;receipt_id:number|null;reason:string|null;}
export const STATUS:Record<string,string>={draft:'待审',approved:'已发布',rejected:'已退回',stale:'来源已更正',withdrawn:'来源已撤选 / 过期'};
interface Data {material:Array<ReviewRow['source'] & {id:string}>;rows:ReviewRow[];syncError:string|null;}
export async function loader({request}:Route.LoaderArgs){return adminGet<Data>(request,'/api/admin/upstream-reviews');}
export default function Reviews({loaderData}:Route.ComponentProps){
 const {material,rows,syncError}=loaderData;const action=useAdminAction();const navigate=useNavigate();const known=new Map(rows.map(r=>[r.id,r]));
 async function create(id:string){const row=await action.run<ReviewRow>('POST','/api/admin/upstream-reviews',{id});if(row)navigate('/admin/reviews/'+row.id);}
 return <AdminPage title="加工审批" subtitle="引用保留原样，加工稿单独审阅。只有你确认通过，才进入网站、RSS和API。">
  {syncError&&<p role="alert" className="mb-4 text-hot">{syncError}</p>}
  <Card title="稿件"><div className="divide-y divide-line">{rows.map(r=><Link key={r.id} to={'/admin/reviews/'+r.id} className="flex items-center justify-between gap-3 py-3"><span className="min-w-0 text-sm text-ink">{r.draft.title||r.source.title}</span><Badge tone={r.status==='approved'?'ok':r.status==='draft'?'accent':'warn'}>{STATUS[r.status]}</Badge></Link>)}{!rows.length&&<Empty>从下方近期材料建立第一份待审稿。</Empty>}</div></Card>
  <section className="mt-6"><h2 className="mb-3 text-base font-semibold text-ink">近期上游材料</h2><div className="divide-y divide-line">{material.map(s=><div key={s.id} className="flex items-start justify-between gap-4 py-4"><div className="min-w-0"><a href={s.links.aihot} target="_blank" rel="noreferrer" className="text-sm font-medium text-ink hover:text-accent">{s.title}</a><p className="mt-1 line-clamp-2 max-w-3xl text-sm text-ink-3">{s.summary}</p><p className="mt-1 text-xs text-ink-4">AIHOT 上游评分：{s.score??'未提供'}</p></div>{known.has(s.id)?<Link className="shrink-0 text-sm text-accent" to={'/admin/reviews/'+s.id}>打开稿件</Link>:<Button disabled={action.busy||!!syncError} onClick={()=>create(s.id)}>建立待审稿</Button>}</div>)}</div></section>
 </AdminPage>;
}
