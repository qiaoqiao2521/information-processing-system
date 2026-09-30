import assert from "node:assert/strict";
import { PassThrough } from "node:stream";
import { test } from "node:test";
import { McodeChannel, MCODE_PREFIX } from "../packages/backend/src/providers/mcode-stdio.ts";

test("mcode replies correlate concurrent calls even when they arrive out of order", async () => {
  const input = new PassThrough(); const output = new PassThrough();
  const frames: Array<{ id: string }> = [];
  output.on("data", (data) => frames.push(JSON.parse(String(data).slice(MCODE_PREFIX.length))));
  const channel = new McodeChannel(input, output);
  const one = channel.request({ messages: ["one"] }); const two = channel.request({ messages: ["two"] });
  input.write(JSON.stringify({ id: frames[1]!.id, response: { choices: ["two"] } }) + "\n");
  input.write(JSON.stringify({ id: frames[0]!.id, response: { choices: ["one"] } }) + "\n");
  assert.deepEqual(await one, { choices: ["one"] }); assert.deepEqual(await two, { choices: ["two"] });
  channel.close();
});
test("lost or invalid transport rejects rather than resending the model request", async () => {
  const input = new PassThrough(); const output = new PassThrough();
  const channel = new McodeChannel(input, output);
  const pending = channel.request({});
  input.write("not json\n");
  await assert.rejects(pending, /Invalid JSON/);
  await assert.rejects(channel.request({}), /closed/);
  channel.close();
  const otherInput = new PassThrough(); const other = new McodeChannel(otherInput, new PassThrough());
  const disconnected = other.request({}); otherInput.end();
  await assert.rejects(disconnected, /disconnected/); other.close();
});
test("a local CLI timeout remains an unknown outcome and is not retried", async () => {
  const channel = new McodeChannel(new PassThrough(), new PassThrough());
  await assert.rejects(channel.request({}, 5), /timed out; no automatic resend/); channel.close();
});
