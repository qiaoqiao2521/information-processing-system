"""Regression checks for real collector shape drift and publication parity."""
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
from web import catalog as data
from web.publish import build_release, WEB
from tests import test_web_studio_bridge as bridge
hub, StudioStub = bridge.hub, bridge.StudioStub


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)/'output'; self.output.mkdir()
        self.extra = Path(self.temp.name)/'data'; self.extra.mkdir()

    def write(self, name, value, extra=False):
        (self.extra if extra else self.output).joinpath(name).write_text(json.dumps(value))

    def library(self):
        return data.catalog(self.output,self.extra)

    def test_collector_shapes_and_nonempty_radar(self):
        self.write('builderpulse_opportunity_radar_sources_latest.json', {'selected_sections':[{'section':'发现机会','items':[{'question':'什么机会？','signal':'真实正文','key_judgment':'判断','contrarian_view':'反向观点'}]}]})
        self.write('ai_builders_digest_sources_latest.json', {'selectedSources':[{'originalTitle':'真正的标题','originalText':'正文','url':'https://example.com/1'}]})
        items=self.library()['items']
        self.assertEqual(len(items),2)
        radar=next(i for i in items if i['sourceId']=='radar')
        self.assertEqual((radar['title'],radar['body']),('什么机会？','真实正文'))
        self.assertIn({'label':'相反观点','value':'反向观点'},radar['fields'])
        self.assertEqual(next(i for i in items if i['sourceId']=='digest')['title'],'真正的标题')

    def test_raw_collection_wins_over_stale_enrichment(self):
        self.write('github_trending_latest.json',{'repos':[{'full_name':'a/b','description':'new','stars':50,'url':'https://github.com/a/b'}]})
        self.write('enriched_trending.json',{'repos':[{'full_name':'a/b','description':'old','stars':10,'local_snapshot':'outdated'}]},extra=True)
        item=self.library()['items'][0]
        self.assertEqual(item['summary'],'new');self.assertEqual(item['body'],'')
        self.assertIn({'label':'总星标','value':'50'},item['fields'])

    def test_four_new_sources_and_stable_ids(self):
        for filename in ('hacker_news_sources_latest.json','juya_daily_sources_latest.json','hf_daily_papers_sources_latest.json','qiaomu_rss_sources_latest.json'):
            self.write(filename,{'generated_at':'2026-09-27T00:00:00Z','items':[{'title':'Title','url':'https://example.com/a','published_at':'Sat, 26 Sep 2026 10:55:56 +0000'}]})
        first=self.library();self.assertEqual(len(first['items']),4)
        self.assertEqual(len({i['id'] for i in first['items']}),4)
        self.assertEqual(first,self.library())
        self.assertEqual(first['items'][0]['collectedAt'],'2026-09-27T00:00:00+00:00')
        self.assertEqual(first['items'][0]['publishedAt'],'2026-09-26T10:55:56+00:00')

    def test_invalid_missing_and_unsafe_url_are_not_reported_as_ready(self):
        self.output.joinpath('hacker_news_sources_latest.json').write_text('{broken')
        states={s['id']:s['status'] for s in self.library()['sources']}
        self.assertEqual(states['hacker-news'],'invalid');self.assertEqual(states['juya'],'missing')
        for url in ('javascript:alert(1)','file:///etc/passwd','https://user:password@example.com','https://['):
            self.assertEqual(data.safe_url(url),'')

    def test_publication_uses_same_data_and_source_timestamp(self):
        self.write('hacker_news_sources_latest.json',{'generated_at':'2026-09-26T00:00:00Z','local_path':'/home/muqiao/private','items':[{'title':'HN','url':'https://example.com'}]})
        bundle, manifest=build_release(Path(self.temp.name)/'build',self.output)
        extracted=Path(self.temp.name)/'unpack';extracted.mkdir()
        with tarfile.open(bundle) as tar: tar.extractall(extracted,filter='data')
        self.assertNotIn('/home/muqiao',(extracted/'snapshots/hacker_news_sources_latest.json').read_text())
        self.assertEqual(manifest['codeDigest'],data.code_digest(WEB))
        self.assertEqual(manifest['datasetDigest'],data.dataset_digest(self.output,WEB/'data'))
        self.assertEqual(manifest['datasetDigest'],data.dataset_digest(extracted/'snapshots',extracted/'web/data'))
        self.assertEqual(next(s for s in data.catalog(extracted/'snapshots',extracted/'web/data')['sources'] if s['id']=='trending')['updatedAt'],next(s for s in data.catalog(self.output,WEB/'data')['sources'] if s['id']=='trending')['updatedAt'])


class PublicBridgeTests(bridge.BridgeTests):
    def test_public_mode_blocks_all_posts_without_contacting_studio(self):
        StudioStub.received.clear()
        with patch.object(hub,'PUBLIC_READONLY',True):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.dispatch({'prompt':'real task','idempotencyKey':'same_key_123'})
            self.assertEqual(error.exception.code,403)
        self.assertEqual(StudioStub.received,[])
