import assert from "node:assert/strict";
import test from "node:test";
import { canResumeReading, hashReadingContent, readingFraction } from "../app/lib/reading-position.ts";
import type { LocalReadingItem } from "../app/lib/local-state.ts";

test("resume requires matching actual body fingerprint and language path", async () => {
  const hash = await hashReadingContent("actual body");
  assert.match(hash, /^[a-f0-9]{64}$/);
  const saved: LocalReadingItem = { id: "news", title: "Title", sourceName: "Source", visitedAt: "2026-10-13T08:00:00Z", publishedAt: null, path: "/items/news", position: 0.5, bodyHash: hash, expanded: false };
  assert.equal(canResumeReading(saved, saved.path, hash), true);
  assert.equal(canResumeReading(saved, saved.path, await hashReadingContent("corrected body")), false);
  assert.equal(canResumeReading(saved, "/items/news/original", hash), false);
  assert.equal(canResumeReading({ ...saved, bodyHash: null }, saved.path, hash), false);
});

test("reading fraction is clamped to the article and handles short bodies", () => {
  assert.equal(readingFraction(200, 2400, 1000, 1075), 0.5);
  assert.equal(readingFraction(200, 2400, 1000, 0), 0);
  assert.equal(readingFraction(200, 2400, 1000, 5000), 1);
  assert.equal(readingFraction(200, 100, 1000, 400), 0);
});
