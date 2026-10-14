import type { FastifyInstance } from "fastify";
import { acceptLifeGameDraft } from "@aihot/backend/admin/lifegame-drafts";
import { sendProblem } from "../http/respond.ts";

export function registerLifeGame(app: FastifyInstance) {
  app.post("/api/integrations/lifegame/distillations", { bodyLimit: 64 * 1024 }, async (req, reply) => {
    reply.header("Cache-Control", "no-store");
    try {
      const result = await acceptLifeGameDraft(req.body, req.headers.authorization);
      return reply.code(200).send(result);
    } catch (error) {
      const status = (error as { statusCode?: number }).statusCode;
      if (status === 401) return sendProblem(req, reply, { status: 401, code: "unauthorized", detail: "Unauthorized." });
      if (status === 400 || error instanceof Error && error.name === "ZodError") return sendProblem(req, reply, { status: 400, code: "invalid_request", detail: "Invalid draft." });
      if ((error as { code?: string }).code === "conflict") return sendProblem(req, reply, { status: 409, code: "conflict", detail: "Request ID already used." });
      req.log.error({ err: error }, "LifeGame integration failed");
      return sendProblem(req, reply, { status: 503, code: "temporarily_unavailable", detail: "Temporarily unavailable." });
    }
  });
}
