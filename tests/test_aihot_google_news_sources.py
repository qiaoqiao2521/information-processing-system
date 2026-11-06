"""Offline checks for the six selected personal Google News RSS subscriptions."""
import copy
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from tools.aihot.subscriptions import TARGET, build_sources


EXPECTED_QUERIES = {
    'rss-google-news-rockchip-linux': '(Rockchip OR RK3588 OR RK3568 OR Armbian OR OpenWrt) when:7d',
    'rss-google-news-embodied-robotics': '(MuJoCo OR "Isaac Lab" OR LeRobot OR "humanoid robot" OR "visuomotor") when:7d',
    'rss-google-news-drone-navigation': '(quadrotor OR "autonomous drone" OR LiDAR OR ROS2) when:7d',
    'rss-google-news-visual-generation': '(Blender OR ComfyUI OR "Gaussian Splatting" OR "motion capture") when:7d',
    'rss-google-news-coding-agents': '("coding agent" OR "Claude Code" OR "Model Context Protocol" OR OpenAI Codex) when:7d',
    'rss-google-news-china-embodied-open-models': '(具身智能 OR 机械臂 OR 瑞芯微 OR RK3588 OR 宇树 OR 开源模型) when:7d',
}


class GoogleNewsSourceTests(unittest.TestCase):
    def test_six_queries_locales_and_personal_subscription_policy(self):
        sources = {s['id']: s for s in build_sources([])['sources']
                   if s['id'].startswith('rss-google-news-')}
        self.assertEqual(set(sources), set(EXPECTED_QUERIES))
        for source_id, query in EXPECTED_QUERIES.items():
            with self.subTest(source_id=source_id):
                source = sources[source_id]
                url = urlsplit(source['config']['feedUrl'])
                chinese = source_id == 'rss-google-news-china-embodied-open-models'
                self.assertEqual((url.scheme, url.netloc, url.path),
                                 ('https', 'news.google.com', '/rss/search'))
                self.assertEqual(parse_qs(url.query), {
                    'q': [query], 'hl': ['zh-CN' if chinese else 'en-US'],
                    'gl': ['CN' if chinese else 'US'],
                    'ceid': ['CN:zh-Hans' if chinese else 'US:en'],
                })
                self.assertTrue(any('\u4e00' <= char <= '\u9fff' for char in source['name']))
                self.assertEqual(source['kind'], 'rss')
                self.assertEqual(source['tier'], 'T2')
                self.assertFalse(source['first_party'])
                self.assertNotIn('owner_entity_id', source)
                self.assertIn('个人订阅', source['tags'])
                self.assertNotIn('官方', source['tags'])
                self.assertEqual(source['participation_mode'], 'editorial')
                self.assertTrue(source.get('enabled', True))
                self.assertTrue(source['config']['sortByPublishedAt'])
                # Native pending publication requires a first-party source. Use normal processing.
                self.assertEqual(set(source['config']), {'feedUrl', 'sortByPublishedAt'})
                self.assertFalse(source['site_fulltext'])
                self.assertFalse(source['syndicate_fulltext'])

    def test_regeneration_keeps_unique_sources(self):
        first = build_sources([])
        self.assertEqual(first, build_sources(first['sources']))
        ids = [s['id'] for s in first['sources']]
        urls = [s['config']['feedUrl'] for s in first['sources'] if s['kind'] == 'rss']
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(urls), len(set(urls)))

    def test_existing_id_or_feed_url_is_preserved_without_duplicate(self):
        for source in build_sources([])['sources']:
            if source['id'] not in EXPECTED_QUERIES:
                continue
            for duplicate_by in ('id', 'feedUrl'):
                with self.subTest(source_id=source['id'], duplicate_by=duplicate_by):
                    existing = copy.deepcopy(source)
                    existing.update(name='我的自定义订阅', enabled=False, interval_minutes=240)
                    if duplicate_by == 'id':
                        existing['config']['feedUrl'] = 'https://example.org/custom-feed.xml'
                    else:
                        existing['id'] = 'existing-personal-subscription'
                    before = copy.deepcopy(existing)
                    generated = build_sources([existing])['sources']
                    matching = [s for s in generated if s['id'] == source['id']
                                or s['config'].get('feedUrl') == source['config']['feedUrl']]
                    self.assertEqual([before], matching)
                    self.assertEqual(before, existing)

    def test_checked_in_seed_matches_generator(self):
        seed = json.loads(TARGET.read_text())
        self.assertEqual(seed, build_sources(seed['sources']))
        self.assertEqual({s['id'] for s in seed['sources'] if s['id'].startswith('rss-google-news-')},
                         set(EXPECTED_QUERIES))
