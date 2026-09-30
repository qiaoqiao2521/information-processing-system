import { closeDb } from "@aihot/backend/db";
import { readKnownXBody } from "@aihot/backend/content/x-reader";

const [id, ...extra] = process.argv.slice(2);
if (!id || extra.length) throw new Error("Pass exactly one existing X article ID; no search or bulk read");
try {
  console.log(JSON.stringify(await readKnownXBody(id)));
} finally { await closeDb(); }
