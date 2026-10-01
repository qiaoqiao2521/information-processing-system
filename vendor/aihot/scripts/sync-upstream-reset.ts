import { refreshUpstreamReset } from "../packages/backend/src/monitor/upstream.ts";
import { closeDb } from "../packages/backend/src/db.ts";
try { console.log(JSON.stringify(await refreshUpstreamReset())); } finally { await closeDb(); }
