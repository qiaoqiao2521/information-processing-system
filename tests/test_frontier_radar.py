"""Evidence, dates and upstream failure boundaries for the public radar adapters."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.knowledge_pipeline.acquisition import fetch_frontier_radar as radar
from tools.aihot.bridge import batches
from web.catalog import catalog
from web.refresh import promote, SourceUnavailable

NOW = datetime(2026, 10, 20, 8, tzinfo=timezone.utc)


class RadarTests(unittest.TestCase):
    def test_hn_discussion_keeps_comment_evidence_and_filters_deleted(self):
        documents = {radar.HN + 'topstories.json': [1, 2],
            radar.HN + 'item/1.json': {'id': 1, 'type': 'story', 'title': 'New LLM compiler',
                'time': NOW.timestamp() - 3600, 'url': 'https://example.org/paper', 'kids': [3, 4], 'by': 'submitter'},
            radar.HN + 'item/2.json': {'id': 2, 'type': 'story', 'title': 'A rainy morning', 'time': NOW.timestamp()},
            radar.HN + 'item/3.json': {'id': 3, 'type': 'comment', 'parent': 1, 'by': 'reader',
                'time': NOW.timestamp() - 1800, 'text': 'My <b>test</b> differs.<script>bad()</script>'},
            radar.HN + 'item/4.json': {'id': 4, 'type': 'comment', 'parent': 1, 'deleted': True}}
        with patch.object(radar, 'fetch_json', side_effect=lambda url: documents[url]):
            items, coverage = radar.hacker_news({'scan_limit': 4, 'max_items': 2, 'comments_per_story': 3}, NOW)
        self.assertEqual(len(items), 1)
        result = items[0]
        self.assertEqual(result['url'], 'https://news.ycombinator.com/item?id=1')
        self.assertEqual(result['raw']['originalUrl'], 'https://example.org/paper')
        comment = result['raw']['comments'][0]
        self.assertEqual(comment['text'], 'My test differs.')
        self.assertEqual(comment['textSha256'], sha256(comment['text'].encode()).hexdigest())
        self.assertIn(comment['url'], result['body'])
        self.assertIn('不代表共识', result['body'])
        self.assertEqual(coverage['comments'], 1)

    def test_hn_all_requests_failed_cannot_be_a_fresh_empty_feed(self):
        with patch.object(radar, 'fetch_json', side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):
                radar.hacker_news({'scan_limit': 4, 'max_items': 2, 'comments_per_story': 3}, NOW)

    def test_release_notes_preserve_original_date_and_version_identity(self):
        value = {'id': 7, 'name': 'v1.2', 'tag_name': 'v1.2', 'draft': False, 'prerelease': False,
                 'published_at': '2026-10-19T06:00:00Z', 'body': 'Added exact feature.',
                 'html_url': 'https://github.com/test/tool/releases/tag/v1.2'}
        with patch.object(radar, 'fetch_json', return_value=value):
            items, _ = radar.github_releases({'repositories': ['test/tool']}, NOW)
        self.assertEqual(items[0]['publishedAt'], '2026-10-19T06:00:00+00:00')
        self.assertIn('test/tool', items[0]['title'])
        self.assertIn('Added exact feature.', items[0]['body'])
        with patch.object(radar, 'fetch_json', return_value={**value, 'prerelease': True}):
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                radar.github_releases({'repositories': ['test/tool']}, NOW)

    def test_quality_unavailable_does_not_replace_the_previous_snapshot(self):
        quality = {'status': 'unavailable', 'reason': 'Upstream event coverage insufficient'}
        with patch.object(radar, 'fetch_json', return_value={'data': {'rows': []}, 'data_quality': quality}):
            items, coverage = radar.oss_insight({'period': 'past_24_hours', 'language': 'All', 'max_items': 8}, NOW)
        self.assertEqual(items, [])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staged, output = root / 'staged', root / 'output'
            staged.mkdir(); output.mkdir()
            name = radar.FILES['oss-insight']
            (staged / name).write_text(json.dumps({'generated_at': NOW.isoformat(), 'items': items, 'coverage': coverage}))
            previous = output / name
            previous.write_text('previous valid snapshot')
            before = previous.stat().st_mtime_ns
            with self.assertRaisesRegex(SourceUnavailable, 'insufficient'):
                promote('oss-insight', staged, output, root / 'backups')
            self.assertEqual(previous.read_text(), 'previous valid snapshot')
            self.assertEqual(previous.stat().st_mtime_ns, before)

    def test_healthy_trend_has_no_fabricated_release_date(self):
        with patch.object(radar, 'fetch_json', return_value={'data': {'rows': [
                {'repo_name': 'example/llm-engine', 'stars': 123, 'description': 'AI inference'}]}}):
            items, _ = radar.oss_insight({'period': 'past_24_hours', 'language': 'All', 'max_items': 8}, NOW)
        self.assertIsNone(items[0]['publishedAt'])
        self.assertEqual(items[0]['raw']['kind'], 'trend_observation')

    def test_evidence_survives_catalog_and_ingest_without_double_html_decode(self):
        body = 'Literal &lt;token&gt;\n原始证据行'
        entry = radar.item('A release', 'https://example.org/release', NOW.isoformat(), body + '\n', {'kind': 'release'})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / radar.FILES['github-releases']).write_text(json.dumps({'generated_at': NOW.isoformat(), 'items': [entry]}))
            library = catalog(root, root)
        payload = list(batches(library, ['github-releases']))[0]['items'][0]
        self.assertEqual(payload['bodyText'], body)
        self.assertEqual(payload['raw']['bodySha256'], sha256(body.encode()).hexdigest())
        library['items'][0]['body'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            list(batches(library, ['github-releases']))

    def test_naive_and_future_dates_are_rejected(self):
        for value in ('2026-10-20', '2026-10-21T00:00:00Z', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                radar.timestamp(value, NOW)


if __name__ == '__main__':
    unittest.main()
