"""X provenance: do not confuse indexed time, login text and actual post content."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools.knowledge_pipeline.acquisition import fetch_x_google as x
from web.catalog import catalog
from web.refresh import promote

POST = 'https://x.com/anthropicai/status/2102897863097545197'
NOW = datetime(2026, 9, 30, tzinfo=timezone.utc)


class XTests(unittest.TestCase):
    @patch.object(x.subprocess, 'run', return_value=Mock(returncode=75))
    def test_risk_hold_stops_before_browser_import_or_attachment(self, run):
        with self.assertRaisesRegex(RuntimeError, 'risk hold'):
            x.collect(None)
        self.assertIn('check', run.call_args.args[0])

    def test_real_post_dates_and_strict_account_url_filter(self):
        old = 'https://x.com/openai/status/2079658951264920020'
        self.assertEqual(x.published_at(old).isoformat(), '2026-07-21T20:05:06.833000+00:00')
        self.assertEqual(x.canonical_url(POST.replace('x.com/anthropicai', 'm.x.com/AnthropicAI')+'/photo/1?lang=ar'), POST)
        for url in ('https://x.com.evil/anthropicai/status/2102897863097545197',
                    'https://user:pass@x.com/anthropicai/status/2102897863097545197',
                    POST+'suffix', POST.replace('/anthropicai/', '/other/'), old):
            self.assertEqual(x.valid_candidate(url, ['anthropicai', 'openai'], NOW-timedelta(days=7), NOW), '')
        self.assertEqual(x.valid_candidate(POST, ['anthropicai'], NOW-timedelta(days=7), NOW), POST)
        self.assertEqual(x.valid_candidate(POST, ['anthropicai'], NOW-timedelta(days=8), NOW-timedelta(days=8)), '')

    def test_reader_requires_matching_post_and_excludes_ui(self):
        content = 'Log in\n\n## Post\n[Anthropic](https://x.com/anthropicai)\n[@AnthropicAI](https://x.com/anthropicai)\n\nAn actual public post with useful content and a [source](https://example.com).\n\n[11:08 PM · Sep 23, 2026](https://x.com/anthropicai/status/2102897863097545197)\nViews\nReplies'
        body = x.extract_jina({'data': {'url': POST, 'content': content}}, POST)
        self.assertIn('actual public post', body)
        self.assertNotIn('Views', body)
        self.assertNotIn('Replies', body)
        for doc in ({'data': {'url': POST, 'content': 'Log in or sign up to X'}},
                    {'data': {'url': POST.replace('/anthropicai/', '/other/'), 'content': content}}):
            with self.assertRaises(ValueError):
                x.extract_jina(doc, POST)

    def test_login_snippets_are_not_news(self):
        self.assertEqual(x.clean_snippet('2 days ago — Log in or sign up to X. Continue with phone'), '')
        self.assertEqual(x.clean_snippet('6 days ago — useful public summary Read more'), 'useful public summary')

    def test_google_challenge_does_not_match_a_search_result_about_captcha(self):
        self.assertTrue(x.is_search_challenge('https://www.google.com/sorry/index', 'Verify you are human'))
        self.assertTrue(x.is_search_challenge('https://www.google.com/search?q=x', 'Our systems detected unusual traffic'))
        self.assertFalse(x.is_search_challenge('https://www.google.com/search?q=x', 'Search Results\nA tool that says not a robot'))

    def test_repeat_search_keeps_body_and_original_body_time(self):
        old = {'url': POST, 'title': 'old', 'content': 'Verified body', 'content_status': 'full-text', 'reader': 'jina-reader', 'body_fetched_at': '2026-09-24T10:00:00Z'}
        fresh = {'url': POST, 'title': 'new', 'summary': 'search snippet', 'content': '', 'content_status': 'snippet'}
        items = x.merge_items([old], [fresh, fresh], ['anthropicai'], NOW-timedelta(days=7), NOW)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['content'], 'Verified body')
        self.assertEqual(items[0]['body_fetched_at'], old['body_fetched_at'])
        self.assertEqual(items[0]['title'], 'new')

    def test_catalog_distinguishes_snippet_and_empty_refresh_keeps_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output=root/'out'; output.mkdir(); staged=root/'staged'; staged.mkdir()
            document={'generated_at': NOW.isoformat(), 'coverage': {'total':8,'succeeded':8,'failed':0},
                      'reading': {'status':'not-configured','fullText':0,'snippets':1},
                      'items':[{'url':POST,'title':'Public summary','summary':'Search extract','content_status':'snippet',
                                'author':'@anthropicai','published_at':x.published_at(POST).isoformat()}]}
            path=output/x.FILENAME; path.write_text(json.dumps(document))
            result=catalog(output,root/'data'); item=result['items'][0]
            self.assertEqual(item['kind'],'搜索摘要')
            self.assertEqual(item['body'],'')
            self.assertNotEqual(item['publishedAt'],item['collectedAt'])
            self.assertIn({'label':'正文状态','value':'搜索摘要 · 正文未取得'},item['fields'])
            before=(path.read_bytes(),path.stat().st_mtime_ns)
            (staged/x.FILENAME).write_text(json.dumps({'generated_at': NOW.isoformat(),'items':[]}))
            with self.assertRaises(ValueError): promote('x',staged,output,root/'backup')
            self.assertEqual((path.read_bytes(),path.stat().st_mtime_ns),before)
