import { createHash, timingSafeEqual } from "node:crypto";
import { z } from "zod";
import { sql } from "../db.ts";
import { stableJson } from "../lib/ids.ts";
import { credential } from "../config.ts";

const Draft = z.object({
  request_id: z.string().uuid().toLowerCase(),
  item_id: z.string().regex(/^[\w-]{1,120}$/),
  title: z.string().trim().min(1).max(600),
  source: z.string().trim().min(1).max(200),
  source_url: z.string().url().max(256),
  fingerprint: z.string().regex(/^[a-f0-9]{64}$/),
  basis: z.enum(["full_text", "public_summary"]),
  truncated: z.boolean(),
  model: z.string().min(1).max(120).refine((value) => /MiniMax/i.test(value) && /3\.1/.test(value)),
  conclusion: z.string().trim().min(1).max(2000),
  key_points: z.array(z.string().trim().min(1).max(1000)).length(3),
  entities: z.array(z.string().trim().min(1).max(200)).max(40),
}).strict();

function authorized(token: string, supplied: string | undefined) {
  if (!supplied?.startsWith("Bearer ")) return false;
  const a = Buffer.from(token); const b = Buffer.from(supplied.slice(7));
  return a.length === b.length && timingSafeEqual(a, b);
}

export async function acceptLifeGameDraft(input: unknown, authorization: string | undefined) {
  const token = credential("integrations", "LIFEGAME_SITE_SYNC_TOKEN") ?? "";
  if (token.length < 32 || !authorized(token, authorization)) throw Object.assign(new Error("Unauthorized"), { statusCode: 401 });
  const draft = Draft.parse(input);
  if (draft.source_url !== `https://intel.muqiao.xyz/items/${draft.item_id}`) throw Object.assign(new Error("Invalid source URL"), { statusCode: 400 });
  const id = createHash("sha256").update(draft.request_id).digest("hex").slice(0, 24);
  const [row] = await sql<any[]>`INSERT INTO lifegame_distillations
    (id,request_id,item_id,title,source,source_url,fingerprint,basis,truncated,model,conclusion,key_points,entities)
    VALUES(${id},${draft.request_id},${draft.item_id},${draft.title},${draft.source},${draft.source_url},${draft.fingerprint},${draft.basis},${draft.truncated},${draft.model},${draft.conclusion},${sql.json(draft.key_points)},${sql.json(draft.entities)})
    ON CONFLICT DO NOTHING RETURNING *`;
  if (row) return { id: row.id, request_id: draft.request_id, status: "draft" as const };
  const [existing] = await sql<any[]>`SELECT id,status,item_id,title,source,source_url,fingerprint,basis,truncated,model,conclusion,key_points,entities FROM lifegame_distillations WHERE request_id=${draft.request_id}`;
  if (!existing || stableJson({
    item_id: existing.item_id, title: existing.title, source: existing.source, source_url: existing.source_url,
    fingerprint: existing.fingerprint, basis: existing.basis, truncated: existing.truncated, model: existing.model,
    conclusion: existing.conclusion, key_points: existing.key_points, entities: existing.entities,
  }) !== stableJson({
    item_id: draft.item_id, title: draft.title, source: draft.source, source_url: draft.source_url, fingerprint: draft.fingerprint,
    basis: draft.basis, truncated: draft.truncated, model: draft.model, conclusion: draft.conclusion, key_points: draft.key_points, entities: draft.entities,
  })) throw Object.assign(new Error("Request ID already used for different content"), { code: "conflict" });
  return { id: existing.id, request_id: draft.request_id, status: "draft" as const };
}

export async function listLifeGameDrafts() {
  const rows = await sql`SELECT * FROM lifegame_distillations ORDER BY created_at DESC LIMIT 200`;
  return { rows };
}
