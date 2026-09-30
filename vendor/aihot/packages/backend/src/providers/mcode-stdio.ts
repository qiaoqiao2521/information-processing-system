// A single operator-started SSH process exchanges model requests with the local CLI.
// No listener, database credentials or CLI account material crosses the connection.
import { createInterface } from "node:readline";
import { randomUUID } from "node:crypto";
import type { Readable, Writable } from "node:stream";

export const MCODE_PREFIX = "AIHOT_MCODE ";
export class McodeChannel {
  private pending = new Map<string, { resolve: (value: Record<string, unknown>) => void; reject: (error: Error) => void; timer: NodeJS.Timeout }>();
  private closed = false;
  private lines: ReturnType<typeof createInterface>;
  private output: Writable;
  constructor(input: Readable, output: Writable) {
    this.output = output;
    this.lines = createInterface({ input });
    this.lines.on("line", (line) => {
      try {
        const reply = JSON.parse(line) as { id?: string; response?: Record<string, unknown>; error?: string };
        const item = reply.id ? this.pending.get(reply.id) : undefined;
        if (!item) return;
        this.pending.delete(reply.id!);
        clearTimeout(item.timer);
        if (reply.error) item.reject(new Error(`Local mcode failed: ${reply.error.slice(0, 200)}`));
        else if (reply.response?.choices) item.resolve(reply.response);
        else item.reject(new Error("Invalid local mcode response"));
      } catch { this.fail(new Error("Invalid JSON on local mcode channel")); }
    });
    this.lines.on("close", () => this.fail(new Error("Local mcode channel disconnected; no automatic resend")));
    input.on("error", () => this.fail(new Error("Local mcode input failed")));
    output.on("error", () => this.fail(new Error("Local mcode output failed")));
  }
  private fail(error: Error) {
    this.closed = true;
    for (const item of this.pending.values()) { clearTimeout(item.timer); item.reject(error); }
    this.pending.clear();
  }
  request(body: Record<string, unknown>, timeoutMs = 300_000): Promise<Record<string, unknown>> {
    if (this.closed) return Promise.reject(new Error("Local mcode channel is closed"));
    const id = randomUUID();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error("Local mcode timed out; no automatic resend")); }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.output.write(`${MCODE_PREFIX}${JSON.stringify({ id, body })}\n`);
    });
  }
  close() { this.fail(new Error("Local mcode channel closed")); this.lines.close(); }
}
let channel: McodeChannel | undefined;
export function requestMcode(body: Record<string, unknown>) {
  channel ??= new McodeChannel(process.stdin, process.stdout);
  return channel.request(body);
}
export function closeMcode() { channel?.close(); }
