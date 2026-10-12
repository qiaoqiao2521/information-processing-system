"""Safety and behavior of the paid public-page acquisition boundary; no external calls."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from tools.aihot.frontier import CONFIG, Scraper, listing, material, timestamp, main


class FrontierTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads(CONFIG.read_text())['sources'][0]

    def test_sort_dates_and_reject_external_and_pdf_links(self):
        data = {'html': '''<article><time datetime="2025-01-01"></time><a href="/publications/old">Old report</a></article>
        <article><time datetime="2026-10-08"></time><a href="/publications/new?utm=x">New report</a></article>
        <a href="https://evil.test/publications/fake">Fake</a><a href="/files/report.pdf">PDF</a>'''}
        rows = listing(data, self.source)
        self.assertEqual([r['url'] for r in rows], ['https://epoch.ai/publications/new', 'https://epoch.ai/publications/old'])

    def test_unknown_date_not_replaced_with_today_and_forecast_not_rewritten(self):
        item = {'url': 'https://epoch.ai/publications/new', 'title': '', 'publishedAt': None}
        data = {'html': '<h1>What might AI look like in 2030?</h1>', 'metadata': {'description': 'Conditional forecast, not a measured result.'}}
        value = material(data, item, self.source, True)
        self.assertIsNone(value['publishedAt'])
        self.assertEqual(value['bodyText'], '')
        self.assertIn('Conditional forecast', value['summary'])
        self.assertTrue(value['raw']['_aihot']['baseline'])

    def test_metadata_date_and_redirect_failure(self):
        item = {'url': 'https://epoch.ai/publications/new', 'title': '', 'publishedAt': None}
        data = {'html': '<h1>Valid report title</h1>', 'metadata': {'article:published_time': '2026-10-08T12:00:00.123Z'}}
        self.assertEqual(material(data, item, self.source, False)['publishedAt'], '2026-10-08T12:00:00.123000Z')
        data['metadata']['url'] = 'https://evil.test/new'
        with self.assertRaises(ValueError): material(data, item, self.source, False)
        self.assertEqual(timestamp('8th September 2026'), '2026-09-08T00:00:00Z')

    def test_budget_counts_failed_and_unknown_attempts_before_network(self):
        with tempfile.TemporaryDirectory() as d, patch('urllib.request.urlopen') as fetch:
            path = Path(d) / 'state.json'
            state = {'receipts': [{'at': time.time(), 'url': 'https://epoch.ai/publications/old', 'status': 'unknown'}]}
            with self.assertRaisesRegex(RuntimeError, 'budget'):
                Scraper(state, path, 'test-only', 1).scrape('https://epoch.ai/publications/new')
            fetch.assert_not_called()

    def test_unknown_failure_is_durable_and_not_automatically_retried(self):
        with tempfile.TemporaryDirectory() as d, patch('urllib.request.urlopen', side_effect=TimeoutError):
            path = Path(d) / 'state.json'; state = {'receipts': []}
            scraper = Scraper(state, path, 'test-only', 10)
            with self.assertRaisesRegex(RuntimeError, 'unknown'): scraper.scrape('https://epoch.ai/publications/new')
            restored = json.loads(path.read_text())
            self.assertEqual(restored['receipts'][0]['status'], 'unknown')
            with self.assertRaisesRegex(RuntimeError, 'cooldown'):
                Scraper(restored, path, 'test-only', 10).scrape('https://epoch.ai/publications/new')
            self.assertEqual(len(restored['receipts']), 1)

    def test_pending_ingest_replays_without_another_paid_scrape(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'frontier').mkdir(); (root / 'app').mkdir()
            (root / 'frontier.env').write_text('FIRECRAWL_API_KEY=test-only\n')
            (root / 'app/.env').write_text('INGEST_TOKEN=test-only-ingest-value\n')
            path = root / 'frontier/state.json'
            path.write_text(json.dumps({'receipts': [], 'sources': {'frontier-epoch': {
                'seen': [], 'pending': [{'url': 'https://epoch.ai/publications/replay'}], 'initialized': True}}}))
            with patch('sys.argv', ['frontier.py', '--root', d, '--sources', 'frontier-epoch']), \
                 patch('tools.aihot.frontier.publish'), patch('tools.aihot.frontier.ingest', return_value=0) as report, \
                 patch.object(Scraper, 'scrape') as scrape:
                main()
                scrape.assert_not_called(); report.assert_called_once()
            state = json.loads(path.read_text())['sources']['frontier-epoch']
            self.assertNotIn('pending', state)
            self.assertIn('https://epoch.ai/publications/replay', state['seen'])

    def test_paused_source_stops_before_paid_request(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'app').mkdir()
            (root / 'frontier.env').write_text('FIRECRAWL_API_KEY=test-only\n')
            (root / 'app/.env').write_text('INGEST_TOKEN=test-only-ingest-value\n')
            with patch('sys.argv', ['frontier.py', '--root', d, '--sources', 'frontier-epoch']), \
                 patch('tools.aihot.frontier.publish', side_effect=RuntimeError('source paused')), \
                 patch.object(Scraper, 'scrape') as scrape:
                with self.assertRaises(SystemExit): main()
                scrape.assert_not_called()
