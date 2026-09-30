import { useState } from 'react';
import { useSearchParams } from 'react-router';
import workflows from '@aihot/industry/workflows/reading.json';
import { titled } from '../lib/seo';

export function meta() { return [{ title: titled('阅读工具') }]; }
export default function ReadingTools() {
  const [query] = useSearchParams();
  const choices = workflows.filter((tool) => tool.mode === 'on-demand');
  const [skill, setSkill] = useState(choices[0]?.id ?? '');
  const [input, setInput] = useState(query.get('url') ?? '');
  const [status, setStatus] = useState('');
  const tool = choices.find((choice) => choice.id === skill);
  const task = tool && input.trim() ? `使用项目技能 ${tool.id}（${tool.name}）。\n${tool.task}\n\n处理材料：\n${input.trim()}\n\n保留原文出处和日期；只有摘要时不要声称已阅读全文。遇到登录或验证请停止并交给我操作。` : '';
  return <section className="py-5">
    <h1 className="text-[24px] font-bold text-ink">阅读工具</h1>
    <p className="mt-2 text-[14px] text-ink-3">选好材料与技能，复制任务交给 Agent。此页面只准备文本。</p>
    <div className="mt-6 grid gap-4">
      <label className="grid gap-2 text-[14px]">选择技能
        <select value={skill} onChange={(event) => { setSkill(event.target.value); setStatus(''); }} className="rounded-control border border-line bg-surface p-3">
          {choices.map((choice) => <option key={choice.id} value={choice.id}>{choice.name}</option>)}
        </select>
      </label>
      <p className="text-[13px] text-ink-3">{tool?.description} {tool?.requires}</p>
      <label className="grid gap-2 text-[14px]">原文链接或处理材料
        <textarea rows={6} maxLength={18000} value={input} onChange={(event) => setInput(event.target.value)} className="rounded-control border border-line bg-surface p-3" />
      </label>
      <details><summary className="cursor-pointer text-[13px] text-ink-3">查看处理任务</summary><pre className="mt-3 whitespace-pre-wrap rounded-control bg-bg-sunk p-4 text-[13px]">{task || '先填入材料。'}</pre></details>
      <button disabled={!task} className="rounded-control bg-accent px-4 py-3 font-medium text-white disabled:opacity-40" onClick={async () => {
        try { await navigator.clipboard.writeText(task); setStatus('已复制处理任务'); }
        catch { setStatus('复制失败，请展开处理任务手动复制。'); }
      }}>复制处理任务</button>
      <p role="status" className="text-[13px] text-ink-3">{status}</p>
    </div>
  </section>;
}
