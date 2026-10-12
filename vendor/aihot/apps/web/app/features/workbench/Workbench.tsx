import { filterHref } from './model';
import { Form, Link, NavLink, useLocation, useNavigation, useRevalidator, useSearchParams, useNavigate } from 'react-router';
import { motion, MotionConfig } from 'motion/react';
import type { ReactNode } from 'react';
import type { FeedItemSummary, SiteStats, TimelineFilters } from '@aihot/contracts/site';
import { CATEGORIES } from '@aihot/industry/taxonomy';
import { CHANNEL_KEYS, CHANNEL_LABELS } from '@aihot/contracts/taxonomy';
import { displayTitle } from '../../lib/item-display.ts';
import { Backdrop } from './FrozenCards';
import { NavigationProgress, BackToTop } from '../../components/shell/Chrome';


const links = [['/all', '全部动态', 'Stream'], ['/starred', '收藏', 'Saved'], ['/hot', '热点', 'Hot'], ['/daily', '日报', 'Daily'], ['/topics', '主题', 'Topics'], ['/reading-tools', '阅读工具', 'Tools'], ['/codex-reset', 'GPT重置', 'Reset'], ['/agent', 'Agent接口', 'API / RSS / MCP'], ['/more', '更多', 'More']] as const;

export function WorkbenchShell({ children }: { children: ReactNode }) {
  const navigation = useNavigation();
  return <MotionConfig reducedMotion="user"><div className="make-workbench grain relative min-h-screen" data-theme="dark">
    <Backdrop pulse={null} /><NavigationProgress active={navigation.state === 'loading'} />
    <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[70] focus:bg-black focus:px-4">跳到正文</a>
    <div className="relative flex"><aside className="sticky top-0 hidden h-screen w-[260px] shrink-0 flex-col justify-between overflow-y-auto py-10 pl-10 pr-6 lg:flex">
      <div><Link to="/" className="flex items-center gap-3"><div className="relative h-10 w-10"><motion.div animate={{ rotate: 360 }} transition={{ duration: 14, repeat: Infinity, ease: 'linear' }} className="absolute inset-0 rounded-full bg-[conic-gradient(from_0deg,#67e8f9,#ffffff,#ffb547,#67e8f9)] blur-[6px]" /><div className="absolute inset-[3px] grid place-items-center rounded-full bg-[#06060c] font-serif text-lg italic">木</div></div><div><div className="text-[15px] font-medium tracking-[0.2em]">木乔</div><div className="font-serif text-sm italic text-white/40">reading desk</div></div></Link>
      <nav aria-label="主要导航" className="mt-12 flex flex-col gap-5">{links.map(([to, label, en], i) => <NavLink end={to === '/all'} key={to} to={to} className={({ isActive }) => `group relative ${isActive ? 'text-white' : 'text-white/55 hover:text-white'}`}><div className="flex items-baseline gap-3"><span className="font-display text-[11px] tracking-widest text-cyan-300/60">{String(i + 1).padStart(2, '0')}</span><span className={i === 0 ? 'text-[22px] font-light tracking-wide' : 'text-[14px]'}>{label}</span></div>{i === 0 && <div className="ml-8 mt-1 font-serif text-sm italic text-white/25">{en}</div>}</NavLink>)}</nav></div>
      <p className="mt-8 border-t border-white/10 pt-4 font-mono text-[10px] text-white/40">公开资料 · 来源可追溯<br />地图为视觉背景</p>
    </aside><main id="main" className="min-w-0 flex-1 px-5 pb-24 pt-5 md:px-10">
      <div className="mb-4 flex items-center justify-between lg:hidden"><Link to="/" className="text-sm tracking-widest">木乔 · 阅读工作台</Link><Link to="/more" className="text-xs text-cyan-200">更多入口 ↗</Link></div>
      <nav aria-label="手机导航" className="mb-4 flex gap-4 overflow-x-auto whitespace-nowrap text-xs text-white/65 lg:hidden">{links.slice(0, 5).map(([to, label]) => <NavLink key={to} end to={to} className={({isActive}) => isActive ? 'text-cyan-200' : ''}>{label}</NavLink>)}<Link to="/reading-tools">工具</Link><Link to="/agent">接口</Link></nav>
      {children}</main></div><BackToTop />
  </div></MotionConfig>;
}

export function WorkbenchFeed({ title, items, filters, generatedAt, stats, total, children }: {
  title: string; items: FeedItemSummary[]; filters: TimelineFilters & { q?: string | null; tab?: string }; generatedAt: string;
  stats?: SiteStats | null; total?: number; children: ReactNode;
}) {
  const { pathname } = useLocation();
  const [params] = useSearchParams();
  const navigation = useNavigation();
  const revalidator = useRevalidator();
  const navigate = useNavigate();
  const base = pathname === '/' ? '/' : '/all';
  const latest = items.map(i => i.publishedAt ?? i.timelineAt).sort().at(-1);
  const stamp = (v: string) => new Intl.DateTimeFormat('zh-CN', {timeZone:'Asia/Shanghai', year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit'}).format(new Date(v));
  const metrics = stats ? [['24H入库', stats.day.collected], ['总入库', stats.items], ['信源', stats.sources]] : [['本页', items.length], ['总条目', total ?? '—']];
  return <div aria-busy={navigation.state === 'loading'}>
    <div className="flex flex-wrap items-center justify-between gap-2 border-y border-white/10 py-2 font-mono text-[10px] tracking-wider text-white/50"><span>DATA <span className="text-cyan-200">公开数据</span> · 读取 {stamp(generatedAt)}</span><button type="button" onClick={() => revalidator.revalidate()} disabled={revalidator.state !== 'idle'} className="text-amber-200">{revalidator.state === 'idle' ? '刷新 ↻' : '刷新中…'}</button></div>
    <header className="mb-4 mt-4 flex flex-wrap items-center gap-x-6 gap-y-3"><div className="flex items-baseline gap-4"><h1 className="text-[28px] font-bold tracking-tight text-holo">{title}</h1><span className="font-mono text-[10px] text-cyan-300/60">STREAM · {total ?? items.length} ITEMS</span></div><div className="edge ml-auto flex flex-wrap items-center divide-x divide-white/10 rounded-xl">{metrics.map(([label, value]) => <div key={label} className="flex items-baseline gap-2 px-3 py-2"><span className="whitespace-nowrap font-mono text-[10px] text-white/50">{label}</span><span className="font-display text-lg tabular-nums">{value}</span></div>)}</div></header>
    <div className="relative mb-5 flex overflow-hidden border-y border-white/10 py-2"><span className="z-10 mr-5 shrink-0 bg-amber-300 px-2 font-mono text-[10px] font-bold text-black">FEED</span><div className="flex min-w-0 gap-8 ticker-track shrink-0 whitespace-nowrap text-[13px] text-white/65">{[...items.slice(0, 8), ...items.slice(0, 8)].map((i, index) => <Link key={`${i.id}:${index}`} to={`/items/${i.id}`}>{displayTitle(i)}</Link>)}</div></div>
    <div className="mb-3 flex flex-col gap-3"><label className="edge flex w-fit items-center gap-3 rounded-full px-4 py-2 text-[13px] text-white/70">分类<select aria-label="分类" value={filters.category ?? ''} onChange={event => navigate(filterHref(base, params, {category:event.target.value || null}))} className="bg-[#101821] text-white outline-none rounded px-2 py-1">{[{key:'', label:'全部分类'}, ...CATEGORIES].map(c => <option key={c.key} value={c.key}>{c.label}</option>)}</select></label>
      <div className="flex flex-wrap items-center gap-3"><nav aria-label="来源筛选" className="flex gap-3 text-[12px]">{CHANNEL_KEYS.map(channel => <Link key={channel} aria-current={filters.channel === channel ? 'page' : undefined} to={filterHref(base, params, {channel: channel === 'all' ? null : channel})} className={filters.channel === channel ? 'text-cyan-200' : 'text-white/55'}>{CHANNEL_LABELS[channel]}</Link>)}</nav><Link to={filterHref('/all', params, {tag: filters.tag === '二次加工' ? null : '二次加工'})} className={`text-[12px] ${filters.tag === '二次加工' ? 'text-amber-200' : 'text-white/55'}`}>AI加工</Link>
      <Form key={`${filters.q ?? ''}:${filters.channel}:${filters.category}:${filters.tag}`} method="get" action="/all" role="search" className="ml-auto flex w-full gap-2 sm:w-auto">{(['channel','category','tag','tab'] as const).map(k => filters[k] && filters[k] !== 'all' && !(k === 'tab' && filters[k] === 'time') ? <input key={k} type="hidden" name={k} value={filters[k]!} /> : null)}<input aria-label="搜索标题、摘要与正文" name="q" defaultValue={filters.q ?? ''} maxLength={200} placeholder="搜索标题、摘要…" className="edge min-w-0 flex-1 rounded-full px-4 py-2 text-xs sm:w-52" /><button type="submit" className="rounded-full border border-white/20 px-4 text-xs text-cyan-200">搜索</button></Form></div>
    </div>
    <div className="mb-5 flex flex-wrap gap-x-4 gap-y-2 text-[11px] text-white/55"><span>{latest ? `本页最新发表：${stamp(latest)}` : '暂无发表记录'} · 北京时间</span><span>采集更新与文章发表时间分开记录</span>{filters.tag && <span>标签：{filters.tag} <Link to={filterHref(base, params, {tag:null})} className="text-cyan-200">清除</Link></span>}{filters.q && <nav aria-label="搜索排序" className="flex gap-3">{[['time','最新'],['relevance','全文相关']].map(([v, label]) => <Link key={v} to={filterHref('/all', params, {tab:v === 'time' ? null : v})} className={filters.tab === v ? 'text-cyan-200' : ''}>{label}</Link>)}</nav>}</div>
    {children}
  </div>;
}
