"""Acceptance boundaries for the retained custom collector adapter."""
import unittest
from tools.aihot.bridge import batches
from tools.aihot.subscriptions import build_sources


class AihotBridgeTests(unittest.TestCase):
    def test_rss_and_x_are_not_recollected_and_missing_dates_stay_missing(self):
        def item(source):
            return {'id': source, 'sourceId': source, 'url': 'https://example.org/' + source,
                    'title': source, 'summary': 'excerpt', 'body': '', 'publishedAt': None,
                    'collectedAt': '2026-09-30T00:00:00Z'}
        payloads = list(batches({'items': [item(x) for x in ('rss', 'ak-rss', 'x', 'juya')]}))
        self.assertEqual([p['sourceId'] for p in payloads], ['hub-juya'])
        self.assertIsNone(payloads[0]['items'][0]['publishedAt'])
        self.assertEqual(payloads[0]['items'][0]['raw']['collectedAt'], '2026-09-30T00:00:00Z')

    def test_subscription_seed_is_idempotent_and_x_stays_paused(self):
        first = build_sources([])
        second = build_sources(first['sources'])
        self.assertEqual(first, second)
        urls = [s['config']['feedUrl'] for s in first['sources'] if s['kind'] == 'rss']
        self.assertEqual(len(urls), len(set(urls)))
        self.assertFalse(next(s for s in first['sources'] if s['id'] == 'hub-x')['enabled'])
        self.assertTrue(all(not s.get('site_fulltext', False) for s in first['sources']))
