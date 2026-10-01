import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone

spec = importlib.util.spec_from_file_location('upstream_feed', Path(__file__).parents[1] / 'tools/aihot/upstream_feed.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
BODY = b'''<rss><channel><item><guid>one</guid><title>Example</title><link>https://aihot.news/items/one</link><description>&lt;p&gt;Summary&lt;/p&gt;&lt;a href="https://example.com/article"&gt;Original&lt;/a&gt;</description><pubDate>Thu, 01 Oct 2026 04:44:34 GMT</pubDate></item></channel></rss>'''
class Response:
    status = 200; headers = {'ETag': '"test"'}
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def geturl(self): return 'https://aihot.news/feed.xml'
    def read(self, _): return BODY

class UpstreamFeedTests(unittest.TestCase):
    def test_original_and_attribution_survive_without_html(self):
        item = m.parse_feed(BODY)[0]
        self.assertEqual(item['links']['original'], 'https://example.com/article')
        self.assertEqual(item['attribution']['url'], 'https://aihot.news/items/one')
        self.assertNotIn('<p>', item['summary'])
        self.assertEqual(item['publishedAt'], 'Thu, 01 Oct 2026 04:44:34 GMT')
        self.assertNotIn('score', item)
    def test_invalid_xml_and_link_are_rejected(self):
        for body in (b'<!DOCTYPE rss>'+BODY, BODY.replace(b'https://aihot.news/items', b'https://evil.example/items'), b'<html/>'):
            with self.assertRaises(ValueError): m.parse_feed(body)
    def test_cache_limits_polling_and_304_retains_items_failure_preserves_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); m.sync('selected', root, lambda *_a, **_k: Response())
            path=root/'selected.json'; old=json.loads(path.read_text()); before=path.read_bytes()
            self.assertEqual(m.sync('selected', root, lambda *_a, **_k: self.fail('ttl must prevent network'))['status'], 'cached')
            old['fetchedAt']=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(); m.atomic_json(path,old)
            def unchanged(req, **kwargs):
                self.assertEqual(req.get_header('If-none-match'), '"test"')
                raise urllib.error.HTTPError(req.full_url,304,'not modified',{},None)
            self.assertEqual(m.sync('selected',root,unchanged)['status'],304)
            self.assertEqual(json.loads(path.read_text())['items'],old['items'])
            old['fetchedAt']=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat();m.atomic_json(path,old);before=path.read_bytes()
            def failed(*args,**kwargs):raise OSError('offline')
            with self.assertRaises(OSError):m.sync('selected',root,failed)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
