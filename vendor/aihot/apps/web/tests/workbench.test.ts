import assert from 'node:assert/strict';
import test from 'node:test';
import type { FeedItemSummary } from '@aihot/contracts/site';
import { arxivHubHref, filterHref, toWorkbenchItem } from '../app/features/workbench/model.ts';

test('combined filters preserve query and tag while resetting legacy paging', () => {
  const params = new URLSearchParams('q=OpenAI&tag=二次加工&channel=firstParty&page=8&deep=1&anchorAt=old&search=1&tab=relevance');
  const url = new URL(filterHref('/all', params, {category:'ai-models'}), 'https://test.local');
  assert.equal(url.searchParams.get('q'), 'OpenAI');
  assert.equal(url.searchParams.get('tag'), '二次加工');
  assert.equal(url.searchParams.get('channel'), 'firstParty');
  assert.equal(url.searchParams.get('tab'), 'relevance');
  assert.equal(url.searchParams.get('category'), 'ai-models');
  for (const key of ['page','deep','anchorAt','search']) assert.equal(url.searchParams.has(key), false);
  assert.equal(params.get('page'), '8');
  assert.equal(new URL(filterHref('/all', url.searchParams, {category:null}),url).searchParams.has('category'),false);
});

test('card adapter retains genuine publication dates, pending status and event identity', () => {
  const raw: FeedItemSummary = {id:'article-1',title:'真实报道',originalTitle:null,summary:null,reason:null,source:{name:'Official'},publishedAt:'2026-10-01T16:15:00Z',timelineAt:'2026-10-11T00:00:00Z',category:null,tags:[],score:null,selected:false,channel:'news',x:null};
  const group = {factId:'f',story:{publicId:'event-1',title:'事件'},additionalSourceCount:1,reportCount:2,developmentCount:1};
  const item = toWorkbenchItem(raw,group,"fact:f");
  assert.equal(item.dataKey,'fact:f');
  assert.equal(item.date,'2026-10-02');
  assert.equal(item.time,'00:15');
  assert.equal(item.tag,'待AI处理');
  assert.equal(item.raw,raw);
  assert.equal(item.group,group);
  assert.equal(item.raw.score,null);
  assert.equal(toWorkbenchItem({...raw,publishedAt:null}).date,'2026-10-11');
});

test('paper tool links use the local paper route and reject unrelated input', () => {
  assert.equal(arxivHubHref('https://arxiv.org/abs/2610.01234v2'), 'https://papers.muqiao.xyz/p/2610.01234v2');
  assert.equal(arxivHubHref('https://arxiv.org/pdf/2610.01234.pdf'), 'https://papers.muqiao.xyz/p/2610.01234');
  assert.equal(arxivHubHref(' 2610.01234 '), 'https://papers.muqiao.xyz/p/2610.01234');
  assert.equal(arxivHubHref('https://arxiv.org.evil.test/abs/2610.01234'), null);
  assert.equal(arxivHubHref('https://user:pass@arxiv.org/abs/2610.01234'), null);
  assert.equal(arxivHubHref('https://arxiv.org/search/2610.01234'), null);
  assert.equal(arxivHubHref('任意材料'), null);
});
