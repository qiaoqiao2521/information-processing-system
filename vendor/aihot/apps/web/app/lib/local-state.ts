// Personal records stay in this browser. Public content is fetched through the site API as usual.
// Keep existing keys and formats; personal actions report storage failures to their callers.
import { useSyncExternalStore } from "react";
import { beijingDate } from "@aihot/contracts/time";

export const KEYS = {
  starred: "aihot-starred-items",
  read: "aihot-read-items",
  theme: "aihot-theme",
  changelogSeen: "aihot-changelog-seen-version",
  feedbackDraft: "aihot-feedback-draft-v1",
  history: "aihot-reading-history-v1",
  tasks: "aihot-reading-tasks-v1",
  following: "aihot-followed-sources-v1",
} as const;

export const STARRED_LIMIT = 500;
export const READ_LIMIT = 5000;
export const IMPORT_MAX_CHARS = 2_000_000;
const ID_PATTERN = /^[a-zA-Z0-9_-]{1,80}$/;

export interface LocalStarredItem {
  id: string;
  title: string;
  summary: string | null;
  sourceName: string;
  savedAt: string;
  publishedAt: string | null;
  score: number | null;
  aiSelected: boolean;
}

function storage(kind: "local" | "session"): Storage | null {
  try {
    const s = kind === "local" ? window.localStorage : window.sessionStorage;
    return s;
  } catch {
    return null;
  }
}

function readRaw(key: string, kind: "local" | "session" = "local"): string | null {
  try {
    return storage(kind)?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

function writeRaw(key: string, value: string | null, kind: "local" | "session" = "local"): boolean {
  try {
    const s = storage(kind);
    if (!s) return false;
    if (value === null) s.removeItem(key);
    else s.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

// --- change notification (same tab via events, other tabs via the storage event) ---
const listeners = new Map<string, Set<() => void>>();
let subscribers = 0;
function emit(key?: string) {
  for (const [subscribedKey, callbacks] of listeners) {
    if (key === undefined || key === subscribedKey) for (const callback of callbacks) callback();
  }
}
function onStorage(event: StorageEvent) {
  if (event.storageArea && event.storageArea !== storage("local")) return;
  if (event.key === null) cache.clear();
  else cache.delete(event.key);
  // Clear the snapshot once, before notifying all cards. Each key is parsed at most once.
  emit(event.key ?? undefined);
}
function subscribeKey(key: string) {
  return (listener: () => void) => {
    let callbacks = listeners.get(key);
    if (!callbacks) listeners.set(key, callbacks = new Set());
    callbacks.add(listener);
    if (subscribers++ === 0) window.addEventListener("storage", onStorage);
    return () => {
      callbacks.delete(listener);
      if (callbacks.size === 0) listeners.delete(key);
      if (--subscribers === 0) window.removeEventListener("storage", onStorage);
    };
  };
}
const subscribeStarred = subscribeKey(KEYS.starred);
const subscribeRead = subscribeKey(KEYS.read);
const subscribeTheme = subscribeKey(KEYS.theme);
const subscribeChangelog = subscribeKey(KEYS.changelogSeen);
const subscribeHistory = subscribeKey(KEYS.history);
const subscribeTasks = subscribeKey(KEYS.tasks);
const subscribeFollowing = subscribeKey(KEYS.following);

// Snapshot cache so useSyncExternalStore gets stable references between changes.
const cache = new Map<string, unknown>();
function cached<T>(key: string, compute: () => T): T {
  if (!cache.has(key)) cache.set(key, compute());
  return cache.get(key) as T;
}
function invalidate(key: string) {
  cache.delete(key);
  emit(key);
}

// --- starred ---
function isStarredItem(v: unknown): v is LocalStarredItem {
  if (!v || typeof v !== "object") return false;
  const o = v as Record<string, unknown>;
  return typeof o.id === "string" && ID_PATTERN.test(o.id) && typeof o.title === "string";
}

/** Imported and already stored dates must be representable in the page's display timezone. */
function isDisplayableDate(value: unknown): value is string {
  if (typeof value !== "string") return false;
  try {
    beijingDate(value);
    return true;
  } catch {
    return false;
  }
}

function normalizeStarred(v: Record<string, unknown>): LocalStarredItem {
  return {
    id: String(v.id),
    title: String(v.title),
    summary: typeof v.summary === "string" ? v.summary : null,
    sourceName: typeof v.sourceName === "string" ? v.sourceName : "",
    savedAt: isDisplayableDate(v.savedAt) ? v.savedAt : new Date().toISOString(),
    publishedAt: isDisplayableDate(v.publishedAt) ? v.publishedAt : null,
    score: typeof v.score === "number" ? v.score : null,
    aiSelected: v.aiSelected === true,
  };
}

export function getStarred(): LocalStarredItem[] {
  return cached(KEYS.starred, () => {
    const raw = readRaw(KEYS.starred);
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.filter(isStarredItem).map((v) => normalizeStarred(v as unknown as Record<string, unknown>)).slice(0, STARRED_LIMIT);
    } catch {
      return [];
    }
  });
}

const starredSetCache = { items: null as LocalStarredItem[] | null, ids: new Set<string>() };
export function isStarred(id: string): boolean {
  const items = getStarred();
  if (starredSetCache.items !== items) {
    starredSetCache.items = items;
    starredSetCache.ids = new Set(items.map((item) => item.id));
  }
  return starredSetCache.ids.has(id);
}

export function toggleStar(item: Omit<LocalStarredItem, "savedAt">): boolean {
  const list = getStarred();
  const exists = list.some((s) => s.id === item.id);
  const next = exists ? list.filter((s) => s.id !== item.id) : [{ ...item, savedAt: new Date().toISOString() }, ...list].slice(0, STARRED_LIMIT);
  writeRaw(KEYS.starred, JSON.stringify(next));
  invalidate(KEYS.starred);
  return !exists;
}

export function removeStar(id: string) {
  writeRaw(KEYS.starred, JSON.stringify(getStarred().filter((s) => s.id !== id)));
  invalidate(KEYS.starred);
}

// --- read items (LRU, newest first) ---
export function getReadIds(): string[] {
  return cached(KEYS.read, () => {
    const raw = readRaw(KEYS.read);
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.filter((v): v is string => typeof v === "string" && ID_PATTERN.test(v)).slice(0, READ_LIMIT) : [];
    } catch {
      return [];
    }
  });
}

const readSetCache = { ids: null as string[] | null, set: new Set<string>() };
export function getReadSet(): Set<string> {
  const ids = getReadIds();
  if (readSetCache.ids !== ids) {
    readSetCache.ids = ids;
    readSetCache.set = new Set(ids);
  }
  return readSetCache.set;
}

export function markRead(id: string) {
  if (!ID_PATTERN.test(id)) return;
  const ids = getReadIds();
  if (ids[0] === id) return;
  const next = [id, ...ids.filter((v) => v !== id)].slice(0, READ_LIMIT);
  writeRaw(KEYS.read, JSON.stringify(next));
  invalidate(KEYS.read);
}

// --- personal reading workspace (same browser, no reader account) ---
export const HISTORY_LIMIT = 200;
export const TASK_LIMIT = 30;
export const FOLLOWING_LIMIT = 200;
export const MATERIAL_LIMIT = 18_000;

export interface LocalReadingItem {
  id: string;
  title: string;
  sourceName: string;
  visitedAt: string;
  publishedAt: string | null;
  path: string;
  position: number;
  bodyHash: string | null;
  expanded: boolean;
}

export interface LocalReadingTask {
  id: string;
  skillId: string;
  skillName: string;
  input: string;
  copiedAt: string;
  result: string | null;
  resultSavedAt: string | null;
}

export interface LocalFollowedSource { id: string; name: string; followedAt: string }

function readingItem(v: unknown): LocalReadingItem | null {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, unknown>;
  if (typeof o.id !== "string" || !ID_PATTERN.test(o.id) || typeof o.title !== "string" || !isDisplayableDate(o.visitedAt)) return null;
  const path = o.path === `/items/${o.id}/original` ? o.path : `/items/${o.id}`;
  return { id: o.id, title: o.title.slice(0, 600), sourceName: typeof o.sourceName === "string" ? o.sourceName.slice(0, 200) : "",
    visitedAt: o.visitedAt, publishedAt: isDisplayableDate(o.publishedAt) ? o.publishedAt : null, path,
    position: typeof o.position === "number" && Number.isFinite(o.position) ? Math.max(0, Math.min(1, o.position)) : 0,
    bodyHash: typeof o.bodyHash === "string" && /^[a-f0-9]{64}$/.test(o.bodyHash) ? o.bodyHash : null, expanded: o.expanded === true };
}

function readingTask(v: unknown): LocalReadingTask | null {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, unknown>;
  if (typeof o.id !== "string" || !ID_PATTERN.test(o.id) || typeof o.skillId !== "string" || !ID_PATTERN.test(o.skillId)
    || typeof o.skillName !== "string" || typeof o.input !== "string" || !o.input.trim() || !isDisplayableDate(o.copiedAt)) return null;
  const result = typeof o.result === "string" && o.result.trim() ? o.result.slice(0, MATERIAL_LIMIT) : null;
  return { id: o.id, skillId: o.skillId, skillName: o.skillName.slice(0, 200), input: o.input.slice(0, MATERIAL_LIMIT), copiedAt: o.copiedAt,
    result, resultSavedAt: result && isDisplayableDate(o.resultSavedAt) ? o.resultSavedAt : null };
}

function followedSource(v: unknown): LocalFollowedSource | null {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, unknown>;
  if (typeof o.id !== "string" || !/^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$/.test(o.id) || typeof o.name !== "string" || !isDisplayableDate(o.followedAt)) return null;
  return { id: o.id, name: o.name.slice(0, 200), followedAt: o.followedAt };
}

function personalList<T extends { id: string }>(key: string, limit: number, normalize: (v: unknown) => T | null): T[] {
  return cached(key, () => {
    try {
      const raw: unknown = JSON.parse(readRaw(key) ?? "[]");
      if (!Array.isArray(raw)) return [];
      const items: T[] = [], seen = new Set<string>();
      for (const value of raw) {
        const item = normalize(value);
        if (!item || seen.has(item.id)) continue;
        seen.add(item.id); items.push(item);
        if (items.length >= limit) break;
      }
      return items;
    } catch { return []; }
  });
}

function savePersonal(key: string, items: unknown[]): boolean {
  if (!writeRaw(key, JSON.stringify(items))) return false;
  invalidate(key);
  return true;
}

export function getReadingHistory() { return personalList(KEYS.history, HISTORY_LIMIT, readingItem); }
export function getReadingTasks() { return personalList(KEYS.tasks, TASK_LIMIT, readingTask); }
export function getFollowedSources() { return personalList(KEYS.following, FOLLOWING_LIMIT, followedSource); }

/** Visiting updates metadata and time, but keeps the last deliberately saved reading position. */
export function rememberReading(item: Pick<LocalReadingItem, "id" | "title" | "sourceName" | "publishedAt" | "path">): boolean {
  const history = getReadingHistory(), previous = history.find((v) => v.id === item.id);
  const value = readingItem({ ...item, visitedAt: new Date().toISOString(), path: previous?.path ?? item.path,
    position: previous?.position ?? 0, bodyHash: previous?.bodyHash ?? null, expanded: previous?.expanded ?? false });
  return !!value && savePersonal(KEYS.history, [value, ...history.filter((v) => v.id !== item.id)].slice(0, HISTORY_LIMIT));
}

export function saveReadingPosition(id: string, value: Pick<LocalReadingItem, "path" | "position" | "bodyHash" | "expanded">): boolean {
  const history = getReadingHistory(), item = history.find((v) => v.id === id);
  if (!item) return false;
  const updated = readingItem({ ...item, ...value });
  return !!updated && savePersonal(KEYS.history, history.map((v) => v.id === id ? updated : v));
}

export function removeReading(id: string): boolean { return savePersonal(KEYS.history, getReadingHistory().filter((v) => v.id !== id)); }

/** Called only after clipboard success; it does not represent a model run. */
export function recordCopiedTask(skillId: string, skillName: string, input: string): string | null {
  const id = globalThis.crypto?.randomUUID?.();
  if (!id) return null;
  const task = readingTask({ id, skillId, skillName, input, copiedAt: new Date().toISOString(), result: null, resultSavedAt: null });
  return task && savePersonal(KEYS.tasks, [task, ...getReadingTasks()].slice(0, TASK_LIMIT)) ? id : null;
}

export function saveTaskResult(id: string, result: string): boolean {
  if (result.length > MATERIAL_LIMIT || !getReadingTasks().some((v) => v.id === id)) return false;
  return savePersonal(KEYS.tasks, getReadingTasks().map((v) => v.id === id
    ? { ...v, result: result.trim() ? result : null, resultSavedAt: result.trim() ? new Date().toISOString() : null } : v));
}

export function removeReadingTask(id: string): boolean { return savePersonal(KEYS.tasks, getReadingTasks().filter((v) => v.id !== id)); }

export function toggleFollowedSource(id: string, name: string): boolean {
  const list = getFollowedSources(), exists = list.some((v) => v.id === id);
  const source = followedSource({ id, name, followedAt: new Date().toISOString() });
  if (!source || (!exists && list.length >= FOLLOWING_LIMIT)) return false;
  return savePersonal(KEYS.following, exists ? list.filter((v) => v.id !== id) : [source, ...list]);
}

// --- theme ---
export type ThemePreference = "light" | "dark" | null;

export function getThemePreference(): ThemePreference {
  const v = readRaw(KEYS.theme);
  if (v === "light" || v === "dark") return v;
  // Tolerate a JSON-quoted value written by other code paths.
  if (v === '"light"' || v === '"dark"') return JSON.parse(v);
  return null;
}

export function setThemePreference(pref: ThemePreference) {
  writeRaw(KEYS.theme, pref);
  invalidate(KEYS.theme);
}

export function resolvedTheme(pref: ThemePreference = getThemePreference()): "light" | "dark" {
  if (pref) return pref;
  try {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  } catch {
    return "light";
  }
}

/** Inline script run before paint so the first frame already has the reader's theme. */
export const THEME_BOOT_SCRIPT = `(function(){try{var t=localStorage.getItem('${KEYS.theme}');if(t==='"light"'||t==='"dark"')t=JSON.parse(t);if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}document.documentElement.setAttribute('data-theme',t)}catch(e){document.documentElement.setAttribute('data-theme','light')}})();`;

// --- changelog red dot ---
export function getChangelogSeen(): string | null {
  const v = readRaw(KEYS.changelogSeen);
  return v && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(v) ? v : null;
}

export function setChangelogSeen(version: string) {
  writeRaw(KEYS.changelogSeen, version);
  invalidate(KEYS.changelogSeen);
}

// --- export / import (version 1) ---
export interface ExportBundle {
  version: 1;
  starred: LocalStarredItem[];
  read: string[];
  theme: "light" | "dark" | "auto" | null;
  history?: LocalReadingItem[];
  tasks?: LocalReadingTask[];
  following?: LocalFollowedSource[];
}

export function exportBundle(): ExportBundle {
  const pref = getThemePreference();
  return { version: 1, starred: getStarred(), read: getReadIds(), theme: pref ?? "auto", history: getReadingHistory(), tasks: getReadingTasks(), following: getFollowedSources() };
}

export interface ImportReport {
  starredAdded: number;
  starredSkipped: number;
  readAdded: number;
  readSkipped: number;
  themeApplied: boolean;
  /** The stars were saved but the read marks could not be (storage full or unavailable). */
  readFailed: boolean;
  personalAdded: number;
  personalSkipped: number;
  personalFailed: boolean;
}

/** Merge: existing stars are not overwritten, read ids are unioned, theme only if unset. */
export function importBundle(text: string): ImportReport {
  if (text.length > IMPORT_MAX_CHARS) throw new Error("文件过大（上限 2,000,000 字符）");
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("不是有效的 JSON 文件");
  }
  const d = data as Partial<ExportBundle>;
  if (!d || typeof d !== "object" || d.version !== 1) throw new Error("文件格式不对（需要 version: 1）");
  return mergeLocalData({
    starred: Array.isArray(d.starred) ? d.starred : [],
    read: Array.isArray(d.read) ? d.read : [],
    theme: d.theme ?? null,
    history: d.history, tasks: d.tasks, following: d.following,
  });
}

export function mergeLocalData(incoming: { starred: unknown[]; read: unknown[]; theme: unknown; history?: unknown; tasks?: unknown; following?: unknown }): ImportReport {
  const current = getStarred();
  const have = new Set(current.map((s) => s.id));
  const additions: LocalStarredItem[] = [];
  let starredSkipped = 0;
  for (const s of incoming.starred) {
    if (!isStarredItem(s)) { starredSkipped++; continue; }
    if (have.has(s.id)) continue;
    have.add(s.id);
    additions.push(normalizeStarred(s as unknown as Record<string, unknown>));
  }
  const room = Math.max(0, STARRED_LIMIT - current.length);
  const accepted = additions.slice(0, room);
  starredSkipped += additions.length - accepted.length;
  const mergedStarred = [...current, ...accepted].sort((a, b) => Date.parse(b.savedAt) - Date.parse(a.savedAt));
  // An import is reported only after it was written; a failure here leaves the browser as it was.
  if (!writeRaw(KEYS.starred, JSON.stringify(mergedStarred))) throw new Error("浏览器存储已满或不可用，这次没有导入任何内容。");

  const readIds = getReadIds();
  const readHave = new Set(readIds);
  const readAdditions: string[] = [];
  let readSkipped = 0;
  for (const id of incoming.read) {
    if (typeof id !== "string" || !ID_PATTERN.test(id)) { readSkipped++; continue; }
    if (readHave.has(id)) continue;
    readHave.add(id);
    readAdditions.push(id);
  }
  const readRoom = Math.max(0, READ_LIMIT - readIds.length);
  readSkipped += Math.max(0, readAdditions.length - readRoom);
  const readFailed = !writeRaw(KEYS.read, JSON.stringify([...readIds, ...readAdditions.slice(0, readRoom)]));

  let themeApplied = false;
  if (!getThemePreference() && (incoming.theme === "light" || incoming.theme === "dark")) {
    themeApplied = writeRaw(KEYS.theme, incoming.theme);
  }
  // Older version-1 files omit these optional arrays. Never overwrite existing personal records.
  let personalAdded = 0, personalSkipped = 0, personalFailed = false;
  const merge = <T extends { id: string }>(raw: unknown, key: string, current: T[], limit: number, normalize: (v: unknown) => T | null) => {
    if (raw === undefined) return;
    if (!Array.isArray(raw)) { personalSkipped++; return; }
    const next = [...current], ids = new Set(next.map((v) => v.id));
    let added = 0;
    for (const value of raw) {
      const item = normalize(value);
      if (!item) { personalSkipped++; continue; }
      if (ids.has(item.id)) continue;
      if (next.length >= limit) { personalSkipped++; continue; }
      next.push(item); ids.add(item.id); added++;
    }
    next.sort((a, b) => {
      const time = (v: T) => { const o = v as unknown as Record<string, string>; return Date.parse(o.visitedAt ?? o.copiedAt ?? o.followedAt!); };
      return time(b) - time(a);
    });
    if (savePersonal(key, next)) personalAdded += added;
    else personalFailed = true;
  };
  merge(incoming.history, KEYS.history, getReadingHistory(), HISTORY_LIMIT, readingItem);
  merge(incoming.tasks, KEYS.tasks, getReadingTasks(), TASK_LIMIT, readingTask);
  merge(incoming.following, KEYS.following, getFollowedSources(), FOLLOWING_LIMIT, followedSource);
  cache.clear();
  emit();
  return { starredAdded: accepted.length, starredSkipped, readAdded: readFailed ? 0 : Math.min(readAdditions.length, readRoom), readSkipped, themeApplied, readFailed, personalAdded, personalSkipped, personalFailed };
}

// --- React hooks ---
const EMPTY_STARRED: LocalStarredItem[] = [];
const EMPTY_SET = new Set<string>();
const EMPTY_HISTORY: LocalReadingItem[] = [];
const EMPTY_TASKS: LocalReadingTask[] = [];
const EMPTY_FOLLOWING: LocalFollowedSource[] = [];

export function useReadingHistory() { return useSyncExternalStore(subscribeHistory, getReadingHistory, () => EMPTY_HISTORY); }
export function useReadingTasks() { return useSyncExternalStore(subscribeTasks, getReadingTasks, () => EMPTY_TASKS); }
export function useFollowedSources() { return useSyncExternalStore(subscribeFollowing, getFollowedSources, () => EMPTY_FOLLOWING); }

export function useStarred(): LocalStarredItem[] {
  return useSyncExternalStore(subscribeStarred, getStarred, () => EMPTY_STARRED);
}

export function useIsStarred(id: string): boolean {
  return useSyncExternalStore(subscribeStarred, () => isStarred(id), () => false);
}

export function useReadSet(): Set<string> {
  return useSyncExternalStore(subscribeRead, getReadSet, () => EMPTY_SET);
}

export function useThemePreference(): ThemePreference {
  return useSyncExternalStore(subscribeTheme, getThemePreference, () => null);
}

export function useChangelogSeen(): string | null {
  return useSyncExternalStore(subscribeChangelog, getChangelogSeen, () => null);
}
