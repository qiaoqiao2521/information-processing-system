import { useEffect, useRef, useState, type MouseEvent } from 'react'
import { motion, useMotionTemplate, useMotionValue, useSpring } from 'motion/react'
import { Link } from 'react-router'
import type { FeedItemSummary, TimelineCard } from '@aihot/contracts/site'
import { markRead, toggleStar, useIsStarred, useReadSet } from '../../lib/local-state'
import { toWorkbenchItem, type Item } from './model'

function ArticleActions({ it }: { it: Item }) {
  const starred = useIsStarred(it.id)
  const read = useReadSet().has(it.id)
  return <div className="relative mt-3 flex flex-wrap items-center gap-3 text-[12px] text-white/60">
    <button type="button" aria-pressed={starred} aria-label={`${starred ? '取消收藏' : '收藏'}：${it.title}`} onClick={() => toggleStar({ id: it.id, title: it.title, summary: it.raw.summary, sourceName: it.source, publishedAt: it.raw.publishedAt, score: it.raw.score, aiSelected: it.raw.selected })} className="hover:text-cyan-200">{starred ? '★ 已收藏' : '☆ 收藏'}</button>
    {read && <span>已读</span>}
    <Link to={`/items/${it.id}/original`} className="hover:text-cyan-200">原文 ↗</Link>
    {it.group?.story && <Link to={`/story/${it.group.story.publicId}`} className="hover:text-cyan-200">事件 · {it.group.reportCount} 篇报道</Link>}
    {it.raw.tags.includes('二次加工') && <span className="text-amber-200">AI加工 · 已复核</span>}
    {!it.raw.selected && it.raw.score === null && !it.raw.tags.includes('二次加工') && <span>待AI处理</span>}
  </div>
}
import WorldMap from './WorldMap'

type View = 'featured' | 'all'
const ease = [0.22, 1, 0.36, 1] as const
const hues: Record<string, string> = {
  '模型发布/更新': '#67e8f9',
  论文研究: '#e2e8f0',
  '产品发布/更新': '#ffb547',
  行业动态: '#fb7185',
  技巧与观点: '#86efac',
  开源: '#86efac',
}

const GLYPHS = '01<>/#$%&*+=?ABCDEFXYZ'
function Scramble({ text, delay = 0 }: { text: string; delay?: number }) {
  const [out, setOut] = useState(text)
  useEffect(() => {
    setOut(text)
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let raf = 0
    const start = performance.now() + delay * 1000
    const tick = (now: number) => {
      if (now < start) return (raf = requestAnimationFrame(tick))
      // Elapsed time stays bounded when background tabs throttle animation frames.
      const done = Math.floor(((now - start) / 750) * text.length)
      setOut(
        [...text]
          .map((ch, i) => (i < done || ch === ' ' ? ch : GLYPHS[(Math.random() * GLYPHS.length) | 0]))
          .join(''),
      )
      if (done < text.length) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [text, delay])
  return <><span className="sr-only">{text}</span><span aria-hidden="true">{out}</span></>
}

export function Backdrop({ pulse }: { pulse: { source: string; n: number } | null }) {
  const x = useSpring(useMotionValue(0), { stiffness: 30, damping: 20 })
  const y = useSpring(useMotionValue(0), { stiffness: 30, damping: 20 })
  useEffect(() => {
    const f = (e: globalThis.MouseEvent) => {
      x.set((e.clientX / innerWidth - 0.5) * 80)
      y.set((e.clientY / innerHeight - 0.5) * 80)
    }
    addEventListener('mousemove', f)
    return () => removeEventListener('mousemove', f)
  }, [x, y])
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden">
      <div className="grid-bg absolute inset-0 opacity-50" />
      <div className="absolute inset-0 opacity-90 [mask-image:radial-gradient(ellipse_at_55%_55%,#000_45%,transparent_85%)]">
        <WorldMap pulse={pulse} />
      </div>
      <motion.div style={{ x, y }} className="absolute inset-0">
        <motion.div
          animate={{ x: [0, 120, -60, 0], y: [0, 80, 40, 0], scale: [1, 1.2, 0.9, 1] }}
          transition={{ duration: 26, repeat: Infinity, ease: 'easeInOut' }}
          className="aurora -left-[10%] -top-[20%] h-[70vh] w-[60vw] bg-[#0c4a6e]/50"
        />
        <motion.div
          animate={{ x: [0, -100, 50, 0], y: [0, 60, -40, 0] }}
          transition={{ duration: 30, repeat: Infinity, ease: 'easeInOut' }}
          className="aurora -right-[15%] top-[10%] h-[60vh] w-[50vw] bg-[#0e7490]/45"
        />
        <motion.div
          animate={{ x: [0, 80, -80, 0], scale: [1, 0.85, 1.15, 1] }}
          transition={{ duration: 34, repeat: Infinity, ease: 'easeInOut' }}
          className="aurora bottom-[-30%] left-[25%] h-[60vh] w-[50vw] bg-[#78350f]/25"
        />
      </motion.div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_30%,#030308_95%)]" />
    </div>
  )
}

function Spotlight({ children, className = '', hue = '#67e8f9' }: { children: React.ReactNode; className?: string; hue?: string }) {
  const mx = useMotionValue(-400)
  const my = useMotionValue(-400)
  const bg = useMotionTemplate`radial-gradient(420px circle at ${mx}px ${my}px, ${hue}22, transparent 60%)`
  const ref = useRef<HTMLDivElement>(null)
  const move = (e: MouseEvent) => {
    const r = ref.current!.getBoundingClientRect()
    mx.set(e.clientX - r.left)
    my.set(e.clientY - r.top)
  }
  return (
    <div
      ref={ref}
      onMouseMove={move}
      onMouseLeave={() => (mx.set(-400), my.set(-400))}
      className={`edge group relative overflow-hidden rounded-[28px] ${className}`}
    >
      <motion.div className="pointer-events-none absolute inset-0" style={{ background: bg }} />
      {children}
    </div>
  )
}

function Tag({ t }: { t: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px] tracking-wider" style={{ color: (hues[t] ?? '#67e8f9') }}>
      <span className="h-1 w-1 rounded-full" style={{ background: (hues[t] ?? '#67e8f9'), boxShadow: `0 0 8px ${(hues[t] ?? '#67e8f9')}` }} />
      {t}
    </span>
  )
}

function Arrow() {
  return (
    <span className="grid h-9 w-9 place-items-center rounded-full border border-white/10 text-white/50 transition-all duration-500 group-hover:rotate-[-45deg] group-hover:border-white/40 group-hover:bg-white group-hover:text-black">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M5 12h14M13 6l6 6-6 6" />
      </svg>
    </span>
  )
}

function Orb({ hue }: { hue: string }) {
  return (
    <div className="pointer-events-none absolute -right-20 -top-20 h-80 w-80">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}
        className="h-full w-full rounded-full opacity-60 blur-2xl"
        style={{ background: `conic-gradient(from 90deg, ${hue}, #0c4a6e, transparent, ${hue})` }}
      />
      <div className="absolute inset-16 rounded-full border border-white/10" />
      <div className="absolute inset-24 rounded-full border border-white/[0.06]" />
    </div>
  )
}

export function Featured({ list }: { list: Item[] }) {
  if (!list.length) return <Empty />
  const [hero, ...rest] = list
  // first two sit beside the hero; the rest tile in rows of 3, last partial row stretches
  const tail = Math.max(rest.length - 2, 0)
  const full = tail - (tail % 3)
  const span = (i: number) => {
    if (i < 2) return 'md:col-span-4'
    const j = i - 2
    if (j < full) return 'md:col-span-4'
    return tail % 3 === 1 ? 'md:col-span-12' : 'md:col-span-6'
  }
  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-12">
      <motion.div
        data-card-key={hero.dataKey ?? hero.id}
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease }}
        className={rest.length ? 'md:col-span-8 md:row-span-2' : 'md:col-span-12'}
      >
        <Spotlight hue={hues[hero.tag]} className="h-full min-h-[340px] p-8">
          <Orb hue={hues[hero.tag]} />
          <div className="relative flex h-full min-h-[270px] flex-col justify-between">
            <div className="flex items-center gap-4">
              <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 font-serif text-sm italic text-white/80">
                精选 · 已处理
              </span>
              <Tag t={hero.tag} />
            </div>
            <div className="max-w-3xl">
              <h2 className="text-[clamp(24px,2.6vw,36px)] font-medium leading-[1.15] tracking-tight"><Link to={`/items/${hero.id}`} onClick={() => markRead(hero.id)}><Scramble text={hero.title} /></Link>
              </h2>
              <p className="mt-5 max-w-xl text-[15px] leading-[1.9] text-white/50">{hero.summary}</p>
              <div className="mt-8 flex items-center gap-5 text-sm text-white/40">
                <span className="text-white/80">{hero.source}</span>
                <span className="h-px w-8 bg-white/20" />
                <span className="font-display">{hero.date}</span>
                <span className="font-display">{hero.time}</span>
                <span className="ml-auto">
                  <Arrow />
                </span>
              </div>
              <ArticleActions it={hero} />
            </div>
          </div>
        </Spotlight>
      </motion.div>

      {rest.map((it, i) => (
        <motion.div
          key={it.dataKey ?? it.id}
          data-card-key={it.dataKey ?? it.id}
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease, delay: 0.12 + i * 0.07 }}
          className={span(i)}
        >
          <Spotlight hue={hues[it.tag]} className="flex h-full min-h-[160px] flex-col p-6">
            <div className="relative flex items-start justify-between">
              <Tag t={it.tag} />
              <span className="font-display text-5xl font-light leading-none outline-text">
                {String(i + 2).padStart(2, '0')}
              </span>
            </div>
            <h3
              className={`relative mt-auto pt-6 font-medium leading-snug ${span(i) === 'md:col-span-4' ? 'text-lg' : 'text-2xl'}`}
            >
              <Link to={`/items/${it.id}`} onClick={() => markRead(it.id)}><Scramble text={it.title} delay={Math.min(0.15 + i * 0.07, 0.5)} /></Link>
            </h3>
            {span(i) !== 'md:col-span-4' && <p className="relative mt-3 line-clamp-2 text-sm leading-relaxed text-white/45">{it.summary}</p>}
            <div className="relative mt-6 flex items-center justify-between text-xs text-white/35">
              <span>
                {it.source} · <span className="font-display">{it.date} {it.time}</span>
              </span>
              <Arrow />
            </div>
            <ArticleActions it={it} />
          </Spotlight>
        </motion.div>
      ))}
    </div>
  )
}

export function Stream({ list }: { list: Item[] }) {
  if (!list.length) return <Empty />
  const groups = list.reduce<Record<string, Item[]>>((a, i) => ((a[i.date] ??= []).push(i), a), {})
  let k = 0
  return (
    <div className="space-y-20">
      {Object.entries(groups).map(([date, g]) => {
        const [year, month, day] = date.split('-')
        return (
          <section key={date} className="grid grid-cols-1 gap-8 md:grid-cols-[180px_1fr]">
            <div className="md:sticky md:top-10 md:self-start">
              <div className="font-display text-[64px] font-light leading-none tracking-tighter text-holo">
                {day}
              </div>
              <div className="mt-2 font-display text-xs tracking-[0.3em] text-white/30">
                {month} / {year}
              </div>

            </div>
            <div className="border-t border-white/10">
              {g.map((it) => {
                const d = k++ * 0.05
                return (
                  <motion.article
                    key={it.dataKey ?? it.id}
          data-card-key={it.dataKey ?? it.id}
                    layout
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0, height: 'auto' }}
                    transition={{ duration: 0.7, ease, delay: Math.min(d, 0.5) }}
                    className="group relative grid grid-cols-[64px_1fr_auto] items-center gap-6 border-b border-white/10 py-7"
                  >
                    <span
                      className="absolute inset-y-0 -left-4 -right-4 origin-left scale-x-0 rounded-2xl opacity-0 transition-all duration-700 ease-out group-hover:scale-x-100 group-hover:opacity-100"
                      style={{ background: `linear-gradient(90deg, ${hues[it.tag]}14, transparent 70%)` }}
                    />
                    <span className="relative font-display text-sm text-white/35 tabular-nums transition-colors group-hover:text-white">
                      {it.time}
                    </span>
                    <div className="relative min-w-0">
                      <div className="mb-2 flex items-center gap-4">
                        <Tag t={it.tag} />
                        <span className="text-[11px] tracking-wider text-white/30">{it.source}</span>
                      </div>
                      <h3 className="text-[19px] font-normal leading-snug text-white/85 transition-all duration-500 group-hover:translate-x-2 group-hover:text-white">
                        <Link to={`/items/${it.id}`} onClick={() => markRead(it.id)}><Scramble text={it.title} delay={Math.min(d, 0.5)} /></Link>
                      </h3>
                      <p className="mt-0 max-h-0 overflow-hidden text-sm leading-relaxed text-white/45 opacity-0 transition-all duration-700 group-hover:mt-2 group-hover:max-h-20 group-hover:translate-x-2 group-hover:opacity-100">
                        {it.summary}
                      </p>
                      <ArticleActions it={it} />
                    </div>
                    <Link to={`/items/${it.id}`} aria-label={`阅读：${it.title}`} className="relative" onClick={() => markRead(it.id)}>
                      <Arrow />
                    </Link>
                  </motion.article>
                )
              })}
            </div>
          </section>
        )
      })}
    </div>
  )
}

export function FrozenCards({ items, variant = 'all', cards }: { items: FeedItemSummary[]; variant?: View; cards?: TimelineCard[] }) {
  const list = cards ? cards.map(c => toWorkbenchItem(c.item, c.group, c.key)) : items.map(i => toWorkbenchItem(i))
  return variant === 'featured' ? <Featured list={list} /> : <Stream list={list} />
}
function Empty() {
  return <div className="py-20 text-center text-white/65">这个筛选下暂时没有内容。<Link to="/all" className="ml-2 text-cyan-200">浏览全部动态</Link></div>
}
