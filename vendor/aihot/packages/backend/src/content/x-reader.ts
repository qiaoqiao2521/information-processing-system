// On-demand enrichment of known X links. No account access, search, analysis or public full-text grant.
import { sql } from "../db.ts";
import { escapeHtml, collapseWhitespace } from "../lib/text.ts";
import { jinaRead, xPostId, type JinaPage } from "../providers/jina.ts";
import { completeReceipt } from "../providers/receipts.ts";
import { contentHash } from "./materials.ts";

/** Reader repeats the post in its H1; require that structure and the previously collected snippet. */
export function confirmedXBody(page: JinaPage, targetUrl: string, reference: string): string | null {
  const postId = xPostId(targetUrl);
  if (!postId || !page.url || xPostId(page.url) !== postId) return null;
  const text = /^# [^\n]+ on X: "(.+)"[ \t]*$/m.exec(page.markdown)?.[1]?.trim();
  if (!text || text.length < 40 || /(?:…|\.\.\.)$/.test(text)) return null;
  const normalize = (value: string) => value.normalize("NFKC").toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
  const prefix = normalize(reference).slice(0, 48);
  if (prefix.length < 20 || !normalize(text).startsWith(prefix)) return null;
  return collapseWhitespace(text);
}

export async function readKnownXBody(articleId: string) {
  const [article] = await sql<{ url: string; title: string; excerpt: string | null; body_status: string }[]>`
    SELECT url, title, excerpt, body_status FROM articles WHERE id = ${articleId}`;
  if (!article || !xPostId(article.url)) throw new Error("Pass an existing article with an X/Twitter post URL");
  if (article.body_status === "ok") return { articleId, status: "skipped" as const };
  const page = await jinaRead(article.url, { purpose: "x_body", subject: `article:${articleId}` });
  const text = confirmedXBody(page, article.url, article.excerpt || article.title);
  return sql.begin(async (tx) => {
    const [row] = await tx<{ title: string; excerpt: string | null; url: string; body_status: string }[]>`
      SELECT title, excerpt, url, body_status FROM articles WHERE id = ${articleId} FOR UPDATE`;
    if (!row || row.url !== article.url) throw new Error("Article changed during X body read");
    if (row.body_status === "ok") {
      await completeReceipt(tx, page.receiptId);
      return { articleId, status: "skipped" as const, receiptId: page.receiptId };
    }
    // Login-only, changed or unfamiliar renderings keep the existing summary and are not retried here.
    if (!text || !confirmedXBody(page, row.url, row.excerpt || row.title)) {
      await tx`UPDATE articles SET body_status = 'unconfirmed', updated_at = now() WHERE id = ${articleId}`;
      await completeReceipt(tx, page.receiptId);
      return { articleId, status: "unconfirmed" as const, receiptId: page.receiptId };
    }
    const hash = contentHash({ title: row.title, bodyText: text, excerpt: row.excerpt });
    const [revised] = await tx<{ revision: number }[]>`
      UPDATE articles SET body_text = ${text}, body_html = ${`<p>${escapeHtml(text)}</p>`}, body_status = 'ok',
        revision = revision + 1, content_hash = ${hash}, updated_at = now()
      WHERE id = ${articleId} RETURNING revision`;
    await tx`INSERT INTO article_revisions (article_id, revision, content_hash, title, body_text)
      VALUES (${articleId}, ${revised!.revision}, ${hash}, ${row.title}, ${text})`;
    await completeReceipt(tx, page.receiptId);
    // Preserve all dates, public summaries and processing state; enriching history does not re-score it.
    return { articleId, status: "ok" as const, bodyChars: text.length, revision: revised!.revision, receiptId: page.receiptId };
  });
}
