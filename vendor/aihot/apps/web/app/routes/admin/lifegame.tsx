import { SITE } from "@aihot/industry/site";
import type { Route } from "./+types/lifegame";
import { adminGet } from "../../lib/admin.server";
import { AdminPage, Badge, Card, Empty, Time } from "../../features/admin/ui";

interface Draft {
  id: string; request_id: string; item_id: string; title: string; source: string; source_url: string;
  fingerprint: string; basis: "full_text" | "public_summary"; truncated: boolean; model: string;
  conclusion: string; key_points: string[]; entities: string[]; status: "draft"; created_at: string;
}

export async function loader({ request }: Route.LoaderArgs) {
  return adminGet<{ rows: Draft[] }>(request, "/api/admin/lifegame-drafts");
}

export const meta: Route.MetaFunction = () => [{ title: `LifeGame 草稿 · ${SITE.name} 后台` }];

export default function LifeGameDrafts({ loaderData }: Route.ComponentProps) {
  return <AdminPage title="LifeGame 整理草稿" subtitle="仅管理员可见。App 同步的 MiniMax 3.1 速读结果保存在个人草稿区，不会自动公开。">
    <div className="space-y-4">
      {loaderData.rows.map((row) => <Card key={row.id}>
        <div className="flex flex-wrap items-center gap-2 text-xs text-ink-3">
          <Badge tone="accent">个人草稿</Badge><Time at={row.created_at} />
          <span>{row.model}</span><span>{row.basis === "full_text" ? "基于公开正文" : "基于公开摘要"}{row.truncated ? " · 正文已截断" : ""}</span>
        </div>
        <h2 className="mt-3 text-base font-semibold text-ink">{row.title}</h2>
        <p className="mt-1 text-sm text-ink-3">{row.source} · <a href={row.source_url} target="_blank" rel="noreferrer" className="text-accent hover:underline">打开来源网站</a></p>
        <section className="mt-4"><h3 className="text-sm font-semibold text-ink">核心结论</h3><p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-ink-2">{row.conclusion}</p></section>
        <section className="mt-4"><h3 className="text-sm font-semibold text-ink">3 条看点</h3><ol className="mt-1 list-decimal space-y-1 pl-5 text-sm leading-relaxed text-ink-2">{row.key_points.map((point, i) => <li key={i}>{point}</li>)}</ol></section>
        {!!row.entities.length && <section className="mt-4"><h3 className="text-sm font-semibold text-ink">技术与机构实体</h3><p className="mt-1 text-sm text-ink-2">{row.entities.join(" · ")}</p></section>}
        <p className="mt-4 border-t border-line pt-3 text-xs text-ink-4">来源指纹：{row.fingerprint.slice(0, 16)}…</p>
      </Card>)}
      {!loaderData.rows.length && <Card><Empty>还没有 LifeGame 整理草稿。App 中打开一篇网页，按下“开始整理”并选择同步后，结果会出现在这里。</Empty></Card>}
    </div>
  </AdminPage>;
}
