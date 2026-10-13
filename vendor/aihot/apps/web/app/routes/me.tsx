import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { pageMeta } from "../lib/seo";
import { fullDateTime } from "../lib/format";
import { LocalDataActions } from "../features/reader/LocalDataActions";
import { MATERIAL_LIMIT, removeReading, removeReadingTask, saveTaskResult, toggleFollowedSource, useFollowedSources, useReadSet, useReadingHistory, useReadingTasks, useStarred, type LocalReadingTask } from "../lib/local-state";

export function meta() { return pageMeta({ title: "我的阅读", path: "/me", noindex: true }); }
export function headers() { return { "Cache-Control": "no-store" }; }

const tabs = [["recent", "最近阅读"], ["tasks", "加工记录"], ["following", "关注来源"], ["settings", "数据与设置"]] as const;

function TaskRecord({ task, report }: { task: LocalReadingTask; report: (message: string) => void }) {
  const [result, setResult] = useState(task.result ?? "");
  useEffect(() => setResult(task.result ?? ""), [task.result]);
  return <details className="rounded-control border border-line p-4">
    <summary className="cursor-pointer text-[14px] font-medium text-ink">
      {task.skillName}<span className="ml-3 text-[12px] font-normal text-ink-3">{task.result ? "已保存结果 · 未复核" : "已复制任务 · 待外部处理"}</span>
    </summary>
    <p className="mt-2 text-[12px] text-ink-4">复制于 {fullDateTime(task.copiedAt)}{task.resultSavedAt ? ` · 结果保存于 ${fullDateTime(task.resultSavedAt)}` : ""}</p>
    <pre className="mt-3 max-h-36 overflow-auto whitespace-pre-wrap break-words text-[13px] text-ink-3">{task.input}</pre>
    <label className="mt-4 grid gap-2 text-[13px] text-ink-3">粘贴处理结果
      <textarea rows={5} maxLength={MATERIAL_LIMIT} value={result} onChange={(event) => setResult(event.target.value)} className="w-full rounded-control border border-line bg-surface p-3 text-ink" />
    </label>
    <p className="mt-2 text-[12px] text-ink-4">结果只保存在本机；保存不代表已审核或已发布。</p>
    <div className="mt-3 flex flex-wrap gap-4 text-[13px] text-accent">
      <button type="button" onClick={() => report(saveTaskResult(task.id, result) ? "结果已保存到本机，尚未复核。" : "结果未能保存，请检查本机存储。")}>保存结果</button>
      <Link to={`/reading-tools?record=${encodeURIComponent(task.id)}`}>重新打开任务</Link>
      <button type="button" className="text-ink-4" onClick={() => report(removeReadingTask(task.id) ? "已移除这条加工记录。" : "记录未能移除。")}>移除记录</button>
    </div>
  </details>;
}

export default function MyReading() {
  const history = useReadingHistory(), tasks = useReadingTasks(), sources = useFollowedSources(), stars = useStarred(), read = useReadSet();
  const [params] = useSearchParams();
  const view = tabs.some(([key]) => key === params.get("view")) ? params.get("view")! : "recent";
  const [ready, setReady] = useState(false), [notice, setNotice] = useState(""), [count, setCount] = useState(20);
  useEffect(() => setReady(true), []);
  useEffect(() => { setCount(20); setNotice(""); }, [view]);
  const latest = history.find((item) => item.position > 0 && item.position < 0.98 && item.bodyHash);
  const resumeHref = (path: string) => `${path}?resume=1`;
  const legacyCount = [...read].filter((id) => !history.some((v) => v.id === id)).length;
  return <section className="mx-auto max-w-[var(--page-max-reading)] pb-10 pt-5 lg:pt-1">
    <header className="border-b border-line pb-5">
      <h1 className="text-[26px] font-semibold text-ink">我的阅读</h1>
      <p className="mt-2 text-[13px] leading-relaxed text-ink-3">留下想读的内容，接着上次的位置阅读，再查看自己的加工记录。</p>
      <p className="mt-1 text-[12px] text-ink-4">仅当前浏览器保存；换设备可用文件导入，清除浏览器数据前请先导出。</p>
      <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-[13px]">
        <Link to="/starred" className="font-medium text-accent">我的收藏{ready ? ` · ${stars.length}` : ""}</Link>
        <Link to="/all" className="text-ink-3">发现新内容</Link>
        <Link to="/reading-tools" className="text-ink-3">准备加工任务</Link>
      </div>
    </header>
    {ready && latest && <div className="my-5 flex flex-wrap items-center justify-between gap-3 border-l-2 border-accent pl-4">
      <div className="min-w-0 flex-1"><p className="text-[12px] text-ink-4">继续阅读 · {Math.round(latest.position * 100)}%</p><h2 className="mt-1 break-words text-[16px] font-medium text-ink">{latest.title}</h2></div>
      <Link to={resumeHref(latest.path)} className="shrink-0 rounded-full border border-line-strong px-4 py-2 text-[13px] text-accent">继续阅读</Link>
    </div>}
    <nav aria-label="我的阅读栏目" className="my-5 flex gap-5 overflow-x-auto whitespace-nowrap border-b border-line pb-3 text-[13px]">
      {tabs.map(([key, label]) => <Link key={key} to={`/me?view=${key}`} aria-current={view === key ? "page" : undefined} className={view === key ? "font-medium text-accent" : "text-ink-3"}>{label}</Link>)}
    </nav>
    {notice && <p role="status" className="mb-4 text-[13px] text-accent">{notice}</p>}
    {!ready ? <p className="text-[13px] text-ink-3">正在读取本机记录…</p> : <>
      {view === "recent" && <>
        {legacyCount > 0 && <p className="mb-4 text-[12px] text-ink-4">已保留 {legacyCount} 条历史已读标记。新的阅读记录会显示标题、时间和位置。</p>}
        {history.length === 0 ? <p className="py-8 text-[14px] text-ink-3">打开一篇动态后，这里会留下阅读记录。<Link to="/all" className="ml-2 text-accent">浏览全部动态</Link></p> : <ul className="divide-y divide-line-soft">
          {history.slice(0, count).map((item) => <li key={item.id} className="py-4">
            <div className="flex items-start justify-between gap-3"><Link to={item.path} className="min-w-0 break-words text-[16px] font-medium text-ink hover:text-accent">{item.title}</Link><button type="button" aria-label={`移除阅读记录：${item.title}`} className="shrink-0 text-[12px] text-ink-4" onClick={() => setNotice(removeReading(item.id) ? "已移除阅读记录，收藏和已读标记已保留。" : "阅读记录未能移除。")}>移除</button></div>
            <p className="mt-2 text-[12px] text-ink-4">{item.sourceName} · 阅读于 {fullDateTime(item.visitedAt)}</p>
            {item.bodyHash && item.position > 0 && <Link to={resumeHref(item.path)} className="mt-2 inline-block text-[13px] text-accent">{item.position >= 0.98 ? "回到阅读末尾" : `继续阅读 · ${Math.round(item.position * 100)}%`}</Link>}
          </li>)}
        </ul>}
        {history.length > count && <button type="button" onClick={() => setCount((v) => v + 20)} className="mt-4 text-[13px] text-accent">查看更早记录</button>}
      </>}
      {view === "tasks" && <>
        <p className="mb-4 text-[13px] leading-relaxed text-ink-3">复制任务后会自动留下记录。交给 Agent 处理后，可把结果粘贴回来保存。<Link to="/all?tag=%E4%BA%8C%E6%AC%A1%E5%8A%A0%E5%B7%A5" className="ml-2 text-accent">查看站内公开加工产出</Link></p>
        {tasks.length === 0 ? <p className="py-8 text-[14px] text-ink-3">还没有加工记录。<Link to="/reading-tools" className="ml-2 text-accent">准备第一个任务</Link></p> : <div className="space-y-3">{tasks.map((task) => <TaskRecord key={task.id} task={task} report={setNotice} />)}</div>}
      </>}
      {view === "following" && <>
        <p className="mb-4 text-[13px] text-ink-3">在内容详情页关注来源，回来查看该来源已收录的动态。</p>
        {sources.length === 0 ? <p className="py-8 text-[14px] text-ink-3">还没有关注来源。<Link to="/all" className="ml-2 text-accent">从全部动态开始</Link></p> : <ul className="divide-y divide-line-soft">{sources.map((source) => <li key={source.id} className="flex items-center justify-between gap-3 py-4">
          <Link to={`/all?source=${encodeURIComponent(source.id)}`} className="min-w-0 break-words text-[15px] text-ink hover:text-accent">{source.name} <span className="ml-2 text-[12px] text-accent">查看动态</span></Link>
          <button type="button" className="shrink-0 text-[12px] text-ink-4" onClick={() => setNotice(toggleFollowedSource(source.id, source.name) ? "已取消关注。" : "关注未能保存。")}>取消关注</button>
        </li>)}</ul>}
      </>}
      {view === "settings" && <div className="space-y-6 text-[14px]">
        <div><h2 className="font-medium text-ink">本机数据</h2><p className="mb-3 mt-2 text-[13px] leading-relaxed text-ink-3">导出包含收藏、已读标记、阅读位置、关注来源、任务与手工保存的结果。导入会保留已有记录，适合手动转到另一台设备。文件可能含私人材料，请自行保管。</p><LocalDataActions /></div>
        <div className="border-t border-line pt-4"><h2 className="font-medium text-ink">外观</h2><p className="mt-2 text-[13px] text-ink-3">沿用当前阅读工作台的深色样式。</p></div>
        <div className="flex flex-wrap gap-4 border-t border-line pt-4 text-[13px] text-accent"><Link to="/more">更多工具与说明</Link><Link to="/privacy">隐私说明</Link><Link to="/feedback">反馈问题</Link></div>
      </div>}
    </>}
  </section>;
}
