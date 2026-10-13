import assert from "node:assert/strict";
import { after, test } from "node:test";
import { beijingDate, beijingTime } from "@aihot/contracts/time";

const originalWindow = Object.getOwnPropertyDescriptor(globalThis, "window");
after(() => {
  if (originalWindow) Object.defineProperty(globalThis, "window", originalWindow);
  else Reflect.deleteProperty(globalThis, "window");
});

let instance = 0;
async function reader(stars: unknown[] = [], persisted: Record<string, string> = {}) {
  const values = new Map<string, string>([["aihot-starred-items", JSON.stringify(stars)], ...Object.entries(persisted)]);
  let failingKey: string | null = null;
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { localStorage: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => { if (key === failingKey) throw new Error("quota"); values.set(key, value); },
      removeItem: (key: string) => { values.delete(key); },
    } },
  });
  // A fresh module has the same empty snapshot cache as a newly opened browser tab.
  const state: typeof import("../app/lib/local-state.ts") = await import(`../app/lib/local-state.ts?test=${instance++}`);
  return { state, values, fail: (key: string) => { failingKey = key; } };
}

const invalidDates = ["not-a-date", "", "999999-01-01", "+275760-09-13T00:00:00.000Z", null, 42, {}];
const displayDate = (value: string) => `${beijingDate(value)} ${beijingTime(value)}`;

test("import normalizes invalid bookmark dates before persisting without dropping bookmarks", async () => {
  const { state, values } = await reader();
  const before = Date.now();
  const result = state.importBundle(JSON.stringify({ version: 1, starred: invalidDates.map((value, i) => ({
    id: `item-${i}`, title: `Title ${i}`, savedAt: value, publishedAt: value,
  })) }));
  assert.equal(result.starredAdded, invalidDates.length);
  const saved = JSON.parse(values.get(state.KEYS.starred)!);
  assert.equal(saved.length, invalidDates.length);
  for (const item of saved) {
    assert.equal(item.publishedAt, null);
    assert.ok(Date.parse(item.savedAt) >= before && Date.parse(item.savedAt) <= Date.now());
    assert.doesNotThrow(() => displayDate(item.savedAt));
  }
});

test("existing invalid dates are readable, exportable and removable after reopening the page", async () => {
  const { state } = await reader([{ id: "old", title: "Keep this bookmark", savedAt: "broken", publishedAt: "broken" }]);
  const stars = state.getStarred();
  assert.equal(stars.length, 1);
  assert.equal(stars[0]!.title, "Keep this bookmark");
  assert.equal(stars[0]!.publishedAt, null);
  assert.doesNotThrow(() => displayDate(stars[0]!.savedAt));
  assert.strictEqual(state.getStarred(), stars, "normalization preserves stable React snapshots");
  assert.deepEqual(state.exportBundle().starred, stars);
  state.removeStar("old");
  assert.deepEqual(state.getStarred(), []);
});

test("valid dates and existing bookmarks survive import unchanged", async () => {
  const item = { id: "valid", title: "Original title", savedAt: "2026-09-29T08:30:00+08:00", publishedAt: "2026-09-28T23:00:00Z" };
  const { state } = await reader([item]);
  const result = state.importBundle(JSON.stringify({ version: 1, starred: [{ ...item, title: "Replacement", savedAt: "broken" }] }));
  assert.equal(result.starredAdded, 0);
  const [saved] = state.getStarred();
  assert.equal(saved!.title, item.title);
  assert.equal(saved!.savedAt, item.savedAt);
  assert.equal(saved!.publishedAt, item.publishedAt);
});

const reading = { id: "news-1", title: "A real article", sourceName: "Source", publishedAt: null, path: "/items/news-1" };
const fingerprint = "a".repeat(64);

test("old read ids remain intact without inventing history dates or positions", async () => {
  const { state } = await reader([], { "aihot-read-items": '["legacy"]' });
  assert.deepEqual(state.getReadingHistory(), []);
  state.rememberReading(reading);
  assert.deepEqual(state.getReadIds(), ["legacy"]);
  const [visit] = state.getReadingHistory();
  assert.equal(visit!.bodyHash, null);
  assert.equal(visit!.position, 0);
  assert.strictEqual(state.getReadingHistory(), state.getReadingHistory());
});

test("reopening does not overwrite an existing position before the user scrolls", async () => {
  const { state } = await reader();
  assert.equal(state.rememberReading(reading), true);
  assert.equal(state.saveReadingPosition(reading.id, { path: reading.path, position: 0.6, bodyHash: fingerprint, expanded: true }), true);
  state.rememberReading({ ...reading, title: "Changed title" });
  const [saved] = state.getReadingHistory();
  assert.equal(saved!.position, 0.6); assert.equal(saved!.bodyHash, fingerprint);
  assert.equal(saved!.title, "Changed title"); assert.equal(saved!.expanded, true);
});

test("clipboard receipts and manual results are distinct and failures preserve prior state", async () => {
  const { state, fail } = await reader();
  const id = state.recordCopiedTask("read-article", "Read", "https://example.com/article")!;
  assert.ok(id); assert.equal(state.getReadingTasks()[0]!.result, null);
  assert.equal(state.getReadingTasks()[0]!.resultSavedAt, null);
  assert.equal(state.saveTaskResult(id, "My saved result"), true);
  const exact = "\n    Markdown indentation and trailing spaces  \n";
  assert.equal(state.saveTaskResult(id, exact), true);
  assert.equal(state.getReadingTasks()[0]!.result, exact);
  const saved = state.getReadingTasks();
  fail(state.KEYS.tasks);
  assert.equal(state.saveTaskResult(id, "This was not stored"), false);
  assert.strictEqual(state.getReadingTasks(), saved);
  assert.equal(state.recordCopiedTask("read-article", "Read", "More input"), null);
  assert.equal(state.removeReadingTask(id), false);
});

test("personal export/import preserves original dates, positions and results without duplication", async () => {
  const first = await reader();
  first.state.rememberReading(reading);
  first.state.saveReadingPosition(reading.id, { path: reading.path, position: 0.6, bodyHash: fingerprint, expanded: false });
  first.state.toggleFollowedSource("official.source", "Official source");
  const id = first.state.recordCopiedTask("read-article", "Read", "Original input")!;
  first.state.saveTaskResult(id, "Saved result");
  const bundle = first.state.exportBundle();
  const second = await reader();
  const report = second.state.importBundle(JSON.stringify(bundle));
  assert.equal(report.personalAdded, 3); assert.equal(report.personalFailed, false);
  assert.deepEqual(second.state.exportBundle(), bundle);
  assert.equal(second.state.importBundle(JSON.stringify(bundle)).personalAdded, 0);
  second.state.importBundle(JSON.stringify({ version: 1, read: ["legacy"] }));
  assert.deepEqual(second.state.getReadingHistory(), bundle.history);
});

test("malformed imports cannot create unsafe reading links or trusted content fingerprints", async () => {
  const { state } = await reader();
  const report = state.importBundle(JSON.stringify({ version: 1, history: [
    { ...reading, visitedAt: "broken" },
    { ...reading, visitedAt: "2026-10-13T08:00:00Z", path: "javascript:alert(1)", position: 9, bodyHash: "unverified" },
  ] }));
  assert.equal(report.personalSkipped, 1);
  const [item] = state.getReadingHistory();
  assert.equal(item!.path, reading.path); assert.equal(item!.position, 1); assert.equal(item!.bodyHash, null);
});

test("partial import reports personal-storage failure while preserving valid old data", async () => {
  const { state, fail } = await reader();
  fail(state.KEYS.following);
  const report = state.importBundle(JSON.stringify({ version: 1, following: [{ id: "source", name: "Source", followedAt: "2026-10-13T08:00:00Z" }] }));
  assert.equal(report.personalFailed, true); assert.equal(report.personalAdded, 0);
  assert.deepEqual(state.getFollowedSources(), []);
});
