"""Exercise feed failures and provenance at the new collector/catalog boundary."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.knowledge_pipeline.acquisition.fetch_ak_rss import normalize
from web.catalog import catalog


class AKFeedTests(unittest.TestCase):
    def payload(self):
        article = {'title': 'Article', 'link': 'https://example.org/post',
                   'published_at': '2026-09-29T20:00:00+08:00', 'feed_name': 'Author', 'summary': 'Summary'}
        return {'feed_count': 3, 'errors': [{'feed_name': 'Failed', 'error': 'timeout'}],
                'items': [article, article.copy(), dict(article, link='javascript:bad'),
                          dict(article, link='https://example.org/undated', published_at=None)],
                'start_date': '2026-09-24', 'target_date': '2026-09-30', 'days': 7, 'timezone': 'Asia/Shanghai'}

    def test_partial_feed_failure_preserves_dates_and_exposes_coverage(self):
        doc = normalize(self.payload(), '2026-09-30T00:00:00+00:00')
        self.assertEqual(len(doc['items']), 1)
        self.assertEqual(doc['selection'], 'unscored')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'ak_rss_sources_latest.json').write_text(json.dumps(doc))
            library = catalog(root, root)
        item = library['items'][0]
        source = next(s for s in library['sources'] if s['id'] == 'ak-rss')
        self.assertEqual(source['coverage'], {'total': 3, 'succeeded': 2, 'failed': 1})
        self.assertEqual(item['publishedAt'], '2026-09-29T20:00:00+08:00')
        self.assertEqual(item['collectedAt'], '2026-09-30T00:00:00+00:00')
        self.assertEqual(item['author'], 'Author')

    def test_all_failed_or_empty_window_is_not_a_fresh_success(self):
        payload = self.payload()
        payload['feed_count'] = 1
        with self.assertRaisesRegex(ValueError, 'All AK feeds failed'):
            normalize(payload, '2026-09-30T00:00:00Z')
        payload['feed_count'] = 3
        payload['items'] = []
        with self.assertRaisesRegex(ValueError, 'No dated AK articles'):
            normalize(payload, '2026-09-30T00:00:00Z')

    def test_long_feed_body_is_preserved_outside_list_excerpt(self):
        payload = self.payload()
        full_body = 'Long article text. ' * 100
        payload['items'][0]['summary'] = full_body
        item = normalize(payload, '2026-09-30T00:00:00Z')['items'][0]
        self.assertEqual(item['content'], full_body)
        self.assertLessEqual(len(item['summary']), 401)
