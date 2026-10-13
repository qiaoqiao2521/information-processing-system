import { useEffect, useState, type RefObject } from "react";
import { useSearchParams } from "react-router";
import { canResumeReading, hashReadingContent, readingFraction } from "../../lib/reading-position";
import { getReadingHistory, rememberReading, saveReadingPosition, toggleFollowedSource, useFollowedSources, type LocalReadingItem } from "../../lib/local-state";

export function SourceFollowButton({ id, name }: { id: string; name: string }) {
  const sources = useFollowedSources(), followed = sources.some((v) => v.id === id);
  const [error, setError] = useState("");
  return <span className="inline-flex flex-wrap items-center gap-2">
    <button type="button" aria-pressed={followed} className="rounded-full border border-line-strong px-3 py-1.5 text-[12px] text-accent hover:border-accent" onClick={() => {
      setError(toggleFollowedSource(id, name) ? "" : "未能保存关注，请检查本机存储或关注数量。");
    }}>{followed ? "已关注来源" : "关注来源"}</button>
    {error && <span role="status" className="text-[12px] text-hot">{error}</span>}
  </span>;
}

export function ReadingMemory({ item, article, content }: {
  item: Pick<LocalReadingItem, "id" | "title" | "sourceName" | "publishedAt" | "path">;
  article: RefObject<HTMLElement | null>;
  content: string;
}) {
  const [params] = useSearchParams();
  const requested = params.get("resume") === "1";
  const [saved, setSaved] = useState<LocalReadingItem>();
  const [notice, setNotice] = useState("");
  const [restore, setRestore] = useState<(() => void) | null>(null);
  const { id, title, sourceName, publishedAt, path } = item;

  useEffect(() => {
    let disposed = false, engaged = false, moved = false, hash: string | null = null;
    let timer: ReturnType<typeof setTimeout> | undefined, frame = 0, position = 0, expanded = false;
    const previous = getReadingHistory().find((v) => v.id === id);
    setSaved(undefined); setRestore(null); setNotice("");
    if (!rememberReading({ id, title, sourceName, publishedAt, path })) setNotice("本机存储不可用，阅读记录未保存。");

    const measure = () => {
      const element = article.current;
      if (!element) return;
      position = readingFraction(element.getBoundingClientRect().top + window.scrollY, element.offsetHeight, window.innerHeight, window.scrollY);
      expanded = !!element.querySelector<HTMLDetailsElement>("details[data-reading-body]")?.open;
    };
    const persist = () => {
      if (!engaged || !moved || !hash) return;
      if (!saveReadingPosition(id, { path, position, bodyHash: hash, expanded }) && !disposed) setNotice("本机存储不可用，阅读位置未保存。");
    };
    const scroll = () => {
      if (!engaged) return;
      measure(); moved = true; clearTimeout(timer); timer = setTimeout(persist, 600);
    };
    const engage = () => { engaged = true; setSaved(undefined); };
    const key = (event: KeyboardEvent) => {
      if (["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "].includes(event.key)) engage();
    };
    const flush = () => { clearTimeout(timer); persist(); };
    const visibility = () => { if (document.visibilityState === "hidden") flush(); };
    window.addEventListener("wheel", engage, { passive: true });
    window.addEventListener("touchmove", engage, { passive: true });
    window.addEventListener("keydown", key);
    window.addEventListener("scroll", scroll, { passive: true });
    window.addEventListener("pagehide", flush);
    document.addEventListener("visibilitychange", visibility);

    void hashReadingContent(content).then((value) => {
      if (disposed) return;
      hash = value;
      if (!previous || previous.position <= 0 || engaged) return;
      if (!canResumeReading(previous, path, value)) {
        setNotice("正文或阅读版本已变化，上次位置暂不恢复。");
        if (previous.path === path && previous.bodyHash !== value) {
          saveReadingPosition(id, { path, position: 0, bodyHash: null, expanded: false });
        }
        return;
      }
      const resume = () => {
        const element = article.current;
        if (!element) return;
        const details = element.querySelector<HTMLDetailsElement>("details[data-reading-body]");
        if (details && previous.expanded) details.open = true;
        setSaved(undefined);
        frame = requestAnimationFrame(() => {
          frame = requestAnimationFrame(() => {
            if (disposed || !article.current) return;
            const target = article.current;
            const top = target.getBoundingClientRect().top + window.scrollY;
            engaged = true;
            window.scrollTo({ top: top + Math.max(0, target.offsetHeight - window.innerHeight * 0.65) * previous.position, behavior: "instant" });
            measure(); moved = true; persist(); setSaved(undefined); setNotice("已恢复上次阅读位置。");
          });
        });
      };
      setSaved(previous); setRestore(() => resume);
      if (requested) resume();
    }).catch(() => { if (!disposed) setNotice("无法校验正文，阅读位置暂不恢复。"); });

    return () => {
      disposed = true; clearTimeout(timer); cancelAnimationFrame(frame); persist();
      window.removeEventListener("wheel", engage); window.removeEventListener("touchmove", engage);
      window.removeEventListener("keydown", key); window.removeEventListener("scroll", scroll);
      window.removeEventListener("pagehide", flush); document.removeEventListener("visibilitychange", visibility);
    };
  }, [id, title, sourceName, publishedAt, path, article, content, requested]);

  return <>
    {saved && restore && <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-control border border-line px-3 py-2 text-[13px] text-ink-3">
      <span>上次读到 {Math.round(saved.position * 100)}%</span>
      <button type="button" onClick={restore} className="font-medium text-accent">继续阅读</button>
    </div>}
    {notice && <p role="status" className="mb-4 text-[12px] text-ink-3">{notice}</p>}
  </>;
}
