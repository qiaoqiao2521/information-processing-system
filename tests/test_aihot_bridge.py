"""Acceptance boundaries for the retained custom collector adapter."""
import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from tools.aihot.bridge import batches, main
from tools.aihot.subscriptions import build_sources
from web.catalog import catalog


class AihotBridgeTests(unittest.TestCase):
    def test_cli_release_date_reaches_ingest_without_becoming_collection_time(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'cli_releases_sources_latest.json').write_text(json.dumps({
                'generated_at': '2026-10-09T10:00:00Z', 'items': [{
                    'title': 'Codex stable', 'url': 'https://github.com/openai/codex/releases/tag/stable',
                    'publishedAt': '2026-10-08T06:00:00Z', 'summary': 'Official note', 'author': 'OpenAI'}]}))
            payloads = list(batches(catalog(root, root), ['cli-releases']))
            self.assertEqual(payloads[0]['sourceId'], 'hub-cli-releases')
            self.assertEqual(payloads[0]['items'][0]['publishedAt'], '2026-10-08T06:00:00+00:00')
            self.assertEqual(payloads[0]['items'][0]['bodyText'], '')

    def test_failed_collection_does_not_ingest_old_snapshot_or_report_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'app').mkdir()
            (root / 'app/.env').write_text('INGEST_TOKEN=isolated-test-value\n')
            with patch('sys.argv', ['bridge.py', '--root', str(root), '--refresh', '--sources', 'cli-releases']), \
                    patch('tools.aihot.bridge.refresh_sources', return_value=[{'source': 'cli-releases', 'status': 'failed'}]), \
                    patch('tools.aihot.bridge.catalog', return_value={'items': [{'id': 'old', 'sourceId': 'cli-releases', 'url': 'https://github.com/openai/codex/releases/tag/old', 'title': 'old', 'publishedAt': None, 'collectedAt': '2026-01-01'}]}), \
                    patch('tools.aihot.bridge.urllib.request.urlopen') as request:
                with self.assertRaises(SystemExit) as failure:
                    main()
                self.assertEqual(failure.exception.code, 1)
                request.assert_not_called()

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
