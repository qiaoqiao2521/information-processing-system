"""Keep official release selection complete and failed collection visibly unsuccessful."""
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools.knowledge_pipeline.acquisition import fetch_cli_releases as releases

NOW = datetime(2026, 10, 9, 8, 0, tzinfo=timezone.utc)


def release(repository='openai/codex', tag='v1.0', **changes):
    value = {'name': f'Official release {tag}', 'tag_name': tag,
             'html_url': f'https://github.com/{repository}/releases/tag/{tag}',
             'published_at': '2026-10-08T10:00:00Z', 'body': 'Release notes.',
             'draft': False, 'prerelease': False}
    return dict(value, **changes)


def payloads(recent=None):
    return [release('anthropics/claude-code'), release(tag='stable-outside-recent'),
            recent if recent is not None else [release(tag='preview-1', prerelease=True)]]


class Response(io.BytesIO):
    def __init__(self, content, headers=None):
        super().__init__(content)
        self.headers = headers or {}
        self.read_sizes = []

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


class ReleaseCollectorTests(unittest.TestCase):
    def collect(self, documents):
        with patch.object(releases, '_fetch_json', side_effect=documents) as fetch:
            document = releases.collect(NOW)
        self.assertEqual([call.args[0] for call in fetch.call_args_list], list(releases.ENDPOINTS))
        return document

    def test_stable_releases_survive_when_outside_recent_list(self):
        recent = [release(tag='preview-1', prerelease=True),
                  release(tag='preview-2', prerelease=True), release(tag='previous-stable')]
        document = self.collect(payloads(recent))
        self.assertEqual([item['url'].rsplit('/', 1)[1] for item in document['items']],
                         ['v1.0', 'stable-outside-recent', 'preview-1'])
        self.assertEqual(document['generated_at'], NOW.isoformat())
        self.assertEqual(document['items'][1]['publishedAt'], '2026-10-08T10:00:00+00:00')
        self.assertEqual(document['selection'], 'unscored')

    def test_preview_is_optional_and_drafts_never_selected(self):
        for recent in ([], [release()], [release(prerelease=True, draft=True)]):
            with self.subTest(recent=recent):
                self.assertEqual(len(self.collect(payloads(recent))['items']), 2)

    def test_duplicate_preview_does_not_duplicate_stable_url(self):
        latest = release(tag='same-url')
        document = self.collect([release('anthropics/claude-code'), latest,
                                 [dict(latest, prerelease=True), dict(latest, prerelease=True)]])
        self.assertEqual(len(document['items']), 2)

    def test_long_release_body_is_only_a_bounded_excerpt(self):
        documents = payloads()
        documents[0]['body'] = 'long release notes ' * 1000
        item = self.collect(documents)['items'][0]
        self.assertLessEqual(len(item['summary']), 600)
        self.assertNotIn('body', item)
        self.assertEqual(set(item), {'title', 'url', 'publishedAt', 'summary', 'author'})

    def test_invalid_schema_title_flags_and_dates_fail(self):
        cases = [[], {}, release(draft='false'), release(prerelease=None),
                 release(name=' ', tag_name=' '), release(published_at=None),
                 release(published_at='not-a-date'), release(published_at='2026-10-08'),
                 release(published_at='2026-10-10T10:00:00Z'), release(body=['not text']),
                 release(draft=True), release(prerelease=True)]
        for invalid in cases:
            with self.subTest(invalid=invalid):
                documents = payloads()
                documents[1] = invalid
                with self.assertRaises(ValueError):
                    self.collect(documents)

    def test_nonarray_or_bad_recent_metadata_fails_even_after_valid_preview(self):
        for recent in ({}, [None], [release(prerelease=True), {'draft': False}]):
            with self.subTest(recent=recent):
                with self.assertRaises(ValueError):
                    self.collect(payloads(recent))

    def test_unofficial_and_unsafe_release_urls_fail(self):
        for url in ('http://github.com/openai/codex/releases/tag/v1',
                    'https://github.com.evil.test/openai/codex/releases/tag/v1',
                    'https://github.com/other/repo/releases/tag/v1',
                    'https://owner@github.com/openai/codex/releases/tag/v1',
                    'https://github.com/openai/codex/releases/tag/',
                    'https://github.com/openai/codex/releases/tag/../v1',
                    'https://github.com/openai/codex/releases/tag/v1?redirect=evil',
                    'https://github.com/openai/codex/releases/tag/v1\n'):
            with self.subTest(url=url):
                documents = payloads()
                documents[1]['html_url'] = url
                with self.assertRaises(ValueError):
                    self.collect(documents)

    def test_each_critical_request_failure_retains_existing_snapshot(self):
        for index in range(3):
            with self.subTest(request_index=index), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                previous = output / releases.FILENAME
                previous.write_text('{"generated_at":"old","items":["old"]}')
                original, timestamp = previous.read_bytes(), previous.stat().st_mtime_ns
                documents = payloads()
                documents[index] = TimeoutError('Official endpoint timed out')
                with patch.object(releases, '_fetch_json', side_effect=documents):
                    with self.assertRaises(TimeoutError):
                        releases.harvest(output, NOW)
                self.assertEqual(previous.read_bytes(), original)
                self.assertEqual(previous.stat().st_mtime_ns, timestamp)

    def test_bad_schema_does_not_create_a_fresh_empty_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            with patch.object(releases, '_fetch_json', side_effect=payloads({})):
                with self.assertRaises(ValueError):
                    releases.harvest(output, NOW)
            self.assertFalse((output / releases.FILENAME).exists())

    def test_workspace_root_uses_output_to_user(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(releases.os.environ, {'WORKSPACE_ROOT': temporary}):
                with patch.object(releases, '_fetch_json', side_effect=payloads()):
                    document = releases.harvest(now=NOW)
            target = Path(temporary) / 'output_to_user' / releases.FILENAME
            self.assertEqual(json.loads(target.read_text()), document)
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_http_request_is_unauthenticated_timed_and_bounded(self):
        response = Response(b'{"ok":true}')
        opener = Mock()
        opener.open.return_value = response
        with patch.object(releases.urllib.request, 'build_opener', return_value=opener):
            self.assertEqual(releases._fetch_json(releases.ENDPOINTS[0]), {'ok': True})
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, releases.ENDPOINTS[0])
        self.assertEqual(opener.open.call_args.kwargs['timeout'], 25)
        self.assertFalse(any(key.lower() == 'authorization' for key in request.headers))
        self.assertEqual(response.read_sizes, [releases.MAX_BYTES + 1])

    def test_large_response_is_rejected_instead_of_truncated(self):
        for headers, content in (({'Content-Length': str(releases.MAX_BYTES + 1)}, b'{}'),
                                 ({}, b' ' * (releases.MAX_BYTES + 1))):
            with self.subTest(headers=headers):
                response = Response(content, headers)
                opener = Mock()
                opener.open.return_value = response
                with patch.object(releases.urllib.request, 'build_opener', return_value=opener):
                    with self.assertRaisesRegex(ValueError, 'exceeds 8 MiB'):
                        releases._fetch_json(releases.ENDPOINTS[0])
                self.assertTrue(all(size <= releases.MAX_BYTES + 1 for size in response.read_sizes))

    def test_redirect_or_unrecognized_endpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            releases._NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.test')
        with patch.object(releases.urllib.request, 'build_opener') as opener:
            with self.assertRaises(ValueError):
                releases._fetch_json('https://api.github.com/repos/evil/repo/releases/latest')
        opener.assert_not_called()

    def test_cli_failure_propagates_instead_of_reporting_success(self):
        with patch.object(releases, 'harvest', side_effect=ValueError('bad source')):
            with patch('builtins.print') as output:
                with self.assertRaisesRegex(ValueError, 'bad source'):
                    releases.main([])
        output.assert_not_called()


if __name__ == '__main__':
    unittest.main()
