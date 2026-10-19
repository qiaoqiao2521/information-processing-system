import { arxivHubHref } from '../features/workbench/model';
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import workflows from '@aihot/industry/workflows/reading.json';
import { titled } from '../lib/seo';
import { getReadingTasks, recordCopiedTask } from '../lib/local-state';

export function meta() { return [{ title: titled('阅读工具') }]; }
export default function ReadingTools() {
  const [query] = useSearchParams();
  const choices = workflows.filter((tool) => tool.mode === 'on-demand');
  const [skill, setSkill] = useState(choices[0]?.id ?? '');
  const [input, setInput] = useState(query.get('url') ?? '');
  const [status, setStatus] = useState('');
  const recordId = query.get('record');
  useEffect(() => {
    if (!recordId) return;
    const saved = getReadingTasks().find((v) => v.id === recordId);
    if (saved) { setInput(saved.input); setSkill(saved.skillId); setStatus('已载入本机任务。'); }
    else setStatus('这条任务不在当前浏览器，请重新填写材料。');
  }, [recordId]);
  const paperLink = arxivHubHref(input);
  const tool = choices.find((choice) => choice.id === skill);
  const task = tool && input.trim() ? `使用项目技能 ${tool.id}（${tool.name}）。\n${tool.task}\n\n处理材料：\n${input.trim()}\n\n保留原文出处和日期；只有摘要时不要声称已阅读全文。遇到登录或验证请停止并交给我操作。` : '';
  return <section className="py-5">
    <h1 className="text-[24px] font-bold text-ink">阅读工具</h1>
    <p className="mt-2 text-[14px] text-ink-3">选好材料与技能，复制任务交给 Agent。此页面只准备文本。</p>
    <div className="mt-6 rounded-control border border-line p-4"><a href="https://papers.muqiao.xyz/" target="_blank" rel="noopener noreferrer" className="text-cyan-200">ArXivHub · 本地论文阅读、翻译与讨论 ↗</a><p className="mt-2 text-sm text-ink-3">填入 arXiv ID 或原文链接，可直接打开该论文的工具目录。</p>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-sm text-ink-3"><a href="https://arxivhub.github.io/" target="_blank" rel="noopener noreferrer">官方站点 ↗</a><a href="https://github.com/Peaceful-World-X/ArXivHub" target="_blank" rel="noopener noreferrer">GitHub 开源项目 ↗</a></div>
      {paperLink && <a href={paperLink} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block text-cyan-200">打开这篇论文的工具入口 ↗</a>}
    </div>
    <div className="mt-4 rounded-control border border-line p-4"><a href="https://news.muqiao.xyz/" target="_blank" rel="noopener noreferrer" className="text-cyan-200">NewsNow · 本地实时新闻与热点 ↗</a><p className="mt-2 text-sm text-ink-3">浏览多平台新闻与热点榜。</p>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-sm text-ink-3"><a href="https://newsnow.busiyi.world/" target="_blank" rel="noopener noreferrer">官方站点 ↗</a><a href="https://github.com/newsnext/newsnow" target="_blank" rel="noopener noreferrer">GitHub 开源项目 ↗</a></div>
    </div>
    <div className="mt-6 grid gap-4">
      <label className="grid gap-2 text-[14px]">选择技能
        <select aria-label="选择技能" value={skill} onChange={(event) => { setSkill(event.target.value); setStatus(''); }} className="rounded-control border border-line bg-surface p-3">
          {choices.map((choice) => <option key={choice.id} value={choice.id}>{choice.name}</option>)}
        </select>
      </label>
      <p className="text-[13px] text-ink-3">{tool?.description} {tool?.requires}</p>
      <label className="grid gap-2 text-[14px]">原文链接或处理材料
        <textarea aria-label="原文链接或处理材料" rows={6} maxLength={18000} value={input} onChange={(event) => setInput(event.target.value)} className="rounded-control border border-line bg-surface p-3" />
      </label>
      <details><summary className="cursor-pointer text-[13px] text-ink-3">查看处理任务</summary><pre className="mt-3 whitespace-pre-wrap rounded-control bg-bg-sunk p-4 text-[13px]">{task || '先填入材料。'}</pre></details>
      <button disabled={!task} className="rounded-control bg-accent px-4 py-3 font-medium text-accent-contrast disabled:opacity-40" onClick={async () => {
        try {
          await navigator.clipboard.writeText(task);
          const saved = tool && recordCopiedTask(tool.id, tool.name, input.trim());
          setStatus(saved ? '已复制处理任务，并保存到本机加工记录。' : '已复制处理任务；本机记录未能保存。');
        }
        catch { setStatus('复制失败，请展开处理任务手动复制。'); }
      }}>复制处理任务</button>
      <p role="status" className="text-[13px] text-ink-3">{status}</p>
      <Link to="/me?view=tasks" className="text-[13px] text-accent">查看我的加工记录</Link>
    </div>
  </section>;
}
