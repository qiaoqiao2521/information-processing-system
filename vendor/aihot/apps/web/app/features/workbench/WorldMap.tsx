import { useEffect, useRef } from 'react'
import { geoNaturalEarth1, geoPath, geoInterpolate } from 'd3-geo'
import { feature } from 'topojson-client'
import land110 from 'world-atlas/land-110m.json'

// source → city coordinates [lon, lat]
const nodes: Record<string, [number, number]> = {
  OpenAI: [-122.42, 37.77],
  Anthropic: [-122.2, 37.5],
  'Google DeepMind': [-0.13, 51.5],
  'Meta AI': [-74.0, 40.71],
  'Hugging Face': [2.35, 48.86],
  arXiv: [-76.5, 42.44],
  机器之心: [121.47, 31.23],
  量子位: [116.4, 39.9],
}
const hub: [number, number] = [114.06, 22.54]
const extra: [number, number][] = [
  [139.69, 35.68], [103.82, 1.35], [77.2, 28.6], [-46.63, -23.55], [151.2, -33.87], [37.62, 55.75], [55.27, 25.2], [-79.38, 43.65],
]

type Arc = { from: [number, number]; to: [number, number]; t: number; speed: number; hot: boolean }

export default function WorldMap({ pulse }: { pulse: { source: string; n: number } | null }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const arcs = useRef<Arc[]>([])
  const rings = useRef<{ p: [number, number]; t: number }[]>([])

  useEffect(() => {
    if (!pulse) return
    const from = nodes[pulse.source]
    if (!from) return
    arcs.current.push({ from, to: hub, t: 0, speed: 0.006, hot: true })
    rings.current.push({ p: from, t: 0 })
  }, [pulse])

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const c = ref.current!
    const g = c.getContext('2d')
    if (!g) return
    const dpr = Math.min(devicePixelRatio, 2)
    const land = feature(land110 as any, (land110 as any).objects.land) as any
    let proj = geoNaturalEarth1()
    let dots: [number, number][] = []
    let raf = 0

    const build = () => {
      const w = (c.width = innerWidth * dpr)
      const h = (c.height = innerHeight * dpr)
      proj = geoNaturalEarth1().fitExtent([[w * 0.02, h * 0.08], [w * 0.98, h * 0.98]], { type: 'Sphere' } as any)
      const off = document.createElement('canvas')
      off.width = w
      off.height = h
      const o = off.getContext('2d')!
      o.fillStyle = '#fff'
      o.beginPath()
      geoPath(proj, o)(land)
      o.fill()
      const data = o.getImageData(0, 0, w, h).data
      const step = 7 * dpr
      dots = []
      for (let y = 0; y < h; y += step)
        for (let x = (y / step) % 2 ? step / 2 : 0; x < w; x += step)
          if (data[((y | 0) * w + (x | 0)) * 4 + 3] > 128) dots.push([x, y])
    }
    build()
    addEventListener('resize', build)

    const all = [...Object.values(nodes), ...extra]
    const spawn = () => {
      if (arcs.current.filter((a) => !a.hot).length < 9) {
        const a = all[(Math.random() * all.length) | 0]
        let b = all[(Math.random() * all.length) | 0]
        if (a === b) b = hub
        arcs.current.push({ from: a, to: b, t: 0, speed: 0.003 + Math.random() * 0.004, hot: false })
      }
    }

    const draw = (now: number) => {
      const w = c.width
      const h = c.height
      g.clearRect(0, 0, w, h)
      g.fillStyle = 'rgba(160,200,215,0.16)'
      for (const [x, y] of dots) g.fillRect(x, y, 1.6 * dpr, 1.6 * dpr)

      if (Math.random() < 0.04) spawn()

      // arcs
      arcs.current = arcs.current.filter((a) => a.t < 1.6)
      for (const a of arcs.current) {
        a.t += a.speed
        const ip = geoInterpolate(a.from, a.to)
        const head = Math.min(a.t, 1)
        const tail = Math.max(0, a.t - 0.6)
        const seg = 40
        const col = a.hot ? '255,181,71' : '103,232,249'
        g.lineWidth = (a.hot ? 1.6 : 1) * dpr
        let prev: [number, number] | null = null
        for (let i = 0; i <= seg; i++) {
          const k = tail + ((head - tail) * i) / seg
          const p = proj(ip(k))!
          // lift arc off the surface
          const lift = Math.sin(k * Math.PI) * 60 * dpr
          const pt: [number, number] = [p[0], p[1] - lift]
          if (prev) {
            g.strokeStyle = `rgba(${col},${(i / seg) * (a.hot ? 0.9 : 0.45)})`
            g.beginPath()
            g.moveTo(prev[0], prev[1])
            g.lineTo(pt[0], pt[1])
            g.stroke()
          }
          prev = pt
        }
        if (a.t < 1 && prev) {
          g.fillStyle = `rgba(${col},1)`
          g.shadowColor = `rgb(${col})`
          g.shadowBlur = 12 * dpr
          g.beginPath()
          g.arc(prev[0], prev[1], (a.hot ? 2.6 : 1.6) * dpr, 0, 7)
          g.fill()
          g.shadowBlur = 0
        }
        if (a.hot && a.t >= 1 && a.t - a.speed < 1) rings.current.push({ p: a.to, t: 0 })
      }

      // nodes
      const blink = (Math.sin(now / 600) + 1) / 2
      for (const n of all) {
        const [x, y] = proj(n)!
        g.fillStyle = `rgba(103,232,249,${0.5 + blink * 0.4})`
        g.fillRect(x - 1.5 * dpr, y - 1.5 * dpr, 3 * dpr, 3 * dpr)
      }
      const [hx, hy] = proj(hub)!
      g.strokeStyle = 'rgba(255,181,71,0.8)'
      g.lineWidth = dpr
      g.strokeRect(hx - 5 * dpr, hy - 5 * dpr, 10 * dpr, 10 * dpr)
      g.fillStyle = 'rgba(255,181,71,0.9)'
      g.font = `${10 * dpr}px "JetBrains Mono", monospace`
      g.fillText('HUB/MUQIAO', hx + 10 * dpr, hy + 3 * dpr)

      // pulse rings
      rings.current = rings.current.filter((r) => r.t < 1)
      for (const r of rings.current) {
        r.t += 0.012
        const [x, y] = proj(r.p)!
        g.strokeStyle = `rgba(255,181,71,${1 - r.t})`
        g.beginPath()
        g.arc(x, y, r.t * 40 * dpr, 0, 7)
        g.stroke()
      }
      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => (cancelAnimationFrame(raf), removeEventListener('resize', build))
  }, [])

  return <canvas aria-hidden="true" ref={ref} className="absolute inset-0 h-full w-full" />
}
