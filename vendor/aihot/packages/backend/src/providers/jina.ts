// Jina Reader (r.jina.ai): browser-rendered page text, billed in output tokens, reached through the egress
// proxy, always behind receipts and the per-minute/hour/day attempt budget (any zero stops it).
import { credential } from "../config.ts";
import { guardedFetch } from "../lib/http-fetch.ts";
import { paidRequest, ProviderRejectedError } from "./receipts.ts";

export interface JinaPage {
  title: string | null;
  url: string | null;
  publishedTime: string | null;
  markdown: string;
}

/** A restricted deployment buys individual public posts, never searches or account timelines. */
export function xPostId(targetUrl: string): string | null {
  const url = URL.parse(targetUrl);
  if (!url || url.protocol !== "https:" || url.username || url.password || url.port) return null;
  if (!["x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"].includes(url.hostname)) return null;
  return /^\/(?:[A-Za-z0-9_]{1,15}|i)\/status\/(\d+)\/?$/.exec(url.pathname)?.[1] ?? null;
}

export function assertJinaTarget(targetUrl: string, scope: string | null): void {
  if (scope === null || scope === "all") return;
  if (scope !== "x") throw new Error("JINA_SCOPE must be x or all");
  if (!xPostId(targetUrl)) throw new Error("JINA_SCOPE=x permits only HTTPS X/Twitter post URLs");
}

export function parseJinaText(text: string): JinaPage {
  const header = text.split(/\nMarkdown Content:\n/)[0] ?? "";
  const body = text.includes("\nMarkdown Content:\n") ? text.split(/\nMarkdown Content:\n/).slice(1).join("\nMarkdown Content:\n") : text;
  const field = (name: string) => new RegExp(`^${name}:\\s*(.+)$`, "m").exec(header)?.[1]?.trim() ?? null;
  return { title: field("Title"), url: field("URL Source"), publishedTime: field("Published Time"), markdown: body.trim() };
}

/**
 * Reads a page through Jina. The receipt key is the target URL plus the day, so a same-day retry of an
 * article's body or detail reuses it. A listing is read afresh on every fetch (`perRead`): with the day
 * key each listing was read once a day and every later fetch saw the morning's page.
 */
export async function jinaRead(
  targetUrl: string,
  opts: { purpose: string; subject: string; format?: "markdown" | "html"; cacheToleranceSeconds?: number; perRead?: boolean },
): Promise<JinaPage & { receiptId: number; raw: string }> {
  // Reject before receipts/budgets/network, including reuse of an earlier unrestricted receipt.
  assertJinaTarget(targetUrl, credential("collectors", "JINA_SCOPE"));
  const tokenLimit = credential("collectors", "JINA_MAX_TOKENS_PER_REQUEST");
  if (tokenLimit && (!/^\d+$/.test(tokenLimit) || !Number.isSafeInteger(Number(tokenLimit)) || Number(tokenLimit) < 1)) {
    throw new Error("JINA_MAX_TOKENS_PER_REQUEST must be a positive integer");
  }
  const tokenBudget: Record<string, string> = tokenLimit ? { "x-token-budget": tokenLimit } : {};
  const key = credential("collectors", "JINA_API_KEY");
  if (!key) throw new Error("JINA_API_KEY is not configured");
  const base = (credential("collectors", "JINA_BASE_URL") ?? "https://r.jina.ai").replace(/\/$/, "");
  // A listing whose freshness matters (xAI news) caps how old Jina's cached rendering may be.
  const tolerance: Record<string, string> = Number.isInteger(opts.cacheToleranceSeconds) && opts.cacheToleranceSeconds! >= 0 ? { "x-cache-tolerance": String(opts.cacheToleranceSeconds) } : {};
  const now = new Date().toISOString();
  const day = opts.perRead ? now : now.slice(0, 10);
  const receipt = await paidRequest(
    { service: "jina", model: null, purpose: opts.purpose, subject: opts.subject, identity: { url: targetUrl, day, format: opts.format ?? "markdown" }, requestSummary: { url: targetUrl } },
    async () => {
      const res = await guardedFetch(`${base}/${targetUrl}`, {
        headers: { authorization: `Bearer ${key}`, "x-return-format": opts.format ?? "markdown", accept: "text/plain", ...tolerance, ...tokenBudget },
        timeoutMs: 60_000,
        maxBytes: 6 * 1024 * 1024,
      });
      if (res.status === 401 || res.status === 402 || res.status === 403 || res.status === 422 || res.status === 400) {
        throw new ProviderRejectedError(`jina HTTP ${res.status}`, res.status, false);
      }
      if (res.status === 429 || res.status >= 500) throw new ProviderRejectedError(`jina HTTP ${res.status}`, res.status, true);
      const text = res.text();
      // Billed in tokens; estimated at about ¥0.36 per million (a recharge-pack price). Without the usage
      // header nothing is guessed.
      const tokens = Number(res.headers.get("x-usage-tokens")) || null;
      const cost = tokens ? { amount: (tokens / 1e6) * 0.36, currency: "CNY", basis: "estimated" as const } : null;
      return { response: { text: text.slice(0, 2_000_000), status: res.status }, requestId: res.headers.get("x-request-id"), usage: { bytes: res.body.length, tokens }, cost };
    },
  );
  const raw = String((receipt.response as { text?: string })?.text ?? "");
  return { ...parseJinaText(raw), receiptId: receipt.receiptId, raw };
}
