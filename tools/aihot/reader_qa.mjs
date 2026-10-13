// Isolated UI acceptance. Records and downloads belong to the temporary QA browser only.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const base = process.argv[2] ?? 'http://127.0.0.1:13030';
const out = process.argv[3] ?? '/tmp/intel-reader-ui-qa';
const require = createRequire(process.env.PLAYWRIGHT_MODULE_ROOT ? path.join(process.env.PLAYWRIGHT_MODULE_ROOT, 'package.json') : import.meta.url);
const { chromium } = require('playwright');
await mkdir(out, { recursive: true, mode: 0o700 });
const browser = await chromium.launch({ headless: true, executablePath: process.env.QA_CHROME_PATH || undefined });
const results = [], errors = [];
const api = async (url) => { const res = await fetch(base + url); assert.equal(res.status, 200, url); return res.json(); };

try {
  const pool = await api('/api/site/pool?tag=' + encodeURIComponent('二次加工'));
  const candidates = process.env.QA_ITEM_ID ? [{ id: process.env.QA_ITEM_ID }] : pool.items.slice(0, 12);
  let item;
  for (const candidate of candidates) {
    const detail = await api('/api/site/items/' + candidate.id);
    if (process.env.QA_ITEM_ID || (detail.body?.zh ?? detail.body?.original ?? '').length > 600) { item = detail; break; }
  }
  assert.ok(item, 'QA requires one public item with a scrollable reading body');

  for (const [name, viewport] of [['desktop', { width: 1440, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
    const context = await browser.newContext({ viewport, permissions: ['clipboard-read', 'clipboard-write'] });
    const page = await context.newPage();
    page.on('pageerror', (error) => errors.push(`${name}: ${error.message}`));
    await page.goto(base + '/me', { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: '我的阅读', exact: true }).waitFor();
    const contrast = await page.evaluate(() => {
      const luminance = (color) => {
        const values = color.match(/[\d.]+/g).slice(0, 3).map(Number).map((v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
        return values[0] * 0.2126 + values[1] * 0.7152 + values[2] * 0.0722;
      };
      const fg = luminance(getComputedStyle(document.querySelector('h1')).color);
      const bg = luminance(getComputedStyle(document.querySelector('.make-workbench')).backgroundColor);
      return (Math.max(fg, bg) + 0.05) / (Math.min(fg, bg) + 0.05);
    });
    assert.ok(contrast >= 4.5, `${name}: personal heading contrast ${contrast}`);
    assert.ok(await page.locator('a[href="/me"]:visible').count() > 0, `${name}: visible personal entry`);
    await page.evaluate(() => {
      localStorage.setItem('aihot-starred-items', JSON.stringify([{ id: 'qa-old', title: 'QA 保留的旧收藏', sourceName: 'QA', savedAt: '2026-10-01T00:00:00Z', publishedAt: null, summary: null, score: null, aiSelected: false }]));
      localStorage.setItem('aihot-read-items', JSON.stringify(['qa-old-read']));
    });
    await page.goto(base + '/items/' + item.id, { waitUntil: 'networkidle' });
    const expanded = page.locator('details[data-reading-body]');
    if (await expanded.count()) await expanded.locator('summary').click();
    assert.ok(await page.locator('.prose p').evaluateAll((elements) => elements.every((el) => el.scrollHeight <= el.offsetHeight + 1)), `${name}: reading paragraphs do not overlap`);
    const range = await page.locator('article').evaluate((el) => Math.max(0, el.offsetHeight - innerHeight * 0.65));
    assert.ok(range > 400, `${name}: scrollable article`);
    await page.mouse.move(viewport.width / 2, viewport.height / 2);
    await page.mouse.wheel(0, Math.min(range * 0.45, range - 100));
    await page.waitForFunction((id) => JSON.parse(localStorage.getItem('aihot-reading-history-v1') || '[]').some((v) => v.id === id && v.position > 0.05 && v.bodyHash), item.id);
    const saved = await page.evaluate((id) => JSON.parse(localStorage.getItem('aihot-reading-history-v1')).find((v) => v.id === id), item.id);
    await page.screenshot({ path: path.join(out, name + '-reading.png') });
    await page.goto(base + '/me', { waitUntil: 'networkidle' });
    await page.getByRole('link', { name: '继续阅读', exact: true }).click();
    await page.getByRole('status').filter({ hasText: '已恢复上次阅读位置' }).waitFor();
    assert.ok(await page.evaluate(() => scrollY) > 100, `${name}: actual resume scroll`);
    const resumed = await page.locator('article').evaluate((el) => Math.max(0, Math.min(1, (scrollY - (el.getBoundingClientRect().top + scrollY)) / Math.max(1, el.offsetHeight - innerHeight * 0.65))));
    assert.ok(Math.abs(resumed - saved.position) < 0.12, `${name}: resume within reading range`);

    await page.goto(base + '/me', { waitUntil: 'networkidle' });
    await page.evaluate((id) => {
      const list = JSON.parse(localStorage.getItem('aihot-reading-history-v1'));
      const row = list.find((v) => v.id === id); row.bodyHash = '0'.repeat(64);
      localStorage.setItem('aihot-reading-history-v1', JSON.stringify(list));
    }, item.id);
    await page.goto(base + '/items/' + item.id + '?resume=1', { waitUntil: 'networkidle' });
    await page.getByRole('status').filter({ hasText: '正文或阅读版本已变化' }).waitFor();
    assert.ok(await page.evaluate(() => scrollY) < 300, `${name}: stale fingerprint does not resume`);
    await page.locator('button:visible').filter({ hasText: /^关注来源$/ }).click();
    await page.goto(base + '/me?view=following', { waitUntil: 'networkidle' });
    await page.getByRole('link').filter({ hasText: '查看动态' }).click();
    await page.getByRole('heading', { name: '来源动态', exact: true }).waitFor();
    assert.equal(new URL(page.url()).searchParams.get('source'), item.source.id);
    const sourcePool = await api('/api/site/pool?source=' + encodeURIComponent(item.source.id));
    assert.ok(sourcePool.items.length > 0);
    assert.ok(sourcePool.items.every((row) => row.source.name === item.source.name));
    await page.getByLabel('分类', { exact: true }).selectOption('ai-models');
    await page.waitForURL((url) => url.searchParams.get('category') === 'ai-models');
    assert.equal(new URL(page.url()).searchParams.get('source'), item.source.id);

    await page.goto(base + '/reading-tools', { waitUntil: 'networkidle' });
    await page.getByLabel('选择技能', { exact: true }).selectOption('ljg-plain');
    await page.getByLabel('原文链接或处理材料').fill(item.links.original);
    await page.getByRole('button', { name: '复制处理任务', exact: true }).click();
    await page.getByRole('status').filter({ hasText: '已复制处理任务，并保存' }).waitFor();
    await page.getByRole('link', { name: '查看我的加工记录' }).click();
    const task = page.locator('details').filter({ hasText: '已复制任务 · 待外部处理' });
    await task.locator('summary').click();
    await task.getByLabel('粘贴处理结果').fill('QA 手工保存结果。未复核，未发布。');
    await task.getByRole('button', { name: '保存结果' }).click();
    await page.getByRole('status').filter({ hasText: '结果已保存到本机' }).waitFor();
    assert.ok(await page.getByText('已保存结果 · 未复核', { exact: true }).count());
    await page.getByRole('link', { name: '重新打开任务', exact: true }).click();
    await page.getByRole('status').filter({ hasText: '已载入本机任务' }).waitFor();
    assert.equal(await page.getByLabel('原文链接或处理材料').inputValue(), item.links.original);

    await page.goto(base + '/me?view=settings', { waitUntil: 'networkidle' });
    const downloading = page.waitForEvent('download');
    await page.getByRole('button', { name: '导出本机数据' }).click();
    const download = await downloading, exported = path.join(out, name + '-local-data.json');
    await download.saveAs(exported);
    const bundle = JSON.parse(await readFile(exported, 'utf8'));
    assert.equal(bundle.starred[0].savedAt, '2026-10-01T00:00:00Z');
    assert.ok(bundle.read.includes('qa-old-read'));
    assert.equal(bundle.tasks[0].result, 'QA 手工保存结果。未复核，未发布。');
    await page.screenshot({ path: path.join(out, name + '-settings.png'), fullPage: true });

    const target = await browser.newContext({ viewport });
    const fresh = await target.newPage(); fresh.on('pageerror', (error) => errors.push(`${name}-import: ${error.message}`));
    await fresh.goto(base + '/me?view=settings', { waitUntil: 'networkidle' });
    await fresh.getByLabel('导入本机数据').setInputFiles(exported);
    await fresh.getByRole('status').filter({ hasText: '个人记录 3 条' }).waitFor();
    await fresh.getByLabel('导入本机数据').setInputFiles(exported);
    await fresh.getByRole('status').filter({ hasText: '个人记录 0 条' }).waitFor();
    await fresh.goto(base + '/me?view=tasks', { waitUntil: 'networkidle' });
    assert.ok(await fresh.getByText('已保存结果 · 未复核', { exact: true }).count());
    await fresh.screenshot({ path: path.join(out, name + '-tasks.png'), fullPage: true });
    assert.ok(await fresh.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${name}: no page overflow`);
    await fresh.goto(base + '/starred', { waitUntil: 'networkidle' });
    await fresh.getByText('QA 保留的旧收藏', { exact: true }).waitFor();
    results.push({ viewport: name, contrast, passed: ['personal-entry', 'contrast', 'body-flow', 'history', 'resume', 'stale-body', 'follow-source', 'combined-filter', 'copied-task', 'manual-result', 'reopen-task', 'export', 'import', 'duplicate-import', 'old-data', 'layout'] });
    await target.close(); await context.close();
  }
  assert.deepEqual(errors, []);
  await writeFile(path.join(out, 'report.json'), JSON.stringify({ base, itemId: item.id, results, errors }, null, 2));
  console.log(JSON.stringify({ base, checks: results.reduce((n, r) => n + r.passed.length, 0), errors, out }));
} finally { await browser.close(); }
